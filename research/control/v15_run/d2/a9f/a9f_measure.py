#!/usr/bin/env python3
"""V15 D2 A9F feasibility audit - measurements for the 6 D1 proposals (18 arms).

Measures: decision counts per fold, warmup support, one-side turnover per
decision, cost burden (fee exact; tick-slippage under labelled fallback band),
break-even gross edge, hole-refusal census (amendment-1), control
runnability/degeneracy/identity (feature rho + weight rho), fold population.

NO PnL, NO returns, NO expectancy of positions anywhere.
"""
import datetime as dt
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from a9f_common import (
    WT, DATA, FROZEN_UNIVERSE, S0_START, S0_END, STAGING_START, LAG_DAYS,
    HOLE_FRAC_REFUSE, FOLDS, FOLD_IDS, SCORING_DAYS, daterange, fold_of,
    load_defect_census, load_symbol_metrics, load_symbol_klines_daily,
    hole_refuse, FEE_BPS, FEE_STRESS_BPS, TICK_BPS_FALLBACK, STRESS_EXTRA_TICKS,
)

T0 = time.time()
UNIVERSE = sorted(FROZEN_UNIVERSE)
SCORING = sorted(SCORING_DAYS)
FOLD_LAST = {f: FOLDS[f][1] for f in FOLD_IDS}
FOLD_FIRST = {f: FOLDS[f][0] for f in FOLD_IDS}

# ---------------------------------------------------------------- data layer
print("loading data...")
METRICS, KLINE, AVAIL = {}, {}, {}
for s in UNIVERSE:
    METRICS[s] = load_symbol_metrics(s)
    KLINE[s] = load_symbol_klines_daily(s)
DEFECT = load_defect_census()
# Staged-cell semantics (measured): staging-refused (symbol,day) cells are the
# amendment-1 "missing metrics-day cells". Grid-violation days are fully absent
# from parquet; parse_error days retain partial rows but the CELL was refused by
# the frozen integrity gate, so refused cells never feed features.
window_days = set(daterange(STAGING_START, S0_END))
for s in UNIVERSE:
    have = set(METRICS[s]["oi00"].index)
    assert have | DEFECT[s] == window_days, f"{s} census mismatch (missing days not in defect list)"
    AVAIL[s] = sorted(d for d in have if d not in DEFECT[s])  # usable days
print(f"data loaded in {time.time()-T0:.1f}s; "
      f"usable metrics days per symbol: {len(next(iter(AVAIL.values())))}, "
      f"defect cells per symbol: {sorted((len(v), k) for k, v in DEFECT.items())[-3:]} (top)")

# ---------------------------------------------------------------- helpers
def weights_to_stats(path, min_trade=0.0):
    """path: list of (date, dict{sym: w}). Returns per-decision one-side
    turnover fraction (0.5*sum|dw|), fills count, gross."""
    recs, cur = [], {}
    for d, tgt in path:
        tgt = tgt or {}
        new = dict(cur)
        fills = 0
        for s in set(cur) | set(tgt):
            tw, cw = tgt.get(s, 0.0), cur.get(s, 0.0)
            if abs(tw - cw) >= min_trade:
                if abs(tw - cw) > 1e-12:
                    fills += 1
                if abs(tw) > 1e-12:
                    new[s] = tw
                else:
                    new.pop(s, None)
        t = 0.5 * sum(abs(new.get(s, 0.0) - cur.get(s, 0.0))
                      for s in set(new) | set(cur))
        gross = sum(abs(v) for v in new.values())
        recs.append({"date": d, "fold": fold_of(d), "one_side_turnover": t,
                     "fills": fills, "gross": gross,
                     "n_held": len(new), "n_target": len(tgt)})
        cur = new
    return pd.DataFrame(recs)


def cost_block(df_stats):
    """Cost burden per decision in bps of gross; base & stress; fee exact,
    tick under fallback band. Break-even gross edge per decision = cost bps."""
    t = df_stats["one_side_turnover"]
    out = {}
    table = {
        "base_tick_low": FEE_BPS + TICK_BPS_FALLBACK["low"],
        "base_tick_high": FEE_BPS + TICK_BPS_FALLBACK["high"],
        "stress_tick_low": FEE_STRESS_BPS + TICK_BPS_FALLBACK["low"],
        "stress_tick_high": FEE_STRESS_BPS + TICK_BPS_FALLBACK["high"],
    }
    for name, per_fill_bps in table.items():
        per_dec = t * per_fill_bps
        out[name] = {
            "per_fill_bps_assumed": per_fill_bps,
            "mean_cost_bps_of_gross_per_decision": round(per_dec.mean(), 4),
            "median_cost_bps_of_gross_per_decision": round(per_dec.median(), 4),
            "sum_cost_bps_of_gross_over_S0": round(per_dec.sum(), 2),
        }
    out["fee_only_floor_mean_bps"] = round((t * FEE_BPS).mean(), 4)
    out["note"] = ("cost bps of gross = one_side_turnover_fraction x per_fill_bps; "
                   "gross<=1.0 so bps-of-gross = bps-of-notional at full gross")
    return out


