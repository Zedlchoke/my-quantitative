"""A3 gate tests: pass & fail path for every hard gate G0..G5."""

from __future__ import annotations

import pytest

from contracts.protocol import GateId, GateVerdict
from research.protocol.gates import (
    DataGateInput,
    GateInputs,
    LeakageGateInput,
    PortfolioInput,
    ReproGateInput,
    RerunComparison,
    StageAInput,
    SurvivorInput,
    evaluate_gates,
)


def _passing_stage_a() -> StageAInput:
    return StageAInput(
        exp_after_cost=0.35,
        pf_after_cost=1.45,
        total_trades=60,
        folds=[
            {"fold_id": "f1", "trades": 20, "pnl_after_cost": 6.0, "exp_after_cost": 0.3, "pf_after_cost": 1.6},
            {"fold_id": "f2", "trades": 20, "pnl_after_cost": 5.0, "exp_after_cost": 0.25, "pf_after_cost": 1.3},
            {"fold_id": "f3", "trades": 20, "pnl_after_cost": 4.0, "exp_after_cost": 0.20, "pf_after_cost": 1.15},
        ],
    )


def test_gate_order_and_defaults_are_na():
    results = evaluate_gates(GateInputs())
    assert [r.gate for r in results] == list(GateId)
    assert all(r.verdict is GateVerdict.NOT_APPLICABLE for r in results[:4])
    assert results[4].verdict is GateVerdict.NOT_IMPLEMENTED
    assert results[5].verdict is GateVerdict.NOT_APPLICABLE


def test_evaluate_gates_accepts_plain_dicts():
    results = evaluate_gates({"data": {"duplicates_present": True}})
    g0 = results[0]
    assert g0.verdict is GateVerdict.FAIL and "duplicate_bars" in g0.reasons


# ------------------------------- G0 ---------------------------------------- #
def test_g0_pass():
    result = evaluate_gates(GateInputs(data=DataGateInput(coverage_ratio=1.0)))[0]
    assert result.verdict is GateVerdict.PASS and result.reasons == ()


def test_g0_fail_all_reasons():
    result = evaluate_gates(
        GateInputs(
            data=DataGateInput(
                duplicates_present=True,
                unexplained_gaps=True,
                funding_coverage_complete=False,
                instrument_metadata_ok=False,
                catalog_current=False,
                coverage_ratio=0.7,
            )
        )
    )[0]
    assert result.verdict is GateVerdict.FAIL
    assert set(result.reasons) == {
        "duplicate_bars",
        "unexplained_gap",
        "coverage_below_declared",
        "funding_coverage_insufficient",
        "missing_instrument_metadata",
        "catalog_not_current",
    }


# ------------------------------- G1 ---------------------------------------- #
def test_g1_pass_with_declared_split_policy():
    result = evaluate_gates(GateInputs(leakage=LeakageGateInput()))[1]
    assert result.verdict is GateVerdict.PASS


def test_g1_fail_each_leakage_vector():
    result = evaluate_gates(
        GateInputs(
            leakage=LeakageGateInput(
                scored_fold_in_selection=True,
                warmup_inside_window=True,
                universe_not_frozen=True,
                posthoc_regime_gate=True,
                split_policy_declared=False,
            )
        )
    )[1]
    assert result.verdict is GateVerdict.FAIL
    assert set(result.reasons) == {
        "scored_fold_in_selection",
        "warmup_inside_window",
        "universe_not_frozen",
        "posthoc_regime_gate",
        "split_policy_missing",
    }


# ------------------------------- G2 ---------------------------------------- #
def test_g2_pass_full_reproducibility():
    inputs = GateInputs(
        reproducibility=ReproGateInput(
            manifest_complete=True,
            rerun=RerunComparison(performed=True, matches=True, config_hash_matches=True),
        )
    )
    assert evaluate_gates(inputs)[2].verdict is GateVerdict.PASS


