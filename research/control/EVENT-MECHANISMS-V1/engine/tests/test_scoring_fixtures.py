"""Lane E scoring — hand-computed fixtures (>= 5 required by dispatch E1).

Every expected number below is computed BY HAND in the comments; the tests
assert exact values (1e-9 tolerance where floating point division is
involved, exact equality on bps roundings where the arithmetic is exact).

Fixtures:
  A  long win           : entry 100 -> exit 101, LONG,  costs 33.5+10 bps
  B  short win          : entry 100 -> exit  99, SHORT, costs 33.5+10 bps
  C  short loss         : entry 100 -> exit 102, SHORT, costs 33.5+10 bps
  D  cost exactly once  : flat trade, band-C costs 83.75+25 bps (x3.35 open)
  E  PF mixed           : nets +100/+50/-40/-25 bps  -> PF 2.3077, exp 21.25
  F  delisting exit     : flagged record is SCORED, never dropped
  G  folds + pooled     : F1 mean -93.5 bps, F2 56.5, pooled -43.5, PF 0.4641
  H  concentration      : 2 names; shares 113/356.5 and 243.5/356.5
  I  Band-1 bar         : date-only/anchor ratio 0.8 >= 0.50 -> fires
"""
from __future__ import annotations

import math
import os
import sys

import pytest

ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ENGINE_DIR)

from scoring import gates, score as S  # noqa: E402


def mkrec(direction, entry, exit_, c_entry, c_exit, ticker="AAA", fold="F1",
          delisting=False):
    return {
        "direction": direction,
        "entry_price": entry,
        "exit_price": exit_,
        "cost_entry_bps_x1": c_entry,
        "cost_exit_bps_x1": c_exit,
        "ticker": ticker,
        "fold": fold,
        "delisting_exit": delisting,
    }


# ---------------------------------------------------------------- fixtures --

def test_A_long_win_hand_computed():
    # gross = 101/100 - 1 = 0.01 ; RT cost x1 = (33.5+10)/1e4 = 0.00435
    # net = 0.00565 -> 56.5 bps
    # x1.5: cost 65.25 bps -> net 34.75 bps ; x2.0: cost 87 bps -> net 13.0 bps
    r = mkrec("LONG", 100.0, 101.0, 33.5, 10.0)
    assert S.event_gross_return(r) == pytest.approx(0.01, abs=1e-12)
    assert S.event_net_return(r, 1.0) * 1e4 == pytest.approx(56.5, abs=1e-9)
    assert S.event_net_return(r, 1.5) * 1e4 == pytest.approx(34.75, abs=1e-9)
    assert S.event_net_return(r, 2.0) * 1e4 == pytest.approx(13.0, abs=1e-9)


def test_B_short_side_hand_computed():
    # SHORT gross = 1 - 99/100 = 0.01 -> identical economics to fixture A
    r = mkrec("SHORT", 100.0, 99.0, 33.5, 10.0)
    assert S.event_gross_return(r) == pytest.approx(0.01, abs=1e-12)
    assert S.event_net_return(r, 1.0) * 1e4 == pytest.approx(56.5, abs=1e-9)
    # short loss: 1 - 102/100 = -0.02 -> net -243.5 bps
    r2 = mkrec("SHORT", 100.0, 102.0, 33.5, 10.0)
    assert S.event_net_return(r2, 1.0) * 1e4 == pytest.approx(-243.5, abs=1e-9)


def test_D_cost_exactly_once_per_fill():
    # Band-C entry at the Q-2 open band: 25 x 3.35 = 83.75 bps; exit 25 bps.
    # Flat trade (gross 0): net x1 = -108.75 bps EXACTLY (two fills, once each).
    # A double-counted side would give -217.5 at x1.0.
    r = mkrec("LONG", 50.0, 50.0, 83.75, 25.0)
    assert S.event_net_return(r, 1.0) * 1e4 == pytest.approx(-108.75, abs=1e-9)
    assert S.event_round_trip_cost_return(r, 1.0) * 1e4 == pytest.approx(108.75, abs=1e-9)
    assert S.event_round_trip_cost_return(r, 2.0) * 1e4 == pytest.approx(217.5, abs=1e-9)
    assert S.event_net_return(r, 2.0) * 1e4 == pytest.approx(-217.5, abs=1e-9)


def test_E_pf_mixed_hand_computed():
    # nets: +100, +50, -40, -25 bps -> gains 150, losses -65
    # PF = 150/65 = 2.307692... ; expectancy = (100+50-40-25)/4 = 21.25 bps
    nets = [0.0100, 0.0050, -0.0040, -0.0025]
    agg = S.aggregate(nets)
    assert agg["n"] == 4
    assert agg["net_expectancy_bps"] == pytest.approx(21.25, abs=1e-9)
    assert agg["pf"] == pytest.approx(2.3077, abs=1e-4)
    assert agg["positive_events"] == 2 and agg["negative_events"] == 2


