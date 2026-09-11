"""FOREX-NG4 D2 measurement tests (hand-computed fixtures).

Covers the three required fixture classes:

1. a hand-computed Spearman rho on a synthetic ng4 schedule PAIR (the
   A5-P1 opposition anchor vs the A5-P2 magnitude-diff anchor built by
   THIS lane's builders on synthetic restricted differential months);
2. fail-closed behaviour when a measurement cannot be proven (a
   predictor month whose vintage window closed before the v2-day entry
   reads None -> the A4 event fails closed with NO cell; a pair-disjoint
   book is an honest NO_SHARED_PAIRS row, never a silent drop; constant
   vectors -> rho None -> novelty unmeasurable ->
   INELIGIBLE_FAIL_CLOSED; the empty-book law);
3. an EZ-stream PIT case: the v2-day entry clock plus the hand-computed
   seasonal-naive surprise s1 = 100*(I_print*97.5/(99*98) - 1) on a
   synthetic EZ vintaged panel, and the CTL-PPPANCESTRY cumulative-
   level control verified by hand.

Run:
    .venv/bin/python -m pytest tests/test_forex_ng4_d2.py -q
"""

from __future__ import annotations

import math
import sys
from datetime import date, timedelta

WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng4/d2"
if WORKTREE not in sys.path:
    sys.path.insert(0, WORKTREE)

import pytest  # noqa: E402

from research.assets.forex_ng1.d2 import rho as R       # noqa: E402
from research.assets.forex_ng1.d2.series import (        # noqa: E402
    VintagedSeries,
)
from research.assets.forex_ng2 import revision_series as ng2  # noqa: E402
from research.assets.forex_ng4.d2 import books as N4     # noqa: E402


# --------------------------------------------------------------------------- #
# synthetic fixtures
# --------------------------------------------------------------------------- #

def _rev(eco: str, month: str, v2_day: str, ratio: float,
         v1_value: str = "100.0") -> ng2.RevisionEvent:
    """A synthetic restricted revision event."""
    return ng2.RevisionEvent(
        economy=eco, obs_month=f"{month}-01",
        v1_realtime_start="2017-01-01", v1_realtime_end="2017-12-31",
        v1_value=v1_value,
        v2_realtime_start=v2_day, v2_realtime_end="2099-12-31",
        v2_value=str(float(v1_value) * (1.0 + ratio)),
        ratio=ratio, first_print_in_realtime_era=True)


def _grid(start: date, n: int) -> list[date]:
    """n consecutive weekdays starting at or after ``start``."""
    days, d = [], start
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


def _ez_panel(prev_window_end: str = "9999-12-31") -> VintagedSeries:
    """Synthetic EZ vintaged panel (monthly):

    obs 2015-05 -> 97.5, obs 2015-06 -> 98.0, obs 2016-05 -> 99.0
    (single ever-open versions, the archive's own first vintage
    2015-02-24); obs 2016-06 -> v1 100.0 [2016-07-01, 2016-08-31],
    v2 101.0 [2016-09-01, open).
    """
    rows = [
        {"obs": "2015-05-01", "rs": date(2015, 2, 24),
         "re": date.fromisoformat(prev_window_end), "value": 97.5},
        {"obs": "2015-06-01", "rs": date(2015, 2, 24),
         "re": date.fromisoformat(prev_window_end), "value": 98.0},
        {"obs": "2016-05-01", "rs": date(2015, 2, 24),
         "re": date.fromisoformat(prev_window_end), "value": 99.0},
        {"obs": "2016-06-01", "rs": date(2016, 7, 1),
         "re": date(2016, 8, 31), "value": 100.0},
        {"obs": "2016-06-01", "rs": date(2016, 9, 1),
         "re": date(9999, 12, 31), "value": 101.0},
    ]
    return VintagedSeries(series_id="SYN-EZ", rows=rows)


# --------------------------------------------------------------------------- #
# 1. hand-computed rho on a synthetic ng4 schedule pair
# --------------------------------------------------------------------------- #

