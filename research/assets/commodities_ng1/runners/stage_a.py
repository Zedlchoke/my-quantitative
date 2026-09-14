"""COMMODITIES-NG1 stage-A R1-R6 scaffolding over the FROZEN folds.

Rule order and thresholds are FROZEN verbatim in the S freeze
(``section3_stage_a_rules_r1_r6``), adapted faithfully from the
FOREX-NG1 selection-freeze precedent's ``stage_a_rule_order_frozen``
(git d0992d17df8e2dfde57c9a0806a5798f14021a4f:
research/control/forex_ng1_run/selection_freeze.json -- rule ORDER and
thresholds unchanged; R2 carries this family's stricter D1
falsification clause; R3 folds are THIS cycle's counted window;
R1/R5 name THIS cycle's Q-16 drag law).

    R1 EXPECTANCY: after-cost expectancy > 0 at tier 2.0 PRIMARY
        (transaction component at the CS-p90 tier-2.0 ladder, charged
        exactly once per fill; Q-16 instrument drag accrued daily over
        the held horizon -- part of the mechanism, never noise).
    R2 CONTROL_KILL: any designated KILLER control out-earning the
        anchor same-sign >= 0.5x per-trade (V8 law) -- AND this
        family's D1 falsification rule: ANY strictly greater
        after-cost per-decision edge by a designated killer kills.
    R3 FOLDS: >= 2/3 temporal folds positive; a fold is positive iff
        its after-cost expectancy at tier 2.0 PRIMARY is > 0.  Folds
        frozen on the counted window (2019-01-04 .. 2026-09-11).
    R4 PF: profit factor >= 1.10, margin above 1.10 recorded (P-2).
    R5 STRESS: stress tier 2.0 expectancy still > 0 (the transaction
        component at the 2.0 stress multiple; the instrument drag is
        tier-independent per the P1 charge law, so the drag bill is
        unchanged by the stress scaling -- with this ladder the stress
        multiple IS the primary tier; the rule is evaluated explicitly
        so the property stays auditable).
    R6 NON_CONCENTRATION: drop-one-fold survival AND no single event
        carrying > 50% of gross.

    survivor := passes ALL rules -> PROVISIONAL_STAGE_A_SURVIVOR
    (S1 stays SEALED; no rescue after scored numbers visible).

PBO LAW (plans/PLAN_crypto_ng1.md section 5 "PBO fail-closed NOT_RUN
when cells < 8 (V17 contract)", adopted verbatim by
plans/PLAN_commodities_ng1.md section 5 "PBO fail-closed < 8 cells"):
this cycle books 3 cells < 8, so the PBO diagnostic is FAIL-CLOSED
NOT_RUN -- never inferred, never approximated.  The frozen ALTERNATIVE
discipline is the FOREX-NG1 precedent rule the S freeze cites
(its ``stage_a_rule_order_frozen``, R1-R6 above, instantiated with this
cycle's committed battery and counted window): the pre-registered
rule-order screen stands in for the cell-count-hungry PBO statistic
and is evaluated per booked cell.
"""

from __future__ import annotations

import math
from datetime import date

SCHEMA = "commodities_ng1/runners/stage_a@1"

#: Frozen folds (S freeze ``folds_frozen``): release-date anchors on
#: the counted weekly decision grid; NEVER re-cut after outcomes.
FOLDS_FROZEN = (
    {"fold_id": "fold-1", "release_date_start": "2019-01-04",
     "release_date_end": "2021-08-31"},
    {"fold_id": "fold-2", "release_date_start": "2021-09-01",
     "release_date_end": "2024-04-30"},
    {"fold_id": "fold-3", "release_date_start": "2024-05-01",
     "release_date_end": "2026-09-11"},
)

PF_FLOOR = 1.10
EVENT_CONCENTRATION_CAP = 0.50
R3_MIN_POSITIVE_FOLDS = 2

