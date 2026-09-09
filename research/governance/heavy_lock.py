"""Global heavy-worker lock — MACHINE-WIDE serialization, OS-enforced.

Scope definition (owner remediation round 2, 2026-09-07) — ONE term
everywhere: **machine-wide**, meaning THIS user account on THIS host.
The runtime lives OUTSIDE any repository (``~/.my-quantitative-governance/
heavy_runtime/``) so that every repository, checkout and worktree on the
machine contends on the SAME lock; a second OS user is out of scope by
declaration (single-user research host). Code and documents (handbook
§10.3, RULES §1 "heavy cap 1 machine-wide", FAMILY_PIPELINE §7 step 32)
all use this single definition. There is no repository-wide mode and no
caller-selected runtime path.

Mechanics:

- exclusive ``fcntl.flock`` on ``heavy_runtime/heavy_worker.lock`` (the
  OS releases it automatically if the holder dies — the LOCK cannot go
  stale);
- a registry (``heavy_worker.registry.json``) recording cycle / role /
  PID / process-start token / command digest / worktree / heartbeat /
  expected artifacts / status. The REGISTRY can lie in three ways, and
  every one of them fails closed as CONTROL_STATE_DRIFT (nothing
  archived, row preserved for inspection):
    1. malformed / unreadable JSON;
    2. RUNNING row with a LIVE pid whose start token is missing or
       unrecoverable;
    3. RUNNING row with a LIVE pid and MATCHING token while the flock
       is free (bookkeeping contradicts the OS).
- reclaim happens ONLY on PROVEN staleness: pid dead, or a DEFINITE
  token mismatch (pid alive but its real token differs — PID reuse).
  Anything less is drift, not proof.
- refusal is ``NOT_RUN_RESOURCE_CONFLICT`` — never spin, never overlap;
- release happens in ``finally`` and records FINISHED / FAILED /
  TECHABORT (FAILED releases SHOULD carry the stderr tail in ``note`` —
  the V16 P0 audit found two FAILED releases with empty notes, whose
  causes were then unrecoverable from artifacts); history is
  append-only;
- :func:`cleanup_stale` performs reconciliation WHILE HOLDING the flock.

Adoption boundary (FAMILY_PIPELINE §11): cycles whose plans preregister
this lock (crypto V16+, forex V7+, stocks V12+). Round-1 lock (repo
runtime via git common-dir) was adopted by CRYPTO-V16 P0 on 2026-09-07
(history: 3 records, 2 FAILED + 1 FINISHED); this round-2 machine-wide
redefinition is a NEW mechanism version that re-adopts when a cycle
actually uses it.
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

RUNTIME_DIRNAME = Path.home() / ".my-quantitative-governance" / "heavy_runtime"
LOCK_NAME = "heavy_worker.lock"
REGISTRY_NAME = "heavy_worker.registry.json"
HISTORY_NAME = "heavy_worker.history.jsonl"

TERMINAL_STATUSES = {"FINISHED", "FAILED", "TECHABORT"}


class LockBusyError(RuntimeError):
    """Another process holds the machine-wide heavy lock."""

    verdict = NOT_RUN_RESOURCE_CONFLICT


class HeavyLockError(RuntimeError):
    """Protocol violation — CONTROL_STATE_DRIFT or bad usage; fail closed."""


def machine_runtime_dir() -> Path:
    """The ONE machine-wide runtime: this user, this host, outside every
    repository. Callers cannot choose a path — there is no parameter."""
    return RUNTIME_DIRNAME


def process_start_token(pid: int) -> Optional[str]:
    """A stable per-process-instance token.

    macOS: ``ps -o lstart=``; Linux: field 22 of /proc/<pid>/stat
    (starttime in clock ticks). A recycled PID produces a different
    token — that is the entire point. Returns None when unrecoverable;
    callers treat that as drift, never as proof of anything.
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


def _load_registry(path: Path) -> tuple[Optional[dict], Optional[str]]:
    """Return (row, error). Missing file is NOT an error (no row yet);
    unparseable or non-object content IS (malformed -> drift)."""
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, None
    except OSError as exc:
        return None, f"unreadable ({exc})"
    try:
        row = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"malformed JSON ({exc})"
    if not isinstance(row, dict):
        return None, "malformed (not a JSON object)"
    return row, None


def _read_json(path: Path) -> Optional[dict]:
    row, _ = _load_registry(path)
    return row


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


