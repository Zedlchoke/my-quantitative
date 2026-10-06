"""EXEC-FIX R2: roll gross PnL must accumulate into the journal lifecycle.

Reproduced on base eae8c3d2 (2026-10-02) with the standard es_universe
fixture (roll scheduled Fri 2026-02-27, gap +10):
  decision 2026-02-24 -> entry fill 2026-02-25 @5120.25 -> roll leg old
  2026-02-27 @5113.75 (segment gross +275) -> new contract @5136.25 ->
  TIME exit 2026-03-04 @5144.75 (segment gross +425).
  Ledger gross = 700, journal gross = 425 (the 275 first-contract segment
  vanished); net 691.04 vs 416.04 — missing exactly 275.

Law after fix: every contract segment (roll legs incl. roll fees) is
accumulated into the journal record; the ledger reconciles against an
INDEPENDENT cash accounting recomputed from journal records, not against
its own event log; per-bar reconciliation covers journal <-> cash <->
events <-> inventory <-> MTM.
"""
import datetime as dt
import unittest

from futbt.engine import Decision
from futbt.journal import TradeJournal

from .test_engine import es_engine, es_universe


def roll_trade_engine():
    cal, cons = es_universe()
    eng = es_engine(cons, cal)
    t0 = dt.date(2026, 2, 24)
    strat = lambda ctx: Decision(
        action="enter_long", tp_price=10**9, sl_price=-10**9,
        time_exit_sessions=6, reason="roll-lifecycle",
        features={}) if ctx.asof == t0 else Decision(action="none")
    return eng, strat


class TestRollGrossInJournalLifecycle(unittest.TestCase):
    def setUp(self):
        self.eng, self.strat = roll_trade_engine()
        self.j = self.eng.run(self.strat, TradeJournal(0.0))
        self.rec = [r for r in self.j.records if r.entry_fill][0]
        self.stats = self.eng.last_run_stats

    def test_journal_gross_equals_full_lifecycle_gross(self):
        # ledger truth
        self.assertAlmostEqual(self.stats["realized_gross_usd"], 700.0,
                               places=6)
        # journal record must carry the FULL gross incl. the roll segment
        # (base bug: 425 — the first-contract segment was dropped)
        self.assertAlmostEqual(self.rec.gross_pnl_usd, 700.0, places=6)
        # net = gross - 4 fill legs x $2.24
        self.assertAlmostEqual(self.rec.net_pnl_usd, 700.0 - 8.96, places=6)

    def test_gross_segments_recorded_per_contract_leg(self):
        segs = self.rec.gross_segments
        self.assertEqual(len(segs), 2)
        self.assertEqual([s["kind"] for s in segs],
                         ["roll_leg_old_contract", "exit"])
        # segment arithmetic from the recorded fills
        entry = self.rec.entry_fill
        roll = self.rec.rolls[0]
        exit_f = self.rec.exit_fill
        new_entry_px = self.rec.mae_mfe_segments[1]["avg_entry_price"]
        seg1 = (segs[0]["fill_price"] - entry.price) * 50 * entry.signed_qty
        seg2 = (exit_f.price - new_entry_px) * 50 * entry.signed_qty
        self.assertAlmostEqual(segs[0]["gross_usd"], seg1, places=6)
        self.assertAlmostEqual(segs[1]["gross_usd"], seg2, places=6)
        self.assertAlmostEqual(segs[0]["gross_usd"]
                               + segs[1]["gross_usd"], 700.0, places=6)
        # segments stay on their own contract frames
        self.assertEqual(segs[0]["conid"], entry.conid)
        self.assertEqual(segs[1]["conid"], exit_f.conid)
        self.assertNotEqual(segs[0]["conid"], segs[1]["conid"])
        self.assertEqual(segs[0]["session"], roll.session.isoformat())

    def test_ledger_reconciles_against_independent_journal_accounting(self):
        ir = self.stats["independent_reconciliation"]
        self.assertTrue(ir["reconciled"])
        # journal-recomputed cash identity equals the ledger's final cash
        self.assertAlmostEqual(
            ir["cash_final_usd"],
            self.stats["ledger"]["initial"] + ir["journal_gross_usd"]
            - ir["journal_costs_usd"], places=6)
        self.assertAlmostEqual(ir["journal_gross_usd"], 700.0, places=6)
        self.assertAlmostEqual(ir["journal_costs_usd"], 8.96, places=6)
        self.assertAlmostEqual(ir["ledger_realize_usd"], 700.0, places=6)
        # per-bar reconciliation ran on every replayed session
        self.assertEqual(ir["per_bar_checks"], self.stats["sessions"])

    def test_roll_gap_not_double_counted_as_transaction_cost(self):
        """The raw roll gap is borne ONCE through raw-contract segment
        accounting; it must never ALSO appear as a cash 'roll cost'. The
        only cash roll costs are the two fill legs' commissions."""
        rec = self.rec
        st = self.stats
        # cash costs = 4 fill legs x 2.24 (entry, roll old, roll new, exit)
        self.assertAlmostEqual(rec.cost_components_total_usd, 8.96, places=6)
        self.assertAlmostEqual(st["total_costs_usd"], 8.96, places=6)
        # journal gross == sum of same-contract segment arithmetic, i.e.
        # (old_fill - entry) + (exit_fill - new_fill): the gap enters ONLY
        # through the difference of the two contracts' fills, never as an
        # extra charge
        entry, roll = rec.entry_fill, rec.rolls[0]
        fpo = rec.gross_segments[0]["fill_price"]
        fpn = rec.mae_mfe_segments[1]["avg_entry_price"]
        exit_f = rec.exit_fill
        expected = ((fpo - entry.price) + (exit_f.price - fpn)) * 50
        self.assertAlmostEqual(rec.gross_pnl_usd, expected, places=6)
        # and the double-count canary: gross != anything that adds the gap
        gap_usd = roll.raw_gap * 50
        self.assertAlmostEqual(gap_usd, 500.0, places=6)
        self.assertNotAlmostEqual(
            rec.gross_pnl_usd, expected + gap_usd, places=6)
        # ledger cost outflow (entry+exit+roll legs, sign-normalized to a
        # positive USD amount) == commissions only
        self.assertAlmostEqual(
            st["independent_reconciliation"]["ledger_cost_outflow_usd"],
            8.96, places=6)


