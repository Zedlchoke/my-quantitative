"""COMMODITIES-NG1 P0 gate tests (offline; no network).

Every assertion is either hand-computed (fixtures, DST clock arithmetic)
or re-verifies a committed P0 artifact (manifest hash checks, census
anchors, floor arithmetic, canary refusals).  Raw archive bytes are
gitignored (pinned by p0_raw_manifest.json); where those bytes are
present locally their digests are re-verified, where absent the test
skips that conditional leg -- committed surfaces are always verified.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from datetime import date, datetime, timezone

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

RUN_DIR = os.path.join(REPO_ROOT, "research", "control",
                       "commodities_ng1_run")

from research.assets.commodities_ng1 import cot_census, etp_census  # noqa: E402
from research.assets.commodities_ng1.cot_census import (  # noqa: E402
    CotLookupRefused, lookup_market, release_instant,
)
from research.assets.commodities_ng1.etp_census import (  # noqa: E402
    EtpLookupRefused,
)
from research.assets.commodities_ng1.plane_adapter import (  # noqa: E402
    CommoditiesNG1Plane, PlaneConsumptionRefused, PlaneDataBlocked,
)


def _load(name):
    with open(os.path.join(RUN_DIR, name), encoding="utf-8") as fh:
        return json.load(fh)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="module")
def gate():
    return _load("p0_gate.json")


@pytest.fixture(scope="module")
def manifest():
    return _load("p0_raw_manifest.json")


@pytest.fixture(scope="module")
def pairs():
    return _load("p0_market_pairs.json")


@pytest.fixture(scope="module")
def cot_censuses():
    return _load("p0_cot_market_census.json")


@pytest.fixture(scope="module")
def etp_censuses():
    return _load("p0_etp_census.json")["censuses"]


@pytest.fixture(scope="module")
def plane():
    return CommoditiesNG1Plane()


# -- PIT release clock (hand-computed DST arithmetic) ------------------------ #

def test_pit_release_clock_hand_computed_dst():
    # Tue 2025-12-30 -> Fri 2026-01-02 15:30 EST (UTC-5) = 20:30Z
    assert release_instant(date(2025, 12, 30)) == datetime(
        2026, 1, 2, 20, 30, tzinfo=timezone.utc)
    # Tue 2026-09-08 -> Fri 2026-09-11 15:30 EDT (UTC-4) = 19:30Z
    assert release_instant(date(2026, 9, 8)) == datetime(
        2026, 9, 11, 19, 30, tzinfo=timezone.utc)
    # Tue 2016-01-05 -> Fri 2016-01-08 15:30 EST = 20:30Z
    assert release_instant(date(2016, 1, 5)) == datetime(
        2016, 1, 8, 20, 30, tzinfo=timezone.utc)


def test_pit_release_clock_refuses_non_tuesday():
    with pytest.raises(CotLookupRefused):
        release_instant(date(2025, 11, 19))     # Wednesday
    with pytest.raises(CotLookupRefused):
        release_instant(date(2025, 11, 21))     # Friday


def test_pit_clock_evidence_pinned(gate):
    pit = gate["sections"]["pit_clock"]
    page = pit["schedule_page"]
    assert page["sha256"], "schedule page must be sha-pinned"
    assert page["status"] in ("FETCHED", "REUSED_PINNED")
    quote = page["release_quote_measured"] or ""
    assert "3:30" in quote and "Tuesday" in quote, (
        "the pinned official statement must carry the release rule")
    sample = pit["sample_release_instants"]
    assert sample["first_release_utc"] == "2016-01-08T20:30:00+00:00"
    assert sample["last_release_utc"] == "2026-09-11T19:30:00+00:00"
    assert pit["verdict"] == "PASS"


# -- CoT parser (hand-built fixture) ------------------------------------------ #

FIXTURE_CSV = (
    '"Market and Exchange Names","As of Date in Form YYMMDD",'
    '"As of Date in Form YYYY-MM-DD","CFTC Contract Market Code",'
    '"CFTC Market Code in Initials","CFTC Region Code",'
    '"CFTC Commodity Code","Open Interest (All)",'
    '"Noncommercial Positions-Long (All)",'
    '"Noncommercial Positions-Short (All)",'
    '"Noncommercial Positions-Spreading (All)",'
    '"Commercial Positions-Long (All)",'
    '"Commercial Positions-Short (All)",'
    '" Total Reportable Positions-Long (All)",'
    '"Total Reportable Positions-Short (All)"\n'
    '"TEST METAL - COMMODITY EXCHANGE INC.",260101,2026-01-06,999101,'
    'CMX ,01,999 ,  488488,  132115,  203106,  151885,  175217,  105241,'
    '  459217,  460232\n'
    '"TEST METAL - COMMODITY EXCHANGE INC.",260108,2026-01-13,999101,'
    'CMX ,01,999 ,  400000,  130000,  200000,  150000,  170000,  100000,'
    '  450000,  455000\n'
    '"TEST METAL - COMMODITY EXCHANGE INC.",260115,2026-01-20,999101,'
    'CMX ,01,999 ,  390000,  129000,  199000,  149000,  169000,   99000,'
    '  445000,  450000\n'
)


def test_cot_parser_fixture_hand_computed():
    recs = cot_census.parse_annual_text(FIXTURE_CSV, source="fixture")
    assert len(recs) == 3
    r0 = recs[0]
    assert r0.contract_market_code == "999101"
    assert r0.market_name == "TEST METAL - COMMODITY EXCHANGE INC."
    assert r0.report_date == date(2026, 1, 6)
    assert r0.exchange_code == "CMX"
    # fixed-width spaced integers are stripped
    assert (r0.open_interest, r0.noncomm_long, r0.noncomm_short) == (
        488488, 132115, 203106)
    assert (r0.noncomm_spreading, r0.comm_long, r0.comm_short) == (
        151885, 175217, 105241)
    cens = cot_census.census_market(recs)
    assert cens["weeks"] == 3
    assert cens["first_report"] == "2026-01-06"
    assert cens["last_report"] == "2026-01-20"
    assert cens["max_gap_days"] == 7
    assert cens["cot_leg_eligible"] is False   # 3 weeks << 520
    # roundtrip through the canonical normalized CSV surface
    again = cot_census.csv_to_records(
        cot_census.records_to_csv(recs))
    assert cot_census.records_digest(again) == cot_census.records_digest(recs)


def test_cot_parser_refuses_format_drift():
    broken = FIXTURE_CSV.replace('"CFTC Contract Market Code",', "")
    with pytest.raises(cot_census.CotParseError):
        cot_census.parse_annual_text(broken, source="broken-fixture")
    with pytest.raises(cot_census.CotParseError):
        cot_census.parse_annual_text("", source="empty")


FIXTURE_HEADER = (
    '"Market and Exchange Names","As of Date in Form YYMMDD",'
    '"As of Date in Form YYYY-MM-DD","CFTC Contract Market Code",'
    '"CFTC Market Code in Initials","CFTC Region Code",'
    '"CFTC Commodity Code","Open Interest (All)",'
    '"Noncommercial Positions-Long (All)",'
    '"Noncommercial Positions-Short (All)",'
    '"Noncommercial Positions-Spreading (All)",'
    '"Commercial Positions-Long (All)",'
    '"Commercial Positions-Short (All)",'
    '" Total Reportable Positions-Long (All)",'
    '"Total Reportable Positions-Short (All)"'
)


def _synthetic_week(n_weeks: int) -> str:
    """A synthetic weekly market starting Tue 2016-01-05."""
    rows = []
    d = date(2016, 1, 5)
    for i in range(n_weeks):
        rows.append(
            f'"M - X",{d.strftime("%y%m%d")},{d.isoformat()},"000101",'
            f'"CMX ","00","001 ",{1000 + i},1,2,3,4,5,6,7')
        d = date.fromordinal(d.toordinal() + 7)
    return FIXTURE_HEADER + "\n" + "\n".join(rows)


def test_cot_coverage_rule_hand_computed():
    """547 weeks spanning 10.5y is eligible; 500 weeks is not."""
    recs = cot_census.parse_annual_text(_synthetic_week(547),
                                        source="synthetic-long")
    cens = cot_census.census_market(recs)
    assert cens["weeks"] == 547
    assert cens["first_report"] == "2016-01-05"
    assert cens["max_gap_days"] == 7
    assert cens["span_years"] > 10.0
    assert cens["cot_leg_eligible"] is True
    # starve it under the 520-week floor -> ineligible, fail-closed
    short = cot_census.parse_annual_text(_synthetic_week(500),
                                         source="synthetic-short")
    cens_short = cot_census.census_market(short)
    assert cens_short["weeks"] == 500
    assert cens_short["cot_leg_eligible"] is False


# -- manifest hash checks (committed surfaces always; raw if present) --------- #

def test_manifest_hash_checks_committed_surfaces(manifest):
    entries = manifest["entries"]
    assert "cftc/deacot2016" in entries and "cftc/deacot2026" in entries
    committed_checked = 0
    for name, meta in sorted(entries.items()):
        if not meta.get("committed"):
            continue
        path = os.path.join(REPO_ROOT, meta["path"])
        assert os.path.isfile(path), f"committed artifact missing: {path}"
        assert sha256_file(path) == meta["sha256"], name
        committed_checked += 1
    assert committed_checked >= 26            # 26 ETP CSVs + targets csv


def test_manifest_hash_checks_raw_when_present(manifest):
    entries = manifest["entries"]
    zips = [n for n in entries if n.startswith("cftc/deacot")]
    assert len(zips) == 11
    present = 0
    for name in zips:
        path = os.path.join(REPO_ROOT, entries[name]["path"])
        if os.path.isfile(path):
            assert sha256_file(path) == entries[name]["sha256"], name
            present += 1
    assert present >= 1


# -- measured census anchors (hand-computed from the pulled archives) --------- #

def test_gold_cot_census_anchor(cot_censuses):
    gold = cot_censuses["markets"]["088691"]
    assert gold["weeks"] == 558
    assert gold["first_report"] == "2016-01-05"
    assert gold["last_report"] == "2026-09-08"
    assert gold["span_years"] == pytest.approx(10.6749)
    assert gold["cot_leg_eligible"] is True
    assert cot_censuses["market_count"] == 648
    assert len(cot_censuses["cot_leg_eligible_markets"]) == 133


def test_wheat_identity_is_code_level(cot_censuses):
    """Display names may drift; identity is the CFTC contract market
    code 001602 across the whole window (recorded as name events)."""
    wheat = cot_censuses["markets"]["001602"]
    assert wheat["weeks"] == 558
    names = {n["market_name"] for n in wheat["market_names"]}
    assert any("WHEAT" in n and "CHICAGO" in n for n in names)


def test_gld_etp_census_matches_lead_probe(etp_censuses):
    """Lead probe (2026-09-12): GLD 2004-11-18 -> 2026-09-11, 5487 rows."""
    gld = etp_censuses["GLD"]
    assert gld["first_eod"] == "2004-11-18"
    assert gld["last_eod"] == "2026-09-11"
    assert gld["rows"] == 5487
    assert gld["etp_leg_eligible"] is True
    # GLD pays no distributions: RAW == adjusted full-length (V8 check)
    assert gld["corp_actions_cross_check"]["divergence_events"] == 0


def test_dead_etp_legs_fail_closed(etp_censuses):
    for sym, last, reason_frag in [
            ("DBS", "2023-03-16", "stale"),
            ("JO", "2023-07-21", "rows"),
            ("NIB", "2023-07-21", "stale"),
            ("COW", "2024-01-04", "stale")]:
        cens = etp_censuses[sym]
        assert cens["etp_leg_eligible"] is False
        assert cens["last_eod"] == last
        assert any(reason_frag in r for r in cens["ineligible_reasons"])


def test_etp_leg_rule_synthetic_fail_closed():
    as_of = date(2026, 9, 12)
    rows = [{"date": date(2026, 1, 5 + i), "open": 1.0, "high": 1.0,
             "low": 1.0, "close": 1.0, "adj_close": 1.0, "volume": 0}
            for i in range(3)]
    cens = etp_census.census_etp(rows, "SHORTLIFE", as_of)
    assert cens["etp_leg_eligible"] is False
    assert len(cens["ineligible_reasons"]) == 3


# -- market-pair floor --------------------------------------------------------- #

def test_market_pair_floor_measured(gate, pairs):
    floor = gate["sections"]["market_pairs_floor"]
    qualifying = [p for p in pairs["pairs"] if p["qualifying"]]
    assert floor["observed"]["qualifying_pairs"] == len(qualifying)
    assert pairs["floor"]["required_pairs"] == 15
    assert len(qualifying) >= 15
    assert pairs["verdict"] == "PASS"
    # every qualifying pair carries BOTH measured legs past frozen rules
    for p in qualifying:
        assert p["cot_weeks"] >= 520
        assert p["etp_rows"] >= 2000
        assert p["cot_span_years"] >= 10.0
    # the 20-pair measured list: 17 pure + 3 packet-declared DBA baskets
    pure = [p for p in qualifying if p["purity"] == "pure"]
    basket = [p for p in qualifying if p["purity"] == "basket"]
    assert len(qualifying) == 20 and len(pure) == 17 and len(basket) == 3
    assert all(p["etp"] == "DBA" for p in basket)


def test_gate_final_verdict_consistency(gate):
    assert gate["final_verdict"] == "PASS"
    assert gate["cycle_id"] == "COMMODITIES-NG1"
    for section in ("cftc_pull", "cot_census", "pit_clock", "etp_pull",
                    "etp_census", "delisted_probe", "market_pairs_floor",
                    "canaries", "shadow_parity", "adoption_query"):
        assert gate["sections"][section]["verdict"] in (
            "PASS", "BLOCKED_DATA"), section
    # no section may be a silent FAIL while the gate says PASS
    for section, body in gate["sections"].items():
        assert body["verdict"] != "FAIL", section


# -- canaries (each must fail; replayed locally) -------------------------------- #

def test_canaries_recorded_failures(gate):
    canaries = gate["sections"]["canaries"]["observed"]
    required = {"fabricated_cftc_market_code_ZZZ999",
                "fabricated_release_date_wednesday",
                "never_existed_etp_ticker",
                "never_existed_etp_ticker_live_wire_404",
                "plane_consume_fabricated_ticker"}
    assert {c["canary"] for c in canaries} == required
    assert all(c["failed_as_required"] for c in canaries)
    assert gate["sections"]["canaries"]["verdict"] == "PASS"


def test_canary_replay_local(plane):
    """Replay every canary locally against committed surfaces."""
    # fabricated market code refused against the committed weekly CSV
    weekly = os.path.join(RUN_DIR, "p0_cot_weekly_targets.csv")
    with open(weekly, encoding="utf-8") as fh:
        recs = cot_census.csv_to_records(fh.read())
    with pytest.raises(CotLookupRefused):
        lookup_market(recs, "ZZZ999")
    # fabricated release date refused
    with pytest.raises(CotLookupRefused):
        release_instant(date(2025, 11, 19))
    # never-existed ticker refused (vendor error-detail payload shape)
    with pytest.raises(EtpLookupRefused):
        etp_census.normalize_eod_payload(
            {"detail": "symbol not found"}, "ZZZZNOPE")
    # plane refuses anything outside the frozen consumption set
    with pytest.raises(PlaneConsumptionRefused):
        plane.consume("etp/eod/ZZZZNOPE")
    with pytest.raises(PlaneConsumptionRefused):
        plane.consume("cftc/deacot2015")          # outside pulled set


# -- plane adoption (digest-verified consume + frozen query + parity) ----------- #

def test_adapter_consume_via_plane_digest_verified(plane, manifest):
    res = plane.consume("etp/eod/GLD")
    pinned = manifest["entries"]["etp/eod/GLD"]
    assert res["sha256_measured"] == res["sha256_pinned"] \
        == pinned["sha256"]
    assert res["verdict"] == "GRANTED"
    assert res["series"] == "S4:eodhd-etp-eod"


def test_adapter_digest_flip_blocked(tmp_path):
    """A tampered artifact is BLOCKED_DATA: never consumed, never fixed."""
    tampered = _load("p0_raw_manifest.json")
    tampered["entries"]["etp/eod/GLD"]["sha256"] = "0" * 64
    bad_manifest = tmp_path / "tampered_manifest.json"
    bad_manifest.write_text(json.dumps(tampered), encoding="utf-8")
    bad_plane = CommoditiesNG1Plane(manifest_path=str(bad_manifest))
    with pytest.raises(PlaneDataBlocked) as err:
        bad_plane.consume("etp/eod/GLD")
    assert err.value.reason == "BLOCKED_DATA"


def test_adapter_refuses_unknown_series(plane):
    with pytest.raises(PlaneConsumptionRefused):
        plane.consume("s4/binance-panels")       # another family's series
    one = plane.manifest["entries"]["cftc/deacot2016"].copy()
    assert plane.verdict(one["series"]) == "GRANTED"
    assert plane.verdict("S9:never-registered") == "UNKNOWN_SERIES"


def test_adapter_frozen_query_success(plane):
    out = plane.query_entry("etp/eod/CORN")
    assert out["query"]["verdict"] == "SUCCESS"
    assert out["query"]["row_count"] == 1
    rows = out["query"]["rows"]
    # hand-computed anchors from the committed CORN.csv census
    assert rows[0][0] == 4090
    assert rows[0][1] == "2010-06-09"
    assert rows[0][2] == "2026-09-11"


def test_adapter_pit_guarded_records(plane):
    recs = plane.pit_guarded_records("cftc/deacot2016")
    assert len(recs) > 0
    # one second before the LAST 2016 report's release instant: a use
    # of the final report must be withheld (fail-closed PIT violation)
    last = max(r.report_date for r in recs)
    just_before = release_instant(last) - __import__("datetime").timedelta(
        seconds=1)
    with pytest.raises(CotLookupRefused):
        plane.pit_guarded_records("cftc/deacot2016",
                                  use_instant_utc=just_before)
    # at the release instant the report becomes visible
    visible = plane.pit_guarded_records("cftc/deacot2016",
                                        use_instant_utc=release_instant(last))
    assert max(r.report_date for r in visible) == last


def test_release_instants_envelope(plane):
    env = plane.release_instants("cftc/deacot2026")
    assert env["rule"].startswith("Friday 15:30 America/New_York")
    assert env["first_release_instant_utc"].endswith("+00:00")


def test_shadow_parity_pilot_passed(gate):
    parity = gate["sections"]["shadow_parity"]
    assert parity["verdict"] == "PASS"
    entries = {r["entry"] for r in parity["observed"]}
    assert entries == {"cftc/deacot2016", "cftc/deacot2020",
                       "cftc/deacot2026", "etp/eod/GLD", "etp/eod/CORN"}
    for row in parity["observed"]:
        assert row["identical"] is True
        assert row["overlap_records"] > 0


# -- delisted-channel probe evidence -------------------------------------------- #

def test_delisted_probe_evidence(gate):
    probe = gate["sections"]["delisted_probe"]
    assert probe["verdict"] == "PASS"
    obs = probe["observed"]
    assert obs["listing_rows"] > 50000        # V8 measured 59,923 (2026-09: 60,075)
    assert set(obs["dead_name_hits"]) == {"BAL", "DNO", "JJA", "OIL"}
    assert "UHN" not in obs["dead_name_hits"]
    assert "DJP" not in obs["dead_name_hits"]


# -- targets CSV consistency ------------------------------------------------------- #

def test_targets_csv_matches_census(cot_censuses):
    path = os.path.join(RUN_DIR, "p0_cot_weekly_targets.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    codes = {r["contract_market_code"] for r in rows}
    assert codes == set(cot_censuses["cot_leg_eligible_markets"]) & codes
    assert "088691" in codes
    # row count == sum of weeks across resolved target markets
    per_code = {}
    for r in rows:
        per_code[r["contract_market_code"]] = \
            per_code.get(r["contract_market_code"], 0) + 1
    for code, n in per_code.items():
        assert n == cot_censuses["markets"][code]["weeks"]
