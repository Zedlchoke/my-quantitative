"""VOL-NG1 I-phase Stage-A R1-R6 enforcement scaffolding (fail-closed).

The frozen rule order is inherited VERBATIM (in adapted form) from the
FOREX-NG1 precedent that the binding freeze itself cites
(``selection_freeze.rule_set_r1_r6`` provenance):

    R1 EXPECTANCY          after-cost expectancy > 0 on the PRIMARY NET
                           book at cost tier 2.0 (Q-16 path component
                           included; cost charged once per fill)
    R2 CONTROL_KILL        the arm's index-only re-clock control
                           out-earns the arm same-sign at >= 0.5x per
                           ROUND TRIP, OR the calendar-clock shadow
                           placement is not distinct from the arm
                           placement, OR the seeded placebo produces a
                           significant differential placement -- each
                           is a VETO (A5-P2 D1 non-distinctness kill
                           binding site)
    R3 FOLDS               >= 2/3 frozen temporal folds with positive
                           after-cost expectancy (folds frozen in the
                           freeze: F1/F2/F3 on the vol bookable window)
    R4 PROFIT_FACTOR       >= 1.10 with margin recorded (P-2)
    R5 STRESS              after-cost expectancy still > 0 under the
                           FULL measured path-cost ladder at tier 2.0
                           including every leg's Q-16 path component,
                           the A4-P2 forced-rebalance count and the
                           A5-P2 both-bucket rotation costs (A4-P2 D1
                           cost-ceiling family kill binding site)
    R6 NON_CONCENTRATION   drop-one-fold survival AND no single round
                           trip > 50% of the cell's gross

    survivor := passes ALL rules -> PROVISIONAL_STAGE_A_SURVIVOR
    (S1 stays SEALED; no rescue after scored numbers are visible)

Fail-closed law: a rule whose metric is missing or uncomputable
evaluates NOT_RUN (never an inferred PASS); any NOT_RUN rule blocks the
survivor verdict (Q-11; the FOREX-NG1 I evaluator precedent realized by
commit f6c17886c32025242fdf21ffb8565666d64cbaec).

PBO LAW: PBO/CSCV is fail-closed NOT_RUN when cells < 8 (V17 contract;
plans/PLAN_forex_ng1.md section 5 precedent).  This cycle books 6
cells, so PBO evaluates NOT_RUN here and the FROZEN ALTERNATIVE
robustness rule applies: R6 NON_CONCENTRATION (drop-one-fold survival +
50% gross cap), stage_a_rule_order_frozen[5] of the FOREX-NG1 freeze
(commit d0992d17df8e2dfde57c9a0806a5798f14021a4f).

This lane is METRIC-DRIVEN SCAFFOLDING only: it never computes scored
metrics itself.  Metrics are supplied at E from scored books under
authority; here the evaluator is exercised ONLY on hand-built synthetic
metric fixtures.
"""

from __future__ import annotations

from research.assets.vol_ng1.runners import config as cfg

NOT_RUN = "NOT_RUN"
PASS = "PASS"
FAIL = "FAIL"

#: evaluable metric keys per rule (documentation + the dry-run's
#: metric-schema check; the evaluator itself fails closed on absence).
RULE_METRIC_KEYS = {
    "R1_EXPECTANCY": ["expectancy_net_tier2"],
    "R2_CONTROL_KILL": ["arm_expectancy_net_tier2",
                        "index_control_expectancy_net_tier2",
                        "calendar_shadow_placement_distinct",
                        "placebo_differential_significant"],
    "R3_FOLDS": ["fold_expectancies_net_tier2"],
    "R4_PF": ["profit_factor_net_tier2"],
    "R5_STRESS": ["stress_tier2_expectancy_net"],
    "R6_NON_CONCENTRATION": ["drop_one_fold_positive",
                             "max_single_round_trip_gross_share"],
}


class EvaluatorInputError(Exception):
    """Malformed metrics (fail-closed)."""


def _expect(metrics: dict, key: str) -> float | None:
    if not isinstance(metrics, dict):
        raise EvaluatorInputError("metrics must be a dict")
    v = metrics.get(key)
    if v is None:
        return None
    v = float(v)
    if v != v:                    # NaN
        return None
    return v


def _expect_bool(metrics: dict, key: str) -> bool | None:
    v = metrics.get(key)
    if v is None or not isinstance(v, bool):
        return None
    return v


def control_reproduces(control_expectancy: float | None,
                       arm_expectancy: float | None) -> bool | None:
    """The V8-law falsification-by-control test at the frozen 0.5x
    per-round-trip ratio: the control REPRODUCES the arm when its
    expectancy is positive same-sign and >= 0.5x the arm's."""
    if control_expectancy is None or arm_expectancy is None:
        return None
    return bool(control_expectancy > 0 and arm_expectancy != 0
                and control_expectancy
                >= cfg.CONTROL_KILL_RATIO * arm_expectancy)


def evaluate_r1(metrics: dict) -> str:
    exp = _expect(metrics, "expectancy_net_tier2")
    if exp is None:
        return NOT_RUN
    return PASS if exp > 0 else FAIL


