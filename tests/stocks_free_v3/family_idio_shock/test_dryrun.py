"""Exact-arm dry-run tests: schedule + canonical accounting + publication
gate, on synthetic data (always) and on the REAL staged S0 snapshot (skipped
when the staging directory is absent).

Nothing here computes a scored metric from real data: the dry-run payload is
asserted to contain NO PnL/expectancy/PF/Sharpe/drawdown/equity-curve field,
the gate runs on a temp ledger, and the real-data run is S0-bounded through
the sealed reader.
"""

from __future__ import annotations

import json
import os
from datetime import date

import pytest

from research.assets.stocks.factory import CASH_SYMBOL
from research.stocks_free_v3.authority import (
    SNAPSHOT_STAGING_PATH,
    S0_END,
    S0_START,
)
from research.stocks_free_v3.family_idio_shock.arms import ARM_A1, ARM_C1, ARM_N1
from research.stocks_free_v3.family_idio_shock.dryrun import (
    dry_run_all_arms,
    dry_run_arm,
    dry_run_real_s0,
    load_s0_snapshot_inputs,
)

from tests.stocks_free_v3.family_idio_shock.conftest import shock_fixture

STAGING = os.environ.get("V2_SNAPSHOT_STAGING", SNAPSHOT_STAGING_PATH)

SCORED_FIELD_NAMES = (
    "pnl", "expectancy", "profit_factor", "sharpe", "drawdown",
    "equity_curve", "period_pnls", "total_return",
)


def _recursive_key_scan(payload) -> list[str]:
    keys: list[str] = []

    def walk(node) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                keys.append(str(key).lower())
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return keys


def _synthetic_accounting_inputs():
    """Shocked returns plus flat raw closes so the canonical valuation path
    has prices to walk (returns of 0.0 keep the arithmetic trivially checkable:
    every charged cost equals the equity deduction)."""
    sessions, returns = shock_fixture(90, {"XLK": {62: -0.06},
                                           "XLE": {67: -0.06}})
    raw_close = {sym: {s: 100.0 for s in sessions if s in series}
                 for sym, series in returns.items()}
    return sessions, returns, raw_close, {}, {}


def test_dry_run_synthetic_arm_end_to_end(tmp_path):
    sessions, returns, raw_close, dist, splits = _synthetic_accounting_inputs()
    ledger_dir = tmp_path / "ledger"
    report = dry_run_arm(ARM_A1, sessions, returns, raw_close, dist, splits,
                         ledger_dir=str(ledger_dir),
                         publish_to_temp_ledger=True)
    # schedule facts (hand-known: entry @63, switch @68, exit @73)
    assert report.feasibility["n_entries_committed"] == 2
    assert report.feasibility["n_same_close_switches"] == 1
    assert report.feasibility["turnover_one_way_total"] == pytest.approx(2.0)
    assert report.feasibility["scored_metrics_computed"] is False
    # canonical accounting: exactly 3 fills charged, identity reconciles
    assert report.n_valuation_fills == 3
    assert report.attribution_reconciles is True
    assert report.etf_leg_turnover_charged_total == pytest.approx(2.0)
    # publication gate exercised against the temp ledger
    assert report.gate["mode"] == "TEMP_PUBLISH_THEN_DELETE"
    assert report.gate["n_fill_events"] == 3
    # each canonical fill holds exactly one sector ETF
    assert report.gate["n_held_positions"] == 1
    assert report.gate["published"] is True
    assert report.gate["ledger_observed"] == 1
    assert report.gate["ledger_published_keys"] == 1
    assert report.gate["ledger_persisted_permanently"] is False
    # the temp ledger file exists inside the caller-owned dir ...
    ledger_file = ledger_dir / "dryrun_trial_ledger.json"
    assert ledger_file.is_file()
    state = json.loads(ledger_file.read_text())
    assert state["published"] == 1
    # ... and no scored metric ever entered it
    assert not any(name in ledger_file.read_text().lower()
                   for name in SCORED_FIELD_NAMES)
    # payload-level scored-field scan
    payload = report.to_payload()
    assert not any(any(name in key for name in SCORED_FIELD_NAMES)
                   for key in _recursive_key_scan(payload))


def test_dry_run_synthetic_no_publish_mode_refuses_nothing(tmp_path):
    sessions, returns, raw_close, dist, splits = _synthetic_accounting_inputs()
    report = dry_run_arm(ARM_N1, sessions, returns, raw_close, dist, splits,
                         ledger_dir=str(tmp_path / "led"),
                         publish_to_temp_ledger=False)
    assert report.gate["mode"] == "NO_PUBLISH"
    assert report.gate["published"] is False
    assert report.gate["ledger_published_keys"] == 0
    assert report.gate["n_refusals"] == 0  # the book holds, so the gate passes
    assert report.gate["n_fill_events"] == 2
    assert report.feasibility["n_entries_committed"] == 1  # N1: switch blocked


