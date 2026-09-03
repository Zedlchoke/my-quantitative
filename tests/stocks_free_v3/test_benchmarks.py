"""Hand-computed golden tests for the four frozen benchmark constructions.

All inputs are SYNTHETIC; every expected number below is computed by hand in
the comments.  These pin the frozen semantics BEFORE any proposal exists —
changing a golden value afterwards is a scientific-threshold change.
"""

from __future__ import annotations

import pytest

from research.stocks_free_v3.authority import (
    BENCHMARK_SYMBOL,
    COHORT_SYMBOLS,
    SECTOR_SYMBOLS,
)
from research.stocks_free_v3.benchmarks import (
    BENCHMARK_EW_SECTOR_TOTAL_RETURN,
    BENCHMARK_FLAT_HARD,
    BENCHMARK_RISK_MATCHED_SPY,
    BENCHMARK_SPY_TOTAL_RETURN,
    BenchmarkError,
    BenchmarkSeries,
    DEFAULT_VOL_SCALING_RULE,
    VolScalingRule,
    build_equal_weight_sector_total_return,
    build_flat_benchmark,
    build_risk_matched_spy,
    build_spy_total_return,
    issuer_total_return_daily,
    split_adjusted_closes,
)

SESSIONS = ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
WINDOW = ("2024-01-02", "2024-01-05")

# Hand-designed fixture: a 2:1 split and a 1.0/share distribution land on the
# same session (2024-01-04).
#   raw:      100, 110, 50, 55
#   sadj:     100, 110, 100, 110          (first post-split close doubled)
#   r(d2)     = 110/100 - 1               = 0.1
#   r(d3)     = (100 + 1.0)/110 - 1       = 101/110 - 1  = -0.081818...
#   r(d4)     = 110/100 - 1               = 0.1
#   levels:   1.0, 1.1, 1.01, 1.111       (1.1 * 101/110 = 1.01)
RAW = {
    "2024-01-02": 100.0,
    "2024-01-03": 110.0,
    "2024-01-04": 50.0,
    "2024-01-05": 55.0,
}
DISTRIBUTIONS = {"2024-01-04": 1.0}
SPLIT_FACTORS = {"2024-01-04": 2.0}


# --- split adjustment and issuer TR ------------------------------------------------ #


def test_split_without_distribution_is_a_zero_return() -> None:
    raw = {"2024-01-02": 100.0, "2024-01-03": 50.0}
    dates, returns = issuer_total_return_daily(raw, {}, {"2024-01-03": 2.0})
    assert dates == ["2024-01-03"]
    assert returns == [0.0]


def test_split_adjusted_closes_match_v2_reconstruction_convention() -> None:
    sadj = split_adjusted_closes(RAW, SPLIT_FACTORS)
    # 2:1 split effective 2024-01-04: every close on/after the split doubles.
    assert sadj == {
        "2024-01-02": 100.0,
        "2024-01-03": 110.0,
        "2024-01-04": 100.0,
        "2024-01-05": 110.0,
    }


def test_issuer_tr_golden() -> None:
    dates, returns = issuer_total_return_daily(RAW, DISTRIBUTIONS, SPLIT_FACTORS)
    assert dates == SESSIONS[1:]
    assert returns[0] == pytest.approx(0.1)
    assert returns[1] == pytest.approx(101.0 / 110.0 - 1.0)
    assert returns[2] == pytest.approx(0.1)


# --- benchmark 1: flat hard --------------------------------------------------------- #


def test_flat_benchmark_golden() -> None:
    flat = build_flat_benchmark(SESSIONS, *WINDOW)
    assert isinstance(flat, BenchmarkSeries)
    assert flat.benchmark_id == BENCHMARK_FLAT_HARD
    assert flat.returns == (None, 0.0, 0.0, 0.0)
    assert flat.levels == (1.0, 1.0, 1.0, 1.0)
    assert flat.total_return == 0.0


# --- benchmark 2: SPY total return --------------------------------------------------- #


