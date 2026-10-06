"""A7 audit R1 — independent recompute of NQ_DEEP_v2 §1 headline numbers.

Lane A7-DEEP-NQ (fresh-context auditor), task FUTURES-DEEPRESEARCH-V2-20261003.
READ-ONLY on data; writes only under audit/a7_nq/.

Recomputed from the lane's own cache artifacts (nq_held_daily.parquet carries
the held-contract daily series produced by NQ_build_cache/NQ_a1) with a FRESH
implementation (no reuse of NQ_a1 code paths):
  * VR(5/20/60) full-era trailing means (dossier: 0.81 / 0.71 / 0.67)
  * ACF(1) full-era and rolling-252d median
  * v1-window (2025-05-30+) rvol20 median percentile within 2010-2024 (57th)
  * calendar-rule ann vol 19.6% vs volume-rule 16.9%
  * rvol20 median/max (16.1% / 92.4% 2020-03-27) and vol tercile counts
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
AN = os.path.dirname(os.path.dirname(HERE)) + "/analysis"  # task dir/analysis
CACHE = f"{AN}/NQ_cache"
OUT = os.path.join(HERE, "r1_regime_recheck.json")

res = {"schema": "a7_nq_r1_regime_recheck@1", "inputs": {
    "held_daily": f"{CACHE}/nq_held_daily.parquet",
    "sessions": f"{CACHE}/nq_sessions.parquet",
    "held_volume_k5": f"{CACHE}/held_volume_k5.parquet",
    "held_calendar": f"{CACHE}/held_calendar.parquet"}}

d = pd.read_parquet(f"{CACHE}/nq_held_daily.parquet")
d["d"] = pd.to_datetime(d["d"])
d = d.sort_values("d").reset_index(drop=True)
ret = d["ret"]

# --- VR(5/20/60): trailing-252d rolling variance basis, mean of last 252 obs
def vr(rets: pd.Series, q: int) -> float:
    var1 = rets.rolling(252, min_periods=189).var()
    varq = rets.rolling(q, min_periods=q).sum().rolling(252, min_periods=189).var()
    v = (varq / (q * var1)).dropna()
    return float(v.iloc[-252:].mean())

res["variance_ratios"] = {f"vr_{q}": vr(ret, q) for q in (5, 20, 60)}

# --- ACF(1)
res["acf1_full"] = float(ret.autocorr(1))
roll_acf = ret.rolling(252).apply(
    lambda x: np.corrcoef(x[:-1], x[1:])[0, 1], raw=True).dropna()
res["acf1_rolling252_median"] = float(roll_acf.median())
res["acf1_rolling252_p10_p90"] = [float(x) for x in roll_acf.quantile([.1, .9])]

# --- rvol20 distribution
rv20 = ret.rolling(20, min_periods=15).std() * np.sqrt(252)
res["rvol20_median_pct"] = float(100 * rv20.dropna().median())
res["rvol20_max_pct"] = float(100 * rv20.dropna().max())
res["rvol20_argmax_date"] = str(d["d"][rv20.dropna().idxmax()].date())
res["rvol20_min_pct"] = float(100 * rv20.dropna().min())
res["rvol20_argmin_date"] = str(d["d"][rv20.dropna().idxmin()].date())

# --- v1 window context
v1w = d["d"] >= pd.Timestamp("2025-05-30")
prior = d["d"] < pd.Timestamp("2025-01-01")
v1_rvol = rv20[v1w].dropna()
prior_rvol = rv20[prior].dropna()
res["v1_window"] = {
    "rvol20_median_pct": float(100 * v1_rvol.median()),
    "percentile_in_2010_2024": float((prior_rvol < v1_rvol.median()).mean()),
    "p10_p90_2010_2024_pct": [float(100 * prior_rvol.quantile(.1)),
                              float(100 * prior_rvol.quantile(.9))],
    "rvol20_range_pct": [float(100 * v1_rvol.min()), float(100 * v1_rvol.max())],
    "max_dd_pct": float(-100 * d.loc[v1w, "dd"].min())}

# --- calendar vs volume rule vol (both from session closes, fresh merge)
sess = pd.read_parquet(f"{CACHE}/nq_sessions.parquet")
held = pd.read_parquet(f"{CACHE}/held_volume_k5.parquet")
held_cal = pd.read_parquet(f"{CACHE}/held_calendar.parquet")


def daily_ret(h: pd.DataFrame) -> pd.Series:
    m = sess.merge(h.rename(columns={"held": "contract"}),
                   on=["session_date", "contract"], how="inner")
    m = m.sort_values("session_date")
    lc = np.log(m["close"].astype(float))
    return lc.diff().dropna()

res["vol_rule"] = {"n": int(len(daily_ret(held))),
                   "ann_vol_pct": float(100 * daily_ret(held).std() * np.sqrt(252))}
rc = daily_ret(held_cal)
res["calendar_rule"] = {"n": int(len(rc)),
                        "ann_vol_pct": float(100 * rc.std() * np.sqrt(252))}

# --- n rolls and sessions
res["n_rolls_volume_k5"] = int((held["held"] != held["held"].shift()).sum() - 1)
res["n_sessions_held_daily"] = int(len(d))

with open(OUT, "w") as fh:
    json.dump({k: (v if not isinstance(v, dict) else v) for k, v in res.items()},
              fh, indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
