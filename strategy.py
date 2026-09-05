from __future__ import annotations

from nautilus_trader.config import PositiveInt
from nautilus_trader.indicators import AverageTrueRange
from nautilus_trader.indicators import ExponentialMovingAverage
from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import PositionSide
from nautilus_trader.model.events import PositionClosed
from nautilus_trader.model.events import PositionOpened

from strategy_base import BaseFuturesStrategy
from strategy_base import BaseFuturesStrategyConfig


class EmaAtrStrategyConfig(BaseFuturesStrategyConfig, frozen=True):
    fast_ema_period: PositiveInt = 20
    slow_ema_period: PositiveInt = 50
    trend_ema_period: PositiveInt = 200


class EmaAtrStrategy(BaseFuturesStrategy):
    """USD-M perpetual trend strategy with long/short entries and risk controls."""

    def __init__(self, config: EmaAtrStrategyConfig) -> None:
        if not config.fast_ema_period < config.slow_ema_period < config.trend_ema_period:
            raise ValueError("EMA periods must satisfy fast < slow < trend")
        if config.atr_stop_multiple <= 0:
            raise ValueError("atr_stop_multiple must be positive")
        if (
            config.risk_per_trade_usdt <= 0
            or config.max_notional_usdt <= 0
            or config.max_daily_loss_usdt <= 0
        ):
            raise ValueError("Risk limits must be positive")

        super().__init__(config)

        self.fast_ema = ExponentialMovingAverage(config.fast_ema_period)
        self.slow_ema = ExponentialMovingAverage(config.slow_ema_period)
        self.trend_ema = ExponentialMovingAverage(config.trend_ema_period)
        self.atr = AverageTrueRange(config.atr_period)

        self.previous_fast: float | None = None
        self.previous_slow: float | None = None
        self.entry_price: float | None = None
        self.extreme_price: float | None = None
        self.trailing_stop: float | None = None

    def indicators(self) -> list:
        return [self.fast_ema, self.slow_ema, self.trend_ema, self.atr]

    def on_bar(self, bar: Bar) -> None:
        self._roll_trading_day()
        self.daily.tick_cooldown()

        if not self.indicators_initialized():
            return

        close = bar.close.as_double()
        fast = self.fast_ema.value
        slow = self.slow_ema.value
        trend = self.trend_ema.value
        atr = self.atr.value

        if self.previous_fast is None or self.previous_slow is None:
            self._remember_ema(fast, slow)
            return

        crossed_up = self.previous_fast <= self.previous_slow and fast > slow
        crossed_down = self.previous_fast >= self.previous_slow and fast < slow

        if self.portfolio.is_net_long(self.config.instrument_id):
            self._update_long_stop(bar.high.as_double(), close, atr)
            stop_hit = self.trailing_stop is not None and close <= self.trailing_stop
            if (stop_hit or crossed_down) and not self._has_active_order():
                reason = "ATR stop" if stop_hit else "bearish EMA crossover"
                self._submit_exit(reason, close)

        elif self.portfolio.is_net_short(self.config.instrument_id):
            self._update_short_stop(bar.low.as_double(), close, atr)
            stop_hit = self.trailing_stop is not None and close >= self.trailing_stop
            if (stop_hit or crossed_up) and not self._has_active_order():
                reason = "ATR stop" if stop_hit else "bullish EMA crossover"
                self._submit_exit(reason, close)

        elif self._can_open_position() and not self._has_active_order():
            if crossed_up and close > trend:
                self._submit_entry(OrderSide.BUY, close, atr)
            elif self.config.allow_short and crossed_down and close < trend:
                self._submit_entry(OrderSide.SELL, close, atr)

        self._remember_ema(fast, slow)

    def _update_long_stop(self, high: float, close: float, atr: float) -> None:
        if self.entry_price is None:
            self.entry_price = close
        self.extreme_price = max(self.extreme_price or high, high)
        initial_stop = self.entry_price - atr * self.config.atr_stop_multiple
        candidate = self.extreme_price - atr * self.config.atr_stop_multiple
        self.trailing_stop = max(self.trailing_stop or initial_stop, candidate)

    def _update_short_stop(self, low: float, close: float, atr: float) -> None:
        if self.entry_price is None:
            self.entry_price = close
        self.extreme_price = min(self.extreme_price or low, low)
        initial_stop = self.entry_price + atr * self.config.atr_stop_multiple
        candidate = self.extreme_price + atr * self.config.atr_stop_multiple
        self.trailing_stop = min(self.trailing_stop or initial_stop, candidate)

    def _remember_ema(self, fast: float, slow: float) -> None:
        self.previous_fast = fast
        self.previous_slow = slow

    def _clear_position_state(self) -> None:
        self.entry_price = None
        self.extreme_price = None
        self.trailing_stop = None

    def _on_position_opened(self, event: PositionOpened) -> None:
        self.entry_price = float(event.avg_px_open)
        self.extreme_price = self.entry_price
        if event.side == PositionSide.LONG:
            self.trailing_stop = self.entry_price - (
                self.atr.value * self.config.atr_stop_multiple
            )
        else:
            self.trailing_stop = self.entry_price + (
                self.atr.value * self.config.atr_stop_multiple
            )

    def _on_position_closed(self, event: PositionClosed) -> None:
        self._clear_position_state()

    def _on_reset(self) -> None:
        self.previous_fast = None
        self.previous_slow = None
        self._clear_position_state()
