"""Golden tests: month ordinals on synthetic (holiday-thinned) calendars.

Deliverable 1a + 3: regular-session month ordinals must count SESSIONS, never
calendar dates, so holiday-thinned months are handled with no special cases;
fail-closed on malformed calendars.
"""

from __future__ import annotations

import pytest

from research.stocks_free_v3.family_tom_settle import (
    MIN_MONTH_SESSIONS,
    ScheduleError,
    SessionOrdinal,
    month_ordinals,
    sessions_by_month,
)

from tests.stocks_free_v3.family_tom_settle.conftest import (
    FEB_2021_SESSIONS,
    HAND_SESSIONS,
    JAN_2021_SESSIONS,
    PADDED_YEAR_2021,
)


def test_ordinals_count_sessions_not_dates():
    ords = month_ordinals(HAND_SESSIONS)
    by_session = {r.session: r for r in ords}
    # January 2021: 19 regular sessions (2021-01-18 MLK holiday has no
    # session and NO GAP in the ordinals): 01-15 is ordinal 10, the next
    # session 01-19 is ordinal 11.
    assert by_session["2021-01-15"] == SessionOrdinal("2021-01-15", "2021-01", 10, 19)
    assert by_session["2021-01-19"] == SessionOrdinal("2021-01-19", "2021-01", 11, 19)
    assert by_session["2021-01-04"] == SessionOrdinal("2021-01-04", "2021-01", 1, 19)
    assert by_session["2021-01-29"] == SessionOrdinal("2021-01-29", "2021-01", 19, 19)
    # February 2021: 19 sessions; 02-12 is ordinal 10, 02-16 (Presidents'
    # Day 02-15 removed) is ordinal 11; the month is 19 sessions long, so the
    # month-END tail ordinals resolve from 19, not from the calendar date.
    assert by_session["2021-02-12"] == SessionOrdinal("2021-02-12", "2021-02", 10, 19)
    assert by_session["2021-02-16"] == SessionOrdinal("2021-02-16", "2021-02", 11, 19)
    assert by_session["2021-02-26"] == SessionOrdinal("2021-02-26", "2021-02", 19, 19)


def test_ordinals_hand_count_for_a_full_synthetic_year():
    ords = month_ordinals(PADDED_YEAR_2021)
    by_month = sessions_by_month(PADDED_YEAR_2021)
    # December 2020: all weekdays; Dec 2020 has 23 weekdays (Dec 25 is a
    # Friday in 2020 but this synthetic calendar keeps all weekdays).
    assert len(by_month["2020-12"]) == 23
    assert len(by_month["2021-04"]) == 22  # April 2021 has 22 weekdays
    # first session of the coverage is ordinal 1 of its month
    assert ords[0] == SessionOrdinal(PADDED_YEAR_2021[0], PADDED_YEAR_2021[0][:7], 1,
                                     len(by_month[PADDED_YEAR_2021[0][:7]]))
    # ordinals restart at 1 at every month boundary
    seen_month = None
    for r in ords:
        if r.month != seen_month:
            assert r.ordinal == 1
            seen_month = r.month
        assert 1 <= r.ordinal <= r.month_length
        assert r.session == PADDED_YEAR_2021[_index_of(PADDED_YEAR_2021, r.session)]


def _index_of(sessions, session):
    return list(sessions).index(session)


def test_every_hand_month_has_the_expected_length():
    ords = month_ordinals(JAN_2021_SESSIONS + FEB_2021_SESSIONS)
    assert {r.month for r in ords} == {"2021-01", "2021-02"}
    assert all(r.month_length == 19 for r in ords)


def test_fail_closed_empty_sessions():
    with pytest.raises(ScheduleError):
        month_ordinals([])


def test_fail_closed_unsorted_or_duplicate():
    with pytest.raises(ScheduleError):
        month_ordinals(list(JAN_2021_SESSIONS[:5]) + [JAN_2021_SESSIONS[2]])
    with pytest.raises(ScheduleError):
        month_ordinals(list(reversed(JAN_2021_SESSIONS)))


def test_fail_closed_non_iso_strings():
    with pytest.raises(ScheduleError):
        month_ordinals(["20210104", "20210105", "20210106", "20210107",
                        "20210108", "20210111", "20210112", "20210113"])


def test_fail_closed_month_below_frozen_minimum():
    short = [f"2021-03-0{d}" for d in range(1, MIN_MONTH_SESSIONS)]  # 7 sessions
    with pytest.raises(ScheduleError):
        month_ordinals(short)


def test_exactly_minimum_month_is_accepted():
    sessions = [f"2021-03-{d:02d}" for d in range(1, 9)]  # 8 sessions
    ords = month_ordinals(sessions)
    assert len(ords) == 8
    assert all(r.month_length == 8 for r in ords)
