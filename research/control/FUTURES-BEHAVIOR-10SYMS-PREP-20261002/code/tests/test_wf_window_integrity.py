"""R5 window-integrity tests (co-owner review, round co-owner-review-fix-1).

Co-owner case: weekday calendar Jan 1 - Jun 30 2026 (129 sessions), 4 folds,
train_frac 0.7, true horizon 2. Planned fold1 test window is
2026-05-08 .. 2026-05-20, but apply_purge_embargo used to emit TEST cells all
the way to 2026-06-30 (29 excess sessions), overlapping the next fold's test
window, and kept test cells whose labels cannot mature inside the fold.

Laws pinned here (per-window integrity):
  * test_end ENFORCED: no emitted test cell beyond the fold's test_end;
    post-test cells are excluded from the fold and audited (out_of_fold).
  * label maturity: a label at t needs horizon h of future data; test cells
    whose horizon extends past test_end are dropped/censored with an audited
    reason (LABEL_CENSORED), never silently truncated.
  * purge >= true horizon on the train side (existing law, regression guard).
  * NO overlapping folds: planned test windows and emitted test cell sets are
    pairwise disjoint.
  * "no fold-total-floor suppression" law intact.
"""
import datetime as dt
import unittest

from futbt.calendarx import WeekdayCalendar
from futbt.taxonomy import PolicyError
from futbt.walkforward import (DroppedCell, ExposureCell, Fold,
                               WalkForwardPlanner)


def sessions_h1_2026():
    return WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 6, 30)).sessions()


def coowner_planner():
    return WalkForwardPlanner(sessions_h1_2026(), true_horizon_sessions=2,
                              embargo_sessions=0)


def all_cells(sessions):
    return [ExposureCell("ES", s) for s in sessions]


class TestCoOwnerCase(unittest.TestCase):
    """The exact reproduction case from the review dispatch."""

    def setUp(self):
        self.p = coowner_planner()
        self.folds = self.p.plan(n_folds=4, train_frac=0.7)
        self.f1 = self.folds[0]
        self.cells = all_cells(self.p.sessions)

    def test_fold1_planned_window_matches_review_numbers(self):
        # 129 weekday sessions; fold1: train_end May 7, test May 8 - May 20.
        self.assertEqual(len(self.p.sessions), 129)
        self.assertEqual(self.f1.train_end, dt.date(2026, 5, 7))
        self.assertEqual(self.f1.test_start, dt.date(2026, 5, 8))
        self.assertEqual(self.f1.test_end, dt.date(2026, 5, 20))

    def test_fold1_emitted_test_ends_at_test_end(self):
        # R5: fold1 TEST labels must end at 2026-05-20, NOT run to Jun 30.
        train, test = self.p.apply_purge_embargo(self.f1, self.cells)
        excess = [c for c in test if c.session > self.f1.test_end]
        self.assertEqual(
            excess, [],
            "test cells past the fold's test_end leak post-test data into "
            f"this fold's evaluation: {len(excess)} excess sessions, last "
            f"{max((c.session for c in excess), default=None)}")
        self.assertEqual(min(c.session for c in test), dt.date(2026, 5, 8))
        self.assertEqual(max(c.session for c in test), dt.date(2026, 5, 18))
        self.assertEqual(len(test), 7)  # May 8..May 18 (May 19/20 censored)

    def test_fold1_exact_split_counts(self):
        train, test = self.p.apply_purge_embargo(self.f1, self.cells)
        self.assertEqual(len(train), 90)      # sessions 0..89 (index)
        self.assertEqual(len(test), 7)
        by_reason = {}
        for d in self.f1.dropped:
            by_reason[(d.phase, d.reason)] = by_reason.get(
                (d.phase, d.reason), 0) + 1
        self.assertEqual(by_reason.get(("train", "PURGE")), 1)          # May 7
        self.assertEqual(by_reason.get(("test", "LABEL_CENSORED")), 2)  # 19/20
        self.assertEqual(by_reason.get(("out_of_fold", "POST_TEST_WINDOW")),
                         29)  # May 21 - Jun 30 excluded from fold1
        # every input cell is accounted for exactly once
        self.assertEqual(len(train) + len(test) + len(self.f1.dropped),
                         len(self.cells))

    def test_no_emitted_overlap_between_folds(self):
        sets = []
        for f in self.folds:
            _, test = self.p.apply_purge_embargo(f, self.cells)
            sets.append(set(c.session for c in test))
        for i in range(len(sets)):
            for j in range(i + 1, len(sets)):
                self.assertEqual(
                    sets[i] & sets[j], set(),
                    f"emitted test cells overlap between fold{i + 1} and "
                    f"fold{j + 1}: {sorted(sets[i] & sets[j])}")


