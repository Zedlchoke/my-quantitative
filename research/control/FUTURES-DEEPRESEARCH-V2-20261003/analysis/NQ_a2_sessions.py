"""A2 — NQ session/intraday structure 2010-2026 (DEEP-NQ).

Held-contract (PIT volume-crossover k=5) 1m bars. DST-correct via
America/Chicago. Segment = clock-based, era-aware (close 16:15 CT through
2015-09-18, 16:00 CT from 2015-09-21, both measured). Clean sessions only
(held RTH coverage >= 0.6) for structure claims; excluded sessions counted.
FIX/FAST->MDP3 vendor-side convention caveat pre-2017 applies to levels.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import NQ_deep_lib as L  # noqa: E402

OUT = os.path.join(L.HERE, "NQ_a2_sessions.json")

ERAS = [
    ("2010-06_2012-12", "2010-06-07", "2012-12-31"),
    ("2013-01_2016-09", "2013-01-01", "2016-09-30"),
    ("2017-01_2020-02", "2017-01-01", "2020-02-21"),
    ("2020-06_2022-12", "2020-06-01", "2022-12-30"),
    ("2023-01_2026-09", "2023-01-01", "2026-10-01"),
]

SEG_LIST = [s[0] for s in L.SEGMENTS]
OVN = ["ovn_evening", "ovn_overnight", "ovn_preopen"]


def main():
    sess = pd.read_parquet(os.path.join(L.CACHE, "nq_sessions.parquet"))
    held = pd.read_parquet(os.path.join(L.CACHE, "held_volume_k5.parquet"))
    hs = sess.merge(held.rename(columns={"held": "contract"}),
                    on=["session_date", "contract"], how="inner")
    hs["d"] = pd.to_datetime(hs["session_date"])
    hs["clean"] = hs["rth_coverage"].fillna(0) >= 0.6
    res = {"schema": "NQ_a2_sessions@1",
           "held_sessions": int(len(hs)),
           "clean_sessions": int(hs["clean"].sum()),
           "excluded_low_coverage": int((~hs["clean"]).sum()),
           "note_exclusions": "vendor hole 2020-03-23..2020-05-29 (front "
                              "contracts absent) + partial 2020-03-16..20"}

    # ---- segment volume shares by era (clean sessions) ----
    era_out = {}
    for name, a, b in ERAS:
        w = hs[(hs["d"] >= a) & (hs["d"] <= b) & hs["clean"]]
        if not len(w):
            continue
        segs = {}
        tot = sum(w[f"vol_{s}"] for s in SEG_LIST)
        for s in SEG_LIST:
            share = w[f"vol_{s}"] / tot
            segs[s] = {"vol_share_mean": float(share.mean()),
                       "vol_share_median": float(share.median()),
                       "rng_median_pts": float(
                           w[f"rng_{s}"].median() / 1e9)}
        # normalized range share (segment range / session true_range)
        rsum = {}
        era_out[name] = {
            "n_sessions": int(len(w)),
            "segments": segs,
            "ovn_share_mean": float(sum(segs[s]["vol_share_mean"] for s in OVN)),
            "rth_core_share_mean": float(
                segs["rth_open30"]["vol_share_mean"]
                + segs["rth_morning"]["vol_share_mean"]
                + segs["rth_lunch"]["vol_share_mean"]
                + segs["rth_afternoon"]["vol_share_mean"]),
            "open30_plus_morning90": float(
                segs["rth_open30"]["vol_share_mean"]
                + segs["rth_morning"]["vol_share_mean"]),
            "avg_session_volume": float(w["volume"].mean()),
        }
    res["era_segments"] = era_out

    # ---- year-level overnight share (structural shift series) ----
    ys = []
    for y, g in hs[hs["clean"]].groupby(hs["d"].dt.year):
        tot = sum(g[f"vol_{s}"] for s in SEG_LIST)
        ovn = sum(g[f"vol_{s}"] for s in OVN)
        opn = g["vol_rth_open30"] / tot
        ys.append({"year": int(y), "ovn_share": float((ovn / tot).mean()),
                   "open30_share": float(opn.mean()),
                   "avg_vol": float(g["volume"].mean())})
    res["yearly_overnight_share"] = ys

    # ---- minute-of-day profile by era (volume share + |1m ret|) ----
    df = L.load_annotated_1m()
    heldsess = held.rename(columns={"held": "contract"})
    dfh = df.merge(heldsess, on=["contract", "session_date"], how="inner")
    del df
    # need minute_of_day: recompute local
    loc = dfh["dt"].dt.tz_convert(L.CHI)
    dfh["minute_of_day"] = loc.dt.hour * 60 + loc.dt.minute
    dfh["d"] = pd.to_datetime(dfh["session_date"])
    # 1m log-|ret| within contract: close-to-close consecutive minutes
    dfh = dfh.sort_values(["contract", "dt"]).reset_index(drop=True)
    dfh["r1"] = (dfh.groupby("contract")["close"].transform(
        lambda s: np.log(s.astype(float)).diff())).abs()
    dfh["same_min_run"] = dfh["contract"].ne(dfh["contract"].shift())
    dfh.loc[dfh["same_min_run"], "r1"] = np.nan  # first bar of each contract
    prof = {}
    for name, a, b in ERAS:
        w = dfh[(dfh["d"] >= a) & (dfh["d"] <= b)]
        if not len(w):
            continue
        sv = w.groupby("minute_of_day")["volume"].sum()
        sv = sv / sv.sum()
        sr = w.groupby("minute_of_day")["r1"].mean()
        prof[name] = {"vol_share_by_minute": {int(k): float(v)
                                              for k, v in sv.items()},
                      "absret_by_minute": {int(k): float(v)
                                           for k, v in sr.items()}}
    res["minute_profiles"] = prof

    # ---- RTH hourly U-shape (compact): 08:30-09:00, 09-10, ..., 15-16 CT ----
    hours = [(8*60+30, 9*60), (9*60, 10*60), (10*60, 11*60), (11*60, 12*60),
             (12*60, 13*60), (13*60, 14*60), (14*60, 15*60), (15*60, 16*60)]
    u = {}
    for name, a, b in ERAS:
        w = dfh[(dfh["d"] >= a) & (dfh["d"] <= b)]
        if not len(w):
            continue
        row = {}
        for h0, h1 in hours:
            m = w[(w["minute_of_day"] >= h0) & (w["minute_of_day"] < h1)]
            row[f"{h0//60:02d}{h0%60:02d}-{h1//60:02d}{h1%60:02d}"] = {
                "vol_share": float(m["volume"].sum() / w["volume"].sum()),
                "absret_mean": float(m["r1"].mean())}
        u[name] = row
    res["rth_hourly"] = u

    # ---- holiday-shorted sessions (inferred from bar coverage) ----
    # short = clean coverage but last trade minute >= 60 min before era close
    def close_min(d):
        return 16*60+15 if pd.Timestamp(d) < L.SESSION_SWITCH_DATE else 16*60
    hs["close_min"] = hs["d"].map(close_min)
    # holiday shorts: detect on sessions with real trading (coverage>0.3)
    # but last trade >=45min before the era's scheduled close; excludes the
    # Friday-early-close era below
    shorts = hs[(hs["rth_coverage"].fillna(0) > 0.3)
                & (hs["last_min"] < hs["close_min"] - 45)].copy()
    # split: era-A recurring FRIDAY early close (15:15 CT; 2010-06..2012-11,
    # measured; ended Nov/Dec 2012) vs other (holiday/expiry) shorts
    fri_era = (shorts["d"].dt.dayofweek == 4) & (shorts["d"] < "2012-12-01") \
        & (shorts["last_min"] < 930)
    res["friday_early_close_eraA"] = {
        "n_sessions": int(fri_era.sum()),
        "window": "2010-06-07..2012-11 (last full month Oct-2012; mixed "
                  "Nov-2012; none from Dec-2012) — measured, not asserted",
        "close_minute_ct": "15:15 CT (last trades 15:14)",
        "mon_thu_close_ct": "16:15 CT in the same era"}
    shorts = shorts[~fri_era]
    short_list = [{"date": str(r.session_date), "last_min": int(r.last_min),
                   "close_min": int(r.close_min)}
                  for r in shorts.itertuples()]
    res["holiday_short_sessions"] = {
        "n": len(short_list), "method": "last trade minute >=45min before the "
        "era's close, coverage otherwise clean (inferred, not exchange-asserted)",
        "dates": short_list}
    # stats: volume on short days vs same-year normal
    sv_norm = []
    for r in shorts.itertuples():
        yr = r.d.year
        peers = hs[hs["clean"] & (hs["d"].dt.year == yr)
                   & (hs["last_min"] >= hs["close_min"] - 45)]
        sv_norm.append(float(r.volume / peers["volume"].median()))
    res["holiday_short_sessions"]["volume_vs_year_median"] = {
        "median": float(np.median(sv_norm)) if sv_norm else None,
        "n": len(sv_norm)}

    L.jdump(res, OUT)
    print("A2 complete ->", OUT)


if __name__ == "__main__":
    main()
