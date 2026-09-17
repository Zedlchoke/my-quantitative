#!/usr/bin/env python
"""FOREX-SEARCH-V1 I-lane adjudication harness (lane fsearch-i).

Wires the §6 ordered kill rules and Stage-A gates over the books built by
i_engine.py, for the three frozen S-selected arms. The harness is PURE:
it consumes books/series given to it (from the engine on synthetic or,
after the owner GO, real data) and produces verdict dicts. It performs NO
real-data execution and computes NO scored output in this lane.

Rules implemented (§6 order, first binding kills):
  R1 net expectancy > 0 at stress 2.0 (conservatively-financed book)
  R2 PF >= 1.10 AND fold positivity AND per-state per-fold floor >= 10
  R3 CTL-COMPLEMENT out-earn/match/self-fail kills; degenerate complement
     NOT_RUN both ways (never an inferred PASS)
  R4 trend-only reproduction >= 0.5x same-sign >= 2/3 folds
     (CLOCK-COND: NOT_ADJUDICABLE per the frozen D1 manifest)
  R5 CLOCK-ONLY out-earn OR fired-census weekday share > 0.35
  R6 USD-drift per-leg AND pooled <= 0.20; DGS10/real-yield/curve/carry/
     SPY shadow reproduction >= 0.5x same-sign (injected shadows;
     absent -> NOT_RUN, kill-only, never a rescue)
  K6 slow-drift combination {fresh, delayed} x {state, complement}
     mutually indistinguishable within fold noise -> REJECT. The exact
     test was NOT frozen at S in this cycle, so absent an injected exact
     test the disposition is NOT_ADJUDICABLE (fail-closed, disclosed on
     every output; never an inferred PASS).
  dual-books sign invariance; P-20 books-distinct re-check; Stage-A
  (fold-positive-share > 50% required, concentration <= 50%, MDD <= 15%,
  stress margin + break-even bps, drop-one stability, C-PIT-MUTATION,
  P-11 per-period series persistence, DSR deflated Sharpe at
  N = frozen grid size 33 / alpha 0.10 owner-relaxed — GATING;
  program-cumulative N=260 / alpha 0.05 reported, never gating);
  explicit scored-cell budget counter (F-8); PBO NOT_RUN disposition;
  R0 NOT_RUN labeling on EVERY output.

F-2 remediation (A7 a7_prelaunch_forex_search_v1.json): the terminal
survivor outcome name FOREX_SEARCH_V1_SURVIVORS_UNDER_RELAXED_BATTERY_...
is emitted ONLY after the DSR gate has COMPUTED (and passed) on every
survivor; without a computed DSR the cycle is INCOMPLETE_NOT_PROMOTABLE.
The Stage-A battery executes only at the scored E run behind the exact
owner GO phrase; every number in this lane's tests is a synthetic fixture.

Disclosures printed verbatim on every output (§3, §3b, §4 F4, §6).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

import i_engine as eng

# ------------------------------------------------------------------ labels

R0_NOT_RUN = ("R0 NOT_RUN (D2 skipped per owner amendment §3b) | standing "
              "per-leg AND pooled |rho| <= 0.20; owner-relaxed 0.30 | "
              "terminal names carry R0_NOT_RUN")
PBO_NOT_RUN = ("PBO NOT_RUN fail-closed by construction (<=3 scored cells; "
               "CSCV PBO needs >= 8 performance-evaluated configs; "
               "d0992d17df8e2dfde57c9a0806a5798f14021a4f class)")
RELAXATION_DISCLOSURE = ("accepted under owner-relaxed acceptance battery "
                         "(R0 0.30 / DSR alpha 0.10 at N = grid) | PBO "
                         "NOT_RUN fail-closed (<=3 cells, d0992d17 class) "
                         "| R0 NOT_RUN (D2 skipped by owner amendment §3b)")
FINANCING_DISCLOSURE = ("financing = stated-conservative nightly-average "
                        "extrapolation (1.7 bps; worst single night may "
                        "exceed it; no per-leg differential census exists "
                        "— OHLC-only source)")
CLOCK_ONLY_DECLARATION = (
    "CLOCK-ONLY book declared by this harness (the D1 manifest pins no "
    "clock-only book): rotation on the same daily decision clock with NO "
    "signal input — +1 every session per leg after the arm's own warmup, "
    "under the identical force-flat/execution gating and cost/financing "
    "ladder. Declaration printed on every R5 output.")
K6_DECLARATION = (
    "K6 slow-drift combination (NG5/stocks-search lineage): {candidate, "
    "delayed} x {state, complement} mutually indistinguishable within "
    "fold noise -> REJECT. The exact test was NOT frozen at S in this "
    "cycle; absent an injected exact test the disposition is "
    "NOT_ADJUDICABLE fail-closed, never an inferred PASS.")
FOLD_POSITIVE_SHARE_LAW = (
    "Stage-A fold-positive-share: the share of the three frozen folds with "
    "positive financed stress-2.0 net MUST EXCEED 50%; at or below 50% the "
    "arm is killed (the '> 50% kills' phrasing of the frozen battery).")
SHADOW_LINEAGES = ["DGS10-LEVEL", "REAL-YIELD", "CURVE", "CARRY",
                   "SPY-RISK-OFF"]
# F-2 (§6 Stage-A): DSR constants frozen by the D1 manifest / plan §3 + §5.
DSR_FROZEN_GRID_N = 33          # §5: frozen grid size = DSR deflation set N
DSR_ALPHA = 0.10                # §3: owner-relaxed DSR alpha (GATING)
DSR_PROGRAM_CUMULATIVE_N = 260  # §6 P-9 program-cumulative count (REPORTED)
DSR_PROGRAM_ALPHA = 0.05        # standing program alpha (REPORTED)
EULER_GAMMA = 0.5772156649015329
# F-8: explicit scored-cell budget counter (plan §0: 3 scored cells max).
SCORED_CELL_BUDGET_MAX = 3
DSR_LAW = (
    "DSR (Bailey & López de Prado 2014) gates Stage-A: DSR = Phi((SR - SR0) "
    "sqrt(T-1) / sqrt(1 - g3*SR + ((g4-1)/4)*SR^2)) >= 1 - alpha with "
    "N = frozen grid size 33 (§5) and alpha = 0.10 owner-relaxed (§3); "
    "SR0 = E[max SR] over N unit-variance standard-normal trials "
    "(conservative convention, documented: the D1 freeze is outcome-blind, "
    "so the other N-1 configurations' SR variance does not exist before "
    "the scored run); SR is per-period on the persisted P-11 series "
    "(financed stress-primary net returns over the frozen master calendar, "
    "flat sessions contribute 0.0). Program-cumulative N=260 (P-9) at "
    "alpha 0.05 is computed on the same series and REPORTED, never "
    "gating (§6).")
P11_LAW = (
    "P-11: the per-period (per-session) financed stress-primary net bps "
    "series on the frozen master calendar is PERSISTED inside this verdict "
    "(and may be re-written via persist_p11_series at the scored E run) so "
    "the DSR computation is reproducible without re-execution.")


def verdict_labels() -> dict:
    """The fail-closed labels carried on EVERY harness output."""
    return {
        "r0_ancestry": "NOT_RUN",
        "r0_not_run_verbatim": R0_NOT_RUN,
        "pbo": "NOT_RUN",
        "pbo_not_run_verbatim": PBO_NOT_RUN,
        "relaxation_disclosure_verbatim": RELAXATION_DISCLOSURE,
        "financing_disclosure_verbatim": FINANCING_DISCLOSURE,
        "d2": "SKIPPED per owner amendment §3b",
        "no_scored_output_this_lane": True,
    }


# ------------------------------------------------------------------ helpers

def book_nets(trades: list, stress: float):
    price, financed = eng.ladder_bps(trades, stress)
    return price, financed


def fold_nets(trades: list, stress: float, folds: dict) -> dict:
    price, financed = book_nets(trades, stress)
    out = {}
    for f in (1, 2, 3):
        idx = [i for i, t in enumerate(trades) if t["fold"] == f]
        out[str(f)] = float(financed[idx].sum()) if idx else 0.0
    _ = folds, price
    return out


def financed_expectancy(trades: list, stress: float) -> float | None:
    if not trades:
        return None
    _, financed = book_nets(trades, stress)
    return float(financed.mean())


def total_net(trades: list, stress: float) -> float:
    _, financed = book_nets(trades, stress)
    return float(financed.sum())


def _row(rule: str, verdict: str, detail) -> dict:
    return {"rule": rule, "verdict": verdict, "detail": detail}


# ------------------------------------------------------------------- rules

def r1_expectancy(ctx: dict) -> dict:
    exp_ = financed_expectancy(ctx["trades"], ctx["stress"])
    if exp_ is None:
        return _row("R1", "NOT_RUN",
                    "no fired decisions in the book — expectancy "
                    "unmeasurable, fail-closed (never an inferred PASS)")
    verdict = "PASS" if exp_ > 0.0 else "KILL"
    return _row("R1", verdict,
                {"metric": "fin-adj net expectancy bps (financed, stress "
                           f"{ctx['stress']})",
                 "value": exp_,
                 "bar": "strictly > 0 (NOT relaxed)"})


def r2_robustness(ctx: dict) -> dict:
    if not ctx["trades"]:
        return _row("R2", "NOT_RUN", "empty book — unmeasurable, fail-closed")
    summ = eng.summarize_book(eng.ladder_bps(ctx["trades"], ctx["stress"])[1],
                              ctx["trades"])
    pf = summ["profit_factor"]
    pf_pass = pf is not None and pf >= 1.10
    fold_pos = {f: n > 0.0 for f, n in summ["per_fold_net_bps"].items()}
    missing_folds = [str(f) for f in (1, 2, 3)
                     if str(f) not in summ["per_fold_net_bps"]]
    fold_positivity = all(fold_pos.values()) and not missing_folds
    counts = eng.substate_counts(ctx["trades"])
    floor_fail = {}
    for f in (1, 2, 3):
        got = counts.get(str(f), {})
        bad = {k: v for k, v in got.items()
               if v < eng.R2_PER_STATE_PER_FOLD_FLOOR}
        if bad or not got:
            floor_fail[str(f)] = {"counts": got, "below_floor": bad,
                                  "floor": eng.R2_PER_STATE_PER_FOLD_FLOOR}
    floor_pass = not floor_fail
    verdict = "PASS" if (pf_pass and fold_positivity and floor_pass) else "KILL"
    return _row("R2", verdict,
                {"profit_factor": pf, "pf_bar": 1.10, "pf_pass": pf_pass,
                 "per_fold_net_bps": summ["per_fold_net_bps"],
                 "fold_positivity": fold_positivity,
                 "missing_folds": missing_folds,
                 "per_state_per_fold_counts": counts,
                 "per_state_per_fold_floor": eng.R2_PER_STATE_PER_FOLD_FLOOR,
                 "floor_failures": floor_fail,
                 "floor_pass": floor_pass})


def r3_mechanism(ctx: dict) -> dict:
    cand = total_net(ctx["trades"], ctx["stress"])
    comp_trades = ctx["complement_trades"]
    if not comp_trades:
        return _row("R3", "NOT_RUN",
                    "degenerate (empty or sub-floor) CTL-COMPLEMENT — "
                    "NOT_RUN both ways, never an inferred PASS (§6 R3)")
    counts = eng.substate_counts(comp_trades)
    subfloor = any(v < eng.R2_PER_STATE_PER_FOLD_FLOOR
                   for f in counts.values() for v in f.values()) or \
        len(counts) < 3
    if subfloor:
        return _row("R3", "NOT_RUN",
                    "degenerate (sub-floor population) CTL-COMPLEMENT — "
                    "NOT_RUN both ways, never an inferred PASS (§6 R3)")
    comp = total_net(comp_trades, ctx["stress"])
    if comp >= cand or comp < 0.0:
        return _row("R3", "KILL",
                    {"candidate_net_bps": cand, "complement_net_bps": comp,
                     "law": "out-earn/match kills (tie kills); a "
                            "self-failing complement still kills (V15)"})
    return _row("R3", "PASS", {"candidate_net_bps": cand,
                               "complement_net_bps": comp})


def _reproduction_folds(cand_fold: dict, shadow_fold: dict) -> list:
    rep = []
    for f in (1, 2, 3):
        c = cand_fold.get(str(f))
        s = shadow_fold.get(str(f))
        if c is None or s is None or c == 0.0:
            continue
        if np.sign(s) == np.sign(c) and abs(s) >= 0.5 * abs(c):
            rep.append(f)
    return rep


def r4_trend_reduction(ctx: dict) -> dict:
    if ctx["config_id"] == "FSS-CLOCK-COND-MONTHPOS-SECOND-LONG":
        return _row("R4", "NOT_ADJUDICABLE",
                    "no trend/vol conditioning-variable analog exists for "
                    "CLOCK-COND (frozen D1 manifest r4_trend_only_book); "
                    "disclosed, never an inferred PASS (§6 R4)")
    cand_trades = ctx["trades"]
    to_trades = ctx.get("trend_only_trades")
    if not cand_trades or not to_trades:
        return _row("R4", "NOT_RUN",
                    "empty candidate or trend-only book — unmeasurable, "
                    "fail-closed")
    cand_fold = fold_nets(cand_trades, ctx["stress"], ctx["folds"])
    to_fold = fold_nets(to_trades, ctx["stress"], ctx["folds"])
    rep = _reproduction_folds(cand_fold, to_fold)
    detail = {"trend_only_book": ctx["trend_only_definition"],
              "candidate_fold_net_bps": cand_fold,
              "trend_only_fold_net_bps": to_fold,
              "reproduced_folds": rep,
              "bar": ">= 0.5x same-sign in >= 2/3 folds -> REJECT"}
    verdict = "KILL" if len(rep) >= 2 else "PASS"
    extra = []
    vol_reg = ctx.get("vol_regime_shadow_trades")
    if vol_reg is not None:
        vr_fold = fold_nets(vol_reg, ctx["stress"], ctx["folds"])
        vr_rep = _reproduction_folds(cand_fold, vr_fold)
        extra.append({"shadow": "VOL-REGIME", "fold_nets": vr_fold,
                      "reproduced_folds": vr_rep})
        if len(vr_rep) >= 2:
            verdict = "KILL"
    detail["vol_regime_shadow"] = extra
    return _row("R4", verdict, detail)


def r5_clock_geometry(ctx: dict) -> dict:
    if not ctx["trades"]:
        return _row("R5", "NOT_RUN", "empty book — unmeasurable, fail-closed")
    cand = total_net(ctx["trades"], ctx["stress"])
    co_trades = ctx.get("clock_only_trades")
    out_earn = None
    if co_trades:
        co = total_net(co_trades, ctx["stress"])
        out_earn = co >= cand
    census = ctx["weekday_census"]
    share_breach = census["max_weekday_share"] > eng.R5_MAX_WEEKDAY_SHARE_FLOOR
    verdict = "KILL" if ((out_earn is True) or share_breach) else "PASS"
    return _row("R5", verdict,
                {"candidate_net_bps": cand,
                 "clock_only_net_bps": (total_net(co_trades, ctx["stress"])
                                        if co_trades else None),
                 "clock_only_out_earns": out_earn,
                 "clock_only_declaration": CLOCK_ONLY_DECLARATION,
                 "fired_census_weekday": census,
                 "weekday_share_floor": eng.R5_MAX_WEEKDAY_SHARE_FLOOR,
                 "weekday_share_breach": share_breach})


def r6_usd_macro(ctx: dict) -> dict:
    usd = ctx.get("usd")
    if not usd:
        return _row("R6", "NOT_RUN",
                    "USD-drift series not provided — the per-leg AND "
                    "pooled law is NOT satisfiable from books alone; "
                    "NOT_RUN (never pooled-only PASS)")
    per_leg = usd.get("per_leg_corr", {})
    pooled = usd.get("pooled_corr")
    unmeasurable = [k for k, v in per_leg.items() if v is None] + \
        (["pooled"] if pooled is None else [])
    if unmeasurable:
        return _row("R6", "NOT_ADJUDICABLE",
                    {"unmeasurable": unmeasurable,
                     "law": "per-leg AND pooled both required; pooled-only "
                            "DILUTES and is NOT_RUN, never PASS"})
    breaches = {k: v for k, v in per_leg.items() if abs(v) > eng.R6_USD_DRIFT_BAR}
    pooled_breach = abs(pooled) > eng.R6_USD_DRIFT_BAR
    verdict = "KILL" if (breaches or pooled_breach) else "PASS"
    detail = {"per_leg_corr": per_leg, "pooled_corr": pooled,
              "bar": eng.R6_USD_DRIFT_BAR,
              "standing_bar_note": "0.20 standing value; NOT relaxed",
              "per_leg_breaches": breaches,
              "pooled_breach": pooled_breach}
    shadows = []
    cand_net = total_net(ctx["trades"], ctx["stress"])
    for name in SHADOW_LINEAGES:
        sh = (ctx.get("shadows") or {}).get(name)
        if not sh:
            shadows.append({"shadow": name, "disposition": "NOT_RUN",
                            "note": "kill-only control not provided; may "
                                    "never rescue (§6 scoping rule)"})
            continue
        sh_net = float(sh.get("net_bps", 0.0))
        item = {"shadow": name, "net_bps": sh_net,
                "fold_nets": sh.get("fold_net_bps", {}),
                "bar": ">= 0.5x same-sign -> REJECT"}
        reproduces = (cand_net != 0.0 and
                      np.sign(sh_net) == np.sign(cand_net) and
                      abs(sh_net) >= 0.5 * abs(cand_net))
        if reproduces:
            item["disposition"] = "REJECT"
            verdict = "KILL"
        else:
            item["disposition"] = "NO_REPRODUCTION"
        shadows.append(item)
    detail["macro_shadows"] = shadows
    return _row("R6", verdict, detail)


def k6_slow_drift(ctx: dict, exact_test=None) -> dict:
    """Four books {candidate, delayed} x {state, complement}; verdict per
    the lineage combination rule. exact_test(fresh_state_fold_nets,
    delayed_state_fold_nets, fresh_complement_fold_nets,
    delayed_complement_fold_nets) -> bool 'all four mutually
    indistinguishable' must be frozen before it may kill."""
    fs = ctx.get("k6_fold_nets")
    if not fs:
        return _row("K6", "NOT_ADJUDICABLE",
                    {"declaration": K6_DECLARATION,
                     "fold_nets": None,
                     "exact_test": "NOT_FROZEN_AT_S"})
    indistinguishable = None
    if exact_test is not None:
        indistinguishable = bool(exact_test(
            fs["fresh_state"], fs["delayed_state"],
            fs["fresh_complement"], fs["delayed_complement"]))
    if indistinguishable is True:
        return _row("K6", "KILL",
                    {"declaration": K6_DECLARATION, "fold_nets": fs,
                     "exact_test": "injected (frozen)"})
    if indistinguishable is False:
        return _row("K6", "PASS",
                    {"declaration": K6_DECLARATION, "fold_nets": fs,
                     "exact_test": "injected (frozen)"})
    return _row("K6", "NOT_ADJUDICABLE",
                {"declaration": K6_DECLARATION, "fold_nets": fs,
                 "exact_test": "NOT_FROZEN_AT_S"})


