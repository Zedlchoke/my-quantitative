"""RATES-NG1 P1 dual-book accounting kernel (inherited, not forked).

P1 work item 1 (dispatch packet RATES-NG1 / rates-ng1-p1-kernel-costs).
Inheritance contract, per the A2 accounting/kernel lane law:

- The shared kernel is ``research/accounting.py`` at the repo root: the
  canonical PnL field adapter (``map_to_canonical`` -- fail-closed,
  never silently 0), the terminal policy constant
  (``FORCE_LIQUIDATE_AT_LAST_OBSERVABLE_BAR``) and the accounting
  identity (``build_accounting_reconciliation``).  This module IMPORTS
  those primitives and uses them verbatim; it does NOT re-implement
  them.  No fork exists: the only copies of the identity math live in
  the shared module.

- Dual books (RULES.md forex standing constraint: "dual books
  (price-only must not invert sign)"; governance conditional diagnostic
  ``financing_dual_books``): every ledger carries a ``price_only`` book
  and a ``cost_adjusted`` book over IDENTICAL fill rows and mark rows.
  Only cost rows differ between the books.  The sign relationship
  between the books is RECORDED per ledger (``sign_record``); the
  sign-non-inversion gate itself is consumed at scoring time, never
  redefined here.

- Cost-once-per-fill law (plan RATES-NG1 section 5): an execution
  spread cost is charged exactly once, at the fill it belongs to.
  Re-applying a fill id raises :class:`CostOnceViolation` (A2 lane
  cost-once fixture surface).

- Cost-field mapping (explicit, disclosed): the per-fill effective
  half-spread maps to the identity field ``slippage``; recurring
  expense-ratio drag maps to the identity field ``commissions``; both
  are ALSO carried as typed cost events (``kind`` label) so any future
  re-mapping can be rebuilt from the serialized ledger without
  re-running.  ``funding_cashflows`` and ``rejection_costs`` stay 0.0
  in this asset family (ETP cash equity carries no funding schedule and
  rejected orders are out of P1 scope).

- Degenerate-case contract (packet work item 1): one fill, one cost
  event, one mark must reconcile by hand in BOTH books with dual-book
  ledger equality.  ``tests/test_rates_ng1_p1.py`` pins the exact
  hand-computed numbers.

No signals, no proposals, no scoring and no outcome numbers live here
(plan section 5: P1 is kernel/cost/clock identity only).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from research.accounting import (  # noqa: F401  (inherited, re-exported)
    TERMINAL_POLICY,
    AccountingFieldError,  # noqa: F401  (compatibility surface)
    build_accounting_reconciliation,
    map_to_canonical,
)

SCHEMA = "rates_ng1/kernel@1"

BOOKS = ("price_only", "cost_adjusted")

#: Cost ladder tier carried by this cycle's kernel (plan section 5).
COST_LADDER_TIER = 2.0

#: Cost frequency law (plan section 5: "cost charged once per fill").
COST_FREQUENCY = "once_per_fill"


class KernelError(Exception):
    """Fail-closed kernel construction error."""


class CostOnceViolation(KernelError):
    """A fill id was applied twice: the cost-once law forbids replay."""


class UnknownBook(KernelError):
    """A book name outside ``BOOKS`` was requested."""


class DualBookLedger:
    """Dual-book (price-only / cost-adjusted) cash-equity ledger.

    Fills and marks are SHARED rows: both books observe identical
    executions and identical marks.  Cost rows are charged only to the
    cost-adjusted book.  Position accounting is average-cost; open
    positions are force-valued at the last observable mark per the
    inherited terminal policy.
    """

    def __init__(self, name: str, starting_equity: float):
        if not name:
            raise KernelError("ledger name must be non-empty")
        self.name = str(name)
        self.starting_equity = float(starting_equity)
        self.fills: list[dict[str, Any]] = []
        self.marks: list[dict[str, Any]] = []
        self.cost_events: list[dict[str, Any]] = []
        self._applied_fill_ids: set[str] = set()
        self._position: dict[str, dict[str, float]] = {}
        self._last_mark: dict[str, float] = {}

    # -- row application --------------------------------------------------- #

    def apply_fill(self, *, fill_id: str, ts: str, ticker: str, side: str,
                   qty: float, price: float,
                   spread_cost: float | None = None) -> dict[str, Any]:
        """Apply one execution to BOTH books (shared row).

        ``spread_cost`` (a currency amount, typically
        ``half_spread_fraction * price * qty``) is charged ONCE, to the
        cost-adjusted book only.  A second application of the same
        ``fill_id`` raises :class:`CostOnceViolation`.
        """
        if fill_id in self._applied_fill_ids:
            raise CostOnceViolation(
                f"fill_id {fill_id!r} already applied to ledger "
                f"{self.name!r}: cost-once-per-fill replay refused")
        if side not in ("BUY", "SELL"):
            raise KernelError(f"side must be BUY or SELL, got {side!r}")
        qty = float(qty)
        price = float(price)
        if qty <= 0 or price <= 0:
            raise KernelError("qty and price must be positive")
        signed = qty if side == "BUY" else -qty
        row = {
            "row_type": "fill",
            "fill_id": str(fill_id),
            "ts": str(ts),
            "ticker": str(ticker),
            "side": side,
            "qty": qty,
            "price": price,
            "spread_cost": None if spread_cost is None else float(spread_cost),
            "canonical_pnl": 0.0,
        }
        self.fills.append(row)
        self._applied_fill_ids.add(str(fill_id))
        pos = self._position.setdefault(
            str(ticker), {"qty": 0.0, "avg_price": 0.0})
        new_qty = pos["qty"] + signed
        if new_qty < -1e-12:
            raise KernelError(
                f"fill {fill_id!r} shorts {ticker} below zero: flat-only "
                "P1 kernel refuses")
        if signed > 0:
            pos["avg_price"] = (
                (pos["avg_price"] * pos["qty"] + price * qty) / new_qty
                if new_qty > 0 else 0.0)
        pos["qty"] = new_qty
        return dict(row)

    def apply_mark(self, *, ts: str, ticker: str, price: float) -> dict:
        """Apply one mark (shared row) for ``ticker``."""
        price = float(price)
        if price <= 0:
            raise KernelError("mark price must be positive")
        row = {"row_type": "mark", "ts": str(ts), "ticker": str(ticker),
               "price": price, "canonical_pnl": 0.0}
        self.marks.append(row)
        self._last_mark[str(ticker)] = price
        return dict(row)

    def apply_expense_drag(self, *, ts: str, days: float, notional: float,
                           per_day_fraction: float) -> dict:
        """Charge one typed expense-drag cost event (cost book only)."""
        days = float(days)
        notional = float(notional)
        per_day = float(per_day_fraction)
        if days < 0 or notional < 0 or per_day < 0:
            raise KernelError("drag inputs must be non-negative")
        amount = notional * per_day * days
        row = {
            "row_type": "cost_event",
            "kind": "expense_drag",
            "ts": str(ts),
            "days": days,
            "notional": notional,
            "per_day_fraction": per_day,
            "amount": amount,
            "canonical_pnl": -amount,
        }
        self.cost_events.append(row)
        return dict(row)

    # -- book views --------------------------------------------------------- #

    def _book_cost_events(self, book: str) -> list[dict[str, Any]]:
        self._require_book(book)
        return self.cost_events if book == "cost_adjusted" else []

    def _require_book(self, book: str) -> None:
        if book not in BOOKS:
            raise UnknownBook(
                f"book {book!r} outside {BOOKS}: refused")

    def price_pnl(self) -> float:
        """Terminal-policy price PnL: open positions force-valued at the
        last observable mark (inherited TERMINAL_POLICY)."""
        total = 0.0
        for ticker, pos in self._position.items():
            if pos["qty"] <= 0:
                continue
            mark = self._last_mark.get(ticker)
            if mark is None:
                raise KernelError(
                    f"open position in {ticker} has no observable mark: "
                    "force-liquidation value unavailable (fail-closed)")
            total += (mark - pos["avg_price"]) * pos["qty"]
        return total

    def total_costs(self, book: str) -> dict[str, float]:
        """Identity-field cost totals for ``book`` (zero for the price
        book)."""
        ev = self._book_cost_events(book)
        drag = sum(e["amount"] for e in ev if e["kind"] == "expense_drag")
        spread = sum(
            f["spread_cost"] for f in self.fills
            if f["spread_cost"] is not None) if book == "cost_adjusted" \
            else 0.0
        return {"commissions": drag, "slippage": spread}

    def equity(self, book: str) -> float:
        self._require_book(book)
        costs = self.total_costs(book)
        return (self.starting_equity + self.price_pnl()
                - costs["commissions"] - costs["slippage"])

    def book_view(self, book: str) -> dict[str, Any]:
        """JSON-safe serialized view of ONE book (fills and marks
        identical across books by construction; cost rows differ)."""
        self._require_book(book)
        costs = self.total_costs(book)
        return {
            "book": book,
            "fills": [dict(f) for f in self.fills],
            "marks": [dict(m) for m in self.marks],
            "cost_events": [dict(e) for e in self._book_cost_events(book)],
            "starting_equity": self.starting_equity,
            "price_pnl": self.price_pnl(),
            "total_costs": costs,
            "ending_equity": self.equity(book),
        }

    def reconcile(self, book: str, scope: str | None = None) -> dict:
        """Inherited accounting identity for one book, via the SHARED
        kernel ``build_accounting_reconciliation`` (no local copy)."""
        self._require_book(book)
        costs = self.total_costs(book)
        return build_accounting_reconciliation(
            starting_equity=self.starting_equity,
            ending_equity=self.equity(book),
            closed_price_pnl=0.0,
            terminal_pnl=self.price_pnl(),
            funding_cashflows=0.0,
            commissions=costs["commissions"],
            slippage=costs["slippage"],
            rejection_costs=0.0,
            scope=scope or f"{self.name}:{book}",
            terminal_policy=TERMINAL_POLICY,
        )

    def dual_book_equality(self, tol: float = 1e-9) -> dict:
        """Ledger-equality proof between the books: shared rows are
        identical, cost deltas reconcile exactly, and the price-only
        sign relationship is recorded (RULES law: price-only must not
        invert sign)."""
        delta_price = self.equity("price_only") - self.starting_equity
        delta_cost = self.equity("cost_adjusted") - self.starting_equity
        total_cost = sum(self.total_costs("cost_adjusted").values())
        residual = (delta_price - total_cost) - delta_cost
        scale = max(1.0, abs(delta_price), abs(delta_cost))
        return {
            "shared_fills_identical": True,
            "shared_marks_identical": True,
            "fills_cost_book": len(self.book_view("cost_adjusted")["fills"]),
            "fills_price_book": len(self.book_view("price_only")["fills"]),
            "marks_cost_book": len(self.book_view("cost_adjusted")["marks"]),
            "marks_price_book": len(self.book_view("price_only")["marks"]),
            "price_only_delta": delta_price,
            "cost_adjusted_delta": delta_cost,
            "total_costs": total_cost,
            "equality_residual": residual,
            "equality_tolerance": tol * scale,
            "equality_ok": bool(abs(residual) <= tol * scale),
            "sign_record": {
                "price_only": "positive" if delta_price > 0 else
                              ("negative" if delta_price < 0 else "zero"),
                "cost_adjusted": "positive" if delta_cost > 0 else
                                 ("negative" if delta_cost < 0 else "zero"),
                "sign_inverted": bool(delta_price * delta_cost < 0),
            },
        }

    def serialize(self) -> dict[str, Any]:
        """Full JSON-safe ledger: both book views, both reconciliations,
        the dual-book equality proof and the inherited law constants."""
        return {
            "schema": SCHEMA,
            "name": self.name,
            "cost_ladder_tier": COST_LADDER_TIER,
            "cost_frequency": COST_FREQUENCY,
            "terminal_policy": TERMINAL_POLICY,
            "books": [self.book_view(b) for b in BOOKS],
            "reconciliation": {b: self.reconcile(b) for b in BOOKS},
            "dual_book_equality": self.dual_book_equality(),
        }

    def sha256(self) -> str:
        payload = json.dumps(self.serialize(), sort_keys=True,
                             separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
