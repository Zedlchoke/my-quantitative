"""Lock-lifecycle and finalization tests for scored_runner_v2.

  T8  lock pre-held (REAL foreign flock in the sandbox lock runtime)
      -> NOT_RUN_RESOURCE_CONFLICT, exit 75
  T9  post-acquire foreign registry row -> abort FAILED + lock released
  T10 mid-run exception -> lock released, ledger re-openable, non-zero
  T11 --test-fault fail_release -> NON-zero, RELEASE_RAISED, never
      EXECUTION_COMPLETE  (BUG1-class proof)
  T20 recovery: stale marker + --resume-with-recovery-check with intact
      ledger -> completes with identity-ID dedupe (no double count)
"""
from __future__ import annotations

import json
import subprocess
import sys

from conftest import PY


def test_T8_lock_pre_held_conflict_75(sb):
    sb.lock_dir.mkdir(parents=True, exist_ok=True)
    holder = subprocess.Popen(
        [PY, "-c",
         "import fcntl,os,sys,time;"
         "fd=os.open(sys.argv[1], os.O_RDWR|os.O_CREAT);"
         "fcntl.flock(fd, fcntl.LOCK_EX);"
         "print('HELD', flush=True); time.sleep(120)",
         str(sb.lock_file)],
        stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "HELD"
        r = sb.run()
        assert r.returncode == 75, (r.returncode, r.stderr)
        fs = sb.final()
        assert fs["status"] == "NOT_RUN_RESOURCE_CONFLICT"
        assert fs["refusal_code"] == "NOT_RUN_RESOURCE_CONFLICT"
        assert fs["exit_code"] == 75
        assert fs["lock"]["acquired"] is False
        # zero denominator consumption
        assert not [x for x in sb.ledger_rows() if x["row_type"] == "TRIAL"]
    finally:
        holder.kill()
        holder.wait()


def test_T9_post_acquire_foreign_row_aborts_and_releases(sb):
    r = sb.run(extra=["--test-fault", "post_acquire_foreign_row"])
    assert r.returncode == 3, (r.returncode, r.stdout, r.stderr)
    fs = sb.final()
    assert fs["status"] == "FAILED"
    assert fs["failure_code"] == "FAILED_POST_ACQUIRE_FOREIGN_ROW"
    assert fs["failed_step"] == "post_acquire_recheck"
    # our row removed, the probe evidence preserved, flock free
    rows = sb.lock_rows()
    assert [x["cycle_id"] for x in rows] == ["FOREIGN-PROBE-CYCLE"]
    assert sb.flock_held() is False
    assert fs["lock"]["acquired"] is True
    assert not sb.out_file("handoff.json").exists()
    # abort evidence recorded in the ledger
    assert any(x["row_type"] == "ABORT" for x in sb.ledger_rows())


def test_T10_mid_run_exception_releases_lock_and_keeps_ledger_open(sb):
    r = sb.run(extra=["--test-fault", "mid_run_exception"])
    assert r.returncode == 3
    fs = sb.final()
    assert fs["status"] == "FAILED"
    assert fs["failure_code"] == "FAILED_UNCAUGHT"
    assert "injected mid-run exception" in json.dumps(fs)
    # exactly the first identity's TRIAL row landed before the fault
    trials = [x for x in sb.ledger_rows() if x["row_type"] == "TRIAL"]
    assert len(trials) == 1
    # the ledger is re-openable: every line is complete JSON
    assert sb.ledger_rows() == sb.ledger_rows()  # idempotent parse
    # lock fully released despite the exception
    assert sb.lock_rows() == []
    assert sb.flock_held() is False
    assert fs["lock"]["released_status"] == "RELEASED"
    # the IN_PROGRESS marker survived (that is the point of the marker)
    assert sb.out_file("IN_PROGRESS.json").exists()
    assert not sb.out_file("handoff.json").exists()


def test_T11_fail_release_bug1_proof(sb):
    r = sb.run(extra=["--test-fault", "fail_release"])
    assert r.returncode != 0, "BUG1-class: release failure must not exit 0"
    fs = sb.final()
    assert fs["status"] == "FAILED"
    assert fs["failure_code"] == "FAILED_LOCK_RELEASE"
    assert fs["failed_step"] == "lock_release"
    assert fs["lock"]["acquired"] is True
    assert fs["lock"]["released_status"] == "RELEASE_RAISED"
    # the false-success string appears NOWHERE in the terminal status
    assert "EXECUTION_COMPLETE" not in (sb.out /
                                        "FINAL_STATUS.run1.json").read_text()
    # handoff never written (terminal artifact requires full completion)
    assert not sb.out_file("handoff.json").exists()
    # release raised BEFORE row removal: evidence preserved, never faked
    assert len(sb.lock_rows()) == 1
    assert sb.lock_rows()[0]["status"] == "RUNNING"
    # computation itself completed — but that never yields success here
    assert fs["computation_complete"] is True
    assert any("release" in f for f in fs["finalization_failures"])


def test_T20_recovery_resume_with_recovery_check(sb):
    # 1) crash mid-run (leaves marker + 1 TRIAL row)
    r1 = sb.run(extra=["--test-fault", "mid_run_exception"])
    assert r1.returncode == 3
    # 2) re-run WITHOUT the flag => refused
    r2 = sb.run(label="run2")
    assert r2.returncode == 2
    assert sb.final("run2")["refusal_code"] == "REFUSED_STALE_IN_PROGRESS"
    # 3) re-run WITH the flag + integrity OK => completes with dedupe
    r3 = sb.run(label="run3", extra=["--resume-with-recovery-check"])
    assert r3.returncode == 0, r3.stderr
    fs3 = sb.final("run3")
    assert fs3["status"] == "EXECUTION_COMPLETE"
    rows = sb.ledger_rows()
    trials = [x for x in rows if x["row_type"] == "TRIAL"]
    dupes = [x for x in rows if x["row_type"] == "DUPLICATE_RETRY"]
    assert len(trials) == 10                      # no double count
    assert len(dupes) == 1                        # the pre-crash identity
    assert dupes[0]["identity_id"] == trials[0]["identity_id"]
    assert fs3["observed_identity_count"] == 10
    # the marker is cleaned by the successful run
    assert not sb.out_file("IN_PROGRESS.json").exists()
