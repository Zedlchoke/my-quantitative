"""RATES-NG1 P0 tests (dispatch item 7).

Hand-computed assertions on the committed P0 census artifacts and
manifest hashes, plus fail-closed adapter behavior on throwaway tmp
fixtures (no network, no shared state):

1. gate + floors: the committed p0_gate.json verdict and every frozen
   floor measured value are asserted against hand-computed numbers;
2. substrate manifest: 63 pinned files, well-formed digests, spot
   re-hash of present raw bytes;
3. census numbers: treasury coverage (5429/5660), tenor columns per
   year (1990: 9, 2005: 10, 2026: 14), ETP rows/windows (TLT 6071
   2002-07-26..2026-09-11 reproduces the Lead's live probe), FRED pins
   + CPIAUCSL 1962-row zero-drift overlap, auction event count 3555
   (>= 150 floor) with window discipline;
4. canaries: all three fabricated accesses REFUSED_AS_EXPECTED;
5. adapter fail-closed (tmp fixtures): frozen-set refusal, one-byte
   digest drift BLOCKED, fabricated date/tenor/ticker refusals,
   overlap-verify and split-step hand-computed math.
"""

from __future__ import annotations

import hashlib
import json
import os

import pytest

from research.assets.rates_ng1 import plane_adapter as pa
from research.assets.rates_ng1 import substrate as sub

WORKTREE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".."))
RUN_DIR = os.path.join(WORKTREE, "research", "control", "rates_ng1_run")
GATE_PATH = os.path.join(RUN_DIR, "p0_gate.json")
MANIFEST_PATH = os.path.join(RUN_DIR, "substrate_manifest.json")


def _load(name: str) -> dict:
    with open(os.path.join(RUN_DIR, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def gate() -> dict:
    return _load("p0_gate.json")


@pytest.fixture(scope="module")
def manifest() -> dict:
    return _load("substrate_manifest.json")


def _tmp_plane(tmp_path, entries: dict[str, bytes]) -> pa.RatesNG1Plane:
    """A throwaway plane over tmp raw bytes + a matching tmp manifest."""
    files: dict[str, dict] = {}
    raw_root = tmp_path / "raw"
    for name, data in entries.items():
        dest = raw_root / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        files[name] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "source_url": "fixture://rates_ng1_test",
        }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(
        {"schema": "fixture", "files": files,
         "file_count": len(files)}))
    return pa.RatesNG1Plane(str(manifest_path), str(raw_root))


# --------------------------------------------------------------------- #
# 1. gate + floors
# --------------------------------------------------------------------- #

def test_gate_verdict_pass(gate):
    assert gate["schema"] == "rates_ng1_run/p0_gate@1"
    assert gate["gate"] == "RATES-NG1-P0"
    assert gate["cycle_id"] == "RATES-NG1"
    assert gate["task_id"] == "rates-ng1-p0-adoption"
    assert gate["verdict"] == "PASS"
    assert gate["blockers"] == []


def test_gate_worktree_identity(gate):
    assert gate["git"]["branch"] == "orca/rates-ng1-integration"
    assert gate["git"]["head_sha"] == \
        "bf576df8e0458dffc286c48b209a31dc25062022"


def test_all_four_floors_pass(gate):
    assert set(gate["floors"]) == {
        "F1_treasury_curve_coverage", "F2_fred_granted_repin",
        "F3_treasury_etp_census", "F4_auction_calendar_events"}
    assert all(f["verdict"] == "PASS" for f in gate["floors"].values())


def test_every_pull_succeeded(gate):
    statuses = {v["status"] for v in gate["pull_log"].values()}
    assert statuses == {"PULLED"}
    assert len(gate["pull_log"]) == 63


def test_no_api_key_in_any_recorded_url(gate):
    """V13 law: no key material in any recorded URL/byte of the gate."""
    blob = json.dumps(gate)
    assert "api_key=REDACTED" not in blob or True  # redactions allowed
    for marker in ("api_key=", "api_token="):
        for line in blob.split('"'):
            if marker in line:
                value = line.split(marker, 1)[1].split("&")[0]
                assert value == "REDACTED", "leaked credential fragment"


# --------------------------------------------------------------------- #
# 2. substrate manifest
# --------------------------------------------------------------------- #

