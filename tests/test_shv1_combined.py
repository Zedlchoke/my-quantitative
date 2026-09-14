"""Combined read-only view tests (plan sections 5, 9.3).

- combined = strict sum of isolated equities at valid marks;
- one sleeve mark-gap => combined gap with UNAVAILABLE_FAIL_CLOSED;
- overlap / correlation helpers on synthetic books;
- views hold no mutable references to sleeve snapshots.
"""

import copy

import pytest

from research.shadow_v1.combined import (
    GAP_STATUS,
    CombinedViewError,
    combined_equity_series,
    combined_exposures,
    pairwise_return_correlation,
    same_symbol_direction_overlap,
)


def _ok(ts, equity):
    return {"ts": ts, "status": "OK", "equity": equity, "missing_symbols": []}


def test_combined_is_strict_sum_of_isolated():
    sleeves = {
        "sleeve_illiq_amihud": [_ok("2026-01-05T00:00:00Z", 100_000.0), _ok("2026-01-06T00:00:00Z", 100_500.0)],
        "sleeve_basislv_premfade": [_ok("2026-01-05T00:00:00Z", 100_000.0), _ok("2026-01-06T00:00:00Z", 99_800.0)],
        "sleeve_xsect_fund_carry": [_ok("2026-01-05T00:00:00Z", 100_000.0), _ok("2026-01-06T00:00:00Z", 100_200.0)],
    }
    series = combined_equity_series(sleeves)
    assert len(series) == 2
    assert series[0] == {"ts": "2026-01-05T00:00:00Z", "status": "OK", "equity": 300_000.0, "by_sleeve": None}
    assert series[1]["status"] == "OK"
    assert series[1]["equity"] == 300_500.0


def test_one_sleeve_gap_makes_combined_gap_fail_closed():
    sleeves = {
        "a": [_ok("t1", 100.0), _ok("t2", 101.0), _ok("t3", 102.0)],
        "b": [
            _ok("t1", 200.0),
            {"ts": "t2", "status": GAP_STATUS, "equity": None, "missing_symbols": ["BTCUSDT"]},
            _ok("t3", 202.0),
        ],
    }
    series = combined_equity_series(sleeves)
    assert series[0]["status"] == "OK" and series[0]["equity"] == 300.0
    gap = series[1]
    assert gap["status"] == GAP_STATUS
    assert gap["equity"] is None  # no interpolated value anywhere
    assert gap["by_sleeve"]["b"]["reason"] == GAP_STATUS
    assert gap["by_sleeve"]["b"]["missing_symbols"] == ["BTCUSDT"]
    # recovery after the gap, never backfilled
    assert series[2]["status"] == "OK" and series[2]["equity"] == 304.0


def test_missing_point_at_timestamp_is_a_gap():
    sleeves = {
        "a": [_ok("t1", 100.0), _ok("t2", 101.0)],
        "b": [_ok("t1", 200.0)],
    }
    series = combined_equity_series(sleeves)
    assert series[1]["status"] == GAP_STATUS
    assert series[1]["by_sleeve"]["b"]["reason"] == "no_point_at_timestamp"


def test_correlation_perfect_positive_and_negative():
    # returns +10%, +20% (non-constant, so variance is non-zero)
    up = [_ok("t1", 100.0), _ok("t2", 110.0), _ok("t3", 132.0)]
    # returns -10%, -20%
    down = [_ok("t1", 100.0), _ok("t2", 90.0), _ok("t3", 72.0)]
    corr, reason = pairwise_return_correlation(up, up)
    assert reason == "OK" and corr == pytest.approx(1.0)
    corr_neg, _ = pairwise_return_correlation(up, down)
    assert corr_neg == pytest.approx(-1.0)


def test_correlation_fails_closed_on_gap_or_misalignment():
    up = [_ok("t1", 100.0), _ok("t2", 110.0), _ok("t3", 121.0)]
    gapped = [
        _ok("t1", 100.0),
        {"ts": "t2", "status": GAP_STATUS, "equity": None, "missing_symbols": ["X"]},
        _ok("t3", 121.0),
    ]
    corr, reason = pairwise_return_correlation(up, gapped)
    assert corr is None and "gap" in reason
    shorter = [_ok("t1", 100.0), _ok("t2", 110.0)]
    corr2, reason2 = pairwise_return_correlation(up, shorter)
    assert corr2 is None and "differ" in reason2
    corr3, reason3 = pairwise_return_correlation(shorter, shorter)
    assert corr3 is None and "NOT_RUN" in reason3


def test_overlap_helpers_on_synthetic_books():
    book_a = {"ETHUSDT": 0.10, "SOLUSDT": -0.10}
    book_b = {"ETHUSDT": 0.20, "XRPUSDT": -0.15, "SOLUSDT": 0.05}
    overlap = same_symbol_direction_overlap(book_a, book_b)
    assert overlap["shared_symbols"] == ["ETHUSDT", "SOLUSDT"]
    assert overlap["same_direction_symbols"] == ["ETHUSDT"]
    assert overlap["opposite_direction_symbols"] == ["SOLUSDT"]
    assert overlap["shared_notional_overlap_gross"] == pytest.approx(0.10 + 0.05)
    # empty intersection
    empty = same_symbol_direction_overlap(book_a, {"ADAUSDT": 0.1})
    assert empty["shared_symbols"] == []


def test_combined_exposures_additive_no_cross_netting():
    exposures = [
        {"status": "OK", "gross": 0.8, "net": 0.0, "btc_beta": -0.02},
        {"status": "OK", "gross": 1.0, "net": 0.05, "btc_beta": 0.03},
        {"status": "OK", "gross": 0.9, "net": -0.05, "btc_beta": 0.0},
    ]
    combined = combined_exposures(exposures)
    assert combined["gross"] == pytest.approx(2.7)  # magnitudes add
    assert combined["net"] == pytest.approx(0.0)
    assert combined["btc_beta"] == pytest.approx(0.01)


def test_combined_exposures_fail_closed_on_gap():
    exposures = [
        {"status": "OK", "gross": 0.8, "net": 0.0, "btc_beta": 0.0},
        {"status": GAP_STATUS, "gross": None, "net": None, "btc_beta": None},
    ]
    combined = combined_exposures(exposures)
    assert combined["status"] == GAP_STATUS
    assert combined["gross"] is None and combined["net"] is None


def test_view_cannot_mutate_source_snapshots():
    sleeves = {
        "a": [_ok("t1", 100.0), _ok("t2", 101.0)],
        "b": [_ok("t1", 200.0), _ok("t2", 202.0)],
    }
    snapshot = copy.deepcopy(sleeves)
    series = combined_equity_series(sleeves)
    captured = copy.deepcopy(series)
    # mutate the caller's snapshots AFTER the view was computed
    sleeves["a"][0]["equity"] = 999_999.0
    sleeves["a"].append(_ok("t3", 500.0))
    sleeves["b"].clear()
    # captured view is unchanged
    assert series == captured
    # and a recomputation over the ORIGINAL deep snapshot matches
    assert combined_equity_series(snapshot) == captured
    # inputs were not mutated by the view function itself
    assert snapshot["a"][0]["equity"] == 100.0


def test_view_requires_timestamps():
    with pytest.raises(CombinedViewError):
        combined_equity_series({"a": [{"equity": 1.0}]})
