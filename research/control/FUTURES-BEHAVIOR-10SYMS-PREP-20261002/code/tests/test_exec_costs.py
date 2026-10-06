"""EXEC-FIX R1: cost-path adversarial tests.

Reproduced findings on base eae8c3d2 (2026-10-02):
  * engine.exec_cost called commission_cash_usd(1) — quantity dropped:
    ES qty1 and qty3 both cost $2.24/side (qty3 must be $6.72/side,
    $13.44 roundtrip at $2.24/side/contract);
  * when ANY commission component was missing, ALL known fees were
    zeroed (CL charged $0.00/side instead of its known $0.85);
  * cost_incomplete only reflected commission components — a NOT_RUN
    slippage component never flagged the record.

Law after fix: allow_incomplete_costs covers ALL cost components
(commission, exchange fee, slippage, any others). When allowed-incomplete:
known fees are deducted; missing components are recorded as NULL with
their source class (PUBLISHED/MEASURED/DECLARED/NOT_RUN) — never a
fabricated 0, never MEASURED. When allow_incomplete_costs=False and the
book is incomplete, the engine refuses to run at all.
"""
import datetime as dt
import unittest

from futbt.costs import CostBook
from futbt.engine import BacktestEngine, Decision, EngineConfig
from futbt.journal import TradeJournal
from futbt.roll import RollEngine
from futbt.taxonomy import PolicyError

from .helpers import make_bar, make_contract
from .test_engine import es_universe

ES = 50.0          # multiplier
ES_COMMISSION = 2.24   # 0.85 broker + 1.39 exchange+reg, per side per contract


def es_engine_cfg(contracts, cal, cfg=None, book=None):
    re = RollEngine("ES", contracts, cal)
    return BacktestEngine("ES", re, re.build_roll_table(),
                          book or CostBook.for_symbol("ES"),
                          cfg or EngineConfig())


def cl_universe():
    """Two CL contracts, roll 2026-02-27; prices stay positive and calm."""
    from futbt.calendarx import WeekdayCalendar
    cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 4, 30))
    sessions = cal.sessions()
    bars_a = [make_bar(s, 60.0, 60.5, 59.5, 60.0, v=500)
              for s in sessions if s <= dt.date(2026, 3, 18)]
    bars_b = [make_bar(s, 61.0, 61.5, 60.5, 61.0, v=500)
              for s in sessions if s >= dt.date(2026, 1, 5)]
    a = make_contract("CL", "CLH6", 11, dt.date(2026, 3, 18), bars_a)
    b = make_contract("CL", "CLJ6", 12, dt.date(2026, 4, 18), bars_b)
    return cal, [a, b]


def cl_engine(contracts, cal, cfg=None):
    re = RollEngine("CL", contracts, cal)
    return BacktestEngine("CL", re, re.build_roll_table(),
                          CostBook.for_symbol("CL"), cfg or EngineConfig())