def dual_books_rule(ctx: dict) -> dict:
    chk = eng.dual_books_check(ctx["trades"], ctx["stress"])
    return _row("DUAL-BOOKS", "PASS" if chk["pass"] else "KILL", chk)


def p20_recheck(positions_by_arm: dict, legs_order: list,
                frozen_matrix=None, tol: float = 1e-9) -> dict:
    """P-20 books-distinct re-check among the three arms from the REBUILT
    series; pairwise pooled |rho| <= 0.98 required; equality with the
    frozen S matrix verified within tol when both measurable."""
    ids = sorted(positions_by_arm)
    rows = []
    fail = False
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            rho, status = eng.p20_pooled_rho(positions_by_arm[a],
                                             positions_by_arm[b], legs_order)
            row = {"arm_a": a, "arm_b": b}
            if status != "OK":
                row.update({"pooled_rho": None, "status": status,
                            "books_distinct": False})
                fail = True
            else:
                distinct = abs(rho) <= eng.P20_BOOKS_DISTINCT_BAR
                row.update({"pooled_rho": rho,
                            "abs": abs(rho),
                            "threshold": eng.P20_BOOKS_DISTINCT_BAR,
                            "books_distinct": bool(distinct)})
                if not distinct:
                    fail = True
                if frozen_matrix:
                    fr = next((r for r in frozen_matrix
                               if {r["arm_a"], r["arm_b"]} == {a, b}), None)
                    if fr is not None and \
                            abs(rho - fr["pooled_rho"]) > 1e-9:
                        row["frozen_mismatch"] = True
                        fail = True
            rows.append(row)
    verdict = "PASS" if not fail else \
        ("NOT_ADJUDICABLE" if any(r.get("status") for r in rows) else "KILL")
    return {"rule": "P-20-RECHECK", "verdict": verdict, "detail": rows}


