"""Offline TrueFX tick archive adapter tests."""

import io
import zipfile
from datetime import datetime, timezone

import pytest

from research.data_fusion.adapters.base import AdapterError
from research.data_fusion.adapters.truefx import (
    TRUEFX_GMT_PARSED_AS_UTC,
    TRUEFX_MONTH_END_UPPER_BOUND,
    TRUEFX_NOT_SWAP_ROLLOVER_AUTHORITY,
    TruefxAdapter,
)

from .conftest import RETRIEVED_TIME, fixture_bytes, response_for

UTC = timezone.utc


@pytest.fixture
def adapter() -> TruefxAdapter:
    return TruefxAdapter()


def zip_response(adapter, body: bytes):
    request = adapter.build_monthly_archive_request("USD/JPY", 2024, 1)
    return response_for(request, body, content_type="application/zip")


def zipped_fixture() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("USDJPY-2024-01.csv", fixture_bytes("truefx_ticks_usdjpy.csv"))
    return buffer.getvalue()


def test_archive_request_is_deterministic_https_only(adapter):
    request = adapter.build_monthly_archive_request("usd/jpy", 2024, 1)
    assert request.url == "https://www.truefx.com/dev/data/2024-01/USDJPY-2024-01.zip"
    assert request.request_id() == adapter.build_monthly_archive_request("USDJPY", 2024, 1).request_id()
    with pytest.raises(AdapterError) as exc:
        adapter.build_monthly_archive_request("USDD", 2024, 1)
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"
    with pytest.raises(AdapterError):
        adapter.build_monthly_archive_request("USD/JPY", 2024, 13)


def test_parse_archive_happy_path(adapter):
    output = adapter.parse_archive(zip_response(adapter, zipped_fixture()), pair="USD/JPY", year=2024, month=1)
    bids = [record.value for record in output.records if record.field == "bid"]
    asks = [record.value for record in output.records if record.field == "ask"]
    assert bids == [141.102, 141.085]
    assert asks == [141.132, 141.115]
    first = output.records[0]
    assert first.entity_id == "FX:USDJPY"
    assert first.event_time_utc == datetime(2024, 1, 1, 22, 0, 0, tzinfo=UTC)
    assert first.available_time_utc == datetime(2024, 1, 31, 23, 59, 59, tzinfo=UTC)
    assert first.effective_time_utc is None
    assert first.license_id == "truefx-internal-use-v1"
    codes = output.note_codes()
    assert TRUEFX_GMT_PARSED_AS_UTC in codes
    assert TRUEFX_MONTH_END_UPPER_BOUND in codes
    assert TRUEFX_NOT_SWAP_ROLLOVER_AUTHORITY in codes


def test_ticks_are_invisible_before_archive_month_end(adapter):
    output = adapter.parse_archive(zip_response(adapter, zipped_fixture()), pair="USD/JPY", year=2024, month=1)
    for record in output.records:
        assert not record.eligible_at(datetime(2024, 1, 15, tzinfo=UTC))
        assert record.eligible_at(datetime(2024, 2, 1, tzinfo=UTC))


def test_swap_field_is_refused(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.refuse_forbidden_field("swap_rate")
    assert exc.value.code == "FORBIDDEN_INFERENCE_FIELD"


def test_pair_mismatch_is_refused(adapter):
    text = fixture_bytes("truefx_ticks_usdjpy.csv").decode().replace("USD/JPY", "EUR/USD", 1)
    with pytest.raises(AdapterError) as exc:
        adapter.parse_tick_csv(
            text,
            pair="USD/JPY",
            year=2024,
            month=1,
            retrieved_time_utc=RETRIEVED_TIME,
            request_id="req",
            raw_sha256="a" * 64,
        )
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_out_of_month_timestamp_is_refused(adapter):
    text = fixture_bytes("truefx_ticks_usdjpy.csv").decode().replace("20240102", "20240202")
    with pytest.raises(AdapterError) as exc:
        adapter.parse_tick_csv(
            text,
            pair="USD/JPY",
            year=2024,
            month=1,
            retrieved_time_utc=RETRIEVED_TIME,
            request_id="req",
            raw_sha256="a" * 64,
        )
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_crossed_quote_is_refused(adapter):
    text = fixture_bytes("truefx_ticks_usdjpy.csv").decode().replace("141.085,141.115", "141.120,141.115")
    with pytest.raises(AdapterError) as exc:
        adapter.parse_tick_csv(
            text,
            pair="USD/JPY",
            year=2024,
            month=1,
            retrieved_time_utc=RETRIEVED_TIME,
            request_id="req",
            raw_sha256="a" * 64,
        )
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_malformed_timestamp_is_refused(adapter):
    text = fixture_bytes("truefx_ticks_usdjpy.csv").decode().replace(
        "20240102 00:00:00.123", "02/01/2024 00:00:00"
    )
    with pytest.raises(AdapterError) as exc:
        adapter.parse_tick_csv(
            text,
            pair="USD/JPY",
            year=2024,
            month=1,
            retrieved_time_utc=RETRIEVED_TIME,
            request_id="req",
            raw_sha256="a" * 64,
        )
    assert exc.value.code == "SCHEMA_TIMESTAMP_INVALID"


def test_duplicate_tick_is_refused(adapter):
    text = fixture_bytes("truefx_ticks_usdjpy.csv").decode() + "USD/JPY,20240102 00:00:00.123,141.085,141.115\n"
    with pytest.raises(AdapterError) as exc:
        adapter.parse_tick_csv(
            text,
            pair="USD/JPY",
            year=2024,
            month=1,
            retrieved_time_utc=RETRIEVED_TIME,
            request_id="req",
            raw_sha256="a" * 64,
        )
    assert exc.value.code == "DUPLICATE_RECORD_ID"


def test_multi_member_archive_is_refused(adapter):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("one.csv", "x")
        archive.writestr("two.csv", "y")
    with pytest.raises(AdapterError) as exc:
        adapter.parse_archive(zip_response(adapter, buffer.getvalue()), pair="USD/JPY", year=2024, month=1)
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_non_zip_body_is_refused(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.parse_archive(zip_response(adapter, b"not a zip"), pair="USD/JPY", year=2024, month=1)
    assert exc.value.code == "SCHEMA_VALUE_TYPE_MISMATCH"
