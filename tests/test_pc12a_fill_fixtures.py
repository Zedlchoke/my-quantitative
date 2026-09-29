"""PC12A fixture accounting gate: fx1..fx6 equality at 1e-9.

Implements the runner spec of
``journal/fixtures/README.md`` verbatim (timeline, fills, swap lines,
totals, the section-6 decomposition invariant, structural journal laws,
per-fixture mechanism pins) against the six hand-computed gates committed
in the cycle's control directory (consumed read-only by absolute path).
"""

import json
import pathlib

import pytest

from research.pc12a.books import FillAccountingEngine

CTRL = pathlib.Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/"
    "portfolio-composite-12assets-100k-v1/integration/research/control/"
    "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1")
FIX = CTRL / "journal/fixtures"
TOL = 1e-9

FIXTURES = [
    "fx1_open_close_same_day",
    "fx2_overnight_hold_with_wed",
    "fx3_netting_two_legs_opposite",
    "fx4_blocked_signal",
    "fx5_deferred_cost_guard",
    "fx6_worst_fill_grading",
]


@pytest.mark.parametrize("fid", FIXTURES)
def test_fill_accounting_fixture(fid):
    fx = json.loads((FIX / f"{fid}.json").read_text())
    conv = fx["conventions"]
    exp = fx["expected"]

    engine = FillAccountingEngine(conv)
    out = engine.replay(bars=fx["input_bars"],
                        decisions=fx["decisions"],
                        guard_state=fx.get("guard_state"))

    # 1. timeline: cash / units / equity at EVERY step (strict order)
    assert len(out.timeline) == len(exp["timeline"])
    for got, want in zip(out.timeline, exp["timeline"]):
        assert got["event"] == want["event"], (want["event"], got["event"])
        assert got["units_after"] == want["units_after"]
        for k in ("cash_usd_after", "equity_usd_after"):
            assert abs(got[k] - want[k]) < TOL, (want["event"], k)
        # book identity at every step
        assert abs(got["equity_usd_after"]
                   - (got["cash_usd_after"]
                      + got["units_after"] * want["mark_mid"])) < TOL
        assert abs(got["mark_mid"] - want["mark_mid"]) < TOL

    # 2. fills: fill price, spread-once law, commission
    assert len(out.fills) == len(exp["fills"])
    for got, want in zip(out.fills, exp["fills"]):
        for k in ("fill_price", "mid_at_fill", "spread_once_usd",
                  "slip_beyond_halfspread_usd", "cross_cost_usd",
                  "commission_usd", "cash_delta_usd"):
            assert abs(got[k] - want[k]) < TOL, k
        # spread-once law: the two crossing lines sum to |fill - mid| x |d|
        assert abs((got["spread_once_usd"]
                    + got["slip_beyond_halfspread_usd"])
                   - abs(got["fill_price"] - got["mid_at_fill"])
                   * abs(want["delta_units"])) < TOL

    # 3. swap lines: dates, multipliers, Wednesday x3, totals
    assert len(out.swap_lines) == len(exp["costs"]["swap_lines"])
    for got, want in zip(out.swap_lines, exp["costs"]["swap_lines"]):
        assert got["ts_utc"] == want["ts_utc"]
        assert got["multiplier"] == want["multiplier"]
        assert got["wed_x3"] == want["wed_x3"]
        assert abs(got["swap_usd"] - want["swap_usd"]) < TOL

    # 4. totals + the decomposition invariant
    for k in ("spread_once_total_usd", "slip_total_usd",
              "commission_total_usd", "swap_total_usd"):
        assert abs(out.costs[k] - exp["costs"][k]) < TOL, k
    assert abs(out.gross_vs_mid_usd - exp["gross_vs_mid_usd"]) < TOL
    assert abs(out.net_pnl_usd - exp["net_pnl_usd"]) < TOL
    lhs = (out.gross_vs_mid_usd - out.costs["spread_once_total_usd"]
           - out.costs["slip_total_usd"] - out.costs["commission_total_usd"]
           - out.costs["swap_total_usd"])
    equity_delta = out.timeline[-1]["equity_usd_after"] \
        - conv["initial_cash_usd"]
    assert abs(lhs - equity_delta) < TOL           # THE invariant, to 1e-9
    assert abs(out.residual) < TOL                  # engine-side residual
    assert abs(exp["decomposition"]["residual"]) < TOL  # fixture self-check

    # 5. structural journal laws
    for row in (out.vote_rows + out.blocked_rows + out.deferred_rows):
        assert row["fill_price"] is None
        assert row.get("spread_once_usd") is None
        assert row["cash_delta_usd"] == 0.0

    # per-fixture mechanism pins
    if fid == "fx4_blocked_signal":
        assert out.blocked_rows[0]["outcome"] == "BLOCKED_STALE"
        assert out.blocked_rows[0]["feature_pit_snapshot"][0][
            "max_age_ok"] is False
    if fid == "fx5_deferred_cost_guard":
        d = out.deferred_rows[0]
        assert d["outcome"] == "DEFERRED_COST_GUARD"
        assert d["order_kind"] == "DEFER"
        assert abs(d["estimate"]["est_total_usd"]
                   - fx["decisions"][1]["estimate"]["est_total_usd"]) < TOL
        assert d["units_after"] == 10_000
        assert d["guard"]["in_window_items"][-1]["usd"] == \
            pytest.approx(0.780191, abs=1e-9)
    if fid == "fx6_worst_fill_grading":
        g = out.fills[1]                       # the graded stop exit
        assert g["graded"] is True
        assert g["order_kind"] == "STOP_EXIT"
        assert abs(g["fill_price"] - exp["fills"][1]["fill_price"]) < TOL
        assert abs(g["fill_price"]
                   - (min(exp["fills"][1]["grading"]["bid_open"],
                          exp["fills"][1]["grading"]["bid_close"])
                      - conv["slip_applied_per_side"])) < TOL
        assert g["fill_price"] < fx["decisions"][0][
            "attached_standing_order"]["stop_level"]   # never at the stop
        assert abs(g["gap_excess_usd"]
                   - exp["fills"][1]["gap_excess_usd"]) < TOL
        assert g["loss_fill_candidate"] is True
        # gap excess sits INSIDE the slip line; identity intact
        assert abs(g["cross_cost_usd"] - (g["spread_once_usd"]
                                          + g["slip_beyond_halfspread_usd"]))\
            < TOL
    if fid == "fx3_netting_two_legs_opposite":
        assert len(out.vote_rows) == 4 and len(out.fills) == 2
        assert out.fills[0]["delta_units"] == 20_000
        v = exp["virtual_check"]
        assert abs(v["leg_TA_gross_vs_mid_usd"]
                   + v["leg_MB_gross_vs_mid_usd"]
                   - exp["gross_vs_mid_usd"]) < TOL
        # virtual attributions sum to the book totals exactly
        for key, book in (("spread_once_usd", "spread_once_total_usd"),
                          ("slip_usd", "slip_total_usd"),
                          ("commission_usd", "commission_total_usd")):
            assert abs(sum(r["virtual_attribution"][key]
                           for r in out.vote_rows
                           if "virtual_attribution" in r)
                       - out.costs[book]) < TOL
        assert abs(sum(r["virtual_attribution"]["gross_vs_mid_usd"]
                       for r in out.vote_rows
                       if "virtual_attribution" in r)
                   - out.gross_vs_mid_usd) < TOL


