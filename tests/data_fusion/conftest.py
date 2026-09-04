from datetime import datetime, timezone

import pytest

from research.data_fusion.models import NormalizedRecord


UTC = timezone.utc


def dt(day: int, hour: int = 0) -> datetime:
    return datetime(2024, 1, day, hour, tzinfo=UTC)


@pytest.fixture
def record_factory():
    def make(**overrides):
        values = dict(
            source_id="SEC_EDGAR",
            dataset_id="company_facts",
            entity_id="CIK0000000001",
            field="revenue",
            value=100,
            unit="USD",
            event_time_utc=dt(1),
            available_time_utc=dt(3),
            effective_time_utc=dt(3),
            vintage_time_utc=dt(3),
            retrieved_time_utc=dt(10),
            raw_path="sec/companyfacts/one.json",
            raw_sha256="a" * 64,
            license_id="sec-public-v1",
            entitlement_id="public",
            normalizer_version="1",
        )
        values.update(overrides)
        return NormalizedRecord(**values)

    return make
