"""STOCKS-SEARCH-V1 E2-lane STREAMING scored-run orchestrator (ssearch-e2).

Owner remediation decision (a) of the STOCKS-SEARCH-V1 TECHABORT
(e/e_run_verdict.json): streaming/out-of-core E-engine + fresh GO.
This orchestrator replaces the memory-infeasible frozen path
(load_real_data + build_all_books materialization) with the streaming
engine (e2/i_stream_engine.py) while reproducing the frozen experiment
byte-for-byte.  The frozen chain (i/, e/, s/, d1/, p0/, m0/, z/) is
READ-ONLY.

Fail-closed phase order:
  P0  environment verification (HEAD == e2/dispatch.json base, clean
      tracked tree apart from the e2/ allowed-write namespace, detached
      shadow workers 15315/15316 alive and untouched)
  P1  heavy lock acquire + heartbeat (NOT_RUN_RESOURCE_CONFLICT on busy)
  P2  MANDATORY data-plane preflight (i_engine.verify_data_plane, A7
      F-1 / GO condition C-2) - RUNS AND PASSES before any cohort byte
      is parsed into a scored computation
  P3  streaming-resource calibration: free-disk floor, declared spill
      quota, and a fresh-subprocess peak-RSS probe of the STREAMING
      engine on a synthetic cohort (hard bound; violation = fail-closed
      TECHABORT - the remediation must be proven O(one-name) BEFORE the
      scored launch, unlike the first-launch incident)
  P4  scored streaming execution of the 3 frozen cells with the exact
      owner GO phrase (P-8), per-name crash-safe checkpoints, RSS
      watchdog (hard abort above RSS_INTERLOCK_BYTES), atomic verdict
      artifacts, honest budget accounting (a cell's observed slot is
      consumed when its scored computation starts), DSR gate on any
      K6/Stage-A survivor (adjudicate.dsr_gate, reused READ-ONLY), and
      P-11 persistence of the candidate daily series.

Scored GO law: this orchestrator is launched ONLY after the owner types
the exact registered phrase `GO STOCKS SEARCH V1 SCORED EXECUTION` in
response to the prelaunch STOP report (streaming remediation +
equivalence PASS + fresh-context A7 zero-unresolved-HIGH/CRITICAL).
The phrase is then re-checked inside verify_and_pin at P4 start.

Non-scored verification modes (no GO, no full cohort, no verdict):
  --selfcheck          targeted unit tests (e2/selfcheck.py)
  --equivalence        reference-vs-streaming fixtures (e2/equivalence.py)
  --probe-stream-rss   fresh-subprocess peak-RSS probe (synthetic only)

Lane discipline: allowed write root research/control/
stocks_search_v1_run/e2/.  No push/merge/rebase.  Never touches the
co-tenant ACTIVE_LIGHT shadow workers.
"""

from __future__ import annotations

import json
import os
import shutil
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
E2_DIR = RUN_DIR / "e2"
P0_DIR = RUN_DIR / "p0"
S_FREEZE_PATH = RUN_DIR / "s" / "selection_freeze.json"
CACHE_DIR = P0_DIR / "raw" / "eod_cache"
MANIFEST_PATH = P0_DIR / "retrieval_manifest.json"
DISPATCH_PATH = E2_DIR / "dispatch.json"

CYCLE_ID = "STOCKS-SEARCH-V1"
ROLE = "quant-implementer"
LANE = "ssearch-e2"
SHADOW_PIDS = (15315, 15316)

PHYSICAL_RAM_BYTES = 8 * 1024 ** 3
SAFE_BUDGET_BYTES = int(6.0 * 1024 ** 3)      # owner resource ceiling
RSS_INTERLOCK_BYTES = int(5.5 * 1024 ** 3)    # live abort (scored path)
RSS_PROBE_BOUND_BYTES = int(1.5 * 1024 ** 3)  # streaming probe bound
SPILL_QUOTA_BYTES = int(6.0 * 1024 ** 3)      # per-cell spill quota
MIN_FREE_DISK_BYTES = int(6.0 * 1024 ** 3)    # refuse to start below

