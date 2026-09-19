"""STOCKS-SEARCH-V1 I-lane adjudication harness (plans/PLAN_stocks_search_v1.md §6, §8–§9).

Ordered first-binding kills over the §6 falsification books built by
i_engine.build_all_books, then the frozen stocks Stage-A battery.  All
numbers are NET (total-return basis, stress-2.0 primary).  Pure over the
provided book bundle: this module never loads market data itself.

Ordered rules (first binding kills; plan §6 verbatim thresholds):
  R1  expectancy            net expectancy <= 0 at stress 2.0 -> REJECT_ALL
  R2  long-market reduction candidate <= max(C-MARKET, C-RANDOM-TIMING)
                            net expectancy -> REJECT (Stage-A additionally
                            requires SPY-excess >= 2/3 folds, MDD <= 15%,
                            largest-fold PnL concentration <= 50%)
  R3  mechanism specificity C-COMPLEMENT out-earns OR reproduces >= 0.5x
                            same-sign in >= 2/3 folds -> REJECT
  R4  reversal reduction    C-REVERSAL-PLAIN out-earns OR reproduces
                            >= 0.5x same-sign in >= 2/3 folds -> REJECT
                            (NG6-R4 re-inherited; MANDATORY)
  R5  component placebo     component-only reproduces >= 0.5x same-sign
                            -> REJECT.  Binding form (fail-closed union,
                            disclosed): fold rule as R3/R4 (>= 2/3 folds)
                            OR full-sample same-sign >= 0.5x.  A control
                            with zero legs is NOT_ADJUDICABLE, never an
                            inferred PASS.
  R6  clock geometry        C-RANDOM-TIMING out-earns -> REJECT; the
                            C-CAL-HIST rule extends here (must NOT
                            out-earn); a sub-floor C-CAL-HIST bucket is
                            NOT_ADJUDICABLE and disclosed.
  K6  slow-drift combination {candidate, C-DELAY-H} x {state, complement}
                            mutually indistinguishable within fold noise
                            -> REJECT.  DEVIATION DISCLOSED: the plan
                            froze the exact test "at S" but the S freeze
                            contains none; the test is pinned in
                            i_engine (SE_f noise scale, >= 2/3 folds)
                            BEFORE any E measurement, recorded in the I
                            handoff.

Stage-A gates on any survivor (plan §6): fold-positive-share > 50%
KILLS (V11 precedent 0.5034 was a FAILING value; the statistic is the
largest positive fold's share of total positive fold PnL on the P-11
daily book series); largest-fold PnL concentration > 50% KILLS
(max |fold PnL| / sum |fold PnL|); SPY-excess positive in >= 2/3 folds
REQUIRED; MDD <= 15%; stress-2.0 net positive with break-even margin;
drop-one sign stability; death contract per BC-7 in full with
death-censoring invariance binding the VERDICT AND every gate; PIT
mutation; DSR gate (Bailey/Lopez de Prado E[max SR], estimator
DSR_BAILEY_LOPEZDEPRADO_V1, N = frozen grid 47 at alpha 0.10) computed
ONLY at the scored E run and gating BEFORE any survivor name is named;
program-cumulative N=260 at alpha 0.05 reported-only; PBO NOT_RUN
fail-closed (<=3 cells, d0992d17 class) printed on every result; R0
NOT_RUN labels verbatim; budget counter carried (max 3 scored cells).

The real-data path is load_real_data: it refuses ANY load unless the
exact owner GO phrase `GO STOCKS SEARCH V1 SCORED EXECUTION` is
presented (early or paraphrased GO dies unconsumed, P-8).  No scored
execution exists anywhere in this lane.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_RUN_DIR = _HERE.parent
_REPO_ROOT = _RUN_DIR.parents[1].parent
for _p in (str(_REPO_ROOT), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from i_engine import (  # noqa: E402
    CELL_BY_ID,
    CELL_IDS,
    DISCLOSURE_SECTION10_VERBATIM,
    GO_PHRASE,
    PBO_NOT_RUN_LABEL,
    PBO_NOT_RUN_VERBATIM,
    R0_NOT_RUN_LABEL,
    R0_NOT_RUN_VERBATIM,
    STRESS_TIER,
    NameData,
    include_censored_nets,
    load_p0_lib,
    spy_legs_for,
    verify_freeze,
)

BUDGET_MAX_SCORED_CELLS = 3
DSR_N_GRID = 47
DSR_ALPHA_RELAXED = 0.10
DSR_N_PROGRAM = 260
DSR_ALPHA_PROGRAM = 0.05
MDD_LIMIT = 0.15
CONCENTRATION_LIMIT = 0.50


class GoGateRefused(RuntimeError):
    """The exact owner GO phrase was not presented (P-8: early or
    paraphrased GO dies unconsumed)."""


# ---------------------------------------------------------------- helpers

def _mean(xs) -> float:
    xs = [x for x in xs if x == x and x is not None]   # NaN-safe
    return float(np.mean(xs)) if xs else math.nan


def _same_sign_half(value: float, ref: float) -> bool:
    """reproduces >= 0.5x same-sign (strictly same sign; zero is neutral)."""
    if value == value and ref == ref and ref != 0.0:
        return value * ref > 0.0 and abs(value) >= 0.5 * abs(ref)
    return False


def _fold_pairs(cand_fold: dict, ctrl_fold: dict) -> dict:
    folds = sorted(set(cand_fold) | set(ctrl_fold))
    return {f: (cand_fold.get(f, math.nan), ctrl_fold.get(f, math.nan))
            for f in folds}


def folds_reproducing(cand_fold: dict, ctrl_fold: dict) -> int:
    return sum(1 for f, (c, k) in _fold_pairs(cand_fold, ctrl_fold).items()
               if _same_sign_half(k, c))


def fold_pnl_by_fold(book, calendar, b1: str, b2: str) -> dict:
    """Fold PnL on the P-11 daily book series (sum of log slices)."""
    L = load_p0_lib()
    out = {"F1": 0.0, "F2": 0.0, "F3": 0.0}
    for d, x in zip(calendar, book.book_log):
        out[L.assign_fold(d, b1, b2)] += float(x)
    return out


def max_drawdown(book_log: np.ndarray) -> float:
    wealth = np.exp(np.cumsum(book_log))
    peak = np.maximum.accumulate(wealth)
    dd = 1.0 - wealth / peak
    return float(dd.max()) if dd.size else 0.0


def break_even_margin(book) -> dict:
    """Extra bps per fill that would zero the expectancy at this stress."""
    gross = _mean([lg.gross for lg in book.legs])
    if gross != gross:
        return {"break_even_bps_per_fill": math.nan, "margin_bps": math.nan}
    be = gross * 1e4 / 2.0
    L = load_p0_lib()
    if book.legs:
        avg_bps = _mean([L.BAND_BPS[lg.band] for lg in book.legs])
    else:
        avg_bps = math.nan
    return {"break_even_bps_per_fill": be,
            "operative_stress_bps_per_fill": avg_bps * book.stress,
            "margin_bps": be - avg_bps * book.stress}


# ---------------------------------------------------------------- kills

def k6_slow_drift(cand, delay, compl) -> dict:
    """K6 exact test as pinned in i_engine (disclosed deviation from
    'frozen at S'): per fold, pairs (candidate, C-DELAY-H) and
    (candidate, C-COMPLEMENT) are indistinguishable iff
    |E_x - E_y| <= SE_f (SE_f = std of candidate leg nets in fold,
    ddof=1 / sqrt(n_f); folds with < 2 candidate legs not counted).
    REJECT iff both pairs indistinguishable in >= 2/3 folds."""
    import statistics
    by_fold: dict[str, list[float]] = {}
    for lg in cand.legs:
        by_fold.setdefault(lg.fold, []).append(lg.net)
    counted = 0
    indist = 0
    detail = {}
    for f in sorted(set(by_fold) | set(cand.fold_expectancy)):
        nets = by_fold.get(f, [])
        if len(nets) < 2:
            detail[f] = {"counted": False, "reason": "fewer than 2 legs"}
            continue
        counted += 1
        se = statistics.stdev(nets) / math.sqrt(len(nets))
        e_c = cand.fold_expectancy.get(f, math.nan)
        d1 = abs(e_c - delay.fold_expectancy.get(f, math.nan))
        d2 = abs(e_c - compl.fold_expectancy.get(f, math.nan))
        pair = bool(d1 <= se and d2 <= se)
        indist += int(pair)
        detail[f] = {"counted": True, "se": se, "d_delay": d1,
                     "d_complement": d2, "indistinguishable": pair}
    reject = counted >= 1 and indist * 3 >= 2 * counted
    return {"rule": "K6", "reject": reject, "folds_counted": counted,
            "folds_indistinguishable": indist, "detail": detail,
            "test_status": "PINNED_AT_I_DEVIATION_DISCLOSED"}


def ordered_kills(bundle: dict, spy: NameData, calendar, b1: str, b2: str) -> dict:
    """The §6 ordered battery, first binding rule kills."""
    cand = bundle["candidate"]
    rows = []

    def bind(rule, why):
        rows.append({"rule": rule, "binding": True, "detail": why})
        return {"binding_rule": rule, "reject": True, "rows": rows,
                "verdict": f"REJECT_{rule}"}

    # R1 expectancy (stress 2.0 net)
    e_c = cand.expectancy
    rows.append({"rule": "R1", "binding": False,
                 "detail": {"net_expectancy_stress2": e_c,
                            "law": "net expectancy <= 0 at stress 2.0 -> REJECT_ALL"}})
    if not (e_c == e_c) or e_c <= 0.0:
        return bind("R1", {"net_expectancy_stress2": e_c})

    # R2 long-market reduction (unpopulated control -> NOT_ADJUDICABLE
    # for that comparator, never a free pass and never a silent skip)
    spy_legs = spy_legs_for(spy, cand.legs) if spy is not None else []
    e_market = _mean(spy_legs)
    e_random = bundle["c_random_timing"].expectancy
    comparators = {k: v for k, v in (("C-MARKET", e_market),
                                     ("C-RANDOM-TIMING", e_random))
                   if v == v}
    rows.append({"rule": "R2", "binding": False,
                 "detail": {"e_candidate": e_c, "e_cmarket": e_market,
                            "e_random_timing": e_random,
                            "populated_comparators": sorted(comparators)}})
    if comparators and e_c <= max(comparators.values()):
        return bind("R2", {"e_candidate": e_c,
                           "comparator": max(comparators, key=comparators.get),
                           "comparator_value": max(comparators.values())})
    if not comparators:
        rows[-1]["detail"]["disposition"] = (
            "both R2 comparators unpopulated -> NOT_ADJUDICABLE")

    # R3 mechanism specificity (C-COMPLEMENT)
    compl = bundle["c_complement"]
    n_repro = folds_reproducing(cand.fold_expectancy, compl.fold_expectancy)
    rows.append({"rule": "R3", "binding": False,
                 "detail": {"e_complement": compl.expectancy, "e_candidate": e_c,
                            "folds_reproducing_0.5x_same_sign": n_repro,
                            "not_adjudicable": len(compl.legs) == 0}})
    if len(compl.legs) == 0:
        rows[-1]["detail"]["disposition"] = (
            "C-COMPLEMENT unpopulated -> NOT_ADJUDICABLE, never silently "
            "skipped (plan §6 disposition rule)")
    else:
        if compl.expectancy > e_c or n_repro >= 2:
            return bind("R3", {"e_complement": compl.expectancy,
                               "folds_reproducing": n_repro})

    # R4 reversal reduction (C-REVERSAL-PLAIN, MANDATORY)
    rev = bundle["c_reversal_plain"]
    n_repro_r = folds_reproducing(cand.fold_expectancy, rev.fold_expectancy)
    rows.append({"rule": "R4", "binding": False,
                 "detail": {"e_reversal_plain": rev.expectancy,
                            "folds_reproducing_0.5x_same_sign": n_repro_r,
                            "not_adjudicable": len(rev.legs) == 0}})
    if len(rev.legs) == 0:
        rows[-1]["detail"]["disposition"] = (
            "C-REVERSAL-PLAIN unpopulated -> NOT_ADJUDICABLE (mandatory "
            "rule cannot pass on an empty control)")
    else:
        if rev.expectancy > e_c or n_repro_r >= 2:
            return bind("R4", {"e_reversal_plain": rev.expectancy,
                               "folds_reproducing": n_repro_r})

    # R5 component placebo (fail-closed union: fold rule OR full-sample)
    r5 = bundle["r5_component"]
    n_repro_5 = folds_reproducing(cand.fold_expectancy, r5.fold_expectancy)
    full_rep = _same_sign_half(r5.expectancy, e_c)
    rows.append({"rule": "R5", "binding": False,
                 "detail": {"e_component_only": r5.expectancy,
                            "folds_reproducing_0.5x_same_sign": n_repro_5,
                            "full_sample_0.5x_same_sign": full_rep,
                            "not_adjudicable": len(r5.legs) == 0,
                            "binding_form": "union(folds>=2/3, full-sample)",
                            "fold_rule_not_adjudicable":
                                len(cand.fold_expectancy) < 3}})
    if len(r5.legs) == 0:
        rows[-1]["detail"]["disposition"] = (
            "R5 component-only unpopulated -> NOT_ADJUDICABLE (manifest "
            "declares every family adjudicable; an empty book on real "
            "data is a disclosed anomaly, never an inferred PASS)")
    else:
        if n_repro_5 >= 2 or full_rep:
            return bind("R5", {"folds_reproducing": n_repro_5,
                               "full_sample": full_rep})

    # R6 clock geometry (C-RANDOM-TIMING; C-CAL-HIST extension)
    rnd = bundle["c_random_timing"]
    ch = bundle["c_cal_hist"]
    sub_floor = any(v["sub_floor"]
                    for rep in bundle["c_cal_hist_report"].values()
                    for v in rep.values())
    rows.append({"rule": "R6", "binding": False,
                 "detail": {"e_random_timing": rnd.expectancy,
                            "e_cal_hist": ch.expectancy,
                            "cal_hist_bucket_sub_floor": sub_floor}})
    if (rnd.expectancy == rnd.expectancy) and rnd.expectancy > e_c:
        return bind("R6", {"out_earner": "C-RANDOM-TIMING"})
    if sub_floor:
        rows[-1]["detail"]["disposition"] = (
            "C-CAL-HIST sub-floor bucket -> NOT_ADJUDICABLE and disclosed; "
            "R6 binds on C-RANDOM-TIMING only (plan §6)")
    elif (ch.expectancy == ch.expectancy) and ch.expectancy > e_c:
        return bind("R6", {"out_earner": "C-CAL-HIST"})

    # K6 slow-drift combination
    k6 = k6_slow_drift(cand, bundle["c_delay_h"], compl)
    rows.append({"rule": "K6", "binding": False, "detail": k6})
    if k6["reject"]:
        return bind("K6", k6)

    return {"binding_rule": None, "reject": False, "rows": rows,
            "verdict": "NO_KILL_THROUGH_K6"}


# ------------------------------------------------------------- stage A

def stage_a_gates(bundle: dict, spy: NameData, calendar, b1: str, b2: str,
                  cand=None) -> dict:
    """The frozen stocks Stage-A battery on a K6-surviving book."""
    cand = cand or bundle["candidate"]
    L = load_p0_lib()
    gates = {}

    pnl = fold_pnl_by_fold(cand, calendar, b1, b2)
    pos = {f: max(v, 0.0) for f, v in pnl.items()}
    tot_pos = sum(pos.values())
    fps = (max(pos.values()) / tot_pos) if tot_pos > 0 else math.nan
    gates["fold_positive_share"] = {
        "value": fps, "limit": CONCENTRATION_LIMIT,
        "pass": fps == fps and fps <= CONCENTRATION_LIMIT,
        "law": "fold-positive-share > 50% KILLS (V11 precedent 0.5034 FAILING)",
        "statistic": "largest positive fold share of total positive fold PnL (P-11)",
        "not_adjudicable": tot_pos <= 0.0}

    abs_pnl = {f: abs(v) for f, v in pnl.items()}
    tot_abs = sum(abs_pnl.values())
    conc = (max(abs_pnl.values()) / tot_abs) if tot_abs > 0 else math.nan
    gates["largest_fold_concentration"] = {
        "value": conc, "limit": CONCENTRATION_LIMIT,
        "pass": conc == conc and conc <= CONCENTRATION_LIMIT,
        "law": "largest-fold PnL concentration > 50% KILLS",
        "statistic": "max |fold PnL| / sum |fold PnL| (P-11)"}

    spy_legs = spy_legs_for(spy, cand.legs) if spy is not None else []
    by_fold: dict[str, list[float]] = {}
    for lg, s in zip(cand.legs, spy_legs):
        if s == s:
            by_fold.setdefault(lg.fold, []).append(lg.net - s)
    excess = {f: _mean(v) for f, v in sorted(by_fold.items())}
    n_pos = sum(1 for v in excess.values() if v > 0)
    gates["spy_excess_folds"] = {
        "per_fold": excess, "positive_folds": n_pos,
        "pass": n_pos >= 2,
        "law": "SPY-excess positive in >= 2/3 folds REQUIRED",
        "not_adjudicable": len(excess) < 3 or spy is None}

    mdd = max_drawdown(cand.book_log)
    gates["mdd"] = {"value": mdd, "limit": MDD_LIMIT, "pass": mdd <= MDD_LIMIT,
                    "law": "MDD <= 15% (P-11 daily book series)"}

    be = break_even_margin(cand)
    gates["stress_margin"] = {
        "net_expectancy_stress2": cand.expectancy,
        "break_even_bps_per_fill": be["break_even_bps_per_fill"],
        "margin_bps": be["margin_bps"],
        "pass": cand.expectancy == cand.expectancy and cand.expectancy > 0,
        "law": "stress-2.0 net positive with break-even margin"}

    drop_one = {}
    stable = True
    adjudicable = True
    for f in ("F1", "F2", "F3"):
        rest = [lg.net for lg in cand.legs if lg.fold != f]
        if not rest:
            drop_one[f] = "NOT_ADJUDICABLE (empty drop-one set)"
            adjudicable = False
            continue
        e_rest = _mean(rest)
        ok = cand.expectancy == cand.expectancy and \
            (e_rest > 0) == (cand.expectancy > 0)
        drop_one[f] = {"e_rest": e_rest, "sign_stable": ok}
        stable = stable and ok
    gates["drop_one_stability"] = {
        "per_fold": drop_one, "pass": stable and adjudicable,
        "not_adjudicable": not adjudicable,
        "law": "drop-one sign stability (all leave-one-fold-out sets)"}

    gates["pit_mutation"] = dict(bundle["pit_mutation"])
    gates["pit_mutation"]["pass"] = bool(bundle["pit_mutation"]["pass"])

    inc = include_censored_nets(cand)
    gates["death_censoring_accounting"] = {
        "censored_legs": len(cand.censored_legs),
        "kinds": sorted({lg.censored_kind for lg in cand.censored_legs
                         if lg.censored_kind}),
        "invariance_mode": "censored legs excluded from the numerator "
                           "(primary); included-at-marks rerun compared "
                           "in adjudicate_candidate (binds verdict AND gates)",
        "law": "BC-7 in full"}

    return {"gates": gates, "fold_pnl": pnl}


def _gate_summary(sa: dict) -> dict:
    out = {}
    for name, g in sa["gates"].items():
        if name in ("death_censoring_accounting",):
            continue
        out[name] = ("NOT_ADJUDICABLE" if g.get("not_adjudicable")
                     else "PASS" if g.get("pass") else "FAIL")
    return out


# ---------------------------------------------------------- full verdict

def adjudicate_candidate(bundle: dict, spy: NameData, calendar,
                         b1: str, b2: str) -> dict:
    """Ordered kills, then Stage-A, then the BC-7 invariance binding."""
    primary = ordered_kills(bundle, spy, calendar, b1, b2)
    result = {
        "config_id": bundle["cell"],
        "stress": STRESS_TIER,
        "primary": primary,
        "r0_status": R0_NOT_RUN_LABEL,
        "r0_verbatim": R0_NOT_RUN_VERBATIM,
        "pbo_status": PBO_NOT_RUN_LABEL,
        "pbo_verbatim": PBO_NOT_RUN_VERBATIM,
        "disclosure_section10": DISCLOSURE_SECTION10_VERBATIM,
        "budget": {"used": 0, "max": BUDGET_MAX_SCORED_CELLS,
                   "label": f"0/{BUDGET_MAX_SCORED_CELLS} (consumed only at scored E)"},
        "dsr": {"gate": "E_SCORED_ONLY", "n_grid": DSR_N_GRID,
                "alpha": DSR_ALPHA_RELAXED,
                "program": {"n": DSR_N_PROGRAM, "alpha": DSR_ALPHA_PROGRAM,
                            "role": "reported-only"}},
    }
    if primary["reject"]:
        result["verdict"] = primary["verdict"]
        result["stage_a"] = None
        # BC-7 invariance binds the VERDICT: rerun on censored-included
        # books and require the same binding rule.
        inv = _invariant_rerun(bundle, spy, calendar, b1, b2,
                               primary["binding_rule"])
        result["death_invariance"] = inv
        if inv["verdict_matches"] is False:
            result["verdict"] = "DEATH_CENSORING_COUPLED_UNBOOKABLE"
        return result

    sa = stage_a_gates(bundle, spy, calendar, b1, b2)
    summary = _gate_summary(sa)
    result["stage_a"] = {"gates": summary, "detail_fold_pnl": sa["fold_pnl"]}
    # invariance: gates AND verdict recomputed on censored-included books
    inv_bundle = dict(bundle)
    for key in ("candidate", "c_complement", "r5_component", "c_delay_h",
                "c_random_timing", "c_cal_hist", "c_reversal_plain"):
        inc = include_censored_nets(bundle[key])
        inv_bundle[key] = inc
    inv_kills = ordered_kills(inv_bundle, spy, calendar, b1, b2)
    inv_sa = stage_a_gates(inv_bundle, spy, calendar, b1, b2)
    inv_summary = _gate_summary(inv_sa)

    def _verdict_from_summary(s: dict, kills_rule) -> str:
        if kills_rule is not None:
            return f"REJECT_{kills_rule}"
        if any(v == "FAIL" for v in s.values()):
            return "STAGE_A_FAIL"
        if any(v == "NOT_ADJUDICABLE" for v in s.values()):
            # never an inferred PASS: the unpopulated/invalid control is
            # disclosed and the verdict stays non-bookable
            return "STAGE_A_NOT_ADJUDICABLE_DISCLOSED"
        return "PASS_I_STAGE_PENDING_DSR_E"

    v_primary = _verdict_from_summary(summary, None)
    v_inv = _verdict_from_summary(inv_summary, inv_kills["binding_rule"])
    matches = (v_inv == v_primary) and (summary == inv_summary)
    result["death_invariance"] = {
        "primary_stage_a": summary, "included_stage_a": inv_summary,
        "primary_kills_rule": primary["binding_rule"],
        "included_kills_rule": inv_kills["binding_rule"],
        "verdict_matches": matches,
        "law": "death-censoring invariance binds the verdict AND every "
               "Stage-A gate (BC-7; a coupled result is unbookable)"}
    if not matches:
        result["verdict"] = "DEATH_CENSORING_COUPLED_UNBOOKABLE"
    else:
        result["verdict"] = v_primary
        if v_primary == "PASS_I_STAGE_PENDING_DSR_E":
            result["dsr"]["binding_law"] = (
                "DSR (E[max SR], DSR_BAILEY_LOPEZDEPRADO_V1) gates BEFORE any "
                "survivor name is named; computed ONLY at the scored E run")
    return result


def _invariant_rerun(bundle: dict, spy: NameData, calendar,
                     b1: str, b2: str, primary_rule: str | None) -> dict:
    inv_bundle = dict(bundle)
    for key in ("candidate", "c_complement", "r5_component", "c_delay_h",
                "c_random_timing", "c_cal_hist", "c_reversal_plain"):
        inv_bundle[key] = include_censored_nets(bundle[key])
    inv = ordered_kills(inv_bundle, spy, calendar, b1, b2)
    return {"included_binding_rule": inv["binding_rule"],
            "primary_binding_rule": primary_rule,
            "verdict_matches": inv["binding_rule"] == primary_rule}


# ------------------------------------------------------------- DSR gate

def dsr_gate(per_period_log: np.ndarray, trial_sharpes, n_trials: int,
             alpha: float, allow_scored: bool = False) -> dict:
    """Bailey/Lopez de Prado DSR gate - computed ONLY at the scored E run.

    Refuses (NOT_RUN_E_ONLY) unless allow_scored is True, which happens
    exclusively on the GO-gated scored path.  Gating BEFORE any survivor
    name; pass iff DSR >= 1 - alpha.
    """
    if not allow_scored:
        return {"dsr": None, "status": "NOT_RUN_E_ONLY",
                "law": "computed only at the scored E run, gating BEFORE "
                       "any survivor name (plan §6; §8 claims law)"}
    from research.dsr import dsr_probability
    r = np.exp(np.asarray(per_period_log, dtype=float)) - 1.0
    if r.size < 2:
        return {"dsr": None, "status": "NOT_RUN_INSUFFICIENT_SAMPLE"}
    sr = float(np.mean(r) / np.std(r, ddof=1))
    skew = float(((r - r.mean()) ** 3).mean() / r.std(ddof=1) ** 3)
    kurt = float(((r - r.mean()) ** 4).mean() / r.std(ddof=1) ** 4)
    out = dsr_probability(sr, list(trial_sharpes), n_trials, int(r.size),
                          skew, kurt)
    out["alpha"] = alpha
    out["pass"] = (out["dsr"] is not None and out["dsr"] >= 1.0 - alpha)
    return out


# ------------------------------------------------------- P-11 persistence

def persist_series(path: Path, book) -> str:
    """Persist a book's P-11 daily series deterministically; returns sha256."""
    payload = {
        "schema": "stocks_search_v1_p11_series@1",
        "book_id": book.book_id,
        "config_id": book.config_id,
        "calendar": list(book.calendar),
        "book_log": [float(x) for x in book.book_log],
        "expectancy": book.expectancy,
        "fold_expectancy": book.fold_expectancy,
    }
    digest = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode("utf-8")).hexdigest()
    payload["sha256"] = digest
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    return digest


