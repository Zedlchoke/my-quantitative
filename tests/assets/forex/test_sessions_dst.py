"""Hand-computed goldens for the FX session/DST/rollover clocks (A4).

Gate: ``FX1_SESSION_DST_PASS`` (PLAN_forex.md section 15, row FX1_SESSION_DST_PASS).

Every golden below was computed BY HAND from the US/EU DST rules (US: DST
begins the second Sunday in March and ends the first Sunday in November at
02:00 local; EU: last Sundays of March and October at 01:00 UTC) and then
cross-checked against ``zoneinfo`` truth in-test.  Holiday tables here are
explicitly SYNTHETIC_TEST_ONLY: they prove calendar mechanics, they are not
an authoritative holiday source.

Golden UTC stamps used repeatedly (America/New_York):

* EST is UTC-5, EDT is UTC-4; US spring-forward 2026-03-08 07:00:00Z,
  US fall-back 2026-11-01 06:00:00Z; UK spring 2026-03-29 01:00:00Z,
  UK fall 2026-10-25 01:00:00Z.
* 17:00 ET rollover: Fri 2026-03-06 (EST) = 22:00:00Z;
  Mon 2026-03-09 (EDT) = 21:00:00Z.
* 16:00 ET Friday close: 2026-03-06 (EST) = 21:00:00Z;
  2026-03-13 (EDT) = 20:00:00Z — one hour earlier after spring-forward.
* Weekly open Sun 21:00 ET: 2026-03-08 (EDT) = 2026-03-09 01:00:00Z;
  2026-03-01 (EST) = 2026-03-02 02:00:00Z.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from research.assets.forex import sessions as fx
from research.assets.forex.calendar import (
    FxHolidayEntry,
    FxHolidayTable,
    FxSessionCalendar,
    MacroEvent,
    SYNTHETIC_TEST_ONLY,
)

UTC = timezone.utc

CONVENTION = fx.DEFAULT_FX_WEEK_CONVENTION


def utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=UTC)


def assert_matches_zoneinfo(local_wall: datetime, zone_name: str, expected_utc: datetime) -> None:
    """Independent zoneinfo truth: local wall time -> UTC must equal the golden."""
    zoned = local_wall.replace(tzinfo=ZoneInfo(zone_name))
    assert zoned.astimezone(UTC) == expected_utc


# --- (a) US spring-forward week (March 2026) -------------------------------- #
def test_us_spring_forward_shifts_new_york_label_by_one_hour() -> None:
    # Hand-computed: Thu 2026-03-05 is EST (UTC-5): 08:00 -> 13:00Z, 17:00 -> 22:00Z.
    # Tue 2026-03-10 is EDT (UTC-4): 08:00 -> 12:00Z, 17:00 -> 21:00Z.
    start_est, end_est = fx.NEW_YORK_SESSION.interval_utc(date(2026, 3, 5))
    assert (start_est, end_est) == (utc(2026, 3, 5, 13), utc(2026, 3, 5, 22))
    start_edt, end_edt = fx.NEW_YORK_SESSION.interval_utc(date(2026, 3, 10))
    assert (start_edt, end_edt) == (utc(2026, 3, 10, 12), utc(2026, 3, 10, 21))
    # Same local wall times land exactly one hour earlier in UTC after the jump.
    assert (start_est.hour - start_edt.hour, end_est.hour - end_edt.hour) == (1, 1)
    # Cross-check against zoneinfo truth (never fixed offsets).
    assert_matches_zoneinfo(datetime(2026, 3, 5, 8), "America/New_York", start_est)
    assert_matches_zoneinfo(datetime(2026, 3, 10, 8), "America/New_York", start_edt)
    assert_matches_zoneinfo(datetime(2026, 3, 10, 17), "America/New_York", end_edt)


def test_us_spring_forward_rollover_and_close_goldens() -> None:
    # Hand-computed: 17:00 ET rollover is 22:00Z in EST, 21:00Z in EDT.
    assert fx.rollover_instant_utc(date(2026, 3, 6), CONVENTION) == utc(2026, 3, 6, 22)
    assert fx.rollover_instant_utc(date(2026, 3, 9), CONVENTION) == utc(2026, 3, 9, 21)
    # The Friday 16:00 ET close moves 21:00Z (before) -> 20:00Z (after) the
    # 2026-03-08 transition.
    assert fx.weekly_close_utc(date(2026, 3, 1), CONVENTION) == utc(2026, 3, 6, 21)
    assert fx.weekly_close_utc(date(2026, 3, 8), CONVENTION) == utc(2026, 3, 13, 20)
    # Weekly open Sun 21:00 ET: 2026-03-02 02:00Z (EST week), 2026-03-09 01:00Z (EDT week).
    assert fx.weekly_open_utc(date(2026, 3, 1), CONVENTION) == utc(2026, 3, 2, 2)
    assert fx.weekly_open_utc(date(2026, 3, 8), CONVENTION) == utc(2026, 3, 9, 1)
    assert_matches_zoneinfo(datetime(2026, 3, 6, 17), "America/New_York", utc(2026, 3, 6, 22))
    assert_matches_zoneinfo(datetime(2026, 3, 9, 17), "America/New_York", utc(2026, 3, 9, 21))


def test_spring_forward_weekend_open_survives_transition_sunday() -> None:
    # The Sunday-open wall time (21:00) sits AFTER the 02:00 local transition,
    # so the open of the transition week is already EDT: Mon 2026-03-09 01:00Z.
    assert fx.weekly_open_utc(date(2026, 3, 8), CONVENTION) == utc(2026, 3, 9, 1)
    assert fx.is_market_open(utc(2026, 3, 9, 1), CONVENTION)
    assert not fx.is_market_open(utc(2026, 3, 9, 0, 59), CONVENTION)


def test_nonexistent_wall_time_fails_closed() -> None:
    # 2026-03-08 02:30 America/New_York does not exist (spring-forward gap).
    with pytest.raises(ValueError, match="does not exist"):
        fx.local_wall_to_utc("America/New_York", datetime(2026, 3, 8, 2, 30))
    # Ambiguous fall-back wall time resolves by fold (2026-11-01 01:30 EDT/EST).
    early = fx.local_wall_to_utc("America/New_York", datetime(2026, 11, 1, 1, 30), fold=0)
    late = fx.local_wall_to_utc("America/New_York", datetime(2026, 11, 1, 1, 30), fold=1)
    assert (late - early) == timedelta(hours=1)


# --- (b) UK/US DST disagreement weeks ---------------------------------------- #
def test_late_march_london_on_gmt_while_new_york_on_edt() -> None:
    # Hand-computed: between 2026-03-08 (US spring) and 2026-03-29 (EU spring)
    # London is still GMT (+0) while New York is EDT (-4).
    ldn = fx.LONDON_SESSION.interval_utc(date(2026, 3, 10))
    ny = fx.NEW_YORK_SESSION.interval_utc(date(2026, 3, 10))
    assert ldn == (utc(2026, 3, 10, 8), utc(2026, 3, 10, 17))
    assert ny == (utc(2026, 3, 10, 12), utc(2026, 3, 10, 21))
    assert_matches_zoneinfo(datetime(2026, 3, 10, 8), "Europe/London", ldn[0])
    assert_matches_zoneinfo(datetime(2026, 3, 10, 8), "America/New_York", ny[0])
    # After 2026-03-29 London is BST (+1): 08:00 -> 07:00Z.
    assert fx.LONDON_SESSION.interval_utc(date(2026, 3, 31)) == (
        utc(2026, 3, 31, 7),
        utc(2026, 3, 31, 16),
    )


def test_october_2026_europe_falls_back_before_us() -> None:
    # Hand-computed: EU falls back 2026-10-25, the US only on 2026-11-01, so in
    # the week of Mon 2026-10-26 London is GMT while New York is still EDT.
    week_open_day = date(2026, 10, 25)
    cal = FxSessionCalendar(calendar_id="FX_G10_SPOT_SYNTHETIC_TEST_ONLY_OCT26")
    assert cal.weekly_open_utc(week_open_day) == utc(2026, 10, 26, 1)  # Sun 21:00 EDT
    assert cal.weekly_close_utc(week_open_day) == utc(2026, 10, 30, 20)  # Fri 16:00 EDT
    labels = {interval.label: interval for interval in cal.labeled_sessions(date(2026, 10, 27))}
    assert labels["LONDON"].start_utc == utc(2026, 10, 27, 8)  # GMT +0
    assert labels["LONDON"].end_utc == utc(2026, 10, 27, 17)
    assert labels["NEW_YORK"].start_utc == utc(2026, 10, 27, 12)  # EDT -4
    assert labels["NEW_YORK"].end_utc == utc(2026, 10, 27, 21)
    assert_matches_zoneinfo(datetime(2026, 10, 27, 8), "Europe/London", utc(2026, 10, 27, 8))
    assert_matches_zoneinfo(datetime(2026, 10, 27, 8), "America/New_York", utc(2026, 10, 27, 12))
    # Session bounds stay inside the weekly window in UTC even as zones disagree.
    bounds = cal.session_bounds(date(2026, 10, 27))
    assert bounds is not None
    assert bounds.start_utc == utc(2026, 10, 26, 21)  # Mon 17:00 EDT rollover
    assert bounds.end_utc == utc(2026, 10, 27, 21)  # Tue 17:00 EDT rollover


def test_dst_transition_instants_and_stress_windows_exact() -> None:
    # Hand-computed instants, located by bisection against zoneinfo truth.
    (ny_spring,) = fx.dst_transitions_utc(fx.NEW_YORK_ZONE, date(2026, 3, 1), date(2026, 3, 31))
    assert ny_spring.instant_utc == utc(2026, 3, 8, 7)
    assert (ny_spring.offset_before, ny_spring.offset_after) == (
        timedelta(hours=-5),
        timedelta(hours=-4),
    )
    (ldn_fall,) = fx.dst_transitions_utc(fx.LONDON_ZONE, date(2026, 10, 20), date(2026, 10, 31))
    assert ldn_fall.instant_utc == utc(2026, 10, 25, 1)
    assert (ldn_fall.offset_before, ldn_fall.offset_after) == (
        timedelta(hours=1),
        timedelta(hours=0),
    )
    (ny_fall,) = fx.dst_transitions_utc(fx.NEW_YORK_ZONE, date(2026, 10, 25), date(2026, 11, 10))
    assert ny_fall.instant_utc == utc(2026, 11, 1, 6)
    windows = fx.dst_stress_windows_utc(
        fx.NEW_YORK_ZONE, date(2026, 3, 1), date(2026, 3, 31), hours_before=2, hours_after=2
    )
    assert windows == ((utc(2026, 3, 8, 5), utc(2026, 3, 8, 9)),)
    both = fx.dst_transitions_utc(fx.NEW_YORK_ZONE, date(2026, 1, 1), date(2026, 12, 31))
    assert [t.instant_utc for t in both] == [utc(2026, 3, 8, 7), utc(2026, 11, 1, 6)]


# --- (c) weekend gap: no fabricated sessions --------------------------------- #
def test_weekend_gap_contains_no_fabricated_sessions() -> None:
    # Gap between Fri 2026-03-06 21:00Z close (16:00 EST) and the next weekly
    # open Mon 2026-03-09 01:00Z (Sun 21:00 EDT).
    gap_start, gap_end = utc(2026, 3, 6, 21), utc(2026, 3, 9, 1)
    week_before = fx.sessions_for_trading_week(date(2026, 3, 1), CONVENTION)
    week_after = fx.sessions_for_trading_week(date(2026, 3, 8), CONVENTION)
    assert week_before and week_after  # both weeks carry real sessions
    for interval in week_before + week_after:
        assert not interval.overlaps(gap_start, gap_end), (
            f"fabricated session {interval} inside the weekend gap"
        )
    cal = FxSessionCalendar(calendar_id="FX_G10_SPOT_SYNTHETIC_TEST_ONLY_WEEKEND")
    assert cal.is_session_day(date(2026, 3, 7)) is False  # Saturday
    assert cal.is_session_day(date(2026, 3, 8)) is False  # Sunday (open belongs to Monday)
    assert cal.session_bounds(date(2026, 3, 7)) is None
    assert cal.labeled_sessions(date(2026, 3, 7)) == ()
    assert cal.sessions_between(date(2026, 3, 7), date(2026, 3, 8)) == ()
    # Friday itself has one session whose end is exactly the weekly close.
    sessions_friday = cal.sessions_between(date(2026, 3, 6), date(2026, 3, 6))
    assert len(sessions_friday) == 1
    assert sessions_friday[0].end_utc == utc(2026, 3, 6, 21)
    for interval in cal.sessions_between(date(2026, 3, 6), date(2026, 3, 9)):
        assert not (
            interval.start_utc < gap_end and gap_start < interval.end_utc
        ), f"fabricated session {interval} inside the weekend gap"


def test_is_market_open_weekly_window_half_open() -> None:
    assert fx.is_market_open(utc(2026, 3, 9, 1), CONVENTION)  # Sun 21:00 EDT open (inclusive)
    assert not fx.is_market_open(utc(2026, 3, 9, 0, 59), CONVENTION)  # one second before
    assert fx.is_market_open(utc(2026, 3, 6, 20, 59), CONVENTION)  # Fri 15:59 EST
    assert not fx.is_market_open(utc(2026, 3, 6, 21), CONVENTION)  # close is half-open
    assert not fx.is_market_open(utc(2026, 3, 7, 18), CONVENTION)  # Saturday
    assert not fx.is_market_open(utc(2026, 3, 8, 18), CONVENTION)  # Sunday pre-open
    assert fx.is_market_open(utc(2026, 3, 11, 12), CONVENTION)  # midweek


# --- (d) rollover boundary and triple roll ------------------------------------ #
def test_rollover_maps_position_across_tue_17et_to_next_trading_day() -> None:
    # Hand-computed: Tue 2026-03-10 17:00 EDT = 21:00:00Z.
    assert fx.trading_day_of(utc(2026, 3, 10, 20, 59, 59), CONVENTION) == date(2026, 3, 10)
    assert fx.trading_day_of(utc(2026, 3, 10, 21, 0, 0), CONVENTION) == date(2026, 3, 11)
    # Monday 17:00 EDT (21:00Z) flips Monday -> Tuesday.
    assert fx.trading_day_of(utc(2026, 3, 9, 20, 59, 59), CONVENTION) == date(2026, 3, 9)
    assert fx.trading_day_of(utc(2026, 3, 9, 21, 0, 0), CONVENTION) == date(2026, 3, 10)
    # The Sunday-evening open belongs to Monday's trading day.
    assert fx.trading_day_of(utc(2026, 3, 9, 1, 0, 0), CONVENTION) == date(2026, 3, 9)
    cal = FxSessionCalendar(calendar_id="FX_G10_SPOT_SYNTHETIC_TEST_ONLY_ROLL")
    assert cal.trading_day_of(utc(2026, 3, 10, 21, 0, 0)) == date(2026, 3, 11)


def test_triple_roll_is_wednesday_and_holiday_aware() -> None:
    assert fx.is_triple_roll(date(2026, 3, 11)) is True  # Wednesday
    assert fx.is_triple_roll(date(2026, 3, 10)) is False  # Tuesday
    assert fx.is_triple_roll(date(2026, 3, 14)) is False  # Saturday
    cal = FxSessionCalendar(calendar_id="FX_G10_SPOT_SYNTHETIC_TEST_ONLY_TRIPLE")
    assert cal.is_triple_roll(date(2026, 3, 11)) is True
    holiday_wednesday = FxHolidayTable.synthetic(
        (FxHolidayEntry(day=date(2026, 3, 11), currencies=("USD", "JPY")),)
    )
    holiday_cal = FxSessionCalendar(
        calendar_id="FX_G10_SPOT_SYNTHETIC_TEST_ONLY_TRIPLE_HOL",
        holiday_table=holiday_wednesday,
    )
    assert holiday_cal.is_session_day(date(2026, 3, 11)) is False
    assert holiday_cal.is_triple_roll(date(2026, 3, 11)) is False  # suppressed by closure


# --- (e) synthetic holiday removes the session -------------------------------- #
def test_synthetic_weekday_holiday_removes_session_and_appears_in_holidays() -> None:
    table = FxHolidayTable.synthetic(
        (
            # SYNTHETIC_TEST_ONLY: invented holiday, no authority claimed.
            FxHolidayEntry(
                day=date(2026, 3, 11),
                currencies=("USD", "JPY"),
                zone_name="America/New_York",
                note="synthetic_test_only midweek closure",
            ),
            # A Saturday entry cannot remove a session and is not surfaced.
            FxHolidayEntry(day=date(2026, 3, 14), currencies=("USD",)),
        )
    )
    assert table.is_synthetic is True
    assert table.provenance == SYNTHETIC_TEST_ONLY
    cal = FxSessionCalendar(
        calendar_id="FX_G10_SPOT_SYNTHETIC_TEST_ONLY_HOL",
        holiday_table=table,
    )
    assert date(2026, 3, 11) in cal.holidays(date(2026, 3, 9), date(2026, 3, 13))
    assert cal.holidays(date(2026, 3, 9), date(2026, 3, 13)) == (date(2026, 3, 11),)
    assert cal.is_session_day(date(2026, 3, 11)) is False
    assert cal.session_bounds(date(2026, 3, 11)) is None
    assert cal.labeled_sessions(date(2026, 3, 11)) == ()
    # Neighbouring days keep their sessions.
    assert cal.is_session_day(date(2026, 3, 10)) is True
    assert cal.is_session_day(date(2026, 3, 12)) is True
    assert cal.holidays(date(2026, 1, 1), date(2026, 12, 31)) == (date(2026, 3, 11),)


def test_synthetic_early_close_shortens_session_and_marks_flags() -> None:
    # Thu 2026-03-12 early close at 14:00 America/New_York = 18:00:00Z (EDT).
    table = FxHolidayTable.synthetic(
        (
            FxHolidayEntry(
                day=date(2026, 3, 12),
                currencies=("USD",),
                closes_market=False,
                early_close_local=time(14, 0),
                note="synthetic_test_only early close",
            ),
        )
    )
    cal = FxSessionCalendar(
        calendar_id="FX_G10_SPOT_SYNTHETIC_TEST_ONLY_EARLY",
        holiday_table=table,
    )
    assert cal.is_session_day(date(2026, 3, 12)) is True
    assert cal.early_close_cutoff_utc(date(2026, 3, 12)) == utc(2026, 3, 12, 18)
    bounds = cal.session_bounds(date(2026, 3, 12))
    assert bounds is not None
    assert (bounds.start_utc, bounds.end_utc) == (utc(2026, 3, 11, 21), utc(2026, 3, 12, 18))
    assert bounds.is_early_close is True
    labels = {interval.label: interval for interval in cal.labeled_sessions(date(2026, 3, 12))}
    assert (labels["NEW_YORK"].start_utc, labels["NEW_YORK"].end_utc) == (
        utc(2026, 3, 12, 12),
        utc(2026, 3, 12, 18),
    )
    assert labels["NEW_YORK"].is_shortened is True
    assert labels["NEW_YORK"].is_illiquid is True  # thin holiday day marking
    # Friday 2026-03-13 keeps its full-session end at the weekly close 20:00Z.
    friday = cal.session_bounds(date(2026, 3, 13))
    assert friday is not None and friday.end_utc == utc(2026, 3, 13, 20)


def test_marking_hooks_shorten_and_flag_illiquid() -> None:
    day = date(2026, 3, 10)
    intervals = fx.day_session_intervals(day)
    by_label = {interval.label: interval for interval in intervals}
    assert (by_label["TOKYO"].start_utc, by_label["TOKYO"].end_utc) == (
        utc(2026, 3, 10, 0),
        utc(2026, 3, 10, 9),
    )
    hooked = fx.apply_session_hooks(
        day,
        intervals,
        (
            fx.LocalCutoffHook(fx.NEW_YORK_ZONE, time(12, 0)),  # cut NY at noon EDT
            fx.IlliquidWindowHook(fx.TOKYO_ZONE, time(15, 0), time(18, 0)),  # 06:00-09:00Z
        ),
    )
    hooked_by_label = {interval.label: interval for interval in hooked}
    assert (hooked_by_label["NEW_YORK"].start_utc, hooked_by_label["NEW_YORK"].end_utc) == (
        utc(2026, 3, 10, 12),
        utc(2026, 3, 10, 16),
    )
    assert hooked_by_label["NEW_YORK"].is_shortened is True
    assert hooked_by_label["TOKYO"].is_illiquid is True
    assert hooked_by_label["LONDON"].is_shortened is False
    assert hooked_by_label["LONDON"].is_illiquid is False


# --- session labels are named-zone derived ------------------------------------ #
def test_session_labels_derived_from_named_zones_not_fixed_offsets() -> None:
    zones = {spec.label: spec.zone_name for spec in fx.FX_SESSION_SPECS}
    assert zones == {
        "SYDNEY": "Australia/Sydney",
        "TOKYO": "Asia/Tokyo",
        "LONDON": "Europe/London",
        "NEW_YORK": "America/New_York",
    }
    for zone_name in zones.values():
        fx.require_zone_name(zone_name)  # resolvable by zoneinfo
    with pytest.raises(ValueError):
        fx.require_zone_name("EST5EDT,M3.2.0,M11.1.0")  # POSIX rule string, not IANA
    with pytest.raises(ValueError):
        fx.require_zone_name("UTC+03:00")  # fixed offset, never a session zone


# --- (f/g) holiday-table and PIT macro-clock fail-closed contracts ------------ #
def test_holiday_table_fail_closed_on_missing_flag_or_authority() -> None:
    entry = FxHolidayEntry(day=date(2026, 3, 11), currencies=("USD",))
    with pytest.raises(ValueError, match="SYNTHETIC_TEST_ONLY"):
        FxHolidayTable(entries=(entry,), synthetic_test_only=False, authority_id=None)
    with pytest.raises(ValueError, match="authority"):
        FxHolidayTable(entries=(entry,), synthetic_test_only=True, authority_id="somewhere")
    authoritative = FxHolidayTable.from_authority((entry,), authority_id="vendor/holidays/v1")
    assert authoritative.is_synthetic is False
    assert authoritative.provenance == "vendor/holidays/v1"


def test_calendar_fail_closed_against_synthetic_holidays() -> None:
    synthetic_cal = FxSessionCalendar(calendar_id="FX_G10_SPOT_SYNTHETIC_TEST_ONLY_X")
    assert synthetic_cal.is_production_ready is False
    assert synthetic_cal.holiday_provenance == SYNTHETIC_TEST_ONLY
    with pytest.raises(ValueError, match=SYNTHETIC_TEST_ONLY):
        synthetic_cal.require_production_ready()
    authoritative_cal = FxSessionCalendar(
        calendar_id="FX_G10_SPOT_AUTH_EXAMPLE",
        holiday_table=FxHolidayTable.from_authority((), authority_id="vendor/holidays/v1"),
    )
    assert authoritative_cal.is_production_ready is True
    authoritative_cal.require_production_ready()  # does not raise
    with pytest.raises(ValueError):
        FxSessionCalendar(calendar_id="")  # calendar_id never defaulted


def test_macro_clock_refuses_backfilled_event_with_reason() -> None:
    cal = FxSessionCalendar(calendar_id="FX_G10_SPOT_SYNTHETIC_TEST_ONLY_PIT")
    digest = "ab" * 32
    good = MacroEvent(
        event_id="us_cpi_2026_03",
        event_time_utc=utc(2026, 3, 11, 14),
        publish_time_utc=utc(2026, 3, 11, 12),  # published before the event: PIT-safe
    )
    backfilled = MacroEvent(
        event_id="us_cpi_backfill_attempt",
        event_time_utc=utc(2026, 3, 11, 14),
        publish_time_utc=utc(2026, 3, 11, 15, 30),  # publish AFTER event: backfill
    )
    missing_publish = MacroEvent(
        event_id="no_publish_time", event_time_utc=utc(2026, 3, 11, 14), publish_time_utc=None
    )
    exact_publish = MacroEvent(
        event_id="published_at_event_time",
        event_time_utc=utc(2026, 3, 11, 14),
        publish_time_utc=utc(2026, 3, 11, 14),  # publish == event is acceptable
    )
    result = cal.pit_event_timestamps(digest, (good, backfilled, missing_publish, exact_publish))
    assert result.source_digest == digest
    assert result.accepted == (
        ("us_cpi_2026_03", utc(2026, 3, 11, 14)),
        ("published_at_event_time", utc(2026, 3, 11, 14)),
    )
    assert [refusal.event_id for refusal in result.refusals] == [
        "us_cpi_backfill_attempt",
        "no_publish_time",
    ]
    backfill_reason = result.refusals[0].reason
    assert "backfill" in backfill_reason and "publish-time" in backfill_reason
    assert "15:30" in backfill_reason  # reason names the offending publish-time
    assert "missing publish-time" in result.refusals[1].reason
    # Provenance: source digest must be a lowercase sha256 hex string.
    with pytest.raises(ValueError):
        cal.pit_event_timestamps("NOT-A-DIGEST", (good,))
    with pytest.raises(ValueError):
        MacroEvent(
            event_id="x",
            event_time_utc=datetime(2026, 3, 11, 14),  # naive event-time
            publish_time_utc=None,
        )
    with pytest.raises(ValueError):
        MacroEvent(
            event_id="x",
            event_time_utc=utc(2026, 3, 11, 14),
            publish_time_utc=datetime(2026, 3, 11, 12),  # naive publish-time
        )


def test_sydney_session_week_start_clipped_to_weekly_open() -> None:
    # Hand-computed: Sydney Monday 2026-03-09 07:00 AEDT (+11) = Sun 2026-03-08
    # 20:00Z, which precedes the weekly open Mon 01:00Z; the weekly model must
    # clip it to the open, never extend the market into the weekend.
    week = fx.sessions_for_trading_week(date(2026, 3, 8), CONVENTION)
    # Nothing in the week may start before the weekly open (Mon 01:00Z).
    assert week == tuple(sorted(week, key=lambda i: (i.start_utc, i.label)))
    assert min(interval.start_utc for interval in week) == utc(2026, 3, 9, 1)
    sydney_monday = [
        interval
        for interval in week
        if interval.label == "SYDNEY" and interval.start_utc == utc(2026, 3, 9, 1)
    ]
    assert len(sydney_monday) == 1
    assert sydney_monday[0].end_utc == utc(2026, 3, 9, 5)  # 16:00 AEDT close
    raw = fx.day_session_intervals(date(2026, 3, 9))
    raw_sydney = [interval for interval in raw if interval.label == "SYDNEY"][0]
    assert raw_sydney.start_utc == utc(2026, 3, 8, 20)  # unclipped zone mapping
