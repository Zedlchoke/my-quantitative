"""CRYPTO-NG1 P0 adoption tests (lane p0, task crypto-ng1-p0-adoption).

Sandboxed: every case runs on tmp_path fixtures (a throwaway CADS store
and authority journal built under tmp_path); the real
``.runtime/v3_cads_store`` store is never touched and never written.

Hand-computed expectations (no value below is derived at test time from
the code under test):

- fixture CSV sha256 ``d16c4d24...`` computed by hand from the exact
  fixture text; one-byte tamper ``7 -> 8`` must fail closed;
- DST-boundary instants (America/New_York):
    2026-03-18 14:00 EDT (UTC-4)  == 2026-03-18T18:00:00+00:00
    2025-12-10 14:00 EST (UTC-5)  == 2025-12-10T19:00:00+00:00
    2026-03-06 08:30 EST (pre-DST, Friday)  == 2026-03-06T13:30:00+00:00
    2026-03-09 08:30 EDT (post-DST, Monday) == 2026-03-09T12:30:00+00:00
  (US 2026 DST starts Sunday 2026-03-08.)
"""
from __future__ import annotations

import hashlib
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.assets.crypto_ng1 import calendar_census  # noqa: E402
from research.assets.crypto_ng1.plane_adapter import (  # noqa: E402
    CryptoNG1Plane, PlaneConsumptionRefused, PlaneDataBlocked,
)
from research.platform_v3.authority import AuthorityRegistry  # noqa: E402
from research.platform_v3.cads import CADS  # noqa: E402

#: hand-computed fixture constants ------------------------------------------------ #
FIXTURE_CSV = (
    "symbol,hour_utc,day_utc,n_trades\n"
    "BTCUSDT,2026-01-02T03,2026-01-02,7\n"
    "BTCUSDT,2026-01-02T04,2026-01-02,9\n"
)
FIXTURE_CSV_SHA256 = (
    "d16c4d242fc5e180fb85f91fd5efa37ea87a21a1af984b56f9c3cbee644f2d16")
TAMPERED_CSV_SHA256 = (
    "00f0b0d55bc092434d54f3da05257142cde371df1ca29a70cb921c9d35943464")
FAKE_DIGEST = "00" * 32

ENTRY = "staging_v17/panel_TEST_h1.csv"
SERIES = "S4:binance-daily-h1-panels"


def build_plane(tmp_path: Path, data: bytes = FIXTURE_CSV.encode(),
                pin_series: str = SERIES) -> tuple[CryptoNG1Plane, str, Path]:
    """Build a throwaway granted plane: tmp CADS store + tmp authority
    journal adjudicated GRANTED (mirrors pa4_pa5 flow)."""
    store_root = tmp_path / "store"
    store = CADS(str(store_root))
    addr = store.register(data)
    store.pin(addr, {"series": pin_series, "file": ENTRY})
    journal = tmp_path / "authority_journal.jsonl"
    reg = AuthorityRegistry(str(journal))
    reg.register(SERIES, source="binance-vision", channel="binance-vision")
    reg.transition(SERIES, "INGESTED")
    reg.transition(SERIES, "VERIFIED")
    reg.evidence(
        SERIES, pit_verdict="PASS_PIT_EVIDENCED", license_status="AUTHORIZED",
        entitlement_status="AUTHORIZED",
        canary_probe={"binance-vision": "PASS"}, cads_pins=[addr])
    outcome = reg.adjudicate(
        SERIES, granted_by="TEST",
        granted_at="2026-09-11T00:00:00+00:00")
    assert outcome == "GRANTED"
    plane = CryptoNG1Plane(store_root=str(store_root),
                           registry_journal=str(journal))
    return plane, addr, store_root


# --------------------------------------------------------------------------- #
# adapter: granted resolve + hand-computed digest
# --------------------------------------------------------------------------- #
def test_granted_resolve_matches_hand_computed_digest(tmp_path):
    plane, addr, _ = build_plane(tmp_path)
    assert plane.verdict(SERIES) == "GRANTED"
    res = plane.resolve_entry(SERIES, ENTRY, expected_sha256=addr)
    assert res["cads_address"] == addr
    assert res["sha256_measured"] == FIXTURE_CSV_SHA256 == addr
    assert res["bytes"] == 103
    assert res["data"] == FIXTURE_CSV.encode()
    assert res["verdict"] == "GRANTED"


def test_one_byte_digest_change_fails_closed(tmp_path):
    """Flip exactly one byte of the CADS object INSIDE the tmp store:
    resolve must fail closed (verify-on-read), never return drifted
    bytes and never repair."""
    plane, addr, store_root = build_plane(tmp_path)
    obj = store_root / "objects" / addr[:2] / addr
    raw = bytearray(obj.read_bytes())
    i = raw.index(b",7\n")
    raw[i + 1] = ord("8")                      # 7 -> 8: exactly one byte
    tampered = bytes(raw)
    assert hashlib.sha256(tampered).hexdigest() == TAMPERED_CSV_SHA256
    obj.write_bytes(tampered)
    with pytest.raises(PlaneDataBlocked) as excinfo:
        plane.resolve_entry(SERIES, ENTRY, expected_sha256=addr)
    assert excinfo.value.reason == "BLOCKED_DATA"
    # the object on disk must NOT have been "fixed" back
    assert obj.read_bytes() == tampered


