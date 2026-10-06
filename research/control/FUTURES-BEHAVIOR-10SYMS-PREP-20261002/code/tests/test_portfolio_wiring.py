"""Portfolio wiring tests (MULTIASSET-WIRING, steering round 2, 2026-10-02).

End-to-end multi-symbol runs on hand-built synthetic universes in the
THREE quote conventions of the real 10-symbol table:
  CL  — USD/barrel, 0.01 tick, x1000, NEGATIVE-legal (arithmetic PnL only)
  6J  — USD per JPY (~0.0063, NEVER inverted), 5e-7 tick, x12,500,000
  ES  — index points, 0.25 tick, x50
Exact USD cash math is asserted against independent recomputation from
journal records + the declared cost model (half-spread price shift,
quantity-scaled known commissions, NULL missing components).
"""
import datetime as dt
import unittest

from futbt.accounting import round_to_tick
from futbt.calendarx import WeekdayCalendar
from futbt.composition import PortfolioRiskGate, sleeve_series_from_result
from futbt.accounting import MarginModel
from futbt.costs import CostBook
from futbt.engine import (BacktestEngine, Decision, EngineConfig,
                          FutureAccessError, PortfolioEngine)
from futbt.journal import TradeJournal
from futbt.roll import RollEngine

from .helpers import make_bar, make_contract

# --------------------------------------------------------------------- #
# universe builder: three quote conventions on one weekday calendar
CAL_START, CAL_END = dt.date(2026, 1, 1), dt.date(2026, 6, 30)

SPEC = {
    # symbol: (start_level, per-session drift, tick, gap to contract B)
    "CL": (70.00, -0.10, 0.01, -0.40),
    "6J": (0.006330, -0.000001, 5e-7, 0.00001),
    "ES": (5000.00, -3.00, 0.25, 10.00),
}
HALF_SPREAD_PX = {"CL": 30.0 / 2.0 / 1000.0,
                  "6J": 25.0 / 2.0 / 12_500_000.0,
                  "ES": 12.5 / 2.0 / 50.0}
KNOWN_COMM_PER_SIDE = {"CL": 0.85, "6J": 0.85, "ES": 2.24}  # ES complete


def _staircase_bars(sessions, start, drift, tick, gap=0.0, until=None):
    """Deterministic staircase: o = previous close, c = o + drift,
    h/l = max/min ± one tick-ish excursion. All on the tick grid."""
    bars = []
    prev_c = None
    px = start + gap
    for i, s in enumerate(sessions):
        if until is not None and s > until:
            break
        c = px + drift * i
        o = prev_c if prev_c is not None else c
        exc = tick * 5 if tick < 0.001 else tick * 4
        h = max(o, c) + exc
        l = min(o, c) - exc
        bars.append(make_bar(
            s, round(o / tick) * tick, round(h / tick) * tick,
            round(l / tick) * tick, round(c / tick) * tick, v=1000))
        prev_c = c
    return bars