# ------------------------------------------------------- Stage-A DSR / P-11

def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    """Inverse standard normal CDF; deterministic bisection to 1e-12
    (stdlib only — the harness stays scipy-free and reproducible)."""
    if not 0.0 < p < 1.0:
        raise ValueError("probability out of range")
    lo, hi = -40.0, 40.0
    while hi - lo > 1e-12:
        mid = 0.5 * (lo + hi)
        if _norm_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def expected_max_sharpe(n_trials: int) -> float:
    """E[max SR] over N independent trials (Bailey & López de Prado 2014,
    'The Deflated Sharpe Ratio'): SR0 = (1 - gamma) Z(1 - 1/N) +
    gamma Z(1 - 1/(N e)) with gamma the Euler-Mascheroni constant, for
    unit-variance standard-normal trial SRs. Deterministic pure function
    of N."""
    z1 = _norm_ppf(1.0 - 1.0 / float(n_trials))
    z2 = _norm_ppf(1.0 - 1.0 / (float(n_trials) * math.e))
    return (1.0 - EULER_GAMMA) * z1 + EULER_GAMMA * z2


def deflated_sharpe_ratio(returns, n_trials: int) -> dict:
    """Bailey & López de Prado (2014) DSR from the candidate's per-period
    returns and the trial count N — deterministic, documented:

        DSR = Phi( (SR - SR0) sqrt(T - 1)
                   / sqrt(1 - g3 SR + ((g4 - 1)/4) SR^2) )

    with SR the per-period Sharpe, T the number of periods, g3/g4 the
    skewness/kurtosis of the per-period returns and SR0 = E[max SR]."""
    r = np.asarray(returns, dtype=np.float64)
    if r.size < 2:
        return {"computed": False,
                "reason": "UNMEASURABLE: fewer than 2 per-period returns"}
    sd = float(np.std(r, ddof=1))
    if sd == 0.0:
        return {"computed": False,
                "reason": "UNMEASURABLE: zero per-period variance"}
    sr = float(np.mean(r)) / sd
    z = (r - float(np.mean(r))) / sd
    g3 = float(np.mean(z ** 3))
    g4 = float(np.mean(z ** 4))
    denom_sq = 1.0 - g3 * sr + ((g4 - 1.0) / 4.0) * sr * sr
    denom = math.sqrt(denom_sq) if denom_sq > 0.0 else 1e-300
    sr0 = expected_max_sharpe(n_trials)
    stat = ((sr - sr0) * math.sqrt(r.size - 1)) / denom
    return {"computed": True, "n_trials": n_trials, "n_periods": int(r.size),
            "sr_per_period": sr, "sr0_expected_max": sr0,
            "skewness": g3, "kurtosis": g4, "psr_stat": stat,
            "dsr_probability": _norm_cdf(stat)}