def test_spy_total_return_golden() -> None:
    spy = build_spy_total_return(RAW, DISTRIBUTIONS, SPLIT_FACTORS, SESSIONS, *WINDOW)
    assert spy.benchmark_id == BENCHMARK_SPY_TOTAL_RETURN
    assert spy.dates == tuple(SESSIONS)
    assert spy.returns == (
        None,
        pytest.approx(0.1),
        pytest.approx(101.0 / 110.0 - 1.0),
        pytest.approx(0.1),
    )
    assert spy.levels[0] == 1.0
    assert spy.levels[1] == pytest.approx(1.1)
    assert spy.levels[2] == pytest.approx(1.01)  # 1.1 * 101/110
    assert spy.levels[3] == pytest.approx(1.111)  # 1.01 * 1.1
    assert spy.total_return == pytest.approx(0.111)


def test_spy_total_return_without_events_is_the_raw_return() -> None:
    spy = build_spy_total_return(RAW, {}, {}, SESSIONS, *WINDOW)
    assert spy.returns == (
        None,
        pytest.approx(0.1),
        pytest.approx(50.0 / 110.0 - 1.0),
        pytest.approx(0.1),
    )


def test_spy_tr_fails_closed_on_missing_session() -> None:
    raw = {"2024-01-02": 100.0, "2024-01-03": 110.0, "2024-01-05": 120.0}
    with pytest.raises(BenchmarkError, match="2024-01-04"):
        build_spy_total_return(raw, {}, {}, SESSIONS, *WINDOW)


# --- benchmark 3: equal-weight sector TR ---------------------------------------------- #


def _sector_inputs() -> tuple[dict, dict, dict, tuple[str, ...]]:
    # Two synthetic sector members:
    #   A: 100 -> 110            r_A = 0.10
    #   B: 200 -> 210            r_B = 0.05
    #   ew(d2) = (0.10 + 0.05)/2 = 0.075, level 1.075
    raws = {
        "AAAA": {"2024-01-02": 100.0, "2024-01-03": 110.0},
        "BBBB": {"2024-01-02": 200.0, "2024-01-03": 210.0},
    }
    return raws, {}, {}, ("AAAA", "BBBB")


def test_equal_weight_sector_golden() -> None:
    raws, dists, splits, members = _sector_inputs()
    ew = build_equal_weight_sector_total_return(
        raws, dists, splits, members, SESSIONS[:2], "2024-01-02", "2024-01-03"
    )
    assert ew.returns == (None, pytest.approx(0.075))
    assert ew.levels == (1.0, pytest.approx(1.075))
    assert ew.total_return == pytest.approx(0.075)


def test_equal_weight_is_the_mean_of_member_returns() -> None:
    raws, dists, splits, members = _sector_inputs()
    ew = build_equal_weight_sector_total_return(
        raws, dists, splits, members, SESSIONS[:2], "2024-01-02", "2024-01-03"
    )
    per_member = [
        build_spy_total_return(  # same TR identity, one member at a time
            raws[s], dists.get(s, {}), splits.get(s, {}), SESSIONS[:2],
            "2024-01-02", "2024-01-03", benchmark_id=s,
        ).returns[1]
        for s in members
    ]
    assert ew.returns[1] == pytest.approx(sum(per_member) / len(per_member))


def test_equal_weight_fails_closed_on_missing_member_session() -> None:
    raws, dists, splits, members = _sector_inputs()
    del raws["BBBB"]["2024-01-03"]  # member loses its session observation
    with pytest.raises(BenchmarkError):
        build_equal_weight_sector_total_return(
            raws, dists, splits, members, SESSIONS[:2], "2024-01-02", "2024-01-03"
        )


def test_frozen_sector_membership_is_cohort_minus_spy() -> None:
    assert len(SECTOR_SYMBOLS) == 10
    assert BENCHMARK_SYMBOL not in SECTOR_SYMBOLS
    assert set(SECTOR_SYMBOLS) | {BENCHMARK_SYMBOL} == set(COHORT_SYMBOLS)
    ew = build_equal_weight_sector_total_return(
        {s: {"2024-01-02": 1.0, "2024-01-03": 1.0} for s in SECTOR_SYMBOLS},
        {s: {} for s in SECTOR_SYMBOLS},
        {s: {} for s in SECTOR_SYMBOLS},
        SECTOR_SYMBOLS,
        SESSIONS[:2],
        "2024-01-02",
        "2024-01-03",
    )
    # constant prices -> constant levels -> zero return
    assert ew.total_return == 0.0


