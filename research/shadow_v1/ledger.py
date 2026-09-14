"""Append-only JSONL virtual ledger per sleeve (plan section 8, G5).

Invariants:
- append is atomic: O_APPEND single write + fsync + mandatory read-back
  verification (prefix unchanged, suffix equals the written bytes);
- an event already present (same ``event_id``) is skipped idempotently on
  re-run — resuming never rewrites committed bytes;
- a crash mid-write leaves a partial line; scanning DETECTS it and
  REFUSES (raises :class:`LedgerCorruptError`) — the ledger is never
  silently truncated or repaired;
- :func:`ledger_digest` is sha256 over the raw file bytes.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

LEDGER_SUFFIX = ".jsonl"


class LedgerError(RuntimeError):
    """Base ledger error."""


class LedgerCorruptError(LedgerError):
    """Detected partial/garbled line: refuse, never truncate."""


class LedgerVerificationError(LedgerError):
    """Read-back verification failed after an append."""


def ledger_path(runtime_root: str, family_id: str) -> str:
    return os.path.join(runtime_root, f"{family_id}{LEDGER_SUFFIX}")


def _encode_line(record: Dict[str, Any]) -> bytes:
    line = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return (line + "\n").encode("utf-8")


def append_event(path: str, record: Dict[str, Any]) -> str:
    """Append one record atomically with read-back verification.

    Returns ``"appended"`` or ``"skipped_existing"`` (idempotent re-run:
    same ``event_id`` present -> committed bytes are never rewritten).
    """
    event_id = record.get("event_id")
    if not isinstance(event_id, str) or not event_id:
        raise LedgerError("record must carry a non-empty event_id")

    if os.path.exists(path):
        existing = event_ids(path)
        if event_id in existing:
            return "skipped_existing"

    payload = _encode_line(record)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    size_before = os.path.getsize(path) if os.path.exists(path) else 0
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        written = 0
        while written < len(payload):
            written += os.write(fd, payload[written:])
        os.fsync(fd)
    finally:
        os.close(fd)

    # Mandatory read-back verification.
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) != size_before + len(payload):
        raise LedgerVerificationError(
            f"read-back size mismatch for {path}: "
            f"expected {size_before + len(payload)}, got {len(data)}"
        )
    if data[size_before:] != payload:
        raise LedgerVerificationError(
            f"read-back content mismatch for {path}: appended bytes differ"
        )
    return "appended"


def read_raw_bytes(path: str) -> Optional[bytes]:
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return fh.read()


def scan_events(path: str) -> List[Dict[str, Any]]:
    """Parse all records; detect crash residue and refuse (no truncation)."""
    data = read_raw_bytes(path)
    if data is None or data == b"":
        return []
    if not data.endswith(b"\n"):
        raise LedgerCorruptError(
            f"{path}: last line is incomplete (crash mid-append); "
            "refusing to scan or truncate"
        )
    records: List[Dict[str, Any]] = []
    for lineno, raw in enumerate(data.split(b"\n")[:-1], start=1):
        try:
            rec = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise LedgerCorruptError(f"{path}: line {lineno} is not valid JSON: {exc}") from exc
        if not isinstance(rec, dict) or not isinstance(rec.get("event_id"), str):
            raise LedgerCorruptError(
                f"{path}: line {lineno} is not an event record"
            )
        records.append(rec)
    return records


def event_ids(path: str) -> set:
    return {rec["event_id"] for rec in scan_events(path)}


def ledger_digest(path: str) -> Optional[str]:
    """sha256 hex over the raw ledger file bytes; None if absent."""
    data = read_raw_bytes(path)
    if data is None:
        return None
    return hashlib.sha256(data).hexdigest()


def byte_count(path: str) -> int:
    data = read_raw_bytes(path)
    return 0 if data is None else len(data)