def test_a5_p1_vs_a5_p2_hand_computed_rho():
    """Five differential months (hold = 1 -> one cell per fired month),
    shared v2 days 2024-01-05/08/09/10/11 -> entries 01-08..01-12.

      m0: R_EZ +0.10 pp, R_US -0.05 pp -> OPPOSED, D = +0.15 pp
          P1 anchor +1 (long EURUSD);  P2 anchor +1     AGREE
      m1: R_EZ +0.10 pp, R_US +0.05 pp -> agreed, D = +0.05 pp
          P1 flat;                     P2 anchor +1
      m2: R_EZ -0.20 pp, R_US +0.10 pp -> OPPOSED, D = -0.30 pp
          P1 anchor -1;                P2 anchor -1     AGREE
      m3: R_EZ +0.30 pp, R_US +0.10 pp -> agreed, D = +0.20 pp
          P1 flat;                     P2 anchor +1
      m4: R_EZ -0.10 pp, R_US -0.05 pp -> agreed, D = -0.05 pp
          P1 flat;                     P2 anchor -1

    union-active cells (5 days, EURUSD):
      P1 x = [+1, 0, -1, 0, 0]   ranks: -1->1, 0->3(x3), +1->5
                                  = [5, 3, 1, 3, 3], mean 3
      P2 y = [+1, +1, -1, +1, -1] ranks: -1->1.5(x2), +1->4(x3)
                                  = [4, 4, 1.5, 4, 1.5], mean 3
    cov = 2*1 + 0 + (-2)(-1.5) + 0 + 0 = 5;  var_x = 8;  var_y = 7.5
    rho = 5 / sqrt(8 * 7.5) = 5 / sqrt(60) = sqrt(5/12)
        = 0.645497224367902...  (hand-computed)
    """
    grid = _grid(date(2024, 1, 1), 20)
    grid_index = {d: i for i, d in enumerate(grid)}
    grid_iso = [d.isoformat() for d in grid]
    v2_days = ["2024-01-05", "2024-01-08", "2024-01-09", "2024-01-10",
               "2024-01-11"]
    specs = [  # (month, ez_ratio_pp/100, us_ratio_pp/100)
        ("2023-10", +0.0010, -0.0005),
        ("2023-11", +0.0010, +0.0005),
        ("2023-12", -0.0020, +0.0010),
        ("2024-01", +0.0030, +0.0010),
        ("2024-02", -0.0010, -0.0005),
    ]
    months = [m for m, _, _ in specs]
    lookup = {}
    for (m, ez_r, us_r), v2 in zip(specs, v2_days):
        lookup[("EZ", m)] = _rev("EZ", m, v2, ez_r)
        lookup[("US", m)] = _rev("US", m, v2, us_r)
    p1 = N4.build_ng4_a5_book("SYN-A5P1", "anchor_p1", months, lookup,
                              grid, grid_index, grid[-1], hold=1)
    p2 = N4.build_ng4_a5_book("SYN-A5P2", "anchor_p2", months, lookup,
                              grid, grid_index, grid[-1], hold=1)
    assert p1["meta"]["months_opposed"] == 2
    assert p1["meta"]["months_agreed"] == 3
    assert p1["meta"]["months_gate_passed"] == 2
    assert p2["meta"]["months_gate_passed"] == 5
    days = ["2024-01-08", "2024-01-09", "2024-01-10", "2024-01-11",
            "2024-01-12"]
    x = [p1["cells"].get(f"{d}|EURUSD", 0) for d in days]
    y = [p2["cells"].get(f"{d}|EURUSD", 0) for d in days]
    assert x == [1, 0, -1, 0, 0]
    assert y == [1, 1, -1, 1, -1]
    expected = math.sqrt(5.0 / 12.0)
    got = R.spearman([float(v) for v in x], [float(v) for v in y])
    assert got is not None and abs(got - expected) < 1e-12
    cmp = R.compare_schedules(p1["cells"], p2["cells"], grid_iso,
                              list(N4.PLANE_PAIRS))
    v = cmp["variants"]["cellwise_union_active"]
    assert v["n"] == 5 and abs(v["rho"] - expected) < 1e-12
    assert cmp["max_abs_rho"] is not None


