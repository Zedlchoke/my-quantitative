"""6B v2 a4 — event-day anatomy: BoE MPC (12:00 London) + FOMC (13:00 CT)
release-anchored volume/vol/range timing descriptives on the 1m panel.
NO conditional mean-return tables (PnL-linked selection = NOT_RUN).
Emits 6B_a4_events.json."""
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
d = df[df["contract"].notna()].merge(held, on="session_date", how="inner")
d = d[d["contract"] == d["held"]].copy()
d["sd"] = pd.to_datetime(d["session_date"]).dt.strftime("%Y-%m-%d")
d = d[d["sd"] != d["sd"].max()]  # drop truncated final session
lon = d["dt"].dt.tz_convert(lib.LON)
chi = d["dt"].dt.tz_convert(lib.CHI)
d["lon_min"] = lon.dt.hour * 60 + lon.dt.minute
d["ct_min"] = chi.dt.hour * 60 + chi.dt.minute
d["lret"] = np.log(d["close"] / d["close"].shift())
d.loc[d["high"] == d["low"], "lret"] = 0.0
d["dow"] = pd.to_datetime(d["session_date"]).dt.dayofweek
d["year"] = pd.to_datetime(d["session_date"]).dt.year


def window_stats(x, center_min, pre, post, tz_col):
    """Release-anchored descriptive stats in [center-pre, center+post) minutes."""
    w = x[(x[tz_col] >= center_min - pre) & (x[tz_col] < center_min + post)]
    if not len(w):
        return None
    per_day = w.groupby("sd").agg(
        vol=("volume", "sum"), absret=("lret", lambda s: float(s.abs().sum())),
        rng=("lret", lambda s: float(s.max() - s.min())))
    return {"n_days": int(w["sd"].nunique()),
            "median_vol": float(per_day["vol"].median()),
            "p90_vol": float(per_day["vol"].quantile(.9)),
            "median_absret_sum": float(per_day["absret"].median()),
            "median_range": float(per_day["rng"].median())}


def minute_profile(x, center_min, pre, post, tz_col):
    w = x[(x[tz_col] >= center_min - pre) & (x[tz_col] < center_min + post)]
    return {int(k): float(v) for k, v in
            w.groupby(tz_col)["volume"].mean().items()}


# ============ BoE MPC ==========================================================
boe = lib.load_mpc_calendar()
boe = boe[boe["date"] <= pd.Timestamp("2026-09-30")]
boe_dates = set(boe["date"].dt.strftime("%Y-%m-%d"))
bd = d[d["sd"].isin(boe_dates)]
ctrl_th = d[(d["dow"] == 3) & (~d["sd"].isin(boe_dates))]
ctrl_all = d[~d["sd"].isin(boe_dates)]

OUT["boe"] = {
    "n_mpc_days_in_panel": int(bd["sd"].nunique()),
    "n_rate_change_days": int(boe["changed_rate"].sum()),
    "n_hold_days_in_panel": int(bd["sd"].nunique() - boe["changed_rate"].sum()),
    "release_minute_empirical": {
        "argmax_mean_volume_minute_london": int(
            bd[(bd["lon_min"] >= 11 * 60) & (bd["lon_min"] < 12 * 60 + 30)]
            .groupby("lon_min")["volume"].mean().idxmax()),
        "note": "v1 had 12:00 London as POSTULATED convention; this is the measured spike minute",
    },
    "windows": {
        "m30_m30": {
            "mpc": window_stats(bd, 720, 30, 30, "lon_min"),
            "non_mpc_thursday": window_stats(ctrl_th, 720, 30, 30, "lon_min"),
            "non_event_all": window_stats(ctrl_all, 720, 30, 30, "lon_min"),
        },
        "pre_window_m30_m0": {
            "mpc": window_stats(bd, 720, 30, 0, "lon_min"),
            "non_mpc_thursday": window_stats(ctrl_th, 720, 30, 0, "lon_min"),
        },
        "post_window_m0_m30": {
            "mpc": window_stats(bd, 720, 0, 30, "lon_min"),
            "non_mpc_thursday": window_stats(ctrl_th, 720, 0, 30, "lon_min"),
        },
        "first5m": {
            "mpc": window_stats(bd, 720, 0, 5, "lon_min"),
            "non_mpc_thursday": window_stats(ctrl_th, 720, 0, 5, "lon_min"),
        },
    },
    "day_level": {
        "mpc_median_day_volume": float(bd.groupby("sd")["volume"].sum().median()),
        "thursday_median_day_volume": float(ctrl_th.groupby("sd")["volume"].sum().median()),
        "mpc_p90_day_volume": float(bd.groupby("sd")["volume"].sum().quantile(.9)),
        "thursday_p90_day_volume": float(ctrl_th.groupby("sd")["volume"].sum().quantile(.9)),
        "mpc_median_day_range_pct": float(
            bd.groupby("sd").apply(
                lambda g: (g["high"].max() - g["low"].min()) / g["close"].iloc[-1] * 100,
                include_groups=False).median()),
        "thursday_median_day_range_pct": float(
            ctrl_th.groupby("sd").apply(
                lambda g: (g["high"].max() - g["low"].min()) / g["close"].iloc[-1] * 100,
                include_groups=False).median()),
    },
    "minute_profile_m30_p30": {
        "mpc": minute_profile(bd, 720, 30, 30, "lon_min"),
        "non_mpc_thursday": minute_profile(ctrl_th, 720, 30, 30, "lon_min"),
    },
}

