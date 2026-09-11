"""FOREX-NG3 P0 tests: RESTRICTED (first-print) revision builder on
hand-computed fixtures.

All fixtures are synthetic (hand-computed in-memory VintageRow lists plus
a /tmp FRED-style vintage JSON file); NO network, NO CADS store, NO
scored data, NO PnL.  Every expected number below was computed by hand
from the fixture tables and is asserted exactly:

- first-print vs backfill classification (era law inherited from ng2:
  obs month >= the feed's first realtime vintage);
- bulk re-referencing exclusion: >= 10 events with an identical
  (v1 day, v2 day, ratio-to-1e-6) signature are ONE bulk transition and
  are excluded from the restricted stream even when first-print-era; a
  9-event identical group is BELOW the frozen threshold and stays;
- CA-anchored restricted differential counting: a month counts iff CA
  has a restricted event AND >= 1 other economy has one in the same obs
  month; non-anchor months without CA are disclosed, never counted;
- frozen floor evaluation and honest fail-cases: A4 >= 30 CA restricted
  events, A4 Q-6 recent >= 15, A5 >= 12 differential months; a single
  shortfall fails the whole verdict; boundary values pass with margin 0;
- anchor universe verification: GB/AU/NZ are excluded-as-anchor with
  disclosed reasons and appear ONLY as non-anchor legs (US quote leg);
  an unknown economy fails the verification;
- canaries: fabricated months FAIL restricted lookup; a real usable
  backfill/bulk event month FAILS the restricted stream (the restriction
  bites, never a no-op);
- STRICT vintage monotonicity stays fail-closed through the ng3 builder
  (planted conflicting duplicate raises and nothing is built);
- Q-6 recent-window bounds + restricted-stream recent counting.
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
from research.assets.forex_ng2 import revision_series as ng2     # noqa: E402
from research.assets.forex_ng3 import revision_series as rs      # noqa: E402


def row(obs, rt_start, rt_end, value):
    return VintageRow(obs_date=obs, realtime_start=rt_start,
                      realtime_end=rt_end, value=value)


def event(eco, obs_month, v1_day, v2_day, ratio,
          first_print=True, v1="100", v2="101"):
    return ng2.RevisionEvent(
        economy=eco, obs_month=obs_month,
        v1_realtime_start=v1_day, v1_realtime_end="2025-08-01",
        v1_value=v1,
        v2_realtime_start=v2_day, v2_realtime_end="2025-08-01",
        v2_value=v2,
        ratio=ratio, first_print_in_realtime_era=first_print)


# --------------------------------------------------------------------------- #
# fixture R1: first-print vs backfill classification
#
# feed era starts 2018-01-05 (the archive's first realtime vintage):
#   1955-01: v1 (2018-01-05, 5.6) -> v2 (2019-01-05, 5.7)  backfill, EXCLUDED
#   2020-01: v1 (2020-02-15, 100) -> v2 (2020-03-15, 101)  first print, KEPT
#   2020-02: v1 (2020-03-15, 100) -> v2 (2020-04-15, 100)  equal: NO event
# --------------------------------------------------------------------------- #

FIXTURE_R1 = [
    row("1955-01-01", "2018-01-05", "2019-01-04", "5.6"),
    row("1955-01-01", "2019-01-05", "2025-08-01", "5.7"),
    row("2020-01-01", "2020-02-15", "2020-03-14", "100"),
    row("2020-01-01", "2020-03-15", "2025-08-01", "101"),
    row("2020-02-01", "2020-03-15", "2020-04-14", "100"),
    row("2020-02-01", "2020-04-15", "2025-08-01", "100"),
]


def test_first_print_vs_backfill_classification():
    stream = rs.build_restricted_stream("CA", FIXTURE_R1)
    # one event survives the restriction: the 2020-01 first print
    assert len(stream["restricted"]) == 1
    e = stream["restricted"][0]
    assert e.obs_month == "2020-01-01"
    assert e.first_print_in_realtime_era is True
    assert e.ratio == pytest.approx(0.01)
    # the backfill month is a REAL usable event (counted, disclosed) but
    # is NOT in the restricted stream
    assert stream["report"]["usable_events"] == 2
    assert stream["report"]["first_print_era_events"] == 1
    assert stream["report"]["backfill_history_events"] == 1
    assert stream["report"]["restricted_events"] == 1
    backfill_months = {x.obs_month for x in stream["usable"]
                       if not x.first_print_in_realtime_era}
    assert backfill_months == {"1955-01-01"}
    # equal-value consecutive vintages produce no event at all
    assert stream["events_all_count"] == 2


# --------------------------------------------------------------------------- #
# fixture R2: bulk re-referencing exclusion
#
# era starts 2019-01-05 (the 2018-06 ingest row):
#   2019-02..2020-01 (12 months): identical signature
#       v1 (2020-03-05, 100) -> v2 (2020-04-05, 101), ratio exactly +1%
#       = ONE bulk re-referencing transition (>= 10): ALL EXCLUDED
#   2020-02..2020-10 (9 months): identical signature
#       v1 (2020-05-05, 200) -> v2 (2020-06-05, 202), +1%
#       = 9 < 10 threshold: NOT bulk, all KEPT (frozen literal law)
#   2020-11: v1 (2020-12-15, 300) -> v2 (2021-01-15, 303), +1%: KEPT
# hand totals: usable 22, first-print 22, bulk-removed 12, restricted 10
# --------------------------------------------------------------------------- #

def _fixture_r2():
    rows = [
        row("2018-06-01", "2019-01-05", "2025-08-01", "90"),  # era row
    ]
    bulk_months = ["2019-%02d-01" % m for m in range(2, 13)]
    bulk_months.append("2020-01-01")
    for m in bulk_months:                                   # 12 bulk
        rows.append(row(m, "2020-03-05", "2020-04-04", "100"))
        rows.append(row(m, "2020-04-05", "2025-08-01", "101"))
    for m in ["2020-%02d-01" % m for m in range(2, 11)]:     # 9 < 10
        rows.append(row(m, "2020-05-05", "2020-06-04", "200"))
        rows.append(row(m, "2020-06-05", "2025-08-01", "202"))
    rows += [                                                # genuine
        row("2020-11-01", "2020-12-15", "2021-01-14", "300"),
        row("2020-11-01", "2021-01-15", "2025-08-01", "303"),
    ]
    return rows, bulk_months


def test_bulk_re_referencing_group_excluded():
    rows, bulk_months = _fixture_r2()
    stream = rs.build_restricted_stream("GB", rows)
    restricted_months = {e.obs_month for e in stream["restricted"]}
    # all 12 bulk months excluded even though every one is first-print era
    for m in bulk_months:
        assert m not in restricted_months
    # the 9-identical group (below the frozen >=10 threshold) stays
    for m in ["2020-%02d-01" % m for m in range(2, 11)]:
        assert m in restricted_months
    assert "2020-11-01" in restricted_months
    # hand totals
    assert stream["report"]["usable_events"] == 22
    assert stream["report"]["first_print_era_events"] == 22
    assert stream["report"]["backfill_history_events"] == 0
    assert stream["report"]["first_print_era_in_bulk_groups"] == 12
    assert stream["report"]["restricted_events"] == 10
    assert len(stream["report"]["bulk_groups_ge_min"]) == 1
    assert list(stream["report"]["bulk_groups_ge_min"].values()) == [12]


def test_bulk_signature_and_threshold_boundary():
    evs = [event("CA", "2020-%02d-01" % m, "2020-03-05", "2020-04-05",
                 0.01) for m in range(1, 11)]        # exactly 10 = bulk
    assert rs.bulk_group_signatures(evs, min_months=10) == {
        ("2020-03-05", "2020-04-05", 0.01): 10}
    assert len(rs.restricted_events(evs)) == 0
    nine = evs[:9]                                    # 9 = below, kept
    assert rs.bulk_group_signatures(nine, min_months=10) == {}
    assert len(rs.restricted_events(nine)) == 9


# --------------------------------------------------------------------------- #
# fixture R3: CA-anchored restricted differential months
#
# CA restricted months: 2020-01, 2020-04, 2020-07
# GB restricted months: 2020-01, 2020-04
# NZ restricted months: 2020-07, 2020-10
# US restricted months: 2020-04
# differential months (CA AND >=1 other): 2020-01 [CA,GB],
#   2020-04 [CA,GB,US], 2020-07 [CA,NZ]  ->  total 3
# 2020-10 (NZ only, no CA) is disclosed, NOT counted
# --------------------------------------------------------------------------- #

def _r3_streams():
    return {
        "CA": [event("CA", "2020-%02d-01" % m,
                     "2020-%02d-10" % m, "2020-%02d-20" % m, 0.01)
               for m in (1, 4, 7)],
        "GB": [event("GB", "2020-%02d-01" % m,
                     "2020-%02d-10" % m, "2020-%02d-20" % m, 0.02)
               for m in (1, 4)],
        "AU": [event("AU", "2020-10-01",
                     "2020-10-10", "2020-10-20", 0.05)],
        "NZ": [event("NZ", "2020-%02d-01" % m,
                     "2020-%02d-10" % m, "2020-%02d-20" % m, 0.03)
               for m in (7, 10)],
        "US": [event("US", "2020-04-01",
                     "2020-04-10", "2020-04-20", 0.004)],
    }


def test_restricted_differential_months_ca_anchored():
    diff = rs.restricted_differential_months(_r3_streams())
    assert diff["total"] == 3
    assert diff["sorted_month_keys"] == ["2020-01", "2020-04", "2020-07"]
    assert diff["months"]["2020-01"] == ["CA", "GB"]
    assert diff["months"]["2020-04"] == ["CA", "GB", "US"]
    assert diff["months"]["2020-07"] == ["CA", "NZ"]
    # 2020-10 carries AU+NZ restricted events but NO CA event:
    # disclosed, never counted toward the A5 floor
    assert diff["non_anchor_event_months_without_anchor"] == {
        "2020-10": ["AU", "NZ"]}
    assert diff["non_anchor_months_without_anchor_count"] == 1
    assert diff["anchor_restricted_months"] == 3


def test_restricted_differential_requires_anchor():
    """No CA stream -> fail-closed, never an empty differential."""
    streams = _r3_streams()
    del streams["CA"]
    with pytest.raises(rs.RestrictedStreamError):
        rs.restricted_differential_months(streams)
    # anchor present but alone -> zero differential months (honest)
    only_ca = {"CA": _r3_streams()["CA"]}
    assert rs.restricted_differential_months(only_ca)["total"] == 0


# ------------------------------- floors ----------------------------------- #

def test_floor_evaluation_honest_fail_cases():
    # A4 total shortfall: 29 < 30
    f = rs.evaluate_floors(29, 30, 20)
    assert f["a4_ca_own_economy"]["verdict"] == "FAIL"
    assert f["a4_ca_own_economy"]["margin"] == -1
    assert f["a4_ca_recent_q6"]["verdict"] == "PASS"
    assert f["a5_restricted_differential"]["verdict"] == "PASS"
    assert f["verdict"] == "FAIL"
    # A4 recent shortfall: 14 < 15
    f = rs.evaluate_floors(72, 14, 20)
    assert f["a4_ca_recent_q6"]["verdict"] == "FAIL"
    assert f["a4_ca_recent_q6"]["margin"] == -1
    assert f["verdict"] == "FAIL"
    # A5 shortfall: 11 < 12
    f = rs.evaluate_floors(72, 30, 11)
    assert f["a5_restricted_differential"]["verdict"] == "FAIL"
    assert f["a5_restricted_differential"]["margin"] == -1
    assert f["verdict"] == "FAIL"


def test_floor_evaluation_boundary_and_expectation():
    # exact boundary values pass with margin 0
    f = rs.evaluate_floors(30, 15, 12)
    assert f["a4_ca_own_economy"]["margin"] == 0
    assert f["a4_ca_recent_q6"]["margin"] == 0
    assert f["a5_restricted_differential"]["margin"] == 0
    assert f["verdict"] == "PASS"
    # the ng2-census expectation shape (72 first-print / 30 recent /
    # 102 wider-differential months is ng2's, restricted re-measure here)
    f2 = rs.evaluate_floors(72, 30, 12)
    assert f2["verdict"] == "PASS"
    assert f2["a4_ca_own_economy"]["margin"] == 42


# --------------------------- anchor universe ------------------------------ #

def test_anchor_universe_excludes_gb_au_nz():
    streams = _r3_streams()
    floors = rs.evaluate_floors(3, 3, 3)
    check = rs.verify_anchor_universe(streams, floors)
    assert check["anchor"] == "CA"
    assert check["anchor_pair"] == "USDCAD"
    assert check["verdict"] == "PASS"
    # GB/AU/NZ: excluded-as-anchor with disclosed reasons; only legs
    assert set(check["non_anchor_legs"]) == {"GB", "AU", "NZ", "US"}
    for eco in ("GB", "AU", "NZ"):
        assert eco in rs.EXCLUDED_AS_ANCHOR
        assert "excluded as anchor" in check["non_anchor_legs"][eco]["role"]
    # US is the quote leg, never anchored
    assert "quote leg" in check["non_anchor_legs"]["US"]["role"]
    assert "excluded as anchor" not in check["non_anchor_legs"]["US"]["role"]
    # no floor row can carry an excluded economy (CA-only anchoring)
    for key in floors:
        for bad in ("GB", "AU", "NZ"):
            assert bad not in str(key)


def test_anchor_universe_unknown_economy_fails():
    streams = _r3_streams()
    streams["FR"] = [event("FR", "2020-01-01",
                           "2020-01-10", "2020-01-20", 0.01)]
    check = rs.verify_anchor_universe(streams, rs.evaluate_floors(3, 3, 3))
    assert check["verdict"] == "FAIL"
    assert any("FR" in p for p in check["problems"])


# ------------------------------- canaries --------------------------------- #

def test_fabricated_and_restriction_canaries():
    streams = _r3_streams()
    # fabricated months must FAIL restricted lookup
    fabricated = rs.lookup_restricted(streams, "CA", "2030-02-01")
    assert fabricated["found"] is False
    assert fabricated["event_count"] == 0
    assert rs.lookup_restricted(streams, "ZZ", "2020-01-01")["found"] is False
    # positive control: a restricted month is found
    real = rs.lookup_restricted(streams, "CA", "2020-04-01")
    assert real["found"] is True and real["event_count"] == 1
    # restriction canary: a real usable-but-excluded month must FAIL the
    # restricted stream (the restriction bites, never a no-op)
    stream = rs.build_restricted_stream("CA", FIXTURE_R1)
    excluded = rs.lookup_restricted(
        {"CA": stream["restricted"]}, "CA", "1955-01-01")
    assert excluded["found"] is False
    assert "1955-01-01" in {e.obs_month for e in stream["usable"]}


# --------------------------- monotonicity law ------------------------------ #

def test_monotonicity_violation_fail_closed_through_ng3_builder():
    """Planted conflicting duplicate realtime_start (ng2 STRICT law,
    inherited via import): the ng3 builder raises and NOTHING is built."""
    rows = [
        row("2020-01-01", "2020-02-15", "2020-03-14", "100"),
        row("2020-01-01", "2020-02-15", "2020-03-14", "101"),  # conflict
    ]
    with pytest.raises(ng2.VintageMonotonicityError):
        rs.build_restricted_stream("CA", rows)
    # byte-identical duplicates dedupe away first (disclosed artifact);
    # the build then proceeds on the deduped rows (obs 2020-03-01 is
    # first-print era: era start 2020-01-15 <= 2020-03-01)
    dup_rows = [
        row("2020-03-01", "2020-01-15", "2020-02-14", "100"),
        row("2020-03-01", "2020-02-15", "2025-08-01", "101"),
        row("2020-03-01", "2020-02-15", "2025-08-01", "101"),  # exact dup
    ]
    stream = rs.build_restricted_stream("US", dup_rows)
    assert stream["exact_duplicate_rows_removed"] == 1
    assert stream["rows"] == 2 and stream["rows_input"] == 3
    assert len(stream["restricted"]) == 1


# ------------------------------ Q-6 window --------------------------------- #

def test_recent_window_bounds_q6_inherited():
    lo, hi = ng2.recent_window_bounds(("2018-04-04", "2025-04-30"), 24)
    assert (lo, hi) == ("2023-05-01", "2025-04-30")
    assert rs.RECENT_WINDOW_MONTHS == 24


def test_recent_count_on_restricted_stream():
    """Q-6 counts v2 availability days of the RESTRICTED stream inside
    the last 24 calendar months (2023-05-01..2025-04-30, inclusive)."""
    evs = [
        event("CA", "2023-04-01", "2023-04-02", "2023-05-01", 0.01),
        event("CA", "2023-12-01", "2023-12-02", "2024-01-15", 0.01),
        event("CA", "2025-03-01", "2025-03-02", "2025-04-30", 0.01),
        event("CA", "2023-03-01", "2023-03-02", "2023-04-30", 0.01),  # out
        event("CA", "2022-05-01", "2022-05-02", "2022-06-15", 0.01),  # out
    ]
    recent = rs.restricted_recent_events(evs)
    assert recent["window"] == ["2023-05-01", "2025-04-30"]
    assert recent["count"] == 3


# ------------------------- end-to-end on /tmp bytes ------------------------ #

def test_tmp_synthetic_vintage_file_end_to_end(tmp_path):
    """/tmp synthetic FRED-style vintage archive through the full ng3
    path: parse -> restricted stream (hand-computed expectations).

    Hand table (era starts 2018-01-05):
      1955-01  v1 (2018-01-05, 5.6) -> v2 (2019-01-05, 5.7)  backfill
      2019-02..2019-11 (10 months)  v1 (2020-03-05, 100) ->
               v2 (2020-04-05, 101)  bulk group (10 identical >= 10)
      2020-11  v1 (2020-12-15, 300) -> v2 (2021-01-15, 303)  KEPT +1%
      2020-12  v1 (2021-01-15, 100) -> v2 (2021-02-15, 100)  equal: none
    usable = 1 backfill + 10 bulk + 1 genuine = 12; restricted = 1.
    """
    observations = [
        {"realtime_start": "2018-01-05", "realtime_end": "2019-01-04",
         "date": "1955-01-01", "value": "5.6"},
        {"realtime_start": "2019-01-05", "realtime_end": "2025-08-01",
         "date": "1955-01-01", "value": "5.7"},
        {"realtime_start": "2020-03-05", "realtime_end": "2020-04-04",
         "date": "2020-01-01", "value": "."},            # missing: skipped
    ]
    for m in range(2, 12):                                # 2019-02..11
        observations += [
            {"realtime_start": "2020-03-05", "realtime_end": "2020-04-04",
             "date": "2019-%02d-01" % m, "value": "100"},
            {"realtime_start": "2020-04-05", "realtime_end": "2025-08-01",
             "date": "2019-%02d-01" % m, "value": "101"},
        ]
    observations += [
        {"realtime_start": "2020-12-15", "realtime_end": "2021-01-14",
         "date": "2020-11-01", "value": "300"},
        {"realtime_start": "2021-01-15", "realtime_end": "2025-08-01",
         "date": "2020-11-01", "value": "303"},
        {"realtime_start": "2021-01-15", "realtime_end": "2021-02-14",
         "date": "2020-12-01", "value": "100"},
        {"realtime_start": "2021-02-15", "realtime_end": "2025-08-01",
         "date": "2020-12-01", "value": "100"},
    ]
    path = tmp_path / "SYNTHETIC_NG3.json"
    path.write_text(json.dumps({"observations": observations}))
    from research.assets.forex_ng1.plane_adapter import parse_fred_vintaged
    rows = parse_fred_vintaged(
        json.loads(path.read_text())["observations"])
    stream = rs.build_restricted_stream("CA", rows)
    assert stream["report"]["usable_events"] == 12
    assert stream["report"]["backfill_history_events"] == 1
    assert stream["report"]["first_print_era_in_bulk_groups"] == 10
    assert stream["report"]["restricted_events"] == 1
    e = stream["restricted"][0]
    assert e.obs_month == "2020-11-01"
    assert e.ratio == pytest.approx(0.01)
    assert e.first_print_in_realtime_era is True
    # restricted differential with CA alone: honest zero
    only_ca = rs.restricted_differential_months({"CA": stream["restricted"]})
    assert only_ca["total"] == 0
    # a vintaged shape without realtime windows must fail structurally
    from research.assets.forex_ng1.plane_adapter import VintageStructureError
    with pytest.raises(VintageStructureError):
        parse_fred_vintaged([{"date": "2020-01-01", "value": "100"}])


def test_frozen_constants_match_plan():
    """Plan section 3 frozen floors + laws, asserted verbatim."""
    assert rs.CA_FIRST_PRINT_FLOOR == 30
    assert rs.CA_RECENT_FLOOR == 15
    assert rs.DIFFERENTIAL_FLOOR == 12
    assert rs.BULK_GROUP_MIN_MONTHS == 10
    assert rs.ANCHOR_ECONOMY == "CA"
    assert sorted(rs.EXCLUDED_AS_ANCHOR) == ["AU", "GB", "NZ"]
    assert rs.NON_ANCHOR_LEGS == ("GB", "AU", "NZ", "US")
    assert rs.S0_WINDOW == ("2018-04-04", "2025-04-30")
