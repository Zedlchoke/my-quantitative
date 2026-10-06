"""QA-layer + PIT + roll-window tests: SHA256 manifest, duplicate/gap/
monotonic checks, coverage report (negative bars, stale bars, close-only
sessions), roll-critical two-contract window with volume/OI migration
spanning the fall-back DST change, PIT publication gating and settlement
vintages, feature-only roll adjustment, unknown-record-type fail-closed."""
from __future__ import annotations

import datetime as dt
import unittest

from futbt.dbn import pit, qa, spec as S
from futbt.dbn.fixtures import build_fixture_dir
from futbt.dbn.ingest import Bar, build_registry, ingest_file
from futbt.dbn.ohlcv import settlement_series
from futbt.taxonomy import PolicyError

NS = 1_000_000_000
MINUTE = 60 * NS


class FixtureBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.tmp = tempfile.TemporaryDirectory(prefix="dbn_qa_")
        cls.universe = build_fixture_dir(cls.tmp.name)
        cls.frames = [ingest_file(f"{cls.tmp.name}/{n}")
                      for n in sorted(cls.universe.files)
                      if n.endswith(".dbn") and "continuous" not in n]
        cls.registry = build_registry(cls.frames)
        cls.stats = [s for f in cls.frames for s in f.statistics]
        cls.report = qa.qa_report(cls.frames, cls.registry)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()


class TestShaManifest(FixtureBase):
    def test_sha256_manifest_keys_are_resolved_paths(self):
        import tempfile, os
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.bin"
            p.write_bytes(b"hello")
            m = qa.sha256_manifest([str(p)])
            self.assertEqual(len(m), 1)
            key = next(iter(m))
            self.assertEqual(os.path.basename(key), "x.bin")
            self.assertEqual(m[key],
                             "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c"
                             "1fa7425e73043362938b9824")

    def test_report_manifest_covers_every_source_file(self):
        rep = self.report
        sources = {f.source for f in self.frames}
        self.assertEqual(set(rep["manifest"].keys()),
                         {str(__import__("pathlib").Path(s).resolve())
                          for s in sources})
        for digest in rep["manifest"].values():
            self.assertRegex(digest, r"^[0-9a-f]{64}$")


class TestTimeSeriesChecks(FixtureBase):
    def _es_1m(self):
        return [b for f in self.frames for b in f.bars
                if b.rtype == S.RTYPE_OHLCV_1M
                and self.registry.raw_for(b.instrument_id) == "ESZ6"]

    def test_duplicate_ts_detected(self):
        chk = qa.check_bars_time_series(self._es_1m(), "ESZ6")
        self.assertEqual(chk.n_duplicate_ts, 1)
        self.assertEqual(chk.duplicate_ts,
                         self.universe.duplicate_bars["ESZ6"])
        self.assertGreater(chk.n_records, len(set(b.ts_event
                                                  for b in self._es_1m())) - 1)

    def test_no_trade_gap_reported_as_inference(self):
        # fixture removed the 9:31 CT bar on 2026-03-06 (sparse ohlcv:
        # no trade -> no bar); QA reports the missing minute, does not error
        chk = qa.check_bars_time_series(self._es_1m(), "ESZ6",
                                        max_gap_report=10_000)
        self.assertIn(self.universe.minute_gaps["ESZ6"][0],
                      chk.no_trade_gap_ts)
        self.assertGreater(chk.n_no_trade_gaps, 0)
        self.assertTrue(chk.ok())

    def test_non_monotonic_detected_in_received_order(self):
        # predecessor bug: the check ran on a sorted copy (always 0).
        bars = sorted(self._es_1m(), key=lambda b: b.ts_event)
        shuffled = list(reversed(bars[:5])) + bars[5:]
        chk = qa.check_bars_time_series(shuffled, "ESZ6")
        self.assertGreater(chk.n_non_monotonic, 0)
        self.assertFalse(chk.ok())

    def test_sorted_input_is_monotonic(self):
        bars = sorted(self._es_1m(), key=lambda b: b.ts_event)
        self.assertEqual(qa.check_bars_time_series(bars, "ESZ6").n_non_monotonic, 0)

    def test_daily_bars_do_not_get_minute_gap_scan(self):
        daily = [b for f in self.frames for b in f.bars
                 if b.rtype == S.RTYPE_OHLCV_1D
                 and self.registry.raw_for(b.instrument_id) == "ESZ6"]
        chk = qa.check_bars_time_series(daily, "ESZ6")
        self.assertEqual(chk.n_no_trade_gaps, 0)   # cadence-aware

    def test_report_time_series_is_per_file(self):
        keys = self.report["time_series"].keys()
        self.assertTrue(any("ohlcv-1m" in k for k in keys))
        for chk in self.report["time_series"].values():
            self.assertEqual(chk["n_non_monotonic"], 0)


