"""FOREX-FREE-V3 exact accounting kernel (V3-P1, A2 lane) -- F1 REMEDIATED.

Factory-only module: synthetic fixtures, no real-data PnL, no network, no
new data authority.  Every convention below is INHERITED UNCHANGED from the
frozen V2 kernel (research/assets/forex_free_v2/accounting.py, itself the
carried V1 terminal authority) except where this cycle explicitly remediates
the V2 terminal MEDIUM finding F1.

Inherited frozen conventions (carried unchanged from V2):

* PnL identity (frozen USD-unit design)::

      pnl_usd = direction * notional_usd * (exit_price / entry_price - 1)
      direction = +1 for LONG, -1 for SHORT

  The notional is 10000 USD-units BY DESIGN: the result is already USD, so
  no quote-currency conversion exists in this design.  Any request for a
  conversion beyond this identity is refused UNAVAILABLE_FAIL_CLOSED
  (:func:`convert_to_usd_identity`).

* Cost (frozen proxy, a priori; PLAN_forex_v3.md section 2 cost authority):
  1.5 bps per side x stress tier in {1.0, 1.5, 2.0}, charged exactly once
  per fill side.  Round trip = 2 x 1.5 x tier bps = 3.0 / 4.5 / 6.0 bps on
  the notional, i.e. exactly 1.50 / 2.25 / 3.00 USD per side at the 10000
  USD-unit notional.  Costs are never softened.

* Cash accounting is separate from pair accounting: the cash/account
  currency ``USD`` is never a tradable pair (rejected at position open,
  excluded from concentration).  Position book PnL is the cash delta of the
  account; pairs only ever appear as traded instruments.

* The fill list is the single source of truth: every state mutation of
  :class:`PositionBook` appends one :class:`Fill`; turnover and trade
  counts reconcile strictly from fills.  A skipped or missing bar is a
  :class:`NoTrade` sentinel touching neither fills, positions nor costs.

* Digests hash EXACT artifact bytes (:func:`canonical_json_bytes` then
  :func:`sha256_hex`).  A ledger line is exactly the canonical bytes of its
  record plus one newline, so ``sha256(line_bytes)`` is the record digest
  and every line is self-verifying.

* Publication is once-only per record digest
  (:class:`AtomicJsonlPublisher`): fcntl.flock-serialized appends, safe
  across threads and processes on one host; replaying an already-published
  digest is a zero-delta no-op, never a second line.

F1 REMEDIATION (the V2 defect class this kernel makes impossible; V3
lessons register V3-L1, status OPEN_P1_GATE):

    V2 booked "stress" rows NEVER applied the stress-tier cost multipliers:
    tier1.5 rows were byte-identical to base and tier2.0 measured fill
    delay only, at base costs.  The V2 runner looped its tier schedule
    upstream, but the booked net PnL never saw the multiplied cost.

    The V3 kernel closes this at the accounting layer:
    :func:`book_stress` re-books the SAME trade set at each tier of the
    frozen ladder through the same once-per-side cost kernel, so the booked
    stress net PnL is recomputed AT the tier's per-side cost.  The booked
    rows are then certified pairwise distinct across {1.0, 1.5, 2.0}
    whenever the trade set is non-empty
    (:func:`assert_stress_rows_distinct`, called internally -- a collision
    raises ``STRESS_ROWS_NOT_DISTINCT`` and the stress book is refused).
    Gross price PnL is asserted tier-invariant (the same trades are
    re-booked; only the cost changes), which also pins V3-L2: the tier
    delta reported by this kernel is a PURE COST component
    (``cost_component_delta_vs_base_usd``); fill-delay events, if any, are
    carried as separately recorded metadata and never blended into the
    cost stress.

DUAL BOOK (PLAN_forex_v3.md section 2, carry-adjacent scope rule): every
scored record carries ``price_only_pnl_usd`` and
``financing_adjusted_pnl_usd`` as SEPARATE immutable columns.  The columns
live on a frozen record type (:class:`DualBookTrade`) and on the published
record payload built by :func:`build_scored_record`, and both are covered
by the record digest: any post-digest mutation fails
:func:`validate_scored_record` (``DUAL_BOOK_VIOLATION``).  The financing
adjustment is passed in as a parameter; the formula that produces it is
frozen in Phase P3 -- this kernel only carries, sums and digests it, never
computes it.

BREAK-EVEN bps (the V2 innovation, mandatory per cell in V3): derived FROM
THE SAME cost kernel -- see :func:`break_even_bps` for the derivation.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import threading
from dataclasses import dataclass, field, replace
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
    "TradeSpec",
    "StressBookResult",
    "DualBookTrade",
    "canonical_json_bytes",
    "sha256_hex",
    "digest_of",
    "per_side_cost_usd",
    "bps_cost",
    "convert_to_usd_identity",
    "book_round_trips",
    "book_stress",
    "assert_stress_rows_distinct",
    "book_dual",
    "build_scored_record",
    "validate_scored_record",
    "break_even_bps",
    "book_metrics",
    "turnover_from_fills",
    "trades_from_fills",
    "pair_concentration",
    "AtomicJsonlPublisher",
    "ScoredLedgerPublisher",
]

# --- frozen conventions (inherited unchanged from the V2/V1 terminal authority) --- #
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
    TRADE_ID_REUSED, DOUBLE_CLOSE, UNKNOWN_TRADE_ID, EMPTY_TRADE_SET,
    STRESS_ROWS_NOT_DISTINCT, DUAL_BOOK_VIOLATION, ...).
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


# --- frozen cost kernel (single source of the break-even derivation) ---------- #
def per_side_cost_usd(notional_usd: float, bps: float) -> float:
    """Per-side cost in USD at ``bps`` basis points: ``notional * bps / 10000``.

    This is THE cost primitive of the V3 kernel.  The frozen ladder cost
    :func:`bps_cost` and the break-even bps :func:`break_even_bps` are both
    expressed through it, so the break-even is derived from the same kernel
    that charges the costs -- never from an independent formula.
    """
    if isinstance(notional_usd, bool) or not isinstance(notional_usd, (int, float)) \
            or not math.isfinite(float(notional_usd)) or float(notional_usd) <= 0:
        raise PositionBookError("BAD_NOTIONAL", f"notional_usd must be a finite number > 0, got {notional_usd!r}")
    if isinstance(bps, bool) or not isinstance(bps, (int, float)) \
            or not math.isfinite(float(bps)) or float(bps) < 0:
        raise PositionBookError("BAD_BPS", f"bps must be a finite number >= 0, got {bps!r}")
    return float(notional_usd) * float(bps) / 10_000.0


def bps_cost(notional_usd: float, cost_tier: float) -> float:
    """Per-side cost in USD at a frozen stress tier:
    ``per_side_cost_usd(notional, 1.5 * tier)``.

    Frozen authority (PLAN_forex_v3.md section 2 + V2 w2_freeze): 1.5 bps
    per side x stress tier; tier in {1.0, 1.5, 2.0}.  On the 10000 USD-unit
    notional this is exactly 1.50 / 2.25 / 3.00 USD per side.
    """
    tier = _resolve_tier(cost_tier)
    return per_side_cost_usd(float(notional_usd), BASE_BPS_PER_SIDE * tier)


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


def _finite(value: Any, code: str, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) \
            or not math.isfinite(float(value)):
        raise PositionBookError(code, f"{name} must be a finite number, got {value!r}")
    return float(value)


def _round10(value: float) -> float:
    """V2 scored-runner convention: book metrics rounded to 10 decimals."""
    return round(float(value), 10)


def convert_to_usd_identity(amount_usd: float, *, from_currency: str = "USD") -> float:
    """The ONLY USD conversion in the V3 design: the identity.

    Frozen USD-unit convention (inherited unchanged from V1/V2)::

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
    return _finite(amount_usd, "BAD_AMOUNT", "amount_usd")


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

    Cash accounting is separate from pair accounting: the cash currency
    ``USD`` is never a pair.  Rejections (state unchanged,
    :class:`PositionBookError` with ``code``): DOUBLE_OPEN, TRADE_ID_REUSED
    (one lifecycle per trade id, even after close), DOUBLE_CLOSE,
    UNKNOWN_TRADE_ID, BAD_SIDE, BAD_NOTIONAL, BAD_PRICE, BAD_COST_TIER,
    BAD_PAIR (the cash currency is not a pair), BAD_TIMESTAMP.
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
    """Inherited V1/V2-convention concentration: shares of POSITIVE PnL by pair.

    Each pair contributes its positive PnL part (negative/zero contributes
    0.0), shares are ``part / total_positive`` rounded to 6 decimals, and
    when no positive PnL exists every share is ``None``.  The cash/account
    currency ``USD`` is excluded automatically wherever it appears -- cash
    is never a pair and must never enter the concentration denominator.
    """
    parts: dict[str, float] = {}
    total_positive = 0.0
    for pair, pnl in pnl_by_pair.items():
        if pair == CASH_CURRENCY:
            continue
        part = _finite(pnl, "BAD_PNL", f"pnl for {pair!r}")
        part = part if part > 0 else 0.0
        parts[pair] = part
        if part > 0:
            total_positive = math.fsum([total_positive, part])
    if total_positive == 0:
        return {pair: None for pair in parts}
    return {pair: round(part / total_positive, 6) for pair, part in parts.items()}


