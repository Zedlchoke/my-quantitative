"""A3 gate tests: pass & fail path for every hard gate G0..G5 (V3 layout).

Sprint V3 changes covered here:

* ``evaluate_gates`` emits SEVEN rows: G0, G1, G2A, G2B, G3, G4, G5.
* G1 REQUIRES runner-emitted ``LeakageEvidence`` -- every way to remove or
  null one required piece of evidence yields INCONCLUSIVE (never PASS);
  ``fill_ts <= signal_ts`` violations yield FAIL; bare-boolean transform
  evidence is rejected.
* G2 is split: ``G2A_ARTIFACT_INTEGRITY`` from ArtifactIntegrityResult,
  ``G2B_INDEPENDENT_REPRODUCIBILITY`` from IndependentReproductionResult,
  including the NOT_YET_TESTED / PASS / FAIL / INCONCLUSIVE matrix and the
  promotion rule requiring BOTH to PASS.
"""

from __future__ import annotations

import dataclasses

import pytest

from contracts.protocol import (
    ArtifactIntegrityResult,
    IndependentReproductionResult,
    LeakageEvidence,
    GateVerdict,
)
from research.protocol.gates import (
    DataGateInput,
    GateInputs,
    LeakageGateInput,
    PortfolioInput,
    ProtocolGateId,
    RunnerLeakageGateInput,
    StageAInput,
    SurvivorInput,
    evaluate_gates,
    g2_promotion_pass,
)

HASH_A = "a" * 64


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


def _warmup_boundaries() -> dict:
    return {
        "warmup_start": "2025-08-11T14:30:00+00:00",
        "scored_start": "2025-08-21T14:30:00+00:00",
        "scored_end": "2026-08-21T00:00:00+00:00",
        "bars_incl_warmup_min": 1000,
        "scored_bars_max": 900,
    }


def _transform_evidence() -> dict:
    return {
        "status": "NOT_APPLICABLE",
        "reason": "no learned transform; indicators are stateless recursive",
    }


def _universe_freeze() -> dict:
    return {
        "candidate_locked_at_utc": "2026-08-23T09:20:00Z",
        "universe_sha256": HASH_A,
        "launch_commit": "1fbbdc6" + "0" * 33,
    }


def _execution_ordering(**overrides) -> dict:
    ordering = {
        "mode": "NEXT_BAR_EVENT_BASELINE",
        "entries": 12,
        "violations": 0,
        "evidence_class": "EXECUTION_EVIDENCE_COMPLETE",
    }
    ordering.update(overrides)
    return ordering


def _leakage_evidence(**overrides) -> LeakageEvidence:
    fields = {
        "split_policy_declared": True,
        "warmup_boundaries": _warmup_boundaries(),
        "transform_evidence": _transform_evidence(),
        "universe_freeze": _universe_freeze(),
        "execution_ordering": _execution_ordering(),
        "notes": (),
    }
    fields.update(overrides)
    return LeakageEvidence(**fields)


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


# --------------------------- layout ----------------------------------------- #
def test_gate_layout_is_seven_rows_with_separated_g2():
    results = evaluate_gates(GateInputs())
    assert [r.gate for r in results] == list(ProtocolGateId)
    assert results[2].gate.value == "G2A_ARTIFACT_INTEGRITY"
    assert results[3].gate.value == "G2B_INDEPENDENT_REPRODUCIBILITY"
    na_rows = [results[0], results[1], results[2], results[3], results[4], results[6]]
    assert all(r.verdict is GateVerdict.NOT_APPLICABLE for r in na_rows)
    assert results[5].verdict is GateVerdict.NOT_IMPLEMENTED


def test_evaluate_gates_accepts_plain_dicts():
    results = evaluate_gates({"data": {"coverage_payload": _coverage_payload(), "duplicates_present": True}})
    g0 = results[0]
    assert g0.verdict is GateVerdict.FAIL and "duplicate_bars" in g0.reasons


def test_dict_leakage_accepts_runner_evidence_instance():
    evidence = _leakage_evidence()
    results = evaluate_gates({"leakage": RunnerLeakageGateInput(evidence=evidence)})
    assert results[1].verdict is GateVerdict.PASS


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


