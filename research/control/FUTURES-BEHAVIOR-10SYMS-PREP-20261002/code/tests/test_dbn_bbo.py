"""BID/ASK synchronization tests: book-time joins with the simultaneity
taxonomy (EXACT/BOOK_TIME/STALE/NO_QUOTE), crossed/locked detection,
executable-quote enforcement, bar-side proxies are BAR_PROXY forever."""
from __future__ import annotations

import unittest

from futbt.dbn import spec as S
from futbt.dbn.bbo import (BboState, Simultaneity, bar_spread_proxy,
                           classify_bbo, crossed_quote_stats, join_book_time,
                           require_executable)
from futbt.dbn.fixtures import build_fixture_dir
from futbt.dbn.ingest import Quote, Trade, build_registry, ingest_file
from futbt.taxonomy import PolicyError

SEC = 1_000_000_000


class FixtureBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.tmp = tempfile.TemporaryDirectory(prefix="dbn_bbo_")
        cls.universe = build_fixture_dir(cls.tmp.name)
        cls.frames = [ingest_file(f"{cls.tmp.name}/{n}")
                      for n in sorted(cls.universe.files)
                      if n.endswith(".dbn") and "continuous" not in n]
        cls.registry = build_registry(cls.frames)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def trades_and_quotes(self):
        """The DESIGNED join scenario: trades-schema trades against the
        mbp-1 book (the fixture truth timeline). Other frames (tbbo /
        bbo-1m duplicates of the same moments) are tested separately."""
        trades = [t for f in self.frames
                  if f.source.endswith("trades.glbx-mdp3.raw_symbol.synthetic.dbn")
                  for t in f.trades]
        quotes = [q for f in self.frames
                  if f.source.endswith("mbp-1.glbx-mdp3.raw_symbol.synthetic.dbn")
                  for q in f.quotes]
        return trades, quotes

    def bbo_states_by_kind(self) -> dict:
        return {state: ts for ts, state in self.universe.bbo_states}


class TestClassifyBbo(unittest.TestCase):
    def test_states(self):
        self.assertIs(classify_bbo(100, 101), BboState.NORMAL)
        self.assertIs(classify_bbo(100, 100), BboState.LOCKED)
        self.assertIs(classify_bbo(101, 100), BboState.CROSSED)
        self.assertIs(classify_bbo(None, 100), BboState.UNDEFINED)
        self.assertIs(classify_bbo(S.UNDEF_PRICE, 100), BboState.UNDEFINED)


class TestBookTimeJoin(FixtureBase):
    def test_join_taxonomy_matches_fixture_truth(self):
        trades, quotes = self.trades_and_quotes()
        joined = join_book_time(trades, quotes)
        self.assertEqual(len(joined), len(self.universe.trade_join_truth))
        truth = dict(self.universe.trade_join_truth)
        for j in joined:
            self.assertEqual(j.simultaneity,
                             Simultaneity(truth[j.trade.ts_recv]),
                             j.trade.ts_recv)
        kinds = {j.simultaneity for j in joined}
        self.assertEqual(kinds, {Simultaneity.EXACT,
                                 Simultaneity.BOOK_TIME,
                                 Simultaneity.STALE,
                                 Simultaneity.NO_QUOTE})

    def test_exact_join_zero_lead(self):
        trades, quotes = self.trades_and_quotes()
        joined = join_book_time(trades, quotes)
        exact = [j for j in joined if j.simultaneity == Simultaneity.EXACT]
        self.assertEqual(len(exact), 1)
        self.assertEqual(exact[0].quote_lead_ns, 0)
        self.assertGreaterEqual(exact[0].spread_nanos(), 0)

    def test_stale_beyond_threshold(self):
        # trades 2.9s and 2s after their last quote with 1s staleness
        trades, quotes = self.trades_and_quotes()
        joined = join_book_time(trades, quotes)
        stale = [j for j in joined if j.simultaneity == Simultaneity.STALE]
        self.assertEqual(len(stale), 2)
        for j in stale:
            self.assertGreater(j.quote_lead_ns, SEC)

    def test_book_time_within_threshold(self):
        trades, quotes = self.trades_and_quotes()
        joined = join_book_time(trades, quotes)
        bt = [j for j in joined if j.simultaneity == Simultaneity.BOOK_TIME]
        self.assertEqual(len(bt), 1)
        self.assertLessEqual(bt[0].quote_lead_ns, SEC)

    def test_no_quote_before_first_trade(self):
        trades, quotes = self.trades_and_quotes()
        joined = join_book_time(trades, quotes)
        nq = [j for j in joined if j.simultaneity == Simultaneity.NO_QUOTE]
        self.assertEqual(len(nq), 1)
        self.assertIsNone(nq[0].bid_px)
        self.assertIsNone(nq[0].spread_nanos())

    def test_mbp1_bbo_is_pretrade_book(self):
        # TBBO/mbp-1 docs: the BBO on a trade record is the book
        # immediately BEFORE the trade's effect — the join must not use
        # quotes AT/after the trade time
        trades, quotes = self.trades_and_quotes()
        joined = join_book_time(trades, quotes)
        for j in joined:
            if j.quote_ts is not None:
                self.assertLessEqual(j.quote_ts, j.trade.ts_recv)


