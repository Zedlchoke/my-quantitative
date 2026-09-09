"""MDP-V1 M0 - reconciled job view + tri-state lock inspection.

Hermetic only. Every test runs against an ISOLATED runtime dir via the same
override mechanism tests/test_heavy_lock.py uses (patch the DERIVATION, not a
caller parameter) and a tmp scheduler journal. The live machine runtime
(~/.my-quantitative-governance/heavy_runtime) is NEVER touched here.

Proven here:
- `job list` is ONE reconciled view: scheduler journal UNION live heavy-lock
  registry, each row labeled with its source; the lock row carries liveness
  evidence (pid alive, process-start token match);
- a dead-pid or token-mismatch (PID reuse) lock row is surfaced as
  CONTROL_STATE_DRIFT - never dropped silently; a malformed lock registry is
  a drift row, never a crash;
- `locks inspect` returns EXACTLY one of HELD_PROVEN / FREE_PROVEN /
  CONTROL_STATE_DRIFT with an evidence object; ambiguous never becomes FREE;
- a hermetic REAL-lock integration test: a subprocess acquires the lock in
  the isolated runtime, the reconciled job view shows the holder with source
  heavy_lock + liveness evidence, the holder releases, and the terminal
  FINISHED release shows in the view's history tail.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "research"))

from governance import heavy_lock, scheduler  # noqa: E402
from governance.heavy_lock import (  # noqa: E402
    CONTROL_STATE_DRIFT,
    HISTORY_NAME,
    REGISTRY_NAME,
    acquire,
    inspect,
    process_start_token,
)

MY_PID = __import__("os").getpid()


@pytest.fixture()
def runtime(tmp_path, monkeypatch):
    """Hermetic machine runtime: patch the DERIVATION, not a caller param."""
    target = tmp_path / "machine_runtime"
    monkeypatch.setattr(heavy_lock, "machine_runtime_dir", lambda: target)
    monkeypatch.setattr(heavy_lock, "RUNTIME_DIRNAME", target)
    return target


def _write_registry(runtime: Path, row: dict):
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / REGISTRY_NAME).write_text(json.dumps(row), encoding="utf-8")


def _running_row(pid, token, cycle="LOCK-CYCLE", status="RUNNING"):
    return {
        "cycle_id": cycle, "role": "P0_BUILD", "pid": pid,
        "process_start_token": token, "worktree": "/wt/lock",
        "command": ["python", "-m", "driver"], "command_digest": "0" * 64,
        "started_at": "2026-09-09T00:00:00Z",
        "last_heartbeat": "2026-09-09T00:00:00Z",
        "expected_artifacts": [], "status": status,
    }


def _view(runtime: Path, tmp_path: Path) -> dict:
    return scheduler.reconciled_jobs(journal_path=tmp_path / "jobs.json")


# ------------------------------------------------------- reconciled job view

def test_job_view_unions_scheduler_and_heavy_lock_with_liveness(runtime, tmp_path):
    s = scheduler.Scheduler(journal_path=tmp_path / "jobs.json")
    s.admit("SCHED-CYCLE", "P0_BUILD", "build")
    _write_registry(runtime, _running_row(MY_PID, process_start_token(MY_PID)))
    view = _view(runtime, tmp_path)
    assert view["schema"] == scheduler.JOB_VIEW_SCHEMA
    sources = {j["source"] for j in view["jobs"]}
    assert sources == {"scheduler", "heavy_lock"}, "the union must carry BOTH sources"
    lock_rows = [j for j in view["jobs"] if j["source"] == "heavy_lock"]
    assert len(lock_rows) == 1
    row = lock_rows[0]
    assert row["cycle_id"] == "LOCK-CYCLE"
    assert row["status"] == "RUNNING"
    liveness = row["liveness"]
    assert liveness["pid"] == MY_PID
    assert liveness["pid_alive"] is True
    assert liveness["token_match"] is True
    assert liveness["registry_process_start_token"] == process_start_token(MY_PID)
    assert row["control_state_drift"] is None
    assert row["evidence"]["registry_path"].endswith(REGISTRY_NAME)


def test_job_view_read_only_never_creates_state(runtime, tmp_path):
    view = _view(runtime, tmp_path)
    assert view["jobs"] == []
    assert not (tmp_path / "jobs.json").exists(), "reading the view must not create a journal"
    assert not (runtime / REGISTRY_NAME).exists()
    assert "absent" in view["notes"][0]


def test_dead_pid_lock_row_is_surfaced_as_drift_never_dropped(runtime, tmp_path):
    dead = subprocess.Popen(["true"])
    dead_pid = dead.pid
    dead.wait()
    _write_registry(runtime, _running_row(dead_pid, "ps:DEAD-HOLDER-TOKEN"))
    view = _view(runtime, tmp_path)
    lock_rows = [j for j in view["jobs"] if j["source"] == "heavy_lock"]
    assert len(lock_rows) == 1, "a stale lock row must be surfaced, not dropped"
    row = lock_rows[0]
    assert row["liveness"]["pid_alive"] is False
    assert row["control_state_drift"] == CONTROL_STATE_DRIFT or \
        CONTROL_STATE_DRIFT in row["control_state_drift"]
    assert "dead pid" in row["control_state_drift"]


def test_pid_reuse_token_mismatch_is_drift(runtime, tmp_path):
    """Same pid alive, but its real process-start token differs from the
    registry row (PID reused since the row was written) -> CONTROL_STATE_DRIFT."""
    _write_registry(runtime, _running_row(MY_PID, "ps:FAKE-TOKEN-FROM-A-DEAD-PROCESS"))
    view = _view(runtime, tmp_path)
    row = [j for j in view["jobs"] if j["source"] == "heavy_lock"][0]
    assert row["liveness"]["pid_alive"] is True
    assert row["liveness"]["token_match"] is False
    assert row["control_state_drift"] is not None
    assert "token mismatch" in row["control_state_drift"]


def test_missing_token_on_live_pid_is_drift(runtime, tmp_path):
    _write_registry(runtime, _running_row(MY_PID, None))
    view = _view(runtime, tmp_path)
    row = [j for j in view["jobs"] if j["source"] == "heavy_lock"][0]
    assert row["control_state_drift"] is not None
    assert "token" in row["control_state_drift"]


def test_malformed_lock_registry_is_a_drift_row_not_a_crash(runtime, tmp_path):
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / REGISTRY_NAME).write_text("{not json", encoding="utf-8")
    s = scheduler.Scheduler(journal_path=tmp_path / "jobs.json")
    s.admit("SCHED-CYCLE", "P0_BUILD", "build")
    view = _view(runtime, tmp_path)
    lock_rows = [j for j in view["jobs"] if j["source"] == "heavy_lock"]
    assert len(lock_rows) == 1
    assert lock_rows[0]["status"] == CONTROL_STATE_DRIFT
    assert "unparseable" in lock_rows[0]["note"] or "malformed" in lock_rows[0]["note"]
    # the scheduler rows are still visible — one broken source never hides the other
    assert [j for j in view["jobs"] if j["source"] == "scheduler"]


def test_scheduler_journal_unparseable_is_drift_row(runtime, tmp_path):
    jp = tmp_path / "jobs.json"
    jp.write_text("{broken", encoding="utf-8")
    view = scheduler.reconciled_jobs(journal_path=jp)
    rows = [j for j in view["jobs"] if j["source"] == "scheduler"]
    assert rows and rows[0]["status"] == CONTROL_STATE_DRIFT


# --------------------------------------------------- tri-state locks inspect

def test_inspect_free_proven_on_empty_runtime(runtime):
    report = inspect()
    assert report["verdict"] == "FREE_PROVEN"
    ev = report["evidence"]
    assert ev["registry_path"].endswith(REGISTRY_NAME)
    assert ev["lock_path"].endswith("heavy_worker.lock")
    assert ev["flock_state"] == "free"


def test_inspect_held_proven_while_acquired_then_free_after_release(runtime):
    with acquire(cycle_id="HOLD-C1", role="worker", worktree="/wt/h",
                 command=["python", "-m", "w"]) as handle:
        assert handle.owner["pid"] == MY_PID
        report = inspect()
        assert report["verdict"] == "HELD_PROVEN"
        ev = report["evidence"]
        assert ev["pid"] == MY_PID
        assert ev["pid_alive"] is True
        assert ev["token_match"] is True
        assert ev["flock_state"] == "held"
        assert ev["lstart"] == process_start_token(MY_PID)
        assert ev["registry_row"]["cycle_id"] == "HOLD-C1"
    report = inspect()
    assert report["verdict"] == "FREE_PROVEN", "a released lock must inspect FREE"


def test_inspect_drift_dead_pid(runtime):
    dead = subprocess.Popen(["true"])
    dead_pid = dead.pid
    dead.wait()
    _write_registry(runtime, _running_row(dead_pid, "ps:GHOST"))
    report = inspect()
    assert report["verdict"] == CONTROL_STATE_DRIFT
    assert report["evidence"]["pid_alive"] is False


def test_inspect_drift_pid_reuse(runtime):
    _write_registry(runtime, _running_row(MY_PID, "ps:TOKEN-OF-A-DEAD-PROCESS"))
    report = inspect()
    assert report["verdict"] == CONTROL_STATE_DRIFT
    assert report["evidence"]["token_match"] is False


def test_inspect_drift_malformed_registry(runtime):
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / REGISTRY_NAME).write_text("[], not an object", encoding="utf-8")
    report = inspect()
    assert report["verdict"] == CONTROL_STATE_DRIFT


def test_inspect_drift_alive_row_under_free_flock(runtime):
    """pid alive + real matching token while the flock is FREE: the
    bookkeeping contradicts the OS -> drift, never HELD, never FREE."""
    _write_registry(runtime, _running_row(MY_PID, process_start_token(MY_PID)))
    report = inspect()
    assert report["verdict"] == CONTROL_STATE_DRIFT
    assert "flock is free" in report["reason"] or "free" in report["reason"]


def test_inspect_drift_flocked_file_without_registry_row(runtime, monkeypatch):
    # hold the flock from a second process (this one must not hold it itself)
    runtime.mkdir(parents=True, exist_ok=True)
    holder_code = (
        "import fcntl, os, time, sys\n"
        f"fd = os.open({str(runtime / 'heavy_worker.lock')!r}, os.O_CREAT | os.O_RDWR)\n"
        "fcntl.flock(fd, fcntl.LOCK_EX)\n"
        "print('HELD', flush=True)\n"
        "time.sleep(5)\n"
    )
    proc = subprocess.Popen([sys.executable, "-c", holder_code],
                            stdout=subprocess.PIPE, text=True)
    try:
        assert proc.stdout.readline().strip() == "HELD"
        report = inspect()
        assert report["verdict"] == CONTROL_STATE_DRIFT, \
            "a flocked file with no registry row must never be FREE (holder unknown)"
    finally:
        proc.kill()
        proc.wait()


# --------------------------------------- hermetic REAL-lock integration test

def _spawn_holder(runtime: Path, cycle="VIEW-CYCLE"):
    """Acquire the REAL flock machinery in a subprocess against the ISOLATED
    runtime dir, wait for the parent's newline, then release FINISHED."""
    code = (
        "import sys, time, pathlib;\n"
        f"sys.path.insert(0, {str(REPO_ROOT)!r});\n"
        "from research.governance import heavy_lock;\n"
        f"rt = pathlib.Path({str(runtime)!r});\n"
        "heavy_lock.machine_runtime_dir = lambda: rt;\n"
        "heavy_lock.RUNTIME_DIRNAME = rt;\n"
        f"h = heavy_lock.acquire(cycle_id={cycle!r}, role='P0_BULK',\n"
        "    worktree='/wt/view', command=['python3','driver.py'],\n"
        "    expected_artifacts=['out.jsonl']);\n"
        "print('ACQUIRED', flush=True);\n"
        "sys.stdin.readline();\n"
        "h.release(status='FINISHED', note='integration test complete');\n"
        "print('RELEASED', flush=True);\n"
    )
    return subprocess.Popen([sys.executable, "-c", code],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)


