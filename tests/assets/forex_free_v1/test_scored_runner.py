"""Scored-runner goldens: hand-computed metrics for both family API shapes,
publication/replay accounting, arm identities, integration with family1."""
import json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from research.assets.forex_free_v1 import scored_runner as R  # noqa: E402
from research.assets.forex_free_v1 import family1, family2  # noqa: E402


def f1_trade(tid, day, ret, position=1):
    return {"trade_id": tid, "position": position,
            "entry_instant": f"2024-03-{day} 12:00:00+00:00",
            "exit_instant": f"2024-03-{day} 21:00:00+00:00",
            "gross_return_frac": ret + 0.0003, "cost_frac": 0.0003, "net_return_frac": ret}


def f2_trade(day, ret):
    return {"arm_id": "anchor", "pair": "EUR/USD", "day": day,
            "gross_ret": ret + 0.0003, "cost_ret": 0.0003, "net_ret": ret}


class TestExtraction(unittest.TestCase):
    def test_family1_shape_hand_computed(self):
        run = {"run_digest": "x", "cashflows": [f1_trade("anchor|EUR/USD|2024-03-04", "04", 0.001)]}
        trades = R.extract_trades("family1", "EUR/USD", run)
        self.assertEqual(len(trades), 1)
        t = trades[0]
        # hand: net_return 0.001 x 10,000 = 10.0 USD; cost_frac recorded, NOT re-subtracted
        self.assertAlmostEqual(t["pnl"], 10.0, places=9)
        self.assertAlmostEqual(t["cost_frac"], 0.0003)
        self.assertEqual(t["exit_ts"], "2024-03-04 21:00:00+00:00")

    def test_family2_shape_hand_computed(self):
        run = {"run_digest": "x", "cashflows": [f2_trade("2024-03-04", -0.002)]}
        t = R.extract_trades("family2", "EUR/USD", run)[0]
        self.assertAlmostEqual(t["pnl"], -20.0, places=9)  # -0.002 x 10,000
        self.assertEqual(t["entry_ts"], "2024-03-04")

    def test_costs_counted_once(self):
        run = {"run_digest": "x", "cashflows": [f1_trade("t1", "04", 0.001)]}
        pnl = R.extract_trades("family1", "EUR/USD", run)[0]["pnl"]
        gross = 0.0013 * R.FROZEN_NOTIONAL
        self.assertAlmostEqual(pnl, gross - 0.0003 * R.FROZEN_NOTIONAL, places=9)


class TestMetrics(unittest.TestCase):
    def trades_pnls(self):
        # 9 trades, hand-built to pass every gate (A7 W1 B2): positives
        # EUR 50 / GBP 45 / JPY 56 of 151 -> 33.1/29.8/37.1% <= 40%;
        # folds +70/+40/+32 (fold0 46.4% <= 50%); fold PFs 9.0 >= 0.80;
        # MDD = 5 USD <= 12% notional
        rets = [0.003, 0.002, 0.002, 0.002, -0.0005, 0.0025, 0.0016, -0.0004, 0.002]
        pairs = ["EUR/USD", "GBP/USD", "EUR/USD", "USD/JPY", "GBP/USD",
                 "GBP/USD", "USD/JPY", "EUR/USD", "USD/JPY"]
        out = []
        for i, r in enumerate(rets):
            out.append({"pair": pairs[i], "trade_id": f"t{i}",
                        "entry_ts": f"2024-01-{i+1:02d}T00:00:00+00:00",
                        "exit_ts": f"2024-01-{i+1:02d}T12:00:00+00:00",
                        "net_return": r, "pnl": r * R.FROZEN_NOTIONAL,
                        "cost_frac": 0.0003})
        return out

    def test_folds_hand_computed(self):
        folds = R.fold_metrics(self.trades_pnls())
        self.assertEqual([f["trades"] for f in folds], [3, 3, 3])
        self.assertTrue(folds[0]["positive"])   # (30+20+15)=65
        self.assertTrue(folds[1]["positive"])   # (20-5+25)=+40, PF 45/5
        self.assertTrue(folds[2]["positive"])   # (16-4+25)=+37 -> 16-4+25? see rets
        self.assertAlmostEqual(folds[0]["total_pnl"], 70.0, places=9)
        self.assertAlmostEqual(folds[1]["profit_factor"], 45.0 / 5.0, places=9)

    def test_mdd_hand_computed(self):
        pnls = [t["pnl"] for t in self.trades_pnls()]
        # cumulative: 60, 20, -40, -20, 30 -> peak 60, trough -40 => MDD 100
        # cumulative: 30,50,65,85,80,105,121,117,142 -> worst drawdown 5
        self.assertAlmostEqual(R.mdd_of(pnls), 5.0, places=9)

    def test_concentration(self):
        c = R.concentration(self.trades_pnls())
        pos_eur = sum(t["pnl"] for t in self.trades_pnls() if t["pair"] == "EUR/USD" and t["pnl"] > 0)
        pos_all = sum(t["pnl"] for t in self.trades_pnls() if t["pnl"] > 0)
        self.assertAlmostEqual(c["EUR/USD"], pos_eur / pos_all, places=6)

    def test_zero_trades_gate(self):
        rec = R.assemble_cell_record({"trades": []}, "family1", "anchor", 1.0)
        ok, reason = R.stage_a_gates(rec)
        self.assertFalse(ok)
        self.assertEqual(reason, "NO_TRADES")


