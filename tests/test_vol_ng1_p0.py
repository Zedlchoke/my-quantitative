"""VOL-NG1 P0 adoption tests (lane p0, task vol-ng1-p0-adoption).

Three law-groups (dispatch packet: "hand-computed census assertions +
manifest hash checks"):

1. SANDBOXED adapter tests -- every case runs on tmp_path fixtures (a
   throwaway CADS store + authority journal built through the SAME
   ``VolNg1Authority``/``CADS`` machinery); the committed cycle store
   and journal are never written.  Hand-computed values:
   - fixture CSV sha256 ``46984b07...`` computed offline from the exact
     fixture text (87 bytes); a one-byte tamper (``20.5 -> 21.5`` at
     offset 53) hashes to ``79b2bec9...`` and MUST fail closed;
   - overlap fixture: VIX has 2020-01-02+03, VIX9D only 2020-01-03,
     VIX3M 2020-01-03+06 -> the common intersection is EXACTLY
     {2020-01-03} (1 day, 0.0y span, 1 instant post-2015);
   - VXX served window 2018-01-18 -> 2026-09-11 is 3158 days =
     8.6461y (hand-computed); UVXY 2011-10-04 -> 2026-09-11 is 5456
     days = 14.9377y.

2. SANDBOXED census canaries (P-7): a fabricated date must be absent
   from every series and the intersection; a never-existed index
   column name must refuse the parser AND the name census; a
   fabricated ETP ticker must be refused at the plane.

3. COMMITTED-ARTIFACT manifest hash checks (offline, read-only): every
   frozen digest in the adapter equals sha256 of the committed raw
   bytes; the committed census floors equal the hand-recorded
   measurements (F1 15.6851y >= 8; F2 2940 >= 1000; F3 six qualifying
   legs; F4 TVIX+ZIV proven with clean never-existed controls); the
   committed adoption store re-resolves through the plane with
   digest-identical shadow parity.

No network, no scoring, no outcome numbers anywhere.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.assets.vol_ng1 import census as vc            # noqa: E402
from research.assets.vol_ng1 import plane_adapter as pa     # noqa: E402
from research.platform_v3.authority import NotInTargetSet   # noqa: E402
from research.platform_v3.cads import CADS                  # noqa: E402

# --------------------------------------------------------------------- #
# hand-computed fixture constants
# --------------------------------------------------------------------- #
FIXTURE_CSV = (
    "DATE,OPEN,HIGH,LOW,CLOSE\n"
    "01/02/2020,20.0,21.0,19.0,20.5\n"
    "01/03/2020,20.5,22.0,20.0,21.0\n"
)
FIXTURE_CSV_SHA256 = (
    "46984b07d682dc6c4712481aff56743b0c3f21eb798786f2af9438e205bc5e76")
TAMPERED_CSV_SHA256 = (
    "79b2bec9a00a9b582d90c199a26327ceb74e432f40d0bc43bebe5979a51256d8")
FIXTURE_ENTRY = "VIX_History.csv"
FIXTURE_SERIES = pa.SERIES_CBOE
FAKE_DIGEST = "00" * 32

SERIES_CBOE = "S7:cboe-vol-index-histories"
SERIES_ETP = "EODHD-F1:eodhd-vol-etp-eod"
SERIES_DELISTED = "EODHD-F1:eodhd-vol-etp-delisted"


# --------------------------------------------------------------------- #
# fixture builders (sandboxed)
# --------------------------------------------------------------------- #
def build_plane(tmp_path: Path, data: bytes = FIXTURE_CSV.encode()):
    """Throwaway granted plane: tmp CADS store + tmp authority journal
    adjudicated GRANTED through VolNg1Authority (full state machine).
    Resolution tests use the explicit-series form; consume-by-name is
    covered against the committed store in group 3."""
    store_root = tmp_path / "store"
    store = CADS(str(store_root))
    addr = store.register(data)
    store.pin(addr, {"series": FIXTURE_SERIES, "file": FIXTURE_ENTRY})
    journal = tmp_path / "authority_journal.jsonl"
    reg = pa.VolNg1Authority(str(journal))
    reg.register(FIXTURE_SERIES, source="cboe-cdn", channel="cboe-official")
    reg.transition(FIXTURE_SERIES, "INGESTED")
    reg.transition(FIXTURE_SERIES, "VERIFIED")
    reg.evidence(FIXTURE_SERIES,
                 pit_verdict="PASS_PIT_EVIDENCED",
                 license_status="AUTHORIZED",
                 entitlement_status="AUTHORIZED",
                 canary_probe={"cboe-official": "PASS"},
                 cads_pins=[addr])
    outcome = reg.adjudicate(FIXTURE_SERIES, granted_by="TEST",
                             granted_at="2026-09-12T00:00:00+00:00")
    assert outcome == "GRANTED"
    plane = pa.VolNg1Plane(store_root=str(store_root),
                           registry_journal=str(journal))
    return plane, addr


# --------------------------------------------------------------------- #
# group 1a: sandboxed adapter (granted resolve, verify-on-read)
# --------------------------------------------------------------------- #
def test_granted_resolve_matches_hand_computed_digest(tmp_path):
    plane, addr = build_plane(tmp_path)
    assert plane.verdict(FIXTURE_SERIES) == "GRANTED"
    res = plane.resolve_entry(FIXTURE_SERIES, FIXTURE_ENTRY,
                              expected_sha256=addr)
    assert res["cads_address"] == addr
    assert res["sha256_measured"] == FIXTURE_CSV_SHA256 == addr
    assert res["bytes"] == 87
    assert res["data"] == FIXTURE_CSV.encode()
    assert res["verdict"] == "GRANTED"


def test_one_byte_digest_change_fails_closed(tmp_path):
    """Flip exactly one byte inside the tmp CADS object (20.5 -> 21.5):
    resolve must fail closed (verify-on-read), never return drifted
    bytes and never repair."""
    plane, addr, = build_plane(tmp_path)
    obj = tmp_path / "store" / "objects" / addr[:2] / addr
    raw = bytearray(obj.read_bytes())
    i = raw.index(b"01/03/2020,20.5")
    raw[i + 12] = ord("1")                     # 20.5 -> 21.5: one byte
    tampered = bytes(raw)
    assert len(tampered) == len(FIXTURE_CSV)
    assert hashlib.sha256(tampered).hexdigest() == TAMPERED_CSV_SHA256
    obj.write_bytes(tampered)
    with pytest.raises(pa.PlaneDataBlocked) as excinfo:
        plane.resolve_entry(FIXTURE_SERIES, FIXTURE_ENTRY,
                            expected_sha256=addr)
    assert excinfo.value.reason == "BLOCKED_DATA"
    assert obj.read_bytes() == tampered        # never "fixed" back


def test_frozen_digest_mismatch_fails_closed_before_resolve(tmp_path):
    plane, _ = build_plane(tmp_path)
    with pytest.raises(pa.PlaneDataBlocked) as excinfo:
        plane.resolve_entry(FIXTURE_SERIES, FIXTURE_ENTRY,
                            expected_sha256=FAKE_DIGEST)
    assert excinfo.value.reason == "BLOCKED_DATA"
    assert "no re-download" in str(excinfo.value)


def test_unknown_series_refused_fail_closed(tmp_path):
    """P-7 shape: a nonexistent series name must be refused."""
    plane, _ = build_plane(tmp_path)
    verdict = plane.verdict("S9:not-a-real-series")
    assert verdict != "GRANTED"
    with pytest.raises(pa.PlaneConsumptionRefused):
        plane.resolve_entry("S9:not-a-real-series", FIXTURE_ENTRY,
                            expected_sha256=None)


def test_cycle_target_set_narrower_than_platform_set(tmp_path):
    """The VOL-NG1 registry must refuse even PLATFORM-frozen series
    (S1:form4-stream is in the platform's S1-S4 set, not the cycle's)."""
    journal = tmp_path / "j2.jsonl"
    reg = pa.VolNg1Authority(str(journal))
    with pytest.raises(NotInTargetSet):
        reg.register("S1:form4-stream", source="sec-edgar",
                     channel="edgar")


def test_adjudication_without_channel_canary_blocks(tmp_path):
    """Fail-closed authority: GRANT requires the PASS channel canary;
    without it the series is BLOCKED (no partial credit)."""
    store_root = tmp_path / "store2"
    store = CADS(str(store_root))
    addr = store.register(FIXTURE_CSV.encode())
    store.pin(addr, {"series": FIXTURE_SERIES, "file": FIXTURE_ENTRY})
    journal = tmp_path / "j3.jsonl"
    reg = pa.VolNg1Authority(str(journal))
    reg.register(FIXTURE_SERIES, source="cboe-cdn", channel="cboe-official")
    reg.transition(FIXTURE_SERIES, "INGESTED")
    reg.transition(FIXTURE_SERIES, "VERIFIED")
    reg.evidence(FIXTURE_SERIES,
                 pit_verdict="PASS_PIT_EVIDENCED",
                 license_status="AUTHORIZED",
                 entitlement_status="AUTHORIZED",
                 canary_probe={"cboe-official": "FAIL"},   # <-- failed canary
                 cads_pins=[addr])
    outcome = reg.adjudicate(FIXTURE_SERIES, granted_by="TEST",
                             granted_at="2026-09-12T00:00:00+00:00")
    assert outcome.startswith("BLOCKED")
    assert reg.verdict(FIXTURE_SERIES) != "GRANTED"


# --------------------------------------------------------------------- #
# group 1b: hand-computed census assertions
# --------------------------------------------------------------------- #
def test_parse_cboe_csv_hand_computed():
    series = vc.parse_cboe_csv(FIXTURE_CSV.encode())
    assert series == {"2020-01-02": 20.5, "2020-01-03": 21.0}


def test_never_existed_index_column_refused_by_parser():
    fake = b"DATE,VIX2M,CLOSE\n01/02/2020,20.0,20.0\n"
    with pytest.raises(vc.CensusError):
        vc.parse_cboe_csv(fake)


def test_never_existed_index_name_refused_by_census():
    with pytest.raises(vc.CensusError):
        vc.require_frozen_index_name("VIX2M")
    with pytest.raises(vc.CensusError):
        vc.require_frozen_index_name("VIXM2")
    # the frozen census names themselves are accepted
    for name in ("VIX", "VIX9D", "VIX3M", "VIX6M"):
        assert vc.require_frozen_index_name(name) == name


def test_overlap_census_hand_computed_single_common_day():
    series = {
        "VIX": {"2020-01-02": 20.5, "2020-01-03": 21.0},
        "VIX9D": {"2020-01-03": 15.0},
        "VIX3M": {"2020-01-03": 18.0, "2020-01-06": 18.2},
    }
    ov = vc.overlap_census(series)
    assert ov["first_common_date"] == "2020-01-03"
    assert ov["last_common_date"] == "2020-01-03"
    assert ov["common_days"] == 1
    assert ov["span_years"] == 0.0
    assert ov["instants_post_2015"] == 1
    assert ov["per_leg_rows"] == {"VIX": 2, "VIX9D": 1, "VIX3M": 2}


def test_overlap_census_missing_leg_fails_closed():
    with pytest.raises(vc.CensusError):
        vc.overlap_census({"VIX": {"2020-01-02": 20.0},
                           "VIX9D": {"2020-01-02": 15.0}})


def test_etp_leg_coverage_hand_computed_vxx_window():
    """The served VXX window (2018-01-18 -> 2026-09-11) is 3158 days
    = 8.6461y (hand-computed); crosses the 6y floor."""
    bars = [{"date": "2018-01-18", "close": 30.0,
             "adjusted_close": 30.0},
            {"date": "2026-09-11", "close": 25.0,
             "adjusted_close": 25.0}]
    cov = vc.etp_leg_coverage(bars)
    assert cov["first_bar"] == "2018-01-18"
    assert cov["last_bar"] == "2026-09-11"
    assert cov["bars"] == 2
    assert cov["years_eod"] == 8.6461


def test_floors_f3_counts_only_qualifying_legs():
    living = {"LEG_A": {"years_eod": 6.5}, "LEG_B": {"years_eod": 6.0},
              "LEG_C": {"years_eod": 5.9999}}
    dl = {"served": True,
          "dead_present": {"TVIX": True},
          "controls_absent": {"ZZZVIX": True, "QVIXX": True}}
    floors = vc.floors(
        {"span_years": 15.6851, "instants_post_2015": 2940,
         "first_common_date": "2011-01-04",
         "last_common_date": "2026-09-11"},
        living, dl)
    assert floors["F1_common_term_structure_coverage_years"]["verdict"] \
        == "PASS"
    assert floors["F2_term_structure_instants_post_2015"]["verdict"] \
        == "PASS"
    assert floors["F3_living_etp_legs_with_6y_eod"]["qualifying_legs"] \
        == ["LEG_A", "LEG_B"]
    assert floors["F3_living_etp_legs_with_6y_eod"]["verdict"] == "PASS"
    assert floors["F4_delisted_vol_etp_proven"]["verdict"] == "PASS"


def test_f4_fails_without_clean_negative_controls():
    floors = vc.floors(
        {"span_years": 15.6851, "instants_post_2015": 2940,
         "first_common_date": "2011-01-04",
         "last_common_date": "2026-09-11"},
        {}, {"served": True, "dead_present": {"TVIX": True},
             "controls_absent": {"ZZZVIX": True, "QVIXX": False}})
    # a never-existed control PRESENT in the list poisons the channel
    assert floors["F4_delisted_vol_etp_proven"]["verdict"] == "FAIL"


def test_corp_action_inventory_hand_computed():
    """A 4x raw step with an exactly-continuous adjusted series
    classifies ADJUSTED_CONTINUOUS with implied factor exactly 4.0; an
    uncompensated step tracks raw in both series (implied 1.0)."""
    bars = [
        {"date": "2020-01-02", "close": 10.0, "adjusted_close": 5.0},
        {"date": "2020-01-03", "close": 40.0, "adjusted_close": 5.0},
    ]
    inv = vc.detect_corp_action_steps(bars)
    assert len(inv["step_events"]) == 1
    step = inv["step_events"][0]
    assert step["classification"] == "ADJUSTED_CONTINUOUS"
    assert step["implied_factor"] == 4.0
    # a real price collapse is tracked by the adjusted series
    bars2 = [
        {"date": "2020-01-02", "close": 71.82, "adjusted_close": 71.82},
        {"date": "2020-01-03", "close": 12.24, "adjusted_close": 12.24},
    ]
    inv2 = vc.detect_corp_action_steps(bars2)
    assert inv2["step_events"][0]["classification"] == "ADJUSTED_TRACKS_RAW"
    assert inv2["step_events"][0]["implied_factor"] == 1.0


# --------------------------------------------------------------------- #
# group 1c: P-7 canary function (fabricated dates)
# --------------------------------------------------------------------- #
def test_canaries_fabricated_dates_absent_hand_computed():
    series = {
        "VIX": {"2020-01-02": 20.5, "2020-01-03": 21.0},
        "VIX9D": {"2020-01-03": 15.0},
        "VIX3M": {"2020-01-03": 18.0},
    }
    dl = {"dead_present": {}, "controls_absent": {"ZZZVIX": True,
                                                  "QVIXX": True}}
    rows = vc.canaries(series, dl)
    by_name = {r["canary"]: r for r in rows}
    assert by_name["fabricated_date"]["verdict"] == "PASS"
    assert by_name["fabricated_date"]["found"] is False
    assert by_name["never_existed_index_column"]["verdict"] == "PASS"
    assert by_name["fabricated_etp_ticker"]["verdict"] == "PASS"


# --------------------------------------------------------------------- #
# group 2: committed-artifact manifest hash checks (offline, read-only)
# --------------------------------------------------------------------- #
def test_every_frozen_digest_matches_committed_raw_bytes():
    for entry_name, meta in pa.all_frozen_entries().items():
        raw = Path(pa.raw_path_for(entry_name))
        assert raw.is_file(), f"raw snapshot missing: {raw}"
        digest = hashlib.sha256(raw.read_bytes()).hexdigest()
        assert digest == meta["sha256"], entry_name


def test_committed_census_floors_equal_hand_recorded_measurements():
    repo = Path(__file__).resolve().parents[1]
    census = json.loads(
        (repo / "research/control/vol_ng1_run/p0_census.json")
        .read_text(encoding="utf-8"))
    floors = census["floors"]
    assert floors["F1_common_term_structure_coverage_years"][
        "measured"] == 15.6851
    assert floors["F1_common_term_structure_coverage_years"][
        "first_common_date"] == "2011-01-04"
    assert floors["F2_term_structure_instants_post_2015"][
        "measured"] == 2940
    assert floors["F3_living_etp_legs_with_6y_eod"]["qualifying_legs"] \
        == ["SVXY", "UVXY", "VIXM", "VIXY", "VXX", "VXZ"]
    assert floors["F4_delisted_vol_etp_proven"]["dead_present"] \
        == ["TVIX", "ZIV"]
    for name, row in floors.items():
        assert row["verdict"] == "PASS", name


def test_committed_ingest_manifest_reproductions_and_negative_probe():
    repo = Path(__file__).resolve().parents[1]
    manifest = json.loads(
        (repo / "research/control/vol_ng1_run/p0_ingest_manifest.json")
        .read_text(encoding="utf-8"))
    assert manifest["key_loaded"] is True
    assert manifest["key_echoed"] is False
    assert all(p["frozen_digest_reproduced"] for p in manifest["cboe"])
    assert all(p["url"].endswith("api_token=<REDACTED>")
               or "api_token" not in p["url"] for p in manifest["cboe"])
    xiv = manifest["xiv_plain_eod_probe"]
    assert xiv["served"] is False or xiv["bars"] == 0
    assert xiv["bars"] == 0          # Lead-probe semantics reproduced
    dl = manifest["delisted_channel"]
    assert dl["served"] is True
    assert dl["total_symbols"] > 1000
    assert dl["dead_present"] == {"XIV": False, "TVIX": True,
                                  "ZIV": True, "XVIX": False}
    assert dl["controls_absent"] == {"ZZZVIX": True, "QVIXX": True}


def test_delisted_census_digest_frozen_in_adapter():
    repo = Path(__file__).resolve().parents[1]
    entry = "eodhd_us_delisted_census.json"
    meta = pa.all_frozen_entries()[entry]
    raw = repo / "research/control/vol_ng1_run/p0_delisted_census.json"
    digest = hashlib.sha256(raw.read_bytes()).hexdigest()
    assert digest == meta["sha256"]
    census = json.loads(raw.read_text(encoding="utf-8"))
    assert census["dead_present"]["TVIX"] is True
    assert census["dead_present"]["ZIV"] is True
    assert census["wanted_records"]["TVIX"]["Code"] == "TVIX"
    assert "VIX Short-Term" in census["wanted_records"]["TVIX"]["Name"]
    # honest absence: XIV is NOT on the delisted channel (and returned
    # an empty list on the plain eod endpoint) -- recorded, never
    # fabricated around
    assert "XIV" not in census["wanted_records"]
    assert census["dead_present"]["XIV"] is False
    assert census["xiv_plain_eod_probe"]["bars"] == 0


# --------------------------------------------------------------------- #
# group 3: the committed adoption store (read-only plane)
# --------------------------------------------------------------------- #
def _real_plane():
    return pa.VolNg1Plane()     # defaults: committed cycle store


def test_real_plane_series_verdicts():
    plane = _real_plane()
    assert plane.verdict(SERIES_CBOE) == "GRANTED"
    assert plane.verdict(SERIES_ETP) == "GRANTED"
    assert plane.verdict(SERIES_DELISTED) == "GRANTED"
    assert plane.verdict("S9:not-a-real-series") != "GRANTED"


def test_real_plane_consume_vix_matches_frozen_digest():
    plane = _real_plane()
    meta = pa.FROZEN_ENTRIES["VIX_History.csv"]
    res = plane.consume("VIX_History.csv")
    assert res["cads_address"] == meta["sha256"]
    assert res["sha256_measured"] == meta["sha256"]
    series = vc.parse_cboe_csv(res["data"])
    assert min(series) == "1990-01-02"     # official VIX history start
    assert max(series) == "2026-09-11"
    assert len(series) == 9271


def test_real_plane_shadow_parity_identical():
    plane = _real_plane()
    for entry_name in ("VIX_History.csv", "VIX9D_History.csv",
                       "VXX.US_eod.json",
                       "eodhd_us_delisted_census.json"):
        p = plane.shadow_parity(entry_name)
        assert p["identical"] is True, entry_name
        assert p["plane_sha256"] == p["direct_sha256"]


def test_real_plane_ticker_canaries_refused():
    """P-7: fabricated ETP tickers / index names are refused at the
    plane (never consumed, never fetched)."""
    plane = _real_plane()
    for fake in ("XVXX.US_eod.json", "VIX2M_History.csv",
                 "ZZZVIX.US_eod.json", "not-in-the-census.csv"):
        with pytest.raises(pa.PlaneConsumptionRefused):
            plane.consume(fake)


def test_real_plane_query_bounds_vix():
    from datetime import date
    plane = _real_plane()
    q = plane.query_csv_bounds("VIX_History.csv")
    assert q["query_verdict"] == "SUCCESS"
    assert q["rows"] == [[9271, date(1990, 1, 2), date(2026, 9, 11)]]
