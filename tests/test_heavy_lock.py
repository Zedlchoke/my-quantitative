"""Tests for the global heavy lock (machine-wide serialization).

Owner remediation items (2026-09-07):
- runtime is SHARED, derived from the git common dir — cross-worktree
  contention is proven on a REAL temporary git repository with two real
  linked worktrees;
- no public entry point accepts a runtime path;
- alive PID + matching start token + free flock => CONTROL_STATE_DRIFT,
  fail closed (nothing archived);
- cleanup holds the flock while reconciling;
- crash cleanup (SIGKILL) archives the stale row only because the OS
  freed the flock AND the pid is dead;
- PID reuse (token mismatch) is stale, never alive.
"""

from __future__ import annotations

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
    process_start_token,
    shared_runtime_dir,
)


@pytest.fixture()
def runtime(tmp_path, monkeypatch):
    """Hermetic shared runtime: patch the DERIVATION, not a caller param."""
    target = tmp_path / "runtime"
    monkeypatch.setattr(heavy_lock, "shared_runtime_dir", lambda: target)
    return target


def test_acquire_writes_registry_with_token_and_digest(runtime):
    with acquire(
        cycle_id="C1",
        role="A1",
        worktree="/wt/x",
        command=["python", "-m", "driver"],
        expected_artifacts=["a.jsonl"],
    ) as handle:
        row = json.loads((runtime / REGISTRY_NAME).read_text())
        assert row["pid"] == os.getpid()
        assert row["process_start_token"] == process_start_token(os.getpid())
        assert row["command_digest"] == command_digest(["python", "-m", "driver"])
        assert row["status"] == "RUNNING"
        handle.heartbeat(extra={"phase": "E"})
        assert json.loads((runtime / REGISTRY_NAME).read_text())["extra"]["phase"] == "E"
    assert not (runtime / REGISTRY_NAME).exists()
    history = (runtime / HISTORY_NAME).read_text().strip().splitlines()
    assert history and json.loads(history[-1])["status"] == "FINISHED"


def test_no_public_api_accepts_a_runtime_path():
    # Remediation: callers cannot choose a worktree-local runtime.
    import inspect

    for fn in (acquire, cleanup_stale):
        params = inspect.signature(fn).parameters
        assert not any("runtime" in p for p in params), (
            f"{fn.__name__} must not expose a runtime parameter"
        )


def test_contention_refuses_with_not_run_resource_conflict(runtime, tmp_path):
    # Cross-process holder with the same patched runtime derivation; the
    # REAL git-derivation path is exercised separately below (worktree test).
    proc = subprocess.Popen(
        [sys.executable, "-c",
         "import sys, os, time;"
         f"sys.path.insert(0, {str(Path(__file__).resolve().parents[1])!r});"
         "os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';"
         "from research.governance import heavy_lock;"
         f"heavy_lock.shared_runtime_dir = lambda: {str(runtime)!r};"
         "h = heavy_lock.acquire(cycle_id='TEST-CYCLE', role='holder', "
         f"worktree={str(tmp_path)!r}, command=['python3','holder.py'], "
         "expected_artifacts=['out.jsonl']);"
         "print('ACQUIRED', flush=True);"
         "[ (h.heartbeat(), time.sleep(0.5)) for _ in range(240) ]"],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert proc.stdout is not None and proc.stdout.readline().strip() == "ACQUIRED"
        with pytest.raises(LockBusyError) as excinfo:
            acquire(cycle_id="C2", role="other", worktree="/wt/y", command=["python", "-m", "other"])
        assert excinfo.value.verdict == NOT_RUN_RESOURCE_CONFLICT
        assert "TEST-CYCLE" in str(excinfo.value)
    finally:
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=10)


def test_crash_cleanup_os_releases_flock_and_registry_archived(runtime, tmp_path):
    proc = subprocess.Popen(
        [sys.executable, "-c",
         "import sys, time;"
         f"sys.path.insert(0, {str(Path(__file__).resolve().parents[1])!r});"
         "from research.governance import heavy_lock;"
         f"heavy_lock.shared_runtime_dir = lambda: {str(runtime)!r};"
         "h = heavy_lock.acquire(cycle_id='TEST-CYCLE', role='holder', "
         f"worktree={str(tmp_path)!r}, command=['python3','holder.py']);"
         "print('ACQUIRED', flush=True);"
         "time.sleep(120)"],
        stdout=subprocess.PIPE,
        text=True,
    )
    assert proc.stdout is not None and proc.stdout.readline().strip() == "ACQUIRED"
    os.kill(proc.pid, signal.SIGKILL)
    proc.wait(timeout=10)

    with acquire(cycle_id="C3", role="reclaimer", worktree="/wt/z", command=["python", "-m", "reclaim"]):
        history = [
            json.loads(line)
            for line in (runtime / HISTORY_NAME).read_text().strip().splitlines()
        ]
        stale = [h for h in history if h.get("cycle_id") == "TEST-CYCLE"]
        assert stale, "crashed holder must be archived"
        assert stale[-1]["reclaim_reason"] == "pid_dead"


