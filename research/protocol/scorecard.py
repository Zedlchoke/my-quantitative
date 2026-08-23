"""Scorecard (100 points) assembled from gate results + REAL metric evidence.

Two public entry points:

* :func:`compute_scorecard` -- Sprint V2 gate-flag scoring (legacy evaluator).
* :func:`compute_scorecard_v3` -- Sprint V3 rewrite per PLAN section 10:
  chronological edge quality is scored from REAL band metrics (expectancy-R,
  position PF, positive folds, closed trades, flat benchmark); rationale /
  cost / risk components are scored from evidence-dict subcomponents, never
  from constant fractions or bare gate booleans.

Weights come from ``contracts.protocol.SCORECARD_COMPONENTS``. Missing or
failed evidence earns 0 for its subcomponent and a machine-readable reason
is recorded.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Mapping

from contracts.protocol import (
    SCORECARD_COMPONENTS,
    GateId,
    GateResult,
    GateVerdict,
    ScorecardResult,
)

# --------------------------------------------------------------------------- #
# Sprint V3 band scorers (PLAN section 10.1) -- pure functions, unit-testable
# at every band edge.
# --------------------------------------------------------------------------- #
def score_expectancy_r_band(value: float | None) -> int:
    """≤0 -> 0 · (0,.03) -> 2 · [.03,.05) -> 4 · [.05,.10) -> 6 · ≥.10 -> 8."""
    if value is None or value <= 0:
        return 0
    if value < 0.03:
        return 2
    if value < 0.05:
        return 4
    if value < 0.10:
        return 6
    return 8


def score_position_pf_band(value: float | None) -> int:
    """<1.10 -> 0 · [1.10,1.15) -> 2 · [1.15,1.25) -> 4 · [1.25,1.50) -> 6 · ≥1.50 -> 7."""
    if value is None or value < 1.10:
        return 0
    if value < 1.15:
        return 2
    if value < 1.25:
        return 4
    if value < 1.50:
        return 6
    return 7


def score_positive_folds_band(
    positive: int | None, outer_folds: int | None = 3
) -> int:
    """<2/3 folds -> 0 · exactly 2/3 -> 3 · 3/3 -> 5."""
    if not positive or not outer_folds:
        return 0
    ratio = positive / outer_folds
    if ratio >= 1.0:
        return 5
    if ratio >= 2.0 / 3.0:
        return 3
    return 0


def score_closed_trades_band(closed_trades: int | None) -> int:
    """<20 -> 0 · 20-49 -> 1 · 50-99 -> 2 · ≥100 -> 3."""
    if closed_trades is None:
        return 0
    if closed_trades < 20:
        return 0
    if closed_trades < 50:
        return 1
    if closed_trades < 100:
        return 2
    return 3


def score_flat_benchmark_band(passed: bool | None) -> int:
    """fail/not-evidenced -> 0 · pass -> 2."""
    return 2 if passed is True else 0


def _flag(points: Mapping[str, int], flags: Mapping[str, Any], key: str) -> int:
    return points[key] if flags.get(key) is True else 0


@dataclass(frozen=True)
class ScorecardEvidence:
    """Real metric/evidence inputs for :func:`compute_scorecard_v3`."""

    expectancy_r: float | None = None
    position_pf: float | None = None
    positive_folds: int | None = None
    outer_folds: int | None = 3
    closed_trades: int | None = None
    flat_benchmark_pass: bool | None = None
    rationale_flags: dict[str, bool] = field(default_factory=dict)
    cost_flags: dict[str, bool] = field(default_factory=dict)
    risk_flags: dict[str, bool] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Mapping) -> "ScorecardEvidence":
        known = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in payload.items() if k in known})


#: Subcomponent point weights (sum == component maximum in each group).
RATIONALE_FLAG_POINTS = {
    "economic_mechanism_specific": 3,
    "expected_counterparty_named": 2,
    "invalidating_evidence_pre_registered": 3,
    "entry_exit_rules_concrete": 2,
}
COST_FLAG_POINTS = {
    "fee_stress_evidence": 3,
    "slippage_stress_evidence": 3,
    "delay_stress_evidence": 2,
    "funding_audit_evidence": 2,
}
RISK_FLAG_POINTS = {
    "max_drawdown_present": 4,
    "dd_duration_present": 3,
    "r_normalization_present": 3,
}


def _verdict_by_id(gate_results: Iterable[GateResult]) -> dict[str, GateVerdict]:
    return {
        (result.gate.value if hasattr(result.gate, "value") else str(result.gate)): result.verdict
        for result in gate_results
    }


def _gate_component_points(
    verdicts: Mapping[str, GateVerdict],
    gate_value: str,
    *,
    full: int,
    inconclusive: int = 0,
) -> int:
    verdict = verdicts.get(gate_value)
    if verdict is GateVerdict.PASS:
        return full
    if verdict in (GateVerdict.INCONCLUSIVE, GateVerdict.NOT_YET_TESTED):
        return inconclusive
    return 0


def compute_scorecard_v3(
    gate_results: Iterable[GateResult],
    evidence: ScorecardEvidence | Mapping | None = None,
) -> ScorecardResult:
    """Sprint V3 scorecard built from real evidence (PLAN section 10).

    Every subcomponent scores 0 unless its specific metric/evidence exists;
    a missing metric yields 0 plus a machine-readable reason.
    """
    ev = (
        evidence
        if isinstance(evidence, ScorecardEvidence)
        else ScorecardEvidence.from_dict(evidence or {})
    )
    verdicts = _verdict_by_id(gate_results)
    components: dict[str, int] = {}
    reasons: dict[str, str] = {}

    # Economic rationale & simplicity (10) ---------------------------------- #
    rationale = sum(_flag(RATIONALE_FLAG_POINTS, ev.rationale_flags, key) for key in RATIONALE_FLAG_POINTS)
    components["economic_rationale_simplicity"] = rationale
    if rationale < SCORECARD_COMPONENTS["economic_rationale_simplicity"]:
        reasons["economic_rationale_simplicity"] = "metric_not_computed"

    # Data / leakage integrity (15): G0 -> 7, G1 -> 8 ------------------------ #
    g0_points = _gate_component_points(verdicts, GateId.G0_DATA.value, full=7, inconclusive=3)
    g1_points = _gate_component_points(verdicts, GateId.G1_LEAKAGE.value, full=8, inconclusive=3)
    components["data_leakage_integrity"] = g0_points + g1_points
    if g0_points < 7:
        reasons["data_leakage_integrity"] = f"g0={verdicts.get(GateId.G0_DATA.value, GateVerdict.NOT_APPLICABLE).value}"
    elif g1_points < 8:
        reasons["data_leakage_integrity"] = f"g1={verdicts.get(GateId.G1_LEAKAGE.value, GateVerdict.NOT_APPLICABLE).value}"

    # Chronological edge quality (25): five real band metrics ---------------- #
    edge_parts = {
        "expectancy_r_band": score_expectancy_r_band(ev.expectancy_r),
        "position_pf_band": score_position_pf_band(ev.position_pf),
        "positive_folds_band": score_positive_folds_band(ev.positive_folds, ev.outer_folds),
        "closed_trades_band": score_closed_trades_band(ev.closed_trades),
        "flat_benchmark_band": score_flat_benchmark_band(ev.flat_benchmark_pass),
    }
    components["chronological_edge_quality"] = sum(edge_parts.values())
    if (
        components["chronological_edge_quality"]
        < SCORECARD_COMPONENTS["chronological_edge_quality"]
    ):
        reasons["chronological_edge_quality"] = "metric_not_computed"

    # Time/symbol/parameter robustness (15) ---------------------------------- #
    components["time_symbol_param_robustness"] = _gate_component_points(
        verdicts, GateId.G4_SURVIVOR_ROBUSTNESS.value, full=15
    )
    if components["time_symbol_param_robustness"] < 15:
        reasons["time_symbol_param_robustness"] = str(
            verdicts.get(GateId.G4_SURVIVOR_ROBUSTNESS.value, GateVerdict.NOT_IMPLEMENTED).value
        )

    # Cost / execution realism (10): stress-evidence availability ------------ #
    cost = sum(_flag(COST_FLAG_POINTS, ev.cost_flags, key) for key in COST_FLAG_POINTS)
    components["cost_execution_realism"] = cost
    if cost < SCORECARD_COMPONENTS["cost_execution_realism"]:
        reasons.setdefault("cost_execution_realism", "metric_not_computed")

    # Risk quality (10): MDD/duration/R-normalization presence --------------- #
    risk = sum(_flag(RISK_FLAG_POINTS, ev.risk_flags, key) for key in RISK_FLAG_POINTS)
    components["risk_quality"] = risk
    if risk < SCORECARD_COMPONENTS["risk_quality"]:
        reasons.setdefault("risk_quality", "metric_missing_drawdown")

    # Portfolio / diversification (5) ----------------------------------------- #
    components["portfolio_diversification"] = _gate_component_points(
        verdicts, GateId.G5_PORTFOLIO.value, full=5
    )
    if components["portfolio_diversification"] < 5:
        reasons.setdefault("portfolio_diversification", str(
            verdicts.get(GateId.G5_PORTFOLIO.value, GateVerdict.NOT_APPLICABLE).value
        ))

    # Reproducibility / auditability (10): G2a -> 5, G2b -> 5 ----------------- #
    g2a_points = _gate_component_points(
        verdicts, "G2A_ARTIFACT_INTEGRITY", full=5
    )
    g2b_verdict = verdicts.get("G2B_INDEPENDENT_REPRODUCIBILITY")
    g2b_points = 5 if g2b_verdict is GateVerdict.PASS else 0
    components["reproducibility_auditability"] = g2a_points + g2b_points
    if g2a_points < 5:
        reasons.setdefault("reproducibility_auditability", "g2a_not_passed")
    if g2b_points < 5:
        reasons.setdefault(
            "reproducibility_auditability",
            "rerun_not_performed" if g2b_verdict is not GateVerdict.FAIL else "g2b_failed",
        )

    # Contract invariant: any non-max component carries an explicit reason.
    for name, max_points in SCORECARD_COMPONENTS.items():
        if components[name] < max_points:
            reasons.setdefault(name, "metric_not_computed")

    total = sum(components.values())
    return ScorecardResult(components=components, total=total, reasons=reasons)


def score_eligibility(gate_results: Iterable[GateResult]) -> dict:
    """Eligibility rules (PLAN section 10.2), fail-closed.

    * G0/G1/G2a FAIL          -> ``UNRANKED_PROTOCOL_FAIL``
    * G2b not run / not PASS  -> ``DIAGNOSTIC_ONLY``
    * G3 fail/inconclusive    -> ``NO_LEADERBOARD``
    * everything PASS         -> ``RANKABLE``
    """
    verdicts = _verdict_by_id(gate_results)
    protocol_fail_gates = ("G0_DATA", "G1_LEAKAGE", "G2A_ARTIFACT_INTEGRITY")
    failed = [
        gate
        for gate in protocol_fail_gates
        if verdicts.get(gate) is GateVerdict.FAIL
    ]
    if failed:
        return {"eligibility": "UNRANKED_PROTOCOL_FAIL", "reasons": sorted(failed)}
    g2b = verdicts.get("G2B_INDEPENDENT_REPRODUCIBILITY")
    if g2b is not GateVerdict.PASS:
        return {
            "eligibility": "DIAGNOSTIC_ONLY",
            "reasons": ["g2b_independent_reproduction_not_run"],
        }
    g3 = verdicts.get(GateId.G3_STAGE_A.value)
    if g3 in (GateVerdict.FAIL, GateVerdict.INCONCLUSIVE, GateVerdict.NOT_YET_TESTED):
        return {"eligibility": "NO_LEADERBOARD", "reasons": ["g3_stage_a_not_passed"]}
    return {"eligibility": "RANKABLE", "reasons": []}



def _round(value: float) -> int:
    return int(math.floor(value + 0.5))


def _round(value: float) -> int:
    return int(math.floor(value + 0.5))


def _verdict_map(
    gate_results: Iterable[GateResult],
) -> dict[str, GateVerdict]:
    """Verdicts keyed by PLAIN gate-id strings (enum-class agnostic)."""
    return {
        (result.gate.value if hasattr(result.gate, "value") else str(result.gate)): result.verdict
        for result in gate_results
    }


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
    integrity_gate_values = ("G0_DATA", "G1_LEAKAGE")
    passed = sum(
        1 for gate in integrity_gate_values if verdicts.get(gate) is GateVerdict.PASS
    )
    components["data_leakage_integrity"] = _round(
        SCORECARD_COMPONENTS["data_leakage_integrity"] * passed / len(integrity_gate_values)
    )
    for gate_value in integrity_gate_values:
        if verdicts.get(gate_value) != GateVerdict.PASS:
            reasons[f"gate_{gate_value}"] = str(
                verdicts.get(gate_value, GateVerdict.NOT_APPLICABLE).value
            )

    # Chronological edge quality (G3) --------------------------------------- #
    g3 = verdicts.get("G3_STAGE_A")
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
    if verdicts.get("G4_SURVIVOR_ROBUSTNESS") is GateVerdict.PASS:
        components["time_symbol_param_robustness"] = SCORECARD_COMPONENTS[
            "time_symbol_param_robustness"
        ]
    else:
        components["time_symbol_param_robustness"] = 0
        reasons["time_symbol_param_robustness"] = str(
            verdicts.get(
                "G4_SURVIVOR_ROBUSTNESS", GateVerdict.NOT_IMPLEMENTED
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
    if verdicts.get("G5_PORTFOLIO") is GateVerdict.PASS:
        components["portfolio_diversification"] = SCORECARD_COMPONENTS[
            "portfolio_diversification"
        ]
    else:
        components["portfolio_diversification"] = 0
        reasons["portfolio_diversification"] = str(
            verdicts.get("G5_PORTFOLIO", GateVerdict.NOT_APPLICABLE).value
        )

    # Reproducibility / auditability (G2) -------------------------------------- #
    # Sprint V3: the combined G2 row is replaced by G2a (artifact integrity)
    # + G2b (independent rerun); both PASS -> full points, one PASS -> half.
    g2a = verdicts.get("G2A_ARTIFACT_INTEGRITY")
    g2b = verdicts.get("G2B_INDEPENDENT_REPRODUCIBILITY")
    g2_passes = [g2a is GateVerdict.PASS, g2b is GateVerdict.PASS]
    if all(g2_passes):
        components["reproducibility_auditability"] = SCORECARD_COMPONENTS[
            "reproducibility_auditability"
        ]
    elif any(g2_passes):
        components["reproducibility_auditability"] = _round(
            SCORECARD_COMPONENTS["reproducibility_auditability"] * 0.5
        )
        reasons.setdefault("reproducibility_auditability", "g2_pair_partial")
    else:
        components["reproducibility_auditability"] = 0
        reasons["reproducibility_auditability"] = "rerun_not_performed"

    # Guarantee the contract invariant: any component below its maximum
    # carries an explicit machine-readable reason.
    for name, max_points in SCORECARD_COMPONENTS.items():
        if components[name] < max_points:
            reasons.setdefault(name, "metric_not_computed")

    total = sum(components.values())
    return ScorecardResult(components=components, total=total, reasons=reasons)
