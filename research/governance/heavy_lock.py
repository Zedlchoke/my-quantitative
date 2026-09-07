"""Global heavy-worker lock — machine-wide serialization, OS-enforced.

Handbook §10.3: the one-heavy-job limit is MACHINE-WIDE, not per cycle.
Each A1 counting its own workers is not enough because two cycles can
both see an idle machine. This module makes the limit a mechanism, not a
convention:

- the runtime is SHARED and derived from the repository's git common
  dir (``git rev-parse --git-common-dir`` -> ``<repo-root>/.runtime``):
  every worktree of the repository resolves the SAME lock file, and
  callers CANNOT choose a worktree-local runtime — there is no runtime
  parameter on any public entry point;
- exclusive ``fcntl.flock`` on ``<root>/.runtime/heavy_worker.lock`` (the
  OS releases it automatically if the holder dies — the LOCK cannot go
  stale);
- a registry (``heavy_worker.registry.json``) recording cycle / role /
  PID / process-start token / command digest / worktree / heartbeat /
  expected artifacts / status — the REGISTRY can go stale (a crashed
  worker leaves a RUNNING row), and is reclaimed ONLY after checking
  both PID liveness AND the process-start token, so a reused PID can
  never be mistaken for the original holder;
- **fail-closed drift rule**: a registry row that is ALIVE (pid alive +
  token matches) while the flock is FREE means the bookkeeping lies —
  ``CONTROL_STATE_DRIFT``; acquire refuses (nothing archived, the row is
  left intact for inspection, a human/cleanup decides);
- refusal is ``NOT_RUN_RESOURCE_CONFLICT`` — never spin, never overlap;
- release happens in ``finally`` and records FINISHED / FAILED /
  TECHABORT; history is append-only;
- :func:`cleanup_stale` performs reconciliation WHILE HOLDING the flock
  (it never touches the registry locklessly).

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
CONTROL_STATE_DRIFT = "CONTROL_STATE_DRIFT"

LOCK_NAME = "heavy_worker.lock"
REGISTRY_NAME = "heavy_worker.registry.json"
HISTORY_NAME = "heavy_worker.history.jsonl"

TERMINAL_STATUSES = {"FINISHED", "FAILED", "TECHABORT"}


class LockBusyError(RuntimeError):
    """Another process holds the global heavy lock."""

    verdict = NOT_RUN_RESOURCE_CONFLICT


class HeavyLockError(RuntimeError):
    """Protocol violation — CONTROL_STATE_DRIFT or bad usage; fail closed."""


def shared_runtime_dir() -> Path:
    """The ONE runtime for the whole repository, derived from the git
    common dir so that every worktree resolves the same directory.

    Callers cannot choose a worktree-local runtime — there is no
    parameter for it anywhere on the public surface.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise HeavyLockError(f"cannot resolve git common dir: {exc}") from exc
    if out.returncode != 0 or not out.stdout.strip():
        raise HeavyLockError(
            "not inside a git repository — shared runtime is not derivable"
        )
    common = Path(out.stdout.strip())
    if not common.is_absolute():
        common = Path.cwd() / common
    return common.resolve().parent / ".runtime"


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


def _utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


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


def _open_lock(runtime: Path) -> int:
    runtime.mkdir(parents=True, exist_ok=True)
    fd = os.open(runtime / LOCK_NAME, os.O_RDWR | os.O_CREAT, 0o644)
    return fd


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


def acquire(
    *,
    cycle_id: str,
    role: str,
    worktree: str,
    command: list[str],
    expected_artifacts: Optional[list[str]] = None,
) -> HeavyLockHandle:
    """Acquire the machine-wide heavy lock or refuse.

    - lock busy                         -> LockBusyError
      (verdict NOT_RUN_RESOURCE_CONFLICT)
    - stale RUNNING row, pid dead or
      token mismatch                    -> archived to history, cleared,
      acquisition proceeds (the OS already freed the flock on death)
    - RUNNING row ALIVE (pid + token)
      while the flock was free         -> CONTROL_STATE_DRIFT: refuse,
      archive NOTHING, leave the row for inspection (fail closed)

    The runtime is derived internally from the git common dir — callers
    cannot select a worktree-local runtime.
    """
    runtime = Path(shared_runtime_dir())
    registry_path = runtime / REGISTRY_NAME
    history_path = runtime / HISTORY_NAME

    fd = _open_lock(runtime)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        holder = _read_json(registry_path)
        detail = (
            f"held by {holder.get('cycle_id')}/{holder.get('role')} pid {holder.get('pid')}"
            if holder
            else "holder unknown"
        )
        raise LockBusyError(f"global heavy lock busy: {detail}")

    stale = _read_json(registry_path)
    if stale and stale.get("status") == "RUNNING":
        if _row_genuinely_alive(stale):
            # We hold the flock yet a verifiably-alive row says RUNNING:
            # the bookkeeping lies. Fail closed; archive nothing.
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
            raise HeavyLockError(
                f"{CONTROL_STATE_DRIFT}: registry row RUNNING and alive "
                f"(pid {stale.get('pid')} + start token match) while the flock "
                f"was free — refusing to acquire or archive; reconcile via "
                f"cleanup_stale() with the worker stopped, or inspect manually"
            )
        _append_history(history_path, dict(stale, reclaim_reason=_stale_reason(stale)))
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
        lock_path=runtime / LOCK_NAME,
        registry_path=registry_path,
        history_path=history_path,
        owner=owner,
    )


def cleanup_stale() -> dict:
    """Reconcile the registry WHILE HOLDING the flock.

    - lock held by a live worker      -> report and touch nothing
    - RUNNING row, pid dead / token
      mismatch                        -> archived + cleared (under flock)
    - RUNNING row alive + flock free  -> CONTROL_STATE_DRIFT reported,
      row preserved (never silently cleared)
    """
    runtime = Path(shared_runtime_dir())
    registry_path = runtime / REGISTRY_NAME
    history_path = runtime / HISTORY_NAME

    fd = _open_lock(runtime)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        return {"action": "none", "reason": "lock held — an active worker owns the runtime"}
    try:
        row = _read_json(registry_path)
        if not row or row.get("status") != "RUNNING":
            return {"action": "none", "reason": "no running row"}
        if _row_genuinely_alive(row):
            return {
                "action": "none",
                "reason": (
                    f"{CONTROL_STATE_DRIFT}: row alive (pid {row.get('pid')} + token "
                    "match) while the flock is free — preserved for inspection; "
                    "stop the worker or repair the registry by hand"
                ),
            }
        reason = _stale_reason(row)
        _append_history(history_path, dict(row, reclaim_reason=reason))
        registry_path.unlink(missing_ok=True)
        return {"action": "archived_stale", "reason": reason}
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
