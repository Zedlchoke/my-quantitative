"""STOCKS-NG2 P0 tests: 4/A parser, P-7 canary fail law, etiquette
limiter, original-matching logic, and EODHD response-shape law.

Fixtures live under /tmp (dispatch packet); NO network, NO API key --
the EODHD path is exercised purely against fake responses and a fake
token string.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

import pytest

_REPO = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.pardir))
sys.path.insert(0, _REPO)

from research.assets.stocks_ng2 import eodhd_probe          # noqa: E402
from research.assets.stocks_ng2.extended_census import (     # noqa: E402
    MalformedForm4Error, census_amendments, census_b_floor_evaluation,
    parse_form4a, well_formed_sample)
from research.assets.stocks_ng2.form4a_ingest import (       # noqa: E402
    RateLimiter, canary_checks, choose_primary_doc, fetch_targets,
    load_state)

_TMP_BASE = "/tmp/stocks_ng2_p0_tests"


@pytest.fixture(scope="module")
def tmpdir_mod():
    d = tempfile.mkdtemp(prefix="ng2p0_", dir=_TMP_BASE
                         if os.path.isdir(_TMP_BASE) else None)
    os.makedirs(_TMP_BASE, exist_ok=True)
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ------------------------------------------------------------------ #
# 1. Form 4/A parser
# ------------------------------------------------------------------ #

FORM4A_XML = b"""<?xml version="1.0"?>
<ownershipDocument>
  <documentType>4/A</documentType>
  <periodOfReport>2024-05-10</periodOfReport>
  <issuer>
    <issuerCik>0000001800</issuerCik>
    <issuerName>ABBOTT LABORATORIES</issuerName>
  </issuer>
  <reportingOwner>
    <reportingOwnerId>
      <rptOwnerCik>0001234567</rptOwnerCik>
    </reportingOwnerId>
  </reportingOwner>
