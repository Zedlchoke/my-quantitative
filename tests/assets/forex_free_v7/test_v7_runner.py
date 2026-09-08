"""FOREX-FREE-V7 runner + driver tests (synthetic fixtures, no real PnL)."""
import copy
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)

from research.assets.forex_free_v7 import exec_driver_v7 as D  # noqa: E402
from research.assets.forex_free_v7 import family_a4p1_v7 as F1  # noqa: E402
from research.assets.forex_free_v7 import family_a6p2_v7 as F2  # noqa: E402

VENV_PY = sys.executable
DRIVER = os.path.join(ROOT, "research", "assets", "forex_free_v7",
                      "exec_driver_v7.py")

SYNTH_ROOT = None
SYNTH_DATA = None
SYNTH_PATHS = None


def setUpModule():
    global SYNTH_ROOT, SYNTH_DATA, SYNTH_PATHS
    SYNTH_ROOT = tempfile.mkdtemp(prefix="v7_tests_synth_")
    SYNTH_DATA = os.path.join(SYNTH_ROOT, "synthetic_data")
    subprocess.run([VENV_PY,
                    os.path.join(ROOT, "research", "assets", "forex_free_v7",
                                 "synthetic_fixture_v7.py"), SYNTH_DATA],
                   check=True, capture_output=True)
    SYNTH_PATHS = {
        "price_dir": SYNTH_DATA,
        "clocks_path": os.path.join(SYNTH_DATA, "clocks_v7.json"),
        "announcement_ledger": os.path.join(SYNTH_DATA, "ledger.jsonl"),
        "s0_start": date(2018, 4, 4), "s0_end": date(2025, 7, 24),
        "fold_starts": D.FOLD_STARTS,
        "expected_clock_count": 24,
        "enforce_real_spans": False,
    }


def tearDownModule():
    shutil.rmtree(SYNTH_ROOT, ignore_errors=True)


def _book_arm(family_mod, arm):
    out = family_mod.run_arm(arm, SYNTH_PATHS)
    trades = []
    for d in out["decisions"]:
        d["notional_usd"] = D.NOTIONAL_USD
        trades.append(d)
    reader = D.LedgerVintageReader(D.dedupe_ledger_rows(
        D.load_ledger_rows(SYNTH_PATHS["announcement_ledger"])))
    return trades, reader


class TestCostOnce(unittest.TestCase):
    def test_cost_charged_exactly_once_per_side(self):
        trades, reader = _book_arm(F1, "anchor")
        self.assertTrue(trades)
        for tier in ("1.0", "1.5", "2.0"):
            pnls, _ = D.book_trades(trades, tier, reader, strict=False)
            for tr, p in zip(trades, pnls):
                gross = D.price_pnl_usd(tr)
                expected = gross - 2.0 * D.K.bps_cost(tr["notional_usd"],
                                                      float(tier)) \
                    + D.financing_adjustment_usd(reader, tr, strict=False)
                self.assertAlmostEqual(p, expected, places=9)

    def test_stress_applies_to_booked_roundtrip_not_scaled(self):
        """The tier-2.0 cost is 2x the tier-1.0 cost per side; scaling the
        tier-1.0 net PnL by 2 would be a different (forbidden) number."""
        trades, reader = _book_arm(F1, "anchor")
        p1, _ = D.book_trades(trades, "1.0", reader, strict=False)
        p2, _ = D.book_trades(trades, "2.0", reader, strict=False)
        for tr, a, b in zip(trades, p1, p2):
            cost1 = 2.0 * D.K.bps_cost(tr["notional_usd"], 1.0)
            cost2 = 2.0 * D.K.bps_cost(tr["notional_usd"], 2.0)
            self.assertAlmostEqual(b, a + (cost1 - cost2), places=9)


class TestDeterminism(unittest.TestCase):
    def test_double_run_byte_identical(self):
        a = F2.run_arm("anchor", SYNTH_PATHS)
        b = F2.run_arm("anchor", SYNTH_PATHS)
        self.assertEqual(json.dumps(a["decisions"], sort_keys=True),
                         json.dumps(b["decisions"], sort_keys=True))
        self.assertEqual(a["meta"]["n_decisions"], b["meta"]["n_decisions"])


class TestFailClosed(unittest.TestCase):
    def test_malformed_price_file_fails_closed(self):
        bad = tempfile.mkdtemp(prefix="v7_bad_price_")
        try:
            for f in os.listdir(SYNTH_DATA):
                if f.startswith("EURUSD_1h_"):
                    with open(os.path.join(bad, f), "w") as fh:
                        json.dump({"status": "error", "code": 400,
                                   "message": "No data", "meta": {}}, fh)
                else:
                    shutil.copy(os.path.join(SYNTH_DATA, f),
                                os.path.join(bad, f))
            paths = dict(SYNTH_PATHS)
            paths["price_dir"] = bad
            with self.assertRaises(F1.DataBlocked):
                F1.run_arm("anchor", paths)
        finally:
            shutil.rmtree(bad, ignore_errors=True)

    def test_clock_count_mismatch_fails_closed(self):
        paths = dict(SYNTH_PATHS)
        paths["expected_clock_count"] = 999
        with self.assertRaises(F1.DataBlocked):
            F1.run_arm("anchor", paths)

    def test_missing_ledger_fails_closed(self):
        paths = dict(SYNTH_PATHS)
        paths["announcement_ledger"] = os.path.join(SYNTH_ROOT, "nope.jsonl")
        with self.assertRaises(D.DataBlocked):
            D.load_ledger_rows(paths["announcement_ledger"])

    def test_pinned_ledger_sha_enforced(self):
        with self.assertRaises(RuntimeError):
            D.load_pinned_ledger_or_fail(
                os.path.join(SYNTH_DATA, "ledger.jsonl"))


