"""Frozen candidate strategies for cell BTC_H1 (plan sec 6; mechanisms fixed
from economic anatomy BEFORE any dry-run counts were seen; at most ONE per
data-sufficient phase per the census).

This module builds, per candidate, the ENGINE INPUTS: entry triggers, stop
flags, phase gate. The engine (signal_path.run_event_engine) owns the book.
Contains NO returns path — only boolean triggers and the event counter.

Stop-window law (frozen clarification, fixed pre-scoring with no PnL ever
computed): trailing Donchian extremes for STOPS/EXITS use the PRIOR-bar
window (excluding the current bar), so a bar making a new extreme can
trigger on itself. Entry windows exclude the current bar by construction
(breakout must exceed the PRIOR N-bar extreme).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from signal_path import run_event_engine

MIN_HOLD_BARS = 24          # frozen churn law = phase-rule transition buffer
DONCHIAN_ENTRY_BARS = 480   # 20 days x 24h (Turtle-20 entry convention)
DONCHIAN_EXIT_BARS = 240    # 10 days x 24h (Turtle-10 stop convention)
RANGE_WINDOW_BARS = 720     # 30 days (same anchor as the phase rule SMA)
RANGE_ENTRY_QUANTILE = 0.25  # lower quartile of the trailing 30d range


def _roll_max(x: np.ndarray, w: int) -> np.ndarray:
    return pd.Series(x).rolling(w).max().to_numpy()


def _roll_min(x: np.ndarray, w: int) -> np.ndarray:
    return pd.Series(x).rolling(w).min().to_numpy()


def _prior_window(arr: np.ndarray, w: int) -> np.ndarray:
    """Trailing w-bar extreme over PRIOR bars only (excludes current)."""
    shifted = np.concatenate([[np.nan], arr[:-1]])
    return pd.Series(shifted).rolling(w, min_periods=w).max().to_numpy()


def _prior_min(arr: np.ndarray, w: int) -> np.ndarray:
    shifted = np.concatenate([[np.nan], arr[:-1]])
    return pd.Series(shifted).rolling(w, min_periods=w).min().to_numpy()


def signals_uptrend_breakout(df: pd.DataFrame, fold_ids: np.ndarray):
    """PSV1-BTC_H1-UPTREND-BREAKOUT_CONT — long only.

    Entry: close > PRIOR 480-bar max of highs, while state == UPTREND.
    Stop:  close < PRIOR 240-bar min of lows (risk override).
    Gate:  state == UPTREND (gate-off exit after min-hold).
    """
    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    state = df["state_label"].to_numpy()
    n = len(close)
    hi_prev = _prior_window(high, DONCHIAN_ENTRY_BARS)
    lo_prev = _prior_min(low, DONCHIAN_EXIT_BARS)
    entry = (state == "UPTREND") & (close > hi_prev)
    stop = close < lo_prev
    active = state == "UPTREND"
    ev = run_event_engine(entry, np.zeros(n, dtype=bool), stop, active,
                          MIN_HOLD_BARS, fold_ids)
    return ev, entry


def signals_downtrend_breakdown_cont(df: pd.DataFrame, fold_ids: np.ndarray):
    """PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT — short only (mirror).

    Entry: close < PRIOR 480-bar min of lows, while state == DOWNTREND.
    Stop:  close > PRIOR 240-bar max of highs (risk override).
    Gate:  state == DOWNTREND.
    """
    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    state = df["state_label"].to_numpy()
    n = len(close)
    lo_prev = _prior_min(low, DONCHIAN_ENTRY_BARS)
    hi_prev = _prior_window(high, DONCHIAN_EXIT_BARS)
    entry = (state == "DOWNTREND") & (close < lo_prev)
    stop = close > hi_prev
    active = state == "DOWNTREND"
    ev = run_event_engine(np.zeros(n, dtype=bool), entry, stop, active,
                          MIN_HOLD_BARS, fold_ids)
    return ev, entry


def signals_acc_floor_provision(df: pd.DataFrame, fold_ids: np.ndarray):
    """PSV1-BTC_H1-ACC-FLOOR_PROVISION — long only.

    Entry: state == ACCUMULATION and close in the lower quartile of the
    trailing 720-bar (30d, INCLUDING current bar) close range.
    Hold gate: {ACCUMULATION, UPTREND} — the position rides the ACC->UP
    markup transition by design; exits when the state leaves the gate
    (after min-hold).
    Stop: close below the 30d range low observed at the ENTRY bar (a NEW 30d
    low after entry = structure break; risk override).
    """
    close = df["close"].to_numpy(float)
    state = df["state_label"].to_numpy()
    n = len(close)
    r_hi = _roll_max(close, RANGE_WINDOW_BARS)
    r_lo = _roll_min(close, RANGE_WINDOW_BARS)
    height = r_hi - r_lo
    in_lower_q = close <= r_lo + RANGE_ENTRY_QUANTILE * height
    trigger = (state == "ACCUMULATION") & in_lower_q & np.isfinite(height)
    # stop: NEW 30d low strictly after entry (entry bar itself is the anchor)
    stop = np.zeros(n, dtype=bool)
    in_pos = False
    stop_level = np.nan
    for t in range(n):
        if not in_pos:
            if trigger[t]:
                in_pos = True
                stop_level = r_lo[t]
        else:
            if np.isfinite(stop_level) and close[t] < stop_level:
                stop[t] = True
                in_pos = False
    hold_gate = (state == "ACCUMULATION") | (state == "UPTREND")
    ev = run_event_engine(trigger, np.zeros(n, dtype=bool), stop, hold_gate,
                          MIN_HOLD_BARS, fold_ids)
    return ev, trigger