sys.path.insert(0, str(REPO / "research"))    # governance package
sys.path.insert(0, str(RUN_DIR / "i"))        # frozen engines (read-only)
sys.path.insert(0, str(E2_DIR))               # streaming engine

LOG_PATH = E2_DIR / "run_log.txt"
LOG_LOCK = threading.Lock()
VERDICT_PATH = E2_DIR / "e2_run_verdict.json"
PROGRESS_PATH = E2_DIR / "progress.json"


def log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {msg}"
    with LOG_LOCK:
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    print(line, flush=True)


def progress(phase: str, state: str, **kw) -> None:
    payload = {"phase": phase, "state": state,
               "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               **kw}
    tmp = PROGRESS_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=1) + "\n")
    os.replace(tmp, PROGRESS_PATH)


def rss_now() -> int:
    import psutil
    return psutil.Process().memory_info().rss


def rss_peak_bytes() -> int:
    import resource
    import sys as _s
    v = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return v if _s.platform == "darwin" else v * 1024


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(WT), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def free_disk_bytes() -> int:
    return shutil.disk_usage(str(E2_DIR)).free


# ------------------------------------------------------------------ P0 env

def _tracked_dirty(lines: list) -> list:
    bad = []
    for l in lines:
        if l.startswith("??"):
            p = l[3:].strip()
            if p.endswith("__pycache__") or "stocks_search_v1_run/e2" in p:
                continue
        bad.append(l)
    return bad


def p0_env() -> dict:
    """Scored-run environment gate.

    The lane dispatch is pinned by CONTENT, not by a self-referential
    commit sha: e2/dispatch.json (committed, unmodified) carries a
    sha256 manifest of every lane code file; the scored run verifies the
    worktree's e2/*.py still hash to that manifest, the branch is the
    cycle branch, and the tracked tree is clean apart from the e2/
    allowed-write namespace.
    """
    import hashlib
    head = git("rev-parse", "HEAD")
    branch = git("branch", "--show-current")
    porcelain = git("status", "--porcelain")
    if not DISPATCH_PATH.exists():
        raise RuntimeError("FROZEN_SHA_MISMATCH: e2/dispatch.json missing")
    dispatch = json.loads(DISPATCH_PATH.read_text())
    # dispatch.json must be COMMITTED and unmodified at run time
    diff = subprocess.run(
        ["git", "-C", str(WT), "diff", "HEAD", "--",
         str(DISPATCH_PATH.relative_to(WT))],
        capture_output=True, text=True).stdout.strip()
    untracked = any(l.startswith("??") and "e2/dispatch.json" in l
                    for l in porcelain.splitlines())
    if diff or untracked:
        raise RuntimeError(
            "FROZEN_SHA_MISMATCH: e2/dispatch.json is not committed-"
            "unmodified (diff/untracked)")
    manifest = dispatch["code_freeze"]
    bad = {}
    for rel, want in sorted(manifest.items()):
        f = WT / rel
        got = hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() \
            else "MISSING"
        if got != want:
            bad[rel] = {"want": want, "got": got}
    shadows = subprocess.run(
        ["ps", "-o", "pid=,stat=,command=", "-p", ",".join(map(str, SHADOW_PIDS))],
        capture_output=True, text=True).stdout.strip()
    rec = {"head": head, "branch": branch,
           "code_freeze_files": len(manifest),
           "code_freeze_ok": not bad,
           "branch_ok": branch == "orca/stocks-search-v1-integration",
           "porcelain": porcelain.splitlines(),
           "tracked_dirty": _tracked_dirty(porcelain.splitlines()),
           "shadow_workers": shadows}
    if bad:
        raise RuntimeError("FROZEN_SHA_MISMATCH: e2 code drifted from the "
                           f"dispatch manifest: {json.dumps(bad)}")
    if not rec["branch_ok"]:
        raise RuntimeError(f"FROZEN_SHA_MISMATCH: branch {branch}")
    if rec["tracked_dirty"]:
        raise RuntimeError("FROZEN_SHA_MISMATCH: tracked tree dirty: "
                           + json.dumps(rec["tracked_dirty"]))
    return rec


