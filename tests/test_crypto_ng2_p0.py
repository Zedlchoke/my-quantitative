"""CRYPTO-NG2 P0 census tests (lane p0, task crypto-ng2-p0-census).

Sandboxed and network-free: BLS schedule fixtures are HAND-BUILT files
created under ``/tmp`` by this module (packet: "fixtures /tmp tu tao");
nothing fetches, nothing touches the real CADS store.

Hand-computed expectations (no value below is derived at test time from
the code under test).  Weekday ground truth for the fixture rows:

- 2026-01-02 Friday, 2026-01-15 Thursday, 2026-01-29 Thursday
- 2026-02-13 Friday, 2026-03-06 Friday (pre-DST), 2026-03-11 Wednesday
  (post-DST; US 2026 spring-forward is Sunday 2026-03-08)
- 2026-04-03 Friday, 2026-06-13 Saturday, 2026-07-03 Friday,
  2026-07-15 Wednesday, 2026-08-07 Friday
- 2025-06-12 Thursday, 2025-09-16 Tuesday (in-window), 2026-10-14
  Wednesday (after window end 2026-08-21)

DST clock arithmetic (America/New_York, 8:30 print clock):
- 08:30 EST (UTC-5)  == 13:30Z   (winter / pre-spring-forward)
- 08:30 EDT (UTC-4)  == 12:30Z   (summer / post-spring-forward)
- 08:30 EST on 2026-11-06 == 13:30Z (after 2026-11-01 fall-back)
- 12:30 p.m. ET == 17:30Z; 12:15 a.m. ET == 05:15Z (meridiem edges)
"""
from __future__ import annotations

import sys
import tempfile
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.assets.crypto_ng2 import bls_census  # noqa: E402

WINDOW = (date(2025, 8, 22), date(2026, 8, 21))

# --------------------------------------------------------------------- #
# hand-built /tmp fixtures                                                #
# --------------------------------------------------------------------- #
_CPI_ROWS = """
<tr><td>Thursday</td><td>January 15, 2026</td><td>8:30 AM</td>
    <td>Consumer Price Index for December 2025</td></tr>
<tr><td>Friday</td><td>March 6, 2026</td><td>8:30 AM</td>
    <td>Consumer Price Index for February 2026</td></tr>
<tr><td>Wednesday</td><td>March 11, 2026</td><td>8:30 AM</td>
    <td>Consumer Price Index for February 2026</td></tr>
<tr><td>Wednesday</td><td>July 15, 2026</td><td>8:30 AM</td>
    <td>Consumer Price Index for June 2026</td></tr>
<tr><td>Thursday</td><td>January 29, 2026</td><td>8:30 AM EDT</td>
    <td>Consumer Price Index for December 2025</td></tr>
<tr><td>Friday</td><td>February 13, 2026</td><td>--</td>
    <td>Consumer Price Index for January 2026</td></tr>
<tr><td>Monday</td><td>April 3, 2026</td><td>8:30 AM</td>
    <td>Consumer Price Index for March 2026</td></tr>
<tr><td>Saturday</td><td>June 13, 2026</td><td>8:30 AM</td>
    <td>Consumer Price Index for May 2026</td></tr>
<tr><td>Tuesday</td><td>September 16, 2025</td><td>8:30 AM</td>
    <td>Producer Price Index for August 2025</td></tr>
<tr><td>Thursday</td><td>June 12, 2025</td><td>8:30 AM</td>
    <td>Consumer Price Index for May 2025</td></tr>
<tr><td>Wednesday</td><td>October 14, 2026</td><td>8:30 AM</td>
    <td>Consumer Price Index for September 2026</td></tr>
"""
_NFP_ROWS = """
<tr><td>Friday</td><td>January 2, 2026</td><td>8:30 AM</td>
    <td>Employment Situation for December 2025</td></tr>
<tr><td>Friday</td><td>July 3, 2026</td><td>8:30 AM</td>
    <td>Employment Situation for June 2026</td></tr>
<tr><td>Friday</td><td>August 7, 2026</td><td>8:30 AM</td>
    <td>Employment Situation for July 2026</td></tr>
"""


