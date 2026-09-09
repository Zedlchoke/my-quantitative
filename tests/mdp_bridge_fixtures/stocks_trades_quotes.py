"""SYNTHETIC stock trades + quotes for the nautilus bridge (AAPL-like).

24 canonical events (12 TRADEs + 12 QUOTEs), price precision 2 (tick 0.01)
and size precision 1 (0.1-share lots), on instrument ``AAPL.XNAS``.

nautilus_trader 1.230.0 fact (verified, see docs/MDP_BRIDGE_NOTES.md): the
``Equity`` instrument type hard-pins ``size_precision = 0`` and exposes no
constructor parameter for it, so the 2dp/1dp stock fixture uses a ``Cfd``
instrument with ``AssetClass.EQUITY`` as its nautilus test instrument.  The
bridge itself is instrument-type agnostic (it reads ``.id``,
``.price_precision``, ``.size_precision``).  Purely synthetic — zero data
authority.
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

SOURCE_ID = "synthetic-equity-tape"
VENUE = "XNAS"
INSTRUMENT_ID = "AAPL.XNAS"
PRICE_PRECISION = 2   # tick 0.01
SIZE_PRECISION = 1    # 0.1-share lots
CURRENCY = "USD"

_BASE_EXCHANGE_NS = 1_700_000_300_000_000_000
_RECEIVE_LAG_NS = 4_000_000        # +4 ms
_AVAILABLE_LAG_NS = 2_000_000      # +2 ms after receive
_STEP_NS = 100_000_000             # one synthetic event per 100 ms


def _price_string(step: int) -> str:
    """Deterministic 2dp price (integer cents); strictly canonical form."""
    cents = 182_00 + 11 * step + (step % 5)
    return f"{cents // 100}.{cents % 100:02d}"


def _size_string(step: int) -> str:
    """Deterministic 1dp size (integer tenths); canonical form."""
    tenths = 300 + 17 * step + (step % 3)
    return f"{tenths // 10}.{tenths % 10}"


def events() -> list[dict]:
    """24 canonical events: 22 VALID + 2 SUSPECT (one STALE_QUOTE, one
    OUT_OF_ORDER_DELIVERY) — all streamable through the quality gate."""
    out = []
    for i in range(12):
        event = make_event(
            event_type="TRADE",
            source_id=SOURCE_ID,
            venue=VENUE,
            instrument_id=INSTRUMENT_ID,
            exchange_ns=_BASE_EXCHANGE_NS + 2 * i * _STEP_NS,
            receive_ns=_BASE_EXCHANGE_NS + 2 * i * _STEP_NS + _RECEIVE_LAG_NS,
            available_ns=(
                _BASE_EXCHANGE_NS + 2 * i * _STEP_NS + _RECEIVE_LAG_NS
                + _AVAILABLE_LAG_NS),
            sequence_number=2 * i,
            price_precision=PRICE_PRECISION,
            size_precision=SIZE_PRECISION,
            raw_id=f"synthetic-stock-trade-{i:04d}",
            raw_sha256=synthetic_raw_sha256("stock-trade", i),
            manifest_sha256=synthetic_manifest_sha256("stocks"),
            currency=CURRENCY,
            price=_price_string(2 * i),
            quantity=_size_string(2 * i),
            # side optional: indices 3 and 9 carry no side
            side=None if i in (3, 9) else ("buy" if i % 2 == 0 else "sell"),
        )
        # post-evaluation label: build_event defaults to QUARANTINED (nothing
        # is VALID merely because parsing succeeded), so fixtures label the
        # evaluated streaming set explicitly (status consistent with codes).
        event = models.set_quality(event, "VALID", [])
        if i == 6:  # SUSPECT trade streams through the bridge (recorded)
            event = models.set_quality(event, "SUSPECT",
                                       ["OUT_OF_ORDER_DELIVERY"])
        out.append(event)
    for i in range(12):
        event = make_event(
            event_type="QUOTE",
            source_id=SOURCE_ID,
            venue=VENUE,
            instrument_id=INSTRUMENT_ID,
            exchange_ns=_BASE_EXCHANGE_NS + (2 * i + 1) * _STEP_NS,
            receive_ns=(
                _BASE_EXCHANGE_NS + (2 * i + 1) * _STEP_NS + _RECEIVE_LAG_NS),
            available_ns=(
                _BASE_EXCHANGE_NS + (2 * i + 1) * _STEP_NS + _RECEIVE_LAG_NS
                + _AVAILABLE_LAG_NS),
            sequence_number=2 * i + 1,
            price_precision=PRICE_PRECISION,
            size_precision=SIZE_PRECISION,
            raw_id=f"synthetic-stock-quote-{i:04d}",
            raw_sha256=synthetic_raw_sha256("stock-quote", i),
            manifest_sha256=synthetic_manifest_sha256("stocks"),
            currency=CURRENCY,
            bid_price=_price_string(2 * i + 1),
            ask_price=_price_string(2 * i + 2),
            bid_size=_size_string(2 * i + 1),
            ask_size=_size_string(2 * i + 3),
        )
        event = models.set_quality(event, "VALID", [])
        if i == 5:  # SUSPECT quote streams through the bridge (recorded)
            event = models.set_quality(event, "SUSPECT", ["STALE_QUOTE"])
        out.append(event)
    return out


def invalid_event() -> dict:
    """INVALID-labelled quote for quality-gate tests (assessment-level code)."""
    return invalid_variant(events()[13], ["SOURCE_RESET_UNEVIDENCED"])


def quarantined_event() -> dict:
    """QUARANTINED-labelled trade for quality-gate tests."""
    return quarantined_variant(events()[0], ["QUARANTINE_ORPHAN"])


def instrument_metadata() -> dict:
    """id/precisions for building the matching nautilus test instrument."""
    return {
        "instrument_id": INSTRUMENT_ID,
        "raw_symbol": "AAPL",
        "venue": VENUE,
        "asset_class": "equity",
        "quote_currency": CURRENCY,
        "price_precision": PRICE_PRECISION,
        "size_precision": SIZE_PRECISION,
        "price_increment": "0.01",
        "size_increment": "0.1",
        "nautilus_type": "Cfd(AssetClass.EQUITY)",
        "nautilus_provider_hint":
            "Cfd(InstrumentId(Symbol('AAPL'), Venue('XNAS')), Symbol('AAPL'), "
            "AssetClass.EQUITY, USD, 2, 1, Price(Decimal('0.01'), 2), "
            "Quantity(Decimal('0.1'), 1), ts_event, ts_init) — nautilus "
            "1.230.0 Equity hard-pins size_precision=0 (no ctor parameter)",
        "normalizer_version": FIXTURE_NORMALIZER_VERSION,
        "data_authority": "NONE — synthetic, proves code semantics only",
    }