@pytest.mark.parametrize("fid", FIXTURES)
def test_fixture_reference_numbers(fid):
    """README reference table: net totals and swap totals per fixture."""
    fx = json.loads((FIX / f"{fid}.json").read_text())
    engine = FillAccountingEngine(fx["conventions"])
    out = engine.replay(fx["input_bars"], fx["decisions"],
                        fx.get("guard_state"))
    ref = {
        "fx1_open_close_same_day": (54.40717, 0.0),
        "fx2_overnight_hold_with_wed": (274.40556, 70.0),
        "fx3_netting_two_legs_opposite": (8.07764, 0.0),
        "fx4_blocked_signal": (4.900432, 0.0),
        "fx5_deferred_cost_guard": (5.658097, 14.0),
        "fx6_worst_fill_grading": (-21.560214, 0.0),
    }
    want_net, want_swap = ref[fid]
    assert out.net_pnl_usd == pytest.approx(want_net, abs=1e-6)
    assert out.costs["swap_total_usd"] == pytest.approx(want_swap, abs=1e-9)
    # fx5 ends OPEN (30,000 units); all others flat
    if fid == "fx5_deferred_cost_guard":
        assert out.timeline[-1]["units_after"] == 30_000
    else:
        assert out.timeline[-1]["units_after"] == 0