# --- benchmark 4: risk-matched SPY (ex-ante scaled) ------------------------------------ #


def test_risk_matched_golden_min_gross_clip() -> None:
    # Rule: lookback=2, target 0.02 daily vol, gross clipped to [0.5, 2.0].
    #   scale(d2): history []               -> insufficient -> min_gross 0.5
    #   scale(d3): history [0.1]            -> insufficient -> 0.5
    #   scale(d4): history [0.1, -0.0818..] -> std(ddof0) = 0.0909..
    #                                         0.02/0.0909 = 0.22 -> clip 0.5
    rule = VolScalingRule(lookback_sessions=2, target_daily_vol=0.02, min_gross=0.5, max_gross=2.0)
    rm = build_risk_matched_spy(RAW, DISTRIBUTIONS, SPLIT_FACTORS, SESSIONS, *WINDOW, rule)
    assert rm.benchmark_id == BENCHMARK_RISK_MATCHED_SPY
    assert rm.scalings == (None, pytest.approx(0.5), pytest.approx(0.5), pytest.approx(0.5))
    assert rm.returns[1] == pytest.approx(0.5 * 0.1)
    assert rm.returns[2] == pytest.approx(0.5 * (101.0 / 110.0 - 1.0))
    assert rm.returns[3] == pytest.approx(0.5 * 0.1)


def test_risk_matched_golden_interior_scaling() -> None:
    # Rule: lookback=2, target 0.001, gross clipped to [0.0, 2.0].
    # SPY-like fixture returns: r(d2)=0.1, r(d3)=-0.081818.., r(d4)=0.1.
    #   scale(d4) = 0.001 / std([0.1, -0.081818..])
    #             = 0.001 / 0.0909090909... = 0.011 (interior, no clip)
    rule = VolScalingRule(lookback_sessions=2, target_daily_vol=0.001, min_gross=0.0, max_gross=2.0)
    rm = build_risk_matched_spy(RAW, DISTRIBUTIONS, SPLIT_FACTORS, SESSIONS, *WINDOW, rule)
    expected_scale = 0.001 / ((0.1 - (101.0 / 110.0 - 1.0)) / 2.0)  # std(ddof0) of 2 pts
    assert rm.scalings[3] == pytest.approx(expected_scale)
    assert 0.0 < expected_scale < 2.0
    assert rm.returns[3] == pytest.approx(expected_scale * 0.1)


def test_ex_ante_scaling_uses_only_data_before_the_decision() -> None:
    """Perturbing the decision-day close changes the scaled return ONLY
    through the unscaled SPY return; the scaling itself is unchanged."""
    rule = VolScalingRule(lookback_sessions=2, target_daily_vol=0.001, min_gross=0.0, max_gross=2.0)
    base = build_risk_matched_spy(RAW, DISTRIBUTIONS, SPLIT_FACTORS, SESSIONS, *WINDOW, rule)
    perturbed_raw = dict(RAW, **{"2024-01-05": 60.0})  # changes r(d4) only
    perturbed = build_risk_matched_spy(
        perturbed_raw, DISTRIBUTIONS, SPLIT_FACTORS, SESSIONS, *WINDOW, rule
    )
    assert perturbed.scalings == base.scalings  # scaling untouched by day-t data
    sadj = split_adjusted_closes(perturbed_raw, SPLIT_FACTORS)
    new_r4 = sadj["2024-01-05"] / sadj["2024-01-04"] - 1.0  # post-split close doubled
    assert new_r4 == pytest.approx(120.0 / 100.0 - 1.0)
    assert perturbed.returns[3] == pytest.approx(base.scalings[3] * new_r4)


def test_scaling_of_frozen_rule_directly() -> None:
    rule = VolScalingRule(lookback_sessions=2, target_daily_vol=0.001, min_gross=0.0, max_gross=2.0)
    assert rule.scale([]) == 0.0  # insufficient -> min_gross
    assert rule.scale([0.01]) == 0.0  # insufficient (1 < 2)
    assert rule.scale([0.01, 0.01]) == 2.0  # zero realized vol -> max_gross
    # history [0.01, 0.03]: mean 0.02, std(ddof0) = 0.01 -> 0.001/0.01 = 0.1
    assert rule.scale([0.01, 0.03]) == pytest.approx(0.1)
    # history [0.0001, 0.0002]: std = 0.00005 -> 0.02/0.00005 = 400 -> clip 2.0
    assert rule.scale([0.0001, 0.0002]) == 2.0


