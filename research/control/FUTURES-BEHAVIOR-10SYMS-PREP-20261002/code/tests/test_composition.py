"""Composition tests: descriptives, additive-attribution ban, declared
weights, risk caps, leave-one-leg via full-path re-runs."""
import datetime as dt
import unittest

from futbt.calendarx import WeekdayCalendar
from futbt.composition import (CombineSpec, FullPathRunner, LeaveOneLegSpec,
                              LeaveOneRuleSpec, PortfolioRiskCaps,
                              SleeveSeries, additive_attribution_guard,
                              always_on_baseline, flat_baseline,
                              pairwise_descriptives, single_leg_baselines)
from futbt.taxonomy import PolicyError


def dates(n):
    return WeekdayCalendar(dt.date(2025, 1, 1),
                           dt.date(2025, 12, 31)).sessions()[:n]


def sleeve(sym, pnls, sessions):
    exposed = {s for s, v in zip(sessions, pnls) if v != 0.0} \
        or set(sessions[:1])
    mapping = {s: v for s, v in zip(sessions, pnls)}
    # pnl allowed only on exposed sessions
    mapping = {s: v for s, v in mapping.items() if s in exposed}
    return SleeveSeries(symbol=sym, pnl_by_session=mapping,
                        exposed_sessions=exposed)


