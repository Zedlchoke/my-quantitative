#!/usr/bin/env python
"""A7-DEEP-ES audit R2: INDEPENDENT recompute of A2 session structure headline
numbers from vendor parquet (own chain, own marks).

Checks (dossier sec 0.4 / sec 3):
  - Overnight variance share by year: 2020 peak 53.8%, 2018 low 20.9%,
    overall 21-54% band
  - era table Var(ON) shares E1..E7 (38.5/38.6/43.6/28.4/50.7/32.8/34.2%)
  - RTH volume share ~79-86% by year/era
  - sd(ON) / sd(RTH) ranges; corr(ON,RTH) per era
  - robustness: ON/RTH variance split computed with ratio-adjusted closes
    around the 66 switch sessions (unadjusted convention embeds the calendar
    spread in on_ret at switches)

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python a7_r2_sessions.py
"""
import glob
import json
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
VEND = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet"
NS = 1_000_000_000.0
PAT = re.compile(r"^ES[HMUZ][0-9]$")
MCODE = {"H": 3, "M": 6, "U": 9, "Z": 12}

chunks = sorted(glob.glob(f"{VEND}/AV1R-O1M-ES-DELTA/*.parquet")) + \
         sorted(glob.glob(f"{VEND}/AV1T-O1M-ES/*.parquet"))
rows = []
for fp in chunks:
    d = pd.read_parquet(fp, columns=["instrument_id", "raw_symbol", "ts_event",
                                     "open", "close", "volume"])
    rows.append(d[d["raw_symbol"].str.match(PAT)])
m = pd.concat(rows, ignore_index=True)
del rows

chi = pd.DatetimeIndex(pd.to_datetime(m["ts_event"].to_numpy(), utc=True)) \
        .tz_convert("America/Chicago")
m["hhmm"] = chi.hour * 100 + chi.minute
m["sess"] = chi + pd.to_timedelta((chi.hour >= 17).astype("int32"), unit="D")
m["sess"] = pd.DatetimeIndex(m["sess"]).normalize().tz_localize(None)
m["mkey"] = np.where(chi.hour >= 17, (chi.hour - 17) * 60 + chi.minute,
                     (chi.hour + 7) * 60 + chi.minute)
m = m.drop(columns=["ts_event"]).sort_values(
    ["instrument_id", "sess", "mkey"], kind="stable")

g = m.groupby(["instrument_id", "sess"], sort=True)
cd = g.agg(vol_total=("volume", "sum"), sess_close=("close", "last")).reset_index()
rth = m[(m["hhmm"] >= 830) & (m["hhmm"] < 1600)]
gm = rth.groupby(["instrument_id", "sess"], sort=True).agg(
    rth_open=("open", "first"), rth_close16=("close", "last")).reset_index()
cd = cd.merge(gm, on=["instrument_id", "sess"], how="left")
cd["sess_close"] = cd["sess_close"] / NS
cd["rth_open"] = cd["rth_open"] / NS
cd["rth_close16"] = cd["rth_close16"] / NS

# per-contract volume by segment (RTH/ON/BRK share)
m["seg"] = np.where(m["hhmm"] >= 1700, "ON",
             np.where(m["hhmm"] >= 1600, "BRK",
             np.where(m["hhmm"] >= 830, "RTH", "ON")))
segv = m.groupby(["instrument_id", "sess", "seg"])["volume"].sum().reset_index()
segw = segv.pivot_table(index=["instrument_id", "sess"], columns="seg",
                        values="volume").fillna(0.0).reset_index()
segw = segw.rename(columns={"ON": "vol_ON", "RTH": "vol_RTH", "BRK": "vol_BRK"})
cd = cd.merge(segw, on=["instrument_id", "sess"], how="left")

# ---- deliveries + VOL chain (strict-past prior-session volume argmax)
sym = m.groupby("instrument_id")["raw_symbol"].first()
maxday = cd.groupby("instrument_id")["vol_total"].max()
real_iids = maxday[maxday >= 100_000].index
last_sess = cd.groupby("instrument_id")["sess"].max()
data_end = cd["sess"].max()
dmap = {}
for iid in real_iids:
    mo = MCODE[sym[iid][2]]
    ls = last_sess[iid]
    yy = ls.year + (1 if mo < ls.month else 0)
    dmap[iid] = f"{yy:04d}-{mo:02d}"
dl = sorted(set(dmap.values()))
iid_of = {v: k for k, v in sorted(dmap.items(), key=lambda kv: kv[1])}

piv = cd.pivot_table(index="sess", columns="instrument_id", values="vol_total")
piv.index = pd.DatetimeIndex(piv.index)
sess_ix = list(piv.index)
cur = dl[0]
front = []
for i, s in enumerate(sess_ix):
    if i > 0:
        cands = [d for d in dl if d >= cur][:2]
        pv = piv.loc[sess_ix[i - 1]]
        vols = {d: pv.get(iid_of[d], np.nan) for d in cands}
        vols = {k: v for k, v in vols.items() if pd.notna(v)}
        if vols:
            best = max(vols, key=lambda d: (vols[d], -dl.index(d)))
            if best != cur and dl.index(best) > dl.index(cur):
                cur = best
    front.append(cur)