def p11_per_period_series(ctx: dict) -> dict:
    """P-11: the per-period (per-session) financed stress-primary net bps
    series on the frozen master calendar, built from the arm's own trades
    and persisted inside the verdict dict (P11_LAW)."""
    trades = ctx["trades"]
    if not trades:
        return {"computed": False,
                "reason": "empty book — no per-period series exists",
                "n_periods": 0, "n_active_periods": 0, "series": [],
                "per_period_returns": [], "series_digest": None}
    _, financed = book_nets(trades, ctx["stress"])
    daily = eng.daily_pnl_series(trades, financed, ctx["master"])
    return {
        "computed": True,
        "convention": ("per decision session on the frozen master calendar; "
                       "financed stress-primary net bps; flat sessions "
                       "contribute 0.0"),
        "n_periods": int(daily.size),
        "n_active_periods": int(np.count_nonzero(daily)),
        "series": [{"date": d, "financed_net_bps": round(float(x), 12)}
                   for d, x in zip(ctx["master"], daily)],
        "per_period_returns": [float(x) / 1e4 for x in daily],
        "series_digest": eng.sha256_obj(
            {"master": list(ctx["master"]),
             "daily_bps": [float(x) for x in daily]}),
    }


def persist_p11_series(arm_verdicts: list, out_path) -> str:
    """Write the persisted P-11 series of the given arm verdicts to
    out_path (the scored E runner calls this after the owner GO). Returns
    the file sha256."""
    payload = {"schema": "fsearch_p11_per_period_series@1",
               "law": P11_LAW,
               "arms": {a["config_id"]: a["stage_a"]["subgates"]
                        ["p11_per_period_series"]["series_persisted"]
                        for a in arm_verdicts}}
    blob = json.dumps(payload, indent=1, sort_keys=True) + "\n"
    Path(out_path).write_text(blob)
    import hashlib
    return hashlib.sha256(blob.encode()).hexdigest()