def test_default_rule_is_frozen() -> None:
    assert DEFAULT_VOL_SCALING_RULE.to_payload() == {
        "kind": "EX_ANTE_GROSS_VOL_CLIP_DD0",
        "lookback_sessions": 63,
        "target_daily_vol": 0.01,
        "min_gross": 0.0,
        "max_gross": 2.0,
        "insufficient_history": "MIN_GROSS",
    }
    assert (
        DEFAULT_VOL_SCALING_RULE.digest
        == VolScalingRule(63, 0.01, 0.0, 2.0).digest
    )


def test_rule_rejects_unfrozen_policies() -> None:
    with pytest.raises(ValueError):
        VolScalingRule(lookback_sessions=0, target_daily_vol=0.01, min_gross=0.0, max_gross=2.0)
    with pytest.raises(ValueError):
        VolScalingRule(lookback_sessions=2, target_daily_vol=-0.01, min_gross=0.0, max_gross=2.0)
    with pytest.raises(ValueError):
        VolScalingRule(lookback_sessions=2, target_daily_vol=0.01, min_gross=2.0, max_gross=1.0)
    with pytest.raises(ValueError):
        VolScalingRule(
            lookback_sessions=2,
            target_daily_vol=0.01,
            min_gross=0.0,
            max_gross=1.0,
            insufficient_history="UNSCALED",
        )


# --- digests and determinism ----------------------------------------------------------- #


def test_series_digests_deterministic_and_definition_sensitive() -> None:
    spy_one = build_spy_total_return(RAW, DISTRIBUTIONS, SPLIT_FACTORS, SESSIONS, *WINDOW)
    spy_two = build_spy_total_return(RAW, DISTRIBUTIONS, SPLIT_FACTORS, SESSIONS, *WINDOW)
    assert spy_one.series_digest() == spy_two.series_digest()
    assert spy_one.definition_digest == spy_two.definition_digest

    rule_a = VolScalingRule(2, 0.02, 0.5, 2.0)
    rule_b = VolScalingRule(2, 0.02, 0.0, 2.0)
    rm_a = build_risk_matched_spy(RAW, DISTRIBUTIONS, SPLIT_FACTORS, SESSIONS, *WINDOW, rule_a)
    rm_b = build_risk_matched_spy(RAW, DISTRIBUTIONS, SPLIT_FACTORS, SESSIONS, *WINDOW, rule_b)
    assert rm_a.definition_digest != rm_b.definition_digest  # rule change = new benchmark
    assert spy_one.series_digest() != rm_a.series_digest()


def test_window_bounds_must_be_declared_sessions() -> None:
    with pytest.raises(BenchmarkError):
        build_flat_benchmark(SESSIONS, "2024-01-02", "2024-01-08")
    with pytest.raises(BenchmarkError):
        build_flat_benchmark(SESSIONS, "2024-01-03", "2024-01-02")


def test_benchmark_series_validates_its_own_chain() -> None:
    with pytest.raises(BenchmarkError):
        BenchmarkSeries(
            benchmark_id="X",
            kind="FLAT",
            window_start="2024-01-02",
            window_end="2024-01-03",
            dates=("2024-01-02", "2024-01-03"),
            returns=(None, 0.1),
            levels=(1.0, 1.5),  # broken chain
            definition_digest="0" * 64,
        )


def test_all_four_benchmark_ids_recorded() -> None:
    assert {
        BENCHMARK_FLAT_HARD,
        BENCHMARK_SPY_TOTAL_RETURN,
        BENCHMARK_EW_SECTOR_TOTAL_RETURN,
        BENCHMARK_RISK_MATCHED_SPY,
    } == {
        "FLAT_HARD",
        "SPY_TOTAL_RETURN",
        "EQUAL_WEIGHT_SECTOR_TOTAL_RETURN",
        "RISK_MATCHED_SPY_CONTEXT",
    }
