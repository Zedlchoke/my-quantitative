#!/usr/bin/env python
"""A5 — CFTC legacy CoT AUD positioning 2006-2026 vs subsequent risk — DEEP-6A.

Descriptive ONLY. Laws: positioning series is as-published weekly (Tue
as-of, Fri 15:30 ET release, no revision — CFTC FAQ, v1 dossier note);
subsequent-vol/drawdown reads are DISTRIBUTIONAL descriptions conditioned on
strict-past positioning states — NOT trade signals, NOT PnL, NOT selection.

Blocks (OBSERVED, script+window stated):
  1. series description 2006-2026: net noncommercial, net commercial, OI;
     regimes of positioning by year; strict-past percentile bands (vs trailing
     3y) — extremes tagged with dates;
  2. strict-past extremes (>90th / <10th percentile of trailing 3y net
     noncomm) -> subsequent 4w / 13w realized vol and max drawdown on the 6A
     held chain (overlap 2020-2026 only; pre-2020 no 6A price in corpus ->
     NOT_RUN and disclosed);
  3. annual pairing: year-end net noncomm vs next-year realized vol (13
     overlap years: 2020..2025 full + 2026 partial) — descriptive table;
  4. crowding metric: net noncomm / open interest vs subsequent vol.

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python 6A_a5_cot.py
Writes: 6A_a5_cot.json
"""
from __future__ import annotations

import importlib.util
import os

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "sixA_deep_lib", os.path.join(_HERE, "6A_deep_lib.py"))
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)

OUT = os.path.join(_HERE, "6A_a5_cot.json")