class TestDescriptives(unittest.TestCase):
    def setUp(self):
        self.ds = dates(10)

    def test_perfect_correlation(self):
        a = sleeve("A", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                   self.ds)
        b = sleeve("B", [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
                   self.ds)
        d = pairwise_descriptives(a, b)
        self.assertAlmostEqual(d["pearson_r"], 1.0, places=9)
        self.assertAlmostEqual(d["spearman_rho"], 1.0, places=9)
        self.assertEqual(d["n_overlap_sessions"], 10)

    def test_inverse_correlation_and_co_loss(self):
        a = sleeve("A", [5.0, -4.0, 3.0, -2.0, 1.0, -1.0, 2.0, -3.0, 4.0, -5.0],
                   self.ds)
        b = sleeve("B", [-5.0, 4.0, -3.0, 2.0, -1.0, 1.0, -2.0, 3.0, -4.0, 5.0],
                   self.ds)
        d = pairwise_descriptives(a, b)
        self.assertAlmostEqual(d["pearson_r"], -1.0, places=9)
        # a loses on 5 days; both lose on none of them (perfect anti)
        self.assertEqual(d["co_loss_days"], 0)

    def test_co_loss_counted_on_overlap(self):
        a = sleeve("A", [-1.0, -1.0, 1.0, 1.0], self.ds)
        b = sleeve("B", [-2.0, 3.0, -2.0, 1.0], self.ds)
        d = pairwise_descriptives(a, b)
        self.assertEqual(d["co_loss_days"], 1)
        self.assertAlmostEqual(d["co_loss_given_a_losing"], 0.5, places=9)

    def test_spearman_tie_safe(self):
        a = sleeve("A", [1.0, 1.0, 1.0, 2.0], self.ds)
        b = sleeve("B", [1.0, 2.0, 3.0, 4.0], self.ds)
        d = pairwise_descriptives(a, b)
        self.assertFalse(d["pearson_r"] != d["pearson_r"])  # not NaN

    def test_sleeve_pnl_outside_exposure_rejected(self):
        with self.assertRaisesRegex(PolicyError, "non-exposed"):
            SleeveSeries(symbol="X",
                         pnl_by_session={self.ds[0]: 1.0},
                         exposed_sessions=set())


class TestAdditiveAttributionBan(unittest.TestCase):
    def test_summing_leg_pnls_forbidden(self):
        with self.assertRaisesRegex(PolicyError, "forbidden|full-path"):
            additive_attribution_guard({"ES": 100.0, "CL": -50.0})


class TestCombineSpec(unittest.TestCase):
    def test_declared_weights_ok(self):
        spec = CombineSpec(weights={"ES": 0.5, "CL": 0.5},
                           weight_provenance="DECLARED", declared_by="owner",
                           rationale="equal risk, declared ex ante")
        self.assertEqual(spec.weights["ES"], 0.5)

    def test_in_sample_masquerade_rejected(self):
        with self.assertRaisesRegex(PolicyError, "IN_SAMPLE_MASQUERADE"):
            CombineSpec(weights={"ES": 0.7, "CL": 0.3},
                        weight_provenance="FITTED", declared_by="optimizer",
                        rationale="best on full sample")

    def test_in_sample_acknowledged_only_for_analysis(self):
        spec = CombineSpec(weights={"ES": 0.7, "CL": 0.3},
                           weight_provenance="FITTED", declared_by="optimizer",
                           rationale="in-sample diagnostic only",
                           acknowledge_in_sample=True)
        self.assertTrue(spec.acknowledge_in_sample)

    def test_all_zero_weights_rejected(self):
        with self.assertRaises(PolicyError):
            CombineSpec(weights={"ES": 0.0}, weight_provenance="DECLARED",
                        declared_by="owner", rationale="degenerate")


class TestRiskCaps(unittest.TestCase):
    def caps(self):
        return PortfolioRiskCaps(
            per_sleeve_max_contracts={"ES": 2, "CL": 1, "NG": 1},
            max_concurrent_sleeves=2,
            max_gross_contracts=3,
            max_gross_notional_usd=None)

    def test_per_sleeve_clip(self):
        out = self.caps().enforce({"ES": 5, "CL": 1}, {})
        self.assertEqual(out["positions"], {"ES": 2, "CL": 1})
        self.assertTrue(any("per-sleeve cap" in a for a in out["actions"]))

    def test_concurrency_veto(self):
        out = self.caps().enforce({"ES": 1, "CL": 1, "NG": 1}, {})
        self.assertEqual(len(out["positions"]), 2)
        self.assertTrue(any("concurrent" in a for a in out["actions"]))

    def test_gross_rescale(self):
        out = self.caps().enforce({"ES": 2, "CL": 1, "NG": 1}, {})
        self.assertLessEqual(sum(abs(q) for q in out["positions"].values()), 3)

    def test_notional_cap_vetoes_all(self):
        caps = PortfolioRiskCaps(
            per_sleeve_max_contracts={"ES": 2}, max_concurrent_sleeves=5,
            max_gross_contracts=10, max_gross_notional_usd=100.0)
        out = caps.enforce({"ES": 1}, {"ES": 200.0})
        self.assertEqual(out["positions"], {})
        self.assertTrue(any("notional" in a for a in out["actions"]))


class TestLeaveOneLeg(unittest.TestCase):
    def test_marginal_effect_uses_two_full_path_runs(self):
        calls = []

        def runner(sleeves):
            calls.append(tuple(sleeves))
            # deliberately non-additive interaction: portfolio effect
            base = {"ES": 100.0, "CL": 60.0, "NG": -10.0}
            if set(sleeves) == {"ES", "CL", "NG"}:
                return {"total_net_usd": 170.0, "interaction": +20.0}
            return {"total_net_usd": sum(base[s] for s in sleeves),
                    "interaction": 0.0}

        fp = FullPathRunner(runner=runner)
        spec = LeaveOneLegSpec(all_sleeves=("ES", "CL", "NG"), runner=fp)
        res = spec.marginal_effect("NG")
        self.assertEqual(len(calls), 2)
        self.assertIn(("CL", "ES"), calls)          # full path without NG
        self.assertEqual(res["method"],
                         "full-path re-run difference (NOT additive attribution)")
        # interaction term makes removal cost differ from leg's own PnL
        self.assertEqual(res["base"]["total_net_usd"], 170.0)
        self.assertEqual(res["without_leg"]["total_net_usd"], 160.0)
        self.assertEqual(len(res["runs"]), 2)

    def test_leave_one_rule_spec(self):
        def runner(rules):
            return {"total_net_usd": 50.0 * len(rules)}
        fp = FullPathRunner(runner=runner)
        spec = LeaveOneRuleSpec(all_rules=("r1", "r2"), runner=fp)
        res = spec.marginal_effect("r1")
        self.assertEqual(res["base"]["total_net_usd"], 100.0)
        self.assertEqual(res["without_rule"]["total_net_usd"], 50.0)


class TestBaselines(unittest.TestCase):
    def test_flat_baseline_is_zero(self):
        ds = dates(5)
        b = flat_baseline(ds)
        self.assertTrue(all(v == 0.0 for v in b["pnl_by_session"].values()))

    def test_always_on_and_single_leg_use_full_path_runners(self):
        ds = dates(4)
        def mk_runner(total):
            return lambda direction: {
                "pnl_by_session": {s: total / len(ds) for s in ds}}
        b = always_on_baseline({"ES": mk_runner(100.0),
                                "CL": mk_runner(50.0)}, ds, "long")
        self.assertAlmostEqual(
            sum(b["pnl_by_session"].values()), 150.0, places=9)
        sl = single_leg_baselines({"ES": mk_runner(100.0)}, ds)
        self.assertAlmostEqual(sum(sl["ES"]["pnl_by_session"].values()), 100.0)
        with self.assertRaises(ValueError):
            always_on_baseline({}, ds, "sideways")


if __name__ == "__main__":
    unittest.main()