def test_alive_row_with_free_flock_is_control_state_drift_fail_closed(runtime):
    # Simulate a LIVE worker whose registry says RUNNING while its flock
    # is free (bookkeeping lies). Our own pid + OUR REAL token = alive.
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / REGISTRY_NAME).write_text(
        json.dumps(
            {
                "cycle_id": "LIVE-GHOST",
                "role": "worker",
                "pid": os.getpid(),
                "process_start_token": process_start_token(os.getpid()),
                "worktree": "/wt/ghost",
                "command_digest": "0" * 64,
                "started_at": "2026-01-01T00:00:00Z",
                "last_heartbeat": "2026-01-01T00:00:00Z",
                "expected_artifacts": [],
                "status": "RUNNING",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(HeavyLockError) as excinfo:
        acquire(cycle_id="X", role="r", worktree="/wt/x", command=["python", "-m", "x"])
    assert CONTROL_STATE_DRIFT in str(excinfo.value)
    # fail closed: the suspicious row is preserved, NOT archived
    row = json.loads((runtime / REGISTRY_NAME).read_text())
    assert row["cycle_id"] == "LIVE-GHOST"
    assert not (runtime / HISTORY_NAME).exists()
    # cleanup reports the drift without clearing
    result = cleanup_stale()
    assert result["action"] == "none"
    assert CONTROL_STATE_DRIFT in result["reason"]
    assert (runtime / REGISTRY_NAME).exists()


def test_pid_reuse_token_mismatch_is_stale_not_alive(runtime):
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / REGISTRY_NAME).write_text(
        json.dumps(
            {
                "cycle_id": "GHOST",
                "role": "old",
                "pid": os.getpid(),
                "process_start_token": "ps:FAKE-TOKEN-1955",
                "worktree": "/wt/ghost",
                "command_digest": "0" * 64,
                "started_at": "2026-01-01T00:00:00Z",
                "last_heartbeat": "2026-01-01T00:00:00Z",
                "expected_artifacts": [],
                "status": "RUNNING",
            }
        ),
        encoding="utf-8",
    )
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
        assert (runtime / REGISTRY_NAME).exists()


def test_release_refuses_bogus_status(runtime):
    handle = acquire(cycle_id="C4", role="r", worktree="/wt/c4", command=["python", "-m", "c4"])
    with pytest.raises(Exception):
        handle.release(status="SOMEHOW_DONE")
    handle.release(status="TECHABORT", note="driver died")
    history = json.loads((runtime / HISTORY_NAME).read_text().strip().splitlines()[-1])
    assert history["status"] == "TECHABORT"


def test_shared_runtime_dir_resolves_from_any_worktree(tmp_path):
    """Cross-worktree contention, proven on a REAL temporary git repo:
    two linked worktrees + the root all derive the SAME runtime, and a
    holder in worktree A blocks an acquirer in worktree B."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "--allow-empty", "-m", "init", "-q"], check=True)
    wt1 = tmp_path / "wt1"
    wt2 = tmp_path / "wt2"
    subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", str(wt1)], check=True)
    subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", str(wt2)], check=True)

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    holder_code = (
        "import sys, os, time;"
        f"sys.path.insert(0, {str(Path(__file__).resolve().parents[1])!r});"
        "from research.governance.heavy_lock import acquire, shared_runtime_dir;"
        "h = acquire(cycle_id='WT1-CYCLE', role='holder', worktree=os.getcwd(), "
        "command=['python3', 'holder.py']);"
        "print('ACQUIRED', shared_runtime_dir(), flush=True);"
        "time.sleep(120)"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", holder_code],
        cwd=str(wt1),
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert proc.stdout is not None
        line = proc.stdout.readline().split()
        assert line[0] == "ACQUIRED"
        wt1_runtime = Path(line[1])
        assert wt1_runtime == repo / ".runtime", "runtime must derive from the git common dir"

        # From worktree 2 (different cwd, real derivation), the same lock:
        old = Path.cwd()
        os.chdir(wt2)
        try:
            assert shared_runtime_dir() == repo / ".runtime"
            with pytest.raises(LockBusyError) as excinfo:
                acquire(cycle_id="WT2", role="contender", worktree=str(wt2), command=["python", "-m", "c"])
            assert excinfo.value.verdict == NOT_RUN_RESOURCE_CONFLICT
            assert "WT1-CYCLE" in str(excinfo.value)
        finally:
            os.chdir(old)
    finally:
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=10)