def dsr_gate(p11: dict, n_trials: int, alpha: float) -> dict:
    """The Stage-A DSR subgate, computed on the persisted P-11 per-period
    returns: pass = computed AND dsr_probability >= 1 - alpha (fail-closed:
    an uncomputable DSR never passes)."""
    row = {"n_trials": n_trials, "alpha": alpha, "bar": 1.0 - alpha,
           "law": DSR_LAW}
    if not p11.get("computed"):
        row.update({"computed": False,
                    "reason": p11.get("reason", "P-11 series unavailable"),
                    "pass": False})
        return row
    res = deflated_sharpe_ratio(p11["per_period_returns"], n_trials)
    if not res["computed"]:
        res.update({"n_trials": n_trials, "alpha": alpha, "bar": 1.0 - alpha,
                    "pass": False, "law": DSR_LAW})
        return res
    res.update({"alpha": alpha, "bar": 1.0 - alpha,
                "pass": bool(res["dsr_probability"] >= 1.0 - alpha),
                "law": DSR_LAW})
    return res


def stage_a(ctx: dict) -> dict:
    """Frozen forex Stage-A gates on a survivor (all must hold)."""
    out = {"rule": "STAGE-A", "subgates": {}, "verdict": "PASS"}
    trades = ctx["trades"]
    stress = ctx["stress"]
    if not trades:
        out["verdict"] = "NOT_RUN"
        out["subgates"]["empty_book"] = "NOT_RUN fail-closed"
        return out
    _, financed = book_nets(trades, stress)
    summ = eng.summarize_book(financed, trades)
    per_fold = summ["per_fold_net_bps"]
    n_pos = sum(1 for f in (1, 2, 3) if per_fold.get(str(f), 0.0) > 0.0)
    share = n_pos / 3.0
    fps_pass = share > 0.5
    out["subgates"]["fold_positive_share"] = {
        "share": share, "per_fold_net_bps": per_fold,
        "law": FOLD_POSITIVE_SHARE_LAW, "pass": fps_pass}
    total = summ["net_bps"]
    conc = None
    if total > 0:
        conc = max(per_fold.values()) / total
    conc_pass = conc is not None and conc <= 0.5
    legs_share = {}
    by_leg = {}
    for t, b in zip(trades, financed):
        by_leg.setdefault(t["leg"], 0.0)
        by_leg[t["leg"]] += float(b)
    if total > 0:
        legs_share = {k: v / total for k, v in by_leg.items()}
    out["subgates"]["concentration"] = {
        "largest_fold_share": conc, "bar": "<= 0.50",
        "largest_leg_share_disclosure": legs_share, "pass": conc_pass}
    daily = eng.daily_pnl_series(trades, financed, ctx["master"])
    mdd = eng.max_drawdown_frac(daily)
    mdd_pass = mdd <= 0.15
    out["subgates"]["mdd"] = {"max_drawdown_frac": mdd, "bar": "<= 0.15",
                              "pass": mdd_pass}
    gross_mean = float(np.mean([t["gross_bps"] for t in trades]))
    margin = gross_mean - eng.WORST_CASE_ROUND_TRIP_BPS
    margin_pass = margin > 0.0
    out["subgates"]["stress_margin"] = {
        "mean_gross_bps_per_round_trip": gross_mean,
        "break_even_bps_per_round_trip": eng.WORST_CASE_ROUND_TRIP_BPS,
        "margin_bps": margin,
        "note": "margin > 0 is equivalent to R1 at stress 2.0 "
                "(2x1.5x2.0 + 1.7x2.0 = 9.4 bps)",
        "pass": margin_pass}
    drops = {}
    drop_pass = True
    drop_adjudicable = True
    legs_with_trades = sorted({t["leg"] for t in trades})
    for lg in legs_with_trades:
        rest = [t for t in trades if t["leg"] != lg]
        if not rest:
            drops[lg] = {"remaining_expectancy_bps": None,
                         "note": "drop leaves an empty book — drop-one "
                                 "NOT_ADJUDICABLE fail-closed"}
            drop_adjudicable = False
            continue
        _, fin_rest = book_nets(rest, stress)
        e = float(fin_rest.mean())
        drops[lg] = {"remaining_expectancy_bps": e}
        if e <= 0.0:
            drop_pass = False
    out["subgates"]["drop_one"] = {"per_leg": drops,
                                   "adjudicable": drop_adjudicable,
                                   "pass": drop_pass and drop_adjudicable}
    mut = ctx.get("mutated_positions")
    if mut is None or any(t["leg"] not in mut for t in trades):
        out["subgates"]["pit_mutation"] = {
            "pass": False, "note": "mutated book not provided (or missing "
                                   "a traded leg) — NOT_RUN fail-closed"}
        out["verdict"] = "KILL"
        return out
    breaches = []
    for t in trades:
        lg, mi, side = t["leg"], t["mi_decision"], t["side"]
        if int(mut[lg][mi]) == side:
            breaches.append({"leg": lg, "mi": mi})
    pit_pass = not breaches
    out["subgates"]["pit_mutation"] = {
        "pass": pit_pass, "breaches": breaches[:20],
        "breach_count": len(breaches),
        "law": "one-bar-earlier recomputation must change or refuse the "
               "book on EVERY fired decision (§6 C-PIT-MUTATION)"}
    # F-2 remediation: P-11 persistence + DSR are Stage-A members (§6,
    # "per-period series persisted (P-11) for DSR with N = frozen grid size
    # at alpha 0.10"). DSR at N=33/alpha 0.10 GATES; the program-cumulative
    # N=260 / alpha 0.05 DSR is computed on the same series and REPORTED
    # only (never gating).
    p11 = p11_per_period_series(ctx)
    p11_pass = bool(p11["computed"]) and p11["n_periods"] > 1
    out["subgates"]["p11_per_period_series"] = {
        "computed": p11["computed"],
        "reason": p11.get("reason"),
        "convention": p11.get("convention"),
        "n_periods": p11["n_periods"],
        "n_active_periods": p11["n_active_periods"],
        "series_digest": p11["series_digest"],
        "series_persisted": p11["series"],
        "law": P11_LAW,
        "pass": p11_pass}
    dsr = dsr_gate(p11, n_trials=DSR_FROZEN_GRID_N, alpha=DSR_ALPHA)
    dsr["reported_program_cumulative"] = dsr_gate(
        p11, n_trials=DSR_PROGRAM_CUMULATIVE_N, alpha=DSR_PROGRAM_ALPHA)
    dsr["reported_program_cumulative"]["role"] = (
        "REPORTED ONLY — never gating (§6: program-cumulative ~260 (P-9) "
        "at alpha 0.05, reported not gating)")
    out["subgates"]["dsr"] = dsr
    dsr_pass = bool(dsr.get("computed")) and bool(dsr.get("pass"))
    if not all([fps_pass, conc_pass, mdd_pass, margin_pass, drop_pass,
                drop_adjudicable, pit_pass, p11_pass, dsr_pass]):
        out["verdict"] = "KILL"
    return out


