"""Offline BIS WS_CBPOL adapter tests."""

import json
from datetime import date, datetime, timezone

import pytest

from research.data_fusion.adapters.base import AdapterError, date_only_evidence
from research.data_fusion.adapters.bis import (
    BIS_EFFECTIVE_DATE_SEMANTICS,
    BIS_POLICY_RATE_NOT_CARRY_AUTHORIZATION,
    BisAdapter,
)

from .conftest import fixture_bytes, response_for

UTC = timezone.utc


@pytest.fixture
def adapter() -> BisAdapter:
    return BisAdapter()


def policy_response(body: bytes):
    request = BisAdapter().build_policy_rate_request("US.P")
    return response_for(request, body, content_type="application/vnd.sdmx.data+json")


def evidence():
    return date_only_evidence("BIS CBPOL release evidence", date(2024, 5, 1))


def test_policy_rate_request_is_deterministic_https_only(adapter):
    request = adapter.build_policy_rate_request("US.P", start_period="2024-01-01")
    assert request.url == "https://data.bis.org/api/v2/data/dataflow/BIS/WS_CBPOL/1.0/US.P"
    assert request.request_id() == adapter.build_policy_rate_request("US.P", start_period="2024-01-01").request_id()
    with pytest.raises(AdapterError):
        adapter.build_policy_rate_request("US P?")


def test_parse_without_evidence_fails_closed(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.parse_policy_rates(policy_response(fixture_bytes("bis_cbpol.json")), release_evidence=None)
    assert exc.value.code == "MISSING_AVAILABLE_TIME_EVIDENCE"


def test_parse_policy_rates_happy_path(adapter):
    output = adapter.parse_policy_rates(policy_response(fixture_bytes("bis_cbpol.json")), release_evidence=evidence())
    assert len(output.records) == 2
    first = output.records[0]
    assert first.entity_id == "BIS:WS_CBPOL:US.P"
    assert first.field == "policy_rate"
    assert first.value == 4.0
    assert first.event_time_utc == datetime(2024, 3, 20, tzinfo=UTC)
    assert first.effective_time_utc == datetime(2024, 3, 20, tzinfo=UTC)
    assert first.available_time_utc == datetime(2024, 5, 1, 23, 59, 59, tzinfo=UTC)
    codes = output.note_codes()
    assert BIS_EFFECTIVE_DATE_SEMANTICS in codes
    assert BIS_POLICY_RATE_NOT_CARRY_AUTHORIZATION in codes
    # carry strategy would need availability at effective time; the record only
    # becomes eligible after the conservative evidence upper bound
    assert not first.eligible_at(datetime(2024, 4, 1, tzinfo=UTC))


def test_parse_policy_rates_malformed_schema_is_refused(adapter):
    payload = json.loads(fixture_bytes("bis_cbpol.json"))
    del payload["dataSets"]
    with pytest.raises(AdapterError) as exc:
        adapter.parse_policy_rates(
            policy_response(json.dumps(payload).encode()), release_evidence=evidence()
        )
    assert exc.value.code == "SCHEMA_FIELD_MISSING"


def test_parse_policy_rates_non_numeric_rate_is_refused(adapter):
    payload = json.loads(fixture_bytes("bis_cbpol.json"))
    payload["dataSets"][0]["series"]["0:0"]["observations"]["0"] = ["4.0", 0]
    with pytest.raises(AdapterError) as exc:
        adapter.parse_policy_rates(
            policy_response(json.dumps(payload).encode()), release_evidence=evidence()
        )
    assert exc.value.code == "SCHEMA_VALUE_TYPE_MISMATCH"


def test_parse_policy_rates_conflicting_evidence_basis_is_recorded(adapter):
    output = adapter.parse_policy_rates(
        policy_response(fixture_bytes("bis_cbpol.json")), release_evidence=evidence()
    )
    for record in output.records:
        assert record.available_time_utc == datetime(2024, 5, 1, 23, 59, 59, tzinfo=UTC)
