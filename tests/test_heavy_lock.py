"""Tests for the machine-wide heavy lock (round-2 remediation).

Owner remediation round 2 (2026-09-07):
- ONE scope definition everywhere: machine-wide = this user on this
  host; runtime lives OUTSIDE every repository (~/.my-quantitative-
  governance/heavy_runtime) — cross-repository/cross-worktree
  contention is proven;
- registry malformed/unreadable => CONTROL_STATE_DRIFT, fail closed
  (file preserved, nothing archived);
- RUNNING row with a LIVE pid whose token is missing or unrecoverable
  => CONTROL_STATE_DRIFT (NOT reclaimable);
- reclaim ONLY on PROVEN pid-dead or DEFINITE token mismatch;
- no public entry point accepts a runtime path;
- FAILED releases should carry a note (V16 P0 audit: two FAILED
  releases with empty notes left causes unrecoverable).
"""

from __future__ import annotations

import inspect
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from research.governance import heavy_lock
from research.governance.heavy_lock import (
    CONTROL_STATE_DRIFT,
    HISTORY_NAME,
    LOCK_NAME,
    REGISTRY_NAME,
    HeavyLockError,
    LockBusyError,
    NOT_RUN_RESOURCE_CONFLICT,
    acquire,
    cleanup_stale,
    command_digest,
    machine_runtime_dir,
    process_start_token,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def runtime(tmp_path, monkeypatch):
    """Hermetic machine runtime: patch the DERIVATION, not a caller param."""
    target = tmp_path / "machine_runtime"
    monkeypatch.setattr(heavy_lock, "machine_runtime_dir", lambda: target)
    monkeypatch.setattr(heavy_lock, "RUNTIME_DIRNAME", target)
    return target


def _spawn_holder(runtime: Path, cycle="TEST-CYCLE", life="time.sleep(120)"):
    code = (
        "import sys, time, pathlib;"
        f"sys.path.insert(0, {str(REPO_ROOT)!r});"
        "from research.governance import heavy_lock;"
        f"rt = pathlib.Path({str(runtime)!r});"
        "heavy_lock.machine_runtime_dir = lambda: rt;"
        "heavy_lock.RUNTIME_DIRNAME = rt;"
        "h = heavy_lock.acquire(cycle_id=%r, role='holder', "
        "worktree='/wt/holder', command=['python3','holder.py'], "
        "expected_artifacts=['out.jsonl']);"
        "print('ACQUIRED', flush=True);" % cycle
        + life
    )
    return subprocess.Popen(
        [sys.executable, "-c", code], stdout=subprocess.PIPE, text=True
    )


def _wait_acquired(proc):
    assert proc.stdout is not None
    assert proc.stdout.readline().strip() == "ACQUIRED"


def _write_registry(runtime: Path, row: dict):
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / REGISTRY_NAME).write_text(json.dumps(row), encoding="utf-8")


def _running_row(pid, token):
    return {
        "cycle_id": "GHOST", "role": "old", "pid": pid,
        "process_start_token": token, "worktree": "/wt/ghost",
        "command_digest": "0" * 64,
        "started_at": "2026-01-01T00:00:00Z",
        "last_heartbeat": "2026-01-01T00:00:00Z",
        "expected_artifacts": [], "status": "RUNNING",
    }


# ------------------------------------------------------------- basic use

def test_acquire_writes_registry_with_token_and_digest(runtime):
    with acquire(
        cycle_id="C1", role="A1", worktree="/wt/x",
        command=["python", "-m", "driver"], expected_artifacts=["a.jsonl"],
    ) as handle:
        row = json.loads((runtime / REGISTRY_NAME).read_text())
        assert row["pid"] == os.getpid()
        assert row["process_start_token"] == process_start_token(os.getpid())
        assert row["command_digest"] == command_digest(["python", "-m", "driver"])
        handle.heartbeat(extra={"phase": "E"})
        assert json.loads((runtime / REGISTRY_NAME).read_text())["extra"]["phase"] == "E"
    assert not (runtime / REGISTRY_NAME).exists()
    history = (runtime / HISTORY_NAME).read_text().strip().splitlines()
    assert history and json.loads(history[-1])["status"] == "FINISHED"


def test_no_public_api_accepts_a_runtime_path():
    for fn in (acquire, cleanup_stale, machine_runtime_dir):
        params = inspect.signature(fn).parameters
        assert not any("runtime" in p or "path" in p for p in params), (
            f"{fn.__name__} must not expose a runtime/path parameter"
        )