# ------------------------------------------------------------------ P1 lock

def p1_lock():
    from governance import heavy_lock
    handle = heavy_lock.acquire(
        cycle_id=CYCLE_ID, role=f"{ROLE}/{LANE}", worktree=str(WT),
        command=[sys.executable, str(Path(__file__).resolve()), "--run"],
        expected_artifacts=[str(VERDICT_PATH)])
    stop = threading.Event()

    def beat():
        n = 0
        while not stop.wait(60.0):
            n += 1
            try:
                handle.heartbeat(extra={"heartbeat_n": n})
            except Exception as e:
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
    out = E2_DIR / "data_plane_preflight.json"
    out.write_text(json.dumps(preflight, indent=1, sort_keys=True) + "\n")
    log(f"data-plane preflight PASS in {dt:.0f}s -> {out}")
    progress("P2_gate", "PASS", seconds=round(dt))
    return preflight


# ------------------------------------------------------------- P3 calib

def _rss_probe_child() -> dict:
    """Peak-RSS probe of the streaming engine on a synthetic cohort
    (fresh subprocess).  Mirrors the incident-1 hardening: probes never
    run in-process with the scored state."""
    r = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()),
         "--probe-stream-rss"],
        capture_output=True, text=True)
    for line in reversed(r.stdout.splitlines()):
        if line.startswith("PROBE_JSON:"):
            return json.loads(line[len("PROBE_JSON:"):])
    raise RuntimeError(f"probe failed rc={r.returncode} "
                       f"stderr={r.stderr[-2000:]}")


def p3_calibration() -> dict:
    free = free_disk_bytes()
    probe = _rss_probe_child()
    cal = {
        "schema": "stocks_search_v1_e2_calibration@1",
        "free_disk_bytes": free,
        "min_free_disk_bytes": MIN_FREE_DISK_BYTES,
        "spill_quota_bytes": SPILL_QUOTA_BYTES,
        "safe_budget_bytes": SAFE_BUDGET_BYTES,
        "rss_probe": probe,
        "rss_probe_bound_bytes": RSS_PROBE_BOUND_BYTES,
    }
    cal["disk_ok"] = free >= MIN_FREE_DISK_BYTES
    cal["rss_probe_ok"] = (probe["peak_rss_bytes"] <= RSS_PROBE_BOUND_BYTES)
    cal["feasible"] = bool(cal["disk_ok"] and cal["rss_probe_ok"])
    cal["law"] = ("streaming remediation interlock: the scored launch "
                  "requires (i) free disk >= MIN_FREE_DISK_BYTES for the "
                  "declared per-cell spill quota and (ii) a fresh-"
                  "subprocess peak-RSS probe of the STREAMING engine "
                  "<= RSS_PROBE_BOUND_BYTES, proving the O(one-name) "
                  "footprint BEFORE any scored byte is parsed (incident-1 "
                  "class false-feasible launches are structurally "
                  "impossible: the probe measures the remediated engine "
                  "itself, not a model of it)")
    (E2_DIR / "calibration_stream.json").write_text(
        json.dumps(cal, indent=1, sort_keys=True) + "\n")
    log(f"stream calibration: free_disk={free / 1024**3:.2f} GiB, "
        f"probe peak RSS={probe['peak_rss_bytes'] / 1024**2:.0f} MiB -> "
        f"feasible={cal['feasible']}")
    progress("P3_calibration", "DONE", feasible=cal["feasible"])
    return cal


# ------------------------------------------------------- RSS watchdog

class RssWatchdog:
    """Hard-abort watchdog: sampled live RSS every interval; a breach
    raises SystemExit -> TECHABORT verdict with state preserved."""

    def __init__(self, ceiling: int):
        self.ceiling = ceiling
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.breach = None

    def _loop(self):
        while not self.stop.wait(5.0):
            try:
                live = rss_now()
            except Exception:
                continue
            if live > self.ceiling:
                self.breach = live
                os.kill(os.getpid(), 15)   # SIGTERM -> SystemExit in main
                return

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.stop.set()
        return False


