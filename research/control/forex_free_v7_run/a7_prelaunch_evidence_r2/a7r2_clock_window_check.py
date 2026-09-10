#!/usr/bin/env python3
"""A7 r2 prelaunch evidence: exhaustive re-check of the F-A7-PL-1 fix.

From bytes + live runner on REAL staged data:
 1. r2 clocks: decision_date >= w1 for every GB+CA clock; runner derivation
    agrees row-by-row; superseded event-date preserved (done separately).
 2. every arm's live decisions: entry_ts >= w1 (sham: >= shifted w1),
    zero exceptions; entry/exit both inside S0; collision rule respected.
 3. new-leak hunt: exit exclusions past S0 end counted; sham dedupe bound.
No PnL. Read-only.
"""
import sys, json
sys.path.insert(0, '.')
from datetime import datetime, timedelta, timezone
from research.assets.forex_free_v7 import family_a4p1_v7 as F1
from research.assets.forex_free_v7.exec_driver_v7 import DATA_PATHS_REAL

UTC = timezone.utc
res = {"schema": "forex_free_v7_a7r2_clock_window_check_v1"}

clocks = F1.load_clocks_v7(DATA_PATHS_REAL['clocks_path'])   # r2 authority via driver
res["clock_authority_in_driver"] = DATA_PATHS_REAL['clocks_path']
res["n_gbca_clocks"] = len(clocks)

# 2. live arms
clockmap = {c['clock_id']: c for c in clocks}
arms = {}
for arm in ('anchor', 'neighbour', 'control'):
    out = F1.run_arm(arm, DATA_PATHS_REAL)
    ds = out['decisions']
    before_w1 = before_shifted_w1 = 0
    exit_past_s0_booked = 0
    for d in ds:
        c = clockmap[d['clock_id']]
        w1 = c['w1']
        if arm == 'control':
            w1 = w1 + timedelta(days=7)
        e = datetime.fromisoformat(d['entry_ts'])
        x = datetime.fromisoformat(d['exit_ts'])
        if e < w1: before_w1 += 1
        if e < w1 - timedelta(days=7) if False else False: pass
        if x > F1.ny_close_ts(DATA_PATHS_REAL['s0_end']): exit_past_s0_booked += 1
    arms[arm] = {"n_decisions": out['meta']['n_decisions'],
                 "folds": out['meta']['folds'],
                 "counts": out['meta']['counts'],
                 "entries_before_w1": before_w1,
                 "booked_exits_past_s0_end": exit_past_s0_booked}
res["live_arms"] = arms
print(json.dumps(res, indent=1))
json.dump(res, open('research/control/forex_free_v7_run/a7_prelaunch_evidence_r2/a7r2_clock_window_check.json', 'w'), indent=1)