def test_machine_runtime_dir_is_outside_any_repository():
    target = machine_runtime_dir()
    assert ".my-quantitative-governance" in str(target)
    assert str(REPO_ROOT) not in str(target)


def test_failed_release_note_roundtrip(runtime):
    handle = acquire(cycle_id="C4", role="r", worktree="/wt/c4", command=["python", "-m", "c4"])
    handle.release(status="FAILED", note="TypeError at stream_reduce entry")
    history = json.loads((runtime / HISTORY_NAME).read_text().strip().splitlines()[-1])
    assert history["status"] == "FAILED"
    assert history["release_note"] == "TypeError at stream_reduce entry"


# ------------------------------------------------------------- contention

def test_contention_refuses_with_not_run_resource_conflict(runtime):
    proc = _spawn_holder(runtime)
    try:
        _wait_acquired(proc)
        with pytest.raises(LockBusyError) as excinfo:
            acquire(cycle_id="C2", role="other", worktree="/wt/y", command=["python", "-m", "other"])
        assert excinfo.value.verdict == NOT_RUN_RESOURCE_CONFLICT
        assert "TEST-CYCLE" in str(excinfo.value)
    finally:
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=10)


def test_crash_cleanup_os_releases_flock_and_registry_archived(runtime):
    proc = _spawn_holder(runtime)
    _wait_acquired(proc)
    os.kill(proc.pid, signal.SIGKILL)
    proc.wait(timeout=10)
    with acquire(cycle_id="C3", role="reclaimer", worktree="/wt/z", command=["python", "-m", "reclaim"]):
        history = [
            json.loads(line)
            for line in (runtime / HISTORY_NAME).read_text().strip().splitlines()
        ]
        stale = [h for h in history if h.get("cycle_id") == "TEST-CYCLE"]
        assert stale and stale[-1]["reclaim_reason"] == "pid_dead"


def test_cross_worktree_and_cross_repo_contention(tmp_path):
    """Machine-wide: a holder in a WORKTREE of one repo blocks a contender
    in a DIFFERENT repo entirely — both resolve the same home runtime."""
    repo = tmp_path / "repoA"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    wt1 = tmp_path / "repoA-wt1"
    subprocess.run(["git", "-C", str(repo), "commit", "--allow-empty", "-qm", "init"], check=True)
    subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", str(wt1)], check=True)
    repo_b = tmp_path / "repoB"
    repo_b.mkdir()

    home = tmp_path / "fakehome"
    home.mkdir()
    env = {**os.environ, "HOME": str(home)}
    holder_code = (
        "import sys, os, time, pathlib;"
        f"sys.path.insert(0, {str(REPO_ROOT)!r});"
        "from research.governance import heavy_lock;"
        "rt = pathlib.Path(os.environ['HOME']) / '.my-quantitative-governance' / 'heavy_runtime';"
        "heavy_lock.machine_runtime_dir = lambda: rt;"
        "h = heavy_lock.acquire(cycle_id='REPOA-WT1', role='holder', worktree=os.getcwd(), "
        "command=['python3','holder.py']);"
        "print('ACQUIRED', heavy_lock.machine_runtime_dir(), flush=True);"
        "time.sleep(120)"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", holder_code], cwd=str(wt1),
        stdout=subprocess.PIPE, text=True, env=env,
    )
    try:
        assert proc.stdout is not None
        line = proc.stdout.readline().split()
        assert line[0] == "ACQUIRED"
        assert Path(line[1]) == home / ".my-quantitative-governance" / "heavy_runtime"

        contender_code = (
            "import sys, os, pathlib\n"
            f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
            "from research.governance import heavy_lock\n"
            "from research.governance.heavy_lock import LockBusyError\n"
            "rt = pathlib.Path(os.environ['HOME']) / '.my-quantitative-governance' / 'heavy_runtime'\n"
            "heavy_lock.machine_runtime_dir = lambda: rt\n"
            "try:\n"
            "    heavy_lock.acquire(cycle_id='REPOB', role='contender', worktree=os.getcwd(), "
            "command=['python','c'])\n"
            "    print('NO-REFUSAL')\n"
            "except LockBusyError as e:\n"
            "    print('REFUSED', e.verdict, e)\n"
        )
        out = subprocess.run(
            [sys.executable, "-c", contender_code], cwd=str(repo_b),
            capture_output=True, text=True, env=env, timeout=60,
        )
        assert "REFUSED NOT_RUN_RESOURCE_CONFLICT" in out.stdout, out.stdout + out.stderr
        assert "REPOA-WT1" in out.stdout
    finally:
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=10)


