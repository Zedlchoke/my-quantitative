"""Synthetic-golden tests for US_EQUITY_REGULAR_V1 (owner: A4, gate SD1).

All dates are hard-coded, hand-verified against the nyse.com published
calendars and documented market history (see PLAN_stocks.md section 2 and
research/audits/stocks/s1_a4/).  The suite is pure: it performs zero repo
writes.
"""

from __future__ import annotations

import dataclasses
from datetime import date, datetime, timezone

import pytest

from research.assets.common.calendar import (
    TEST_ONLY_DUMMY_SOLAR_24X7_ID,
    Session,
    SessionCalendar,
    is_test_only_calendar_id,
    require_production_calendar_id,
)
from research.assets.stocks.calendar import (
    CALENDAR_ID,
    CALENDAR_TABLE_END,
    CALENDAR_TABLE_START,
    CALENDAR_TABLE_VERSION,
    ET_ZONE,
    GAP_OK_WITH_REASON,
    GAP_UNEXPLAINED,
    GapClassification,
    HaltInterval,
    NEEDS_PROVIDER_VERIFICATION,
    USEquityRegularCalendar,
    US_EQUITY_REGULAR_V1,
    assert_no_unexplained_gap,
)

UTC = timezone.utc

# Golden: sha256 of the frozen table JSON serialized canonically.
# Any change to the frozen table MUST change this digest and re-freeze a
# new CALENDAR_TABLE_VERSION (calendar/version drift = new manifest).
GOLDEN_CALENDAR_MANIFEST_DIGEST = (
    "028a7b21c9e306c7399467309d18e3ed696181682ca01f1e3170c21bdceb69ab"
)


def utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=UTC)


# --- identity and interface ------------------------------------------------- #
def test_implements_shared_session_calendar_interface():
    assert isinstance(US_EQUITY_REGULAR_V1, SessionCalendar)
    assert US_EQUITY_REGULAR_V1.calendar_id == CALENDAR_ID == "US_EQUITY_REGULAR_V1"
    assert not is_test_only_calendar_id(US_EQUITY_REGULAR_V1.calendar_id)
    assert not US_EQUITY_REGULAR_V1.is_test_only()
    assert (
        require_production_calendar_id(US_EQUITY_REGULAR_V1.calendar_id, context="t")
        == US_EQUITY_REGULAR_V1.calendar_id
    )
    with pytest.raises(ValueError, match="TEST_ONLY"):
        require_production_calendar_id(TEST_ONLY_DUMMY_SOLAR_24X7_ID, context="t")


def test_table_version_and_source_note_are_documented():
    import research.assets.stocks.calendar as cal_module

    doc = cal_module.__doc__
    assert CALENDAR_TABLE_VERSION == "US_EQUITY_REGULAR_V1_TABLE_20260902"
    assert "https://www.nyse.com/trade/hours-calendars" in doc
    assert CALENDAR_TABLE_VERSION in doc
    assert "NEEDS_PROVIDER_VERIFICATION" in doc
    assert "Never manufacture" in doc or "never claims" in doc
    assert NEEDS_PROVIDER_VERIFICATION, "verification list must not be empty"


# --- DST-correct session bounds (America/New_York via zoneinfo) -------------- #
def test_session_bounds_est_before_spring_forward_2024():
    session = US_EQUITY_REGULAR_V1.require_session(date(2024, 3, 8))  # Friday, EST
    assert session.start_utc == utc(2024, 3, 8, 14, 30)  # 09:30 EST == UTC-5
    assert session.end_utc == utc(2024, 3, 8, 21, 0)  # 16:00 EST
    assert session.is_early_close is False
    assert session.label == "US_EQUITY_REGULAR_V1:2024-03-08"


def test_session_bounds_edt_after_spring_forward_2024():
    session = US_EQUITY_REGULAR_V1.require_session(date(2024, 3, 11))  # Monday, EDT
    assert session.start_utc == utc(2024, 3, 11, 13, 30)  # 09:30 EDT == UTC-4
    assert session.end_utc == utc(2024, 3, 11, 20, 0)  # 16:00 EDT


def test_fall_back_2024_boundaries():
    # Nov 1 2024 is EDT (UTC-4); Nov 4 2024 is EST (UTC-5).
    assert US_EQUITY_REGULAR_V1.require_session(date(2024, 11, 1)).end_utc == utc(
        2024, 11, 1, 20, 0
    )
    assert US_EQUITY_REGULAR_V1.require_session(date(2024, 11, 4)).start_utc == utc(
        2024, 11, 4, 14, 30
    )


