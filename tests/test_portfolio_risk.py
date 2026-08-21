from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest import TestCase

from risk.portfolio import PortfolioRiskLimits
from risk.portfolio import PortfolioRiskManager


class PortfolioRiskManagerTests(TestCase):
    def _manager(self, **overrides) -> PortfolioRiskManager:
        values = {
            "max_gross_notional": Decimal("1000"),
            "max_portfolio_risk_pct": 3.0,
            "max_concurrent_positions": 3,
            "max_positions_per_cluster": 1,
            "max_daily_loss_pct": 2.0,
            "circuit_breaker_losses": 3,
        }
        values.update(overrides)
        return PortfolioRiskManager(
            PortfolioRiskLimits(**values),
            clusters={"SOLUSDT": "layer1", "BNBUSDT": "layer1", "XRPUSDT": "payments"},
        )

    def test_blocks_second_symbol_in_same_cluster(self) -> None:
        manager = self._manager()
        self.assertTrue(manager.try_reserve("SOLUSDT", notional=Decimal("200"), risk_amount=Decimal("10"), equity=Decimal("1000"))[0])
        allowed, reason = manager.try_reserve("BNBUSDT", notional=Decimal("200"), risk_amount=Decimal("10"), equity=Decimal("1000"))
        self.assertFalse(allowed)
        self.assertEqual(reason, "max_positions_per_cluster")

    def test_blocks_gross_notional_and_total_risk(self) -> None:
        manager = self._manager(max_positions_per_cluster=2)
        self.assertTrue(manager.try_reserve("SOLUSDT", notional=Decimal("700"), risk_amount=Decimal("10"), equity=Decimal("1000"))[0])
        self.assertEqual(manager.try_reserve("XRPUSDT", notional=Decimal("400"), risk_amount=Decimal("10"), equity=Decimal("1000"))[1], "max_gross_notional")
        manager.release("SOLUSDT")
        self.assertTrue(manager.try_reserve("SOLUSDT", notional=Decimal("200"), risk_amount=Decimal("25"), equity=Decimal("1000"))[0])
        self.assertEqual(manager.try_reserve("XRPUSDT", notional=Decimal("200"), risk_amount=Decimal("10"), equity=Decimal("1000"))[1], "max_portfolio_risk_pct")

    def test_release_returns_budget(self) -> None:
        manager = self._manager(max_concurrent_positions=1)
        manager.try_reserve("SOLUSDT", notional=Decimal("100"), risk_amount=Decimal("5"), equity=Decimal("1000"))
        manager.release("SOLUSDT")
        self.assertTrue(manager.try_reserve("XRPUSDT", notional=Decimal("100"), risk_amount=Decimal("5"), equity=Decimal("1000"))[0])

    def test_daily_loss_and_global_loss_streak_halt_entries(self) -> None:
        manager = self._manager(max_positions_per_cluster=2)
        manager.roll_day(date(2026, 8, 21))
        manager.on_close(Decimal("-25"))
        self.assertEqual(
            manager.try_reserve("SOLUSDT", notional=Decimal("100"), risk_amount=Decimal("5"), equity=Decimal("1000"))[1],
            "portfolio_daily_loss",
        )
        manager.roll_day(date(2026, 8, 22))
        for _ in range(3):
            manager.on_close(Decimal("-1"))
        self.assertEqual(
            manager.try_reserve("SOLUSDT", notional=Decimal("100"), risk_amount=Decimal("5"), equity=Decimal("1000"))[1],
            "portfolio_circuit_breaker",
        )
