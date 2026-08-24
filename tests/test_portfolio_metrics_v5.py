"""Sprint V5 family-aware portfolio metrics (PLAN section 31.4, owner A3).

Fixtures pin the F01/F02/F03 defects:

* top-symbol share of ~64.4% must compute 0.644 -- NEVER 0 (F02);
* reset-fold curves cannot pass the continuous-MDD check (F03);
* contribution identities fail closed via ContributionMismatch (F01).
"""

from __future__ import annotations

import pytest

from research.portfolio_metrics import (
    CHAINED_MDD_ESTIMATOR,
    CONTRIBUTION_TOLERANCE,
    DAILY_SHARPE_ESTIMATOR,
    MEDIAN_FOLD_RETURN_ESTIMATOR,
    ContributionMismatch,
    chain_fold_segments,
    chained_returns_mdd,
    daily_sharpe,
    max_drawdown_from_equity,
    median_fold_return,
    per_fold_contribution,
    per_symbol_contribution,
)

DAY = 86_400_000_000_000


# ----------------------------- daily sharpe --------------------------------- #
def test_daily_sharpe_estimator_id_frozen():
    assert DAILY_SHARPE_ESTIMATOR == "DAILY_SHARPE_RF0_V1"


def test_daily_sharpe_from_plain_returns_hand_computed():
    returns = [0.01, 0.02, -0.005, 0.03, -0.01]
    value, reason = daily_sharpe(returns)
    assert reason is None
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assert value == pytest.approx(mean / (var**0.5))


def test_daily_sharpe_rf_subtracted():
    flat = [0.05, 0.05, 0.05]
    assert daily_sharpe(flat)[1] == "zero_variance"
    value, reason = daily_sharpe([0.06, 0.06, 0.04], rf=0.04)
    assert reason == "zero_variance" or value is not None
    # rf exactly equal to every return removes all variance -> zero_variance
    value2, reason2 = daily_sharpe([0.04, 0.04], rf=0.04)
    assert value2 is None and reason2 == "zero_variance"
    del value, reason


def test_daily_sharpe_from_equity_curve_matches_returns_path():
    growth = [1.0, 1.01, 0.995, 1.02, 1.005]
    curve = [(i * DAY, 100_000.0 * g) for i, g in enumerate(growth)]
    from_curve, reason_curve = daily_sharpe(curve)
    direct_returns = [
        growth[i + 1] / growth[i] - 1.0 for i in range(len(growth) - 1)
    ]
    direct, _ = daily_sharpe(direct_returns)
    assert reason_curve is None
    assert from_curve == pytest.approx(direct)


def test_daily_sharpe_fail_closed_degenerate_inputs():
    assert daily_sharpe([]) == (None, "insufficient_observations")
    assert daily_sharpe([0.01]) == (None, "insufficient_observations")
    assert daily_sharpe([0.01, 0.01]) == (None, "zero_variance")


def test_daily_sharpe_from_mapping_keyed_by_date():
    mapping = {"2026-08-01": 0.01, "2026-08-02": -0.01}
    value, reason = daily_sharpe(mapping)
    assert reason is None and value == pytest.approx(0.0)


# -------------------------- median fold return ------------------------------ #
def test_median_fold_return_estimator_id_and_values():
    assert MEDIAN_FOLD_RETURN_ESTIMATOR == "MEDIAN_FOLD_RETURN_V1"
    assert median_fold_return([0.10, -0.02, 0.04]) == pytest.approx(0.04)
    assert median_fold_return([0.10, -0.02, 0.04, 0.30]) == pytest.approx(0.07)
    assert median_fold_return([]) is None
    assert median_fold_return([None, None]) is None


def test_median_fold_return_negative_blocks_gate_style_usage():
    # A portfolio whose typical fold LOSES money cannot be rescued by one
    # lucky outlier fold: median stays negative.
    assert median_fold_return([-0.30, -0.20, 0.50]) == pytest.approx(-0.20)


# --------------------------- contributions ---------------------------------- #
def test_top_symbol_share_64p4_fixture_computes_0644_not_zero():
    """F02 regression: MOM-7D true top share was ~64.4% yet artifacts said 0%."""
    legs = [
        {"symbol": "BTCUSDT", "canonical_pnl": 64_400.0},
        {"symbol": "ETHUSDT", "canonical_pnl": 20_000.0},
        {"symbol": "SOLUSDT", "canonical_pnl": 10_000.0},
        {"symbol": "XRPUSDT", "canonical_pnl": 5_600.0},
        {"symbol": "DOGEUSDT", "canonical_pnl": -12_345.0},
    ]
    total_pnl = 64_400 + 20_000 + 10_000 + 5_600 - 12_345
    shares = per_symbol_contribution(
        legs, total_pnl=total_pnl,
        population=["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"],
    )
    # positive aggregate denominator = 100k -> BTC share exactly 0.644
    assert shares["BTCUSDT"] == pytest.approx(0.644)
    assert shares["BTCUSDT"] != 0.0


