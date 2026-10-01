"""Corpus-verbatim rule implementations for the admitted daily slate.

The two legs of DAILY-EXPLORATORY-V1 (slate frozen per FREEZE.md item 5:
DS-03 + DS-05 only; 5 candidates parked by the owner review law —
PLAN_DAILY_SUCCESSOR_DRAFT section 0b item 1). Every corpus-quoted
parameter below is a frozen constant with its corpus citation in the
comment; every declared PARAM-GAP resolution carries its label.

**DS-03 — USDJPY-S065** (corpus verbatim, symbols/USDJPY.md S65):
    "Signal: NATGAS 10d ret > +15% (breaking structure) khi Brent flat.
     Trade: long USDJPY 5 phien, stop 1xATR. ... Coupling: chi khi Brent
     flat (de tach channel -- neu Brent cung chay thi la S64)."
- NATGAS = RNGWHHD (Henry Hub spot, EIA, OI-5 signal-only); Brent =
  RBRTE (Europe Brent spot, EIA, OI-5).
- Brent-flat gate is CORPUS-MANDATORY (S65 coupling line); the
  unquantified "flat" is grid G1 (<=3 nodes, plan section 3): node A
  null-control (gate OFF, reported only, never selectable), node B
  |RBRTE 10d ret| < 3% (the G7 frozen DEFAULT), node C < 5%.
- EIA serving 1bd declared (OI-5): a 10d return on bars through T
  decides at the T+1 session open; EIA values are never fill prices.
- Trade: long USDJPY, hold 5 sessions (EXIT_HOLD_N@1: entry fill
  session is session 0; exit decided at the close of the 5th held
  session, filled at the next session open), stop 1x ATR-14
  (STOP_K_ATR@1: stop level = fill price - k*ATR14(T) for a long,
  T = signal session; breach detected on the D1 bar low, exit filled
  at the next session open — DAILY-CLOCK-STOP@1, no intraday clock).
- ATR-14: Wilder RMA on the vehicle D1 mid OHLC, SMA(14) seed
  (ATR14_WILDER@1 declared convention).

**DS-05 — EURUSD-S006** (corpus verbatim, symbols/EURUSD.md S6):
    "Signal: rank 20d return cua {EUR,GBP,AUD,NZD,CHF,JPY,CAD} vs USD;
     vao EURUSD long chi khi EUR rank 1-2. Trade: hold toi khi roi khoi
     top-3, stop 2xATR. ... Coupling: rank nhat quan 2 tuan lien tiep
     moi vao."
- Cross-sectional rank of 20d returns of the 7 currencies vs USD;
  rank 1 = strongest (RANK_WIN20@1; USD-quoted pairs JPY/CHF/CAD
  measured as the INVERSE price return — the value of the currency in
  USD — INVERSE_RET@1 declared; ties broken lexicographically by
  currency code TIE_LEX@1).
- Entry: long EURUSD when EUR rank in {1,2} (ENTRY_RANK_1_2@1) AND the
  2-consecutive-week consistency holds (corpus coupling = entry law):
  EUR rank in top-2 at the consumed bar T AND at the bar 5 sessions
  earlier on the vehicle calendar (WEEK2_CONSISTENCY_5SESS@1 declared).
- Exit: EUR rank drops out of top-3 (EXIT_RANK_TOP3@1); stop 2xATR-14
  (same STOP_K_ATR@1 law as DS-03 with k=2). No time cap in corpus.
- Inputs: 7 USD-pair D1 closes — EURUSD/GBPUSD/USDJPY from the M1
  panels (declared 17:00 ET aggregation), AUDUSD/USDCAD from the H1 ANC
  panel + G6 IBKR extension, NZDUSD/USDCHF from the IBKR panels-of-
  record (OI-1). One missing/stale input blocks the leg fail-closed
  (BLOCKED_STALE) — the rank needs all 7.

Both rules are PURE signal computers over consumed-bar snapshots: they
take the input state at consumed bar T and return an intent (ENTER /
EXIT / HOLD / NO_SIGNAL) plus the frozen reason codes; fills, costs and
books live in the battery engine. No performance field exists here
(RGC-INC-1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Frozen corpus parameters (verbatim citations in the docstring above)
# ---------------------------------------------------------------------------

#: DS-03 — corpus "NATGAS 10d ret > +15%"
DS03_NG_WINDOW = 10
DS03_NG_TRIGGER = Decimal("0.15")
#: DS-03 — corpus "khi Brent flat" quantified by grid G1 (plan section 3):
#: A = null-control (gate OFF; REPORTED ONLY, never selectable — G7),
#: B = |10d ret| < 3% (frozen default), C = |10d ret| < 5%.
DS03_BRENT_WINDOW = 10
DS03_GRID = {
    "A": None,      # null-control: no Brent-flat filter
    "B": Decimal("0.03"),
    "C": Decimal("0.05"),
}
DS03_GRID_DEFAULT = "B"
DS03_GRID_SELECTABLE = ("B", "C")
#: DS-03 — corpus "long USDJPY 5 phien, stop 1xATR"
DS03_HOLD_SESSIONS = 5
DS03_STOP_ATR_MULT = Decimal("1")
#: DS-03/DS-05 — ATR window (PARAM-GAP declared: D1 ATR-14 convention)
ATR_WINDOW = 14

#: DS-05 — corpus "rank 20d return cua {EUR,GBP,AUD,NZD,CHF,JPY,CAD} vs USD"
DS05_RANK_WINDOW = 20
DS05_CURRENCIES = ("AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD")
#: USD-quoted pairs (currency is the QUOTE): value-of-currency-in-USD is
#: the inverse price (INVERSE_RET@1 declared).
DS05_USD_QUOTED = ("CAD", "CHF", "JPY")
#: DS-05 — corpus "vao EURUSD long chi khi EUR rank 1-2"
DS05_ENTRY_RANK_MAX = 2
#: DS-05 — corpus "hold toi khi roi khoi top-3"
DS05_EXIT_RANK_MAX = 3
#: DS-05 — corpus coupling "rank nhat quan 2 tuan lien tiep moi vao":
#: 1 week = 5 vehicle sessions on the consumed-bar calendar
#: (WEEK2_CONSISTENCY_5SESS@1 declared resolution).
DS05_CONSISTENCY_SESSIONS = 5
#: DS-05 — corpus "stop 2xATR"
DS05_STOP_ATR_MULT = Decimal("2")

ENTRY_REASON_DS03 = "S065_NATGAS10D_GT_15PCT_BRENTFLAT"
ENTRY_REASON_DS05 = "S006_EUR_RANK_TOP2_2WK_CONSISTENT"
EXIT_REASON_HOLD = "HOLD_SESSIONS_REACHED"
EXIT_REASON_STOP = "STOP_K_ATR_BREACH"
EXIT_REASON_RANK = "EUR_RANK_OUT_OF_TOP3"
EXIT_REASON_FOLD_EDGE = "FOLD_EDGE_FORCE_FLAT"


# ---------------------------------------------------------------------------
# Signal state snapshots (consumed-bar T; all values at bar close)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DS03Inputs:
    """Consumed-bar state for DS-03 (all through bar T)."""

    session_date: str                 # consumed bar T (EIA calendar)
    ng_ret10: Decimal                 # RNGWHHD 10-session return
    br_ret10: Decimal                 # RBRTE 10-session return
    atr14_vehicle: Decimal            # USDJPY ATR-14 at T (JPY units)

    def brent_flat(self, node: str) -> Optional[bool]:
        """None for node A (gate off); else |br_ret10| < threshold."""
        thr = DS03_GRID[node]
        if thr is None:
            return None
        return abs(self.br_ret10) < thr


@dataclass(frozen=True)
class DS05Inputs:
    """Consumed-bar state for DS-05 (all through bar T)."""

    session_date: str                 # consumed bar T (joint calendar)
    ret20: Dict[str, Decimal]         # currency -> 20-session return vs USD
    atr14_vehicle: Decimal            # EURUSD ATR-14 at T
    eur_rank_hist: Tuple[int, ...] = ()   # EUR rank, oldest..newest

    def ranks(self) -> Dict[str, int]:
        """Cross-sectional rank (1 = strongest vs USD; ties lexicographic)."""
        order = sorted(DS05_CURRENCIES,
                       key=lambda c: (-self.ret20[c], c))
        return {c: i + 1 for i, c in enumerate(order)}

    def eur_rank(self) -> int:
        return self.ranks()["EUR"]


# ---------------------------------------------------------------------------
# Rule intents
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RuleIntent:
    """What the rule wants at the T+1 open, given the position state."""

    action: str            # ENTER | EXIT | HOLD | NO_SIGNAL
    reason_code: str
    direction: str         # LONG | "" (both admitted legs are long-only)
    stop_level: Optional[Decimal] = None   # absolute stop (quote ccy)
    detail: Dict[str, object] = field(default_factory=dict)


class DS03Rule:
    """USDJPY-S065 (xasset_energy_lng). Pure stateless signal computer."""

    sleeve_id = "DS-03"
    corpus_gid = "USDJPY-S065"
    family_id = "G-XASSET"
    mech_key = "xasset_energy_lng"
    vehicle = "USDJPY"

    def entry_signal(self, x: DS03Inputs, grid_node: str) -> bool:
        if grid_node not in DS03_GRID:
            raise ValueError(f"unknown grid node {grid_node!r}")
        if x.ng_ret10 <= DS03_NG_TRIGGER:
            return False
        flat = x.brent_flat(grid_node)
        if flat is None:                      # node A null-control
            return True
        return flat

    def intent_entry(self, x: DS03Inputs, grid_node: str
                     ) -> Optional[RuleIntent]:
        if self.entry_signal(x, grid_node):
            return RuleIntent(
                action="ENTER", reason_code=ENTRY_REASON_DS03,
                direction="LONG", stop_level=None,
                detail={"ng_ret10": str(x.ng_ret10),
                        "br_ret10": str(x.br_ret10),
                        "grid_node": grid_node,
                        "brent_threshold": str(DS03_GRID[grid_node])})
        return None

    def stop_level(self, fill_price: Decimal, x: DS03Inputs) -> Decimal:
        """STOP_K_ATR@1: long stop = fill - 1x ATR14(signal bar)."""
        return fill_price - DS03_STOP_ATR_MULT * x.atr14_vehicle

    def exits_due(self, held_sessions: int, bar_low_mid: Decimal,
                  stop_level: Decimal) -> Optional[Tuple[str, str]]:
        """Exit check at the close of each held session.

        Returns (reason_code, which) or None. STOP first (risk law),
        then the corpus 5-session hold.
        """
        if bar_low_mid <= stop_level:
            return (EXIT_REASON_STOP, "low<=stop")
        if held_sessions >= DS03_HOLD_SESSIONS:
            return (EXIT_REASON_HOLD, "5 phien")
        return None


class DS05Rule:
    """EURUSD-S006 (trend_xsect_antiusd_rank). Pure signal computer."""

    sleeve_id = "DS-05"
    corpus_gid = "EURUSD-S006"
    family_id = "A-TREND"
    mech_key = "usdbasket_rank"
    vehicle = "EURUSD"

    def entry_signal(self, x: DS05Inputs,
                     prior_rank: Optional[int]) -> bool:
        """Corpus entry law: EUR rank 1-2 now AND 1 week earlier
        (2-consecutive-week consistency, coupling line = entry law)."""
        if x.eur_rank() > DS05_ENTRY_RANK_MAX:
            return False
        if prior_rank is None or prior_rank > DS05_ENTRY_RANK_MAX:
            return False
        return True

    def prior_week_rank(self, x: DS05Inputs) -> Optional[int]:
        """EUR rank 5 sessions earlier on the consumed-bar history
        (eur_rank_hist oldest..newest)."""
        h = x.eur_rank_hist
        if len(h) < DS05_CONSISTENCY_SESSIONS + 1:
            return None
        return h[-(DS05_CONSISTENCY_SESSIONS + 1)]

    def intent_entry(self, x: DS05Inputs) -> Optional[RuleIntent]:
        prior = self.prior_week_rank(x)
        if self.entry_signal(x, prior):
            return RuleIntent(
                action="ENTER", reason_code=ENTRY_REASON_DS05,
                direction="LONG",
                detail={"eur_rank_now": x.eur_rank(),
                        "eur_rank_1w": prior,
                        "ret20_eur": str(x.ret20["EUR"]),
                        "ranks": {c: x.ranks()[c] for c in DS05_CURRENCIES}})
        return None

    def exit_signal(self, x: DS05Inputs) -> bool:
        return x.eur_rank() > DS05_EXIT_RANK_MAX

    def stop_level(self, fill_price: Decimal, x: DS05Inputs) -> Decimal:
        """STOP_K_ATR@1 with k=2: fill - 2x ATR14(signal bar)."""
        return fill_price - DS05_STOP_ATR_MULT * x.atr14_vehicle


def ret_over(series_dates: List[str], series_vals: Dict[str, Decimal],
             window: int, at_date: str) -> Optional[Decimal]:
    """window-session return of a per-session series at a date:
    v[T]/v[T-window] - 1 on the series' OWN calendar (PER_PANEL@1).
    None if either anchor is absent (fail-closed, never interpolated)."""
    try:
        i = series_dates.index(at_date)
    except ValueError:
        return None
    j = i - window
    if j < 0:
        return None
    a, b = series_vals[at_date], series_vals[series_dates[j]]
    if a is None or b in (None, 0) or b == 0:
        return None
    return a / b - 1


def inverse_ret_over(series_dates: List[str],
                     series_vals: Dict[str, Decimal], window: int,
                     at_date: str) -> Optional[Decimal]:
    """Value-of-currency-in-USD 20d return for USD-quoted pairs
    (INVERSE_RET@1): (1/P_T)/(1/P_{T-w}) - 1 = P_{T-w}/P_T - 1."""
    try:
        i = series_dates.index(at_date)
    except ValueError:
        return None
    j = i - window
    if j < 0:
        return None
    a, b = series_vals[at_date], series_vals[series_dates[j]]
    if not a or not b:
        return None
    return b / a - 1