# ------------------------------- G1 (V3 runner evidence) -------------------- #
def test_g1_runner_evidence_complete_is_the_only_path_to_pass():
    result = evaluate_gates(
        GateInputs(leakage=RunnerLeakageGateInput(evidence=_leakage_evidence()))
    )[1]
    assert result.verdict is GateVerdict.PASS and result.reasons == ()


@pytest.mark.parametrize("field_to_null", [
    "split_policy_declared",
    "warmup_boundaries",
    "transform_evidence",
    "universe_freeze",
    "execution_ordering",
])
def test_g1_missing_each_required_key_is_inconclusive(field_to_null):
    # dataclasses.replace on a frozen contract instance: null one field.
    evidence = dataclasses.replace(_leakage_evidence(), **{field_to_null: None})
    result = evaluate_gates(GateInputs(leakage=RunnerLeakageGateInput(evidence=evidence)))[1]
    assert result.verdict is GateVerdict.INCONCLUSIVE
    assert "g1_evidence_missing" in result.reasons


def test_g1_no_evidence_at_all_is_inconclusive():
    result = evaluate_gates(GateInputs(leakage=RunnerLeakageGateInput(evidence=None)))[1]
    assert result.verdict is GateVerdict.INCONCLUSIVE
    assert result.reasons == ("g1_evidence_missing",)


def test_g1_execution_ordering_violation_fails_hard():
    evidence = _leakage_evidence(
        execution_ordering=_execution_ordering(violations=2, evidence_class="ORDERING_VIOLATION_DETECTED")
    )
    result = evaluate_gates(GateInputs(leakage=RunnerLeakageGateInput(evidence=evidence)))[1]
    assert result.verdict is GateVerdict.FAIL
    assert "signal_fill_ordering_violation" in result.reasons


def test_g1_evidence_missing_execution_class_is_inconclusive():
    evidence = _leakage_evidence(
        execution_ordering=_execution_ordering(entries=0, evidence_class="EVIDENCE_MISSING")
    )
    result = evaluate_gates(GateInputs(leakage=RunnerLeakageGateInput(evidence=evidence)))[1]
    assert result.verdict is GateVerdict.INCONCLUSIVE
    assert result.reasons == ("g1_evidence_missing",)


def test_g1_bare_true_transform_evidence_rejected():
    evidence = _leakage_evidence(transform_evidence=True)
    result = evaluate_gates(GateInputs(leakage=RunnerLeakageGateInput(evidence=evidence)))[1]
    assert result.verdict is GateVerdict.INCONCLUSIVE
    assert "g1_evidence_missing" in result.reasons


def test_g1_not_applicable_transform_without_reason_rejected():
    evidence = _leakage_evidence(transform_evidence={"status": "NOT_APPLICABLE"})
    result = evaluate_gates(GateInputs(leakage=RunnerLeakageGateInput(evidence=evidence)))[1]
    assert result.verdict is GateVerdict.INCONCLUSIVE


def test_g1_split_policy_false_is_fail_even_with_otherwise_full_evidence():
    evidence = _leakage_evidence(split_policy_declared=False)
    result = evaluate_gates(GateInputs(leakage=RunnerLeakageGateInput(evidence=evidence)))[1]
    assert result.verdict is GateVerdict.FAIL
    assert "split_policy_missing" in result.reasons


def test_g1_universe_freeze_missing_keys_is_inconclusive():
    evidence = _leakage_evidence(universe_freeze={"candidate_locked_at_utc": "x"})
    result = evaluate_gates(GateInputs(leakage=RunnerLeakageGateInput(evidence=evidence)))[1]
    assert result.verdict is GateVerdict.INCONCLUSIVE


def test_g1_warmup_boundaries_empty_is_inconclusive():
    evidence = _leakage_evidence(warmup_boundaries={})
    result = evaluate_gates(GateInputs(leakage=RunnerLeakageGateInput(evidence=evidence)))[1]
    assert result.verdict is GateVerdict.INCONCLUSIVE


def test_g1_auditor_violation_flags_still_fail():
    evidence = _leakage_evidence()
    result = evaluate_gates(
        GateInputs(
            leakage=RunnerLeakageGateInput(
                evidence=evidence, scored_fold_in_selection=True
            )
        )
    )[1]
    assert result.verdict is GateVerdict.FAIL
    assert "scored_fold_in_selection" in result.reasons


