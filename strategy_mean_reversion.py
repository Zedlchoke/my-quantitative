"""Mean-reversion strategy for ranging crypto markets.

Trades the assumption that price tends to revert to its mean when the market is
not trending. A **Vertical Horizontal Filter (VHF)** acts as a regime filter: it
is high in trends and low in ranges, so mean-reversion entries are only taken
while ``vhf <= vhf_max``.

Entries (Bollinger + RSI):
  - LONG  when close touches the lower band and RSI is oversold, in a range.
  - SHORT when close touches the upper band and RSI is overbought, in a range.

Exits:
  - ATR-based protective stop (``atr_stop_multiple``, tight ~1R), or
  - take-profit at ``take_profit_multiple`` x stop distance (reward:risk).
"""

from __future__ import annotations

from nautilus_trader.config import PositiveFloat
from nautilus_trader.config import PositiveInt
from nautilus_trader.indicators import AverageTrueRange
from nautilus_trader.indicators import BollingerBands
from nautilus_trader.indicators import RelativeStrengthIndex
from nautilus_trader.indicators import VerticalHorizontalFilter
from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.events import PositionClosed
from nautilus_trader.model.events import PositionOpened

from strategy_base import BaseFuturesStrategy
from strategy_base import BaseFuturesStrategyConfig


class MeanReversionStrategyConfig(BaseFuturesStrategyConfig, frozen=True):
    bb_period: PositiveInt = 20
    bb_k: PositiveFloat = 2.0
    rsi_period: PositiveInt = 2
    rsi_oversold: float = 10.0
    rsi_overbought: float = 90.0
    vhf_period: PositiveInt = 28
    vhf_max: float = 0.35  # <= this => ranging regime (mean-reversion active)
    take_profit_multiple: float = 1.5  # reward:risk target


class MeanReversionStrategy(BaseFuturesStrategy):
    """Bollinger + RSI mean-reversion with a VHF ranging-regime filter."""

    def __init__(self, config: MeanReversionStrategyConfig) -> None:
        if not 0 <= config.rsi_oversold < config.rsi_overbought <= 100:
            raise ValueError("RSI levels must satisfy 0 <= oversold < overbought <= 100")
        if config.atr_stop_multiple <= 0:
            raise ValueError("atr_stop_multiple must be positive")
        if config.take_profit_multiple <= 0:
            raise ValueError("take_profit_multiple must be positive")

        super().__init__(config)

        self.bb = BollingerBands(config.bb_period, config.bb_k)
        self.rsi = RelativeStrengthIndex(config.rsi_period)
        self.vhf = VerticalHorizontalFilter(config.vhf_period)
        self.atr = AverageTrueRange(config.atr_period)

        self.entry_price: float | None = None

    def indicators(self) -> list:
        return [self.bb, self.rsi, self.vhf, self.atr]

    def on_bar(self, bar: Bar) -> None:
        self._roll_trading_day()
        self.daily.tick_cooldown()

        if not self.indicators_initialized():
            return

        close = bar.close.as_double()
        atr = self.atr.value
        stop_distance = atr * self.config.atr_stop_multiple
        in_range = self.vhf.value <= self.config.vhf_max

        if self.portfolio.is_net_long(self.config.instrument_id):
            stop = (self.entry_price or close) - stop_distance
            target = (self.entry_price or close) + (
                stop_distance * self.config.take_profit_multiple
            )
            if close >= target and not self._has_active_order():
                self._submit_exit("take-profit (1.5R)", close)
            elif close <= stop and not self._has_active_order():
                self._submit_exit("ATR stop", close)

        elif self.portfolio.is_net_short(self.config.instrument_id):
            stop = (self.entry_price or close) + stop_distance
            target = (self.entry_price or close) - (
                stop_distance * self.config.take_profit_multiple
            )
            if close <= target and not self._has_active_order():
                self._submit_exit("take-profit (1.5R)", close)
            elif close >= stop and not self._has_active_order():
                self._submit_exit("ATR stop", close)

        elif self._can_open_position() and not self._has_active_order() and in_range:
            if close <= self.bb.lower and self.rsi.value <= self.config.rsi_oversold:
                self._submit_entry(OrderSide.BUY, close, atr)
            elif (
                self.config.allow_short
                and close >= self.bb.upper
                and self.rsi.value >= self.config.rsi_overbought
            ):
                self._submit_entry(OrderSide.SELL, close, atr)

    def _on_position_opened(self, event: PositionOpened) -> None:
        self.entry_price = float(event.avg_px_open)

    def _on_position_closed(self, event: PositionClosed) -> None:
        self.entry_price = None

    def _on_reset(self) -> None:
        self.entry_price = None
