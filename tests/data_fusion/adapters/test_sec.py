"""Offline tests for the SEC EDGAR adapter: fixtures only, no network.

Every test runs the adapter against hand-written fixture bytes via the
shared offline harness (``response_for``).  Malformed, duplicate, timezone
and revision cases are derived from the committed fixtures by mutation so
the fixture set stays minimal.
"""

import json
from datetime import date, datetime, timezone

import pytest

from research.data_fusion.adapters.base import (
    AdapterError,
    AvailabilityBasis,
    CONTENT_TYPE_UNEXPECTED,
    DUPLICATE_RECORD_ID,
    HTTP_STATUS_UNEXPECTED,
    NON_EXACT_AVAILABLE_TIME_FORBIDDEN,
    RequestSpec,
    SCHEMA_FIELD_MISSING,
    SCHEMA_INVARIANT_VIOLATED,
    SCHEMA_TIMESTAMP_INVALID,
    SCHEMA_UNKNOWN_FIELD,
    SCHEMA_VALUE_TYPE_MISMATCH,
    end_of_utc_day,
    midnight_utc,
    timings_from_evidence,
    date_only_evidence,
)
from research.data_fusion.authority import AuthorityStatus
from research.data_fusion.adapters.sec import (
    SEC_ACCEPTANCE_TIME_NOT_DISSEMINATION_PROOF,
    SEC_DURATION_FACTS_SKIPPED_V1,
    SEC_FILED_DATE_ONLY_NOT_EXACT_AVAILABILITY,
    SecAdapter,
)

from .conftest import RETRIEVED_TIME, fixture_bytes, fixture_text, response_for

UTC = timezone.utc

SUBMISSIONS_FIXTURE = "sec_submissions.json"
COMPANY_FACTS_FIXTURE = "sec_companyfacts.json"


@pytest.fixture
def adapter() -> SecAdapter:
    return SecAdapter()


def submissions_response(adapter: SecAdapter, body: bytes, **kwargs) -> object:
    request = adapter.build_submissions_request("1")
    return response_for(request, body, **kwargs)


def company_facts_response(adapter: SecAdapter, body: bytes, **kwargs) -> object:
    request = adapter.build_company_facts_request("1")
    return response_for(request, body, **kwargs)


def mutated(name: str, mutate) -> bytes:
    payload = json.loads(fixture_text(name))
    mutate(payload)
    return json.dumps(payload, indent=2).encode("utf-8")


# ---------------------------------------------------------------------------
# Request identity, fair access, entitlement
# ---------------------------------------------------------------------------


def test_request_identity_deterministic_across_cik_spellings():
    adapter = SecAdapter()
    a = adapter.build_submissions_request("320193")
    b = adapter.build_submissions_request(320193)
    c = adapter.build_submissions_request("0000320193")
    d = adapter.build_company_facts_request("cik320193")
    assert a.url == b.url == c.url == "https://data.sec.gov/submissions/CIK0000320193.json"
    assert a.request_id() == b.request_id() == c.request_id()
    assert d.url == "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"
    assert a.request_id() != d.request_id()


@pytest.mark.parametrize("bad", ["12A4", "", "12345678901", -7, True, None, "320.193"])
def test_malformed_cik_refused(bad):
    with pytest.raises(AdapterError) as err:
        SecAdapter().build_submissions_request(bad)
    assert err.value.code == SCHEMA_INVARIANT_VIOLATED


def test_requests_are_https_get_with_declared_user_agent_and_no_credentials():
    adapter = SecAdapter()
    for request in (
        adapter.build_submissions_request("1"),
        adapter.build_company_facts_request("1"),
    ):
        assert request.url.startswith("https://")
        assert request.method == "GET"
        assert request.query == () and request.credential_query == ()
        user_agents = [value for name, value in request.headers if name == "User-Agent"]
        assert len(user_agents) == 1
        forbidden = {"authorization", "cookie", "x-api-key", "api-key"}
        assert all(name.lower() not in forbidden for name, _ in request.headers)


