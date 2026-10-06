"""Replay engine tests: execution model, ambiguous TP/SL, rolls, censoring,
PIT enforcement, determinism, truncation/future-mutation invariance,
negative CL and 6J accounting through full engine runs."""
import datetime as dt
import unittest

from futbt.accounting import pnl
from futbt.calendarx import WeekdayCalendar
from futbt.costs import CostBook
from futbt.engine import (BacktestEngine, Decision, EngineConfig,
                          FutureAccessError)
from futbt.journal import FillRecord, TradeJournal
from futbt.roll import RollEngine
from futbt.taxonomy import PolicyError

from .helpers import close_only_bar, flat_bar, make_bar, make_contract

ES_HALF_SPREAD_PX = 6.25 / 50.0     # 12.50 USD spread on ES -> 0.125 px


def es_universe(gap=10.0, second_lists_late=False):
    """Two ES contracts: ESH6 (expiry month Mar-2026, LTD Mar-18) and ESM6
    (expiry month Jun-2026, LTD Jun-18). Roll: last session before
    Mar-01 = Fri 2026-02-27. Deterministic staircase prices."""
    cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 6, 30))
    sessions = cal.sessions()
    base = 5000.0
    bars_a, bars_b = [], []
    for i, s in enumerate(sessions):
        px = base + 3.0 * i
        if not second_lists_late or s >= dt.date(2026, 3, 2):
            bars_b.append(make_bar(s, px + gap, px + gap + 5, px + gap - 5,
                                   px + gap, v=1000))
        if s <= dt.date(2026, 3, 18):
            bars_a.append(make_bar(s, px, px + 5, px - 5, px, v=1000))
    a = make_contract("ES", "ESH6", 101, dt.date(2026, 3, 18), bars_a)
    b = make_contract("ES", "ESM6", 102, dt.date(2026, 6, 18), bars_b)
    return cal, [a, b]


def es_engine(contracts, cal, cfg=None):
    re = RollEngine("ES", contracts, cal)
    return BacktestEngine("ES", re, re.build_roll_table(),
                          CostBook.for_symbol("ES"),
                          cfg or EngineConfig())


def decisions_prefix(journal, cutoff):
    return [(r.decision_session.isoformat(), r.entry_decision_reason,
             r.direction, r.veto_reason)
            for r in journal.records if r.decision_session <= cutoff]


class TestEntryAndTP(unittest.TestCase):
    def setUp(self):
        self.cal, self.cons = es_universe()
        self.eng = es_engine(self.cons, self.cal)
        self.sessions = self.eng.sessions

    def test_entry_fills_next_open_with_cost_shift(self):
        t0, t1 = dt.date(2026, 1, 5), dt.date(2026, 1, 6)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=6000.0, sl_price=10.0,
            time_exit_sessions=3, reason="r",
            features={"mom": (0.01, ctx.asof)}) if ctx.asof == t0 \
            else Decision(action="none")
        j = self.eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertEqual(rec.decision_session, t0)
        self.assertEqual(rec.entry_fill.session, t1)
        self.assertEqual(rec.entry_fill.fill_timing, "next_open")
        open_px = self.eng._chain[t1].o
        # buy: open + half-spread 0.125 -> ceil to 0.25 tick
        self.assertEqual(rec.entry_fill.price, round(open_px + 0.25, 10)
                         if abs(open_px % 0.25) < 1e-9 else open_px + 0.25)
        self.assertEqual(rec.exit_type, "TIME")
        # cash commissions only (ES complete: 2.24/side), spread in price
        self.assertAlmostEqual(rec.cost_components_total_usd, 4.48, places=9)
        self.assertAlmostEqual(rec.entry_fill.cost_total_usd, 2.24, places=9)

    def test_tp_hit_exits_at_tp_with_sell_shift(self):
        t0 = dt.date(2026, 1, 5)
        t1 = dt.date(2026, 1, 6)
        entry_open = self.eng._chain[t1].o          # staircase open
        tp = round(entry_open + 3.0, 2)             # inside t1 high (+5)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=tp, sl_price=10.0, reason="r",
            features={}) if ctx.asof == t0 else Decision(action="none")
        j = self.eng.run(strat, TradeJournal(0.0))
        recs = [r for r in j.records if r.entry_fill]
        self.assertEqual(len(recs), 1)
        rec = recs[0]
        self.assertEqual(rec.exit_type, "TP")
        self.assertGreaterEqual(self.eng._chain[t1].h, tp)
        self.assertLessEqual(self.eng._chain[t1].l, tp)
        expected_exit = tp - 0.25  # sell shift floor(0.125 -> 0.25)
        self.assertEqual(rec.exit_fill.price, expected_exit)
        gross = (expected_exit - (entry_open + 0.25)) * 50
        self.assertAlmostEqual(rec.gross_pnl_usd, gross, places=9)
        self.assertAlmostEqual(rec.net_pnl_usd, gross - 4.48, places=9)

    def test_time_exit_fills_at_session_close(self):
        t0 = dt.date(2026, 1, 5)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=99999.0, sl_price=1.0,
            time_exit_sessions=4, reason="r", features={}) \
            if ctx.asof == t0 else Decision(action="none")
        j = self.eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertEqual(rec.exit_type, "TIME")
        idx = self.sessions.index(rec.exit_fill.session)
        self.assertEqual(idx, self.sessions.index(t0) + 4)
        self.assertEqual(rec.exit_fill.fill_timing, "session_close")


