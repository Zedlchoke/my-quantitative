"""Offline SEC EDGAR adapter tests against hand-written fixtures."""

import json
from datetime import datetime, timezone

import pytest

from research.data_fusion.adapters.base import AdapterError
from research.data_fusion.adapters.sec import (
    SEC_ACCEPTANCE_TIME_NOT_DISSEMINATION_PROOF,
    SEC_DURATION_FACTS_SKIPPED_V1,
    SEC_FILED_DATE_ONLY_NOT_EXACT_AVAILABILITY,
    SecAdapter,
)

from .conftest import RETRIEVED_TIME, fixture_bytes, response_for

UTC = timezone.utc


@pytest.fixture
def adapter() -> SecAdapter:
    return SecAdapter()


def submissions_response(body: bytes) -> object:
    from research.data_fusion.adapters.base import RequestSpec

    request = SecAdapter().build_submissions_request("1")
    return response_for(request, body)


def test_submissions_request_is_deterministic_and_https_only(adapter):
    first = adapter.build_submissions_request("1")
    second = adapter.build_submissions_request("0000000001")
    assert first.url == "https://data.sec.gov/submissions/CIK0000000001.json"
    assert first.request_id() == second.request_id()
    with pytest.raises(AdapterError) as exc:
        adapter.normalize_cik("abc")
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_parse_submissions_happy_path(adapter):
    output = adapter.parse_submissions(submissions_response(fixture_bytes("sec_submissions.json")))
    assert len(output.records) == 2
    first = output.records[0]
    assert first.value == "0000000001-24-000001"
    assert first.entity_id == "CIK0000000001"
    # exact acceptance time becomes event_time; availability stays date-only upper bound
    assert first.event_time_utc == datetime(2024, 1, 3, 14, 30, tzinfo=UTC)
    assert first.available_time_utc == datetime(2024, 1, 3, 23, 59, 59, tzinfo=UTC)
    assert first.effective_time_utc is None
    second = output.records[1]
    assert second.event_time_utc == datetime(2024, 1, 8, 23, 59, 59, tzinfo=UTC)
    assert second.available_time_utc == datetime(2024, 1, 8, 23, 59, 59, tzinfo=UTC)
    assert first.raw_path == output.raw_path
    assert first.raw_sha256 == output.raw_sha256
    assert SEC_FILED_DATE_ONLY_NOT_EXACT_AVAILABILITY in output.note_codes()
    assert SEC_ACCEPTANCE_TIME_NOT_DISSEMINATION_PROOF in output.note_codes()


def test_parse_submissions_never_claims_exact_availability(adapter):
    output = adapter.parse_submissions(submissions_response(fixture_bytes("sec_submissions.json")))
    timings_basis = {record.available_time_utc for record in output.records}
    assert all(time.hour == 23 and time.minute == 59 for time in timings_basis)


def test_submissions_duplicate_accession_is_refused(adapter):
    payload = json.loads(fixture_bytes("sec_submissions.json"))
    payload["filings"]["recent"]["accessionNumber"][1] = payload["filings"]["recent"]["accessionNumber"][0]
    with pytest.raises(AdapterError) as exc:
        adapter.parse_submissions(submissions_response(json.dumps(payload).encode()))
    assert exc.value.code == "DUPLICATE_RECORD_ID"


def test_submissions_unknown_column_is_refused(adapter):
    payload = json.loads(fixture_bytes("sec_submissions.json"))
    payload["filings"]["recent"]["totallyNew"] = ["x", "y"]
    with pytest.raises(AdapterError) as exc:
        adapter.parse_submissions(submissions_response(json.dumps(payload).encode()))
    assert exc.value.code == "SCHEMA_UNKNOWN_FIELD"


def test_submissions_malformed_acceptance_time_is_refused(adapter):
    payload = json.loads(fixture_bytes("sec_submissions.json"))
    payload["filings"]["recent"]["acceptanceDateTime"][0] = "not-a-timestamp"
    with pytest.raises(AdapterError) as exc:
        adapter.parse_submissions(submissions_response(json.dumps(payload).encode()))
    assert exc.value.code == "SCHEMA_TIMESTAMP_INVALID"


def test_company_facts_instant_fact_is_mapped_with_upper_bound_availability(adapter):
    request = adapter.build_company_facts_request("1")
    output = adapter.parse_company_facts(response_for(request, fixture_bytes("sec_companyfacts.json")))
    assert len(output.records) == 1
    record = output.records[0]
    assert record.field == "us-gaap:Assets"
    assert record.value == 5000
    assert record.unit == "USD"
    assert record.event_time_utc == datetime(2023, 12, 31, tzinfo=UTC)
    assert record.available_time_utc == datetime(2024, 1, 8, 23, 59, 59, tzinfo=UTC)
    assert record.vintage_time_utc == datetime(2024, 1, 8, 23, 59, 59, tzinfo=UTC)
    codes = output.note_codes()
    assert SEC_FILED_DATE_ONLY_NOT_EXACT_AVAILABILITY in codes
    assert SEC_DURATION_FACTS_SKIPPED_V1 in codes


def test_company_facts_pit_eligibility_uses_filed_upper_bound(adapter):
    request = adapter.build_company_facts_request("1")
    output = adapter.parse_company_facts(response_for(request, fixture_bytes("sec_companyfacts.json")))
    record = output.records[0]
    assert not record.eligible_at(datetime(2024, 1, 8, 12, 0, tzinfo=UTC))
    assert record.eligible_at(datetime(2024, 1, 9, 0, 0, 0, tzinfo=UTC))


def test_company_facts_unknown_fact_field_is_refused(adapter):
    payload = json.loads(fixture_bytes("sec_companyfacts.json"))
    asset_fact = payload["facts"]["us-gaap"]["Assets"]["units"]["USD"][0]
    asset_fact["suspicious"] = True
    request = adapter.build_company_facts_request("1")
    with pytest.raises(AdapterError) as exc:
        adapter.parse_company_facts(response_for(request, json.dumps(payload).encode()))
    assert exc.value.code == "SCHEMA_UNKNOWN_FIELD"


def test_company_facts_duplicate_fact_is_refused(adapter):
    payload = json.loads(fixture_bytes("sec_companyfacts.json"))
    units = payload["facts"]["us-gaap"]["Assets"]["units"]["USD"]
    units.append(dict(units[0]))
    request = adapter.build_company_facts_request("1")
    with pytest.raises(AdapterError) as exc:
        adapter.parse_company_facts(response_for(request, json.dumps(payload).encode()))
    assert exc.value.code == "DUPLICATE_RECORD_ID"


def test_two_pull_equality(adapter):
    body = fixture_bytes("sec_submissions.json")
    first = adapter.parse_submissions(submissions_response(body))
    second = adapter.parse_submissions(submissions_response(body))
    assert [record.canonical_bytes() for record in first.records] == [
        record.canonical_bytes() for record in second.records
    ]
    assert first.raw_sha256 == second.raw_sha256
