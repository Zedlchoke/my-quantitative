"""Double-generation equality: two code paths, byte-identical schedules.

Deliverable 2: the schedule is built TWICE — once by the session walk
(:func:`build_schedule`) and once from window blocks
(:func:`build_schedule_from_windows`) — and the canonical JSON payloads must
be byte-identical (same fills, same order, same target dicts, same turnover
floats, same digests) on every arm and on several synthetic calendars,
including holiday-thinned months and coverage boundaries.
"""

from __future__ import annotations

import pytest

from research.stocks_free_v3.family_tom_settle import (
    build_schedule,
    build_schedule_from_windows,
    schedules_equal,
)
from tests.stocks_free_v3.family_tom_settle.conftest import (
    HAND_SESSIONS,
    PADDED_YEAR_2021,
    weekday_sessions,
)

ARMS = ("A", "N", "C")


def _iter_days(start: str, end: str):
    import datetime as dt
    d = dt.date.fromisoformat(start)
    last = dt.date.fromisoformat(end)
    while d <= last:
        yield d
        d += dt.timedelta(days=1)


#: deterministic pseudo-random holidays removed from a 2021-2023 weekday grid
#: (fixed arithmetic -> fixed calendar; exercises heavily thinned months).
_FIXED_HOLIDAYS = frozenset(
    d.isoformat()
    for d in _iter_days("2021-01-01", "2023-12-31")
    if (d.day * d.month + d.year) % 29 == 0
)


def _thinned_calendar(min_month_sessions: int = 8) -> tuple[str, ...]:
    """Weekday grid minus the fixed holiday set, dropping months below minimum."""
    by_month: dict[str, list[str]] = {}
    for d in _iter_days("2021-01-01", "2023-12-31"):
        if d.weekday() >= 5 or d.isoformat() in _FIXED_HOLIDAYS:
            continue
        by_month.setdefault(d.isoformat()[:7], []).append(d.isoformat())
    out: list[str] = []
    for month in sorted(by_month):
        if len(by_month[month]) >= min_month_sessions:
            out.extend(by_month[month])
    return tuple(out)


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("calendar", [HAND_SESSIONS, PADDED_YEAR_2021],
                         ids=["hand_months", "padded_year"])
def test_two_paths_byte_identical(arm_configs, arm, calendar):
    s1 = build_schedule(arm_configs[arm], calendar)
    s2 = build_schedule_from_windows(arm_configs[arm], calendar)
    assert s1.canonical_json() == s2.canonical_json()
    assert schedules_equal(s1, s2)
    assert s1.schedule_digest == s2.schedule_digest
    assert s1.window_sessions == s2.window_sessions
    assert s1.fills == s2.fills


@pytest.mark.parametrize("arm", ARMS)
def test_two_paths_byte_identical_on_thinned_multiyear_calendar(arm_configs, arm):
    calendar = _thinned_calendar()
    # the synthetic thinned calendar must really be irregular
    lengths = {}
    for s in calendar:
        lengths[s[:7]] = lengths.get(s[:7], 0) + 1
    assert min(lengths.values()) >= 8 and len(lengths) > 24
    s1 = build_schedule(arm_configs[arm], calendar)
    s2 = build_schedule_from_windows(arm_configs[arm], calendar)
    assert s1.canonical_json() == s2.canonical_json()


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("start,end", [
    ("2021-01-04", "2021-02-26"),   # starts inside an arm-A window
    ("2021-01-11", "2021-01-29"),   # short interior slice (one partial month)
    ("2021-01-13", "2021-02-18"),   # starts/ends on control-window sessions
    ("2021-01-27", "2021-02-02"),   # too short for the frozen month minimum
])
def test_two_paths_byte_identical_on_slices(arm_configs, arm, start, end):
    from research.stocks_free_v3.family_tom_settle import MIN_MONTH_SESSIONS
    calendar = [s for s in PADDED_YEAR_2021 if start <= s <= end]
    per_month: dict[str, int] = {}
    for s in calendar:
        per_month[s[:7]] = per_month.get(s[:7], 0) + 1
    if min(per_month.values()) < MIN_MONTH_SESSIONS:
        # a partial month below the frozen minimum cannot carry a schedule
        pytest.skip("slice month below the frozen month minimum")
    s1 = build_schedule(arm_configs[arm], calendar)
    s2 = build_schedule_from_windows(arm_configs[arm], calendar)
    assert s1.canonical_json() == s2.canonical_json()


def test_double_generation_holds_for_all_arms_on_realistic_synthetic_years(arm_configs):
    for year_start, year_end in (("2019-01-01", "2020-02-15"),
                                 ("2020-11-16", "2022-01-14"),
                                 ("2022-06-01", "2023-07-15")):
        calendar = weekday_sessions(year_start, year_end)
        for arm in ARMS:
            s1 = build_schedule(arm_configs[arm], calendar)
            s2 = build_schedule_from_windows(arm_configs[arm], calendar)
            assert s1.canonical_json() == s2.canonical_json(), (arm, year_start)
