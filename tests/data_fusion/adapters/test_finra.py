"""Offline FINRA short-sale-volume adapter tests."""

from datetime import date, datetime, timezone

import pytest

from research.data_fusion.adapters.base import AdapterError
from research.data_fusion.adapters.finra import (
    FINRA_DATE_ONLY_NOT_EXACT_AVAILABILITY,
    FINRA_SHORT_SALE_NOT_SHORT_INTEREST,
    FinraAdapter,
)

from .conftest import fixture_bytes, response_for

UTC = timezone.utc

TRADE_DATE = date(2024, 1, 2)


@pytest.fixture
def adapter() -> FinraAdapter:
    return FinraAdapter()


def file_response(body: bytes):
    request = FinraAdapter().build_daily_short_sale_request(TRADE_DATE)
    return response_for(request, body, content_type="text/plain")


def volume_fields(output, symbol):
    kept = {"short_volume", "short_exempt_volume", "total_volume"}
    return {
        record.field: record.value
        for record in output.records
        if record.entity_id == f"FINRA:{symbol}" and record.field in kept
    }


def test_daily_request_is_deterministic_https_only(adapter):
    request = adapter.build_daily_short_sale_request(TRADE_DATE)
    assert request.url == "https://cdn.finra.org/equity/regsho/nms/shrt20240102"
    assert request.request_id() == adapter.build_daily_short_sale_request(TRADE_DATE).request_id()
    with pytest.raises(AdapterError):
        adapter.build_daily_short_sale_request(TRADE_DATE, tier="bogus")


def test_parse_daily_file_happy_path(adapter):
    output = adapter.parse_daily_short_sale(file_response(fixture_bytes("finra_shortsale_volume.txt")), trade_date=TRADE_DATE)
    aapl = volume_fields(output, "AAPL")
    assert aapl == {"short_volume": 1000, "short_exempt_volume": 100, "total_volume": 5000}
    assert volume_fields(output, "MSFT") == {
        "short_volume": 2000,
        "short_exempt_volume": 0,
        "total_volume": 7000,
    }
    first = output.records[0]
    assert first.event_time_utc == datetime(2024, 1, 2, tzinfo=UTC)
    assert first.available_time_utc == datetime(2024, 1, 2, 23, 59, 59, tzinfo=UTC)
    codes = output.note_codes()
    assert FINRA_DATE_ONLY_NOT_EXACT_AVAILABILITY in codes
    assert FINRA_SHORT_SALE_NOT_SHORT_INTEREST in codes


def test_forbidden_inference_fields_are_refused(adapter):
    for field in ("short_interest", "borrow_fee", "utilization"):
        with pytest.raises(AdapterError) as exc:
            adapter.refuse_forbidden_field(field)
        assert exc.value.code == "FORBIDDEN_INFERENCE_FIELD"


def test_malformed_row_column_count_is_refused(adapter):
    body = fixture_bytes("finra_shortsale_volume.txt").replace(
        b"2024-01-02|AAPL|1000|100|5000|B", b"2024-01-02|AAPL|1000|100|5000"
    )
    with pytest.raises(AdapterError) as exc:
        adapter.parse_daily_short_sale(file_response(body), trade_date=TRADE_DATE)
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_wrong_header_is_refused(adapter):
    body = fixture_bytes("finra_shortsale_volume.txt").replace(
        b"Date|Symbol|ShortVolume", b"Date|Ticker|ShortVolume"
    )
    with pytest.raises(AdapterError) as exc:
        adapter.parse_daily_short_sale(file_response(body), trade_date=TRADE_DATE)
    assert exc.value.code == "SCHEMA_FIELD_MISSING"


def test_row_date_mismatch_is_refused(adapter):
    body = fixture_bytes("finra_shortsale_volume.txt").replace(b"2024-01-02|MSFT", b"2024-01-03|MSFT")
    with pytest.raises(AdapterError) as exc:
        adapter.parse_daily_short_sale(file_response(body), trade_date=TRADE_DATE)
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_non_numeric_volume_is_refused(adapter):
    body = fixture_bytes("finra_shortsale_volume.txt").replace(b"|1000|", b"|many|")
    with pytest.raises(AdapterError) as exc:
        adapter.parse_daily_short_sale(file_response(body), trade_date=TRADE_DATE)
    assert exc.value.code == "SCHEMA_VALUE_TYPE_MISMATCH"


def test_invariant_short_above_total_is_refused(adapter):
    body = fixture_bytes("finra_shortsale_volume.txt").replace(b"|100|5000|", b"|6000|5000|")
    with pytest.raises(AdapterError) as exc:
        adapter.parse_daily_short_sale(file_response(body), trade_date=TRADE_DATE)
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_duplicate_symbol_rows_are_refused(adapter):
    body = fixture_bytes("finra_shortsale_volume.txt") + b"2024-01-02|AAPL|1|0|2|B\n"
    with pytest.raises(AdapterError) as exc:
        adapter.parse_daily_short_sale(file_response(body), trade_date=TRADE_DATE)
    assert exc.value.code == "DUPLICATE_RECORD_ID"


def test_symbol_case_is_normalized(adapter):
    body = fixture_bytes("finra_shortsale_volume.txt").replace(b"AAPL", b"aapl")
    output = adapter.parse_daily_short_sale(file_response(body), trade_date=TRADE_DATE)
    entities = {record.entity_id for record in output.records}
    assert "FINRA:AAPL" in entities
    assert "FINRA:aapl" not in entities