def main():
    cot = L.load_cot_6a()
    cot["release"] = pd.to_datetime(cot["obs_date"]) + pd.offsets.BDay(3)
    chain = pd.read_parquet(f"{L.CACHE}/chain_daily.parquet")
    chain["session_date"] = pd.to_datetime(chain["session_date"])

    out = {"meta": {
        "lane": "DEEP-6A", "analysis": "A5 CoT positioning",
        "cot_window": [str(cot["obs_date"].min().date()), str(cot["obs_date"].max().date())],
        "price_window": [str(chain["session_date"].min().date()),
                         str(chain["session_date"].max().date())],
        "laws": ("descriptive only; positioning from as-published weekly files; "
                 "subsequent-vol reads are distributional, NOT signals; pre-2020 "
                 "price-side NOT_RUN (no 6A price in corpus before 2020)"),
    }}

    # ---- 1. series description ----------------------------------------------
    cot = cot.sort_values("obs_date").reset_index(drop=True)
    cot["net_noncomm_k"] = cot["net_noncomm"] / 1000.0
    cot["oi_k"] = cot["open_interest_all"] / 1000.0
    cot["crowding"] = cot["net_noncomm"] / cot["open_interest_all"]
    by_year = {}
    for y, g in cot.groupby(cot["obs_date"].dt.year):
        by_year[int(y)] = {
            "n": int(len(g)),
            "net_noncomm_k_mean": float(g["net_noncomm_k"].mean()),
            "net_noncomm_k_min": float(g["net_noncomm_k"].min()),
            "net_noncomm_k_max": float(g["net_noncomm_k"].max()),
            "oi_k_mean": float(g["oi_k"].mean()),
            "crowding_mean": float(g["crowding"].mean()),
        }
    out["series_by_year"] = by_year
    out["series_summary"] = {
        "net_noncomm_k": {"min": float(cot["net_noncomm_k"].min()),
                          "max": float(cot["net_noncomm_k"].max()),
                          "min_date": str(cot.loc[cot["net_noncomm_k"].idxmin(), "obs_date"].date()),
                          "max_date": str(cot.loc[cot["net_noncomm_k"].idxmax(), "obs_date"].date())},
        "note": "net noncommercial = noncomm_long - noncomm_short (legacy futures-only, 6A = AUSTRALIAN DOLLAR - CME mapping verified)",
    }

    # strict-past 3y percentile bands
    pct = []
    for i, r in enumerate(cot.itertuples()):
        lo = max(0, i - 156)
        past = cot["net_noncomm"].iloc[lo:i]
        pct.append(float((r.net_noncomm > past).mean() * 100) if len(past) >= 78 else None)
    cot["pct_past3y"] = pct

    # ---- 2. extremes -> subsequent vol/dd (2020+ overlap) ---------------------
    px = chain.set_index("session_date")
    rets = px["ret_rolled"]

    def fwd_risk(d, weeks):
        end = d + pd.Timedelta(weeks=weeks)
        w = rets[(rets.index > d + pd.Timedelta(days=3)) & (rets.index <= end)].dropna()
        # release lag: CoT usable from obs_date + 3 business days (~release Friday)
        if len(w) < 15:
            return None
        vol_ann = float(w.std() * np.sqrt(252) * 100)
        lvl = px["px"][(px.index > d + pd.Timedelta(days=3)) & (px.index <= end)].dropna()
        dd = float((lvl / lvl.cummax() - 1).min() * 100)
        return {"vol_ann_pct": vol_ann, "max_dd_pct": dd, "n": int(len(w))}

    ex_hi = cot[(cot["pct_past3y"] > 90) & (cot["obs_date"] >= "2020-01-01")]
    ex_lo = cot[(cot["pct_past3y"] < 10) & (cot["obs_date"] >= "2020-01-01")]
    mid = cot[(cot["pct_past3y"].between(25, 75)) & (cot["obs_date"] >= "2020-01-01")]

    def agg(frames):
        res = {"fwd4w": [], "fwd13w": []}
        for r in frames.itertuples():
            for k, wk in [("fwd4w", 4), ("fwd13w", 13)]:
                x = fwd_risk(r.obs_date + pd.offsets.BDay(3), wk)
                if x:
                    res[k].append(x)
        out = {}
        for k in ("fwd4w", "fwd13w"):
            if not res[k]:
                out[k] = None
                continue
            out[k] = {
                "n": len(res[k]),
                "median_vol_ann_pct": float(np.median([x["vol_ann_pct"] for x in res[k]])),
                "median_max_dd_pct": float(np.median([x["max_dd_pct"] for x in res[k]])),
            }
        return out

    out["strict_past_extremes_vs_subsequent_risk"] = {
        "definition": ("tag week with net-noncomm percentile vs TRAILING 3y (strict past); "
                       "subsequent window starts at CoT release (obs + 3 business days); "
                       "overlap era 2020+ only"),
        "high_gt_p90": {"n_weeks": int(len(ex_hi)), **agg(ex_hi)},
        "mid_25_75": {"n_weeks": int(len(mid)), **agg(mid)},
        "low_lt_p10": {"n_weeks": int(len(ex_lo)), **agg(ex_lo)},
        "law_note": "descriptive distributional contrast; NOT a signal table; no PnL evaluation",
    }

    # ---- 3. year-end positioning vs next-year vol -----------------------------
    ye = []
    for y in range(2019, 2025):
        row = cot[cot["obs_date"].dt.year == y].tail(1)
        if not len(row):
            continue
        d = row["obs_date"].iloc[0]
        nxt = rets[(rets.index > f"{y + 1}-01-01") & (rets.index <= f"{y + 1}-12-31")]
        ye.append({
            "as_of": str(d.date()),
            "net_noncomm_k": float(row["net_noncomm_k"].iloc[0]),
            "pct_past3y": (float(row["pct_past3y"].iloc[0])
                           if pd.notna(row["pct_past3y"].iloc[0]) else None),
            "next_year_vol_ann_pct": (float(nxt.std() * np.sqrt(252) * 100)
                                      if len(nxt) > 100 else None),
            "next_year_available": len(nxt) > 100,
        })
    out["year_end_positioning_vs_next_year_vol"] = ye

    # ---- 4. release timing re-check ------------------------------------------
    out["release_timing_check"] = {
        "obs_to_release_gap_days_median": float(
            (cot["release"] - cot["obs_date"]).dt.days.median()),
        "note": "CoT positions as-of Tuesday, released Friday 15:30 ET (FACT, cftc.gov, v1 dossier verification); PIT use = release date, not obs date",
    }

    L.jdump(out, OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
