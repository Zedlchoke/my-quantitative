from datetime import datetime

import pytest


def test_record_is_not_visible_before_available_time(record_factory):
    record = record_factory()
    assert not record.eligible_at(datetime.fromisoformat("2024-01-02T00:00:00+00:00"))
    assert record.eligible_at(datetime.fromisoformat("2024-01-03T00:00:00+00:00"))


def test_naive_time_is_refused(record_factory):
    with pytest.raises(ValueError, match="timezone-aware"):
        record_factory(available_time_utc=datetime(2024, 1, 3))


def test_non_utc_offset_is_refused(record_factory):
    with pytest.raises(ValueError, match="must be UTC"):
        record_factory(
            available_time_utc=datetime.fromisoformat("2024-01-03T07:00:00+07:00")
        )


@pytest.mark.parametrize("path", ["/tmp/raw.json", "../raw.json", ""])
def test_unsafe_raw_path_is_refused(record_factory, path):
    with pytest.raises(ValueError, match="relative POSIX"):
        record_factory(raw_path=path)


def test_non_finite_value_is_refused(record_factory):
    with pytest.raises(ValueError, match="finite"):
        record_factory(value=float("nan"))


def test_canonical_bytes_are_stable(record_factory):
    assert record_factory().canonical_bytes() == record_factory().canonical_bytes()
