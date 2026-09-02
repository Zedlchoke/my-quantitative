"""FX weekly session model: 24/5 clock, named-zone session labels, DST, rollover.

Owner: A4 (PLAN_forex.md sections 3, 7/A4, 8; gate ``FX1_SESSION_DST_PASS``).

Correctness contracts frozen here:

* the trading week is 24/5 with an explicit, provider-specific weekend
  convention (:class:`FxWeekConvention`); the module default opens Sunday
  21:00 America/New_York and closes Friday 16:00 America/New_York, but the
  convention parameters are always exposed and never hidden;
* session labels (SYDNEY / TOKYO / LONDON / NEW_YORK) are derived from named
  IANA zones via :mod:`zoneinfo` — never from fixed UTC offsets;
* all intervals are UTC half-open ``[start, end)``;
* the weekend gap between the Friday close and the Sunday open contains no
  fabricated sessions;
* the New York 17:00 daily rollover boundary is computed in the named zone so
  DST shifts it correctly (17:00 EST = 22:00Z, 17:00 EDT = 21:00Z);
* DST transition instants are located by bisection against zoneinfo truth and
  exposed as exact UTC stress windows for later lanes.

Session local times (Sydney 07:00-16:00, Tokyo 09:00-18:00, London
08:00-17:00, New York 08:00-17:00) and the weekly open/close convention are
SYNTHETIC_TEST_ONLY inputs: they are conventional defaults for testing, not an
authoritative venue calendar.  Real provider conventions must be passed
explicitly via :class:`FxWeekConvention` / :class:`FxSessionSpec`.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6

# A position still open across the Wednesday New York 17:00 rollover books
# three days of swap (wedged over the weekend).  Consumed by the rollover lane.
TRIPLE_ROLL_WEEKDAY = WEDNESDAY
TRIPLE_ROLL_MULTIPLIER = 3

SYDNEY_ZONE = "Australia/Sydney"
TOKYO_ZONE = "Asia/Tokyo"
LONDON_ZONE = "Europe/London"
NEW_YORK_ZONE = "America/New_York"


def require_zone_name(zone_name: str) -> str:
    """Validate an IANA zone name resolvable by zoneinfo; fail closed."""
    if not isinstance(zone_name, str) or not zone_name.strip():
        raise ValueError(f"zone name must be a non-empty string, got {zone_name!r}")
    try:
        ZoneInfo(zone_name)
    except Exception as exc:  # noqa: BLE001 - zoneinfo raises several types
        raise ValueError(f"unknown IANA time zone {zone_name!r}: {exc}") from exc
    return zone_name


def local_wall_to_utc(
    zone_name: str,
    wall: datetime,
    *,
    fold: int = 0,
) -> datetime:
    """Convert a naive local wall time in ``zone_name`` to an aware UTC instant.

    Fails closed on wall times that do not exist (DST spring-forward gap).
    Ambiguous wall times (DST fall-back) resolve via ``fold`` (0 = earlier
    instant, 1 = later instant) per PEP 495.
    """
    require_zone_name(zone_name)
    if wall.tzinfo is not None:
        raise ValueError("wall datetime must be naive local time")
    if fold not in (0, 1):
        raise ValueError(f"fold must be 0 or 1, got {fold!r}")
    zone = ZoneInfo(zone_name)
    local = wall.replace(tzinfo=zone, fold=fold)
    off0 = wall.replace(tzinfo=zone, fold=0).utcoffset()
    off1 = wall.replace(tzinfo=zone, fold=1).utcoffset()
    if off0 is None or off1 is None:  # pragma: no cover - zoneinfo always answers
        raise ValueError(f"zoneinfo could not resolve offset for {wall} in {zone_name}")
    if off0 < off1:
        raise ValueError(
            f"local time {wall} does not exist in {zone_name} "
            "(DST spring-forward gap); refusing to fabricate an instant"
        )
    return local.astimezone(timezone.utc)


# --- session label specs ---------------------------------------------------- #
@dataclass(frozen=True)
class FxSessionSpec:
    """One labeled FX session defined by local wall times in a named zone.

    The local times are SYNTHETIC_TEST_ONLY conventions; providers with real
    session definitions must construct their own explicit specs.
    """

    label: str
    zone_name: str
    open_local: time
    close_local: time

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError(f"session label must be non-empty, got {self.label!r}")
        require_zone_name(self.zone_name)
        if not isinstance(self.open_local, time) or not isinstance(self.close_local, time):
            raise ValueError("open_local/close_local must be datetime.time")
        if self.close_local <= self.open_local:
            raise ValueError(
                f"session {self.label}: close_local must be after open_local (same local day)"
            )

    def interval_utc(self, day: date) -> tuple[datetime, datetime]:
        """UTC half-open ``[start, end)`` for the session on local civil ``day``."""
        start = local_wall_to_utc(
            self.zone_name, datetime.combine(day, self.open_local)
        )
        end = local_wall_to_utc(
            self.zone_name, datetime.combine(day, self.close_local)
        )
        if end <= start:  # pragma: no cover - validated by construction
            raise ValueError(f"session {self.label} on {day}: end not after start")
        return start, end


# Conventional G10 session wall times (SYNTHETIC_TEST_ONLY defaults).
SYDNEY_SESSION = FxSessionSpec("SYDNEY", SYDNEY_ZONE, time(7, 0), time(16, 0))
TOKYO_SESSION = FxSessionSpec("TOKYO", TOKYO_ZONE, time(9, 0), time(18, 0))
LONDON_SESSION = FxSessionSpec("LONDON", LONDON_ZONE, time(8, 0), time(17, 0))
NEW_YORK_SESSION = FxSessionSpec("NEW_YORK", NEW_YORK_ZONE, time(8, 0), time(17, 0))

FX_SESSION_SPECS: tuple[FxSessionSpec, ...] = (
    SYDNEY_SESSION,
    TOKYO_SESSION,
    LONDON_SESSION,
    NEW_YORK_SESSION,
)


# --- weekly 24/5 market window ---------------------------------------------- #
@dataclass(frozen=True)
class FxWeekConvention:
    """Explicit provider-specific 24/5 weekly convention (no hidden defaults).

    The default instance opens Sunday 21:00 America/New_York and closes Friday
    16:00 America/New_York with the New York 17:00 rollover — a conventional
    SYNTHETIC_TEST_ONLY choice, exposed field by field so a real provider
    convention can be declared instead.
    """

    provider_id: str
    open_weekday: int
    open_local: time
    open_zone_name: str
    close_weekday: int
    close_local: time
    close_zone_name: str
    rollover_zone_name: str
    rollover_local: time

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, str) or not self.provider_id.strip():
            raise ValueError(f"provider_id must be non-empty, got {self.provider_id!r}")
        for field_name in ("open_weekday", "close_weekday"):
            value = getattr(self, field_name)
            if not isinstance(value, int) or not 0 <= value <= 6:
                raise ValueError(f"{field_name} must be an int weekday 0-6, got {value!r}")
        for field_name in ("open_local", "close_local", "rollover_local"):
            value = getattr(self, field_name)
            if not isinstance(value, time):
                raise ValueError(f"{field_name} must be datetime.time, got {value!r}")
        for field_name in ("open_zone_name", "close_zone_name", "rollover_zone_name"):
            require_zone_name(getattr(self, field_name))

    def week_open_day_for(self, day: date) -> date:
        """The week's open civil date: most recent ``open_weekday`` <= ``day``."""
        if not isinstance(day, date):
            raise ValueError(f"day must be a date, got {type(day).__name__}")
        delta = (day.weekday() - self.open_weekday) % 7
        return day - timedelta(days=delta)


