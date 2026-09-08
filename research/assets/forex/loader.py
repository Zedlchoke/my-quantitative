"""Normalized bid/ask quote loader (owner: A3, PLAN_forex.md 7-A3).

Loads quote/bar records from in-memory mappings supplied by the caller
(tests/synthetic feeds).  Fail-closed rules, each with a stable reason code:

* missing either quote side → ``MISSING_BID`` / ``MISSING_ASK``;
* crossed or negative spread → ``CROSSED_SPREAD`` (``ask < bid`` for price
  records; for OHLC bars, any ask price below any bid price);
* stale quotes: ``event_ts_utc`` older than ``as_of_utc - max_age`` →
  ``STALE_QUOTE`` (``max_age`` is a required, caller-configured bound);
* naive timestamps → ``NAIVE_TIMESTAMP``; aware-but-non-UTC →
  ``NON_UTC_TIMESTAMP``; unparseable/missing → ``MALFORMED_TIMESTAMP``;
* unsorted or duplicate events → ``UNSORTED_EVENTS`` / ``DUPLICATE_EVENT``
  (input order is never silently corrected);
* unknown symbols → ``UNKNOWN_SYMBOL`` (resolved through the frozen
  instrument registry);
* structurally invalid rows → ``MALFORMED_RECORD`` / ``NON_FINITE_PRICE`` /
  ``OHLC_INVALID``; ingest preceding event → ``INGEST_BEFORE_EVENT``.

The midpoint is derived ONLY by the named function :func:`midpoint` — no
code path substitutes mid for a side.  There is deliberately no gap-filling
API at all: weekend/session gaps pass through unfilled for calendar-based
classification (see data_audit.py, which takes a session calendar by
dependency injection).
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from research.assets.common.contracts import require_token
from research.assets.forex.instruments import lookup_symbol

# --- reason codes ------------------------------------------------------------ #
MISSING_BID = "MISSING_BID"
MISSING_ASK = "MISSING_ASK"
CROSSED_SPREAD = "CROSSED_SPREAD"
STALE_QUOTE = "STALE_QUOTE"
NAIVE_TIMESTAMP = "NAIVE_TIMESTAMP"
NON_UTC_TIMESTAMP = "NON_UTC_TIMESTAMP"
MALFORMED_TIMESTAMP = "MALFORMED_TIMESTAMP"
UNSORTED_EVENTS = "UNSORTED_EVENTS"
DUPLICATE_EVENT = "DUPLICATE_EVENT"
UNKNOWN_SYMBOL = "UNKNOWN_SYMBOL"
MALFORMED_RECORD = "MALFORMED_RECORD"
NON_FINITE_PRICE = "NON_FINITE_PRICE"
OHLC_INVALID = "OHLC_INVALID"
INGEST_BEFORE_EVENT = "INGEST_BEFORE_EVENT"

#: Every rejection reason this loader can emit (used by tests and audits).
REASON_CODES = frozenset(
    {
        MISSING_BID,
        MISSING_ASK,
        CROSSED_SPREAD,
        STALE_QUOTE,
        NAIVE_TIMESTAMP,
        NON_UTC_TIMESTAMP,
        MALFORMED_TIMESTAMP,
        UNSORTED_EVENTS,
        DUPLICATE_EVENT,
        UNKNOWN_SYMBOL,
        MALFORMED_RECORD,
        NON_FINITE_PRICE,
        OHLC_INVALID,
        INGEST_BEFORE_EVENT,
    }
)

_OHLC_KEYS = ("o", "h", "l", "c")
_UTC = timezone.utc


def midpoint(bid: float, ask: float) -> float:
    """The ONLY midpoint derivation in the forex lane: ``(bid + ask) / 2``.

    Never use a midpoint where an executable side is required; this function
    exists so the derivation is explicit, named and auditable.
    """
    return (bid + ask) / 2


# --- normalized record types ------------------------------------------------- #
@dataclass(frozen=True)
class Ohlc:
    """One bid or ask OHLC bar (all fields finite floats)."""

    o: float
    h: float
    l: float
    c: float

    def __post_init__(self) -> None:
        for name in _OHLC_KEYS:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"Ohlc.{name} must be a real number, got {value!r}")
            if not math.isfinite(float(value)):
                raise ValueError(f"Ohlc.{name} must be finite, got {value!r}")
        if self.l > self.h:
            raise ValueError(f"Ohlc low {self.l!r} exceeds high {self.h!r}")

    def span(self) -> tuple[float, float]:
        """``(min, max)`` across o/h/l/c."""
        values = (self.o, self.h, self.l, self.c)
        return min(values), max(values)


@dataclass(frozen=True)
class QuoteRow:
    """One accepted, normalized bid/ask record.

    Exactly one form is present: scalar prices (``bid``/``ask``) or OHLC
    bars (``bid_ohlc``/``ask_ohlc``).  ``midpoint`` is defined only for the
    scalar form (bar rows expose :meth:`bar_midpoints`); it is always
    derived via :func:`midpoint`.
    """

    symbol: str
    event_ts_utc: datetime
    ingest_ts_utc: datetime
    bid: float | None = None
    ask: float | None = None
    bid_ohlc: Ohlc | None = None
    ask_ohlc: Ohlc | None = None

    def __post_init__(self) -> None:
        require_token(self.symbol, "symbol")
        for name in ("event_ts_utc", "ingest_ts_utc"):
            ts = getattr(self, name)
            if not isinstance(ts, datetime) or ts.tzinfo is None:
                raise ValueError(f"{name} must be a tz-aware datetime")
            if ts.utcoffset() != timedelta(0):
                raise ValueError(f"{name} must be UTC")
        if self.ingest_ts_utc < self.event_ts_utc:
            raise ValueError("ingest_ts_utc must not precede event_ts_utc")
        scalar_form = self.bid is not None or self.ask is not None
        ohlc_form = self.bid_ohlc is not None or self.ask_ohlc is not None
        if scalar_form and ohlc_form:
            raise ValueError("quote row must be scalar (bid/ask) OR bar (ohlc), not both")
        if scalar_form:
            if self.bid is None or self.ask is None:
                raise ValueError("scalar form requires both bid and ask")
            if self.ask < self.bid:
                raise ValueError(f"crossed spread: ask {self.ask!r} < bid {self.bid!r}")
        if ohlc_form:
            if self.bid_ohlc is None or self.ask_ohlc is None:
                raise ValueError("bar form requires both bid_ohlc and ask_ohlc")
            bid_max = self.bid_ohlc.span()[1]
            ask_min = self.ask_ohlc.span()[0]
            if ask_min < bid_max:
                raise ValueError(
                    f"crossed spread: min ask {ask_min!r} < max bid {bid_max!r}"
                )

    @property
    def is_bar(self) -> bool:
        return self.bid_ohlc is not None

    @property
    def midpoint(self) -> float:
        """Explicit midpoint (scalar form only; derived via ``midpoint()``)."""
        if self.bid is None or self.ask is None:
            raise ValueError(
                "midpoint is undefined for an OHLC-form row; derive per-field "
                "via bar_midpoints()"
            )
        return midpoint(self.bid, self.ask)

    def bar_midpoints(self) -> Ohlc:
        """Per-field OHLC midpoints (bar form only; via ``midpoint()``)."""
        if self.bid_ohlc is None or self.ask_ohlc is None:
            raise ValueError("bar_midpoints() is defined only for OHLC-form rows")
        return Ohlc(
            o=midpoint(self.bid_ohlc.o, self.ask_ohlc.o),
            h=midpoint(self.bid_ohlc.h, self.ask_ohlc.h),
            l=midpoint(self.bid_ohlc.l, self.ask_ohlc.l),
            c=midpoint(self.bid_ohlc.c, self.ask_ohlc.c),
        )


@dataclass(frozen=True)
class RejectedQuote:
    """One rejected input row with its fail-closed reason code."""

    index: int
    reason_code: str
    detail: str
    symbol: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.index, int) or isinstance(self.index, bool):
            raise ValueError(f"index must be an int, got {self.index!r}")
        if self.reason_code not in REASON_CODES:
            raise ValueError(
                f"reason_code must be one of {sorted(REASON_CODES)}, "
                f"got {self.reason_code!r}"
            )
        if not isinstance(self.detail, str) or not self.detail.strip():
            raise ValueError("detail must be a non-empty string")


@dataclass(frozen=True)
class QuoteBatch:
    """Accepted rows plus per-row rejections; ``accepted + rejected == input``."""

    rows: tuple[QuoteRow, ...]
    rejected: tuple[RejectedQuote, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple) or not all(
            isinstance(r, QuoteRow) for r in self.rows
        ):
            raise ValueError("rows must be a tuple of QuoteRow")
        if not isinstance(self.rejected, tuple) or not all(
            isinstance(r, RejectedQuote) for r in self.rejected
        ):
            raise ValueError("rejected must be a tuple of RejectedQuote")

    @property
    def accepted_count(self) -> int:
        return len(self.rows)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected)

    def rejected_by_reason(self) -> Mapping[str, int]:
        """Sorted ``{reason_code: count}`` over the rejections."""
        counts: dict[str, int] = {}
        for rejection in self.rejected:
            counts[rejection.reason_code] = counts.get(rejection.reason_code, 0) + 1
        return dict(sorted(counts.items()))


# --- parsing helpers --------------------------------------------------------- #
def _parse_utc_timestamp(value: Any, field: str) -> tuple[datetime | None, str | None]:
    """Parse a tz-aware UTC timestamp; returns ``(dt, failure_reason)``."""
    if value is None:
        return None, MALFORMED_TIMESTAMP
    dt: datetime | None = None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return None, MALFORMED_TIMESTAMP
    else:
        return None, MALFORMED_TIMESTAMP
    if dt.tzinfo is None:
        return None, NAIVE_TIMESTAMP
    if dt.utcoffset() != timedelta(0):
        return None, NON_UTC_TIMESTAMP
    return dt, None


def _parse_scalar_price(value: Any) -> tuple[float | None, str | None]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, MALFORMED_RECORD
    price = float(value)
    if not math.isfinite(price):
        return None, NON_FINITE_PRICE
    return price, None


def _parse_ohlc(value: Any) -> tuple[Ohlc | None, str | None]:
    if not isinstance(value, Mapping):
        return None, MALFORMED_RECORD
    for key in _OHLC_KEYS:
        if key not in value:
            return None, OHLC_INVALID
    parsed: dict[str, float] = {}
    for key in _OHLC_KEYS:
        price, failure = _parse_scalar_price(value[key])
        if failure is not None:
            return None, NON_FINITE_PRICE if failure == NON_FINITE_PRICE else failure
        parsed[key] = float(price)  # type: ignore[arg-type]
    try:
        return Ohlc(o=parsed["o"], h=parsed["h"], l=parsed["l"], c=parsed["c"]), None
    except ValueError as exc:
        return None, OHLC_INVALID if "low" in str(exc) else MALFORMED_RECORD


# --- the loader --------------------------------------------------------------- #
def load_quotes(
    records: Sequence[Any],
    *,
    max_age: timedelta,
    as_of_utc: datetime,
    symbol: str | None = None,
) -> QuoteBatch:
    """Load in-memory bid/ask records into a validated :class:`QuoteBatch`.

    ``max_age`` (positive) and ``as_of_utc`` (tz-aware UTC) are required so
    staleness is explicit and deterministic — wall-clock time is never read.
    ``symbol`` optionally pins the expected instrument; rows claiming any
    other symbol fail closed as ``UNKNOWN_SYMBOL`` rather than being
    silently filtered.

    Rows are never reordered, deduplicated silently or gap-filled: input
    order is preserved, duplicates and regressions are rejected per row
    (against the last *accepted* event timestamp for that symbol), and any
    weekend/session gap simply stays absent from the output rows.
    """
    if not isinstance(max_age, timedelta) or max_age <= timedelta(0):
        raise ValueError(f"max_age must be a positive timedelta, got {max_age!r}")
    as_of, failure = _parse_utc_timestamp(as_of_utc, "as_of_utc")
    if failure is not None or as_of is None:
        raise ValueError(f"as_of_utc must be a tz-aware UTC timestamp, got {as_of_utc!r}")
    if symbol is not None:
        require_token(symbol, "symbol")
        lookup_symbol(symbol)

    rows: list[QuoteRow] = []
    rejected: list[RejectedQuote] = []
    last_accepted_ts: dict[str, datetime] = {}

    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            rejected.append(
                RejectedQuote(
                    index=index,
                    reason_code=MALFORMED_RECORD,
                    detail=f"record {index} is not a mapping: {type(record).__name__}",
                )
            )
            continue

        # symbol / instrument identity
        row_symbol = record.get("symbol")
        if symbol is not None and row_symbol != symbol:
            rejected.append(
                RejectedQuote(
                    index=index,
                    reason_code=UNKNOWN_SYMBOL,
                    detail=f"record symbol {row_symbol!r} != expected {symbol!r}",
                    symbol=str(row_symbol) if isinstance(row_symbol, str) else None,
                )
            )
            continue
        try:
            pair = lookup_symbol(row_symbol)  # type: ignore[arg-type]
        except ValueError:
            rejected.append(
                RejectedQuote(
                    index=index,
                    reason_code=UNKNOWN_SYMBOL,
                    detail=f"symbol {row_symbol!r} is not in the frozen registry",
                    symbol=str(row_symbol) if isinstance(row_symbol, str) else None,
                )
            )
            continue
        assert pair is not None  # for type checkers; lookup_symbol raised otherwise

        # timestamps
        event_ts, event_failure = _parse_utc_timestamp(
            record.get("event_ts_utc"), "event_ts_utc"
        )
        if event_failure is not None or event_ts is None:
            rejected.append(
                RejectedQuote(
                    index=index,
                    reason_code=event_failure or MALFORMED_TIMESTAMP,
                    detail=f"invalid event_ts_utc: {record.get('event_ts_utc')!r}",
                    symbol=pair.symbol,
                )
            )
            continue
        ingest_ts, ingest_failure = _parse_utc_timestamp(
            record.get("ingest_ts_utc"), "ingest_ts_utc"
        )
        if ingest_failure is not None or ingest_ts is None:
            rejected.append(
                RejectedQuote(
                    index=index,
                    reason_code=ingest_failure or MALFORMED_TIMESTAMP,
                    detail=f"invalid ingest_ts_utc: {record.get('ingest_ts_utc')!r}",
                    symbol=pair.symbol,
                )
            )
            continue
        if ingest_ts < event_ts:
            rejected.append(
                RejectedQuote(
                    index=index,
                    reason_code=INGEST_BEFORE_EVENT,
                    detail=f"ingest {ingest_ts.isoformat()} < event {event_ts.isoformat()}",
                    symbol=pair.symbol,
                )
            )
            continue

        # quote sides: scalar (bid/ask) or bar (bid_ohlc/ask_ohlc), one form only
        bid_raw, ask_raw = record.get("bid"), record.get("ask")
        bid_ohlc_raw, ask_ohlc_raw = record.get("bid_ohlc"), record.get("ask_ohlc")
        scalar_present = bid_raw is not None or ask_raw is not None
        ohlc_present = bid_ohlc_raw is not None or ask_ohlc_raw is not None
        if scalar_present and ohlc_present:
            rejected.append(
                RejectedQuote(
                    index=index,
                    reason_code=MALFORMED_RECORD,
                    detail="record mixes scalar (bid/ask) and bar (ohlc) forms",
                    symbol=pair.symbol,
                )
            )
            continue

        if scalar_present:
            if bid_raw is None or ask_raw is None:
                side_missing = MISSING_BID if bid_raw is None else MISSING_ASK
                rejected.append(
                    RejectedQuote(
                        index=index,
                        reason_code=side_missing,
                        detail=f"{side_missing.lower()} side absent: bid={bid_raw!r} ask={ask_raw!r}",
                        symbol=pair.symbol,
                    )
                )
                continue
            bid, bid_failure = _parse_scalar_price(bid_raw)
            ask, ask_failure = _parse_scalar_price(ask_raw)
            if bid_failure == MALFORMED_RECORD or ask_failure == MALFORMED_RECORD:
                rejected.append(
                    RejectedQuote(
                        index=index,
                        reason_code=MALFORMED_RECORD,
                        detail=f"non-numeric price: bid={bid_raw!r} ask={ask_raw!r}",
                        symbol=pair.symbol,
                    )
                )
                continue
            if bid_failure == NON_FINITE_PRICE or ask_failure == NON_FINITE_PRICE:
                rejected.append(
                    RejectedQuote(
                        index=index,
                        reason_code=NON_FINITE_PRICE,
                        detail=f"non-finite price: bid={bid_raw!r} ask={ask_raw!r}",
                        symbol=pair.symbol,
                    )
                )
                continue
            bid_f, ask_f = bid, ask
            bid_ohlc = ask_ohlc = None
        else:
            if bid_ohlc_raw is None or ask_ohlc_raw is None:
                side_missing = MISSING_BID if bid_ohlc_raw is None else MISSING_ASK
                rejected.append(
                    RejectedQuote(
                        index=index,
                        reason_code=side_missing,
                        detail=f"{side_missing.lower()} side absent: missing {side_missing.lower()}_ohlc",
                        symbol=pair.symbol,
                    )
                )
                continue
            bid_ohlc, bid_failure = _parse_ohlc(bid_ohlc_raw)
            ask_ohlc, ask_failure = _parse_ohlc(ask_ohlc_raw)
            if (
                bid_failure in (MALFORMED_RECORD, NON_FINITE_PRICE, OHLC_INVALID)
                or ask_failure in (MALFORMED_RECORD, NON_FINITE_PRICE, OHLC_INVALID)
            ):
                rejected.append(
                    RejectedQuote(
                        index=index,
                        reason_code=(
                            bid_failure
                            if bid_failure is not None
                            else ask_failure
                        )
                        or MALFORMED_RECORD,
                        detail=(
                            f"invalid ohlc: bid_ohlc={bid_ohlc_raw!r} "
                            f"ask_ohlc={ask_ohlc_raw!r}"
                        ),
                        symbol=pair.symbol,
                    )
                )
                continue
            bid_f = ask_f = None

        # crossed / negative spread
        if bid_f is not None and ask_f is not None:
            if ask_f < bid_f:
                rejected.append(
                    RejectedQuote(
                        index=index,
                        reason_code=CROSSED_SPREAD,
                        detail=f"ask {ask_f!r} < bid {bid_f!r}",
                        symbol=pair.symbol,
                    )
                )
                continue
        else:
            assert bid_ohlc is not None and ask_ohlc is not None
            bid_max = bid_ohlc.span()[1]
            ask_min = ask_ohlc.span()[0]
            if ask_min < bid_max:
                rejected.append(
                    RejectedQuote(
                        index=index,
                        reason_code=CROSSED_SPREAD,
                        detail=f"min ask {ask_min!r} < max bid {bid_max!r} (ohlc form)",
                        symbol=pair.symbol,
                    )
                )
                continue

        # staleness against the caller-supplied as-of instant
        if as_of - event_ts > max_age:
            rejected.append(
                RejectedQuote(
                    index=index,
                    reason_code=STALE_QUOTE,
                    detail=(
                        f"event {event_ts.isoformat()} older than "
                        f"as_of {as_of.isoformat()} minus max_age {max_age}"
                    ),
                    symbol=pair.symbol,
                )
            )
            continue

        # sequence integrity: strictly increasing per symbol, no silent fixes
        previous = last_accepted_ts.get(pair.symbol)
        if previous is not None:
            if event_ts == previous:
                rejected.append(
                    RejectedQuote(
                        index=index,
                        reason_code=DUPLICATE_EVENT,
                        detail=f"duplicate event_ts_utc {event_ts.isoformat()}",
                        symbol=pair.symbol,
                    )
                )
                continue
            if event_ts < previous:
                rejected.append(
                    RejectedQuote(
                        index=index,
                        reason_code=UNSORTED_EVENTS,
                        detail=(
                            f"event {event_ts.isoformat()} precedes previously "
                            f"accepted {previous.isoformat()}"
                        ),
                        symbol=pair.symbol,
                    )
                )
                continue
        last_accepted_ts[pair.symbol] = event_ts

        rows.append(
            QuoteRow(
                symbol=pair.symbol,
                event_ts_utc=event_ts,
                ingest_ts_utc=ingest_ts,
                bid=bid_f,
                ask=ask_f,
                bid_ohlc=bid_ohlc,
                ask_ohlc=ask_ohlc,
            )
        )

    return QuoteBatch(rows=tuple(rows), rejected=tuple(rejected))
