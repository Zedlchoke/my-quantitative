"""Trend pullback/retest baseline for markup and markdown legs."""

from __future__ import annotations

from nautilus_trader.config import PositiveInt
from nautilus_trader.indicators import AverageTrueRange
from nautilus_trader.indicators import ExponentialMovingAverage
from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import PositionSide
from nautilus_trader.model.events import PositionClosed
from nautilus_trader.model.events import PositionOpened

from regime import AverageDirectionalIndex
from regime import VolumeSMA
from regime_wyckoff import WyckoffDailyTracker
from regime_wyckoff import WyckoffPhase
from strategy_base import BaseFuturesStrategy
from strategy_base import BaseFuturesStrategyConfig


class TrendPullbackStrategyConfig(BaseFuturesStrategyConfig, frozen=True):
    fast_ema_period: PositiveInt = 20
    slow_ema_period: PositiveInt = 50
    trend_ema_period: PositiveInt = 200
    adx_period: PositiveInt = 14
    adx_min: float = 20.0
    volume_sma_period: PositiveInt = 20
    volume_min_ratio: float = 0.8
    phase_gate: bool = True


class TrendPullbackStrategy(BaseFuturesStrategy):
    """Enter after a pullback reclaims the fast EMA inside a directional phase."""

    def __init__(self, config: TrendPullbackStrategyConfig) -> None:
        if not config.fast_ema_period < config.slow_ema_period < config.trend_ema_period:
            raise ValueError("EMA periods must satisfy fast < slow < trend")
        if config.adx_min <= 0 or config.volume_min_ratio <= 0:
            raise ValueError("ADX and volume thresholds must be positive")
        if config.atr_stop_multiple <= 0:
            raise ValueError("atr_stop_multiple must be positive")
        super().__init__(config)

        self.fast = ExponentialMovingAverage(config.fast_ema_period)
        self.slow = ExponentialMovingAverage(config.slow_ema_period)
        self.trend = ExponentialMovingAverage(config.trend_ema_period)
        self.atr = AverageTrueRange(config.atr_period)
        self.adx = AverageDirectionalIndex(config.adx_period)
        self.volume_sma = VolumeSMA(config.volume_sma_period)
        self.wyckoff = WyckoffDailyTracker() if config.phase_gate else None
        self.phase = WyckoffPhase.TRANSITION
        self.previous_close: float | None = None
        self.previous_fast: float | None = None
        self.entry_price: float | None = None
        self.extreme_price: float | None = None
        self.trailing_stop: float | None = None

    def indicators(self) -> list:
        return [self.fast, self.slow, self.trend, self.atr]

    def on_bar(self, bar: Bar) -> None:
        self._roll_trading_day()
        self.daily.tick_cooldown()
        self.adx.update_bar(bar)
        self.volume_sma.update_bar(bar)
        if self.wyckoff is not None:
            self.phase = self.wyckoff.update_bar(bar)
        if not self.indicators_initialized() or not self.adx.initialized:
            return

        close = bar.close.as_double()
        atr = self.atr.value
        if self.portfolio.is_net_long(self.config.instrument_id):
            self._manage_long(bar, close, atr)
        elif self.portfolio.is_net_short(self.config.instrument_id):
            self._manage_short(bar, close, atr)
        elif self._can_open_position() and not self._has_active_order():
            if self._volume_ok(bar) and self._reclaim_up(close) and self._long_context():
                self._submit_entry(OrderSide.BUY, close, atr)
            elif self.config.allow_short and self._volume_ok(bar) and self._reclaim_down(close):
                if self._short_context():
                    self._submit_entry(OrderSide.SELL, close, atr)

        self.previous_close = close
        self.previous_fast = self.fast.value

    def _volume_ok(self, bar: Bar) -> bool:
        return (
            self.volume_sma.value > 0
            and bar.volume.as_double() >= self.volume_sma.value * self.config.volume_min_ratio
        )

    def _reclaim_up(self, close: float) -> bool:
        return (
            self.previous_close is not None
            and self.previous_fast is not None
            and self.previous_close <= self.previous_fast
            and close > self.fast.value
        )

    def _reclaim_down(self, close: float) -> bool:
        return (
            self.previous_close is not None
            and self.previous_fast is not None
            and self.previous_close >= self.previous_fast
            and close < self.fast.value
        )

    def _long_context(self) -> bool:
        if not self.fast.value > self.slow.value > self.trend.value:
            return False
        if self.wyckoff is None or not self.wyckoff.initialized:
            return True
        return self.phase in {WyckoffPhase.MARKUP, WyckoffPhase.TRANSITION}

    def _short_context(self) -> bool:
        if not self.fast.value < self.slow.value < self.trend.value:
            return False
        if self.wyckoff is None or not self.wyckoff.initialized:
            return True
        return self.phase in {WyckoffPhase.MARKDOWN, WyckoffPhase.TRANSITION}

    def _manage_long(self, bar: Bar, close: float, atr: float) -> None:
        if self._has_active_order():
            return
        self._update_long_stop(bar.high.as_double(), close, atr)
        if self.trailing_stop is not None and close <= self.trailing_stop:
            self._submit_exit("ATR trailing stop", close)

    def _manage_short(self, bar: Bar, close: float, atr: float) -> None:
        if self._has_active_order():
            return
        self._update_short_stop(bar.low.as_double(), close, atr)
        if self.trailing_stop is not None and close >= self.trailing_stop:
            self._submit_exit("ATR trailing stop", close)

    def _update_long_stop(self, high: float, close: float, atr: float) -> None:
        self.extreme_price = max(self.extreme_price or high, high)
        entry = self.entry_price or close
        initial = entry - atr * self.config.atr_stop_multiple
        candidate = self.extreme_price - atr * self.config.atr_stop_multiple
        self.trailing_stop = max(self.trailing_stop or initial, candidate)

    def _update_short_stop(self, low: float, close: float, atr: float) -> None:
        self.extreme_price = min(self.extreme_price or low, low)
        entry = self.entry_price or close
        initial = entry + atr * self.config.atr_stop_multiple
        candidate = self.extreme_price + atr * self.config.atr_stop_multiple
        self.trailing_stop = min(self.trailing_stop or initial, candidate)

    def _on_position_opened(self, event: PositionOpened) -> None:
        self.entry_price = float(event.avg_px_open)
        self.extreme_price = self.entry_price
        if event.side == PositionSide.LONG:
            self.trailing_stop = self.entry_price - self.atr.value * self.config.atr_stop_multiple
        else:
            self.trailing_stop = self.entry_price + self.atr.value * self.config.atr_stop_multiple

    def _on_position_closed(self, event: PositionClosed) -> None:
        self.entry_price = None
        self.extreme_price = None
        self.trailing_stop = None

    def _on_reset(self) -> None:
        self.adx.reset()
        self.volume_sma.reset()
        if self.wyckoff is not None:
            self.wyckoff.reset()
        self.phase = WyckoffPhase.TRANSITION
        self.previous_close = None
        self.previous_fast = None
        self.entry_price = None
        self.extreme_price = None
        self.trailing_stop = None
