"""Hand-built synthetic calendars and shared fixtures for the A9 family suite.

OFFLINE and SYNTHETIC only: no real data, no network, no disk writes outside
pytest temporary directories.  The primary hand calendar mirrors two real
19-session US equity months (January and February 2021, with the MLK and
Presidents' Day holidays removed) so the goldens stay close to reality while
remaining fully hand-computable.
"""

from __future__ import annotations

import datetime as dt

import pytest

from research.stocks_free_v3.family_tom_settle import build_arm_configs

# --------------------------------------------------------------------------
# the primary hand calendar: Jan 2021 (19 sessions, MLK 01-18 removed) and
# Feb 2021 (19 sessions, Presidents' Day 02-15 removed)
# --------------------------------------------------------------------------
JAN_2021_SESSIONS = (
    "2021-01-04", "2021-01-05", "2021-01-06", "2021-01-07", "2021-01-08",
    "2021-01-11", "2021-01-12", "2021-01-13", "2021-01-14", "2021-01-15",
    "2021-01-19", "2021-01-20", "2021-01-21", "2021-01-22",
    "2021-01-25", "2021-01-26", "2021-01-27", "2021-01-28", "2021-01-29",
)
FEB_2021_SESSIONS = (
    "2021-02-01", "2021-02-02", "2021-02-03", "2021-02-04", "2021-02-05",
    "2021-02-08", "2021-02-09", "2021-02-10", "2021-02-11", "2021-02-12",
    "2021-02-16", "2021-02-17", "2021-02-18", "2021-02-19",
    "2021-02-22", "2021-02-23", "2021-02-24", "2021-02-25", "2021-02-26",
)
HAND_SESSIONS = JAN_2021_SESSIONS + FEB_2021_SESSIONS

# --------------------------------------------------------------------------
# synthetic padded calendar years: all weekdays are sessions (no holidays)
# --------------------------------------------------------------------------
def weekday_sessions(start: str, end: str) -> tuple[str, ...]:
    d = dt.date.fromisoformat(start)
    last = dt.date.fromisoformat(end)
    out = []
    while d <= last:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return tuple(out)


#: 2021 padded by December 2020 and January 2022 so 2021 is a COMPLETE year
#: (establishment outside 2021; December window entry inside; exit in 2022).
PADDED_YEAR_2021 = weekday_sessions("2020-11-16", "2022-01-14")


@pytest.fixture(scope="session")
def arm_configs():
    return build_arm_configs()


@pytest.fixture(scope="session")
def hand_sessions():
    return HAND_SESSIONS


@pytest.fixture(scope="session")
def padded_year_sessions():
    return PADDED_YEAR_2021