def _page(title: str, rows: str) -> str:
    return (
        "<html><head><title>" + title + "</title></head><body>"
        "<h3>2026 Schedule</h3>"
        '<table class="regular-table" summary="fixture">'
        "<thead><tr><th scope=\"col\">Day</th><th scope=\"col\">Date</th>"
        "<th scope=\"col\">Time</th><th scope=\"col\">Release</th></tr>"
        "</thead><tbody>" + rows + "</tbody></table></body></html>\n")


@pytest.fixture(scope="module")
def fixture_dir():
    """Self-created /tmp fixture directory (packet: fixtures /tmp tu tao)."""
    d = Path(tempfile.mkdtemp(prefix="crypto_ng2_p0_fixtures_",
                              dir="/tmp"))
    (d / "bls_cpi_schedule_fixture.htm").write_text(
        _page("CPI Release Schedule (fixture)", _CPI_ROWS), encoding="utf-8")
    (d / "bls_nfp_schedule_fixture.htm").write_text(
        _page("Employment Situation Release Schedule (fixture)", _NFP_ROWS),
        encoding="utf-8")
    return d


@pytest.fixture(scope="module")
def cpi_html(fixture_dir) -> str:
    return (fixture_dir / "bls_cpi_schedule_fixture.htm").read_text(
        encoding="utf-8")


@pytest.fixture(scope="module")
def nfp_html(fixture_dir) -> str:
    return (fixture_dir / "bls_nfp_schedule_fixture.htm").read_text(
        encoding="utf-8")


def _stub_fetch(pages: dict):
    def fetch(url, max_attempts=3, timeout=25.0, backoff_s=(0, 0)):
        if url in pages:
            return {"url": url, "ok": True, "status": 200,
                    "attempts": [{"attempt": 1,
                                  "retrieved_utc": "2026-09-11T00:00:00+00:00",
                                  "status": 200, "error": None}],
                    "body": pages[url],
                    "retrieved_utc": "2026-09-11T00:00:00+00:00"}
        return {"url": url, "ok": False, "status": 403,
                "attempts": [{"attempt": 1,
                              "retrieved_utc": "2026-09-11T00:00:00+00:00",
                              "status": 403, "error": "HTTPError 403"}],
                "body": None, "retrieved_utc": "2026-09-11T00:00:00+00:00"}
    return fetch


def _verdict_fn(series_id):
    if series_id == "S4:binance-daily-h1-panels":
        return "GRANTED"
    return "BLOCKED_DATA: not in registry (S1-S4 frozen set)"


# --------------------------------------------------------------------- #
# parser instants: DST-boundary 8:30 ET clock (hand-computed)            #
# --------------------------------------------------------------------- #
def test_bls_830_clock_dst_hand_computed():
    # winter (EST, UTC-5)
    assert bls_census.local_to_utc(
        date(2026, 1, 15), 8, 30, "a", "ET") == "2026-01-15T13:30:00+00:00"
    # pre-spring-forward Friday 2026-03-06 (EST)
    assert bls_census.local_to_utc(
        date(2026, 3, 6), 8, 30, "a", "EST") == "2026-03-06T13:30:00+00:00"
    # post-spring-forward Wednesday 2026-03-11 (EDT)
    assert bls_census.local_to_utc(
        date(2026, 3, 11), 8, 30, "a", "EDT") == "2026-03-11T12:30:00+00:00"
    # after 2026-11-01 fall-back (EST again)
    assert bls_census.local_to_utc(
        date(2026, 11, 6), 8, 30, "a", "EST") == "2026-11-06T13:30:00+00:00"


def test_meridiem_edges_hand_computed():
    assert bls_census.local_to_utc(
        date(2026, 1, 15), 12, 30, "p", "ET") == "2026-01-15T17:30:00+00:00"
    assert bls_census.local_to_utc(
        date(2026, 1, 15), 12, 15, "a", "ET") == "2026-01-15T05:15:00+00:00"


