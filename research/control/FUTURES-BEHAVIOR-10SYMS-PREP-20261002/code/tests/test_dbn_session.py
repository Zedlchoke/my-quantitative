"""Session-calendar tests: exchange-tz conversion, DST-correct boundaries
(spring forward 2026-03-08, fall back 2026-11-01), holiday short-session
inference, absence-aware NO_DATA, maintenance-break rejection, full-session
reconstruction. America/Chicago, zoneinfo-based (no manual offset tables)."""
from __future__ import annotations

import datetime as dt
import unittest

from futbt.dbn import spec as S
from futbt.dbn.fixtures import build_fixture_dir, session_bounds
from futbt.dbn.ingest import build_registry, ingest_file
from futbt.dbn.ohlcv import aggregate_1m_to_session
from futbt.dbn.session import (SessionKind, _session_bounds,
                               _spans_dst_change, build_session_map,
                               exchange_to_utc, session_date_of,
                               utc_to_exchange)
from futbt.taxonomy import PolicyError


class FixtureBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.tmp = tempfile.TemporaryDirectory(prefix="dbn_sess_")
        cls.universe = build_fixture_dir(cls.tmp.name)
        cls.frames = [ingest_file(f"{cls.tmp.name}/{n}")
                      for n in sorted(cls.universe.files)
                      if n.endswith(".dbn") and "continuous" not in n]
        cls.registry = build_registry(cls.frames)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def bars_1m(self, raw):
        return [b for f in self.frames for b in f.bars
                if b.rtype == S.RTYPE_OHLCV_1M
                and self.registry.raw_for(b.instrument_id) == raw]

    def bars_1d(self, raw):
        return [b for f in self.frames for b in f.bars
                if b.rtype == S.RTYPE_OHLCV_1D
                and self.registry.raw_for(b.instrument_id) == raw]


class TestTzConversion(unittest.TestCase):
    def test_utc_to_exchange_dst_correct(self):
        # spring forward 2026-03-08 02:00 CT (America/Chicago)
        before = utc_to_exchange(int(dt.datetime(
            2026, 3, 7, 12, 0, tzinfo=dt.timezone.utc).timestamp()) * 10**9)
        after = utc_to_exchange(int(dt.datetime(
            2026, 3, 8, 12, 0, tzinfo=dt.timezone.utc).timestamp()) * 10**9)
        self.assertEqual(before.utcoffset().total_seconds(), -6 * 3600)  # CST
        self.assertEqual(after.utcoffset().total_seconds(), -5 * 3600)  # CDT
        # fall back 2026-11-01 02:00 CT
        before = utc_to_exchange(int(dt.datetime(
            2026, 10, 31, 12, 0, tzinfo=dt.timezone.utc).timestamp()) * 10**9)
        after = utc_to_exchange(int(dt.datetime(
            2026, 11, 1, 12, 0, tzinfo=dt.timezone.utc).timestamp()) * 10**9)
        self.assertEqual(before.utcoffset().total_seconds(), -5 * 3600)
        self.assertEqual(after.utcoffset().total_seconds(), -6 * 3600)

    def test_exchange_to_utc_roundtrip(self):
        wall = dt.datetime(2026, 11, 2, 17, 0,
                           tzinfo=utc_to_exchange(0).tzinfo)
        ns = exchange_to_utc(wall)
        self.assertEqual(utc_to_exchange(ns).replace(tzinfo=None),
                         wall.replace(tzinfo=None))


class TestSessionDates(unittest.TestCase):
    def test_session_date_of_rolls_at_1700_ct(self):
        # 2026-03-05 16:30 CT belongs to the Mar-5 session;
        # 2026-03-05 17:00 CT belongs to the Mar-6 session.
        d = dt.date(2026, 3, 5)
        before = exchange_to_utc(dt.datetime(2026, 3, 5, 16, 30,
                                             tzinfo=utc_to_exchange(0).tzinfo))
        at_open = exchange_to_utc(dt.datetime(2026, 3, 5, 17, 0,
                                              tzinfo=utc_to_exchange(0).tzinfo))
        self.assertEqual(session_date_of(before), d)
        self.assertEqual(session_date_of(at_open), dt.date(2026, 3, 6))

    def test_session_date_of_weekend_rolls_to_monday(self):
        # Friday 17:00 CT opens Monday's session (no Sat/Sun sessions)
        friday_open = exchange_to_utc(dt.datetime(
            2026, 3, 6, 17, 0, tzinfo=utc_to_exchange(0).tzinfo))
        self.assertEqual(session_date_of(friday_open), dt.date(2026, 3, 9))

    def test_utc_midnight_maps_to_same_utc_date(self):
        # ohlcv-1d bars stamp ts_event at UTC-midnight interval START; on
        # weekdays the exchange session date of that stamp equals the UTC
        # date (weekend dates roll to Monday, tested separately).
        for d in (dt.date(2026, 3, 13), dt.date(2026, 11, 2),
                  dt.date(2026, 7, 1)):
            ns = int(dt.datetime(d.year, d.month, d.day,
                                 tzinfo=dt.timezone.utc).timestamp()) * 10**9
            self.assertEqual(session_date_of(ns), d)


