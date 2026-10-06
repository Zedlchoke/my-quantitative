#!/usr/bin/env python
"""A2 — session / intraday structure 2020-2026 for 6A — lane DEEP-6A.

Descriptive ONLY. This analysis fixes v1's RTH-blindness: the vendor panel
covers the FULL Globex session, so the Asia-Pacific hours, Sydney open and
China-data windows are now measurable in 1m bars.

Blocks (all OBSERVED, script + window stated):
  1. volume share by exchange-clock (CT) hour and by CT segment, front
     quarterly contract, per era — DST-correct via tz_convert;
  2. hub-local windows (overlapping by design):
       Sydney day 07:00-17:00 Australia/Sydney (home session; RBA 14:30 and
         ABS 11:30 announcements inside);
       Tokyo 09:00-15:00 Asia/Tokyo;
       Shanghai data window 09:30-10:00 Asia/Shanghai (NBS 09:30, Caixin 09:45);
       London 08:00-16:30 Europe/London;
       US data block 07:00-08:30 CT; US RTH core 08:30-15:00 CT;
     volume share + mean per-minute range (ticks) + volume-active-minute share
     per window, per era;
  3. Sydney-open minute anatomy: volume/range in the 09:50-10:10 Sydney window
     (Sydney FX market open ~09:50 local for banks) and around RBA 14:30
     Sydney minute ±15/±60 minutes on ALL sessions (non-event baseline; the
     event-day split itself is A4);
  4. intraday volatility U-shurve: mean |1m return| by CT hour (front, eras);
  5. weekday structure: session volume by day-of-week;
  6. v1 reconciliation: RTH share of volume vs IBKR RTH-only daily volumes.

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python 6A_a2_sessions.py
Writes: 6A_a2_sessions.json
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

OUT = os.path.join(_HERE, "6A_a2_sessions.json")

ERA_BOUNDS = [("2020-2021", "2020-01-01", "2021-12-31"),
              ("2022-2023", "2022-01-01", "2023-12-31"),
              ("2024-2026-09", "2024-01-01", "2026-10-01")]

# hub windows in hub-local minutes [a, b)
HUB_WINDOWS = {
    "sydney_day_0700_1700": ("syd_min", 7 * 60, 17 * 60),
    "sydney_rba_window_1400_1530": ("syd_min", 14 * 60, 15 * 60 + 30),
    "abs_release_1100_1200_syd": ("syd_min", 11 * 60, 12 * 60),
    "tokyo_0900_1500": ("tyo_min", 9 * 60, 15 * 60),
    "shanghai_data_0930_1000": ("sha_min", 9 * 60 + 30, 10 * 60),
    "london_0800_1630": ("lon_min", 8 * 60, 16 * 60 + 30),
    "us_data_0700_0830_CT": ("ct_minute", 7 * 60, 8 * 60 + 30),
    "rth_core_0830_1500_CT": ("ct_minute", 8 * 60 + 30, 15 * 60),
    "settle_tail_1500_1600_CT": ("ct_minute", 15 * 60, 16 * 60),
    "evening_open_1700_2000_CT": ("ct_minute", 17 * 60, 20 * 60),
    "overnight_0000_0600_CT": ("ct_minute", 0, 6 * 60),
}


def front_sessions(sess: pd.DataFrame) -> pd.DataFrame:
    """Held-contract (quarterly chain) session rows."""
    ch = L.calendar_chain(sess, quarterly_only=True)
    ch["session_date"] = pd.to_datetime(ch["session_date"])
    s = sess.copy()
    s["session_date"] = pd.to_datetime(s["session_date"])
    m = ch.merge(s, left_on=["session_date", "held"],
                 right_on=["session_date", "contract"], how="left")
    return m.dropna(subset=["close_px"]).sort_values("session_date")


def main():
    sess = pd.read_parquet(f"{L.CACHE}/session_contract.parquet")
    sess = sess[~sess["contract"].str.startswith("STRAY")]
    front = front_sessions(sess)
    bars = pd.read_parquet(f"{L.CACHE}/outright_1m.parquet",
                           columns=["dt", "contract", "session_date", "ct_minute",
                                    "segment", "syd_min", "tyo_min", "sha_min",
                                    "lon_min", "open", "high", "low", "close",
                                    "volume", "era"])
    bars["session_date"] = pd.to_datetime(bars["session_date"])
    held_pairs = set(zip(front["session_date"], front["held"]))
    mask = [(d, c) in held_pairs
            for d, c in zip(bars["session_date"], bars["contract"])]
    fb = bars[pd.Series(mask, index=bars.index)]
    fb = fb.assign(ret1=(fb["close"] / fb["close"].shift(1) - 1),
                   range_t=(fb["high"] - fb["low"]) / L.TICK)
    # drop cross-contract 1m returns
    fb.loc[fb["contract"] != fb["contract"].shift(1), "ret1"] = np.nan

    out = {"meta": {
        "lane": "DEEP-6A", "analysis": "A2 sessions/intraday",
        "window": [str(front["session_date"].min().date()),
                   str(front["session_date"].max().date())],
        "front": "held quarterly chain (declared calendar rule, quarterly adaptation)",
        "laws": "descriptive only; no mean-return conditioning; DST-correct hub clocks via zoneinfo",
    }}

    # ---- 1. volume by CT hour per era ---------------------------------------
    byhour = {}
    for name, a, b in ERA_BOUNDS:
        e = fb[(fb["session_date"] >= a) & (fb["session_date"] <= b)]
        hv = e.groupby(e["ct_minute"] // 60)["volume"].sum()
        tot = hv.sum()
        byhour[name] = {int(h): {"share_pct": float(v / tot * 100)}
                        for h, v in hv.items()}
    out["volume_share_by_ct_hour"] = byhour

    # segment shares (pure partition)
    seg = {}
    for name, a, b in ERA_BOUNDS:
        e = fb[(fb["session_date"] >= a) & (fb["session_date"] <= b)]
        sv = e.groupby("segment")["volume"].sum()
        seg[name] = {k: float(v / sv.sum() * 100) for k, v in sv.items()}
    out["volume_share_by_ct_segment"] = seg

    # ---- 2. hub windows ------------------------------------------------------
    hub = {}
    for name, a, b in ERA_BOUNDS:
        e = fb[(fb["session_date"] >= a) & (fb["session_date"] <= b)]
        totvol = float(e["volume"].sum())
        row = {"total_volume": totvol, "n_minutes": int(len(e))}
        for wname, (col, lo, hi) in HUB_WINDOWS.items():
            w = e[(e[col] >= lo) & (e[col] < hi)]
            row[wname] = {
                "volume_share_pct": float(w["volume"].sum() / totvol * 100),
                "mean_range_ticks": float(w["range_t"].mean()) if len(w) else None,
                "share_minutes_with_volume": float((w["volume"] > 0).mean()) if len(w) else None,
                "mean_abs_1m_ret_bp": float(w["ret1"].abs().mean() * 1e4) if len(w) else None,
            }
        hub[name] = row
    out["hub_windows"] = hub
    out["hub_windows_note"] = (
        "windows OVERLAP in real time by design (hubs overlap); volume shares do "
        "not sum to 100%; Sydney day 07:00-17:00 local is the 6A home session "
        "containing RBA 14:30 and ABS 11:30 releases; shanghai_data covers NBS "
        "09:30 and Caixin 09:45 local data releases")

    # ---- 3. minute-of-Sydney-morning profile ---------------------------------
    prof = {}
    for name, a, b in ERA_BOUNDS:
        e = fb[(fb["session_date"] >= a) & (fb["session_date"] <= b)]
        g = e.groupby(e["syd_min"] // 30 * 30)["volume"].sum()
        tot = g.sum()
        prof[name] = {f"{int(k)//60:02d}:{int(k)%60:02d}":
                      float(v / tot * 100) for k, v in g.items()}
    out["volume_by_syd_halfhour"] = prof

    # RBA window minute profile (14:00-15:30 Sydney) — baseline ALL days
    rba_prof = {}
    for name, a, b in ERA_BOUNDS:
        e = fb[(fb["session_date"] >= a) & (fb["session_date"] <= b)]
        w = e[(e["syd_min"] >= 14 * 60) & (e["syd_min"] < 15 * 60 + 30)]
        g = w.groupby(w["syd_min"] - 14 * 60).agg(
            vol=("volume", "sum"), rng=("range_t", "mean"))
        rba_prof[name] = {
            f"m+{int(k)}": {"vol_share_in_window_pct": float(r.vol / g["vol"].sum() * 100),
                            "mean_range_ticks": float(r.rng)}
            for k, r in g.iterrows()}
    out["rba_window_minute_profile_all_days"] = rba_prof

    # ---- 4. U-curve: mean |1m ret| by CT hour --------------------------------
    ucurve = {}
    for name, a, b in ERA_BOUNDS:
        e = fb[(fb["session_date"] >= a) & (fb["session_date"] <= b)]
        g = e.groupby(e["ct_minute"] // 60)["ret1"].agg(
            lambda s: float(np.abs(s).mean() * 1e4))
        ucurve[name] = {int(h): v for h, v in g.items()}
    out["mean_abs_1m_ret_by_ct_hour_bp"] = ucurve

    # ---- 5. weekday structure -------------------------------------------------
    wd = {}
    for name, a, b in ERA_BOUNDS:
        e = front[(front["session_date"] >= a) & (front["session_date"] <= b)]
        g = e.groupby(e["session_date"].dt.dayofweek)["volume"].median()
        wd[name] = {int(k): float(v) for k, v in g.items()}
    out["median_front_volume_by_weekday"] = wd

    # ---- 6. v1 reconciliation -------------------------------------------------
    v1w = front[(front["session_date"] >= "2025-09-10") &
                (front["session_date"] <= "2026-10-01")]
    out["v1_reconciliation"] = {
        "window": ["2025-09-10", "2026-10-01"],
        "median_front_daily_volume_full_session": float(v1w["volume"].median()),
        "median_front_rth_volume": float(v1w["rth_volume"].median()),
        "rth_share_median_pct": float((v1w["rth_volume"] / v1w["volume"]).median() * 100),
        "v1_ibkr_rth_only_median_daily": 35139.0,
        "note": ("v1 IBKR useRTH=true daily median ~35.1k lots (v1 dossier); "
                 "vendor full-session median vs RTH-only share quantifies what "
                 "the RTH-only recording hid"),
    }

    # ---- Sydney open / home-session activity concentration --------------------
    sydopen = {}
    for name, a, b in ERA_BOUNDS:
        e = fb[(fb["session_date"] >= a) & (fb["session_date"] <= b)]
        w = e[(e["syd_min"] >= 9 * 60 + 45) & (e["syd_min"] < 10 * 60 + 15)]
        pre = e[(e["syd_min"] >= 9 * 60 + 15) & (e["syd_min"] < 9 * 60 + 45)]
        sydopen[name] = {
            "open30_0945_1015_syd_vol_share_pct": float(
                w["volume"].sum() / e["volume"].sum() * 100),
            "pre30_vol_share_pct": float(pre["volume"].sum() / e["volume"].sum() * 100),
            "open30_mean_range_ticks": float(w["range_t"].mean()),
            "pre30_mean_range_ticks": float(pre["range_t"].mean()),
        }
    out["sydney_open_30min"] = sydopen

    L.jdump(out, OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
