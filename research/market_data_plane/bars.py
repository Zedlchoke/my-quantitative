"""mdp.market_bar@2 — the frozen bar contract (lane A4, MDP-V2).

Freeze authority: research/control/market_data_plane_v2_run/architecture_freeze_v2.json
(p3_wave_sha 09a223f6ce166e219beb67b25b8151361979ca21), section
"bar_contract" and findings F4.  mdp.market_event@1 stays byte-frozen; this
module is purely ADDITIVE (the @2 bar mapping).

Schemas implemented here (frozen):

* ``mdp.market_bar@2`` — the exact frozen bar field list
  (``bar_contract.exact_field_list_31``; the frozen enumeration carries 32
  field NAMES — the enumeration is authoritative, the count label in the
  freeze prose is off by one; surfaced to A1 for ratification).
* ``mdp.bar_reason_codes@2`` — the frozen bar reason-code EXTENSION set.
  It extends, and never mutates, reason_codes@1 (research/market_data_plane/
  reason_codes.py stays untouched).

Frozen rules honoured here:

* OHLV values persist as exact canonical fixed-point DECIMAL STRINGS with the
  models.py discipline (canonical_json, fixed-point, trailing-zero
  normalisation only when lossless).  Binary floats are REJECTED outright —
  no float ever enters the bar model (stricter than the @1 event path,
  exactly as frozen: "no floats anywhere in the bar model").
* Time order ``open_time_utc_ns < close_time_utc_ns <=
  available_time_utc_ns`` is strict and fail-closed.  The ONLY exception
  path is the ``availability_rule`` context parameter (default
  :data:`STRICT`): a per-asset evidenced publication rule must be passed
  EXPLICITLY at every build/validate site and must return a non-empty
  evidence string.  A relaxed bar stays visibly anomalous in its persisted
  timestamps and fails every strict re-validation — the relaxation is never
  silent.  The ``open_time < close_time`` leg is never relaxable.
* NO microstructure: a bar can never create BBO/depth/spread/TCA evidence.
  mdp.market_event@1's validator rejects bar dicts (test-enforced); the
  bridge quote/trade paths refuse bar-shaped input (test-enforced).
* raw vs adjusted are separate identities: ``adjustment_mode in
  {RAW, CORP_ACTION_ADJUSTED}``; adjusted bars require a non-null
  ``corporate_action_ref``; ``adjustment_mode`` participates in ``bar_id``.
* Missing volume/quote_volume/trade_count/taker_buy_base/taker_buy_quote is
  ``null`` plus reason code ``BAR_VOLUME_NOT_EVALUABLE`` contributing
  ``completeness_status="NOT_EVALUABLE"`` — NEVER zero.
* ``bar_id`` = sha256 of canonical_json of the frozen identity tuple
  (IDENTITY_FIELDS below).  ``raw_id`` is 64-hex and frozen to equal
  ``raw_sha256`` for row-derived bars in @2.  ``raw_sha256`` (sha256 of the
  exact raw provider record bytes) and ``manifest_sha256`` (the upstream
  retrieval manifest id, mirroring the A3_Q4 event ruling) are required
  64-hex.
* quality_status reuses the @1 status vocabulary
  (VALID/SUSPECT/INVALID/QUARANTINED via quality.status_from_codes /
  reason_codes.final_status_for; reuse noted in :func:`bar_status_from_codes`
  as the freeze requires — bar extension codes are classified locally
  because reason_codes@1's frozen classes cannot be mutated).
* Duplicate or non-disjoint intervals FAIL CLOSED with
  :class:`BarIntervalError` (see bar_stream.py) — never quarantine.

stdlib + sibling modules only (import isolation: no nautilus_trader import
at module import time).  This module never mutates its inputs.
"""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from decimal import Decimal

from . import models as _models
from . import reason_codes as _rc

# --- frozen constants -------------------------------------------------------

SCHEMA_VERSION = "mdp.market_bar@2"

#: The exact frozen bar field list (order exactly as frozen in
#: architecture_freeze_v2.json bar_contract.exact_field_list_31).
BAR_FIELDS: tuple[str, ...] = (
    "schema_version", "bar_id", "raw_id", "source_id", "provider_id",
    "venue", "instrument_id", "asset_class", "bar_type", "interval_ns",
    "open_time_utc_ns", "close_time_utc_ns", "available_time_utc_ns",
    "open", "high", "low", "close", "volume", "quote_volume", "trade_count",
    "taker_buy_base", "taker_buy_quote", "price_precision", "size_precision",
    "adjustment_mode", "corporate_action_ref", "completeness_status",
    "quality_status", "reason_codes", "raw_sha256", "manifest_sha256",
    "normalizer_version",
)

