"""Fail-closed license, entitlement and PIT authority decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AuthorityStatus(str, Enum):
    DOCUMENTED_CANDIDATE = "DOCUMENTED_CANDIDATE"
    CANDIDATE_NOT_AUTHORIZED = "CANDIDATE_NOT_AUTHORIZED"
    AUTHORIZED_INTERNAL_RESEARCH = "AUTHORIZED_INTERNAL_RESEARCH"
    UNAVAILABLE_FAIL_CLOSED = "UNAVAILABLE_FAIL_CLOSED"
    REJECTED_LICENSE = "REJECTED_LICENSE"


@dataclass(frozen=True, slots=True)
class AuthorityEvidence:
    source_id: str
    terms_captured: bool
    internal_research_allowed: bool | None
    local_storage_allowed: bool | None
    redistribution_allowed: bool | None
    entitlement_active: bool
    deterministic_retrieval: bool
    historical_available_time: bool
    raw_hashes_recorded: bool
    account_or_key_required: bool
    account_or_key_authorized: bool


@dataclass(frozen=True, slots=True)
class AuthorityDecision:
    status: AuthorityStatus
    reasons: tuple[str, ...]

    @property
    def usable_for_scored_research(self) -> bool:
        return self.status is AuthorityStatus.AUTHORIZED_INTERNAL_RESEARCH


def evaluate_authority(evidence: AuthorityEvidence) -> AuthorityDecision:
    reasons: list[str] = []
    if not evidence.terms_captured:
        reasons.append("TERMS_NOT_CAPTURED")
    if evidence.internal_research_allowed is False or evidence.local_storage_allowed is False:
        return AuthorityDecision(AuthorityStatus.REJECTED_LICENSE, ("LICENSE_FORBIDS_REQUIRED_USE",))
    if evidence.internal_research_allowed is None:
        reasons.append("INTERNAL_RESEARCH_RIGHT_UNKNOWN")
    if evidence.local_storage_allowed is None:
        reasons.append("LOCAL_STORAGE_RIGHT_UNKNOWN")
    if not evidence.entitlement_active:
        reasons.append("ENTITLEMENT_INACTIVE")
    if evidence.account_or_key_required and not evidence.account_or_key_authorized:
        reasons.append("ACCOUNT_OR_KEY_NOT_AUTHORIZED")
    if not evidence.deterministic_retrieval:
        reasons.append("DETERMINISTIC_RETRIEVAL_UNPROVEN")
    if not evidence.historical_available_time:
        reasons.append("HISTORICAL_AVAILABLE_TIME_MISSING")
    if not evidence.raw_hashes_recorded:
        reasons.append("RAW_HASHES_MISSING")
    if reasons:
        return AuthorityDecision(AuthorityStatus.CANDIDATE_NOT_AUTHORIZED, tuple(reasons))
    return AuthorityDecision(AuthorityStatus.AUTHORIZED_INTERNAL_RESEARCH, ())