class TestDstBoundaries(FixtureBase):
    def test_utc_open_times_shift_across_fall_back(self):
        # session open 17:00 CT: 22:00Z before fall-back, 23:00Z after
        open_oct30, _ = _session_bounds(dt.date(2026, 10, 30))
        open_nov02, _ = _session_bounds(dt.date(2026, 11, 2))
        hour_oct = utc_to_exchange(open_oct30).astimezone(
            dt.timezone.utc).hour
        hour_nov = utc_to_exchange(open_nov02).astimezone(
            dt.timezone.utc).hour
        self.assertEqual(hour_oct, 22)
        self.assertEqual(hour_nov, 23)
        # Oct-30 open -> Nov-2 open: 3 calendar days + the extra DST hour
        self.assertEqual(open_nov02 - open_oct30, 73 * 3_600_000_000_000)

    def test_session_window_length_constant_in_exchange_time(self):
        # DST never changes the exchange-local session length; only its
        # UTC span (23h vs 25h across transitions inside a window).
        for d in (dt.date(2026, 3, 9), dt.date(2026, 11, 2),
                  dt.date(2026, 6, 15)):
            o, c = _session_bounds(d)
            span_ct = (utc_to_exchange(c) - utc_to_exchange(o))
            self.assertEqual(span_ct, dt.timedelta(hours=23))

    def test_spans_dst_change_helper(self):
        # a synthetic window crossing 2026-03-08 02:00 CT
        o = exchange_to_utc(dt.datetime(2026, 3, 7, 18, 0,
                                        tzinfo=utc_to_exchange(0).tzinfo))
        c = exchange_to_utc(dt.datetime(2026, 3, 8, 6, 0,
                                        tzinfo=utc_to_exchange(0).tzinfo))
        self.assertTrue(_spans_dst_change(o, c))
        # a window entirely inside CDT
        o2 = exchange_to_utc(dt.datetime(2026, 6, 1, 18, 0,
                                         tzinfo=utc_to_exchange(0).tzinfo))
        c2 = exchange_to_utc(dt.datetime(2026, 6, 2, 10, 0,
                                         tzinfo=utc_to_exchange(0).tzinfo))
        self.assertFalse(_spans_dst_change(o2, c2))

    def test_roll_window_sessions_span_fall_back_weekend(self):
        # CLZ6 daily bars cover 2026-10-26..2026-11-06 across fall-back;
        # all sessions classify presence-only (daily cadence) and no
        # Sat/Sun session exists.
        smap = build_session_map("CLZ6", self.bars_1d("CLZ6"), self.registry)
        rec = smap.reconstruction()
        dates = [dt.date.fromisoformat(r["date"]) for r in rec]
        self.assertIn(dt.date(2026, 11, 2), dates)
        self.assertIn(dt.date(2026, 10, 30), dates)
        for d in dates:
            self.assertLess(d.weekday(), 5)
        self.assertNotIn(dt.date(2026, 10, 31), dates)   # Saturday
        self.assertNotIn(dt.date(2026, 11, 1), dates)    # Sunday


