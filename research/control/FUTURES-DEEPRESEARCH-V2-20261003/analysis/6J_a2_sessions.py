"""A2 — 6J session/intraday structure 2020-2026 (DEEP-6J).

From the held-contract (PIT volume-crossover k=5 HMUZ chain) 1m bars:
  * volume / range / vol distribution by exchange-clock hour (CT) and by
    center-local windows (Tokyo incl. lunch + fix, London, New York) —
    DST-correct via per-center tz_convert (v1 was RTH-blind: this measures the
    Asia overnight for the first time);
  * where session highs/lows print (window share of extrema minutes);
  * era stability (2020-21 / 2022-23 / 2024-26);
  * close->open and weekend gap anatomy;
  * BoJ MPM decision window (Tokyo afternoon ~02:00-05:00 UTC) liquidity
    context — v1 could not see it at all.
Descriptive only; no PnL, no conditioning.
"""
from __future__ import annotations

import os
import sys

import importlib

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
L = importlib.import_module("6J_deep_lib")

OUT = os.path.join(L.HERE, "6J_a2_sessions.json")
ERAS = [("2020-01-01", "2021-12-31", "era_2020_21"),
        ("2022-01-01", "2023-12-31", "era_2022_23"),
        ("2024-01-01", "2026-10-01", "era_2024_26")]


def era_of(s: pd.Series) -> pd.Series:
    d = pd.to_datetime(s)
    out = pd.Series("none", index=s.index)
    for a, b, name in ERAS:
        out[(d >= pd.Timestamp(a)) & (d <= pd.Timestamp(b))] = name
    return out


