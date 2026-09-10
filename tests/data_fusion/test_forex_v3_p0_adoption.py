"""FOREX-FREE-V3 P0 adoption regressions (PLAN_forex_v3.md section 6, P0).

Pins the three macro-adoption invariants required of the A2 fusion lane,
against the adopted Data Fusion V1 core and A3-macro adapters only:

a) policy-rate rows map onto ``NormalizedRecord`` with TRUE
   effective/availability semantics: ``effective_time_utc`` (when a rate
   starts to bind) is a distinct field from ``available_time_utc`` (when the
   value was first knowable), proven against the offline BIS WS_CBPOL and
   ECB SDMX fixtures;
b) PIT no-lookahead pin: a decision/query at time T can never return a row
   whose ``available_time_utc > T`` (and, by default, never one whose
   ``effective_time_utc > T``), via the adopted ``pit.select_asof`` /
   ``pit.asof_join`` primitives — this test must FAIL if those semantics
   regress;
c) rate-change events surface as dated vintages: a policy-rate change
   produces a NEW vintage row carrying its own effective and availability
   stamps, append-only via ``pit.VintageSeries``.

Hand-computed expectations are read straight from the fixture bytes:
BIS ``bis_cbpol.json``: observations {"0": [4.0, 0], "1": [4.25, 0]} over
TIME_PERIOD ["2024-03-20", "2024-05-01"] for series US.P -> the US policy
rate is 4.0 effective 2024-03-20 and 4.25 effective 2024-05-01 (a 25bp
change).  ECB ``ecb_sdmx_exr.json``: observations {"0": [1.0951, 0],
"1": [1.0969, 0]} over TIME_PERIOD ["2024-01-02", "2024-01-03"] for
D.USD.EUR.SP00.A -> the USD/EUR reference rate is 1.0951 on 2024-01-02.

Offline only: fixture bytes, no network, no wall clock, no new data files.
"""

from datetime import date, datetime, timezone

import pytest

from research.data_fusion.adapters.base import AdapterError, date_only_evidence
from research.data_fusion.adapters.bis import BisAdapter
from research.data_fusion.adapters.ecb import EcbAdapter
from research.data_fusion.models import NormalizedRecord
from research.data_fusion.pit import AmbiguousVintageError, VintageSeries, asof_join, select_asof

from .adapters.conftest import fixture_bytes, response_for

UTC = timezone.utc

BIS_FIXTURE = "bis_cbpol.json"
ECB_FIXTURE = "ecb_sdmx_exr.json"


def bis_response():
    request = BisAdapter().build_policy_rate_request("US.P")
    return response_for(
        request, fixture_bytes(BIS_FIXTURE), content_type="application/vnd.sdmx.data+json"
    )


def bis_parse(evidence_day: date):
    return BisAdapter().parse_policy_rates(
        bis_response(), release_evidence=date_only_evidence("BIS CBPOL effective-date evidence", evidence_day)
    )


def bis_record_by_effective(evidence_day: date, effective_day: date) -> NormalizedRecord:
    matches = [
        record
        for record in bis_parse(evidence_day).records
        if record.effective_time_utc == datetime(effective_day.year, effective_day.month, effective_day.day, tzinfo=UTC)
    ]
    assert len(matches) == 1
    return matches[0]


def ecb_parse(evidence_day: date):
    request = EcbAdapter().build_series_request("EXR", "D.USD.EUR.SP00.A")
    response = response_for(
        request, fixture_bytes(ECB_FIXTURE), content_type="application/vnd.sdmx.data+json"
    )
    return EcbAdapter().parse_series(
        response,
        dataflow="EXR",
        release_evidence=date_only_evidence("ECB reference-rate publication calendar", evidence_day),
        unit="USD_PER_EUR",
    )


# ---------------------------------------------------------------------------
# (a) schema mapping with true effective/availability semantics
# ---------------------------------------------------------------------------


