"""FOREX-FREE-V2 exact accounting kernel (F2-P1, A2 lane).

Factory-only module: synthetic fixtures, no real-data PnL, no network, no
new data authority.  Every convention below is FROZEN and carried unchanged
from the validated V1 line (research/assets/forex_free_v1/scored_runner.py
``extract_trades`` + family1/family2 cost code) and from the frozen cost
authority in research/control/forex_free_v2_run/run_contract.json and
frequency_contract.json:

* PnL identity (frozen USD-unit design)::

      pnl_usd = direction * notional_usd * (exit_price / entry_price - 1)
      direction = +1 for LONG, -1 for SHORT

  V1 family1 computes ``gross = position * (flatten_price / entry_price -
  1.0)`` and the scored runner converts with ``pnl = net_return x
  FROZEN_NOTIONAL``.  The notional is 10000 USD-units BY DESIGN: the result
  is already USD, so no quote-currency conversion exists in this design.
  Any request for a conversion beyond this identity is refused
  UNAVAILABLE_FAIL_CLOSED (see :func:`convert_to_usd_identity`).

* Cost (frozen proxy, a priori): 1.5 bps per side x stress tier in
  {1.0, 1.5, 2.0}, charged exactly once per fill side.  Tier 2.0 also adds
  one fill-delay event upstream; the accounting charge is identical.
  Round trip = 2 x 1.5 x tier bps = 3.0 / 4.5 / 6.0 bps on the notional.

* The fill list is the single source of truth: every state mutation of
  :class:`PositionBook` appends one :class:`Fill`; turnover and trade
  counts reconcile strictly from fills
  (:func:`turnover_from_fills`, :func:`trades_from_fills`).  A skipped or
  missing bar is recorded as a :class:`NoTrade` sentinel and touches
  neither fills, positions, nor costs.

* Concentration follows the V1 convention (shares of positive PnL by pair,
  rounded to 6 decimals; all-``None`` when no positive PnL exists).  The
  cash/account currency ``USD`` is never a pair: it is rejected as a pair
  at position open and excluded automatically from concentration.

* Digests hash EXACT artifact bytes: :func:`canonical_json_bytes` (sorted
  keys, separators ``(',', ':')``, ``ensure_ascii=False``, UTF-8) then
  :func:`sha256_hex`.  The ledger line for a record is exactly its
  canonical bytes plus one newline, so ``sha256(line_bytes)`` is the
  record digest.

* Publication is once-only per record digest
  (:class:`AtomicJsonlPublisher`): fcntl.flock-serialized appends (safe
  across threads and processes on one host), idempotent replay returns
  ``(observed_delta=0, published_now=0)``.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import threading
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from research.assets.forex.conversion import parse_utc_timestamp

__all__ = [
    "BASE_BPS_PER_SIDE",
    "COST_TIERS",
    "FROZEN_NOTIONAL_USD_UNIT",
    "CASH_CURRENCY",
    "UnavailableFailClosed",
    "PositionBookError",
    "Fill",
    "NoTrade",
    "ClosedTrade",
    "PositionBook",
    "canonical_json_bytes",
    "sha256_hex",
    "digest_of",
    "bps_cost",
    "convert_to_usd_identity",
    "turnover_from_fills",
    "trades_from_fills",
    "pair_concentration",
    "AtomicJsonlPublisher",
]

# --- frozen conventions (V1 terminal authority, carried unchanged) ---------- #
BASE_BPS_PER_SIDE = 1.5                    # frozen proxy spread cost per fill side
COST_TIERS = (1.0, 1.5, 2.0)               # frozen cost-stress multipliers (S1, S2, S3)
FROZEN_NOTIONAL_USD_UNIT = 10_000.0        # notional is 10000 USD-units by design
CASH_CURRENCY = "USD"                      # account currency; never a tradable pair

_SIDES = ("LONG", "SHORT")
_LEGS = ("ENTRY", "EXIT")


class UnavailableFailClosed(Exception):
    """A request beyond the frozen USD-unit identity design cannot be served.

    There is no fabricated FX-rate or fixing authority in this design, so
    anything that would require one fails closed with
    ``reason == "UNAVAILABLE_FAIL_CLOSED"``.
    """

    reason = "UNAVAILABLE_FAIL_CLOSED"

    def __init__(self, detail: str) -> None:
        super().__init__(f"UNAVAILABLE_FAIL_CLOSED: {detail}")
        self.detail = detail


class PositionBookError(ValueError):
    """An accounting rule was violated; the book state is unchanged.

    ``code`` is a machine-readable rejection reason (DOUBLE_OPEN,
    TRADE_ID_REUSED, DOUBLE_CLOSE, UNKNOWN_TRADE_ID, ...).
    """

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


# --- canonical bytes and digests -------------------------------------------- #
def canonical_json_bytes(obj: Any) -> bytes:
    """Canonical JSON encoding of ``obj`` as EXACT artifact bytes.

    ``json.dumps(obj, sort_keys=True, separators=(',', ':'),
    ensure_ascii=False)`` encoded UTF-8.  Digests must hash exactly these
    bytes -- the same bytes a publisher writes as one ledger line.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(raw: bytes) -> str:
    """Lowercase hex sha256 of the exact bytes ``raw``."""
    return hashlib.sha256(raw).hexdigest()


