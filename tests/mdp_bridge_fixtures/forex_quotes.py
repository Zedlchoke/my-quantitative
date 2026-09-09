"""SYNTHETIC forex quotes for the nautilus bridge (EUR/USD-like).

20 canonical QUOTE events, price precision 5 (pip fractions, tick 0.00001)
and size precision 0 (whole-number lots), matching the nautilus 1.230.0 test
instrument ``TestInstrumentProvider.default_fx_ccy('EUR/USD')``
(CurrencyPair ``EUR/USD.SIM``).  Purely synthetic — zero data authority.
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

SOURCE_ID = "synthetic-fx-spot"
VENUE = "SIM"
INSTRUMENT_ID = "EUR/USD.SIM"
PRICE_PRECISION = 5   # tick 0.00001
SIZE_PRECISION = 0    # whole lots
CURRENCY = "USD"

_BASE_EXCHANGE_NS = 1_700_000_200_000_000_000
_RECEIVE_LAG_NS = 3_000_000        # +3 ms
_AVAILABLE_LAG_NS = 2_000_000      # +2 ms after receive
_STEP_NS = 500_000_000             # one synthetic quote per 500 ms


def _bid_ask_strings(i: int) -> tuple[str, str]:
    """Deterministic 5dp bid/ask with a strictly positive spread (never crossed).

    Bid/ask carried as integer 1e-5 units: bid ~1.085xx walking with the
    index; the spread is a constant 10 units (0.00010).
    """
    bid_units = 108_540 + 2 * i - (i % 4)
    ask_units = bid_units + 10
    return (f"{bid_units // 100000}.{bid_units % 100000:05d}",
            f"{ask_units // 100000}.{ask_units % 100000:05d}")


def events() -> list[dict]:
    """20 canonical QUOTE events: 19 VALID + 1 SUSPECT (STALE_QUOTE)."""
    out = []
    for i in range(20):
        bid, ask = _bid_ask_strings(i)
        # integer lot sizes, canonical at size_precision 0 (no '.0' padding)
        bid_size = str(1 + (i % 5))
        ask_size = str(2 + (i % 3))
        event = make_event(
            event_type="QUOTE",
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
            raw_id=f"synthetic-fx-quote-{i:04d}",
            raw_sha256=synthetic_raw_sha256("fx-quote", i),
            manifest_sha256=synthetic_manifest_sha256("fx-quotes"),
            currency=CURRENCY,
            bid_price=bid,
            ask_price=ask,
            bid_size=bid_size,
            ask_size=ask_size,
        )
        # post-evaluation label: build_event defaults to QUARANTINED (nothing
        # is VALID merely because parsing succeeded), so fixtures label the
        # evaluated streaming set explicitly (status consistent with codes).
        event = models.set_quality(event, "VALID", [])
        if i == 7:  # one SUSPECT event streams through the bridge (recorded)
            event = models.set_quality(event, "SUSPECT", ["STALE_QUOTE"])
        out.append(event)
    return out


def invalid_event() -> dict:
    """Field-consistent INVALID quote: the bid/ask pair is genuinely crossed
    (bid == ask) and labelled with the frozen CROSSED_QUOTE code."""
    crossed = make_event(
        event_type="QUOTE",
        source_id=SOURCE_ID,
        venue=VENUE,
        instrument_id=INSTRUMENT_ID,
        exchange_ns=_BASE_EXCHANGE_NS,
        receive_ns=_BASE_EXCHANGE_NS + _RECEIVE_LAG_NS,
        available_ns=_BASE_EXCHANGE_NS + _RECEIVE_LAG_NS + _AVAILABLE_LAG_NS,
        sequence_number=999,
        price_precision=PRICE_PRECISION,
        size_precision=SIZE_PRECISION,
        raw_id="synthetic-fx-quote-crossed-0000",
        raw_sha256=synthetic_raw_sha256("fx-quote", 9001),
        manifest_sha256=synthetic_manifest_sha256("fx-quotes"),
        currency=CURRENCY,
        bid_price="1.08540",
        ask_price="1.08540",
        bid_size="1",
        ask_size="1",
    )
    return invalid_variant(crossed, ["CROSSED_QUOTE"])


def quarantined_event() -> dict:
    """QUARANTINED-labelled quote for quality-gate tests."""
    return quarantined_variant(events()[2], ["QUARANTINE_ORPHAN"])


def instrument_metadata() -> dict:
    """id/precisions for building the matching nautilus test instrument."""
    return {
        "instrument_id": INSTRUMENT_ID,
        "raw_symbol": "EUR/USD",
        "venue": VENUE,
        "asset_class": "fx_spot",
        "base_currency": "EUR",
        "quote_currency": CURRENCY,
        "price_precision": PRICE_PRECISION,
        "size_precision": SIZE_PRECISION,
        "price_increment": "0.00001",
        "size_increment": "1",
        "nautilus_type": "CurrencyPair",
        "nautilus_provider_hint":
            "nautilus_trader.test_kit.providers.TestInstrumentProvider"
            ".default_fx_ccy('EUR/USD')",
        "normalizer_version": FIXTURE_NORMALIZER_VERSION,
        "data_authority": "NONE — synthetic, proves code semantics only",
    }
