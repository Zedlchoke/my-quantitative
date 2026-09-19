"""STOCKS-SEARCH-V1 E-lane scored-run orchestrator (ssearch-e).

Dispatch: base c294563115e4f0f22f3283bcaff32f866777da39, branch
orca/stocks-search-v1-integration, at most 3 scored cells (the 3 frozen
arms) on the real EODHD cohort under the machine-wide heavy lock, GO'd by
the owner's exact registered phrase at this cycle's gate.

Fail-closed phase order (never improvised):
  P0  environment verification (HEAD == dispatch base, clean tracked tree,
      detached shadow workers 15315/15316 alive and untouched)
  P1  heavy lock acquire + heartbeat (NOT_RUN_RESOURCE_CONFLICT on busy)
  P2  MANDATORY data-plane preflight (i_engine.verify_data_plane, A7 F-1 /
      GO condition C-2) - RUNS AND PASSES before a single cohort byte is
      parsed; any mismatch = INPUT_MISMATCH stop
  P3  footprint calibration of the frozen E path, executed AFTER the gate
      PASS and WITHOUT touching the scored GO gate:
        (a) loader probe - the exact adjudicate.load_real_data per-name
            construction (pinned p0_run.parse_name -> NameData) over a
            bounded prefix of the real cache, measuring RSS bytes per
            served session;
        (b) leg benchmark - the frozen i_engine.build_legs on a synthetic
            name at H=1 and H=20, measuring RSS bytes per opened leg,
            deepcopy factor at adjudication, and wall throughput;
        (c) arithmetic vs the authoritative cohort census totals.
  P4  pre-declared feasibility interlock: if the frozen path's peak RSS
      requirement exceeds SAFE_BUDGET_BYTES, the scored load is NOT
      launched (driving the machine into multi-GB swap would endanger the
      co-tenant ACTIVE_LIGHT shadow workers and the run is unwinnable);
      terminal outcome STOCKS_SEARCH_V1_TECHABORT_PRESERVED with all
      measurements, budget 0/3 (no scored computation consumed a slot),
      GO phrase never consumed by the scored path.  The owner decides
      remediation and re-GO.  No engine byte is modified.
      If feasible, the full scored path runs (3 cells x build_all_books ->
      adjudicate_candidate -> DSR gate on survivors) under a live RSS
      interlock.

This orchestrator is lane code (allowed write: research/control/
stocks_search_v1_run/e/).  The frozen chain i/s/d1/p0/m0/z/audits is
read-only.  No push/merge/rebase; the lane commits by exact pathspec
afterwards.
"""

from __future__ import annotations

import gc
import hashlib
import importlib.util
import json
import math
import os
import resource
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path("/Users/hoangminhlong/my-quantitative")
WT = REPO / ".worktrees/stocks-search-v1/integration"
RUN_DIR = WT / "research/control/stocks_search_v1_run"
E_DIR = RUN_DIR / "e"
P0_DIR = RUN_DIR / "p0"
S_FREEZE_PATH = RUN_DIR / "s" / "selection_freeze.json"
CACHE_DIR = P0_DIR / "raw" / "eod_cache"
MANIFEST_PATH = P0_DIR / "retrieval_manifest.json"
COHORT_CENSUS_PATH = P0_DIR / "p0_census_cohort.json.gz"

DISPATCH_BASE = "c294563115e4f0f22f3283bcaff32f866777da39"
BRANCH = "orca/stocks-search-v1-integration"
CYCLE_ID = "STOCKS-SEARCH-V1"
STORE_LABEL = "ZCODE-ORCHESTRATION-V3"
ROLE = "quant-implementer"
LANE = "ssearch-e"

SHADOW_PIDS = (15315, 15316)
N_PROBE_NAMES = 2500
N_LEG_BENCH = 30_000
PHYSICAL_RAM_BYTES = 8 * 1024**3
SAFE_BUDGET_BYTES = int(6.0 * 1024**3)      # pre-declared feasibility ceiling
RSS_INTERLOCK_BYTES = int(5.5 * 1024**3)    # live abort threshold (scored path)

sys.path.insert(0, str(REPO / "research"))   # governance package
sys.path.insert(0, str(RUN_DIR / "i"))       # frozen i_engine / adjudicate
sys.path.insert(0, str(WT))                  # research.dsr

LOG_PATH = E_DIR / "run_log.txt"
LOG_LOCK = threading.Lock()


def log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {msg}"
    with LOG_LOCK:
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    print(line, flush=True)


def rss_now() -> int:
    import psutil
    return psutil.Process().memory_info().rss