def book_metrics(pnls: Sequence[float]) -> dict[str, Any]:
    """V2 scored-runner book metrics convention, carried into the kernel.

    ``trades`` / ``total_pnl`` / ``expectancy`` / ``pf`` / ``gross_positive``
    with the V2 rounding (10 decimals; PF None when there are no losers).
    """
    if not pnls:
        return {"trades": 0, "total_pnl": 0.0, "expectancy": 0.0, "pf": 0.0,
                "gross_positive": 0.0}
    gross_pos = math.fsum(p for p in pnls if p > 0)
    gross_neg = -math.fsum(p for p in pnls if p < 0)
    pf = (gross_pos / gross_neg) if gross_neg > 0 else None
    return {
        "trades": len(pnls),
        "total_pnl": _round10(math.fsum(pnls)),
        "expectancy": _round10(math.fsum(pnls) / len(pnls)),
        "pf": _round10(pf) if pf is not None else None,
        "gross_positive": _round10(gross_pos),
    }


# --- trade specs and the F1-fixed stress booking ------------------------------- #
@dataclass(frozen=True)
class TradeSpec:
    """One round trip to be booked identically at every stress tier.

    A spec is the TIER-INVARIANT description of a trade: prices, notional,
    side, timestamps.  All tier-dependent quantities (per-side costs, net
    PnL) are derived at booking time by the cost kernel, never carried on
    the spec.
    """

    trade_id: str
    pair: str
    side: str          # LONG / SHORT
    notional_usd: float
    entry_price: float
    exit_price: float
    entry_ts_utc: str
    exit_ts_utc: str

    def __post_init__(self) -> None:
        if not isinstance(self.trade_id, str) or not self.trade_id:
            raise PositionBookError("BAD_TRADE_ID", f"trade_id must be a non-empty string, got {self.trade_id!r}")
        if not isinstance(self.pair, str) or not self.pair:
            raise PositionBookError("BAD_PAIR", f"pair must be a non-empty string, got {self.pair!r}")
        if self.pair == CASH_CURRENCY:
            raise PositionBookError("BAD_PAIR",
                                    f"{CASH_CURRENCY} is the cash/account currency and is never a pair")
        if self.side not in _SIDES:
            raise PositionBookError("BAD_SIDE", f"side must be one of {_SIDES}, got {self.side!r}")
        _finite_positive(self.notional_usd, "BAD_NOTIONAL", "notional_usd")
        _finite_positive(self.entry_price, "BAD_PRICE", "entry_price")
        _finite_positive(self.exit_price, "BAD_PRICE", "exit_price")
        parse_utc_timestamp(self.entry_ts_utc, field="entry_ts_utc")
        parse_utc_timestamp(self.exit_ts_utc, field="exit_ts_utc")


