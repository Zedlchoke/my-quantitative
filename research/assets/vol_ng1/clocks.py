"""VOL-NG1 P1 clock identity: daily close decision grid (plan section 5).

Laws inherited from the program clock identity (V7) and the FOREX-NG1
P1 16:00-NY grid precedent:

- the decision grid is DAILY and bar-readable: its sessions are the
  actual bar dates of the consumed series, so weekends and holidays
  can never be selected (fail-closed, nothing inferred);
- close instant: 16:00 America/New_York on the session date, converted
  to UTC -- the conversion MUST run through the real timezone database
  so DST transitions are measured, not assumed;
- V7 close+1 law: a decision observed at the close of session t is
  executable at the NEXT grid session (t+1 in grid order).  A decision
  date not on the grid, or a decision on the last grid session (no
  next bar readable yet), is ClockRefused -- never silently mapped to
  the same bar.

No proposals, no signals, no scoring, no outcome numbers anywhere.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

SCHEMA = "vol_ng1/clocks@1"

#: The decision-grid close (US equity/EOD convention for these legs).
CLOSE_TIME_NY = time(16, 0)

#: Measured DST boundary facts for the fixture suite (US 2007 rule:
#: second Sunday in March, first Sunday in November).
DST_BOUNDARY_SESSIONS = {
    # EST (UTC-5): 16:00 NY == 21:00 UTC
    "est_midwinter": "2026-01-15",
    # spring forward 2026-03-08: 16:00 NY on the FIRST EDT session after
    # the transition == 20:00 UTC
    "edt_after_spring_forward": "2026-03-09",
    # EDT (UTC-4): 16:00 NY == 20:00 UTC
    "edt_midsummer": "2026-07-15",
    # fall back 2026-11-01: 16:00 NY on the FIRST EST session after the
    # transition == 21:00 UTC
    "est_after_fall_back": "2026-11-02",
}

_HAND_COMPUTED_UTC = {
    "2026-01-15": "2026-01-15T21:00:00+00:00",
    "2026-03-09": "2026-03-09T20:00:00+00:00",
    "2026-07-15": "2026-07-15T20:00:00+00:00",
    "2026-11-02": "2026-11-02T21:00:00+00:00",
}


class ClockError(Exception):
    """Fail-closed clock violation: off-grid date, empty grid, or no
    next readable bar.  Never silently mapped."""


def ny_close_utc(session: str | date) -> datetime:
    """The 16:00 America/New_York close instant of ``session`` as an
    aware UTC datetime (measured through the timezone database)."""
    d = session if isinstance(session, date) \
        else date.fromisoformat(str(session))
    aware = datetime.combine(d, CLOSE_TIME_NY, tzinfo=ZoneInfo("America/New_York"))
    return aware.astimezone(timezone.utc)


def decision_grid(bar_dates) -> list[str]:
    """Sorted unique ISO-date grid from actual bar dates (bar-readable:
    only sessions that really have bars exist here)."""
    dates = sorted({str(d) for d in bar_dates})
    if not dates:
        raise ClockError("decision grid from zero bar dates: refused")
    for d in dates:
        date.fromisoformat(d)  # strict ISO parse or fail
    return dates


def require_on_grid(grid: list[str], session: str) -> int:
    """Index of ``session`` in ``grid`` (fail-closed)."""
    try:
        return grid.index(str(session))
    except ValueError as exc:
        raise ClockError(
            f"session {session!r} is not on the bar-readable grid: "
            "off-grid decisions are refused (V7)") from exc


def next_session(grid: list[str], session: str) -> str:
    """V7 close+1: the executable session after ``session``'s close."""
    i = require_on_grid(grid, session)
    if i + 1 >= len(grid):
        raise ClockError(
            f"no next readable bar after {session!r} (last grid "
            f"session): close+1 is NOT_RUN, never same-bar")
    return grid[i + 1]


def close_instant(session: str | date) -> str:
    """ISO-UTC string of the session close (decision-grid instant)."""
    return ny_close_utc(session).isoformat()


def dst_boundary_report() -> dict:
    """Measured 16:00-NY -> UTC conversions at the four boundary
    sessions + the hand-computed expectations (fixture law)."""
    rows = {}
    for label, d in DST_BOUNDARY_SESSIONS.items():
        got = close_instant(d)
        rows[label] = {
            "session": d,
            "close_utc": got,
            "expected_utc": _HAND_COMPUTED_UTC[d],
            "match": got == _HAND_COMPUTED_UTC[d],
        }
    return {
        "schema": SCHEMA,
        "timezone": "America/New_York",
        "close_time": CLOSE_TIME_NY.isoformat(),
        "boundaries": rows,
        "all_match": all(r["match"] for r in rows.values()),
    }