# split: change vs hold days (descriptive only)
chg = boe[boe["changed_rate"]]["date"].dt.strftime("%Y-%m-%d")
hld = boe[~boe["changed_rate"]]["date"].dt.strftime("%Y-%m-%d")
bdc = bd[bd["sd"].isin(set(chg))]
bdh = bd[bd["sd"].isin(set(hld))]
OUT["boe"]["change_vs_hold"] = {
    "n_change": int(bdc["sd"].nunique()), "n_hold": int(bdh["sd"].nunique()),
    "median_day_volume_change": float(bdc.groupby("sd")["volume"].sum().median()),
    "median_day_volume_hold": float(bdh.groupby("sd")["volume"].sum().median()),
    "first5m_vol_change": window_stats(bdc, 720, 0, 5, "lon_min"),
    "first5m_vol_hold": window_stats(bdh, 720, 0, 5, "lon_min"),
}

# ============ FOMC =============================================================
fomc = lib.load_fomc()
fomc = fomc[(fomc["date"] >= pd.Timestamp("2020-01-01"))
            & (fomc["date"] <= pd.Timestamp("2026-09-30"))]
fomc_dates = set(fomc["date"].dt.strftime("%Y-%m-%d"))
fd = d[d["sd"].isin(fomc_dates)]
# control: non-event Wednesdays (FOMC mostly Wed) — and non-event all days
ctrl_wed = d[(d["dow"] == 2) & (~d["sd"].isin(fomc_dates))]
# 13:00 CT statement convention; use only scheduled-day statements (13:00 CT);
# intermeeting specials (2020-03-03 10:00 ET etc.) get their own section.
sched = fomc[fomc["time_et"].notna()].copy()
sched["has_1400et"] = sched["time_et"].apply(lambda t: (t.hour, t.minute) == (14, 0))
n_1300 = int(sched["has_1400et"].sum())
inter = fomc[fomc["time_et"].isna()]
OUT["fomc"] = {
    "n_statement_days_in_panel": int(fd["sd"].nunique()),
    "n_with_release_time_proof": int(len(sched)),
    "n_at_1400_et_1300ct": n_1300,
    "release_times_et_other": sorted({
        f"{t.hour:02d}:{t.minute:02d}" for t in sched[~sched["has_1400et"]]["time_et"]}),
    "n_no_time_proof": int(len(inter)),
    "no_time_proof_dates": [str(x.date()) for x in inter["date"]],
    "windows_1300_ct": {
        "fomc": window_stats(fd, 13 * 60, 30, 30, "ct_min"),
        "non_fomc_wednesday": window_stats(ctrl_wed, 13 * 60, 30, 30, "ct_min"),
        "pre": {"fomc": window_stats(fd, 13 * 60, 30, 0, "ct_min"),
                "non_fomc_wednesday": window_stats(ctrl_wed, 13 * 60, 30, 0, "ct_min")},
        "post": {"fomc": window_stats(fd, 13 * 60, 0, 30, "ct_min"),
                 "non_fomc_wednesday": window_stats(ctrl_wed, 13 * 60, 0, 30, "ct_min")},
        "first5m": {"fomc": window_stats(fd, 13 * 60, 0, 5, "ct_min"),
                    "non_fomc_wednesday": window_stats(ctrl_wed, 13 * 60, 0, 5, "ct_min")},
    },
    "day_level": {
        "fomc_median_day_volume": float(fd.groupby("sd")["volume"].sum().median()),
        "wednesday_median_day_volume": float(ctrl_wed.groupby("sd")["volume"].sum().median()),
        "fomc_p90_day_volume": float(fd.groupby("sd")["volume"].sum().quantile(.9)),
        "wednesday_p90_day_volume": float(ctrl_wed.groupby("sd")["volume"].sum().quantile(.9)),
    },
    "minute_profile_m30_p30_ct": {
        "fomc": minute_profile(fd, 13 * 60, 30, 30, "ct_min"),
        "non_fomc_wednesday": minute_profile(ctrl_wed, 13 * 60, 30, 30, "ct_min"),
    },
}

# intermeeting specials (2020 COVID moves) — best-effort anchors
specials = {
    "2020-03-03": ("10:00 ET", 10 * 60 + 60 - 60, "ct"),   # 09:00 CT
    "2020-03-15": ("Sunday 19:00 ET emergency cut", None, "ct"),
    "2020-03-19": ("08:00 ET", 7 * 60, "ct"),
    "2020-03-23": ("08:00 ET", 7 * 60, "ct"),
}
sp_rows = []
for s, (label, anchor, _) in specials.items():
    g = d[d["sd"] == s]
    if not len(g):
        continue
    row = {"date": s, "label": label,
           "day_volume": int(g["volume"].sum()),
           "day_range_pct": float((g["high"].max() - g["low"].min())
                                  / g["close"].iloc[-1] * 100)}
    if anchor is not None:
        w = window_stats(g, anchor, 15, 15, "ct_min")
        row["pm15pm15_window"] = w
    sp_rows.append(row)
OUT["fomc"]["intermeeting_2020_specials"] = sp_rows

# ============ top volume spikes (1m) — event attribution =======================
top = d.nlargest(12, "volume")[["sd", "dt", "volume", "high", "low"]]
OUT["top12_1m_volume_bars"] = [
    {"session": str(t.sd), "dt_utc": str(t.dt), "volume": int(t.volume),
     "in_boe_window": (t.sd in boe_dates)}
    for t in top.itertuples()]

lib.jdump(OUT, os.path.join(HERE, "6B_a4_events.json"))
print("a4 done. BOE m30/m30 median vol:",
      OUT["boe"]["windows"]["m30_m30"]["mpc"]["median_vol"], "vs",
      OUT["boe"]["windows"]["m30_m30"]["non_mpc_thursday"]["median_vol"])
print("FOMC first5m:", OUT["fomc"]["windows_1300_ct"]["first5m"])
