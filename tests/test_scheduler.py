"""SHV1 G3/G4 - scheduler and retry safety (tests/test_scheduler.py).

Gate H3 fixture: the Stocks fromisoformat TypeError (INC_V12_4) executes ONCE
and stops as CODE_OR_SCHEMA_ERROR - it never enters retry/backoff. All state
is sandboxed in tmp_path journals; sleeps are recorded, never taken.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from governance import retry_classifier as rc  # noqa: E402
from governance import scheduler as sched  # noqa: E402
from governance.heavy_lock import LockBusyError  # noqa: E402


@pytest.fixture()
def sleeps():
    return []


@pytest.fixture()
def sched_factory(tmp_path, sleeps):
    def make():
        return sched.Scheduler(journal_path=tmp_path / "jobs.json",
                               sleep=sleeps.append, now=lambda: 0.0)
    return make


def test_gate_h3_fromisoformat_typeerror_runs_once_no_retry(sched_factory, sleeps):
    """GATE H3 FIXTURE - INC_V12_4: deterministic TypeError must execute once
    and classify CODE_OR_SCHEMA_ERROR; never retry, never backoff."""
    calls = {"n": 0}

    def d2_measure():
        calls["n"] += 1
        raise TypeError("fromisoformat: argument must be str, not datetime.date")

    s = sched_factory()
    job = s.run_job("STOCKS-FREE-V12", "D2_MEASUREMENT", d2_measure)
    assert calls["n"] == 1, "deterministic code/schema failure must execute exactly once"
    assert job["status"] == "FAILED"
    assert job["verdict"] == "FAILED_CODE_OR_SCHEMA_ERROR"
    assert job["last_classification"]["kind"] == rc.CODE_OR_SCHEMA_ERROR
    assert sleeps == [], "no backoff may be scheduled for a deterministic failure"
    # re-running the same job (fresh controller, same journal) also runs once - the
    # taxonomy never converts it into a loop
    job2 = sched_factory().run_job("STOCKS-FREE-V12", "D2_MEASUREMENT", d2_measure)
    assert calls["n"] == 2 and job2["verdict"] == "FAILED_CODE_OR_SCHEMA_ERROR"


def test_transient_transport_bounded_backoff_then_success(sched_factory, sleeps):
    calls = {"n": 0}

    def flaky_download():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionResetError(54, "connection reset by peer")
        return "39 months ok"

    s = sched_factory()
    job = s.run_job("CRYPTO-V17", "P0_BUILD", flaky_download)
    assert calls["n"] == 3 and job["status"] == "FINISHED"
    assert sleeps == [30.0, 60.0], "bounded frozen backoff schedule"
    assert job["attempt"] == 3


def test_transient_transport_exhausts_frozen_limit(sched_factory, sleeps):
    def always_reset():
        raise ConnectionResetError(54, "connection reset by peer")

    s = sched_factory()
    job = s.run_job("CRYPTO-V17", "P0_BUILD", always_reset)
    assert job["status"] == "FAILED"
    assert job["attempt"] == rc.TRANSIENT_MAX_ATTEMPTS
    assert len(sleeps) == rc.TRANSIENT_MAX_ATTEMPTS - 1
    assert "EXHAUSTED" in job["verdict"]


def test_resource_busy_does_not_consume_attempt(sched_factory):
    def blocked():
        raise LockBusyError("machine-wide heavy lock busy: STOCKS-FREE-V12/D2")

    s = sched_factory()
    job = s.run_job("CRYPTO-V17", "P0_BUILD", blocked)
    assert job["status"] == "WAITING"
    assert job["verdict"] == "NOT_RUN_RESOURCE_CONFLICT"
    assert job["attempt"] == 0, "resource busy must not consume a scientific attempt"


def test_admission_refuses_when_heavy_lock_held(sched_factory):
    s = sched_factory()
    job = s.admit("CRYPTO-V17", "P0_BUILD", "build",
                  lock_inspector=lambda: True)
    assert job["status"] == "WAITING"
    assert job["verdict"] == "NOT_RUN_RESOURCE_CONFLICT"


def test_rate_limited_honors_provider_reset(sched_factory):
    class RateLimited(RuntimeError):
        retry_after = 900.0

    def throttled():
        raise RateLimited("http 429 quota exceeded for this window")

    s = sched_factory()
    job = s.run_job("FOREX-FREE-V8", "P0_FETCH", throttled)
    assert job["status"] == "WAITING"
    assert job["verdict"] == "RATE_LIMITED_RETRY_AFTER=900.0"
    assert job["attempt"] == 0


def test_hash_drift_is_immediate_hard_stop(sched_factory):
    calls = {"n": 0}

    def drifted():
        calls["n"] += 1
        raise RuntimeError("sha256 mismatch for month manifest")

    s = sched_factory()
    job = s.run_job("CRYPTO-V17", "P0_BUILD", drifted)
    assert calls["n"] == 1
    assert job["status"] == "BLOCKED"
    assert job["verdict"] == "HASH_OR_CONTRACT_DRIFT_HARD_STOP"


def test_retry_state_survives_controller_restart(sched_factory, tmp_path):
    jp = tmp_path / "jobs.json"

    def blocked():
        raise LockBusyError("machine-wide heavy lock busy: held")

    sched.Scheduler(journal_path=jp).run_job("CRYPTO-V17", "P0_BUILD", blocked)
    fresh = sched.Scheduler(journal_path=jp)  # a brand-new controller
    jobs = fresh.list_jobs()
    assert len(jobs) == 1
    assert jobs[0]["status"] == "WAITING"
    assert jobs[0]["verdict"] == "NOT_RUN_RESOURCE_CONFLICT"
    assert jobs[0]["attempt"] == 0


def test_stale_running_row_recovered_only_on_proven_dead_pid(sched_factory, tmp_path):
    jp = tmp_path / "jobs.json"
    s = sched.Scheduler(journal_path=jp)
    job = s._record("CRYPTO-V17", "P0_BUILD", "build", status="RUNNING", pid=999999)
    # a live pid must NOT be reclaimed
    me = subprocess.Popen(["sleep", "0"]); me.wait()
    assert s.recover_stale_running(alive=lambda pid: pid == 999999) == []
    assert s.get_job(job["job_id"])["status"] == "RUNNING"
    # a proven-dead pid is reclaimed as FAILED crash recovery
    dead = subprocess.Popen(["sleep", "0"]); dead_pid = dead.pid; dead.wait()
    s._update({**job, "pid": dead_pid})
    assert s.recover_stale_running(alive=lambda pid: False) == [job["job_id"]]
    row = s.get_job(job["job_id"])
    assert row["status"] == "FAILED" and row["verdict"] == "CRASH_RECOVERED_PID_DEAD"


def test_cancel_records_operator_cancellation(sched_factory):
    s = sched_factory()
    job = s._record("FOREX-FREE-V8", "A8_BUILD", "build", status="ADMITTED")
    assert s.cancel(job["job_id"]) == f"CANCELLED {job['job_id']}"
    row = s.get_job(job["job_id"])
    assert row["status"] == "CANCELLED"
    assert row["last_classification"]["kind"] == rc.OPERATOR_CANCELLED
    assert s.cancel(job["job_id"]).startswith("TERMINAL_ALREADY")


def test_command_digest_stable_and_distinct():
    a = sched.Scheduler.command_digest("CRYPTO-V17", "P0_BUILD", "extract --full")
    b = sched.Scheduler.command_digest("CRYPTO-V17", "P0_BUILD", "extract --full")
    c = sched.Scheduler.command_digest("CRYPTO-V17", "P0_BUILD", "extract --smoke")
    assert a == b and a != c


def test_unknown_failure_fails_closed_to_no_retry(sched_factory, sleeps):
    calls = {"n": 0}

    def weird():
        calls["n"] += 1
        raise ArithmeticError("never seen before")

    job = sched_factory().run_job("CRYPTO-V17", "P0_BUILD", weird)
    assert calls["n"] == 1 and job["status"] == "FAILED"
    assert job["last_classification"]["kind"] == rc.CODE_OR_SCHEMA_ERROR
    assert sleeps == []
