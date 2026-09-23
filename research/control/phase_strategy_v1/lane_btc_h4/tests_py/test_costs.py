"""Cost-model unit fixtures (hand-computed; plan §14): fee/slip, signed
funding, exact 1.0/1.5/2.0 tier multiplication on the FULL stack."""

import pytest

from research.control.phase_strategy_v1.lane_btc_h4.pipeline import config
from research.control.phase_strategy_v1.lane_btc_h4.pipeline.costs import (
    side_cost_fraction, round_trip_cost_fraction, funding_cost_fraction,
    per_trade_cost_fraction, ceiling_check)


def test_side_and_round_trip_bps():
    assert side_cost_fraction(1.0) == pytest.approx(6.0 * 1e-4)   # 5 taker + 1 slip
    assert round_trip_cost_fraction(1.0) == pytest.approx(12.0 * 1e-4)
    assert round_trip_cost_fraction(1.5) == pytest.approx(18.0 * 1e-4)
    assert round_trip_cost_fraction(2.0) == pytest.approx(24.0 * 1e-4)


def test_funding_signed_by_position():
    long_pay = funding_cost_fraction(3, +1, 1.0)
    short_receive = funding_cost_fraction(3, -1, 1.0)
    assert long_pay == pytest.approx(3 * config.FUNDING_PER_8H)
    assert short_receive == pytest.approx(-3 * config.FUNDING_PER_8H)
    assert long_pay == -short_receive


def test_tier_multiplier_applies_to_full_stack():
    boundaries, sign = 11, +1
    one = per_trade_cost_fraction(boundaries, sign, 1.0)
    one_and_half = per_trade_cost_fraction(boundaries, sign, 1.5)
    two = per_trade_cost_fraction(boundaries, sign, 2.0)
    assert one_and_half == pytest.approx(1.5 * one)
    assert two == pytest.approx(2.0 * one)
    # hand-computed: (12 bps + 11 x 1.377e-5) at 1.5x
    expected = 1.5 * (12.0 * 1e-4 + 11 * config.FUNDING_PER_8H)
    assert one_and_half == pytest.approx(expected)


def test_ceiling_verdict_rules():
    ok = ceiling_check({"F1": 89}, median_hold_bars=23)
    assert ok["verdict"] == "PASS_WITHIN_CEILING"
    # hand-computed: 18 bps RT at 1.5x + funding 3 boundaries/day at 1.5x
    # scaled by hold_days = 23*4/24
    funding_per_day_bps_15 = 3 * config.FUNDING_PER_8H * 1.5 * 1e4   # 0.61965
    expected = 18.0 + funding_per_day_bps_15 * (23 * 4 / 24)
    assert ok["per_trade_cost_bps_at_1.5x"] == pytest.approx(expected, rel=1e-9)
    # pathological hold: funding drag at 1.5x exceeds the plausible-edge bound
    struck = ceiling_check({"F1": 1}, median_hold_bars=1000)
    assert struck["verdict"] == "STRUCK_BY_CEILING"


def test_config_cost_constants():
    assert config.TAKER_FEE_BPS == 5.0 and config.SLIPPAGE_BPS == 1.0
    assert config.COST_ROUND_TRIP_BPS == 12.0
    assert config.FUNDING_PER_8H == 1.377e-5
    assert config.COST_TIERS == [1.0, 1.5, 2.0]
    assert config.PLAUSIBLE_EDGE_BPS == 100.0
