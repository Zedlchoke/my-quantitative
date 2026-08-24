"""Hand-checked unit fixtures for Sprint V4 portfolio metrics (A3, D1)."""

from __future__ import annotations

import math

import pytest

from research.portfolio_metrics import (
    MISSING_R_NORMALIZATION,
    btc_daily_returns_from_closes,
    daily_returns_from_equity_curve,
    expectancy_r_portfolio,
    fold_contribution,
    max_drawdown_from_equity,
    realized_btc_beta,
    turnover_from_orders,
    top_symbol_contribution,
)

DAY = 86_400_000_000_000
T0 = 1_758_479_400_000_000_000  # 2025-09-21T17:43:20Z-ish epoch ns anchor


def _ns(day_offset: int) -> int:
    return T0 + day_offset * DAY


# ------------------------------- beta --------------------------------------- #
def test_beta_perfect_two_to_one_slope():
    portfolio = {"2025-08-21": 0.02, "2025-08-22": -0.01, "2025-08-23": 0.04}
    btc = {"2025-08-21": 0.01, "2025-08-22": -0.005, "2025-08-23": 0.02}
    beta, reason = realized_btc_beta(portfolio, btc)
    assert reason is None
    assert beta == pytest.approx(2.0)


def test_beta_inverse_relationship():
    btc = {"2025-08-21": 0.02, "2025-08-22": -0.01}
    portfolio = {"2025-08-21": -0.02, "2025-08-22": 0.01}
    beta, _ = realized_btc_beta(portfolio, btc)
    assert beta == pytest.approx(-1.0)


def test_beta_aligns_by_utc_date_and_ignores_extra_days():
    portfolio = {"2025-08-21": 0.02, "2025-08-22": -0.01, "2025-08-24": 0.99}
    btc = {"2025-08-21T00:00:00Z": 0.01, "2025-08-22T00:00:00Z": -0.005,
           "2025-08-25": 0.50}
    beta, _ = realized_btc_beta(portfolio, btc)
    assert beta == pytest.approx(2.0)


def test_beta_insufficient_overlap_fail_closed():
    beta, reason = realized_btc_beta({"2025-08-21": 0.01}, {"2025-08-21": 0.02})
    assert beta is None and reason == "insufficient_overlap"
    beta, reason = realized_btc_beta({}, {})
    assert beta is None and reason == "insufficient_overlap"


def test_beta_zero_btc_variance_fail_closed():
    btc = {"2025-08-21": 0.01, "2025-08-22": 0.01}
    portfolio = {"2025-08-21": 0.05, "2025-08-22": -0.03}
    beta, reason = realized_btc_beta(portfolio, btc)
    assert beta is None and reason == "zero_btc_variance"


# --------------------------- return helpers --------------------------------- #
def test_daily_returns_last_sample_per_day():
    curve = [(_ns(0), 100.0), (_ns(0) + 3_600_000_000_000, 110.0), (_ns(1), 121.0)]
    returns = daily_returns_from_equity_curve(curve)
    assert set(returns) == {f"{_date(_ns(1))}"}
    assert returns[f"{_date(_ns(1))}"] == pytest.approx(0.10)


def _date(ns: int) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(ns / 1e9, tz=timezone.utc).strftime("%Y-%m-%d")


def test_btc_daily_returns_hand_checked():
    closes = [(_ns(0), 100.0), (_ns(1), 110.0), (_ns(2), 99.0)]
    returns = btc_daily_returns_from_closes(closes)
    assert returns[_date(_ns(1))] == pytest.approx(0.10)
    assert returns[_date(_ns(2))] == pytest.approx(-0.10)
    assert _date(_ns(0)) not in returns


# ------------------------------ turnover ------------------------------------ #
def test_turnover_sums_abs_notional_and_normalizes():
    orders = [
        {"quantity": 2.0, "fill_price": 50.0},
        {"quantity": -1.0, "fill_price": 70.0},
        {"quantity": 5.0, "fill_price": 10.0, "status": "CANCELLED"},
    ]
    assert turnover_from_orders(orders) == pytest.approx(170.0)
    assert turnover_from_orders(orders, equity=1000.0) == pytest.approx(0.17)


def test_turnover_executed_row_missing_fields_raises():
    with pytest.raises(ValueError):
        turnover_from_orders([{"quantity": 1.0}])


# ---------------------------- contributions --------------------------------- #
def test_top_symbol_positive_aggregate_denominator():
    legs = [
        {"symbol": "ETHUSDT", "canonical_pnl": 100.0},
        {"symbol": "ETHUSDT", "canonical_pnl": -30.0},
        {"symbol": "SOLUSDT", "canonical_pnl": 30.0},
        {"symbol": "XRPUSDT", "canonical_pnl": -50.0},
    ]
    symbol, share = top_symbol_contribution(legs)
    # positive aggregates: ETH 70, SOL 30 => denominator 100
    assert symbol == "ETHUSDT"
    assert share == pytest.approx(0.70)


def test_top_symbol_no_positive_pnl_yields_none():
    assert top_symbol_contribution([{"symbol": "A", "pnl": -5.0}]) == (None, 0.0)
    assert top_symbol_contribution([]) == (None, 0.0)


def test_fold_contribution_hand_checked():
    fold_id, share = fold_contribution({"f1": 60.0, "f2": 40.0, "f3": -10.0})
    assert fold_id == "f1" and share == pytest.approx(0.6)
    fold_id, share = fold_contribution({"f1": 50.0, "f2": 50.0})
    assert fold_id == "f1" and share == pytest.approx(0.5)
    assert fold_contribution({"f1": 0.0}) == (None, 0.0)


# ------------------------------ drawdown ------------------------------------ #
def test_mdd_fraction_and_recovery_duration():
    curve = [
        (_ns(0), 100.0),
        (_ns(1), 120.0),
        (_ns(2), 90.0),
        (_ns(3), 96.0),
        (_ns(4), 130.0),
        (_ns(5), 117.0),
    ]
    mdd, days = max_drawdown_from_equity(curve)
    assert mdd == pytest.approx(0.25)
    assert days == pytest.approx(3.0)  # peak day1 -> recovery day4


def test_mdd_unrecovered_episode_runs_to_curve_end():
    mdd, days = max_drawdown_from_equity([(_ns(0), 100.0), (_ns(1), 80.0)])
    assert mdd == pytest.approx(0.20)
    assert days == pytest.approx(1.0)


def test_mdd_flat_and_empty_curves():
    assert max_drawdown_from_equity([]) == (0.0, 0.0)
    mdd, days = max_drawdown_from_equity([(_ns(0), 10.0), (_ns(1), 11.0)])
    assert mdd == 0.0 and days == 0.0


def test_mdd_accepts_iso_timestamps():
    curve = [
        ("2025-08-21T00:00:00Z", 100.0),
        ("2025-08-22T00:00:00Z", 150.0),
        ("2025-08-23T00:00:00Z", 75.0),
    ]
    mdd, days = max_drawdown_from_equity(curve)
    assert mdd == pytest.approx(0.5)
    assert days == pytest.approx(1.0)


# ----------------------------- expectancy R --------------------------------- #
def test_expectancy_r_mean_of_leg_multiples():
    value, reason = expectancy_r_portfolio([0.5, -0.1, 0.4])
    assert value == pytest.approx(math.fsum([0.5, -0.1, 0.4]) / 3)
    assert reason is None


def test_expectancy_r_missing_normalization_documented():
    for payload in (None, []):
        value, reason = expectancy_r_portfolio(payload)
        assert value is None
        assert reason == MISSING_R_NORMALIZATION
