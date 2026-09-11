"""FOREX-NG3 D2 measurement tests (hand-computed fixtures).

Covers the three required fixture classes:

1. a hand-computed Spearman rho on a synthetic ng3 schedule PAIR (an
   A5-P1 anchor book vs its CTL-V7NODIFF control built by THIS lane's
   builders on synthetic restricted events);
2. fail-closed behaviour when a measurement cannot be proven (constant
   vector -> rho None -> novelty unmeasurable -> INELIGIBLE_FAIL_CLOSED;
   duplicate restricted events raise; DGS10 as-of reads fail closed
   outside every realtime window);
3. a Q-6 recent-window floor boundary case (exactly at the floor passes,
   one below fails) on synthetic books.

Run:
    .venv/bin/python -m pytest tests/test_forex_ng3_d2.py -q
"""

from __future__ import annotations

import sys
from datetime import date, timedelta

WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng3/d2"
if WORKTREE not in sys.path:
    sys.path.insert(0, WORKTREE)

import pytest  # noqa: E402

from research.assets.forex_ng1.d2 import rho as R       # noqa: E402
from research.assets.forex_ng1.plane_adapter import (  # noqa: E402
    VintageRow)
from research.assets.forex_ng2 import revision_series as ng2  # noqa: E402
from research.assets.forex_ng3.d2 import books as N3    # noqa: E402


# --------------------------------------------------------------------------- #
# synthetic fixtures
# --------------------------------------------------------------------------- #

def _rev(eco: str, month: str, v2_day: str, ratio: float) -> ng2.RevisionEvent:
    """A synthetic restricted revision event (pp ratio handed in)."""
    return ng2.RevisionEvent(
        economy=eco, obs_month=f"{month}-01",
        v1_realtime_start="2017-01-01", v1_realtime_end="2017-12-31",
        v1_value="100.0",
        v2_realtime_start=v2_day, v2_realtime_end="2099-12-31",
        v2_value=str(100.0 * (1.0 + ratio)),
        ratio=ratio, first_print_in_realtime_era=True)


def _grid(start: date, n: int) -> list[date]:
    """n consecutive weekdays starting at or after ``start``."""
    days, d = [], start
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


# --------------------------------------------------------------------------- #
# 1. hand-computed rho on a synthetic ng3 schedule PAIR
# --------------------------------------------------------------------------- #

def test_a5p1_anchor_vs_v7nodiff_hand_computed_rho():
    """Five differential months built by THIS lane's builders, hold = 1
    so each month contributes exactly its entry-day cell (no overlap
    netting); v2 days 2024-01-05/08/09/10/11 (Fri/Mon/Tue/Wed/Thu) give
    five distinct entry days 01-08..01-12.

    Month ratios (fractions), all gates pass (|D|, |R_CA| >= 0.02 pp):
      m0: CA -0.0010, US +0.0010 -> D = -0.20 pp (anchor LONG +1);
          R_CA = -0.10 pp         -> control LONG +1    AGREE
      m1: same as m0                                  AGREE (+1/+1)
      m2: CA +0.0020, US -0.0010 -> D = +0.30 pp (anchor SHORT -1);
          R_CA = +0.20 pp         -> control SHORT -1   AGREE
      m3: CA +0.0010, US +0.0030 -> D = -0.20 pp (anchor LONG +1);
          R_CA = +0.10 pp         -> control SHORT -1   DISAGREE
      m4: CA -0.0010, US +0.0030 -> D = -0.40 pp (anchor LONG +1);
          R_CA = -0.10 pp         -> control LONG +1    AGREE

    anchor  = [+1, +1, -1, +1, +1];  control = [+1, +1, -1, -1, +1]
    average-tie ranks: anchor [-1]->1, [+1 x4]->3.5  => [3.5,3.5,1,3.5,3.5]
                       control [-1 x2]->1.5, [+1 x3]->4 => [4,4,1.5,1.5,4]
    means 3.0; cov = 0.5+0.5+3.0-0.75+0.5 = 3.75;
    var_a = 5, var_c = 7.5 -> rho = 3.75/sqrt(37.5) = sqrt(3/8)
    (hand-computed; verified below through the union-active variant of
    the schedule comparison, where both books are active on the same
    five single-pair days so no zero cells dilute the ranks).
    """
    import math
    grid = _grid(date(2024, 1, 1), 20)
    grid_index = {d: i for i, d in enumerate(grid)}
    grid_iso = [d.isoformat() for d in grid]
    v2_days = ["2024-01-05", "2024-01-08", "2024-01-09", "2024-01-10",
               "2024-01-11"]
    specs = [  # (month, ca_ratio, us_ratio)
        ("2023-10", -0.0010, +0.0010),
        ("2023-11", -0.0010, +0.0010),
        ("2023-12", +0.0020, -0.0010),
        ("2024-01", +0.0010, +0.0030),
        ("2024-02", -0.0010, +0.0030),
    ]
    months = {m: ["CA", "US"] for m, _, _ in specs}
    lookup = {}
    for (m, ca_r, us_r), v2 in zip(specs, v2_days):
        lookup[("CA", m)] = _rev("CA", m, v2, ca_r)
        lookup[("US", m)] = _rev("US", m, v2, us_r)
    anchor = N3.build_ng3_a5p1_book("SYN-A5P1", "anchor", months, lookup,
                                    grid, grid_index, grid[-1], hold=1)
    ctl = N3.build_ng3_a5p1_book("SYN-A5P1-CTL", "v7nodiff", months,
                                 lookup, grid, grid_index, grid[-1],
                                 hold=1)
    assert anchor["meta"]["months_gate_passed"] == 5
    assert ctl["meta"]["months_gate_passed"] == 5
    assert anchor["meta"]["recent_months_obs_basis"] == 5
    a_days = sorted(k.split("|")[0] for k in anchor["cells"])
    assert a_days == ["2024-01-08", "2024-01-09", "2024-01-10",
                      "2024-01-11", "2024-01-12"]
    a_signs = [anchor["cells"][f"{d}|USDCAD"] for d in a_days]
    c_signs = [ctl["cells"][f"{d}|USDCAD"] for d in a_days]
    assert a_signs == [1, 1, -1, 1, 1]
    assert c_signs == [1, 1, -1, -1, 1]
    expected = math.sqrt(3.0 / 8.0)
    got = R.spearman([float(s) for s in a_signs],
                     [float(s) for s in c_signs])
    assert got is not None and abs(got - expected) < 1e-12
    cmp = R.compare_schedules(anchor["cells"], ctl["cells"], grid_iso,
                              ["USDCAD"])
    v = cmp["variants"]["cellwise_union_active"]
    assert v["n"] == 5 and abs(v["rho"] - expected) < 1e-12
    assert cmp["max_abs_rho"] is not None