#: Frozen bar_id identity tuple (bar_contract.identity_rules.bar_id):
#: sha256 of canonical_json of exactly these fields.
IDENTITY_FIELDS: tuple[str, ...] = (
    "schema_version", "source_id", "provider_id", "venue", "instrument_id",
    "asset_class", "bar_type", "interval_ns", "open_time_utc_ns",
    "adjustment_mode",
)

#: Frozen adjustment modes (bar_contract.field_rules.raw_vs_adjusted).
ADJUSTMENT_MODES: tuple[str, ...] = ("RAW", "CORP_ACTION_ADJUSTED")

#: Frozen extension set mdp.bar_reason_codes@2 (order exactly as frozen).
#: EXTENDS reason_codes@1; the @1 registry itself is never mutated.
BAR_REASON_CODES: tuple[str, ...] = (
    "BAR_OHLC_ORDER_VIOLATION",
    "BAR_NONPOSITIVE_PRICE",
    "BAR_INTERVAL_OVERLAP",
    "BAR_INTERVAL_DUPLICATE",
    "BAR_VOLUME_NOT_EVALUABLE",
    "BAR_OUTSIDE_CALENDAR",
    "BAR_PRECISION_LOSS",
)

#: Bar extension codes that reject (INVALID) when present.
BAR_REJECT_CODES: tuple[str, ...] = (
    "BAR_OHLC_ORDER_VIOLATION",
    "BAR_NONPOSITIVE_PRICE",
    "BAR_INTERVAL_OVERLAP",
    "BAR_INTERVAL_DUPLICATE",
    "BAR_PRECISION_LOSS",
)

#: Bar extension codes that flag SUSPECT (calendar membership is an
#: asset-adapter rule per the freeze; an outside-calendar bar is suspect
#: evidence, not deletion).
BAR_SUSPECT_CODES: tuple[str, ...] = ("BAR_OUTSIDE_CALENDAR",)

#: Bar extension codes that classify COMPLETENESS only (never degrade
#: quality_status: a genuinely non-evaluable volume is not a quality defect
#: and is never patched with a zero).
BAR_COMPLETENESS_CODES: tuple[str, ...] = ("BAR_VOLUME_NOT_EVALUABLE",)

#: Every reason code a mdp.market_bar@2 bar may carry:
#: reason_codes@1 (whole registry, unmodified) + the frozen @2 extension.
ALL_BAR_REASON_CODES = frozenset(_rc.CODES) | frozenset(BAR_REASON_CODES)

#: Bar completeness vocabulary (quality_status vocabulary is reused from
#: models.QUALITY_STATUSES — the @1 enum, unmodified).
BAR_COMPLETENESS_STATUSES: tuple[str, ...] = (
    "COMPLETE", "NOT_EVALUABLE", "GAPS_PRESENT",
)

#: Volume-class fields: null => NOT_EVALUABLE + BAR_VOLUME_NOT_EVALUABLE.
VOLUME_FIELDS: tuple[str, ...] = (
    "volume", "quote_volume", "trade_count", "taker_buy_base", "taker_buy_quote",
)

OHLC_FIELDS: tuple[str, ...] = ("open", "high", "low", "close")

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


# --- strict availability sentinel -------------------------------------------

