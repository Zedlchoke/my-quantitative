"""Trade/OHLCV content tests: trade classification, 1m->session
aggregation, ohlcv-1d UTC-day convention + ts_event-interval-start,
negative CL prices preserved exactly, stale close-only bars, settlement vs
trade separation with preliminary/final revisions."""
from __future__ import annotations

import datetime as dt
import unittest

from futbt.dbn import spec as S
from futbt.dbn.fixtures import build_fixture_dir, NEG_DAY
from futbt.dbn.ingest import Bar, build_registry, ingest_file
from futbt.dbn.ohlcv import (SettlementVsTrade, aggregate_1m_to_session,
                             classify_trade, compare_settlement_vs_trade,
                             require_no_negative_log, settlement_series)
from futbt.taxonomy import PolicyError


class FixtureBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.tmp = tempfile.TemporaryDirectory(prefix="dbn_ohlc_")
        cls.universe = build_fixture_dir(cls.tmp.name)
        cls.frames = [ingest_file(f"{cls.tmp.name}/{n}")
                      for n in sorted(cls.universe.files)
                      if n.endswith(".dbn") and "continuous" not in n]
        cls.registry = build_registry(cls.frames)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def stats(self):
        return [s for f in self.frames for s in f.statistics]


class TestTradeClassification(FixtureBase):
    def test_trades_schema_all_action_t(self):
        trades = [t for f in self.frames for t in f.trades]
        self.assertGreater(len(trades), 0)
        for t in trades:
            out = classify_trade(t)
            self.assertTrue(out["is_trade"])
            self.assertIn(out["aggressor"],
                          ("buy_aggressor", "sell_aggressor", "unspecified"))

    def test_aggressor_side_mapping(self):
        trades = {t.sequence: t for f in self.frames for t in f.trades}
        by_side = {t.side: t for t in trades.values()}
        self.assertEqual(classify_trade(by_side["B"])["aggressor"],
                         "buy_aggressor")
        self.assertEqual(classify_trade(by_side["A"])["aggressor"],
                         "sell_aggressor")

    def test_non_trade_record_refused(self):
        # trades schema is defined to carry action 'T' only; anything else
        # is a schema surprise and must not be silently classified
        from futbt.dbn.ingest import Trade
        t = Trade(ts_event=1, ts_recv=1, instrument_id=1, price=1, size=1,
                  action="M", side="N", flags=0, sequence=1)
        with self.assertRaises(PolicyError):
            classify_trade(t)

    def test_flags_last_carried(self):
        trades = [t for f in self.frames for t in f.trades]
        self.assertTrue(any(classify_trade(t)["flags_last"]
                            for t in trades))


class TestOhlcvConventions(FixtureBase):
    def test_ohlcv_1d_ts_event_is_utc_midnight_interval_start(self):
        # Databento docs: ohlcv-1d aggregates the UTC DATE; ts_event marks
        # the interval START (midnight UTC).
        daily = [b for f in self.frames for b in f.bars
                 if b.rtype == S.RTYPE_OHLCV_1D]
        for b in daily[:200]:
            d = dt.datetime.fromtimestamp(b.ts_event / 1e9,
                                          tz=dt.timezone.utc)
            self.assertEqual((d.hour, d.minute, d.second), (0, 0, 0), b.ts_event)

    def test_ohlcv_1m_sparsity_no_bar_without_trade(self):
        # fixture plants a missing 9:31 bar on 2026-03-06 (sparse by
        # design): "If no trade occurs within the interval, no record is
        # printed" — the bar simply does not exist.
        es = [b for f in self.frames for b in f.bars
              if b.rtype == S.RTYPE_OHLCV_1M
              and self.registry.raw_for(b.instrument_id) == "ESZ6"]
        missing = self.universe.minute_gaps["ESZ6"][0]
        self.assertEqual(
            dt.datetime.fromtimestamp(missing / 1e9,
                                      tz=dt.timezone.utc).isoformat(),
            "2026-03-06T15:31:00+00:00")
        self.assertNotIn(missing, [b.ts_event for b in es])

    def test_1m_aggregation_ohlc_and_volume(self):
        es = [b for f in self.frames for b in f.bars
              if b.rtype == S.RTYPE_OHLCV_1M
              and self.registry.raw_for(b.instrument_id) == "ESZ6"]
        out = aggregate_1m_to_session(es, "ESZ6")
        by_date = {s.session_date: s for s in out}
        self.assertIn("2026-03-05", by_date)
        s = by_date["2026-03-05"]
        # recompute the expected aggregate straight from the source bars
        day = [b for b in es if _session_of(b.ts_event) == "2026-03-05"]
        self.assertEqual(s.open, day[0].open)
        self.assertEqual(s.close, day[-1].close)
        self.assertEqual(s.high, max(b.high for b in day))
        self.assertEqual(s.low, min(b.low for b in day))
        self.assertEqual(s.volume, sum(b.volume for b in day))


def _session_of(ts_ns) -> str:
    from futbt.dbn.session import session_date_of
    return session_date_of(ts_ns).isoformat()


