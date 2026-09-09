"""Deterministic replay for MDP-V1 (lane A3).

Implements the frozen ``replay_contract`` from
``research/control/market_data_plane_v1_run/architecture_freeze.json``
(sha256 7f7403e67bfb9707b547b6762cc0a3c87f2c96f701b3f1ec3ad2197478736c02):

- total order key ``(exchange_time_utc_ns, receive_time_utc_ns,
  available_time_utc_ns, source_id, venue, instrument_id, event_type,
  sequence_number, event_id)`` with ``event_id`` as the final total
  tie-break; order is total, stable and independent of input file order;
- inputs are an EXPLICIT manifest id list plus a JSON-serializable predicate
  dict; both are recorded verbatim into the result;
- replay NEVER discovers newer files: only the named manifests and the
  chunks their ``payload_sha256`` fields reference are read; no directory
  scanning anywhere in this module;
- ``stream_digest = sha256`` over the exact canonical byte stream
  (canonical_json + newline per event); per-chunk digests recorded
  alongside;
- a corrupted record (bad JSON, non-canonical bytes, chunk-vs-manifest hash
  mismatch, count/length mismatch) raises CorruptReplayInput or is routed to
  a caller-supplied quarantine callback -- always visible; ``except
  Exception: pass`` is forbidden and absent;
- identical event ids appear once in the stream: the first occurrence in the
  total order streams, later occurrences are routed visibly as
  DUPLICATE_EVENT (bookkeeping class per reason_codes@1);
- semantic flags (SEQUENCE_GAP / SEQUENCE_RESET / OUT_OF_ORDER_DELIVERY) are
  raised ONLY under the declaring manifest's semantics flags
  (sequence_semantics=CONTIGUOUS / ordered_delivery=true); flags are
  recorded in the result and never rewrite streamed event bytes.

stdlib only. Events are plain dicts per the parallel-lane rule; A2's
models.py does not exist in this worktree and is never imported here.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from ._canonical import REPLAY_ORDER_FIELDS, canonical_json, canonical_line_bytes, replay_order_key
from .archive import ArchiveError, chunk_path, load_manifest, scan_payload
from .manifest import ManifestValidationError

__all__ = [
    "ReplayError",
    "ReplayInputError",
    "CorruptReplayInput",
    "ENVELOPE_FIELDS",
    "replay",
    "replay_events",
]

# Freeze schemas.envelope_fields (27-field list, local frozen copy; A1
# reconciles with A2's models.py at integration).
ENVELOPE_FIELDS: List[str] = [
    "schema_version",
    "event_id",
    "raw_id",
    "source_id",
    "venue",
    "instrument_id",
    "asset_class",
    "event_type",
    "exchange_time_utc_ns",
    "receive_time_utc_ns",
    "available_time_utc_ns",
    "sequence_number",
    "price",
    "quantity",
    "side",
    "bid_price",
    "ask_price",
    "bid_size",
    "ask_size",
    "currency",
    "price_precision",
    "size_precision",
    "quality_status",
    "reason_codes",
    "raw_sha256",
    "manifest_sha256",
    "normalizer_version",
]

# Fields replay itself structurally requires to compute the frozen total
# order (deep schema validation belongs to A2's models at the ingestion
# boundary).
_ORDER_REQUIRED_STR_FIELDS = (
    "source_id",
    "venue",
    "instrument_id",
    "event_type",
    "event_id",
)
_ORDER_REQUIRED_INT_FIELDS = (
    "exchange_time_utc_ns",
    "receive_time_utc_ns",
    "available_time_utc_ns",
)


class ReplayError(RuntimeError):
    """Base replay failure (visible, never silent)."""


class ReplayInputError(ReplayError):
    """Malformed replay arguments (bad predicate shape, non-string ids)."""


class CorruptReplayInput(ReplayError):
    """Corrupted replay input raised when no quarantine callback is given.

    ``record`` describes the corruption: manifest_id, chunk_sha256,
    byte_offset (line-level where known), a reason code drawn from
    reason_codes@1, and a human-readable detail.
    """

    def __init__(self, record: Mapping[str, Any]) -> None:
        self.record = dict(record)
        super().__init__(
            f"corrupt replay input: {self.record.get('reason')} "
            f"(manifest={self.record.get('manifest_id')!r}, "
            f"chunk={self.record.get('chunk_sha256')!r}, "
            f"offset={self.record.get('byte_offset')!r}): {self.record.get('detail')}"
        )


def _corrupt_record(
    manifest_id: Optional[str],
    chunk_sha256: Optional[str],
    byte_offset: Optional[int],
    reason: str,
    detail: str,
) -> Dict[str, Any]:
    return {
        "manifest_id": manifest_id,
        "chunk_sha256": chunk_sha256,
        "byte_offset": byte_offset,
        "reason": reason,
        "detail": detail,
    }


def _route(
    record: Mapping[str, Any],
    routed: List[Dict[str, Any]],
    on_corrupt: Optional[Callable[[Mapping[str, Any]], None]],
) -> None:
    """Route one corruption/duplicate record: callback or raise. Never hide."""
    routed.append(dict(record))
    if on_corrupt is None:
        raise CorruptReplayInput(record)
    on_corrupt(record)


def _validate_predicate(predicate: Any) -> None:
    if predicate is None or isinstance(predicate, dict):
        pass
    else:
        raise ReplayInputError("predicate must be None or a JSON-serializable dict")
    if isinstance(predicate, dict):
        for key, value in predicate.items():
            if not isinstance(key, str) or key not in ENVELOPE_FIELDS:
                raise ReplayInputError(
                    f"predicate key {key!r} is not an mdp.market_event@1 envelope field"
                )
            try:
                canonical_json({key: value})
            except (TypeError, ValueError) as exc:
                raise ReplayInputError(
                    f"predicate value for {key!r} is not JSON-serializable: {exc}"
                ) from exc


def _structural_event_check(event: Any, sequence_semantics: str) -> Optional[str]:
    """Return a defect detail string, or None when structurally orderable."""
    if not isinstance(event, dict):
        return "record is not a JSON object"
    for field in _ORDER_REQUIRED_STR_FIELDS:
        value = event.get(field)
        if not isinstance(value, str) or not value:
            return f"field {field} must be a non-empty string"
    for field in _ORDER_REQUIRED_INT_FIELDS:
        value = event.get(field)
        if isinstance(value, bool) or not isinstance(value, int):
            return f"field {field} must be int UTC nanoseconds"
    sequence = event.get("sequence_number")
    if sequence is not None and (isinstance(sequence, bool) or not isinstance(sequence, int)):
        return "field sequence_number must be int or null"
    if sequence is not None and sequence < 0:
        return "field sequence_number must be >= 0"
    if sequence_semantics == "CONTIGUOUS" and sequence is None:
        return "null sequence_number under sequence_semantics=CONTIGUOUS manifest"
    return None


def _load_chunk_records(
    root: Path,
    manifest: Mapping[str, Any],
    chunk_cache: Dict[str, Tuple[List[Any], List[Dict[str, Any]]]],
    routed: List[Dict[str, Any]],
    on_corrupt: Optional[Callable[[Mapping[str, Any]], None]],
) -> Tuple[List[Any], List[Dict[str, Any]]]:
    """Load and parse one referenced chunk exactly once (cache by sha).

    Returns (records, corruption_records) where records are (event,
    byte_offset) tuples in file order and corruption_records were already
    routed to on_corrupt on first load. Chunk-level defects (hash, byte
    length, record count, trailing partial) reject the WHOLE chunk visibly.
    """
    sha = manifest["payload_sha256"]
    manifest_id = manifest["manifest_id"]
    cached = chunk_cache.get(sha)
    if cached is not None:
        return cached

    records: List[Tuple[Any, int]] = []
    corruption: List[Dict[str, Any]] = []

    def reject(reason: str, detail: str) -> None:
        record = _corrupt_record(manifest_id, sha, None, reason, detail)
        corruption.append(record)
        _route(record, routed, on_corrupt)

    path = chunk_path(root, sha)
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        reject("MANIFEST_MISMATCH", f"manifest references missing chunk file {path.name}")
        chunk_cache[sha] = (records, corruption)
        return records, corruption
    except OSError as exc:
        reject("MANIFEST_MISMATCH", f"chunk file unreadable: {exc}")
        chunk_cache[sha] = (records, corruption)
        return records, corruption

    actual_sha = hashlib.sha256(data).hexdigest()
    if actual_sha != sha:
        reject(
            "HASH_DISAGREEMENT",
            f"chunk content sha256 {actual_sha} != manifest payload_sha256 {sha}",
        )
        chunk_cache[sha] = (records, corruption)
        return records, corruption

    scanned = scan_payload(data)
    if scanned["has_trailing_partial"]:
        reject(
            "MANIFEST_MISMATCH",
            "chunk has a trailing partial record (file does not end with newline)",
        )
        chunk_cache[sha] = (records, corruption)
        return records, corruption
    if scanned["record_count"] != manifest["record_count"]:
        reject(
            "MANIFEST_MISMATCH",
            f"record count {scanned['record_count']} != manifest record_count "
            f"{manifest['record_count']}",
        )
        chunk_cache[sha] = (records, corruption)
        return records, corruption
    if len(data) != manifest["payload_byte_length"]:
        reject(
            "MANIFEST_MISMATCH",
            f"byte length {len(data)} != manifest payload_byte_length "
            f"{manifest['payload_byte_length']}",
        )
        chunk_cache[sha] = (records, corruption)
        return records, corruption

    sequence_semantics = manifest["sequence_semantics"]
    offset = 0
    for line in data.split(b"\n")[:-1]:
        line_offset = offset
        offset += len(line) + 1
        try:
            event = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            record = _corrupt_record(manifest_id, sha, line_offset, "MALFORMED_SHAPE",
                                     f"record is not valid JSON: {exc}")
            corruption.append(record)
            _route(record, routed, on_corrupt)
            continue
        if canonical_json(event).encode("utf-8") != line:
            record = _corrupt_record(manifest_id, sha, line_offset, "MALFORMED_SHAPE",
                                     "record bytes are not canonical_json form")
            corruption.append(record)
            _route(record, routed, on_corrupt)
            continue
        defect = _structural_event_check(event, sequence_semantics)
        if defect is not None:
            record = _corrupt_record(manifest_id, sha, line_offset, "MALFORMED_SHAPE", defect)
            corruption.append(record)
            _route(record, routed, on_corrupt)
            continue
        records.append((event, line_offset))

    chunk_cache[sha] = (records, corruption)
    return records, corruption


def _sequence_semantic_flags(manifest: Mapping[str, Any], entries: List[Any]) -> List[Dict[str, Any]]:
    """Gaps/resets only under sequence_semantics=CONTIGUOUS (freeze semantics)."""
    if manifest["sequence_semantics"] != "CONTIGUOUS":
        return []
    groups: Dict[Tuple[str, str, str, str], List[Any]] = {}
    for entry in entries:
        event = entry[0]
        key = (
            event["source_id"],
            event["venue"],
            event["instrument_id"],
            event["event_type"],
        )
        groups.setdefault(key, []).append(entry)
    flags: List[Dict[str, Any]] = []
    for key in sorted(groups):
        group = sorted(groups[key], key=lambda e: replay_order_key(e[0])[:7] + (e[0]["event_id"],))
        previous: Optional[int] = None
        for entry in group:
            event = entry[0]
            sequence = event.get("sequence_number")
            if sequence is None:
                # Illegal under CONTIGUOUS and already routed as corruption.
                continue
            if previous is not None and sequence <= previous:
                flags.append(
                    {
                        "manifest_id": manifest["manifest_id"],
                        "reason": "SEQUENCE_RESET",
                        "source_id": key[0],
                        "venue": key[1],
                        "instrument_id": key[2],
                        "detail": f"sequence {sequence} follows {previous} (non-increasing)",
                    }
                )
            elif previous is not None and sequence > previous + 1:
                missing = list(range(previous + 1, sequence))
                flags.append(
                    {
                        "manifest_id": manifest["manifest_id"],
                        "reason": "SEQUENCE_GAP",
                        "source_id": key[0],
                        "venue": key[1],
                        "instrument_id": key[2],
                        "detail": f"missing sequence numbers {missing}",
                    }
                )
            previous = sequence
    return flags


def _order_semantic_flags(manifest: Mapping[str, Any], entries: List[Any]) -> List[Dict[str, Any]]:
    """OUT_OF_ORDER_DELIVERY only under ordered_delivery=true (freeze semantics)."""
    if not manifest["ordered_delivery"]:
        return []
    file_order = [replay_order_key(entry[0]) for entry in entries]
    if file_order == sorted(file_order):
        return []
    first_bad = next(
        index for index in range(1, len(file_order)) if file_order[index] < file_order[index - 1]
    )
    event = entries[first_bad][0]
    return [
        {
            "manifest_id": manifest["manifest_id"],
            "reason": "OUT_OF_ORDER_DELIVERY",
            "source_id": event["source_id"],
            "venue": event["venue"],
            "instrument_id": event["instrument_id"],
            "detail": (
                f"file order violates total order at byte offset {entries[first_bad][1]} "
                "(manifest declares ordered_delivery=true)"
            ),
        }
    ]


def _run_replay(
    root: Path,
    manifest_ids: Sequence[str],
    predicate: Optional[Mapping[str, Any]],
    on_corrupt: Optional[Callable[[Mapping[str, Any]], None]],
) -> Tuple[Dict[str, Any], List[Mapping[str, Any]]]:
    """Single-pass core: returns (result, streamed_events).

    Exactly one pass so corruption routing side effects (callback calls or
    raises) happen exactly once regardless of which public wrapper is used.
    """
    root = Path(root)
    _validate_predicate(predicate)
    for manifest_id in manifest_ids:
        if not isinstance(manifest_id, str) or not manifest_id:
            raise ReplayInputError(f"manifest id must be a non-empty string: {manifest_id!r}")

    routed: List[Dict[str, Any]] = []
    duplicates: List[Dict[str, Any]] = []

    # Load manifests strictly by id from the explicit list; no discovery.
    loaded: "Dict[str, Dict[str, Any]]" = {}
    for manifest_id in manifest_ids:
        if manifest_id in loaded:
            continue
        try:
            loaded[manifest_id] = load_manifest(root, manifest_id)
        except ArchiveError as exc:
            record = _corrupt_record(manifest_id, None, None, "MANIFEST_MISMATCH", str(exc))
            _route(record, routed, on_corrupt)
        except ManifestValidationError as exc:
            record = _corrupt_record(manifest_id, None, None, exc.code, str(exc))
            _route(record, routed, on_corrupt)

    chunk_cache: Dict[str, Tuple[List[Any], List[Dict[str, Any]]]] = {}
    per_manifest_entries: Dict[str, List[Any]] = {}
    all_entries: List[Any] = []
    for manifest_id, manifest in loaded.items():
        records, _corruption = _load_chunk_records(root, manifest, chunk_cache, routed, on_corrupt)
        entries = [(event, offset, manifest["payload_sha256"]) for event, offset in records]
        per_manifest_entries[manifest_id] = entries
        all_entries.extend(entries)

    # Total order over all valid events; event_id is the final tie-break.
    all_entries.sort(key=lambda entry: replay_order_key(entry[0]))

    seen_event_ids: set = set()
    streamed: List[Mapping[str, Any]] = []
    for event, _offset, chunk_sha in all_entries:
        event_id = event["event_id"]
        if event_id in seen_event_ids:
            record = _corrupt_record(
                None,
                chunk_sha,
                None,
                "DUPLICATE_EVENT",
                f"event_id {event_id} already streamed; second occurrence routed, first streams",
            )
            record["event_id"] = event_id
            duplicates.append(record)
            _route(record, routed, on_corrupt)
            continue
        seen_event_ids.add(event_id)
        if predicate is None or all(event.get(key) == value for key, value in predicate.items()):
            streamed.append(event)

    stream_bytes = b"".join(canonical_line_bytes(event) for event in streamed)

    semantic_flags: List[Dict[str, Any]] = []
    for manifest_id in sorted(per_manifest_entries):
        manifest = loaded[manifest_id]
        entries = per_manifest_entries[manifest_id]
        semantic_flags.extend(_sequence_semantic_flags(manifest, entries))
        semantic_flags.extend(_order_semantic_flags(manifest, entries))
    semantic_flags.sort(key=lambda flag: (flag["manifest_id"], flag["reason"], flag["detail"]))

    chunk_digests = []
    for sha, (records, corruption) in chunk_cache.items():
        manifest_ids_for_sha = sorted(
            m["manifest_id"] for m in loaded.values() if m["payload_sha256"] == sha
        )
        chunk_digests.append(
            {
                "manifest_ids": manifest_ids_for_sha,
                "chunk_sha256": sha,
                "record_count": len(records) + len(corruption),
                "event_count": len(records),
                "corrupt_record_count": len(corruption),
            }
        )
    chunk_digests.sort(key=lambda item: item["chunk_sha256"])

    result = {
        "manifest_ids": list(manifest_ids),
        "predicate": dict(predicate) if isinstance(predicate, Mapping) else predicate,
        "stream_digest": hashlib.sha256(stream_bytes).hexdigest(),
        "stream_byte_length": len(stream_bytes),
        "event_count": len(streamed),
        "chunk_digests": chunk_digests,
        "input_complete": not routed,
        "quarantined": sorted(
            routed,
            key=lambda record: (
                record.get("manifest_id") or "",
                -1 if record.get("byte_offset") is None else record["byte_offset"],
                record.get("reason", ""),
            ),
        ),
        "duplicates": sorted(
            duplicates, key=lambda record: (record.get("chunk_sha256") or "", record["event_id"])
        ),
        "semantic_flags": semantic_flags,
        "order_key_fields": list(REPLAY_ORDER_FIELDS),
    }
    return result, streamed


def replay(
    root: Path,
    manifest_ids: Sequence[str],
    predicate: Optional[Mapping[str, Any]] = None,
    *,
    on_corrupt: Optional[Callable[[Mapping[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """Deterministic replay over an explicit manifest list + predicate.

    Returns a result dict recording exactly the inputs (``manifest_ids`` in
    the given order, ``predicate`` verbatim), the ``stream_digest`` over the
    exact canonical byte stream, per-chunk digests, the event count, routed
    corruption/duplicate records and manifest-semantics flags.

    Only the named manifests and their referenced chunk files are read.
    Duplicates (repeated event_id): first occurrence in the total order
    streams; later occurrences route to ``on_corrupt`` as DUPLICATE_EVENT,
    or raise CorruptReplayInput when no callback is supplied.
    """
    result, _events = _run_replay(root, manifest_ids, predicate, on_corrupt)
    return result


def replay_events(
    root: Path,
    manifest_ids: Sequence[str],
    predicate: Optional[Mapping[str, Any]] = None,
    *,
    on_corrupt: Optional[Callable[[Mapping[str, Any]], None]] = None,
) -> List[Mapping[str, Any]]:
    """The exact total-ordered, predicate-filtered event list for a replay.

    Same inputs and corruption routing as ``replay`` (one pass, one set of
    side effects); returns the events so callers can rebuild the canonical
    stream bytes and compare digests directly.
    """
    _result, events = _run_replay(root, manifest_ids, predicate, on_corrupt)
    return events
