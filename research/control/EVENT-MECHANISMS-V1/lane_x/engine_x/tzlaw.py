"""R2-4 timezone law: ET conversion, clock strata, weekend bucketing.

Strata (half-open, America/New_York market clock):
    S1 pre-open    [00:00, 09:30)
    S2 in-session  [09:30, 16:00)
    S3 after-close [16:00, 20:00)
    S4 late        [20:00, 24:00)

Weekend acceptances carry their clock stratum but are flagged into the
separate weekend bucket (G3: "weekend bucket separate"; S7 fixture c).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

SESSION_OPEN = time(9, 30)
SESSION_CLOSE = time(16, 0)

STRATUM_S1 = "S1"
STRATUM_S2 = "S2"
STRATUM_S3 = "S3"
STRATUM_S4 = "S4"


@dataclass(frozen=True)
class ClockFacts:
    et_local: str            # ISO-8601 with ET offset, e.g. 2024-06-10T18:30:00-04:00
    et_offset_hours: int     # -4 EDT / -5 EST
    et_date: str             # ET-local calendar date, YYYY-MM-DD
    weekday: str
    is_weekend: bool
    weekend_bucket: bool
    stratum: str             # S1..S4 by ET clock, regardless of weekend


def parse_acceptance(acceptance_utc: str) -> datetime:
    """Parse a staged acceptance instant (Z-suffixed UTC)."""
    txt = acceptance_utc.strip()
    if txt.endswith("Z"):
        txt = txt[:-1] + "+00:00"
    dt = datetime.fromisoformat(txt)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def clock_facts(acceptance_utc: str) -> ClockFacts:
    inst = parse_acceptance(acceptance_utc)
    local = inst.astimezone(ET)
    minutes = local.hour * 60 + local.minute
    if minutes < 9 * 60 + 30:
        stratum = STRATUM_S1
    elif minutes < 16 * 60:
        stratum = STRATUM_S2
    elif minutes < 20 * 60:
        stratum = STRATUM_S3
    else:
        stratum = STRATUM_S4
    is_weekend = local.weekday() >= 5
    return ClockFacts(
        et_local=local.isoformat(),
        et_offset_hours=int(local.utcoffset().total_seconds() // 3600),
        et_date=local.date().isoformat(),
        weekday=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                 "Saturday", "Sunday"][local.weekday()],
        is_weekend=is_weekend,
        weekend_bucket=is_weekend,
        stratum=stratum,
    )


def session_close_instant(date_str: str) -> datetime:
    """Aware instant of the 16:00 ET regular close on a session date."""
    y, m, d = int(date_str[0:4]), int(date_str[5:7]), int(date_str[8:10])
    return datetime(y, m, d, 16, 0, tzinfo=ET)


def session_open_instant(date_str: str) -> datetime:
    """Aware instant of the 09:30 ET regular open on a session date."""
    y, m, d = int(date_str[0:4]), int(date_str[5:7]), int(date_str[8:10])
    return datetime(y, m, d, 9, 30, tzinfo=ET)