</ownershipDocument>
"""


def test_parse_form4a_extracts_match_key(tmpdir_mod):
    parsed = parse_form4a(FORM4A_XML)
    assert parsed == {
        "documentType": "4/A",
        "issuerCik": "0000001800",
        "rptOwnerCik": "0001234567",
        "periodOfReport": "2024-05-10",
    }


def test_parse_form4a_missing_elements_are_none_not_guessed():
    parsed = parse_form4a(b"<ownershipDocument><documentType>4/A"
                          b"</documentType></ownershipDocument>")
    assert parsed["documentType"] == "4/A"
    assert parsed["issuerCik"] is None
    assert parsed["rptOwnerCik"] is None
    assert parsed["periodOfReport"] is None


def test_parse_form4a_malformed_fails_closed():
    with pytest.raises(MalformedForm4Error):
        parse_form4a(b"<not-xml><broken")


# ------------------------------------------------------------------ #
# 2. P-7 canary law: fabricated accessions + dead CIK must FAIL
# ------------------------------------------------------------------ #

def _fake_transport_404(url: str):
    return 404, b"Not Found"


def _fake_transport_serves_everything(url: str):
    if url.endswith("index.json") or "/submissions/" in url:
        body: bytes = json.dumps({"directory": {"item": [
            {"name": "fake.xml", "type": "text.xml", "size": "10"}]}}
        ).encode()
    else:
        body = FORM4A_XML
    return 200, body


def test_canaries_all_404_is_expected_failure():
    out = canary_checks(transport=_fake_transport_404)
    assert len(out["checks"]) == 3
    assert all(c["failed_as_expected"] for c in out["checks"])
    assert out["all_failed_as_expected"] is True


def test_canary_served_is_positive_anomaly_fail_closed():
    # a never-existed accession serving data MUST flip the verdict
    out = canary_checks(transport=_fake_transport_serves_everything)
    assert out["all_failed_as_expected"] is False


# ------------------------------------------------------------------ #
# 3. etiquette limiter: start-to-start spacing (<= 2 req/s)
# ------------------------------------------------------------------ #

def test_rate_limiter_spaces_request_starts():
    clock = {"t": 0.0}
    waits: list[float] = []

    def fake_sleep(w: float) -> None:
        waits.append(round(w, 3))
        clock["t"] += w              # sleep advances the clock

    rl = RateLimiter(min_interval=0.55,
                     clock=lambda: clock["t"], sleeper=fake_sleep)
    starts = []
    starts.append(rl.acquire())      # first: no wait
    clock["t"] += 0.10              # 0.10s of work
    starts.append(rl.acquire())      # must wait 0.45s
    assert abs((starts[1] - starts[0]) - 0.55) < 1e-9
    assert waits and abs(waits[0] - 0.45) < 1e-6


# ------------------------------------------------------------------ #
# 4. original-matching logic (extended census, fixtures under /tmp)
# ------------------------------------------------------------------ #

def _write_state(path: str, rows: list[dict]) -> None:
    with open(path, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def _mk_amendment(root: str, cik: str, acc: str, issuer: str,
                  owner: str, period: str, doc_type: str = "4/A",
                  fname: str = "doc4a.xml") -> str:
    xml = (f"<?xml version='1.0'?><ownershipDocument>"
           f"<documentType>{doc_type}</documentType>"
           f"<periodOfReport>{period}</periodOfReport>"
           f"<issuer><issuerCik>{issuer}</issuerCik></issuer>"
           f"<reportingOwner><reportingOwnerId>"
           f"<rptOwnerCik>{owner}</rptOwnerCik>"
           f"</reportingOwnerId></reportingOwner></ownershipDocument>")
    d = os.path.join(root, cik, acc)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, fname)
    with open(p, "w") as fh:
        fh.write(xml)
    return p


@pytest.fixture()
def census_fixture(tmpdir_mod):
    root = os.path.join(tmpdir_mod, "form4a_census")
    shutil.rmtree(root, ignore_errors=True)
    state = os.path.join(tmpdir_mod, "form4a_census_state.jsonl")
    rows = []

    def add(cik, acc, issuer, owner, period, doc_type="4/A",
            is_xml=True, primary="doc4a.xml"):
        _mk_amendment(root, cik, acc, issuer, owner, period, doc_type)
        rows.append({"cik": cik, "accession": acc, "status": "OK",
                     "accession_nodash": acc, "filing_date":
                     f"{period[:4]}-06-01",
                     "primary_file": primary,
                     "primary_is_xml": is_xml,
                     "index_sha256": "0" * 64,
                     "primary_sha256": "1" * 64})
    # 200 resolvable amendments (floor boundary, honest boundary test)
    for i in range(200):
        add("CIK0000001800", f"0000001800240000{i:03d}",
            "0000001800", "0001234567", "2024-05-10")
    # 1 unresolvable (period not in originals index)
    add("CIK0000001800", "000000180024999999",
        "0000001800", "0001234567", "1999-01-01")
    # 1 vintage non-XML row (fetched, not a parseable amendment)
    add("CIK0000002969", "000000296905000001",
        "0000002969", "0000987654", "2005-05-10", is_xml=False)
    # 1 unexpected docType (a plain '4' served under a 4/A accession)
    add("CIK0000003570", "000000357024000001",
        "0000003570", "0000987654", "2024-05-10", doc_type="4")
    _write_state(state, rows)
    original_index = {"0000001800|0001234567|2024-05-10": 1}
    return root, state, original_index


def test_original_matching_resolvable_and_floor_boundary(census_fixture):
    root, state, original_index = census_fixture
    census = census_amendments(root, state, original_index)
    assert census["fetched_accessions"] == 203
    assert census["fetched_non_xml"] == 1
    assert census["amendment_docs"] == 201       # 200 + 1 unresolvable
    assert census["unexpected_doc_types"] == {"4": 1}
    assert census["amendments_with_resolvable_original"] == 200
    floor = census_b_floor_evaluation(census)
    assert floor["floor"] == 200
    assert floor["met"] is True                  # exactly at the floor


def test_floor_unmet_when_below_200(census_fixture):
    root, state, original_index = census_fixture
    original_index = {}                          # nothing resolvable
    census = census_amendments(root, state, original_index)
    assert census["amendments_with_resolvable_original"] == 0
    assert census_b_floor_evaluation(census)["met"] is False


def test_malformed_amendment_fails_closed_counted(tmpdir_mod):
    root = os.path.join(tmpdir_mod, "form4a_malformed")
    shutil.rmtree(root, ignore_errors=True)
    state = os.path.join(tmpdir_mod, "form4a_malformed_state.jsonl")
    d = os.path.join(root, "CIK0000001800", "000000180024000001")
    os.makedirs(d)
    with open(os.path.join(d, "doc4a.xml"), "w") as fh:
        fh.write("<broken not=xml")
    _write_state(state, [{
        "cik": "CIK0000001800", "accession": "0000001800-24-000001",
        "accession_nodash": "000000180024000001", "status": "OK",
        "filing_date": "2024-06-01", "primary_file": "doc4a.xml",
        "primary_is_xml": True}])
    census = census_amendments(root, state, {"k": 1})
    assert census["amendment_docs"] == 0        # NOT counted
    assert census["malformed_xml_docs"] == 1


def test_well_formed_sample_5_docs(census_fixture):
    root, state, _ = census_fixture
    paths = []
    for dirpath, _ds, fns in os.walk(root):
        for fn in fns:
            if fn.endswith(".xml"):
                paths.append(os.path.join(dirpath, fn))
    sample = well_formed_sample(paths)
    assert sample["sample_size"] == 5
    assert sample["all_well_formed"] is True


# ------------------------------------------------------------------ #
# 5. primary-doc selection + resume (no network)
# ------------------------------------------------------------------ #

def test_choose_primary_doc_matches_metadata_basename():
    idx = json.dumps({"directory": {"item": [
        {"name": "0000001800-24-000001-index.htm"},
        {"name": "form4a.xml"}]}}).encode()
    out = choose_primary_doc(idx, "xslF345X05/form4a.xml")
    assert out == {"filename": "form4a.xml", "source": "metadata"}


def test_choose_primary_doc_falls_back_to_index_xml():
    idx = json.dumps({"directory": {"item": [
        {"name": "0000001800-24-000001-index.htm"},
        {"name": "ownership.xml"}]}}).encode()
    out = choose_primary_doc(idx, "gone.txt")
    assert out == {"filename": "ownership.xml", "source": "index_xml"}


def test_fetch_resume_skips_completed(tmpdir_mod):
    root = os.path.join(tmpdir_mod, "form4a_fetch")
    shutil.rmtree(root, ignore_errors=True)
    state = os.path.join(tmpdir_mod, "form4a_fetch_state.jsonl")
    calls = {"n": 0}

    def transport(url: str):
        calls["n"] += 1
        if url.endswith("index.json"):
            body = json.dumps({"directory": {"item": [
                {"name": "doc4a.xml"}]}})
            return 200, body.encode()
        return 200, FORM4A_XML

    targets = [{
        "cik": "CIK0000001800", "cik_int": 1800,
        "accession": "0000001800-24-000001",
        "accession_nodash": "000000180024000001",
        "filing_date": "2024-06-01",
        "primary_document": "doc4a.xml", "form": "4/A"}]
    s1 = fetch_targets(targets, root, state, transport=transport)
    assert s1["fetched_ok"] == 1 and calls["n"] == 2
    s2 = fetch_targets(targets, root, state, transport=transport)
    assert s2["resumed_done"] == 1 and calls["n"] == 2  # zero new calls
    terminal = load_state(state)
    assert terminal["000000180024000001"]["status"] == "OK"


# ------------------------------------------------------------------ #
# 6. EODHD response-shape law (fake responses, NO key)
# ------------------------------------------------------------------ #

FAKE_KEY = "fake-key-never-real"          # never a real credential

SI_RECORDS = json.dumps([
    {"date": "2026-09-01", "shortInterest": 1_234_567,
     "avgDailyShareVolume": 5_000_000, "daysToCover": 0.25}]).encode()


def test_shape_not_authorized_on_http_403():
    v = eodhd_probe.classify_short_interest_response(403, b"")
    assert v["class"] == "NOT_AUTHORIZED"


def test_shape_not_authorized_on_error_payload():
    v = eodhd_probe.classify_short_interest_response(
        200, json.dumps({"code": 403, "message": "plan limited"}).encode())
    assert v["class"] == "NOT_AUTHORIZED"


def test_shape_ok_nonempty_list():
    v = eodhd_probe.classify_short_interest_response(200, SI_RECORDS)
    assert v["class"] == "OK_NONEMPTY"
    assert v["records"] == 1


def test_shape_ok_empty_list():
    v = eodhd_probe.classify_short_interest_response(200, b"[]")
    assert v["class"] == "OK_EMPTY"


def test_shape_malformed_body():
    v = eodhd_probe.classify_short_interest_response(200, b"<html>")
    assert v["class"] == "MALFORMED"


def _probe_transport_factory(status_by_symbol: dict):
    """Fake EODHD transport: matches the EXACT symbol segment of the
    URL (never a substring), so 'A' does not hijack 'AA'/'AAA'."""
    def transport(url: str):
        # url = .../short-interests/{sym}?api_token=...
        seg = url.rsplit("/", 1)[-1].split("?")[0]
        if seg in status_by_symbol:
            val = status_by_symbol[seg]
            if isinstance(val, int):
                return val, b""
            return 200, val
        return 200, SI_RECORDS
    return transport


def test_probe_aborts_not_authorized_fail_closed():
    transport = _probe_transport_factory({"A": 403, "AA": 403})
    out = eodhd_probe.probe_symbols(["A", "AA"], FAKE_KEY,
                                    transport=transport,
                                    sleep_between=0.0)
    assert out["aborted"] is True
    assert out["rows"][0]["class"] == "NOT_AUTHORIZED"


def test_probe_family_not_served_404_classified():
    # entitlement gateway 404s families the plan lacks (no JSON 403);
    # BOTH symbol forms 404 for every symbol
    transport = _probe_transport_factory(
        {"A": 404, "A.US": 404, "AA": 404, "AA.US": 404})
    out = eodhd_probe.probe_symbols(["A", "AA"], FAKE_KEY,
                                    transport=transport,
                                    sleep_between=0.0)
    assert out["aborted"] is False
    assert all(r["class"] == "FAMILY_NOT_SERVED_404"
               for r in out["rows"])


def test_control_probe_distinguishes_key_from_family():
    alive = _probe_transport_factory({"AAPL.US": SI_RECORDS})
    assert eodhd_probe.control_probe(
        FAKE_KEY, transport=alive)["alive"] is True
    dead = _probe_transport_factory({"AAPL.US": 401})
    assert eodhd_probe.control_probe(
        FAKE_KEY, transport=dead)["alive"] is False


def test_probe_coverage_and_floor_projection():
    symbols = ["A", "AA", "AAA", "B", "C", "D", "E", "F"]
    empty = json.dumps([]).encode()
    # A and AA serve short-interest data; AAA served but empty;
    # the rest fall through to the default (nonempty) response
    transport = _probe_transport_factory(
        {"A": SI_RECORDS, "AA": SI_RECORDS, "AAA": empty})
    out = eodhd_probe.probe_symbols(symbols, FAKE_KEY,
                                    transport=transport,
                                    sleep_between=0.0)
    assert out["aborted"] is False
    ev = eodhd_probe.evaluate_family(out)
    assert ev["probe_symbols"] == 8
    assert ev["symbols_nonempty_data"] == 7
    assert abs(ev["measured_coverage_fraction"] - 0.875) < 1e-9
    assert ev["projected_entities_with_data"] == round(
        0.875 * eodhd_probe.PINNED_EODHD_UNIVERSE)     # 1897
    assert ev["floor_met_projected"] is True           # 1897 >= 500
    assert ev["projection_method"].startswith(
        "measured_coverage_fraction")                  # labelled PROJECTION


def test_deterministic_sample_spread():
    syms = [f"S{i:04d}" for i in range(2168)]
    sample = eodhd_probe.deterministic_sample(syms, 50)
    assert len(sample) == 50
    assert len(set(sample)) == 50            # distinct, spread picks
    assert sample[0] == "S0000"
    assert sample[-1] == "S2124"             # 49*2168//50 -- by rule


def test_key_loader_never_leaks_value(tmpdir_mod):
    env = os.path.join(tmpdir_mod, "fake.env")
    with open(env, "w") as fh:
        fh.write("OTHER=x\nEODHD_API_KEY=  super-secret-value  \n")
    assert eodhd_probe.load_api_key(env) == "super-secret-value"
    with open(env, "w") as fh:
        fh.write("OTHER=x\n")
    with pytest.raises(eodhd_probe.KeyLoadError) as exc:
        eodhd_probe.load_api_key(env)
    assert "super-secret-value" not in str(exc.value)