def test_bis_policy_rate_rows_map_with_true_effective_availability_semantics():
    output = bis_parse(date(2024, 5, 1))
    assert len(output.records) == 2

    march = bis_record_by_effective(date(2024, 5, 1), date(2024, 3, 20))
    may = bis_record_by_effective(date(2024, 5, 1), date(2024, 5, 1))

    # Hand-computed from fixture bytes: observations {"0": [4.0, 0], "1": [4.25, 0]}
    # over TIME_PERIOD ["2024-03-20", "2024-05-01"].
    assert march.value == 4.0
    assert may.value == 4.25

    # Schema mapping: these are real NormalizedRecords of the policy-rate key.
    for record in (march, may):
        assert isinstance(record, NormalizedRecord)
        assert record.logical_key == ("policy_rates", "BIS:WS_CBPOL:US.P", "policy_rate")
        assert record.source_id == "BIS_CBPOL"
        assert record.unit == "PERCENT_PER_ANNUM"

    # Effective semantics: a CBPOL date is the date the rate starts to bind,
    # so effective_time_utc is midnight of the TIME_PERIOD string.
    assert march.event_time_utc == datetime(2024, 3, 20, tzinfo=UTC)
    assert march.effective_time_utc == datetime(2024, 3, 20, tzinfo=UTC)
    assert may.effective_time_utc == datetime(2024, 5, 1, tzinfo=UTC)

    # Availability semantics: date-only release evidence yields the
    # conservative end-of-UTC-day upper bound of the evidence day
    # (2024-05-01T23:59:59Z), never the effective date itself.
    assert march.available_time_utc == datetime(2024, 5, 1, 23, 59, 59, tzinfo=UTC)
    assert may.available_time_utc == datetime(2024, 5, 1, 23, 59, 59, tzinfo=UTC)
    for record in (march, may):
        assert record.available_time_utc != record.effective_time_utc
        assert record.available_time_utc > record.effective_time_utc

    # The distinction is observable: the 2024-05-01 rate is effective at
    # midnight but is NOT eligible on its effective date because it only
    # becomes available at end of that UTC day.
    assert not may.eligible_at(datetime(2024, 5, 1, 0, 0, 0, tzinfo=UTC))
    assert not may.eligible_at(datetime(2024, 5, 1, 12, 0, 0, tzinfo=UTC))
    assert may.eligible_at(datetime(2024, 5, 1, 23, 59, 59, tzinfo=UTC))

    # Provenance ties to the fixture bytes themselves.
    import hashlib

    fixture_sha = hashlib.sha256(fixture_bytes(BIS_FIXTURE)).hexdigest()
    for record in (march, may):
        assert record.raw_sha256 == fixture_sha


def test_bis_availability_is_never_invented():
    # Without owner evidence the adapter refuses rows outright: availability
    # cannot be inferred from the effective date or from header.prepared.
    with pytest.raises(AdapterError) as exc:
        BisAdapter().parse_policy_rates(bis_response(), release_evidence=None)
    assert exc.value.code == "MISSING_AVAILABLE_TIME_EVIDENCE"


def test_ecb_series_rows_map_with_true_effective_availability_semantics():
    output = ecb_parse(date(2024, 1, 3))
    assert len(output.records) == 2
    first = output.records[0]

    # Hand-computed from fixture bytes: observations {"0": [1.0951, 0], ...}
    # over TIME_PERIOD ["2024-01-02", ...].
    assert first.value == 1.0951
    assert first.logical_key == ("sdmx_series", "ECB:EXR:D.USD.EUR.SP00.A", "observation")
    assert first.effective_time_utc == datetime(2024, 1, 2, tzinfo=UTC)
    assert first.available_time_utc == datetime(2024, 1, 3, 23, 59, 59, tzinfo=UTC)

    # Effective (fixing date) and availability (end of evidence day) are
    # distinct, and neither collapses into the SDMX message metadata stamp
    # header.prepared = 2024-01-03T15:10:00Z.
    assert first.effective_time_utc != first.available_time_utc
    prepared = datetime(2024, 1, 3, 15, 10, 0, tzinfo=UTC)
    assert first.available_time_utc != prepared
    assert first.available_time_utc > prepared


# ---------------------------------------------------------------------------
# (b) PIT no-lookahead pin: decision at T never reads available_time_utc > T
# ---------------------------------------------------------------------------


