"""Offline BIS WS_CBPOL policy-rate adapter tests: no network, no wall clock."""

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from research.data_fusion.adapters.base import AdapterError, date_only_evidence
from research.data_fusion.adapters.bis import (
    BIS_AVAILABILITY_NOT_EXACT,
    BIS_EFFECTIVE_DATE_SEMANTICS,
    BIS_POLICY_RATE_NOT_CARRY_AUTHORIZATION,
    BisAdapter,
)
from research.data_fusion.authority import AuthorityStatus

from .conftest import fixture_bytes, response_for

UTC = timezone.utc


@pytest.fixture
def adapter() -> BisAdapter:
    return BisAdapter()


def policy_response(body: bytes) -> object:
    request = BisAdapter().build_policy_rate_request("US.P")
    return response_for(request, body, content_type="application/vnd.sdmx.data+json")


def evidence():
    return date_only_evidence("BIS CBPOL effective-date release evidence", date(2024, 5, 1))


def parse(adapter: BisAdapter, body: bytes | None = None):
    return adapter.parse_policy_rates(
        policy_response(body if body is not None else fixture_bytes("bis_cbpol.json")),
        release_evidence=evidence(),
    )


def test_policy_rate_request_is_deterministic_https_only(adapter):
    request = adapter.build_policy_rate_request("US.P", start_period="2024-01-01")
    assert request.url == "https://data.bis.org/api/v2/data/dataflow/BIS/WS_CBPOL/1.0/US.P"
    assert request.method == "GET"
    assert request.request_id() == adapter.build_policy_rate_request(
        "US.P", start_period="2024-01-01"
    ).request_id()
    with pytest.raises(AdapterError):
        adapter.build_policy_rate_request("US P?")
    with pytest.raises(AdapterError):
        adapter.build_policy_rate_request("US.P", end_period="01-02-2024")


def test_parse_without_evidence_fails_closed(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.parse_policy_rates(
            policy_response(fixture_bytes("bis_cbpol.json")), release_evidence=None
        )
    assert exc.value.code == "MISSING_AVAILABLE_TIME_EVIDENCE"


def test_parse_policy_rates_happy_path(adapter):
    output = parse(adapter)
    assert len(output.records) == 2
    first = output.records[0]
    assert first.entity_id == "BIS:WS_CBPOL:US.P"
    assert first.field == "policy_rate"
    assert first.value == 4.0
    assert first.unit == "PERCENT_PER_ANNUM"
    assert first.event_time_utc == datetime(2024, 3, 20, tzinfo=UTC)
    # CBPOL dates are effective dates: effective time == event time
    assert first.effective_time_utc == datetime(2024, 3, 20, tzinfo=UTC)
    assert first.available_time_utc == datetime(2024, 5, 2, 0, 0, 0, tzinfo=UTC)  # DF-ISSUE-1: next-day exclusive end
    codes = output.note_codes()
    assert BIS_EFFECTIVE_DATE_SEMANTICS in codes
    assert BIS_AVAILABILITY_NOT_EXACT in codes
    assert BIS_POLICY_RATE_NOT_CARRY_AUTHORIZATION in codes


def test_effective_date_is_not_availability_no_carry_unlock(adapter):
    output = parse(adapter)
    for record in output.records:
        # availability is strictly later than the effective date, so a record
        # is never eligible on its effective date: no backdated carry signal
        assert record.available_time_utc > record.effective_time_utc
        assert not record.eligible_at(record.event_time_utc)
        assert not record.eligible_at(datetime(2024, 5, 1, 12, 0, tzinfo=UTC))
        assert record.eligible_at(datetime(2024, 5, 2, tzinfo=UTC))


def test_missing_datasets_is_refused(adapter):
    payload = json.loads(fixture_bytes("bis_cbpol.json"))
    del payload["dataSets"]
    with pytest.raises(AdapterError) as exc:
        parse(adapter, json.dumps(payload).encode())
    assert exc.value.code == "SCHEMA_FIELD_MISSING"


def test_non_numeric_rate_is_refused(adapter):
    payload = json.loads(fixture_bytes("bis_cbpol.json"))
    payload["dataSets"][0]["series"]["0:0"]["observations"]["0"] = ["4.0", 0]
    with pytest.raises(AdapterError) as exc:
        parse(adapter, json.dumps(payload).encode())
    assert exc.value.code == "SCHEMA_VALUE_TYPE_MISMATCH"


def test_duplicate_observation_is_refused(adapter):
    payload = json.loads(fixture_bytes("bis_cbpol.json"))
    periods = payload["structure"]["dimensions"]["observation"][0]["values"]
    periods[1] = dict(periods[0])
    with pytest.raises(AdapterError) as exc:
        parse(adapter, json.dumps(payload).encode())
    assert exc.value.code == "DUPLICATE_RECORD_ID"


def test_timezones_are_utc_anchored(adapter):
    output = parse(adapter)
    for record in output.records:
        assert record.event_time_utc.utcoffset() == timedelta(0)
        assert record.effective_time_utc.utcoffset() == timedelta(0)
        assert record.available_time_utc == datetime(2024, 5, 2, 0, 0, 0, tzinfo=UTC)  # DF-ISSUE-1: next-day exclusive end


def test_two_pull_equality(adapter):
    body = fixture_bytes("bis_cbpol.json")
    first = parse(adapter, body)
    second = parse(adapter, body)
    assert [record.canonical_bytes() for record in first.records] == [
        record.canonical_bytes() for record in second.records
    ]


def test_bis_never_claims_authorization(adapter):
    assert adapter.authority_status is AuthorityStatus.DOCUMENTED_CANDIDATE
    assert adapter.authority_status is not AuthorityStatus.AUTHORIZED_INTERNAL_RESEARCH
