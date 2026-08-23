"""Sprint V3 real-band scorecard tests (PLAN section 10.1).

Every band edge is exercised AT the boundary value; missing metrics must
score 0 with a machine-readable reason; eligibility rules (section 10.2)
are fail-closed.
"""

from __future__ import annotations

import pytest

from contracts.protocol import GateId, GateResult, GateVerdict
from research.protocol.gates import ProtocolGateId
from research.protocol.scorecard import (
    compute_scorecard_v3,
    score_closed_trades_band,
    score_eligibility,
    score_expectancy_r_band,
    score_flat_benchmark_band,
    score_position_pf_band,
    score_positive_folds_band,
)


# --------------------- band edges AT boundaries ------------------------------ #
@pytest.mark.parametrize(
    ("value", "points"),
    [
        (-0.5, 0),
        (0.0, 0),          # <= 0 -> 0
        (0.0001, 2),       # just above zero
        (0.0299, 2),
        (0.03, 4),         # [.03, .05) edge
        (0.0499, 4),
        (0.05, 6),         # [.05, .10) edge
        (0.0999, 6),
        (0.10, 8),         # >= .10 edge
        (1.0, 8),
        (None, 0),
    ],
)
def test_expectancy_r_band_edges(value, points):
    assert score_expectancy_r_band(value) == points


@pytest.mark.parametrize(
    ("value", "points"),
    [
        (None, 0),
        (1.09, 0),
        (1.10, 2),   # >= 1.10 edge
        (1.14, 2),
        (1.15, 4),   # [1.15, 1.25) edge
        (1.24, 4),
        (1.25, 6),   # [1.25, 1.50) edge
        (1.49, 6),
        (1.50, 7),   # >= 1.50 edge
        (3.00, 7),
    ],
)
def test_position_pf_band_edges(value, points):
    assert score_position_pf_band(value) == points


@pytest.mark.parametrize(
    ("positive", "total", "points"),
    [(0, 3, 0), (1, 3, 0), (2, 3, 3), (3, 3, 5)],
)
def test_positive_folds_band_edges(positive, total, points):
    assert score_positive_folds_band(positive, total) == points


@pytest.mark.parametrize(
    ("trades", "points"),
    [
        (0, 0),
        (19, 0),
        (20, 1),   # >= 20 edge
        (49, 1),
        (50, 2),   # >= 50 edge
        (99, 2),
        (100, 3),  # >= 100 edge
    ],
)
def test_closed_trades_band_edges(trades, points):
    assert score_closed_trades_band(trades) == points


def test_flat_benchmark_band():
    assert score_flat_benchmark_band(True) == 2
    assert score_flat_benchmark_band(False) == 0
    assert score_flat_benchmark_band(None) == 0


def test_edge_component_max_is_25():
    total = (
        score_expectancy_r_band(0.20)
        + score_position_pf_band(1.60)
        + score_positive_folds_band(3, 3)
        + score_closed_trades_band(150)
        + score_flat_benchmark_band(True)
    )
    assert total == 25


# --------------------------- full scorecard ---------------------------------- #
def _gates(**overrides):
    verdicts = {
        "G0": GateVerdict.PASS,
        "G1": GateVerdict.PASS,
        "G2A": GateVerdict.PASS,
        "G2B": GateVerdict.NOT_YET_TESTED,
        "G3": GateVerdict.PASS,
        "G4": GateVerdict.NOT_IMPLEMENTED,
        "G5": GateVerdict.PASS,
    }
    verdicts.update(overrides)
    return [
        GateResult(GateId.G0_DATA, verdicts["G0"]),
        GateResult(GateId.G1_LEAKAGE, verdicts["G1"]),
        GateResult(ProtocolGateId.G2A_ARTIFACT_INTEGRITY, verdicts["G2A"]),
        GateResult(ProtocolGateId.G2B_INDEPENDENT_REPRODUCIBILITY, verdicts["G2B"]),
        GateResult(GateId.G3_STAGE_A, verdicts["G3"]),
        GateResult(GateId.G4_SURVIVOR_ROBUSTNESS, verdicts["G4"]),
        GateResult(GateId.G5_PORTFOLIO, verdicts["G5"]),
    ]