DEFAULT_FX_WEEK_CONVENTION = FxWeekConvention(
    provider_id="SYNTHETIC_TEST_ONLY_NY_SUN21_CLOSE_FRI16",
    open_weekday=SUNDAY,
    open_local=time(21, 0),
    open_zone_name=NEW_YORK_ZONE,
    close_weekday=FRIDAY,
    close_local=time(16, 0),
    close_zone_name=NEW_YORK_ZONE,
    rollover_zone_name=NEW_YORK_ZONE,
    rollover_local=time(17, 0),
)


def weekly_open_utc(week_open_day: date, convention: FxWeekConvention) -> datetime:
    """Aware UTC instant of the weekly open whose open-day is ``week_open_day``."""
    if not isinstance(convention, FxWeekConvention):
        raise ValueError("convention must be an FxWeekConvention (never implicit)")
    if week_open_day.weekday() != convention.open_weekday:
        raise ValueError(
            f"week_open_day {week_open_day} is a {week_open_day.weekday()=}, "
            f"expected weekday {convention.open_weekday}"
        )
    return local_wall_to_utc(
        convention.open_zone_name,
        datetime.combine(week_open_day, convention.open_local),
    )


def weekly_close_utc(week_open_day: date, convention: FxWeekConvention) -> datetime:
    """Aware UTC instant of the weekly close for the week opened by ``week_open_day``."""
    if not isinstance(convention, FxWeekConvention):
        raise ValueError("convention must be an FxWeekConvention (never implicit)")
    if week_open_day.weekday() != convention.open_weekday:
        raise ValueError(
            f"week_open_day {week_open_day} is a {week_open_day.weekday()=}, "
            f"expected weekday {convention.open_weekday}"
        )
    close_day = week_open_day + timedelta(days=(convention.close_weekday - convention.open_weekday) % 7)
    return local_wall_to_utc(
        convention.close_zone_name,
        datetime.combine(close_day, convention.close_local),
    )


