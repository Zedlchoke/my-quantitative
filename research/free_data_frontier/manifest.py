"""Deterministic manifests and manifest verification from raw bytes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from .contract import validate_record


def deterministic_json_bytes(payload: Any) -> bytes:
    """Sorted keys, fixed separators, trailing newline -> byte-stable."""
    return (
        json.dumps(payload, sort_keys=True, indent=2, separators=(",", ": ")) + "\n"
    ).encode("utf-8")


def write_manifest(path: Path, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    validated = [validate_record(dict(record)) for record in records]
    validated.sort(key=lambda r: (r["source_id"], r["dataset_id"], r["raw_path"] or ""))
    blob = deterministic_json_bytes(validated)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(blob)
    tmp.replace(path)
    return {
        "manifest_path": str(path),
        "records": len(validated),
        "manifest_sha256": hashlib.sha256(blob).hexdigest(),
    }


def load_manifest(path: Path) -> List[Dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def recompute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(path: Path) -> Dict[str, Any]:
    """Verify every record's raw bytes against its pinned digest."""
    records = load_manifest(path)
    rows = []
    verified = 0
    failed = 0
    missing = 0
    for record in records:
        raw_path = record.get("raw_path")
        if not raw_path or record.get("raw_sha256") == "NOT_APPLIED":
            rows.append(
                {
                    "dataset_id": record["dataset_id"],
                    "verdict": "NOT_APPLIED",
                }
            )
            continue
        raw = Path(raw_path)
        if not raw.is_file():
            missing += 1
            rows.append({"dataset_id": record["dataset_id"], "verdict": "MISSING"})
            continue
        actual = recompute_sha256(raw)
        if actual == record["raw_sha256"]:
            verified += 1
            rows.append({"dataset_id": record["dataset_id"], "verdict": "VERIFIED"})
        else:
            failed += 1
            rows.append(
                {
                    "dataset_id": record["dataset_id"],
                    "verdict": "DIGEST_MISMATCH",
                    "pinned": record["raw_sha256"],
                    "actual": actual,
                }
            )
    return {
        "manifest_path": str(path),
        "records": len(records),
        "verified": verified,
        "failed": failed,
        "missing": missing,
        "verdict": "ALL_MATCH" if failed == 0 and missing == 0 else "MISMATCH_OR_MISSING",
        "rows": rows,
    }
