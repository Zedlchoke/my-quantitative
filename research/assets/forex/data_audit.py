"""Gap/staleness/duplicate classification over loaded quote batches
(owner: A3, PLAN_forex.md 7-A3).

The audit takes a ``research.assets.common.calendar.SessionCalendar``
instance by dependency injection — this lane never imports a concrete forex
calendar module (a sibling lane owns it) and this module ships no calendar
at all.  Provider gaps are classified by the session calendar rather than a
fixed 24/7 cadence (PLAN_forex.md section 7-A3, initial data floors):

* an interval between consecutive accepted rows longer than ``max_gap`` is
  a :data:`GAP_IN_SESSION` when any calendar session overlaps it (missing
  data where the market traded) and :data:`GAP_NON_SESSION` otherwise
  (e.g. a weekend closure — expected, passed through unfilled);

* gaps are never filled: every :class:`GapRecord` carries
  ``filled=False`` by construction and the audit raises if told otherwise;

* staleness and duplicate evidence is counted from the batch rejections
  produced by the loader, per reason code.

The report carries a checksum manifest: sha256 over the canonical JSON of
the audit payload (sorted keys, tight separators) so audit evidence is
byte-stable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from types import MappingProxyType
from typing import Any, Mapping

from research.assets.common.calendar import SessionCalendar
from research.assets.common.contracts import canonical_json, sha256_text
from research.assets.forex.loader import QuoteBatch

AUDIT_SCHEMA = "forex_data_audit_manifest"
AUDIT_SCHEMA_VERSION = 1

GAP_IN_SESSION = "GAP_IN_SESSION"
GAP_NON_SESSION = "GAP_NON_SESSION"
GAP_CLASSIFICATIONS = (GAP_IN_SESSION, GAP_NON_SESSION)


@dataclass(frozen=True)
class GapRecord:
    """One unfilled gap between consecutive accepted rows of one symbol."""

    symbol: str
    start_utc: str  # ISO-8601 UTC (manifest-safe by construction)
    end_utc: str
    duration_seconds: float
    classification: str
    filled: bool = False  # structural: this module never fills gaps

    def __post_init__(self) -> None:
        if self.classification not in GAP_CLASSIFICATIONS:
            raise ValueError(
                f"classification must be one of {GAP_CLASSIFICATIONS}, "
                f"got {self.classification!r}"
            )
        if self.filled is not False:
            raise ValueError(
                "gaps are passed through unfilled by contract; filled=True "
                "is not a valid audit record"
            )
        if not isinstance(self.duration_seconds, (int, float)) or isinstance(
            self.duration_seconds, bool
        ):
            raise ValueError("duration_seconds must be a real number")


def _overlaps_any_session(
    calendar: SessionCalendar, start: datetime, end: datetime
) -> bool:
    """True when any calendar session overlaps the half-open gap interval."""
    day = start.date()
    last = end.date()
    while day <= last:
        session = calendar.session_bounds(day)
        if session is not None and session.start_utc < end and start < session.end_utc:
            return True
        day = date.fromordinal(day.toordinal() + 1)
    return False


def classify_gap(calendar: SessionCalendar, start_utc: datetime, end_utc: datetime) -> str:
    """Classify one gap interval against the injected session calendar."""
    _require_calendar(calendar)
    if end_utc <= start_utc:
        raise ValueError(
            f"gap end {end_utc.isoformat()} must be after gap start "
            f"{start_utc.isoformat()}"
        )
    if _overlaps_any_session(calendar, start_utc, end_utc):
        return GAP_IN_SESSION
    return GAP_NON_SESSION


def _require_calendar(calendar: SessionCalendar) -> None:
    if not isinstance(calendar, SessionCalendar):
        raise TypeError(
            "calendar must be a research.assets.common.calendar.SessionCalendar "
            f"instance, got {type(calendar).__name__}"
        )


def find_gaps(
    batch: QuoteBatch, *, calendar: SessionCalendar, max_gap: timedelta
) -> tuple[GapRecord, ...]:
    """Detect and classify inter-row gaps per symbol over accepted rows."""
    _require_calendar(calendar)
    if not isinstance(batch, QuoteBatch):
        raise TypeError(
            f"batch must be a loader QuoteBatch, got {type(batch).__name__}"
        )
    if not isinstance(max_gap, timedelta) or max_gap <= timedelta(0):
        raise ValueError(f"max_gap must be a positive timedelta, got {max_gap!r}")

    previous: dict[str, datetime] = {}
    gaps: list[GapRecord] = []
    for row in batch.rows:
        last = previous.get(row.symbol)
        previous[row.symbol] = row.event_ts_utc
        if last is None:
            continue
        if row.event_ts_utc == last:
            raise ValueError(
                "audit input contains a duplicate event timestamp; loader "
                "must reject duplicates before audit"
            )
        if row.event_ts_utc < last:
            raise ValueError(
                "audit input rows must be sorted by event time per symbol; "
                "loader must reject unsorted events before audit"
            )
        if row.event_ts_utc - last > max_gap:
            last_iso = last.isoformat()
            event_iso = row.event_ts_utc.isoformat()
            gaps.append(
                GapRecord(
                    symbol=row.symbol,
                    start_utc=last_iso,
                    end_utc=event_iso,
                    duration_seconds=(row.event_ts_utc - last).total_seconds(),
                    classification=classify_gap(calendar, last, row.event_ts_utc),
                )
            )
    return tuple(gaps)


@dataclass(frozen=True)
class AuditReport:
    """Accepted/rejected counts, reason codes, gaps and a checksum manifest."""

    calendar_id: str
    calendar_is_test_only: bool
    accepted_count: int
    rejected_count: int
    rejected_by_reason: Mapping[str, int]
    gaps: tuple[GapRecord, ...]
    max_gap_seconds: float
    symbols: tuple[str, ...]
    manifest: Mapping[str, Any] = field(repr=False)
    checksum: str

    def __post_init__(self) -> None:
        if not isinstance(self.calendar_id, str) or not self.calendar_id.strip():
            raise ValueError("calendar_id must be a non-empty string")
        if not isinstance(self.calendar_is_test_only, bool):
            raise ValueError("calendar_is_test_only must be a bool")
        for name in ("accepted_count", "rejected_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative int, got {value!r}")
        if not isinstance(self.checksum, str) or len(self.checksum) != 64:
            raise ValueError("checksum must be a 64-char sha256 hex string")

    @property
    def stale_count(self) -> int:
        return self.rejected_by_reason.get("STALE_QUOTE", 0)

    @property
    def duplicate_count(self) -> int:
        return self.rejected_by_reason.get("DUPLICATE_EVENT", 0)

    def gaps_by_classification(self) -> Mapping[str, int]:
        counts: dict[str, int] = {}
        for gap in self.gaps:
            counts[gap.classification] = counts.get(gap.classification, 0) + 1
        return MappingProxyType(dict(sorted(counts.items())))


def audit_quote_batch(
    batch: QuoteBatch,
    *,
    calendar: SessionCalendar,
    max_gap: timedelta,
) -> AuditReport:
    """Audit a loader batch: counts, reason codes, gap classification, manifest."""
    _require_calendar(calendar)
    if not isinstance(batch, QuoteBatch):
        raise TypeError(
            f"batch must be a loader QuoteBatch, got {type(batch).__name__}"
        )
    if not isinstance(max_gap, timedelta) or max_gap <= timedelta(0):
        raise ValueError(f"max_gap must be a positive timedelta, got {max_gap!r}")

    gaps = find_gaps(batch, calendar=calendar, max_gap=max_gap)
    rejected_by_reason = batch.rejected_by_reason()
    symbols = tuple(sorted({row.symbol for row in batch.rows}))

    manifest: dict[str, Any] = {
        "schema": AUDIT_SCHEMA,
        "version": AUDIT_SCHEMA_VERSION,
        "calendar_id": calendar.calendar_id,
        "calendar_is_test_only": calendar.is_test_only(),
        "max_gap_seconds": max_gap.total_seconds(),
        "accepted_count": batch.accepted_count,
        "rejected_count": batch.rejected_count,
        "rejected_by_reason": dict(rejected_by_reason),
        "symbols": list(symbols),
        "gaps": [
            {
                "symbol": gap.symbol,
                "start_utc": gap.start_utc,
                "end_utc": gap.end_utc,
                "duration_seconds": gap.duration_seconds,
                "classification": gap.classification,
                "filled": gap.filled,
            }
            for gap in gaps
        ],
    }
    checksum = sha256_text(canonical_json(manifest))
    return AuditReport(
        calendar_id=calendar.calendar_id,
        calendar_is_test_only=calendar.is_test_only(),
        accepted_count=batch.accepted_count,
        rejected_count=batch.rejected_count,
        rejected_by_reason=MappingProxyType(dict(rejected_by_reason)),
        gaps=gaps,
        max_gap_seconds=max_gap.total_seconds(),
        symbols=symbols,
        manifest=MappingProxyType(manifest),
        checksum=checksum,
    )