@dataclass(frozen=True)
class StressBookResult:
    """Booked result of the whole trade set at ONE stress tier (F1-fixed).

    ``net_pnl_usd`` is the booked net of the trade set AT this tier's
    per-side cost -- this is the field whose V2 counterpart was never
    re-costed.  ``cost_component_delta_vs_base_usd`` is the tier delta of
    net PnL versus the base tier; because :func:`book_stress` asserts the
    gross price PnL is tier-invariant, this delta is a PURE COST component
    (V3-L2 separation).  ``fill_delay_events`` is separately recorded
    metadata carried unblended -- it never enters any PnL here.
    """

    cost_tier: float
    n_trades: int
    gross_price_pnl_usd: float
    round_trip_cost_usd: float
    net_pnl_usd: float
    expectancy_usd: float
    metrics: Mapping[str, Any]                       # book_metrics over net PnLs
    cost_component_delta_vs_base_usd: float          # 0.0 at the base tier
    fill_delay_events: Mapping[str, int] | None      # carried, never blended
    booked_rows: tuple[tuple[str, float], ...]       # sorted (trade_id, net_pnl_usd)


def book_round_trips(specs: Sequence[TradeSpec], *, cost_tier: float = 1.0) -> tuple[ClosedTrade, ...]:
    """Book every round-trip spec once per side AT ``cost_tier``.

    Each spec goes through the standard :class:`PositionBook` lifecycle at
    the given tier: the frozen identity gross PnL, the per-side cost
    :func:`bps_cost` charged once at ENTRY and once at EXIT, and the net
    PnL ``gross - entry_cost - exit_cost``.
    """
    tier = _resolve_tier(cost_tier)
    book = PositionBook()
    for spec in specs:
        if not isinstance(spec, TradeSpec):
            raise PositionBookError("BAD_TRADE_SPEC", f"expected TradeSpec, got {spec!r}")
        book.open_position(trade_id=spec.trade_id, pair=spec.pair, side=spec.side,
                           notional_usd=spec.notional_usd, price=spec.entry_price,
                           ts_utc=spec.entry_ts_utc, cost_tier=tier)
        book.close_position(spec.trade_id, spec.exit_price, spec.exit_ts_utc)
    return tuple(book.closed_trades)