# ------------------------------------------------------------------ P4

def _load_spy_full() -> "object":
    import i_engine
    freeze = json.loads(S_FREEZE_PATH.read_text())
    p0_run = i_engine._load_pinned_p0_run(
        freeze["data_manifests_sha256"]["p0_run.py"])
    parsed = p0_run.parse_name(CACHE_DIR / "SPY.json.gz")
    dates, o, h, lo, c, v, _mal = parsed
    return i_engine.NameData(
        "SPY", tuple(d[:10] for d in dates),
        np.asarray(o, dtype=float), np.asarray(h, dtype=float),
        np.asarray(lo, dtype=float), np.asarray(c, dtype=float),
        np.asarray(v, dtype=float))


def p4_scored_stream(go_phrase: str) -> dict:
    import i_engine
    import i_stream_engine as se
    import adjudicate

    ctx = se.verify_and_pin(go_phrase, CACHE_DIR, MANIFEST_PATH)
    log("GO phrase verified at the streaming gate; data-plane preflight "
        "PASS inside the pinned loader context")
    freeze = json.loads(S_FREEZE_PATH.read_text())
    b1 = freeze["folds"]["boundaries"]["B1"]
    b2 = freeze["folds"]["boundaries"]["B2"]
    calendar, _ = i_engine._build_calendar_from_cache(
        CACHE_DIR, freeze["s0_window"]["start"], freeze["s0_window"]["end"])
    spy = _load_spy_full()
    se.set_spy_reference(spy)

    used = 0
    cell_results = {}
    survivors = []
    for cell in i_engine.FROZEN_CELLS:
        cid = cell["config_id"]
        cdir = E2_DIR / "cells" / cid
        if (cdir / "DONE").exists() and (cdir / "cell_verdict.json").exists():
            # crash-resume law: a cell whose verdict was atomically
            # written is COMPLETE; reloading it never re-consumes a slot
            rep = json.loads((cdir / "cell_verdict.json").read_text())
            used = max(used, int(rep["budget"]["used"]))
            cell_results[cid] = rep
            if rep["verdict"] == "PASS_I_STAGE_PENDING_DSR_E" and \
                    rep.get("dsr", {}).get("computed", {}).get("pass"):
                survivors.append(cid)
            log(f"scored cell {rep['budget']['used']}/3 (RESUMED, "
                f"atomic): {cid} verdict {rep['verdict']}")
            continue
        used += 1                      # observed slot consumed at START
        log(f"scored cell {used}/3 (streaming): {cid}")
        cdir.mkdir(parents=True, exist_ok=True)
        resume = (cdir / "ckpt_pass_a.json").exists()
        pa = se.CheckpointablePassA(
            cell, calendar, b1, b2, cdir, SPILL_QUOTA_BYTES, spy,
            resume=resume)
        # E2F-1 law: the FULL iterator is passed; resume skipping is
        # owned solely by the checkpointable pass (names_done) - never
        # pre-skipped here
        it_a = se.stream_iter_names(ctx, CACHE_DIR)

        def guard(where: str):
            live = rss_now()
            if live > RSS_INTERLOCK_BYTES:
                raise RuntimeError(
                    f"RSS_INTERLOCK at {where}: {live} > "
                    f"{RSS_INTERLOCK_BYTES} (TECHABORT: streaming "
                    f"resource breach; state preserved under {cdir})")
            if free_disk_bytes() < 2 * 1024 ** 3:
                raise RuntimeError(
                    f"DISK_INTERLOCK at {where}: free < 2 GiB")

        pa.run(it_a, checkpoint_every=256, guard=guard, log=log)
        pb = se.CheckpointablePassB(
            cell, calendar, b1, b2, cdir, SPILL_QUOTA_BYTES, spy,
            pa.result()["fired_dates"], pa.result()["_rev_rows"],
            resume=(cdir / "ckpt_pass_b.json").exists())
        it_b = se.stream_iter_names(ctx, CACHE_DIR)
        pb.run(it_b, checkpoint_every=256, guard=guard, log=log)

        stats = {k: acc.finalize() for k, acc in pa.books.items()}
        stats.update({k: acc.finalize() for k, acc in pb.books.items()})
        res_a = pa.result()
        res_b = pb.result()
        bundle = {
            "cell": cid, "H": int(cell["params"]["H"]),
            "stress": i_engine.STRESS_TIER,
            "candidate": stats["candidate"],
            "c_complement": stats["c_complement"],
            "r5_component": stats["r5_component"],
            "c_delay_h": stats["c_delay_h"],
            "c_random_timing": stats["c_random_timing"],
            "c_cal_hist": stats["c_cal_hist"],
            "c_reversal_plain": stats["c_reversal_plain"],
            "pit_mutation": res_a["pit_mutation"],
            "c_cal_hist_report": res_b["c_cal_hist_report"],
            "reversal_stats": res_b["reversal_stats"],
            "counts_cohort": res_b["counts_cohort"],
        }
        rep = se.adjudicate_candidate_stream(bundle, spy, calendar, b1, b2)
        rep["budget"] = {"used": used, "max": 3, "label": f"{used}/3"}
        # A7S14-2/A7S14-5: surfaced OUTSIDE the mirrored verdict dict
        # (the mirror must stay byte-equal to the frozen adjudication);
        # plan §14 count disclosure on every cell verdict
        rep["unpriceable_adj_price_legs"] = {
            "candidate": int(stats["candidate"].counts.get(
                "censored_unpriceable_adj_price", 0)),
            "law": "plan §14 DEGENERATE_ADJ_PRICE (censored BC-7 class; "
                   "excluded from numerator and included-at-marks)"}
        if rep["verdict"] == "PASS_I_STAGE_PENDING_DSR_E":
            # DSR wiring is FROZEN-IDENTICAL to e/e_run.py p4
            # (trial_sharpes = []): the 47-config trial set is
            # structurally uncomputable under plan §5 (no performance
            # for any configuration outside scored cells), so dsr_gate
            # returns insufficient_trials and a K6/Stage-A survivor
            # stays PASS_I_STAGE_PENDING_DSR_E - never a bookable
            # SURVIVORS outcome.  Inherited frozen property, disclosed
            # (A7 finding E2F-3); NOT changed by the remediation.
            dsr = adjudicate.dsr_gate(
                stats["candidate"].book_log, [], 47, 0.10,
                allow_scored=True)
            rep["dsr"]["computed"] = dsr
            rep["dsr"]["trial_set_law"] = (
                "frozen-identical wiring (e_run p4): trial_sharpes=[] "
                "structural insufficient_trials; the §5 ban makes the "
                "N=47 trial set uncomputable outside scored cells")
            if dsr.get("pass"):
                survivors.append(cid)
        digest = se.persist_p11(E2_DIR / "p11_series" / f"{cid}_candidate.jsonl",
                                stats["candidate"])
        rep["p11_series_sha256"] = digest
        # peak-RSS + resource evidence carried per cell
        rep["stream_resources"] = {
            "peak_rss_bytes": rss_peak_bytes(),
            "spill_bytes": sum(f.stat().st_size
                               for f in cdir.glob("*.f64"))}
        (cdir / "cell_verdict.json.tmp").write_text(
            json.dumps(rep, indent=1, sort_keys=True, default=str) + "\n")
        os.replace(cdir / "cell_verdict.json.tmp",
                   cdir / "cell_verdict.json")
        (cdir / "DONE").write_text(
            datetime.now(timezone.utc).isoformat() + "\n")
        cell_results[cid] = rep
        log(f"cell {cid} verdict: {rep['verdict']}")
        for st in stats.values():
            st.free_arrays()
        import gc
        gc.collect()
    return {"cells": cell_results, "survivors": survivors,
            "budget_used": used,
            "data_plane_preflight": ctx["preflight"]}


