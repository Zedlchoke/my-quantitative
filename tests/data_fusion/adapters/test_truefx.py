"""Offline TrueFX monthly tick archive adapter tests.

No network, no wall clock: the monthly archive ZIP is built in memory from a
tiny hand-written fixture CSV (stdlib ``zipfile`` + ``io``) and fed to the
adapter through the offline ``response_for`` helper.
"""

import io
import zipfile
from datetime import datetime, timezone

import pytest

from research.data_fusion.adapters.base import (
    NON_EXACT_AVAILABLE_TIME_FORBIDDEN,
    AdapterError,
    AvailabilityBasis,
    timings_from_evidence,
)
from research.data_fusion.adapters.truefx import (
    PRICE_UNIT,
    TOP_OF_BOOK_TICKS_DATASET,
    TRUEFX_GMT_PARSED_AS_UTC,
    TRUEFX_MONTH_END_UPPER_BOUND,
    TRUEFX_NOT_SWAP_ROLLOVER_AUTHORITY,
    TruefxAdapter,
)
from research.data_fusion.authority import (
    AuthorityEvidence,
    AuthorityStatus,
    evaluate_authority,
)

from .conftest import RETRIEVED_TIME, fixture_bytes, response_for

UTC = timezone.utc

PAIR = "USD/JPY"
YEAR, MONTH = 2024, 1
FIXTURE_CSV = "truefx_ticks_usdjpy.csv"


@pytest.fixture
def adapter() -> TruefxAdapter:
    return TruefxAdapter()


def zip_bytes(
    members: dict[str, str | bytes] | None = None,
) -> bytes:
    """Build an in-memory ZIP archive; defaults to the fixture CSV member."""

    if members is None:
        members = {"USDJPY-2024-01.csv": fixture_bytes(FIXTURE_CSV)}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)
    return buffer.getvalue()


def archive_response(adapter: TruefxAdapter, body: bytes, *, content_type: str = "application/zip"):
    request = adapter.build_monthly_archive_request(PAIR, YEAR, MONTH)
    return response_for(request, body, content_type=content_type)


def parse_fixture(adapter: TruefxAdapter) -> object:
    return adapter.parse_archive(
        archive_response(adapter, zip_bytes()), pair=PAIR, year=YEAR, month=MONTH
    )


def csv_variant(adapter: TruefxAdapter, old: str, new: str) -> bytes:
    """Fixture CSV with one literal replacement, zipped in memory."""

    text = fixture_bytes(FIXTURE_CSV).decode("utf-8")
    assert old in text
    return zip_bytes({"USDJPY-2024-01.csv": text.replace(old, new, 1)})


# ---------------------------------------------------------------------------
# Request identity and pair normalization
# ---------------------------------------------------------------------------


def test_pair_spellings_normalize_to_one_deterministic_request(adapter):
    spellings = ["usd/jpy", "USDJPY", "USD-JPY", "USD_JPY", " Usd / Jpy "]
    requests = [adapter.build_monthly_archive_request(spelling, YEAR, MONTH) for spelling in spellings]
    expected_url = "https://www.truefx.com/dev/data/2024-01/USDJPY-2024-01.zip"
    for request in requests:
        assert request.url == expected_url
        assert request.method == "GET"
        assert request.query == ()
        assert request.headers == ()
        assert request.credential_query == ()
    request_ids = {request.request_id() for request in requests}
    assert len(request_ids) == 1


@pytest.mark.parametrize(
    "bad_pair",
    ["USDD", "USD/U", "USD/USD", "us", "US1/JPY", "USD/JP!", "", "USD/JPY/EUR", "USD-", "-JPY"],
)
def test_invalid_pairs_are_refused(adapter, bad_pair):
    with pytest.raises(AdapterError) as exc:
        adapter.build_monthly_archive_request(bad_pair, YEAR, MONTH)
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


