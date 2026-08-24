"""Threshold-edge unit fixtures for Sprint V4 XG gates (A3, D2)."""

from __future__ import annotations

import pytest

from contracts.protocol import (
    ArtifactIntegrityResult,
    GateVerdict,
    IndependentReproductionResult,
)
from research.protocol.gates import (
    PortfolioConstraints,
    XGateId,
    XRobustnessInput,
    XStageAInput,
    XRiskInput,
    evaluate_parameter_spike,
    evaluate_xg5,
    evaluate_xgates,
)


def _coverage(days=10, required=10, btc_clean=True, btc_days=10, symbols=None,
              benchmark=None):
    benchmark = benchmark or {
        "symbol": "BTCUSDT", "days_present": btc_days, "clean": btc_clean,
    }
    symbols = symbols or {
        "ETHUSDT": {"days_present": days},
        "SOLUSDT": {"days_present": days},
    }
    return {
        "required_days": required,
        "traded_symbols": dict(symbols),
        "benchmark": benchmark,
    }


def _pit(**overrides):
    evidence = {
        "features_completed_before_signal": True,
        "signal_before_every_fill": True,
        "membership_tie_deterministic": True,
        "execution_bar_excluded": True,
        "warmup_boundaries": {"warmup_start": "w", "scored_start": "s", "scored_end": "e"},
    }
    evidence.update(overrides)
    return {k: v for k, v in evidence.items() if v is not ...}


def _stage_a(**overrides):
    base = dict(
        pnl=100.0,
        pf=1.20,
        pf_reason=None,
        expectancy_r=0.05,
        folds=(
            {"fold_id": "f1", "pnl": 40.0, "exp_r": 0.06},
            {"fold_id": "f2", "pnl": 35.0, "exp_r": 0.05},
            {"fold_id": "f3", "pnl": 25.0, "exp_r": 0.04},
        ),
        rebalances_scored=30,
        legs_closed=100,
        top_fold_contribution=None,
        top_symbol_contribution=0.30,
    )
    base.update(overrides)
    return XStageAInput(**base)


def _robust(**overrides):
    base = dict(
        fee50_exp_r=0.02,
        twotick_exp_r=0.01,
        extradelay_exp_r=0.01,
        dropone_symbol_clean=True,
        dropone_fold_clean=True,
        turnover_budget_exceeded=False,
    )
    base.update(overrides)
    return XRobustnessInput(**base)


def _risk(**overrides):
    base = dict(
        gross_max=1.0,
        net_abs_max=0.05,
        max_abs_weight=0.25,
        margin_breach_rows=0,
        top_symbol_contribution=0.40,
        realized_beta=0.25,
        mdd_fraction=0.08,
    )
    base.update(overrides)
    return XRiskInput(**base)


def _integrity_ok():
    return ArtifactIntegrityResult(
        schema_valid=True, hashes_match=True,
        positions_reconcile=True, report_index_reconcile=True,
    )


# ------------------------------- XG0 ---------------------------------------- #
def test_xg0_missing_payload_inconclusive():
    result = evaluate_xgates({"coverage": None})[0]
    assert result.gate == XGateId.XG0_DATA_UNIVERSE
    assert result.verdict is GateVerdict.INCONCLUSIVE
    assert result.reasons == ("g0_coverage_not_evidenced",)


def test_xg0_malformed_payload_inconclusive():
    for bad in ({}, {"traded_symbols": {}}, {"traded_symbols": {"E": {}}, "required_days": 5},
                _coverage(benchmark={"symbol": "BTCUSDT"})):
        assert evaluate_xgates({"coverage": bad})[0].verdict is GateVerdict.INCONCLUSIVE


def test_xg0_clean_panel_passes_and_btc_dirty_fails():
    ok = evaluate_xgates({"coverage": _coverage()})[0]
    assert ok.verdict is GateVerdict.PASS
    dirty_btc = evaluate_xgates({"coverage": _coverage(btc_clean=False)})[0]
    assert dirty_btc.verdict is GateVerdict.FAIL
    short_days = evaluate_xgates({"coverage": _coverage(days=9)})[0]
    assert short_days.verdict is GateVerdict.FAIL
    assert "coverage_below_declared" in short_days.reasons


