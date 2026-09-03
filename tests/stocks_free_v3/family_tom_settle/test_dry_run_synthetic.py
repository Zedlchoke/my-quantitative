"""Exact-arm dry run on SYNTHETIC data: accounting + publication gate goldens.

Deliverable 4 (synthetic half): full schedule build + canonical
``factory.value_book`` accounting + ``GatedTrialLedger`` publication gate on a
TEMPORARY pytest-managed ledger.  Hand-computed cost chain with zero-return
prices pins the canonical semantics (cost exactly once, CASH never in
turnover, fill day earns no same-day return) without any scored metric.
"""

from __future__ import annotations

import pytest

from research.assets.stocks.factory import (
    CASH_SYMBOL,
    GatedTrialLedger,
    assert_reconciles,
    publication_metrics,
    value_book,
)
from research.stocks_free_v3.authority import COHORT_SYMBOLS
from research.stocks_free_v3.family_tom_settle import (
    build_schedule,
    run_exact_arm_dry_run,
    schedule_book_entries,
)
from tests.stocks_free_v3.family_tom_settle.conftest import HAND_SESSIONS

ARMS = ("A", "N", "C")

FLAT_RAW = {s: {d: 100.0 for d in HAND_SESSIONS} for s in COHORT_SYMBOLS}


def _flat_inputs():
    return dict(
        raw_close={s: dict(FLAT_RAW[s]) for s in COHORT_SYMBOLS},
        distributions={s: {} for s in COHORT_SYMBOLS},
        split_factors={s: {} for s in COHORT_SYMBOLS},
    )


@pytest.mark.parametrize("arm", ARMS)
def test_dry_run_cost_chain_hand_computed(arm_configs, arm, tmp_path):
    """Zero-return prices: equity moves only by costs.

    Hand arithmetic: equity after each fill is
    ``equity_prev x (1 - turnover x bps/1e4)`` with turnovers
    0.50 (establishment) then 0.20 per transition; costs are charged exactly
    once and CASH never counts in turnover.
    """
    cfg = arm_configs[arm]
    schedule = build_schedule(cfg, HAND_SESSIONS)
    ledger = GatedTrialLedger(str(tmp_path / f"{arm}_dry_run.json"))
    report = run_exact_arm_dry_run(
        cfg, HAND_SESSIONS,
        cost_bps=100.0,
        ledger=ledger,
        trial_key=f"DRYRUN::{cfg.arm_id}::SYNTHETIC",
        **_flat_inputs(),
    )

    equity = 1.0
    for fill in schedule.fills:
        equity *= 1.0 - fill.turnover_one_way * 100.0 / 10_000.0
    # the valuation numbers stay INSIDE the dry run; we recompute the chain
    # here independently and the report only certifies the reconciliation
    assert report.double_generation_identical is True
    assert report.n_fills == len(schedule.fills)
    assert report.n_transitions == len(schedule.transitions)
    assert report.establishment_fill_session == HAND_SESSIONS[0]
    assert report.valuation["attribution_reconciled"] is True
    assert report.valuation["cost_charged_once"] is True
    assert report.valuation["n_fills_costed"] == len(schedule.fills)
    assert report.valuation["n_held_positions"] == 11
    assert report.ledger == {
        "observed_after_compute": 1,
        "published": True,
        "replay_zero_delta": True,
        "n_published_keys": 1,
    }


def test_dry_run_report_carries_no_scored_metric(arm_configs, tmp_path):
    ledger = GatedTrialLedger(str(tmp_path / "noscore.json"))
    report = run_exact_arm_dry_run(
        arm_configs["A"], HAND_SESSIONS,
        cost_bps=10.0,
        ledger=ledger,
        trial_key="DRYRUN::NO_SCORED_METRIC",
        **_flat_inputs(),
    )
    payload = report.to_payload()

    forbidden = (
        "pnl", "equity", "expectancy", "profit_factor", "sharpe",
        "drawdown", "mdd", "alpha", "total_return",
    )

    def _walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                assert not any(tok in str(key).lower() for tok in forbidden), key
                _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(payload)
    assert payload["scored_metric"] == "NONE_SCHEDULE_AND_VALUATION_ONLY"


def test_ledger_is_temporary_and_deleted_after(arm_configs, tmp_path):
    path = tmp_path / "temp_ledger.json"
    ledger = GatedTrialLedger(str(path))
    run_exact_arm_dry_run(
        arm_configs["N"], HAND_SESSIONS,
        cost_bps=10.0, ledger=ledger, trial_key="DRYRUN::TEMP::N",
        **_flat_inputs(),
    )
    ledger.save()
    assert path.exists()
    path.unlink()
    assert not path.exists()          # the temporary ledger is deleted after


