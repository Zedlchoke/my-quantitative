"""COMMODITIES-NG1 P2 Q-6 feasibility tests (offline; no network).

Every assertion is hand-computed on synthetic fixtures (release-rule
week anchors incl. the measured Monday holiday shifts, DST clock
arithmetic, tiny hand-countable decision grids, warmup carve-out
arithmetic, exact cost-ceiling algebra) or re-verifies the committed
P2 artifact against the committed P0/P1 frozen substrate (digest pins,
census reproduction from the pinned CSVs, floor reconciliation, cost
ceiling recomputation from the frozen P1 contract).

Q-6 only: NO proposals, NO signal design, NO scoring, NO PnL/outcome
numbers anywhere.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import date, datetime, timezone

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

RUN_DIR = os.path.join(REPO_ROOT, "research", "control",
                       "commodities_ng1_run")

from research.assets.commodities_ng1 import feasibility as F  # noqa: E402
from research.assets.commodities_ng1.cot_census import (  # noqa: E402
    csv_to_records,
    release_instant as p0_release_instant,
)

# sha256 of the COMMITTED p2_gate.json (frozen artifact; the runner is
# never re-run inside tests -- this pin is the tamper check).
P2_GATE_SHA256 = (
    "ee32c9df86c3f33126d3899fad62f74cb880f654970791cf260e59e4652b973c")

# hand-listed measured Monday (holiday-shifted) as-of dates in the
# frozen substrate and the Friday of their report week.
MEASURED_MONDAY_SHIFTS = {
    date(2017, 7, 3): date(2017, 7, 7),
    date(2018, 12, 24): date(2018, 12, 28),
    date(2018, 12, 31): date(2019, 1, 4),
    date(2020, 12, 21): date(2020, 12, 25),
    date(2023, 7, 3): date(2023, 7, 7),
    date(2025, 11, 10): date(2025, 11, 14),
}

# frozen-floor measured literals on the committed substrate (every one
# of the 20 qualifying pairs; hand-derived from 558 weekly reports:
# 454 releases on/after 2018-01-01, minus 52 warmup => 402 counted,
# minus the single exhausted-calendar release 2026-09-11 => 401).
EXPECT_QUALIFYING_PAIRS = 20
EXPECT_INSTANTS_WINDOW = 454
EXPECT_WARMUP_LAST = "2018-12-28"
EXPECT_COUNTED_FIRST = "2019-01-04"
EXPECT_COUNTED_LAST = "2026-09-11"
EXPECT_COUNTED_EXPECTED = 402
EXPECT_MAPPED = 401
EXPECT_COVERAGE = round(EXPECT_MAPPED / EXPECT_COUNTED_EXPECTED, 6)
EXPECT_UNMAPPED = ["2026-09-11"]
EXPECT_EXPENSE_NOT_MEASURED = sorted(
    ["BAR", "CPER", "PALL", "PPLT", "SGOL", "SIVR", "UNG", "USL", "USO"])

FORBIDDEN_KEY_SUBSTRINGS = (
    "pnl", "sharpe", "sortino", "drawdown", "hit_rate", "expectancy",
    "cagr", "profit",
)


def _load(name):
    with open(os.path.join(RUN_DIR, name), encoding="utf-8") as fh:
        return json.load(fh)


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="module")
def gate():
    return _load("p2_gate.json")


@pytest.fixture(scope="module")
def p1_contract():
    return _load("p1_cost_contract.json")


@pytest.fixture(scope="module")
def p0_pairs():
    return _load("p0_market_pairs.json")


def _iter_keys(node):
    if isinstance(node, dict):
        for k, v in node.items():
            yield k
            yield from _iter_keys(v)
    elif isinstance(node, list):
        for v in node:
            yield from _iter_keys(v)


# --------------------------------------------------------------------- #
# 1. Release rule: P0 identity + measured holiday shifts (hand-computed)
# --------------------------------------------------------------------- #

def test_tuesday_release_matches_p0_rule_exactly():
    # Tuesday 2026-01-06 -> Friday 2026-01-09 15:30 America/New_York
    # (EST in January) = 20:30 UTC.  The P2 module must return the P0
    # frozen rule object verbatim (same instants, same source tag).
    inst, src = F.release_instant_for_report(date(2026, 1, 6))
    assert inst == p0_release_instant(date(2026, 1, 6))
    assert inst == datetime(2026, 1, 9, 20, 30, tzinfo=timezone.utc)
    assert src == "p0_release_instant"


def test_release_dst_boundaries_hand_computed():
    # EST winter: 15:30 ET = 20:30 UTC; EDT summer: 15:30 ET = 19:30 UTC.
    inst, _ = F.release_instant_for_report(date(2026, 1, 13))
    assert inst == datetime(2026, 1, 16, 20, 30, tzinfo=timezone.utc)
    inst, _ = F.release_instant_for_report(date(2026, 6, 9))
    assert inst == datetime(2026, 6, 12, 19, 30, tzinfo=timezone.utc)


def test_monday_holiday_shift_week_anchor_hand_computed():
    # Measured CFTC holiday-shifted Monday as-of dates: Friday 15:30 ET
    # of the SAME Mon-Sun week.  December (EST) and July (EDT) cases.
    inst, src = F.release_instant_for_report(date(2018, 12, 24))
    assert inst == datetime(2018, 12, 28, 20, 30, tzinfo=timezone.utc)
    assert src == "week_anchor_holiday_shift"
    inst, src = F.release_instant_for_report(date(2017, 7, 3))
    assert inst == datetime(2017, 7, 7, 19, 30, tzinfo=timezone.utc)
    assert src == "week_anchor_holiday_shift"


def test_every_measured_monday_shift_maps_to_hand_listed_friday():
    # The 6 measured Monday as-of dates in the frozen substrate each
    # land on the hand-listed report-week Friday -- and ONLY these six
    # Mondays exist in the substrate (fail-closed if data drifts).
    path = os.path.join(RUN_DIR, "p0_cot_weekly_targets.csv")
    with open(path, encoding="utf-8") as fh:
        records = csv_to_records(fh.read())
    dates = {r.report_date for r in records}
    mondays = {d for d in dates if d.weekday() == 0}
    assert mondays == set(MEASURED_MONDAY_SHIFTS)
    for monday, friday in MEASURED_MONDAY_SHIFTS.items():
        assert F.week_friday(monday) == friday
        inst, src = F.release_instant_for_report(monday)
        assert inst.date() == friday
        assert src == "week_anchor_holiday_shift"


def test_release_rule_refuses_other_weekdays():
    # Wednesday/Saturday/Sunday as-of dates are refused fail-closed
    # (the measured substrate contains only Tuesdays and the six
    # measured holiday-shifted Mondays).
    for bad in (date(2026, 1, 7), date(2026, 1, 10), date(2026, 1, 11)):
        with pytest.raises(F.FeasibilityRefused):
            F.release_instant_for_report(bad)


def test_week_friday_hand_computed():
    assert F.week_friday(date(2026, 1, 7)) == date(2026, 1, 9)
    assert F.week_friday(date(2018, 12, 30)) == date(2018, 12, 28)
    assert F.week_friday(date(2019, 1, 1)) == date(2019, 1, 4)
    # Tuesday identity with the P0 anchor (d + 3):
    assert F.week_friday(date(2026, 1, 6)) == date(2026, 1, 9)


def test_tuesday_rule_identity_holds_on_entire_measured_calendar():
    # For EVERY Tuesday report in the pinned substrate, the P2 week
    # anchor reduces exactly to the P0 frozen rule (552 dates).
    path = os.path.join(RUN_DIR, "p0_cot_weekly_targets.csv")
    with open(path, encoding="utf-8") as fh:
        records = csv_to_records(fh.read())
    tuesdays = sorted({r.report_date for r in records
                       if r.report_date.weekday() == 1})
    assert len(tuesdays) == 552
    for d in tuesdays:
        inst, src = F.release_instant_for_report(d)
        assert inst == p0_release_instant(d)
        assert src == "p0_release_instant"


# --------------------------------------------------------------------- #
# 2. Decision-grid census on synthetic fixtures (hand-counted)
# --------------------------------------------------------------------- #

def _synthetic_grid():
    # Reports (as-of): Tue 2017-12-19 (pre-window), Tue 2018-01-02,
    # Tue 2018-01-09, Mon 2018-12-24 (holiday shift), Tue 2019-01-08.
    # Sessions: 2018-01-08, 2018-01-16 (Mon 01-15 holiday -> Tue),
    # 2018-12-31, 2019-01-02 (calendar then exhausted).
    reports = [date(2017, 12, 19), date(2018, 1, 2), date(2018, 1, 9),
               date(2018, 12, 24), date(2019, 1, 8)]
    sessions = [date(2018, 1, 8), date(2018, 1, 16), date(2018, 12, 31),
                date(2019, 1, 2)]
    return F.census_pair_grid(reports, sessions)


def test_census_grid_synthetic_hand_counted():
    g = _synthetic_grid()
    # Window (release_date >= 2018-01-01): rel 2018-01-05, 2018-01-12,
    # 2018-12-28, 2019-01-11 => 4 rows; the pre-window release
    # 2017-12-22 is excluded by the declared window convention.
    assert g["instants_window"] == 4
    # Mapped: 01-05 -> 01-08; 01-12 -> 01-16 (Mon holiday skipped);
    # 12-28 -> 12-31.  Exhausted: 2019-01-11 -> no session.
    assert g["instants_grid_eligible"] == 3
    assert g["unmapped_release_dates"] == ["2019-01-11"]
    by_rel = {r["release_date"]: r for r in g["rows"]}
    assert by_rel["2018-01-05"]["decision_session"] == "2018-01-08"
    assert by_rel["2018-01-12"]["decision_session"] == "2018-01-16"
    assert by_rel["2018-12-28"]["decision_session"] == "2018-12-31"
    assert by_rel["2019-01-11"]["decision_session"] is None
    assert by_rel["2018-12-28"]["rule_source"] == "week_anchor_holiday_shift"
    assert by_rel["2018-01-05"]["rule_source"] == "p0_release_instant"
    # pre-window row is present in the full row set but outside window
    assert len(g["rows"]) == 5
    assert by_rel["2017-12-22"]["decision_session"] is None


def test_floors_synthetic_warmup_and_thresholds_hand_computed():
    g = _synthetic_grid()
    # warmup_weeks=2 removes rel 2018-01-05 and 2018-01-12 (both
    # mapped); counted = {12-28: mapped, 2019-01-11: unmapped}:
    # expected 2, mapped 1, coverage 0.5 exactly.
    ev = F.evaluate_floors(g, warmup_weeks=2, instant_floor=1,
                           coverage_floor=0.5)
    assert ev["warmup_carve_out_instants"] == 2
    assert ev["counted_expected_releases"] == 2
    assert ev["grid_eligible_instants"] == 1
    assert ev["release_to_session_coverage"] == 0.5
    assert ev["floor_a_instants"] == {"frozen_floor": 1, "measured": 1,
                                      "verdict": "PASS"}
    assert ev["floor_b_coverage"]["frozen_floor"] == 0.5
    assert ev["floor_b_coverage"]["measured"] == 0.5
    assert ev["floor_b_coverage"]["verdict"] == "PASS"
    assert ev["pair_meets_floors"] is True
    # identical grid, coverage floor a hair above measured: coverage
    # fails while instants pass -> pair excluded (never dropped).
    ev2 = F.evaluate_floors(g, warmup_weeks=2, instant_floor=1,
                            coverage_floor=0.5 + 1e-9)
    assert ev2["floor_a_instants"]["verdict"] == "PASS"
    assert ev2["floor_b_coverage"]["verdict"] == "FAIL"
    assert ev2["pair_meets_floors"] is False
    # instant floor above measured with generous coverage: the reverse.
    ev3 = F.evaluate_floors(g, warmup_weeks=2, instant_floor=2,
                            coverage_floor=0.4)
    assert ev3["floor_a_instants"]["verdict"] == "FAIL"
    assert ev3["floor_b_coverage"]["verdict"] == "PASS"
    assert ev3["pair_meets_floors"] is False
    # unmapped counted release is listed explicitly.
    assert ev["unmapped_release_dates_counted"] == ["2019-01-11"]


def test_floors_warmup_larger_than_window_fail_closed():
    g = _synthetic_grid()
    ev = F.evaluate_floors(g, warmup_weeks=99, instant_floor=0,
                           coverage_floor=0.0)
    assert ev["counted_expected_releases"] == 0
    assert ev["grid_eligible_instants"] == 0
    assert ev["release_to_session_coverage"] == 0.0


def test_census_refuses_duplicate_reports_and_sessions():
    with pytest.raises(F.FeasibilityRefused):
        F.census_pair_grid([date(2018, 1, 2), date(2018, 1, 2)], [])
    with pytest.raises(F.FeasibilityRefused):
        F.census_pair_grid([date(2018, 1, 2)],
                           [date(2018, 1, 8), date(2018, 1, 8)])


def test_evaluate_floors_refuses_non_census_grid():
    with pytest.raises(F.FeasibilityRefused):
        F.evaluate_floors({"schema": "something/else", "rows": []})


# --------------------------------------------------------------------- #
# 3. Cost ceilings: exact algebra on synthetic legs
# --------------------------------------------------------------------- #

def test_round_trip_ceiling_synthetic_hand_computed():
    leg = {"symbol": "SYN", "half_spread_frac_p90_per_fill": 0.0025,
           "expense_fact": {"status": "MEASURED_OFFICIAL_PAGE",
                            "expense_ratio_annual": 0.006}}
    c = F.round_trip_cost_ceiling(leg)
    # transaction = 2 fills x 0.0025 = 0.005 => 50 bps
    assert c["transaction_ceiling_frac_round_trip"] == 0.005
    assert c["transaction_ceiling_bps_round_trip"] == 50.0
    # expense at the declared 10/252 horizon: 0.006*10/252 = 2.380952...
    assert abs(c["expense_bps_at_declared_horizon"]
               - 0.006 * 10 / 252 * 1e4) < 1e-6
    assert abs(c["round_trip_cost_ceiling_bps"]
               - (0.005 + 0.006 * 10 / 252) * 1e4) < 1e-6
    assert c["expense_fail_closed"] is False
    assert c["limitation"] is None
    # horizon linearity: at 21 trading days the expense term is exactly
    # 0.006*21/252 = 0.0005 => ceiling 55.0 bps.
    c21 = F.round_trip_cost_ceiling(leg, horizon_trading_days=21)
    assert abs(c21["round_trip_cost_ceiling_bps"] - 55.0) < 1e-9


def test_round_trip_ceiling_not_measured_fail_closed():
    leg = {"symbol": "NM", "half_spread_frac_p90_per_fill": 0.004,
           "expense_fact": {"status": "NOT_MEASURED",
                            "expense_ratio_annual": None}}
    c = F.round_trip_cost_ceiling(leg)
    assert c["transaction_ceiling_bps_round_trip"] == 80.0
    assert c["round_trip_cost_ceiling_bps"] is None
    assert c["expense_bps_at_declared_horizon"] is None
    assert c["expense_fail_closed"] is True
    assert "NOT MEASURED" in c["limitation"]
    assert "conservatively or exclude" in c["limitation"]


def test_round_trip_ceiling_refuses_incomplete_legs():
    with pytest.raises(F.FeasibilityRefused):
        F.round_trip_cost_ceiling({"symbol": "X", "expense_fact": {}})
    with pytest.raises(F.FeasibilityRefused):
        F.round_trip_cost_ceiling(
            {"symbol": "X", "half_spread_frac_p90_per_fill": 0.001,
             "expense_fact": {"status": "MEASURED_OFFICIAL_PAGE",
                              "expense_ratio_annual": None}})


# --------------------------------------------------------------------- #
# 4. Committed P2 gate: hash pin, floors, structure, no-PnL
# --------------------------------------------------------------------- #

def test_p2_gate_committed_hash_pin():
    path = os.path.join(RUN_DIR, "p2_gate.json")
    assert os.path.isfile(path)
    assert _sha256_file(path) == P2_GATE_SHA256


def test_p2_gate_schema_and_verdict(gate):
    assert gate["schema"] == "commodities_ng1_run/p2_gate@1"
    assert gate["cycle_id"] == "COMMODITIES-NG1"
    assert gate["task_id"] == "commodities-ng1-p2-feasibility"
    assert gate["final_verdict"] == "PASS"
    assert gate["frozen_floors"]["declared_before_measurement"] is True
    assert gate["frozen_floors"]["instants"]["floor"] == 300
    assert gate["frozen_floors"]["instants"]["window_start"] == "2018-01-01"
    assert gate["frozen_floors"]["instants"][
        "warmup_carve_out_weeks"] == 52
    assert gate["frozen_floors"]["coverage"]["floor"] == 0.90


def test_p2_gate_no_pnl_or_scoring_keys(gate):
    # "no_pnl" is the gate's explicit prohibition marker key (its value
    # text asserts the law) -- whitelisted exactly; every other key
    # containing an outcome-number substring is a violation.
    allowed_exact = {"no_pnl"}
    banned = [k for k in _iter_keys(gate)
              if k not in allowed_exact
              and any(s in k.lower() for s in FORBIDDEN_KEY_SUBSTRINGS)]
    assert banned == []


def test_p2_gate_floor_reconciliation_measured_literals(gate):
    pp = gate["per_pair_census"]
    assert len(pp) == EXPECT_QUALIFYING_PAIRS
    for key, v in pp.items():
        fe = v["floor_evaluation"]
        assert v["instants_window"] == EXPECT_INSTANTS_WINDOW
        assert fe["warmup_carve_out_instants"] == 52
        assert fe["warmup_last_release"] == EXPECT_WARMUP_LAST
        assert fe["counted_first_release"] == EXPECT_COUNTED_FIRST
        assert fe["counted_last_release"] == EXPECT_COUNTED_LAST
        assert fe["counted_expected_releases"] == EXPECT_COUNTED_EXPECTED
        assert fe["grid_eligible_instants"] == EXPECT_MAPPED
        assert fe["release_to_session_coverage"] == EXPECT_COVERAGE
        assert fe["unmapped_release_dates_counted"] == EXPECT_UNMAPPED
        assert fe["floor_a_instants"] == {"frozen_floor": 300,
                                          "measured": EXPECT_MAPPED,
                                          "verdict": "PASS"}
        assert fe["floor_b_coverage"]["frozen_floor"] == 0.9
        assert fe["floor_b_coverage"]["measured"] == EXPECT_COVERAGE
        assert fe["floor_b_coverage"]["verdict"] == "PASS"
        assert fe["pair_meets_floors"] is True


def test_p2_gate_per_lane_bookable_set_and_no_blocked_paths(gate):
    lanes = gate["items"]["item4_frozen_floor_reconciliation"]["values"][
        "per_lane"]
    assert set(lanes) == {"A4", "A5"}
    for lane, lv in lanes.items():
        assert lv["bookable_pair_count"] == EXPECT_QUALIFYING_PAIRS
        assert len(lv["bookable_pairs"]) == EXPECT_QUALIFYING_PAIRS
        assert lv["excluded_pairs"] == {}
        assert lv["floors_met_all_qualifying_pairs"] is True
        assert lv["bookable_pairs"] == sorted(lv["bookable_pairs"])
    assert gate["items"]["item4_frozen_floor_reconciliation"]["values"][
        "blocked_paths"] == []


def test_p2_gate_pair_universe_matches_p0_qualifying_set(gate, p0_pairs):
    qualifying = sorted(
        f"{p['cot_market_code']}/{p['etp']}"
        for p in p0_pairs["pairs"] if p["qualifying"])
    assert p0_pairs["verdict"] == "PASS"
    assert len(qualifying) == EXPECT_QUALIFYING_PAIRS
    assert sorted(gate["per_pair_census"]) == qualifying
    # the dispatch-declared DBA basket triple earns pair credit and is
    # present; non-qualifying pairs are absent from the P2 census.
    for dba in ("001602/DBA", "002602/DBA", "005602/DBA"):
        assert dba in gate["per_pair_census"]
    for absent in ("084691/DBS", "083731/JO", "073732/NIB"):
        assert absent not in gate["per_pair_census"]


# --------------------------------------------------------------------- #
# 5. Committed P2 gate vs frozen P1 contract / P0 substrate
# --------------------------------------------------------------------- #

def test_p2_gate_cost_ceilings_recompute_from_frozen_contract(
        gate, p1_contract):
    vals = gate["items"]["item3_cost_ceilings"]["values"]
    legs = p1_contract["per_leg"]
    horizon = F.CEILING_HORIZON_TRADING_DAYS
    assert vals["declared_conventions"]["transaction"].startswith(
        "2 fills x half_spread_frac_p90")
    fail_closed = []
    for key, c in vals["per_pair_leg_ceilings"].items():
        leg = legs[c["symbol"]]
        half = leg["half_spread_frac_p90_per_fill"]
        assert c["half_spread_frac_p90_per_fill"] == half
        assert c["transaction_ceiling_frac_round_trip"] == 2.0 * half
        assert abs(c["transaction_bps_full_spread_p90"]
                   - leg["transaction_bps_full_spread_p90"]) < 1e-9
        fee = leg["expense_fact"]
        assert c["expense_status"] == fee["status"]
        if fee["status"] == "MEASURED_OFFICIAL_PAGE":
            rate = fee["expense_ratio_annual"]
            assert c["expense_ratio_annual"] == rate
            assert abs(c["expense_bps_at_declared_horizon"]
                       - rate * horizon / 252 * 1e4) < 1e-5
            assert abs(c["round_trip_cost_ceiling_bps"]
                       - (2.0 * half + rate * horizon / 252) * 1e4) < 1e-5
            assert c["expense_fail_closed"] is False
            assert c["expense_page_sha256"] == fee["page_sha256"]
        else:
            assert fee["status"] == "NOT_MEASURED"
            assert c["round_trip_cost_ceiling_bps"] is None
            assert c["expense_fail_closed"] is True
            assert c["limitation"]
            fail_closed.append(c["symbol"])
    assert vals["expense_not_measured_legs_fail_closed"] == sorted(
        set(fail_closed))
    assert vals["expense_not_measured_legs_fail_closed"] == \
        EXPECT_EXPENSE_NOT_MEASURED


def test_p2_gate_substrate_pins_verify():
    pins = _load("p2_gate.json")["substrate_pins"]
    assert pins["cot_weekly_targets_csv_sha256"] == _sha256_file(
        os.path.join(RUN_DIR, "p0_cot_weekly_targets.csv"))
    assert pins["p1_cost_contract_sha256"] == _sha256_file(
        os.path.join(RUN_DIR, "p1_cost_contract.json"))
    assert pins["fee_facts_sha256"] == _sha256_file(
        os.path.join(RUN_DIR, "fee_facts.json"))
    etps = pins["etp_eod_sha256"]
    assert len(etps) == 18
    for sym, pin in etps.items():
        assert pin == _sha256_file(
            os.path.join(RUN_DIR, "etp_eod", f"{sym}.csv"))


def test_p2_gate_census_reproduces_from_committed_substrate(gate):
    """Re-derive the FULL census for every pair from the pinned CSVs
    (same module, same declared conventions) and require exact
    agreement with the committed gate."""
    pins = gate["substrate_pins"]
    with open(os.path.join(RUN_DIR, "p0_cot_weekly_targets.csv"),
              encoding="utf-8") as fh:
        records = csv_to_records(fh.read())
    by_code = {}
    for r in records:
        by_code.setdefault(r.contract_market_code, []).append(r.report_date)
    sessions = {}
    for sym in pins["etp_eod_sha256"]:
        with open(os.path.join(RUN_DIR, "etp_eod", f"{sym}.csv"),
                  encoding="utf-8") as fh:
            header = fh.readline()
            assert header.strip().split(",")[0] == "date"
            sessions[sym] = sorted(
                date.fromisoformat(line.split(",")[0])
                for line in fh if line.strip())
    for key, v in gate["per_pair_census"].items():
        code, sym = key.split("/")
        grid = F.census_pair_grid(by_code[code], sessions[sym])
        fe = F.evaluate_floors(grid)
        assert grid["instants_window"] == v["instants_window"]
        assert grid["instants_grid_eligible"] == \
            v["instants_grid_eligible_window"]
        assert grid["unmapped_release_dates"] == \
            v["unmapped_release_dates_window"]
        assert fe["counted_expected_releases"] == \
            v["floor_evaluation"]["counted_expected_releases"]
        assert fe["grid_eligible_instants"] == \
            v["floor_evaluation"]["grid_eligible_instants"]
        assert fe["release_to_session_coverage"] == \
            v["floor_evaluation"]["release_to_session_coverage"]
        assert fe["warmup_last_release"] == \
            v["floor_evaluation"]["warmup_last_release"]
        assert fe["counted_first_release"] == \
            v["floor_evaluation"]["counted_first_release"]
        assert fe["counted_last_release"] == \
            v["floor_evaluation"]["counted_last_release"]


def test_p2_gate_exhausted_calendar_release_hand_checked(gate):
    # The single unmapped release on the counted window is the LAST
    # report (as-of Tue 2026-09-08): its release Friday 2026-09-11 is
    # the ETP calendars' final measured session, so no session exists
    # STRICTLY after it (clock law, not a data gap).
    for v in gate["per_pair_census"].values():
        assert v["unmapped_release_dates_window"] == ["2026-09-11"]
        assert v["etp_session_calendar"]["last"] == "2026-09-11"
        assert v["cot_weeks_measured"] == 558