def test_per_symbol_contribution_requires_canonical_field_no_silent_fallback():
    legs = [{"symbol": "BTCUSDT", "realized_pnl": 500.0}]  # wrong field name
    with pytest.raises(ContributionMismatch):
        per_symbol_contribution(legs, total_pnl=500.0)


def test_per_symbol_contribution_mismatch_raises():
    legs = [{"symbol": "A", "canonical_pnl": 60.0}, {"symbol": "B", "canonical_pnl": 40.0}]
    with pytest.raises(ContributionMismatch):
        per_symbol_contribution(legs, total_pnl=150.0)  # reported total lies


def test_per_symbol_contribution_leg_outside_population_raises():
    legs = [{"symbol": "C", "canonical_pnl": 10.0}]
    with pytest.raises(ContributionMismatch):
        per_symbol_contribution(legs, total_pnl=10.0, population=["A", "B"])


def test_per_symbol_contribution_population_symbols_without_legs_included():
    legs = [{"symbol": "A", "canonical_pnl": 30.0}]
    shares = per_symbol_contribution(
        legs, total_pnl=30.0, population=["A", "B"]
    )
    assert shares["A"] == pytest.approx(1.0)
    assert "B" not in shares  # zero-aggregate symbol earns no positive share


def test_per_symbol_contribution_tight_tolerance():
    legs = [{"symbol": "A", "canonical_pnl": 1e9}, {"symbol": "B", "canonical_pnl": 1.0}]
    # scale = 1e9 -> allowed drift 1.0; a 2.0 drift must raise
    with pytest.raises(ContributionMismatch):
        per_symbol_contribution(legs, total_pnl=1e9 + 3.0)
    ok = per_symbol_contribution(legs, total_pnl=1e9 + 1.0 + CONTRIBUTION_TOLERANCE)
    assert ok["A"] > 0


def test_per_fold_contribution_identity_and_mismatch():
    folds = {"f1": 50.0, "f2": 30.0, "f3": -20.0}
    shares = per_fold_contribution(folds, total_pnl=60.0)
    assert shares["f1"] == pytest.approx(50.0 / 80.0)
    with pytest.raises(ContributionMismatch):
        per_fold_contribution({"f1": 50.0}, total_pnl=99.0)
    with pytest.raises(ContributionMismatch):
        per_fold_contribution(folds, total_pnl=60.0, population=["f1", "f2"])


# ------------------------- chained WFA drawdown ----------------------------- #
def test_chained_mdd_estimator_id_frozen():
    assert CHAINED_MDD_ESTIMATOR == "CHAINED_FOLD_RETURNS_MDD_V1"


def test_reset_fold_curve_cannot_pass_continuous_mdd_check():
    """F03 regression: two reset folds each down 20%/25% look like 25% MDD on a
    naive concatenated-reset curve, but the TRUE walk-forward path lost 40%."""
    starts = [100_000.0, 100_000.0]
    series = [[-0.20], [-0.25]]
    true_mdd = chained_returns_mdd(starts, series)
    assert true_mdd == pytest.approx(0.40)

    # The defect: naive per-fold reset curves stitched together hide it.
    def _reset_segment(start, ret):
        return [(0, float(start)), (DAY, start * (1.0 + ret))]

    naive_segments = [_reset_segment(s, r[0]) for s, r in zip(starts, series)]
    naive_curves = []
    offset = 0
    for seg in naive_segments:
        naive_curves.extend([(ts + offset * 2 * DAY, eq) for ts, eq in seg])
        offset += 1
    hidden_mdd, _ = max_drawdown_from_equity(naive_curves)
    assert hidden_mdd < 0.26  # what the V4 artifact would have reported
    assert true_mdd > hidden_mdd + 0.10


def test_chained_returns_mdd_recovery_between_folds_not_double_counted():
    # Fold 1 loses 10%, fold 2 gains 25% back: chained path ends above start.
    mdd = chained_returns_mdd([100.0, 100.0], [[-0.10], [0.25]])
    assert mdd == pytest.approx(0.10)


def test_chained_returns_mdd_length_validation_and_empty():
    assert chained_returns_mdd([], []) == 0.0
    with pytest.raises(ValueError):
        chained_returns_mdd([100.0], [[0.01], [0.02]])
    with pytest.raises(ValueError):
        chained_returns_mdd([0.0], [[0.01]])


def test_chain_fold_segments_compounds_capital_across_resets():
    segments = [
        [(0, 100.0), (DAY, 120.0)],          # fold 1: +20%
        [(0, 100.0), (DAY, 90.0)],           # fold 2 resets to 100k, -10%
    ]
    chained = chain_fold_segments(segments)
    values = [v for _, v in chained]
    assert values[0] == pytest.approx(100.0)
    assert values[1] == pytest.approx(120.0)
    assert values[2] == pytest.approx(120.0)   # no reset: continues at 120
    assert values[3] == pytest.approx(108.0)   # -10% of 120
