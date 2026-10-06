"""Portfolio composition tests (MULTIASSET-WIRING, 2026-10-02).

Wired composition layer over real PortfolioEngine runs:
  * co-loss / overlap descriptives computed from the run's own journals;
  * combined breakeven under the frozen journal tolerance (ambiguous and
    censored records excluded, never netted into point totals);
  * leave-one-leg FULL-PATH harness with genuine non-additivity: with a
    binding margin cap, removing a small leg can UNBLOCK a big one, so
    the marginal effect of a leg differs from the leg's own PnL — the
    additive shortcut is provably wrong (and forbidden);
  * baselines flat / always-on / single-leg as full-path portfolio runs;
  * drawdown arithmetic.
"""
import datetime as dt
import unittest

from futbt.accounting import MarginModel, drawdown_series, max_drawdown
from futbt.composition import (AlwaysOn, CombineSpec,
                               PortfolioRiskGate, additive_attribution_guard,
                               always_on_baseline, combined_breakeven,
                               flat_baseline, portfolio_leave_one_leg,
                               portfolio_pairwise_descriptives,
                               portfolio_run_summary,
                               sleeve_series_from_result,
                               single_leg_baselines)
from futbt.costs import CostBook
from futbt.engine import BacktestEngine, EngineConfig, PortfolioEngine
from futbt.journal import TradeJournal
from futbt.taxonomy import PolicyError

from .helpers import make_bar
from .test_portfolio_wiring import (T0, enter_at, three_symbol_engines)

TIGHT_CASH = {"6J": 500.0, "CL": 8_000.0, "ES": 30_000.0}


def tight_run(sleeves):
    """Full-path portfolio run over the tight-cash universe with a margin
    gate: interactions are real (see TestLeaveOneLegNonAdditive)."""
    engines = three_symbol_engines(TIGHT_CASH)
    pe = PortfolioEngine({s: engines[s] for s in sleeves})
    gate = PortfolioRiskGate(margin_model=MarginModel())
    return pe.run({s: enter_at(T0) for s in sleeves}, gate=gate)


class TestCoLossDescriptivesFromJournals(unittest.TestCase):
    """Synchronized losers: co-loss counted from the wired run itself."""

    @classmethod
    def setUpClass(cls):
        cls.result = tight_run(["CL", "ES"])

    def test_both_sleeves_lose_on_the_overlap(self):
        descs = portfolio_pairwise_descriptives(self.result)
        self.assertEqual(len(descs), 1)
        d = descs[0]
        self.assertEqual(d["pair"], "CL/ES")
        sleeves = sleeve_series_from_result(self.result)
        exposed = sorted(sleeves["CL"].exposed_sessions
                         & sleeves["ES"].exposed_sessions)
        self.assertGreater(len(exposed), 3)
        self.assertEqual(d["n_overlap_sessions"], len(exposed))
        # down staircases + long entries: every overlap session is a
        # co-loss session for both sleeves
        self.assertEqual(d["co_loss_days"], len(exposed))
        self.assertAlmostEqual(d["co_loss_given_a_losing"], 1.0, places=9)
        self.assertGreaterEqual(d["joint_tail_5pct_days"], 1)
        self.assertAlmostEqual(d["overlap_ratio_vs_union"], 1.0, places=9)

    def test_descriptives_are_description_only(self):
        d = portfolio_pairwise_descriptives(self.result)[0]
        self.assertIn("no selection performed", d["note"])