def test_E2_pf_no_losses_is_infinite_class():
    agg = S.aggregate([0.01, 0.005])
    assert agg["pf"] is None and agg["pf_class"] == "NO_LOSSES"
    assert gates._pf_pass(agg) is True  # mechanically passes a finite PF bar


def test_F_delisting_exit_scored_not_dropped():
    # LONG 10 -> 9 = -10% gross; net x1 = -1000 - 43.5 = -1043.5 bps.
    # A delisting-flagged record is SCORED (counted), never silently dropped.
    r = mkrec("LONG", 10.0, 9.0, 33.5, 10.0, delisting=True)
    assert r["delisting_exit"] is True
    agg = S.aggregate([S.event_net_return(r, 1.0)])
    assert agg["n"] == 1
    assert agg["net_expectancy_bps"] == pytest.approx(-1043.5, abs=1e-9)


def test_G_folds_and_pooled_hand_computed():
    # F1: fixtures A (net 56.5) + C (net -243.5) -> mean -93.5 bps
    # F2: fixture B (net 56.5)
    # pooled mean = (56.5 - 243.5 + 56.5)/3 = -43.5 bps
    # pooled PF = (56.5+56.5)/243.5 = 0.464067...
    a = mkrec("LONG", 100.0, 101.0, 33.5, 10.0, fold="F1")
    c = mkrec("SHORT", 100.0, 102.0, 33.5, 10.0, fold="F1")
    b = mkrec("SHORT", 100.0, 99.0, 33.5, 10.0, fold="F2")
    fa = S.fold_aggregates([a, c, b], 1.0, gates.FOLD_ORDER)
    assert fa["F1"]["net_expectancy_bps"] == pytest.approx(-93.5, abs=1e-9)
    assert fa["F2"]["net_expectancy_bps"] == pytest.approx(56.5, abs=1e-9)
    assert "F3" not in fa  # folds without support are omitted
    pooled = S.aggregate([S.event_net_return(r, 1.0) for r in (a, c, b)])
    assert pooled["net_expectancy_bps"] == pytest.approx(-43.5, abs=1e-9)
    assert pooled["pf"] == pytest.approx(0.4641, abs=1e-4)
    assert gates.fold_positive_count(fa) == 1


def test_H_concentration_hand_computed():
    # name AAA: two events of +56.5 bps -> sum 113.0 ; name BBB: -243.5
    # abs_total = 356.5 ; shares = 113/356.5 = 0.316971, 243.5/356.5 = 0.683029
    a = mkrec("LONG", 100.0, 101.0, 33.5, 10.0, ticker="AAA")
    a2 = mkrec("LONG", 100.0, 101.0, 33.5, 10.0, ticker="AAA")
    b = mkrec("SHORT", 100.0, 102.0, 33.5, 10.0, ticker="BBB")
    c = S.concentration([a, a2, b], 1.0)
    assert c["n_names"] == 2
    assert c["max_share"] == pytest.approx(243.5 / 356.5, abs=1e-6)
    assert c["top"][0]["ticker"] == "BBB"
    assert c["top"][0]["share_abs_denom"] == pytest.approx(243.5 / 356.5, abs=1e-6)
    assert c["top"][1]["share_abs_denom"] == pytest.approx(113.0 / 356.5, abs=1e-6)


def test_I_band1_bar_fires_at_ratio_0_8():
    # anchor: 10 events each net +50 bps (gross 93.5 - cost 43.5)
    # date-only: 10 events each net +40 bps (gross 83.5 - cost 43.5)
    # ratio = 0.8 >= 0.50 -> identity DIES (fires)
    def recs(exit_mult):
        return [mkrec("LONG", 100.0, 100.0 * exit_mult, 33.5, 10.0,
                      ticker=f"T{i}") for i in range(10)]
    anchor = recs(1.00935)    # gross 93.5 bps -> net 50 bps
    dateonly = recs(1.00835)  # gross 83.5 bps -> net 40 bps
    assert S.net_expectancy_bps(anchor, 1.0) == pytest.approx(50.0, abs=1e-6)
    assert S.net_expectancy_bps(dateonly, 1.0) == pytest.approx(40.0, abs=1e-6)
    ident = gates.identity_bars(anchor, [], dateonly, {})
    b1 = ident["BAND1_DATEONLY"]
    assert b1["adjudicated"] is True
    assert b1["fired"] is True
    assert b1["value"] == pytest.approx(0.8, abs=1e-6)
    assert b1["margin"] == pytest.approx(-0.3, abs=1e-6)


def test_I2_band1_not_adjudicated_for_nonpositive_anchor():
    # anchor net = -43.5 bps (all three fixtures below lose) -> NOT adjudicated
    recs = [mkrec("SHORT", 100.0, 102.0, 33.5, 10.0) for _ in range(3)]
    ident = gates.identity_bars(recs, [], recs[:1], {})
    assert ident["BAND1_DATEONLY"]["adjudicated"] is False
    assert ident["BAND1_DATEONLY"]["fired"] is False