_FULL_EVIDENCE = {
    "expectancy_r": 0.20,
    "position_pf": 1.60,
    "positive_folds": 3,
    "outer_folds": 3,
    "closed_trades": 150,
    "flat_benchmark_pass": True,
    "rationale_flags": {
        "economic_mechanism_specific": True,
        "expected_counterparty_named": True,
        "invalidating_evidence_pre_registered": True,
        "entry_exit_rules_concrete": True,
    },
    "cost_flags": {
        "fee_stress_evidence": True,
        "slippage_stress_evidence": True,
        "delay_stress_evidence": True,
        "funding_audit_evidence": True,
    },
    "risk_flags": {
        "max_drawdown_present": True,
        "dd_duration_present": True,
        "r_normalization_present": True,
    },
}


def test_full_real_evidence_scores_maximum():
    result = compute_scorecard_v3(_gates(), _FULL_EVIDENCE)
    assert result.components["chronological_edge_quality"] == 25
    assert result.components["economic_rationale_simplicity"] == 10
    assert result.components["cost_execution_realism"] == 10
    assert result.components["risk_quality"] == 10
    assert result.components["data_leakage_integrity"] == 15
    assert result.components["reproducibility_auditability"] == 5  # G2b pending
    # G4 NOT_IMPLEMENTED -> robustness 0; G2b pending -> only G2a's 5 points.
    assert result.total == 80
    # Every sub-max component carries a reason.
    assert "rerun_not_performed" in result.reasons["reproducibility_auditability"]


def test_missing_metrics_score_zero_with_reasons():
    result = compute_scorecard_v3(_gates(), None)
    assert result.total < 40
    assert result.reasons["chronological_edge_quality"] == "metric_not_computed"
    assert result.reasons["economic_rationale_simplicity"] == "metric_not_computed"
    assert result.reasons["cost_execution_realism"] == "metric_not_computed"
    assert result.reasons["risk_quality"] == "metric_missing_drawdown"


def test_g1_inconclusive_scores_partial_integrity_not_zero():
    gates = _gates(G1=GateVerdict.INCONCLUSIVE, G3=GateVerdict.FAIL)
    result = compute_scorecard_v3(gates, {"expectancy_r": None})
    assert result.components["data_leakage_integrity"] == 7 + 3


def test_g2b_fail_blocks_reproducibility_points():
    result = compute_scorecard_v3(
        _gates(G2B=GateVerdict.FAIL), {"closed_trades": 100}
    )
    assert result.components["reproducibility_auditability"] == 5  # G2a only


# --------------------------- eligibility -------------------------------------- #
def test_eligibility_protocol_fail_on_g0_g1_g2a_failures():
    for gate, gate_id in (
        ("G0", GateId.G0_DATA),
        ("G1", GateId.G1_LEAKAGE),
        ("G2A", ProtocolGateId.G2A_ARTIFACT_INTEGRITY),
    ):
        results = _gates(**{gate: GateVerdict.FAIL})
        payload = score_eligibility(results)
        assert payload["eligibility"] == "UNRANKED_PROTOCOL_FAIL"


def test_eligibility_diagnostic_only_when_g2b_not_run():
    payload = score_eligibility(_gates())
    assert payload["eligibility"] == "DIAGNOSTIC_ONLY"
    assert "g2b_independent_reproduction_not_run" in payload["reasons"]


def test_eligibility_no_leaderboard_when_g3_fails():
    results = _gates(G2B=GateVerdict.PASS, G3=GateVerdict.FAIL)
    assert score_eligibility(results)["eligibility"] == "NO_LEADERBOARD"


def test_eligibility_rankable_requires_everything_pass():
    results = _gates(G2B=GateVerdict.PASS, G4=GateVerdict.PASS)
    assert score_eligibility(results)["eligibility"] == "RANKABLE"
