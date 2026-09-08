from research.data_fusion.authority import (
    AuthorityEvidence,
    AuthorityStatus,
    evaluate_authority,
)


def evidence(**overrides):
    values = dict(
        source_id="SEC_EDGAR",
        terms_captured=True,
        internal_research_allowed=True,
        local_storage_allowed=True,
        redistribution_allowed=False,
        entitlement_active=True,
        deterministic_retrieval=True,
        historical_available_time=True,
        raw_hashes_recorded=True,
        account_or_key_required=False,
        account_or_key_authorized=False,
    )
    values.update(overrides)
    return AuthorityEvidence(**values)


def test_complete_evidence_authorizes_internal_research():
    decision = evaluate_authority(evidence())
    assert decision.status is AuthorityStatus.AUTHORIZED_INTERNAL_RESEARCH
    assert decision.usable_for_scored_research


def test_free_key_is_still_an_authority_gate():
    decision = evaluate_authority(
        evidence(account_or_key_required=True, account_or_key_authorized=False)
    )
    assert decision.status is AuthorityStatus.CANDIDATE_NOT_AUTHORIZED
    assert "ACCOUNT_OR_KEY_NOT_AUTHORIZED" in decision.reasons


def test_unknown_license_fails_closed():
    decision = evaluate_authority(evidence(internal_research_allowed=None))
    assert decision.status is AuthorityStatus.CANDIDATE_NOT_AUTHORIZED


def test_forbidden_local_storage_rejects_license():
    decision = evaluate_authority(evidence(local_storage_allowed=False))
    assert decision.status is AuthorityStatus.REJECTED_LICENSE


def test_missing_historical_available_time_fails_closed():
    decision = evaluate_authority(evidence(historical_available_time=False))
    assert decision.status is AuthorityStatus.CANDIDATE_NOT_AUTHORIZED
    assert "HISTORICAL_AVAILABLE_TIME_MISSING" in decision.reasons
    assert not decision.usable_for_scored_research


def test_unproven_deterministic_retrieval_fails_closed():
    decision = evaluate_authority(evidence(deterministic_retrieval=False))
    assert decision.status is AuthorityStatus.CANDIDATE_NOT_AUTHORIZED
    assert "DETERMINISTIC_RETRIEVAL_UNPROVEN" in decision.reasons
