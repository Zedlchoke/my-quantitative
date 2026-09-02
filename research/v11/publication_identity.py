"""V11 versioned trial identity (v2) + append-only denominator reconciliation.

Sprint V11P lane A2. This module repairs the V10 publication-identity defect
documented in ``research/control/v10r_run/family_terminal_m01.json`` (lesson
``L-CONTRACT-1``): the frozen V10 key payload keyed on ``arm_config_id``
alone, so two arms that differ only inside ``StrategyIdentity.config`` (e.g.
``neighbour_mode``) collided on one ``trial_key_sha256`` -- the second arm was
computed but could never be published (``duplicate_trial_key_already_published``).

What lives here:

* **Identity v2** -- :func:`canonical_scored_payload_v2` adds an explicit
  ``arm_id`` and a canonical ``arm_config_digest`` to the trial key payload.
  Every score-affecting arm field (``arm_config_id``, ``arm_id``,
  ``direction``, funding sign convention, benchmark-exclusion set and the
  ENTIRE ``config`` mapping) influences the digest, so anchor, neighbour and
  causal-control arms always produce distinct keys.  Exact replay of the same
  arm produces the same key, preserving exactly-once publication.
* **Historical readability** -- v1 keys are never rewritten.  The frozen v1
  payload structure is pinned by :func:`legacy_v1_payload` /
  :func:`legacy_v1_key` so historical ledger rows remain readable and
  reproducible; historical bytes are never modified by this lane.
* **Trial observations (append-only reconciliation)** -- a computed-but-
  unpublished scored trial is recorded as a provenance-linked observation row
  (no ``kind`` field, so the registry kind contract accepts it and it can
  never count toward the published ``CELL_RESULT`` denominator).  Exactly-once
  per ``observation_key_sha256``; observations are marked computed-unpublished
  and are never re-scored.
* **M01 neighbour amendment** -- :func:`m01_neighbour_amendment_entry` freezes
  the M01 neighbour values from ``family_terminal_m01.json`` as documented
  provenance, giving the honest reconciliation ledger=published 119 /
  observed=120 (PLAN section 0) without touching any historical row.

Fail-closed rules inherited from the factory: no silent defaults, no
fabricated metrics, appends only after the ledger verifies append-only, and
any violation leaves the ledger untouched.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from research.adapter_v10.protocol import ContractViolation, StrategyIdentity

# --------------------------------------------------------------------------- #
# Versioned identity schema constants
# --------------------------------------------------------------------------- #
#: Historical V10 publication schema (READABLE ONLY -- never emitted again
#: for new arm-aware trials; pinned so historical rows stay reproducible).
TRIAL_PUBLICATION_SCHEMA_VERSION_V1 = "v10.adapter.trial_publication.v1"
#: V11 publication schema carrying the versioned arm identity.
TRIAL_PUBLICATION_SCHEMA_VERSION_V2 = "v11.adapter.trial_publication.v2"

IDENTITY_VERSION_V2 = "v2"
#: Schema token embedded inside the digest payload so the digest definition
#: itself is versioned and auditable.
ARM_CONFIG_DIGEST_SCHEMA = "v11.arm_config_digest.v1"

#: Schema for append-only computed-unpublished trial observations.
TRIAL_OBSERVATION_SCHEMA_VERSION = "v11.trial_observation.v1"
#: Free-text ``verdict`` token required by the registry on every row.
OBSERVATION_VERDICT = "TRIAL_OBSERVATION_AMENDMENT"

# --------------------------------------------------------------------------- #
# Frozen M01 reconciliation provenance (PLAN section 0 / 1; values are read
# from the documented terminal artifact, never re-computed or re-scored).
# --------------------------------------------------------------------------- #
M01_TERMINAL_ARTIFACT = "research/control/v10r_run/family_terminal_m01.json"
M01_FAMILY_ID = "A8-V10-M01-AGGRESSOR-ABSORPTION-PANEL"
#: ``family_terminal_m01.json``: 117 historical + 2 published = 119.
M01_FROZEN_PUBLISHED_DENOMINATOR = 119
#: PLAN section 0: observed scored denominator = 119 published + 1
#: computed-unpublished neighbour = 120 (pending this reconciliation).
M01_FROZEN_OBSERVED_DENOMINATOR = 120
M01_NEIGHBOUR_ARM_ID = "neighbour"
#: Metric values as documented by producer A1 (verbatim, never re-scored).
M01_NEIGHBOUR_FROZEN_METRICS: dict[str, float] = {
    "net_return_sum": -515951.9347,
    "expectancy_per_day": -1413.5669,
    "max_drawdown": 515951.9347,
}


def _canonical_json(payload: Mapping[str, Any]) -> str:
    """Single canonicalisation used by every digest in this module."""
    return json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), default=str)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Identity v2 -- explicit arm_id + canonical arm_config_digest
# --------------------------------------------------------------------------- #
def resolve_arm_id(identity: StrategyIdentity, arm_id: str = "") -> str:
    """Explicit arm id: the argument wins over ``identity.arm_id``.

    Raises :class:`ContractViolation` on whitespace-only non-empty input so a
    silently-blank arm can never enter a v2 key.
    """
    explicit = str(arm_id or "").strip()
    declared = str(getattr(identity, "arm_id", "") or "").strip()
    if arm_id and not explicit:
        raise ContractViolation("arm_id must not be whitespace-only")
    resolved = explicit or declared
    if not resolved:
        raise ContractViolation(
            "v2 trial identity requires an explicit non-empty arm_id "
            "(argument or identity.arm_id)"
        )
    return resolved


def canonical_arm_payload(identity: StrategyIdentity, *, arm_id: str = "") -> dict[str, Any]:
    """Canonical, digestable payload of every score-affecting arm field.

    The ENTIRE ``config`` mapping is included verbatim (JSON-safe via
    ``StrategyIdentity.public_payload``), so any plugin-declared arm knob that
    can move a score necessarily moves the digest.  Window stamps are
    deliberately EXCLUDED: they are cell fields (already part of the full
    trial key), not arm fields, so the digest stays comparable across cells.
    """
    resolved_arm = resolve_arm_id(identity, arm_id=arm_id)
    view = identity.public_payload()
    return {
        "schema": ARM_CONFIG_DIGEST_SCHEMA,
        "strategy_id": view["strategy_id"],
        "family_id": view["family_id"],
        "arm_config_id": view["arm_config_id"],
        "arm_id": resolved_arm,
        "direction": view["direction"],
        "funding_sign_convention": view["funding_sign_convention"],
        "benchmark_symbols_excluded": list(view["benchmark_symbols_excluded"]),
        "config": view["config"],
    }


def arm_config_digest(identity: StrategyIdentity, *, arm_id: str = "") -> str:
    """sha256 over :func:`canonical_arm_payload` (versioned, canonical JSON)."""
    return _sha256_text(_canonical_json(canonical_arm_payload(identity, arm_id=arm_id)))


def canonical_scored_payload_v2(
    *,
    identity: StrategyIdentity,
    stress_signature: Mapping[str, Any],
    extra: Optional[Mapping[str, Any]] = None,
    arm_id: str = "",
) -> dict[str, Any]:
    """V2 deterministic key payload for one scored cell (see module docstring).

    Superset of the frozen v1 payload: adds ``identity_version``, ``arm_id``
    and ``arm_config_digest``.  ``arm_id`` is mandatory (fail closed).
    """
    resolved_arm = resolve_arm_id(identity, arm_id=arm_id)
    return {
        "schema_version": TRIAL_PUBLICATION_SCHEMA_VERSION_V2,
        "identity_version": IDENTITY_VERSION_V2,
        "arm_id": resolved_arm,
        "arm_config_digest": arm_config_digest(identity, arm_id=resolved_arm),
        "strategy_id": identity.strategy_id,
        "family_id": identity.family_id,
        "arm_config_id": identity.arm_config_id,
        "direction": identity.direction,
        "window_start_iso": identity.window_start_iso,
        "window_end_iso": identity.window_end_iso,
        "stress": {
            str(k): stress_signature[k] for k in sorted(stress_signature, key=str)
        },
        "extra": {str(k): extra[k] for k in sorted(extra or {}, key=str)},
    }


def trial_key_v2(
    *,
    identity: StrategyIdentity,
    stress_signature: Mapping[str, Any],
    extra: Optional[Mapping[str, Any]] = None,
    arm_id: str = "",
) -> str:
    """Stable sha256 key of the v2 payload (same canonicalisation as v1)."""
    return _sha256_text(
        _canonical_json(
            canonical_scored_payload_v2(
                identity=identity,
                stress_signature=stress_signature,
                extra=extra,
                arm_id=arm_id,
            )
        )
    )


# --------------------------------------------------------------------------- #
# Historical v1 readability (never rewrites old ledger bytes)
# --------------------------------------------------------------------------- #
V1_PAYLOAD_KEYS: tuple[str, ...] = (
    "schema_version",
    "strategy_id",
    "family_id",
    "arm_config_id",
    "direction",
    "window_start_iso",
    "window_end_iso",
    "stress",
    "extra",
)


def legacy_v1_payload(
    *, identity: StrategyIdentity, stress_signature: Mapping[str, Any]
) -> dict[str, Any]:
    """Byte-stable reconstruction of the frozen v1 key payload.

    Delegates to ``research.adapter_v10.publish.canonical_scored_payload``
    (lazy import -- that module imports this one) and pins its key set so any
    future drift of the historical builder is caught by tests.
    """
    from research.adapter_v10.publish import canonical_scored_payload

    payload = canonical_scored_payload(identity=identity, stress_signature=stress_signature)
    if tuple(sorted(payload)) != tuple(sorted(V1_PAYLOAD_KEYS)):
        raise ContractViolation("legacy v1 payload shape drifted from the frozen contract")
    return payload


def legacy_v1_key(
    *, identity: StrategyIdentity, stress_signature: Mapping[str, Any]
) -> str:
    """Recomputed historical v1 key (for reading/matching old rows only)."""
    return _sha256_text(
        _canonical_json(
            legacy_v1_payload(identity=identity, stress_signature=stress_signature)
        )
    )


# --------------------------------------------------------------------------- #
# Trial observations -- append-only computed-unpublished reconciliation
# --------------------------------------------------------------------------- #
def observation_key_sha256(key_material: Mapping[str, Any]) -> str:
    """Exactly-once key for one observation (digest of its key material)."""
    return _sha256_text(_canonical_json(key_material))


def unpublished_trial_observation_entry(
    *,
    identity: StrategyIdentity,
    arm_id: str,
    stress_signature: Mapping[str, Any],
    publication_stage: str,
    publication_reasons: Sequence[str],
    matrix_id: str,
    scored_metrics_digest: str = "",
    producer_role: str = "A2",
    provenance: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Ledger entry recording a computed-but-unpublished scored trial.

    The row deliberately carries NO ``kind`` field: the registry kind contract
    accepts it, and ``publish.published_cell_rows`` can therefore never count
    it toward the published denominator.  Dedupe key is the trial's own v2
    identity key, so an exact re-observation is refused.
    """
    resolved_arm = resolve_arm_id(identity, arm_id=arm_id)
    v2_key = trial_key_v2(
        identity=identity, stress_signature=stress_signature, arm_id=resolved_arm
    )
    key_material = {
        "schema": TRIAL_OBSERVATION_SCHEMA_VERSION,
        "observed_trial_key_sha256": v2_key,
        "publication_stage": str(publication_stage),
    }
    return {
        "schema": TRIAL_OBSERVATION_SCHEMA_VERSION,
        "experiment_id": f"{str(matrix_id)}-obs-{v2_key[:16]}",
        "verdict": OBSERVATION_VERDICT,
        "matrix_id": str(matrix_id),
        "entry_role": "TRIAL_OBSERVATION",
        "observation_key_sha256": observation_key_sha256(key_material),
        "observation": {
            "status": "COMPUTED_UNPUBLISHED",
            "counts_toward_published_denominator": False,
            "counts_toward_observed_denominator": True,
            "rescore_forbidden": True,
            "identity_version_of_key": IDENTITY_VERSION_V2,
            "arm_id": resolved_arm,
            "observed_trial_key_sha256": v2_key,
            "arm_config_digest": arm_config_digest(identity, arm_id=resolved_arm),
            "publication_stage_documented": str(publication_stage),
            "publication_reasons": [str(r) for r in publication_reasons],
            "scored_metrics_digest": str(scored_metrics_digest),
        },
        "provenance": dict(sorted((provenance or {}))),
        "producer_role": str(producer_role),
    }


