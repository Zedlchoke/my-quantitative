"""Portable V12 ledger transfer -- cross-host checksum verification (L-V11-5).

P1 lane A2.  The canonical ledger is gitignored and machine-local; a host
migration without a verified transfer package strands it (lesson L-V11-5:
"host migration without this package is a prelaunch FAIL").  This module
implements the frozen transfer rule of
``research/control/v12_run/ledger_package/schema.json``:

    "a host may adopt this ledger only after transfer_manifest.json sha256
    verification of every shard file"

What lives here:

* :func:`sha256_file` / :func:`sha256_bytes` -- the single hashing primitive
  (streaming, 1 MiB chunks).
* :func:`verify_transfer_manifest` -- loads a
  ``v12_ledger_transfer_manifest_v1`` manifest and RECOMPUTES sha256 (plus
  byte size and, for ``.jsonl`` shards, the row count) for every declared
  file under ``root``.  ANY mismatch, missing file, path escape
  (absolute path or ``..`` segment) or schema violation fails closed with a
  :class:`ContractViolation` listing the stable reason codes.
* :func:`regenerate_transfer_manifest` -- builds a fresh manifest dict from
  a ledger path (for host migration): per-file sha256/bytes/rows plus the
  pinned ``empty_ledger_sha256`` seed.
* :func:`write_transfer_manifest` -- atomic (tmp + fsync + rename) manifest
  writer; refuses to silently overwrite an existing manifest unless
  ``overwrite=True``.

Calling convention (host migration):

1. OLD HOST: ``write_transfer_manifest(regenerate_transfer_manifest(ledger_path,
   root=...), <package>/transfer_manifest.json)`` and ship the package
   (schema.json + transfer_manifest.json) together with the ledger bytes.
2. NEW HOST: ``verify_transfer_manifest(<package>/transfer_manifest.json,
   root=<new host root>)`` -- the ledger may be adopted for scoring ONLY
   after this passes; anything else stays ``UNAVAILABLE_FAIL_CLOSED``.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping, Optional

from research.adapter_v10.protocol import ContractViolation

#: Frozen manifest schema token (transfer_manifest.json).
TRANSFER_MANIFEST_SCHEMA = "v12_ledger_transfer_manifest_v1"

#: Stable failure reason codes (machine-readable, fail closed).
MANIFEST_REASON_SCHEMA_MISMATCH = "TRANSFER_MANIFEST_SCHEMA_MISMATCH"
MANIFEST_REASON_NO_FILES = "TRANSFER_MANIFEST_NO_FILES"
MANIFEST_REASON_FILE_MISSING = "TRANSFER_MANIFEST_FILE_MISSING"
MANIFEST_REASON_SHA256_MISMATCH = "TRANSFER_MANIFEST_SHA256_MISMATCH"
MANIFEST_REASON_BYTES_MISMATCH = "TRANSFER_MANIFEST_BYTES_MISMATCH"
MANIFEST_REASON_ROWS_MISMATCH = "TRANSFER_MANIFEST_ROWS_MISMATCH"
MANIFEST_REASON_PATH_ESCAPE = "TRANSFER_MANIFEST_PATH_ESCAPE"
MANIFEST_REASON_EMPTY_SEED_MISMATCH = "TRANSFER_MANIFEST_EMPTY_SEED_MISMATCH"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: str | Path) -> str:
    """Streaming sha256 of one file (the single transfer-hash primitive)."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_under_root(root: Path, declared_path: str) -> Path:
    """Resolve a manifest-declared relative path, refusing any root escape.

    Fail closed: absolute paths and ``..`` segments can never smuggle the
    verification into reading (or pinning trust to) a file outside the
    transferred package root.
    """
    if not str(declared_path).strip():
        raise ContractViolation(f"{MANIFEST_REASON_PATH_ESCAPE}:empty_path")
    candidate = Path(declared_path)
    if candidate.is_absolute():
        raise ContractViolation(
            f"{MANIFEST_REASON_PATH_ESCAPE}:{declared_path}"
        )
    parts = candidate.parts
    if ".." in parts or "." in parts or not parts:
        raise ContractViolation(f"{MANIFEST_REASON_PATH_ESCAPE}:{declared_path}")
    resolved = (root / candidate).resolve()
    root_resolved = root.resolve()
    if root_resolved != resolved and root_resolved not in resolved.parents:
        raise ContractViolation(f"{MANIFEST_REASON_PATH_ESCAPE}:{declared_path}")
    return resolved