F = pd.Series(front, index=piv.index, name="front")
cd["front"] = cd["sess"].map(dict(zip(piv.index, front)))
cdf = cd[cd["instrument_id"].map(dmap) == cd["front"]].copy().set_index("sess")
cdf = cdf.sort_index()

# ---- ON/RTH returns (chain marks, lane convention: unadjusted across switches)
mk = cdf[["front", "vol_total", "vol_RTH", "vol_ON", "vol_BRK",
          "sess_close", "rth_open", "rth_close16"]].copy()
mk["on_ret"] = mk["rth_open"] / mk["sess_close"].shift(1) - 1
mk["rth_ret"] = mk["rth_close16"] / mk["rth_open"] - 1
mk["switch"] = mk["front"] != mk["front"].shift()

# ratio-adjusted variant (remove calendar-spread jump at switch sessions)
adj = 1.0
adjc = []
prev_close = None
idx = mk.index
cdi = cd.set_index(["sess", "instrument_id"])
for i, (s, r) in enumerate(mk.iterrows()):
    if i > 0 and r["switch"]:
        old_close = prev_close
        try:
            new_on_prev = cdi.loc[(idx[i - 1], iid_of[r["front"]]), "sess_close"]
        except KeyError:
            new_on_prev = np.nan
        if pd.notna(old_close) and pd.notna(new_on_prev) and new_on_prev:
            adj *= old_close / new_on_prev
    adjc.append(adj)
    prev_close = r["sess_close"]
mk["close_adj"] = mk["sess_close"] * pd.Series(adjc, index=mk.index, dtype=float)
mk["rth_open_adj"] = mk["rth_open"] * pd.Series(adjc, index=mk.index, dtype=float)
mk["on_ret_adj"] = mk["rth_open_adj"] / mk["close_adj"].shift(1) - 1

ERAS = [
    ("E1", "2010-06-07", "2012-12-31"), ("E2", "2013-01-01", "2015-11-19"),
    ("E3", "2015-11-20", "2017-05-20"), ("E4", "2017-05-21", "2020-02-19"),
    ("E5", "2020-02-20", "2021-12-31"), ("E6", "2022-01-01", "2023-09-30"),
    ("E7", "2023-10-01", "2026-10-01"),
]

def stats(mm):
    var_on = mm["on_ret"].var()
    var_rth = mm["rth_ret"].var()
    return {
        "n": int(len(mm)),
        "var_on_pct": float(var_on / (var_on + var_rth) * 100),
        "var_on_pct_adj": float(
            (mm["on_ret_adj"].var()) /
            (mm["on_ret_adj"].var() + mm["rth_ret"].var()) * 100),
        "sd_on_pct": float(mm["on_ret"].std() * 100),
        "sd_rth_pct": float(mm["rth_ret"].std() * 100),
        "corr_on_rth": float(mm["on_ret"].corr(mm["rth_ret"])),
        "vol_rth_share_median": float((mm["vol_RTH"] / mm["vol_total"]).median()),
    }

era_rows = {n: stats(mk.loc[a:b]) for n, a, b in ERAS}
year_rows = {}
for y, mm in mk.groupby(mk.index.year):
    year_rows[int(y)] = stats(mm)

out = {
    "n_sessions": int(len(mk)),
    "window": [str(mk.index.min().date()), str(mk.index.max().date())],
    "eras": era_rows,
    "years": year_rows,
    "claims_check": {
        "var_on_2020": year_rows.get(2020, {}).get("var_on_pct"),
        "var_on_2018": year_rows.get(2018, {}).get("var_on_pct"),
        "var_on_min_year": min(year_rows, key=lambda y: year_rows[y]["var_on_pct"]),
        "var_on_max_year": max(year_rows, key=lambda y: year_rows[y]["var_on_pct"]),
        "sd_on_minmax_by_year": [min(v["sd_on_pct"] for v in year_rows.values()),
                                 max(v["sd_on_pct"] for v in year_rows.values())],
        "sd_rth_minmax_by_year": [min(v["sd_rth_pct"] for v in year_rows.values()),
                                  max(v["sd_rth_pct"] for v in year_rows.values())],
        "vol_rth_share_minmax_by_year": [
            min(v["vol_rth_share_median"] for v in year_rows.values()),
            max(v["vol_rth_share_median"] for v in year_rows.values())],
    },
}
with open(os.path.join(HERE, "r2_sessions.json"), "w") as f:
    json.dump(out, f, indent=1)

print("years: year var_on% sd_on sd_rth corr rthshare | var_on_adj%")
for y in sorted(year_rows):
    r = year_rows[y]
    print(f"  {y} {r['var_on_pct']:5.1f} {r['sd_on_pct']:.2f} {r['sd_rth_pct']:.2f} "
          f"{r['corr_on_rth']:+.2f} {r['vol_rth_share_median']:.3f} | {r['var_on_pct_adj']:5.1f}")
print("eras:")
for n in era_rows:
    r = era_rows[n]
    print(f"  {n} {r['var_on_pct']:5.1f} (adj {r['var_on_pct_adj']:5.1f}) "
          f"corr={r['corr_on_rth']:+.2f} rthshare={r['vol_rth_share_median']:.3f}")
print("claims:", json.dumps(out["claims_check"], indent=1))
print("WROTE r2_sessions.json")
