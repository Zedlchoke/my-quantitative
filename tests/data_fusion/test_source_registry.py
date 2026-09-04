from research.data_fusion.authority import AuthorityStatus
from research.data_fusion.source_registry import SOURCES, by_id


def test_source_ids_are_unique_and_not_implicitly_authorized():
    ids = [source.source_id for source in SOURCES]
    assert len(ids) == len(set(ids))
    assert all(source.status is not AuthorityStatus.AUTHORIZED_INTERNAL_RESEARCH for source in SOURCES)


def test_finra_forbidden_inferences_are_explicit():
    source = by_id("FINRA_SHORT")
    assert "borrow_fee" in source.forbidden_inference
    assert "short_sale_volume_equals_short_interest" in source.forbidden_inference


def test_fred_key_gate_is_explicit():
    assert by_id("FRED_ALFRED").account_or_key_required
