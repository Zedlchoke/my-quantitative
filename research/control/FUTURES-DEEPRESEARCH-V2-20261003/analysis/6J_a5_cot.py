"""A5 — CoT JPY (CME Japanese Yen futures, legacy futures-only) 2006-2026 (DEEP-6J).

As-published weekly CoT (Tue as-of, Fri 15:30 ET release, not revised; TFF
classification caveat per v1 note). Descriptive only:
  * full-history positioning regimes by year (net non-commercial contracts,
    net commercial, share of OI);
  * STRICT-PAST extremes: |z| >= 2 vs trailing-150-week own distribution;
  * ex-post anatomy of extreme weeks (subsequent-4w realized vol vs trailing,
    subsequent-20-session max drawdown on the held 6J chain 2020-2026) —
    EX-POST LABELS FOR DESCRIPTION ONLY, never a signal or selection;
  * CoT state at the start of each A1 zigzag leg (2020-2026).
Release-lag disclosure: positions known only as of prior Tuesday, released
Friday — any future strategy use must lag to the release timestamp.
"""
from __future__ import annotations

import os
import sys

import importlib

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
L = importlib.import_module("6J_deep_lib")

OUT = os.path.join(L.HERE, "6J_a5_cot.json")


def main():
    cot = L.load_cot_6j()
    cot = cot.sort_values("obs_date").reset_index(drop=True)
    cot["net_noncomm_pct_oi"] = 100 * cot["net_noncomm"] / cot["open_interest_all"]
    # strict-past z vs trailing 150 weeks (~3y)
    mu = cot["net_noncomm"].rolling(150, min_periods=100).mean().shift(1)
    sd = cot["net_noncomm"].rolling(150, min_periods=100).std().shift(1)
    cot["z_past"] = (cot["net_noncomm"] - mu) / sd

    res = {"schema": "6J_a5_cot@1",
           "source": "CFTC legacy futures-only, JAPANESE YEN - CHICAGO MERCANTILE "
                     "EXCHANGE, as-published (not revised), Tue as-of / Fri 15:30 ET release",
           "panel": {"n_weeks": int(len(cot)),
                     "first": str(cot['obs_date'].min().date()),
                     "last": str(cot['obs_date'].max().date())}}

    yearly = []
    cot["year"] = cot["obs_date"].dt.year
    for y, g in cot.groupby("year"):
        yearly.append({
            "year": int(y), "n": int(len(g)),
            "net_noncomm_median": float(g["net_noncomm"].median()),
            "net_noncomm_min": int(g["net_noncomm"].min()),
            "net_noncomm_max": int(g["net_noncomm"].max()),
            "oi_median": float(g["open_interest_all"].median()),
            "net_noncomm_pct_oi_median": float(g["net_noncomm_pct_oi"].median()),
            "n_weeks_z_ge2": int((g["z_past"] >= 2).sum()),
            "n_weeks_z_le_minus2": int((g["z_past"] <= -2).sum())})
    res["yearly"] = yearly

    # extreme weeks (first week of each |z|>=2 run)
    ext = cot[cot["z_past"].abs() >= 2].copy()
    runs = (ext["obs_date"].diff() > pd.Timedelta(weeks=2)).cumsum()
    firsts = ext.groupby(runs).first()

    # ex-post anatomy for extremes 2020+ (joint with 6J held chain)
    hd = pd.read_parquet(os.path.join(L.CACHE, "6j_held_daily.parquet"))
    hd["d"] = pd.to_datetime(hd["d"])
    hd = hd.set_index("d")
    rows = []
    for _, w in firsts.iterrows():
        # subsequent 4w realized vol (ex-post label, ~20 sessions after release)
        t0 = w["obs_date"] + pd.Timedelta(days=4)  # approx Friday release
        fwd = hd.loc[t0: t0 + pd.Timedelta(days=28), "ret_within"].dropna()
        pre = hd.loc[t0 - pd.Timedelta(days=28): t0, "ret_within"].dropna()
        nxt20 = hd.loc[t0: t0 + pd.Timedelta(days=40), "close"].dropna()
        dd = float((nxt20 / nxt20.cummax() - 1).min()) if len(nxt20) > 5 else None
        rows.append({
            "week": str(w["obs_date"].date()), "z_past": float(w["z_past"]),
            "net_noncomm": int(w["net_noncomm"]),
            "pct_oi": float(w["net_noncomm_pct_oi"]),
            "fwd4w_vol_ann_pct": (float(100 * fwd.std() * np.sqrt(252))
                                  if len(fwd) >= 10 else None),
            "pre4w_vol_ann_pct": (float(100 * pre.std() * np.sqrt(252))
                                  if len(pre) >= 10 else None),
            "next20sess_maxdd_pct": (float(100 * dd) if dd is not None else None)})
    res["extreme_weeks_expost"] = rows
    res["extreme_note"] = ("ex-post labels for description only; fwd vol measured "
                           "from ~release date; NOT a conditional signal table")

    # CoT state at zigzag leg starts (2020-2026)
    a1 = __import__("json").load(open(os.path.join(L.HERE, "6J_a1_regimes.json")))
    legs = []
    for leg in a1["zigzag_down_legs_3pct"]:
        t = pd.Timestamp(leg["from"])
        c = cot[cot["obs_date"] <= t].tail(1)
        if len(c):
            c = c.iloc[0]
            legs.append({"leg_start": leg["from"], "move_pct": leg["move_pct"],
                         "cot_week_asof": str(c["obs_date"].date()),
                         "net_noncomm": int(c["net_noncomm"]),
                         "z_past": (float(c["z_past"]) if pd.notna(c["z_past"]) else None)})
    res["cot_at_downleg_starts"] = legs

    # extremes before the record 2026 intervention window: net noncomm in Apr-Jul 2026
    rec = cot[(cot["obs_date"] >= "2026-03-01") & (cot["obs_date"] <= "2026-08-01")]
    res["net_noncomm_2026_mar_aug"] = [
        {"week": str(r["obs_date"].date()), "net_noncomm": int(r["net_noncomm"]),
         "z_past": (float(r["z_past"]) if pd.notna(r["z_past"]) else None)}
        for _, r in rec.iterrows()]

    L.jdump(res, OUT)
    print("A5 complete ->", OUT)


if __name__ == "__main__":
    main()
