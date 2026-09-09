"""Offline ECB Data API (SDMX-JSON) adapter tests: no network, no wall clock."""

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from research.data_fusion.adapters.base import (
    AdapterError,
    AvailabilityBasis,
    ReleaseEvidence,
    date_only_evidence,
)
from research.data_fusion.adapters.ecb import (
    ECB_AVAILABILITY_NOT_EXACT,
    ECB_DATA_NOT_CARRY_AUTHORIZATION,
    ECB_PREPARED_TIME_NOT_AVAILABILITY_PROOF,
    EcbAdapter,
)
from research.data_fusion.authority import AuthorityStatus

from .conftest import fixture_bytes, response_for

UTC = timezone.utc


@pytest.fixture
def adapter() -> EcbAdapter:
    return EcbAdapter()


def series_response(body: bytes) -> object:
    request = EcbAdapter().build_series_request("EXR", "D.USD.EUR.SP00.A")
    return response_for(request, body, content_type="application/vnd.sdmx.data+json")


def evidence() -> ReleaseEvidence:
    return date_only_evidence("ECB reference-rate publication calendar", date(2024, 1, 3))


def parse(adapter: EcbAdapter, body: bytes | None = None) -> object:
    return adapter.parse_series(
        series_response(body if body is not None else fixture_bytes("ecb_sdmx_exr.json")),
        dataflow="EXR",
        release_evidence=evidence(),
        unit="USD_PER_EUR",
    )


def test_series_request_is_deterministic_https_only(adapter):
    request = adapter.build_series_request("EXR", "D.USD.EUR.SP00.A", start_period="2024-01-01")
    assert request.url == "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"
    assert request.method == "GET"
    assert request.request_id() == adapter.build_series_request(
        "exr", " D.USD.EUR.SP00.A ", start_period="2024-01-01"
    ).request_id()
    assert request.request_id() == request.request_id()  # stable across calls
    with pytest.raises(AdapterError):
        adapter.build_series_request("EXR", "bad key with spaces")
    with pytest.raises(AdapterError):
        adapter.build_series_request("EX", "D.USD.EUR.SP00.A", start_period="2024-13-01")


