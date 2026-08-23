"""Shared base for futures strategies.

Every strategy in this project inherits from ``BaseFuturesStrategy`` so that
position sizing, order submission, daily risk tracking and shutdown behaviour are
implemented exactly once and therefore identical between backtest and live.
"""

from __future__ import annotations

import functools
from decimal import Decimal

import pandas as pd

from nautilus_trader.common.enums import LogColor
from nautilus_trader.config import PositiveInt
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import PositionSide
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.events import OrderFilled
from nautilus_trader.model.events import PositionClosed
from nautilus_trader.model.events import PositionOpened
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.trading.strategy import Strategy

from contracts.protocol import ExecutionMode
from risk.limits import DailyRiskTracker
from risk.limits import RiskLimits
from risk.portfolio import PortfolioRiskManager

EVIDENCE_CLASS_SCORED = "SCORED"
EVIDENCE_CLASS_DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"

EXECUTION_RECORD_KEYS: tuple[str, ...] = (
    "position_id",
    "strategy_type",
    "symbol",
    "fold",
    "side",
    "signal_ts",
    "submit_ts",
    "fill_ts",
    "signal_reference_price",
    "fill_price",
    "execution_mode",
    "slippage_ticks",
    "quantity",
    "initial_stop_price",
    "initial_risk_usdt",
    "gross_pnl",
    "commission",
    "slippage_cost",
    "funding_pnl",
    "canonical_pnl",
    "r_multiple",
)


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
    # -- V3 execution truth (PLAN section 7) --------------------------------- #
    # NEXT_BAR_EVENT_BASELINE: a signal on closed bar t is submitted on the
    # FIRST subsequent bar event (t+1) and fills at that bar's CLOSE (+-
    # slippage ticks). This engine reality is 'next-bar-close', never
    # 'next-open'. SAME_BAR_CLOSE_DIAGNOSTIC: legacy same-bar-close behaviour,
    # every record labelled evidence_class=DIAGNOSTIC_ONLY.
    execution_mode: str = ExecutionMode.NEXT_BAR_EVENT_BASELINE.value
    slippage_ticks: PositiveInt = 1
    fold: str | None = None
    strict_execution_invariant: bool = True


def _wrap_entry_deferral(user_on_bar):
    """Wrap a subclass ``on_bar`` so queued entries flush before its body.

    The wrapper also records the latest event timestamp so signal/submit/fill
    facts are captured even when strategies never pass the bar down.
    """

    @functools.wraps(user_on_bar)
    def wrapped(self, bar, *args, **kwargs):
        self._latest_bar_ts = int(bar.ts_event)
        if getattr(self, "_deferral_enabled", False):
            self._flush_pending_entry(bar)
        return user_on_bar(self, bar, *args, **kwargs)

    wrapped._entry_deferral_wrapped = True  # type: ignore[attr-defined]
    return wrapped