def test_g2_fail_manifest_incomplete_then_hash_then_rerun():
    base = dict(rerun=RerunComparison(performed=True, matches=True))
    incomplete = GateInputs(reproducibility=ReproGateInput(manifest_complete=False, **base))
    result = evaluate_gates(incomplete)[2]
    assert result.verdict is GateVerdict.FAIL
    assert "manifest_missing_field" in result.reasons

    hash_bad = GateInputs(
        reproducibility=ReproGateInput(
            manifest_complete=True,
            rerun=RerunComparison(performed=True, matches=True, config_hash_matches=False),
        )
    )
    result = evaluate_gates(hash_bad)[2]
    assert result.verdict is GateVerdict.FAIL and "hash_mismatch" in result.reasons

    mismatch = GateInputs(
        reproducibility=ReproGateInput(
            manifest_complete=True,
            rerun=RerunComparison(
                performed=True,
                matches=False,
                reasons=("rerun_pnl_mismatch",),
                config_hash_matches=True,
            ),
        )
    )
    result = evaluate_gates(mismatch)[2]
    assert result.verdict is GateVerdict.FAIL
    assert "rerun_pnl_mismatch" in result.reasons


def test_g2_rerun_not_performed_is_not_yet_tested():
    inputs = GateInputs(reproducibility=ReproGateInput(manifest_complete=True))
    result = evaluate_gates(inputs)[2]
    assert result.verdict is GateVerdict.NOT_YET_TESTED


# ------------------------------- G3 ---------------------------------------- #
def test_g3_pass_healthy_strategy():
    result = evaluate_gates(GateInputs(stage_a=_passing_stage_a()))[3]
    assert result.verdict is GateVerdict.PASS and result.reasons == ()


def test_g3_fail_negative_expectancy_and_weak_pf():
    stage = StageAInput(exp_after_cost=-0.1, pf_after_cost=1.05, total_trades=40)
    result = evaluate_gates(GateInputs(stage_a=stage))[3]
    assert result.verdict is GateVerdict.FAIL
    assert {"exp_nonpositive", "pf_below_min"}.issubset(result.reasons)


def test_g3_fail_positive_fold_ratio_and_fold_pf_floor():
    folds = [
        {"fold_id": "f1", "trades": 20, "pnl_after_cost": 9.0, "exp_after_cost": 0.45, "pf_after_cost": 2.0},
        {"fold_id": "f2", "trades": 20, "pnl_after_cost": -4.0, "exp_after_cost": -0.2, "pf_after_cost": 0.5},
        {"fold_id": "f3", "trades": 20, "pnl_after_cost": -3.0, "exp_after_cost": -0.15, "pf_after_cost": 0.6},
    ]
    stage = StageAInput(
        exp_after_cost=0.03, pf_after_cost=1.12, total_trades=60, folds=folds
    )
    result = evaluate_gates(GateInputs(stage_a=stage))[3]
    assert result.verdict is GateVerdict.FAIL
    assert "positive_folds_ratio_low" in result.reasons
    assert "fold_pf_below_floor" in result.reasons


def test_g3_fail_fold_concentration_from_caller_pct():
    stage = StageAInput(
        exp_after_cost=0.4,
        pf_after_cost=1.4,
        total_trades=40,
        top_fold_contribution_pct=62.0,
    )
    result = evaluate_gates(GateInputs(stage_a=stage))[3]
    assert result.verdict is GateVerdict.FAIL
    assert "fold_concentration_high" in result.reasons


def test_g3_fail_symbol_masked_by_average():
    symbols = [
        {"symbol": "ETHUSDT", "trades": 30, "pnl_after_cost": 10.0, "exp_after_cost": 0.3},
        {"symbol": "SOLUSDT", "trades": 25, "pnl_after_cost": -2.0, "exp_after_cost": -0.08},
    ]
    stage = StageAInput(
        exp_after_cost=0.15,
        pf_after_cost=1.2,
        total_trades=55,
        symbols=symbols,
    )
    result = evaluate_gates(GateInputs(stage_a=stage))[3]
    assert result.verdict is GateVerdict.FAIL
    assert "symbol_masked_by_average" in result.reasons


def test_g3_trades_below_min_maps_to_not_yet_tested():
    stage = StageAInput(exp_after_cost=0.4, pf_after_cost=1.3, total_trades=19)
    result = evaluate_gates(GateInputs(stage_a=stage))[3]
    assert result.verdict is GateVerdict.NOT_YET_TESTED
    assert "trades_below_min" in result.reasons