def test_xg0_silent_symbol_exclusion_detected():
    payload = _coverage()
    declared = list(payload["traded_symbols"]) + ["XRPUSDT"]
    result = evaluate_xgates({"coverage": payload, "declared_symbols": declared})[0]
    assert result.verdict is GateVerdict.FAIL
    assert "coverage_below_declared" in result.reasons


# ------------------------------- XG1 ---------------------------------------- #
def test_xg1_complete_evidence_passes():
    assert evaluate_xgates({"pit_evidence": _pit()})[1].verdict is GateVerdict.PASS


def test_xg1_missing_or_null_key_inconclusive():
    for mutate in ({"features_completed_before_signal": ...},
                   {"signal_before_every_fill": None},
                   {"warmup_boundaries": ...}):
        result = evaluate_xgates({"pit_evidence": _pit(**mutate)})[1]
        assert result.verdict is GateVerdict.INCONCLUSIVE
        assert result.reasons == ("g1_evidence_missing",)


def test_xg1_warmup_missing_subkey_inconclusive():
    evidence = _pit(warmup_boundaries={"warmup_start": "w", "scored_start": "s"})
    result = evaluate_xgates({"pit_evidence": evidence})[1]
    assert result.verdict is GateVerdict.INCONCLUSIVE


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"signal_before_every_fill": False}, "signal_fill_ordering_violation"),
        ({"features_completed_before_signal": False}, "feature_lookahead_detected"),
        ({"execution_bar_excluded": False}, "execution_bar_in_lookback"),
        ({"membership_tie_deterministic": False}, "membership_nondeterministic"),
    ],
)
def test_xg1_contradicted_claims_fail(override, expected):
    result = evaluate_xgates({"pit_evidence": _pit(**override)})[1]
    assert result.verdict is GateVerdict.FAIL and expected in result.reasons


# ----------------------------- XG2a / XG2b ---------------------------------- #
def test_xg2a_reuses_artifact_integrity_verdict():
    rows = evaluate_xgates({"artifact_integrity": _integrity_ok()})
    assert rows[2].gate == XGateId.XG2A_ARTIFACT_INTEGRITY
    assert rows[2].verdict is GateVerdict.PASS
    bad = ArtifactIntegrityResult(
        schema_valid=True, hashes_match=False,
        positions_reconcile=True, report_index_reconcile=True,
        reasons=("hash_mismatch",),
    )
    assert evaluate_xgates({"artifact_integrity": bad})[2].verdict is GateVerdict.FAIL


def test_xg2b_not_yet_tested_without_rerun_and_pass_with_match():
    rows = evaluate_xgates({})
    assert rows[3].verdict is GateVerdict.NOT_YET_TESTED
    rerun = IndependentReproductionResult(
        performed=True, rerun_process_separate=True,
        parameters_match=True, positions_digest_match=True,
        trade_count_match=True, canonical_pnl_match=True,
    )
    assert evaluate_xgates({"independent_reproduction": rerun})[3].verdict is GateVerdict.PASS


# ------------------------------- XG3 ---------------------------------------- #
def test_xg3_baseline_passes_all_exact_thresholds():
    result = evaluate_xgates({"stage_a": _stage_a()})[4]
    assert result.gate == XGateId.XG3_STAGE_A_PORTFOLIO
    assert result.verdict is GateVerdict.PASS


def test_xg3_pnl_zero_is_fail_and_pf_boundary():
    assert evaluate_xgates({"stage_a": _stage_a(pnl=0.0)})[4].verdict is GateVerdict.FAIL
    below = evaluate_xgates({"stage_a": _stage_a(pf=1.0999)})[4]
    assert below.verdict is GateVerdict.FAIL and "pf_below_min" in below.reasons
    at = evaluate_xgates({"stage_a": _stage_a(pf=PortfolioConstraints.MIN_POSITION_PF)})[4]
    assert at.verdict is GateVerdict.PASS


def test_xg3_undefined_pf_blocks_pass_with_its_reason():
    result = evaluate_xgates({"stage_a": _stage_a(pf=None, pf_reason="no_losing_positions")})[4]
    assert result.verdict is GateVerdict.FAIL
    assert "no_losing_positions" in result.reasons


