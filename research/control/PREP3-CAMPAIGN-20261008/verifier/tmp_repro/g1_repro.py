#!/usr/bin/env python
"""g1_sigma20_sensitivity.py — LANE G (NQ-F3X FEASIBILITY), PREP only.

CENSUS_FEATURE_ONLY: replicates lane B's b1_census.py PIT feature pipeline and
recomputes the run_stretch_sigma tercile bounds under variant sigma20
conventions. ZERO outcome/PnL anywhere: the only columns read are
d, close, ret, rth_coverage, contract; no forward return, no per-trade PnL,
no intent-packet exit price is consumed. The trigger SET is fixed by the
frozen law (sigma20 plays no role in it); variants change only the stretch
FEATURE value, hence tercile bounds and cell membership.

Variants (all else identical to the pin):
  V0 PIN  : w = ret[i-20:i], min 15 valid rets, ddof=1, panel log rets
  V1      : ddof=0 (population std), else V0
  V2      : simple close-to-close rets (same NaN positions), ddof=1
  V3      : window ret[i-21:i] (21 rets), ddof=1
  V4      : window ret[i-19:i+1] (trigger-day ret INCLUDED), ddof=1
  V5      : min 2 valid rets (lane F verifier convention, F-VF-01), else V0

Sanity anchors (must reproduce to machine precision):
  V0 -> B1_FEATURE_CENSUS.json DN bounds [1.409113756644449, 1.9353218450806864]
  V5 -> f4_census_check_result.json DN bounds [1.3571752347959558, 1.8966051746129284]
"""
from __future__ import annotations

import hashlib
import json
import os

import numpy as np
import pandas as pd

WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-mechrecon-prep/prep"
CACHE = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep"
         "/research/control/FUTURES-SIX-READINESS-20261004/nq/cache_v3")
ES_FOMC = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep"
           "/research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_fomc_stats.json")
OUT = "/Users/hoangminhlong/my-quantitative/research/control/PREP3-CAMPAIGN-20261008/verifier/tmp_repro/g1_repro.json"

K_RUN = 5
HELD = hd = pd.read_parquet(os.path.join(CACHE, "nq_held_daily_v3.parquet")).sort_values(
    "d").reset_index(drop=True)
dts = HELD["d"].astype(str).str.slice(0, 10).to_numpy()
close = HELD["close"].astype(float).to_numpy()          # index points x1e9
ret_log = HELD["ret"].astype(float).to_numpy()          # panel NaN-aware chain LOG rets
cov = HELD["rth_coverage"].astype(float).to_numpy()
contract = HELD["contract"].astype(str).to_numpy()
n = len(HELD)

# simple returns pinned to the SAME NaN positions as the panel log rets
ret_simple = np.where(np.isnan(ret_log), np.nan, close / np.roll(close, 1) - 1.0)
ret_simple[0] = np.nan

# run lengths (b1/f4 chain law) — sign of log vs simple is identical at daily
# magnitudes, so the trigger set is variant-independent
def run_lengths(ret):
    rl = np.zeros(n, dtype=int)
    prev_sign, run = 0, 0
    for i in range(n):
        s = ret[i]
        if np.isnan(s):
            rl[i] = 0
            prev_sign, run = 0, 0
            continue
        sign = 1 if s > 0 else (-1 if s < 0 else 0)
        run = run + 1 if (sign != 0 and sign == prev_sign) else (1 if sign != 0 else 0)
        if sign != 0:
            prev_sign = sign
        rl[i] = run
    return rl

rl = run_lengths(ret_log)
fomc = set(r["date"] for r in json.load(open(ES_FOMC))["per_event_day_level"])

# declared trigger set (H1 low-coverage entry + E1 FOMC-day entry refused),
# exactly b1's law; sigma20 never enters the trigger definition
declared = []
for i in range(1, n):
    if rl[i] >= K_RUN and rl[i - 1] < K_RUN:
        tail = "UP" if ret_log[i] > 0 else ("DN" if ret_log[i] < 0 else None)
        if tail is None:
            continue
        e = i + 1
        if e >= n:
            continue
        if cov[e] < 0.60:
            continue
        if str(dts[e]) in fomc:
            continue
        declared.append({"i": int(i), "date": str(dts[i]), "tail": tail})

# warmup cut: entry bar index >= 252 (b1: entry session index < warmup excluded)
WARMUP = 252


def sigma20(i, ret, lo_off, hi_off, min_valid, ddof):
    w = ret[max(0, i + lo_off): i + hi_off]
    w = w[~np.isnan(w)]
    return float(np.std(w, ddof=ddof)) if len(w) >= min_valid else np.nan


VARIANTS = {
    "V0_PIN": dict(ret="log", lo=-20, hi=0, min_valid=15, ddof=1),
    "V1_DDOF0": dict(ret="log", lo=-20, hi=0, min_valid=15, ddof=0),
    "V2_SIMPLE": dict(ret="simple", lo=-20, hi=0, min_valid=15, ddof=1),
    "V3_WIN21": dict(ret="log", lo=-21, hi=0, min_valid=15, ddof=1),
    "V4_INCL_TRIGDAY": dict(ret="log", lo=-19, hi=1, min_valid=15, ddof=1),
    "V5_MINVAL2": dict(ret="log", lo=-20, hi=0, min_valid=2, ddof=1),
}

