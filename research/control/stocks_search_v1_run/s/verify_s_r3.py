#!/usr/bin/env python3
"""SAMPLE VERIFY (ssearch-s-r3, step 3) — the FIXED s_select.heavy_pass
production code, invoked directly on the bounded 305-name sample, must
reproduce the frozen p0_run.run_census per-config per-fold cells EXACTLY
(same 305 names), and two pooled position series must match an independent
naive per-name recomputation (validates the bincount accumulation fix).

Run: python verify_s_r3.py  -> exits 0 iff every cell matches EXACTLY.
"""
from __future__ import annotations

import gzip
import importlib.util
import json
import random
import sys
from pathlib import Path

import numpy as np

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
          "stocks-search-v1/integration")
P0 = WT / "research/control/stocks_search_v1_run/p0"
S_DIR = WT / "research/control/stocks_search_v1_run/s"
WINDOW_START, WINDOW_END = "2015-01-02", "2026-09-16"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


L = load_module("p0_lib_v", P0 / "p0_lib.py")
R = load_module("p0_run_v", P0 / "p0_run.py")
S = load_module("s_select_v", S_DIR / "s_select.py")

# ---- sample (identical construction to diag_s_r3.py)
retrieval = json.loads((P0 / "retrieval_manifest.json").read_text())
pulls = retrieval["pulls"]
names = sorted(s for s, m in pulls.items()
               if m.get("status") == 200 and (R.CACHE / f"{s}.json.gz").exists())
force = [s for s in ("SPY", "QQQ", "AAPL", "^MGTN", "^TNX", "^W5000")
         if s in names]
rest = [s for s in names if s not in force]
rng = random.Random(20260918)
sample = sorted(force + rest[:150] + rng.sample(rest[150:], 149))
sub_pulls = {s: pulls[s] for s in sample}
print(f"sample n={len(sample)}", flush=True)

manifest = json.loads((WT / "research/control/stocks_search_v1_run/d1/"
                       "search_space_manifest.json").read_text())
p0_census = json.loads((P0 / "p0_census.json").read_text())

# ---- frozen engine path on the SAME sample
print("frozen engine path: p0_run.run_census(sample) ...", flush=True)
rowsA = R.run_census(sub_pulls)["summary"]["per_config_per_fold"]
A = {(r["config_id"], r["fold"]): (r["fired"], r["bookable_fired"])
     for r in rowsA}

# ---- calendar identical to s_select.build_calendar
spy_rows = json.loads(gzip.open(R.CACHE / "SPY.json.gz", "rt").read())
spy_dates = sorted(str(r["date"])[:10] for r in spy_rows
                   if r.get("date") is not None)
calendar = [d for d in spy_dates if WINDOW_START <= d <= WINDOW_END]
print(f"calendar {len(calendar)} sessions", flush=True)


class StubChecks:
    def __init__(self):
        self.rows = []

    def add(self, check_id, ok, detail):
        self.rows.append((check_id, ok, detail))
        return ok


pass_result = S.heavy_pass(L, R, manifest, p0_census,
                           {"pulls": sub_pulls}, calendar, StubChecks())
sff = pass_result["state_fired_fold"]
sbf = pass_result["state_bookable_fold"]

state_key_of, _ = S.state_maps(manifest)
bad = []
for cfg in manifest["configs"]:
    cid = cfg["config_id"]
    key = state_key_of[cid]
    for fold in ("F1", "F2", "F3"):
        want_f, want_b = A[(cid, fold)]
        got_f, got_b = sff[key][fold], sbf[key][fold]
        if (got_f, got_b) != (want_f, want_b):
            bad.append({"config": cid, "fold": fold, "want": (want_f, want_b),
                        "got": (got_f, got_b)})
print(f"census cells vs frozen engine on sample: "
      f"{len(manifest['configs']) * 3 - len(bad)}/{len(manifest['configs']) * 3} EXACT")
for r in bad[:8]:
    print("   MISMATCH", r)

# ---- independent naive recomputation of TWO pooled series (bincount check)
CHECK_CIDS = ["SSS-52W-HIGH-B10-H20", "SSS-GAP-P75-FADE-H1"]
cfg_by_id = {c["config_id"]: c for c in manifest["configs"]}
cal_idx = {d: i for i, d in enumerate(calendar)}
naive = {cid: np.zeros(len(calendar), dtype=np.int64) for cid in CHECK_CIDS}
for sym in sample:
    parsed = R.parse_name(R.CACHE / f"{sym}.json.gz")
    if parsed is None:
        continue
    dates, o, h, lo, c, v, _mal = parsed
    if len(dates) < 3:
        continue
    n = len(dates)
    for cid in CHECK_CIDS:
        cfg = dict(cfg_by_id[cid])
        hold = int(cfg["params"]["H"])
        spcfg = {"config_id": cid, "family": cfg["family"],
                 "params": {k: vv for k, vv in cfg["params"].items()
                            if k != "H"}}
        med60 = L._rolling_median(c * v, L.DVOL_WINDOW)
        fired, bookable, _ = L.run_config_census(spcfg, o, h, lo, c, v,
                                                 med60=med60)
        fi = np.nonzero(fired)[0]
        fi = fi[fi >= S.warmup_from_params(cfg["family"], cfg["params"])]
        fb = fi[bookable[fi]]
        holding = set()
        for t in fb:
            if t + hold <= n - 1:
                holding.update(range(int(t) + 1, int(t) + hold + 1))
        for i in holding:
            d = dates[i][:10]
            j = cal_idx.get(d)
            if j is not None:
                naive[cid][j] += 1
for cid in CHECK_CIDS:
    same = bool(np.array_equal(naive[cid], pass_result["pooled"][cid]))
    nz = int(np.count_nonzero(naive[cid]))
    print(f"pooled series naive-vs-heavy_pass {cid}: "
          f"{'EXACT' if same else 'DIFFER'} (nonzero days {nz})")
    if not same:
        diff = np.nonzero(naive[cid] != pass_result["pooled"][cid])[0][:5]
        for j in diff:
            print(f"   day {calendar[j]} naive={naive[cid][j]} "
                  f"heavy={pass_result['pooled'][cid][j]}")
        bad.append({"config": cid, "check": "pooled_series"})

print("\nVERDICT:", "PASS — sample-verify EXACT" if not bad
      else f"FAIL ({len(bad)} problems)")
sys.exit(0 if not bad else 1)
