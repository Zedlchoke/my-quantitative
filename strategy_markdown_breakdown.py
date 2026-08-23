"""Markdown breakdown short baseline."""

from __future__ import annotations

from collections import deque

from nautilus_trader.config import PositiveInt
from nautilus_trader.indicators import AverageTrueRange
from nautilus_trader.indicators import ExponentialMovingAverage
from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.events import PositionClosed
from nautilus_trader.model.events import PositionOpened

from regime import AverageDirectionalIndex
from regime import VolumeSMA
from regime_wyckoff import WyckoffDailyTracker
from regime_wyckoff import WyckoffPhase
from strategy_base import BaseFuturesStrategy
from strategy_base import BaseFuturesStrategyConfig


class MarkdownBreakdownStrategyConfig(BaseFuturesStrategyConfig, frozen=True):
    donchian_period: PositiveInt = 20
    trend_ema_period: PositiveInt = 200
    adx_period: PositiveInt = 14
    adx_min: float = 20.0
    volume_sma_period: PositiveInt = 20
    volume_min_ratio: float = 1.3
    take_profit_multiple: float = 1.5
    phase_gate: bool = True


class MarkdownBreakdownStrategy(BaseFuturesStrategy):
    """Short only after a lower-Donchian breakdown in Wyckoff markdown."""

    def __init__(self, config: MarkdownBreakdownStrategyConfig) -> None:
        if config.donchian_period <= 0 or config.trend_ema_period <= 0:
            raise ValueError("periods must be positive")
        if config.adx_min <= 0 or config.volume_min_ratio <= 0:
            raise ValueError("ADX and volume thresholds must be positive")
        if config.atr_stop_multiple <= 0 or config.take_profit_multiple <= 0:
            raise ValueError("stop and take-profit multiples must be positive")
        super().__init__(config)

        self.trend = ExponentialMovingAverage(config.trend_ema_period)
        self.atr = AverageTrueRange(config.atr_period)
        self.adx = AverageDirectionalIndex(config.adx_period)
        self.volume_sma = VolumeSMA(config.volume_sma_period)
        self.wyckoff = WyckoffDailyTracker() if config.phase_gate else None
        self.phase = WyckoffPhase.TRANSITION
        self.lows: deque[float] = deque(maxlen=config.donchian_period)
        self.entry_price: float | None = None
        self.stop_distance: float | None = None

    def indicators(self) -> list:
        return [self.trend, self.atr]

    def on_bar(self, bar: Bar) -> None:
        self._roll_trading_day()
        self.daily.tick_cooldown()
        self.adx.update_bar(bar)
        self.volume_sma.update_bar(bar)
        if self.wyckoff is not None:
            self.phase = self.wyckoff.update_bar(bar)

        low = bar.low.as_double()
        close = bar.close.as_double()
        prior_lower = min(self.lows) if len(self.lows) >= self.config.donchian_period else None
        self.lows.append(low)
        if not self.indicators_initialized() or not self.adx.initialized or prior_lower is None:
            return

        atr = self.atr.value
        if self.portfolio.is_net_short(self.config.instrument_id):
            self._manage_short(close, atr)
        elif self._can_open_position() and not self._has_active_order():
            phase_ok = (
                self.wyckoff is None
                or not self.wyckoff.initialized
                or self.phase == WyckoffPhase.MARKDOWN
            )
            volume_ok = (
                self.volume_sma.value > 0
                and bar.volume.as_double() >= self.volume_sma.value * self.config.volume_min_ratio
            )
            breakdown = close < prior_lower and close < self.trend.value
            if phase_ok and volume_ok and self.adx.value >= self.config.adx_min and breakdown:
                self._submit_entry(OrderSide.SELL, close, atr)

    def _manage_short(self, close: float, atr: float) -> None:
        if self._has_active_order():
            return
        distance = self.stop_distance or atr * self.config.atr_stop_multiple
        entry = self.entry_price or close
        if close >= entry + distance:
            self._submit_exit("ATR stop", close)
        elif close <= entry - distance * self.config.take_profit_multiple:
            self._submit_exit("take-profit", close)

    def _on_position_opened(self, event: PositionOpened) -> None:
        self.entry_price = float(event.avg_px_open)
        self.stop_distance = self.atr.value * self.config.atr_stop_multiple

    def _on_position_closed(self, event: PositionClosed) -> None:
        self.entry_price = None
        self.stop_distance = None

    def _on_reset(self) -> None:
        self.adx.reset()
        self.volume_sma.reset()
        if self.wyckoff is not None:
            self.wyckoff.reset()
        self.phase = WyckoffPhase.TRANSITION
        self.lows.clear()
        self.entry_price = None
        self.stop_distance = None
