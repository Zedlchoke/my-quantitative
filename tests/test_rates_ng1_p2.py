"""RATES-NG1 P2 tests (dispatch: rates-ng1-p2-feasibility, Q-6 no-PnL).

Hand-computed census assertions on small synthetic fixtures +
committed-artifact hash checks.  No network access; no PnL, no
expectancy and no outcome number anywhere.

1. common-grid census fixtures (work item 1): intersection semantics
   (curve x ALL-FOUR-legs ETP, window-restricted), weekday-denominator
   hand count, warmup carve-out boundary, bookable-instant chain
   (V7 readable bar = previous grid session) and hand-computed EST/EDT
   decision instants across the 2026 DST boundary;
2. auction PIT grid-eligibility fixtures (work item 2): hand-computed
   end-of-announced-NY-day PIT instants (EST), same-day close refused,
   no-later-session refusal, bisection semantics, and the built-in
   clock-authority cross-check;
3. cost-ceiling fixture (work item 3): 2 x CS p90 + ACT/365F ER drag
   over the declared holding convention, hand-computed exactly;
4. committed artifacts: p2_gate.json / p2_grid_census.json /
   p2_auction_eligibility.json hash pins and full internal-consistency
   recomputation (every bookable instant re-derived through the P1
   clock; every floor re-evaluated frozen-vs-measured); the FROZEN P1
   cost contract sha256 cited by the gate; substrate verify-on-read
   re-hash of one ETP leg against the manifest pin and the P0 census;
   the P0 auction census re-verified count equality (3555).
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import date

import pytest

from research.assets.rates_ng1 import clock as ck
from research.assets.rates_ng1 import feasibility as fz
from research.assets.rates_ng1 import plane_adapter as pa

WORKTREE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RUN_DIR = os.path.join(WORKTREE, "research", "control", "rates_ng1_run")
GATE_PATH = os.path.join(RUN_DIR, "p2_gate.json")
GRID_SIDECAR_PATH = os.path.join(RUN_DIR, "p2_grid_census.json")
AUCTION_SIDECAR_PATH = os.path.join(
    RUN_DIR, "p2_auction_eligibility.json")
CONTRACT_PATH = os.path.join(RUN_DIR, "p1_cost_contract.json")
P0_AUCTION_CENSUS_PATH = os.path.join(RUN_DIR, "p0_auction_census.json")

WINDOW = fz.FEASIBILITY_WINDOW


def _weekdays(start_iso: str, end_iso: str) -> list[str]:
    d0 = date.fromisoformat(start_iso)
    d1 = date.fromisoformat(end_iso)
    out = []
    d = d0
    while d <= d1:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d = date.fromordinal(d.toordinal() + 1)
    return out


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------- #
# 1. common-grid census fixtures (hand-computed)                         #
# --------------------------------------------------------------------- #

def _jan2018_sources() -> tuple[set[str], dict[str, set[str]]]:
    """January 2018 synthetic substrate: no bar on the New Year holiday
    (Mon 2018-01-01), the curve misses Mon 2018-01-15, leg A misses
    Mon 2018-01-22.  Common grid = 20 sessions (hand count: 23 January
    weekdays - 3 missing dates)."""
    trading = set(_weekdays("2018-01-01", "2018-01-31")) - {"2018-01-01"}
    curve = trading - {"2018-01-15"}
    etp = {"LEGA": trading - {"2018-01-22"}, "LEGB": set(trading)}
    return curve, etp


def test_common_grid_intersection_semantics_hand_computed():
    curve, etp = _jan2018_sources()
    grid = fz.build_common_grid(curve, etp, ("2018-01-01", "2018-01-31"))
    assert grid == [d for d in _weekdays("2018-01-01", "2018-01-31")
                    if d not in ("2018-01-01", "2018-01-15",
                                 "2018-01-22")]
    assert len(grid) == 20                      # hand count
    # a date present on curve and only SOME legs is excluded
    partial = fz.build_common_grid(
        curve | {"2018-01-01"}, {**etp, "LEGB": set()},  # LEGB empty
        ("2018-01-01", "2018-01-31"))
    assert partial == []
    # window restriction: dates outside the window never enter the grid
    trimmed = fz.build_common_grid(
        curve, etp, ("2018-01-08", "2018-01-12"))
    assert trimmed == ["2018-01-08", "2018-01-09", "2018-01-10",
                       "2018-01-11", "2018-01-12"]


def test_expected_weekday_denominator_jan2018_hand_computed():
    # January 2018: 23 Mon-Fri days (5+5+5+5+3), hand count
    assert fz.expected_weekday_count("2018-01-01", "2018-01-31") == 23
    # the real window denominator, hand-derived by modular arithmetic:
    # 2018..2025 = 6 x 261 (common years) + 2 x 262 (leap 2020/2024)
    # = 2090; 2026-01-01..2026-09-11 = 183 (hand count) => 2270.
    assert fz.expected_weekday_count(*WINDOW) == 2270


def test_grid_census_warmup_carveout_and_bookable_chain_hand_computed():
    curve, etp = _jan2018_sources()
    grid = fz.build_common_grid(curve, etp, ("2018-01-01", "2018-01-31"))
    census = fz.grid_census(grid, warmup_sessions=3,
                            window=("2018-01-01", "2018-01-31"))
    # coverage: 20 grid sessions are weekdays; denominator 23
    assert census["grid_session_count"] == 20
    assert census["covered_weekdays"] == 20
    assert census["expected_weekdays_window"] == 23
    assert census["coverage_fraction"] == round(20 / 23, 6)
    # warmup carve-out: first 3 sessions reserved (history only)
    assert census["warmup_carveout_dates"] == ["2018-01-02", "2018-01-03",
                                               "2018-01-04"]
    assert census["bookable_count"] == 17            # 20 - 3
    assert census["first_decision_session"] == "2018-01-05"
    inst = census["bookable_instants"]
    assert len(inst) == 17
    # first bookable instant: hand-computed EST close (21:00Z)
    assert inst[0] == {
        "session_index": 3,
        "decision_session": "2018-01-05",
        "decision_utc": "2018-01-05T21:00:00+00:00",
        "readable_bar_date": "2018-01-04",
    }
    # the readable-bar chain follows the grid exactly
    for k, rec in enumerate(inst):
        assert rec["session_index"] == 3 + k
        assert rec["decision_session"] == grid[3 + k]
        assert rec["readable_bar_date"] == grid[2 + k]


def test_grid_census_dst_boundary_instants_hand_computed():
    # 2026 DST switch: Fri 2026-03-06 close is 21:00Z (EST), the next
    # session Mon 2026-03-09 close is 20:00Z (EDT) -- same 16:00 NY law.
    grid = ["2026-03-05", "2026-03-06", "2026-03-09"]
    census = fz.grid_census(grid, warmup_sessions=1,
                            window=("2026-03-05", "2026-03-09"))
    inst = census["bookable_instants"]
    assert [r["decision_utc"] for r in inst] == [
        "2026-03-06T21:00:00+00:00",     # EST
        "2026-03-09T20:00:00+00:00",     # EDT
    ]
    assert [r["readable_bar_date"] for r in inst] == [
        "2026-03-05", "2026-03-06"]
    assert census["coverage_fraction"] == 1.0    # 3/3 weekdays in window


def test_grid_census_warmup_ge_grid_zero_bookable_fail_closed():
    curve, etp = _jan2018_sources()
    grid = fz.build_common_grid(curve, etp, ("2018-01-01", "2018-01-31"))
    census = fz.grid_census(grid, warmup_sessions=len(grid),
                            window=("2018-01-01", "2018-01-31"))
    assert census["bookable_count"] == 0
    assert census["bookable_instants"] == []
    assert census["first_decision_session"] is None
    bigger = fz.grid_census(grid, warmup_sessions=len(grid) + 5,
                            window=("2018-01-01", "2018-01-31"))
    assert bigger["bookable_count"] == 0


def test_grid_census_rejects_unordered_grid():
    with pytest.raises(ValueError):
        fz.grid_census(["2018-01-03", "2018-01-02"], warmup_sessions=1)


# --------------------------------------------------------------------- #
# 2. auction PIT grid-eligibility fixtures (hand-computed)               #
# --------------------------------------------------------------------- #

_JAN_GRID = ["2018-01-02", "2018-01-03", "2018-01-04", "2018-01-05"]


def test_first_decision_index_after_bisect_semantics():
    assert fz.first_decision_index_after("2017-12-29", _JAN_GRID) == 0
    assert fz.first_decision_index_after("2018-01-01", _JAN_GRID) == 0
    assert fz.first_decision_index_after("2018-01-02", _JAN_GRID) == 1
    assert fz.first_decision_index_after("2018-01-04", _JAN_GRID) == 3
    assert fz.first_decision_index_after("2018-01-05", _JAN_GRID) is None
    assert fz.first_decision_index_after("2018-01-06", _JAN_GRID) is None


def test_auction_pit_mapping_hand_computed_est_same_day_refused():
    events = [
        {"cusip": "C1", "securityType": "Note", "announcementDate":
         "2018-01-03", "auctionDate": "2018-01-04"},
        {"cusip": "C2", "securityType": "Bill", "announcementDate":
         "2018-01-05", "auctionDate": "2018-01-09"},
        {"cusip": "C3", "securityType": "Bond", "announcementDate":
         "2018-01-01", "auctionDate": "2018-01-05"},
        {"cusip": "C4", "securityType": "Note", "announcementDate":
         "2018-01-04", "auctionDate": "2018-01-05"},
    ]
    out = fz.auction_grid_eligibility(events, _JAN_GRID,
                                      cross_check_stride=1,
                                      cross_check_edges=5)
    m = {r["cusip"]: r for r in out["mappings"]}
    # C1 announced Wed 2018-01-03: PIT = end of the announced NY day at
    # EST (UTC-5) => 2018-01-04T04:59:59.999999+00:00 (hand value);
    # the SAME-DAY 2018-01-03 close is refused; first eligible decision
    # is the NEXT session's close, Thu 2018-01-04 21:00Z (hand value).
    assert m["C1"]["pit_instant_utc"] == \
        "2018-01-04T04:59:59.999999+00:00"
    assert m["C1"]["same_day_close_eligible"] is False
    assert m["C1"]["eligible"] is True
    assert m["C1"]["decision_session"] == "2018-01-04"
    assert m["C1"]["decision_utc"] == "2018-01-04T21:00:00+00:00"
    # C3 announced BEFORE the grid: first grid session's close.
    assert m["C3"]["decision_session"] == "2018-01-02"
    assert m["C3"]["decision_utc"] == "2018-01-02T21:00:00+00:00"
    # C4 announced Thu 2018-01-04 -> Fri 2018-01-05 close.
    assert m["C4"]["decision_session"] == "2018-01-05"
    # C2 announced ON the last session: no later session => ineligible
    # (fail-closed, never mapped to the same-day close).
    assert m["C2"]["eligible"] is False
    assert m["C2"]["decision_session"] is None
    assert m["C2"]["refusal"] == "NO_LATER_GRID_SESSION"
    assert out["events_total"] == 4
    assert out["eligible_count"] == 3
    assert out["ineligible_count"] == 1
    # the deterministic clock-authority cross-check ran and agreed
    assert out["clock_authority_cross_check"]["all_agree"] is True
    assert (out["clock_authority_cross_check"]["sample_size"] == 4)
    # empty grid: nothing is eligible
    empty = fz.auction_grid_eligibility(events, [])
    assert empty["eligible_count"] == 0
    assert empty["ineligible_count"] == 4


def test_frozen_floor_constants_unchanged():
    """The floors live as constants and must equal the packet's frozen
    values (a moved floor is a rubric violation, never a measurement)."""
    assert fz.FEASIBILITY_WINDOW == ("2018-01-01", "2026-09-11")
    assert fz.WARMUP_SESSIONS == 252
    assert fz.MIN_BOOKABLE_INSTANTS == 1500
    assert fz.MIN_GRID_COVERAGE_FRACTION == 0.90
    assert fz.MIN_GRID_ELIGIBLE_AUCTION_EVENTS == 150
    assert fz.ROUND_TRIP_SPREAD_MULTIPLIER == 2.0
    assert fz.HOLDING_TRADING_DAYS == 5
    assert fz.HOLDING_CALENDAR_DAYS_CHARGED == 7


# --------------------------------------------------------------------- #
# 3. cost-ceiling fixture (hand-computed, NO PnL)                        #
# --------------------------------------------------------------------- #

def test_round_trip_ceiling_synthetic_hand_computed():
    contract = {"per_etp": {
        "FAKE": {"stress_tier_bps": 10.0,
                 "expense_drag": {"drag_per_day_fraction":
                                  0.0015 / 365.0}}}}
    out = fz.round_trip_cost_ceilings(contract)
    leg = out["per_leg"]["FAKE"]
    # hand: 2 x 10 bps spread + 7 x (0.0015/365) x 1e4 = 20 + 105/365
    assert leg["round_trip_spread_bps"] == 20.0
    assert leg["er_drag_round_trip_bps"] == pytest.approx(
        105.0 / 365.0, rel=1e-15, abs=1e-15)
    assert leg["worst_case_round_trip_ceiling_bps"] == pytest.approx(
        20.0 + 105.0 / 365.0, rel=1e-15, abs=1e-15)
    assert leg["worst_case_round_trip_ceiling_bps"] == pytest.approx(
        20.287671232876713, rel=1e-12)
    assert "no PnL" in out["no_pnl_note"]


def test_deterministic_payload_sha256_order_invariant():
    a = {"x": 1, "y": {"b": [1, 2], "a": "z"}}
    b = {"y": {"a": "z", "b": [1, 2]}, "x": 1}
    assert fz.deterministic_payload_sha256(a) \
        == fz.deterministic_payload_sha256(b)
    blob = json.dumps(a, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
    assert fz.deterministic_payload_sha256(a) \
        == hashlib.sha256(blob).hexdigest()


# --------------------------------------------------------------------- #
# 4. committed artifacts: hash pins + full consistency recomputation     #
# --------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def gate() -> dict:
    with open(GATE_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def grid_side() -> dict:
    with open(GRID_SIDECAR_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def auction_side() -> dict:
    with open(AUCTION_SIDECAR_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_gate_schema_and_frozen_floors_unchanged(gate):
    assert gate["schema"] == "rates_ng1_run/p2_gate@1"
    assert gate["gate"] == "RATES-NG1-P2"
    assert gate["cycle_id"] == "RATES-NG1"
    assert gate["task_id"] == "rates-ng1-p2-feasibility"
    frozen = {"A5_F1_bookable_decision_instants":
              fz.MIN_BOOKABLE_INSTANTS,
              "A5_F2_common_grid_coverage":
              fz.MIN_GRID_COVERAGE_FRACTION,
              "A4_F1_grid_eligible_auction_events":
              fz.MIN_GRID_ELIGIBLE_AUCTION_EVENTS}
    for name, value in frozen.items():
        f = gate["floors"][name]
        assert f["frozen"] == value
        assert f["operator"] == ">="
        assert f["verdict"] in ("PASS", "BLOCKED_LANE")
        assert f["verdict"] == ("PASS" if f["measured"] >= value
                                else "BLOCKED_LANE")
    assert gate["frozen_floor_provenance"]["warmup_carveout_sessions"] \
        == 252
    assert gate["frozen_floor_provenance"]["declared"].startswith(
        "dispatch packet")
    # fail-closed per lane + verdict consistency
    lanes = gate["lanes"]
    for lane in ("A5_curve_shape", "A4_auction_clock"):
        lane_floors = [f for f in gate["floors"].values()
                       if f["lane"] == lane]
        feasible = all(f["verdict"] == "PASS" for f in lane_floors)
        assert lanes[lane]["feasibility"] == ("FEASIBLE" if feasible
                                              else "BLOCKED")
        if feasible:
            assert lanes[lane]["blocked_path"] is None
        else:
            assert "dies cheap" in lanes[lane]["blocked_path"]
    both = all(lanes[l]["feasibility"] == "FEASIBLE"
               for l in lanes)
    if both:
        assert gate["verdict"] == "PASS"
        assert gate["blockers"] == []
    else:
        assert gate["verdict"].startswith("BLOCKED_")


def test_grid_sidecar_hashes_and_full_recomputation(gate, grid_side):
    assert _sha256_file(GRID_SIDECAR_PATH) == \
        gate["census_artifacts"]["grid_census"]["sha256"]
    census = grid_side["census"]
    assert grid_side["frozen_floors"] == {
        "min_bookable_instants": 1500,
        "min_grid_coverage_fraction": 0.90,
        "warmup_sessions": 252,
        "window": ["2018-01-01", "2026-09-11"],
    }
    dates = census["grid_dates"]
    # ascending, unique, inside the window
    assert dates == sorted(set(dates))
    assert WINDOW[0] <= dates[0] and dates[-1] <= WINDOW[1]
    assert census["grid_session_count"] == len(dates)
    assert census["warmup_sessions"] == 252
    # warmup carve-out = the FIRST 252 grid sessions
    assert census["warmup_carveout_dates"] == dates[:252]
    assert census["first_decision_session"] == dates[252]
    # bookable instants: every one re-derived through the P1 clock
    inst = census["bookable_instants"]
    assert census["bookable_count"] == len(dates) - 252 == len(inst)
    for k, rec in enumerate(inst):
        assert rec["session_index"] == 252 + k
        assert rec["decision_session"] == dates[252 + k]
        assert rec["readable_bar_date"] == dates[251 + k]
        assert rec["decision_utc"] == ck.ny_close_utc(
            dates[252 + k]).isoformat()
    # the frozen A5 floor evaluated against the census, both directions
    assert (census["bookable_count"] >= 1500) == \
        (gate["floors"]["A5_F1_bookable_decision_instants"]["verdict"]
         == "PASS")
    # coverage recomputation: weekday-grid convention, denominator 2270
    cw = sum(1 for d in dates
             if date.fromisoformat(d).weekday() < 5)
    assert census["covered_weekdays"] == cw
    assert census["expected_weekdays_window"] == 2270
    assert census["coverage_fraction"] == round(cw / 2270, 6)
    assert (census["coverage_fraction"] >= 0.90) == \
        (gate["floors"]["A5_F2_common_grid_coverage"]["verdict"]
         == "PASS")
    # gate headline numbers equal the sidecar
    ga = gate["census_artifacts"]["grid_census"]
    assert ga["bookable_count"] == census["bookable_count"]
    assert ga["grid_session_count"] == census["grid_session_count"]
    assert ga["coverage_fraction"] == census["coverage_fraction"]


def test_auction_sidecar_hashes_and_full_recomputation(gate, auction_side):
    assert _sha256_file(AUCTION_SIDECAR_PATH) == \
        gate["census_artifacts"]["auction_eligibility"]["sha256"]
    with open(P0_AUCTION_CENSUS_PATH, "r", encoding="utf-8") as fh:
        p0 = json.load(fh)
    headline = auction_side["eligibility_headline"]
    mappings = auction_side["mappings"]
    # the P0 raw census was 3555 -- re-verified equality, fail-closed
    assert auction_side["provenance"]["cross_check"]["counts_match"] \
        is True
    assert auction_side["census_headline"]["event_count"] == 3555
    assert p0["census"]["event_count"] == 3555
    assert headline["events_total"] == 3555 == len(mappings)
    assert headline["eligible_count"] == sum(
        1 for m in mappings if m["eligible"])
    assert (headline["eligible_count"]
            + headline["ineligible_count"]) == 3555
    # P1 PIT law on EVERY mapping: end-of-announced-NY-day bound, the
    # same-day close refused, decision strictly after the announcement
    for m in mappings:
        assert m["same_day_close_eligible"] is False
        assert m["pit_instant_utc"] == ck.pit_instant_for_day_event(
            m["announcementDate"]).isoformat()
        if m["eligible"]:
            assert m["decision_session"] > m["announcementDate"]
            assert m["decision_utc"] == ck.ny_close_utc(
                m["decision_session"]).isoformat()
        else:
            assert m["decision_session"] is None
            assert m["refusal"] == "NO_LATER_GRID_SESSION"
    # every eligible decision session is ON the common grid
    with open(GRID_SIDECAR_PATH, "r", encoding="utf-8") as fh:
        grid_dates = set(json.load(fh)["census"]["grid_dates"])
    assert all(m["decision_session"] in grid_dates
               for m in mappings if m["eligible"])
    # the frozen A4 floor evaluated, both directions
    assert (headline["eligible_count"] >= 150) == \
        (gate["floors"]["A4_F1_grid_eligible_auction_events"]["verdict"]
         == "PASS")
    # clock-authority cross-check sample agreed
    assert headline["clock_authority_cross_check"]["all_agree"] is True
    assert headline["clock_authority_cross_check"]["sample_size"] > 0
    ga = gate["census_artifacts"]["auction_eligibility"]
    assert ga["events_total"] == headline["events_total"]
    assert ga["eligible_count"] == headline["eligible_count"]


def test_cost_ceilings_recomputed_from_frozen_contract(gate):
    assert _sha256_file(CONTRACT_PATH) == \
        gate["cost_ceilings"]["contract"]["sha256"]
    with open(CONTRACT_PATH, "r", encoding="utf-8") as fh:
        contract = json.load(fh)
    # the cited contract carries the frozen tier-2.0 law
    assert contract["cost_ladder_tier"] == 2.0
    assert contract["cost_frequency"] == "once_per_fill"
    assert contract["stress_tier"]["quantile"] == 0.9
    assert gate["cost_ceilings"]["contract"]["cost_ladder_tier"] == 2.0
    # every leg's ceiling = 2 x CS p90 + 7 x drag x 1e4 (exact law)
    for ticker, leg in gate["cost_ceilings"]["per_leg"].items():
        rec = contract["per_etp"][ticker]
        p90 = rec["stress_tier_bps"]
        drag = rec["expense_drag"]["drag_per_day_fraction"]
        assert leg["cs_p90_stress_tier_bps"] == p90
        assert leg["round_trip_spread_bps"] == 2.0 * p90
        assert leg["er_drag_round_trip_bps"] == pytest.approx(
            7 * drag * 1e4, rel=1e-12, abs=1e-12)
        assert leg["worst_case_round_trip_ceiling_bps"] == pytest.approx(
            2.0 * p90 + 7 * drag * 1e4, rel=1e-12, abs=1e-12)
    # the declared convention is present and unchanged
    conv = gate["cost_ceilings"]["holding_convention"]
    assert conv["holding_trading_days"] == 5
    assert conv["calendar_days_charged"] == 7
    assert conv["drag_basis"].startswith("ACT/365F")


def test_substrate_verify_on_read_tlt_pin_chain():
    """Verify-on-read re-hash: the TLT RAW bytes still hash to the
    substrate-manifest pin AND to the committed P0 census digest."""
    plane = pa.RatesNG1Plane()
    res = plane.consume_via_plane("etp_eod/TLT.US.json")
    etp_census_path = os.path.join(RUN_DIR, "p0_etp_census.json")
    with open(etp_census_path, "r", encoding="utf-8") as fh:
        etp_census = json.load(fh)
    assert res["sha256_measured"] == res["sha256_pinned"] == \
        etp_census["tickers"]["TLT"]["sha256"]
