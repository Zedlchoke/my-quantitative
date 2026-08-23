"""Scorecard (100 points) assembled from gate results + evidence flags.

Weights come from ``contracts.protocol.SCORECARD_COMPONENTS``.  Missing or
failed evidence earns 0 for its component and a reason string is recorded.
Partial fractions (0..1) are supported only where explicitly documented so
band-edge behaviour stays deterministic:

* ``data_leakage_integrity``: mean of G0/G1 PASS states x 15
* ``chronological_edge_quality``: G3 PASS=25, NOT_YET_TESTED=12, else 0
* ``time_symbol_param_robustness``: G4 PASS=15 else 0
* ``portfolio_diversification``: G5 PASS=5 else 0
* ``reproducibility_auditability``: G2 PASS=10, NOT_YET_TESTED=5, else 0
* ``cost_execution_realism``: round(10 * flags['cost_execution'])
* ``risk_quality``: round(10 * flags['risk_quality'])
* ``economic_rationale_simplicity``: 10 iff
  ``hypothesis_quality_flags['economic_rationale_documented']``
"""

from __future__ import annotations

import math
from typing import Iterable

from contracts.protocol import (
    SCORECARD_COMPONENTS,
    GateId,
    GateResult,
    GateVerdict,
    ScorecardResult,
)


def _round(value: float) -> int:
    return int(math.floor(value + 0.5))


def _verdict_map(
    gate_results: Iterable[GateResult],
) -> dict[GateId, GateVerdict]:
    return {result.gate: result.verdict for result in gate_results}


def compute_scorecard(
    gate_results: Iterable[GateResult],
    metrics_present_flags: dict | None = None,
    hypothesis_quality_flags: dict | None = None,
) -> ScorecardResult:
    """Build a :class:`ScorecardResult`; missing evidence scores 0 + reason."""
    metrics_present_flags = metrics_present_flags or {}
    hypothesis_quality_flags = hypothesis_quality_flags or {}
    verdicts = _verdict_map(gate_results)
    components: dict[str, int] = {}
    reasons: dict[str, str] = {}

    def _fraction(name: str, default: float = 0.0) -> float:
        value = metrics_present_flags.get(name, default)
        if isinstance(value, bool):
            value = 1.0 if value else 0.0
        return max(0.0, min(1.0, float(value)))

    # Economic rationale & simplicity ------------------------------------- #
    if hypothesis_quality_flags.get("economic_rationale_documented"):
        components["economic_rationale_simplicity"] = SCORECARD_COMPONENTS[
            "economic_rationale_simplicity"
        ]
    else:
        components["economic_rationale_simplicity"] = 0
        reasons["economic_rationale_simplicity"] = "metric_not_computed"

    # Data / leakage integrity (G0 + G1) ----------------------------------- #
    integrity_gates = (GateId.G0_DATA, GateId.G1_LEAKAGE)
    passed = sum(
        1 for gate in integrity_gates if verdicts.get(gate) is GateVerdict.PASS
    )
    components["data_leakage_integrity"] = _round(
        SCORECARD_COMPONENTS["data_leakage_integrity"] * passed / len(integrity_gates)
    )
    for gate in integrity_gates:
        if verdicts.get(gate) != GateVerdict.PASS:
            reasons[f"gate_{gate.value}"] = str(
                verdicts.get(gate, GateVerdict.NOT_APPLICABLE).value
            )

    # Chronological edge quality (G3) --------------------------------------- #
    g3 = verdicts.get(GateId.G3_STAGE_A)
    if g3 is GateVerdict.PASS:
        components["chronological_edge_quality"] = SCORECARD_COMPONENTS[
            "chronological_edge_quality"
        ]
    elif g3 is GateVerdict.NOT_YET_TESTED:
        components["chronological_edge_quality"] = _round(
            SCORECARD_COMPONENTS["chronological_edge_quality"] * 0.5
        )
        reasons["chronological_edge_quality"] = "trades_below_min"
    else:
        components["chronological_edge_quality"] = 0
        reasons.setdefault(
            "chronological_edge_quality",
            str(g3.value) if g3 is not None else GateVerdict.NOT_APPLICABLE.value,
        )

    # Time/symbol/parameter robustness (G4) --------------------------------- #
    if verdicts.get(GateId.G4_SURVIVOR_ROBUSTNESS) is GateVerdict.PASS:
        components["time_symbol_param_robustness"] = SCORECARD_COMPONENTS[
            "time_symbol_param_robustness"
        ]
    else:
        components["time_symbol_param_robustness"] = 0
        reasons["time_symbol_param_robustness"] = str(
            verdicts.get(
                GateId.G4_SURVIVOR_ROBUSTNESS, GateVerdict.NOT_IMPLEMENTED
            ).value
        )

    # Cost / execution realism ---------------------------------------------- #
    cost_fraction = _fraction("cost_execution")
    components["cost_execution_realism"] = _round(
        SCORECARD_COMPONENTS["cost_execution_realism"] * cost_fraction
    )
    if cost_fraction < 1.0:
        reasons["cost_execution_realism"] = (
            "metric_not_computed" if cost_fraction == 0.0 else "partial_cost_evidence"
        )

    # Risk quality ----------------------------------------------------------- #
    risk_fraction = _fraction("risk_quality")
    components["risk_quality"] = _round(
        SCORECARD_COMPONENTS["risk_quality"] * risk_fraction
    )
    if risk_fraction < 1.0:
        reasons["risk_quality"] = (
            "metric_missing_drawdown" if risk_fraction == 0.0 else "partial_risk_evidence"
        )

    # Portfolio / diversification (G5) ---------------------------------------- #
    if verdicts.get(GateId.G5_PORTFOLIO) is GateVerdict.PASS:
        components["portfolio_diversification"] = SCORECARD_COMPONENTS[
            "portfolio_diversification"
        ]
    else:
        components["portfolio_diversification"] = 0
        reasons["portfolio_diversification"] = str(
            verdicts.get(GateId.G5_PORTFOLIO, GateVerdict.NOT_APPLICABLE).value
        )

    # Reproducibility / auditability (G2) -------------------------------------- #
    g2 = verdicts.get(GateId.G2_REPRODUCIBILITY)
    if g2 is GateVerdict.PASS:
        components["reproducibility_auditability"] = SCORECARD_COMPONENTS[
            "reproducibility_auditability"
        ]
    elif g2 is GateVerdict.NOT_YET_TESTED:
        components["reproducibility_auditability"] = _round(
            SCORECARD_COMPONENTS["reproducibility_auditability"] * 0.5
        )
        reasons["reproducibility_auditability"] = "rerun_not_performed"
    else:
        components["reproducibility_auditability"] = 0
        reasons.setdefault(
            "reproducibility_auditability",
            str(g2.value) if g2 is not None else GateVerdict.NOT_APPLICABLE.value,
        )

    # Guarantee the contract invariant: any component below its maximum
    # carries an explicit machine-readable reason.
    for name, max_points in SCORECARD_COMPONENTS.items():
        if components[name] < max_points:
            reasons.setdefault(name, "metric_not_computed")

    total = sum(components.values())
    return ScorecardResult(components=components, total=total, reasons=reasons)
