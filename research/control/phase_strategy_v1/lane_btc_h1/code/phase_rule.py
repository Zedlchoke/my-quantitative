"""Phase rule for cell BTC_H1 — PSV1 cycle PHASE-STRATEGY-V1, lane L1.

Code-owned deterministic PIT phase classification per
freezes/phase_rule_freeze.json (frozen BEFORE any history-wide computation).

Outcome-blindness law: this module contains NO returns, NO PnL, NO equity
code path. Labels and durations only.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PHASES = [
    "ACCUMULATION",
    "UPTREND",
    "DISTRIBUTION",
    "DOWNTREND",
    "TRANSITION_UNKNOWN",
]

# Frozen parameters (must equal freezes/phase_rule_freeze.json; asserted by test)
ADX_PERIOD = 14
ADX_TREND_THRESHOLD = 20.0
ADX_MARGIN = 2.0
SMA_SLOW_BARS = 720
WARMUP_BARS = 720
TRANSITION_BUFFER_BARS = 24


def lane_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def load_freeze(name: str) -> dict:
    p = lane_dir() / "freezes" / name
    return json.loads(p.read_text())


def wilder_rma(x: np.ndarray, period: int) -> np.ndarray:
    """Wilder's smoothing: seed = SMA of first `period` values, then
    s_t = s_{t-1} + (x_t - s_{t-1}) / period. Values before the seed are NaN."""
    out = np.full_like(x, np.nan, dtype=float)
    n = len(x)
    if n < period:
        return out
    out[period - 1] = x[:period].mean()
    period_f = float(period)
    for t in range(period, n):
        out[t] = out[t - 1] + (x[t] - out[t - 1]) / period_f
    return out


def adx_di(high: np.ndarray, low: np.ndarray, close: np.ndarray,
           period: int = ADX_PERIOD):
    """Standard Wilder ADX / +DI / -DI. Returns (adx, di_plus, di_minus).

    Degenerate-flat law (frozen): where TR == 0, DX := 0.
    """
    n = len(high)
    di_plus = np.full(n, np.nan)
    di_minus = np.full(n, np.nan)
    adx = np.full(n, np.nan)
    if n < 2 * period:
        return adx, di_plus, di_minus
    prev_close = np.roll(close, 1)
    up = high[1:] - high[:-1]
    dn = low[:-1] - low[1:]
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = np.maximum.reduce([
        high[1:] - low[1:],
        np.abs(high[1:] - prev_close[1:]),
        np.abs(low[1:] - prev_close[1:]),
    ])
    sm_tr = wilder_rma(tr, period)
    sm_pdm = wilder_rma(plus_dm, period)
    sm_mdm = wilder_rma(minus_dm, period)
    with np.errstate(invalid="ignore", divide="ignore"):
        di_plus[1:] = 100.0 * sm_pdm / sm_tr
        di_minus[1:] = 100.0 * sm_mdm / sm_tr
        denom = di_plus[1:] + di_minus[1:]
        dx_inner = np.where(denom > 0,
                            100.0 * np.abs(di_plus[1:] - di_minus[1:]) / denom,
                            0.0)
        dx = np.where(sm_tr > 0, dx_inner, 0.0)
    dx = np.where(np.isfinite(dx), dx, 0.0)
    dx_s = dx[period - 1:]  # DX valid from bar `period` (array-index period-1)
    if len(dx_s) >= period:
        adx_vals = wilder_rma(dx_s, period)
        adx[2 * period - 1:] = adx_vals[period - 1:]
    return adx, di_plus, di_minus


def raw_labels(close: np.ndarray, adx: np.ndarray, di_plus: np.ndarray,
               di_minus: np.ndarray, sma_slow: np.ndarray,
               warmup_bars: int = WARMUP_BARS,
               adx_threshold: float = ADX_TREND_THRESHOLD,
               adx_margin: float = ADX_MARGIN) -> list[str]:
    """Frozen raw label law (top-down, total partition). Parameters default to
    the frozen constants; sensitivity variants may notch threshold/margin
    ONLY for the reported label-agreement table (never iterated)."""
    lo = adx_threshold - adx_margin
    hi = adx_threshold + adx_margin
    out: list[str] = []
    for t in range(len(close)):
        if t < warmup_bars or not np.isfinite(adx[t]):
            out.append("TRANSITION_UNKNOWN")
            continue
        if lo < adx[t] < hi:
            out.append("TRANSITION_UNKNOWN")
        elif adx[t] >= hi:
            out.append("UPTREND" if di_plus[t] >= di_minus[t] else "DOWNTREND")
        else:  # adx[t] <= lo
            out.append("DISTRIBUTION" if close[t] >= sma_slow[t] else "ACCUMULATION")
    return out


def state_labels(raw: list[str],
                 buffer_bars: int = TRANSITION_BUFFER_BARS) -> list[str]:
    """Frozen state machine: a new raw label must persist `buffer_bars`
    consecutive bars to be adopted (TRANSITION_UNKNOWN obeys the same law)."""
    state = raw[0] if raw else "TRANSITION_UNKNOWN"
    pending_label: str | None = None
    pending_count = 0
    out: list[str] = []
    for r in raw:
        if r == state:
            pending_label, pending_count = None, 0
        else:
            if r == pending_label:
                pending_count += 1
            else:
                pending_label, pending_count = r, 1
            if pending_count >= buffer_bars:
                state = r
                pending_label, pending_count = None, 0
        out.append(state)
    return out


def compute_labels(df: pd.DataFrame, warmup_bars: int = WARMUP_BARS,
                   buffer_bars: int = TRANSITION_BUFFER_BARS,
                   sma_slow_bars: int = SMA_SLOW_BARS,
                   adx_threshold: float = ADX_TREND_THRESHOLD,
                   adx_margin: float = ADX_MARGIN) -> pd.DataFrame:
    """df indexed by bar-open UTC timestamps with columns open/high/low/close.
    Returns df plus indicator columns, raw label and final STATE label."""
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    close = df["close"].to_numpy(float)
    adx, dip, dim = adx_di(high, low, close, ADX_PERIOD)
    sma_slow = pd.Series(close).rolling(sma_slow_bars).mean().to_numpy()
    raw = raw_labels(close, adx, dip, dim, sma_slow, warmup_bars,
                     adx_threshold, adx_margin)
    state = state_labels(raw, buffer_bars)
    out = df.copy()
    out["adx"] = adx
    out["di_plus"] = dip
    out["di_minus"] = dim
    out["sma_slow"] = sma_slow
    out["raw_label"] = raw
    out["state_label"] = state
    return out
