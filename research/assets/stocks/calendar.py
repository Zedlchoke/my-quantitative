"""US equity regular-session calendar ``US_EQUITY_REGULAR_V1`` (owner: A4).

Implements the shared :class:`research.assets.common.calendar.SessionCalendar`
interface for NYSE/Nasdaq regular trading sessions: 09:30-16:00
America/New_York, DST-correct via :mod:`zoneinfo`, with an EMBEDDED FROZEN
table of holidays and 13:00 ET early closes covering 2010-01-01 through
2030-12-31.

Source note (PLAN_stocks.md section 2 pinned references)
--------------------------------------------------------
Reference pinned in the contract: ``https://www.nyse.com/trade/hours-calendars``
(NYSE hours/calendar page).  The frozen table below is a deterministic
rendering of NYSE Rule 7.2 as published there:

* New Year's Day (Jan 1): Sunday -> observed Monday Jan 2; Saturday ->
  NOT observed (regular session on the preceding Friday Dec 31;
  documented precedents 2004-12-31, 2010-12-31, 2021-12-31 all open).
* Martin Luther King Jr. Day: 3rd Monday of January.
* Washington's Birthday: 3rd Monday of February.
* Good Friday: 2 days before Easter (Anonymous Gregorian computus).
* Memorial Day: last Monday of May.
* Juneteenth National Independence Day: June 19, effective 2022 only
  (federal holiday signed 2021-06-17; first NYSE closure Mon 2022-06-20).
  Saturday -> observed Friday; Sunday -> observed Monday.
* Independence Day (Jul 4): Saturday -> observed Friday Jul 3
  (precedents 2015, 2020); Sunday -> observed Monday Jul 5 (2010, 2021).
* Labor Day: 1st Monday of September.
* Thanksgiving: 4th Thursday of November; the following Friday is a
  13:00 ET early close every year.
* Christmas (Dec 25): Saturday -> observed Friday Dec 24 (2010, 2021);
  Sunday -> observed Monday Dec 26 (2011, 2016, 2022).
* Early close 13:00 ET on Jul 3 / Dec 24 only when the following holiday
  falls Tuesday-Friday, so the early-close day is the session immediately
  preceding the holiday.  When the holiday falls on Saturday the Friday
  (Jul 3 / Dec 24) is the FULL observed holiday, never an early close.
* Documented unscheduled full closures embedded explicitly:
  2012-10-29 and 2012-10-30 (Hurricane Sandy), 2018-12-05 (national day
  of mourning, President G.H.W. Bush), 2025-01-09 (national day of
  mourning, President J. Carter).

Table version and retrieval note
--------------------------------
``CALENDAR_TABLE_VERSION = "US_EQUITY_REGULAR_V1_TABLE_20260902"``: frozen
2026-09-02 by the A4 lane from the rule set above; generation script and
per-year session-count cross-checks (2010: 252, 2012: 250, 2018: 251,
2019: 252, 2020: 253, 2021: 252, 2022: 251, 2023: 250, 2024: 252,
2025: 250 documented counts, all reproduced) are archived under
``research/audits/stocks/s1_a4/``.  The 2010-2026 entries are consistent
with the nyse.com published calendars; 2027-2030 entries are rule-derived
pending publication and are listed in ``NEEDS_PROVIDER_VERIFICATION``.

This table is NOT an official provider feed and this module never claims
to be one: it is a frozen synthetic-golden baseline.  Never manufacture a
weekly calendar and call it official — production scoring must verify the
frozen table against the provider calendar and re-freeze a new table
version (new calendar manifest) on any drift.

Fail-closed behavior
--------------------
Queries outside ``[CALENDAR_TABLE_START, CALENDAR_TABLE_END]`` raise
``ValueError`` (the calendar never guesses).  Halts and no-print intervals
are never filled: :meth:`USEquityRegularCalendar.classify_gap` classifies a
missing-bar interval as ``GAP_OK_WITH_REASON`` (overnight/weekend/holiday
gaps are returns, not fabricated bars) or ``GAP_UNEXPLAINED``, and never
authorizes a synthetic fill.

Pre/post-market are represented as separate explicit flags and are
DISABLED in baseline scoring; :meth:`USEquityRegularCalendar.phase_bounds`
fails closed unless the phase was explicitly enabled at construction.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, time as dt_time, timedelta, timezone
from typing import Iterable, Sequence
from zoneinfo import ZoneInfo

from research.assets.common.calendar import Session, SessionCalendar

CALENDAR_ID = "US_EQUITY_REGULAR_V1"

CALENDAR_TABLE_VERSION = "US_EQUITY_REGULAR_V1_TABLE_20260902"
CALENDAR_TABLE_START = date(2010, 1, 1)
CALENDAR_TABLE_END = date(2030, 12, 31)

ET_ZONE = ZoneInfo("America/New_York")
SESSION_OPEN_ET = dt_time(9, 30)
REGULAR_CLOSE_ET = dt_time(16, 0)
EARLY_CLOSE_ET = dt_time(13, 0)

PHASE_PRE_MARKET = "PRE_MARKET"
PHASE_REGULAR = "REGULAR"
PHASE_POST_MARKET = "POST_MARKET"

PRE_MARKET_OPEN_ET = dt_time(4, 0)
POST_MARKET_CLOSE_ET = dt_time(20, 0)

GAP_OK_WITH_REASON = "GAP_OK_WITH_REASON"
GAP_UNEXPLAINED = "GAP_UNEXPLAINED"

# Entries below are rule-derived (NYSE typically publishes calendars about
# one year ahead).  They follow NYSE Rule 7.2 exactly as verified on the
# 2010-2026 published calendars; verify against nyse.com when published
# and re-freeze a new table version on any drift.  Nothing in this module
# is silently guessed: anything uncertain is listed here, never fabricated.
NEEDS_PROVIDER_VERIFICATION: tuple[str, ...] = (
    "2027-06-18: first Juneteenth Saturday-observance (Jun 19 2027 is a "
    "Saturday); Friday observance assumed per the Independence Day "
    "Saturday precedents (2015-07-03, 2020-07-03) — confirm on nyse.com",
    "2027-07-05: Independence Day Sunday-observance (Jul 4 2027 is a "
    "Sunday); precedents 2010-07-05 and 2021-07-05 — confirm on nyse.com",
    "2027-12-24: Christmas Saturday-observance (Dec 25 2027 is a "
    "Saturday); precedents 2010-12-24 and 2021-12-24 — confirm on nyse.com",
    "2028-01-17..2030-12-31: all remaining 2028-2030 entries are "
    "rule-derived from NYSE Rule 7.2 pending publication on nyse.com "
    "(includes 2028-2029-2030 early closes 07-03/11-24..29/12-24 and the "
    "2029-01-01..01-02 New Year entries)",
)

# --- frozen table (GENERATED — do not hand-edit; see audits generator) ----- #

_HOLIDAYS: frozenset[str] = frozenset({
    "2010-01-01",  # NEW_YEARS_DAY
    "2010-01-18",  # MARTIN_LUTHER_KING_JR_DAY
    "2010-02-15",  # WASHINGTONS_BIRTHDAY
    "2010-04-02",  # GOOD_FRIDAY
    "2010-05-31",  # MEMORIAL_DAY
    "2010-07-05",  # INDEPENDENCE_DAY_OBSERVED
    "2010-09-06",  # LABOR_DAY
    "2010-11-25",  # THANKSGIVING_DAY
    "2010-12-24",  # CHRISTMAS_DAY_OBSERVED
    "2011-01-17",  # MARTIN_LUTHER_KING_JR_DAY
    "2011-02-21",  # WASHINGTONS_BIRTHDAY
    "2011-04-22",  # GOOD_FRIDAY
    "2011-05-30",  # MEMORIAL_DAY
    "2011-07-04",  # INDEPENDENCE_DAY
    "2011-09-05",  # LABOR_DAY
    "2011-11-24",  # THANKSGIVING_DAY
    "2011-12-26",  # CHRISTMAS_DAY_OBSERVED
    "2012-01-02",  # NEW_YEARS_DAY_OBSERVED
    "2012-01-16",  # MARTIN_LUTHER_KING_JR_DAY
    "2012-02-20",  # WASHINGTONS_BIRTHDAY
    "2012-04-06",  # GOOD_FRIDAY
    "2012-05-28",  # MEMORIAL_DAY
    "2012-07-04",  # INDEPENDENCE_DAY
    "2012-09-03",  # LABOR_DAY
    "2012-11-22",  # THANKSGIVING_DAY
    "2012-12-25",  # CHRISTMAS_DAY
    "2013-01-01",  # NEW_YEARS_DAY
    "2013-01-21",  # MARTIN_LUTHER_KING_JR_DAY
    "2013-02-18",  # WASHINGTONS_BIRTHDAY
    "2013-03-29",  # GOOD_FRIDAY
    "2013-05-27",  # MEMORIAL_DAY
    "2013-07-04",  # INDEPENDENCE_DAY
    "2013-09-02",  # LABOR_DAY
    "2013-11-28",  # THANKSGIVING_DAY
    "2013-12-25",  # CHRISTMAS_DAY
    "2014-01-01",  # NEW_YEARS_DAY
    "2014-01-20",  # MARTIN_LUTHER_KING_JR_DAY
    "2014-02-17",  # WASHINGTONS_BIRTHDAY
    "2014-04-18",  # GOOD_FRIDAY
    "2014-05-26",  # MEMORIAL_DAY
    "2014-07-04",  # INDEPENDENCE_DAY
    "2014-09-01",  # LABOR_DAY
    "2014-11-27",  # THANKSGIVING_DAY
    "2014-12-25",  # CHRISTMAS_DAY
    "2015-01-01",  # NEW_YEARS_DAY
    "2015-01-19",  # MARTIN_LUTHER_KING_JR_DAY
    "2015-02-16",  # WASHINGTONS_BIRTHDAY
    "2015-04-03",  # GOOD_FRIDAY
    "2015-05-25",  # MEMORIAL_DAY
    "2015-07-03",  # INDEPENDENCE_DAY_OBSERVED
    "2015-09-07",  # LABOR_DAY
    "2015-11-26",  # THANKSGIVING_DAY
    "2015-12-25",  # CHRISTMAS_DAY
    "2016-01-01",  # NEW_YEARS_DAY
    "2016-01-18",  # MARTIN_LUTHER_KING_JR_DAY
    "2016-02-15",  # WASHINGTONS_BIRTHDAY
    "2016-03-25",  # GOOD_FRIDAY
    "2016-05-30",  # MEMORIAL_DAY
    "2016-07-04",  # INDEPENDENCE_DAY
    "2016-09-05",  # LABOR_DAY
    "2016-11-24",  # THANKSGIVING_DAY
    "2016-12-26",  # CHRISTMAS_DAY_OBSERVED
    "2017-01-02",  # NEW_YEARS_DAY_OBSERVED
    "2017-01-16",  # MARTIN_LUTHER_KING_JR_DAY
    "2017-02-20",  # WASHINGTONS_BIRTHDAY
    "2017-04-14",  # GOOD_FRIDAY
    "2017-05-29",  # MEMORIAL_DAY
    "2017-07-04",  # INDEPENDENCE_DAY
    "2017-09-04",  # LABOR_DAY
    "2017-11-23",  # THANKSGIVING_DAY
    "2017-12-25",  # CHRISTMAS_DAY
    "2018-01-01",  # NEW_YEARS_DAY
    "2018-01-15",  # MARTIN_LUTHER_KING_JR_DAY
    "2018-02-19",  # WASHINGTONS_BIRTHDAY
    "2018-03-30",  # GOOD_FRIDAY
    "2018-05-28",  # MEMORIAL_DAY
    "2018-07-04",  # INDEPENDENCE_DAY
    "2018-09-03",  # LABOR_DAY
    "2018-11-22",  # THANKSGIVING_DAY
    "2018-12-25",  # CHRISTMAS_DAY
    "2019-01-01",  # NEW_YEARS_DAY
    "2019-01-21",  # MARTIN_LUTHER_KING_JR_DAY
    "2019-02-18",  # WASHINGTONS_BIRTHDAY
    "2019-04-19",  # GOOD_FRIDAY
    "2019-05-27",  # MEMORIAL_DAY
    "2019-07-04",  # INDEPENDENCE_DAY
    "2019-09-02",  # LABOR_DAY
    "2019-11-28",  # THANKSGIVING_DAY
    "2019-12-25",  # CHRISTMAS_DAY
    "2020-01-01",  # NEW_YEARS_DAY
    "2020-01-20",  # MARTIN_LUTHER_KING_JR_DAY
    "2020-02-17",  # WASHINGTONS_BIRTHDAY
    "2020-04-10",  # GOOD_FRIDAY
    "2020-05-25",  # MEMORIAL_DAY
    "2020-07-03",  # INDEPENDENCE_DAY_OBSERVED
    "2020-09-07",  # LABOR_DAY
    "2020-11-26",  # THANKSGIVING_DAY
    "2020-12-25",  # CHRISTMAS_DAY
    "2021-01-01",  # NEW_YEARS_DAY
    "2021-01-18",  # MARTIN_LUTHER_KING_JR_DAY
    "2021-02-15",  # WASHINGTONS_BIRTHDAY
    "2021-04-02",  # GOOD_FRIDAY
    "2021-05-31",  # MEMORIAL_DAY
    "2021-07-05",  # INDEPENDENCE_DAY_OBSERVED
    "2021-09-06",  # LABOR_DAY
    "2021-11-25",  # THANKSGIVING_DAY
    "2021-12-24",  # CHRISTMAS_DAY_OBSERVED
    "2022-01-17",  # MARTIN_LUTHER_KING_JR_DAY
    "2022-02-21",  # WASHINGTONS_BIRTHDAY
    "2022-04-15",  # GOOD_FRIDAY
    "2022-05-30",  # MEMORIAL_DAY
    "2022-06-20",  # JUNETEENTH_OBSERVED
    "2022-07-04",  # INDEPENDENCE_DAY
    "2022-09-05",  # LABOR_DAY
    "2022-11-24",  # THANKSGIVING_DAY
    "2022-12-26",  # CHRISTMAS_DAY_OBSERVED
    "2023-01-02",  # NEW_YEARS_DAY_OBSERVED
    "2023-01-16",  # MARTIN_LUTHER_KING_JR_DAY
    "2023-02-20",  # WASHINGTONS_BIRTHDAY
    "2023-04-07",  # GOOD_FRIDAY
    "2023-05-29",  # MEMORIAL_DAY
    "2023-06-19",  # JUNETEENTH
    "2023-07-04",  # INDEPENDENCE_DAY
    "2023-09-04",  # LABOR_DAY
    "2023-11-23",  # THANKSGIVING_DAY
    "2023-12-25",  # CHRISTMAS_DAY
    "2024-01-01",  # NEW_YEARS_DAY
    "2024-01-15",  # MARTIN_LUTHER_KING_JR_DAY
    "2024-02-19",  # WASHINGTONS_BIRTHDAY
    "2024-03-29",  # GOOD_FRIDAY
    "2024-05-27",  # MEMORIAL_DAY
    "2024-06-19",  # JUNETEENTH
    "2024-07-04",  # INDEPENDENCE_DAY
    "2024-09-02",  # LABOR_DAY
    "2024-11-28",  # THANKSGIVING_DAY
    "2024-12-25",  # CHRISTMAS_DAY
    "2025-01-01",  # NEW_YEARS_DAY
    "2025-01-20",  # MARTIN_LUTHER_KING_JR_DAY
    "2025-02-17",  # WASHINGTONS_BIRTHDAY
    "2025-04-18",  # GOOD_FRIDAY
    "2025-05-26",  # MEMORIAL_DAY
    "2025-06-19",  # JUNETEENTH
    "2025-07-04",  # INDEPENDENCE_DAY
    "2025-09-01",  # LABOR_DAY
    "2025-11-27",  # THANKSGIVING_DAY
    "2025-12-25",  # CHRISTMAS_DAY
    "2026-01-01",  # NEW_YEARS_DAY
    "2026-01-19",  # MARTIN_LUTHER_KING_JR_DAY
    "2026-02-16",  # WASHINGTONS_BIRTHDAY
    "2026-04-03",  # GOOD_FRIDAY
    "2026-05-25",  # MEMORIAL_DAY
    "2026-06-19",  # JUNETEENTH
    "2026-07-03",  # INDEPENDENCE_DAY_OBSERVED
    "2026-09-07",  # LABOR_DAY
    "2026-11-26",  # THANKSGIVING_DAY
    "2026-12-25",  # CHRISTMAS_DAY
    "2027-01-01",  # NEW_YEARS_DAY
    "2027-01-18",  # MARTIN_LUTHER_KING_JR_DAY
    "2027-02-15",  # WASHINGTONS_BIRTHDAY
    "2027-03-26",  # GOOD_FRIDAY
    "2027-05-31",  # MEMORIAL_DAY
    "2027-06-18",  # JUNETEENTH_OBSERVED
    "2027-07-05",  # INDEPENDENCE_DAY_OBSERVED
    "2027-09-06",  # LABOR_DAY
    "2027-11-25",  # THANKSGIVING_DAY
    "2027-12-24",  # CHRISTMAS_DAY_OBSERVED
    "2028-01-17",  # MARTIN_LUTHER_KING_JR_DAY
    "2028-02-21",  # WASHINGTONS_BIRTHDAY
    "2028-04-14",  # GOOD_FRIDAY
    "2028-05-29",  # MEMORIAL_DAY
    "2028-06-19",  # JUNETEENTH
    "2028-07-04",  # INDEPENDENCE_DAY
    "2028-09-04",  # LABOR_DAY
    "2028-11-23",  # THANKSGIVING_DAY
    "2028-12-25",  # CHRISTMAS_DAY
    "2029-01-01",  # NEW_YEARS_DAY
    "2029-01-15",  # MARTIN_LUTHER_KING_JR_DAY
    "2029-02-19",  # WASHINGTONS_BIRTHDAY
    "2029-03-30",  # GOOD_FRIDAY
    "2029-05-28",  # MEMORIAL_DAY
    "2029-06-19",  # JUNETEENTH
    "2029-07-04",  # INDEPENDENCE_DAY
    "2029-09-03",  # LABOR_DAY
    "2029-11-22",  # THANKSGIVING_DAY
    "2029-12-25",  # CHRISTMAS_DAY
    "2030-01-01",  # NEW_YEARS_DAY
    "2030-01-21",  # MARTIN_LUTHER_KING_JR_DAY
    "2030-02-18",  # WASHINGTONS_BIRTHDAY
    "2030-04-19",  # GOOD_FRIDAY
    "2030-05-27",  # MEMORIAL_DAY
    "2030-06-19",  # JUNETEENTH
    "2030-07-04",  # INDEPENDENCE_DAY
    "2030-09-02",  # LABOR_DAY
    "2030-11-28",  # THANKSGIVING_DAY
    "2030-12-25",  # CHRISTMAS_DAY
})

_HALF_DAYS: frozenset[str] = frozenset({
    "2010-11-26",  # 13:00 ET early close
    "2011-11-25",  # 13:00 ET early close
    "2012-07-03",  # 13:00 ET early close
    "2012-11-23",  # 13:00 ET early close
    "2012-12-24",  # 13:00 ET early close
    "2013-07-03",  # 13:00 ET early close
    "2013-11-29",  # 13:00 ET early close
    "2013-12-24",  # 13:00 ET early close
    "2014-07-03",  # 13:00 ET early close
    "2014-11-28",  # 13:00 ET early close
    "2014-12-24",  # 13:00 ET early close
    "2015-11-27",  # 13:00 ET early close
    "2015-12-24",  # 13:00 ET early close
    "2016-11-25",  # 13:00 ET early close
    "2017-07-03",  # 13:00 ET early close
    "2017-11-24",  # 13:00 ET early close
    "2018-07-03",  # 13:00 ET early close
    "2018-11-23",  # 13:00 ET early close
    "2018-12-24",  # 13:00 ET early close
    "2019-07-03",  # 13:00 ET early close
    "2019-11-29",  # 13:00 ET early close
    "2019-12-24",  # 13:00 ET early close
    "2020-11-27",  # 13:00 ET early close
    "2020-12-24",  # 13:00 ET early close
    "2021-11-26",  # 13:00 ET early close
    "2022-11-25",  # 13:00 ET early close
    "2023-07-03",  # 13:00 ET early close
    "2023-11-24",  # 13:00 ET early close
    "2024-07-03",  # 13:00 ET early close
    "2024-11-29",  # 13:00 ET early close
    "2024-12-24",  # 13:00 ET early close
    "2025-07-03",  # 13:00 ET early close
    "2025-11-28",  # 13:00 ET early close
    "2025-12-24",  # 13:00 ET early close
    "2026-11-27",  # 13:00 ET early close
    "2026-12-24",  # 13:00 ET early close
    "2027-11-26",  # 13:00 ET early close
    "2028-07-03",  # 13:00 ET early close
    "2028-11-24",  # 13:00 ET early close
    "2029-07-03",  # 13:00 ET early close
    "2029-11-23",  # 13:00 ET early close
    "2029-12-24",  # 13:00 ET early close
    "2030-07-03",  # 13:00 ET early close
    "2030-11-29",  # 13:00 ET early close
    "2030-12-24",  # 13:00 ET early close
})

_SPECIAL_CLOSURES: dict[str, str] = {
    "2012-10-29": "HURRICANE_SANDY",
    "2012-10-30": "HURRICANE_SANDY",
    "2018-12-05": "NATIONAL_MOURNING_GHW_BUSH",
    "2025-01-09": "NATIONAL_MOURNING_J_CARTER",
}

_ALL_CLOSURES: frozenset[str] = _HOLIDAYS | frozenset(_SPECIAL_CLOSURES)


def _require_date(value: object, name: str = "day") -> date:
    """Fail closed: accept only real calendar dates (never datetime, never None)."""
    if isinstance(value, datetime):
        raise ValueError(f"{name} must be a datetime.date, not a datetime; convert via .date() in America/New_York first")
    if not isinstance(value, date):
        raise ValueError(f"{name} must be a datetime.date, got {type(value).__name__}")
    return value


def _require_in_table(day: date, name: str = "day") -> date:
    if day < CALENDAR_TABLE_START or day > CALENDAR_TABLE_END:
        raise ValueError(
            f"{name} {day.isoformat()} is outside the frozen table horizon "
            f"[{CALENDAR_TABLE_START.isoformat()}, {CALENDAR_TABLE_END.isoformat()}]; "
            "the calendar fails closed instead of guessing"
        )
    return day


def _et_to_utc(day: date, clock: dt_time) -> datetime:
    return datetime.combine(day, clock, tzinfo=ET_ZONE).astimezone(timezone.utc)


def _require_utc(value: object, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError(f"{name} must be a tz-aware datetime")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class HaltInterval:
    """A declared halt/no-print interval (UTC, half-open ``[start, end)``).

    Declaring a halt only explains missing prints; it never authorizes a
    synthetic fill (see :class:`GapClassification`).
    """

    start_utc: datetime
    end_utc: datetime
    label: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "start_utc", _require_utc(self.start_utc, "start_utc"))
        object.__setattr__(self, "end_utc", _require_utc(self.end_utc, "end_utc"))
        if self.end_utc <= self.start_utc:
            raise ValueError("halt end must be after halt start")
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError("halt label must be a non-empty string")


@dataclass(frozen=True)
class GapClassification:
    """Fail-closed classification of a missing-bar interval.

    ``synthetic_fill_allowed`` is ALWAYS ``False``: overnight gaps are
    returns, not fabricated bars, and halts/no-print intervals fail closed
    with no synthetic fill.  The classification only explains the gap.
    """

    start_utc: datetime
    end_utc: datetime
    status: str
    reason: str
    synthetic_fill_allowed: bool = False

    def __post_init__(self) -> None:
        if self.status not in (GAP_OK_WITH_REASON, GAP_UNEXPLAINED):
            raise ValueError(f"unknown gap status {self.status!r}")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("gap classification requires a non-empty reason")
        if self.synthetic_fill_allowed:
            raise ValueError("synthetic fills are never allowed; fail closed")

    @property
    def ok(self) -> bool:
        return self.status == GAP_OK_WITH_REASON

    @property
    def unexplained(self) -> bool:
        return self.status == GAP_UNEXPLAINED


def assert_no_unexplained_gap(classification: GapClassification) -> GapClassification:
    """Fail closed: raise when a gap is :data:`GAP_UNEXPLAINED`."""
    if classification.unexplained:
        raise ValueError(f"unexplained gap: {classification.reason}")
    return classification


class USEquityRegularCalendar(SessionCalendar):
    """NYSE/Nasdaq regular-session calendar over the frozen 2010-2030 table.

    Pre/post-market exist as explicit flags and are disabled unless the
    caller explicitly enables them at construction; baseline scoring runs
    with both disabled (regular session only).
    """

    def __init__(
        self,
        *,
        pre_market_enabled: bool = False,
        post_market_enabled: bool = False,
    ) -> None:
        self.pre_market_enabled = bool(pre_market_enabled)
        self.post_market_enabled = bool(post_market_enabled)
        self._manifest_digest: str | None = None

    # --- identity ---------------------------------------------------------- #
    @property
    def calendar_id(self) -> str:
        return CALENDAR_ID

    @property
    def table_version(self) -> str:
        return CALENDAR_TABLE_VERSION

    @property
    def enabled_phases(self) -> tuple[str, ...]:
        phases = [PHASE_REGULAR]
        if self.pre_market_enabled:
            phases.insert(0, PHASE_PRE_MARKET)
        if self.post_market_enabled:
            phases.append(PHASE_POST_MARKET)
        return tuple(phases)

    # --- SessionCalendar interface ----------------------------------------- #
    def is_session_day(self, day: date) -> bool:
        _require_date(day)
        _require_in_table(day)
        return day.weekday() < 5 and day.isoformat() not in _ALL_CLOSURES

    def is_session(self, day: date) -> bool:
        """Alias of :meth:`is_session_day`."""
        return self.is_session_day(day)

    def holidays(self, start: date, end: date) -> tuple[date, ...]:
        """Scheduled holidays plus documented unscheduled closures in range."""
        start = _require_in_table(_require_date(start, "start"), "start")
        end = _require_in_table(_require_date(end, "end"), "end")
        if end < start:
            raise ValueError("end date precedes start date")
        return tuple(
            day
            for day in self._days(start, end)
            if day.isoformat() in _ALL_CLOSURES
        )

    def session_bounds(self, day: date) -> Session | None:
        """UTC session bounds for ``day`` (early closes end at 13:00 ET).

        Returns ``None`` on holidays/weekends inside the table horizon and
        raises ``ValueError`` outside the horizon (never guesses).
        """
        day = _require_date(day)
        _require_in_table(day)
        if not self.is_session_day(day):
            return None
        is_early = day.isoformat() in _HALF_DAYS
        close_et = EARLY_CLOSE_ET if is_early else REGULAR_CLOSE_ET
        return Session(
            start_utc=_et_to_utc(day, SESSION_OPEN_ET),
            end_utc=_et_to_utc(day, close_et),
            is_early_close=is_early,
            label=f"{CALENDAR_ID}:{day.isoformat()}",
        )

    def require_session(self, day: date) -> Session:
        """Like :meth:`session_bounds` but fails closed on closed days."""
        session = self.session_bounds(day)
        if session is None:
            raise ValueError(f"{day.isoformat()} is not a regular session day")
        return session

    def early_close_cutoff_utc(self, day: date) -> datetime | None:
        day = _require_date(day)
        _require_in_table(day)
        if not self.is_session_day(day) or day.isoformat() not in _HALF_DAYS:
            return None
        return _et_to_utc(day, EARLY_CLOSE_ET)

    def closure_reason(self, day: date) -> str | None:
        """Why ``day`` has no session: weekday, holiday or special closure."""
        day = _require_date(day)
        _require_in_table(day)
        iso = day.isoformat()
        if iso in _SPECIAL_CLOSURES:
            return f"SPECIAL_CLOSURE:{_SPECIAL_CLOSURES[iso]}"
        if iso in _HOLIDAYS:
            return "SCHEDULED_HOLIDAY"
        if day.weekday() >= 5:
            return "WEEKEND"
        return None

    # --- range helpers ------------------------------------------------------ #
    @staticmethod
    def _days(start: date, end: date) -> Iterable[date]:
        day = start
        while day <= end:
            yield day
            day = day + timedelta(days=1)

    def sessions_in_range(self, start: date, end: date) -> tuple[Session, ...]:
        """Sessions for every session day in ``[start, end]`` (inclusive)."""
        start = _require_in_table(_require_date(start, "start"), "start")
        end = _require_in_table(_require_date(end, "end"), "end")
        if end < start:
            raise ValueError("end date precedes start date")
        return tuple(
            session
            for day in self._days(start, end)
            if (session := self.session_bounds(day)) is not None
        )

    # keep the interface helper aligned with the horizon-checked variant
    sessions_between = sessions_in_range

    def next_session(self, after: date) -> Session:
        """First session strictly after ``after``; fails closed past the table."""
        after = _require_date(after)
        _require_in_table(after, "after")
        day = after + timedelta(days=1)
        while day <= CALENDAR_TABLE_END:
            session = self.session_bounds(day)
            if session is not None:
                return session
            day = day + timedelta(days=1)
        raise ValueError(
            f"no session after {after.isoformat()} within the frozen table horizon"
        )

    def session_count(self, start: date, end: date) -> int:
        return len(self.sessions_in_range(start, end))

    # --- pre/post market (explicit, disabled in baseline scoring) ----------- #
    def phase_bounds(self, day: date, phase: str) -> Session:
        """Bounds for an explicit market phase; fails closed when disabled.

        ``PRE_MARKET`` is 04:00-09:30 ET, ``REGULAR`` is 09:30-close ET,
        ``POST_MARKET`` is 16:00-20:00 ET.  Pre/post are DISABLED in
        baseline scoring and only exist when explicitly enabled at
        construction; asking for a disabled phase raises ``ValueError``.
        """
        session = self.require_session(day)
        if phase == PHASE_REGULAR:
            return session
        if phase == PHASE_PRE_MARKET:
            if not self.pre_market_enabled:
                raise ValueError(
                    "PRE_MARKET phase is disabled; baseline scoring uses the "
                    "regular session only and pre/post must be enabled explicitly"
                )
            return Session(
                start_utc=_et_to_utc(day, PRE_MARKET_OPEN_ET),
                end_utc=session.start_utc,
                is_early_close=False,
                label=f"{CALENDAR_ID}:{day.isoformat()}:PRE",
            )
        if phase == PHASE_POST_MARKET:
            if not self.post_market_enabled:
                raise ValueError(
                    "POST_MARKET phase is disabled; baseline scoring uses the "
                    "regular session only and pre/post must be enabled explicitly"
                )
            return Session(
                start_utc=session.end_utc,
                end_utc=_et_to_utc(day, POST_MARKET_CLOSE_ET),
                is_early_close=False,
                label=f"{CALENDAR_ID}:{day.isoformat()}:POST",
            )
        raise ValueError(f"unknown market phase {phase!r}")

    def assert_baseline_scoring_phases(self) -> None:
        """Fail closed unless pre/post market are disabled (baseline scoring)."""
        if self.pre_market_enabled or self.post_market_enabled:
            raise ValueError(
                "baseline scoring requires pre/post market phases disabled"
            )

    # --- manifests ----------------------------------------------------------- #
    def frozen_table_payload(self) -> dict[str, object]:
        """Canonical-JSON-safe payload of the frozen table (digest input)."""
        return {
            "calendar_id": CALENDAR_ID,
            "table_version": CALENDAR_TABLE_VERSION,
            "table_start": CALENDAR_TABLE_START.isoformat(),
            "table_end": CALENDAR_TABLE_END.isoformat(),
            "session_open_et": SESSION_OPEN_ET.isoformat(),
            "regular_close_et": REGULAR_CLOSE_ET.isoformat(),
            "early_close_et": EARLY_CLOSE_ET.isoformat(),
            "holidays": sorted(_HOLIDAYS),
            "half_days": sorted(_HALF_DAYS),
            "special_closures": {k: _SPECIAL_CLOSURES[k] for k in sorted(_SPECIAL_CLOSURES)},
        }

    def calendar_manifest_digest(self) -> str:
        """sha256 of the frozen table JSON serialized canonically."""
        if self._manifest_digest is None:
            payload = json.dumps(
                self.frozen_table_payload(), sort_keys=True, separators=(",", ":")
            )
            self._manifest_digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return self._manifest_digest

    def slice_payload(self, start: date, end: date) -> dict[str, object]:
        start = _require_in_table(_require_date(start, "start"), "start")
        end = _require_in_table(_require_date(end, "end"), "end")
        if end < start:
            raise ValueError("end date precedes start date")
        sessions: list[str] = []
        holidays: list[str] = []
        half_days: list[str] = []
        for day in self._days(start, end):
            iso = day.isoformat()
            if iso in _ALL_CLOSURES:
                holidays.append(iso)
            elif day.weekday() >= 5:
                pass
            else:
                sessions.append(iso)
                if iso in _HALF_DAYS:
                    half_days.append(iso)
        return {
            "calendar_id": CALENDAR_ID,
            "table_version": CALENDAR_TABLE_VERSION,
            "calendar_manifest_digest": self.calendar_manifest_digest(),
            "slice_start": start.isoformat(),
            "slice_end": end.isoformat(),
            "sessions": sessions,
            "holidays": holidays,
            "half_days": half_days,
        }

    def _slice_digest(self, payload: dict[str, object]) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def monthly_manifest_digest(self, year: int, month: int) -> str:
        """Digest of one calendar month bound to the full-table manifest."""
        import calendar as _calendar

        if not 1 <= month <= 12:
            raise ValueError("month must be in 1..12")
        last_day = _calendar.monthrange(year, month)[1]
        payload = self.slice_payload(date(year, month, 1), date(year, month, last_day))
        return self._slice_digest(payload)

    def annual_manifest_digest(self, year: int) -> str:
        """Digest of one calendar year bound to the full-table manifest."""
        payload = self.slice_payload(date(year, 1, 1), date(year, 12, 31))
        return self._slice_digest(payload)

    # --- gap classification --------------------------------------------------- #
    def classify_gap(
        self,
        start_utc: datetime,
        end_utc: datetime,
        *,
        declared_halts: Sequence[HaltInterval] = (),
    ) -> GapClassification:
        """Classify a missing-bar interval against session bounds.

        ``[start_utc, end_utc)`` is the interval with no bars.  Intervals
        fully outside regular sessions are ``GAP_OK_WITH_REASON``
        (overnight/weekend/holiday gaps are returns, not fabricated bars).
        Intervals intersecting a session are OK only when fully covered by
        a declared :class:`HaltInterval`; otherwise ``GAP_UNEXPLAINED``.
        Halts never authorize a synthetic fill.
        """
        start = _require_utc(start_utc, "start_utc")
        end = _require_utc(end_utc, "end_utc")
        if end < start:
            raise ValueError("gap end precedes gap start")
        halts = tuple(
            h if isinstance(h, HaltInterval) else HaltInterval(*h) for h in declared_halts
        )

        def _ok(reason: str) -> GapClassification:
            return GapClassification(
                start_utc=start, end_utc=end, status=GAP_OK_WITH_REASON, reason=reason
            )

        def _bad(reason: str) -> GapClassification:
            return GapClassification(
                start_utc=start, end_utc=end, status=GAP_UNEXPLAINED, reason=reason
            )

        if end == start:
            return _ok("empty interval; nothing to classify")
        if start.date() < CALENDAR_TABLE_START or end.date() > CALENDAR_TABLE_END:
            return _bad(
                f"gap extends beyond the frozen table horizon "
                f"[{CALENDAR_TABLE_START.isoformat()}, {CALENDAR_TABLE_END.isoformat()}]; "
                "fail closed: no synthetic fill"
            )

        first_day = start.astimezone(ET_ZONE).date()
        last_day = end.astimezone(ET_ZONE).date()
        uncovered: list[tuple[datetime, datetime, str]] = []
        covered_by: dict[str, set[str]] = {}
        overlaps_session = False
        day = first_day
        while day <= last_day:
            session = self.session_bounds(day)
            if session is not None:
                lo = max(session.start_utc, start)
                hi = min(session.end_utc, end)
                if lo < hi:  # half-open interval intersection
                    overlaps_session = True
                    remaining = [(lo, hi)]
                    for halt in halts:
                        nxt: list[tuple[datetime, datetime]] = []
                        for chunk_lo, chunk_hi in remaining:
                            if halt.start_utc <= chunk_lo and chunk_hi <= halt.end_utc:
                                covered_by.setdefault(day.isoformat(), set()).add(halt.label)
                                continue
                            # split off the part covered by this halt
                            inner_lo = max(chunk_lo, halt.start_utc)
                            inner_hi = min(chunk_hi, halt.end_utc)
                            if inner_lo < inner_hi:
                                if chunk_lo < inner_lo:
                                    nxt.append((chunk_lo, inner_lo))
                                if inner_hi < chunk_hi:
                                    nxt.append((inner_hi, chunk_hi))
                            else:
                                nxt.append((chunk_lo, chunk_hi))
                        remaining = nxt
                    for chunk_lo, chunk_hi in remaining:
                        uncovered.append((chunk_lo, chunk_hi, day.isoformat()))
            day = day + timedelta(days=1)

        if uncovered:
            lo, hi, day_iso = uncovered[0]
            return _bad(
                f"missing bars inside regular session {day_iso} "
                f"[{lo.isoformat()}, {hi.isoformat()}) without a fully covering "
                "declared halt; fail closed: no synthetic fill"
            )
        if overlaps_session:
            labels = sorted({lbl for per_day in covered_by.values() for lbl in per_day})
            return _ok(
                "missing prints inside sessions fully covered by declared halt(s) "
                f"{labels}; halt/no-print interval fails closed: no synthetic fill"
            )
        reasons: list[str] = []
        day = first_day
        while day <= last_day:
            reason = self.closure_reason(day)
            if reason is not None:
                reasons.append(f"{day.isoformat()}={reason}")
            day = day + timedelta(days=1)
        detail = "; ".join(reasons) if reasons else "adjacent to session bounds"
        return _ok(
            "interval outside regular sessions (overnight/weekend/holiday gap; "
            f"{detail}); the gap is a return, not a missing bar; no synthetic fill"
        )


US_EQUITY_REGULAR_V1 = USEquityRegularCalendar()

__all__ = [
    "CALENDAR_ID",
    "CALENDAR_TABLE_END",
    "CALENDAR_TABLE_START",
    "CALENDAR_TABLE_VERSION",
    "EARLY_CLOSE_ET",
    "ET_ZONE",
    "GAP_OK_WITH_REASON",
    "GAP_UNEXPLAINED",
    "GapClassification",
    "HaltInterval",
    "NEEDS_PROVIDER_VERIFICATION",
    "PHASE_POST_MARKET",
    "PHASE_PRE_MARKET",
    "PHASE_REGULAR",
    "POST_MARKET_CLOSE_ET",
    "PRE_MARKET_OPEN_ET",
    "REGULAR_CLOSE_ET",
    "SESSION_OPEN_ET",
    "USEquityRegularCalendar",
    "US_EQUITY_REGULAR_V1",
    "assert_no_unexplained_gap",
]