def _bis_vintage_pair():
    """As-known-then rows from two evidence-dated retrievals of the fixture.

    Pass 1 (evidence day 2024-03-20) yields the then-current rate 4.0
    effective 2024-03-20; pass 2 (evidence day 2024-05-01) yields the
    rate-change vintage 4.25 effective 2024-05-01.  Same-rank conflicting
    rows are refused by design (AmbiguousVintageError), so a PIT store keeps
    exactly these as-known-then revisions.
    """
    rate_400 = bis_record_by_effective(date(2024, 3, 20), date(2024, 3, 20))
    rate_425 = bis_record_by_effective(date(2024, 5, 1), date(2024, 5, 1))
    return rate_400, rate_425


def test_pit_no_lookahead_decision_at_t_never_reads_unavailable_rows():
    rate_400, rate_425 = _bis_vintage_pair()
    records = [rate_400, rate_425]

    decisions = [
        datetime(2024, 1, 3, 23, 59, 58, tzinfo=UTC),
        datetime(2024, 3, 20, 0, 0, 0, tzinfo=UTC),
        datetime(2024, 3, 20, 23, 59, 58, tzinfo=UTC),
        datetime(2024, 3, 20, 23, 59, 59, tzinfo=UTC),
        datetime(2024, 4, 15, tzinfo=UTC),
        datetime(2024, 5, 1, 0, 0, 0, tzinfo=UTC),
        datetime(2024, 5, 1, 12, 0, 0, tzinfo=UTC),
        datetime(2024, 5, 1, 23, 59, 58, tzinfo=UTC),
        datetime(2024, 5, 1, 23, 59, 59, tzinfo=UTC),
        datetime(2024, 5, 2, tzinfo=UTC),
        datetime(2025, 1, 1, tzinfo=UTC),
    ]

    # Core invariant: whatever comes back at T was already available at T
    # (and, by the default, already effective at T).  If the availability
    # gate or the effective gate regresses, one of the pinned outcomes
    # below or this loop fails.
    for decision in decisions:
        selected = select_asof(records, decision)
        if selected is not None:
            assert selected.available_time_utc <= decision, (
                f"lookahead: row available {selected.available_time_utc} returned for T={decision}"
            )
            assert selected.effective_time_utc <= decision, (
                f"future-effective row returned for T={decision}"
            )
        # The availability gate holds even with effective checking disabled.
        relaxed = select_asof(records, decision, require_effective=False)
        if relaxed is not None:
            assert relaxed.available_time_utc <= decision, (
                f"lookahead with require_effective=False at T={decision}"
            )

    # Pinned hand-computed outcomes across the rate-change boundary.
    assert select_asof(records, datetime(2024, 3, 20, 23, 59, 58, tzinfo=UTC)) is None
    assert select_asof(records, datetime(2024, 3, 20, 23, 59, 59, tzinfo=UTC)).value == 4.0
    # The hike is effective at 2024-05-01T00:00Z but its availability stamp
    # is 2024-05-01T23:59:59Z: a decision on the effective day must still
    # see the OLD rate.  If effective-time were (wrongly) treated as
    # availability, these would return 4.25 and the pin would fail.
    assert select_asof(records, datetime(2024, 5, 1, 0, 0, 0, tzinfo=UTC)).value == 4.0
    assert select_asof(records, datetime(2024, 5, 1, 12, 0, 0, tzinfo=UTC)).value == 4.0
    assert select_asof(records, datetime(2024, 5, 1, 23, 59, 59, tzinfo=UTC)).value == 4.25
    assert select_asof(records, datetime(2024, 5, 2, tzinfo=UTC)).value == 4.25


