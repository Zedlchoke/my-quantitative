"""Shared portfolio-level risk budget for concurrent strategy instances."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from threading import RLock


@dataclass(frozen=True)
class PortfolioRiskLimits:
    max_gross_notional: Decimal = Decimal("1200")
    max_portfolio_risk_pct: float = 3.0
    max_concurrent_positions: int = 4
    max_positions_per_cluster: int = 2
    max_daily_loss_pct: float = 2.0
    circuit_breaker_losses: int = 6

    def validate(self) -> None:
        if self.max_gross_notional <= 0:
            raise ValueError("max_gross_notional must be > 0")
        if self.max_portfolio_risk_pct <= 0:
            raise ValueError("max_portfolio_risk_pct must be > 0")
        if self.max_concurrent_positions <= 0 or self.max_positions_per_cluster <= 0:
            raise ValueError("portfolio position caps must be > 0")
        if self.max_daily_loss_pct <= 0 or self.circuit_breaker_losses <= 0:
            raise ValueError("portfolio daily loss and circuit breaker must be > 0")


@dataclass(frozen=True)
class ExposureReservation:
    symbol: str
    cluster: str
    asset_class: str
    notional: Decimal
    risk_amount: Decimal


class PortfolioRiskManager:
    """Atomic exposure reservations shared by all strategies in one account."""

    def __init__(
        self,
        limits: PortfolioRiskLimits,
        *,
        clusters: dict[str, str] | None = None,
        asset_classes: dict[str, str] | None = None,
    ) -> None:
        limits.validate()
        self.limits = limits
        self.clusters = {k.upper(): v for k, v in (clusters or {}).items()}
        self.asset_classes = {k.upper(): v for k, v in (asset_classes or {}).items()}
        self._reservations: dict[str, ExposureReservation] = {}
        self._lock = RLock()
        self._day: date | None = None
        self.realized_pnl = Decimal("0")
        self.consecutive_losses = 0
        self.halted_for_day = False

    def roll_day(self, current_day: date) -> None:
        with self._lock:
            if current_day != self._day:
                self._day = current_day
                self.realized_pnl = Decimal("0")
                self.consecutive_losses = 0
                self.halted_for_day = False

    def on_close(self, pnl: Decimal) -> None:
        with self._lock:
            self.realized_pnl += pnl
            if pnl < 0:
                self.consecutive_losses += 1
                if self.consecutive_losses >= self.limits.circuit_breaker_losses:
                    self.halted_for_day = True
            else:
                self.consecutive_losses = 0

    def try_reserve(
        self,
        symbol: str,
        *,
        notional: Decimal,
        risk_amount: Decimal,
        equity: Decimal,
    ) -> tuple[bool, str]:
        key = symbol.upper()
        if notional <= 0 or risk_amount <= 0:
            return False, "invalid_exposure"
        with self._lock:
            daily_cap = equity * Decimal(str(self.limits.max_daily_loss_pct)) / Decimal("100")
            if self.halted_for_day:
                return False, "portfolio_circuit_breaker"
            if equity > 0 and self.realized_pnl <= -daily_cap:
                return False, "portfolio_daily_loss"
            if key in self._reservations:
                return False, "symbol_already_reserved"
            if len(self._reservations) >= self.limits.max_concurrent_positions:
                return False, "max_concurrent_positions"
            gross = sum((r.notional for r in self._reservations.values()), Decimal("0"))
            if gross + notional > self.limits.max_gross_notional:
                return False, "max_gross_notional"
            cluster = self.clusters.get(key, "unclassified")
            if sum(r.cluster == cluster for r in self._reservations.values()) >= self.limits.max_positions_per_cluster:
                return False, "max_positions_per_cluster"
            risk_cap = equity * Decimal(str(self.limits.max_portfolio_risk_pct)) / Decimal("100")
            current_risk = sum((r.risk_amount for r in self._reservations.values()), Decimal("0"))
            if equity > 0 and current_risk + risk_amount > risk_cap:
                return False, "max_portfolio_risk_pct"
            self._reservations[key] = ExposureReservation(
                symbol=key,
                cluster=cluster,
                asset_class=self.asset_classes.get(key, "crypto"),
                notional=notional,
                risk_amount=risk_amount,
            )
            return True, "reserved"

    def release(self, symbol: str) -> None:
        with self._lock:
            self._reservations.pop(symbol.upper(), None)

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            rows = list(self._reservations.values())
        return {
            "positions": len(rows),
            "gross_notional": sum((r.notional for r in rows), Decimal("0")),
            "risk_amount": sum((r.risk_amount for r in rows), Decimal("0")),
            "symbols": sorted(r.symbol for r in rows),
            "realized_pnl": self.realized_pnl,
            "halted_for_day": self.halted_for_day,
        }
