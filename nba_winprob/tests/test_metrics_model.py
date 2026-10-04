"""Metrics + deterministic logistic tests (synthetic only)."""
import math

from nba_winprob.protocol import (
    brier, calibration_slope, fit_logistic, log_loss, predict_logistic,
    paired_block_bootstrap_delta, reliability_bins,
)


def test_log_loss_brier_golden():
    assert abs(log_loss([0.8], [1]) - (-math.log(0.8))) < 1e-12
    assert abs(brier([0.8], [1]) - 0.04) < 1e-12
    assert abs(log_loss([0.5, 0.5], [0, 1]) - math.log(2)) < 1e-12


def test_reliability_bins_edges():
    bins = reliability_bins([0.05, 0.95, 0.95], [0, 1, 1])
    # tuple layout: (bin_index, n, mean_p, observed_rate)
    assert bins[0][1] == 1 and abs(bins[0][3] - 0.0) < 1e-12
    assert bins[9][1] == 2 and abs(bins[9][3] - 1.0) < 1e-12
    assert bins[5][1] == 0 and bins[5][3] is None


def test_calibration_slope_sign():
    ps = [0.2, 0.2, 0.2, 0.8, 0.8, 0.8]
    ys = [0, 1, 0, 1, 1, 1]
    s = calibration_slope(ps, ys)
    assert s > 0


def test_logistic_deterministic_and_directional():
    X = [[1.0, -2.0], [1.0, -1.5], [1.0, 1.5], [1.0, 2.0]]
    y = [0.0, 0.0, 1.0, 1.0]
    w1 = fit_logistic(X, y, l2=1.0)
    w2 = fit_logistic(X, y, l2=1.0)
    assert w1 == w2                       # deterministic
    assert w1[1] > 0                      # slope direction recovered
    assert predict_logistic(w1, [1.0, 2.0]) > predict_logistic(w1, [1.0, -2.0])


def test_logistic_l2_bounds():
    X = [[1.0, 100.0], [1.0, -100.0]]
    y = [1.0, 0.0]
    w = fit_logistic(X, y, l2=1.0)
    assert abs(w[1]) < 1.0                # L2 keeps the separator bounded


def test_paired_bootstrap_delta_sign_and_determinism():
    # arm: p=0.75 always; ref: p=0.5 always; y=1 always -> arm better (Δ<0)
    ps_arm = [0.75] * 6
    ps_ref = [0.5] * 6
    ys = [1, 1, 1, 1, 1, 1]
    dates = ["2010-01-01", "2010-01-01", "2010-01-02", "2010-01-02", "2010-01-03", "2010-01-03"]
    r1 = paired_block_bootstrap_delta(ps_arm, ps_ref, ys, dates, n_resamples=500)
    r2 = paired_block_bootstrap_delta(ps_arm, ps_ref, ys, dates, n_resamples=500)
    assert r1 == r2                       # seeded determinism
    assert r1[0] < 0
    assert r1[1] <= r1[0] <= r1[2]
