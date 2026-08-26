"""V10 fail-closed statistics tests (A5, H07).

Synthetic fixtures with provably-by-hand answers only:

* byte-identical matrix determinism across two constructions and two temp
  roots;
* DSR sanity against a hand-computed SR0;
* CSCV PBO exactly 0.0 when the in-sample winner stays best out-of-sample
  and exactly 7970/12870 for the adversarial antisymmetric construction;
* every insufficient-input path returns UNAVAILABLE_FAIL_CLOSED objects —
  never exceptions carrying numbers, never inferred credit;
* the haircut refuses stale denominators (V9 gap: N=112 vs honest 117).
"""

from __future__ import annotations

import json
import math

import pytest

from research.stats_v10 import (
    HAIRCUT_ESTIMATOR_ID,
    VERDICT_OK,
    VERDICT_UNAVAILABLE,
    build_returns_matrix,
    deflated_sharpe_ratio,
    deserialize_matrix_payload,
    pbo_cscv,
    serialize_matrix_payload,
    statistical_haircut_v10,
    sharpe_inputs,
)

EULER_GAMMA = 0.5772156649015329


def stable_matrix_data():
    data = {}
    for i in range(8):
        variant = f"VAR-{i}"
        base = -0.04 + i * 0.01
        data[variant] = [
            base + ((t % 3) - 1) * 1e-5 * (i + 1) for t in range(32)
        ]
    return data


def adversarial_matrix_data():
    up = 0.01
    noise = [0.0001 * (j + 1) for j in range(6)]
    data = {"ADV-X": [], "ADV-Y": []}
    for t in range(32):
        first_half = t < 16
        data["ADV-X"].append(up if first_half else -up)
        data["ADV-Y"].append(-up if first_half else up)
    for j, c in enumerate(noise):
        data[f"NOISE-{j}"] = [c] * 32
    return data


# --------------------------------------------------------------------------- #
# Deterministic matrix + byte-stable round trip
# --------------------------------------------------------------------------- #
def test_matrix_determinism_identical_bytes_two_constructions_two_roots(tmp_path):
    payload_a = build_returns_matrix(stable_matrix_data())
    reversed_insertion = dict(reversed(list(stable_matrix_data().items())))
    payload_b = build_returns_matrix(reversed_insertion)
    assert payload_a["verdict"] == VERDICT_OK
    assert payload_b["verdict"] == VERDICT_OK
    assert payload_a["variants"] == sorted(payload_a["variants"])
    assert payload_a == payload_b

    text_a = serialize_matrix_payload(payload_a)
    text_b = serialize_matrix_payload(payload_b)
    assert text_a == text_b

    file_one = tmp_path / "root_one" / "matrix.json"
    file_two = tmp_path / "root_two" / "matrix.json"
    file_one.parent.mkdir(parents=True)
    file_two.parent.mkdir(parents=True)
    file_one.write_text(text_a, encoding="utf-8")
    file_two.write_text(text_b, encoding="utf-8")
    assert file_one.read_bytes() == file_two.read_bytes()

    restored = deserialize_matrix_payload(file_one.read_bytes())
    assert restored == payload_a
    with pytest.raises(ValueError):
        deserialize_matrix_payload(text_a[:-2])


def test_sharpe_inputs_matches_hand_computed_values():
    series = [0.01, -0.02, 0.03, 0.04]
    payload = build_returns_matrix({"V": series})
    result = sharpe_inputs(payload)
    assert result["verdict"] == VERDICT_OK
    row = result["inputs"][0]
    mean = sum(series) / len(series)
    var = sum((x - mean) ** 2 for x in series) / (len(series) - 1)
    assert row["mean_per_period"] == pytest.approx(mean)
    assert row["std_sample"] == pytest.approx(math.sqrt(var))
    assert row["sharpe_per_period"] == pytest.approx(mean / math.sqrt(var))
    assert row["count"] == 4


