"""Offline tests for the FINRA short-sale-volume adapter: fixtures only.

Every test runs the adapter against hand-written fixture bytes via the
shared offline harness (``response_for``).  Malformed, duplicate and
invariant-violation cases are derived from the committed fixture by line
mutation so the fixture set stays minimal.
"""

from datetime import date, datetime, timezone

import pytest

from research.data_fusion.adapters.base import (
    AdapterError,
    AvailabilityBasis,
    CONTENT_TYPE_UNEXPECTED,
    DUPLICATE_RECORD_ID,
    FORBIDDEN_INFERENCE_FIELD,
    SCHEMA_FIELD_MISSING,
    SCHEMA_INVARIANT_VIOLATED,
    SCHEMA_VALUE_TYPE_MISMATCH,
    end_of_utc_day,
    midnight_utc,
    timings_from_evidence,
    date_only_evidence,
    NON_EXACT_AVAILABLE_TIME_FORBIDDEN,
)
from research.data_fusion.authority import AuthorityStatus
from research.data_fusion.adapters.finra import (
    FINRA_DATE_ONLY_NOT_EXACT_AVAILABILITY,
    FINRA_SHORT_SALE_NOT_SHORT_INTEREST,
    FinraAdapter,
)

from .conftest import RETRIEVED_TIME, fixture_bytes, fixture_text, response_for

UTC = timezone.utc

TRADE_DATE = date(2024, 1, 2)
FIXTURE = "finra_shortsale_daily.txt"


@pytest.fixture
def adapter() -> FinraAdapter:
    return FinraAdapter()


def finra_response(adapter: FinraAdapter, body: bytes, **kwargs) -> object:
    request = adapter.build_short_sale_request(TRADE_DATE)
    return response_for(request, body, content_type="text/plain", **kwargs)


def mutated_lines(lines: list[str]) -> bytes:
    return ("\n".join(lines) + "\n").encode("utf-8")


def fixture_lines() -> list[str]:
    return fixture_text(FIXTURE).splitlines()


# ---------------------------------------------------------------------------
# Request construction
# ---------------------------------------------------------------------------


def test_daily_request_url_and_identity(adapter):
    request = adapter.build_short_sale_request(TRADE_DATE)
    assert request.url == "https://cdn.finra.org/equity/regsho/nms/shrt20240102"
    assert request.method == "GET"
    assert request.query == () and request.credential_query == ()
    assert request.request_id() == adapter.build_short_sale_request(TRADE_DATE).request_id()
    assert request.request_id() != adapter.build_short_sale_request(date(2024, 1, 3)).request_id()


def test_otc_tier_request_url(adapter):
    request = adapter.build_short_sale_request(TRADE_DATE, tier="otc")
    assert request.url == "https://cdn.finra.org/equity/otcmarket/biweekly/shrt20240102"


def test_unknown_tier_refused(adapter):
    with pytest.raises(AdapterError) as err:
        adapter.build_short_sale_request(TRADE_DATE, tier="dark-pool")
    assert err.value.code == SCHEMA_INVARIANT_VIOLATED


def test_datetime_is_not_a_trade_date(adapter):
    with pytest.raises(AdapterError) as err:
        adapter.build_short_sale_request(datetime(2024, 1, 2, tzinfo=UTC))
    assert err.value.code == SCHEMA_VALUE_TYPE_MISMATCH


def test_default_rate_limit_is_conservative():
    policy = FinraAdapter.default_rate_limit()
    assert policy.source_id == "FINRA_SHORT"
    assert policy.min_interval_seconds >= 1.0
    assert 429 in policy.retry_status_codes


def test_authority_is_documented_candidate_only():
    assert FinraAdapter.authority_status == AuthorityStatus.DOCUMENTED_CANDIDATE
    assert FinraAdapter.authority_status != AuthorityStatus.AUTHORIZED_INTERNAL_RESEARCH


# ---------------------------------------------------------------------------
# Happy path and point-in-time semantics
# ---------------------------------------------------------------------------


