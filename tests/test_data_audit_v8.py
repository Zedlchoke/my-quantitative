"""Unit tests for the T12 V8P data audit (synthetic fixtures only, owner A2)."""

from __future__ import annotations

import pytest

from research.data_audit_v8 import (
    INTERVAL_NS,
    classify_gaps,
    duplicate_count,
    evaluate_materiality,
    funding_stats_for_window,
    gap_census,
    intersection_endpoints,
    monotonic_strict,
    ns_to_iso,
    ohlc_violations,
    parse_iso_ns,
)
from research.panel import parse_iso_ns as panel_parse_iso_ns

BASE_NS = panel_parse_iso_ns("2025-01-01T00:00:00Z")


def _series(count: int, base_ns: int = BASE_NS) -> list[int]:
    # Binance-style close stamps ~61ms before each nominal grid boundary.
    return [base_ns + (i + 1) * INTERVAL_NS - 61_000_064 for i in range(count)]


# --------------------------------------------------------------------------- #
# Duplicate detection / monotonicity
# --------------------------------------------------------------------------- #
def test_duplicate_detection_counts_repeated_timestamps():
    stamps = _series(6)
    stamps_with_dupes = stamps + [stamps[2], stamps[2], stamps[4]]
    assert duplicate_count(stamps) == 0
    assert duplicate_count(stamps_with_dupes) == 3


def test_monotonic_strict_flags_equal_and_descending():
    assert monotonic_strict(_series(5))
    duped = _series(3)
    assert not monotonic_strict([duped[0], duped[0], duped[1]])
    assert not monotonic_strict([duped[2], duped[1], duped[0]])


# --------------------------------------------------------------------------- #
# Gap census + classification
# --------------------------------------------------------------------------- #
def _series_with_gap(count_a: int, missing_slots: int, count_b: int) -> list[int]:
    indices = list(range(1, count_a + 1)) + list(
        range(count_a + missing_slots + 1, count_a + missing_slots + 1 + count_b)
    )
    return [BASE_NS + i * INTERVAL_NS - 61_000_064 for i in indices]


def test_gap_census_finds_gap_and_missing_slots():
    stamps = _series_with_gap(4, missing_slots=8, count_b=3)
    gaps = gap_census(stamps)
    assert len(gaps) == 1
    gap = gaps[0]
    assert gap["missing_grid_slots"] == 8
    assert abs(gap["missing_hours"] - 2.0) < 1e-6
    clean = gap_census(_series(10))
    assert clean == []


def test_gap_classifier_defaults_to_unexplained():
    stamps = _series_with_gap(4, missing_slots=4, count_b=2)
    gaps = gap_census(stamps)
    classified, totals = classify_gaps(gaps, rules=None)
    assert totals == {"explained": 0, "unexplained": 1}
    assert classified[0]["classification"] == "unexplained"
    assert classified[0]["matched_rule"] is None


def test_gap_classifier_explained_only_with_preregistered_rule():
    stamps = _series_with_gap(4, missing_slots=4, count_b=2)
    gaps = gap_census(stamps)
    after = parse_iso_ns(str(gaps[0]["after_ts_utc"]))
    before = parse_iso_ns(str(gaps[0]["before_ts_utc"]))
    rules = [
        {
            "rule_id": "declared_maintenance",
            "windows": [(after - 1, before + 1)],
        }
    ]
    classified, totals = classify_gaps(gaps, rules=rules)
    assert totals["explained"] == 1
    assert classified[0]["matched_rule"] == "declared_maintenance"
    partial_rules = [{"rule_id": "too_narrow", "windows": [(after + 1, before + 1)]}]
    classified2, totals2 = classify_gaps(gaps, rules=partial_rules)
    assert totals2["unexplained"] == 1
    assert classified2[0]["matched_rule"] is None


# --------------------------------------------------------------------------- #
# OHLC validity
# --------------------------------------------------------------------------- #
def _row(ts: int, o: float, h: float, low: float, c: float, v: float):
    return (ts, o, h, low, c, v)


def test_ohlc_validity_clean_rows_pass():
    ts = BASE_NS
    rows = [_row(ts, 100.0, 101.0, 99.0, 100.5, 12.0)]
    assert all(v == 0 for v in ohlc_violations(rows).values())


def test_ohlc_validity_flags_each_violation_class():
    ts = BASE_NS
    rows = [
        _row(ts, 10.0, 9.0, 11.0, 10.5, -1.0),
        _row(ts + 1, 10.0, 9.5, 10.2, 10.4, 1.0),
        _row(ts + 2, 0.0, 1.0, 0.5, 0.8, 1.0),
    ]
    counts = ohlc_violations(rows)
    assert counts["high_lt_low"] >= 1
    assert counts["negative_volume"] == 1
    assert counts["nonpositive_price"] == 1


# --------------------------------------------------------------------------- #
# Funding coverage math
# --------------------------------------------------------------------------- #
def _bundle(rows_ms: list[int]) -> dict:
    return {
        "requested_start_ms": min(rows_ms),
        "requested_end_ms": max(rows_ms),
        "rows": [
            {"fundingTime": t, "fundingRate": "0.00010000", "markPrice": "1.0"}
            for t in rows_ms
        ],
    }


