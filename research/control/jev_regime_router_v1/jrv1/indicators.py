"""Indicator primitives (deterministic, strictly trailing, numpy only).

Conventions (pinned here, hand-computed in tests):
- EMA(n): recursive EMA with alpha = 2/(n+1), seeded with the FIRST close
  (fully causal; value defined from index 0).
- Wilder ATR(n): TR_0 = high-low; TR_t = max(h-l, |h-c_{t-1}|, |l-c_{t-1}|.
  ATR = SMA of the first n TRs (index n-1), then Wilder recursion
  atr = (prev*(n-1) + TR)/n. NaN before initialization. Matches the repo
  ancestry Wilder smoothing used by regime.py.
- Wilder ADX(n): ancestry regime.py AverageDirectionalIndex exactly: seed on
  the first bar; accumulate raw TR/+DM/-DM sums for the first n updatable
  bars (first DX on the n-th updatable bar); DX seed = running SUM of the
  first n DX values then ADX = sum/n; afterwards ADX = (prev*(n-1)+DX)/n.
  NaN until initialized (first value at bar index 2n-1).
- RSI(n): Wilder: first avg gain/loss = simple means of the first n moves
  (from index 1), then smoothed; RSI = 100 - 100/(1+rs); rs = inf-safe;
  RSI defined from index n.
- BOLL(n, k): SMA(n) +/- k * population std (ddof=0), defined from index n-1.
"""

from __future__ import annotations

import numpy as np


def ema(x: np.ndarray, period: int) -> np.ndarray:
    """Recursive EMA seeded with x[0]; defined for all indices."""
    x = np.asarray(x, dtype=np.float64)
    alpha = 2.0 / (period + 1.0)
    out = np.empty_like(x)
    prev = x[0]
    out[0] = prev
    for i in range(1, len(x)):
        prev = prev + alpha * (x[i] - prev)
        out[i] = prev
    return out


def true_range(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    tr = np.empty(len(high), dtype=np.float64)
    tr[0] = high[0] - low[0]
    for i in range(1, len(high)):
        tr[i] = max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1]),
        )
    return tr


def wilder_smooth(x: np.ndarray, period: int) -> np.ndarray:
    """Wilder smoothing: SMA seed of first `period` values, then recursion.

    Returns NaN for the first period-1 indices; value at index period-1 is
    the seed mean.
    """
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    out = np.full(n, np.nan)
    if n < period:
        return out
    acc = float(np.sum(x[:period]))
    out[period - 1] = acc / period
    for i in range(period, n):
        acc = acc - acc / period + x[i]
        out[i] = acc / period
    return out


def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    return wilder_smooth(true_range(high, low, close), period)


def adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """Wilder ADX matching repo regime.py AverageDirectionalIndex semantics."""
    n = period
    N = len(high)
    out = np.full(N, np.nan)
    if N < 2 * n:
        return out
    prev_h = high[0]
    prev_l = low[0]
    prev_c = close[0]
    sum_tr = 0.0
    sum_pdm = 0.0
    sum_mdm = 0.0
    seed_count = 0
    dx_count = 0
    dx_sum = 0.0
    adx_val = 0.0
    for i in range(1, N):
        up = high[i] - prev_h
        dn = prev_l - low[i]
        pdm = up if (up > dn and up > 0) else 0.0
        mdm = dn if (dn > up and dn > 0) else 0.0
        tr = max(high[i] - low[i], abs(high[i] - prev_c), abs(low[i] - prev_c))
        prev_h, prev_l, prev_c = high[i], low[i], close[i]

        if seed_count < n:
            sum_tr += tr
            sum_pdm += pdm
            sum_mdm += mdm
            seed_count += 1
            if seed_count < n:
                continue
        else:
            sum_tr = sum_tr - sum_tr / n + tr
            sum_pdm = sum_pdm - sum_pdm / n + pdm
            sum_mdm = sum_mdm - sum_mdm / n + mdm

        if sum_tr <= 0:
            continue
        plus_di = 100.0 * sum_pdm / sum_tr
        minus_di = 100.0 * sum_mdm / sum_tr
        denom = plus_di + minus_di
        dx = 0.0 if denom <= 0 else 100.0 * abs(plus_di - minus_di) / denom

        if dx_count < n:
            dx_sum += dx
            dx_count += 1
            if dx_count == n:
                adx_val = dx_sum / n
                out[i] = adx_val
            continue
        adx_val = (adx_val * (n - 1) + dx) / n
        out[i] = adx_val
    return out


def rsi(close: np.ndarray, period: int = 14) -> np.ndarray:
    """Wilder RSI; NaN before index `period`."""
    N = len(close)
    out = np.full(N, np.nan)
    if N <= period:
        return out
    gains = np.zeros(N)
    losses = np.zeros(N)
    for i in range(1, N):
        d = close[i] - close[i - 1]
        gains[i] = d if d > 0 else 0.0
        losses[i] = -d if d < 0 else 0.0
    avg_gain = float(np.sum(gains[1 : period + 1])) / period
    avg_loss = float(np.sum(losses[1 : period + 1])) / period

    def _val(g: float, l: float) -> float:
        if l <= 0:
            return 100.0 if g > 0 else 50.0
        rs = g / l
        return 100.0 - 100.0 / (1.0 + rs)

    out[period] = _val(avg_gain, avg_loss)
    for i in range(period + 1, N):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        out[i] = _val(avg_gain, avg_loss)
    return out


def bollinger(close: np.ndarray, period: int = 20, k: float = 2.0):
    """SMA(period) and bands SMA +/- k*population-std; NaN before period-1."""
    N = len(close)
    mid = np.full(N, np.nan)
    upper = np.full(N, np.nan)
    lower = np.full(N, np.nan)
    if N < period:
        return mid, upper, lower
    csum = 0.0
    csq = 0.0
    for i in range(N):
        csum += close[i]
        csq += close[i] * close[i]
        if i >= period:
            csum -= close[i - period]
            csq -= close[i - period] * close[i - period]
        if i >= period - 1:
            m = csum / period
            var = max(csq / period - m * m, 0.0)
            sd = var**0.5
            mid[i] = m
            upper[i] = m + k * sd
            lower[i] = m - k * sd
    return mid, upper, lower


def sma(x: np.ndarray, period: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if len(x) < period:
        return out
    c = np.cumsum(np.insert(np.asarray(x, dtype=np.float64), 0, 0.0))
    out[period - 1 :] = (c[period:] - c[:-period]) / period
    return out
