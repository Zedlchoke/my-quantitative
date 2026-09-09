"""Quarantine store with lineage for MDP-V1 (lane A3).

Implements the frozen quarantine semantics from
``research/control/market_data_plane_v1_run/architecture_freeze.json``
(sha256 7f7403e67bfb9707b547b6762cc0a3c87f2c96f701b3f1ec3ad2197478736c02)
and plan section 6.4/7.1 ("quarantine with lineage", "orphans are diagnosed
and quarantined"):

- record carries a quarantine_id plus full lineage: reason_codes, the raw
  reference (original manifest_id + chunk sha256 + byte offset), the event
  dict when parseable, ``quarantined_utc_ns`` and ``rule_version``;
- store: append-only canonical JSONL under ``<root>/quarantine/records.jsonl``,
  written per batch with the frozen temp+fsync+replace protocol (the whole
  store file is rewritten atomically: append-only content, atomic visibility;
  no code path opens the store in append mode);
- dedupe by (raw reference, reason codes): a re-quarantine of the same bytes
  for the same reasons is a no-op;
- an event is NEVER silently dropped: the API forces a non-empty
  ``reason_codes`` list drawn from the frozen reason_codes@1 registry --
  empty or unknown codes raise, visibly.

LOCAL FROZEN COPY of reason_codes@1 (codes + classes) duplicated below
because A2's ``research/market_data_plane/reason_codes.py`` does not exist in
this parallel lane's worktree and must not be imported here. A1 reconciles
this module constant with A2's registry at integration; the freeze JSON is
the single source of truth.

stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from ._canonical import canonical_json, canonical_line_bytes
from .archive import atomic_write_bytes

__all__ = [
    "REASON_CODES_VERSION",
    "REASON_CODES",
    "REJECT_TO_QUARANTINE_CODES",
    "FLAG_SUSPECT_CODES",
    "BOOKKEEPING_CODES",
    "QuarantineStoreError",
    "QuarantineStore",
]

REASON_CODES_VERSION = "reason_codes@1"

# --- BEGIN local frozen copy of freeze "reason_codes@1" (A1 reconciles). ---
REASON_CODES: Tuple[str, ...] = (
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

REJECT_TO_QUARANTINE_CODES: Tuple[str, ...] = (
    "MALFORMED_SHAPE",
    "MISSING_REQUIRED_FIELD",
    "UNKNOWN_EVENT_TYPE",
    "TIMEZONE_NAIVE_REJECTED",
    "NON_FINITE_PRICE",
    "PRECISION_LOSS",
    "NEGATIVE_PRICE",
    "NEGATIVE_SIZE",
    "CROSSED_QUOTE",
    "IMPOSSIBLE_TIME_ORDER",
    "SOURCE_RESET_UNEVIDENCED",
    "UNKNOWN_INSTRUMENT",
    "MANIFEST_MISMATCH",
    "HASH_DISAGREEMENT",
    "QUARANTINE_ORPHAN",
)

FLAG_SUSPECT_CODES: Tuple[str, ...] = (
    "STALE_QUOTE",
    "OUT_OF_ORDER_DELIVERY",
    "SEQUENCE_GAP",
    "SEQUENCE_RESET",
    "STATISTICAL_ANOMALY",
)

BOOKKEEPING_CODES: Tuple[str, ...] = ("DUPLICATE_EVENT",)
# --- END local frozen copy of freeze "reason_codes@1". ---


class QuarantineStoreError(RuntimeError):
    """Quarantine store failure or invalid quarantine request (visible)."""


def _normalize_reason_codes(reason_codes: Sequence[str]) -> List[str]:
    """Force a valid reason code set; an event is never stored without one."""
    if not isinstance(reason_codes, (list, tuple)) or len(reason_codes) == 0:
        raise QuarantineStoreError(
            "reason_codes must be a non-empty list drawn from reason_codes@1; "
            "an event is never silently dropped"
        )
    for code in reason_codes:
        if not isinstance(code, str) or code not in REASON_CODES:
            raise QuarantineStoreError(
                f"reason code {code!r} is outside the frozen reason_codes@1 registry"
            )
    return sorted(set(reason_codes))


def _lineage_key(record: Mapping[str, Any]) -> Tuple[Any, ...]:
    return (
        record.get("manifest_id"),
        record.get("chunk_sha256"),
        record.get("byte_offset"),
        tuple(record.get("reason_codes") or ()),
    )


class QuarantineStore:
    """Append-only, crash-safe quarantine JSONL store with lineage.

    Layout: ``<root>/quarantine/records.jsonl``. Every write batch rewrites
    the store atomically (sibling temp file -> flush -> fsync ->
    ``os.replace``), so a crash leaves either the previous store intact or
    the new complete store -- never a torn file under the store path.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.path = self.root / "quarantine" / "records.jsonl"

    # -- reading -----------------------------------------------------------

    def records(self) -> List[Dict[str, Any]]:
        """All quarantined records in append (file) order.

        A corrupted store line -- including a torn trailing partial record
        from external corruption -- raises QuarantineStoreError: quarantined
        evidence is never silently skipped, truncated, or repaired. (The
        store's own atomic writes can never produce a torn file; only
        external tampering can, and it must be visible.)
        """
        if not self.path.exists():
            return []
        out: List[Dict[str, Any]] = []
        data = self.path.read_bytes()
        if data and not data.endswith(b"\n"):
            raise QuarantineStoreError(
                "quarantine store has a trailing partial record "
                "(torn write/external corruption); refusing to guess completeness"
            )
        for number, line in enumerate(data.split(b"\n")[:-1], start=1):
            try:
                out.append(json.loads(line.decode("utf-8")))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise QuarantineStoreError(
                    f"quarantine store line {number} is corrupt (not valid JSON): {exc}"
                ) from exc
        return out

    def replay(
        self, predicate: Optional[Mapping[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Listing/replay of quarantined records, optionally filtered.

        ``predicate`` is a flat equality dict over record fields (e.g.
        ``{"manifest_id": X}`` or ``{"reason_codes": ["MALFORMED_SHAPE"]}``);
        keys not present in a record simply do not match. Records return in
        stable file order.
        """
        if predicate is None:
            return self.records()
        return [
            record
            for record in self.records()
            if all(record.get(key) == value for key, value in predicate.items())
        ]

    def events(self) -> List[Mapping[str, Any]]:
        """The stored event dicts (where the original record was parseable)."""
        return [record["event"] for record in self.records() if record.get("event") is not None]

    # -- writing -----------------------------------------------------------

    def quarantine_id_for(self, record: Mapping[str, Any]) -> str:
        """quarantine_id = sha256(canonical_json(record minus quarantine_id))."""
        material = {k: v for k, v in record.items() if k != "quarantine_id"}
        return hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()

    def build_record(
        self,
        *,
        reason_codes: Sequence[str],
        manifest_id: Optional[str] = None,
        chunk_sha256: Optional[str] = None,
        byte_offset: Optional[int] = None,
        event: Optional[Mapping[str, Any]] = None,
        rule_version: str = REASON_CODES_VERSION,
        quarantined_utc_ns: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Build one lineage-carrying quarantine record (validated, no IO)."""
        if byte_offset is not None and (isinstance(byte_offset, bool) or not isinstance(byte_offset, int)):
            raise QuarantineStoreError("byte_offset must be int or null")
        if event is not None and not isinstance(event, dict):
            raise QuarantineStoreError("event must be a dict (when parseable) or null")
        record: Dict[str, Any] = {
            "reason_codes": _normalize_reason_codes(reason_codes),
            "manifest_id": manifest_id,
            "chunk_sha256": chunk_sha256,
            "byte_offset": byte_offset,
            "event": event,
            "quarantined_utc_ns": (
                time.time_ns() if quarantined_utc_ns is None else quarantined_utc_ns
            ),
            "rule_version": rule_version,
        }
        record["quarantine_id"] = self.quarantine_id_for(record)
        return record

    def add(self, records: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
        """Persist a batch atomically; dedupe by (raw ref, reason codes).

        Existing store bytes are preserved verbatim (append-only); new
        records whose (manifest_id, chunk_sha256, byte_offset, reason_codes)
        tuple already exists are skipped and counted. The rewritten store is
        committed with the frozen temp+fsync+replace protocol in one batch.
        """
        new_records: List[Dict[str, Any]] = []
        for raw in records:
            record = dict(raw)
            if "quarantine_id" not in record:
                raise QuarantineStoreError(
                    "records passed to add() must come from build_record()/add_record()"
                )
            expected_id = self.quarantine_id_for(record)
            if record["quarantine_id"] != expected_id:
                raise QuarantineStoreError(
                    f"quarantine_id mismatch for record: {record['quarantine_id']!r} "
                    f"!= computed {expected_id!r}"
                )
            new_records.append(record)

        existing_keys = {_lineage_key(record) for record in self.records()}
        to_append: List[Dict[str, Any]] = []
        deduped = 0
        seen_in_batch = set(existing_keys)
        for record in new_records:
            key = _lineage_key(record)
            if key in seen_in_batch:
                deduped += 1
                continue
            seen_in_batch.add(key)
            to_append.append(record)

        if to_append:
            existing_bytes = self.path.read_bytes() if self.path.exists() else b""
            payload = existing_bytes + b"".join(
                canonical_line_bytes(record) for record in to_append
            )
            atomic_write_bytes(self.path, payload)
        return {
            "added": [record["quarantine_id"] for record in to_append],
            "deduped": deduped,
            "store_record_count": len(self.records()),
        }

    def add_record(self, **kwargs: Any) -> Dict[str, Any]:
        """Build one record via build_record() and persist it (convenience)."""
        return self.add([self.build_record(**kwargs)])