class TestCombinedBreakeven(unittest.TestCase):
    def _run(self, sleeves, tolerance=0.0):
        cash = {s: 100_000.0 for s in sleeves}
        engines = three_symbol_engines(cash)
        pe = PortfolioEngine({s: engines[s] for s in sleeves})
        journals = {s: TradeJournal(breakeven_tolerance_usd=tolerance)
                    for s in sleeves}
        return pe.run({s: enter_at(T0) for s in sleeves}, journals=journals)

    def test_point_total_equals_record_nets_exactly(self):
        res = self._run(["CL", "6J", "ES"], tolerance=0.0)
        be = combined_breakeven(res)
        expected = sum(r.net_pnl_usd
                       for j in res.journals.values() for r in j.records
                       if r.entry_fill is not None and not r.right_censored
                       and r.net_pnl_usd is not None)
        self.assertAlmostEqual(be["point_net_usd"], expected, places=6)
        self.assertEqual(be["classification"], "LOSS")   # down staircases
        self.assertEqual(be["ambiguous_excluded"], 0)

    def test_breakeven_within_frozen_tolerance(self):
        res = self._run(["CL", "ES"], tolerance=1e9)   # tolerance dwarfs
        be = combined_breakeven(res)
        self.assertEqual(be["classification"],
                         "BREAKEVEN_WITHIN_FROZEN_TOLERANCE")
        self.assertEqual(be["frozen_tolerance_usd"], 1e9)

    def test_mixed_tolerances_refused(self):
        cash = {"CL": 100_000.0, "ES": 100_000.0}
        engines = three_symbol_engines(cash)
        pe = PortfolioEngine({s: engines[s] for s in cash})
        res = pe.run({"CL": enter_at(T0), "ES": enter_at(T0)},
                     journals={"CL": TradeJournal(0.0),
                               "ES": TradeJournal(5.0)})
        with self.assertRaisesRegex(PolicyError, "tolerance"):
            combined_breakeven(res)

    def test_censored_records_excluded_never_netted(self):
        # enter late with NO exit -> right-censored at end of data
        engines = three_symbol_engines({"CL": 100_000.0})
        pe = PortfolioEngine({"CL": engines["CL"]})
        res = pe.run({"CL": enter_at(dt.date(2026, 6, 1), time_exit=999)})
        be = combined_breakeven(res)
        self.assertEqual(be["right_censored_excluded"], 1)
        self.assertEqual(be["point_net_usd"], 0.0)   # nothing netted

    def test_ambiguous_records_bounded_not_netted(self):
        # same-bar TP+SL straddle -> AMBIGUOUS_ORDER, excluded from the
        # point total but disclosed with both scenario bounds
        engines = three_symbol_engines({"CL": 100_000.0})
        eng = engines["CL"]
        victim = eng.sessions[eng.sessions.index(T0) + 1]   # fill session
        for cd in eng.roll_engine.contracts:                # mutate in place
            cd.daily_trades = [
                make_bar(b.t, 70.0, 90.0, 50.0, 70.0, v=1000)
                if b.t == victim else b for b in cd.daily_trades]
        # rebuild the engine so the mutated bars are validated + chained
        eng2 = BacktestEngine("CL", eng.roll_engine,
                              eng.roll_engine.build_roll_table(),
                              CostBook.for_symbol("CL"),
                              EngineConfig(initial_cash_usd=100_000.0))
        pe = PortfolioEngine({"CL": eng2})
        res = pe.run({"CL": enter_at(T0, time_exit=999, tp=75.0, sl=65.0)})
        recs = [r for r in res.journals["CL"].records
                if r.entry_fill is not None]
        self.assertEqual(recs[0].ambiguity, "AMBIGUOUS_ORDER")
        be = combined_breakeven(res)
        self.assertEqual(be["ambiguous_excluded"], 1)
        self.assertIn("tp_first", be["ambiguous_bounds"][0]
                      ["scenario_bounds"])
        self.assertEqual(be["point_net_usd"], 0.0)


