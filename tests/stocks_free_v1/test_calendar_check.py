"""Synthetic goldens for exchange-calendar reconciliation (A3)."""

from __future__ import annotations

import importlib.util
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_MODULE_PATH = REPO_ROOT / "research" / "stocks_free_v1" / "calendar_check.py"
_SPEC = importlib.util.spec_from_file_location("z1_a3_calendar_check", _MODULE_PATH)
calendar_check = importlib.util.module_from_spec(_SPEC)
sys.modules["z1_a3_calendar_check"] = calendar_check
_SPEC.loader.exec_module(calendar_check)

from research.assets.stocks.calendar import (
    ET_ZONE,
    HaltInterval,
    US_EQUITY_REGULAR_V1 as CAL,
)

UTC = timezone.utc


def _sessions(year: int, month: int) -> list[date]:
    last = (date(year, month % 12 + 1, 1) - timedelta(days=1)) if month < 12 else date(year, 12, 31)
    return [
        s.start_utc.astimezone(ET_ZONE).date()
        for s in CAL.sessions_in_range(date(year, month, 1), last)
    ]


def _round_trip(year: int, month: int) -> list[date]:
    return _sessions(year, month)  # exactly what the calendar declares


# --- PASS golden ----------------------------------------------------------------


def test_exact_session_list_passes_with_boundaries_classified() -> None:
    provided = _round_trip(2016, 1)
    result = calendar_check.reconcile_session_list(provided, calendar=CAL)
    assert result.passed is True
    assert result.verdict == "PASS"
    assert result.missing_sessions == ()
    assert result.unexpected_sessions == ()
    assert result.anomalies == ()
    assert result.provided_count == result.expected_count
    assert result.overnight_boundaries_classified == len(provided) - 1
    # every overnight boundary is explained as OUTSIDE regular sessions:
    # the gap IS a return, never a fabricated bar
    assert result.gap_classifications
    assert all(g.ok for g in result.gap_classifications)
    assert all(not g.synthetic_fill_allowed for g in result.gap_classifications)
    assert result.calendar_id == "US_EQUITY_REGULAR_V1"
    assert result.calendar_table_version == "US_EQUITY_REGULAR_V1_TABLE_20260902"


def test_holiday_and_weekend_absences_need_no_record() -> None:
    provided = _round_trip(2016, 3)  # Good Friday 2016-03-25 closed
    result = calendar_check.reconcile_session_list(provided, calendar=CAL)
    assert result.passed
    assert date(2016, 3, 25) not in provided


# --- missing session fails closed ------------------------------------------------


def test_missing_session_is_recorded_never_filled() -> None:
    provided = _round_trip(2016, 2)
    victim = provided[7]
    provided = [d for d in provided if d != victim]
    result = calendar_check.reconcile_session_list(provided, calendar=CAL)
    assert result.passed is False
    assert victim in result.missing_sessions
    kinds = {a.kind for a in result.anomalies}
    assert "MISSING_SESSION" in kinds
    detail = next(a.detail for a in result.anomalies if a.kind == "MISSING_SESSION")
    assert "never fabricated" in detail


def test_unexpected_saturday_session_recorded() -> None:
    provided = _round_trip(2016, 1) + [date(2016, 1, 9)]  # Saturday
    result = calendar_check.reconcile_session_list(sorted(provided), calendar=CAL)
    assert result.passed is False
    assert date(2016, 1, 9) in result.unexpected_sessions
    detail = next(a.detail for a in result.anomalies if a.kind == "UNEXPECTED_SESSION")
    assert "WEEKEND" in detail


def test_special_closure_day_present_is_unexpected() -> None:
    provided = _round_trip(2012, 10) + [date(2012, 10, 29)]  # Hurricane Sandy
    result = calendar_check.reconcile_session_list(sorted(provided), calendar=CAL)
    assert result.passed is False
    detail = next(a.detail for a in result.anomalies if a.kind == "UNEXPECTED_SESSION")
    assert "SPECIAL_CLOSURE:HURRICANE_SANDY" in detail


# --- duplicates / unsorted / horizon ---------------------------------------------


def test_duplicate_session_fails() -> None:
    provided = _round_trip(2016, 1)
    provided.append(provided[3])
    result = calendar_check.reconcile_session_list(provided, calendar=CAL)
    assert result.passed is False
    assert "DUPLICATE_SESSION" in {a.kind for a in result.anomalies}
    assert provided[3] in result.duplicate_sessions


