"""Golden tests for the frozen PIT features (hand-computed closed forms).

The derivations live in conftest.py; every expected number here is the
closed-form hand computation, NOT a module output.
"""

from __future__ import annotations

import math

import pytest

from research.stocks_free_v3.family_idio_shock.features import (
    FeatureError,
    compute_features,
    ols_slope,
    population_std,
)

from tests.stocks_free_v3.family_idio_shock.conftest import (
    FIRST_FEATURE_INDEX,
    SIGMA_ONE_SHOCK_REL,
    Z_ONE_SHOCK,
    shock_fixture,
)


def test_single_shock_hand_computed_z_beta_sigma(single_shock):
    sessions, returns = single_shock
    frame = compute_features(sessions, returns, ("XLK", "XLE"), "SPY")
    t = sessions[62]
    # hand values: beta exactly 2, sigma = 0.06 * sqrt(59)/60, z = -60/sqrt(59)
    assert frame.beta[t]["XLK"] == pytest.approx(2.0, rel=1e-12, abs=1e-15)
    assert frame.sigma[t]["XLK"] == pytest.approx(0.06 * SIGMA_ONE_SHOCK_REL,
                                                  rel=1e-12)
    assert frame.z[t]["XLK"] == pytest.approx(Z_ONE_SHOCK, rel=1e-12)
    assert frame.z[t]["XLK"] < -3.0  # the anchor trigger must breach


def test_first_feature_session_is_the_61st_index_and_warmup_is_absent(
        single_shock):
    sessions, returns = single_shock
    frame = compute_features(sessions, returns, ("XLK", "XLE"), "SPY")
    assert set(frame.z) == set(sessions[FIRST_FEATURE_INDEX:])
    # perfect-fit history: sigma == 0 -> z undefined (None), never triggering
    for session in (sessions[FIRST_FEATURE_INDEX], sessions[61]):
        assert frame.sigma[session]["XLK"] == 0.0
        assert frame.z[session]["XLK"] is None
        assert frame.z[session]["XLE"] is None


def test_post_shock_sessions_have_zero_residual_and_do_not_trigger(
        single_shock):
    """After the shock the ETF resumes the perfect fit: today's residual is
    exactly 0 -> z = 0.0 (defined, non-triggering) while sigma stays > 0."""
    sessions, returns = single_shock
    frame = compute_features(sessions, returns, ("XLK", "XLE"), "SPY")
    for k in (63, 64, 79):
        t = sessions[k]
        assert frame.sigma[t]["XLK"] > 0.0
        assert frame.z[t]["XLK"] == pytest.approx(0.0, abs=1e-15)


def test_clean_control_symbol_has_no_defined_z_anywhere(single_shock):
    sessions, returns = single_shock
    frame = compute_features(sessions, returns, ("XLK", "XLE"), "SPY")
    defined = [s for s, row in frame.z.items() if row["XLE"] is not None]
    assert defined == []


def test_positive_shock_mirrors_the_sign():
    sessions, returns = shock_fixture(70, {"XLF": {62: +0.08}})
    frame = compute_features(sessions, returns, ("XLF",), "SPY")
    t = sessions[62]
    assert frame.beta[t]["XLF"] == pytest.approx(2.0, rel=1e-12, abs=1e-15)
    assert frame.sigma[t]["XLF"] == pytest.approx(0.08 * SIGMA_ONE_SHOCK_REL,
                                                  rel=1e-12)
    assert frame.z[t]["XLF"] == pytest.approx(-Z_ONE_SHOCK, rel=1e-12)
    assert frame.z[t]["XLF"] > 3.0  # the control trigger must breach


def test_two_shocks_in_one_window_hand_computed():
    """AAA shocked at 50 and 62 (equal -0.05): at the window ending 62 the
    residual set is {-S, -S} -> sigma = S*sqrt(29)/30, z = -30/sqrt(29)."""
    from tests.stocks_free_v3.family_idio_shock.conftest import Z_TWO_SHOCKS
    sessions, returns = shock_fixture(
        80, {"XLK": {50: -0.05, 62: -0.05}})
    frame = compute_features(sessions, returns, ("XLK",), "SPY")
    t = sessions[62]
    assert frame.beta[t]["XLK"] == pytest.approx(2.0, rel=1e-12, abs=1e-15)
    assert frame.sigma[t]["XLK"] == pytest.approx(0.05 * math.sqrt(29.0) / 30.0,
                                                  rel=1e-12)
    assert frame.z[t]["XLK"] == pytest.approx(Z_TWO_SHOCKS, rel=1e-12)
    assert frame.z[t]["XLK"] <= -3.0


def test_missing_sector_return_inside_window_fails_closed():
    sessions, returns = shock_fixture(70, {"XLK": {62: -0.06}})
    del returns["XLK"][sessions[30]]  # a hole inside every late window
    with pytest.raises(FeatureError, match="missing issuer-TR return"):
        compute_features(sessions, returns, ("XLK",), "SPY")


def test_degenerate_benchmark_window_raises():
    sessions = [f"2020-01-{d:02d}" for d in range(1, 12)]
    flat = {s: 0.01 for s in sessions[1:]}
    returns = {"SPY": dict(flat), "XLK": dict(flat)}
    with pytest.raises(FeatureError, match="zero x-variance"):
        compute_features(sessions, returns, ("XLK",), "SPY",
                         lookback_sessions=10)


def test_short_history_returns_empty_frame():
    sessions, returns = shock_fixture(30, {})
    frame = compute_features(sessions, returns, ("ZZZ",), "SPY")
    assert frame.z == {} and frame.beta == {} and frame.sigma == {}


def test_ols_slope_and_population_std_primitives():
    assert ols_slope([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) == pytest.approx(2.0)
    assert population_std([1.0, 1.0, 1.0]) == 0.0
    assert population_std([0.0] * 59 + [-0.06]) == pytest.approx(
        0.06 * math.sqrt(59.0) / 60.0)
    with pytest.raises(FeatureError):
        ols_slope([1.0, 1.0], [1.0, 2.0])