def evaluate_r2(metrics: dict) -> str:
    """R2 CONTROL_KILL, three VETO limbs; ALL limb metrics must be
    present for a PASS (any missing limb -> NOT_RUN, fail-closed):
      (a) index-only control out-earns the arm same-sign >= 0.5x per
          round trip;
      (b) calendar-clock shadow placement NOT distinct from the arm
          placement;
      (c) seeded placebo produces a significant differential placement.
    """
    ae = _expect(metrics, "arm_expectancy_net_tier2")
    ce = _expect(metrics, "index_control_expectancy_net_tier2")
    rep = control_reproduces(ce, ae)
    cal = _expect_bool(metrics, "calendar_shadow_placement_distinct")
    pl = _expect_bool(metrics, "placebo_differential_significant")
    if rep is None or cal is None or pl is None:
        return NOT_RUN
    if rep or (cal is False) or (pl is True):
        return FAIL
    return PASS


def evaluate_r3(metrics: dict) -> str:
    folds = metrics.get("fold_expectancies_net_tier2")
    if not isinstance(folds, dict) or len(folds) != cfg.FOLDS_TOTAL:
        return NOT_RUN
    vals = [_expect({"x": folds[k]}, "x") for k in sorted(folds)]
    if any(v is None for v in vals):
        return NOT_RUN
    positive = sum(1 for v in vals if v > 0)
    return PASS if positive >= cfg.MIN_POSITIVE_FOLDS else FAIL


def evaluate_r4(metrics: dict) -> dict:
    pf = _expect(metrics, "profit_factor_net_tier2")
    if pf is None:
        return {"verdict": NOT_RUN, "margin_to_bar": None}
    return {"verdict": PASS if pf >= cfg.PF_BAR else FAIL,
            "margin_to_bar": round(pf - cfg.PF_BAR, 10)}


def evaluate_r5(metrics: dict) -> str:
    """R5 STRESS: the stress-convention expectancy from the cost-path
    control (FULL measured path-cost ladder at tier 2.0, Q-16 path
    component, A4 forced-rebalance count, A5 both-bucket rotation)."""
    stress = _expect(metrics, "stress_tier2_expectancy_net")
    if stress is None:
        return NOT_RUN
    return PASS if stress > 0 else FAIL


def evaluate_r6(metrics: dict) -> str:
    drop_one = metrics.get("drop_one_fold_positive")
    max_share = _expect(metrics, "max_single_round_trip_gross_share")
    if not isinstance(drop_one, dict) \
            or len(drop_one) != cfg.FOLDS_TOTAL:
        return NOT_RUN
    vals = [bool(drop_one[k]) for k in sorted(drop_one)
            if drop_one[k] is not None]
    if len(vals) != cfg.FOLDS_TOTAL or max_share is None:
        return NOT_RUN
    survival = all(vals)
    concentration_ok = max_share <= cfg.MAX_ROUND_TRIP_GROSS_SHARE
    return PASS if (survival and concentration_ok) else FAIL


def evaluate_stage_a(metrics: dict) -> dict:
    """The full frozen rule order; survivor requires ALL rules PASS;
    any NOT_RUN blocks (fail-closed, never an inferred PASS)."""
    r4 = evaluate_r4(metrics)
    rules = {
        "R1_EXPECTANCY": evaluate_r1(metrics),
        "R2_CONTROL_KILL": evaluate_r2(metrics),
        "R3_FOLDS": evaluate_r3(metrics),
        "R4_PF": r4["verdict"],
        "R5_STRESS": evaluate_r5(metrics),
        "R6_NON_CONCENTRATION": evaluate_r6(metrics),
    }
    any_not_run = any(v == NOT_RUN for v in rules.values())
    any_fail = any(v == FAIL for v in rules.values())
    verdict = NOT_RUN if any_not_run else (
        "PROVISIONAL_STAGE_A_SURVIVOR" if not any_fail else "STAGE_A_DEAD")
    return {
        "rule_verdicts": rules,
        "r4_margin_to_bar": r4["margin_to_bar"],
        "verdict": verdict,
        "law": "survivor := passes ALL rules (R1-R6); any missing metric "
               "is NOT_RUN (fail-closed, never an inferred PASS); S1 "
               "stays SEALED; no rescue after scored numbers",
    }


def pbo_law(n_cells: int) -> dict:
    """The frozen PBO law, enforced mechanically.

    PBO/CSCV requires >= 8 cells (V17 contract).  This cycle books 6
    cells, so PBO evaluates NOT_RUN fail-closed and the FROZEN
    ALTERNATIVE robustness rule applies in its place: R6
    NON_CONCENTRATION (drop-one-fold survival + no single round trip
    > 50% of the cell's gross), inherited verbatim from the FOREX-NG1
    precedent the freeze cites.  For >= 8 cells the CSCV computation
    itself is still NOT implemented in the I lane and honestly stays
    NOT_RUN here (an E-phase obligation); this function never fabricates
    a PBO number."""
    n_cells = int(n_cells)
    if n_cells < cfg.PBO_MIN_CELLS:
        reason = (f"PBO fail-closed: {n_cells} booked cells < "
                  f"{cfg.PBO_MIN_CELLS} (CSCV undefined; V17 contract)")
    else:
        reason = ("CSCV not implemented in the I lane: PBO stays NOT_RUN "
                  "(no number fabricated)")
    return {
        "rule": "PBO/CSCV",
        "n_cells": n_cells,
        "min_cells": cfg.PBO_MIN_CELLS,
        "verdict": NOT_RUN,
        "reason": reason,
        "alternative_rule_applied": cfg.PBO_ALTERNATIVE_RULE,
        "alternative_rule_binding_site": "R6_NON_CONCENTRATION",
        "precedent_commits": list(cfg.PBO_PRECEDENT_COMMITS),
    }
