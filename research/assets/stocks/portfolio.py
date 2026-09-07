"""Shared-capital multi-arm replay interface (owner: A5).

PLAN_stocks.md section 7 (A5): several arms/strategies trade against ONE
USD equity account.  This module is INTERFACE + ACCOUNTING only — it
contains no strategy logic; strategies implement :class:`ReplayArm`.

Accounting model:

* one shared USD cash account (``starting_equity``);
* each arm owns an :class:`~research.assets.stocks.accounting.IdentityLedger`
  attribution book with ``starting_equity=0``; shared cash is
  ``starting_equity + sum(arm cash deltas)``;
* the canonical identity closes PER ARM and for the WHOLE account, and the
  account terms are the field-wise sums of the arm terms (no double count);
* concentration helper: per-symbol share of positive PnL per arm.

Every fill/rejection/carry event arrives through explicit booking methods;
nothing is inferred and nothing writes to disk.
"""

from __future__ import annotations

import abc
import math
from dataclasses import dataclass
from typing import Any, Mapping

from research.assets.common.contracts import require_finite_float, require_token

from research.assets.stocks.accounting import (
    BorrowLocate,
    DividendEvent,
    IdentityLedger,
    IdentityTerms,
    ObservableEvent,
    OrderRejection,
    FLOAT_IDENTITY_TOLERANCE_USD,
)
from research.assets.stocks.execution import ExecutionDecision

_TERM_FIELDS = (
    "realized_price_pnl",
    "terminal_pnl",
    "cash_dividends",
    "commissions",
    "spread",
    "slippage",
    "market_impact",
    "short_borrow_fees",
    "short_dividend_liability",
    "rejection_costs",
)
_PNL_TERMS = ("realized_price_pnl", "terminal_pnl", "cash_dividends")
_COST_TERMS = (
    "commissions",
    "spread",
    "slippage",
    "market_impact",
    "short_borrow_fees",
    "short_dividend_liability",
    "rejection_costs",
)


# --- replay interface (strategies implement this; no logic here) --------------- #
@dataclass(frozen=True)
class OrderIntent:
    """An arm's intent to trade; becomes a fill decision through the model."""

    symbol: str
    side: str
    quantity: float

    def __post_init__(self) -> None:
        require_token(self.symbol, "symbol")
        if self.side not in ("BUY", "SELL"):
            raise ValueError(f"side must be BUY or SELL, got {self.side!r}")
        require_finite_float(self.quantity, "quantity")
        if float(self.quantity) <= 0:
            raise ValueError(f"quantity must be > 0, got {self.quantity!r}")


class ReplayArm(abc.ABC):
    """Interface one arm/strategy implements.  NO strategy logic lives here."""

    @property
    @abc.abstractmethod
    def arm_id(self) -> str:
        """Stable identifier of this arm inside the shared account."""

    @abc.abstractmethod
    def decide(self, event: Mapping[str, Any]) -> tuple[OrderIntent, ...]:
        """Orders proposed for one replay event (pure; must not book anything)."""


# --- concentration helper ------------------------------------------------------- #
def positive_pnl_shares(
    contributions: Mapping[str, Mapping[str, float]],
) -> dict[str, float]:
    """Per-symbol share of POSITIVE PnL over a set of symbol contributions.

    A symbol's PnL is ``realized + terminal + cash dividends - costs``
    (contribution dicts carry RAW bucket values, so the cost terms are
    subtracted here).  Only positive PnL enters the denominator;
    non-positive symbols get no share.  Returns ``{}`` when nothing is
    positive (no division by zero, no fake zeros).
    """
    positive: dict[str, float] = {}
    for symbol, terms in contributions.items():
        require_token(symbol, "symbol")
        missing = [name for name in _TERM_FIELDS if name not in terms]
        if missing:
            raise ValueError(f"contribution for {symbol!r} missing terms: {sorted(missing)}")
        pnl = math.fsum((
            math.fsum([float(terms[name]) for name in _PNL_TERMS]),
            -math.fsum([float(terms[name]) for name in _COST_TERMS]),
        ))
        if pnl > 0.0:
            positive[symbol] = pnl
    total = math.fsum(positive.values())
    if total <= 0.0:
        return {}
    return {symbol: pnl / total for symbol, pnl in positive.items()}


