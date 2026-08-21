from __future__ import annotations

from decimal import Decimal
from unittest import TestCase

from data.derivatives import funding_cashflow


class FundingCashflowTests(TestCase):
    def test_positive_rate_long_pays_and_short_receives(self) -> None:
        self.assertEqual(
            funding_cashflow(
                side="LONG",
                position_notional=Decimal("1000"),
                funding_rate=Decimal("0.0001"),
            ),
            Decimal("-0.1000"),
        )
        self.assertEqual(
            funding_cashflow(
                side="SHORT",
                position_notional=Decimal("1000"),
                funding_rate=Decimal("0.0001"),
            ),
            Decimal("0.1000"),
        )

    def test_negative_rate_reverses_cashflow(self) -> None:
        self.assertGreater(
            funding_cashflow(
                side="LONG",
                position_notional=Decimal("500"),
                funding_rate=Decimal("-0.001"),
            ),
            0,
        )

    def test_rejects_unknown_side(self) -> None:
        with self.assertRaises(ValueError):
            funding_cashflow(side="FLAT", position_notional=Decimal("1"), funding_rate=Decimal("1"))
