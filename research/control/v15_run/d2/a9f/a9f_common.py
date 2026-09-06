#!/usr/bin/env python3
"""V15 D2 A9F feasibility audit - shared data layer.

Measures RUNNABILITY ONLY: decision counts, warmup coverage, turnover/cost
structures, fold population, hole-refusal census, control identifiability.
NO PnL, NO returns, NO expectancy of positions is computed anywhere.

Reads (READ-ONLY):
  /Users/hoangminhlong/my-quantitative/.worktrees/crypto/v15/integration/v15_data/parquet/{metrics,klines,funding}
  research/control/v15_run/staging/staging_report.json   (defect census)
Writes (allowed): research/control/v15_run/d2/a9f/**
"""
import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v15/d2-a9f-feasibility")
DATA = Path("/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v15/integration/v15_data/parquet")
STAGING_REPORT = WT / "research/control/v15_run/staging/staging_report.json"

FROZEN_UNIVERSE = [
    "1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT",
    "BCHUSDT", "BNBUSDT", "BOMEUSDT", "BTCUSDT", "DOGEUSDT",
    "ENAUSDT", "ETHUSDT", "LINKUSDT", "NEARUSDT", "ONGUSDT",
    "SOLUSDT", "SUIUSDT", "WLDUSDT", "XRPUSDT", "ZECUSDT",
]
S0_START = dt.date(2025, 8, 22)
S0_END = dt.date(2026, 8, 21)
STAGING_START = dt.date(2025, 6, 20)
LAG_DAYS = 3                     # MEASURED_BOUND_LAG_3D
HOLE_FRAC_REFUSE = 0.10          # amendment-1 hole-refusal rule
# Fold calendar: proposers' unanimous working thirds, 1-day purge (V12/V14 contract)
FOLDS = {
    "F0": (dt.date(2025, 8, 22), dt.date(2025, 12, 20)),
    "PURGE1": (dt.date(2025, 12, 21), dt.date(2025, 12, 21)),
    "F1": (dt.date(2025, 12, 22), dt.date(2026, 4, 20)),
    "PURGE2": (dt.date(2026, 4, 21), dt.date(2026, 4, 21)),
    "F2": (dt.date(2026, 4, 22), dt.date(2026, 8, 21)),
}
def daterange(a, b):
    out, d = [], a
    while d <= b:
        out.append(d)
        d += dt.timedelta(days=1)
    return out


FOLD_IDS = ["F0", "F1", "F2"]
SCORING_DAYS = [d for f in FOLD_IDS for d in daterange(*FOLDS[f])]

# Cost model (from proposals' stated ex-ante assumptions)
FEE_BPS = 5.0
FEE_STRESS_BPS = 7.5
# Tick slippage per fill: the staged instrument config for the V15 universe is
# NOT present in staged data (only BTC/ETH exist in the legacy catalog), so the
# per-symbol native-tick component is declared NOT_RUN from staged config and
# priced under a labelled FALLBACK band (bps of price per fill), covering
# essentially all liquid Binance USDT-M perpetual tick-notional ratios.
TICK_BPS_FALLBACK = {"low": 0.5, "high": 2.0}
STRESS_EXTRA_TICKS = 2.0


def fold_of(d):
    for f in FOLD_IDS:
        a, b = FOLDS[f]
        if a <= d <= b:
            return f
    return None


# --------------------------------------------------------------------------
# Defect census (amendment-1): per-symbol missing metrics days in staging window
# --------------------------------------------------------------------------
def load_defect_census():
    rep = json.loads(STAGING_REPORT.read_text())
    defect_days = {s: set() for s in FROZEN_UNIVERSE}
    for x in rep["defects"]["metrics"]:
        defect_days[x["symbol"]].add(dt.date.fromisoformat(x["date"]))
    return defect_days


# --------------------------------------------------------------------------
# Metrics panel
# --------------------------------------------------------------------------
def load_symbol_metrics(sym):
    """Return dict with per-day metric views, over available (staged) days only.

    day_open00  : value at the 00:00 label row (daily observation per A5)
    day_close55 : value at the 23:55 label row (day-end stock per A6)
    day_agg     : A6 daily aggression = mean of clip(ln r_t, -1.609, 1.609), r_t = taker ratio clipped [0.2,5]
    day_absagg  : A6-P2 denominator daily mean = mean |clip(ln r_t)|  (same clip bounds)
    """
    df = pd.read_parquet(DATA / "metrics" / f"{sym}.parquet")
    ct = pd.to_datetime(df["create_time"])
    df = df.assign(day=ct.dt.date, label=ct.dt.strftime("%H:%M")).sort_values("ts")
    out = {}
    r = df["sum_taker_long_short_vol_ratio"].clip(0.2, 5.0)
    lr = np.log(r)
    lrc = lr.clip(-1.609, 1.609)
    tmp = pd.DataFrame({
        "day": df["day"].values,
        "label": df["label"].values,
        "oi": df["sum_open_interest"].values,
        "oiv": df["sum_open_interest_value"].values,
        "count_tt": df["count_toptrader_long_short_ratio"].values,
        "sum_tt": df["sum_toptrader_long_short_ratio"].values,
        "count_ls": df["count_long_short_ratio"].values,
        "lrc": lrc.values,
        "alrc": lrc.abs().values,
    })
    g = tmp.groupby("day")
    out["n_labels"] = g.size()
    first = g.first()
    last = g.last()
    out["oi00"] = first["oi"]          # 00:00 label row
    out["oi55"] = last["oi"]           # 23:55 label row
    out["oiv55"] = last["oiv"]
    out["count_tt00"] = first["count_tt"]
    out["sum_tt00"] = first["sum_tt"]
    out["count_ls00"] = first["count_ls"]
    out["agg"] = g["lrc"].mean()       # A6 daily aggression
    out["absagg"] = g["alrc"].mean()   # A6-P2 denominator
    return out


# --------------------------------------------------------------------------
# Klines daily panel (controls only; price never enters any anchor feature)
# --------------------------------------------------------------------------
def load_symbol_klines_daily(sym):
    df = pd.read_parquet(DATA / "klines" / f"{sym}.parquet")
    day = pd.to_datetime(df["open_time_ms"], unit="ms").dt.date
    g = df.assign(day=day).groupby("day")
    hi = g["high"].max()
    lo = g["low"].min()
    cl = g["close"].last()
    prev_close = cl.shift(1)
    tr_pct = (hi - lo) / prev_close      # daily true-range percent (close-to-close gap included in hi-lo only as specified)
    return pd.DataFrame({"high": hi, "low": lo, "close": cl, "tr_pct": tr_pct})


def hole_refuse(span_days_sorted, missing_set):
    """Amendment-1 rule: >10% missing metrics-day cells in the feature window
    => refuse. span_days_sorted: calendar dates spanned by the feature window;
    missing_set: defect dates for the symbol."""
    if not span_days_sorted:
        return True, 1, 1
    span = (span_days_sorted[-1] - span_days_sorted[0]).days + 1
    n_missing = sum(1 for d in missing_set if span_days_sorted[0] <= d <= span_days_sorted[-1])
    return (n_missing / span) > HOLE_FRAC_REFUSE, n_missing, span


def last_available_dates(avail_sorted, end_date, n):
    """Last n available metrics dates <= end_date (ascending list of dates)."""
    lo, hi = 0, len(avail_sorted)
    while lo < hi:
        mid = (lo + hi) // 2
        if avail_sorted[mid] <= end_date:
            lo = mid + 1
        else:
            hi = mid
    return avail_sorted[max(0, lo - n):lo]
