"""Stock accounting: canonical identity, USD ledger, borrow/dividend (owner: A5).

PLAN_stocks.md section 7 (A5).  Everything here is implemented strictly
against the frozen common interfaces (``research.assets.common``); this
module never edits them.

Canonical identity (floats with a declared tolerance, plus an exact
Decimal path for hand-computed goldens)::

    ending_equity - starting_equity
    = realized_price_pnl + terminal_pnl + cash_dividends
      - commissions - spread - slippage - market_impact
      - short_borrow_fees - short_dividend_liability - rejection_costs

Conventions (fail-closed, no silent defaults):

* USD cash account only; any other currency is a construction error.
* Average-cost position bookkeeping; realized price PnL is recognized on
  every fill that reduces an existing position.
* Terminal valuation happens on the LAST OBSERVABLE EXECUTABLE EVENT only
  (:class:`ObservableEvent` records arrive as inputs; no calendar logic
  lives here — the calendar is another lane's module).
* Borrow/dividend events arrive as explicit input records; no dependence
  on another lane's corporate-actions module.
* An unavailable borrow locate REJECTS the short sale; a short is never
  filled for free and a locate rejection books zero cost.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence

from research.assets.common.carrying_cost import (
    EquityBorrowDividendCarry,
    CashflowLine,
)
from research.assets.common.contracts import require_finite_float, require_token

#: Declared float tolerance (USD) for the canonical identity.
FLOAT_IDENTITY_TOLERANCE_USD = 1e-9

#: Day-count basis for equity borrow fees (street convention).
BORROW_DAY_COUNT_BASIS = 360

_COST_TERMS = (
    "commissions",
    "spread",
    "slippage",
    "market_impact",
    "short_borrow_fees",
    "short_dividend_liability",
    "rejection_costs",
)
_PNL_TERMS = (
    "realized_price_pnl",
    "terminal_pnl",
    "cash_dividends",
)


def _require_iso_utc(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty ISO-8601 UTC string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} is not ISO-8601: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware (UTC): {value!r}")
    return value


# --- identity --------------------------------------------------------------- #
@dataclass(frozen=True)
class IdentityTerms:
    """Every term of the canonical identity, explicitly materialized.

    Cost terms must be >= 0; PnL/dividend terms may take either sign
    (``cash_dividends`` is a receipts bucket and must be >= 0).
    """

    starting_equity: float
    ending_equity: float
    realized_price_pnl: float
    terminal_pnl: float
    cash_dividends: float
    commissions: float
    spread: float
    slippage: float
    market_impact: float
    short_borrow_fees: float
    short_dividend_liability: float
    rejection_costs: float

    def __post_init__(self) -> None:
        for name in (
            "starting_equity",
            "ending_equity",
        ) + _PNL_TERMS + _COST_TERMS:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be a number, got {value!r}")
            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite, got {value!r}")
        for name in _COST_TERMS + ("cash_dividends",):
            if float(getattr(self, name)) < 0.0:
                raise ValueError(f"{name} must be >= 0, got {getattr(self, name)!r}")

    @property
    def lhs(self) -> float:
        """``ending_equity - starting_equity`` (fsum for float hygiene)."""
        return math.fsum((float(self.ending_equity), -float(self.starting_equity)))

    @property
    def rhs(self) -> float:
        """The right-hand side of the canonical identity (fsum)."""
        return math.fsum((
            float(self.realized_price_pnl),
            float(self.terminal_pnl),
            float(self.cash_dividends),
            -float(self.commissions),
            -float(self.spread),
            -float(self.slippage),
            -float(self.market_impact),
            -float(self.short_borrow_fees),
            -float(self.short_dividend_liability),
            -float(self.rejection_costs),
        ))

    @property
    def residual(self) -> float:
        """``lhs - rhs``; zero (within tolerance) means the books close."""
        return math.fsum((self.lhs, -self.rhs))

    def assert_closes(self, tolerance: float = FLOAT_IDENTITY_TOLERANCE_USD) -> None:
        if not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or tolerance < 0:
            raise ValueError(f"tolerance must be a finite float >= 0, got {tolerance!r}")
        if abs(self.residual) > tolerance:
            raise IdentityBreakError(self, tolerance)


class IdentityBreakError(AssertionError):
    """The canonical identity does not close within the declared tolerance."""

    def __init__(self, terms: IdentityTerms, tolerance: float) -> None:
        self.terms = terms
        self.tolerance = float(tolerance)
        super().__init__(
            "IDENTITY BREAK: residual "
            f"{terms.residual!r} exceeds tolerance {tolerance!r}; "
            f"lhs={terms.lhs!r} rhs={terms.rhs!r} terms={terms!r}"
        )


# --- exact Decimal path (goldens only) --------------------------------------- #
def _to_decimal(value: str | Decimal | int | float, name: str) -> Decimal:
    try:
        converted = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{name} is not decimal-convertible: {value!r}") from exc
    if not converted.is_finite():
        raise ValueError(f"{name} must be finite, got {value!r}")
    return converted


def identity_residual_exact(
    terms: Mapping[str, str | Decimal | int | float],
) -> Decimal:
    """EXACT Decimal residual of the canonical identity (golden path).

    Every term is converted with ``Decimal(str(v))`` so goldens written as
    decimal strings close to exactly ``Decimal("0")`` — no float noise.
    """
    missing = [
        name
        for name in ("starting_equity", "ending_equity") + _PNL_TERMS + _COST_TERMS
        if name not in terms
    ]
    if missing:
        raise ValueError(f"exact identity payload missing terms: {sorted(missing)}")
    lhs = _to_decimal(terms["ending_equity"], "ending_equity") - _to_decimal(
        terms["starting_equity"], "starting_equity"
    )
    rhs = math_fsum_decimal((
        _to_decimal(terms["realized_price_pnl"], "realized_price_pnl"),
        _to_decimal(terms["terminal_pnl"], "terminal_pnl"),
        _to_decimal(terms["cash_dividends"], "cash_dividends"),
        -_to_decimal(terms["commissions"], "commissions"),
        -_to_decimal(terms["spread"], "spread"),
        -_to_decimal(terms["slippage"], "slippage"),
        -_to_decimal(terms["market_impact"], "market_impact"),
        -_to_decimal(terms["short_borrow_fees"], "short_borrow_fees"),
        -_to_decimal(terms["short_dividend_liability"], "short_dividend_liability"),
        -_to_decimal(terms["rejection_costs"], "rejection_costs"),
    ))
    return lhs - rhs


def math_fsum_decimal(values: Sequence[Decimal]) -> Decimal:
    """Exact left-to-right sum; Decimal addition of finites is exact here."""
    total = Decimal("0")
    for value in values:
        total += value
    return total


def assert_identity_exact(terms: Mapping[str, str | Decimal | int | float]) -> Decimal:
    """Exact-path closure: residual must be exactly ``Decimal("0")``."""
    residual = identity_residual_exact(terms)
    if residual != Decimal("0"):
        raise IdentityBreakExactError(residual, dict(terms))
    return residual


class IdentityBreakExactError(AssertionError):
    def __init__(self, residual: Decimal, terms: Mapping[str, Any]) -> None:
        self.residual = residual
        super().__init__(
            f"EXACT IDENTITY BREAK: residual={residual} (must be exactly 0); "
            f"terms={terms!r}"
        )


# --- input records ----------------------------------------------------------- #
@dataclass(frozen=True)
class CostBreakdown:
    """Per-fill execution cost components (all >= 0, all explicit)."""

    commission: float
    spread: float
    slippage: float
    market_impact: float

    def __post_init__(self) -> None:
        for name in ("commission", "spread", "slippage", "market_impact"):
            value = getattr(self, name)
            require_finite_float(value, name)
            if float(value) < 0.0:
                raise ValueError(f"{name} must be >= 0, got {value!r}")

    @classmethod
    def zero(cls) -> "CostBreakdown":
        return cls(commission=0.0, spread=0.0, slippage=0.0, market_impact=0.0)

    def total(self) -> float:
        return math.fsum((
            float(self.commission),
            float(self.spread),
            float(self.slippage),
            float(self.market_impact),
        ))


@dataclass(frozen=True)
class FillRecord:
    """One executed fill with its cost breakdown (input to the ledger)."""

    symbol: str
    side: str
    quantity: float
    price: float
    timestamp_utc: str
    cost: CostBreakdown
    fill_id: str | None = None

    def __post_init__(self) -> None:
        require_token(self.symbol, "symbol")
        if self.side not in ("BUY", "SELL"):
            raise ValueError(f"side must be BUY or SELL, got {self.side!r}")
        require_finite_float(self.quantity, "quantity")
        if float(self.quantity) <= 0:
            raise ValueError(f"quantity must be > 0, got {self.quantity!r}")
        require_finite_float(self.price, "price")
        if float(self.price) <= 0:
            raise ValueError(f"price must be > 0, got {self.price!r}")
        _require_iso_utc(self.timestamp_utc, "timestamp_utc")
        if not isinstance(self.cost, CostBreakdown):
            raise ValueError("cost must be a CostBreakdown")
        if self.fill_id is not None:
            require_token(self.fill_id, "fill_id")

    @property
    def notional(self) -> float:
        return float(self.quantity) * float(self.price)

    @property
    def signed_quantity(self) -> float:
        return float(self.quantity) if self.side == "BUY" else -float(self.quantity)


@dataclass(frozen=True)
class OrderRejection:
    """A rejected order; booked as evidence, never as a fill."""

    symbol: str
    side: str
    quantity: float
    reason: str
    timestamp_utc: str
    cost: float = 0.0

    def __post_init__(self) -> None:
        require_token(self.symbol, "symbol")
        if self.side not in ("BUY", "SELL"):
            raise ValueError(f"side must be BUY or SELL, got {self.side!r}")
        require_finite_float(self.quantity, "quantity")
        if float(self.quantity) <= 0:
            raise ValueError(f"quantity must be > 0, got {self.quantity!r}")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string")
        _require_iso_utc(self.timestamp_utc, "timestamp_utc")
        require_finite_float(self.cost, "cost")
        if float(self.cost) < 0.0:
            raise ValueError(f"cost must be >= 0, got {self.cost!r}")


@dataclass(frozen=True)
class DividendEvent:
    """A cash-dividend ex-date event (arrives as an input record)."""

    symbol: str
    dividend_per_share: float
    ex_date_utc: str

    def __post_init__(self) -> None:
        require_token(self.symbol, "symbol")
        require_finite_float(self.dividend_per_share, "dividend_per_share")
        if float(self.dividend_per_share) <= 0:
            raise ValueError(
                f"dividend_per_share must be > 0, got {self.dividend_per_share!r}"
            )
        _require_iso_utc(self.ex_date_utc, "ex_date_utc")


@dataclass(frozen=True)
class BorrowLocate:
    """Point-in-time locate availability + borrow rate for one short.

    ``available=False`` means NO locate: the short must be rejected, never
    filled free.  An available locate REQUIRES its PIT ``annual_rate``.
    """

    symbol: str
    as_of_utc: str
    available: bool
    annual_rate: float | None

    def __post_init__(self) -> None:
        require_token(self.symbol, "symbol")
        _require_iso_utc(self.as_of_utc, "as_of_utc")
        if not isinstance(self.available, bool):
            raise ValueError(f"available must be a bool, got {self.available!r}")
        if self.available:
            if self.annual_rate is None:
                raise ValueError("an available locate REQUIRES annual_rate (PIT)")
            require_finite_float(self.annual_rate, "annual_rate")
            if float(self.annual_rate) < 0:
                raise ValueError(f"annual_rate must be >= 0, got {self.annual_rate!r}")
        elif self.annual_rate is not None:
            raise ValueError("an unavailable locate must not carry annual_rate")


@dataclass(frozen=True)
class ObservableEvent:
    """One observable market event with an explicit executability flag."""

    timestamp_utc: str
    price: float
    executable: bool

    def __post_init__(self) -> None:
        _require_iso_utc(self.timestamp_utc, "timestamp_utc")
        require_finite_float(self.price, "price")
        if float(self.price) <= 0:
            raise ValueError(f"price must be > 0, got {self.price!r}")
        if not isinstance(self.executable, bool):
            raise ValueError(f"executable must be a bool, got {self.executable!r}")


def last_executable_event(events: Sequence[ObservableEvent]) -> ObservableEvent:
    """The LAST observable EXECUTABLE event of an ordered sequence.

    Terminal valuation uses only this event; later non-executable prints
    are ignored.  Fails closed when no executable event exists.
    """
    if not isinstance(events, (list, tuple)) or not events:
        raise ValueError("events must be a non-empty sequence of ObservableEvent")
    for event in events:
        if not isinstance(event, ObservableEvent):
            raise ValueError(f"expected ObservableEvent, got {event!r}")
    for event in reversed(events):
        if event.executable:
            return event
    raise ValueError("no executable event in sequence; terminal valuation fails closed")


# --- the ledger -------------------------------------------------------------- #
@dataclass
class _Position:
    qty: float
    avg_cost: float


class IdentityLedger:
    """USD cash ledger with average-cost positions and explicit buckets.

    ``ending_equity`` is mark-to-market: ``cash + sum(qty * terminal_mark)``.
    With average-cost accounting the canonical identity closes by
    construction — the ledger exists to PROVE it on every replay.
    """

    def __init__(self, *, starting_equity: float, currency: str = "USD") -> None:
        require_finite_float(starting_equity, "starting_equity")
        require_token(currency, "currency")
        if currency != "USD":
            raise ValueError(f"stocks lane books USD only, got {currency!r}")
        self.starting_equity = float(starting_equity)
        self.currency = currency
        self.cash = float(starting_equity)
        self._positions: dict[str, _Position] = {}
        self._marks: dict[str, ObservableEvent] = {}
        self._fills: tuple[FillRecord, ...] = ()
        self._rejections: tuple[OrderRejection, ...] = ()
        self._totals: dict[str, float] = {name: 0.0 for name in _PNL_TERMS + _COST_TERMS}
        self._per_symbol: dict[str, dict[str, float]] = {}

    # -- reads -------------------------------------------------------------- #
    @property
    def fills(self) -> tuple[FillRecord, ...]:
        return self._fills

    @property
    def rejections(self) -> tuple[OrderRejection, ...]:
        return self._rejections

    def position_qty(self, symbol: str) -> float:
        require_token(symbol, "symbol")
        pos = self._positions.get(symbol)
        return 0.0 if pos is None else pos.qty

    def open_positions(self) -> Mapping[str, float]:
        return {s: p.qty for s, p in self._positions.items() if p.qty != 0.0}

    def bucket(self, name: str) -> float:
        if name not in self._totals:
            raise ValueError(f"unknown identity bucket {name!r}")
        return self._totals[name]

    def mark_to_market_equity(self) -> float:
        """``cash + sum(open qty * mark)``; every open position needs a mark."""
        parts = [self.cash]
        for symbol, pos in self._positions.items():
            if pos.qty == 0.0:
                continue
            mark = self._marks.get(symbol)
            if mark is None:
                raise ValueError(
                    f"open position in {symbol!r} has no terminal mark; "
                    "terminal valuation fails closed"
                )
            parts.append(pos.qty * float(mark.price))
        return math.fsum(parts)

    def identity_terms(self) -> IdentityTerms:
        return IdentityTerms(
            starting_equity=self.starting_equity,
            ending_equity=self.mark_to_market_equity(),
            realized_price_pnl=self._totals["realized_price_pnl"],
            terminal_pnl=self._totals["terminal_pnl"],
            cash_dividends=self._totals["cash_dividends"],
            commissions=self._totals["commissions"],
            spread=self._totals["spread"],
            slippage=self._totals["slippage"],
            market_impact=self._totals["market_impact"],
            short_borrow_fees=self._totals["short_borrow_fees"],
            short_dividend_liability=self._totals["short_dividend_liability"],
            rejection_costs=self._totals["rejection_costs"],
        )

    def assert_closed(self, tolerance: float = FLOAT_IDENTITY_TOLERANCE_USD) -> None:
        self.identity_terms().assert_closes(tolerance)

    def symbol_contribution(self, symbol: str) -> dict[str, float]:
        """Per-symbol contribution to the identity (cash-accounting terms)."""
        require_token(symbol, "symbol")
        return dict(self._per_symbol.get(symbol, {name: 0.0 for name in _PNL_TERMS + _COST_TERMS}))

    def symbol_contributions(self) -> dict[str, dict[str, float]]:
        return {symbol: dict(terms) for symbol, terms in self._per_symbol.items()}

    # -- writes ------------------------------------------------------------- #
    def _bump(self, name: str, symbol: str, amount: float) -> None:
        self._totals[name] = math.fsum((self._totals[name], amount))
        row = self._per_symbol.setdefault(
            symbol, {term: 0.0 for term in _PNL_TERMS + _COST_TERMS}
        )
        row[name] = math.fsum((row[name], amount))

    def apply_fill(self, fill: FillRecord) -> None:
        """Book one fill: cash moves, average-cost position updates, buckets."""
        if not isinstance(fill, FillRecord):
            raise ValueError(f"expected FillRecord, got {fill!r}")
        cost = fill.cost.total()
        self.cash = math.fsum((self.cash, -fill.signed_quantity * float(fill.price), -cost))
        self._bump("commissions", fill.symbol, float(fill.cost.commission))
        self._bump("spread", fill.symbol, float(fill.cost.spread))
        self._bump("slippage", fill.symbol, float(fill.cost.slippage))
        self._bump("market_impact", fill.symbol, float(fill.cost.market_impact))

        pos = self._positions.get(fill.symbol)
        if pos is None or pos.qty == 0.0 or pos.qty * fill.signed_quantity > 0.0:
            # Opening or increasing: blend the average cost.
            if pos is None or pos.qty == 0.0:
                self._positions[fill.symbol] = _Position(
                    qty=fill.signed_quantity, avg_cost=float(fill.price)
                )
            else:
                new_qty = math.fsum((pos.qty, fill.signed_quantity))
                new_avg = math.fsum((
                    abs(pos.qty) * pos.avg_cost,
                    float(fill.quantity) * float(fill.price),
                )) / abs(new_qty)
                self._positions[fill.symbol] = _Position(qty=new_qty, avg_cost=new_avg)
        else:
            # Reducing / crossing: realize PnL on the closed quantity.
            closed = min(abs(pos.qty), float(fill.quantity))
            if pos.qty > 0:
                realized = math.fsum((float(fill.price), -pos.avg_cost)) * closed
            else:
                realized = math.fsum((pos.avg_cost, -float(fill.price))) * closed
            self._bump("realized_price_pnl", fill.symbol, realized)
            remaining = math.fsum((float(fill.quantity), -closed))
            new_qty = math.fsum((pos.qty, fill.signed_quantity))
            if remaining > 0.0:
                # Crossed through zero into the opposite direction.
                self._positions[fill.symbol] = _Position(
                    qty=fill.signed_quantity / float(fill.quantity) * remaining,
                    avg_cost=float(fill.price),
                )
            else:
                self._positions[fill.symbol] = _Position(qty=new_qty, avg_cost=pos.avg_cost)
        self._fills = self._fills + (fill,)

    def record_rejection(self, rejection: OrderRejection) -> None:
        """Book a rejected order: evidence + optional venue fee, NO fill."""
        if not isinstance(rejection, OrderRejection):
            raise ValueError(f"expected OrderRejection, got {rejection!r}")
        self._bump("rejection_costs", rejection.symbol, float(rejection.cost))
        self.cash = math.fsum((self.cash, -float(rejection.cost)))
        self._rejections = self._rejections + (rejection,)

    def apply_dividend(self, event: DividendEvent) -> CashflowLine | None:
        """Ex-date cash dividend: longs receive, shorts owe the liability.

        A flat position books NOTHING (no event, no cashflow) — dividends
        apply only to positions HELD through the ex-date.
        """
        if not isinstance(event, DividendEvent):
            raise ValueError(f"expected DividendEvent, got {event!r}")
        pos = self._positions.get(event.symbol)
        if pos is None or pos.qty == 0.0:
            return None
        if pos.qty > 0:
            amount = math.fsum((float(event.dividend_per_share) * pos.qty,))
            self.cash = math.fsum((self.cash, amount))
            self._bump("cash_dividends", event.symbol, amount)
            note = "cash dividend receipt"
        else:
            amount = math.fsum((float(event.dividend_per_share) * abs(pos.qty),))
            self.cash = math.fsum((self.cash, -amount))
            self._bump("short_dividend_liability", event.symbol, amount)
            note = "short dividend liability"
        return CashflowLine(
            timestamp_utc=event.ex_date_utc,
            amount=amount if pos.qty > 0 else -amount,
            currency=self.currency,
            kind="DIVIDEND",
            instrument_symbol=event.symbol,
            note=note,
        )

    def accrue_borrow_fee(self, *, symbol: str, amount: float, timestamp_utc: str) -> CashflowLine:
        """Book one borrow-fee accrual against an OPEN short (fail closed).

        ``amount >= 0`` (use :func:`compute_borrow_fee` to size it).  A fee
        without an open short in ``symbol`` is an accounting error and raises.
        """
        require_token(symbol, "symbol")
        require_finite_float(amount, "amount")
        if amount < 0:
            raise ValueError(f"amount must be >= 0, got {amount!r}")
        _require_iso_utc(timestamp_utc, "timestamp_utc")
        pos = self._positions.get(symbol)
        if pos is None or pos.qty >= 0.0:
            raise ValueError(
                f"borrow fee accrual for {symbol!r} without an open short; "
                "fees accrue only while a short is held"
            )
        self.cash = math.fsum((self.cash, -amount))
        self._bump("short_borrow_fees", symbol, amount)
        return CashflowLine(
            timestamp_utc=timestamp_utc,
            amount=-amount,
            currency=self.currency,
            kind="BORROW",
            instrument_symbol=symbol,
            note="borrow fee accrual",
        )

    def mark_terminal(self, symbol: str, event: ObservableEvent) -> ObservableEvent:
        """Attach ONE terminal mark and book the terminal PnL it implies.

        The event must be EXECUTABLE (terminal valuation happens on the last
        observable executable event only — a non-executable print is never a
        mark).  Marking a symbol twice is an accounting error and raises.
        Open positions book ``terminal_pnl += qty * (mark - avg_cost)``;
        flat symbols only record the mark.
        """
        require_token(symbol, "symbol")
        if not isinstance(event, ObservableEvent):
            raise ValueError(f"expected ObservableEvent for {symbol!r}, got {event!r}")
        if not event.executable:
            raise ValueError(
                f"terminal mark for {symbol!r} must be an EXECUTABLE event; "
                "never valuate on a halt/closed print"
            )
        if symbol in self._marks:
            raise ValueError(f"{symbol!r} is already terminal-marked")
        pos = self._positions.get(symbol)
        if pos is not None and pos.qty != 0.0:
            terminal_pnl = math.fsum((pos.qty * float(event.price), -pos.qty * pos.avg_cost))
            self._bump("terminal_pnl", symbol, terminal_pnl)
        self._marks[symbol] = event
        return event

    def finalize_terminal(self, symbol: str, events: Sequence[ObservableEvent]) -> ObservableEvent:
        """Terminal-valuate one symbol on its LAST observable executable event."""
        require_token(symbol, "symbol")
        return self.mark_terminal(symbol, last_executable_event(events))


# --- borrow / dividend handling ---------------------------------------------- #
def compute_borrow_fee(
    *,
    price: float,
    quantity: float,
    annual_rate: float,
    days: float,
    day_count_basis: float = BORROW_DAY_COUNT_BASIS,
) -> float:
    """Borrow fee for one accrual: ``price * qty * rate * days / basis``."""
    require_finite_float(price, "price")
    if price <= 0:
        raise ValueError(f"price must be > 0, got {price!r}")
    require_finite_float(quantity, "quantity")
    if quantity <= 0:
        raise ValueError(f"quantity must be > 0, got {quantity!r}")
    require_finite_float(annual_rate, "annual_rate")
    if annual_rate < 0:
        raise ValueError(f"annual_rate must be >= 0, got {annual_rate!r}")
    require_finite_float(days, "days")
    if days < 0:
        raise ValueError(f"days must be >= 0, got {days!r}")
    require_finite_float(day_count_basis, "day_count_basis")
    if day_count_basis <= 0:
        raise ValueError(f"day_count_basis must be > 0, got {day_count_basis!r}")
    return math.fsum((price * quantity * annual_rate * days / day_count_basis,))


def submit_short_sale(
    ledger: IdentityLedger,
    fill: FillRecord,
    locate: BorrowLocate | None,
    *,
    timestamp_utc: str,
) -> bool:
    """Locate-gated short sale: unavailable borrow REJECTS, never fills free.

    Returns True when the fill was booked, False when the order was rejected
    (a zero-cost rejection record is kept either way — a missing locate and
    an unavailable locate are distinct reasons, both cost nothing here).
    """
    if not isinstance(ledger, IdentityLedger):
        raise ValueError(f"expected IdentityLedger, got {ledger!r}")
    if not isinstance(fill, FillRecord):
        raise ValueError(f"expected FillRecord, got {fill!r}")
    _require_iso_utc(timestamp_utc, "timestamp_utc")
    if locate is None:
        reason = "MISSING_LOCATE"
    elif locate.symbol != fill.symbol:
        reason = "LOCATE_SYMBOL_MISMATCH"
    elif not locate.available:
        reason = "NO_LOCATE"
    else:
        reason = None
    if reason is not None:
        ledger.record_rejection(
            OrderRejection(
                symbol=fill.symbol,
                side=fill.side,
                quantity=fill.quantity,
                reason=reason,
                timestamp_utc=timestamp_utc,
                cost=0.0,
            )
        )
        return False
    ledger.apply_fill(fill)
    return True


class StockBorrowDividendCarry(EquityBorrowDividendCarry):
    """Equity borrow + dividend carry implementing the frozen common interface.

    Cashflows are signed :class:`CashflowLine` records: shorts pay borrow
    fees (``kind="BORROW"``) and dividend liabilities on ex-dates
    (``kind="DIVIDEND"``, negative); longs receive cash dividends
    (``kind="DIVIDEND"``, positive).  Rates and dividend events arrive as
    explicit PIT context — nothing is defaulted or fetched.
    """

    def __init__(self, *, model_id: str = "STOCKS_BORROW_DIVIDEND_V1") -> None:
        require_token(model_id, "model_id")
        self._model_id = model_id

    @property
    def model_id(self) -> str:
        return self._model_id

    def cashflows(
        self,
        *,
        instrument_symbol: str,
        position_qty: float,
        interval_start_utc: str,
        interval_end_utc: str,
        context: Mapping[str, Any] | None = None,
    ) -> tuple[CashflowLine, ...]:
        require_token(instrument_symbol, "instrument_symbol")
        require_finite_float(position_qty, "position_qty")
        _require_iso_utc(interval_start_utc, "interval_start_utc")
        _require_iso_utc(interval_end_utc, "interval_end_utc")
        ctx: Mapping[str, Any] = {} if context is None else context
        start = datetime.fromisoformat(interval_start_utc.replace("Z", "+00:00"))
        end = datetime.fromisoformat(interval_end_utc.replace("Z", "+00:00"))
        if end <= start:
            raise ValueError("interval_end_utc must be after interval_start_utc")
        lines: list[CashflowLine] = []
        qty = float(position_qty)

        if qty == 0.0:
            # A flat position holds nothing: no borrow, no dividend cashflow.
            return ()

        if qty < 0.0:
            # Shorts accrue borrow fees while held (PIT rate + mark required).
            rate = ctx.get("borrow_rate_annual")
            price = ctx.get("price")
            if rate is None:
                raise ValueError(
                    "short position requires borrow_rate_annual in context "
                    "(no free borrow, no default rate)"
                )
            if price is None:
                raise ValueError("short position requires price (notional mark) in context")
            days = (end - start).total_seconds() / 86400.0
            fee = compute_borrow_fee(
                price=float(price),
                quantity=abs(qty),
                annual_rate=float(rate),
                days=days,
            )
            lines.append(
                CashflowLine(
                    timestamp_utc=interval_end_utc,
                    amount=-fee,
                    currency="USD",
                    kind="BORROW",
                    instrument_symbol=instrument_symbol,
                    note=f"borrow fee {float(rate)!r} annual, {days!r} days",
                )
            )

        for event in ctx.get("dividend_events", ()):
            dps = event["dividend_per_share"]
            require_finite_float(dps, "dividend_per_share")
            if float(dps) <= 0:
                raise ValueError(f"dividend_per_share must be > 0, got {dps!r}")
            stamp = _require_iso_utc(event["timestamp_utc"], "dividend timestamp_utc")
            amount = float(dps) * qty  # long: +dps*qty ; short: -dps*|qty|
            lines.append(
                CashflowLine(
                    timestamp_utc=stamp,
                    amount=amount,
                    currency="USD",
                    kind="DIVIDEND",
                    instrument_symbol=instrument_symbol,
                    note="cash dividend receipt" if qty > 0 else "short dividend liability",
                )
            )
        return tuple(lines)
