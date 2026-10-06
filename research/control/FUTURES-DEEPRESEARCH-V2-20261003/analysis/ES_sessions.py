#!/usr/bin/env python
"""ES deep-research v2 — A2 full-era session/intraday structure from 1m bars
(lane DEEP-ES).

RTH AND overnight/Globex (which the v1 IBKR useRTH snapshot hid), DST-correct
(America/Chicago via tz database), era drift 2010-2026.

Front contract per session = VOL chain (prior-session volume argmax, strict
past) — matches actual liquidity. Segments (Chicago clock):
  ON  17:00 -> 08:29 (Globex overnight, incl. Sunday open 17:00 Sun)
  RTH 08:30 -> 15:59 (futures RTH; NY cash hours 08:30-14:59 sub-tagged)
  BRK 16:00 -> 16:59 (maintenance; no trading expected)

DESCRIPTIVE ONLY. Outputs ES_session_stats.json.

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python ES_sessions.py
"""
import json
import os
from datetime import datetime

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "ES_cache")

m = pd.read_parquet(os.path.join(CACHE, "es_1m_seg.parquet"))
ch = pd.read_parquet(os.path.join(CACHE, "es_chain_VOL.parquet")).sort_index()
m = m.merge(ch.reset_index()[["sess", "front"]], on="sess")
m = m[m["delivery"] == m["front"]]
print("front-contract 1m rows:", len(m))

m["dow"] = pd.DatetimeIndex(m["sess"]).dayofweek
m["year"] = pd.DatetimeIndex(m["sess"]).year
m["hour_chi"] = m["chi"].dt.hour

# ---------------------------------------------------------------- daily seg
g = m.groupby(["sess", "seg"], sort=True)
seg = g.agg(vol=("volume", "sum"), nbars=("volume", "size"),
            sq_ret=("close", lambda x: float(
                np.nansum(np.diff(np.log(x.replace(0, np.nan).values)) ** 2)))
            ).reset_index()
d = seg.pivot_table(index="sess", columns="seg",
                    values=["vol", "nbars", "sq_ret"]).reset_index()
d.columns = [f"{a}_{b}".strip("_") for a, b in d.columns]
d = d.set_index("sess")
d["vol_total"] = d[["vol_ON", "vol_RTH", "vol_BRK"]].sum(axis=1)
d["vol_rth_share"] = d["vol_RTH"] / d["vol_total"]
d["rv_ON"] = np.sqrt(d["sq_ret_ON"] * 252)     # per-session intraday-only
d["rv_RTH"] = np.sqrt(d["sq_ret_RTH"] * 252)
d["vol_on_share"] = d["vol_ON"] / d["vol_total"]

# session-level variance decomposition from marks (front contract only):
# ON ret = prev 16:00 close -> 08:30 open; RTH ret = 08:30 open -> 16:00 close
mk = ch.copy()
mk["on_ret"] = mk["rth_open"] / mk["close"].shift(1) - 1
mk["rth_ret"] = mk["rth_close16"] / mk["rth_open"] - 1
mk["day_ret"] = mk["close"] / mk["close"].shift(1) - 1

ERAS = [
    ("E1 2010-06..2012-12", "2010-06-07", "2012-12-31"),
    ("E2 2013..2015-11", "2013-01-01", "2015-11-19"),
    ("E3 2015-11..2017-05", "2015-11-20", "2017-05-20"),
    ("E4 2017-05..2020-02", "2017-05-21", "2020-02-19"),
    ("E5 2020-02..2021-12", "2020-02-20", "2021-12-31"),
    ("E6 2022..2023-09", "2022-01-01", "2023-09-30"),
    ("E7 2023-10..2026-10", "2023-10-01", "2026-10-01"),
]

def era_sessions(a, b):
    dd = d.loc[a:b]
    mm = mk.loc[a:b]
    out = {
        "n_sessions": int(len(dd)),
        "median_front_vol_total": float(dd["vol_total"].median()),
        "median_front_vol_rth": float(dd["vol_RTH"].median()),
        "median_front_vol_on": float(dd["vol_ON"].median()),
        "vol_rth_share_median": float(dd["vol_rth_share"].median()),
        "var_on_pct": float(mm["on_ret"].var() /
                            (mm["on_ret"].var() + mm["rth_ret"].var()) * 100),
        "var_rth_pct": float(mm["rth_ret"].var() /
                             (mm["on_ret"].var() + mm["rth_ret"].var()) * 100),
        "sd_on_pct": float(mm["on_ret"].std() * 100),
        "sd_rth_pct": float(mm["rth_ret"].std() * 100),
        "corr_on_rth": float(mm["on_ret"].corr(mm["rth_ret"])),
        "rv_on_median": float(dd["rv_ON"].median()),
        "rv_rth_median": float(dd["rv_RTH"].median()),
        "brk_vol_median": float(dd["vol_BRK"].median()),
    }
    return out

era_rows = [{"era": n, **era_sessions(a, b)} for n, a, b in ERAS]