def assert_stress_rows_distinct(booked_by_tier: Mapping[float, StressBookResult]) -> None:
    """F1 regression pin: booked stress rows differ pairwise across tiers.

    THE anti-V2-defect assertion.  For a NON-EMPTY trade set, the booked
    rows ``(trade_id, net_pnl_usd)`` of the base tier 1.0 book, the tier
    1.5 book and the tier 2.0 book must be pairwise distinct: each round
    trip pays a strictly larger round-trip cost at a strictly higher tier
    (3.00 < 4.50 < 6.00 USD at the frozen 10000 USD-unit notional) against
    a tier-invariant gross PnL, so ``tier1.5 == base`` or ``tier2.0 ==
    base`` -- the exact byte-identical-row defect V2 shipped -- raises
    ``STRESS_ROWS_NOT_DISTINCT`` here instead of ever reaching a record.
    """
    tiers = sorted(booked_by_tier)
    if tiers != sorted(COST_TIERS):
        raise PositionBookError("BAD_STRESS_TIERS",
                                f"stress certification requires the frozen ladder {COST_TIERS}, got {tiers!r}")
    results = [booked_by_tier[t] for t in sorted(COST_TIERS)]
    if any(r.n_trades <= 0 for r in results) or any(not r.booked_rows for r in results):
        raise PositionBookError("EMPTY_TRADE_SET",
                                "stress-tier distinctness is defined only for a non-empty trade set")
    base, t15, t20 = results
    for left, right, ln, rn in ((base, t15, "1.0", "1.5"),
                                (base, t20, "1.0", "2.0"),
                                (t15, t20, "1.5", "2.0")):
        if left.booked_rows == right.booked_rows:
            raise PositionBookError(
                "STRESS_ROWS_NOT_DISTINCT",
                f"booked stress rows of tier {ln} equal tier {rn}: stress-tier cost "
                "multipliers were not applied to booked stress PnL (the V2 F1 defect)")