def test_unsorted_input_fails() -> None:
    provided = _round_trip(2016, 1)
    unsorted_list = list(provided)
    unsorted_list[2], unsorted_list[9] = unsorted_list[9], unsorted_list[2]
    result = calendar_check.reconcile_session_list(unsorted_list, calendar=CAL)
    assert result.passed is False
    assert "UNSORTED_INPUT" in {a.kind for a in result.anomalies}


def test_out_of_horizon_input_fails_closed() -> None:
    result = calendar_check.reconcile_session_list([date(2005, 6, 1)], calendar=CAL)
    assert result.passed is False
    assert "OUTSIDE_CALENDAR_HORIZON" in {a.kind for a in result.anomalies}


def test_empty_input_fails() -> None:
    result = calendar_check.reconcile_session_list([], calendar=CAL)
    assert result.passed is False


# --- halt / no-print records fail closed ------------------------------------------


def _utc(y: int, mo: int, d: int, h: int, mi: int) -> datetime:
    return datetime(y, mo, d, h, mi, tzinfo=UTC)


def test_no_print_inside_session_without_halt_fails() -> None:
    # 2016-01-19 15:00-16:00 UTC sits INSIDE the regular session
    # (10:00-11:00 ET) with no declared halt -> GAP_UNEXPLAINED -> FAIL
    result = calendar_check.reconcile_session_list(
        _round_trip(2016, 1),
        calendar=CAL,
        no_print_intervals=[
            (_utc(2016, 1, 19, 15, 0), _utc(2016, 1, 19, 16, 0))
        ],
    )
    assert result.passed is False
    assert "UNEXPLAINED_GAP" in {a.kind for a in result.anomalies}
    unexplained = [g for g in result.gap_classifications if g.unexplained]
    assert unexplained and all(not g.synthetic_fill_allowed for g in unexplained)


def test_no_print_fully_covered_by_declared_halt_is_ok_but_never_filled() -> None:
    halt = HaltInterval(
        start_utc=_utc(2016, 1, 19, 15, 0),
        end_utc=_utc(2016, 1, 19, 16, 0),
        label="SYNTHETIC_VENUE_HALT",
    )
    result = calendar_check.reconcile_session_list(
        _round_trip(2016, 1),
        calendar=CAL,
        declared_halts=[halt],
        no_print_intervals=[
            (_utc(2016, 1, 19, 15, 0), _utc(2016, 1, 19, 16, 0))
        ],
    )
    assert result.passed is True
    assert result.anomalies == ()
    covered = [
        g for g in result.gap_classifications if "SYNTHETIC_VENUE_HALT" in g.reason
    ]
    assert covered, "halt-covered gap must be classified with the halt label"
    # even covered, a halt NEVER authorizes a synthetic fill
    assert all(not g.synthetic_fill_allowed for g in covered)


def test_partially_covered_no_print_fails() -> None:
    halt = HaltInterval(
        start_utc=_utc(2016, 1, 19, 15, 0),
        end_utc=_utc(2016, 1, 19, 15, 30),
        label="PARTIAL_HALT",
    )
    result = calendar_check.reconcile_session_list(
        _round_trip(2016, 1),
        calendar=CAL,
        declared_halts=[halt],
        no_print_intervals=[
            (_utc(2016, 1, 19, 15, 0), _utc(2016, 1, 19, 16, 0))
        ],
    )
    assert result.passed is False
    assert "UNEXPLAINED_GAP" in {a.kind for a in result.anomalies}


def test_overnight_no_print_interval_is_a_return_not_a_bar() -> None:
    # from one close to the next open: fully outside regular sessions
    result = calendar_check.reconcile_session_list(
        _round_trip(2016, 1),
        calendar=CAL,
        no_print_intervals=[
            (_utc(2016, 1, 19, 21, 0), _utc(2016, 1, 20, 14, 30))
        ],
    )
    assert result.passed is True
    ok = [g for g in result.gap_classifications if "overnight" in g.reason.lower()
          or "outside regular sessions" in g.reason.lower()]
    assert ok and all(not g.synthetic_fill_allowed for g in ok)


# --- fail-closed helper ------------------------------------------------------------


def test_assert_sessions_reconciled_raises_on_fail() -> None:
    failing = calendar_check.reconcile_session_list(
        [date(2016, 1, 9)], calendar=CAL  # a Saturday
    )
    with pytest.raises(ValueError, match="calendar reconciliation failed"):
        calendar_check.assert_sessions_reconciled(failing)
    passing = calendar_check.reconcile_session_list(_round_trip(2016, 1), calendar=CAL)
    assert calendar_check.assert_sessions_reconciled(passing) is passing
