#!/usr/bin/env python3
"""A7 prelaunch evidence: exhaustive decision-instant vs reaction-window check.

Recomputes, from bytes only:
 1. all 833 GB+CA clocks in p2_conditioning_clocks_v7.json -> w0/w1 per the
    frozen census semantics; entry = 16:00-NY of the clock's decision_date;
 2. the frozen runner's live decision records (anchor/neighbour/control)
    -> how many entries precede w1 / w0.
No PnL. Read-only.
"""
import sys, json
sys.path.insert(0, '.')
from datetime import datetime, timedelta, timezone, date
from zoneinfo import ZoneInfo
from research.assets.forex_free_v7 import family_a4p1_v7 as F1
from research.assets.forex_free_v7.exec_driver_v7 import DATA_PATHS_REAL

NY = ZoneInfo("America/New_York"); UTC = timezone.utc

def ny_close(day):
    return datetime(day.year, day.month, day.day, 16, tzinfo=NY).astimezone(UTC)

result = {"schema": "forex_free_v7_a7_clock_window_check_v1"}
clocks = F1.load_clocks_v7(DATA_PATHS_REAL['clocks_path'])
gbca = [c for c in clocks if c['economy'] in ('GB','CA')]
viol = []
for c in gbca:
    T = c['event_instant']; w0, w1 = c['w0'], c['w1']
    entry = ny_close(c['decision_date'])
    if entry < w1:
        viol.append({"clock_id": c['clock_id'], "decision_date": str(c['decision_date']),
                     "event_available_time_utc": T.isoformat(), "precision_class": c['precision_class'],
                     "w0": w0.isoformat(), "w1": w1.isoformat(), "entry_instant": entry.isoformat(),
                     "entry_minus_w1_hours": round((entry-w1).total_seconds()/3600.0, 2)})
result["p2_clocks_gb_ca"] = {"n": len(gbca), "entries_before_w1": len(viol),
                             "worst_gap_hours": min(v['entry_minus_w1_hours'] for v in viol) if viol else None,
                             "best_gap_hours": max(v['entry_minus_w1_hours'] for v in viol) if viol else None,
                             "sample_violations": viol[:3]}

clockmap = {c['clock_id']: c for c in clocks}
arms = {}
for arm in ('anchor','neighbour','control'):
    out = F1.run_arm(arm, DATA_PATHS_REAL)
    before_w1 = before_w0 = 0
    for d in out['decisions']:
        c = clockmap[d['clock_id']]
        w0, w1 = c['w0'], c['w1']
        if arm == 'control':
            w0 += timedelta(days=7); w1 += timedelta(days=7)
        e = datetime.fromisoformat(d['entry_ts'])
        before_w1 += (e < w1); before_w0 += (e < w0)
    arms[arm] = {"n_decisions": out['meta']['n_decisions'], "folds": out['meta']['folds'],
                 "entries_before_w1": before_w1, "entries_before_w0": before_w0}
result["frozen_runner_live"] = arms
print(json.dumps(result, indent=1))
json.dump(result, open('research/control/forex_free_v7_run/a7_prelaunch_evidence/a7_clock_window_check.json','w'), indent=1)