def test_daily_happy_path(adapter):
    output = adapter.parse_short_sale(finra_response(adapter, fixture_bytes(FIXTURE)), trade_date=TRADE_DATE)
    assert output.source_id == "FINRA_SHORT"
    assert output.dataset_id == "short_sale_volume_daily"
    assert len(output.records) == 8  # 3 volumes + market code per symbol

    by_key = {(r.entity_id, r.field): r for r in output.records}
    aapl = by_key[("FINRA:AAPL", "short_volume")]
    assert aapl.value == 1000 and aapl.unit == "SHARES"
    assert by_key[("FINRA:AAPL", "short_exempt_volume")].value == 100
    assert by_key[("FINRA:AAPL", "total_volume")].value == 5000
    assert by_key[("FINRA:AAPL", "market")].value == "B"
    assert by_key[("FINRA:AAPL", "market")].unit == "MARKET_CODE"
    assert by_key[("FINRA:MSFT", "short_volume")].value == 2000
    assert by_key[("FINRA:MSFT", "short_exempt_volume")].value == 0
    assert by_key[("FINRA:MSFT", "total_volume")].value == 7000
    assert by_key[("FINRA:MSFT", "market")].value == "Q"

    for record in output.records:
        assert record.event_time_utc == datetime(2024, 1, 2, tzinfo=UTC)
        assert record.effective_time_utc == datetime(2024, 1, 2, tzinfo=UTC)
        assert record.available_time_utc == datetime(2024, 1, 3, 0, 0, 0, tzinfo=UTC)  # DF-ISSUE-1: next-day exclusive end
        assert record.vintage_time_utc == record.available_time_utc
        assert record.available_time_utc < record.retrieved_time_utc == RETRIEVED_TIME


def test_availability_is_end_of_trade_day_upper_bound(adapter):
    output = adapter.parse_short_sale(finra_response(adapter, fixture_bytes(FIXTURE)), trade_date=TRADE_DATE)
    assert set(output.note_codes()) == {
        FINRA_DATE_ONLY_NOT_EXACT_AVAILABILITY,
        FINRA_SHORT_SALE_NOT_SHORT_INTEREST,
    }
    assert output.records[0].available_time_utc == end_of_utc_day(TRADE_DATE)
    assert output.records[0].available_time_utc != RETRIEVED_TIME


def test_trade_date_can_never_be_exact_market_availability():
    timings = timings_from_evidence(
        midnight_utc(TRADE_DATE),
        date_only_evidence("FINRA short-sale file trade date (date only)", TRADE_DATE),
        effective_time_utc=midnight_utc(TRADE_DATE),
    )
    assert timings.availability_basis is AvailabilityBasis.DATE_ONLY_UPPER_BOUND
    with pytest.raises(AdapterError) as err:
        timings.require_exact_availability()
    assert err.value.code == NON_EXACT_AVAILABLE_TIME_FORBIDDEN


# ---------------------------------------------------------------------------
# Fail-closed inference guard: never short interest / borrow fee / utilization
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field", ["short_interest", "borrow_fee", "utilization"])
def test_forbidden_fields_refused(adapter, field):
    assert field in FinraAdapter.forbidden_fields
    with pytest.raises(AdapterError) as err:
        adapter.refuse_forbidden_field(field)
    assert err.value.code == FORBIDDEN_INFERENCE_FIELD


@pytest.mark.parametrize("field", ["short_interest", "borrow_fee", "utilization"])
def test_make_record_never_emits_forbidden_fields(adapter, field):
    timings = timings_from_evidence(
        midnight_utc(TRADE_DATE),
        date_only_evidence("FINRA short-sale file trade date (date only)", TRADE_DATE),
        effective_time_utc=midnight_utc(TRADE_DATE),
    )
    with pytest.raises(AdapterError) as err:
        adapter.make_record(
            dataset_id="short_sale_volume_daily",
            entity_id="FINRA:AAPL",
            field_name=field,
            value=1,
            unit="SHARES",
            timings=timings,
            retrieved_time_utc=RETRIEVED_TIME,
            request_id="0" * 64,
            raw_sha256="a" * 64,
        )
    assert err.value.code == FORBIDDEN_INFERENCE_FIELD


# ---------------------------------------------------------------------------
# Schema and invariant rejection
# ---------------------------------------------------------------------------


def test_wrong_header_rejected(adapter):
    lines = fixture_lines()
    lines[0] = "Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Exchange"
    with pytest.raises(AdapterError) as err:
        adapter.parse_short_sale(finra_response(adapter, mutated_lines(lines)), trade_date=TRADE_DATE)
    assert err.value.code == SCHEMA_FIELD_MISSING


def test_missing_header_rejected(adapter):
    with pytest.raises(AdapterError) as err:
        adapter.parse_short_sale(finra_response(adapter, b""), trade_date=TRADE_DATE)
    assert err.value.code == SCHEMA_FIELD_MISSING


def test_five_columns_rejected(adapter):
    lines = fixture_lines()
    lines[1] = "2024-01-02|AAPL|1000|100|5000"  # market column missing
    with pytest.raises(AdapterError) as err:
        adapter.parse_short_sale(finra_response(adapter, mutated_lines(lines)), trade_date=TRADE_DATE)
    assert err.value.code == SCHEMA_INVARIANT_VIOLATED


