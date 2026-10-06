"""Raw adapter tests against the synthetic fixture (real IBKR JSON schema)."""
import datetime as dt
import unittest

from futbt.rawdata import (RawFileName, RawFileError, contracts_by_symbol,
                           load_raw_file, split_local_symbol)
from futbt.synth import FIXTURE_FETCHED_UTC

from .helpers import FixtureTestCase


class TestFilenameParsing(unittest.TestCase):
    def test_canonical_daily(self):
        n = RawFileName.parse("CL_CLX6_304037511_TRADES_1day_6Y.json")
        self.assertEqual((n.symbol, n.local_symbol, n.conid), ("CL", "CLX6", 304037511))
        self.assertEqual((n.what, n.bar_size, n.span), ("TRADES", "1 day", "6Y"))

    def test_ng_two_digit_year(self):
        n = RawFileName.parse("NG_NGX26_269460170_TRADES_1day_6Y.json")
        self.assertEqual(n.local_symbol, "NGX26")

    def test_front_marker(self):
        n = RawFileName.parse("CL_CLX6_304037511_front_TRADES_1min_1800S.json")
        self.assertTrue(n.is_front_marker)
        self.assertEqual((n.what, n.bar_size, n.span), ("TRADES", "1 min", "1800S"))

    def test_next_and_nearest_expired_markers(self):
        n = RawFileName.parse("6A_6AX6_881167003_next_TRADES_1day_3D.json")
        self.assertEqual(n.marker, "next")
        self.assertTrue(n.is_front_marker)
        m = RawFileName.parse(
            "CL_CLU6_304037484_nearest_expired_ASK_1day_3D.json")
        self.assertEqual(m.marker, "nearest_expired")
        self.assertEqual(m.what, "ASK")

    def test_bid_ask(self):
        n = RawFileName.parse("6J_6JV6_881167175_ASK_1day_1Y.json")
        self.assertEqual(n.what, "ASK")

    def test_bad_names_rejected(self):
        for bad in ("random.json", "CL_CLX6_TRADES_1day_6Y.json",
                    "CL_CLX6_304037511_TRADES_1sec_6Y.json",
                    "CL_CLX6_304037511_WHAT_1day_6Y.json"):
            with self.assertRaises(RawFileError, msg=bad):
                RawFileName.parse(bad)

    def test_split_local_symbol(self):
        self.assertEqual(split_local_symbol("CL", "CLX6"), ("CL", "X", "6"))
        self.assertEqual(split_local_symbol("NG", "NGX26"), ("NG", "X", "26"))
        self.assertEqual(split_local_symbol("6J", "6JV6"), ("6J", "V", "6"))
        with self.assertRaises(RawFileError):
            split_local_symbol("CL", "NGX26")
        with self.assertRaises(RawFileError):
            split_local_symbol("CL", "CLA6")  # A is not a month code


