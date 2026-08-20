"""Regime-switch strategy: trend-following in trends, mean-reversion in ranges.

A **Vertical Horizontal Filter (VHF)** classifies the current regime:
  - VHF <= ``vhf_max``  -> ranging   -> Bollinger + RSI mean-reversion leg
  - VHF  > ``vhf_max``  -> trending  -> EMA-ATR trend leg

Both legs share one netting position and the same risk engine. The leg that
opens a position also manages its exit, so a position is never "orphaned" by a
regime flip mid-trade.
"""

from __future__ import annotations

from nautilus_trader.config import PositiveFloat
from nautilus_trader.config import PositiveInt
from nautilus_trader.indicators import AverageTrueRange
from nautilus_trader.indicators import BollingerBands
from nautilus_trader.indicators import ExponentialMovingAverage
from nautilus_trader.indicators import RelativeStrengthIndex
from nautilus_trader.indicators import VerticalHorizontalFilter
from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import PositionSide
from nautilus_trader.model.events import PositionClosed
from nautilus_trader.model.events import PositionOpened

from strategy_base import BaseFuturesStrategy
from strategy_base import BaseFuturesStrategyConfig


class RegimeSwitchStrategyConfig(BaseFuturesStrategyConfig, frozen=True):
    # Trend leg (EMA-ATR)
    fast_ema_period: PositiveInt = 20
    slow_ema_period: PositiveInt = 50
    trend_ema_period: PositiveInt = 200
    # Mean-reversion leg (Bollinger + RSI)
    bb_period: PositiveInt = 20
    bb_k: PositiveFloat = 2.0
    rsi_period: PositiveInt = 2
    rsi_oversold: float = 10.0
    rsi_overbought: float = 90.0
    # Regime filter (VHF)
    vhf_period: PositiveInt = 28
    vhf_max: float = 0.35
    # Stops / target
    trend_stop_multiple: float = 2.0
    mean_reversion_stop_multiple: float = 1.0
    take_profit_multiple: float = 1.5