class TestAmbiguousSameBar(unittest.TestCase):
    def test_both_tp_sl_in_same_bar_flags_ambiguity(self):
        cal, cons = es_universe()
        # overwrite one bar (Jan 7) to straddle both levels
        victim = cal.next_session(dt.date(2026, 1, 6))
        for cd in cons:
            cd.daily_trades = [make_bar(b.t, 6000.0, 6100.0, 4900.0, 6000.0,
                                        v=1000) if b.t == victim else b
                               for b in cd.daily_trades]
        eng = es_engine(cons, cal)
        t0 = dt.date(2026, 1, 5)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=5050.0, sl_price=4950.0,
            reason="r", features={}) if ctx.asof == t0 else Decision("none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertEqual(rec.ambiguity, "AMBIGUOUS_ORDER")
        self.assertEqual(rec.exit_type, "TP_SL_SAME_BAR")
        self.assertIsNone(rec.net_pnl_usd)
        self.assertIsNone(rec.gross_pnl_usd)
        b = rec.scenario_bounds
        self.assertIn("tp_first", b)
        self.assertIn("sl_first", b)
        # ledger booked the worst-case bound (SL), deterministically
        stats = eng.last_run_stats
        self.assertAlmostEqual(
            stats["realized_gross_usd"],
            b["sl_first"] + stats["total_costs_usd"], places=6)
        # summary counts ambiguity; point records exclude it
        self.assertEqual(j.summary()["n_ambiguous"], 1)
        self.assertEqual(len(j.point_pnl_records()), 0)


class TestRollDuringPosition(unittest.TestCase):
    def test_position_follows_roll_with_rebased_stops(self):
        cal, cons = es_universe(gap=10.0)
        eng = es_engine(cons, cal)
        t0 = dt.date(2026, 2, 20)   # well before the Feb-27 roll
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=99999.0, sl_price=1.0,
            time_exit_sessions=25, reason="r", features={}) \
            if ctx.asof == t0 else Decision(action="none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertEqual(len(rec.rolls), 1)
        rv = rec.rolls[0]
        self.assertEqual(rv.session, dt.date(2026, 2, 27))
        self.assertEqual(rv.from_contract, "ESH6")
        self.assertEqual(rv.to_contract, "ESM6")
        self.assertAlmostEqual(rv.raw_gap, 10.0, places=9)
        # position never holds the expired contract past the roll date
        self.assertEqual(rec.entry_fill.local_symbol, "ESH6")
        self.assertEqual(rec.exit_fill.local_symbol, "ESM6")
        # qty preserved across roll
        self.assertEqual(rec.qty, rec.entry_fill.signed_qty)

    def test_forced_exit_when_next_contract_bar_missing(self):
        cal, cons = es_universe(gap=10.0, second_lists_late=True)
        eng = es_engine(cons, cal)
        t0 = dt.date(2026, 2, 20)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=99999.0, sl_price=1.0,
            time_exit_sessions=60, reason="r", features={}) \
            if ctx.asof == t0 else Decision(action="none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertEqual(rec.exit_type, "FORCED_ROLL")
        self.assertEqual(rec.exit_session, dt.date(2026, 2, 27))
        self.assertEqual(rec.exit_fill.local_symbol, "ESH6")
        self.assertIn("first-notice", "".join(rec.notes))


class TestCensoringAndLapse(unittest.TestCase):
    def test_open_at_end_is_right_censored(self):
        cal, cons = es_universe()
        eng = es_engine(cons, cal)
        t0 = self.sessions_last(eng)
        strat = lambda ctx: Decision(
            action="enter_short", tp_price=1.0, sl_price=99999.0,
            reason="r", features={}) if ctx.asof == t0 else Decision("none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertTrue(rec.right_censored)
        self.assertEqual(rec.exit_type, "END_OF_DATA")
        self.assertIsNone(rec.exit_fill)

    def sessions_last(self, eng):
        return eng.sessions[-4]

    def test_order_lapses_on_close_only_bar(self):
        cal, cons = es_universe()
        # make the FILL session (day after the decision) close-only on the
        # front chain -> no tradeable price, order must lapse, not fabricate
        t0 = dt.date(2026, 1, 5)
        victim = cal.next_session(t0)
        cons[0].daily_trades = [
            close_only_bar(b.t, b.c) if b.t == victim else b
            for b in cons[0].daily_trades]
        eng = es_engine(cons, cal)
        strat = lambda ctx: Decision(
            action="enter_long", reason="r",
            features={}) if ctx.asof == t0 else Decision(action="none")
        j = eng.run(strat, TradeJournal(0.0))
        vetoed = [r for r in j.records if r.veto_reason]
        self.assertEqual(len(vetoed), 1)
        self.assertEqual(vetoed[0].veto_reason, "ORDER_LAPSED_CLOSE_ONLY_BAR")
        self.assertEqual([r for r in j.records if r.entry_fill], [])


class TestPITAndDeterminism(unittest.TestCase):
    def test_future_access_raises(self):
        from .helpers import ScriptedStrategy
        cal, cons = es_universe()
        eng = es_engine(cons, cal)
        strat = ScriptedStrategy({})
        strat.abuse_at = dt.date(2026, 1, 8)
        with self.assertRaisesRegex(FutureAccessError, "pinned"):
            eng.run(strat, TradeJournal(0.0))

    def test_same_day_access_allowed(self):
        from .helpers import ScriptedStrategy
        cal, cons = es_universe()
        eng = es_engine(cons, cal)

        def strat(ctx):
            ctx.view.close(ctx.asof)          # legal: decision at close
            ctx.view.closes(ctx.asof, 5)      # legal: trailing window
            return Decision(action="none")
        eng.run(strat, TradeJournal(0.0))

    def test_deterministic_replay_identical_journal(self):
        cal, cons = es_universe()
        script = {}
        for k, s in enumerate(WeekdayCalendar(dt.date(2026, 1, 1),
                                              dt.date(2026, 6, 30)).sessions()):
            if k % 7 == 0:
                script[s] = Decision(action="enter_long", tp_price=10**6,
                                     sl_price=-10**6, time_exit_sessions=3,
                                     reason="cycled", features={})
        from .helpers import ScriptedStrategy
        eng1 = es_engine(cons, cal)
        j1 = eng1.run(ScriptedStrategy(script), TradeJournal(1.0))
        eng2 = es_engine(cons, cal)
        j2 = eng2.run(ScriptedStrategy(script), TradeJournal(1.0))
        self.assertEqual(j1.to_json(), j2.to_json())

    def test_truncation_prefix_determinism(self):
        cal, cons = es_universe()
        cutoff = dt.date(2026, 3, 31)
        script = {}
        for k, s in enumerate(cal.sessions()):
            if k % 5 == 0 and s <= cutoff - dt.timedelta(days=10):
                script[s] = Decision(action="enter_long", tp_price=10**6,
                                     sl_price=-10**6, time_exit_sessions=2,
                                     reason="cycled", features={})
        from .helpers import ScriptedStrategy
        full = es_engine(cons, cal).run(ScriptedStrategy(script),
                                        TradeJournal(0.0))
        trunc = es_engine(cons, cal).run(ScriptedStrategy(script),
                                         TradeJournal(0.0), cutoff=cutoff)
        self.assertEqual(decisions_prefix(full, cutoff),
                         decisions_prefix(trunc, cutoff))

    def test_future_mutation_invariance(self):
        cal, cons = es_universe()
        cutoff = dt.date(2026, 3, 31)
        script = {}
        for k, s in enumerate(cal.sessions()):
            if k % 5 == 0 and s <= cutoff - dt.timedelta(days=10):
                script[s] = Decision(action="enter_short", tp_price=-10**6,
                                     sl_price=10**6, time_exit_sessions=2,
                                     reason="cycled", features={})
        from .helpers import ScriptedStrategy
        base = es_engine(cons, cal).run(ScriptedStrategy(script),
                                        TradeJournal(0.0))
        mut = es_engine(cons, cal).run(
            ScriptedStrategy(script), TradeJournal(0.0), cutoff=cutoff,
            data_after_cutoff_mutate_seed=99)
        self.assertEqual(decisions_prefix(base, cutoff),
                         decisions_prefix(mut, cutoff))


class TestLedgerReconciliation(unittest.TestCase):
    def test_cash_identity_holds_with_costs_and_rolls(self):
        cal, cons = es_universe()
        eng = es_engine(cons, cal)
        script = {}
        for k, s in enumerate(cal.sessions()):
            if k % 9 == 0:
                script[s] = Decision(action="enter_long", tp_price=10**6,
                                     sl_price=-10**6, time_exit_sessions=40,
                                     reason="cycled", features={})
        from .helpers import ScriptedStrategy
        j = eng.run(ScriptedStrategy(script), TradeJournal(0.0))
        st = eng.last_run_stats
        self.assertAlmostEqual(
            st["ledger"]["final"],
            st["ledger"]["initial"] + st["realized_gross_usd"]
            - st["total_costs_usd"], places=6)
        # every closed point record satisfies net = gross - cash costs
        for r in j.point_pnl_records():
            if r.net_pnl_usd is not None:
                self.assertAlmostEqual(
                    r.net_pnl_usd, r.gross_pnl_usd
                    - r.cost_components_total_usd, places=6)


class TestNegativeCLAndSixJ(unittest.TestCase):
    def _cl_engine(self, bars_a, bars_b):
        cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 4, 30))
        a = make_contract("CL", "CLG6", 11, dt.date(2026, 2, 20), bars_a)
        b = make_contract("CL", "CLH6", 12, dt.date(2026, 3, 20), bars_b)
        re = RollEngine("CL", [a, b], cal)
        return BacktestEngine("CL", re, re.build_roll_table(),
                              CostBook.for_symbol("CL"), EngineConfig()), cal

    def test_negative_price_trade_pnl_arithmetic(self):
        cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 4, 30))
        sessions = cal.sessions()
        # contract A dies mid-Feb (expiry month Feb); prices dive negative
        bars_a = []
        for i, s in enumerate(sessions):
            if s > dt.date(2026, 2, 20):
                continue
            px = 30.0 - 0.4 * i          # goes negative by mid-Feb
            if px < 0:
                bars_a.append(make_bar(s, px, px + 1.5, px - 1.5, px, v=500))
            else:
                bars_a.append(make_bar(s, px, px + 1.0, px - 1.0, px, v=500))
        bars_b = [make_bar(s, 30.0 - 0.4 * i + 1.0, 30.0 - 0.4 * i + 2.0,
                           30.0 - 0.4 * i, 30.0 - 0.4 * i + 1.0, v=500)
                  for i, s in enumerate(sessions)
                  if s <= dt.date(2026, 3, 20) or s > dt.date(2026, 4, 1)]
        # simpler: full series for B
        bars_b = [make_bar(s, 30.0 - 0.4 * i + 1.0, 30.0 - 0.4 * i + 2.0,
                           30.0 - 0.4 * i, 30.0 - 0.4 * i + 1.0, v=500)
                  for i, s in enumerate(sessions)]
        eng, cal = self._cl_engine(bars_a, bars_b)
        t0 = dt.date(2026, 2, 2)
        strat = lambda ctx: Decision(
            action="enter_short", tp_price=-10.0, sl_price=60.0,
            time_exit_sessions=15, reason="neg",
            features={}) if ctx.asof == t0 else Decision("none")
        j = eng.run(strat, TradeJournal(0.0))
        recs = [r for r in j.records if r.entry_fill]
        self.assertTrue(recs)
        for r in recs:
            if r.gross_pnl_usd is not None:
                # gross matches arithmetic difference x 1000 bbl
                self.assertAlmostEqual(
                    r.gross_pnl_usd,
                    (r.exit_fill.price - r.entry_fill.price) * 1000
                    * r.entry_fill.signed_qty, places=6)

    def test_6j_tick_economics_and_orientation_guard(self):
        cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 4, 30))
        sessions = cal.sessions()
        px0 = 0.006330
        bars_a = [make_bar(s, px0, px0 + 0.00002, px0 - 0.00002, px0, v=300)
                  for s in sessions if s <= dt.date(2026, 2, 18)]
        bars_b = [make_bar(s, px0 + 0.00001, px0 + 0.00003, px0 - 0.00001,
                           px0 + 0.00001, v=300) for s in sessions]
        a = make_contract("6J", "6JG6", 21, dt.date(2026, 2, 18), bars_a)
        b = make_contract("6J", "6JH6", 22, dt.date(2026, 3, 18), bars_b)
        re = RollEngine("6J", [a, b], cal)
        eng = BacktestEngine("6J", re, re.build_roll_table(),
                             CostBook.for_symbol("6J"), EngineConfig())
        t0 = dt.date(2026, 1, 5)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=0.006340, sl_price=0.006300,
            time_exit_sessions=10, reason="jpy",
            features={}) if ctx.asof == t0 else Decision("none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        # fills live on the 5e-7 tick grid (no inversion to ~157 anywhere)
        for f in (rec.entry_fill, rec.exit_fill):
            self.assertLess(f.price, 0.05)
            self.assertAlmostEqual(f.price / 5e-7, round(f.price / 5e-7),
                                   places=6)
        if rec.gross_pnl_usd is not None:
            self.assertAlmostEqual(
                rec.gross_pnl_usd,
                (rec.exit_fill.price - rec.entry_fill.price) * 12_500_000,
                places=6)

    def test_6j_inverted_data_rejected_by_engine(self):
        cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 4, 30))
        sessions = cal.sessions()
        bars_a = [make_bar(s, 157.2, 157.4, 157.0, 157.2, v=300)
                  for s in sessions if s <= dt.date(2026, 2, 18)]
        bars_b = [make_bar(s, 157.3, 157.5, 157.1, 157.3, v=300)
                  for s in sessions]
        a = make_contract("6J", "6JG6", 21, dt.date(2026, 2, 18), bars_a)
        b = make_contract("6J", "6JH6", 22, dt.date(2026, 3, 18), bars_b)
        re = RollEngine("6J", [a, b], cal)
        eng = BacktestEngine("6J", re, re.build_roll_table(),
                             CostBook.for_symbol("6J"), EngineConfig())
        t0 = dt.date(2026, 1, 5)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=160.0, sl_price=150.0,
            reason="bad", features={}) if ctx.asof == t0 else Decision("none")
        with self.assertRaisesRegex(PolicyError, "inverted"):
            eng.run(strat, TradeJournal(0.0))