class TestLabelMaturity(unittest.TestCase):
    def test_test_labels_never_extend_past_test_end(self):
        p = coowner_planner()
        folds = p.plan(n_folds=4, train_frac=0.7)
        cells = all_cells(p.sessions)
        pos = {d: i for i, d in enumerate(p.sessions)}
        for f in folds:
            _, test = p.apply_purge_embargo(f, cells)
            te = pos[f.test_end]
            for c in test:
                self.assertLessEqual(
                    pos[c.session] + f.true_horizon_sessions, te,
                    f"kept test cell {c.session} in {f.fold_id} has a label "
                    "window extending past the fold's legal boundary "
                    f"{f.test_end} — censor it, never truncate it")
            censored = [d for d in f.dropped
                        if d.phase == "test" and d.reason == "LABEL_CENSORED"]
            self.assertTrue(
                censored,
                f"{f.fold_id}: the last horizon sessions of the test window "
                "must be censored (their labels need data past test_end)")

    def test_censoring_audited_not_silent(self):
        p = coowner_planner()
        f = p.plan(n_folds=4, train_frac=0.7)[0]
        p.apply_purge_embargo(f, all_cells(p.sessions))
        d = f.to_dict()
        reasons = {row["reason"] for row in d["dropped"]}
        self.assertIn("LABEL_CENSORED", reasons)
        self.assertIn("POST_TEST_WINDOW", reasons)
        self.assertEqual(d["n_dropped"], len(f.dropped))

    def test_last_fold_labels_censored_at_calendar_end(self):
        # the final fold's boundary is the calendar end: its last horizon
        # test cells cannot mature labels either
        p = coowner_planner()
        folds = p.plan(n_folds=4, train_frac=0.7)
        flast = folds[-1]
        _, test = p.apply_purge_embargo(flast, all_cells(p.sessions))
        self.assertEqual(max(c.session for c in test),
                         dt.date(2026, 6, 26))  # Jun 29/30 censored (h=2)
        censored = [d for d in flast.dropped if d.reason == "LABEL_CENSORED"]
        self.assertEqual(len(censored), 2)


class TestTrainPurgeLawIntact(unittest.TestCase):
    def test_purge_boundary_still_enforced(self):
        p = coowner_planner()
        f = p.plan(n_folds=4, train_frac=0.7)[0]
        train, _ = p.apply_purge_embargo(f, all_cells(p.sessions))
        pos = {d: i for i, d in enumerate(p.sessions)}
        last_train = max(c.session for c in train)
        self.assertLessEqual(pos[last_train] + f.purge_sessions,
                             pos[f.test_start])
        purge_drops = [d for d in f.dropped
                       if d.phase == "train" and d.reason == "PURGE"]
        self.assertTrue(purge_drops)

    def test_under_purge_refused_without_side_effects(self):
        p = coowner_planner()
        f = p.plan(n_folds=4, train_frac=0.7)[0]
        bad = Fold(fold_id=f.fold_id, train_start=f.train_start,
                   train_end=f.train_end, test_start=f.test_start,
                   test_end=f.test_end, purge_sessions=1,
                   embargo_sessions=0, true_horizon_sessions=2)
        with self.assertRaisesRegex(PolicyError, "under-purge"):
            p.apply_purge_embargo(bad, all_cells(p.sessions))
        self.assertEqual(
            bad.dropped, [],
            "refusal must happen BEFORE any fold mutation (validation first)")


class TestWindowValidation(unittest.TestCase):
    def _planner(self):
        return coowner_planner()

    def _fold(self, **kw):
        p = self._planner()
        f = p.plan(n_folds=4, train_frac=0.7)[0]
        vals = dict(fold_id=f.fold_id, train_start=f.train_start,
                    train_end=f.train_end, test_start=f.test_start,
                    test_end=f.test_end, purge_sessions=f.purge_sessions,
                    embargo_sessions=0, true_horizon_sessions=2)
        vals.update(kw)
        return Fold(**vals)

    def test_test_end_outside_calendar_refused(self):
        p = self._planner()
        f = self._fold(test_end=dt.date(2026, 7, 31))
        with self.assertRaisesRegex(PolicyError, "test_end"):
            p.apply_purge_embargo(f, all_cells(p.sessions))

    def test_inverted_test_window_refused(self):
        p = self._planner()
        f = self._fold(test_end=dt.date(2026, 5, 7))  # < test_start
        with self.assertRaisesRegex(PolicyError, "test_end"):
            p.apply_purge_embargo(f, all_cells(p.sessions))

    def test_train_end_not_before_test_start_refused(self):
        p = self._planner()
        f = self._fold(train_end=dt.date(2026, 5, 20))  # == test_end
        with self.assertRaisesRegex(PolicyError, "train_end"):
            p.apply_purge_embargo(f, all_cells(p.sessions))

    def test_horizon_authority_mismatch_refused(self):
        p = self._planner()
        f = self._fold(true_horizon_sessions=5)  # planner says 2
        with self.assertRaisesRegex(PolicyError, "horizon"):
            p.apply_purge_embargo(f, all_cells(p.sessions))

    def test_pre_window_cells_excluded_and_audited(self):
        p = self._planner()
        f = self._fold(train_start=dt.date(2026, 3, 2))
        cells = all_cells(p.sessions)
        train, test = p.apply_purge_embargo(f, cells)
        pre = [d for d in f.dropped if d.reason == "PRE_WINDOW"]
        self.assertTrue(pre)
        self.assertTrue(all(d.phase == "out_of_fold" for d in pre))
        kept = {c.session for c in train} | {c.session for c in test}
        self.assertTrue(all(d.cell.session < f.train_start for d in pre))
        self.assertFalse(any(s < f.train_start for s in kept))


