"""Regime classification used by mean-reversion and regime-switch strategies.

NOTES.md: VHF alone did not keep mean-reversion out of trends (ETH had two
consecutive losing folds). Range entries therefore require **all three**:

- VHF low  (not a directional range expansion)
- ADX low  (trend strength is weak)
- volume not elevated vs its SMA (breakouts often print a volume spike)
"""

from __future__ import annotations

from collections import deque


class AverageDirectionalIndex:
    """Wilder ADX. ``value`` is trend *strength* on 0–100 (direction-agnostic)."""

    def __init__(self, period: int = 14) -> None:
        if period <= 0:
            raise ValueError("period must be > 0")
        self.period = period
        self.value = 0.0
        self.initialized = False
        self._prev_high: float | None = None
        self._prev_low: float | None = None
        self._prev_close: float | None = None
        self._atr = 0.0
        self._plus_dm = 0.0
        self._minus_dm = 0.0
        self._adx = 0.0
        self._dx_count = 0
        self._seed_count = 0

    def reset(self) -> None:
        self.value = 0.0
        self.initialized = False
        self._prev_high = None
        self._prev_low = None
        self._prev_close = None
        self._atr = 0.0
        self._plus_dm = 0.0
        self._minus_dm = 0.0
        self._adx = 0.0
        self._dx_count = 0
        self._seed_count = 0

    def update_bar(self, bar) -> None:
        self.update(
            high=bar.high.as_double(),
            low=bar.low.as_double(),
            close=bar.close.as_double(),
        )

    def update(self, high: float, low: float, close: float) -> None:
        if self._prev_high is None or self._prev_low is None or self._prev_close is None:
            self._prev_high = high
            self._prev_low = low
            self._prev_close = close
            return

        up_move = high - self._prev_high
        down_move = self._prev_low - low
        plus_dm = up_move if up_move > down_move and up_move > 0 else 0.0
        minus_dm = down_move if down_move > up_move and down_move > 0 else 0.0
        tr = max(
            high - low,
            abs(high - self._prev_close),
            abs(low - self._prev_close),
        )

        n = self.period
        self._prev_high = high
        self._prev_low = low
        self._prev_close = close

        if self._seed_count < n:
            self._atr += tr
            self._plus_dm += plus_dm
            self._minus_dm += minus_dm
            self._seed_count += 1
            if self._seed_count < n:
                return
        else:
            self._atr = self._atr - (self._atr / n) + tr
            self._plus_dm = self._plus_dm - (self._plus_dm / n) + plus_dm
            self._minus_dm = self._minus_dm - (self._minus_dm / n) + minus_dm

        if self._atr <= 0:
            return

        plus_di = 100.0 * self._plus_dm / self._atr
        minus_di = 100.0 * self._minus_dm / self._atr
        denom = plus_di + minus_di
        dx = 0.0 if denom <= 0 else 100.0 * abs(plus_di - minus_di) / denom

        if self._dx_count < n:
            self._adx += dx
            self._dx_count += 1
            if self._dx_count == n:
                self._adx /= n
                self.value = self._adx
                self.initialized = True
            return

        self._adx = (self._adx * (n - 1) + dx) / n
        self.value = self._adx
        self.initialized = True


class VolumeSMA:
    """Simple moving average of bar volume (breakout / participation filter)."""

    def __init__(self, period: int = 20) -> None:
        if period <= 0:
            raise ValueError("period must be > 0")
        self.period = period
        self._window: deque[float] = deque(maxlen=period)
        self.value = 0.0
        self.initialized = False

    def reset(self) -> None:
        self._window.clear()
        self.value = 0.0
        self.initialized = False

    def update_bar(self, bar) -> None:
        self.update(bar.volume.as_double())

    def update(self, volume: float) -> None:
        self._window.append(volume)
        self.value = sum(self._window) / len(self._window)
        self.initialized = len(self._window) >= self.period


def is_ranging(
    *,
    vhf: float,
    vhf_max: float,
    adx: float,
    adx_max: float,
    volume: float,
    volume_sma: float,
    volume_max_ratio: float,
) -> bool:
    """True only when VHF, ADX and volume all say 'range', not trend/breakout."""
    if vhf > vhf_max:
        return False
    if adx > adx_max:
        return False
    if volume_sma > 0 and volume > volume_sma * volume_max_ratio:
        return False
    return True


class HtfTrendTracker:
    """Higher-timeframe EMA trend filter built from lower-timeframe closes.

    Aggregates ``base_minutes`` bars into ``htf_minutes`` candles (e.g. 15m → 1h)
    and tracks an EMA. Mean-reversion longs are blocked below the EMA; shorts
    above it — avoids catching knives in bear trends (NOTES.md fold F1/F2).
    """

    def __init__(
        self,
        *,
        base_minutes: int = 15,
        htf_minutes: int = 60,
        ema_period: int = 200,
    ) -> None:
        if htf_minutes <= base_minutes or htf_minutes % base_minutes != 0:
            raise ValueError("htf_minutes must be a whole multiple of base_minutes")
        self._bars_per_htf = htf_minutes // base_minutes
        self._ema_period = ema_period
        self._htf_count = 0
        self._bar_in_bucket = 0
        self._bucket_close: float | None = None
        self.ema: float | None = None
        self.last_htf_close: float | None = None
        self.initialized = False

    def reset(self) -> None:
        self._htf_count = 0
        self._bar_in_bucket = 0
        self._bucket_close = None
        self.ema = None
        self.last_htf_close = None
        self.initialized = False

    def update(self, close: float) -> None:
        self._bucket_close = close
        self._bar_in_bucket += 1
        if self._bar_in_bucket < self._bars_per_htf:
            return
        self._bar_in_bucket = 0
        self.last_htf_close = self._bucket_close
        self._htf_count += 1
        if self.ema is None:
            self.ema = self.last_htf_close
        else:
            k = 2.0 / (self._ema_period + 1)
            self.ema = self.last_htf_close * k + self.ema * (1 - k)
        self.initialized = self._htf_count >= self._ema_period

    def allows_long(self) -> bool:
        if not self.initialized or self.ema is None or self.last_htf_close is None:
            return True
        return self.last_htf_close >= self.ema

    def allows_short(self) -> bool:
        if not self.initialized or self.ema is None or self.last_htf_close is None:
            return True
        return self.last_htf_close <= self.ema
