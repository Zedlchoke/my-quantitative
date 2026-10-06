"""A3 — 6J term structure + quarterly-chain rolls 2020-2026 (DEEP-6J).

From per-contract session closes (outright 1m panel):
  * near-vs-next-quarterly calendar spread on overlapping sessions (sign,
    magnitude in ticks and bp, by year) — the persistent premium/discount;
  * all ~27 quarterly rolls: roll gap (old close -> new close at the PIT
    volume-crossover switch), liquidity migration windows (old/new volume
    around the switch; crossover lead/lag vs delivery month), serial-book
    share of total volume by year (dead-book confirmation on the new data);
  * OI migration for rolls in 2023-10+ (GLBX statistics stat_type 9 only);
  * CIP check: annualized roll gap vs US 3m T-bill (FRED DTB3, latest +
    year-end ALFRED vintages — sparse-vintage caveat disclosed) -> implied
    JPY short rate; NOT a PIT-strict instrument, descriptive only.
"""
from __future__ import annotations

import os
import sys

import importlib

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
L = importlib.import_module("6J_deep_lib")

OUT = os.path.join(L.HERE, "6J_a3_term.json")
QRE = "6J[HMUZ]\\d_\\d{4}"


def main():
    sess = pd.read_parquet(os.path.join(L.CACHE, "6j_sessions.parquet"))
    held = pd.read_parquet(os.path.join(L.CACHE, "held_volume_k5.parquet"))
    reg = pd.read_json(os.path.join(L.CACHE, "contract_registry.json"))
    exp = dict(zip(reg["contract"], reg["expiry"]))

    q = sess[sess["contract"].str.match(QRE)].copy()
    q["d"] = pd.to_datetime(q["session_date"])
    q["exp"] = pd.to_datetime(q["contract"].map(exp))
    q = q.sort_values(["exp", "d"])

    res = {"schema": "6J_a3_term@1"}

    # ---- serial vs quarterly share of total 6J volume by year ----
    tot = sess.copy()
    tot["year"] = pd.to_datetime(tot["session_date"]).dt.year
    tot["is_q"] = tot["contract"].str.match(QRE)
    byy = tot.groupby("year").apply(
        lambda g: float(100 * g.loc[~g["is_q"], "volume"].sum() / g["volume"].sum()),
        include_groups=False)
    res["serial_volume_share_pct_by_year"] = {str(k): float(v) for k, v in byy.items()}

    # ---- near-vs-next quarterly spread on overlapping sessions ----
    closes = q.pivot_table(index="d", columns="contract", values="close")
    bars = q.pivot_table(index="d", columns="contract", values="n_bars")
    vols = q.pivot_table(index="d", columns="contract", values="volume")
    qcons = sorted(closes.columns, key=lambda c: exp[c])
    pairs = []
    for a, b in zip(qcons[:-1], qcons[1:]):
        # both quoted (>=30 bars) on same session
        m = (closes[a].notna() & closes[b].notna()
             & bars[a].fillna(0).ge(30) & bars[b].fillna(0).ge(30))
        if m.sum() < 50:
            continue
        sp = (closes.loc[m, a] - closes.loc[m, b]) / 5e-7
        pairs.append({
            "near": a, "far": b, "n_sessions": int(m.sum()),
            "first": str(m.index[m].min().date()), "last": str(m.index[m].max().date()),
            "pct_near_below_far": float(100 * (sp < 0).mean()),
            "median_spread_ticks": float(sp.median()),
            "median_spread_bp_of_price": float(
                1e4 * (sp * 5e-7 / closes.loc[m, a]).median()),
            "min_spread_ticks": float(sp.min()), "max_spread_ticks": float(sp.max())})
    res["quarterly_pair_spreads"] = pairs
    allpct = [p["pct_near_below_far"] for p in pairs]
    res["summary"] = {
        "n_pairs_measured": len(pairs),
        "pairs_with_near_below_far_ge95pct": int(sum(x >= 95 for x in allpct)),
        "pairs_with_any_near_above_far": int(sum(x < 100 for x in allpct)),
        "min_pct_near_below_far": float(min(allpct)) if allpct else None,
        "median_median_spread_ticks": float(np.median([p["median_spread_ticks"] for p in pairs]))}

    # ---- roll events: gap + liquidity migration ----
    held = held.sort_values("session_date").reset_index(drop=True)
    switches = held[held["held"] != held["held"].shift()].iloc[1:]  # skip first
    rolls = []
    for i, row in switches.iterrows():
        new = row["held"]
        old = held.loc[i - 1, "held"]
        rdate = pd.Timestamp(row["session_date"])
        prevd = pd.Timestamp(held.loc[i - 1, "session_date"])
        # Roll gap = same-session calendar spread at the LAST session before the
        # switch where BOTH contracts have closes (sell old / buy new at the
        # same close — the economically correct carry cost). close-to-close
        # across the switch would mix in the old contract's final partial
        # session (it ceases trading 09:16 CT two business days before the 3rd
        # Wednesday) and is NOT used.
        both_ok = (closes[old].notna() & closes[new].notna()) if (
            old in closes.columns and new in closes.columns) else pd.Series(dtype=bool)
        true_idx = both_ok.index[both_ok.values] if len(both_ok) else pd.DatetimeIndex([])
        true_idx = true_idx[true_idx <= rdate]
        t_last = true_idx.max() if len(true_idx) else None
        if t_last is not None:
            old_close = float(closes.loc[t_last, old])
            new_close = float(closes.loc[t_last, new])
            gap_ticks = (new_close - old_close) / 5e-7
            gap_pct = new_close / old_close - 1
        else:
            old_close = new_close = np.nan
            gap_ticks = gap_pct = np.nan
        # liquidity migration around switch: old/new volume ±10 sessions
        win = pd.date_range(rdate - pd.Timedelta(days=16), rdate + pd.Timedelta(days=16))
        vold = vols.loc[vols.index.isin(win), old] if old in vols.columns else None
        vnew = vols.loc[vols.index.isin(win), new] if new in vols.columns else None
        mig = {}
        if vold is not None and vnew is not None:
            both = pd.DataFrame({"old": vold, "new": vnew}).dropna()
            both = both[(both["old"] > 0) | (both["new"] > 0)]
            if len(both):
                cross_idx = both.index[both["new"] > both["old"]]
                first_cross = cross_idx.min() if len(cross_idx) else None
                mig = {"first_session_new_vol_gt_old": (
                            str(first_cross.date()) if first_cross is not None else None),
                       "cross_days_before_old_expiry": (
                           int((pd.Timestamp(exp[old]) - first_cross).days)
                           if first_cross is not None else None),
                       "switch_days_before_old_expiry": int(
                           (pd.Timestamp(exp[old]) - rdate).days),
                       "old_vol_last_common": float(both["old"].iloc[-1]),
                       "new_vol_last_common": float(both["new"].iloc[-1])}
        exp_old = pd.Timestamp(exp[old])
        exp_new = pd.Timestamp(exp[new])
        dte = (exp_new - exp_old).days
        rolls.append({
            "switch_session": str(rdate.date()), "old": old, "new": new,
            "gap_measured_on": str(t_last.date()) if t_last is not None else None,
            "gap_ticks": (float(gap_ticks) if np.isfinite(gap_ticks) else None),
            "gap_pct": (float(gap_pct) if np.isfinite(gap_pct) else None),
            "old_expiry": exp[old], "new_expiry": exp[new], "days_between_expiries": dte,
            "gap_ann_pct_cip": (float(100 * gap_pct * 365.0 / dte)
                                if dte and np.isfinite(gap_pct) else None),
            **mig})
    res["rolls"] = rolls
    gaps = [r["gap_ticks"] for r in rolls if r["gap_ticks"] is not None]
    res["roll_summary"] = {
        "n_rolls": len(rolls),
        "n_rolls_gap_measured": len(gaps),
        "positive_gap_rolls": int(sum(g > 0 for g in gaps)),
        "negative_gap_rolls": int(sum(g <= 0 for g in gaps)),
        "median_gap_ticks": float(np.median(gaps)),
        "min_gap_ticks": float(min(gaps)), "max_gap_ticks": float(max(gaps)),
        "median_gap_pct": float(np.median([r["gap_pct"] for r in rolls
                                           if r["gap_pct"] is not None])),
        "median_gap_ann_pct": float(np.median([r["gap_ann_pct_cip"] for r in rolls
                                               if r["gap_ann_pct_cip"] is not None])),
        "gap_definition": "same-session close spread new-minus-old at last "
                          "both-traded session before the k=5 volume switch",
        "switch_before_old_delivery_all": all(
            pd.Timestamp(r["switch_session"]) <= pd.Timestamp(r["old_expiry"])
            for r in rolls)}

    # gap by year
    gy = {}
    for r in rolls:
        if r["gap_ann_pct_cip"] is None:
            continue
        y = r["switch_session"][:4]
        gy.setdefault(y, []).append(r["gap_ann_pct_cip"])
    res["gap_ann_pct_by_year"] = {y: {"median": float(np.median(v)),
                                      "n": len(v)} for y, v in sorted(gy.items())}

    # ---- CIP: implied JPY short rate vs US 3m bill ----
    tb = L.load_fred("FRED_DTB3", "latest")
    tb["month"] = tb["obs"].dt.to_period("M")
    tbm = tb.groupby("month")["value"].mean()
    rows = []
    for r in rolls:
        m = pd.Period(r["switch_session"][:7], freq="M")
        usd3m = float(tbm.get(m, np.nan)) if m in tbm.index else np.nan
        if np.isfinite(usd3m) and r["gap_ann_pct_cip"] is not None:
            rows.append({"switch": r["switch_session"],
                         "us_tb3m_pct": usd3m,
                         "implied_rate_diff_ann_pct": r["gap_ann_pct_cip"],
                         "implied_jpy_short_rate_pct": usd3m - r["gap_ann_pct_cip"]})
    res["cip"] = {
        "method": "annualized quarterly roll gap at PIT volume-crossover switch vs "
                  "FRED DTB3 (3m T-bill discount, monthly avg, latest snapshot 2026-09-30); "
                  "implied JPY rate = US rate - implied USD-over-JPY forward premium",
        "vintage_caveat": "ALFRED vintages in store are YEAR-END snapshots only "
                          "(2020..2025 + 2026-09-30 latest); this is descriptive CIP "
                          "context, NOT a PIT-strict series",
        "n_rolls_matched": len(rows),
        "rows": rows,
        "implied_jpy_rate_median_by_year": {}}
    byy2 = {}
    for x in rows:
        byy2.setdefault(x["switch"][:4], []).append(x["implied_jpy_short_rate_pct"])
    res["cip"]["implied_jpy_rate_median_by_year"] = {
        y: float(np.median(v)) for y, v in sorted(byy2.items())}

    # stability check with a year-end vintage (2022-12-31)
    tb22 = L.load_fred("FRED_DTB3", "2022-12-31")
    if len(tb22):
        tb22 = tb22[tb22["obs"] <= "2022-12-01"]
        tb22m = tb22.groupby(tb22["obs"].dt.to_period("M"))["value"].mean()
        alt = []
        for r in rolls:
            m = pd.Period(r["switch_session"][:7], freq="M")
            if m in tb22m.index and r["gap_ann_pct_cip"] is not None:
                alt.append(tb22m[m] - r["gap_ann_pct_cip"])
        if alt:
            res["cip"]["alt_vintage_2022_12_31_implied_jpy"] = {
                "n": len(alt), "median_pct": float(np.median(alt))}

    # ---- OI migration (2023-10+ only) ----
    stats = L.load_statistics_6j()
    oi = stats[stats["stat_type"] == 9].copy()
    oi["d"] = pd.to_datetime(oi["ref_date"])
    piv = oi.pivot_table(index="d", columns="raw_symbol", values="quantity")
    regmap = dict(zip(reg["symbol"] + "|" + reg["year"].astype(str), reg["contract"]))
    piv = piv.rename(columns={c: c for c in piv.columns})
    oi_rolls = []
    for r in rolls:
        rd = pd.Timestamp(r["switch_session"])
        if rd < pd.Timestamp("2023-10-01"):
            continue
        olds = r["old"].split("_")[0]
        news = r["new"].split("_")[0]
        win = pd.date_range(rd - pd.Timedelta(days=20), rd + pd.Timedelta(days=20))
        if olds not in piv.columns or news not in piv.columns:
            continue
        sub = piv.loc[piv.index.isin(win), [olds, news]].dropna()
        if len(sub) < 5:
            continue
        cross = sub.index[sub[news] > sub[olds]]
        oi_rolls.append({
            "switch": r["switch_session"], "old": r["old"], "new": r["new"],
            "first_oi_crossover": str(cross.min().date()) if len(cross) else None,
            "oi_crossover_before_volume_switch": bool(
                len(cross) and cross.min() < rd),
            "n_days": int(len(sub))})
    res["oi_migration_2023plus"] = oi_rolls

    L.jdump(res, OUT)
    print("A3 complete ->", OUT)


if __name__ == "__main__":
    main()
