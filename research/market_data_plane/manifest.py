"""Raw chunk manifest build/verify for MDP-V1 (lane A3).

Implements the frozen ``mdp.raw_chunk_manifest@1`` schema from
``research/control/market_data_plane_v1_run/architecture_freeze.json``
(sha256 7f7403e67bfb9707b547b6762cc0a3c87f2c96f701b3f1ec3ad2197478736c02):

- exact 33-field manifest list (``schemas.manifest_fields``);
- ``manifest_id = sha256(canonical_json(manifest minus manifest_id))``
  (``schemas.manifest_rules``);
- type / min-max / count / length consistency validation;
- ``completeness_status in {COMPLETE, GAPS_PRESENT}`` with ``gap_reasons``
  drawn from the frozen ``reason_codes@1`` registry;
- prev/next linkage checks;
- mandatory entitlement fields
  (``entitlement_evidence_ref``, ``allowed_use_classification in
  {RESEARCH_AUTHORIZED, RESEARCH_CONDITIONAL, NOT_AUTHORIZED}``);
- secrets-removed request identity: the validator rejects any key under
  ``request_identity_secrets_removed`` matching a denylist pattern
  (password / token / api_key / secret / credential family) -- fail closed.

Pure data layer: no filesystem IO. Atomic publication of manifest files is
owned by ``archive.py`` (the frozen write_sequence owner). stdlib only.

Local frozen copies duplicated from the freeze (A1 reconciles with A2's
``models.py``/``reason_codes.py`` at integration; A2's module does not exist
in this parallel lane's worktree and must not be imported here).
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence

from ._canonical import canonical_json

__all__ = [
    "MANIFEST_SCHEMA_VERSION",
    "MANIFEST_FIELDS",
    "ALLOWED_USE_CLASSIFICATIONS",
    "COMPLETENESS_STATUSES",
    "SEQUENCE_SEMANTICS",
    "REASON_CODES",
    "ManifestValidationError",
    "is_hex64",
    "sha256_hex",
    "compute_manifest_id",
    "build_manifest",
    "validate_manifest",
    "verify_manifest_chain",
    "canonical_manifest_bytes",
]

MANIFEST_SCHEMA_VERSION = "mdp.raw_chunk_manifest@1"

# Freeze schemas.manifest_fields (exact 33-field list, local frozen copy).
MANIFEST_FIELDS: List[str] = [
    "schema_version",
    "manifest_id",
    "source_id",
    "provider_id",
    "venue",
    "instrument_id",
    "asset_class",
    "event_class",
    "request_identity_secrets_removed",
    "entitlement_evidence_ref",
    "allowed_use_classification",
    "retrieval_start_utc_ns",
    "retrieval_end_utc_ns",
    "payload_byte_length",
    "record_count",
    "payload_sha256",
    "media_type",
    "encoding",
    "min_exchange_time_utc_ns",
    "max_exchange_time_utc_ns",
    "min_receive_time_utc_ns",
    "max_receive_time_utc_ns",
    "min_available_time_utc_ns",
    "max_available_time_utc_ns",
    "parser_version",
    "normalizer_version",
    "prev_manifest_id",
    "next_manifest_id",
    "completeness_status",
    "gap_reasons",
    "sequence_semantics",
    "ordered_delivery",
    "created_utc",
]

ALLOWED_USE_CLASSIFICATIONS = ("RESEARCH_AUTHORIZED", "RESEARCH_CONDITIONAL", "NOT_AUTHORIZED")
COMPLETENESS_STATUSES = ("COMPLETE", "GAPS_PRESENT")

# The freeze references sequence_semantics values CONTIGUOUS and NONE only
# (reason_codes@1.semantics.SEQUENCE_GAP / field_rules.sequence_number).
# The closed set below is A3's reading; A1 ratifies at integration.
SEQUENCE_SEMANTICS = ("CONTIGUOUS", "NONE")

# Freeze reason_codes@1.codes (local frozen copy; A2's reason_codes.py does
# not exist in this worktree). A1 reconciles at integration.
REASON_CODES = (
    "MALFORMED_SHAPE",
    "MISSING_REQUIRED_FIELD",
    "UNKNOWN_EVENT_TYPE",
    "TIMEZONE_NAIVE_REJECTED",
    "NON_FINITE_PRICE",
    "PRECISION_LOSS",
    "NEGATIVE_PRICE",
    "NEGATIVE_SIZE",
    "CROSSED_QUOTE",
    "STALE_QUOTE",
    "IMPOSSIBLE_TIME_ORDER",
    "OUT_OF_ORDER_DELIVERY",
    "SEQUENCE_GAP",
    "SEQUENCE_RESET",
    "DUPLICATE_EVENT",
    "SOURCE_RESET_UNEVIDENCED",
    "UNKNOWN_INSTRUMENT",
    "MANIFEST_MISMATCH",
    "STATISTICAL_ANOMALY",
    "QUARANTINE_ORPHAN",
    "HASH_DISAGREEMENT",
)

# Small denylist for keys of request_identity_secrets_removed. A key matching
# this pattern means the caller tried to persist a credential-bearing field:
# the manifest validator fails closed (archive_protocol: never guess clean).
_SECRET_KEY_PATTERN = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|authorization|credential|private[_-]?key)",
    re.IGNORECASE,
)

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


def is_hex64(value: Any) -> bool:
    """True iff ``value`` is a str matching the frozen content-ID grammar.

    The grammar ``^[0-9a-f]{64}$`` (exactly 64 lowercase hex chars) is the
    V2 (finding F2) contract for caller-supplied content-ID path arguments
    (chunk sha256 and manifest_id). Empty, short, 63/65-length, overlong,
    uppercase, non-hex, traversal/separator/absolute, trailing-newline and
    non-string (pathlike/bytes) inputs all fail; the archive path builders
    reject them fail-closed before any filesystem access. Implemented with
    ``re.fullmatch`` because ``$`` would also accept a trailing newline.
    """
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))


class ManifestValidationError(ValueError):
    """A manifest violates the frozen mdp.raw_chunk_manifest@1 contract.

    ``code`` is drawn from reason_codes@1 where a code applies
    (HASH_DISAGREEMENT for manifest_id disagreement, MANIFEST_MISMATCH
    otherwise); secret-key findings use code "SECRET_KEY_REJECTED" (not in
    the registry -- registry codes classify event quality, not manifest
    hygiene) and are always surfaced, never stripped silently.
    """

    def __init__(self, message: str, code: str = "MANIFEST_MISMATCH") -> None:
        super().__init__(message)
        self.code = code


def sha256_hex(data: bytes) -> str:
    """Lowercase hex sha256 of bytes."""
    return hashlib.sha256(data).hexdigest()


def canonical_manifest_bytes(manifest: Mapping[str, Any]) -> bytes:
    """Exact bytes a manifest file persists: canonical_json + newline."""
    return (canonical_json(dict(manifest)) + "\n").encode("utf-8")


def compute_manifest_id(manifest: Mapping[str, Any]) -> str:
    """manifest_id = sha256(canonical_json(manifest minus manifest_id field))."""
    material = {k: v for k, v in manifest.items() if k != "manifest_id"}
    return sha256_hex(canonical_json(material).encode("utf-8"))


def build_manifest(
    payload_sha256: str,
    payload_byte_length: int,
    record_count: int,
    *,
    source_id: str,
    provider_id: str,
    venue: str,
    instrument_id: str,
    asset_class: str,
    event_class: str,
    request_identity_secrets_removed: Optional[Mapping[str, Any]] = None,
    entitlement_evidence_ref: str = "",
    allowed_use_classification: str = "RESEARCH_AUTHORIZED",
    retrieval_start_utc_ns: Optional[int] = None,
    retrieval_end_utc_ns: Optional[int] = None,
    media_type: str = "application/x-ndjson",
    encoding: str = "utf-8",
    time_bounds: Optional[Mapping[str, Any]] = None,
    parser_version: str = "",
    normalizer_version: str = "",
    prev_manifest_id: Optional[str] = None,
    next_manifest_id: Optional[str] = None,
    completeness_status: str = "COMPLETE",
    gap_reasons: Optional[Sequence[str]] = None,
    sequence_semantics: str = "CONTIGUOUS",
    ordered_delivery: bool = False,
    created_utc: Any = None,
) -> Dict[str, Any]:
    """Build a complete manifest dict and stamp its frozen manifest_id.

    ``time_bounds`` carries the six optional min/max time fields
    (keys ``min/max_exchange_time_utc_ns``, ``..._receive_...``,
    ``..._available_...``); values may be None for an empty chunk.
    ``created_utc`` has no unit in the freeze (sibling fields use
    ``_utc_ns``); when omitted it defaults to ``time.time_ns()``. A1 to
    ratify the created_utc type (int ns assumed) at integration.
    """
    import time

    manifest: Dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "manifest_id": "",  # stamped below, after canonical material is final
        "source_id": source_id,
        "provider_id": provider_id,
        "venue": venue,
        "instrument_id": instrument_id,
        "asset_class": asset_class,
        "event_class": event_class,
        "request_identity_secrets_removed": dict(request_identity_secrets_removed or {}),
        "entitlement_evidence_ref": entitlement_evidence_ref,
        "allowed_use_classification": allowed_use_classification,
        "retrieval_start_utc_ns": retrieval_start_utc_ns,
        "retrieval_end_utc_ns": retrieval_end_utc_ns,
        "payload_byte_length": payload_byte_length,
        "record_count": record_count,
        "payload_sha256": payload_sha256,
        "media_type": media_type,
        "encoding": encoding,
        "min_exchange_time_utc_ns": None,
        "max_exchange_time_utc_ns": None,
        "min_receive_time_utc_ns": None,
        "max_receive_time_utc_ns": None,
        "min_available_time_utc_ns": None,
        "max_available_time_utc_ns": None,
        "parser_version": parser_version,
        "normalizer_version": normalizer_version,
        "prev_manifest_id": prev_manifest_id,
        "next_manifest_id": next_manifest_id,
        "completeness_status": completeness_status,
        "gap_reasons": list(gap_reasons or []),
        "sequence_semantics": sequence_semantics,
        "ordered_delivery": ordered_delivery,
        "created_utc": time.time_ns() if created_utc is None else created_utc,
    }
    if time_bounds:
        for key in (
            "min_exchange_time_utc_ns",
            "max_exchange_time_utc_ns",
            "min_receive_time_utc_ns",
            "max_receive_time_utc_ns",
            "min_available_time_utc_ns",
            "max_available_time_utc_ns",
        ):
            if key in time_bounds:
                manifest[key] = time_bounds[key]
    manifest["manifest_id"] = compute_manifest_id(manifest)
    return manifest


def _require_int(manifest: Mapping[str, Any], key: str, errors: List[str]) -> None:
    value = manifest[key]
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{key} must be int, got {type(value).__name__}")


def _require_optional_int(manifest: Mapping[str, Any], key: str, errors: List[str]) -> None:
    value = manifest[key]
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{key} must be int or null, got {type(value).__name__}")


def _require_nonempty_str(manifest: Mapping[str, Any], key: str, errors: List[str]) -> None:
    value = manifest[key]
    if not isinstance(value, str) or not value:
        errors.append(f"{key} must be a non-empty string")


def _require_hex64(manifest: Mapping[str, Any], key: str, errors: List[str]) -> None:
    value = manifest[key]
    if not isinstance(value, str) or not _HEX64_RE.match(value):
        errors.append(f"{key} must be 64-char lowercase hex sha256")


def _require_optional_hex64(manifest: Mapping[str, Any], key: str, errors: List[str]) -> None:
    value = manifest[key]
    if value is None:
        return
    if not isinstance(value, str) or not _HEX64_RE.match(value):
        errors.append(f"{key} must be null or 64-char lowercase hex sha256")


def _reject_secret_keys(node: Any, path: str, errors: List[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            key_str = key if isinstance(key, str) else str(key)
            here = f"{path}.{key_str}"
            if _SECRET_KEY_PATTERN.search(key_str):
                errors.append(f"secret-denylist key under {here} (fail closed)")
            _reject_secret_keys(value, here, errors)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _reject_secret_keys(item, f"{path}[{index}]", errors)


def validate_manifest(manifest: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate a manifest against the frozen schema; return it as a dict.

    Raises ManifestValidationError (aggregated findings) on any violation.
    Checks: exact frozen field set, schema version, types, min<=max pairs,
    retrieval window order, count/length ranges, payload sha shape, enum
    membership, gap_reasons <-> completeness consistency, entitlement field
    presence and classification enum, sequence_semantics enum, ordered_delivery
    strict bool, secret-denylist scan of request_identity_secrets_removed, and
    manifest_id == sha256(canonical_json(manifest minus manifest_id))
    (HASH_DISAGREEMENT on mismatch).
    """
    errors: List[str] = []
    expected = set(MANIFEST_FIELDS)
    actual = set(manifest.keys())
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append(f"missing fields: {missing}")
    if extra:
        errors.append(f"unexpected fields: {extra}")

    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        errors.append(f"schema_version must be {MANIFEST_SCHEMA_VERSION!r}")

    if "manifest_id" in manifest:
        _require_hex64(manifest, "manifest_id", errors)
    for key in ("source_id", "provider_id", "venue", "instrument_id", "asset_class", "event_class"):
        if key in manifest:
            _require_nonempty_str(manifest, key, errors)
    for key in ("payload_sha256",):
        if key in manifest:
            _require_hex64(manifest, key, errors)
    for key in ("prev_manifest_id", "next_manifest_id"):
        if key in manifest:
            _require_optional_hex64(manifest, key, errors)
    for key in ("media_type", "encoding", "parser_version", "normalizer_version"):
        if key in manifest:
            _require_nonempty_str(manifest, key, errors)
    for key in ("payload_byte_length", "record_count"):
        if key in manifest:
            _require_int(manifest, key, errors)
            value = manifest[key]
            if not isinstance(value, bool) and isinstance(value, int) and value < 0:
                errors.append(f"{key} must be >= 0")
    for key in ("retrieval_start_utc_ns", "retrieval_end_utc_ns"):
        if key in manifest:
            _require_optional_int(manifest, key, errors)
    for key in (
        "min_exchange_time_utc_ns",
        "max_exchange_time_utc_ns",
        "min_receive_time_utc_ns",
        "max_receive_time_utc_ns",
        "min_available_time_utc_ns",
        "max_available_time_utc_ns",
    ):
        if key in manifest:
            _require_optional_int(manifest, key, errors)

    if manifest.get("entitlement_evidence_ref") is not None:
        _require_nonempty_str(manifest, "entitlement_evidence_ref", errors)
    else:
        errors.append("entitlement_evidence_ref must be present (non-empty string)")
    if manifest.get("allowed_use_classification") not in ALLOWED_USE_CLASSIFICATIONS:
        errors.append(
            f"allowed_use_classification must be one of {list(ALLOWED_USE_CLASSIFICATIONS)}"
        )

    identity = manifest.get("request_identity_secrets_removed")
    if not isinstance(identity, dict):
        errors.append("request_identity_secrets_removed must be a dict (secrets removed)")
    else:
        _reject_secret_keys(identity, "request_identity_secrets_removed", errors)

    start = manifest.get("retrieval_start_utc_ns")
    end = manifest.get("retrieval_end_utc_ns")
    if (
        isinstance(start, int)
        and not isinstance(start, bool)
        and isinstance(end, int)
        and not isinstance(end, bool)
        and start > end
    ):
        errors.append("retrieval_start_utc_ns must be <= retrieval_end_utc_ns")

    for low_key, high_key in (
        ("min_exchange_time_utc_ns", "max_exchange_time_utc_ns"),
        ("min_receive_time_utc_ns", "max_receive_time_utc_ns"),
        ("min_available_time_utc_ns", "max_available_time_utc_ns"),
    ):
        low = manifest.get(low_key)
        high = manifest.get(high_key)
        if (
            isinstance(low, int)
            and not isinstance(low, bool)
            and isinstance(high, int)
            and not isinstance(high, bool)
            and low > high
        ):
            errors.append(f"{low_key} must be <= {high_key}")

    completeness = manifest.get("completeness_status")
    if completeness not in COMPLETENESS_STATUSES:
        errors.append(f"completeness_status must be one of {list(COMPLETENESS_STATUSES)}")
    gap_reasons = manifest.get("gap_reasons")
    if not isinstance(gap_reasons, list) or any(not isinstance(c, str) for c in gap_reasons):
        errors.append("gap_reasons must be a list of strings")
    else:
        unknown = [code for code in gap_reasons if code not in REASON_CODES]
        if unknown:
            errors.append(f"gap_reasons contains codes outside reason_codes@1: {unknown}")
        if sorted(set(gap_reasons)) != sorted(gap_reasons):
            errors.append("gap_reasons must be sorted and unique")
        if completeness == "COMPLETE" and gap_reasons:
            errors.append("completeness_status COMPLETE requires empty gap_reasons")
        if completeness == "GAPS_PRESENT" and not gap_reasons:
            errors.append("completeness_status GAPS_PRESENT requires non-empty gap_reasons")

    if manifest.get("sequence_semantics") not in SEQUENCE_SEMANTICS:
        errors.append(f"sequence_semantics must be one of {list(SEQUENCE_SEMANTICS)}")
    if not isinstance(manifest.get("ordered_delivery"), bool):
        errors.append("ordered_delivery must be a strict bool")

    created = manifest.get("created_utc")
    if not isinstance(created, (int, str)) or isinstance(created, bool) or (
        isinstance(created, str) and not created
    ):
        errors.append("created_utc must be a non-empty string or int (ns assumed)")

    if errors:
        raise ManifestValidationError("; ".join(errors))

    computed = compute_manifest_id(manifest)
    if manifest["manifest_id"] != computed:
        raise ManifestValidationError(
            f"manifest_id mismatch: stored {manifest['manifest_id']!r} != computed {computed!r}",
            code="HASH_DISAGREEMENT",
        )
    return dict(manifest)