class TestCommissionScalesWithQuantity(unittest.TestCase):
    def test_es_qty3_charges_3x_commission_per_side(self):
        cal, cons = es_universe()
        eng = es_engine_cfg(cons, cal)
        t0 = dt.date(2026, 1, 5)
        strat = lambda ctx: Decision(
            action="enter_long", qty=3, tp_price=10**9, sl_price=-10**9,
            time_exit_sessions=3, reason="qty3",
            features={}) if ctx.asof == t0 else Decision(action="none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertEqual(rec.qty, 3)
        self.assertEqual(rec.entry_fill.signed_qty, 3)
        # per side: 3 contracts x $2.24 = $6.72 (base bug: $2.24)
        self.assertAlmostEqual(rec.entry_fill.cost_total_usd,
                               3 * ES_COMMISSION, places=9)
        self.assertAlmostEqual(rec.exit_fill.cost_total_usd,
                               3 * ES_COMMISSION, places=9)
        # roundtrip: 6 sides x $2.24 = $13.44 (base bug: $4.48)
        self.assertAlmostEqual(rec.cost_components_total_usd,
                               6 * ES_COMMISSION, places=9)
        self.assertAlmostEqual(rec.entry_fill.cost_breakdown["contracts"], 3)
        # spread price shift is per contract (same px shift), cash scales
        st = eng.last_run_stats
        self.assertAlmostEqual(st["total_costs_usd"], 6 * ES_COMMISSION,
                               places=6)
        # ledger identity with qty-scaled costs
        self.assertAlmostEqual(
            st["ledger"]["final"],
            st["ledger"]["initial"] + st["realized_gross_usd"]
            - st["total_costs_usd"], places=6)

    def test_commission_cash_usd_scales(self):
        book = CostBook.for_symbol("ES")
        for q in (1, 3, 10):
            comm = book.commission_cash_usd(q)
            self.assertAlmostEqual(comm["usd"], q * ES_COMMISSION, places=9)
            self.assertEqual(comm["contracts"], q)
        with self.assertRaises(PolicyError):
            book.commission_cash_usd(0)


class TestIncompleteCostLaw(unittest.TestCase):
    def test_cl_known_broker_commission_charged_when_exchange_missing(self):
        # CL book: commission_broker $0.85 KNOWN, exchange+reg NOT_RUN.
        # Base bug: one missing commission component zeroed ALL cash fees.
        cal, cons = cl_universe()
        eng = cl_engine(cons, cal)
        t0 = dt.date(2026, 1, 5)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=10**9, sl_price=-10**9,
            time_exit_sessions=2, reason="cl",
            features={}) if ctx.asof == t0 else Decision(action="none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertAlmostEqual(rec.entry_fill.cost_total_usd, 0.85, places=9)
        self.assertAlmostEqual(rec.exit_fill.cost_total_usd, 0.85, places=9)
        self.assertAlmostEqual(rec.cost_components_total_usd, 1.70, places=9)
        self.assertTrue(rec.cost_incomplete)
        self.assertIn("exchange_plus_regulatory",
                      rec.cost_missing_components)

    def test_cost_incomplete_covers_all_components_not_just_commission(self):
        # ES commission components are complete, but slippage is NOT_RUN —
        # the record must still be cost_incomplete=True with the component
        # named (base bug: cost_incomplete stayed False).
        cal, cons = es_universe()
        eng = es_engine_cfg(cons, cal)
        t0 = dt.date(2026, 1, 5)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=10**9, sl_price=-10**9,
            time_exit_sessions=2, reason="es",
            features={}) if ctx.asof == t0 else Decision(action="none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertTrue(rec.cost_incomplete)
        self.assertIn("slippage", rec.cost_missing_components)
        bd = rec.entry_fill.cost_breakdown
        self.assertIn("slippage", bd["missing_cost_components"])
        status = bd["missing_component_status"]["slippage"]
        self.assertIsNone(status["value_usd_per_contract_side"])
        self.assertEqual(status["provenance"], "NOT_RUN")
        self.assertEqual(status["expected_source_class_when_provided"],
                         "DECLARED")
        # known fees still deducted despite the missing component
        self.assertAlmostEqual(rec.entry_fill.cost_total_usd, 2.24, places=9)

    def test_missing_exchange_fee_disclosed_with_null_value(self):
        cal, cons = cl_universe()
        eng = cl_engine(cons, cal)
        t0 = dt.date(2026, 1, 5)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=10**9, sl_price=-10**9,
            time_exit_sessions=2, reason="cl",
            features={}) if ctx.asof == t0 else Decision(action="none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        bd = rec.entry_fill.cost_breakdown
        status = bd["missing_component_status"]["exchange_plus_regulatory"]
        # NULL value with source class — never a fabricated 0 / MEASURED
        self.assertIsNone(status["value_usd_per_contract_side"])
        self.assertEqual(status["provenance"], "NOT_RUN")
        self.assertEqual(status["expected_source_class_when_provided"],
                         "PUBLISHED")

    def test_allow_incomplete_costs_false_refuses_incomplete_book(self):
        # fail-fast at construction: CL book incomplete (exchange+reg,
        # slippage NOT_RUN) + allow_incomplete_costs=False -> PolicyError
        cal, cons = cl_universe()
        with self.assertRaisesRegex(PolicyError, "allow_incomplete_costs"):
            cl_engine(cons, cal, EngineConfig(allow_incomplete_costs=False))
        cal2, cons2 = es_universe()
        with self.assertRaisesRegex(PolicyError, "allow_incomplete_costs"):
            es_engine_cfg(cons2, cal2,
                          EngineConfig(allow_incomplete_costs=False))

    def test_complete_book_with_allow_false_runs_and_flags_nothing(self):
        # ES + declared slippage = complete book: allow_incomplete_costs=False
        # must run, charge full costs, and stamp cost_incomplete=False
        cal, cons = es_universe()
        book = CostBook.for_symbol("ES").declare_slippage(
            10.0, "test-scenario", "declared nonzero slippage for the "
            "complete-book path")
        eng = es_engine_cfg(cons, cal,
                            EngineConfig(allow_incomplete_costs=False),
                            book=book)
        t0 = dt.date(2026, 1, 5)
        strat = lambda ctx: Decision(
            action="enter_long", tp_price=10**9, sl_price=-10**9,
            time_exit_sessions=2, reason="complete",
            features={}) if ctx.asof == t0 else Decision(action="none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        self.assertFalse(rec.cost_incomplete)
        self.assertEqual(rec.cost_missing_components, [])
        self.assertAlmostEqual(rec.entry_fill.cost_total_usd, 2.24, places=9)


class TestNegativeCLCostPath(unittest.TestCase):
    def test_negative_cl_arithmetic_with_incomplete_cost_book(self):
        """Negative CL prices + the incomplete-cost path: arithmetic PnL
        unchanged, known broker commission charged (base: $0), missing
        exchange fee/slippage disclosed as NULL/NOT_RUN."""
        from futbt.calendarx import WeekdayCalendar
        cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 4, 30))
        sessions = cal.sessions()
        px = {s: 20.0 - 0.5 * i for i, s in enumerate(sessions)}
        # contract A prices dive through zero (negative-CL arithmetic)
        bars_a = [make_bar(s, px[s], px[s] + 0.8, px[s] - 0.8, px[s], v=400)
                  for s in sessions if s <= dt.date(2026, 2, 20)]
        bars_b = [make_bar(s, px[s] + 1.0, px[s] + 1.8, px[s] + 0.2,
                           px[s] + 1.0, v=400) for s in sessions]
        a = make_contract("CL", "CLG6", 11, dt.date(2026, 2, 20), bars_a)
        b = make_contract("CL", "CLH6", 12, dt.date(2026, 3, 20), bars_b)
        re = RollEngine("CL", [a, b], cal)
        eng = BacktestEngine("CL", re, re.build_roll_table(),
                             CostBook.for_symbol("CL"), EngineConfig())
        t0 = dt.date(2026, 1, 5)
        strat = lambda ctx: Decision(
            action="enter_short", tp_price=-10.0, sl_price=60.0,
            time_exit_sessions=12, reason="neg-cl",
            features={}) if ctx.asof == t0 else Decision(action="none")
        j = eng.run(strat, TradeJournal(0.0))
        recs = [r for r in j.records if r.entry_fill]
        self.assertTrue(recs)
        for r in recs:
            if r.gross_pnl_usd is not None:
                self.assertAlmostEqual(
                    r.gross_pnl_usd,
                    (r.exit_fill.price - r.entry_fill.price) * 1000
                    * r.entry_fill.signed_qty, places=6)
            # CL incomplete book: 0.85/side charged, NULL-disclosed rest
            self.assertAlmostEqual(r.entry_fill.cost_total_usd, 0.85,
                                   places=9)
            self.assertTrue(r.cost_incomplete)
            self.assertIn("exchange_plus_regulatory",
                          r.cost_missing_components)
            self.assertIn("slippage", r.cost_missing_components)