def book_stress(
    specs: Sequence[TradeSpec],
    *,
    tiers: Sequence[float] = COST_TIERS,
    fill_delay_events: Mapping[str, int] | None = None,
) -> dict[float, StressBookResult]:
    """F1-FIXED stress booking: re-book the SAME trades at every tier's cost.

    The frozen tier ladder {1.0, 1.5, 2.0} is mandatory.  For each tier the
    identical :class:`TradeSpec` sequence is booked through the once-per-
    side cost kernel at that tier, so the booked stress net PnL is
    RECOMPUTED at the tier's multiplied per-side cost.  The gross price PnL
    is asserted bit-identical across tiers (only the cost may change), and
    :func:`assert_stress_rows_distinct` certifies the booked rows pairwise
    distinct across the ladder for a non-empty trade set -- a collision
    (the V2 F1 defect: stress rows byte-identical to base) fails closed
    instead of publishing.

    ``fill_delay_events`` (V3-L2 separation) is optional metadata mapping
    trade_id -> delayed-fill count.  It is validated and carried on the
    result UNBLENDED: delay stress acts upstream on prices/fills and is
    never a cost component of this kernel, so it changes no PnL here.
    """
    specs = tuple(specs)
    if not specs:
        raise PositionBookError("EMPTY_TRADE_SET",
                                "stress booking over an empty trade set is refused")
    if tuple(sorted(float(t) for t in tiers)) != COST_TIERS:
        raise PositionBookError("BAD_STRESS_TIERS",
                                f"stress booking requires exactly the frozen ladder {COST_TIERS}, got {tiers!r}")
    trade_ids = {s.trade_id for s in specs}
    if len(trade_ids) != len(specs):
        raise PositionBookError("DUPLICATE_TRADE_ID", "trade specs must have unique trade ids")
    delay: dict[str, int] | None = None
    if fill_delay_events is not None:
        if not isinstance(fill_delay_events, Mapping):
            raise PositionBookError("BAD_FILL_DELAY_EVENTS",
                                    "fill_delay_events must be a mapping of trade_id -> non-negative int")
        delay = {}
        for tid, count in fill_delay_events.items():
            if tid not in trade_ids:
                raise PositionBookError("BAD_FILL_DELAY_EVENTS", f"unknown trade_id {tid!r}")
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                raise PositionBookError("BAD_FILL_DELAY_EVENTS",
                                        f"fill delay count for {tid!r} must be a non-negative int, got {count!r}")
            delay[tid] = count

    booked_by_tier: dict[float, StressBookResult] = {}
    gross_by_tier: dict[float, float] = {}
    for tier in COST_TIERS:
        booked = book_round_trips(specs, cost_tier=tier)
        gross = math.fsum(t.pnl_usd for t in booked)
        rt_cost = math.fsum([math.fsum(t.entry_cost_usd for t in booked),
                             math.fsum(t.exit_cost_usd for t in booked)])
        net = math.fsum(t.net_pnl_usd for t in booked)
        gross_by_tier[tier] = gross
        booked_by_tier[tier] = StressBookResult(
            cost_tier=tier,
            n_trades=len(booked),
            gross_price_pnl_usd=gross,
            round_trip_cost_usd=rt_cost,
            net_pnl_usd=net,
            expectancy_usd=_round10(net / len(booked)),
            metrics=book_metrics([t.net_pnl_usd for t in booked]),
            cost_component_delta_vs_base_usd=0.0,  # filled below against base
            fill_delay_events=delay,
            booked_rows=tuple(sorted((t.trade_id, t.net_pnl_usd) for t in booked)),
        )
    base_gross = gross_by_tier[1.0]
    for tier, result in booked_by_tier.items():
        if result.gross_price_pnl_usd != base_gross:
            raise PositionBookError(
                "STRESS_GROSS_NOT_INVARIANT",
                f"tier {tier} re-booked gross PnL {result.gross_price_pnl_usd!r} != base {base_gross!r}: "
                "stress booking must re-book the SAME trades and vary only the cost")
    base_net = booked_by_tier[1.0].net_pnl_usd
    booked_by_tier = {
        tier: replace(r, cost_component_delta_vs_base_usd=_round10(math.fsum([r.net_pnl_usd, -base_net])))
        for tier, r in booked_by_tier.items()
    }
    assert_stress_rows_distinct(booked_by_tier)  # fail closed on any V2-style collision
    return booked_by_tier


