"""V12 I lane -- schedule feasibility, funding counts, drop-one, dry-run.

Deliverables exercised on the read-only staged snapshot (skipped when the
workspace data is absent):

* 52-stamp schedule feasibility re-run via ``research.v12.feasibility``
  for all three frozen arms (breadth >= 9, exact 4+4 legs, cap <= 0.30);
* the A4 open item resolved: funding events while held counted from the
  native ``funding_data/scan_2026`` settlements (schedule-only counts);
* the L-V11-7 drop-one diagnostic verified through the repaired stress
  layer (dropped = held max |weight| symbol);
* the exact-arm dummy dry-run: adapter primitives traversed per arm and
  DUMMY finite metrics published into a temporary empty ledger via
  ``research.v12.accounting`` -- a zero-position payload must be REFUSED
  and an exact replay must be an idempotent skip.  NO real scored metric
  is computed anywhere.
"""

from __future__ import annotations
from pathlib import Path

import pytest

from research.v12.accounting import (
    REFUSED_ZERO_POSITIONS,
    STAGE_IDEMPOTENT_REPLAY,
    STAGE_PUBLISHED,
    STAGE_REFUSED,
    read_v12_ledger,
    v12_denominator_view,
)
from research.v12.families.oilev_v2.audits import (
    evidence_drop_one,
    evidence_feasibility_52,
    evidence_funding_events_while_held,
    require_temporary_ledger,
    run_exact_arm_dummy_dryrun,
)

DATA_ROOT = Path("/Users/hoangminhlong/my-quantitative/oi_data/consolidated")

_requires_data = pytest.mark.skipif(
    not DATA_ROOT.is_dir(), reason="read-only workspace data absent"
)


@_requires_data
def test_feasibility_52_stamps_all_arms_pass() -> None:
    payload = evidence_feasibility_52()
    assert payload["n_schedule_stamps"] == 52
    assert payload["universe_size"] == 19
    assert payload["all_arms_pass"] is True
    for arm_id, arm in payload["arms"].items():
        assert arm["verdict"] == "PASS", arm_id
        assert arm["n_stamps"] == 52
        assert arm["n_pass"] == 52
        assert arm["n_fail"] == 0
        assert arm["failing_stamps"] == []
        # breadth: every stamp >= the frozen min_eligible
        assert arm["n_eligible_min"] >= 9
        # the staged snapshot serves all 19 names at every stamp (A4 parity)
        assert arm["n_eligible_min"] == arm["n_eligible_max"] == 19
        # exact 4+4 legs (validator legs_per_side=4) and cap <= 0.30
        assert arm["max_abs_weight_observed"] <= 0.30
        assert arm["uniform_scale_triggered"] is False


@_requires_data
def test_funding_events_while_held_resolved_from_scan_2026() -> None:
    payload = evidence_funding_events_while_held()
    assert payload["bundle"].endswith("scan_2026 (native Binance settlements)")
    assert payload["schedule_only"] is True
    assert payload["resolved"] is True
    for arm_id, arm in payload["arms"].items():
        assert arm["funding_status"] == "OK", arm_id
        assert arm["events_while_held_total"] > 0
        assert arm["decision_count"] == 52
        assert arm["n_held_spans"] > 0
        # every cohort symbol has a native settlement series loaded
        assert all(n > 0 for n in arm["n_settlements_loaded"].values())


@_requires_data
def test_drop_one_diagnostic_selects_held_max_weight() -> None:
    payload = evidence_drop_one()
    assert payload["all_match"] is True
    for check in payload["checks"]:
        assert check["matches_held_max"] is True
        assert check["unheld_never_selected"] is True
        assert check["zero_held_book_refused"] is True


def test_require_temporary_ledger_refuses_non_temp_paths(tmp_path) -> None:
    with pytest.raises(Exception):
        require_temporary_ledger(None)
    with pytest.raises(Exception):
        require_temporary_ledger(tmp_path / "wrong_name.jsonl")
    with pytest.raises(Exception):
        require_temporary_ledger(tmp_path / "dryrun_wrong_ext.json")
    ok = require_temporary_ledger(tmp_path / "dryrun_ok.jsonl")
    assert ok.name == "dryrun_ok.jsonl"


@_requires_data
def test_exact_arm_dummy_dryrun_refusal_publication_and_replay(tmp_path) -> None:
    ledger = tmp_path / "dryrun_oilev_v2.jsonl"
    payload = run_exact_arm_dummy_dryrun(ledger_path=ledger)
    assert payload["scored"] is False and payload["real_pnl"] is False
    assert payload["ok"] is True
    for arm_id, arm in payload["arms"].items():
        traversal = arm["adapter_traversal"]
        assert traversal["n_universe"] == 19
        assert traversal["n_schedule_instants"] == 52
        assert traversal["fold_labels"] == ["F0", "F1", "F2"]
        assert traversal["dropped_fold_accepted"] is True
        assert traversal["first_stamp_book_symbols"] == 8
        assert traversal["n_fills_applied"] == 19
        assert traversal["first_stamp_mark_finite"] is True
        assert traversal["n_funding_cashflows_probe_span"] > 0
        assert traversal["funding_sign_convention"] == "LONG_PAYS_POSITIVE_RATE"
        # zero-position output must be REFUSED (L-V11-4 guard)
        assert arm["zero_position_stage"] == STAGE_REFUSED
        assert REFUSED_ZERO_POSITIONS in arm["zero_position_reason"]
        assert arm["zero_position_refused"] is True
        # the DUMMY held-position payload publishes exactly once...
        assert arm["dummy_publish_stage"] == STAGE_PUBLISHED
        # ...and its exact replay is an idempotent skip
        assert arm["replay_stage"] == STAGE_IDEMPOTENT_REPLAY
        assert arm["replay_idempotent"] is True
        assert arm["dummy_metrics_kind"] == "DUMMY_DRYRUN_METRICS"
    denominators = payload["ledger_denominators"]
    assert denominators["published"] == 3  # one DUMMY CELL_RESULT per arm
    assert denominators["observed"] == 3  # one zero-position OBSERVATION per arm
    assert denominators["observed_total"] == 6
    state = read_v12_ledger(ledger)
    assert state["count"] == 6


@_requires_data
def test_dummy_dryrun_replay_is_idempotent_on_rerun(tmp_path) -> None:
    """Re-running the whole dry-run on the SAME ledger adds no rows."""
    ledger = tmp_path / "dryrun_oilev_v2.jsonl"
    first = run_exact_arm_dummy_dryrun(ledger_path=ledger)
    assert first["ok"] is True
    before = v12_denominator_view(ledger)
    second = run_exact_arm_dummy_dryrun(ledger_path=ledger)
    after = v12_denominator_view(ledger)
    assert before == after
    for arm_id, arm in second["arms"].items():
        # same trial keys: both the refusal and the dummy publish replay
        assert arm["replay_idempotent"] is True
    assert after["published"] == 3 and after["observed"] == 3
