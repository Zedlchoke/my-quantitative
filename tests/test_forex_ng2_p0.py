"""FOREX-NG2 P0 tests: revision-event builder on hand-computed fixtures.

All fixtures are synthetic (hand-computed in-memory VintageRow lists plus
a /tmp FRED-style vintage JSON file); NO network, NO CADS store, NO
scored data, NO PnL.  Every expected number below was computed by hand
from the fixture tables and is asserted exactly:

- revision detection (v1 != v2 with full availability windows);
- equal-value consecutive vintages produce NO event;
- months with a single vintage produce NO event;
- STRICT vintage monotonicity: a duplicate realtime_start for the same
  month raises VintageMonotonicityError (fail-closed, nothing built);
- fabricated-month canary lookups must return found=False;
- S0-window usability filter;
- cross-economy differential month counting;
- magnitude distribution (median/quartiles, linear interpolation);
- frozen floor evaluation (>=30 own per pair-anchor economy, >=12
  cross; honest FAIL on a single economy shortfall);
- Q-6 recent-window bounds (24 calendar months);
- a v2 vintage lacking available-time evidence (no realtime window) is
  NOT a usable revision event.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.forex_ng1.plane_adapter import VintageRow   # noqa: E402
from research.assets.forex_ng2 import revision_series as rs      # noqa: E402


def row(obs, rt_start, rt_end, value):
    return VintageRow(obs_date=obs, realtime_start=rt_start,
                      realtime_end=rt_end, value=value)


# --------------------------------------------------------------------------- #
# fixture A: monthly leg, hand table
#
# month        v1 (realtime, value)          v2 (realtime, value)     event?
# 2020-01-01   (2020-02-15..2020-03-14, 100) (2020-03-15.., 101)      YES +1%
# 2020-02-01   (2020-03-15.., 100)           (2020-04-15.., 100)      no (equal)
# 2020-03-01   (2020-04-15.., 100)           --                       no (single)
# 2020-04-01   (2020-05-15.., 100)           (2020-06-15.., 99)       YES -1%
# --------------------------------------------------------------------------- #

FIXTURE_A = [
    # 2020-01: revised 100 -> 101
    row("2020-01-01", "2020-02-15", "2020-03-14", "100"),
    row("2020-01-01", "2020-03-15", "2020-04-14", "101"),
    row("2020-01-01", "2020-04-15", "2025-08-01", "101"),
    # 2020-02: NOT revised (equal consecutive vintages)
    row("2020-02-01", "2020-03-15", "2020-04-14", "100"),
    row("2020-02-01", "2020-04-15", "2020-05-14", "100"),
    # 2020-03: single vintage only
    row("2020-03-01", "2020-04-15", "2025-08-01", "100"),
    # 2020-04: revised 100 -> 99
    row("2020-04-01", "2020-05-15", "2020-06-14", "100"),
    row("2020-04-01", "2020-06-15", "2025-08-01", "99"),
]


def test_revision_detection_hand_computed():
    built = rs.build_revision_events("GB", FIXTURE_A)
    events = built["events_all"]
    assert built["months_carried"] == 4
    assert built["months_with_second_vintage"] == 3
    assert len(events) == 2
    by_month = {e.obs_month: e for e in events}
    e1 = by_month["2020-01-01"]
    assert e1.v1_value == "100" and e1.v2_value == "101"
    assert e1.v1_realtime_start == "2020-02-15"
    assert e1.v2_realtime_start == "2020-03-15"   # PIT instant of the event
    assert e1.ratio == pytest.approx(101.0 / 100.0 - 1.0)
    e4 = by_month["2020-04-01"]
    assert e4.v2_value == "99"
    assert e4.ratio == pytest.approx(-0.01)
    # equal-value and single-vintage months must NOT be events
    assert "2020-02-01" not in by_month
    assert "2020-03-01" not in by_month


def test_third_vintage_is_not_the_event():
    """The event is the FIRST-to-SECOND vintage gap only (plan section 4):
    a later third vintage changing again does not create another event
    for the same month, and does not change the recorded v1/v2 pair."""
    built = rs.build_revision_events("GB", FIXTURE_A)
    by_month = {e.obs_month: e for e in built["events_all"]}
    # 2020-01 carries a third vintage (101 again): still exactly one
    # event with the original v1/v2 values
    assert by_month["2020-01-01"].v2_value == "101"
    assert sum(1 for e in built["events_all"]
               if e.obs_month == "2020-01-01") == 1


def test_v2_without_available_time_evidence_is_not_an_event():
    """v2 lacking a realtime window carries no available-time evidence:
    excluded (channel law), never silently counted."""
    rows = [
        row("2021-01-01", "2021-02-15", "2021-03-14", "100"),
        row("2021-01-01", "", "", "105"),   # malformed v2 window
    ]
    built = rs.build_revision_events("CA", rows)
    assert built["events_all_count"] == 0


def test_monotonicity_violation_fail_closed():
    """v2.realtime > v1.realtime STRICT: a CONFLICTING duplicate
    realtime_start (different value) for the same month raises and
    NOTHING is built."""
    rows = [
        row("2020-01-01", "2020-02-15", "2020-03-14", "100"),
        row("2020-01-01", "2020-02-15", "2020-03-14", "101"),  # conflict
    ]
    with pytest.raises(rs.VintageMonotonicityError):
        rs.vintages_by_month(rows)
    with pytest.raises(rs.VintageMonotonicityError):
        rs.build_revision_events("GB", rows)


def test_exact_duplicate_rows_deduped_conflicts_still_raise():
    """BYTE-IDENTICAL duplicate rows (same window + value, the measured
    US ingest artifact) dedupe away and the build proceeds; a same-day
    CONFLICT still raises fail-closed."""
    dup_rows = [
        row("2020-01-01", "2020-02-15", "2020-03-14", "100"),
        row("2020-01-01", "2020-03-15", "2025-08-01", "101"),
        row("2020-01-01", "2020-03-15", "2025-08-01", "101"),  # exact dup
    ]
    deduped, removed = rs.dedupe_exact_rows(dup_rows)
    assert removed == 1
    assert len(deduped) == 2
    built = rs.build_revision_events("US", deduped)
    assert built["events_all_count"] == 1
    # without dedupe the archive would fail strictly (disclosed law)
    with pytest.raises(rs.VintageMonotonicityError):
        rs.build_revision_events("US", dup_rows)
    # a conflicting same-day pair survives dedupe and raises downstream
    conflict_rows = [
        row("2020-01-01", "2020-02-15", "2020-03-14", "100"),
        row("2020-01-01", "2020-02-15", "2020-03-14", "100.5"),
    ]
    conflict_deduped, removed2 = rs.dedupe_exact_rows(conflict_rows)
    assert removed2 == 0 and len(conflict_deduped) == 2
    with pytest.raises(rs.VintageMonotonicityError):
        rs.build_revision_events("US", conflict_deduped)


def test_fabricated_month_canary():
    built = rs.build_revision_events("GB", FIXTURE_A)
    events_by_eco = {"GB": built["events_all"]}
    # fabricated months must FAIL lookup
    fabricated = rs.lookup_event(events_by_eco, "GB", "2019-06-01")
    assert fabricated["found"] is False
    assert fabricated["event_count"] == 0
    fabricated2 = rs.lookup_event(events_by_eco, "AU", "2030-02-01")
    assert fabricated2["found"] is False
    # unknown economy must also fail closed
    assert rs.lookup_event(events_by_eco, "ZZ", "2020-01-01")["found"] is False
    # positive control: a real event month is found
    real = rs.lookup_event(events_by_eco, "GB", "2020-01-01")
    assert real["found"] is True
    assert real["event_count"] == 1


def test_usable_window_filter():
    built = rs.build_revision_events("GB", FIXTURE_A)
    usable = rs.usable_events(built["events_all"], rs.S0_WINDOW)
    # both fixture events (v2 realtime 2020-03-15 / 2020-06-15) are
    # inside the S0 window 2018-04-04..2025-04-30
    assert len(usable) == 2
    # a narrower window excludes on the v2 availability day (PIT law)
    narrow = rs.usable_events(built["events_all"],
                              ("2020-01-01", "2020-03-31"))
    assert [e.obs_month for e in narrow] == ["2020-01-01"]


def test_first_print_era_flag():
    """Months older than the feed's realtime era are backfilled history:
    counted per the frozen literal definition but flagged.  The feed's
    era starts 2018-01-01 (its first vintage); 1955 predates it, the
    2020 months are first-printed by the feed itself."""
    rows = [
        row("1955-01-01", "2018-01-01", "2020-03-14", "5.6"),
        row("1955-01-01", "2020-03-15", "2025-08-01", "5.7"),
        row("2020-01-01", "2020-02-15", "2020-03-14", "100"),
        row("2020-01-01", "2020-03-15", "2025-08-01", "101"),
    ]
    built = rs.build_revision_events("GB", rows)
    by_month = {e.obs_month: e for e in built["events_all"]}
    assert by_month["1955-01-01"].first_print_in_realtime_era is False
    assert by_month["2020-01-01"].first_print_in_realtime_era is True


# --------------------------------------------------------------------------- #
# fixture B: two economies for the cross-economy differential
#
# GB usable event months: 2020-01, 2020-04
# CA usable event months: 2020-01, 2020-04, 2020-07
# differential months (>=2 economies): 2020-01, 2020-04  (2020-07 GB absent)
# --------------------------------------------------------------------------- #

def _events_for_months(eco, months, v1_day="15", v2_day_next="16"):
    out = []
    for i, m in enumerate(months):
        out.append(rs.RevisionEvent(
            economy=eco, obs_month=f"{m}-01",
            v1_realtime_start=f"2020-{m[5:]}-{v1_day}",
            v1_realtime_end="2025-08-01", v1_value="100",
            v2_realtime_start=f"2020-{m[5:]}-{v2_day_next}",
            v2_realtime_end="2025-08-01", v2_value="101",
            ratio=0.01, first_print_in_realtime_era=True))
    return out


def test_cross_economy_differential_months():
    usable_by_eco = {
        "GB": _events_for_months("GB", ["2020-01", "2020-04"]),
        "CA": _events_for_months("CA", ["2020-01", "2020-04", "2020-07"]),
    }
    diff = rs.cross_economy_differential_months(usable_by_eco)
    assert diff["total"] == 2
    assert diff["sorted_month_keys"] == ["2020-01", "2020-04"]
    assert diff["months"]["2020-01"] == ["CA", "GB"]   # sorted economies
    assert "2020-07" not in diff["months"]             # single economy


def test_magnitude_distribution_hand_computed():
    """ratios -2%, +1%, +3%, +5% -> median 2.0%, q1 0.25%, q3 3.5%,
    abs-median 2.5% (linear interpolation on positions)."""
    ratios = [-0.02, 0.01, 0.03, 0.05]
    events = _events_for_months("GB", [f"2020-0{i}" for i in
                                       range(1, len(ratios) + 1)])
    events = [
        rs.RevisionEvent(
            economy="GB", obs_month=f"2020-0{i + 1}-01",
            v1_realtime_start="2020-01-15", v1_realtime_end="2020-01-16",
            v1_value="100", v2_realtime_start="2020-02-15",
            v2_realtime_end="2025-08-01", v2_value="101",
            ratio=r, first_print_in_realtime_era=True)
        for i, r in enumerate(ratios)]
    d = rs.magnitude_distribution(events)
    assert d["n"] == 4
    assert d["median_pct"] == pytest.approx(2.0)
    assert d["q1_pct"] == pytest.approx(0.25)
    assert d["q3_pct"] == pytest.approx(3.5)
    assert d["min_pct"] == pytest.approx(-2.0)
    assert d["max_pct"] == pytest.approx(5.0)
    assert d["abs_median_pct"] == pytest.approx(2.5)


def test_magnitude_distribution_empty():
    assert rs.magnitude_distribution([])["n"] == 0


def test_floor_evaluation_honest_fail():
    counts = {"GB": 68, "CA": 85, "AU": 26, "NZ": 44, "US": 0}
    floors = rs.evaluate_floors(counts, cross_differential_total=58)
    assert floors["own_economy"]["GB"]["verdict"] == "PASS"
    assert floors["own_economy"]["GB"]["margin"] == 38
    assert floors["own_economy"]["AU"]["verdict"] == "FAIL"
    assert floors["own_economy"]["AU"]["margin"] == -4
    assert floors["cross_economy"]["verdict"] == "PASS"
    assert floors["cross_economy"]["margin"] == 46
    # one economy below the frozen floor -> honest overall FAIL
    assert floors["verdict"] == "FAIL"
    # US is measured + disclosed, never floor-anchored
    assert floors["non_anchor_economies"]["US"]["usable_events"] == 0


def test_floor_evaluation_all_pass_and_boundary():
    counts = {"GB": 30, "CA": 30, "AU": 30, "NZ": 30}   # boundary: >= floor
    floors = rs.evaluate_floors(counts, cross_differential_total=12)
    assert all(r["verdict"] == "PASS"
               for r in floors["own_economy"].values())
    assert all(r["margin"] == 0 for r in floors["own_economy"].values())
    assert floors["cross_economy"]["verdict"] == "PASS"
    assert floors["verdict"] == "PASS"
    # one below at the boundary -> FAIL
    floors2 = rs.evaluate_floors(
        {"GB": 30, "CA": 30, "AU": 29, "NZ": 30}, 12)
    assert floors2["verdict"] == "FAIL"
    # cross below floor -> FAIL even if own passes
    floors3 = rs.evaluate_floors(counts, 11)
    assert floors3["cross_economy"]["verdict"] == "FAIL"
    assert floors3["verdict"] == "FAIL"


def test_recent_window_bounds_q6():
    lo, hi = rs.recent_window_bounds(("2018-04-04", "2025-04-30"), 24)
    assert (lo, hi) == ("2023-05-01", "2025-04-30")


def test_events_by_year_uses_v2_availability():
    events = _events_for_months("GB", ["2020-01", "2020-04"])
    by_year = rs.events_by_year(events)
    assert by_year == {"2020": 2}


def test_tmp_synthetic_vintage_file_end_to_end(tmp_path):
    """/tmp synthetic FRED-style vintage series: the full parse -> build
    -> usable -> floors path on file bytes (hand-computed expectations)."""
    observations = [
        {"realtime_start": "2020-02-15", "realtime_end": "2020-03-14",
         "date": "2020-01-01", "value": "100"},
        {"realtime_start": "2020-03-15", "realtime_end": "2020-04-14",
         "date": "2020-01-01", "value": "100.5"},   # +0.5% revision
        {"realtime_start": "2020-03-15", "realtime_end": "2020-04-14",
         "date": "2020-02-01", "value": "."},        # missing: skipped
        {"realtime_start": "2020-04-15", "realtime_end": "2025-08-01",
         "date": "2020-02-01", "value": "101"},      # v1 of 2020-02
    ]
    path = tmp_path / "SYNTHETIC.json"
    path.write_text(json.dumps({"observations": observations}))
    payload = json.loads(path.read_text())
    from research.assets.forex_ng1.plane_adapter import parse_fred_vintaged
    rows = parse_fred_vintaged(payload["observations"])
    built = rs.build_revision_events("NZ", rows)
    assert built["events_all_count"] == 1
    event = built["events_all"][0]
    assert event.obs_month == "2020-01-01"
    assert event.ratio == pytest.approx(0.005)
    assert len(rs.usable_events(built["events_all"])) == 1
    # a vintaged shape without realtime windows must fail structurally
    with pytest.raises(pa_error()):
        parse_fred_vintaged(
            [{"date": "2020-01-01", "value": "100"}])


def pa_error():
    from research.assets.forex_ng1.plane_adapter import VintageStructureError
    return VintageStructureError


def test_nonpositive_index_fail_closed():
    rows = [
        row("2020-01-01", "2020-02-15", "2020-03-14", "0"),
        row("2020-01-01", "2020-03-15", "2025-08-01", "101"),
    ]
    with pytest.raises(rs.RevisionStructureError):
        rs.build_revision_events("GB", rows)