# --------------------- G1 legacy dict shape (v1/v2 paths) ------------------- #
def _legacy_evidence(**overrides) -> dict:
    evidence = {
        "split_policy_declared": True,
        "warmup_outside_window": {"warmup_days": 10, "bars_incl_warmup": 12640},
        "transforms_fit_on_train": True,
        "universe_frozen_before_run": {"lock_utc": "2026-08-23T00:00:00+00:00"},
        "execution_model_declared": {"fee_model": "maker_taker", "slippage_model": "one_tick"},
    }
    evidence.update(overrides)
    return evidence


def test_g1_legacy_partial_evidence_is_inconclusive():
    full = _legacy_evidence()
    for key in sorted(full):
        partial = {k: v for k, v in full.items() if k != key}
        result = evaluate_gates(GateInputs(leakage=LeakageGateInput(evidence=partial)))[1]
        assert result.verdict is GateVerdict.INCONCLUSIVE
        assert result.reasons == ("g1_evidence_missing",)


def test_g1_legacy_full_evidence_passes():
    result = evaluate_gates(GateInputs(leakage=LeakageGateInput(evidence=_legacy_evidence())))[1]
    assert result.verdict is GateVerdict.PASS


# ------------------------------- G2A ---------------------------------------- #
def _integrity_result(**overrides) -> ArtifactIntegrityResult:
    fields = dict(
        schema_valid=True,
        hashes_match=True,
        positions_reconcile=True,
        report_index_reconcile=True,
        reasons=(),
    )
    fields.update(overrides)
    return ArtifactIntegrityResult(**fields)


def test_g2a_pass_when_all_integrity_checks_clean():
    result = evaluate_gates(GateInputs(artifact_integrity=_integrity_result()))[2]
    assert result.gate.value == "G2A_ARTIFACT_INTEGRITY"
    assert result.verdict is GateVerdict.PASS


@pytest.mark.parametrize(
    "override",
    [
        {"schema_valid": False},
        {"hashes_match": False},
        {"positions_reconcile": False},
        {"report_index_reconcile": False},
        {"reasons": ("hash_mismatch",)},
    ],
)
def test_g2a_fail_paths(override):
    result = evaluate_gates(GateInputs(artifact_integrity=_integrity_result(**override)))[2]
    assert result.verdict is GateVerdict.FAIL


# ------------------------------- G2B ---------------------------------------- #
def _reproduction_result(**overrides) -> IndependentReproductionResult:
    fields = dict(
        performed=True,
        rerun_process_separate=True,
        parameters_match=True,
        positions_digest_match=True,
        trade_count_match=True,
        canonical_pnl_match=True,
    )
    fields.update(overrides)
    return IndependentReproductionResult(**fields)


def test_g2b_not_yet_tested_when_rerun_not_performed():
    for section in (
        _reproduction_result(performed=False),
        _reproduction_result(performed=False, rerun_process_separate=False),
    ):
        result = evaluate_gates(GateInputs(independent_reproduction=section))[3]
        assert result.gate.value == "G2B_INDEPENDENT_REPRODUCIBILITY"
        assert result.verdict is GateVerdict.NOT_YET_TESTED


def test_g2b_pass_only_when_every_check_matches():
    result = evaluate_gates(GateInputs(independent_reproduction=_reproduction_result()))[3]
    assert result.verdict is GateVerdict.PASS


@pytest.mark.parametrize(
    "override",
    [
        {"parameters_match": False},
        {"positions_digest_match": False},
        {"trade_count_match": False},
        {"canonical_pnl_match": False},
    ],
)
def test_g2b_fail_on_any_mismatch(override):
    result = evaluate_gates(GateInputs(independent_reproduction=_reproduction_result(**override)))[3]
    assert result.verdict is GateVerdict.FAIL


def test_g2b_inconclusive_when_checks_pending():
    result = evaluate_gates(
        GateInputs(
            independent_reproduction=_reproduction_result(trade_count_match=None)
        )
    )[3]
    assert result.verdict is GateVerdict.INCONCLUSIVE


