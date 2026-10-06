#!/usr/bin/env python
"""A7-DEEP-6A CoT recompute on the FIXED tidy (+ pre-fix backup comparison).

The CFTC legacy tidy was regenerated 2026-10-03 08:43 by lane INTEGRATION-FIX-V2
(exact market-name mapping) — AFTER DEEP-6A's 6A_a5_cot.py ran (07:51), so the
dossier's CoT numbers were computed on the PRE-FIX tidy. This script recomputes
the dossier's 6A CoT claims on both tides and flags changes.
"""
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
NP = "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms"


def load(path):
    df = pd.read_parquet(path)
    a = df[df["series_id"] == "COT_LEGACY_6A"].copy()
    a["obs_date"] = pd.to_datetime(a["observation_period"])
    a["net_noncomm"] = a["noncomm_long"] - a["noncomm_short"]
    a["crowding"] = a["net_noncomm"] / a["open_interest_all"]
    return a.sort_values("obs_date").reset_index(drop=True)


def summarize(a, label):
    out = {"label": label, "n_rows": int(len(a)),
           "span": [str(a["obs_date"].min().date()), str(a["obs_date"].max().date())],
           "dup_obs_dates": int(a["obs_date"].duplicated().sum()),
           "market_names": (a["market_name"].unique().tolist()
                            if "market_name" in a.columns else None),
           "net_noncomm_k_min": round(float(a["net_noncomm"].min() / 1e3), 2),
           "net_noncomm_k_min_date": str(a.loc[a["net_noncomm"].idxmin(), "obs_date"].date()),
           "net_noncomm_k_max": round(float(a["net_noncomm"].max() / 1e3), 2),
           "net_noncomm_k_max_date": str(a.loc[a["net_noncomm"].idxmax(), "obs_date"].date())}
    yearly = {}
    for y, g in a.groupby(a["obs_date"].dt.year):
        yearly[int(y)] = {
            "n": int(len(g)),
            "net_noncomm_k_mean": round(float(g["net_noncomm"].mean() / 1e3), 2),
            "net_noncomm_k_max": round(float(g["net_noncomm"].max() / 1e3), 2),
            "net_noncomm_k_min": round(float(g["net_noncomm"].min() / 1e3), 2),
            "oi_k_mean": round(float(g["open_interest_all"].mean() / 1e3), 1),
            "crowding_mean": round(float(g["crowding"].mean()), 4)}
    out["by_year"] = yearly
    return out


def main():
    fixed = load(f"{NP}/normalized/cftc_legacy_tidy.parquet")
    prefix = load(f"{NP}/normalized/cftc_legacy_tidy.parquet.bak_prefix_mixed_20261003")
    res = {"fixed_tidy": summarize(fixed, "FIXED (exact-name, 2026-10-03 08:43)"),
           "prefix_tidy": summarize(prefix, "PRE-FIX backup (substring-mixed)")}
    # row-level diff between tides for 6A
    m = fixed.merge(prefix, on="obs_date", suffixes=("_fx", "_pf"), how="outer",
                   indicator=True)
    both = m[m["_merge"] == "both"]
    res["row_diff"] = {
        "only_in_fixed": int((m["_merge"] == "left_only").sum()),
        "only_in_prefix": int((m["_merge"] == "right_only").sum()),
        "n_shared": int(len(both)),
        "net_noncomm_mismatch_rows": int(
            (both["net_noncomm_fx"] != both["net_noncomm_pf"]).sum()),
        "oi_mismatch_rows": int(
            (both["open_interest_all_fx"] != both["open_interest_all_pf"]).sum())}
    # dossier claims
    fy = res["fixed_tidy"]["by_year"]
    res["dossier_claims_vs_fixed"] = {
        "2021_mean": [fy[2021]["net_noncomm_k_mean"], -33.1],
        "2022_mean": [fy[2022]["net_noncomm_k_mean"], -51.6],
        "2023_mean": [fy[2023]["net_noncomm_k_mean"], -52.4],
        "2024_mean": [fy[2024]["net_noncomm_k_mean"], -38.2],
        "2025_mean": [fy[2025]["net_noncomm_k_mean"], -66.1],
        "2026_mean": [fy[2026]["net_noncomm_k_mean"], 16.0],
        "2026_max": [fy[2026]["net_noncomm_k_max"], 85.6],
        "oi_2020_mean_k": [fy[2020]["oi_k_mean"], 138.0],
        "oi_2026_mean_k": [fy[2026]["oi_k_mean"], 278.0],
        "crowding_2021_2025_range": [
            [fy[y]["crowding_mean"] for y in range(2021, 2026)], "-0.19..-0.36"],
        "series_min": [res["fixed_tidy"]["net_noncomm_k_min"], -107.5],
        "series_min_date": [res["fixed_tidy"]["net_noncomm_k_min_date"], "2024-03-19"],
        "series_max": [res["fixed_tidy"]["net_noncomm_k_max"], 103.4],
        "series_max_date": [res["fixed_tidy"]["net_noncomm_k_max_date"], "2012-12-11"],
        "note": "[recomputed_on_fixed, dossier_claim]"}
    with open(os.path.join(HERE, "recompute_cot.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=str)
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
