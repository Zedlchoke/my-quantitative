"""Mock classifier canaries vs the frozen synthetic fixtures; schema laws."""

from __future__ import annotations

import json

import numpy as np
import pytest

from jrv1.decisions import validate_response_line
from jrv1.mock_adapter import MOCK_MODEL, MOCK_NAMESPACE, mock_decide, mock_rule

LABELS = ["ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND", "TRANSITION_UNKNOWN"]


def test_canary_fixtures_mock_labels_within_acceptable_sets(fz):
    law = fz.canary_fixtures
    assert law["feature_order"] == [
        "r1", "r4", "r12", "r24", "r72", "ema_slope_fast", "ema_slope_slow",
        "dist_ema", "adx14", "atr_pct", "rv_pctile", "dd_168", "dist_low",
        "range_pos", "vol_z", "clv_24",
    ]
    results = {}
    for fx in law["fixtures"]:
        if fx["vector"] is None:
            results[fx["id"]] = "LOCAL_INVALID"
            continue
        label = mock_rule(fx["vector"])
        results[fx["id"]] = label
        assert label in fx["expected_acceptable"], (fx["id"], label)
    assert results["FIX6_MISSING_STALE"] == "LOCAL_INVALID"
    # directional fixtures not absurdly inverted
    assert results["FIX1_CLEAR_UPTREND"] == "UPTREND"
    assert results["FIX2_CLEAR_DOWNTREND"] == "DOWNTREND"


def test_mock_response_schema_valid_and_namespaced():
    payload = {"feature_vector": fz_vector(), "prior_regime": None}
    resp = mock_decide("a" * 16, payload)
    assert resp["model"] == MOCK_MODEL
    assert resp["namespace"] == MOCK_NAMESPACE
    n, v = validate_response_line(resp, "a" * 16, resp["input_digest"], pinned_model=None)
    assert v is None and n["status"] == "OK"
    # probabilities sum exactly to 1
    assert sum(resp["probabilities"].values()) == pytest.approx(1.0, abs=1e-9)
    # margin exactly 0.30 (>= frozen 0.20)
    vals = sorted(resp["probabilities"].values(), reverse=True)
    assert vals[0] - vals[1] == pytest.approx(0.30, abs=1e-9)
    assert len(resp["state_id"]) == 16


def test_mock_unknown_response_is_persistence_ineligible():
    vec = [0.001, 0.004, 0.003, 0.012, 0.07, 0.0002, 0.0001, 0.1, 19.0, 0.007, 0.5, -0.01, 0.05, 0.2, 0.1, 0.5]
    resp = mock_decide("b" * 16, {"feature_vector": vec, "prior_regime": None})
    assert resp["regime"] == "TRANSITION_UNKNOWN"
    assert resp["confidence"] == 0.40  # below the frozen 0.50 floor
    from jrv1.persistence import raw_from_response

    raw, eligible = raw_from_response(
        resp, {"min_confidence": 0.5, "min_margin": 0.2}
    )
    assert raw == "TRANSITION_UNKNOWN" and eligible is False


def test_mock_deterministic_across_calls():
    vec = {"feature_vector": fz_vector(), "prior_regime": "UPTREND"}
    a = mock_decide("c" * 16, vec)
    b = mock_decide("c" * 16, dict(vec))
    assert a == b  # no RNG state, hash-seeded only


def fz_vector():
    return [0.004, 0.02, 0.05, 0.11, 0.28, 0.004, 0.0025, 1.2, 34.0, 0.008, 0.62, -0.03, 0.3, 0.42, 0.35, 0.62]


def test_metrics_suite_shapes(fz):
    from conftest import make_bars
    from jrv1.arms import AssetContext, run_arm_B
    from jrv1.engine import CostModel
    from jrv1.metrics import compute_arm_metrics, margin_to_fail, max_drawdown
    from jrv1.strategies import TREND_LONG

    close = 100 * (1 + 0.008) ** np.arange(260)
    bars = make_bars(close, close * 1.002, close * 0.998, close, np.ones(260))
    ctx = AssetContext(
        asset="btcusdt", exec_bars=bars, regime_period_ns=3600 * 10**9,
        mapping={"UPTREND": TREND_LONG}, folds_exec=[(0, 100, 259)],
        costs=CostModel(5.0, 1.0), periods_per_year=35064.0,
    )
    res, m = run_arm_B(ctx)
    full = compute_arm_metrics(res, bars, ctx.periods_per_year, timeline_labels=["UPTREND"] * 260)
    for key in (
        "gross_pnl", "costs_fee", "costs_slip", "costs_funding", "net_pnl",
        "total_return", "cagr", "sharpe", "sortino", "max_drawdown",
        "profit_factor", "expectancy_per_trade", "trades", "win_rate",
        "turnover", "time_in_market", "regime_switches", "regime_occupancy",
        "avg_dwell", "unknown_share", "fold_by_fold_net_pnl",
        "concentration_top_fold_profit_share", "skipped_trade_pnl_fraction",
    ):
        assert key in full, key
    assert max_drawdown(res.equity) <= 0.0
    # margin-to-fail measurable with >=2 folds of distinct deltas
    mt = margin_to_fail([1.0, 2.0], [0.5, 0.5], 3.0, 1.0)
    assert mt is not None and mt > 0
    assert margin_to_fail([1.0], [1.0], 0.0, 0.0) is None  # unmeasurable -> None


def test_skipped_trade_pnl_hand_computed():
    from conftest import make_bars
    from jrv1.metrics import skipped_trade_pnl

    # 6 bars: FLAT segment bars 1..4 (targets), entry at open1=100, exit close4=110
    close = [90.0, 100.0, 105.0, 110.0, 110.0, 120.0]
    bars = make_bars(close, close, close, close, np.ones(6))
    targets = ["UPTREND", "FLAT", "FLAT", "FLAT", "FLAT", "UPTREND"]
    c = 0.001  # 10 bps per side
    got = skipped_trade_pnl(bars, targets, c)
    seg = 110.0 / 100.0 - 1.0
    expect = (1 + seg) * (1 - c) * (1 - c) - 1.0
    assert got == pytest.approx(expect, rel=1e-12)
