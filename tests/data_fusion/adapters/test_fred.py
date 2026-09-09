"""Offline FRED/ALFRED key-gated vintage adapter tests: no network, no real key."""

import json
from datetime import datetime, timedelta, timezone

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

# Fixture-only placeholder; never a real FRED key.
OWNER_SECRET = "owner-secret"


@pytest.fixture
def adapter() -> FredAdapter:
    return FredAdapter()


def test_request_requires_key_but_excludes_it_from_identity(adapter):
    for build in (adapter.build_vintagedates_request, adapter.build_alfred_observations_request):
        with pytest.raises(AdapterError) as exc:
            build("CPIAUCSL", api_key="")
        assert exc.value.code == "CREDENTIAL_REQUIRED"
        with pytest.raises(AdapterError) as exc:
            build("CPIAUCSL", api_key="   ")
        assert exc.value.code == "CREDENTIAL_REQUIRED"

    keyed = adapter.build_vintagedates_request("CPIAUCSL", api_key=OWNER_SECRET)
    other = adapter.build_vintagedates_request("CPIAUCSL", api_key="another-secret")
    # the key travels with the request...
    assert keyed.credential_query == (("api_key", OWNER_SECRET),)
    assert f"api_key={OWNER_SECRET}" in keyed.full_url()
    # ...but never enters the canonical payload or the request identity
    assert "api_key" not in keyed.canonical_payload()
    assert OWNER_SECRET not in json.dumps(keyed.canonical_payload())
    assert keyed.request_id() == other.request_id()
    assert keyed.query == (("file_type", "json"), ("series_id", "CPIAUCSL"))


def test_alfred_request_shape_and_period_validation(adapter):
    request = adapter.build_alfred_observations_request(
        "CPIAUCSL", api_key=OWNER_SECRET, realtime_start="2024-01-01", realtime_end="2024-03-01"
    )
    assert request.url == "https://api.stlouisfed.org/alfred/series/observations"
    assert ("realtime_start", "2024-01-01") in request.query
    assert ("file_type", "json") in request.query
    with pytest.raises(AdapterError):
        adapter.build_alfred_observations_request(
            "CPIAUCSL", api_key=OWNER_SECRET, realtime_start="03/01/2024"
        )


def test_series_id_normalization(adapter):
    request = adapter.build_vintagedates_request("cpiaucsl", api_key=OWNER_SECRET)
    assert request.query[1] == ("series_id", "CPIAUCSL")
    with pytest.raises(AdapterError):
        adapter.build_vintagedates_request("bad series!", api_key=OWNER_SECRET)


def test_parse_vintagedates_happy_path(adapter):
    request = adapter.build_vintagedates_request("CPIAUCSL", api_key=OWNER_SECRET)
    output = adapter.parse_vintagedates(
        response_for(request, fixture_bytes("fred_vintagedates.json")), series_id="CPIAUCSL"
    )
    assert len(output.records) == 2
    first = output.records[0]
    assert first.entity_id == "FRED:CPIAUCSL"
    assert first.field == "vintage_date"
    assert first.value == "2024-01-12"
    assert first.unit == "DATE"
    # date-only vintage -> end-of-vintage-day UTC upper bound
    assert first.available_time_utc == datetime(2024, 1, 13, 0, 0, 0, tzinfo=UTC)  # DF-ISSUE-1: next-day exclusive end
    assert first.vintage_time_utc == datetime(2024, 1, 13, 0, 0, 0, tzinfo=UTC)  # DF-ISSUE-1: next-day exclusive end
    codes = output.note_codes()
    assert FRED_VINTAGE_DATE_ONLY_NOT_EXACT_RELEASE_TIME in codes
    assert FRED_KEY_GATED_CANDIDATE in codes


def test_parse_vintagedates_malformed_and_duplicate(adapter):
    request = adapter.build_vintagedates_request("CPIAUCSL", api_key=OWNER_SECRET)
    with pytest.raises(AdapterError) as exc:
        adapter.parse_vintagedates(
            response_for(request, b'["01/12/2024"]'), series_id="CPIAUCSL"
        )
    assert exc.value.code == "SCHEMA_TIMESTAMP_INVALID"
    with pytest.raises(AdapterError) as exc:
        adapter.parse_vintagedates(
            response_for(request, b'["2024-01-12", "2024-01-12"]'), series_id="CPIAUCSL"
        )
    assert exc.value.code == "DUPLICATE_RECORD_ID"
    with pytest.raises(AdapterError) as exc:
        adapter.parse_vintagedates(response_for(request, b"[]"), series_id="CPIAUCSL")
    assert exc.value.code == "SCHEMA_VALUE_TYPE_MISMATCH"


def test_fred_error_payload_is_refused(adapter):
    request = adapter.build_vintagedates_request("CPIAUCSL", api_key=OWNER_SECRET)
    payload = json.dumps({"error_code": 400, "error_message": "Bad Request"}).encode()
    with pytest.raises(AdapterError) as exc:
        adapter.parse_vintagedates(response_for(request, payload), series_id="CPIAUCSL")
    assert exc.value.code == "UPSTREAM_ERROR_PAYLOAD"

    request = adapter.build_alfred_observations_request("CPIAUCSL", api_key=OWNER_SECRET)
    with pytest.raises(AdapterError) as exc:
        adapter.parse_observations(response_for(request, payload), series_id="CPIAUCSL", unit="INDEX")
    assert exc.value.code == "UPSTREAM_ERROR_PAYLOAD"