def digest_of(record: Any) -> str:
    """Record digest = sha256 of the record's canonical JSON bytes."""
    return sha256_hex(canonical_json_bytes(record))


# --- frozen cost and conversion identity ------------------------------------- #
def bps_cost(notional_usd: float, cost_tier: float) -> float:
    """Per-side cost in USD: ``notional * (1.5 * tier) / 10000``.

    Frozen authority: 1.5 bps per side x stress tier; tier in
    {1.0, 1.5, 2.0}.  On the 10000 USD-unit notional this is exactly
    1.50 / 2.25 / 3.00 USD per side.
    """
    if isinstance(notional_usd, bool) or not isinstance(notional_usd, (int, float)) \
            or not math.isfinite(float(notional_usd)) or float(notional_usd) <= 0:
        raise PositionBookError("BAD_NOTIONAL", f"notional_usd must be a finite number > 0, got {notional_usd!r}")
    tier = _resolve_tier(cost_tier)
    return float(notional_usd) * (BASE_BPS_PER_SIDE * tier) / 10_000.0


def _resolve_tier(cost_tier: Any) -> float:
    if isinstance(cost_tier, bool) or not isinstance(cost_tier, (int, float)):
        raise PositionBookError("BAD_COST_TIER", f"cost_tier must be a number, got {cost_tier!r}")
    tier = float(cost_tier)
    if tier not in COST_TIERS:
        raise PositionBookError("BAD_COST_TIER", f"cost_tier must be one of {COST_TIERS}, got {cost_tier!r}")
    return tier


def _finite_positive(value: Any, code: str, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) \
            or not math.isfinite(float(value)) or float(value) <= 0:
        raise PositionBookError(code, f"{name} must be a finite number > 0, got {value!r}")
    return float(value)


def convert_to_usd_identity(amount_usd: float, *, from_currency: str = "USD") -> float:
    """The ONLY USD conversion in the V2 design: the identity.

    Frozen USD-unit convention (V1 ``extract_trades``: ``pnl = net_return x
    FROZEN_NOTIONAL`` with notional 10000 USD-units)::

        pnl_usd = direction * notional_usd * (exit_price / entry_price - 1)

    The notional is denominated in USD-units by design, so amounts are
    already USD and the conversion is the identity ``x -> x``.  No
    quote-currency conversion graph, no fixing, no rate authority exists in
    this design; requesting conversion from any other currency would
    require one, so it fails closed with UNAVAILABLE_FAIL_CLOSED.
    """
    if from_currency != "USD":
        raise UnavailableFailClosed(
            f"conversion {from_currency!r} -> USD is beyond the frozen USD-unit "
            "identity design (no FX-rate authority exists; fail closed)"
        )
    if isinstance(amount_usd, bool) or not isinstance(amount_usd, (int, float)) \
            or not math.isfinite(float(amount_usd)):
        raise PositionBookError("BAD_AMOUNT", f"amount_usd must be a finite number, got {amount_usd!r}")
    return float(amount_usd)


