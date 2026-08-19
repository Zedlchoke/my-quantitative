"""Shared base for futures strategies.

Every strategy in this project inherits from ``BaseFuturesStrategy`` so that
position sizing, order submission, daily risk tracking and shutdown behaviour are
implemented exactly once and therefore identical between backtest and live.
"""

from __future__ import annotations

from decimal import Decimal

import pandas as pd

from nautilus_trader.common.enums import LogColor
from nautilus_trader.config import PositiveInt
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.events import PositionClosed
from nautilus_trader.model.events import PositionOpened
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.trading.strategy import Strategy

from risk.limits import DailyRiskTracker
from risk.limits import RiskLimits


class BaseFuturesStrategyConfig(StrategyConfig, frozen=True):
    """Config fields shared by all futures strategies."""

    instrument_id: InstrumentId
    bar_type: BarType
    atr_period: PositiveInt = 14
    atr_stop_multiple: float = 2.0
    risk_per_trade_usdt: Decimal = Decimal("5")
    max_notional_usdt: Decimal = Decimal("100")
    max_daily_loss_usdt: Decimal = Decimal("20")
    max_trades_per_day: PositiveInt = 4
    cooldown_bars_after_loss: PositiveInt = 4
    history_days: PositiveInt = 10
    allow_short: bool = True
    enable_trading: bool = False
    request_historical_bars: bool = True
    close_position_on_stop: bool = True


class BaseFuturesStrategy(Strategy):
    """Common plumbing: instrument, risk, orders, daily limits."""

    config: BaseFuturesStrategyConfig

    def __init__(self, config: BaseFuturesStrategyConfig) -> None:
        super().__init__(config)

        self.instrument: Instrument | None = None
        self.risk_limits = RiskLimits(
            risk_per_trade=config.risk_per_trade_usdt,
            max_notional=config.max_notional_usdt,
            max_daily_loss=config.max_daily_loss_usdt,
            max_trades_per_day=config.max_trades_per_day,
            cooldown_bars_after_loss=config.cooldown_bars_after_loss,
            atr_stop_multiple=config.atr_stop_multiple,
            leverage=1,  # leverage is applied at the venue/client level
        )
        self.daily = DailyRiskTracker(self.risk_limits)

    # -- hooks ---------------------------------------------------------------- #

    def indicators(self) -> list:
        """Indicators to register for ``config.bar_type`` and reset."""
        raise NotImplementedError

    def _on_position_opened(self, event: PositionOpened) -> None:
        """Strategy-specific state after a position opens."""

    def _on_position_closed(self, event: PositionClosed) -> None:
        """Strategy-specific state after a position closes."""

    def _on_reset(self) -> None:
        """Strategy-specific reset state."""

    # -- lifecycle ------------------------------------------------------------- #

    def on_start(self) -> None:
        self.instrument = self.cache.instrument(self.config.instrument_id)
        if self.instrument is None:
            self.log.error(f"Instrument not found: {self.config.instrument_id}")
            self.stop()
            return

        for indicator in self.indicators():
            self.register_indicator_for_bars(self.config.bar_type, indicator)

        mode = "TRADING" if self.config.enable_trading else "SIGNAL-ONLY"
        self.log.info(
            f"{type(self).__name__} started for {self.config.instrument_id} [{mode}]",
            color=LogColor.GREEN,
        )

        if self.config.request_historical_bars:
            self.request_bars(
                self.config.bar_type,
                start=self.clock.utc_now() - pd.Timedelta(days=self.config.history_days),
                callback=lambda _: self.subscribe_bars(self.config.bar_type),
            )
        else:
            self.subscribe_bars(self.config.bar_type)

    def on_stop(self) -> None:
        self.cancel_all_orders(self.config.instrument_id)
        if (
            self.config.enable_trading
            and self.config.close_position_on_stop
            and not self.portfolio.is_flat(self.config.instrument_id)
        ):
            self.close_all_positions(
                self.config.instrument_id,
                reduce_only=True,
            )
        self.unsubscribe_bars(self.config.bar_type)

    def on_reset(self) -> None:
        for indicator in self.indicators():
            indicator.reset()
        self.daily.reset()
        self._on_reset()

    # -- shared behaviour ------------------------------------------------------ #

    def _roll_trading_day(self) -> None:
        self.daily.roll_day(self.clock.utc_now().date())

    def _can_open_position(self) -> bool:
        if not self.portfolio.is_flat(self.config.instrument_id):
            return False
        return self.daily.can_open()

    def _has_active_order(self) -> bool:
        return bool(
            self.cache.orders_open(
                instrument_id=self.config.instrument_id,
                strategy_id=self.id,
            )
            or self.cache.orders_inflight(
                instrument_id=self.config.instrument_id,
                strategy_id=self.id,
            ),
        )

    def _submit_entry(self, side: OrderSide, close: float, atr: float) -> None:
        side_name = "LONG" if side == OrderSide.BUY else "SHORT"
        self.log.info(
            f"{side_name} signal at {close:.2f} | ATR={atr:.2f}",
            color=LogColor.YELLOW,
        )
        if not self.config.enable_trading:
            return
        if self.instrument is None or atr <= 0:
            self.log.error("Cannot calculate a valid order quantity")
            return

        raw_quantity = self.risk_limits.position_quantity(
            close=Decimal(str(close)),
            atr=atr,
        )
        quantity = self.instrument.make_qty(raw_quantity)

        if quantity.as_double() <= 0:
            self.log.error("Order quantity is zero after precision rounding")
            return
        if self.instrument.min_quantity and quantity < self.instrument.min_quantity:
            self.log.error(f"Order quantity {quantity} is below minimum")
            return
        if (
            self.instrument.min_notional
            and quantity.as_double() * close < self.instrument.min_notional.as_double()
        ):
            self.log.error("Order notional is below the instrument minimum")
            return

        order = self.order_factory.market(
            instrument_id=self.config.instrument_id,
            order_side=side,
            quantity=quantity,
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)

    def _submit_exit(self, reason: str, close: float) -> None:
        self.log.warning(f"EXIT signal: {reason} at {close:.2f}")
        if self.config.enable_trading:
            self.close_all_positions(
                self.config.instrument_id,
                time_in_force=TimeInForce.GTC,
                reduce_only=True,
            )

    # -- position events ------------------------------------------------------- #

    def on_position_opened(self, event: PositionOpened) -> None:
        if event.instrument_id != self.config.instrument_id:
            return
        self.daily.on_open()
        self._on_position_opened(event)

    def on_position_closed(self, event: PositionClosed) -> None:
        if event.instrument_id != self.config.instrument_id:
            return
        pnl = event.realized_pnl.as_double()
        self.daily.on_close(pnl)
        self._on_position_closed(event)
        self.log.info(
            f"Position closed | PnL={pnl:.2f} | daily PnL={self.daily.realized_pnl:.2f}",
            color=LogColor.GREEN if pnl >= 0 else LogColor.RED,
        )
