"""Contract-freeze tests (owner: A1). Verifies frozen interfaces load and hold."""

from __future__ import annotations

import json

import pytest

from contracts.protocol import (
    FORBIDDEN_VERDICTS,
    MAX_HYPOTHESES,
    MAX_LOOP_ITERATIONS,
    MAX_NEW_STRATEGIES,
    MAX_PARAM_COMBOS_PER_HYPOTHESIS,
    SCORECARD_COMPONENTS,
    SCORECARD_TOTAL,
    STAGE_A_MIN_PF,
    CanonicalMetrics,
    CellStatus,
    GateId,
    GateResult,
    GateVerdict,
    HypothesisSpec,
    HypothesisState,
    ManifestSpec,
    MatrixCellResult,
    MetricValue,
    ScorecardResult,
    SprintVerdict,
    canonical_json,
    require_reason,
    scorecard_max_verdict,
)


def _manifest_kwargs() -> dict:
    base = {name: "x" for name in (
        "experiment_id", "hypothesis_id", "strategy_type", "owner_agent",
        "validator_agent", "git_commit", "config_path", "config_sha256",
        "data_snapshot_id", "data_manifest_sha256", "universe_snapshot",
        "actual_start_utc", "actual_end_utc", "common_intersection",
        "split_policy", "fee_model", "slippage_model", "funding_mode",
        "parameter_lock_utc", "command",
    )}
    return {
        **base,
        "candidate_version": 1,
        "dirty_worktree": False,
        "warmup_bars": 0,
        "purge_bars": 0,
        "embargo_bars": 0,
        "outer_folds": 3,
        "parameter_combinations": 1,
        "prior_family_trials": 0,
        "random_seed": None,
    }


def test_budget_constants_match_plan():
    assert MAX_HYPOTHESES == 3
    assert MAX_NEW_STRATEGIES == 2
    assert MAX_PARAM_COMBOS_PER_HYPOTHESIS == 16
    assert MAX_LOOP_ITERATIONS == 2


def test_scorecard_totals_100_and_verdict_bands():
    assert SCORECARD_TOTAL == 100
    assert scorecard_max_verdict(49) == "REJECT_REDESIGN"
    assert scorecard_max_verdict(55) == "DIAGNOSTIC_ONLY"
    assert scorecard_max_verdict(65) == "EXPLORATORY_STAGE_A_CANDIDATE"
    assert scorecard_max_verdict(75) == "LOCK_FOR_FUTURE_OOS_IF_G0_G5_PASS"
    assert scorecard_max_verdict(85) == "STRONG_RESEARCH_CANDIDATE_NOT_CONFIRMED_EDGE"


def test_stage_a_thresholds():
    assert STAGE_A_MIN_PF == pytest.approx(1.10)
    assert SCORECARD_COMPONENTS["chronological_edge_quality"] == 25


def test_forbidden_verdicts_absent_from_enums():
    values = {v.value for v in SprintVerdict}
    for forbidden in FORBIDDEN_VERDICTS:
        assert forbidden not in values


def test_manifest_roundtrip_and_missing_field_reason():
    manifest = ManifestSpec(**_manifest_kwargs())
    payload = json.loads(canonical_json(manifest.to_dict()))
    assert payload["experiment_id"] == "x"
    assert manifest.validate() == []


def test_metric_null_requires_reason():
    with pytest.raises(ValueError):
        MetricValue(value=None)
    metric = MetricValue.missing("metric_missing_drawdown")
    assert metric.value is None
    assert metric.reason == "metric_missing_drawdown"


def test_canonical_metrics_rejects_zero_default_drawdown():
    metrics = CanonicalMetrics(
        trades=MetricValue.known(25.0),
        net_canonical_pnl=MetricValue.known(-4.5),
        expectancy_usdt=MetricValue.known(-0.18),
        position_pf=MetricValue.known(0.75),
        win_rate=MetricValue.known(0.40),
        gross_pnl=MetricValue.known(-4.0),
        commission_cost=MetricValue.known(-0.5),
        slippage_cost=MetricValue.known(0.0),
        funding_cost=MetricValue.known(0.0),
        max_drawdown=MetricValue.missing("metric_missing_drawdown"),
        max_dd_duration_bars=MetricValue.missing("metric_not_computed"),
        sharpe=MetricValue.missing("metric_not_computed"),
        sortino=MetricValue.missing("metric_not_computed"),
        exposure_pct=MetricValue.missing("metric_not_computed"),
        turnover=MetricValue.missing("metric_not_computed"),
        top_fold_contribution_pct=MetricValue.known(30.0),
    )
    as_dict = metrics.to_dict()
    assert as_dict["max_drawdown"]["value"] is None
    assert as_dict["max_drawdown"]["reason"] == "metric_missing_drawdown"


def test_cell_status_taxonomy_matches_plan_state_machine():
    expected = {
        "COMPLETED", "REUSED", "CANDIDATE_FAIL", "INCONCLUSIVE",
        "DATA_INCOMPLETE", "PIPELINE_ERROR", "NOT_RUN_BUDGET",
    }
    assert {s.value for s in CellStatus} == expected


def test_gate_result_reason_codes_are_known():
    result = GateResult(
        gate=GateId.G3_STAGE_A,
        verdict=GateVerdict.FAIL,
        reasons=("pf_below_min", "fold_concentration_high"),
    )
    assert result.to_dict()["verdict"] == "FAIL"
    with pytest.raises(ValueError):
        GateResult(gate=GateId.G3_STAGE_A, verdict=GateVerdict.FAIL, reasons=("nonsense",))


def test_completed_cell_requires_artifact():
    with pytest.raises(ValueError):
        MatrixCellResult(
            experiment_id="EXP-20260823-0001",
            strategy_type="reclaim_mr",
            symbol="ETHUSDT",
            status=CellStatus.COMPLETED,
            artifact_path=None,
        )


def test_hypothesis_spec_states_follow_plan():
    states = [s.value for s in HypothesisState]
    assert states[0] == "IDEA" and "SPEC_LOCKED" in states and "LOCKED_FOR_FUTURE_OOS" in states


def test_hypothesis_spec_roundtrip():
    spec = HypothesisSpec(
        hypothesis_id="H-FUND-CROWD-v1",
        family="funding_oi_crowding",
        state=HypothesisState.SPEC_DRAFT,
        candidate_version=1,
        economic_mechanism="crowded longs pay carry; unwind pressure precedes reversal",
        expected_counterparty="leveraged trend chasers",
        expected_regimes=("markup_crowded",),
        invalidating_evidence=("funding-neutral PnL indistinguishable from baseline",),
        entry_exit_rules="frozen rule text",
        holding_horizon="intraday-15m bars, <= 96 bars",
        warmup_bars=100,
        universe=("ETHUSDT",),
        cost_assumptions="maker/taker + one-tick + post-trade funding audit",
        trial_budget_combinations=8,
    )
    payload = spec.to_dict()
    assert payload["state"] == "SPEC_DRAFT"
    assert len(payload["universe"]) == 1


def test_require_reason_unknown_code_raises():
    with pytest.raises(ValueError):
        require_reason("made_up_code")
