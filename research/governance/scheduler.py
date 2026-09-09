"""Job scheduler with bounded retry, admission and crash recovery (SHV1 sec7.4).

Machine-wide invariants honored here:
- heavy admission inspects the machine-wide heavy lock (research.governance
  .heavy_lock); contention is NOT_RUN_RESOURCE_CONFLICT - never spin, never
  contention, and it does NOT consume a scientific attempt;
- job state is persisted to a journal OUTSIDE every repository
  (~/.my-quantitative-governance/heavy_runtime/scheduler_jobs.json) on every
  transition, so retry state survives a controller restart;
- deterministic failures execute ONCE (CODE_OR_SCHEMA_ERROR, the V12
  fromisoformat fixture) - never retry, never backoff.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Callable, Optional

from governance import retry_classifier as rc

DEFAULT_JOURNAL = Path.home() / ".my-quantitative-governance" / "heavy_runtime" / "scheduler_jobs.json"

CONTROL_STATE_DRIFT = "CONTROL_STATE_DRIFT"


class Scheduler:
    def __init__(self, journal_path: Optional[os.PathLike] = None,
                 sleep: Callable[[float], None] = time.sleep,
                 now: Callable[[], float] = time.time):
        self.journal = Path(journal_path) if journal_path else DEFAULT_JOURNAL
        self._sleep = sleep
        self._now = now
        if not self.journal.exists():
            self.journal.parent.mkdir(parents=True, exist_ok=True)
            self._write({"schema": "scheduler_jobs@1", "jobs": []})

    # ------------------------------------------------------------- journal
    def _read(self) -> dict:
        return json.loads(self.journal.read_bytes().decode("utf-8"))

    def _write(self, state: dict) -> None:
        payload = (json.dumps(state, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
        tmp = self.journal.with_name(self.journal.name + f".tmp.{os.getpid()}")
        with open(tmp, "wb") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, self.journal)

    def _update(self, job: dict) -> None:
        state = self._read()
        jobs = [j for j in state["jobs"] if j["job_id"] != job["job_id"]]
        jobs.append(job)
        state["jobs"] = jobs
        self._write(state)

    def list_jobs(self) -> list:
        return self._read()["jobs"]

    def get_job(self, job_id: str) -> Optional[dict]:
        for j in self._read()["jobs"]:
            if j["job_id"] == job_id:
                return j
        return None

    # ------------------------------------------------------------- admission
    @staticmethod
    def command_digest(owner_cycle: str, role: str, command: str) -> str:
        return hashlib.sha256(f"{owner_cycle}|{role}|{command}".encode()).hexdigest()

    def admit(self, owner_cycle: str, role: str, command: str,
              lock_inspector: Optional[Callable[[], bool]] = None) -> dict:
        """Create a job record; refuses (fail closed) if the heavy lock is held.

        `lock_inspector` returns True when the machine-wide heavy lock is BUSY.
        Production passes heavy_lock.is_busy; tests inject fakes.
        """
        if lock_inspector and lock_inspector():
            job = self._record(owner_cycle, role, command, status="WAITING",
                               verdict="NOT_RUN_RESOURCE_CONFLICT",
                               last_classification={"kind": rc.RESOURCE_BUSY,
                                                    "detail": "heavy lock held at admission"},
                               note="queued without consuming a scientific attempt (sec7.4)")
            return job
        return self._record(owner_cycle, role, command, status="ADMITTED")

    def _record(self, owner_cycle, role, command, **extra) -> dict:
        job = {
            "job_id": f"{owner_cycle}/{role}/{self.command_digest(owner_cycle, role, command)[:12]}",
            "owner_cycle": owner_cycle,
            "role": role,
            "command_digest": self.command_digest(owner_cycle, role, command),
            "attempt": 0,
            "max_attempts": rc.TRANSIENT_MAX_ATTEMPTS,
            "started_at": self._now(),
            "last_heartbeat": self._now(),
            "resources": {"heavy_lock": "machine-wide"},
            "status": "ADMITTED",
            "verdict": None,
            "last_classification": None,
            "note": None,
        }
        job.update(extra)
        self._update(job)
        return job

    # ------------------------------------------------------------- execution
    def run_job(self, owner_cycle: str, role: str, fn: Callable[[], object],
                lock_inspector: Optional[Callable[[], bool]] = None) -> dict:
        """Execute fn under the taxonomy. Returns the final job record.

        - CODE_OR_SCHEMA_ERROR / DATA_AUTHORITY_FAILURE: executed once, FAILED, no retry
        - HASH_OR_CONTRACT_DRIFT: executed once, BLOCKED hard stop
        - TRANSIENT_TRANSPORT: bounded retries with frozen backoff, then FAILED
        - RESOURCE_BUSY (lock busy at start): WAITING, NOT_RUN_RESOURCE_CONFLICT,
          attempt counter untouched
        - OPERATOR_CANCELLED: CANCELLED, clean release
        """
        job = self.admit(owner_cycle, role, getattr(fn, "command", fn.__name__),
                         lock_inspector=lock_inspector)
        if job["status"] == "WAITING":
            return job

        attempt = 0
        while True:
            attempt += 1
            job["attempt"] = attempt
            job["status"] = "RUNNING"
            job["last_heartbeat"] = self._now()
            self._update(job)
            try:
                result = fn()
                job["status"] = "FINISHED"
                job["verdict"] = "FINISHED"
                job["last_classification"] = {"kind": None, "detail": f"result: {str(result)[:120]}"}
                job["last_heartbeat"] = self._now()
                self._update(job)
                return job
            except BaseException as exc:  # noqa: BLE001 - classified below
                if isinstance(exc, KeyboardInterrupt):
                    cls = rc._policy(rc.OPERATOR_CANCELLED, "operator interrupt")
                else:
                    cls = rc.classify_exception(exc)
                job["last_classification"] = {"kind": cls.kind, "detail": cls.detail[:300]}
                job["last_heartbeat"] = self._now()

                if cls.hard_stop:
                    job["status"] = "BLOCKED"
                    job["verdict"] = "HASH_OR_CONTRACT_DRIFT_HARD_STOP"
                    self._update(job)
                    return job
                if cls.terminal:
                    # the V12 fixture class: executed exactly once, never retried
                    job["status"] = "FAILED"
                    job["verdict"] = f"FAILED_{cls.kind}"
                    self._update(job)
                    return job
                if cls.kind == rc.OPERATOR_CANCELLED:
                    job["status"] = "CANCELLED"
                    job["verdict"] = "OPERATOR_CANCELLED"
                    self._update(job)
                    return job
                if cls.kind == rc.RESOURCE_BUSY:
                    job["attempt"] -= 1  # busy does NOT consume a scientific attempt
                    job["status"] = "WAITING"
                    job["verdict"] = "NOT_RUN_RESOURCE_CONFLICT"
                    self._update(job)
                    return job
                if cls.kind == rc.RATE_LIMITED:
                    job["attempt"] -= 1
                    job["status"] = "WAITING"
                    job["verdict"] = f"RATE_LIMITED_RETRY_AFTER={cls.retry_after}"
                    self._update(job)
                    return job
                # TRANSIENT_TRANSPORT: bounded
                if attempt >= job["max_attempts"]:
                    job["status"] = "FAILED"
                    job["verdict"] = f"FAILED_{rc.TRANSIENT_TRANSPORT}_EXHAUSTED_{attempt}"
                    self._update(job)
                    return job
                delay = cls.backoff_hint[min(attempt - 1, len(cls.backoff_hint) - 1)]
                job["status"] = "WAITING_RETRY"
                job["note"] = f"transient backoff {delay}s (bounded, frozen limit {job['max_attempts']})"
                self._update(job)
                self._sleep(delay)

    # ------------------------------------------------------------- recovery
    def recover_stale_running(self, alive: Callable[[int], bool]) -> list:
        """Mark RUNNING rows whose owning process is proven dead as FAILED.

        Reclaims only on PROVEN pid-dead (heavy_lock round-2 discipline) -
        never on heartbeat age alone. Returns the recovered job ids.
        """
        recovered = []
        state = self._read()
        for job in state["jobs"]:
            pid = job.get("pid")
            if job["status"] == "RUNNING" and isinstance(pid, int) and not alive(pid):
                job["status"] = "FAILED"
                job["verdict"] = "CRASH_RECOVERED_PID_DEAD"
                job["last_classification"] = {
                    "kind": rc.CODE_OR_SCHEMA_ERROR,
                    "detail": f"controller restart found RUNNING row with proven-dead pid {pid}",
                }
                recovered.append(job["job_id"])
        if recovered:
            self._write(state)
        return recovered

    def cancel(self, job_id: str) -> str:
        job = self.get_job(job_id)
        if job is None:
            return f"NOT_FOUND {job_id}"
        if job["status"] in ("FINISHED", "FAILED", "CANCELLED", "BLOCKED"):
            return f"TERMINAL_ALREADY {job_id}:{job['status']}"
        job["status"] = "CANCELLED"
        job["verdict"] = "OPERATOR_CANCELLED"
        job["last_classification"] = {"kind": rc.OPERATOR_CANCELLED,
                                      "detail": "clean resource release, recorded cancellation"}
        self._update(job)
        return f"CANCELLED {job_id}"


def list_jobs(journal_path: Optional[os.PathLike] = None) -> list:
    return Scheduler(journal_path=journal_path).list_jobs()


def cancel_job(job_id: str, journal_path: Optional[os.PathLike] = None) -> str:
    return Scheduler(journal_path=journal_path).cancel(job_id)


# ----------------------------------------------- reconciled job view (MDP-V1 M0)

JOB_VIEW_SCHEMA = "job_view@1"
LIVENESS_METHOD = "os.kill(pid, 0) + ps -p PID -o lstart= compared to registry process_start_token"


def reconciled_jobs(journal_path: Optional[os.PathLike] = None) -> dict:
    """ONE reconciled view: scheduler journal UNION live heavy-lock registry.

    MDP-V1 M0 (PLAN sec3.2): silent divergence between the scheduler journal
    and machine-wide heavy-lock ownership is forbidden. Every row is labeled
    with its source ("scheduler" / "heavy_lock") and the heavy-lock row
    carries liveness evidence (pid alive, live process-start token, token
    match). A dead-pid or token-mismatch lock row is surfaced as
    CONTROL_STATE_DRIFT — never dropped, never guessed away.

    Read-only. This view is NOT a second writable authority: the scheduler
    journal stays written by controllers, the lock registry by
    heavy_lock.acquire/heartbeat/release; the union is derived on read.
    The journal file is never created by this function.
    """
    from governance import heavy_lock as hl

    jp = Path(journal_path) if journal_path else DEFAULT_JOURNAL
    notes = []
    jobs: list = []
    if jp.exists():
        try:
            state = json.loads(jp.read_bytes().decode("utf-8"))
            jobs = [{"source": "scheduler", **job} for job in state.get("jobs", [])]
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError) as exc:
            jobs = [{"source": "scheduler", "job_id": "JOURNAL_DRIFT",
                     "status": CONTROL_STATE_DRIFT,
                     "note": f"scheduler journal unparseable, preserved unread ({exc})"}]
    else:
        notes.append(f"scheduler journal absent at {jp} (no controller has run here)")

    runtime = Path(hl.machine_runtime_dir())
    registry_path = runtime / hl.REGISTRY_NAME
    lock_path = runtime / hl.LOCK_NAME
    history_path = runtime / hl.HISTORY_NAME

    lock_row, err = hl._load_registry(registry_path)
    if err is not None:
        jobs.append({
            "source": "heavy_lock", "job_id": "HEAVY_LOCK_DRIFT",
            "status": CONTROL_STATE_DRIFT,
            "note": f"heavy-lock registry {err} — fail closed, preserved for inspection",
            "evidence": {"registry_path": str(registry_path), "lock_path": str(lock_path)},
        })
    elif lock_row is not None:
        pid = lock_row.get("pid")
        alive = hl._pid_alive(pid) if isinstance(pid, int) else False
        live_token = hl.process_start_token(int(pid)) if (alive and isinstance(pid, int)) else None
        row_token = lock_row.get("process_start_token")
        token_match = bool(alive and live_token and row_token and live_token == row_token)
        drift = None
        if lock_row.get("status") != "RUNNING":
            drift = f"registry row status {lock_row.get('status')!r} (not RUNNING)"
        elif not isinstance(pid, int):
            drift = "malformed row (pid missing or not an int)"
        elif not alive:
            drift = f"dead pid {pid} — stale registry row (CONTROL_STATE_DRIFT, never dropped silently)"
        elif not row_token or live_token is None:
            drift = "pid alive with missing/unrecoverable process-start token"
        elif not token_match:
            drift = f"process-start token mismatch for pid {pid} (PID reuse or stale row)"
        jobs.append({
            "source": "heavy_lock",
            "job_id": (f"heavy-lock/{lock_row.get('cycle_id')}/{lock_row.get('role')}"
                       if lock_row.get("cycle_id") else "heavy-lock/unknown"),
            "cycle_id": lock_row.get("cycle_id"),
            "role": lock_row.get("role"),
            "status": lock_row.get("status"),
            "command": lock_row.get("command"),
            "worktree": lock_row.get("worktree"),
            "started_at": lock_row.get("started_at"),
            "last_heartbeat": lock_row.get("last_heartbeat"),
            "liveness": {
                "pid": pid,
                "pid_alive": alive,
                "live_process_start_token": live_token,
                "registry_process_start_token": row_token,
                "token_match": token_match if alive else None,
                "method": LIVENESS_METHOD,
            },
            "control_state_drift": drift,
            "evidence": {"registry_path": str(registry_path), "lock_path": str(lock_path)},
        })

    history_tail = []
    if history_path.exists():
        try:
            lines = history_path.read_text(encoding="utf-8").splitlines()
            history_tail = [json.loads(l) for l in lines[-3:] if l.strip()]
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            notes.append(f"heavy-lock history tail unreadable ({exc})")

    return {
        "schema": JOB_VIEW_SCHEMA,
        "journal": str(jp),
        "jobs": jobs,
        "heavy_lock_history_tail": history_tail,
        "notes": notes,
    }