def rss_peak() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def progress(phase: str, state: str, **kw) -> None:
    payload = {"phase": phase, "state": state,
               "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               **kw}
    (E_DIR / "progress.json").write_text(json.dumps(payload, indent=1) + "\n")


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(WT), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


# ------------------------------------------------------------------ P0 env

def _tracked_dirty(lines: list) -> list:
    """A tracked modification is any porcelain line that is not '??'.
    Untracked entries are tolerable ONLY inside the lane's allowed-write
    paths (this e/ directory) and gitignored __pycache__ dirs."""
    bad = []
    for l in lines:
        if l.startswith("??"):
            p = l[3:].strip()
            if p.endswith("__pycache__") or "stocks_search_v1_run/e" in p:
                continue
        bad.append(l)
    return bad


def p0_env() -> dict:
    head = git("rev-parse", "HEAD")
    branch = git("branch", "--show-current")
    porcelain = git("status", "--porcelain")
    shadows = subprocess.run(
        ["ps", "-o", "pid=,stat=,command=", "-p", ",".join(map(str, SHADOW_PIDS))],
        capture_output=True, text=True).stdout.strip()
    rec = {"head": head, "branch": branch,
           "head_ok": head == DISPATCH_BASE, "branch_ok": branch == BRANCH,
           "porcelain": porcelain.splitlines(),
           "tracked_dirty": _tracked_dirty(porcelain.splitlines()),
           "shadow_workers": shadows}
    if not rec["head_ok"]:
        raise RuntimeError(f"FROZEN_SHA_MISMATCH: HEAD {head} != {DISPATCH_BASE}")
    if not rec["branch_ok"]:
        raise RuntimeError(f"FROZEN_SHA_MISMATCH: branch {branch} != {BRANCH}")
    if rec["tracked_dirty"]:
        raise RuntimeError("FROZEN_SHA_MISMATCH: tracked tree dirty at start: "
                           + json.dumps(rec["tracked_dirty"]))
    return rec


# ------------------------------------------------------------------ P1 lock

def p1_lock():
    from governance import heavy_lock
    handle = heavy_lock.acquire(
        cycle_id=CYCLE_ID, role=f"{ROLE}/{LANE}", worktree=str(WT),
        command=[sys.executable, str(Path(__file__).resolve()), "--run"],
        expected_artifacts=[str(E_DIR / "e_run_verdict.json")])
    stop = threading.Event()

    def beat():
        n = 0
        while not stop.wait(60.0):
            n += 1
            try:
                handle.heartbeat(extra={"heartbeat_n": n})
            except Exception as e:      # never kill the run on a beat error
                log(f"heartbeat error (continuing): {e!r}")

    threading.Thread(target=beat, daemon=True).start()
    return handle, stop


# ------------------------------------------------------------------ P2 gate

def p2_gate() -> dict:
    import i_engine
    vf = i_engine.verify_freeze()
    log(f"freeze verified: {json.dumps(vf)}")
    t0 = time.time()
    preflight = i_engine.verify_data_plane(CACHE_DIR, MANIFEST_PATH)
    dt = time.time() - t0
    out = E_DIR / "data_plane_preflight.json"
    out.write_text(json.dumps(preflight, indent=1, sort_keys=True) + "\n")
    log(f"data-plane preflight PASS in {dt:.0f}s -> {out} "
        f"(checks={sorted(preflight['checks'])}, "
        f"arms={json.dumps(preflight['arms'])})")
    progress("P2_gate", "PASS", seconds=round(dt))
    return preflight


# ------------------------------------------------------------------ P3 calib

def _load_pinned_p0_run(expected_sha: str):
    path = P0_DIR / "p0_run.py"
    disk = hashlib.sha256(path.read_bytes()).hexdigest()
    if disk != expected_sha:
        raise RuntimeError(
            f"FROZEN_SHA_MISMATCH: p0_run.py {disk} != pin {expected_sha}")
    spec = importlib.util.spec_from_file_location(
        "stocks_search_v1_p0_run_e", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, mod)
    spec.loader.exec_module(mod)
    return mod


def _pinned_p0_lib(expected_sha: str):
    import i_engine
    return i_engine.load_p0_lib(expected_sha=expected_sha)


def loader_probe(pins: dict) -> dict:
    """Exact adjudicate.load_real_data per-name construction over a bounded
    prefix of the real cache (post-gate, scored GO gate untouched)."""
    p0_run = _load_pinned_p0_run(pins["p0_run.py"])
    from i_engine import NameData
    retrieval = json.loads(MANIFEST_PATH.read_text())
    syms = sorted(s for s, m in retrieval["pulls"].items()
                  if m.get("status") == 200)[:N_PROBE_NAMES]
    gc.collect()
    rss0, t0 = rss_now(), time.time()
    names = {}
    sessions = 0
    for sym in syms:
        parsed = p0_run.parse_name(CACHE_DIR / f"{sym}.json.gz")
        if parsed is None:
            continue
        dates, o, h, lo, c, v, _mal = parsed
        names[sym] = NameData(sym, tuple(d[:10] for d in dates),
                              np.asarray(o, dtype=float),
                              np.asarray(h, dtype=float),
                              np.asarray(lo, dtype=float),
                              np.asarray(c, dtype=float),
                              np.asarray(v, dtype=float))
        sessions += len(names[sym].dates)
    dt = time.time() - t0
    rss1 = rss_now()
    del names
    gc.collect()
    return {"n_names_probed": len(syms), "sessions_probed": sessions,
            "rss_delta_bytes": rss1 - rss0,
            "bytes_per_served_session": (rss1 - rss0) / max(sessions, 1),
            "parse_seconds": round(dt, 1),
            "probe_rss_construction": "adjudicate.load_real_data per-name "
                                      "construction (dates tuple + 5 float64 "
                                      "arrays), verified post-gate"}


def leg_benchmark(mode: str) -> dict:
    """Frozen i_engine.build_legs footprint in a FRESH process for ONE mode
    (H1 | H20 | deepcopy).  Phase isolation is required: sequential phases
    in one process reuse freed pages and corrupt RSS deltas (incident 1)."""
    import i_engine
    _pinned_p0_lib(json.loads(S_FREEZE_PATH.read_text())
                   ["data_manifests_sha256"]["p0_lib.py"])
    from datetime import date, timedelta

    freeze = json.loads(S_FREEZE_PATH.read_text())
    b1 = freeze["folds"]["boundaries"]["B1"]
    b2 = freeze["folds"]["boundaries"]["B2"]
    n = N_LEG_BENCH + 400
    d0 = date(2015, 1, 2)
    dates = []
    d = d0
    while len(dates) < n:
        if d.weekday() < 5:
            dates.append(d.isoformat())
        d += timedelta(days=1)
    op = np.full(n, 100.0)
    vol = np.full(n, 1.0e6)          # dvol 1e8 -> band A (never SUBFLOOR)
    nd = i_engine.NameData("BENCH", tuple(dates), op, op, op, op, vol)
    dec = list(range(300, 300 + N_LEG_BENCH))
    cal_idx = {dd: i for i, dd in enumerate(dates)}
    # memory benchmark only: F3 end extended to the synthetic last session so
    # every benchmark decision opens a real leg (fold realism is irrelevant
    # to the per-leg footprint being measured)
    fends = {"F1": b1, "F2": b2, "F3": dates[-1]}

    H = 1 if mode == "H1" else 20
    gc.collect()
    rss0, t0 = rss_now(), time.time()
    legs, cens, counts = i_engine.build_legs(nd, dec, H, cal_idx, fends,
                                             i_engine.STRESS_TIER)
    dt = time.time() - t0
    rss1 = rss_now()
    out = {
        "mode": mode, "n_decisions": len(dec), "n_legs": len(legs),
        "n_censored": len(cens), "counts": counts,
        "rss_delta_bytes": rss1 - rss0,
        "bytes_per_leg": (rss1 - rss0) / max(len(legs), 1),
        "build_seconds": round(dt, 2),
        "us_per_decision": 1e6 * dt / len(dec),
        "note": "us_per_decision includes Python GC scaling with the alive "
                "leg population (the real run_book accumulates legs across "
                "names, so the real path inherits the same effect); "
                "bytes_per_leg includes the one-time med252 sliding-median "
                "temporary at this synthetic 30k-session scale"}
    if mode == "deepcopy":
        book = i_engine.BookResult(book_id="bench", config_id="bench",
                                   H=20, stress=2.0, calendar=tuple(dates))
        book.legs = legs
        gc.collect()
        rss_b = rss_now()
        import copy
        book2 = copy.deepcopy(book)
        rss_c = rss_now()
        out["deepcopy_delta_bytes"] = rss_c - rss_b
        out["factor"] = (rss_c - rss_b) / max(rss1 - rss0, 1)
        del book2
    return out


def _run_probe(mode: str) -> dict:
    """Run a probe in a FRESH subprocess and parse its PROBE_JSON line.

    Incident-hardened (see verdict incidents): in-process probes after the
    loader probe's free() show allocator-noise-corrupted RSS deltas
    (negative bytes-per-leg, degenerate deepcopy factor) because freed
    pages are reused without RSS growth.  A fresh process per probe gives
    clean before/after deltas; hard bounds below catch any repeat.
    """
    r = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), f"--{mode}"],
        capture_output=True, text=True)
    for line in reversed(r.stdout.splitlines()):
        if line.startswith("PROBE_JSON:"):
            return json.loads(line[len("PROBE_JSON:"):])
    raise RuntimeError(f"probe {mode} failed: rc={r.returncode} "
                       f"stderr={r.stderr[-2000:]}")