class TestTickRoundedCosts(unittest.TestCase):
    def test_sixj_costs_tick_rounded_and_qty_scaled(self):
        from futbt.calendarx import WeekdayCalendar
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
        from futbt.engine import BacktestEngine as BE
        eng = BE("6J", re, re.build_roll_table(),
                 CostBook.for_symbol("6J"), EngineConfig())
        t0 = dt.date(2026, 1, 5)
        strat = lambda ctx: Decision(
            action="enter_long", qty=3, tp_price=0.006360, sl_price=0.006300,
            time_exit_sessions=8, reason="jpy3",
            features={}) if ctx.asof == t0 else Decision(action="none")
        j = eng.run(strat, TradeJournal(0.0))
        rec = [r for r in j.records if r.entry_fill][0]
        # fills live on the 5e-7 tick grid (cost shift tick-rounded)
        for f in (rec.entry_fill, rec.exit_fill):
            self.assertAlmostEqual(f.price / 5e-7, round(f.price / 5e-7),
                                   places=6)
            # cash commission scales with qty (base: dropped -> 0.85)
            self.assertAlmostEqual(f.cost_total_usd, 3 * 0.85, places=9)
        if rec.gross_pnl_usd is not None:
            self.assertAlmostEqual(
                rec.gross_pnl_usd,
                (rec.exit_fill.price - rec.entry_fill.price) * 12_500_000 * 3,
                places=6)
        # 6J spread price shift: half of $25 = $12.50 = 1e-6 px = 2 ticks
        bd = rec.entry_fill.cost_breakdown
        self.assertAlmostEqual(bd["price_shift_breakdown"]["half_spread_usd"],
                               12.50, places=9)


if __name__ == "__main__":
    unittest.main()