def _classify_row(row: dict) -> tuple[str, str]:
    """Classify a RUNNING registry row found while we hold the flock.

    Returns (disposition, reason):
      ("reclaim", ...)  PROVEN stale — pid dead, or DEFINITE token
                        mismatch (PID reused). Safe to archive+clear.
      ("drift", ...)    CONTROL_STATE_DRIFT — the row cannot be proven
                        stale and cannot be trusted. Fail closed.
    """
    if not isinstance(row, dict) or "pid" not in row:
        return "drift", "malformed row (no pid)"
    if not _pid_alive(row.get("pid")):
        return "reclaim", "pid_dead"
    row_token = row.get("process_start_token")
    if row_token is None:
        return "drift", "pid alive with missing start token — unverifiable"
    live_token = process_start_token(int(row["pid"]))
    if live_token is None:
        return "drift", "pid alive; live start token unrecoverable — unverifiable"
    if live_token != row_token:
        return "reclaim", "pid_reused_token_mismatch"
    return "drift", "pid alive + token match while the flock was free"


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


def _open_lock(runtime: Path) -> int:
    runtime.mkdir(parents=True, exist_ok=True)
    return os.open(runtime / LOCK_NAME, os.O_RDWR | os.O_CREAT, 0o644)


def acquire(
    *,
    cycle_id: str,
    role: str,
    worktree: str,
    command: list[str],
    expected_artifacts: Optional[list[str]] = None,
) -> HeavyLockHandle:
    """Acquire the machine-wide heavy lock or refuse.

    - lock busy                -> LockBusyError (verdict
                                  NOT_RUN_RESOURCE_CONFLICT)
    - registry malformed       -> CONTROL_STATE_DRIFT, fail closed,
                                  file preserved
    - RUNNING row PROVEN stale -> archived to history, cleared,
                                  acquisition proceeds
    - anything else (alive row,
      token missing/unrecover-
      able, or alive+matching
      under a free flock)      -> CONTROL_STATE_DRIFT, fail closed,
                                  row preserved

    The runtime is derived internally — callers cannot select one.
    """
    runtime = Path(machine_runtime_dir())
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
        raise LockBusyError(f"machine-wide heavy lock busy: {detail}")

    row, err = _load_registry(registry_path)
    if err is not None:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        raise HeavyLockError(
            f"{CONTROL_STATE_DRIFT}: registry {registry_path} is {err} — "
            f"refusing to acquire or archive; inspect/repaired by hand"
        )
    if row is not None and row.get("status") == "RUNNING":
        disposition, reason = _classify_row(row)
        if disposition == "drift":
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
            raise HeavyLockError(
                f"{CONTROL_STATE_DRIFT}: RUNNING row not provably stale "
                f"({reason}) — refusing to acquire or archive; reconcile via "
                f"cleanup_stale() with the worker stopped, or inspect manually"
            )
        _append_history(history_path, dict(row, reclaim_reason=reason))
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

    - lock held by a live worker      -> report, touch nothing
    - registry malformed              -> CONTROL_STATE_DRIFT reported,
      file preserved (never deleted on a guess)
    - RUNNING row PROVEN stale        -> archived + cleared (under flock)
    - anything else                   -> drift reported, row preserved
    """
    runtime = Path(machine_runtime_dir())
    registry_path = runtime / REGISTRY_NAME
    history_path = runtime / HISTORY_NAME

    fd = _open_lock(runtime)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        return {"action": "none", "reason": "lock held — an active worker owns the runtime"}
    try:
        row, err = _load_registry(registry_path)
        if err is not None:
            return {
                "action": "none",
                "reason": f"{CONTROL_STATE_DRIFT}: registry is {err} — preserved "
                          f"for inspection; repair by hand",
            }
        if row is None or row.get("status") != "RUNNING":
            return {"action": "none", "reason": "no running row"}
        disposition, reason = _classify_row(row)
        if disposition == "drift":
            return {
                "action": "none",
                "reason": f"{CONTROL_STATE_DRIFT}: {reason} — row preserved "
                          f"for inspection",
            }
        _append_history(history_path, dict(row, reclaim_reason=reason))
        registry_path.unlink(missing_ok=True)
        return {"action": "archived_stale", "reason": reason}
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


# ------------------------------------------------------- inspection (MDP-V1 M0)

def flock_state(lock_path: Path) -> str:
    """Read-only probe: 'held' when ANOTHER process holds the flock, 'free'
    when it could be taken (immediately released again). Never blocks."""
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    except OSError as exc:
        return f"unopenable ({exc})"
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return "held"
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass
        return "free"
    finally:
        os.close(fd)


VERDICT_HELD_PROVEN = "HELD_PROVEN"
VERDICT_FREE_PROVEN = "FREE_PROVEN"
VERDICT_DRIFT = CONTROL_STATE_DRIFT


def inspect() -> dict:
    """Classify the machine-wide heavy lock into EXACTLY one verdict:
    HELD_PROVEN | FREE_PROVEN | CONTROL_STATE_DRIFT, each with an evidence
    object. Ambiguous state NEVER becomes FREE (fail closed); this is a
    read-only diagnostic — it never reclaims, archives or repairs.

    HELD_PROVEN: RUNNING registry row + pid alive + process-start token
                 matches the live holder + the flock is actually held.
    FREE_PROVEN: no registry row AND the lock file is not flocked.
    everything else (dead pid, token mismatch / PID reuse, missing or
    unrecoverable token, malformed registry, registry row under a free
    flock, flocked file without a row) -> CONTROL_STATE_DRIFT.
    """
    runtime = Path(machine_runtime_dir())
    lock_path = runtime / LOCK_NAME
    registry_path = runtime / REGISTRY_NAME

    def evidence(pid=None, pid_alive=None, lstart=None, row_token=None,
                 token_match=None, flock=None, row=None, note=None) -> dict:
        ev = {
            "pid": pid,
            "pid_alive": pid_alive,
            "lstart": lstart,
            "registry_process_start_token": row_token,
            "token_match": token_match,
            "flock_state": flock,
            "registry_path": str(registry_path),
            "lock_path": str(lock_path),
            "liveness_method": "os.kill(pid, 0) + ps -p PID -o lstart= token comparison",
        }
        if row is not None:
            ev["registry_row"] = row
        if note is not None:
            ev["note"] = note
        return ev

    row, err = _load_registry(registry_path)
    if err is not None:
        return {
            "verdict": VERDICT_DRIFT,
            "reason": f"registry malformed ({err}) — fail closed, preserved for inspection",
            "evidence": evidence(flock=flock_state(lock_path), row=None),
        }

    flock = flock_state(lock_path)
    if row is None:
        if flock == "free":
            return {"verdict": VERDICT_FREE_PROVEN,
                    "reason": "no registry row and the lock file is not flocked",
                    "evidence": evidence(pid=None, pid_alive=False, lstart=None,
                                         row_token=None, token_match=None, flock=flock)}
        return {
            "verdict": VERDICT_DRIFT,
            "reason": "lock file is flocked but no registry row exists — holder unknown",
            "evidence": evidence(flock=flock),
        }

    # a registry row exists — only a RUNNING row with full proof may be HELD
    status = row.get("status")
    pid = row.get("pid")
    if status != "RUNNING":
        return {
            "verdict": VERDICT_DRIFT,
            "reason": f"registry row status {status!r} (not RUNNING) — bookkeeping "
                      "contradicts a clean lock state",
            "evidence": evidence(pid=pid, flock=flock, row=row),
        }
    if not isinstance(pid, int):
        return {
            "verdict": VERDICT_DRIFT,
            "reason": "malformed RUNNING row (pid missing or not an int)",
            "evidence": evidence(pid=pid, flock=flock, row=row),
        }
    alive = _pid_alive(pid)
    live_token = process_start_token(pid) if alive else None
    row_token = row.get("process_start_token")
    token_match = bool(alive and live_token and row_token and live_token == row_token)
    ev = evidence(pid=pid, pid_alive=alive, lstart=live_token, row_token=row_token,
                  token_match=token_match if alive else None, flock=flock, row=row)
    if alive and token_match and flock == "held":
        return {"verdict": VERDICT_HELD_PROVEN,
                "reason": f"pid {pid} alive, process-start token matches the registry "
                          f"row, and the flock is held ({row.get('cycle_id')}/{row.get('role')})",
                "evidence": ev}
    if not alive:
        return {"verdict": VERDICT_DRIFT,
                "reason": f"RUNNING registry row pid {pid} is dead — stale registry "
                          "(reclaim only per round-2 discipline, never by inspection)",
                "evidence": ev}
    if not row_token or live_token is None:
        return {"verdict": VERDICT_DRIFT,
                "reason": "pid alive with missing or unrecoverable process-start "
                          "token — liveness unverifiable",
                "evidence": ev}
    if not token_match:
        return {"verdict": VERDICT_DRIFT,
                "reason": f"process-start token mismatch for pid {pid} (PID reuse or "
                          "stale registry row) — ambiguity is never FREE",
                "evidence": ev}
    return {"verdict": VERDICT_DRIFT,
            "reason": "pid alive + token match while the flock is free — bookkeeping "
                      "contradicts the OS",
            "evidence": ev}
