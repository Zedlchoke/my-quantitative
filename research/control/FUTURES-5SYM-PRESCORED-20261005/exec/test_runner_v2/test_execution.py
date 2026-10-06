"""Execution-path tests for scored_runner_v2 — the REAL CLI driven against
sandbox temp dirs (no stubs, no mocks of the runner itself).

  T1  happy path all 5 symbols            -> exit 0, EXECUTION_COMPLETE,
                                             ledger rows, twin match, lock
                                             acquired+released, handoff
                                             written, published==observed
  T12 --test-fault fail_handoff_write     -> non-zero, no handoff artifact,
                                             no EXECUTION_COMPLETE anywhere
                                             (BUG2-class proof)
  T13 --test-fault fail_publication       -> observed kept, published
                                             missing, quarantine marker,
                                             non-zero
  T14 duplicate identity retry            -> no double count (idempotency)
  T15 --test-fault force_twin_drift       -> FAILED_TWIN_MISMATCH +
                                             reconciliation report
  extra: fail_ledger_summary (BUG2-class sibling path proof)
"""
from __future__ import annotations

import json

SYMBOLS = ["NQ", "6E", "6B", "6J", "6A"]


def test_T1_happy_path_all_5_symbols(sb):
    r = sb.run()
    assert r.returncode == 0, r.stderr
    fs = sb.final()
    assert fs["status"] == "EXECUTION_COMPLETE"
    assert fs["exit_code"] == 0
    assert fs["refusal_code"] is None and fs["failed_step"] is None
    assert fs["computation_complete"] is True
    assert all(fs["mandatory_steps"].values())
    assert fs["lock"]["acquired"] is True
    assert fs["lock"]["released_status"] == "RELEASED"

    rows = sb.ledger_rows()
    trials = [x for x in rows if x["row_type"] == "TRIAL"]
    assert len(trials) == 10  # 2 identities x 5 symbols
    assert all(x["counts_observed"] for x in trials)
    assert {x["payload"]["symbol"] for x in trials} == set(SYMBOLS)
    fold_rows = [x for x in rows if x["row_type"] == "FOLD"]
    assert len(fold_rows) == 2  # F1, F2
    assert any(x["row_type"] == "PUBLICATION" for x in rows)

    pub = json.loads(sb.out_file("published_summary.json").read_text())
    assert pub["observed_identity_count"] == \
        pub["published_identity_count"] == 10

    handoff = json.loads(sb.out_file("handoff.json").read_text())
    assert handoff["status"] == "EXECUTION_COMPLETE"
    assert handoff["lock"]["released_status"] == "RELEASED"
    assert handoff["observed_identity_count"] == \
        handoff["published_identity_count"] == 10

    recon = json.loads(sb.out_file("reconciliation_report.json").read_text())
    assert recon["match"] is True and recon["diff_count"] == 0
    assert sb.out_file("ledger_summary.json").is_file()

    # a successful run leaves NO stale IN_PROGRESS marker
    assert not sb.out_file("IN_PROGRESS.json").exists()
    # lock released: registry empty, flock free
    assert sb.lock_rows() == []
    assert sb.flock_held() is False
    # per-trade contract law: usd_per_price_unit == multiplier, all symbols
    for t in trials:
        for fold in t["payload"]["folds"]:
            for tr in fold["trades"]:
                assert abs(tr["tick_value_usd"] / tr["tick_size"]
                           - _multiplier(tr["era"])) < 1e-6


_ERA_MULT = {"NQ-era1": 20, "ES-era1": 50, "6E-era1": 125000,
             "6B-era1": 62500, "6J-era1": 12500000,
             "6A-era1": 100000, "6A-era2": 100000}


def _multiplier(era: str) -> float:
    return float(_ERA_MULT[era])


