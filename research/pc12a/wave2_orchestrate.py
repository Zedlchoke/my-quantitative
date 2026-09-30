"""Wave-2 TRAIN-diagnostics orchestrator — holds the MACHINE-WIDE heavy
lock for the whole multi-pass job and runs the per-symbol run_diag passes
in parallel worker processes (one heavy job; children belong to it).

Groups (memory-bounded: <=5 concurrent processes, <=2.5GB panels):
  EUR   EURUSD (11 legs)
  GBPA  GBPUSD first half / GBP B second half (parallel split: GBPUSD is
        the long pole at ~31 legs x ~80s solo)
  JPY   USDJPY (11 legs)
  H1    AUDUSD + USDCAD (9 legs, ANC H1 adapter via PC12A_H1_PARQUETS)

Phases: MAIN (8 folds, tier 1.0) -> X2 (fold-7 window, tier 2.0) ->
assemble (controls + complementarity + ledger append, in-process).

Runtime disclosure is written into DIAG_MANIFEST.json ("orchestrator").
"""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import time

ROOT = "/Users/hoangminhlong/my-quantitative"
WORKTREE = os.path.join(
    ROOT, ".worktrees/portfolio-composite-12assets-100k-v1/integration")
PY = os.path.join(ROOT, ".venv/bin/python")
CYCLE = "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1"
OUT = os.path.join(WORKTREE, "research/control", CYCLE, "diagnostics")
LEDGER = os.path.join(WORKTREE, "research/control", CYCLE,
                      "TRIAL_LEDGER.jsonl")
LEGS = "/tmp/w2_diag_legs"

H1_PARQUETS = json.dumps({
    "AUDUSD": "/Users/hoangminhlong/my-quantitative/.worktrees/"
              "erp1-tracka-cohort-1/repro_twin/research/control/"
              "ERP1-TRACKA-COHORT-1/data_local/derived/"
              "bars1h_ANC_AUDUSD.parquet",
    "USDCAD": "/Users/hoangminhlong/my-quantitative/.worktrees/"
              "erp1-tracka-cohort-1/repro_twin/research/control/"
              "ERP1-TRACKA-COHORT-1/data_local/derived/"
              "bars1h_ANC_USDCAD.parquet",
})


