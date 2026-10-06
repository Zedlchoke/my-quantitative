"""Roll engine tests: calendar baseline exactness, PIT legality of the
volume rule, causal adjustment, raw execution series."""
import datetime as dt
import unittest

from futbt.roll import (ExpiryMonthBasis, RollEngine, VolumeRollRule,
                        build_universe_roll_tables, roll_decision_session)
from futbt.taxonomy import PolicyError

from .helpers import FixtureTestCase


class TestCalendarRollOnFixture(FixtureTestCase):
    def test_calendar_rolls_match_known_truth_all_symbols(self):
        for sym in ("CL", "6J", "ES"):
            eng = RollEngine(sym, self.contracts_for(sym), self.uni.calendar)
            table = eng.build_roll_table()
            exp = self.uni.expected_calendar_rolls(sym)
            self.assertEqual(len(table.rows), len(exp), sym)
            for (t, old, new), row in zip(exp, table.rows):
                self.assertEqual(row.decision_session, t, f"{sym} roll date")
                self.assertEqual((row.old_conid, row.new_conid), (old, new))
                self.assertEqual(row.reason_code, "CALENDAR_EXPIRY_MONTH_BASELINE")

    def contracts_for(self, sym):
        from futbt.rawdata import contracts_by_symbol
        return contracts_by_symbol(self.contracts)[sym]

    def test_raw_price_gap_equals_known_truth(self):
        for sym in ("CL", "6J", "ES"):
            eng = RollEngine(sym, self.contracts_for(sym), self.uni.calendar)
            table = eng.build_roll_table()
            for r in table.rows:
                oc = self.uni.close(sym, r.old_conid, r.decision_session)
                nc = self.uni.close(sym, r.new_conid, r.decision_session)
                self.assertAlmostEqual(r.raw_price_gap, nc - oc, places=10)
                if oc and oc > 0 and nc and nc > 0:
                    self.assertAlmostEqual(r.adjustment_ratio, nc / oc, places=12)

    def test_roll_rule_uses_no_market_data(self):
        eng = RollEngine("CL", self.contracts_for("CL"), self.uni.calendar)
        cfg = eng.build_roll_table().rule_config
        self.assertTrue(cfg["decision_inputs"]["inputs"][0]
                        .startswith("expiry_schedule"))
        self.assertIn("PIT", cfg["decision_inputs"]["pit_note"])

    def test_oi_fields_not_run(self):
        eng = RollEngine("CL", self.contracts_for("CL"), self.uni.calendar)
        row = eng.build_roll_table().rows[0]
        self.assertIsNone(row.old_oi_at_decision)
        self.assertIsNone(row.new_oi_at_decision)
        self.assertIn("NOT_RUN", row.to_dict()["oi_status"]["tag"])