class TestHolidayShortSession(FixtureBase):
    def test_declared_early_close_detected_as_holiday_short(self):
        # fixture: 2026-04-03 early close 12:00 CT; NQ 1m bars stop 11:59
        smap = build_session_map("NQZ6", self.bars_1m("NQZ6"), self.registry)
        w = smap.window(dt.date(2026, 4, 3))
        self.assertEqual(w.kind, SessionKind.HOLIDAY_SHORT)
        self.assertTrue(w.inferred_short)      # inference, not exchange fact
        self.assertLess(w.coverage_ratio, 0.85)

    def test_full_session_not_flagged_short(self):
        smap = build_session_map("NQZ6", self.bars_1m("NQZ6"), self.registry)
        w = smap.window(dt.date(2026, 4, 2))
        self.assertEqual(w.kind, SessionKind.NORMAL)
        self.assertFalse(w.inferred_short)
        self.assertGreaterEqual(w.coverage_ratio, 0.85)

    def test_fixture_session_bounds_match_map(self):
        # The map's windows use STANDARD Globex bounds (17:00 open /
        # 16:00 close) — the early close itself is INFERRED (coverage +
        # inferred_short), never asserted, because no exchange holiday
        # calendar exists offline. The fixture truth carries the real
        # early close for comparison.
        truth = self.universe.minute_sessions["NQZ6"]
        for t in truth:
            d = dt.date.fromisoformat(t.date)
            w = build_session_map("NQZ6", self.bars_1m("NQZ6"),
                                  self.registry).window(d)
            self.assertEqual(w.open_utc_ns, t.open_utc_ns, t.date)
            if t.kind == "HOLIDAY_SHORT":
                self.assertLess(t.close_utc_ns, w.close_utc_ns)
            else:
                self.assertEqual(w.close_utc_ns, t.close_utc_ns, t.date)


class TestNoDataAndReconstruction(FixtureBase):
    def test_absent_sessions_are_no_data(self):
        # GCZ6 has settlement-only sessions 2026-03-16/17 (no daily bar)
        smap = build_session_map("GCZ6", self.bars_1d("GCZ6"), self.registry)
        for d in (dt.date(2026, 3, 16), dt.date(2026, 3, 17)):
            w = smap.window(d)
            self.assertEqual(w.kind, SessionKind.NO_DATA)
            self.assertEqual(w.n_bars, 0)

    def test_daily_cadence_presence_only(self):
        # daily bars must NOT go through minute-coverage logic (the
        # predecessor version mislabeled every daily session HOLIDAY_SHORT)
        smap = build_session_map("ESZ6", self.bars_1d("ESZ6"), self.registry)
        for w in smap.sessions.values():
            self.assertEqual(w.kind, SessionKind.NORMAL)
            self.assertIsNone(w.coverage_ratio)
            self.assertFalse(w.inferred_short)

    def test_mixed_cadence_refused(self):
        with self.assertRaises(PolicyError):
            build_session_map("ESZ6", self.bars_1d("ESZ6")
                              + self.bars_1m("ESZ6"), self.registry)

    def test_reconstruction_is_sorted_and_complete(self):
        smap = build_session_map("NQZ6", self.bars_1m("NQZ6"), self.registry)
        rec = smap.reconstruction()
        self.assertEqual([r["date"] for r in rec],
                         ["2026-04-02", "2026-04-03"])
        for r in rec:
            self.assertIn("open_utc_ns", r)
            self.assertIn("close_utc_ns", r)
            self.assertLess(r["open_utc_ns"], r["close_utc_ns"])

    def test_window_contains(self):
        smap = build_session_map("NQZ6", self.bars_1m("NQZ6"), self.registry)
        w = smap.window(dt.date(2026, 4, 2))
        self.assertTrue(w.contains(w.open_utc_ns))
        self.assertFalse(w.contains(w.close_utc_ns))   # half-open [o, c)


class TestAggregationBoundaries(FixtureBase):
    def test_maintenance_break_bar_rejected(self):
        # a 1m bar at 16:30 CT sits in the 16:00-17:00 break: no session
        from futbt.dbn.ingest import Bar
        bad_ts = exchange_to_utc(dt.datetime(2026, 4, 2, 16, 30,
                                             tzinfo=utc_to_exchange(0).tzinfo))
        bar = Bar(ts_event=bad_ts, instrument_id=1, open=1, high=1, low=1,
                  close=1, volume=1, rtype=S.RTYPE_OHLCV_1M)
        with self.assertRaises(PolicyError):
            aggregate_1m_to_session([bar], "NQZ6")

    def test_aggregate_explicit_session_boundaries(self):
        bars = self.bars_1m("NQZ6")
        out = aggregate_1m_to_session(bars, "NQZ6")
        self.assertEqual([s.session_date for s in out],
                         ["2026-04-02", "2026-04-03"])
        for s in out:
            self.assertGreater(s.n_bars, 0)
            self.assertLessEqual(s.first_ts, s.last_ts)
            self.assertEqual(s.volume, sum(b.volume for b in bars
                                           if s.first_ts <= b.ts_event
                                           <= s.last_ts))


if __name__ == "__main__":
    unittest.main()
