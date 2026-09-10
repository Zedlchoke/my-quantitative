"""Binance USDM kline -> mdp.market_bar@2 crypto adapter (lane A5, MDP-V2).

Freeze authority: research/control/market_data_plane_v2_run/architecture_freeze_v2.json,
sections "adapters" (frozen_interface + adapters.crypto) and "bar_contract".
This module is purely ADDITIVE: it lives in the adapters/crypto namespace and
imports only stdlib + the frozen sibling modules (bars, bar_stream, models).
The namespace is a PEP 420 namespace package — there is deliberately NO
``__init__.py`` here; with ``<repo>/research`` on sys.path the import is::

    from market_data_plane.adapters.crypto import kline

Frozen interface implemented (adapters.frozen_interface):

* :func:`normalize_bar` — ONE raw Binance USDM kline JSON record -> ONE
  validated canonical mdp.market_bar@2 dict via ``bars.build_bar``; any
  violation raises (fail closed).
* :func:`normalize_stream` — ordered normalization of a kline stream:
  per-record failures are QUARANTINED with frozen reason codes (counted,
  never silently dropped) while interval duplicate/overlap failures are
  FAIL-CLOSED (:class:`bars.BarIntervalError`), reusing
  ``bar_stream.normalize_bar_stream`` semantics.
* :func:`check_coverage` — continuous 24/7 calendar coverage report
  (expected slots = ceil(span / interval); unexplained gaps classified).
* :func:`project_decision_schedule` — schedule-only decision rows at bar
  close with EXACTLY ONE completed-bar lag.  NO PnL, NO returns, NO
  position/size numbers, NO ranking — placeholder constants only.

Frozen crypto rules honoured here (adapters.crypto):

* identity: venue ``BINANCE_USDM``; instrument_id = raw symbol (e.g.
  ``BTCUSDT``); asset_class ``crypto_perpetual``; the perpetual contract
  identity is asserted via the :class:`AdapterContext` instrument table —
  a symbol outside the table is UNKNOWN_INSTRUMENT (fail closed).
* clock: continuous 24/7; kline open_time milliseconds -> nanoseconds
  EXACTLY ONCE at the frozen conversion helper :func:`_ms_to_ns` (the
  module contains exactly one ms->ns conversion literal, pinned by a
  structural test).  Re-normalizing an already-converted nanosecond record
  FAILS CLOSED (the helper rejects non-plausible epoch-ms magnitudes).
* close_time_rule: close_time_ns = open_time_ns + interval_ns minus one
  millisecond (Binance kline inclusive-close ms rule).  The record's own
  ``close_time`` must agree exactly, else IMPOSSIBLE_TIME_ORDER.
* availability_rule: available_time = close_time (frozen CLOSE_TIME rule);
  the strict bar time-order check therefore always passes unrelaxed.
* interval_aggregation: 1m->2m aggregation ONLY from complete adjacent 1m
  bars with the frozen boundary rule (exact slot set per target window);
  direct Binance 2m is NOT claimed — :func:`aggregate_bars` refuses to be
  labeled provider-native (required ``derived_label`` keyword).
* aggtrades_event_path: OPTIONAL synthetic-only TRADE event adapter —
  NOT implemented in this lane (skipped; noted in the lane handoff).

raw_sha256 bytes rule (FROZEN, documented): the "exact raw record bytes"
are ``models.canonical_json(dict(raw_record)).encode("utf-8")`` — i.e. the
canonical JSON serialization (sort_keys, compact separators, ensure_ascii,
allow_nan=False) of the record EXACTLY as passed, computed BEFORE any
coercion, defaulting, or field reordering.  The rule is byte-stable and
key-order independent; it hashes the provider values verbatim (decimal
strings stay strings; ints stay ints).

Record shape (frozen): the 11 Binance USDM kline fields
``open_time, open, high, low, close, volume, close_time,
quote_asset_volume, number_of_trades, taker_buy_base_volume,
taker_buy_quote_volume`` (epoch-ms ints and decimal strings) plus AT MOST
the retriever envelope key ``symbol`` naming the instrument.  Any other
key fails closed (MALFORMED_SHAPE); a missing provider field fails closed
(MISSING_REQUIRED_FIELD); an unknown ``symbol`` fails closed
(UNKNOWN_INSTRUMENT).

Quarantine slot attribution: a quarantined record carries
``open_time_utc_ns`` / ``instrument_id`` ONLY when its identity and epoch
fields were parseable enough to place it on the clock (the same frozen
helper, so an already-ns epoch is never attributed).  check_coverage uses
these to classify a missing slot as quarantine-explained; everything else
is conservatively UNEXPLAINED.

stdlib + sibling modules only; never mutates its inputs; no network.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping

from market_data_plane import bar_stream as _bar_stream
from market_data_plane import bars as _bars
from market_data_plane import models as _models

__all__ = [
    "ASSET_CLASS",
    "AVAILABILITY_CLOSE_TIME",
    "AdapterContext",
    "AdapterResult",
    "CoverageReport",
    "DERIVED_PROVENANCE_LABEL",
    "InstrumentCoverage",
    "InstrumentSpec",
    "KLINE_FIELDS",
    "SCHEDULE_SIGNAL_PLACEHOLDER",
    "SCHEDULE_TARGET_PLACEHOLDER",
    "VENUE",
    "aggregate_bars",
    "check_coverage",
    "interval_name",
    "normalize_bar",
    "normalize_stream",
    "project_decision_schedule",
    "raw_record_bytes",
]

# --- frozen identity constants (adapters.crypto) -----------------------------

VENUE = "BINANCE_USDM"
ASSET_CLASS = "crypto_perpetual"

#: Frozen availability declaration: available_time = close_time.  The crypto
#: kline adapter implements exactly this rule and no other.
AVAILABILITY_CLOSE_TIME = "CLOSE_TIME"

#: The 11 frozen Binance USDM kline provider fields (order as listed in the
#: lane freeze; the adapter accepts them in any key order).
KLINE_FIELDS: tuple[str, ...] = (
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_asset_volume", "number_of_trades", "taker_buy_base_volume",
    "taker_buy_quote_volume",
)

#: The single allowed retriever envelope key naming the instrument.
SYMBOL_ENVELOPE_KEY = "symbol"

#: Frozen ms -> ns factor.  The ONLY occurrence of this conversion literal in
#: this module is this definition: every conversion goes through
#: :func:`_ms_to_ns` (a structural test pins the source to exactly one
#: occurrence so no second conversion site can be introduced silently).
_MS_TO_NS = 1_000_000

#: Plausible epoch-ms magnitude window (0 < ms <= 2100-01-01T00:00:00Z in ms).
#: An already-converted nanosecond value exceeds it and fails closed here —
#: the single conversion point is self-defending against double conversion.
_MS_EPOCH_MAX = 4_102_444_800_000

#: Schedule placeholders: the data plane projects SCHEDULE ONLY.  Targets,
#: signals, positions, sizes, PnL and selection belong to strategy lanes.
SCHEDULE_TARGET_PLACEHOLDER = "SCHEDULE_TARGET_PLACEHOLDER"
SCHEDULE_SIGNAL_PLACEHOLDER = "SCHEDULE_SIGNAL_PLACEHOLDER"

#: The one provenance label :func:`aggregate_bars` accepts.  Derived bars are
#: adapter artifacts, never provider-native rows; direct Binance 2m is NOT
#: claimed (freeze: interval_aggregation boundary rule).
DERIVED_PROVENANCE_LABEL = "ADAPTER_DERIVED_AGGREGATION"

#: Suffix appended to normalizer_version on derived (aggregated) bars —
#: in-band evidence that the row is an adapter artifact.
_DERIVED_VERSION_SUFFIX = "+agg"

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


# --- errors -------------------------------------------------------------------

def _bar_error(reason_code: str, message: str) -> _bars.BarError:
    return _bars.BarError(reason_code, message)


def _plain_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


# --- frozen conversion helper (single ms->ns site) ------------------------------

def _ms_to_ns(ms) -> int:
    """Frozen Binance kline epoch-ms -> epoch-ns conversion (EXACTLY ONCE).

    This helper is the single conversion point in the adapter (the structural
    test pins the module source to exactly one conversion literal).  It is
    fail-closed both ways:

    * non-integer input -> MALFORMED_SHAPE (Binance kline epochs are ms ints;
      strings, floats and bools are refused);
    * a value outside the plausible epoch-ms magnitude window ->
      IMPOSSIBLE_TIME_ORDER.  Re-normalizing an ALREADY-CONVERTED nanosecond
      record therefore fails closed here instead of silently double-scaling
      the timestamps.
    """
    if not _plain_int(ms):
        raise _bar_error(
            "MALFORMED_SHAPE",
            f"kline epoch fields must be int milliseconds, got {type(ms).__name__}")
    if ms <= 0 or ms > _MS_EPOCH_MAX:
        raise _bar_error(
            "IMPOSSIBLE_TIME_ORDER",
            f"kline epoch value {ms} is not a plausible epoch-millisecond "
            f"timestamp (must satisfy 0 < ms <= {_MS_EPOCH_MAX}); "
            f"already-converted nanosecond values must not be re-normalized — "
            f"ms->ns conversion happens exactly once at this helper")
    return ms * _MS_TO_NS


def raw_record_bytes(raw_record: Mapping) -> bytes:
    """The FROZEN exact raw-record bytes rule (see module docstring).

    canonical_json of the record EXACTLY as passed — computed before any
    coercion — encoded UTF-8.  Raises BarError(MALFORMED_SHAPE) when the
    record is not canonically serialisable.
    """
    try:
        return _models.canonical_json(dict(raw_record)).encode("utf-8")
    except _models.MarketDataPlaneError as exc:
        raise _bar_error(
            "MALFORMED_SHAPE",
            f"raw kline record is not canonically serialisable: {exc}") from exc


def _raw_sha256(raw_record: Mapping) -> str:
    return hashlib.sha256(raw_record_bytes(raw_record)).hexdigest()


# --- frozen context ---------------------------------------------------------------

@dataclass(frozen=True)
class InstrumentSpec:
    """Per-instrument contract identity asserted by the adapter context table.

    The freeze (adapters.crypto.identity) pins venue BINANCE_USDM and
    asset_class crypto_perpetual; this spec asserts exactly that identity —
    any other value fails closed at construction.  ``price_precision`` /
    ``size_precision`` are the DECLARED provider precisions the bar decimal
    discipline is checked against (BAR_PRECISION_LOSS beyond them).
    """

    symbol: str
    price_precision: int
    size_precision: int
    venue: str = VENUE
    asset_class: str = ASSET_CLASS

    def __post_init__(self):
        if not isinstance(self.symbol, str) or not self.symbol:
            raise _bar_error("MALFORMED_SHAPE", "symbol must be a non-empty string")
        if self.venue != VENUE or self.asset_class != ASSET_CLASS:
            raise _bar_error(
                "MALFORMED_SHAPE",
                f"crypto adapter asserts venue {VENUE!r} / asset_class "
                f"{ASSET_CLASS!r}; got {self.venue!r} / {self.asset_class!r}")
        for name in ("price_precision", "size_precision"):
            value = getattr(self, name)
            if not _plain_int(value) or value < 1:
                raise _bar_error(
                    "MALFORMED_SHAPE",
                    f"{name} must be an int >= 1 (bar model floor), got {value!r}")


@dataclass(frozen=True)
class AdapterContext:
    """Frozen crypto adapter context (adapters.frozen_interface).

    * ``instruments`` — the instrument table: symbol -> InstrumentSpec
      (contract identity + declared precisions).  Unknown symbols fail
      closed (UNKNOWN_INSTRUMENT).
    * ``interval_ns`` — the frozen bar interval for this stream.
    * ``availability_rule`` — frozen to AVAILABILITY_CLOSE_TIME: the adapter
      implements exactly ``available_time = close_time`` and refuses any
      other rule (fail closed).
    * ``manifest_sha256`` — the upstream retrieval manifest id every bar
      carries (bar_contract.identity_rules.manifest_sha256; mirrors A3_Q4).
    * ``schedule_target`` / ``schedule_signal`` — the declared placeholder
      constants copied verbatim into decision-schedule rows.
    """

    instruments: Mapping[str, InstrumentSpec]
    interval_ns: int
    manifest_sha256: str
    availability_rule: str = AVAILABILITY_CLOSE_TIME
    source_id: str = "binance_usdm_kline"
    provider_id: str = "BINANCE"
    normalizer_version: str = "2"
    schedule_target: str = SCHEDULE_TARGET_PLACEHOLDER
    schedule_signal: str = SCHEDULE_SIGNAL_PLACEHOLDER

    def __post_init__(self):
        if not isinstance(self.instruments, Mapping) or not self.instruments:
            raise _bar_error(
                "MALFORMED_SHAPE",
                "instruments must be a non-empty symbol -> InstrumentSpec table")
        for symbol, spec in self.instruments.items():
            if not isinstance(symbol, str) or not symbol:
                raise _bar_error(
                    "MALFORMED_SHAPE",
                    "instrument table keys must be non-empty strings")
            if not isinstance(spec, InstrumentSpec):
                raise _bar_error(
                    "MALFORMED_SHAPE",
                    f"instrument table entry for {symbol!r} must be an InstrumentSpec")
            if spec.symbol != symbol:
                raise _bar_error(
                    "MALFORMED_SHAPE",
                    f"instrument table key {symbol!r} != spec symbol {spec.symbol!r}")
        if not _plain_int(self.interval_ns) or self.interval_ns <= 0:
            raise _bar_error("MALFORMED_SHAPE", "interval_ns must be an int > 0")
        if self.interval_ns % _MS_TO_NS:
            raise _bar_error(
                "MALFORMED_SHAPE",
                f"crypto kline intervals are whole milliseconds; interval_ns "
                f"{self.interval_ns} is not")
        if self.availability_rule != AVAILABILITY_CLOSE_TIME:
            raise _bar_error(
                "MALFORMED_SHAPE",
                f"crypto kline adapter implements exactly "
                f"{AVAILABILITY_CLOSE_TIME!r} availability (available = close); "
                f"got {self.availability_rule!r}")
        if not isinstance(self.manifest_sha256, str) \
                or not _HEX64_RE.match(self.manifest_sha256):
            raise _bar_error(
                "MALFORMED_SHAPE",
                "manifest_sha256 must be lowercase hex sha256 (64 chars)")
        for name in ("source_id", "provider_id", "normalizer_version",
                     "schedule_target", "schedule_signal"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise _bar_error(
                    "MALFORMED_SHAPE", f"{name} must be a non-empty string")


@dataclass(frozen=True)
class AdapterResult:
    """Frozen normalize_stream result (counts + gap accounting + quarantine).

    ``bars`` are canonical validated mdp.market_bar@2 dicts in input order.
    ``quarantined`` records are counted with frozen reason codes and are
    NEVER silently dropped.  Interval duplicate/overlap failures do not
    reach this result — they raise BarIntervalError (fail closed).
    """

    bars: tuple
    quarantined: tuple
    total_count: int
    accepted_count: int
    quarantined_count: int
    completeness_status: str | None
    gap_reasons: tuple
    gaps: tuple
    stream_digest: str
    stream_byte_length: int


@dataclass(frozen=True)
class InstrumentCoverage:
    """Per-instrument continuous 24/7 calendar coverage row."""

    instrument_id: str
    first_open_time_utc_ns: int | None
    last_open_time_utc_ns: int | None
    expected_slots: int
    observed_bars: int
    missing_slots: int
    explained_missing_slots: int
    unexplained_missing_slots: int


@dataclass(frozen=True)
class CoverageReport:
    """Frozen continuous 24/7 coverage report (adapters.frozen_interface).

    ``expected_slots`` = ceil(span / interval_ns) per instrument, where the
    span covers first open through last close (inclusive) over accepted bars
    PLUS quarantine-attributable kline opens (a quarantined record is
    evidence the window intended a slot the accepted stream does not carry).
    Missing slots covered by quarantine attribution are EXPLAINED; every
    other missing slot is UNEXPLAINED.  ``duplicate_count`` is structurally
    always 0 — duplicates/overlaps fail closed upstream (BarIntervalError)
    and can never reach a result; the count is reported to make the
    invariant visible rather than implied.
    """

    calendar: str
    interval_ns: int
    instrument_reports: tuple
    expected_slots: int
    observed_bars: int
    quarantined_records: int
    duplicate_count: int
    gap_count: int
    explained_missing_slots: int
    unexplained_missing_slots: int
    completeness_status: str
    duplicate_invariant: str = (
        "duplicates impossible: BAR_INTERVAL_DUPLICATE/OVERLAP fail closed "
        "upstream (BarIntervalError); count is structurally 0")


# --- normalize_bar ------------------------------------------------------------------

def _resolve_spec(raw_record: Mapping, context: AdapterContext) -> InstrumentSpec:
    """Resolve the instrument spec; UNKNOWN_INSTRUMENT outside the table."""
    symbol = raw_record.get(SYMBOL_ENVELOPE_KEY)
    if symbol is None:
        if len(context.instruments) == 1:
            return next(iter(context.instruments.values()))
        raise _bar_error(
            "MISSING_REQUIRED_FIELD",
            f"kline record carries no {SYMBOL_ENVELOPE_KEY!r} envelope and the "
            f"context instrument table has {len(context.instruments)} entries; "
            f"the instrument is ambiguous")
    if not isinstance(symbol, str):
        raise _bar_error(
            "MALFORMED_SHAPE",
            f"{SYMBOL_ENVELOPE_KEY!r} envelope must be a string instrument symbol")
    spec = context.instruments.get(symbol)
    if spec is None:
        raise _bar_error(
            "UNKNOWN_INSTRUMENT",
            f"symbol {symbol!r} is not in the adapter context instrument table "
            f"(fail closed)")
    return spec


def normalize_bar(raw_record: Mapping, context: AdapterContext) -> dict:
    """ONE raw Binance USDM kline record -> ONE validated mdp.market_bar@2.

    Fail closed on any violation (raises BarError with the frozen reason
    code).  ms->ns conversion happens EXACTLY ONCE here via :func:`_ms_to_ns`.
    close_time_ns = open_time_ns + interval_ns minus one millisecond (Binance
    inclusive-close rule, cross-checked against the record's own close_time);
    available_time_ns = close_time_ns (frozen CLOSE_TIME availability).
    Provider decimal strings are passed through VERBATIM to
    ``bars.build_bar`` (trailing zeros survive when the declared precision
    accommodates them; precision beyond the declaration is BAR_PRECISION_LOSS).
    """
    if not isinstance(raw_record, Mapping):
        raise _bar_error(
            "MALFORMED_SHAPE",
            f"raw kline record must be a Mapping, got {type(raw_record).__name__}")

    # Exact raw-record bytes are frozen FIRST (before any coercion).
    raw_sha256 = _raw_sha256(raw_record)

    keys = set(raw_record.keys())
    missing = [name for name in KLINE_FIELDS if name not in keys]
    if missing:
        raise _bar_error(
            "MISSING_REQUIRED_FIELD",
            f"kline record missing provider field(s): {sorted(missing)}")
    extra = sorted(keys - set(KLINE_FIELDS) - {SYMBOL_ENVELOPE_KEY})
    if extra:
        raise _bar_error(
            "MALFORMED_SHAPE",
            f"kline record carries unknown field(s) {extra}; the frozen shape "
            f"is the 11 provider fields plus at most the "
            f"{SYMBOL_ENVELOPE_KEY!r} envelope key")

    spec = _resolve_spec(raw_record, context)

    open_ms = raw_record["open_time"]
    open_ns = _ms_to_ns(open_ms)
    record_close_ns = _ms_to_ns(raw_record["close_time"])
    interval_ms = context.interval_ns // _MS_TO_NS
    if open_ms % interval_ms:
        # Binance kline opens are exact interval-grid multiples (UTC-aligned);
        # a non-aligned open is inconsistent with the declared interval.
        raise _bar_error(
            "MALFORMED_SHAPE",
            f"kline open_time {open_ms} is not aligned to the {interval_ms}ms "
            f"interval grid for interval_ns {context.interval_ns}")
    expected_close_ns = open_ns + context.interval_ns - _MS_TO_NS
    if record_close_ns != expected_close_ns:
        raise _bar_error(
            "IMPOSSIBLE_TIME_ORDER",
            f"kline close_time {raw_record['close_time']}ms disagrees with the "
            f"frozen close rule (open_time + interval - 1 ms) for interval_ns "
            f"{context.interval_ns}")

    close_ns = expected_close_ns
    available_ns = close_ns  # frozen CLOSE_TIME availability rule

    return _bars.build_bar({
        "source_id": context.source_id,
        "provider_id": context.provider_id,
        "venue": spec.venue,
        "instrument_id": spec.symbol,
        "asset_class": spec.asset_class,
        "bar_type": f"{interval_name(context.interval_ns)}-LAST",
        "interval_ns": context.interval_ns,
        "open_time_utc_ns": open_ns,
        "close_time_utc_ns": close_ns,
        "available_time_utc_ns": available_ns,
        "open": raw_record["open"],
        "high": raw_record["high"],
        "low": raw_record["low"],
        "close": raw_record["close"],
        "volume": raw_record["volume"],
        "quote_volume": raw_record["quote_asset_volume"],
        "trade_count": raw_record["number_of_trades"],
        "taker_buy_base": raw_record["taker_buy_base_volume"],
        "taker_buy_quote": raw_record["taker_buy_quote_volume"],
        "price_precision": spec.price_precision,
        "size_precision": spec.size_precision,
        "adjustment_mode": "RAW",
        "corporate_action_ref": None,
        "raw_sha256": raw_sha256,
        "manifest_sha256": context.manifest_sha256,
        "normalizer_version": context.normalizer_version,
    })


# --- normalize_stream -----------------------------------------------------------------

def _quarantine_entry(index: int, record, exc: _bars.BarError) -> dict:
    """Quarantine record with frozen reason code (counted, never dropped).

    ``open_time_utc_ns`` / ``instrument_id`` are best-effort attributes used
    ONLY for coverage slot attribution: they are present only when the
    identity and epoch fields were parseable (plausible epoch-ms int, known
    symbol) — an already-ns epoch never passes the frozen helper and is
    never attributed.
    """
    symbol = None
    open_time_utc_ns = None
    if isinstance(record, Mapping):
        maybe_symbol = record.get(SYMBOL_ENVELOPE_KEY)
        if isinstance(maybe_symbol, str):
            symbol = maybe_symbol
        maybe_open_ms = record.get("open_time")
        if _plain_int(maybe_open_ms) and 0 < maybe_open_ms <= _MS_EPOCH_MAX:
            open_time_utc_ns = _ms_to_ns(maybe_open_ms)
    try:
        sha = _raw_sha256(record) if isinstance(record, Mapping) else None
    except _bars.BarError:
        sha = None
    return {
        "input_index": index,
        "reason_code": exc.reason_code,
        "message": str(exc),
        "raw_sha256": sha,
        "instrument_id": symbol,
        "open_time_utc_ns": open_time_utc_ns,
    }


def normalize_stream(raw_records, context: AdapterContext) -> AdapterResult:
    """Ordered stream normalization (adapters.frozen_interface.normalize_stream).

    Per-record normalization failures (malformed shape, missing fields,
    unknown instrument, precision loss, ...) are QUARANTINED with their
    frozen reason code and counted — never silently dropped.  Interval
    duplicate/overlap (and ordering / no-lookahead) violations in the
    accepted stream are FAIL-CLOSED: they raise
    :class:`bars.BarIntervalError` (or BarError) exactly as
    ``bar_stream.normalize_bar_stream`` does.  Gap accounting uses the
    continuous 24/7 clock: any missing kline slot is a gap (SEQUENCE_GAP
    reason, completeness GAPS_PRESENT).
    """
    records = list(raw_records)
    accepted: list[dict] = []
    quarantined: list[dict] = []
    for index, record in enumerate(records):
        try:
            accepted.append(normalize_bar(record, context))
        except _bars.BarError as exc:
            quarantined.append(_quarantine_entry(index, record, exc))

    # bar_stream semantics: ordering + disjointness + no-lookahead + gap
    # accounting over the accepted bars; duplicates/overlaps raise (fail
    # closed) and never quarantine.
    stream = _bar_stream.normalize_bar_stream(accepted)
    return AdapterResult(
        bars=tuple(stream["bars"]),
        quarantined=tuple(quarantined),
        total_count=len(records),
        accepted_count=len(accepted),
        quarantined_count=len(quarantined),
        completeness_status=stream["completeness_status"],
        gap_reasons=tuple(stream["gap_reasons"]),
        gaps=tuple(stream["gaps"]),
        stream_digest=stream["stream_digest"],
        stream_byte_length=stream["stream_byte_length"],
    )


# --- check_coverage ---------------------------------------------------------------------

def check_coverage(result: AdapterResult, context: AdapterContext) -> CoverageReport:
    """Continuous 24/7 calendar coverage (adapters.frozen_interface).

    Per instrument: expected slots = ceil(span / interval_ns) over the window
    [first open, last open + interval), where the window bounds cover the
    accepted bars PLUS quarantine-attributable kline opens.  Missing slots
    (expected grid minus accepted opens) covered by quarantine attribution
    are EXPLAINED; every other missing slot is UNEXPLAINED (conservative —
    attribution requires a parseable quarantine record on that exact slot).
    Duplicates are structurally impossible (fail closed upstream) and the
    report states that invariant with a count of 0.
    """
    accepted_by_symbol: dict[str, set] = {}
    attributable: dict[str, set] = {}
    for bar in result.bars:
        accepted_by_symbol.setdefault(bar["instrument_id"], set()).add(
            bar["open_time_utc_ns"])
    for entry in result.quarantined:
        symbol = entry.get("instrument_id")
        open_ns = entry.get("open_time_utc_ns")
        if symbol in context.instruments and open_ns is not None:
            attributable.setdefault(symbol, set()).add(open_ns)

    interval_ns = context.interval_ns
    rows: list[InstrumentCoverage] = []
    total_expected = total_observed = 0
    total_explained = total_unexplained = 0

    for symbol in sorted(set(accepted_by_symbol) | set(attributable)):
        accepted = accepted_by_symbol.get(symbol, set())
        known = accepted | attributable.get(symbol, set())
        first_open = min(known)
        last_open = max(known)
        span_ns = (last_open - first_open) + interval_ns
        expected_slots = -(-span_ns // interval_ns)  # exact ceil, positive ints
        grid = {first_open + k * interval_ns for k in range(expected_slots)}
        missing = sorted(grid - accepted)
        attr = attributable.get(symbol, set())
        explained = sum(1 for slot in missing if slot in attr)
        unexplained = len(missing) - explained
        rows.append(InstrumentCoverage(
            instrument_id=symbol,
            first_open_time_utc_ns=first_open,
            last_open_time_utc_ns=last_open,
            expected_slots=expected_slots,
            observed_bars=len(accepted),
            missing_slots=len(missing),
            explained_missing_slots=explained,
            unexplained_missing_slots=unexplained,
        ))
        total_expected += expected_slots
        total_observed += len(accepted)
        total_explained += explained
        total_unexplained += unexplained

    gap_count = sum(int(gap["missing_interval_count"]) for gap in result.gaps)
    return CoverageReport(
        calendar="CONTINUOUS_24_7",
        interval_ns=interval_ns,
        instrument_reports=tuple(rows),
        expected_slots=total_expected,
        observed_bars=total_observed,
        quarantined_records=result.quarantined_count,
        duplicate_count=0,
        gap_count=gap_count,
        explained_missing_slots=total_explained,
        unexplained_missing_slots=total_unexplained,
        completeness_status="GAPS_PRESENT" if result.gaps else "COMPLETE",
    )


# --- project_decision_schedule -------------------------------------------------------------

def project_decision_schedule(result: AdapterResult,
                              context: AdapterContext) -> list[dict]:
    """Schedule-only decision rows with EXACTLY ONE completed-bar lag.

    For bars b0..bn the schedule emits n rows: row i is scheduled at the
    close of reference bar b(i) (decision_utc_ns = close_time =
    available_time of b(i) — the moment exactly one completed bar is
    available) and references ONLY that completed bar's timestamps.  The
    next bar in sequence is the forward window; the decision strictly
    precedes its completion (no lookahead).  Rows carry ONLY timestamps,
    ids and the declared placeholder constants — NO PnL, NO returns, NO
    position/size numbers, NO ranking.
    """
    bars_ = list(result.bars)
    rows: list[dict] = []
    for index in range(len(bars_) - 1):
        ref = bars_[index]
        forward = bars_[index + 1]
        decision_utc_ns = ref["available_time_utc_ns"]
        if decision_utc_ns != ref["close_time_utc_ns"]:
            raise _bar_error(
                "IMPOSSIBLE_TIME_ORDER",
                "decision schedule requires CLOSE_TIME availability "
                "(available == close) on every reference bar")
        if not decision_utc_ns < forward["close_time_utc_ns"]:
            raise _bar_error(
                "IMPOSSIBLE_TIME_ORDER",
                "decision timestamp is not strictly before the forward bar's "
                "close; one-completed-bar lag violated (lookahead evidence)")
        rows.append({
            "decision_utc_ns": decision_utc_ns,
            "instrument_id": ref["instrument_id"],
            "reference_bar_open_time_utc_ns": ref["open_time_utc_ns"],
            "reference_bar_close_time_utc_ns": ref["close_time_utc_ns"],
            "reference_bar_available_time_utc_ns": ref["available_time_utc_ns"],
            "schedule_target": context.schedule_target,
            "schedule_signal": context.schedule_signal,
        })
    return rows


# --- interval aggregation (frozen boundary; provider-native NOT claimed) -----------

def interval_name(interval_ns: int) -> str:
    """Deterministic interval label (1m, 2m, 1h, 1d, ...; ns fallback)."""
    if not _plain_int(interval_ns) or interval_ns <= 0:
        raise _bar_error("MALFORMED_SHAPE", "interval_ns must be an int > 0")
    second_ns = _MS_TO_NS * 1000
    minute_ns = 60 * second_ns
    hour_ns = 60 * minute_ns
    day_ns = 24 * hour_ns
    week_ns = 7 * day_ns
    if interval_ns % week_ns == 0:
        return f"{interval_ns // week_ns}w"
    if interval_ns % day_ns == 0:
        return f"{interval_ns // day_ns}d"
    if interval_ns % hour_ns == 0:
        return f"{interval_ns // hour_ns}h"
    if interval_ns % minute_ns == 0:
        return f"{interval_ns // minute_ns}m"
    if interval_ns % second_ns == 0:
        return f"{interval_ns // second_ns}s"
    return f"{interval_ns}ns"


def aggregate_bars(source_bars, target_interval_ns: int,
                   context: AdapterContext, *, derived_label: str) -> list[dict]:
    """Aggregate validated bars to an exact-multiple target interval.

    FROZEN BOUNDARY (adapters.crypto.interval_aggregation): a target window
    ``[t, t + target)`` is emitted ONLY from EXACTLY the complete set of
    source slots ``t + k * source_interval`` it comprises — an incomplete
    group fails closed (SEQUENCE_GAP).  Direct Binance 2m is NOT claimed:
    ``derived_label`` MUST equal DERIVED_PROVENANCE_LABEL or this function
    refuses (fail closed) — aggregated rows are adapter artifacts, never
    provider-native records.  Derived identity rules: ``raw_sha256`` =
    sha256 of the canonical stream bytes of the exact source bars,
    ``normalizer_version`` = context version + ``+agg`` suffix (in-band
    derived labeling; bar_type stays the target interval name).
    """
    if derived_label != DERIVED_PROVENANCE_LABEL:
        raise _bar_error(
            "MALFORMED_SHAPE",
            "aggregated bars refuse provider-native labeling: direct Binance "
            "2m is NOT claimed; pass derived_label=DERIVED_PROVENANCE_LABEL "
            f"(got {derived_label!r})")
    if not _plain_int(target_interval_ns) or target_interval_ns <= 0:
        raise _bar_error("MALFORMED_SHAPE", "target_interval_ns must be an int > 0")
    source_interval = context.interval_ns
    if target_interval_ns <= source_interval or target_interval_ns % source_interval:
        raise _bar_error(
            "MALFORMED_SHAPE",
            f"target_interval_ns {target_interval_ns} must be an exact integer "
            f"multiple (> 1x) of the source interval {source_interval}")

    validated = [_bars.validate_bar(bar) for bar in source_bars]
    by_instrument: dict[str, list[dict]] = {}
    for bar in validated:
        if bar["interval_ns"] != source_interval or bar["adjustment_mode"] != "RAW":
            raise _bar_error(
                "MALFORMED_SHAPE",
                f"aggregate_bars aggregates RAW "
                f"{interval_name(source_interval)} source bars only; got "
                f"interval_ns={bar['interval_ns']}, "
                f"adjustment_mode={bar['adjustment_mode']!r}")
        for volume_field in ("volume", "quote_volume", "trade_count",
                             "taker_buy_base", "taker_buy_quote"):
            if bar[volume_field] is None:
                raise _bar_error(
                    "BAR_VOLUME_NOT_EVALUABLE",
                    f"cannot aggregate source bar at open_time_utc_ns "
                    f"{bar['open_time_utc_ns']}: {volume_field} is NOT_EVALUABLE "
                    f"(never zero-filled)")
        by_instrument.setdefault(bar["instrument_id"], []).append(bar)

    slots_per_group = target_interval_ns // source_interval
    target_type = f"{interval_name(target_interval_ns)}-LAST"
    aggregated: list[dict] = []
    for symbol in sorted(by_instrument):
        bars_i = sorted(by_instrument[symbol], key=lambda b: b["open_time_utc_ns"])
        groups: dict[int, list[dict]] = {}
        for bar in bars_i:
            groups.setdefault(bar["open_time_utc_ns"] // target_interval_ns,
                              []).append(bar)

        def _sum_decimal(members, field_name) -> str:
            total = Decimal(0)
            for member in members:
                total += Decimal(member[field_name])
            return _models.to_fixed_point_string(total)

        for group_start in sorted(groups):
            members = groups[group_start]
            window_open = group_start * target_interval_ns
            required_opens = [window_open + k * source_interval
                              for k in range(slots_per_group)]
            got_opens = [bar["open_time_utc_ns"] for bar in members]
            if got_opens != required_opens:
                raise _bar_error(
                    "SEQUENCE_GAP",
                    f"incomplete {interval_name(target_interval_ns)} window at "
                    f"open_time_utc_ns {window_open}: required source slots "
                    f"{required_opens}, got {got_opens} (fail closed; aggregate "
                    f"only complete adjacent windows)")
            first, last = members[0], members[-1]
            highs = [Decimal(bar["high"]) for bar in members]
            lows = [Decimal(bar["low"]) for bar in members]
            high = members[max(range(len(members)), key=lambda i: highs[i])]["high"]
            low = members[min(range(len(members)), key=lambda i: lows[i])]["low"]
            trade_count = sum(int(bar["trade_count"]) for bar in members)
            close_ns = window_open + target_interval_ns - _MS_TO_NS
            aggregated.append(_bars.build_bar({
                "source_id": context.source_id,
                "provider_id": context.provider_id,
                "venue": first["venue"],
                "instrument_id": symbol,
                "asset_class": first["asset_class"],
                "bar_type": target_type,
                "interval_ns": target_interval_ns,
                "open_time_utc_ns": first["open_time_utc_ns"],
                "close_time_utc_ns": close_ns,
                "available_time_utc_ns": close_ns,
                "open": first["open"],
                "high": high,
                "low": low,
                "close": last["close"],
                "volume": _sum_decimal(members, "volume"),
                "quote_volume": _sum_decimal(members, "quote_volume"),
                "trade_count": trade_count,
                "taker_buy_base": _sum_decimal(members, "taker_buy_base"),
                "taker_buy_quote": _sum_decimal(members, "taker_buy_quote"),
                "price_precision": first["price_precision"],
                "size_precision": first["size_precision"],
                "adjustment_mode": "RAW",
                "corporate_action_ref": None,
                "raw_sha256": hashlib.sha256(
                    _models.stream_bytes(members)).hexdigest(),
                "manifest_sha256": context.manifest_sha256,
                "normalizer_version":
                    context.normalizer_version + _DERIVED_VERSION_SUFFIX,
            }))
    return aggregated