class TestLeaveOneLegNonAdditive(unittest.TestCase):
    """The wired full-path harness with a REAL interaction: with the
    tight margin cap the full portfolio blocks ES, but removing the tiny
    6J leg (margin 3,080, cash 500) frees enough margin for ES to trade.
    Removing a losing leg makes the portfolio WORSE — the additive
    shortcut (sum of leg PnLs) is directionally wrong here."""

    @classmethod
    def setUpClass(cls):
        cls.harness = portfolio_leave_one_leg(
            portfolio_factory=lambda sleeves: (
                lambda: tight_run(sleeves)),
            legs=("6J", "CL", "ES"))

    def test_base_portfolio_blocks_es_on_margin(self):
        base = self.harness["base"]
        self.assertEqual(base["symbols"], ["6J", "CL", "ES"])
        self.assertEqual(base["n_blocked"], 1)
        self.assertEqual(base["blocked_by_code"],
                         {"BLOCKED_MARGIN_INITIAL": 1})

    def test_removing_6j_unblocks_es(self):
        without = self.harness["leave_one_leg"]["6J"]["without_leg"]
        self.assertEqual(without["symbols"], ["CL", "ES"])
        self.assertEqual(without["n_blocked"], 0)   # ES now trades

    def test_marginal_effect_opposite_sign_to_leg_pnl(self):
        # 6J's own trade LOSES (long into a falling market); removing it
        # makes the portfolio WORSE (ES's bigger loss is unblocked) ->
        # marginal(6J) > 0 while pnl(6J) < 0: non-additivity proven
        base_res = tight_run(["6J", "CL", "ES"])
        pnl_6j = [r for r in base_res.journals["6J"].records
                  if r.entry_fill is not None][0].net_pnl_usd
        self.assertLess(pnl_6j, 0.0)
        marginal = self.harness["leave_one_leg"]["6J"][
            "marginal_effect_total_net_usd"]
        self.assertGreater(marginal, 0.0)
        self.assertNotAlmostEqual(marginal, -pnl_6j, places=6)

    def test_single_legs_differ_from_full_portfolio(self):
        # single-leg runs are NOT the portfolio decomposition: 6J and CL
        # alone are margin-BLOCKED (their own cash is below their own
        # margin) while they trade fine inside the portfolio
        for sym, blocked_expected in (("6J", True), ("CL", True),
                                      ("ES", False)):
            single = portfolio_run_summary(tight_run([sym]))
            self.assertEqual(single["n_blocked"] > 0, blocked_expected, sym)
        base_net = self.harness["base"]["realized_point_net_usd"]
        single_sum = sum(portfolio_run_summary(tight_run([s]))
                         ["realized_point_net_usd"] for s in ("6J", "CL", "ES"))
        self.assertNotAlmostEqual(single_sum, base_net, places=6)

    def test_method_is_full_path_not_additive(self):
        self.assertIn("full-path", self.harness["method"])
        self.assertIn("NEVER attributed-PnL sums", self.harness["method"])
        # every removal recorded as its own complete run
        self.assertEqual(len(self.harness["runs"]), 6)   # base + 3 removals
        # (LeaveOneLegSpec re-runs base_all per removal)

    def test_additive_shortcut_forbidden(self):
        with self.assertRaisesRegex(PolicyError,
                                    "forbidden|full-path"):
            additive_attribution_guard({"ES": -100.0, "CL": -50.0})


class TestBaselinesFullPath(unittest.TestCase):
    def test_flat_baseline_zero(self):
        res = tight_run(["CL", "ES"])   # any sessions source
        flat = flat_baseline(res.sessions)
        self.assertTrue(all(v == 0.0 for v in flat["pnl_by_session"].values()))

    def test_always_on_strategy_censors_at_end_of_data(self):
        engines = three_symbol_engines({"CL": 100_000.0})
        pe = PortfolioEngine({"CL": engines["CL"]})
        res = pe.run({"CL": AlwaysOn("long")})
        recs = [r for r in res.journals["CL"].records
                if r.entry_fill is not None]
        self.assertEqual(len(recs), 1)
        self.assertTrue(recs[0].right_censored)
        self.assertEqual(recs[0].exit_type, "END_OF_DATA")
        with self.assertRaises(ValueError):
            AlwaysOn("sideways")

    def test_single_leg_and_always_on_adapters_use_full_path_runs(self):
        def runner_for(sym, direction):
            engines = three_symbol_engines({sym: 100_000.0})
            res = PortfolioEngine({sym: engines[sym]}).run(
                {sym: AlwaysOn(direction)})
            return {"pnl_by_session":
                    sleeve_series_from_result(res)[sym].pnl_by_session}

        one_cl = runner_for("CL", "long")
        sessions = sorted(one_cl["pnl_by_session"])
        single = single_leg_baselines(
            {s: (lambda d, s=s: runner_for(s, d)) for s in ("CL", "ES")},
            sessions)
        self.assertEqual(set(single), {"CL", "ES"})
        for sym, b in single.items():
            self.assertEqual(b["method"], "full-path re-run")
            one = runner_for(sym, "long")
            self.assertAlmostEqual(sum(b["pnl_by_session"].values()),
                                   sum(one["pnl_by_session"].values()),
                                   places=6)
        both = always_on_baseline(
            {s: (lambda d, s=s: runner_for(s, d)) for s in ("CL", "ES")},
            sessions, "long")
        self.assertAlmostEqual(
            sum(both["pnl_by_session"].values()),
            sum(single["CL"]["pnl_by_session"].values())
            + sum(single["ES"]["pnl_by_session"].values()), places=6)


class TestDrawdownArithmetic(unittest.TestCase):
    def test_series_and_max(self):
        eq = [100.0, 120.0, 90.0, 130.0, 110.0]
        self.assertEqual(drawdown_series(eq), [0.0, 0.0, -30.0, 0.0, -20.0])
        m = max_drawdown(eq)
        self.assertAlmostEqual(m["max_drawdown_usd"], -30.0)
        self.assertEqual(m["peak_index"], 1)
        self.assertEqual(m["trough_index"], 2)
        self.assertAlmostEqual(m["peak_equity_usd"], 120.0)
        self.assertAlmostEqual(m["trough_equity_usd"], 90.0)

    def test_empty_and_monotone_up(self):
        self.assertEqual(drawdown_series([]), [])
        self.assertEqual(max_drawdown([])["max_drawdown_usd"], 0.0)
        self.assertTrue(all(v == 0.0 for v in drawdown_series([1.0, 2.0, 3.0])))