def three_symbol_engines(cash=None, drift_sign=1.0):
    """Engines for CL (2 monthly contracts), 6J (single quarterly contract)
    and ES (2 quarterly contracts). cash: {sym: initial_cash}."""
    cal = WeekdayCalendar(CAL_START, CAL_END)
    sessions = cal.sessions()
    out = {}
    # CL: CLH6 (LTD Fri 2026-03-20, expiry month Mar), CLJ6 (Apr)
    cl_a_bars = _staircase_bars(sessions, SPEC["CL"][0],
                                drift_sign * SPEC["CL"][1], SPEC["CL"][2],
                                until=dt.date(2026, 3, 20))
    cl_b_bars = _staircase_bars(sessions, SPEC["CL"][0],
                                drift_sign * SPEC["CL"][1], SPEC["CL"][2],
                                gap=SPEC["CL"][3])
    cons = [make_contract("CL", "CLH6", 11, dt.date(2026, 3, 20), cl_a_bars),
            make_contract("CL", "CLJ6", 12, dt.date(2026, 4, 20), cl_b_bars)]
    # 6J: single contract 6JM6 (LTD 2026-06-18) — no roll in the window
    j_bars = _staircase_bars(sessions, SPEC["6J"][0],
                             drift_sign * SPEC["6J"][1], SPEC["6J"][2])
    cons_j = [make_contract("6J", "6JM6", 21, dt.date(2026, 6, 18), j_bars)]
    # ES: ESH6 (LTD 2026-03-18), ESM6 (LTD 2026-06-18)
    es_a = _staircase_bars(sessions, SPEC["ES"][0], drift_sign * SPEC["ES"][1],
                           SPEC["ES"][2], until=dt.date(2026, 3, 18))
    es_b = _staircase_bars(sessions, SPEC["ES"][0], drift_sign * SPEC["ES"][1],
                           SPEC["ES"][2], gap=SPEC["ES"][3])
    cons_e = [make_contract("ES", "ESH6", 31, dt.date(2026, 3, 18), es_a),
              make_contract("ES", "ESM6", 32, dt.date(2026, 6, 18), es_b)]
    for sym, contracts in (("CL", cons), ("6J", cons_j), ("ES", cons_e)):
        re = RollEngine(sym, contracts, cal)
        cfg = EngineConfig(initial_cash_usd=(cash or {}).get(sym, 1_000_000.0))
        out[sym] = BacktestEngine(sym, re, re.build_roll_table(),
                                  CostBook.for_symbol(sym), cfg)
    return out


def expected_fill(ref, side, sym):
    """Declared cost model: fill = tick-round(ref +/- half-spread)."""
    tick = SPEC[sym][2]
    shift = HALF_SPREAD_PX[sym]
    return round_to_tick(ref + side * shift, tick,
                         mode="ceil" if side > 0 else "floor")


def enter_at(t0, direction="long", qty=1, time_exit=5, tp=None, sl=None):
    """Scripted strategy: one entry decision at t0, nothing else."""
    def strat(ctx):
        if ctx.asof == t0 and ctx.position is None:
            return Decision(action=f"enter_{direction}", qty=qty,
                            tp_price=tp, sl_price=sl,
                            time_exit_sessions=time_exit, reason="t",
                            features={})
        return Decision(action="none")
    return strat


def sessions_of(eng):
    return eng.sessions


T0 = dt.date(2026, 1, 5)     # Monday