def test_v7nodiff_p1_subsumes_the_opposition_anchor_subset():
    """The P1 anchor's direction set is a SUBSET of the sign(R_EZ)
    all-months book (the ng3-A5-P1 structural overlap): with ALL months
    opposed the two books coincide cell-for-cell on distinct entry days
    -> rho exactly 1.0 (the identifiability-kill geometry)."""
    grid = _grid(date(2024, 1, 1), 20)
    grid_index = {d: i for i, d in enumerate(grid)}
    grid_iso = [d.isoformat() for d in grid]
    specs = [("2023-10", +0.0010, -0.0005, "2024-01-05"),
             ("2023-11", -0.0010, +0.0005, "2024-01-08"),
             ("2023-12", -0.0020, +0.0010, "2024-01-09"),
             ("2024-01", +0.0030, -0.0010, "2024-01-10")]
    months = [m for m, _, _, _ in specs]
    lookup = {}
    for m, ez_r, us_r, v2 in specs:
        lookup[("EZ", m)] = _rev("EZ", m, v2, ez_r)
        lookup[("US", m)] = _rev("US", m, v2, us_r)
    p1 = N4.build_ng4_a5_book("SYN-A5P1", "anchor_p1", months, lookup,
                              grid, grid_index, grid[-1], hold=1)
    nod = N4.build_ng4_a5_book("SYN-NODIFF", "v7nodiff_p1", months,
                               lookup, grid, grid_index, grid[-1], hold=1)
    assert p1["cells"] == nod["cells"]      # all months opposed
    cmp = R.compare_schedules(p1["cells"], nod["cells"], grid_iso,
                              list(N4.PLANE_PAIRS))
    assert cmp["max_abs_rho"] == 1.0
    assert N4.q11_null_validity(1.0, "CTL-V7NODIFF",
                                {1: 2, -1: 2}, {1: 2, -1: 2},
                                ).startswith("control null INVALID")


# --------------------------------------------------------------------------- #
# 2. fail-closed unmeasured cases
# --------------------------------------------------------------------------- #

def test_pair_disjoint_book_is_an_honest_no_shared_pairs_row():
    """A funded-pair-only book (the verbatim ng3/ng1 non-EURUSD shadows'
    geometry) shares no pair with an EURUSD-only anchor: the row reads
    NO_SHARED_PAIRS with max_abs_rho None -- recorded honestly, never a
    silent drop, never an inferred PASS."""
    grid = _grid(date(2024, 1, 1), 20)
    grid_iso = [d.isoformat() for d in grid]
    eurusd_book = {"cells": {f"{d.isoformat()}|EURUSD": 1
                             for d in grid[:5]}}
    cad_book = {"cells": {f"{d.isoformat()}|USDCAD": 1
                          for d in grid[:5]}}
    cmp = R.compare_schedules(eurusd_book["cells"], cad_book["cells"],
                              grid_iso, list(N4.PLANE_PAIRS))
    assert cmp["verdict"] == "NO_SHARED_PAIRS"
    assert cmp.get("max_abs_rho") is None
    pooled = R.pooled_max_abs_rho({"cad_shadow": cmp})
    assert pooled["max_pooled_abs_rho"] is None


def test_unmeasurable_novelty_is_ineligible_fail_closed():
    verdict = N4.proposal_verdict(novelty_max_abs_rho=None)
    assert verdict.startswith("INELIGIBLE_FAIL_CLOSED")
    assert "unmeasurable" in verdict


def test_empty_book_law_beats_everything():
    """The D1 vacuous-book law: 0 fired in-window events ->
    INELIGIBLE_FAIL_CLOSED even if a rho existed (the anchor cannot be
    measured on an empty schedule)."""
    verdict = N4.proposal_verdict(novelty_max_abs_rho=0.05,
                                  empty_book=True)
    assert verdict.startswith("INELIGIBLE_FAIL_CLOSED")
    assert "EMPTY BOOK" in verdict


def test_verdict_boundaries_bar_and_identifiability_kill():
    assert N4.proposal_verdict(novelty_max_abs_rho=0.20) == "ELIGIBLE"
    v = N4.proposal_verdict(novelty_max_abs_rho=0.2499)
    assert v.startswith("VETO(ANCESTRY_VETO rho=0.2499 margin=-0.0499)")
    kill = N4.proposal_verdict(novelty_max_abs_rho=0.10,
                               identifiability_kill=0.98,
                               kill_control_name="CTL-PPPANCESTRY")
    assert "IDENTIFIABILITY_KILL" in kill and "CTL-PPPANCESTRY" in kill
    ok = N4.proposal_verdict(novelty_max_abs_rho=0.10,
                             identifiability_kill=0.9799,
                             kill_control_name="CTL-PPPANCESTRY")
    assert ok == "ELIGIBLE"


def test_q6_row_never_invents_a_floor():
    """No EZ recent floor was ever frozen: the Q-6 row is measured with
    floor null and verdict MEASURED_NO_FLOOR_FROZEN -- never PASS/FAIL."""
    row = N4.evaluate_q6_no_floor(2, "synthetic basis")
    assert row["measured"] == 2 and row["floor"] is None
    assert row["margin"] is None
    assert row["verdict"] == "MEASURED_NO_FLOOR_FROZEN"
    # the verdict function has NO Q-6 axis this cycle: a thin recent
    # window cannot veto and cannot pass anything
    assert N4.proposal_verdict(novelty_max_abs_rho=0.10) == "ELIGIBLE"


