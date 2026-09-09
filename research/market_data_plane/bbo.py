"""Venue-local and consolidated best-bid/offer views (MDP-V1 lane A4).

Frozen contract (research/control/market_data_plane_v1_run/architecture_freeze.json,
``bbo_contract`` and plans/PLAN_market_data_plane_v1.md section 7.3):

- venue-local BBO per (venue, instrument): the last non-stale quote wins; ties
  are broken by ``(exchange_time_utc_ns, receive_time_utc_ns, event_id)``;
- consolidated BBO is the union of venue-locals whose venue is in
  ``permitted_venues`` and identity-compatible (same ``instrument_id`` AND same
  ``currency``); best bid = max bid, best ask = min ask; the contributing quote
  event IDs are recorded per side;
- a crossed CONSOLIDATED result is information, not an error: it is reported
  as-is with ``crossed=True`` and its contributors.  Cross-venue price
  disagreement must NEVER raise ``CROSSED_QUOTE`` (that reason code is reserved
  by the frozen quality layer for ``bid >= ask`` inside ONE venue+instrument
  quote and is owned by A2, not by this view);
- ``staleness_threshold_ns`` is a REQUIRED parameter of every evaluation call
  (no hidden default).  A quote is stale iff its ``exchange_time_utc_ns`` is
  older than ``now_ns - staleness_threshold_ns`` (equality at the boundary is
  fresh).

Arithmetic policy: all price/size values are parsed into ``decimal.Decimal``
from the canonical decimal strings of the frozen 27-field envelope
(``mdp.market_event@1``, plain dicts here -- A2's models module is not a
dependency of this lane).  No binary float ever participates in a computed
view output: consolidated bid/ask are returned as ``Decimal``.  Views never
persist anything, so no string re-canonicalisation happens here.

Import isolation: this module imports the standard library only (no pandas,
pandera, dvc, nautilus_trader).
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

__all__ = [
    "parse_decimal",
    "quote_sort_key",
    "is_quote_stale",
    "VenueBook",
    "venue_asof_quote",
]

# quality_status values that may contribute evidence.  The frozen quality
# layer rejects INVALID/QUARANTINED events; if they still reach a view they
# are ignored (a view consumes evidence, it does not rehabilitate it).
# SUSPECT events remain usable (flag_suspect is a flag, not a rejection).
_USABLE_STATUSES = frozenset({"VALID", "SUSPECT"})

_QUOTE_REQUIRED_FIELDS = (
    "event_id",
    "venue",
    "instrument_id",
    "exchange_time_utc_ns",
    "receive_time_utc_ns",
    "bid_price",
    "ask_price",
    "bid_size",
    "ask_size",
)


def parse_decimal(value: Any, field: str = "price") -> Decimal:
    """Parse a canonical decimal evidence value into an exact ``Decimal``.

    Accepts ``str`` (canonical fixed-point, no exponent form), ``int``,
    ``Decimal``; ``float`` is converted via ``Decimal(repr(x))`` exactly as the
    frozen field rules prescribe (then it is never touched by float math
    again).  Canonical strings in exponent form, non-finite values and bools
    are rejected -- malformed evidence must fail loudly, not silently coerce.
    """
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError(f"non-finite {field}: {value!r}")
        return value
    if isinstance(value, bool):
        raise ValueError(f"bool is not a decimal evidence value for {field}")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        # Frozen rule: float input converts via Decimal(repr(x)) and is then
        # validated; no float arithmetic happens downstream of this point.
        d = Decimal(repr(value))
        if not d.is_finite():
            raise ValueError(f"non-finite {field}: {value!r}")
        return d
    if isinstance(value, str):
        if "e" in value or "E" in value:
            raise ValueError(
                f"{field} must be canonical fixed-point without exponent form: {value!r}"
            )
        try:
            d = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError(f"malformed decimal string for {field}: {value!r}") from exc
        if not d.is_finite():
            raise ValueError(f"non-finite {field}: {value!r}")
        return d
    raise ValueError(f"unsupported evidence type for {field}: {type(value)!r}")


def _as_int_ns(value: Any, field: str) -> int:
    """Validate a nanosecond clock field: exact int, never float/bool/str."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be integer UTC nanoseconds, got {value!r}")
    return value


def quote_sort_key(event: Mapping[str, Any]) -> Tuple[int, int, str]:
    """Deterministic venue-local order key (frozen tie-break)."""
    return (
        _as_int_ns(event["exchange_time_utc_ns"], "exchange_time_utc_ns"),
        _as_int_ns(event["receive_time_utc_ns"], "receive_time_utc_ns"),
        str(event["event_id"]),
    )


