"""Accounting kernel: prices, ticks, PnL, cash, margin.

Invariants enforced here:
  * PnL is ARITHMETIC (price difference x multiplier x signed qty). CL
    settled negative in April 2020; any log-return or multiplicative-return
    computation on non-positive prices is forbidden (log_return raises).
  * 6J orientation: quotes are already USD per JPY. PnL = dprice x 12.5M x
    qty. There is NO USDJPY inversion anywhere; attempting to feed an
    inverted (≈157) price into 6J accounting trips the plausibility guard.
  * All cash is USD. Multipliers/minTicks come from the instrument table,
    never assumed.
  * Margin is an INTERFACE over published broker tables (NinjaTrader/AMP);
    official CME SPAN is NOT_RUN (transport-blocked 2026-10-02).
"""
from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal

from .instruments import InstrumentSpec, MARGINS, get_instrument
from .taxonomy import PolicyError

# 6J plausibility band (USD per JPY). Inverted quotes are ~150-160.
SIXJ_PRICE_BAND = (0.001, 0.05)


class NegativePriceLogForbidden(PolicyError):
    pass


def log_return(p0: float, p1: float) -> float:
    """Forbidden on non-positive prices — kept as an explicit tripwire so no
    code path quietly computes log returns on negative CL prices."""
    if p0 <= 0 or p1 <= 0:
        raise NegativePriceLogForbidden(
            f"log return undefined for p0={p0}, p1={p1} "
            "(CL settled negative in Apr-2020); use arithmetic pnl()")
    return math.log(p1 / p0)


def round_to_tick(price: float, min_tick: float, mode: str = "nearest") -> float:
    """Exact tick rounding via Decimal (no float drift)."""
    if min_tick <= 0:
        raise ValueError("min_tick must be positive")
    q = Decimal(str(price)) / Decimal(str(min_tick))
    quant = {"nearest": ROUND_HALF_UP, "floor": ROUND_FLOOR,
             "ceil": ROUND_CEILING}[mode]
    n = q.to_integral_value(rounding=quant)
    return float(Decimal(str(min_tick)) * n)


def check_price_plausible(symbol: str, price: float) -> float:
    """Orientation guard. 6J must arrive as USD-per-JPY (~0.006), never as an
    inverted USDJPY (~150). Negative prices are LEGAL for CL (and tolerated
    elsewhere with a note — exchange rules govern, not us)."""
    if symbol == "6J":
        lo, hi = SIXJ_PRICE_BAND
        if not (lo <= price <= hi):
            raise PolicyError(
                f"6J price {price} outside USD-per-JPY band {SIXJ_PRICE_BAND}: "
                "looks like an inverted USDJPY quote; 6J accounting must NOT "
                "invert — quotes are already USD per JPY")
    return price


@dataclass(frozen=True)
class Fill:
    session: dt.date
    symbol: str
    local_symbol: str
    conid: int
    signed_qty: int          # + buy, - sell
    price: float             # raw tradeable price (tick-rounded)
    is_close_only_bar: bool  # fill on a settlement-derived bar -> forbidden
    cost_usd: float = 0.0
    cost_breakdown: dict = field(default_factory=dict)
    note: str = ""

    def __post_init__(self) -> None:
        if self.is_close_only_bar:
            raise PolicyError(
                f"fill on {self.local_symbol} {self.session}: bar is "
                "close-only settlement-derived (v=0) — legal as signal/"
                "reference price, NOT as fill price (data-lane wall #3)")


def pnl(entry_price: float, exit_price: float, signed_qty: int,
        multiplier: float) -> float:
    """Arithmetic PnL in USD. Safe for negative prices. No log anywhere."""
    return (exit_price - entry_price) * float(multiplier) * int(signed_qty)


def pnl_for_symbol(symbol: str, entry_price: float, exit_price: float,
                   signed_qty: int) -> float:
    spec = get_instrument(symbol)
    return pnl(entry_price, exit_price, signed_qty, spec.multiplier)


def usd_notional(symbol: str, price: float, signed_qty: int) -> float:
    """Approximate USD notional (for risk caps; futures margin not notional)."""
    spec = get_instrument(symbol)
    check_price_plausible(symbol, price)
    return price * spec.multiplier * signed_qty


def tick_value(symbol: str) -> float:
    return get_instrument(symbol).tick_value_usd


# --------------------------------------------------------------------- #
# Drawdown arithmetic (portfolio equity series; MULTIASSET-WIRING 2026-10-02)
def drawdown_series(equity: list[float]) -> list[float]:
    """Per-point drawdown vs the running peak: equity[i] - max(equity[:i+1]).
    Always <= 0; arithmetic on the equity LEVELS (never log returns —
    negative-CL equity paths are legal)."""
    out: list[float] = []
    peak: float | None = None
    for x in equity:
        peak = x if peak is None else max(peak, x)
        out.append(x - peak)
    return out