# --- early close golden ------------------------------------------------------- #
def test_2024_07_03_early_close_13_00_et():
    day = date(2024, 7, 3)
    session = US_EQUITY_REGULAR_V1.require_session(day)
    assert session.is_early_close is True
    assert session.end_utc == utc(2024, 7, 3, 17, 0)  # 13:00 EDT
    assert US_EQUITY_REGULAR_V1.early_close_cutoff_utc(day) == utc(2024, 7, 3, 17, 0)
    assert US_EQUITY_REGULAR_V1.early_close_cutoff_utc(date(2024, 7, 2)) is None


def test_2024_11_29_and_2024_12_24_are_half_days():
    # Both 13:00 ET early closes fall in EST (UTC-5) after the Nov 3 fall-back.
    for day in (date(2024, 11, 29), date(2024, 12, 24)):
        session = US_EQUITY_REGULAR_V1.require_session(day)
        assert session.is_early_close is True
        assert session.end_utc == utc(day.year, day.month, day.day, 18, 0)


# --- holiday goldens ----------------------------------------------------------- #
@pytest.mark.parametrize(
    "day",
    [
        date(2024, 7, 4),  # Independence Day
        date(2025, 7, 4),  # Independence Day (Friday, after 2025-07-03 half day)
        date(2025, 6, 19),  # Juneteenth
        date(2022, 6, 20),  # Juneteenth observed (June 19, 2022 was Sunday)
        date(2024, 3, 29),  # Good Friday 2024
        date(2024, 12, 25),
        date(2012, 1, 2),  # New Year 2012 observed (Jan 1 was Sunday)
        date(2010, 7, 5),  # July 4, 2010 (Sunday) observed Monday
        date(2021, 12, 24),  # Christmas 2021 (Saturday) observed Friday: FULL day
        date(2020, 7, 3),  # July 4, 2020 (Saturday) observed Friday: FULL day
        date(2026, 7, 3),  # July 4, 2026 (Saturday) observed Friday: FULL day
    ],
)
def test_documented_holiday_closures(day: date):
    assert US_EQUITY_REGULAR_V1.is_session(day) is False
    assert US_EQUITY_REGULAR_V1.session_bounds(day) is None
    assert day in US_EQUITY_REGULAR_V1.holidays(day, day)


@pytest.mark.parametrize(
    "day,expected_reason",
    [
        (date(2012, 10, 29), "SPECIAL_CLOSURE:HURRICANE_SANDY"),
        (date(2012, 10, 30), "SPECIAL_CLOSURE:HURRICANE_SANDY"),
        (date(2018, 12, 5), "SPECIAL_CLOSURE:NATIONAL_MOURNING_GHW_BUSH"),
        (date(2025, 1, 9), "SPECIAL_CLOSURE:NATIONAL_MOURNING_J_CARTER"),
    ],
)
def test_documented_unscheduled_closures(day: date, expected_reason: str):
    assert US_EQUITY_REGULAR_V1.is_session(day) is False
    assert US_EQUITY_REGULAR_V1.closure_reason(day) == expected_reason
    assert day in US_EQUITY_REGULAR_V1.holidays(day, day)


def test_saturday_new_years_day_is_not_observed():
    # Documented precedents: preceding Friday Dec 31 was a REGULAR session
    # when Jan 1 fell on Saturday (2004, 2010, 2021).
    for day in (date(2010, 12, 31), date(2021, 12, 31), date(2027, 12, 31)):
        session = US_EQUITY_REGULAR_V1.session_bounds(day)
        assert session is not None
        assert session.is_early_close is False


def test_weekends_are_not_sessions_and_carry_reason():
    assert US_EQUITY_REGULAR_V1.is_session(date(2024, 7, 6)) is False
    assert US_EQUITY_REGULAR_V1.closure_reason(date(2024, 7, 6)) == "WEEKEND"
    assert date(2024, 7, 6) not in US_EQUITY_REGULAR_V1.holidays(
        date(2024, 7, 6), date(2024, 7, 6)
    )


def test_holidays_range_is_sorted_and_fails_closed():
    holidays = US_EQUITY_REGULAR_V1.holidays(date(2024, 7, 1), date(2024, 7, 31))
    assert holidays == (date(2024, 7, 4),)
    with pytest.raises(ValueError, match="end date precedes start date"):
        US_EQUITY_REGULAR_V1.holidays(date(2024, 7, 31), date(2024, 7, 1))