def test_fx2_seven_pip_nights_declared_calendar():
    fx = json.loads((FIX / "fx2_overnight_hold_with_wed.json").read_text())
    engine = FillAccountingEngine(fx["conventions"])
    out = engine.replay(fx["input_bars"], fx["decisions"])
    mults = [s["multiplier"] for s in out.swap_lines]
    assert mults == [1, 1, 1, 3, 1]
    assert sum(mults) == 7          # 7 pip-nights per 7 calendar nights
    assert out.swap_lines[3]["wed_x3"] is True


@pytest.mark.parametrize("tau", [1.5, 2.0])
def test_stress_sweep_proportionality(tau):
    """Spec section 5: rerun at tier tau with every variable component
    scaled. The crossing and swap lines scale EXACTLY; the commission line
    is tau x rate x |delta| x (the tau-scaled fill), so it is checked
    against its own exact formula and is within ~0.1% of tau x base. The
    invariant still closes at every tier."""
    for fid in FIXTURES:
        fx = json.loads((FIX / f"{fid}.json").read_text())
        conv = dict(fx["conventions"])
        conv["stress_tier"] = tau
        base = FillAccountingEngine(fx["conventions"]).replay(
            fx["input_bars"], fx["decisions"], fx.get("guard_state"))
        stressed = FillAccountingEngine(conv).replay(
            fx["input_bars"], fx["decisions"], fx.get("guard_state"))
        # commission: tau x rate x |delta| x the tau-scaled fill price
        exact_comm = tau * conv["commission_rate_per_side"] * sum(
            abs(f["delta_units"]) * f["fill_price"] for f in stressed.fills)
        assert stressed.costs["commission_total_usd"] == pytest.approx(
            exact_comm, rel=1e-9), fid
        assert stressed.costs["commission_total_usd"] == pytest.approx(
            tau * base.costs["commission_total_usd"], rel=5e-3), fid
        assert stressed.costs["swap_total_usd"] == pytest.approx(
            tau * base.costs["swap_total_usd"], rel=1e-9), fid
        crossing = (base.costs["spread_once_total_usd"]
                    + base.costs["slip_total_usd"])
        crossing_s = (stressed.costs["spread_once_total_usd"]
                      + stressed.costs["slip_total_usd"])
        # the graded worst-fill path is MARKET-set: its measured half-spread
        # and realized GAP EXCESS do not scale with the tier -- only the U3
        # band does. Ordinary fills scale their whole crossing distance
        # (section 5 formula), so net of the graded fills' unscaled parts
        # the crossing scales exactly.
        gap_b = base.costs.get("gap_excess_total_usd", 0.0)
        gap_s = stressed.costs.get("gap_excess_total_usd", 0.0)
        assert gap_s == pytest.approx(gap_b, rel=1e-9, abs=1e-12), fid
        band_b = base.costs.get("slip_band_total_usd", 0.0)
        band_s = stressed.costs.get("slip_band_total_usd", 0.0)
        assert band_s == pytest.approx(tau * band_b, rel=1e-9), fid
        graded_spread_b = sum(f["spread_once_usd"] for f in base.fills
                              if f.get("graded"))
        graded_spread_s = sum(f["spread_once_usd"] for f in stressed.fills
                              if f.get("graded"))
        assert graded_spread_s == pytest.approx(graded_spread_b, rel=1e-9
                                                if graded_spread_b else 1e-9,
                                                abs=1e-12), fid
        variable_b = crossing - gap_b - graded_spread_b
        variable_s = crossing_s - gap_s - graded_spread_s
        assert variable_s == pytest.approx(tau * variable_b, rel=1e-9), fid
        assert abs(stressed.residual) < TOL, fid
