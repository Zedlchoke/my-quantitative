"""A3 gate tests: pass & fail path for every hard gate G0..G5.

Sprint V2 additions: G0 requires a REAL coverage payload (fail-closed
INCONCLUSIVE otherwise), G1 requires an explicit evidence dict, G2 uses the
ReproductionComparison struct where ANY hash mismatch is ALWAYS FAIL, and G3
trade shortfall maps to INCONCLUSIVE per PLAN section 9.
"""

from __future__ import annotations

import pytest

from contracts.protocol import GateId, GateVerdict
from research.protocol.gates import (
    DataGateInput,
    GateInputs,
    LeakageGateInput,
    PortfolioInput,
    ReproGateInput,
    ReproductionComparison,
    RerunComparison,
    StageAInput,
    SurvivorInput,
    evaluate_gates,
    evaluate_reproduction,
)

HASH_A = "a" * 64
HASH_B = "b" * 64


def _coverage_payload(**symbol_overrides) -> dict:
    """Minimal REAL-artifact-shaped coverage payload (clean by default)."""
    bars = {"duplicate_timestamps": 0, "gaps_over_interval": 0}
    funding = {"bundle_present": True, "covers_declared_window": True, "coverage_ratio": 1.0}
    entry = {
        "instrument_metadata_present": True,
        "bars": {**bars, **symbol_overrides.get("bars", {})},
        "funding": {**funding, **symbol_overrides.get("funding", {})},
    }
    if "instrument_metadata_present" in symbol_overrides:
        entry["instrument_metadata_present"] = symbol_overrides["instrument_metadata_present"]
    return {"symbols": {"SOLUSDT": entry, "ETHUSDT": {**entry}}}


def _g1_evidence(**overrides) -> dict:
    evidence = {
        "split_policy_declared": True,
        "warmup_outside_window": {"warmup_days": 10, "bars_incl_warmup": 12640},
        "transforms_fit_on_train": True,
        "universe_frozen_before_run": {"lock_utc": "2026-08-23T00:00:00+00:00"},
        "execution_model_declared": {"fee_model": "maker_taker", "slippage_model": "one_tick"},
    }
    evidence.update(overrides)
    return evidence


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
    results = evaluate_gates({"data": {"coverage_payload": _coverage_payload(), "duplicates_present": True}})
    g0 = results[0]
    assert g0.verdict is GateVerdict.FAIL and "duplicate_bars" in g0.reasons


# ------------------------------- G0 ---------------------------------------- #
def test_g0_pass():
    result = evaluate_gates(
        GateInputs(data=DataGateInput(coverage_payload=_coverage_payload()))
    )[0]
    assert result.verdict is GateVerdict.PASS and result.reasons == ()


def test_g0_fail_all_reasons():
    payload = _coverage_payload(
        bars={"duplicate_timestamps": 3, "gaps_over_interval": 1},
        funding={"bundle_present": False, "covers_declared_window": False},
        instrument_metadata_present=False,
    )
    result = evaluate_gates(
        GateInputs(
            data=DataGateInput(
                catalog_current=False,
                coverage_payload=payload,
            )
        )
    )[0]
    assert result.verdict is GateVerdict.FAIL
    assert set(result.reasons) == {
        "duplicate_bars",
        "unexplained_gap",
        "funding_coverage_insufficient",
        "missing_instrument_metadata",
        "catalog_not_current",
    }


def test_g0_missing_payload_is_inconclusive_not_pass():
    for section in (
        DataGateInput(),
        DataGateInput(coverage_payload=None),
        DataGateInput(coverage_payload={}),
        DataGateInput(coverage_payload={"symbols": {}}),
    ):
        result = evaluate_gates(GateInputs(data=section))[0]
        assert result.verdict is GateVerdict.INCONCLUSIVE
        assert result.reasons == ("g0_coverage_not_evidenced",)


@pytest.mark.parametrize(
    "payload",
    [
        {"symbols": {"SOLUSDT": {"bars": {"duplicate_timestamps": 0}}}},  # missing keys
        {"symbols": {"SOLUSDT": "junk"}},  # non-mapping symbol entry
        {"universe": ["SOLUSDT"]},  # symbols block absent
        {"symbols": {"SOLUSDT": {"bars": {"duplicate_timestamps": 0, "gaps_over_interval": 0},
                                  "instrument_metadata_present": True}}},  # funding absent
        {"symbols": {"SOLUSDT": {"bars": {"gaps_over_interval": 0},
                                  "instrument_metadata_present": True,
                                  "funding": {"bundle_present": True, "covers_declared_window": True}}}},
    ],
)
def test_g0_malformed_payload_is_fail_closed(payload):
    result = evaluate_gates(GateInputs(data=DataGateInput(coverage_payload=payload)))[0]
    assert result.verdict is GateVerdict.INCONCLUSIVE
    assert result.reasons == ("g0_coverage_not_evidenced",)


def test_g0_funding_coverage_ratio_below_one_fails():
    payload = _coverage_payload(funding={"bundle_present": True, "covers_declared_window": True,
                                         "coverage_ratio": 0.93})
    result = evaluate_gates(GateInputs(data=DataGateInput(coverage_payload=payload)))[0]
    assert result.verdict is GateVerdict.FAIL and "coverage_below_declared" in result.reasons


# ------------------------------- G1 ---------------------------------------- #
def test_g1_pass_with_full_evidence():
    result = evaluate_gates(
        GateInputs(leakage=LeakageGateInput(evidence=_g1_evidence()))
    )[1]
    assert result.verdict is GateVerdict.PASS


