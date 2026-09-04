"""Offline tests for the shared adapter foundation."""

from datetime import date, datetime, timezone

import pytest

from research.data_fusion.adapters.base import (
    AdapterError,
    AdapterOutput,
    AvailabilityBasis,
    RawCacheStore,
    RawResponse,
    RateLimitPolicy,
    ReleaseEvidence,
    RequestSpec,
    Timings,
    date_only_evidence,
    end_of_utc_day,
    extract_sdmx_json_series,
    midnight_utc,
    parse_date,
    parse_utc,
    reject_unknown_keys,
    require_keys,
    require_mapping,
    require_str,
    sdmx_series_id,
    timings_from_evidence,
)


UTC = timezone.utc


def spec(**overrides):
    values = dict(
        source_id="TEST",
        url="https://example.com/data",
        query=(("b", "2"), ("a", "1")),
    )
    values.update(overrides)
    return RequestSpec(**values)


def test_request_identity_is_order_and_time_independent():
    first = spec(query=(("a", "1"), ("b", "2")))
    second = spec(query=(("b", "2"), ("a", "1")))
    assert first.request_id() == second.request_id()


def test_different_query_produces_different_identity():
    assert spec(query=(("a", "1"),)).request_id() != spec(query=(("a", "2"),)).request_id()


def test_http_url_is_refused():
    with pytest.raises(AdapterError) as exc:
        spec(url="http://example.com/data")
    assert exc.value.code == "NON_HTTPS_REQUEST_REFUSED"


def test_non_get_method_is_refused():
    with pytest.raises(AdapterError) as exc:
        spec(method="POST")
    assert exc.value.code == "NON_GET_METHOD_REFUSED"


def test_credential_header_is_refused():
    with pytest.raises(AdapterError) as exc:
        spec(headers=(("Authorization", "Bearer nope"),))
    assert exc.value.code == "CREDENTIAL_IN_REQUEST_IDENTITY"


def test_credential_query_is_excluded_from_identity():
    keyed = spec(credential_query=(("api_key", "secret-token"),))
    assert keyed.request_id() == spec().request_id()
    assert "secret-token" not in str(keyed.canonical_payload())
    assert keyed.full_url().endswith("api_key=secret-token")


def test_credential_value_in_canonical_query_is_refused():
    with pytest.raises(AdapterError) as exc:
        spec(query=(("api_key", "secret-token"),), credential_query=(("api_key", "secret-token"),))
    assert exc.value.code == "CREDENTIAL_IN_REQUEST_IDENTITY"


def test_response_sha256_binds_body():
    body = b"deterministic bytes"
    response = RawResponse("req", "https://example.com", 200, "OK", (), body, datetime(2026, 1, 1, tzinfo=UTC))
    import hashlib

    assert response.sha256_hex() == hashlib.sha256(body).hexdigest()