class BaseFuturesStrategy(Strategy):
    """Common plumbing: instrument, risk, orders, daily limits."""

    config: BaseFuturesStrategyConfig

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        user_on_bar = cls.__dict__.get("on_bar")
        if callable(user_on_bar) and not getattr(
            user_on_bar, "_entry_deferral_wrapped", False
        ):
            cls.on_bar = _wrap_entry_deferral(user_on_bar)

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

        # -- V3 execution-truth state ---------------------------------------- #
        self.execution_mode: str = config.execution_mode
        self._deferral_enabled = (
            self.execution_mode == ExecutionMode.NEXT_BAR_EVENT_BASELINE.value
        )
        self._pending_entry: dict | None = None
        self._pending_exit_timing: dict | None = None
        self._latest_bar_ts: int | None = None
        self._entry_meta_by_order: dict[str, dict] = {}
        self._last_entry_meta: dict | None = None
        self._open_records: dict[str, dict] = {}
        self._order_commission: dict[str, float] = {}
        self.execution_records: list[dict] = []
        self.execution_violations: list[str] = []

    # -- V3 execution truth (PLAN section 7) ---------------------------------- #

    def _signal_ts_now(self) -> int:
        """Event timestamp of the bar currently being processed (ns)."""
        if self._latest_bar_ts is not None:
            return self._latest_bar_ts
        clock = getattr(self, "clock", None)
        timestamp_ns = getattr(clock, "timestamp_ns", None)
        if callable(timestamp_ns):
            try:
                return int(timestamp_ns())
            except Exception:  # noqa: BLE001 - abstract Clock raises in tests
                pass
        utc_now = getattr(clock, "utc_now", None)
        if callable(utc_now):
            try:
                return int(utc_now().timestamp() * 1e9)
            except Exception:  # noqa: BLE001
                pass
        return 0

    def _flush_pending_entry(self, bar) -> None:
        """Submit the entry queued on a previous bar, at this bar's event.

        Fill semantics: a market order submitted during ``on_bar(bar_{t+1})``
        fills at ``bar_{t+1}.close +- slippage ticks`` with
        ``ts_init == bar_{t+1}.ts_event`` — i.e. NEXT-BAR-CLOSE (never
        next-open; there is no native next-bar-open fill for bar data).
        """
        if self._pending_entry is None:
            return
        intent = self._pending_entry
        self._pending_entry = None
        if not self.config.enable_trading:
            return
        if not self.portfolio.is_flat(self.config.instrument_id):
            self.log.warning("Deferred entry dropped: position already open")
            return
        if self._has_active_order():
            self.log.warning("Deferred entry dropped: order already active")
            return
        intent["submit_reference_price"] = float(bar.close.as_double())
        self.log.info(
            "Flushing deferred entry at next-bar event "
            f"(signal_ts={intent['signal_ts']}, submit_ts={self._signal_ts_now()})",
            color=LogColor.YELLOW,
        )
        self._execute_entry_intent(intent)

    def _execute_entry_intent(self, intent: dict) -> None:
        """Reserve portfolio risk and submit one frozen entry intent."""
        side = intent["side"]
        close = intent["signal_reference_price"]
        if self.portfolio_risk is not None:
            quantity_decimal = Decimal(str(intent["quantity"].as_double()))
            reserved, reason = self.portfolio_risk.try_reserve(
                self._portfolio_symbol(),
                notional=quantity_decimal * Decimal(str(close)),
                risk_amount=(
                    quantity_decimal
                    * Decimal(str(intent["atr"]))
                    * Decimal(str(intent["stop_multiple"]))
                ),
                equity=self._account_equity(),
            )
            if not reserved:
                self.log.warning(f"Portfolio risk blocked entry: {reason}")
                return
        order = self.order_factory.market(
            instrument_id=self.config.instrument_id,
            order_side=side,
            quantity=intent["quantity"],
            time_in_force=TimeInForce.GTC,
        )
        meta = {
            **intent,
            "submit_ts": self._signal_ts_now(),
        }
        self._entry_meta_by_order[str(order.client_order_id)] = meta
        self._last_entry_meta = meta
        try:
            self.submit_order(order)
        except Exception:
            self._entry_meta_by_order.pop(str(order.client_order_id), None)
            self._release_portfolio_reservation()
            raise

    def _initial_stop_for(self, side: PositionSide, fill_price: float) -> float | None:
        """Initial protective stop frozen at entry.

        Default: ATR-multiple stop computed from the ATR captured at SIGNAL
        time (the same value used for sizing), anchored at the actual fill
        price. Strategies may override for their own stop rule.
        """
        meta = self._last_entry_meta or {}
        atr = meta.get("atr")
        multiple = meta.get("stop_multiple")
        if atr is None or multiple is None:
            return None
        distance = float(atr) * float(multiple)
        if side == PositionSide.LONG:
            return fill_price - distance
        if side == PositionSide.SHORT:
            return fill_price + distance
        return None

    def _finalize_entry_record(self, event: PositionOpened) -> dict | None:
        position_id = getattr(event, "position_id", None)
        if position_id is None:
            # Synthetic event without engine identity (test harnesses) — no
            # execution evidence can exist for it.
            return None
        opening_order_id = getattr(event, "opening_order_id", None)
        meta = (
            self._entry_meta_by_order.pop(str(opening_order_id), None)
            if opening_order_id
            else None
        )
        if meta is None:
            meta = self._last_entry_meta
        fill_price = float(event.avg_px_open)
        raw_last_qty = getattr(event, "last_qty", None)
        if raw_last_qty is not None:
            quantity = abs(float(raw_last_qty))
        elif meta is not None:
            quantity = abs(float(meta["quantity"].as_double()))
        else:
            quantity = 0.0
        side = "LONG" if event.side == PositionSide.LONG else "SHORT"
        initial_stop_price = self._initial_stop_for(event.side, fill_price)
        initial_risk_usdt: float | None = None
        reason_codes: list[str] = []
        if (
            initial_stop_price is not None
            and quantity > 0
            and abs(fill_price - initial_stop_price) > 0
        ):
            initial_risk_usdt = abs(fill_price - initial_stop_price) * quantity
        if initial_risk_usdt is None or initial_risk_usdt <= 0:
            initial_risk_usdt = None
            reason_codes.append("invalid_initial_risk")
        submit_reference = meta.get("submit_reference_price") if meta else None
        slippage_cost: float | None = None
        if submit_reference is not None and quantity > 0:
            if event.side == PositionSide.LONG:
                slippage_cost = (fill_price - submit_reference) * quantity
            elif event.side == PositionSide.SHORT:
                slippage_cost = (submit_reference - fill_price) * quantity
        commission = (
            self._order_commission.get(str(opening_order_id))
            if opening_order_id
            else None
        )
        diagnostic = (
            self.execution_mode == ExecutionMode.SAME_BAR_CLOSE_DIAGNOSTIC.value
        )
        record: dict = {
            "position_id": str(position_id),
            "strategy_type": type(self).__name__,
            "symbol": self._portfolio_symbol(),
            "fold": self.config.fold or "n/a",
            "side": side,
            "signal_ts": meta.get("signal_ts") if meta else None,
            "submit_ts": meta.get("submit_ts") if meta else None,
            "fill_ts": int(event.ts_event) if getattr(event, "ts_event", None) else None,
            "signal_reference_price": (
                meta.get("signal_reference_price") if meta else None
            ),
            "fill_price": fill_price,
            "execution_mode": self.execution_mode,
            "slippage_ticks": int(self.config.slippage_ticks),
            "quantity": quantity,
            "initial_stop_price": initial_stop_price,
            "initial_risk_usdt": initial_risk_usdt,
            "gross_pnl": None,
            "commission": commission,
            "slippage_cost": slippage_cost,
            "funding_pnl": None,  # joined later by the funding audit/runner
            "canonical_pnl": None,  # filled at close (funding join point)
            "r_multiple": None,  # filled at close when initial risk valid
            "evidence_class": (
                EVIDENCE_CLASS_DIAGNOSTIC_ONLY
                if diagnostic
                else EVIDENCE_CLASS_SCORED
            ),
            "reason_codes": reason_codes,
        }
        for key in EXECUTION_RECORD_KEYS:
            if key not in record:
                raise AssertionError(f"execution record missing §7 key: {key}")
        return record

    def _check_signal_fill_ordering(self, record: dict) -> bool:
        """Enforce signal_ts < submit_ts <= fill_ts for scored baseline entries."""
        if record["execution_mode"] != ExecutionMode.NEXT_BAR_EVENT_BASELINE.value:
            return True  # SAME_BAR_CLOSE_DIAGNOSTIC is exempt (diagnostic only)
        signal_ts, submit_ts, fill_ts = (
            record.get("signal_ts"),
            record.get("submit_ts"),
            record.get("fill_ts"),
        )
        if signal_ts is None or submit_ts is None or fill_ts is None:
            ok = False
        else:
            ok = bool(signal_ts < submit_ts <= fill_ts)
        if ok:
            return True
        record["reason_codes"].append("signal_fill_ordering_violation")
        self.execution_violations.append(
            f"{record.get('position_id')}: "
            f"signal_ts={signal_ts} submit_ts={submit_ts} fill_ts={fill_ts}",
        )
        if self.config.strict_execution_invariant:
            raise AssertionError(
                "signal_fill_ordering_violation: scored entry must satisfy "
                f"signal_ts < submit_ts <= fill_ts, got {record}"
            )
        self.log.error(
            f"signal_fill_ordering_violation on {record.get('position_id')}",
        )
        return False

    @staticmethod
    def expectancy_r(positions: list[dict]) -> float | None:
        """Mean of valid r_multiples across positions; None-safe."""
        values = [
            float(p["r_multiple"])
            for p in positions
            if p.get("r_multiple") is not None
        ]
        if not values:
            return None
        return sum(values) / len(values)

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

        # Freeze the intent at SIGNAL time: quantity, stop distance, reference
        # price and the signal bar's close timestamp all come from bar t.
        effective_stop_multiple = float(
            stop_multiple
            if stop_multiple is not None
            else self.config.atr_stop_multiple
        )
        intent = {
            "side": side,
            "quantity": quantity,
            "atr": atr,
            "stop_multiple": effective_stop_multiple,
            "signal_reference_price": close,
            "signal_ts": self._signal_ts_now(),
        }
        if self._deferral_enabled:
            # NEXT_BAR_EVENT_BASELINE: do NOT submit during the signal bar.
            # The intent is flushed on the first subsequent on_bar event.
            self._pending_entry = intent
            self.log.info(
                f"Entry deferred to next-bar event (signal_ts={intent['signal_ts']})",
                color=LogColor.YELLOW,
            )
            return
        self._execute_entry_intent(intent)

    def _submit_exit(self, reason: str, close: float) -> None:
        """Risk-reducing exit — always submitted immediately.

        Timing fields are still recorded (exit_signal_ts == exit_submit_ts ==
        the current bar's close timestamp; exit_fill_ts arrives with the
        PositionClosed event) so delay stress can be measured later.
        """
        self.log.warning(f"EXIT signal: {reason} at {close:.2f}")
        self._pending_exit_timing = {
            "exit_signal_ts": self._signal_ts_now(),
            "exit_submit_ts": self._signal_ts_now(),
            "exit_reason": reason,
            "exit_reference_price": close,
        }
        if self.config.enable_trading:
            self.close_all_positions(
                self.config.instrument_id,
                time_in_force=TimeInForce.GTC,
                reduce_only=True,
            )

    # -- fill/commission facts -------------------------------------------------- #

    def on_order_filled(self, event: OrderFilled) -> None:
        if event.instrument_id != self.config.instrument_id:
            return
        commission = getattr(event, "commission", None)
        if commission is not None:
            self._order_commission[str(event.client_order_id)] = float(
                commission.as_double(),
            )

    # -- position events ------------------------------------------------------- #

    def on_position_opened(self, event: PositionOpened) -> None:
        if event.instrument_id != self.config.instrument_id:
            return
        self.daily.on_open()
        record = self._finalize_entry_record(event)
        if record is not None:
            self._open_records[str(event.position_id)] = record
            self.execution_records.append(record)
            self._check_signal_fill_ordering(record)
        self._on_position_opened(event)

    def on_position_closed(self, event: PositionClosed) -> None:
        if event.instrument_id != self.config.instrument_id:
            return
        pnl = event.realized_pnl.as_double()
        self.daily.on_close(pnl)
        if self.portfolio_risk is not None:
            self.portfolio_risk.on_close(Decimal(str(pnl)))
        self._release_portfolio_reservation()
        record = self._open_records.pop(str(getattr(event, "position_id", "")), None)
        if record is not None:
            closing_order_id = getattr(event, "closing_order_id", None)
            closing_commission = (
                self._order_commission.get(str(closing_order_id))
                if closing_order_id
                else None
            )
            commissions = [
                c
                for c in (record.get("commission"), closing_commission)
                if c is not None
            ]
            record["commission"] = sum(commissions) if commissions else None
            record["gross_pnl"] = pnl
            # canonical_pnl is realized PnL after funding; funding_pnl is joined
            # by the runner's funding audit later. This is the join point.
            record["canonical_pnl"] = pnl
            initial_risk = record.get("initial_risk_usdt")
            if initial_risk is not None and initial_risk > 0:
                record["r_multiple"] = pnl / initial_risk
            timing = getattr(self, "_pending_exit_timing", None)
            if timing is not None:
                record.update(timing)
                record["exit_fill_ts"] = int(event.ts_event)
                self._pending_exit_timing = None
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
