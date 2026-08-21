from __future__ import annotations

from unittest import TestCase

from data.tradfi import TradfiSessionGate


class TradfiSessionGateTests(TestCase):
    def test_allows_only_configured_session_and_fails_closed(self) -> None:
        payload = {
            "marketSchedules": {
                "EQUITY": {
                    "sessions": [
                        {"startTime": 1000, "endTime": 2000, "type": "REGULAR"},
                        {"startTime": 2000, "endTime": 3000, "type": "NO_TRADING"},
                    ],
                },
            },
        }
        gate = TradfiSessionGate.from_payload(payload, market_type="EQUITY")
        self.assertTrue(gate.allows(1_500_000_000))
        self.assertFalse(gate.allows(2_500_000_000))
        self.assertFalse(gate.allows(4_000_000_000))

    def test_missing_market_has_no_allowed_time(self) -> None:
        gate = TradfiSessionGate.from_payload({"marketSchedules": {}}, market_type="EQUITY")
        self.assertFalse(gate.allows(1_500_000_000))
