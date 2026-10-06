"""Deterministic daily replay engine (offline, prep-grade).

Single symbol per engine; one position at a time; front-chain trading with
the declared roll baseline. All prices are RAW per-contract prices — the
adjusted continuous series is for features only and is never used for fills,
MTM, or PnL.

Execution model (declared, default):
  * strategy decides at the CLOSE of session t through a PITDataView pinned
    at t (any attempt to read > t raises FutureAccessError);
  * entry fills at the OPEN of session t+1 ('next_open', default) — or at
    the close of t if fill_timing='same_close', which stamps every record
    with OPTIMISTIC_SAME_CLOSE;
  * while open, TP/SL are evaluated intrabar against each session's
    high/low. Both touched in one bar -> AMBIGUOUS_ORDER (see journal.py);
    the ledger books the deterministic worst-case bound, the journal keeps
    both bounds and NO point PnL;
  * EXEC-FIX R3 (2026-10-02): barriers are evaluated on the OLD
    position/contract BEFORE the end-of-session roll, against that bar's
    own extrema only; a stopped position never rolls, old extrema are
    never mixed with the gap-rebased levels/entry of the new contract,
    and the new position's bars only count from AFTER the roll fill;
  * EXEC-FIX R4 (2026-10-02): SL is a stop-MARKET order — when the bar
    opens beyond the barrier the fill reference is the OPEN (long stop:
    min(open, sl); short stop: max(open, sl)) and the adverse cost shift
    is applied afterwards, so a long stop can never fill above the open.
    TP is a LIMIT — fills at the barrier or better (long TP sell:
    max(open, tp); short TP buy: min(open, tp)). Same-bar TP+SL stays
    AMBIGUOUS_ORDER with gap-aware bounds; the order is NEVER inferred
    from OHLC alone;
  * a roll decision session rolls any open position at that close
    (sell old / buy new at raw closes, costs on both legs); TP/SL are
    rebased by the raw gap so economic distances survive the roll;
  * hard expiry constraint: the engine never holds a contract after its
    roll date (auto-roll), and force-exits (FORCED_ROLL) if no next
    contract exists — expired/first-notice walls are never crossed.

CLOSE-ONLY FILL LAW (unconditional, audit M3 fix 2026-10-02): close-only
bars (o=h=l=c, v=0 — settlement-derived) can NEVER fill, on ANY path:
  * pending entries on a close-only bar lapse (ORDER_LAPSED_CLOSE_ONLY_BAR);
  * TP/SL (incl. same-bar ambiguity) evaluate only against a real high/low
    — never on close-only bars (the settlement close is not an intrabar
    touch, and a stop beyond it must not "fill" at a settlement price);
  * TIME and MANUAL exits wait for the next tradeable session (deferral
    recorded in notes; MANUAL converts to a pending exit filled at the
    next tradeable OPEN);
  * roll legs execute on the first session (>= the scheduled roll session)
    where BOTH old and new bars are tradeable; if no next-contract price
    exists on the scheduled session the position force-exits at the old
    close (FORCED_ROLL, still only on a tradeable bar); a roll that never
    finds a tradeable pair leaves the record right-censored with the roll
    marked unexecuted.
journal.FillRecord enforces the law structurally (is_close_only_bar=True
is refused), and tests/test_engine.py::TestCloseOnlyNeverFills proves it.

Determinism: same inputs -> byte-identical journal JSON. The engine exposes
truncation (run through cutoff) and future-mutation (data after cutoff
replaced by seeded garbage) so tests can prove decisions at t never depend
on data > t.

EXEC-FIX round co-owner-review-fix-1 (2026-10-02) additional laws:
  * R1 — cost law: allow_incomplete_costs covers ALL cost components
    (commission, exchange fee, slippage, any others). When incomplete is
    allowed, KNOWN fees are deducted (quantity-scaled: the base engine
    dropped the order size and charged qty-1 commissions, and zeroed ALL
    fees whenever one commission component was missing) and missing
    components are recorded as NULL with their source class — never a
    fabricated 0, never MEASURED. When allow_incomplete_costs=False and
    the book is incomplete the engine refuses at construction.
  * R2 — lifecycle accounting: every contract segment (roll old legs and
    the final exit) accumulates into the journal record's gross PnL; the
    ledger is reconciled every bar AND at end-of-run against an
    INDEPENDENT cash accounting recomputed from journal records (never
    against its own event log alone).
  * finite-OHLC validation: every bar of every contract (chain bars and
    the per-conid bars used for deferred rolls / held-contract marks) is
    validated at construction: all OHLCV finite, h >= l, o and c inside
    [l, h] — rawdata.Bar.validate only checks h >= l.

MULTIASSET-WIRING round steering-waiting-databento (2026-10-02), portfolio
laws (PortfolioEngine below; single-symbol BacktestEngine.run behavior is
UNCHANGED — its loop body now lives in the steppable _Replay so the
portfolio layer can drive many symbols in session lockstep):
  * lockstep replay: sessions = sorted union of the member calendars; each
    session steps every symbol that has a bar, in SORTED symbol order —
    deterministic by construction (later symbols' fill-time margin checks
    see earlier symbols' same-session fills; same-close decisions of one
    symbol never feed another symbol's same-close decision);
  * portfolio state: one net signed quantity per symbol, on the symbol's
    CURRENT chain contract (rolls move the net qty to the next contract;
    positions are marked on the HELD contract's bars, not the chain front);
  * USD cash aggregation: portfolio cash = sum of member ledgers (all
    USD); asserted EVERY session against an independent recomputation
    from the ledger event logs;
  * per-bar portfolio MTM: open positions marked at the held contract's
    latest close <= t (settlement closes are legal MARKS; fills never are)
    — equity = cash + MTM; drawdown = equity - running peak;
  * margin aggregation vs the risk-cap interface: MarginModel.check over
    the aggregated book (per-session requirement + utilization recorded);
  * portfolio risk caps are enforced ONLY as VETO / blocked-signal
    JOURNAL ENTRIES (decision-time structural caps; fill-time margin
    admission). Quantities are NEVER silently clipped, rescaled or
    dropped — composition.PortfolioRiskCaps.enforce_veto is the wired
    path; the legacy clip-mode enforce() is analysis-only;
  * lookahead: the gate and the series only ever read sessions <= t;
    portfolio-level cutoff + future-mutation hooks prove it (mutating
    every symbol's post-cutoff bars cannot change any decision, journal
    record or series value at or before the cutoff).
"""
from __future__ import annotations

import datetime as dt
import json
import math
import random
from dataclasses import dataclass, field

from .accounting import (CashLedger, MarginModel, Position,
                         check_price_plausible, pnl, round_to_tick)
from .costs import CostBook
from .instruments import get_instrument
from .journal import (FillRecord, JournalRecord, OrderRecord, RollEvent,
                      TradeJournal, validate_feature_snapshot)
from .roll import RollEngine, RollTable
from .taxonomy import PolicyError


class FutureAccessError(PolicyError):
    pass


class MissingBarError(KeyError):
    pass


def _validate_ohlc(symbol: str, local_symbol: str, t: dt.date,
                   o: float, h: float, l: float, c: float, v: float) -> None:
    """Finite-OHLC validation (EXEC-FIX review-extra, 2026-10-02). A bar
    the engine can execute or mark against must be internally consistent:
    all fields finite, h >= l, o and c inside [l, h]. rawdata.Bar.validate
    only checks h >= l, so an o=105/h=101/l=99 bar would otherwise feed
    barriers, fills and MAE/MFE impossible extrema."""
    for name, val in (("o", o), ("h", h), ("l", l), ("c", c), ("v", v)):
        if not math.isfinite(val):
            raise PolicyError(
                f"{symbol} {local_symbol} {t}: bar field {name}={val} is "
                "not finite — garbage bar refused")
    if h < l:
        raise PolicyError(
            f"{symbol} {local_symbol} {t}: h={h} < l={l} — invalid bar")
    for name, val in (("o", o), ("c", c)):
        if not (l <= val <= h):
            raise PolicyError(
                f"{symbol} {local_symbol} {t}: {name}={val} outside "
                f"[l,h]=[{l},{h}] — invalid OHLC (open/close must lie "
                "inside the bar's range)")


@dataclass(frozen=True)
class ChainBar:
    session: dt.date
    local_symbol: str
    conid: int
    o: float
    h: float
    l: float
    c: float
    v: float
    is_close_only: bool


class PITDataView:
    """Point-in-time window over the raw front chain; pinned at `asof`."""

    def __init__(self, chain: dict[dt.date, ChainBar], asof: dt.date):
        self._chain = chain
        self.asof = asof

    def _check(self, d: dt.date) -> None:
        if d > self.asof:
            raise FutureAccessError(
                f"strategy requested {d} but is pinned at {self.asof}; "
                "future information is not available at decision time")

    def has(self, d: dt.date) -> bool:
        self._check(d)
        return d in self._chain

    def bar(self, d: dt.date) -> ChainBar:
        self._check(d)
        try:
            return self._chain[d]
        except KeyError:
            raise MissingBarError(f"no front-chain bar on {d}") from None

    def close(self, d: dt.date) -> float:
        return self.bar(d).c

    def closes(self, end: dt.date, lookback: int) -> list[float]:
        self._check(end)
        ds = sorted(d for d in self._chain if d <= end)
        return [self._chain[d].c for d in ds[-lookback:]]

    def sessions_available(self) -> list[dt.date]:
        return sorted(d for d in self._chain if d <= self.asof)