def test_parser_cpi_instants_dst_hand_computed(cpi_html):
    instants, dropped, in_window = bls_census.parse_bls_instants(
        cpi_html, "CPI", "https://www.bls.gov/schedule/news_release/cpi.htm",
        "2026-09-11T00:00:00+00:00", "stubbed_fetch", *WINDOW)
    # the four clean rows, in calendar order, hand-computed UTC
    assert [i["scheduled_utc"] for i in instants] == [
        "2026-01-15T13:30:00+00:00",   # 8:30 ET winter -> 13:30Z
        "2026-03-06T13:30:00+00:00",   # 8:30 EST pre-spring-forward
        "2026-03-11T12:30:00+00:00",   # 8:30 EDT post-spring-forward
        "2026-07-15T12:30:00+00:00",   # 8:30 ET summer -> 12:30Z
    ]
    assert [i["series"] for i in instants] == [
        "US-MACRO/BLS_CPI_RELEASE"] * 4
    for inst in instants:
        assert inst["scheduled_local"].endswith("8:30 a.m. ET")
        assert inst["source_url"] == (
            "https://www.bls.gov/schedule/news_release/cpi.htm")
        assert inst["retrieved_utc"] == "2026-09-11T00:00:00+00:00"
        assert inst["method"] == "stubbed_fetch"
        # zone defaulted per the plan 8:30 ET standard, never silently
        assert inst["evidence"]["zone"] == "ET"
        assert inst["evidence"]["zone_source"].startswith("defaulted")
    # 9 rows fall inside the window: 4 instants + 5 dropped rows below
    assert in_window == 9
    assert len(dropped) == 5


def test_parser_nfp_instants_hand_computed(nfp_html):
    instants, dropped, in_window = bls_census.parse_bls_instants(
        nfp_html, "NFP", "https://www.bls.gov/schedule/news_release/empsit.htm",
        "2026-09-11T00:00:00+00:00", "stubbed_fetch", *WINDOW)
    assert [i["scheduled_utc"] for i in instants] == [
        "2026-01-02T13:30:00+00:00",   # Friday 8:30 ET winter
        "2026-07-03T12:30:00+00:00",   # Friday 8:30 ET summer
        "2026-08-07T12:30:00+00:00",   # Friday 8:30 ET summer
    ]
    assert all(i["series"] == "US-MACRO/BLS_EMPLOYMENT_SITUATION_RELEASE"
               for i in instants)
    assert dropped == [] and in_window == 3


# --------------------------------------------------------------------- #
# fail-closed: every malformed row drops, never infers                   #
# --------------------------------------------------------------------- #
def test_zone_abbr_mismatch_row_dropped_fail_closed(cpi_html):
    _, dropped, _ = bls_census.parse_bls_instants(
        cpi_html, "CPI", "u", None, "stubbed_fetch", *WINDOW)
    zones = [d for d in dropped if d["date"] == "2026-01-29"]
    assert len(zones) == 1
    assert "fail-closed" in zones[0]["reason"]
    assert "EDT" in zones[0]["reason"]


def test_missing_time_row_dropped_never_inferred(cpi_html):
    _, dropped, _ = bls_census.parse_bls_instants(
        cpi_html, "CPI", "u", None, "stubbed_fetch", *WINDOW)
    notime = [d for d in dropped if d["date"] == "2026-02-13"]
    assert len(notime) == 1
    assert "never inferred" in notime[0]["reason"]


def test_weekday_mismatch_row_dropped(cpi_html):
    # 2026-04-03 is a Friday; the fixture row claims Monday
    _, dropped, _ = bls_census.parse_bls_instants(
        cpi_html, "CPI", "u", None, "stubbed_fetch", *WINDOW)
    wd = [d for d in dropped if d["date"] == "2026-04-03"]
    assert len(wd) == 1
    assert "three-way check failed" in wd[0]["reason"]


def test_weekend_row_dropped(cpi_html):
    _, dropped, _ = bls_census.parse_bls_instants(
        cpi_html, "CPI", "u", None, "stubbed_fetch", *WINDOW)
    we = [d for d in dropped if d["date"] == "2026-06-13"]
    assert len(we) == 1
    assert "weekend" in we[0]["reason"]


