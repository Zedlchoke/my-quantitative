"""Session-calendar interface (owner: A2, PLAN_stocks.md section 6).

Pure interface only: session boundaries, holidays and early closes are
declared here; equities/forex implement their own concrete calendars in
their own lanes.  This module contains **no** implicit 24/7 default — the
only 24/7 calendar shipped is ``TEST_ONLY_DummySolar24x7``, whose id starts
with ``TEST_ONLY_`` so it can never be mistaken for a production calendar
and production code can fail closed against it via
:func:`require_production_calendar_id`.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from datetime import date, datetime, time, timezone

TEST_ONLY_CALENDAR_PREFIX = "TEST_ONLY_"

TEST_ONLY_DUMMY_SOLAR_24X7_ID = "TEST_ONLY_DUMMY_SOLAR_24X7"


@dataclass(frozen=True)
class Session:
    """One trading session in UTC (half-open interval ``[start, end)``)."""

    start_utc: datetime
    end_utc: datetime
    is_early_close: bool = False
    label: str | None = None

    def __post_init__(self) -> None:
        for name in ("start_utc", "end_utc"):
            value = getattr(self, name)
            if not isinstance(value, datetime) or value.tzinfo is None:
                raise ValueError(f"{name} must be a tz-aware datetime")
        if self.end_utc <= self.start_utc:
            raise ValueError("session end must be after session start")
        if not self.is_early_close and self.label is not None and not self.label.strip():
            raise ValueError("session label must be non-empty when given")


class SessionCalendar(abc.ABC):
    """Abstract session calendar.

    Implementations declare, for a calendar id, which days are sessions,
    their UTC boundaries, holidays and early closes.  A calendar is always
    referenced by id from manifests/contracts; there is no global default
    calendar object in this package.
    """

    @property
    @abc.abstractmethod
    def calendar_id(self) -> str: ...

    @abc.abstractmethod
    def is_session_day(self, day: date) -> bool:
        """True when ``day`` has at least one trading session."""

    @abc.abstractmethod
    def holidays(self, start: date, end: date) -> tuple[date, ...]:
        """Holidays (non-session days declared by the venue) in the range."""

    @abc.abstractmethod
    def session_bounds(self, day: date) -> Session | None:
        """UTC session boundaries for ``day``, or ``None`` when closed."""

    @abc.abstractmethod
    def early_close_cutoff_utc(self, day: date) -> datetime | None:
        """Early-close cutoff for ``day`` in UTC, or ``None`` if full day."""

    def sessions_between(self, start: date, end: date) -> tuple[Session, ...]:
        """Concrete helper: sessions for every session day in ``[start, end]``."""
        if end < start:
            raise ValueError("end date precedes start date")
        sessions: list[Session] = []
        day = start
        while day <= end:
            session = self.session_bounds(day)
            if session is not None:
                sessions.append(session)
            day = date.fromordinal(day.toordinal() + 1)
        return tuple(sessions)

    def is_test_only(self) -> bool:
        return is_test_only_calendar_id(self.calendar_id)


class TEST_ONLY_DummySolar24x7(SessionCalendar):
    """TEST-ONLY 24x7 solar-day calendar (every UTC day, 00:00-24:00).

    ``TEST_ONLY_`` prefix is contractual: this calendar exists so the
    historical crypto lane can adapt onto the shared interface in tests and
    dev scaffolding.  It is NOT a production calendar, must never be chosen
    implicitly, and any production path must reject it via
    :func:`require_production_calendar_id`.  Equities/forex implement real
    session calendars in their own lanes.
    """

    @property
    def calendar_id(self) -> str:
        return TEST_ONLY_DUMMY_SOLAR_24X7_ID

    def is_session_day(self, day: date) -> bool:
        return True

    def holidays(self, start: date, end: date) -> tuple[date, ...]:
        if end < start:
            raise ValueError("end date precedes start date")
        return ()

    def session_bounds(self, day: date) -> Session | None:
        midnight = datetime.combine(day, time.min, tzinfo=timezone.utc)
        next_midnight = datetime.combine(
            date.fromordinal(day.toordinal() + 1), time.min, tzinfo=timezone.utc
        )
        return Session(start_utc=midnight, end_utc=next_midnight)

    def early_close_cutoff_utc(self, day: date) -> datetime | None:
        return None


def is_test_only_calendar_id(calendar_id: str) -> bool:
    """True when the id is explicitly marked TEST_ONLY."""
    return str(calendar_id).startswith(TEST_ONLY_CALENDAR_PREFIX)


def require_production_calendar_id(calendar_id: str, *, context: str = "") -> str:
    """Fail closed: reject empty or TEST_ONLY calendar ids on production paths."""
    if not str(calendar_id).strip():
        raise ValueError(f"{context}: calendar_id must be explicit (never defaulted)")
    if is_test_only_calendar_id(calendar_id):
        raise ValueError(
            f"{context}: TEST_ONLY calendar {calendar_id!r} is not valid on a "
            "production path; declare a real venue calendar id"
        )
    return calendar_id