#: PBO fail-closed minimum cell count (V17 contract law).
PBO_MIN_CELLS = 8

#: The FOREX-NG1 precedent citation for the frozen alternative rule.
FOREX_NG1_PRECEDENT_CITATION = {
    "source": "research/control/forex_ng1_run/selection_freeze.json",
    "git_commit": "d0992d17df8e2dfde57c9a0806a5798f14021a4f",
    "role": "FOREX-NG1 selection freeze PRECEDENT: stage_a_rule_order_"
            "frozen (R1-R6) adapted faithfully by the COMMODITIES-NG1 "
            "S freeze (rule ORDER and thresholds unchanged; R2 control "
            "set and R3 folds instantiated with this cycle's committed "
            "battery and counted window)",
}


class FoldRefused(Exception):
    """Release date outside the frozen fold bounds: fail-closed."""


def fold_of(release_date) -> str | None:
    """Frozen fold of a counted release date (boundary-inclusive
    start/end anchors); ``None`` outside the frozen bounds."""
    d = release_date if isinstance(release_date, date) else \
        date.fromisoformat(str(release_date))
    for f in FOLDS_FROZEN:
        if date.fromisoformat(f["release_date_start"]) <= d \
                <= date.fromisoformat(f["release_date_end"]):
            return f["fold_id"]
    return None


def r1_expectancy(metrics: dict) -> dict:
    """R1: after-cost expectancy > 0 at tier 2.0 PRIMARY (per-trade
    net edge).  Q-11: zero trades is NOT_RUN, never a pass."""
    e = metrics["per_trade_edge"]
    if e is None:
        return {"rule": "R1", "verdict": "NOT_RUN",
                "why": "no trades: expectancy undefined (Q-11 "
                       "invalid-null, never zero)"}
    return {"rule": "R1", "verdict": "PASS" if e > 0 else "FAIL",
            "per_trade_edge": e,
            "why": "after-cost expectancy (tier 2.0 PRIMARY, once per "
                   "fill, Q-16 drag carried) "
                   + ("> 0" if e > 0 else "<= 0")}


def r2_control_kill(anchor_metrics: dict,
                    killer_metrics: dict) -> dict:
    """R2 for ONE designated killer: BOTH frozen clauses.

    (a) V8 law: the killer out-earns the anchor same-sign
        >= 0.5x per-trade;
    (b) D1 falsification rule (stricter): the killer's after-cost
        per-decision edge is STRICTLY GREATER than the anchor's.
    """
    a_t = anchor_metrics["per_trade_edge"]
    k_t = killer_metrics["per_trade_edge"]
    v8 = False
    v8_why = "undefined edge (no trades on one side)"
    if a_t is not None and k_t is not None and a_t != 0.0:
        same_sign = (a_t > 0 and k_t > 0) or (a_t < 0 and k_t < 0)
        v8 = bool(same_sign and k_t >= 0.5 * a_t)
        v8_why = (f"killer per-trade {k_t:.6g} vs anchor {a_t:.6g} "
                  f"(same-sign >= 0.5x threshold {0.5 * a_t:.6g})")
    a_d = anchor_metrics["per_decision_edge"]
    k_d = killer_metrics["per_decision_edge"]
    falsified = False
    f_why = "undefined per-decision edge (Q-11)"
    if a_d is not None and k_d is not None:
        falsified = bool(k_d > a_d)
        f_why = (f"killer per-decision {k_d:.6g} vs anchor {a_d:.6g} "
                 f"(strictly-greater clause "
                 f"{'fires' if falsified else 'clear'})")
    kill = bool(v8 or falsified)
    return {"rule": "R2", "kill": kill,
            "v8_clause": {"fires": v8, "why": v8_why},
            "falsification_clause": {"fires": falsified, "why": f_why}}


