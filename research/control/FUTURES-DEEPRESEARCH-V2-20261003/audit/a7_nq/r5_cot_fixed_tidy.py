"""A7 audit R5 — recompute NQ_DEEP_v2 §5 CoT claims on the FIXED tidy.

The dossier's A5 run predates the 2026-10-03 INTEGRATION-FIX-V2 exact-name fix
(uncommitted diff to cftc_normalize.py). Pre-fix, series COT_LEGACY_NQ mixed
three market lines (Consolidated + Micro + Nasdaq Mini) and A5 applied a LOCAL
filter (market_name startswith 'NASDAQ-100 Consolidated'). Post-fix:
  * COT_LEGACY_NQ = the true E-mini line ('NASDAQ-100 STOCK INDEX (MINI)' 840
    rows + renamed 'NASDAQ MINI' 242 rows; 2006-01-03..2026-09-22)
  * the Consolidated line lives on as COT_LEGACY_NQ__ALT__NASDAQ_100_... (850
    rows 2010-06-15..2026-09-22)

This script:
  A) reruns the A5 analysis logic verbatim against the __ALT__ Consolidated
     line (the line the dossier's numbers rest on) — do the dossier numbers
     reproduce?
  B) reruns the A5 loader+filter AS WRITTEN (series COT_LEGACY_NQ, filter
     'NASDAQ-100 Consolidated') against the fixed tidy — does the script still
     work, i.e. is a re-run hazard created by the fix?
  C) recomputes the same bucket table on the CANONICAL E-mini line for
     comparison — would the dossier's conclusions change if restated on the
     canonical line?
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
TIDY = ("/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms"
        "/normalized/cftc_legacy_tidy.parquet")
DAILY = os.path.dirname(os.path.dirname(HERE)) + "/analysis/NQ_cache/nq_held_daily.parquet"
OUT = os.path.join(HERE, "r5_cot_fixed_tidy.json")

cot = pd.read_parquet(TIDY)
nq = cot[cot["series_id"].str.startswith("COT_LEGACY_NQ")].copy()
nq["mn"] = nq["market_name"].str.strip()

ALT = "COT_LEGACY_NQ__ALT__NASDAQ_100_CONSOLIDATED_CHICAGO_MERCANTILE_EXCHANGE"

res = {"schema": "a7_nq_r5_cot_fixed_tidy@1",
       "series_present": sorted(nq["series_id"].unique().tolist())}

# ---------------- A) consolidated line via __ALT__ ----------------
cons = nq[nq["series_id"] == ALT].copy()
cons["obs_date"] = pd.to_datetime(cons["observation_period"])
cons["net_noncomm"] = cons["noncomm_long"] - cons["noncomm_short"]
cons = cons.sort_values("obs_date").reset_index(drop=True)
res["A_consolidated_alt"] = {"n_rows": int(len(cons)),
                             "window": [str(cons.obs_date.min().date()),
                                        str(cons.obs_date.max().date())]}

# ---------------- B) A5 loader as written on fixed tidy ----------------
as_written = nq[nq["series_id"] == "COT_LEGACY_NQ"].copy()
as_written["obs_date"] = pd.to_datetime(as_written["observation_period"])
hit = as_written[as_written["mn"].str.startswith("NASDAQ-100 Consolidated")]
res["B_as_written_on_fixed_tidy"] = {
    "n_rows_COT_LEGACY_NQ": int(len(as_written)),
    "n_rows_after_Consolidated_filter": int(len(hit)),
    "verdict": ("A5's filter now selects ZERO rows -> NQ_a5_cot.py re-run on the "
                "fixed tidy yields an empty frame (silent empty analysis / crash); "
                "the script is NOT idempotent across the tidy fix")}


def bucket_analysis(df: pd.DataFrame, tag: str) -> dict:
    """A5 logic verbatim: strict-past 3y percentile -> fwd 10-session stats."""
    out = {"tag": tag, "n_rows": int(len(df)),
           "window": [str(df.obs_date.min().date()), str(df.obs_date.max().date())]}
    df = df.sort_values("obs_date").reset_index(drop=True)
    s = df.set_index("obs_date")["net_noncomm"].astype(float)
    pct = []
    for i in range(len(s)):
        if i < 156:
            pct.append(None)
            continue
        w = s.iloc[i - 156:i]
        pct.append(float((w < s.iloc[i]).mean()))
    df["pct"] = pct

    daily = pd.read_parquet(DAILY)
    daily["d"] = pd.to_datetime(daily["d"])
    rows = []
    for r in df.itertuples():
        if r.pct is None or pd.isna(r.pct):
            continue
        rel = r.obs_date + pd.Timedelta(days=3)
        fwd = daily[(daily["d"] > rel)
                    & (daily["d"] <= rel + pd.Timedelta(days=35))].head(10)
        if len(fwd) < 8 or fwd["ret"].isna().all():
            continue
        rets = fwd["ret"].dropna()
        cum = fwd["ret"].fillna(0).cumsum()
        rows.append({"obs": r.obs_date, "pct": r.pct,
                     "rvol": float(rets.std() * np.sqrt(252)),
                     "absret": float(rets.abs().sum()),
                     "mdd": float((cum - cum.cummax()).min())})
    fw = pd.DataFrame(rows)
    out["n_forward_obs"] = int(len(fw))

    def bucket(lo, hi):
        b = fw[(fw["pct"] >= lo) & (fw["pct"] < hi)]
        return {"n": int(len(b)),
                "rvol10_median_pct": round(100 * b["rvol"].median(), 2) if len(b) else None,
                "absret10_median_pct": round(100 * b["absret"].median(), 2) if len(b) else None,
                "mdd10_median_pct": round(100 * b["mdd"].median(), 2) if len(b) else None}
    out["buckets"] = {
        "extreme_short_lt10": bucket(0.0, 0.1),
        "low_10_40": bucket(0.1, 0.4),
        "mid_40_60": bucket(0.4, 0.6),
        "high_60_90": bucket(0.6, 0.9),
        "extreme_long_ge90": bucket(0.9, 1.01)}
    # era stability (extreme vs mid fwd rvol)
    fw["year"] = fw["obs"].dt.year
    stab = {}
    for nm, a, b in [("2013_2016", 2013, 2016), ("2017_2020", 2017, 2020),
                     ("2021_2026", 2021, 2026)]:
        w = fw[(fw["year"] >= a) & (fw["year"] <= b)]
        ex = w[(w["pct"] >= 0.9) | (w["pct"] < 0.1)]
        mid = w[(w["pct"] >= 0.4) & (w["pct"] < 0.6)]
        if len(ex) > 5 and len(mid) > 5:
            stab[nm] = {"rvol_extreme_pct": round(100 * ex["rvol"].median(), 2),
                        "rvol_mid_pct": round(100 * mid["rvol"].median(), 2)}
    out["era_stability_extreme_vs_mid"] = stab
    # OI context
    df["year"] = df["obs_date"].dt.year
    out["oi_by_year"] = {
        str(int(y)): {"oi_median": float(g["open_interest_all"].median()),
                      "net_pct_oi_median": float(
                          (g["net_noncomm"] / g["open_interest_all"]).median())}
        for y, g in df.groupby("year")}
    return out


res["A_consolidated_alt"]["analysis"] = bucket_analysis(cons, "consolidated_ALT")

# ---------------- C) canonical e-mini line ----------------
emi = as_written.copy()
emi["net_noncomm"] = emi["noncomm_long"] - emi["noncomm_short"]
emi["obs_date"] = pd.to_datetime(emi["observation_period"])
res["C_canonical_emini"] = bucket_analysis(emi, "canonical_emini")

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
