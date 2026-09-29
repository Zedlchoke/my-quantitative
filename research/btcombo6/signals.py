"""Per-leg decision frames — frozen cross/state-change rules, no lookahead.

decision_ts convention (PIT, unified across clocks):
  decision_ts = open time of the LAST 5m bar of the decision bar
  (for the 5m clock: the bar itself). The decision is knowable at that bar's
  close (= decision_ts + 5min); the engine fills at the first 5m bar with
  open_time >= decision_ts + 5min.

Indicator conventions (plan §1):
- SMA legs: SMAs are TIME windows on the 5m close master reindexed to the
  full UTC 5m grid (min_periods=window -> NaN whenever any slot in the
  trailing window is missing -> signal ineligible), sampled at the leg's
  complete-bucket decision closes.
- Cross rule: prev <= 0 AND cur > 0 on consecutive emitted bars of the
  decision clock (absent buckets are skipped); NaN on either side -> no
  signal.
- LEG-1 momentum: state-change false->true of (close/close[-48 5m bars] - 1
  >= +1%) evaluated at 5m closes; NaN on either side -> no signal.
- LEG-5 RSI: Wilder RSI (TA-Lib seed convention), periods are bar-counts on
  the emitted 15m close series.
"""
from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from . import data, spec

_TS_NS = "datetime64[ns, UTC]"


def wilder_rsi(close: np.ndarray, period: int) -> np.ndarray:
    """Wilder RSI with the TA-Lib seed convention.

    avg_gain/avg_loss seeded with the simple mean of the first `period`
    deltas, then smoothed recursively (avg = (prev*(n-1) + cur)/n).
    First valid value at index `period`. avg_loss == 0 -> RSI 100.
    """
    n = len(close)
    out = np.full(n, np.nan)
    if n <= period:
        return out
    delta = np.diff(close)                      # len n-1, delta[i] = c[i+1]-c[i]
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_gain = float(np.mean(gain[:period]))
    avg_loss = float(np.mean(loss[:period]))
    out[period] = _rsi_from(avg_gain, avg_loss)
    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gain[i - 1]) / period
        avg_loss = (avg_loss * (period - 1) + loss[i - 1]) / period
        out[i] = _rsi_from(avg_gain, avg_loss)
    return out


def _rsi_from(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0.0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def _grid_close(m5: pd.DataFrame) -> pd.Series:
    """5m closes reindexed to the full UTC 5m grid (missing slots -> NaN)."""
    ts = m5["ts"]
    idx = pd.date_range(start=ts.iloc[0], end=ts.iloc[-1], freq="5min")
    s = m5.set_index("ts")["c"].reindex(idx)
    s.index.name = "ts"
    return s


def _decisions_from(decision_ts: pd.Series, enter: np.ndarray) -> pd.DataFrame:
    dts = pd.to_datetime(pd.Series(decision_ts).reset_index(drop=True), utc=True)
    out = pd.DataFrame({"decision_ts": dts.astype(_TS_NS),
                        "enter": enter.astype(bool)})
    return out.sort_values("decision_ts", kind="mergesort").reset_index(drop=True)


def _momentum_decisions(leg: dict, m5: pd.DataFrame) -> pd.DataFrame:
    c = _grid_close(m5)
    mom = c / c.shift(leg["mom_bars"]) - 1.0
    present = c.notna()
    cond = mom >= leg["mom_threshold"]           # NaN -> False
    prev_cond = cond.shift(1, fill_value=False)
    eligible = mom.notna() & mom.shift(1).notna()
    enter = (present & cond & ~prev_cond & eligible).to_numpy()
    return _decisions_from(pd.Series(c.index), enter)


def _sma_spread_decisions(leg: dict, m5: pd.DataFrame) -> pd.DataFrame:
    c = _grid_close(m5)
    fast = c.rolling(leg["fast_bars"], min_periods=leg["fast_bars"]).mean()
    slow = c.rolling(leg["slow_bars"], min_periods=leg["slow_bars"]).mean()
    spread = fast - slow
    rule = spec.CLOCK_PANDAS_RULE[leg["clock"]]
    agg = data.aggregate(m5, rule)
    # decision close = bucket close; sample the spread at the grid slot of the
    # bucket's last constituent 5m bar (open = bucket_close - 5min).
    decision_ts = agg["ts"] + spec.CLOCK_TD[leg["clock"]] - pd.Timedelta(minutes=5)
    sampled = spread.loc[decision_ts.to_numpy()].to_numpy()
    s = pd.Series(sampled)
    prev = s.shift(1)
    enter = ((prev <= 0) & (s > 0) & prev.notna() & s.notna()).to_numpy()
    return _decisions_from(decision_ts, enter)


def _rsi_decisions(leg: dict, m5: pd.DataFrame) -> pd.DataFrame:
    agg = data.aggregate(m5, "15min")
    cl = agg["c"].to_numpy(dtype=float)
    fast = wilder_rsi(cl, leg["rsi_fast"])
    slow = wilder_rsi(cl, leg["rsi_slow"])
    diff = pd.Series(fast - slow)
    prev = diff.shift(1)
    enter = ((prev <= 0) & (diff > 0) & prev.notna() & diff.notna()).to_numpy()
    decision_ts = agg["ts"] + pd.Timedelta(minutes=15) - pd.Timedelta(minutes=5)
    return _decisions_from(decision_ts, enter)


_BUILDERS = {
    "momentum_state_change": _momentum_decisions,
    "sma_spread_cross": _sma_spread_decisions,
    "rsi_cross": _rsi_decisions,
}


def leg_decisions(leg_id: str, m5: pd.DataFrame,
                  eval_end=None) -> pd.DataFrame:
    """Decision frame [decision_ts, enter] for one leg, truncated to
    decision_ts < eval_end (sealed tail never produces decisions)."""
    leg = spec.LEGS[leg_id]
    frame = _BUILDERS[leg["rule"]](leg, m5)
    if eval_end is None:
        eval_end = spec.EVAL_END
    frame = frame[frame["decision_ts"] < pd.Timestamp(eval_end)]
    return frame.reset_index(drop=True)


def signal_digest(decisions: pd.DataFrame) -> str:
    """sha256 over decision frames: int64 epoch-seconds (little endian) of
    decision_ts concatenated with uint8 enter flags. Deterministic bytes."""
    ts_ns = decisions["decision_ts"].to_numpy(dtype="datetime64[ns]").astype("int64")
    secs = (ts_ns // 1_000_000_000).astype("<i8").tobytes()
    flags = decisions["enter"].to_numpy().astype(np.uint8).tobytes()
    return hashlib.sha256(b"btcombo6/signal_digest@1" + secs + flags).hexdigest()