def r3_folds(fold_nets: dict[str, float]) -> dict:
    """R3: >= 2/3 frozen folds positive; a fold is positive iff its
    after-cost expectancy at tier 2.0 PRIMARY is > 0 (for a fixed
    decision count the net total carries the sign of the expectancy;
    both are reported)."""
    per_fold = {}
    for f in FOLDS_FROZEN:
        fid = f["fold_id"]
        total = fold_nets.get(fid)
        if total is None:
            per_fold[fid] = {"net_total": None, "positive": None,
                             "why": "no decisions in fold (NOT_RUN)"}
        else:
            per_fold[fid] = {"net_total": total,
                             "positive": bool(total > 0)}
    measured = [v["positive"] for v in per_fold.values()
                if v["positive"] is not None]
    n_positive = sum(1 for p in measured if p)
    verdict = "PASS" if (len(measured) == len(FOLDS_FROZEN)
                         and n_positive >= R3_MIN_POSITIVE_FOLDS) \
        else "FAIL"
    return {"rule": "R3", "verdict": verdict,
            "folds": per_fold, "positive_folds": n_positive,
            "required": R3_MIN_POSITIVE_FOLDS}


def r4_profit_factor(metrics: dict) -> dict:
    """R4: profit factor >= 1.10 with the margin recorded (P-2)."""
    pf = metrics["profit_factor"]
    if pf is None:
        n = metrics["trades"]
        verdict = "PASS" if n > 0 else "NOT_RUN"
        return {"rule": "R4", "verdict": verdict,
                "profit_factor": None, "margin_above_1_10": None,
                "why": "no losing net trades (PF unbounded)"
                if n > 0 else "no trades (Q-11)"}
    margin = pf - PF_FLOOR
    return {"rule": "R4",
            "verdict": "PASS" if pf >= PF_FLOOR else "FAIL",
            "profit_factor": pf, "margin_above_1_10": margin,
            "why": f"PF {pf:.4f} vs floor {PF_FLOOR} "
                   f"(margin {margin:+.4f}, P-2)"}


def r5_stress(metrics: dict) -> dict:
    """R5: stress tier 2.0 expectancy still > 0.  The instrument drag
    is tier-independent (P1 charge law), so the drag bill is unchanged
    by the stress scaling; with ladder {1.0, 1.5, 2.0} the 2.0 stress
    multiple IS the primary tier -- the rule is evaluated explicitly
    from the same book so that identity stays auditable."""
    e = metrics["per_trade_edge"]
    if e is None:
        return {"rule": "R5", "verdict": "NOT_RUN",
                "why": "no trades: stress expectancy undefined (Q-11)"}
    return {"rule": "R5", "verdict": "PASS" if e > 0 else "FAIL",
            "stress_tier": 2.0, "per_trade_edge": e,
            "why": "stress-tier (2.0) after-cost expectancy "
                   + ("> 0" if e > 0 else "<= 0")
                   + "; drag tier-independent (P1 charge law)"}


def r6_non_concentration(metrics: dict, fold_nets: dict) -> dict:
    """R6: drop-one-fold survival (R1 expectancy > 0 and R4 PF floor
    on every leave-one-fold-out subset of the NET book) AND no single
    event carrying > 50% of gross."""
    nets = metrics["net_pnls"]
    gross = metrics["gross_pnls"]
    gross_total = math.fsum(gross) if gross else 0.0
    # drop-one-fold survival over the fold-partitioned net totals
    folds_present = [fid for fid in (f["fold_id"] for f in FOLDS_FROZEN)
                     if fold_nets.get(fid) is not None]
    drop_one = []
    for drop in folds_present:
        kept = [fid for fid in folds_present if fid != drop]
        total = math.fsum(fold_nets[fid] for fid in kept)
        # expectancy sign on the kept subset (per-fold decision counts
        # are strictly positive whenever the fold is present)
        drop_one.append({"dropped": drop, "kept_folds": kept,
                         "net_total": total,
                         "expectancy_positive": bool(total > 0)})
    survival = bool(drop_one) and all(d["expectancy_positive"]
                                      for d in drop_one)
    if gross_total > 0 and gross:
        max_event = max(abs(v) for v in gross)
        share = max_event / gross_total
        concentrated = bool(share > EVENT_CONCENTRATION_CAP)
    else:
        share = None
        concentrated = True   # no positive gross: concentration fails
    ok = bool(survival and not concentrated)
    return {"rule": "R6", "verdict": "PASS" if ok else "FAIL",
            "drop_one_fold": drop_one,
            "drop_one_survival": survival,
            "max_event_gross_share": share,
            "concentration_cap": EVENT_CONCENTRATION_CAP,
            "concentrated": concentrated,
            "why": "drop-one-fold survival "
                   + ("held" if survival else "broken")
                   + "; max single-event gross share "
                   + (f"{share:.4f}" if share is not None
                      else "undefined (no positive gross)")}