def test_spearman_perfect_anticorrelation_with_ties():
    """a = [-1, 0, 0, +1, +1], b = [+1, 0, 0, -1, -1]: average-tie
    ranks a = [1, 2.5, 2.5, 4.5, 4.5], b = [4.5, 2.5, 2.5, 1, 1];
    means 3; cov = -3 + 0 + 0 - 3 - 3 = -9; var 9 each -> rho = -1
    (hand-computed; a constant vector still yields None)."""
    got = R.spearman([-1.0, 0.0, 0.0, 1.0, 1.0],
                     [1.0, 0.0, 0.0, -1.0, -1.0])
    assert got is not None and abs(got + 1.0) < 1e-12
    assert R.spearman([1.0] * 5, [1, 2, 3, 4, 5]) is None


def test_a4_book_cells_and_direction_hand_computed():
    """One material CA event: ratio -0.0002 (|R| = 0.02% >= 1e-4), v2
    day Friday 2024-01-05 -> D(e) = next grid day 2024-01-08 (Mon);
    R < 0 -> LONG USDCAD (+1) on cells i..i+9 (H = 10).  A second event
    with ratio -0.00005 (below 1e-4) must NOT fire the material book
    but MUST fire the sign book (no magnitude gate)."""
    grid = _grid(date(2024, 1, 1), 40)
    grid_index = {d: i for i, d in enumerate(grid)}
    ev_material = _rev("CA", "2023-11", "2024-01-05", -0.0002)
    ev_tiny = _rev("CA", "2023-12", "2024-02-05", -0.00005)
    sign_book = N3.build_ng3_a4_book("SYN-A4-SIGN", "sign",
                                     [ev_material, ev_tiny], grid,
                                     grid_index, grid[-1], hold=5)
    mat_book = N3.build_ng3_a4_book("SYN-A4-MAT", "material",
                                    [ev_material, ev_tiny], grid,
                                    grid_index, grid[-1],
                                    material_threshold=1e-4, hold=10)
    assert sign_book["meta"]["fired_events"] == 2
    assert mat_book["meta"]["fired_events"] == 1
    assert mat_book["meta"]["below_material_threshold"] == 1
    # entry day: first grid day strictly after Friday 2024-01-05
    entry = date(2024, 1, 8)
    assert entry in grid_index
    days = sorted({k.split("|")[0] for k in mat_book["cells"]})
    assert days[0] == entry.isoformat()
    assert len(days) == 10            # H = 10 exposure cells
    assert set(mat_book["cells"].values()) == {1}    # R < 0 -> long