def test_default_rate_limit_encodes_sec_fair_access():
    policy = SecAdapter.default_rate_limit()
    assert policy.source_id == "SEC_EDGAR"
    assert "10 requests/second" in policy.documented_limit
    assert policy.min_interval_seconds >= 0.1
    assert 429 in policy.retry_status_codes


def test_authority_is_documented_candidate_only():
    assert SecAdapter.authority_status == AuthorityStatus.DOCUMENTED_CANDIDATE
    assert SecAdapter.authority_status != AuthorityStatus.AUTHORIZED_INTERNAL_RESEARCH


# ---------------------------------------------------------------------------
# Submissions happy path and point-in-time semantics
# ---------------------------------------------------------------------------


def test_submissions_happy_path(adapter):
    output = adapter.parse_submissions(submissions_response(adapter, fixture_bytes(SUBMISSIONS_FIXTURE)))
    assert output.source_id == "SEC_EDGAR"
    assert output.dataset_id == "submissions"
    assert len(output.records) == 2
    first, second = output.records
    assert all(r.entity_id == "CIK0000000001" for r in output.records)
    assert all(r.field == "filing" for r in output.records)
    assert all(r.unit == "ACCESSION_ID" for r in output.records)
    assert first.value == "0000000001-24-000001"
    assert second.value == "0000000001-24-000002"
    assert output.raw_sha256 == output.raw_sha256  # stable within output
    assert len(output.raw_sha256) == 64


def test_submissions_availability_is_end_of_filed_day_upper_bound(adapter):
    output = adapter.parse_submissions(submissions_response(adapter, fixture_bytes(SUBMISSIONS_FIXTURE)))
    first, second = output.records
    assert first.event_time_utc == datetime(2024, 1, 3, 14, 30, tzinfo=UTC)
    assert first.available_time_utc == datetime(2024, 1, 4, 0, 0, 0, tzinfo=UTC)  # DF-ISSUE-1: next-day exclusive end
    assert second.event_time_utc == datetime(2024, 1, 8, tzinfo=UTC)
    assert second.available_time_utc == datetime(2024, 1, 9, 0, 0, 0, tzinfo=UTC)  # DF-ISSUE-1: next-day exclusive end
    for record in output.records:
        # Separated PIT roles; retrieved_time never substitutes availability.
        assert record.available_time_utc == record.vintage_time_utc
        assert record.available_time_utc < record.retrieved_time_utc == RETRIEVED_TIME
        assert record.effective_time_utc is not None
        assert record.effective_time_utc != record.retrieved_time_utc


def test_submissions_acceptance_is_event_not_availability(adapter):
    output = adapter.parse_submissions(submissions_response(adapter, fixture_bytes(SUBMISSIONS_FIXTURE)))
    first, second = output.records
    # Accepted 14:30Z on the filed day: availability stays the EOD upper bound.
    assert first.event_time_utc == datetime(2024, 1, 3, 14, 30, tzinfo=UTC)
    assert first.available_time_utc == end_of_utc_day(date(2024, 1, 3))
    # No acceptance time: event falls back to the filed-day midnight.
    assert second.event_time_utc == midnight_utc(date(2024, 1, 8))
    assert second.available_time_utc == end_of_utc_day(date(2024, 1, 8))
    assert set(output.note_codes()) == {
        SEC_FILED_DATE_ONLY_NOT_EXACT_AVAILABILITY,
        SEC_ACCEPTANCE_TIME_NOT_DISSEMINATION_PROOF,
    }


def test_submissions_filing_date_ordering(adapter):
    output = adapter.parse_submissions(submissions_response(adapter, fixture_bytes(SUBMISSIONS_FIXTURE)))
    first, second = output.records
    assert first.available_time_utc < second.available_time_utc
    assert first.vintage_time_utc < second.vintage_time_utc


def test_filed_dates_can_never_be_exact_market_availability():
    timings = timings_from_evidence(
        midnight_utc(date(2024, 1, 3)),
        date_only_evidence("SEC submissions filingDate (date only)", date(2024, 1, 3)),
    )
    assert timings.availability_basis is AvailabilityBasis.DATE_ONLY_UPPER_BOUND
    with pytest.raises(AdapterError) as err:
        timings.require_exact_availability()
    assert err.value.code == NON_EXACT_AVAILABLE_TIME_FORBIDDEN


