"""Isolated 100,000-USDT sleeve accounting (plan sections 5, 6, G3, G6).

Invariants enforced here:
- identity: ``equity == cash + sum(position qty x mark)`` asserted on
  every mutation (when all marks are available);
- fee and slippage are each charged EXACTLY ONCE per virtual fill;
- TWO independent cost books per plan section 6 — ``LINEAGE_COST`` and
  ``CURRENT_CONSERVATIVE_COST`` — evaluated per fill over the SAME
  quantities with different fee/slippage/funding parameters. The account
  cash/equity reality follows the PRIMARY book (default
  CURRENT_CONSERVATIVE_COST, the primary shadow reality check); other
  books are tracked as cumulative cost differences with
  ``equity_view(book)`` exposing their equity path;
- funding charged ONCE per settled event while held, window
  ``ts_opened <= fundingTime < ts_closed``; positive rate: long pays,
  short receives; negative inverted;
- a missing required mark => equity for that interval is
  UNAVAILABLE_FAIL_CLOSED (mark-gap state). No interpolation, ever;
- no margin, no leverage: a fill that would exceed available cash (or
  push gross notional above equity) raises and refuses;
- POLICY: REDUCING_SELL_NETS_POSITION (condition C1, audit finding F3):
  a sell that reduces or closes an existing LONG nets against that
  position — the only requirement is the position-size check (sell qty
  <= current long qty); the proceeds credit cash after fees/slippage.
  A reducing sell is NOT required to carry full sell-notional cash/gross
  headroom (the prior guard overcounted post-trade gross by the
  reduction and could refuse valid rebalance sells in fully-invested
  gross-1.0 books). Opening or increasing sells (new shorts), including
  sells that flip through zero (qty > current long qty), still pass the
  UNCHANGED no-margin/no-leverage cash and gross checks. Both cost
  books always keep identical quantities (positions/cash are mutated
  once and shared across books);
- SIZING_AND_CAP_BASIS: start_of_rebalance_equity (Q-14 fix): the
  rebalance sizes every leg at the equity snapshot taken at the START
  of the rebalance (executor._rebalance_steps), so the no-leverage
  gross cap for each fill of that rebalance measures gross-after
  against that SAME start-of-rebalance equity — supplied per fill via
  ``apply_fill(..., gross_cap_equity=...)`` — and NOT against the
  running equity already reduced by this rebalance's own booked
  fees/slippage. At a target gross of exactly 1.0 the post-cost book
  sits marginally above 1.0 when measured on post-cost equity (by
  exactly the booked cost) and every leg completes; a fill WITHOUT the
  supplied basis still measures on the current equity snapshot and
  refuses exactly as before, and a gross meaningfully above the basis
  still refuses pre-mutation. The CASH subchecks (a buy needs cash on
  hand; short proceeds must keep cash >= 0) remain on ACTUAL cash —
  real money, never a basis-adjusted value — so an opening short
  without cash backing still refuses;
- decision_count / order_intent_count / fill_count /
  closed_position_count are SEPARATE counters, never conflated.

Fill price convention (frozen, from cost_regime_manifest
slippage_model): the fill reference is a bar close; a buy fills at
``ref + slippage_ticks * tick`` and a sell at ``ref - ticks * tick``.
Fee is charged on reference notional ``|qty| * ref * fee_rate``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

LINEAGE_COST = "LINEAGE_COST"
CURRENT_CONSERVATIVE_COST = "CURRENT_CONSERVATIVE_COST"
DEFAULT_PRIMARY_BOOK = CURRENT_CONSERVATIVE_COST

_IDENTITY_ABS_TOL = 1e-6
_IDENTITY_REL_TOL = 1e-9
_EPS = 1e-9


class AccountingError(RuntimeError):
    """Sleeve accounting invariant violation or fail-closed refusal."""


class InsufficientCashError(AccountingError):
    """No margin/leverage: the fill would exceed the sleeve's own cash."""


