"""Offline tests for the source-evidence registry (A2)."""

import json

from research.stocks_free_v1 import source_evidence as se


def test_registry_verdicts_are_from_closed_enum():
    for sc in se.SOURCE_CANDIDATES:
        assert sc.verdict in se.VERDICTS, sc.source_id


def test_registry_integrity_validator_passes():
    assert se.validate_registry() == []


def test_every_source_has_captured_terms_provenance():
    # PLAN 4.1 items 1-3: identity, official URLs, terms URL + access date.
    for sc in se.SOURCE_CANDIDATES:
        assert sc.identity
        assert sc.official_urls and all(u.startswith("https://") for u in sc.official_urls)
        assert sc.terms_url
        assert sc.terms_accessed_utc  # date string, e.g. 2026-09-03


def test_candidates_must_quote_captured_terms():
    for sc in se.SOURCE_CANDIDATES:
        if sc.verdict == se.VERDICT_CANDIDATE:
            assert sc.terms_excerpt, (
                f"{sc.source_id}: CANDIDATE verdict requires a captured "
                "terms excerpt (no invented license conclusions)"
            )


def test_account_required_exclusions_are_marked():
    ids = {sc.source_id: sc for sc in se.SOURCE_CANDIDATES}
    for sid in ("massive_polygon_free_tier", "nasdaq_data_link_free"):
        sc = ids[sid]
        assert sc.verdict == se.VERDICT_EXCLUDED_ACCOUNT_REQUIRED
        assert sc.account_required is True
        assert any("pricing" in u or "terms" in u for u in sc.official_urls) or sc.terms_url


def test_stooq_is_license_unproven_with_blocker_evidence():
    stooq = {sc.source_id: sc for sc in se.SOURCE_CANDIDATES}["stooq_daily_csv"]
    assert stooq.verdict == se.VERDICT_EXCLUDED_LICENSE_UNPROVEN
    assert stooq.access_blocker  # recorded challenge evidence, not silence
    assert "proof-of-work" in stooq.access_blocker.lower() or "challenge" in (
        stooq.access_blocker.lower()
    )


def test_ssga_access_proven_but_license_unproven():
    ssga = {sc.source_id: sc for sc in se.SOURCE_CANDIDATES}["ssga_spdr_official"]
    # data endpoints downloaded without account (access evidence digests kept)
    assert any("navhist" in label for label, _ in ssga.evidence_digests)
    # but terms text could not be captured in-session -> license unproven
    assert ssga.verdict == se.VERDICT_EXCLUDED_LICENSE_UNPROVEN
    assert ssga.account_required is False
    assert "SPA" in ssga.access_blocker or "terms text not capturable" in ssga.access_blocker


def test_fred_is_conditional_candidate_with_captured_terms():
    fred = {sc.source_id: sc for sc in se.SOURCE_CANDIDATES}["fred_fredgraph_csv"]
    assert fred.verdict == se.VERDICT_CANDIDATE
    assert "non-commercial" in fred.terms_excerpt.lower()
    assert "robots" in fred.terms_excerpt.lower()  # automation ambiguity recorded
    assert any("fred_terms_of_use" in label for label, _ in fred.evidence_digests)


def test_yahoo_is_diagnostic_only():
    yahoo = {sc.source_id: sc for sc in se.SOURCE_CANDIDATES}["yahoo_finance_chart"]
    assert yahoo.verdict == se.VERDICT_DIAGNOSTIC_ONLY


def test_registry_json_round_trip(tmp_path):
    out = tmp_path / "source_evidence.json"
    doc = se.write_registry_json(out)
    assert out.exists()
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["schema"] == doc["schema"]
    assert loaded["integrity_problems"] == []
    by_id = {s["source_id"]: s for s in loaded["sources"]}
    assert set(by_id) == {
        "stooq_daily_csv",
        "ssga_spdr_official",
        "fred_fredgraph_csv",
        "yahoo_finance_chart",
        "massive_polygon_free_tier",
        "nasdaq_data_link_free",
    }
    # frozen verdicts per mandate
    assert by_id["stooq_daily_csv"]["verdict"] == "EXCLUDED_LICENSE_UNPROVEN"
    assert by_id["yahoo_finance_chart"]["verdict"] == "DIAGNOSTIC_ONLY"
    assert by_id["massive_polygon_free_tier"]["verdict"] == "EXCLUDED_ACCOUNT_REQUIRED"


def test_terms_excerpts_are_short():
    for sc in se.SOURCE_CANDIDATES:
        # short excerpts only (no substantial copyrighted text in Git)
        assert len(sc.terms_excerpt) <= 2000, sc.source_id


def test_validator_flags_candidate_without_excerpt():
    bad = se.SourceCandidate(
        source_id="x",
        identity="i",
        role="r",
        official_urls=("https://example.com/",),
        terms_url="https://example.com/terms",
        terms_accessed_utc="2026-09-03",
        terms_excerpt="",
        account_required=False,
        verdict=se.VERDICT_CANDIDATE,
        rationale="",
    )
    problems = se.validate_registry((bad,))
    assert any("CANDIDATE without captured terms excerpt" in p for p in problems)