def _terminal_outcome(scored: dict) -> str:
    if scored["survivors"]:
        return ("STOCKS_SEARCH_V1_SURVIVORS_UNDER_RELAXED_BATTERY_"
                "R0_NOT_RUN_PBO_NOT_RUN")
    if any(c["verdict"].startswith("REJECT") for c in
           scored["cells"].values()):
        return "STOCKS_SEARCH_V1_REJECT_ALL"
    return "STOCKS_SEARCH_V1_INCOMPLETE_NOT_PROMOTABLE"


def write_verdict(payload: dict) -> None:
    tmp = VERDICT_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=1, sort_keys=True,
                              default=str) + "\n")
    os.replace(tmp, VERDICT_PATH)


# ------------------------------------------------------------------ main

def main() -> int:
    import signal
    signal.signal(
        signal.SIGTERM,
        lambda s, f: (_ for _ in ()).throw(SystemExit("RSS_INTERLOCK")))
    t0 = time.time()
    E2_DIR.mkdir(parents=True, exist_ok=True)
    log(f"{LANE} orchestrator start; pid {os.getpid()}")
    env = p0_env()
    log(f"env verified: HEAD {env['head'][:12]} branch "
        f"{env['branch']}; code_freeze files "
        f"{env['code_freeze_files']} ok")
    handle, beat_stop = p1_lock()
    log("heavy lock acquired + heartbeat thread running")
    result = {"status": "RUNNING"}
    write_verdict({"schema": "stocks_search_v1_e2_run_verdict@1",
                   "status": "RUNNING",
                   "started_utc": datetime.now(timezone.utc).isoformat()})
    try:
        preflight = p2_gate()
        cal = p3_calibration()
        if not cal["feasible"]:
            verdict = {
                "schema": "stocks_search_v1_e2_run_verdict@1",
                "status": "TECHABORT_PRESERVED",
                "stop_condition": "TECHABORT_STREAM_RESOURCE",
                "terminal_outcome": "STOCKS_SEARCH_V1_TECHABORT_PRESERVED",
                "calibration_stream": cal,
                "budget": {"used": 0, "max": 3, "label": "0/3"},
                "note": "streaming remediation resource interlock fired "
                        "BEFORE any scored computation; no slot consumed"}
            write_verdict(verdict)
            result = verdict
            return 0
        with RssWatchdog(RSS_INTERLOCK_BYTES):
            scored = p4_scored_stream(_read_go_phrase())
        verdict = {
            "schema": "stocks_search_v1_e2_run_verdict@1",
            "status": "SCORED_RUN_COMPLETE",
            "engine": "STREAMING_E2 (owner remediation decision (a); "
                      "equivalence + A7 prelaunch audit under "
                      "e2/equivalence_verdict.json, e2/audits/)",
            "terminal_outcome": _terminal_outcome(scored),
            "cells": scored["cells"],
            "survivors": scored["survivors"],
            "budget": {"used": scored["budget_used"], "max": 3,
                       "label": f"{scored['budget_used']}/3"},
            "r0_status": "R0_NOT_RUN",
            "pbo_status": "PBO_NOT_RUN",
            "wall_seconds": round(time.time() - t0, 1),
        }
        write_verdict(verdict)
        result = verdict
        log(f"verdict written: {verdict['status']} / "
            f"{verdict['terminal_outcome']}")
        return 0
    except SystemExit as e:
        log(f"interlock exit: {e}")
        result = {"status": "TECHABORT_PRESERVED"}
        write_verdict({
            "schema": "stocks_search_v1_e2_run_verdict@1",
            "status": "TECHABORT_PRESERVED",
            "stop_condition": "RSS_INTERLOCK",
            "terminal_outcome": "STOCKS_SEARCH_V1_TECHABORT_PRESERVED",
            "note": "streaming resource interlock; state preserved; "
                    "budget intact for the cells not started"})
        return 9
    except Exception as e:
        tb = traceback.format_exc()
        log(f"FAIL-CLOSED EXCEPTION: {e!r}\n{tb}")
        from i_engine import DataPlaneMismatch, FrozenShaMismatch
        stop = ("INPUT_MISMATCH" if isinstance(e, DataPlaneMismatch)
                else "FROZEN_SHA_MISMATCH" if isinstance(e, FrozenShaMismatch)
                else "TECHABORT")
        result = {"status": "STOPPED"}
        write_verdict({"schema": "stocks_search_v1_e2_run_verdict@1",
                       "status": "STOPPED", "stop_condition": stop,
                       "failure_record": {"repr": repr(e),
                                          "traceback": tb}})
        return 2
    finally:
        try:
            status = ("FINISHED" if isinstance(result, dict) and
                      result.get("status") == "SCORED_RUN_COMPLETE"
                      else "TECHABORT" if isinstance(result, dict) and
                      result.get("status") == "TECHABORT_PRESERVED"
                      else "FAILED")
            handle.release(status=status,
                           note=f"{LANE}: {result.get('status') if isinstance(result, dict) else 'unknown'}")
            log("heavy lock released")
        except Exception as e:
            log(f"lock release error: {e!r}")
        beat_stop.set()
        log(f"orchestrator exit after {time.time() - t0:.0f}s")


