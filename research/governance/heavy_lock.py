"""Global heavy-worker lock — machine-wide serialization, OS-enforced.

Handbook §10.3: the one-heavy-job limit is MACHINE-WIDE, not per cycle.
Each A1 counting its own workers is not enough because two cycles can
both see an idle machine. This module makes the limit a mechanism, not a
convention:

- exclusive ``fcntl.flock`` on ``.runtime/heavy_worker.lock`` (the OS
  releases it automatically if the holder dies — the LOCK cannot go
  stale);
- a registry (``.runtime/heavy_worker.registry.json``) recording cycle /
  role / PID / process-start token / command digest / worktree /
  heartbeat / expected artifacts / status — the REGISTRY can go stale
  (a crashed worker leaves a RUNNING row), and is reclaimed ONLY after
  checking both PID liveness AND the process-start token, so a reused
  PID can never be mistaken for the original holder;
- refusal is ``NOT_RUN_RESOURCE_CONFLICT`` — never spin, never overlap;
- release happens in ``finally`` and records FINISHED / FAILED /
  TECHABORT; a state file claiming ``workers=0`` while the registry row
  is RUNNING and alive is CONTROL_STATE_DRIFT (see §10.3).

Adoption boundary (FAMILY_PIPELINE.md §11): cycles whose plans
preregister this lock (crypto V16+, forex V7+, stocks V12+). Frozen and
running cycles are NOT retrofitted — their conventions keep applying.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

NOT_RUN_RESOURCE_CONFLICT = "NOT_RUN_RESOURCE_CONFLICT"

LOCK_NAME = "heavy_worker.lock"
REGISTRY_NAME = "heavy_worker.registry.json"
HISTORY_NAME = "heavy_worker.history.jsonl"

TERMINAL_STATUSES = {"FINISHED", "FAILED", "TECHABORT"}


class LockBusyError(RuntimeError):
    """Another process holds the global heavy lock."""

    verdict = NOT_RUN_RESOURCE_CONFLICT


class HeavyLockError(RuntimeError):
    """Registry/protocol violation (never guessed around — fail closed)."""


def process_start_token(pid: int) -> Optional[str]:
    """A stable per-process-instance token.

    macOS: ``ps -o lstart=``; Linux: field 22 of /proc/<pid>/stat
    (starttime in clock ticks). A recycled PID produces a different
    token — that is the entire point.
    """
    try:
        with open(f"/proc/{pid}/stat", "rb") as fh:
            parts = fh.read().rsplit(b")", 1)[1].split()
            return f"procfs:{parts[19].decode()}"
    except (OSError, IndexError):
        pass
    try:
        out = subprocess.run(
            ["ps", "-o", "lstart=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        token = out.stdout.strip()
        if out.returncode == 0 and token:
            return f"ps:{token}"
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def command_digest(argv: list[str]) -> str:
    return hashlib.sha256(" ".join(argv).encode("utf-8")).hexdigest()


def _atomic_write_json(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def _read_json(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _append_history(history: Path, record: dict) -> None:
    with history.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


@dataclass
class HeavyLockHandle:
    fd: int
    lock_path: Path
    registry_path: Path
    history_path: Path
    owner: dict = field(default_factory=dict)
    _released: bool = False

    def heartbeat(self, extra: Optional[dict] = None) -> None:
        if self._released:
            raise HeavyLockError("heartbeat after release")
        record = _read_json(self.registry_path) or {}
        record.update({"last_heartbeat": _utcnow(), "status": "RUNNING"})
        if extra:
            record.setdefault("extra", {}).update(extra)
        _atomic_write_json(self.registry_path, record)

    def release(self, status: str = "FINISHED", note: str = "") -> None:
        if status not in TERMINAL_STATUSES:
            raise HeavyLockError(f"status must be one of {sorted(TERMINAL_STATUSES)}")
        if self._released:
            return
        record = _read_json(self.registry_path) or {}
        record.update({"status": status, "released_at": _utcnow(), "release_note": note})
        _atomic_write_json(self.registry_path, record)
        _append_history(self.history_path, record)
        try:
            self.registry_path.unlink()
        except OSError:
            pass
        fcntl.flock(self.fd, fcntl.LOCK_UN)
        os.close(self.fd)
        self._released = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release(status="FAILED" if exc_type else "FINISHED")
        return False


def _utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def acquire(
    runtime_dir: os.PathLike | str,
    *,
    cycle_id: str,
    role: str,
    worktree: str,
    command: list[str],
    expected_artifacts: Optional[list[str]] = None,
    reclaim_stale: bool = True,
) -> HeavyLockHandle:
    """Acquire the machine-wide heavy lock or refuse with LockBusyError.

    On refusal the caller records ``NOT_RUN_RESOURCE_CONFLICT`` and
    stops — never spins, never overlaps.
    """
    runtime = Path(runtime_dir)
    runtime.mkdir(parents=True, exist_ok=True)
    lock_path = runtime / LOCK_NAME
    registry_path = runtime / REGISTRY_NAME
    history_path = runtime / HISTORY_NAME

    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        holder = _read_json(registry_path)
        detail = f"held by {holder.get('cycle_id')}/{holder.get('role')} pid {holder.get('pid')}" if holder else "holder unknown"
        raise LockBusyError(f"global heavy lock busy: {detail}")

    # We hold the lock but a registry row may remain from a crashed
    # worker (the OS already freed the flock when it died; the JSON did
    # not get the memo). Reclaim only with BOTH checks, archive first.
    stale = _read_json(registry_path)
    if stale and stale.get("status") == "RUNNING":
        if not _row_genuinely_alive(stale):
            _append_history(history_path, dict(stale, reclaim_reason=_stale_reason(stale)))
            registry_path.unlink(missing_ok=True)
        elif reclaim_stale is False:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
            raise HeavyLockError(
                "registry row RUNNING and alive while lock was free — "
                "CONTROL_STATE_DRIFT; refusing to shadow it"
            )
        else:
            # Alive row but flock was free: the worker lost the lock
            # without releasing (crash between flock-death and registry
            # update is impossible; this is drift). Archive and proceed.
            _append_history(history_path, dict(stale, reclaim_reason="drift_row_alive_lock_free"))
            registry_path.unlink(missing_ok=True)

    owner = {
        "cycle_id": cycle_id,
        "role": role,
        "pid": os.getpid(),
        "process_start_token": process_start_token(os.getpid()),
        "worktree": str(worktree),
        "command_digest": command_digest(command),
        "command": list(command),
        "started_at": _utcnow(),
        "last_heartbeat": _utcnow(),
        "expected_artifacts": list(expected_artifacts or []),
        "status": "RUNNING",
    }
    _atomic_write_json(registry_path, owner)
    return HeavyLockHandle(
        fd=fd,
        lock_path=lock_path,
        registry_path=registry_path,
        history_path=history_path,
        owner=owner,
    )


def _pid_alive(pid) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError, TypeError):
        return False


def _row_genuinely_alive(row: dict) -> bool:
    pid = row.get("pid")
    if not _pid_alive(pid):
        return False
    token = row.get("process_start_token")
    if token is None:
        return False  # unverifiable -> treat as stale, fail closed on shadowing
    return process_start_token(int(pid)) == token


def _stale_reason(row: dict) -> str:
    pid = row.get("pid")
    if not _pid_alive(pid):
        return "pid_dead"
    if row.get("process_start_token") is None:
        return "token_unrecoverable"
    if process_start_token(int(pid)) != row.get("process_start_token"):
        return "pid_reused_token_mismatch"
    return "unknown"


def cleanup_stale(runtime_dir: os.PathLike | str) -> dict:
    """Standalone reconciliation: archive + clear a stale registry row.

    Safe by construction: the flock gate in :func:`acquire` is the real
    authority; this only tidies the bookkeeping and reports what it saw.
    """
    runtime = Path(runtime_dir)
    registry_path = runtime / REGISTRY_NAME
    row = _read_json(registry_path)
    if not row or row.get("status") != "RUNNING":
        return {"action": "none", "reason": "no running row"}
    alive = _row_genuinely_alive(row)
    if alive:
        return {"action": "none", "reason": "row alive (pid + token verified)"}
    reason = _stale_reason(row)
    _append_history(runtime / HISTORY_NAME, dict(row, reclaim_reason=reason))
    registry_path.unlink(missing_ok=True)
    return {"action": "archived_stale", "reason": reason}