def is_market_open(moment_utc: datetime, convention: FxWeekConvention) -> bool:
    """True when ``moment_utc`` is inside the half-open weekly window.

    ``[weekly_open, weekly_close)`` for the week containing the moment;
    the weekend gap and the post-close Friday afternoon are closed.
    """
    if not isinstance(convention, FxWeekConvention):
        raise ValueError("convention must be an FxWeekConvention (never implicit)")
    if moment_utc.tzinfo is None:
        raise ValueError("moment_utc must be tz-aware")
    open_day = convention.week_open_day_for(moment_utc.astimezone(
        ZoneInfo(convention.open_zone_name)
    ).date())
    week_open = weekly_open_utc(open_day, convention)
    if moment_utc < week_open:
        return False  # before this week's open (e.g. Sunday pre-open)
    week_close = weekly_close_utc(open_day, convention)
    return moment_utc < week_close


# --- per-day labeled sessions ------------------------------------------------ #
@dataclass(frozen=True)
class FxSessionInterval:
    """One labeled session as a UTC half-open interval plus marking flags."""

    start_utc: datetime
    end_utc: datetime
    label: str
    zone_name: str = ""
    is_shortened: bool = False
    is_illiquid: bool = False

    def __post_init__(self) -> None:
        for name in ("start_utc", "end_utc"):
            value = getattr(self, name)
            if not isinstance(value, datetime) or value.tzinfo is None:
                raise ValueError(f"{name} must be a tz-aware datetime")
        if self.end_utc <= self.start_utc:
            raise ValueError("session interval end must be after start")
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError(f"session label must be non-empty, got {self.label!r}")

    def overlaps(self, start_utc: datetime, end_utc: datetime) -> bool:
        """Half-open overlap test against ``[start_utc, end_utc)``."""
        return self.start_utc < end_utc and start_utc < self.end_utc

    def clipped(self, start_utc: datetime, end_utc: datetime) -> "FxSessionInterval | None":
        """Interval intersected with ``[start_utc, end_utc)``, or ``None`` if empty."""
        new_start = max(self.start_utc, start_utc)
        new_end = min(self.end_utc, end_utc)
        if new_start >= new_end:
            return None
        return replace(self, start_utc=new_start, end_utc=new_end)


def day_session_intervals(
    day: date,
    specs: tuple[FxSessionSpec, ...] = FX_SESSION_SPECS,
) -> tuple[FxSessionInterval, ...]:
    """Labeled session intervals (UTC, half-open) for zone-local civil ``day``.

    Pure named-zone mapping: no weekend/holiday awareness — market-window
    gating happens in :func:`sessions_for_trading_week` and the calendar.
    """
    intervals: list[FxSessionInterval] = []
    for spec in specs:
        if not isinstance(spec, FxSessionSpec):
            raise ValueError("specs must contain FxSessionSpec instances")
        start, end = spec.interval_utc(day)
        intervals.append(
            FxSessionInterval(
                start_utc=start, end_utc=end, label=spec.label, zone_name=spec.zone_name
            )
        )
    return tuple(intervals)


# --- shortened / illiquid marking hooks -------------------------------------- #
class SessionMarkingHook(abc.ABC):
    """Hook that rewrites one day's labeled interval (short/illiquid marking)."""

    @abc.abstractmethod
    def apply(self, day: date, interval: FxSessionInterval) -> FxSessionInterval:
        """Return the (possibly modified) interval for ``day``."""