@dataclass
class Decision:
    action: str = "none"           # none | enter_long | enter_short | exit | veto
    qty: int = 1
    tp_price: float | None = None
    sl_price: float | None = None
    time_exit_sessions: int | None = None
    reason: str = ""
    features: dict = field(default_factory=dict)
    veto_reason: str | None = None


@dataclass
class EngineConfig:
    fill_timing: str = "next_open"     # 'next_open' | 'same_close'
    initial_cash_usd: float = 1_000_000.0
    ambiguous_booking: str = "worst_case"   # ledger booking for AMBIGUOUS_ORDER
    stress: float = 1.0
    force_roll_open_positions: bool = True
    allow_incomplete_costs: bool = True   # prep: True, stamps cost_incomplete
    seed: int = 0


EXIT_TYPES = ("TP", "SL", "TIME", "END_OF_DATA", "FORCED_ROLL", "MANUAL",
              "TP_SL_SAME_BAR")  # journal owns the canonical tuple; kept for
# reference by engine callers


class BacktestEngine:
    """Deterministic single-symbol daily replay over the raw front chain."""

    def __init__(self, symbol: str, roll_engine: RollEngine,
                 roll_table: RollTable, cost_book: CostBook,
                 config: EngineConfig | None = None):
        self.symbol = symbol
        self.spec = get_instrument(symbol)
        self.roll_engine = roll_engine
        self.roll_table = roll_table
        self.cost_book = cost_book.stressed_copy(
            config.stress if config else 1.0)
        self.cfg = config or EngineConfig()
        if self.cfg.fill_timing not in ("next_open", "same_close"):
            raise PolicyError("fill_timing must be next_open|same_close")
        if self.cfg.ambiguous_booking != "worst_case":
            raise PolicyError(
                "ambiguous_booking must be 'worst_case' (deterministic, "
                "conservative); never an invented hit order")
        # R1 preflight: the incomplete-cost law covers ALL components. A
        # refusal here is fail-fast — running with a fabricated-complete
        # book is forbidden even if no trade ever executes.
        missing = self.cost_book.missing_components()
        if missing and not self.cfg.allow_incomplete_costs:
            raise PolicyError(
                f"{symbol}: cost components {missing} are NOT_RUN while "
                "allow_incomplete_costs=False — running would fabricate a "
                "complete cost book; complete the book (declare_slippage + "
                "exchange fees) or allow incomplete costs (known fees "
                "deducted, missing components recorded as NULL with their "
                "source class)")
        held = roll_engine.held_contract_index_by_session(roll_table)
        self._chain: dict[dt.date, ChainBar] = {}
        bm = roll_engine.raw_chain(roll_table)
        # is_close_only flags per (conid, date); finite-OHLC validation of
        # EVERY bar of EVERY contract (chain bars and the per-conid bars
        # used by deferred rolls / held-contract marks)
        flat = {}
        for cd in roll_engine.contracts:
            for b in cd.daily_trades:
                _validate_ohlc(symbol, cd.identity.local_symbol, b.t,
                               b.o, b.h, b.l, b.c, b.v)
                flat[(cd.identity.conid, b.t)] = b.is_close_only
        # per-conid bar maps: needed when a roll is deferred past its
        # scheduled session (close-only fill law) and the held contract is
        # no longer the chain's front contract
        self._bars_by_conid: dict[int, dict[dt.date, object]] = {
            cd.identity.conid: {b.t: b for b in cd.daily_trades}
            for cd in roll_engine.contracts}
        self._close_only = flat
        for t, (ls, cid, ohlcv) in bm.items():
            self._chain[t] = ChainBar(
                session=t, local_symbol=ls, conid=cid,
                o=ohlcv["o"], h=ohlcv["h"], l=ohlcv["l"], c=ohlcv["c"],
                v=ohlcv["v"],
                is_close_only=flat.get((cid, t), False))
        self.sessions = sorted(self._chain)
        # roll decision sessions by conid
        self._roll_at: dict[int, dt.date] = {
            r.old_conid: r.decision_session for r in roll_table.rows}
        self._roll_row: dict[dt.date, object] = {
            r.decision_session: r for r in roll_table.rows}

    # ------------------------------------------------------------------ #
    def _make_replay(self, strategy, journal: TradeJournal,
                     chain: dict[dt.date, ChainBar]) -> "_Replay":
        """Fresh steppable replay over `chain` (MULTIASSET-WIRING 2026-10-02:
        run() and PortfolioEngine both build on this; the single-symbol
        behavior is byte-identical to the pre-refactor run())."""
        return _Replay(self, strategy, journal, chain)

    def run(self, strategy, journal: TradeJournal | None = None,
            cutoff: dt.date | None = None,
            data_after_cutoff_mutate_seed: int | None = None
            ) -> TradeJournal:
        """Replay. `strategy` is called as strategy(ctx) -> Decision with ctx
        carrying a PITDataView pinned at each session close.

        cutoff: run only sessions <= cutoff (truncation test hook).
        data_after_cutoff_mutate_seed: if set, bars AFTER cutoff are replaced
        by seeded garbage before the run (future-mutation test hook) —
        decisions at t <= cutoff must be unaffected.
        """
        chain = self._chain
        if cutoff is not None and data_after_cutoff_mutate_seed is not None:
            chain = self._mutate_future(cutoff, data_after_cutoff_mutate_seed)
        sessions = [s for s in self.sessions
                    if cutoff is None or s <= cutoff]
        journal = journal or TradeJournal(
            breakeven_tolerance_usd=0.0)  # engine default; strategies pass theirs
        replay = self._make_replay(strategy, journal, chain)
        for t in sessions:
            replay.step(t, gate=None)
        return replay.finalize(sessions)

    # ------------------------------------------------------------------ #
    def _session_ordinal(self, d: dt.date) -> int:
        try:
            return self.sessions.index(d)
        except ValueError:
            return len(self.sessions)

    def _mutate_future(self, cutoff: dt.date, seed: int
                       ) -> dict[dt.date, ChainBar]:
        """Replace bars strictly after cutoff with seeded garbage (test hook
        proving decisions at t <= cutoff cannot read the future)."""
        rng = random.Random(seed)
        out: dict[dt.date, ChainBar] = {}
        for d, b in self._chain.items():
            if d <= cutoff:
                out[d] = b
            else:
                c = rng.uniform(-500.0, 500.0)
                out[d] = ChainBar(
                    session=d, local_symbol=b.local_symbol, conid=b.conid,
                    o=c, h=c + rng.uniform(0, 10), l=c - rng.uniform(0, 10),
                    c=c, v=rng.uniform(0, 1e6), is_close_only=b.is_close_only)
        return out


