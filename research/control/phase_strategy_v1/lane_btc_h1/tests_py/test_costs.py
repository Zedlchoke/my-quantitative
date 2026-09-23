"""Cost-model unit fixtures — hand-computed, exact (dispatch sec 8).

BTC: taker 5 bps/side + slippage 1 bps/side = 6 bps/side = 12 bps round trip.
Funding 1.377e-5 per 8h, signed by position. Tier multipliers 1.0/1.5/2.0
apply to the FULL stack (fees+slippage AND funding).
"""
import pytest

import costs as costs


def test_round_trip_fees_exact_by_tier():
    assert costs.round_trip_cost_fraction(1.0) == pytest.approx(12.0 / 1e4)
    assert costs.round_trip_cost_fraction(1.5) == pytest.approx(18.0 / 1e4)
    assert costs.round_trip_cost_fraction(2.0) == pytest.approx(24.0 / 1e4)
    assert costs.BPS_PER_SIDE == 6.0 and costs.ROUND_TRIP_BPS == 12.0


def test_funding_counting_law_strictly_inside():
    # entry fill at t=0h, exit fill at t=20h: funding stamps at 8h and 16h
    ent = costs.Fill(price=100.0, direction=1, timestamp_hours=0.0)
    ex = costs.Fill(price=100.0, direction=-1, timestamp_hours=20.0)
    assert costs.funding_between(ent, ex, 1.0) == 2 * 1.377e-5  # 8h + 16h

    # exit exactly at 16h: stamp included (t0 < t <= t1)
    ex16 = costs.Fill(price=100.0, direction=-1, timestamp_hours=16.0)
    assert costs.funding_between(ent, ex16, 1.0) == 2 * 1.377e-5

    # exit at 15h: only the 8h stamp
    ex15 = costs.Fill(price=100.0, direction=-1, timestamp_hours=15.0)
    assert costs.funding_between(ent, ex15, 1.0) == 1 * 1.377e-5

    # entry at 7h, exit at 9h: only the 8h stamp
    e7 = costs.Fill(price=100.0, direction=1, timestamp_hours=7.0)
    e9x = costs.Fill(price=100.0, direction=-1, timestamp_hours=9.0)
    assert costs.funding_between(e7, e9x, 1.0) == 1 * 1.377e-5

    # funding stamp exactly at the entry timestamp is NOT charged (strict >)
    e8 = costs.Fill(price=100.0, direction=1, timestamp_hours=8.0)
    assert costs.funding_between(e8, ex16, 1.0) == 1 * 1.377e-5  # 16h only


def test_funding_sign_by_position():
    ent_l = costs.Fill(price=100.0, direction=1, timestamp_hours=0.0)
    ent_s = costs.Fill(price=100.0, direction=-1, timestamp_hours=0.0)
    ex = costs.Fill(price=100.0, direction=-1, timestamp_hours=24.0)
    long_f = costs.funding_between(ent_l, ex, 1.0)   # long PAYS positive funding
    short_f = costs.funding_between(ent_s, ex, 1.0)  # short RECEIVES it
    assert long_f == 3 * 1.377e-5
    assert short_f == -3 * 1.377e-5


def test_full_stack_tier_multiplication_exact():
    ent = costs.Fill(price=100.0, direction=1, timestamp_hours=0.0)
    ex = costs.Fill(price=101.0, direction=-1, timestamp_hours=20.0)
    for tier, fees_bps, fund_mult in [(1.0, 12.0, 2.0), (1.5, 18.0, 3.0),
                                      (2.0, 24.0, 4.0)]:
        r = costs.position_cost_fraction(ent, ex, tier)
        assert r["fees_slippage_bps"] == pytest.approx(fees_bps)
        expected_fund_bps = fund_mult * 1.377e-5 * 1e4  # 2 accruals, signed +
        assert r["funding_bps_signed"] == pytest.approx(expected_fund_bps)
        assert r["total_cost_bps_signed"] == pytest.approx(
            fees_bps + expected_fund_bps)


def test_zero_and_negative_duration_positions():
    ent = costs.Fill(price=100.0, direction=1, timestamp_hours=5.0)
    same = costs.Fill(price=100.0, direction=-1, timestamp_hours=5.0)
    assert costs.funding_between(ent, same, 1.0) == 0.0
    back = costs.Fill(price=100.0, direction=-1, timestamp_hours=4.0)
    assert costs.funding_between(ent, back, 1.0) == 0.0