class MarkGapError(AccountingError):
    """A required mark is missing; operation refused, state fail-closed."""


@dataclass
class BookCostParams:
    """Per-book frozen cost parameters (same quantities, different costs)."""

    fee_rate: float
    slippage_ticks: float
    funding_sign_convention: str = "LONG_PAYS_POSITIVE_RATE"


@dataclass
class CostBook:
    name: str
    params: BookCostParams
    fee: float = 0.0
    slippage: float = 0.0
    funding_cashflow: float = 0.0

    @property
    def cumulative_cost(self) -> float:
        # Costs enter equity negatively; this is the total drag booked
        # through this book (funding may be negative, i.e. a credit).
        return self.fee + self.slippage + self.funding_cashflow

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "fee": self.fee,
            "slippage": self.slippage,
            "funding_cashflow": self.funding_cashflow,
            "cumulative_cost": self.cumulative_cost,
        }


@dataclass
class Position:
    symbol: str
    qty: float  # signed: >0 long, <0 short
    avg_price: float  # signed-weighted average fill price (primary book)
    ts_opened: str
    ts_closed: Optional[str] = None
    realized_pnl: float = 0.0
    funding_paid: float = 0.0
    last_mark: Optional[float] = None


@dataclass
class MarkGapState:
    """Exposed mark-gap state; equity is UNAVAILABLE_FAIL_CLOSED here."""

    ts_utc: str
    missing_symbols: Tuple[str, ...]
    status: str = "UNAVAILABLE_FAIL_CLOSED"


@dataclass
class EquitySnapshot:
    status: str  # "OK" | "UNAVAILABLE_FAIL_CLOSED"
    equity: Optional[float]
    missing_symbols: Tuple[str, ...] = ()
    ts_utc: Optional[str] = None


@dataclass
class BookingResult:
    booked: bool
    reason: str
    cashflow: float = 0.0


@dataclass
class VirtualFillEvent:
    """Record of one virtual fill (primary-book economics)."""

    symbol: str
    side: str
    qty: float
    ref_price: float
    fill_price: float
    fee: float
    slippage_amount: float
    ts_utc: str
    fill_id: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "qty": self.qty,
            "ref_price": self.ref_price,
            "fill_price": self.fill_price,
            "fee": self.fee,
            "slippage_amount": self.slippage_amount,
            "ts_utc": self.ts_utc,
            "fill_id": self.fill_id,
        }


