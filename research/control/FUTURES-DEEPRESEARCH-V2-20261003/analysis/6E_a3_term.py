"""A3 — 6E term structure + roll anatomy 2020-2026 (DEEP-6E).

All quarterly rolls measured (2020-2026, ~27 under the declared calendar
rule): roll gaps vs CIP-predicted gaps (SOFR minus ESTR), volume-crossover
and OI-crossover timing, liquidity migration paths, thin-window counts,
serial vs quarterly book anatomy, calendar-spread-instrument volume share,
and what an unadjusted chain would embed per year. OI only from 2023-10
(statistics dataset) with publication-lag disclosure. Descriptive only.
"""
from __future__ import annotations

import importlib
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
L = importlib.import_module("6E_deep_lib")

OUT = os.path.join(L.HERE, "6E_a3_term.json")


def main():
    res = {"schema": "6E_a3_term@1", "window": "2020-01-02..2026-09-30"}
    sess = pd.read_parquet(os.path.join(L.CACHE, "6e_sessions.parquet"))
    reg = pd.read_json(os.path.join(L.CACHE, "contract_registry.json"))
    held_cal = pd.read_parquet(os.path.join(L.CACHE, "held_calendar.parquet"))
    held_vol = pd.read_parquet(os.path.join(L.CACHE, "held_volume_k5.parquet"))

    closes = sess.pivot_table(index="session_date", columns="contract", values="close")
    vols = sess.pivot_table(index="session_date", columns="contract", values="volume")
    exp = reg.set_index("contract")["expiry"].to_dict()

    # rate differential (SOFR - ESTR), daily
    sofr = L.load_sofr().set_index("date")["SOFR"]
    estr = L.load_estr().set_index("date")["value"]
    diff = (sofr / 100.0 - estr / 100.0).dropna()

    # ---- roll events under the declared calendar rule ----
    hc = held_cal.sort_values("session_date").reset_index(drop=True)
    hc["prev"] = hc["held"].shift()
    rolls = hc[hc["held"].ne(hc["prev"]) & hc["prev"].notna()].copy()
    hv = held_vol.sort_values("session_date").reset_index(drop=True)
    hv["prev"] = hv["held"].shift()
    vol_switch = hv[hv["held"].ne(hv["prev"]) & hv["prev"].notna()]
    vol_switch_map = dict(zip(vol_switch["prev"], vol_switch["session_date"]))

    # OI crossover (2023-10+): last OI stat per (contract, ref_date)
    stats = L.load_statistics_6e()
    oi = stats[stats["stat_type"] == 9].copy()
    oi["contract"] = oi["raw_symbol"] + "_" + (
        2020 + oi["raw_symbol"].str[-1].astype(int)).astype(str)
    # dedupe: keep latest publication per ref_date; quantity = OI
    oi_daily = oi.groupby(["contract", "ref_date"]).agg(
        oi=("quantity", "last"), pub=("dt", "max")).reset_index()
    oi_wide = oi_daily.pivot_table(index="ref_date", columns="contract", values="oi")

    rows = []
    for r in rolls.itertuples():
        old, new, dstr = r.prev, r.held, r.session_date
        if old not in closes.columns or new not in closes.columns:
            continue
        if old not in exp or new not in exp:
            continue
        exp_old = pd.Timestamp(exp[old])
        exp_new = pd.Timestamp(exp[new])
        d_exp = (exp_new - exp_old).days
        # gap at roll session: new close - old close
        co = closes.at[dstr, old] if dstr in closes.index else np.nan
        cn = closes.at[dstr, new] if dstr in closes.index else np.nan
        gap_px = cn - co
        gap_ticks = gap_px / L.TICK
        gap_pct = gap_px / co * 100
        gap_ann = gap_pct / (d_exp / 365.0)
        # CIP prediction at roll date: (SOFR-ESTR) x d_exp/360
        rd = pd.Timestamp(dstr)
        near = diff.index.asof(rd)
        rd_diff = float(diff.loc[near]) if near is not None else np.nan
        cip_gap_pct = rd_diff * (d_exp / 360.0) * 100
        # volume crossover date for this old contract
        vol_x = vol_switch_map.get(old)
        # OI crossover: first ref_date where new OI > old OI
        oi_x = None
        if str(rd) >= "2023-10-01" and old in oi_wide.columns and new in oi_wide.columns:
            pair = oi_wide[[old, new]].dropna()
            cross = pair[pair[new] > pair[old]]
            if len(cross):
                oi_x = str(cross.index[0])
        # thin-window: sessions from prev delivery-month start.. roll where
        # old volume < 10k (the declared rule's thin tail)
        win = closes.index[
            (pd.to_datetime(closes.index) >= exp_old.replace(day=1) - pd.DateOffset(months=1))
            & (pd.to_datetime(closes.index) < exp_old.replace(day=1))]
        old_v = vols.loc[[d for d in win if d in vols.index], old] \
            if len(win) else pd.Series(dtype=float)
        rows.append({
            "roll_session": str(dstr), "old": old, "new": new,
            "expiry_old": str(exp_old.date()), "days_to_expiry": int(
                (exp_old - pd.Timestamp(dstr)).days),
            "gap_ticks": float(gap_ticks), "gap_pct": float(gap_pct),
            "gap_annualized_pct": float(gap_ann),
            "cip_gap_pct": float(cip_gap_pct),
            "rate_diff_sofr_estr_pct": float(rd_diff * 100),
            "front_close": float(co),
            "vol_crossover_session": str(vol_x) if vol_x else None,
            "oi_crossover_ref_date": oi_x,
            "old_vol_roll_day": float(vols.at[dstr, old]) if dstr in vols.index else None,
            "new_vol_roll_day": float(vols.at[dstr, new]) if dstr in vols.index else None,
        })
    rdf = pd.DataFrame(rows)
    rdf["gap_minus_cip_ticks"] = (rdf["gap_pct"] - rdf["cip_gap_pct"]) / 0.005
    ok = rdf.dropna(subset=["gap_ticks"])
    res["n_rolls_measured"] = int(len(ok))
    res["rolls"] = ok.to_dict(orient="records")
    res["gap_summary"] = {
        "n": int(len(ok)),
        "n_positive": int((ok["gap_ticks"] > 0).sum()),
        "median_ticks": float(ok["gap_ticks"].median()),
        "p05_ticks": float(ok["gap_ticks"].quantile(.05)),
        "p95_ticks": float(ok["gap_ticks"].quantile(.95)),
        "min_ticks": float(ok["gap_ticks"].min()), "max_ticks": float(ok["gap_ticks"].max()),
        "median_annualized_pct": float(ok["gap_annualized_pct"].median()),
        "corr_gap_vs_cip": float(ok[["gap_pct", "cip_gap_pct"]].corr().iloc[0, 1]),
        "mean_gap_minus_cip_ticks": float(ok["gap_minus_cip_ticks"].mean()),
        "median_gap_minus_cip_ticks": float(ok["gap_minus_cip_ticks"].median()),
        "cip_caveat": "SOFR/ESTR are latest-vintage daily series, not "
                      "point-in-time (ALFRED year-end vintages exist on disk "
                      "but are annual); ESTR essentially unrevised; SOFR "
                      "revisions negligible per NY Fed methodology. Rate "
                      "diff is the roll-date nearest observation.",
    }
    # sign agreement with rate differential
    same = ((ok["gap_ticks"] > 0) & (ok["rate_diff_sofr_estr_pct"] > 0)) | (
        (ok["gap_ticks"] < 0) & (ok["rate_diff_sofr_estr_pct"] < 0))
    res["gap_summary"]["sign_agreement_gap_vs_ratediff"] = f"{int(same.sum())}/{len(ok)}"

    # ---- volume vs OI crossover timing (2023-10+ subset) ----
    sub = ok[ok["oi_crossover_ref_date"].notna()].copy()
    lag_rows = []
    for r in sub.itertuples():
        vx = pd.to_datetime(r.vol_crossover_session)
        ox = pd.to_datetime(r.oi_crossover_ref_date)
        if pd.notna(vx) and pd.notna(ox):
            lag_rows.append({"old": r.old, "vol_x": str(vx.date()),
                             "oi_x": str(ox.date()),
                             "oi_minus_vol_days": int((ox - vx).days)})
    res["oi_vs_vol_crossover"] = {
        "n": len(lag_rows), "rows": lag_rows,
        "publication_lag_caveat": "GLBX OI statistic is published the "
                                  "following morning; a PIT OI rule must "
                                  "consume it with that lag (adapter law).",
    }

    # ---- liquidity migration path: new/(new+old) volume, T-10..roll ----
    path_rows = []
    for r in rolls.itertuples():
        old, new, dstr = r.prev, r.held, r.session_date
        if old not in vols.columns or new not in vols.columns:
            continue
        exp_old = pd.Timestamp(exp.get(old))
        if pd.isna(exp_old):
            continue
        idx = pd.DatetimeIndex(pd.to_datetime(vols.index))
        winmask = (idx <= exp_old) & (idx >= exp_old - pd.Timedelta(days=25))
        w = vols.loc[winmask, [old, new]]
        for d, row in w.iterrows():
            o, n = row[old], row[new]
            if pd.isna(o) and pd.isna(n):
                continue
            path_rows.append({
                "old": old, "days_to_expiry": int((exp_old - pd.Timestamp(d)).days),
                "new_share_pct": float(n / (n + o) * 100) if (n + o) > 0 else None})
    pdf = pd.DataFrame(path_rows)
    med_path = pdf.groupby("days_to_expiry")["new_share_pct"].median()
    n_path = pdf.groupby("days_to_expiry")["new_share_pct"].size()
    res["migration_median_new_volume_share"] = {
        str(int(k)): {"median_new_share_pct": float(v), "n_rolls": int(n_path[k])}
        for k, v in med_path.items() if 0 <= k <= 25}
    res["migration_note"] = (
        "quarterly expiries are Mondays (32/33; the Friday is 2023-06 "
        "Juneteenth-shifted), so calendar distances 1/2 carry ~1 roll only "
        "- read the Friday (d=3) and Thursday (d=4) buckets: the spot "
        "volume crossover lands on the Friday before expiry week")

    # ---- thin windows under the declared rule ----
    thin = []
    for r in rolls.itertuples():
        old, dstr = r.prev, r.session_date
        if old not in vols.columns:
            continue
        exp_old = pd.Timestamp(exp.get(old))
        if pd.isna(exp_old):
            continue
        idx = pd.DatetimeIndex(pd.to_datetime(vols.index))
        winmask = (idx < exp_old.replace(day=1)) & (
            idx >= exp_old.replace(day=1) - pd.Timedelta(days=14))
        w = vols.loc[winmask, old].dropna()
        thin.append({"old": old, "sessions_in_final_14_pre_month": int(len(w)),
                     "n_below_10k": int((w < 10000).sum()),
                     "n_below_25k": int((w < 25000).sum())})
    res["declared_rule_thin_windows"] = {
        "n_rolls": len(thin),
        "total_sessions_below_10k": int(sum(t["n_below_10k"] for t in thin)),
        "total_sessions_below_25k": int(sum(t["n_below_25k"] for t in thin)),
        "worst": sorted(thin, key=lambda t: -t["n_below_10k"])[:6],
    }

    # ---- serial vs quarterly anatomy ----
    q = reg[reg["quarterly"]]
    s = reg[~reg["quarterly"]]
    sessq = sess[sess["contract"].isin(set(q["contract"]))]
    sesss = sess[sess["contract"].isin(set(s["contract"]))]
    sv = sesss.groupby("contract")["volume"].sum()
    qv = sessq.groupby("contract")["volume"].sum()
    res["serial_vs_quarterly"] = {
        "n_quarterly_contracts": int(len(q)), "n_serial_contracts": int(len(s)),
        "serial_total_volume": float(sv.sum()), "quarterly_total_volume": float(qv.sum()),
        "serial_share_of_outright_volume_pct": float(sv.sum() / (sv.sum() + qv.sum()) * 100),
        "serial_median_daily_volume_when_active": float(
            sesss.groupby("contract")["volume"].median().median()),
        "serial_max_daily_volume": float(sesss.groupby(["contract", "session_date"])["volume"].sum().max()),
        "quarterly_front_median_daily": float(
            sessq.groupby("contract")["volume"].median().median()),
        "n_serial_with_median_ge_1k": int((sesss.groupby("contract")["volume"].median() >= 1000).sum()),
    }
    # when are serials active: distance from own expiry of last active session
    s2 = s.set_index("contract")
    last_act = sesss.groupby("contract")["session_date"].max()
    dist = []
    for c, d in last_act.items():
        if c in s2.index:
            dist.append((pd.Timestamp(s2.loc[c, "expiry"]) - pd.Timestamp(d)).days)
    res["serial_vs_quarterly"]["median_days_before_expiry_last_active"] = float(np.median(dist))
    res["serial_vs_quarterly"]["serial_last_active_within_5d_of_expiry"] = int(
        sum(1 for d in dist if d <= 5))

    # ---- calendar-spread instrument volume (from raw files) ----
    census = L.load_all_symbol_census()
    res["calendar_spread_instruments"] = {
        era: {"spread_rows": v["rows_calendar_spread_instr"],
              "outright_rows": v["rows_outright"],
              "spread_row_share_pct": float(
                  v["rows_calendar_spread_instr"] /
                  (v["rows_calendar_spread_instr"] + v["rows_outright"]) * 100)}
        for era, v in census.items()}
    res["stray_symbol_rows"] = {e: v["stray_rows"] for e, v in census.items()}

    # ---- unadjusted-chain embedded drift per year ----
    yr = ok.copy()
    yr["year"] = pd.to_datetime(yr["roll_session"]).dt.year
    emb = yr.groupby("year").agg(n_rolls=("gap_ticks", "size"),
                                 sum_gap_pct=("gap_pct", "sum"),
                                 mean_gap_ann_pct=("gap_annualized_pct", "mean"))
    res["unadjusted_chain_embedding_per_year"] = {
        str(y): {"n_rolls": int(r["n_rolls"]), "sum_gap_pct": float(r["sum_gap_pct"]),
                 "mean_gap_ann_pct": float(r["mean_gap_ann_pct"])}
        for y, r in emb.iterrows()}
    L.jdump(res, OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
