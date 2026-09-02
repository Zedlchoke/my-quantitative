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
"""

from __future__ import annotations

import hashlib
import math
from typing import Any, Mapping, Optional, Sequence

from research.adapter_v10.protocol import ContractViolation, StrategyIdentity
from research.global_ledger import append_verified, digest, snapshot

TRIAL_PUBLICATION_SCHEMA_VERSION = "v10.adapter.trial_publication.v1"
PUBLISHED_CELL_KIND = "CELL_RESULT"

PRESCORE_BLOCKED = "PRE_SCORE_GATE_BLOCKED"
PUBLISHED = "PUBLISHED"
IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY_SKIPPED"

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
) -> dict[str, Any]:
    """Exactly-once publication of one scored cell (see module docstring).

    Returns an honest decision record; ``published=False`` always comes with
    machine-readable reasons and never mutates the ledger.
    """
    payload = canonical_scored_payload(
        identity=identity, stress_signature=stress_signature
    )
    key_hex = trial_key(payload)
    gate_ok, gate_reasons = evaluate_pre_score_gate(scored_metrics)
    state_before = snapshot(ledger_path)
    denominator_before = len(published_cell_rows(state_before["rows"]))
    record: dict[str, Any] = {
        "trial_key_sha256": key_hex,
        "ledger_path": state_before["path"],
        "ledger_count_before": state_before["count"],
        "ledger_sha256_before": state_before["sha256"],
        "denominator_before": denominator_before,
        "pre_score_passed": gate_ok,
        "pre_score_reasons": gate_reasons,
        "published": False,
        "stage": "",
        "reasons": [],
    }
    if not gate_ok:
        record.update(stage=PRESCORE_BLOCKED, reasons=list(gate_reasons))
        return record

    existing = find_existing_trial(key_hex, ledger_path)
    if existing is not None:
        record.update(
            stage=IDEMPOTENT_REPLAY,
            reasons=["duplicate_trial_key_already_published"],
            existing_experiment_id=existing.get("experiment_id"),
            denominator_after=denominator_before,
            denominator_delta=0,
        )
        return record

    entry = {
        "experiment_id": f"{matrix_id}-{key_hex[:16]}",
        "verdict": verdict,
        "kind": PUBLISHED_CELL_KIND,
        "schema": TRIAL_PUBLICATION_SCHEMA_VERSION,
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
        record.update(stage="LEDGER_APPEND_REFUSED", reasons=[str(exc)])
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
    "canonical_scored_payload",
    "evaluate_pre_score_gate",
    "find_existing_trial",
    "publish_trial",
    "trial_denominator",
    "trial_key",
]
