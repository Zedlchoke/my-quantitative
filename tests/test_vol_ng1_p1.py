"""VOL-NG1 P1 tests (lane p1, task vol-ng1-p1-kernel-costs).

Hand-computed assertions per the dispatch packet:

1. Estimator on synthetic OHLC with KNOWN spread (Corwin-Schultz
   primary; Roll cross-check with exact serial-covariance cases);
2. Split-event VALUE INVARIANCE (4:1 split keeps value constant) and
   the VXX 64x reorg handled as a REORG event, NOT a return; the
   Volmageddon -83% session KEPT as a market return;
3. Kernel dual-book ledger EQUALITY on the degenerate hand-computed
   case (one round trip, one cost event per fill, one mark);
4. DST boundaries (16:00 America/New_York across the 2026 spring-
   forward / fall-back transitions, measured through zoneinfo) and
   the V7 bar-readable close+1 law;
5. Cost-contract constants: every living leg carries a measured
   Corwin-Schultz p90 stress spread, a Roll cross-check, an official
   expense fact (URL + digest) and the Q-16 measured roll/decay path
   component; tier ladder {1.0, 1.5, 2.0} with tier 2.0 primary.

Group-5 committed-artifact tests read ONLY committed bytes (P0 gate
inventory, fee-fact evidence, the cost contract, the raw substrate via
the read-only cycle plane).  No network, no proposals, no scoring, no
outcome numbers anywhere.
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research import accounting as shared                    # noqa: E402
from research.assets.vol_ng1 import accounting as ak        # noqa: E402
from research.assets.vol_ng1 import census as vc            # noqa: E402
from research.assets.vol_ng1 import clocks as ck            # noqa: E402
from research.assets.vol_ng1 import corp_actions as ca      # noqa: E402
from research.assets.vol_ng1 import costs as cs             # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
P0_GATE_PATH = REPO_ROOT / "research/control/vol_ng1_run/p0_gate.json"
FEE_EVIDENCE_PATH = (REPO_ROOT /
                     "research/control/vol_ng1_run/p1_fee_facts.json")
CONTRACT_PATH = (REPO_ROOT /
                 "research/control/vol_ng1_run/p1_cost_contract.json")


def _bars(*closes: float, spread_frac: float = 0.0,
          start: str = "2024-01-02") -> list[dict]:
    """Synthetic OHLC bars: close walks the given closes; high/low add
    a symmetric known spread band when spread_frac > 0."""
    from datetime import date, timedelta
    d0 = date.fromisoformat(start)
    out = []
    for i, c in enumerate(closes):
        c = float(c)
        half = c * spread_frac / 2.0
        out.append({
            "date": (d0 + timedelta(days=i)).isoformat(),
            "open": c, "high": c + half, "low": c - half,
            "close": c, "adjusted_close": c, "volume": 1000,
        })
    return out


# ===================================================================== #
# 1. Corwin-Schultz on synthetic OHLC with known spread
# ===================================================================== #
def test_cs_recovers_known_spread():
    s = 0.02
    bars = _bars(*[100.0] * 30, spread_frac=s)
    monthly = cs.corwin_schultz_monthly(bars)
    assert monthly["months"], "expected monthly estimates"
    spreads = [m["spread"] for m in monthly["months"]]
    assert all(abs(x - s) < 2e-3 for x in spreads), spreads
    assert not any(m["floored"] for m in monthly["months"])


def test_cs_monotone_in_spread():
    small = cs.cs_stress_tier(cs.corwin_schultz_monthly(
        _bars(*[100.0] * 30, spread_frac=0.01)))
    large = cs.cs_stress_tier(cs.corwin_schultz_monthly(
        _bars(*[100.0] * 30, spread_frac=0.05)))
    assert large["p50_spread_frac"] > small["p50_spread_frac"]
    assert large["p90_spread_frac"] >= large["p50_spread_frac"]


def test_cs_negative_alpha_floored_to_zero_and_counted():
    # tiny daily ranges, huge 2-day overlap => alpha < 0 (CS floor)
    bars = [
        {"date": "2024-01-02", "high": 100.10, "low": 99.90,
         "close": 100.0},
        {"date": "2024-01-03", "high": 109.90, "low": 109.70,
         "close": 109.8},
    ]
    monthly = cs.corwin_schultz_monthly(bars)
    assert len(monthly["months"]) == 1
    assert monthly["months"][0]["floored"] is True
    assert monthly["months"][0]["spread"] == 0.0
    assert monthly["floored_months"] == 1


def test_percentile_linear_convention_hand_computed():
    vals = sorted([1.0, 2.0, 3.0, 4.0])
    assert cs.percentile(vals, 0.5) == pytest.approx(2.5)
    assert cs.percentile(vals, 0.9) == pytest.approx(3.7)
    assert cs.percentile([7.0], 0.9) == 7.0


# ===================================================================== #
# 1b. Roll cross-check: exact serial-covariance cases
# ===================================================================== #
def test_roll_hand_computed_exact_unit_bounce():
    # closes 101,100,101,100,101 -> dP = [-1,+1,-1,+1]; products = -3;
    # mean-centred population cov over 3 lags = -1 => S = 2*sqrt(1)
    out = cs.roll_spread([101.0, 100.0, 101.0, 100.0, 101.0])
    assert out["lag1_autocov"] == pytest.approx(-1.0, abs=1e-12)
    assert out["spread_frac"] == pytest.approx(2.0, abs=1e-12)


def test_roll_constant_series_zero():
    out = cs.roll_spread([10.0, 10.0, 10.0, 10.0])
    assert out["lag1_autocov"] == 0.0
    assert out["spread_frac"] == 0.0


def test_roll_bid_ask_bounce_doubles_gap_documented():
    # perfect alternation between 10 and 10.1 (zero-mean dP):
    # cov = -(0.1)^2 exactly => S = 2 * gap (the documented
    # degenerate-series property; CS is primary, Roll is a cross-check)
    out = cs.roll_spread([10.0, 10.1, 10.0, 10.1, 10.0])
    assert out["spread_frac"] == pytest.approx(0.2, abs=1e-12)


def test_roll_needs_three_closes():
    with pytest.raises(cs.CostsError):
        cs.roll_spread([1.0, 2.0])


# ===================================================================== #
# 2. Event-adjusted position layer (synthetic, known factors)
# ===================================================================== #
def test_split_4_for_1_keeps_value_constant():
    pos_shares, pos_price = 100.0, 40.0
    event = {"symbol": "TEST", "date": "2024-01-03", "kind": "SPLIT",
             "factor": 4.0, "nominal_factor": 4.0,
             "raw_ratio": 4.0, "adjusted_ratio": 1.0,
             "p0_classification": "ADJUSTED_CONTINUOUS",
             "named_note": None, "provenance": "fixture"}
    shares, price = ca.apply_event(pos_shares, pos_price, event)
    assert shares == pytest.approx(25.0)
    assert price == pytest.approx(160.0)
    # VALUE INVARIANCE (the hand-computed law)
    assert shares * price == pytest.approx(
        pos_shares * pos_price, abs=1e-12)


def test_vxx_64x_reorg_is_not_a_return():
    bars = _bars(1.0, 64.0)
    event = {"symbol": "VXX", "date": "2024-01-03", "kind": "REORG",
             "factor": 64.0, "nominal_factor": 64.0,
             "raw_ratio": 64.0, "adjusted_ratio": 64.0,
             "p0_classification": "ADJUSTED_TRACKS_RAW",
             "named_note": "uncompensated reorg (fixture)",
             "provenance": "fixture"}
    adj = ca.event_adjusted_closes(bars, [event])
    ratios = ca.continuity_residuals(bars, [event])
    # the 64x step is CANCELLED from the return stream, not booked
    assert ratios["per_event"][0]["adjusted_ratio"] == \
        pytest.approx(1.0, abs=1e-12)
    # value-preserving restatement: 6400 sh @ 1 -> 100 sh @ 64
    shares, price = ca.apply_event(6400.0, 1.0, event)
    assert shares == pytest.approx(100.0)
    assert price == pytest.approx(64.0)
    assert shares * price == pytest.approx(6400.0, abs=1e-9)
    assert adj  # adjusted series built


def test_volmageddon_price_event_is_kept_as_a_return():
    bars = _bars(100.0, 17.0426)
    event = {"symbol": "SVXY", "date": "2024-01-03",
             "kind": "PRICE_EVENT", "factor": 1.0,
             "nominal_factor": None, "raw_ratio": 0.170426,
             "adjusted_ratio": 0.170426,
             "p0_classification": "ADJUSTED_TRACKS_RAW",
             "named_note": "market return (fixture)",
             "provenance": "fixture"}
    ratios = ca.continuity_residuals(bars, [event])
    # NO restatement: the -83% session stays a market return
    assert ratios["per_event"][0]["adjusted_ratio"] == \
        pytest.approx(0.170426, abs=1e-12)
    shares, price = ca.apply_event(100.0, 100.0, event)
    assert (shares, price) == (100.0, 100.0)


def test_build_event_table_from_synthetic_inventory():
    inventory = {
        "by_symbol": {
            "AAA": {"step_events": [
                {"date": "2024-02-01", "raw_ratio": 3.990953,
                 "adjusted_ratio": 0.997738,
                 "implied_factor": 4.0,
                 "classification": "ADJUSTED_CONTINUOUS"},
                {"date": "2024-03-01", "raw_ratio": 0.170426,
                 "adjusted_ratio": 0.170426,
                 "implied_factor": 1.0,
                 "classification": "ADJUSTED_TRACKS_RAW"},
            ]},
        },
        "total_steps": 2, "gate_path": "fixture",
    }
    table = ca.build_event_table(inventory)
    evs = table["AAA"]
    assert evs[0]["kind"] == "SPLIT"
    assert evs[0]["nominal_factor"] == 4.0
    assert evs[0]["factor"] == pytest.approx(3.990953 / 0.997738,
                                             rel=1e-9)
    assert evs[1]["kind"] == "REORG"      # tracks-raw default
    assert evs[1]["factor"] == pytest.approx(0.170426)


def test_named_price_event_override_wins():
    inventory = {
        "by_symbol": {
            "SVXY": {"step_events": [
                {"date": "2018-02-06", "raw_ratio": 0.170426,
                 "adjusted_ratio": 0.170426, "implied_factor": 1.0,
                 "classification": "ADJUSTED_TRACKS_RAW"},
            ]},
        },
        "total_steps": 1, "gate_path": "fixture",
    }
    table = ca.build_event_table(inventory)
    ev = table["SVXY"][0]
    assert ev["kind"] == "PRICE_EVENT"     # named override wins
    assert ev["factor"] == 1.0
    assert "dispatch packet" in ev["provenance"]


def test_uncovered_step_scan_fails_closed():
    bars = _bars(10.0, 50.0, 50.0)  # 5x step, no event
    assert len(ca.scan_uncovered_steps(bars, [])) == 1
    covered = [{"symbol": "TEST", "date": bars[1]["date"],
                "kind": "SPLIT", "factor": 5.0, "nominal_factor": 5.0,
                "raw_ratio": 5.0, "adjusted_ratio": 1.0,
                "p0_classification": "ADJUSTED_CONTINUOUS",
                "named_note": None, "provenance": "fixture"}]
    assert ca.scan_uncovered_steps(bars, covered) == []


# ===================================================================== #
# 2b. Committed P0 inventory -> event table (real, committed bytes)
# ===================================================================== #
def test_committed_p0_inventory_consumed_fail_closed():
    inv = ca.load_inventory()
    assert inv["total_steps"] == 27
    assert set(inv["by_symbol"]) == {"VXX", "UVXY", "SVXY", "VIXY",
                                     "VIXM", "VXZ"}


def test_named_events_measured_factors():
    table = ca.build_event_table(ca.load_inventory())
    by_key = {(e["symbol"], e["date"]): e
              for evs in table.values() for e in evs}
    vxx_split = by_key[("VXX", "2024-07-24")]
    assert vxx_split["kind"] == "SPLIT"
    assert vxx_split["factor"] == pytest.approx(4.0, rel=1e-4)
    uvxy_split = by_key[("UVXY", "2025-11-20")]
    assert uvxy_split["kind"] == "SPLIT"
    assert uvxy_split["factor"] == pytest.approx(5.0, rel=1e-4)
    vxx_reorg = by_key[("VXX", "2018-01-25")]
    assert vxx_reorg["kind"] == "REORG"
    assert vxx_reorg["factor"] == pytest.approx(64.0, rel=1e-4)
    svxy_px = by_key[("SVXY", "2018-02-06")]
    assert svxy_px["kind"] == "PRICE_EVENT"


def test_continuity_on_real_bars_named_events():
    # consumes the committed raw substrate through the read-only plane
    from research.assets.vol_ng1 import plane_adapter as pa
    plane = pa.VolNg1Plane()
    table = ca.build_event_table(ca.load_inventory())
    named = [("VXX", "2024-07-24"), ("VXX", "2018-01-25"),
             ("SVXY", "2018-02-06"), ("UVXY", "2025-11-20")]
    bars_cache = {}
    for sym, date_s in named:
        if sym not in bars_cache:
            bars_cache[sym] = json.loads(
                plane.consume(f"{sym}.US_eod.json")["data"])
        ev = next(e for e in table[sym] if e["date"] == date_s)
        res = ca.continuity_residuals(bars_cache[sym], [ev])
        row = res["per_event"][0]
        if ev["kind"] in ("SPLIT", "REORG"):
            assert res["max_abs_mechanical_residual"] < 1e-4
        else:
            assert row["adjusted_ratio"] == pytest.approx(
                0.170426, abs=1e-4)


def test_full_event_table_covers_every_real_raw_step():
    from research.assets.vol_ng1 import plane_adapter as pa
    plane = pa.VolNg1Plane()
    table = ca.build_event_table(ca.load_inventory())
    for leg in ("VXX", "UVXY", "SVXY", "VIXY", "VIXM", "VXZ"):
        bars = json.loads(plane.consume(f"{leg}.US_eod.json")["data"])
        ca.require_coverage(leg, table[leg])
        assert ca.scan_uncovered_steps(bars, table[leg]) == [], leg
        res = ca.continuity_residuals(bars, table[leg])
        assert res["max_abs_mechanical_residual"] < 1e-4, leg
        assert ca.inventory_mismatches(ca.load_inventory(), table) == []


# ===================================================================== #
# 3. Kernel: degenerate dual-book case + ledger equality
# ===================================================================== #
def test_kernel_degenerate_case_hand_computed():
    rt = ak.book_round_trip(direction=1, notional_usd=10_000.0,
                            entry_price=40.0, exit_price=44.0,
                            stress_spread_frac=0.02)
    assert rt["gross_pnl_usd"] == pytest.approx(1000.0, abs=1e-9)
    assert rt["fills"]["1.0"]["cost_per_fill_usd"] == \
        pytest.approx(100.0, abs=1e-9)
    assert rt["fills"]["1.5"]["cost_per_fill_usd"] == \
        pytest.approx(150.0, abs=1e-9)
    assert rt["fills"]["2.0"]["cost_per_fill_usd"] == \
        pytest.approx(200.0, abs=1e-9)
    assert rt["fills"]["1.0"]["fills"] == 2  # once per fill x 2 fills
    assert rt["net_pnl_usd_by_tier"]["1.0"] == \
        pytest.approx(800.0, abs=1e-9)
    assert rt["net_pnl_usd_by_tier"]["1.5"] == \
        pytest.approx(700.0, abs=1e-9)
    assert rt["net_pnl_usd_by_tier"]["2.0"] == \
        pytest.approx(600.0, abs=1e-9)


def test_kernel_dual_book_ledger_equality():
    rt = ak.book_round_trip(direction=-1, notional_usd=5_000.0,
                            entry_price=10.0, exit_price=9.0,
                            stress_spread_frac=0.04)
    ledger = ak.dual_book_ledger([rt], starting_equity=50_000.0)
    books = ledger["books"]
    # short 10 -> 9: gross = -1 * 5000 * (9/10 - 1) = +500
    assert books["GROSS"]["equity_delta"] == pytest.approx(
        500.0, abs=1e-9)
    assert books["GROSS"]["cost_total"] == 0.0
    # tier 1.0: half-spread 2% => 100/fill x 2 fills = 200
    assert books["NET_1.0"]["cost_total"] == pytest.approx(
        200.0, abs=1e-9)
    assert books["NET_1.0"]["equity_delta"] == pytest.approx(
        300.0, abs=1e-9)
    assert books["NET_2.0"]["equity_delta"] == pytest.approx(
        100.0, abs=1e-9)
    assert ledger["primary_book"] == "NET_2.0"
    assert ledger["dual_book_equality_ok"] is True
    for name, row in books.items():
        assert row["identity_ok"] is True, name
        assert row["shared_identity"]["identity_ok"] is True


def test_kernel_ledger_multi_trip_flow_totals():
    rt1 = ak.book_round_trip(direction=1, notional_usd=1_000.0,
                             entry_price=10.0, exit_price=11.0,
                             stress_spread_frac=0.02)
    rt2 = ak.book_round_trip(direction=1, notional_usd=1_000.0,
                             entry_price=11.0, exit_price=10.0,
                             stress_spread_frac=0.02)
    ledger = ak.dual_book_ledger([rt1, rt2], starting_equity=1_000.0)
    # gross flows: +100 and -90.909090909...
    gross = 100.0 + 1000.0 * (10.0 / 11.0 - 1.0)
    assert ledger["books"]["GROSS"]["flow_total"] == pytest.approx(
        gross, abs=1e-9)
    # tier 2.0: 20 per fill x 2 fills x 2 round trips = 80 total
    assert ledger["books"]["NET_2.0"]["cost_total"] == \
        pytest.approx(80.0, abs=1e-9)
    assert ledger["books"]["NET_2.0"]["equity_delta"] == \
        pytest.approx(gross - 80.0, abs=1e-9)
    assert ledger["dual_book_equality_ok"] is True


def test_kernel_scored_path_refused_fail_closed():
    rt = ak.book_round_trip(direction=1, notional_usd=100.0,
                            entry_price=1.0, exit_price=1.1,
                            stress_spread_frac=0.02)
    with pytest.raises(ak.AccountingRefused):
        ak.compute_outcomes([rt])                       # scored=False
    with pytest.raises(ak.AccountingRefused):
        ak.compute_outcomes([rt], scored=True)          # no authority
    with pytest.raises(ak.AccountingRefused):
        ak.compute_outcomes([rt], scored=True,
                            market_authority="DOCUMENTED_CANDIDATE")


def test_kernel_tier_ladder_fail_closed():
    with pytest.raises(ak.AccountingRefused):
        ak.per_fill_cost_usd(1_000.0, 0.02, 1.3)
    with pytest.raises(ak.AccountingRefused):
        ak.per_fill_cost_usd(-1.0, 0.02, 2.0)
    with pytest.raises(ak.AccountingRefused):
        ak.per_fill_cost_usd(1_000.0, 1.5, 2.0)  # spread > 100%


def test_kernel_shared_module_inherited_not_forked():
    # the shared root module provides the identity reconciliation and
    # the explicit legacy-row adapter (never a silent 0)
    with pytest.raises(shared.AccountingFieldError):
        ak.canonical_flow({"pnl": 1.0})
    assert ak.canonical_flow({"realized_pnl": 3.5}) == 3.5
    assert ak.canonical_flow({"canonical_pnl": 1.25,
                              "realized_pnl": 3.5}) == 1.25


# ===================================================================== #
# 4. Clocks: UTC/NY DST boundaries + V7 bar-readable close+1
# ===================================================================== #
def test_dst_boundaries_hand_computed():
    rep = ck.dst_boundary_report()
    assert rep["all_match"] is True
    rows = rep["boundaries"]
    assert rows["est_midwinter"]["close_utc"] == \
        "2026-01-15T21:00:00+00:00"      # EST: 16:00 NY = 21:00 UTC
    assert rows["edt_midsummer"]["close_utc"] == \
        "2026-07-15T20:00:00+00:00"      # EDT: 16:00 NY = 20:00 UTC
    # first session after each 2026 transition
    assert rows["edt_after_spring_forward"]["close_utc"] == \
        "2026-03-09T20:00:00+00:00"
    assert rows["est_after_fall_back"]["close_utc"] == \
        "2026-11-02T21:00:00+00:00"


def test_grid_skips_weekend_and_transition_crosses_dst():
    grid = ck.decision_grid(["2026-03-10", "2026-03-06",
                             "2026-03-09"])
    assert grid == ["2026-03-06", "2026-03-09", "2026-03-10"]
    # Friday -> Monday across the 2026-03-08 spring-forward weekend
    assert ck.next_session(grid, "2026-03-06") == "2026-03-09"
    # 16:00 America/New_York lands on 21:00 UTC (EST) then 20:00 UTC
    # (EDT) across the transition -- measured through zoneinfo
    fri = ck.ny_close_utc("2026-03-06")
    mon = ck.ny_close_utc("2026-03-09")
    assert (fri.hour, fri.minute, fri.second) == (21, 0, 0)
    assert (mon.hour, mon.minute, mon.second) == (20, 0, 0)
    assert ck.close_instant("2026-03-06") == \
        "2026-03-06T21:00:00+00:00"
    assert ck.close_instant("2026-03-09") == \
        "2026-03-09T20:00:00+00:00"


def test_v7_close_plus_1_fail_closed():
    grid = ck.decision_grid(["2024-01-02", "2024-01-03"])
    assert ck.next_session(grid, "2024-01-02") == "2024-01-03"
    with pytest.raises(ck.ClockError):
        ck.next_session(grid, "2024-01-04")     # off-grid
    with pytest.raises(ck.ClockError):
        ck.next_session(grid, "2024-01-03")     # last bar: NOT_RUN
    with pytest.raises(ck.ClockError):
        ck.decision_grid([])


def test_v7_close_plus_1_on_real_vxx_grid():
    from research.assets.vol_ng1 import plane_adapter as pa
    plane = pa.VolNg1Plane()
    bars = json.loads(plane.consume("VXX.US_eod.json")["data"])
    grid = ck.decision_grid(b["date"] for b in bars)
    assert grid[0] == "2018-01-18"
    assert grid[-1] == "2026-09-11"
    # the reorg-session executable bar is the NEXT session
    assert ck.next_session(grid, "2018-01-24") == "2018-01-25"
    assert ck.next_session(grid, "2024-07-23") == "2024-07-24"
    with pytest.raises(ck.ClockError):
        ck.next_session(grid, "2026-09-11")     # no next bar yet


# ===================================================================== #
# 5. Q-16 path-cost ladder component (synthetic exact + real law)
# ===================================================================== #
def test_path_cost_synthetic_hand_computed():
    idx = {"VIX9D": {"2024-01-02": 10.0, "2024-01-03": 10.0},
           "VIX": {"2024-01-02": 12.0, "2024-01-03": 12.0}}
    out = cs.path_cost_series(idx, "SHORT")
    # ln(10/12)/21 = -0.1823215567939546/21 = -0.008681978895...
    expected_log = math.log(10.0 / 12.0) / 21.0
    assert out["mean_daily_log"] == pytest.approx(expected_log,
                                                  abs=1e-15)
    assert out["mean_daily_bps"] == pytest.approx(
        expected_log * 1e4, abs=1e-6)
    assert out["mean_daily_bps"] == pytest.approx(-86.819789, abs=1e-4)
    # contango (front below spot) => NEGATIVE drag for a long
    assert out["mean_daily_bps"] < 0


def test_path_cost_backwardation_positive():
    idx = {"VIX9D": {"2024-01-02": 12.0},
           "VIX": {"2024-01-02": 10.0}}
    out = cs.path_cost_series(idx, "SHORT")
    assert out["mean_daily_bps"] > 0
    assert out["mean_daily_bps"] == pytest.approx(+86.819789, abs=1e-4)


def test_path_cost_mid_bucket_day_gap_90():
    idx = {"VIX3M": {"2024-01-02": 20.0},
           "VIX6M": {"2024-01-02": 24.0}}
    out = cs.path_cost_series(idx, "MID")
    assert out["day_gap"] == 90.0
    assert out["mean_daily_bps"] == pytest.approx(
        math.log(20.0 / 24.0) / 90.0 * 1e4, abs=1e-6)
    assert out["mean_daily_bps"] == pytest.approx(-20.257951, abs=1e-4)


def test_path_cost_requires_its_series():
    with pytest.raises(cs.CostsError):
        cs.path_cost_series({"VIX": {"2024-01-02": 12.0}}, "MID")


# ===================================================================== #
# 5b. Committed cost-contract constants (offline, read-only)
# ===================================================================== #
def test_fee_fact_evidence_official_sources():
    assert FEE_EVIDENCE_PATH.is_file()
    data = json.loads(FEE_EVIDENCE_PATH.read_text())
    assert data["schema"] == "vol_ng1_run/p1_fee_facts@1"
    legs = data["legs"]
    assert set(legs) == {"VXX", "UVXY", "SVXY", "VIXY", "VIXM", "VXZ"}
    for leg, row in legs.items():
        assert row["verdict"] == "MEASURED", leg
        assert row["url"].startswith(("https://www.proshares.com/",
                                      "https://www.sec.gov/")), leg
        assert len(row["sha256"]) == 64
        assert 0.0 < row["percent_per_annum"] < 2.0, leg
        assert row["bps_per_day"] == pytest.approx(
            row["percent_per_annum"] * 100.0 / 365.0, abs=1e-6)
    # the ETN investor fee is the SEC-filed 0.89%/annum fact
    assert legs["VXX"]["percent_per_annum"] == pytest.approx(0.89)
    assert legs["VXZ"]["percent_per_annum"] == pytest.approx(0.89)


def test_cost_contract_complete_and_lawful():
    assert CONTRACT_PATH.is_file()
    c = json.loads(CONTRACT_PATH.read_text())
    assert c["schema"] == "vol_ng1_run/p1_cost_contract@1"
    assert c["primary_tier"] == 2.0
    assert c["tier_ladder"] == [1.0, 1.5, 2.0]
    assert set(c["legs"]) == {"VXX", "UVXY", "SVXY", "VIXY", "VIXM",
                              "VXZ"}
    for leg, blk in c["legs"].items():
        sp = blk["spread"]
        assert sp["p90_spread_frac"] >= sp["p50_spread_frac"] >= 0.0
        assert sp["stress_tier"] == "p90"
        assert "measurable" in sp["stress_basis"]
        assert sp["n_months"] > 100
        # the CS instability on these bars is DISCLOSED, not repaired
        assert sp["n_measurable_months"] >= 3, leg
        assert sp["floored_months"] == (
            sp["n_months"] - sp["n_measurable_months"]
            - sp["skipped_months"])
        assert sp["p90_all_months_frac"] <= sp["p90_spread_frac"]
        rc = blk["roll_crosscheck"]
        assert rc["spread_frac"] >= 0.0
        # Roll is defined only for negative lag-1 serial covariance;
        # a trending (>= 0) regime yields a 0.0 cross-check, disclosed
        if rc["lag1_autocov"] >= 0.0:
            assert rc["spread_frac"] == 0.0, leg
        else:
            assert rc["spread_frac"] > 0.0, leg
        ex = blk["expense"]
        assert ex["source_sha256"] and \
            ex["source_url"].startswith("https://")
        assert ex["bps_per_day"] > 0.0
        pc = blk["path_cost"]
        assert pc["formula"] in ("ln(VIX9D/VIX)/21",
                                 "ln(VIX3M/VIX6M)/90")
        assert pc["days"] > 1000
        # Q-16 law on committed bytes: contango drag is negative on
        # average for both buckets over the measured window
        assert pc["mean_daily_bps"] < 0.0, leg
        tiers = blk["tiers"]
        assert tiers["2.0"]["primary"] is True
        assert tiers["1.0"]["primary"] is False
        assert tiers["2.0"]["execution_spread_bps_per_fill"] == \
            pytest.approx(
                2.0 * tiers["1.0"]["execution_spread_bps_per_fill"])
        assert tiers["1.5"]["execution_spread_bps_per_fill"] == \
            pytest.approx(
                1.5 * tiers["1.0"]["execution_spread_bps_per_fill"])
        # mechanisms are carried explicitly, unchanged across tiers
        assert tiers["2.0"]["expense_bps_per_day"] == \
            tiers["1.0"]["expense_bps_per_day"]
        assert tiers["2.0"]["path_mean_daily_bps"] == \
            tiers["1.0"]["path_mean_daily_bps"]


def test_cost_contract_path_bucket_assignment():
    c = json.loads(CONTRACT_PATH.read_text())
    for leg, bucket in (("VXX", "SHORT"), ("UVXY", "SHORT"),
                        ("SVXY", "SHORT"), ("VIXY", "SHORT"),
                        ("VIXM", "MID"), ("VXZ", "MID")):
        assert c["legs"][leg]["bucket"] == bucket
        assert c["legs"][leg]["path_cost"]["formula"] == (
            "ln(VIX9D/VIX)/21" if bucket == "SHORT"
            else "ln(VIX3M/VIX6M)/90")


def test_expense_drag_daily_conversion():
    c = json.loads(CONTRACT_PATH.read_text())
    for blk in c["legs"].values():
        er = blk["expense"]
        assert er["bps_per_day"] == pytest.approx(
            er["percent_per_annum"] * 100.0 / 365.0, abs=1e-6)