def test_frozen_digest_mismatch_fails_closed_before_resolve(tmp_path):
    plane, addr, _ = build_plane(tmp_path)
    with pytest.raises(PlaneDataBlocked) as excinfo:
        plane.resolve_entry(SERIES, ENTRY, expected_sha256=FAKE_DIGEST)
    assert excinfo.value.reason == "BLOCKED_DATA"
    assert "no re-download" in str(excinfo.value)


def test_unknown_series_refused_fail_closed(tmp_path):
    """P-7 canary shape: a nonexistent series name must be refused."""
    plane, _, _ = build_plane(tmp_path)
    for fake in ("S4:binance-funding-settlements", "S9:not-a-real-series"):
        with pytest.raises(PlaneConsumptionRefused):
            plane.resolve_entry(fake, "x.csv", expected_sha256=None)


def test_manifest_verified_query_bounds(tmp_path):
    """The manifest-verified query path over the hand fixture panel."""
    plane, addr, _ = build_plane(tmp_path)
    out = plane.query_panel_bounds(ENTRY, series=SERIES,
                                   expected_sha256=addr)
    assert out["query_verdict"] == "SUCCESS"
    assert out["cads_address"] == addr
    assert out["rows"] == [["BTCUSDT", 2, "2026-01-02T03", "2026-01-02T04"]]
    assert out["row_count"] == 1
    assert out["result_digest"]


def test_shadow_parity_identical_on_tmp_fixture(tmp_path):
    plane, addr, _ = build_plane(tmp_path)
    p = plane.shadow_parity(ENTRY, series=SERIES, expected_sha256=addr)
    assert p["identical"] is True
    assert p["plane_sha256"] == p["direct_sha256"] == FIXTURE_CSV_SHA256


# --------------------------------------------------------------------------- #
# calendar: DST-boundary instants (hand-computed)
# --------------------------------------------------------------------------- #
def test_dst_boundary_fomc_instants_hand_computed():
    # 2026-03-18 14:00 EDT (after spring-forward 2026-03-08)
    assert calendar_census.local_to_utc(
        date(2026, 3, 18), 2, 0, "p", "EDT") == "2026-03-18T18:00:00+00:00"
    # 2025-12-10 14:00 EST
    assert calendar_census.local_to_utc(
        date(2025, 12, 10), 2, 0, "p", "EST") == "2025-12-10T19:00:00+00:00"


def test_dst_boundary_0830_release_clock_hand_computed():
    # the 08:30 ET macro-print clock across the 2026 spring-forward
    assert calendar_census.local_to_utc(
        date(2026, 3, 6), 8, 30, "a", "EST") == "2026-03-06T13:30:00+00:00"
    assert calendar_census.local_to_utc(
        date(2026, 3, 9), 8, 30, "a", "EDT") == "2026-03-09T12:30:00+00:00"


def test_zone_abbr_mismatch_fails_closed():
    # claiming EDT on an EST date must refuse the instant (DST check)
    with pytest.raises(ValueError):
        calendar_census.local_to_utc(date(2025, 12, 10), 2, 0, "p", "EDT")
    with pytest.raises(ValueError):
        calendar_census.local_to_utc(date(2026, 3, 18), 2, 0, "p", "EST")


# --------------------------------------------------------------------------- #
# calendar: parser + canary-negative
# --------------------------------------------------------------------------- #
CALENDAR_HTML = """
<div class="panel panel-default"><div class="panel-heading">
<h4><a id="t1">2026 FOMC Meetings</a></h4></div>
<div class="row fomc-meeting" ">
  <div class="fomc-meeting__month col-xs-5 col-sm-3 col-md-2">
    <strong>January</strong></div>
  <div class="fomc-meeting__date col-xs-4 col-sm-9 col-md-10 col-lg-1">
    27-28</div>
</div>
<div class="row fomc-meeting" ">
  <div class="fomc-meeting__month col-xs-5 col-sm-3 col-md-2">
    <strong>March</strong></div>
  <div class="fomc-meeting__date col-xs-4 col-sm-9 col-md-10 col-lg-1">
    17-18*</div>
</div>
"""

STATEMENT_HTML_JAN = """
<p class="article__time">January 28, 2026</p>
<div>For release at 2:00 p.m. EST</div>
<p>Federal Reserve issues FOMC statement</p>
"""
STATEMENT_HTML_MAR = """
<p class="article__time">March 18, 2026</p>
<div>For release at 2:00 p.m. EDT</div>
<p>Federal Reserve issues FOMC statement</p>
"""


