from __future__ import annotations

from decimal import Decimal
from unittest import TestCase
from unittest.mock import patch

from data.derivatives import fetch_open_interest_history
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


class OpenInterestHistoryTests(TestCase):
    @patch("data.derivatives._request")
    def test_paginates_until_short_page(self, request) -> None:
        period_ms = 15 * 60_000
        first = [{"timestamp": str(index * period_ms)} for index in range(501, 1_001)]
        second = [{"timestamp": str(500 * period_ms)}]
        request.side_effect = [first, second]

        rows = fetch_open_interest_history(
            "SOLUSDT",
            start_ms=1,
            end_ms=1_000 * period_ms,
            base_url="https://example.test",
        )

        self.assertEqual(len(rows), 501)
        self.assertEqual(request.call_count, 2)
        self.assertEqual(request.call_args_list[1].args[1]["endTime"], 500 * period_ms)

    def test_rejects_unknown_period(self) -> None:
        with self.assertRaises(ValueError):
            fetch_open_interest_history("SOLUSDT", start_ms=1, end_ms=2, period="7m")
