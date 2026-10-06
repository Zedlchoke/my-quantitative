"""EXEC-FIX R4: gap-stop and limit (TP) fill semantics.

Reproduced on base eae8c3d2 (2026-10-02): a long with SL95 facing a bar
  O80/H90/L70/C85 exited at 94.75 — above the entire bar (open 80, high
  90). The base engine filled stop-market orders AT the barrier and then
  applied the adverse cost shift, producing fills outside the bar range.

Laws after fix:
  * SL (stop-market): trigger reference = the open when the bar gaps
    beyond the barrier (long stop: min(open, sl); short stop:
    max(open, sl)); the adverse cost shift is then applied — a long stop
    can NEVER fill above the open, a short stop never below it;
  * TP (limit): fills at the barrier or better — a long TP sell takes
    max(open, tp) (opening above the limit = price improvement), a short
    TP buy takes min(open, tp); never worse than the barrier;
  * same-bar TP+SL -> AMBIGUOUS_ORDER with gap-aware scenario bounds;
    TP-vs-SL order is NEVER inferred from OHLC alone;
  * a barrier already beyond at entry fills against the open.
"""
import datetime as dt
import unittest

from futbt.calendarx import WeekdayCalendar
from futbt.costs import CostBook
from futbt.engine import BacktestEngine, Decision, EngineConfig
from futbt.journal import TradeJournal
from futbt.roll import RollEngine

from .helpers import make_bar, make_contract


def one_contract_engine(bars):
    """Single ES contract (no roll possible): the chain is exactly bars."""
    cal = WeekdayCalendar(bars[0].t, bars[-1].t)
    a = make_contract("ES", "ESH6", 101, bars[-1].t, bars)
    re = RollEngine("ES", [a], cal)
    return BacktestEngine("ES", re, re.build_roll_table(),
                          CostBook.for_symbol("ES"), EngineConfig())


def run_decision(eng, t0, **kw):
    kw.setdefault("action", "enter_long")
    kw.setdefault("reason", "r4")
    kw.setdefault("features", {})
    strat = lambda ctx: Decision(**kw) if ctx.asof == t0 \
        else Decision(action="none")
    j = eng.run(strat, TradeJournal(0.0))
    recs = [r for r in j.records if r.entry_fill]
    return recs[0] if recs else None


def bars_jan(o1, h1, l1, c1):
    """Jan 5 (decision), Jan 6 entry bar O100/H101/L99, Jan 7 custom."""
    return [make_bar(dt.date(2026, 1, 5), 100.5, 101, 99.5, 100.0, v=1000),
            make_bar(dt.date(2026, 1, 6), 100.0, 101.0, 99.0, 100.5, v=1000),
            make_bar(dt.date(2026, 1, 7), o1, h1, l1, c1, v=1000),
            make_bar(dt.date(2026, 1, 8), 100.0, 101.0, 99.0, 100.5, v=1000)]