def test_validate_response_status_and_content_type():
    response = RawResponse(
        "req",
        "https://example.com",
        404,
        "Not Found",
        (),
        b"{}",
        datetime(2026, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(AdapterError) as exc:
        from research.data_fusion.adapters.base import validate_response

        validate_response(response, allowed_content_types=("application/json",))
    assert exc.value.code == "HTTP_STATUS_UNEXPECTED"


def test_validate_response_rejects_unexpected_content_type():
    from research.data_fusion.adapters.base import validate_response

    response = RawResponse(
        "req",
        "https://example.com",
        200,
        "OK",
        (("Content-Type", "text/html; charset=utf-8"),),
        b"<html>",
        datetime(2026, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(AdapterError) as exc:
        validate_response(response, allowed_content_types=("application/json",))
    assert exc.value.code == "CONTENT_TYPE_UNEXPECTED"


def test_rate_limit_policy_retry_boundary():
    policy = RateLimitPolicy("SRC", "fair use", 1.0, 2, 1.0, (429, 503))
    assert policy.should_retry(429, 0)
    assert policy.should_retry(503, 1)
    assert not policy.should_retry(429, 2)
    assert not policy.should_retry(500, 0)
    assert "SRC" in policy.describe()
    assert policy.describe() == RateLimitPolicy("SRC", "fair use", 1.0, 2, 1.0, (429, 503)).describe()


def test_raw_cache_store_roundtrip_outside_repo(tmp_path):
    store = RawCacheStore(tmp_path / "cache-root")
    assert store.path_for("sec_edgar", "abc").is_relative_to(tmp_path)
    stored = store.store("sec_edgar", "abc", b"raw-bytes")
    assert stored.read_bytes() == b"raw-bytes"
    assert store.load("sec_edgar", "abc") == b"raw-bytes"
    assert store.load("sec_edgar", "missing") is None


def test_parse_utc_accepts_z_and_offset_zero_only():
    assert parse_utc("2024-01-03T14:30:00Z", "x") == datetime(2024, 1, 3, 14, 30, tzinfo=UTC)
    assert parse_utc("2024-01-03T14:30:00+00:00", "x") == datetime(2024, 1, 3, 14, 30, tzinfo=UTC)
    with pytest.raises(AdapterError) as naive:
        parse_utc("2024-01-03T14:30:00", "x")
    assert naive.value.code == "SCHEMA_TIMESTAMP_INVALID"
    with pytest.raises(AdapterError) as offset:
        parse_utc("2024-01-03T14:30:00+07:00", "x")
    assert offset.value.code == "SCHEMA_TIMESTAMP_INVALID"


def test_date_only_evidence_is_end_of_day_upper_bound():
    evidence = date_only_evidence("calendar", date(2024, 1, 3))
    assert evidence.available_time_utc == datetime(2024, 1, 3, 23, 59, 59, tzinfo=UTC)
    assert evidence.basis is AvailabilityBasis.DATE_ONLY_UPPER_BOUND


def test_timings_require_exact_availability_refuses_date_only():
    timings = timings_from_evidence(midnight_utc(date(2024, 1, 2)), date_only_evidence("cal", date(2024, 1, 3)))
    with pytest.raises(AdapterError) as exc:
        timings.require_exact_availability()
    assert exc.value.code == "NON_EXACT_AVAILABLE_TIME_FORBIDDEN"


def test_missing_evidence_fails_closed():
    with pytest.raises(AdapterError) as exc:
        timings_from_evidence(midnight_utc(date(2024, 1, 2)), None)
    assert exc.value.code == "MISSING_AVAILABLE_TIME_EVIDENCE"


def test_schema_helpers_raise_stable_codes():
    with pytest.raises(AdapterError) as not_mapping:
        require_mapping([], "ctx")
    assert not_mapping.value.code == "SCHEMA_VALUE_TYPE_MISMATCH"
    with pytest.raises(AdapterError) as missing:
        require_keys({}, {"a"}, "ctx")
    assert missing.value.code == "SCHEMA_FIELD_MISSING"
    with pytest.raises(AdapterError) as unknown:
        reject_unknown_keys({"b": 1}, {"a"}, "ctx")
    assert unknown.value.code == "SCHEMA_UNKNOWN_FIELD"
    with pytest.raises(AdapterError) as bad_str:
        require_str({"a": ""}, "a", "ctx")
    assert bad_str.value.code == "SCHEMA_VALUE_TYPE_MISMATCH"
    with pytest.raises(AdapterError) as bad_date:
        parse_date("01/02/2024", "ctx")
    assert bad_date.value.code == "SCHEMA_TIMESTAMP_INVALID"


def test_sdmx_extraction_and_series_resolution():
    payload = {
        "header": {"id": "x", "prepared": "2024-01-03T15:10:00.000Z"},
        "dataSets": [{"series": {"0:0": {"observations": {"0": [1.5, 0], "1": [None, 0]}}}}],
        "structure": {
            "dimensions": {
                "series": [
                    {"id": "COUNTRY", "values": [{"id": "US"}]},
                    {"id": "FREQ", "values": [{"id": "Q"}]},
                ],
                "observation": [
                    {"id": "TIME_PERIOD", "values": [{"id": "2024-03-20"}, {"id": "2024-05-01"}]}
                ],
            }
        },
    }
    rows = extract_sdmx_json_series(payload)
    assert rows == [
        {"series_key": "0:0", "time_period": "2024-03-20", "value": 1.5},
        {"series_key": "0:0", "time_period": "2024-05-01", "value": None},
    ]
    assert sdmx_series_id(payload, "0:0") == "US.Q"
    with pytest.raises(AdapterError) as out_of_range:
        sdmx_series_id(payload, "1:0")
    assert out_of_range.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_two_pull_equality_for_expected_immutable_source():
    """Building the same request twice yields byte-identical identity (contract stub
    for the two-pull equality checks performed per adapter)."""
    assert spec().canonical_payload() == spec().canonical_payload()
