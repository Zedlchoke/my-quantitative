"""Walk-forward tests: purge/embargo, fold suppression ban, nested selection
stamps, deterministic replay, mutation hooks."""
import datetime as dt
import unittest

from futbt.walkforward import (ExposureCell, Fold, WalkForwardPlanner,
                               assert_future_mutation_invariance,
                               assert_prefix_determinism, replay_deterministic)
from futbt.taxonomy import PolicyError


def sessions_2025():
    from futbt.calendarx import WeekdayCalendar
    return WeekdayCalendar(dt.date(2025, 1, 1), dt.date(2025, 12, 31)).sessions()


class TestPlanning(unittest.TestCase):
    def test_plan_produces_folds_with_purge_equal_to_horizon(self):
        p = WalkForwardPlanner(sessions_2025(), true_horizon_sessions=10)
        folds = p.plan(n_folds=4)
        self.assertGreaterEqual(len(folds), 1)
        for f in folds:
            self.assertEqual(f.purge_sessions, 10)
            self.assertEqual(f.true_horizon_sessions, 10)
            self.assertLess(f.train_end, f.test_start)

    def test_horizon_must_be_positive(self):
        with self.assertRaises(PolicyError):
            WalkForwardPlanner(sessions_2025(), true_horizon_sessions=0)

    def test_short_history_raises(self):
        p = WalkForwardPlanner(sessions_2025()[:5], true_horizon_sessions=5)
        with self.assertRaises(PolicyError):
            p.plan(n_folds=3, train_frac=0.95)  # no test room at all


class TestPurgeEmbargo(unittest.TestCase):
    def _planner(self, horizon=5, embargo=2):
        return WalkForwardPlanner(sessions_2025(), true_horizon_sessions=horizon,
                                  embargo_sessions=embargo)

    def _fold(self, planner):
        folds = planner.plan(n_folds=1, train_frac=0.5)
        return folds[0]

    def _cells(self, planner):
        # one exposure cell per session for one symbol
        return [ExposureCell("ES", s) for s in planner.sessions]

    def test_purge_drops_train_cells_within_horizon_of_test(self):
        p = self._planner(horizon=5, embargo=0)
        f = self._fold(p)
        train, test = p.apply_purge_embargo(f, self._cells(p))
        # boundary: train_end itself is within 5 sessions of test_start
        last_train = max(c.session for c in train)
        gap = p.sessions.index(f.test_start) - p.sessions.index(last_train)
        self.assertGreaterEqual(gap, 5)  # >= true horizon by construction
        dropped_train = [d for d in f.dropped if d.phase == "train"]
        self.assertTrue(dropped_train)
        self.assertTrue(all(d.reason == "PURGE" for d in dropped_train))

    def test_embargo_drops_test_cells_right_after_train(self):
        p = self._planner(horizon=5, embargo=3)
        f = self._fold(p)
        train, test = p.apply_purge_embargo(f, self._cells(p))
        first_test = min(c.session for c in test)
        gap = p.sessions.index(first_test) - p.sessions.index(f.train_end)
        self.assertGreater(gap, 3)
        # embargo drops are exactly the cells in (train_end, train_end+3]
        # (test-phase drops may now also include LABEL_CENSORED cells at
        # the fold's legal boundary — R5 fix, audited separately)
        emb = [d for d in f.dropped if d.reason == "EMBARGO"]
        self.assertTrue(emb)
        self.assertTrue(all(d.phase == "test" for d in emb))
        idx = {d: i for i, d in enumerate(p.sessions)}
        self.assertEqual({idx[d.cell.session] for d in emb},
                         set(range(idx[f.train_end] + 1,
                                   idx[f.train_end] + 4)))

    def test_under_purged_fold_refused(self):
        p = self._planner(horizon=5)
        f = self._fold(p)
        bad = Fold(fold_id=f.fold_id, train_start=f.train_start,
                   train_end=f.train_end, test_start=f.test_start,
                   test_end=f.test_end, purge_sessions=3,
                   embargo_sessions=0, true_horizon_sessions=5)
        with self.assertRaisesRegex(PolicyError, "under-purge"):
            p.apply_purge_embargo(bad, self._cells(p))