def observation_rows(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Ledger rows that are trial observations (schema-tagged, kind-less)."""
    return [
        row
        for row in rows
        if row.get("schema") == TRIAL_OBSERVATION_SCHEMA_VERSION
        and row.get("entry_role") == "TRIAL_OBSERVATION"
    ]


def denominator_split(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Honest denominator view over ledger rows.

    ``published`` counts ``CELL_RESULT`` rows only; ``observed_unpublished``
    counts DISTINCT observation keys; ``observed_total`` is the scientific
    scored denominator (published + observed-unpublished).

    Supersede rule (no double counting): an observation whose
    ``observation.observed_trial_key_sha256`` equals the
    ``trial_key_sha256`` of an already-published row no longer counts toward
    ``observed_unpublished`` -- the trial moved from observed-unpublished to
    published, so it is counted exactly once overall.  Historical rows are
    unaffected (the M01 amendment is provenance-keyed and never matches a
    published trial key).
    """
    from research.adapter_v10.publish import published_cell_rows

    published_rows = published_cell_rows(rows)
    published_keys = {row.get("trial_key_sha256") for row in published_rows}
    published_keys.discard(None)
    distinct_observed: set[Any] = set()
    for row in observation_rows(rows):
        observation = row.get("observation")
        observed_key = (
            observation.get("observed_trial_key_sha256")
            if isinstance(observation, Mapping)
            else None
        )
        if observed_key is not None and observed_key in published_keys:
            continue  # superseded: the observed trial later published
        distinct_observed.add(row.get("observation_key_sha256"))
    distinct_observed.discard(None)
    return {
        "published": len(published_rows),
        "observed_unpublished": len(distinct_observed),
        "observed_total": len(published_rows) + len(distinct_observed),
    }


# --------------------------------------------------------------------------- #
# M01 neighbour amendment (documented provenance; never re-scored)
# --------------------------------------------------------------------------- #
def load_m01_terminal(path: str | Path | None = None) -> dict[str, Any]:
    """Read the frozen M01 terminal artifact (read-only provenance source)."""
    target = Path(path) if path is not None else Path(M01_TERMINAL_ARTIFACT)
    with open(target, "r", encoding="utf-8") as handle:
        doc = json.load(handle)
    if not isinstance(doc, Mapping):
        raise ContractViolation("m01 terminal artifact is not a JSON object")
    return dict(doc)


def _file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def m01_neighbour_amendment_entry(
    *,
    terminal: Optional[Mapping[str, Any]] = None,
    terminal_path: str | Path | None = None,
    matrix_id: str = "v10r-m01-family",
    producer_role: str = "A2",
) -> dict[str, Any]:
    """Provenance-linked historical observation for the M01 neighbour arm.

    Preferred reconciliation option of PLAN section 7-A2: an explicit,
    append-only amendment ACCEPTED BY the ledger schema (kind-less row).  It
    carries the M01 neighbour values verbatim from
    ``family_terminal_m01.json``, is marked computed-unpublished and
    rescore-forbidden, and can never count toward the published denominator.
    The dedupe key is the provenance digest (terminal artifact sha256 + arm
    label), so re-running the reconciliation is a no-op.
    """
    doc = dict(terminal) if terminal is not None else load_m01_terminal(terminal_path)
    cells = doc.get("cells")
    if not isinstance(cells, Mapping):
        raise ContractViolation("m01 terminal artifact lacks a cells mapping")
    cell = cells.get("neighbour")
    if not isinstance(cell, Mapping):
        raise ContractViolation("m01 terminal artifact lacks the neighbour cell")

    # The on-disk artifact bytes win whenever a path is available; only an
    # in-memory terminal without a path falls back to its declared digest.
    if terminal_path is not None:
        artifact_sha = _file_sha256(Path(terminal_path))
    elif terminal is None:
        artifact_sha = _file_sha256(Path(M01_TERMINAL_ARTIFACT))
    else:
        artifact_sha = str(doc.get("artifact_sha256") or "")

    missing_metrics = [name for name in M01_NEIGHBOUR_FROZEN_METRICS if name not in cell]
    if missing_metrics:
        raise ContractViolation(
            "m01 neighbour cell lacks frozen metric fields: "
            f"{sorted(missing_metrics)}; reconciliation refuses to invent values"
        )
    metrics = {
        name: float(cell[name]) for name in sorted(M01_NEIGHBOUR_FROZEN_METRICS)
    }
    if metrics != dict(M01_NEIGHBOUR_FROZEN_METRICS):
        raise ContractViolation(
            "m01 neighbour metrics drifted from the frozen documented values; "
            "reconciliation refuses to re-score or rewrite history"
        )

    key_material = {
        "schema": TRIAL_OBSERVATION_SCHEMA_VERSION,
        "family_id": M01_FAMILY_ID,
        "arm_id": M01_NEIGHBOUR_ARM_ID,
        "artifact": M01_TERMINAL_ARTIFACT,
        "artifact_sha256": artifact_sha,
        "amendment": "computed_unpublished_observation",
    }
    observation_key = observation_key_sha256(key_material)
    return {
        "schema": TRIAL_OBSERVATION_SCHEMA_VERSION,
        "experiment_id": f"{matrix_id}-obs-{observation_key[:16]}",
        "verdict": OBSERVATION_VERDICT,
        "matrix_id": str(matrix_id),
        "entry_role": "TRIAL_OBSERVATION",
        "observation_key_sha256": observation_key,
        "observation": {
            "status": str(cell.get("status", "COMPUTED_UNPUBLISHED_CONTRACT_GAP")),
            "counts_toward_published_denominator": False,
            "counts_toward_observed_denominator": True,
            "rescore_forbidden": True,
            "computed_unpublished": True,
            "identity_version_of_key": "v2-retrofitted-provenance",
            "arm_id": M01_NEIGHBOUR_ARM_ID,
            "family_id": M01_FAMILY_ID,
            "frozen_metrics": metrics,
            "publish_stage_documented": str(cell.get("publish_stage", "")),
            "root_cause": str(cell.get("root_cause", "")),
        },
        "provenance": {
            "artifact": M01_TERMINAL_ARTIFACT,
            "artifact_sha256": artifact_sha,
            "original_producer_role": str(doc.get("producer_role", "")),
            "original_at_utc": str(doc.get("at_utc", "")),
            "original_w3": str(doc.get("w3", "")),
            "family_id": str(doc.get("family_id", M01_FAMILY_ID)),
            "verdict": str(doc.get("verdict", "")),
        },
        "producer_role": str(producer_role),
    }


__all__ = [
    "ARM_CONFIG_DIGEST_SCHEMA",
    "IDENTITY_VERSION_V2",
    "M01_FROZEN_OBSERVED_DENOMINATOR",
    "M01_FROZEN_PUBLISHED_DENOMINATOR",
    "M01_NEIGHBOUR_ARM_ID",
    "M01_TERMINAL_ARTIFACT",
    "OBSERVATION_VERDICT",
    "TRIAL_OBSERVATION_SCHEMA_VERSION",
    "TRIAL_PUBLICATION_SCHEMA_VERSION_V1",
    "TRIAL_PUBLICATION_SCHEMA_VERSION_V2",
    "V1_PAYLOAD_KEYS",
    "arm_config_digest",
    "canonical_arm_payload",
    "canonical_scored_payload_v2",
    "denominator_split",
    "legacy_v1_key",
    "legacy_v1_payload",
    "load_m01_terminal",
    "m01_neighbour_amendment_entry",
    "observation_key_sha256",
    "observation_rows",
    "resolve_arm_id",
    "trial_key_v2",
    "unpublished_trial_observation_entry",
]
