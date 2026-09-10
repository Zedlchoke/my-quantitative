"""Instrument-metadata goldens for the seven G10 pairs (owner: A3).

Hand-computed, self-contained: all seven pairs resolve; pip sizes are
0.0001 with 0.01 for the JPY quote; unknown symbols fail closed; the
instrument digest is stable across calls and distinct per symbol; and the
inverse-pair flag is True exactly for the USD-base conventions
(USDJPY, USDCAD, USDCHF) and False for the USD-quote conventions
(EURUSD, GBPUSD, AUDUSD, NZDUSD).
"""

from __future__ import annotations

import re

import pytest

from research.assets.common.contracts import canonical_json
from research.assets.forex.instruments import (
    ALL_SYMBOLS,
    FX_PAIRS,
    ForexPair,
    all_instrument_digests,
    instrument_digest,
    lookup_symbol,
)

EXPECTED = {
    # symbol:  (base, quote, pip, inverse_usd_pair)
    "EURUSD": ("EUR", "USD", 0.0001, False),
    "GBPUSD": ("GBP", "USD", 0.0001, False),
    "USDJPY": ("USD", "JPY", 0.01, True),
    "AUDUSD": ("AUD", "USD", 0.0001, False),
    "USDCAD": ("USD", "CAD", 0.0001, True),
    "USDCHF": ("USD", "CHF", 0.0001, True),
    "NZDUSD": ("NZD", "USD", 0.0001, False),
}


def test_all_seven_pairs_resolve_with_expected_conventions():
    assert tuple(sorted(EXPECTED)) == ALL_SYMBOLS == tuple(sorted(FX_PAIRS))
    for symbol, (base, quote, _pip, _inverse) in EXPECTED.items():
        pair = lookup_symbol(symbol)
        assert isinstance(pair, ForexPair)
        assert pair.symbol == symbol
        assert pair.base_currency == base
        assert pair.quote_currency == quote
        assert pair.symbol == pair.base_currency + pair.quote_currency


def test_pip_sizes_jpy_quote_is_point_zero_one_others_point_zero_zero_zero_one():
    for symbol, (_base, _quote, pip, _inverse) in EXPECTED.items():
        assert lookup_symbol(symbol).pip_size == pip
    assert lookup_symbol("USDJPY").pip_size == 0.01  # the only JPY quote
    for symbol in ("EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"):
        assert lookup_symbol(symbol).pip_size == 0.0001


def test_tick_size_display_precision_and_size_increment():
    for symbol, (_base, _quote, pip, _inverse) in EXPECTED.items():
        pair = lookup_symbol(symbol)
        # fractional-pip convention: tick is one tenth of a pip
        assert pair.tick_size * 10 == pytest.approx(pip)
        expected_precision = 3 if symbol == "USDJPY" else 5
        assert pair.display_precision == expected_precision
        assert pair.size_increment == 1.0


def test_inverse_pair_flags_match_usd_quote_conventions():
    for symbol, (_base, _quote, _pip, inverse) in EXPECTED.items():
        pair = lookup_symbol(symbol)
        assert pair.is_inverse_usd_pair is inverse
        # flag consistency: True iff USD is the base currency
        assert pair.is_inverse_usd_pair == (pair.base_currency == "USD")
    assert [s for s, p in FX_PAIRS.items() if p.is_inverse_usd_pair] == [
        "USDJPY",  # registry insertion order: EURUSD, GBPUSD, USDJPY, ...
        "USDCAD",
        "USDCHF",
    ]
    assert [s for s, p in FX_PAIRS.items() if not p.is_inverse_usd_pair] == [
        "EURUSD",
        "GBPUSD",
        "AUDUSD",
        "NZDUSD",
    ]


def test_unknown_symbol_fails_closed():
    for bad in ("EURGBP", "eurusd", "EURUSDX", "USD/JPY", "", "  ", None, 42):
        with pytest.raises(ValueError):
            lookup_symbol(bad)
    with pytest.raises(ValueError):
        instrument_digest("EURGBP")


def test_digest_stable_across_calls_and_distinct_per_symbol():
    first = instrument_digest("EURUSD")
    assert first == instrument_digest("EURUSD")  # stable across calls
    assert re.fullmatch(r"[0-9a-f]{64}", first)
    digests = all_instrument_digests()
    assert tuple(sorted(digests)) == ALL_SYMBOLS
    assert len(set(digests.values())) == len(ALL_SYMBOLS)  # distinct per symbol
    assert digests["EURUSD"] == lookup_symbol("EURUSD").digest()
    assert instrument_digest("USDJPY") != first


def test_digest_binds_every_convention_field():
    pair = lookup_symbol("EURUSD")
    payload = pair.canonical_payload()
    assert payload["schema"] == "forex_instrument"
    assert payload["version"] == 1
    assert payload["fields"]["pip_size"] == 0.0001
    assert payload["fields"]["is_inverse_usd_pair"] is False
    # canonical JSON is byte-stable, so the digest is reproducible by hand
    import hashlib

    assert pair.digest() == hashlib.sha256(
        canonical_json(payload).encode("utf-8")
    ).hexdigest()


def test_registry_is_read_only_and_records_are_frozen():
    with pytest.raises(TypeError):
        FX_PAIRS["EURGBP"] = lookup_symbol("EURUSD")  # type: ignore[index]
    pair = lookup_symbol("USDJPY")
    with pytest.raises(AttributeError):
        pair.pip_size = 0.0001  # type: ignore[misc]
    with pytest.raises(ValueError):
        ForexPair(
            symbol="USDJPY",
            base_currency="USD",
            quote_currency="JPY",
            pip_size=0.01,
            tick_size=0.001,
            size_increment=1.0,
            display_precision=3,
            is_inverse_usd_pair=False,  # contradicts USD base -> construction error
        )
    with pytest.raises(ValueError):
        ForexPair(
            symbol="EURXX",
            base_currency="EUR",
            quote_currency="XX",  # not a 3-letter currency code
            pip_size=0.0001,
            tick_size=0.00001,
            size_increment=1.0,
            display_precision=5,
            is_inverse_usd_pair=False,
        )
