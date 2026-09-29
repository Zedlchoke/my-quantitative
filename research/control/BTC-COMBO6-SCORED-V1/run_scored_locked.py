"""BTC-COMBO6 scored execution under the machine-wide heavy lock.

Two-key law: this wrapper MUST NOT be run until (1) fresh-context A7 prelaunch
verdict AUTHORIZED (0 unresolved HIGH/CRITICAL) is on disk at
audits/A7_PRELAUNCH.md (worktree copy), and (2) the owner scored-GO authority
is recorded in auth/GO_RECORDED.json (owner standing directive 2026-09-29,
consumed at the gate after A7). Pattern: DAYTRADER-100-V1 run_scored_locked.
"""
from __future__ import annotations

import subprocess
import sys
import time

ROOT = "/Users/hoangminhlong/my-quantitative"
WT = f"{ROOT}/.worktrees/btc-combo6-scored-v1/integration"
sys.path.insert(0, f"{ROOT}/research")          # governance package
from governance import heavy_lock               # noqa: E402

CMD = [f"{ROOT}/.venv/bin/python",
       f"{WT}/research/btcombo6/run_btcombo6.py",
       "--mode", "scored", "--stress-all"]

ARTIFACTS = [
    f"{WT}/research/control/BTC-COMBO6-SCORED-V1/scored/btcombo6_scored_stress1.0.json",
    f"{WT}/research/control/BTC-COMBO6-SCORED-V1/scored/btcombo6_scored_stress1.5.json",
    f"{WT}/research/control/BTC-COMBO6-SCORED-V1/scored/btcombo6_scored_stress2.0.json",
]

try:
    handle = heavy_lock.acquire(
        cycle_id="BTC-COMBO6-SCORED-V1", role="E_SCORED_CELLS", worktree=WT,
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