def test_xg3_expectancy_none_is_inconclusive_negative_is_fail():
    inc = evaluate_xgates({"stage_a": _stage_a(expectancy_r=None)})[4]
    assert inc.verdict is GateVerdict.INCONCLUSIVE
    assert inc.reasons == ("metric_not_computed",)
    neg = evaluate_xgates({"stage_a": _stage_a(expectancy_r=-0.01)})[4]
    assert neg.verdict is GateVerdict.FAIL and "exp_nonpositive" in neg.reasons


def test_xg3_positive_folds_require_both_pnl_and_exp_r():
    folds = (
        {"fold_id": "f1", "pnl": -40.0, "exp_r": 0.06},  # expR positive but pnl negative
        {"fold_id": "f2", "pnl": 60.0, "exp_r": 0.05},
        {"fold_id": "f3", "pnl": 80.0, "exp_r": -0.01},
    )
    result = evaluate_xgates({"stage_a": _stage_a(folds=folds, top_fold_contribution=0.45)})[4]
    assert result.verdict is GateVerdict.FAIL
    assert "positive_folds_ratio_low" in result.reasons
    two_of_three = evaluate_xgates({"stage_a": _stage_a(
        folds=folds[:2] + ({"fold_id": "f3", "pnl": 65.0, "exp_r": 0.02},),
    )})[4]
    # positive agg 130; top fold share exactly 0.50 -> inside limit
    assert two_of_three.verdict is GateVerdict.PASS


def test_xg3_sample_size_shortfall_is_inconclusive():
    result = evaluate_xgates({"stage_a": _stage_a(rebalances_scored=29, legs_closed=100)})[4]
    assert result.verdict is GateVerdict.INCONCLUSIVE
    assert result.reasons == ("sample_below_min",)
    legs = evaluate_xgates({"stage_a": _stage_a(rebalances_scored=30, legs_closed=99)})[4]
    assert legs.verdict is GateVerdict.INCONCLUSIVE
    edge = evaluate_xgates({"stage_a": _stage_a(rebalances_scored=30, legs_closed=100)})[4]
    assert edge.verdict is GateVerdict.PASS


def test_xg3_top_fold_contribution_boundary_derived_from_folds():
    # f1=100, f2=60, f3=40 => positive agg 200; f1 share exactly 0.50 -> PASS
    folds = (
        {"fold_id": "f1", "pnl": 100.0, "exp_r": 0.03},
        {"fold_id": "f2", "pnl": 60.0, "exp_r": 0.03},
        {"fold_id": "f3", "pnl": 40.0, "exp_r": 0.03},
    )
    at_limit = evaluate_xgates({"stage_a": _stage_a(folds=folds)})[4]
    assert at_limit.verdict is GateVerdict.PASS
    over = evaluate_xgates({"stage_a": _stage_a(folds=(
        {"fold_id": "f1", "pnl": 101.0, "exp_r": 0.03},
        {"fold_id": "f2", "pnl": 60.0, "exp_r": 0.03},
        {"fold_id": "f3", "pnl": 40.0, "exp_r": 0.03},
    ))})[4]
    assert over.verdict is GateVerdict.FAIL and "fold_concentration_high" in over.reasons


def test_xg3_top_symbol_boundary():
    at = evaluate_xgates({"stage_a": _stage_a(top_symbol_contribution=0.40)})[4]
    assert at.verdict is GateVerdict.PASS
    over = evaluate_xgates({"stage_a": _stage_a(top_symbol_contribution=0.400001)})[4]
    assert over.verdict is GateVerdict.FAIL
    assert "symbol_contribution_high" in over.reasons


# ------------------------------- XG4 ---------------------------------------- #
def test_xg4_all_stresses_positive_passes():
    assert evaluate_xgates({"robustness": _robust()})[5].verdict is GateVerdict.PASS


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"fee50_exp_r": 0.0}, "fee_stress_negative"),
        ({"twotick_exp_r": -0.01}, "slippage_stress_negative"),
        ({"extradelay_exp_r": 0.0}, "delay_stress_negative"),
        ({"dropone_symbol_clean": False}, "dropone_signflip"),
        ({"dropone_fold_clean": False}, "dropone_signflip"),
        ({"turnover_budget_exceeded": True}, "limit_violation"),
    ],
)
def test_xg4_each_failure_reason(override, expected):
    result = evaluate_xgates({"robustness": _robust(**override)})[5]
    assert result.verdict is GateVerdict.FAIL and expected in result.reasons


