"""Exact trial arm identity and observed-vs-published counters (owner: A2).

Identity
--------
An :class:`ArmIdentity` is the exact identity of one scored arm:
``asset_class + venue + calendar_id + cost_model_id + universe_digest +
family_id + arm_id + arm_config_digest`` (+ optional provenance).  The
canonical digest is sha256 over the canonical JSON of a payload that
namespaces every non-asset-class field under the asset class, so identities
belonging to different asset classes can never collide (asserted by
:func:`assert_cross_asset_class_separation`, proven by tests).

Counters
--------
Pure counting contract for scored results (no ledger IO here):

* every computed scored result increments ``observed`` exactly once, even
  when publication later fails;
* an idempotent replay of an already-observed identity increments neither
  counter;
``published`` only ever grows via :func:`record_publication_success`, at
most once per observed identity.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, replace
from typing import Any, Mapping

from research.assets.common.contracts import (
    canonical_json,
    require_asset_class,
    require_digest_hex,
    require_token,
)

IDENTITY_SCHEMA_VERSION = 1

_STATUS_OBSERVED = "OBSERVED"
_STATUS_PUBLISHED = "PUBLISHED"


@dataclass(frozen=True, kw_only=True)
class ArmIdentity:
    """Exact identity of one scored arm (all fields validated, no defaults)."""

    asset_class: str
    venue: str
    calendar_id: str
    cost_model_id: str
    universe_digest: str
    family_id: str
    arm_id: str
    arm_config_digest: str
    calendar_version: str | None = None
    provider_id: str | None = None
    provider_schema_digest: str | None = None
    window_digest: str | None = None

    def __post_init__(self) -> None:
        require_asset_class(self.asset_class)
        require_token(self.venue, "venue")
        require_token(self.calendar_id, "calendar_id")
        require_token(self.cost_model_id, "cost_model_id")
        require_digest_hex(self.universe_digest, "universe_digest")
        require_token(self.family_id, "family_id")
        require_token(self.arm_id, "arm_id")
        require_digest_hex(self.arm_config_digest, "arm_config_digest")
        for optional in ("calendar_version", "provider_id"):
            value = getattr(self, optional)
            if value is not None:
                require_token(value, optional)
        for digest_field in ("provider_schema_digest", "window_digest"):
            value = getattr(self, digest_field)
            if value is not None:
                require_digest_hex(value, digest_field)

    @property
    def non_class_fields(self) -> dict[str, Any]:
        """Every identity field except ``asset_class`` (for collision checks)."""
        return {
            name: getattr(self, name)
            for name in self.field_names()
            if name != "asset_class"
        }

    @staticmethod
    def field_names() -> tuple[str, ...]:
        return (
            "asset_class", "venue", "calendar_id", "cost_model_id",
            "universe_digest", "family_id", "arm_id", "arm_config_digest",
            "calendar_version", "provider_id", "provider_schema_digest",
            "window_digest",
        )


def canonical_identity_payload(identity: ArmIdentity) -> dict[str, Any]:
    """Namespaced canonical payload: asset class wraps all other fields.

    ``asset_class`` appears both as the namespace key and inside the payload,
    so changing only the asset class always changes the canonical bytes —
    cross-asset-class identities are structurally unable to share a digest.
    """
    fields = {
        name: getattr(identity, name)
        for name in ArmIdentity.field_names()
        if name != "asset_class"
    }
    return {
        "schema": "arm_identity",
        "version": IDENTITY_SCHEMA_VERSION,
        "namespace": identity.asset_class,
        "asset_class": identity.asset_class,
        "fields": fields,
    }


def identity_digest(identity: ArmIdentity) -> str:
    """Canonical sha256 of the namespaced identity payload."""
    return hashlib.sha256(
        canonical_json(canonical_identity_payload(identity)).encode("utf-8")
    ).hexdigest()


def digest_preimage(identity: ArmIdentity) -> str:
    """Canonical JSON string hashed by :func:`identity_digest` (for tests)."""
    return canonical_json(canonical_identity_payload(identity))


def assert_cross_asset_class_separation(a: ArmIdentity, b: ArmIdentity) -> None:
    """Fail closed if two different asset classes ever produce one digest."""
    if a.asset_class == b.asset_class:
        return
    if identity_digest(a) == identity_digest(b):
        raise ValueError(
            "IDENTITY COLLISION: distinct asset classes "
            f"{a.asset_class!r} and {b.asset_class!r} share one digest; "
            "the namespacing contract is broken"
        )


def assert_no_collision(identities: list[ArmIdentity] | tuple[ArmIdentity, ...]) -> None:
    """Pairwise: equal digests require fully equal identities (any fields)."""
    for i in range(len(identities)):
        for j in range(i + 1, len(identities)):
            a, b = identities[i], identities[j]
            assert_cross_asset_class_separation(a, b)
            if identity_digest(a) == identity_digest(b):
                raise ValueError(
                    "IDENTITY COLLISION: distinct identities share one digest: "
                    f"{a!r} vs {b!r}"
                )


# --- observed-vs-published counters (pure, no ledger IO) -------------------- #
@dataclass(frozen=True)
class TrialCounters:
    """Observed vs published trial counters (``published <= observed``)."""

    observed: int = 0
    published: int = 0

    def __post_init__(self) -> None:
        for name in ("observed", "published"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative int, got {value!r}")
        if self.published > self.observed:
            raise ValueError("published cannot exceed observed")


def check_counter_invariants(counters: TrialCounters) -> list[str]:
    """List of violated invariants (empty list = consistent counters)."""
    problems: list[str] = []
    if counters.published > counters.observed:
        problems.append("published_exceeds_observed")
    if counters.observed < 0 or counters.published < 0:
        problems.append("negative_counter")
    return problems


def record_computation(counters: TrialCounters, *, already_observed: bool) -> TrialCounters:
    """A scored result was computed.

    Increments ``observed`` exactly once; a replay of an already-observed
    identity increments NEITHER counter (idempotent replay).  Publication
    success/failure does not affect this call: even if publication later
    fails, the observation has already been counted once.
    """
    if already_observed:
        return counters
    return replace(counters, observed=counters.observed + 1)


def record_publication_success(counters: TrialCounters) -> TrialCounters:
    """Publication succeeded: ``published`` may grow at most once per trial."""
    if counters.published >= counters.observed:
        raise ValueError(
            "publish_requires_unpublished_observed_trial "
            f"(observed={counters.observed}, published={counters.published})"
        )
    return replace(counters, published=counters.published + 1)


def record_publication_failure(counters: TrialCounters) -> TrialCounters:
    """Publication failed: observation stays counted, published does not move."""
    return counters


def record_idempotent_replay(counters: TrialCounters) -> TrialCounters:
    """Idempotent replay of an observed trial: neither counter moves."""
    return counters


@dataclass(frozen=True)
class TrialCounterBook:
    """Pure in-memory bookkeeping of identity statuses + counters.

    Immutable by copy: every operation returns a NEW book and never mutates
    the receiver.  This is the counting logic only — persistence is a
    ledger concern and deliberately out of scope here.
    """

    counters: TrialCounters = field(default_factory=TrialCounters)
    statuses: Mapping[str, str] = field(default_factory=dict)

    def status_of(self, digest: str) -> str | None:
        return self.statuses.get(digest)

    def record_computation(self, digest: str) -> tuple["TrialCounterBook", str]:
        """Record a computed result; returns (new_book, "OBSERVED"|"REPLAYED")."""
        current = self.status_of(digest)
        if current is not None:
            return self, "REPLAYED"
        new_status = dict(self.statuses)
        new_status[digest] = _STATUS_OBSERVED
        book = TrialCounterBook(
            counters=record_computation(self.counters, already_observed=False),
            statuses=new_status,
        )
        return book, _STATUS_OBSERVED

    def record_publication(self, digest: str) -> "TrialCounterBook":
        """Mark an observed-but-unpublished identity as published (once)."""
        current = self.status_of(digest)
        if current == _STATUS_PUBLISHED:
            raise ValueError(f"double publication of {digest}")
        if current is None:
            raise ValueError(f"cannot publish an unobserved identity: {digest}")
        new_status = dict(self.statuses)
        new_status[digest] = _STATUS_PUBLISHED
        return TrialCounterBook(
            counters=record_publication_success(self.counters),
            statuses=new_status,
        )

    def replay(self, digest: str) -> "TrialCounterBook":
        """Idempotent replay: nothing changes, the same book is returned."""
        if self.status_of(digest) is None:
            raise ValueError(f"replay of an unobserved identity: {digest}")
        return TrialCounterBook(
            counters=record_idempotent_replay(self.counters),
            statuses=dict(self.statuses),
        )
