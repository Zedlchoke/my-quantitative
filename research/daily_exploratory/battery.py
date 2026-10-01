"""Exploratory battery engine for DAILY-EXPLORATORY-V1.

Executes the frozen 2-leg slate (DS-03 + DS-05) over LEARN + the 8
EXPLORATORY folds under the DECLARED cost kernel (tiers x1.0/1.5/2.0),
journaling every intent (journal_row@1 via the G9 writer, leak-clean:
performance fields live in the METRICS outputs, labeled
EXPLORATORY_DECLARED_COSTS — the journal carries bookkeeping only).

Frozen calendar (PLAN_DAILY_SUCCESSOR_DRAFT section 2):
    warmup 2020-10-02..2021-09-30 | LEARN 2021-10-01..2022-09-22
    | embargo 2022-09-23..2022-09-29 | 8 x 26w folds 2022-09-30..2026-09-24
    (fold-edge force-flat inherited; per-panel session calendars are the
    named holiday calendar — DECLARED-PANEL-CALENDAR@1).

Clock law: a decision at session S consumes bars through the previous
session (EIA bars: freshest with next_business_day(bar) <= S, OI-5 1bd
serving) and fills at the S bar open on the quoted side. Snapshots are
therefore ADDRESSED BY DECISION SESSION S (never by the consumed one).

Arms (10 identities / <=83 trial rows; dispatch enumeration):
    SLATE, B0_FLAT (0 rows), B1S_ALWAYS_ON, B2_EQUAL_WEIGHT,
    B3_BEST_SINGLE (LEARN-selected), LORO_EX_DS03, LORO_EX_DS05,
    STRESS15_{SLATE,B1S} (x1.5 governing), REPORT20_{SLATE,B1S} (x2.0
    reporting pair — one identity).

Declared battery conventions (labeled on every artifact):
    RISK_UNIT_100USD@1 — each entry risks 100.00 USD at its stop
    distance (units = risk_quote / (k x ATR14(signal bar)), risk_quote
    converted at the CONSUMED bar close rate — no sizing look-ahead).
    B2 splits the SLATE's realized per-decision total risk equally
    across active legs (degenerate == SLATE at this 2-leg slate with
    symmetric per-leg risk; disclosed in the report).
    STOP_K_ATR@1 / DAILY-CLOCK-STOP@1 — stop = fill - k x ATR14(signal
    bar); breach detected on the D1 mid low of the held session; exit
    filled at the next session open.
    FRESHNESS_1BD_TOLERANCE@1 — an input bar is consumable at decision
    session S iff it is the FRESHEST bar with next_business_day(bar) <= S
    AND next_business_day(bar) >= previous business day of S (source
    holidays typed fresh, disclosed; longer gaps BLOCKED_STALE).
    SWAP_CONV_CLOSE_MID@1 — each swap accrual event converts at its
    owning session's close mid; fills convert at the fill bar open mid.
    FORCE_FLAT_LAST_BAR_OPEN@1 — fold-edge force-flat fills at the last
    available session's open; entry intents that would fill at the last
    session open are blocked (UNAVAILABLE_FILL_BAR — no holdable
    session remains in the window).
    EXPLORATORY-ONLY — no PASS of any kind is computed here; every PnL
    field carries EXPLORATORY_DECLARED_COSTS.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import datainputs as di
from . import rules
from .costkernel import (BUY, SELL, DailyBar, DeclaredCostKernel,
                         QUOTE_CCY_OF)
from .journal import (DailyJournalWriter, next_business_day,
                      OUTCOME_BLOCKED_FLOOR, OUTCOME_BLOCKED_STALE,
                      OUTCOME_FILLED, OUTCOME_UNAVAILABLE_FILL_BAR)
from .quoteccy import QuoteCcyBook

CYCLE_ID = "DAILY-EXPLORATORY-V1"
EXPLORATORY_LABEL = "EXPLORATORY_DECLARED_COSTS"
EXPLORATORY_ONLY_HEADER = (
    "EXPLORATORY-ONLY under DECLARED costs (x1.0/1.5/2.0). No edge "
    "claim; NO after-cost PASS is readable from this battery (OI-2 "
    "statement NOT_RUN); validation = prospective surface only "
    "(post-registration accumulation, earliest honest ~2029-09).")

WARMUP = ("2020-10-02", "2021-09-30")
LEARN = ("2021-10-01", "2022-09-22")
EMBARGO = ("2022-09-23", "2022-09-29")
FOLDS: List[Tuple[int, str, str]] = [
    (1, "2022-09-30", "2023-03-30"),
    (2, "2023-03-31", "2023-09-28"),
    (3, "2023-09-29", "2024-03-28"),
    (4, "2024-03-29", "2024-09-26"),
    (5, "2024-09-27", "2025-03-27"),
    (6, "2025-03-28", "2025-09-25"),
    (7, "2025-09-26", "2026-03-26"),
    (8, "2026-03-27", "2026-09-24"),
]

#: Trial floors (dispatch): >=20 fires full window per leg, >=3 per fold
#: (leg FLAT in failing folds, typed NOT_RUN_THIN), >=100 aggregate.
FLOOR_FULL_WINDOW = 20
FLOOR_PER_FOLD = 3
FLOOR_AGGREGATE = 100

RISK_UNIT_USD = Decimal("100")
OPENING_USD = Decimal("100000")
DS03_GRID_NODE_DEFAULT = rules.DS03_GRID_DEFAULT


# ---------------------------------------------------------------------------
# Input panel assembly
# ---------------------------------------------------------------------------

@dataclass
class Panels:
    meta: Dict[str, object]
    eia_ng: Dict[str, Decimal]
    eia_br: Dict[str, Decimal]
    ng_dates: List[str]
    br_dates: List[str]
    d1: Dict[str, Dict[str, di.D1Bar]]
    session_dates: Dict[str, List[str]]
    anc_closes: Dict[str, Dict[str, Tuple[float, float]]]


def build_panels(cache_dir: Optional[Path] = None,
                 use_cache: bool = True) -> Panels:
    """Load + verify every frozen input; assemble D1 panels."""
    cache = Path(cache_dir) if cache_dir else None
    d1_cache = cache / "d1_panels_cache.json" if cache else None
    if use_cache and d1_cache is not None and d1_cache.exists():
        blob = json.loads(d1_cache.read_text())
        d1 = {inst: {d: di.D1Bar(**row) for d, row in rows.items()}
              for inst, rows in blob["d1"].items()}
        anc = {inst: {d: tuple(v) for d, v in rows.items()}
               for inst, rows in blob["anc_closes"].items()}
        return Panels(meta=blob["meta"],
                      eia_ng={k: Decimal(v) for k, v in blob["eia_ng"].items()},
                      eia_br={k: Decimal(v) for k, v in blob["eia_br"].items()},
                      ng_dates=blob["ng_dates"], br_dates=blob["br_dates"],
                      d1=d1, session_dates={i: sorted(r) for i, r in d1.items()},
                      anc_closes=anc)

    ng, ng_meta = di.load_eia("RNGWHHD")
    br, br_meta = di.load_eia("RBRTE")
    nzd, nzd_meta = di.load_ibkr_panel("NZDUSD")
    chf, chf_meta = di.load_ibkr_panel("USDCHF")
    aud_g6, audg6_meta = di.load_g6_panel("AUDUSD")
    cad_g6, cadg6_meta = di.load_g6_panel("USDCAD")
    aud_anc, aud_anc_meta, _ = di.load_anc_d1_closes("AUDUSD")
    cad_anc, cad_anc_meta, _ = di.load_anc_d1_closes("USDCAD")

    d1: Dict[str, Dict[str, di.D1Bar]] = {}
    m1_meta = {}
    for pair in ("EURUSD", "GBPUSD", "USDJPY"):
        bars, meta = di.aggregate_m1_to_d1(pair)
        d1[pair] = bars
        m1_meta[pair] = meta

    anc_closes = {"AUDUSD": aud_anc, "USDCAD": cad_anc}
    d1["AUDUSD"] = dict(aud_g6)
    d1["USDCAD"] = dict(cad_g6)
    d1["NZDUSD"] = dict(nzd)
    d1["USDCHF"] = dict(chf)

    meta = {
        "cycle": CYCLE_ID,
        "label": "EXPLORATORY battery inputs (frozen, sha-verified)",
        "eia": {"RNGWHHD": ng_meta, "RBRTE": br_meta},
        "ibkr_panels": {"NZDUSD": nzd_meta, "USDCHF": chf_meta},
        "g6": {"AUDUSD": audg6_meta, "USDCAD": cadg6_meta},
        "anc": {"AUDUSD": aud_anc_meta, "USDCAD": cad_anc_meta},
        "m1_d1": m1_meta,
        "holiday_calendar": di.HOLIDAY_CALENDAR_NAME,
    }
    if d1_cache is not None:
        d1_cache.parent.mkdir(parents=True, exist_ok=True)
        d1_cache.write_text(json.dumps({
            "meta": meta,
            "eia_ng": {k: str(v) for k, v in ng.items()},
            "eia_br": {k: str(v) for k, v in br.items()},
            "ng_dates": sorted(ng), "br_dates": sorted(br),
            "anc_closes": {i: {d: list(v) for d, v in c.items()}
                           for i, c in anc_closes.items()},
            "d1": {i: {d: b.to_row() for d, b in bars.items()}
                   for i, bars in d1.items()},
        }))
    return Panels(meta=meta, eia_ng=ng, eia_br=br,
                  ng_dates=sorted(ng), br_dates=sorted(br),
                  d1=d1, session_dates={i: sorted(r) for i, r in d1.items()},
                  anc_closes=anc_closes)


# ---------------------------------------------------------------------------
# Per-panel signal series helpers
# ---------------------------------------------------------------------------

def close_series(inst: str, p: Panels) -> Tuple[List[str], Dict[str, Decimal]]:
    """Mid-close series per instrument (SIGNAL_MID_CLOSE@1).

    AUD/CAD pre-2026-07-01 from the ANC closes (H1 panel); G6 IBKR bars
    extend them (June venue seam adjudicated coherent, FREEZE.md item 3).
    """
    dates: List[str] = []
    vals: Dict[str, Decimal] = {}
    if inst in p.anc_closes:
        for d, (b, a) in sorted(p.anc_closes[inst].items()):
            dates.append(d)
            vals[d] = Decimal(str((b + a) / 2.0))
        for d in p.session_dates[inst]:        # G6 extension (later dates)
            if not dates or d > dates[-1]:
                dates.append(d)
                vals[d] = Decimal(str(p.d1[inst][d].mid_close))
        return dates, vals
    for d in p.session_dates[inst]:
        dates.append(d)
        vals[d] = Decimal(str(p.d1[inst][d].mid_close))
    return dates, vals


def atr14_wilder(bars: Dict[str, di.D1Bar], dates: List[str]
                 ) -> Dict[str, Decimal]:
    """Wilder ATR-14 on mid OHLC (ATR14_WILDER@1: RMA, SMA(14) seed)."""
    out: Dict[str, Decimal] = {}
    trs: List[Decimal] = []
    prev_close: Optional[Decimal] = None
    atr: Optional[Decimal] = None
    for d in dates:
        b = bars[d]
        h = Decimal(str(b.mid_high)); l = Decimal(str(b.mid_low))
        c = Decimal(str(b.mid_close))
        tr = (h - l) if prev_close is None else max(
            h - l, abs(h - prev_close), abs(l - prev_close))
        trs.append(tr)
        if len(trs) == rules.ATR_WINDOW:
            atr = sum(trs) / Decimal(rules.ATR_WINDOW)
        elif atr is not None:
            atr = (atr * Decimal(rules.ATR_WINDOW - 1) + tr) / Decimal(rules.ATR_WINDOW)
        if atr is not None:
            out[d] = atr
        prev_close = c
    return out


def _prev_business_day(iso: str) -> str:
    d = _dt.date.fromisoformat(iso) - _dt.timedelta(days=1)
    while d.weekday() >= 5:
        d -= _dt.timedelta(days=1)
    return d.isoformat()


def freshest_consumable(dates: List[str], decision: str) -> Optional[str]:
    """Freshest panel bar servable at the decision session
    (next_business_day(bar) <= decision); None if none."""
    best = None
    for d in dates:
        if d >= decision:
            break
        if next_business_day(d) <= decision:
            best = d
    return best


def age_ok(consumed: str, decision: str) -> bool:
    """FRESHNESS_1BD_TOLERANCE@1: serving day within one business day."""
    nbd = next_business_day(consumed)
    return nbd == decision or nbd == _prev_business_day(decision)


# ---------------------------------------------------------------------------
# Decision snapshots (addressed BY DECISION SESSION S)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Snapshot03:
    decision_session: str
    consumable: bool
    stale_inputs: List[str]
    prev_vehicle_bar: Optional[str]
    ng_ret10: Optional[Decimal] = None
    br_ret10: Optional[Decimal] = None
    atr: Optional[Decimal] = None
    ng_consumed: Optional[str] = None
    br_consumed: Optional[str] = None


@dataclass(frozen=True)
class Snapshot05:
    decision_session: str
    consumable: bool
    stale_inputs: List[str]
    prev_vehicle_bar: Optional[str]
    ret20: Dict[str, Decimal] = field(default_factory=dict)
    consumed: Dict[str, str] = field(default_factory=dict)
    atr: Optional[Decimal] = None
    eur_rank: Optional[int] = None


class LegContext:
    """Per-leg precomputed series + snapshot builder (shared by arms)."""

    def __init__(self, leg: str, p: Panels, grid_node: Optional[str] = None):
        self.leg = leg
        self.p = p
        self.grid_node = grid_node
        if leg == "DS-03":
            self.vehicle = "USDJPY"
            self.atr = atr14_wilder(p.d1["USDJPY"], p.session_dates["USDJPY"])
            self.rule: object = rules.DS03Rule()
            self.pair_series: Dict[str, Tuple] = {}
            self._sidx = {d: i for i, d in enumerate(p.session_dates["USDJPY"])}
        else:
            self.vehicle = "EURUSD"
            self.atr = atr14_wilder(p.d1["EURUSD"], p.session_dates["EURUSD"])
            self.rule = rules.DS05Rule()
            self.pair_series = {
                "EUR": close_series("EURUSD", p),
                "GBP": close_series("GBPUSD", p),
                "JPY": close_series("USDJPY", p),
                "AUD": close_series("AUDUSD", p),
                "CAD": close_series("USDCAD", p),
                "NZD": close_series("NZDUSD", p),
                "CHF": close_series("USDCHF", p),
            }
            self._sidx = {d: i for i, d in enumerate(p.session_dates["EURUSD"])}
        self._snap_cache: Dict[str, object] = {}

    def prev_vehicle_session(self, decision: str) -> Optional[str]:
        i = self._sidx.get(decision, 0)
        dates = self.p.session_dates[self.vehicle]
        return dates[i - 1] if i >= 1 else None

    def snapshot(self, decision: str):
        if decision in self._snap_cache:
            return self._snap_cache[decision]
        snap = (self.snapshot03(decision) if self.leg == "DS-03"
                else self.snapshot05(decision))
        self._snap_cache[decision] = snap
        return snap

    def snapshot03(self, decision: str) -> Snapshot03:
        prev_bar = self.prev_vehicle_session(decision)
        stale: List[str] = []
        ngT = freshest_consumable(self.p.ng_dates, decision)
        brT = freshest_consumable(self.p.br_dates, decision)
        ng_ret = br_ret = None
        ng_c = br_c = None
        if ngT is not None and age_ok(ngT, decision):
            ng_c = ngT
            ng_ret = rules.ret_over(self.p.ng_dates, self.p.eia_ng,
                                    rules.DS03_NG_WINDOW, ngT)
        else:
            stale.append("I-EIA-NG")
        if brT is not None and age_ok(brT, decision):
            br_c = brT
            br_ret = rules.ret_over(self.p.br_dates, self.p.eia_br,
                                    rules.DS03_BRENT_WINDOW, brT)
        else:
            stale.append("I-EIA-BR")
        atr = self.atr.get(prev_bar) if prev_bar else None
        if atr is None:
            stale.append("I-JPY")
        consumable = ng_ret is not None and br_ret is not None and atr is not None
        return Snapshot03(decision, consumable, sorted(set(stale)), prev_bar,
                          ng_ret, br_ret, atr, ng_c, br_c)

    def snapshot05(self, decision: str) -> Snapshot05:
        prev_bar = self.prev_vehicle_session(decision)
        stale: List[str] = []
        ret20: Dict[str, Decimal] = {}
        consumed: Dict[str, str] = {}
        for ccy in rules.DS05_CURRENCIES:
            dates, vals = self.pair_series[ccy]
            T = freshest_consumable(dates, decision)
            if T is None or not age_ok(T, decision):
                stale.append(f"I-{ccy}")
                continue
            if ccy in rules.DS05_USD_QUOTED:
                r = rules.inverse_ret_over(dates, vals,
                                           rules.DS05_RANK_WINDOW, T)
            else:
                r = rules.ret_over(dates, vals, rules.DS05_RANK_WINDOW, T)
            if r is None:
                stale.append(f"I-{ccy}")
                continue
            ret20[ccy] = r
            consumed[ccy] = T
        atr = self.atr.get(prev_bar) if prev_bar else None
        if atr is None:
            stale.append("I-EUR")
        consumable = (not stale) and len(ret20) == len(rules.DS05_CURRENCIES)
        eur_rank = None
        if consumable:
            x = rules.DS05Inputs(decision, ret20, atr)
            eur_rank = x.eur_rank()
        return Snapshot05(decision, consumable, sorted(set(stale)), prev_bar,
                          ret20, consumed, atr, eur_rank)


# ---------------------------------------------------------------------------
# Timestamps + journal row builders (G9 writer; bookkeeping only)
# ---------------------------------------------------------------------------

def _session_open_utc(session_date: str) -> str:
    d = _dt.date.fromisoformat(session_date) - _dt.timedelta(days=1)
    t = _dt.datetime.combine(d, _dt.time(17, 0), tzinfo=di.ET)
    return t.astimezone(_dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _session_close_utc(session_date: str) -> str:
    t = _dt.datetime.combine(_dt.date.fromisoformat(session_date),
                             _dt.time(17, 0), tzinfo=di.ET)
    return t.astimezone(_dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _pit_entry(input_id: str, consumed: str, value) -> Dict[str, object]:
    return {
        "input_id": input_id,
        "consumed_bar_date": consumed,
        "available_time_utc": f"{next_business_day(consumed)}T00:00:00Z",
        "value_digest": hashlib.sha256(str(value).encode()).hexdigest()[:16],
        "max_age_ok": True,
    }


def _pit_entry_stale(input_id: str, newest: Optional[str]) -> Dict[str, object]:
    consumed = newest or "1970-01-01"
    return {
        "input_id": input_id,
        "consumed_bar_date": consumed,
        "available_time_utc": f"{next_business_day(consumed)}T00:00:00Z",
        "value_digest": "UNAVAILABLE",
        "max_age_ok": False,
    }


def _decision_block(ctx: LegContext, decision: str, snap, direction: str,
                    risk_units: Optional[Decimal], reason: str,
                    window_id: str, tier: float) -> Dict[str, object]:
    if ctx.leg == "DS-03":
        fam = rules.DS03Rule.family_id
        mech = rules.DS03Rule.mech_key
        symbol = "USDJPY"
        if snap.consumable:
            pit = [
                _pit_entry("I-EIA-NG", snap.ng_consumed, snap.ng_ret10),
                _pit_entry("I-EIA-BR", snap.br_consumed, snap.br_ret10),
                _pit_entry("I-JPY", snap.prev_vehicle_bar, snap.atr),
            ]
        else:
            pit = [
                _pit_entry_stale("I-EIA-NG",
                                 freshest_consumable(ctx.p.ng_dates, decision)),
                _pit_entry_stale("I-EIA-BR",
                                 freshest_consumable(ctx.p.br_dates, decision)),
                _pit_entry("I-JPY", snap.prev_vehicle_bar or "1970-01-01",
                           snap.atr),
            ]
    else:
        fam = rules.DS05Rule.family_id
        mech = rules.DS05Rule.mech_key
        symbol = "EURUSD"
        pit = []
        for ccy in rules.DS05_CURRENCIES:
            if ccy in snap.consumed:
                pit.append(_pit_entry(f"I-{ccy}", snap.consumed[ccy],
                                      snap.ret20[ccy]))
            else:
                dates, _ = ctx.pair_series[ccy]
                pit.append(_pit_entry_stale(
                    f"I-{ccy}", freshest_consumable(dates, decision)))
        pit.append(_pit_entry("I-EUR", snap.prev_vehicle_bar or "1970-01-01",
                              snap.atr))
    return {
        "ts_decision_utc": _session_open_utc(decision),
        "window_id": window_id,
        "fold_id": window_id,
        "cycle_id": CYCLE_ID,
        "sleeve_id": ctx.leg,
        "corpus_gid": (rules.DS03Rule.corpus_gid if ctx.leg == "DS-03"
                       else rules.DS05Rule.corpus_gid),
        "symbol": symbol,
        "family_id": fam,
        "mech_key": mech,
        "feature_pit_snapshot": pit,
        "direction_vote": direction,
        "desired_risk_units": float(risk_units) if risk_units else 0.0,
        "entry_reason_code": reason,
        "eligibility_state": "ALWAYS_ON",
        "arm_label": "EXPLORATORY",
        "costs_label": EXPLORATORY_LABEL,
        "tier": tier,
        "ds03_grid_node": ctx.grid_node,
    }


# ---------------------------------------------------------------------------
# Leg simulation
# ---------------------------------------------------------------------------

@dataclass
class Position:
    units: Decimal
    entry_fill_price: Decimal
    stop_level: Decimal
    entry_session: str
    entry_idx: int
    held_sessions: int
    entry_reason: str
    entry_ts: str
    entry_cost_quote: Decimal = Decimal(0)   # spread+slip+commission at entry
    entry_conv_rate: Decimal = Decimal(1)


@dataclass
class LegResult:
    leg: str
    vehicle: str
    trades: List[Dict[str, object]] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)
    books: Dict[str, QuoteCcyBook] = field(default_factory=dict)


def _swap_events(kernel: DeclaredCostKernel, start_ts: str, end_ts: str
                 ) -> List[Tuple[str, int, bool]]:
    s = _dt.datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
    e = _dt.datetime.fromisoformat(end_ts.replace("Z", "+00:00"))
    return [(ts.isoformat().replace("+00:00", "Z"), m, w)
            for ts, m, w in kernel.iter_swap_events(s, e)]


def run_leg(ctx: LegContext, lo: str, hi: str, window_id: str, tier: float,
            journal: Optional[DailyJournalWriter], floor_blocked: bool,
            risk_usd: Decimal = RISK_UNIT_USD,
            b2_split: Optional[Dict[str, Decimal]] = None,
            ) -> LegResult:
    """Simulate one leg over [lo, hi] on its own vehicle sessions."""
    sessions = [s for s in ctx.p.session_dates[ctx.vehicle] if lo <= s <= hi]
    res = LegResult(ctx.leg, ctx.vehicle)
    if not sessions:
        res.counts["sessions"] = 0
        return res
    res.counts["sessions"] = len(sessions)
    kernel = DeclaredCostKernel(ctx.vehicle, tier=tier)
    first_prev = ctx.prev_vehicle_session(sessions[0])
    open_rate = (Decimal(1) if ctx.vehicle != "USDJPY"
                 else _inv(ctx.p.d1["USDJPY"][first_prev].mid_close)
                 if first_prev and first_prev in ctx.p.d1["USDJPY"]
                 else _inv(ctx.p.d1["USDJPY"][sessions[0]].mid_open))
    book = QuoteCcyBook(ctx.vehicle, kernel, str(OPENING_USD),
                        _session_open_utc(sessions[0]), open_rate)
    res.books[ctx.vehicle] = book
    pos: Optional[Position] = None
    pending: Optional[Tuple[str, object, str]] = None
    order_seq = 0

    def conv_open(sess: str) -> Decimal:
        if ctx.vehicle != "USDJPY":
            return Decimal(1)
        return _inv(ctx.p.d1["USDJPY"][sess].mid_open)

    def conv_close(sess: str) -> Decimal:
        if ctx.vehicle != "USDJPY":
            return Decimal(1)
        return _inv(ctx.p.d1["USDJPY"][sess].mid_close)

    def accrue_and_journal_swaps(pr: Position, end_ts: str
                                 ) -> Tuple[List[Dict[str, object]],
                                            Decimal]:
        """Accrue swap events (entry, exit-fill] at the owning session's
        close-mid rate (SWAP_CONV_CLOSE_MID@1); explicit units_abs so the
        zero book after the exit fill cannot suppress the accrual."""
        rows: List[Dict[str, object]] = []
        total = Decimal(0)
        for ev_ts, mult, wed in _swap_events(kernel, pr.entry_ts, end_ts):
            rate = (conv_close(ev_ts[:10]) if ev_ts[:10] in ctx._sidx
                    else conv_close(sessions[0]))
            rec = book.accrue_swap(ev_ts, mult, rate, units_abs=pr.units)
            if rec is None:
                continue
            total += rec.charge_quote
            rows.append({
                "accrual_ts": ev_ts, "multiplier": mult, "wed_x3": wed,
                "quote_amount": float(rec.charge_quote),
                "rate_to_usd": float(rate),
                "usd_amount": float(rec.charge_quote * rate)})
        return rows, total

    def journal_fill(decision: str, snap, kind: str, fq, rate: Decimal,
                     reason: str, pr: Optional[Position],
                     swaps: Optional[List[Dict[str, object]]]) -> None:
        nonlocal order_seq
        order_seq += 1
        base = _decision_block(ctx, decision, snap,
                               "LONG" if kind == "OPEN" else "EXIT",
                               (pr.units if kind == "CLOSE" else fq.units_delta),
                               reason, window_id, tier)
        units_abs = abs(fq.units_delta)
        spread_unit = fq.spread_once_total / units_abs
        slip_unit = fq.slip_beyond_total / units_abs
        base.update({
            "record_kind": "TRADE_ROW", "outcome": OUTCOME_FILLED,
            "order_id": f"{ctx.leg}-{window_id}-{order_seq:04d}",
            "order_kind": kind,
            "ts_fill_utc": fq.ts,
            "fill_price": float(fq.fill_price),
            "fill_side_quote": ("ask" if fq.side == BUY else "bid"),
            "spread_pips_charged": float(spread_unit / kernel.pip_size),
            "slippage_beyond_spread": float(slip_unit / kernel.pip_size),
            "venue_model": "DUKA_M1_D1AGG_DECLARED@1",
            "commission": float(fq.commission),
            "swap_financing": swaps,
            "cash_delta_quoteccy": float(fq.cash_delta_quote),
            "cash_delta_usd": float(fq.cash_delta_quote * rate),
            "fx_conversion": {
                "quote_ccy": QUOTE_CCY_OF[ctx.vehicle],
                "rate_to_usd": float(rate),
                "rate_source_ts": fq.ts,
                "convention": "REALIZATION_SAME_BAR@1"},
            "quoted_side_price": float(
                fq.mid_at_fill + (spread_unit if fq.side == BUY
                                  else -spread_unit)),
            "mid_at_fill": float(fq.mid_at_fill),
        })
        if kind == "CLOSE" and pr is not None:
            base["exit_reason_code"] = reason
            base["hold_bars"] = pr.held_sessions
        else:
            base["entry_reason_code"] = reason
        journal and journal.write_row(base)

    for i, sess in enumerate(sessions):
        bar = ctx.p.d1[ctx.vehicle][sess]
        dbar = DailyBar(sess, bar.bid_open, bar.ask_open,
                        bar.bid_close, bar.ask_close)
        last = (i == len(sessions) - 1)

        # ---- (a) pending exit fills at the open --------------------------
        if pending and pending[0] == "EXIT" and pos is not None:
            reason, snap = pending[2], pending[1]
            rate = conv_open(sess)
            fq = book.apply_fill(_session_open_utc(sess), dbar, SELL,
                                 pos.units, rate, _session_open_utc(sess))
            swaps, swap_total = accrue_and_journal_swaps(pos, fq.ts)
            journal_fill(sess, snap, "CLOSE", fq, rate, reason, pos, swaps)
            gross = pos.units * (fq.fill_price - pos.entry_fill_price)
            exit_cost = (fq.spread_once_total + fq.slip_beyond_total
                         + fq.commission)
            res.trades.append(_trade_rec(ctx, pos, fq.fill_price, sess,
                                         reason, swaps, gross, exit_cost,
                                         swap_total, rate, tier, window_id))
            res.counts[f"exit_{reason}"] = res.counts.get(f"exit_{reason}", 0) + 1
            pos = None
            pending = None

        # ---- (b) fold-edge force-flat at the last session open -----------
        if pos is not None and last:
            reason = rules.EXIT_REASON_FOLD_EDGE
            snap = ctx.snapshot(sessions[i - 1]) if i >= 1 else snap
            rate = conv_open(sess)
            fq = book.apply_fill(_session_open_utc(sess), dbar, SELL,
                                 pos.units, rate, _session_open_utc(sess))
            swaps, swap_total = accrue_and_journal_swaps(pos, fq.ts)
            journal_fill(sess, snap, "CLOSE", fq, rate, reason, pos, swaps)
            gross = pos.units * (fq.fill_price - pos.entry_fill_price)
            exit_cost = (fq.spread_once_total + fq.slip_beyond_total
                         + fq.commission)
            res.trades.append(_trade_rec(ctx, pos, fq.fill_price, sess,
                                         reason, swaps, gross, exit_cost,
                                         swap_total, rate, tier, window_id))
            res.counts["exit_FOLD_EDGE_FORCE_FLAT"] = \
                res.counts.get("exit_FOLD_EDGE_FORCE_FLAT", 0) + 1
            pos = None

        # ---- (c) pending entry fills at the open -------------------------
        if pending and pending[0] == "ENTER" and pos is None:
            snap, reason = pending[1], pending[2]
            if last:
                journal and journal.write_row(_decision_block(
                    ctx, sess, snap, "LONG", None, reason, window_id, tier) | {
                    "record_kind": "BLOCKED_ROW",
                    "outcome": OUTCOME_UNAVAILABLE_FILL_BAR,
                    "blocked_reason_detail":
                        "FOLD_EDGE: fill session is the window's last "
                        "session; no holdable session remains "
                        "(FORCE_FLAT_LAST_BAR_OPEN@1)",
                })
                res.counts["blocked_fold_edge_entry"] = \
                    res.counts.get("blocked_fold_edge_entry", 0) + 1
            elif floor_blocked:
                journal and journal.write_row(_decision_block(
                    ctx, sess, snap, "LONG", None, reason, window_id, tier) | {
                    "record_kind": "BLOCKED_ROW",
                    "outcome": OUTCOME_BLOCKED_FLOOR,
                    "blocked_reason_detail":
                        "NOT_RUN_THIN: leg below the per-fold decision floor "
                        f"(>={FLOOR_PER_FOLD}); leg FLAT for this fold",
                })
                res.counts["blocked_floor"] = \
                    res.counts.get("blocked_floor", 0) + 1
            else:
                k = (rules.DS03_STOP_ATR_MULT if ctx.leg == "DS-03"
                     else rules.DS05_STOP_ATR_MULT)
                stop_dist = k * snap.atr
                # sizing at the CONSUMED bar close rate (no look-ahead)
                rate_dec = (Decimal(1) if ctx.vehicle != "USDJPY"
                            else _inv(ctx.p.d1["USDJPY"][snap.prev_vehicle_bar]
                                      .mid_close))
                eff_risk = (b2_split.get(sess, risk_usd)
                            if b2_split is not None else risk_usd)
                risk_quote = eff_risk / rate_dec
                units = risk_quote / stop_dist
                rate = conv_open(sess)
                fq = book.apply_fill(_session_open_utc(sess), dbar, BUY,
                                     units, rate, _session_open_utc(sess))
                stop_level = fq.fill_price - stop_dist
                entry_cost = (fq.spread_once_total + fq.slip_beyond_total
                              + fq.commission)
                pos = Position(units, fq.fill_price, stop_level, sess, i, 0,
                               reason, fq.ts, entry_cost, rate)
                journal_fill(sess, snap, "OPEN", fq, rate, reason, None, None)
                res.counts["entries_filled"] = \
                    res.counts.get("entries_filled", 0) + 1
            pending = None

        # ---- equity mark at the session close ----------------------------
        book.mark(_session_close_utc(sess), bar.mid_close, conv_close(sess),
                  _session_close_utc(sess))

        # ---- close-of-session evaluation (decision = NEXT session) -------
        if last:
            break
        nxt = sessions[i + 1]
        snap = ctx.snapshot(nxt)

        if pos is not None:
            pos.held_sessions += 1
            if Decimal(str(bar.mid_low)) <= pos.stop_level:
                pending = ("EXIT", snap, rules.EXIT_REASON_STOP)
            elif ctx.leg == "DS-03":
                if pos.held_sessions >= rules.DS03_HOLD_SESSIONS:
                    pending = ("EXIT", snap, rules.EXIT_REASON_HOLD)
            else:
                if snap.consumable and snap.eur_rank is not None:
                    if snap.eur_rank > rules.DS05_EXIT_RANK_MAX:
                        pending = ("EXIT", snap, rules.EXIT_REASON_RANK)
                else:
                    journal and journal.write_row(_decision_block(
                        ctx, nxt, snap, "EXIT", pos.units,
                        rules.EXIT_REASON_RANK, window_id, tier) | {
                        "record_kind": "BLOCKED_ROW",
                        "outcome": OUTCOME_BLOCKED_STALE,
                        "blocked_reason_detail":
                            "exit evaluation inputs stale: "
                            f"{snap.stale_inputs} (FRESHNESS_1BD_TOLERANCE@1)"
                            "; position held until a fresh exit or the "
                            "fold-edge force-flat",
                    })
                    res.counts["blocked_stale_exit"] = \
                        res.counts.get("blocked_stale_exit", 0) + 1
        else:
            if not snap.consumable:
                journal and journal.write_row(_decision_block(
                    ctx, nxt, snap, "LONG", None, "SIGNAL_EVALUATION",
                    window_id, tier) | {
                    "record_kind": "BLOCKED_ROW",
                    "outcome": OUTCOME_BLOCKED_STALE,
                    "blocked_reason_detail":
                        "entry evaluation inputs stale: "
                        f"{snap.stale_inputs} (FRESHNESS_1BD_TOLERANCE@1)",
                })
                res.counts["blocked_stale_signal"] = \
                    res.counts.get("blocked_stale_signal", 0) + 1
            elif ctx.leg == "DS-03":
                x = rules.DS03Inputs(snap.prev_vehicle_bar or sess,
                                     snap.ng_ret10, snap.br_ret10, snap.atr)
                intent = ctx.rule.intent_entry(
                    x, ctx.grid_node or DS03_GRID_NODE_DEFAULT)
                if intent:
                    res.counts["entry_fires"] = \
                        res.counts.get("entry_fires", 0) + 1
                    pending = ("ENTER", snap, intent.reason_code)
            else:
                hist = _eur_rank_history(ctx, sessions, i)
                x = rules.DS05Inputs(snap.prev_vehicle_bar or sess,
                                     dict(snap.ret20), snap.atr,
                                     tuple(hist))
                intent = ctx.rule.intent_entry(x)
                if intent:
                    res.counts["entry_fires"] = \
                        res.counts.get("entry_fires", 0) + 1
                    pending = ("ENTER", snap, intent.reason_code)

    res.counts.setdefault("entry_fires", 0)
    res.counts.setdefault("entries_filled", 0)
    return res


def _trade_rec(ctx: LegContext, pr: Position, exit_fill: Decimal,
               exit_session: str, reason: str,
               swaps: List[Dict[str, object]], gross_quote: Decimal,
               exit_cost_quote: Decimal, swap_total_quote: Decimal,
               conv_rate: Decimal, tier: float, window_id: str
               ) -> Dict[str, object]:
    cost_quote = pr.entry_cost_quote + exit_cost_quote + swap_total_quote
    net_quote = gross_quote - cost_quote
    return {
        "leg": ctx.leg, "vehicle": ctx.vehicle,
        "entry_session": pr.entry_session, "exit_session": exit_session,
        "units": float(pr.units), "entry_fill": float(pr.entry_fill_price),
        "exit_fill": float(exit_fill), "stop_level": float(pr.stop_level),
        "held_sessions": pr.held_sessions,
        "entry_reason": pr.entry_reason, "exit_reason": reason,
        "swap_events": len(swaps),
        "gross_quoteccy": float(gross_quote),
        "cost_quoteccy": float(cost_quote),
        "net_quoteccy": float(net_quote),
        "net_usd__EXPLORATORY_DECLARED_COSTS":
            float(net_quote * pr.entry_conv_rate),
        "gross_usd__EXPLORATORY_DECLARED_COSTS":
            float(gross_quote * pr.entry_conv_rate),
        "cost_usd__EXPLORATORY_DECLARED_COSTS":
            float(cost_quote * pr.entry_conv_rate),
        "conv_rate_note": "per-trade USD at the entry realization rate "
                          "(REALIZATION_SAME_BAR@1)",
        "label": EXPLORATORY_LABEL, "tier": tier,
        "window_id": window_id, "sleeve_id": ctx.leg,
    }


def _inv(px: float) -> Decimal:
    return Decimal(1) / Decimal(str(px))


def _eur_rank_history(ctx: LegContext, sessions: List[str], i: int
                      ) -> List[int]:
    """EUR rank series (oldest..newest) over the trailing 6 DECISION
    sessions ending at the current next session — supplies the 2-week
    consistency lookback (rank at D and at D-5 sessions)."""
    nxt = i + 1
    hist: List[int] = []
    for j in range(max(0, nxt - rules.DS05_CONSISTENCY_SESSIONS), nxt + 1):
        snap = ctx.snapshot(sessions[j])
        hist.append(snap.eur_rank if snap.eur_rank is not None else 99)
    return hist
