"""Stage-A R1-R6 mechanical evaluator (frozen rule order, fail-closed).

The rule battery is frozen verbatim from
``selection_freeze.stage_a_rule_order_frozen``:

    R1 EXPECTANCY   after-cost expectancy > 0 (tier 2.0 PRIMARY)
    R2 CONTROL_KILL control out-earns anchor same-sign >= 0.5x per-trade
                    (V8 law; for A5 additionally the V7-recap kill R2' if
                    CTL-V7RECAP reproduces the anchor)
    R3 FOLDS        >= 2/3 temporal folds positive (folds frozen)
    R4 PF           >= 1.10 with margin recorded (P-2)
    R5 STRESS       stress tier 2.0 expectancy still > 0
    R6 NON_CONCENTRATION
                    drop-one-fold survival + no single event > 50% gross

    survivor := passes ALL rules -> PROVISIONAL_STAGE_A_SURVIVOR

Fail-closed law: a rule whose metric is MISSING evaluates to NOT_RUN
(never an inferred PASS), and any NOT_RUN rule blocks the survivor
verdict.  This lane exercises the evaluator ONLY on synthetic fixtures;
it is never run on real outcomes here (the RA namespace is entered only
when a scored run exists).
"""

from __future__ import annotations

PF_BAR = 1.10
CONTROL_KILL_RATIO = 0.5
MIN_POSITIVE_FOLDS = 2
FOLDS_TOTAL = 3
MAX_EVENT_GROSS_SHARE = 0.50

NOT_RUN = "NOT_RUN"
PASS = "PASS"
FAIL = "FAIL"


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


def control_reproduces(control_expectancy: float | None,
                       anchor_expectancy: float | None) -> bool | None:
    """V8 falsification-by-control law: the control REPRODUCES the anchor
    when its expectancy is positive and >= 0.5x the anchor's."""
    if control_expectancy is None or anchor_expectancy is None:
        return None
    return bool(control_expectancy > 0 and anchor_expectancy != 0
                and control_expectancy
                >= CONTROL_KILL_RATIO * anchor_expectancy)


def evaluate_r1(metrics: dict) -> str:
    exp = _expect(metrics, "expectancy_net_tier2")
    if exp is None:
        return NOT_RUN
    return PASS if exp > 0 else FAIL


def evaluate_r2(metrics: dict) -> str:
    """R2 CONTROL_KILL (+ the A5 R2' V7-recap kill when the v7recap
    expectancy is supplied).  FAIL fires when EITHER the family control
    or the additional V7-recap control reproduces the anchor."""
    ae = _expect(metrics, "anchor_expectancy_net_tier2")
    ce = _expect(metrics, "control_expectancy_net_tier2")
    rep = control_reproduces(ce, ae)
    v7 = _expect(metrics, "v7recap_expectancy_net_tier2")
    rep7 = control_reproduces(v7, ae) if v7 is not None else None
    if rep is None:
        return NOT_RUN
    if rep or (rep7 is True):
        return FAIL
    return PASS


def evaluate_r3(metrics: dict) -> str:
    folds = metrics.get("fold_expectancies_net_tier2")
    if not isinstance(folds, dict) or len(folds) != FOLDS_TOTAL:
        return NOT_RUN
    vals = [_expect({"x": folds[k]}, "x") for k in sorted(folds)]
    if any(v is None for v in vals):
        return NOT_RUN
    positive = sum(1 for v in vals if v > 0)
    return PASS if positive >= MIN_POSITIVE_FOLDS else FAIL


def evaluate_r4(metrics: dict) -> dict:
    pf = _expect(metrics, "profit_factor_net_tier2")
    if pf is None:
        return {"verdict": NOT_RUN, "margin_to_bar": None}
    return {"verdict": PASS if pf >= PF_BAR else FAIL,
            "margin_to_bar": round(pf - PF_BAR, 10)}


def evaluate_r5(metrics: dict) -> str:
    exp = _expect(metrics, "expectancy_net_tier2")   # tier 2.0 IS the
    # stress tier of the frozen ladder (PRIMARY = 2.0); a separately
    # supplied stress metric, when present, must agree.
    stress = _expect(metrics, "stress_tier2_expectancy_net")
    if stress is not None:
        exp = stress
    if exp is None:
        return NOT_RUN
    return PASS if exp > 0 else FAIL


def evaluate_r6(metrics: dict) -> str:
    drop_one = metrics.get("drop_one_fold_positive")
    max_share = _expect(metrics, "max_single_event_gross_share")
    if not isinstance(drop_one, dict) or len(drop_one) != FOLDS_TOTAL:
        return NOT_RUN
    vals = [bool(drop_one[k]) for k in sorted(drop_one)
            if drop_one[k] is not None]
    if len(vals) != FOLDS_TOTAL or max_share is None:
        return NOT_RUN
    survival = all(vals)
    concentration_ok = max_share <= MAX_EVENT_GROSS_SHARE
    return PASS if (survival and concentration_ok) else FAIL


def evaluate_stage_a(metrics: dict) -> dict:
    """The full frozen rule order; survivor requires ALL rules PASS."""
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
    verdict = "NOT_RUN" if any_not_run else (
        "PROVISIONAL_STAGE_A_SURVIVOR" if not any_fail else
        "STAGE_A_DEAD")
    return {
        "rule_verdicts": rules,
        "r4_margin_to_bar": r4["margin_to_bar"],
        "verdict": verdict,
        "law": "survivor := passes ALL rules (R1-R6); any missing metric "
               "is NOT_RUN (fail-closed, never an inferred PASS)",
    }
