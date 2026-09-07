"""Tests for the global heavy lock (machine-wide serialization).

Covers the owner-mandated behaviours: OS-level flock, refusal verdict
NOT_RUN_RESOURCE_CONFLICT (never spin/overlap), registry with PID +
process-start token, heartbeat + command digest + cycle/worktree
ownership, and SAFE stale-lock recovery (a killed worker's flock is
auto-released by the OS; its registry row is archived only after PID +
token checks — a reused PID must not be mistaken for the holder).
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from research.governance.heavy_lock import (
    HISTORY_NAME,
    LOCK_NAME,
    REGISTRY_NAME,
    LockBusyError,
    NOT_RUN_RESOURCE_CONFLICT,
    acquire,
    cleanup_stale,
    command_digest,
    process_start_token,
)

HOLDER_SCRIPT = textwrap.dedent(
    """
    import sys, time
    sys.path.insert(0, {repo!r})
    from research.governance.heavy_lock import acquire
    handle = acquire(
        {runtime!r},
        cycle_id="TEST-CYCLE",
        role="holder",
        worktree="/tmp/wt",
        command=["python3", "holder.py"],
        expected_artifacts=["out.jsonl"],
    )
    print("ACQUIRED", flush=True)
    for _ in range(120):
        handle.heartbeat()
        time.sleep(0.5)
    """
)


@pytest.fixture()
def runtime(tmp_path):
    return tmp_path / "runtime"


def _spawn_holder(runtime: Path, repo_root: Path):
    script = runtime.parent / "holder.py"
    script.write_text(HOLDER_SCRIPT.format(repo=str(repo_root), runtime=str(runtime)), encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, str(script)],
        stdout=subprocess.PIPE,
        text=True,
    )
    assert proc.stdout is not None
    assert proc.stdout.readline().strip() == "ACQUIRED"
    return proc


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_acquire_writes_registry_with_token_and_digest(runtime):
    with acquire(
        runtime,
        cycle_id="C1",
        role="A1",
        worktree="/wt/x",
        command=["python", "-m", "driver"],
        expected_artifacts=["a.jsonl"],
    ) as handle:
        row = json.loads((runtime / REGISTRY_NAME).read_text())
        assert row["cycle_id"] == "C1"
        assert row["pid"] == os.getpid()
        assert row["process_start_token"] == process_start_token(os.getpid())
        assert row["command_digest"] == command_digest(["python", "-m", "driver"])
        assert row["worktree"] == "/wt/x"
        assert row["status"] == "RUNNING"
        handle.heartbeat(extra={"phase": "E"})
        row = json.loads((runtime / REGISTRY_NAME).read_text())
        assert row["last_heartbeat"]
        assert row["extra"]["phase"] == "E"
    assert not (runtime / REGISTRY_NAME).exists()
    history = (runtime / HISTORY_NAME).read_text().strip().splitlines()
    assert history and json.loads(history[-1])["status"] == "FINISHED"


def test_contention_refuses_with_not_run_resource_conflict(runtime):
    proc = _spawn_holder(runtime, _repo_root())
    try:
        with pytest.raises(LockBusyError) as excinfo:
            acquire(
                runtime,
                cycle_id="C2",
                role="other",
                worktree="/wt/y",
                command=["python", "-m", "other"],
            )
        assert excinfo.value.verdict == NOT_RUN_RESOURCE_CONFLICT
        assert "TEST-CYCLE" in str(excinfo.value)
    finally:
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=10)


def test_crash_cleanup_os_releases_flock_and_registry_archived(runtime):
    proc = _spawn_holder(runtime, _repo_root())
    row_pid = None
    deadline = time.time() + 10
    while time.time() < deadline:
        row_path = runtime / REGISTRY_NAME
        if row_path.exists():
            row = json.loads(row_path.read_text())
            row_pid = row["pid"]
            break
        time.sleep(0.05)
    assert row_pid and row_pid != os.getpid()
    os.kill(proc.pid, signal.SIGKILL)
    proc.wait(timeout=10)

    # OS auto-released the flock; acquire must succeed and archive the
    # stale RUNNING row into history with the death reason.
    with acquire(
        runtime,
        cycle_id="C3",
        role="reclaimer",
        worktree="/wt/z",
        command=["python", "-m", "reclaim"],
    ) as handle:
        history = [
            json.loads(line)
            for line in (runtime / HISTORY_NAME).read_text().strip().splitlines()
        ]
        stale = [h for h in history if h.get("cycle_id") == "TEST-CYCLE"]
        assert stale, "crashed holder must be archived"
        assert stale[-1]["reclaim_reason"] == "pid_dead"
        assert handle.owner["cycle_id"] == "C3"


def test_pid_reuse_token_mismatch_is_stale_not_alive(runtime):
    # Simulate a reused PID: registry row carries OUR pid but a WRONG
    # process-start token. The row must be judged stale (archived), not
    # alive — a recycled PID may never be mistaken for the holder.
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
    result = cleanup_stale(runtime)
    assert result["action"] == "archived_stale"
    assert result["reason"] == "pid_reused_token_mismatch"
    assert not (runtime / REGISTRY_NAME).exists()
    history = json.loads((runtime / HISTORY_NAME).read_text().strip().splitlines()[0])
    assert history["cycle_id"] == "GHOST"


def test_cleanup_stale_leaves_live_row_alone(runtime):
    with acquire(
        runtime,
        cycle_id="ALIVE",
        role="worker",
        worktree="/wt/a",
        command=["python", "-m", "w"],
    ):
        result = cleanup_stale(runtime)
        assert result["action"] == "none"
        assert (runtime / REGISTRY_NAME).exists()


def test_release_refuses_bogus_status(runtime):
    handle = acquire(
        runtime,
        cycle_id="C4",
        role="r",
        worktree="/wt/c4",
        command=["python", "-m", "c4"],
    )
    with pytest.raises(Exception):
        handle.release(status="SOMEHOW_DONE")
    handle.release(status="TECHABORT", note="driver died")
    history = json.loads((runtime / HISTORY_NAME).read_text().strip().splitlines()[-1])
    assert history["status"] == "TECHABORT"
    assert history["release_note"] == "driver died"


def test_lock_file_is_gitignored_path_shape(runtime):
    with acquire(
        runtime,
        cycle_id="C5",
        role="r",
        worktree="/wt/c5",
        command=["python", "-m", "c5"],
    ):
        assert (runtime / LOCK_NAME).exists()