def test_book_entries_are_factory_valid_with_explicit_cash(arm_configs):
    schedule = build_schedule(arm_configs["C"], HAND_SESSIONS)
    entries = schedule_book_entries(schedule)
    assert len(entries) == len(schedule.fills)
    for entry, fill in zip(entries, schedule.fills):
        assert entry["entry_type"] == "FILL"
        assert entry["fill_date"] == fill.fill_session
        assert CASH_SYMBOL in entry["targets"]
        assert entry["cash_weight"] == entry["targets"][CASH_SYMBOL]
        # must pass the canonical normalizer with no disagreement
        from research.assets.stocks.factory import normalize_entry_targets
        targets, cash = normalize_entry_targets(entry)
        assert abs(cash - entry["cash_weight"]) < 1e-12
        assert len(targets) == 11


def test_accounting_cost_chain_matches_hand_computation_exactly(arm_configs):
    """Direct value_book cross-check on the anchor arm (100 bps, zero returns)."""
    schedule = build_schedule(arm_configs["A"], HAND_SESSIONS)
    entries = schedule_book_entries(schedule)
    result = value_book(
        entries, FLAT_RAW,
        {s: {} for s in COHORT_SYMBOLS},
        {s: {} for s in COHORT_SYMBOLS},
        list(HAND_SESSIONS), cost_bps=100.0,
    )
    assert_reconciles(result)
    # per-fill turnovers: establishment 0.50 then 0.20 per transition
    assert result.fill_costs[0][1] == pytest.approx(0.50, abs=1e-12)
    for _, turnover, _ in result.fill_costs[1:]:
        assert turnover == pytest.approx(0.20, abs=1e-12)
    # hand-computed equity chain (costs only)
    equity = 1.0
    for _, turnover, _ in result.fill_costs:
        equity *= 1.0 - turnover * 100.0 / 10_000.0
    assert result.equity_curve[HAND_SESSIONS[-1]] == pytest.approx(equity, rel=1e-12)
    assert result.total_cost == pytest.approx(1.0 - equity, rel=1e-12)
    # CASH excluded from turnover: BASE->TOM costs 0.20 of ETF legs, never 1.0
    assert all(abs(t - 1.0) > 1e-9 for _, t, _ in result.fill_costs)


def test_publication_gate_refuses_zero_result(arm_configs, tmp_path):
    ledger = GatedTrialLedger(str(tmp_path / "gate.json"))
    ledger.compute_recorded("K1")
    published = ledger.publish_result("K1", {"artifact": 1}, n_fill_events=0,
                                      n_held_positions=11)
    assert published is False
    assert "K1" not in ledger.published_keys
    assert ledger.refusals == [{"key": "K1", "reasons": ["ZERO_FILL_EVENTS"]}]
    assert ledger.observed == 1            # compute recorded even when refused
    with pytest.raises(ValueError):
        ledger.publish_result("K2", {"artifact": 1}, n_fill_events=1,
                              n_held_positions=True)  # bool is not an int count


def test_publication_gate_replay_zero_delta(tmp_path):
    ledger = GatedTrialLedger(str(tmp_path / "replay.json"))
    ledger.compute_recorded("K")
    assert ledger.publish_result("K", {"a": 1}, n_fill_events=3,
                                 n_held_positions=2) is True
    assert ledger.publish_result("K", {"a": 1}, n_fill_events=3,
                                 n_held_positions=2) is False
    assert ledger.observed == 1
    assert len(ledger.published_keys) == 1


def test_dry_run_rejects_non_gated_ledger(arm_configs):
    from research.stocks_free_v2.harness import TrialLedger
    with pytest.raises(Exception):
        run_exact_arm_dry_run(
            arm_configs["A"], HAND_SESSIONS,
            cost_bps=10.0, ledger=TrialLedger(), trial_key="X",
            **_flat_inputs(),
        )


def test_dry_run_rejects_schedule_with_missing_closes(arm_configs, tmp_path):
    raw = {s: {d: 100.0 for d in HAND_SESSIONS} for s in COHORT_SYMBOLS}
    del raw["SPY"][HAND_SESSIONS[0]]     # a fill date without a close
    ledger = GatedTrialLedger(str(tmp_path / "missing.json"))
    with pytest.raises(Exception):
        run_exact_arm_dry_run(
            arm_configs["A"], HAND_SESSIONS,
            cost_bps=10.0, ledger=ledger, trial_key="X",
            raw_close=raw, distributions={s: {} for s in COHORT_SYMBOLS},
            split_factors={s: {} for s in COHORT_SYMBOLS},
        )