class SleeveAccount:
    """One isolated sleeve; no access to any other sleeve's cash/risk."""

    def __init__(
        self,
        sleeve_id: str,
        books: Dict[str, BookCostParams],
        starting_cash: float = 100_000.0,
        primary_book: str = DEFAULT_PRIMARY_BOOK,
    ):
        if not books:
            raise AccountingError("sleeve requires at least one cost book")
        if primary_book not in books:
            raise AccountingError(
                f"primary book {primary_book!r} not among provided books"
            )
        self.sleeve_id = sleeve_id
        self.primary_book = primary_book
        self.books: Dict[str, CostBook] = {
            name: CostBook(name=name, params=p) for name, p in books.items()
        }
        self.starting_cash = float(starting_cash)
        self.cash = float(starting_cash)
        self.positions: Dict[str, Position] = {}
        self.closed_positions: list = []
        # decision_count, order_intent_count, fill_count,
        # closed_position_count: separate counters, never conflated.
        self.decision_count = 0
        self.order_intent_count = 0
        self.fill_count = 0
        self.closed_position_count = 0
        self.realized_pnl = 0.0
        self._settled_funding_keys: set = set()
        self._mark_gap: Optional[MarkGapState] = None
        self.equity_history: list = []  # [(ts_utc, equity)] valid points only
        self._expected_equity: float = float(starting_cash)
        self._peak_equity: float = float(starting_cash)
        self._max_dd_abs: float = 0.0
        self._max_dd_pct: float = 0.0
        self._assert_identity()

    # ------------------------------------------------------------------
    # counters
    # ------------------------------------------------------------------
    def record_decision(self) -> None:
        self.decision_count += 1

    def record_order_intent(self) -> None:
        self.order_intent_count += 1

    # ------------------------------------------------------------------
    # marks / equity / drawdown
    # ------------------------------------------------------------------
    @property
    def mark_gap(self) -> Optional[MarkGapState]:
        return self._mark_gap

    def update_marks(self, marks: Dict[str, float], ts_utc: str) -> None:
        """Update marks for open positions; expose a gap when any is missing.

        Missing mark => UNAVAILABLE_FAIL_CLOSED gap state; NEVER an
        interpolated price.
        """
        missing = tuple(
            sorted(
                sym
                for sym, pos in self.positions.items()
                if pos.qty != 0.0 and sym not in marks
            )
        )
        for sym, price in marks.items():
            pos = self.positions.get(sym)
            if pos is not None and pos.qty != 0.0:
                if not isinstance(price, (int, float)) or math.isnan(price):
                    raise AccountingError(f"invalid mark for {sym}: {price!r}")
                pos.last_mark = float(price)
        if missing:
            self._mark_gap = MarkGapState(ts_utc=ts_utc, missing_symbols=missing)
        else:
            self._mark_gap = None
            if self.equity_snapshot().status == "OK":
                # Mark moves are exogenous equity changes: rebase the
                # expected identity value at the freshly measured marks.
                self._expected_equity = self.cash + sum(
                    p.qty * float(p.last_mark)
                    for p in self.positions.values()
                    if p.qty != 0.0
                )

    def equity_snapshot(self, ts_utc: Optional[str] = None) -> EquitySnapshot:
        """Valid only when every open position has a mark; else gap state."""
        missing = tuple(
            sorted(
                sym
                for pos in self.positions.values()
                if pos.qty != 0.0 and pos.last_mark is None
                for sym in (pos.symbol,)
            )
        )
        if self._mark_gap is not None or missing:
            missing = tuple(
                sorted(
                    set(missing)
                    | (set(self._mark_gap.missing_symbols) if self._mark_gap else set())
                )
            )
            return EquitySnapshot(
                status="UNAVAILABLE_FAIL_CLOSED",
                equity=None,
                missing_symbols=missing,
                ts_utc=ts_utc,
            )
        equity = self.cash + sum(
            pos.qty * float(pos.last_mark)
            for pos in self.positions.values()
            if pos.qty != 0.0
        )
        if not math.isfinite(equity):
            raise AccountingError("non-finite equity computed")
        snap = EquitySnapshot(status="OK", equity=equity, ts_utc=ts_utc)
        # Peak/max-drawdown update on EVERY valid mark measurement;
        # history only records stamped observations.
        if equity > self._peak_equity:
            self._peak_equity = equity
        dd_abs = self._peak_equity - equity
        dd_pct = dd_abs / self._peak_equity if self._peak_equity > 0 else 0.0
        if dd_abs > self._max_dd_abs:
            self._max_dd_abs = dd_abs
            self._max_dd_pct = dd_pct
        if ts_utc is not None:
            self.equity_history.append((ts_utc, equity))
        return snap

    @property
    def equity(self) -> Optional[float]:
        return self.equity_snapshot().equity

    def drawdown(self) -> Dict[str, Optional[float]]:
        """Current and max drawdown in USDT and percent.

        Current drawdown is only defined at valid marks; during a gap it
        is UNAVAILABLE (None) — no interpolation.
        """
        snap = self.equity_snapshot()
        if snap.status != "OK":
            current_abs = None
            current_pct = None
        else:
            current_abs = self._peak_equity - snap.equity
            current_pct = (
                current_abs / self._peak_equity if self._peak_equity > 0 else 0.0
            )
        return {
            "current_drawdown_abs": current_abs,
            "current_drawdown_pct": current_pct,
            "max_drawdown_abs": self._max_dd_abs,
            "max_drawdown_pct": self._max_dd_pct,
            "status": snap.status,
        }

    # ------------------------------------------------------------------
    # fills
    # ------------------------------------------------------------------
    def _fill_economics(self, side: str, qty: float, ref_price: float, tick: float):
        """Per-book fill price / fee / slippage for one virtual fill.

        Buy fills at ref + ticks*tick, sell at ref - ticks*tick (adverse).
        Fee charged EXACTLY ONCE per book on reference notional.
        """
        tick_sign = 1.0 if side == "buy" else -1.0
        econ = {}
        for name, book in self.books.items():
            fill_price = ref_price + tick_sign * book.params.slippage_ticks * tick
            fee = qty * ref_price * book.params.fee_rate
            slip = qty * book.params.slippage_ticks * tick
            econ[name] = (fill_price, fee, slip)
        return econ

    def apply_fill(
        self,
        symbol: str,
        side: str,
        qty: float,
        ref_price: float,
        tick_size: float,
        ts_utc: str,
        fill_id: Optional[str] = None,
        *,
        gross_cap_equity: Optional[float] = None,
    ) -> VirtualFillEvent:
        """Apply one virtual fill; fee and slippage charged exactly once.

        ``gross_cap_equity`` (SIZING_AND_CAP_BASIS:
        start_of_rebalance_equity): when the rebalancing executor
        supplies it, the no-leverage gross cap for an opening short
        measures gross-after against this START-OF-REBALANCE equity —
        the same basis the sizing used — instead of the running equity
        already reduced by this rebalance's own booked costs. Omitted
        (default), the current equity snapshot is used, exactly as
        before. The cash subchecks are unaffected (actual cash).
        """
        if side not in ("buy", "sell"):
            raise AccountingError(f"invalid side {side!r}")
        qty = float(qty)
        ref_price = float(ref_price)
        tick_size = float(tick_size)
        if qty <= 0 or ref_price <= 0 or tick_size <= 0:
            raise AccountingError("qty/ref_price/tick_size must be positive")
        if gross_cap_equity is not None:
            if (
                not isinstance(gross_cap_equity, (int, float))
                or isinstance(gross_cap_equity, bool)
                or not math.isfinite(gross_cap_equity)
                or gross_cap_equity <= 0
            ):
                raise AccountingError(
                    f"invalid gross_cap_equity basis {gross_cap_equity!r}; "
                    "must be a finite positive number (fail closed)"
                )
            cap_equity = float(gross_cap_equity)
        else:
            cap_equity = self.equity_snapshot().equity

        if self._mark_gap is not None:
            # Fail closed: no-leverage guard needs valid equity.
            raise MarkGapError(
                f"mark gap open for {self._mark_gap.missing_symbols}; "
                "fill refused (UNAVAILABLE_FAIL_CLOSED)"
            )

        econ = self._fill_economics(side, qty, ref_price, tick_size)
        primary_fill, primary_fee, _ = econ[self.primary_book]
        signed = qty if side == "buy" else -qty

        # ---- no margin / no leverage guards (refuse BEFORE mutating) ----
        if side == "buy":
            needed = qty * primary_fill + primary_fee
            if needed > self.cash + _EPS:
                raise InsufficientCashError(
                    f"buy needs {needed:.10f} USDT, sleeve {self.sleeve_id} "
                    f"has {self.cash:.10f}; no margin/leverage permitted"
                )
        else:
            pos_probe = self.positions.get(symbol)
            pre_sell_qty = pos_probe.qty if pos_probe is not None else 0.0
            if pre_sell_qty > 0.0 and qty <= pre_sell_qty + _EPS:
                # POLICY: REDUCING_SELL_NETS_POSITION — a sell that reduces
                # or closes an existing LONG nets against the position:
                # the position-size check above (qty <= current long qty)
                # is the only requirement; proceeds credit cash after
                # fees/slippage below. No full sell-notional cash/gross
                # headroom is required (the previous guard overcounted
                # post-trade gross by the reduction). Opening/increasing
                # sells — including flips through zero — fall through to
                # the unchanged checks below.
                pass
            else:
                cash_after = self.cash + qty * primary_fill - primary_fee
                if cash_after < -_EPS:
                    raise InsufficientCashError(
                        "short fee exceeds available cash; refusing"
                    )
                gross_notional_after = sum(
                    abs(p.qty) * float(p.last_mark)
                    for p in self.positions.values()
                    if p.qty != 0.0
                ) + qty * ref_price
                # SIZING_AND_CAP_BASIS: start_of_rebalance_equity when the
                # rebalancing executor supplies the sizing basis
                # (gross_cap_equity); the current equity snapshot otherwise
                # (unchanged fallback for direct callers).
                if cap_equity is not None and gross_notional_after > cap_equity + _EPS:
                    raise InsufficientCashError(
                        f"short would push gross notional {gross_notional_after:.10f} "
                        f"above equity {cap_equity:.10f}; no leverage permitted"
                    )

        # Capture pre-fill quantity and mark: the fill itself carries the
        # new mark (ref) for its symbol, and any gap between the previous
        # mark and ref is mark-to-market on the pre-fill quantity,
        # distinct from the booked costs.
        pos_before = self.positions.get(symbol)
        pre_qty = pos_before.qty if pos_before is not None else 0.0
        old_mark = pos_before.last_mark if pos_before is not None else None
        mark_pnl = 0.0
        if pre_qty != 0.0 and old_mark is not None:
            mark_pnl = (ref_price - float(old_mark)) * pre_qty

        # ---- mutate cash (primary book economics) ----
        self.cash -= signed * primary_fill + primary_fee

        # ---- position bookkeeping ----
        realized = self._apply_to_position(symbol, signed, primary_fill, ts_utc, ref_price)
        self.realized_pnl += realized
        self.fill_count += 1

        primary_slip = qty * self.books[self.primary_book].params.slippage_ticks * tick_size
        for name, book in self.books.items():
            fill_price_b, fee_b, slip_b = econ[name]
            book.fee += fee_b
            book.slippage += slip_b

        event = VirtualFillEvent(
            symbol=symbol,
            side=side,
            qty=qty,
            ref_price=ref_price,
            fill_price=primary_fill,
            fee=primary_fee,
            slippage_amount=primary_slip,
            ts_utc=ts_utc,
            fill_id=fill_id,
        )
        # Equity must equal the previous valid equity moved by the
        # mark-to-market this fill carries plus exactly the booked costs
        # (fee once, slippage once): the identity assert on this mutation.
        self._assert_identity(
            expected_equity=self._expected_equity + mark_pnl - (primary_fee + primary_slip)
        )
        return event

    def _apply_to_position(
        self, symbol: str, signed: float, fill_price: float, ts_utc: str, ref_price: float
    ) -> float:
        """Weighted-average position update; closing realizes PnL."""
        pos = self.positions.get(symbol)
        realized = 0.0
        if pos is None or pos.qty == 0.0:
            self.positions[symbol] = Position(
                symbol=symbol,
                qty=signed,
                avg_price=fill_price,
                ts_opened=ts_utc,
                last_mark=ref_price,
            )
            return realized
        if pos.qty * signed > 0:
            # extending
            new_qty = pos.qty + signed
            pos.avg_price = (pos.qty * pos.avg_price + signed * fill_price) / new_qty
            pos.qty = new_qty
            pos.last_mark = ref_price
            return realized
        # reducing / closing / flipping
        closing_qty = min(abs(pos.qty), abs(signed))
        direction = 1.0 if pos.qty > 0 else -1.0
        realized = closing_qty * (fill_price - pos.avg_price) * direction
        pos.realized_pnl += realized
        remaining = pos.qty + signed
        if remaining == 0.0:
            pos.qty = 0.0
            pos.ts_closed = ts_utc
            self.closed_positions.append(pos)
            self.closed_position_count += 1
        elif remaining * pos.qty > 0:
            pos.qty = remaining
        else:
            # flipped through zero: remainder is a new position
            pos.qty = remaining
            pos.avg_price = fill_price
            pos.ts_opened = ts_utc
            pos.ts_closed = None
            pos.realized_pnl = 0.0
            pos.funding_paid = 0.0
        pos.last_mark = ref_price
        return realized

    # ------------------------------------------------------------------
    # funding
    # ------------------------------------------------------------------
    def apply_funding(
        self,
        symbol: str,
        funding_time_utc: str,
        rate: float,
        mark_price: float,
    ) -> BookingResult:
        """Book a settled funding event ONCE while held.

        Window rule: ``ts_opened <= fundingTime < ts_closed``. Positive
        rate: long pays, short receives; negative inverted.
        """
        pos = self.positions.get(symbol)
        if pos is None or pos.qty == 0.0:
            return BookingResult(booked=False, reason="no_open_position")
        opened = pos.ts_opened
        closed = pos.ts_closed
        if not (opened <= funding_time_utc and (closed is None or funding_time_utc < closed)):
            return BookingResult(
                booked=False,
                reason="outside_holding_window",
            )
        key = (symbol, funding_time_utc)
        if key in self._settled_funding_keys:
            return BookingResult(booked=False, reason="already_booked")
        if mark_price is None:
            raise MarkGapError("funding notional needs a mark; none supplied")
        notional = abs(pos.qty) * float(mark_price)
        sign = 1.0 if pos.qty > 0 else -1.0

        def cashflow_for(book: CostBook) -> float:
            conv = book.params.funding_sign_convention
            if conv == "LONG_PAYS_POSITIVE_RATE":
                return -float(rate) * notional * sign
            if conv == "SHORT_PAYS_POSITIVE_RATE":
                return float(rate) * notional * sign
            raise AccountingError(f"unknown funding convention {conv!r}")

        primary_cf = cashflow_for(self.books[self.primary_book])
        self.cash += primary_cf
        pos.funding_paid += primary_cf
        for name, book in self.books.items():
            book.funding_cashflow += cashflow_for(book)
        self._settled_funding_keys.add(key)
        self._assert_identity(expected_equity=self._expected_equity + primary_cf)
        return BookingResult(booked=True, reason="settled_while_held", cashflow=primary_cf)

    # ------------------------------------------------------------------
    # exposure
    # ------------------------------------------------------------------
    def exposure_snapshot(
        self, symbol_betas: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Gross / net / btc_beta at valid marks (equity fractions).

        ``btc_beta`` is computed against the supplied per-symbol BTC betas
        (from the supplied BTC mark series upstream); a flat book is 0.0.
        """
        snap = self.equity_snapshot()
        if snap.status != "OK":
            return {
                "gross": None,
                "net": None,
                "btc_beta": None,
                "status": "UNAVAILABLE_FAIL_CLOSED",
                "missing_symbols": snap.missing_symbols,
            }
        equity = snap.equity
        weights = {
            sym: (pos.qty * float(pos.last_mark)) / equity
            for sym, pos in self.positions.items()
            if pos.qty != 0.0
        }
        gross = sum(abs(w) for w in weights.values())
        net = sum(weights.values())
        if not weights:
            btc_beta = 0.0
        elif symbol_betas is None:
            btc_beta = None  # betas not supplied: measured gross/net only
        else:
            btc_beta = sum(w * float(symbol_betas.get(sym, 0.0)) for sym, w in weights.items())
        return {
            "gross": gross,
            "net": net,
            "btc_beta": btc_beta,
            "weights": weights,
            "status": "OK",
            "missing_symbols": (),
        }

    # ------------------------------------------------------------------
    # per-book equity view
    # ------------------------------------------------------------------
    def equity_view(self, book_name: str) -> Optional[float]:
        """Equity path for a non-primary book: same quantities, that
        book's costs. ``equity - (primary costs - this book costs)``."""
        if book_name not in self.books:
            raise AccountingError(f"unknown cost book {book_name!r}")
        snap = self.equity_snapshot()
        if snap.status != "OK":
            return None
        primary_cost = self.books[self.primary_book].cumulative_cost
        book_cost = self.books[book_name].cumulative_cost
        return snap.equity + (primary_cost - book_cost)

    # ------------------------------------------------------------------
    # identity assertion
    # ------------------------------------------------------------------
    def _assert_identity(self, expected_equity: Optional[float] = None) -> None:
        """``equity == cash + sum(qty x mark)`` at every mutation.

        When ``expected_equity`` is supplied (fill / funding mutations)
        the freshly computed cash+marks equity must equal the previous
        valid equity moved by exactly the booked costs; any divergence
        raises ``IDENTITY_MISMATCH``. When marks are missing the check
        is deferred and the mark-gap state is exposed instead.
        """
        missing = [
            p.symbol
            for p in self.positions.values()
            if p.qty != 0.0 and p.last_mark is None
        ]
        if missing:
            # Cannot assert without marks; gap state must be exposed.
            if self._mark_gap is None:
                self._mark_gap = MarkGapState(
                    ts_utc=None, missing_symbols=tuple(sorted(missing))
                )
            return
        actual = self.cash + sum(
            p.qty * float(p.last_mark) for p in self.positions.values() if p.qty != 0.0
        )
        if not math.isfinite(actual):
            raise AccountingError("non-finite equity")
        if expected_equity is None:
            expected_equity = self._expected_equity
        if not math.isclose(
            actual,
            expected_equity,
            rel_tol=_IDENTITY_REL_TOL,
            abs_tol=_IDENTITY_ABS_TOL,
        ):
            raise AccountingError(
                f"equity identity mismatch: cash+marks={actual!r} "
                f"expected={expected_equity!r} "
                f"(IDENTITY_MISMATCH, sleeve {self.sleeve_id})"
            )
        self._expected_equity = actual

    def snapshot(self) -> Dict[str, Any]:
        """Read-only plain-dict snapshot for the ledger/dashboard lanes."""
        snap = self.equity_snapshot()
        return {
            "sleeve_id": self.sleeve_id,
            "cash": self.cash,
            "equity": snap.equity,
            "equity_status": snap.status,
            "missing_symbols": list(snap.missing_symbols),
            "realized_pnl": self.realized_pnl,
            "fee": self.books[self.primary_book].fee,
            "slippage": self.books[self.primary_book].slippage,
            "funding_cashflow": self.books[self.primary_book].funding_cashflow,
            "unrealized_pnl": self.unrealized_pnl(),
            "decision_count": self.decision_count,
            "order_intent_count": self.order_intent_count,
            "fill_count": self.fill_count,
            "closed_position_count": self.closed_position_count,
            "drawdown": self.drawdown(),
            "exposure": self.exposure_snapshot(),
            "mark_gap": self._mark_gap.missing_symbols if self._mark_gap else None,
            "books": {name: b.as_dict() for name, b in self.books.items()},
        }

    def unrealized_pnl(self) -> Optional[float]:
        snap = self.equity_snapshot()
        if snap.status != "OK":
            return None
        pos_value = sum(
            p.qty * float(p.last_mark) for p in self.positions.values() if p.qty != 0.0
        )
        cost_basis = sum(
            p.qty * p.avg_price for p in self.positions.values() if p.qty != 0.0
        )
        return pos_value - cost_basis