class TestGapStopFills(unittest.TestCase):
    def test_long_stop_gaps_down_fills_at_open_not_barrier(self):
        eng = one_contract_engine(bars_jan(80.0, 90.0, 70.0, 85.0))
        rec = run_decision(eng, dt.date(2026, 1, 5), tp_price=10**9,
                           sl_price=95.0)
        self.assertEqual(rec.exit_type, "SL")
        self.assertEqual(rec.exit_session, dt.date(2026, 1, 7))
        # stop reference = min(open=80, sl=95) = 80; adverse shift 0.25
        self.assertEqual(rec.exit_fill.price, 79.75)
        # never above the open for a long stop; inside the bar range
        self.assertLessEqual(rec.exit_fill.price, 80.0)
        self.assertGreaterEqual(rec.exit_fill.price, 70.0)
        self.assertLessEqual(rec.exit_fill.price, 90.0)
        # base bug: 94.75 — outside the entire bar (O80/H90/L70/C85)
        self.assertAlmostEqual(rec.gross_pnl_usd, (79.75 - 100.25) * 50.0,
                               places=6)

    def test_short_stop_gaps_up_fills_at_open_not_barrier(self):
        bars = [make_bar(dt.date(2026, 1, 5), 100.5, 101, 99.5, 100.0,
                         v=1000),
                make_bar(dt.date(2026, 1, 6), 100.0, 101.0, 99.0, 100.5,
                         v=1000),
                make_bar(dt.date(2026, 1, 7), 120.0, 125.0, 115.0, 122.0,
                         v=1000),
                make_bar(dt.date(2026, 1, 8), 100.0, 101.0, 99.0, 100.5,
                         v=1000)]
        eng = one_contract_engine(bars)
        strat = lambda ctx: Decision(
            action="enter_short", tp_price=-10**9, sl_price=105.0,
            reason="r4s", features={}) if ctx.asof == dt.date(2026, 1, 5) \
            else Decision(action="none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertEqual(rec.exit_type, "SL")
        # short entry fills 100 - 0.25 = 99.75; stop reference =
        # max(open=120, sl=105) = 120; buy shift +0.25 -> 120.25,
        # never BELOW the open for a short stop
        self.assertEqual(rec.exit_fill.price, 120.25)
        self.assertGreaterEqual(rec.exit_fill.price, 120.0)
        self.assertLessEqual(rec.exit_fill.price, 125.0)
        self.assertAlmostEqual(rec.gross_pnl_usd, (99.75 - 120.25) * 50.0,
                               places=6)

    def test_long_stop_no_gap_fills_at_barrier(self):
        # open 96 above SL 95: intrabar touch -> barrier reference
        eng = one_contract_engine(bars_jan(96.0, 97.0, 90.0, 94.0))
        rec = run_decision(eng, dt.date(2026, 1, 5), tp_price=10**9,
                           sl_price=95.0)
        self.assertEqual(rec.exit_type, "SL")
        self.assertEqual(rec.exit_fill.price, 94.75)   # 95 - 0.25 shift
        self.assertLessEqual(rec.exit_fill.price, 96.0)


class TestTakeProfitLimitSemantics(unittest.TestCase):
    def test_long_tp_gap_up_fills_at_open_price_improvement(self):
        # bar opens ABOVE the TP: a sell limit fills at the open (better
        # than the barrier), never at the barrier below the open
        eng = one_contract_engine(bars_jan(120.0, 125.0, 115.0, 122.0))
        rec = run_decision(eng, dt.date(2026, 1, 5), tp_price=110.0,
                           sl_price=1.0)
        self.assertEqual(rec.exit_type, "TP")
        self.assertEqual(rec.exit_session, dt.date(2026, 1, 7))
        # reference = max(open=120, tp=110) = 120; sell shift 0.25
        self.assertEqual(rec.exit_fill.price, 119.75)
        # limit law: market reference at-or-better than the barrier
        self.assertGreaterEqual(rec.exit_fill.price + 0.25, 110.0)
        self.assertAlmostEqual(rec.gross_pnl_usd, (119.75 - 100.25) * 50.0,
                               places=6)

    def test_long_tp_intrabar_touch_fills_at_barrier(self):
        eng = one_contract_engine(bars_jan(99.0, 110.0, 98.0, 105.0))
        rec = run_decision(eng, dt.date(2026, 1, 5), tp_price=105.0,
                           sl_price=1.0)
        self.assertEqual(rec.exit_type, "TP")
        self.assertEqual(rec.exit_fill.price, 104.75)  # 105 - 0.25 shift

    def test_short_tp_gap_down_fills_at_open(self):
        bars = [make_bar(dt.date(2026, 1, 5), 100.5, 101, 99.5, 100.0,
                         v=1000),
                make_bar(dt.date(2026, 1, 6), 100.0, 101.0, 99.0, 100.5,
                         v=1000),
                make_bar(dt.date(2026, 1, 7), 80.0, 90.0, 70.0, 85.0,
                         v=1000)]
        eng = one_contract_engine(bars)
        strat = lambda ctx: Decision(
            action="enter_short", tp_price=95.0, sl_price=10**9,
            reason="r4s", features={}) if ctx.asof == dt.date(2026, 1, 5) \
            else Decision(action="none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertEqual(rec.exit_type, "TP")
        # short entry 99.75; buy-to-cover reference = min(open=80, tp=95)
        # = 80 (price improvement), +0.25 buy shift
        self.assertEqual(rec.exit_fill.price, 80.25)
        self.assertAlmostEqual(rec.gross_pnl_usd, (99.75 - 80.25) * 50.0,
                               places=6)


class TestEntryBeyondBarrier(unittest.TestCase):
    def test_sl_already_beyond_at_entry_fills_against_open(self):
        # long entry fills 100.25 while SL sits at 101 (ABOVE the fill):
        # the stop is triggered at entry; fill reference = the open 100
        eng = one_contract_engine(bars_jan(100.0, 101.0, 99.0, 100.5))
        rec = run_decision(eng, dt.date(2026, 1, 5), tp_price=10**9,
                           sl_price=101.0)
        self.assertEqual(rec.exit_type, "SL")
        self.assertEqual(rec.exit_session, dt.date(2026, 1, 6))
        self.assertEqual(rec.exit_fill.price, 99.75)   # min(o=100, sl=101)
        self.assertAlmostEqual(rec.gross_pnl_usd, (99.75 - 100.25) * 50.0,
                               places=6)

    def test_tp_at_or_below_open_fills_against_open(self):
        # TP 100.0 == the entry bar's open: limit sells immediately at the
        # open reference (100), not below it
        eng = one_contract_engine(bars_jan(100.0, 101.0, 99.0, 100.5))
        rec = run_decision(eng, dt.date(2026, 1, 5), tp_price=100.0,
                           sl_price=1.0)
        self.assertEqual(rec.exit_type, "TP")
        self.assertEqual(rec.exit_session, dt.date(2026, 1, 6))
        self.assertEqual(rec.exit_fill.price, 99.75)
        self.assertAlmostEqual(rec.gross_pnl_usd, (99.75 - 100.25) * 50.0,
                               places=6)


class TestSameBarAmbiguityWithGap(unittest.TestCase):
    def test_gap_open_with_both_barriers_touched_stays_ambiguous(self):
        # open 80 gaps below SL 95; high 110 crosses TP 105: both touched
        # in one bar -> AMBIGUOUS_ORDER, never an invented order
        eng = one_contract_engine(bars_jan(80.0, 110.0, 70.0, 85.0))
        rec = run_decision(eng, dt.date(2026, 1, 5), tp_price=105.0,
                           sl_price=95.0)
        self.assertEqual(rec.ambiguity, "AMBIGUOUS_ORDER")
        self.assertEqual(rec.exit_type, "TP_SL_SAME_BAR")
        self.assertIsNone(rec.net_pnl_usd)
        self.assertIsNone(rec.gross_pnl_usd)
        b = rec.scenario_bounds
        self.assertIn("tp_first", b)
        self.assertIn("sl_first", b)
        # gap-aware scenario bounds:
        #   tp_first: TP reference = max(o=80, tp=105) = 105 -> 104.75
        #   sl_first: SL reference = min(o=80, sl=95) = 80 -> 79.75
        self.assertAlmostEqual(b["tp_first"],
                               (104.75 - 100.25) * 50 - 4.48, places=6)
        self.assertAlmostEqual(b["sl_first"],
                               (79.75 - 100.25) * 50 - 4.48, places=6)
        self.assertGreater(b["tp_first"], b["sl_first"])
        # ledger booked the deterministic worst case (sl_first scenario)
        st = eng.last_run_stats
        self.assertAlmostEqual(st["realized_gross_usd"],
                               (79.75 - 100.25) * 50, places=6)
        self.assertAlmostEqual(rec.ledger_booked_gross_usd,
                               (79.75 - 100.25) * 50, places=6)

    def test_ambiguity_never_resolved_from_ohlc(self):
        # symmetric straddle, no gap: same law, bounds at the barriers
        eng = one_contract_engine(bars_jan(100.0, 110.0, 90.0, 100.0))
        rec = run_decision(eng, dt.date(2026, 1, 5), tp_price=105.0,
                           sl_price=95.0)
        self.assertEqual(rec.ambiguity, "AMBIGUOUS_ORDER")
        b = rec.scenario_bounds
        self.assertAlmostEqual(b["tp_first"],
                               (104.75 - 100.25) * 50 - 4.48, places=6)
        self.assertAlmostEqual(b["sl_first"],
                               (94.75 - 100.25) * 50 - 4.48, places=6)
        self.assertEqual(eng.last_run_stats["journal_summary"]
                         ["n_ambiguous"], 1)


if __name__ == "__main__":
    unittest.main()
