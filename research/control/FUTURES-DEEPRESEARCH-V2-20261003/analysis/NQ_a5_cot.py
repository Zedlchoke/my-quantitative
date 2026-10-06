"""A5 — NQ positioning: CFTC legacy CoT as-published (DEEP-NQ).

[ERRATUM F2 fix, 2026-10-03, lane DOSSIER-ERRATA-V2 — evidence
audit/a7_nq/A7_DEEP_NQ.md F2/r5.] Uses ONLY the 'NASDAQ-100 Consolidated'
line (850 weekly rows 2010-06-15..2026-09-22). On the FIXED tidy
(INTEGRATION-FIX-V2, 2026-10-03) that line is its own series id
COT_LEGACY_NQ__ALT__NASDAQ_100_CONSOLIDATED_CHICAGO_MERCANTILE_EXCHANGE;
canonical COT_LEGACY_NQ is now the single E-mini line (2006-2026). The
loader pins the __ALT__ id and HARD-FAILS on an unexpected row count —
the pre-fix local startswith() filter silently selected ZERO rows on the
fixed tidy (silent-empty re-run hazard; A7-NQ r5 part B). Numbers on the
Consolidated line are unchanged by the tidy fix (A7-NQ r5 part A: exact
reproduction).

Descriptive only: positioning extremes vs SUBSEQUENT realized vol /
drawdown / |return| distributions. No return-signaling claims, no trade
rules, no PnL. Percentiles are STRICT-PAST (trailing 3y). Alignment is
release-honest: Tuesday position -> forward window starts after the Friday
15:30 ET release.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import NQ_deep_lib as L  # noqa: E402

OUT = os.path.join(L.HERE, "NQ_a5_cot.json")

ALT_ID = "COT_LEGACY_NQ__ALT__NASDAQ_100_CONSOLIDATED_CHICAGO_MERCANTILE_EXCHANGE"
EXPECTED_ROWS = 850          # A7-NQ r5 pinned count on the fixed tidy
EXPECTED_WINDOW = ("2010-06-15", "2026-09-22")


def main():
    cot = L.load_cot_nq_all_lines()
    cons = cot[cot["series_id"] == ALT_ID].copy()
    # hard guard: never run a silent-empty analysis (ERRATUM F2)
    if len(cons) != EXPECTED_ROWS:
        raise SystemExit(
            f"ERRATUM F2 guard: series {ALT_ID!r} yielded {len(cons)} rows, "
            f"expected {EXPECTED_ROWS} (window {EXPECTED_WINDOW}). Refusing "
            "to produce an empty/stale analysis — inspect the tidy "
            "(cftc_legacy_tidy.parquet) before re-running.")
    cons["obs_date"] = pd.to_datetime(cons["observation_period"])
    cons = cons.sort_values("obs_date").reset_index(drop=True)
    res = {"schema": "NQ_a5_cot@1",
           "source": "cftc_legacy_tidy.parquet (fixed 2026-10-03), series "
                     + ALT_ID,
           "line_used": "NASDAQ-100 Consolidated only (__ALT__ series id; "
                        "ERRATUM F2 loader re-point)",
           "n_rows": int(len(cons)),
           "window": [str(cons.obs_date.min().date()),
                      str(cons.obs_date.max().date())],
           "excluded_lines": {
             "micro": int(cot["series_id"].str.contains("MICRO_E_MINI_NASDAQ").sum()),
             "nasdaq_mini": int(
                 cot["series_id"].str.contains("NASDAQ_100_STOCK_INDEX").sum())},
           "vintage": "as_published_no_revision; released Friday 15:30 ET "
                      "(positions as-of Tuesday)"}

    # OI era table
    cons["year"] = cons.obs_date.dt.year
    res["oi_by_year"] = [
        {"year": int(y), "oi_median": float(g["open_interest_all"].median()),
         "net_noncomm_median": float(g["net_noncomm"].median()),
         "net_noncomm_pct_oi": float(
             (g["net_noncomm"] / g["open_interest_all"]).median())}
        for y, g in cons.groupby("year")]

    # held daily series for forward stats
    daily = pd.read_parquet(os.path.join(L.CACHE, "nq_held_daily.parquet"))
    daily["d"] = pd.to_datetime(daily["d"])

    # strict-past 3y percentile of net_noncomm
    s = cons.set_index("obs_date")["net_noncomm"].astype(float)
    pct = []
    for i in range(len(s)):
        if i < 156:
            pct.append(None)
            continue
        w = s.iloc[i - 156:i]  # strictly past
        pct.append(float((w < s.iloc[i]).mean()))
    cons["pct_net_noncomm"] = pct

    # forward stats from the session AFTER release (obs Tue + 3 days = Fri
    # release; forward window starts next session)
    rows = []
    dd_cum = daily["dd"].fillna(0.0)
    for r in cons.itertuples():
        if r.pct_net_noncomm is None or pd.isna(r.pct_net_noncomm):
            continue
        rel = r.obs_date + pd.Timedelta(days=3)  # Friday release
        fwd = daily[(daily["d"] > rel) & (daily["d"] <= rel + pd.Timedelta(days=35))]
        fwd = fwd.head(10)
        if len(fwd) < 8 or fwd["ret"].isna().all():
            continue
        rets = fwd["ret"].dropna()
        rows.append({
            "obs": str(r.obs_date.date()), "pct": r.pct_net_noncomm,
            "fwd_rvol10_ann": float(rets.std() * np.sqrt(252)),
            "fwd_absret10": float(rets.abs().sum()),
            "fwd_maxdd10": float(-fwd["dd"].min() if "dd" in fwd else 0)})
    fw = pd.DataFrame(rows)

    def bucket(lo, hi):
        b = fw[(fw["pct"] >= lo) & (fw["pct"] < hi)]
        return {"n": int(len(b)),
                "rvol10_median": float(b["fwd_rvol10_ann"].median()) if len(b) else None,
                "absret10_median": float(b["fwd_absret10"].median()) if len(b) else None,
                "maxdd10_median": float(b["fwd_maxdd10"].median()) if len(b) else None}
    res["buckets_net_noncomm_pct"] = {
        "extreme_short_lt10": bucket(0.0, 0.1),
        "low_10_40": bucket(0.1, 0.4),
        "mid_40_60": bucket(0.4, 0.6),
        "high_60_90": bucket(0.6, 0.9),
        "extreme_long_ge90": bucket(0.9, 1.01)}
    # fwd_maxdd10 in the frame is from held daily dd (log units, negative) —
    # recompute properly: max drawdown WITHIN the 10-session window
    rows2 = []
    for r in cons.itertuples():
        if r.pct_net_noncomm is None or pd.isna(r.pct_net_noncomm):
            continue
        rel = r.obs_date + pd.Timedelta(days=3)
        fwd = daily[(daily["d"] > rel) & (daily["d"] <= rel + pd.Timedelta(days=35))].head(10)
        if len(fwd) < 8:
            continue
        cum = fwd["ret"].fillna(0).cumsum()
        mdd = float((cum - cum.cummax()).min())  # log units, <= 0
        rows2.append({"obs": str(r.obs_date.date()), "pct": r.pct_net_noncomm,
                      "mdd10": mdd})
    fw2 = pd.DataFrame(rows2)
    res["mdd10_by_bucket"] = {
        f"{lo:.1f}_{hi:.2f}": {"n": int(len(b)),
                               "mdd10_median": float(b["mdd10"].median())}
        for lo, hi, b in [
            (0.0, 0.1, fw2[(fw2["pct"] >= 0.0) & (fw2["pct"] < 0.1)]),
            (0.4, 0.6, fw2[(fw2["pct"] >= 0.4) & (fw2["pct"] < 0.6)]),
            (0.9, 1.01, fw2[(fw2["pct"] >= 0.9)])]}

    # era stability of the extreme-vs-mid vol gap
    fw["year"] = pd.to_datetime(fw["obs"]).dt.year
    eras = [("2013_2016", 2013, 2016), ("2017_2020", 2017, 2020),
            ("2021_2026", 2021, 2026)]
    stab = {}
    for nm, a, b in eras:
        w = fw[(fw["year"] >= a) & (fw["year"] <= b)]
        ex = w[(w["pct"] >= 0.9) | (w["pct"] < 0.1)]
        mid = w[(w["pct"] >= 0.4) & (w["pct"] < 0.6)]
        if len(ex) > 5 and len(mid) > 5:
            stab[nm] = {
                "n_extreme": int(len(ex)), "n_mid": int(len(mid)),
                "rvol_extreme": float(ex["fwd_rvol10_ann"].median()),
                "rvol_mid": float(mid["fwd_rvol10_ann"].median())}
    res["era_stability_rvol_extreme_vs_mid"] = stab

    # extreme-episodes table (top-5 extreme long, short by pct)
    cons2 = cons.dropna(subset=["pct_net_noncomm"])
    top_l = cons2.nlargest(5, "pct_net_noncomm")[["obs_date", "net_noncomm", "pct_net_noncomm"]]
    top_s = cons2.nsmallest(5, "pct_net_noncomm")[["obs_date", "net_noncomm", "pct_net_noncomm"]]
    res["extreme_episodes"] = {
        "extreme_long": [{"obs": str(r.obs_date.date()),
                          "net": int(r.net_noncomm), "pct": float(r.pct_net_noncomm)}
                         for r in top_l.itertuples()],
        "extreme_short": [{"obs": str(r.obs_date.date()),
                           "net": int(r.net_noncomm), "pct": float(r.pct_net_noncomm)}
                          for r in top_s.itertuples()]}

    L.jdump(res, OUT)
    print("A5 complete ->", OUT)


if __name__ == "__main__":
    main()
