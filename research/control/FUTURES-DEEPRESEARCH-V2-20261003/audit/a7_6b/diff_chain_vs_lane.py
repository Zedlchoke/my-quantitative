#!/usr/bin/env python
"""A7-DEEP-6B: diff my independently built calendar chain vs the lane's cached
chain_calendar.parquet, and recompute my chain to compare (session-level)."""
import glob
import re
import datetime as dt

import numpy as np
import pandas as pd

DATA_ROOT = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim"
CACHE = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/"
         "research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/6B_cache")

# --- my chain (rebuilt exactly as in recompute script) ---
files = (sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1B-O1M-6B-BACKFILL2/*.parquet"))
         + sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1R-O1M-6B-BACKFILL/*.parquet"))
         + sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1T-O1M-6B/*.parquet")))
df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
df = df[~df["raw_symbol"].str.contains("-")].copy()
df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
df = df.sort_values("dt").reset_index(drop=True)
loc = df["dt"].dt.tz_convert("America/Chicago")
sd = loc.dt.normalize() + pd.to_timedelta((loc.dt.hour >= 17).astype(int), unit="D")
df["session_date"] = sd.dt.tz_localize(None).dt.date

MONTH = {"H": 3, "M": 6, "U": 9, "Z": 12}
CODE = {3: "H", 6: "M", 9: "U", 12: "Z"}


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


panel_max = df["dt"].max()
lut = {}
for sym, g in df.groupby("raw_symbol"):
    m = re.fullmatch(r"6B([HMUZ])(\d)", sym)
    if not m:
        continue
    g = g.sort_values("dt")
    newcl = (g["dt"].diff() > pd.Timedelta(days=45)).astype(int).cumsum()
    for cid, gg in g.groupby(newcl.values):
        t1 = gg["dt"].max()
        hits = []
        for y in range(2019, 2029):
            if y % 10 != int(m.group(2)):
                continue
            ltd = approx_ltd(y, MONTH[m.group(1)])
            delta = (t1.tz_localize(None) - pd.Timestamp(ltd)).days
            if -100 <= delta <= 12 or (t1 == panel_max
                                       and pd.Timestamp(ltd) >= t1.tz_localize(None)):
                hits.append((y, ltd))
        if len(hits) == 1:
            lut[(sym, cid)] = (f"6B{CODE[hits[0][1].month]}{hits[0][0]}",
                               pd.Timestamp(hits[0][1]))

df["_cl"] = ((df.groupby("raw_symbol")["dt"].diff() > pd.Timedelta(days=45))
             .groupby(df["raw_symbol"]).cumsum().fillna(0))
df["_key"] = list(zip(df["raw_symbol"], df["_cl"]))
df["contract"] = df["_key"].map(lambda k: lut.get(k, (None, None))[0])
d2 = df[df["contract"].notna()]
sess = (d2.groupby(["session_date", "contract"])
        .agg(close=("close", "last"), high=("high", "max"), low=("low", "min"),
             volume=("volume", "sum"), n_bars=("volume", "size")).reset_index())
for c in ("close", "high", "low"):
    sess[c] = sess[c] / 1e9
sess["d"] = pd.to_datetime(sess["session_date"])

corder = sorted(sess["contract"].unique(),
                key=lambda c: (int(c[-4:]), "HMUZ".index(c[2])))
expmap = {lut[k][0]: lut[k][1] for k in lut}
fronts = []
for i, c in enumerate(corder):
    expm = pd.Timestamp(int(c[-4:]), "HMUZ".index(c[2]) * 3 + 3, 1)
    sub = sess[(sess["contract"] == c) & (sess["d"] < expm)]
    if i > 0:
        pm = pd.Timestamp(int(corder[i - 1][-4:]),
                          "HMUZ".index(corder[i - 1][2]) * 3 + 3, 1)
        sub = sub[sub["d"] >= pm]
    if len(sub):
        fronts.append(sub[["session_date", "contract"]])
held = pd.concat(fronts).groupby("session_date")["contract"].last().rename("held").reset_index()
mine = sess.merge(held, on="session_date")
mine = mine[mine["contract"] == mine["held"]].sort_values("d").reset_index(drop=True)

# --- lane cached chain ---
lane = pd.read_parquet(f"{CACHE}/chain_calendar.parquet")
lane["d"] = pd.to_datetime(lane["session_date"])

j = mine[["d", "close", "n_bars", "volume", "held"]].merge(
    lane[["d", "close", "n_bars", "volume", "held"]], on="d",
    suffixes=("_mine", "_lane"), how="outer")
bad = j[(j["close_mine"].notna() & j["close_lane"].notna())
        & ((j["close_mine"] != j["close_lane"])
           | (j["held_mine"] != j["held_lane"])
           | (j["n_bars_mine"] != j["n_bars_lane"]))]
print("sessions mine/lane:", len(mine), len(lane), "| mismatched rows:", len(bad))
print(bad[["d", "close_mine", "close_lane", "n_bars_mine", "n_bars_lane",
           "volume_mine", "volume_lane", "held_mine", "held_lane"]].to_string())
only_mine = j[j["close_lane"].isna() & j["close_mine"].notna()]
only_lane = j[j["close_mine"].isna() & j["close_lane"].notna()]
print("only in mine:", len(only_mine), only_mine["d"].tolist())
print("only in lane:", len(only_lane), only_lane["d"].tolist())