class TestCrossedBook(FixtureBase):
    def test_crossed_and_locked_moments_present(self):
        trades, quotes = self.trades_and_quotes()
        stats = crossed_quote_stats(quotes)
        self.assertGreater(stats["CROSSED"], 0)
        self.assertGreater(stats["LOCKED"], 0)
        self.assertGreater(stats["crossed_locked_fraction"], 0.0)
        self.assertIn("CROSSED", stats["first_example_ts"])

    def test_crossed_bbo_never_executable(self):
        # craft a trade at the fixture's CROSSED book moment to prove the guard
        crossed_ts = self.bbo_states_by_kind()["CROSSED"]
        t = Trade(ts_event=crossed_ts, ts_recv=crossed_ts, instrument_id=1,
                  price=1, size=1, action="T", side="B", flags=0, sequence=99)
        _, quotes = self.trades_and_quotes()
        j = join_book_time([t], quotes)[0]
        self.assertIs(classify_bbo(j.bid_px, j.ask_px), BboState.CROSSED)
        with self.assertRaises(PolicyError):
            require_executable(j)

    def test_locked_bbo_not_executable(self):
        locked_ts = self.bbo_states_by_kind()["LOCKED"]
        t = Trade(ts_event=locked_ts, ts_recv=locked_ts, instrument_id=1,
                  price=1, size=1, action="T", side="B", flags=0, sequence=98)
        _, quotes = self.trades_and_quotes()
        j = join_book_time([t], quotes)[0]
        self.assertIs(classify_bbo(j.bid_px, j.ask_px), BboState.LOCKED)
        with self.assertRaises(PolicyError):
            require_executable(j)

    def test_stale_quote_not_executable(self):
        trades, quotes = self.trades_and_quotes()
        joined = join_book_time(trades, quotes)
        stale = [j for j in joined if j.simultaneity == Simultaneity.STALE][0]
        with self.assertRaises(PolicyError):
            require_executable(stale)

    def test_normal_book_time_join_executable(self):
        trades, quotes = self.trades_and_quotes()
        joined = join_book_time(trades, quotes)
        ok = [j for j in joined
              if j.simultaneity == Simultaneity.EXACT
              and classify_bbo(j.bid_px, j.ask_px) is BboState.NORMAL]
        self.assertGreater(len(ok), 0)
        for j in ok:
            require_executable(j)               # must not raise


class TestBarSpreadProxy(FixtureBase):
    def test_bar_proxy_always_bar_proxy(self):
        # a bar close is an interval aggregate, never a quote: the proxy
        # can never claim simultaneity regardless of data density —
        # EXACT/BOOK_TIME are reserved for real book-time joins
        from futbt.dbn.ingest import Bar
        bars = [b for f in self.frames for b in f.bars
                if b.rtype == S.RTYPE_OHLCV_1M][:20]
        _, quotes = self.trades_and_quotes()
        proxies = bar_spread_proxy(bars, quotes)
        self.assertEqual(len(proxies), len(bars))
        for p in proxies:
            self.assertEqual(p.simultaneity, Simultaneity.BAR_PROXY)
            self.assertNotIn(p.simultaneity,
                             (Simultaneity.EXACT, Simultaneity.BOOK_TIME))

    def test_bar_proxy_without_quotes_undefined(self):
        from futbt.dbn.ingest import Bar
        bars = [Bar(ts_event=1, instrument_id=1, open=1, high=2, low=0,
                    close=1, volume=1, rtype=S.RTYPE_OHLCV_1M)]
        proxies = bar_spread_proxy(bars, [])
        self.assertIs(proxies[0].bbo_state, BboState.UNDEFINED)
        self.assertIsNone(proxies[0].spread_nanos())


class TestQuoteFrames(FixtureBase):
    def test_mbp1_quotes_and_bbo1m_quotes_both_ingested(self):
        quotes = [q for f in self.frames for q in f.quotes]
        # 6 mbp-1 + 3 tbbo(dbn, same rtype) + 3 bbo-1m rows
        self.assertGreaterEqual(len(quotes), 12)

    def test_bbo_1m_records_have_no_action_semantics(self):
        f = [x for x in self.frames
             if x.source.endswith("bbo-1m.glbx-mdp3.raw_symbol.synthetic.dbn")][0]
        self.assertEqual(len(f.quotes), 3)
        for q in f.quotes:
            self.assertEqual(q.action, "N")


if __name__ == "__main__":
    unittest.main()
