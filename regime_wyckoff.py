"""Wyckoff market-cycle regime classification (accumulation → markup → distribution → markdown).

Design goals (anti-overfitting)
-------------------------------
- **Fixed thresholds** from standard TA (ADX 25, EMA50/200 structure) — not tuned on ETH.
- Classify on **daily** bars resampled from 15m — less noise than intraday rules.
- ``TRANSITION`` when no phase is clear — default to reduced risk, not forced labels.
- Policy table is **hand-crafted** from phase economics, not optimized on backtest PnL.

This is a *descriptive* framework for research and live risk scaling, not a curve-fit
signal generator.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import date
from datetime import datetime
from enum import Enum


class WyckoffPhase(str, Enum):
    ACCUMULATION = "accumulation"
    MARKUP = "markup"
    DISTRIBUTION = "distribution"
    MARKDOWN = "markdown"
    TRANSITION = "transition"


@dataclass(frozen=True)
class WyckoffConfig:
    """Fixed, literature-style thresholds — do not optimize on one symbol."""

    range_lookback_days: int = 60
    return_lookback_days: int = 20
    ema_fast: int = 50
    ema_slow: int = 200
    adx_period: int = 14
    # Trend legs: require meaningful drift (≈ one month move on crypto daily).
    markup_min_return_pct: float = 6.0
    markdown_max_return_pct: float = -6.0
    # Range legs: price position in N-day range (0 = low, 1 = high).
    accumulation_range_max: float = 0.35
    distribution_range_min: float = 0.65
    # Range legs: trend strength must be weak (classic ADX range gate).
    range_adx_max: float = 25.0
    # Range legs: not already in a strong drift.
    range_max_abs_return_pct: float = 5.0


@dataclass(frozen=True)
class WyckoffPolicy:
    """Recommended strategy + risk per phase (conservative defaults)."""

    phase: WyckoffPhase
    strategy: str
    risk_pct: float
    notes: str


DEFAULT_POLICIES: dict[WyckoffPhase, WyckoffPolicy] = {
    WyckoffPhase.ACCUMULATION: WyckoffPolicy(
        phase=WyckoffPhase.ACCUMULATION,
        strategy="mean_reversion_long_bias",
        risk_pct=0.75,
        notes="Range at lows; MR long OK, avoid shorts, HTF filter relaxed for longs only.",
    ),
    WyckoffPhase.MARKUP: WyckoffPolicy(
        phase=WyckoffPhase.MARKUP,
        strategy="trend_follow_or_flat",
        risk_pct=0.5,
        notes="MR shorts dangerous; prefer ema_atr long or sit out MR entirely.",
    ),
    WyckoffPhase.DISTRIBUTION: WyckoffPolicy(
        phase=WyckoffPhase.DISTRIBUTION,
        strategy="mean_reversion_short_bias",
        risk_pct=0.75,
        notes="Range at highs; MR short OK, avoid longs, tight stops.",
    ),
    WyckoffPhase.MARKDOWN: WyckoffPolicy(
        phase=WyckoffPhase.MARKDOWN,
        strategy="flat_or_trend_short",
        risk_pct=0.25,
        notes="No MR long; circuit breaker active; ema short only if enabled.",
    ),
    WyckoffPhase.TRANSITION: WyckoffPolicy(
        phase=WyckoffPhase.TRANSITION,
        strategy="reduced_mr_or_flat",
        risk_pct=0.5,
        notes="Unclear phase — half size, stricter filters, prefer signal-only.",
    ),
}


def classify_wyckoff_row(
    *,
    close: float,
    ema_fast: float,
    ema_slow: float,
    return_pct: float,
    range_position: float,
    adx: float,
    cfg: WyckoffConfig | None = None,
) -> WyckoffPhase:
    """Classify one daily bar into a Wyckoff phase.

    Priority: strong trend legs (markup/markdown) before range legs (accumulation/
    distribution) so crash/rally phases are not mislabeled as range.
    """
    c = cfg or WyckoffConfig()

    above_slow = close > ema_slow
    below_slow = close < ema_slow
    fast_above_slow = ema_fast > ema_slow
    fast_below_slow = ema_fast < ema_slow

    if (
        return_pct <= c.markdown_max_return_pct
        and below_slow
        and fast_below_slow
    ):
        return WyckoffPhase.MARKDOWN

    if (
        return_pct >= c.markup_min_return_pct
        and above_slow
        and fast_above_slow
    ):
        return WyckoffPhase.MARKUP

    if (
        range_position <= c.accumulation_range_max
        and adx <= c.range_adx_max
        and abs(return_pct) <= c.range_max_abs_return_pct
    ):
        return WyckoffPhase.ACCUMULATION

    if (
        range_position >= c.distribution_range_min
        and adx <= c.range_adx_max
        and abs(return_pct) <= c.range_max_abs_return_pct
        and above_slow
    ):
        return WyckoffPhase.DISTRIBUTION

    return WyckoffPhase.TRANSITION


@dataclass
class _DailyOhlcv:
    day: date
    open: float
    high: float
    low: float
    close: float
    volume: float


def _ema_series(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    k = 2.0 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def _wilder_adx_daily(highs: list[float], lows: list[float], closes: list[float], period: int) -> float:
    if len(closes) < period + 2:
        return 0.0
    adx_vals: list[float] = []
    atr = 0.0
    plus_dm_s = 0.0
    minus_dm_s = 0.0
    prev_high = highs[0]
    prev_low = lows[0]
    prev_close = closes[0]
    for i in range(1, len(closes)):
        high, low, close = highs[i], lows[i], closes[i]
        up = high - prev_high
        down = prev_low - low
        plus_dm = up if up > down and up > 0 else 0.0
        minus_dm = down if down > up and down > 0 else 0.0
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        if i <= period:
            atr += tr
            plus_dm_s += plus_dm
            minus_dm_s += minus_dm
            if i == period:
                atr /= period
                plus_dm_s /= period
                minus_dm_s /= period
                plus_di = 100 * plus_dm_s / atr if atr else 0
                minus_di = 100 * minus_dm_s / atr if atr else 0
                denom = plus_di + minus_di
                dx = 100 * abs(plus_di - minus_di) / denom if denom else 0
                adx_vals.append(dx)
        else:
            atr = atr - atr / period + tr
            plus_dm_s = plus_dm_s - plus_dm_s / period + plus_dm
            minus_dm_s = minus_dm_s - minus_dm_s / period + minus_dm
            plus_di = 100 * plus_dm_s / atr if atr else 0
            minus_di = 100 * minus_dm_s / atr if atr else 0
            denom = plus_di + minus_di
            dx = 100 * abs(plus_di - minus_di) / denom if denom else 0
            if len(adx_vals) < period:
                adx_vals.append(dx)
            else:
                adx = (adx_vals[-1] * (period - 1) + dx) / period if adx_vals else dx
                adx_vals.append(adx)
        prev_high, prev_low, prev_close = high, low, close
    return adx_vals[-1] if adx_vals else 0.0


def wyckoff_risk_scale(phase: WyckoffPhase) -> float:
    """Hand-crafted risk multiplier per phase (not optimized on backtest PnL)."""
    if phase == WyckoffPhase.MARKDOWN:
        return 0.0
    if phase == WyckoffPhase.TRANSITION:
        return DEFAULT_POLICIES[WyckoffPhase.TRANSITION].risk_pct / 1.0
    return 1.0


def wyckoff_allows_entries(phase: WyckoffPhase) -> bool:
    """Block new MR entries in markdown; manage open positions elsewhere."""
    return phase != WyckoffPhase.MARKDOWN


def wyckoff_allows_long(phase: WyckoffPhase) -> bool:
    """Phase bias for MR longs (``config/wyckoff_policy.yaml``, not tuned on ETH)."""
    if phase in (WyckoffPhase.MARKDOWN, WyckoffPhase.MARKUP, WyckoffPhase.DISTRIBUTION):
        return False
    return True


def wyckoff_allows_short(phase: WyckoffPhase) -> bool:
    """Phase bias for MR shorts — distribution short-only leg + transition."""
    if phase in (WyckoffPhase.MARKDOWN, WyckoffPhase.MARKUP, WyckoffPhase.ACCUMULATION):
        return False
    return True


class WyckoffDailyTracker:
    """Build daily OHLC from intraday bars and classify Wyckoff phase (UTC days)."""

    def __init__(self, cfg: WyckoffConfig | None = None) -> None:
        self.cfg = cfg or WyckoffConfig()
        self._history: deque[_DailyOhlcv] = deque(maxlen=260)
        self._cur_day: date | None = None
        self._cur_open = 0.0
        self._cur_high = 0.0
        self._cur_low = 0.0
        self._cur_close = 0.0
        self._cur_volume = 0.0
        self.phase = WyckoffPhase.TRANSITION
        self.initialized = False

    def reset(self) -> None:
        self._history.clear()
        self._cur_day = None
        self.phase = WyckoffPhase.TRANSITION
        self.initialized = False

    def update_bar(self, bar) -> WyckoffPhase:
        """Ingest one intraday bar; returns current phase (may update on UTC day roll)."""
        ts = datetime.utcfromtimestamp(bar.ts_event / 1_000_000_000)
        o = bar.open.as_double()
        h = bar.high.as_double()
        l = bar.low.as_double()
        c = bar.close.as_double()
        v = bar.volume.as_double()
        day = ts.date()
        if self._cur_day is None:
            self._start_day(day, o, h, l, c, v)
        elif day != self._cur_day:
            self._finalize_day()
            self._start_day(day, o, h, l, c, v)
        else:
            self._cur_high = max(self._cur_high, h)
            self._cur_low = min(self._cur_low, l)
            self._cur_close = c
            self._cur_volume += v
        return self.phase

    def _start_day(self, day: date, o: float, h: float, l: float, c: float, v: float) -> None:
        self._cur_day = day
        self._cur_open = o
        self._cur_high = h
        self._cur_low = l
        self._cur_close = c
        self._cur_volume = v

    def _finalize_day(self) -> None:
        assert self._cur_day is not None
        self._history.append(
            _DailyOhlcv(
                day=self._cur_day,
                open=self._cur_open,
                high=self._cur_high,
                low=self._cur_low,
                close=self._cur_close,
                volume=self._cur_volume,
            ),
        )
        self._recompute_phase()

    def _recompute_phase(self) -> None:
        c = self.cfg
        min_len = max(c.ema_slow, c.range_lookback_days, c.return_lookback_days) + 5
        if len(self._history) < min_len:
            self.initialized = False
            return

        closes = [b.close for b in self._history]
        highs = [b.high for b in self._history]
        lows = [b.low for b in self._history]
        ema_fast = _ema_series(closes, c.ema_fast)[-1]
        ema_slow = _ema_series(closes, c.ema_slow)[-1]
        ret = (closes[-1] / closes[-1 - c.return_lookback_days] - 1) * 100
        window_low = min(lows[-c.range_lookback_days :])
        window_high = max(highs[-c.range_lookback_days :])
        span = window_high - window_low
        range_pos = (closes[-1] - window_low) / span if span > 0 else 0.5
        adx = _wilder_adx_daily(highs, lows, closes, c.adx_period)

        self.phase = classify_wyckoff_row(
            close=closes[-1],
            ema_fast=ema_fast,
            ema_slow=ema_slow,
            return_pct=ret,
            range_position=range_pos,
            adx=adx,
            cfg=c,
        )
        self.initialized = True