class _StrictAvailability:
    """Sentinel for the strict ``close_time <= available_time`` rule."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - display only
        return "STRICT"


#: Default ``availability_rule``: strict, fail-closed (no relaxation).
STRICT = _StrictAvailability()


# --- error family (frozen) ---------------------------------------------------

class BarError(ValueError):
    """Validation failure carrying a reason code from ALL_BAR_REASON_CODES.

    The bar-plane error family: reason codes come from reason_codes@1 (whole
    frozen registry, unmodified) plus the frozen mdp.bar_reason_codes@2
    extension set.  :class:`BarIntervalError` is the dedicated subclass for
    interval duplicate/overlap failures (fail-closed, never quarantine).
    """

    def __init__(self, reason_code: str, message: str):
        if reason_code not in ALL_BAR_REASON_CODES:
            raise AssertionError(f"internal error: unknown bar reason code {reason_code!r}")
        super().__init__(f"[{reason_code}] {message}")
        self.reason_code = reason_code


class BarIntervalError(BarError):
    """Duplicate or non-disjoint bar intervals (fail-closed, not quarantine).

    Raised for the same
    ``(instrument_id, bar_type, interval_ns, adjustment_mode)`` identity when
    two bars share an interval (BAR_INTERVAL_DUPLICATE) or their half-open
    ``[open_time, open_time + interval_ns)`` ranges intersect / go backwards
    in stream order (BAR_INTERVAL_OVERLAP).
    """


# --- helpers -----------------------------------------------------------------


def _malformed(message: str) -> BarError:
    return BarError("MALFORMED_SHAPE", message)


def _missing(message: str) -> BarError:
    return BarError("MISSING_REQUIRED_FIELD", message)


def _wrap_models_error(exc: _models.MarketDataPlaneError) -> BarError:
    """Re-cast a models error into the bar error family (same code+text)."""
    text = str(exc)
    prefix = f"[{exc.reason_code}] "
    if text.startswith(prefix):
        text = text[len(prefix):]
    return BarError(exc.reason_code, text)


def _is_plain_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _fractional_digits(d: Decimal) -> int:
    return max(0, -d.as_tuple().exponent)


def _validated_hash64(value, field: str) -> str:
    if not isinstance(value, str) or not _HEX64_RE.match(value):
        raise _malformed(f"{field} must be lowercase hex sha256 (64 chars)")
    return value


def _validated_identifier(value, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise _malformed(f"{field} must be a non-empty string")
    return value


def _validated_reason_codes(value) -> list[str]:
    """Canonicalise reason_codes to a sorted unique list of known codes.

    Codes may come from reason_codes@1 OR the mdp.bar_reason_codes@2
    extension (the @1 registry is never mutated by this module).
    """
    if value is None:
        return []
    if not isinstance(value, list):
        raise _malformed("reason_codes must be a list")
    for code in value:
        if not isinstance(code, str) or code not in ALL_BAR_REASON_CODES:
            raise _malformed(
                f"reason code outside reason_codes@1 + mdp.bar_reason_codes@2: {code!r}")
    return sorted(set(value))


def _bar_decimal(value, declared_precision: int, *, field: str,
                 positive: bool, required: bool):
    """Apply the frozen bar decimal rules; return the canonical string/None.

    Mirrors the models.py decimal discipline (canonical fixed-point strings,
    trailing-zero normalisation only when lossless) with the bar-specific
    frozen strictness: binary float input is REJECTED (no floats anywhere in
    the bar model) and a value not exactly representable at the declared
    precision raises BAR_PRECISION_LOSS (the @2 extension code).
    """
    if value is None:
        if required:
            raise _missing(f"{field} is required")
        return None
    if isinstance(value, bool):
        raise _malformed(f"{field}: bool is not a decimal value")
    if isinstance(value, float):
        raise _malformed(
            f"{field}: float input rejected; mdp.market_bar@2 carries no "
            f"binary floats — supply an exact decimal string")
    if isinstance(value, Decimal):
        d = value
    elif isinstance(value, int):
        d = Decimal(value)
    elif isinstance(value, str):
        try:
            d = _models.decimal_string_to_decimal(value)
        except _models.MarketDataPlaneError as exc:
            raise _wrap_models_error(exc) from exc
    else:
        raise _malformed(
            f"{field}: unsupported decimal input type {type(value).__name__}")

    if not d.is_finite():
        raise BarError("NON_FINITE_PRICE", f"{field}: non-finite value")
    if positive and d <= 0:
        # BAR_NONPOSITIVE_PRICE subsumes negatives for the frozen
        # "positive prices" OHLC rule.
        raise BarError("BAR_NONPOSITIVE_PRICE",
                       f"{field}: {_models.to_fixed_point_string(d)} must be positive")
    if not positive and d < 0:
        raise BarError("NEGATIVE_SIZE",
                       f"{field}: {_models.to_fixed_point_string(d)}")

    if _fractional_digits(d) > declared_precision:
        # PRECISION_LOSS only when the VALUE is not exactly representable at
        # the declared precision; trailing-zero artifacts are losslessly
        # normalised (same semantics as models).
        from decimal import localcontext
        with localcontext() as ctx:
            ctx.prec = max(len(d.as_tuple().digits) + declared_precision, 60)
            stripped = d.normalize()
        if _fractional_digits(stripped) > declared_precision:
            raise BarError(
                "BAR_PRECISION_LOSS",
                f"{field}: {_models.to_fixed_point_string(d)} exceeds declared "
                f"precision {declared_precision}")
        d = stripped
    return _models.to_fixed_point_string(d)


# --- identity ----------------------------------------------------------------

def compute_bar_id(identity_fields: dict) -> str:
    """bar_id = sha256 of canonical_json of the frozen identity tuple.

    Exactly the IDENTITY_FIELDS entries, canonical_json-serialised
    (sort_keys/compact/ensure_ascii — frozen canonical form) and hashed.
    """
    material = {field: identity_fields[field] for field in IDENTITY_FIELDS}
    return hashlib.sha256(
        _models.canonical_json(material).encode("utf-8")).hexdigest()


# --- status (documented @1 reuse) --------------------------------------------

def bar_status_from_codes(reason_codes) -> str:
    """Frozen final-status rule over bar reason codes.

    REUSE (noted per freeze bar_contract.bar_reason_codes_extension): the
    status vocabulary and final-status rule are the @1 ones —
    quality.status_from_codes / reason_codes.final_status_for (INVALID if any
    rejection code, else SUSPECT if any suspect code, else VALID).  The
    mdp.bar_reason_codes@2 extension codes are classified by the frozen local
    tables BAR_REJECT_CODES / BAR_SUSPECT_CODES because reason_codes@1's
    frozen classes cannot be mutated; BAR_VOLUME_NOT_EVALUABLE is a
    completeness classification and never degrades quality_status.
    """
    codes = list(reason_codes)
    for code in codes:
        if _rc.is_rejection(code) or code in BAR_REJECT_CODES:
            return "INVALID"
    for code in codes:
        if _rc.is_suspect(code) or code in BAR_SUSPECT_CODES:
            return "SUSPECT"
    return "VALID"


# --- time order ---------------------------------------------------------------

def _check_time_order(open_ns: int, close_ns: int, available_ns: int,
                      availability_rule, candidate: dict) -> None:
    """Frozen time order: open < close <= available (strict, fail-closed).

    ``open_time < close_time`` is NEVER relaxable.  The
    ``close_time <= available_time`` leg may be relaxed ONLY by an explicit
    per-asset evidenced publication rule: ``availability_rule`` must be a
    callable that receives the candidate bar dict and returns a non-empty
    evidence string.  Any silent relaxation is forbidden: the default is
    :data:`STRICT`, a rule returning an empty/non-string evidence still
    raises, and the relaxed bar remains visibly anomalous in its persisted
    timestamps (it fails every strict re-validation).
    """
    if open_ns >= close_ns:
        raise BarError(
            "IMPOSSIBLE_TIME_ORDER",
            f"open_time_utc_ns ({open_ns}) must be strictly < close_time_utc_ns "
            f"({close_ns}); never relaxable")
    if close_ns <= available_ns:
        return
    if availability_rule is None or isinstance(availability_rule, _StrictAvailability):
        raise BarError(
            "IMPOSSIBLE_TIME_ORDER",
            f"close_time_utc_ns ({close_ns}) must be <= available_time_utc_ns "
            f"({available_ns}); pass an explicit evidenced availability_rule "
            f"to relax (default STRICT, never silent)")
    if not callable(availability_rule):
        raise _malformed(
            "availability_rule must be STRICT (default) or a callable "
            "returning a non-empty evidence string")
    evidence = availability_rule(candidate)
    if not isinstance(evidence, str) or not evidence:
        raise BarError(
            "IMPOSSIBLE_TIME_ORDER",
            "availability_rule refused or returned empty evidence; relaxation "
            "without evidence is forbidden (fail closed)")


# --- validation --------------------------------------------------------------

def validate_bar(bar, *, availability_rule=STRICT) -> dict:
    """Validate one mdp.market_bar@2 bar; return the canonical dict.

    Raises :class:`BarError` with the frozen reason code on any violation.
    Never mutates the input.  The returned dict contains every frozen field,
    satisfies ``validate_bar(validate_bar(b)) == validate_bar(b)`` and
    ``from_dict(to_dict(b)) == b``.
    """
    if not isinstance(bar, dict):
        raise _malformed("bar must be a dict")
    keys = set(bar.keys())
    fields = set(BAR_FIELDS)
    if not keys <= fields:
        extra = sorted(keys - fields)
        raise _malformed(f"unknown bar field(s): {extra}")
    if bar.get("schema_version") not in (None, SCHEMA_VERSION):
        raise _malformed(
            f"schema_version must be {SCHEMA_VERSION!r}, got {bar.get('schema_version')!r}")

    canonical = {field: bar.get(field) for field in BAR_FIELDS}
    canonical["schema_version"] = SCHEMA_VERSION

    for field in ("source_id", "provider_id", "venue", "instrument_id",
                  "asset_class", "bar_type", "normalizer_version"):
        _validated_identifier(canonical[field], field)

    _validated_hash64(canonical["raw_sha256"], "raw_sha256")
    _validated_hash64(canonical["manifest_sha256"], "manifest_sha256")
    if canonical["raw_id"] is None:
        # Frozen @2 rule: raw_id equals raw_sha256 for row-derived bars.
        canonical["raw_id"] = canonical["raw_sha256"]
    _validated_hash64(canonical["raw_id"], "raw_id")
    if canonical["raw_id"] != canonical["raw_sha256"]:
        raise BarError(
            "HASH_DISAGREEMENT",
            f"raw_id {canonical['raw_id']} != raw_sha256 "
            f"{canonical['raw_sha256']} (frozen @2 row-derived identity)")

    if not _is_plain_int(canonical["interval_ns"]) or canonical["interval_ns"] <= 0:
        raise _malformed("interval_ns must be an int > 0")

    times = {}
    for field in ("open_time_utc_ns", "close_time_utc_ns", "available_time_utc_ns"):
        value = canonical[field]
        if value is None:
            raise _missing(f"{field} is required")
        try:
            times[field] = _models.timestamp_to_ns(value)
        except _models.MarketDataPlaneError as exc:
            raise _wrap_models_error(exc) from exc
        canonical[field] = times[field]
    _check_time_order(
        times["open_time_utc_ns"], times["close_time_utc_ns"],
        times["available_time_utc_ns"], availability_rule, canonical)

    price_precision = canonical["price_precision"]
    size_precision = canonical["size_precision"]
    # Bar precision fields are POSITIVE ints (bar_contract field_rules); the
    # @1 event floor (>= 0) is deliberately tightened here as frozen.
    if not _is_plain_int(price_precision) or price_precision < 1:
        raise _malformed("price_precision must be an int >= 1")
    if not _is_plain_int(size_precision) or size_precision < 1:
        raise _malformed("size_precision must be an int >= 1")

    for field in OHLC_FIELDS:
        canonical[field] = _bar_decimal(
            canonical[field], price_precision, field=field,
            positive=True, required=True)
    open_d, high_d, low_d, close_d = (
        _models.decimal_string_to_decimal(canonical[f]) for f in OHLC_FIELDS)
    if high_d < open_d or high_d < close_d or high_d < low_d or \
            low_d > open_d or low_d > close_d or low_d > high_d:
        raise BarError(
            "BAR_OHLC_ORDER_VIOLATION",
            f"high ({canonical['high']}) must be >= max(open, close, low) and "
            f"low ({canonical['low']}) must be <= min(open, close, high) "
            f"[open={canonical['open']}, close={canonical['close']}]")

    null_volume_fields = []
    for field in ("volume", "quote_volume", "taker_buy_base", "taker_buy_quote"):
        canonical[field] = _bar_decimal(
            canonical[field], size_precision, field=field,
            positive=False, required=False)
        if canonical[field] is None:
            null_volume_fields.append(field)
    trade_count = canonical["trade_count"]
    if trade_count is not None and (not _is_plain_int(trade_count) or trade_count < 0):
        raise _malformed("trade_count must be an int >= 0, or null when not "
                         "evaluable (NEVER a zero substitute)")
    if trade_count is None:
        null_volume_fields.append("trade_count")

    # Completeness: any null volume-class field => NOT_EVALUABLE with the
    # frozen code; never zero.  The code is added deterministically (and
    # must not contradict an all-present stream).
    if null_volume_fields:
        canonical["completeness_status"] = "NOT_EVALUABLE"
        codes = set(_validated_reason_codes(canonical["reason_codes"]))
        codes.add("BAR_VOLUME_NOT_EVALUABLE")
        canonical["reason_codes"] = sorted(codes)
    else:
        canonical["completeness_status"] = "COMPLETE"
        codes = _validated_reason_codes(canonical["reason_codes"])
        if "BAR_VOLUME_NOT_EVALUABLE" in codes:
            raise _malformed(
                "BAR_VOLUME_NOT_EVALUABLE present but all volume-class fields "
                "are non-null (contradictory completeness evidence)")
        canonical["reason_codes"] = codes
    if canonical["completeness_status"] not in BAR_COMPLETENESS_STATUSES:
        raise _malformed(
            f"completeness_status {canonical['completeness_status']!r} outside "
            f"{BAR_COMPLETENESS_STATUSES}")

    mode = canonical["adjustment_mode"]
    if mode not in ADJUSTMENT_MODES:
        raise _malformed(f"adjustment_mode {mode!r} outside {ADJUSTMENT_MODES}")
    ref = canonical["corporate_action_ref"]
    if mode == "CORP_ACTION_ADJUSTED":
        if ref is None:
            raise _missing(
                "CORP_ACTION_ADJUSTED requires a non-null corporate_action_ref")
        _validated_identifier(ref, "corporate_action_ref")
    elif ref is not None:
        # Identity hygiene: a corporate-action reference on a RAW bar blurs
        # the raw/adjusted identity split (raw_vs_adjusted field rule).
        raise _malformed(
            "RAW bars must carry a null corporate_action_ref; adjusted bars "
            "are a different identity (adjustment_mode=CORP_ACTION_ADJUSTED)")

    status = canonical["quality_status"]
    if status is None:
        # No bar is VALID merely because parsing succeeded (models discipline).
        status = "QUARANTINED"
    if status not in _models.QUALITY_STATUSES:
        raise _malformed(f"quality_status {status!r} outside frozen enum")
    canonical["quality_status"] = status

    # bar_id: computed from the canonical identity tuple; a supplied
    # disagreeing id is HASH_DISAGREEMENT (fail closed).
    computed_id = compute_bar_id(canonical)
    supplied_id = bar.get("bar_id")
    if supplied_id is None:
        canonical["bar_id"] = computed_id
    else:
        _validated_hash64(supplied_id, "bar_id")
        if supplied_id != computed_id:
            raise BarError(
                "HASH_DISAGREEMENT",
                f"supplied bar_id {supplied_id} != computed {computed_id}")
        canonical["bar_id"] = supplied_id

    return canonical


def build_bar(fields: dict | None = None, *, availability_rule=STRICT,
              **kwargs) -> dict:
    """Construct a canonical mdp.market_bar@2 bar from partial fields.

    Every frozen field omitted here is filled with an explicit null;
    ``raw_id`` defaults to ``raw_sha256`` and ``bar_id`` is computed from the
    frozen identity tuple.  ``completeness_status`` and the
    BAR_VOLUME_NOT_EVALUABLE code are derived deterministically from the
    volume-class nulls; ``quality_status`` defaults to ``QUARANTINED``
    (never VALID merely because parsing succeeded).
    """
    if fields and kwargs:
        raise ValueError("pass either a dict or kwargs, not both")
    source = dict(fields) if fields is not None else dict(kwargs)
    unknown = set(source) - set(BAR_FIELDS)
    if unknown:
        raise _malformed(f"unknown bar field(s): {sorted(unknown)}")
    candidate = {field: source.get(field) for field in BAR_FIELDS}
    if candidate["schema_version"] is None:
        candidate["schema_version"] = SCHEMA_VERSION
    return validate_bar(candidate, availability_rule=availability_rule)


def to_dict(bar: dict) -> dict:
    """Deep copy of a canonical bar dict (round-trip half)."""
    if not isinstance(bar, dict):
        raise _malformed("bar must be a dict")
    return deepcopy(bar)


def from_dict(raw) -> dict:
    """Validate + canonicalise a raw bar dict (round-trip half)."""
    return validate_bar(raw)


def set_quality(bar: dict, quality_status: str, reason_codes) -> dict:
    """Return a copy of *bar* with quality fields replaced (validated).

    Mirrors models.set_quality.  The completeness classification
    (BAR_VOLUME_NOT_EVALUABLE on a NOT_EVALUABLE bar) is preserved/added
    deterministically so the result always re-validates.
    """
    if quality_status not in _models.QUALITY_STATUSES:
        raise _malformed(f"quality_status {quality_status!r} outside frozen enum")
    updated = deepcopy(bar)
    updated["quality_status"] = quality_status
    updated["reason_codes"] = list(reason_codes)
    return validate_bar(updated)