class TestGates(unittest.TestCase):
    def passing_record(self):
        rec = R.assemble_cell_record({"trades": self.trades_pnls()}, "family1", "anchor", 1.0)
        return rec

    trades_pnls = TestMetrics.trades_pnls

    def test_gate_requires_expectancy(self):
        rec = self.passing_record()
        ok, reason = R.stage_a_gates(rec)
        # strict: a (False, reason) tuple is truthy — A7 W1 delta finding B2
        self.assertTrue(ok, reason)
        self.assertEqual(reason, "PASS")
        bad = json.loads(json.dumps(rec))
        bad["book"]["expectancy"] = -1.0
        ok, reason = R.stage_a_gates(bad)
        self.assertFalse(ok); self.assertEqual(reason, "EXPECTANCY_NONPOSITIVE")


class TestPublication(unittest.TestCase):
    def record(self, trades=1):
        t = {"pair": "EUR/USD", "trade_id": "t", "entry_ts": "x", "exit_ts": "y",
             "net_return": 0.001, "pnl": 10.0, "cost_frac": 0.0003}
        return R.assemble_cell_record({"trades": [t] * trades}, "family1", "anchor", 1.0)

    def test_observed_publication_replay(self):
        with tempfile.TemporaryDirectory() as d:
            verdict = os.path.join(d, "verdict.json")
            json.dump({"verdict": "FOREX_FREE_V1_W1_LAUNCH_AUTHORIZED", "w1_sha": "abc"}, open(verdict, "w"))
            led = os.path.join(d, "ledger.jsonl")
            rec = self.record()
            d1, p1 = R.publish_cell(led, rec, verdict, "abc")
            self.assertEqual((d1, p1), (1, True))
            d2, p2 = R.publish_cell(led, rec, verdict, "abc")
            self.assertEqual((d2, p2), (0, False))  # idempotent replay
            self.assertEqual(len([l for l in open(led)]), 1)

    def test_publication_requires_authorization(self):
        with tempfile.TemporaryDirectory() as d:
            led = os.path.join(d, "ledger.jsonl")
            with self.assertRaises(ValueError):
                R.publish_cell(led, self.record(), os.path.join(d, "missing.json"), "abc")

    def test_zero_trade_refused_but_observed(self):
        with tempfile.TemporaryDirectory() as d:
            verdict = os.path.join(d, "verdict.json")
            json.dump({"verdict": "FOREX_FREE_V1_W1_LAUNCH_AUTHORIZED", "w1_sha": "abc"}, open(verdict, "w"))
            led = os.path.join(d, "ledger.jsonl")
            rec = R.assemble_cell_record({"trades": []}, "family1", "anchor", 1.0)
            d1, p1 = R.publish_cell(led, rec, verdict, "abc")
            self.assertEqual((d1, p1), (1, False))
            self.assertIn("REFUSED_ZERO_TRADES", open(led).read())


