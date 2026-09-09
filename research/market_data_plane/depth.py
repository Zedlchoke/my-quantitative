"""Market-by-level depth view (MDP-V1 lane A4).

Frozen contract (``bbo_contract.depth`` and plans/PLAN_market_data_plane_v1.md
section 7.3):

- L1 is required and is always produced by the BBO view
  (``research.market_data_plane.bbo``); this module attaches it but never
  gates it -- see :func:`evaluate_l1`;
- L2/depth is optional and reports ``NOT_EVALUABLE`` unless PROVEN
  snapshot/delta sequence semantics are supplied as explicit input flags by
  the caller (``snapshot_proven=True`` AND ``sequence_contiguous=True``);
- depth updates require snapshot/delta and sequence semantics to be proven per
  source; this module additionally verifies actual sequence contiguity of the
  supplied deltas and refuses on a detected gap (defense in depth behind the
  caller's flag);
- aggregate interval records (candles) are not a depth source and can never
  become one: this module has no synthesis path for them.  Any input that is
  not depth-shaped fails the proven-semantics gate and is reported as
  ``NOT_EVALUABLE`` -- never a guessed book.

Return protocol: every unevaluable outcome is a :class:`NotEvaluable` sentinel
carrying a machine-readable ``reason`` (and optional ``detail``); the sentinel
is falsy.  It is information, never an exception, and never a silent zero.

Arithmetic policy: level prices/sizes are ``decimal.Decimal`` parsed from the
canonical decimal strings of the frozen envelope.  No binary float appears in
any output of this module.

Import isolation: standard library only (plus sibling ``bbo`` for L1).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .bbo import VenueBook, parse_decimal

__all__ = [
    "NotEvaluable",
    "DepthView",
    "evaluate_depth",
    "evaluate_l1",
    "DEPTH_SEMANTICS_UNPROVEN",
    "MALFORMED_DEPTH_RECORD",
    "SEQUENCE_GAP_DETECTED",
    "MISSING_BBO_EVIDENCE",
    "MISSING_CLOCK_EVIDENCE",
]

DEPTH_SEMANTICS_UNPROVEN = "DEPTH_SEMANTICS_UNPROVEN"
MALFORMED_DEPTH_RECORD = "MALFORMED_DEPTH_RECORD"
SEQUENCE_GAP_DETECTED = "SEQUENCE_GAP_DETECTED"
MISSING_BBO_EVIDENCE = "MISSING_BBO_EVIDENCE"
MISSING_CLOCK_EVIDENCE = "MISSING_CLOCK_EVIDENCE"


@dataclass(frozen=True)
class NotEvaluable:
    """Falsy sentinel returned instead of guessing a value.

    ``reason`` is a stable machine-readable code; substituting a zero (or any
    fabricated number) for missing evidence is forbidden by the frozen
    contracts, so every missing-evidence path returns this sentinel.
    """

    reason: str
    detail: str = ""

    def __bool__(self) -> bool:  # pragma: no cover - trivial
        return False


@dataclass(frozen=True)
class DepthView:
    """Depth evaluation result for one proven snapshot/delta stream.

    ``l1``: consolidated BBO dict from the BBO view, or a :class:`NotEvaluable`
    explaining why the BBO evidence was absent (L1 itself never depends on the
    depth inputs; obtain it unconditionally via :func:`evaluate_l1`).
    ``l2``: market-by-level dict of exact ``Decimal`` price/size levels, or a
    :class:`NotEvaluable` sentinel.
    """

    l1: Any
    l2: Any


def _as_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be integer nanoseconds, got {value!r}")
    return value


def _parse_levels(raw: Any, side: str) -> List[Tuple[Any, Any]]:
    if not isinstance(raw, list):
        raise TypeError(f"snapshot {side} must be a list of [price, size] pairs")
    out: List[Tuple[Any, Any]] = []
    for entry in raw:
        if not isinstance(entry, (list, tuple)) or len(entry) != 2:
            raise TypeError(f"snapshot {side} entry must be a [price, size] pair")
        price = parse_decimal(entry[0], f"{side}_level_price")
        size = parse_decimal(entry[1], f"{side}_level_size")
        if price < 0 or size < 0:
            raise ValueError(f"negative {side} level value")
        out.append((price, size))
    return out


def _build_l2(depth_inputs: Mapping[str, Any]) -> Any:
    """Build the market-by-level view from proven inputs (or return sentinel)."""
    snapshot = depth_inputs.get("snapshot")
    deltas = depth_inputs.get("deltas")
    if not isinstance(snapshot, Mapping):
        return NotEvaluable(
            MALFORMED_DEPTH_RECORD,
            "snapshot must be a mapping with bids/asks/sequence_number",
        )
    if not isinstance(deltas, list):
        return NotEvaluable(MALFORMED_DEPTH_RECORD, "deltas must be a list of delta mappings")
    for key in ("venue", "instrument_id", "sequence_number"):
        if snapshot.get(key) is None:
            return NotEvaluable(MALFORMED_DEPTH_RECORD, f"snapshot missing {key}")

    try:
        snap_seq = _as_int(snapshot["sequence_number"], "snapshot sequence_number")
        bids = dict(_parse_levels(snapshot.get("bids", []), "bid"))
        asks = dict(_parse_levels(snapshot.get("asks", []), "ask"))
    except (TypeError, ValueError) as exc:
        return NotEvaluable(MALFORMED_DEPTH_RECORD, str(exc))

    ordered: List[Mapping[str, Any]] = []
    for delta in deltas:
        if not isinstance(delta, Mapping):
            return NotEvaluable(MALFORMED_DEPTH_RECORD, "each delta must be a mapping")
        try:
            seq = _as_int(delta.get("sequence_number"), "delta sequence_number")
        except TypeError as exc:
            return NotEvaluable(MALFORMED_DEPTH_RECORD, str(exc))
        ordered.append(dict(delta, _seq=seq))
    ordered.sort(key=lambda d: (d["_seq"], str(d.get("event_id", ""))))

    expected = snap_seq + 1
    for delta in ordered:
        seq = delta["_seq"]
        if seq != expected:
            return NotEvaluable(
                SEQUENCE_GAP_DETECTED,
                f"expected delta sequence {expected}, got {seq}",
            )
        expected += 1
        side = delta.get("side")
        action = delta.get("action")
        if side not in ("bid", "ask") or action not in ("set", "remove"):
            return NotEvaluable(
                MALFORMED_DEPTH_RECORD,
                "delta needs side in {bid, ask} and action in {set, remove}",
            )
        levels = bids if side == "bid" else asks
        try:
            price = parse_decimal(delta.get("price"), "delta_price")
        except ValueError as exc:
            return NotEvaluable(MALFORMED_DEPTH_RECORD, str(exc))
        if action == "set":
            if delta.get("size") is None:
                return NotEvaluable(MALFORMED_DEPTH_RECORD, "set delta requires size")
            try:
                size = parse_decimal(delta["size"], "delta_size")
            except ValueError as exc:
                return NotEvaluable(MALFORMED_DEPTH_RECORD, str(exc))
            if size < 0:
                return NotEvaluable(MALFORMED_DEPTH_RECORD, "negative delta size")
            levels[price] = size
        else:  # remove of an absent level is a deterministic no-op
            levels.pop(price, None)

    last_seq = ordered[-1]["_seq"] if ordered else snap_seq
    bids_out = [[p, s] for p, s in sorted(bids.items(), key=lambda kv: kv[0], reverse=True)]
    asks_out = [[p, s] for p, s in sorted(asks.items(), key=lambda kv: kv[0])]
    return {
        "venue": snapshot["venue"],
        "instrument_id": snapshot["instrument_id"],
        "currency": snapshot.get("currency"),
        "bids": bids_out,
        "asks": asks_out,
        "sequence_number": last_seq,
        "snapshot_sequence_number": snap_seq,
        "delta_count": len(ordered),
        "level_counts": {"bids": len(bids_out), "asks": len(asks_out)},
    }


def evaluate_depth(
    depth_inputs: Any = None,
    *,
    staleness_threshold_ns: int,
    l1_book: Optional[VenueBook] = None,
    l1_venues: Iterable[str] = (),
    l1_permitted_venues: Optional[Any] = None,
    l1_now_ns: Optional[int] = None,
    l1_instrument_id: Optional[str] = None,
) -> Any:
    """Evaluate the depth view for one instrument.

    ``depth_inputs`` must carry PROVEN snapshot/delta sequence semantics as
    explicit caller-supplied flags::

        {"snapshot_proven": True, "sequence_contiguous": True,
         "snapshot": {"venue": ..., "instrument_id": ..., "currency": ...,
                      "sequence_number": int,
                      "bids": [["100.00", "5"], ...],    # exact decimal strings
                      "asks": [["100.02", "4"], ...]},
         "deltas": [{"side": "bid"|"ask", "action": "set"|"remove",
                     "price": "...", "size": "...",   # size required for set
                     "sequence_number": int, "event_id": ...}, ...]}

    Returns a :class:`NotEvaluable` sentinel (reason ``DEPTH_SEMANTICS_UNPROVEN``
    or ``MALFORMED_DEPTH_RECORD`` / ``SEQUENCE_GAP_DETECTED``) unless the flags
    are both explicitly True and the payload is depth-shaped -- aggregate
    interval records and any other shape simply fail the gate and are never
    turned into a book.  On success returns a :class:`DepthView` whose ``l2``
    holds exact ``Decimal`` levels and whose ``l1`` holds the BBO-view result
    (or a sentinel explaining the absent BBO evidence).
    ``staleness_threshold_ns`` is REQUIRED with no default (it parameterises
    the attached L1 evaluation, mirroring the frozen BBO contract).
    """
    unproven = NotEvaluable(
        DEPTH_SEMANTICS_UNPROVEN,
        "depth evaluation requires explicit snapshot_proven=True and "
        "sequence_contiguous=True supplied by the caller",
    )
    if not isinstance(depth_inputs, Mapping):
        return unproven
    if depth_inputs.get("snapshot_proven") is not True:
        return unproven
    if depth_inputs.get("sequence_contiguous") is not True:
        return unproven

    l2 = _build_l2(depth_inputs)
    if isinstance(l2, NotEvaluable):
        # proven flags claimed but the payload is malformed or the sequence is
        # broken: the depth view as a whole is NOT_EVALUABLE (never a guess)
        return l2

    if l1_book is None:
        l1: Any = NotEvaluable(
            MISSING_BBO_EVIDENCE,
            "L1 comes from the BBO view; pass l1_book (research.market_data_plane.bbo.VenueBook) "
            "to attach it, or call evaluate_l1 directly",
        )
    elif l1_now_ns is None:
        l1 = NotEvaluable(MISSING_CLOCK_EVIDENCE, "l1_now_ns is required to evaluate L1")
    else:
        instrument = l1_instrument_id or l2["instrument_id"]
        permitted = (
            l1_permitted_venues
            if l1_permitted_venues is not None
            else {str(v) for v in l1_venues}
        )
        l1 = l1_book.consolidated_bbo(
            l1_venues,
            instrument,
            permitted,
            l1_now_ns,
            staleness_threshold_ns,
        )
    return DepthView(l1=l1, l2=l2)


def evaluate_l1(
    book: VenueBook,
    venues: Iterable[str],
    instrument_id: str,
    permitted_venues: Any,
    now_ns: int,
    staleness_threshold_ns: int,
) -> Dict[str, Any]:
    """L1 is always available from the BBO view, independent of depth inputs.

    Thin delegation to :meth:`bbo.VenueBook.consolidated_bbo` with the required
    (no-default) staleness threshold.
    """
    return book.consolidated_bbo(
        venues,
        instrument_id,
        permitted_venues,
        now_ns,
        staleness_threshold_ns,
    )