@dataclass(frozen=True)
class LocalCutoffHook(SessionMarkingHook):
    """Shorten sessions in one zone at a local wall-time cutoff (early close)."""

    zone_name: str
    cutoff_local: time

    def __post_init__(self) -> None:
        require_zone_name(self.zone_name)
        if not isinstance(self.cutoff_local, time):
            raise ValueError("cutoff_local must be datetime.time")

    def apply(self, day: date, interval: FxSessionInterval) -> FxSessionInterval:
        if interval.zone_name != self.zone_name:
            return interval  # hook is scoped to its own zone
        cutoff_utc = local_wall_to_utc(
            self.zone_name, datetime.combine(day, self.cutoff_local)
        )
        clipped = interval.clipped(interval.start_utc, cutoff_utc)
        if clipped is None or clipped == interval:
            return interval
        return replace(clipped, is_shortened=True)


@dataclass(frozen=True)
class IlliquidWindowHook(SessionMarkingHook):
    """Mark sessions illiquid where they overlap a local wall-time window."""

    zone_name: str
    window_start_local: time
    window_end_local: time

    def __post_init__(self) -> None:
        require_zone_name(self.zone_name)
        if self.window_end_local <= self.window_start_local:
            raise ValueError("window_end_local must be after window_start_local")

    def apply(self, day: date, interval: FxSessionInterval) -> FxSessionInterval:
        if interval.zone_name != self.zone_name:
            return interval  # hook is scoped to its own zone
        zone = ZoneInfo(self.zone_name)
        win_start = datetime.combine(day, self.window_start_local, tzinfo=zone)
        win_end = datetime.combine(day, self.window_end_local, tzinfo=zone)
        if interval.start_utc < win_end and win_start < interval.end_utc:
            return replace(interval, is_illiquid=True)
        return interval


def apply_session_hooks(
    day: date,
    intervals: tuple[FxSessionInterval, ...],
    hooks: tuple[SessionMarkingHook, ...] = (),
) -> tuple[FxSessionInterval, ...]:
    """Apply each hook in order to every interval (zone-mismatched hooks no-op)."""
    for hook in hooks:
        if not isinstance(hook, SessionMarkingHook):
            raise ValueError("hooks must be SessionMarkingHook instances")
        intervals = tuple(hook.apply(day, interval) for interval in intervals)
    return intervals


def sessions_for_trading_week(
    week_open_day: date,
    convention: FxWeekConvention,
    specs: tuple[FxSessionSpec, ...] = FX_SESSION_SPECS,
    hooks: tuple[SessionMarkingHook, ...] = (),
) -> tuple[FxSessionInterval, ...]:
    """Labeled sessions of one trading week, clipped to the weekly window.

    Only zone-local Monday..Friday dates are mapped and each interval is
    intersected with ``[weekly_open, weekly_close)``; the weekend gap between
    the Friday close and the Sunday/Monday open therefore contains no
    fabricated sessions by construction.
    """
    week_open = weekly_open_utc(week_open_day, convention)
    week_close = weekly_close_utc(week_open_day, convention)
    out: list[FxSessionInterval] = []
    for offset in range(1, 6):  # Monday..Friday local civil dates of the week
        day = week_open_day + timedelta(days=offset)
        for interval in apply_session_hooks(day, day_session_intervals(day, specs), hooks):
            clipped = interval.clipped(week_open, week_close)
            if clipped is not None:
                out.append(clipped)
    return tuple(out)


# --- rollover / trading-day clock -------------------------------------------- #
def rollover_instant_utc(day: date, convention: FxWeekConvention) -> datetime:
    """Aware UTC instant of the daily rollover at ``convention.rollover_local``
    on civil date ``day`` in the rollover zone (New York 17:00 by default)."""
    if not isinstance(convention, FxWeekConvention):
        raise ValueError("convention must be an FxWeekConvention (never implicit)")
    return local_wall_to_utc(
        convention.rollover_zone_name,
        datetime.combine(day, convention.rollover_local),
    )


def trading_day_of(moment_utc: datetime, convention: FxWeekConvention) -> date:
    """The FX trading day a UTC moment belongs to (rollover-zone anchored).

    The trading day runs rollover-to-rollover: local times at or after
    ``rollover_local`` map to the next civil date.  The Sunday-evening open
    therefore maps to Monday's trading day.
    """
    if moment_utc.tzinfo is None:
        raise ValueError("moment_utc must be tz-aware")
    local = moment_utc.astimezone(ZoneInfo(convention.rollover_zone_name))
    day = local.date()
    if local.time() >= convention.rollover_local:
        day = date.fromordinal(day.toordinal() + 1)
    return day