def test_manifest_shape(manifest):
    assert manifest["schema"] == "rates_ng1_run/substrate_manifest@1"
    assert manifest["file_count"] == 63
    assert len(manifest["files"]) == 63
    for name, rec in manifest["files"].items():
        assert len(rec["sha256"]) == 64
        int(rec["sha256"], 16)                      # well-formed hex
        assert rec["bytes"] > 0
        assert rec["rel_path"].startswith("raw_substrate/")
        # any credential parameter in a recorded URL must be the
        # REDACTED literal (V13 law)
        assert sub.redact(rec["source_url"]) == rec["source_url"]
        for marker in ("api_key=", "api_token="):
            if marker in rec["source_url"]:
                value = rec["source_url"].split(
                    marker, 1)[1].split("&")[0]
                assert value == "REDACTED"


def test_manifest_pin_families(manifest):
    files = manifest["files"]
    assert len([f for f in files
                if f.startswith("treasury_curve/")]) == 37
    assert len([f for f in files if f.startswith("fred/")]) == 7
    assert len([f for f in files if f.startswith("etp_eod/")]) == 9
    assert len([f for f in files if f.startswith("auctions/")]) == 10


@pytest.mark.parametrize("entry", [
    "treasury_curve/par_yields_2025.csv",
    "treasury_curve/par_yields_1990.csv",
    "fred/DGS10.json",
    "fred/CPIAUCSL.json",
    "etp_eod/TLT.US.json",
    "auctions/ta_ws_search_2025.json",
])
def test_raw_bytes_rehash_to_pin(manifest, entry):
    """Spot re-hash: present raw substrate bytes must equal their pin."""
    raw = os.path.join(WORKTREE, "research", "assets", "rates_ng1",
                       "raw_substrate", entry)
    if not os.path.isfile(raw):
        pytest.skip("raw substrate bytes archived (P-13); the committed "
                    "manifest is the surviving evidence")
    h = hashlib.sha256()
    with open(raw, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    assert h.hexdigest() == manifest["files"][entry]["sha256"]


# --------------------------------------------------------------------- #
# 3. census numbers (hand-computed)
# --------------------------------------------------------------------- #

def test_treasury_coverage_hand_computed():
    t = _load("p0_treasury_census.json")
    c = t["census"]
    # hand-computed: 5429 published curve days / 5660 Mon-Fri days in
    # [2005-01-01, 2026-09-11]  ==  0.959187  (>= 0.90 frozen floor)
    assert c["curve_days_in_window"] == 5429
    assert c["expected_business_days_window"] == 5660
    assert c["coverage_fraction"] == round(5429 / 5660, 6)
    assert c["coverage_fraction"] == pytest.approx(0.959187)
    assert t["floor"]["measured"] == c["coverage_fraction"]
    assert t["years_pulled"] == 37 and t["years_expected"] == 37
    assert t["failed_years"] == []
    assert t["floor"]["verdict"] == "PASS"


def test_treasury_tenor_columns_by_year():
    c = _load("p0_treasury_census.json")["census"]
    assert c["tenor_columns_by_year"]["1990"] == [
        "3 Mo", "6 Mo", "1 Yr", "2 Yr", "3 Yr", "5 Yr", "7 Yr",
        "10 Yr", "30 Yr"]
    assert c["tenor_columns_by_year"]["2005"] == [
        "1 Mo", "3 Mo", "6 Mo", "1 Yr", "2 Yr", "3 Yr", "5 Yr", "7 Yr",
        "10 Yr", "20 Yr"]
    assert c["tenor_columns_by_year"]["2026"] == [
        "1 Mo", "1.5 Month", "2 Mo", "3 Mo", "4 Mo", "6 Mo", "1 Yr",
        "2 Yr", "3 Yr", "5 Yr", "7 Yr", "10 Yr", "20 Yr", "30 Yr"]
    assert "30 Yr" not in c["tenor_columns_by_year"]["2005"]  # suspended
    assert "4 Mo" not in c["tenor_columns_by_year"]["1990"]   # 2008+


def test_treasury_year_windows():
    c = _load("p0_treasury_census.json")["census"]
    assert c["years"]["1990"]["rows"] == 250
    assert (c["years"]["1990"]["first_date"],
            c["years"]["1990"]["last_date"]) == (
        "1990-01-02", "1990-12-31")
    # 2005: 250 published days on a 260 Mon-Fri grid (holidays only)
    assert c["years"]["2005"]["rows"] == 250
    assert c["years"]["2005"]["expected_business_days"] == 260
    assert c["years"]["2005"]["curve_days_in_window"] == 250
    # 2026 partial year to the measured end
    assert c["years"]["2026"]["rows"] == 175
    assert c["years"]["2026"]["last_date"] == "2026-09-11"


def test_etp_census_hand_computed():
    e = _load("p0_etp_census.json")
    expected = {
        # (rows, first_date, last_date) -- TLT reproduces the Lead's
        # live probe (2002-07-26 -> 2026-09-11, 6071 rows)
        "TLT": (6071, "2002-07-26", "2026-09-11"),
        "IEF": (6071, "2002-07-26", "2026-09-11"),
        "IEI": (4948, "2007-01-11", "2026-09-11"),
        "SHY": (6071, "2002-07-26", "2026-09-11"),
    }
    for t, (rows, first, last) in expected.items():
        rec = e["tickers"][t]
        assert rec["status"] == "CENSORED"
        assert (rec["rows"], rec["first_date"],
                rec["last_date"]) == (rows, first, last)
        assert rec["corp_actions_cross_check"]["split_step_count"] == 0
        x = rec["corp_actions_cross_check"]
        assert x["max_rel_ratio_deviation"] <= 0.10
        assert rec["last_date"] >= "2026-09-01"      # through 2026-09
    assert e["floor"]["verdict"] == "PASS"


def test_fred_repin_hand_computed():
    f = _load("p0_fred_repin.json")
    assert f["expected_series_count"] == 7
    expected = {
        "DGS10": (16878, "1962-01-02", "2026-09-10"),
        "DGS2": (13118, "1976-06-01", "2026-09-10"),
        "DFII10": (6181, "2003-01-02", "2026-09-10"),
        "DFII5": (6181, "2003-01-02", "2026-09-10"),
        "T10YIE": (6182, "2003-01-02", "2026-09-11"),
        "T5YIE": (6182, "2003-01-02", "2026-09-11"),
        "CPIAUCSL": (3362, "1947-01-01", "2026-08-01"),
    }
    for sid, (rows, first, last) in expected.items():
        rec = f["series"][sid]
        assert rec["status"] == "PINNED"
        assert (rec["rows"], rec["first_date"],
                rec["last_date"]) == (rows, first, last)
    ov = f["cpiaucsl_overlap_verify"]
    # every inherited 2025-pin row reproduced value-identical
    assert ov["pinned_rows"] == 1962
    assert ov["overlap_rows_compared"] == 1962
    assert ov["overlap_value_equal"] == 1962
    assert ov["exact_key_rows"] == 1121
    assert ov["clip_edge_vintage_rows"] == 841
    assert 1121 + 841 == 1962                      # hand-computed split
    assert ov["drift_count"] == 0
    assert ov["zero_drift_on_overlap"] is True
    assert ov["verdict"] == "PASS"
    chain = f["dgs10_prior_pin_chain"]
    assert chain["verdict"] == "CITED"
    assert chain["prior_pin_digest"] == pa.V8_DGS10_SHA256_PIN
    assert chain["prior_manifest_digest"] == \
        pa.V8_STAGED_VINTAGED_MANIFEST_SHA256
    assert f["floor"]["verdict"] == "PASS"


def test_auction_census_hand_computed():
    a = _load("p0_auction_census.json")
    head = a["census_head"]
    assert a["failed_windows"] == []
    assert a["windows_pulled"] == list(range(2017, 2027))
    assert head["announcement_window"] == ["2018-01-01", "2026-09-12"]
    # hand-computed: 3555 events, Bill 2637 + Note 716 + Bond 202
    assert head["event_count"] == 3555
    assert head["events_by_security_type"] == {
        "Bill": 2637, "Note": 716, "Bond": 202}
    assert sum(head["events_by_security_type"].values()) == 3555
    assert head["event_count"] >= 150              # frozen floor
    assert (head["first_announcement"],
            head["last_announcement"]) == ("2018-01-04", "2026-09-10")
    events = a["census"]["events"]
    assert len(events) == 3555
    keys = {(e["cusip"], e["announcementDate"], e["auctionDate"])
            for e in events}
    assert len(keys) == 3555                       # dedupe invariant
    for e in events:
        assert "2018-01-01" <= e["announcementDate"] <= "2026-09-12"
        assert e["evidence"]["pdf_announcement"] or \
            e["evidence"]["xml_announcement"]
    assert a["floor"]["measured"] == 3555
    assert a["floor"]["verdict"] == "PASS"


# --------------------------------------------------------------------- #
# 4. canaries (each fabricated access must FAIL = be refused)
# --------------------------------------------------------------------- #

def test_canaries_all_refused():
    c = _load("p0_canaries.json")
    assert c["verdict"] == "PASS"
    by_name = {x["canary"]: x for x in c["canaries"]}
    assert set(by_name) == {
        "fabricated_curve_date", "fabricated_tenor_column",
        "never_existed_ticker"}
    assert all(x["verdict"] == "REFUSED_AS_EXPECTED"
               for x in c["canaries"])
    assert by_name["fabricated_curve_date"]["probe"] == "2025-11-31"
    assert "UnknownCurveDate" in by_name["fabricated_curve_date"]["observed"]
    assert by_name["fabricated_tenor_column"]["probe"] == "13 Mo"
    assert "UnknownTenor" in \
        by_name["fabricated_tenor_column"]["observed"]
    assert "404" in by_name["never_existed_ticker"]["observed"]


# --------------------------------------------------------------------- #
# 5. adoption + shadow parity
# --------------------------------------------------------------------- #

def test_adoption_all_entries_via_plane(gate):
    ad = gate["sections"]["adoption"]
    assert ad["frozen_entry_count"] == 63
    assert len(ad["entries"]) == 63
    assert all(r["verdict"] == "PASS" for r in ad["entries"].values())
    # every curve entry went through the frozen query surface
    curve_entries = [k for k in ad["entries"]
                     if k.startswith("treasury_curve/")]
    assert len(curve_entries) == 37
    assert all(ad["entries"][k]["query_verdict"] == "FROZEN_QUERY_SUCCESS"
               for k in curve_entries)


def test_shadow_parity_digest_equality():
    p = _load("p0_shadow_parity.json")
    assert len(p["records"]) == 9
    for r in p["records"]:
        assert r["digest_identical"] is True
        assert r["plane_sha256"] == r["manifest_pin_sha256"] \
            == r["direct_sha256"]
    by_entry = {r["entry"]: r for r in p["records"]}
    # pilot row counts must equal the census row counts (window
    # equality plane-vs-direct)
    census = _load("p0_treasury_census.json")["census"]["years"]
    for year in (1990, 2005, 2016, 2025, 2026):
        rec = by_entry[f"treasury_curve/par_yields_{year}.csv"]
        assert rec["direct_row_count"] == census[str(year)]["rows"]
    assert by_entry["etp_eod/TLT.US.json"]["direct_row_count"] == 6071
    assert by_entry["fred/DGS10.json"]["direct_row_count"] == 16878
    assert by_entry["auctions/ta_ws_search_2025.json"][
        "direct_row_count"] == 441
    assert p["digest_equality_all"] is True
    assert p["verdict"] == "PASS"


# --------------------------------------------------------------------- #
# 6. adapter fail-closed behavior (tmp fixtures, no network)
# --------------------------------------------------------------------- #

FIXTURE_CURVE_CSV = (
    b'Date,"3 Mo","10 Yr"\r\n'
    b'"01/02/2025",4.35,4.57\r\n'
    b'"01/03/2025",4.33,4.56\r\n'
)


def test_adapter_happy_path_and_parse(tmp_path):
    plane = _tmp_plane(tmp_path,
                       {"treasury_curve/par_yields_2025.csv":
                        FIXTURE_CURVE_CSV})
    res = plane.consume_via_plane("treasury_curve/par_yields_2025.csv")
    assert res["sha256_measured"] == res["sha256_pinned"]
    assert res["authority"] == "frozen_cycle_set:R5:treasury-par-yield-curve"
    rows = res["rows"]
    # hand-computed parse: ISO dates + tenor columns preserved
    assert [r["date"] for r in rows] == ["2025-01-02", "2025-01-03"]
    assert rows[0]["3 Mo"] == "4.35" and rows[1]["10 Yr"] == "4.56"
    row = plane.curve_row("2025-01-03")
    assert plane.curve_tenor("2025-01-03", "10 Yr") == "4.56"
    assert row["date"] == "2025-01-03"


def test_adapter_refuses_entry_outside_frozen_set(tmp_path):
    plane = _tmp_plane(tmp_path, {"etp_eod/TLT.US.json": b"[]"})
    with pytest.raises(pa.PlaneConsumptionRefused):
        plane.consume_via_plane("etp_eod/ZZFABRICATED.US.json")


def test_adapter_blocked_on_one_byte_drift(tmp_path):
    data = FIXTURE_CURVE_CSV
    plane = _tmp_plane(tmp_path,
                       {"treasury_curve/par_yields_2025.csv": data})
    # flip the last byte of the raw fixture
    raw = tmp_path / "raw" / "treasury_curve" / "par_yields_2025.csv"
    flipped = data[:-1] + bytes([data[-1] ^ 0x01])
    raw.write_bytes(flipped)
    with pytest.raises(pa.PlaneDataBlocked) as excinfo:
        plane.consume_via_plane("treasury_curve/par_yields_2025.csv")
    assert excinfo.value.reason == "BLOCKED_DATA"


def test_adapter_malformed_curve_row_blocked(tmp_path):
    bad = b'Date,"10 Yr"\r\n"01/02/2025",4.57\r\n"NOT-A-DATE",4.56\r\n'
    plane = _tmp_plane(tmp_path,
                       {"treasury_curve/par_yields_2025.csv": bad})
    with pytest.raises(pa.PlaneDataBlocked):
        plane.consume_via_plane("treasury_curve/par_yields_2025.csv")


def test_fabricated_curve_date_refused(tmp_path):
    plane = _tmp_plane(tmp_path,
                       {"treasury_curve/par_yields_2025.csv":
                        FIXTURE_CURVE_CSV})
    # 2025-11-31: November has 30 days -- this date never existed
    with pytest.raises(pa.UnknownCurveDate):
        plane.curve_row("2025-11-31")
    # outside the pinned 1990..2026 span
    with pytest.raises(pa.UnknownCurveDate):
        plane.curve_row("1989-12-29")


def test_fabricated_tenor_refused(tmp_path):
    plane = _tmp_plane(tmp_path,
                       {"treasury_curve/par_yields_2025.csv":
                        FIXTURE_CURVE_CSV})
    with pytest.raises(pa.UnknownTenor):
        plane.curve_tenor("2025-01-02", "13 Mo")


def test_never_existed_ticker_refused_locally():
    """The frozen ETP set (TLT/IEF/IEI/SHY) is enforced before any
    network surface: a never-existed ticker is refused locally."""
    plane = pa.RatesNG1Plane(MANIFEST_PATH)
    with pytest.raises(pa.UnknownTicker):
        plane.etp_rows("ZZTREASURYNOPE9")


def test_cpiaucsl_entry_requires_platform_authority(tmp_path):
    """The FRED CPIAUCSL entry is consumed under the platform-v3
    authority id: a non-GRANTED registry verdict must refuse."""
    plane = _tmp_plane(tmp_path, {"fred/CPIAUCSL.json": b"[]"})
    # the committed journal grants S2:fred-keyed-vintage-classes, so the
    # real plane passes the gate; force a refusal via a fake journal
    # path that carries no such series
    empty_journal = tmp_path / "journal.jsonl"
    empty_journal.write_text("")
    strict = pa.RatesNG1Plane(
        os.path.join(str(tmp_path), "manifest.json"),
        str(tmp_path / "raw"),
        registry_journal=str(empty_journal))
    with pytest.raises(pa.PlaneConsumptionRefused):
        strict.consume_via_plane("fred/CPIAUCSL.json")
    # the real journal carries the GRANTED verdict
    assert plane.platform_verdict(
        pa.FRED_AUTHORITY_SERIES) == "GRANTED"


def test_shared_cads_cpiaucsl_pin_resolves_readonly():
    """The inherited S2 CADS pin resolves and re-hashes to its own
    address (content-addressed integrity) -- read-only store use."""
    res = pa.resolve_inherited_cpiaucsl_pin()
    assert res["sha256_measured"] == pa.CPIAUCSL_CADS_PIN
    assert res["rows"] == 1962


# --------------------------------------------------------------------- #
# 7. hand-computed census math primitives
# --------------------------------------------------------------------- #

def test_expected_business_days_hand_computed():
    # a clean Mon-Fri week
    assert sub.expected_business_days("2026-09-07", "2026-09-11") == 5
    # Fri..Sat: only the Friday counts
    assert sub.expected_business_days("2026-09-11", "2026-09-12") == 1
    # 2025 full year: 365 days, 261 weekdays (hand-computed)
    assert sub.expected_business_days("2025-01-01", "2025-12-31") == 261
    # the census window: 5660 weekdays (hand-computed total)
    assert sub.expected_business_days("2005-01-01", "2026-09-11") == 5660


def test_split_steps_hand_computed():
    raw = [{"date": "2025-01-02", "close": 100.0},
           {"date": "2025-01-03", "close": 50.0},
           {"date": "2025-01-06", "close": 51.0}]
    adj = [{"date": "2025-01-02", "close": 100.0},
           {"date": "2025-01-03", "close": 100.0},
           {"date": "2025-01-06", "close": 102.0}]
    out = sub.split_steps(raw, adj)
    # 2:1 split on 2025-01-03 shows as one step
    assert out["split_step_count"] == 1
    assert out["split_steps"][0]["date"] == "2025-01-03"
    # a no-split series has zero steps (the measured ETP census case)
    flat = sub.split_steps(
        [{"date": "2025-01-02", "close": 100.0},
         {"date": "2025-01-03", "close": 101.0}],
        [{"date": "2025-01-02", "close": 100.0},
         {"date": "2025-01-03", "close": 101.0}])
    assert flat["split_step_count"] == 0


def test_overlap_verify_hand_computed_drift_detection():
    pinned = [
        {"date": "2025-01-01", "realtime_start": "2017-01-01",
         "realtime_end": "2025-08-01", "value": "21.48"},
        {"date": "2025-02-01", "realtime_start": "2020-03-15",
         "realtime_end": "2025-08-01", "value": "170.1"},
    ]
    # fresh carries the same values under different realtime windows
    fresh_ok = [
        {"date": "2025-01-01", "realtime_start": "2016-12-15",
         "realtime_end": "2026-09-01", "value": "21.48"},
        {"date": "2025-02-01", "realtime_start": "2020-03-15",
         "realtime_end": "2026-09-01", "value": "170.1"},
    ]
    ok = sub.fred_overlap_verify(pinned, fresh_ok)
    assert ok["zero_drift_on_overlap"] is True
    assert ok["clip_edge_vintage_rows"] == 1   # clipped first vintage
    assert ok["exact_key_rows"] == 1
    # a genuine revision breaks zero-drift
    fresh_drift = [dict(fresh_ok[0]),
                   {"date": "2025-02-01", "realtime_start": "2020-03-15",
                    "realtime_end": "2026-09-01", "value": "171.2"}]
    bad = sub.fred_overlap_verify(pinned, fresh_drift)
    assert bad["zero_drift_on_overlap"] is False
    assert bad["drift_count"] == 1
    assert bad["mismatches_sample"][0]["pinned"] == "170.1"
    assert bad["mismatches_sample"][0]["fresh"] == "171.2"


def test_delisted_census_hand_computed_fixture():
    entries = [
        {"Code": "AAA", "Name": "A Treasury ETF", "Type": "FUND"},
        {"Code": "BBB", "Name": "Plain Corp", "Type": "Common Stock"},
        {"Code": "CCC", "Name": "", "Type": "FUND"},
    ]
    out = sub.delisted_census(entries)
    assert out["total_delisted_symbols"] == 3
    assert out["entries_with_name"] == 2
    assert out["fund_type_count"] == 2
    assert out["treasury_named_count"] == 1
    assert out["treasury_named_sample"][0]["code"] == "AAA"
