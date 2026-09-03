"""Z9 A7T independent recomputation (audit-only, no repairs).

Own valuation loop implementing the documented harness semantics from scratch:
- day return r = sadj(t)/sadj(t-1) - 1 + dist(t)/sadj(t-1), weighted by current weights
- fill processed AFTER the fill day's return (fill close rebalance, no same-day return)
- cost = equity * one_way_turnover * bps / 10000 (ETF legs only, cash residual)
- per-period pnl = equity delta across holding period; MDD from daily curve

Book generation uses the frozen W1 family module exactly as the staged runner does
(data conventions), but NO harness.value_book / harness.attribution code is called.
"""
import importlib.util
import json
import sys
from datetime import date, timedelta

Z8 = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z8-exec-1"
STAGE = Z8 + "/.staging"

sys.path.insert(0, Z8)

spec_cr = importlib.util.spec_from_file_location("cell_runner_mod", STAGE + "/cell_runner.py")
cr = importlib.util.module_from_spec(spec_cr)
spec_cr.loader.exec_module(cr)

from research.assets.stocks.calendar import US_EQUITY_REGULAR_V1 as CAL  # noqa: E402

COV_START, COV_END = "2018-01-02", "2026-08-27"
SYMBOLS = ["SPY", "XLK", "XLE", "XLF", "XLV", "XLI", "XLP", "XLY", "XLU", "XLB", "XLRE"]


def sessions_between(a, b):
    out, d = [], date.fromisoformat(a)
    while d <= date.fromisoformat(b):
        if CAL.is_session_day(d):
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


# ---------- independent math ----------
def split_adj(series_d: str, close: float, factors: dict) -> float:
    cum = 1.0
    for eff, f in sorted(factors.items()):
        if series_d < eff:
            cum *= float(f)
    return close * cum


class Series:
    def __init__(self, raw, splits):
        self.raw = raw
        self.dates = sorted(raw)
        self.splits = splits

    def prev(self, d):
        import bisect
        i = bisect.bisect_left(self.dates, d)
        return self.dates[i - 1] if i > 0 else None

    def ret(self, d, dist):
        p = self.prev(d)
        if p is None or d not in self.raw:
            return None
        sadj_p = split_adj(p, self.raw[p], self.splits)
        sadj_d = split_adj(d, self.raw[d], self.splits)
        return sadj_d / sadj_p - 1.0 + float(dist.get(d, 0.0)) / sadj_p


def my_value(entries, series_map, dist_map, fold_sessions, cost_bps):
    """Independent reimplementation of the documented valuation semantics."""
    fill_map = {}
    for e in entries:
        if e.get("entry_type") == "FORCE_FLAT":
            fill_map[e["fill_date"]] = {}
        else:
            fill_map[e["fill_date"]] = {s: w for s, w in e["targets"].items() if s != "CASH"}
    dates = [d for d in fold_sessions if any(d in series_map[s].raw for s in SYMBOLS)]
    equity = 1.0
    curve = {}
    weights = {}
    periods = []
    period_start = 1.0
    pending = None
    total_cost = 0.0
    first = True
    for d in dates:
        if not first:
            ret = 0.0
            for s, w in weights.items():
                if w:
                    r = series_map[s].ret(d, dist_map.get(s, {}))
                    if r is not None:
                        ret += w * r
            equity *= (1.0 + ret)
        else:
            first = False
        if d in fill_map:
            if pending is not None:
                periods.append((pending, equity - period_start))
            targets = fill_map[d]
            turnover = sum(abs(targets.get(s, 0.0) - weights.get(s, 0.0))
                           for s in set(targets) | set(weights))
            cost = equity * turnover * cost_bps / 10_000.0
            equity -= cost
            total_cost += cost
            weights = dict(targets)
            period_start = equity
            pending = d
        curve[d] = equity
    if pending is not None:
        periods.append((pending, equity - period_start))
    peak, mdd = 0.0, 0.0
    for d in sorted(curve):
        v = curve[d]
        peak = max(peak, v)
        if peak > 0:
            mdd = max(mdd, (peak - v) / peak)
    return {"pnl": equity - 1.0, "periods": periods, "mdd": mdd,
            "total_cost": total_cost, "curve": curve}