def test_dry_run_all_arms_reports_no_scored_metrics():
    sessions, returns, raw_close, dist, splits = _synthetic_accounting_inputs()
    payload = dry_run_all_arms(sessions, returns, raw_close, dist, splits)
    assert payload["scored_metrics_computed"] is False
    assert payload["scored_metrics_persisted"] is False
    assert payload["s1_dates_read"] is False
    assert len(payload["arms"]) == 3
    keys = _recursive_key_scan(payload)
    assert not any(any(name in key for name in SCORED_FIELD_NAMES) for key in keys)


def test_zero_event_book_would_be_refused_by_the_gate(tmp_path):
    """A C1 book on negative-only shocks has no fills: the gate must refuse."""
    sessions, returns = shock_fixture(80, {"XLK": {62: -0.06}})
    raw_close = {sym: {s: 100.0 for s in series} for sym, series in returns.items()}
    report = dry_run_arm(ARM_C1, sessions, returns, raw_close, {}, {},
                         ledger_dir=str(tmp_path / "led"),
                         publish_to_temp_ledger=True)
    assert report.feasibility["n_entries_committed"] == 0
    assert report.gate["n_refusals"] == 1
    assert report.gate["published"] is False
    assert report.gate["ledger_published_keys"] == 0


@pytest.mark.skipif(not os.path.isdir(STAGING),
                    reason=f"UNAVAILABLE: V2 staging snapshot not present at {STAGING}")
class TestRealStagedS0DryRun:
    """Schedule + valuation only, on the real staged snapshot, S0 window."""

    def test_s0_load_bounds_and_seal(self):
        inputs = load_s0_snapshot_inputs(STAGING)
        sessions = inputs["sessions"]
        assert sessions[0] == S0_START.isoformat()
        assert sessions[-1] == S0_END.isoformat()
        assert not any(d >= "2025-08-01" for d in sessions)
        for symbol, closes in inputs["raw_close"].items():
            assert not any(d >= "2025-08-01" for d in closes)
        # distribution records truncated to pre-S1 dates before use
        for symbol, dists in inputs["distributions"].items():
            assert not any(d >= "2025-08-01" for d in dists)

    def test_schedule_only_feasibility_three_arms(self):
        inputs = load_s0_snapshot_inputs(STAGING)
        from research.stocks_free_v3.family_idio_shock.dryrun import (
            _issuer_tr_returns,
        )
        from research.stocks_free_v3.family_idio_shock.schedule import (
            build_arm_schedule,
            schedule_feasibility,
        )
        returns = _issuer_tr_returns(inputs)
        sessions = inputs["sessions"]
        summaries = {}
        for arm in (ARM_A1, ARM_N1, ARM_C1):
            result = build_arm_schedule(arm, sessions, returns)
            feas = schedule_feasibility(sessions, result, arm)
            summaries[arm.arm_id] = feas
            # frozen invariants hold on real data (enforced by the builder)
            assert feas.gross_within_limit is True
            assert feas.max_gross_observed == pytest.approx(0.5)
            assert feas.within_turnover_ceiling is True
            assert feas.n_sessions == len(sessions)
            assert feas.entries_per_year <= 5.0 + 1e-9  # the structural budget
        # deterministic: rebuilding arm A1 reproduces the same schedule digest
        again = build_arm_schedule(ARM_A1, sessions, returns)
        assert again.schedule_digest == summaries[ARM_A1.arm_id].schedule_digest

    def test_dry_run_real_s0_temp_ledger_only(self, tmp_path):
        payload = dry_run_real_s0(STAGING, publish_to_temp_ledger=True)
        assert payload["scored_metrics_computed"] is False
        assert payload["scored_metrics_persisted"] is False
        assert payload["s1_dates_read"] is False
        assert payload["data"]["last_session"] == S0_END.isoformat()
        assert not any(d >= "2025-08-01" for d in [payload["data"]["last_session"]])
        keys = _recursive_key_scan(payload)
        assert not any(any(name in key for name in SCORED_FIELD_NAMES)
                       for key in keys)
        for arm in payload["arms"]:
            assert arm["valuation_accounting"]["attribution_reconciles"] is True
            gate = arm["publication_gate"]
            assert gate["published"] is True
            assert gate["ledger_persisted_permanently"] is False
            assert gate["n_fill_events"] > 0
            assert gate["n_held_positions"] > 0

    def test_arm_digests_present_in_payload(self):
        payload = dry_run_real_s0(STAGING, arms=(ARM_A1,))
        assert payload["arms"][0]["config_digest"] == ARM_A1.config_digest
        assert len(payload["arms"][0]["schedule_digest"]) == 64