# --- dual book: price-only vs financing-adjusted columns ----------------------- #
@dataclass(frozen=True)
class DualBookTrade:
    """One booked trade carrying BOTH book columns, immutably.

    ``price_only_pnl_usd`` is the after-cost PnL from prices alone (gross
    identity PnL minus the once-per-side round-trip cost at the record's
    tier).  ``financing_adjusted_pnl_usd`` is
    ``price_only_pnl_usd + financing_adjustment_usd`` where the adjustment
    is a CARRIED PARAMETER -- the formula that produces it is frozen in
    Phase P3 and this kernel never computes it.  The dataclass is frozen:
    any attribute mutation raises.  Both columns are digest-covered
    wherever the trade appears inside a scored record.
    """

    trade_id: str
    pair: str
    side: str
    cost_tier: float
    notional_usd: float
    entry_price: float
    exit_price: float
    gross_price_pnl_usd: float
    round_trip_cost_usd: float
    price_only_pnl_usd: float
    financing_adjustment_usd: float
    financing_adjusted_pnl_usd: float


def _resolve_financing_adjustments(
    specs: Sequence[TradeSpec],
    financing_adjustment_usd: float | Mapping[str, float],
) -> dict[str, float]:
    """Validate the carried financing adjustment; compute NOTHING.

    Accepts one finite number applied to every trade, or a per-trade
    mapping that must cover EVERY trade id (fail closed).  Values may be
    negative or zero; only finiteness is enforced here.  The formula
    behind the numbers belongs to Phase P3.
    """
    if isinstance(financing_adjustment_usd, Mapping):
        missing = [s.trade_id for s in specs if s.trade_id not in financing_adjustment_usd]
        if missing:
            raise PositionBookError("BAD_FINANCING_ADJUSTMENT",
                                    f"financing adjustment mapping is missing trade ids {missing}")
        return {s.trade_id: _finite(financing_adjustment_usd[s.trade_id],
                                    "BAD_FINANCING_ADJUSTMENT",
                                    f"financing_adjustment_usd[{s.trade_id!r}]")
                for s in specs}
    flat = _finite(financing_adjustment_usd, "BAD_FINANCING_ADJUSTMENT", "financing_adjustment_usd")
    return {s.trade_id: flat for s in specs}


def book_dual(
    specs: Sequence[TradeSpec],
    *,
    cost_tier: float = 1.0,
    financing_adjustment_usd: float | Mapping[str, float] = 0.0,
) -> tuple[DualBookTrade, ...]:
    """Book the trade set once per side and carry BOTH book columns.

    ``price_only_pnl_usd = gross - round_trip_cost`` (costs at ``cost_tier``)
    and ``financing_adjusted_pnl_usd = price_only_pnl_usd + adjustment``,
    with the adjustment carried as a parameter (formula frozen in P3).
    """
    tier = _resolve_tier(cost_tier)
    adjustments = _resolve_financing_adjustments(specs, financing_adjustment_usd)
    booked = book_round_trips(specs, cost_tier=tier)
    dual: list[DualBookTrade] = []
    for spec, closed in zip(specs, booked):
        if closed.trade_id != spec.trade_id:
            raise PositionBookError("BOOK_ORDER_MISMATCH",
                                    f"booked {closed.trade_id!r} out of order for spec {spec.trade_id!r}")
        rt_cost = math.fsum([closed.entry_cost_usd, closed.exit_cost_usd])
        price_only = math.fsum([closed.pnl_usd, -rt_cost])
        adjustment = adjustments[spec.trade_id]
        dual.append(DualBookTrade(
            trade_id=spec.trade_id, pair=spec.pair, side=spec.side, cost_tier=tier,
            notional_usd=spec.notional_usd, entry_price=spec.entry_price,
            exit_price=spec.exit_price,
            gross_price_pnl_usd=closed.pnl_usd,
            round_trip_cost_usd=rt_cost,
            price_only_pnl_usd=price_only,
            financing_adjustment_usd=adjustment,
            financing_adjusted_pnl_usd=math.fsum([price_only, adjustment]),
        ))
    return tuple(dual)