def test_promotion_requires_both_g2a_and_g2b_pass():
    g2a_pass = evaluate_gates(GateInputs(artifact_integrity=_integrity_result()))[2]
    g2b_pending = evaluate_gates(
        GateInputs(independent_reproduction=_reproduction_result(performed=False))
    )[3]
    g2b_pass = evaluate_gates(GateInputs(independent_reproduction=_reproduction_result()))[3]
    g2a_fail = evaluate_gates(GateInputs(artifact_integrity=_integrity_result(hashes_match=False)))[2]

    assert g2_promotion_pass(g2a_pass, g2b_pass) is True
    assert g2_promotion_pass(g2a_pass, g2b_pending) is False
    assert g2_promotion_pass(g2a_fail, g2b_pass) is False


# ------------------------------- G3 ---------------------------------------- #
def test_g3_pass_healthy_strategy():
    result = evaluate_gates(GateInputs(stage_a=_passing_stage_a()))[4]
    assert result.verdict is GateVerdict.PASS and result.reasons == ()


def test_g3_fail_negative_expectancy_and_weak_pf():
    stage = StageAInput(exp_after_cost=-0.1, pf_after_cost=1.05, total_trades=40)
    result = evaluate_gates(GateInputs(stage_a=stage))[4]
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
    result = evaluate_gates(GateInputs(stage_a=stage))[4]
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
    result = evaluate_gates(GateInputs(stage_a=stage))[4]
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
    result = evaluate_gates(GateInputs(stage_a=stage))[4]
    assert result.verdict is GateVerdict.FAIL
    assert "symbol_masked_by_average" in result.reasons


def test_g3_trades_below_min_is_inconclusive_per_plan_v2():
    stage = StageAInput(exp_after_cost=0.4, pf_after_cost=1.3, total_trades=19)
    result = evaluate_gates(GateInputs(stage_a=stage))[4]
    assert result.verdict is GateVerdict.INCONCLUSIVE
    assert result.reasons == ("trades_below_min",)


def test_g3_missing_aggregates_is_not_yet_tested():
    stage = StageAInput(exp_after_cost=None, pf_after_cost=None)
    result = evaluate_gates(GateInputs(stage_a=stage))[4]
    assert result.verdict is GateVerdict.NOT_YET_TESTED
    assert "metric_not_computed" in result.reasons


# ------------------------------- G4/G5 -------------------------------------- #
def test_g4_absent_inputs_not_implemented():
    result = evaluate_gates(GateInputs())[5]
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
    result = evaluate_gates(GateInputs(survivor=survivor))[5]
    assert result.verdict is GateVerdict.PASS and result.reasons == ()


def test_g4_fail_fee_flip_and_spike():
    survivor = SurvivorInput(
        fee_stress_positive=False,
        neighborhood_spike_detected=True,
        dropone_signflip_detected=False,
    )
    result = evaluate_gates(GateInputs(survivor=survivor))[5]
    assert result.verdict is GateVerdict.FAIL
    assert {"fee_stress_negative", "neighborhood_spike"}.issubset(result.reasons)


def test_g5_absent_inputs_na():
    assert evaluate_gates(GateInputs())[6].verdict is GateVerdict.NOT_APPLICABLE


def test_g5_pass():
    portfolio = PortfolioInput(portfolio_pnl=42.0, portfolio_pf=1.35,
                               max_symbol_contribution_pct=0.31)
    result = evaluate_gates(GateInputs(portfolio=portfolio))[6]
    assert result.verdict is GateVerdict.PASS


def test_g5_fail_every_portfolio_rule():
    portfolio = PortfolioInput(
        portfolio_pnl=-1.0,
        portfolio_pf=1.05,
        limits_ok=False,
        max_symbol_contribution_pct=55.0,
    )
    result = evaluate_gates(GateInputs(portfolio=portfolio))[6]
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
        ({"stage_a": {"exp_after_cost": 0.2, "pf_after_cost": 1.2}}, 4),
    ],
)
def test_partial_sections_leave_other_gates_na(section_payload, index):
    results = evaluate_gates(section_payload)
    assert results[index].verdict is not GateVerdict.NOT_APPLICABLE
    for i, result in enumerate(results):
        if i in (index, 5):
            continue  # G4 defaults to NOT_IMPLEMENTED
        assert result.verdict is GateVerdict.NOT_APPLICABLE