def test_g1_missing_or_partial_evidence_is_inconclusive():
    full = _g1_evidence()
    for key in sorted(full):
        partial = {k: v for k, v in full.items() if k != key}
        result = evaluate_gates(GateInputs(leakage=LeakageGateInput(evidence=partial)))[1]
        assert result.verdict is GateVerdict.INCONCLUSIVE
        assert result.reasons == ("g1_evidence_missing",)
    # No evidence dict at all -> fail-closed too.
    result = evaluate_gates(GateInputs(leakage=LeakageGateInput()))[1]
    assert result.verdict is GateVerdict.INCONCLUSIVE
    assert result.reasons == ("g1_evidence_missing",)
    # Explicit null value counts as missing.
    result = evaluate_gates(
        GateInputs(leakage=LeakageGateInput(evidence=_g1_evidence(transforms_fit_on_train=None)))
    )[1]
    assert result.verdict is GateVerdict.INCONCLUSIVE


def test_g1_fail_each_leakage_vector():
    result = evaluate_gates(
        GateInputs(
            leakage=LeakageGateInput(
                scored_fold_in_selection=True,
                warmup_inside_window=True,
                universe_not_frozen=True,
                posthoc_regime_gate=True,
                evidence=_g1_evidence(),
            )
        )
    )[1]
    assert result.verdict is GateVerdict.FAIL
    assert set(result.reasons) == {
        "scored_fold_in_selection",
        "warmup_inside_window",
        "universe_not_frozen",
        "posthoc_regime_gate",
    }


def test_g1_contradicted_evidence_maps_to_fail_codes():
    result = evaluate_gates(
        GateInputs(
            leakage=LeakageGateInput(
                evidence=_g1_evidence(
                    split_policy_declared=False,
                    warmup_outside_window=False,
                    universe_frozen_before_run=False,
                )
            )
        )
    )[1]
    assert result.verdict is GateVerdict.FAIL
    assert {"split_policy_missing", "warmup_inside_window", "universe_not_frozen"}.issubset(
        result.reasons
    )


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


# --------------------- G2 reproduction struct (V2) ------------------------- #
def _matching_comparison(**overrides) -> dict:
    comparison = {
        "config_sha256_expected": HASH_A,
        "config_sha256_actual": HASH_A,
        "candidate_sha256_expected": HASH_B,
        "candidate_sha256_actual": HASH_B,
        "data_manifest_sha256_expected": HASH_A,
        "data_manifest_sha256_actual": HASH_A,
        "positions_digest_original": "digest-1",
        "positions_digest_rerun": "digest-1",
        "canonical_pnl_original": 123.456,
        "canonical_pnl_rerun": 123.456 * (1 + 1e-9),
        "pnl_rtol": 1e-6,
    }
    comparison.update(overrides)
    return comparison


def test_g2_reproduction_struct_pass_when_all_evidence_matches():
    result = evaluate_reproduction(ReproductionComparison(**_matching_comparison()))
    assert result.verdict is GateVerdict.PASS and result.reasons == ()
    # Also reachable through evaluate_gates with the precedence wiring.
    via_gates = evaluate_gates(
        GateInputs(reproduction=ReproductionComparison(**_matching_comparison()))
    )[2]
    assert via_gates.verdict is GateVerdict.PASS


def test_g2_hash_mismatch_always_fails_even_with_identical_pnl():
    # THE no-benign-interpretation rule: PnL matches EXACTLY, digest matches,
    # but one frozen hash differs -> FAIL, always.
    result = evaluate_reproduction(
        ReproductionComparison(
            **_matching_comparison(
                config_sha256_actual="c" * 64,
                canonical_pnl_rerun=123.456,
                positions_digest_rerun="digest-1",
            )
        )
    )
    assert result.verdict is GateVerdict.FAIL
    assert result.reasons == ("hash_mismatch",)


def test_g2_all_hash_mismatches_reported_together():
    result = evaluate_reproduction(
        ReproductionComparison(
            **_matching_comparison(
                candidate_sha256_actual="d" * 64,
                data_manifest_sha256_actual="e" * 64,
            )
        )
    )
    assert result.verdict is GateVerdict.FAIL
    assert result.reasons == ("hash_mismatch",)


def test_g2_missing_hashes_fail_closed():
    result = evaluate_reproduction(
        ReproductionComparison(
            **_matching_comparison(data_manifest_sha256_expected=None)
        )
    )
    assert result.verdict is GateVerdict.FAIL
    assert "manifest_missing_field" in result.reasons


def test_g2_positions_digest_mismatch_fails():
    result = evaluate_reproduction(
        ReproductionComparison(
            **_matching_comparison(positions_digest_rerun="digest-2")
        )
    )
    assert result.verdict is GateVerdict.FAIL
    assert "positions_digest_mismatch" in result.reasons


def test_g2_canonical_pnl_beyond_tolerance_fails():
    result = evaluate_reproduction(
        ReproductionComparison(
            **_matching_comparison(canonical_pnl_rerun=124.0)  # > 1e-6 rel
        )
    )
    assert result.verdict is GateVerdict.FAIL
    assert "rerun_pnl_mismatch" in result.reasons


def test_g2_reproduction_not_performed_is_not_yet_tested():
    result = evaluate_reproduction(
        ReproductionComparison(**_matching_comparison(rerun_performed=False))
    )
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


def test_g3_trades_below_min_is_inconclusive_per_plan_v2():
    stage = StageAInput(exp_after_cost=0.4, pf_after_cost=1.3, total_trades=19)
    result = evaluate_gates(GateInputs(stage_a=stage))[3]
    assert result.verdict is GateVerdict.INCONCLUSIVE
    assert result.reasons == ("trades_below_min",)


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
