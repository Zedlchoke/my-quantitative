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
* ``Bar`` — NOT mapped from ``mdp.market_event@1`` events (the @1 envelope
  has no BAR type, so OHLCV can never become quotes or depth: any non-bar
  input to :func:`to_bar` raises the frozen ``BAR_NOT_MAPPED_IN_V1``
  NotImplementedError).  The V2 cycle ADDITIVELY maps canonical
  ``mdp.market_bar@2`` bars (research/market_data_plane/bars.py) to nautilus
  1.230.0 ``Bar``: OHLC Price / volume Quantity at the bar's DECLARED
  precisions (which must equal the instrument's — precision/identity
  mismatch fails closed), ``ts_event = close_time_utc_ns`` (bar completion)
  and ``ts_init = available_time_utc_ns``; a null NOT_EVALUABLE volume is
  refused, never substituted with zero; bars have no aggressor so the
  deterministic TradeId rule does not apply.

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

from . import bars as _bars
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

#: Bars are NOT mapped from mdp.market_event@1 events (plan section 8 +
#: freeze mappings.Bar).  The @2 :func:`to_bar` mapping is additive: any
#: NON-bar input (every @1 event included) is refused with this frozen
#: message, so OHLCV can never enter the tick paths from event land.
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


# --- bar mapping (mdp.market_bar@2, V2-additive; @1 events stay refused) -----

def _bar_no_lookahead_gate(bar: dict) -> None:
    """Frozen no-lookahead rule for bars: ts_init >= ts_event.

    ``ts_event = close_time_utc_ns`` (bar completion) and
    ``ts_init = available_time_utc_ns``.  Checked on the RAW input before
    revalidation (same convention as the event path) so a mutated stream is
    refused here even when its bar_id would otherwise mask the mutation.
    nautilus ts fields are uint64 ns: negative values cannot be represented.
    """
    ts_event = bar.get("close_time_utc_ns")
    ts_init = bar.get("available_time_utc_ns")
    if not isinstance(ts_event, int) or isinstance(ts_event, bool) or \
            not isinstance(ts_init, int) or isinstance(ts_init, bool):
        raise NautilusBridgeError(
            "close_time_utc_ns/available_time_utc_ns must be int ns")
    if ts_event < 0 or ts_init < 0:
        raise NautilusBridgeError(
            f"timestamps must be non-negative uint64 ns; got "
            f"close={ts_event} available={ts_init}")
    if ts_init < ts_event:
        raise BridgeLookaheadError(
            f"no-lookahead violation: available_time_utc_ns ({ts_init}) < "
            f"close_time_utc_ns ({ts_event}); the bridge never substitutes "
            f"timestamps")


def _bar_spec_from_interval_ns(interval_ns: int, instrument_id: str) -> str:
    """Derive the nautilus BarType ``{step}-{AGGREGATION}`` segment.

    nautilus 1.230.0 restricts aggregation steps to values that evenly divide
    the parent unit (verified: ``BarSpecification`` raises "step must evenly
    divide 60 / 1000"): MILLISECOND step | 1000, SECOND/MINUTE step | 60,
    HOUR step | 24.  The largest qualifying unit wins so 15-minute bars map
    to ``15-MINUTE`` (never ``900-SECOND``).  Intervals outside these rules
    raise (fail closed) — the caller must then pass an explicit nautilus
    BarType; the bridge never rounds an interval into a different one.
    """
    if not isinstance(interval_ns, int) or isinstance(interval_ns, bool) \
            or interval_ns <= 0:
        raise NautilusBridgeError(
            f"interval_ns must be an int > 0, got {interval_ns!r}")
    unit_ns_step = (
        (3_600_000_000_000, 24, "HOUR"),
        (60_000_000_000, 60, "MINUTE"),
        (1_000_000_000, 60, "SECOND"),
        (1_000_000, 1000, "MILLISECOND"),
    )
    for unit_ns, divides, name in unit_ns_step:
        if interval_ns % unit_ns == 0:
            step = interval_ns // unit_ns
            if divides % step == 0:
                return f"{step}-{name}"
    raise NautilusBridgeError(
        f"bar interval_ns {interval_ns} is not representable as a nautilus "
        f"1.230.0 periodic BarType step (step must evenly divide the parent "
        f"unit); pass an explicit bar_type — the bridge never rounds the "
        f"interval (bar {instrument_id})")