# --- range helpers --------------------------------------------------------------- #
def test_sessions_in_range_july_2024_golden():
    sessions = US_EQUITY_REGULAR_V1.sessions_in_range(date(2024, 7, 1), date(2024, 7, 31))
    assert len(sessions) == 22  # 23 weekdays minus July 4
    assert sessions[0].start_utc == utc(2024, 7, 1, 13, 30)
    early = [s for s in sessions if s.is_early_close]
    assert [s.end_utc for s in early] == [utc(2024, 7, 3, 17, 0)]


@pytest.mark.parametrize(
    "year,expected",
    [
        (2010, 252),
        (2018, 251),  # Dec 5 Bush national mourning
        (2020, 253),
        (2021, 252),
        (2022, 251),
        (2023, 250),
        (2024, 252),
        (2025, 250),  # includes the Jan 9 Carter national mourning closure
    ],
)
def test_documented_annual_session_counts(year: int, expected: int):
    assert US_EQUITY_REGULAR_V1.session_count(date(year, 1, 1), date(year, 12, 31)) == expected


def test_next_session_goldens():
    assert US_EQUITY_REGULAR_V1.next_session(date(2025, 7, 3)).label == (
        "US_EQUITY_REGULAR_V1:2025-07-07"
    )  # across July 4 + weekend
    assert US_EQUITY_REGULAR_V1.next_session(date(2024, 3, 8)).label == (
        "US_EQUITY_REGULAR_V1:2024-03-11"
    )  # Friday -> DST-switch Monday
    assert US_EQUITY_REGULAR_V1.next_session(date(2012, 10, 26)).label == (
        "US_EQUITY_REGULAR_V1:2012-10-31"
    )  # across the Sandy closure


# --- fail-closed horizon and input validation ------------------------------------- #
def test_queries_outside_table_horizon_fail_closed():
    for bad_day in (CALENDAR_TABLE_START.replace(year=2009), CALENDAR_TABLE_END.replace(year=2031)):
        with pytest.raises(ValueError, match="frozen table horizon"):
            US_EQUITY_REGULAR_V1.session_bounds(bad_day)
        with pytest.raises(ValueError, match="frozen table horizon"):
            US_EQUITY_REGULAR_V1.is_session(bad_day)
    with pytest.raises(ValueError, match="frozen table horizon"):
        US_EQUITY_REGULAR_V1.next_session(CALENDAR_TABLE_END)
    with pytest.raises(ValueError, match="frozen table horizon"):
        US_EQUITY_REGULAR_V1.sessions_in_range(date(2009, 1, 1), date(2009, 12, 31))


def test_datetime_input_is_rejected_fail_closed():
    with pytest.raises(ValueError, match="datetime.date"):
        US_EQUITY_REGULAR_V1.session_bounds(datetime(2024, 7, 3, tzinfo=UTC))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="datetime.date"):
        US_EQUITY_REGULAR_V1.is_session(None)  # type: ignore[arg-type]


# --- pre/post market: explicit flags, disabled in baseline scoring ----------------- #
def test_pre_and_post_market_disabled_in_baseline_scoring():
    assert US_EQUITY_REGULAR_V1.pre_market_enabled is False
    assert US_EQUITY_REGULAR_V1.post_market_enabled is False
    assert US_EQUITY_REGULAR_V1.enabled_phases == ("REGULAR",)
    US_EQUITY_REGULAR_V1.assert_baseline_scoring_phases()  # does not raise
    with pytest.raises(ValueError, match="PRE_MARKET phase is disabled"):
        US_EQUITY_REGULAR_V1.phase_bounds(date(2024, 7, 2), "PRE_MARKET")
    with pytest.raises(ValueError, match="POST_MARKET phase is disabled"):
        US_EQUITY_REGULAR_V1.phase_bounds(date(2024, 7, 2), "POST_MARKET")
    with pytest.raises(ValueError, match="unknown market phase"):
        US_EQUITY_REGULAR_V1.phase_bounds(date(2024, 7, 2), "OVERNIGHT")


def test_pre_post_market_available_only_when_explicitly_enabled():
    cal = USEquityRegularCalendar(pre_market_enabled=True, post_market_enabled=True)
    assert cal.enabled_phases == ("PRE_MARKET", "REGULAR", "POST_MARKET")
    pre = cal.phase_bounds(date(2024, 7, 2), "PRE_MARKET")
    post = cal.phase_bounds(date(2024, 7, 2), "POST_MARKET")
    assert pre.start_utc == utc(2024, 7, 2, 8, 0)  # 04:00 EDT
    assert pre.end_utc == utc(2024, 7, 2, 13, 30)  # 09:30 EDT
    assert post.start_utc == utc(2024, 7, 2, 20, 0)  # 16:00 EDT
    assert post.end_utc == utc(2024, 7, 3, 0, 0)  # 20:00 EDT
    with pytest.raises(ValueError, match="baseline scoring"):
        cal.assert_baseline_scoring_phases()


