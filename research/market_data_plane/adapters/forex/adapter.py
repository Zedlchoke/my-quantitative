"""Forex OHLCV -> mdp.market_bar@2 adapter — normalize_bar/normalize_stream (A6).

Freeze authority: research/control/market_data_plane_v2_run/architecture_freeze_v2.json
(p3_wave_sha 09a223f6ce166e219beb67b25b8151361979ca21), section
``"adapters" -> "forex"`` and ``"bar_contract"``.

Per-record pipeline (:func:`normalize_bar`, fail closed):

* plane boundary FIRST: any record key containing bid/ask/spread/swap/
  rollover (case-insensitive) is rejected — OHLCV NEVER creates bid/ask,
  spread, swap or rollover evidence (frozen microstructure_rule);
* macro boundary: a date-only macro observation (e.g.
  ``{"date": "2026-03-04", "rate": "4.25"}``) is NOT a bar — it is rejected
  with ``FOREX_MACRO_DATE_ONLY_ROW``; macro rows stay Data Fusion
  observables with next-day-exclusive availability bounds, never fabricated
  as market events;
* provider clock: ``ts`` is a local wall time (no offset) and ``tz`` the
  IANA zone name; the record ``tz`` must equal the context
  ``provider_timezone``; conversion via :mod:`zoneinfo` is fold-aware and
  rejects ambiguous/imaginary local times instead of guessing;
* pair identity: provider symbol -> declared :class:`PairIdentity`
  (``"EUR_USD"`` and ``"EURUSD"`` both carry instrument_id ``"EUR/USD"``);
  unknown symbols raise ``UNKNOWN_INSTRUMENT`` — never string surgery;
* bar times: ``close_time = open_time + interval_ns - 1`` (inclusive last
  nanosecond of the half-open ``[open, open + interval)`` slot);
  ``available_time = close_time + context.publication_lag_ns`` (frozen
  publication-lag constant; default 0 == close_time);
* a bar whose slot opens inside the frozen weekly closure is flagged
  ``BAR_OUTSIDE_CALENDAR`` (SUSPECT evidence, never deleted);
* the bar itself is built and validated by the frozen
  :func:`market_data_plane.bars.build_bar`; missing volume persists as
  ``null`` + ``BAR_VOLUME_NOT_EVALUABLE`` (NOT_EVALUABLE), never zero.

Stream pipeline (:func:`normalize_stream`): per-record failures are
QUARANTINED with reason codes (never silently dropped); the accepted bars go
through the frozen :func:`market_data_plane.bar_stream.normalize_bar_stream`
so interval duplicate/overlap FAILS CLOSED (``BarIntervalError``) exactly as
the bar contract requires — that family is never quarantined.

``raw_sha256`` is taken from the record when present (validated 64-hex) and
otherwise computed over the exact canonical serialization of the verbatim
record (``models.canonical_json``); ``manifest_sha256`` comes from the
record or the context (upstream retrieval manifest id, required).

stdlib + sibling market_data_plane modules only; never mutates inputs.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Optional

from market_data_plane import bar_stream as _bar_stream
from market_data_plane import bars as _bars
from market_data_plane import models as _models

from .context import (AdapterContext, ForexAdapterError, load_provider_timezone,
                      local_wall_to_utc_ns)

__all__ = [
    "FOREX_ASSET_CLASS",
    "REQUIRED_RECORD_FIELDS",
    "AdapterResult",
    "normalize_bar",
    "normalize_stream",
]

#: Frozen asset class for the forex OHLCV path (adapters.forex identity).
FOREX_ASSET_CLASS = "forex_spot"

#: Required raw provider record fields (provider-local OHLCV row shape).
REQUIRED_RECORD_FIELDS: tuple[str, ...] = (
    "ts", "tz", "symbol", "open", "high", "low", "close",
)

#: Date-only macro observation signature keys (Data Fusion observables).
_MACRO_DATE_KEYS = frozenset({"date", "observation_date", "rate_date"})

#: Microstructure evidence substrings barred from the OHLCV record plane
#: (frozen microstructure_rule: OHLCV never creates bid/ask/spread/swap/
#: rollover evidence).  Case-insensitive substring match on record keys.
_FORBIDDEN_KEY_SUBSTRINGS: tuple[str, ...] = ("bid", "ask", "spread", "swap", "rollover")

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

_BAR_ERROR_PREFIX = re.compile(r"^\[[A-Z0-9_]+\] ")


def _strip_code_prefix(text: str) -> str:
    return _BAR_ERROR_PREFIX.sub("", text, count=1)


def _require_mapping(raw_record) -> None:
    if not isinstance(raw_record, Mapping):
        raise _bars.BarError(
            "MALFORMED_SHAPE",
            f"raw provider record must be a mapping, got {type(raw_record).__name__}")


def _reject_microstructure_keys(raw_record: Mapping) -> None:
    for key in raw_record:
        lowered = str(key).lower()
        for substring in _FORBIDDEN_KEY_SUBSTRINGS:
            if substring in lowered:
                raise ForexAdapterError(
                    "FOREX_FORBIDDEN_MICROSTRUCTURE_FIELD",
                    f"record key {key!r} carries bid/ask/spread/swap/rollover "
                    f"evidence; OHLCV never creates microstructure evidence "
                    f"(frozen adapters.forex.microstructure_rule)")


def _reject_macro_row(raw_record: Mapping) -> None:
    if "ts" in raw_record:
        return
    macro_keys = sorted(set(str(k) for k in raw_record) & _MACRO_DATE_KEYS)
    if macro_keys:
        raise ForexAdapterError(
            "FOREX_MACRO_DATE_ONLY_ROW",
            f"date-only macro observation (keys {macro_keys}) is NOT a bar; "
            f"macro rows stay Data Fusion observables (next-day-exclusive "
            f"availability bounds) and are never fabricated as market events")


def _require_fields(raw_record: Mapping) -> None:
    missing = [name for name in REQUIRED_RECORD_FIELDS if name not in raw_record]
    if missing:
        raise _bars.BarError(
            "MISSING_REQUIRED_FIELD", f"missing required record field(s): {missing}")


def _resolve_raw_sha256(raw_record: Mapping) -> str:
    supplied = raw_record.get("raw_sha256")
    if supplied is not None:
        if not isinstance(supplied, str) or not _HEX64_RE.match(supplied):
            raise _bars.BarError(
                "MALFORMED_SHAPE",
                "record raw_sha256 must be lowercase hex sha256 (64 chars)")
        return supplied
    try:
        digest_input = _models.canonical_json(dict(raw_record)).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise _bars.BarError(
            "MALFORMED_SHAPE",
            f"raw record is not canonically serializable for raw_sha256: {exc}") \
            from exc
    return hashlib.sha256(digest_input).hexdigest()


def _resolve_manifest_sha256(raw_record: Mapping, context: AdapterContext) -> str:
    supplied = raw_record.get("manifest_sha256") or context.manifest_sha256
    if supplied is None:
        raise _bars.BarError(
            "MISSING_REQUIRED_FIELD",
            "manifest_sha256 required (record field or context.manifest_sha256); "
            "the upstream retrieval manifest id is never assumed")
    if not isinstance(supplied, str) or not _HEX64_RE.match(supplied):
        raise _bars.BarError(
            "MALFORMED_SHAPE",
            "manifest_sha256 must be lowercase hex sha256 (64 chars)")
    return supplied


def _resolve_provider_timezone(raw_record: Mapping, context: AdapterContext):
    record_tz = raw_record.get("tz")
    if not isinstance(record_tz, str) or not record_tz:
        raise _bars.BarError("MALFORMED_SHAPE", "record tz must be a non-empty IANA name")
    if record_tz != context.provider_timezone:
        raise ForexAdapterError(
            "FOREX_PROVIDER_TZ_MISMATCH",
            f"record tz {record_tz!r} != context provider_timezone "
            f"{context.provider_timezone!r}; refusing to mix clocks")
    return load_provider_timezone(record_tz)


# --- normalize_bar ------------------------------------------------------------

def normalize_bar(raw_record: Mapping, context: AdapterContext) -> dict:
    """One provider OHLCV record -> one canonical mdp.market_bar@2 dict.

    Fail closed on every contract violation (raises; see module docstring
    for the rejection order).  Never mutates the input record.
    """
    _require_mapping(raw_record)
    _reject_microstructure_keys(raw_record)
    _reject_macro_row(raw_record)
    _require_fields(raw_record)

    tz = _resolve_provider_timezone(raw_record, context)
    identity = context.pair_identity(raw_record.get("symbol"))
    open_ns = local_wall_to_utc_ns(raw_record.get("ts"), tz)
    close_ns = open_ns + context.interval_ns - 1
    available_ns = close_ns + context.publication_lag_ns

    volume = raw_record.get("volume")
    reason_codes: list[str] = []
    if context.is_session_closed(open_ns):
        # Suspect evidence, never deleted: the slot opens inside the frozen
        # weekly closure (BAR_OUTSIDE_CALENDAR, the bar SUSPECT class).
        reason_codes.append("BAR_OUTSIDE_CALENDAR")

    bar = _bars.build_bar({
        "schema_version": _bars.SCHEMA_VERSION,
        "source_id": context.source_id,
        "provider_id": context.provider_id,
        "venue": context.venue,
        "instrument_id": identity.instrument_id,
        "asset_class": FOREX_ASSET_CLASS,
        "bar_type": context.resolved_bar_type,
        "interval_ns": context.interval_ns,
        "open_time_utc_ns": open_ns,
        "close_time_utc_ns": close_ns,
        "available_time_utc_ns": available_ns,
        "open": raw_record.get("open"),
        "high": raw_record.get("high"),
        "low": raw_record.get("low"),
        "close": raw_record.get("close"),
        "volume": volume,
        "quote_volume": None,
        "trade_count": None,
        "taker_buy_base": None,
        "taker_buy_quote": None,
        "price_precision": context.price_precision,
        "size_precision": context.size_precision,
        "adjustment_mode": "RAW",
        "corporate_action_ref": None,
        "quality_status": None,  # classified below from the final code set
        "reason_codes": reason_codes,
        "raw_sha256": _resolve_raw_sha256(raw_record),
        "manifest_sha256": _resolve_manifest_sha256(raw_record, context),
        "normalizer_version": context.normalizer_version,
    })
    # Adapter quality classification: exactly the frozen final-status rule
    # over the bar's own codes (VALID only when no code says otherwise —
    # parsing success alone never upgrades a bar).
    return _bars.set_quality(
        bar, _bars.bar_status_from_codes(bar["reason_codes"]), bar["reason_codes"])


# --- normalize_stream -----------------------------------------------------------

@dataclass(frozen=True)
class AdapterResult:
    """Ordered forex normalization result (A6 half of the frozen interface).

    ``bars`` are canonical mdp.market_bar@2 dicts in input order (the stream
    normalizer never reorders) after the frozen
    :func:`bar_stream.normalize_bar_stream` semantics; ``quarantined`` holds
    one entry per rejected record with an adapter/local or frozen reason
    code — never silently dropped.  Interval duplicate/overlap between
    accepted bars is NOT quarantined: it raises :class:`BarIntervalError`.
    """

    bars: tuple[dict, ...]
    quarantined: tuple[dict, ...]
    accepted_count: int
    quarantined_count: int
    completeness_status: Optional[str]
    gap_reasons: tuple[str, ...]
    stream_gaps: tuple[dict, ...]
    stream_digest: str
    stream_byte_length: int
    normalizer_version: str
    quarantine_reason_codes: tuple[str, ...] = field(default=())

    def as_dict(self) -> dict:
        return {
            "bars": [dict(bar) for bar in self.bars],
            "quarantined": [dict(entry) for entry in self.quarantined],
            "accepted_count": self.accepted_count,
            "quarantined_count": self.quarantined_count,
            "completeness_status": self.completeness_status,
            "gap_reasons": list(self.gap_reasons),
            "stream_gaps": [dict(gap) for gap in self.stream_gaps],
            "stream_digest": self.stream_digest,
            "stream_byte_length": self.stream_byte_length,
            "normalizer_version": self.normalizer_version,
            "quarantine_reason_codes": list(self.quarantine_reason_codes),
        }


def normalize_stream(raw_records: Iterable[Mapping], context: AdapterContext) -> AdapterResult:
    """Ordered normalization with per-record quarantine; disjointness fail-closed.

    Ordered via bar_stream semantics: accepted bars preserve input order and
    must be strictly increasing and non-disjoint per identity
    ``(instrument_id, bar_type, interval_ns, adjustment_mode)`` — duplicate
    or overlapping intervals raise :class:`BarIntervalError` (fail closed,
    never quarantine).  Per-record contract failures are quarantined with
    reason codes and recorded verbatim (nothing discovered, nothing deleted).
    """
    if raw_records is None:
        raise _bars.BarError("MALFORMED_SHAPE", "raw_records must be an iterable of mappings")
    accepted: list[dict] = []
    quarantined: list[dict] = []
    for index, record in enumerate(raw_records):
        try:
            accepted.append(normalize_bar(record, context))
        except _bars.BarError as exc:
            entry = {
                "stream_index": index,
                "reason_code": exc.reason_code,
                "detail": _strip_code_prefix(str(exc)),
                "raw_record": deepcopy(dict(record)) if isinstance(record, Mapping)
                else record,
            }
            if isinstance(record, Mapping) and isinstance(record.get("symbol"), str):
                entry["provider_symbol"] = record["symbol"]
            quarantined.append(entry)
    stream = _bar_stream.normalize_bar_stream(accepted)
    return AdapterResult(
        bars=tuple(stream["bars"]),
        quarantined=tuple(quarantined),
        accepted_count=len(accepted),
        quarantined_count=len(quarantined),
        completeness_status=stream["completeness_status"],
        gap_reasons=tuple(stream["gap_reasons"]),
        stream_gaps=tuple(stream["gaps"]) if stream["gaps"] else (),
        stream_digest=stream["stream_digest"],
        stream_byte_length=stream["stream_byte_length"],
        normalizer_version=context.normalizer_version,
        quarantine_reason_codes=tuple(sorted({e["reason_code"] for e in quarantined})),
    )