def _resolve_bar_type(bar_type, interval_ns: int, instrument_id: str):
    """Explicit nautilus BarType/str, or the deterministic derivation."""
    from nautilus_trader.model.data import BarType

    if bar_type is None:
        derived = (f"{instrument_id}-"
                   f"{_bar_spec_from_interval_ns(interval_ns, instrument_id)}"
                   f"-LAST-EXTERNAL")
        return BarType.from_str(derived)
    if isinstance(bar_type, str):
        return BarType.from_str(bar_type)
    if isinstance(bar_type, BarType):
        return bar_type
    raise NautilusBridgeError(
        f"bar_type must be None (deterministic derivation), a nautilus "
        f"BarType, or its string form; got {type(bar_type).__name__}")


def _bar_quality_gate(
    bar: dict,
    instrument_id: str,
    *,
    diagnostic_only: bool,
    diagnostics: BridgeDiagnostics | None,
) -> bool:
    """Frozen quality gate for bars (same semantics as the event gate).

    Mirrors :func:`_quality_gate` on the bar identity fields (bar_id instead
    of event_id, schema name instead of event_type); kept as a separate
    helper so the event-path helpers stay byte-identical.
    """
    status = bar["quality_status"]
    if status in ("INVALID", "QUARANTINED"):
        if not diagnostic_only:
            raise BridgeQualityError(
                f"bar {bar['bar_id']} has quality_status {status} "
                f"(reason_codes={bar['reason_codes']}); INVALID/QUARANTINED "
                f"bars cannot enter the conversion stream — pass "
                f"diagnostic_only=True explicitly to exclude+record them")
        if diagnostics is None:
            raise NautilusBridgeError(
                f"bar {bar['bar_id']} is {status} and diagnostic_only=True "
                f"was passed: a BridgeDiagnostics sink is mandatory so the "
                f"exclusion is recorded, never silent")
        diagnostics.records.append(BridgeDiagnostic(
            event_id=bar["bar_id"],
            instrument_id=instrument_id,
            event_type=_bars.SCHEMA_VERSION,
            quality_status=status,
            reason_codes=tuple(bar["reason_codes"]),
            action=ACTION_REJECTED_EXCLUDED,
            detail=("excluded from conversion output under diagnostic_only="
                    f"True (status {status})"),
        ))
        return False
    if status == "SUSPECT" and diagnostics is None:
        raise BridgeQualityError(
            f"bar {bar['bar_id']} is SUSPECT (reason_codes={bar['reason_codes']}): "
            f"the freeze requires its status to be preserved in a sidecar; "
            f"pass a BridgeDiagnostics sink to stream it")
    return True


def _record_bar_converted(
    diagnostics: BridgeDiagnostics | None,
    bar: dict,
    instrument_id: str,
) -> None:
    if diagnostics is None:
        return
    action = (ACTION_SUSPECT_STREAMED
              if bar["quality_status"] == "SUSPECT" else ACTION_CONVERTED)
    diagnostics.records.append(BridgeDiagnostic(
        event_id=bar["bar_id"],
        instrument_id=instrument_id,
        event_type=_bars.SCHEMA_VERSION,
        quality_status=bar["quality_status"],
        reason_codes=tuple(bar["reason_codes"]),
        action=action,
        detail=(f"streamed mdp.market_bar@2 bar with quality_status "
                f"{bar['quality_status']}"),
    ))


