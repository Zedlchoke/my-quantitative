"""Golden tests for the incremental mechanism alpha and falsification contract.

All strategy returns here are DECLARED SYNTHETIC inputs (this module never
computes a real strategy return); benchmark side uses the hand-computed
fixtures from the benchmark golden suite.
"""

from __future__ import annotations

import pytest

from research.stocks_free_v3.benchmarks import (
    BENCHMARK_FLAT_HARD,
    BENCHMARK_RISK_MATCHED_SPY,
    VolScalingRule,
    build_flat_benchmark,
    build_risk_matched_spy,
    build_spy_total_return,
)
from research.stocks_free_v3.incremental import (
    BETA_ISOLATION_NONE,
    BETA_ISOLATION_RISK_MATCHED,
    CONTRACT_SCHEMA,
    FALSIFICATION_NOTE,
    FoldAlphaRecord,
    FoldAlphaReport,
    IncrementalAlphaError,
    compute_fold_alpha,
)

SESSIONS = ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
RAW = {
    "2024-01-02": 100.0,
    "2024-01-03": 110.0,
    "2024-01-04": 50.0,
    "2024-01-05": 55.0,
}
DIST = {"2024-01-04": 1.0}
SPLIT = {"2024-01-04": 2.0}
RULE = VolScalingRule(lookback_sessions=2, target_daily_vol=0.02, min_gross=0.5, max_gross=2.0)


def test_fold_alpha_hand_computed() -> None:
    """Hand math from the SPY golden (levels 1.0, 1.1, 1.01, 1.111) scaled
    ex ante by 0.5 on every session under this rule and compounded:
    1.05 * (1 - 9/220) * 1.05 - 1.  Strategy declared at +20% after cost."""
    benchmark = build_risk_matched_spy(
        RAW, DIST, SPLIT, SESSIONS, SESSIONS[0], SESSIONS[-1], RULE
    )
    r2, r3, r4 = 0.1, 101.0 / 110.0 - 1.0, 0.1
    assert benchmark.scalings == (None, 0.5, 0.5, 0.5)
    assert benchmark.returns[1:] == pytest.approx([0.5 * r2, 0.5 * r3, 0.5 * r4])
    expected_total = (1 + 0.5 * r2) * (1 + 0.5 * r3) * (1 + 0.5 * r4) - 1
    assert benchmark.total_return == pytest.approx(expected_total)
    record = compute_fold_alpha(
        family_id="FAM_X",
        arm_id="ARM_1",
        fold_id="F1",
        strategy_return_after_cost=0.20,
        strategy_metric_digest="a" * 64,
        benchmark=benchmark,
    )
    assert record.incremental_alpha == pytest.approx(0.20 - expected_total)
    assert record.beta_isolation == BETA_ISOLATION_RISK_MATCHED
    assert record.eligible_for_pass is True
    assert record.ex_ante_rule_digest == RULE.digest
    assert record.window_start == SESSIONS[0]
    assert record.window_end == SESSIONS[-1]


def test_falsification_beta_only_arm_cannot_pass() -> None:
    """An arm whose after-cost return merely equals its risk-matched beta
    context yields alpha ~ 0 — NOT pass-eligible."""
    benchmark = build_risk_matched_spy(
        RAW, DIST, SPLIT, SESSIONS, SESSIONS[0], SESSIONS[-1], RULE
    )
    record = compute_fold_alpha(
        family_id="FAM_X",
        arm_id="BETA_ONLY",
        fold_id="F1",
        strategy_return_after_cost=benchmark.total_return,  # beta, nothing else
        strategy_metric_digest="b" * 64,
        benchmark=benchmark,
    )
    assert record.incremental_alpha == pytest.approx(0.0)
    assert record.eligible_for_pass is False


def test_flat_and_spy_benchmarks_are_never_pass_eligible() -> None:
    flat = build_flat_benchmark(SESSIONS, SESSIONS[0], SESSIONS[-1])
    record = compute_fold_alpha(
        family_id="FAM_X",
        arm_id="ARM_1",
        fold_id="F1",
        strategy_return_after_cost=0.05,
        strategy_metric_digest="c" * 64,
        benchmark=flat,
        require_beta_isolation=False,
    )
    assert record.beta_isolation == BETA_ISOLATION_NONE
    assert record.eligible_for_pass is False
    assert record.ex_ante_rule_digest is None

    spy = build_spy_total_return(RAW, DIST, SPLIT, SESSIONS, SESSIONS[0], SESSIONS[-1])
    with pytest.raises(IncrementalAlphaError, match="risk-matched"):
        compute_fold_alpha(
            family_id="FAM_X",
            arm_id="ARM_1",
            fold_id="F2",
            strategy_return_after_cost=0.05,
            strategy_metric_digest="c" * 64,
            benchmark=spy,
        )