# ------------------------------------------------- drift classification

def test_malformed_registry_is_drift_fail_closed(runtime):
    # Adversarial: garbage bytes where the registry should be.
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / REGISTRY_NAME).write_text("{not json at all", encoding="utf-8")
    with pytest.raises(HeavyLockError) as excinfo:
        acquire(cycle_id="X", role="r", worktree="/wt/x", command=["python", "-m", "x"])
    assert CONTROL_STATE_DRIFT in str(excinfo.value)
    # preserved for inspection, nothing archived
    assert (runtime / REGISTRY_NAME).read_text().startswith("{not json")
    assert not (runtime / HISTORY_NAME).exists()
    result = cleanup_stale()
    assert result["action"] == "none"
    assert CONTROL_STATE_DRIFT in result["reason"]
    assert (runtime / REGISTRY_NAME).exists()


def test_non_object_registry_is_drift_fail_closed(runtime):
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / REGISTRY_NAME).write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(HeavyLockError) as excinfo:
        acquire(cycle_id="X", role="r", worktree="/wt/x", command=["python", "-m", "x"])
    assert CONTROL_STATE_DRIFT in str(excinfo.value)


def test_alive_pid_with_missing_token_is_drift_not_reclaimable(runtime):
    # Adversarial: a RUNNING row pointing at OUR OWN live pid with NO
    # token. Old code archived-and-proceeded; round 2 refuses.
    _write_registry(runtime, _running_row(os.getpid(), None))
    with pytest.raises(HeavyLockError) as excinfo:
        acquire(cycle_id="X", role="r", worktree="/wt/x", command=["python", "-m", "x"])
    assert CONTROL_STATE_DRIFT in str(excinfo.value)
    assert "missing start token" in str(excinfo.value)
    row = json.loads((runtime / REGISTRY_NAME).read_text())
    assert row["status"] == "RUNNING"  # preserved, not cleared
    assert not (runtime / HISTORY_NAME).exists()


def test_alive_pid_with_unrecoverable_live_token_is_drift(runtime, monkeypatch):
    # pid alive, row HAS a token, but the live token cannot be read now.
    _write_registry(runtime, _running_row(os.getpid(), "ps:SOME-TOKEN"))
    monkeypatch.setattr(heavy_lock, "process_start_token", lambda pid: None)
    with pytest.raises(HeavyLockError) as excinfo:
        acquire(cycle_id="X", role="r", worktree="/wt/x", command=["python", "-m", "x"])
    assert "unrecoverable" in str(excinfo.value)


def test_alive_row_with_free_flock_is_control_state_drift_fail_closed(runtime):
    # pid alive + REAL matching token + flock free: bookkeeping lies.
    _write_registry(runtime, _running_row(os.getpid(), process_start_token(os.getpid())))
    with pytest.raises(HeavyLockError) as excinfo:
        acquire(cycle_id="X", role="r", worktree="/wt/x", command=["python", "-m", "x"])
    assert CONTROL_STATE_DRIFT in str(excinfo.value)
    row = json.loads((runtime / REGISTRY_NAME).read_text())
    assert row["status"] == "RUNNING"
    result = cleanup_stale()
    assert result["action"] == "none"
    assert CONTROL_STATE_DRIFT in result["reason"]


def test_pid_reuse_definite_token_mismatch_is_reclaimable(runtime):
    # pid alive (ours) + DEFINITELY different token -> PID reuse -> reclaim.
    _write_registry(runtime, _running_row(os.getpid(), "ps:FAKE-TOKEN-1955"))
    result = cleanup_stale()
    assert result["action"] == "archived_stale"
    assert result["reason"] == "pid_reused_token_mismatch"
    history = json.loads((runtime / HISTORY_NAME).read_text().strip().splitlines()[0])
    assert history["cycle_id"] == "GHOST"


def test_cleanup_stale_leaves_live_lock_alone(runtime):
    with acquire(cycle_id="ALIVE", role="worker", worktree="/wt/a", command=["python", "-m", "w"]):
        result = cleanup_stale()
        assert result["action"] == "none"
        assert "lock held" in result["reason"]
