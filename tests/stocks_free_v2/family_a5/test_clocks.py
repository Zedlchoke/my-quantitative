"""Calendar-golden tests: MONTHLY and WEEKLY clocks derived from the frozen
US_EQUITY_REGULAR_V1 calendar (imported READ-ONLY; A4 owns that module)."""

from datetime import date


def test_monthly_clock_golden_jan_apr_2018(a5, real_calendar):
    # Hand golden: last completed regular session per calendar month.
    # March 2018: Good Friday 2018-03-30 is a frozen holiday closure, so
    # March's last completed session is Thursday 2018-03-29.
    sessions = [s.start_utc.date() for s in real_calendar.sessions_in_range(date(2018, 1, 1), date(2018, 4, 30))]
    assert a5.schedule.decision_dates_monthly(sessions) == [
        date(2018, 1, 31),  # Wednesday
        date(2018, 2, 28),  # Wednesday
        date(2018, 3, 29),  # Thursday — 03-30 is Good Friday (frozen table)
        date(2018, 4, 30),  # Monday
    ]


def test_monthly_clock_golden_year_boundary(a5, real_calendar):
    # 2018-12-31 is a regular session (the 2018-12-05 national day of mourning
    # closure is mid-month and does not affect the month-end date).
    sessions = [s.start_utc.date() for s in real_calendar.sessions_in_range(date(2018, 12, 1), date(2019, 1, 31))]
    assert a5.schedule.decision_dates_monthly(sessions) == [date(2018, 12, 31), date(2019, 1, 31)]


def test_weekly_clock_golden_iso_weeks_jan_feb_2018(a5, real_calendar):
    # Hand golden: last completed session per ISO week.
    # ISO 2018-W05 spans Mon Jan 29 .. Sun Feb 4, so its decision lands in
    # FEBRUARY (Fri 2018-02-02) even though the week starts in January —
    # proving ISO-week grouping, not calendar-month grouping.
    # W3 (Jan 15-21): MLK Day Mon Jan 15 is a frozen holiday -> decision Jan 19.
    # Range ends Fri 2018-02-16 so the final ISO week (W07) is complete.
    sessions = [s.start_utc.date() for s in real_calendar.sessions_in_range(date(2018, 1, 1), date(2018, 2, 16))]
    assert a5.schedule.decision_dates_weekly(sessions) == [
        date(2018, 1, 5),
        date(2018, 1, 12),
        date(2018, 1, 19),  # W3: Jan 15 closed (Martin Luther King Jr. Day)
        date(2018, 1, 26),
        date(2018, 2, 2),  # W5 spills across the month boundary
        date(2018, 2, 9),
        date(2018, 2, 16),
    ]


def test_clock_dispatch_matches_config(a5, real_calendar):
    # The frozen MONTHLY arm uses month-ends; the frozen WEEKLY arm ISO weeks.
    s = a5.schedule
    sessions = [x.start_utc.date() for x in real_calendar.sessions_in_range(date(2018, 1, 1), date(2018, 1, 31))]
    assert s.decision_dates_for(s.ARM_CONFIG_ANCHOR, sessions) == [date(2018, 1, 31)]
    # Synthetic holiday-free January: ISO weeks ending 01-05, 01-12, 01-19, 01-26, 01-31
    assert s.decision_dates_for(s.ARM_CONFIG_NEIGHBOUR, sessions) == [
        date(2018, 1, 5),
        date(2018, 1, 12),
        date(2018, 1, 19),
        date(2018, 1, 26),
        date(2018, 1, 31),
    ]
