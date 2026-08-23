"""A3 scorecard tests incl. verdict band edges 49/50, 59/60, 69/70, 79/80."""

from __future__ import annotations

import pytest

from contracts.protocol import (
    GateId,
    GateResult,
    GateVerdict,
    ScorecardResult,
    scorecard_max_verdict,
)
from research.protocol.gates import ProtocolGateId
from research.protocol.scorecard import compute_scorecard


def _gate(gate, verdict: GateVerdict) -> GateResult:
    return GateResult(gate=gate, verdict=verdict)


def _all_pass() -> list[GateResult]:
    return [
        _gate(GateId.G0_DATA, GateVerdict.PASS),
        _gate(GateId.G1_LEAKAGE, GateVerdict.PASS),
        _gate(ProtocolGateId.G2A_ARTIFACT_INTEGRITY, GateVerdict.PASS),
        _gate(ProtocolGateId.G2B_INDEPENDENT_REPRODUCIBILITY, GateVerdict.PASS),
        _gate(GateId.G3_STAGE_A, GateVerdict.PASS),
        _gate(GateId.G4_SURVIVOR_ROBUSTNESS, GateVerdict.PASS),
        _gate(GateId.G5_PORTFOLIO, GateVerdict.PASS),
    ]


def test_full_evidence_scores_maximum():
    result = compute_scorecard(
        _all_pass(),
        {"cost_execution": 1.0, "risk_quality": True},
        {"economic_rationale_documented": True},
    )
    assert isinstance(result, ScorecardResult)
    assert result.total == 100
    assert result.reasons == {}
    assert result.max_verdict() == "STRONG_RESEARCH_CANDIDATE_NOT_CONFIRMED_EDGE"


def test_missing_evidence_scores_zero_with_reasons():
    result = compute_scorecard([], None, None)
    assert result.total == 0
    assert set(result.components) == set(
        [
            "economic_rationale_simplicity",
            "data_leakage_integrity",
            "chronological_edge_quality",
            "time_symbol_param_robustness",
            "cost_execution_realism",
            "risk_quality",
            "portfolio_diversification",
            "reproducibility_auditability",
        ]
    )
    assert all(points == 0 for points in result.components.values())
    for name in result.components:
        assert name in result.reasons


def test_gate_failures_zero_their_components():
    gates = [
        _gate(GateId.G0_DATA, GateVerdict.FAIL),
        _gate(GateId.G1_LEAKAGE, GateVerdict.PASS),
        _gate(ProtocolGateId.G2A_ARTIFACT_INTEGRITY, GateVerdict.FAIL),
        _gate(ProtocolGateId.G2B_INDEPENDENT_REPRODUCIBILITY, GateVerdict.FAIL),
        _gate(GateId.G3_STAGE_A, GateVerdict.FAIL),
        _gate(GateId.G4_SURVIVOR_ROBUSTNESS, GateVerdict.NOT_IMPLEMENTED),
        _gate(GateId.G5_PORTFOLIO, GateVerdict.NOT_APPLICABLE),
    ]
    result = compute_scorecard(
        gates,
        {"cost_execution": False, "risk_quality": False},
        {"economic_rationale_documented": True},
    )
    # econ 10 + integrity round(15*1/2)=8 + everything else 0
    assert result.components["economic_rationale_simplicity"] == 10
    assert result.components["data_leakage_integrity"] == 8
    assert result.components["chronological_edge_quality"] == 0
    assert result.components["time_symbol_param_robustness"] == 0
    assert result.components["reproducibility_auditability"] == 0
    assert result.total == 18


def test_partial_credit_for_trades_short_and_unrerun():
    gates = [
        _gate(ProtocolGateId.G2A_ARTIFACT_INTEGRITY, GateVerdict.NOT_APPLICABLE),
        _gate(
            ProtocolGateId.G2B_INDEPENDENT_REPRODUCIBILITY,
            GateVerdict.NOT_YET_TESTED,
        ),
        _gate(GateId.G3_STAGE_A, GateVerdict.NOT_YET_TESTED),
    ]
    result = compute_scorecard(gates, None, None)
    assert result.components["chronological_edge_quality"] == 13
    # G2b not run => no independent verification evidence => 0 + reason.
    assert result.components["reproducibility_auditability"] == 0
    assert result.reasons["chronological_edge_quality"] == "trades_below_min"
    assert result.reasons["reproducibility_auditability"] == "rerun_not_performed"