_SCORED_RECORD_REQUIRED_COLUMNS = ("price_only_pnl_usd", "financing_adjusted_pnl_usd")


def build_scored_record(
    dual_trades: Sequence[DualBookTrade],
    *,
    record_id: str,
    cost_tier: float = 1.0,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble a scored record carrying BOTH book columns (digest-covered).

    The returned payload carries ``price_only_pnl_usd`` and
    ``financing_adjusted_pnl_usd`` as separate top-level columns, sums of
    the per-trade frozen columns.  It is published with
    ``published: false``; :meth:`ScoredLedgerPublisher.publish_scored_once`
    flips the flag pre-digest so the WRITTEN ledger row carries
    ``published: true`` (V3-L4) and its self-verifying line digest covers
    both columns.  ``extra`` may add cell metadata; keys must not collide
    with the kernel-owned fields.
    """
    if not isinstance(record_id, str) or not record_id:
        raise PositionBookError("BAD_RECORD_ID", f"record_id must be a non-empty string, got {record_id!r}")
    _resolve_tier(cost_tier)
    record: dict[str, Any] = {
        "schema": "forex_free_v3_scored_record_v1",
        "record_id": record_id,
        "cost_tier": _resolve_tier(cost_tier),
        "n_trades": len(dual_trades),
        "gross_price_pnl_usd": _round10(math.fsum(t.gross_price_pnl_usd for t in dual_trades)),
        "price_only_pnl_usd": _round10(math.fsum(t.price_only_pnl_usd for t in dual_trades)),
        "financing_adjustment_usd": _round10(math.fsum(t.financing_adjustment_usd for t in dual_trades)),
        "financing_adjusted_pnl_usd": _round10(math.fsum(t.financing_adjusted_pnl_usd for t in dual_trades)),
        "dry_run": False,
        "real_pnl": True,
        "published": False,
    }
    if extra:
        collision = sorted(set(extra) & set(record))
        if collision:
            raise PositionBookError("BAD_RECORD_EXTRA", f"extra keys collide with kernel fields: {collision}")
        record.update(extra)
    return record


def validate_scored_record(record: Mapping[str, Any], expected_digest: str) -> None:
    """Fail closed unless the scored record is intact and dual-booked.

    Validation (any failure raises ``DUAL_BOOK_VIOLATION``):

    * both book columns exist as SEPARATE keys and are finite numbers;
    * the record digest, recomputed over the record's exact canonical
      bytes, equals ``expected_digest`` -- so ANY post-digest mutation of
      ANY digest-covered field (including either book column) is refused.
    """
    for column in _SCORED_RECORD_REQUIRED_COLUMNS:
        if column not in record:
            raise PositionBookError("DUAL_BOOK_VIOLATION",
                                    f"scored record is missing the required column {column!r}")
        _finite(record[column], "DUAL_BOOK_VIOLATION", f"column {column!r}")
    observed = digest_of(record)
    if observed != expected_digest:
        raise PositionBookError(
            "DUAL_BOOK_VIOLATION",
            f"record mutated after digest: expected {expected_digest}, observed {observed}")


# --- break-even bps, derived from the same cost kernel -------------------------- #
def break_even_bps(
    gross_pnls_usd: Sequence[float],
    notional_usd: float = FROZEN_NOTIONAL_USD_UNIT,
) -> float | None:
    """Per-side break-even cost in bps: expectancy crosses zero exactly there.

    Derivation FROM THE SAME COST KERNEL (the primitive
    :func:`per_side_cost_usd`, ``cost_usd = notional * bps / 10000``):

        Let G = fsum(gross price PnL) over n round trips at notional N.
        At a per-side cost of b bps, each round trip pays
        ``2 * per_side_cost_usd(N, b) = 2 * N * b / 10000`` USD, so the
        after-cost expectancy is::

            E(b) = G / n - 2 * N * b / 10000

        ``E(b) = 0`` at the break-even::

            b* = (G / n) * 10000 / (2 * N)

    This is literally the inversion of the charging formula -- the same
    kernel that charges 1.5 bps x tier per side answers "how many bps per
    side could I pay before the gross edge is gone".  Comparing ``b*``
    against the frozen band ``1.5 * tier`` gives the stress headroom: a
    cell with ``b* <= 1.5`` has no base-cost headroom, one with
    ``b* < 4.5`` cannot survive tier 1.5, and so on.  At ``b*`` the booked
    net PnL of the same trades is exactly zero; below it positive, above
    it negative.  Returns ``None`` for an empty book and rounds to 6
    decimals (the V2 ``scored_runner.break_even_bps`` publication
    convention, whose formula this function generalizes by parameterizing
    the notional).
    """
    if not gross_pnls_usd:
        return None
    notional = _finite_positive(notional_usd, "BAD_NOTIONAL", "notional_usd")
    gross = math.fsum(_finite(p, "BAD_PNL", "gross_pnls_usd entry") for p in gross_pnls_usd)
    n = len(gross_pnls_usd)
    return round(gross / (n * 2 * notional) * 10_000.0, 6)


# --- once-only canonical JSONL publication ------------------------------------ #
class AtomicJsonlPublisher:
    """fcntl.flock-protected JSONL ledger with once-only publication.

    One record = one line = exactly ``canonical_json_bytes(record)`` plus a
    newline.  The record digest is ``sha256_hex`` of those exact bytes, so
    a ledger line is self-verifying.  ``publish_once`` is once-only per
    digest: under the exclusive lock it rescans the ledger (authoritative,
    restart-safe) and returns ``(observed_delta=1, published_now=1)`` on
    first publication or ``(0, 0)`` on idempotent replay of the same
    digest.  A per-instance ``threading.Lock`` plus ``flock`` serializes
    appends across threads and processes on the same host.
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


class ScoredLedgerPublisher(AtomicJsonlPublisher):
    """Once-only publisher for scored records (V3-L4 fixed by construction).

    ``publish_scored_once`` refuses anything that is not a real, non-dry
    scored record (``REAL_PNL_REQUIRED_FOR_SCORED_PUBLICATION``), flips
    ``published`` to ``True`` BEFORE digesting, and then appends once-only
    by digest under the flock.  The written ledger row therefore carries
    ``"published": true`` and its self-verifying line digest covers the
    flipped flag and both book columns -- the V2 defect of ledger rows
    frozen at ``published: false`` cannot recur through this path.
    """

    def publish_scored_once(self, record: Mapping[str, Any]) -> tuple[int, int]:
        if not isinstance(record, Mapping):
            raise PositionBookError("BAD_RECORD", f"expected a scored record mapping, got {record!r}")
        if record.get("dry_run") or not record.get("real_pnl"):
            raise PositionBookError("REAL_PNL_REQUIRED_FOR_SCORED_PUBLICATION",
                                    "scored publication requires real_pnl=true and dry_run=false")
        # V3-L4: flip the published flag BEFORE digesting, so the written
        # row itself carries published=true covered by its line digest.
        record = dict(record)
        record["published"] = True
        return self.publish_once(record)
