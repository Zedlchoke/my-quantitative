"""Canonical JSON + frozen replay order key for MDP-V1 (lane A3 internal helper).

The lane contract limits this module to EXACTLY two frozen conventions:

1. ``canonical_json``  -- freeze ``schemas.canonical_json``:
   ``json.dumps(obj, sort_keys=True, separators=(',',':'), ensure_ascii=True,
   allow_nan=False)``.
2. ``replay_order_key`` -- freeze ``replay_contract.total_order_key``:
   (exchange_time_utc_ns, receive_time_utc_ns, available_time_utc_ns,
   source_id, venue, instrument_id, event_type, sequence_number, event_id)
   with ``event_id`` as the final total tie-break.

Source of truth:
``research/control/market_data_plane_v1_run/architecture_freeze.json``
(sha256 7f7403e67bfb9707b547b6762cc0a3c87f2c96f701b3f1ec3ad2197478736c02).

A1 reconciles helper placement at integration; no other functionality may be
added here. This module imports stdlib only (event-stream hot-path import
isolation rule).

Documented deviation surfaced to A1 (not a silent spec change): the freeze
does not state how a null ``sequence_number`` (legal only under
``sequence_semantics=NONE`` manifests) sorts against integers in the total
order. Python tuple comparison raises ``TypeError`` on ``None`` vs ``int``,
so the key maps null sequence to the sentinel ``-1`` (null sorts before all
legal sequence numbers, which are ``int >= 0``). A1 must ratify or replace
this choice at integration.
"""
from __future__ import annotations

import json
from typing import Any, Mapping, Tuple

__all__ = ["canonical_json", "canonical_line_bytes", "replay_order_key", "REPLAY_ORDER_FIELDS"]

CANONICAL_JSON_KWARGS = {
    "sort_keys": True,
    "separators": (",", ":"),
    "ensure_ascii": True,
    "allow_nan": False,
}

# Freeze replay_contract.total_order_key (exact field order).
REPLAY_ORDER_FIELDS: Tuple[str, ...] = (
    "exchange_time_utc_ns",
    "receive_time_utc_ns",
    "available_time_utc_ns",
    "source_id",
    "venue",
    "instrument_id",
    "event_type",
    "sequence_number",
    "event_id",
)

# Sentinel for null sequence_number in the total order (see module docstring).
_NULL_SEQUENCE_SENTINEL = -1


def canonical_json(obj: Any) -> str:
    """Frozen canonical JSON serialization (freeze schemas.canonical_json)."""
    return json.dumps(obj, **CANONICAL_JSON_KWARGS)


def canonical_line_bytes(obj: Any) -> bytes:
    """Exact newline-delimited canonical bytes for one stream record.

    The freeze defines the replay stream as ``canonical_json + "\\n"`` per
    event; chunk payloads use the same record framing.
    """
    return (canonical_json(obj) + "\n").encode("utf-8")


def replay_order_key(event: Mapping[str, Any]) -> Tuple[Any, ...]:
    """Frozen total order key (replay_contract.total_order_key).

    ``event_id`` is the final tie-break, making the order total, stable and
    independent of input file order. Null ``sequence_number`` maps to -1
    (documented deviation above).
    """
    sequence = event.get("sequence_number")
    sequence_key = _NULL_SEQUENCE_SENTINEL if sequence is None else sequence
    return (
        event["exchange_time_utc_ns"],
        event["receive_time_utc_ns"],
        event["available_time_utc_ns"],
        event["source_id"],
        event["venue"],
        event["instrument_id"],
        event["event_type"],
        sequence_key,
        event["event_id"],
    )