class TestThreeConventionsExactCash(unittest.TestCase):
    """CL + 6J + ES concurrently, with exact USD cash math per convention."""

    @classmethod
    def setUpClass(cls):
        cls.cash = {"CL": 100_000.0, "6J": 100_000.0, "ES": 100_000.0}
        cls.engines = three_symbol_engines(cls.cash)
        cls.pe = PortfolioEngine(cls.engines)
        cls.strats = {s: enter_at(T0) for s in ("CL", "6J", "ES")}
        cls.result = cls.pe.run(cls.strats)

    def test_all_three_traded_and_exited_time(self):
        for sym in ("CL", "6J", "ES"):
            recs = [r for r in self.result.journals[sym].records
                    if r.entry_fill is not None]
            self.assertEqual(len(recs), 1, sym)
            self.assertEqual(recs[0].exit_type, "TIME", sym)
            self.assertFalse(recs[0].right_censored, sym)

    def test_exact_usd_cash_per_convention(self):
        mult = {"CL": 1000.0, "6J": 12_500_000.0, "ES": 50.0}
        cal = WeekdayCalendar(CAL_START, CAL_END)
        sessions = cal.sessions()
        i_fill = sessions.index(T0) + 1            # next open after T0
        i_exit = i_fill + 4                        # held_sessions >= 5
        for sym in ("CL", "6J", "ES"):
            eng = self.engines[sym]
            chain = eng._chain
            entry_ref = chain[sessions[i_fill]].o
            exit_ref = chain[sessions[i_exit]].c
            exp_entry = expected_fill(entry_ref, +1, sym)
            exp_exit = expected_fill(exit_ref, -1, sym)
            rec = [r for r in self.result.journals[sym].records
                   if r.entry_fill is not None][0]
            self.assertEqual(rec.entry_fill.price, exp_entry, sym)
            self.assertEqual(rec.exit_fill.price, exp_exit, sym)
            exp_gross = (exp_exit - exp_entry) * mult[sym]
            exp_costs = 2.0 * KNOWN_COMM_PER_SIDE[sym]
            self.assertAlmostEqual(rec.gross_pnl_usd, exp_gross, places=6)
            self.assertAlmostEqual(rec.cost_components_total_usd, exp_costs,
                                   places=6)
            self.assertAlmostEqual(rec.net_pnl_usd, exp_gross - exp_costs,
                                   places=6)
            # slippage is NOT_RUN for EVERY symbol (no declared value in
            # the repo) -> cost_incomplete True everywhere; ES is the only
            # symbol with a complete COMMISSION stack (2.24/side known)
            self.assertTrue(rec.cost_incomplete, sym)
            self.assertEqual(rec.cost_missing_components,
                             ["slippage"] if sym == "ES"
                             else ["exchange_plus_regulatory", "slippage"],
                             sym)

    def test_portfolio_cash_identity_from_journals(self):
        # independent recomputation: Σ(initial) + Σ(journal gross booked)
        # - Σ(journal costs) == final aggregated portfolio cash
        total = sum(self.cash.values())
        gross = costs = 0.0
        for sym in ("CL", "6J", "ES"):
            for r in self.result.journals[sym].records:
                if r.entry_fill is None:
                    continue
                booked = (r.gross_pnl_usd if r.gross_pnl_usd is not None
                          else r.ledger_booked_gross_usd)
                gross += booked
                costs += r.cost_components_total_usd
        self.assertAlmostEqual(self.result.final_cash_usd(), total + gross - costs,
                               places=6)
        # and each symbol's ledger equals its own journal identity
        for sym in ("CL", "6J", "ES"):
            r = [x for x in self.result.journals[sym].records
                 if x.entry_fill is not None][0]
            self.assertAlmostEqual(
                self.result.cash_by_session[self.result.sessions[-1]][sym],
                self.cash[sym] + r.gross_pnl_usd
                - r.cost_components_total_usd, places=6, msg=sym)

    def test_equity_decomposition_and_mtm_laws(self):
        res = self.result
        for t in res.sessions:
            self.assertAlmostEqual(
                res.equity_by_session[t],
                sum(res.cash_by_session[t].values())
                + sum(res.mtm_by_session[t].values()), places=6)
        # losing path (all staircases drift down, long positions): peak is
        # the initial cash level, drawdown == equity - initial at the end
        init_total = sum(self.cash.values())
        self.assertAlmostEqual(res.equity_by_session[res.sessions[0]],
                               init_total, places=6)
        self.assertAlmostEqual(res.peak_equity_by_session[res.sessions[-1]],
                               init_total, places=6)
        self.assertAlmostEqual(res.drawdown_by_session[res.sessions[-1]],
                               res.equity_by_session[res.sessions[-1]]
                               - init_total, places=6)
        self.assertTrue(all(v <= 1e-9
                            for v in res.drawdown_by_session.values()))
        # MTM while open: exact arithmetic against the held contract close
        cal = WeekdayCalendar(CAL_START, CAL_END)
        sessions = cal.sessions()
        t_open = sessions[sessions.index(T0) + 1]
        for sym in ("CL", "6J", "ES"):
            rec = [r for r in res.journals[sym].records
                   if r.entry_fill is not None][0]
            t_mid = sessions[sessions.index(t_open) + 2]
            mark = self.engines[sym]._chain[t_mid].c
            exp_mtm = (mark - rec.entry_fill.price) * \
                {"CL": 1000.0, "6J": 12_500_000.0, "ES": 50.0}[sym]
            self.assertAlmostEqual(res.mtm_by_session[t_mid][sym], exp_mtm,
                                   places=6, msg=sym)
        # after the exits: flat -> MTM exactly zero everywhere
        t_after = rec.exit_session
        for t in res.sessions:
            if t >= t_after:
                self.assertEqual(sum(res.mtm_by_session[t].values()), 0.0)
                self.assertEqual(res.positions_by_session[t], {})

    def test_determinism_byte_identical(self):
        engines2 = three_symbol_engines(self.cash)
        res2 = PortfolioEngine(engines2).run(
            {s: enter_at(T0) for s in ("CL", "6J", "ES")})
        self.assertEqual(res2.to_json(), self.result.to_json())
        for sym in ("CL", "6J", "ES"):
            self.assertEqual(res2.journals[sym].to_json(),
                             self.result.journals[sym].to_json(), sym)


