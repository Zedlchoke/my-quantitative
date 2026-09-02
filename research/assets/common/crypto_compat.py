"""Migration adapter: historical crypto manifests -> asset-neutral contract.

(owner: A2, PLAN_stocks.md section 6)

This module READS :mod:`research.protocol.manifest` and
``contracts.protocol`` (A1-owned, historical crypto).  It never patches,
wraps-at-runtime or rewrites them: the adapter only converts a manifest
produced by :func:`research.protocol.manifest.build_manifest` /
:func:`write_manifest` into an :class:`AssetExperimentContract`, proving old
manifests parse identically.  Every historical value is preserved verbatim;
the only synthesized values are the asset-class namespace (``CRYPTO_PERP``),
a deterministic cost-model id composed FROM the historical fee/slippage/
funding strings, and digests computed from historical values.

No default venue and no default calendar exist here: the caller must supply
the real ``venue`` and ``calendar_id`` for the historical experiment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import yaml
from contracts.protocol import ManifestSpec

from research.assets.common.contracts import (
    CRYPTO_PERP,
    AssetExperimentContract,
    canonical_json,
    require_asset_class,
    require_token,
    sha256_text,
)
from research.protocol.manifest import build_manifest

CRYPTO_PERP_ASSET_CLASS = CRYPTO_PERP

COMPAT_SCHEMA_VERSION = 1

_COST_MODEL_PREFIX = "CRYPTO_COMPAT"


# --- normalization (object OR persisted dict payload) ----------------------- #
def _normalize_payload(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a persisted payload exactly like ``read_manifest`` does."""
    allowed = set(ManifestSpec.REQUIRED_FIELDS) | {"random_seed_reason"}
    unknown = sorted(set(manifest) - allowed)
    if unknown:
        raise ValueError(f"manifest has unknown fields: {unknown}")
    missing = sorted(
        name
        for name in ManifestSpec.REQUIRED_FIELDS
        if manifest.get(name) is None and name not in ManifestSpec.NULLABLE_FIELDS
    )
    if missing:
        raise ValueError(f"manifest_missing_field: {missing}")
    seed_reason = manifest.get("random_seed_reason")
    if manifest.get("random_seed") is None:
        if seed_reason != "seed_unavailable":
            raise ValueError("null random_seed requires random_seed_reason=seed_unavailable")
    elif seed_reason is not None:
        raise ValueError("random_seed_reason only allowed when random_seed is null")
    return {
        name: manifest[name] for name in ManifestSpec.REQUIRED_FIELDS
    }


def normalize_legacy_manifest(
    manifest: ManifestSpec | Mapping[str, Any],
) -> ManifestSpec:
    """Accept a ``ManifestSpec`` or its persisted dict/YAML payload.

    Rebuilds through :func:`research.protocol.manifest.build_manifest`, so a
    payload that would not pass historical validation is rejected here too.
    """
    if isinstance(manifest, ManifestSpec):
        return manifest
    if isinstance(manifest, Mapping):
        return build_manifest(**_normalize_payload(manifest))
    raise TypeError(
        f"manifest must be ManifestSpec or mapping, got {type(manifest).__name__}"
    )


def legacy_payload(manifest: ManifestSpec | Mapping[str, Any]) -> dict[str, Any]:
    """Exact persisted payload of a historical manifest (seed-reason aware).

    Byte-for-byte the key set that ``research.protocol.manifest.write_manifest``
    would dump to YAML for this manifest.
    """
    spec = normalize_legacy_manifest(manifest)
    payload: dict[str, Any] = spec.to_dict()
    if spec.random_seed is None:
        payload["random_seed_reason"] = "seed_unavailable"
    return payload


def yaml_bytes(manifest: ManifestSpec | Mapping[str, Any]) -> str:
    """The exact YAML bytes ``write_manifest`` produces for this manifest."""
    payload = legacy_payload(manifest)
    return yaml.safe_dump(payload, sort_keys=False, default_flow_style=False)


# --- derived identifiers ----------------------------------------------------- #
def derive_cost_model_id(manifest: ManifestSpec | Mapping[str, Any]) -> str:
    """Deterministic cost-model id composed FROM historical cost strings.

    The historical ``fee_model`` / ``slippage_model`` / ``funding_mode``
    values are embedded verbatim, so no cost semantics are invented and two
    manifests with different historical cost configs can never share a
    cost-model id.
    """
    spec = normalize_legacy_manifest(manifest)
    components = (spec.fee_model, spec.slippage_model, spec.funding_mode)
    for index, component in enumerate(components):
        if not isinstance(component, str) or not component.strip():
            raise ValueError(f"cost component {index} must be a non-empty string")
        if "::" in component:
            raise ValueError(f"cost component {index} contains the separator '::'")
    return f"{_COST_MODEL_PREFIX}::" + "::".join(components)


