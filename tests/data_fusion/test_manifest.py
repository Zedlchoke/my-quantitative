import pytest

from research.data_fusion.manifest import RawFileEvidence, SourceManifest


def raw(path="raw/a.json", digest="a" * 64):
    return RawFileEvidence(path, digest, 10)


def manifest(files):
    return SourceManifest(
        source_id="SEC_EDGAR",
        dataset_id="company_facts",
        schema_version="1",
        normalizer_version="1",
        authority_status="DOCUMENTED_CANDIDATE",
        license_id="sec-public-v1",
        entitlement_id="public",
        files=tuple(files),
    )


def test_manifest_hash_is_order_independent():
    a, b = raw("raw/a.json", "a" * 64), raw("raw/b.json", "b" * 64)
    assert manifest([a, b]).digest() == manifest([b, a]).digest()


def test_duplicate_raw_path_is_refused():
    with pytest.raises(ValueError, match="duplicate"):
        manifest([raw(), raw(digest="b" * 64)])


def test_manifest_path_traversal_is_refused():
    with pytest.raises(ValueError, match="traversal"):
        raw("../escape")


def test_undocumented_authority_status_is_refused():
    with pytest.raises(ValueError, match="authority status"):
        manifest([raw()]).__class__(
            source_id="SEC_EDGAR",
            dataset_id="company_facts",
            schema_version="1",
            normalizer_version="1",
            authority_status="AUTHORIZED_BECAUSE_HTTP_200",
            license_id="sec-public-v1",
            entitlement_id="public",
            files=(raw(),),
        )


def test_all_documented_authority_statuses_are_accepted():
    from research.data_fusion.authority import AuthorityStatus

    for status in AuthorityStatus:
        built = SourceManifest(
            source_id="SEC_EDGAR",
            dataset_id="company_facts",
            schema_version="1",
            normalizer_version="1",
            authority_status=status.value,
            license_id="sec-public-v1",
            entitlement_id="public",
            files=(raw(),),
        )
        assert built.authority_status == status.value