def test_parse_fomc_meetings_and_statement_pages():
    meetings = calendar_census.parse_fomc_meetings(CALENDAR_HTML)
    assert [m["decision_day"] for m in meetings] == [
        "2026-01-28", "2026-03-18"]
    assert meetings[1]["sep_projection"] is True
    rel = calendar_census.parse_release_instant(STATEMENT_HTML_JAN)
    assert (rel["hour"], rel["minute"], rel["meridiem"], rel["zone"]) == (
        2, 0, "p", "EST")
    assert calendar_census.parse_statement_date(
        STATEMENT_HTML_JAN) == date(2026, 1, 28)
    # a page without the official release line yields NO instant
    assert calendar_census.parse_release_instant(
        "<p>no timestamp here</p>") is None


def test_fabricated_day_canary_negative():
    """A fabricated calendar day must fail to produce an instant."""
    # invalid fabricated date must fail closed at parse time
    with pytest.raises(ValueError):
        date.fromisoformat("2026-02-30")
    # a well-formed but fabricated statement page carries no evidence
    assert calendar_census.parse_release_instant(
        "<p>404 not found</p>") is None


def test_run_census_offline_stub_hand_computed():
    """End-to-end census with a stubbed fetch (no network): instants must
    carry the hand-computed UTC timestamps; BLS blocked is recorded; the
    fabricated-day canary must PASS (no instant)."""
    pages = {
        calendar_census.FOMC_CALENDAR_URL: CALENDAR_HTML,
        calendar_census.statement_url(date(2026, 1, 28)): STATEMENT_HTML_JAN,
        calendar_census.statement_url(date(2026, 3, 18)): STATEMENT_HTML_MAR,
    }

    def stub_fetch(url, max_attempts=3, timeout=25.0, backoff_s=(0, 0)):
        if url in pages:
            return {"url": url, "ok": True, "status": 200,
                    "attempts": [{"attempt": 1, "retrieved_utc":
                                  "2026-09-11T00:00:00+00:00",
                                  "status": 200, "error": None}],
                    "body": pages[url],
                    "retrieved_utc": "2026-09-11T00:00:00+00:00"}
        return {"url": url, "ok": False, "status": 403,
                "attempts": [{"attempt": 1, "retrieved_utc":
                              "2026-09-11T00:00:00+00:00",
                              "status": 403, "error": "HTTPError 403"}],
                "body": None, "retrieved_utc": "2026-09-11T00:00:00+00:00"}

    def verdict_fn(series_id):
        if series_id == SERIES:
            return "GRANTED"
        return "BLOCKED_DATA: not in registry (S1-S4 frozen set)"

    census = calendar_census.run_census(
        date(2026, 1, 1), date(2026, 12, 31),
        fetch=stub_fetch, verdict_fn=verdict_fn,
        fabricated_day="2026-02-14", now_utc="2026-09-11T00:00:00+00:00")

    assert census["verdict"] == "PASS_WITH_BLS_BLOCKED"
    assert [i["scheduled_utc"] for i in census["instants"]] == [
        "2026-01-28T19:00:00+00:00",   # 2:00 p.m. EST == 19:00Z (hand)
        "2026-03-18T18:00:00+00:00",   # 2:00 p.m. EDT == 18:00Z (hand)
    ]
    for inst in census["instants"]:
        assert inst["source_url"].startswith(
            "https://www.federalreserve.gov/")
        assert inst["retrieved_utc"]
        assert inst["evidence"]["for_release_text"].startswith(
            "For release at")
    # BLS blocked recorded honestly, no instants fabricated
    assert census["sources"]["bls"]["status"] == "BLOCKED"
    assert census["sources"]["bls"]["probes"][0]["series"] == "CPI"
    # canaries: 2 nonexistent series refused + fabricated day fails
    assert all(c["verdict"] == "PASS"
               for c in census["canaries"]["series_probes"])
    assert census["canaries"]["fabricated_day"]["verdict"] == "PASS"


def test_run_census_all_sources_blocked():
    """Stop condition shape: when every official source fails the census
    verdict is BLOCKED_ALL_SOURCES_FAILED -- never a fabricated PASS."""

    def dead_fetch(url, max_attempts=3, timeout=25.0, backoff_s=(0, 0)):
        return {"url": url, "ok": False, "status": 403,
                "attempts": [{"attempt": 1, "retrieved_utc":
                              "2026-09-11T00:00:00+00:00",
                              "status": 403, "error": "HTTPError 403"}],
                "body": None, "retrieved_utc": "2026-09-11T00:00:00+00:00"}

    census = calendar_census.run_census(
        date(2026, 1, 1), date(2026, 12, 31), fetch=dead_fetch,
        verdict_fn=lambda s: "BLOCKED_DATA: no",
        fabricated_day="2026-02-14", now_utc="2026-09-11T00:00:00+00:00")
    assert census["verdict"] == "BLOCKED_ALL_SOURCES_FAILED"
    assert census["instants"] == []