# --------------------------------------------------------------------------- #
# 3. the EZ-stream PIT case (v2-day clock + hand-computed s1)
# --------------------------------------------------------------------------- #

def test_a4_s1_pit_v2day_clock_hand_computed():
    """EZ restricted event obs 2016-06, v1 100.0, v2 day Thu 2016-09-01.

    D(e) = first grid day STRICTLY after 2016-09-01 = Fri 2016-09-02
    (a same-day 16:00-NY decision never sees a v2 bound at 23:59:59Z).
    Predictor as-of D(e): I(2016-05)=99.0, I(2015-06)=98.0,
    I(2015-05)=97.5 ->
      I_hat = 99.0 * 98.0 / 97.5 = 9702/97.5
      s1    = 100 * (100 / (9702/97.5) - 1) = 4800/9702
            = 0.49464027932... pp  >= 0.10 -> LONG EURUSD (+1),
    H = 5 cells on EURUSD from 2016-09-02.
    """
    grid = _grid(date(2016, 8, 29), 15)
    grid_index = {d: i for i, d in enumerate(grid)}
    ez = _ez_panel()
    ev = _rev("EZ", "2016-06", "2016-09-01", 0.01, v1_value="100.0")
    book = N4.build_ng4_a4_book("SYN-A4-P1", "anchor", "s1_seasonal_naive",
                                0.10, [ev], ez, grid, grid_index,
                                grid[-1])
    assert book["meta"]["fired_events"] == 1
    assert book["meta"]["events_failed_closed"] == 0
    rec = book["fired_records"][0]
    assert rec["entry"] == date(2016, 9, 2)
    assert rec["sign"] == 1
    expected_s1 = 4800.0 / 9702.0
    assert abs(rec["surprise_pp"] - expected_s1) < 1e-12
    days = sorted({k.split("|")[0] for k in book["cells"]})
    assert days[0] == "2016-09-02"
    assert len(days) == 5                       # H = 5 exposure cells
    assert set(book["cells"].values()) == {1}
    assert all(k.endswith("|EURUSD") for k in book["cells"])


def test_a4_pit_fail_closed_when_predictor_window_closed():
    """The 2015-06 predictor month's ONLY version closes 2016-08-31
    (no later version): at the 2016-09-02 entry the as-of read is None
    -> the event FAILS CLOSED (no cell, never a backfilled guess)."""
    grid = _grid(date(2016, 8, 29), 15)
    grid_index = {d: i for i, d in enumerate(grid)}
    ez = _ez_panel(prev_window_end="2016-08-31")
    assert ez.value_asof("2015-06", date(2016, 9, 2)) is None
    ev = _rev("EZ", "2016-06", "2016-09-01", 0.01, v1_value="100.0")
    book = N4.build_ng4_a4_book("SYN-A4-FC", "anchor", "s1_seasonal_naive",
                                0.10, [ev], ez, grid, grid_index,
                                grid[-1])
    assert book["meta"]["events_failed_closed"] == 1
    assert book["meta"]["fired_events"] == 0
    assert book["cells"] == {}


def test_v7recap_fires_every_event_sign_only():
    """CTL-V7RECAP: ALL events fire regardless of |s|, direction =
    sign(s) (the magnitude structure removed)."""
    grid = _grid(date(2016, 8, 29), 30)
    grid_index = {d: i for i, d in enumerate(grid)}
    ez = _ez_panel()
    ev = _rev("EZ", "2016-06", "2016-09-01", 0.01, v1_value="100.0")
    book = N4.build_ng4_a4_book("SYN-RECAP", "v7recap", "s1_seasonal_naive",
                                0.10, [ev], ez, grid, grid_index,
                                grid[-1])
    assert book["meta"]["fired_events"] == 1
    assert book["meta"]["below_threshold"] == 0
    assert set(book["cells"].values()) == {1}