def gbp_gids():
    """All GBPUSD legs (S-legs AND the VC2/VC3-GBPUSD class arms — the
    first cut globbed GBPUSD-*.json only and dropped the 2 VC arms)."""
    import glob

    gids = sorted(
        os.path.basename(p)[:-5] for p in glob.glob(
            os.path.join(LEGS, "GBPUSD-*.json"))
        + glob.glob(os.path.join(LEGS, "VC*-GBPUSD.json")))
    return gids[:len(gids) // 2], gids[len(gids) // 2:]


def spawn(cmd: list, env: dict, tag: str, logfh):
    logfh.write(f"[{dt.datetime.now().isoformat()}] spawn {tag}: "
                f"{' '.join(cmd[:8])}...\n")
    logfh.flush()
    return subprocess.Popen(cmd, cwd=WORKTREE, env=env,
                            stdout=logfh, stderr=subprocess.STDOUT)


def run_group(pass_type: str, log_path: str,
              group_filter: str = "all") -> float:
    t0 = time.time()
    env = dict(os.environ)
    env.pop("PC12A_H1_PARQUETS", None)
    a, b = gbp_gids()
    groups = [
        ("EUR", ["--symbols", "EURUSD"], {}),
        ("GBPA", ["--symbols", "GBPUSD", "--gids", ",".join(a)], {}),
        ("GBPB", ["--symbols", "GBPUSD", "--gids", ",".join(b)], {}),
        ("JPY", ["--symbols", "USDJPY"], {}),
        ("H1", ["--symbols", "AUDUSD,USDCAD"],
         {"PC12A_H1_PARQUETS": H1_PARQUETS}),
    ]
    if group_filter == "main_vc_only":
        # resume-only gap filler: the first orchestration's split glob
        # dropped the 2 GBPUSD VC arms from MAIN
        groups = [("GBPVC", ["--symbols", "GBPUSD", "--gids",
                             "VC2-LVNFAIL-GBPUSD,VC3-POCMAG-GBPUSD"], {})]
    with open(log_path, "a", encoding="utf-8") as logfh:
        procs = []
        for tag, extra, extra_env in groups:
            e = dict(env)
            e.update(extra_env)
            cmd = [PY, "-m", "research.pc12a.run_diag",
                   "--legs", LEGS, "--out", OUT, "--mode", "pass",
                   "--pass-type", pass_type, "--file-tag", tag] + extra
            procs.append((tag, spawn(cmd, e, tag, logfh)))
        fails = []
        for tag, p in procs:
            rc = p.wait()
            logfh.write(f"[{dt.datetime.now().isoformat()}] {tag} "
                        f"exit {rc}\n")
            if rc != 0:
                fails.append(tag)
        if fails:
            raise RuntimeError(f"{pass_type} pass failures: {fails}")
    return round(time.time() - t0, 1)


def main() -> int:
    sys.path.insert(0, os.path.join(ROOT, "research"))
    from governance import heavy_lock

    resume = "--resume" in sys.argv
    t0 = time.time()
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    log_path = os.path.join(OUT, "ORCHESTRATOR_LOG.txt")
    os.makedirs(OUT, exist_ok=True)

    lock = heavy_lock.acquire(
        cycle_id=CYCLE, role="stage-a-wave2-train-diag",
        worktree=WORKTREE,
        command=[PY, "-m", "research.pc12a.wave2_orchestrate"]
        + (["--resume"] if resume else []),
        expected_artifacts=[
            os.path.join(OUT, "COMPLEMENTARITY_TRAIN.json")])
    timings = {}
    status = "FINISHED"
    note = ""
    try:
        # resume: the 60-leg MAIN grid is already on disk from the first
        # (killed) orchestration; only the 2 GBPUSD VC arms were missed by
        # the original split glob, so MAIN reruns as GBPVC-only
        if resume:
            timings["MAIN_GBPVC_seconds"] = run_group(
                "MAIN", log_path, group_filter="main_vc_only")
        else:
            timings["MAIN_group_seconds"] = run_group("MAIN", log_path)
        timings["X2_group_seconds"] = run_group("X2", log_path)
        t = time.time()
        rc = subprocess.run(
            [PY, "-m", "research.pc12a.run_diag", "--legs", LEGS,
             "--out", OUT, "--mode", "assemble", "--ledger", LEDGER],
            cwd=WORKTREE, env=dict(os.environ)).returncode
        timings["assemble_seconds"] = round(time.time() - t, 1)
        if rc != 0:
            raise RuntimeError(f"assemble exit {rc}")
        timings["total_seconds"] = round(time.time() - t0, 1)
    except Exception as exc:  # noqa: BLE001
        status, note = "FAILED", f"{type(exc).__name__}: {exc}"[:400]
        raise
    finally:
        man_path = os.path.join(OUT, "DIAG_MANIFEST.json")
        man = {}
        if os.path.exists(man_path):
            man = json.load(open(man_path, encoding="utf-8"))
        man["orchestrator"] = {
            "started_utc": started, "status": status, "note": note,
            "timings": timings,
            "lock": {"method": "governance/heavy_lock.acquire "
                               "(root checkout research/governance)",
                     "role": "stage-a-wave2-train-diag",
                     "held_for_whole_job": True,
                     "parallel_workers": 5},
        }
        with open(man_path, "w", encoding="utf-8") as fh:
            json.dump(man, fh, sort_keys=True, indent=1)
            fh.write("\n")
        lock.release(status=status, note=note or json.dumps(timings))
    print(json.dumps({"done": True, "timings": timings}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
