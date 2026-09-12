"""VOL-NG1 P2 tests (task vol-ng1-p2-feasibility, Q-6 no-PnL).

Hand-computed census assertions on synthetic fixtures + committed
artifact hash checks, per the dispatch packet:

1. Common-grid construction (strict 9-leg intersection, fail-closed
   on missing legs) on synthetic series;
2. Warmup carve-out + V7 close+1 bookable counts, HAND-COMPUTED
   (254 sessions -> 1 bookable; holiday gaps reduce the grid and the
   coverage denominator exactly as computed by hand);
3. A5 declared-proxy computability on synthetic grids (fully populated
   proxy vs late-start proxy), floor logic, GRANTED-only refusal;
4. Cost ceilings HAND-COMPUTED from the frozen committed contract
   constants (CS p90 x 2 fills + expense bps/day x H + adverse path
   tail x H), and refusal when the declared holding convention does
   not bind to the contract's own measured day_gap;
5. Committed-artifact checks: p2_gate.json schema/verdicts, sha256
   citations (p0_gate, p1_gate, p1_cost_contract), consumed digests ==
   the frozen plane constants, gate census == independent re-measure
   through the plane + event-adjusted layer, frozen floors recorded
   EXACTLY (252 / 1500 / 0.90 / 1000 -- no threshold drift), zero
   network reads, and the A5 structural limitation written down.

No network, no proposals, no signal design, no scoring, no PnL/outcome
numbers anywhere.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.assets.vol_ng1 import census as vc           # noqa: E402
from research.assets.vol_ng1 import corp_actions as ca     # noqa: E402
from research.assets.vol_ng1 import feasibility as fb      # noqa: E402
from research.assets.vol_ng1 import plane_adapter as pa    # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
P0_GATE_PATH = REPO_ROOT / "research/control/vol_ng1_run/p0_gate.json"
P1_GATE_PATH = REPO_ROOT / "research/control/vol_ng1_run/p1_gate.json"
CONTRACT_PATH = (REPO_ROOT /
                 "research/control/vol_ng1_run/p1_cost_contract.json")
P2_GATE_PATH = REPO_ROOT / "research/control/vol_ng1_run/p2_gate.json"

GRANTED_ALL = {s: "GRANTED" for s in sorted(pa.FROZEN_TARGET_SET)}


def _weekdays(n: int, start: str = "2020-01-06") -> list[str]:
    """n consecutive Mon-Fri ISO dates (hand-computable grids)."""
    d0 = date.fromisoformat(start)
    out: list[str] = []
    d = d0
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _sets(grid: list[str]) -> tuple[dict[str, dict[str, float]],
                                    dict[str, dict[str, float]]]:
    idx = {leg: {d: 1.0 for d in grid} for leg in fb.GRID_INDEX_LEGS}
    etp = {leg: {d: 1.0 for d in grid} for leg in fb.GRID_ETP_LEGS}
    return idx, etp


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ===================================================================== #
# 1. common grid construction
# ===================================================================== #
def test_common_grid_is_strict_nine_leg_intersection():
    dates = _weekdays(10)
    idx, etp = _sets(dates)
    assert fb.common_grid(idx, etp) == dates
    # one leg missing one date -> that date leaves the grid
    del etp["SVXY"][dates[3]]
    assert fb.common_grid(idx, etp) == [d for i, d in
                                        enumerate(dates) if i != 3]


def test_common_grid_refuses_missing_legs_fail_closed():
    dates = _weekdays(5)
    idx, etp = _sets(dates)
    del idx["VIX3M"]
    with pytest.raises(fb.FeasibilityError):
        fb.common_grid(idx, etp)
    idx, etp = _sets(dates)
    del etp["VXZ"]
    with pytest.raises(fb.FeasibilityError):
        fb.common_grid(idx, etp)


# ===================================================================== #
# 2. warmup carve-out + bookable counts (HAND-COMPUTED)
# ===================================================================== #
def test_bookable_warmup_and_v7_tail_hand_computed():
    dates = _weekdays(260)
    idx, etp = _sets(dates)
    grid = fb.common_grid(idx, etp)
    window = fb.window_sessions(grid)
    assert len(window) == 260
    bookable, tail = fb.bookable_sessions(grid, window)
    # warmup = first 252 sessions -> candidates = idx 252..259 (8);
    # the last session (idx 259) has no next bar -> V7-refused.
    assert len(bookable) == 7
    assert bookable == dates[252:259]
    assert tail == [dates[259]]
    # coverage: bookable 7 / Mon-Fri dates in [dates[252], dates[259]]
    # = 8 consecutive weekdays -> 0.875 exactly.
    cov = fb.coverage_fraction(bookable, grid[-1])
    assert cov["denominator_primary"] == 8
    assert cov["primary"] == pytest.approx(7.0 / 8.0)
    a4 = fb.a4_lane(grid)
    assert a4["bookable_instants"] == 7
    assert a4["coverage_primary"] == pytest.approx(0.875)
    # disclosed secondary (never gated): denominator spans the full
    # window INCLUDING the warmup -> 260 consecutive weekdays.
    assert a4["coverage_secondary_denominator_full_window"] == 260
    assert a4["coverage_full_window_secondary_disclosed"] == \
        pytest.approx(7.0 / 260.0, abs=1e-6)
    assert a4["verdict"] == "FAIL"  # 7 << 1500 on the synthetic fixture
    assert a4["verdict_components"] == {"instants_ok": False,
                                        "coverage_ok": False}


def test_warmup_boundary_hand_computed():
    dates = _weekdays(254)
    idx, etp = _sets(dates)
    grid = fb.common_grid(idx, etp)
    window = fb.window_sessions(grid)
    bookable, tail = fb.bookable_sessions(grid, window)
    # candidates = idx 252,253 -> only idx 252 has a next session.
    assert bookable == [dates[252]]
    assert tail == [dates[253]]
    # exactly 252 sessions: the whole window is warmup -> zero bookable
    dates252 = _weekdays(252)
    grid252 = fb.common_grid(*_sets(dates252))
    b252, t252 = fb.bookable_sessions(grid252,
                                      fb.window_sessions(grid252))
    assert b252 == [] and t252 == []
    # 253 sessions: one candidate, refused by the V7 tail law.
    dates253 = _weekdays(253)
    grid253 = fb.common_grid(*_sets(dates253))
    b253, t253 = fb.bookable_sessions(grid253,
                                      fb.window_sessions(grid253))
    assert b253 == [] and t253 == [dates253[252]]


def test_holiday_gap_coverage_hand_computed():
    dates = _weekdays(260)
    idx, etp = _sets(dates)
    del etp["SVXY"][dates[253]]
    del etp["SVXY"][dates[254]]
    grid = fb.common_grid(idx, etp)
    assert len(grid) == 258
    a4 = fb.a4_lane(grid)
    # warmup = first 252 window sessions (d0..d251); candidates =
    # d252, d255, d256, d257, d258, d259; bookable = all but d259 = 5.
    assert a4["bookable_instants"] == 5
    # coverage denominator: Mon-Fri dates in [d252, d259] = 8 (the two
    # gap weekdays d253, d254 count in the denominator, not the grid).
    assert a4["coverage_primary_denominator"] == 8
    assert a4["coverage_primary"] == pytest.approx(5.0 / 8.0)


# ===================================================================== #
# 3. A5 declared-proxy computability (synthetic)
# ===================================================================== #
def test_a5_computability_fully_populated_proxy_hand_computed():
    dates = _weekdays(275)
    idx, etp = _sets(dates)
    grid = fb.common_grid(idx, etp)
    a5 = fb.a5_lane(grid, {d: 1.0 for d in grid}, GRANTED_ALL)
    # bookable = idx 252..273 (22 instants); the 21-session lookback is
    # satisfied at every bookable instant (warmup serves it by design).
    assert a5["bookable_instants_state_computable"] == 22
    assert a5["first_bookable_computable_instant"] == dates[252]
    assert a5["computable_at_all"] is True
    # floor is 1000: the synthetic fixture CANNOT meet it -> BLOCKED.
    assert a5["verdict"] == "BLOCKED"
    assert "A4-only" in a5["blocked_note"]
    assert "NOT S&P" in a5["structural_limitation"]
    assert "implied-complex" in a5["structural_limitation"]


def test_a5_late_start_proxy_blocks():
    dates = _weekdays(275)
    idx, etp = _sets(dates)
    grid = fb.common_grid(idx, etp)
    proxy = {d: 1.0 for d in dates[260:]}  # exists only from idx 260
    comp = fb.realized_proxy_computable(proxy, grid)
    assert comp["computable"] is False
    a5 = fb.a5_lane(grid, proxy, GRANTED_ALL)
    assert a5["bookable_instants_state_computable"] == 0
    assert a5["verdict"] == "BLOCKED"


def test_a5_requires_granted_series_only():
    dates = _weekdays(275)
    idx, etp = _sets(dates)
    grid = fb.common_grid(idx, etp)
    verdicts = dict(GRANTED_ALL)
    verdicts["S7:cboe-vol-index-histories"] = "BLOCKED: x"
    a5 = fb.a5_lane(grid, {d: 1.0 for d in grid}, verdicts)
    assert a5["all_inputs_granted"] is False
    assert a5["verdict"] == "BLOCKED"
    with pytest.raises(fb.FeasibilityError):
        fb.a5_lane(grid, {d: 1.0 for d in grid}, {"other": "GRANTED"})


def test_frozen_floor_constants_are_exact():
    # threshold drift guard: the floors are frozen in the task objective
    assert fb.WARMUP_SESSIONS == 252
    assert fb.A4_FLOOR_INSTANTS == 1500
    assert fb.COVERAGE_FLOOR == 0.90
    assert fb.A5_FLOOR_INSTANTS == 1000
    assert fb.PROXY_LOOKBACK_SESSIONS == 21
    assert fb.GRID_INDEX_LEGS == ("VIX9D", "VIX", "VIX3M")
    assert fb.GRID_ETP_LEGS == ("VXX", "UVXY", "SVXY", "VIXY",
                                "VIXM", "VXZ")
    assert fb.PROXY_LEG == "VXX"


# ===================================================================== #
# 4. cost ceilings HAND-COMPUTED from the frozen contract
# ===================================================================== #
def test_cost_ceiling_hand_computed_from_frozen_constants():
    with open(CONTRACT_PATH, "r", encoding="utf-8") as fh:
        contract = json.load(fh)
    out = fb.cost_ceilings(contract)
    legs = out["legs"]
    assert sorted(legs) == ["SVXY", "UVXY", "VIXM", "VIXY", "VXX", "VXZ"]
    # VXX (SHORT, H=21): 2*155.0714 + 0.243836*21 + 89.492726*21
    vxx = legs["VXX"]
    assert vxx["holding_convention_sessions"] == 21.0
    assert vxx["execution_spread_bps_round_trip"] == pytest.approx(
        310.1428, abs=1e-9)
    assert vxx["expense_bps_over_holding"] == pytest.approx(
        5.120556, abs=1e-9)
    assert vxx["path_adverse_tail_daily_bps"] == pytest.approx(
        89.492726, abs=1e-9)
    assert vxx["round_trip_cost_ceiling_bps"] == pytest.approx(
        310.1428 + 5.120556 + 1879.347246, abs=1e-6)
    # VXZ (MID, H=90): 2*66.5029 + 0.243836*90 + 15.139477*90
    vxz = legs["VXZ"]
    assert vxz["holding_convention_sessions"] == 90.0
    assert vxz["round_trip_cost_ceiling_bps"] == pytest.approx(
        133.0058 + 21.94524 + 1362.55293, abs=1e-6)
    # SVXY is the cheapest execution spread at tier 2.0: 2*35.4976
    assert legs["SVXY"]["execution_spread_bps_round_trip"] == \
        pytest.approx(70.9952, abs=1e-9)
    # every leg cites its expense source digest from the contract
    for leg, blk in legs.items():
        assert blk["expense_source_sha256"] == \
            contract["legs"][leg]["expense"]["source_sha256"]


def test_cost_ceiling_refuses_daygap_convention_mismatch():
    with open(CONTRACT_PATH, "r", encoding="utf-8") as fh:
        contract = json.load(fh)
    bad = copy.deepcopy(contract)
    bad["legs"]["VXX"]["path_cost"]["day_gap"] = 5.0
    with pytest.raises(fb.FeasibilityError):
        fb.cost_ceilings(bad)


# ===================================================================== #
# 5. committed artifacts: p2_gate.json
# ===================================================================== #
@pytest.fixture(scope="module")
def p2_gate() -> dict:
    if not P2_GATE_PATH.is_file():
        pytest.fail("p2_gate.json missing: run "
                    "research/control/vol_ng1_run/p2_run.py first "
                    "(committed-artifact checks are mandatory)")
    with open(P2_GATE_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_p2_gate_identity_and_verdicts(p2_gate):
    assert p2_gate["schema"] == "vol_ng1_run/p2_gate@1"
    assert p2_gate["task_id"] == "vol-ng1-p2-feasibility"
    assert p2_gate["cycle_id"] == "VOL-NG1"
    assert p2_gate["lane"] == "p2"
    tests_sec = p2_gate["sections"]["tests"]
    assert tests_sec["command"].endswith("tests/test_vol_ng1_p2.py -q")
    # internal consistency of the recorded pytest evidence (the gate is
    # written AFTER the pytest run, so the recorded exit code is from
    # the run that read the previous gate; the runner's own gate law
    # forces overall FAIL unless its embedded pytest passed).
    assert (tests_sec["exit_code"] == 0) == \
        (tests_sec["verdict"] == "PASS")
    a4 = p2_gate["sections"]["a4_term_structure_slope"]
    a5 = p2_gate["sections"]["a5_risk_premium"]
    assert a4["verdict"] in ("PASS", "FAIL")
    assert a5["verdict"] in ("FEASIBLE", "BLOCKED")
    # gate law: a5 FEASIBLE or BLOCKED are both valid outcomes; the
    # overall verdict must be PASS iff a4/costs/tests all PASS.
    hard_sections_pass = (
        a4["verdict"] == "PASS"
        and p2_gate["sections"]["cost_ceilings"]["verdict"] == "PASS"
        and p2_gate["sections"]["event_adjusted_layer"]["verdict"] ==
        "PASS"
        and p2_gate["sections"]["tests"]["verdict"] == "PASS")
    assert p2_gate["verdict"] == ("PASS" if hard_sections_pass
                                  else "FAIL")


def test_p2_gate_floors_recorded_exactly(p2_gate):
    a4 = p2_gate["sections"]["a4_term_structure_slope"]
    a5 = p2_gate["sections"]["a5_risk_premium"]
    assert a4["frozen_floors"] == {"min_bookable_instants": 1500,
                                   "min_coverage": 0.90}
    assert a4["warmup_carveout_sessions"] == 252
    assert a5["frozen_floor"] == \
        {"min_bookable_computable_instants": 1000}
    assert a5["proxy_lookback_sessions"] == 21
    assert p2_gate["consumed_via_plane"]["network_reads"] == 0
    assert p2_gate["consumed_via_plane"]["store_write_ops"] == 0


def test_p2_gate_hash_citations_match_committed_bytes(p2_gate):
    cited = p2_gate["artifact_hashes_cited"]
    assert cited["p0_gate_json_sha256"] == _sha256(P0_GATE_PATH)
    assert cited["p1_gate_json_sha256"] == _sha256(P1_GATE_PATH)
    assert cited["p1_cost_contract_json_sha256"] == \
        _sha256(CONTRACT_PATH)
    assert p2_gate["sections"]["cost_ceilings"][
        "contract_sha256_cited"] == _sha256(CONTRACT_PATH)


def test_p2_gate_consumed_digests_equal_frozen_plane_constants(p2_gate):
    frozen = pa.all_frozen_entries()
    for leg, entry in {"VXX": "VXX.US_eod.json",
                       "UVXY": "UVXY.US_eod.json",
                       "SVXY": "SVXY.US_eod.json",
                       "VIXY": "VIXY.US_eod.json",
                       "VIXM": "VIXM.US_eod.json",
                       "VXZ": "VXZ.US_eod.json"}.items():
        assert p2_gate["consumed_via_plane"]["etp_digests"][leg] == \
            frozen[entry]["sha256"]
    for name, entry in {"VIX": "VIX_History.csv",
                        "VIX9D": "VIX9D_History.csv",
                        "VIX3M": "VIX3M_History.csv"}.items():
        assert p2_gate["consumed_via_plane"]["index_digests"][name] == \
            frozen[entry]["sha256"]


def test_p2_gate_census_matches_independent_remeasure(p2_gate):
    """Re-measure the census through the plane + event-adjusted layer,
    independent of the gate's stored numbers, and require equality."""
    plane = pa.VolNg1Plane()
    index_closes = {}
    for name, entry in {"VIX": "VIX_History.csv",
                        "VIX9D": "VIX9D_History.csv",
                        "VIX3M": "VIX3M_History.csv"}.items():
        index_closes[name] = vc.parse_cboe_csv(
            plane.consume(entry)["data"])
    inventory = ca.load_inventory()
    table = ca.build_event_table(inventory)
    adj = {}
    for leg, entry in {"VXX": "VXX.US_eod.json",
                       "UVXY": "UVXY.US_eod.json",
                       "SVXY": "SVXY.US_eod.json",
                       "VIXY": "VIXY.US_eod.json",
                       "VIXM": "VIXM.US_eod.json",
                       "VXZ": "VXZ.US_eod.json"}.items():
        bars = json.loads(plane.consume(entry)["data"])
        adj[leg] = ca.event_adjusted_closes(bars, table[leg])
    grid = fb.common_grid(index_closes, adj)
    a4_re = fb.a4_lane(grid)
    a5_re = fb.a5_lane(grid, adj[fb.PROXY_LEG], GRANTED_ALL)
    ceil_re = fb.cost_ceilings(json.loads(CONTRACT_PATH.read_text()))

    a4 = p2_gate["sections"]["a4_term_structure_slope"]
    a5 = p2_gate["sections"]["a5_risk_premium"]
    assert a4["grid_sessions_total"] == a4_re["grid_sessions_total"]
    assert a4["window_sessions_post_2015"] == \
        a4_re["window_sessions_post_2015"]
    assert a4["bookable_instants"] == a4_re["bookable_instants"]
    assert a4["first_bookable_instant"] == \
        a4_re["first_bookable_instant"]
    assert a4["coverage_primary"] == a4_re["coverage_primary"]
    assert a4["coverage_primary_denominator"] == \
        a4_re["coverage_primary_denominator"]
    assert a4["verdict"] == a4_re["verdict"]
    assert a5["bookable_instants_state_computable"] == \
        a5_re["bookable_instants_state_computable"]
    assert a5["first_bookable_computable_instant"] == \
        a5_re["first_bookable_computable_instant"]
    assert a5["verdict"] == a5_re["verdict"]
    gate_ceils = p2_gate["sections"]["cost_ceilings"]["legs"]
    for leg, blk in ceil_re["legs"].items():
        assert gate_ceils[leg]["round_trip_cost_ceiling_bps"] == \
            blk["round_trip_cost_ceiling_bps"]


def test_p2_gate_event_layer_law_recorded(p2_gate):
    ev = p2_gate["sections"]["event_adjusted_layer"]
    assert ev["verdict"] == "PASS"
    assert ev["inventory_total_steps"] == 27
    assert ev["max_abs_mechanical_residual"] < 1e-4
    assert "event_adjusted_closes" in ev["consumption_law"]
    a5 = p2_gate["sections"]["a5_risk_premium"]
    assert "NOT S&P" in a5["structural_limitation"]
    assert a5["implied_series"].startswith("S7:cboe-vol-index-histories")
    assert "event-adjusted VXX" in a5["realized_proxy_declared"]