def my_attribution(entries, series_map, dist_map, fold_sessions, cost_bps, cost_multiplier=1):
    """Independent attribution sidecar; cost_multiplier probes the runner's
    double-count (`total_cost += cost` twice at staged runner lines 227-228)."""
    fill_map = {e["fill_date"]: e for e in entries}
    weights = {}
    equity = 1.0
    contrib = {}
    total_cost = 0.0
    first = True
    for d in fold_sessions:
        if not first:
            rets = {}
            for s, w in weights.items():
                if w:
                    r = series_map[s].ret(d, dist_map.get(s, {}))
                    if r is not None:
                        rets[s] = r
            port = sum(w * rets.get(s, 0.0) for s, w in weights.items())
            for s, r in rets.items():
                contrib[s] = contrib.get(s, 0.0) + equity * weights.get(s, 0.0) * r
            equity *= (1.0 + port)
        else:
            first = False
        if d in fill_map:
            e = fill_map[d]
            targets = {} if e.get("entry_type") == "FORCE_FLAT" else {
                s: w for s, w in e["targets"].items() if s != "CASH"}
            turnover = sum(abs(targets.get(s, 0.0) - weights.get(s, 0.0))
                           for s in set(targets) | set(weights))
            cost = equity * turnover * cost_bps / 10_000.0
            equity -= cost  # runner deducts equity ONCE (line 226)
            total_cost += cost
            if cost_multiplier == 2:
                total_cost += cost  # runner doubles the ACCUMULATOR ONLY (lines 227-228)
            weights = dict(targets)
    return contrib, total_cost