def test_a5p2_transfer_direction_hand_computed():
    """One AU transfer event: R_CA -0.0020, R_AU +0.0040 ->
    D_L = 100*(-0.0020 - 0.0040) = -0.60 pp <= -0.02 -> SHORT AUDUSD
    (-1) on the leg's own pair, H = 5 cells."""
    grid = _grid(date(2024, 5, 1), 20)
    grid_index = {d: i for i, d in enumerate(grid)}
    lookup = {("CA", "2024-03"): _rev("CA", "2024-03", "2024-05-03",
                                      -0.0020),
              ("AU", "2024-03"): _rev("AU", "2024-03", "2024-05-10",
                                      +0.0040)}
    book = N3.build_ng3_a5p2_book("SYN-A5P2", "anchor",
                                  [("2024-03", "AU")], lookup, grid,
                                  grid_index, grid[-1])
    # clock: max(v2_CA 05-03, v2_AU 05-10) -> first grid day after 05-10
    entry = date(2024, 5, 13)
    assert entry in grid_index and entry.weekday() == 0
    days = sorted({k.split("|")[0] for k in book["cells"]})
    assert days[0] == entry.isoformat()
    assert all(k.endswith("|AUDUSD") for k in book["cells"])
    assert set(book["cells"].values()) == {-1}     # short the leg vs USD


# --------------------------------------------------------------------------- #
# 2. fail-closed unmeasured cases
# --------------------------------------------------------------------------- #

def test_month_event_lookup_duplicate_fails_closed():
    ev1 = _rev("CA", "2024-01", "2024-02-01", -0.001)
    ev2 = _rev("CA", "2024-01", "2024-03-01", -0.002)
    with pytest.raises(N3.Ng3D2BookError):
        N3.month_event_lookup({"CA": [ev1, ev2]})


def test_a5_month_missing_event_fails_closed_not_inferred():
    """A join month whose leg event is absent from the lookup is
    unmeasurable: months_failed_closed increments, no cells are built,
    and the month is never patched from a neighbouring vintage."""
    grid = _grid(date(2024, 1, 1), 20)
    grid_index = {d: i for i, d in enumerate(grid)}
    months = {"2024-01": ["CA", "AU"]}
    lookup = {("CA", "2024-01"): _rev("CA", "2024-01", "2024-02-01",
                                      -0.001)}          # AU leg absent
    book = N3.build_ng3_a5p1_book("SYN-FC", "anchor", months, lookup,
                                  grid, grid_index, grid[-1])
    assert book["meta"]["months_failed_closed"] == 1
    assert book["cells"] == {}
    assert book["meta"]["months_gate_passed"] == 0


def test_unmeasurable_novelty_is_ineligible_fail_closed():
    """A pooled rho that cannot be computed (constant vectors) must
    produce INELIGIBLE_FAIL_CLOSED -- never an inferred PASS."""
    verdict = N3.proposal_verdict(novelty_max_abs_rho=None,
                                  q6_row={"measured": 99, "floor": 1,
                                          "margin": 98,
                                          "verdict": "PASS"})
    assert verdict.startswith("INELIGIBLE_FAIL_CLOSED")
    assert "unmeasurable" in verdict


def test_a4p2_r0_empty_book_fail_closed():
    verdict = N3.proposal_verdict(
        novelty_max_abs_rho=0.05, r0_empty_book=True,
        q6_row={"measured": 17, "floor": 15, "margin": 2,
                "verdict": "PASS"})
    assert verdict.startswith("INELIGIBLE_FAIL_CLOSED")
    assert "EMPTY BOOK" in verdict


def test_dgs10_asof_read_fails_closed_outside_windows():
    """A grid day outside every realtime window reads None (never
    backfilled from a later vintage); a containing window reads the
    latest daily observation of the in-force vintage."""
    from research.assets.forex_ng1.plane_adapter import parse_fred_vintaged
    rows = parse_fred_vintaged([
        {"realtime_start": "2018-01-01", "realtime_end": "2018-05-31",
         "date": "2018-05-10", "value": "2.95"},
        {"realtime_start": "2018-01-01", "realtime_end": "2018-05-31",
         "date": "2018-05-11", "value": "2.97"},
        {"realtime_start": "2018-06-02", "realtime_end": "2019-01-01",
         "date": "2018-05-30", "value": "2.80"},
    ])
    levels = N3.dgs10_grid_levels(
        rows, [date(2018, 5, 15), date(2018, 6, 1), date(2018, 6, 5)])
    assert levels[date(2018, 5, 15)] == 2.97   # latest obs of in-force
    assert levels[date(2018, 6, 1)] is None    # gap day: no containing
    assert levels[date(2018, 6, 5)] == 2.80