class TestFoldSuppressionBan(unittest.TestCase):
    def test_performance_reason_refused(self):
        p = WalkForwardPlanner(sessions_2025(), true_horizon_sessions=5)
        f = p.plan(n_folds=1)[0]
        for reason in ("LOW_TOTAL_RETURN", "NEGATIVE_FOLD_PNL",
                       "BELOW_FLOOR"):
            with self.assertRaisesRegex(PolicyError, "performance"):
                p.drop_fold(f, reason, {"metric": -0.1})

    def test_coverage_reason_allowed_and_recorded(self):
        p = WalkForwardPlanner(sessions_2025(), true_horizon_sessions=5)
        f = p.plan(n_folds=1)[0]
        p.drop_fold(f, "INSUFFICIENT_COVERAGE", {"n_test_cells": 3})
        self.assertIn("INSUFFICIENT_COVERAGE", f.selection_note)


class TestNestedSelection(unittest.TestCase):
    def test_selection_frozen_and_stamped_at_train_end(self):
        p = WalkForwardPlanner(sessions_2025(), true_horizon_sessions=5)
        f = p.plan(n_folds=1)[0]

        class PinnedView:
            def __init__(self, asof):
                self.asof = asof

        view = PinnedView(f.train_end)
        params = p.run_selection(f, lambda v: {"threshold": 0.5},
                                 view)
        self.assertEqual(params, {"threshold": 0.5})
        self.assertEqual(f.selected_params, {"threshold": 0.5})
        self.assertEqual(f.selection_asof, f.train_end)

    def test_selector_must_return_dict(self):
        p = WalkForwardPlanner(sessions_2025(), true_horizon_sessions=5)
        f = p.plan(n_folds=1)[0]
        with self.assertRaises(PolicyError):
            p.run_selection(f, lambda v: "best", None)


class TestReplayAndHooks(unittest.TestCase):
    def test_replay_deterministic(self):
        p = WalkForwardPlanner(sessions_2025(), true_horizon_sessions=5)
        folds = p.plan(n_folds=3)

        def runner(fold, phase, seed):
            return {"fold": fold.fold_id, "phase": phase, "seed": seed,
                    "checksum": hash((fold.fold_id, phase, seed)) == 0
                    or sum(ord(c) for c in fold.fold_id + phase) + seed}
        a = replay_deterministic(folds, runner, seed=42)
        b = replay_deterministic(folds, runner, seed=42)
        self.assertEqual(a, b)

    def test_prefix_determinism_hook(self):
        full = {"decisions": [
            {"session": "2025-01-06", "act": "A"},
            {"session": "2025-02-03", "act": "B"},
            {"session": "2025-03-03", "act": "C"}]}
        trunc = {"decisions": full["decisions"][:2]}
        assert_prefix_determinism(full, trunc, dt.date(2025, 2, 28))
        bad = {"decisions": full["decisions"][:2][::-1]}
        with self.assertRaises(AssertionError):
            assert_prefix_determinism(full, bad, dt.date(2025, 2, 28))

    def test_future_mutation_hook(self):
        base = {"decisions": [{"session": "2025-01-06", "act": "A"},
                              {"session": "2025-02-03", "act": "B"}]}
        same = {"decisions": [{"session": "2025-01-06", "act": "A"},
                              {"session": "2025-02-03", "act": "B"}]}
        assert_future_mutation_invariance(base, same, dt.date(2025, 1, 31))
        mutated = {"decisions": [{"session": "2025-01-06", "act": "Z"}]}
        with self.assertRaises(AssertionError):
            assert_future_mutation_invariance(base, mutated,
                                              dt.date(2025, 1, 31))


if __name__ == "__main__":
    unittest.main()