class TestReconciliationAcrossManyTrades(unittest.TestCase):
    def test_multi_trade_multi_roll_journal_ledger_identity(self):
        """Scripted trades crossing the roll repeatedly: the independent
        journal recomputation must equal the ledger for every run."""
        from .helpers import ScriptedStrategy
        cal, cons = es_universe()
        eng = es_engine(cons, cal)
        script = {}
        for k, s in enumerate(cal.sessions()):
            if k % 7 == 0:
                script[s] = Decision(action="enter_long", tp_price=10**9,
                                     sl_price=-10**9, time_exit_sessions=11,
                                     reason="cycle", features={})
        j = eng.run(ScriptedStrategy(script), TradeJournal(0.0))
        st = eng.last_run_stats
        ir = st["independent_reconciliation"]
        self.assertTrue(ir["reconciled"])
        self.assertAlmostEqual(
            st["ledger"]["final"],
            st["ledger"]["initial"] + ir["journal_gross_usd"]
            - ir["journal_costs_usd"], places=6)
        # every closed point record: net = gross - accumulated costs, and
        # gross == sum of its segment grosses
        for r in j.point_pnl_records():
            if r.net_pnl_usd is None:
                continue
            self.assertAlmostEqual(r.net_pnl_usd,
                                   r.gross_pnl_usd
                                   - r.cost_components_total_usd, places=6)
            if r.gross_segments:
                self.assertAlmostEqual(
                    r.gross_pnl_usd,
                    sum(s["gross_usd"] for s in r.gross_segments), places=6)

    def test_ambiguous_booking_reconciles_from_journal(self):
        """AMBIGUOUS records keep no point PnL but the ledger's booked
        worst-case bound must still reconcile from journal artifacts."""
        cal, cons = es_universe()
        victim = dt.date(2026, 1, 7)
        from .helpers import make_bar
        for cd in cons:
            cd.daily_trades = [make_bar(b.t, 6000.0, 6100.0, 4900.0, 6000.0,
                                        v=1000) if b.t == victim else b
                               for b in cd.daily_trades]
        eng = es_engine(cons, cal)
        t0 = dt.date(2026, 1, 5)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=5050.0, sl_price=4950.0,
            reason="amb", features={}) if ctx.asof == t0 \
            else Decision(action="none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertEqual(rec.ambiguity, "AMBIGUOUS_ORDER")
        st = eng.last_run_stats
        ir = st["independent_reconciliation"]
        self.assertTrue(ir["reconciled"])
        # booked bound equals the sl_first scenario gross
        b = rec.scenario_bounds
        self.assertAlmostEqual(
            rec.ledger_booked_gross_usd,
            b["sl_first"] + rec.cost_components_total_usd, places=6)
        self.assertAlmostEqual(ir["journal_gross_usd"],
                               rec.ledger_booked_gross_usd, places=6)


if __name__ == "__main__":
    unittest.main()