@pytest.mark.parametrize("bad_month", [0, 13, -1])
def test_out_of_range_month_is_refused(adapter, bad_month):
    with pytest.raises(AdapterError) as exc:
        adapter.build_monthly_archive_request(PAIR, YEAR, bad_month)
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_non_real_month_is_refused(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.build_monthly_archive_request(PAIR, 10**5, 1)  # year out of calendar range
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"
    with pytest.raises(AdapterError) as exc:
        adapter.parse_tick_csv(
            fixture_bytes(FIXTURE_CSV).decode("utf-8"), pair=PAIR, year=2024, month=13
        )
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_parse_archive_happy_path(adapter):
    response = archive_response(adapter, zip_bytes())
    output = adapter.parse_archive(response, pair=PAIR, year=YEAR, month=MONTH)

    # Three ticks x (bid, ask), in file order.
    assert [(r.field, r.value) for r in output.records] == [
        ("bid", 141.085),
        ("ask", 141.115),
        ("bid", 141.090),
        ("ask", 141.120),
        ("bid", 141.095),
        ("ask", 141.125),
    ]
    first = output.records[0]
    assert first.source_id == "TRUEFX"
    assert first.dataset_id == TOP_OF_BOOK_TICKS_DATASET
    assert first.entity_id == "FX:USDJPY"
    assert first.unit == PRICE_UNIT
    # TrueFX timestamps are GMT by spec: parsed as naive, attached to UTC.
    assert first.event_time_utc == datetime(2024, 1, 1, 22, 0, 0, 123000, tzinfo=UTC)
    assert first.effective_time_utc is None
    assert first.retrieved_time_utc == RETRIEVED_TIME
    assert first.license_id == "truefx-internal-use-v1"
    assert first.normalizer_version == "truefx-adapter-1.0.0"
    # Provenance binds to the real archive bytes, not a placeholder.
    assert output.raw_sha256 == response.sha256_hex()
    assert all(record.raw_sha256 == response.sha256_hex() for record in output.records)

    codes = output.note_codes()
    assert TRUEFX_GMT_PARSED_AS_UTC in codes
    assert TRUEFX_MONTH_END_UPPER_BOUND in codes
    assert TRUEFX_NOT_SWAP_ROLLOVER_AUTHORITY in codes


def test_availability_is_end_of_month_upper_bound_never_exact(adapter):
    output = parse_fixture(adapter)
    month_end = datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC)  # DF-ISSUE-1: next-day exclusive end
    for record in output.records:
        assert record.available_time_utc == month_end
        assert record.vintage_time_utc == month_end
    assert TRUEFX_MONTH_END_UPPER_BOUND in output.note_codes()

    # The adapter may only ever derive a date-only upper bound for monthly
    # archives: exact-availability consumers must be refused outright.
    evidence = adapter._month_end_evidence(YEAR, MONTH)
    assert evidence.basis is AvailabilityBasis.DATE_ONLY_UPPER_BOUND
    assert evidence.available_time_utc == month_end
    tick_time = datetime(2024, 1, 2, 0, 0, 0, 456000, tzinfo=UTC)
    timings = timings_from_evidence(tick_time, evidence)
    with pytest.raises(AdapterError) as exc:
        timings.require_exact_availability()
    assert exc.value.code == "NON_EXACT_AVAILABLE_TIME_FORBIDDEN"


def test_ticks_are_invisible_until_month_end(adapter):
    output = parse_fixture(adapter)
    for record in output.records:
        assert not record.eligible_at(datetime(2024, 1, 15, tzinfo=UTC))
        assert record.eligible_at(datetime(2024, 2, 1, tzinfo=UTC))


# ---------------------------------------------------------------------------
# Mandatory guards
# ---------------------------------------------------------------------------


