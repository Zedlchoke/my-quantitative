"""A7 audit R2 — independent recompute of NQ_DEEP_v2 §2 session-structure numbers.

Fresh implementation from NQ_cache/nq_annotated_1m.parquet + held_volume_k5:
  * overnight (17:00->08:30 CT) volume share by year: 2010 10.2% -> 2026 23.8%
  * first-30-min RTH share by era (16.2/17.2/17.1/16.0/15.6%)
  * 07:30 CT minute-volume share vs neighbors, 2023-26 (0.185% vs 0.041/0.089)
  * clean-session gating (n=4,016 of 4,170) — RTH-core coverage >= 0.6

DST-correct America/Chicago; session date = local day, >=17:00 rolls to next day.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.dirname(os.path.dirname(HERE)) + "/analysis/NQ_cache"
OUT = os.path.join(HERE, "r2_sessions_recheck.json")

CHI = "America/Chicago"

df = pd.read_parquet(f"{CACHE}/nq_annotated_1m.parquet",
                     columns=["dt", "close", "volume", "contract", "session_date"])
held = pd.read_parquet(f"{CACHE}/held_volume_k5.parquet")
df = df.merge(held.rename(columns={"held": "contract"}),
              on=["contract", "session_date"], how="inner")
loc = df["dt"].dt.tz_convert(CHI)
hhmm = loc.dt.hour * 60 + loc.dt.minute
df["d"] = pd.to_datetime(df["session_date"])

res = {"schema": "a7_nq_r2_sessions_recheck@1",
       "n_held_1m_bars": int(len(df))}

# RTH coverage per session (core 08:30-15:00 = 390 min) for clean gating
core = df[(hhmm >= 510) & (hhmm < 900)]
cov = core.groupby("d").size() / 390.0
clean_dates = set(cov[cov >= 0.6].index)
res["n_sessions_held"] = int(df["d"].nunique())
res["n_clean_sessions"] = len(clean_dates)

# overnight share: full session = all held bars of the session; OVN = 17:00->08:30
ovn = df[(hhmm >= 1020) | (hhmm < 510)]
tot_by_year = df[df["d"].isin(clean_dates)].groupby(df["d"].dt.year)["volume"].sum()
ovn_by_year = ovn[ovn["d"].isin(clean_dates)].groupby(ovn["d"].dt.year)["volume"].sum()
share = (ovn_by_year / tot_by_year)
res["ovn_share_by_year_pct"] = {int(k): round(100 * v, 2)
                                for k, v in share.items()}

# first-30-min RTH share by dossier eras
ERAS = [("2010-06_2012-12", "2010-06-07", "2012-12-31"),
        ("2013-01_2016-09", "2013-01-01", "2016-09-30"),
        ("2017-01_2020-02", "2017-01-01", "2020-02-21"),
        ("2020-06_2022-12", "2020-06-01", "2022-12-30"),
        ("2023-01_2026-09", "2023-01-01", "2026-10-01")]
era_out = {}
for name, a, b in ERAS:
    w = df[(df["d"] >= a) & (df["d"] <= b) & df["d"].isin(clean_dates)]
    tot = w["volume"].sum()
    rth = w[(hhmm.reindex(w.index) >= 510) & (hhmm.reindex(w.index) < 900)]
    o30 = w[(hhmm.reindex(w.index) >= 510) & (hhmm.reindex(w.index) < 540)]
    era_out[name] = {"first30_share_of_rth_pct": round(100 * o30["volume"].sum()
                                                       / rth["volume"].sum(), 2)}
res["era_first30_share"] = era_out

# minute-of-day volume shares, 2023-26 era, around 07:30 CT (450)
w = df[(df["d"] >= "2023-01-01") & df["d"].isin(clean_dates)]
sv = w.groupby(hhmm.reindex(w.index))["volume"].sum()
sv = sv / sv.sum()
res["minute_share_2023_26_pct"] = {
    "0725": round(100 * float(sv.loc[445]), 4),
    "0729": round(100 * float(sv.loc[449]), 4),
    "0730": round(100 * float(sv.loc[450]), 4),
    "0731": round(100 * float(sv.loc[451]), 4),
    "0735": round(100 * float(sv.loc[455]), 4)}
# and the quiet era 2017-01..2020-02 share at 07:30
w2 = df[(df["d"] >= "2017-01-01") & (df["d"] <= "2020-02-21")
        & df["d"].isin(clean_dates)]
sv2 = w2.groupby(hhmm.reindex(w2.index))["volume"].sum()
sv2 = sv2 / sv2.sum()
res["minute_share_0730_2017_20_pct"] = round(100 * float(sv2.loc[450]), 4)

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