# --- fill / sentinel / closed-trade records ----------------------------------- #
@dataclass(frozen=True)
class Fill:
    """One accounting fill; the atomic unit of the single source of truth.

    ``side`` is the POSITION side of the trade (LONG/SHORT) and is the same
    on both legs: the EXIT leg closes that same position (order-side
    buy/sell is an execution detail, not accounting state).  ``cost_usd``
    is the once-charged per-side cost :func:`bps_cost` at ``cost_tier``.
    """

    trade_id: str
    pair: str
    side: str          # LONG / SHORT (position side, both legs)
    notional_usd: float
    price: float
    ts_utc: str        # canonical UTC ISO-8601 (validated, aware)
    leg: str           # ENTRY / EXIT
    cost_tier: float   # 1.0 / 1.5 / 2.0
    cost_usd: float


@dataclass(frozen=True)
class NoTrade:
    """Sentinel for a skipped or missing bar: NO position and NO cost.

    Sentinels never touch :attr:`PositionBook.fills`; that is exactly what
    makes "no position, no cost" provable from the fill list.
    """

    pair: str
    ts_utc: str
    reason: str


@dataclass(frozen=True)
class ClosedTrade:
    """Summary of one completed round trip (derived; fills remain truth)."""

    trade_id: str
    pair: str
    side: str
    notional_usd: float
    entry_price: float
    exit_price: float
    entry_ts_utc: str
    exit_ts_utc: str
    cost_tier: float
    pnl_usd: float          # gross price PnL under the frozen identity
    entry_cost_usd: float
    exit_cost_usd: float
    net_pnl_usd: float      # pnl_usd - entry_cost_usd - exit_cost_usd


@dataclass(frozen=True)
class _OpenPosition:
    trade_id: str
    pair: str
    side: str
    notional_usd: float
    entry_price: float
    entry_ts_utc: str
    cost_tier: float


