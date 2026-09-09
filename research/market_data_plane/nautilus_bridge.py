"""NautilusTrader bridge for canonical MDP-V1 events (frozen mapping).

Freeze authority: research/control/market_data_plane_v1_run/architecture_freeze.json
(sha256 7f7403e67bfb9707b547b6762cc0a3c87f2c96f701b3f1ec3ad2197478736c02),
section "nautilus_bridge_contract", and plans/PLAN_market_data_plane_v1.md
section 8.  Target: nautilus_trader==1.230.0 exactly (verified signatures are
recorded in docs/MDP_BRIDGE_NOTES.md and asserted by the bridge tests).

Frozen mapping (section nautilus_bridge_contract.mappings):

* ``QUOTE  -> QuoteTick`` — bid/ask Price and sizes built from the INSTRUMENT
  metadata precisions (the instrument argument is mandatory, no defaults);
  ``ts_event = exchange_time_utc_ns``, ``ts_init = available_time_utc_ns``;
  there is no implicit ``now()`` anywhere in this module.
* ``TRADE -> TradeTick`` — price/size via instrument precisions; aggressor
  side mapped ``buy -> AggressorSide.BUYER``, ``sell -> AggressorSide.SELLER``,
  absent side -> ``AggressorSide.NO_AGGRESSOR`` (nautilus enum).
* ``Bar`` — NOT mapped in @1: the plane has no canonical BAR event type, so
  OHLCV can never become quotes or depth (:func:`to_bar` always raises).

Frozen rules honoured here:

* Lossless decimals: canonical decimal STRINGS are converted to nautilus
  ``Price``/``Quantity`` through exact ``Decimal`` arithmetic at the
  instrument's precision.  nautilus 1.230.0 itself SILENTLY ROUNDS values
  that are not representable at the requested precision (verified:
  ``Price(Decimal('0.15'), 1) -> 0.2``), so this bridge pre-checks
  representability AND post-verifies the constructed object; any drift
  raises :class:`BridgePrecisionError` — never a silent round.
* Quality gate: INVALID/QUARANTINED events raise
  (:class:`BridgeQualityError`) unless ``diagnostic_only=True`` is passed
  explicitly; in diagnostic-only mode they are EXCLUDED from the conversion
  output and recorded in a :class:`BridgeDiagnostics` sidecar — never
  silently streamed.  SUSPECT events stream, with their status recorded in
  the sidecar (a diagnostics sink is mandatory to stream SUSPECT events).
* No lookahead: the bridge never reorders and never substitutes timestamps;
  ``ts_init >= ts_event`` is enforced on every conversion.
* Import isolation: ``nautilus_trader`` is imported ONLY inside functions
  (freeze ``package.import_isolation``); importing this module in a fresh
  subprocess must not import nautilus_trader (golden-tested).
* No strategy, risk, portfolio, broker or execution code is introduced here.

This module is lane A8 property; it never mutates its inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import Any

from . import models as _models

__all__ = [
    "BAR_NOT_MAPPED_IN_V1",
    "BridgeDiagnostic",
    "BridgeDiagnostics",
    "BridgeLookaheadError",
    "BridgePrecisionError",
    "BridgeQualityError",
    "NautilusBridgeError",
    "convert_stream",
    "requires_instrument_metadata",
    "to_bar",
    "to_quote_tick",
    "to_trade_tick",
]

# --- frozen constants --------------------------------------------------------

#: Bar mapping is frozen OUT of @1 (plan section 8 + freeze mappings.Bar).
BAR_NOT_MAPPED_IN_V1 = (
    "mdp.market_event@1 has no BAR type; OHLCV can never become quotes/depth"
)

#: Diagnostic actions recorded in the sidecar (never a hidden state — the
#: sink object is always caller-owned and passed explicitly).
ACTION_CONVERTED = "CONVERTED"
ACTION_SUSPECT_STREAMED = "SUSPECT_STREAMED"
ACTION_REJECTED_EXCLUDED = "REJECTED_EXCLUDED"

#: nautilus Price/Quantity accept precision 0..16 (verified 1.230.0 docs).
_MAX_NAUTILUS_PRECISION = 16

#: nautilus 1.230.0 TradeId length cap is 36; the bridge uses a deterministic
#: 32-hex-char (128-bit) prefix of the canonical event_id sha256.
_TRADE_ID_PREFIX_LEN = 32

_INSTRUMENT_CONTRACT = (
    "instrument metadata is a MANDATORY bridge input (freeze rule: "
    "'instrument metadata (precisions, instrument_id) is a mandatory bridge "
    "input').  The instrument object must expose .id, .price_precision and "
    ".size_precision (any nautilus_trader 1.230.0 Instrument qualifies).  "
    "Canonical decimal strings are converted at the INSTRUMENT's precisions "
    "and raise BridgePrecisionError when not exactly representable there; "
    "event['instrument_id'] must equal str(instrument.id)."
)


# --- errors ------------------------------------------------------------------

class NautilusBridgeError(ValueError):
    """Base error for the nautilus bridge (fail-closed conversions)."""


class BridgePrecisionError(NautilusBridgeError):
    """A canonical decimal cannot map to the instrument precision losslessly."""


class BridgeQualityError(NautilusBridgeError):
    """The quality gate refused to stream an INVALID/QUARANTINED/SUSPECT event."""


class BridgeLookaheadError(NautilusBridgeError):
    """ts_init < ts_event on a conversion (frozen no-lookahead rule)."""


# --- diagnostics sidecar -----------------------------------------------------

@dataclass(frozen=True)
class BridgeDiagnostic:
    """One immutable sidecar record (quality-gate outcome for one event)."""

    event_id: str
    instrument_id: str
    event_type: str
    quality_status: str
    reason_codes: tuple[str, ...]
    action: str
    detail: str


class BridgeDiagnostics:
    """Caller-owned sidecar sink for quality-gate outcomes.

    The bridge never keeps hidden state: a diagnostics sink takes effect only
    when explicitly passed to a conversion call.  ``diagnostic_only=True``
    without a sink raises (an excluded event that is recorded nowhere would
    be silent — forbidden by the freeze).
    """

    __slots__ = ("records",)

    def __init__(self) -> None:
        self.records: list[BridgeDiagnostic] = []

    def record(
        self,
        event: dict,
        instrument_id: str,
        action: str,
        detail: str,
    ) -> BridgeDiagnostic:
        entry = BridgeDiagnostic(
            event_id=event["event_id"],
            instrument_id=instrument_id,
            event_type=event["event_type"],
            quality_status=event["quality_status"],
            reason_codes=tuple(event["reason_codes"]),
            action=action,
            detail=detail,
        )
        self.records.append(entry)
        return entry

    def by_action(self, action: str) -> list[BridgeDiagnostic]:
        return [r for r in self.records if r.action == action]


# --- frozen contract helper --------------------------------------------------

def requires_instrument_metadata() -> str:
    """Document the frozen instrument-metadata contract (mandatory input).

    The mapping functions take ``instrument`` as a required positional
    argument with NO default: there is deliberately no way to convert a
    canonical event without declaring the instrument precisions it must be
    rendered at.  Returns the contract text so callers/tests can assert it.
    """
    return _INSTRUMENT_CONTRACT


# --- internal helpers (nautilus-free except the two _nautilus_* builders) ----

def _require_dict(event: Any) -> dict:
    if not isinstance(event, dict):
        raise NautilusBridgeError(
            f"event must be a canonical mdp.market_event@1 dict, "
            f"got {type(event).__name__}")
    return event


def _no_lookahead_gate(event: dict) -> None:
    """Frozen no-lookahead rule: ts_init >= ts_event on every conversion.

    Checked on the RAW input before revalidation so a mutated stream is
    refused here with the dedicated error even when its event_id would
    otherwise mask the mutation.
    """
    ts_event = event.get("exchange_time_utc_ns")
    ts_init = event.get("available_time_utc_ns")
    if not isinstance(ts_event, int) or isinstance(ts_event, bool) or \
            not isinstance(ts_init, int) or isinstance(ts_init, bool):
        raise NautilusBridgeError(
            "exchange_time_utc_ns/available_time_utc_ns must be int ns")
    if ts_event < 0 or ts_init < 0:
        # nautilus ts fields are uint64 ns; negative ns cannot be represented.
        raise NautilusBridgeError(
            f"timestamps must be non-negative uint64 ns; got "
            f"exchange={ts_event} available={ts_init}")
    if ts_init < ts_event:
        raise BridgeLookaheadError(
            f"no-lookahead violation: available_time_utc_ns ({ts_init}) < "
            f"exchange_time_utc_ns ({ts_event}); the bridge never substitutes "
            f"timestamps")


def _validate_instrument(instrument: Any) -> tuple[str, int, int]:
    """Extract (instrument_id, price_precision, size_precision) and range-check."""
    instrument_id = getattr(instrument, "id", None)
    if instrument_id is None:
        raise NautilusBridgeError(
            "instrument metadata is mandatory and must expose .id "
            "(nautilus InstrumentId); pass the nautilus instrument for the "
            "event's instrument_id")
    price_precision = getattr(instrument, "price_precision", None)
    size_precision = getattr(instrument, "size_precision", None)
    for name, value in (("price_precision", price_precision),
                        ("size_precision", size_precision)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise NautilusBridgeError(
                f"instrument.{name} must be an int >= 0, got {value!r}")
        if value > _MAX_NAUTILUS_PRECISION:
            raise NautilusBridgeError(
                f"instrument.{name}={value} exceeds the nautilus 1.230.0 "
                f"Price/Quantity maximum of {_MAX_NAUTILUS_PRECISION} decimals")
    return str(instrument_id), price_precision, size_precision


def _canonicalise(event: dict) -> dict:
    """Revalidate the event against the frozen schema; return canonical dict.

    Keeps the bridge fail-closed: only contract-legal ``mdp.market_event@1``
    events ever reach conversion, whatever the caller claims.
    """
    return _models.validate_event(event)


def _stripped_decimal(d: Decimal) -> Decimal:
    """Trailing-zero-normalised Decimal (same semantics as models)."""
    with localcontext() as ctx:
        ctx.prec = max(len(d.as_tuple().digits) + 8, 60)
        return d.normalize()


def _require_lossless(
    event: dict,
    field: str,
    instrument_id: str,
    precision: int,
) -> Decimal:
    """Parse a canonical decimal string and prove it fits the instrument.

    Raises :class:`BridgePrecisionError` when the value is not exactly
    representable at the instrument precision (drift would occur).  Trailing
    zeros beyond the precision (e.g. ``'10.10'`` at precision 1) are
    losslessly normalised away, mirroring the frozen models semantics.
    """
    raw = event.get(field)
    if raw is None:
        raise NautilusBridgeError(
            f"event {event['event_id']} {event['event_type']} lacks {field}")
    d = _models.decimal_string_to_decimal(raw)
    stripped = _stripped_decimal(d)
    exponent = stripped.as_tuple().exponent
    fractional_digits = max(0, -exponent)
    if fractional_digits > precision:
        raise BridgePrecisionError(
            f"event {event['event_id']} field {field}={raw!r} is not exactly "
            f"representable at instrument {instrument_id} precision "
            f"{precision}; the bridge never rounds silently")
    return stripped


def _nautilus_price(
    value: Decimal,
    precision: int,
    field: str,
    instrument_id: str,
    event_id: str,
):
    """Construct a nautilus Price and PROVE no internal drift occurred.

    nautilus 1.230.0 routes the value through a binary double internally;
    huge magnitudes can therefore drift even when the decimal fits the
    instrument precision.  The post-construction comparison against the
    exact Decimal makes any such drift a hard error, never a silent round.
    """
    from nautilus_trader.model.objects import Price

    try:
        obj = Price(value, precision)
    except (ValueError, OverflowError, TypeError) as exc:
        raise BridgePrecisionError(
            f"event {event_id} field {field}={str(value)!r} rejected by "
            f"nautilus Price(precision={precision}): {exc}") from exc
    rendered = Decimal(str(obj))
    if rendered != value:
        raise BridgePrecisionError(
            f"event {event_id} field {field}: nautilus Price rendered "
            f"{str(obj)!r} which differs from the exact value "
            f"{str(value)!r}; refusing precision drift")
    return obj


def _nautilus_quantity(
    value: Decimal,
    precision: int,
    field: str,
    instrument_id: str,
    event_id: str,
    *,
    must_be_positive: bool,
):
    from nautilus_trader.model.objects import Quantity

    if must_be_positive and value <= 0:
        raise NautilusBridgeError(
            f"event {event_id} field {field}={str(value)!r}: nautilus "
            f"TradeTick requires a positive size")
    try:
        obj = Quantity(value, precision)
    except (ValueError, OverflowError, TypeError) as exc:
        raise BridgePrecisionError(
            f"event {event_id} field {field}={str(value)!r} rejected by "
            f"nautilus Quantity(precision={precision}): {exc}") from exc
    rendered = Decimal(str(obj))
    if rendered != value:
        raise BridgePrecisionError(
            f"event {event_id} field {field}: nautilus Quantity rendered "
            f"{str(obj)!r} which differs from the exact value "
            f"{str(value)!r}; refusing precision drift")
    return obj


def _quality_gate(
    event: dict,
    instrument_id: str,
    *,
    diagnostic_only: bool,
    diagnostics: BridgeDiagnostics | None,
) -> bool:
    """Frozen quality gate.  Returns False when the event must be excluded.

    * INVALID/QUARANTINED + not diagnostic_only -> raise;
    * INVALID/QUARANTINED + diagnostic_only -> require a sink, record
      REJECTED_EXCLUDED, return False (caller returns None — excluded);
    * SUSPECT -> a sink is MANDATORY (streaming an unrecorded SUSPECT event
      would be silent); recorded as SUSPECT_STREAMED after conversion;
    * VALID -> streams; recorded as CONVERTED when a sink is supplied.
    """
    status = event["quality_status"]
    if status in ("INVALID", "QUARANTINED"):
        if not diagnostic_only:
            raise BridgeQualityError(
                f"event {event['event_id']} has quality_status {status} "
                f"(reason_codes={event['reason_codes']}); INVALID/QUARANTINED "
                f"events cannot enter the conversion stream — pass "
                f"diagnostic_only=True explicitly to exclude+record them")
        if diagnostics is None:
            raise NautilusBridgeError(
                f"event {event['event_id']} is {status} and "
                f"diagnostic_only=True was passed: a BridgeDiagnostics sink "
                f"is mandatory so the exclusion is recorded, never silent")
        diagnostics.record(
            event, instrument_id, ACTION_REJECTED_EXCLUDED,
            f"excluded from conversion output under diagnostic_only=True "
            f"(status {status})")
        return False
    if status == "SUSPECT" and diagnostics is None:
        raise BridgeQualityError(
            f"event {event['event_id']} is SUSPECT "
            f"(reason_codes={event['reason_codes']}): the freeze requires its "
            f"status to be preserved in a sidecar; pass a BridgeDiagnostics "
            f"sink to stream it")
    return True


def _record_converted(
    diagnostics: BridgeDiagnostics | None,
    event: dict,
    instrument_id: str,
) -> None:
    if diagnostics is None:
        return
    action = (ACTION_SUSPECT_STREAMED
              if event["quality_status"] == "SUSPECT" else ACTION_CONVERTED)
    diagnostics.record(
        event, instrument_id, action,
        f"streamed with quality_status {event['quality_status']}")


# --- mapping entry points ----------------------------------------------------

def to_quote_tick(
    event: dict,
    instrument,
    *,
    diagnostic_only: bool = False,
    diagnostics: BridgeDiagnostics | None = None,
):
    """Map one canonical QUOTE event to a nautilus ``QuoteTick``.

    Frozen mapping: bid/ask Price and sizes from the INSTRUMENT precisions
    (mandatory argument, lossless — drift raises); ``ts_event =
    exchange_time_utc_ns`` and ``ts_init = available_time_utc_ns`` (int
    nanoseconds, nautilus-verified); no implicit now().

    Returns ``None`` only when the event is INVALID/QUARANTINED AND
    ``diagnostic_only=True`` was passed — the exclusion is then recorded in
    the ``diagnostics`` sidecar (mandatory in that mode), never silent.
    """
    event = _require_dict(event)
    _no_lookahead_gate(event)
    canonical = _canonicalise(event)
    instrument_id, price_precision, size_precision = _validate_instrument(instrument)
    if canonical["event_type"] != "QUOTE":
        raise NautilusBridgeError(
            f"to_quote_tick requires event_type QUOTE, got "
            f"{canonical['event_type']!r} (event {canonical['event_id']})")
    if canonical["instrument_id"] != instrument_id:
        raise NautilusBridgeError(
            f"event instrument_id {canonical['instrument_id']!r} does not "
            f"match instrument metadata {instrument_id!r} "
            f"(UNKNOWN_INSTRUMENT semantics)")
    if not _quality_gate(
            canonical, instrument_id,
            diagnostic_only=diagnostic_only, diagnostics=diagnostics):
        return None

    # nautilus_trader imported INSIDE functions only (freeze import_isolation).
    from nautilus_trader.model.data import QuoteTick

    bid = _nautilus_price(
        _require_lossless(canonical, "bid_price", instrument_id, price_precision),
        price_precision, "bid_price", instrument_id, canonical["event_id"])
    ask = _nautilus_price(
        _require_lossless(canonical, "ask_price", instrument_id, price_precision),
        price_precision, "ask_price", instrument_id, canonical["event_id"])
    bid_size = _nautilus_quantity(
        _require_lossless(canonical, "bid_size", instrument_id, size_precision),
        size_precision, "bid_size", instrument_id, canonical["event_id"],
        must_be_positive=False)
    ask_size = _nautilus_quantity(
        _require_lossless(canonical, "ask_size", instrument_id, size_precision),
        size_precision, "ask_size", instrument_id, canonical["event_id"],
        must_be_positive=False)
    tick = QuoteTick(
        instrument.id,
        bid,
        ask,
        bid_size,
        ask_size,
        canonical["exchange_time_utc_ns"],   # ts_event (verified uint64 ns)
        canonical["available_time_utc_ns"],  # ts_init  (verified uint64 ns)
    )
    _record_converted(diagnostics, canonical, instrument_id)
    return tick


def to_trade_tick(
    event: dict,
    instrument,
    *,
    diagnostic_only: bool = False,
    diagnostics: BridgeDiagnostics | None = None,
):
    """Map one canonical TRADE event to a nautilus ``TradeTick``.

    Frozen mapping: price/size via instrument precisions (lossless — drift
    raises); aggressor side ``buy -> BUYER`` / ``sell -> SELLER`` / absent ->
    ``AggressorSide.NO_AGGRESSOR``.  The canonical envelope has no venue
    trade-id field, so the ``TradeId`` is the deterministic 32-character
    (128-bit) prefix of the canonical ``event_id`` sha256 — nautilus 1.230.0
    caps ``TradeId`` at 36 characters (verified), so the full 64-hex id does
    not fit; the prefix derivation is total, deterministic and documented in
    docs/MDP_BRIDGE_NOTES.md.
    """
    event = _require_dict(event)
    _no_lookahead_gate(event)
    canonical = _canonicalise(event)
    instrument_id, price_precision, size_precision = _validate_instrument(instrument)
    if canonical["event_type"] != "TRADE":
        raise NautilusBridgeError(
            f"to_trade_tick requires event_type TRADE, got "
            f"{canonical['event_type']!r} (event {canonical['event_id']})")
    if canonical["instrument_id"] != instrument_id:
        raise NautilusBridgeError(
            f"event instrument_id {canonical['instrument_id']!r} does not "
            f"match instrument metadata {instrument_id!r} "
            f"(UNKNOWN_INSTRUMENT semantics)")
    if not _quality_gate(
            canonical, instrument_id,
            diagnostic_only=diagnostic_only, diagnostics=diagnostics):
        return None

    # nautilus_trader imported INSIDE functions only (freeze import_isolation).
    from nautilus_trader.model.data import TradeTick
    from nautilus_trader.model.enums import AggressorSide
    from nautilus_trader.model.identifiers import TradeId

    price = _nautilus_price(
        _require_lossless(canonical, "price", instrument_id, price_precision),
        price_precision, "price", instrument_id, canonical["event_id"])
    size = _nautilus_quantity(
        _require_lossless(canonical, "quantity", instrument_id, size_precision),
        size_precision, "quantity", instrument_id, canonical["event_id"],
        must_be_positive=True)
    side = canonical["side"]
    if side == "buy":
        aggressor_side = AggressorSide.BUYER
    elif side == "sell":
        aggressor_side = AggressorSide.SELLER
    else:
        aggressor_side = AggressorSide.NO_AGGRESSOR
    tick = TradeTick(
        instrument.id,
        price,
        size,
        aggressor_side,
        TradeId(canonical["event_id"][:_TRADE_ID_PREFIX_LEN]),
        canonical["exchange_time_utc_ns"],   # ts_event (verified uint64 ns)
        canonical["available_time_utc_ns"],  # ts_init  (verified uint64 ns)
    )
    _record_converted(diagnostics, canonical, instrument_id)
    return tick


def convert_stream(
    events,
    instrument,
    *,
    diagnostic_only: bool = False,
    diagnostics: BridgeDiagnostics | None = None,
) -> list:
    """Convert an ordered iterable of canonical events, never reordering.

    Routes each event by its frozen ``event_type`` (QUOTE -> to_quote_tick,
    TRADE -> to_trade_tick) and preserves the caller's order exactly: the
    bridge never reorders and never substitutes timestamps (freeze
    replay/bridge rules — ordering is replay.py's authority).  Under
    ``diagnostic_only=True`` excluded events are skipped (recorded in the
    sidecar); otherwise an INVALID/QUARANTINED event fails the whole call.
    """
    out = []
    for event in events:
        canonical_type = event["event_type"] if isinstance(event, dict) else None
        if canonical_type == "QUOTE":
            tick = to_quote_tick(
                event, instrument,
                diagnostic_only=diagnostic_only, diagnostics=diagnostics)
        elif canonical_type == "TRADE":
            tick = to_trade_tick(
                event, instrument,
                diagnostic_only=diagnostic_only, diagnostics=diagnostics)
        else:
            raise NautilusBridgeError(
                f"convert_stream requires QUOTE/TRADE events, got "
                f"{canonical_type!r}")
        if tick is not None:
            out.append(tick)
    return out


def to_bar(*_args, **_kwargs):
    """Bars are NOT mapped in @1 — always raises ``NotImplementedError``.

    The plane has no canonical BAR event type, so OHLCV can never become
    quotes or depth (frozen mappings.Bar; plan section 8).
    """
    raise NotImplementedError(BAR_NOT_MAPPED_IN_V1)