def test_J_baseline_buy_hold_hand_computed():
    # Buy-and-hold ignores the signal direction and holds every event LONG:
    # LONG 100 -> 101 with costs 43.5 bps: net = 100 - 43.5 = +56.5 bps
    up = mkrec("LONG", 100.0, 101.0, 33.5, 10.0)
    base = gates.baseline_buy_hold([up])
    assert base["pooled_net_expectancy_bps"] == pytest.approx(56.5, abs=1e-9)
    # the same price path taken SHORT by the signal (a signal winner, 100->99)
    # held LONG by the baseline: -100 - 43.5 = -143.5 bps
    short_rec = mkrec("SHORT", 100.0, 99.0, 33.5, 10.0)  # signal-short winner
    base2 = gates.baseline_buy_hold([short_rec])
    assert base2["pooled_net_expectancy_bps"] == pytest.approx(-143.5, abs=1e-9)


def test_K_stress_and_fold_bar_mechanics():
    # 4 folds all net-positive -> FOLD_BAR passes (>=3); stress bar passes
    recs = []
    for i, f in enumerate(("F1", "F2", "F3", "F4")):
        # gross 93.5 bps -> net 50 bps at x1 ; at x2.0: 93.5 - 87 = 6.5 bps > 0
        recs.append(mkrec("LONG", 100.0, 100.935, 33.5, 10.0, fold=f))
    cb = gates.cell_bars(recs, "TEST")
    assert cb["bars"]["FOLD_BAR"]["fired"] is False
    assert cb["bars"]["PF_BAR_1X"]["fired"] is False  # pf = None (no losses)
    assert cb["bars"]["STRESS_BAR"]["fired"] is False  # 6.5 bps > 0 at x2.0
    assert math.isclose(cb["agg_2x"]["net_expectancy_bps"], 6.5, abs_tol=1e-6)


def test_L_placebo_structural_invariance_detected():
    # The within-(issuer,form,year) stamp shuffle preserves the (ticker,stamp)
    # multiset -> booked-record multiset identical -> draws reproduce the
    # anchor BY CONSTRUCTION -> placebo classified NOT adjudicable, no fire.
    # Two events A/B; the "permuted" book swaps their stamps.
    a = mkrec("LONG", 100.0, 101.0, 33.5, 10.0, ticker="A")
    b = mkrec("SHORT", 100.0, 102.0, 33.5, 10.0, ticker="B")
    a["acceptance_utc"] = "2020-01-01T10:00:00Z"
    b["acceptance_utc"] = "2020-06-01T10:00:00Z"
    a_perm = dict(a); a_perm["acceptance_utc"] = b["acceptance_utc"]  # swapped
    b_perm = dict(b); b_perm["acceptance_utc"] = a["acceptance_utc"]
    # entry/exit/direction move with the clock, but the multiset is preserved:
    # give the permuted records each other's fills to emulate the invariance
    a_perm2 = dict(b); a_perm2["acceptance_utc"] = b["acceptance_utc"]
    b_perm2 = dict(a); b_perm2["acceptance_utc"] = a["acceptance_utc"]
    ident = gates.identity_bars([a, b], [], [], {1: [a_perm2, b_perm2]})
    p = ident["PERMUTED_PLACEBO"]
    assert p["structurally_invariant"] is True
    assert p["adjudicated"] is False
    assert p["fired"] is False
    assert p["draws"]["1"]["stamp_multiset_invariant"] is True
    assert p["draws"]["1"]["booked_record_multiset_invariant"] is True
    assert p["draws"]["1"]["ratio_vs_anchor"] == pytest.approx(1.0, abs=1e-9)


def test_L2_placebo_non_invariant_adjudicates():
    # a genuinely moved clock (different stamp set) must adjudicate
    a = mkrec("LONG", 100.0, 101.0, 33.5, 10.0, ticker="A")
    b = mkrec("SHORT", 100.0, 102.0, 33.5, 10.0, ticker="B")
    a["acceptance_utc"] = "2020-01-01T10:00:00Z"
    b["acceptance_utc"] = "2020-06-01T10:00:00Z"
    p1 = dict(a); p1["ticker"] = "A"; p1["entry_price"] = 100.0
    p1["acceptance_utc"] = "2019-03-01T10:00:00Z"  # stamp NOT in the anchor set
    p1["exit_price"] = 100.935  # different fills -> different aggregate
    p2 = dict(b); p2["ticker"] = "B"; p2["entry_price"] = 100.0
    p2["acceptance_utc"] = "2019-09-01T10:00:00Z"  # stamp NOT in the anchor set
    p2["exit_price"] = 100.935
    ident = gates.identity_bars([a, b], [], [], {1: [p1, p2]})
    p = ident["PERMUTED_PLACEBO"]
    assert p["structurally_invariant"] is False
    assert p["adjudicated"] is True
    assert p["draws"]["1"]["stamp_multiset_invariant"] is False
