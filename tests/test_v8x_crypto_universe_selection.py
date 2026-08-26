"""Unit tests for the corrected V8X/A8 crypto universe-selection logic.

Pure-function coverage over synthetic data only (offline, no catalog access):
15m slot mapping, exact gap census classification, funding held-exposure
completeness gates, pre-window median metric and deterministic ranking.
"""

import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import v8x_crypto_universe_selection as sel  # noqa: E402


def ns_at(slot_open_s: int) -> int:
    """ns timestamp as stamped locally: slot close minus ~0.1 ms."""
    return (slot_open_s + sel.BAR_INTERVAL_S) * 1_000_000_000 - 100_000


class TestSlotMapping:
    def test_close_minus_100us_maps_to_own_slot(self):
        opens = sel.slot_opens_from_ts_event(
            np.array([ns_at(1753142400), ns_at(1753143300)], dtype=np.int64))
        assert list(opens) == [1753142400, 1753143300]

    def test_empty_input(self):
        assert sel.slot_opens_from_ts_event(np.empty(0, dtype=np.int64)).size == 0


class TestGapCensus:
    def test_full_grid_has_no_gaps(self):
        obs = np.arange(1753142400, 1755734400, 900, dtype=np.int64)
        n_exp, runs = sel.gap_runs(obs, 1753142400, 1755734400)
        assert n_exp == 2880 and runs == []

    def test_missing_run_detected_with_extent(self):
        obs = np.arange(1753142400, 1755734400, 900, dtype=np.int64)
        obs = obs[(obs < 1753200000) | (obs > 1753218000)]  # hole of 21 slots
        _, runs = sel.gap_runs(obs, 1753142400, 1755734400)
        assert len(runs) == 1
        assert runs[0]["slots"][0] == 1753200000
        assert len(runs[0]["slots"]) == 21

    def test_hole_between_sessions_is_explained_boundary(self):
        sessions = [(1753000000, 1753199900, 0), (1753220000, 1755700000, 1)]
        cls = sel.classify_run([1753200000 + i * 900 for i in range(3)], sessions)
        assert cls["explained"] is True
        assert cls["cause"] == "local_capture_boundary_between_sessions"

    def test_hole_inside_one_session_is_unexplained(self):
        sessions = [(1753100000, 1755700000, 0)]
        cls = sel.classify_run([1753200000 + i * 900 for i in range(3)], sessions)
        assert cls["explained"] is False
        assert cls["cause"] == "unexplained_hole_inside_single_capture_session"


def eight_hour_rows(start_ms: int, end_ms: int, drop_at_ms=None):
    rows, t = [], start_ms
    while t <= end_ms:
        if drop_at_ms is None or t != drop_at_ms:
            rows.append({"fundingTime": t})
        t += 8 * 3600 * 1000
    return rows


SPAN_START_MS = sel.SCORED_START_S * 1000
SPAN_END_MS = sel.SCORED_END_S * 1000


class TestFundingHeldExposureCompleteness:
    def test_complete_8h_grid_passes_all_gates(self):
        rows = eight_hour_rows(SPAN_START_MS - 28800000, SPAN_END_MS)
        res = sel.analyze_funding(rows, {})
        assert res["complete"] is True
        assert res["gate_sorted_unique_f1"] and res["gate_legal_intervals_f2"]
        assert res["gate_boundary_coverage_f3"]

    def test_dropped_settlement_breaks_proof(self):
        victim = SPAN_START_MS + 40 * 28800000
        rows = eight_hour_rows(SPAN_START_MS - 28800000, SPAN_END_MS,
                               drop_at_ms=victim)
        res = sel.analyze_funding(rows, {})
        assert res["gate_legal_intervals_f2"] is False
        assert res["complete"] is False

    def test_isolated_sub8h_step_without_corroboration_fails(self):
        rows = [{"fundingTime": t} for t in
                range(SPAN_START_MS - 14400000, SPAN_END_MS + 1, 14400000)]
        del rows[50]  # single missing 4h settlement -> one isolated 8h step
        res = sel.analyze_funding(rows, {})
        assert res["flagged_interval_steps"]
        assert res["flagged_interval_steps"][0]["explained"] is False
        assert res["complete"] is False

    def test_corroborated_exchange_wide_step_passes(self):
        rows = [{"fundingTime": t} for t in
                range(SPAN_START_MS - 14400000, SPAN_END_MS + 1, 14400000)]
        del rows[50]
        res = sel.analyze_funding(rows, {(rows[49]["fundingTime"],
                                         rows[50]["fundingTime"]): 4})
        assert res["complete"] is True
        assert res["flagged_interval_steps"][0][
            "cause"] == "exchange_wide_funding_interval_step"


class TestMetricAndRanking:
    def test_median_even_count_decimal_exact(self):
        vol = {
            "days_with_bars_pre_window": 2,
            "median_daily_quote_volume_usdt_exact": str((Decimal("10") + Decimal("30")) / 2),
        }
        assert vol["median_daily_quote_volume_usdt_exact"] == "20"

    def test_ranking_desc_then_symbol_asc_and_top_n(self):
        cands = [
            {"symbol": "BBB", "volume": {"median_daily_quote_volume_usdt_exact": "5"}},
            {"symbol": "AAA", "volume": {"median_daily_quote_volume_usdt_exact": "7"}},
            {"symbol": "ZZZ", "volume": {"median_daily_quote_volume_usdt_exact": "7"}},
            {"symbol": "CCC", "volume": {"median_daily_quote_volume_usdt_exact": "6"}},
        ]
        chosen, ranked = sel.rank_and_select(cands, top_n=3)
        assert [c["symbol"] for c in ranked] == ["AAA", "ZZZ", "CCC", "BBB"]
        assert [c["symbol"] for c in chosen] == ["AAA", "ZZZ", "CCC"]

    def test_tie_on_identical_volume_uses_symbol_asc(self):
        cands = [
            {"symbol": "B", "volume": {"median_daily_quote_volume_usdt_exact": "1"}},
            {"symbol": "A", "volume": {"median_daily_quote_volume_usdt_exact": "1"}},
        ]
        chosen, _ = sel.rank_and_select(cands, top_n=1)
        assert chosen[0]["symbol"] == "A"


class TestFrozenContractConstants:
    def test_windows_are_strictly_ordered(self):
        assert sel.PRE_START_S < sel.PRE_END_S
        assert sel.PRE_END_S == sel.SCORED_START_S
        assert sel.SCORED_START_S < sel.SCORED_END_S

    def test_btc_symbol_excluded_constant(self):
        assert sel.BTC_SYMBOL == "BTCUSDT"