def test_wrong_release_row_dropped(cpi_html):
    # a Producer Price Index row on the CPI page must not yield a CPI instant
    _, dropped, _ = bls_census.parse_bls_instants(
        cpi_html, "CPI", "u", None, "stubbed_fetch", *WINDOW)
    rel = [d for d in dropped if d["date"] == "2025-09-16"]
    assert len(rel) == 1
    assert "does not name the expected release" in rel[0]["reason"]


def test_out_of_window_rows_never_yield_instants(cpi_html):
    instants, _, _ = bls_census.parse_bls_instants(
        cpi_html, "CPI", "u", None, "stubbed_fetch", *WINDOW)
    dates = {i["scheduled_utc"][:10] for i in instants}
    assert "2025-06-12" not in dates        # before the panel window
    assert "2026-10-14" not in dates        # after the panel window
    assert dates == {"2026-01-15", "2026-03-06",
                     "2026-03-11", "2026-07-15"}


def test_invalid_calendar_text_never_yields_instant():
    bad = ("<table><tr><td>February 30, 2026</td><td>8:30 AM</td>"
           "<td>Consumer Price Index for January 2026</td></tr></table>")
    rows = bls_census.parse_schedule_rows(bad)
    assert len(rows) == 1 and "invalid_date" in rows[0]
    instants, dropped, in_window = bls_census.parse_bls_instants(
        bad, "CPI", "u", None, "stubbed_fetch", *WINDOW)
    assert instants == [] and dropped == [] and in_window == 0
    # the malformed string itself must fail closed as a date
    with pytest.raises(ValueError):
        date.fromisoformat("2026-02-30")


# --------------------------------------------------------------------- #
# canary-negative + fail-closed census (offline stubs, no network)       #
# --------------------------------------------------------------------- #
def _live_pages(cpi_html, nfp_html):
    return {
        bls_census.BLS_SCHEDULE_URLS["CPI"]: cpi_html,
        bls_census.BLS_SCHEDULE_URLS["NFP"]: nfp_html,
    }


def test_run_census_stubbed_live_sources(cpi_html, nfp_html):
    census = bls_census.run_bls_census(
        *WINDOW, fetch=_stub_fetch(_live_pages(cpi_html, nfp_html)),
        verdict_fn=_verdict_fn, fabricated_days=("2026-02-14", "2026-06-20"),
        now_utc="2026-09-11T00:00:00+00:00")
    assert census["verdict"] == "PASS"
    assert census["instant_count"] == 7           # 4 CPI + 3 NFP (hand)
    assert census["method_chain"]["curl_class"]["status"] == "STUBBED"
    assert census["method_chain"]["webfetch_tool"]["status"] == "NOT_RUN"
    assert census["method_chain"]["browser_use_skill"]["status"] == "NOT_RUN"
    for inst in census["instants"]:
        assert inst["method"] == "stubbed_fetch"
        assert inst["source_url"].startswith("https://www.bls.gov/")
        assert inst["retrieved_utc"]
    # P-7 canaries: both fabricated Saturdays FAIL to produce instants
    fab = census["canaries"]["fabricated_days"]
    assert [f["fabricated_day"] for f in fab] == ["2026-02-14", "2026-06-20"]
    assert all(f["weekday"] == "saturday" for f in fab)
    assert all(f["verdict"] == "PASS" and "no instant produced" in f["observed"]
               for f in fab)
    assert "note" not in fab[0]        # live sources: canary is not vacuous
    # P-7: nonexistent series refused
    sp = census["canaries"]["series_probe"]
    assert sp["series"] == "S9:bls-cpi-instants-fabricated"
    assert sp["refused"] is True and sp["verdict"] == "PASS"


