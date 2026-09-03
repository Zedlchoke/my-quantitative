"""Offline tests for the series gap audit (A2).

The session predicate is injected — tests use a Mon-Fri weekday lambda, never
an embedded calendar.
"""

import datetime as dt

import pytest

from research.stocks_free_v1.gap_audit import (
    audit_series,
    summarize_reports,
)


def weekday(d: dt.date) -> bool:
    return d.weekday() < 5  # Mon-Fri sessions; weekends are not


D = dt.date


def test_clean_series_has_no_findings():
    dates = [D(2026, 1, 2), D(2026, 1, 5), D(2026, 1, 6)]  # Fri, Mon, Tue
    values = [100.0, 101.0, 100.5]
    report = audit_series(dates, weekday, values)
    assert report.is_clean, [f.kind for f in report.findings]
    assert report.n_observations == 3
    assert report.span_days == 4


def test_empty_series_is_a_finding():
    report = audit_series([], weekday)
    assert not report.is_clean
    assert report.findings[0].kind == "EMPTY_SERIES"


def test_duplicate_dates_detected():
    dates = [D(2026, 1, 5), D(2026, 1, 5)]
    report = audit_series(dates, weekday)
    kinds = [f.kind for f in report.findings]
    assert "DUPLICATE_DATE" in kinds


def test_out_of_order_detected():
    dates = [D(2026, 1, 6), D(2026, 1, 5)]
    report = audit_series(dates, weekday)
    kinds = [f.kind for f in report.findings]
    assert "OUT_OF_ORDER" in kinds


def test_non_positive_and_missing_values_detected():
    dates = [D(2026, 1, 5), D(2026, 1, 6), D(2026, 1, 7)]
    report = audit_series(dates, weekday, [0.0, None, 5.0])
    kinds = sorted(f.kind for f in report.findings)
    assert kinds == ["MISSING_VALUE", "NON_POSITIVE_PRICE"]


def test_missing_session_detected_via_injected_predicate():
    # Mon 1/5 observed, Tue 1/6 absent, Wed 1/7 observed
    dates = [D(2026, 1, 5), D(2026, 1, 7)]
    report = audit_series(dates, weekday)
    missing = [f for f in report.findings if f.kind == "MISSING_SESSION"]
    assert len(missing) == 1
    assert "2026-01-06" in missing[0].detail


def test_weekend_gap_is_not_a_missing_session():
    # Fri 1/2 -> Mon 1/5 crosses a weekend the predicate excludes
    dates = [D(2026, 1, 2), D(2026, 1, 5)]
    report = audit_series(dates, weekday)
    assert report.is_clean


def test_gap_beyond_declared_tolerance_even_if_predicate_excludes():
    # two-week holiday the predicate wrongly claims is all non-session:
    # the declared calendar-day tolerance still fires (fail-closed)
    dates = [D(2026, 1, 2), D(2026, 1, 20)]
    report = audit_series(dates, lambda d: False, max_gap_calendar_days=14)
    kinds = [f.kind for f in report.findings]
    assert "GAP_BEYOND_TOLERANCE" in kinds
    gap = [f for f in report.findings if f.kind == "GAP_BEYOND_TOLERANCE"][0]
    assert "18 calendar days" in gap.detail


def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        audit_series([D(2026, 1, 5)], weekday, [1.0, 2.0])


def test_summarize_reports_aggregates():
    r1 = audit_series([D(2026, 1, 5), D(2026, 1, 6)], weekday, [1.0, 2.0])
    r2 = audit_series([], weekday)
    summary = summarize_reports([("SPY", r1), ("BAD", r2)])
    assert summary["clean"] is False
    assert summary["total_findings"] == 1
    assert summary["instruments"]["BAD"]["findings"][0]["kind"] == "EMPTY_SERIES"
