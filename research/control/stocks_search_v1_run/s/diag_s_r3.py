#!/usr/bin/env python3
"""DIAGNOSTIC (ssearch-s-r3) — bounded-sample root-cause for the
state_totals_equal_p0_census_all_47 FAIL (n_ok=0/47, run_log_s_r3.txt).

Three counting paths on ONE deterministic bounded sample (<=500 names):
  A  FROZEN ENGINE PATH: p0_run.run_census(sub_pulls) invoked read-only on
     the sample — the exact code that produced p0_census.json.
  B  CENSUS-SPACE REPLICATION per state: full served history, warm gate in
     full-history index space, fold assignment by decision DATE (L.assign_fold),
     med60 over the FULL history — the semantics A implements per config.
  C  CURRENT s_select TRIM SPACE: bars mapped onto the SPY window calendar,
     off-calendar/out-of-window bars DROPPED first, med60 recomputed on the
     trimmed arrays, warm gate in trimmed index space, no fold assignment.

Questions answered:
  Q1  B == A per state per fold EXACT?      (is B a faithful census replica)
  Q2  C - B per state: constant offset / ratio / sign?   (characterize delta)
  Q3  data recon: how many sample names carry bars after WINDOW_END, before
      WINDOW_START, or off the SPY calendar within the window?

Read-only on p0/ and the cache; writes nothing outside s/.
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


L = load_module("p0_lib_diag", P0 / "p0_lib.py")
R = load_module("p0_run_diag", P0 / "p0_run.py")

# ------------------------------------------------------------------ sample
retrieval = json.loads((P0 / "retrieval_manifest.json").read_text())
pulls = retrieval["pulls"]
CACHE = R.CACHE
names = sorted(s for s, m in pulls.items()
               if m.get("status") == 200 and (CACHE / f"{s}.json.gz").exists())
force = [s for s in ("SPY", "QQQ", "AAPL", "^MGTN", "^TNX", "^W5000")
         if s in names]
rest = [s for s in names if s not in force]
rng = random.Random(20260918)
sample = sorted(force + rest[:150] + rng.sample(rest[150:], 149))
assert len(sample) <= 500
print(f"sample n={len(sample)} (cohort {len(names)})", flush=True)

# ------------------------------------------------------------------- state map (from s_select)
def warmup_from_params(family, params):
    W = 252
    if family == "EVENT-UNWIND":
        return max(W, params["K"])
    if family == "GAP":
        return W
    if family == "52W-HIGH":
        return W
    if family == "CLV-RANGE":
        return max(W, 20 - 1 + params["k"])
    if family == "DVOL-SHOCK":
        return W
    if family == "VOL-REGIME":
        return max(W, W - 1 + params["L"])
    raise ValueError(family)


cfgs = L.enumerate_configs()
state_key_of = {}
warmup_of = {}
state_cfg = {}
for c in cfgs:
    key = (c["family"],
           tuple(sorted((k, v) for k, v in c["params"].items() if k != "H")))
    state_key_of[c["config_id"]] = key
    warmup_of[key] = warmup_from_params(c["family"], c["params"])
    state_cfg.setdefault(key, {"config_id": c["config_id"],
                               "family": c["family"],
                               "params": {k: v for k, v in c["params"].items()
                                          if k != "H"}})
    assert warmup_of[key] == c["warmup_need"], c["config_id"]
b1, b2 = L.fold_boundaries()
FCODE = {"F1": 0, "F2": 1, "F3": 2}
print(f"fold boundaries B1={b1} B2={b2}; states={len(state_cfg)}", flush=True)

# ---------------------------------------------------------------- calendar (as s_select)
spy_rows = json.loads(gzip.open(CACHE / "SPY.json.gz", "rt").read())
spy_dates = sorted(str(r["date"])[:10] for r in spy_rows
                   if r.get("date") is not None)
cal = [d for d in spy_dates if WINDOW_START <= d <= WINDOW_END]
cal_arr = np.array(cal, dtype="<U10")
ncal = len(cal)
print(f"calendar sessions={ncal} [{cal[0]}..{cal[-1]}]", flush=True)

# ------------------------------------------------------------------ paths
sub_pulls = {s: pulls[s] for s in sample}
print("path A: frozen p0_run.run_census on sample ...", flush=True)
resA = R.run_census(sub_pulls)
rowsA = resA["summary"]["per_config_per_fold"]
A = {}  # (state_key, fold) -> [fired, bookable]
for r in rowsA:
    k = state_key_of[r["config_id"]]
    cell = A.setdefault((k, r["fold"]), [0, 0])
    cell[0] += r["fired"]
    cell[1] += r["bookable_fired"]

B = {k: {f: [0, 0] for f in ("F1", "F2", "F3")} for k in state_cfg}
Btot = {k: 0 for k in state_cfg}
Bbook = {k: 0 for k in state_cfg}
C = {k: [0, 0] for k in state_cfg}
recon = {"names": 0, "names_post_window_bars": 0, "names_pre_window_bars": 0,
         "names_offcal_bars": 0, "post_window_bars": 0, "pre_window_bars": 0,
         "offcal_bars": 0}

for i_sym, sym in enumerate(sample, 1):
    parsed = R.parse_name(CACHE / f"{sym}.json.gz")
    if parsed is None:
        continue
    dates, o, h, lo, c, v, _mal = parsed
    if len(dates) < 3:
        continue
    recon["names"] += 1
    darr = np.array([d[:10] for d in dates], dtype="<U10")
    n_post = int((darr > WINDOW_END).sum())
    n_pre = int((darr < WINDOW_START).sum())
    ins = np.searchsorted(cal_arr, darr)
    vic = np.clip(ins, 0, ncal - 1)
    valid = cal_arr[vic] == darr
    n_off = int((~valid).sum())
    if n_post:
        recon["names_post_window_bars"] += 1
        recon["post_window_bars"] += n_post
    if n_pre:
        recon["names_pre_window_bars"] += 1
        recon["pre_window_bars"] += n_pre
    if n_off:
        recon["names_offcal_bars"] += 1
        recon["offcal_bars"] += n_off

    # ---- path B: census space (full history, fold by date)
    n = len(dates)
    fold_code = np.empty(n, dtype=np.int8)
    for i, d in enumerate(dates):
        fold_code[i] = FCODE[L.assign_fold(d, b1, b2)]
    med60_all = L._rolling_median(c * v, L.DVOL_WINDOW)
    for key, scfg in state_cfg.items():
        fired, bookable, _ = L.run_config_census(scfg, o, h, lo, c, v,
                                                 med60=med60_all)
        fi_all = np.nonzero(fired)[0]
        fi = fi_all[fi_all >= warmup_of[key]]
        Btot[key] += int(fi.size)
        Bbook[key] += int(np.count_nonzero(bookable[fi]))
        for fc, f in enumerate(("F1", "F2", "F3")):
            m = fi[fold_code[fi] == fc]
            B[key][f][0] += int(m.size)
            B[key][f][1] += int(np.count_nonzero(bookable[m]))

    # ---- path C: current s_select trim space
    keep = np.nonzero(valid)[0]
    o2, h2, lo2, c2, v2 = o[keep], h[keep], lo[keep], c[keep], v[keep]
    med60_trim = L._rolling_median(c2 * v2, L.DVOL_WINDOW)
    for key, scfg in state_cfg.items():
        fired, bookable, _ = L.run_config_census(scfg, o2, h2, lo2, c2, v2,
                                                 med60=med60_trim)
        fi_all = np.nonzero(fired)[0]
        fi = fi_all[fi_all >= warmup_of[key]]
        fb = fi[bookable[fi]]
        C[key][0] += int(fi.size)
        C[key][1] += int(fb.size)
    if i_sym % 50 == 0:
        print(f"  ... {i_sym}/{len(sample)}", flush=True)

# ------------------------------------------------------------------ report
q1_bad = []
for (k, f), (af, ab) in sorted(A.items(), key=lambda kv: str(kv[0])):
    bf, bb = B[k][f]
    if af != bf or ab != bb:
        q1_bad.append({"state": f"{k[0]}|{json.dumps(k[1], sort_keys=True)}",
                       "fold": f, "A_fired": af, "B_fired": bf,
                       "A_bookable": ab, "B_bookable": bb})
print("\nQ1 B-vs-A (frozen engine) per state/fold EXACT:",
      "YES" if not q1_bad else f"NO ({len(q1_bad)} mismatches)")
for row in q1_bad[:10]:
    print("   ", row)

print("\nQ2 C-vs-B per state (trimmed-space drift):")
print(f"{'state':60s} {'B_fired':>9s} {'C_fired':>9s} {'d_fired':>8s} "
      f"{'B_book':>9s} {'C_book':>9s} {'d_book':>8s}")
tot_b = tot_c = tot_bb = tot_cb = 0
for k in sorted(Btot, key=str):
    bf, cf = Btot[k], C[k][0]
    bb, cb = Bbook[k], C[k][1]
    tot_b += bf; tot_c += cf; tot_bb += bb; tot_cb += cb
    print(f"{(k[0] + '|' + json.dumps(k[1], sort_keys=True))[:60]:60s} "
          f"{bf:9d} {cf:9d} {cf - bf:8d} {bb:9d} {cb:9d} {cb - bb:8d}")
print(f"{'TOTAL':60s} {tot_b:9d} {tot_c:9d} {tot_c - tot_b:8d} "
      f"{tot_bb:9d} {tot_cb:9d} {tot_cb - tot_bb:8d}")

print("\nQ3 sample data recon:", json.dumps(recon, indent=1))

# frozen cohort totals for scale (per state via hold-invariant fired rows)
p0c = json.loads((P0 / "p0_census.json").read_text())
fro = {}
for r in p0c["per_config_per_fold"]:
    k = state_key_of[r["config_id"]]
    cell = fro.setdefault(k, [0, 0])
    cell[0] += r["fired"]
    cell[1] += r["bookable_fired"]
print("\nfrozen cohort totals (first 6 states, for scale):")
for k in sorted(fro, key=str)[:6]:
    print(f"   {k[0]}|{json.dumps(k[1], sort_keys=True)[:40]:42s} "
          f"fired={fro[k][0]:9d} bookable={fro[k][1]:9d}")

out = {"sample_n": len(sample), "q1_mismatches": q1_bad,
       "recon": recon,
       "per_state": {f"{k[0]}|{json.dumps(k[1], sort_keys=True)}":
                     {"B_fired": Btot[k], "C_fired": C[k][0],
                      "B_bookable": Bbook[k], "C_bookable": C[k][1]}
                     for k in sorted(Btot, key=str)}}
(S_DIR / "diag_s_r3_result.json").write_text(json.dumps(out, indent=1) + "\n")
print("\nwrote diag_s_r3_result.json", flush=True)
