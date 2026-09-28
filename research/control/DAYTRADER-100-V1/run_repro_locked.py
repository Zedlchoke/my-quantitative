"""DT100 scored execution under the machine-wide heavy lock (GO consumed).

GO DAYTRADER 100 V1 SCORED EXECUTION — typed verbatim at the gate 2026-09-28,
recorded in auth/GO_RECORDED.json (two-key complete). This wrapper acquires
the governance heavy lock, runs the scored pass (stress x1.0/x1.5/x2.0 in one
data load), and releases with FINISHED/FAILED in `finally`.
"""
from __future__ import annotations

import subprocess
import sys
import time

ROOT = "/Users/hoangminhlong/my-quantitative"
WT = f"{ROOT}/.worktrees/daytrader-100-v1/integration"
sys.path.insert(0, f"{ROOT}/research")          # governance package
from governance import heavy_lock               # noqa: E402

CMD = [f"{ROOT}/.venv/bin/python",
       f"{WT}/research/daytrader100/run_dt100.py",
       "--mode", "scored", "--stress-all", "--out", f"{WT}/research/control/DAYTRADER-100-V1/scored_repro"]

ARTIFACTS = [
    f"{WT}/research/control/DAYTRADER-100-V1/scored/dt100_scored_stress1.0.json",
]

try:
    handle = heavy_lock.acquire(
        cycle_id="DAYTRADER-100-V1", role="R_REPRODUCTION", worktree=WT,
        command=CMD, expected_artifacts=ARTIFACTS)
except Exception as e:  # noqa: BLE001 — busy/drift both fail closed, recorded
    print(f"NOT_RUN_RESOURCE_CONFLICT / CONTROL_STATE_DRIFT: {e}", file=sys.stderr)
    raise SystemExit(75)

t0 = time.time()
try:
    with handle:
        handle.heartbeat({"phase": "scored stress-all pass"})
        rc = subprocess.call(CMD, cwd=WT)
        handle.heartbeat({"phase": "done", "rc": rc, "seconds": round(time.time() - t0, 1)})
        print(f"SCORED_RC={rc} seconds={round(time.time() - t0, 1)}")
        raise SystemExit(rc)
except SystemExit:
        raise
except Exception as e:  # noqa: BLE001
    print(f"FAILED: {e}", file=sys.stderr)
    raise SystemExit(1)
