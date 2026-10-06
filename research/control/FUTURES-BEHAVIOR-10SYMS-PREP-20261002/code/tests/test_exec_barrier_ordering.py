"""EXEC-FIX R3: intraday barriers vs end-of-session roll ordering.

Reproduced on base eae8c3d2 (2026-10-02): the engine rolled an open
position at the session close BEFORE evaluating intraday TP/SL, then
checked the OLD position's stop — rebased by the raw gap onto the NEW
contract — against the OLD contract's bar, and filled on the NEW
contract. Synthetic repro (roll scheduled Fri 2026-02-27, end-of-day):
  old ESH6: Feb26 O100/H101/L99/C100 (entry 2026-02-26 @100.25, long
  TP150 SL95); Feb27 old O110/H115/L90/C112; new ESM6 Feb27
  O200/H205/L198/C202.
  Base engine rolled first (gap +90 -> SL rebased 95->185), then SL
  "fired" at 184.75 on the NEW contract — outside the new bar's entire
  range [198,205] (and outside the old bar's [90,115] too), with the old
  bar's low checked against a gap-rebased level: three frame mixes.

Law after fix: barriers are evaluated on the OLD position/contract
BEFORE the end-of-session roll, using old-bar extrema only; if stopped,
no roll executes; MAE/MFE are computed per contract segment on legal
intervals (the new contract's roll-session bar belongs to the OLD
segment's day — the new position's fill happens at that close, so its
bars only count from the NEXT session).
"""
import datetime as dt
import unittest

from futbt.calendarx import WeekdayCalendar
from futbt.costs import CostBook
from futbt.engine import BacktestEngine, Decision, EngineConfig
from futbt.journal import TradeJournal
from futbt.roll import RollEngine

from .helpers import make_bar, make_contract


def build_universe(old_feb26, old_feb27, new_feb27):
    """ESH6/ESM6 with the roll at the 2026-02-27 close; precise bars on
    Feb 26/27, quiet staircase elsewhere."""
    cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 6, 30))
    sessions = cal.sessions()
    bars_a, bars_b = [], []
    for i, s in enumerate(sessions):
        px = 5000.0 + 3.0 * i
        if s == dt.date(2026, 2, 26):
            bars_a.append(make_bar(s, *old_feb26, v=1000))
        elif s == dt.date(2026, 2, 27):
            bars_a.append(make_bar(s, *old_feb27, v=1000))
        elif s <= dt.date(2026, 3, 18):
            bars_a.append(make_bar(s, px, px + 5, px - 5, px, v=1000))
        if s == dt.date(2026, 2, 27):
            bars_b.append(make_bar(s, *new_feb27, v=1000))
        elif s >= dt.date(2026, 1, 2):
            bars_b.append(make_bar(s, px + 10, px + 15, px + 5, px + 10,
                                   v=1000))
    a = make_contract("ES", "ESH6", 101, dt.date(2026, 3, 18), bars_a)
    b = make_contract("ES", "ESM6", 102, dt.date(2026, 6, 18), bars_b)
    return cal, [a, b]


def make_engine(cal, cons):
    re = RollEngine("ES", cons, cal)
    return BacktestEngine("ES", re, re.build_roll_table(),
                          CostBook.for_symbol("ES"), EngineConfig())


class TestBarrierBeforeRoll(unittest.TestCase):
    def setUp(self):
        self.cal, self.cons = build_universe(
            old_feb26=(100.0, 101.0, 99.0, 100.0),
            old_feb27=(110.0, 115.0, 90.0, 112.0),
            new_feb27=(200.0, 205.0, 198.0, 202.0))
        self.eng = make_engine(self.cal, self.cons)

    def test_sl_evaluated_on_old_contract_before_roll(self):
        t0 = dt.date(2026, 2, 25)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=150.0, sl_price=95.0,
            time_exit_sessions=10, reason="r3",
            features={}) if ctx.asof == t0 else Decision(action="none")
        j = self.eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        # stopped on the OLD contract at the old-bar stop reference: the
        # old bar (O110/L90) touches SL95 -> fill 95 - 0.25 = 94.75,
        # INSIDE the old bar's range; NO roll executed afterwards
        self.assertEqual(rec.exit_type, "SL")
        self.assertEqual(rec.exit_session, dt.date(2026, 2, 27))
        self.assertEqual(rec.exit_fill.conid, 101)
        self.assertEqual(rec.exit_fill.local_symbol, "ESH6")
        self.assertEqual(rec.exit_fill.price, 94.75)
        self.assertGreaterEqual(rec.exit_fill.price, 90.0)
        self.assertLessEqual(rec.exit_fill.price, 115.0)
        self.assertEqual(rec.rolls, [])          # stopped -> no roll
        # base bug produced: exit on ESM6 conid 102 at 184.75 — outside
        # the new bar's [198,205] entirely — after rolling first
        self.assertAlmostEqual(
            rec.gross_pnl_usd, (94.75 - 100.25) * 50.0, places=6)

    def test_no_frame_mixing_in_mae_mfe(self):
        t0 = dt.date(2026, 2, 25)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=150.0, sl_price=95.0,
            time_exit_sessions=10, reason="r3",
            features={}) if ctx.asof == t0 else Decision(action="none")
        j = self.eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        segs = rec.mae_mfe_segments
        # exactly ONE segment: the position stopped before the roll
        self.assertEqual(len(segs), 1)
        self.assertEqual(segs[0]["conid"], 101)
        self.assertEqual(segs[0]["avg_entry_price"], 100.25)
        # MAE bounded by the old bar's low on the entry frame — never the
        # new contract's ~200 prices (base produced ~ -5600 cross-frame)
        self.assertAlmostEqual(segs[0]["mae_usd"],
                               (90.0 - 100.25) * 50.0, places=6)
        self.assertAlmostEqual(segs[0]["mfe_usd"],
                               (115.0 - 100.25) * 50.0, places=6)
        self.assertEqual(segs[0]["first_bar_session"],
                         dt.date(2026, 2, 26).isoformat())
        self.assertEqual(segs[0]["last_bar_session"],
                         dt.date(2026, 2, 27).isoformat())