class TestEngineConfigGuards(unittest.TestCase):
    def test_bad_fill_timing_refused(self):
        cal, cons = es_universe()
        with self.assertRaises(PolicyError):
            es_engine(cons, cal, EngineConfig(fill_timing="mid"))

    def test_non_worst_case_ambiguous_booking_refused(self):
        cal, cons = es_universe()
        with self.assertRaises(PolicyError):
            es_engine(cons, cal, EngineConfig(ambiguous_booking="optimistic"))


class TestCloseOnlyNeverFills(unittest.TestCase):
    """Audit M3 regression: close-only (settlement-derived, v=0, o=h=l=c)
    bars can NEVER fill on ANY path — entries lapse; TP/SL never trigger;
    TIME/MANUAL exits wait for a tradeable session; roll legs wait for a
    tradeable bar pair; otherwise the record right-censors."""

    def test_sl_never_triggers_on_close_only_bar(self):
        # the close-only bar's settlement (5060) sits ABOVE the short's stop
        # (5050): old code would book an intrabar SL fill at a settlement
        # price on 2026-01-07; the law forbids any touch without a real
        # high/low — real neighbor bars never reach the stop
        cal, cons = es_universe()
        t0 = dt.date(2026, 1, 5)
        victim = cal.next_session(cal.next_session(t0))   # 2026-01-07
        cons[0].daily_trades = [
            close_only_bar(b.t, 5060.0) if b.t == victim else b
            for b in cons[0].daily_trades]
        eng = es_engine(cons, cal)
        strat = lambda ctx: Decision(
            action="enter_short", tp_price=1.0, sl_price=5050.0,
            time_exit_sessions=4, reason="r",
            features={}) if ctx.asof == t0 else Decision("none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertEqual(rec.exit_type, "TIME")           # SL did not fire
        self.assertNotEqual(rec.exit_session, victim)     # no fill on victim
        self.assertGreater(rec.exit_session, victim)

    def test_time_exit_deferred_off_close_only_bar(self):
        cal, cons = es_universe()
        t0 = dt.date(2026, 1, 5)
        victim = cal.next_session(cal.next_session(t0))   # 2026-01-07
        cons[0].daily_trades = [
            close_only_bar(b.t, b.c) if b.t == victim else b
            for b in cons[0].daily_trades]
        eng = es_engine(cons, cal)
        strat = lambda ctx: Decision(
            action="enter_long", time_exit_sessions=2, reason="r",
            features={}) if ctx.asof == t0 else Decision("none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertEqual(rec.exit_type, "TIME")
        self.assertEqual(rec.exit_fill.session,
                         cal.next_session(victim))        # waited one session
        self.assertIn("deferred", " ".join(rec.notes))

    def test_manual_exit_deferred_to_next_tradeable_open(self):
        cal, cons = es_universe()
        t0 = dt.date(2026, 1, 5)
        victim = cal.next_session(cal.next_session(t0))   # 2026-01-07
        nxt = cal.next_session(victim)                    # 2026-01-08
        cons[0].daily_trades = [
            close_only_bar(b.t, b.c) if b.t == victim else b
            for b in cons[0].daily_trades]
        eng = es_engine(cons, cal)
        script = {t0: Decision(action="enter_long", reason="r", features={}),
                  victim: Decision(action="exit", reason="out")}
        from .helpers import ScriptedStrategy
        j = eng.run(ScriptedStrategy(script), TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertEqual(rec.exit_type, "MANUAL")
        self.assertEqual(rec.exit_fill.session, nxt)
        self.assertEqual(rec.exit_fill.fill_timing, "next_open")
        expected = round(eng._chain[nxt].o - 0.25, 10)    # sell shift
        self.assertAlmostEqual(rec.exit_fill.price, expected, places=9)
        self.assertIn("close-only", " ".join(rec.notes))

    def test_roll_legs_never_fill_on_close_only_bar(self):
        # scheduled roll session 2026-02-27 has a close-only OLD bar: the
        # roll must NOT fill legs at settlement prices — it waits for the
        # first session with a tradeable bar pair (2026-03-02 here)
        cal, cons = es_universe(gap=10.0)
        roll_day = dt.date(2026, 2, 27)
        cons[0].daily_trades = [
            close_only_bar(b.t, b.c) if b.t == roll_day else b
            for b in cons[0].daily_trades]
        eng = es_engine(cons, cal)
        t0 = dt.date(2026, 2, 20)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=99999.0, sl_price=1.0,
            time_exit_sessions=25, reason="r", features={}) \
            if ctx.asof == t0 else Decision("none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertEqual(len(rec.rolls), 1)
        rv = rec.rolls[0]
        self.assertEqual(rv.session, cal.next_session(roll_day))
        self.assertEqual(rv.from_contract, "ESH6")
        self.assertEqual(rv.to_contract, "ESM6")
        self.assertAlmostEqual(rv.raw_gap, 10.0, places=9)
        self.assertIn("deferred", " ".join(rec.notes))
        self.assertEqual(rec.exit_fill.local_symbol, "ESM6")

    def test_censored_when_no_tradeable_bar_ever_again(self):
        # entry fills on a real bar; every later bar of the held contract is
        # close-only -> TP/SL silent, time exit deferred forever, roll never
        # executes -> right-censored with the unexecuted intents disclosed
        cal, cons = es_universe(gap=10.0)
        fill_day = dt.date(2026, 1, 6)
        cons[0].daily_trades = [
            close_only_bar(b.t, b.c) if b.t > fill_day else b
            for b in cons[0].daily_trades]
        eng = es_engine(cons, cal)
        t0 = dt.date(2026, 1, 5)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=99999.0, sl_price=1.0,
            time_exit_sessions=5, reason="r", features={}) \
            if ctx.asof == t0 else Decision("none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertTrue(rec.right_censored)
        self.assertEqual(rec.exit_type, "END_OF_DATA")
        self.assertIsNone(rec.exit_fill)
        self.assertEqual(rec.rolls, [])
        notes = " ".join(rec.notes)
        self.assertIn("roll scheduled 2026-02-27 never executed", notes)
        self.assertIn("time exit never executed", notes)

    def test_zero_fills_when_whole_universe_is_close_only(self):
        # the law, end to end: with ONLY settlement-derived bars nothing can
        # fill anywhere — entries lapse, no exits, no roll legs, no costs
        cal, cons = es_universe(gap=10.0)
        for cd in cons:
            cd.daily_trades = [close_only_bar(b.t, b.c)
                               for b in cd.daily_trades]
        eng = es_engine(cons, cal)
        t0 = dt.date(2026, 1, 5)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=99999.0, sl_price=1.0,
            time_exit_sessions=3, reason="r", features={}) \
            if ctx.asof == t0 else Decision("none")
        j = eng.run(strat, TradeJournal(0.0))
        self.assertTrue(j.records)
        for r in j.records:
            self.assertEqual(r.veto_reason, "ORDER_LAPSED_CLOSE_ONLY_BAR")
            self.assertIsNone(r.entry_fill)
            self.assertIsNone(r.exit_fill)
            self.assertEqual(r.rolls, [])
        self.assertEqual(eng.last_run_stats["realized_gross_usd"], 0.0)
        self.assertEqual(eng.last_run_stats["total_costs_usd"], 0.0)

    def test_fill_record_on_close_only_bar_refused(self):
        # structural tripwire: a FillRecord stamped close-only cannot even
        # be constructed (and so can never enter a journal)
        with self.assertRaisesRegex(PolicyError, "close-only"):
            FillRecord(session=dt.date(2026, 1, 6), local_symbol="ESH6",
                       conid=101, signed_qty=1, price=5000.0,
                       cost_breakdown={}, cost_total_usd=0.0,
                       is_close_only_bar=True)


if __name__ == "__main__":
    unittest.main()
