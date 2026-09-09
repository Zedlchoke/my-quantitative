"""Canonical market-event and raw-chunk-manifest models for MDP-V1.

Freeze authority: research/control/market_data_plane_v1_run/architecture_freeze.json
(sha256 7f7403e67bfb9707b547b6762cc0a3c87f2c96f701b3f1ec3ad2197478736c02),
section "schemas", and plans/PLAN_market_data_plane_v1.md sections 6.2/6.3.

Schemas implemented here (frozen):
  * ``mdp.market_event@1`` — the exact 27-field envelope.
  * ``mdp.raw_chunk_manifest@1`` — the exact manifest_fields list.

Everything is plain dicts plus stdlib; no pandas/pandera/dvc/nautilus_trader
import at module import time (freeze ``import_isolation``).  This module owns
construction + validation + canonical serialisation only; quality
classification lives in ``quality.py`` and quarantine decisions belong to
callers (A3's quarantine store).
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from . import reason_codes as _rc

# --- frozen constants -------------------------------------------------------

SCHEMA_VERSION = "mdp.market_event@1"
MANIFEST_SCHEMA_VERSION = "mdp.raw_chunk_manifest@1"

#: The exact frozen 27-field event envelope (order as frozen).
ENVELOPE_FIELDS: tuple[str, ...] = (
    "schema_version", "event_id", "raw_id", "source_id", "venue",
    "instrument_id", "asset_class", "event_type",
    "exchange_time_utc_ns", "receive_time_utc_ns", "available_time_utc_ns",
    "sequence_number", "price", "quantity", "side",
    "bid_price", "ask_price", "bid_size", "ask_size",
    "currency", "price_precision", "size_precision",
    "quality_status", "reason_codes", "raw_sha256",
    "manifest_sha256", "normalizer_version",
)

#: The exact frozen manifest_fields list (order as frozen).
MANIFEST_FIELDS: tuple[str, ...] = (
    "schema_version", "manifest_id", "source_id", "provider_id", "venue",
    "instrument_id", "asset_class", "event_class",
    "request_identity_secrets_removed", "entitlement_evidence_ref",
    "allowed_use_classification", "retrieval_start_utc_ns",
    "retrieval_end_utc_ns", "payload_byte_length", "record_count",
    "payload_sha256", "media_type", "encoding",
    "min_exchange_time_utc_ns", "max_exchange_time_utc_ns",
    "min_receive_time_utc_ns", "max_receive_time_utc_ns",
    "min_available_time_utc_ns", "max_available_time_utc_ns",
    "parser_version", "normalizer_version", "prev_manifest_id",
    "next_manifest_id", "completeness_status", "gap_reasons",
    "sequence_semantics", "ordered_delivery", "created_utc",
)

#: Frozen event-type matrix (TRADE/QUOTE constructible; DEPTH_* RESERVED).
EVENT_TYPE_MATRIX = {
    "TRADE": {
        "required": ("price", "quantity"),
        "optional": ("side", "currency"),
        "forbidden_non_null": ("bid_price", "ask_price", "bid_size", "ask_size"),
    },
    "QUOTE": {
        "required": ("bid_price", "ask_price", "bid_size", "ask_size"),
        "optional": ("currency",),
        "forbidden_non_null": ("price", "quantity", "side"),
    },
}

#: Event types RESERVED in @1 — constructing them raises UNKNOWN_EVENT_TYPE.
RESERVED_EVENT_TYPES = ("DEPTH_SNAPSHOT", "DEPTH_DELTA")

QUALITY_STATUSES = ("VALID", "SUSPECT", "INVALID", "QUARANTINED")
COMPLETENESS_STATUSES = ("COMPLETE", "GAPS_PRESENT")
ALLOWED_USE_CLASSES = ("RESEARCH_AUTHORIZED", "RESEARCH_CONDITIONAL", "NOT_AUTHORIZED")
SEQUENCE_SEMANTICS = ("CONTIGUOUS", "NONE")

#: Frozen canonical_json: json.dumps(obj, sort_keys=True, separators=(',',':'),
#: ensure_ascii=True, allow_nan=False); decimals as strings per field_rules.
_JSON_KWARGS = dict(sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                    allow_nan=False)

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_FIXED_POINT_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
_UNIT_FRACTION_SEP = "\x1f"  # 0x1F field separator of the canonical identity string

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

#: Price-like decimal fields (NON_FINITE_PRICE / NEGATIVE_PRICE apply).
PRICE_FIELDS = ("price", "bid_price", "ask_price")
#: Size-like decimal fields (NEGATIVE_SIZE applies).
SIZE_FIELDS = ("quantity", "bid_size", "ask_size")
DECIMAL_FIELDS = PRICE_FIELDS + SIZE_FIELDS
TIMESTAMP_FIELDS = (
    "exchange_time_utc_ns", "receive_time_utc_ns", "available_time_utc_ns",
)


class MarketDataPlaneError(ValueError):
    """Validation failure carrying the frozen reason code that explains it."""

    def __init__(self, reason_code: str, message: str):
        if not _rc.is_known(reason_code):
            raise AssertionError(f"internal error: unknown reason code {reason_code!r}")
        super().__init__(f"[{reason_code}] {message}")
        self.reason_code = reason_code


def _malformed(message: str) -> MarketDataPlaneError:
    return MarketDataPlaneError("MALFORMED_SHAPE", message)


def _missing(message: str) -> MarketDataPlaneError:
    return MarketDataPlaneError("MISSING_REQUIRED_FIELD", message)


# --- canonical serialisation ------------------------------------------------

def canonical_json(obj) -> str:
    """Frozen canonical JSON serialisation (byte-stable, deterministic).

    Exactly ``json.dumps(obj, sort_keys=True, separators=(',',':'),
    ensure_ascii=True, allow_nan=False)``.  Decimal values must already be
    represented as strings per field_rules before calling this.
    """
    try:
        return json.dumps(obj, **_JSON_KWARGS)
    except (TypeError, ValueError) as exc:  # e.g. NaN under allow_nan=False
        raise _malformed(f"value is not canonically serialisable: {exc}") from exc


def stream_bytes(events) -> bytes:
    """Replay stream bytes: newline-delimited canonical_json per event."""
    out = []
    for event in events:
        out.append(canonical_json(event).encode("utf-8"))
        out.append(b"\n")
    return b"".join(out)


def stream_digest(events) -> str:
    """sha256 hex over the exact byte stream (canonical_json + newline/event)."""
    return hashlib.sha256(stream_bytes(events)).hexdigest()


# --- total replay order (frozen key; A3's replay.py is the authority user) --

_TOTAL_ORDER_KEY = (
    "exchange_time_utc_ns", "receive_time_utc_ns", "available_time_utc_ns",
    "source_id", "venue", "instrument_id", "event_type", "sequence_number",
    "event_id",
)


def replay_order_key(event: dict):
    """Frozen total_order_key tuple; event_id is the final total tie-break.

    ``None`` sorts before any concrete value so ordering stays total even
    when optional fields are null (e.g. sequence_number under semantics NONE).
    """
    key = []
    for field in _TOTAL_ORDER_KEY:
        value = event[field]
        key.append((0, "") if value is None else (1, value))
    return tuple(key)


def sort_events_for_replay(events):
    """Deterministic total sort; never deletes, independent of input order."""
    return sorted(events, key=replay_order_key)


# --- timestamps -------------------------------------------------------------

def timestamp_to_ns(value) -> int:
    """Coerce a timestamp input to integer UTC nanoseconds (frozen rules).

    int (not bool) passes through; a timezone-aware ``datetime`` is converted
    exactly (datetime has microsecond resolution); float, str, bool, naive
    datetime and anything else are rejected.  Naive datetimes raise
    TIMEZONE_NAIVE_REJECTED; every other malformed input raises
    MALFORMED_SHAPE.
    """
    if isinstance(value, bool):
        raise _malformed("timestamp must be int UTC ns; bool is not a timestamp")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        raise _malformed("float timestamp rejected; timestamps are int UTC ns")
    if isinstance(value, str):
        raise _malformed("string timestamp rejected; timestamps are int UTC ns")
    if isinstance(value, datetime):
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise MarketDataPlaneError(
                "TIMEZONE_NAIVE_REJECTED",
                "naive/local datetime rejected; supply timezone-aware input or int ns",
            )
        delta = value - _EPOCH
        return (delta.days * 86400 + delta.seconds) * 10**9 + delta.microseconds * 1000
    raise _malformed(f"unsupported timestamp type {type(value).__name__}")


def ns_to_timestamp(ns: int) -> datetime:
    """Inverse of :func:`timestamp_to_ns` for display/tests (aware UTC)."""
    return _EPOCH + timedelta(microseconds=ns // 1000)


# --- decimals ---------------------------------------------------------------

def _fractional_digits(d: Decimal) -> int:
    return max(0, -d.as_tuple().exponent)


def to_fixed_point_string(d: Decimal) -> str:
    """Canonical fixed-point decimal string: no exponent, no float artefacts.

    ``Decimal('0.1') -> '0.1'``; ``Decimal('1E+2') -> '100'``;
    ``Decimal('0.00000001') -> '0.00000001'``.  The input representation's
    significant trailing digits are preserved (deterministic).
    """
    text = format(d, "f")
    if text.startswith("+"):
        text = text[1:]
    return text


def decimal_string_to_decimal(text: str):
    """Parse a canonical fixed-point decimal string strictly (no exponent)."""
    if not isinstance(text, str) or not _FIXED_POINT_RE.match(text):
        raise _malformed(
            f"decimal fields persist as fixed-point strings without exponent; got {text!r}"
        )
    return Decimal(text)


def _validated_decimal(value, declared_precision: int, *, price_like: bool,
                       field: str) -> Decimal:
    """Apply the frozen decimal field_rules to one value; return the Decimal.

    * binary float is forbidden in persisted evidence: float input converts
      via ``Decimal(repr(x))`` then validates — PRECISION_LOSS when it is not
      exactly representable at the declared precision;
    * non-finite price-like input -> NON_FINITE_PRICE (a non-finite size-like
      value has no dedicated frozen code and is MALFORMED_SHAPE);
    * negative price-like -> NEGATIVE_PRICE, negative size-like -> NEGATIVE_SIZE;
    * more fractional digits than declared precision -> PRECISION_LOSS.
    """
    if isinstance(value, bool):
        raise _malformed(f"{field}: bool is not a decimal value")
    if isinstance(value, Decimal):
        d = value
    elif isinstance(value, int):
        d = Decimal(value)
    elif isinstance(value, float):
        if not math.isfinite(value):
            if price_like:
                raise MarketDataPlaneError("NON_FINITE_PRICE",
                                           f"{field}: non-finite float input")
            raise _malformed(f"{field}: non-finite float input")
        d = Decimal(repr(value))
    elif isinstance(value, str):
        d = decimal_string_to_decimal(value)
        if not d.is_finite():
            if price_like:
                raise MarketDataPlaneError("NON_FINITE_PRICE", f"{field}: non-finite")
            raise _malformed(f"{field}: non-finite")
    else:
        raise _malformed(f"{field}: unsupported decimal input type {type(value).__name__}")

    if not d.is_finite():
        if price_like:
            raise MarketDataPlaneError("NON_FINITE_PRICE", f"{field}: non-finite value")
        raise _malformed(f"{field}: non-finite value")

    if price_like and d < 0:
        raise MarketDataPlaneError("NEGATIVE_PRICE", f"{field}: {to_fixed_point_string(d)}")
    if not price_like and d < 0:
        raise MarketDataPlaneError("NEGATIVE_SIZE", f"{field}: {to_fixed_point_string(d)}")

    if _fractional_digits(d) > declared_precision:
        # PRECISION_LOSS only when the VALUE is not exactly representable at
        # the declared precision; trailing-zero artifacts (e.g. repr(1e9) =
        # '1000000000.0' at precision 0) are losslessly normalised away.
        import decimal as _decimal
        with _decimal.localcontext() as ctx:
            ctx.prec = max(len(d.as_tuple().digits) + declared_precision, 60)
            stripped = d.normalize()
        if _fractional_digits(stripped) > declared_precision:
            raise MarketDataPlaneError(
                "PRECISION_LOSS",
                f"{field}: {to_fixed_point_string(d)} exceeds declared precision "
                f"{declared_precision}",
            )
        d = stripped
    return d


def _canonical_decimal_field(value, declared_precision: int, *, price_like: bool,
                             field: str):
    """Validate one decimal field; return its canonical fixed-point string."""
    d = _validated_decimal(value, declared_precision, price_like=price_like, field=field)
    return to_fixed_point_string(d)


def quote_mid(bid_price: str, ask_price: str) -> Decimal:
    """Exact Decimal mid ``(bid+ask)/2`` (never binary float)."""
    bid = decimal_string_to_decimal(bid_price)
    ask = decimal_string_to_decimal(ask_price)
    return (bid + ask) / Decimal(2)


# --- event identity ---------------------------------------------------------

def compute_event_id(fields: dict) -> str:
    """Lowercase hex sha256 of the 0x1F-joined canonical identity string.

    Identity fields (frozen field_rules): schema_version | source_id | venue |
    instrument_id | event_type | exchange_time_utc_ns | receive_time_utc_ns |
    available_time_utc_ns | sequence_number | raw_sha256.  A null
    sequence_number contributes the empty string.
    """
    seq = fields.get("sequence_number")
    parts = (
        SCHEMA_VERSION,
        fields["source_id"],
        fields["venue"],
        fields["instrument_id"],
        fields["event_type"],
        str(fields["exchange_time_utc_ns"]),
        str(fields["receive_time_utc_ns"]),
        str(fields["available_time_utc_ns"]),
        "" if seq is None else str(seq),
        fields["raw_sha256"],
    )
    identity = _UNIT_FRACTION_SEP.join(parts)
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


# --- helpers ----------------------------------------------------------------

def _is_plain_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validated_reason_codes(value):
    """Validate + canonicalise reason_codes to a sorted unique list."""
    if value is None:
        return []
    if not isinstance(value, list):
        raise _malformed("reason_codes must be a list")
    for code in value:
        if not isinstance(code, str) or not _rc.is_known(code):
            raise _malformed(f"reason code outside reason_codes@1: {code!r}")
    return sorted(set(value))


def _validated_hash64(value, field: str) -> str:
    if not isinstance(value, str) or not _HEX64_RE.match(value):
        raise _malformed(f"{field} must be lowercase hex sha256 (64 chars)")
    return value


def _validated_identifier(value, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise _malformed(f"{field} must be a non-empty string")
    return value


# --- event construction / validation ---------------------------------------

def validate_event(event) -> dict:
    """Validate one market event; return the canonical 27-field dict.

    Raises :class:`MarketDataPlaneError` with the frozen reason code on any
    violation.  Never mutates the input.  The returned dict contains every
    envelope field (absent matrix-conditional fields are explicit nulls) and
    satisfies ``from_dict(to_dict(e)) == e``.
    """
    if not isinstance(event, dict):
        raise _malformed("event must be a dict")
    keys = set(event.keys())
    envelope = set(ENVELOPE_FIELDS)
    if not keys <= envelope:
        extra = sorted(keys - envelope)
        raise _malformed(f"unknown envelope field(s): {extra}")

    event_type = event.get("event_type")
    if event_type is None:
        raise _missing("event_type is required")
    if event_type not in EVENT_TYPE_MATRIX:
        # DEPTH_SNAPSHOT / DEPTH_DELTA and every other type are rejected here.
        raise MarketDataPlaneError("UNKNOWN_EVENT_TYPE",
                                   f"event_type {event_type!r} not constructible in @1")
    matrix = EVENT_TYPE_MATRIX[event_type]

    if event.get("schema_version") != SCHEMA_VERSION:
        raise _malformed(
            f"schema_version must be {SCHEMA_VERSION!r}, got {event.get('schema_version')!r}"
        )

    for field in ("source_id", "venue", "instrument_id"):
        _validated_identifier(event.get(field), field)
    _validated_identifier(event.get("raw_id"), "raw_id")
    _validated_identifier(event.get("normalizer_version"), "normalizer_version")
    _validated_hash64(event.get("raw_sha256"), "raw_sha256")

    manifest_sha = event.get("manifest_sha256")
    # Nullability note (flagged to A1, not silently decided as spec): the
    # archive write sequence publishes the chunk before its manifest, so a
    # not-yet-linked event may carry an explicit null here; when present the
    # value must be a 64-char lowercase hex sha256.
    if manifest_sha is not None:
        _validated_hash64(manifest_sha, "manifest_sha256")

    currency = event.get("currency")
    if currency is not None:
        _validated_identifier(currency, "currency")

    price_precision = event.get("price_precision")
    size_precision = event.get("size_precision")
    if not _is_plain_int(price_precision) or price_precision < 0:
        raise _malformed("price_precision must be an int >= 0")
    if not _is_plain_int(size_precision) or size_precision < 0:
        raise _malformed("size_precision must be an int >= 0")

    sequence = event.get("sequence_number")
    if sequence is not None and (not _is_plain_int(sequence) or sequence < 0):
        raise _malformed("sequence_number must be int >= 0 (null only when the "
                         "manifest declares sequence_semantics=NONE)")

    timestamps = {}
    for field in TIMESTAMP_FIELDS:
        if field not in event or event.get(field) is None:
            raise _missing(f"{field} is required")
        timestamps[field] = timestamp_to_ns(event[field])

    # Impossible time order is rejected at construction (frozen field
    # semantics: exchange <= receive <= available; the three times are never
    # aliases).  Checked before identity so the code is never masked by a
    # stale supplied event_id.
    if timestamps["exchange_time_utc_ns"] > timestamps["receive_time_utc_ns"] or \
            timestamps["receive_time_utc_ns"] > timestamps["available_time_utc_ns"]:
        raise MarketDataPlaneError(
            "IMPOSSIBLE_TIME_ORDER",
            "exchange_time <= receive_time <= available_time required",
        )

    side = event.get("side")
    if side is not None and side not in ("buy", "sell"):
        raise _malformed("side must be 'buy' or 'sell' when present")

    # Event-type matrix: required non-null, forbidden must be null.
    for field in matrix["required"]:
        if field not in event or event.get(field) is None:
            raise _missing(f"{event_type} requires non-null {field}")
    for field in matrix["forbidden_non_null"]:
        if event.get(field) is not None:
            raise _malformed(f"{event_type} must not carry non-null {field}")

    # Decimals: canonical fixed-point strings with declared precisions.
    canonical = {field: event.get(field) for field in ENVELOPE_FIELDS}
    for field in ("price", "bid_price", "ask_price"):
        if canonical[field] is not None:
            canonical[field] = _canonical_decimal_field(
                canonical[field], price_precision, price_like=True, field=field)
    for field in ("quantity", "bid_size", "ask_size"):
        if canonical[field] is not None:
            canonical[field] = _canonical_decimal_field(
                canonical[field], size_precision, price_like=False, field=field)
    for field, value in timestamps.items():
        canonical[field] = value
    canonical["sequence_number"] = sequence
    canonical["side"] = side

    # quality_status enum; no event is VALID merely because parsing succeeded,
    # so an unevaluated event defaults to QUARANTINED until classify/evaluate.
    status = event.get("quality_status")
    if status is None:
        status = "QUARANTINED"
    if status not in QUALITY_STATUSES:
        raise _malformed(f"quality_status {status!r} outside frozen enum")
    canonical["quality_status"] = status

    canonical["reason_codes"] = _validated_reason_codes(event.get("reason_codes"))

    # event_id: computed from canonical identity; a supplied disagreeing id is
    # a HASH_DISAGREEMENT (fail closed).
    computed_id = compute_event_id(canonical)
    supplied_id = event.get("event_id")
    if supplied_id is None:
        canonical["event_id"] = computed_id
    else:
        _validated_hash64(supplied_id, "event_id")
        if supplied_id != computed_id:
            raise MarketDataPlaneError(
                "HASH_DISAGREEMENT",
                f"supplied event_id {supplied_id} != computed {computed_id}",
            )
        canonical["event_id"] = supplied_id

    return canonical


def build_event(fields: dict | None = None, **kwargs) -> dict:
    """Construct a canonical event from partial fields.

    Every envelope field omitted here is filled with an explicit null; the
    event-type matrix, precision rules and identity hash are then enforced by
    :func:`validate_event`.  ``quality_status`` defaults to ``QUARANTINED``
    (never VALID merely because parsing succeeded) and ``reason_codes`` to
    ``[]``; callers overwrite them from :func:`quality.evaluate` results via
    :func:`set_quality`.
    """
    if fields and kwargs:
        raise ValueError("pass either a dict or kwargs, not both")
    source = dict(fields) if fields is not None else dict(kwargs)
    unknown = set(source) - set(ENVELOPE_FIELDS)
    if unknown:
        raise _malformed(f"unknown event field(s): {sorted(unknown)}")
    candidate = {field: source.get(field) for field in ENVELOPE_FIELDS}
    if candidate["schema_version"] is None:
        candidate["schema_version"] = SCHEMA_VERSION
    return validate_event(candidate)


def to_dict(event: dict) -> dict:
    """Deep copy of a canonical event dict (round-trip half)."""
    if not isinstance(event, dict):
        raise _malformed("event must be a dict")
    return copy.deepcopy(event)


def from_dict(raw) -> dict:
    """Validate + canonicalise a raw event dict (round-trip half)."""
    return validate_event(raw)


def set_quality(event: dict, quality_status: str, reason_codes) -> dict:
    """Return a copy of *event* with quality fields replaced (validated).

    Classification only: the physical quarantine move is a caller (A3) decision.
    ``quality_status`` must be in the frozen enum; reason codes are canonicalised
    sorted-unique and must come from reason_codes@1.
    """
    if quality_status not in QUALITY_STATUSES:
        raise _malformed(f"quality_status {quality_status!r} outside frozen enum")
    updated = copy.deepcopy(event)
    updated["quality_status"] = quality_status
    updated["reason_codes"] = _validated_reason_codes(list(reason_codes))
    return updated


# --- raw chunk manifest -----------------------------------------------------

def compute_manifest_id(manifest_minus_id: dict) -> str:
    """manifest_id = sha256 of canonical_json(manifest minus manifest_id)."""
    return hashlib.sha256(
        canonical_json(manifest_minus_id).encode("utf-8")
    ).hexdigest()


def build_manifest(fields: dict | None = None) -> dict:
    """Construct a canonical manifest, computing manifest_id.

    ``prev_manifest_id``/``next_manifest_id`` default to null; ``gap_reasons``
    defaults to ``[]``; ``completeness_status`` must be supplied (or defaults
    to ``COMPLETE``); ``sequence_semantics`` defaults to ``CONTIGUOUS``;
    ``ordered_delivery`` defaults to True.
    """
    source = dict(fields) if fields is not None else {}
    unknown = set(source) - set(MANIFEST_FIELDS)
    if unknown:
        raise _malformed(f"unknown manifest field(s): {sorted(unknown)}")
    candidate = {field: source.get(field) for field in MANIFEST_FIELDS}
    candidate["schema_version"] = MANIFEST_SCHEMA_VERSION
    if candidate["gap_reasons"] is None:
        candidate["gap_reasons"] = []
    if candidate["completeness_status"] is None:
        candidate["completeness_status"] = "COMPLETE"
    if candidate["sequence_semantics"] is None:
        candidate["sequence_semantics"] = "CONTIGUOUS"
    if candidate["ordered_delivery"] is None:
        candidate["ordered_delivery"] = True
    manifest = validate_manifest(candidate, skip_id=True)
    manifest["manifest_id"] = compute_manifest_id(
        {k: v for k, v in manifest.items() if k != "manifest_id"})
    return manifest


def validate_manifest(manifest, skip_id: bool = False) -> dict:
    """Validate a raw chunk manifest; return the canonical dict.

    Consistency checks enforced here: exact frozen field set, schema version,
    enum membership (completeness_status / allowed_use_classification /
    sequence_semantics), ordered_delivery is a real bool, gap_reasons are
    reason_codes@1 members, retrieval_start <= retrieval_end, min <= max for
    all three timestamp ranges, non-negative counts/lengths, and (unless
    *skip_id*) manifest_id == sha256(canonical_json(manifest minus manifest_id)).
    """
    if not isinstance(manifest, dict):
        raise _malformed("manifest must be a dict")
    keys = set(manifest.keys())
    fields = set(MANIFEST_FIELDS)
    if not keys <= fields:
        raise _malformed(f"unknown manifest field(s): {sorted(keys - fields)}")

    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise _malformed(
            f"manifest schema_version must be {MANIFEST_SCHEMA_VERSION!r}, "
            f"got {manifest.get('schema_version')!r}")

    canonical = {field: manifest.get(field) for field in MANIFEST_FIELDS}

    for field in ("source_id", "provider_id", "venue", "instrument_id",
                  "asset_class", "event_class", "entitlement_evidence_ref",
                  "media_type", "encoding", "parser_version",
                  "normalizer_version"):
        _validated_identifier(canonical[field], field)

    if canonical["allowed_use_classification"] not in ALLOWED_USE_CLASSES:
        raise _malformed(
            f"allowed_use_classification {canonical['allowed_use_classification']!r} "
            f"outside {ALLOWED_USE_CLASSES}")
    if canonical["completeness_status"] not in COMPLETENESS_STATUSES:
        raise _malformed(
            f"completeness_status {canonical['completeness_status']!r} "
            f"outside {COMPLETENESS_STATUSES}")
    if canonical["sequence_semantics"] not in SEQUENCE_SEMANTICS:
        raise _malformed(
            f"sequence_semantics {canonical['sequence_semantics']!r} "
            f"outside {SEQUENCE_SEMANTICS}")
    if not isinstance(canonical["ordered_delivery"], bool):
        raise _malformed("ordered_delivery must be a bool")

    gap_reasons = canonical["gap_reasons"]
    if not isinstance(gap_reasons, list):
        raise _malformed("gap_reasons must be a list of reason codes")
    for code in gap_reasons:
        if not isinstance(code, str) or not _rc.is_known(code):
            raise _malformed(f"gap_reasons entry outside reason_codes@1: {code!r}")
    canonical["gap_reasons"] = sorted(set(gap_reasons))

    request_identity = canonical["request_identity_secrets_removed"]
    if not isinstance(request_identity, (str, dict, list)) or (
            isinstance(request_identity, str) and not request_identity):
        raise _malformed(
            "request_identity_secrets_removed must be a non-empty string/dict/list "
            "(request identity with secrets removed)")

    retrieval_start = timestamp_to_ns(canonical["retrieval_start_utc_ns"])
    retrieval_end = timestamp_to_ns(canonical["retrieval_end_utc_ns"])
    canonical["retrieval_start_utc_ns"] = retrieval_start
    canonical["retrieval_end_utc_ns"] = retrieval_end
    if retrieval_start > retrieval_end:
        raise MarketDataPlaneError("MANIFEST_MISMATCH",
                                   "retrieval_start_utc_ns > retrieval_end_utc_ns")
    canonical["created_utc"] = timestamp_to_ns(canonical["created_utc"])

    if not _is_plain_int(canonical["payload_byte_length"]) or canonical["payload_byte_length"] < 0:
        raise _malformed("payload_byte_length must be int >= 0")
    if not _is_plain_int(canonical["record_count"]) or canonical["record_count"] < 0:
        raise _malformed("record_count must be int >= 0")
    _validated_hash64(canonical["payload_sha256"], "payload_sha256")

    ranges = (("min_exchange_time_utc_ns", "max_exchange_time_utc_ns"),
              ("min_receive_time_utc_ns", "max_receive_time_utc_ns"),
              ("min_available_time_utc_ns", "max_available_time_utc_ns"))
    for lo_field, hi_field in ranges:
        # min/max are null exactly when the chunk carries no records
        # (cross-checked against events by check_manifest_consistency).
        lo_value, hi_value = canonical[lo_field], canonical[hi_field]
        if lo_value is None or hi_value is None:
            if not (lo_value is None and hi_value is None):
                raise MarketDataPlaneError(
                    "MANIFEST_MISMATCH",
                    f"{lo_field}/{hi_field} must both be null or both be set")
            continue
        lo = timestamp_to_ns(lo_value)
        hi = timestamp_to_ns(hi_value)
        if lo > hi:
            raise MarketDataPlaneError(
                "MANIFEST_MISMATCH", f"{lo_field} > {hi_field}")
        canonical[lo_field] = lo
        canonical[hi_field] = hi

    for field in ("prev_manifest_id", "next_manifest_id"):
        value = canonical[field]
        if value is not None:
            _validated_hash64(value, field)

    if not skip_id:
        supplied = canonical["manifest_id"]
        _validated_hash64(supplied, "manifest_id")
        computed = compute_manifest_id(
            {k: v for k, v in canonical.items() if k != "manifest_id"})
        if supplied != computed:
            raise MarketDataPlaneError(
                "HASH_DISAGREEMENT",
                f"manifest_id {supplied} != computed {computed}")
    return canonical


def manifest_stream_bytes(events) -> bytes:
    """Byte stream whose length/hash back a chunk payload (canonical events)."""
    return stream_bytes(events)


def check_manifest_consistency(manifest: dict, events, payload_bytes=None) -> None:
    """Cross-check a manifest against the events it describes.

    Verifies record_count == len(events), the min/max exchange/receive/
    available timestamps equal the event extremes, and — when the raw
    *payload_bytes* are supplied — payload_byte_length and payload_sha256.
    Raises MANIFEST_MISMATCH on any disagreement.
    """
    events = list(events)
    if manifest["record_count"] != len(events):
        raise MarketDataPlaneError(
            "MANIFEST_MISMATCH",
            f"record_count {manifest['record_count']} != {len(events)} events")

    extremes = {
        "min_exchange_time_utc_ns": "exchange_time_utc_ns",
        "max_exchange_time_utc_ns": "exchange_time_utc_ns",
        "min_receive_time_utc_ns": "receive_time_utc_ns",
        "max_receive_time_utc_ns": "receive_time_utc_ns",
        "min_available_time_utc_ns": "available_time_utc_ns",
        "max_available_time_utc_ns": "available_time_utc_ns",
    }
    if events:
        for manifest_field, event_field in extremes.items():
            actual = (min if manifest_field.startswith("min") else max)(
                e[event_field] for e in events)
            if manifest[manifest_field] != actual:
                raise MarketDataPlaneError(
                    "MANIFEST_MISMATCH",
                    f"{manifest_field} {manifest[manifest_field]} != observed {actual}")
    else:
        for manifest_field in extremes:
            if manifest[manifest_field] is not None:
                raise MarketDataPlaneError(
                    "MANIFEST_MISMATCH",
                    f"{manifest_field} must be null for an empty chunk")

    if payload_bytes is not None:
        if manifest["payload_byte_length"] != len(payload_bytes):
            raise MarketDataPlaneError(
                "MANIFEST_MISMATCH",
                f"payload_byte_length {manifest['payload_byte_length']} != {len(payload_bytes)}")
        digest = hashlib.sha256(payload_bytes).hexdigest()
        if manifest["payload_sha256"] != digest:
            raise MarketDataPlaneError(
                "MANIFEST_MISMATCH",
                f"payload_sha256 {manifest['payload_sha256']} != observed {digest}")
