"""Cost model tests: provenance tags, incompleteness refusal, declared
slippage hook, stress levels, sampled-BBO caveat, ES all-in example."""
import unittest

from futbt.costs import (SAMPLED_BBO_CAVEAT, CostBook,
                         IncompleteCostModelError, VALID_STRESS_LEVELS)
from futbt.taxonomy import CostProvenance


class TestCostBookBasics(unittest.TestCase):
    def test_components_and_provenance(self):
        book = CostBook.for_symbol("CL")
        c = book.components
        self.assertEqual(c["commission_broker"].provenance,
                         CostProvenance.PUBLISHED)
        self.assertEqual(c["commission_broker"].usd_per_contract_side, 0.85)
        self.assertEqual(c["exchange_plus_regulatory"].provenance,
                         CostProvenance.NOT_RUN)
        self.assertIsNone(c["exchange_plus_regulatory"].usd_per_contract_side)
        self.assertEqual(c["spread"].provenance, CostProvenance.MEASURED)
        self.assertEqual(c["spread"].usd_per_contract_side, 30.0)
        self.assertIn(SAMPLED_BBO_CAVEAT, c["spread"].note)
        self.assertEqual(c["slippage"].provenance, CostProvenance.NOT_RUN)

    def test_es_documented_example_reproduced_for_commissions(self):
        book = CostBook.for_symbol("ES")
        comm = book.commission_cash_usd(1)
        self.assertAlmostEqual(comm["usd"], 2.24, places=9)  # 0.85+1.38+0.01
        self.assertEqual(comm["missing"], [])
        # a COMPLETE total is still refused while slippage is NOT_RUN —
        # no fabricated zero
        with self.assertRaises(IncompleteCostModelError):
            book.total_per_contract_side()
        book.declare_slippage(10.0, "owner", "declared nonzero scenario")
        tot = book.total_per_contract_side()
        self.assertFalse(tot["cost_incomplete"])
        self.assertAlmostEqual(tot["total_usd_per_contract_side"],
                               2.24 + 12.50 + 10.0, places=9)

    def test_non_es_complete_total_refused(self):
        book = CostBook.for_symbol("CL")
        with self.assertRaises(IncompleteCostModelError):
            book.total_per_contract_side()
        partial = book.total_per_contract_side(allow_incomplete=True)
        self.assertTrue(partial["cost_incomplete"])
        self.assertIn("exchange_plus_regulatory", partial["missing_components"])
        # partial total = 0.85 + 30.0 spread; slippage NOT_RUN stays out
        self.assertAlmostEqual(partial["total_usd_per_contract_side"], 30.85,
                               places=9)

    def test_round_trip(self):
        book = CostBook.for_symbol("ES")
        book.declare_slippage(10.0, "owner", "declared scenario")
        rt = book.round_trip_per_contract()
        self.assertAlmostEqual(rt["round_trip_usd_per_contract"],
                               2.0 * (2.24 + 12.50 + 10.0), places=9)


class TestDeclaredSlippage(unittest.TestCase):
    def test_declared_slippage_must_be_nonzero(self):
        book = CostBook.for_symbol("CL")
        with self.assertRaisesRegex(Exception, "NONZERO"):
            book.declare_slippage(0.0, "owner", "scenario")
        with self.assertRaisesRegex(Exception, "NONZERO"):
            book.declare_slippage(-5.0, "owner", "scenario")

    def test_declaration_requires_identity_and_rationale(self):
        book = CostBook.for_symbol("CL")
        with self.assertRaises(Exception):
            book.declare_slippage(10.0, "", "rationale")
        with self.assertRaises(Exception):
            book.declare_slippage(10.0, "owner", "")

    def test_declared_slippage_flows_into_totals(self):
        book = CostBook.for_symbol("CL")
        book.declare_slippage(12.0, "owner", "one tick of CL slippage "
                                        "declared for stress scenarios")
        slip = book.components["slippage"]
        self.assertEqual(slip.provenance, CostProvenance.DECLARED)
        self.assertEqual(slip.declared_by, "owner")
        partial = book.total_per_contract_side(allow_incomplete=True)
        self.assertAlmostEqual(partial["total_usd_per_contract_side"], 42.85,
                               places=9)


class TestStressInterface(unittest.TestCase):
    def test_stress_levels_exposed(self):
        self.assertEqual(CostBook.stress_levels(), (1.0, 1.5, 2.0))

    def test_invalid_stress_refused(self):
        book = CostBook.for_symbol("ES")
        for bad in (0.5, 3.0, 1.2):
            with self.assertRaisesRegex(Exception, "stress"):
                book.stressed_copy(bad)

    def test_stress_scales_variable_not_published_commission(self):
        book = CostBook.for_symbol("ES")
        book.declare_slippage(10.0, "owner", "declared scenario")
        s15 = book.stressed_copy(1.5)
        self.assertAlmostEqual(
            s15.components["spread"].usd_per_contract_side, 12.50 * 1.5, places=9)
        self.assertAlmostEqual(
            s15.components["slippage"].usd_per_contract_side, 15.0, places=9)
        self.assertAlmostEqual(
            s15.components["commission_broker"].usd_per_contract_side, 0.85,
            places=9)  # published schedule fee unchanged
        self.assertIn("[stressed x1.5]", s15.components["spread"].note)

    def test_fill_adjustment_worsens_buy_and_sell(self):
        book = CostBook.for_symbol("ES")
        buy = book.fill_adjustment_usd(+1)
        sell = book.fill_adjustment_usd(-1)
        self.assertAlmostEqual(buy["total_usd"], 6.25, places=9)   # half 12.5
        self.assertAlmostEqual(sell["total_usd"], 6.25, places=9)
        self.assertTrue(any("does NOT prove" in cav for cav in buy["caveats"]))
        book.declare_slippage(10.0, "owner", "scenario")
        buy2 = book.fill_adjustment_usd(+1)
        self.assertAlmostEqual(buy2["total_usd"], 16.25, places=9)

    def test_commission_cash_discloses_missing_exchange_fee(self):
        cl = CostBook.for_symbol("CL").commission_cash_usd(1)
        self.assertEqual(cl["usd"], 0.85)
        self.assertIn("exchange_plus_regulatory", cl["missing"])
        es = CostBook.for_symbol("ES").commission_cash_usd(2)
        self.assertAlmostEqual(es["usd"], 2 * 2.24, places=9)
        self.assertEqual(es["missing"], [])


if __name__ == "__main__":
    unittest.main()