def test_real_lock_job_view_shows_holder_then_terminal_release(runtime, tmp_path):
    """The full reconciliation story against a REAL lock in an ISOLATED dir:
    holder visible with source heavy_lock + proven liveness; after release,
    the terminal FINISHED release is visible in the view's history tail."""
    proc = _spawn_holder(runtime)
    try:
        assert proc.stdout.readline().strip() == "ACQUIRED"
        view = _view(runtime, tmp_path)
        holders = [j for j in view["jobs"]
                   if j["source"] == "heavy_lock" and j.get("cycle_id") == "VIEW-CYCLE"]
        assert len(holders) == 1, "job list must show the live lock holder"
        row = holders[0]
        assert row["status"] == "RUNNING"
        assert row["liveness"]["pid"] == proc.pid
        assert row["liveness"]["pid_alive"] is True
        assert row["liveness"]["token_match"] is True, \
            "the exact live holder must be proven by the process-start token"
        assert row["control_state_drift"] is None

        proc.stdin.write("\n")
        proc.stdin.flush()
        assert proc.stdout.readline().strip() == "RELEASED"
        proc.wait(timeout=10)

        view_after = _view(runtime, tmp_path)
        assert not [j for j in view_after["jobs"]
                    if j["source"] == "heavy_lock" and j.get("status") == "RUNNING"], \
            "after release no RUNNING lock row may remain"
        tail = view_after["heavy_lock_history_tail"]
        assert tail and tail[-1]["status"] == "FINISHED", \
            "the terminal release must show in the reconciled view's history tail"
        assert tail[-1]["cycle_id"] == "VIEW-CYCLE"
        assert tail[-1]["release_note"] == "integration test complete"
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)
