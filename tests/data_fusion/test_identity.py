from datetime import datetime, timezone

import pytest

from research.data_fusion.identity import IdentityConflict, TemporalAlias, resolve_identity


UTC = timezone.utc


def dt(year):
    return datetime(year, 1, 1, tzinfo=UTC)


def alias(**overrides):
    values = dict(
        namespace="ticker",
        alias="OLD",
        canonical_id="SECURITY-1",
        valid_from_utc=dt(2018),
        valid_to_utc=dt(2022),
        available_time_utc=dt(2018),
        source_id="SEC_EDGAR",
        raw_sha256="a" * 64,
    )
    values.update(overrides)
    return TemporalAlias(**values)


def test_current_alias_is_not_projected_backward():
    current = alias(alias="NEW", valid_from_utc=dt(2022), valid_to_utc=None, available_time_utc=dt(2022))
    assert resolve_identity([current], "ticker", "NEW", dt(2020)) is None
    assert resolve_identity([current], "ticker", "NEW", dt(2023)) == "SECURITY-1"


def test_historical_alias_expires():
    old = alias()
    assert resolve_identity([old], "ticker", "OLD", dt(2020)) == "SECURITY-1"
    assert resolve_identity([old], "ticker", "OLD", dt(2023)) is None


def test_overlapping_conflicting_aliases_fail_closed():
    rows = [alias(), alias(canonical_id="SECURITY-2", raw_sha256="b" * 64)]
    with pytest.raises(IdentityConflict) as exc:
        resolve_identity(rows, "ticker", "OLD", dt(2020))
    assert exc.value.code == "IDENTITY_CONFLICT_MULTIPLE_CANONICAL"
