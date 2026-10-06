"""Ingestion + contract-identity tests: DBN/CSV/JSONL parity, definition
A/M/D semantics, identity traps (6J scale, SI multiplier), first-notice
law, continuous execution guard (NO-CONTFUT-fill law)."""
from __future__ import annotations

import unittest

from futbt.dbn import spec as S
from futbt.dbn.fixtures import build_fixture_dir
from futbt.dbn.ingest import (ContractRegistry, DefinitionAction, IngestError,
                              build_registry, ingest_file, require_outright,
                              resolve_first_notice)
from futbt.taxonomy import PolicyError


class FixtureBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.tmp = tempfile.TemporaryDirectory(prefix="dbn_ing_")
        cls.universe = build_fixture_dir(cls.tmp.name)
        cls.frames = [ingest_file(f"{cls.tmp.name}/{n}")
                      for n in sorted(cls.universe.files)
                      if n.endswith(".dbn") and "continuous" not in n]
        cls.registry = build_registry(cls.frames)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()


class TestIngestParity(FixtureBase):
    def test_dbn_bars_ingested(self):
        bars = [b for f in self.frames for b in f.bars]
        self.assertGreater(len(bars), 400)
        self.assertTrue(all(b.rtype in S.OHLCV_RTYPES for b in bars))

    def test_csv_ingest_equals_dbn_ingest(self):
        csv_frames = [ingest_file(f"{self.tmp.name}/{n}")
                      for n in sorted(self.universe.files)
                      if n.endswith(".csv")]
        csv_reg = build_registry(csv_frames)
        self.assertEqual(sorted(csv_reg.by_raw), sorted(self.registry.by_raw))
        for raw in self.registry.by_raw:
            a = self.registry.require(raw_symbol=raw)
            b = csv_reg.require(raw_symbol=raw)
            self.assertEqual((a.instrument_id, a.expiration,
                              a.min_price_increment),
                             (b.instrument_id, b.expiration,
                              b.min_price_increment), raw)

    def test_jsonl_ingest_equals_dbn_bars(self):
        jf = ingest_file(f"{self.tmp.name}/"
                         "ohlcv-1d.glbx-mdp3.raw_symbol.synthetic.jsonl")
        bf = [f for f in self.frames
              if f.source.endswith("ohlcv-1d.glbx-mdp3.raw_symbol.synthetic.dbn")][0]
        self.assertEqual(sorted(b.ts_event for b in bf.bars),
                         sorted(b.ts_event for b in jf.bars))
        self.assertEqual(sorted(b.close for b in bf.bars),
                         sorted(b.close for b in jf.bars))

    def test_zst_refused_typed(self):
        p = f"{self.tmp.name}/whatever.dbn.zst"
        open(p, "wb").write(b"fake")
        with self.assertRaises(IngestError) as cm:
            ingest_file(p)
        self.assertIn("NOT_IMPLEMENTED", str(cm.exception))

    def test_statistics_frame_fields(self):
        stats = [s for f in self.frames for s in f.statistics]
        self.assertGreater(len(stats), 400)
        for s in stats:
            self.assertIn(s.stat_type, S.STAT_TYPE_NAMES)
            self.assertIn(s.update_action, (1, 2))


class TestContractIdentity(FixtureBase):
    def test_identity_resolved_for_all_listed(self):
        for raw, truth in self.universe.contracts.items():
            if raw == "CLV6":
                continue                       # deleted at expiry
            ident = self.registry.require(raw_symbol=raw)
            self.assertEqual(ident.instrument_id, truth.instrument_id, raw)
            self.assertEqual(ident.expiration, truth.expiration_ns, raw)
            self.assertEqual(ident.activation, truth.activation_ns, raw)
            self.assertEqual(ident.maturity_year, truth.maturity_year, raw)
            self.assertEqual(ident.maturity_month, truth.maturity_month, raw)

    def test_expiry_and_listing_from_definitions(self):
        ident = self.registry.require(raw_symbol="CLZ6")
        self.assertEqual(ident.maturity_year, 2026)
        self.assertEqual(ident.maturity_month, 12)
        self.assertLess(ident.activation, ident.expiration)

    def test_deleted_contract_unresolved(self):
        # CLV6's last definition action is a DELETE at expiration
        with self.assertRaises(IngestError):
            self.registry.require(raw_symbol="CLV6")

    def test_modify_action_keeps_identity(self):
        # NQZ6 got an M action; identity stays live and consistent
        ident = self.registry.require(raw_symbol="NQZ6")
        self.assertEqual(ident.instrument_id,
                         self.universe.contracts["NQZ6"].instrument_id)

    def test_instrument_id_lookup(self):
        ident = self.registry.require(
            instrument_id=self.universe.contracts["ESZ6"].instrument_id)
        self.assertEqual(ident.raw_symbol, "ESZ6")
        self.assertEqual(self.registry.raw_for(ident.instrument_id), "ESZ6")

    def test_identity_clash_detected(self):
        reg = ContractRegistry()

        def act(inst, sym, action="A"):
            return DefinitionAction(
                ts_event=1, instrument_id=inst, raw_symbol=sym, action=action,
                activation=0, expiration=10, maturity_year=2026,
                maturity_month=12, min_price_increment=1,
                unit_of_measure_qty=1_000_000_000, exchange="CME",
                security_type="FUT", instrument_class="F")

        reg.apply(act(1, "ESZ6"))
        with self.assertRaises(IngestError):
            reg.apply(act(2, "ESZ6"))          # same raw, different id

    def test_unknown_security_action_fails_closed(self):
        reg = ContractRegistry()
        with self.assertRaises(IngestError):
            reg.apply(DefinitionAction(
                ts_event=1, instrument_id=1, raw_symbol="X", action="~",
                activation=0, expiration=10, maturity_year=2026,
                maturity_month=1, min_price_increment=1,
                unit_of_measure_qty=1, exchange="CME",
                security_type="FUT", instrument_class="F"))

    def test_bars_resolve_to_identity(self):
        bars = [b for f in self.frames for b in f.bars]
        for b in bars:
            raw = self.registry.raw_for(b.instrument_id)
            self.assertIn(raw, self.universe.contracts)