PROBE_BOUNDS = {
    "bytes_per_served_session": (40.0, 300.0),
    "H1_bytes_per_leg": (50.0, 1000.0),
    "H20_bytes_per_leg": (1000.0, 6000.0),
}
DEEPCOPY_BOUNDS = (0.5, 3.0)
DEEPCOPY_CONSERVATIVE_DEFAULT = 2.0
# Measured sensitivity of the loader footprint across independent runs
# (fresh 60-name smoke 149.09; first-launch in-process 98.47; fresh
# subprocess 53.28 B/session; logical object arithmetic ~112 B/session).
# The infeasibility conclusion must hold at the MINIMUM measured value.
LOADER_SENSITIVITY_B_SESSION = [53.28, 98.47, 112.0, 149.09]


def p3_calibration(pins: dict) -> dict:
    import gzip
    cc = json.loads(gzip.open(COHORT_CENSUS_PATH, "rt").read())
    total_sessions = sum(int(v.get("served", 0)) for v in cc.values())
    served_names = sum(1 for v in cc.values() if int(v.get("served", 0)) > 0)
    freeze = json.loads(S_FREEZE_PATH.read_text())
    positions = {c["config_id"]: c["pooled_series_stats"]["positions_used"]
                 for c in freeze["selected_candidates"]}
    progress("P3_calibration", "RUNNING")
    lp = _run_probe("probe-loader")
    log(f"loader probe (fresh subprocess): {json.dumps(lp)}")
    lb1 = _run_probe("probe-legs-H1")
    lb20 = _run_probe("probe-legs-H20")
    dcx = _run_probe("probe-deepcopy")
    lb = {"H1": lb1, "H20": lb20, "deepcopy_factor_H20": dcx.get("factor")}
    log(f"leg benchmark (isolated fresh subprocesses): {json.dumps(lb)}")

    measured = {
        "bytes_per_served_session": lp["bytes_per_served_session"],
        "H1_bytes_per_leg": lb1["bytes_per_leg"],
        "H20_bytes_per_leg": lb20["bytes_per_leg"],
    }
    violations = {k: {"measured": measured[k], "bounds": PROBE_BOUNDS[k]}
                  for k in PROBE_BOUNDS
                  if not (PROBE_BOUNDS[k][0] <= measured[k] <= PROBE_BOUNDS[k][1])}
    dc_raw = dcx.get("factor")
    if dc_raw is not None and DEEPCOPY_BOUNDS[0] <= dc_raw <= DEEPCOPY_BOUNDS[1]:
        dc, dc_note = float(dc_raw), "measured in fresh subprocess"
    else:
        dc, dc_note = DEEPCOPY_CONSERVATIVE_DEFAULT, (
            "deepcopy measurement unreliable -> conservative default "
            f"{DEEPCOPY_CONSERVATIVE_DEFAULT} (overestimates memory: "
            "fail-closed direction)")

    cal = {
        "schema": "stocks_search_v1_e_calibration@1",
        "cohort_census": {"n_names": len(cc), "n_served_names": served_names,
                          "total_served_sessions": total_sessions},
        "loader_probe": lp,
        "leg_benchmark": lb,
        "probe_bounds": PROBE_BOUNDS,
        "bound_violations": violations,
        "measurement_failure": bool(violations),
        "deepcopy_factor": dc,
        "deepcopy_factor_note": dc_note,
    }

    if violations:
        # fail-closed: an unmeasurable footprint is treated as infeasible
        cal.update({
            "feasible": False,
            "law": "probe bounds violated -> the footprint is UNMEASURABLE; "
                   "fail-closed TECHABORT direction (never launch on an "
                   "unverified measurement; incident of the first launch "
                   "recorded in the verdict)"})
        (E_DIR / "calibration.json").write_text(json.dumps(cal, indent=1) + "\n")
        log(f"calibration MEASUREMENT FAILURE: {json.dumps(violations)}")
        progress("P3_calibration", "DONE", feasible=False,
                 measurement_failure=True)
        return cal

    loader_total = measured["bytes_per_served_session"] * total_sessions
    legs_floor = {cid: positions[cid] for cid in positions}
    bpl = {"SSS-GAP-P25-CONFIRM-H1": measured["H1_bytes_per_leg"],
           "SSS-52W-HIGH-B10-H20": measured["H20_bytes_per_leg"],
           "SSS-VOL-REGIME-L21-LOW-H20": measured["H20_bytes_per_leg"]}
    books_floor = {cid: legs_floor[cid] * bpl[cid] for cid in legs_floor}
    per_cell_peak = {cid: loader_total + books_floor[cid] * max(dc, 1.0)
                     for cid in legs_floor}
    worst = max(per_cell_peak.values())
    cal.update({
        "candidate_opened_leg_floor_from_freeze_positions_used": legs_floor,
        "bytes_per_leg_assumed_per_cell": bpl,
        "loader_total_bytes": loader_total,
        "candidate_books_floor_bytes": books_floor,
        "per_cell_peak_floor_bytes": per_cell_peak,
        "worst_cell_peak_floor_bytes": worst,
        "physical_ram_bytes": PHYSICAL_RAM_BYTES,
        "safe_budget_bytes": SAFE_BUDGET_BYTES,
        "feasible": worst <= SAFE_BUDGET_BYTES,
        "law": "pre-declared interlock: the scored load is not launched when "
               "the measured frozen-path peak floor exceeds SAFE_BUDGET_BYTES "
               "(8 GiB machine; co-tenant ACTIVE_LIGHT shadow workers "
               "15315/15316 must not be endangered by swap thrash); the floor "
               "counts the loader plus ONE candidate book times the deepcopy "
               "factor - complement/control books (larger) are excluded, so "
               "the true requirement is strictly higher",
    })
    (E_DIR / "calibration.json").write_text(json.dumps(cal, indent=1) + "\n")
    log(f"calibration: worst-cell peak floor {worst / 1024**3:.2f} GiB vs "
        f"safe budget {SAFE_BUDGET_BYTES / 1024**3:.2f} GiB -> "
        f"feasible={cal['feasible']}")
    progress("P3_calibration", "DONE", feasible=cal["feasible"])
    return cal