class TestCoverageReport(FixtureBase):
    def test_negative_price_bar_counted(self):
        cl = self.report["coverage"]["CLZ6"]
        self.assertEqual(cl["n_negative_price_bars"], 1)

    def test_close_only_sessions_counted(self):
        self.assertEqual(self.report["coverage"]["GCZ6"]["n_close_only_sessions"], 2)
        self.assertEqual(self.report["coverage"]["6BZ6"]["n_close_only_sessions"], 1)
        self.assertIn("GCZ6", self.report["failures"])
        self.assertIn("6BZ6", self.report["failures"])

    def test_stale_flat_bar_counted(self):
        self.assertEqual(self.report["coverage"]["6JZ6"]["n_stale_flat_bars"], 1)

    def test_coverage_sessions_typed(self):
        for raw, cov in self.report["coverage"].items():
            for s in cov["sessions"]:
                self.assertIn(s["kind"],
                              ("NORMAL", "DST_SHIFTED", "HOLIDAY_SHORT",
                               "NO_DATA", "OUT_OF_LISTING"))
                self.assertIsInstance(s["n_bars"], int)

    def test_absent_sessions_appear_as_no_data(self):
        gc = {s["date"]: s for s in self.report["coverage"]["GCZ6"]["sessions"]}
        self.assertEqual(gc["2026-03-16"]["kind"], "NO_DATA")
        self.assertEqual(gc["2026-03-17"]["kind"], "NO_DATA")


class TestRollWindow(FixtureBase):
    def test_volume_crossover_matches_truth(self):
        self.assertEqual(self.report["roll_window"]["volume_pair"],
                         ["CLZ6", "CLF7"])
        self.assertEqual(self.report["roll_window"]["volume_crossover"],
                         self.universe.volume_roll["crossover"])
        self.assertEqual(self.report["roll_window"]["volume_crossover"],
                         "2026-11-02")

    def test_oi_crossover_lags_volume_crossover(self):
        rw = self.report["roll_window"]
        self.assertEqual(rw["open_interest_pair"], ["CLZ6", "CLF7"])
        self.assertEqual(rw["open_interest_crossover"],
                         self.universe.oi_roll["crossover"])
        vol = dt.date.fromisoformat(rw["volume_crossover"])
        oi = dt.date.fromisoformat(rw["open_interest_crossover"])
        self.assertLess(vol, oi)

    def test_roll_window_spans_fall_back_dst(self):
        vol = dt.date.fromisoformat(
            self.report["roll_window"]["volume_crossover"])
        oi = dt.date.fromisoformat(
            self.report["roll_window"]["open_interest_crossover"])
        # the roll-critical window (2026-10-26..2026-11-06) straddles the
        # 2026-11-01 America/Chicago fall-back; both crossovers land AFTER
        # the transition, the window start precedes it
        self.assertGreater(vol, dt.date(2026, 11, 1))
        self.assertGreater(oi, dt.date(2026, 11, 1))
        self.assertLess(vol, oi)
        bars = [b for f in self.frames for b in f.bars
                if b.rtype == S.RTYPE_OHLCV_1D
                and self.registry.raw_for(b.instrument_id) == "CLZ6"]
        first = min(dt.datetime.fromtimestamp(b.ts_event / 1e9,
                                              tz=dt.timezone.utc).date()
                    for b in bars)
        self.assertLess(first, dt.date(2026, 11, 1))

    def test_both_contracts_have_bars_through_window(self):
        for raw in ("CLZ6", "CLF7"):
            bars = [b for f in self.frames for b in f.bars
                    if b.rtype == S.RTYPE_OHLCV_1D
                    and self.registry.raw_for(b.instrument_id) == raw]
            dates = {dt.datetime.fromtimestamp(b.ts_event / 1e9,
                                               tz=dt.timezone.utc).date()
                     for b in bars}
            self.assertIn(dt.date(2026, 11, 2), dates, raw)
            self.assertIn(dt.date(2026, 11, 5), dates, raw)

    def test_volume_migration_shape(self):
        # old-contract volume decays, new-contract volume grows across the
        # window (adjacent-contract roll-critical window)
        d1, d2 = "2026-10-26", "2026-11-06"
        self.assertGreater(self.universe.volume_roll[d1]["old"],
                           self.universe.volume_roll[d1]["new"])
        self.assertLess(self.universe.volume_roll[d2]["old"],
                        self.universe.volume_roll[d2]["new"])