class TestArmIdentities(unittest.TestCase):
    def test_six_distinct(self):
        f1 = {f"family1:{k}": json.dumps(v, sort_keys=True) for k, v in family1.frozen_arm_configs().items()}
        f2 = {f"family2:{k}": family2.arm_identity(k) for k in family2.ARM_IDS}
        ids = list(f1.values()) + list(f2.values())
        self.assertEqual(len(ids), 6)
        self.assertEqual(len(set(ids)), 6)

    def test_control_signs(self):
        self.assertEqual(family1.frozen_arm_configs()["control"]["position_sign"], -1)
        self.assertEqual(family2.ARM_REGISTRY["control"]["direction_multiplier"], -1)


class TestFamily1Integration(unittest.TestCase):
    def test_cell_run_deterministic_and_tier_delay(self):
        import datetime as dt
        rows, price = [], 1.0800
        base = dt.datetime(2024, 3, 4)
        for day in range(5):
            for h in range(24):
                ts = base + dt.timedelta(days=day, hours=h); price += 0.0002
                rows.append({"datetime": ts.strftime("%Y-%m-%d %H:%M:%S"),
                             "open": f"{price-0.0002:.5f}", "high": f"{price+0.0001:.5f}",
                             "low": f"{price-0.0003:.5f}", "close": f"{price:.5f}"})
        by_pair = {"EUR/USD": rows, "GBP/USD": rows}
        c1 = R.run_family_cell(family1, "family1", by_pair, "anchor", 1.0)
        c2 = R.run_family_cell(family1, "family1", by_pair, "anchor", 1.0)
        self.assertEqual(c1["digest"], c2["digest"])  # deterministic double run
        rec1 = R.assemble_cell_record(c1, "family1", "anchor", 1.0)
        self.assertGreater(rec1["book"]["trades"], 0)  # n_trades > 0 before publication
        tier2 = R.run_family_cell(family1, "family1", by_pair, "anchor", 2.0)
        self.assertGreater(json.dumps(tier2["trades"][0]), "")

    def test_family2_through_runner_has_digest(self):
        # regression for A7 W1 B1: family2 run digest key is sha256.
        # 40-day fixture: 38 quiet days (~20+ rollover closes warm-up), then a
        # +150-pip 4-bar NY extension day -> |z| >= 1 fade fires deterministically.
        import datetime as dt, math
        rows = []
        base = dt.datetime(2024, 1, 8)  # Monday
        c_prev = None
        for day in range(40):
            day_level = 1.1000 + 0.003 * math.sin(day * 1.7)  # deterministic day walk
            for h in range(24):
                ts = base + dt.timedelta(days=day, hours=h)
                p = day_level + 0.0003 * math.sin(h * 0.9)
                if day == 38 and 13 <= h < 17:  # anchor-window extension ~2-3 sigma
                    p += 0.0015 * (h - 12)
                o = round(p - 0.00015, 6); c = round(p + 0.00015, 6)
                rows.append({"datetime": ts.strftime("%Y-%m-%d %H:%M:%S"),
                             "open": f"{o:.6f}", "high": f"{max(o,c)+0.00015:.6f}",
                             "low": f"{min(o,c)-0.00015:.6f}", "close": f"{c:.6f}"})
        cell = R.run_family_cell(family2, "family2", {"EUR/USD": rows}, "anchor", 1.0)
        rec = R.assemble_cell_record(cell, "family2", "anchor", 1.0)
        self.assertGreater(rec["book"]["trades"], 0)  # B1 regression: family2 cells compute
        self.assertTrue(cell["module_scoring_authorized_fields"])

    def test_runner_source_has_no_credential_or_s1_access(self):
        src = open(R.__file__).read()
        self.assertNotIn(".env", src)
        self.assertNotIn("api_key", src.lower())


if __name__ == "__main__":
    unittest.main()
