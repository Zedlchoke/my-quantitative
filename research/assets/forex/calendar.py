"""FxSessionCalendar: FX spot session calendar and PIT macro-event clock.

Owner: A4 (PLAN_forex.md sections 3, 7/A4, 8; gate ``FX1_SESSION_DST_PASS``).

Implements the abstract ``research.assets.common.calendar.SessionCalendar``
interface for G10 spot FX on top of the weekly 24/5 model in
:mod:`research.assets.forex.sessions`.

Correctness contracts frozen here:

* the calendar id is explicit and validated (never defaulted, never a silent
  24/7 fallback);
* the holiday table is an explicit constructor input.  Every shipped holiday
  table is SYNTHETIC_TEST_ONLY — it carries no authority claim — unless the
  caller passes a real ``authority_id``; a table without an authority and
  without the SYNTHETIC_TEST_ONLY flag is a construction error;
* ``is_session_day`` is trading-day anchored (New York rollover convention):
  Monday..Friday, weekend days are not session days, and a full-closure
  holiday removes the day;
* ``session_bounds`` stays inside the weekly market window, so the weekend
  gap contains no fabricated sessions;
* ``pit_event_timestamps`` only accepts macro events that carry a publish
  time and refuses any event whose publish-time is later than its event-time
  (no post-release backfill into pre-release features).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta
from typing import Iterable, Sequence

from research.assets.common.calendar import Session, SessionCalendar
from research.assets.common.contracts import require_digest_hex, require_token
from research.assets.forex.sessions import (
    DEFAULT_FX_WEEK_CONVENTION,
    FxSessionInterval,
    FxWeekConvention,
    apply_session_hooks,
    day_session_intervals,
    is_triple_roll as weekly_is_triple_roll,
    local_wall_to_utc,
    rollover_instant_utc,
    trading_day_of,
    weekly_close_utc,
    weekly_open_utc,
)

SYNTHETIC_TEST_ONLY = "SYNTHETIC_TEST_ONLY"


# --- holiday inputs (synthetic unless an authority is declared) -------------- #
@dataclass(frozen=True)
class FxHolidayEntry:
    """One holiday declaration: a date plus affected currencies/zone.

    ``closes_market=True`` removes the trading day entirely;
    ``closes_market=False`` keeps the day but marks it thin (illiquid) and
    may carry an ``early_close_local`` wall time in the weekly convention's
    rollover zone.
    """

    day: date
    currencies: tuple[str, ...]
    zone_name: str | None = None
    closes_market: bool = True
    early_close_local: time | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.day, date):
            raise ValueError(f"day must be a date, got {type(self.day).__name__}")
        if not self.currencies or not all(
            isinstance(c, str) and c.strip() for c in self.currencies
        ):
            raise ValueError("currencies must be a non-empty tuple of codes")
        if self.zone_name is not None and not isinstance(self.zone_name, str):
            raise ValueError("zone_name must be a string or None")
        if self.early_close_local is not None and not isinstance(
            self.early_close_local, time
        ):
            raise ValueError("early_close_local must be datetime.time or None")
        if self.early_close_local is not None and self.closes_market:
            raise ValueError("an early close cannot coexist with a full-market closure")


@dataclass(frozen=True)
class FxHolidayTable:
    """Explicit holiday table: SYNTHETIC_TEST_ONLY unless ``authority_id`` is set.

    Construction is fail-closed: exactly one of the SYNTHETIC_TEST_ONLY flag
    or a non-empty ``authority_id`` must be present, so a synthetic table can
    never masquerade as authoritative (and vice versa).
    """

    entries: tuple[FxHolidayEntry, ...]
    synthetic_test_only: bool
    authority_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.synthetic_test_only, bool):
            raise ValueError("synthetic_test_only must be a bool")
        if self.synthetic_test_only:
            if self.authority_id is not None:
                raise ValueError(
                    "a SYNTHETIC_TEST_ONLY holiday table must not carry an authority id"
                )
        else:
            if self.authority_id is None:
                raise ValueError(
                    "holiday table without an authority must be flagged "
                    f"{SYNTHETIC_TEST_ONLY} (no authoritative holidays are claimed)"
                )
            require_token(self.authority_id, "authority_id")
        for entry in self.entries:
            if not isinstance(entry, FxHolidayEntry):
                raise ValueError("entries must be FxHolidayEntry instances")

    @classmethod
    def synthetic(cls, entries: Sequence[FxHolidayEntry]) -> "FxHolidayTable":
        """Build a clearly-labeled SYNTHETIC_TEST_ONLY table (never authoritative)."""
        return cls(entries=tuple(entries), synthetic_test_only=True)

    @classmethod
    def from_authority(
        cls, entries: Sequence[FxHolidayEntry], authority_id: str
    ) -> "FxHolidayTable":
        """Build a table attributed to an explicit holiday authority id."""
        return cls(
            entries=tuple(entries), synthetic_test_only=False, authority_id=authority_id
        )

    @property
    def is_synthetic(self) -> bool:
        return self.synthetic_test_only

    @property
    def provenance(self) -> str:
        return SYNTHETIC_TEST_ONLY if self.synthetic_test_only else str(self.authority_id)


EMPTY_SYNTHETIC_HOLIDAY_TABLE = FxHolidayTable.synthetic(())


# --- PIT macro-event clock ---------------------------------------------------- #
@dataclass(frozen=True)
class MacroEvent:
    """A scheduled macro event with publication provenance.

    ``publish_time_utc`` is when the record was published by its source; it is
    mandatory for the PIT clock.  An event whose publish-time is later than
    its event-time is backfill and is refused downstream.
    """

    event_id: str
    event_time_utc: datetime
    publish_time_utc: datetime | None

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError(f"event_id must be non-empty, got {self.event_id!r}")
        for name in ("event_time_utc",):
            value = getattr(self, name)
            if not isinstance(value, datetime) or value.tzinfo is None:
                raise ValueError(f"{name} must be a tz-aware datetime")
        publish = self.publish_time_utc
        if publish is not None and (
            not isinstance(publish, datetime) or publish.tzinfo is None
        ):
            raise ValueError("publish_time_utc must be a tz-aware datetime or None")


@dataclass(frozen=True)
class PitRefusal:
    """One refused macro event plus the reason it cannot enter PIT features."""

    event_id: str
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError(f"event_id must be non-empty, got {self.event_id!r}")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError(f"reason must be non-empty, got {self.reason!r}")


@dataclass(frozen=True)
class PitEventClockResult:
    """Accepted PIT event timestamps plus explicit refusals with reasons."""

    source_digest: str
    accepted: tuple[tuple[str, datetime], ...]
    refusals: tuple[PitRefusal, ...]


# --- the calendar -------------------------------------------------------------- #
class FxSessionCalendar(SessionCalendar):
    """G10 spot-FX session calendar over the weekly 24/5 model.

    Trading days are New-York-rollover anchored (Monday..Friday; the Sunday
    open belongs to Monday's trading day; Saturday is never a session day).
    Holiday tables are SYNTHETIC_TEST_ONLY unless an authority id is passed.
    """

    def __init__(
        self,
        *,
        calendar_id: str,
        convention: FxWeekConvention | None = None,
        holiday_table: FxHolidayTable | None = None,
        session_hooks: tuple = (),
    ) -> None:
        require_token(calendar_id, "calendar_id")
        self._calendar_id = calendar_id
        self.convention = (
            convention if convention is not None else DEFAULT_FX_WEEK_CONVENTION
        )
        if not isinstance(self.convention, FxWeekConvention):
            raise ValueError("convention must be an FxWeekConvention")
        self.holiday_table = (
            holiday_table if holiday_table is not None else EMPTY_SYNTHETIC_HOLIDAY_TABLE
        )
        if not isinstance(self.holiday_table, FxHolidayTable):
            raise ValueError("holiday_table must be an FxHolidayTable")
        self.session_hooks = tuple(session_hooks)

    # -- identity -------------------------------------------------------------- #
    @property
    def calendar_id(self) -> str:
        return self._calendar_id

    @property
    def holiday_provenance(self) -> str:
        """``SYNTHETIC_TEST_ONLY`` or the authority id backing the holiday table."""
        return self.holiday_table.provenance

    @property
    def is_production_ready(self) -> bool:
        """False unless holidays come from a declared authority (fail closed)."""
        return not self.holiday_table.is_synthetic

    def require_production_ready(self) -> None:
        """Raise unless the holiday table is authoritative — scoring must fail
        closed against SYNTHETIC_TEST_ONLY holiday inputs."""
        if not self.is_production_ready:
            raise ValueError(
                f"calendar {self._calendar_id}: holiday table is "
                f"{SYNTHETIC_TEST_ONLY} and must never back a production path"
            )

    # -- holiday helpers -------------------------------------------------------- #
    def _closure_entries_for(self, day: date) -> tuple["FxHolidayEntry", ...]:
        return tuple(
            entry
            for entry in self.holiday_table.entries
            if entry.day == day and entry.closes_market
        )

    def _nonclosure_entries_for(self, day: date) -> tuple["FxHolidayEntry", ...]:
        return tuple(
            entry
            for entry in self.holiday_table.entries
            if entry.day == day and not entry.closes_market
        )

    # -- SessionCalendar interface ---------------------------------------------- #
    def is_session_day(self, day: date) -> bool:
        """True for Monday..Friday trading days without a full-closure holiday.

        Saturday (and Sunday: the Sunday open belongs to Monday's trading
        day) are never session days.
        """
        if not isinstance(day, date):
            raise ValueError(f"day must be a date, got {type(day).__name__}")
        if day.weekday() > 4:  # Saturday/Sunday
            return False
        return not self._closure_entries_for(day)

    def holidays(self, start: date, end: date) -> tuple[date, ...]:
        """Full-closure holiday dates (weekdays only) in ``[start, end]``.

        Weekend entries cannot remove a session (the market is closed) and are
        therefore not surfaced as holidays.
        """
        if end < start:
            raise ValueError("end date precedes start date")
        days = {
            entry.day
            for entry in self.holiday_table.entries
            if entry.closes_market and entry.day.weekday() <= 4 and start <= entry.day <= end
        }
        return tuple(sorted(days))

    def session_bounds(self, day: date) -> Session | None:
        """UTC session for trading day ``day``, or ``None`` when closed.

        The trading day runs from the previous day's 17:00 rollover (clamped
        up to the weekly open) to this day's 17:00 rollover (clamped down to
        the weekly close), so the weekend gap is never fabricated.
        """
        if not self.is_session_day(day):
            return None
        convention = self.convention
        week_open_day = convention.week_open_day_for(day)
        week_open = weekly_open_utc(week_open_day, convention)
        week_close = weekly_close_utc(week_open_day, convention)
        start = max(
            rollover_instant_utc(day - timedelta(days=1), convention), week_open
        )
        end = min(rollover_instant_utc(day, convention), week_close)
        cutoff = self.early_close_cutoff_utc(day)
        if cutoff is not None:
            end = min(end, cutoff)
        if end <= start:  # pragma: no cover - validated by construction
            raise ValueError(f"trading day {day}: bounds collapsed (start={start}, end={end})")
        return Session(start_utc=start, end_utc=end, is_early_close=cutoff is not None)

    def early_close_cutoff_utc(self, day: date) -> datetime | None:
        """Early-close cutoff in UTC for ``day``, or ``None`` for a full day."""
        for entry in self._nonclosure_entries_for(day):
            if entry.early_close_local is not None:
                return local_wall_to_utc(
                    self.convention.rollover_zone_name,
                    datetime.combine(day, entry.early_close_local),
                )
        return None

    # -- FX-specific views ------------------------------------------------------- #
    def weekly_open_utc(self, week_open_day: date) -> datetime:
        """UTC instant of the weekly open for the week opened by ``week_open_day``."""
        return weekly_open_utc(week_open_day, self.convention)

    def weekly_close_utc(self, week_open_day: date) -> datetime:
        """UTC instant of the weekly close for the week opened by ``week_open_day``."""
        return weekly_close_utc(week_open_day, self.convention)

    def rollover_instant_utc(self, day: date) -> datetime:
        """UTC instant of the daily rollover on civil date ``day``."""
        return rollover_instant_utc(day, self.convention)

    def trading_day_of(self, moment_utc: datetime) -> date:
        """Trading day owning ``moment_utc`` (17:00 rollover-anchored)."""
        return trading_day_of(moment_utc, self.convention)

    def is_triple_roll(self, day: date) -> bool:
        """True when ``day``'s rollover books three days of swap.

        Weekly Wednesday rule AND the day must be a live session day (a
        full-closure holiday on the Wednesday suppresses the triple roll).
        """
        return weekly_is_triple_roll(day) and self.is_session_day(day)

    def labeled_sessions(self, day: date) -> tuple[FxSessionInterval, ...]:
        """Named-zone labeled sessions for trading day ``day``.

        Each zone-local session (Sydney/Tokyo/London/New_York civil date ==
        ``day``) is clipped to the trading-day bounds; non-closure holidays
        mark the surviving sessions illiquid.  Empty on closed days.
        """
        bounds = self.session_bounds(day)
        if bounds is None:
            return ()
        cutoff = self.early_close_cutoff_utc(day)
        thin_day = bool(self._nonclosure_entries_for(day))
        intervals = apply_session_hooks(
            day, day_session_intervals(day), self.session_hooks
        )
        out: list[FxSessionInterval] = []
        for interval in intervals:
            clipped = interval.clipped(bounds.start_utc, bounds.end_utc)
            if clipped is None:
                continue
            if clipped.end_utc < interval.end_utc and not clipped.is_shortened:
                # Friday weekly close and holiday early closes genuinely cut
                # the tail of a session: mark it shortened.
                clipped = replace(clipped, is_shortened=True)
            if thin_day:
                clipped = replace(clipped, is_illiquid=True)
            out.append(clipped)
        return tuple(out)

    # -- PIT macro-event clock ---------------------------------------------------- #
    def pit_event_timestamps(
        self,
        source_digest: str,
        events: Iterable[MacroEvent],
    ) -> PitEventClockResult:
        """PIT-safe event timestamps from one source, refusing backfill.

        * every event must carry a publish time (``publish_time_utc``);
        * any event whose publish-time is later than its event-time is
          refused with an explicit reason — no post-release backfill into
          pre-release features;
        * accepted events contribute their event-time (knowable by then,
          because publication happened at or before the event).

        ``source_digest`` is the lowercase sha256 of the source snapshot the
        events were read from (provenance, fail-closed format check).
        """
        require_digest_hex(source_digest, "source_digest")
        accepted: list[tuple[str, datetime]] = []
        refusals: list[PitRefusal] = []
        for event in events:
            if not isinstance(event, MacroEvent):
                raise TypeError(
                    f"events must be MacroEvent instances, got {type(event).__name__}"
                )
            if event.publish_time_utc is None:
                refusals.append(
                    PitRefusal(
                        event_id=event.event_id,
                        reason=(
                            "missing publish-time: the PIT macro clock only accepts "
                            "events that carry an explicit publish timestamp"
                        ),
                    )
                )
            elif event.publish_time_utc > event.event_time_utc:
                refusals.append(
                    PitRefusal(
                        event_id=event.event_id,
                        reason=(
                            f"backfilled event refused: publish-time "
                            f"{event.publish_time_utc.isoformat()} is later than "
                            f"event-time {event.event_time_utc.isoformat()} "
                            "(no post-release backfill into pre-release features)"
                        ),
                    )
                )
            else:
                accepted.append((event.event_id, event.event_time_utc))
        return PitEventClockResult(
            source_digest=source_digest,
            accepted=tuple(accepted),
            refusals=tuple(refusals),
        )


__all__ = [
    "SYNTHETIC_TEST_ONLY",
    "FxHolidayEntry",
    "FxHolidayTable",
    "EMPTY_SYNTHETIC_HOLIDAY_TABLE",
    "MacroEvent",
    "PitRefusal",
    "PitEventClockResult",
    "FxSessionCalendar",
]