class TestRollWhileOtherHolds(unittest.TestCase):
    """A roll in one symbol while another symbol holds (no roll of its
    own): chain netting, journal lifecycles and cash stay exact."""

    @classmethod
    def setUpClass(cls):
        cls.cash = {"CL": 100_000.0, "6J": 100_000.0, "ES": 100_000.0}
        cls.engines = three_symbol_engines(cls.cash)
        cls.t0 = dt.date(2026, 2, 20)      # Friday before the 2026-02-27 roll
        cls.pe = PortfolioEngine({"CL": cls.engines["CL"],
                                  "6J": cls.engines["6J"]})
        cls.result = cls.pe.run({"CL": enter_at(cls.t0, time_exit=15),
                                 "6J": enter_at(cls.t0, time_exit=15)})

    def test_cl_rolled_6j_did_not(self):
        rec_cl = [r for r in self.result.journals["CL"].records
                  if r.entry_fill is not None][0]
        rec_j = [r for r in self.result.journals["6J"].records
                 if r.entry_fill is not None][0]
        self.assertEqual(len(rec_cl.rolls), 1)
        roll = rec_cl.rolls[0]
        self.assertEqual(roll.session, dt.date(2026, 2, 27))
        self.assertEqual(roll.from_contract, "CLH6")
        self.assertEqual(roll.to_contract, "CLJ6")
        kinds = [s["kind"] for s in rec_cl.gross_segments]
        self.assertIn("roll_leg_old_contract", kinds)
        self.assertEqual(rec_j.rolls, [])
        self.assertEqual(rec_j.exit_type, "TIME")

    def test_positions_netting_across_the_roll(self):
        res = self.result
        old_conid, new_conid = 11, 12
        before = dt.date(2026, 2, 26)
        roll_day = dt.date(2026, 2, 27)
        # before the roll session: CL on CLH6; 6J on 6JM6 throughout
        self.assertEqual(res.positions_by_session[before]["CL"]["conid"],
                         old_conid)
        self.assertEqual(res.positions_by_session[before]["CL"]["qty"], 1)
        # the roll executes at the close of 2026-02-27 -> end-of-session
        # state already carries the NEW chain contract with the SAME net qty
        self.assertEqual(res.positions_by_session[roll_day]["CL"]["conid"],
                         new_conid)
        self.assertEqual(res.positions_by_session[roll_day]["CL"]["qty"], 1)
        for t in res.sessions:
            if res.positions_by_session[t].get("6J"):
                self.assertEqual(res.positions_by_session[t]["6J"]["conid"],
                                 21)

    def test_cash_identity_through_the_roll_session(self):
        res = self.result
        total = sum(res.initial_cash_by_symbol.values())
        gross = costs = 0.0
        for sym in ("CL", "6J"):
            for r in res.journals[sym].records:
                if r.entry_fill is None:
                    continue
                for seg in r.gross_segments:
                    gross += seg["gross_usd"]
                costs += r.cost_components_total_usd
        self.assertAlmostEqual(res.final_cash_usd(), total + gross - costs,
                               places=6)
        # roll session cash drop == roll commissions only (the raw gap is
        # borne through segment fills, never double-charged): the record's
        # lifetime cost is 4 legs (entry + roll pair + exit) x 0.85
        rec_cl = [r for r in res.journals["CL"].records
                  if r.entry_fill is not None][0]
        self.assertAlmostEqual(rec_cl.cost_components_total_usd,
                               4.0 * 0.85, places=6)

    def test_equity_continuous_across_roll(self):
        res = self.result
        roll_day = dt.date(2026, 2, 27)
        prev = roll_day - dt.timedelta(days=1)
        while prev not in res.equity_by_session:
            prev -= dt.timedelta(days=1)
        # rebased marks + segment accounting keep equity continuous: the
        # change that day is the economic move + costs, never the raw gap
        delta = res.equity_by_session[roll_day] - res.equity_by_session[prev]
        self.assertGreater(delta, -500.0)
        self.assertLess(delta, 500.0)


