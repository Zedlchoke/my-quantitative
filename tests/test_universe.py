from __future__ import annotations

from datetime import datetime
from datetime import timezone
from unittest import TestCase

from data.universe import UniverseFilters
from data.universe import build_universe_snapshot


AS_OF = datetime(2026, 8, 21, tzinfo=timezone.utc)
DAY_MS = 86_400_000


def _symbol(symbol: str, *, days: int = 500, contract_type: str = "PERPETUAL", underlying="COIN") -> dict:
    return {
        "symbol": symbol,
        "pair": symbol,
        "baseAsset": symbol.removesuffix("USDT"),
        "quoteAsset": "USDT",
        "marginAsset": "USDT",
        "contractType": contract_type,
        "underlyingType": underlying,
        "status": "TRADING",
        "onboardDate": int(AS_OF.timestamp() * 1000) - days * DAY_MS,
    }


def _ticker(symbol: str, volume: float = 100_000_000, trades: int = 20_000) -> dict:
    return {
        "symbol": symbol,
        "quoteVolume": str(volume),
        "count": trades,
        "priceChangePercent": "1.25",
    }


class UniverseTests(TestCase):
    def test_filters_history_and_liquidity_with_reasons(self) -> None:
        exchange = {"symbols": [_symbol("SOLUSDT"), _symbol("NEWUSDT", days=20)]}
        snapshot = build_universe_snapshot(
            exchange,
            [_ticker("SOLUSDT"), _ticker("NEWUSDT", volume=1_000)],
            as_of=AS_OF,
        )
        self.assertEqual(snapshot["eligible_symbols"], ["SOLUSDT"])
        rejected = next(row for row in snapshot["contracts"] if row["symbol"] == "NEWUSDT")
        self.assertEqual(rejected["rejection_reasons"], ["insufficient_history", "low_quote_volume"])

    def test_tradfi_is_opt_in_and_classified(self) -> None:
        exchange = {
            "symbols": [
                _symbol(
                    "SPYUSDT",
                    contract_type="TRADIFI_PERPETUAL",
                    underlying="EQUITY",
                ),
            ],
        }
        default = build_universe_snapshot(exchange, [_ticker("SPYUSDT")], as_of=AS_OF)
        self.assertFalse(default["contracts"][0]["eligible"])
        enabled = build_universe_snapshot(
            exchange,
            [_ticker("SPYUSDT")],
            filters=UniverseFilters(include_crypto=False, include_tradfi=True),
            as_of=AS_OF,
        )
        self.assertEqual(enabled["eligible_symbols"], ["SPYUSDT"])
        self.assertEqual(enabled["contracts"][0]["cluster"], "equity")