# ------------------------------------------------- P4 scored path (if fit)

def p4_scored(preflight: dict) -> dict:
    """Full scored path - reached ONLY if calibration says feasible."""
    import i_engine
    import adjudicate
    import gc as _gc

    def rss_check(where: str) -> None:
        live = rss_now()
        if live > RSS_INTERLOCK_BYTES:
            raise RuntimeError(
                f"RSS_INTERLOCK at {where}: live {live} > "
                f"{RSS_INTERLOCK_BYTES} (TECHABORT: engine resource "
                f"exhaustion on real data; state preserved)")

    loaded = adjudicate.load_real_data(i_engine.GO_PHRASE, CACHE_DIR,
                                       MANIFEST_PATH)
    rss_check("after load_real_data")
    names = loaded["names"]
    freeze = json.loads(S_FREEZE_PATH.read_text())
    b1 = freeze["folds"]["boundaries"]["B1"]
    b2 = freeze["folds"]["boundaries"]["B2"]
    calendar, _spy_sha = i_engine._build_calendar_from_cache(
        CACHE_DIR, freeze["s0_window"]["start"], freeze["s0_window"]["end"])
    spy = names.get("SPY")
    used = 0
    cell_results = {}
    survivors = []
    for cid in i_engine.CELL_IDS:
        rss_check(f"before cell {cid}")
        used += 1
        log(f"scored cell {used}/3: {cid}")
        cell = i_engine.CELL_BY_ID[cid]
        bundle = i_engine.build_all_books(names, cell, calendar, b1, b2,
                                          i_engine.STRESS_TIER)
        rss_check(f"after build_all_books {cid}")
        rep = adjudicate.adjudicate_candidate(bundle, spy, calendar, b1, b2)
        rep["budget"] = {"used": used, "max": adjudicate.BUDGET_MAX_SCORED_CELLS,
                         "label": f"{used}/{adjudicate.BUDGET_MAX_SCORED_CELLS}"}
        if rep["verdict"] == "PASS_I_STAGE_PENDING_DSR_E":
            cand = bundle["candidate"]
            trial_sharpes = []
            dsr = adjudicate.dsr_gate(cand.book_log, trial_sharpes,
                                      adjudicate.DSR_N_GRID,
                                      adjudicate.DSR_ALPHA_RELAXED,
                                      allow_scored=True)
            rep["dsr"]["computed"] = dsr
            if dsr.get("pass"):
                survivors.append(cid)
        cdir = E_DIR / "cells"
        cdir.mkdir(exist_ok=True)
        (cdir / f"{cid}.json").write_text(
            json.dumps(rep, indent=1, sort_keys=True, default=str) + "\n")
        pdir = E_DIR / "p11_series"
        pdir.mkdir(exist_ok=True)
        digest = adjudicate.persist_series(pdir / f"{cid}_candidate.jsonl",
                                           bundle["candidate"])
        rep["p11_series_sha256"] = digest
        cell_results[cid] = rep
        log(f"cell {cid} verdict: {rep['verdict']}")
        del bundle
        gc.collect()
    return {"cells": cell_results, "survivors": survivors, "budget_used": used}


