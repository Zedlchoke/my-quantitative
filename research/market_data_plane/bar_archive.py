"""mdp.bar_chunk_manifest@2 + content-addressed bar chunk store (lane A4).

Freeze authority: research/control/market_data_plane_v2_run/architecture_freeze_v2.json
(p3_wave_sha 09a223f6ce166e219beb67b25b8151361979ca21), section
"bar_contract".extensions ("archive.put_bar_records + bar manifest builder
(mdp.bar_chunk_manifest@2 with bar-class statistics)").

The bar manifest keeps the EXACT 33-field skeleton of
``mdp.raw_chunk_manifest@1`` (same identity/entitlement/payload/linkage/
completeness fields, same ``manifest_id = sha256(canonical_json(manifest
minus manifest_id))`` rule) with ``event_class="BAR"`` and BAR-CLASS time
bounds: the six min/max timestamp slots carry
``min/max_{open,close,available}_time_utc_ns`` (bars have no receive-time
evidence; open/close/available are the bar-class clocks).

Content IDs are FROZEN strict 64-hex (F2 grammar
``^[0-9a-f]{64}$``): every path-affecting id is pre-validated HERE before it
reaches the shared helpers, so this module fails closed regardless of which
hardened helper generation is installed.  The confined store helpers are
imported from archive.py (``chunk_path``/``manifest_path``/
``atomic_write_bytes``/``sha256_hex`` — frozen at the P3 wave SHA; F2 owns
their hardening, never this lane).

Write sequence is the frozen archive protocol, unchanged for bars: chunk
bytes committed + verified first (content-addressed, immutable, re-put of
identical bytes a no-op, different bytes HashDisagreement), manifest
published only afterwards by the same temp+fsync+replace protocol with a
re-read validation and a filename/body binding check.  A manifest
publication failure leaves the chunk as a diagnosable orphan and propagates.

stdlib + sibling modules only; never mutates its inputs.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from . import bars as _bars
from . import models as _models
from . import reason_codes as _rc
from .archive import (
    ArchiveError,
    HashDisagreement,
    atomic_write_bytes,
    chunk_path,
    manifest_path,
    scan_payload,
    sha256_hex,
    write_chunk,
)
from .manifest import (
    ALLOWED_USE_CLASSIFICATIONS,
    COMPLETENESS_STATUSES,
    ManifestValidationError,
    SEQUENCE_SEMANTICS,
)

__all__ = [
    "BAR_MANIFEST_SCHEMA_VERSION",
    "BAR_MANIFEST_FIELDS",
    "BAR_TIME_BOUND_FIELDS",
    "BarManifestValidationError",
    "compute_bar_manifest_id",
    "build_bar_manifest",
    "validate_bar_manifest",
    "bar_time_bounds",
    "bar_chunk_payload_bytes",
    "put_bar_records",
    "publish_bar_manifest",
    "load_bar_manifest",
    "load_bar_records",
    "verify_bar_chunk",
]

BAR_MANIFEST_SCHEMA_VERSION = "mdp.bar_chunk_manifest@2"

#: Exact 33-field skeleton of mdp.raw_chunk_manifest@1 with BAR-class time
#: bounds (min/max over open/close/available bar clocks).
BAR_MANIFEST_FIELDS: tuple[str, ...] = (
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
    "min_open_time_utc_ns",
    "max_open_time_utc_ns",
    "min_close_time_utc_ns",
    "max_close_time_utc_ns",
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
)

BAR_TIME_BOUND_FIELDS: tuple[str, ...] = (
    "min_open_time_utc_ns", "max_open_time_utc_ns",
    "min_close_time_utc_ns", "max_close_time_utc_ns",
    "min_available_time_utc_ns", "max_available_time_utc_ns",
)

_TIME_BOUND_PAIRS = (
    ("min_open_time_utc_ns", "max_open_time_utc_ns"),
    ("min_close_time_utc_ns", "max_close_time_utc_ns"),
    ("min_available_time_utc_ns", "max_available_time_utc_ns"),
)

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

#: Mirrored from manifest.py (private there; the bar manifest enforces the
#: same secrets-removed discipline without importing a private symbol).
_SECRET_KEY_PATTERN = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|authorization|credential|private[_-]?key)",
    re.IGNORECASE,
)


class BarManifestValidationError(ManifestValidationError):
    """A manifest violates the frozen mdp.bar_chunk_manifest@2 contract.

    Subclass of the @1 ManifestValidationError family with the same
    ``code`` convention (HASH_DISAGREEMENT for manifest_id disagreement,
    MANIFEST_MISMATCH otherwise).
    """


def _require_hex64(value: Any, field: str) -> None:
    if not isinstance(value, str) or not _HEX64_RE.match(value):
        raise ArchiveError(
            f"{field} must be strict 64-char lowercase hex (frozen F2 "
            f"grammar ^[0-9a-f]{{64}}$), got {value!r}")


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


# --- manifest build / validate ------------------------------------------------

def compute_bar_manifest_id(manifest: Mapping[str, Any]) -> str:
    """manifest_id = sha256(canonical_json(manifest minus manifest_id))."""
    material = {k: v for k, v in manifest.items() if k != "manifest_id"}
    return sha256_hex(_models.canonical_json(material).encode("utf-8"))


def bar_time_bounds(bars: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Six bar-class min/max time bounds from canonical bar dicts.

    Only genuine ints are collected (bools excluded); for an empty sequence
    every bound stays None (empty-chunk rule mirrors mdp.raw_chunk_manifest@1).
    """
    bounds: Dict[str, Any] = {}
    for stem in ("open", "close", "available"):
        values = [
            b[f"{stem}_time_utc_ns"] for b in bars
            if isinstance(b.get(f"{stem}_time_utc_ns"), int)
            and not isinstance(b.get(f"{stem}_time_utc_ns"), bool)
        ]
        bounds[f"min_{stem}_time_utc_ns"] = min(values) if values else None
        bounds[f"max_{stem}_time_utc_ns"] = max(values) if values else None
    return bounds


