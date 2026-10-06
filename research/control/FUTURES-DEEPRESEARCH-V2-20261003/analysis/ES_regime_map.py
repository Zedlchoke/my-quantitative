#!/usr/bin/env python
"""ES deep-research v2 — A1 strict-past regime map 2010-2026 (lane DEEP-ES).

DESCRIPTIVE ONLY: no PnL, no signal ranking. Returns are computed on the
ratio-back-adjusted VOL chain (front quarterly selected by prior-session
volume, strict past; switch sessions carry no artificial jump because the
adjustment is applied at the switch). Vol-regime tags use TRAILING windows
only (the tag on day t uses returns up to t-1; ex-post labels descriptive).

Outputs: ES_regime_stats.json (+ per-year table printed).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python ES_regime_map.py
"""
import json
import os
from datetime import datetime

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "ES_cache")

ch = pd.read_parquet(os.path.join(CACHE, "es_chain_VOL.parquet")).sort_index()
ch["year"] = ch.index.year

# daily log/simple returns on ratio-adjusted close (no roll jumps embedded)
ch["ret"] = ch["close_adj"].pct_change()
ch["lret"] = np.log(ch["close_adj"]).diff()

# sanity: roll-boundary contamination check — compare VOL-chain returns on
# switch vs non-switch sessions using same-contract returns
sw = ch["switch"].fillna(False).astype(bool)
same_ret = ch["close"].pct_change()
same_ret[sw] = np.nan            # true same-contract daily returns, switch days excluded
print("switch sessions:", int(sw.sum()),
      "| max |ret| on switch days (should be ~market, adj removes jump):",
      round(ch.loc[sw, "ret"].abs().max(), 4))

ERAS = [
    ("E1 2010-06..2012-12 FIX/FAST 2nd-prec-era | post-GFC/EU-crisis", "2010-06-07", "2012-12-31"),
    ("E2 2013-01..2015-11 pre-ms-precision | taper->liftoff", "2013-01-01", "2015-11-19"),
    ("E3 2015-11..2017-05 ms-prec FIX/FAST | late- QE / low-vol start", "2015-11-20", "2017-05-20"),
    ("E4 2017-05..2020-02 MDP3-native | low-vol era", "2017-05-21", "2020-02-19"),
    ("E5 2020-02..2021-12 | COVID crisis + recovery", "2020-02-20", "2021-12-31"),
    ("E6 2022-01..2023-09 | hiking bear + 2023 rally", "2022-01-01", "2023-09-30"),
    ("E7 2023-10..2026-10 AV1T-era | AI bull", "2023-10-01", "2026-10-01"),
]

def era_stats(sub, name):
    r = sub["ret"].dropna()
    lr = sub["lret"].dropna()
    if len(r) < 30:
        return None
    out = {
        "era": name, "n_days": int(len(r)),
        "first": r.index.min().date().isoformat(),
        "last": r.index.max().date().isoformat(),
        "mean_bp_day": float(r.mean() * 1e4),
        "ann_vol_pct": float(r.std() * np.sqrt(252) * 100),
        "skew": float(r.skew()), "excess_kurtosis": float(r.kurtosis()),
        "min_pct": float(r.min() * 100), "max_pct": float(r.max() * 100),
        "pct_days_gt1pct": float((r.abs() > 0.01).mean() * 100),
        "pct_days_gt2pct": float((r.abs() > 0.02).mean() * 100),
        "pct_days_gt3pct": float((r.abs() > 0.03).mean() * 100),
    }
    # multi-horizon vol + variance ratios (trend persistence descriptor)
    logpx = np.log(ch["close_adj"])
    for q in (1, 5, 20, 63):
        rq = logpx.diff(q).reindex(sub.index).dropna()
        out[f"vol_{q}d_ann_pct"] = float(rq.std() * np.sqrt(252 / q) * 100) if len(rq) > q else None
    v1 = logpx.diff().reindex(sub.index).dropna().var()
    for q in (5, 20, 63):
        rq = np.log(ch["close_adj"]).diff(q).reindex(sub.index).dropna()
        out[f"VR_q{q}"] = float(rq.var() / (q * v1)) if len(rq) > q + 5 and v1 > 0 else None
    # lag-1 autocorr (daily) + |ret| autocorr (vol clustering), overlapping q for 5d
    out["acf1_daily"] = float(r.autocorr(1))
    out["acf1_absret"] = float(r.abs().autocorr(1))
    r5 = np.log(ch["close_adj"]).diff(5).reindex(sub.index).dropna()
    out["acf1_5d"] = float(r5.autocorr(1)) if len(r5) > 30 else None
    # drawdown anatomy within era
    px = sub["close_adj"].dropna()
    dd = px / px.cummax() - 1
    out["max_drawdown_pct"] = float(dd.min() * 100)
    out["max_dd_date"] = dd.idxmin().date().isoformat()
    underwater = (px < px.cummax())
    # longest underwater spell (sessions)
    runs = []
    c = 0
    for u in underwater:
        c = c + 1 if u else 0
        runs.append(c)
    out["longest_underwater_sessions"] = int(max(runs)) if runs else 0
    return out