# --- manifests ---------------------------------------------------------------------- #
def test_calendar_manifest_digest_matches_pinned_golden():
    digest = US_EQUITY_REGULAR_V1.calendar_manifest_digest()
    assert digest == GOLDEN_CALENDAR_MANIFEST_DIGEST
    # Recompute straight from the frozen table payload: byte-stable canonical JSON.
    import hashlib
    import json

    payload = json.dumps(
        US_EQUITY_REGULAR_V1.frozen_table_payload(), sort_keys=True, separators=(",", ":")
    )
    assert hashlib.sha256(payload.encode("utf-8")).hexdigest() == digest


def test_table_payload_shape_is_frozen():
    payload = US_EQUITY_REGULAR_V1.frozen_table_payload()
    assert payload["table_version"] == CALENDAR_TABLE_VERSION
    assert payload["table_start"] == "2010-01-01"
    assert payload["table_end"] == "2030-12-31"
    assert len(payload["holidays"]) == 195
    assert len(payload["half_days"]) == 45
    assert payload["special_closures"] == {
        "2012-10-29": "HURRICANE_SANDY",
        "2012-10-30": "HURRICANE_SANDY",
        "2018-12-05": "NATIONAL_MOURNING_GHW_BUSH",
        "2025-01-09": "NATIONAL_MOURNING_J_CARTER",
    }


def test_monthly_and_annual_manifest_digests_are_stable_and_bound_to_table():
    july_2024 = US_EQUITY_REGULAR_V1.monthly_manifest_digest(2024, 7)
    assert july_2024 == US_EQUITY_REGULAR_V1.monthly_manifest_digest(2024, 7)
    year_2024 = US_EQUITY_REGULAR_V1.annual_manifest_digest(2024)
    assert year_2024 == US_EQUITY_REGULAR_V1.annual_manifest_digest(2024)
    assert july_2024 != year_2024
    assert july_2024 != GOLDEN_CALENDAR_MANIFEST_DIGEST
    assert US_EQUITY_REGULAR_V1.annual_manifest_digest(2024) != US_EQUITY_REGULAR_V1.annual_manifest_digest(
        2025
    )
    with pytest.raises(ValueError, match="month must be in 1..12"):
        US_EQUITY_REGULAR_V1.monthly_manifest_digest(2024, 13)
    with pytest.raises(ValueError, match="frozen table horizon"):
        US_EQUITY_REGULAR_V1.annual_manifest_digest(2031)


# --- gap classification: overnight gaps are returns, halts fail closed --------------- #
def test_overnight_gap_is_ok_with_reason_and_no_synthetic_fill():
    gap = US_EQUITY_REGULAR_V1.classify_gap(
        utc(2024, 7, 2, 20, 0), utc(2024, 7, 3, 13, 30)
    )
    assert gap.status == GAP_OK_WITH_REASON
    assert gap.ok is True
    assert gap.synthetic_fill_allowed is False
    assert "overnight" in gap.reason


def test_early_close_tail_and_holiday_gap_is_ok():
    gap = US_EQUITY_REGULAR_V1.classify_gap(
        utc(2024, 7, 3, 17, 0), utc(2024, 7, 5, 13, 30)
    )  # after 13:00 early close, across July 4
    assert gap.ok is True
    assert "2024-07-04=SCHEDULED_HOLIDAY" in gap.reason


def test_weekend_gap_is_ok():
    gap = US_EQUITY_REGULAR_V1.classify_gap(
        utc(2024, 7, 5, 20, 0), utc(2024, 7, 8, 13, 30)
    )
    assert gap.ok is True
    assert "2024-07-06=WEEKEND" in gap.reason and "2024-07-07=WEEKEND" in gap.reason


def test_sandy_week_gap_without_halt_declaration_is_unexplained():
    # A full missing week across the 2012-10-29/30 closures still contains
    # the 2012-10-31..11-02 regular sessions: a data defect, not a closure.
    gap = US_EQUITY_REGULAR_V1.classify_gap(
        utc(2012, 10, 26, 20, 0), utc(2012, 11, 6, 14, 30)
    )  # Monday Nov 5 open is 09:30 EST == 14:30Z (fall-back was Nov 4)
    assert gap.unexplained is True
    assert "2012-10-31" in gap.reason
    assert gap.synthetic_fill_allowed is False


