"""Content-addressed immutable chunk store for MDP-V1 (lane A3).

Implements the frozen ``archive_protocol`` from
``research/control/market_data_plane_v1_run/architecture_freeze.json``
(sha256 7f7403e67bfb9707b547b6762cc0a3c87f2c96f701b3f1ec3ad2197478736c02):

- layout ``<root>/chunks/<h2>/<h2b>/<sha256>.jsonl`` plus
  ``<root>/manifests/<manifest_id>.json``;
- write_sequence EXACTLY: sibling temp file ``.tmp-<pid>-<monotonic counter>``
  in the SAME directory -> flush -> ``os.fsync`` -> ``os.replace`` (atomic)
  -> re-read and verify sha256 + byte length + record count -> only then
  publish the manifest atomically (same temp+fsync+replace, plus re-read
  validation of the published manifest);
- immutability: re-put of identical bytes is a no-op; DIFFERENT bytes at an
  existing content path raise HashDisagreement (fail closed, never
  overwrite);
- append forbidden: no code path opens a published file for appending --
  every persisted byte sequence is written whole via temp+replace;
- orphans: chunk without manifest, manifest without chunk, trailing partial
  record are diagnosed by ``scan_orphans`` -- never guessed complete;
- manifest publication failure leaves the chunk in place (diagnosable
  orphan) and the failure propagates visibly.

stdlib only (event-stream hot-path import isolation rule). Events are plain
dicts per the parallel-lane rule; A2's models.py does not exist in this
worktree and is never imported here.

V2 (finding F2, MDP-V2 architecture freeze
``research/control/market_data_plane_v2_run/architecture_freeze_v2.json``)
hardening, applied without changing the V1 layout for valid IDs:
- content-ID grammar: caller-supplied chunk sha256 and manifest_id path
  arguments must match ``^[0-9a-f]{64}$`` exactly or the path builders raise
  ArchiveError before any filesystem access;
- path confinement: the resolved absolute target of chunk_path/manifest_path
  must remain strictly below ``Path(root).resolve()`` (symlink escapes fail
  closed) -- enforced before ANY filesystem read or write on the
  write_chunk/publish_manifest/load_manifest/verify_chunk paths;
- filename/body binding: load_manifest raises ManifestValidationError unless
  the validated body's manifest_id equals the requested manifest_id;
- verify_chunk raises ArchiveError for a grammar-violating ID (pinned
  choice): malicious IDs are rejected loudly, never probed, never written.
"""
from __future__ import annotations

import itertools
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from ._canonical import canonical_line_bytes
from .manifest import (
    ManifestValidationError,
    build_manifest,
    canonical_manifest_bytes,
    is_hex64,
    sha256_hex,
    validate_manifest,
)

__all__ = [
    "ArchiveError",
    "HashDisagreement",
    "atomic_write_bytes",
    "chunk_path",
    "manifest_path",
    "write_chunk",
    "publish_manifest",
    "load_manifest",
    "put_chunk_records",
    "verify_chunk",
    "scan_orphans",
    "scan_payload",
]


class ArchiveError(RuntimeError):
    """Base error for archive store failures (visible, never silent)."""


class HashDisagreement(ArchiveError):
    """Different bytes at an existing content path, or a re-read mismatch.

    Maps to reason_codes@1 ``HASH_DISAGREEMENT``. Fail closed: the on-disk
    bytes are never overwritten by this module.
    """

    code = "HASH_DISAGREEMENT"


_TEMP_COUNTER = itertools.count()


