"""Risk-management primitives for the crypto-futures system.

``RiskLimits`` is the runtime counterpart to ``config.settings.RiskSettings`` and
``DailyRiskTracker`` enforces the per-day trading limits. Both are shared by the
backtest report layer and every strategy, so position sizing and daily-loss rules
are identical across research and live runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class RiskLimits:
    """Effective per-trade and daily risk limits (base-currency denominated)."""

    risk_per_trade: Decimal
    max_notional: Decimal
    max_daily_loss: Decimal
    max_trades_per_day: int
    cooldown_bars_after_loss: int
    atr_stop_multiple: float
    leverage: int
    risk_pct_per_trade: float | None = None
    max_risk_per_trade_usdt: Decimal | None = None
    max_daily_loss_pct: float | None = None
    circuit_breaker_losses: int = 0
    circuit_breaker_pause_bars: int = 96

    def effective_risk_per_trade(self, equity: Decimal) -> Decimal:
        """Fixed USDT risk, or ``risk_pct_per_trade`` of equity when set."""
        if self.risk_pct_per_trade is not None and equity > 0:
            amount = equity * Decimal(str(self.risk_pct_per_trade)) / Decimal("100")
            if self.max_risk_per_trade_usdt is not None:
                amount = min(amount, self.max_risk_per_trade_usdt)
            return amount
        return self.risk_per_trade

    def effective_max_daily_loss(self, equity: Decimal) -> Decimal:
        if self.max_daily_loss_pct is not None and equity > 0:
            return equity * Decimal(str(self.max_daily_loss_pct)) / Decimal("100")
        return self.max_daily_loss

    def position_quantity(
        self,
        close: Decimal,
        atr: float,
        stop_multiple: float | None = None,
        equity: Decimal | None = None,
    ) -> Decimal:
        """Return the raw (unrounded) risk-based quantity capped by max notional.

        ``risk_per_trade`` is risked on the ATR-based stop distance; the result
        is additionally capped so position notional never exceeds
        ``max_notional``. Returns ``0`` if the stop distance is non-positive.

        ``stop_multiple`` overrides ``atr_stop_multiple`` (used by multi-leg
        strategies that size each leg against its own stop).
        """
        multiple = self.atr_stop_multiple if stop_multiple is None else stop_multiple
        stop_distance = Decimal(str(atr)) * Decimal(str(multiple))
        if stop_distance <= 0:
            return Decimal("0")

        risk = (
            self.effective_risk_per_trade(equity)
            if equity is not None
            else self.risk_per_trade
        )
        risk_qty = risk / stop_distance
        notional_qty = self.max_notional / close
        return min(risk_qty, notional_qty)


class DailyRiskTracker:
    """Tracks realised PnL / trade count / cooldown across UTC trading days."""

    def __init__(self, limits: RiskLimits) -> None:
        self.limits = limits
        self._day: date | None = None
        self.realized_pnl = 0.0
        self.trade_count = 0
        self.cooldown_remaining = 0
        self.consecutive_losses = 0
        self.circuit_pause_remaining = 0

    def roll_day(self, current_day: date) -> None:
        """Reset daily counters when the UTC trading day changes.

        Daily loss, max trades/day and the post-loss cooldown are all scoped
        to the UTC day (NOTES.md §2).
        """
        if current_day != self._day:
            self._day = current_day
            self.realized_pnl = 0.0
            self.trade_count = 0
            self.cooldown_remaining = 0

    def tick_cooldown(self) -> None:
        """Decrement the post-loss cooldown and circuit-breaker pause by one bar."""
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1
        if self.circuit_pause_remaining > 0:
            self.circuit_pause_remaining -= 1

    def can_open(self, equity: Decimal = Decimal("0")) -> bool:
        """Whether a new position may be opened under the daily limits."""
        if self.circuit_pause_remaining > 0:
            return False
        if self.cooldown_remaining > 0:
            return False
        if self.trade_count >= self.limits.max_trades_per_day:
            return False
        max_loss = float(self.limits.effective_max_daily_loss(equity))
        return self.realized_pnl > -max_loss

    def on_open(self) -> None:
        self.trade_count += 1

    def on_close(self, pnl: float) -> None:
        """Record a realised PnL and (on a loss) start the cooldown."""
        self.realized_pnl += pnl
        if pnl < 0:
            self.cooldown_remaining = self.limits.cooldown_bars_after_loss
            self.consecutive_losses += 1
            if (
                self.limits.circuit_breaker_losses > 0
                and self.consecutive_losses >= self.limits.circuit_breaker_losses
            ):
                self.circuit_pause_remaining = self.limits.circuit_breaker_pause_bars
                self.consecutive_losses = 0
        else:
            self.consecutive_losses = 0

    def reset(self) -> None:
        self._day = None
        self.realized_pnl = 0.0
        self.trade_count = 0
        self.cooldown_remaining = 0
        self.consecutive_losses = 0
        self.circuit_pause_remaining = 0