# ------------------------------------------------------------- adjudication

KILL_ORDER = ["R1", "R2", "R3", "R4", "R5", "R6", "K6"]


def adjudicate_arm(ctx: dict, k6_exact_test=None) -> dict:
    """Ordered battery for one arm. First binding kill stops the ordered
    rules (later rows NOT_EVALUATED); the structural gates (dual-books,
    P-20 re-check inputs) and labels always reported. Stage-A applies to
    ordered-battery survivors only."""
    rows = []
    killed_by = None
    for rule in KILL_ORDER:
        if killed_by is not None:
            rows.append(_row(rule, "NOT_EVALUATED",
                             "first-binding kill already recorded at "
                             f"{killed_by} (§6 ordered kills)"))
            continue
        if rule == "R1":
            row = r1_expectancy(ctx)
        elif rule == "R2":
            row = r2_robustness(ctx)
        elif rule == "R3":
            row = r3_mechanism(ctx)
        elif rule == "R4":
            row = r4_trend_reduction(ctx)
        elif rule == "R5":
            row = r5_clock_geometry(ctx)
        elif rule == "R6":
            row = r6_usd_macro(ctx)
        else:
            row = k6_slow_drift(ctx, k6_exact_test)
        rows.append(row)
        if row["verdict"] == "KILL":
            killed_by = rule
    dual = dual_books_rule(ctx)
    survivor = killed_by is None and dual["verdict"] == "PASS"
    stage = stage_a(ctx) if survivor else \
        _row("STAGE-A", "NOT_EVALUATED", "arm did not survive the ordered "
                                         "battery + dual-books")
    # Rules that neither kill nor pass (NOT_RUN / NOT_ADJUDICABLE) ride as
    # DISCLOSURES on a survivor — the same law that lets this cycle carry
    # R0 NOT_RUN (D2 skipped, §3b) into the terminal outcome name. They are
    # listed explicitly; they never become an inferred PASS.
    incomplete_rules = [r["rule"] for r in rows
                        if r["verdict"] in ("NOT_RUN", "NOT_ADJUDICABLE")]
    if killed_by is not None or dual["verdict"] == "KILL" or \
            stage["verdict"] == "KILL":
        arm_verdict = "REJECTED"
    elif stage["verdict"] != "PASS":
        # e.g. Stage-A NOT_RUN fail-closed on a degenerate book
        arm_verdict = "NOT_ADJUDICABLE_FAIL_CLOSED"
    elif survivor:
        arm_verdict = "SURVIVOR_CANDIDATE"
    else:
        arm_verdict = "REJECTED"
    return {
        "schema": "fsearch_i_arm_verdict@1",
        "config_id": ctx["config_id"],
        "family": ctx["family"],
        "arm_verdict": arm_verdict,
        "incomplete_rules": incomplete_rules,
        "stress_multiplier_primary": ctx["stress"],
        "ordered_rules": rows,
        "dual_books": dual,
        "stage_a": stage,
        "labels": verdict_labels(),
        "serial_clustering_census": ctx.get("serial_clustering"),
    }


