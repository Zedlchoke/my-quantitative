"""Battery runner for DAILY-EXPLORATORY-V1 (exploratory execution lane).

HEAVY JOB: holds the machine-wide heavy lock (governance.heavy_lock)
end-to-end and releases it FINISHED. All outputs land under
research/control/DAILY-EXPLORATORY-V1/battery/ (inside this worktree).

Phases:
  0. inputs: load + sha-verify every frozen panel (EIA / IBKR / G6 /
     ANC / M1->D1), derive the vehicle-side D1 band cells for EURUSD +
     USDJPY (the G5 freeze-time act; MEASURED-DERIVED, validation-only).
  1. LEARN grid G1 (DS-03 Brent-flat): nodes A (null-control, reported
     only) / B / C on LEARN; frozen selection objective = net
     improvement vs B1S on LEARN subject to maxDD not worse; tie-break
     fewer deferred decisions, then the G7 frozen default B. Floor
     failure on LEARN -> NOT_RUN_GRID_THIN -> default B.
  2. B3 BEST_SINGLE selection: per-leg LEARN runs at tier x2.0;
     obj_B3 = DSR (PASS_BARS_V2 section 5 construction, N_eff = 2
     clusters) on per-trade NET USD; frozen tie-break chain (higher
     LEARN net x2.0, lower LEARN maxDD, lower turnover, earlier id).
  3. Floors: entry fires per (leg, fold) on the SLATE path at the
     selected node; <3 per fold -> leg FLAT in that fold in EVERY arm
     (typed NOT_RUN_THIN); full-window >=20 and aggregate >=100
     reported with typings.
  4. Arms: 10 identities / <=83 trial rows over the 8 EXPLORATORY
     folds (+3 LEARN grid rows), journals via the G9 writer, metrics
     per arm per fold, pooled; EXPLORATORY_DECLARED_COSTS on every PnL
     field; BATTERY_REPORT.md + TRIAL_LEDGER.jsonl.

NO PASS/FAIL of any PASS bar is computed — exploratory reporting only.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import statistics
import sys
import time
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import os

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[1]))

from . import battery as bt          # noqa: E402
from . import datainputs as di       # noqa: E402
from . import rules                  # noqa: E402
from .journal import DailyJournalWriter  # noqa: E402

REPO = Path("/Users/hoangminhlong/my-quantitative/"
            ".worktrees/pc12a-daily-exploratory-prep")
OUT = REPO / "research" / "control" / "DAILY-EXPLORATORY-V1" / "battery"
JOURNAL_DIR = OUT / "journals"
METRICS_DIR = OUT / "metrics"
INPUTS_DIR = OUT / "inputs"

TRIAL_ROWS_CAP = 83
IDENTITIES_CAP = 10

#: Identity registry (10; dispatch enumeration). REPORT20_PAIR carries
#: two member arms (SLATE + B1S re-priced at x2.0) = 16 fold rows.
IDENTITIES: List[Dict[str, object]] = [
    {"identity_id": "SLATE", "arm_class": "POLICY_SLATE", "tier": 1.0,
     "legs": ["DS-03", "DS-05"], "fold_rows": 8},
    {"identity_id": "B0_FLAT", "arm_class": "B0_FLAT", "tier": 1.0,
     "legs": [], "fold_rows": 0},
    {"identity_id": "B1S_ALWAYS_ON", "arm_class": "B1_ALWAYS_ON", "tier": 1.0,
     "legs": ["DS-03", "DS-05"], "fold_rows": 8},
    {"identity_id": "B2_EQUAL_WEIGHT", "arm_class": "B2_EQUAL_WEIGHT",
     "tier": 1.0, "legs": ["DS-03", "DS-05"], "fold_rows": 8},
    {"identity_id": "B3_BEST_SINGLE", "arm_class": "B3_BEST_SINGLE",
     "tier": 1.0, "legs": ["SELECTED"], "fold_rows": 8},
    {"identity_id": "LORO_EX_DS03", "arm_class": "LORO_LEAVE_ONE_OUT",
     "tier": 1.0, "legs": ["DS-05"], "fold_rows": 8},
    {"identity_id": "LORO_EX_DS05", "arm_class": "LORO_LEAVE_ONE_OUT",
     "tier": 1.0, "legs": ["DS-03"], "fold_rows": 8},
    {"identity_id": "STRESS15_SLATE", "arm_class": "STRESS_TIER", "tier": 1.5,
     "legs": ["DS-03", "DS-05"], "fold_rows": 8},
    {"identity_id": "STRESS15_B1S", "arm_class": "STRESS_TIER", "tier": 1.5,
     "legs": ["DS-03", "DS-05"], "fold_rows": 8},
    {"identity_id": "REPORT20_PAIR", "arm_class": "REPORT_TIER_PAIR",
     "tier": 2.0, "legs": ["DS-03", "DS-05"], "fold_rows": 16,
     "members": ["SLATE", "B1S"]},
]
LEARN_GRID_ROWS = 3  # nodes A (null-control, reported) / B / C


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def arm_config_digest(spec: Dict[str, object], node: str,
                      selected_leg: Optional[str]) -> str:
    payload = {
        "identity_id": spec["identity_id"], "arm_class": spec["arm_class"],
        "tier": spec["tier"], "legs": spec["legs"],
        "ds03_grid_node": node, "b3_selected_leg": selected_leg,
        "risk_unit_usd": str(bt.RISK_UNIT_USD),
        "calendar": [f for f in bt.FOLDS],
        "kernel": "DECLARED_COST_KERNEL@09fb1b74",
    }
    return hashlib.sha256(canonical(payload).encode()).hexdigest()


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def portfolio_metrics(leg_results: List[bt.LegResult], tier: float
                      ) -> Dict[str, object]:
    """Pooled per-window portfolio metrics from the quote-CCY books.

    Every PnL/DD field name carries the EXPLORATORY_DECLARED_COSTS
    label (dispatch law). USD numbers follow section 7b: equity marks
    convert at the same bar's rate (the books' conversion rows).
    """
    # REALIZED-USD equity curve (section 7b / REALIZATION_SAME_BAR@1):
    # every cash event (BOOK_OPEN / FILL / SWAP_ACCRUAL) contributes its
    # own conversion-row USD amount; the open position is marked at the
    # same bar's rate. Re-translating the whole quote-ccy CAPITAL BASE at
    # spot (level x rate) would add FX-translation noise of the untraded
    # base (the PC12A at-par lesson applied in reverse) and is NOT used.
    # Per-book state walk: the open position's USD value is exactly its
    # BASE units (mark rate = 1/same-bar mid cancels), so the curve is
    # cumulative realized cash + current base units at every event/mark
    # timestamp — no stale-mark dips between a fill and the next mark.
    per_book_curves: Dict[str, List[Tuple[str, Decimal]]] = {}
    realized_final: Dict[str, Decimal] = {}
    for lr in leg_results:
        for sym, book in lr.books.items():
            # Steps: mark (units snapshot at a session close), fillpair
            # (ATOMIC cash + units delta of one fill — cash and units of
            # the same fill always land on the curve together), cash
            # (BOOK_OPEN / SWAP_ACCRUAL). At the shared 17:00 ET boundary
            # ts the session's close MARK precedes the NEXT session's
            # open fills recorded at the same instant — marks sort first.
            steps: List[Tuple[str, str, Decimal, Decimal]] = []
            for c in book.conversion_rows:
                if c.event_kind in ("BOOK_OPEN", "SWAP_ACCRUAL"):
                    steps.append((c.event_ts, "cash", c.usd_amount, Decimal(0)))
            fill_rows = [c for c in book.conversion_rows
                         if c.event_kind == "FILL"]
            for f, c in zip(book.fills, fill_rows):  # append-order aligned
                steps.append((f.ts, "fillpair", c.usd_amount,
                              f.units_delta))
            for m in book.marks:
                steps.append((m.ts, "mark", Decimal(0), m.units))
            steps.sort(key=lambda x: (x[0], 0 if x[1] == "mark" else 1))
            cum = Decimal(0)
            units = Decimal(0)
            pts: List[Tuple[str, Decimal]] = []
            for ts, kind, cash_d, units_d in steps:
                if kind == "cash":
                    cum += cash_d
                elif kind == "fillpair":
                    cum += cash_d
                    units += units_d
                else:
                    units = units_d
                pts.append((ts, cum + units))
            realized_final[sym] = (cum + units) if steps else Decimal(0)
            per_book_curves.setdefault(sym, []).extend(pts)
    timeline = sorted({ts for pts in per_book_curves.values() for ts, _ in pts})
    equi: List[Decimal] = []
    levels = {sym: None for sym in per_book_curves}
    idx = {sym: 0 for sym in per_book_curves}
    seqs = {sym: sorted(pts) for sym, pts in per_book_curves.items()}
    for ts in timeline:
        for sym, seq in seqs.items():
            while idx[sym] < len(seq) and seq[idx[sym]][0] <= ts:
                levels[sym] = seq[idx[sym]][1]
                idx[sym] += 1
        equi.append(sum((v for v in levels.values() if v is not None),
                        Decimal(0)))
    total_open = Decimal(len(per_book_curves)) * bt.OPENING_USD
    peak = Decimal("-Infinity")
    maxdd = Decimal(0)
    for v in equi:
        if v > peak:
            peak = v
        if peak - v > maxdd:
            maxdd = peak - v
    net = (sum(realized_final.values()) - total_open) if realized_final \
        else Decimal(0)

    per_symbol = {}
    for lr in leg_results:
        for sym, book in lr.books.items():
            last_mark = book.marks[-1] if book.marks else None
            ir = book.check_identity(
                last_mark.ts if last_mark else "n/a",
                last_mark.mid if last_mark else Decimal(0))
            pr = book.par_replay(
                last_mark.ts if last_mark else "n/a",
                last_mark.mid if last_mark else Decimal(0),
                last_mark.conversion.rate_to_usd if last_mark else Decimal(1))
            conv = (last_mark.conversion.rate_to_usd
                    if last_mark else Decimal(1))
            per_symbol[sym] = {
                "quote_ccy": book.quote_ccy,
                "identity_holds_1e_9": ir.holds,
                "identity_residual": float(ir.residual),
                "par_replay_within_bound": pr.within_bound,
                "n_fills": ir.n_fills, "n_swap_events": ir.n_swap_events,
                "gross_vs_mid_quoteccy": float(ir.identity_gross_vs_mid_sum),
                "cost_spread_once_quoteccy": float(
                    ir.identity_cost_sum_spread_once),
                "cost_slip_beyond_quoteccy": float(
                    ir.identity_cost_sum_slip_beyond),
                "cost_commission_quoteccy": float(
                    ir.identity_cost_sum_commission),
                "cost_swap_quoteccy": float(ir.identity_cost_sum_swap),
                "reporting_conversion_rate_final_mark": float(conv),
                "final_mark_rate_source": "SAME_BAR_MID (REALIZATION_SAME_BAR@1)",
            }
    trades = [t for lr in leg_results for t in lr.trades]
    counts: Dict[str, int] = {}
    for lr in leg_results:
        for k, v in lr.counts.items():
            counts[f"{lr.leg}.{k}"] = counts.get(f"{lr.leg}.{k}", 0) + v
    return {
        "tier": tier,
        "labels": {
            "scope": "EXPLORATORY", "costs": bt.EXPLORATORY_LABEL,
            "bookkeeping": "quote-CCY (section 7b), REALIZATION_SAME_BAR@1",
        },
        "net_pnl_usd__EXPLORATORY_DECLARED_COSTS": float(net),
        "max_drawdown_usd__EXPLORATORY_DECLARED_COSTS": float(maxdd),
        "gross_vs_mid_usd__EXPLORATORY_DECLARED_COSTS":
            float(sum((Decimal(str(s["gross_vs_mid_quoteccy"]))
                       * Decimal(str(s["reporting_conversion_rate_final_mark"]))
                       for s in per_symbol.values()), Decimal(0))),
        "costs_total_usd__EXPLORATORY_DECLARED_COSTS":
            float(sum(((
                Decimal(str(s["cost_spread_once_quoteccy"]))
                + Decimal(str(s["cost_slip_beyond_quoteccy"]))
                + Decimal(str(s["cost_commission_quoteccy"]))
                + Decimal(str(s["cost_swap_quoteccy"])))
                * Decimal(str(s["reporting_conversion_rate_final_mark"]))
                for s in per_symbol.values()), Decimal(0))),
        "cost_decomposition_quoteccy": {
            k: {sym: s[k] for sym, s in per_symbol.items()}
            for k in ("cost_spread_once_quoteccy", "cost_slip_beyond_quoteccy",
                      "cost_commission_quoteccy", "cost_swap_quoteccy")},
        "equity_open_usd": float(total_open),
        "n_trades": len(trades),
        "n_marks": len(timeline),
        "per_symbol": per_symbol,
        "counts": counts,
        "trades": trades,
        "gross_cost_note": (
            "gross/cost USD components converted at the final-mark rate "
            "(REPORTING-CONVENTION@1); the GOVERNING USD figures are the "
            "equity-difference net and the equity-curve maxDD above"),
    }


# ---------------------------------------------------------------------------
# DSR (PASS_BARS_V2 section 5) for B3 selection
# ---------------------------------------------------------------------------

def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    """Acklam inverse-normal approximation (deterministic, stdlib-only)."""
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def sharpe(r: List[float]) -> Optional[float]:
    if len(r) < 2:
        return None
    sd = statistics.stdev(r)
    if sd == 0:
        return None
    return statistics.mean(r) / sd


def moments(rets: List[float]) -> Tuple[float, float]:
    """Biased sample skewness and kurtosis (moment definitions; 0 / 3
    fallbacks disclosed when n is too small)."""
    n = len(rets)
    m = statistics.mean(rets)
    m2 = sum((x - m) ** 2 for x in rets) / n
    if m2 <= 0 or n < 3:
        return 0.0, 3.0
    m3 = sum((x - m) ** 3 for x in rets) / n
    m4 = sum((x - m) ** 4 for x in rets) / n
    return m3 / m2 ** 1.5, m4 / m2 ** 2


def dsr(sr: Optional[float], rets: List[float], sr0: float
        ) -> Optional[float]:
    """DSR = Phi((SR-SR0)*sqrt(n-1)/sqrt(1 - g3*SR + (g4-1)/4*SR^2))."""
    if sr is None or len(rets) < 2:
        return None
    n = len(rets)
    g3, g4 = moments(rets)
    denom = math.sqrt(max(1e-12, 1 - g3 * sr + (g4 - 1) / 4 * sr * sr))
    return _norm_cdf((sr - sr0) * math.sqrt(n - 1) / denom)


def e_max(n_eff: int) -> float:
    """E[max] of N_eff null Sharpes (Bailey & LdP; gamma = Euler)."""
    gamma = 0.5772156649
    e = 2.7182818284
    return ((1 - gamma) * _norm_ppf(1 - 1 / n_eff)
            + gamma * _norm_ppf(1 - 1 / (n_eff * e)))


# ---------------------------------------------------------------------------
# Execution phases
# ---------------------------------------------------------------------------

def run_identity_window(legs: List[str], ctxs: Dict[str, bt.LegContext],
                        lo: str, hi: str, window_id: str, tier: float,
                        journal_dir: Path, journal_name: str,
                        floor_mask: Dict[Tuple[str, int], bool],
                        fold_no: Optional[int],
                        b2_split: Optional[Dict[str, Decimal]] = None,
                        journal: bool = True) -> List[bt.LegResult]:
    jw = None
    if journal:
        jw = DailyJournalWriter(
            journal_dir / f"{journal_name}.jsonl", cycle_id=bt.CYCLE_ID,
            fold_id=window_id,
            run_label=f"{journal_name}@x{tier}-EXPLORATORY", dry_mode=True)
    try:
        results = []
        for leg in legs:
            ctx = ctxs[leg]
            fb = bool(floor_mask.get((leg, fold_no), False)) \
                if fold_no is not None else False
            results.append(bt.run_leg(
                ctx, lo, hi, window_id, tier, jw,
                floor_blocked=fb, b2_split=b2_split))
        return results
    finally:
        if jw is not None:
            jw.close()


def main() -> int:
    t_start = time.time()
    for d in (OUT, JOURNAL_DIR, METRICS_DIR, INPUTS_DIR):
        d.mkdir(parents=True, exist_ok=True)

    # ---------------- phase 0: inputs -----------------------------------
    print("[0] loading frozen panels (sha-verified)...", flush=True)
    p = bt.build_panels(cache_dir=INPUTS_DIR)
    (INPUTS_DIR / "INPUTS_MANIFEST.json").write_text(json.dumps(
        p.meta, indent=1, sort_keys=True))

    bands: Dict[str, Dict[str, object]] = {}
    for inst in ("EURUSD", "USDJPY"):
        cells = di.derive_vehicle_bands(inst, p.d1[inst])
        bands.update(cells)
    di.register_vehicle_band_cells(bands)
    (INPUTS_DIR / "VEHICLE_BANDS_G5_FREEZE_ACT.json").write_text(json.dumps({
        "label": "MEASURED-DERIVED vehicle-side D1 band cells (G5 "
                 "freeze-time act for the two vehicles; fills price at "
                 "the bar's own quoted side — VALIDATION BANDS ONLY)",
        "instruments": ["EURUSD", "USDJPY"],
        "cells": bands,
    }, indent=1, sort_keys=True))
    print(f"    vehicle bands: {len(bands)} cells", flush=True)

    # ---------------- phase 1: LEARN grid G1 ----------------------------
    print("[1] LEARN grid G1 (DS-03 Brent-flat)...", flush=True)
    learn_grid: Dict[str, Dict[str, object]] = {}
    ctx03_by_node = {n: bt.LegContext("DS-03", p, n) for n in ("A", "B", "C")}
    ctx05 = bt.LegContext("DS-05", p)
    for node in ("A", "B", "C"):
        res = run_identity_window(
            ["DS-03", "DS-05"], {"DS-03": ctx03_by_node[node], "DS-05": ctx05},
            bt.LEARN[0], bt.LEARN[1], "LEARN", 1.0, JOURNAL_DIR,
            f"LEARN_GRID_G1_node{node}", {}, None, journal=True)
        m = portfolio_metrics(res, 1.0)
        learn_grid[node] = {
            "net_pnl_usd__EXPLORATORY_DECLARED_COSTS":
                m["net_pnl_usd__EXPLORATORY_DECLARED_COSTS"],
            "max_drawdown_usd__EXPLORATORY_DECLARED_COSTS":
                m["max_drawdown_usd__EXPLORATORY_DECLARED_COSTS"],
            "counts": m["counts"],
            "selectable": node in rules.DS03_GRID_SELECTABLE,
        }
    # frozen objective: net improvement vs B1S on LEARN, maxDD not worse.
    # B1S == SLATE mechanically at this slate (no eligibility layer
    # exists on the daily legs) -> improvement identically 0 for every
    # node -> frozen tie-break falls to the G7 default node B.
    grid_obj = {}
    for node in rules.DS03_GRID_SELECTABLE:
        slate_net = learn_grid[node][
            "net_pnl_usd__EXPLORATORY_DECLARED_COSTS"]
        grid_obj[node] = {
            "improvement_vs_b1s_learn": 0.0,
            "note": "B1S == SLATE mechanically (no eligibility layer on "
                    "the daily slate; PB2 B1 pins an L2 that does not "
                    "exist here) — disclosed degeneracy",
            "net_learn": slate_net,
        }
    fires_learn = {n: learn_grid[n]["counts"].get("DS-03.entry_fires", 0)
                   for n in rules.DS03_GRID_SELECTABLE}
    grid_thin = all(v < bt.FLOOR_PER_FOLD for v in fires_learn.values())
    if grid_thin:
        selected_node = bt.DS03_GRID_NODE_DEFAULT
        grid_verdict = "NOT_RUN_GRID_THIN (LEARN fires below floor; grid " \
                       "collapses to the frozen default B)"
    else:
        # improvement ties at 0.0 for B and C; frozen tie-break = fewer
        # deferred decisions (0 = 0), then the G7 default-first order.
        selected_node = bt.DS03_GRID_NODE_DEFAULT
        grid_verdict = ("SELECTED_BY_TIE_BREAK: improvement vs B1S "
                        "identically 0.0 on both selectable nodes "
                        "(B1S==SLATE degeneracy); G7 frozen default B")
    print(f"    LEARN fires: {fires_learn}; node={selected_node} "
          f"({grid_verdict})", flush=True)

    ctx03 = ctx03_by_node[selected_node]
    ctxs = {"DS-03": ctx03, "DS-05": ctx05}

    # ---------------- phase 2: B3 selection -----------------------------
    print("[2] B3 BEST_SINGLE selection (LEARN @ x2.0)...", flush=True)
    b3_record: Dict[str, object] = {}
    leg_learn = {}
    for leg in ("DS-03", "DS-05"):
        res = run_identity_window([leg], ctxs, bt.LEARN[0], bt.LEARN[1],
                                  "LEARN", 2.0, JOURNAL_DIR,
                                  f"B3_SELECTION_{leg}", {}, None,
                                  journal=True)
        m = portfolio_metrics(res, 2.0)
        leg_learn[leg] = {"metrics": m, "results": res}
    srs = {}
    for leg, blob in leg_learn.items():
        rets = _per_trade_net_usd(blob["results"])
        srs[leg] = sharpe(rets)
        blob["rets"] = rets
    sr_vals = [v for v in srs.values() if v is not None]
    if len(sr_vals) == 2:
        var_sr = statistics.variance(sr_vals)
    elif len(sr_vals) == 1:
        var_sr = sr_vals[0] ** 2
    else:
        var_sr = 0.0
    sr0 = math.sqrt(var_sr) * e_max(2)
    for leg, blob in leg_learn.items():
        blob["dsr"] = dsr(srs[leg], blob["rets"], sr0)
    cands = [leg for leg in ("DS-03", "DS-05")]
    # frozen tie-break: (1) higher LEARN net @x2.0; (2) lower maxDD;
    # (3) lower turnover (n fills); (4) earlier ledger row id (DS-03).
    def key(leg):
        m = leg_learn[leg]["metrics"]
        return (-m["net_pnl_usd__EXPLORATORY_DECLARED_COSTS"],
                m["max_drawdown_usd__EXPLORATORY_DECLARED_COSTS"],
                m["counts"].get(f"{leg}.entries_filled", 0))
    order = sorted(cands, key=key)
    best_dsrs = {l: leg_learn[l]["dsr"] for l in cands}
    if best_dsrs.get(order[0]) is not None and \
            best_dsrs.get(order[1]) is not None and \
            best_dsrs[order[0]] != best_dsrs[order[1]]:
        selected_leg = max(cands, key=lambda l: (best_dsrs[l] is not None,
                                                 best_dsrs[l] or -9))
        selection_stat = "DSR"
    else:
        selected_leg = order[0]
        selection_stat = "TIE_BREAK_CHAIN"
    b3_record = {
        "objective": "obj_B3 = DSR_T(leg) on LEARN per-trade NET USD at "
                     "x2.0 (PASS_BARS_V2 section 1/5; N_eff=2 clusters)",
        "sr0": sr0, "var_sharpes": var_sr, "n_eff": 2,
        "per_leg": {leg: {"sharpe": srs[leg], "dsr": best_dsrs[leg],
                          "n_trades": len(leg_learn[leg]["rets"]),
                          "net_learn_x2":
                              leg_learn[leg]["metrics"][
                                  "net_pnl_usd__EXPLORATORY_DECLARED_COSTS"],
                          "maxdd_learn_x2":
                              leg_learn[leg]["metrics"][
                                  "max_drawdown_usd__EXPLORATORY_DECLARED_COSTS"]}
                    for leg in cands},
        "selected_leg": selected_leg, "selection_stat": selection_stat,
        "tie_break_chain": "(1) higher LEARN net x2.0; (2) lower LEARN "
                           "maxDD; (3) lower turnover; (4) earlier row id",
    }
    print(f"    B3 selected: {selected_leg} via {selection_stat} "
          f"(DSR {best_dsrs})", flush=True)

    # ---------------- phase 3: floors ------------------------------------
    print("[3] decision floors (SLATE path @ x1.0)...", flush=True)
    fires: Dict[Tuple[str, int], int] = {}
    slate_pilot_b2_entry_dates: Dict[str, List[str]] = {"DS-03": [], "DS-05": []}
    for fold_no, lo, hi in bt.FOLDS:
        res = run_identity_window(["DS-03", "DS-05"], ctxs, lo, hi,
                                  f"FOLD-{fold_no}", 1.0, JOURNAL_DIR,
                                  f"_PILOT_FLOOR_FOLD{fold_no}", {}, fold_no,
                                  journal=False)
        for lr in res:
            fires[(lr.leg, fold_no)] = lr.counts.get("entry_fires", 0)
            for t in lr.trades:
                slate_pilot_b2_entry_dates[lr.leg].append(t["entry_session"])
    floor_mask: Dict[Tuple[str, int], bool] = {
        k: v < bt.FLOOR_PER_FOLD for k, v in fires.items()}
    thin_folds = {f"fold{f}_{leg}": "NOT_RUN_THIN"
                  for (leg, f), blocked in floor_mask.items() if blocked}
    full_window_fires = {leg: sum(v for (l, f), v in fires.items() if l == leg)
                         for leg in ("DS-03", "DS-05")}
    aggregate_fires = sum(fires.values())
    floor_report = {
        "floors": {">=3/fold": bt.FLOOR_PER_FOLD,
                   ">=20/full-window": bt.FLOOR_FULL_WINDOW,
                   ">=100/aggregate": bt.FLOOR_AGGREGATE},
        "fires_per_fold": {f"{leg}|fold{f}": fires[(leg, f)]
                           for (leg, f) in sorted(fires)},
        "thin_typed": thin_folds,
        "full_window_fires": full_window_fires,
        "full_window_verdict": {
            leg: ("OK" if v >= bt.FLOOR_FULL_WINDOW else "NOT_RUN_THIN")
            for leg, v in full_window_fires.items()},
        "aggregate_fires": aggregate_fires,
        "aggregate_verdict": ("OK" if aggregate_fires >= bt.FLOOR_AGGREGATE
                              else "NOT_RUN_THIN_AGGREGATE"),
        "law": "floor-failing (leg, fold) -> leg FLAT in that fold in "
               "EVERY arm (BLOCKED_FLOOR rows); battery continues",
    }
    print(f"    fires/fold: {fires}", flush=True)
    print(f"    full-window: {full_window_fires}, aggregate "
          f"{aggregate_fires}", flush=True)

    # B2 equal-split arithmetic (PB2 F-2 law): the SLATE's realized
    # per-decision total risk split equally across legs entering that
    # date. With RISK_UNIT_100USD@1 symmetric per leg this evaluates to
    # 100.00 for every entry (disclosed degeneracy == SLATE).
    from collections import Counter
    entry_counts = Counter(slate_pilot_b2_entry_dates["DS-03"]
                           + slate_pilot_b2_entry_dates["DS-05"])
    b2_split = {d: (bt.RISK_UNIT_USD * Decimal(n)) / Decimal(n)
                for d, n in entry_counts.items()}

    # ---------------- phase 4: arms --------------------------------------
    print("[4] arms over 8 EXPLORATORY folds...", flush=True)
    metrics: Dict[str, Dict[str, object]] = {}
    journals_written: List[str] = []
    fold_rows_used = 0

    def run_arm(identity_id: str, legs: List[str], tier: float,
                label_suffix: str = "") -> None:
        nonlocal fold_rows_used
        per_fold = {}
        for fold_no, lo, hi in bt.FOLDS:
            window_id = f"FOLD-{fold_no}"
            name = identity_id + label_suffix
            res = run_identity_window(
                legs, ctxs, lo, hi, window_id, tier, JOURNAL_DIR,
                f"{name}_{window_id}",
                floor_mask, fold_no,
                b2_split=b2_split if identity_id == "B2_EQUAL_WEIGHT" else None,
                journal=True)
            per_fold[window_id] = portfolio_metrics(res, tier)
            fold_rows_used += 1
            journals_written.append(f"{name}_{window_id}.jsonl")
        pooled_trades = []
        for w, m in per_fold.items():
            pooled_trades.extend(m["trades"])
        pooled = _pooled(per_fold, tier, pooled_trades)
        arm_class = next((i["arm_class"] for i in IDENTITIES
                          if i["identity_id"] == identity_id), None)
        if arm_class is None and identity_id.startswith("REPORT20_PAIR"):
            arm_class = "REPORT_TIER_PAIR_MEMBER"
        metrics[name] = {
            "identity_id": identity_id,
            "arm_class": arm_class,
            "tier": tier, "legs": legs,
            "per_fold": per_fold, "pooled": pooled,
            "labels": {"scope": "EXPLORATORY",
                       "costs": bt.EXPLORATORY_LABEL,
                       "pnl_fields": bt.EXPLORATORY_LABEL},
        }

    run_arm("SLATE", ["DS-03", "DS-05"], 1.0)
    metrics["B0_FLAT"] = {
        "identity_id": "B0_FLAT", "arm_class": "B0_FLAT", "tier": 1.0,
        "legs": [], "per_fold": {}, "journals": [],
        "pooled": {"net_pnl_usd__EXPLORATORY_DECLARED_COSTS": 0.0,
                   "max_drawdown_usd__EXPLORATORY_DECLARED_COSTS": 0.0,
                   "n_trades": 0,
                   "note": "FLAT by construction (PB2 section 1 B0 law): "
                           "no orders ever; zero journal rows"},
        "labels": {"scope": "EXPLORATORY", "costs": bt.EXPLORATORY_LABEL,
                   "pnl_fields": bt.EXPLORATORY_LABEL},
    }
    run_arm("B1S_ALWAYS_ON", ["DS-03", "DS-05"], 1.0)
    run_arm("B2_EQUAL_WEIGHT", ["DS-03", "DS-05"], 1.0)
    run_arm("B3_BEST_SINGLE", [selected_leg], 1.0)
    run_arm("LORO_EX_DS03", ["DS-05"], 1.0)
    run_arm("LORO_EX_DS05", ["DS-03"], 1.0)
    run_arm("STRESS15_SLATE", ["DS-03", "DS-05"], 1.5)
    run_arm("STRESS15_B1S", ["DS-03", "DS-05"], 1.5)
    run_arm("REPORT20_PAIR", ["DS-03", "DS-05"], 2.0, "_SLATE")
    run_arm("REPORT20_PAIR", ["DS-03", "DS-05"], 2.0, "_B1S")

    # degeneracy disclosures (byte-identical arms)
    degen = []
    if _same_arm(metrics["SLATE"], metrics["B1S_ALWAYS_ON"]):
        degen.append("B1S_ALWAYS_ON == SLATE (no eligibility layer on the "
                     "daily slate; PB2 B1 pins an L2 that does not exist)")
    if _same_arm(metrics["SLATE"], metrics["B2_EQUAL_WEIGHT"]):
        degen.append("B2_EQUAL_WEIGHT == SLATE (equal-split of the same "
                     "total budget at symmetric per-leg risk)")
    loro_of = {"DS-03": "LORO_EX_DS05", "DS-05": "LORO_EX_DS03"}
    if _same_arm(metrics["B3_BEST_SINGLE"],
                 metrics[loro_of[selected_leg]]):
        degen.append(f"B3_BEST_SINGLE ({selected_leg}) == "
                     f"{loro_of[selected_leg]} (the same leg alone)")

    # ---------------- budget guard ---------------------------------------
    trial_rows = fold_rows_used + LEARN_GRID_ROWS
    assert trial_rows <= TRIAL_ROWS_CAP, f"trial rows {trial_rows} > cap"
    assert len(IDENTITIES) <= IDENTITIES_CAP

    # ---------------- write metrics --------------------------------------
    print("[5] writing outputs...", flush=True)
    for name, m in metrics.items():
        (METRICS_DIR / f"{name}.json").write_text(
            json.dumps(m, indent=1, sort_keys=True, default=float))
    ledger_rows = []
    for spec in IDENTITIES:
        rows = spec["fold_rows"]
        digest = arm_config_digest(spec, selected_node, selected_leg)
        ledger_rows.append({
            "schema": "trial_ledger_row@1",
            "cycle_id": bt.CYCLE_ID,
            "identity_id": spec["identity_id"],
            "arm_class": spec["arm_class"],
            "tier": spec["tier"],
            "legs": (spec["legs"] if spec["legs"] != ["SELECTED"]
                     else [selected_leg]),
            "fold_scope": "EXPLORATORY (folds 1-8, 2022-09-30..2026-09-24)",
            "trial_rows": rows,
            "arm_config_digest": digest,
            "label": "EXPLORATORY",
            "costs_label": bt.EXPLORATORY_LABEL,
            "no_after_cost_pass": True,
            "budget": {"identities_used": len(IDENTITIES),
                       "trial_rows_used": trial_rows,
                       "caps": {"identities": IDENTITIES_CAP,
                                "rows": TRIAL_ROWS_CAP}},
            "ds03_grid_node_selected": selected_node,
            "b3_selected_leg": selected_leg,
        })
    (OUT / "TRIAL_LEDGER.jsonl").write_text(
        "\n".join(canonical(r) for r in ledger_rows) + "\n")

    summary = {
        "cycle_id": bt.CYCLE_ID,
        "header": bt.EXPLORATORY_ONLY_HEADER,
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "runtime_s": round(time.time() - t_start, 1),
        "learn_grid": {"nodes": learn_grid, "objective": grid_obj,
                       "selected_node": selected_node,
                       "verdict": grid_verdict,
                       "fires_learn": fires_learn},
        "b3_selection": b3_record,
        "floors": floor_report,
        "degeneracies": degen,
        "trial_rows_used": trial_rows,
        "identities": len(IDENTITIES),
        "journals": journals_written,
        "arm_pooled_net_usd": {
            name: m["pooled"]["net_pnl_usd__EXPLORATORY_DECLARED_COSTS"]
            for name, m in metrics.items()},
        "arm_pooled_maxdd_usd": {
            name: m["pooled"]["max_drawdown_usd__EXPLORATORY_DECLARED_COSTS"]
            for name, m in metrics.items()},
    }
    (OUT / "BATTERY_SUMMARY.json").write_text(json.dumps(
        summary, indent=1, sort_keys=True, default=float))
    (OUT / "REPORT20_PAIR.json").write_text(json.dumps({
        "identity_id": "REPORT20_PAIR",
        "members": {"SLATE@x2.0": metrics["REPORT20_PAIR_SLATE"]["pooled"],
                    "B1S@x2.0": metrics["REPORT20_PAIR_B1S"]["pooled"]},
        "labels": {"scope": "EXPLORATORY", "costs": bt.EXPLORATORY_LABEL},
    }, indent=1, sort_keys=True, default=float))
    print(json.dumps({k: summary[k] for k in
                      ("trial_rows_used", "identities", "degeneracies",
                       "arm_pooled_net_usd")}, indent=1, default=float))
    print(f"DONE in {time.time() - t_start:.1f}s", flush=True)
    return 0


def _per_trade_net_usd(results: List[bt.LegResult]) -> List[float]:
    """Per-trade NET USD (EXPLORATORY bookkeeping; each trade's quote-ccy
    net converted at its entry realization rate — declared reporting
    convention for the B3 selection statistic)."""
    return [float(t["net_usd__EXPLORATORY_DECLARED_COSTS"])
            for lr in results for t in lr.trades]


def _pooled(per_fold: Dict[str, Dict[str, object]], tier: float,
            trades: List[Dict[str, object]]) -> Dict[str, object]:
    net = sum((Decimal(str(m["net_pnl_usd__EXPLORATORY_DECLARED_COSTS"]))
               for m in per_fold.values()), Decimal(0))
    dd = max((Decimal(str(m["max_drawdown_usd__EXPLORATORY_DECLARED_COSTS"]))
              for m in per_fold.values()), default=Decimal(0))
    cost = sum((Decimal(str(m["costs_total_usd__EXPLORATORY_DECLARED_COSTS"]))
                for m in per_fold.values()), Decimal(0))
    gross = sum((Decimal(str(m["gross_vs_mid_usd__EXPLORATORY_DECLARED_COSTS"]))
                 for m in per_fold.values()), Decimal(0))
    counts: Dict[str, int] = {}
    for m in per_fold.values():
        for k, v in m["counts"].items():
            counts[k] = counts.get(k, 0) + v
    return {
        "tier": tier,
        "labels": {"scope": "EXPLORATORY", "costs": bt.EXPLORATORY_LABEL},
        "net_pnl_usd__EXPLORATORY_DECLARED_COSTS": float(net),
        "max_drawdown_usd__EXPLORATORY_DECLARED_COSTS": float(dd),
        "gross_vs_mid_usd__EXPLORATORY_DECLARED_COSTS": float(gross),
        "costs_total_usd__EXPLORATORY_DECLARED_COSTS": float(cost),
        "n_trades": len(trades),
        "counts": counts,
    }


def _same_arm(a: Dict[str, object], b: Dict[str, object]) -> bool:
    ga = {w: (m["net_pnl_usd__EXPLORATORY_DECLARED_COSTS"],
              m["max_drawdown_usd__EXPLORATORY_DECLARED_COSTS"],
              m["n_trades"])
          for w, m in a["per_fold"].items()}
    gb = {w: (m["net_pnl_usd__EXPLORATORY_DECLARED_COSTS"],
              m["max_drawdown_usd__EXPLORATORY_DECLARED_COSTS"],
              m["n_trades"])
          for w, m in b["per_fold"].items()}
    return ga == gb


def run_under_heavy_lock() -> int:
    """Canonical execution: machine-wide heavy lock held END-TO-END,
    released FINISHED (or FAILED with the stderr tail in the note)."""
    import governance.heavy_lock as hl
    cmd = [".venv/bin/python", "-c",
           "from daily_exploratory.run_battery import main; main()"]
    try:
        handle = hl.acquire(
            cycle_id="DAILY-EXPLORATORY-V1",
            role="battery-execution",
            worktree=str(REPO),
            command=cmd,
            expected_artifacts=[
                str(OUT / "BATTERY_REPORT.md"),
                str(OUT / "TRIAL_LEDGER.jsonl"),
                str(OUT / "BATTERY_SUMMARY.json"),
            ],
        )
    except hl.LockBusyError as exc:
        print(json.dumps({"verdict": "NOT_RUN_RESOURCE_CONFLICT",
                          "reason": str(exc)}))
        return 4
    except hl.HeavyLockError as exc:
        print(json.dumps({"verdict": "CONTROL_STATE_DRIFT",
                          "reason": str(exc)}))
        return 5
    rc = 1
    note = ""
    try:
        rc = main()
        note = f"battery complete rc={rc}"
    except SystemExit as exc:            # budget-guard asserts
        note = f"aborted: {exc}"
        rc = int(exc.code or 1)
    except Exception as exc:             # noqa: BLE001 — record the tail
        import traceback
        note = "FAILED: " + traceback.format_exc()[-800:]
        rc = 2
    finally:
        handle.release(status="FINISHED" if rc == 0 else "FAILED",
                       note=note)
    return rc


if __name__ == "__main__":
    sys.exit(run_under_heavy_lock())
