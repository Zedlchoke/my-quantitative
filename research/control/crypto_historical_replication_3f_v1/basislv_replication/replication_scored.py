"""BASISLV window-fold replication SCORED launcher (DO NOT RUN until the
cycle's own A7 prelaunch artifact authorizes it).

Cycle CRYPTO-HISTORICAL-REPLICATION-3F-V1, namespace basislv_replication.
8 cells = {Y2021, Y2022, Y2023, Y2020P} x {anchor BASISLV-PREMFADE-28D,
control BASISLV-PREMFADE-28D-INV}; per cell one subprocess running the FROZEN
``run_strategy`` over the window-fold bound ``BasislvWindowFoldPlugin``
(the proven chr3f ILLIQ launcher/cell-runner structure).

SELF-GATE: refuses to run unless ``basislv_replication/A7_PRELAUNCH.json``
exists with ``verdict == "AUTHORIZED"`` (the cycle's own prelaunch gate for
THIS lane; it does not exist yet -- the artifact is written by the A7
review, never by the implementer lane).  Heavy machine-wide lock held for
the whole sweep (cycle CRYPTO-HISTORICAL-REPLICATION-3F-V1, role
scored-cells).  Outputs cycle-local under ``basislv_replication/scored_out/``;
resume-safe via ``basislv_replication/scored_status.json``.

LABELS on every status row (exactly three, per the lane brief):
  REPLICATION_NOT_PROSPECTIVE
      historical replication, never a forward signal;
  EQUIVALENCE_BIT_EXACT_ORIGINAL_WINDOW
      the frozen anchor was reproduced bit-exactly on its ORIGINAL window by
      basislv_equivalence/EQUIV_VERDICT.json (verdict EQUIVALENT, all
      canonical surfaces abs_diff 0.0, run hashes equal per arm);
  UNIVERSE_LISTED_AT_WINDOW_START
      context-marks disclosure ONLY: the scored universe stays the frozen
      19 at every window (no A4-equivalent universe amendment); only the
      context-only buy-and-hold marks are narrowed to symbols listed at the
      window start (benchmark_context_symbols; enters_denominator False).

DESIGN DECISIONS THE A7 REVIEW MUST CONFIRM (implemented + disclosed in
gated_plugin.py / replication_data.py; measured by dryrun_report.json):
  D1 flat-refusal convention: stamps with < MIN_ELIGIBLE (12) eligible names
     answer the flat refusal-counted book (INSUFFICIENT_ELIGIBLE_REFUSAL)
     instead of aborting the cell -- the frozen strategy's "the stamp
     refuses and the refusal is counted" schedule-level semantics, mirroring
     the frozen fold-terminal force-flat precedent.  Measured: Y2023 carries
     exactly 4 such stamps (2023-11-13..2023-12-04, n_eligible=0), caused by
     ONE systematic missing basis bucket (open 2023-11-10T03:45Z, 15/19
     names).  Alternative: fail-closed cell abort.
  D2 gap-tolerant basis load: the single 2023-11-10T03:45Z bucket is NaN and
     the engine's per-slot eligibility refuses straddling formation windows
     (deviation from the A9F restage loader's zero-gap refusal, which would
     refuse to load the 4.6-year re-fetch at all).
  D3 fold-terminal executability check re-scoped to symbols whose bar series
     covers the stamp (the frozen all-universe check would fail-closed on
     never-listed names that can never be held at that stamp).
  D4 bars loaded at each symbol's FULL catalog coverage (superset of the
     frozen -7d/+3d per-fold window; only on-schedule stamps consumed; 7 of
     the 19 names have no bars at all inside Y2021/Y2022).
  D5 funding consumed AS-IS from scan_2026 (no frozen-count authority on the
     B window); ticks = fapi exchangeInfo metadata recorded in the b20 build
     report (current metadata, disclosed convention).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

R = Path("/Users/hoangminhlong/my-quantitative")
sys.path.insert(0, str(R))
from research.governance import heavy_lock  # noqa: E402

HERE = Path(__file__).resolve().parent
CD = HERE.parent
V14_ROOT = CD / "recovered/v14_root"
PY = R / ".venv/bin/python"

A7_PATH = HERE / "A7_PRELAUNCH.json"
STATUS_PATH = HERE / "scored_status.json"
OUT_ROOT = HERE / "scored_out"

CYCLE = "CRYPTO-HISTORICAL-REPLICATION-3F-V1"
LABELS = [
    "REPLICATION_NOT_PROSPECTIVE",
    "EQUIVALENCE_BIT_EXACT_ORIGINAL_WINDOW",
    "UNIVERSE_LISTED_AT_WINDOW_START",
]
LABELS_NOTE = (
    "UNIVERSE_LISTED_AT_WINDOW_START is a context-marks disclosure only "
    "(scored universe = frozen 19; benchmark_context_symbols narrowed to "
    "listed-at-start, enters_denominator False)"
)
AUTHORITY = "preregistered replication plan (section 3) + A7 prelaunch AUTHORIZED"


def main() -> int:
    v = json.loads(A7_PATH.read_text()) if A7_PATH.exists() else {}
    if v.get("verdict") != "AUTHORIZED":
        print(
            f"REFUSED: A7 BASISLV-replication prelaunch verdict = "
            f"{v.get('verdict', 'MISSING')} (A7_PRELAUNCH.json not present "
            "or not AUTHORIZED; the scored sweep may not run)"
        )
        return 5
    status = json.loads(STATUS_PATH.read_text()) if STATUS_PATH.exists() else {"cells": []}
    done = {
        c["cell_id"]
        for c in status["cells"]
        if c.get("rc") == 0 and "outcome_class" not in c
    }
    handle = heavy_lock.acquire(
        cycle_id=CYCLE,
        role="scored-cells",
        worktree=str(R / ".worktrees/crypto-historical-replication-3f-v1/integration"),
        command=[str(PY), str(Path(__file__))],
        expected_artifacts=[str(STATUS_PATH)],
    )
    # v14-context constants via subprocess (replication_data imports the
    # v14_root research package; the launcher runs in root governance context
    # and must not collide on the cached `research` package)
    import json as _json
    _probe = subprocess.run(
        [str(PY), "-c",
         "import sys, json; sys.path.insert(0, r'" + str(CD) + "'); "
         "from replication_data import ARMS, FOLDS; "
         "print(json.dumps({'ARMS': ARMS, 'FOLDS': FOLDS}))"],
        capture_output=True, text=True,
        env=dict(os.environ, PYTHONPATH=str(V14_ROOT)))
    if _probe.returncode != 0:
        print("REFUSED: constants probe failed:", _probe.stderr[-300:])
        return 7
    _c = _json.loads(_probe.stdout.strip().splitlines()[-1])
    ARMS = [(a, b) for a, b in _c["ARMS"]]
    FOLDS = [(f, w0, w1) for f, w0, w1 in _c["FOLDS"]]

    try:
        for fold, w0, w1 in FOLDS:
            for arm_label, arm_id in ARMS:
                cell_id = f"CHR3F-BASISLV-{fold}-{arm_label}"
                if cell_id in done:
                    continue
                t0 = time.time()
                env = dict(os.environ, PYTHONPATH=str(V14_ROOT))
                r = subprocess.run(
                    [
                        str(PY),
                        str(HERE / "basislv_cell_runner.py"),
                        "--fold", fold,
                        "--window-start", w0,
                        "--window-end", w1,
                        "--arm-id", arm_id,
                        "--out", str(OUT_ROOT / cell_id),
                    ],
                    cwd=str(HERE),
                    capture_output=True,
                    text=True,
                    env=env,
                )
                OUT_ROOT.mkdir(parents=True, exist_ok=True)
                (OUT_ROOT / f"{cell_id}.log").write_text(r.stdout + "\n" + r.stderr)
                metrics: dict = {}
                if r.returncode == 0 and r.stdout.strip():
                    try:
                        metrics = json.loads(r.stdout.strip().splitlines()[-1])
                    except Exception:
                        metrics = {}
                row = {
                    "cell_id": cell_id,
                    "fold": fold,
                    "window": [w0, w1],
                    "arm": arm_label,
                    "arm_id": arm_id,
                    "namespace": "basislv_replication",
                    "labels": list(LABELS),
                    "labels_note": LABELS_NOTE,
                    "authority": AUTHORITY,
                    "rc": r.returncode,
                    "runtime_s": round(time.time() - t0, 1),
                    "utc": datetime.now(timezone.utc).isoformat(),
                    "net_return_sum": metrics.get("net_return_sum"),
                    "position_pf": metrics.get("position_pf"),
                    "max_drawdown": metrics.get("max_drawdown"),
                    "n_positions": metrics.get("n_positions"),
                    "n_insufficient_eligible_refusals": metrics.get(
                        "n_insufficient_eligible_refusals"
                    ),
                    "n_fold_terminal_force_flats": metrics.get(
                        "n_fold_terminal_force_flats"
                    ),
                    "eligible_min": metrics.get("eligible_min"),
                    "eligible_max": metrics.get("eligible_max"),
                    "design_decisions_for_a7": ["D1", "D2", "D3", "D4", "D5"],
                }
                status["cells"].append(row)
                STATUS_PATH.write_text(json.dumps(status, indent=1))
                print(
                    "CELL", cell_id, "rc", r.returncode,
                    "net", row["net_return_sum"],
                    "pf", row["position_pf"],
                    "refusals", row["n_insufficient_eligible_refusals"],
                    flush=True,
                )
    finally:
        handle.release()
    print("BASISLV REPLICATION SCORED SWEEP COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