def _count_jsonl_rows(path: Path) -> int:
    rows = 0
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            if raw.strip():
                rows += 1
    return rows


def verify_transfer_manifest(
    manifest: str | Path | Mapping[str, Any],
    *,
    root: str | Path,
) -> dict[str, Any]:
    """Verify every declared shard file by RECOMPUTED sha256.  Fail closed.

    ``manifest`` is a path to a ``transfer_manifest.json`` or an already
    loaded mapping.  ``root`` is the directory the manifest's relative file
    paths resolve against (the ledger package root on THIS host).

    Returns an honest ``{"ok": True, "files_verified", "sha256s", ...}``.
    Any problem raises :class:`ContractViolation` with a stable
    ``TRANSFER_MANIFEST_*`` reason code; nothing is adopted on failure.
    """
    if isinstance(manifest, Mapping):
        doc: Mapping[str, Any] = manifest
    else:
        manifest_path = Path(manifest)
        if not manifest_path.exists():
            raise ContractViolation(f"{MANIFEST_REASON_FILE_MISSING}:{manifest_path}")
        with open(manifest_path, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
    if not isinstance(doc, Mapping):
        raise ContractViolation(MANIFEST_REASON_SCHEMA_MISMATCH + ":not_an_object")
    if str(doc.get("schema", "")) != TRANSFER_MANIFEST_SCHEMA:
        raise ContractViolation(
            f"{MANIFEST_REASON_SCHEMA_MISMATCH}:{doc.get('schema')!r}"
        )
    files = doc.get("files")
    if not isinstance(files, list) or not files:
        raise ContractViolation(MANIFEST_REASON_NO_FILES)

    root_path = Path(root)
    if not root_path.is_dir():
        raise ContractViolation(f"{MANIFEST_REASON_FILE_MISSING}:root:{root_path}")

    verified: dict[str, str] = {}
    for entry in files:
        if not isinstance(entry, Mapping):
            raise ContractViolation(MANIFEST_REASON_SCHEMA_MISMATCH + ":file_entry")
        declared_path = str(entry.get("path", ""))
        target = _resolve_under_root(root_path, declared_path)
        if not target.exists() or not target.is_file():
            raise ContractViolation(f"{MANIFEST_REASON_FILE_MISSING}:{declared_path}")
        actual_sha = sha256_file(target)
        declared_sha = str(entry.get("sha256", ""))
        if len(declared_sha) != 64 or actual_sha != declared_sha:
            raise ContractViolation(
                f"{MANIFEST_REASON_SHA256_MISMATCH}:{declared_path}:"
                f"declared={declared_sha[:12]}..actual={actual_sha[:12]}.."
            )
        actual_bytes = target.stat().st_size
        declared_bytes = entry.get("bytes")
        if declared_bytes is not None and int(declared_bytes) != actual_bytes:
            raise ContractViolation(
                f"{MANIFEST_REASON_BYTES_MISMATCH}:{declared_path}:"
                f"declared={declared_bytes} actual={actual_bytes}"
            )
        if target.suffix.lower() == ".jsonl" and entry.get("rows") is not None:
            actual_rows = _count_jsonl_rows(target)
            if int(entry["rows"]) != actual_rows:
                raise ContractViolation(
                    f"{MANIFEST_REASON_ROWS_MISMATCH}:{declared_path}:"
                    f"declared={entry['rows']} actual={actual_rows}"
                )
        verified[declared_path] = actual_sha

    # The empty-ledger seed must stay the sha256 of zero bytes so a fresh
    # per-sprint package can always be re-derived and compared.
    empty_seed = doc.get("empty_ledger_sha256")
    if empty_seed is not None:
        if str(empty_seed) != sha256_bytes(b""):
            raise ContractViolation(
                f"{MANIFEST_REASON_EMPTY_SEED_MISMATCH}:{empty_seed}"
            )

    return {
        "ok": True,
        "files_verified": len(verified),
        "sha256s": verified,
        "schema": TRANSFER_MANIFEST_SCHEMA,
    }


def regenerate_transfer_manifest(
    ledger_path: str | Path,
    *,
    root: str | Path,
    producer_role: str = "A2",
    generated_utc: str = "",
    note: str = "",
) -> dict[str, Any]:
    """Build a fresh transfer manifest from a ledger path (host migration).

    ``ledger_path`` must live under ``root``; the manifest declares it
    root-relative (the same convention as the frozen package).  ``rows`` is
    the recounted JSONL row count; ``empty_ledger_sha256`` pins the
    sha256-of-zero-bytes seed so an empty per-sprint ledger is detectable.
    """
    root_path = Path(root)
    ledger = Path(ledger_path)
    if not ledger.exists() or not ledger.is_file():
        raise ContractViolation(f"{MANIFEST_REASON_FILE_MISSING}:{ledger}")
    resolved = ledger.resolve()
    root_resolved = root_path.resolve()
    if root_resolved != resolved and root_resolved not in resolved.parents:
        raise ContractViolation(f"{MANIFEST_REASON_PATH_ESCAPE}:{ledger}")
    relative = resolved.relative_to(root_resolved).as_posix()
    size = resolved.stat().st_size
    return {
        "schema": TRANSFER_MANIFEST_SCHEMA,
        "generated_utc": str(generated_utc),
        "producer_role": str(producer_role),
        "files": [
            {
                "path": relative,
                "sha256": sha256_file(resolved),
                "bytes": size,
                "rows": _count_jsonl_rows(resolved),
            }
        ],
        "empty_ledger_sha256": sha256_bytes(b""),
        "note": str(note),
    }


def write_transfer_manifest(
    manifest: Mapping[str, Any],
    manifest_path: str | Path,
    *,
    overwrite: bool = False,
) -> str:
    """Atomically write a manifest (tmp + fsync + rename).  Fail closed.

    Refuses to silently replace an existing manifest unless
    ``overwrite=True``; returns the sha256 of the written bytes.
    """
    target = Path(manifest_path)
    if target.exists() and not overwrite:
        raise ContractViolation(
            f"TRANSFER_MANIFEST_WRITE_REFUSED_EXISTS:{target}"
        )
    payload = json.dumps(dict(manifest), indent=1, sort_keys=True) + "\n"
    data = payload.encode("utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    with open(tmp, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, target)
    return sha256_bytes(data)


def verify_or_refuse(
    manifest: str | Path | Mapping[str, Any],
    *,
    root: str | Path,
) -> dict[str, Any]:
    """Non-raising wrapper: ``{"ok": True, ...}`` or ``{"ok": False,
    "reason": <stable code>, "detail": ...}`` (never partially adopts)."""
    try:
        result = verify_transfer_manifest(manifest, root=root)
    except ContractViolation as exc:
        text = str(exc)
        reason = text.split(":", 1)[0]
        return {"ok": False, "reason": reason, "detail": text}
    return dict(result)


__all__ = [
    "MANIFEST_REASON_BYTES_MISMATCH",
    "MANIFEST_REASON_EMPTY_SEED_MISMATCH",
    "MANIFEST_REASON_FILE_MISSING",
    "MANIFEST_REASON_NO_FILES",
    "MANIFEST_REASON_PATH_ESCAPE",
    "MANIFEST_REASON_ROWS_MISMATCH",
    "MANIFEST_REASON_SCHEMA_MISMATCH",
    "MANIFEST_REASON_SHA256_MISMATCH",
    "TRANSFER_MANIFEST_SCHEMA",
    "regenerate_transfer_manifest",
    "sha256_bytes",
    "sha256_file",
    "verify_or_refuse",
    "verify_transfer_manifest",
    "write_transfer_manifest",
]
