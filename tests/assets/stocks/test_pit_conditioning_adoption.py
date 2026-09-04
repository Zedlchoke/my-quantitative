"""STOCKS-FREE-V5 P0 adoption regression (PLAN_stocks_v5.md §6.P0).

Pins, inside the stocks tree, that the adopted Data Fusion V1 core satisfies
the compatibility contract required before any V5 data or selection freeze:

1. a decision at session T can never read a row whose ``available_time_utc``
   is at or after the session gate (no-lookahead, mutation-pinned at the
   exact gate boundary);
2. the conditioning-lag rule: an availability stamp first influences the
   session AFTER the session it lands in;
3. vintage revisions supersede strictly after their own availability stamp;
4. filer-level SEC facts aggregate to the frozen sector cohort
   deterministically (input-order invariant) and survivorship-aware (a filer
   that stops filing keeps its pre-death history and is later absent by the
   availability gate, never by silent panel trimming);
5. the frozen adapter fixtures (SEC EDGAR company facts, ALFRED vintages)
   map through the fusion record schema onto the bridge unchanged — this is
   a schema/semantics proof on fixture bytes only and authorizes no data
   source (FRED/ALFRED data remains CANDIDATE_NOT_AUTHORIZED pending an
   owner key decision).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from research.data_fusion.adapters.base import (
    RawResponse,
    RequestSpec,
    midnight_utc,
    timings_from_evidence,
)
from research.data_fusion.adapters.fred import FredAdapter
from research.data_fusion.adapters.sec import SecAdapter
from research.data_fusion.models import NormalizedRecord
from research.assets.stocks.pit_conditioning import (
    aggregate_sector_asof,
    conditioning_panel,
    session_gate_utc,
    usable_for_session,
)

UTC = timezone.utc
FIXTURES = Path(__file__).resolve().parents[2] / "data_fusion" / "adapters" / "fixtures"
RETRIEVED = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

ASSETS = "us-gaap:Assets"


def _response(url: str, body: bytes) -> RawResponse:
    request = RequestSpec(source_id="adoption-test", url=url)
    return RawResponse(
        request_id=request.request_id(),
        url=request.full_url(),
        status=200,
        reason="OK",
        headers=(("content-type", "application/json"),),
        body=body,
        retrieved_time_utc=RETRIEVED,
    )


def _sec_fact_records() -> list[NormalizedRecord]:
    adapter = SecAdapter()
    response = _response(
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json",
        (FIXTURES / "sec_companyfacts.json").read_bytes(),
    )
    output = adapter.parse_company_facts(response)
    return list(output.records)


def _fred_records() -> list[NormalizedRecord]:
    adapter = FredAdapter()
    response = _response(
        "https://api.stlouisfed.org/fred/series/observations",
        (FIXTURES / "fred_alfred_obs.json").read_bytes(),
    )
    output = adapter.parse_observations(response, series_id="CPIAUCSL", unit="lin")
    return list(output.records)


def _fact(
    entity: str,
    value: float,
    *,
    end: date,
    filed: date,
    field: str = ASSETS,
) -> NormalizedRecord:
    adapter = SecAdapter()
    event_time = midnight_utc(end)
    timings = timings_from_evidence(
        event_time,
        adapter._filing_evidence(filed, "synthetic adoption test evidence"),
        effective_time_utc=event_time,
    )
    return adapter.make_record(
        dataset_id="company_facts",
        entity_id=entity,
        field_name=field,
        value=value,
        unit="USD",
        timings=timings,
        retrieved_time_utc=RETRIEVED,
        request_id="adoption-test",
        raw_sha256="0" * 64,
    )


class TestNoLookaheadGate:
    def test_sec_filing_is_invisible_on_its_own_session(self) -> None:
        records = _sec_fact_records()
        assets = [r for r in records if r.field == ASSETS]
        assert assets, "fixture must carry us-gaap:Assets instant facts"
        original = assets[0]
        # filed 2024-01-08 -> availability 2024-01-08T23:59:59Z upper bound
        assert original.available_time_utc == datetime(2024, 1, 8, 23, 59, 59, tzinfo=UTC)
        assert not usable_for_session(original, date(2024, 1, 8))
        assert usable_for_session(original, date(2024, 1, 9))

    def test_gate_boundary_is_strict(self) -> None:
        # mutation pin: a row whose availability EQUALS the gate midnight must
        # stay invisible for that session (strict <), and one second before
        # midnight must be visible
        record = _fact("CIK0000000001", 1.0, end=date(2024, 1, 1), filed=date(2024, 1, 1))
        gate = session_gate_utc(date(2024, 1, 2))
        at_gate = NormalizedRecord(
            **{**record.__dict__, "available_time_utc": gate}
        ) if hasattr(record, "__dict__") else record
        # NormalizedRecord is frozen/slots; rebuild explicitly instead
        at_gate = NormalizedRecord(
            source_id=record.source_id,
            dataset_id=record.dataset_id,
            entity_id=record.entity_id,
            field=record.field,
            value=record.value,
            unit=record.unit,
            event_time_utc=record.event_time_utc,
            available_time_utc=gate,
            effective_time_utc=record.effective_time_utc,
            vintage_time_utc=record.vintage_time_utc,
            retrieved_time_utc=record.retrieved_time_utc,
            raw_path=record.raw_path,
            raw_sha256=record.raw_sha256,
            license_id=record.license_id,
            entitlement_id=record.entitlement_id,
            normalizer_version=record.normalizer_version,
        )
        assert not usable_for_session(at_gate, date(2024, 1, 2))
        before_gate = NormalizedRecord(
            source_id=at_gate.source_id,
            dataset_id=at_gate.dataset_id,
            entity_id=at_gate.entity_id,
            field=at_gate.field,
            value=at_gate.value,
            unit=at_gate.unit,
            event_time_utc=at_gate.event_time_utc,
            available_time_utc=gate - timedelta(seconds=1),
            effective_time_utc=at_gate.effective_time_utc,
            vintage_time_utc=at_gate.vintage_time_utc,
            retrieved_time_utc=at_gate.retrieved_time_utc,
            raw_path=at_gate.raw_path,
            raw_sha256=at_gate.raw_sha256,
            license_id=at_gate.license_id,
            entitlement_id=at_gate.entitlement_id,
            normalizer_version=at_gate.normalizer_version,
        )
        assert usable_for_session(before_gate, date(2024, 1, 2))

    def test_stamp_on_non_session_day_first_usable_next_session(self) -> None:
        # availability lands on Saturday 2024-01-13; the last session before
        # it is Friday 2024-01-12, so Monday 2024-01-15 is the first session
        # the row may influence
        record = _fact("CIK0000000001", 2.0, end=date(2024, 1, 5), filed=date(2024, 1, 13))
        assert not usable_for_session(record, date(2024, 1, 12))
        assert usable_for_session(record, date(2024, 1, 15))


class TestVintageRevisions:
    def test_refile_supersedes_only_after_its_own_availability(self) -> None:
        records = _sec_fact_records()
        # 10-K filed 2024-01-08 val 5000; 10-Q/A re-filed 2024-04-15 val 5100
        panel_xlk = aggregate_sector_asof(
            records,
            filer_sectors={"CIK0000000001": "XLF"},
            decision_session=date(2024, 4, 15),
            field=ASSETS,
        )
        assert panel_xlk["XLF"].value == 5000.0
        panel_next = aggregate_sector_asof(
            records,
            filer_sectors={"CIK0000000001": "XLF"},
            decision_session=date(2024, 4, 16),
            field=ASSETS,
        )
        assert panel_next["XLF"].value == 5100.0


class TestSectorAggregation:
    def _panel_records(self) -> list[NormalizedRecord]:
        alive_1 = _fact("CIK0000000010", 100.0, end=date(2023, 12, 31), filed=date(2024, 1, 8))
        alive_2 = _fact("CIK0000000020", 300.0, end=date(2023, 12, 31), filed=date(2024, 1, 9))
        # dead filer: last filing available 2024-01-30, never files again
        dead = _fact("CIK0000000030", 500.0, end=date(2023, 12, 31), filed=date(2024, 1, 30))
        # live filers keep filing annually (10-K for FY2024 filed 2025-02-03)
        alive_1_fy24 = _fact(
            "CIK0000000010", 120.0, end=date(2024, 12, 31), filed=date(2025, 2, 3)
        )
        alive_2_fy24 = _fact(
            "CIK0000000020", 330.0, end=date(2024, 12, 31), filed=date(2025, 2, 4)
        )
        return [alive_1, alive_2, dead, alive_1_fy24, alive_2_fy24]

    def test_deterministic_under_input_permutation(self) -> None:
        records = self._panel_records()
        filers = {
            "CIK0000000010": "XLK",
            "CIK0000000020": "XLK",
            "CIK0000000030": "XLK",
        }
        first = aggregate_sector_asof(
            records,
            filer_sectors=filers,
            decision_session=date(2024, 3, 1),
            field=ASSETS,
            max_filing_gap_days=400,
        )
        second = aggregate_sector_asof(
            list(reversed(records)),
            filer_sectors=filers,
            decision_session=date(2024, 3, 1),
            field=ASSETS,
            max_filing_gap_days=400,
        )
        assert first == second
        # single-vintage equal-weight mean of the three filers at FY2023
        assert first["XLK"].value == pytest.approx((100.0 + 300.0 + 500.0) / 3)
        assert first["XLK"].filers_included == 3
        assert first["XLK"].filers_mapped == 3

    def test_survivorship_aware_dead_filer_keeps_history(self) -> None:
        records = self._panel_records()
        filers = {
            "CIK0000000010": "XLK",
            "CIK0000000020": "XLK",
            "CIK0000000030": "XLK",
        }
        before_death = aggregate_sector_asof(
            records,
            filer_sectors=filers,
            decision_session=date(2024, 2, 1),
            field=ASSETS,
            max_filing_gap_days=400,
        )
        after_death = aggregate_sector_asof(
            records,
            filer_sectors=filers,
            decision_session=date(2025, 6, 2),
            field=ASSETS,
            max_filing_gap_days=400,
        )
        # while the dead filer's 2024-01-30 filing is fresh it participates;
        # once the 400-day filing gap is exceeded it drops out by an explicit
        # filing-clock rule while the annually-filing live filers stay in and
        # the aggregate moves to their FY2024 vintage
        assert before_death["XLK"].filers_included == 3
        assert before_death["XLK"].value == pytest.approx((100.0 + 300.0 + 500.0) / 3)
        assert after_death["XLK"].filers_included == 2
        assert after_death["XLK"].filers_mapped == 3
        assert after_death["XLK"].effective_date == date(2024, 12, 31)
        assert after_death["XLK"].value == pytest.approx((120.0 + 330.0) / 2)

    def test_sector_with_no_usable_rows_is_absent(self) -> None:
        records = self._panel_records()
        panel = aggregate_sector_asof(
            records,
            filer_sectors={"CIK0000000010": "XLE"},
            decision_session=date(2024, 1, 8),
            field=ASSETS,
        )
        assert "XLE" not in panel

    def test_panel_never_reads_future_sessions(self) -> None:
        records = self._panel_records()
        filers = {"CIK0000000010": "XLK"}
        sessions = [date(2024, 1, 8), date(2024, 1, 9), date(2024, 1, 10)]
        panel = conditioning_panel(
            records, filer_sectors=filers, sessions=sessions, field=ASSETS
        )
        assert panel[date(2024, 1, 8)] == {}
        assert panel[date(2024, 1, 9)] != {}
        assert panel[date(2024, 1, 10)] != {}


class TestFrozenFixtureSchemaMapping:
    def test_sec_company_facts_map_onto_bridge(self) -> None:
        records = _sec_fact_records()
        # duration facts (Revenues with a start) are skipped by the frozen
        # adapter; instant Assets facts map through
        assert {r.field for r in records} >= {ASSETS, "dei:EntityCommonStockSharesOutstanding"}
        panel = aggregate_sector_asof(
            records,
            filer_sectors={"CIK0000000001": "XLF"},
            decision_session=date(2024, 1, 9),
            field=ASSETS,
        )
        observation = panel["XLF"]
        assert observation.effective_date == date(2023, 12, 31)
        assert observation.value == 5000.0
        assert observation.filers_included == 1

    def test_fred_vintage_schema_maps_through_gate(self) -> None:
        records = _fred_records()
        # two vintages for observation date 2023-12-01: realtime 2024-01-12
        # (272.712) and 2024-02-09 revision (272.690); the '.' row is null
        assert len(records) == 3
        assert any(r.value is None for r in records)
        jan = [r for r in records if r.value is not None][0]
        # vintage day 2024-01-12 (Friday) -> end-of-day upper bound
        assert jan.available_time_utc == datetime(2024, 1, 12, 23, 59, 59, tzinfo=UTC)
        assert not usable_for_session(jan, date(2024, 1, 12))
        assert usable_for_session(jan, date(2024, 1, 15))
