"""R2-4 timezone law: ET strata via zoneinfo, DST-safe; session instants.

A session date = a date on which the name has a bar (R2-4); a session's
close occurs at 16:00 ET of that bar date; open at 09:30 ET.
"""
from __future__ import annotations

from datetime import datetime, date, time, timedelta
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

from . import config as C

ET = ZoneInfo(C.ET_TZ)


def parse_acceptance_utc(s: str) -> datetime:
    """'2019-07-27T01:30:16.000Z' -> aware UTC datetime."""
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=ZoneInfo("UTC"))


def to_et(utc_dt: datetime) -> Tuple[datetime, float]:
    """Convert to America/New_York; return (et_datetime, utcoffset_hours)."""
    et = utc_dt.astimezone(ET)
    off = et.utcoffset().total_seconds() / 3600.0
    return et, off


def stratum_of(et_dt: datetime) -> Tuple[str, bool]:
    """Clock stratum S1..S4 + separate weekend flag (never collapsed, S7-c)."""
    minutes = et_dt.hour * 60 + et_dt.minute
    stratum = "S4"
    for name, lo, hi in C.STRATA_BOUNDS:
        if lo <= minutes < hi:
            stratum = name
            break
    is_weekend = et_dt.weekday() >= 5  # 5=Sat, 6=Sun (ET local date)
    return stratum, is_weekend


def session_close_instant(d: date) -> datetime:
    return datetime.combine(d, time(16, 0), tzinfo=ET)


def session_open_instant(d: date) -> datetime:
    return datetime.combine(d, time(9, 30), tzinfo=ET)


def date_of(s: str) -> date:
    return date.fromisoformat(s)


def fold_of(acceptance_utc: str) -> str:
    d = acceptance_utc[:10]
    for name, lo, hi in C.FOLDS:
        if lo <= d < hi:
            return name
    return "OUTSIDE"


# DST boundary dates (second Sunday March / first Sunday November) used by
# the spring-forward / fall-back fixtures.
def us_dst_boundaries(year: int) -> Tuple[str, str]:
    march1 = date(year, 3, 1)
    spring = march1 + timedelta(days=(6 - march1.weekday()) % 7 + 7)  # 2nd Sunday
    nov1 = date(year, 11, 1)
    fall = nov1 + timedelta(days=(6 - nov1.weekday()) % 7)            # 1st Sunday
    return spring.isoformat(), fall.isoformat()