def test_row_date_mismatch_rejected(adapter):
    lines = fixture_lines()
    lines[1] = "2024-01-03|AAPL|1000|100|5000|B"
    with pytest.raises(AdapterError) as err:
        adapter.parse_short_sale(finra_response(adapter, mutated_lines(lines)), trade_date=TRADE_DATE)
    assert err.value.code == SCHEMA_INVARIANT_VIOLATED


@pytest.mark.parametrize("bad_volume", ["-5", "1000.5", "1e3", "abc", "", "+7", "1 000"])
def test_non_integer_volume_rejected(adapter, bad_volume):
    lines = fixture_lines()
    parts = lines[1].split("|")
    parts[2] = bad_volume
    lines[1] = "|".join(parts)
    with pytest.raises(AdapterError) as err:
        adapter.parse_short_sale(finra_response(adapter, mutated_lines(lines)), trade_date=TRADE_DATE)
    assert err.value.code == SCHEMA_VALUE_TYPE_MISMATCH


def test_short_exempt_exceeding_short_rejected(adapter):
    lines = fixture_lines()
    lines[2] = "2024-01-02|MSFT|2000|3000|7000|Q"
    with pytest.raises(AdapterError) as err:
        adapter.parse_short_sale(finra_response(adapter, mutated_lines(lines)), trade_date=TRADE_DATE)
    assert err.value.code == SCHEMA_INVARIANT_VIOLATED


def test_short_exceeding_total_rejected(adapter):
    lines = fixture_lines()
    lines[2] = "2024-01-02|MSFT|9000|0|7000|Q"
    with pytest.raises(AdapterError) as err:
        adapter.parse_short_sale(finra_response(adapter, mutated_lines(lines)), trade_date=TRADE_DATE)
    assert err.value.code == SCHEMA_INVARIANT_VIOLATED


def test_duplicate_symbol_row_rejected(adapter):
    lines = fixture_lines()
    lines.append("2024-01-02|AAPL|1|0|1|B")
    with pytest.raises(AdapterError) as err:
        adapter.parse_short_sale(finra_response(adapter, mutated_lines(lines)), trade_date=TRADE_DATE)
    assert err.value.code == DUPLICATE_RECORD_ID


def test_lowercase_symbol_rejected(adapter):
    lines = fixture_lines()
    lines[1] = "2024-01-02|aapl|1000|100|5000|B"
    with pytest.raises(AdapterError) as err:
        adapter.parse_short_sale(finra_response(adapter, mutated_lines(lines)), trade_date=TRADE_DATE)
    assert err.value.code == SCHEMA_INVARIANT_VIOLATED


def test_empty_symbol_rejected(adapter):
    lines = fixture_lines()
    lines[1] = "2024-01-02||1000|100|5000|B"
    with pytest.raises(AdapterError) as err:
        adapter.parse_short_sale(finra_response(adapter, mutated_lines(lines)), trade_date=TRADE_DATE)
    assert err.value.code == SCHEMA_INVARIANT_VIOLATED


def test_multi_letter_market_rejected(adapter):
    lines = fixture_lines()
    lines[1] = "2024-01-02|AAPL|1000|100|5000|NYSE"
    with pytest.raises(AdapterError) as err:
        adapter.parse_short_sale(finra_response(adapter, mutated_lines(lines)), trade_date=TRADE_DATE)
    assert err.value.code == SCHEMA_INVARIANT_VIOLATED


def test_wrong_content_type_rejected(adapter):
    request = adapter.build_short_sale_request(TRADE_DATE)
    response = response_for(request, fixture_bytes(FIXTURE), content_type="application/json")
    with pytest.raises(AdapterError) as err:
        adapter.parse_short_sale(response, trade_date=TRADE_DATE)
    assert err.value.code == CONTENT_TYPE_UNEXPECTED


def test_blank_line_between_rows_is_tolerated(adapter):
    body = ("\n\n".join(fixture_lines()) + "\n").encode("utf-8")
    output = adapter.parse_short_sale(finra_response(adapter, body), trade_date=TRADE_DATE)
    assert len(output.records) == 8


# ---------------------------------------------------------------------------
# Determinism: two pulls of the same bytes produce identical canonical output
# ---------------------------------------------------------------------------


def test_two_pull_equality(adapter):
    pulls = []
    for _ in range(2):
        response = finra_response(adapter, fixture_bytes(FIXTURE))
        output = adapter.parse_short_sale(response, trade_date=TRADE_DATE)
        pulls.append(
            (
                [record.canonical_bytes() for record in output.records],
                output.note_codes(),
                output.raw_sha256,
                output.parser_version,
            )
        )
    assert pulls[0] == pulls[1]