# ---------------------------------------------------------------------------
# Submissions schema rejection
# ---------------------------------------------------------------------------


def test_duplicate_accession_rejected(adapter):
    def duplicate(payload):
        recent = payload["filings"]["recent"]
        recent["accessionNumber"][1] = recent["accessionNumber"][0]

    body = mutated(SUBMISSIONS_FIXTURE, duplicate)
    with pytest.raises(AdapterError) as err:
        adapter.parse_submissions(submissions_response(adapter, body))
    assert err.value.code == DUPLICATE_RECORD_ID


def test_unknown_column_rejected(adapter):
    def add_unknown(payload):
        payload["filings"]["recent"]["bogusColumn"] = ["x", "y"]

    body = mutated(SUBMISSIONS_FIXTURE, add_unknown)
    with pytest.raises(AdapterError) as err:
        adapter.parse_submissions(submissions_response(adapter, body))
    assert err.value.code == SCHEMA_UNKNOWN_FIELD


def test_missing_required_column_rejected(adapter):
    def drop_form(payload):
        del payload["filings"]["recent"]["form"]

    body = mutated(SUBMISSIONS_FIXTURE, drop_form)
    with pytest.raises(AdapterError) as err:
        adapter.parse_submissions(submissions_response(adapter, body))
    assert err.value.code == SCHEMA_FIELD_MISSING


def test_unequal_column_lengths_rejected(adapter):
    def truncate(payload):
        payload["filings"]["recent"]["primaryDocument"] = ["a8k.htm"]

    body = mutated(SUBMISSIONS_FIXTURE, truncate)
    with pytest.raises(AdapterError) as err:
        adapter.parse_submissions(submissions_response(adapter, body))
    assert err.value.code == SCHEMA_INVARIANT_VIOLATED


def test_malformed_filing_date_rejected(adapter):
    def bad_date(payload):
        payload["filings"]["recent"]["filingDate"][0] = "01/03/2024"

    body = mutated(SUBMISSIONS_FIXTURE, bad_date)
    with pytest.raises(AdapterError) as err:
        adapter.parse_submissions(submissions_response(adapter, body))
    assert err.value.code == SCHEMA_TIMESTAMP_INVALID


@pytest.mark.parametrize(
    "bad_acceptance",
    [
        "2024-01-03T14:30:00",  # naive, no offset
        "2024-01-03T09:30:00-05:00",  # aware but non-UTC
        "not-a-timestamp",  # not ISO-8601 at all
    ],
)
def test_non_utc_or_malformed_acceptance_time_rejected(adapter, bad_acceptance):
    def swap(payload):
        payload["filings"]["recent"]["acceptanceDateTime"][0] = bad_acceptance

    body = mutated(SUBMISSIONS_FIXTURE, swap)
    with pytest.raises(AdapterError) as err:
        adapter.parse_submissions(submissions_response(adapter, body))
    assert err.value.code == SCHEMA_TIMESTAMP_INVALID


def test_acceptance_after_filed_day_bound_rejected(adapter):
    def late(payload):
        payload["filings"]["recent"]["acceptanceDateTime"][0] = "2024-01-04T02:00:00.000Z"

    body = mutated(SUBMISSIONS_FIXTURE, late)
    with pytest.raises(AdapterError) as err:
        adapter.parse_submissions(submissions_response(adapter, body))
    assert err.value.code == SCHEMA_INVARIANT_VIOLATED


def test_body_cik_mismatching_url_rejected(adapter):
    def swap_cik(payload):
        payload["cik"] = 2

    body = mutated(SUBMISSIONS_FIXTURE, swap_cik)
    with pytest.raises(AdapterError) as err:
        adapter.parse_submissions(submissions_response(adapter, body))
    assert err.value.code == SCHEMA_INVARIANT_VIOLATED