def test_half_credit_when_only_one_g2_row_passes():
    gates = [
        _gate(ProtocolGateId.G2A_ARTIFACT_INTEGRITY, GateVerdict.PASS),
        _gate(ProtocolGateId.G2B_INDEPENDENT_REPRODUCIBILITY, GateVerdict.FAIL),
    ]
    result = compute_scorecard(gates, None, None)
    assert result.components["reproducibility_auditability"] == 5


def _score(
    g2a: GateVerdict = GateVerdict.NOT_APPLICABLE,
    g2b: GateVerdict = GateVerdict.NOT_APPLICABLE,
    *,
    g3: GateVerdict = GateVerdict.NOT_APPLICABLE,
    g5_pass: bool = False,
    g4_pass: bool = False,
    cost: float = 1.0,
    risk: float = 1.0,
    econ: bool = True,
) -> ScorecardResult:
    """Deterministic scaffold: G0+G1 pass by default, others per args."""
    gates = [
        _gate(GateId.G0_DATA, GateVerdict.PASS),
        _gate(GateId.G1_LEAKAGE, GateVerdict.PASS),
        _gate(ProtocolGateId.G2A_ARTIFACT_INTEGRITY, g2a),
        _gate(ProtocolGateId.G2B_INDEPENDENT_REPRODUCIBILITY, g2b),
        _gate(GateId.G3_STAGE_A, g3),
        _gate(
            GateId.G4_SURVIVOR_ROBUSTNESS,
            GateVerdict.PASS if g4_pass else GateVerdict.NOT_IMPLEMENTED,
        ),
        _gate(
            GateId.G5_PORTFOLIO,
            GateVerdict.PASS if g5_pass else GateVerdict.NOT_APPLICABLE,
        ),
    ]
    return compute_scorecard(
        gates,
        {"cost_execution": cost, "risk_quality": risk},
        {"economic_rationale_documented": econ},
    )


FAIL = GateVerdict.FAIL
NYET = GateVerdict.NOT_YET_TESTED
PASS = GateVerdict.PASS


@pytest.mark.parametrize(
    ("kwargs", "expected_total", "expected_band"),
    [
        # 15(G0G1)+13(G3 half)+10(econ)+10(cost)+1(risk .1) = 49
        ({"g2a": FAIL, "g2b": FAIL, "g3": NYET, "risk": 0.1},
         49, "REJECT_REDESIGN"),
        ({"g2a": FAIL, "g2b": FAIL, "g3": NYET, "risk": 0.2},
         50, "DIAGNOSTIC_ONLY"),
        # 15+13(G3 half)+5(G2a pass only)+5(G5)+10(econ)+10(cost)+1(risk .1)=59
        ({"g2a": PASS, "g2b": NYET, "g3": NYET, "g5_pass": True, "risk": 0.1},
         59, "DIAGNOSTIC_ONLY"),
        ({"g2a": PASS, "g2b": NYET, "g3": NYET, "g5_pass": True, "risk": 0.2},
         60, "EXPLORATORY_STAGE_A_CANDIDATE"),
        # 15+25(G3 pass)+10(econ)+9(cost .9) = 69
        ({"g2a": FAIL, "g2b": FAIL, "g3": PASS, "cost": 0.9},
         69, "EXPLORATORY_STAGE_A_CANDIDATE"),
        ({"g2a": FAIL, "g2b": FAIL, "g3": PASS},
         70, "LOCK_FOR_FUTURE_OOS_IF_G0_G5_PASS"),
        # 15+25+5(G2a only)+10(econ)+5(G5)+9(cost .9) = 79
        ({"g2a": PASS, "g2b": NYET, "g3": PASS, "g5_pass": True, "cost": 0.9},
         79, "LOCK_FOR_FUTURE_OOS_IF_G0_G5_PASS"),
        # all gates pass, no econ doc: 15+25+10(g2)+15(g4)+5(cost .5)
        # +5(risk .5)+5(G5) = 80
        ({"g2a": PASS, "g2b": PASS, "g3": PASS, "g4_pass": True,
          "g5_pass": True, "cost": 0.5, "risk": 0.5, "econ": False},
         80, "STRONG_RESEARCH_CANDIDATE_NOT_CONFIRMED_EDGE"),
    ],
)
def test_band_edges_achieved_through_real_inputs(kwargs, expected_total, expected_band):
    result = _score(**kwargs)
    assert result.total == expected_total
    assert result.max_verdict() == expected_band
    assert scorecard_max_verdict(expected_total) == expected_band
