"""Frozen anchor strategies on the EXECUTION clock (mapping_arms_freeze).

V2 note: strategies are IDENTICAL frozen specs carried over from V1
(jrv2 carries the same math byte-for-byte; only the docstring differs).

TREND_LONG  entry close>EMA20 and EMA20>EMA50 (flat) — exec clock
            exit   close<EMA20 | intrabar stop entry-3*ATR14 |
                   regime off | fold force-flat
TREND_SHORT mirror (BTC only; stop entry+3*ATR14)
MR_LONG     entry RSI14<30 and close<BOLL(20,2.0) lower (flat)
            exit   close>=BOLL mid | RSI14>55 | 96 exec bars max hold |
                   intrabar stop entry-2*ATR14 | regime off | fold force-flat

Signals are evaluated on a COMPLETED exec bar and filled at the NEXT exec
bar open (PIT law). Indicators are computed once per instrument.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import indicators as ind
from .data import Bars

TREND_LONG = "TREND_LONG"
TREND_SHORT = "TREND_SHORT"
MR_LONG = "MR_LONG"
FLAT = "FLAT"

MR_MAX_HOLD_BARS = 96
TREND_STOP_ATR_MULT = 3.0
MR_STOP_ATR_MULT = 2.0


@dataclass
class ExecIndicators:
    ema20: np.ndarray
    ema50: np.ndarray
    atr14: np.ndarray
    rsi14: np.ndarray
    boll_mid: np.ndarray
    boll_upper: np.ndarray
    boll_lower: np.ndarray


def exec_indicators(bars: Bars) -> ExecIndicators:
    close = bars.close
    mid, upper, lower = ind.bollinger(close, 20, 2.0)
    return ExecIndicators(
        ema20=ind.ema(close, 20),
        ema50=ind.ema(close, 50),
        atr14=ind.atr(bars.high, bars.low, close, 14),
        rsi14=ind.rsi(close, 14),
        boll_mid=mid,
        boll_upper=upper,
        boll_lower=lower,
    )


def trend_long_entry(i: int, bars: Bars, x: ExecIndicators) -> bool:
    return (
        np.isfinite(x.ema20[i])
        and np.isfinite(x.ema50[i])
        and bars.close[i] > x.ema20[i]
        and x.ema20[i] > x.ema50[i]
    )


def trend_long_exit(i: int, bars: Bars, x: ExecIndicators) -> bool:
    return np.isfinite(x.ema20[i]) and bars.close[i] < x.ema20[i]


def trend_short_entry(i: int, bars: Bars, x: ExecIndicators) -> bool:
    return (
        np.isfinite(x.ema20[i])
        and np.isfinite(x.ema50[i])
        and bars.close[i] < x.ema20[i]
        and x.ema20[i] < x.ema50[i]
    )


def trend_short_exit(i: int, bars: Bars, x: ExecIndicators) -> bool:
    return np.isfinite(x.ema20[i]) and bars.close[i] > x.ema20[i]


def mr_long_entry(i: int, bars: Bars, x: ExecIndicators) -> bool:
    return (
        np.isfinite(x.rsi14[i])
        and np.isfinite(x.boll_lower[i])
        and x.rsi14[i] < 30.0
        and bars.close[i] < x.boll_lower[i]
    )


def mr_long_exit(i: int, bars: Bars, x: ExecIndicators, bars_held: int) -> bool:
    if bars_held >= MR_MAX_HOLD_BARS:
        return True
    if np.isfinite(x.rsi14[i]) and x.rsi14[i] > 55.0:
        return True
    if np.isfinite(x.boll_mid[i]) and bars.close[i] >= x.boll_mid[i]:
        return True
    return False


def stop_price(strategy: str, entry_px: float, atr_at_entry: float) -> float:
    """Stop level for the strategy; NaN (disabled) until ATR is available."""
    if not np.isfinite(atr_at_entry) or atr_at_entry <= 0:
        return float("nan")
    if strategy == TREND_LONG:
        return entry_px - TREND_STOP_ATR_MULT * atr_at_entry
    if strategy == TREND_SHORT:
        return entry_px + TREND_STOP_ATR_MULT * atr_at_entry
    if strategy == MR_LONG:
        return entry_px - MR_STOP_ATR_MULT * atr_at_entry
    raise ValueError(strategy)


def stop_hit(strategy: str, high: float, low: float, stop: float) -> bool:
    if not np.isfinite(stop):
        return False  # stop disabled until ATR initializes (fail-safe hold)
    if strategy in (TREND_LONG, MR_LONG):
        return low <= stop
    if strategy == TREND_SHORT:
        return high >= stop
    raise ValueError(strategy)