# --- position book ------------------------------------------------------------ #
class PositionBook:
    """One lifecycle per trade id; fills are the single source of truth.

    Rejections (state unchanged, :class:`PositionBookError` with ``code``):
    DOUBLE_OPEN, TRADE_ID_REUSED (one lifecycle per trade id, even after
    close), DOUBLE_CLOSE, UNKNOWN_TRADE_ID, BAD_SIDE, BAD_NOTIONAL,
    BAD_PRICE, BAD_COST_TIER, BAD_PAIR (the cash currency is not a pair),
    BAD_TIMESTAMP.
    """

    def __init__(self) -> None:
        self.fills: list[Fill] = []
        self.no_trades: list[NoTrade] = []
        self.closed_trades: list[ClosedTrade] = []
        self._open: dict[str, _OpenPosition] = {}
        self._used: set[str] = set()

    # --- introspection (derived from fills, never stored separately) ------- #
    @property
    def open_trade_ids(self) -> list[str]:
        return sorted(self._open)

    @property
    def total_cost_usd(self) -> float:
        """Total cost paid, summed from fills (single source of truth)."""
        return math.fsum(f.cost_usd for f in self.fills)

    @property
    def pnl_usd_total(self) -> float:
        """Gross price PnL over closed trades (frozen USD-unit identity)."""
        return math.fsum(t.pnl_usd for t in self.closed_trades)

    @property
    def net_usd_total(self) -> float:
        """Gross PnL minus total cost: the economic result of the book."""
        return math.fsum([self.pnl_usd_total, -self.total_cost_usd])

    # --- mutations: every one appends exactly one Fill ---------------------- #
    def open_position(
        self,
        *,
        trade_id: str,
        pair: str,
        side: str,
        notional_usd: float,
        price: float,
        ts_utc: str,
        cost_tier: float,
    ) -> Fill:
        """Open one position; charge the ENTRY cost exactly once."""
        if not isinstance(trade_id, str) or not trade_id:
            raise PositionBookError("BAD_TRADE_ID", f"trade_id must be a non-empty string, got {trade_id!r}")
        if trade_id in self._open:
            raise PositionBookError("DOUBLE_OPEN", f"trade_id {trade_id!r} is already open")
        if trade_id in self._used:
            raise PositionBookError("TRADE_ID_REUSED",
                                    f"trade_id {trade_id!r} already had its one lifecycle")
        if not isinstance(pair, str) or not pair:
            raise PositionBookError("BAD_PAIR", f"pair must be a non-empty string, got {pair!r}")
        if pair == CASH_CURRENCY:
            raise PositionBookError("BAD_PAIR",
                                    f"{CASH_CURRENCY} is the cash/account currency and is never a pair")
        if side not in _SIDES:
            raise PositionBookError("BAD_SIDE", f"side must be one of {_SIDES}, got {side!r}")
        notional = _finite_positive(notional_usd, "BAD_NOTIONAL", "notional_usd")
        entry_price = _finite_positive(price, "BAD_PRICE", "price")
        tier = _resolve_tier(cost_tier)
        entry_ts = parse_utc_timestamp(ts_utc, field="ts_utc").isoformat()

        cost = bps_cost(notional, tier)  # charged ONCE, here, at entry
        fill = Fill(trade_id=trade_id, pair=pair, side=side, notional_usd=notional,
                    price=entry_price, ts_utc=entry_ts, leg="ENTRY",
                    cost_tier=tier, cost_usd=cost)
        self.fills.append(fill)
        self._open[trade_id] = _OpenPosition(
            trade_id=trade_id, pair=pair, side=side, notional_usd=notional,
            entry_price=entry_price, entry_ts_utc=entry_ts, cost_tier=tier)
        self._used.add(trade_id)
        return fill

    def close_position(self, trade_id: str, exit_price: float, ts_utc: str) -> ClosedTrade:
        """Close the open position; charge the EXIT cost exactly once.

        PnL is the frozen USD-unit identity
        ``direction * notional * (exit/entry - 1)``; the only USD
        conversion applied is :func:`convert_to_usd_identity` (the
        identity).  The cost tier is the one bound at entry.
        """
        if not isinstance(trade_id, str) or not trade_id:
            raise PositionBookError("BAD_TRADE_ID", f"trade_id must be a non-empty string, got {trade_id!r}")
        position = self._open.get(trade_id)
        if position is None:
            if trade_id in self._used:
                raise PositionBookError("DOUBLE_CLOSE",
                                        f"trade_id {trade_id!r} was already closed (one lifecycle)")
            raise PositionBookError("UNKNOWN_TRADE_ID",
                                    f"trade_id {trade_id!r} was never opened")
        exit_px = _finite_positive(exit_price, "BAD_PRICE", "exit_price")
        exit_ts = parse_utc_timestamp(ts_utc, field="ts_utc").isoformat()

        exit_cost = bps_cost(position.notional_usd, position.cost_tier)  # charged ONCE, here, at exit
        direction = 1.0 if position.side == "LONG" else -1.0
        raw_pnl = direction * position.notional_usd * (exit_px / position.entry_price - 1.0)
        pnl_usd = convert_to_usd_identity(raw_pnl, from_currency="USD")  # identity by design
        fill = Fill(trade_id=trade_id, pair=position.pair, side=position.side,
                    notional_usd=position.notional_usd, price=exit_px, ts_utc=exit_ts,
                    leg="EXIT", cost_tier=position.cost_tier, cost_usd=exit_cost)
        self.fills.append(fill)
        del self._open[trade_id]
        closed = ClosedTrade(
            trade_id=trade_id, pair=position.pair, side=position.side,
            notional_usd=position.notional_usd,
            entry_price=position.entry_price, exit_price=exit_px,
            entry_ts_utc=position.entry_ts_utc, exit_ts_utc=exit_ts,
            cost_tier=position.cost_tier, pnl_usd=pnl_usd,
            entry_cost_usd=bps_cost(position.notional_usd, position.cost_tier),
            exit_cost_usd=exit_cost,
            net_pnl_usd=math.fsum([pnl_usd, -exit_cost,
                                   -bps_cost(position.notional_usd, position.cost_tier)]))
        self.closed_trades.append(closed)
        return closed

    def record_no_trade(self, *, pair: str, ts_utc: str, reason: str) -> NoTrade:
        """Record a skipped/missing bar: NO position, NO cost, NO fill.

        The sentinel goes to :attr:`no_trades` only, so fills-derived
        turnover, trade counts and costs are provably unchanged.
        """
        if not isinstance(pair, str) or not pair:
            raise PositionBookError("BAD_PAIR", f"pair must be a non-empty string, got {pair!r}")
        if pair == CASH_CURRENCY:
            raise PositionBookError("BAD_PAIR",
                                    f"{CASH_CURRENCY} is the cash/account currency and is never a pair")
        if not isinstance(reason, str) or not reason:
            raise PositionBookError("BAD_REASON", f"reason must be a non-empty string, got {reason!r}")
        ts = parse_utc_timestamp(ts_utc, field="ts_utc").isoformat()
        sentinel = NoTrade(pair=pair, ts_utc=ts, reason=reason)
        self.no_trades.append(sentinel)
        return sentinel