def is_quote_stale(exchange_time_utc_ns: int, now_ns: int, staleness_threshold_ns: int) -> bool:
    """Frozen staleness rule: stale iff ``et < now_ns - staleness_threshold_ns``.

    Equality at ``now_ns - staleness_threshold_ns`` is fresh (the quote is not
    *older than* the threshold window).  The threshold is always an explicit
    input; there is no hidden default anywhere in this module.
    """
    _as_int_ns(exchange_time_utc_ns, "exchange_time_utc_ns")
    _as_int_ns(now_ns, "now_ns")
    _as_int_ns(staleness_threshold_ns, "staleness_threshold_ns")
    return exchange_time_utc_ns < now_ns - staleness_threshold_ns


def _parse_quote_view(event: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate a QUOTE event dict and pre-parse its exact Decimal fields."""
    if event.get("event_type") != "QUOTE":
        raise ValueError(f"VenueBook consumes QUOTE events only, got {event.get('event_type')!r}")
    missing = [f for f in _QUOTE_REQUIRED_FIELDS if event.get(f) is None]
    if missing:
        raise ValueError(f"QUOTE event missing required fields: {sorted(missing)}")
    return {
        "event_id": str(event["event_id"]),
        "venue": str(event["venue"]),
        "instrument_id": str(event["instrument_id"]),
        "currency": event.get("currency"),
        "exchange_time_utc_ns": _as_int_ns(event["exchange_time_utc_ns"], "exchange_time_utc_ns"),
        "receive_time_utc_ns": _as_int_ns(event["receive_time_utc_ns"], "receive_time_utc_ns"),
        "bid": parse_decimal(event["bid_price"], "bid_price"),
        "ask": parse_decimal(event["ask_price"], "ask_price"),
        "bid_size": parse_decimal(event["bid_size"], "bid_size"),
        "ask_size": parse_decimal(event["ask_size"], "ask_size"),
        # Diagnostic only: per-venue crossedness (bid >= ask inside ONE
        # venue+instrument quote).  Reporting it here is information; the
        # CROSSED_QUOTE reason code itself belongs to the A2 quality layer.
        "crossed": parse_decimal(event["bid_price"], "bid_price")
        >= parse_decimal(event["ask_price"], "ask_price"),
    }


class VenueBook:
    """Venue-local BBO book keyed by ``(venue, instrument_id)``.

    Only the winning quote per key is retained: the maximum of the frozen
    total order key ``(exchange_time_utc_ns, receive_time_utc_ns, event_id)``.
    Because ``event_id`` is unique, ``apply_quote`` is deterministic and
    independent of arrival order: a late-arriving older quote never replaces a
    newer winner.  Staleness is evaluated at EVALUATION time (the threshold is
    an evaluation-call parameter), not at ingest time.
    """

    def __init__(self) -> None:
        self._latest: Dict[Tuple[str, str], Dict[str, Any]] = {}

    def apply_quote(self, event: Mapping[str, Any]) -> bool:
        """Apply one QUOTE event dict.  Returns True if it became the winner.

        Events with quality_status INVALID/QUARANTINED are ignored (return
        False).  Malformed evidence raises ValueError -- views fail loudly
        instead of guessing.
        """
        status = event.get("quality_status")
        if status is not None and status not in _USABLE_STATUSES:
            return False
        view = _parse_quote_view(event)
        key = quote_sort_key(event)
        book_key = (view["venue"], view["instrument_id"])
        current = self._latest.get(book_key)
        if current is not None and key <= current["_key"]:
            return False
        stored = dict(view)
        stored["_key"] = key
        self._latest[book_key] = stored
        return True

    def venue_local(self, venue: str, instrument_id: str) -> Optional[Dict[str, Any]]:
        """Stored venue-local winner without staleness evaluation (or None)."""
        stored = self._latest.get((str(venue), str(instrument_id)))
        if stored is None:
            return None
        out = {k: v for k, v in stored.items() if k != "_key"}
        return out

    def evaluate_venue_local(
        self,
        venue: str,
        instrument_id: str,
        now_ns: int,
        staleness_threshold_ns: int,
    ) -> Optional[Dict[str, Any]]:
        """Venue-local winner if fresh at ``now_ns`` under the threshold, else None."""
        stored = self._latest.get((str(venue), str(instrument_id)))
        if stored is None:
            return None
        if is_quote_stale(stored["exchange_time_utc_ns"], now_ns, staleness_threshold_ns):
            return None
        out = {k: v for k, v in stored.items() if k != "_key"}
        return out

    def consolidated_bbo(
        self,
        venues: Iterable[str],
        instrument_id: str,
        permitted_venues: Any,
        now_ns: int,
        staleness_threshold_ns: int,
    ) -> Dict[str, Any]:
        """Consolidated BBO over candidate ``venues`` (frozen contract).

        Parameters are positional-or-keyword with NO defaults for ``now_ns``
        and ``staleness_threshold_ns`` -- the staleness threshold is a required
        input of every evaluation call.

        Only candidate venues that are in ``permitted_venues`` AND hold a
        fresh venue-local quote for ``instrument_id`` participate.
        Identity compatibility is: same ``instrument_id`` (inherent in the
        book key) AND same ``currency``.  The reference currency is the
        currency of the fresh venue-local with the lexicographically smallest
        venue name, so the result is deterministic and independent of input
        order; venue-locals with a different (or unproven-against-anchor)
        currency are excluded -- no conversion is ever assumed.  A ``None``
        currency is only compatible with another ``None``.

        Returns exactly::

            {"bid": Decimal|None, "ask": Decimal|None,
             "bid_contributors": [event_id, ...],   # ties all recorded, sorted
             "ask_contributors": [event_id, ...],
             "venues_used": [venue, ...],           # sorted
             "skipped_stale_count": int,
             "crossed": bool,
             "reference_currency": str|None}   # recorded per A1 ruling A4_Q2

        ``crossed`` mirrors the frozen convention (``bid >= ask``, so a locked
        book also reports True).  A crossed CONSOLIDATED result is reported
        as-is -- this function never raises CROSSED_QUOTE; cross-venue price
        disagreement is information carried by the contributors.
        """
        _as_int_ns(now_ns, "now_ns")
        _as_int_ns(staleness_threshold_ns, "staleness_threshold_ns")
        cutoff = now_ns - staleness_threshold_ns
        skipped_stale = 0
        fresh: List[Dict[str, Any]] = []
        for venue in sorted({str(v) for v in venues}):
            if venue not in permitted_venues:
                continue
            stored = self._latest.get((venue, str(instrument_id)))
            if stored is None:
                continue
            if stored["exchange_time_utc_ns"] < cutoff:
                skipped_stale += 1
                continue
            fresh.append(stored)

        if not fresh:
            return {
                "bid": None,
                "ask": None,
                "bid_contributors": [],
                "ask_contributors": [],
                "venues_used": [],
                "skipped_stale_count": skipped_stale,
                "crossed": False,
                "reference_currency": None,
            }

        anchor_currency = fresh[0]["currency"]
        compatible = [q for q in fresh if q["currency"] == anchor_currency]
        # A1 ruling (a1_rulings.json A4_Q2, MDP-V1): the chosen reference
        # currency is RECORDED so currency exclusion is observable, not silent.
        # fresh[] is built over sorted venue names, so fresh[0] is the fresh
        # venue-local with the lexicographically smallest venue name.

        best_bid = max(q["bid"] for q in compatible)
        best_ask = min(q["ask"] for q in compatible)
        bid_contributors = [q["event_id"] for q in compatible if q["bid"] == best_bid]
        ask_contributors = [q["event_id"] for q in compatible if q["ask"] == best_ask]
        return {
            "bid": best_bid,
            "ask": best_ask,
            "bid_contributors": bid_contributors,
            "ask_contributors": ask_contributors,
            "venues_used": sorted({q["venue"] for q in compatible}),
            "skipped_stale_count": skipped_stale,
            "crossed": best_bid >= best_ask,
            "reference_currency": anchor_currency,
        }


def venue_asof_quote(
    quotes: Iterable[Mapping[str, Any]],
    venue: str,
    instrument_id: str,
    at_ns: int,
    staleness_threshold_ns: int,
) -> Optional[Mapping[str, Any]]:
    """Point-in-time venue-local quote: the deterministic winner known at ``at_ns``.

    A quote qualifies iff its venue/instrument match, its quality_status is
    usable, and ``at_ns - staleness_threshold_ns <= exchange_time_utc_ns <=
    at_ns`` (both boundaries inclusive).  The winner is the maximum by
    ``(exchange_time_utc_ns, receive_time_utc_ns, event_id)``.  Returns the
    original event dict, or None when no fresh quote exists.  Used by the TCA
    view for arrival / at-fill / at-horizon evidence.
    """
    _as_int_ns(at_ns, "at_ns")
    _as_int_ns(staleness_threshold_ns, "staleness_threshold_ns")
    lower = at_ns - staleness_threshold_ns
    best: Optional[Mapping[str, Any]] = None
    best_key: Optional[Tuple[int, int, str]] = None
    for event in quotes:
        if event.get("event_type") != "QUOTE":
            continue
        if event.get("venue") != venue or event.get("instrument_id") != instrument_id:
            continue
        status = event.get("quality_status")
        if status is not None and status not in _USABLE_STATUSES:
            continue
        if event.get("event_id") is None:
            continue
        et = _as_int_ns(event["exchange_time_utc_ns"], "exchange_time_utc_ns")
        rt = _as_int_ns(event["receive_time_utc_ns"], "receive_time_utc_ns")
        if et > at_ns or et < lower:
            continue
        key = (et, rt, str(event["event_id"]))
        if best_key is None or key > best_key:
            best, best_key = event, key
    return best