# --- shared-capital replay ------------------------------------------------------- #
class SharedCapitalReplay:
    """Several arms against one USD equity account (accounting core only).

    Booking methods accept already-decided events; the driver is the
    caller.  Nothing here proposes trades, reads a calendar, or writes
    files — this is the capital-accounting substrate of the replay.
    """

    def __init__(self, *, starting_equity: float, currency: str = "USD") -> None:
        require_finite_float(starting_equity, "starting_equity")
        require_token(currency, "currency")
        if currency != "USD":
            raise ValueError(f"stocks lane books USD only, got {currency!r}")
        self.starting_equity = float(starting_equity)
        self.currency = currency
        self._books: dict[str, IdentityLedger] = {}

    # -- arms ------------------------------------------------------------------ #
    def register_arm(self, arm_id: str) -> None:
        require_token(arm_id, "arm_id")
        if arm_id in self._books:
            raise ValueError(f"arm {arm_id!r} is already registered")
        # Attribution book: starting equity 0; the shared account carries capital.
        self._books[arm_id] = IdentityLedger(starting_equity=0.0, currency=self.currency)

    def require_arm(self, arm_id: str) -> IdentityLedger:
        require_token(arm_id, "arm_id")
        try:
            return self._books[arm_id]
        except KeyError:
            raise ValueError(f"unknown arm {arm_id!r}; register it first") from None

    @property
    def arm_ids(self) -> tuple[str, ...]:
        return tuple(self._books)

    # -- booking ---------------------------------------------------------------- #
    def book_decision(self, arm_id: str, decision: ExecutionDecision) -> None:
        """Book an :class:`ExecutionDecision`: fills move cash, rejections don't."""
        ledger = self.require_arm(arm_id)
        if not isinstance(decision, ExecutionDecision):
            raise ValueError(f"expected ExecutionDecision, got {decision!r}")
        if decision.status == "FILLED":
            ledger.apply_fill(decision.fill)
            return
        reason = decision.reason
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("NO_FILL decisions must carry a non-empty reason")
        ledger.record_rejection(
            OrderRejection(
                symbol=decision.symbol,
                side=decision.side,
                quantity=decision.quantity,
                reason=reason,
                timestamp_utc=decision.timestamp_utc,
                cost=float(decision.rejection_cost),
            )
        )

    def submit_intent(
        self,
        arm_id: str,
        intent: OrderIntent,
        *,
        model: Any,
        reference_price: float,
        timestamp_utc: str,
        session_open: bool,
        halted: bool,
        bid: float | None = None,
        ask: float | None = None,
        adv: float | None = None,
        locate: BorrowLocate | None = None,
    ) -> ExecutionDecision:
        """Locate-gate a SELL that would open/increase a short, then attempt the fill.

        The locate check happens BEFORE the fill attempt: an unavailable
        borrow rejects the order with zero cost and NO fill is ever booked.
        Sells that only reduce an existing long need no locate.
        """
        ledger = self.require_arm(arm_id)
        if not isinstance(intent, OrderIntent):
            raise ValueError(f"expected OrderIntent, got {intent!r}")
        long_qty = max(ledger.position_qty(intent.symbol), 0.0)
        opens_short = intent.side == "SELL" and float(intent.quantity) > long_qty
        if opens_short:
            if locate is None:
                decision = ExecutionDecision.no_fill(
                    symbol=intent.symbol, side=intent.side, quantity=intent.quantity,
                    timestamp_utc=timestamp_utc,
                    reason="MISSING_LOCATE",
                    detail="short sale without a locate record; fail closed",
                )
                self.book_decision(arm_id, decision)
                return decision
            if locate.symbol != intent.symbol or not locate.available:
                reason = "NO_LOCATE" if locate.symbol == intent.symbol else "LOCATE_SYMBOL_MISMATCH"
                decision = ExecutionDecision.no_fill(
                    symbol=intent.symbol, side=intent.side, quantity=intent.quantity,
                    timestamp_utc=timestamp_utc,
                    reason=reason,
                    detail="unavailable borrow rejects the short; never filled free",
                )
                self.book_decision(arm_id, decision)
                return decision
        decision = model.attempt_fill(
            symbol=intent.symbol,
            side=intent.side,
            quantity=float(intent.quantity),
            reference_price=reference_price,
            timestamp_utc=timestamp_utc,
            session_open=session_open,
            halted=halted,
            bid=bid,
            ask=ask,
            adv=adv,
        )
        self.book_decision(arm_id, decision)
        return decision

    def apply_dividend(self, arm_id: str, event: DividendEvent) -> None:
        """Long receipt / short liability booked by the arm's own ledger."""
        self.require_arm(arm_id).apply_dividend(event)

    def accrue_borrow_fee(
        self, arm_id: str, *, symbol: str, amount: float, timestamp_utc: str
    ) -> None:
        self.require_arm(arm_id).accrue_borrow_fee(
            symbol=symbol, amount=amount, timestamp_utc=timestamp_utc
        )

    def record_rejection(self, arm_id: str, rejection: OrderRejection) -> None:
        self.require_arm(arm_id).record_rejection(rejection)

    # -- terminal valuation ------------------------------------------------------ #
    def finalize_terminal(self, marks: Mapping[str, ObservableEvent]) -> None:
        """Terminal-valuate every arm on the SAME terminal observable events.

        Each open position's symbol must receive an EXECUTABLE event; the
        ledger books the implied ``terminal_pnl`` and refuses double marks.
        """
        if not isinstance(marks, Mapping):
            raise ValueError("marks must be a Mapping[symbol, ObservableEvent]")
        for ledger in self._books.values():
            needed = {
                symbol
                for symbol, qty in ledger.open_positions().items()
                if qty != 0.0 and symbol not in marks
            }
            if needed:
                raise ValueError(
                    f"terminal marks missing for open positions: {sorted(needed)}"
                )
        for symbol, event in marks.items():
            for ledger in self._books.values():
                ledger.mark_terminal(symbol, event)

    # -- identity accounting ------------------------------------------------------- #
    def arm_terms(self, arm_id: str) -> IdentityTerms:
        return self.require_arm(arm_id).identity_terms()

    def account_terms(self) -> IdentityTerms:
        """Field-wise sum of the arm terms under the shared starting equity."""
        if not self._books:
            raise ValueError("no arms registered; the account has no terms")
        terms_by_arm = {arm: book.identity_terms() for arm, book in self._books.items()}
        totals = {
            name: math.fsum([float(getattr(terms, name)) for terms in terms_by_arm.values()])
            for name in _TERM_FIELDS
        }
        # Every attribution book starts at 0, so arm ending_equity IS its delta;
        # shared ending equity = starting equity + sum of arm deltas.
        ending_delta = math.fsum(
            [float(terms.ending_equity) for terms in terms_by_arm.values()]
        )
        return IdentityTerms(
            starting_equity=self.starting_equity,
            ending_equity=math.fsum((self.starting_equity, ending_delta)),
            **totals,
        )

    def assert_closed(self, tolerance: float = FLOAT_IDENTITY_TOLERANCE_USD) -> None:
        """Per-arm identity AND the account identity must close."""
        for arm_id in self._books:
            self.arm_terms(arm_id).assert_closes(tolerance)
        self.account_terms().assert_closes(tolerance)

    # -- concentration --------------------------------------------------------------- #
    def arm_concentration(self, arm_id: str) -> dict[str, float]:
        """Per-symbol share of the arm's POSITIVE PnL (concentration breakdown)."""
        ledger = self.require_arm(arm_id)
        return positive_pnl_shares(ledger.symbol_contributions())

    # -- cash read -------------------------------------------------------------- #
    def shared_cash(self) -> float:
        """Shared USD cash: starting equity plus every arm's cash delta."""
        return math.fsum(
            [self.starting_equity] + [book.cash for book in self._books.values()]
        )