def test_g3_missing_aggregates_is_not_yet_tested():
    stage = StageAInput(exp_after_cost=None, pf_after_cost=None)
    result = evaluate_gates(GateInputs(stage_a=stage))[3]
    assert result.verdict is GateVerdict.NOT_YET_TESTED
    assert "metric_not_computed" in result.reasons


# ------------------------------- G4 ---------------------------------------- #
def test_g4_absent_inputs_not_implemented():
    result = evaluate_gates(GateInputs())[4]
    assert result.verdict is GateVerdict.NOT_IMPLEMENTED
    assert "slippage_stress_not_implemented" in result.reasons


def test_g4_pass_when_all_checks_executed_clean():
    survivor = SurvivorInput(
        fee_stress_positive=True,
        delay_stress_positive=True,
        delay_stress_supported=True,
        neighborhood_spike_detected=False,
        dropone_signflip_detected=False,
    )
    result = evaluate_gates(GateInputs(survivor=survivor))[4]
    assert result.verdict is GateVerdict.PASS and result.reasons == ()


def test_g4_fail_fee_flip_and_spike():
    survivor = SurvivorInput(
        fee_stress_positive=False,
        neighborhood_spike_detected=True,
        dropone_signflip_detected=False,
    )
    result = evaluate_gates(GateInputs(survivor=survivor))[4]
    assert result.verdict is GateVerdict.FAIL
    assert {"fee_stress_negative", "neighborhood_spike"}.issubset(result.reasons)


def test_g4_partial_execution_not_implemented():
    survivor = SurvivorInput(fee_stress_positive=True)
    result = evaluate_gates(GateInputs(survivor=survivor))[4]
    assert result.verdict is GateVerdict.NOT_IMPLEMENTED
    assert "neighborhood_spike" in result.reasons


def test_g4_delay_flip_fails_even_without_support_flag():
    survivor = SurvivorInput(
        fee_stress_positive=True,
        delay_stress_positive=False,
        neighborhood_spike_detected=False,
        dropone_signflip_detected=False,
    )
    result = evaluate_gates(GateInputs(survivor=survivor))[4]
    assert result.verdict is GateVerdict.FAIL
    assert "delay_stress_negative" in result.reasons


# ------------------------------- G5 ---------------------------------------- #
def test_g5_absent_inputs_na():
    assert evaluate_gates(GateInputs())[5].verdict is GateVerdict.NOT_APPLICABLE


def test_g5_pass():
    portfolio = PortfolioInput(portfolio_pnl=42.0, portfolio_pf=1.35,
                               max_symbol_contribution_pct=0.31)
    result = evaluate_gates(GateInputs(portfolio=portfolio))[5]
    assert result.verdict is GateVerdict.PASS


def test_g5_fail_every_portfolio_rule():
    portfolio = PortfolioInput(
        portfolio_pnl=-1.0,
        portfolio_pf=1.05,
        limits_ok=False,
        max_symbol_contribution_pct=55.0,
    )
    result = evaluate_gates(GateInputs(portfolio=portfolio))[5]
    assert result.verdict is GateVerdict.FAIL
    assert set(result.reasons) == {
        "portfolio_pnl_nonpositive",
        "portfolio_pf_below_min",
        "limit_violation",
        "symbol_contribution_high",
    }


@pytest.mark.parametrize(
    ("section_payload", "index"),
    [
        ({"data": {}}, 0),
        ({"leakage": {}}, 1),
        ({"reproducibility": {"manifest_complete": True}}, 2),
        ({"stage_a": {"exp_after_cost": 0.2, "pf_after_cost": 1.2}}, 3),
    ],
)
def test_partial_sections_leave_other_gates_na(section_payload, index):
    results = evaluate_gates(section_payload)
    assert results[index].verdict is not GateVerdict.NOT_APPLICABLE
    for i, result in enumerate(results):
        if i == index:
            continue
        if i == 4:
            continue  # G4 defaults to NOT_IMPLEMENTED
        assert result.verdict is GateVerdict.NOT_APPLICABLE
