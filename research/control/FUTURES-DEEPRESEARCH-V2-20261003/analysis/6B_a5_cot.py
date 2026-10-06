"""6B v2 a5 — CFTC legacy CoT POUND STERLING (COT_LEGACY_6B) 2006-2026:
positioning level/z vs SUBSEQUENT realized vol + drawdowns (descriptive,
|ret|-based; no signed mean-return conditioning). Emits 6B_a5_cot.json."""
from __future__ import annotations

import importlib.util
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "six_b_deep_lib", os.path.join(HERE, "6B_deep_lib.py"))
lib = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lib)

OUT = {}

cot = lib.load_cot_6b()
cot["rel"] = pd.to_datetime(cot["released_at"].str[:10])
cot = cot.sort_values("obs").reset_index(drop=True)

# strict-past rolling z (156w window, min 3y) of net noncomm / OI
cot["nn_ratio"] = cot["net_noncomm"] / cot["open_interest_all"]
mu = cot["nn_ratio"].rolling(156, min_periods=156).mean().shift(1)
sd = cot["nn_ratio"].rolling(156, min_periods=156).std().shift(1)
cot["z"] = (cot["nn_ratio"] - mu) / sd
cot["oi_ma26"] = cot["open_interest_all"].rolling(26).mean().shift(1)

# forward outcomes on the 6B quarterly chain (calendar rule), 2006+ where CoT
# starts — the chain only exists 2020+ here; forward vol/drawdown from 2020.
chain = pd.read_parquet(os.path.join(lib.CACHE, "chain_calendar.parquet"))
chain["d"] = pd.to_datetime(chain["session_date"])
c = chain.dropna(subset=["ret"]).reset_index(drop=True)

fwd = []
h = 20  # sessions (~4 weeks)
c["fwd_vol20"] = c["ret"].rolling(h).std().shift(-h) * np.sqrt(252) * 100
# forward drawdown LOCAL to the 20-session window (peak resets at window
# start; NOT contaminated by the secular 2021-22 decline)
px = c["close"].values
fdd = np.full(len(px), np.nan)
for i in range(len(px) - h):
    w = px[i:i + h + 1]
    fdd[i] = (w / np.maximum.accumulate(w) - 1.0).min()
c["fwd_maxdd20"] = fdd

m = cot.dropna(subset=["z"])[["obs", "z", "nn_ratio", "net_noncomm",
                              "net_comm", "open_interest_all", "oi_ma26"]].copy()
m = m.merge(c[["d", "fwd_vol20", "fwd_maxdd20", "ret"]],
            left_on="obs", right_on="d", how="inner")
m = m.dropna(subset=["fwd_vol20"])

buckets = pd.cut(m["z"], [-np.inf, -1.5, -0.5, 0.5, 1.5, np.inf],
                 labels=["z<-1.5", "-1.5..-0.5", "-0.5..0.5", "0.5..1.5", "z>1.5"])
g = m.groupby(buckets, observed=True)
OUT["forward_20s_outcomes_by_z_bucket"] = {
    str(k): {"n": int(len(v)), "median_fwd_vol20_pct": float(v["fwd_vol20"].median()),
             "p90_fwd_vol20_pct": float(v["fwd_vol20"].quantile(.9)),
             "median_fwd_maxdd20_pct": float(v["fwd_maxdd20"].median() * 100),
             "p05_fwd_maxdd20_pct": float(v["fwd_maxdd20"].quantile(.05) * 100)}
    for k, v in g}
OUT["corr_abs_z_fwd_vol20"] = float(m["z"].abs().corr(m["fwd_vol20"]))
OUT["corr_z_fwd_vol20"] = float(m["z"].corr(m["fwd_vol20"]))
OUT["n_obs"] = int(len(m))
OUT["span"] = [str(m["obs"].min().date()), str(m["obs"].max().date())]

# extremes episodes list (|z|>1.5) with forward outcome
ext = m[m["z"].abs() > 1.5]
OUT["extreme_episodes"] = [
    {"obs": str(t.obs.date()), "z": round(float(t.z), 2),
     "net_noncomm": int(t.net_noncomm), "fwd_vol20_pct": round(float(t.fwd_vol20), 2),
     "fwd_maxdd20_pct": round(float(t.fwd_maxdd20) * 100, 2)}
    for t in ext.itertuples()]

# 2022 turmoil positioning snapshot
snap = cot[(cot["obs"] >= "2022-08-01") & (cot["obs"] <= "2022-11-30")].copy()
fwd_lut = m.set_index("obs")[["fwd_vol20"]]
snap["fwd_vol20"] = snap["obs"].map(fwd_lut["fwd_vol20"])
OUT["turmoil_2022_positioning"] = [
    {"obs": str(t.obs.date()), "z": None if pd.isna(t.z) else round(float(t.z), 2),
     "net_noncomm": int(t.net_noncomm), "net_comm": int(t.net_comm),
     "oi": int(t.open_interest_all),
     "fwd_vol20_pct": None if pd.isna(t.fwd_vol20) else round(float(t.fwd_vol20), 2)}
    for t in snap.itertuples()]

# positioning long-run descriptives
OUT["net_noncomm_stats_2006_2026"] = {
    "median": float(cot["net_noncomm"].median()),
    "q05": float(cot["net_noncomm"].quantile(.05)),
    "q95": float(cot["net_noncomm"].quantile(.95)),
    "min": float(cot["net_noncomm"].min()), "max": float(cot["net_noncomm"].max()),
    "argmin_obs": str(cot.loc[cot["net_noncomm"].idxmin(), "obs"].date()),
    "argmax_obs": str(cot.loc[cot["net_noncomm"].idxmax(), "obs"].date()),
}
# OI structural level by era
cot["era"] = pd.cut(cot["obs"].dt.year,
                    [2005, 2009, 2013, 2017, 2021, 2027],
                    labels=["2006-09", "2010-13", "2014-17", "2018-21", "2022-26"])
OUT["oi_median_by_era"] = {str(k): float(v) for k, v in
                           cot.groupby("era", observed=True)["open_interest_all"].median().items()}
# release-lag sanity: released_at Friday after obs Tuesday
lag = (cot["rel"] - cot["obs"]).dt.days
OUT["release_lag_days"] = {"median": float(lag.median()), "min": int(lag.min()),
                           "max": int(lag.max())}

lib.jdump(OUT, os.path.join(HERE, "6B_a5_cot.json"))
print("a5 done. buckets:", {k: (v['n'], round(v['median_fwd_vol20_pct'],2))
      for k, v in OUT['forward_20s_outcomes_by_z_bucket'].items()})
print("corr |z| vs fwd vol:", OUT["corr_abs_z_fwd_vol20"])