era_rows = []
for name, a, b in ERAS:
    sub = ch.loc[a:b]
    st = era_stats(sub, name)
    if st:
        era_rows.append(st)

# per-year table
year_rows = []
for y, sub in ch.groupby("year"):
    r = sub["ret"].dropna()
    px = sub["close_adj"].dropna()
    dd = px / px.cummax() - 1
    year_rows.append({
        "year": int(y), "n_days": int(len(r)),
        "ret_yr_pct": float((px.iloc[-1] / px.iloc[0] - 1) * 100) if len(px) > 1 else None,
        "ann_vol_pct": float(r.std() * np.sqrt(252) * 100),
        "mean_bp_day": float(r.mean() * 1e4),
        "max_dd_pct": float(dd.min() * 100),
        "worst_day_pct": float(r.min() * 100),
        "best_day_pct": float(r.max() * 100),
        "pct_days_gt2pct": float((r.abs() > 0.02).mean() * 100),
    })

# top-15 |ret| days (descriptive extremes, with context labels appended in dossier)
ext = ch["ret"].abs().nlargest(15)
extremes = [{
    "date": d.date().isoformat(), "ret_pct": float(ch.loc[d, "ret"] * 100),
    "level": float(ch.loc[d, "close_adj"]),
} for d in ext.index]

# trailing-vol regime occupancy (PIT-legal descriptor): tercile thresholds
# from trailing 1000 sessions ending t-1; day tagged Low/Mid/High
vol63 = ch["lret"].rolling(63).std() * np.sqrt(252) * 100
vshift = vol63.shift(1)
q1 = vshift.rolling(1000, min_periods=300).quantile(1 / 3)
q2 = vshift.rolling(1000, min_periods=300).quantile(2 / 3)
regime = np.where(vol63 < q1, "LOW", np.where(vol63 > q2, "HIGH", "MID"))
regime = np.where(q1.isna() | vol63.isna(), "NAN", regime)
regser = pd.Series(regime, index=ch.index, name="vol_regime_trailing")
regser.to_frame().to_parquet(os.path.join(CACHE, "es_vol_regime.parquet"))
occupancy = regser.value_counts(normalize=True).round(3).to_dict()

# rolling-vol summary across full sample
v21 = (ch["lret"].rolling(21).std() * np.sqrt(252) * 100)
v252 = (ch["lret"].rolling(252).std() * np.sqrt(252) * 100)

out = {
    "generated_utc": datetime.utcnow().isoformat() + "+00:00",
    "chain": "VOL (prior-session volume argmax, strict past), ratio-back-adjusted",
    "window": [ch.index.min().date().isoformat(), ch.index.max().date().isoformat()],
    "n_sessions": int(len(ch)),
    "switch_sessions": int(sw.sum()),
    "full_sample": {
        "n_ret_days": int(ch["ret"].notna().sum()),
        "mean_bp_day": float(ch["ret"].mean() * 1e4),
        "ann_vol_pct": float(ch["ret"].std() * np.sqrt(252) * 100),
        "skew": float(ch["ret"].skew()),
        "excess_kurtosis": float(ch["ret"].kurtosis()),
        "acf1_daily": float(ch["ret"].autocorr(1)),
        "acf1_absret": float(ch["ret"].abs().autocorr(1)),
        "acf1_5d": float(np.log(ch["close_adj"]).diff(5).autocorr(1)),
        "vol21_pctiles": {q: float(v21.quantile(q / 100))
                          for q in (5, 25, 50, 75, 95)},
        "vol252_min": float(v252.min()), "vol252_max": float(v252.max()),
        "vol252_max_date": v252.idxmax().date().isoformat(),
        "vol252_min_date": v252.idxmin().date().isoformat(),
    },
    "trailing_vol_regime_occupancy": occupancy,
    "eras": era_rows,
    "years": year_rows,
    "extreme_days": extremes,
}
with open(os.path.join(HERE, "ES_regime_stats.json"), "w") as f:
    json.dump(out, f, indent=1)
print(json.dumps(out["full_sample"], indent=1))
print("era rows:", len(era_rows), "| year rows:", len(year_rows))
print("WROTE ES_regime_stats.json")