def test_parse_observations_revisions_are_append_only(adapter):
    request = adapter.build_alfred_observations_request(
        "CPIAUCSL", api_key=OWNER_SECRET, realtime_start="2024-01-01", realtime_end="2024-03-01"
    )
    output = adapter.parse_observations(
        response_for(request, fixture_bytes("fred_alfred_obs.json")), series_id="CPIAUCSL", unit="INDEX"
    )
    assert len(output.records) == 3
    by_vintage = {
        (record.event_time_utc.isoformat(), record.available_time_utc.isoformat()): record
        for record in output.records
    }
    dec_2023 = datetime(2023, 12, 1, tzinfo=UTC)
    first_vintage = by_vintage[
        (dec_2023.isoformat(), datetime(2024, 1, 13, 0, 0, 0, tzinfo=UTC).isoformat())  # DF-ISSUE-1: next-day exclusive end
    ]
    second_vintage = by_vintage[
        (dec_2023.isoformat(), datetime(2024, 2, 10, 0, 0, 0, tzinfo=UTC).isoformat())  # DF-ISSUE-1: next-day exclusive end
    ]
    # two vintages of the same observation date: two separate records,
    # both kept, never an overwrite
    assert first_vintage.value == 272.712
    assert second_vintage.value == 272.690
    assert first_vintage.canonical_bytes() != second_vintage.canonical_bytes()
    # a revision is only eligible after its own vintage upper bound
    assert not second_vintage.eligible_at(datetime(2024, 2, 9, 12, 0, tzinfo=UTC))
    assert second_vintage.eligible_at(datetime(2024, 2, 10, tzinfo=UTC))
    assert first_vintage.eligible_at(datetime(2024, 1, 15, tzinfo=UTC))
    missing = [record for record in output.records if record.value is None]
    assert len(missing) == 1
    assert FRED_MISSING_VALUE_MARKED_DOT in output.note_codes()


def test_observations_unknown_fields_are_refused(adapter):
    request = adapter.build_alfred_observations_request("CPIAUCSL", api_key=OWNER_SECRET)
    payload = {"observations": [
        {"realtime_start": "2024-01-12", "date": "2023-12-01", "value": "1.0", "extra": 1}
    ]}
    with pytest.raises(AdapterError) as exc:
        adapter.parse_observations(
            response_for(request, json.dumps(payload).encode()), series_id="CPIAUCSL", unit="INDEX"
        )
    assert exc.value.code == "SCHEMA_UNKNOWN_FIELD"

    # a non-object payload is likewise refused (documented shape is an envelope)
    with pytest.raises(AdapterError) as exc:
        adapter.parse_observations(
            response_for(request, json.dumps([{"date": "2023-12-01", "value": "1.0"}]).encode()),
            series_id="CPIAUCSL",
            unit="INDEX",
        )
    assert exc.value.code == "SCHEMA_VALUE_TYPE_MISMATCH"

    envelope = json.loads(fixture_bytes("fred_alfred_obs.json"))
    envelope["surprise_key"] = 1
    with pytest.raises(AdapterError) as exc:
        adapter.parse_observations(
            response_for(request, json.dumps(envelope).encode()), series_id="CPIAUCSL", unit="INDEX"
        )
    assert exc.value.code == "SCHEMA_UNKNOWN_FIELD"


def test_observations_non_numeric_value_is_refused(adapter):
    request = adapter.build_alfred_observations_request("CPIAUCSL", api_key=OWNER_SECRET)
    payload = [{"realtime_start": "2024-01-12", "date": "2023-12-01", "value": "N/A"}]
    with pytest.raises(AdapterError) as exc:
        adapter.parse_observations(
            response_for(request, json.dumps(payload).encode()), series_id="CPIAUCSL", unit="INDEX"
        )
    assert exc.value.code == "SCHEMA_VALUE_TYPE_MISMATCH"


def test_observations_timezone_anchor_and_two_pull_equality(adapter):
    request = adapter.build_alfred_observations_request("CPIAUCSL", api_key=OWNER_SECRET)
    body = fixture_bytes("fred_alfred_obs.json")
    output = adapter.parse_observations(response_for(request, body), series_id="CPIAUCSL", unit="INDEX")
    for record in output.records:
        assert record.available_time_utc.utcoffset() == timedelta(0)
        assert record.available_time_utc.hour == 0 and record.available_time_utc.minute == 0  # DF-ISSUE-1: next-day exclusive end
    second = adapter.parse_observations(response_for(request, body), series_id="CPIAUCSL", unit="INDEX")
    assert [record.canonical_bytes() for record in output.records] == [
        record.canonical_bytes() for record in second.records
    ]


def test_forbidden_inference_fields(adapter):
    for field in ("analyst_consensus", "wire_release_timestamp"):
        with pytest.raises(AdapterError) as exc:
            adapter.refuse_forbidden_field(field)
        assert exc.value.code == "FORBIDDEN_INFERENCE_FIELD"


def test_key_gated_source_is_never_authorized(adapter):
    assert adapter.authority_status is AuthorityStatus.CANDIDATE_NOT_AUTHORIZED
    assert adapter.authority_status is not AuthorityStatus.AUTHORIZED_INTERNAL_RESEARCH
    assert adapter.entitlement_id == "api-key-required-not-provisioned"
