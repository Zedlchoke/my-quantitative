"""Walk-forward scaffolding: exposure calendar, nested TRAIN selection,
purge/embargo by true horizon, deterministic replay, mutation test hooks.

Rules enforced (not configurable away silently):
  * purge >= TRUE HORIZON (in sessions). The horizon is the label window —
    e.g. a k-session hold with entry delay d has horizon k + d. Under-purging
    raises PolicyError; there is no silent default.
  * PER-WINDOW INTEGRITY (review R5 fix, 2026-10-02): a fold evaluates only
    cells inside [train_start, test_end]. Cells past test_end never enter
    the fold's evaluation (recorded out_of_fold/POST_TEST_WINDOW) — the
    fold's test window ENDS where the plan says it ends, so post-test data
    cannot leak into this fold and folds cannot overlap in emitted cells.
  * LABEL MATURITY: a label at session t needs `true_horizon_sessions` of
    future data. Test cells whose label window extends past the fold's
    legal boundary (test_end) are dropped/censored with an audited reason
    (LABEL_CENSORED) — never silently truncated, never evaluated on data
    past the boundary. The same law applies to the last fold at the
    calendar end.
  * NO OVERLAPPING FOLDS: plan() validates that test windows are pairwise
    disjoint (WalkForwardPlanner.validate_no_overlap); the final fold's
    test window is extended to the calendar end so windows are gapless
    (coverage completion — never a performance-based change).
  * folds are NEVER dropped for performance reasons ("no fold-total-floor
    suppression"). The only legal drop reason is INSUFFICIENT_COVERAGE,
    recorded per fold with the coverage numbers.
  * selection happens ONLY inside TRAIN via a selector callback that
    receives a PIT view pinned at TRAIN end; the selected params are frozen
    and stamped into the fold before TEST runs.
  * the planner is the single horizon authority: a Fold whose
    true_horizon_sessions differs from the planner's is refused (a
    mismatched horizon could silently under-censor labels).
  * window validation happens BEFORE any fold mutation: a refused fold is
    left untouched (no partially-appended drop records).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from .taxonomy import PolicyError

ALLOWED_DROP_REASONS = {"INSUFFICIENT_COVERAGE"}


@dataclass(frozen=True)
class ExposureCell:
    symbol: str
    session: dt.date
    weight: float = 1.0


@dataclass
class DroppedCell:
    cell: ExposureCell
    phase: str          # 'train' | 'test' | 'out_of_fold'
    reason: str         # 'PURGE' | 'EMBARGO' | 'LABEL_CENSORED' |
                        # 'PRE_WINDOW' | 'POST_TEST_WINDOW' | fold-level
                        # drop reason


@dataclass
class Fold:
    fold_id: str
    train_start: dt.date
    train_end: dt.date
    test_start: dt.date
    test_end: dt.date
    purge_sessions: int
    embargo_sessions: int
    true_horizon_sessions: int
    dropped: list[DroppedCell] = field(default_factory=list)
    selected_params: dict | None = None
    selection_asof: dt.date | None = None
    selection_note: str = ""

    def to_dict(self) -> dict:
        return {
            "fold_id": self.fold_id,
            "train_start": self.train_start.isoformat(),
            "train_end": self.train_end.isoformat(),
            "test_start": self.test_start.isoformat(),
            "test_end": self.test_end.isoformat(),
            "purge_sessions": self.purge_sessions,
            "embargo_sessions": self.embargo_sessions,
            "true_horizon_sessions": self.true_horizon_sessions,
            "n_dropped": len(self.dropped),
            "dropped": [
                {"cell": f"{d.cell.symbol}@{d.cell.session}", "phase": d.phase,
                 "reason": d.reason} for d in self.dropped],
            "selected_params": self.selected_params,
            "selection_asof": (self.selection_asof.isoformat()
                               if self.selection_asof else None),
            "selection_note": self.selection_note,
        }


class WalkForwardPlanner:
    def __init__(self, sessions: list[dt.date], true_horizon_sessions: int,
                 embargo_sessions: int = 0):
        if true_horizon_sessions < 1:
            raise PolicyError("true horizon must be >= 1 session (label window)")
        if embargo_sessions < 0:
            raise ValueError("embargo_sessions >= 0")
        self.sessions = sorted(sessions)
        self.horizon = int(true_horizon_sessions)
        self.embargo = int(embargo_sessions)

    def plan(self, n_folds: int, train_frac: float = 0.7) -> list[Fold]:
        """Anchored-expanding folds over the session list."""
        if n_folds < 1:
            raise ValueError("n_folds >= 1")
        if not (0.1 <= train_frac <= 0.95):
            raise ValueError("train_frac out of range")
        n = len(self.sessions)
        test_len = max(1, int(n * (1.0 - train_frac) / n_folds))
        folds: list[Fold] = []
        idx = 0
        for k in range(n_folds):
            train_end_idx = int(n * train_frac) + k * test_len
            test_start_idx = train_end_idx + 1
            test_end_idx = min(test_start_idx + test_len - 1, n - 1)
            if test_start_idx > n - 1 or train_end_idx >= n:
                break
            folds.append(Fold(
                fold_id=f"fold{k + 1:02d}",
                train_start=self.sessions[idx],
                train_end=self.sessions[train_end_idx],
                test_start=self.sessions[test_start_idx],
                test_end=self.sessions[test_end_idx],
                purge_sessions=self.horizon,
                embargo_sessions=self.embargo,
                true_horizon_sessions=self.horizon,
            ))
        if not folds:
            raise PolicyError("session list too short for the requested folds")
        # NO-overlap law: test windows must be pairwise disjoint.
        self.validate_no_overlap(folds)
        # coverage completion: the FINAL fold's legal boundary is the
        # calendar end — extend its test window so the fold test windows are
        # gapless. This is coverage arithmetic only, never performance-based.
        last = folds[-1]
        if last.test_end < self.sessions[-1]:
            last.test_end = self.sessions[-1]
            last.selection_note += (" | final-fold test window extended to "
                                    "calendar end (coverage completion)")
        return folds

    @staticmethod
    def validate_no_overlap(folds: list[Fold]) -> None:
        """Raise PolicyError if any two folds' test windows overlap
        (the emitted cell sets could then double-evaluate sessions)."""
        windows = sorted((f.test_start, f.test_end, f.fold_id) for f in folds)
        for (s1, e1, id1), (s2, e2, id2) in zip(windows, windows[1:]):
            if s2 <= e1:
                raise PolicyError(
                    f"test windows of {id1} [{s1}..{e1}] and {id2} "
                    f"[{s2}..{e2}] overlap — NO overlapping folds is a "
                    "hard law (double evaluation of the same sessions)")

    # ------------------------------------------------------------------ #
    def apply_purge_embargo(self, fold: Fold,
                            cells: list[ExposureCell]) -> tuple[list, list]:
        """Split exposure cells into (train, test) with per-window integrity.

        The fold evaluates ONLY cells inside [train_start, test_end]:
        - TRAIN cells whose label window would reach into TEST (purge):
          any train cell with session > test_start - horizon sessions;
        - TEST cells starting within embargo sessions after TRAIN end;
        - TEST cells whose label window (session + true horizon) extends
          past the fold's legal boundary test_end are CENSORED
          (LABEL_CENSORED): the label cannot mature inside the fold, so it
          is dropped from evaluation — never truncated silently, never
          computed on data past the boundary;
        - cells outside the window (before train_start, past test_end) are
          excluded from this fold and audited (out_of_fold) — POST_TEST
          cells belong to later folds and must not leak into this one.
        Every drop is recorded in fold.dropped with its reason. The window
        is validated BEFORE any mutation: a refused fold is left untouched.
        """
        # ---- validation first (no partial side effects on refusal) ----- #
        if fold.purge_sessions < self.horizon:
            raise PolicyError(
                f"fold {fold.fold_id}: purge ({fold.purge_sessions}) < true "
                f"horizon ({self.horizon}) — silent under-purge forbidden")
        if fold.true_horizon_sessions != self.horizon:
            raise PolicyError(
                f"fold {fold.fold_id}: true_horizon_sessions "
                f"({fold.true_horizon_sessions}) != planner horizon "
                f"({self.horizon}) — the planner is the single horizon "
                "authority; a mismatched horizon could silently under-censor")
        s = self.sessions
        pos = {d: i for i, d in enumerate(s)}
        for name, d in (("train_start", fold.train_start),
                        ("train_end", fold.train_end),
                        ("test_start", fold.test_start),
                        ("test_end", fold.test_end)):
            if d not in pos:
                raise PolicyError(
                    f"fold {fold.fold_id}: {name} {d} not in session list — "
                    "per-window integrity cannot be enforced")
        train_end_i = pos[fold.train_end]
        test_start_i = pos[fold.test_start]
        test_end_i = pos[fold.test_end]
        if train_end_i >= test_start_i:
            raise PolicyError(
                f"fold {fold.fold_id}: train_end {fold.train_end} must be "
                f"strictly before test_start {fold.test_start}")
        if test_end_i < test_start_i:
            raise PolicyError(
                f"fold {fold.fold_id}: test_end {fold.test_end} must not "
                f"precede test_start {fold.test_start}")
        # ---- per-cell classification ----------------------------------- #
        purge_boundary_i = test_start_i - fold.purge_sessions
        embargo_boundary_i = train_end_i + fold.embargo_sessions
        train: list[ExposureCell] = []
        test: list[ExposureCell] = []
        for c in cells:
            if c.session not in pos:
                continue
            ci = pos[c.session]
            if ci > test_end_i:
                fold.dropped.append(DroppedCell(c, "out_of_fold",
                                                "POST_TEST_WINDOW"))
            elif c.session < fold.train_start:
                fold.dropped.append(DroppedCell(c, "out_of_fold",
                                                "PRE_WINDOW"))
            elif c.session <= fold.train_end:
                if ci > purge_boundary_i:
                    fold.dropped.append(DroppedCell(c, "train", "PURGE"))
                else:
                    train.append(c)
            else:
                if ci <= embargo_boundary_i:
                    fold.dropped.append(DroppedCell(c, "test", "EMBARGO"))
                elif ci + fold.true_horizon_sessions > test_end_i:
                    fold.dropped.append(DroppedCell(c, "test",
                                                    "LABEL_CENSORED"))
                else:
                    test.append(c)
        return train, test

    # ------------------------------------------------------------------ #
    def drop_fold(self, fold: Fold, reason: str, coverage: dict) -> None:
        if reason not in ALLOWED_DROP_REASONS:
            raise PolicyError(
                f"fold drop reason '{reason}' not allowed. Only "
                f"{sorted(ALLOWED_DROP_REASONS)} are legal; performance-based "
                "fold suppression is forbidden")
        fold.selection_note += (f" | DROPPED ({reason}) coverage={coverage}")

    # ------------------------------------------------------------------ #
    def run_selection(self, fold: Fold, selector, pit_view_at_train_end) -> dict:
        """Nested TRAIN selection: selector sees only a view pinned at
        train_end. Selected params are frozen and stamped on the fold."""
        params = selector(pit_view_at_train_end)
        if not isinstance(params, dict):
            raise PolicyError("selector must return a dict of frozen params")
        fold.selected_params = {k: v for k, v in params.items()}
        fold.selection_asof = fold.train_end
        fold.selection_note += " | params frozen at train_end (PIT view)"
        return fold.selected_params


def replay_deterministic(folds: list[Fold], runner, seed: int = 0
                         ) -> list[dict]:
    """Deterministic fold replay: `runner(fold, phase, seed)` must be pure.
    The same (folds, runner, seed) must always produce identical output."""
    out = []
    for f in folds:
        out.append({
            "fold": f.fold_id,
            "train": runner(f, "train", seed),
            "test": runner(f, "test", seed),
            "fold_dict": f.to_dict(),
        })
    return out


# --------------------------------------------------------------------- #
def assert_prefix_determinism(full_output, truncated_output, cutoff: dt.date,
                              key: str = "decisions") -> None:
    """Truncation hook: replay outputs must agree on every session <= cutoff."""
    a = [d for d in full_output.get(key, []) if d["session"] <= cutoff.isoformat()]
    b = [d for d in truncated_output.get(key, [])
         if d["session"] <= cutoff.isoformat()]
    if a != b:
        raise AssertionError(
            f"prefix determinism violated at cutoff {cutoff}: decisions up to "
            "the cutoff differ between full and truncated runs (look-ahead)")


def assert_future_mutation_invariance(base_output, mutated_output,
                                      cutoff: dt.date,
                                      key: str = "decisions") -> None:
    """Future-mutation hook: garbage data after cutoff must not change any
    decision at or before cutoff."""
    a = [d for d in base_output.get(key, []) if d["session"] <= cutoff.isoformat()]
    b = [d for d in mutated_output.get(key, [])
         if d["session"] <= cutoff.isoformat()]
    if a != b:
        raise AssertionError(
            f"future-mutation invariance violated at cutoff {cutoff}: "
            "decisions depend on data strictly after the decision date")
