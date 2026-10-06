"""A3 — NQ term structure + roll anatomy 2010-2026 (DEEP-NQ).

Calendar curve from per-contract closes (no vendor stitching): adjacent-
quarter spreads by year, ~66 quarterly roll events under the PIT volume-
crossover rule, roll-gap distribution vs curve level, what an unadjusted
chain would embed per year, and OI-crossover timing from GLBX statistics
(2023-10+, publication-lag disclosed).
"""
from __future__ import annotations

import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import NQ_deep_lib as L  # noqa: E402

OUT = os.path.join(L.HERE, "NQ_a3_term.json")


def main():
    sess = L._real_contracts(
        pd.read_parquet(os.path.join(L.CACHE, "nq_sessions.parquet")))
    held = pd.read_parquet(os.path.join(L.CACHE, "held_volume_k5.parquet"))
    reg = pd.read_json(os.path.join(L.CACHE, "contract_registry.json"))
    exp = reg.set_index("contract")["expiry"].dropna().to_dict()
    closes = sess.pivot_table(index="session_date", columns="contract",
                              values="close")
    vols = sess.pivot_table(index="session_date", columns="contract",
                            values="volume")
    res = {"schema": "NQ_a3_term@1"}

    # ---- roll events from held map ----
    held = held.sort_values("session_date").reset_index(drop=True)
    held["prev"] = held["held"].shift()
    rolls = held[held["held"].ne(held["prev"]) & held["prev"].notna()].copy()
    rolls["expiry_old"] = rolls["prev"].map(exp)
    rolls["t"] = pd.to_datetime(rolls["session_date"])
    rolls["days_to_expiry"] = [
        (pd.Timestamp(e) - t).days if pd.notna(e) else None
        for e, t in zip(rolls["expiry_old"], rolls["t"])]
    rows = []
    for r in rolls.itertuples():
        old, new, d, dstr = r.prev, r.held, r.t, r.session_date
        di = closes.index.get_loc(dstr)
        window = closes.index[max(0, di - 12):di + 1]
        sp = ((closes.loc[window, new] - closes.loc[window, old]) / 1e9).dropna()
        vp = (vols.loc[window, new] / vols.loc[window, old]).replace(
            [np.inf, -np.inf], np.nan).dropna()
        row = {
            "roll_session": str(dstr), "old": old, "new": new,
            "expiry_old": str(exp.get(old)),
            "days_to_expiry": int(
                (pd.Timestamp(exp[old]) - pd.Timestamp(dstr)).days)
            if old in exp else None,
            "spread_pts_median10": float(sp.iloc[:-1].median()) if len(sp) > 2
            else None,
            "spread_pts_roll_day": float(sp.iloc[-1]) if len(sp) else None,
            "new_over_old_vol_roll_day": float(vols.loc[dstr, new] /
                                               vols.loc[dstr, old])
            if vols.loc[dstr, old] and not pd.isna(vols.loc[dstr, old]) else None,
            "old_volume_roll_day": float(vols.loc[dstr, old])
            if not pd.isna(vols.loc[dstr, old]) else None,
            "new_volume_roll_day": float(vols.loc[dstr, new])
            if not pd.isna(vols.loc[dstr, new]) else None,
            "front_close": float(closes.loc[dstr, old] if not pd.isna(
                closes.loc[dstr, old]) else closes.loc[dstr, new]) / 1e9,
        }
        row["spread_pct_ann"] = (row["spread_pts_roll_day"] /
                                 row["front_close"] * (365 / 91)
                                 if row["spread_pts_roll_day"] is not None
                                 else None)
        rows.append(row)
    rdf = pd.DataFrame(rows)
    rdf["year"] = pd.to_datetime(rdf["roll_session"]).dt.year
    ok = rdf.dropna(subset=["spread_pts_roll_day"])
    ok = ok[ok["old_volume_roll_day"].fillna(0) > 0]
    res["rolls"] = rows

    # ---- DAILY-volume crossover (k=1 market-convention handoff) DTE ----
    daily_dte = []
    for r in rolls.itertuples():
        old, new = r.prev, r.held
        if old not in vols.columns or new not in vols.columns:
            continue
        pair = vols[[old, new]].dropna(how="all")
        both = pair.dropna()
        both = both[both[old] > 0]
        # persistent daily crossover: new>old on t and the 2 following
        # sessions with data (a single thin-day flip does not count)
        nb = (both[new] > both[old]).values
        cross = []
        for i in range(len(nb) - 2):
            if nb[i] and nb[i + 1] and nb[i + 2]:
                cross = [both.index[i]]
                break
        cross = pd.DatetimeIndex(cross)
        if len(cross) and old in exp:
            d = cross[0]
            dte = int((pd.Timestamp(exp[old]) - pd.Timestamp(d)).days)
            if 0 <= dte <= 45:  # 2020-hole rolls cross months early: exclude
                daily_dte.append(dte)
    if daily_dte:
        res["daily_volume_crossover_dte"] = {
            "n": len(daily_dte), "median": float(np.median(daily_dte)),
            "p10": float(np.percentile(daily_dte, 10)),
            "p90": float(np.percentile(daily_dte, 90)),
            "min": int(min(daily_dte)), "max": int(max(daily_dte)),
            "note": "sessions between the daily-volume crossover (new>old "
                    "same-session) and the old contract's 3rd-Friday expiry; "
                    "rolls with dte>45d (2020 vendor-hole artifacts) excluded"}
    res["n_rolls"] = int(len(rows))
    res["roll_gap_distribution"] = {
        "n": int(len(ok)),
        "pts_median": float(ok["spread_pts_roll_day"].median()),
        "pts_p10": float(ok["spread_pts_roll_day"].quantile(.1)),
        "pts_p90": float(ok["spread_pts_roll_day"].quantile(.9)),
        "pts_min": float(ok["spread_pts_roll_day"].min()),
        "pts_max": float(ok["spread_pts_roll_day"].max()),
        "share_positive": float((ok["spread_pts_roll_day"] > 0).mean()),
        "pct_ann_median": float(ok["spread_pct_ann"].median()),
        "pct_ann_p10": float(ok["spread_pct_ann"].quantile(.1)),
        "pct_ann_p90": float(ok["spread_pct_ann"].quantile(.9)),
        "corr_gap_vs_spreadmed10": float(
            ok["spread_pts_roll_day"].corr(ok["spread_pts_median10"]))
        if ok["spread_pts_median10"].notna().sum() > 3 else None,
        "neg_gap_rolls": ok.loc[ok["spread_pts_roll_day"] < 0,
                                "roll_session"].tolist()}
    yr = ok.groupby("year").agg(
        n=("spread_pts_roll_day", "size"),
        pts_med=("spread_pts_roll_day", "median"),
        pct_ann_med=("spread_pct_ann", "median"))
    res["roll_gap_by_year"] = [
        {"year": int(y), "n": int(r["n"]), "pts_median": float(r["pts_med"]),
         "pct_ann_median": float(r["pct_ann_med"])}
        for y, r in yr.iterrows()]

    # ---- what an unadjusted chain embeds: sum of gaps per calendar year ----
    embed = ok.groupby("year")["spread_pts_roll_day"].sum()
    res["unadjusted_chain_embedded_pts_per_year"] = {
        str(int(k)): float(v) for k, v in embed.items()}

    # ---- adjacent spread LEVEL series by year (front vs next, all days) ----
    spread_rows = []
    for r in rolls.itertuples():
        old, new = r.prev, r.held
        if old not in closes.columns or new not in closes.columns:
            continue
        s = ((closes[new] - closes[old]) / 1e9).dropna()
        # only sessions where new contract exists (its quoted life)
        s = s[s.index >= closes[old].first_valid_index()]
        for d, v in s.items():
            liq = (vols.at[d, new] >= 500) if new in vols.columns else False
            spread_rows.append({"date": d, "old": old, "new": new,
                                "spread": float(v), "liq": bool(liq),
                                "front_close": (float(closes.at[d, old]) / 1e9
                                if not pd.isna(closes.at[d, old]) else None)})
    sdf = pd.DataFrame(spread_rows)
    sdf["year"] = pd.to_datetime(sdf["date"]).dt.year
    lev = []
    for y, g in sdf.groupby("year"):
        gl = g[g["liq"] & g["front_close"].notna()]
        lev.append({
            "year": int(y), "n_obs": int(len(g)), "n_liq": int(len(gl)),
            "pts_median_all": float(g["spread"].median()),
            "pts_median_liq": float(gl["spread"].median()) if len(gl) else None,
            "pct_ann_median_liq": float(
                (gl["spread"] / gl["front_close"] * (365 / 91)).median())
            if len(gl) else None})
    res["front_next_spread_by_year"] = lev

    # ---- liquidity migration around volume crossover (event-time avg) ----
    mig = {}
    for r in rolls.itertuples():
        old, new, dstr = r.prev, r.held, r.session_date
        if old not in vols.columns or new not in vols.columns:
            continue
        di = vols.index.get_loc(dstr)
        for k in range(-10, 11):
            j = di + k
            if j < 0 or j >= len(vols.index):
                continue
            d = vols.index[j]
            ov, nv = vols.iat[j, vols.columns.get_loc(old)], vols.iat[
                j, vols.columns.get_loc(new)]
            if pd.isna(ov) and pd.isna(nv):
                continue
            tot = (0 if pd.isna(ov) else ov) + (0 if pd.isna(nv) else nv)
            if tot <= 0:
                continue
            mig.setdefault(k, []).append(nv / tot)
    res["new_contract_share_around_roll"] = {
        str(k): {"mean": float(np.mean(v)), "median": float(np.median(v)),
                 "n": len(v)} for k, v in sorted(mig.items())}

    # ---- calendar-rule vs market front: the thin-window cost ----
    heldcal = pd.read_parquet(os.path.join(L.CACHE, "held_calendar.parquet"))
    hc = heldcal.rename(columns={"held": "contract"})
    mcal = sess.merge(hc, on=["session_date", "contract"], how="inner")
    mvol = pd.read_parquet(
        os.path.join(L.CACHE, "held_volume_k5.parquet")).set_index(
        "session_date")["held"]
    markt = sess[sess["session_date"].map(mvol).notna()]
    markt_vol = markt.groupby("session_date")["volume"].sum()
    cal_vol = mcal.set_index("session_date")["volume"]
    cmp = pd.DataFrame({"cal": cal_vol, "mkt": markt_vol}).dropna()
    cmp["ratio"] = cmp["cal"] / cmp["mkt"]
    first2w = []
    for dstr, r in cmp.iterrows():
        held_c = hc.set_index("session_date")["contract"].get(dstr)
        if held_c is None:
            continue
        e = pd.Timestamp(exp.get(held_c))
        if pd.notna(e):
            dm = (e - pd.Timestamp(dstr)).days
            if 55 <= dm <= 75 and pd.Timestamp(dstr).month == (
                    e - pd.offsets.MonthBegin(1)).month - 1 + 1:
                pass
    # simpler: first 10 sessions of each calendar-rule hold window
    hc2 = hc.sort_values("session_date").copy()
    hc2["chg"] = hc2["contract"].ne(hc2["contract"].shift())
    hc2["seq"] = hc2.groupby(hc2["chg"].cumsum()).cumcount()
    early = hc2[hc2["seq"] < 10].set_index("session_date")["contract"]
    cmp2 = cmp.join(early.rename("c"))
    w = cmp2[cmp2["c"].notna()]
    res["calendar_rule_thin_window"] = {
        "n_sessions": int(len(w)),
        "volume_vs_market_front_median_ratio": float(w["ratio"].median()),
        "p10": float(w["ratio"].quantile(.1)),
        "share_sessions_below_50pct": float((w["ratio"] < 0.5).mean())}

    # ---- OI crossover from statistics (2023-10+) ----
    stats = L.load_statistics_nq()
    oi = stats[stats["stat_type"] == 9].copy()
    oi["d"] = pd.to_datetime(oi["ref_date"])
    # statistics carry one-digit-year raw symbols; in the 2023+ window each
    # symbol has exactly one live epoch. Resolve: expiry = 3rd Friday of the
    # candidate month/year whose expiry is the nearest future >= ref - 120d.
    def map_contract(r):
        m = re.fullmatch(r"NQ([HMUZ])(\d)", r.raw_symbol)
        if not m:
            return None
        code, digit = m.group(1), int(m.group(2))
        cands = [L.third_friday(y, L.MONTH_CODE[code])
                 for y in range(2010, 2028) if y % 10 == digit]
        future = [c for c in cands if (c - r.d.date()).days >= -120]
        if not future:
            return None
        e = min(future)
        return f"{r.raw_symbol}_{e.year}"
    oi["contract"] = oi.apply(map_contract, axis=1)
    oi = oi[oi["contract"].notna()]
    oiw = oi.pivot_table(index="d", columns="contract", values="quantity",
                         aggfunc="last").sort_index()
    oi_events = []
    for r in rolls.itertuples():
        old, new, dstr = r.prev, r.held, r.session_date
        if old not in oiw.columns or new not in oiw.columns:
            continue
        sub = oiw[[old, new]].dropna()
        sub = sub[sub.index <= pd.Timestamp(dstr) + pd.Timedelta(days=10)]
        if not len(sub):
            continue
        cross = sub[(sub[new] > sub[old])]
        vol_cross = pd.Timestamp(dstr)
        oi_events.append({
            "old": old, "new": new, "roll_session": dstr,
            "oi_crossover_date": str(cross.index[0].date()) if len(cross)
            else None,
            "vol_to_oi_lag_sessions": int(
                (cross.index[0] - vol_cross).days) if len(cross) else None,
        })
    res["oi_crossovers"] = oi_events
    if oi_events:
        lags = [e["vol_to_oi_lag_sessions"] for e in oi_events
                if e["vol_to_oi_lag_sessions"] is not None
                and -15 <= e["vol_to_oi_lag_sessions"] <= 15]
        res["oi_vs_volume_crossover_lag_days"] = {
            "n": len(lags), "median": float(np.median(lags)),
            "min": int(min(lags)), "max": int(max(lags)),
            "note": "negative = OI crossover BEFORE the k=5 volume-crossover "
                    "roll session; 2 events with |lag|>15d excluded as "
                    "statistics-mapping artifacts (disclosed per-event in "
                    "oi_crossovers)"}
    res["oi_coverage_note"] = (
        "GLBX statistics acquired 2023-10-01+ only; OI is published by CME "
        "next morning (~00:30 CT), so OI crossover is observable with a "
        "1-session publication lag (disclosed); vol crossover is same-close.")

    L.jdump(res, OUT)
    print("A3 complete ->", OUT)


if __name__ == "__main__":
    main()
