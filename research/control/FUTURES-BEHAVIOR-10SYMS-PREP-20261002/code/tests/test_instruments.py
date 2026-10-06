"""Instrument table tests: tick identities, 6J orientation, SI class, margins."""
import unittest

from futbt.instruments import (MARGINS, all_symbols, get_instrument,
                               spec_evidence)
from futbt.taxonomy import CostProvenance, EvidenceTag


class TestInstruments(unittest.TestCase):
    def test_all_ten_symbols_present(self):
        self.assertEqual(
            sorted(all_symbols()),
            ["6A", "6B", "6E", "6J", "CL", "ES", "GC", "NG", "NQ", "SI"])

    def test_tick_value_identities(self):
        expected = {
            "NQ": 5.00, "ES": 12.50, "CL": 10.00, "NG": 10.00, "GC": 10.00,
            "SI": 25.00, "6E": 6.25, "6J": 6.25, "6B": 6.25, "6A": 5.00,
        }
        for sym, tv in expected.items():
            spec = get_instrument(sym)
            self.assertAlmostEqual(spec.tick_value_usd, tv, places=9,
                                   msg=f"{sym} tick value")
            self.assertEqual(spec.tick_value_usd,
                             spec.multiplier * spec.min_tick)

    def test_6j_orientation_usd_per_jpy(self):
        spec = get_instrument("6J")
        self.assertEqual(spec.multiplier, 12_500_000)
        self.assertEqual(spec.min_tick, 5e-07)
        self.assertIn("USD per JPY", spec.quote_convention)
        # one long contract, +1 tick -> +6.25 USD (no inversion anywhere)
        from futbt.accounting import pnl_for_symbol
        self.assertAlmostEqual(
            pnl_for_symbol("6J", 0.0, spec.min_tick, 1), 6.25, places=9)

    def test_si_is_5000oz_class(self):
        spec = get_instrument("SI")
        self.assertEqual(spec.trading_class, "SI")
        self.assertEqual(spec.multiplier, 5000)
        with self.assertRaisesRegex(Exception, "5000oz|SIL"):
            import dataclasses
            bad = dataclasses.replace(spec, trading_class="SIL")
            bad.validate()

    def test_fx_tick_conflicts_recorded(self):
        for sym in ("6E", "6J", "6B", "6A"):
            self.assertTrue(get_instrument(sym).fx_tick_conflict_note,
                            f"{sym} must record the tick-source conflict")

    def test_unknown_symbol_raises(self):
        with self.assertRaises(KeyError):
            get_instrument("ZZ")

    def test_margins_published_with_sources(self):
        for sym in all_symbols():
            mq = MARGINS[sym]
            self.assertEqual(mq.provenance, CostProvenance.PUBLISHED)
            self.assertGreater(mq.initial_usd, mq.maintenance_usd)
            self.assertTrue(mq.source.startswith("NinjaTrader"))
            self.assertIn("NOT_RUN", mq.note)  # CME SPAN official not fetched

    def test_spec_evidence_bundle(self):
        ev = spec_evidence("CL")
        self.assertEqual(ev["multiplier_minTick_timeZone"]["tag"],
                         EvidenceTag.OBSERVED.value)
        self.assertEqual(ev["unit_cycle_lastTrade margins"]["tag"],
                         EvidenceTag.FACT.value)
        self.assertIn("NOT_RUN", ev["margin_quote"]["cme_span_official"])


if __name__ == "__main__":
    unittest.main()