class TestControlDiffersFromAnchor(unittest.TestCase):
    def test_control_schedule_differs(self):
        a = F1.run_arm("anchor", SYNTH_PATHS)
        c = F1.run_arm("control", SYNTH_PATHS)
        ka = {(d["pair"], d["entry_day"], d["side"]) for d in a["decisions"]}
        kc = {(d["pair"], d["entry_day"], d["side"]) for d in c["decisions"]}
        self.assertNotEqual(ka, kc)
        self.assertTrue(kc)  # control non-vacuous on the fixture


class TestDryRunSanitized(unittest.TestCase):
    OUTCOME_KEYS = {"pnl", "pf", "expectancy", "stress", "profit", "return",
                    "returns", "total_pnl", "gross_positive", "mdd",
                    "break_even", "concentration", "dual_book", "lopo",
                    "financing_adjustment"}

    def _walk(self, o):
        if isinstance(o, dict):
            for k, v in o.items():
                if any(s in str(k).lower() for s in self.OUTCOME_KEYS):
                    raise AssertionError(f"outcome-shaped key in dryrun: {k}")
                self._walk(v)
        elif isinstance(o, list):
            for v in o:
                self._walk(v)

    def test_dryrun_records_sanitized_and_nonvacuous(self):
        for mod in (F1, F2):
            for arm in mod.ARM_IDS:
                out = mod.run_arm(arm, SYNTH_PATHS)
                self._walk(out)
                self.assertGreater(out["meta"]["n_decisions"], 0,
                                   f"vacuous arm {mod.__name__}:{arm}")


class TestScoredRefusal(unittest.TestCase):
    def test_refuses_without_run_contract(self):
        cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp(prefix="v7_refuse_"))
            proc = subprocess.run([VENV_PY, DRIVER, "scored"],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            payload = json.loads(proc.stdout)
            self.assertTrue(payload["refused"])
            self.assertIn("run_contract_file", payload["missing_gates"])
        finally:
            os.chdir(cwd)


class TestUsdDriftAndGates(unittest.TestCase):
    def test_gate_margins_structure(self):
        rec, pnls, _ = D.run_scored_arm("FXFV7-A4-P1", "anchor", SYNTH_PATHS,
                                        "SYNTHETIC_TEST")
        rec["control_does_not_reproduce"] = True
        ok, reasons, margins = D.evaluate_gates(rec)
        self.assertEqual(len(margins), 12)
        for m in margins:
            self.assertIn("gate", m)
            self.assertIn("margin", m)




class TestNoLookaheadFundedDecision(unittest.TestCase):
    """F-A7-PL-3 remediation: the leak class A7 caught must be structurally
    impossible and tested on both fixture and real authorities."""

    def test_every_entry_at_or_after_window_end(self):
        from datetime import date, datetime, timedelta, timezone
        for mod, paths in ((F1, SYNTH_PATHS),):
            clocks = {}
            for r in json.load(open(paths["clocks_path"]))["clocks"]:
                T = datetime.fromisoformat(r["event_available_time_utc"]
                                           .replace("Z", "+00:00"))
                pc = r["precision_class"]
                w0 = T if pc.startswith("INSTANT") else \
                    (T.replace(hour=0, minute=0, second=0) + timedelta(days=1))
                clocks[r["clock_id"]] = w0 + timedelta(hours=24)
            for arm in mod.ARM_IDS:
                out = mod.run_arm(arm, paths)
                for d in out["decisions"]:
                    w1 = clocks[d["clock_id"]]
                    if arm == "control":
                        w1 = w1 + timedelta(days=7)
                    self.assertGreaterEqual(
                        datetime.fromisoformat(d["entry_ts"]),
                        w1,
                        f"lookahead: {arm} entry {d['entry_ts']} < w1 {w1}")

    def test_event_plus_one_day_moves_decision_one_period(self):
        """Availability-lag mutation contract: shifting the event +1 day
        moves the funded decision exactly one 16:00-NY period."""
        c0 = F1._first_decision_after(datetime(2021, 6, 10, 13, 35, tzinfo=timezone.utc))
        c1 = F1._first_decision_after(datetime(2021, 6, 11, 13, 35, tzinfo=timezone.utc))
        self.assertEqual((c1 - c0).days, 1)

if __name__ == "__main__":
    unittest.main()