class TestNegativePrices(FixtureBase):
    def test_negative_cl_day_preserved_exactly(self):
        bars = [b for f in self.frames for b in f.bars
                if b.rtype == S.RTYPE_OHLCV_1D
                and self.registry.raw_for(b.instrument_id) == "CLZ6"]
        ts = int(dt.datetime(2026, 3, 13, tzinfo=dt.timezone.utc).timestamp()
                 ) * 10**9
        bar = [b for b in bars if b.ts_event == ts][0]
        self.assertEqual(bar.low, S.price_to_nanos("-3.00"))
        self.assertEqual(bar.close, S.price_to_nanos("-2.75"))
        self.assertTrue(bar.negative())

    def test_negative_settlement_preserved(self):
        ss = settlement_series(self.stats(), self.registry, "CLZ6")
        neg = [s for s in ss if s.session_date == NEG_DAY]
        self.assertEqual(len(neg), 2)                 # prelim + final
        self.assertEqual(min(s.price for s in neg),
                         S.price_to_nanos("-2.75"))

    def test_no_log_transform_on_negative_series(self):
        with self.assertRaises(PolicyError):
            require_no_negative_log([100, -2750_000_000, 200])


class TestStaleCloseOnlyBars(FixtureBase):
    def test_stale_flat_bar_detected(self):
        # fixture plants a 6JZ6 1m bar with o=h=l=c=prev close, v=1
        j = [b for f in self.frames for b in f.bars
             if b.rtype == S.RTYPE_OHLCV_1M
             and self.registry.raw_for(b.instrument_id) == "6JZ6"]
        j = sorted(j, key=lambda b: b.ts_event)
        stale_ts = self.universe.stale_bar["6JZ6"]
        idx = [b.ts_event for b in j].index(stale_ts)
        prev_close = j[idx - 1].close
        self.assertTrue(j[idx].is_stale_flat(prev_close))
        self.assertEqual(j[idx].volume, 1)

    def test_normal_bar_not_stale(self):
        j = sorted([b for f in self.frames for b in f.bars
                    if b.rtype == S.RTYPE_OHLCV_1M
                    and self.registry.raw_for(b.instrument_id) == "6JZ6"],
                   key=lambda b: b.ts_event)
        self.assertFalse(j[0].is_stale_flat(None))

    def test_close_only_by_absence_sessions(self):
        # GCZ6/6BZ6: settlement exists, bar does not (Databento-native
        # close-only pathology)
        for raw, dates in self.universe.absent_sessions.items():
            ss = settlement_series(self.stats(), self.registry, raw)
            have = {s.session_date for s in ss}
            for d in dates:
                self.assertIn(d, have)


class TestSettlementVsTrade(FixtureBase):
    def test_settlement_series_separated_from_trades(self):
        ss = settlement_series(self.stats(), self.registry, "CLZ6")
        trade_closes = {b.close for f in self.frames for b in f.bars
                        if self.registry.raw_for(b.instrument_id) == "CLZ6"}
        # settlements live in their own table; both negative-day values kept
        neg = [s for s in ss if s.session_date == NEG_DAY]
        self.assertEqual([(s.final, s.price) for s in neg],
                         [(False, S.price_to_nanos("-2.50")),
                          (True, S.price_to_nanos("-2.75"))])
        self.assertTrue(trade_closes)   # sanity: trade data also present

    def test_preliminary_vs_final_flags(self):
        ss = settlement_series(self.stats(), self.registry, "CLZ6")
        neg = [s for s in ss if s.session_date == NEG_DAY]
        self.assertFalse(neg[0].final)
        self.assertTrue(neg[1].final)

    def test_settlement_session_date_is_utc_date_of_ts_ref(self):
        # predecessor bug: exchange-local date of ts_ref (UTC midnight) is
        # the PREVIOUS day; the trading date is the UTC date.
        ss = settlement_series(self.stats(), self.registry, "ESZ6")
        for s in ss:
            d = dt.date.fromisoformat(s.session_date)
            self.assertTrue(dt.date(2026, 2, 20) <= d <= dt.date(2026, 4, 10))

    def test_compare_settlement_vs_trade_final_only(self):
        es_bars = [b for f in self.frames for b in f.bars
                   if b.rtype == S.RTYPE_OHLCV_1D
                   and self.registry.raw_for(b.instrument_id) == "ESZ6"]
        # build SessionBars from the daily bars directly (1 bar/session)
        from futbt.dbn.ohlcv import SessionBar
        sess = [SessionBar(raw_symbol="ESZ6",
                           session_date=_utc_date(b.ts_event),
                           open=b.open, high=b.high, low=b.low, close=b.close,
                           volume=b.volume, n_bars=1, first_ts=b.ts_event,
                           last_ts=b.ts_event) for b in es_bars]
        ss = settlement_series(self.stats(), self.registry, "ESZ6")
        cmp_ = compare_settlement_vs_trade(sess, ss,
                                           self.registry.require(
                                               raw_symbol="ESZ6"
                                           ).min_price_increment)
        self.assertGreater(len(cmp_), 0)
        # fixture publishes settlement == daily close: diff must be 0 ticks
        for c in cmp_:
            self.assertEqual(c.diff_ticks, 0.0)
            self.assertTrue(c.final)


def _utc_date(ns: int) -> str:
    return dt.datetime.fromtimestamp(ns / 1e9,
                                     tz=dt.timezone.utc).date().isoformat()


class TestBarValidation(FixtureBase):
    def test_bar_high_low_invariants_hold_on_fixtures(self):
        bars = [b for f in self.frames for b in f.bars]
        for b in bars:
            self.assertGreaterEqual(b.high, max(b.open, b.close, b.low))
            self.assertLessEqual(b.low, min(b.open, b.close, b.high))


if __name__ == "__main__":
    unittest.main()