results = {}
for vname, v in VARIANTS.items():
    r = ret_log if v["ret"] == "log" else ret_simple
    rows = []
    for t in declared:
        i = t["i"]
        if i < K_RUN or np.isnan(close[i - K_RUN]):
            continue
        c5 = close[i] / close[i - K_RUN] - 1.0
        s20 = sigma20(i, r, v["lo"], v["hi"], v["min_valid"], v["ddof"])
        stretch = (abs(c5) / (s20 * np.sqrt(K_RUN))
                   if (not np.isnan(s20) and s20 > 0) else np.nan)
        rows.append({"date": t["date"], "tail": t["tail"], "stretch": stretch,
                     "warmup_ok": i >= WARMUP})
    per_tail = {}
    for tail in ("UP", "DN"):
        s = np.array([x["stretch"] for x in rows
                      if x["tail"] == tail and not np.isnan(x["stretch"])])
        t1, t2 = float(np.quantile(s, 1 / 3)), float(np.quantile(s, 2 / 3))
        top_dates = [x["date"] for x in rows
                     if x["tail"] == tail and not np.isnan(x["stretch"])
                     and x["stretch"] >= t2]
        top_after_warmup = [x["date"] for x in rows
                            if x["tail"] == tail and not np.isnan(x["stretch"])
                            and x["stretch"] >= t2 and x["warmup_ok"]]
        per_tail[tail] = {
            "n_valid_stretch": int(len(s)),
            "tercile_bounds_sigma": [t1, t2],
            "n_high": int((s >= t2).sum()),
            "n_high_after_warmup": len(top_after_warmup),
            "top_cell_dates_after_warmup": top_after_warmup,
        }
    results[vname] = per_tail

# shifts vs pin
pin_dn = results["V0_PIN"]["DN"]["tercile_bounds_sigma"]
pin_up = results["V0_PIN"]["UP"]["tercile_bounds_sigma"]
shifts = {}
for vname in VARIANTS:
    dn = results[vname]["DN"]["tercile_bounds_sigma"]
    up = results[vname]["UP"]["tercile_bounds_sigma"]
    shifts[vname] = {
        "DN_top_bound_abs_shift": dn[1] - pin_dn[1],
        "DN_top_bound_pct_shift": dn[1] / pin_dn[1] - 1.0,
        "UP_top_bound_abs_shift": up[1] - pin_up[1],
        "UP_top_bound_pct_shift": up[1] / pin_up[1] - 1.0,
        "DN_top_cell_n_after_warmup": results[vname]["DN"]["n_high_after_warmup"],
        "DN_top_cell_same_as_pin": (results[vname]["DN"]["top_cell_dates_after_warmup"]
                                    == results["V0_PIN"]["DN"]["top_cell_dates_after_warmup"]),
    }

anchors = {
    "V0_vs_B1_census": {
        "expected": [1.409113756644449, 1.9353218450806864],
        "got": pin_dn,
        "match": bool(np.allclose(pin_dn, [1.409113756644449, 1.9353218450806864],
                                  rtol=0, atol=1e-12)),
    },
    "V5_vs_F4_verifier": {
        "expected": [1.3571752347959558, 1.8966051746129284],
        "got": results["V5_MINVAL2"]["DN"]["tercile_bounds_sigma"],
        "match": bool(np.allclose(results["V5_MINVAL2"]["DN"]["tercile_bounds_sigma"],
                                  [1.3571752347959558, 1.8966051746129284],
                                  rtol=0, atol=1e-12)),
    },
}

out = {
    "schema": "lane_g_sigma20_convention_sensitivity@1",
    "lane": "G_NQF3X_FEAS",
    "campaign": "PREP-FUTURES-MECHRECON-20261008",
    "label": "CENSUS_FEATURE_ONLY — zero outcome/PnL columns read anywhere",
    "columns_read": ["d", "close", "ret", "rth_coverage", "contract"],
    "inputs_sha256": {
        "nq_held_daily_v3.parquet": hashlib.sha256(
            open(os.path.join(CACHE, "nq_held_daily_v3.parquet"), "rb").read()).hexdigest(),
    },
    "declared_trigger_count": len(declared),
    "pin_convention": VARIANTS["V0_PIN"],
    "variants": VARIANTS,
    "bounds": results,
    "shifts_vs_pin": shifts,
    "reproduction_anchors": anchors,
}
with open(OUT, "w") as fh:
    json.dump(out, fh, indent=1)
print(json.dumps({"anchors": anchors,
                  "DN_bounds": {v: results[v]["DN"]["tercile_bounds_sigma"] for v in VARIANTS},
                  "UP_bounds": {v: results[v]["UP"]["tercile_bounds_sigma"] for v in VARIANTS},
                  "DN_top_n_after_warmup": {v: results[v]["DN"]["n_high_after_warmup"] for v in VARIANTS}},
                 indent=1))
