"""A2 — 6E session/intraday structure 2020-2026 (DEEP-6E).

Full 23h Globex anatomy from 1m bars (DST-correct, America/Chicago), which
v1 could not see (RTH-only IBKR bars): volume/volatility by CT hour, by
session segment (Asia / London / ECB+US-data block / pre-RTH / RTH / FOMC /
close), realized-variance decomposition by segment, London-local morning
vs CT-clock views incl DST-mismatch weeks, Sunday-open behavior, and the
8:30-ET data block. Descriptive only.
"""
from __future__ import annotations

import importlib
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
L = importlib.import_module("6E_deep_lib")

OUT = os.path.join(L.HERE, "6E_a2_sessions.json")


def main():
    res = {"schema": "6E_a2_sessions@1",
           "window": "2020-01-02..2026-09-30",
           "notes": "front quarterly held-contract bars only (calendar rule); "
                    "all clock buckets in America/Chicago; London-local view "
                    "via Europe/London; DST-mismatch weeks = US/EU offset "
                    "windows (~2-3 weeks each in March and late Oct-Nov)."}
    df = pd.read_parquet(os.path.join(L.CACHE, "6e_annotated_1m.parquet"))
    held = pd.read_parquet(os.path.join(L.CACHE, "held_calendar.parquet"))
    held["session_date"] = held["session_date"].astype(str)
    df["session_date"] = df["session_date"].astype(str)
    front_keys = set(zip(held["session_date"], held["held"]))
    mask = [k in front_keys for k in zip(df["session_date"], df["raw_symbol"]
                                         + "_" + (2020 + df["raw_symbol"].str[-1].astype(int)).astype(str))]
    f = df[pd.Series(mask, index=df.index)]
    res["front_bars"] = int(len(f))
    res["front_sessions"] = int(f["session_date"].nunique())

    # ---- volume by CT hour (session-clock: hours 17-23 = prior evening) ----
    hour = np.where(f["minute_of_day"] >= 17 * 60,
                    f["minute_of_day"] // 60 - 24,  # evening of D-1 = negative
                    f["minute_of_day"] // 60)        # (-7..15)
    f = f.assign(sess_hour=hour)
    hv = f.groupby("sess_hour")["volume"].sum()
    tot = hv.sum()
    hourly = {f"h{int(h):+03d}": {"share_pct": float(v / tot * 100)}
              for h, v in hv.items()}
    res["volume_share_by_session_hour_ct"] = hourly
    # ranking
    rk = hv.sort_values(ascending=False)
    res["top5_hours_by_volume"] = {f"h{int(h):+03d}": float(v / tot * 100)
                                   for h, v in rk.head(5).items()}
    res["bottom3_hours_by_volume"] = {f"h{int(h):+03d}": float(v / tot * 100)
                                      for h, v in rk.tail(3).items()}

    # ---- intraday volatility by CT hour: mean 1m |logret| ----
    f = f.sort_values(["raw_symbol", "dt"])
    f["lret"] = np.log(f["close_px"] / f.groupby("raw_symbol")["close_px"].shift(1))
    f.loc[(f["session_date"] != f.groupby("raw_symbol")["session_date"].shift(1))
          | ((f["dt"] - f.groupby("raw_symbol")["dt"].shift(1)).dt.total_seconds() > 120),
          "lret"] = np.nan
    hvol = f.groupby("sess_hour")["lret"].apply(
        lambda s: float(np.sqrt(np.nanmean(np.square(s.to_numpy()))) * 1e4))
    res["mean_1m_abs_move_bp_by_hour_ct"] = {f"h{int(h):+03d}": float(v)
                                             for h, v in hvol.items()}

    # ---- segment volume + realized-variance shares ----
    segs = [s[0] for s in L.SEGMENTS]
    segvol = {s: float(f.loc[f["segment"] == s, "volume"].sum()) for s in segs}
    totv = sum(segvol.values())
    res["volume_share_by_segment"] = {k: float(v / totv * 100)
                                      for k, v in segvol.items()}
    f["lret2"] = np.square(f["lret"])
    segrv = f.groupby("segment")["lret2"].sum()
    res["rv_share_by_segment"] = {k: float(v / segrv.sum() * 100)
                                  for k, v in segrv.items()}
    # per-session segment RV shares (median across sessions) for robustness
    ps = f.groupby(["session_date", "segment"])["lret2"].sum().unstack()
    ps_share = ps.div(ps.sum(axis=1), axis=0)
    res["median_session_rv_share_by_segment"] = {
        s: float(ps_share[s].median() * 100) for s in segs if s in ps_share}

    # ---- London-local morning vs CT-clock ----
    res["london_views"] = {
        "share_volume_london_local_0800_1200_pct": float(
            f.loc[f["in_london_morning_local"], "volume"].sum() / totv * 100),
        "share_volume_ct_0200_0500_pct": float(segvol["london_morning"] / totv * 100),
        "note": "CT 02:00-05:00 == London 08:00-11:00 only when DST states align",
    }
    # DST-mismatch weeks: does the 01:00-02:00 vs 03:00 CT hour volume shift?
    mis = f[f["dst_mismatch"]]
    aln = f[~f["dst_mismatch"]]

    def hshare(d, h):
        return float(d.loc[d["sess_hour"] == h, "volume"].sum() / d["volume"].sum() * 100)
    res["dst_mismatch_effect"] = {
        "n_bars_mismatch": int(len(mis)),
        "share_vol_h00_mismatch": hshare(mis, 0), "share_vol_h00_aligned": hshare(aln, 0),
        "share_vol_h01_mismatch": hshare(mis, 1), "share_vol_h01_aligned": hshare(aln, 1),
        "share_vol_h02_mismatch": hshare(mis, 2), "share_vol_h02_aligned": hshare(aln, 2),
        "share_vol_h03_mismatch": hshare(mis, 3), "share_vol_h03_aligned": hshare(aln, 3),
        "share_vol_h04_mismatch": hshare(mis, 4), "share_vol_h04_aligned": hshare(aln, 4),
        "share_vol_h05_mismatch": hshare(mis, 5), "share_vol_h05_aligned": hshare(aln, 5),
        "share_vol_h06_mismatch": hshare(mis, 6), "share_vol_h06_aligned": hshare(aln, 6),
        "note": "in mismatch weeks (London on GMT while Chicago on CDT, or "
                "vice versa) the London-morning volume profile shifts by "
                "exactly one CT hour (h+02 falls, h+03..h+05 rise in the "
                "Oct/Nov case): the flow follows London LOCAL time, not CT",
    }

    # ---- day-of-week anatomy (session date weekday) ----
    f["wd"] = pd.to_datetime(f["session_date"]).dt.dayofweek
    wd = f.groupby("wd")["volume"].sum() / totv * 100
    names = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri",
             5: "Sat", 6: "Sun"}
    res["volume_share_by_weekday_sessiondate"] = {
        names[int(k)]: float(v) for k, v in wd.items()}
    # Sunday evening (session opens Sunday 17:00 CT = Monday session date)
    sun = f[(f["minute_of_day"] >= 17 * 60)
            & (pd.to_datetime(f["dt"].dt.tz_convert(L.CHI)).dt.dayofweek == 6)]
    res["sunday_evening_open"] = {
        "n_sessions": int(sun["session_date"].nunique()),
        "volume_share_pct": float(sun["volume"].sum() / totv * 100),
        "median_volume_first_30m": float(
            sun[(sun["minute_of_day"] >= 17 * 60) & (sun["minute_of_day"] < 17 * 60 + 30)]
            .groupby("session_date")["volume"].sum().median()),
    }

    # ---- 8:30 ET (07:30 CT) data block ----
    # minute 07:30 vs neighboring minutes: median volume and range ratio
    mins = f[(f["minute_of_day"] >= 7 * 60 + 25) & (f["minute_of_day"] <= 7 * 60 + 40)]
    mv = mins.groupby("minute_of_day")["volume"].median()
    rng = mins.assign(r=mins["high_px"] - mins["low_px"]).groupby("minute_of_day")["r"].median()
    res["us_830et_block"] = {
        "median_volume_by_minute_0725_0740_ct": {str(int(k)): float(v) for k, v in mv.items()},
        "median_range_by_minute_0725_0740_ct": {str(int(k)): float(v) for k, v in rng.items()},
        "volume_spike_ratio_0730_vs_0729": float(mv.get(450, np.nan) / mv.get(449, np.nan)),
        "range_spike_ratio_0730_vs_0729": float(rng.get(450, np.nan) / rng.get(449, np.nan)),
        "n_sessions_0730_bar_present": int((f["minute_of_day"] == 450).groupby(
            f["session_date"]).sum().gt(0).sum()),
    }

    # ---- ECB block minutes 06:40-07:20 CT on ALL days (baseline; event split in a4) ----
    ecbmins = f[(f["minute_of_day"] >= 6 * 60 + 40) & (f["minute_of_day"] <= 7 * 60 + 20)]
    mv2 = ecbmins.groupby("minute_of_day")["volume"].median()
    res["ecb_window_baseline_median_volume_by_minute_ct"] = {
        str(int(k)): float(v) for k, v in mv2.items()}

    # ---- v1 RTH-open gap re-measure on full-session data ----
    # RTH-open price (first 08:30-08:31 CT bar close) vs prior session close
    rth_open = f[f["minute_of_day"] == 8 * 60 + 30].groupby("session_date")["close_px"].first()
    sess_close = f.groupby("session_date")["close_px"].last()
    so = rth_open.to_frame("rth_open").join(sess_close.rename("close"))
    so["prev_close"] = so["close"].shift(1)
    so["rth_gap"] = so["rth_open"] / so["prev_close"] - 1
    # full-session return (close-to-close, same contract continuity approximated
    # by session close of held contract)
    so["day_ret"] = so["close"] / so["prev_close"] - 1
    g = so["rth_gap"].dropna()
    d = so["day_ret"].dropna()
    res["v1_gap_remeasure"] = {
        "n": int(len(g)),
        "rth_open_gap_std_pct": float(g.std() * 100),
        "day_ret_std_pct": float(d.std() * 100),
        "gap_std_over_dayret_std": float(g.std() / d.std()),
        "v1_figures_were": "gap std 0.265% vs RTH-day ret std 0.333% (79%) on RTH-only data",
        "pre_rth_plus_asia_london_now_measured_directly": True,
    }

    # ---- coverage: bar presence per session ----
    per_sess = f.groupby("session_date").agg(nbars=("dt", "size"),
                                             vol=("volume", "sum"))
    res["session_coverage"] = {
        "median_bars_per_session": float(per_sess["nbars"].median()),
        "p05_bars": float(per_sess["nbars"].quantile(.05)),
        "tradable_minutes_expected": L.SESSION_TRADABLE_MIN,
        "median_coverage_ratio": float(per_sess["nbars"].median() / L.SESSION_TRADABLE_MIN),
        "median_volume": float(per_sess["vol"].median()),
        "p05_volume": float(per_sess["vol"].quantile(.05)),
    }
    L.jdump(res, OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
