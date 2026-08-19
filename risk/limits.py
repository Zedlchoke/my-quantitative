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

    def position_quantity(self, close: Decimal, atr: float) -> Decimal:
        """Return the raw (unrounded) risk-based quantity capped by max notional.

        ``risk_per_trade`` is risked on the ATR-based stop distance; the result
        is additionally capped so position notional never exceeds
        ``max_notional``. Returns ``0`` if the stop distance is non-positive.
        """
        stop_distance = Decimal(str(atr)) * Decimal(str(self.atr_stop_multiple))
        if stop_distance <= 0:
            return Decimal("0")

        risk_qty = self.risk_per_trade / stop_distance
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

    def roll_day(self, current_day: date) -> None:
        """Reset daily counters when the UTC trading day changes."""
        if current_day != self._day:
            self._day = current_day
            self.realized_pnl = 0.0
            self.trade_count = 0

    def tick_cooldown(self) -> None:
        """Decrement the post-loss cooldown by one bar."""
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1

    def can_open(self) -> bool:
        """Whether a new position may be opened under the daily limits."""
        if self.cooldown_remaining > 0:
            return False
        if self.trade_count >= self.limits.max_trades_per_day:
            return False
        return self.realized_pnl > -float(self.limits.max_daily_loss)

    def on_open(self) -> None:
        self.trade_count += 1

    def on_close(self, pnl: float) -> None:
        """Record a realised PnL and (on a loss) start the cooldown."""
        self.realized_pnl += pnl
        if pnl < 0:
            self.cooldown_remaining = self.limits.cooldown_bars_after_loss

    def reset(self) -> None:
        self._day = None
        self.realized_pnl = 0.0
        self.trade_count = 0
        self.cooldown_remaining = 0
