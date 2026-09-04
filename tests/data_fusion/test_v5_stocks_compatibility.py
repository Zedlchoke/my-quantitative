"""V5-P0 stocks-compatibility harness for the frozen Data Fusion V1 core.

Proves, inside the stocks tree and against offline fixtures only:

1. SEC rows (submissions + instant company facts) map onto the fusion
   ``NormalizedRecord`` schema and carry availability stamped from the
   FILING timestamp, never the retrieval time;
2. FRED/ALFRED vintage-date availability semantics: a decision at T cannot
   see a vintage dated after T;
3. PIT regression pin: a reader querying as-of T excludes every row with
   ``available_time_utc > T`` (the plan's binding rule);
4. sector aggregation over filer-level facts is deterministic (byte-identical
   across independent calls and stable under input reordering) and
   survivorship-aware (the filer set at each as-of is derived from
   availability, not a fixed modern membership list).

No network, no downloads, no filer-universe construction (P2/A3 authority
work), no PnL.
"""

import json
from datetime import date, datetime, timezone

from research.data_fusion.models import NormalizedRecord
from research.data_fusion.pit import select_asof
from research.data_fusion.stocks_compat import sector_mean_asof_bytes
from research.data_fusion.adapters.base import (
    end_of_utc_day,
    midnight_utc,
)
from research.data_fusion.adapters.fred import FredAdapter
from research.data_fusion.adapters.sec import SecAdapter

from .adapters.conftest import RETRIEVED_TIME, fixture_bytes, response_for

UTC = timezone.utc

SUBMISSIONS_FIXTURE = "sec_submissions.json"
COMPANY_FACTS_FIXTURE = "sec_companyfacts.json"
FRED_OBS_FIXTURE = "fred_alfred_obs.json"
FRED_VINTAGEDATES_FIXTURE = "fred_vintagedates.json"

_OWNER_KEY = "offline-test-key-not-a-real-credential"


def _sec_submissions(adapter: SecAdapter):
    request = adapter.build_submissions_request("1")
    return adapter.parse_submissions(response_for(request, fixture_bytes(SUBMISSIONS_FIXTURE)))


def _sec_company_facts(adapter: SecAdapter):
    request = adapter.build_company_facts_request("1")
    return adapter.parse_company_facts(
        response_for(request, fixture_bytes(COMPANY_FACTS_FIXTURE))
    )


def _fred_observations(adapter: FredAdapter):
    request = adapter.build_alfred_observations_request("CPIAUCSL", api_key=_OWNER_KEY)
    return adapter.parse_observations(
        response_for(request, fixture_bytes(FRED_OBS_FIXTURE)),
        series_id="CPIAUCSL",
        unit="INDEX_1982_100",
    )


def _fred_vintagedates(adapter: FredAdapter):
    request = adapter.build_vintagedates_request("CPIAUCSL", api_key=_OWNER_KEY)
    return adapter.parse_vintagedates(
        response_for(request, fixture_bytes(FRED_VINTAGEDATES_FIXTURE)),
        series_id="CPIAUCSL",
    )


def _pin_record(
    value,
    available_day: date,
    *,
    entity_id: str = "CIK0000000001",
    field: str = "us-gaap:Assets",
) -> NormalizedRecord:
    """Hand-built fusion table row with an explicit availability stamp."""

    return NormalizedRecord(
        source_id="SEC_EDGAR",
        dataset_id="company_facts",
        entity_id=entity_id,
        field=field,
        value=value,
        unit="USD",
        event_time_utc=midnight_utc(date(2023, 12, 31)),
        available_time_utc=end_of_utc_day(available_day),
        effective_time_utc=None,
        vintage_time_utc=end_of_utc_day(available_day),
        retrieved_time_utc=datetime(2024, 6, 1, tzinfo=UTC),
        raw_path="sec_edgar/v5-pin/raw",
        raw_sha256="a" * 64,
        license_id="sec-public-domain-v1",
        entitlement_id="anonymous-no-key",
        normalizer_version="v5-p0-pit-pin-1",
    )


# ---------------------------------------------------------------------------
# 1. SEC row mapping onto the fusion record schema
# ---------------------------------------------------------------------------


