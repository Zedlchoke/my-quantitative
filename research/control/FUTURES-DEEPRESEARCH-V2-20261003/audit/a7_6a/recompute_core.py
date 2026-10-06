#!/usr/bin/env python
"""A7-DEEP-6A fresh-context independent recomputation — audit lane, task
FUTURES-DEEPRESEARCH-V2-20261003. READ-ONLY over vendor + nonprice data.

Deliberately INDEPENDENT of the DEEP-6A lane's code (no import of 6A_deep_lib,
no use of 6A_cache): loads the raw ohlcv-1m parquet union directly, rebuilds
the documented held-chain rule from scratch, and recomputes the dossier's
headline numbers. Writes only audit/a7_6a/recompute_core.json.
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
import re
import zoneinfo

import numpy as np
import pandas as pd

DATA = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet"
NONPRICE = "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms"
HERE = os.path.dirname(os.path.abspath(__file__))

CHI, SYD, TYO, SHA, LON = ("America/Chicago", "Australia/Sydney", "Asia/Tokyo",
                           "Asia/Shanghai", "Europe/London")
SCALE = 1_000_000_000.0
TICK = 50_000.0
MC = {"F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
      "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12}
CM = {v: k for k, v in MC.items()}
OUTRIGHT_RE = re.compile(r"^6A([FGHJKMNQUVXZ])(\d)$")
ERAS = [("2020-2021", "2020-01-01", "2021-12-31"),
        ("2022-2023", "2022-01-01", "2023-12-31"),
        ("2024-2026-09", "2024-01-01", "2026-10-01")]


def era_of(d):
    d = pd.Timestamp(d)
    if d <= pd.Timestamp("2021-12-31"):
        return "BF2_2020_21"
    if d <= pd.Timestamp("2023-12-31"):
        return "BF1A_2022_23"
    if d <= pd.Timestamp("2025-12-31"):
        return "BF1B_2024_25"
    if d <= pd.Timestamp("2026-03-31"):
        return "BF1C_2026Q1"
    return "TRIM_2026Q2_09"


def load_raw():
    files = []
    for line in ["AV1B-O1M-6A-BACKFILL2", "AV1R-O1M-6A-BACKFILL", "AV1T-O1M-6A"]:
        files += sorted(glob.glob(f"{DATA}/{line}/*.parquet"))
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    return df.sort_values(["raw_symbol", "dt"]).reset_index(drop=True)


def build_panel(raw):
    """Independent outright-panel + spread split + contaminant exclusion."""
    is_spread = raw["raw_symbol"].str.contains("-")
    spr = raw[is_spread].copy()
    outr = raw[~is_spread].copy()
    good = outr["raw_symbol"].str.fullmatch(r"6A[FGHJKMNQUVXZ]\d")
    contamin = outr[~good].copy()
    outr = outr[good].copy()
    # contract identity: digit -> year 2020+d (window 2020-2026, listings <=2029)
    def contract(sym):
        m = OUTRIGHT_RE.fullmatch(sym)
        code, digit = m.group(1), int(m.group(2))
        return sym, code, 2020 + digit, MC[code]
    ci = outr["raw_symbol"].map(lambda s: contract(s))
    outr["contract"] = [f"{c[0]}_{c[2]}" for c in ci]
    outr["month"] = [c[3] for c in ci]
    outr["year"] = [c[2] for c in ci]
    outr["is_q"] = [c[1] in "HMUZ" for c in ci]
    # CT clock + trade date
    loc = outr["dt"].dt.tz_convert(CHI)
    hhmm = (loc.dt.hour * 60 + loc.dt.minute).astype("int32")
    nd = loc.dt.normalize().values.astype("datetime64[D]")
    nd = nd + np.where(loc.dt.hour >= 17, 1, 0).astype("int64")
    outr["ct_minute"] = hhmm
    outr["session_date"] = pd.DatetimeIndex(nd).date
    outr["syd_min"] = (outr["dt"].dt.tz_convert(SYD).dt.hour * 60 +
                       outr["dt"].dt.tz_convert(SYD).dt.minute).astype("int32")
    outr["tyo_min"] = (outr["dt"].dt.tz_convert(TYO).dt.hour * 60 +
                       outr["dt"].dt.tz_convert(TYO).dt.minute).astype("int32")
    outr["sha_min"] = (outr["dt"].dt.tz_convert(SHA).dt.hour * 60 +
                       outr["dt"].dt.tz_convert(SHA).dt.minute).astype("int32")
    outr["lon_min"] = (outr["dt"].dt.tz_convert(LON).dt.hour * 60 +
                       outr["dt"].dt.tz_convert(LON).dt.minute).astype("int32")
    outr["era"] = pd.to_datetime(outr["session_date"]).map(era_of)
    return outr, spr, contamin


def held_chain(outr):
    """Documented v1 rule w/ quarterly adaptation: hold nearest HMUZ until the
    last session before day-1 of its delivery month; roll at that close."""
    q = outr[outr["is_q"]]
    dates = sorted(q["session_date"].unique())
    dmap = {}
    for d in dates:
        dmap[d] = set(q[q["session_date"] == d]["contract"])
    held, cur = [], None
    for d in dates:
        avail = dmap[d]
        dm = pd.Timestamp(d)
        # candidate: nearest HMUZ whose delivery month start > d
        cands = []
        for c in avail:
            y, m = int(c.split("_")[1]), MC[c[2]]
            if pd.Timestamp(year=y, month=m, day=1) > dm:
                cands.append((pd.Timestamp(year=y, month=m, day=1), c))
        if cands:
            cur = min(cands)[1]
        else:
            cur = None
        held.append(cur)
    out = pd.DataFrame({"session_date": list(dates), "held": held}).dropna()
    return out.reset_index(drop=True)


def main():
    raw = load_raw()
    res = {"raw_rows": int(len(raw)),
           "first_bar": str(raw["dt"].min()), "last_bar": str(raw["dt"].max())}
    outr, spr, contamin = build_panel(raw)
    res["outright_rows"] = int(len(outr))
    res["spread_rows"] = int(len(spr))
    res["contaminant"] = {
        "n_bars": int(len(contamin)),
        "symbols": contamin["raw_symbol"].unique().tolist(),
        "instrument_ids": sorted(contamin["instrument_id"].unique().tolist()),
        "span": [str(contamin["dt"].min()), str(contamin["dt"].max())],
        "volume": int(contamin["volume"].sum())}

    # ---- negative price ledger (fresh) ---------------------------------------
    def neg(df):
        return int((df[["open", "high", "low", "close"]] < 0).any(axis=1).sum())
    res["neg_outright"] = neg(outr)
    spr2 = spr.assign(era=pd.to_datetime(
        pd.to_datetime(spr["ts_event"], unit="ns", utc=True)
        .dt.tz_convert(CHI).dt.strftime("%Y-%m-%d")).map(era_of))
    # simpler: recompute session_date for spread era mapping
    locs = pd.to_datetime(spr["ts_event"], unit="ns", utc=True).dt.tz_convert(CHI)
    nds = locs.dt.normalize().values.astype("datetime64[D]") + np.where(
        locs.dt.hour >= 17, 1, 0).astype("int64")
    spr_era = pd.to_datetime(pd.DatetimeIndex(nds).date).map(era_of)
    negbars = (spr[["open", "high", "low", "close"]] < 0).any(axis=1)
    res["neg_spread_total"] = int(negbars.sum())
    res["neg_spread_by_era"] = {
        str(k): int(v) for k, v in negbars.groupby(spr_era).sum().items()}
    res["spread_total_by_era"] = {
        str(k): int(v) for k, v in spr_era.value_counts().items()}

    # ---- held chain + front panel --------------------------------------------
    chain = held_chain(outr)
    chain["session_date"] = pd.to_datetime(chain["session_date"])
    outr["session_date"] = pd.to_datetime(outr["session_date"])
    pairs = set(zip(chain["session_date"], chain["held"]))
    mask = [(d, c) in pairs for d, c in zip(outr["session_date"], outr["contract"])]
    fb = outr[pd.Series(mask, index=outr.index)].sort_values("dt").reset_index(drop=True)
    fb["ret1"] = fb["close"] / fb["close"].shift(1) - 1
    fb.loc[fb["contract"] != fb["contract"].shift(1), "ret1"] = np.nan
    fb["range_t"] = (fb["high"] - fb["low"]) / TICK
    res["chain"] = {
        "n_sessions": int(len(chain)),
        "first": str(chain["session_date"].min().date()),
        "last": str(chain["session_date"].max().date()),
        "n_rolls": int((chain["held"] != chain["held"].shift(1)).sum() - 1)}

    # ---- R1: hub window volume shares per era --------------------------------
    WINDOWS = {
        "sydney_day_0700_1700": ("syd_min", 7 * 60, 17 * 60),
        "tokyo_0900_1500": ("tyo_min", 9 * 60, 15 * 60),
        "shanghai_0930_1000": ("sha_min", 9 * 60 + 30, 10 * 60),
        "london_0800_1630": ("lon_min", 8 * 60, 16 * 60 + 30),
        "us_rth_core_0830_1500_CT": ("ct_minute", 8 * 60 + 30, 15 * 60),
        "us_data_0700_0830_CT": ("ct_minute", 7 * 60, 8 * 60 + 30),
        "evening_1700_2000_CT": ("ct_minute", 17 * 60, 20 * 60),
        "overnight_0000_0600_CT": ("ct_minute", 0, 6 * 60),
    }
    hub = {}
    for name, a, b in ERAS:
        e = fb[(fb["session_date"] >= a) & (fb["session_date"] <= b)]
        tot = float(e["volume"].sum())
        row = {}
        for wname, (col, lo, hi) in WINDOWS.items():
            w = e[(e[col] >= lo) & (e[col] < hi)]
            row[wname] = round(float(w["volume"].sum() / tot * 100), 2)
        hub[name] = row
    res["hub_volume_shares_pct"] = hub

    # U-curve mean |1m ret| by CT hour, 2024-26 era
    e = fb[(fb["session_date"] >= "2024-01-01") & (fb["session_date"] <= "2026-10-01")]
    u = e.groupby(e["ct_minute"] // 60)["ret1"].agg(
        lambda s: float(np.abs(s).mean() * 1e4))
    res["u_curve_2024_26_bp_by_ct_hour"] = {int(h): round(v, 3)
                                            for h, v in u.items()}

    # Sydney half-hour volume profile (share of day) 2024-26 + 11:30 slot
    g = e.groupby(e["syd_min"] // 30 * 30)["volume"].sum()
    tot = g.sum()
    prof = {f"{int(k)//60:02d}:{int(k)%60:02d}": round(float(v / tot * 100), 3)
            for k, v in g.items()}
    res["syd_halfhour_share_2024_26"] = prof
    if "11:30" in prof:
        avg30 = tot / len(g)
        res["syd_1130_slot"] = {
            "share_pct": prof["11:30"],
            "x_vs_avg_halfhour": round(prof["11:30"] / 100 * tot / avg30, 2)}
    # 11:30 slot across ALL eras (time-of-day only, no ABS conditioning)
    for name, a, b in ERAS:
        ee = fb[(fb["session_date"] >= a) & (fb["session_date"] <= b)]
        gg = ee.groupby(ee["syd_min"] // 30 * 30)["volume"].sum()
        tt = gg.sum()
        res.setdefault("syd_1130_all_eras", {})[name] = {
            "share_pct": round(float(gg.get(690, 0) / tt * 100), 3),
            "x_vs_avg": round(float(gg.get(690, 0) / (tt / len(gg))), 2)}

    # ---- R2: RBA events -------------------------------------------------------
    html = open(f"{NONPRICE}/rba/cash_rate_gate.html", encoding="utf-8",
                errors="replace").read()
    rows = re.findall(
        r"<th[^>]*>\s*(\d{1,2} [A-Za-z]+ \d{4})\s*</th>\s*"
        r"<td[^>]*>\s*([+\-]?\d+\.\d+)\s*</td>\s*"
        r"<td[^>]*>\s*(\d+\.\d+)\s*</td>", html)
    rec = []
    for d, ch, lvl in rows:
        try:
            ts = dt.datetime.strptime(d, "%d %b %Y")
        except ValueError:
            ts = dt.datetime.strptime(d, "%d %B %Y")
        rec.append({"effective_date": pd.Timestamp(ts), "change_pp": float(ch),
                    "cash_rate_pct": float(lvl)})
    rba = pd.DataFrame(rec).drop_duplicates("effective_date").sort_values("effective_date")
    rba["announcement_date"] = [pd.Timestamp((d - pd.offsets.BDay(1)).date())
                                for d in rba["effective_date"]]
    SYD_TZ = zoneinfo.ZoneInfo("Australia/Sydney")
    w = rba[(rba["announcement_date"] >= "2020-01-01") &
            (rba["announcement_date"] <= "2026-10-01")]
    res["rba_gate"] = {
        "n_meetings_2020_2026": int(len(w)),
        "n_changes": int((w["change_pp"] != 0).sum()),
        "n_holds": int((w["change_pp"] == 0).sum()),
        "special_non_tuesday": [str(pd.Timestamp(r).date()) for r in
                                w[w["announcement_date"].dt.dayofweek != 1]
                                ["announcement_date"]],
        "first5": [{"ann": str(r.announcement_date.date()),
                    "eff": str(r.effective_date.date()),
                    "chg": r.change_pp, "rate": r.cash_rate_pct}
                   for r in w.head(5).itertuples()],
        "last5": [{"ann": str(r.announcement_date.date()),
                   "eff": str(r.effective_date.date()),
                   "chg": r.change_pp, "rate": r.cash_rate_pct}
                  for r in w.tail(5).itertuples()]}

    def wstats(df, t0, a, b):
        lo, hi = t0 + pd.Timedelta(minutes=a), t0 + pd.Timedelta(minutes=b)
        x = df[(df["dt"] >= lo) & (df["dt"] < hi)]
        if not len(x):
            return {"n": 0, "volume": 0, "absret_bp": None}
        return {"n": int(len(x)), "volume": int(x["volume"].sum()),
                "absret_bp": float(np.nanmean(np.abs(x["ret1"])) * 1e4)
                if x["ret1"].notna().any() else None}

    # windows: pre(-60,-5) around(-5,+5) post(5,15) post(15,60) post(60,240)
    WIN = [(-60, -5), (-5, 5), (5, 15), (15, 60), (60, 240)]
    ev_rows = []
    for r in w.itertuples():
        day = pd.Timestamp(r.announcement_date)
        t0 = (pd.Timestamp(day, tz=SYD_TZ) +
              pd.Timedelta(hours=14, minutes=30)).tz_convert("UTC")
        ev_rows.append({"date": str(day.date()), "chg": r.change_pp,
                        "t0": t0, **{f"w{a}_{b}": wstats(fb, t0, a, b)
                                     for a, b in WIN}})
    evdates = set(pd.to_datetime(w["announcement_date"]).dt.normalize())
    base = {}
    for a, b in WIN:
        lo, hi = 14 * 60 + 30 + a, 14 * 60 + 30 + b
        x = fb[(fb["syd_min"] >= lo) & (fb["syd_min"] < hi) &
               (~fb["session_date"].isin(evdates))]
        per = x.groupby("session_date").agg(
            vol=("volume", "sum"),
            absr=("ret1", lambda s: float(np.nanmean(np.abs(s)))
                  if s.notna().any() else np.nan))
        base[f"w{a}_{b}"] = {"median_volume": float(per["vol"].median()),
                             "median_absret_bp": float(per["absr"].median() * 1e4)}
    med = {}
    for a, b in WIN:
        k = f"w{a}_{b}"
        med[k] = {
            "event_median_volume": float(np.median([e[k]["volume"] for e in ev_rows])),
            "event_median_absret_bp": float(np.median(
                [e[k]["absret_bp"] for e in ev_rows if e[k]["absret_bp"] is not None])),
            "baseline": base[k],
            "ratio_volume": round(float(np.median(
                [e[k]["volume"] for e in ev_rows])) / base[k]["median_volume"], 2),
            "ratio_absret": round(float(np.median(
                [e[k]["absret_bp"] for e in ev_rows if e[k]["absret_bp"] is not None]))
                / base[k]["median_absret_bp"], 2)}
    res["rba_windows"] = med

    # event-day session totals + change/hold split
    daily = fb.groupby("session_date").agg(
        vol=("volume", "sum"), rng=("range_t", "max")).reset_index()
    chg_dates = set(pd.to_datetime(w[w["change_pp"] != 0]["announcement_date"])
                    .dt.normalize())
    hold_dates = evdates - chg_dates
    nonev = daily[~daily["session_date"].isin(evdates)]
    ev = daily[daily["session_date"].isin(evdates)]
    ch = daily[daily["session_date"].isin(chg_dates)]
    ho = daily[daily["session_date"].isin(hold_dates)]
    res["rba_day_split"] = {
        "event_med_vol": float(ev["vol"].median()),
        "non_event_med_vol": float(nonev["vol"].median()),
        "event_med_range_ticks": float(ev["rng"].median()),
        "non_event_med_range_ticks": float(nonev["rng"].median()),
        "change_days": {"n": int(len(ch)), "med_vol": float(ch["vol"].median()),
                        "med_range_ticks": float(ch["rng"].median())},
        "hold_days": {"n": int(len(ho)), "med_vol": float(ho["vol"].median()),
                      "med_range_ticks": float(ho["rng"].median())}}

    # ---- R4: drawdowns + COVID week ------------------------------------------
    sess_close = fb.groupby("session_date").agg(
        close=("close", "last"), vol=("volume", "sum"),
        hi=("high", "max"), lo=("low", "min")).reset_index()
    sess_close["px"] = sess_close["close"] / SCALE
    # session return with roll-gap (rolled variant): close-to-close regardless of roll
    sess_close["ret"] = sess_close["px"] / sess_close["px"].shift(1) - 1
    dd = sess_close["px"] / sess_close["px"].cummax() - 1
    trough = dd.idxmin()
    peak = sess_close.loc[:trough]["px"].idxmax()
    res["drawdown"] = {
        "worst_depth_pct": round(float(dd.min() * 100), 2),
        "worst_trough_date": str(sess_close.loc[trough, "session_date"]),
        "worst_peak_date": str(sess_close.loc[peak, "session_date"]),
        "covid_trough_2020Q1": round(float(
            dd[sess_close["session_date"] <= "2020-06-30"].min() * 100), 2),
        "covid_trough_date": str(sess_close.loc[
            dd[sess_close["session_date"] <= "2020-06-30"].idxmin(), "session_date"]),
        "covid_peak_date": str(sess_close.loc[
            dd[sess_close["session_date"] <= "2020-06-30"].idxmin() - 0:, "session_date"])}
    # COVID episode peak = running max before Mar-19 trough
    t_i = dd[sess_close["session_date"] <= "2020-06-30"].idxmin()
    p_i = sess_close.loc[:t_i]["px"].idxmax()
    res["drawdown"]["covid_peak_date"] = str(sess_close.loc[p_i, "session_date"])
    res["drawdown"]["covid_depth_pct"] = round(float(
        (sess_close.loc[t_i, "px"] / sess_close.loc[p_i, "px"] - 1) * 100), 2)
    cov = sess_close[(sess_close["session_date"] >= "2020-03-09") &
                     (sess_close["session_date"] <= "2020-03-13")]
    res["covid_week_mar9_13_cum_pct"] = round(float(
        (np.prod(1 + cov["ret"].fillna(0)) - 1) * 100), 2)
    # annualized vol by year (rolled)
    vy = {}
    for y, g in sess_close.groupby(sess_close["session_date"].dt.year):
        vy[int(y)] = round(float(g["ret"].std(ddof=1) * np.sqrt(252) * 100), 2)
    res["vol_by_year_rolled_pct"] = vy

    # save intermediate chain for later scripts
    sess_close[["session_date", "px", "ret", "vol"]].to_parquet(
        os.path.join(HERE, "a7_chain_daily.parquet"), index=False)

    # ---- R3: rolls + CIP ------------------------------------------------------
    sc = sess_close.copy()
    ch = chain.copy()
    ch["roll_flag"] = ch["held"] != ch["held"].shift(1)
    idx = ch.index[ch["roll_flag"]][1:]
    allc = outr.groupby(["session_date", "contract"]).agg(
        close=("close", "last"), vol=("volume", "sum")).reset_index()
    piv = allc.pivot(index="session_date", columns="contract", values="close").sort_index()
    pivv = allc.pivot(index="session_date", columns="contract", values="vol").sort_index()
    rolls = []
    for i in idx:
        d_new = ch.loc[i, "session_date"]
        new, old = ch.loc[i, "held"], ch.loc[i - 1, "held"]
        if old not in piv.columns or new not in piv.columns:
            continue
        co = piv.loc[d_new].get(old)
        cn = piv.loc[d_new].get(new)
        if pd.isna(co) or pd.isna(cn):
            continue
        gap_ticks = (cn - co) / TICK
        span = None
        for j in range(i + 1, len(ch)):
            if ch.loc[j, "roll_flag"]:
                span = (ch.loc[j, "session_date"] - d_new).days
                break
        if span is None:
            span = (ch["session_date"].max() - d_new).days
        ann = float(gap_ticks * TICK / co * 365.0 / max(span, 1) * 100)
        # volume crossover: first session after roll where new > old
        both = pivv.loc[d_new:, [old, new]].dropna(how="all").fillna(0)
        cross = both[both[new] > both[old]]
        rolls.append({"roll_session": str(pd.Timestamp(d_new).date()), "old": old,
                      "new": new, "gap_ticks": float(gap_ticks),
                      "gap_ann_pct": round(ann, 4),
                      "volume_crossover": (str(pd.Timestamp(cross.index[0]).date())
                                           if len(cross) else None)})
    res["n_rolls"] = len(rolls)

    # rates: RBA effective-date series vs DFF latest
    dff = pd.read_csv(f"{NONPRICE}/fred_alfred/latest/DFF_latest.csv")
    cdate, cval = dff.columns[0], [c for c in dff.columns if c.upper().startswith("DFF")][0]
    dff = dff[[cdate, cval]].dropna()
    dff["date"] = pd.to_datetime(dff[cdate])
    dff["dff"] = pd.to_numeric(dff[cval], errors="coerce")
    dff = dff[["date", "dff"]].sort_values("date").reset_index(drop=True)
    rba_eff = rba[["effective_date", "cash_rate_pct"]].rename(
        columns={"effective_date": "date", "cash_rate_pct": "rba"})
    m = pd.merge_asof(dff.sort_values("date"), rba_eff.sort_values("date"),
                      on="date", direction="backward")
    m["diff"] = m["rba"] - m["dff"]
    cip_rows = []
    for r in rolls:
        d = pd.Timestamp(r["roll_session"])
        mm = m[m["date"] <= d].tail(1)
        if not len(mm):
            continue
        diff = float(mm["diff"].iloc[0])
        cip_rows.append({
            "roll": r["roll_session"], "gap_ann_pct": r["gap_ann_pct"],
            "rba": float(mm["rba"].iloc[0]), "dff": float(mm["dff"].iloc[0]),
            "diff_rba_minus_dff": round(diff, 3),
            "material": bool(abs(diff) >= 0.25),
            "cip_match": bool(np.sign(r["gap_ann_pct"]) == np.sign(-diff))})
    mat = [r for r in cip_rows if r["material"]]
    res["cip"] = {
        "n": len(cip_rows),
        "overall_match_pct": round(float(np.mean(
            [r["cip_match"] for r in cip_rows]) * 100), 1),
        "n_material": len(mat),
        "material_match_pct": round(float(np.mean(
            [r["cip_match"] for r in mat]) * 100), 1) if mat else None,
        "mismatches": [r for r in cip_rows if not r["cip_match"]],
        "2026_rolls": [r for r in cip_rows if r["roll"].startswith("2026")],
        "dff_latest_at_2026_09": float(
            dff[dff["date"] <= "2026-09-30"].tail(1)["dff"].iloc[0])}
    res["rolls_full"] = rolls

    # ---- R5: OI crossover vs volume crossover --------------------------------
    stat_files = sorted(glob.glob(f"{DATA}/AV1T-statistics-ALL10/*.parquet"))
    stats = []
    for f in stat_files:
        d = pd.read_parquet(f, columns=["instrument_id", "raw_symbol", "ts_event",
                                        "ts_ref", "stat_type", "quantity"])
        d = d[d["raw_symbol"].str.fullmatch(r"6A[FGHJKMNQUVXZ]\d")]
        stats.append(d)
    st = pd.concat(stats, ignore_index=True)
    st["ref_date"] = pd.to_datetime(st["ts_ref"], unit="ns", utc=True).dt.date
    oi = st[st["stat_type"] == 9]
    # contract map: digit->year
    oi_contract = oi["raw_symbol"].map(lambda s: f"{s}_{2020 + int(s[3])}")
    oid = pd.DataFrame({"session_date": pd.to_datetime(oi["ref_date"]),
                        "contract": oi_contract, "oi": oi["quantity"].values})
    # drop dup (instrument, date) keep last
    oid = oid.drop_duplicates(["session_date", "contract"], keep="last")
    piv_oi = oid.pivot(index="session_date", columns="contract", values="oi").sort_index()
    oi_lead = []
    for r in rolls:
        if r["roll_session"] < "2023-10-01":
            continue  # OI availability 2023-10+
        d0 = pd.Timestamp(r["roll_session"])
        old, new = r["old"], r["new"]
        if old not in piv_oi.columns or new not in piv_oi.columns:
            continue
        w = piv_oi.loc[d0:, [old, new]].dropna(how="all")
        cr = w[w[new] > w[old]]
        oi_cross = str(cr.index[0].date()) if len(cr) else None
        vol_cross = r["volume_crossover"]
        lead = None
        if oi_cross and vol_cross:
            lead = (pd.Timestamp(vol_cross) - pd.Timestamp(oi_cross)).days
        oi_lead.append({"roll": r["roll_session"], "oi_crossover": oi_cross,
                        "vol_crossover": vol_cross, "oi_leads_days": lead})
    res["oi_vs_volume_crossover"] = oi_lead

    # ---- R7b: spread mark vs outright-implied ---------------------------------
    spr_loc = pd.to_datetime(spr["ts_event"], unit="ns", utc=True).dt.tz_convert(CHI)
    spr_sd = pd.DatetimeIndex(
        (spr_loc.dt.normalize().values.astype("datetime64[D]") +
         np.where(spr_loc.dt.hour >= 17, 1, 0).astype("int64"))).date
    spr = spr.assign(session_date=pd.to_datetime(spr_sd))
    last = spr["session_date"].max() - pd.Timedelta(days=90)
    sample = spr[spr["session_date"] >= last]
    allc2 = outr.groupby(["session_date", "contract"]).agg(
        close=("close", "last")).reset_index()
    closes2 = allc2.pivot(index="session_date", columns="contract",
                          values="close").sort_index()
    checks = []
    for sym, g in sample.groupby("raw_symbol"):
        a, b = sym.split("-")
        ca, cb = f"{a}_{2020 + int(a[3])}", f"{b}_{2020 + int(b[3])}"
        if ca not in closes2.columns or cb not in closes2.columns:
            continue
        gg = g.groupby("session_date")["close"].last()
        diffs = []
        for d, v in gg.items():
            if d in closes2.index and pd.notna(closes2.loc[d].get(ca)) \
                    and pd.notna(closes2.loc[d].get(cb)):
                implied = (closes2.loc[d, ca] - closes2.loc[d, cb]) / SCALE
                diffs.append(v / SCALE - implied)
        if len(diffs) >= 5:
            checks.append({"symbol": sym, "n": len(diffs),
                           "median_abs_diff_usd": round(float(
                               np.median(np.abs(diffs))), 7),
                           "median_abs_diff_ticks": round(float(
                               np.median(np.abs(diffs)) / 0.00005), 1)})
    checks = sorted(checks, key=lambda c: -c["n"])[:6]
    res["spread_vs_outright_implied_last90d"] = checks

    with open(os.path.join(HERE, "recompute_core.json"), "w") as fh:
        json.dump({k: v for k, v in res.items()}, fh, indent=1, default=str)
    print("AUDIT recompute written; key numbers:")
    print(" raw rows", res["raw_rows"], "| outright", res["outright_rows"],
          "| spread", res["spread_rows"])
    print(" contaminant", res["contaminant"]["n_bars"], res["contaminant"]["symbols"])
    print(" neg outright", res["neg_outright"], "| neg spread", res["neg_spread_total"],
          res["neg_spread_by_era"])
    print(" RTH/Sydney/London shares:", json.dumps(res["hub_volume_shares_pct"], indent=1))
    print(" RBA:", res["rba_gate"]["n_meetings_2020_2026"],
          res["rba_gate"]["n_changes"], res["rba_gate"]["n_holds"])
    print(" RBA w-5+5:", res["rba_windows"]["w-5_5"])
    print(" day split:", res["rba_day_split"])
    print(" DD:", res["drawdown"])
    print(" CIP:", {k: v for k, v in res["cip"].items() if k != "mismatches"})
    print(" OI leads:", res["oi_vs_volume_crossover"][:4])


if __name__ == "__main__":
    main()
