"""FOREX-NG1 P0 tests (dispatch item 7).

Three mandated classes:

1. fail-closed: the plane adapter must refuse to return bytes whose
   digest drifted by a single byte (tmp CADS store copy), and must
   refuse non-granted series / GA4-missing series;
2. vintage parser fixture: two vintages of the same month, hand-computed
   expectations (first appearance, latest vintage, structure proof);
3. DST/UTC boundaries of announcement instants: exact local->UTC
   conversion across DST boundaries (NZ, CA) and the conservative
   end-of-day bound for date-only evidence on the 16:00-NY grid.
"""

from __future__ import annotations

import os

import pytest

from research.assets.forex_ng1 import plane_adapter as pa
from research.platform_v3.cads import CADS, CADSIntegrityError

SERIES = "S3:forex-announcement-ledger"
ENTRY_CSV = "CA/canada_allitems_nsa_2002_100_monthly.csv"
SAMPLE_CSV = (b"ref_month,index_2002_100\n"
              b"2025-01,167.8\n"
              b"2025-02,168.9\n"
              b"2025-03,169.1\n")


def _tmp_store_with_pin(tmp_path, data: bytes = SAMPLE_CSV):
    store = CADS(str(tmp_path / "store"))
    address = store.register(data)
    store.pin(address, {"series": SERIES, "file": ENTRY_CSV})
    return store, address


# --------------------------------------------------------------------- #
# 1. fail-closed on a 1-byte digest change (tmp copy)
# --------------------------------------------------------------------- #

def test_consume_via_plane_happy_path(tmp_path):
    registry = pa.load_registry()
    ga4 = pa.ga4_granted()
    store, address = _tmp_store_with_pin(tmp_path)
    consumed = pa.consume_via_plane(
        registry, str(tmp_path / "store"), SERIES, ENTRY_CSV,
        str(tmp_path / "scratch"), ga4=ga4)
    assert consumed.resolved_address == address
    assert consumed.nbytes == len(SAMPLE_CSV)
    assert consumed.query_verdict == "FROZEN_QUERY_SUCCESS"
    with open(consumed.scratch_path, "rb") as fh:
        assert fh.read() == SAMPLE_CSV


def test_consume_fail_closed_on_one_byte_flip(tmp_path):
    """Adapter is fail-closed when the object digest changes by 1 byte."""
    registry = pa.load_registry()
    store, address = _tmp_store_with_pin(tmp_path)
    scratch = str(tmp_path / "scratch")

    # happy path proves the tmp copy is consumable
    pa.consume_via_plane(registry, str(tmp_path / "store"), SERIES,
                         ENTRY_CSV, scratch)

    # flip exactly one byte of the pinned object in the tmp store
    obj_path = os.path.join(str(tmp_path / "store"), "objects",
                            address[:2], address)
    with open(obj_path, "rb") as fh:
        raw = fh.read()
    assert raw.endswith(b"1\n") or raw  # non-empty guard
    flipped = raw[:-1] + bytes([raw[-1] ^ 0x01])  # last byte, 1-bit change
    assert flipped != raw and len(flipped) == len(raw)
    with open(obj_path, "wb") as fh:
        fh.write(flipped)

    with pytest.raises(CADSIntegrityError):
        # resolve() verify-on-read must raise; nothing may be returned
        pa.consume_via_plane(registry, str(tmp_path / "store"), SERIES,
                             ENTRY_CSV, scratch)


def test_consume_refused_for_non_granted_series(tmp_path):
    registry = pa.load_registry()
    store, _ = _tmp_store_with_pin(tmp_path)
    store.pin(store.register(b"other"), {"series": "X:unplanned",
                                         "file": "x.csv"})
    with pytest.raises(pa.ConsumptionRefused):
        pa.consume_via_plane(registry, str(tmp_path / "store"),
                             "X:unplanned", "x.csv",
                             str(tmp_path / "scratch"))


def test_consume_refused_when_ga4_cross_check_fails(tmp_path):
    """Registry GRANTED is necessary but not sufficient: the frozen
    V3-GA4 table must also list the series (double-fail-closed)."""
    registry = pa.load_registry()
    _tmp_store_with_pin(tmp_path)
    with pytest.raises(pa.ConsumptionRefused):
        pa.consume_via_plane(
            registry, str(tmp_path / "store"), SERIES, ENTRY_CSV,
            str(tmp_path / "scratch"), ga4=frozenset({"S4:other"}))


def test_consume_refused_when_pin_entry_absent(tmp_path):
    registry = pa.load_registry()
    _tmp_store_with_pin(tmp_path)
    with pytest.raises(pa.ConsumptionRefused):
        pa.consume_via_plane(registry, str(tmp_path / "store"), SERIES,
                             "GB/not_pinned.csv",
                             str(tmp_path / "scratch"))


# --------------------------------------------------------------------- #
# 2. vintage parser fixture: two vintages of the same month (hand-computed)
# --------------------------------------------------------------------- #

