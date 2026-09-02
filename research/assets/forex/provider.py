"""Provider/dealer identity and entitlement surface (owner: A3, PLAN_forex.md 2, 7-A3).

FX is decentralized: one feed is never labeled "the global FX market", so the
provider/dealer identity is recorded explicitly and promoted evidence must
come from an owner-authorized bid/ask provider (PLAN_forex.md section 2,
candidate 1-3).  Midpoint-only public data (candidate 4) is
``DIAGNOSTIC_ONLY`` and is structurally never promotable.

Fail-closed rules frozen here:

* with no owner-authorized provider recorded (the current state of this
  factory: entitlement ``UNAVAILABLE_FAIL_CLOSED``), no quote data may be
  promoted — :func:`classify_provider` returns
  :data:`PROVIDER_STATUS_UNAVAILABLE` and nothing may override it;
* a ``MIDPOINT_ONLY`` source is :data:`PROVIDER_STATUS_DIAGNOSTIC_ONLY`
  even when someone marks it owner-authorized; it can never become
  promotable evidence;
* only ``owner_authorized=True`` AND ``quote_mode=BID_ASK`` yields
  :data:`PROVIDER_STATUS_PROMOTABLE`.

No network calls, no credentials, no IO of any kind — identity records are
supplied by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from research.assets.common.contracts import (
    canonical_json,
    canonical_payload,
    require_digest_hex,
    require_token,
)

# --- frozen vocabulary ------------------------------------------------------ #
QUOTE_MODE_BID_ASK = "BID_ASK"
QUOTE_MODE_MIDPOINT_ONLY = "MIDPOINT_ONLY"
QUOTE_MODES = (QUOTE_MODE_BID_ASK, QUOTE_MODE_MIDPOINT_ONLY)

PROVIDER_STATUS_PROMOTABLE = "PROMOTABLE"
PROVIDER_STATUS_DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
PROVIDER_STATUS_UNAVAILABLE = "UNAVAILABLE_FAIL_CLOSED"

# Explicit, non-overridable rule of this lane (PLAN_forex.md section 2,
# candidate 4): midpoint-only data is diagnostic, never promotable evidence.
MIDPOINT_ONLY_PROMOTABLE = False


@dataclass(frozen=True)
class ProviderIdentity:
    """Frozen provider/dealer identity record.

    ``provider_id`` + ``schema_digest`` are the identity pair referenced by
    forex trial identities (PLAN_forex.md section 3).  ``venue_scope`` names
    the dealer/venue scope of the feed (FX is decentralized; scope is never
    implied).  All fields are required — there are no defaults.
    """

    provider_id: str
    schema_digest: str
    quote_mode: str
    owner_authorized: bool
    venue_scope: str

    def __post_init__(self) -> None:
        require_token(self.provider_id, "provider_id")
        require_digest_hex(self.schema_digest, "schema_digest")
        if self.quote_mode not in QUOTE_MODES:
            raise ValueError(
                f"quote_mode must be one of {QUOTE_MODES}, got {self.quote_mode!r}"
            )
        if not isinstance(self.owner_authorized, bool):
            raise ValueError(
                f"owner_authorized must be a bool, got {self.owner_authorized!r}"
            )
        require_token(self.venue_scope, "venue_scope")

    def canonical_payload(self) -> dict[str, Any]:
        return canonical_payload(self)

    def canonical_json(self) -> str:
        return canonical_json(self.canonical_payload())


@dataclass(frozen=True)
class EntitlementDecision:
    """Outcome of the entitlement/authority check.

    Invariant enforced at construction (fail-closed): ``promotable`` is True
    if and only if ``status`` is :data:`PROVIDER_STATUS_PROMOTABLE`, and a
    non-empty machine-readable ``reason`` is always attached.
    """

    status: str
    promotable: bool
    reason: str

    def __post_init__(self) -> None:
        if self.status not in (
            PROVIDER_STATUS_PROMOTABLE,
            PROVIDER_STATUS_DIAGNOSTIC_ONLY,
            PROVIDER_STATUS_UNAVAILABLE,
        ):
            raise ValueError(f"unknown entitlement status: {self.status!r}")
        if not isinstance(self.promotable, bool):
            raise ValueError(f"promotable must be a bool, got {self.promotable!r}")
        if self.promotable != (self.status == PROVIDER_STATUS_PROMOTABLE):
            raise ValueError(
                "promotable must be True exactly when status is "
                f"{PROVIDER_STATUS_PROMOTABLE} (status={self.status!r})"
            )
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("EntitlementDecision requires a non-empty reason")


def classify_provider(identity: ProviderIdentity | None) -> EntitlementDecision:
    """Entitlement/authority check for a recorded provider (or absence).

    Fail-closed decision order:

    1. nothing recorded (or not owner-authorized) →
       :data:`PROVIDER_STATUS_UNAVAILABLE`;
    2. ``MIDPOINT_ONLY`` → :data:`PROVIDER_STATUS_DIAGNOSTIC_ONLY`
       (never promotable, by explicit rule — see
       :data:`MIDPOINT_ONLY_PROMOTABLE`);
    3. ``BID_ASK`` + owner authorization → :data:`PROVIDER_STATUS_PROMOTABLE`.
    """
    if identity is None:
        return EntitlementDecision(
            status=PROVIDER_STATUS_UNAVAILABLE,
            promotable=False,
            reason="NO_OWNER_AUTHORIZED_PROVIDER_RECORDED",
        )
    if not isinstance(identity, ProviderIdentity):
        raise TypeError(
            f"identity must be ProviderIdentity or None, got {type(identity).__name__}"
        )
    if identity.quote_mode == QUOTE_MODE_MIDPOINT_ONLY:
        return EntitlementDecision(
            status=PROVIDER_STATUS_DIAGNOSTIC_ONLY,
            promotable=MIDPOINT_ONLY_PROMOTABLE,
            reason="MIDPOINT_ONLY_SOURCE_NEVER_PROMOTABLE",
        )
    if not identity.owner_authorized:
        return EntitlementDecision(
            status=PROVIDER_STATUS_UNAVAILABLE,
            promotable=False,
            reason=f"PROVIDER_{identity.provider_id}_NOT_OWNER_AUTHORIZED",
        )
    return EntitlementDecision(
        status=PROVIDER_STATUS_PROMOTABLE,
        promotable=True,
        reason=f"OWNER_AUTHORIZED_BID_ASK_PROVIDER_{identity.provider_id}",
    )


def require_promotable(decision: EntitlementDecision) -> EntitlementDecision:
    """Fail closed unless the decision is promotable (gate helper)."""
    if not isinstance(decision, EntitlementDecision):
        raise TypeError(
            f"decision must be EntitlementDecision, got {type(decision).__name__}"
        )
    if not decision.promotable:
        raise ValueError(
            f"provider evidence is not promotable: status={decision.status} "
            f"reason={decision.reason}"
        )
    return decision