def test_xg4_unexecuted_checks_are_inconclusive_never_pass():
    result = evaluate_xgates({"robustness": XRobustnessInput()})[5]
    assert result.verdict is GateVerdict.INCONCLUSIVE


def test_parameter_spike_adjacent_rule():
    spike = evaluate_parameter_spike({3: True, 7: False, 14: False})
    assert spike.verdict is GateVerdict.FAIL
    assert spike.reasons == ("parameter_spike_fail",)
    ok_left = evaluate_parameter_spike({3: True, 7: True, 14: False})
    ok_right = evaluate_parameter_spike({3: False, 7: True, 14: True})
    assert ok_left.verdict is GateVerdict.PASS and ok_right.verdict is GateVerdict.PASS
    incomplete = evaluate_parameter_spike({3: True, 7: None, 14: False})
    assert incomplete.verdict is GateVerdict.INCONCLUSIVE


# ------------------------------- XG5 ---------------------------------------- #
def test_xg5_within_all_limits_passes_no_lock_blocker():
    result, details = evaluate_xg5(_risk())
    assert result.verdict is GateVerdict.PASS
    assert details["mdd_lock_blocker"] is False


@pytest.mark.parametrize(
    ("override",),
    [
        ({"gross_max": 1.0000001},),
        ({"net_abs_max": 0.1000001},),
        ({"net_abs_max": -0.11},),
        ({"max_abs_weight": 0.2500001},),
        ({"margin_breach_rows": 1},),
        ({"top_symbol_contribution": 0.41},),
        ({"realized_beta": 0.2500001},),
        ({"realized_beta": -0.26},),
    ],
)
def test_xg5_each_violation_fails(override):
    result, _ = evaluate_xg5(_risk(**override))
    assert result.verdict is GateVerdict.FAIL


def test_xg5_beta_boundary_values_pass():
    for beta in (0.25, -0.25):
        result, _ = evaluate_xg5(_risk(realized_beta=beta))
        assert result.verdict is GateVerdict.PASS


def test_xg5_mdd_over_ten_percent_flags_lock_blocker_but_passes():
    result, details = evaluate_xg5(_risk(mdd_fraction=0.101))
    assert result.verdict is GateVerdict.PASS
    assert details["mdd_lock_blocker"] is True
    assert "mdd_lock_blocker" in result.reasons
    at_limit, details_at = evaluate_xg5(_risk(mdd_fraction=0.10))
    assert at_limit.verdict is GateVerdict.PASS
    assert details_at["mdd_lock_blocker"] is False


def test_xg5_missing_core_metric_inconclusive():
    result, _ = evaluate_xg5(_risk(gross_max=None))
    assert result.verdict is GateVerdict.INCONCLUSIVE


# --------------------------- full row set ----------------------------------- #
def test_evaluate_xgates_emits_fixed_seven_row_layout():
    rows = evaluate_xgates({})
    assert [row.gate.value for row in rows] == [
        "XG0_DATA_UNIVERSE", "XG1_POINT_IN_TIME", "XG2A_ARTIFACT_INTEGRITY",
        "XG2B_INDEPENDENT_REPRODUCIBILITY", "XG3_STAGE_A_PORTFOLIO",
        "XG4_ROBUSTNESS_EXECUTION", "XG5_SHARED_CAPITAL_RISK",
    ]


def test_full_pass_candidate_payload_end_to_end():
    rows = evaluate_xgates({
        "coverage": _coverage(),
        "declared_symbols": ["ETHUSDT", "SOLUSDT"],
        "pit_evidence": _pit(),
        "artifact_integrity": _integrity_ok(),
        "stage_a": _stage_a(),
        "robustness": _robust(),
        "risk": _risk(),
    })
    # Without an independent rerun XG2b stays NOT_YET_TESTED (fail-closed);
    # every other row must PASS on this clean candidate payload.
    assert all(row.verdict is GateVerdict.PASS for row in rows if row.gate != XGateId.XG2B_INDEPENDENT_REPRODUCIBILITY)
    assert rows[3].verdict is GateVerdict.NOT_YET_TESTED
