"""BG6 -- idempotent, exactly-once trial publication (G1).

Publication is the ONLY writer this lane has, and it delegates every write to
``research.global_ledger.append_verified`` over the append-only registry, so:

* a trial whose pre-score gate failed appends NOTHING;
* a valid score appends EXACTLY ONE row, keyed by a deterministic
  ``trial_key_sha256`` over the strategy identity + stress cell + window +
  artifact digests;
* re-running the same cell finds the existing key in the snapshot and appends
  nothing, so the scored-trial denominator can never be double-counted;
* the ledger must verify append-only before any append, otherwise nothing is
  written (fail closed).

V11P lane A2 additions (identity repair):

* ``publish_trial`` accepts an explicit ``arm_id`` / ``identity_version``.
  Declaring an arm switches the key to the versioned v2 identity
  (:mod:`research.v11.publication_identity`), whose canonical
  ``arm_config_digest`` covers every score-affecting arm field, so arms that
  differ only inside ``identity.config`` can never collide again.  Omitting
  the arm reproduces the frozen historical v1 key exactly (readability of old
  rows; never rewritten).
* computed-but-unpublished scored trials can be recorded as append-only
  trial observations (:func:`record_trial_observation`) -- e.g. a neighbour
  arm refused by the historical v1 key collision -- which increments the
  observed denominator without touching the published one;
* every check-then-append critical section runs under one process-local
  reentrant lock, so exactly-once publication and observation dedupe also
  hold when publishers race inside one process (cross-process writers to one
  ledger file stay outside this guarantee; factory policy assigns one writer
  per worktree ledger).
"""

from __future__ import annotations

import hashlib
import math
import threading
from typing import Any, Mapping, Optional, Sequence

from research.adapter_v10.protocol import ContractViolation, StrategyIdentity
from research.global_ledger import append_verified, digest, snapshot
from research.v11.publication_identity import (
    IDENTITY_VERSION_V2,
    TRIAL_PUBLICATION_SCHEMA_VERSION_V2,
    denominator_split,
    observation_rows,
    unpublished_trial_observation_entry,
)

TRIAL_PUBLICATION_SCHEMA_VERSION = "v10.adapter.trial_publication.v1"
PUBLISHED_CELL_KIND = "CELL_RESULT"

#: Process-local guard around every check-then-append critical section so
#: exactly-once publication and observation dedupe hold under in-process
#: concurrency (threads), not only in serial flows.  Reentrant because
#: ``publish_trial`` calls :func:`record_trial_observation` while holding it.
#: Cross-process writers to ONE ledger file remain outside this guarantee;
#: factory concurrency policy (PLAN section 5.2) assigns one writer per
#: worktree ledger.
_PUBLICATION_LOCK = threading.RLock()

PRESCORE_BLOCKED = "PRE_SCORE_GATE_BLOCKED"
PUBLISHED = "PUBLISHED"
IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY_SKIPPED"
LEDGER_APPEND_REFUSED = "LEDGER_APPEND_REFUSED"

#: Scored metric fields that MUST be present and finite for a publish attempt.
REQUIRED_SCORED_FIELDS: tuple[str, ...] = (
    "net_return_sum",
    "expectancy_per_day",
    "max_drawdown",
)


def canonical_scored_payload(
    *, identity: StrategyIdentity, stress_signature: Mapping[str, Any], extra: Optional[Mapping[str, Any]] = None
) -> dict[str, Any]:
    """Deterministic key payload for one scored cell."""
    return {
        "schema_version": TRIAL_PUBLICATION_SCHEMA_VERSION,
        "strategy_id": identity.strategy_id,
        "family_id": identity.family_id,
        "arm_config_id": identity.arm_config_id,
        "direction": identity.direction,
        "window_start_iso": identity.window_start_iso,
        "window_end_iso": identity.window_end_iso,
        "stress": {
            str(k): stress_signature[k]
            for k in sorted(stress_signature, key=str)
        },
        "extra": {str(k): extra[k] for k in sorted(extra or {}, key=str)},
    }