class TestCausalAdjustment(FixtureTestCase):
    def _eng_table(self, sym="ES"):
        from futbt.rawdata import contracts_by_symbol
        eng = RollEngine(sym, contracts_by_symbol(self.contracts)[sym],
                         self.uni.calendar)
        return eng, eng.build_roll_table()

    def test_ratio_adjustment_refuses_negative_prices(self):
        from futbt.rawdata import contracts_by_symbol
        eng = RollEngine("CL", contracts_by_symbol(self.contracts)["CL"],
                         self.uni.calendar)
        table = eng.build_roll_table()
        with self.assertRaisesRegex(PolicyError, "negative"):
            eng.adjusted_chain(table, how="ratio")

    def test_factor_zero_before_first_roll(self):
        eng, table = self._eng_table()
        first = table.rows[0].decision_session
        self.assertEqual(eng.adjustment_factor_at(table, dt.date(2024, 7, 5)), 0.0)
        self.assertEqual(eng.adjustment_factor_at(table, first), 0.0)

    def test_factor_causal_between_rolls(self):
        eng, table = self._eng_table()
        r1, r2 = table.rows[0], table.rows[1]
        mid = r1.decision_session + dt.timedelta(days=3)
        self.assertAlmostEqual(
            eng.adjustment_factor_at(table, mid), r1.raw_price_gap, places=10)
        after2 = r2.decision_session + dt.timedelta(days=3)
        self.assertAlmostEqual(
            eng.adjustment_factor_at(table, after2),
            r1.raw_price_gap + r2.raw_price_gap, places=10)

    def test_additive_adjustment_removes_roll_jump(self):
        eng, table = self._eng_table("ES")
        adj = eng.adjusted_chain(table, how="additive")
        raw = eng.raw_chain(table)
        for r in table.rows[:6]:
            t = r.decision_session
            nxt = self.uni.calendar.next_session(t)
            # adjusted move across the roll == same-contract daily move
            new_close_next = self.uni.close("ES", r.new_conid, nxt)
            new_close_t = self.uni.close("ES", r.new_conid, t)
            self.assertAlmostEqual(
                adj[nxt]["c"] - adj[t]["c"],
                new_close_next - new_close_t, places=9,
                msg=f"adjusted series jumps at roll {t}")
            # raw series DOES jump (by construction of the fixture offsets)
            self.assertAlmostEqual(raw[nxt][2]["c"] - raw[t][2]["c"]
                                   - (new_close_next - new_close_t),
                                   r.raw_price_gap, places=9)

    def test_raw_chain_never_adjusted_and_carries_contract_identity(self):
        eng, table = self._eng_table("CL")
        raw = eng.raw_chain(table)
        adj = eng.adjusted_chain(table, how="additive")
        for t in list(raw)[:5]:
            self.assertEqual(raw[t][2]["c"], adj[t]["raw_c"])
        # on a roll decision session the OLD contract is still the vehicle
        r = table.rows[0]
        self.assertEqual(raw[r.decision_session][0], r.old_contract)
        nxt = self.uni.calendar.next_session(r.decision_session)
        self.assertEqual(raw[nxt][0], r.new_contract)


class TestVolumeRollPITLegality(FixtureTestCase):
    def test_final_same_day_volume_configuration_refused(self):
        with self.assertRaisesRegex(PolicyError, "final same-day"):
            VolumeRollRule(use_same_day_final_volume=True)

    def test_zero_cutoff_lag_refused(self):
        with self.assertRaisesRegex(PolicyError, "cutoff_lag_sessions"):
            VolumeRollRule(cutoff_lag_sessions=0)

    def test_volume_rolls_are_strictly_earlier_than_calendar(self):
        eng_v = RollEngine("CL", self.contracts_for("CL"), self.uni.calendar,
                           rule=VolumeRollRule(confirm_sessions=2))
        vtable = eng_v.build_roll_table()
        ctable = RollEngine("CL", self.contracts_for("CL"),
                            self.uni.calendar).build_roll_table()
        self.assertTrue(vtable.rows)
        self.assertLess(vtable.rows[0].decision_session,
                        ctable.rows[0].decision_session)

    def test_volume_rows_carry_pit_cutoff_and_volumes(self):
        eng = RollEngine("CL", self.contracts_for("CL"), self.uni.calendar,
                         rule=VolumeRollRule(confirm_sessions=2))
        for r in eng.build_roll_table().rows:
            self.assertLess(r.volume_cutoff_session, r.decision_session)
            self.assertIsNotNone(r.old_volume_at_decision)
            self.assertIsNotNone(r.new_volume_at_decision)
            self.assertGreaterEqual(r.new_volume_at_decision,
                                    r.old_volume_at_decision)

    def contracts_for(self, sym):
        from futbt.rawdata import contracts_by_symbol
        return contracts_by_symbol(self.contracts)[sym]


class TestDeliveryMonthBasisNotRun(unittest.TestCase):
    def test_delivery_month_basis_raises_not_run(self):
        from futbt.rawdata import ContractData, ContractIdentity
        ident = ContractIdentity("CL", "CLX6", 1, dt.date(2026, 10, 20))
        cd = ContractData(identity=ident)
        cal = None
        with self.assertRaisesRegex(PolicyError, "NOT_RUN"):
            roll_decision_session(cd, cal, ExpiryMonthBasis.DELIVERY_MONTH)


class TestUniverseTables(FixtureTestCase):
    def test_build_universe_roll_tables(self):
        tables = build_universe_roll_tables(self.contracts, self.uni.calendar)
        self.assertEqual(sorted(tables), ["6J", "CL", "ES"])
        for sym, t in tables.items():
            self.assertEqual(len(t.rows),
                             len(self.uni.expected_calendar_rolls(sym)))


if __name__ == "__main__":
    unittest.main()