def _read_go_phrase() -> str:
    """The GO phrase arrives via the dispatch environment variable
    SSEARCH_E2_GO_PHRASE (never argv, never logged).  A1 sets it only
    from the owner's exact typed phrase in the GO turn."""
    phrase = os.environ.get("SSEARCH_E2_GO_PHRASE", "")
    if phrase != "GO STOCKS SEARCH V1 SCORED EXECUTION":
        raise RuntimeError(
            "GO gate: SSEARCH_E2_GO_PHRASE absent/incorrect - the scored "
            "path refuses (P-8; early or paraphrased GO dies unconsumed)")
    return phrase


# ------------------------------------------------------ verification modes

def _mode_probe_stream_rss() -> None:
    import i_engine
    import i_stream_engine as se
    from equivalence import real_calendar_spy, synthetic_cohort
    cal, b1, b2, spy = real_calendar_spy()
    names = synthetic_cohort(cal, spy, n_names=260, seed=7)
    cell = i_engine.FROZEN_CELLS[0]
    spill = E2_DIR / "probe_spill"
    t0 = time.time()
    pa, _ = se.stream_cell_pass_a(
        iter(sorted(names.items())), cell, cal, b1, b2, spill,
        SPILL_QUOTA_BYTES, spy)
    pb = se.stream_cell_pass_b(
        iter(sorted(names.items())), cell, cal, b1, b2, spill,
        SPILL_QUOTA_BYTES, pa["fired_dates"], pa["_rev_rows"], spy)
    stats = {k: acc.finalize() for k, acc in pa["books"].items()}
    stats.update({k: acc.finalize() for k, acc in pb["books"].items()})
    bundle = dict(pa["books"])
    bundle.update(pb["books"])
    import gc
    gc.collect()
    peak = rss_peak_bytes()
    print("PROBE_JSON:" + json.dumps({
        "mode": "stream-rss", "n_names": len(names),
        "cell": cell["config_id"],
        "peak_rss_bytes": peak,
        "elapsed_s": round(time.time() - t0, 1),
        "names_per_second": round(len(names) / (time.time() - t0), 3)}))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        a = sys.argv[1]
        if a == "--run":
            sys.exit(main())
        if a == "--probe-stream-rss":
            _mode_probe_stream_rss()
            sys.exit(0)
        if a == "--equivalence":
            rc = subprocess.call([sys.executable,
                                  str(E2_DIR / "equivalence.py")])
            sys.exit(rc)
        if a == "--selfcheck":
            rc = subprocess.call([sys.executable,
                                  str(E2_DIR / "selfcheck.py")])
            sys.exit(rc)
        print(f"unknown mode {a}", file=sys.stderr)
        sys.exit(2)
    sys.exit(main())