def to_bar(
    bar: dict,
    instrument,
    *,
    bar_type=None,
    diagnostic_only: bool = False,
    diagnostics: BridgeDiagnostics | None = None,
):
    """Map one canonical ``mdp.market_bar@2`` bar to a nautilus ``Bar``.

    Frozen @2 mapping (additive — ``mdp.market_event@1`` stays byte-frozen
    and bar-free): OHLC become nautilus ``Price`` and volume a
    ``Quantity`` at the bar's DECLARED ``price_precision``/``size_precision``
    (lossless-or-raise; declared precisions must EQUAL the instrument
    metadata precisions — a mismatch is a precision/identity failure and
    raises).  ``ts_event = close_time_utc_ns`` (bar completion) and
    ``ts_init = available_time_utc_ns`` (no-lookahead available-time gate on
    the raw input, uint64 ns enforced); there is no implicit ``now()`` and
    no aggressor side (bars have none, so the deterministic TradeId rule
    does not apply).

    ``bar_type`` is the nautilus ``BarType`` (or its string form); when
    ``None`` it is derived deterministically from ``interval_ns``
    (``{step}-{MINUTE|SECOND|MILLISECOND|HOUR}-LAST-EXTERNAL``, step must
    evenly divide the parent nautilus unit) — unrepresentable intervals
    raise instead of being rounded.  The plane's own ``bar_type`` label field
    is never parsed by the bridge.

    A bar whose volume is not evaluable (null, NOT_EVALUABLE) is REFUSED:
    nautilus requires a Quantity and the bridge never substitutes zero
    (frozen "NEVER zero" rule).  The quality gate mirrors the event path
    (INVALID/QUARANTINED raise unless diagnostic_only=True with a mandatory
    sidecar; SUSPECT streams only with a recorded sidecar; VALID records
    CONVERTED when a sink is given).

    Any non-bar input (every ``mdp.market_event@1`` event included) raises
    ``NotImplementedError(BAR_NOT_MAPPED_IN_V1)``: bars are NOT mapped from
    @1 events.
    """
    if not isinstance(bar, dict):
        raise NautilusBridgeError(
            f"bar must be a canonical mdp.market_bar@2 dict, "
            f"got {type(bar).__name__}")
    if bar.get("schema_version") != _bars.SCHEMA_VERSION:
        # Bars are NOT mapped in @1 (frozen): every non-mdp.market_bar@2
        # input — mdp.market_event@1 events included — is refused with the
        # frozen stub message.
        raise NotImplementedError(BAR_NOT_MAPPED_IN_V1)

    _bar_no_lookahead_gate(bar)
    canonical = _bars.validate_bar(bar)
    instrument_id, price_precision, size_precision = _validate_instrument(instrument)
    if canonical["instrument_id"] != instrument_id:
        raise NautilusBridgeError(
            f"bar instrument_id {canonical['instrument_id']!r} does not "
            f"match instrument metadata {instrument_id!r} "
            f"(UNKNOWN_INSTRUMENT semantics)")
    if canonical["price_precision"] != price_precision or \
            canonical["size_precision"] != size_precision:
        raise BridgePrecisionError(
            f"bar {canonical['bar_id']} declared precisions "
            f"(price {canonical['price_precision']}, size "
            f"{canonical['size_precision']}) differ from instrument "
            f"{instrument_id} precisions (price {price_precision}, size "
            f"{size_precision}); the bridge refuses precision/identity "
            f"mismatch — never re-renders a bar at another precision")
    if not _bar_quality_gate(
            canonical, instrument_id,
            diagnostic_only=diagnostic_only, diagnostics=diagnostics):
        return None
    if canonical["volume"] is None:
        raise NautilusBridgeError(
            f"bar {canonical['bar_id']} volume is not evaluable (null, "
            f"completeness NOT_EVALUABLE); nautilus Bar requires a Quantity "
            f"and the bridge never substitutes zero — exclude it explicitly")

    # nautilus_trader imported INSIDE functions only (freeze import_isolation).
    from nautilus_trader.model.data import Bar

    open_price = _nautilus_price(
        _require_lossless(canonical, "open", instrument_id, price_precision),
        price_precision, "open", instrument_id, canonical["bar_id"])
    high_price = _nautilus_price(
        _require_lossless(canonical, "high", instrument_id, price_precision),
        price_precision, "high", instrument_id, canonical["bar_id"])
    low_price = _nautilus_price(
        _require_lossless(canonical, "low", instrument_id, price_precision),
        price_precision, "low", instrument_id, canonical["bar_id"])
    close_price = _nautilus_price(
        _require_lossless(canonical, "close", instrument_id, price_precision),
        price_precision, "close", instrument_id, canonical["bar_id"])
    volume = _nautilus_quantity(
        _require_lossless(canonical, "volume", instrument_id, size_precision),
        size_precision, "volume", instrument_id, canonical["bar_id"],
        must_be_positive=False)

    nautilus_bar = Bar(
        _resolve_bar_type(bar_type, canonical["interval_ns"], instrument_id),
        open_price,
        high_price,
        low_price,
        close_price,
        volume,
        canonical["close_time_utc_ns"],     # ts_event (verified uint64 ns)
        canonical["available_time_utc_ns"],  # ts_init  (verified uint64 ns)
    )
    _record_bar_converted(diagnostics, canonical, instrument_id)
    return nautilus_bar
