"""A5 — CFTC legacy CoT positioning for EURO FX, 2006-2026 (DEEP-6E).

Descriptive positioning anatomy: net non-commercial positioning history
(2006-2026), strict-past rolling percentile extremes, positioning vs
subsequent realized volatility and drawdowns of the 6E quarterly chain
(2020-2026 overlap only), positioning around the 2022 EUR crisis, and
positioning vs futures OI (2023-10+ overlap). NO conditional mean-return
tables; no ranking/selection. PIT: Tuesday as-of positions released Friday
15:30 ET (>=3-day lag honored by using only released_at-reachable rows for
'forward' descriptives; those descriptives are ex-post labeled descriptive
only).
"""
from __future__ import annotations

import importlib
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
L = importlib.import_module("6E_deep_lib")

OUT = os.path.join(L.HERE, "6E_a5_cot.json")


def main():
    res = {"schema": "6E_a5_cot@1",
           "market_mapping": "COT_LEGACY_6E == 'EURO FX - CHICAGO MERCANTILE "
                             "EXCHANGE' (verified in nonprice normalized data)"}
    cot = L.load_cot_6e()
    res["coverage"] = {
        "n_weeks": int(len(cot)),
        "first": str(cot["obs_date"].min().date()),
        "last": str(cot["obs_date"].max().date()),
        "pit": "observation Tuesday; released Friday 15:30 ET; "
               "as_published_no_revision vintage",
    }
    cot["pct_oi_noncomm"] = cot["net_noncomm"] / cot["open_interest_all"] * 100

    # strict-past rolling 3y percentile of net_noncomm
    win = 156
    roll_min = cot["net_noncomm"].rolling(win, min_periods=104).min()
    roll_max = cot["net_noncomm"].rolling(win, min_periods=104).max()
    cot["pctile_past3y"] = (cot["net_noncomm"] - roll_min) / (roll_max - roll_min) * 100

    # history descriptors
    res["net_noncomm_history"] = {
        "min": float(cot["net_noncomm"].min()),
        "min_date": str(cot.loc[cot["net_noncomm"].idxmin(), "obs_date"].date()),
        "max": float(cot["net_noncomm"].max()),
        "max_date": str(cot.loc[cot["net_noncomm"].idxmax(), "obs_date"].date()),
        "latest": float(cot["net_noncomm"].iloc[-1]),
        "latest_date": str(cot["obs_date"].iloc[-1].date()),
        "pct_oi_noncomm_latest_pct": float(cot["pct_oi_noncomm"].iloc[-1]),
        "pct_oi_noncomm_median_pct": float(cot["pct_oi_noncomm"].median()),
    }
    # era means
    eras = {"2006-2009": ("2006-01-01", "2009-12-31"),
            "2010-2014": ("2010-01-01", "2014-12-31"),
            "2015-2019": ("2015-01-01", "2019-12-31"),
            "2020-2022": ("2020-01-01", "2022-12-31"),
            "2023-2026": ("2023-01-01", "2026-12-31")}
    res["era_means"] = {}
    for name, (a, b) in eras.items():
        m = cot[(cot["obs_date"] >= a) & (cot["obs_date"] <= b)]
        res["era_means"][name] = {
            "n": int(len(m)), "mean_net_noncomm": float(m["net_noncomm"].mean()),
            "min": float(m["net_noncomm"].min()), "max": float(m["net_noncomm"].max()),
            "mean_oi": float(m["open_interest_all"].mean())}

    # 2022 EUR crisis positioning path (quarterly samples)
    c22 = cot[(cot["obs_date"] >= "2022-01-01") & (cot["obs_date"] <= "2022-12-31")]
    res["crisis_2022_path"] = [
        {"date": str(r.obs_date.date()), "net_noncomm": float(r.net_noncomm),
         "oi": float(r.open_interest_all)}
        for r in c22.itertuples()][::4]  # every 4th week to keep JSON small
    res["crisis_2022_summary"] = {
        "start_net": float(c22["net_noncomm"].iloc[0]),
        "min_net": float(c22["net_noncomm"].min()),
        "min_net_date": str(c22.loc[c22["net_noncomm"].idxmin(), "obs_date"].date()),
        "end_net": float(c22["net_noncomm"].iloc[-1]),
        "oi_start": float(c22["open_interest_all"].iloc[0]),
        "oi_max": float(c22["open_interest_all"].max()),
    }

    # ---- positioning vs subsequent realized vol (2020-2026 overlap) ----
    # chain daily realized vol (21d forward, ex-post label, descriptive only)
    sess = pd.read_parquet(os.path.join(L.CACHE, "6e_sessions.parquet"))
    held = pd.read_parquet(os.path.join(L.CACHE, "held_calendar.parquet"))
    closes = sess.pivot_table(index="session_date", columns="contract", values="close")
    closes.index = closes.index.astype(str)  # date objects -> ISO strings
    daily = held.copy()
    daily["session_date"] = daily["session_date"].astype(str)
    daily["close"] = [closes.at[d, c] if (d in closes.index and c in closes.columns
                                          and pd.notna(closes.at[d, c])) else np.nan
                      for d, c in zip(daily["session_date"], daily["held"])]
    daily.index = pd.to_datetime(daily["session_date"])
    daily = daily.sort_index()
    px = closes.stack().rename("close").reset_index()
    px["session_date"] = px["session_date"].astype(str)
    px["prev_close"] = px.groupby("contract")["close"].shift(1)
    lut = px.set_index(["session_date", "contract"])["prev_close"]
    daily["prev_close"] = [lut.get((d, c), np.nan)
                           for d, c in zip(daily["session_date"], daily["held"])]
    daily["ret"] = daily["close"] / daily["prev_close"] - 1
    fwd_vol = daily["ret"].rolling(21).std().shift(-21) * np.sqrt(252) * 100

    # join CoT (use release-Friday-effective availability: obs Tuesday, so a
    # forward window starting at obs_date+3 sessions is fully release-safe;
    # descriptive ex-post anyway)
    cot2 = cot.dropna(subset=["pctile_past3y"]).copy()
    rows = []
    for r in cot2.itertuples():
        if not (pd.Timestamp("2020-01-01") <= r.obs_date <= pd.Timestamp("2026-09-01")):
            continue
        # forward vol from the release-safe point (obs + 3 sessions)
        start = daily.index.asof(r.obs_date + pd.Timedelta(days=3))
        if start is None or pd.isna(fwd_vol.get(start)):
            continue
        rows.append({"date": str(r.obs_date.date()),
                     "pctile": float(r.pctile_past3y),
                     "net": float(r.net_noncomm),
                     "fwd21_ann_vol_pct": float(fwd_vol.loc[start])})
    j = pd.DataFrame(rows)
    hi = j[j["pctile"] >= 80]
    lo = j[j["pctile"] <= 20]
    mid = j[(j["pctile"] > 20) & (j["pctile"] < 80)]
    res["positioning_vs_fwd_vol_descriptive"] = {
        "n_joined": int(len(j)),
        "n_pctile_ge80": int(len(hi)), "n_pctile_le20": int(len(lo)),
        "fwd21_vol_mean_pct_when_ge80": float(hi["fwd21_ann_vol_pct"].mean()) if len(hi) else None,
        "fwd21_vol_mean_pct_when_le20": float(lo["fwd21_ann_vol_pct"].mean()) if len(lo) else None,
        "fwd21_vol_mean_pct_mid": float(mid["fwd21_ann_vol_pct"].mean()) if len(mid) else None,
        "fwd21_vol_median_pct_when_ge80": float(hi["fwd21_ann_vol_pct"].median()) if len(hi) else None,
        "fwd21_vol_median_pct_when_le20": float(lo["fwd21_ann_vol_pct"].median()) if len(lo) else None,
        "caveat": "ex-post labels, descriptive only; percentiles strict-past "
                  "3y rolling; fwd vol starts at release-safe obs+3 sessions; "
                  "NOT a conditional mean-return table (vol/risk anatomy, "
                  "not signal ranking)",
    }
    # extreme-positioning dates list (for dossier narrative)
    ext = j[(j["pctile"] >= 90) | (j["pctile"] <= 10)]
    res["extreme_positioning_dates_2020_2026"] = ext.to_dict(orient="records")

    # ---- CoT OI vs venue OI (2023-10+) sanity ----
    stats = L.load_statistics_6e()
    oi = stats[stats["stat_type"] == 9].copy()
    oi["date"] = pd.to_datetime(oi["ref_date"])
    cot3 = cot[(cot["obs_date"] >= "2023-10-01")].copy()
    pairs = []
    for r in cot3.itertuples():
        d = oi[oi["date"] == r.obs_date]
        if len(d):
            tot = d["quantity"].sum()
            pairs.append({"date": str(r.obs_date.date()),
                          "cot_oi": float(r.open_interest_all),
                          "venue_oi_sum_all_outrights": float(tot)})
    pv = pd.DataFrame(pairs)
    if len(pv):
        pv["ratio"] = pv["venue_oi_sum_all_outrights"] / pv["cot_oi"]
        res["cot_oi_vs_venue_oi"] = {
            "n_overlap_weeks": int(len(pv)),
            "median_ratio": float(pv["ratio"].median()),
            "p05_ratio": float(pv["ratio"].quantile(.05)),
            "p95_ratio": float(pv["ratio"].quantile(.95)),
            "note": "venue OI summed over ALL listed 6E outrights incl "
                    "deferred quarterlies/serials; CoT OI is the legacy "
                    "futures-only aggregate for the EURO FX market",
        }
    L.jdump(res, OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
