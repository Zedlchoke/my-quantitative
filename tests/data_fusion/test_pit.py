from datetime import datetime, timezone

import pytest

from research.data_fusion.pit import (
    AmbiguousVintageError,
    VintageSeries,
    asof_join,
    select_asof,
)


UTC = timezone.utc


def dt(day):
    return datetime(2024, 1, day, tzinfo=UTC)


def test_later_revision_does_not_leak_backward(record_factory):
    original = record_factory(value=100, available_time_utc=dt(3), vintage_time_utc=dt(3))
    revision = record_factory(
        value=120,
        available_time_utc=dt(8),
        vintage_time_utc=dt(8),
        raw_sha256="b" * 64,
    )
    assert select_asof([original, revision], dt(5)).value == 100
    assert select_asof([original, revision], dt(9)).value == 120


def test_effective_date_is_enforced(record_factory):
    announced = record_factory(available_time_utc=dt(3), effective_time_utc=dt(7))
    assert select_asof([announced], dt(5)) is None
    assert select_asof([announced], dt(7)) is announced
    assert select_asof([announced], dt(5), require_effective=False) is announced


def test_asof_join_handles_multiple_fields(record_factory):
    revenue = record_factory()
    assets = record_factory(field="assets", value=200, raw_sha256="c" * 64)
    joined = asof_join([revenue, assets], [dt(4)])
    assert set(joined[dt(4)]) == {
        ("company_facts", "CIK0000000001", "revenue"),
        ("company_facts", "CIK0000000001", "assets"),
    }


def test_mixed_logical_keys_are_refused(record_factory):
    with pytest.raises(ValueError, match="one logical key"):
        select_asof([record_factory(), record_factory(field="assets")], dt(5))


def test_same_rank_conflict_is_refused(record_factory):
    one = record_factory(value=100)
    two = record_factory(value=101, raw_sha256="b" * 64)
    with pytest.raises(AmbiguousVintageError) as exc:
        select_asof([one, two], dt(5))
    assert exc.value.code == "AMBIGUOUS_VINTAGE_RANK"


def test_vintage_series_is_append_only(record_factory):
    original = record_factory(value=100, available_time_utc=dt(3), vintage_time_utc=dt(3))
    revision = record_factory(value=120, available_time_utc=dt(8), vintage_time_utc=dt(8))
    series = VintageSeries.started_by(original).append(revision)

    assert len(series.records) == 2
    assert series.select(dt(5)).value == 100
    assert series.select(dt(9)).value == 120


def test_vintage_series_never_overwrites_a_filled_rank(record_factory):
    original = record_factory(value=100)
    restated = record_factory(value=999, raw_sha256="b" * 64)
    series = VintageSeries.started_by(original)
    with pytest.raises(AmbiguousVintageError) as exc:
        series.append(restated)
    assert exc.value.code == "AMBIGUOUS_VINTAGE_RANK"
    assert series.records == (original,)


def test_vintage_series_reappend_of_identical_bytes_is_idempotent(record_factory):
    record = record_factory()
    series = VintageSeries.started_by(record).append(record_factory())
    assert series.records == (record,)


def test_vintage_series_refuses_foreign_logical_key(record_factory):
    series = VintageSeries.started_by(record_factory())
    with pytest.raises(ValueError, match="logical key"):
        series.append(record_factory(field="assets", raw_sha256="b" * 64))


def test_df_issue2_later_retrieval_never_silently_resolves_equal_rank(record_factory):
    """DF-ISSUE-2 characterization (MDP-V1 versioned closure).

    Two records with EQUAL available_time and EQUAL vintage but DIFFERING
    content must fail closed even when one was retrieved LATER — the later
    retrieval timestamp is never an authoritative revision key at the pin or
    under MDP-V1.  Verified present at the audited pin c6a0576; this test
    pins the contract so it cannot regress silently.
    """
    late_retrieval = datetime(2024, 2, 8, tzinfo=UTC)
    early_pull = record_factory(value=100, retrieved_time_utc=dt(10))
    late_pull = record_factory(
        value=101, raw_sha256="b" * 64, retrieved_time_utc=late_retrieval
    )
    with pytest.raises(AmbiguousVintageError) as exc_late_first:
        select_asof([late_pull, early_pull], dt(5))
    assert exc_late_first.value.code == "AMBIGUOUS_VINTAGE_RANK"
    with pytest.raises(AmbiguousVintageError) as exc_early_first:
        select_asof([early_pull, late_pull], dt(5))
    assert exc_early_first.value.code == "AMBIGUOUS_VINTAGE_RANK"


def test_df_issue2_append_refuses_later_pull_with_different_content(record_factory):
    """VintageSeries.append must also refuse equal-vintage differing content
    regardless of retrieval time (DF-ISSUE-2: both entry paths closed)."""
    early_pull = record_factory(value=100, retrieved_time_utc=dt(10))
    late_pull = record_factory(
        value=101, raw_sha256="b" * 64, retrieved_time_utc=datetime(2024, 2, 8, tzinfo=UTC)
    )
    series = VintageSeries.started_by(early_pull)
    with pytest.raises(AmbiguousVintageError):
        series.append(late_pull)