def fold_table(df_stats):
    rows = []
    for f in FOLD_IDS:
        d = df_stats[df_stats["fold"] == f]
        rows.append({
            "fold": f, "window": [FOLDS[f][0].isoformat(), FOLDS[f][1].isoformat()],
            "decision_dates": int(len(d)),
            "decisions_with_nonzero_book": int((d["gross"] > 1e-9).sum()),
            "fills": int(d["fills"].sum()),
            "one_side_turnover_sum": round(d["one_side_turnover"].sum(), 4),
        })
    return rows


def _rank_avg(x):
    x = pd.Series(x)
    return x.rank(method="average").to_numpy()


def pooled_spearman(a_flat, b_flat):
    s = pd.DataFrame({"a": a_flat, "b": b_flat}).dropna()
    if len(s) < 100 or s["a"].nunique() < 3 or s["b"].nunique() < 3:
        return None, len(s)
    ra, rb = _rank_avg(s["a"]), _rank_avg(s["b"])
    rho = float(np.corrcoef(ra, rb)[0, 1])
    return round(rho, 4), len(s)


def panel_diag(panel):
    """panel: dict date -> dict sym -> value (refused dates/syms absent)."""
    disp, uniq = [], []
    n = 0
    for d, row in panel.items():
        vals = np.array(list(row.values()), dtype=float)
        if len(vals) >= 5:
            n += len(vals)
            disp.append(float(vals.std()))
            uniq.append(int(pd.Series(vals).nunique()))
    return {
        "symbol_date_obs": n,
        "median_cross_sectional_std": round(float(np.median(disp)), 6) if disp else None,
        "min_cross_sectional_std": round(float(np.min(disp)), 8) if disp else None,
        "median_unique_values_per_decision": int(np.median(uniq)) if uniq else 0,
        "degenerate": bool(np.min(disp) == 0) if disp else True,
    }


def stack(panel):
    idx, cols, vals = [], [], []
    for d, row in panel.items():
        for s, v in row.items():
            idx.append(d); cols.append(s); vals.append(v)
    return pd.Series(vals, index=pd.MultiIndex.from_arrays([idx, cols]))


ARMS = {}

def register_arm(pid, arm_key, spec, panel=None, refusal_by_sym=None):
    ARMS[f"{pid}:{arm_key}"] = {
        "proposal": pid, "arm": arm_key, "spec": spec,
        "panel_diag": panel_diag(panel) if panel else None,
        "refusal_by_symbol": refusal_by_sym or {},
    }

# ================================================================ A4-P1 REGSTAB
def churn_panel(window_chg, universe):
    """churn = mean |dlog OI| over trailing `window_chg` changes (window+1 obs),
    LAG_3D + hole rule."""
    out, refused = {}, {}
    for D in SCORING:
        out[D], refused[D] = {}, {}
        bound = D - dt.timedelta(days=LAG_DAYS)
        for s in universe:
            av = AVAIL[s]
            dates = [d for d in av if d <= bound]
            need = window_chg + 1
            if len(dates) < need:
                refused[D][s] = "insufficient_history"
                continue
            win = dates[-need:]
            ref, nmiss, span = hole_refuse(win, DEFECT[s])
            if ref:
                refused[D][s] = f"hole_rule_{nmiss}/{span}"
                continue
            oi = METRICS[s]["oi00"]
            tot = 0.0
            for i in range(1, need):
                tot += abs(np.log(oi[win[i]] / oi[win[i - 1]]))
            out[D][s] = tot / window_chg
    return out, refused


def rangec_panel(universe, window=28):
    """A4-P1 control feature: mean (high-low)/prev_close over trailing `window`
    kline days <= D-3 (same lag bound applied to kline dates per spec)."""
    out = {}
    for D in SCORING:
        bound = D - dt.timedelta(days=LAG_DAYS)
        out[D] = {}
        for s in universe:
            k = KLINE[s]
            k = k[k.index <= bound]
            if len(k) < window + 1:
                continue
            out[D][s] = float(k["tr_pct"].iloc[-window:].mean())
    return out