def test_dgs10_missing_value_row_is_skipped():
    from research.assets.forex_ng1.plane_adapter import parse_fred_vintaged
    rows = parse_fred_vintaged([
        {"realtime_start": "2018-01-01", "realtime_end": "2019-01-01",
         "date": "2018-05-10", "value": "."},
        {"realtime_start": "2018-01-01", "realtime_end": "2019-01-01",
         "date": "2018-05-09", "value": "3.10"},
    ])
    levels = N3.dgs10_grid_levels(rows, [date(2018, 5, 15)])
    assert levels[date(2018, 5, 15)] == 3.10


# --------------------------------------------------------------------------- #
# 3. Q-6 floor boundary cases
# --------------------------------------------------------------------------- #

def test_q6_floor_boundary_at_and_below():
    """Exactly at the floor passes; one below fails (P-2 margin)."""
    at = N3.evaluate_q6_floor(6, 6)
    below = N3.evaluate_q6_floor(5, 6)
    assert at["verdict"] == "PASS" and at["margin"] == 0
    assert below["verdict"] == "FAIL" and below["margin"] == -1
    # the verdict function turns a floor FAIL into a VETO
    v = N3.proposal_verdict(
        novelty_max_abs_rho=0.10, q6_row=below)
    assert v.startswith("VETO(Q6_FLOOR_FAIL 5 < 6")
    v_at = N3.proposal_verdict(novelty_max_abs_rho=0.10, q6_row=at)
    assert v_at == "ELIGIBLE"


def test_q6_recent_months_on_synthetic_a5p1_book():
    """Six differential months with obs months inside 2023-05..2025-04
    measure exactly 6 on the obs-month basis (boundary PASS at floor 6);
    moving two of them outside the window measures 4 (FAIL)."""
    grid = _grid(date(2023, 1, 2), 600)
    grid_index = {d: i for i, d in enumerate(grid)}
    months_in = ["2023-06", "2023-08", "2023-10", "2024-02", "2024-09",
                 "2025-03"]
    months_out = ["2022-06", "2022-08", "2023-10", "2024-02", "2024-09",
                  "2025-03"]

    def build(months):
        mdict = {m: ["CA", "US"] for m in months}
        lookup = {}
        for m in sorted(months):
            # one shared v2 day well inside the grid so every month's
            # entry exists (the obs-month basis is what the floor reads)
            v2 = "2024-06-03"
            lookup[("CA", m)] = _rev("CA", m, v2, -0.0030)
            lookup[("US", m)] = _rev("US", m, v2, +0.0030)
        return N3.build_ng3_a5p1_book("SYN-Q6", "anchor", mdict, lookup,
                                      grid, grid_index, grid[-1])

    b_in = build(months_in)
    b_out = build(months_out)
    assert b_in["meta"]["recent_months_obs_basis"] == 6
    assert b_out["meta"]["recent_months_obs_basis"] == 4
    assert N3.evaluate_q6_floor(
        b_in["meta"]["recent_months_obs_basis"], 6)["verdict"] == "PASS"
    assert N3.evaluate_q6_floor(
        b_out["meta"]["recent_months_obs_basis"], 6)["verdict"] == "FAIL"


def test_novelty_bar_and_identifiability_kill_boundaries():
    """rho exactly at the 0.20 bar passes (<= bar); above vetoes with the
    P-2 margin; identifiability kill fires at exactly 0.98."""
    q6 = {"measured": 17, "floor": 15, "margin": 2, "verdict": "PASS"}
    assert N3.proposal_verdict(novelty_max_abs_rho=0.20,
                               q6_row=q6) == "ELIGIBLE"
    v = N3.proposal_verdict(novelty_max_abs_rho=0.2589, q6_row=q6)
    assert v.startswith("VETO(ANCESTRY_VETO rho=0.2589 margin=-0.0589)")
    kill = N3.proposal_verdict(novelty_max_abs_rho=0.10, q6_row=q6,
                               identifiability_kill=0.98)
    assert "IDENTIFIABILITY_KILL" in kill and "0.98" in kill
    no_kill = N3.proposal_verdict(novelty_max_abs_rho=0.10, q6_row=q6,
                                  identifiability_kill=0.9799)
    assert no_kill == "ELIGIBLE"


def test_rule_order_r0_before_novelty():
    """The A4-P2 R0 empty-book check precedes every other rule (its own
    frozen rule order): an empty book is INELIGIBLE even if the Q-6
    floor would also fail."""
    verdict = N3.proposal_verdict(
        novelty_max_abs_rho=0.05, r0_empty_book=True,
        q6_row={"measured": 0, "floor": 15, "margin": -15,
                "verdict": "FAIL"})
    assert verdict.startswith("INELIGIBLE_FAIL_CLOSED")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