def verify_manifest_chain(manifests: Sequence[Mapping[str, Any]]) -> List[str]:
    """Check prev/next linkage across an ordered manifest sequence.

    For every adjacent pair (a, b): ``a.next_manifest_id`` must equal
    ``b.manifest_id`` and ``b.prev_manifest_id`` must equal ``a.manifest_id``
    whenever those links are non-null. Nullable linkage is legal
    (manifest_rules: "prev/next linkage nullable"); a disagreement between a
    declared link and the actual neighbor is a visible chain break.

    Returns the list of manifest ids in chain order. Raises
    ManifestValidationError with code MANIFEST_MISMATCH on any break.
    """
    ids = [m["manifest_id"] for m in manifests]
    if len(set(ids)) != len(ids):
        raise ManifestValidationError("chain contains duplicate manifest ids", code="MANIFEST_MISMATCH")
    for index in range(len(manifests) - 1):
        a, b = manifests[index], manifests[index + 1]
        a_next = a.get("next_manifest_id")
        b_prev = b.get("prev_manifest_id")
        if a_next is not None and a_next != b["manifest_id"]:
            raise ManifestValidationError(
                f"chain break at {index}: {a['manifest_id']}.next={a_next!r} != {b['manifest_id']!r}",
                code="MANIFEST_MISMATCH",
            )
        if b_prev is not None and b_prev != a["manifest_id"]:
            raise ManifestValidationError(
                f"chain break at {index + 1}: {b['manifest_id']}.prev={b_prev!r} != {a['manifest_id']!r}",
                code="MANIFEST_MISMATCH",
            )
    return ids