class TestIdentityTraps(FixtureBase):
    def test_6j_usd_per_jpy_scale(self):
        ident = self.registry.require(raw_symbol="6JZ6")
        self.assertEqual(ident.min_price_increment, 500)      # 5e-7
        self.assertEqual(ident.tick_decimal_str, "0.000000500")
        # ~0.006335 level, i.e. USD per JPY — NOT the ~157 inverted quote
        self.assertAlmostEqual(
            self.universe.contracts["6JZ6"].tick_nanos / 1e9, 5e-7)
        self.registry.check_identity_traps("6JZ6")            # must pass

    def test_6j_inverted_tick_trap(self):
        from futbt.dbn.ingest import ContractIdentity
        good = self.registry.require(raw_symbol="6JZ6")
        bad_ident = ContractIdentity(
            raw_symbol="6JZ6", instrument_id=good.instrument_id,
            activation=good.activation, expiration=good.expiration,
            maturity_year=good.maturity_year,
            maturity_month=good.maturity_month,
            min_price_increment=628_000_000,    # ~0.628: inverted-quote scale
            unit_of_measure_qty=good.unit_of_measure_qty,
            exchange=good.exchange)
        bad = ContractRegistry()
        bad.by_raw["6JZ6"] = bad_ident
        bad.by_id[bad_ident.instrument_id] = bad_ident
        with self.assertRaises(IngestError):
            bad.check_identity_traps("6JZ6")

    def test_si_5000oz_class(self):
        ident = self.registry.require(raw_symbol="SIZ6")
        self.assertEqual(ident.multiplier, 5000)
        self.registry.check_identity_traps("SIZ6")

    def test_first_notice_not_available_typed(self):
        # DBN definitions carry NO first-notice field: asking must raise,
        # never return a fabricated date
        with self.assertRaises(PolicyError) as cm:
            resolve_first_notice("GCZ6")
        self.assertIn("NOT_AVAILABLE", str(cm.exception))


class TestContinuousGuard(FixtureBase):
    def test_continuous_series_detected_from_metadata(self):
        f = ingest_file(f"{self.tmp.name}/"
                        "ohlcv-1d.glbx-mdp3.continuous.synthetic.dbn")
        self.assertTrue(f.continuous)
        self.assertEqual(f.execution_use(), "EXECUTION_FORBIDDEN")

    def test_require_outright_raises_on_continuous(self):
        f = ingest_file(f"{self.tmp.name}/"
                        "ohlcv-1d.glbx-mdp3.continuous.synthetic.dbn")
        with self.assertRaises(PolicyError) as cm:
            require_outright(f, what="test fill path")
        self.assertIn("signal-feature-only", str(cm.exception))

    def test_require_outright_passes_on_outright_dbn(self):
        outright = [f for f in self.frames if not f.continuous]
        require_outright(*outright)               # must not raise

    def test_continuous_instrument_ids_not_in_outright_registry(self):
        f = ingest_file(f"{self.tmp.name}/"
                        "ohlcv-1d.glbx-mdp3.continuous.synthetic.dbn")
        for b in f.bars:
            with self.assertRaises(IngestError):
                self.registry.raw_for(b.instrument_id)

    def test_text_exports_have_unproven_stype(self):
        # CSV/JSONL carry no stype metadata: the frame cannot PROVE it is
        # outright (limitation, typed — see dbn/README.md)
        f = ingest_file(f"{self.tmp.name}/"
                        "ohlcv-1d.glbx-mdp3.raw_symbol.synthetic.csv")
        self.assertFalse(f.continuous)
        self.assertFalse(f.stype_proven)
        self.assertEqual(f.execution_use(), "unproven_stype")
        g = ingest_file(f"{self.tmp.name}/"
                        "ohlcv-1d.glbx-mdp3.raw_symbol.synthetic.dbn")
        self.assertTrue(g.stype_proven)
        self.assertEqual(g.execution_use(), "outright")


if __name__ == "__main__":
    unittest.main()