# --- reconciliation strictly from fills --------------------------------------- #
def turnover_from_fills(fills: Iterable[Fill]) -> dict[str, float]:
    """Turnover reconciled strictly from fills: notional summed per leg.

    Returns ``entry_notional_usd``, ``exit_notional_usd``,
    ``total_notional_usd`` and the per-leg fill counts.  Unknown legs fail
    closed.
    """
    entry = exit_ = 0.0
    n_entry = n_exit = 0
    for fill in fills:
        if fill.leg == "ENTRY":
            entry = math.fsum([entry, fill.notional_usd])
            n_entry += 1
        elif fill.leg == "EXIT":
            exit_ = math.fsum([exit_, fill.notional_usd])
            n_exit += 1
        else:
            raise PositionBookError("BAD_LEG", f"fill leg must be one of {_LEGS}, got {fill.leg!r}")
    return {
        "entry_notional_usd": entry,
        "exit_notional_usd": exit_,
        "total_notional_usd": math.fsum([entry, exit_]),
        "n_entry_fills": n_entry,
        "n_exit_fills": n_exit,
    }


def trades_from_fills(fills: Iterable[Fill]) -> dict[str, Any]:
    """Trade counts reconciled strictly from fills.

    A round trip is exactly one ENTRY plus one EXIT fill for a trade id;
    an ENTRY alone is still open.  Malformed sequences (duplicate legs,
    an EXIT before any ENTRY) fail closed.
    """
    state: dict[str, dict[str, Any]] = {}
    for fill in fills:
        st = state.setdefault(fill.trade_id, {"pair": fill.pair, "entry": 0, "exit": 0})
        if fill.leg == "ENTRY":
            if st["entry"]:
                raise PositionBookError("DUPLICATE_ENTRY",
                                        f"trade_id {fill.trade_id!r} has more than one ENTRY fill")
            st["entry"] += 1
        elif fill.leg == "EXIT":
            if st["exit"]:
                raise PositionBookError("DUPLICATE_EXIT",
                                        f"trade_id {fill.trade_id!r} has more than one EXIT fill")
            if st["entry"] == 0:
                raise PositionBookError("ORPHAN_EXIT",
                                        f"trade_id {fill.trade_id!r} has an EXIT before any ENTRY")
            st["exit"] += 1
        else:
            raise PositionBookError("BAD_LEG", f"fill leg must be one of {_LEGS}, got {fill.leg!r}")
    closed = sorted(tid for tid, st in state.items() if st["entry"] == 1 and st["exit"] == 1)
    open_ids = sorted(tid for tid, st in state.items() if st["exit"] == 0)
    return {
        "n_fills": sum(st["entry"] + st["exit"] for st in state.values()),
        "round_trips": len(closed),
        "open_positions": len(open_ids),
        "trade_ids_closed": closed,
        "trade_ids_open": open_ids,
        "pairs": sorted({st["pair"] for st in state.values()}),
    }


