"""DECLARED-cost kernel for the DAILY exploratory cycle (G9 prep build).

Laws frozen by (all under
research/control/terminal_review_2026-10-01/successor/daily_successor/):

- PLAN_DAILY_SUCCESSOR_DRAFT.md §5 (cost law) and §0b gate G5 (co-owner
  decision 2026-10-01): NO PnL-based trim; the async two-sided OPEN
  difference is a BAR-SIDE DIFFERENCE, NOT a simultaneously-measured
  executable spread; O-FOLDS = pessimistic EXPLORATORY fill-facing band,
  C-FULL = control; execution cost is MEASURED only where simultaneous
  quotes exist — everything else DECLARED.
- G5_G6_SPREADS_INPUTEND.md §1.8 — the frozen-READY D1 band table
  (cell ids `D1BAND-<INST>-<C|O>-<FULL|EVAL|FOLDS>`), hardcoded below
  verbatim with the §1.2 aggregate sha pins.
- PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/journal/FILL_ACCOUNTING_SPEC.md
  §1 (price conventions), §2 (spread-once law), §5 (stress tiers),
  adapted to the D1 clock per plan §5: fills at the NEXT D1 bar open on
  the quoted side; no roll/reopen window cells exist at the Daily clock.

Cost components (all DECLARED pessimistic bands, U-register ids carried):
- commission U2 = 0.35 bps per side of traded notional, both legs,
  never amortized;
- slippage U3 = 0.2 pip (non-event) / 1.0 pip (event window) beyond the
  quoted side;
- swap U4/U5 = 1.0 pip per night against the position in BOTH directions
  (pessimistic symmetry, never income), frozen DECLARED calendar
  Sun x1 Mon x1 Tue x1 Wed x3 Thu x1 Fri x0, Sat no event = exactly 7
  pip-nights per 7-night week; accrual boundary 22:00 UTC; an event at E
  charges iff the position from fills strictly before E is nonzero (a
  fill exactly at E neither sees nor triggers E's accrual; a position
  closed exactly at E was open at E- and DOES accrue).
  The OI-2 statement replaces this calendar whole when it lands.

THE BAR-SIDE-DIFFERENCE LAW (this cycle's load-bearing G5 finding):
IBKR HMDS daily bars carry each side's own first print of the session, so
ASK_open and BID_open are asynchronous. The open-side difference is NOT
an executable spread. This kernel therefore fills at the side's OWN open
quote — buys at ASK_open + slip, sells at BID_open - slip — charges
spread_once = |quoted_side_open - mid_open| (the bar-quoted cost of that
fill; spread-once identity spread_once + slip == |fill - mid| holds by
construction), and REPORTS the full open-side difference as the separate
diagnostic field ``bar_side_difference_bps`` with
``bar_side_difference_executable = False`` — never as a cost line.

Stress tiers (FILL_ACCOUNTING_SPEC §5): at tier tau every VARIABLE
component scales — fill = mid +/- tau*(half_spread + slip_band),
commission = tau * 0.000035 * |units| * fill, swap = tau * 1.0 pip/night
(Wed x3 preserved), band-cell p90s x tau. The bar-quoted half-spread
itself is a market fact and does not scale; the stress excess lands in
the slip_beyond_halfspread line so the spread-once identity holds at
every tier (tau = 1.0 reduces exactly to the plain model).

All money arithmetic is Decimal internally (exact hand-checkable
decimals); public dataclasses expose float views for engine/reporting
use. This module computes COSTS and FILL PRICES only — it contains no
performance metric of any kind (RGC-INC-1 law: no PnL/PF/Sharpe/
drawdown/equity-delta/return field in any output).
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterator, Optional, Tuple

# ---------------------------------------------------------------------------
# Frozen constants (DECLARED unless a MEASURED source is named)
# ---------------------------------------------------------------------------

#: U2 — commission, 0.35 bps per side of traded notional (DECLARED).
COMMISSION_RATE = Decimal("0.000035")
COMMISSION_BAND_ID = "U2-0.35BPS-PER-SIDE-DECLARED"

#: U3 — slippage beyond the quoted side (DECLARED pessimistic band).
SLIP_NON_EVENT_PIPS = Decimal("0.2")
SLIP_EVENT_PIPS = Decimal("1.0")
SLIP_BAND_ID_NON_EVENT = "U3-DAILY-0.2PIP-DECLARED"
SLIP_BAND_ID_EVENT = "U3-DAILY-1.0PIP-EVENT-DECLARED"

#: U4/U5 — swap, 1.0 pip per night against the position both directions
#: (DECLARED frozen modeling calendar; the OI-2 statement replaces it whole).
SWAP_PIPS_PER_NIGHT = Decimal("1.0")
SWAP_BAND_ID = "U4U5-1PIP-NIGHT-WEDX3-DECLARED"
SWAP_ACCRUAL_UTC_TIME = _dt.time(22, 0)
#: weekday(int) -> multiplier. Sun=6 .. Sat=5. Friday x0 (no accrual event
#: exists at market close), Saturday no event.
SWAP_WEEKDAY_MULTIPLIERS: Dict[int, int] = {
    6: 1,  # Sunday (reopen boundary)
    0: 1,  # Monday
    1: 1,  # Tuesday
    2: 3,  # Wednesday (spot T+2 rolls settlement Fri->Mon: the weekend)
    3: 1,  # Thursday
    4: 0,  # Friday (close boundary) — no accrual
    5: 0,  # Saturday — no event
}

#: FILL_ACCOUNTING_SPEC §5 — stress tiers.
STRESS_TIERS: Tuple[float, ...] = (1.0, 1.5, 2.0)

#: Pip sizes per instrument (price units per pip). FX-spot vehicles are the
#: executable class; XAU/XAG are listed for band validation completeness
#: only (XAU signal-only per OI-3; XAG NOT_RUN per OI-4 — never vehicles).
PIP_SIZES: Dict[str, Decimal] = {
    "EURUSD": Decimal("0.0001"),
    "GBPUSD": Decimal("0.0001"),
    "AUDUSD": Decimal("0.0001"),
    "NZDUSD": Decimal("0.0001"),
    "USDCHF": Decimal("0.0001"),
    "USDCAD": Decimal("0.0001"),
    "USDJPY": Decimal("0.01"),
    "XAUUSD": Decimal("0.01"),
    "XAGUSD": Decimal("0.001"),
}

#: Quote currency per instrument (drives the conversion-row law).
QUOTE_CCY_OF: Dict[str, str] = {
    "EURUSD": "USD",
    "GBPUSD": "USD",
    "AUDUSD": "USD",
    "NZDUSD": "USD",
    "USDCAD": "USD",
    "XAUUSD": "USD",
    "XAGUSD": "USD",
    "USDJPY": "JPY",  # explicit JPY->USD conversion rows required
    "USDCHF": "CHF",  # explicit CHF->USD conversion rows required
}

# ---------------------------------------------------------------------------
# The frozen D1 band table (G5 §1.8, verbatim, bps, quantile 'lower')
# ---------------------------------------------------------------------------

#: Per-instrument sha-pinned daily aggregates (G5 §1.2) — the source of
#: every cell below. Recomputed from raw 2026-10-01; probe cross-check
#: exact (G5 §1.4).
BAND_AGGREGATE_SHA256: Dict[str, str] = {
    "NZDUSD": "c681402b03e58502fcb7a22d7d7b26ccefcccf5117b20fa2ec82e2689a9782ed",
    "USDCHF": "7fbd3a80e64114c54a411c75adf24725fc9ef631433b341484e6dd40468d69c3",
    "XAUUSD": "02445884c9b28f4a7385e6924ae1b8827d349c41d019f7d7c063c2d54e2c653f",
    "XAGUSD": "492dfbc0803dca58831490d603034859a668e633bef369cc31cfeb0368207bb7",
}

#: Source of record for the band table (read-only reference, prep stage).
BAND_SOURCE_REF = (
    "research/control/terminal_review_2026-10-01/successor/daily_successor/"
    "G5_G6_SPREADS_INPUTEND.md#1.8 (frozen-READY, PASS-pending-freeze at the "
    "registration freeze)"
)


def _cell(inst: str, side: str, window: str, p50: str, p90: str, p95: str,
          mx: str, n: int) -> Dict[str, object]:
    return {
        "cell_id": f"D1BAND-{inst}-{side}-{window}",
        "instrument": inst,
        "side": {"O": "OPEN", "C": "CLOSE"}[side],
        "window": window,
        "p50_bps": float(p50),
        "p90_bps": float(p90),
        "p95_bps": float(p95),
        "max_bps": float(mx),
        "n_days": n,
        "aggregate_sha256": BAND_AGGREGATE_SHA256[inst],
    }


#: The frozen band table, hardcoded from G5 §1.8 (all bps; quantile
#: convention 'lower' = order statistic at floor(q*(n-1))).
D1BAND_TABLE: Dict[str, Dict[str, object]] = {
    c["cell_id"]: c  # type: ignore[index]
    for c in [
        # ---- OPEN side (fill-facing cells — what spread_once prices) ----
        _cell("NZDUSD", "O", "FOLDS", "2.6118", "21.3272", "32.7445", "414.6256", 1031),
        _cell("NZDUSD", "O", "EVAL",  "2.5790", "20.1550", "32.5256", "414.6256", 1291),
        _cell("NZDUSD", "O", "FULL",  "2.5268", "18.8891", "30.1971", "414.6256", 1552),
        _cell("USDCHF", "O", "FOLDS", "27.1656", "60.1794", "74.3012", "642.3908", 1031),
        _cell("USDCHF", "O", "EVAL",  "26.1966", "57.8974", "71.9782", "642.3908", 1291),
        _cell("USDCHF", "O", "FULL",  "24.6858", "55.6476", "70.0525", "642.3908", 1553),
        _cell("XAUUSD", "O", "FOLDS", "45.8149", "168.5161", "229.4216", "1979.9436", 1026),
        _cell("XAUUSD", "O", "EVAL",  "39.6615", "178.8056", "258.5901", "1979.9436", 1283),
        _cell("XAUUSD", "O", "FULL",  "38.4426", "167.4323", "242.4678", "1979.9436", 1544),
        _cell("XAGUSD", "O", "FOLDS", "99.6954", "519.7948", "746.2894", "2454.2424", 1024),
        _cell("XAGUSD", "O", "EVAL",  "91.0865", "536.4807", "774.6032", "2454.2424", 1281),
        _cell("XAGUSD", "O", "FULL",  "83.1665", "523.9870", "766.8394", "2454.2424", 1542),
        # ---- CLOSE side (validation / continuity cells) ----
        _cell("NZDUSD", "C", "FULL",  "0.8822", "18.6544", "33.0409", "239.0719", 1553),
        _cell("NZDUSD", "C", "EVAL",  "0.8834", "21.8526", "34.8600", "239.0719", 1291),
        _cell("NZDUSD", "C", "FOLDS", "0.8616", "22.1107", "37.8657", "239.0719", 1031),
        _cell("USDCHF", "C", "FULL",  "4.5124", "16.0242", "22.7266", "216.0960", 1553),
        _cell("USDCHF", "C", "EVAL",  "5.0810", "17.0275", "25.3951", "216.0960", 1291),
        _cell("USDCHF", "C", "FOLDS", "5.0399", "17.9392", "26.9498", "216.0960", 1031),
        _cell("XAUUSD", "C", "FULL",  "5.5163", "18.6133", "27.4684", "74.1656", 1543),
        _cell("XAUUSD", "C", "EVAL",  "5.8348", "19.8004", "28.0865", "74.1656", 1282),
        _cell("XAUUSD", "C", "FOLDS", "6.8696", "22.6451", "29.7664", "74.1656", 1025),
        _cell("XAGUSD", "C", "FULL",  "10.3526", "40.8256", "73.8310", "162.8053", 1544),
        _cell("XAGUSD", "C", "EVAL",  "9.3699", "48.4475", "75.8573", "162.8053", 1283),
        _cell("XAGUSD", "C", "FOLDS", "7.9051", "53.9084", "82.0345", "162.8053", 1026),
    ]
}

#: Co-owner G5 decision 2026-10-01: O-FOLDS = fill-facing pessimistic
#: EXPLORATORY band; C-FULL = validation control (probe-continuity).
BAND_ROLE_FILL_FACING = "O-FOLDS"
BAND_ROLE_VALIDATION_CONTROL = "C-FULL"

#: Instruments whose D1 bands are NOT YET COMPUTED (plan §5: deterministic
#: derivation from the frozen M1/H1 panels at the registration freeze,
#: label MEASURED-DERIVED; until then NOT_COMPUTED, never guessed).
D1BAND_NOT_COMPUTED_INSTRUMENTS = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD")
NOT_COMPUTED_CELL_LABEL = "D1BAND-NOT_COMPUTED-PENDING-REGISTRATION-FREEZE"

#: The frozen table is quoted to 4 decimal bps (G5 §1.8); band comparisons
#: allow this display-rounding half-width so a day that IS the tabled max
#: (e.g. NZD 2025-03-03, open-side 414.62561... vs tabled 414.6256) is not
#: spuriously rejected.
BAND_ROUNDING_EPS_BPS = 1e-4


def band_cell(instrument: str, role: str = BAND_ROLE_FILL_FACING) -> Optional[Dict[str, object]]:
    """Return the frozen band cell for an instrument's designated role.

    None (NOT_COMPUTED) for instruments whose D1 band derivation is a
    registration-freeze act that has not executed. Fill pricing NEVER
    consumes the cell — fills price from the bar's own quoted side; cells
    are validation bands only (FILL_ACCOUNTING_SPEC §2).
    """
    return D1BAND_TABLE.get(f"D1BAND-{instrument}-{role}")


# ---------------------------------------------------------------------------
# Bars and fills
# ---------------------------------------------------------------------------

def D(x) -> Decimal:
    """Exact-decimal view of a float input (via repr, so hand-written
    fixture floats keep their written value exactly)."""
    if isinstance(x, Decimal):
        return x
    return Decimal(repr(float(x)))


@dataclass(frozen=True)
class DailyBar:
    """One D1 session, both quoted sides, open and close (OI-1 panel shape).

    ``session_date`` is the ISO session date; fills price at the OPEN of the
    bar (next-bar-open law: a decision at T consuming bars through T close
    fills at the T+1 bar open).
    """

    session_date: str
    bid_open: float
    ask_open: float
    bid_close: float
    ask_close: float

    def dec(self, name: str) -> Decimal:
        return D(getattr(self, name))

    @property
    def mid_open(self) -> Decimal:
        return (self.dec("ask_open") + self.dec("bid_open")) / 2

    @property
    def mid_close(self) -> Decimal:
        return (self.dec("ask_close") + self.dec("bid_close")) / 2


BUY, SELL = "BUY", "SELL"


@dataclass(frozen=True)
class FillQuote:
    """The priced fill (all amounts in QUOTE currency, Decimal-exact).

    Crossing lines obey the spread-once law exactly:
    ``spread_once_per_unit + slip_beyond_per_unit == |fill - mid_at_fill|``.
    ``bar_side_difference_bps`` is the DIAGNOSTIC open-side difference
    (full width) — reported, never charged (BAR-SIDE-DIFFERENCE law).
    """

    symbol: str
    session_date: str
    side: str                      # BUY | SELL
    units: Decimal                 # |delta|, base-currency units
    fill_price: Decimal            # quote ccy per base unit
    quoted_side_price: Decimal     # ask_open (BUY) | bid_open (SELL)
    fill_side_quote: str           # "ask" | "bid"
    mid_at_fill: Decimal           # mid_open of the same fill bar
    spread_once_per_unit: Decimal  # |quoted_side - mid| (bar-quoted)
    slip_beyond_per_unit: Decimal  # |fill - quoted_side| (U3 band + tier excess)
    spread_once_total: Decimal
    slip_beyond_total: Decimal
    commission_total: Decimal      # U2, quote ccy
    bar_side_difference_bps: Decimal   # DIAGNOSTIC only
    bar_side_difference_executable: bool  # always False (frozen law)
    spread_band_cell_id: str       # validation cell id / NOT_COMPUTED label
    slippage_band_id: str
    commission_band_id: str
    swap_band_id: str
    tier: float
    event_window: bool

    def crossing_identity_residual(self) -> Decimal:
        """Per-fill spread-once identity residual (exact; must be 0)."""
        return (self.spread_once_per_unit + self.slip_beyond_per_unit
                - abs(self.fill_price - self.mid_at_fill))

    def to_jsonable(self) -> Dict[str, object]:
        return {
            "symbol": self.symbol,
            "session_date": self.session_date,
            "side": self.side,
            "units": float(self.units),
            "fill_price": float(self.fill_price),
            "quoted_side_price": float(self.quoted_side_price),
            "fill_side_quote": self.fill_side_quote,
            "mid_at_fill": float(self.mid_at_fill),
            "spread_once_total_quoteccy": float(self.spread_once_total),
            "slip_beyond_total_quoteccy": float(self.slip_beyond_total),
            "commission_total_quoteccy": float(self.commission_total),
            "bar_side_difference_bps": float(self.bar_side_difference_bps),
            "bar_side_difference_executable": self.bar_side_difference_executable,
            "spread_band_cell_id": self.spread_band_cell_id,
            "slippage_band_id": self.slippage_band_id,
            "commission_band_id": self.commission_band_id,
            "swap_band_id": self.swap_band_id,
            "tier": self.tier,
            "event_window": self.event_window,
        }


class DeclaredCostKernel:
    """DECLARED daily-clock cost kernel for one instrument.

    Produces fill prices and cost lines only. Band cells are validation
    bands, never a pricing source for the fill (the fill prices at the
    bar's own quoted side; spec §2 law "measured cells enter only as
    validation bands").
    """

    def __init__(self, symbol: str, tier: float = 1.0, event_window: bool = False):
        if symbol not in PIP_SIZES:
            raise ValueError(f"unknown instrument {symbol!r} (no frozen pip size)")
        if tier not in STRESS_TIERS:
            raise ValueError(f"tier {tier!r} not in frozen STRESS_TIERS {STRESS_TIERS}")
        self.symbol = symbol
        self.pip_size = PIP_SIZES[symbol]
        self.tier = Decimal(repr(tier))
        self.tier_f = tier
        self.event_window = event_window

    # -- slippage band ------------------------------------------------------

    @property
    def slip_pips(self) -> Decimal:
        return SLIP_EVENT_PIPS if self.event_window else SLIP_NON_EVENT_PIPS

    @property
    def slippage_band_id(self) -> str:
        return SLIP_BAND_ID_EVENT if self.event_window else SLIP_BAND_ID_NON_EVENT

    # -- fill pricing (BAR-SIDE-DIFFERENCE law) ------------------------------

    def price_fill(self, bar: DailyBar, side: str, units: float | int | Decimal) -> FillQuote:
        if side not in (BUY, SELL):
            raise ValueError(f"side must be BUY or SELL, got {side!r}")
        units_d = D(units)
        if units_d <= 0:
            raise ValueError("units must be positive (sign is carried by side)")

        ask_o, bid_o = bar.dec("ask_open"), bar.dec("bid_open")
        if not ask_o >= bid_o:
            # Crossed raw quotes on the fill bar: the kernel still prices from
            # the raw side quotes (crossed-book filter governs band STATISTICS
            # only — G5 §1.6); flag via the diagnostic, never fail to 0-price
            # (UNAVAILABLE != 0 law is the caller's, for MISSING quotes).
            pass
        mid = bar.mid_open
        pip = self.pip_size
        slip_unit = self.slip_pips * pip

        if side == BUY:
            quoted = ask_o
            crossing = self.tier * (abs(ask_o - mid) + slip_unit)
            fill_price = mid + crossing
        else:
            quoted = bid_o
            crossing = self.tier * (abs(mid - bid_o) + slip_unit)
            fill_price = mid - crossing

        spread_once_unit = abs(quoted - mid)          # bar-quoted, unscaled
        slip_beyond_unit = abs(fill_price - quoted)   # U3 band + tier excess
        if slip_beyond_unit < 0:  # defensive; tau >= 1 keeps this >= 0
            slip_beyond_unit = Decimal(0)

        spread_once_total = spread_once_unit * units_d
        slip_beyond_total = slip_beyond_unit * units_d
        commission_total = self.tier * COMMISSION_RATE * units_d * fill_price

        # BAR-SIDE-DIFFERENCE diagnostic: full open-side width, bps of mid.
        side_diff_bps = (ask_o - bid_o) / mid * Decimal(10000)

        cell = band_cell(self.symbol, BAND_ROLE_FILL_FACING)
        cell_id = cell["cell_id"] if cell else NOT_COMPUTED_CELL_LABEL  # type: ignore[index]

        fq = FillQuote(
            symbol=self.symbol,
            session_date=bar.session_date,
            side=side,
            units=units_d,
            fill_price=fill_price,
            quoted_side_price=quoted,
            fill_side_quote="ask" if side == BUY else "bid",
            mid_at_fill=mid,
            spread_once_per_unit=spread_once_unit,
            slip_beyond_per_unit=slip_beyond_unit,
            spread_once_total=spread_once_total,
            slip_beyond_total=slip_beyond_total,
            commission_total=commission_total,
            bar_side_difference_bps=side_diff_bps,
            bar_side_difference_executable=False,
            spread_band_cell_id=cell_id,
            slippage_band_id=self.slippage_band_id,
            commission_band_id=COMMISSION_BAND_ID,
            swap_band_id=SWAP_BAND_ID,
            tier=self.tier_f,
            event_window=self.event_window,
        )
        if fq.crossing_identity_residual() != 0:
            raise AssertionError(
                "spread-once identity violated per fill: "
                f"{fq.crossing_identity_residual()}"
            )
        return fq

    # -- swap ----------------------------------------------------------------

    def swap_charge(self, units_abs: Decimal | float | int,
                    multiplier: int) -> Decimal:
        """One accrual event's charge, quote ccy, against the position:
        ``|u| x pip_size x 1.0 pip x multiplier x tier`` (both directions,
        never income)."""
        u = D(units_abs)
        if multiplier < 0:
            raise ValueError("multiplier must be >= 0")
        return u * self.pip_size * SWAP_PIPS_PER_NIGHT * multiplier * self.tier

    @staticmethod
    def swap_multiplier(event_ts: _dt.datetime) -> int:
        return SWAP_WEEKDAY_MULTIPLIERS[event_ts.weekday()]

    @staticmethod
    def iter_swap_events(start_ts: _dt.datetime, end_ts: "_dt.datetime"
                         ) -> Iterator[Tuple["_dt.datetime", int, bool]]:
        """Accrual boundaries E with ``start_ts < E <= end_ts`` (membership
        law: E charges iff the position from fills strictly before E is
        nonzero — a position closed exactly at E was open at E- and DOES
        accrue). Yields ``(event_ts, multiplier, wed_x3)`` for multiplier
        days only (Fri x0 / Sat are not events)."""
        if end_ts < start_ts:
            return
        d = start_ts.date()
        while True:
            ev = _dt.datetime.combine(d, SWAP_ACCRUAL_UTC_TIME,
                                      tzinfo=_dt.timezone.utc)
            if ev > start_ts and ev <= end_ts:
                m = SWAP_WEEKDAY_MULTIPLIERS[ev.weekday()]
                if m > 0:
                    yield ev, m, (ev.weekday() == 2)
            if ev > end_ts:
                return
            d += _dt.timedelta(days=1)

    # -- band validation (never a cost) --------------------------------------

    def validate_bar_spread(self, bar: DailyBar, which: str = "OPEN",
                            role: str = BAND_ROLE_FILL_FACING
                            ) -> Dict[str, object]:
        """Validate the bar's own quoted spread against the frozen band.

        Validation-only report (spec §2): the band NEVER prices a fill.
        For NOT_COMPUTED instruments returns the typed
        ``NOT_COMPUTED`` verdict — never a guessed band (plan §5).
        """
        if which == "OPEN":
            spread = bar.dec("ask_open") - bar.dec("bid_open")
            mid = bar.mid_open
        elif which == "CLOSE":
            spread = bar.dec("ask_close") - bar.dec("bid_close")
            mid = bar.mid_close
        else:
            raise ValueError("which must be 'OPEN' or 'CLOSE'")
        spread_bps = float(spread / mid * Decimal(10000))
        cell = band_cell(self.symbol, role)
        if cell is None:
            return {
                "instrument": self.symbol,
                "spread_bps": spread_bps,
                "cell_id": NOT_COMPUTED_CELL_LABEL,
                "verdict": "NOT_COMPUTED",
                "reason": "D1 band derivation is a registration-freeze act "
                          "(plan §5); never guessed",
            }
        return {
            "instrument": self.symbol,
            "spread_bps": spread_bps,
            "cell_id": cell["cell_id"],
            "p50_bps": cell["p50_bps"],
            "p90_bps": cell["p90_bps"],
            "max_bps": cell["max_bps"],
            "within_max": spread_bps <= float(cell["max_bps"]) + BAND_ROUNDING_EPS_BPS,  # type: ignore[arg-type]
            "gt_p90": spread_bps > float(cell["p90_bps"]),  # type: ignore[arg-type]
            "verdict": "VALIDATED_AGAINST_FROZEN_BAND",
            "note": "validation band only — fills price at the bar's own "
                    "quoted side, never from the cell",
        }
