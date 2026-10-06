"""Portfolio risk-cap wiring tests (MULTIASSET-WIRING, 2026-10-02).

Laws under test:
  * margin-cap breach -> the entry is BLOCKED and journaled — never a
    silent clip, never a partial fill, never a reduced quantity;
  * structural caps (per-sleeve / concurrency / gross contracts / gross
    notional) veto at the DECISION close, counting same-close pending
    signals (the effective book), and are journaled;
  * blocked-signal accounting reconciles the gate audit trail with the
    journal's blocked records;
  * enforce_veto (the wired cap mode) never mutates quantities or the
    held book; missing notional evidence blocks (never 0).
"""
import datetime as dt
import unittest

from futbt.accounting import MarginModel
from futbt.composition import (PortfolioRiskCaps, PortfolioRiskGate,
                               blocked_signal_accounting)
from futbt.engine import PortfolioEngine
from futbt.taxonomy import PolicyError

from .test_portfolio_wiring import (T0, enter_at, three_symbol_engines)

# margin table (PUBLISHED broker tables, instruments.py): initial
MARGIN_INIT = {"6J": 3_080.00, "CL": 8_823.20, "ES": 28_631.65}


class TestEnforceVetoStandalone(unittest.TestCase):
    """The wired veto mode: never clips, never rescales, codes everything."""

    def caps(self, **kw):
        base = dict(per_sleeve_max_contracts={"6J": 1, "CL": 1, "ES": 5},
                    max_concurrent_sleeves=10, max_gross_contracts=10,
                    max_gross_notional_usd=None)
        base.update(kw)
        return PortfolioRiskCaps(**base)

    def test_per_sleeve_cap_blocks_without_clipping(self):
        caps = self.caps(per_sleeve_max_contracts={"6J": 1, "CL": 1, "ES": 2})
        out = caps.enforce_veto({"ES": 3}, {})
        self.assertEqual(out["admitted"], {})
        blk = out["blocked"]["ES"]
        self.assertEqual(blk["code"], "BLOCKED_PER_SLEEVE_CAP")
        self.assertEqual(blk["qty"], 3)          # requested qty preserved
        self.assertEqual(blk["detail"]["per_sleeve_cap"], 2)

    def test_admission_preserves_signed_quantity(self):
        out = self.caps().enforce_veto({"ES": -2}, {})
        self.assertEqual(out["admitted"], {"ES": -2})
        self.assertEqual(out["blocked"], {})

    def test_concurrency_blocks_new_sleeve_only(self):
        caps = self.caps(max_concurrent_sleeves=1)
        out = caps.enforce_veto({"CL": 1}, {"6J": 1})
        self.assertEqual(out["blocked"]["CL"]["code"],
                         "BLOCKED_MAX_CONCURRENT_SLEEVES")
        self.assertEqual(out["admitted"], {})
        # the held book is NEVER force-closed or modified
        self.assertEqual(out["held_unchanged"], {"6J": 1})

    def test_gross_contracts_blocks_when_full(self):
        caps = self.caps(max_gross_contracts=2)
        # ES per-sleeve cap is 5, so the per-sleeve check passes and the
        # gross check binds: held 1 + requested 2 > 2
        out = caps.enforce_veto({"ES": 2}, {"6J": 1})
        self.assertEqual(out["blocked"]["ES"]["code"],
                         "BLOCKED_MAX_GROSS_CONTRACTS")
        self.assertEqual(out["blocked"]["ES"]["detail"]["held_gross_contracts"],
                         1)

    def test_notional_cap_uses_abs_notional(self):
        caps = self.caps(max_gross_notional_usd=100_000.0)
        out = caps.enforce_veto({"CL": 1}, {"6J": 1},
                                {"6J": 79_125.0, "CL": 70_000.0})
        self.assertEqual(out["blocked"]["CL"]["code"],
                         "BLOCKED_GROSS_NOTIONAL_USD")
        self.assertAlmostEqual(out["blocked"]["CL"]["detail"]
                               ["added_notional_usd"], 70_000.0)

    def test_missing_notional_price_for_target_blocks(self):
        caps = self.caps(max_gross_notional_usd=1e9)
        out = caps.enforce_veto({"CL": 1}, {}, {})   # no CL price at all
        self.assertEqual(out["blocked"]["CL"]["code"],
                         "BLOCKED_NOTIONAL_PRICE_MISSING")
        self.assertEqual(out["admitted"], {})

    def test_missing_notional_price_for_held_raises(self):
        caps = self.caps(max_gross_notional_usd=100_000.0)
        with self.assertRaisesRegex(PolicyError, "missing evidence"):
            caps.enforce_veto({"CL": 1}, {"6J": 1}, {})  # held 6J unpriced

    def test_deterministic_sorted_admission(self):
        caps = self.caps(max_concurrent_sleeves=2, max_gross_contracts=10)
        out = caps.enforce_veto({"CL": 1, "ES": 1, "6J": 1}, {})
        # sorted symbol order 6J -> CL -> ES: the first two fill the
        # concurrency cap, the third is vetoed (same quantities kept)
        self.assertEqual(out["admitted"], {"6J": 1, "CL": 1})
        self.assertEqual(out["blocked"]["ES"]["code"],
                         "BLOCKED_MAX_CONCURRENT_SLEEVES")


