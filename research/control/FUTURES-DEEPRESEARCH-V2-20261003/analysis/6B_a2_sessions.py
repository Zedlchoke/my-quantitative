"""6B v2 a2 — session/intraday structure, DST-correct (city-clock segments):
London morning + Asia overnight (invisible to v1's RTH-only bars), era drift.
Volume/realized-vol/range descriptives only. Emits 6B_a2_sessions.json."""
from __future__ import annotations

import importlib.util
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "six_b_deep_lib", os.path.join(HERE, "6B_deep_lib.py"))
lib = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lib)

OUT = {}

df = pd.read_parquet(os.path.join(lib.CACHE, "6b_annotated_1m.parquet"))
held = pd.read_parquet(os.path.join(lib.CACHE, "held_calendar.parquet"))
d = df[df["contract"].notna()].merge(
    held, on="session_date", how="inner")
d = d[d["contract"] == d["held"]].copy()
d["year"] = pd.to_datetime(d["session_date"]).dt.year
# drop the truncated final session
d = d[d["session_date"] != d["session_date"].max()]
d["lret"] = np.log(d["close"] / d["close"].shift())
d.loc[d["high"] == d["low"], "lret"] = 0.0  # dohji minute: no range info
d["absret"] = d["lret"].abs()

SEG_ORDER = ["asia_early", "asia_core", "lon_pre_boe", "boe_release",
             "lon_us_overlap", "us_rth", "us_close", "other"]

# note: segments overlap by construction (a minute can be in both lon_pre_boe
# and us_rth during 08:30-11:30 CT == 13:30-16:30 London summer). To avoid
# double counting in SHARES, use a mutually exclusive partition with GBP
# priority: boe_release > lon_pre_boe > asia_core > asia_early > us_rth >
# us_close > lon_us_overlap(resid) > other.
d["seg_excl"] = "other"
prio = ["boe_release", "lon_pre_boe", "asia_core", "asia_early",
        "us_rth", "us_close"]
seg_any = {s: d["segment"] == s for s in SEG_ORDER[:7]}
for s in prio:
    d.loc[seg_any[s], "seg_excl"] = s

# ---- volume + activity shares by year -----------------------------------------
vol_by = d.pivot_table(index="year", columns="seg_excl",
                       values="volume", aggfunc="sum").fillna(0)
share = vol_by.div(vol_by.sum(axis=1), axis=0)
OUT["volume_share_by_segment_by_year"] = {
    str(y): {c: float(share.loc[y, c]) for c in share.columns} for y in share.index}
# active-minute share (liquidity presence, not contracts)
act = d.pivot_table(index="year", columns="seg_excl", values="volume",
                    aggfunc="size").fillna(0)
ashare = act.div(act.sum(axis=1), axis=0)
OUT["active_minute_share_by_segment_by_year"] = {
    str(y): {c: float(ashare.loc[y, c]) for c in ashare.columns} for y in ashare.index}

# ---- per-minute realized vol by segment ---------------------------------------
mrv = d.groupby(["year", "seg_excl"])["lret"].std() * np.sqrt(252 * 1380) * 100
OUT["per_minute_vol_by_segment_pct_ann_by_year"] = {
    f"{y}|{s}": float(v) for (y, s), v in mrv.items()}

# ---- hour-of-London-day volume profile by era ---------------------------------
lon = d["dt"].dt.tz_convert(lib.LON)
d["lon_hour"] = lon.dt.hour
eras = [(2020, 2021, "2020-2021"), (2022, 2022, "2022"),
        (2023, 2024, "2023-2024"), (2025, 2026, "2025-2026")]
prof = {}
for y0, y1, name in eras:
    g = d[(d["year"] >= y0) & (d["year"] <= y1)]
    p = g.groupby("lon_hour")["volume"].sum()
    prof[name] = {int(h): float(v) for h, v in (p / p.sum()).items()}
OUT["volume_share_by_london_hour"] = prof
OUT["london_morning_share_07_12"] = {
    name: float(sum(v for h, v in p.items() if 7 <= h < 12))
    for name, p in prof.items()}