def test_dsr_hand_computed_small_case():
    trials = [0.18, 0.19, 0.20, 0.21, 0.22, 0.23, 0.24, 0.25]
    hand_variance = sum(
        (x - sum(trials) / len(trials)) ** 2 for x in trials
    ) / (len(trials) - 1)
    z1 = 1.1503493803760087
    z2 = 1.6844085916926693
    hand_sr0 = math.sqrt(hand_variance) * (
        (1 - EULER_GAMMA) * z1 + EULER_GAMMA * z2
    )
    result = deflated_sharpe_ratio(1.0, trials, 8, 252, 0.0, 3.0)
    assert result["verdict"] == VERDICT_OK
    assert result["estimator_id"] == "DSR_BAILEY_LOPEZDEPRADO_V1"
    assert result["sr0"] == pytest.approx(hand_sr0, rel=1e-3)
    assert result["dsr"] > 0.999
    assert result["effective_n_trials"] == 8


def test_dsr_decreases_with_trial_count_and_dispersion():
    trials = [0.10 * i for i in range(2, 10)]
    few = deflated_sharpe_ratio(0.85, trials, len(trials), 200, 0.0, 3.0)
    many = deflated_sharpe_ratio(0.85, trials, 5000, 200, 0.0, 3.0)
    assert few["verdict"] == many["verdict"] == VERDICT_OK
    assert many["dsr"] < few["dsr"]
    wide = [-0.50, 0.10, 0.30, 2.30]
    tight = [0.74, 0.76, 0.78, 0.80]
    assert (
        deflated_sharpe_ratio(0.8, wide, 4, 126, 0.0, 3.0)["dsr"]
        < deflated_sharpe_ratio(0.8, tight, 4, 126, 0.0, 3.0)["dsr"]
    )


# --------------------------------------------------------------------------- #
# CSCV PBO: stable -> 0.0; adversarial flip -> high, exact by hand
# --------------------------------------------------------------------------- #
def test_pbo_low_when_best_in_sample_stays_best_out_of_sample():
    payload = build_returns_matrix(stable_matrix_data())
    result = pbo_cscv(payload, n_partitions=16)
    assert result["verdict"] == VERDICT_OK
    assert result["pbo"] == 0.0
    assert result["classification"] == "PASS"


def test_pbo_high_on_adversarial_flip_exact_fraction():
    payload = build_returns_matrix(adversarial_matrix_data())
    result = pbo_cscv(payload, n_partitions=16)
    assert result["verdict"] == VERDICT_OK
    expected = 7970 / 12870
    assert result["pbo"] == pytest.approx(expected, abs=1e-9)
    assert result["classification"] == "FAIL"
    assert result["pbo_max_acceptable"] == 0.5


# --------------------------------------------------------------------------- #
# Every fail-closed path returns verdict objects, never numbers/exceptions
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "bad_input",
    [None, {}, {"A": []}, {"A": [0.1], "B": [0.1, 0.2]},
     {"A": ["x", 0.1]}, {"A": [0.1, float("nan")]}],
)
def test_build_returns_matrix_fail_closed_paths(bad_input):
    result = build_returns_matrix(bad_input)
    assert result["verdict"] == VERDICT_UNAVAILABLE
    assert isinstance(result["reason"], str) and result["reason"]
    assert "matrix" not in result or not isinstance(result.get("matrix"), list)


def test_sharpe_inputs_fail_closed_paths():
    garbage = sharpe_inputs({"verdict": "whatever"})
    assert garbage["verdict"] == VERDICT_UNAVAILABLE
    single_obs = sharpe_inputs(build_returns_matrix({"A": [0.1], "B": [0.2]}))
    assert single_obs["reason"].startswith("insufficient_observations:A")
    zero_var = sharpe_inputs(
        build_returns_matrix({"A": [0.05, 0.05, 0.05], "B": [0.1, 0.2, 0.3]})
    )
    assert zero_var["reason"].startswith("zero_variance_variant:A")