def test_ppp_ancestry_control_cumulative_median_hand_computed():
    """CTL-PPPANCESTRY hand case.  EZ restricted events (v2 days
    ascending) with R = +0.10, -0.20, +0.30, +0.10 pp -> cumulative
    S = [+0.10, -0.10, +0.20, +0.30].

    anchor fired records with A(m) bounds:
      A1 after v2_1 only: prior S = [+0.10], len 1 < 2 -> dropped
      A2 after v2_2:      S(m) = -0.10; median([-0.10? no: [+0.10,
                          -0.10]) = 0.0; |S-med| = 0.10 >= 0.02 and
                          S < med -> LONG EURUSD (+1)
      A4 after v2_4:      S(m) = +0.30; median([-0.10, +0.10, +0.20,
                          +0.30]) = 0.15; S > med -> SHORT (-1)
    """
    grid = _grid(date(2024, 1, 1), 20)
    grid_index = {d: i for i, d in enumerate(grid)}
    ez_events = [
        _rev("EZ", "2023-09", "2024-01-02", +0.0010),
        _rev("EZ", "2023-10", "2024-01-03", -0.0020),
        _rev("EZ", "2023-11", "2024-01-04", +0.0030),
        _rev("EZ", "2023-12", "2024-01-05", +0.0010),
    ]
    source = {"fired_records": [
        {"entry": date(2024, 1, 8), "month": "2024-02",
         "avail_bound": date(2024, 1, 2)},          # after v2_1 only
        {"entry": date(2024, 1, 9), "month": "2024-03",
         "avail_bound": date(2024, 1, 3)},          # after v2_2
        {"entry": date(2024, 1, 10), "month": "2024-04",
         "avail_bound": date(2024, 1, 5)},          # after v2_4
    ]}
    book = N4.build_ng4_ppp_ancestry_control("SYN-PPP", source, ez_events,
                                             grid, grid_index, hold=1)
    m = book["meta"]
    assert m["dropped_insufficient_priors"] == 1
    assert m["fired_events"] == 2
    assert m["sign_counts"] == {1: 1, -1: 1}
    assert book["cells"][f"{date(2024, 1, 9).isoformat()}|EURUSD"] == 1
    assert book["cells"][f"{date(2024, 1, 10).isoformat()}|EURUSD"] == -1


def test_ng1_kill_shadow_us_leg_fires_eurusd_inverted():
    """The ng1 A4 kill shadow: a US event with a computable positive s1
    fires LONG USD across the funded pairs and SHORT EURUSD (the
    disclosed ng4-plane extension: long USD = short EUR vs USD); a GB
    event fires ONLY its own funded pair (no EURUSD leg exists for
    non-US ng1 economies)."""
    grid = _grid(date(2024, 1, 1), 130)
    grid_index = {d: i for i, d in enumerate(grid)}
    rows = []
    for obs, val in (("2023-04", 97.5), ("2023-05", 98.0),
                     ("2024-04", 100.0), ("2024-05", 101.0)):
        rows.append({"obs": f"{obs}-01", "rs": date(2020, 1, 1),
                     "re": date(9999, 12, 31), "value": val})
    series = {"US": VintagedSeries(series_id="SYN-US", rows=list(rows)),
              "GB": VintagedSeries(series_id="SYN-GB", rows=list(rows))}
    events = [
        {"economy": "US", "reference_period": "2024-05",
         "vintaged_first_value": "103.0",
         "operative_vintaged_available_from": "2024-06-14"},
        {"economy": "GB", "reference_period": "2024-05",
         "vintaged_first_value": "103.0",
         "operative_vintaged_available_from": "2024-06-14"},
    ]
    book = N4.build_ng1_a4_kill_shadow(
        "SYN-NG1-A4P1", "s1_seasonal_naive", 0.10, events, series,
        grid, grid_index, grid[-1])
    # entry: first grid day strictly after Fri 2024-06-14 = Mon 06-17
    entry = date(2024, 6, 17)
    assert entry in grid_index
    # s1 = 100*(103/(100*98/97.5)-1) = 100*(103*97.5/9800 - 1)
    #    = +2.4745... pp >= 0.10 -> fires LONG USD (ssign = +1)
    s1 = 100.0 * (103.0 / (100.0 * 98.0 / 97.5) - 1.0)
    assert s1 >= 0.10
    ssign = 1
    # US event, ng1 law + the ng4 EURUSD extension: long USD -> short
    # every non-USD currency vs USD (EURUSD/GBPUSD/AUDUSD/NZDUSD = -1,
    # USDCAD = +1); GB event same surprise -> funded_pair_sign GB = +1,
    # netting the GBPUSD cell (+1 vs -1 -> sign-of-sum -> -1)
    assert book["cells"][f"{entry.isoformat()}|EURUSD"] == -ssign
    assert book["cells"][f"{entry.isoformat()}|USDCAD"] == ssign
    assert book["cells"][f"{entry.isoformat()}|AUDUSD"] == -ssign
    assert book["cells"][f"{entry.isoformat()}|NZDUSD"] == -ssign
    assert book["meta"]["net_collisions"] >= 1
    assert book["meta"]["eurusd_cells_fired"] == 1   # only the US event
    assert book["meta"]["pair_decisions_fired"] == 6  # US 5 + GB 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