def pair_concentration(pnl_by_pair: Mapping[str, float]) -> dict[str, Any]:
    """V1-convention concentration: shares of POSITIVE PnL by pair.

    Parity with ``scored_runner.concentration``: each pair contributes its
    positive PnL part (negative/zero contributes 0.0), shares are
    ``part / total_positive`` rounded to 6 decimals, and when no positive
    PnL exists every share is ``None``.  The cash/account currency
    ``USD`` is excluded automatically wherever it appears -- cash is never
    a pair and must never enter the concentration denominator.
    """
    parts: dict[str, float] = {}
    total_positive = 0.0
    for pair, pnl in pnl_by_pair.items():
        if pair == CASH_CURRENCY:
            continue
        if isinstance(pnl, bool) or not isinstance(pnl, (int, float)) or not math.isfinite(float(pnl)):
            raise PositionBookError("BAD_PNL", f"pnl for {pair!r} must be a finite number, got {pnl!r}")
        part = float(pnl) if float(pnl) > 0 else 0.0
        parts[pair] = part
        if part > 0:
            total_positive = math.fsum([total_positive, part])
    if total_positive == 0:
        return {pair: None for pair in parts}
    return {pair: round(part / total_positive, 6) for pair, part in parts.items()}


# --- once-only canonical JSONL publication ------------------------------------ #
class AtomicJsonlPublisher:
    """fcntl.flock-protected JSONL ledger with once-only publication.

    One record = one line = exactly ``canonical_json_bytes(record)`` plus a
    newline.  The record digest is ``sha256_hex`` of those exact bytes, so
    a ledger line is self-verifying.  ``publish_once`` is once-only per
    digest: under the exclusive lock it rescans the ledger (authoritative,
    restart-safe) and returns ``(observed_delta=1, published_now=1)`` on
    first publication or ``(0, 0)`` on idempotent replay.  A per-instance
    ``threading.Lock`` plus ``flock`` serializes appends across threads and
    processes on the same host.
    """

    def __init__(self, ledger_path: str | os.PathLike[str]) -> None:
        self.ledger_path = os.fspath(ledger_path)
        self._thread_lock = threading.Lock()

    def digest_of(self, record: Any) -> str:
        """Digest of ``record`` = sha256 of its canonical JSON bytes."""
        return digest_of(record)

    def _published_digests(self, handle) -> set[str]:
        handle.seek(0)
        digests: set[str] = set()
        for raw_line in handle:
            line = raw_line.rstrip(b"\n")
            if line:
                digests.add(sha256_hex(line))
        return digests

    def publish_once(self, record: Any) -> tuple[int, int]:
        """Publish ``record`` at most once (by digest). Returns
        ``(observed_delta, published_now)``: ``(1, 1)`` when written now,
        ``(0, 0)`` when the digest already exists (zero-delta no-op).
        """
        payload = canonical_json_bytes(record)
        digest = sha256_hex(payload)
        parent = os.path.dirname(self.ledger_path)
        with self._thread_lock:
            if parent:
                os.makedirs(parent, exist_ok=True)
            # "a+b": writes always append; reads require an explicit seek.
            with open(self.ledger_path, "a+b") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    if digest in self._published_digests(handle):
                        return (0, 0)  # idempotent replay: no delta, no write
                    handle.seek(0, os.SEEK_END)
                    handle.write(payload + b"\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                    return (1, 1)
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
