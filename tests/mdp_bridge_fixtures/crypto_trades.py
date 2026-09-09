"""SYNTHETIC crypto perpetual trades for the nautilus bridge (BTC-PERP-like).

20 canonical TRADE events, price precision 1 (tick 0.1) and size precision 3
(step 0.001), matching the nautilus 1.230.0 test instrument
``TestInstrumentProvider.btcusdt_perp_binance()`` (CryptoPerpetual
``BTCUSDT-PERP.BINANCE``).  Purely synthetic — zero data authority.
"""

from __future__ import annotations

from market_data_plane import models

from . import (
    FIXTURE_NORMALIZER_VERSION,
    invalid_variant,
    make_event,
    quarantined_variant,
    synthetic_manifest_sha256,
    synthetic_raw_sha256,
)

__all__ = [
    "events",
    "invalid_event",
    "instrument_metadata",
    "quarantined_event",
]

SOURCE_ID = "synthetic-crypto-perp"
VENUE = "BINANCE"
INSTRUMENT_ID = "BTCUSDT-PERP.BINANCE"
PRICE_PRECISION = 1   # tick 0.1
SIZE_PRECISION = 3    # step 0.001
CURRENCY = "USDT"

_BASE_EXCHANGE_NS = 1_700_000_100_000_000_000
_RECEIVE_LAG_NS = 5_000_000        # +5 ms
_AVAILABLE_LAG_NS = 1_000_000      # +1 ms after receive
_STEP_NS = 250_000_000             # one synthetic trade per 250 ms


def _price_string(i: int) -> str:
    """Deterministic 1dp price (integer tenths); strictly canonical form."""
    tenths = 265_000 + 7 * i + (i % 3)   # ~26500.x walking with the index
    return f"{tenths // 10}.{tenths % 10}"


def _quantity_string(i: int) -> str:
    """Deterministic 3dp size (integer thousandths); canonical form."""
    millis = 1_500 + 13 * i + (i % 7)
    return f"{millis // 1000}.{millis % 1000:03d}"


def events() -> list[dict]:
    """20 canonical TRADE events: 19 VALID + 1 SUSPECT (STATISTICAL_ANOMALY)."""
    out = []
    for i in range(20):
        # side optional per the frozen matrix: index 5 and 11 carry no side
        side = None if i in (5, 11) else ("buy" if i % 2 == 0 else "sell")
        event = make_event(
            event_type="TRADE",
            source_id=SOURCE_ID,
            venue=VENUE,
            instrument_id=INSTRUMENT_ID,
            exchange_ns=_BASE_EXCHANGE_NS + i * _STEP_NS,
            receive_ns=_BASE_EXCHANGE_NS + i * _STEP_NS + _RECEIVE_LAG_NS,
            available_ns=(
                _BASE_EXCHANGE_NS + i * _STEP_NS + _RECEIVE_LAG_NS
                + _AVAILABLE_LAG_NS),
            sequence_number=i,
            price_precision=PRICE_PRECISION,
            size_precision=SIZE_PRECISION,
            raw_id=f"synthetic-crypto-trade-{i:04d}",
            raw_sha256=synthetic_raw_sha256("crypto-trade", i),
            manifest_sha256=synthetic_manifest_sha256("crypto-trades"),
            currency=CURRENCY,
            price=_price_string(i),
            quantity=_quantity_string(i),
            side=side,
        )
        # post-evaluation label: build_event defaults to QUARANTINED (nothing
        # is VALID merely because parsing succeeded), so fixtures label the
        # evaluated streaming set explicitly (status consistent with codes).
        event = models.set_quality(event, "VALID", [])
        if i == 13:  # one SUSPECT event streams through the bridge (recorded)
            event = models.set_quality(event, "SUSPECT",
                                       ["STATISTICAL_ANOMALY"])
        out.append(event)
    return out


def invalid_event() -> dict:
    """INVALID-labelled trade for quality-gate tests (assessment-level code)."""
    return invalid_variant(events()[0], ["SOURCE_RESET_UNEVIDENCED"])


def quarantined_event() -> dict:
    """QUARANTINED-labelled trade for quality-gate tests."""
    return quarantined_variant(events()[1], ["QUARANTINE_ORPHAN"])


def instrument_metadata() -> dict:
    """id/precisions for building the matching nautilus test instrument."""
    return {
        "instrument_id": INSTRUMENT_ID,
        "raw_symbol": "BTCUSDT-PERP",
        "venue": VENUE,
        "asset_class": "crypto_perpetual",
        "base_currency": "BTC",
        "quote_currency": CURRENCY,
        "price_precision": PRICE_PRECISION,
        "size_precision": SIZE_PRECISION,
        "price_increment": "0.1",
        "size_increment": "0.001",
        "nautilus_type": "CryptoPerpetual",
        "nautilus_provider_hint":
            "nautilus_trader.test_kit.providers.TestInstrumentProvider"
            ".btcusdt_perp_binance()",
        "normalizer_version": FIXTURE_NORMALIZER_VERSION,
        "data_authority": "NONE — synthetic, proves code semantics only",
    }