def test_falsification_contract_fields_complete() -> None:
    benchmark = build_risk_matched_spy(
        RAW, DIST, SPLIT, SESSIONS, SESSIONS[0], SESSIONS[-1], RULE
    )
    record = compute_fold_alpha(
        family_id="FAM_X",
        arm_id="ARM_1",
        fold_id="F1",
        strategy_return_after_cost=0.20,
        strategy_metric_digest="a" * 64,
        benchmark=benchmark,
    )
    payload = record.to_payload()
    required = {
        "schema",
        "family_id",
        "arm_id",
        "fold_id",
        "window",
        "strategy_return_after_cost",
        "strategy_metric_digest",
        "benchmark_id",
        "benchmark_definition_digest",
        "benchmark_series_digest",
        "benchmark_return",
        "incremental_alpha",
        "beta_isolation",
        "ex_ante_rule_digest",
        "eligible_for_pass",
        "falsification_note",
    }
    assert required <= set(payload)
    assert payload["schema"] == CONTRACT_SCHEMA
    assert payload["benchmark_id"] == BENCHMARK_RISK_MATCHED_SPY
    assert payload["falsification_note"] == FALSIFICATION_NOTE
    assert len(record.digest) == 64
    # digest is replay-stable
    assert record.digest == compute_fold_alpha(
        family_id="FAM_X",
        arm_id="ARM_1",
        fold_id="F1",
        strategy_return_after_cost=0.20,
        strategy_metric_digest="a" * 64,
        benchmark=build_risk_matched_spy(
            RAW, DIST, SPLIT, SESSIONS, SESSIONS[0], SESSIONS[-1], RULE
        ),
    ).digest


def test_alpha_identity_is_enforced() -> None:
    with pytest.raises(IncrementalAlphaError, match="incremental_alpha"):
        FoldAlphaRecord(
            family_id="FAM_X",
            arm_id="ARM_1",
            fold_id="F1",
            window_start=SESSIONS[0],
            window_end=SESSIONS[-1],
            strategy_return_after_cost=0.20,
            strategy_metric_digest="a" * 64,
            benchmark_id=BENCHMARK_RISK_MATCHED_SPY,
            benchmark_definition_digest="0" * 64,
            benchmark_series_digest="1" * 64,
            benchmark_return=0.05,
            incremental_alpha=0.99,  # != 0.20 - 0.05
            beta_isolation=BETA_ISOLATION_RISK_MATCHED,
            ex_ante_rule_digest="2" * 64,
        )


def test_report_aggregates_and_pass_eligibility() -> None:
    benchmark = build_risk_matched_spy(
        RAW, DIST, SPLIT, SESSIONS, SESSIONS[0], SESSIONS[-1], RULE
    )
    beta_only = compute_fold_alpha(
        family_id="FAM_X",
        arm_id="ARM_1",
        fold_id="F1",
        strategy_return_after_cost=benchmark.total_return,
        strategy_metric_digest="b" * 64,
        benchmark=benchmark,
    )
    positive = compute_fold_alpha(
        family_id="FAM_X",
        arm_id="ARM_1",
        fold_id="F2",
        strategy_return_after_cost=benchmark.total_return + 0.01,
        strategy_metric_digest="b" * 64,
        benchmark=benchmark,
    )
    report = FoldAlphaReport(family_id="FAM_X", arm_id="ARM_1", records=(beta_only, positive))
    assert report.pass_eligible_folds == ("F2",)
    assert report.mean_incremental_alpha == pytest.approx((0.0 + 0.01) / 2)
    assert len(report.digest) == 64
    with pytest.raises(IncrementalAlphaError):
        FoldAlphaReport(family_id="FAM_X", arm_id="ARM_1", records=())
    with pytest.raises(IncrementalAlphaError, match="same family"):
        FoldAlphaReport(
            family_id="FAM_X",
            arm_id="OTHER",
            records=(beta_only,),
        )


def test_window_fields_come_from_the_benchmark() -> None:
    benchmark = build_risk_matched_spy(
        RAW, DIST, SPLIT, SESSIONS, SESSIONS[0], SESSIONS[-1], RULE
    )
    record = compute_fold_alpha(
        family_id="FAM_X",
        arm_id="ARM_1",
        fold_id="F1",
        strategy_return_after_cost=0.0,
        strategy_metric_digest="d" * 64,
        benchmark=benchmark,
    )
    assert (record.window_start, record.window_end) == (SESSIONS[0], SESSIONS[-1])
