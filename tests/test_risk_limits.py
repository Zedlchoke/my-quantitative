from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest import TestCase

from risk.limits import DailyRiskTracker
from risk.limits import RiskLimits


def _limits(**overrides) -> RiskLimits:
    values = dict(
        risk_per_trade=Decimal("5"),
        max_notional=Decimal("100"),
        max_daily_loss=Decimal("20"),
        max_trades_per_day=4,
        cooldown_bars_after_loss=3,
        atr_stop_multiple=2.0,
        leverage=3,
    )
    values.update(overrides)
    return RiskLimits(**values)


class RiskLimitsTests(TestCase):
    def test_quantity_is_risk_over_stop_distance(self) -> None:
        qty = _limits().position_quantity(close=Decimal("100"), atr=5.0)
        # stop distance = 5 * 2 = 10; 5 / 10 = 0.5; notional cap = 100/100 = 1
        self.assertEqual(qty, Decimal("0.5"))

    def test_quantity_capped_by_max_notional(self) -> None:
        qty = _limits(max_notional=Decimal("10")).position_quantity(
            close=Decimal("100"),
            atr=0.1,
        )
        self.assertEqual(qty, Decimal("0.1"))

    def test_zero_when_atr_non_positive(self) -> None:
        self.assertEqual(
            _limits().position_quantity(close=Decimal("100"), atr=0.0),
            Decimal("0"),
        )

    def test_stop_multiple_override(self) -> None:
        qty = _limits().position_quantity(
            close=Decimal("100"),
            atr=5.0,
            stop_multiple=1.0,
        )
        self.assertEqual(qty, Decimal("1"))

    def test_pct_equity_risk(self) -> None:
        qty = _limits(risk_pct_per_trade=1.0).position_quantity(
            close=Decimal("100"),
            atr=5.0,
            equity=Decimal("10000"),
        )
        # 1% of 10k = 100 risk; stop = 10; qty = 10; notional cap = 100/100 = 1
        self.assertEqual(qty, Decimal("1"))

    def test_pct_equity_capped_by_max_risk(self) -> None:
        qty = _limits(
            risk_pct_per_trade=2.0,
            max_risk_per_trade_usdt=Decimal("10"),
        ).position_quantity(
            close=Decimal("100"),
            atr=5.0,
            equity=Decimal("10000"),
        )
        # capped at 10 USDT risk → qty 1
        self.assertEqual(qty, Decimal("1"))


class DailyRiskTrackerTests(TestCase):
    def test_blocks_after_max_trades(self) -> None:
        tracker = DailyRiskTracker(_limits(max_trades_per_day=2))
        tracker.roll_day(date(2026, 1, 1))
        tracker.on_open()
        tracker.on_open()
        self.assertFalse(tracker.can_open())

    def test_blocks_after_daily_loss(self) -> None:
        tracker = DailyRiskTracker(_limits(max_daily_loss=Decimal("5")))
        tracker.roll_day(date(2026, 1, 1))
        tracker.on_close(-5.0)
        self.assertFalse(tracker.can_open())

    def test_cooldown_after_loss_and_ticks_down(self) -> None:
        tracker = DailyRiskTracker(_limits(cooldown_bars_after_loss=2))
        tracker.roll_day(date(2026, 1, 1))
        tracker.on_close(-1.0)
        self.assertFalse(tracker.can_open())
        tracker.tick_cooldown()
        self.assertFalse(tracker.can_open())
        tracker.tick_cooldown()
        self.assertTrue(tracker.can_open())

    def test_new_utc_day_resets_pnl_trades_and_cooldown(self) -> None:
        tracker = DailyRiskTracker(_limits(cooldown_bars_after_loss=9))
        tracker.roll_day(date(2026, 1, 1))
        tracker.on_open()
        tracker.on_close(-3.0)
        tracker.roll_day(date(2026, 1, 2))
        self.assertEqual(tracker.trade_count, 0)
        self.assertEqual(tracker.realized_pnl, 0.0)
        self.assertEqual(tracker.cooldown_remaining, 0)
        self.assertTrue(tracker.can_open())

    def test_circuit_breaker_pauses_after_consecutive_losses(self) -> None:
        tracker = DailyRiskTracker(
            _limits(circuit_breaker_losses=3, circuit_breaker_pause_bars=5),
        )
        tracker.roll_day(date(2026, 1, 1))
        for _ in range(3):
            tracker.on_close(-1.0)
        self.assertFalse(tracker.can_open())
        self.assertEqual(tracker.circuit_pause_remaining, 5)
        for _ in range(5):
            tracker.tick_cooldown()
        self.assertTrue(tracker.can_open())

    def test_pct_daily_loss_limit(self) -> None:
        tracker = DailyRiskTracker(_limits(max_daily_loss_pct=2.0))
        tracker.roll_day(date(2026, 1, 1))
        tracker.on_close(-150.0)
        self.assertFalse(tracker.can_open(Decimal("10000")))