class _Replay:
    """Steppable per-symbol replay (one session per step()).

    Extracted verbatim from BacktestEngine.run (MULTIASSET-WIRING
    2026-10-02) so PortfolioEngine can drive several symbols in session
    lockstep through an optional portfolio `gate`:

      * gate.admit_entry_fill(symbol, t, bar, signed_qty) -> denial|None is
        called BEFORE a pending entry fills at the open of t (portfolio
        margin admission). A denial BLOCKS the fill: the order dies and a
        blocked-signal journal record is filed (never a silent drop, never
        a partial/adjusted quantity);
      * gate.vet_entry_decision(symbol, t, decision) -> denial|None is
        called at the close of t for every entry decision BEFORE the order
        becomes pending (portfolio structural caps). A denial files a VETO
        journal record.

    With gate=None the replay is exactly the historical single-symbol run.
    """

    def __init__(self, engine: BacktestEngine, strategy,
                 journal: TradeJournal, chain: dict[dt.date, ChainBar]):
        self.eng = engine
        self.strategy = strategy
        self.journal = journal
        self.chain = chain
        ledger = CashLedger(self.eng.cfg.initial_cash_usd)
        self.ledger = ledger
        self.position: Position | None = None
        self.pending: OrderRecord | None = None
        self.pending_decision: Decision | None = None
        self.realized_gross = 0.0
        self.total_costs = 0.0
        self.n_trades = 0
        self.tp: float | None = None
        self.sl: float | None = None
        self.time_exit: int | None = None
        self.cur_rec: JournalRecord | None = None
        self.entry_session: dt.date | None = None
        # R2: lifecycle gross accumulated for the CURRENT open record
        # (roll old-leg segments + final exit segment)
        self.cur_gross = 0.0
        # R3: per-contract segment state for MAE/MFE (a segment runs from
        # the entry fill / roll fill until the next roll or the exit; bars
        # before the fill timestamp never count for a fresh segment)
        self.seg_mae = 0.0
        self.seg_mfe = 0.0
        self.seg_entry_px: float | None = None
        self.seg_conid: int | None = None
        self.seg_local: str | None = None
        self.seg_first_bar: dt.date | None = None
        self.seg_last_bar: dt.date | None = None
        self.n_recon_checks = 0
        # close-only fill law state (audit M3 fix, 2026-10-02)
        self.pending_roll = None        # roll row awaiting a tradeable bar pair
        self.roll_deferral_noted = False
        self.pending_exit = False       # manual exit awaiting a tradeable open
        self.time_exit_deferred = 0     # sessions the time exit waited

    # ---- cost choke point ------------------------------------------- #
    def exec_cost(self, side: int, ref_price: float, session: dt.date,
                  qty: int = 1, bar_is_close_only: bool = False
                  ) -> tuple[float, dict, float]:
        """Apply half-spread + declared slippage as a price shift and
        commissions as cash. Returns (fill_price, breakdown, cash_cost).

        EXEC-FIX R1 (2026-10-02): `qty` scales every cash commission
        component (the base engine charged qty-1 commissions for any
        order size), and the incomplete-cost law covers ALL cost
        components: known fees are ALWAYS deducted; missing components
        are disclosed as NULL with their source class — never zeroed,
        never fabricated, never upgraded to MEASURED.

        Close-only fill law: calling this for a close-only bar is a bug —
        every caller must have checked tradeability first (the flag makes
        the law explicit at the single choke point all fills pass)."""
        if bar_is_close_only:
            raise PolicyError(
                f"fill on {session}: close-only (settlement-derived) "
                "bars can never fill — entry, exits and roll legs alike")
        q = abs(int(qty))
        if q < 1:
            raise PolicyError(
                f"fill on {session}: qty {qty!r} — fills must carry a "
                "positive integer quantity")
        missing = self.eng.cost_book.missing_components()
        if missing and not self.eng.cfg.allow_incomplete_costs:
            raise PolicyError(
                f"{self.eng.symbol}: cost components {missing} are NOT_RUN "
                "and allow_incomplete_costs=False — fills are forbidden "
                "on an incomplete book (never fabricate a complete one)")
        adj = self.eng.cost_book.fill_adjustment_usd(side)
        price_shift = adj["total_usd"] / self.eng.spec.multiplier
        fp = round_to_tick(ref_price + side * price_shift,
                           self.eng.spec.min_tick,
                           mode="ceil" if side > 0 else "floor")
        check_price_plausible(self.eng.symbol, fp)
        comm = self.eng.cost_book.commission_cash_usd(q)
        breakdown = {
            "contracts": q,
            "price_shift_usd": adj["total_usd"],
            "price_shift_breakdown": adj,
            "commissions": comm,
            "missing_cost_components": list(missing),
            "missing_component_status":
                self.eng.cost_book.missing_component_status(),
            "cost_incomplete": bool(missing),
            "stress_level": self.eng.cfg.stress,
            "fill_timing": self.eng.cfg.fill_timing,
        }
        # known fees deducted even while other components are missing
        return fp, breakdown, comm["usd"]

    # ---- R2/R3 lifecycle segment + exit helpers --------------------- #
    def close_segment(self) -> None:
        """Close the current per-contract MAE/MFE segment into the
        open record (if any) and reset the segment state."""
        if self.cur_rec is None or self.seg_conid is None:
            return
        self.cur_rec.mae_mfe_segments.append({
            "conid": self.seg_conid,
            "local_symbol": self.seg_local,
            "avg_entry_price": self.seg_entry_px,
            "first_bar_session": (self.seg_first_bar.isoformat()
                                  if self.seg_first_bar else None),
            "last_bar_session": (self.seg_last_bar.isoformat()
                                 if self.seg_last_bar else None),
            "mae_usd": self.seg_mae,
            "mfe_usd": self.seg_mfe,
        })
        self.seg_conid = None
        self.seg_local = None
        self.seg_entry_px = None
        self.seg_first_bar = self.seg_last_bar = None
        self.seg_mae = self.seg_mfe = 0.0

    def start_segment(self, conid: int, local: str, entry_px: float) -> None:
        """Open a fresh segment. Bars BEFORE the segment's fill
        timestamp (e.g. the roll session's new-contract bar, whose
        high/low happened before the close-time roll fill) never count:
        seg_first_bar stays None until the first counted bar."""
        self.seg_conid, self.seg_local, self.seg_entry_px = conid, local, entry_px
        self.seg_first_bar = self.seg_last_bar = None
        self.seg_mae = self.seg_mfe = 0.0

    def book_exit(self, exit_fill: FillRecord, exit_type: str,
                  session: dt.date, leg_gross: float, cash_cost: float,
                  note: str | None = None,
                  scenario_bounds: dict | None = None,
                  booked_gross: float | None = None) -> None:
        """Single booking path for EVERY exit: books the final gross
        segment, closes the MAE/MFE segment, stamps the full lifecycle
        PnL (R2), resets position/roll state and files the record."""
        self.cur_rec.gross_segments.append({
            "session": session.isoformat(),
            "conid": exit_fill.conid,
            "local_symbol": exit_fill.local_symbol,
            "kind": ("exit_ambiguous_worst_case_booked"
                     if scenario_bounds is not None else "exit"),
            "gross_usd": leg_gross,
            "fill_price": exit_fill.price,
        })
        self.cur_gross += leg_gross
        self.close_segment()
        self.cur_rec.exit_fill = exit_fill
        self.cur_rec.exit_type = exit_type
        self.cur_rec.exit_session = session
        if scenario_bounds is None:
            self.cur_rec.gross_pnl_usd = self.cur_gross
            self.cur_rec.net_pnl_usd = (
                self.cur_gross - self.cur_rec.cost_components_total_usd
                - cash_cost)
        else:
            self.cur_rec.gross_pnl_usd = None
            self.cur_rec.net_pnl_usd = None
            self.cur_rec.ambiguity = "AMBIGUOUS_ORDER"
            self.cur_rec.scenario_bounds = scenario_bounds
            self.cur_rec.ledger_booked_gross_usd = booked_gross
            self.cur_rec.notes.append(
                "ledger booked deterministic worst-case bound; "
                "journal keeps both bounds, no point PnL")
        self.cur_rec.cost_components_total_usd += cash_cost
        self.cur_rec.mae_usd, self.cur_rec.mfe_usd = \
            self.cur_rec.segment_mae_mfe()
        if note:
            self.cur_rec.notes.append(note)
        self.journal.add(self.cur_rec)
        self.position = None
        self.cur_rec = None
        self.tp = self.sl = self.time_exit = None
        self.pending_roll = None
        self.pending_exit = False
        self.time_exit_deferred = 0
        self.roll_deferral_noted = False

    def reconcile_state(self, mtm_bar) -> None:
        """R2 per-bar reconciliation: journal <-> cash <-> events <->
        inventory <-> MTM. The cash check is an INDEPENDENT counter
        path (running realized/cost totals) against the ledger's cash —
        not the ledger against its own event log."""
        self.ledger.reconcile()   # internal events <-> cash identity
        if abs(self.ledger.cash - (self.eng.cfg.initial_cash_usd
                                   + self.realized_gross
                                   - self.total_costs)) > 1e-6:
            raise AssertionError(
                "per-bar reconciliation failed: ledger cash "
                f"{self.ledger.cash} != initial + realized_gross "
                f"({self.realized_gross}) - total_costs ({self.total_costs}) — "
                "the independent counter path diverged from the ledger")
        if (self.position is None) != (self.cur_rec is None):
            raise AssertionError(
                f"inventory/journal divergence: position={self.position!r} "
                f"while record={self.cur_rec!r}")
        if self.position is not None and self.cur_rec is not None:
            if self.cur_rec.entry_fill is None:
                raise AssertionError("open record without an entry fill")
            if self.position.signed_qty != self.cur_rec.entry_fill.signed_qty:
                raise AssertionError(
                    "inventory qty drifted from the journal entry fill")
            if abs(self.cur_rec.entry_fill.signed_qty) != self.cur_rec.qty:
                raise AssertionError("journal qty inconsistent with fill")
            expected_conid = (self.cur_rec.rolls[-1].to_conid
                              if self.cur_rec.rolls
                              else self.cur_rec.entry_fill.conid)
            if self.position.conid != expected_conid:
                raise AssertionError(
                    f"held conid {self.position.conid} != journal chain "
                    f"{expected_conid} — inventory diverged from rolls")
            # MTM at the session close must lie inside the current
            # segment's recorded excursions (same-frame check)
            if mtm_bar is not None and self.seg_first_bar is not None:
                unreal = pnl(self.position.avg_entry_price, mtm_bar.c,
                             self.position.signed_qty,
                             self.eng.spec.multiplier)
                if not (self.seg_mae - 1e-6 <= unreal <= self.seg_mfe + 1e-6):
                    raise AssertionError(
                        f"MTM at close {unreal:.2f} outside the "
                        f"segment's recorded excursions [{self.seg_mae:.2f}, "
                        f"{self.seg_mfe:.2f}] — MAE/MFE frame mixing")
        self.n_recon_checks += 1

    # ---- one session ------------------------------------------------ #
    def step(self, t: dt.date, gate=None) -> None:
        """Replay ONE session of the (possibly mutated) chain. Must be
        called in strictly increasing session order over the chain."""
        bar = self.chain[t]

        # ---- 1. pending entry fill at this session's open ------------
        if self.pending is not None and self.pending_decision is not None:
            d = self.pending_decision
            side = 1 if d.action == "enter_long" else -1
            if not bar.is_close_only:
                denial = None
                if gate is not None:
                    denial = gate.admit_entry_fill(
                        self.eng.symbol, t, bar, side * abs(int(d.qty)))
                if denial is not None:
                    # Portfolio admission refused the fill (margin cap).
                    # The order DIES here — never a silent drop, never a
                    # reduced quantity — and the blocked signal is
                    # journaled with its reason code + detail.
                    self.n_trades += 1
                    rec = JournalRecord(
                        trade_id=f"{self.eng.symbol}-{self.n_trades:04d}",
                        symbol=self.eng.symbol,
                        decision_session=self.pending.session,
                        entry_decision_reason=d.reason,
                        veto_reason=str(denial.get(
                            "code", "BLOCKED_PORTFOLIO_ADMISSION")),
                        direction=0, qty=d.qty, entry_fill=None,
                        exit_fill=None, exit_type=None, exit_session=None,
                        feature_snapshot=d.features,
                    )
                    rec.notes.append(
                        f"entry blocked at fill session {t.isoformat()} by "
                        f"the portfolio gate: {denial.get('code')} "
                        f"{json.dumps(denial.get('detail', {}), sort_keys=True, default=str)}")
                    self.journal.add(rec)
                else:
                    q = abs(int(d.qty))
                    fp, breakdown, cash_cost = self.exec_cost(side, bar.o, t, q)
                    fill = FillRecord(
                        session=t, local_symbol=bar.local_symbol,
                        conid=bar.conid, signed_qty=side * q, price=fp,
                        cost_breakdown=breakdown, cost_total_usd=cash_cost,
                        fill_timing="next_open")
                    self.position = Position(
                        symbol=self.eng.symbol, local_symbol=bar.local_symbol,
                        conid=bar.conid, signed_qty=side * q,
                        avg_entry_price=fp, opened_session=t)
                    self.ledger.apply("entry_cost", t, -cash_cost,
                                      f"entry fill {bar.local_symbol}@{fp}")
                    self.total_costs += cash_cost
                    self.tp, self.sl = d.tp_price, d.sl_price
                    self.time_exit = d.time_exit_sessions
                    self.entry_session = t
                    self.n_trades += 1
                    self.cur_rec = JournalRecord(
                        trade_id=f"{self.eng.symbol}-{self.n_trades:04d}",
                        symbol=self.eng.symbol, decision_session=self.pending.session,
                        entry_decision_reason=d.reason, veto_reason=None,
                        direction=side, qty=q, entry_fill=fill,
                        exit_fill=None, exit_type=None, exit_session=None,
                        feature_snapshot=d.features,
                        cost_components_total_usd=cash_cost,
                        cost_breakdown=breakdown,
                        cost_incomplete=bool(breakdown.get("cost_incomplete")),
                        cost_missing_components=list(breakdown.get(
                            "missing_cost_components", [])),
                        stress_level=self.eng.cfg.stress,
                    )
                    if self.eng.cfg.fill_timing == "same_close":
                        self.cur_rec.notes.append("OPTIMISTIC_SAME_CLOSE")
                    # R2/R3: the lifecycle segment accounting opens with the
                    # fill; cur_gross resets for the new record
                    self.cur_gross = 0.0
                    self.start_segment(bar.conid, bar.local_symbol, fp)
            else:
                # cannot fill on a close-only settlement bar (no tradeable
                # price): order lapses, recorded, NOT fabricated
                if self.cur_rec is None:
                    self.n_trades += 1
                    self.cur_rec = JournalRecord(
                        trade_id=f"{self.eng.symbol}-{self.n_trades:04d}",
                        symbol=self.eng.symbol, decision_session=self.pending.session,
                        entry_decision_reason=d.reason,
                        veto_reason="ORDER_LAPSED_CLOSE_ONLY_BAR",
                        direction=0, qty=d.qty, entry_fill=None,
                        exit_fill=None, exit_type=None, exit_session=None,
                        feature_snapshot=d.features,
                    )
                    self.journal.add(self.cur_rec)
                    self.cur_rec = None
            self.pending = self.pending_decision = None

        # ---- 2. manage open position --------------------------------
        pbar = None
        if self.position is not None and self.cur_rec is not None:
            direction = 1 if self.position.signed_qty > 0 else -1
            # Bar of the contract ACTUALLY held: equals the chain bar
            # except while a roll is deferred past its scheduled session
            # (close-only fill law) and the chain has moved on.
            pbar = (bar if bar.conid == self.position.conid
                    else self.eng._bars_by_conid.get(
                        self.position.conid, {}).get(t))

            # 2a. deferred MANUAL exit fills at the OPEN of the first
            # tradeable session (close-only bars never fill)
            if self.pending_exit:
                if pbar is not None and not pbar.is_close_only:
                    q = abs(self.position.signed_qty)
                    fp, breakdown, cash_cost = self.exec_cost(
                        -direction, pbar.o, t, q)
                    gross = pnl(self.position.avg_entry_price, fp,
                                self.position.signed_qty,
                                self.eng.spec.multiplier)
                    self.ledger.apply("realize", t, gross, "manual exit")
                    self.ledger.apply("exit_cost", t, -cash_cost, "manual exit")
                    self.realized_gross += gross
                    self.total_costs += cash_cost
                    self.book_exit(
                        FillRecord(
                            session=t, local_symbol=self.position.local_symbol,
                            conid=self.position.conid,
                            signed_qty=-self.position.signed_qty, price=fp,
                            cost_breakdown=breakdown,
                            cost_total_usd=cash_cost,
                            fill_timing="next_open"),
                        "MANUAL", t, gross, cash_cost,
                        note="manual exit filled at the next tradeable "
                             "open (exit was requested on a close-only "
                             "bar; close-only bars never fill)")

        if self.position is not None and self.cur_rec is not None:
            direction = 1 if self.position.signed_qty > 0 else -1
            q = abs(self.position.signed_qty)

            # 2b. MAE/MFE from THIS session's extremes — computed on the
            # SAME contract as the current segment's entry, BEFORE any
            # exit handling (the exit bar itself counts) and BEFORE the
            # end-of-session roll (R3: extrema never mix frames). OHLC
            # after an intrabar fill can only bound, never resolve.
            if pbar is not None:
                worst = pbar.l if direction > 0 else pbar.h
                best = pbar.h if direction > 0 else pbar.l
                self.seg_mae = min(self.seg_mae, pnl(
                    self.seg_entry_px, worst, self.position.signed_qty,
                    self.eng.spec.multiplier))
                self.seg_mfe = max(self.seg_mfe, pnl(
                    self.seg_entry_px, best, self.position.signed_qty,
                    self.eng.spec.multiplier))
                if self.seg_first_bar is None:
                    self.seg_first_bar = t
                self.seg_last_bar = t

            # 2c. TP / SL intrabar — on the OLD position/contract BEFORE
            # any end-of-session roll (R3), with gap-aware fill
            # references (R4). NEVER on a close-only bar (h=l=c=
            # settlement: a settlement close is not an intrabar touch).
            if (self.position is not None and self.cur_rec is not None
                    and pbar is not None and not pbar.is_close_only):
                hit_sl = (self.sl is not None and
                          ((direction > 0 and pbar.l <= self.sl)
                           or (direction < 0 and pbar.h >= self.sl)))
                hit_tp = (self.tp is not None and
                          ((direction > 0 and pbar.h >= self.tp)
                           or (direction < 0 and pbar.l <= self.tp)))
                if hit_sl and hit_tp:
                    # Same-bar ambiguity: the intraday order is UNKNOWN;
                    # inventing one from OHLC alone is forbidden.
                    # Gap-aware scenario references (R4): a gap through a
                    # stop fills at the open; a limit fills at the
                    # barrier or better.
                    ref_tp = (max(pbar.o, self.tp) if direction > 0
                              else min(pbar.o, self.tp))
                    ref_sl = (min(pbar.o, self.sl) if direction > 0
                              else max(pbar.o, self.sl))
                    fp_tp, bd_tp, cash_tp = self.exec_cost(
                        -direction, ref_tp, t, q)
                    fp_sl, bd_sl, cash_sl = self.exec_cost(
                        -direction, ref_sl, t, q)
                    gross_tp = pnl(self.position.avg_entry_price, fp_tp,
                                   self.position.signed_qty,
                                   self.eng.spec.multiplier)
                    gross_sl = pnl(self.position.avg_entry_price, fp_sl,
                                   self.position.signed_qty,
                                   self.eng.spec.multiplier)
                    worst_is_sl = gross_sl <= gross_tp
                    gross_worst = gross_sl if worst_is_sl else gross_tp
                    fp, breakdown, cash_cost = (
                        (fp_sl, bd_sl, cash_sl) if worst_is_sl
                        else (fp_tp, bd_tp, cash_tp))
                    self.ledger.apply("realize", t, gross_worst,
                                      "AMBIGUOUS booked worst-case bound")
                    self.ledger.apply("exit_cost", t, -cash_cost, "ambiguous")
                    self.realized_gross += gross_worst
                    self.total_costs += cash_cost
                    bounds = {
                        "tp_first": gross_tp - cash_tp
                        - self.cur_rec.cost_components_total_usd,
                        "sl_first": gross_sl - cash_sl
                        - self.cur_rec.cost_components_total_usd,
                    }
                    self.book_exit(
                        FillRecord(
                            session=t, local_symbol=self.position.local_symbol,
                            conid=self.position.conid,
                            signed_qty=-self.position.signed_qty, price=fp,
                            cost_breakdown=breakdown,
                            cost_total_usd=cash_cost,
                            fill_timing="intrabar"),
                        "TP_SL_SAME_BAR", t, gross_worst, cash_cost,
                        scenario_bounds=bounds,
                        booked_gross=gross_worst)
                elif hit_sl or hit_tp:
                    is_sl = hit_sl
                    lvl = self.sl if is_sl else self.tp
                    # R4 fill references:
                    #   SL (stop-market): the OPEN when the bar gaps
                    #   through the barrier (long stop: min(o, sl);
                    #   short stop: max(o, sl)); adverse cost shift
                    #   afterwards — a long stop never fills above the
                    #   open, a short stop never below it;
                    #   TP (limit): the barrier or better (long TP sell:
                    #   max(o, tp); short TP buy: min(o, tp)).
                    if is_sl:
                        ref = (min(pbar.o, lvl) if direction > 0
                               else max(pbar.o, lvl))
                    else:
                        ref = (max(pbar.o, lvl) if direction > 0
                               else min(pbar.o, lvl))
                    fp, breakdown, cash_cost = self.exec_cost(
                        -direction, ref, t, q)
                    gross = pnl(self.position.avg_entry_price, fp,
                                self.position.signed_qty,
                                self.eng.spec.multiplier)
                    self.ledger.apply("realize", t, gross, "exit")
                    self.ledger.apply("exit_cost", t, -cash_cost, "exit")
                    self.realized_gross += gross
                    self.total_costs += cash_cost
                    self.book_exit(
                        FillRecord(
                            session=t, local_symbol=self.position.local_symbol,
                            conid=self.position.conid,
                            signed_qty=-self.position.signed_qty, price=fp,
                            cost_breakdown=breakdown,
                            cost_total_usd=cash_cost,
                            fill_timing="intrabar"),
                        "SL" if is_sl else "TP", t, gross, cash_cost)

            # 2d. time exit at the session close — BEFORE the roll, so an
            # expiring time exit never pays pointless roll legs (waits
            # for a tradeable bar; close-only bars never fill — the
            # deferral is counted)
            if self.position is not None and self.cur_rec is not None:
                held_sessions = (self.eng._session_ordinal(t)
                                 - self.eng._session_ordinal(self.entry_session)
                                 + 1) if self.entry_session else 0
                if self.time_exit is not None and held_sessions >= self.time_exit:
                    if pbar is not None and not pbar.is_close_only:
                        fp, breakdown, cash_cost = self.exec_cost(
                            -direction, pbar.c, t, q)
                        gross = pnl(self.position.avg_entry_price, fp,
                                    self.position.signed_qty,
                                    self.eng.spec.multiplier)
                        self.ledger.apply("realize", t, gross, "time exit")
                        self.ledger.apply("exit_cost", t, -cash_cost,
                                          "time exit")
                        self.realized_gross += gross
                        self.total_costs += cash_cost
                        note = None
                        if self.time_exit_deferred:
                            note = (f"time-exit fill deferred "
                                    f"{self.time_exit_deferred} session(s) "
                                    "across close-only bars")
                        self.book_exit(
                            FillRecord(
                                session=t,
                                local_symbol=self.position.local_symbol,
                                conid=self.position.conid,
                                signed_qty=-self.position.signed_qty,
                                price=fp, cost_breakdown=breakdown,
                                cost_total_usd=cash_cost,
                                fill_timing="session_close"),
                            "TIME", t, gross, cash_cost, note=note)
                    else:
                        self.time_exit_deferred += 1

            # 2e. ROLL at the session close — strictly AFTER the intrabar
            # barriers and the time exit (R3): the position that traded
            # the whole session is the one whose barriers matter, and a
            # stopped/expired position never rolls. Hard expiry wall:
            # the engine never holds a contract past its roll date.
            if self.position is not None and self.cur_rec is not None:
                row_due = self.eng._roll_row.get(t)
                due_now = (row_due is not None
                           and row_due.old_conid == self.position.conid)
                if due_now:
                    self.pending_roll = row_due
                if (self.pending_roll is not None
                        and self.pending_roll.old_conid == self.position.conid):
                    if due_now and not self.eng.cfg.force_roll_open_positions:
                        raise PolicyError(
                            "force_roll_open_positions=False would allow "
                            "holding past the roll date into the expiry/"
                            "first-notice zone — forbidden")
                    roll_row = self.pending_roll
                    old_bar = pbar
                    new_bar = self.eng._bars_by_conid.get(
                        roll_row.new_conid, {}).get(t)
                    if due_now and new_bar is None:
                        if old_bar is not None and not old_bar.is_close_only:
                            # no next-contract price -> forced exit at the
                            # old close (tradeable bar required; else the
                            # roll stays deferred and the trade censors)
                            old_close = old_bar.c
                            fp, breakdown, cash_cost = self.exec_cost(
                                -direction, old_close, t, q)
                            gross = pnl(self.position.avg_entry_price, fp,
                                        self.position.signed_qty,
                                        self.eng.spec.multiplier)
                            self.ledger.apply("realize", t, gross, "forced exit")
                            self.ledger.apply("exit_cost", t, -cash_cost,
                                              "forced exit")
                            self.realized_gross += gross
                            self.total_costs += cash_cost
                            self.book_exit(
                                FillRecord(
                                    session=t,
                                    local_symbol=self.position.local_symbol,
                                    conid=self.position.conid,
                                    signed_qty=-self.position.signed_qty,
                                    price=fp,
                                    cost_breakdown=breakdown,
                                    cost_total_usd=cash_cost,
                                    fill_timing="session_close"),
                                "FORCED_ROLL", t, gross, cash_cost,
                                note="no next contract price on roll "
                                     "date; forced exit (expired/"
                                     "first-notice wall)")
                        elif not self.roll_deferral_noted:
                            self.cur_rec.notes.append(
                                f"roll scheduled {roll_row.decision_session}"
                                " deferred: no tradeable old bar (close-only"
                                " bars never fill)")
                            self.roll_deferral_noted = True
                    elif (old_bar is not None
                          and not old_bar.is_close_only
                          and new_bar is not None
                          and not new_bar.is_close_only):
                        # explicit old fill + new fill at raw closes —
                        # only when BOTH bars are tradeable
                        old_close = old_bar.c
                        new_price = new_bar.c
                        fpo, bdo, co = self.exec_cost(-direction, old_close,
                                                      t, q)
                        fpn, bdn, cn = self.exec_cost(direction, new_price,
                                                      t, q)
                        gross = pnl(self.position.avg_entry_price, fpo,
                                    self.position.signed_qty,
                                    self.eng.spec.multiplier)
                        self.ledger.apply("realize", t, gross,
                                          f"roll leg old {self.position.local_symbol}")
                        self.ledger.apply("roll_cost", t, -(co + cn), "roll legs")
                        self.realized_gross += gross
                        self.total_costs += co + cn
                        gap = new_price - old_close
                        self.cur_rec.rolls.append(RollEvent(
                            session=t, from_contract=self.position.local_symbol,
                            to_contract=roll_row.new_contract,
                            from_conid=self.position.conid,
                            to_conid=roll_row.new_conid,
                            old_close=old_close, new_close=new_price,
                            raw_gap=gap,
                            reason_code=roll_row.reason_code,
                            reason_text=roll_row.reason_text))
                        # R2: the old-contract segment's realized gross is
                        # part of THIS record's lifecycle (base bug: it
                        # vanished from the journal). The raw gap itself
                        # is NOT a transaction cost — it is borne once
                        # through the raw-contract segment fills.
                        self.cur_rec.gross_segments.append({
                            "session": t.isoformat(),
                            "conid": self.position.conid,
                            "local_symbol": self.position.local_symbol,
                            "kind": "roll_leg_old_contract",
                            "gross_usd": gross,
                            "fill_price": fpo,
                        })
                        self.cur_gross += gross
                        self.cur_rec.cost_components_total_usd += co + cn
                        # R3: close the old segment (its bars end here);
                        # the new segment's entry is the roll fill and
                        # its bars only count from the NEXT session (the
                        # fill happens at THIS close — the new contract's
                        # own high/low today happened BEFORE the fill)
                        self.close_segment()
                        self.position.with_roll(
                            roll_row.new_contract, roll_row.new_conid,
                            fpn, t, gap)
                        self.start_segment(roll_row.new_conid,
                                           roll_row.new_contract, fpn)
                        if self.tp is not None and gap is not None:
                            self.tp = round_to_tick(self.tp + gap,
                                                    self.eng.spec.min_tick)
                        if self.sl is not None and gap is not None:
                            self.sl = round_to_tick(self.sl + gap,
                                                    self.eng.spec.min_tick)
                        self.pending_roll = None
                        self.roll_deferral_noted = False
                    elif not self.roll_deferral_noted:
                        self.cur_rec.notes.append(
                            f"roll scheduled {roll_row.decision_session}"
                            " deferred: no tradeable bar pair this session"
                            " (close-only bars never fill)")
                        self.roll_deferral_noted = True

        # ---- 3. strategy decision at close ---------------------------
        view = PITDataView(self.chain, t)
        ctx = _Ctx(view=view, asof=t, position=self.position,
                   symbol=self.eng.symbol, spec=self.eng.spec)
        dec = self.strategy(ctx)
        if not isinstance(dec, Decision):
            raise PolicyError("strategy must return a Decision")
        if self.position is None:
            if dec.action in ("enter_long", "enter_short"):
                if (not isinstance(dec.qty, int)
                        or isinstance(dec.qty, bool) or dec.qty < 1):
                    raise PolicyError(
                        f"Decision.qty must be an integer >= 1 (got "
                        f"{dec.qty!r}) — commissions and risk scale "
                        "with quantity")
                if dec.features:
                    validate_feature_snapshot(dec.features, t)
                denial = None
                if gate is not None:
                    denial = gate.vet_entry_decision(
                        self.eng.symbol, t, dec)
                if denial is not None:
                    # Portfolio structural caps refused the SIGNAL at the
                    # decision close: journaled as a veto (qty unchanged —
                    # the cap layer NEVER clips or rescales).
                    self.n_trades += 1
                    rec = JournalRecord(
                        trade_id=f"{self.eng.symbol}-{self.n_trades:04d}",
                        symbol=self.eng.symbol, decision_session=t,
                        entry_decision_reason=dec.reason or "veto",
                        veto_reason=str(denial.get(
                            "code", "VETO_PORTFOLIO_CAP")),
                        direction=0, qty=dec.qty, entry_fill=None,
                        exit_fill=None, exit_type=None, exit_session=None,
                        feature_snapshot=dec.features)
                    rec.notes.append(
                        f"signal vetoed by the portfolio gate at close "
                        f"{t.isoformat()}: {denial.get('code')} "
                        f"{json.dumps(denial.get('detail', {}), sort_keys=True, default=str)}")
                    self.journal.add(rec)
                else:
                    self.pending = OrderRecord(
                        session=t, intent=dec.action.upper(), qty=dec.qty,
                        reason=dec.reason)
                    self.pending_decision = dec
            elif dec.action == "veto":
                self.n_trades += 1
                self.journal.add(JournalRecord(
                    trade_id=f"{self.eng.symbol}-{self.n_trades:04d}",
                    symbol=self.eng.symbol, decision_session=t,
                    entry_decision_reason=dec.reason or "veto",
                    veto_reason=dec.veto_reason or "VETO",
                    direction=0, qty=0, entry_fill=None, exit_fill=None,
                    exit_type=None, exit_session=None,
                    feature_snapshot=dec.features))
        # strategy exit requests are honored next session via TP/SL/time
        # or by returning Decision(action='exit') below
        elif dec.action == "exit":
            direction = 1 if self.position.signed_qty > 0 else -1
            mbar = (bar if bar.conid == self.position.conid
                    else self.eng._bars_by_conid.get(
                        self.position.conid, {}).get(t))
            if mbar is not None and not mbar.is_close_only:
                q = abs(self.position.signed_qty)
                fp, breakdown, cash_cost = self.exec_cost(-direction, mbar.c,
                                                          t, q)
                gross = pnl(self.position.avg_entry_price, fp,
                            self.position.signed_qty,
                            self.eng.spec.multiplier)
                self.ledger.apply("realize", t, gross, "manual exit")
                self.ledger.apply("exit_cost", t, -cash_cost, "manual exit")
                self.realized_gross += gross
                self.total_costs += cash_cost
                self.book_exit(
                    FillRecord(
                        session=t, local_symbol=self.position.local_symbol,
                        conid=self.position.conid,
                        signed_qty=-self.position.signed_qty, price=fp,
                        cost_breakdown=breakdown,
                        cost_total_usd=cash_cost,
                        fill_timing="same_close"),
                    "MANUAL", t, gross, cash_cost,
                    note="OPTIMISTIC_SAME_CLOSE")
            else:
                # close-only bar (or no bar for the held contract): a
                # same-close exit would fill at a settlement price —
                # defer to the next tradeable session's OPEN
                self.pending_exit = True
                self.cur_rec.notes.append(
                    f"manual exit requested {t.isoformat()} on a "
                    "close-only bar: deferred (close-only bars never "
                    "fill); will fill at the next tradeable open")

        # ---- 4. per-session reconciliation --------------------------
        # R2: journal <-> cash <-> events <-> inventory <-> MTM, every
        # bar (see reconcile_state: the cash check is an independent
        # counter path, not the ledger against its own events)
        end_bar = None
        if self.position is not None and self.cur_rec is not None:
            end_bar = (bar if bar.conid == self.position.conid
                       else self.eng._bars_by_conid.get(
                           self.position.conid, {}).get(t))
        self.reconcile_state(end_bar)

    # ---- end of data + final reconciliation ------------------------ #
    def finalize(self, sessions: list[dt.date]) -> TradeJournal:
        """Censoring of still-open positions + end-of-run independent
        reconciliation. Mirrors the historical end-of-run path verbatim."""
        if self.position is not None and self.cur_rec is not None:
            last = sessions[-1]
            lbar = (self.chain[last] if self.chain[last].conid == self.position.conid
                    else self.eng._bars_by_conid.get(
                        self.position.conid, {}).get(last))
            unreal = (pnl(self.position.avg_entry_price, lbar.c,
                          self.position.signed_qty,
                          self.eng.spec.multiplier)
                      if lbar is not None else None)
            self.cur_rec.right_censored = True
            self.cur_rec.exit_type = "END_OF_DATA"
            self.cur_rec.exit_session = None
            self.cur_rec.gross_pnl_usd = None
            self.cur_rec.net_pnl_usd = None
            if unreal is not None:
                self.cur_rec.notes.append(
                    f"right-censored: still open at end of data; unrealized "
                    f"(unbooked, descriptive only) = {unreal:.2f} USD")
            else:
                self.cur_rec.notes.append(
                    "right-censored: still open at end of data; unrealized "
                    "NOT_COMPUTED (no bar for the held contract on the last "
                    "session)")
            if self.pending_roll is not None:
                self.cur_rec.notes.append(
                    f"roll scheduled {self.pending_roll.decision_session} never "
                    "executed: no tradeable bar pair before end of data "
                    "(close-only bars never fill)")
            if self.pending_exit:
                self.cur_rec.notes.append(
                    "manual exit never executed: no tradeable session before "
                    "end of data (close-only bars never fill)")
            if self.time_exit_deferred:
                self.cur_rec.notes.append(
                    f"time exit never executed: {self.time_exit_deferred} deferred "
                    "session(s) on close-only bars")
            self.close_segment()
            self.cur_rec.mae_usd, self.cur_rec.mfe_usd = \
                self.cur_rec.segment_mae_mfe()
            if self.cur_rec.gross_segments:
                seg_gross = sum(s["gross_usd"]
                                for s in self.cur_rec.gross_segments)
                self.cur_rec.notes.append(
                    f"right-censored, but {len(self.cur_rec.gross_segments)} "
                    f"lifecycle segment(s) already EXECUTED "
                    f"(roll legs): realized gross booked in the ledger = "
                    f"{seg_gross:.2f} USD; the record claims NO point "
                    "trade PnL")
            self.journal.add(self.cur_rec)
            self.position = None

        # ---- final reconciliation --------------------------------------
        final = self.ledger.reconcile()
        expected = (self.eng.cfg.initial_cash_usd + self.realized_gross
                    - self.total_costs)
        if abs(final["final"] - expected) > 1e-6:
            raise AssertionError(
                f"cash identity failed: {final['final']} != {expected}")
        # R2: reconcile the ledger against an INDEPENDENT cash accounting
        # recomputed from the JOURNAL RECORDS — never against its own event
        # log. Any divergence between the journal artifacts, the ledger
        # event stream and the running counters is a hard failure.
        kind_sums = self.ledger.sums_by_kind()
        jr_gross = 0.0
        jr_costs = 0.0
        censored_realized = 0.0
        for r in self.journal.records:
            jr_costs += r.cost_components_total_usd
            if r.veto_reason is not None or r.entry_fill is None:
                continue
            if r.gross_pnl_usd is not None:
                jr_gross += r.gross_pnl_usd
            elif r.ledger_booked_gross_usd is not None:
                jr_gross += r.ledger_booked_gross_usd
            elif r.gross_segments:
                # MULTIASSET-WIRING fix (2026-10-02) of an EXEC-FIX R2 gap:
                # a RIGHT-CENSORED record whose roll legs already EXECUTED
                # booked realize events in the ledger; skipping censored
                # records wholesale made the independent journal<->cash
                # identity explode (found by the ALWAYS-ON baseline). The
                # EXECUTED segment gross is cash-realized and must count —
                # the record still claims NO point trade PnL (stays
                # censored, gross/net stay None).
                seg_gross = sum(s["gross_usd"] for s in r.gross_segments)
                jr_gross += seg_gross
                censored_realized += seg_gross
        event_realize = kind_sums.get("realize", 0.0)
        event_costs = -sum(v for k, v in kind_sums.items()
                           if k in ("entry_cost", "exit_cost", "roll_cost"))
        problems = []
        if abs(jr_gross - event_realize) > 1e-6:
            problems.append(
                f"journal gross {jr_gross} != ledger realize events "
                f"{event_realize}")
        if abs(jr_gross - self.realized_gross) > 1e-6:
            problems.append(
                f"journal gross {jr_gross} != realized counter "
                f"{self.realized_gross}")
        if abs(jr_costs - self.total_costs) > 1e-6:
            problems.append(
                f"journal costs {jr_costs} != cost counter {self.total_costs}")
        if abs(event_costs - self.total_costs) > 1e-6:
            problems.append(
                f"ledger cost events {event_costs} != cost counter "
                f"{self.total_costs}")
        if abs(final["final"] - (self.eng.cfg.initial_cash_usd + jr_gross
                                 - jr_costs)) > 1e-6:
            problems.append(
                f"cash {final['final']} != independent journal identity "
                f"{self.eng.cfg.initial_cash_usd + jr_gross - jr_costs}")
        for r in self.journal.records:
            booked = (r.gross_pnl_usd if r.gross_pnl_usd is not None
                      else r.ledger_booked_gross_usd)
            if booked is not None and r.gross_segments:
                seg_sum = sum(s["gross_usd"] for s in r.gross_segments)
                if abs(booked - seg_sum) > 1e-6:
                    problems.append(
                        f"{r.trade_id}: booked gross {booked} != segment "
                        f"sum {seg_sum}")
        if self.position is not None:
            problems.append("inventory not flat at end of run")
        if problems:
            raise AssertionError(
                "independent journal<->cash reconciliation failed: "
                + "; ".join(problems))
        self.eng.last_run_stats = {
            "symbol": self.eng.symbol,
            "sessions": len(sessions),
            "ledger": final,
            "realized_gross_usd": self.realized_gross,
            "total_costs_usd": self.total_costs,
            "journal_summary": self.journal.summary(),
            "independent_reconciliation": {
                "journal_gross_usd": jr_gross,
                "journal_costs_usd": jr_costs,
                "censored_realized_segments_usd": censored_realized,
                "ledger_realize_usd": event_realize,
                "ledger_cost_outflow_usd": event_costs,
                "cash_final_usd": final["final"],
                "identity_usd": (self.eng.cfg.initial_cash_usd + jr_gross
                                 - jr_costs),
                "per_bar_checks": self.n_recon_checks,
                "reconciled": True,
            },
        }
        return self.journal