def test_wrong_content_type_rejected(adapter):
    with pytest.raises(AdapterError) as err:
        adapter.parse_submissions(
            submissions_response(adapter, fixture_bytes(SUBMISSIONS_FIXTURE), content_type="application/xml")
        )
    assert err.value.code == CONTENT_TYPE_UNEXPECTED


def test_http_error_rejected(adapter):
    with pytest.raises(AdapterError) as err:
        adapter.parse_submissions(
            submissions_response(adapter, b"{}", status=404, reason="Not Found")
        )
    assert err.value.code == HTTP_STATUS_UNEXPECTED


# ---------------------------------------------------------------------------
# Company facts happy path, revisions, duration skip
# ---------------------------------------------------------------------------


def test_company_facts_happy_path(adapter):
    output = adapter.parse_company_facts(company_facts_response(adapter, fixture_bytes(COMPANY_FACTS_FIXTURE)))
    assert output.dataset_id == "company_facts"
    assert all(r.entity_id == "CIK0000000001" for r in output.records)
    by_field = {(r.field, r.value): r for r in output.records}
    assert len(output.records) == 3  # 2 Assets instants + 1 dei instant
    dei = by_field[("dei:EntityCommonStockSharesOutstanding", 1000)]
    assert dei.unit == "shares"
    assert dei.event_time_utc == datetime(2023, 12, 31, tzinfo=UTC)
    assert dei.available_time_utc == datetime(2024, 1, 4, 0, 0, 0, tzinfo=UTC)  # DF-ISSUE-1: next-day exclusive end
    original = by_field[("us-gaap:Assets", 5000)]
    assert original.unit == "USD"
    assert original.available_time_utc == datetime(2024, 1, 9, 0, 0, 0, tzinfo=UTC)  # DF-ISSUE-1: next-day exclusive end


def test_duration_facts_skipped_with_note(adapter):
    output = adapter.parse_company_facts(company_facts_response(adapter, fixture_bytes(COMPANY_FACTS_FIXTURE)))
    assert all(not r.field.endswith(":Revenues") for r in output.records)
    skip_notes = [n for n in output.notes if n.code == SEC_DURATION_FACTS_SKIPPED_V1]
    assert len(skip_notes) == 1
    assert "1 duration facts" in skip_notes[0].message
    assert SEC_FILED_DATE_ONLY_NOT_EXACT_AVAILABILITY in output.note_codes()


def test_revision_availability_follows_filed_date(adapter):
    output = adapter.parse_company_facts(company_facts_response(adapter, fixture_bytes(COMPANY_FACTS_FIXTURE)))
    assets = sorted(
        (r for r in output.records if r.field == "us-gaap:Assets"),
        key=lambda r: r.available_time_utc,
    )
    assert [r.value for r in assets] == [5000, 5100]
    assert assets[0].available_time_utc == datetime(2024, 1, 9, 0, 0, 0, tzinfo=UTC)  # DF-ISSUE-1: next-day exclusive end
    assert assets[1].available_time_utc == datetime(2024, 4, 16, 0, 0, 0, tzinfo=UTC)  # DF-ISSUE-1: next-day exclusive end
    # Same period end event for both vintages; availability strictly ordered.
    assert assets[0].event_time_utc == assets[1].event_time_utc == datetime(2023, 12, 31, tzinfo=UTC)
    assert assets[0].available_time_utc < assets[1].available_time_utc <= RETRIEVED_TIME


# ---------------------------------------------------------------------------
# Company facts schema rejection
# ---------------------------------------------------------------------------


def test_duplicate_fact_rejected(adapter):
    def duplicate(payload):
        units = payload["facts"]["us-gaap"]["Assets"]["units"]["USD"]
        units.append(dict(units[0]))

    body = mutated(COMPANY_FACTS_FIXTURE, duplicate)
    with pytest.raises(AdapterError) as err:
        adapter.parse_company_facts(company_facts_response(adapter, body))
    assert err.value.code == DUPLICATE_RECORD_ID


