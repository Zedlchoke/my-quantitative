"""Calendar interface tests: no implicit 24/7 default; TEST_ONLY is explicit."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

import research.assets.common.calendar as calendar_module
from research.assets.common.calendar import (
    TEST_ONLY_CALENDAR_PREFIX,
    TEST_ONLY_DUMMY_SOLAR_24X7_ID,
    TEST_ONLY_DummySolar24x7,
    Session,
    SessionCalendar,
    is_test_only_calendar_id,
    require_production_calendar_id,
)


def test_session_calendar_is_abstract():
    with pytest.raises(TypeError):
        SessionCalendar()  # type: ignore[abstract]
    for method in (
        "calendar_id",
        "is_session_day",
        "holidays",
        "session_bounds",
        "early_close_cutoff_utc",
    ):
        assert method in SessionCalendar.__abstractmethods__


def test_module_has_no_default_calendar():
    # No implicit default calendar object/factory may exist in the module.
    forbidden = [
        name
        for name in dir(calendar_module)
        if name.upper().startswith("DEFAULT") or name in {"Solar24x7", "TwentyFourSeven"}
    ]
    assert forbidden == []


def test_test_only_calendar_is_explicitly_marked():
    cal = TEST_ONLY_DummySolar24x7()
    assert cal.calendar_id.startswith(TEST_ONLY_CALENDAR_PREFIX)
    assert cal.is_test_only()
    assert is_test_only_calendar_id(cal.calendar_id)
    assert not is_test_only_calendar_id("XNYS_SESSIONS_V1")


def test_test_only_calendar_sessions_are_solar_days():
    cal = TEST_ONLY_DummySolar24x7()
    day = date(2026, 9, 2)
    assert cal.is_session_day(day)
    assert cal.holidays(day, day) == ()
    assert cal.early_close_cutoff_utc(day) is None
    session = cal.session_bounds(day)
    assert session == Session(
        start_utc=datetime(2026, 9, 2, tzinfo=timezone.utc),
        end_utc=datetime(2026, 9, 3, tzinfo=timezone.utc),
    )
    sessions = cal.sessions_between(date(2026, 9, 2), date(2026, 9, 4))
    assert len(sessions) == 3


def test_production_calendar_ids_are_enforced_fail_closed():
    assert (
        require_production_calendar_id("XNYS_SESSIONS_V1", context="t")
        == "XNYS_SESSIONS_V1"
    )
    with pytest.raises(ValueError, match="TEST_ONLY"):
        require_production_calendar_id(TEST_ONLY_DUMMY_SOLAR_24X7_ID, context="t")
    with pytest.raises(ValueError, match="explicit"):
        require_production_calendar_id("", context="t")
    with pytest.raises(ValueError, match="explicit"):
        require_production_calendar_id("   ", context="t")


def test_session_requires_tz_aware_and_ordered_bounds():
    with pytest.raises(ValueError, match="tz-aware"):
        Session(start_utc=datetime(2026, 9, 2), end_utc=datetime(2026, 9, 3))
    with pytest.raises(ValueError, match="after session start"):
        Session(
            start_utc=datetime(2026, 9, 3, tzinfo=timezone.utc),
            end_utc=datetime(2026, 9, 2, tzinfo=timezone.utc),
        )
