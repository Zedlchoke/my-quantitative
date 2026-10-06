"""A7-R2 independent reproduction/verification of co-owner finding R5
(walkforward fold-window integrity).

Co-owner case: weekday calendar 2026-01-01..2026-06-30 (129 sessions),
4 folds, train_frac 0.7, horizon 2. Fold1 planned test window is
2026-05-08..2026-05-20, so NO emitted TEST cell may exist outside that
window; label-immature cells (ci + horizon > test_end) must be censored,
never silently kept.

At base eae8c3d2 apply_purge_embargo emitted TEST cells through
2026-06-30 (38 cells, 29 excess sessions, 29-session overlap with fold2,
31 label-immature kept).

Run from either checkout's code/ dir with PYTHONPATH set to it.
"""
import datetime as dt
import json
import sys

from futbt.calendarx import WeekdayCalendar
from futbt.walkforward import (ExposureCell, WalkForwardPlanner)

OUT = {"commit_context": sys.argv[1] if len(sys.argv) > 1 else "unspecified"}

cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 6, 30))
sessions = cal.sessions()
HORIZON = 2
planner = WalkForwardPlanner(sessions, true_horizon_sessions=HORIZON,
                             embargo_sessions=1)
folds = planner.plan(n_folds=4, train_frac=0.7)
cells = [ExposureCell(symbol="ES", session=s) for s in sessions]

fold_reports = []
emitted_sets = {}
for f in folds:
    tr, te = planner.apply_purge_embargo(f, cells)
    te_sessions = [c.session for c in te]
    emitted_sets[f.fold_id] = set(te_sessions)
    in_window = [s for s in te_sessions if f.test_start <= s <= f.test_end]
    outside = sorted(s for s in te_sessions if s > f.test_end)
    # label maturity: cell ci needs data through ci+horizon INCLUSIVE
    pos = {d: i for i, d in enumerate(sessions)}
    immature = [s for s in te_sessions
                if pos[s] + HORIZON > pos[f.test_end]]
    drops = {}
    for d in f.dropped:
        key = (d.phase, d.reason)
        drops[key] = drops.get(key, 0) + 1
    fold_reports.append({
        "fold_id": f.fold_id,
        "train": [f.train_start.isoformat(), f.train_end.isoformat()],
        "planned_test": [f.test_start.isoformat(), f.test_end.isoformat()],
        "n_emitted_test": len(te_sessions),
        "emitted_test_range": [min(te_sessions).isoformat(),
                               max(te_sessions).isoformat()] if te_sessions else None,
        "n_outside_test_end": len(outside),
        "outside_sessions_sample": [s.isoformat() for s in outside[:3]] + (
            ["..."] if len(outside) > 3 else []) + [outside[-1].isoformat()
                                                    if outside else None],
        "n_label_immature_kept": len(immature),
        "drops": {f"{k[0]}:{k[1]}": v for k, v in drops.items()},
    })

# pairwise disjointness of emitted TEST sets
overlaps = []
ids = sorted(emitted_sets)
for i in range(len(ids)):
    for jj in range(i + 1, len(ids)):
        inter = emitted_sets[ids[i]] & emitted_sets[ids[jj]]
        if inter:
            overlaps.append({"folds": [ids[i], ids[jj]],
                             "n_shared": len(inter),
                             "sample": sorted(inter)[:3]})

OUT["n_sessions"] = len(sessions)
OUT["folds"] = fold_reports
OUT["pairwise_overlap"] = overlaps
OUT["fold1_r5_base_bug"] = (
    fold_reports and fold_reports[0]["n_outside_test_end"] == 29
)
OUT["fold1_fixed_shape"] = (
    fold_reports and fold_reports[0]["n_emitted_test"] == 7
    and fold_reports[0]["n_outside_test_end"] == 29
    and fold_reports[0]["n_label_immature_kept"] == 0
    and not overlaps
)
print(json.dumps(OUT, indent=1, default=str))
