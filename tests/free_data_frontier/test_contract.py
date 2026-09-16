import pytest

from research.free_data_frontier.contract import (
    PARSER_VERSION,
    SchemaRefusal,
    availability_semantics,
    source_verdict,
    validate_iso_utc,
    validate_record,
)
from research.free_data_frontier.http import RetrievalResult, build_record


def _record(**overrides):
    base = {
        "source_id": "s",
        "dataset_id": "d",
        "canonical_request_id": "r" * 64,
        "source_url_redacted": "https://x/y",
        "retrieved_time_utc": "2026-09-16T00:00:00Z",
        "http_status": 200,
        "content_type": "application/json",
        "content_length": 10,
        "raw_path": "/x/raw/f.json",
        "raw_sha256": "a" * 64,
        "parser_version": PARSER_VERSION,
        "authority_status": "PASS_SAMPLE",
        "event_time_utc": None,
        "effective_time_utc": None,
        "available_time_utc": None,
        "available_time_evidence": None,
        "vintage": None,
        "retrieval_time_only": True,
        "notes": [],
    }
    base.update(overrides)
    return base


def test_valid_record_passes():
    validate_record(_record())


def test_missing_field_refused():
    record = _record()
    del record["raw_sha256"]
    with pytest.raises(SchemaRefusal):
        validate_record(record)


def test_unknown_field_refused():
    with pytest.raises(SchemaRefusal):
        validate_record(_record(extra_field=1))


def test_bad_status_refused():
    with pytest.raises(SchemaRefusal):
        validate_record(_record(authority_status="PASS_FULL_HISTORICAL"))


def test_bad_sha_refused():
    with pytest.raises(SchemaRefusal):
        validate_record(_record(raw_sha256="short"))


def test_bad_timestamp_refused():
    with pytest.raises(SchemaRefusal):
        validate_record(_record(retrieved_time_utc="2026-09-16 00:00:00"))


def test_available_time_requires_evidence():
    with pytest.raises(SchemaRefusal):
        validate_record(
            _record(available_time_utc="2026-09-15T00:00:00Z", retrieval_time_only=False)
        )


def test_retrieval_only_contradicts_available_time():
    with pytest.raises(SchemaRefusal):
        validate_record(
            _record(
                available_time_utc="2026-09-15T00:00:00Z",
                available_time_evidence="publication page",
            )
        )


def test_raw_path_must_live_under_raw_root():
    with pytest.raises(SchemaRefusal):
        validate_record(_record(raw_path="/tmp/elsewhere/f.json"))


def test_retrieved_time_never_becomes_available_time():
    result = RetrievalResult(
        request_id="r" * 64,
        url_redacted="https://x",
        http_status=200,
        content_type=None,
        content_length=0,
        retrieved_time_utc="2026-09-16T00:00:00Z",
        raw_path=None,
        raw_sha256=None,
        bytes_written=0,
        response_headers_redacted={},
    )
    record = build_record(
        result,
        source_id="s",
        dataset_id="d",
        authority_status="PASS_SAMPLE",
    )
    assert record["available_time_utc"] is None
    assert record["retrieval_time_only"] is True
    assert availability_semantics(record) == "RETRIEVAL_TIME_ONLY"


def test_evidenced_available_time_classifies_pit():
    record = _record(
        available_time_utc="2026-09-15T00:00:00Z",
        available_time_evidence="official release calendar row",
        retrieval_time_only=False,
    )
    validate_record(record)
    assert availability_semantics(record) == "PIT_EVIDENCED"


def test_source_verdict_aggregation():
    rows = [_record(dataset_id="a"), _record(dataset_id="b")]
    assert source_verdict(rows, "s")["status"] == "PASS_SAMPLE"
    assert source_verdict([], "s")["status"] == "PASS_INVENTORY_ONLY"