FIXTURE_OBS = [
    # January 2025 first print (first vintage): public 2025-02-19
    {"realtime_start": "2025-02-19", "realtime_end": "2025-03-19",
     "date": "2025-01-01", "value": "135.1"},
    # January 2025 REVISED in the second vintage: public 2025-03-19
    {"realtime_start": "2025-03-19", "realtime_end": "2025-08-01",
     "date": "2025-01-01", "value": "135.4"},
    # December 2024 (single vintage)
    {"realtime_start": "2025-02-19", "realtime_end": "2025-08-01",
     "date": "2024-12-01", "value": "134.8"},
    # missing-value marker row must not count as a value
    {"realtime_start": "2025-02-19", "realtime_end": "2025-03-19",
     "date": "2025-01-01", "value": "."},
]


def test_vintage_parser_hand_computed():
    rows = pa.parse_fred_vintaged(FIXTURE_OBS)
    fa = pa.first_appearance(rows)
    # hand-computed: Jan-2025 first appears in the 2025-02-19 vintage at 135.1
    assert fa["2025-01-01"] == ("2025-02-19", "135.1")
    # hand-computed: Dec-2024 first (and only) appearance
    assert fa["2024-12-01"] == ("2025-02-19", "134.8")
    assert len(fa) == 2

    latest = pa.latest_vintage_by_month(rows)
    # hand-computed: the last vintage carrying Jan-2025 is 2025-03-19@135.4
    assert latest["2025-01-01"] == ("2025-03-19", "2025-08-01", "135.4")
    assert latest["2024-12-01"] == ("2025-02-19", "2025-08-01", "134.8")

    proof = pa.vintage_structure_proof(rows)
    assert proof["rows"] == 4
    assert proof["rows_with_realtime_window"] == 4
    assert proof["pct_rows_with_realtime_window"] == 100.0
    assert proof["non_missing_values"] == 3   # the "." row is not a value
    assert proof["distinct_vintages"] == 2
    assert proof["months_with_values"] == 2
    assert proof["months_with_multiple_distinct_values"] == 1  # Jan-2025
    assert proof["every_value_vintaged"] is True


def test_current_vintage_table_fails_structurally():
    """A revised-in-place table (no realtime windows) is rejected at
    parse time -- it can never masquerade as a vintaged archive."""
    with pytest.raises(pa.VintageStructureError):
        pa.parse_fred_vintaged([
            {"date": "2025-01-01", "value": "135.1"},
        ])


def test_ons_snapshot_structure_detected_as_current_vintage():
    """The ONS D7BT official CSV is a single-release snapshot: no
    per-value vintage -> continuation only, never the PIT channel."""
    text = ('"Title","CPI INDEX 00: ALL ITEMS 2015=100"\n'
            '"CDID","D7BT"\n'
            '"Release date","19-08-2026"\n'
            '"2025 MAR","136.1"\n'
            '"2025 APR","136.7"\n')
    parsed = pa.parse_ons_d7bt(text)
    assert parsed["release_date_header"] == "19-08-2026"
    assert parsed["cdid"] == "D7BT"
    assert parsed["rows"] == 2
    assert parsed["per_value_vintage_column"] is False
    assert parsed["structure_verdict"] == "CURRENT_VINTAGE_SNAPSHOT"


# --------------------------------------------------------------------- #
# 3. DST / UTC boundaries of announcement instants
# --------------------------------------------------------------------- #

def test_nz_instant_across_dst_boundary():
    # NZDT (UTC+13) before the April DST end: 10:45 NZ -> 21:45Z prev day
    assert pa.normalize_instant_utc(
        "2024-01-24", "10:45", "Pacific/Auckland") == (
        "2024-01-23T21:45:00Z", "CALENDAR_TIME_UTC_EXACT")
    # NZST (UTC+12) after the 2024-04-07 DST end: 10:45 NZ -> 22:45Z prev day
    assert pa.normalize_instant_utc(
        "2024-04-24", "10:45", "Pacific/Auckland") == (
        "2024-04-23T22:45:00Z", "CALENDAR_TIME_UTC_EXACT")


def test_nz_dst_shift_is_exactly_one_hour():
    from datetime import datetime
    a = pa.normalize_instant_utc(
        "2024-01-24", "10:45", "Pacific/Auckland")[0]
    b = pa.normalize_instant_utc(
        "2024-04-24", "10:45", "Pacific/Auckland")[0]
    dt_a = datetime.fromisoformat(a.replace("Z", "+00:00"))
    dt_b = datetime.fromisoformat(b.replace("Z", "+00:00"))
    # same wall-clock time, 91 days apart: the UTC instants differ by
    # 91 days + 1 hour exactly (the DST offset change), hand-checked
    assert (dt_b - dt_a).total_seconds() == (91 * 86400) + 3600