# ------------------------------------------------------------------------- #
# Multi-symbol portfolio layer (MULTIASSET-WIRING, steering round 2, 2026-10-02)
# ------------------------------------------------------------------------- #
@dataclass
class PortfolioRunResult:
    """Artifacts of one portfolio replay (all USD, all deterministic)."""
    symbols: tuple[str, ...]
    journals: dict[str, TradeJournal]
    sessions: list[dt.date]
    initial_cash_by_symbol: dict[str, float]
    cash_by_session: dict[dt.date, dict[str, float]]
    mtm_by_session: dict[dt.date, dict[str, float]]
    equity_by_session: dict[dt.date, float]
    peak_equity_by_session: dict[dt.date, float]
    drawdown_by_session: dict[dt.date, float]
    positions_by_session: dict[dt.date, dict[str, dict]]
    margin_by_session: dict[dt.date, dict] = field(default_factory=dict)
    gate_audit: list[dict] = field(default_factory=list)

    def to_json(self) -> str:
        """Deterministic series dump (journals dump separately)."""
        doc = {
            "symbols": list(self.symbols),
            "sessions": [s.isoformat() for s in self.sessions],
            "initial_cash_by_symbol": self.initial_cash_by_symbol,
            "cash_by_session": {s.isoformat(): v
                                for s, v in self.cash_by_session.items()},
            "mtm_by_session": {s.isoformat(): v
                               for s, v in self.mtm_by_session.items()},
            "equity_by_session": {s.isoformat(): v
                                  for s, v in self.equity_by_session.items()},
            "peak_equity_by_session": {
                s.isoformat(): v
                for s, v in self.peak_equity_by_session.items()},
            "drawdown_by_session": {
                s.isoformat(): v
                for s, v in self.drawdown_by_session.items()},
            "positions_by_session": {
                s.isoformat(): v
                for s, v in self.positions_by_session.items()},
            "margin_by_session": {s.isoformat(): v
                                  for s, v in self.margin_by_session.items()},
        }
        return json.dumps(doc, indent=1, sort_keys=True)

    def final_cash_usd(self) -> float:
        if not self.sessions:
            return sum(self.initial_cash_by_symbol.values())
        return sum(self.cash_by_session[self.sessions[-1]].values())