def main():
    df = pd.read_parquet(os.path.join(L.CACHE, "6j_annotated_1m.parquet"))
    held = pd.read_parquet(os.path.join(L.CACHE, "held_volume_k5.parquet"))
    hmap = dict(zip(held["session_date"], held["held"]))
    df = df[df["session_date"].map(hmap).notna()].copy()
    df = df[df["contract"] == df["session_date"].map(hmap)]
    df["range_px"] = (df["high"].astype(float) - df["low"].astype(float)) * L.PX_SCALE
    df["mid_px"] = (df["high"].astype(float) + df["low"].astype(float)) / 2 * L.PX_SCALE
    df["ret1m"] = df.groupby("contract")["mid_px"].transform(
        lambda x: np.log(x).diff())
    df["era"] = era_of(df["session_date"].astype(str))
    df["hour_ct"] = df["minute_ct"] // 60

    res = {"schema": "6J_a2_sessions@1",
           "panel": {"bars": int(len(df)),
                     "sessions": int(df["session_date"].nunique()),
                     "held_rule": "PIT volume-crossover k=5 HMUZ",
                     "note": "bars of the held contract only; prices USD/JPY"}}

    def block(sub: pd.DataFrame, tag: str):
        b = {"n_bars": int(len(sub)), "volume_sum": int(sub["volume"].sum())}
        # CT-hour partition (24 buckets; 17..23 = D-1 evening of trade date)
        hv = sub.groupby("hour_ct")["volume"].sum()
        hr = sub.groupby("hour_ct")["range_px"].sum()
        vol_share = (hv / hv.sum())
        b["ct_hour_volume_share"] = {f"{h:02d}": float(vol_share.get(h, 0))
                                     for h in range(24)}
        b["ct_hour_range_share"] = {f"{h:02d}": float(hr.get(h, 0) / hr.sum())
                                    for h in range(24)}
        b["top3_ct_hours_by_volume"] = [
            f"{int(h):02d}" for h in vol_share.sort_values(ascending=False).index[:3]]
        mv = sub.groupby("hour_ct")["volume"].median()
        b["ct_hour_median_1m_volume"] = {f"{int(h):02d}": (float(mv[h]) if h in mv.index else None)
                                         for h in range(24)}
        # center windows (overlap disclosed)
        b["center_windows"] = {}
        for name in L.CENTER_WINDOWS:
            w = sub[sub[f"w_{name}"]]
            if len(w) == 0:
                continue
            b["center_windows"][name] = {
                "volume_share_pct": float(100 * w["volume"].sum() / sub["volume"].sum()),
                "range_share_pct": float(100 * w["range_px"].sum() / sub["range_px"].sum()),
                "median_1m_volume": float(w["volume"].median()),
                "median_1m_range_bp": float(1e4 * (w["range_px"] / w["mid_px"]).median()),
                "var_share_pct": float(100 * w["ret1m"].var() / sub["ret1m"].var())}
        # disjoint CT buckets
        bv = sub.groupby("ct_bucket")["volume"].sum()
        bs = (bv / bv.sum())
        b["ct_bucket_volume_share_pct"] = {k: float(100 * bs.get(k, 0))
                                           for k in ["asia_early_17_21", "tokyo_day_21_02",
                                                     "asia_late_02_07", "ny_am_07_10",
                                                     "ny_lunch_10_12", "ny_pm_12_15",
                                                     "close_15_16", "break_16_17", "outside"]}
        return b

    res["full"] = block(df, "full")
    res["eras"] = {}
    for _a, _b, name in ERAS:
        res["eras"][name] = block(df[df["era"] == name], name)

    # ---- where do session highs/lows print? ----
    d2 = df.sort_values(["session_date", "dt"])
    hi_idx = d2.groupby("session_date")["high"].idxmax()
    lo_idx = d2.groupby("session_date")["low"].idxmin()
    def win_of(rows):
        out = {}
        for name in L.CENTER_WINDOWS:
            out[name] = int(rows[f"w_{name}"].sum())
        out["other"] = int(len(rows)) - sum(int(rows[f"w_{n}"].sum()) for n in L.CENTER_WINDOWS)
        tot = len(rows)
        return {k: float(100 * v / tot) for k, v in out.items()}
    res["session_high_minute_window_pct"] = win_of(d2.loc[hi_idx])
    res["session_low_minute_window_pct"] = win_of(d2.loc[lo_idx])
    res["extrema_note"] = ("first-occurrence argmax/argmin per session; windows "
                           "overlap (London PM overlaps NY AM)")

    # ---- close->open and weekend gaps (held contract) ----
    sess_first = d2.groupby("session_date").first()
    sess_last = d2.groupby("session_date").last()
    sd = pd.to_datetime(sess_last.index)
    prev_last = sess_last["close"].astype(float).shift(1) * L.PX_SCALE
    gap = (sess_first["open"].astype(float) * L.PX_SCALE) / prev_last - 1
    is_mon = sd.dayofweek == 0
    res["gaps"] = {
        "overnight_gap_bp_median": float(1e4 * gap.median()),
        "overnight_gap_bp_p95_abs": float(1e4 * gap.abs().quantile(.95)),
        "weekend_gap_monday_open_bp_median": float(1e4 * gap[is_mon].median()),
        "weekend_gap_monday_open_bp_p95_abs": float(1e4 * gap[is_mon].abs().quantile(.95)),
        "note": "close 16:00 CT -> next session open 17:00 CT (1h halt); weekend = Fri close -> Sun open"}

    # ---- BoJ MPM decision window liquidity (Tokyo afternoon JST) ----
    # decisions announced "in the afternoon JST" on day-2 (~12:00-15:00 JST
    # historically 约为 03:00-06:00 UTC; descriptive window below)
    w = df[df["minute_tokyo"].between(12 * 60, 15 * 60 + 30)]
    res["boj_decision_window"] = {
        "window": "12:00-15:30 JST (Tokyo afternoon; decisions land here)",
        "volume_share_pct_of_session": float(100 * w["volume"].sum() / df["volume"].sum()),
        "median_1m_volume": float(w["volume"].median()),
        "median_1m_volume_full_day": float(df["volume"].median()),
        "bars": int(len(w)),
        "note": "v1 RTH-blind: this window is US overnight (~22:00-01:00 CT)"}

    L.jdump(res, OUT)
    print("A2 complete ->", OUT)


if __name__ == "__main__":
    main()