def main():
    results = {}
    symbols, raw, dist, splits, tr = cr.load_inputs()
    series_map = {s: Series(raw[s], splits.get(s, {})) for s in SYMBOLS}
    folds = json.load(open(STAGE + "/partition_folds.json"))
    sessions = sessions_between(COV_START, COV_END)
    part = json.load(open(Z8 + "/research/control/stocks_free_v2_run/partition.json"))

    def build(family, arm_id):
        return cr.build_book(family, arm_id, symbols, raw, tr)

    # ---------- T2: A4 anchor + negative control ----------
    for family, arm_id in [("A4_XSEC_ETF_RELATIVE_MOMENTUM", "ARM_A4_ANCHOR_MOM121_EQW_TOP3"),
                           ("A4_XSEC_ETF_RELATIVE_MOMENTUM", "ARM_A4_NEGCTRL_BOTTOM3_EQW_MOM121")]:
        entries, _ = build(family, arm_id)
        fold_out = []
        all_periods = []
        for f in folds:
            fid, fs, fe = f["fold_id"], f["start"], f["scored_end"]
            sub = [e for e in entries if e.get("fold_id") == fid and e["fill_date"] <= fe]
            fsess = [x for x in sessions if fs <= x <= fe]
            r = my_value(sub, series_map, dist, fsess, 7.0)
            fold_out.append({"fold_id": fid, "pnl": r["pnl"], "mdd": r["mdd"],
                             "n_periods": len(r["periods"])})
            all_periods += r["periods"]
        total = 1.0
        for b in fold_out:
            total *= (1.0 + b["pnl"])
        total -= 1.0
        exp = sum(p for _, p in all_periods) / max(1, len(all_periods))
        gains = sum(p for _, p in all_periods if p > 0)
        losses = sum(p for _, p in all_periods if p < 0)
        pf = gains / abs(losses) if losses < 0 else None
        results[arm_id] = {"total_pnl": total, "expectancy": exp, "pf_overall": pf,
                           "folds_positive": sum(1 for b in fold_out if b["pnl"] > 0),
                           "folds": fold_out,
                           "max_fold_mdd": max(b["mdd"] for b in fold_out)}

    anchor, control = results["ARM_A4_ANCHOR_MOM121_EQW_TOP3"], results["ARM_A4_NEGCTRL_BOTTOM3_EQW_MOM121"]
    print("T2 ANCHOR  total_pnl =", round(anchor["total_pnl"], 6), "(published 1.371909)")
    print("T2 ANCHOR  expectancy =", anchor["expectancy"], "(published 0.0129348274848704)")
    print("T2 ANCHOR  pf_overall =", anchor["pf_overall"], "(published 1.8959883586565809)")
    print("T2 ANCHOR  folds =", [(b['fold_id'], round(b['pnl'], 6), round(b['mdd'], 6)) for b in anchor["folds"]])
    print("T2 ANCHOR  max fold MDD =", round(anchor["max_fold_mdd"], 6), "(claimed 30.36%)")
    print("T2 CONTROL expectancy =", control["expectancy"], "(published 0.012476374265088816)")
    print("T2 CONTROL/ANCHOR ratio =", control["expectancy"] / anchor["expectancy"], "(claimed 96.5%)")
    print("T2 CONTROL folds_positive =", control["folds_positive"], "(claimed 2/3)")

    # ---------- T3: A5 crosscheck provenance (double-cost probe) ----------
    print("\nT3 A5 crosscheck probe (recorded tolerance 0.02):")
    for arm_id in ["A5-SFV2-ARM1-TSM12-VOLTARGET", "A5-SFV2-ARM2-SMA200-WEEKLY",
                   "A5-SFV2-ARM3-TSM12-INVERTED-CONTROL"]:
        entries, _ = cr.build_book("A5-SFV2-TREND-DEFENSIVE", arm_id, symbols, raw, tr)
        art = json.load(open(STAGE + "/cell_" + arm_id + ".json"))
        for i, f in enumerate(folds):
            fid, fs, fe = f["fold_id"], f["start"], f["scored_end"]
            sub = [e for e in entries if e.get("fold_id") == fid and e["fill_date"] <= fe]
            fsess = [x for x in sessions if fs <= x <= fe]
            val = my_value(sub, series_map, dist, fsess, 10.0)
            c1, cost1 = my_attribution(sub, series_map, dist, fsess, 10.0, cost_multiplier=1)
            c2, cost2 = my_attribution(sub, series_map, dist, fsess, 10.0, cost_multiplier=2)
            cross1 = abs(sum(c1.values()) - cost1 - val["pnl"])
            cross2 = abs(sum(c2.values()) - cost2 - val["pnl"])
            rec = art["base_folds"][i]["attribution_crosscheck"]
            print(f"  {arm_id} {fid}: recorded={rec:.6f} double_cost_repro={cross2:.9f} "
                  f"single_cost={cross1:.6f} {'<=0.02' if cross1 <= 0.02 else '>0.02'}")

    # ---------- T4: S1 isolation ----------
    print("\nT4 S1 isolation:")
    arms = ["ARM_A4_ANCHOR_MOM121_EQW_TOP3", "ARM_A4_NEIGHBOR_VOLADJ_MOM121_INVVOL_TOP3",
            "ARM_A4_NEGCTRL_BOTTOM3_EQW_MOM121", "A5-SFV2-ARM1-TSM12-VOLTARGET",
            "A5-SFV2-ARM2-SMA200-WEEKLY", "A5-SFV2-ARM3-TSM12-INVERTED-CONTROL"]
    global_max = ""
    for arm in arms:
        art = json.load(open(STAGE + "/cell_" + arm + ".json"))
        dates = [p[0] for b in art["base_folds"] for p in b["periods"]]
        mx = max(dates)
        global_max = max(global_max, mx)
        print(f"  {arm}: max period date {mx}")
    print("  GLOBAL max fill/period date =", global_max, "(S1 start 2025-08-01; must be <= 2025-07-31)")
    sfx = json.load(open(STAGE + "/split_factors.json"))
    print("  split factors:", sfx)
    pre_s0 = {s: {d: f for d, f in v.items() if d <= "2025-07-31"} for s, v in sfx.items()}
    print("  split events inside S0 window:", {k: v for k, v in pre_s0.items() if v} or "NONE")

    import os
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a7t_recompute_results.json")
    json.dump(results, open(out, "w"), indent=1, default=str)
    print("\nDONE")


if __name__ == "__main__":
    main()