def test_sec_rows_map_onto_fusion_schema_with_filing_availability():
    adapter = SecAdapter()
    facts = _sec_company_facts(adapter)
    subs = _sec_submissions(adapter)

    for record in facts.records + subs.records:
        # Constructing NormalizedRecord validates the full schema (UTC
        # awareness, availability <= retrieval, 64-hex raw digest, ...).
        assert isinstance(record, NormalizedRecord)
        assert record.source_id == "SEC_EDGAR"
        assert record.license_id and record.entitlement_id and record.normalizer_version

    # Instant facts only: the duration Revenues fact (carries "start") is
    # skipped by the adapter, never coerced into an instant (3 instants kept
    # = dei shares + two Assets vintages).
    assert len(facts.records) == 3
    assets = sorted((r for r in facts.records if r.field == "us-gaap:Assets"), key=lambda r: r.value)
    assert [r.value for r in assets] == [5000, 5100]

    # TRUE availability stamps come from the FILING date as end-of-UTC-day
    # upper bounds, not from retrieval time (2026-01-01).
    assert assets[0].available_time_utc == end_of_utc_day(date(2024, 1, 8))
    assert assets[1].available_time_utc == end_of_utc_day(date(2024, 4, 15))
    assert all(record.available_time_utc != RETRIEVED_TIME for record in facts.records + subs.records)
    assert all(record.vintage_time_utc == record.available_time_utc for record in facts.records)

    # Submissions availability likewise follows filingDate, not acceptance or
    # retrieval time; the accepted 8-K's event time is its acceptance instant.
    assert sorted(r.available_time_utc for r in subs.records) == [
        end_of_utc_day(date(2024, 1, 3)),
        end_of_utc_day(date(2024, 1, 8)),
    ]
    accepted = next(r for r in subs.records if r.value == "0000000001-24-000001")
    assert accepted.event_time_utc == datetime(2024, 1, 3, 14, 30, tzinfo=UTC)

    # Revision selection follows availability: a decision between the two
    # filings sees only the first filing's value.
    early = select_asof(assets, datetime(2024, 3, 1, tzinfo=UTC))
    assert early is not None and early.value == 5000
    late = select_asof(assets, datetime(2024, 5, 1, tzinfo=UTC))
    assert late is not None and late.value == 5100


# ---------------------------------------------------------------------------
# 2. FRED/ALFRED vintage availability semantics
# ---------------------------------------------------------------------------


def test_fred_vintage_availability_semantics():
    adapter = FredAdapter()
    obs = _fred_observations(adapter)
    vdates = _fred_vintagedates(adapter)

    # Two vintages of the 2023-12-01 observation stay append-only; the "."
    # row parses to an explicit null record.
    assert len(obs.records) == 3
    dec_rows = [r for r in obs.records if r.event_time_utc == midnight_utc(date(2023, 12, 1))]
    assert len(dec_rows) == 2
    v_jan = next(r for r in dec_rows if r.vintage_time_utc == end_of_utc_day(date(2024, 1, 12)))
    v_feb = next(r for r in dec_rows if r.vintage_time_utc == end_of_utc_day(date(2024, 2, 9)))
    assert (v_jan.value, v_feb.value) == (272.712, 272.690)

    # Availability is the end of the vintage UTC day: a decision on Jan 15
    # cannot see a vintage dated Feb 9.
    t = datetime(2024, 1, 15, tzinfo=UTC)
    assert v_feb.available_time_utc > t
    selected = select_asof(dec_rows, t)
    assert selected is v_jan and selected.value == 272.712
    # After the later vintage becomes available, the revision is adopted.
    later = select_asof(dec_rows, datetime(2024, 3, 1, tzinfo=UTC))
    assert later is v_feb and later.value == 272.690

    # Vintage-date records themselves carry end-of-vintage-day availability.
    assert len(vdates.records) == 2
    for record in vdates.records:
        assert record.available_time_utc == end_of_utc_day(date.fromisoformat(str(record.value)))

    # The "." missing marker becomes an explicit null, still availability-
    # stamped, never silently dropped or forward-filled.
    nulls = [r for r in obs.records if r.value is None]
    assert len(nulls) == 1
    assert nulls[0].available_time_utc == end_of_utc_day(date(2024, 1, 12))


