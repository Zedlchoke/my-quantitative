"""DSR/PBO fixtures with synthetic distributions of KNOWN inflation (D4).

Deterministic constructions where the right answer is provable by hand:

* low trial-dispersion + strong candidate  -> DSR ~ 1;
* inflating trial count / dispersion       -> DSR strictly decreases;
* CSCV matrix whose IS-winner always lands below OOS median -> PBO = 1;
* consistently-ranked matrix               -> PBO = 0;
* below pre-registered minima              -> NOT_ENOUGH_CONFIGURATIONS.
"""

from __future__ import annotations

import math

import pytest

from research.dsr import (
    DSR_ESTIMATOR_ID,
    PBO_ESTIMATOR_ID,
    PBO_MIN_CONFIGURATIONS,
    PBO_MIN_PARTITIONS,
    dsr_probability,
    pbo_cscv,
)


# ------------------------------ DSR ------------------------------------------ #
def test_dsr_estimator_id_frozen():
    assert DSR_ESTIMATOR_ID == "DSR_BAILEY_LOPEZDEPRADO_V1"


def test_dsr_strong_candidate_low_dispersion_near_certain():
    trials = [0.18, 0.19, 0.20, 0.21, 0.22, 0.23, 0.24, 0.25]
    result = dsr_probability(
        sharpe_star_candidate=1.0,
        sharpe_trials=trials,
        n_trials=8,
        sample_len=252,
        skew=0.0,
        kurtosis=3.0,
    )
    assert result["reason"] is None
    # SR0 ~ 0.036 << candidate 1.0 with a year of daily samples
    assert result["dsr"] > 0.999
    assert result["sr0"] > 0
    hand_sr0 = math.sqrt(0.0006) * (
        (1 - 0.5772156649015329) * 1.1503493803760087
        + 0.5772156649015329 * 1.6844085916926693
    )
    assert result["sr0"] == pytest.approx(hand_sr0, rel=1e-3)


def test_dsr_inflates_with_trial_dispersion_known_effect():
    candidate = 0.8
    tight = [0.74, 0.76, 0.78, 0.80]
    wide = [-0.50, 0.10, 0.30, 2.30]  # same-ish mean, far bigger variance
    tight_dsr = dsr_probability(candidate, tight, 4, 126, 0.0, 3.0)["dsr"]
    wide_dsr = dsr_probability(candidate, wide, 4, 126, 0.0, 3.0)["dsr"]
    assert wide_dsr < tight_dsr


def test_dsr_inflates_with_global_trial_count():
    trials = [0.10 * i for i in range(2, 10)]  # fixed dispersion sample
    few = dsr_probability(0.85, trials, len(trials), 200, 0.0, 3.0)
    many = dsr_probability(0.85, trials, 5000, 200, 0.0, 3.0)
    assert many["effective_n_trials"] == 5000
    assert many["dsr"] < few["dsr"]


def test_dsr_negative_skew_and_excess_kurtosis_reduce_confidence():
    trials = [0.1, 0.2, 0.3, 0.4]
    normal = dsr_probability(0.45, trials, 4, 64, 0.0, 3.0)["dsr"]
    fat_tailed = dsr_probability(0.45, trials, 4, 64, -0.8, 9.0)["dsr"]
    assert fat_tailed < normal


def test_dsr_fail_closed_degenerate_inputs():
    missing = dsr_probability(1.0, [0.5], 1, 100, 0.0, 3.0)
    assert missing["dsr"] is None and missing["reason"] == "insufficient_trials"
    none_trials = dsr_probability(1.0, None, 8, 100, 0.0, 3.0)
    assert none_trials["dsr"] is None and none_trials["reason"] == "insufficient_trials"
    short_sample = dsr_probability(1.0, [0.1, 0.2], 2, 1, 0.0, 3.0)
    assert short_sample["reason"] == "insufficient_sample"
    bad_kurt = dsr_probability(1.0, [0.1, 0.2], 2, 100, 0.0, 0.5)
    assert bad_kurt["reason"] == "invalid_kurtosis"


def test_dsr_zero_variance_trials_reduces_to_plain_psr_benchmark_zero():
    flat = [0.3, 0.3]
    result = dsr_probability(0.5, flat, 2, 100, 0.0, 3.0)
    assert result["trial_variance"] == 0.0
    assert result["sr0"] == 0.0
    # PSR z with SR*=0.5: denominator sqrt(1 + (3-1)/4 * 0.25)
    expected = 0.5 * math.sqrt(99) / math.sqrt(1.0 + 0.5**2 / 2.0)
    assert result["z_statistic"] == pytest.approx(expected)


# ------------------------------ PBO/CSCV ------------------------------------- #
def test_pbo_estimator_id_and_preregistered_minima_frozen():
    assert PBO_ESTIMATOR_ID == "PBO_CSCV_BAILEY_ETAL_V1"
    assert PBO_MIN_CONFIGURATIONS == 8
    assert PBO_MIN_PARTITIONS == 8


def _consistent_matrix(n_configs=8, n_blocks=16):
    """Ranking preserved on every subset -> PBO must be 0."""
    return {
        f"c{i}": [(i + 1) * (1.0 + 0.01 * b) for b in range(n_blocks)]
        for i in range(n_configs)
    }


def _overfit_matrix(n_configs=8):
    """Orthogonal spike design: whatever half is in-sample, its winner sits
    exactly at the OOS median boundary -> logit < 0 on EVERY split."""
    big, eps = 100.0, 0.01
    return {
        f"c{i}": [
            (big if j == i else 0.0) + eps * i for j in range(n_configs)
        ]
        for i in range(n_configs)
    }


def test_pbo_consistent_matrix_scores_zero_overfitting():
    result = pbo_cscv(_consistent_matrix())
    assert result["verdict"] == "PASS"
    assert result["pbo"] == 0.0
    assert result["n_combinations"] == 70  # C(8,4)
    assert result["reason"] is None


def test_pbo_overfit_matrix_scores_total_overfitting():
    result = pbo_cscv(_overfit_matrix(), partitions=8)
    assert result["verdict"] == "FAIL"
    assert result["pbo"] == pytest.approx(1.0)
    assert result["n_combinations"] == 70


def test_pbo_not_enough_configurations_below_preregistered_floor():
    matrix = {k: v for k, v in list(_consistent_matrix().items())[:7]}
    result = pbo_cscv(matrix)
    assert result["verdict"] == "NOT_ENOUGH_CONFIGURATIONS"
    assert result["pbo"] is None
    assert result["n_configs"] == 7


def test_pbo_not_enough_partitions():
    matrix = {
        f"c{i}": [float(i), float(-i), float(i / 2), float(-i / 2)]
        for i in range(8)
    }
    result = pbo_cscv(matrix, partitions=8)
    assert result["n_configs"] == 8
    assert result["n_blocks"] == 4
    assert result["verdict"] == "NOT_ENOUGH_CONFIGURATIONS"


def test_pbo_ragged_matrix_rejected():
    ragged = dict(_consistent_matrix())
    ragged["c0"] = ragged["c0"][:-1]
    result = pbo_cscv(ragged)
    assert result["verdict"] == "NOT_ENOUGH_CONFIGURATIONS"
    assert result["reason"] == "ragged_block_matrix"


def test_pbo_none_or_empty_input_never_passes():
    for empty in (None, {}, []):
        assert pbo_cscv(empty)["verdict"] == "NOT_ENOUGH_CONFIGURATIONS"