def test_swap_rollover_financing_fields_are_refused(adapter):
    for field in ("swap", "swap_rate", "rollover", "tom_next", "financing"):
        with pytest.raises(AdapterError) as exc:
            adapter.refuse_forbidden_field(field)
        assert exc.value.code == "FORBIDDEN_INFERENCE_FIELD"
    assert TruefxAdapter.forbidden_fields == ("swap", "swap_rate", "rollover", "tom_next", "financing")


def test_not_swap_authority_note_is_carried(adapter):
    output = parse_fixture(adapter)
    assert TRUEFX_NOT_SWAP_ROLLOVER_AUTHORITY in output.note_codes()


def test_indicative_pricing_role_is_explicit(adapter):
    output = parse_fixture(adapter)
    # Naming boundary: indicative top-of-book dataset and PRICE unit only.
    assert output.dataset_id == TOP_OF_BOOK_TICKS_DATASET
    assert all(record.unit == PRICE_UNIT for record in output.records)
    assert all(record.field in {"bid", "ask"} for record in output.records)


# ---------------------------------------------------------------------------
# Row-level refusals (fail-closed, no coercion)
# ---------------------------------------------------------------------------


def test_malformed_row_is_refused(adapter):
    # Three columns.
    with pytest.raises(AdapterError) as exc:
        adapter.parse_archive(
            archive_response(adapter, csv_variant(adapter, "141.090,141.120", "141.090")),
            pair=PAIR,
            year=YEAR,
            month=MONTH,
        )
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"
    # Five columns.
    with pytest.raises(AdapterError) as exc:
        adapter.parse_archive(
            archive_response(adapter, csv_variant(adapter, "141.090,141.120", "141.090,141.120,7")),
            pair=PAIR,
            year=YEAR,
            month=MONTH,
        )
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_bad_timestamp_format_is_refused(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.parse_tick_csv(
            "USD/JPY,2024-01-02 00:00:00.456,141.090,141.120\n",
            pair=PAIR,
            year=YEAR,
            month=MONTH,
        )
    assert exc.value.code == "SCHEMA_TIMESTAMP_INVALID"


def test_pair_mismatch_is_refused(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.parse_archive(
            archive_response(adapter, csv_variant(adapter, "USD/JPY", "EUR/USD")),
            pair=PAIR,
            year=YEAR,
            month=MONTH,
        )
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_out_of_month_timestamp_is_refused(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.parse_archive(
            archive_response(adapter, csv_variant(adapter, "20240102", "20240202")),
            pair=PAIR,
            year=YEAR,
            month=MONTH,
        )
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_crossed_quote_is_refused(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.parse_archive(
            archive_response(adapter, csv_variant(adapter, "141.090,141.120", "141.121,141.120")),
            pair=PAIR,
            year=YEAR,
            month=MONTH,
        )
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_non_positive_price_is_refused(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.parse_tick_csv("USD/JPY,20240102 00:00:00.456,0,141.120\n", pair=PAIR, year=YEAR, month=MONTH)
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"
    with pytest.raises(AdapterError) as exc:
        adapter.parse_tick_csv(
            "USD/JPY,20240102 00:00:00.456,-1.0,141.120\n", pair=PAIR, year=YEAR, month=MONTH
        )
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_non_numeric_price_is_refused(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.parse_tick_csv(
            "USD/JPY,20240102 00:00:00.456,abc,141.120\n", pair=PAIR, year=YEAR, month=MONTH
        )
    assert exc.value.code == "SCHEMA_VALUE_TYPE_MISMATCH"


def test_duplicate_tick_timestamp_is_refused(adapter):
    text = fixture_bytes(FIXTURE_CSV).decode("utf-8")
    first_line = text.splitlines()[0]
    with pytest.raises(AdapterError) as exc:
        adapter.parse_archive(
            archive_response(adapter, zip_bytes({"USDJPY-2024-01.csv": text + first_line + "\n"})),
            pair=PAIR,
            year=YEAR,
            month=MONTH,
        )
    assert exc.value.code == "DUPLICATE_RECORD_ID"


# ---------------------------------------------------------------------------
# Archive-level refusals
# ---------------------------------------------------------------------------


def test_multi_member_archive_is_refused(adapter):
    members = {
        "USDJPY-2024-01.csv": fixture_bytes(FIXTURE_CSV),
        "EURUSD-2024-01.csv": fixture_bytes(FIXTURE_CSV),
    }
    with pytest.raises(AdapterError) as exc:
        adapter.parse_archive(archive_response(adapter, zip_bytes(members)), pair=PAIR, year=YEAR, month=MONTH)
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_empty_archive_is_refused(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.parse_archive(archive_response(adapter, zip_bytes({})), pair=PAIR, year=YEAR, month=MONTH)
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_non_csv_member_is_refused(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.parse_archive(
            archive_response(adapter, zip_bytes({"USDJPY-2024-01.txt": fixture_bytes(FIXTURE_CSV)})),
            pair=PAIR,
            year=YEAR,
            month=MONTH,
        )
    assert exc.value.code == "SCHEMA_INVARIANT_VIOLATED"


def test_non_zip_body_is_refused(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.parse_archive(
            archive_response(adapter, b"<html>not a zip</html>", content_type="application/zip"),
            pair=PAIR,
            year=YEAR,
            month=MONTH,
        )
    assert exc.value.code == "SCHEMA_VALUE_TYPE_MISMATCH"


def test_unexpected_content_type_is_refused(adapter):
    with pytest.raises(AdapterError) as exc:
        adapter.parse_archive(
            archive_response(adapter, zip_bytes(), content_type="text/html"),
            pair=PAIR,
            year=YEAR,
            month=MONTH,
        )
    assert exc.value.code == "CONTENT_TYPE_UNEXPECTED"


def test_unexpected_status_is_refused(adapter):
    request = adapter.build_monthly_archive_request(PAIR, YEAR, MONTH)
    response = response_for(request, zip_bytes(), content_type="application/zip", status=404, reason="Not Found")
    with pytest.raises(AdapterError) as exc:
        adapter.parse_archive(response, pair=PAIR, year=YEAR, month=MONTH)
    assert exc.value.code == "HTTP_STATUS_UNEXPECTED"


# ---------------------------------------------------------------------------
# Determinism and authority posture
# ---------------------------------------------------------------------------


def test_two_pull_equality(adapter):
    first = parse_fixture(adapter)
    second = parse_fixture(adapter)
    assert first.request_id == second.request_id
    assert first.raw_sha256 == second.raw_sha256
    assert [r.canonical_bytes() for r in first.records] == [r.canonical_bytes() for r in second.records]
    assert first.notes == second.notes
    assert first.parser_version == second.parser_version


def test_authority_verdict_stays_candidate_not_authorized():
    # license_id is a pure label; the verdict must remain NOT authorized.
    assert TruefxAdapter.authority_status is AuthorityStatus.CANDIDATE_NOT_AUTHORIZED
    assert TruefxAdapter.authority_status is not AuthorityStatus.AUTHORIZED_INTERNAL_RESEARCH
    assert TruefxAdapter.license_id == "truefx-internal-use-v1"  # label only

    # With TrueFX internal-use status UNKNOWN/PENDING, fail-closed evaluation
    # can only yield CANDIDATE_NOT_AUTHORIZED.
    evidence = AuthorityEvidence(
        source_id="TRUEFX",
        terms_captured=False,
        internal_research_allowed=None,
        local_storage_allowed=None,
        redistribution_allowed=None,
        entitlement_active=True,
        deterministic_retrieval=True,
        historical_available_time=True,
        raw_hashes_recorded=True,
        account_or_key_required=False,
        account_or_key_authorized=False,
    )
    decision = evaluate_authority(evidence)
    assert decision.status is AuthorityStatus.CANDIDATE_NOT_AUTHORIZED
    assert decision.usable_for_scored_research is False
