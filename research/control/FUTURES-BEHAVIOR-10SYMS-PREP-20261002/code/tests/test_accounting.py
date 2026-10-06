"""Accounting kernel tests: negative CL prices, 6J orientation, ticks,
cash ledger, margin interface, close-only fill ban."""
import datetime as dt
import unittest

from futbt.accounting import (CashLedger, Fill, MarginModel,
                              NegativePriceLogForbidden, Position,
                              check_price_plausible, log_return, pnl,
                              pnl_for_symbol, round_to_tick, usd_notional)
from futbt.taxonomy import PolicyError


class TestPnLAndPrices(unittest.TestCase):
    def test_negative_cl_prices_arithmetic(self):
        # long from -37.63 to -30.00: +7.63/bbl * 1000
        self.assertAlmostEqual(pnl(-37.63, -30.00, 1, 1000), 7630.0, places=9)
        # long from -10 to -25: loses 15,000
        self.assertAlmostEqual(pnl(-10.0, -25.0, 1, 1000), -15000.0, places=9)
        # short into negative territory profits
        self.assertAlmostEqual(pnl(20.0, -5.0, -1, 1000), 25000.0, places=9)

    def test_negative_price_crossing_zero_no_log(self):
        with self.assertRaises(NegativePriceLogForbidden):
            log_return(-10.0, 5.0)
        with self.assertRaises(NegativePriceLogForbidden):
            log_return(5.0, 0.0)
        self.assertAlmostEqual(log_return(100.0, 110.0), 0.09531017980432493,
                               places=12)

    def test_pnl_for_symbol_uses_instrument_table(self):
        self.assertAlmostEqual(pnl_for_symbol("ES", 5000.0, 5001.0, 1), 50.0)
        self.assertAlmostEqual(pnl_for_symbol("6J", 0.006330, 0.006331, 1),
                               12.50, places=6)  # 2 ticks x $6.25
        self.assertAlmostEqual(pnl_for_symbol("CL", 80.0, 80.01, -2), -20.0)

    def test_6j_inverted_quote_rejected(self):
        with self.assertRaisesRegex(PolicyError, "inverted"):
            check_price_plausible("6J", 157.2)
        with self.assertRaisesRegex(PolicyError, "inverted"):
            usd_notional("6J", 157.2, 1)
        self.assertAlmostEqual(usd_notional("6J", 0.0064, 1), 80000.0, places=3)


class TestTickRounding(unittest.TestCase):
    def test_nearest_floor_ceil(self):
        self.assertEqual(round_to_tick(80.123, 0.01), 80.12)
        self.assertEqual(round_to_tick(80.129, 0.01, "floor"), 80.12)
        self.assertEqual(round_to_tick(80.121, 0.01, "ceil"), 80.13)
        self.assertEqual(round_to_tick(5000.13, 0.25), 5000.25)
        self.assertEqual(round_to_tick(5000.12, 0.25, "floor"), 5000.0)

    def test_6j_sub_micro_tick(self):
        self.assertEqual(round_to_tick(0.0063304, 5e-07), 0.0063305)
        self.assertEqual(round_to_tick(0.0063302, 5e-07, "floor"), 0.00633)

    def test_negative_price_rounding(self):
        self.assertEqual(round_to_tick(-37.636, 0.01), -37.64)
        self.assertEqual(round_to_tick(-37.631, 0.01, "ceil"), -37.63)


class TestFillGuard(unittest.TestCase):
    def test_fill_on_close_only_bar_forbidden(self):
        with self.assertRaisesRegex(PolicyError, "close-only"):
            Fill(session=dt.date(2026, 1, 5), symbol="CL", local_symbol="CLF6",
                 conid=1, signed_qty=1, price=80.0, is_close_only_bar=True)

    def test_fill_on_live_bar_ok(self):
        f = Fill(session=dt.date(2026, 1, 5), symbol="CL", local_symbol="CLF6",
                 conid=1, signed_qty=1, price=80.0, is_close_only_bar=False)
        self.assertEqual(f.signed_qty, 1)


class TestCashLedger(unittest.TestCase):
    def test_reconcile_ok_and_detects_tampering(self):
        led = CashLedger(1_000_000.0)
        led.apply("realize", dt.date(2026, 1, 5), 500.0, "trade1")
        led.apply("cost", dt.date(2026, 1, 5), -4.48, "commissions")
        self.assertEqual(led.reconcile()["final"], 1_000_495.52)
        led.cash += 100.0  # tamper
        with self.assertRaises(AssertionError):
            led.reconcile()

    def test_negative_cash_allowed_but_recorded(self):
        led = CashLedger(100.0)
        led.apply("realize", dt.date(2026, 4, 20), -5000.0, "apr-2020")
        self.assertEqual(led.cash, -4900.0)


class TestPositionRoll(unittest.TestCase):
    def test_roll_preserves_qty_and_records_event(self):
        pos = Position("CL", "CLX6", 1, 2, 80.0, dt.date(2026, 9, 1))
        pos.with_roll("CLZ6", 2, 81.5, dt.date(2026, 9, 30), 1.5)
        self.assertEqual((pos.signed_qty, pos.local_symbol, pos.conid),
                         (2, "CLZ6", 2))
        self.assertEqual(pos.avg_entry_price, 81.5)
        self.assertEqual(len(pos.rolls), 1)
        self.assertEqual(pos.rolls[0]["raw_gap"], 1.5)

    def test_cannot_roll_flat(self):
        pos = Position("CL", "CLX6", 1, 0, 80.0, dt.date(2026, 9, 1))
        with self.assertRaises(PolicyError):
            pos.with_roll("CLZ6", 2, 81.5, dt.date(2026, 9, 30), 1.5)


class TestMarginInterface(unittest.TestCase):
    def test_requirement_from_published_table(self):
        mm = MarginModel()
        req = mm.requirement("NQ", 2)
        self.assertAlmostEqual(req.initial_usd, 46473.17 * 2, places=6)
        self.assertIn("NOT_RUN", req.official_cme_span)

    def test_breach_detection(self):
        mm = MarginModel(buffer_fraction=0.10)
        status = mm.check({"ES": 1}, equity_usd=10_000.0)
        self.assertTrue(status["breach"])
        self.assertGreater(status["shortfall_usd"], 0)
        ok = mm.check({"6B": 1}, equity_usd=100_000.0, level="maintenance")
        self.assertFalse(ok["breach"])

    def test_buffer_fraction_must_be_nonnegative(self):
        with self.assertRaises(ValueError):
            MarginModel(buffer_fraction=-0.1)


if __name__ == "__main__":
    unittest.main()