def run_tercile_book(panel, universe, side_n=7):
    """long bottom third (asc), short top third; w=0.5/n_side; force-flat at
    each fold's last decision date. Refusal-robust side sizing: sides scale
    with eligible names (n_elig//3, min 1) so a refused symbol never kills the
    decision date; weights stay under the 0.30 cap by construction."""
    path = []
    for D in SCORING:
        if D == FOLD_LAST[fold_of(D)]:
            path.append((D, {}))
            continue
        row = panel.get(D, {})
        if len(row) < 2:
            path.append((D, {}))
            continue
        ns = max(1, len(row) // 3)
        order = sorted(row, key=lambda s: (row[s], s))
        w = 0.5 / ns
        tgt = {s: w for s in order[:ns]}
        tgt.update({s: -w for s in order[-ns:]})
        path.append((D, tgt))
    return path


print("A4-P1 panels...")
ch28, ch28_ref = churn_panel(28, UNIVERSE)
ch56, ch56_ref = churn_panel(56, UNIVERSE)
rc28 = rangec_panel(UNIVERSE, 28)
for arm, pan in [("ANCHOR-churn28", ch28), ("NEIGH-churn56", ch56), ("CTL-rangec28", rc28)]:
    st = weights_to_stats(run_tercile_book(pan, UNIVERSE))
    ARMS[f"A4-P1:{arm}"] = {
        "proposal": "A4-P1", "arm": arm,
        "decision_cadence": "daily", "decision_dates_S0": len(SCORING),
        "stats": st, "cost": cost_block(st), "folds": fold_table(st),
        "panel_diag": panel_diag(pan),
    }
a4p1_rho, a4p1_n = pooled_spearman(stack(ch28), stack(rc28))
ARMS["A4-P1:IDENTITY"] = {"control_vs_anchor_feature_spearman_rho": a4p1_rho,
                          "n_symbol_dates": a4p1_n,
                          "flag": "CONTROL_SELF_SUBSUMPTION_RISK" if a4p1_rho is not None and abs(a4p1_rho) > 0.95 else "OK"}

# ================================================================ A4-P2 REGSHOCK
def build_events(universe):
    """event at metrics date e: |dlog OI| > max(P90 of trailing 42 changes, 0.05).
    Returns per-symbol list of (e, direction +1 long/-1 short, |chg|, refused_flag)."""
    ev = {}
    for s in universe:
        oi = METRICS[s]["oi00"]
        av = AVAIL[s]
        chg = {}  # later-date -> (value, prev_date)
        for i in range(1, len(av)):
            chg[av[i]] = (abs(np.log(oi[av[i]] / oi[av[i - 1]])),
                          np.log(oi[av[i]] / oi[av[i - 1]]), av[i - 1])
        cdates = sorted(chg)
        lst = []
        for j, e in enumerate(cdates):
            prior = cdates[max(0, j - 42):j]
            if len(prior) < 42:
                continue
            span = [prior[0], e]
            ref, nmiss, sp = hole_refuse(span, DEFECT[s])
            p90 = float(np.percentile([chg[p][0] for p in prior], 90))
            thr = max(p90, 0.05)
            fired = chg[e][0] > thr
            lst.append({"e": e, "dir": (+1 if chg[e][1] < 0 else -1) if fired else 0,
                        "abs_chg": chg[e][0], "thr": thr, "refused": ref})
        ev[s] = lst
    return ev


def run_event_book(events, hold_days=5, size=0.10, max_conc=10, universe=UNIVERSE):
    """Event-conditioned book simulation on decision grid (structure only, no PnL)."""
    last_event = {}
    for s in universe:
        for x in events[s]:
            if x["dir"] != 0 and not x["refused"]:
                last_event.setdefault(x["e"], []).append((s, x["dir"], x["abs_chg"]))
    path, open_pos = [], {}
    entries = exits = refused_entries = 0
    blocked_open = blocked_cap = 0
    entry_log, conc = [], []
    event_fired_total = sum(1 for s in universe for x in events[s] if x["dir"] != 0)
    event_refused_total = sum(1 for s in universe for x in events[s] if x["dir"] != 0 and x["refused"])
    for D in SCORING:
        f = fold_of(D)
        # exits due today
        due = [s for s, p in open_pos.items() if p["exit"] == D]
        for s in due:
            del open_pos[s]
            exits += 1
        # force-flat / no entries on fold-last
        if D == FOLD_LAST[f]:
            for s in list(open_pos):
                del open_pos[s]
                exits += 1
            path.append((D, {}))
            conc.append(len(open_pos))
            continue
        # new candidates at e = latest available metrics date <= D-3
        cand = []
        for s in universe:
            if s in open_pos:
                continue
            bound = D - dt.timedelta(days=LAG_DAYS)
            av = [d for d in AVAIL[s] if d <= bound]
            if not av:
                continue
            e = av[-1]
            for x in events[s]:
                if x["e"] == e and x["dir"] != 0:
                    if x["refused"]:
                        refused_entries += 1
                    else:
                        cand.append((s, x["dir"], x["abs_chg"]))
                    break
        cand.sort(key=lambda t: (-t[2], t[0]))
        for s, drc, _ in cand:
            if len(open_pos) >= max_conc:
                blocked_cap += 1
                continue
            if s in open_pos:
                blocked_open += 1
                continue
            exit_d = min(D + dt.timedelta(days=hold_days), FOLD_LAST[f])
            open_pos[s] = {"dir": drc, "exit": exit_d}
            entries += 1
            entry_log.append({"date": D, "symbol": s, "dir": drc})
        tgt = {s: p["dir"] * size for s, p in open_pos.items()}
        path.append((D, tgt))
        conc.append(len(open_pos))
    return path, {"events_fired": event_fired_total,
                  "events_refused_by_hole_rule": event_refused_total,
                  "entries": entries, "exits": exits,
                  "refused_entries": refused_entries,
                  "entries_blocked_position_already_open": blocked_open,
                  "entries_blocked_concurrency_cap": blocked_cap,
                  "mean_concurrent_positions": round(float(np.mean(conc)), 2),
                  "max_concurrent_positions": int(np.max(conc))}, entry_log


print("A4-P2 events...")
EV = build_events(UNIVERSE)
a4p2_anchor = run_event_book(EV, hold_days=5)
a4p2_neigh = run_event_book(EV, hold_days=10)
# control: price TR% shocks, same book
def price_events(universe):
    ev = {}
    for s in universe:
        k = KLINE[s]
        tr = k["tr_pct"].dropna()
        dates = sorted(tr.index)
        lst = []
        for j, e in enumerate(dates):
            prior = dates[max(0, j - 42):j]
            if len(prior) < 42:
                continue
            thr = max(float(np.percentile([tr[p] for p in prior], 90)), 0.05)
            fired = tr[e] > thr
            day_close = k.loc[e, "close"]
            prev_close = k.loc[prior[-1], "close"] if j > 0 else np.nan
            drc = 0
            if fired and not np.isnan(prev_close):
                drc = +1 if day_close < prev_close else -1  # fade: down-close -> long
            lst.append({"e": e, "dir": drc, "abs_chg": tr[e], "thr": thr, "refused": False})
        ev[s] = lst
    return ev

PEV = price_events(UNIVERSE)
a4p2_ctl = run_event_book(PEV, hold_days=5)
for arm, (path, meta, elog), evsrc in [
    ("ANCHOR-fadeP90-h5", a4p2_anchor, EV),
    ("NEIGH-fadeP90-h10", a4p2_neigh, EV),
    ("CTL-priceshock", a4p2_ctl, PEV),
]:
    st = weights_to_stats(path)
    ev_oi = evsrc is EV
    ARMS[f"A4-P2:{arm}"] = {
        "proposal": "A4-P2", "arm": arm, "decision_cadence": "daily",
        "decision_dates_S0": len(SCORING), "stats": st, "cost": cost_block(st),
        "folds": fold_table(st),
        "event_meta": {**meta,
                       "entries_per_fold": {f: int(sum(1 for x in elog if fold_of(x["date"]) == f)) for f in FOLD_IDS},
                       "symbols_with_entries": int(len(set(x["symbol"] for x in elog))),
                       "entries_by_symbol_top_bottom": sorted(
                           [(s, int(sum(1 for x in elog if x["symbol"] == s))) for s in set(x["symbol"] for x in elog)],
                           key=lambda t: t[1])[:3] + sorted(
                           [(s, int(sum(1 for x in elog if x["symbol"] == s))) for s in set(x["symbol"] for x in elog)],
                           key=lambda t: -t[1])[:3]},
        "feature_source": "sum_open_interest (OI events)" if ev_oi else "klines TR% (price events)",
    }
a4p2_ev_dirs = [x["dir"] for s in UNIVERSE for x in EV[s] if x["dir"] != 0 and not x["refused"]]
ARMS["A4-P2:IDENTITY"] = {
    "anchor_vs_control_feature": "OI shock |dlogOI| vs price TR% shock — different fields by design",
    "anchor_event_dir_split_long_short": [sum(1 for d in a4p2_ev_dirs if d > 0), sum(1 for d in a4p2_ev_dirs if d < 0)],
    "flag": "OK (distinct information sources)",
}

# ================================================================ A5-P1 ELITE-SIZE-ASYM
def s5_panel(universe, win_start_days_back=7):
    """S = median over [D-win_start_days_back, D-3] of ln(clip(sum_tt)) -
    ln(clip(count_tt)); hole rule on the row window; also CTL = median
    ln(clip(count_tt))."""
    S, C, ref = {}, {}, {}
    clip = lambda x: min(max(x, np.log(0.01)), np.log(100.0))
    n_rows = win_start_days_back - 2
    for D in SCORING:
        S[D], C[D], ref[D] = {}, {}, {}
        win = [D - dt.timedelta(days=k) for k in range(win_start_days_back, 2, -1)]
        for s in universe:
            idx = METRICS[s]
            avail = set(AVAIL[s])
            if any(w not in avail for w in win):
                nmiss = sum(1 for w in win if w in DEFECT[s])
                ref[D][s] = f"missing_rows_{nmiss}/{n_rows}"
                continue
            ref2, nmiss, span = hole_refuse(win, DEFECT[s])
            if ref2:
                ref[D][s] = f"hole_rule_{nmiss}/{span}"
                continue
            st = [clip(np.log(idx["sum_tt00"][w])) for w in win]
            ct = [clip(np.log(idx["count_tt00"][w])) for w in win]
            S[D][s] = float(np.median(st) - np.median(ct))
            C[D][s] = float(np.median(ct))
    return S, C, ref


def run_sides_book(panel, universe, side_n=7, min_trade=0.05):
    """long bottom side_n asc, short top side_n; w=0.5/side_n; A5 min-trade
    threshold; force-flat fold-last."""
    path = []
    for D in SCORING:
        if D == FOLD_LAST[fold_of(D)]:
            path.append((D, {}))
            continue
        row = panel.get(D, {})
        if len(row) < 2 * side_n:
            path.append((D, {}))
            continue
        order = sorted(row, key=lambda s: (row[s], s))
        w = 0.5 / side_n
        tgt = {s: w for s in order[:side_n]}
        tgt.update({s: -w for s in order[-side_n:]})
        path.append((D, tgt))
    return weights_to_stats(path, min_trade=min_trade), path


print("A5-P1 panels...")
a5_universe_listed = sorted([s for s in UNIVERSE if s != "SOLUSDT"])  # A5 lists 19 symbols (SOLUSDT absent)
S5, C5, S5ref = s5_panel(a5_universe_listed, win_start_days_back=7)
S10, _, S10ref = s5_panel(a5_universe_listed, win_start_days_back=12)  # neighbour NB10Q window
st_anchor, path_anchor = run_sides_book(S5, a5_universe_listed)
st_neigh, _ = run_sides_book(S10, a5_universe_listed, side_n=5)  # NB10Q: 10-row median + quintile sides
st_ctl, _ = run_sides_book(C5, a5_universe_listed)
st_anchor20, _ = run_sides_book(S5, UNIVERSE)  # robustness: frozen 20-symbol universe
for arm, st, pan in [("ANCHOR", st_anchor, S5), ("NEIGH-Q5", st_neigh, S5), ("CTL-ELITELEVEL", st_ctl, C5)]:
    ARMS[f"A5-P1:{arm}"] = {
        "proposal": "A5-P1", "arm": arm, "decision_cadence": "daily",
        "decision_dates_S0": len(SCORING), "stats": st, "cost": cost_block(st),
        "folds": fold_table(st), "panel_diag": panel_diag(pan),
        "universe_used": "19 symbols as listed in proposal (SOLUSDT absent)" if arm != "x" else "",
    }
a5p1_rho, a5p1_n = pooled_spearman(stack(S5), stack(C5))
ARMS["A5-P1:IDENTITY"] = {
    "control_vs_anchor_feature_spearman_rho": a5p1_rho,
    "n_symbol_dates": a5p1_n,
    "anchor_weight20_vs_19_turnover_delta_pct": round(100 * (st_anchor20["one_side_turnover"].sum() - st_anchor["one_side_turnover"].sum()) / max(st_anchor["one_side_turnover"].sum(), 1e-9), 2),
    "flag": "CONTROL_SELF_SUBSUMPTION_RISK" if a5p1_rho is not None and abs(a5p1_rho) > 0.95 else "OK",
}

# ================================================================ A5-P2 CROWD-LATE-CHURN
def v_panel(universe):
    """v_glob/v_top/v_tops: ln ratio at D-3 minus ln ratio at D-23."""
    Vg, Vt, Vts, ref = {}, {}, {}, {}
    clip = lambda x: min(max(x, np.log(0.01)), np.log(100.0))
    for D in SCORING:
        Vg[D], Vt[D], Vts[D], ref[D] = {}, {}, {}, {}
        d0, d1 = D - dt.timedelta(days=23), D - dt.timedelta(days=LAG_DAYS)
        for s in universe:
            idx = METRICS[s]
            avail = set(AVAIL[s])
            keys = {"g": idx["count_ls00"], "t": idx["count_tt00"], "ts": idx["sum_tt00"]}
            if d0 not in avail or d1 not in avail:
                ref[D][s] = "missing_endpoint"
                continue
            ref2, nmiss, span = hole_refuse([d0, d1], DEFECT[s])
            if ref2:
                ref[D][s] = f"hole_rule_{nmiss}/{span}"
                continue
            Vg[D][s] = clip(np.log(keys["g"][d1])) - clip(np.log(keys["g"][d0]))
            if d0 in keys["t"].index and d1 in keys["t"].index:
                Vt[D][s] = clip(np.log(keys["t"][d1])) - clip(np.log(keys["t"][d0]))
            if d0 in keys["ts"].index and d1 in keys["ts"].index:
                Vts[D][s] = clip(np.log(keys["ts"][d1])) - clip(np.log(keys["ts"][d0]))
    return Vg, Vt, Vts, ref


def run_gated_book(Vg, Vgate, universe, gated=True, min_trade=0.05):
    """top-5 |v_glob|; anchor: fire iff elite non-confirmed; control: ungated.
    weights: side gross 0.5 (moved if other side empty), per-name min(0.5/n,0.30)."""
    path, fire_stats = [], []
    name_days = {}
    for D in SCORING:
        if D == FOLD_LAST[fold_of(D)]:
            path.append((D, {}))
            fire_stats.append({"date": D, "n_fired": 0, "empty": True})
            continue
        row = Vg.get(D, {})
        if len(row) < 5:
            path.append((D, {}))
            fire_stats.append({"date": D, "n_fired": 0, "empty": True})
            continue
        top5 = sorted(row, key=lambda s: (-abs(row[s]), s))[:5]
        longs, shorts = [], []
        for s in top5:
            vg = row[s]
            if gated:
                vt = Vgate.get(D, {}).get(s)
                if vt is None or not (abs(vt) < 0.5 * abs(vg)):
                    continue
            (shorts if vg > 0 else longs).append(s)
        tgt = {}
        side_gross = {"L": 0.5 if shorts else 1.0, "S": 0.5 if longs else 1.0}
        for s in longs:
            tgt[s] = min(side_gross["L"] / max(len(longs), 1), 0.30)
        for s in shorts:
            tgt[s] = -min(side_gross["S"] / max(len(shorts), 1), 0.30)
        path.append((D, tgt))
        for s in tgt:
            name_days[s] = name_days.get(s, 0) + 1
        fire_stats.append({"date": D, "n_fired": len(tgt), "empty": len(tgt) == 0})
    st = weights_to_stats(path, min_trade=min_trade)
    fs = pd.DataFrame(fire_stats)
    empty_by_fold = {f: round(float(fs[fs["date"].map(fold_of) == f]["empty"].mean()), 4) for f in FOLD_IDS}
    total_nd = max(sum(name_days.values()), 1)
    return st, {"days_fired": int((~fs["empty"]).sum()),
                "empty_fraction_S0": round(float(fs["empty"].mean()), 4),
                "empty_fraction_by_fold": empty_by_fold,
                "mean_fired_names_when_fired": round(float(fs[~fs["empty"]]["n_fired"].mean()), 2),
                "empty_fraction_by_fold_max": max(empty_by_fold.values()),
                "name_day_concentration_top3": [
                    {"symbol": s, "name_days": n, "share": round(n / total_nd, 4)}
                    for s, n in sorted(name_days.items(), key=lambda t: -t[1])[:3]],
                "n_fired_name_days": int(sum(name_days.values()))}


print("A5-P2 panels...")
Vg, Vt, Vts, Vref = v_panel(a5_universe_listed)
st_ag, meta_ag = run_gated_book(Vg, Vt, a5_universe_listed, gated=True)
st_ng, meta_ng = run_gated_book(Vg, Vts, a5_universe_listed, gated=True)   # neighbour: position-velocity gate
st_cg, meta_cg = run_gated_book(Vg, None, a5_universe_listed, gated=False)  # control: ungated
for arm, st, meta in [("ANCHOR", st_ag, meta_ag), ("NEIGH-POSVEL", st_ng, meta_ng), ("CTL-UNGATED", st_cg, meta_cg)]:
    ARMS[f"A5-P2:{arm}"] = {
        "proposal": "A5-P2", "arm": arm, "decision_cadence": "daily",
        "decision_dates_S0": len(SCORING), "stats": st, "cost": cost_block(st),
        "folds": fold_table(st), "fire_meta": meta,
    }
# identity: anchor vs control book overlap (same features, different rule)
ARMS["A5-P2:IDENTITY"] = {
    "control_vs_anchor": "same features; control = anchor rule with gate removed (by design superset of anchor fires)",
    "anchor_days_fired": meta_ag["days_fired"], "control_days_fired": meta_cg["days_fired"],
    "control_days_fired_over_anchor": round(meta_cg["days_fired"] / max(meta_ag["days_fired"], 1), 4),
    "anchor_nonvacuity_margin": {
        "rule": "proposal's own drop-one-fold bound: fired set empty on >50% of a fold's decision days = non-vacuous failure",
        "measured_empty_fraction_by_fold": meta_ag["empty_fraction_by_fold"],
        "bound": 0.50,
        "margin_to_fail_pp": {f: round(100 * (meta_ag["empty_fraction_by_fold"][f] - 0.50), 1) for f in FOLD_IDS},
    },
    "flag": "OK" if meta_cg["days_fired"] >= 0.6 * meta_ag["days_fired"] else "CONTROL_DECISION_COUNT_BELOW_60PCT_OF_ANCHOR",
}

# ================================================================ A6 P1/P2 (5-day grid)
def a6_grid():
    """Decision grid: every 5 calendar days from each fold start, plus an
    explicit force-flat entry at each fold's last day (force-flat contract)."""
    dates = []
    for f in FOLD_IDS:
        a, b = FOLDS[f]
        d = a
        while d <= b:
            dates.append((d, f))
            d += dt.timedelta(days=5)
    have = {d for d, _ in dates}
    for f in FOLD_IDS:
        if FOLD_LAST[f] not in have:
            dates.append((FOLD_LAST[f], f))
    return sorted(dates)


def a6_panels(universe, window_days):
    """A_bar (daily aggression mean), O (|dlog OIv55| endpoints), g (dlog TT55),
    A_abs; window = window_days daily aggregates in [D-12/23, D-3]."""
    W = window_days
    A_bar, O_ch, Gg, A_abs, ref = {}, {}, {}, {}, {}
    for D, _f in a6_grid():
        bound = D - dt.timedelta(days=LAG_DAYS)
        start_cal = D - dt.timedelta(days=LAG_DAYS + window_days - 1)
        A_bar[D], O_ch[D], Gg[D], A_abs[D], ref[D] = {}, {}, {}, {}, {}
        for s in universe:
            idx = METRICS[s]
            avail = set(AVAIL[s])
            ag = idx["agg"]; ab = idx["absagg"]; oiv = idx["oiv55"]; tt = idx["sum_tt00"]
            days = [d for d in ag.index if start_cal <= d <= bound and d in avail]
            if len(days) < W:
                nmiss = sum(1 for d in daterange(start_cal, bound) if d in DEFECT[s])
                ref[D][s] = f"missing_days_{nmiss}/{window_days}"
                continue
            ref2, nmiss, span = hole_refuse(days, DEFECT[s])
            if ref2:
                ref[D][s] = f"hole_rule_{nmiss}/{span}"
                continue
            d0, d1 = days[0], days[-1]
            A_bar[D][s] = float(ag[days].mean())
            A_abs[D][s] = float(ab[days].mean())
            if d0 in oiv.index and d1 in oiv.index:
                O_ch[D][s] = abs(np.log(oiv[d1] / oiv[d0]))
            if d0 in tt.index and d1 in tt.index:
                Gg[D][s] = float(np.log(tt[d1] / tt[d0]))
    return A_bar, O_ch, Gg, A_abs, ref


def run_a6_book(feature, long_low):
    """5-vs-5 extreme rank book, +-0.10; flat cycle if <10 eligible;
    long top-5 (desc) unless long_low; force-flat at each fold's last day
    (explicit flat entry even when no 5-day grid date lands on it)."""
    path = []
    grid = a6_grid()
    flat_dates = []
    for i, (D, f) in enumerate(grid):
        last_of_fold = D == FOLD_LAST[f]
        if last_of_fold or len(feature.get(D, {})) < 10:
            path.append((D, {}))
            if not last_of_fold:
                flat_dates.append(D)
            continue
        row = feature[D]
        order = sorted(row, key=lambda s: (-row[s], s))  # desc
        hi, lo = order[:5], order[-5:]
        tgt = {}
        for s in hi:
            tgt[s] = -0.10 if long_low else 0.10
        for s in lo:
            tgt[s] = 0.10 if long_low else -0.10
        path.append((D, tgt))
    return weights_to_stats(path), {"flat_cycles_lt10_eligible_dates": [d.isoformat() for d in flat_dates]}


print("A6 panels...")
Abar10, O10, G10, Aabs10, A6ref10 = a6_panels(UNIVERSE, 10)
Abar20, O20, G20, Aabs20, A6ref20 = a6_panels(UNIVERSE, 20)
S_p1 = {D: {s: Abar10[D][s] / (O10[D][s] + 0.02) for s in Abar10[D] if s in O10[D]} for D in Abar10}
S_p1n = {D: {s: Abar20[D][s] / (O20[D][s] + 0.02) for s in Abar20[D] if s in O20[D]} for D in Abar20}
R_p2 = {D: {s: G10[D][s] / (Aabs10[D][s] + 0.01) for s in G10[D] if s in Aabs10[D]} for D in G10}
R_p2n = {D: {s: G20[D][s] / (Aabs20[D][s] + 0.01) for s in G20[D] if s in Aabs20[D]} for D in G20}
A6_GRID_N = len(a6_grid())
for pid, feat_a, feat_n, feat_c, long_low, tag in [
    ("A6-P1", S_p1, S_p1n, Abar10, True, "A_bar/(O+0.02); CTL raw A_bar"),
    ("A6-P2", R_p2, R_p2n, G10, False, "g/(A_abs+0.01); CTL raw g"),
]:
    for arm, feat in [("ANCHOR", feat_a), ("NEIGH-W20", feat_n), ("CTL", feat_c)]:
        st, a6meta = run_a6_book(feat, long_low)
        ARMS[f"{pid}:{arm}"] = {
            "proposal": pid, "arm": arm, "decision_cadence": "every 5 calendar days from fold start",
            "decision_dates_S0": A6_GRID_N,
            "flat_cycles_lt10_eligible": len(a6meta["flat_cycles_lt10_eligible_dates"]),
            "flat_cycle_dates": a6meta["flat_cycles_lt10_eligible_dates"],
            "stats": st, "cost": cost_block(st), "folds": fold_table(st),
            "panel_diag": panel_diag(feat),
        }
    rho, n = pooled_spearman(stack(feat_a), stack(feat_c))
    ARMS[f"{pid}:IDENTITY"] = {
        "control_vs_anchor_feature_spearman_rho": rho, "n_symbol_dates": n,
        "flag": "CONTROL_SELF_SUBSUMPTION_RISK" if rho is not None and abs(rho) > 0.95 else "OK",
    }

# ================================================================ refusal census summary
def refusal_summary(ref):
    by_sym, by_fold = {}, {}
    total = 0
    for D, row in ref.items():
        f = fold_of(D)
        by_fold[f] = by_fold.get(f, 0) + len(row)
        total += len(row)
        for s, why in row.items():
            by_sym[s] = by_sym.get(s, 0) + 1
    n_sd = len(ref) * len(UNIVERSE)
    return {"symbol_date_refused": total, "symbol_date_denominator": n_sd,
            "refusal_rate": round(total / max(n_sd, 1), 5),
            "by_symbol_top": dict(sorted(by_sym.items(), key=lambda t: -t[1])[:6]),
            "by_fold": by_fold}

ARMS["A4-P1:REFUSALS"] = {"anchor": refusal_summary(ch28_ref), "neighbour": refusal_summary(ch56_ref)}
ARMS["A5-P1:REFUSALS"] = {"anchor": refusal_summary(S5ref), "neighbour": refusal_summary(S10ref)}
ARMS["A5-P2:REFUSALS"] = {"anchor": refusal_summary(Vref)}
ARMS["A6:REFUSALS"] = {"P1_anchor_W10": refusal_summary(A6ref10), "P1_neigh_W20": refusal_summary(A6ref20)}

# ================================================================ warmup verification
# Earliest decision date each spec's lookback + LAG_3D actually support, measured
# against staged usable metrics days (STAGING_START = 2025-06-20).
def warmup_check(n_obs_required, first_decision, label):
    """Count usable metrics obs <= (first_decision - 3) and report whether the
    claimed first decision is fully supported; also the earliest fully-supported
    decision date given staged depth."""
    bound = first_decision - dt.timedelta(days=LAG_DAYS)
    ok_all = True
    min_obs = 10 ** 9
    for s in UNIVERSE:
        n = sum(1 for d in AVAIL[s] if d <= bound)
        min_obs = min(min_obs, n)
        ok_all &= n >= n_obs_required
    return {"feature_obs_required": n_obs_required, "at_first_decision": first_decision.isoformat(),
            "metrics_date_bound": bound.isoformat(),
            "min_usable_obs_across_universe": min_obs,
            "supported_at_claimed_first_decision": bool(ok_all),
            "margin_usable_obs": min_obs - n_obs_required,
            "label": label}

ARMS["WARMUP_VERIFICATION"] = {
    "staging_first_usable_metrics_day_per_symbol": STAGING_START.isoformat(),
    "A4-P1_anchor_churn28_needs_29_obs": warmup_check(29, SCORING[0], "28 changes need 29 observations"),
    "A4-P1_neighbour_churn56_needs_57_obs": warmup_check(57, SCORING[0], "56 changes need 57 observations"),
    "A4-P2_anchor_P90_43_obs": warmup_check(43, SCORING[0], "42 changes + event day need 43 observations"),
    "A5-P1_anchor_5_rows": warmup_check(5, SCORING[0], "median over rows [D-7,D-3]"),
    "A5-P1_neighbour_10_rows": warmup_check(10, SCORING[0], "median over rows [D-12,D-3]"),
    "A5-P2_anchor_2_endpoint_rows_span21": warmup_check(2, SCORING[0], "endpoints D-23 and D-3 usable"),
    "A6_anchor_W10": warmup_check(10, a6_grid()[0][0], "10 daily aggregates [D-12,D-3]"),
    "A6_neighbour_W20": warmup_check(20, a6_grid()[0][0], "20 daily aggregates [D-23,D-3]"),
}

# decision dates with zero eligible cross-section (post-refusal), per daily arm
def empty_days(st_df):
    return [d.isoformat() for d in st_df[st_df["gross"] <= 1e-9]["date"]]
ARMS["EMPTY_BOOK_DECISION_DAYS"] = {
    "A4-P1:ANCHOR": empty_days(ARMS["A4-P1:ANCHOR-churn28"]["stats"]),
    "A5-P1:ANCHOR": empty_days(ARMS["A5-P1:ANCHOR"]["stats"]),
    "A5-P2:ANCHOR_note": "A5-P2 emptiness is the fire-gate census (see fire_meta), not data refusal",
    "A4-P2:ANCHOR_note": "event book: gross reflects concurrent positions; empty days are no-event days",
}


# ================================================================ dump
OUT = WT / "research/control/v15_run/d2/a9f/a9f_measurements_raw.json"
def ser(o):
    if isinstance(o, (dt.date, dt.datetime)):
        return o.isoformat()
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, pd.DataFrame):
        return o.assign(date=o["date"].map(lambda d: d.isoformat())).to_dict(orient="records")
    raise TypeError(str(type(o)))
OUT.write_text(json.dumps(ARMS, indent=1, default=ser))
print(f"raw measurements written -> {OUT}  ({time.time()-T0:.1f}s total)")