class TestPitVintage(FixtureBase):
    def test_settlement_publication_gated(self):
        ss = settlement_series(self.stats, self.registry, "CLZ6")
        neg = [s for s in ss if s.session_date == "2026-03-13"]
        prelim, final = neg
        # before the preliminary publication: nothing visible for that day
        v = pit.settlement_vintage(ss, prelim.published_ts - 1)
        self.assertNotIn("2026-03-13", v)
        # after prelim, before final: preliminary visible
        v = pit.settlement_vintage(ss, final.published_ts - 1)
        self.assertEqual(v["2026-03-13"].visible_price, prelim.price)
        self.assertFalse(v["2026-03-13"].final)
        # after final: final visible, supersedes prelim
        v = pit.settlement_vintage(ss, final.published_ts)
        self.assertEqual(v["2026-03-13"].visible_price, final.price)
        self.assertTrue(v["2026-03-13"].final)

    def test_cleared_volume_publishes_next_morning(self):
        # fixture: cleared volume for trading date D publishes at 08:00 CT
        # the NEXT weekday; PIT view at D 23:59 must NOT see it
        from futbt.dbn.session import exchange_to_utc, utc_to_exchange
        day = dt.date(2026, 11, 2)
        day_end = exchange_to_utc(dt.datetime(2026, 11, 2, 23, 59,
                                              tzinfo=utc_to_exchange(0).tzinfo))
        visible = pit.asof_statistics(self.stats, day_end)
        vols = [s for s in visible
                if s.stat_type == S.STAT_TYPE_CLEARED_VOLUME
                and dt.datetime.fromtimestamp(s.ts_ref / NS,
                                              tz=dt.timezone.utc).date() == day]
        self.assertEqual(vols, [])
        next_morning = exchange_to_utc(dt.datetime(
            2026, 11, 3, 8, 0, tzinfo=utc_to_exchange(0).tzinfo))
        visible = pit.asof_statistics(self.stats, next_morning)
        vols = [s for s in visible
                if s.stat_type == S.STAT_TYPE_CLEARED_VOLUME
                and dt.datetime.fromtimestamp(s.ts_ref / NS,
                                              tz=dt.timezone.utc).date() == day]
        self.assertGreater(len(vols), 0)

    def test_time_traveling_statistic_refused(self):
        # a statistic referencing trading date X cannot publish before X
        ref = int(dt.datetime(2026, 11, 2, tzinfo=dt.timezone.utc).timestamp()) * NS
        pub = int(dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc).timestamp()) * NS
        with self.assertRaises(pit.PitViolation):
            pit.require_asof_order(pub, ref, "cleared_volume")

    def test_identity_asof_respects_delete(self):
        defs = [d for f in self.frames for d in f.definitions]
        clv6 = self.universe.contracts["CLV6"]
        before = pit.asof_identity(defs, "CLV6", clv6.expiration_ns - 1)
        self.assertIsNotNone(before)
        after = pit.asof_identity(defs, "CLV6", clv6.expiration_ns + 1)
        self.assertIsNone(after)                     # deleted


