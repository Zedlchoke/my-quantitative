"""Exchange-calendar reconciliation for provided session lists (owner: A3).

Reconciles a data lane's provided daily session list against the shared
frozen calendar ``US_EQUITY_REGULAR_V1``
(``research/assets/stocks/calendar.py``, imported read-only) and fails
closed on every anomaly:

* missing regular sessions (expected by the calendar, absent from the
  data) are RECORDED, never filled: overnight/weekend/holiday gaps are
  returns, not fabricated bars;
* sessions present in the data but closed on the calendar
  (weekends/holidays/special closures) are RECORDED as unexpected;
* duplicate or unsorted input fails closed;
* no-print / halt interval records are classified with the calendar's
  ``classify_gap``; any ``GAP_UNEXPLAINED`` record fails the whole
  reconciliation (a declared halt only explains missing prints, it never
  authorizes a synthetic fill).

The verdict is ``PASS`` only when none of the above fires.  Anything else
is ``FAIL`` with machine-readable records — a truthful FAIL is a good
outcome and blocks the affected instrument (PLAN 4.1/4.2, gate FD5).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Sequence

try:  # normal package import (available after A2/integration merge)
    from research.assets.stocks.calendar import (
        CALENDAR_TABLE_END,
        CALENDAR_TABLE_START,
        ET_ZONE,
        USEquityRegularCalendar,
        US_EQUITY_REGULAR_V1,
        GapClassification,
        HaltInterval,
    )
except ImportError:  # direct file-path import in the A3 lane worktree
    _REPO_ROOT = Path(__file__).resolve().parents[2]
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from research.assets.stocks.calendar import (
        CALENDAR_TABLE_END,
        CALENDAR_TABLE_START,
        ET_ZONE,
        USEquityRegularCalendar,
        US_EQUITY_REGULAR_V1,
        GapClassification,
        HaltInterval,
    )

CALENDAR_CHECK_ID = "STOCKS_FREE_V1_CALENDAR_CHECK_V1"

VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"


@dataclass(frozen=True)
class CalendarAnomaly:
    """One recorded reconciliation anomaly (never silently repaired)."""

    kind: str  # MISSING_SESSION | UNEXPECTED_SESSION | DUPLICATE_SESSION |
    #            UNSORTED_INPUT | OUTSIDE_CALENDAR_HORIZON | UNEXPLAINED_GAP
    detail: str


@dataclass(frozen=True)
class SessionReconciliation:
    """Full reconciliation record for one provided session list."""

    verdict: str  # PASS | FAIL
    calendar_id: str
    calendar_table_version: str
    calendar_manifest_digest: str
    first_session: date | None
    last_session: date | None
    provided_count: int
    expected_count: int
    missing_sessions: tuple[date, ...]
    unexpected_sessions: tuple[date, ...]
    duplicate_sessions: tuple[date, ...]
    anomalies: tuple[CalendarAnomaly, ...]
    gap_classifications: tuple[GapClassification, ...]
    overnight_boundaries_classified: int

    @property
    def passed(self) -> bool:
        return self.verdict == VERDICT_PASS


def _require_date(value: object, name: str) -> date:
    if isinstance(value, datetime) or not isinstance(value, date):
        raise ValueError(
            f"{name} must be a datetime.date, got {type(value).__name__}"
        )
    return value


def reconcile_session_list(
    provided: Sequence[date],
    *,
    calendar: USEquityRegularCalendar = US_EQUITY_REGULAR_V1,
    declared_halts: Sequence[HaltInterval] = (),
    no_print_intervals: Sequence[tuple[datetime, datetime]] = (),
) -> SessionReconciliation:
    """Reconcile ``provided`` session dates against the frozen calendar.

    ``provided``: the session list the data lane actually delivered.
    ``declared_halts``: declared halt/no-print intervals (explain missing
    prints inside sessions; never authorize fills).
    ``no_print_intervals``: UTC half-open intervals reported by the data as
    having no prints; each is classified by ``calendar.classify_gap`` and
    any ``GAP_UNEXPLAINED`` fails the reconciliation.

    Never mutates, fills or extends the provided list.
    """
    anomalies: list[CalendarAnomaly] = []

    dates = [_require_date(d, "provided session") for d in provided]

    seen: set[date] = set()
    duplicates: list[date] = []
    unsorted_at: list[int] = []
    for i, day in enumerate(dates):
        if day in seen:
            duplicates.append(day)
        seen.add(day)
        if i > 0 and day < dates[i - 1] and not unsorted_at:
            unsorted_at.append(i)
    if unsorted_at:
        i = unsorted_at[0]
        anomalies.append(
            CalendarAnomaly(
                "UNSORTED_INPUT",
                f"provided list not strictly chronological at index {i}: "
                f"{dates[i - 1].isoformat()} -> {dates[i].isoformat()}",
            )
        )
    if duplicates:
        shown = ", ".join(d.isoformat() for d in sorted(set(duplicates))[:5])
        anomalies.append(
            CalendarAnomaly(
                "DUPLICATE_SESSION",
                f"{len(duplicates)} duplicate session date(s) (first: {shown})",
            )
        )

    if not dates:
        return SessionReconciliation(
            verdict=VERDICT_FAIL,
            calendar_id=calendar.calendar_id,
            calendar_table_version=calendar.table_version,
            calendar_manifest_digest=calendar.calendar_manifest_digest(),
            first_session=None,
            last_session=None,
            provided_count=0,
            expected_count=0,
            missing_sessions=(),
            unexpected_sessions=(),
            duplicate_sessions=tuple(sorted(set(duplicates))),
            anomalies=tuple(
                anomalies
                + [CalendarAnomaly("MISSING_SESSION", "empty provided session list")]
            ),
            gap_classifications=(),
            overnight_boundaries_classified=0,
        )

    first, last = dates[0], dates[-1]
    in_horizon = (
        first >= CALENDAR_TABLE_START and last <= CALENDAR_TABLE_END
    )
    if not in_horizon:
        anomalies.append(
            CalendarAnomaly(
                "OUTSIDE_CALENDAR_HORIZON",
                f"provided range [{first.isoformat()}, {last.isoformat()}] "
                f"leaves the frozen table horizon "
                f"[{CALENDAR_TABLE_START.isoformat()}, "
                f"{CALENDAR_TABLE_END.isoformat()}]; fail closed",
            )
        )

    expected = (
        [
            s.start_utc.astimezone(ET_ZONE).date()
            for s in calendar.sessions_in_range(first, last)
        ]
        if in_horizon
        else []
    )

    provided_set = set(dates)
    expected_set = set(expected)
    missing = sorted(expected_set - provided_set)
    unexpected = sorted(provided_set - expected_set)

    if missing:
        shown = ", ".join(d.isoformat() for d in missing[:5])
        anomalies.append(
            CalendarAnomaly(
                "MISSING_SESSION",
                f"{len(missing)} regular session(s) absent from the data "
                f"(first: {shown}); gaps are returns, never fabricated bars",
            )
        )
    if unexpected:
        reasons: list[str] = []
        for day in unexpected[:5]:
            if in_horizon:
                reason = calendar.closure_reason(day) or "UNKNOWN"
            else:
                reason = "OUTSIDE_CALENDAR_HORIZON"
            reasons.append(f"{day.isoformat()}={reason}")
        anomalies.append(
            CalendarAnomaly(
                "UNEXPECTED_SESSION",
                f"{len(unexpected)} provided date(s) with no regular session "
                f"(first: {'; '.join(reasons)})",
            )
        )

    # Overnight/weekend/holiday boundaries between consecutive provided
    # sessions are returns by construction; classify each so the record
    # shows WHY they are not fabricated bars.  Classification runs only for
    # strictly increasing pairs inside the calendar horizon; anything else
    # is already recorded above and is never guessed at.
    gap_classifications: list[GapClassification] = []
    boundary_classified = 0
    if in_horizon:
        for prev, nxt in zip(dates, dates[1:]):
            if nxt <= prev:
                continue  # duplicate/unsorted pair; already recorded
            prev_session = calendar.session_bounds(prev)
            nxt_session = calendar.session_bounds(nxt)
            if prev_session is None or nxt_session is None:
                continue
            classification = calendar.classify_gap(
                prev_session.end_utc,
                nxt_session.start_utc,
                declared_halts=declared_halts,
            )
            gap_classifications.append(classification)
            boundary_classified += 1

    # Caller-reported no-print intervals: fail closed on anything the
    # calendar cannot explain as fully outside sessions or halt-covered.
    for start_utc, end_utc in no_print_intervals:
        try:
            classification = calendar.classify_gap(
                start_utc, end_utc, declared_halts=declared_halts
            )
        except ValueError as exc:
            anomalies.append(
                CalendarAnomaly(
                    "UNEXPLAINED_GAP",
                    f"no-print interval [{start_utc.isoformat()}, "
                    f"{end_utc.isoformat()}) cannot be classified against "
                    f"the frozen calendar ({exc}); fail closed",
                )
            )
            continue
        gap_classifications.append(classification)
        if classification.unexplained:
            anomalies.append(
                CalendarAnomaly(
                    "UNEXPLAINED_GAP",
                    f"no-print interval [{start_utc.isoformat()}, "
                    f"{end_utc.isoformat()}) intersects regular sessions "
                    f"without a fully covering declared halt: "
                    f"{classification.reason}",
                )
            )

    verdict = VERDICT_FAIL if anomalies else VERDICT_PASS
    return SessionReconciliation(
        verdict=verdict,
        calendar_id=calendar.calendar_id,
        calendar_table_version=calendar.table_version,
        calendar_manifest_digest=calendar.calendar_manifest_digest(),
        first_session=first,
        last_session=last,
        provided_count=len(dates),
        expected_count=len(expected_set),
        missing_sessions=tuple(missing),
        unexpected_sessions=tuple(unexpected),
        duplicate_sessions=tuple(sorted(set(duplicates))),
        anomalies=tuple(anomalies),
        gap_classifications=tuple(gap_classifications),
        overnight_boundaries_classified=boundary_classified,
    )


def assert_sessions_reconciled(
    reconciliation: SessionReconciliation,
) -> SessionReconciliation:
    """Fail closed: raise ``ValueError`` when the verdict is FAIL."""
    if not reconciliation.passed:
        details = "; ".join(f"{a.kind}: {a.detail}" for a in reconciliation.anomalies)
        raise ValueError(f"calendar reconciliation failed: {details}")
    return reconciliation


__all__ = [
    "CALENDAR_CHECK_ID",
    "CalendarAnomaly",
    "SessionReconciliation",
    "VERDICT_FAIL",
    "VERDICT_PASS",
    "assert_sessions_reconciled",
    "reconcile_session_list",
]