def adjudicate_cycle(arm_ctxs: list, positions_by_arm: dict,
                     legs_order: list, frozen_matrix=None,
                     k6_exact_test=None) -> dict:
    arms = [adjudicate_arm(c, k6_exact_test) for c in arm_ctxs]
    p20 = p20_recheck(positions_by_arm, legs_order, frozen_matrix)
    survivors = [a["config_id"] for a in arms
                 if a["arm_verdict"] == "SURVIVOR_CANDIDATE"]
    # F-8: explicit scored-cell budget counter on every cycle output.
    budget = {"used": len(arm_ctxs), "max": SCORED_CELL_BUDGET_MAX,
              "within_budget": len(arm_ctxs) <= SCORED_CELL_BUDGET_MAX,
              "source": "plans/PLAN_forex_search_v1.md §0 (3 scored cells "
                        "max) + s/selection_freeze.json walk.budget.max_cells"}
    # F-2: the survivor outcome name is emitted ONLY after the DSR gate has
    # COMPUTED (and passed) on every survivor. stage_a PASS already implies
    # it; the explicit check makes the law structural — a harness change
    # that drops DSR from Stage-A can no longer emit the relaxed-battery
    # name.
    dsr_computed_on_survivors = all(
        a["stage_a"]["subgates"]["dsr"]["computed"] is True and
        a["stage_a"]["subgates"]["dsr"]["pass"] is True
        for a in arms if a["config_id"] in survivors)
    if p20["verdict"] != "PASS" or not budget["within_budget"]:
        outcome = "FOREX_SEARCH_V1_INCOMPLETE_NOT_PROMOTABLE"
    elif survivors and dsr_computed_on_survivors and \
            all(a["stage_a"]["verdict"] == "PASS" for a in arms
                if a["config_id"] in survivors):
        outcome = ("FOREX_SEARCH_V1_SURVIVORS_UNDER_RELAXED_BATTERY_"
                   "R0_NOT_RUN_PBO_NOT_RUN")
    elif all(a["arm_verdict"] == "REJECTED" for a in arms) and \
            any(r["rule"] == "R1" and r["verdict"] == "KILL"
                for a in arms for r in a["ordered_rules"]):
        outcome = "FOREX_SEARCH_V1_REJECT_ALL"
    else:
        outcome = "FOREX_SEARCH_V1_INCOMPLETE_NOT_PROMOTABLE"
    return {
        "schema": "fsearch_i_cycle_verdict@1",
        "arms": arms,
        "p20_recheck": p20,
        "survivors": survivors,
        "scored_cell_budget": budget,
        "dsr_gate_on_survivors": {"survivor_count": len(survivors),
                                  "computed_and_passed_on_every_survivor":
                                  bool(survivors) and
                                  dsr_computed_on_survivors},
        "incomplete_rules_by_arm": {a["config_id"]: a["incomplete_rules"]
                                    for a in arms},
        "proposed_outcome_name": outcome,
        "scored_execution": "NOT_AUTHORIZED_PRE_GO (plan §9: E runs only "
                            "after the exact owner GO at this cycle's gate)",
        "labels": verdict_labels(),
    }


def build_verdict_skeleton(config_ids: list) -> dict:
    """The pre-GO skeleton: structure + fail-closed labels only — no
    books, no numbers, no scored output of any kind."""
    return {
        "schema": "fsearch_i_verdict_skeleton@1",
        "phase": "I (isolated implementation lane; NO scored output)",
        "arms": [{"config_id": cid, "arm_verdict": None,
                  "ordered_rules": [], "stage_a": None} for cid in config_ids],
        "scored_cell_budget": {"used": 0, "max": SCORED_CELL_BUDGET_MAX,
                               "within_budget": True,
                               "source": "pre-GO skeleton: no scored cell "
                                         "consumed (plan §0 budget)"},
        "labels": verdict_labels(),
    }


# --------------------------------------------------------------------- main

def main() -> int:
    """I-lane entrypoint: verifies the frozen inputs and prints the
    pre-GO skeleton. Performs NO real-data execution (the staging loader
    in i_engine is gated behind the exact owner GO phrase and is for the
    E phase only)."""
    freeze = eng.load_freeze()
    skel = build_verdict_skeleton(
        [s["config_id"] for s in freeze["selections"]])
    import json
    print(json.dumps(skel, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
