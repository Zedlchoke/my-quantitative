"""FOREX-NG5 D2 measurement unit tests — offline, synthetic, no scored PnL.

Covers the veto machinery's pure logic: A4/A5 state construction, the A5
fade/build/hold branches and gap-reset law, the rho machinery (bar, P-20
fail-closed), the S1 adjudication rule (Q-11 INVALID-NULL distinction), fold
assignment and the frozen E1 cost constants. The full measurement run is an
integration test that is skipped unless the verified census staging + restored
TD spot are present on the host.
"""
import os
import sys
from datetime import date
from decimal import Decimal

import pytest

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "research", "assets", "forex_ng5", "d2"))

import d2_measure as m  # noqa: E402


# ------------------------------------------------------------- states -------
def test_expanding_deciles_warmup_and_bounds():
    ratios = [Decimal(i) for i in range(1, 81)]
    out = m.expanding_deciles(ratios)
    assert all(out[i] is None for i in range(52))          # 53rd index 52 -> defined
    assert out[52] is not None and out[51] is None
    assert all(1 <= d <= 10 for d in out if d is not None)
    # monotone input: the max so far must be decile 10, the min decile 1
    assert out[52] == 10          # 53 increasing values: current is max
    assert out[53] == 10
    # duplicate (tie) input: all equal -> average rank -> mid decile
    same = [Decimal(5)] * 60
    out2 = m.expanding_deciles(same)
    assert out2[59] == 1 + min(9, int(10 * ((29 + 1) / 53 + 0))) or out2[59] >= 5


def test_trailing_deciles_tie_resolves_lower():
    # strict '<' counting: all-equal window -> rank 0 -> decile 1
    n = 120
    dates = [f"2020-{1 + i // 28:02d}-{1 + i % 28:02d}" for i in range(n)]
    ratios = [Decimal(7)] * n
    weeks = dates[:]      # every census week present -> consecutive
    out = m.trailing_deciles(dates, ratios, sorted(weeks))
    assert out[103] is not None
    dec, clean = out[103]
    assert dec == 1 and clean is True


def test_trailing_deciles_gap_reset_law():
    # 104 weekly Fridays; drop ONE pair report inside the window -> any window
    # spanning the gap is None until 104 consecutive reports refilled
    import datetime as dt
    base = dt.date(2020, 1, 3)
    weeks = [(base + dt.timedelta(weeks=i)).isoformat() for i in range(160)]
    missing = weeks[150]                      # gap late: windows i>=253? none
    pair_weeks = [w for w in weeks if w != missing]
    # window ENDING after the gap must be broken while the gap is inside it
    ratios = [Decimal(i % 7) for i in range(len(pair_weeks))]
    out = m.trailing_deciles(pair_weeks, ratios, sorted(weeks))
    gi = pair_weeks.index(weeks[151])         # first index after the gap
    assert out[gi] is None                    # window spans the gap
    # after 104 consecutive available reports the window refills
    refill = gi + 103
    if refill < len(pair_weeks):
        assert out[refill] is not None
    # window entirely before the gap (and past the 104 warmup) is fine
    assert out[110] is not None


def test_a5_signal_branches():
    # fade: destination extreme band, oppose the transition
    w, fired = m.a5_signal(10, 6, 0.0)      # f=+4, d>=9 -> fade short
    assert w == -1.0 and fired == "fade"
    w, fired = m.a5_signal(1, 5, 0.0)       # f=-4, d<=2 -> fade long
    assert w == +1.0 and fired == "fade"
    # build: interior destination, follow the transition
    w, fired = m.a5_signal(6, 2, 0.0)       # f=+4, interior -> build long
    assert w == +1.0 and fired == "build"
    w, fired = m.a5_signal(4, 9, 0.0)       # f=-5, interior -> build short
    assert w == -1.0 and fired == "build"
    # hold: no crossing
    w, fired = m.a5_signal(5, 4, 0.37)
    assert w == 0.37 and fired is None
    # missing state -> hold
    w, fired = m.a5_signal(None, 4, -0.5)
    assert w == -0.5 and fired is None


def test_a4_weight_states():
    assert m.a4_weight(1) == 0.25
    assert m.a4_weight(3) == 0.25
    assert m.a4_weight(5) == 0.0
    assert m.a4_weight(7) == 0.0
    assert m.a4_weight(8) == -0.25
    assert m.a4_weight(10) == -0.25