class TestPortfolioPITAndLookahead(unittest.TestCase):
    """Portfolio decisions cannot see future legs — proven, not asserted."""

    def _pe(self):
        engines = three_symbol_engines({"CL": 100_000.0, "ES": 100_000.0})
        return PortfolioEngine({"CL": engines["CL"], "ES": engines["ES"]})

    def test_future_view_trap_raises_inside_portfolio(self):
        pe = self._pe()

        def abusive(ctx):
            if ctx.asof == T0:
                ctx.view.close(ctx.asof + dt.timedelta(days=3))
            return Decision(action="none")

        with self.assertRaises(FutureAccessError):
            pe.run({"CL": abusive, "ES": enter_at(T0)})

    def test_future_mutation_invariance_portfolio_wide(self):
        cutoff = dt.date(2026, 3, 31)
        strats = {"CL": enter_at(T0), "ES": enter_at(T0)}
        clean = self._pe().run(strats, cutoff=cutoff)
        dirty = self._pe().run(strats, cutoff=cutoff,
                               data_after_cutoff_mutate_seed=999)
        for sym in ("CL", "ES"):
            self.assertEqual(clean.journals[sym].to_json(),
                             dirty.journals[sym].to_json(), sym)
        self.assertEqual(clean.to_json(), dirty.to_json())

    def test_prefix_determinism_full_vs_cutoff(self):
        cutoff = dt.date(2026, 3, 31)
        strats = {"CL": enter_at(T0), "ES": enter_at(T0)}
        full = self._pe().run(strats)
        cut = self._pe().run(strats, cutoff=cutoff)
        for sym in ("CL", "ES"):
            fa = [(r.decision_session, r.entry_decision_reason, r.direction,
                   r.veto_reason) for r in full.journals[sym].records
                  if r.decision_session <= cutoff]
            fb = [(r.decision_session, r.entry_decision_reason, r.direction,
                   r.veto_reason) for r in cut.journals[sym].records]
            self.assertEqual(fa, fb, sym)
        for t in cut.sessions:
            self.assertEqual(full.equity_by_session[t],
                             cut.equity_by_session[t])

    def test_gate_audit_never_runs_ahead_of_the_calendar(self):
        engines = three_symbol_engines({"CL": 100_000.0, "ES": 100_000.0})
        pe = PortfolioEngine({"CL": engines["CL"], "ES": engines["ES"]})
        gate = PortfolioRiskGate(margin_model=MarginModel())
        res = pe.run({"CL": enter_at(T0), "ES": enter_at(T0)}, gate=gate,
                     cutoff=dt.date(2026, 1, 31))
        self.assertTrue(res.gate_audit)
        for d in res.gate_audit:
            self.assertLessEqual(dt.date.fromisoformat(d["session"]),
                                 dt.date(2026, 1, 31))


