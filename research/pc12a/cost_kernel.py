"""Cost kernel — measured cells C1/C2/C3 + declared bands U2/U3/U4-U5.

DUAL-SOURCE LAW (FILL_ACCOUNTING_SPEC §3, erratum 2026-09-29): the C2
Mon-Thu (21:00,22:00] roll cell is governed by the Lane D audit's CORRECTED
numbers, NOT by the COST_AUTHORITY_TABLE's Mon-Thu column — that column was
measured on the WRONG hour (22:00-23:00Z) and undercharges the declared
window ~1.3-2x. Both sources are cited per cell below so no implementation
can silently pick the stale column.

Cell provenance (p50/p90 in PIPS):
- C1 Friday-20:00 general:  COST_AUTHORITY_TABLE.md C1, reproduced EXACTLY
  by DATA_AUDIT_REPORT.md §D(ii), n=286/286 per pair.
- C2 Mon-Thu (21:00,22:00]: DATA_AUDIT_REPORT.md §D(iii) CORRECTED cells
  (GOVERNING; n=65,109 / 65,274 / 64,892). Table's Mon-Thu column
  (0.6/2.7, 1.4/5.8, 1.0/4.9) is the hour-shifted artifact - REFUSED here.
- C2 Friday (21:00,22:00]:  COST_AUTHORITY_TABLE.md C2 Fri, reproduced
  EXACTLY by the audit (n=5,964-5,979 per pair).
- C3 Sunday reopen:         COST_AUTHORITY_TABLE.md C3, corroborated by the
  audit §D(iv) spot sample (n=4 vs the table's n=283/284 full population).

Declared (UNMEASURED register, pessimistic bands):
- U2 commission 0.35 bps of traded notional per side (both entry and exit).
- U3 slippage 0.2 pip/side non-event, 1.0 pip/side inside event windows
  (rollover 21:00-23:00 UTC, Sunday reopen first 15 min).
- U4/U5 swap 1.0 pip/night charged AGAINST the position both directions,
  Wed x3, accrual boundary 22:00 UTC, never income.

Stress tiers x1.0/x1.5/x2.0 (spec §5): every VARIABLE component scales
(crossing distance, commission rate, swap rate, window-cell p90); fences do
not. The spread-once identity holds at every tier by construction.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Dict, Optional

from . import panels as _panels

# --- measured cells (pips; p50/p90) ----------------------------------------

MEASURED_CELLS: Dict[str, Dict[str, Dict[str, float]]] = {
    # source: COST_AUTHORITY_TABLE.md C1 == DATA_AUDIT_REPORT.md §D(ii)
    # (exact agreement, n=286/286 per pair)
    "C1": {
        "EURUSD": {"p50": 0.3, "p90": 0.5},
        "GBPUSD": {"p50": 0.8, "p90": 1.3},
        "USDJPY": {"p50": 0.5, "p90": 0.9},
    },
    # source: DATA_AUDIT_REPORT.md §D(iii) CORRECTED (21:00,22:00] Mon-Thu
    # cells -- GOVERNING over the table's hour-shifted Mon-Thu column
    "C2_MON_THU": {
        "EURUSD": {"p50": 1.2, "p90": 3.7},   # n=65,109
        "GBPUSD": {"p50": 2.8, "p90": 7.8},   # n=65,274
        "USDJPY": {"p50": 2.1, "p90": 7.4},   # n=64,892
    },
    # source: COST_AUTHORITY_TABLE.md C2 Fri == audit §D(iii) (exact)
    "C2_FRI": {
        "EURUSD": {"p50": 0.5, "p90": 1.1},
        "GBPUSD": {"p50": 1.2, "p90": 2.3},
        "USDJPY": {"p50": 0.8, "p90": 1.8},
    },
    # source: COST_AUTHORITY_TABLE.md C3; corroborated audit §D(iv)
    "C3": {
        "EURUSD": {"p50": 5.9, "p90": 9.0},
        "GBPUSD": {"p50": 13.4, "p90": 23.8},
        "USDJPY": {"p50": 11.0, "p90": 22.0},
    },
}

# --- declared bands ----------------------------------------------------------

COMMISSION_RATE_PER_SIDE = 3.5e-05        # U2: 0.35 bps of notional
SLIP_NON_EVENT_PIPS = 0.2                 # U3 band per side
SLIP_EVENT_PIPS = 1.0                     # U3 inside event windows
SWAP_PIPS_PER_NIGHT = 1.0                 # U4/U5 against, both directions
SWAP_WEDNESDAY_MULTIPLIER = 3
STRESS_TIERS = (1.0, 1.5, 2.0)

# --- fill-quote law (FILL_ACCOUNTING_SPEC §1-§2) ---------------------------


@dataclass(frozen=True)
class FillQuote:
    """Spread-once decomposition of one fill.

    ``spread_once + slip_beyond_halfspread == |fill - mid_at_fill|`` per
    unit, exactly (the two attribution sub-lines; NO third crossing line).
    """

    side: str                 # "buy" | "sell"
    delta_units: int
    fill_price: float
    quoted_side: float        # ask_open (buy) / bid_open (sell)
    mid_at_fill: float        # mid_open of the SAME fill bar
    spread_once_pips: float
    slip_pips: float
    cell_id: Optional[str]    # measured cell used for validation/window pricing
    graded: bool = False
    slip_band_pips: float = 0.0   # U3 band portion (== slip when ungraded)
    gap_excess_pips: float = 0.0  # graded worst-fill excess inside slip line

    @property
    def spread_once_usd(self) -> float:
        return abs(self.quoted_side - self.mid_at_fill) * abs(self.delta_units)

    @property
    def slip_beyond_halfspread_usd(self) -> float:
        return abs(self.fill_price - self.quoted_side) * abs(self.delta_units)

    @property
    def cross_cost_usd(self) -> float:
        return abs(self.fill_price - self.mid_at_fill) * abs(self.delta_units)

    @property
    def loss_fill_candidate(self) -> bool:
        return self.gap_excess_pips > 0.0


class CostKernel:
    """Per-pair, per-tier pricing of fills, commission and swap.

    All USD conversions are quote-currency aware: USD-quoted pairs
    (EURUSD/GBPUSD) take notional = units x price; JPY-quoted USDJPY takes
    notional = units (base IS USD), pip value converted at the accrual-time
    mid (declared convention, disclosed in the dry-run report).
    """

    def __init__(self, symbol: str, tier: float = 1.0):
        if tier not in STRESS_TIERS:
            raise ValueError(f"tier {tier} not in frozen {STRESS_TIERS}")
        if symbol not in _panels.PAIR_SPECS:
            raise ValueError(f"unknown pair {symbol}")
        self.symbol = symbol
        self.spec = _panels.PAIR_SPECS[symbol]
        self.tier = tier
        self.pip = self.spec.pip_size

    # -- crossing -----------------------------------------------------------

    def slip(self, event_window: bool) -> float:
        """U3 band in PRICE units, tier-scaled."""
        pips = SLIP_EVENT_PIPS if event_window else SLIP_NON_EVENT_PIPS
        return self.tier * pips * self.pip

    def price_ordinary_fill(self, side: str, delta_units: int,
                            bid_open: float, ask_open: float) -> FillQuote:
        """Next-bar-open fill at the quoted side +/- the U3 band (§1.3),
        tier-scaled per §5: fill = mid +/- tau*(half_spread + slip_band).

        buys: fill = mid + tau*(h + s); sells: fill = mid - tau*(h + s);
        mid_at_fill = (bid_open + ask_open)/2 of the same bar. The two
        attribution lines are tau*h and tau*s and sum to |fill - mid|
        exactly at every tier.
        """
        if side not in ("buy", "sell"):
            raise ValueError(side)
        mid = (bid_open + ask_open) / 2.0
        h = abs((ask_open if side == "buy" else bid_open) - mid)
        slip = self.slip(event_window=False)
        quoted = mid + self.tier * h if side == "buy" else mid - self.tier * h
        fill = quoted + slip if side == "buy" else quoted - slip
        return FillQuote(side=side, delta_units=delta_units, fill_price=fill,
                         quoted_side=quoted, mid_at_fill=mid,
                         spread_once_pips=self.tier * h / self.pip,
                         slip_pips=slip / self.pip, cell_id="C1",
                         slip_band_pips=slip / self.pip)

    def price_graded_fill(self, side: str, delta_units: int, bid_open: float,
                          ask_open: float, bid_close: float,
                          ask_close: float) -> FillQuote:
        """Worst-fill grading for exception fills (§1.5).

        Executes at the WORST of the fill bar's open and close on the quoted
        side (buys max(ask_open, ask_close); sells min(bid_open, bid_close)),
        then +/- the U3 band -- NEVER at the stop/level price. mid_at_fill
        stays the fill bar's OPEN mid; the distance beyond the ordinary
        quoted-side-open+band fill is booked as GAP EXCESS inside the slip
        line.
        """
        mid = (bid_open + ask_open) / 2.0
        slip = self.slip(event_window=False)
        quoted = ask_open if side == "buy" else bid_open
        h = abs(quoted - mid)          # the bar's measured half-spread
        if side == "buy":
            worst = max(ask_open, ask_close)
            fill = worst + slip
        else:
            worst = min(bid_open, bid_close)
            fill = worst - slip
        ordinary = quoted + slip if side == "buy" else quoted - slip
        excess = abs(fill - ordinary)
        # the graded fill is MARKET-set; only the U3 band scales with the
        # tier -- spread_once stays the measured half-spread and the gap
        # excess stays the realized market impact
        cross = abs(fill - mid) * abs(delta_units)
        spread_once = h * abs(delta_units)
        return FillQuote(side=side, delta_units=delta_units, fill_price=fill,
                         quoted_side=quoted, mid_at_fill=mid,
                         spread_once_pips=h / self.pip,
                         slip_pips=(cross - spread_once) / abs(delta_units)
                         / self.pip,
                         cell_id="C1",
                         graded=True, slip_band_pips=slip / self.pip,
                         gap_excess_pips=excess / self.pip)

    def price_window_fill(self, side: str, delta_units: int, mid_at_fill: float,
                          ts_fill: dt.datetime) -> FillQuote:
        """Rollover-window / Sunday-reopen fill priced from MEASURED cells
        (§3): S_eff = max(p90 window cell, p90 general C1); fill =
        mid +/- (S_eff/2 + 1.0 pip event slip); tier scales S_eff and slip.

        Windows: C2 = the (21:00, 22:00] roll window (Friday vs Mon-Thu
        cell); C3 = the Sunday-reopen first 15 minutes with the reopen
        instant tzdata-rebuilt at 17:00 America/New_York (audit §B DST
        evidence: winter 22:00Z, summer 21:00Z)."""
        from . import calendar_service as _cal

        if _cal.is_sunday_reopen(ts_fill):
            cell_id = "C3"
        elif _cal.is_in_roll_charge_window(ts_fill):
            weekday = ts_fill.astimezone(dt.timezone.utc).strftime("%a")
            cell_id = "C2_FRI" if weekday == "Fri" else "C2_MON_THU"
        else:
            raise ValueError(f"ts {ts_fill} not in a window cell")
        cell = MEASURED_CELLS[cell_id][self.symbol]
        s_eff = max(cell["p90"], MEASURED_CELLS["C1"][self.symbol]["p90"])
        s_eff *= self.tier
        half = s_eff / 2.0 * self.pip
        slip = self.slip(event_window=True)
        if side == "buy":
            fill = mid_at_fill + half + slip
        else:
            fill = mid_at_fill - half - slip
        # attribution: quoted_side is the synthetic band edge mid +/- half
        quoted = mid_at_fill + half if side == "buy" else mid_at_fill - half
        return FillQuote(side=side, delta_units=delta_units, fill_price=fill,
                         quoted_side=quoted, mid_at_fill=mid_at_fill,
                         spread_once_pips=half / self.pip,
                         slip_pips=slip / self.pip, cell_id=cell_id,
                         slip_band_pips=slip / self.pip)

    # -- non-crossing components --------------------------------------------

    def notional_usd(self, units: float, price: float) -> float:
        """Traded notional in USD (quote-currency aware)."""
        return abs(units) * price if self.spec.quote_is_usd else abs(units)

    def commission(self, units: float, fill_price: float) -> float:
        """U2: tau x 0.35 bps of USD notional, per side, never amortized."""
        return self.tier * COMMISSION_RATE_PER_SIDE * self.notional_usd(
            units, fill_price)

    def pip_value_usd(self, mid: float) -> float:
        """USD value of 1 pip on 1 unit of base (JPY converted at mid)."""
        v = self.pip
        return v if self.spec.quote_is_usd else v / mid

    def swap_usd(self, units_abs: float, multiplier: int,
                 mid: float) -> float:
        """U4/U5: tau x 1.0 pip/night x multiplier, charged AGAINST the
        position in BOTH directions (pessimistic symmetry; never income)."""
        return (self.tier * SWAP_PIPS_PER_NIGHT * multiplier
                * units_abs * self.pip_value_usd(mid))

    def estimate_all_in(self, side: str, delta_units: int, bid_close: float,
                        ask_close: float) -> Dict[str, float]:
        """Pre-commit cost estimate from the DECISION bar's close quotes
        (cost guard §8): est spread_once + est slip + est commission."""
        q = self.price_ordinary_fill(side, delta_units, bid_close, ask_close)
        comm = self.commission(delta_units, q.fill_price)
        return {
            "est_fill_price": q.fill_price,
            "est_spread_once_usd": q.spread_once_usd,
            "est_slip_usd": q.slip_beyond_halfspread_usd,
            "est_commission_usd": comm,
            "est_total_usd": q.spread_once_usd
            + q.slip_beyond_halfspread_usd + comm,
        }


def dual_source_c2_doc() -> Dict[str, str]:
    """Machine-readable dual-source citation for the corrected C2 cells."""
    return {
        "C2_MON_THU": (
            "GOVERNING: DATA_AUDIT_REPORT.md #D(iii) corrected (21:00,22:00] "
            "cells; COST_AUTHORITY_TABLE Mon-Thu column measured on the "
            "wrong hour (22:00-23:00Z) and REFUSED"),
        "C2_FRI": ("COST_AUTHORITY_TABLE.md C2 Fri, reproduced exactly by "
                   "DATA_AUDIT_REPORT.md #D(iii)"),
        "C1": ("COST_AUTHORITY_TABLE.md C1, reproduced exactly by "
               "DATA_AUDIT_REPORT.md #D(ii), n=286/286 per pair"),
        "C3": ("COST_AUTHORITY_TABLE.md C3, corroborated by audit #D(iv) "
               "spot sample"),
    }
