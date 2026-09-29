"""Decision calendar + session/cost windows — PC12A implementation lane.

Authorities:
- BACKTEST_CAMPAIGN_DESIGN.md §3 — fold calendar: window 2021-01-08 →
  2026-06-26 (286 Fridays), 52-week warmup, 8 test folds × 26 weeks,
  1-week embargo between train and test, remaining 26-week sealed tail
  EXCLUDED (S1-class, untouched).
- CLASS_SPEC_VOLPROF_M1.md §4 — session windows rebuilt from IANA tzdata
  (Europe/London, America/New_York), no hardcoded DST offsets; hard flat
  19:55 UTC; no-trade window 21:00–23:00 UTC daily.
- FILL_ACCOUNTING_SPEC.md §2 — swap calendar: accrual events at 22:00 UTC;
  Sun/Mon/Tue ×1, Wed ×3, Thu ×1, NO event at the Fri close boundary or
  Saturday (the DECLARED U4/U5 modeling calendar).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import List, Tuple
from zoneinfo import ZoneInfo

UTC = dt.timezone.utc
CAMPAIGN_START = dt.date(2021, 1, 8)    # first decision Friday
CAMPAIGN_END = dt.date(2026, 6, 26)     # last decision Friday
N_DECISION_FRIDAYS = 286
WARMUP_WEEKS = 52
N_TEST_FOLDS = 8
TEST_FOLD_WEEKS = 26
EMBARGO_WEEKS = 1
SEALED_TAIL_WEEKS = 26

_TZ_LONDON = ZoneInfo("Europe/London")
_TZ_NEWYORK = ZoneInfo("America/New_York")
_TZ_TOKYO = ZoneInfo("Asia/Tokyo")

# Declared swap calendar (U4/U5): weekday name -> accrual multiplier at the
# 22:00 UTC boundary. Friday's close boundary carries NO event; Saturday has
# none; the weekend is carried by Wednesday's x3.
SWAP_CALENDAR = {"Sun": 1, "Mon": 1, "Tue": 1, "Wed": 3, "Thu": 1,
                 "Fri": 0, "Sat": 0}

ROLLOVER_WINDOW_UTC = (dt.time(21, 0), dt.time(23, 0))  # no-trade / event slip
ROLL_WINDOW_CHARGE = (dt.time(21, 0), dt.time(22, 0))   # C2 (21:00,22:00]
SUNDAY_REOPEN_EVENT_MIN = 15                            # C3 first 15 min


class CalendarError(RuntimeError):
    pass


def decision_fridays() -> List[dt.date]:
    """The 286 campaign decision Fridays 2021-01-08..2026-06-26 inclusive."""
    if CAMPAIGN_START.weekday() != 4 or CAMPAIGN_END.weekday() != 4:
        raise CalendarError("campaign bounds must be Fridays")
    out = []
    d = CAMPAIGN_START
    while d <= CAMPAIGN_END:
        out.append(d)
        d += dt.timedelta(days=7)
    if len(out) != N_DECISION_FRIDAYS:
        raise CalendarError(
            f"expected {N_DECISION_FRIDAYS} Fridays, got {len(out)}")
    return out


@dataclass(frozen=True)
class Fold:
    fold_id: int          # 0..7
    train_start: dt.date  # expanding train window (walk-forward)
    train_end: dt.date    # inclusive; excludes the embargo week
    test_start: dt.date   # first decision Friday of the test fold
    test_end: dt.date     # last decision Friday of the test fold


def fold_calendar() -> List[Fold]:
    """8 expanding-train folds with the 1-week train-side embargo.

    Arithmetic (286 = 52 + 8x26 + 26): warmup f[0..51]; test fold k covers
    f[52 + 26k .. 52 + 26(k+1) - 1]; sealed tail f[260..285] is EXCLUDED from
    every fold and from warmup. For each fold the TRAIN window ends one week
    (the embargo) before the fold's first test Friday; fold 0's train is the
    warmup itself.
    """
    fridays = decision_fridays()
    folds: List[Fold] = []
    for k in range(N_TEST_FOLDS):
        test_start_idx = WARMUP_WEEKS + k * TEST_FOLD_WEEKS
        test_end_idx = test_start_idx + TEST_FOLD_WEEKS - 1
        if test_end_idx >= len(fridays) - SEALED_TAIL_WEEKS:
            raise CalendarError("test fold intrudes into the sealed tail")
        test_start, test_end = fridays[test_start_idx], fridays[test_end_idx]
        train_end = fridays[test_start_idx - 1 - EMBARGO_WEEKS] \
            if test_start_idx - EMBARGO_WEEKS > 0 else fridays[test_start_idx - 1]
        train_start = fridays[0]
        folds.append(Fold(k, train_start, train_end, test_start, test_end))
    if folds[-1].test_end != fridays[52 + N_TEST_FOLDS * TEST_FOLD_WEEKS - 1]:
        raise CalendarError("fold arithmetic drift")
    return folds


def sealed_tail() -> Tuple[dt.date, dt.date]:
    fridays = decision_fridays()
    start = fridays[WARMUP_WEEKS + N_TEST_FOLDS * TEST_FOLD_WEEKS]
    return start, fridays[-1]


# ---------------------------------------------------------------------------
# Session marks (tzdata-rebuilt, DST-correct; never hardcoded offsets)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SessionMark:
    name: str
    tz_name: str
    local_start: dt.time
    local_end: dt.time


LONDON_ENTRY = SessionMark("London", "Europe/London",
                           dt.time(8, 0), dt.time(12, 0))
NY_ENTRY = SessionMark("NewYork", "America/New_York",
                       dt.time(9, 30), dt.time(16, 0))


def _to_utc(day: dt.date, tz: ZoneInfo, t: dt.time) -> dt.datetime:
    local = dt.datetime.combine(day, t, tzinfo=tz)
    return local.astimezone(UTC)


def session_windows_utc(day: dt.date) -> List[Tuple[dt.datetime, dt.datetime,
                                                    str]]:
    """UTC entry windows for the day from the pinned tzdata zones.

    The conversion is the ONLY place offset knowledge lives (VOLPROF spec
    §4.1): London [08:00,12:00) and NY [09:30,16:00) in local wall time,
    rebuilt per calendar date, DST-correct on both sides of every seam.
    """
    out = []
    for mark in (LONDON_ENTRY, NY_ENTRY):
        tz = ZoneInfo(mark.tz_name)
        start = _to_utc(day, tz, mark.local_start)
        end = _to_utc(day, tz, mark.local_end)
        if end <= start:
            # cannot happen for these windows; fail closed if tzdata shifts
            raise CalendarError(f"{mark.name} window inverted on {day}")
        out.append((start, end, mark.name))
    return out


def in_entry_window(ts: dt.datetime, day: dt.date) -> bool:
    return any(s <= ts < e for s, e, _ in session_windows_utc(day))


def utc_time_of(ts: dt.datetime) -> dt.time:
    """UTC wall time of an aware timestamp as a NAIVE time (comparable
    with the frozen window constants; tzdata work happens in the
    zoneinfo conversions only)."""
    return ts.astimezone(UTC).time()


def sunday_reopen_window_utc(day: dt.date) -> Tuple[dt.datetime, dt.datetime]:
    """C3 window: the first 15 minutes after the FX spot reopen.

    The feed reopens when New York closes Friday and comes back Sunday
    ~17:00 America/New_York (audit §B: winter reopen 22:00-22:05Z, summer
    21:00-21:04Z -- exactly the NY-close boundary shifting with US DST),
    so the reopen instant is tzdata-rebuilt, never hardcoded.
    """
    if day.strftime("%a") != "Sun":
        raise CalendarError(f"{day} is not a Sunday")
    reopen_local = dt.datetime.combine(day, dt.time(17, 0),
                                       tzinfo=_TZ_NEWYORK)
    start = reopen_local.astimezone(UTC)
    return start, start + dt.timedelta(minutes=SUNDAY_REOPEN_EVENT_MIN)


def is_sunday_reopen(ts: dt.datetime) -> bool:
    if ts.astimezone(UTC).weekday() != 6:
        return False
    start, end = sunday_reopen_window_utc(ts.astimezone(UTC).date())
    return start <= ts < end


def is_in_rollover_window(ts: dt.datetime) -> bool:
    t = utc_time_of(ts)
    return ROLLOVER_WINDOW_UTC[0] <= t < ROLLOVER_WINDOW_UTC[1]


def is_in_roll_charge_window(ts: dt.datetime) -> bool:
    """The C2 pricing window (21:00,22:00] on the fill-bar timestamp."""
    t = utc_time_of(ts)
    return dt.time(21, 0) < t <= dt.time(22, 0)


def is_hard_flat_instant(ts: dt.datetime) -> bool:
    """VOLPROF hard-flat boundary: 19:55 UTC daily (positions must be 0)."""
    return utc_time_of(ts) == dt.time(19, 55)


# ---------------------------------------------------------------------------
# Swap accrual events (DECLARED U4/U5 modeling calendar)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SwapEvent:
    ts_utc: dt.datetime
    weekday: str
    multiplier: int
    wed_x3: bool


def swap_multiplier(weekday_name: str) -> int:
    m = SWAP_CALENDAR[weekday_name]
    if m < 0:
        raise CalendarError("negative swap multiplier")
    return m


def swap_events_between(start: dt.datetime,
                        end: dt.datetime) -> List[SwapEvent]:
    """Accrual boundaries in (start, end] at 22:00 UTC with the frozen
    calendar (no Friday-close or Saturday event; Wednesday carries x3)."""
    if end <= start:
        return []
    events: List[SwapEvent] = []
    d = start.astimezone(UTC).date()
    last = end.astimezone(UTC).date()
    while d <= last:
        name = d.strftime("%a")
        mult = swap_multiplier(name)
        if mult > 0:
            ts = dt.datetime.combine(d, dt.time(22, 0), tzinfo=UTC)
            if start < ts <= end:
                events.append(SwapEvent(ts, name, mult, name == "Wed"))
        d += dt.timedelta(days=1)
    return events


def wed_x3_weeklies(start: dt.date, end: dt.date) -> int:
    """Number of Wednesday x3 accrual events in [start, end] (disclosure)."""
    n = 0
    d = start
    while d <= end:
        if d.strftime("%a") == "Wed":
            n += 1
        d += dt.timedelta(days=1)
    return n
