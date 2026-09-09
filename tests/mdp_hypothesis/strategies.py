"""Hypothesis strategies for MDP-V1 event/manifest/quality properties.

Generates valid AND invalid shapes exactly as the freeze requires: timestamp
order and equality boundaries, exact decimal precision and extreme magnitudes
(1e-8 .. 1e9), duplicate ids, sequence gaps/resets, out-of-order delivery,
naive timestamps, non-finite values, crossed/locked/stale quotes, unknown
event types and malformed shapes.  Invalid generators yield
``(event_dict, expected_frozen_reason_code)`` pairs so a property can assert
that validation fails with exactly the frozen code.  Random tests touch no
provider API, no raw licensed data, no ledger and no orders (freeze rule).

Note: ``reason_codes`` inputs are canonicalised (sorted + deduplicated) by the
models rather than rejected, so unsorted code lists are covered by a
canonicalisation property, not by an invalid-shape pair.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from decimal import Decimal

from hypothesis import strategies as st

SCHEMA_VERSION = "mdp.market_event@1"

_EPOCH_OFFSET_MAX = 4_000_000_000_000_000_000  # well inside int64 ns
_MAX_PRECISION = 12


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --- primitives -------------------------------------------------------------

def timestamps_ns():
    """Base UTC-ns timestamps plus non-negative offsets (0 => equality case)."""
    base = st.integers(min_value=0, max_value=_EPOCH_OFFSET_MAX)
    return st.tuples(base, st.integers(0, 10**9), st.integers(0, 10**9)).map(
        lambda t: (t[0], t[0] + t[1], t[0] + t[1] + t[2]))


def identifiers():
    return st.from_regex(r"[a-z0-9_]{1,12}", fullmatch=True)


def hex64():
    return st.from_regex(r"[0-9a-f]{64}", fullmatch=True)


def bounded_decimal(precision: int, min_value=Decimal("1e-8"),
                    max_value=Decimal("1e9"), min_mantissa: int = 0) -> Decimal:
    """Strategy for a Decimal with scale <= precision within [min, max].

    Zero is always a valid draw (it needs no precision); nonzero values below
    ``min_value`` are clamped up to ``min_value`` (whose scale 8 therefore
    requires precision >= 8 to be drawn, which the mantissa clamp enforces:
    for precision < 8 every positive value is >= 1e-<precision> >= 1e-8).
    """
    mantissa_max = min(int(max_value * (10 ** precision)), 10 ** 13)

    def _convert(m: int) -> Decimal:
        value = Decimal(m).scaleb(-precision)
        if value == 0:
            return value
        return min(max(value, min_value), max_value)

    return st.integers(min_value=min_mantissa, max_value=mantissa_max).map(_convert)


def decimal_strings(min_value=Decimal("1e-8"), max_value=Decimal("1e9"),
                    allow_zero=True):
    """Non-negative fixed-point decimal strings within [min, max].

    The string's scale is bounded by a jointly drawn declared precision, so a
    drawn value is always exactly representable at that precision (valid by
    construction).
    """

    @st.composite
    def _draw(draw):
        precision = draw(st.integers(min_value=0, max_value=_MAX_PRECISION))
        value = draw(bounded_decimal(precision, min_value, max_value,
                                     min_mantissa=0 if allow_zero else 1))
        return format(value, "f")

    return _draw()


# --- valid events -----------------------------------------------------------

@st.composite
def trade_fields(draw):
    price_precision = draw(st.integers(0, _MAX_PRECISION))
    size_precision = draw(st.integers(0, _MAX_PRECISION))
    ex, rc, av = draw(timestamps_ns())
    price = draw(bounded_decimal(price_precision))
    quantity = draw(bounded_decimal(size_precision))
    return {
        "raw_id": draw(identifiers()),
        "source_id": draw(identifiers()),
        "venue": draw(identifiers()),
        "instrument_id": draw(identifiers()),
        "asset_class": draw(st.sampled_from(["crypto", "forex", "stocks"])),
        "event_type": "TRADE",
        "exchange_time_utc_ns": ex,
        "receive_time_utc_ns": rc,
        "available_time_utc_ns": av,
        "sequence_number": draw(st.one_of(st.none(), st.integers(0, 2**40))),
        "price": format(price, "f"),
        "quantity": format(quantity, "f"),
        "side": draw(st.sampled_from(["buy", "sell", None])),
        "currency": draw(st.sampled_from(["USD", None])),
        "price_precision": price_precision,
        "size_precision": size_precision,
        "raw_sha256": draw(hex64()),
        "manifest_sha256": draw(st.one_of(st.none(), hex64())),
        "normalizer_version": draw(identifiers()),
    }


@st.composite
def quote_fields(draw):
    price_precision = draw(st.integers(1, _MAX_PRECISION))
    size_precision = draw(st.integers(0, _MAX_PRECISION))
    ex, rc, av = draw(timestamps_ns())
    # bid < ask strictly; both carry at most the declared precision.
    bid = draw(bounded_decimal(price_precision))
    tick = Decimal(draw(st.integers(min_value=1, max_value=10**6))).scaleb(
        -price_precision)
    ask = bid + tick
    bid_size = draw(bounded_decimal(size_precision))
    ask_size = draw(bounded_decimal(size_precision))
    return {
        "raw_id": draw(identifiers()),
        "source_id": draw(identifiers()),
        "venue": draw(identifiers()),
        "instrument_id": draw(identifiers()),
        "asset_class": draw(st.sampled_from(["crypto", "forex", "stocks"])),
        "event_type": "QUOTE",
        "exchange_time_utc_ns": ex,
        "receive_time_utc_ns": rc,
        "available_time_utc_ns": av,
        "sequence_number": draw(st.integers(0, 2**40)),
        "bid_price": format(bid, "f"),
        "ask_price": format(ask, "f"),
        "bid_size": format(bid_size, "f"),
        "ask_size": format(ask_size, "f"),
        "currency": draw(st.sampled_from(["USD", "EUR", None])),
        "price_precision": price_precision,
        "size_precision": size_precision,
        "raw_sha256": draw(hex64()),
        "manifest_sha256": None,
        "normalizer_version": draw(identifiers()),
    }


def valid_event_dicts():
    """Fully valid market-event field dicts (TRADE or QUOTE)."""
    return st.one_of(trade_fields(), quote_fields())


# --- invalid construction shapes -------------------------------------------

def _quote_like(fields):
    return fields["event_type"] == "QUOTE"


@st.composite
def invalid_event_dicts(draw):
    """Yield ``(event_dict, expected_frozen_code)`` pairs.

    The base event is a valid canonical dict; exactly one frozen-rule
    violation is injected so validation must raise exactly the expected code.
    """
    from market_data_plane import models  # local import: test-support module

    base = models.build_event(draw(valid_event_dicts()))
    kind = draw(st.sampled_from([
        "bad_schema_version", "extra_key", "unknown_type_depth_snapshot",
        "unknown_type_depth_delta", "unknown_type_garbage",
        "float_timestamp", "string_timestamp", "bool_timestamp",
        "naive_datetime", "negative_price", "negative_quantity",
        "precision_violation", "event_id_mismatch",
        "bad_quality_status", "bad_reason_code",
        "forbidden_non_null", "drop_required", "negative_sequence",
        "bool_sequence", "string_sequence", "bad_raw_sha256",
        "time_order_violation", "non_finite_price", "empty_venue",
    ]))
    event = dict(base)

    if kind == "bad_schema_version":
        event["schema_version"] = "mdp.market_event@2"
        expected = "MALFORMED_SHAPE"
    elif kind == "extra_key":
        event["unexpected_field"] = 1
        expected = "MALFORMED_SHAPE"
    elif kind in ("unknown_type_depth_snapshot", "unknown_type_depth_delta",
                  "unknown_type_garbage"):
        event["event_type"] = {"unknown_type_depth_snapshot": "DEPTH_SNAPSHOT",
                               "unknown_type_depth_delta": "DEPTH_DELTA",
                               "unknown_type_garbage": "SWAP_PRINT"}[kind]
        expected = "UNKNOWN_EVENT_TYPE"
    elif kind == "float_timestamp":
        event["receive_time_utc_ns"] = float(event["receive_time_utc_ns"])
        expected = "MALFORMED_SHAPE"
    elif kind == "string_timestamp":
        event["receive_time_utc_ns"] = str(event["receive_time_utc_ns"])
        expected = "MALFORMED_SHAPE"
    elif kind == "bool_timestamp":
        event["receive_time_utc_ns"] = True
        expected = "MALFORMED_SHAPE"
    elif kind == "naive_datetime":
        event["receive_time_utc_ns"] = datetime(2026, 1, 1)  # no tzinfo
        expected = "TIMEZONE_NAIVE_REJECTED"
    elif kind == "negative_price":
        if _quote_like(base):
            event["bid_price"] = "-1.0"
        else:
            event["price"] = "-0.5"
        expected = "NEGATIVE_PRICE"
    elif kind == "negative_quantity":
        if _quote_like(base):
            event["bid_size"] = "-2.0"
        else:
            event["quantity"] = "-2.0"
        expected = "NEGATIVE_SIZE"
    elif kind == "precision_violation":
        digits = base["price_precision"] + 1
        event["price" if not _quote_like(base) else "bid_price"] = \
            "0." + "1" * digits
        expected = "PRECISION_LOSS"
    elif kind == "event_id_mismatch":
        event["event_id"] = _sha(b"not-this-event")
        expected = "HASH_DISAGREEMENT"
    elif kind == "bad_quality_status":
        event["quality_status"] = "GREAT"
        expected = "MALFORMED_SHAPE"
    elif kind == "bad_reason_code":
        event["reason_codes"] = ["TOTALLY_UNKNOWN_CODE"]
        expected = "MALFORMED_SHAPE"
    elif kind == "forbidden_non_null":
        if _quote_like(base):
            event["price"] = "1.0"
        else:
            event["bid_price"] = "1.0"
        expected = "MALFORMED_SHAPE"
    elif kind == "drop_required":
        event.pop("quantity" if not _quote_like(base) else "ask_size")
        expected = "MISSING_REQUIRED_FIELD"
    elif kind == "negative_sequence":
        event["sequence_number"] = -1
        expected = "MALFORMED_SHAPE"
    elif kind == "bool_sequence":
        event["sequence_number"] = True
        expected = "MALFORMED_SHAPE"
    elif kind == "string_sequence":
        event["sequence_number"] = "7"
        expected = "MALFORMED_SHAPE"
    elif kind == "bad_raw_sha256":
        event["raw_sha256"] = "NOT-A-HASH"
        expected = "MALFORMED_SHAPE"
    elif kind == "time_order_violation":
        event["exchange_time_utc_ns"] = base["available_time_utc_ns"] + 10**6
        expected = "IMPOSSIBLE_TIME_ORDER"
    elif kind == "non_finite_price":
        if _quote_like(base):
            event["ask_price"] = float("inf")
        else:
            event["price"] = float("nan")
        expected = "NON_FINITE_PRICE"
    else:  # empty_venue
        event["venue"] = ""
        expected = "MALFORMED_SHAPE"

    return event, expected


# --- quality-level scenarios (constructible, classified by evaluate) --------

@st.composite
def crossed_or_locked_quote_dicts(draw):
    """Canonical QUOTE dicts with bid_price >= ask_price (crossed or locked)."""
    from market_data_plane import models

    fields = draw(quote_fields())
    precision = fields["price_precision"]
    ask = Decimal(fields["ask_price"])
    # 0 extra => locked (bid == ask); > 0 => crossed (bid > ask)
    extra = Decimal(draw(st.integers(0, 10**5))).scaleb(-precision)
    fields["bid_price"] = format(ask + extra, "f")
    return models.build_event(fields)


@st.composite
def stale_quote_scenario(draw):
    """(canonical QUOTE dict, params) where the quote is stale by construction."""
    from market_data_plane import models, quality

    fields = draw(quote_fields())
    event = models.build_event(fields)
    threshold = draw(st.integers(0, 10**12))
    eval_time = event["exchange_time_utc_ns"] + threshold + draw(
        st.integers(1, 10**9))
    params = quality.QualityParams(evaluation_time_ns=eval_time,
                                   staleness_threshold_ns=threshold)
    return event, params


def manifest_contexts():
    """Explicit stream-context dicts for evaluate()."""
    return st.fixed_dictionaries({
        "sequence_semantics": st.sampled_from(["CONTIGUOUS", "NONE", None]),
        "ordered_delivery": st.one_of(st.booleans(), st.none()),
        "last_sequence_number": st.one_of(st.none(), st.integers(0, 2**40)),
        "sequence_reset_evidenced": st.booleans(),
        "last_receive_time_ns": st.one_of(st.none(), st.integers(0, 2**62)),
    })


def quality_params():
    """Explicit QualityParams inputs (evaluation time + threshold required)."""
    from market_data_plane import quality

    return st.builds(
        quality.QualityParams,
        evaluation_time_ns=st.integers(0, 2**62),
        staleness_threshold_ns=st.integers(0, 10**12),
        anomaly_z_threshold=st.just(6.0),
        recent_prices=st.just(()),
        instrument_registry=st.none(),
    )


def utc_aware_datetime():
    return st.datetimes(
        min_value=datetime(1970, 1, 1, tzinfo=timezone.utc),
        max_value=datetime(2099, 1, 1, tzinfo=timezone.utc),
        timezones=st.just(timezone.utc),
    )