def is_triple_roll(day: date) -> bool:
    """True when a position held across ``day``'s rollover books three days
    of swap (Wednesday by convention; weekend value-date wedge)."""
    if not isinstance(day, date):
        raise ValueError(f"day must be a date, got {type(day).__name__}")
    return day.weekday() == TRIPLE_ROLL_WEEKDAY


# --- DST transition discovery ------------------------------------------------ #
@dataclass(frozen=True)
class DstTransition:
    """One named-zone DST transition located exactly, in UTC."""

    zone_name: str
    instant_utc: datetime
    offset_before: timedelta
    offset_after: timedelta

    @property
    def shift(self) -> timedelta:
        return self.offset_after - self.offset_before


def _offset_at_utc(zone: ZoneInfo, moment_utc: datetime) -> timedelta:
    """Zone offset in force AT a UTC instant.

    ``ZoneInfo.utcoffset(dt)`` interprets ``dt``'s wall clock as zone-local
    time, so a UTC moment must be converted into the zone first — reading the
    offset directly on a UTC datetime silently answers for the wrong instant.
    """
    return zone.utcoffset(moment_utc.astimezone(zone))


def _first_instant_with_offset(
    zone: ZoneInfo,
    lo_utc: datetime,
    hi_utc: datetime,
    target_offset: timedelta,
) -> datetime:
    """First UTC second in ``(lo_utc, hi_utc]`` whose offset equals target.

    Precondition: ``_offset_at_utc(lo_utc) != target_offset`` and
    ``_offset_at_utc(hi_utc) == target_offset``.  Bisection against zoneinfo
    truth on integer epoch seconds, so probes and the result are exact
    whole seconds.
    """
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    lo = int((lo_utc - epoch).total_seconds())
    hi = int((hi_utc - epoch).total_seconds())
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if _offset_at_utc(zone, epoch + timedelta(seconds=mid)) == target_offset:
            hi = mid
        else:
            lo = mid
    return epoch + timedelta(seconds=hi)


def dst_transitions_utc(
    zone_name: str,
    start_day: date,
    end_day: date,
) -> tuple[DstTransition, ...]:
    """Exact UTC instants of every DST transition of ``zone_name`` in a range.

    Scans in 12-hour steps at UTC midnights/noons and bisects each detected
    offset change to one-second precision (transitions in the supported zones
    land on whole seconds/minutes).
    """
    require_zone_name(zone_name)
    if end_day < start_day:
        raise ValueError("end_day precedes start_day")
    zone = ZoneInfo(zone_name)
    t = datetime.combine(start_day, time(0, 0), tzinfo=timezone.utc)
    stop = datetime.combine(end_day, time(0, 0), tzinfo=timezone.utc) + timedelta(days=1)
    step = timedelta(hours=12)
    transitions: list[DstTransition] = []
    while t < stop:
        nxt = min(t + step, stop)
        off_t = _offset_at_utc(zone, t)
        off_nxt = _offset_at_utc(zone, nxt)
        if off_t != off_nxt:
            instant = _first_instant_with_offset(zone, t, nxt, off_nxt)
            transitions.append(
                DstTransition(
                    zone_name=zone_name,
                    instant_utc=instant,
                    offset_before=_offset_at_utc(
                        zone, instant - timedelta(seconds=1)
                    ),
                    offset_after=off_nxt,
                )
            )
        t = nxt
    return tuple(transitions)


def dst_stress_windows_utc(
    zone_name: str,
    start_day: date,
    end_day: date,
    *,
    hours_before: int = 2,
    hours_after: int = 2,
) -> tuple[tuple[datetime, datetime], ...]:
    """Exact UTC half-open windows ``[instant - before, instant + after)`` around
    each DST transition — the stress-test subset for later lanes."""
    if hours_before < 0 or hours_after < 0:
        raise ValueError("hours_before/hours_after must be non-negative")
    windows: list[tuple[datetime, datetime]] = []
    for transition in dst_transitions_utc(zone_name, start_day, end_day):
        windows.append(
            (
                transition.instant_utc - timedelta(hours=hours_before),
                transition.instant_utc + timedelta(hours=hours_after),
            )
        )
    return tuple(windows)