def max_drawdown(equity: list[float]) -> dict:
    """Peak-to-trough maximum drawdown + where it happened (levels and
    indices). Empty input -> zero drawdown."""
    dds = drawdown_series(equity)
    if not dds:
        return {"max_drawdown_usd": 0.0, "trough_index": None,
                "peak_index": None, "note": "empty equity series"}
    trough_i = min(range(len(dds)), key=lambda i: dds[i])
    peak_i = max(range(trough_i + 1), key=lambda i: equity[i])
    return {
        "max_drawdown_usd": dds[trough_i],
        "trough_index": trough_i,
        "peak_index": peak_i,
        "peak_equity_usd": equity[peak_i],
        "trough_equity_usd": equity[trough_i],
        "note": "arithmetic levels only; never log returns",
    }


# --------------------------------------------------------------------- #
class CashLedger:
    """USD cash accounting with an append-only event log for reconciliation."""

    def __init__(self, initial_cash_usd: float):
        if not math.isfinite(initial_cash_usd):
            raise ValueError("initial cash must be finite")
        self.initial_cash_usd = float(initial_cash_usd)
        self.cash = float(initial_cash_usd)
        self.events: list[tuple[str, dt.date, float, str]] = []

    def apply(self, kind: str, session: dt.date, amount_usd: float,
              note: str = "") -> float:
        self.cash += float(amount_usd)
        self.events.append((kind, session, float(amount_usd), note))
        return self.cash

    def reconcile(self) -> dict:
        recon = self.initial_cash_usd + sum(e[2] for e in self.events)
        if abs(recon - self.cash) > 1e-9:
            raise AssertionError(
                f"cash reconciliation failed: {recon} != {self.cash}")
        return {
            "initial": self.initial_cash_usd,
            "final": self.cash,
            "n_events": len(self.events),
            "reconciled": True,
        }

    def sums_by_kind(self) -> dict[str, float]:
        """Signed USD totals per event kind. EXEC-FIX R2: lets the engine
        cross-check its event stream (realize / entry_cost / exit_cost /
        roll_cost) against an INDEPENDENT recomputation from the journal
        — a ledger must never reconcile only against its own events."""
        out: dict[str, float] = {}
        for kind, _session, amount, _note in self.events:
            out[kind] = out.get(kind, 0.0) + amount
        return out


@dataclass
class Position:
    symbol: str
    local_symbol: str
    conid: int
    signed_qty: int
    avg_entry_price: float
    opened_session: dt.date
    rolls: list[dict] = field(default_factory=list)  # roll events while held

    def with_roll(self, new_local: str, new_conid: int, new_price: float,
                  session: dt.date, raw_gap: float | None) -> "Position":
        if self.signed_qty == 0:
            raise PolicyError("cannot roll a flat position")
        self.rolls.append({
            "session": session.isoformat(),
            "from": self.local_symbol, "to": new_local,
            "from_conid": self.conid, "to_conid": new_conid,
            "new_price": new_price, "raw_gap": raw_gap,
        })
        self.local_symbol = new_local
        self.conid = new_conid
        self.avg_entry_price = new_price
        return self


# --------------------------------------------------------------------- #
@dataclass(frozen=True)
class MarginRequirement:
    initial_usd: float
    maintenance_usd: float
    source: str
    as_of: str
    official_cme_span: str = "NOT_RUN"


class MarginModel:
    """Margin interface (margin risk law): requirement per contract from
    PUBLISHED broker tables; NOT exchange-official SPAN."""

    def __init__(self, buffer_fraction: float = 0.0):
        if buffer_fraction < 0:
            raise ValueError("buffer_fraction >= 0")
        self.buffer_fraction = buffer_fraction

    def requirement(self, symbol: str, abs_qty: int) -> MarginRequirement:
        mq = MARGINS[symbol]
        buf = 1.0 + self.buffer_fraction
        return MarginRequirement(
            initial_usd=mq.initial_usd * buf * abs(abs_qty),
            maintenance_usd=mq.maintenance_usd * buf * abs(abs_qty),
            source=mq.source, as_of=mq.as_of,
        )

    def check(self, positions: dict[str, int], equity_usd: float,
              level: str = "initial") -> dict:
        """Return margin status for a {symbol: signed_qty} book."""
        if level not in ("initial", "maintenance"):
            raise ValueError("level must be initial|maintenance")
        total = 0.0
        detail = {}
        for sym, qty in positions.items():
            if qty == 0:
                continue
            req = self.requirement(sym, abs(qty))
            amt = (req.initial_usd if level == "initial"
                   else req.maintenance_usd)
            detail[sym] = amt
            total += amt
        shortfall = total - equity_usd
        return {
            "level": level,
            "required_usd": total,
            "equity_usd": equity_usd,
            "shortfall_usd": max(0.0, shortfall),
            "breach": shortfall > 0,
            "per_symbol_usd": detail,
            "official_cme_span": "NOT_RUN",
            "source": "NinjaTrader 2026-08-31 + AMP 2026-10-02 (PUBLISHED)",
        }