# yearly drift table
year_rows = []
for y, dd in d.groupby(pd.DatetimeIndex(d.index).year):
    mm = mk.loc[dd.index]
    year_rows.append({
        "year": int(y),
        "median_vol_total": float(dd["vol_total"].median()),
        "vol_rth_share_median": float(dd["vol_rth_share"].median()),
        "var_on_pct": float(mm["on_ret"].var() /
                            (mm["on_ret"].var() + mm["rth_ret"].var()) * 100),
        "sd_on_pct": float(mm["on_ret"].std() * 100),
        "sd_rth_pct": float(mm["rth_ret"].std() * 100),
        "median_bars_rth": float(dd["nbars_RTH"].median()),
        "median_bars_on": float(dd["nbars_ON"].median()),
    })

# ------------------------------------------------- hour-of-day profiles
# volume share per Chicago hour + mean per-minute |log ret| (bps), per era
m["lret1"] = np.log(m["close"]).groupby([m["sess"], m["hour_chi"]]).diff()
m.loc[m.groupby("sess").head(1).index, "lret1"] = np.nan
prof = {}
for n, a, b in ERAS:
    mm = m[(m["sess"] >= pd.Timestamp(a)) & (m["sess"] <= pd.Timestamp(b))]
    pv = mm.groupby(["sess", "hour_chi"])["volume"].sum().reset_index()
    tot = pv.groupby("sess")["volume"].transform("sum")
    pv["share"] = pv["volume"] / tot
    vsh = pv.groupby("hour_chi")["share"].mean()
    lr = mm.groupby("hour_chi")["lret1"].apply(
        lambda x: float(np.nanmean(np.abs(x))) * 1e4)
    prof[n] = {"vol_share_by_hour_chi": {int(h): round(float(vsh.get(h, 0)), 4)
                                          for h in range(24)},
               "abs_1m_ret_bp_by_hour_chi": {int(h): round(float(lr.get(h, np.nan)), 2)
                                             for h in range(24)}}

# RTH intra-hour structure (front only) — explicit time buckets (Chicago)
rth = m[m["seg"] == "RTH"].copy()
rth["bucket"] = np.where(rth["hhmm"] < 900, "0830-0900",
                  np.where(rth["hhmm"] < 1100, "0900-1100",
                  np.where(rth["hhmm"] < 1300, "1100-1300",
                  np.where(rth["hhmm"] < 1430, "1300-1430",
                  np.where(rth["hhmm"] < 1500, "1430-1500",
                  np.where(rth["hhmm"] < 1600, "1500-1600", "other"))))))
buck = {}
for n, a, b in ERAS:
    rr = rth[(rth["sess"] >= pd.Timestamp(a)) & (rth["sess"] <= pd.Timestamp(b))]
    bv = rr.groupby(["sess", "bucket"])["volume"].sum().reset_index()
    bv["share"] = bv["volume"] / bv.groupby("sess")["volume"].transform("sum")
    buck[n] = {k: round(float(v), 4) for k, v in
               bv.groupby("bucket")["share"].mean().items()}

# Sunday open vs weekday 17:00 hour (volume, per era)
sunday = {}
for n, a, b in ERAS:
    mm = m[(m["sess"] >= pd.Timestamp(a)) & (m["sess"] <= pd.Timestamp(b))]
    s17 = mm[mm["chi"].dt.dayofweek == 6]
    s17 = s17[s17["hour_chi"] == 17]
    w17 = mm[mm["chi"].dt.dayofweek <= 4]
    w17 = w17[w17["hour_chi"] == 17]
    sunday[n] = {
        "sunday_17h_vol_median": float(s17["volume"].median()) if len(s17) else None,
        "weekday_17h_vol_median": float(w17["volume"].median()) if len(w17) else None,
    }

out = {
    "generated_utc": datetime.utcnow().isoformat() + "+00:00",
    "window": [str(d.index.min().date()), str(d.index.max().date())],
    "eras": era_rows,
    "years": year_rows,
    "hour_profiles": prof,
    "rth_buckets": buck,
    "sunday_open": sunday,
    "notes": {
        "front_rule": "VOL chain (prior-session volume argmax, strict past)",
        "segments": "ON 17:00-08:29, RTH 08:30-15:59, BRK 16:00-16:59 (Chicago)",
        "on_ret": "prev session 16:00 close -> 08:30 open (front contract)",
        "rth_ret": "08:30 open -> 16:00 close",
    },
}
with open(os.path.join(HERE, "ES_session_stats.json"), "w") as f:
    json.dump(out, f, indent=1)

# quick print
for r in era_rows:
    print(f"{r['era']:24s} n={r['n_sessions']:4d} vol_med={r['median_front_vol_total']:9.0f} "
          f"RTHsh={r['vol_rth_share_median']:.3f} varON={r['var_on_pct']:5.1f}% "
          f"sdON={r['sd_on_pct']:.2f}% sdRTH={r['sd_rth_pct']:.2f}% corr={r['corr_on_rth']:+.2f}")
print("WROTE ES_session_stats.json")