def test_fact_unknown_key_rejected(adapter):
    def add_unknown(payload):
        payload["facts"]["us-gaap"]["Assets"]["units"]["USD"][0]["bogus"] = 1

    body = mutated(COMPANY_FACTS_FIXTURE, add_unknown)
    with pytest.raises(AdapterError) as err:
        adapter.parse_company_facts(company_facts_response(adapter, body))
    assert err.value.code == SCHEMA_UNKNOWN_FIELD


def test_fact_meta_unknown_key_rejected(adapter):
    def add_unknown(payload):
        payload["facts"]["us-gaap"]["Assets"]["bogusMeta"] = "x"

    body = mutated(COMPANY_FACTS_FIXTURE, add_unknown)
    with pytest.raises(AdapterError) as err:
        adapter.parse_company_facts(company_facts_response(adapter, body))
    assert err.value.code == SCHEMA_UNKNOWN_FIELD


def test_fact_missing_required_key_rejected(adapter):
    def drop_accn(payload):
        del payload["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"][0]["accn"]

    body = mutated(COMPANY_FACTS_FIXTURE, drop_accn)
    with pytest.raises(AdapterError) as err:
        adapter.parse_company_facts(company_facts_response(adapter, body))
    assert err.value.code == SCHEMA_FIELD_MISSING


def test_fact_malformed_period_end_rejected(adapter):
    def bad_end(payload):
        payload["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"][0]["end"] = "2023-13-45"

    body = mutated(COMPANY_FACTS_FIXTURE, bad_end)
    with pytest.raises(AdapterError) as err:
        adapter.parse_company_facts(company_facts_response(adapter, body))
    assert err.value.code == SCHEMA_TIMESTAMP_INVALID


def test_fact_filed_before_period_end_rejected(adapter):
    def time_travel(payload):
        payload["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"][0]["filed"] = "2023-06-30"

    body = mutated(COMPANY_FACTS_FIXTURE, time_travel)
    with pytest.raises(AdapterError) as err:
        adapter.parse_company_facts(company_facts_response(adapter, body))
    assert err.value.code == SCHEMA_INVARIANT_VIOLATED


def test_fact_non_integer_fy_rejected(adapter):
    def bad_fy(payload):
        payload["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"][0]["fy"] = "2024"

    body = mutated(COMPANY_FACTS_FIXTURE, bad_fy)
    with pytest.raises(AdapterError) as err:
        adapter.parse_company_facts(company_facts_response(adapter, body))
    assert err.value.code == SCHEMA_VALUE_TYPE_MISMATCH


def test_fact_malformed_accession_rejected(adapter):
    def bad_accn(payload):
        payload["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"][0]["accn"] = "1-24-1"

    body = mutated(COMPANY_FACTS_FIXTURE, bad_accn)
    with pytest.raises(AdapterError) as err:
        adapter.parse_company_facts(company_facts_response(adapter, body))
    assert err.value.code == SCHEMA_INVARIANT_VIOLATED


def test_company_facts_wrong_content_type_rejected(adapter):
    with pytest.raises(AdapterError) as err:
        adapter.parse_company_facts(
            company_facts_response(adapter, fixture_bytes(COMPANY_FACTS_FIXTURE), content_type="text/html")
        )
    assert err.value.code == CONTENT_TYPE_UNEXPECTED


# ---------------------------------------------------------------------------
# Determinism: two pulls of the same bytes produce identical canonical output
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "builder", "fixture_name"),
    [
        ("parse_submissions", "build_submissions_request", SUBMISSIONS_FIXTURE),
        ("parse_company_facts", "build_company_facts_request", COMPANY_FACTS_FIXTURE),
    ],
)
def test_two_pull_equality(adapter, method, builder, fixture_name):
    pulls = []
    for _ in range(2):
        request: RequestSpec = getattr(adapter, builder)("1")
        response = response_for(request, fixture_bytes(fixture_name))
        output = getattr(adapter, method)(response)
        pulls.append(
            (
                [record.canonical_bytes() for record in output.records],
                output.note_codes(),
                output.raw_sha256,
                output.parser_version,
            )
        )
    assert pulls[0] == pulls[1]