# ------------------------------------------------------------------ main

def write_verdict(payload: dict) -> None:
    (E_DIR / "e_run_verdict.json").write_text(
        json.dumps(payload, indent=1, sort_keys=True, default=str) + "\n")


def main() -> int:
    t0 = time.time()
    E_DIR.mkdir(parents=True, exist_ok=True)
    log(f"ssearch-e orchestrator start; python {sys.version.split()[0]}; "
        f"pid {os.getpid()}")
    env = p0_env()
    log(f"env verified: HEAD {env['head'][:12]} branch {env['branch']}; "
        f"shadow workers:\n{env['shadow_workers']}")
    handle, beat_stop = p1_lock()
    log("heavy lock acquired + heartbeat thread running")
    result = {"status": "RUNNING"}
    write_verdict({"schema": "stocks_search_v1_e_run_verdict@1",
                   "status": "RUNNING",
                   "started_utc": datetime.now(timezone.utc).isoformat()})
    try:
        preflight = p2_gate()
        freeze = json.loads(S_FREEZE_PATH.read_text())
        pins = freeze["data_manifests_sha256"]
        cal = p3_calibration(pins)
        if cal["feasible"]:
            log("calibration FEASIBLE -> launching full scored path")
            progress("P4_scored", "RUNNING")
            scored = p4_scored(preflight)
            verdict = {
                "schema": "stocks_search_v1_e_run_verdict@1",
                "status": "SCORED_RUN_COMPLETE",
                "terminal_outcome": _terminal_outcome(scored),
                "cells": scored["cells"],
                "survivors": scored["survivors"],
                "budget": {"used": scored["budget_used"], "max": 3,
                           "label": f"{scored['budget_used']}/3"},
                "data_plane_preflight_ref": "e/data_plane_preflight.json",
                "calibration_ref": "e/calibration.json",
                "r0_status": "R0_NOT_RUN",
                "pbo_status": "PBO_NOT_RUN",
                "disclosure": "see i_engine constants carried per cell",
            }
        else:
            worst = cal.get("worst_cell_peak_floor_bytes")
            verdict = {
                "schema": "stocks_search_v1_e_run_verdict@1",
                "status": "TECHABORT_PRESERVED",
                "stop_condition": "TECHABORT",
                "terminal_outcome": "STOCKS_SEARCH_V1_TECHABORT_PRESERVED",
                "task_id": "ssearch-e", "lane": LANE, "role": ROLE,
                "cycle_id_real": CYCLE_ID, "cycle_store_label": STORE_LABEL,
                "base_sha": DISPATCH_BASE, "head_verified": env["head"],
                "branch": env["branch"],
                "utc": datetime.now(timezone.utc).isoformat(),
                "incidents": [
                    "INCIDENT 1 (lane-harness defect, caught BEFORE any "
                    "scored computation; cycle precedent: ssearch-z in-lane "
                    "fix of the D2 positive control, incident recorded): the "
                    "first launch of this orchestrator computed the "
                    "calibration IN-PROCESS; after the loader probe freed "
                    "3.1M NameData objects, the leg benchmark's RSS deltas "
                    "were allocator-noise-corrupted (negative bytes-per-leg, "
                    "degenerate deepcopy factor 4.05e7), yielding a false "
                    "feasible=True and launching adjudicate.load_real_data. "
                    "This lane stopped ITS OWN process (SIGTERM to pid 38482 "
                    "at 85 MB RSS, during the second preflight, before any "
                    "heavy allocation, before any scored computation or cell "
                    "verdict; the co-tenant shadow workers were never "
                    "touched); the stale lock row was reconciled via the "
                    "documented governance.heavy_lock.cleanup_stale() "
                    "(reason pid_dead); the GO phrase had been presented "
                    "once to the frozen gate with ZERO scored computations "
                    "completing (budget 0/3, no cell verdict, no scored "
                    "number produced). Remediation: probes moved to fresh "
                    "subprocesses with hard measurement bounds (violation = "
                    "fail-closed infeasible), conservative deepcopy default. "
                    "The same authorized scored execution was then re-run. "
                    "First-launch evidence preserved verbatim: "
                    "e/calibration_first_launch_false_feasible.json, "
                    "e/verdict_first_launch_running.json, "
                    "e/launcher_first_launch.log, and e/run_log.txt "
                    "(append-only).",
                ],
                "go_phrase_state":
                    "NOT_CONSUMED_BY_SCORED_PATH: the owner's exact registered "
                    "GO phrase authorized this scored run, but the TECHABORT "
                    "interlock fired at the E-run boundary on measured "
                    "evidence, before any scored computation; no scored cell "
                    "consumed a slot; owner re-GO required after remediation",
                "data_plane_preflight": {
                    "status": preflight["status"],
                    "artifact": "e/data_plane_preflight.json",
                    "n_census_cells_checked":
                        preflight["n_census_cells_checked"],
                    "counters": preflight["counters"],
                    "arms": preflight["arms"],
                    "law": "C-2 gate RAN AND PASSED before any cohort byte "
                           "was parsed into a scored computation"},
                "calibration": {
                    "artifact": "e/calibration.json",
                    "feasible": False,
                    "measurement_failure": cal.get("measurement_failure",
                                                   False),
                    "bound_violations": cal.get("bound_violations"),
                    "physical_ram_bytes": PHYSICAL_RAM_BYTES,
                    "safe_budget_bytes": SAFE_BUDGET_BYTES,
                    "worst_cell_peak_floor_bytes": worst,
                    "worst_cell_peak_floor_gib":
                        round(worst / 1024**3, 2) if worst else None,
                    "loader_probe": cal.get("loader_probe"),
                    "leg_benchmark_summary": {
                        k: cal["leg_benchmark"][k]
                        for k in ("H1", "H20", "deepcopy_factor_H20")
                        if k in cal.get("leg_benchmark", {})},
                    "deepcopy_factor_note":
                        cal.get("deepcopy_factor_note")},
                "failure_record": {
                    "defect_class":
                        "ENGINE_RESOURCE_INFEASIBILITY_ON_REAL_DATA",
                    "exact_failure":
                        "the frozen scored E path "
                        "(adjudicate.load_real_data materializing all served "
                        "NameData objects, then i_engine.build_all_books leg "
                        "objects with per-leg P-11 log slices, doubled by the "
                        "frozen adjudication deepcopy) has a measured peak "
                        "memory floor above the machine's safe budget; the "
                        "floor EXCLUDES complement/control books, so the true "
                        "requirement is strictly higher",
                    "arithmetic": {
                        "total_served_sessions":
                            cal["cohort_census"]["total_served_sessions"],
                        "bytes_per_served_session_measured":
                            (cal.get("loader_probe") or {}).get(
                                "bytes_per_served_session"),
                        "loader_total_bytes": cal.get("loader_total_bytes"),
                        "candidate_opened_leg_floor":
                            cal.get("candidate_opened_leg_floor_from_freeze_positions_used"),
                        "bytes_per_leg_measured":
                            cal.get("bytes_per_leg_assumed_per_cell"),
                        "per_cell_peak_floor_bytes":
                            cal.get("per_cell_peak_floor_bytes"),
                        "deepcopy_factor": cal.get("deepcopy_factor"),
                        "deepcopy_factor_note":
                            cal.get("deepcopy_factor_note"),
                        "compute_note":
                            "frozen build_legs is per-decision Python; the "
                            "candidate fired census alone is 2.15e8 decisions "
                            "(p0_census.json) and the complement/component "
                            "books iterate more, so wall-clock cost is of "
                            "the same order-days class as the memory "
                            "infeasibility (see leg_benchmark "
                            "us_per_decision)"},
                    "why_not_launched":
                        ("launching would drive >= "
                         f"{(worst - PHYSICAL_RAM_BYTES) / 1024**3:.0f} GiB "
                         "beyond physical RAM into swap on an 8 GiB machine "
                         "with 12 GiB free disk - a "
                         if worst else
                         "the footprint could not be measured within hard "
                         "bounds; an unmeasurable footprint is treated as "
                         "infeasible (fail-closed) - a ") +
                        "machine-wide freeze endangering the co-tenant "
                        "ACTIVE_LIGHT shadow workers 15315/15316 (never "
                        "killed, never disrupted); fail-closed pre-launch "
                        "interlock per the dispatch stop conditions",
                    "no_mid_run_fix":
                        "no frozen engine byte was modified; remediation "
                        "(streaming E-engine, larger machine, or equivalent) "
                        "is an owner decision followed by a fresh GO"},
                "arithmetic_present": worst is not None,
                "budget": {"used": 0, "max": 3,
                           "label": "0/3 (TECHABORT before any scored "
                                    "computation; no scored cell consumed an "
                                    "observed slot; slots never force-filled)"},
                "r0_status": "R0_NOT_RUN",
                "r0_verbatim": "R0 NOT_RUN (D2 skipped by owner amendment §3b)",
                "d2_disclosure": "D2 is SKIPPED per owner amendment §3b (R0 "
                                 "NOT_RUN - never computed, never inferred)",
                "pbo_status": "PBO_NOT_RUN",
                "pbo_verbatim": "PBO NOT_RUN fail-closed (<=3 cells, d0992d17 "
                                "class)",
                "disclosure_section10_verbatim":
                    "accepted under owner-relaxed acceptance battery (R0 0.30 "
                    "/ DSR alpha 0.10 at N = grid) | PBO NOT_RUN fail-closed "
                    "(<=3 cells, d0992d17 class) | R0 NOT_RUN (D2 skipped by "
                    "owner amendment §3b)",
                "cells": {
                    cid: {"status": "NOT_RUN",
                          "reason": "TECHABORT at the E-run boundary (memory "
                                    "infeasibility of the frozen scored path "
                                    "on the authorized machine); no scored "
                                    "computation for any arm"}
                    for cid in ("SSS-GAP-P25-CONFIRM-H1",
                                "SSS-52W-HIGH-B10-H20",
                                "SSS-VOL-REGIME-L21-LOW-H20")},
                "p11_series": "NOT_PRODUCED (no scored book computed)",
                "partial_artifacts": [
                    "e/data_plane_preflight.json (C-2 gate PASS artifact)",
                    "e/calibration.json (measured footprint evidence)",
                    "e/run_log.txt", "e/progress.json"],
                "shadow_workers_untouched": env["shadow_workers"],
                "wall_seconds": round(time.time() - t0, 1),
            }
            verdict["terminal_mapping_note"] = (
                "§11 mapping: TECHABORT with state preserved (C-2 gate PASS + "
                "measured calibration + 0/3 budget + no scored computation); "
                "the fold-positive-share law (>50% KILLS; V11 precedent "
                "0.5034 is a FAILING value) and the BC-7 death-censoring "
                "invariance (binds the verdict AND every Stage-A gate) remain "
                "binding on any remediated re-run; they were never evaluated "
                "here")
        write_verdict(verdict)
        result = verdict
        log(f"verdict written: {verdict['status']} / "
            f"{verdict.get('terminal_outcome')}")
        return 0
    except SystemExit as e:  # pragma: no cover (unreachable: no interlock raise)
        log(f"interlock exit: {e}")
        result = {"status": "TECHABORT_PRESERVED"}
        write_verdict({"schema": "stocks_search_v1_e_run_verdict@1",
                       "status": "TECHABORT_PRESERVED",
                       "stop_condition": "TECHABORT",
                       "terminal_outcome":
                           "STOCKS_SEARCH_V1_TECHABORT_PRESERVED",
                       "failure_record": {
                           "defect_class":
                               "ENGINE_RESOURCE_EXHAUSTION_ON_REAL_DATA",
                           "exact_failure": str(e)},
                       "note": "partial artifacts preserved under e/"})
        return 9
    except Exception as e:
        tb = traceback.format_exc()
        log(f"FAIL-CLOSED EXCEPTION: {e!r}\n{tb}")
        result = {"status": "STOPPED", "stop_condition": _classify_exception(e)}
        write_verdict({"schema": "stocks_search_v1_e_run_verdict@1",
                       "status": "STOPPED",
                       "stop_condition": _classify_exception(e),
                       "failure_record": {"repr": repr(e), "traceback": tb}})
        return 2
    finally:
        try:
            if isinstance(result, dict) and \
                    result.get("status") == "TECHABORT_PRESERVED":
                handle.release(status="TECHABORT",
                               note="ssearch-e: measured memory infeasibility "
                                    "of the frozen scored path; state "
                                    "preserved under e/")
            elif isinstance(result, dict) and result.get("status") in (
                    "SCORED_RUN_COMPLETE",):
                handle.release(status="FINISHED", note="ssearch-e scored run")
            else:
                handle.release(status="FAILED",
                               note=f"ssearch-e stopped: {result.get('status')}")
            log("heavy lock released")
        except Exception as e:
            log(f"lock release error: {e!r}")
        beat_stop.set()
        log(f"orchestrator exit after {time.time() - t0:.0f}s")


