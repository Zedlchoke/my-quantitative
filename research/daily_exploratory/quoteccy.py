"""Quote-currency book for the DAILY exploratory cycle (G9 prep build).

Implements the quote-CCY accounting law the successor engine must carry
(PLAN_DAILY_SUCCESSOR_DRAFT.md §6 item 4, closing the PC12A at-par defect
— DECISION_PACKET §13 ERRATUM):

- the BOOK is kept in the pair's QUOTE currency (USD for EURUSD-class
  pairs; JPY for USDJPY, CHF for USDCHF — the JPY/CHF->USD conversion is
  explicit, one conversion row per event);
- frozen conversion convention REALIZATION_SAME_BAR@1: ONE conversion per
  cash event (fill, swap accrual) at THAT bar's rate; equity marks
  convert at the same bar's conversion rate; USD-quoted books convert at
  identity 1.0 and are STILL logged (the conversion row exists for every
  event, no silent identity);
- the FILL_ACCOUNTING_SPEC §6 equity-decomposition invariant holds in
  QUOTE-CCY to 1e-9 (exact in Decimal here):
      sum(trade gross vs mid) - sum(spread_once) - sum(commission)
        - sum(swap) - sum(slip_beyond_halfspread) == equity_T - equity_0
  exposed ONLY as the reconciliation residual plus component sums —
  identity terms and cost bills are lawful prep-stage outputs
  (RGC-INC-1: identities, decision counts, cost bills; performance
  fields are absent by construction);
- a par-convention replay cross-check (the PC12A defect made mechanical):
  the same event stream reported at par (rate = 1) vs the frozen
  realization-rate convention, with the DISCLOSED algebraic divergence
  bound
      |sum_i c_i (r_i - 1) + u_T*m_T*(r_T - 1)|
        <= sum_i |c_i| |r_i - 1| + |u_T*m_T| |r_T - 1|
  (c_i = quote-ccy cash events incl. the opening conversion, r_i their
  frozen same-bar rates, r_T the final mark's rate). USD-quoted books
  have divergence exactly 0.

All arithmetic is Decimal (exact); public records expose float views.
Synthetic fixtures only at this stage — no real panel is consumed here,
nothing scores (OI-2 blocker stands; plan §0b G1).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional

from .costkernel import (  # noqa: F401  (re-exported for callers)
    BUY,
    SELL,
    DailyBar,
    DeclaredCostKernel,
    D,
    QUOTE_CCY_OF,
)

#: The frozen conversion convention id.
CONVERSION_CONVENTION = "REALIZATION_SAME_BAR@1"
RATE_SOURCE = "SAME_BAR_MID"

#: FILL_ACCOUNTING_SPEC §6 tolerance, quote-ccy units (Decimal-exact here,
#: so the observed residual is 0; the 1e-9 bound is the frozen gate).
IDENTITY_TOLERANCE = Decimal("1e-9")

EVENT_BOOK_OPEN = "BOOK_OPEN"
EVENT_FILL = "FILL"
EVENT_SWAP_ACCRUAL = "SWAP_ACCRUAL"
EVENT_EQUITY_MARK = "EQUITY_MARK"


@dataclass(frozen=True)
class ConversionRow:
    """One conversion row: exactly one per cash event / mark, at that
    bar's rate (realization-rate convention). Signed quote_amount for
    cash events; the marked level for BOOK_OPEN / EQUITY_MARK rows."""

    row_seq: int
    event_kind: str          # BOOK_OPEN | FILL | SWAP_ACCRUAL | EQUITY_MARK
    event_ts: str            # ISO UTC timestamp of the event
    quote_ccy: str
    quote_amount: Decimal    # signed cash delta (or level, for marks)
    rate_to_usd: Decimal     # quote-ccy -> USD multiplier (1.0 for USD books)
    usd_amount: Decimal
    rate_source: str         # SAME_BAR_MID
    rate_source_ts: str      # ts of the bar the rate came from
    convention: str          # REALIZATION_SAME_BAR@1

    def to_jsonable(self) -> Dict[str, object]:
        return {
            "row_seq": self.row_seq,
            "event_kind": self.event_kind,
            "event_ts": self.event_ts,
            "quote_ccy": self.quote_ccy,
            "quote_amount": float(self.quote_amount),
            "rate_to_usd": float(self.rate_to_usd),
            "usd_amount": float(self.usd_amount),
            "rate_source": self.rate_source,
            "rate_source_ts": self.rate_source_ts,
            "convention": self.convention,
        }


@dataclass(frozen=True)
class FillRecord:
    ts: str
    session_date: str
    side: str
    units_delta: Decimal     # signed d_i (BUY +, SELL -)
    fill_price: Decimal
    mid_at_fill: Decimal
    cash_delta_quote: Decimal    # signed, includes commission (slip inside price)
    commission: Decimal
    spread_once_total: Decimal
    slip_beyond_total: Decimal
    conversion: ConversionRow
    bar_side_difference_bps: Decimal  # diagnostic passthrough (never a cost)

    def to_jsonable(self) -> Dict[str, object]:
        return {
            "ts": self.ts,
            "session_date": self.session_date,
            "side": self.side,
            "units_delta": float(self.units_delta),
            "fill_price": float(self.fill_price),
            "mid_at_fill": float(self.mid_at_fill),
            "cash_delta_quoteccy": float(self.cash_delta_quote),
            "commission_quoteccy": float(self.commission),
            "spread_once_total_quoteccy": float(self.spread_once_total),
            "slip_beyond_total_quoteccy": float(self.slip_beyond_total),
            "fx_conversion": self.conversion.to_jsonable(),
            "bar_side_difference_bps": float(self.bar_side_difference_bps),
        }


@dataclass(frozen=True)
class SwapAccrualRecord:
    ts: str
    units_abs: Decimal
    multiplier: int
    wed_x3: bool
    charge_quote: Decimal
    conversion: ConversionRow

    def to_jsonable(self) -> Dict[str, object]:
        return {
            "accrual_ts": self.ts,
            "units_abs": float(self.units_abs),
            "multiplier": self.multiplier,
            "wed_x3": self.wed_x3,
            "quote_amount": float(self.charge_quote),
            "rate_to_usd": float(self.conversion.rate_to_usd),
            "usd_amount": float(self.conversion.usd_amount),
            "fx_conversion": self.conversion.to_jsonable(),
        }


@dataclass(frozen=True)
class MarkRecord:
    ts: str
    mid: Decimal
    cash_quote: Decimal
    units: Decimal
    equity_level_quote: Decimal
    conversion: ConversionRow

    def to_jsonable(self) -> Dict[str, object]:
        return {
            "ts": self.ts,
            "mid": float(self.mid),
            "cash_quoteccy": float(self.cash_quote),
            "units_base": float(self.units),
            "equity_level_quoteccy": float(self.equity_level_quote),
            "fx_conversion": self.conversion.to_jsonable(),
        }


@dataclass(frozen=True)
class IdentityReport:
    """FILL_ACCOUNTING_SPEC §6 reconciliation, quote-ccy, Decimal-exact.

    Fields are identity components, cost bills, bookkeeping levels and the
    residual gate only — no performance field exists here (RGC-INC-1).
    residual == (gross - spread_once - commission - swap - slip)
                - (equity_level_final - equity_level_open)
    """

    symbol: str
    quote_ccy: str
    window_open_ts: str
    window_final_ts: str
    equity_level_open_quote: Decimal
    equity_level_final_quote: Decimal
    identity_gross_vs_mid_sum: Decimal
    identity_cost_sum_spread_once: Decimal
    identity_cost_sum_slip_beyond: Decimal
    identity_cost_sum_commission: Decimal
    identity_cost_sum_swap: Decimal
    residual: Decimal
    tolerance: Decimal
    holds: bool
    n_fills: int
    n_swap_events: int

    def to_jsonable(self) -> Dict[str, object]:
        return {
            "symbol": self.symbol,
            "quote_ccy": self.quote_ccy,
            "window_open_ts": self.window_open_ts,
            "window_final_ts": self.window_final_ts,
            "equity_level_open_quoteccy": float(self.equity_level_open_quote),
            "equity_level_final_quoteccy": float(self.equity_level_final_quote),
            "identity_gross_vs_mid_sum": float(self.identity_gross_vs_mid_sum),
            "identity_cost_sum_spread_once": float(self.identity_cost_sum_spread_once),
            "identity_cost_sum_slip_beyond": float(self.identity_cost_sum_slip_beyond),
            "identity_cost_sum_commission": float(self.identity_cost_sum_commission),
            "identity_cost_sum_swap": float(self.identity_cost_sum_swap),
            "residual": float(self.residual),
            "tolerance": float(self.tolerance),
            "holds": self.holds,
            "n_fills": self.n_fills,
            "n_swap_events": self.n_swap_events,
        }


@dataclass(frozen=True)
class ParReplayReport:
    """Par-convention cross-check (PC12A at-par defect, closed).

    Compares the SAME quote-ccy book reported under the frozen
    realization-rate convention vs at par (rate = 1), with the disclosed
    algebraic divergence bound. Bookkeeping levels only (RGC-INC-1)."""

    symbol: str
    quote_ccy: str
    final_usd_level_realization_convention: Decimal
    final_usd_level_par_convention: Decimal
    divergence_abs: Decimal
    divergence_bound: Decimal
    within_bound: bool

    def to_jsonable(self) -> Dict[str, object]:
        return {
            "symbol": self.symbol,
            "quote_ccy": self.quote_ccy,
            "final_usd_level_realization_convention":
                float(self.final_usd_level_realization_convention),
            "final_usd_level_par_convention":
                float(self.final_usd_level_par_convention),
            "divergence_abs": float(self.divergence_abs),
            "divergence_bound": float(self.divergence_bound),
            "within_bound": self.within_bound,
        }


class QuoteCcyBook:
    """Per-symbol quote-ccy book: u (base units), cash (quote ccy),
    conversion rows, fills, swap accruals, marks.

    The book never computes or stores any performance metric; it is a
    ledger (G9 prep; real-panel runs wait for the registered cycle).
    """

    def __init__(self, symbol: str, kernel: DeclaredCostKernel,
                 opening_usd: str | float, open_ts: str,
                 open_rate_to_usd: str | float):
        self.symbol = symbol
        self.kernel = kernel
        if kernel.symbol != symbol:
            raise ValueError("kernel symbol mismatch")
        self.quote_ccy = QUOTE_CCY_OF[symbol]
        self._validate_rate(open_rate_to_usd)
        rate = D(open_rate_to_usd)
        opening = D(opening_usd)
        self.open_ts = open_ts
        self.cash_quote = opening / rate
        self.units = Decimal(0)
        self.equity_level_open = self.cash_quote  # u_0 = 0
        self.conversion_rows: List[ConversionRow] = []
        self.fills: List[FillRecord] = []
        self.swap_events: List[SwapAccrualRecord] = []
        self.marks: List[MarkRecord] = []
        self._conv(open_ts, EVENT_BOOK_OPEN, self.cash_quote, rate, open_ts)

    # -- internals -----------------------------------------------------------

    def _validate_rate(self, rate) -> None:
        r = D(rate)
        if r <= 0:
            raise ValueError("rate_to_usd must be > 0")
        if self.quote_ccy == "USD" and r != Decimal(1):
            # USD-quoted book: conversion identity 1.0, still logged —
            # never silently different (plan §6 item 4).
            raise ValueError("USD-quoted book requires rate_to_usd == 1.0")

    def _conv(self, event_ts: str, kind: str, amount: Decimal, rate: Decimal,
              rate_source_ts: str) -> ConversionRow:
        row = ConversionRow(
            row_seq=len(self.conversion_rows),
            event_kind=kind,
            event_ts=event_ts,
            quote_ccy=self.quote_ccy,
            quote_amount=amount,
            rate_to_usd=rate,
            usd_amount=amount * rate,
            rate_source=RATE_SOURCE,
            rate_source_ts=rate_source_ts,
            convention=CONVERSION_CONVENTION,
        )
        self.conversion_rows.append(row)
        return row

    # -- events --------------------------------------------------------------

    def apply_fill(self, ts: str, bar: DailyBar, side: str, units,
                   rate_to_usd, rate_source_ts: Optional[str] = None
                   ) -> FillRecord:
        """Fill at the bar's own quoted OPEN side (next-bar-open law),
        one conversion row at that bar's rate."""
        self._validate_rate(rate_to_usd)
        fq = self.kernel.price_fill(bar, side, units)
        d = fq.units if side == BUY else -fq.units
        if side == BUY:
            cash_delta = -(fq.units * fq.fill_price + fq.commission_total)
        else:
            cash_delta = fq.units * fq.fill_price - fq.commission_total
        self.cash_quote += cash_delta
        self.units += d
        conv = self._conv(ts, EVENT_FILL, cash_delta, D(rate_to_usd),
                          rate_source_ts or ts)
        rec = FillRecord(
            ts=ts,
            session_date=bar.session_date,
            side=side,
            units_delta=d,
            fill_price=fq.fill_price,
            mid_at_fill=fq.mid_at_fill,
            cash_delta_quote=cash_delta,
            commission=fq.commission_total,
            spread_once_total=fq.spread_once_total,
            slip_beyond_total=fq.slip_beyond_total,
            conversion=conv,
            bar_side_difference_bps=fq.bar_side_difference_bps,
        )
        self.fills.append(rec)
        return rec

    def accrue_swap(self, ts: str, multiplier: int, rate_to_usd,
                    rate_source_ts: Optional[str] = None,
                    units_abs: Optional[Decimal] = None
                    ) -> Optional[SwapAccrualRecord]:
        """One accrual event (caller iterates the frozen calendar).
        Membership law: charge iff the position is nonzero; flat books
        are a no-op returning None."""
        self._validate_rate(rate_to_usd)
        u = units_abs if units_abs is not None else abs(self.units)
        if self.units == 0 and units_abs is None:
            return None
        charge = self.kernel.swap_charge(u, multiplier)
        self.cash_quote -= charge
        conv = self._conv(ts, EVENT_SWAP_ACCRUAL, -charge, D(rate_to_usd),
                          rate_source_ts or ts)
        rec = SwapAccrualRecord(
            ts=ts,
            units_abs=u,
            multiplier=multiplier,
            wed_x3=(multiplier == 3),
            charge_quote=charge,
            conversion=conv,
        )
        self.swap_events.append(rec)
        return rec

    def mark(self, ts: str, mid, rate_to_usd, rate_source_ts: Optional[str] = None
             ) -> MarkRecord:
        """Equity mark: level = cash + u*mid, converted at the same bar's
        rate (marks never move cash)."""
        self._validate_rate(rate_to_usd)
        m = D(mid)
        level = self.cash_quote + self.units * m
        conv = self._conv(ts, EVENT_EQUITY_MARK, level, D(rate_to_usd),
                          rate_source_ts or ts)
        rec = MarkRecord(
            ts=ts,
            mid=m,
            cash_quote=self.cash_quote,
            units=self.units,
            equity_level_quote=level,
            conversion=conv,
        )
        self.marks.append(rec)
        return rec

    # -- reconciliation ------------------------------------------------------

    def check_identity(self, final_ts: str, final_mid
                       ) -> IdentityReport:
        """FILL_ACCOUNTING_SPEC §6, quote-ccy, Decimal-exact.

        gross-vs-mid telescopes per fill: sum_i d_i*(m_T - m_i) (closed
        trades and the open leg together — the open leg is the same
        expression with u_T carried to the final mark)."""
        m_T = D(final_mid)
        gross = sum((f.units_delta * (m_T - f.mid_at_fill) for f in self.fills),
                    Decimal(0))
        spread = sum((f.spread_once_total for f in self.fills), Decimal(0))
        slip = sum((f.slip_beyond_total for f in self.fills), Decimal(0))
        comm = sum((f.commission for f in self.fills), Decimal(0))
        swap = sum((e.charge_quote for e in self.swap_events), Decimal(0))
        level_final = self.cash_quote + self.units * m_T
        lhs = gross - spread - slip - comm - swap
        rhs = level_final - self.equity_level_open
        residual = lhs - rhs
        return IdentityReport(
            symbol=self.symbol,
            quote_ccy=self.quote_ccy,
            window_open_ts=self.open_ts,
            window_final_ts=final_ts,
            equity_level_open_quote=self.equity_level_open,
            equity_level_final_quote=level_final,
            identity_gross_vs_mid_sum=gross,
            identity_cost_sum_spread_once=spread,
            identity_cost_sum_slip_beyond=slip,
            identity_cost_sum_commission=comm,
            identity_cost_sum_swap=swap,
            residual=residual,
            tolerance=IDENTITY_TOLERANCE,
            holds=abs(residual) <= IDENTITY_TOLERANCE,
            n_fills=len(self.fills),
            n_swap_events=len(self.swap_events),
        )

    def par_replay(self, final_ts: str, final_mid, final_rate_to_usd
                   ) -> ParReplayReport:
        """Par-convention cross-check with the disclosed divergence bound.

        realization: opening converted at r_0 + every cash event converted
        at its own frozen same-bar rate + open position marked at r_T.
        par: the identical quote-ccy book reported at rate 1 (the PC12A
        convention)."""
        self._validate_rate(final_rate_to_usd)
        m_T = D(final_mid)
        r_T = D(final_rate_to_usd)

        cash_events = [c for c in self.conversion_rows
                       if c.event_kind in (EVENT_BOOK_OPEN, EVENT_FILL,
                                           EVENT_SWAP_ACCRUAL)]
        realized = sum((c.quote_amount * c.rate_to_usd for c in cash_events),
                       Decimal(0)) + self.units * m_T * r_T
        par = self.cash_quote + self.units * m_T
        bound = sum((abs(c.quote_amount) * abs(c.rate_to_usd - 1)
                     for c in cash_events), Decimal(0)) \
            + abs(self.units * m_T) * abs(r_T - 1)
        divergence = realized - par
        return ParReplayReport(
            symbol=self.symbol,
            quote_ccy=self.quote_ccy,
            final_usd_level_realization_convention=realized,
            final_usd_level_par_convention=par,
            divergence_abs=abs(divergence),
            divergence_bound=bound,
            within_bound=abs(divergence) <= bound,
        )

    # -- state views (bookkeeping only) --------------------------------------

    def state(self) -> Dict[str, object]:
        return {
            "symbol": self.symbol,
            "quote_ccy": self.quote_ccy,
            "units_base": float(self.units),
            "cash_quoteccy": float(self.cash_quote),
            "n_fills": len(self.fills),
            "n_swap_events": len(self.swap_events),
            "n_marks": len(self.marks),
            "n_conversion_rows": len(self.conversion_rows),
        }
