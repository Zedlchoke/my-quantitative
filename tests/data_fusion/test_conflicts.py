import pytest

from research.data_fusion.conflicts import ConflictError, SourcePolicy, SourceRole, resolve_primary


def test_cross_check_never_patches_primary_gap(record_factory):
    cross = record_factory(source_id="TWELVE_DATA")
    policy = SourcePolicy(
        dataset_id="company_facts",
        field="revenue",
        roles={"SEC_EDGAR": SourceRole.PRIMARY, "TWELVE_DATA": SourceRole.CROSS_CHECK},
    )
    primary, checks = resolve_primary([cross], policy)
    assert primary == []
    assert checks == {"TWELVE_DATA": [cross]}


def test_exactly_one_primary_is_required():
    with pytest.raises(ConflictError) as exc:
        SourcePolicy("prices", "close", {"A": SourceRole.CROSS_CHECK}).primary_source()
    assert exc.value.code == "NO_PRIMARY_SOURCE_DECLARED"
    assert "exactly one" in str(exc.value)


def test_two_primaries_are_refused_with_stable_code():
    policy = SourcePolicy(
        "prices", "close", {"A": SourceRole.PRIMARY, "B": SourceRole.PRIMARY}
    )
    with pytest.raises(ConflictError) as exc:
        policy.primary_source()
    assert exc.value.code == "MULTIPLE_PRIMARY_SOURCES"