# ---------------------------------------------------------------------------
# 3. PIT regression pin: as-of readers exclude future-availability rows
# ---------------------------------------------------------------------------


def test_pit_pin_asof_reader_excludes_every_future_availability_row():
    table = [
        _pin_record(100, date(2024, 1, 5)),
        _pin_record(200, date(2024, 1, 10)),
        _pin_record(300, date(2024, 2, 1)),
    ]

    # Sweep daily decisions across and beyond the revision window.
    sweep = [datetime(2024, 1, day, tzinfo=UTC) for day in range(1, 32)]
    sweep += [datetime(2024, 2, 15, tzinfo=UTC), datetime(2024, 3, 1, tzinfo=UTC)]
    for decision in sweep:
        visible = [r for r in table if r.available_time_utc <= decision]
        selected = select_asof(table, decision)
        if not visible:
            assert selected is None
            continue
        # THE BINDING RULE: no row with available_time_utc > T is returned.
        assert selected is not None and selected.available_time_utc <= decision
        assert selected in visible
        # The winner is the latest-available visible vintage (fixed rank).
        expected = max(
            visible,
            key=lambda r: (r.available_time_utc, r.vintage_time_utc, r.retrieved_time_utc, r.raw_sha256),
        )
        assert selected is expected

    # Exact pin values at the boundaries.
    asof = lambda day: select_asof(table, datetime.combine(day, datetime.min.time(), tzinfo=UTC))
    assert asof(date(2024, 1, 4)) is None  # nothing available yet
    assert asof(date(2024, 1, 7)).value == 100  # first revision visible
    assert asof(date(2024, 1, 11)).value == 200  # second revision visible
    assert asof(date(2024, 1, 31)).value == 200  # Feb-1 row still hidden
    assert asof(date(2024, 2, 2)).value == 300  # third revision adopted
    # A decision exactly AT the availability stamp can see the row (<=).
    assert select_asof(table, end_of_utc_day(date(2024, 2, 1))).value == 300


def test_pit_pin_survives_input_order_and_idempotent_reappend():
    from research.data_fusion.pit import VintageSeries

    first = _pin_record(100, date(2024, 1, 5))
    second = _pin_record(200, date(2024, 1, 10))
    third = _pin_record(300, date(2024, 2, 1))

    for order in ([first, second, third], [third, first, second], [second, third, first]):
        assert select_asof(order, datetime(2024, 1, 20, tzinfo=UTC)).value == 200

    # Append-only series: re-appending byte-identical content is idempotent
    # and appending out of availability order cannot resurrect hidden rows.
    series = VintageSeries.started_by(first).append(third).append(second).append(third)
    assert [r.value for r in series.records] == [100, 300, 200]
    assert series.select(datetime(2024, 1, 20, tzinfo=UTC)).value == 200


# ---------------------------------------------------------------------------
# 4. Deterministic, survivorship-aware sector aggregation
# ---------------------------------------------------------------------------

_SECTOR_OF = {
    "CIK0000000001": "Information Technology",
    "CIK0000000002": "Information Technology",
    "CIK0000000003": "Energy",
}


def _cohort_records() -> list[NormalizedRecord]:
    return [
        _pin_record(100, date(2024, 1, 5), entity_id="CIK0000000001"),
        _pin_record(200, date(2024, 1, 10), entity_id="CIK0000000001"),
        _pin_record(300, date(2024, 2, 1), entity_id="CIK0000000002"),
        _pin_record(400, date(2024, 1, 5), entity_id="CIK0000000003"),
    ]


