"""Offline FRED/ALFRED vintage adapter tests."""

import json
from datetime import datetime, timezone

import pytest

from research.data_fusion.adapters.base import AdapterError
from research.data_fusion.adapters.fred import (
    FRED_KEY_GATED_CANDIDATE,
    FRED_MISSING_VALUE_MARKED_DOT,
    FRED_VINTAGE_DATE_ONLY_NOT_EXACT_RELEASE_TIME,
    FredAdapter,
)
from research.data_fusion.authority import AuthorityStatus

from .conftest import fixture_bytes, response_for

UTC = timezone.utc


@pytest.fixture
def adapter() -> FredAdapter:
    return FredAdapter()


def test_request_requires_key_but_excludes_it_from_identity(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.build_vintagedates_request("CPIAUCSL", api_key="")
    assert exc.value.code == "CREDENTIAL_REQUIRED"
    keyed = adapter.build_vintagedates_request("CPIAUCSL", api_key="owner-secret")
    assert keyed.request_id() == adapter.build_vintagedates_request("CPIAUCSL", api_key="other-secret").request_id()
    assert "owner-secret" not in str(keyed.canonical_payload())
    assert keyed.query == (("file_type", "json"), ("series_id", "CPIAUCSL"))


def test_series_id_normalization(adapter):
    request = adapter.build_vintagedates_request("cpiaucsl", api_key="k")
    assert request.query[1] == ("series_id", "CPIAUCSL")
    with pytest.raises(AdapterError):
        adapter.build_vintagedates_request("bad series!", api_key="k")


def test_parse_vintagedates_happy_path(adapter):
    request = adapter.build_vintagedates_request("CPIAUCSL", api_key="owner-secret")
    output = adapter.parse_vintagedates(
        response_for(request, fixture_bytes("fred_vintagedates.json")), series_id="CPIAUCSL"
    )
    assert len(output.records) == 2
    first = output.records[0]
    assert first.value == "2024-01-12"
    assert first.available_time_utc == datetime(2024, 1, 12, 23, 59, 59, tzinfo=UTC)
    assert first.vintage_time_utc == datetime(2024, 1, 12, 23, 59, 59, tzinfo=UTC)
    codes = output.note_codes()
    assert FRED_VINTAGE_DATE_ONLY_NOT_EXACT_RELEASE_TIME in codes
    assert FRED_KEY_GATED_CANDIDATE in codes


def test_parse_vintagedates_malformed_entry_is_refused(adapter):
    request = adapter.build_vintagedates_request("CPIAUCSL", api_key="owner-secret")
    with pytest.raises(AdapterError) as exc:
        adapter.parse_vintagedates(response_for(request, b'["01/12/2024"]'), series_id="CPIAUCSL")
    assert exc.value.code == "SCHEMA_TIMESTAMP_INVALID"


def test_fred_error_payload_is_refused(adapter):
    request = adapter.build_vintagedates_request("CPIAUCSL", api_key="owner-secret")
    payload = json.dumps({"error_code": 400, "error_message": "Bad Request"}).encode()
    with pytest.raises(AdapterError) as exc:
        adapter.parse_vintagedates(response_for(request, payload), series_id="CPIAUCSL")
    assert exc.value.code == "UPSTREAM_ERROR_PAYLOAD"


def test_parse_alfred_observations_revisions_and_missing(adapter):
    request = adapter.build_alfred_observations_request("CPIAUCSL", api_key="owner-secret")
    output = adapter.parse_observations(
        response_for(request, fixture_bytes("fred_alfred_obs.json")), series_id="CPIAUCSL", unit="INDEX"
    )
    assert len(output.records) == 3
    by_vintage = {
        (record.event_time_utc.isoformat(), record.available_time_utc.isoformat()): record
        for record in output.records
    }
    dec_2023 = datetime(2023, 12, 1, tzinfo=UTC)
    first_vintage = by_vintage[(dec_2023.isoformat(), datetime(2024, 1, 12, 23, 59, 59, tzinfo=UTC).isoformat())]
    second_vintage = by_vintage[(dec_2023.isoformat(), datetime(2024, 2, 9, 23, 59, 59, tzinfo=UTC).isoformat())]
    assert first_vintage.value == 272.712
    assert second_vintage.value == 272.690
    # revision visible only after its own vintage availability
    assert not second_vintage.eligible_at(datetime(2024, 2, 9, 12, 0, tzinfo=UTC))
    assert second_vintage.eligible_at(datetime(2024, 2, 10, tzinfo=UTC))
    assert first_vintage.eligible_at(datetime(2024, 1, 15, tzinfo=UTC))
    missing = [record for record in output.records if record.value is None]
    assert len(missing) == 1
    assert FRED_MISSING_VALUE_MARKED_DOT in output.note_codes()


def test_observations_unknown_field_is_refused(adapter):
    request = adapter.build_alfred_observations_request("CPIAUCSL", api_key="owner-secret")
    payload = [{"realtime_start": "2024-01-12", "date": "2023-12-01", "value": "1.0", "extra": 1}]
    with pytest.raises(AdapterError) as exc:
        adapter.parse_observations(response_for(request, json.dumps(payload).encode()), series_id="CPIAUCSL", unit="INDEX")
    assert exc.value.code == "SCHEMA_UNKNOWN_FIELD"


def test_forbidden_inference_fields(adapter):
    for field in ("analyst_consensus", "wire_release_timestamp"):
        with pytest.raises(AdapterError) as exc:
            adapter.refuse_forbidden_field(field)
        assert exc.value.code == "FORBIDDEN_INFERENCE_FIELD"


def test_key_gated_authority_never_authorizes(adapter):
    assert adapter.authority_status is AuthorityStatus.CANDIDATE_NOT_AUTHORIZED
    assert adapter.entitlement_id == "api-key-required-not-provisioned"