class TestRollSessionBarrierThenRoll(unittest.TestCase):
    """When no barrier fires on the roll session, the roll executes at
    that close and the NEW position's segments start on the NEXT session
    (the roll fills at the close: the roll-session bar of the new
    contract is BEFORE the fill timestamp and must not count)."""

    def test_rolled_position_mae_mfe_excludes_roll_session_new_bar(self):
        cal, cons = build_universe(
            old_feb26=(100.0, 101.0, 99.0, 100.0),
            old_feb27=(110.0, 111.0, 109.0, 110.0),   # no barrier touch
            new_feb27=(200.0, 205.0, 198.0, 202.0))
        eng = make_engine(cal, cons)
        t0 = dt.date(2026, 2, 25)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=10**9, sl_price=1.0,
            time_exit_sessions=4, reason="r3-roll",
            features={}) if ctx.asof == t0 else Decision(action="none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertEqual(len(rec.rolls), 1)
        segs = rec.mae_mfe_segments
        self.assertEqual(len(segs), 2)
        # segment 2 = ESM6 starting from the roll fill price; its first
        # counted bar is AFTER the roll session (2026-03-02), never the
        # roll session's own [198,205] bar
        self.assertEqual(segs[1]["conid"], 102)
        self.assertEqual(segs[1]["first_bar_session"],
                         dt.date(2026, 3, 2).isoformat())
        self.assertEqual(segs[1]["last_bar_session"],
                         rec.exit_session.isoformat())
        # the new segment entry is the roll fill (202 + 0.25 shift)
        self.assertAlmostEqual(segs[1]["avg_entry_price"], 202.25, places=9)
        # segment 2 excursions come ONLY from ESM6 bars after the roll:
        # each within that segment's own bar extremes
        for seg, bars in ((segs[1], None),):
            self.assertLessEqual(seg["mae_usd"], 0.0)
            self.assertGreaterEqual(seg["mfe_usd"], 0.0)
        # full lifecycle gross still accumulates both segments (R2)
        self.assertAlmostEqual(
            rec.gross_pnl_usd,
            sum(s["gross_usd"] for s in rec.gross_segments), places=6)
        self.assertEqual(len(rec.gross_segments), 2)

    def test_tp_on_roll_session_exits_old_contract_no_roll(self):
        # old Feb27 bar reaches the TP: exit happens on the OLD contract
        # BEFORE the roll -> no roll event, no rebase
        cal, cons = build_universe(
            old_feb26=(100.0, 101.0, 99.0, 100.0),
            old_feb27=(110.0, 130.0, 105.0, 125.0),
            new_feb27=(200.0, 205.0, 198.0, 202.0))
        eng = make_engine(cal, cons)
        t0 = dt.date(2026, 2, 25)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=120.0, sl_price=1.0,
            reason="r3-tp", features={}) if ctx.asof == t0 \
            else Decision(action="none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertEqual(rec.exit_type, "TP")
        self.assertEqual(rec.exit_session, dt.date(2026, 2, 27))
        self.assertEqual(rec.exit_fill.conid, 101)
        self.assertEqual(rec.exit_fill.local_symbol, "ESH6")
        # limit semantics: reference = barrier (open 110 < TP 120)
        self.assertEqual(rec.exit_fill.price, 119.75)
        self.assertEqual(rec.rolls, [])
        # base rolled first (gap +90 -> TP rebased to 210) and the old
        # bar's 130 never reached it -> different (wrong) path entirely


if __name__ == "__main__":
    unittest.main()