class RegimeSwitchStrategy(BaseFuturesStrategy):
    """Trend-following in trends, mean-reversion in ranges (VHF-selected)."""

    def __init__(self, config: RegimeSwitchStrategyConfig) -> None:
        if not config.fast_ema_period < config.slow_ema_period < config.trend_ema_period:
            raise ValueError("EMA periods must satisfy fast < slow < trend")
        if not 0 <= config.rsi_oversold < config.rsi_overbought <= 100:
            raise ValueError("RSI levels must satisfy 0 <= oversold < overbought <= 100")

        super().__init__(config)

        # Trend leg indicators
        self.fast_ema = ExponentialMovingAverage(config.fast_ema_period)
        self.slow_ema = ExponentialMovingAverage(config.slow_ema_period)
        self.trend_ema = ExponentialMovingAverage(config.trend_ema_period)
        # Mean-reversion leg indicators
        self.bb = BollingerBands(config.bb_period, config.bb_k)
        self.rsi = RelativeStrengthIndex(config.rsi_period)
        # Regime filter + stop sizing
        self.vhf = VerticalHorizontalFilter(config.vhf_period)
        self.atr = AverageTrueRange(config.atr_period)

        self.previous_fast: float | None = None
        self.previous_slow: float | None = None
        self.entry_price: float | None = None
        self.extreme_price: float | None = None
        self.trailing_stop: float | None = None
        self.mode: str | None = None  # "trend" | "mean_reversion"

    def indicators(self) -> list:
        return [
            self.fast_ema,
            self.slow_ema,
            self.trend_ema,
            self.bb,
            self.rsi,
            self.vhf,
            self.atr,
        ]

    def on_bar(self, bar: Bar) -> None:
        self._roll_trading_day()
        self.daily.tick_cooldown()

        if not self.indicators_initialized():
            return

        close = bar.close.as_double()
        atr = self.atr.value
        fast = self.fast_ema.value
        slow = self.slow_ema.value
        trend = self.trend_ema.value

        crossed_up = self.previous_fast is not None and self.previous_fast <= self.previous_slow and fast > slow
        crossed_down = self.previous_fast is not None and self.previous_fast >= self.previous_slow and fast < slow
        in_range = self.vhf.value <= self.config.vhf_max

        if self.portfolio.is_net_long(self.config.instrument_id):
            self._manage_long(bar, close, atr, crossed_down, in_range, trend)
        elif self.portfolio.is_net_short(self.config.instrument_id):
            self._manage_short(bar, close, atr, crossed_up, in_range, trend)
        elif self._can_open_position() and not self._has_active_order():
            if in_range:
                self._try_mean_reversion_entry(close, atr)
            else:
                self._try_trend_entry(close, fast, slow, trend, crossed_up, crossed_down, atr)

        self._remember_ema(fast, slow)

    # -- entries --------------------------------------------------------------- #

    def _try_trend_entry(
        self,
        close: float,
        fast: float,
        slow: float,
        trend: float,
        crossed_up: bool,
        crossed_down: bool,
        atr: float,
    ) -> None:
        if crossed_up and close > trend:
            self.mode = "trend"
            self._submit_entry(OrderSide.BUY, close, atr, self.config.trend_stop_multiple)
        elif self.config.allow_short and crossed_down and close < trend:
            self.mode = "trend"
            self._submit_entry(OrderSide.SELL, close, atr, self.config.trend_stop_multiple)

    def _try_mean_reversion_entry(self, close: float, atr: float) -> None:
        if close <= self.bb.lower and self.rsi.value <= self.config.rsi_oversold:
            self.mode = "mean_reversion"
            self._submit_entry(
                OrderSide.BUY,
                close,
                atr,
                self.config.mean_reversion_stop_multiple,
            )
        elif (
            self.config.allow_short
            and close >= self.bb.upper
            and self.rsi.value >= self.config.rsi_overbought
        ):
            self.mode = "mean_reversion"
            self._submit_entry(
                OrderSide.SELL,
                close,
                atr,
                self.config.mean_reversion_stop_multiple,
            )

    # -- exit management -------------------------------------------------------- #

    def _manage_long(
        self,
        bar: Bar,
        close: float,
        atr: float,
        crossed_down: bool,
        in_range: bool,
        trend: float,
    ) -> None:
        if self._has_active_order():
            return

        if self.mode == "trend":
            self._update_trend_long_stop(bar.high.as_double(), close, atr)
            stop_hit = self.trailing_stop is not None and close <= self.trailing_stop
            if stop_hit or crossed_down:
                reason = "ATR stop" if stop_hit else "bearish EMA crossover"
                self._submit_exit(reason, close)
        else:  # mean_reversion
            stop = (self.entry_price or close) - atr * self.config.mean_reversion_stop_multiple
            target = (self.entry_price or close) + (
                atr * self.config.mean_reversion_stop_multiple * self.config.take_profit_multiple
            )
            if close >= target:
                self._submit_exit("take-profit (1.5R)", close)
            elif close <= stop:
                self._submit_exit("ATR stop", close)

    def _manage_short(
        self,
        bar: Bar,
        close: float,
        atr: float,
        crossed_up: bool,
        in_range: bool,
        trend: float,
    ) -> None:
        if self._has_active_order():
            return

        if self.mode == "trend":
            self._update_trend_short_stop(bar.low.as_double(), close, atr)
            stop_hit = self.trailing_stop is not None and close >= self.trailing_stop
            if stop_hit or crossed_up:
                reason = "ATR stop" if stop_hit else "bullish EMA crossover"
                self._submit_exit(reason, close)
        else:  # mean_reversion
            stop = (self.entry_price or close) + atr * self.config.mean_reversion_stop_multiple
            target = (self.entry_price or close) - (
                atr * self.config.mean_reversion_stop_multiple * self.config.take_profit_multiple
            )
            if close <= target:
                self._submit_exit("take-profit (1.5R)", close)
            elif close >= stop:
                self._submit_exit("ATR stop", close)

    # -- trend-leg trailing stop ------------------------------------------------ #

    def _update_trend_long_stop(self, high: float, close: float, atr: float) -> None:
        if self.entry_price is None:
            self.entry_price = close
        self.extreme_price = max(self.extreme_price or high, high)
        initial_stop = self.entry_price - atr * self.config.trend_stop_multiple
        candidate = self.extreme_price - atr * self.config.trend_stop_multiple
        self.trailing_stop = max(self.trailing_stop or initial_stop, candidate)

    def _update_trend_short_stop(self, low: float, close: float, atr: float) -> None:
        if self.entry_price is None:
            self.entry_price = close
        self.extreme_price = min(self.extreme_price or low, low)
        initial_stop = self.entry_price + atr * self.config.trend_stop_multiple
        candidate = self.extreme_price + atr * self.config.trend_stop_multiple
        self.trailing_stop = min(self.trailing_stop or initial_stop, candidate)

    # -- helpers ---------------------------------------------------------------- #

    def _remember_ema(self, fast: float, slow: float) -> None:
        self.previous_fast = fast
        self.previous_slow = slow

    def _clear_position_state(self) -> None:
        self.entry_price = None
        self.extreme_price = None
        self.trailing_stop = None
        self.mode = None

    def _on_position_opened(self, event: PositionOpened) -> None:
        self.entry_price = float(event.avg_px_open)
        self.extreme_price = self.entry_price
        if self.mode == "trend":
            if event.side == PositionSide.LONG:
                self.trailing_stop = self.entry_price - (
                    self.atr.value * self.config.trend_stop_multiple
                )
            else:
                self.trailing_stop = self.entry_price + (
                    self.atr.value * self.config.trend_stop_multiple
                )

    def _on_position_closed(self, event: PositionClosed) -> None:
        self._clear_position_state()

    def _on_reset(self) -> None:
        self.previous_fast = None
        self.previous_slow = None
        self._clear_position_state()