def bar_chunk_payload_bytes(bars: Sequence[Mapping[str, Any]]) -> bytes:
    """Frozen chunk framing: canonical_json + newline per bar."""
    return b"".join(
        (_models.canonical_json(bar) + "\n").encode("utf-8") for bar in bars)


def build_bar_manifest(
    payload_sha256: str,
    payload_byte_length: int,
    record_count: int,
    *,
    source_id: str,
    provider_id: str,
    venue: str,
    instrument_id: str,
    asset_class: str,
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
    """Build a validated mdp.bar_chunk_manifest@2 and stamp its manifest_id."""
    manifest: Dict[str, Any] = {
        "schema_version": BAR_MANIFEST_SCHEMA_VERSION,
        "manifest_id": "",  # stamped below, after canonical material is final
        "source_id": source_id,
        "provider_id": provider_id,
        "venue": venue,
        "instrument_id": instrument_id,
        "asset_class": asset_class,
        "event_class": "BAR",
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
        "min_open_time_utc_ns": None,
        "max_open_time_utc_ns": None,
        "min_close_time_utc_ns": None,
        "max_close_time_utc_ns": None,
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
        for key in BAR_TIME_BOUND_FIELDS:
            if key in time_bounds:
                manifest[key] = time_bounds[key]
    manifest["manifest_id"] = compute_bar_manifest_id(manifest)
    return validate_bar_manifest(manifest)


def _optional_int(manifest: Mapping[str, Any], key: str, errors: List[str]) -> None:
    value = manifest[key]
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{key} must be int or null, got {type(value).__name__}")


def _nonempty_str(manifest: Mapping[str, Any], key: str, errors: List[str]) -> None:
    value = manifest[key]
    if not isinstance(value, str) or not value:
        errors.append(f"{key} must be a non-empty string")


def _hex64(manifest: Mapping[str, Any], key: str, errors: List[str]) -> None:
    value = manifest[key]
    if not isinstance(value, str) or not _HEX64_RE.match(value):
        errors.append(f"{key} must be 64-char lowercase hex sha256")


def _optional_hex64(manifest: Mapping[str, Any], key: str, errors: List[str]) -> None:
    value = manifest[key]
    if value is None:
        return
    if not isinstance(value, str) or not _HEX64_RE.match(value):
        errors.append(f"{key} must be null or 64-char lowercase hex sha256")


def validate_bar_manifest(manifest, skip_id: bool = False) -> Dict[str, Any]:
    """Validate a mdp.bar_chunk_manifest@2; return the canonical dict copy.

    Mirrors the mdp.raw_chunk_manifest@1 validation rules over the bar-class
    skeleton: exact frozen field set, schema version, types, min<=max for the
    three bar time-bound pairs, retrieval window order, non-negative
    count/length, strict 64-hex payload sha, enum membership, sorted-unique
    gap_reasons drawn from reason_codes@1 + mdp.bar_reason_codes@2,
    COMPLETE<->gap_reasons consistency, entitlement field presence,
    secret-denylist scan of request_identity_secrets_removed, and (unless
    *skip_id*) manifest_id == sha256(canonical_json(minus manifest_id)).
    """
    if not isinstance(manifest, dict):
        raise BarManifestValidationError("manifest must be a dict")
    errors: List[str] = []
    expected = set(BAR_MANIFEST_FIELDS)
    actual = set(manifest.keys())
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append(f"missing fields: {missing}")
    if extra:
        errors.append(f"unexpected fields: {extra}")

    if manifest.get("schema_version") != BAR_MANIFEST_SCHEMA_VERSION:
        errors.append(f"schema_version must be {BAR_MANIFEST_SCHEMA_VERSION!r}")

    if "manifest_id" in manifest:
        _hex64(manifest, "manifest_id", errors)
    for key in ("source_id", "provider_id", "venue", "instrument_id",
                "asset_class", "event_class", "media_type", "encoding",
                "parser_version", "normalizer_version"):
        if key in manifest:
            _nonempty_str(manifest, key, errors)
    if manifest.get("event_class") not in (None, "BAR"):
        errors.append('event_class must be "BAR" for mdp.bar_chunk_manifest@2')
    if "payload_sha256" in manifest:
        _hex64(manifest, "payload_sha256", errors)
    for key in ("prev_manifest_id", "next_manifest_id"):
        if key in manifest:
            _optional_hex64(manifest, key, errors)

    if manifest.get("entitlement_evidence_ref") is not None:
        _nonempty_str(manifest, "entitlement_evidence_ref", errors)
    else:
        errors.append("entitlement_evidence_ref must be present (non-empty string)")
    if manifest.get("allowed_use_classification") not in ALLOWED_USE_CLASSIFICATIONS:
        errors.append(
            f"allowed_use_classification must be one of {list(ALLOWED_USE_CLASSIFICATIONS)}")

    identity = manifest.get("request_identity_secrets_removed")
    if not isinstance(identity, dict):
        errors.append("request_identity_secrets_removed must be a dict (secrets removed)")
    else:
        _reject_secret_keys(identity, "request_identity_secrets_removed", errors)

    for key in ("payload_byte_length", "record_count"):
        value = manifest.get(key)
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(f"{key} must be int, got {type(value).__name__}")
            elif value < 0:
                errors.append(f"{key} must be >= 0")
    for key in ("retrieval_start_utc_ns", "retrieval_end_utc_ns") + BAR_TIME_BOUND_FIELDS:
        if key in manifest:
            _optional_int(manifest, key, errors)

    start = manifest.get("retrieval_start_utc_ns")
    end = manifest.get("retrieval_end_utc_ns")
    if (isinstance(start, int) and not isinstance(start, bool)
            and isinstance(end, int) and not isinstance(end, bool) and start > end):
        errors.append("retrieval_start_utc_ns must be <= retrieval_end_utc_ns")
    for low_key, high_key in _TIME_BOUND_PAIRS:
        low, high = manifest.get(low_key), manifest.get(high_key)
        if (isinstance(low, int) and not isinstance(low, bool)
                and isinstance(high, int) and not isinstance(high, bool) and low > high):
            errors.append(f"{low_key} must be <= {high_key}")

    completeness = manifest.get("completeness_status")
    if completeness not in COMPLETENESS_STATUSES:
        errors.append(f"completeness_status must be one of {list(COMPLETENESS_STATUSES)}")
    gap_reasons = manifest.get("gap_reasons")
    if not isinstance(gap_reasons, list) or any(not isinstance(c, str) for c in gap_reasons):
        errors.append("gap_reasons must be a list of strings")
    else:
        known = _rc.CODES + _bars.BAR_REASON_CODES
        unknown = [code for code in gap_reasons if code not in known]
        if unknown:
            errors.append(
                "gap_reasons contains codes outside reason_codes@1 + "
                f"mdp.bar_reason_codes@2: {unknown}")
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
            isinstance(created, str) and not created):
        errors.append("created_utc must be a non-empty string or int (ns assumed)")

    if errors:
        raise BarManifestValidationError("; ".join(errors))

    if not skip_id:
        computed = compute_bar_manifest_id(manifest)
        if manifest["manifest_id"] != computed:
            raise BarManifestValidationError(
                f"manifest_id mismatch: stored {manifest['manifest_id']!r} != "
                f"computed {computed!r}", code="HASH_DISAGREEMENT")
    return dict(manifest)


# --- store (frozen write_sequence, bar-class payload) --------------------------

def publish_bar_manifest(root: Path, manifest: Mapping[str, Any]) -> Path:
    """Validate and atomically publish a bar manifest (frozen protocol).

    Same write_sequence as the @1 store: validate (including the frozen
    self-hash manifest_id) -> strict 64-hex id check -> sibling temp file ->
    fsync -> atomic replace -> re-read and re-validate with the
    filename/body binding check.  Identical re-publication is a no-op;
    different bytes at an existing manifest path raise HashDisagreement.
    """
    root = Path(root)
    validated = validate_bar_manifest(manifest)
    manifest_id = validated["manifest_id"]
    _require_hex64(manifest_id, "manifest_id")
    data = (_models.canonical_json(validated) + "\n").encode("utf-8")
    final = manifest_path(root, manifest_id)

    if final.exists():
        existing = final.read_bytes()
        if existing == data:
            return final
        raise HashDisagreement(
            f"manifest path {final} already holds DIFFERENT bytes; fail "
            f"closed, never overwrite")

    atomic_write_bytes(final, data)
    # Same protocol as the chunk stage: re-read and verify (binding included).
    loaded = load_bar_manifest(root, manifest_id)
    if loaded != validated:  # pragma: no cover - defensive re-read check
        raise ArchiveError(
            f"re-read bar manifest at {final} differs from published bytes")
    return final


def load_bar_manifest(root: Path, manifest_id: str) -> Dict[str, Any]:
    """Load and fully validate one bar manifest by strict 64-hex id.

    Fail-closed filename/body binding: the validated body's manifest_id must
    equal the requested id (F2 frozen rule, pre-validated here too).
    """
    _require_hex64(manifest_id, "manifest_id")
    path = manifest_path(root, manifest_id)
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise ArchiveError(f"bar manifest not found: {path}") from exc
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BarManifestValidationError(
            f"bar manifest {manifest_id} is not valid JSON: {exc}") from exc
    validated = validate_bar_manifest(manifest)
    if validated["manifest_id"] != manifest_id:
        raise BarManifestValidationError(
            f"bar manifest {manifest_id} is stored under a mismatched filename "
            f"(body manifest_id {validated['manifest_id']!r}); fail closed",
            code="HASH_DISAGREEMENT")
    return validated


def put_bar_records(root: Path, bars: Sequence[Mapping[str, Any]],
                    **identity: Any) -> Dict[str, Any]:
    """Serialize canonical bars to a JSONL chunk, then publish the manifest.

    Every bar is validated (fail closed) BEFORE any IO.  Chunk bytes are the
    frozen canonical framing; the mdp.bar_chunk_manifest@2 is built from
    derived payload statistics (payload_sha256, payload_byte_length,
    record_count, six bar-class time bounds) plus caller-supplied identity
    fields (entitlement evidence and classification are mandatory — the
    validator rejects their absence).  Order follows the frozen
    write_sequence: chunk committed and verified first, manifest published
    only afterwards; a manifest failure leaves the chunk as a diagnosable
    orphan and propagates.
    """
    root = Path(root)
    canonical = [_bars.validate_bar(bar) for bar in bars]
    payload = bar_chunk_payload_bytes(canonical)
    manifest = build_bar_manifest(
        payload_sha256=sha256_hex(payload),
        payload_byte_length=len(payload),
        record_count=len(canonical),
        time_bounds=bar_time_bounds(canonical),
        **identity,
    )
    validate_bar_manifest(manifest)  # fail before any IO on invalid identity
    chunk_result = write_chunk(
        root, payload,
        expected_sha256=manifest["payload_sha256"],
        expected_byte_length=manifest["payload_byte_length"],
        expected_record_count=manifest["record_count"],
    )
    manifest_file = publish_bar_manifest(root, manifest)
    return {
        "manifest": manifest,
        "manifest_path": manifest_file,
        "chunk_sha256": chunk_result["sha256"],
        "chunk_path": chunk_result["path"],
        "chunk_byte_length": chunk_result["byte_length"],
        "record_count": chunk_result["record_count"],
        "chunk_deduplicated": chunk_result["deduplicated"],
    }


def load_bar_records(root: Path, manifest_id: str) -> List[Dict[str, Any]]:
    """Load one bar chunk through its strict-64-hex manifest id, verified.

    Verifies content sha256, byte length, record count, trailing-partial and
    canonical per-record framing before validating each bar with
    bars.validate_bar.  Any disagreement raises (ArchiveError /
    HashDisagreement / BarManifestValidationError / BarError) — never silent.
    """
    root = Path(root)
    manifest = load_bar_manifest(root, manifest_id)
    sha = manifest["payload_sha256"]
    _require_hex64(sha, "payload_sha256")
    path = chunk_path(root, sha)
    try:
        data = path.read_bytes()
    except FileNotFoundError as exc:
        raise ArchiveError(
            f"manifest {manifest_id} references missing chunk file {path.name}") from exc
    actual = sha256_hex(data)
    if actual != sha:
        raise HashDisagreement(
            f"chunk content sha256 {actual} != manifest payload_sha256 {sha}")
    if len(data) != manifest["payload_byte_length"]:
        raise ArchiveError(
            f"chunk byte length {len(data)} != manifest payload_byte_length "
            f"{manifest['payload_byte_length']}")
    scanned = scan_payload(data)
    if scanned["record_count"] != manifest["record_count"]:
        raise ArchiveError(
            f"chunk record count {scanned['record_count']} != manifest "
            f"record_count {manifest['record_count']}")
    if scanned["has_trailing_partial"]:
        raise ArchiveError(
            "chunk has a trailing partial record (file does not end with newline)")

    bars_out: List[Dict[str, Any]] = []
    offset = 0
    for line in data.split(b"\n")[:-1]:
        line_offset = offset
        offset += len(line) + 1
        try:
            bar = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ArchiveError(
                f"chunk {sha} record at byte offset {line_offset} is not valid "
                f"JSON: {exc}") from exc
        if (_models.canonical_json(bar).encode("utf-8") != line):
            raise ArchiveError(
                f"chunk {sha} record at byte offset {line_offset} is not "
                f"canonical_json form")
        bars_out.append(_bars.validate_bar(bar))
    return bars_out


def verify_bar_chunk(root: Path, sha256: str, *,
                     expected_byte_length: Optional[int] = None,
                     expected_record_count: Optional[int] = None) -> Dict[str, Any]:
    """Recompute and compare one bar chunk; diagnostic report (never raises
    for findings — corruption is listed, callers route it visibly)."""
    _require_hex64(sha256, "sha256")
    path = chunk_path(Path(root), sha256)
    report: Dict[str, Any] = {
        "sha256": sha256,
        "path": path,
        "exists": path.exists(),
        "byte_length": None,
        "record_count": None,
        "actual_sha256": None,
        "has_trailing_partial": None,
        "errors": [],
    }
    if not path.exists():
        report["errors"].append("chunk file missing")
        return report
    data = path.read_bytes()
    report["byte_length"] = len(data)
    scanned = scan_payload(data)
    report["record_count"] = scanned["record_count"]
    report["has_trailing_partial"] = scanned["has_trailing_partial"]
    report["actual_sha256"] = sha256_hex(data)
    if report["actual_sha256"] != sha256:
        report["errors"].append(
            f"content sha256 {report['actual_sha256']} != path name {sha256}")
    if expected_byte_length is not None and report["byte_length"] != expected_byte_length:
        report["errors"].append(
            f"byte length {report['byte_length']} != expected {expected_byte_length}")
    if expected_record_count is not None and report["record_count"] != expected_record_count:
        report["errors"].append(
            f"record count {report['record_count']} != expected {expected_record_count}")
    if scanned["has_trailing_partial"]:
        report["errors"].append("trailing partial record (file does not end with newline)")
    return report