class TestMarginUtilizationSeries(unittest.TestCase):
    """Margin aggregation recorded per session (descriptive; enforcement
    is the gate's blocked entries — see test_portfolio_risk_caps)."""

    def test_margin_series_with_buffer(self):
        engines = three_symbol_engines({"ES": 100_000.0})
        pe = PortfolioEngine({"ES": engines["ES"]})
        res = pe.run({"ES": enter_at(T0)},
                     margin_model=MarginModel(buffer_fraction=0.1))
        held = [t for t in res.sessions
                if res.positions_by_session.get(t)]
        self.assertTrue(held)
        for t in held:
            m = res.margin_by_session[t]
            self.assertAlmostEqual(m["required_usd"],
                                   1.1 * 28_631.65, places=6)
            self.assertAlmostEqual(m["utilization"],
                                   m["required_usd"] / m["equity_usd"],
                                   places=9)
            self.assertFalse(m["breach"])
        # flat sessions carry no margin requirement
        flat = [t for t in res.sessions if not res.positions_by_session.get(t)]
        for t in flat:
            self.assertNotIn(t, res.margin_by_session)


class TestSleeveSeriesFromWiredRun(unittest.TestCase):
    """Sleeve daily PnL = Δ(cash + MTM) per sleeve, exposure-gated."""

    @classmethod
    def setUpClass(cls):
        cls.cash = {"CL": 100_000.0, "6J": 100_000.0, "ES": 100_000.0}
        cls.result = PortfolioEngine(three_symbol_engines(cls.cash)).run(
            {s: enter_at(T0) for s in ("CL", "6J", "ES")})

    def test_daily_pnl_equals_contribution_deltas(self):
        sleeves = sleeve_series_from_result(self.result)
        self.assertEqual(set(sleeves), {"CL", "6J", "ES"})
        prev = dict(self.result.initial_cash_by_symbol)
        for sym in ("CL", "6J", "ES"):
            for t in self.result.sessions:
                cur = (self.result.cash_by_session[t][sym]
                       + self.result.mtm_by_session[t][sym])
                if t in sleeves[sym].exposed_sessions:
                    self.assertAlmostEqual(sleeves[sym].pnl_by_session[t],
                                           cur - prev[sym], places=6,
                                           msg=f"{sym}@{t}")
                else:
                    self.assertNotIn(t, sleeves[sym].pnl_by_session)
                prev[sym] = cur

    def test_exposure_matches_journal_lifecycles(self):
        sleeves = sleeve_series_from_result(self.result)
        for sym in ("CL", "6J", "ES"):
            rec = [r for r in self.result.journals[sym].records
                   if r.entry_fill is not None][0]
            expected = {t for t in self.result.sessions
                        if rec.entry_fill.session <= t <= rec.exit_session}
            self.assertEqual(sleeves[sym].exposed_sessions, expected, sym)

    def test_sleeve_pnls_sum_to_equity_path(self):
        sleeves = sleeve_series_from_result(self.result)
        prev_eq = sum(self.result.initial_cash_by_symbol.values())
        for t in self.result.sessions:
            eq = self.result.equity_by_session[t]
            self.assertAlmostEqual(eq - prev_eq,
                                   sum(sleeves[s].pnl_by_session.get(t, 0.0)
                                       for s in sleeves), places=6)
            prev_eq = eq


class TestBadPortfolioConstruction(unittest.TestCase):
    def test_empty_portfolio_refused(self):
        with self.assertRaisesRegex(Exception, "at least one symbol"):
            PortfolioEngine({})

    def test_engine_key_must_match_symbol(self):
        engines = three_symbol_engines()
        with self.assertRaisesRegex(Exception, "engine key"):
            PortfolioEngine({"CL": engines["ES"]})

    def test_strategies_must_cover_every_symbol(self):
        engines = three_symbol_engines()
        pe = PortfolioEngine({"CL": engines["CL"], "ES": engines["ES"]})
        with self.assertRaisesRegex(Exception, "strategies"):
            pe.run({"CL": enter_at(T0)})

    def test_mutation_hook_requires_cutoff(self):
        engines = three_symbol_engines()
        pe = PortfolioEngine({"CL": engines["CL"]})
        with self.assertRaisesRegex(Exception, "cutoff"):
            pe.run({"CL": enter_at(T0)},
                   data_after_cutoff_mutate_seed=1)


if __name__ == "__main__":
    unittest.main()