def test_parse_without_release_evidence_fails_closed(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.parse_series(
            series_response(fixture_bytes("ecb_sdmx_exr.json")),
            dataflow="EXR",
            release_evidence=None,
            unit="USD_PER_EUR",
        )
    assert exc.value.code == "MISSING_AVAILABLE_TIME_EVIDENCE"


def test_parse_series_happy_path(adapter):
    output = parse(adapter)
    assert len(output.records) == 2
    first = output.records[0]
    assert first.entity_id == "ECB:EXR:D.USD.EUR.SP00.A"
    assert first.field == "observation"
    assert first.value == 1.0951
    assert first.unit == "USD_PER_EUR"
    assert first.event_time_utc == datetime(2024, 1, 2, tzinfo=UTC)
    assert first.effective_time_utc == datetime(2024, 1, 2, tzinfo=UTC)
    assert first.available_time_utc == datetime(2024, 1, 4, 0, 0, 0, tzinfo=UTC)  # DF-ISSUE-1: next-day exclusive end
    assert output.raw_sha256 == series_response(fixture_bytes("ecb_sdmx_exr.json")).sha256_hex()
    codes = output.note_codes()
    assert ECB_PREPARED_TIME_NOT_AVAILABILITY_PROOF in codes
    assert ECB_AVAILABILITY_NOT_EXACT in codes
    assert ECB_DATA_NOT_CARRY_AUTHORIZATION in codes


def test_prepared_time_is_never_used_as_availability(adapter):
    output = parse(adapter)
    prepared = datetime(2024, 1, 3, 15, 10, tzinfo=UTC)
    for record in output.records:
        # the record only becomes eligible after the conservative upper bound,
        # never at the SDMX message's own metadata instant
        assert record.available_time_utc != prepared
        assert record.available_time_utc > prepared
        assert not record.eligible_at(prepared)
        assert record.eligible_at(datetime(2024, 1, 4, tzinfo=UTC))


def test_missing_or_invalid_prepared_is_refused(adapter):
    payload = json.loads(fixture_bytes("ecb_sdmx_exr.json"))
    del payload["header"]["prepared"]
    with pytest.raises(AdapterError) as exc:
        parse(adapter, json.dumps(payload).encode())
    assert exc.value.code == "SCHEMA_FIELD_MISSING"

    payload = json.loads(fixture_bytes("ecb_sdmx_exr.json"))
    payload["header"]["prepared"] = "not-a-timestamp"
    with pytest.raises(AdapterError) as exc:
        parse(adapter, json.dumps(payload).encode())
    assert exc.value.code == "SCHEMA_TIMESTAMP_INVALID"


def test_duplicate_observation_is_refused(adapter):
    payload = json.loads(fixture_bytes("ecb_sdmx_exr.json"))
    periods = payload["structure"]["dimensions"]["observation"][0]["values"]
    periods[1] = dict(periods[0])  # two observation positions share one TIME_PERIOD
    with pytest.raises(AdapterError) as exc:
        parse(adapter, json.dumps(payload).encode())
    assert exc.value.code == "DUPLICATE_RECORD_ID"


def test_missing_structure_or_datasets_is_refused(adapter):
    payload = json.loads(fixture_bytes("ecb_sdmx_exr.json"))
    del payload["structure"]
    with pytest.raises(AdapterError) as exc:
        parse(adapter, json.dumps(payload).encode())
    assert exc.value.code == "SCHEMA_FIELD_MISSING"

    payload = json.loads(fixture_bytes("ecb_sdmx_exr.json"))
    del payload["dataSets"]
    with pytest.raises(AdapterError) as exc:
        parse(adapter, json.dumps(payload).encode())
    assert exc.value.code == "SCHEMA_FIELD_MISSING"


def test_non_numeric_observation_is_refused(adapter):
    payload = json.loads(fixture_bytes("ecb_sdmx_exr.json"))
    payload["dataSets"][0]["series"]["0:0:0:0:0"]["observations"]["0"] = ["1.0951", 0]
    with pytest.raises(AdapterError) as exc:
        parse(adapter, json.dumps(payload).encode())
    assert exc.value.code == "SCHEMA_VALUE_TYPE_MISMATCH"


def test_multi_series_payload_is_refused(adapter):
    payload = json.loads(fixture_bytes("ecb_sdmx_exr.json"))
    series = payload["dataSets"][0]["series"]
    series["1:0:0:0:0"] = {"observations": {"0": [1.1, 0]}}
    with pytest.raises(AdapterError) as exc:
        parse(adapter, json.dumps(payload).encode())
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_timezones_are_utc_anchored(adapter):
    output = parse(adapter)
    for record in output.records:
        assert record.available_time_utc.utcoffset() == timedelta(0)
        assert record.available_time_utc == datetime(2024, 1, 4, 0, 0, 0, tzinfo=UTC)  # DF-ISSUE-1: next-day exclusive end
    # date-only evidence must be anchored to UTC end of day; naive or
    # non-UTC evidence instants are refused outright
    with pytest.raises(ValueError):
        ReleaseEvidence(
            captured_from="local wall clock",
            available_time_utc=datetime(2024, 1, 4, 0, 0, 0),  # DF-ISSUE-1: next-day exclusive end,
            basis=AvailabilityBasis.EXACT,
        )
    with pytest.raises(ValueError):
        ReleaseEvidence(
            captured_from="local wall clock",
            available_time_utc=datetime(2024, 1, 4, 0, 0, 0, tzinfo=timezone(timedelta(hours=7))),  # DF-ISSUE-1: next-day exclusive end,
            basis=AvailabilityBasis.EXACT,
        )


def test_two_pull_equality(adapter):
    body = fixture_bytes("ecb_sdmx_exr.json")
    first = parse(adapter, body)
    second = parse(adapter, body)
    assert [record.canonical_bytes() for record in first.records] == [
        record.canonical_bytes() for record in second.records
    ]


def test_ecb_never_claims_authorization(adapter):
    assert adapter.authority_status is AuthorityStatus.DOCUMENTED_CANDIDATE
    assert adapter.authority_status is not AuthorityStatus.AUTHORIZED_INTERNAL_RESEARCH
    assert not adapter.authority_status.value.startswith("AUTHORIZED")