def historical_arm_fields(manifest: ManifestSpec | Mapping[str, Any]) -> dict[str, str]:
    """Map historical identity fields onto family/arm/config-digest fields.

    ``hypothesis_id`` -> ``family_id``; ``strategy_type`` + ``candidate_version``
    -> ``arm_id``; ``config_sha256`` -> ``arm_config_digest``.  Values are the
    historical ones, never new inventions.
    """
    spec = normalize_legacy_manifest(manifest)
    return {
        "family_id": spec.hypothesis_id,
        "arm_id": f"{spec.strategy_type}@v{spec.candidate_version}",
        "arm_config_digest": spec.config_sha256,
    }


# --- the adapter -------------------------------------------------------------- #
@dataclass(frozen=True)
class CryptoCompatResult:
    """Adapter result: the new contract PLUS the untouched legacy manifest."""

    contract: AssetExperimentContract
    legacy_manifest: ManifestSpec
    legacy_payload: Mapping[str, Any]


def to_asset_contract(
    manifest: ManifestSpec | Mapping[str, Any],
    *,
    venue: str,
    calendar_id: str,
    asset_class: str = CRYPTO_PERP_ASSET_CLASS,
) -> CryptoCompatResult:
    """Yield the asset-neutral contract for a historical crypto manifest.

    ``venue`` and ``calendar_id`` are keyword-only and REQUIRED (there is no
    historical field to derive them from and none may be defaulted).
    ``asset_class`` defaults to the historical crypto value ``CRYPTO_PERP``.

    Raises ``ValueError`` when the manifest fails the very same historical
    validation enforced by :func:`research.protocol.manifest.build_manifest`,
    i.e. the adapter proves old manifests parse identically by construction.
    """
    spec = normalize_legacy_manifest(manifest)
    require_token(venue, "venue")
    require_token(calendar_id, "calendar_id")
    require_asset_class(asset_class)
    payload = legacy_payload(spec)
    arm = historical_arm_fields(spec)
    contract = AssetExperimentContract(
        schema_version=COMPAT_SCHEMA_VERSION,
        experiment_id=spec.experiment_id,
        asset_class=asset_class,
        venue=venue,
        calendar_id=calendar_id,
        cost_model_id=derive_cost_model_id(spec),
        universe_digest=sha256_text(spec.universe_snapshot),
        family_id=arm["family_id"],
        arm_id=arm["arm_id"],
        arm_config_digest=arm["arm_config_digest"],
        window_digest=sha256_text(
            f"{spec.actual_start_utc}..{spec.actual_end_utc}|{spec.common_intersection}"
        ),
        split_policy_digest=sha256_text(spec.split_policy),
        provider_id=None,
        provider_schema_digest=sha256_text(spec.data_manifest_sha256),
    )
    return CryptoCompatResult(
        contract=contract,
        legacy_manifest=spec,
        legacy_payload=payload,
    )


def verify_roundtrip(
    result: CryptoCompatResult,
    original: ManifestSpec | Mapping[str, Any],
) -> list[str]:
    """Compatibility problems list (empty = old manifest parsed identically).

    Checks that (1) the preserved payload normalizes back to a ManifestSpec
    equal to the original object, (2) the YAML bytes the adapter would write
    equal the bytes ``write_manifest`` produces for the original, and
    (3) the contract's canonical JSON is stable under re-serialization.
    """
    problems: list[str] = []
    original_spec = normalize_legacy_manifest(original)
    if result.legacy_manifest != original_spec:
        problems.append("legacy_manifest_differs_from_original")
    rebuilt = normalize_legacy_manifest(result.legacy_payload)
    if rebuilt != original_spec:
        problems.append("payload_does_not_roundtrip_to_original")
    if yaml_bytes(result.legacy_payload) != yaml_bytes(original_spec):
        problems.append("yaml_bytes_differ")
    if (
        result.contract.canonical_json()
        != canonical_json(result.contract.canonical_payload())
    ):
        problems.append("contract_canonical_json_not_stable")
    return problems