class TestCensoredRollLegReconciliation(unittest.TestCase):
    """DEFECT REPRO (found by this lane, 2026-10-02, in EXEC-FIX's R2
    final reconciliation — logic verbatim from the pre-refactor run()):

    a right-censored record with EXECUTED roll legs books `realize`
    events in the ledger, but the final independent journal<->cash
    reconciliation skipped censored records entirely (gross None and
    booked None -> contributed 0), so cash != initial + journal_gross -
    journal_costs exploded. Any hold-through-roll-to-end-of-data run
    tripped it (e.g. the ALWAYS-ON baseline). Fixed in engine.py
    _Replay.finalize: censored records contribute their EXECUTED segment
    gross (roll legs) — still never a point trade PnL."""

    def _hold_through_roll_universe(self):
        from futbt.calendarx import WeekdayCalendar
        from .helpers import make_bar, make_contract
        cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 6, 30))
        sessions = cal.sessions()
        # CLH6 (expiry month Mar-2026) rolls to CLJ6 at Fri 2026-02-27's
        # close; the position holds to end of data (right-censored)
        a, b = [], []
        for i, s in enumerate(sessions):
            px = 70.0 + 0.1 * i
            if s <= dt.date(2026, 3, 20):
                a.append(make_bar(s, px, px + 0.5, px - 0.5, px, v=1000))
            b.append(make_bar(s, px - 0.4, px + 0.1, px - 0.9, px - 0.4,
                              v=1000))
        ca = make_contract("CL", "CLH6", 11, dt.date(2026, 3, 20), a)
        cb = make_contract("CL", "CLJ6", 12, dt.date(2026, 4, 20), b)
        return cal, [ca, cb]

    def test_single_symbol_censored_after_executed_roll(self):
        from futbt.costs import CostBook
        from futbt.engine import BacktestEngine, Decision
        from futbt.roll import RollEngine
        cal, cons = self._hold_through_roll_universe()
        re = RollEngine("CL", cons, cal)
        eng = BacktestEngine("CL", re, re.build_roll_table(),
                             CostBook.for_symbol("CL"))
        strat = lambda ctx: Decision(
            action="enter_long", reason="hold",
            features={}) if ctx.asof == dt.date(2026, 1, 5) \
            else Decision(action="none")
        j = eng.run(strat, TradeJournal(0.0))
        recs = [r for r in j.records if r.entry_fill is not None]
        self.assertEqual(len(recs), 1)
        self.assertTrue(recs[0].right_censored)
        self.assertEqual(recs[0].exit_type, "END_OF_DATA")
        self.assertEqual(len(recs[0].rolls), 1)
        # the executed roll-leg gross must reconcile with the ledger
        stats = eng.last_run_stats["independent_reconciliation"]
        self.assertAlmostEqual(stats["journal_gross_usd"],
                               stats["ledger_realize_usd"], places=6)

    def test_always_on_portfolio_censors_after_rolls(self):
        # AlwaysOn holds through every CL roll to end of data
        engines = three_symbol_engines({"CL": 100_000.0})
        pe = PortfolioEngine({"CL": engines["CL"]})
        res = pe.run({"CL": AlwaysOn("long")})
        rec = [r for r in res.journals["CL"].records
               if r.entry_fill is not None][0]
        self.assertTrue(rec.right_censored)
        self.assertGreaterEqual(len(rec.rolls), 1)


class TestCombineSpecIntact(unittest.TestCase):
    """DECLARED-weights guard untouched by the wiring round."""

    def test_declared_ok_and_fitted_rejected(self):
        CombineSpec(weights={"CL": 0.5, "ES": 0.5},
                    weight_provenance="DECLARED", declared_by="owner",
                    rationale="equal risk ex ante")
        with self.assertRaisesRegex(PolicyError,
                                    "IN_SAMPLE_MASQUERADE"):
            CombineSpec(weights={"CL": 0.9, "ES": 0.1},
                        weight_provenance="FITTED", declared_by="opt",
                        rationale="fitted on the evaluated history")


if __name__ == "__main__":
    unittest.main()
