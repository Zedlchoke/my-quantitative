"""Offline ECB Data API (SDMX) adapter tests."""

import json
from datetime import date, datetime, timezone

import pytest

from research.data_fusion.adapters.base import AdapterError, date_only_evidence
from research.data_fusion.adapters.ecb import (
    ECB_AVAILABILITY_NOT_EXACT,
    ECB_DATA_NOT_CARRY_AUTHORIZATION,
    ECB_PREPARED_TIME_NOT_AVAILABILITY_PROOF,
    EcbAdapter,
)

from .conftest import fixture_bytes, response_for

UTC = timezone.utc


@pytest.fixture
def adapter() -> EcbAdapter:
    return EcbAdapter()


def series_response(body: bytes):
    request = EcbAdapter().build_series_request("EXR", "D.USD.EUR.SP00.A")
    return response_for(
        request,
        body,
        content_type="application/vnd.sdmx.data+json",
    )


def evidence():
    return date_only_evidence("ECB reference-rate publication calendar", date(2024, 1, 3))


def test_series_request_is_deterministic_https_only(adapter):
    request = adapter.build_series_request("EXR", "D.USD.EUR.SP00.A", start_period="2024-01-01")
    assert request.url == "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"
    assert request.request_id() == adapter.build_series_request(
        "exr", "D.USD.EUR.SP00.A", start_period="2024-01-01"
    ).request_id()
    with pytest.raises(AdapterError):
        adapter.build_series_request("EXR", "bad key with spaces")


def test_parse_without_release_evidence_fails_closed(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.parse_series(series_response(fixture_bytes("ecb_sdmx_exr.json")), dataflow="EXR", release_evidence=None, unit="EUR_PER_UNIT")
    assert exc.value.code == "MISSING_AVAILABLE_TIME_EVIDENCE"


def test_parse_series_happy_path(adapter):
    output = adapter.parse_series(
        series_response(fixture_bytes("ecb_sdmx_exr.json")),
        dataflow="EXR",
        release_evidence=evidence(),
        unit="EUR_PER_UNIT",
    )
    assert len(output.records) == 2
    first = output.records[0]
    assert first.entity_id == "ECB:EXR:D.EUR.USD.SP00.A"
    assert first.field == "observation"
    assert first.value == 1.0951
    assert first.event_time_utc == datetime(2024, 1, 2, tzinfo=UTC)
    assert first.effective_time_utc == datetime(2024, 1, 2, tzinfo=UTC)
    assert first.available_time_utc == datetime(2024, 1, 3, 23, 59, 59, tzinfo=UTC)
    codes = output.note_codes()
    assert ECB_PREPARED_TIME_NOT_AVAILABILITY_PROOF in codes
    assert ECB_AVAILABILITY_NOT_EXACT in codes
    assert ECB_DATA_NOT_CARRY_AUTHORIZATION in codes


def test_parse_series_never_uses_prepared_time_as_availability(adapter):
    output = adapter.parse_series(
        series_response(fixture_bytes("ecb_sdmx_exr.json")),
        dataflow="EXR",
        release_evidence=evidence(),
        unit="EUR_PER_UNIT",
    )
    prepared = datetime(2024, 1, 3, 15, 10, tzinfo=UTC)
    for record in output.records:
        assert record.available_time_utc != prepared
        assert record.available_time_utc > prepared  # upper bound, not the prepared time


def test_parse_series_duplicate_observation_is_refused(adapter):
    payload = json.loads(fixture_bytes("ecb_sdmx_exr.json"))
    periods = payload["structure"]["dimensions"]["observation"][0]["values"]
    periods[1] = dict(periods[0])  # two observation positions share one TIME_PERIOD
    with pytest.raises(AdapterError) as exc:
        adapter.parse_series(
            series_response(json.dumps(payload).encode()),
            dataflow="EXR",
            release_evidence=evidence(),
            unit="EUR_PER_UNIT",
        )
    assert exc.value.code == "DUPLICATE_RECORD_ID"


def test_parse_series_missing_structure_is_refused(adapter):
    payload = json.loads(fixture_bytes("ecb_sdmx_exr.json"))
    del payload["structure"]
    with pytest.raises(AdapterError) as exc:
        adapter.parse_series(
            series_response(json.dumps(payload).encode()),
            dataflow="EXR",
            release_evidence=evidence(),
            unit="EUR_PER_UNIT",
        )
    assert exc.value.code == "SCHEMA_FIELD_MISSING"


def test_parse_series_non_numeric_observation_is_refused(adapter):
    payload = json.loads(fixture_bytes("ecb_sdmx_exr.json"))
    payload["dataSets"][0]["series"]["0:0:0:0:0"]["observations"]["0"] = ["1.0951", 0]
    with pytest.raises(AdapterError) as exc:
        adapter.parse_series(
            series_response(json.dumps(payload).encode()),
            dataflow="EXR",
            release_evidence=evidence(),
            unit="EUR_PER_UNIT",
        )
    assert exc.value.code == "SCHEMA_VALUE_TYPE_MISMATCH"


def test_two_pull_equality(adapter):
    body = fixture_bytes("ecb_sdmx_exr.json")
    first = adapter.parse_series(series_response(body), dataflow="EXR", release_evidence=evidence(), unit="EUR_PER_UNIT")
    second = adapter.parse_series(series_response(body), dataflow="EXR", release_evidence=evidence(), unit="EUR_PER_UNIT")
    assert [record.canonical_bytes() for record in first.records] == [
        record.canonical_bytes() for record in second.records
    ]
