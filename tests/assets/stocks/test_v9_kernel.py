"""V9 P1 kernel primitive tests: hand-computed fixtures only (handbook
sec 14.2). No production outcome, no real S0 data, no profitability pins."""

import pytest

from research.assets.stocks.kernel_band_cost_v9 import (
    BAND_BPS,
    BandResolutionError,
    append_publication_record,
    band_of,
    driver_ledger_counters,
    fill_cost_bps,
    resolve_band_bps,
)


def test_band_of_thresholds_hand_computed():
    assert band_of(50_000_000) == "A"
    assert band_of(49_999_999) == "B"
    assert band_of(10_000_000) == "B"
    assert band_of(9_999_999) == "C"
    assert band_of(2_000_000) == "C"
    assert band_of(1_999_999) == "UNTRADABLE"


def test_resolve_band_passthrough():
    assert resolve_band_bps("X", {"X": "A"}) == 10.0
    assert resolve_band_bps("Y", {"X": "A", "Y": "C"}) == 25.0


def test_missing_band_fails_closed_L_I3():
    with pytest.raises(BandResolutionError):
        resolve_band_bps("DEAD_MID_FOLD", {"OTHER": "A"})


def test_untradable_reaching_costing_is_caller_bug():
    with pytest.raises(BandResolutionError):
        resolve_band_bps("X", {"X": "UNTRADABLE"})


def test_fill_cost_linear_once_hand_computed():
    # 0.25 weight change at band B (15 bps), multiplier 1.0
    assert fill_cost_bps("X", 0.25, {"X": "B"}, 1.0) == pytest.approx(0.25 * 15.0 / 10_000.0)
    # negative direction priced identically (abs)
    assert fill_cost_bps("X", -0.25, {"X": "B"}, 1.0) == pytest.approx(0.25 * 15.0 / 10_000.0)
    # stress tier 2.0 doubles
    assert fill_cost_bps("X", 0.10, {"X": "A"}, 2.0) == pytest.approx(0.10 * 10.0 * 2.0 / 10_000.0)


def test_band_table_matches_inherited_semantics():
    assert BAND_BPS == {"A": 10.0, "B": 15.0, "C": 25.0}


def test_driver_counters_and_publication_record():
    counters = driver_ledger_counters(observed_delta=6, published_delta=0)
    assert counters["observed_delta"] == 6
    assert counters["published_delta"] == 0
    with pytest.raises(ValueError):
        driver_ledger_counters(observed_delta=6, published_delta=7)
    rec = append_publication_record(None, at="T1", delta=6)
    rec = append_publication_record(rec, at="T2", delta=0)
    assert [r["at"] for r in rec["publication_records"]] == ["T1", "T2"]