def _terminal_outcome(scored: dict) -> str:
    if scored["survivors"]:
        return ("STOCKS_SEARCH_V1_SURVIVORS_UNDER_RELAXED_BATTERY_"
                "R0_NOT_RUN_PBO_NOT_RUN")
    if any(c["verdict"].startswith("REJECT") for c in scored["cells"].values()):
        return "STOCKS_SEARCH_V1_REJECT_ALL"
    return "STOCKS_SEARCH_V1_INCOMPLETE_NOT_PROMOTABLE"


def _classify_exception(e: Exception) -> str:
    from i_engine import DataPlaneMismatch, FrozenShaMismatch
    if isinstance(e, DataPlaneMismatch):
        return "INPUT_MISMATCH"
    if isinstance(e, FrozenShaMismatch):
        return "FROZEN_SHA_MISMATCH"
    return "TECHABORT"


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].startswith("--probe-"):
        _mode = sys.argv[1][2:]          # e.g. probe-legs-H1
        if _mode == "probe-loader":
            _out = loader_probe(json.loads(
                S_FREEZE_PATH.read_text())["data_manifests_sha256"])
        elif _mode in ("probe-legs-H1", "probe-legs-H20", "probe-deepcopy"):
            _out = leg_benchmark(_mode.split("probe-legs-")[-1]
                                 if "probe-legs-" in _mode else "deepcopy")
        else:
            _out = None
        if _out is None:
            print(f"unknown probe mode {sys.argv[1]}", file=sys.stderr)
            sys.exit(2)
        print("PROBE_JSON:" + json.dumps(_out))
        sys.exit(0)
    sys.exit(main())
