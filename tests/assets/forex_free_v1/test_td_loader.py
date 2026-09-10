"""Loader goldens: synthetic TD windows -> normalized bars; integrity fails closed.
Uses an isolated temp data root; never touches real data_raw files."""
import json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from research.assets.forex_free_v1 import td_loader as L  # noqa: E402


def win(vals):
    return {"meta": {}, "values": vals, "status": "ok"}


def bar(dt, o, h, l, c):
    return {"datetime": dt, "open": str(o), "high": str(h), "low": str(l), "close": str(c)}


class TestTdLoader(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="fxv1_loader_")
        os.makedirs(os.path.join(self.root, "forex_free_v1"))

    def _write(self, name, obj):
        with open(os.path.join(self.root, "forex_free_v1", name), "w") as f:
            json.dump(obj, f)

    def test_sorted_unique_deterministic(self):
        self._write("EURUSD_1h_2024-03-04_05_a.json", win(
            [bar("2024-03-04 05:00:00", 1, 2, 0.5, 1.4),
             bar("2024-03-04 04:00:00", 1, 2, 0.5, 1.3)]))
        self._write("EURUSD_1h_2024-03-04_02_a.json", win(
            [bar("2024-03-04 02:00:00", 1, 2, 0.5, 1.5),   # boundary dup of next window
             bar("2024-03-04 01:00:00", 1, 2, 0.5, 1.2)]))
        rows, quar = L.load_pair_h1("EUR/USD", self.root)
        self.assertEqual([r["datetime"] for r in rows],
                         ["2024-03-04 01:00:00", "2024-03-04 02:00:00",
                          "2024-03-04 04:00:00", "2024-03-04 05:00:00"])
        self.assertEqual(L.digest_bars(rows), L.digest_bars(L.load_pair_h1("EUR/USD", self.root)[0]))
        self.assertEqual(quar, [])

    def test_request_manifest_verification(self):
        self._write("GBPUSD_1h_2099-01-01_01_a.json", win([bar("2099-01-01 01:00:00", 1, 1.1, 0.9, 1.0)]))
        good = {"requests": [{"sha256": L.sha256_file(os.path.join(self.root, "forex_free_v1", "GBPUSD_1h_2099-01-01_01_a.json"))}]}
        self.assertEqual(len(L.load_pair_h1("GBP/USD", self.root, good)[0]), 1)
        with self.assertRaises(ValueError):
            L.load_pair_h1("GBP/USD", self.root, {"requests": [{"sha256": "0" * 64}]})

    def test_ohlc_violation_fails_closed(self):
        self._write("AUDUSD_1h_2099-01-01_01_a.json", win([bar("2099-01-01 01:00:00", 2, 1, 0.5, 1.5)]))
        with self.assertRaises(ValueError):
            L.load_pair_h1("AUD/USD", self.root)

    def test_malformed_ts_fails_closed(self):
        self._write("USDJPY_1h_2099-01-01_01_a.json", win(
            [{"datetime": "not-a-time", "open": "1", "high": "1", "low": "1", "close": "1"}]))
        with self.assertRaises(ValueError):
            L.load_pair_h1("USD/JPY", self.root)

    def test_quarantine_and_ceiling(self):
        # one artifact bar (low > open by 2 pipettes) -> quarantined, not loaded
        self._write("NZDUSD_1h_2099-01-01_01_a.json", win(
            [bar("2099-01-01 01:00:00", 1.1000, 1.1010, 1.1002, 1.1005),
             bar("2099-01-01 02:00:00", 1.2000, 1.2002, 1.1998, 1.2001)]))
        rows, quar = L.load_pair_h1("NZD/USD", self.root, quarantine_ceiling=0.6)
        self.assertEqual(len(rows), 1); self.assertEqual(len(quar), 1)
        self.assertEqual(quar[0]["reason"], "OHLC_INCONSISTENT_PROVIDER_ARTIFACT")
        with self.assertRaises(ValueError):
            L.load_pair_h1("NZD/USD", self.root, quarantine_ceiling=0.4)  # 1/2 exceeds 40%%? no: 0.5>0.4 raises

    def test_missing_files_fail_closed(self):
        with self.assertRaises(ValueError):
            L.load_pair_h1("NZD/USD", self.root)


if __name__ == "__main__":
    unittest.main()