class TestAdapterOnFixture(FixtureTestCase):
    def test_universe_loaded_through_real_schema(self):
        self.assertGreaterEqual(len(self.contracts), 40)
        by = contracts_by_symbol(self.contracts)
        self.assertEqual(sorted(by), ["6J", "CL", "ES"])

    def test_daily_trades_header_fields(self):
        by = contracts_by_symbol(self.contracts)
        # a mid-universe contract: long life, deep bars close-only
        cd = by["CL"][5]
        bars = cd.daily_trades
        self.assertGreater(len(bars), 50)
        # deep history is close-only (v=0, o=h=l=c) — the measured pathology
        frac = sum(1 for b in bars if b.is_close_only) / len(bars)
        self.assertGreater(frac, 0.3)
        # recent bars carry real volume
        self.assertGreater(bars[-1].v, 0)

    def test_expiry_month_field_is_last_trade_date(self):
        by = contracts_by_symbol(self.contracts)
        for cd in by["CL"]:
            raw = load_raw_file(self._path_for(cd))
            self.assertEqual(cd.identity.last_trade_date,
                             dt.datetime.strptime(
                                 raw.header["expiry_month"], "%Y%m%d").date())

    def _path_for(self, cd):
        from pathlib import Path
        name = (f"{cd.identity.symbol}_{cd.identity.local_symbol}_"
                f"{cd.identity.conid}_TRADES_1day_6Y.json")
        return Path(self.uni.raw_dir, name)

    def test_bid_ask_bars_carry_minus_one_volume(self):
        by = contracts_by_symbol(self.contracts)
        cd = by["CL"][-1]  # most recent contract has BID/ASK
        self.assertTrue(cd.daily_bid and cd.daily_ask)
        for b in cd.daily_bid:
            self.assertEqual(b.v, -1)
            self.assertEqual(b.wap, -1.0)
        for d, (bid_close, ask_close) in cd.daily_bidask_map().items():
            self.assertLess(bid_close, ask_close)

    def test_intraday_bars_have_iso_timestamps(self):
        by = contracts_by_symbol(self.contracts)
        cd = by["ES"][-1]
        self.assertTrue(cd.hourly_trades)
        self.assertIn("-04:00", cd.hourly_trades[0].t_iso)
        self.assertEqual(cd.hourly_trades[0].t,
                         dt.date.fromisoformat(cd.hourly_trades[0].t_iso.split("T")[0]))
        self.assertTrue(cd.minute_trades)

    def test_marker_files_not_merged_into_daily(self):
        by = contracts_by_symbol(self.contracts)
        cd = by["CL"][-1]
        self.assertTrue(any("_front_" in f for f in cd.extra_files))

    def test_error_162_empty_files_tolerated(self):
        import json as _json
        import tempfile
        import pathlib
        doc = {
            "fetched_utc": FIXTURE_FETCHED_UTC, "symbol": "CL",
            "conId": 999, "localSymbol": "CLZ9", "expiry_month": "20261120",
            "exchange": "NYMEX", "whatUse": "TRADES", "barSize": "1 hour",
            "durationStr": "30 D", "endDateTime": "", "useRTH": True,
            "endpoint": "synthetic", "timeZoneId": "US/Eastern", "ok": True,
            "errors": [{"code": 162, "msg": "HMDS query returned no data"}],
            "exception": None, "n_rows": 0, "bars": [],
        }
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td, "CL_CLZ9_999_TRADES_1hour_30D.json")
            p.write_text(_json.dumps(doc))
            rf = load_raw_file(p)
            self.assertEqual(rf.bars, [])
        # any OTHER error class fails the load
        doc["errors"] = [{"code": 10168, "msg": "malformed"}]
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td, "CL_CLZ9_999_TRADES_1hour_30D.json")
            p.write_text(_json.dumps(doc))
            with self.assertRaises(RawFileError):
                load_raw_file(p)

    def test_ordering_authority_is_last_trade_date(self):
        # CLZ6 (Dec-2026 expiry) must precede CLF7 (Jan-2027) even though
        # 'F' < 'Z' lexicographically.
        from futbt.rawdata import ContractIdentity
        a = ContractIdentity("CL", "CLZ6", 1, dt.date(2026, 11, 20))
        b = ContractIdentity("CL", "CLF7", 2, dt.date(2026, 12, 21))
        self.assertLess(a.order_key(), b.order_key())

    def test_bad_file_duplicate_bar_raises(self):
        import json
        p = self._path_for(contracts_by_symbol(self.contracts)["CL"][-1])
        doc = json.loads(p.read_text())
        doc["bars"].append(dict(doc["bars"][-1]))
        import tempfile, pathlib
        with tempfile.TemporaryDirectory() as td:
            bad = pathlib.Path(td, p.name)
            bad.write_text(json.dumps(doc))
            with self.assertRaisesRegex(RawFileError, "duplicate"):
                load_raw_file(bad)

    def test_n_rows_mismatch_raises(self):
        import json, tempfile, pathlib
        p = self._path_for(contracts_by_symbol(self.contracts)["CL"][-1])
        doc = json.loads(p.read_text())
        doc["n_rows"] = doc["n_rows"] + 1
        with tempfile.TemporaryDirectory() as td:
            bad = pathlib.Path(td, p.name)
            bad.write_text(json.dumps(doc))
            with self.assertRaisesRegex(RawFileError, "n_rows"):
                load_raw_file(bad)


if __name__ == "__main__":
    unittest.main()