class TestMarginCapBreachBlocksAndJournals(unittest.TestCase):
    """Fill-time margin admission: aggregated book vs aggregated equity."""

    @classmethod
    def setUpClass(cls):
        # tight cash: sorted fill order 6J -> CL -> ES; the aggregate
        # initial margin 40,534.85 exceeds the 38,500 equity only once ES
        # is added, so ES must be the blocked one
        cls.cash = {"6J": 500.0, "CL": 8_000.0, "ES": 30_000.0}
        cls.engines = three_symbol_engines(cls.cash)
        cls.gate = PortfolioRiskGate(margin_model=MarginModel())
        cls.pe = PortfolioEngine(cls.engines)
        cls.strats = {s: enter_at(T0) for s in cls.cash}
        cls.result = cls.pe.run(cls.strats, gate=cls.gate)
        cls.ungated = PortfolioEngine(
            three_symbol_engines(cls.cash)).run(cls.strats)

    def test_es_blocked_never_filled(self):
        es_records = self.result.journals["ES"].records
        self.assertEqual(len(es_records), 1)
        rec = es_records[0]
        self.assertEqual(rec.veto_reason, "BLOCKED_MARGIN_INITIAL")
        self.assertEqual(rec.decision_session, T0)
        self.assertIsNone(rec.entry_fill)          # never executed
        self.assertEqual(rec.qty, 1)               # quantity NOT clipped
        self.assertEqual(rec.direction, 0)
        self.assertIn("BLOCKED_MARGIN_INITIAL", rec.notes[0])
        self.assertIn("shortfall_usd", rec.notes[0])

    def test_blocked_detail_math_exact(self):
        rec = self.result.journals["ES"].records[0]
        # required = sum of the PUBLISHED initial margins (hypothetical
        # post-fill book incl. 6J + CL already filled this open)
        required = sum(MARGIN_INIT.values())
        # equity at the ES fill check: all initial cash less the 6J/CL
        # entry commissions already booked; no marks yet (positions just
        # filled at this open mark at their own fill price, MTM 0)
        equity = sum(self.cash.values()) - 2 * 0.85
        self.assertIn(f'"required_usd": {required}', rec.notes[0])
        self.assertIn(f'"equity_usd": {equity}', rec.notes[0])
        self.assertAlmostEqual(
            required - equity,
            float(rec.notes[0].split('"shortfall_usd": ')[1]
                  .split(",")[0].rstrip("}")), places=6)

    def test_other_sleeves_unaffected(self):
        # 6J and CL fills are IDENTICAL to the ungated run: the gate
        # blocked ES only, never touched the executed legs
        for sym in ("6J", "CL"):
            self.assertEqual(self.result.journals[sym].to_json(),
                             self.ungated.journals[sym].to_json(), sym)
            self.assertTrue([r for r in self.result.journals[sym].records
                             if r.entry_fill is not None])

    def test_blocked_signal_accounting_reconciles(self):
        acc = blocked_signal_accounting(self.result)
        self.assertEqual(acc["total_blocked"], 1)
        self.assertEqual(acc["by_code"], {"BLOCKED_MARGIN_INITIAL": 1})
        self.assertEqual(acc["by_symbol"], {"ES": 1})
        self.assertEqual(acc["gate_blocks_audited"], 1)
        self.assertEqual(acc["records"][0]["qty"], 1)

    def test_gate_audit_trail(self):
        kinds = {(d["symbol"], d["kind"]) for d in self.result.gate_audit}
        self.assertIn(("6J", "fill_admit"), kinds)
        self.assertIn(("CL", "fill_admit"), kinds)
        self.assertIn(("ES", "fill_block"), kinds)

    def test_no_positions_beyond_the_cap(self):
        # at no session does the held book breach the margin cap (every
        # breaching fill was refused before execution)
        for t, book in self.result.positions_by_session.items():
            if book:
                req = sum(MARGIN_INIT[s] for s in book)
                equity = self.result.equity_by_session[t]
                self.assertLessEqual(req, equity + 1e-6,
                                     msg=f"{t}: {book}")