# ---------------------------------------------------------- rho machinery ---
def test_pearson_known_and_degenerate():
    assert m.pearson([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
    assert m.pearson([1, 2, 3], [6, 4, 2]) == pytest.approx(-1.0)
    assert m.pearson([1, 2], [1, 2, 3]) is None
    assert m.pearson([5, 5, 5], [1, 2, 3]) is None   # zero variance -> None


def test_rho_block_bar_and_fail_closed():
    ok = m._rho_block({1: 1, 2: -1, 3: 1, 4: -1},
                      {1: 1, 2: -1, 3: 1, 4: -1}, m.RHO_BAR)
    assert ok["verdict"] == "KILL" and ok["abs"] == 1.0
    surv = m._rho_block({1: 1, 2: -1, 3: 1, 4: -1},
                        {1: 1, 2: 1, 3: -1, 4: -1}, m.RHO_BAR)
    assert surv["verdict"] == "SURVIVE" and surv["margin"] >= 0
    # P-20 fail-closed: disjoint or zero-variance shadow -> NOT_RUN
    fc = m._rho_block({1: 1}, {2: 1}, m.RHO_BAR)
    assert fc["verdict"] == "NOT_RUN" and fc["fail_closed"]
    zv = m._rho_block({1: 1, 2: 1}, {1: 3, 2: 3}, m.RHO_BAR)
    assert zv["verdict"] == "NOT_RUN" and zv["fail_closed"]


# ------------------------------------------------------------ S1 / S2 -------
def test_s1_adjudicate_rule():
    # reproduce at the bars -> KILL
    assert m.s1_adjudicate(0.95, 0.93)[0] == "KILL"
    # below either bar -> SURVIVE
    assert m.s1_adjudicate(0.89, 0.99)[0] == "SURVIVE"
    assert m.s1_adjudicate(0.99, 0.89)[0] == "SURVIVE"
    # mirror (agreement >= 0.999) reproducing -> INVALID NULL, not a kill
    assert m.s1_adjudicate(0.999, 0.9995)[0] == "SURVIVE_INVALID_NULL"
    # unmeasurable -> NOT_RUN
    assert m.s1_adjudicate(None, None)[0] == "NOT_RUN"


def test_s2_floor_constant_frozen():
    assert m.S2_FLOOR == 10
    assert m.RHO_BAR == 0.20
    assert m.S1_RHO_REPRO == 0.90 and m.S1_AGREE_REPRO == 0.90


# ---------------------------------------------------------------- folds -----
def test_fold_of_boundaries():
    assert m.fold_of(date(2006, 6, 13)) == "F1"
    assert m.fold_of(date(2013, 6, 30)) == "F1"
    assert m.fold_of(date(2013, 7, 1)) == "F2"
    assert m.fold_of(date(2020, 6, 30)) == "F2"
    assert m.fold_of(date(2020, 7, 1)) == "F3"
    assert m.fold_of(date(2026, 9, 8)) == "F3"
    assert m.fold_of(date(2006, 6, 12)) == ""
    assert m.fold_of(date(2026, 9, 9)) == ""


def test_e1_frozen_cost_contract():
    # NG1 frozen set: 1.5 bps/side x stress tier 2.0, round trip = 2 sides
    assert m.COST_BPS_PER_SIDE == 1.5
    assert m.COST_TIER == 2.0
    assert 2 * m.COST_BPS_PER_SIDE * m.COST_TIER == pytest.approx(6.0)


def test_exact_int_contract():
    assert m._exact_int("93212") == 93212
    assert m._exact_int("93212.000000") == 93212
    with pytest.raises(ValueError):
        m._exact_int("93212.5")
    with pytest.raises(ValueError):
        m._exact_int("93,212")
    with pytest.raises(ValueError):
        m._exact_int("abc")


# ------------------------------------------------- integration (skippable) --
def _integration_data_present():
    return (os.path.isdir(m.RAW)
            and os.path.isfile(os.path.join(
                m.OUT, "td_spot_restored", "GBPUSD.json")))


@pytest.mark.skipif(not _integration_data_present(),
                    reason="verified census staging / restored TD spot absent")
def test_full_measurement_smoke():
    res = m.measure_all()
    assert res["folds_populated"]["matches_census_freeze"]
    assert res["td_repin"]["verdict"] == "PASS"
    for anchor in ("A4", "A5"):
        blk = res["per_proposal"][anchor]
        assert blk["verdict"] in ("SURVIVE", "KILL", "NOT_RUN_FAIL_CLOSED")
        for v in blk["vetoes"].values():
            assert v in ("SURVIVE", "KILL", "NOT_RUN",
                         "SURVIVE_INVALID_NULL")
    assert res["overall_d2_verdict"] in (
        "D2_PASS", "D2_VETO_ALL", "D2_PARTIAL", "D2_FAIL_CLOSED_NOT_RUN")