def _temp_name() -> str:
    # Frozen write_sequence: .tmp-<pid>-<monotonic counter> (sibling file).
    return f".tmp-{os.getpid()}-{next(_TEMP_COUNTER)}"


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Frozen atomic write protocol: temp sibling -> flush -> fsync -> replace.

    On any failure the temp file is removed and the exception propagates;
    no partial file is ever visible under ``path``. Callers that need
    post-write verification (the chunk write_sequence) perform it after this
    function returns.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / _temp_name()
    try:
        with open(tmp, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def scan_payload(data: bytes) -> Dict[str, Any]:
    """Inspect newline-delimited canonical payload bytes.

    Returns ``record_count`` (complete lines), ``has_trailing_partial`` (file
    does not end with the record-terminating newline) and ``empty_lines``.
    A correctly written chunk has one canonical record plus ``"\\n"`` per
    event, so ``record_count`` equals the event count and there is no
    trailing partial record.
    """
    if not data:
        return {"record_count": 0, "has_trailing_partial": False, "empty_lines": 0}
    has_trailing_partial = not data.endswith(b"\n")
    record_count = data.count(b"\n")
    empty_lines = sum(1 for line in data.split(b"\n")[:-1] if line == b"")
    return {
        "record_count": record_count,
        "has_trailing_partial": has_trailing_partial,
        "empty_lines": empty_lines,
    }


def _confine(root: Path, target: Path) -> None:
    """V2 F2 path confinement: fail closed unless target is strictly below root.

    The resolved absolute ``target`` must remain strictly below
    ``Path(root).resolve()``. Verified BEFORE any filesystem read or write;
    a violation (``..`` traversal, absolute escape, or a symlink at a
    directory boundary pointing outside the root) raises ArchiveError and no
    fallback path is ever taken.
    """
    root_resolved = Path(root).resolve()
    target_resolved = target.resolve()
    if target_resolved == root_resolved or not target_resolved.is_relative_to(root_resolved):
        raise ArchiveError(
            f"path escapes archive root: {target} resolves to {target_resolved}, "
            f"which is not strictly below {root_resolved}"
        )


def chunk_path(root: Path, sha256: str) -> Path:
    """Frozen layout: <root>/chunks/<h2>/<h2b>/<sha256>.jsonl.

    V2 F2: ``sha256`` must match the content-ID grammar ``^[0-9a-f]{64}$``
    exactly -- empty, short (<64), 63/65-length, overlong, uppercase,
    non-hex, traversal/separator/absolute and non-string (pathlike) inputs
    raise ArchiveError. The resolved target must additionally remain
    strictly below the resolved root (symlink escapes raise ArchiveError).
    Both checks run BEFORE any filesystem access. For valid 64-hex IDs the
    returned path and the on-disk V1 layout are unchanged (byte-compatible).
    """
    if not is_hex64(sha256):
        raise ArchiveError(
            "invalid sha256 for chunk path "
            f"(must match ^[0-9a-f]{{64}}$ exactly): {sha256!r}"
        )
    target = Path(root) / "chunks" / sha256[:2] / sha256[2:4] / f"{sha256}.jsonl"
    _confine(root, target)
    return target


def manifest_path(root: Path, manifest_id: str) -> Path:
    """Frozen layout: <root>/manifests/<manifest_id>.json.

    V2 F2: ``manifest_id`` must match ``^[0-9a-f]{64}$`` exactly and the
    resolved target must remain strictly below the resolved root; violations
    raise ArchiveError before any filesystem access (previously this builder
    validated nothing).
    """
    if not is_hex64(manifest_id):
        raise ArchiveError(
            "invalid manifest_id for manifest path "
            f"(must match ^[0-9a-f]{{64}}$ exactly): {manifest_id!r}"
        )
    target = Path(root) / "manifests" / f"{manifest_id}.json"
    _confine(root, target)
    return target


def write_chunk(
    root: Path,
    payload: bytes,
    *,
    expected_sha256: Optional[str] = None,
    expected_byte_length: Optional[int] = None,
    expected_record_count: Optional[int] = None,
) -> Dict[str, Any]:
    """Write one content-addressed chunk by the frozen write_sequence.

    Steps, exactly: immutability pre-check at the final content path ->
    sibling temp file -> write -> flush -> ``os.fsync`` -> ``os.replace`` ->
    re-read and verify sha256 + byte length + record count (+ no trailing
    partial record).

    Re-put of identical bytes is a no-op (``deduplicated: True``). Existing
    bytes that differ from ``payload`` raise HashDisagreement; the on-disk
    bytes are never overwritten.
    """
    root = Path(root)
    sha = sha256_hex(payload)
    if expected_sha256 is not None and expected_sha256 != sha:
        raise HashDisagreement(
            f"payload sha256 {sha} != expected {expected_sha256}; refusing to write"
        )
    final = chunk_path(root, sha)

    if final.exists():
        existing = final.read_bytes()
        if existing == payload:
            return {
                "sha256": sha,
                "path": final,
                "byte_length": len(payload),
                "record_count": scan_payload(payload)["record_count"],
                "deduplicated": True,
            }
        raise HashDisagreement(
            f"content path {final} already holds DIFFERENT bytes "
            f"({len(existing)}B vs {len(payload)}B incoming); fail closed, never overwrite"
        )

    atomic_write_bytes(final, payload)

    # Frozen write_sequence: re-read and verify sha256 + byte length +
    # record count before anything else may reference this chunk.
    readback = final.read_bytes()
    readback_sha = sha256_hex(readback)
    if readback_sha != sha:
        raise HashDisagreement(
            f"re-read sha256 mismatch at {final}: {readback_sha} != {sha}"
        )
    if len(readback) != len(payload):
        raise ArchiveError(
            f"re-read byte length mismatch at {final}: {len(readback)} != {len(payload)}"
        )
    scanned = scan_payload(readback)
    if expected_record_count is not None and scanned["record_count"] != expected_record_count:
        raise ArchiveError(
            f"re-read record count mismatch at {final}: "
            f"{scanned['record_count']} != {expected_record_count}"
        )
    if scanned["has_trailing_partial"]:
        raise ArchiveError(f"re-read found trailing partial record at {final}")
    if expected_byte_length is not None and len(readback) != expected_byte_length:
        raise ArchiveError(
            f"re-read byte length mismatch at {final}: {len(readback)} != {expected_byte_length}"
        )

    return {
        "sha256": sha,
        "path": final,
        "byte_length": len(readback),
        "record_count": scanned["record_count"],
        "deduplicated": False,
    }


def publish_manifest(root: Path, manifest: Mapping[str, Any]) -> Path:
    """Validate and atomically publish a manifest (same write protocol).

    The manifest is validated (including its frozen self-hash manifest_id)
    BEFORE publication. Identical re-publication is a no-op; different bytes
    at an existing manifest path raise HashDisagreement. After replace, the
    file is re-read and re-validated (same protocol as the chunk stage).
    """
    root = Path(root)
    validated = validate_manifest(manifest)
    data = canonical_manifest_bytes(validated)
    manifest_id = validated["manifest_id"]
    final = manifest_path(root, manifest_id)

    if final.exists():
        existing = final.read_bytes()
        if existing == data:
            return final
        raise HashDisagreement(
            f"manifest path {final} already holds DIFFERENT bytes; fail closed, never overwrite"
        )

    atomic_write_bytes(final, data)

    # Same protocol as the chunk stage: re-read and verify.
    load_manifest(root, manifest_id)
    return final


def load_manifest(root: Path, manifest_id: str) -> Dict[str, Any]:
    """Load and fully validate one manifest by id.

    V2 F2 filename/body binding: after parse and full validation, the
    validated body's ``manifest_id`` must equal the requested (filename)
    ``manifest_id`` -- valid manifest bytes stored under a different valid
    64-hex filename raise ManifestValidationError (fail closed, file never
    rewritten). The path grammar and root confinement are enforced by
    ``manifest_path`` before any read.
    """
    path = manifest_path(root, manifest_id)
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise ArchiveError(f"manifest not found: {path}") from exc
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestValidationError(
            f"manifest {manifest_id} is not valid JSON: {exc}"
        ) from exc
    validated = validate_manifest(manifest)
    if validated["manifest_id"] != manifest_id:
        raise ManifestValidationError(
            f"manifest filename/body binding mismatch at {path}: requested "
            f"{manifest_id!r} but validated body carries manifest_id "
            f"{validated['manifest_id']!r}",
            code="HASH_DISAGREEMENT",
        )
    return validated


def _time_bounds(events: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Derive the six min/max manifest time fields from event dicts.

    Only genuine ints are collected (bools excluded); absent/None bounds stay
    null. Deep event-field validation belongs to A2's models at the
    ingestion boundary; this derives manifest statistics only.
    """
    bounds: Dict[str, Any] = {}
    for stem in ("exchange", "receive", "available"):
        values = [
            e[f"{stem}_time_utc_ns"]
            for e in events
            if isinstance(e.get(f"{stem}_time_utc_ns"), int)
            and not isinstance(e.get(f"{stem}_time_utc_ns"), bool)
        ]
        bounds[f"min_{stem}_time_utc_ns"] = min(values) if values else None
        bounds[f"max_{stem}_time_utc_ns"] = max(values) if values else None
    return bounds


def put_chunk_records(
    root: Path,
    events: Sequence[Mapping[str, Any]],
    **identity: Any,
) -> Dict[str, Any]:
    """Serialize events to a canonical JSONL chunk, then publish manifest.

    Chunk bytes are the frozen stream framing: canonical_json + newline per
    event. The manifest is built from derived payload statistics
    (payload_sha256, payload_byte_length, record_count, six time bounds)
    plus caller-supplied identity fields forwarded to
    ``manifest.build_manifest`` (entitlement evidence and classification are
    mandatory: the manifest validator rejects their absence).

    Order follows the frozen write_sequence: chunk bytes committed and
    verified first, manifest published only afterwards. If manifest
    publication fails, the chunk remains in place as an explicit orphan
    (findable via ``scan_orphans``) and the exception propagates.
    """
    root = Path(root)
    payload = b"".join(canonical_line_bytes(event) for event in events)
    manifest = build_manifest(
        payload_sha256=sha256_hex(payload),
        payload_byte_length=len(payload),
        record_count=len(events),
        time_bounds=_time_bounds(events),
        **identity,
    )
    validate_manifest(manifest)  # fail before any IO on invalid identity input
    chunk_result = write_chunk(
        root,
        payload,
        expected_sha256=manifest["payload_sha256"],
        expected_byte_length=manifest["payload_byte_length"],
        expected_record_count=manifest["record_count"],
    )
    manifest_file = publish_manifest(root, manifest)
    return {
        "manifest": manifest,
        "manifest_path": manifest_file,
        "chunk_sha256": chunk_result["sha256"],
        "chunk_path": chunk_result["path"],
        "chunk_byte_length": chunk_result["byte_length"],
        "record_count": chunk_result["record_count"],
        "chunk_deduplicated": chunk_result["deduplicated"],
    }


def verify_chunk(
    root: Path,
    sha256: str,
    *,
    expected_byte_length: Optional[int] = None,
    expected_record_count: Optional[int] = None,
) -> Dict[str, Any]:
    """Recompute and compare one chunk; returns a diagnostic report.

    Never raises for content findings (unlike the write path): the report
    lists every mismatch so callers (and ``scan_orphans``) can route
    corruption visibly instead of guessing completeness. Pinned V2 F2
    exception: a sha256 argument violating the content-ID grammar, or a
    target escaping the archive root, raises ArchiveError BEFORE any
    filesystem access -- a malicious ID is rejected loudly, never probed
    and never written.
    """
    path = chunk_path(root, sha256)
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
            f"content sha256 {report['actual_sha256']} != path name {sha256}"
        )
    if expected_byte_length is not None and report["byte_length"] != expected_byte_length:
        report["errors"].append(
            f"byte length {report['byte_length']} != expected {expected_byte_length}"
        )
    if expected_record_count is not None and report["record_count"] != expected_record_count:
        report["errors"].append(
            f"record count {report['record_count']} != expected {expected_record_count}"
        )
    if scanned["has_trailing_partial"]:
        report["errors"].append("trailing partial record (file does not end with newline)")
    if scanned["empty_lines"]:
        report["errors"].append(f"{scanned['empty_lines']} empty line(s) inside payload")
    return report


def scan_orphans(root: Path) -> Dict[str, Any]:
    """Diagnose orphaned/corrupted archive state; never guesses complete.

    Categories (frozen archive_protocol.orphans plus extra diagnosability):
    - ``chunks_without_manifest``: chunk present, referenced by no readable
      manifest (includes the post-publication-failure case);
    - ``manifests_without_chunk``: manifest present, its payload chunk absent;
    - ``trailing_partial_records``: chunk files not ending with the record
      newline (crash/truncation signature);
    - ``sha_mismatch_chunks``: content hash differs from the file's content
      address (corruption, worse than orphan);
    - ``manifest_unreadable``: manifest file that fails parse/validate;
    - ``stray_temp_files``: leftover ``.tmp-*`` siblings from interrupted
      writes.
    All lists are sorted for deterministic output.
    """
    root = Path(root)
    manifests_dir = root / "manifests"
    chunks_dir = root / "chunks"

    referenced_by: Dict[str, List[str]] = {}
    manifests_without_chunk: List[Dict[str, str]] = []
    manifest_unreadable: List[Dict[str, str]] = []
    manifest_names = sorted(manifests_dir.glob("*.json")) if manifests_dir.is_dir() else []
    for path in manifest_names:
        try:
            manifest = json.loads(path.read_bytes().decode("utf-8"))
            validated = validate_manifest(manifest)
        except (UnicodeDecodeError, json.JSONDecodeError, ManifestValidationError, OSError) as exc:
            manifest_unreadable.append({"name": path.name, "error": str(exc)})
            continue
        sha = validated["payload_sha256"]
        referenced_by.setdefault(sha, []).append(validated["manifest_id"])
        if not chunk_path(root, sha).exists():
            manifests_without_chunk.append(
                {"manifest_id": validated["manifest_id"], "payload_sha256": sha}
            )

    chunks_without_manifest: List[str] = []
    sha_mismatch_chunks: List[Dict[str, str]] = []
    trailing_partial_records: List[Dict[str, str]] = []
    malformed_line_chunks: List[Dict[str, str]] = []
    chunk_files = sorted(chunks_dir.rglob("*.jsonl")) if chunks_dir.is_dir() else []
    for path in chunk_files:
        sha_from_name = path.name[: -len(".jsonl")]
        data = path.read_bytes()
        scanned = scan_payload(data)
        rel = str(path.relative_to(root))
        if scanned["has_trailing_partial"]:
            trailing_partial_records.append({"path": rel, "sha256": sha_from_name})
        actual = sha256_hex(data)
        if actual != sha_from_name:
            sha_mismatch_chunks.append(
                {"path": rel, "expected_sha256": sha_from_name, "actual_sha256": actual}
            )
        if sha_from_name not in referenced_by:
            chunks_without_manifest.append(sha_from_name)
        # A manifest-referenced chunk with an unparsable line is corruption
        # the manifest cannot describe: surfaced here, never guessed complete.
        if not scanned["has_trailing_partial"]:
            for line in data.split(b"\n")[:-1]:
                try:
                    json.loads(line.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    malformed_line_chunks.append(
                        {"path": rel, "sha256": sha_from_name}
                    )
                    break

    unexpected_names = [
        str(path.relative_to(root))
        for path in chunk_files
        if len(path.name) != 64 + len(".jsonl") or not path.name.endswith(".jsonl")
    ]
    stray_temp_files = sorted(
        str(path.relative_to(root))
        for pattern in (manifests_dir, chunks_dir)
        if pattern.is_dir()
        for path in pattern.rglob(".tmp-*")
    )

    return {
        "chunks_without_manifest": sorted(chunks_without_manifest),
        "manifests_without_chunk": sorted(
            manifests_without_chunk, key=lambda item: item["manifest_id"]
        ),
        "trailing_partial_records": sorted(trailing_partial_records, key=lambda item: item["path"]),
        "sha_mismatch_chunks": sorted(sha_mismatch_chunks, key=lambda item: item["path"]),
        "malformed_line_chunks": sorted(malformed_line_chunks, key=lambda item: item["path"]),
        "manifest_unreadable": sorted(manifest_unreadable, key=lambda item: item["name"]),
        "unexpected_chunk_names": sorted(unexpected_names),
        "stray_temp_files": stray_temp_files,
        "chunk_count": len(chunk_files),
        "manifest_count": len(manifest_names),
    }
