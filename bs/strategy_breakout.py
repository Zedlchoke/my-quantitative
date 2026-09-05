"""Volatility breakout strategy — markup-only leg (research prototype).

Complements mean-reversion (range) with trend expansion entries. **Fixed rules**
(not tuned on ETH):

- Long only; no shorts.
- Enter only when Wyckoff daily phase == **markup**.
- ADX >= adx_min (trend strength), volume >= SMA × volume_min_ratio.
- Close breaks prior Donchian upper band (N-bar high, excluding current bar).

Exits: ATR stop frozen at entry; take-profit at take_profit_multiple × stop.
"""

from __future__ import annotations

from collections import deque

from nautilus_trader.config import PositiveInt
from nautilus_trader.indicators import AverageTrueRange
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


class BreakoutStrategyConfig(BaseFuturesStrategyConfig, frozen=True):
    donchian_period: PositiveInt = 20
    adx_period: PositiveInt = 14
    adx_min: float = 25.0
    volume_sma_period: PositiveInt = 20
    volume_min_ratio: float = 1.3
    take_profit_multiple: float = 2.0
    wyckoff_markup_only: bool = True
    history_days: PositiveInt = 220


class BreakoutStrategy(BaseFuturesStrategy):
    """Donchian + ADX + volume breakout; Wyckoff markup gate."""

    def __init__(self, config: BreakoutStrategyConfig) -> None:
        if config.adx_min <= 0:
            raise ValueError("adx_min must be positive")
        if config.volume_min_ratio <= 0:
            raise ValueError("volume_min_ratio must be positive")
        if config.take_profit_multiple <= 0:
            raise ValueError("take_profit_multiple must be positive")
        super().__init__(config)

        self.atr = AverageTrueRange(config.atr_period)
        self.adx = AverageDirectionalIndex(config.adx_period)
        self.volume_sma = VolumeSMA(config.volume_sma_period)
        self.wyckoff = WyckoffDailyTracker()
        self._wyckoff_phase = WyckoffPhase.TRANSITION
        self._highs: deque[float] = deque(maxlen=config.donchian_period)
        self._lows: deque[float] = deque(maxlen=config.donchian_period)

        self.entry_price: float | None = None
        self.stop_distance: float | None = None

    def indicators(self) -> list:
        return [self.atr]

    def on_bar(self, bar: Bar) -> None:
        self._roll_trading_day()
        self.daily.tick_cooldown()
        self.adx.update_bar(bar)
        self.volume_sma.update_bar(bar)
        self._wyckoff_phase = self.wyckoff.update_bar(bar)

        high = bar.high.as_double()
        low = bar.low.as_double()
        close = bar.close.as_double()
        prior_upper = max(self._highs) if len(self._highs) >= self.config.donchian_period else None
        self._highs.append(high)
        self._lows.append(low)

        if not self.indicators_initialized() or not self.adx.initialized:
            return
        if prior_upper is None:
            return

        atr = self.atr.value
        stop_distance = self.stop_distance or (atr * self.config.atr_stop_multiple)

        if self.portfolio.is_net_long(self.config.instrument_id):
            stop = (self.entry_price or close) - stop_distance
            target = (self.entry_price or close) + (
                stop_distance * self.config.take_profit_multiple
            )
            if close >= target and not self._has_active_order():
                self._submit_exit("take-profit", close)
            elif close <= stop and not self._has_active_order():
                self._submit_exit("ATR stop", close)

        elif self._can_open_position() and not self._has_active_order():
            if self.config.wyckoff_markup_only:
                if not self.wyckoff.initialized or self._wyckoff_phase != WyckoffPhase.MARKUP:
                    return

            volume_ok = (
                self.volume_sma.value > 0
                and bar.volume.as_double() >= self.volume_sma.value * self.config.volume_min_ratio
            )
            trend_ok = self.adx.value >= self.config.adx_min
            breakout = close > prior_upper

            if breakout and trend_ok and volume_ok:
                self._submit_entry(OrderSide.BUY, close, atr)

    def _on_position_opened(self, event: PositionOpened) -> None:
        self.entry_price = float(event.avg_px_open)
        self.stop_distance = self.atr.value * self.config.atr_stop_multiple

    def _on_position_closed(self, event: PositionClosed) -> None:
        self.entry_price = None
        self.stop_distance = None

    def _on_reset(self) -> None:
        self.entry_price = None
        self.stop_distance = None
        self.adx.reset()
        self.volume_sma.reset()
        self.wyckoff.reset()
        self._wyckoff_phase = WyckoffPhase.TRANSITION
        self._highs.clear()
        self._lows.clear()