class TestNoOverlappingFolds(unittest.TestCase):
    def test_planned_test_windows_disjoint(self):
        p = coowner_planner()
        folds = p.plan(n_folds=4, train_frac=0.7)
        wins = [(f.test_start, f.test_end) for f in folds]
        for i in range(len(wins)):
            for j in range(i + 1, len(wins)):
                self.assertLess(wins[i][1], wins[j][0],
                                f"planned windows overlap: {wins[i]} {wins[j]}")

    def test_validate_no_overlap_raises_on_crafted_overlap(self):
        p = coowner_planner()
        folds = p.plan(n_folds=4, train_frac=0.7)
        WalkForwardPlanner.validate_no_overlap(folds)  # must not raise
        bad = [Fold(fold_id="a", train_start=dt.date(2026, 1, 1),
                    train_end=dt.date(2026, 3, 31),
                    test_start=dt.date(2026, 4, 1),
                    test_end=dt.date(2026, 4, 30), purge_sessions=2,
                    embargo_sessions=0, true_horizon_sessions=2),
               Fold(fold_id="b", train_start=dt.date(2026, 1, 1),
                    train_end=dt.date(2026, 4, 20),
                    test_start=dt.date(2026, 4, 21),
                    test_end=dt.date(2026, 5, 20), purge_sessions=2,
                    embargo_sessions=0, true_horizon_sessions=2)]
        with self.assertRaisesRegex(PolicyError, "overlap"):
            WalkForwardPlanner.validate_no_overlap(bad)

    def test_last_fold_test_reaches_calendar_end(self):
        # windows are gapless and cover through the final session (the last
        # fold's legal boundary is the calendar end); only its final horizon
        # cells are label-censored, none are silently dropped
        p = coowner_planner()
        folds = p.plan(n_folds=4, train_frac=0.7)
        pos = {d: i for i, d in enumerate(p.sessions)}
        for a, b in zip(folds, folds[1:]):
            self.assertEqual(pos[b.test_start], pos[a.test_end] + 1)
        self.assertEqual(folds[-1].test_end, p.sessions[-1])


class TestFoldSuppressionLawIntact(unittest.TestCase):
    def test_performance_drop_still_forbidden(self):
        p = coowner_planner()
        f = p.plan(n_folds=4, train_frac=0.7)[0]
        for reason in ("LOW_TOTAL_RETURN", "NEGATIVE_FOLD_PNL", "TOO_FEW_TRADES"):
            with self.assertRaisesRegex(PolicyError, "performance"):
                p.drop_fold(f, reason, {"metric": -1.0})
        # coverage drop stays legal and is the ONLY legal reason
        p.drop_fold(f, "INSUFFICIENT_COVERAGE", {"n_test_cells": 7})
        self.assertIn("INSUFFICIENT_COVERAGE", f.selection_note)


class TestEmbargoAuditTrail(unittest.TestCase):
    def test_embargo_drops_recorded_per_cell(self):
        p = WalkForwardPlanner(sessions_h1_2026(), true_horizon_sessions=2,
                               embargo_sessions=3)
        f = p.plan(n_folds=1, train_frac=0.7)[0]
        train, test = p.apply_purge_embargo(f, all_cells(p.sessions))
        pos = {d: i for i, d in enumerate(p.sessions)}
        emb = [d for d in f.dropped if d.reason == "EMBARGO"]
        self.assertTrue(emb)
        self.assertTrue(all(d.phase == "test" for d in emb))
        be = pos[f.train_end] + 3
        for d in emb:
            self.assertLessEqual(pos[d.cell.session], be)
            self.assertGreater(pos[d.cell.session], pos[f.train_end])
        first_test = min(c.session for c in test)
        self.assertGreater(pos[first_test] - pos[f.train_end], 3)


if __name__ == "__main__":
    unittest.main()