def test_intraday_missing_bar_is_unexplained_and_fails_closed():
    gap = US_EQUITY_REGULAR_V1.classify_gap(
        utc(2024, 7, 2, 15, 0), utc(2024, 7, 2, 16, 0)
    )
    assert gap.status == GAP_UNEXPLAINED
    assert "no synthetic fill" in gap.reason
    assert gap.synthetic_fill_allowed is False
    with pytest.raises(ValueError, match="unexplained gap"):
        assert_no_unexplained_gap(gap)


def test_declared_halt_fully_covering_gap_is_ok_but_never_filled():
    halts = [
        HaltInterval(
            start_utc=utc(2024, 7, 2, 15, 0),
            end_utc=utc(2024, 7, 2, 16, 0),
            label="LULD_VOLATILITY_HALT",
        )
    ]
    gap = US_EQUITY_REGULAR_V1.classify_gap(
        utc(2024, 7, 2, 15, 0), utc(2024, 7, 2, 16, 0), declared_halts=halts
    )
    assert gap.ok is True
    assert "LULD_VOLATILITY_HALT" in gap.reason
    assert gap.synthetic_fill_allowed is False  # halt explains, never fills
    assert_no_unexplained_gap(gap)  # does not raise


def test_partially_covered_halt_gap_is_unexplained():
    halts = [
        HaltInterval(
            start_utc=utc(2024, 7, 2, 15, 30),
            end_utc=utc(2024, 7, 2, 16, 0),
            label="PARTIAL_HALT",
        )
    ]
    gap = US_EQUITY_REGULAR_V1.classify_gap(
        utc(2024, 7, 2, 15, 0), utc(2024, 7, 2, 16, 0), declared_halts=halts
    )
    assert gap.unexplained is True


def test_gap_beyond_table_horizon_is_unexplained():
    gap = US_EQUITY_REGULAR_V1.classify_gap(
        utc(2030, 12, 31, 21, 0), utc(2031, 1, 5, 14, 30)
    )
    assert gap.unexplained is True
    assert "horizon" in gap.reason


def test_gap_input_validation():
    with pytest.raises(ValueError, match="tz-aware"):
        US_EQUITY_REGULAR_V1.classify_gap(datetime(2024, 7, 2), utc(2024, 7, 3))
    with pytest.raises(ValueError, match="end precedes"):
        US_EQUITY_REGULAR_V1.classify_gap(utc(2024, 7, 3), utc(2024, 7, 2))
    with pytest.raises(ValueError, match="halt end must be after"):
        HaltInterval(utc(2024, 7, 2, 16, 0), utc(2024, 7, 2, 15, 0), "BAD")
    with pytest.raises(ValueError, match="non-empty"):
        HaltInterval(utc(2024, 7, 2, 15, 0), utc(2024, 7, 2, 16, 0), "  ")
    empty = US_EQUITY_REGULAR_V1.classify_gap(utc(2024, 7, 2, 15, 0), utc(2024, 7, 2, 15, 0))
    assert empty.ok is True


def test_gap_classification_is_immutable_and_fails_closed_on_bad_status():
    gap = US_EQUITY_REGULAR_V1.classify_gap(utc(2024, 7, 2, 15, 0), utc(2024, 7, 2, 16, 0))
    with pytest.raises(dataclasses.FrozenInstanceError):
        gap.status = GAP_OK_WITH_REASON  # type: ignore[misc]
    with pytest.raises(ValueError, match="never allowed"):
        GapClassification(
            start_utc=utc(2024, 7, 2, 15, 0),
            end_utc=utc(2024, 7, 2, 16, 0),
            status=GAP_OK_WITH_REASON,
            reason="synthetic fill",
            synthetic_fill_allowed=True,
        )
    with pytest.raises(ValueError, match="non-empty reason"):
        GapClassification(
            start_utc=utc(2024, 7, 2, 15, 0),
            end_utc=utc(2024, 7, 2, 16, 0),
            status=GAP_UNEXPLAINED,
            reason="",
        )


def test_early_close_day_afternoon_interval_is_outside_session():
    # 2024-07-03 14:00 ET (18:00Z) is after the 13:00 early close: no prints
    # expected there, so a missing interval is OK, not a data defect.
    gap = US_EQUITY_REGULAR_V1.classify_gap(
        utc(2024, 7, 3, 17, 0), utc(2024, 7, 4, 13, 30)
    )
    assert gap.ok is True


# --- zone sanity ------------------------------------------------------------------------ #
def test_calendar_zone_is_america_new_york():
    assert str(ET_ZONE) == "America/New_York"