def test_dsr_pbo_haircut_fail_closed_paths():
    dsr_missing_trials = deflated_sharpe_ratio(1.0, [0.5], 1, 100, 0.0, 3.0)
    assert dsr_missing_trials["verdict"] == VERDICT_UNAVAILABLE
    assert dsr_missing_trials["reason"] == "insufficient_trials"
    dsr_short_sample = deflated_sharpe_ratio(1.0, [0.1, 0.2], 2, 1, 0.0, 3.0)
    assert dsr_short_sample["reason"] == "insufficient_sample"
    dsr_bad_kurtosis = deflated_sharpe_ratio(1.0, [0.1, 0.2], 2, 100, 0.0, 0.5)
    assert dsr_bad_kurtosis["reason"] == "invalid_kurtosis"
    dsr_garbage = deflated_sharpe_ratio(None, [0.1, 0.2], 2, 100, 0.0, 3.0)
    assert dsr_garbage["reason"] == "candidate_sharpe_not_numeric"

    small = pbo_cscv(build_returns_matrix({"A": [0.01] * 16, "B": [0.02] * 16}))
    assert small["verdict"] == VERDICT_UNAVAILABLE
    assert small["reason"].startswith("insufficient_configurations:2<8")
    odd_parts = pbo_cscv(build_returns_matrix(stable_matrix_data()), n_partitions=15)
    assert odd_parts["reason"] == "partitions_must_be_even"
    too_few_blocks = pbo_cscv(
        build_returns_matrix({f"V{i}": [0.001 * i] * 4 for i in range(8)}),
        n_partitions=16,
    )
    assert too_few_blocks["reason"].startswith("insufficient_blocks:4<16")
    not_a_matrix = pbo_cscv({"oops": True})
    assert not_a_matrix["verdict"] == VERDICT_UNAVAILABLE

    bad_haircut = statistical_haircut_v10("117")
    assert bad_haircut["verdict"] == VERDICT_UNAVAILABLE
    assert bad_haircut["reason"] == "effective_n_must_be_positive_int"
    bad_base = statistical_haircut_v10(120, base_n=0)
    assert bad_base["reason"] == "base_n_must_be_positive_int"


# --------------------------------------------------------------------------- #
# Haircut: V9 stale-N documentation gap regression
# --------------------------------------------------------------------------- #
def test_haircut_flags_stale_denominator_honestly():
    stale = statistical_haircut_v10(112)
    assert stale["verdict"] == VERDICT_UNAVAILABLE
    assert stale["reason"] == "stale_or_regressed_denominator"
    assert stale["effective_n"] == 112
    assert stale["current_denominator"] == 117
    assert "112" in stale["documentation_gap"]
    assert "117" in stale["documentation_gap"]
    assert "pbo" not in stale and "haircut_fraction" not in stale


def test_haircut_at_and_above_current_denominator():
    exact = statistical_haircut_v10(117)
    assert exact["verdict"] == VERDICT_OK
    assert exact["matches_current_denominator"] is True
    assert exact["haircut_fraction"] == 0.0
    grown = statistical_haircut_v10(130)
    assert grown["verdict"] == VERDICT_OK
    assert grown["matches_current_denominator"] is False
    assert grown["haircut_fraction"] == pytest.approx(1 - math.sqrt(117 / 130))
    assert grown["haircut_fraction"] > 0.0
    assert "recomputed" in grown["note"]
    assert grown["estimator_id"] == HAIRCUT_ESTIMATOR_ID


def test_haircut_tracks_live_denominator(tmp_path):
    from research.contract_v10 import MultipleTestingDenominator

    denom = MultipleTestingDenominator(base=117)
    denom.add_scored_cell("V10-CELL-1")
    denom.add_scored_cell("V10-CELL-2")
    live = statistical_haircut_v10(denom.N)
    assert live["verdict"] == VERDICT_OK
    assert live["effective_n"] == 119
    assert live["haircut_fraction"] == pytest.approx(1 - math.sqrt(117 / 119))