def test_funding_coverage_counts_window_and_missing_estimate():
    eight_h = 8 * 3_600_000
    start_ms = BASE_NS // 1_000_000
    times = [start_ms + i * eight_h for i in range(30)]
    del times[10]  # one dropped settlement inside the window
    payload = _bundle(times)
    win_start = times[0]
    win_end = times[-1] + eight_h // 2  # half-open-ish end mid-cadence
    stats = funding_stats_for_window(payload, win_start, win_end)
    assert stats["settlements_in_window"] == 29
    assert stats["settlement_interval_hours"] == 8.0
    assert stats["expected_settlements_in_window"] == 30
    assert stats["missing_settlements_estimate"] == 1
    assert stats["coverage_ratio"] == pytest.approx(29 / 30, abs=1e-6)
    assert stats["head_uncovered_hours"] == 0.0
    assert stats["tail_uncovered_hours"] == pytest.approx(4.0)


def test_funding_coverage_head_uncovered_hours_ms_scale():
    eight_h = 8 * 3_600_000
    start_ms = BASE_NS // 1_000_000
    times = [start_ms + i * eight_h for i in range(10)]
    payload = _bundle(times)
    stats = funding_stats_for_window(payload, start_ms - 32 * 3_600_000, times[-1])
    assert stats["head_uncovered_hours"] == pytest.approx(32.0)
    assert stats["tail_uncovered_hours"] == 0.0


def test_funding_coverage_zero_when_bundle_empty():
    payload = {"requested_start_ms": 0, "requested_end_ms": 1, "rows": []}
    stats = funding_stats_for_window(payload, 0, 1_000_000)
    assert stats["settlements_in_window"] == 0
    assert stats["coverage_ratio"] is None


def test_funding_coverage_window_before_first_settlement():
    eight_h = 8 * 3_600_000
    times = [BASE_NS // 1_000_000 + i * eight_h for i in range(10)]
    payload = _bundle(times)
    stats = funding_stats_for_window(payload, times[0] - eight_h * 10, times[0] - eight_h * 5)
    assert stats["settlements_in_window"] == 0
    assert stats["expected_settlements_in_window"] == 0
    assert stats["missing_settlements_estimate"] == 0
    assert stats["head_uncovered_hours"] == pytest.approx(40.0)
    assert stats["tail_uncovered_hours"] == pytest.approx(40.0)


# --------------------------------------------------------------------------- #
# Intersection logic
# --------------------------------------------------------------------------- #
def test_intersection_endpoints_measured_from_data():
    ranges = {
        "A": (100, 900),
        "B": (150, 800),
        "C": (200, 850),
    }
    start, end = intersection_endpoints(ranges)
    assert (start, end) == (200, 800)


def test_intersection_endpoints_none_without_data():
    assert intersection_endpoints({}) == (None, None)
    assert intersection_endpoints({"A": (None, None)}) == (None, None)  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# Frozen gate rule
# --------------------------------------------------------------------------- #
def test_materiality_boundary_exactly_24h_does_not_fail():
    failed, reasons = evaluate_materiality(
        required=True,
        bar_count_in_window=70_000,
        funding_settlements_in_window=2100,
        duplicate_timestamps=0,
        unexplained_gap_hours=24.0,
        window_hours=17_000,
    )
    assert not failed and reasons == []


def test_materiality_fails_above_thresholds():
    failed, reasons = evaluate_materiality(
        required=True,
        bar_count_in_window=70_000,
        funding_settlements_in_window=2100,
        duplicate_timestamps=0,
        unexplained_gap_hours=25.0,
        window_hours=4_000,
    )
    assert failed and reasons == ["unexplained_gaps_material"]
    failed_frac, _ = evaluate_materiality(
        required=True,
        bar_count_in_window=70_000,
        funding_settlements_in_window=2100,
        duplicate_timestamps=0,
        unexplained_gap_hours=48.0,
        window_hours=9_000,
    )
    assert failed_frac


def test_materiality_large_hours_but_tiny_fraction_does_not_fail():
    failed, _ = evaluate_materiality(
        required=True,
        bar_count_in_window=70_000,
        funding_settlements_in_window=2100,
        duplicate_timestamps=0,
        unexplained_gap_hours=30.0,
        window_hours=20_000,
    )
    assert not failed


def test_materiality_absent_bars_or_funding_or_dupes_fail():
    for kwargs, expected_reason in (
        ({"bar_count_in_window": 0}, "bars_absent_in_common_window"),
        ({"funding_settlements_in_window": 0}, "funding_settlements_zero_in_common_window"),
        ({"duplicate_timestamps": 2}, "duplicate_timestamps_present"),
    ):
        merged = dict(
            bar_count_in_window=100,
            funding_settlements_in_window=100,
            duplicate_timestamps=0,
            unexplained_gap_hours=0.0,
            window_hours=100.0,
        )
        merged.update(kwargs)
        failed, reasons = evaluate_materiality(required=True, **merged)  # type: ignore[arg-type]
        assert failed and expected_reason in reasons


def test_materiality_benchmark_not_required_never_fails():
    failed, reasons = evaluate_materiality(
        required=False,
        bar_count_in_window=0,
        funding_settlements_in_window=0,
        duplicate_timestamps=99,
        unexplained_gap_hours=999.0,
        window_hours=1.0,
    )
    assert not failed and reasons == []


# --------------------------------------------------------------------------- #
# Misc helpers
# --------------------------------------------------------------------------- #
def test_ns_to_iso_roundtrip_matches_panel_parser():
    ns = BASE_NS + 123_456_789
    iso = ns_to_iso(ns)
    assert parse_iso_ns(iso) == (ns // 1000) * 1000
