"""FOREX-NG5 P0 — A2 release-clock model (documented convention -> 16:00-NY grid).

The convention frozen by the amended plan (A2): CFTC CoT reports are released
Fridays 15:30 America/New_York (as-of the preceding Tuesday); a federal
holiday delays release to the next business day (documented 1-2 day slip;
critic V2 verified verbatim from the ReleaseSchedule page). For pre-window
years where no per-release evidence exists, decisions use this convention
shifted to the NEXT 16:00-NY grid point, and the census marks every such
decision window ``convention`` (never ``evidenced``).

Federal-holiday arithmetic here is deterministic calendar RULES (not
evidence); the model's CONVENTION status comes from the plan, not from this
code. Holiday rules implemented: New Year's Day, MLK (3rd Mon Jan),
Washington's Birthday (3rd Mon Feb), Memorial (last Mon May), Juneteenth
(2021+), Independence, Labor (1st Mon Sep), Columbus (2nd Mon Oct), Veterans,
Thanksgiving (4th Thu Nov), Christmas — fixed-date holidays observed to the
adjacent weekday when they land on a weekend.

Evidenced windows (rolling release-schedule page, Historical Special
Announcements republication table) carry their own dates; the runner attaches
them explicitly and never mixes them with this convention model.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")
RELEASE_CLOCK = "15:30 America/New_York (documented convention)"
GRID_CLOCK = "16:00 America/New_York (frozen decision grid)"


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    d = date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    return d + timedelta(days=offset + 7 * (n - 1))


def _last_weekday_of_month(year: int, month: int, weekday: int) -> date:
    if month == 12:
        d = date(year, 12, 31)
    else:
        d = date(year, month + 1, 1) - timedelta(days=1)
    offset = (d.weekday() - weekday) % 7
    return d - timedelta(days=offset)


def _observed(d: date) -> date:
    """Weekend fixed-date holidays are observed Fri-before / Mon-after."""
    if d.weekday() == 5:  # Saturday
        return d - timedelta(days=1)
    if d.weekday() == 6:  # Sunday
        return d + timedelta(days=1)
    return d


def is_federal_holiday(d: date) -> Optional[str]:
    """Name of the federal holiday observed on ``d``, else None (1986+).

    Observation rules: fixed-date holidays falling on Saturday are observed
    the preceding Friday; falling on Sunday, the following Monday.
    """
    year = d.year
    named = []
    fixed = [
        (date(year, 1, 1), "New Year's Day"),
        (date(year, 7, 4), "Independence Day"),
        (date(year, 11, 11), "Veterans Day"),
        (date(year, 12, 25), "Christmas Day"),
    ]
    if year >= 2021:
        fixed.append((date(year, 6, 19), "Juneteenth"))
    for fd, nm in fixed:
        named.append((_observed(fd), nm))
    named.append((_nth_weekday(year, 1, 0, 3), "Birthday of Martin Luther King, Jr."))
    named.append((_nth_weekday(year, 2, 0, 3), "Washington's Birthday"))
    named.append((_last_weekday_of_month(year, 5, 0), "Memorial Day"))
    named.append((_nth_weekday(year, 9, 0, 1), "Labor Day"))
    named.append((_nth_weekday(year, 10, 0, 2), "Columbus Day"))
    thanksgiving = _nth_weekday(year, 11, 3, 4)
    named.append((thanksgiving, "Thanksgiving Day"))
    for obs_day, nm in named:
        if d == obs_day:
            return nm
    return None


def next_business_day(d: date) -> date:
    nxt = d + timedelta(days=1)
    while nxt.weekday() >= 5 or is_federal_holiday(nxt):
        nxt += timedelta(days=1)
    return nxt


def convention_release(as_of: date) -> dict:
    """Documented-convention release date + decision grid for a Tuesday as-of.

    as_of is the Tuesday as-of date; the convention release is that Friday
    15:30 NY, sliding one business day per federal holiday. Decision grid =
    first 16:00-NY grid point STRICTLY AFTER the release instant; 15:30 <
    16:00 so the grid date is the release date itself.
    """
    d = as_of + timedelta(days=3)  # Friday of that week
    shifted = False
    while d.weekday() >= 5 or is_federal_holiday(d) is not None:
        d += timedelta(days=1)
        shifted = True
    return {
        "as_of": as_of.isoformat(),
        "release_date": d.isoformat(),
        "holiday_shifted": shifted,
        "release_clock": RELEASE_CLOCK,
        "grid_date": d.isoformat(),
        "grid_clock": GRID_CLOCK,
        "basis": "convention",
    }


def schedule_as_of(release_date: date) -> date:
    """The as-of Tuesday for a schedule-page release date.

    Non-delayed Friday release: the Tuesday of that week (release - 3).
    Delayed Mon/Tue release: the Tuesday of the ORIGINAL week (the Friday
    that was missed - 3). Rule: the most recent Tuesday strictly before
    ``release_date`` for weekday >= Tue, else before ``release_date - 4``.
    """
    probe = release_date if release_date.weekday() >= 1 else release_date - timedelta(days=4)
    back = (probe.weekday() - 1) % 7
    if back == 0:
        back = 7
    return probe - timedelta(days=back)


def evidenced_grid(release_date: date, basis_note: str) -> dict:
    """Decision grid from an EVIDENCED release date (schedule / announcements).

    Release instant = documented 15:30 NY on the evidenced date; grid = same
    day 16:00 NY (strictly after). Marked ``evidenced`` with the source note.
    """
    return {
        "release_date": release_date.isoformat(),
        "release_clock": RELEASE_CLOCK + " (time-of-day documented; date evidenced)",
        "grid_date": release_date.isoformat(),
        "grid_clock": GRID_CLOCK,
        "basis": "evidenced",
        "basis_note": basis_note,
    }


def grid_instant_utc(grid_date: date) -> str:
    """The 16:00-NY grid point as a UTC ISO instant (audit convenience)."""
    from datetime import timezone

    dt = datetime(grid_date.year, grid_date.month, grid_date.day, 16, 0, tzinfo=NY_TZ)
    return dt.astimezone(timezone.utc).isoformat()


def month_name_to_int(name: str) -> Optional[int]:
    names = ["january", "february", "march", "april", "may", "june", "july",
             "august", "september", "october", "november", "december"]
    n = names.index((name or "").strip().lower()) + 1
    return n if 1 <= n <= 12 else None
