"""Crypto compatibility proof (V13 P0): authorized crypto datasets re-keyed as
fusion records with TRUE availability semantics.

Scope (PLAN_crypto_v13.md section 6 P0): the four AUTHORIZED crypto datasets
-- bars, funding settlements, open-interest snapshots, mark-price snapshots --
are mapped into the frozen :class:`~research.data_fusion.models.NormalizedRecord`
schema.  This module is a pure row-to-record mapping: it performs NO I/O, never
reads a real data file and never mutates a frozen loader
(``research/funding_pit.py``, ``research/funding_settlements_v10.py``,
``research/v12/data_contract.py`` stay byte-identical).

Availability semantics (binding; retrieval time NEVER substitutes):

=================  ==========================================================
dataset type       available_time_utc
=================  ==========================================================
bars               the bar close time (Nautilus ``ts_event`` close boundary;
                   a bar is completed at instant ``t`` iff ``t >= ts_event``,
                   per ``research/v12/data_contract.py``)
funding            the funding settlement stamp (``fundingTime``)
open_interest      the OI snapshot stamp (``timestamp`` / ``create_time``)
mark_price         the mark snapshot stamp (kline close time for
                   ``markPriceKlines`` rows -- a kline snapshot is only
                   complete at its close; ``timestamp`` for direct snapshots)
=================  ==========================================================

The row's ``event_time_utc`` equals its availability stamp for these native
observables and ``vintage_time_utc`` equals it too (exchange-native facts are
not retroactively revised); ``effective_time_utc`` stays ``None``.
``retrieved_time_utc`` is a REQUIRED separate input recorded as provenance only
-- it is never derived from, nor used as, availability.  Supplying a retrieval
instant earlier than the row's availability is refused fail-closed (the frozen
model itself also enforces ``available_time_utc <= retrieved_time_utc``).

Fail-closed refusals: any dataset type outside :data:`AUTHORIZED_DATASET_TYPES`
raises :class:`UnsupportedDatasetError`; malformed rows, missing stamps,
non-integral epoch values, naive/ambiguous stamp strings and lowercase symbols
all raise :class:`CryptoCompatError`.  Nothing is inferred, back-filled or
snapped here -- stamp normalization (ms jitter, slot snapping) remains the
frozen loaders' audited job.

Authority note: mapping a row proves COMPATIBILITY only.  Authorization of
these owner datasets is governed by PLAN_crypto_v13.md and the V13 run
contract; no new source is registered or authorized by this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
from typing import Any, Mapping, Sequence

from .models import NormalizedRecord

__all__ = [
    "AUTHORIZED_DATASET_TYPES",
    "AVAILABILITY_SEMANTICS",
    "CryptoCompatContext",
    "CryptoCompatError",
    "DATASET_IDS",
    "SOURCE_ID_CRYPTO",
    "UnsupportedDatasetError",
    "map_row",
    "map_rows",
]

#: The only dataset types this compatibility layer accepts.  Anything else is
#: refused fail-closed -- silence or pass-through would be an authorization
#: claim this module is not allowed to make.
AUTHORIZED_DATASET_TYPES: frozenset[str] = frozenset(
    {"bars", "funding", "open_interest", "mark_price"}
)

#: Human-auditable statement of the availability stamp class per dataset type.
AVAILABILITY_SEMANTICS: dict[str, str] = {
    "bars": "bar_close_time",
    "funding": "funding_settlement_stamp",
    "open_interest": "oi_snapshot_stamp",
    "mark_price": "mark_snapshot_stamp",
}

#: Fusion dataset_id per authorized dataset type.
DATASET_IDS: dict[str, str] = {
    "bars": "crypto_bars",
    "funding": "crypto_funding",
    "open_interest": "crypto_open_interest",
    "mark_price": "crypto_mark_price",
}

#: Fusion source_id for the authorized Binance USDT-M perpetual datasets.
SOURCE_ID_CRYPTO = "BINANCE_USDM"

#: Bar/derivative fields this layer knows how to key (fail-closed otherwise).
_BAR_FIELDS: frozenset[str] = frozenset({"open", "high", "low", "close", "volume"})

_UNIT_BY_FIELD: dict[str, str] = {
    "open": "USDT",
    "high": "USDT",
    "low": "USDT",
    "close": "USDT",
    "volume": "BASE",
    "funding_rate": "RATIO",
    "open_interest": "BASE",
    "mark_price": "USDT",
}

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_NS_PER_MS = 1_000_000


class CryptoCompatError(ValueError):
    """Fail-closed refusal: malformed row, missing stamp or bad context."""


class UnsupportedDatasetError(CryptoCompatError):
    """Fail-closed refusal: dataset type is not one of the authorized four."""


@dataclass(frozen=True, slots=True)
class CryptoCompatContext:
    """Per-bundle provenance shared by every row of one staged source file.

    ``retrieved_time_utc`` is the instant the staged bundle was actually
    loaded.  It is recorded as provenance only; availability always comes from
    the row's own dataset-native stamp.
    """

    symbol: str
    retrieved_time_utc: datetime
    raw_path: str
    raw_sha256: str
    source_id: str = SOURCE_ID_CRYPTO
    license_id: str = "owner-authorized-crypto-v13"
    entitlement_id: str = "internal_research"
    normalizer_version: str = "v13-crypto-compat-1.0.0"

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or self.symbol != self.symbol.strip():
            raise CryptoCompatError(f"symbol must be a stripped string: {self.symbol!r}")
        if not self.symbol or self.symbol != self.symbol.upper():
            raise CryptoCompatError(
                "symbol must be non-empty UPPERCASE to match the frozen staged "
                f"per-symbol keys (e.g. BTCUSDT): {self.symbol!r}"
            )


def map_rows(
    dataset_type: str,
    rows: Sequence[Any],
    context: CryptoCompatContext,
    *,
    field: str | None = None,
) -> list[NormalizedRecord]:
    """Map every row of one authorized dataset; refuse unknown types."""
    _require_authorized(dataset_type)
    return [map_row(dataset_type, row, context, field=field) for row in rows]


def map_row(
    dataset_type: str,
    row: Any,
    context: CryptoCompatContext,
    *,
    field: str | None = None,
) -> NormalizedRecord:
    """Map ONE row of an authorized crypto dataset into a fusion record."""
    _require_authorized(dataset_type)
    if dataset_type == "bars":
        return _map_bar(row, context, field)
    if dataset_type == "funding":
        return _map_funding(row, context)
    if dataset_type == "open_interest":
        return _map_open_interest(row, context)
    return _map_mark_price(row, context)


# --------------------------------------------------------------------------- #
# per-dataset row mapping
# --------------------------------------------------------------------------- #
def _map_bar(
    row: Any, context: CryptoCompatContext, field: str | None
) -> NormalizedRecord:
    """Bars: ``ts_event`` (epoch ns) IS the close boundary (v12 contract)."""
    mapping = _require_mapping(row)
    close_ns = _require_int_epoch(mapping.get("ts_event"), "ts_event")
    name = field if field is not None else "close"
    if name not in _BAR_FIELDS:
        raise CryptoCompatError(f"unsupported bar field {name!r}; authorized: {sorted(_BAR_FIELDS)}")
    if name not in mapping:
        raise CryptoCompatError(f"bar row lacks field {name!r}")
    value = _require_finite_number(mapping[name], name)
    available = _ns_to_utc(close_ns)
    return _record(
        context,
        dataset_id=DATASET_IDS["bars"],
        field=name,
        value=value,
        event_time=available,
        available_time=available,
    )


def _map_funding(row: Any, context: CryptoCompatContext) -> NormalizedRecord:
    """Funding: available at the settlement stamp (``fundingTime``, epoch ms)."""
    mapping = _require_mapping(row)
    stamp_ms = _require_int_epoch(mapping.get("fundingTime"), "fundingTime")
    value = _require_finite_number(mapping.get("fundingRate"), "fundingRate")
    available = _ms_to_utc(stamp_ms)
    return _record(
        context,
        dataset_id=DATASET_IDS["funding"],
        field="funding_rate",
        value=value,
        event_time=available,
        available_time=available,
    )


def _map_open_interest(row: Any, context: CryptoCompatContext) -> NormalizedRecord:
    """OI: available at the snapshot stamp.

    Two authorized staged shapes are accepted, each carrying its own explicit
    stamp; ambiguous or naive stamps are refused.

    * Binance open-interest history rows: ``timestamp`` (epoch ms) +
      ``sumOpenInterest`` (decimal string).
    * Consolidated parquet rows: ``create_time`` (timezone-aware ISO-8601 UTC)
      + ``sum_open_interest`` (number).
    """
    mapping = _require_mapping(row)
    if "timestamp" in mapping and "sumOpenInterest" in mapping:
        stamp = _ms_to_utc(_require_int_epoch(mapping["timestamp"], "timestamp"))
        value = _require_finite_number(mapping["sumOpenInterest"], "sumOpenInterest")
    elif "create_time" in mapping and "sum_open_interest" in mapping:
        stamp = _parse_utc_iso(mapping["create_time"], "create_time")
        value = _require_finite_number(mapping["sum_open_interest"], "sum_open_interest")
    else:
        raise CryptoCompatError(
            "open_interest row matches no authorized staged shape "
            "(expected timestamp/sumOpenInterest or create_time/sum_open_interest)"
        )
    return _record(
        context,
        dataset_id=DATASET_IDS["open_interest"],
        field="open_interest",
        value=value,
        event_time=stamp,
        available_time=stamp,
    )


def _map_mark_price(row: Any, context: CryptoCompatContext) -> NormalizedRecord:
    """Mark price: available at the mark snapshot stamp.

    Two authorized staged shapes are accepted:

    * ``markPriceKlines`` array rows (Binance kline layout, per
      ``data.derivatives.fetch_mark_price_klines``):
      ``[open_time_ms, open, high, low, close, volume, close_time_ms, ...]``.
      A kline snapshot is only COMPLETE at its close, so availability is the
      kline close time -- never the open time.
    * Direct snapshot mappings: ``timestamp`` (epoch ms) + ``markPrice``.
    """
    if isinstance(row, (list, tuple)):
        if len(row) < 7:
            raise CryptoCompatError(
                f"mark kline row needs >= 7 elements (open/close times), got {len(row)}"
            )
        close_ms = _require_int_epoch(row[6], "kline close_time")
        value = _require_finite_number(row[4], "kline close")
        available = _ms_to_utc(close_ms)
    else:
        mapping = _require_mapping(row)
        if "timestamp" not in mapping or "markPrice" not in mapping:
            raise CryptoCompatError(
                "mark_price row matches no authorized staged shape "
                "(expected kline array or timestamp/markPrice mapping)"
            )
        available = _ms_to_utc(_require_int_epoch(mapping["timestamp"], "timestamp"))
        value = _require_finite_number(mapping["markPrice"], "markPrice")
    return _record(
        context,
        dataset_id=DATASET_IDS["mark_price"],
        field="mark_price",
        value=value,
        event_time=available,
        available_time=available,
    )


# --------------------------------------------------------------------------- #
# record assembly
# --------------------------------------------------------------------------- #
def _record(
    context: CryptoCompatContext,
    *,
    dataset_id: str,
    field: str,
    value: float,
    event_time: datetime,
    available_time: datetime,
) -> NormalizedRecord:
    if available_time > context.retrieved_time_utc:
        raise CryptoCompatError(
            "retrieval_time_utc precedes the row's availability; retrieval time "
            "must never substitute for availability -- supply the true retrieval "
            f"instant (availability={available_time.isoformat()}, "
            f"retrieval={context.retrieved_time_utc.isoformat()})"
        )
    return NormalizedRecord(
        source_id=context.source_id,
        dataset_id=dataset_id,
        entity_id=context.symbol,
        field=field,
        value=value,
        unit=_UNIT_BY_FIELD[field],
        event_time_utc=event_time,
        available_time_utc=available_time,
        effective_time_utc=None,
        vintage_time_utc=available_time,
        retrieved_time_utc=context.retrieved_time_utc,
        raw_path=context.raw_path,
        raw_sha256=context.raw_sha256,
        license_id=context.license_id,
        entitlement_id=context.entitlement_id,
        normalizer_version=context.normalizer_version,
    )


# --------------------------------------------------------------------------- #
# strict scalar/time coercion (stdlib only; every failure is loud)
# --------------------------------------------------------------------------- #
def _require_authorized(dataset_type: Any) -> None:
    if dataset_type not in AUTHORIZED_DATASET_TYPES:
        raise UnsupportedDatasetError(
            f"unsupported dataset type {dataset_type!r}; authorized types only: "
            f"{sorted(AUTHORIZED_DATASET_TYPES)}"
        )


def _require_mapping(row: Any) -> Mapping[str, Any]:
    if not isinstance(row, Mapping):
        raise CryptoCompatError(f"row must be a mapping, got {type(row).__name__}")
    return row


def _require_int_epoch(raw: Any, field_name: str) -> int:
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise CryptoCompatError(f"{field_name} must be integer epoch, got {raw!r}")
    as_float = float(raw)
    if not math.isfinite(as_float) or as_float != int(as_float):
        raise CryptoCompatError(f"{field_name} must be integral, got {raw!r}")
    return int(as_float)


def _require_finite_number(raw: Any, field_name: str) -> float:
    try:
        value = float(str(raw))
    except (TypeError, ValueError) as exc:
        raise CryptoCompatError(f"{field_name} not parseable as a number: {raw!r}") from exc
    if not math.isfinite(value):
        raise CryptoCompatError(f"{field_name} must be finite, got {raw!r}")
    return value


def _ms_to_utc(ms: int) -> datetime:
    return _EPOCH + timedelta(milliseconds=ms)


def _ns_to_utc(ns: int) -> datetime:
    # datetime resolution is microseconds; sub-microsecond remainder is
    # truncated (15m bar close boundaries are exact on this grid).
    return _EPOCH + timedelta(microseconds=ns // 1_000)


def _parse_utc_iso(raw: Any, field_name: str) -> datetime:
    if not isinstance(raw, str) or not raw.strip():
        raise CryptoCompatError(f"{field_name} must be a non-empty ISO-8601 string")
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise CryptoCompatError(f"{field_name} not ISO-8601: {raw!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CryptoCompatError(
            f"{field_name} is a naive stamp ({raw!r}); timezone-aware UTC stamps "
            "are required -- ambiguous stamps are refused fail-closed"
        )
    return parsed.astimezone(timezone.utc)