class TestStructuralCapVetoes(unittest.TestCase):
    """Decision-close vetoes: caps count same-close pending signals."""

    def _run(self, caps, strats=None, cash=None):
        cash = cash or {"6J": 100_000.0, "CL": 100_000.0, "ES": 100_000.0}
        engines = three_symbol_engines(cash)
        gate = PortfolioRiskGate(caps=caps)
        strats = strats or {s: enter_at(T0) for s in cash}
        pe = PortfolioEngine({s: engines[s] for s in strats})
        return pe.run(strats, gate=gate), gate

    def test_per_sleeve_cap_veto_at_decision(self):
        caps = PortfolioRiskCaps(per_sleeve_max_contracts={"ES": 1},
                                 max_concurrent_sleeves=10,
                                 max_gross_contracts=10)
        result, gate = self._run(
            caps, strats={"ES": enter_at(T0, qty=2)})
        rec = result.journals["ES"].records[0]
        self.assertEqual(rec.decision_session, T0)
        self.assertEqual(rec.veto_reason, "BLOCKED_PER_SLEEVE_CAP")
        self.assertEqual(rec.qty, 2)              # never clipped to 1
        self.assertIsNone(rec.entry_fill)
        self.assertTrue(all(not book for book
                            in result.positions_by_session.values()))
        self.assertEqual(
            blocked_signal_accounting(result)["by_code"],
            {"BLOCKED_PER_SLEEVE_CAP": 1})

    def test_concurrency_counts_pending_same_close_signals(self):
        # all three decide at the SAME close; without the effective book
        # each would see an empty portfolio and over-admit. Sorted symbol
        # order 6J -> CL -> ES: the third signal must be vetoed.
        caps = PortfolioRiskCaps(
            per_sleeve_max_contracts={"6J": 1, "CL": 1, "ES": 1},
            max_concurrent_sleeves=2, max_gross_contracts=10)
        result, gate = self._run(caps)
        es = result.journals["ES"].records[0]
        self.assertEqual(es.veto_reason, "BLOCKED_MAX_CONCURRENT_SLEEVES")
        self.assertEqual(es.decision_session, T0)
        self.assertIsNone(es.entry_fill)
        for sym in ("6J", "CL"):
            self.assertTrue([r for r in result.journals[sym].records
                             if r.entry_fill is not None], sym)
        acc = blocked_signal_accounting(result)
        self.assertEqual(acc["by_code"],
                         {"BLOCKED_MAX_CONCURRENT_SLEEVES": 1})

    def test_gross_contracts_veto(self):
        caps = PortfolioRiskCaps(
            per_sleeve_max_contracts={"6J": 1, "CL": 1, "ES": 1},
            max_concurrent_sleeves=10, max_gross_contracts=2)
        result, _ = self._run(caps)
        es = result.journals["ES"].records[0]
        self.assertEqual(es.veto_reason, "BLOCKED_MAX_GROSS_CONTRACTS")
        self.assertEqual(es.qty, 1)
        # gross contracts never exceeded the cap on any session
        for t, book in result.positions_by_session.items():
            self.assertLessEqual(sum(abs(v["qty"]) for v in book.values()),
                                 2, msg=str(t))

    def test_notional_veto_with_real_prices(self):
        # 6J notional ~0.00633 x 12.5M = ~79k; adding CL (~70k) busts a
        # 100k cap -> CL vetoed at the decision close with exact notional
        caps = PortfolioRiskCaps(
            per_sleeve_max_contracts={"6J": 1, "CL": 1, "ES": 1},
            max_concurrent_sleeves=10, max_gross_contracts=10,
            max_gross_notional_usd=100_000.0)
        result, _ = self._run(caps, strats={"6J": enter_at(T0),
                                            "CL": enter_at(T0)})
        cl = result.journals["CL"].records[0]
        self.assertEqual(cl.veto_reason, "BLOCKED_GROSS_NOTIONAL_USD")
        self.assertIsNone(cl.entry_fill)
        self.assertTrue([r for r in result.journals["6J"].records
                         if r.entry_fill is not None])

    def test_caps_never_touch_filled_quantities(self):
        # across every vetoed scenario, no journal record ever carries a
        # quantity different from what its strategy requested
        caps = PortfolioRiskCaps(
            per_sleeve_max_contracts={"6J": 1, "CL": 1, "ES": 1},
            max_concurrent_sleeves=1, max_gross_contracts=10)
        strats = {"6J": enter_at(T0, qty=1), "CL": enter_at(T0, qty=1),
                  "ES": enter_at(T0, qty=1)}
        result, _ = self._run(caps, strats=strats)
        for sym, journal in result.journals.items():
            for r in journal.records:
                if r.entry_fill is not None:
                    self.assertEqual(abs(r.entry_fill.signed_qty), 1, sym)
                    self.assertEqual(r.qty, 1, sym)
                else:
                    self.assertEqual(r.qty, 1, sym)  # blocked: qty intact


class TestGateWithoutCapsOrMargin(unittest.TestCase):
    def test_noop_gate_admits_everything(self):
        engines = three_symbol_engines({"CL": 100_000.0})
        gate = PortfolioRiskGate()          # no caps, no margin model
        pe = PortfolioEngine({"CL": engines["CL"]})
        res = pe.run({"CL": enter_at(T0)}, gate=gate)
        self.assertTrue([r for r in res.journals["CL"].records
                         if r.entry_fill is not None])
        self.assertEqual(blocked_signal_accounting(res)["total_blocked"], 0)


if __name__ == "__main__":
    unittest.main()