# --------------------------------------------------------- GO-gated loader

def load_real_data(go_phrase: str, cache_dir, retrieval_manifest_path,
                   max_names: int | None = None) -> dict:
    """THE scored-E data path.  Refuses any load without the EXACT owner
    GO phrase at this cycle's gate (P-8: early/paraphrased GO dies
    unconsumed).  With the exact phrase: verifies the frozen artifacts
    (S freeze sha + arm identities; p0_lib pin) and loads the death-
    inclusive priced cohort from the P0 raw cache, READ-ONLY, via the
    frozen p0_run parser."""
    if go_phrase != GO_PHRASE:
        raise GoGateRefused(
            "GO gate: the exact phrase 'GO STOCKS SEARCH V1 SCORED "
            "EXECUTION' was not presented; early or paraphrased GO dies "
            "unconsumed (P-8). No data is loaded.")
    verify_freeze()                      # FROZEN_SHA_MISMATCH on drift
    load_p0_lib()                        # p0_lib pin inside
    cache_dir = Path(cache_dir)
    if not cache_dir.exists():
        raise FileNotFoundError(
            f"raw cache dir not found: {cache_dir} (no cohort loaded)")
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "stocks_search_v1_p0_run", _RUN_DIR / "p0" / "p0_run.py")
    p0_run = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, p0_run)
    spec.loader.exec_module(p0_run)
    retrieval = json.loads(Path(retrieval_manifest_path).read_text())
    pulls = retrieval["pulls"]
    names = {}
    for sym in sorted(s for s, m in pulls.items() if m.get("status") == 200):
        parsed = p0_run.parse_name(cache_dir / f"{sym}.json.gz")
        if parsed is None:
            continue
        dates, o, h, lo, c, v, _mal = parsed
        names[sym] = NameData(sym, tuple(d[:10] for d in dates),
                              np.asarray(o, dtype=float),
                              np.asarray(h, dtype=float),
                              np.asarray(lo, dtype=float),
                              np.asarray(c, dtype=float),
                              np.asarray(v, dtype=float))
        if max_names is not None and len(names) >= max_names:
            break
    if not names:
        raise FileNotFoundError("no served names parsed from the cache")
    return {"names": names, "retrieval_manifest": retrieval,
            "go_phrase_state": "CONSUMED_AT_GATE (exact phrase presented)"}


# ------------------------------------------------------- bundle assembly

def run_candidate_adjudication(names: dict, config_id: str, calendar,
                               b1: str, b2: str, spy: NameData,
                               stress: float = STRESS_TIER) -> dict:
    """I-lane dry-run path: build all books for one frozen cell and
    adjudicate.  SYNTHETIC/sanitized inputs only in this lane; real runs
    go through load_real_data at E under the owner GO."""
    from i_engine import build_all_books
    cell = CELL_BY_ID[config_id]
    bundle = build_all_books(names, cell, calendar, b1, b2, stress)
    report = adjudicate_candidate(bundle, spy, calendar, b1, b2)
    report["cells_remaining"] = [c for c in CELL_IDS if c != config_id]
    return report