def test_pit_no_lookahead_asof_join_over_bis_and_ecb():
    rate_400, rate_425 = _bis_vintage_pair()
    ecb_row = ecb_parse(date(2024, 1, 3)).records[0]  # value 1.0951, effective 2024-01-02
    records = [rate_400, rate_425, ecb_row]

    decisions = [
        datetime(2024, 1, 3, 23, 59, 58, tzinfo=UTC),
        datetime(2024, 1, 3, 23, 59, 59, tzinfo=UTC),
        datetime(2024, 3, 20, 23, 59, 58, tzinfo=UTC),
        datetime(2024, 3, 20, 23, 59, 59, tzinfo=UTC),
        datetime(2024, 5, 1, 12, 0, 0, tzinfo=UTC),
        datetime(2024, 5, 1, 23, 59, 59, tzinfo=UTC),
        datetime(2024, 5, 2, tzinfo=UTC),
    ]
    joined = asof_join(records, decisions)

    bis_key = ("policy_rates", "BIS:WS_CBPOL:US.P", "policy_rate")
    ecb_key = ("sdmx_series", "ECB:EXR:D.USD.EUR.SP00.A", "observation")

    for decision, row in joined.items():
        for key, selected in row.items():
            assert selected.available_time_utc <= decision, (
                f"lookahead in join: {key} available {selected.available_time_utc} at T={decision}"
            )
            assert selected.effective_time_utc <= decision

    # Hand-pinned join boundaries.
    assert joined[datetime(2024, 1, 3, 23, 59, 58, tzinfo=UTC)] == {}
    assert ecb_key not in joined[datetime(2024, 1, 3, 23, 59, 58, tzinfo=UTC)]
    assert joined[datetime(2024, 1, 3, 23, 59, 59, tzinfo=UTC)][ecb_key].value == 1.0951
    assert bis_key not in joined[datetime(2024, 3, 20, 23, 59, 58, tzinfo=UTC)]
    assert joined[datetime(2024, 3, 20, 23, 59, 59, tzinfo=UTC)][bis_key].value == 4.0
    # Effective-day decision still reads the old rate (no lookahead).
    assert joined[datetime(2024, 5, 1, 12, 0, 0, tzinfo=UTC)][bis_key].value == 4.0
    assert joined[datetime(2024, 5, 2, tzinfo=UTC)][bis_key].value == 4.25


# ---------------------------------------------------------------------------
# (c) rate-change events surface as dated vintages
# ---------------------------------------------------------------------------


def test_rate_change_surfaces_as_new_dated_vintage_row():
    rate_400, rate_425 = _bis_vintage_pair()

    # Hand-computed stamps for the two vintages of the SAME logical key.
    assert rate_400.logical_key == rate_425.logical_key
    assert rate_400.value == 4.0
    assert rate_425.value == 4.25
    assert rate_400.effective_time_utc == datetime(2024, 3, 20, tzinfo=UTC)
    assert rate_400.available_time_utc == datetime(2024, 3, 20, 23, 59, 59, tzinfo=UTC)
    assert rate_425.effective_time_utc == datetime(2024, 5, 1, tzinfo=UTC)
    assert rate_425.available_time_utc == datetime(2024, 5, 1, 23, 59, 59, tzinfo=UTC)
    # Each vintage carries its own dated stamps; the vintage stamp comes
    # from the owner evidence and equals the availability stamp.
    assert rate_400.vintage_time_utc == datetime(2024, 3, 20, 23, 59, 59, tzinfo=UTC)
    assert rate_425.vintage_time_utc == datetime(2024, 5, 1, 23, 59, 59, tzinfo=UTC)
    assert rate_425.available_time_utc != rate_400.available_time_utc

    # The rate change appends a NEW vintage row; earlier revisions are
    # never mutated.
    series = VintageSeries.started_by(rate_400).append(rate_425)
    assert len(series.records) == 2
    assert series.records[0].canonical_bytes() == rate_400.canonical_bytes()
    assert series.records[1].canonical_bytes() == rate_425.canonical_bytes()

    # As-of reads walk the vintages by their dated stamps.
    assert series.select(datetime(2024, 4, 15, tzinfo=UTC)).value == 4.0
    assert series.select(datetime(2024, 5, 1, 12, 0, 0, tzinfo=UTC)).value == 4.0
    assert series.select(datetime(2024, 5, 2, tzinfo=UTC)).value == 4.25

    # Re-appending byte-identical content is idempotent.
    assert series.append(rate_425) is series

    # A conflicting row landing on an already-filled rank (a restated
    # 4.0-effective row from the later retrieval shares rank with the
    # 4.25 vintage) fails closed instead of overwriting the vintage.
    restated = bis_record_by_effective(date(2024, 5, 1), date(2024, 3, 20))
    assert restated.value == 4.0
    with pytest.raises(AmbiguousVintageError):
        series.append(restated)
    assert len(series.records) == 2
