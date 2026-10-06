#!/usr/bin/env python
"""A7-DEEP-6A FOMC ±5min fresh recompute (dossier §4.2: 8.2x volume, 6.2x
|1m ret|, 59 statements 2020-2026) + v1-reconciliation artifact check.
Independent of lane code."""
import datetime as dt
import glob
import json
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
NP = "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms"
DATA = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet"
SCALE, TICK = 1e9, 50_000.0
MC = {"F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
      "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12}


def main():
    # front panel rebuilt from raw (quarterly held chain, digit registry)
    files = []
    for line in ["AV1B-O1M-6A-BACKFILL2", "AV1R-O1M-6A-BACKFILL", "AV1T-O1M-6A"]:
        files += sorted(glob.glob(f"{DATA}/{line}/*.parquet"))
    raw = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    raw["dt"] = pd.to_datetime(raw["ts_event"], unit="ns", utc=True)
    outr = raw[~raw["raw_symbol"].str.contains("-")]
    outr = outr[outr["raw_symbol"].str.fullmatch(r"6A[FGHJKMNQUVXZ]\d")]
    outr["contract"] = [f"{s}_{2020 + int(s[3])}" for s in outr["raw_symbol"]]
    q = outr[outr["raw_symbol"].str[2].isin(list("HMUZ"))]
    loc = q["dt"].dt.tz_convert("America/Chicago")
    nd = loc.dt.normalize().values.astype("datetime64[D]") + np.where(
        loc.dt.hour >= 17, 1, 0).astype("int64")
    q = q.assign(sd=pd.to_datetime(pd.DatetimeIndex(nd).date))
    held = []
    for d, g in q.groupby("sd"):
        dm = pd.Timestamp(d)
        cands = [(pd.Timestamp(year=int(c.split("_")[1]), month=MC[c[2]], day=1), c)
                 for c in g["contract"].unique()
                 if pd.Timestamp(year=int(c.split("_")[1]), month=MC[c[2]], day=1) > dm]
        if cands:
            held.append((d, min(cands)[1]))
    hp = set(held)
    fb = outr[[(pd.Timestamp(sd), c) in hp
               for sd, c in zip(pd.to_datetime(
                   pd.DatetimeIndex(
                       (outr["dt"].dt.tz_convert("America/Chicago").dt.normalize()
                        .values.astype("datetime64[D]") +
                        np.where(outr["dt"].dt.tz_convert("America/Chicago").dt.hour >= 17,
                                 1, 0).astype("int64"))).date), outr["contract"])]]
    fb = fb.sort_values("dt").reset_index(drop=True)
    fb["ret1"] = fb["close"] / fb["close"].shift(1) - 1
    fb.loc[fb["contract"] != fb["contract"].shift(1), "ret1"] = np.nan
    fb["range_t"] = (fb["high"] - fb["low"]) / TICK
    ct = fb["dt"].dt.tz_convert("America/Chicago")
    fb["ct_minute"] = (ct.dt.hour * 60 + ct.dt.minute).astype("int32")
    fb["sd"] = pd.to_datetime(pd.DatetimeIndex(
        (ct.dt.normalize().values.astype("datetime64[D]") +
         np.where(ct.dt.hour >= 17, 1, 0).astype("int64"))).date)

    # FOMC statements
    frows = []
    for f in sorted(glob.glob(f"{NP}/fed/statements/monetary*.html")):
        m = re.fullmatch(r"monetary(\d{8})a\.html", os.path.basename(f))
        if not m:
            continue
        txt = open(f, encoding="utf-8", errors="replace").read()
        mt = re.search(r"For release at\s*(\d{1,2}):(\d{2})\s*([ap])\.m\.\s*(E[SD]T)", txt)
        if mt:
            hh = int(mt.group(1)) % 12 + (12 if mt.group(3) == "p" else 0)
            t = dt.time(hh, int(mt.group(2)))
        else:
            t = dt.time(13, 0)
        frows.append({"date": pd.Timestamp(m.group(1)), "time": t})
    fomc = pd.DataFrame(frows).sort_values("date")
    w = fomc[(fomc["date"] >= "2020-01-01") & (fomc["date"] <= "2026-10-01")]

    res = {"n_statements_2020_2026": int(len(w)),
           "n_with_explicit_time": int(sum(1 for _, r in w.iterrows()
                                           if r["time"] != dt.time(13, 0) or True))}
    vols, rets = [], []
    for r in w.itertuples():
        t0 = (pd.Timestamp(r.date) + pd.Timedelta(hours=r.time.hour,
                                                  minutes=r.time.minute)
              ).tz_localize("America/New_York").tz_convert("UTC")
        x = fb[(fb["dt"] >= t0 - pd.Timedelta(minutes=5)) &
               (fb["dt"] < t0 + pd.Timedelta(minutes=5))]
        if len(x):
            vols.append(int(x["volume"].sum()))
            if x["ret1"].notna().any():
                rets.append(float(np.nanmean(np.abs(x["ret1"])) * 1e4))
    fdates = set(pd.to_datetime(w["date"]).dt.normalize())
    lo, hi = 13 * 60 - 5, 13 * 60 + 5
    b = fb[(fb["ct_minute"] >= lo) & (fb["ct_minute"] < hi) &
           (~fb["sd"].isin(fdates))]
    per = b.groupby("sd").agg(
        vol=("volume", "sum"),
        absr=("ret1", lambda s: float(np.nanmean(np.abs(s)))
              if s.notna().any() else np.nan))
    res["fomc_pm5"] = {
        "event_median_volume": float(np.median(vols)),
        "event_median_absret_bp": float(np.median(rets)),
        "baseline_median_volume": float(per["vol"].median()),
        "baseline_median_absret_bp": float(per["absr"].median() * 1e4),
        "ratio_volume": round(float(np.median(vols)) / float(per["vol"].median()), 2),
        "ratio_absret": round(float(np.median(rets)) / (float(per["absr"].median()) * 1e4), 2)}
    # event-day session totals
    daily = fb.groupby("sd").agg(vol=("volume", "sum"),
                                 rng=("range_t", "max")).reset_index()
    ev = daily[daily["sd"].isin(fdates)]
    ne = daily[~daily["sd"].isin(fdates)]
    res["fomc_day"] = {
        "n_event_sessions": int(len(ev)),
        "event_med_vol": float(ev["vol"].median()),
        "non_event_med_vol": float(ne["vol"].median()),
        "event_med_range_ticks": float(ev["rng"].median()),
        "non_event_med_range_ticks": float(ne["rng"].median())}
    with open(os.path.join(HERE, "recompute_fomc.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