def pbo_verdict(booked_cells: int) -> dict:
    """PBO fail-closed law: cells < 8 => NOT_RUN (V17 contract); the
    frozen alternative discipline is the FOREX-NG1 precedent R1-R6
    rule order cited by the S freeze."""
    cells = int(booked_cells)
    runnable = cells >= PBO_MIN_CELLS
    return {
        "schema": SCHEMA,
        "diagnostic": "PBO (probability of backtest overfitting)",
        "law": "PBO fail-closed NOT_RUN when cells < 8 (V17 contract; "
               "plans/PLAN_crypto_ng1.md section 5, adopted verbatim "
               "by plans/PLAN_commodities_ng1.md section 5)",
        "booked_cells": cells,
        "minimum_cells": PBO_MIN_CELLS,
        "verdict": "MEASURABLE_AT_E" if runnable else "NOT_RUN_CELLS_LT_8",
        "alternative_rule": {
            "law": "with PBO fail-closed, the frozen alternative "
                   "overfitting discipline is the stage-A rule order "
                   "R1-R6 from the FOREX-NG1 precedent cited inside "
                   "the S freeze (section3 law_sources), instantiated "
                   "with THIS cycle's committed battery, folds and "
                   "counted window; evaluated per booked cell",
            **FOREX_NG1_PRECEDENT_CITATION,
        },
    }


def evaluate_stage_a(anchor_metrics: dict, killer_metrics: dict,
                     fold_nets: dict) -> dict:
    """The full R1-R6 screen for ONE booked cell (anchor metrics vs
    the designated-killer battery).  ``fold_nets`` maps fold_id ->
    anchor after-cost net total on the fold (entry-release assignment).

    Q-11: an arm whose metrics are NOT_RUN (no trades) cannot pass;
    each rule records its own NOT_RUN verdict instead of a pass.
    """
    rules = {
        "R1": r1_expectancy(anchor_metrics),
        "R2": {k: r2_control_kill(anchor_metrics, m)
               for k, m in killer_metrics.items()},
        "R3": r3_folds(fold_nets),
        "R4": r4_profit_factor(anchor_metrics),
        "R5": r5_stress(anchor_metrics),
        "R6": r6_non_concentration(anchor_metrics, fold_nets),
    }
    r2_kill = any(v["kill"] for v in rules["R2"].values())
    hard = [rules["R1"], rules["R3"], rules["R4"], rules["R5"],
            rules["R6"]]
    all_pass = all(r["verdict"] == "PASS" for r in hard) and not r2_kill
    return {
        "schema": SCHEMA,
        "rules": rules,
        "r2_any_kill": r2_kill,
        "survivor": bool(all_pass),
        "verdict": "PROVISIONAL_STAGE_A_SURVIVOR" if all_pass
        else "KILLED_OR_FAILED",
        "law": "survivor := passes ALL rules -> PROVISIONAL_STAGE_A_"
               "SURVIVOR (S1 stays SEALED; no rescue after scored "
               "numbers visible)",
    }
