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
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.trading.strategy import Strategy

from risk.limits import DailyRiskTracker
from risk.limits import RiskLimits
from risk.portfolio import PortfolioRiskManager


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
    risk_pct_per_trade: float | None = None
    max_risk_per_trade_usdt: Decimal | None = None
    max_daily_loss_pct: float | None = None
    circuit_breaker_losses: PositiveInt = 0
    circuit_breaker_pause_bars: PositiveInt = 96
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
            risk_pct_per_trade=config.risk_pct_per_trade,
            max_risk_per_trade_usdt=config.max_risk_per_trade_usdt,
            max_daily_loss_pct=config.max_daily_loss_pct,
            circuit_breaker_losses=int(config.circuit_breaker_losses),
            circuit_breaker_pause_bars=int(config.circuit_breaker_pause_bars),
        )
        self.daily = DailyRiskTracker(self.risk_limits)
        self.portfolio_risk: PortfolioRiskManager | None = None

    def set_portfolio_risk_manager(self, manager: PortfolioRiskManager | None) -> None:
        """Attach the account-wide coordinator shared by all symbol strategies."""
        self.portfolio_risk = manager

    def _portfolio_symbol(self) -> str:
        return str(self.config.instrument_id.symbol).removesuffix("-PERP")

    def _release_portfolio_reservation(self) -> None:
        if self.portfolio_risk is not None:
            self.portfolio_risk.release(self._portfolio_symbol())

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
        if self.portfolio_risk is not None:
            self.portfolio_risk.roll_day(self.clock.utc_now().date())

    def _account_equity(self) -> Decimal:
        """Return account equity in base currency, or zero if unavailable."""
        try:
            money = self.portfolio.equity(Venue(self.config.instrument_id.venue.value))
            if money is not None:
                return Decimal(str(money.as_double()))
        except (AttributeError, TypeError, ValueError):
            pass
        return Decimal("0")

    def _can_open_position(self) -> bool:
        if not self.portfolio.is_flat(self.config.instrument_id):
            return False
        return self.daily.can_open(self._account_equity())

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

    def _submit_entry(
        self,
        side: OrderSide,
        close: float,
        atr: float,
        stop_multiple: float | None = None,
        risk_scale: float = 1.0,
    ) -> None:
        side_name = "LONG" if side == OrderSide.BUY else "SHORT"
        phase_note = f" | risk_scale={risk_scale:.2f}" if risk_scale != 1.0 else ""
        self.log.info(
            f"{side_name} signal at {close:.2f} | ATR={atr:.2f}{phase_note}",
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
            stop_multiple=stop_multiple,
            equity=self._account_equity(),
        )
        if risk_scale != 1.0:
            raw_quantity *= Decimal(str(risk_scale))
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

        if self.portfolio_risk is not None:
            quantity_decimal = Decimal(str(quantity.as_double()))
            reserved, reason = self.portfolio_risk.try_reserve(
                self._portfolio_symbol(),
                notional=quantity_decimal * Decimal(str(close)),
                risk_amount=(
                    quantity_decimal
                    * Decimal(str(atr))
                    * Decimal(str(stop_multiple or self.config.atr_stop_multiple))
                ),
                equity=self._account_equity(),
            )
            if not reserved:
                self.log.warning(f"Portfolio risk blocked entry: {reason}")
                return

        order = self.order_factory.market(
            instrument_id=self.config.instrument_id,
            order_side=side,
            quantity=quantity,
            time_in_force=TimeInForce.GTC,
        )
        try:
            self.submit_order(order)
        except Exception:
            self._release_portfolio_reservation()
            raise

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
        if self.portfolio_risk is not None:
            self.portfolio_risk.on_close(Decimal(str(pnl)))
        self._release_portfolio_reservation()
        self._on_position_closed(event)
        self.log.info(
            f"Position closed | PnL={pnl:.2f} | daily PnL={self.daily.realized_pnl:.2f}",
            color=LogColor.GREEN if pnl >= 0 else LogColor.RED,
        )

    def on_order_rejected(self, event) -> None:
        if event.instrument_id == self.config.instrument_id:
            self._release_portfolio_reservation()

    def on_order_denied(self, event) -> None:
        if event.instrument_id == self.config.instrument_id:
            self._release_portfolio_reservation()

    def on_order_canceled(self, event) -> None:
        if event.instrument_id == self.config.instrument_id and self.portfolio.is_flat(
            self.config.instrument_id,
        ):
            self._release_portfolio_reservation()