class TestFeatureOnlyRollAdjustment(FixtureBase):
    def _closes(self):
        rows = []
        for raw in ("CLZ6", "CLF7"):
            bars = sorted([b for f in self.frames for b in f.bars
                           if b.rtype == S.RTYPE_OHLCV_1D
                           and self.registry.raw_for(b.instrument_id) == raw],
                          key=lambda b: b.ts_event)
            rows.append((raw, bars))
        return rows

    def test_factor_requires_declarer(self):
        with self.assertRaises(PolicyError):
            pit.compute_roll_factor(100, 90, raw_symbol_old="CLZ6",
                                    raw_symbol_new="CLF7",
                                    roll_session="2026-11-02")

    def test_additive_factor_and_splice(self):
        (old, old_bars), (new, new_bars) = self._closes()
        old_close = [b for b in old_bars if _utc_date(b.ts_event)
                     == "2026-10-30"][0].close
        new_close = [b for b in new_bars if _utc_date(b.ts_event)
                     == "2026-10-30"][0].close
        f = pit.compute_roll_factor(old_close, new_close, raw_symbol_old=old,
                                    raw_symbol_new=new,
                                    roll_session="2026-11-02",
                                    declared_by="synthetic test")
        self.assertEqual(f.additive_nanos, old_close - new_close)
        self.assertTrue(f.feature_only)
        spliced = pit.apply_feature_adjustment(old_bars + new_bars, [f])
        roll_start = pit._session_start_ns("2026-11-02")
        orig = {(b.ts_event, b.instrument_id): b.close
                for _, bars in self._closes() for b in bars}
        for b in spliced:
            base = orig[(b.ts_event, b.instrument_id)]
            if b.ts_event >= roll_start:
                self.assertEqual(b.close, base + f.additive_nanos)
            else:
                self.assertEqual(b.close, base)

    def test_ratio_refused_on_non_positive(self):
        with self.assertRaises(PolicyError):
            pit.compute_roll_factor(-100, 90, raw_symbol_old="CLZ6",
                                    raw_symbol_new="CLF7",
                                    roll_session="2026-11-02",
                                    method="ratio", declared_by="t")

    def test_execution_context_refused(self):
        f = pit.compute_roll_factor(100, 90, raw_symbol_old="A",
                                    raw_symbol_new="B",
                                    roll_session="2026-11-02",
                                    declared_by="t")
        with self.assertRaises(PolicyError):
            pit.apply_feature_adjustment([], [f], execution_context=True)


def _utc_date(ns: int) -> str:
    return dt.datetime.fromtimestamp(ns / NS,
                                     tz=dt.timezone.utc).date().isoformat()


class TestFailClosedSchema(FixtureBase):
    def test_unknown_rtype_in_dbn_stream_typed_error(self):
        # craft a stream with an mbo record (0xA0): typed error, no skip
        from futbt.dbn.wire import DbnMetadata, decode_dbn_bytes, encode_metadata
        rec = bytearray(S.pack_record(
            S.RTYPE_OHLCV_1M, 1, dict(open=1, high=1, low=1, close=1, volume=1)))
        rec[1] = 0xA0
        with self.assertRaises(S.UnknownRecordTypeError):
            decode_dbn_bytes(encode_metadata(DbnMetadata()) + bytes(rec))

    def test_unknown_stat_type_flagged_in_report(self):
        # unknown stat TYPES (values) are census-flagged, not crashes —
        # the record type itself is still valid
        self.assertEqual(self.report["unknown_stat_types"], [])

    def test_csv_unknown_rtype_fails_closed(self):
        from futbt.dbn.textio import TextSchemaError, parse_csv
        with self.assertRaises(TextSchemaError):
            parse_csv("a,b\n1,2\n", rtype=None)


if __name__ == "__main__":
    unittest.main()
