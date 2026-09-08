"""Tests for the V5 SEC companyfacts sanitizing shim.

Fixture bytes are hand-written (no production data).  Each pathology observed
in live SEC payloads is reproduced and the shim must (a) drop it with an
explicit counter and (b) leave the payload parseable by the FROZEN adapter
with unchanged record semantics for the surviving facts.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from research.data_fusion.adapters.base import RawResponse, RequestSpec, AdapterError
from research.data_fusion.adapters.sec import SecAdapter
from research.assets.stocks.sec_sanitize import (
    SANITIZER_VERSION,
    chunk_companyfacts,
    sanitize_companyfacts,
)

UTC = timezone.utc
RETRIEVED = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


def _payload(**facts: dict) -> dict:
    return {"cik": 1, "entityName": "Fixture Issuer", "facts": facts}


def _instant(val, *, end="2023-12-31", filed="2024-01-08", accn="0000000001-24-000002",
             fp="FY", form="10-K"):
    return {"end": end, "val": val, "accn": accn, "fy": 2023, "fp": fp, "form": form, "filed": filed}


def _response(payload: dict) -> RawResponse:
    request = RequestSpec(
        source_id="SEC_EDGAR",
        url="https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json",
    )
    return RawResponse(
        request_id=request.request_id(),
        url=request.full_url(),
        status=200,
        reason="OK",
        headers=(("content-type", "application/json"),),
        body=json.dumps(payload).encode("utf-8"),
        retrieved_time_utc=RETRIEVED,
    )


def _parse(payload: dict):
    sanitized, stats = sanitize_companyfacts(payload)
    adapter = SecAdapter()
    return adapter.parse_company_facts(_response(sanitized)), stats


class TestPathologies:
    def test_null_label_and_description_are_deleted_not_dropped(self) -> None:
        payload = _payload(**{
            "us-gaap": {"Assets": {"label": None, "description": None,
                                   "units": {"USD": [_instant(5000.0)]}}},
        })
        (output, stats) = _parse(payload)
        assert len(output.records) == 1
        assert stats.deleted_null_label == 1
        assert stats.deleted_null_description == 1
        assert stats.total_dropped() == 0

    def test_null_and_nonnumeric_vals_dropped_with_counter(self) -> None:
        payload = _payload(**{
            "us-gaap": {"Assets": {"units": {"USD": [
                _instant(None),
                _instant("not-a-number"),
                _instant(5000.0),
            ]}}},
        })
        (output, stats) = _parse(payload)
        assert len(output.records) == 1
        assert stats.dropped_null_val == 2

    def test_empty_fp_and_form_dropped(self) -> None:
        payload = _payload(**{
            "us-gaap": {"Assets": {"units": {"USD": [
                {**_instant(5000.0), "fp": ""},
                {**_instant(5000.0), "form": " "},
                _instant(5100.0, filed="2024-04-15", accn="0000000001-24-000003", fp="Q1", form="10-Q/A"),
            ]}}},
        })
        (output, stats) = _parse(payload)
        assert len(output.records) == 1
        assert stats.dropped_empty_fp == 1
        assert stats.dropped_empty_form == 1
        assert output.records[0].value == 5100.0

    def test_malformed_dates_dropped_not_fatal(self) -> None:
        payload = _payload(**{
            "us-gaap": {"Assets": {"units": {"USD": [
                {**_instant(5000.0), "end": "20231231"},
                _instant(5000.0),
            ]}}},
        })
        (output, stats) = _parse(payload)
        assert len(output.records) == 1
        assert stats.dropped_malformed_dates == 1

    def test_identical_duplicates_collapse(self) -> None:
        payload = _payload(**{
            "us-gaap": {"Assets": {"units": {"USD": [
                _instant(5000.0), _instant(5000.0),
            ]}}},
        })
        (output, stats) = _parse(payload)
        assert len(output.records) == 1
        assert stats.dropped_duplicate_identical == 1

    def test_conflicting_duplicates_drop_both(self) -> None:
        payload = _payload(**{
            "us-gaap": {"Assets": {"units": {"USD": [
                _instant(5000.0), _instant(9999.0),
            ]}}},
        })
        (output, stats) = _parse(payload)
        assert len(output.records) == 0
        assert stats.dropped_duplicate_conflicting == 1

    def test_duration_facts_still_handled_by_frozen_adapter(self) -> None:
        payload = _payload(**{
            "us-gaap": {"Revenues": {"units": {"USD": [
                {"start": "2023-01-01", **_instant(100.0)},
            ]}}},
        })
        (output, stats) = _parse(payload)
        assert len(output.records) == 0
        assert stats.total_dropped() == 0  # duration skip belongs to the frozen adapter, not the shim

    def test_structural_corruption_still_fails_closed(self) -> None:
        payload = {"cik": 1, "facts": {"us-gaap": {"Assets": "not-a-mapping"}}}
        with pytest.raises(AdapterError):
            _parse(payload)


class TestSemanticsUnchanged:
    def test_surviving_facts_keep_frozen_availability_semantics(self) -> None:
        payload = _payload(**{
            "us-gaap": {"Assets": {"units": {"USD": [_instant(5000.0)]}}},
        })
        output, _ = _parse(payload)
        record = output.records[0]
        assert record.available_time_utc == datetime(2024, 1, 8, 23, 59, 59, tzinfo=UTC)
        assert record.event_time_utc == datetime(2023, 12, 31, 0, 0, 0, tzinfo=UTC)
        assert record.raw_sha256  # sanitized payload hash, distinct from raw disk bytes
        assert record.normalizer_version

    def test_raw_payload_not_mutated(self) -> None:
        payload = _payload(**{
            "us-gaap": {"Assets": {"label": None, "units": {"USD": [_instant(None), _instant(1.0)]}}},
        })
        before = json.dumps(payload, sort_keys=True)
        sanitize_companyfacts(payload)
        assert json.dumps(payload, sort_keys=True) == before

    def test_sanitizer_version_pinned(self) -> None:
        assert SANITIZER_VERSION == "sec-companyfacts-sanitize-1.0.0"


def test_filed_before_end_dropped_not_fatal() -> None:
    payload = _payload(**{
        "us-gaap": {"Assets": {"units": {"USD": [
            _instant(5000.0, end="2010-12-31", filed="2010-11-05"),
            _instant(5100.0),
        ]}}},
    })
    output, stats = _parse(payload)
    assert len(output.records) == 1
    assert stats.dropped_filed_before_end == 1
    assert output.records[0].value == 5100.0


def test_chunking_preserves_records_semantically() -> None:
    payload = _payload(**{
        "us-gaap": {"Assets": {"units": {"USD": [
            _instant(5000.0),
            {**_instant(5100.0), "accn": "0000000001-24-000003",
             "filed": "2024-04-15", "fp": "Q1", "form": "10-Q/A"},
        ]}}},
        "dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": [
            {"end": "2023-12-31", "val": 1000, "accn": "0000000001-24-000001",
             "fy": 2024, "fp": "Q1", "form": "8-K", "filed": "2024-01-03"},
        ]}}},
    })
    sanitized, stats = sanitize_companyfacts(payload)
    chunks = chunk_companyfacts(sanitized)
    assert len(chunks) == 2
    adapter = SecAdapter()
    chunk_records = []
    for _tag, body in chunks:
        request = RequestSpec(
            source_id="SEC_EDGAR",
            url="https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json",
        )
        response = RawResponse(
            request_id=request.request_id(), url=request.full_url(), status=200,
            reason="OK", headers=(("content-type", "application/json"),),
            body=body, retrieved_time_utc=RETRIEVED,
        )
        chunk_records.extend(adapter.parse_company_facts(response).records)
    whole_body = json.dumps(sanitized, sort_keys=True).encode()
    request = RequestSpec(
        source_id="SEC_EDGAR",
        url="https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json",
    )
    whole = adapter.parse_company_facts(RawResponse(
        request_id=request.request_id(), url=request.full_url(), status=200,
        reason="OK", headers=(("content-type", "application/json"),),
        body=whole_body, retrieved_time_utc=RETRIEVED,
    )).records
    strip = lambda rs: sorted(
        (r.field, r.value, r.unit, r.event_time_utc.isoformat(),
         r.available_time_utc.isoformat()) for r in rs
    )
    assert strip(chunk_records) == strip(whole)
    assert stats.total_dropped() == 0