def test_run_census_all_sources_blocked_fail_closed():
    """Every official source denied (the measured ng2 reality): the census
    records BLOCKED_PER_SOURCE with ZERO instants -- never a fabricated
    PASS -- and the fabricated-day canaries still hold (vacuously, with
    the honest note attached)."""
    def dead_fetch(url, max_attempts=3, timeout=25.0, backoff_s=(0, 0)):
        return {"url": url, "ok": False, "status": 403,
                "attempts": [{"attempt": 1,
                              "retrieved_utc": "2026-09-11T00:00:00+00:00",
                              "status": 403, "error": "HTTPError 403"}],
                "body": None, "retrieved_utc": "2026-09-11T00:00:00+00:00"}

    census = bls_census.run_bls_census(
        *WINDOW, fetch=dead_fetch, verdict_fn=_verdict_fn,
        fabricated_days=("2026-02-14", "2026-06-20"),
        now_utc="2026-09-11T00:00:00+00:00")
    assert census["verdict"] == "BLOCKED_PER_SOURCE"
    assert census["instants"] == [] and census["instant_count"] == 0
    assert census["dropped"] == []
    for key, src in census["sources"].items():
        assert src["status"] == "BLOCKED"
        assert src["http_status"] == 403
        assert "no instants fabricated" in src["note"]
        assert src["sibling_urls_skipped"]      # etiquette: no hammering
    fab = census["canaries"]["fabricated_days"]
    assert all(f["verdict"] == "PASS" for f in fab)
    assert all("blocked source" in f.get("note", "") for f in fab)
    assert census["canaries"]["series_probe"]["verdict"] == "PASS"


def test_run_census_no_verdict_fn_records_not_run(cpi_html, nfp_html):
    census = bls_census.run_bls_census(
        *WINDOW, fetch=_stub_fetch(_live_pages(cpi_html, nfp_html)),
        verdict_fn=None, fabricated_days=("2026-02-14",),
        now_utc="2026-09-11T00:00:00+00:00")
    assert census["canaries"]["series_probe"]["verdict"] == "NOT_RUN"
    # a NOT_RUN series canary must not silently pass the census
    assert census["verdict"] == "FAIL_CANARIES"


def test_canary_dates_are_saturdays_not_in_any_fixture_instant(
        cpi_html, nfp_html):
    census = bls_census.run_bls_census(
        *WINDOW, fetch=_stub_fetch(_live_pages(cpi_html, nfp_html)),
        verdict_fn=_verdict_fn, fabricated_days=("2026-02-14", "2026-06-20"),
        now_utc="2026-09-11T00:00:00+00:00")
    dates = {i["scheduled_utc"][:10] for i in census["instants"]}
    assert {"2026-02-14", "2026-06-20"}.isdisjoint(dates)


# --------------------------------------------------------------------- #
# funding probe: offline stub (settlement-boundary sanity)               #
# --------------------------------------------------------------------- #
def test_funding_probe_stubbed_keyless():
    eight_h = 28_800_000
    rows = [{"symbol": "BTCUSDT", "fundingTime": str(eight_h * k),
             "fundingRate": "0.00001"} for k in (1, 2, 3)]

    def fetch_json(url):
        return {"ok": True, "status": 200, "payload": rows,
                "retrieved_utc": "2026-09-11T00:00:00+00:00"}

    out = bls_census.funding_probe(["BTCUSDT"], fetch_json=fetch_json)
    assert out["schema"] == "crypto_ng2_run/p0_funding_probe@1"
    assert out["status"] == "KEYLESS_ENDPOINT_PROVEN"
    probe = out["probes"][0]
    assert probe["ok"] is True and probe["rows_observed"] == 3
    assert probe["funding_time_min_ms"] == eight_h
    assert probe["funding_time_max_ms"] == eight_h * 3
    assert probe["boundary_hours_mod8_observed"] == [0]   # 8h boundaries


def test_funding_probe_stubbed_blocked_is_non_blocking():
    def fetch_json(url):
        return {"ok": False, "status": None, "payload": None,
                "error": "stub denial", "retrieved_utc":
                "2026-09-11T00:00:00+00:00"}

    out = bls_census.funding_probe(["BTCUSDT"], fetch_json=fetch_json)
    assert out["status"] == "BLOCKED_NOT_CONSUMED"
    assert out["probes"][0]["ok"] is False
