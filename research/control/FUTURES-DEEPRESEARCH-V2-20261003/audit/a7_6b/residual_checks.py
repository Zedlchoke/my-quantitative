#!/usr/bin/env python
"""A7-DEEP-6B residual verification: QA-ledger claims, stray inventory,
definitions tick, butt joints, record-volume/low claims, FOMC 2022-05-31 note."""
import glob
import os
import re

import numpy as np
import pandas as pd

DATA_ROOT = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim"
NONPRICE = "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms"
OUT = {}

eras = [("backfill_2020_2022", "AV1B-O1M-6B-BACKFILL2"),
        ("main_2022_2026_04", "AV1R-O1M-6B-BACKFILL"),
        ("recent_2026_04_10", "AV1T-O1M-6B")]
tot_out, tot_spread = 0, 0
gcq4 = []
for name, pat in eras:
    fs = sorted(glob.glob(f"{DATA_ROOT}/parquet/{pat}/*.parquet"))
    d = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    spread = int(d["raw_symbol"].str.contains("-").sum())
    out = int(len(d)) - spread
    tot_out += out
    tot_spread += spread
    OUT[name] = {"rows_outright": out, "rows_spread": spread}
    g = d[d["raw_symbol"] == "GCQ4"]
    if len(g):
        gcq4.append({"era": name, "bars": int(len(g)),
                     "span": [str(pd.to_datetime(g["ts_event"], unit="ns", utc=True).min()),
                              str(pd.to_datetime(g["ts_event"], unit="ns", utc=True).max())],
                     "volume": int(g["volume"].sum())})
OUT["panel_outright_total"] = tot_out
OUT["panel_spread_total"] = tot_spread
OUT["gcq4"] = gcq4

# serial (non-HMUZ 6B) bar/volume totals + stray-cluster totals via 45d clustering
files = [f for _, pat in eras for f in sorted(glob.glob(f"{DATA_ROOT}/parquet/{pat}/*.parquet"))]
df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
df = df[~df["raw_symbol"].str.contains("-")].copy()
df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
serial = df[~df["raw_symbol"].str.fullmatch(r"6B[HMUZ]\d")]
OUT["serial_rows"] = int(len(serial))
OUT["serial_volume"] = int(serial["volume"].sum())
OUT["serial_volume_share_pct"] = float(serial["volume"].sum() / df["volume"].sum() * 100)

# weekend bars + maintenance-break bars (Chicago clock)
loc = df["dt"].dt.tz_convert("America/Chicago")
hhmm = loc.dt.hour * 60 + loc.dt.minute
OUT["bars_in_break_1600_1700_ct"] = int(((hhmm >= 960) & (hhmm < 1020)).sum())
OUT["weekend_bars_sat_or_fri_ge1700"] = int(
    ((loc.dt.dayofweek == 5) | ((loc.dt.dayofweek == 4) & (hhmm >= 1020))).sum())

# definitions tick
defs = []
for f in sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1T-definition-ALL10/*.parquet")):
    d = pd.read_parquet(f)
    defs.append(d[d["raw_symbol"].str.fullmatch(r"6B[HMUZ]\d")])
de = pd.concat(defs, ignore_index=True)
OUT["definitions_6B_rows"] = int(len(de))
OUT["definitions_min_price_increment_usd"] = sorted((de["min_price_increment"].unique() / 1e9).tolist())

# butt joints
frames = {}
for name, pat in eras:
    fs = sorted(glob.glob(f"{DATA_ROOT}/parquet/{pat}/*.parquet"))
    d = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    d["dt"] = pd.to_datetime(d["ts_event"], unit="ns", utc=True)
    frames[name] = d
for a, b, jd, sym in [("backfill_2020_2022", "main_2022_2026_04", "2022-01-01", "6BH2"),
                      ("main_2022_2026_04", "recent_2026_04_10", "2026-04-01", "6BM6")]:
    jt = pd.Timestamp(jd, tz="UTC")
    wa = frames[a][(frames[a]["dt"] >= jt - pd.Timedelta(days=3)) & (frames[a]["dt"] < jt + pd.Timedelta(days=3))]
    wb = frames[b][(frames[b]["dt"] >= jt - pd.Timedelta(days=3)) & (frames[b]["dt"] < jt + pd.Timedelta(days=3))]
    ka = set(zip(wa["instrument_id"], wa["ts_event"]))
    kb = set(zip(wb["instrument_id"], wb["ts_event"]))
    fa = frames[a][(frames[a]["raw_symbol"] == sym) & (frames[a]["dt"] < jt)]
    fb = frames[b][(frames[b]["raw_symbol"] == sym) & (frames[b]["dt"] >= jt)]
    gap = (float(fb["open"].iloc[0]) - float(fa["close"].iloc[-1])) / float(fa["close"].iloc[-1]) * 100 if len(fa) and len(fb) else None
    OUT[f"joint_{jd}"] = {"dup_keys": len(ka & kb), "front_gap_pct": gap}

# all-time session volume record + all-time low on front contracts:
# session table over the 28 front-scale quarterlies only
import datetime as dt
MONTH = {"H": 3, "M": 6, "U": 9, "Z": 12}


def approx_ltd(y, m):
    d0 = dt.date(y, m, 1)
    off = (2 - d0.weekday()) % 7
    tw = d0 + dt.timedelta(days=off + 14)
    n = 0
    while n < 2:
        tw -= dt.timedelta(days=1)
        if tw.weekday() < 5:
            n += 1
    return tw


loc2 = df["dt"].dt.tz_convert("America/Chicago")
sd2 = loc2.dt.normalize()
sd2 = sd2.where(loc2.dt.hour < 17, sd2 + pd.offsets.Day(1))
df["session_date"] = sd2.dt.tz_localize(None).dt.date
panel_max = df["dt"].max()
keep_rows = []
for sym, g in df.groupby("raw_symbol"):
    m = re.fullmatch(r"6B([HMUZ])(\d)", sym)
    if not m:
        continue
    g = g.sort_values("dt")
    cl = (g["dt"].diff() > pd.Timedelta(days=45)).astype(int).cumsum()
    for _, gg in g.groupby(cl.values):
        if gg["volume"].sum() > 1_000_000:
            keep_rows.append(gg)
fr = pd.concat(keep_rows) if keep_rows else df.iloc[0:0]
st = (fr.groupby("session_date")
       .agg(vol=("volume", "sum"), low=("low", "min"), n=("volume", "size")).reset_index())
st["low"] = st["low"] / 1e9
OUT["max_session_volume"] = {"date": str(st.loc[st["vol"].idxmax(), "session_date"]),
                             "volume": int(st["vol"].max()),
                             "median_volume": float(st["vol"].median()),
                             "ratio_max_over_median": float(st["vol"].max() / st["vol"].median())}
OUT["all_time_low_front_contracts"] = {"low": float(st["low"].min()),
                                       "date": str(st.loc[st["low"].idxmin(), "session_date"])}

# FOMC June-2022 statement date (for the '+13 outlier one week before scheduled hike' note)
fomc_files = sorted(glob.glob(f"{NONPRICE}/fed/statements/monetary202206*.html"))
OUT["fomc_june2022_files"] = [os.path.basename(f) for f in fomc_files]

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "residual_checks.json"), "w") as fh:
    import json
    json.dump({k: (v if not isinstance(v, (np.integer, np.floating)) else (int(v) if isinstance(v, np.integer) else float(v)))
               for k, v in OUT.items()}, fh, indent=1, default=str)
print(json.dumps(OUT, indent=1, default=str))