def trial_key(payload: Mapping[str, Any]) -> str:
    """Stable sha256 over the canonical scored payload."""
    import json

    canonical = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def evaluate_pre_score_gate(
    scored_metrics: Optional[Mapping[str, Any]], *,
    required_fields: Sequence[str] = REQUIRED_SCORED_FIELDS
) -> tuple[bool, list[str]]:
    """Fail-closed pre-score gate (no fabricated metrics allowed)."""
    if not isinstance(scored_metrics, Mapping):
        return False, ["pre_score_missing_metrics_payload"]
    reasons: list[str] = []
    if not bool(scored_metrics.get("score_valid", False)):
        reasons.append("pre_score_flag_false")
    for field in required_fields:
        value = scored_metrics.get(field)
        if value is None:
            reasons.append(f"pre_score_field_absent:{field}")
        elif isinstance(value, float) and not math.isfinite(value):
            reasons.append(f"pre_score_field_non_finite:{field}")
        elif not isinstance(value, (int, float)):
            reasons.append(f"pre_score_field_not_numeric:{field}")
    return (not reasons), reasons


def published_cell_rows(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Ledger rows that count toward the scored-trial denominator."""
    return [row for row in rows if row.get("kind") == PUBLISHED_CELL_KIND]


def trial_denominator(ledger_path: Optional[str] = None) -> int:
    """Number of already-published scored cells in the global ledger."""
    return len(published_cell_rows(snapshot(ledger_path)["rows"]))


def find_existing_trial(
    key_hex: str, ledger_path: Optional[str] = None
) -> Optional[Mapping[str, Any]]:
    """First ledger row carrying ``trial_key_sha256 == key_hex`` (or None)."""
    rows = snapshot(ledger_path)["rows"]
    for row in published_cell_rows(rows):
        if row.get("trial_key_sha256") == key_hex:
            return row
    return None


def _resolve_key_payload(
    *,
    identity: StrategyIdentity,
    stress_signature: Mapping[str, Any],
    arm_id: str,
    identity_version: Optional[str],
) -> tuple[dict[str, Any], str, str]:
    """Build the key payload for the requested identity version.

    Returns ``(payload, version, effective_arm_id)``.  Fail closed: an
    arm-aware trial must use v2, a v2 key must declare an arm, and an unknown
    version is refused (no silent fallback, ever).
    """
    declared = str(getattr(identity, "arm_id", "") or "").strip()
    effective_arm = str(arm_id or "").strip() or declared
    if arm_id and not str(arm_id).strip():
        raise ContractViolation("arm_id must not be whitespace-only")
    if identity_version is None:
        version = IDENTITY_VERSION_V2 if effective_arm else "v1"
    else:
        version = str(identity_version).strip().lower()
    if version == IDENTITY_VERSION_V2:
        from research.v11.publication_identity import canonical_scored_payload_v2

        if not effective_arm:
            raise ContractViolation(
                "v2 publication requires an explicit arm_id (argument or "
                "identity.arm_id); refusing a key that could collide across arms"
            )
        payload = canonical_scored_payload_v2(
            identity=identity, stress_signature=stress_signature, arm_id=effective_arm
        )
    elif version == "v1":
        if effective_arm:
            raise ContractViolation(
                "arm-aware trials must use identity_version='v2'; the v1 key is "
                "frozen for historical rows and cannot express arms"
            )
        payload = canonical_scored_payload(identity=identity, stress_signature=stress_signature)
    else:
        raise ContractViolation(f"unknown identity_version: {identity_version!r}")
    return payload, version, effective_arm


def _observation_outcome(
    record: Mapping[str, Any],
    *,
    identity: StrategyIdentity,
    stress_signature: Mapping[str, Any],
    effective_arm: str,
    identity_version: str,
    matrix_id: str,
    observe_unpublished: bool,
    ledger_path: Optional[str],
) -> Optional[dict[str, Any]]:
    """Record a compute-once observation when publication was refused.

    Only scored computes (pre-score gate passed) whose publication was refused
    AFTER the gate are observable.  A true v2 idempotent replay is the same
    arm trial already published, so it is never observed (neither counter may
    move).
    """
    if not observe_unpublished:
        return None
    stage = str(record.get("stage", ""))
    if stage not in (IDEMPOTENT_REPLAY, LEDGER_APPEND_REFUSED):
        return None
    if stage == IDEMPOTENT_REPLAY and identity_version == IDENTITY_VERSION_V2:
        return {
            "attempted": False,
            "appended": False,
            "reasons": ["true_v2_replay_of_published_trial_not_observable"],
        }
    if not effective_arm:
        return {
            "attempted": False,
            "appended": False,
            "reasons": ["observation_requires_explicit_arm_id"],
        }
    entry = unpublished_trial_observation_entry(
        identity=identity,
        arm_id=effective_arm,
        stress_signature=stress_signature,
        publication_stage=stage,
        publication_reasons=record.get("reasons", []),
        matrix_id=matrix_id,
        producer_role="A2",
    )
    return record_trial_observation(entry, ledger_path)


def record_trial_observation(
    entry: Mapping[str, Any], ledger_path: Optional[str] = None
) -> dict[str, Any]:
    """Append-only record of ONE computed-but-unpublished scored trial.

    Exactly-once per ``observation_key_sha256``: an exact re-observation is
    refused (no double counting).  Observation rows carry no ``kind``, so the
    published ``CELL_RESULT`` denominator can never move.  Serialised by the
    same reentrant lock as :func:`publish_trial` so a concurrent
    check-then-append cannot duplicate an observation.
    """
    key_hex = str(entry.get("observation_key_sha256", "") or "")
    if not key_hex:
        raise ContractViolation(
            "trial observation entry lacks observation_key_sha256"
        )
    with _PUBLICATION_LOCK:
        existing = {
            row.get("observation_key_sha256")
            for row in observation_rows(snapshot(ledger_path)["rows"])
        }
        if key_hex in existing:
            return {
                "attempted": True,
                "appended": False,
                "reasons": ["duplicate_observation_key_already_recorded"],
                "observation_key_sha256": key_hex,
            }
        try:
            stored = append_verified(dict(entry), ledger_path)
        except ValueError as exc:
            return {
                "attempted": True,
                "appended": False,
                "reasons": [str(exc)],
                "observation_key_sha256": key_hex,
            }
        return {
            "attempted": True,
            "appended": True,
            "reasons": [],
            "observation_key_sha256": key_hex,
            "experiment_id": stored.get("experiment_id"),
        }


def denominator_view(ledger_path: Optional[str] = None) -> dict[str, int]:
    """Honest denominator split of the ledger (see
    :func:`research.v11.publication_identity.denominator_split`).

    ``published`` is the frozen scored-trial denominator;
    ``observed_unpublished`` counts distinct computed-but-unpublished scored
    trials; ``observed_total`` is the scientific denominator used by
    statistical consumers.
    """
    return denominator_split(snapshot(ledger_path)["rows"])


def publish_trial(
    *,
    identity: StrategyIdentity,
    stress_signature: Mapping[str, Any],
    scored_metrics: Mapping[str, Any],
    payload_digests: Mapping[str, str],
    experiment_digest: str,
    matrix_id: str,
    verdict: str = "CELL_RESULT",
    ledger_path: Optional[str] = None,
    arm_id: str = "",
    identity_version: Optional[str] = None,
    observe_unpublished: bool = False,
) -> dict[str, Any]:
    """Exactly-once publication of one scored cell (see module docstring).

    Returns an honest decision record; ``published=False`` always comes with
    machine-readable reasons and never mutates the ledger.  With
    ``arm_id``/``identity_version='v2'`` the key carries the explicit arm
    identity; with ``observe_unpublished=True`` a post-gate publication
    refusal also records an append-only trial observation (compute-once
    accounting) without ever touching the published denominator.
    """
    payload, version, effective_arm = _resolve_key_payload(
        identity=identity,
        stress_signature=stress_signature,
        arm_id=arm_id,
        identity_version=identity_version,
    )
    key_hex = trial_key(payload)
    gate_ok, gate_reasons = evaluate_pre_score_gate(scored_metrics)
    record: dict[str, Any] = {
        "trial_key_sha256": key_hex,
        "identity_version": version,
        "pre_score_passed": gate_ok,
        "pre_score_reasons": gate_reasons,
        "published": False,
        "stage": "",
        "reasons": [],
    }
    if not gate_ok:
        record.update(stage=PRESCORE_BLOCKED, reasons=list(gate_reasons))
        return record

    # Exactly-once critical section: the denominator-before read, the
    # duplicate-key check and the append must observe one consistent ledger
    # state, so concurrent publishers can never double count.
    with _PUBLICATION_LOCK:
        state_before = snapshot(ledger_path)
        denominator_before = len(published_cell_rows(state_before["rows"]))
        record.update(
            ledger_path=state_before["path"],
            ledger_count_before=state_before["count"],
            ledger_sha256_before=state_before["sha256"],
            denominator_before=denominator_before,
        )
        if version == IDENTITY_VERSION_V2:
            record["arm_id"] = effective_arm
            record["arm_config_digest"] = payload["arm_config_digest"]

        existing = find_existing_trial(key_hex, ledger_path)
        if existing is not None:
            record.update(
                stage=IDEMPOTENT_REPLAY,
                reasons=["duplicate_trial_key_already_published"],
                existing_experiment_id=existing.get("experiment_id"),
                denominator_after=denominator_before,
                denominator_delta=0,
            )
            record["observed"] = _observation_outcome(
                record,
                identity=identity,
                stress_signature=stress_signature,
                effective_arm=effective_arm,
                identity_version=version,
                matrix_id=matrix_id,
                observe_unpublished=observe_unpublished,
                ledger_path=ledger_path,
            )
            return record

        entry = {
            "experiment_id": f"{matrix_id}-{key_hex[:16]}",
            "verdict": verdict,
            "kind": PUBLISHED_CELL_KIND,
            "schema": payload["schema_version"],
            "matrix_id": str(matrix_id),
            "trial_key_sha256": key_hex,
            "payload": payload,
            "experiment_digest": experiment_digest,
            "artifact_digests": {str(k): str(v) for k, v in sorted(payload_digests.items())},
            "producer_role": "G1",
        }
        try:
            stored = append_verified(entry, ledger_path)
        except ValueError as exc:
            record.update(stage=LEDGER_APPEND_REFUSED, reasons=[str(exc)])
            record["observed"] = _observation_outcome(
                record,
                identity=identity,
                stress_signature=stress_signature,
                effective_arm=effective_arm,
                identity_version=version,
                matrix_id=matrix_id,
                observe_unpublished=observe_unpublished,
                ledger_path=ledger_path,
            )
            return record

        state_after = snapshot(ledger_path)
        denominator_after = len(published_cell_rows(state_after["rows"]))
        if denominator_after != denominator_before + 1:
            raise ContractViolation(
                f"ledger append changed the denominator by "
                f"{denominator_after - denominator_before}, expected +1"
            )
        record.update(
            stage=PUBLISHED,
            reasons=[],
            published=True,
            experiment_id=stored["experiment_id"],
            appended_at=stored["appended_at"],
            ledger_count_after=state_after["count"],
            ledger_sha256_after=state_after["sha256"],
            ledger_digest_after=digest(state_after),
            denominator_after=denominator_after,
            denominator_delta=denominator_after - denominator_before,
        )
        return record


__all__ = [
    "IDEMPOTENT_REPLAY",
    "PRESCORE_BLOCKED",
    "PUBLISHED",
    "PUBLISHED_CELL_KIND",
    "REQUIRED_SCORED_FIELDS",
    "TRIAL_PUBLICATION_SCHEMA_VERSION",
    "TRIAL_PUBLICATION_SCHEMA_VERSION_V2",
    "canonical_scored_payload",
    "denominator_view",
    "evaluate_pre_score_gate",
    "find_existing_trial",
    "publish_trial",
    "record_trial_observation",
    "trial_denominator",
    "trial_key",
]