def test_ca_toronto_across_dst_boundary():
    # EST (UTC-5): 08:30 Toronto -> 13:30Z same day
    assert pa.normalize_instant_utc(
        "2024-01-17", "08:30", "America/Toronto") == (
        "2024-01-17T13:30:00Z", "CALENDAR_TIME_UTC_EXACT")
    # EDT (UTC-4): 08:30 Toronto -> 12:30Z same day
    assert pa.normalize_instant_utc(
        "2024-07-16", "08:30", "America/Toronto") == (
        "2024-07-16T12:30:00Z", "CALENDAR_TIME_UTC_EXACT")


def test_date_only_evidence_is_conservative_for_16ny_grid():
    instant, precision = pa.normalize_instant_utc("2025-04-16")
    assert instant == "2025-04-16T23:59:59Z"
    assert precision == "DATE_ONLY_CONSERVATIVE_END_OF_DAY"
    # the same-day 16:00-NY decision (20:00Z in EDT) is BEFORE the
    # bound -> it cannot see the print; first readable grid point is
    # the next day (no lookahead on date-only evidence)
    assert "2025-04-16T20:00:00Z" < instant


def test_instant_helpers_for_calendars():
    assert pa.parse_gb_release_display("16 April 2025") == "2025-04-16"
    assert pa.gb_ref_period("march2025") == "2025-03"
    assert pa.quarter_first_month_from_end("dec", 2024) == "2024-10"
    assert pa.quarter_first_month_from_end("mar", 2025) == "2025-01"


def test_census_canary_lookup_fabricated_instant_fails():
    """Two fabricated instants (dates absent from every calendar) must
    FAIL lookup -- the census canary rule."""
    coverage = {"GB": {"2025-01-01": ("2025-03-17", "135.1")}}
    instants = [{
        "economy": "GB", "reference_period": "2025-01",
        "publication_date": "2025-02-19",
        "time_local": None, "tz": None,
        "evidence": {"archive_path": "x", "archive_sha256": "y"},
    }]
    census = pa.build_census(instants, coverage, "2018-04-04", "2025-04-30")
    assert census["total_instants"] == 1
    assert pa.census_lookup_instant(
        census, "GB", "2019-03-09")["found"] is False     # fabricated
    assert pa.census_lookup_instant(
        census, "AU", "2021-02-14")["found"] is False     # fabricated
    assert pa.census_lookup_instant(
        census, "GB", "2025-02-19")["found"] is True      # real one


def test_census_pit_fields_and_correction_ordinals():
    coverage = {"GB": {"2025-01-01": ("2025-03-17", "135.1")}}
    base = {"time_local": None, "tz": None, "evidence": {}}
    instants = [
        # primary print of Jan-2025 (bulletin 2025-02-19; archive ingest
        # lags at 2025-03-17 -- the normal OECD-feed direction)
        {"economy": "GB", "reference_period": "2025-01",
         "publication_date": "2025-02-19", **base},
        # a later WDS-style correction release of the SAME ref month
        {"economy": "GB", "reference_period": "2025-01",
         "publication_date": "2025-02-21", **base},
        # reference period has no vintaged value -> excluded
        {"economy": "GB", "reference_period": "2025-02",
         "publication_date": "2025-03-19", **base},
    ]
    census = pa.build_census(instants, coverage, "2018-04-04", "2025-04-30")
    assert census["total_instants"] == 2
    firsts = [i for i in census["instants"] if i["is_first_release_of_period"]]
    assert len(firsts) == 1
    assert census["first_release_counts_by_economy"]["GB"] == 1
    prim, corr = census["instants"]
    # hand-computed: the vintaged value is provably public only from the
    # LATER of bulletin and archive first-realtime (conservative max)
    assert prim["operative_vintaged_available_from"] == "2025-03-17"
    assert prim["vintaged_first_value"] == "135.1"
    assert corr["release_ordinal_in_reference_period"] == 2
    assert corr["is_first_release_of_period"] is False
    reasons = [r for rec in census["excluded"]
               for r in rec["exclusion_reasons"]]
    assert "ref_period_not_vintaged_covered" in reasons


def test_census_records_archive_led_bulletin_anomaly_not_exclusion():
    """When the archive first-realtime PRECEDES the bulletin (NZ 2019Q2
    pattern, FRED 2019-07-11 vs bulletin 2019-07-16), the instant is
    INCLUDED with a recorded anomaly note and the conservative
    availability stays at the bulletin date."""
    coverage = {"NZ": {"2019-04-01": ("2019-07-11", "129.5")}}
    census = pa.build_census(
        [{"economy": "NZ", "reference_period": "2019-04",
          "publication_date": "2019-07-16",
          "time_local": "10:45", "tz": "Pacific/Auckland", "evidence": {}}],
        coverage, "2018-04-04", "2025-04-30")
    assert census["total_instants"] == 1
    rec = census["instants"][0]
    assert rec["pit_notes"] == ["archive_led_bulletin"]
    assert rec["operative_vintaged_available_from"] == "2019-07-16"
    assert rec["publication_instant_utc"] == "2019-07-15T22:45:00Z"  # NZST