def test_T12_fail_handoff_write_bugs2_class(sb):
    r = sb.run(extra=["--test-fault", "fail_handoff_write"])
    assert r.returncode != 0 and r.returncode != 75
    fs = sb.final()
    assert fs["status"] == "FAILED"
    assert fs["failure_code"] == "FAILED_HANDOFF_WRITE"
    assert fs["failed_step"] == "handoff_write"
    assert fs["lock"]["released_status"] == "RELEASED"  # release succeeded
    # the terminal artifact was NOT produced and success is nowhere claimed
    assert not sb.out_file("handoff.json").exists()
    fs_text = (sb.out / "FINAL_STATUS.run1.json").read_text()
    assert "EXECUTION_COMPLETE" not in fs_text
    # publication succeeded before the handoff fault — it stands
    pub = json.loads(sb.out_file("published_summary.json").read_text())
    assert pub["published_identity_count"] == 10
    assert fs["published_identity_count"] == 10
    assert any("handoff" in f for f in fs["finalization_failures"])


def test_T13_fail_publication_keeps_observed(sb):
    r = sb.run(extra=["--test-fault", "fail_publication"])
    assert r.returncode != 0 and r.returncode != 75
    fs = sb.final()
    assert fs["status"] == "FAILED"
    assert fs["failure_code"] == "FAILED_PUBLICATION"
    # observed denominator already counted in the append-only ledger
    trials = [x for x in sb.ledger_rows() if x["row_type"] == "TRIAL"]
    assert len(trials) == 10
    assert fs["observed_identity_count"] == 10
    assert fs["published_identity_count"] is None
    assert not sb.out_file("published_summary.json").exists()
    q = sb.out_file("PUBLICATION_QUARANTINE.json")
    assert q.is_file()
    assert json.loads(q.read_text())["observed_identity_count"] == 10
    assert not sb.out_file("handoff.json").exists()


def test_T14_duplicate_retry_never_double_counts(sb):
    r1 = sb.run(label="run1")
    assert r1.returncode == 0
    r2 = sb.run(label="run2")
    assert r2.returncode == 0, r2.stderr
    rows = sb.ledger_rows()
    trial_ids = [x["identity_id"] for x in rows if x["row_type"] == "TRIAL"]
    dupes = [x for x in rows if x["row_type"] == "DUPLICATE_RETRY"]
    assert len(trial_ids) == 10                       # unchanged
    assert len(trial_ids) == len(set(trial_ids))      # no double rows
    assert len(dupes) == 10                           # retried, not recomputed
    assert all(not x["counts_observed"] for x in dupes)
    fs2 = sb.final("run2")
    assert fs2["status"] == "EXECUTION_COMPLETE"
    pub = json.loads(sb.out_file("published_summary.json", "run2")
                     .read_text())
    assert pub["observed_identity_count"] == \
        pub["published_identity_count"] == 10
    # the retry published NOTHING new: all 10 were duplicates
    assert pub["published_identity_ids"] == []
    assert len(pub["duplicate_retry_ids"]) == 10


def test_T15_force_twin_drift_fails(sb):
    r = sb.run(extra=["--test-fault", "force_twin_drift"])
    assert r.returncode != 0
    fs = sb.final()
    assert fs["status"] == "FAILED"
    assert fs["failure_code"] == "FAILED_TWIN_MISMATCH"
    assert fs["failed_step"] == "twin_verify"
    recon = json.loads(sb.out_file("reconciliation_report.json").read_text())
    assert recon["match"] is False and recon["diff_count"] >= 1
    assert recon["diffs_sample"], "reconciliation report must carry diffs"
    assert not sb.out_file("handoff.json").exists()
    # twin mismatch never writes TRIAL rows (append happens after twin)
    assert not [x for x in sb.ledger_rows() if x["row_type"] == "TRIAL"]
    # lock still released on the failure path
    assert fs["lock"]["released_status"] == "RELEASED"


def test_fail_ledger_summary_bugs2_sibling(sb):
    r = sb.run(extra=["--test-fault", "fail_ledger_summary"])
    assert r.returncode != 0
    fs = sb.final()
    assert fs["status"] == "FAILED"
    assert fs["failure_code"] == "FAILED_LEDGER_SUMMARY"
    assert not sb.out_file("ledger_summary.json").exists()
    assert not sb.out_file("handoff.json").exists()
    assert fs["published_identity_count"] == 10  # publication stands
    assert any("ledger_summary" in f
               for f in fs["finalization_failures"]) or \
        fs["failure_code"] == "FAILED_LEDGER_SUMMARY"