def test_sector_aggregation_is_byte_deterministic_across_calls_and_orders():
    records = _cohort_records()
    kwargs = {"as_of": datetime(2024, 3, 1, tzinfo=UTC), "sector_of": _SECTOR_OF, "field": "us-gaap:Assets"}

    first = sector_mean_asof_bytes(records, **kwargs)
    second = sector_mean_asof_bytes(records, **kwargs)
    assert first == second  # byte-identical across two independent calls

    for order in (list(reversed(records)), records[2:] + records[:2]):
        assert sector_mean_asof_bytes(order, **kwargs) == first  # input order cannot matter

    payload = json.loads(first)
    assert payload["sectors"]["INFORMATION TECHNOLOGY"] == {
        "count": 2,
        "mean": (200 + 300) / 2,
        "entity_ids": ["CIK0000000001", "CIK0000000002"],
    }
    assert payload["sectors"]["ENERGY"] == {
        "count": 1,
        "mean": 400.0,
        "entity_ids": ["CIK0000000003"],
    }


def test_sector_aggregation_is_survivorship_aware_at_each_asof():
    records = _cohort_records()

    # Before anything is available the as-of filer set is empty.
    empty = json.loads(
        sector_mean_asof_bytes(records, as_of=datetime(2024, 1, 1, tzinfo=UTC), sector_of=_SECTOR_OF, field="us-gaap:Assets")
    )
    assert empty["sectors"] == {}

    # Jan 7 cohort: A and C are available, B is not, and A is on its first
    # vintage.  The cohort derives purely from availability at that date.
    jan7 = json.loads(
        sector_mean_asof_bytes(records, as_of=datetime(2024, 1, 7, tzinfo=UTC), sector_of=_SECTOR_OF, field="us-gaap:Assets")
    )
    assert set(jan7["sectors"]) == {"INFORMATION TECHNOLOGY", "ENERGY"}
    assert jan7["sectors"]["INFORMATION TECHNOLOGY"]["mean"] == 100.0
    assert jan7["sectors"]["ENERGY"]["mean"] == 400.0

    # Jan 20: A revised to 200; B still unavailable.
    jan20 = json.loads(
        sector_mean_asof_bytes(records, as_of=datetime(2024, 1, 20, tzinfo=UTC), sector_of=_SECTOR_OF, field="us-gaap:Assets")
    )
    assert jan20["sectors"]["INFORMATION TECHNOLOGY"]["mean"] == 200.0

    # Mar 1: B joins the cohort exactly when its availability allows.
    mar1 = json.loads(
        sector_mean_asof_bytes(records, as_of=datetime(2024, 3, 1, tzinfo=UTC), sector_of=_SECTOR_OF, field="us-gaap:Assets")
    )
    assert mar1["sectors"]["INFORMATION TECHNOLOGY"]["entity_ids"] == ["CIK0000000001", "CIK0000000002"]
    assert mar1["sectors"]["INFORMATION TECHNOLOGY"]["mean"] == 250.0


def test_sector_aggregation_reports_unmapped_filers_explicitly():
    records = _cohort_records()
    payload = json.loads(
        sector_mean_asof_bytes(
            records,
            as_of=datetime(2024, 3, 1, tzinfo=UTC),
            sector_of={"CIK0000000001": "Information Technology"},
            field="us-gaap:Assets",
        )
    )
    assert payload["sectors"] == {
        "INFORMATION TECHNOLOGY": {
            "count": 1,
            "mean": 200.0,
            "entity_ids": ["CIK0000000001"],
        }
    }
    assert payload["unmapped_entity_ids"] == ["CIK0000000002", "CIK0000000003"]


def test_sector_aggregation_over_real_sec_fixture_rows():
    adapter = SecAdapter()
    facts = _sec_company_facts(adapter)
    assets = [r for r in facts.records if r.field == "us-gaap:Assets"]
    sector_of = {"CIK0000000001": "Information Technology"}

    before = sector_mean_asof_bytes(
        assets, as_of=datetime(2024, 3, 1, tzinfo=UTC), sector_of=sector_of, field="us-gaap:Assets"
    )
    after = sector_mean_asof_bytes(
        assets, as_of=datetime(2024, 5, 1, tzinfo=UTC), sector_of=sector_of, field="us-gaap:Assets"
    )
    assert json.loads(before)["sectors"]["INFORMATION TECHNOLOGY"]["mean"] == 5000.0
    assert json.loads(after)["sectors"]["INFORMATION TECHNOLOGY"]["mean"] == 5100.0