class PortfolioEngine:
    """Synchronous multi-symbol portfolio replay over per-symbol engines.

    See the module docstring (MULTIASSET-WIRING laws). The gate protocol
    (any object with bind/vet_entry_decision/admit_entry_fill — see
    composition.PortfolioRiskGate for the reference implementation) is
    the ONLY enforcement path: caps arrive as veto/blocked journal
    entries, never as silent quantity adjustments.
    """

    def __init__(self, engines: dict[str, BacktestEngine]):
        if not engines:
            raise PolicyError("PortfolioEngine needs at least one symbol")
        syms = list(engines)
        if len(set(syms)) != len(syms):
            raise PolicyError(f"duplicate symbols in portfolio: {syms}")
        for sym, eng in engines.items():
            if eng.symbol != sym:
                raise PolicyError(
                    f"engine key {sym} != engine.symbol {eng.symbol}")
        self.engines: dict[str, BacktestEngine] = dict(engines)
        self._replays: dict[str, _Replay] | None = None
        # marks protocol (no within-session lookahead):
        #   _marks_live    — end-of-session marks of the HELD contracts
        #                    (series/equity reporting AFTER a session ends)
        #   _marks_frozen  — copy of live marks as of the LAST COMPLETED
        #                    session; everything the gate reads at fill
        #                    time. A position filled at t's open has no
        #                    frozen mark -> MTM 0 (== marked at its own
        #                    fill price); the CURRENT session's close is
        #                    never visible at its own open.
        self._marks_live: dict[str, float] = {}
        self._marks_frozen: dict[str, float] = {}
        self._last_close: dict[str, float] = {}   # sym -> last chain close (PIT)

    # ---- live portfolio state (gate interface; sessions <= t only) -- #
    def net_positions(self) -> dict[str, int]:
        """Net signed quantity per symbol, each on its CURRENT chain
        contract (per-contract-chain netting: rolls move the net qty)."""
        if self._replays is None:
            raise PolicyError("no active portfolio run — state unavailable")
        return {sym: rp.position.signed_qty
                for sym, rp in sorted(self._replays.items())
                if rp.position is not None}

    def effective_book(self) -> dict[str, int]:
        """Held net positions MERGED with already-decided pending entry
        orders (state as of the last stepped close). Pendings are PAST
        decisions (<= t), so this stays PIT-legal; the gate uses it so
        concurrency / gross-contract caps count signals that will fill
        tomorrow — without it, N same-close signals would each see an
        empty book and over-admit."""
        if self._replays is None:
            raise PolicyError("no active portfolio run — state unavailable")
        out = self.net_positions()
        for sym, rp in sorted(self._replays.items()):
            if rp.pending is not None and rp.pending_decision is not None:
                side = 1 if rp.pending_decision.action == "enter_long" else -1
                out[sym] = out.get(sym, 0) + side * abs(int(rp.pending_decision.qty))
        return {s: q for s, q in out.items() if q}

    def held_contracts(self) -> dict[str, dict]:
        if self._replays is None:
            raise PolicyError("no active portfolio run — state unavailable")
        return {sym: {"conid": rp.position.conid,
                      "local_symbol": rp.position.local_symbol,
                      "qty": rp.position.signed_qty,
                      "avg_entry_price": rp.position.avg_entry_price}
                for sym, rp in sorted(self._replays.items())
                if rp.position is not None}

    def _mtm(self, sym: str, marks: dict[str, float] | None = None) -> float:
        rp = self._replays[sym]
        if rp.position is None:
            return 0.0
        mark = (self._marks_frozen if marks is None else marks).get(sym)
        if mark is None:
            return 0.0   # no mark as of this frame -> a just-filled position
            # marks at its own fill price (MTM 0); never a fabricated mark
        return pnl(rp.position.avg_entry_price, mark,
                   rp.position.signed_qty, rp.eng.spec.multiplier)

    def equity_usd(self) -> float:
        """Aggregated USD equity for GATE decisions = Σ ledger cash +
        Σ MTM at the FROZEN marks (last COMPLETED session) — a just-filled
        position contributes MTM 0 (its own fill price); the current
        session's close is never visible at its own open."""
        if self._replays is None:
            raise PolicyError("no active portfolio run — state unavailable")
        cash = sum(rp.ledger.cash for rp in self._replays.values())
        return cash + sum(self._mtm(s) for s in self._replays)

    def usd_notional_per_contract(self, sym: str) -> float:
        """ABSOLUTE USD notional of one contract at the latest chain close
        (PIT: latest session stepped; abs because negative CL prices are
        legal and must not offset gross notional)."""
        price = self._last_close.get(sym)
        if price is None:
            raise PolicyError(
                f"{sym}: no PIT close available yet — notional caps cannot "
                "treat a missing price as zero")
        spec = self.engines[sym].spec
        return abs(check_price_plausible(sym, price) * spec.multiplier)

    # ---- the portfolio replay --------------------------------------- #
    def run(self, strategies: dict, journals: dict[str, TradeJournal] | None = None,
            cutoff: dt.date | None = None, gate=None,
            data_after_cutoff_mutate_seed: int | None = None,
            margin_model: MarginModel | None = None
            ) -> PortfolioRunResult:
        """Lockstep replay of all member symbols.

        cutoff: run only sessions <= cutoff (truncation hook).
        data_after_cutoff_mutate_seed: if set (requires cutoff), every
        symbol's bars strictly after cutoff are replaced by seeded
        garbage (per-symbol seed = seed + symbol index) — portfolio
        decisions/journals/series at t <= cutoff must be unaffected.
        margin_model: if provided, per-session aggregated margin
        requirement + utilization vs equity is recorded (DESCRIPTIVE;
        enforcement is the gate's job, never silent).
        """
        if set(strategies) != set(self.engines):
            raise PolicyError(
                f"strategies {sorted(strategies)} != portfolio symbols "
                f"{sorted(self.engines)}")
        if data_after_cutoff_mutate_seed is not None and cutoff is None:
            raise PolicyError(
                "data_after_cutoff_mutate_seed requires cutoff")
        if gate is not None and hasattr(gate, "bind"):
            gate.bind(self)

        chains: dict[str, dict[dt.date, ChainBar]] = {}
        replays: dict[str, _Replay] = {}
        jrn: dict[str, TradeJournal] = {}
        for i, sym in enumerate(sorted(self.engines)):
            eng = self.engines[sym]
            chain = eng._chain
            if cutoff is not None and data_after_cutoff_mutate_seed is not None:
                chain = eng._mutate_future(cutoff, data_after_cutoff_mutate_seed + i)
            chains[sym] = chain
            j = (journals or {}).get(sym)
            if j is None:
                j = TradeJournal(breakeven_tolerance_usd=0.0)
            jrn[sym] = j
            replays[sym] = eng._make_replay(strategies[sym], j, chain)
        self._replays = replays
        self._marks_live = {}
        self._marks_frozen = {}
        self._last_close = {}

        sym_sessions = {sym: [s for s in self.engines[sym].sessions
                              if cutoff is None or s <= cutoff]
                        for sym in sorted(self.engines)}
        union_sessions = sorted({s for ss in sym_sessions.values() for s in ss})

        cash_by: dict[dt.date, dict[str, float]] = {}
        mtm_by: dict[dt.date, dict[str, float]] = {}
        eq_by: dict[dt.date, float] = {}
        peak_by: dict[dt.date, float] = {}
        dd_by: dict[dt.date, float] = {}
        pos_by: dict[dt.date, dict[str, dict]] = {}
        margin_by: dict[dt.date, dict] = {}
        peak: float | None = None

        for t in union_sessions:
            # freeze marks at the last COMPLETED session: the gate's
            # fill-time equity can never see THIS session's closes
            self._marks_frozen = dict(self._marks_live)
            stepped: list[str] = []
            for sym in sorted(replays):
                if t not in sym_sessions[sym] or t not in chains[sym]:
                    continue
                b = chains[sym][t]
                # publish this symbol's own close BEFORE its step: the
                # close is settled information at the decision point of
                # the same session (notional caps read it PIT-legally)
                self._last_close[sym] = b.c
                replays[sym].step(t, gate=gate)
                stepped.append(sym)
            # end-of-session marks on the HELD contract's bar at t
            # (marks may be settlement closes; fills never are)
            for sym in stepped:
                rp = replays[sym]
                if rp.position is None:
                    self._marks_live.pop(sym, None)
                    continue
                b = chains[sym][t]
                pb = (b if b.conid == rp.position.conid
                      else self.engines[sym]._bars_by_conid.get(
                          rp.position.conid, {}).get(t))
                if pb is not None:
                    self._marks_live[sym] = pb.c
            cash_row = {sym: replays[sym].ledger.cash
                        for sym in sorted(replays)}
            mtm_row = {sym: self._mtm(sym, self._marks_live)
                       for sym in sorted(replays)}
            equity = sum(cash_row.values()) + sum(mtm_row.values())
            peak = equity if peak is None else max(peak, equity)
            cash_by[t] = cash_row
            mtm_by[t] = mtm_row
            eq_by[t] = equity
            peak_by[t] = peak
            dd_by[t] = equity - peak
            pos_by[t] = {
                sym: {"qty": rp.position.signed_qty,
                      "conid": rp.position.conid,
                      "local_symbol": rp.position.local_symbol}
                for sym, rp in sorted(replays.items())
                if rp.position is not None}
            if margin_model is not None:
                book = {sym: p["qty"] for sym, p in pos_by[t].items()}
                if book:
                    chk = margin_model.check(book, equity, level="initial")
                    margin_by[t] = {
                        "required_usd": chk["required_usd"],
                        "equity_usd": equity,
                        "utilization": (chk["required_usd"] / equity
                                        if equity > 0 else None),
                        "breach": chk["breach"],
                        "per_symbol_usd": chk["per_symbol_usd"],
                        "source": chk["source"],
                        "note": "descriptive aggregation; enforcement is "
                                "the gate's job (blocked journal entries)",
                    }

        for sym in sorted(replays):
            replays[sym].finalize(sym_sessions[sym])

        # ---- portfolio-level reconciliation (hard failures) ---------- #
        initial_by = {sym: self.engines[sym].cfg.initial_cash_usd
                      for sym in sorted(replays)}
        for t in union_sessions:
            indep_cash = sum(
                initial_by[sym]
                + sum(a for _k, s, a, _n in replays[sym].ledger.events
                      if s <= t)
                for sym in sorted(replays))
            if abs(indep_cash - sum(cash_by[t].values())) > 1e-6:
                raise AssertionError(
                    f"portfolio cash aggregation failed at {t}: "
                    f"{sum(cash_by[t].values())} != independent event-log "
                    f"recomputation {indep_cash}")
            if abs(eq_by[t] - (sum(cash_by[t].values())
                               + sum(mtm_by[t].values()))) > 1e-6:
                raise AssertionError(
                    f"portfolio equity decomposition failed at {t}")
            if not pos_by[t] and any(abs(v) > 1e-9
                                     for v in mtm_by[t].values()):
                raise AssertionError(
                    f"portfolio MTM nonzero at {t} with no open positions")

        result = PortfolioRunResult(
            symbols=tuple(sorted(replays)),
            journals=jrn,
            sessions=union_sessions,
            initial_cash_by_symbol=initial_by,
            cash_by_session=cash_by,
            mtm_by_session=mtm_by,
            equity_by_session=eq_by,
            peak_equity_by_session=peak_by,
            drawdown_by_session=dd_by,
            positions_by_session=pos_by,
            margin_by_session=margin_by,
            gate_audit=list(getattr(gate, "decisions", [])
                            if gate is not None else []),
        )
        self.last_result = result
        return result


class _Ctx:
    """Read-only context handed to the strategy at each session close."""

    def __init__(self, view, asof, position, symbol, spec):
        self.view = view
        self.asof = asof
        self.position = position
        self.symbol = symbol
        self.spec = spec