OUT["asia_overnight_share_00_07_london"] = {
    name: float(sum(v for h, v in p.items() if h < 7))
    for name, p in prof.items()}

# ---- BoE release window alignment across DST mismatches ------------------------
# demonstrate DST-correct anchoring: minute-of-day (CT) of 12:00 London on MPC
# Thursdays around UK/US DST switches differs by an hour in CT but the London
# clock anchor is stable.
boe = lib.load_mpc_calendar()
boe = boe[boe["date"] <= pd.Timestamp("2026-09-30")]
sample_days = ["2022-03-17", "2022-10-06", "2022-11-03", "2023-03-23",
               "2023-11-02", "2024-03-21", "2024-10-31", "2025-03-20"]
rows = []
for s in sample_days:
    ts = pd.Timestamp(s, tz="UTC").tz_convert(lib.LON).replace(hour=12, minute=0)
    ct = ts.tz_convert(lib.CHI)
    rows.append({"date": s, "london_1200_ct_minute": int(ct.hour * 60 + ct.minute),
                 "ct_clock": ct.strftime("%H:%M")})
OUT["boe_1200_london_in_ct_clock"] = rows

# ---- volume spike minute on MPC days (empirical release-minute check) ---------
boe_dates = set(boe["date"].dt.strftime("%Y-%m-%d"))
d["sd"] = pd.to_datetime(d["session_date"]).dt.strftime("%Y-%m-%d")
d["lon_min"] = lon.dt.hour * 60 + lon.dt.minute
bd = d[d["sd"].isin(boe_dates)]
win = bd[(bd["lon_min"] >= 11 * 60 + 30) & (bd["lon_min"] < 12 * 60 + 30)]
minprof = win.groupby("lon_min")["volume"].mean()
top_minutes = minprof.nlargest(5)
OUT["mpc_day_mean_volume_by_london_minute_1130_1230"] = {
    str(k): float(v) for k, v in minprof.items()}
OUT["mpc_day_top5_minutes"] = {str(k): float(v) for k, v in top_minutes.items()}
OUT["n_mpc_days_in_panel"] = int(bd["sd"].nunique())

# ---- matched control: same London minutes on non-MPC Thursdays -----------------
d["dow"] = pd.to_datetime(d["session_date"]).dt.dayofweek
ctrl = d[(d["dow"] == 3) & (~d["sd"].isin(boe_dates))]
cwin = ctrl[(ctrl["lon_min"] >= 11 * 60 + 30) & (ctrl["lon_min"] < 12 * 60 + 30)]

def _wstats(x):
    return {"n_sessions": int(x["sd"].nunique()),
            "mean_vol_per_min": float(x.groupby("lon_min")["volume"].mean().mean()),
            "mean_absret_per_min": float(x.groupby("lon_min")["absret"].mean().mean())}

OUT["boe_window_1130_1230"] = {"mpc": _wstats(win), "non_mpc_thursday": _wstats(cwin)}

# narrow release window 12:00-12:05
w2 = bd[(bd["lon_min"] >= 12 * 60) & (bd["lon_min"] < 12 * 60 + 5)]
c2 = ctrl[(ctrl["lon_min"] >= 12 * 60) & (ctrl["lon_min"] < 12 * 60 + 5)]
OUT["boe_window_1200_1205"] = {"mpc": _wstats(w2), "non_mpc_thursday": _wstats(c2)}

# full-day volume/range comparison (descriptive, not conditional-return)
def _day_stats(x):
    g = x.groupby("sd")
    return {"n": int(x["sd"].nunique()),
            "median_day_volume": float(g["volume"].sum().median()),
            "p90_day_volume": float(g["volume"].sum().quantile(.9))}

OUT["mpc_vs_thursday_daily_volume"] = {"mpc": _day_stats(bd), "non_mpc_thursday": _day_stats(ctrl)}

lib.jdump(OUT, os.path.join(HERE, "6B_a2_sessions.json"))
print("a2 done. London-morning share:", OUT["london_morning_share_07_12"])
print("MPC top minutes:", OUT["mpc_day_top5_minutes"])
