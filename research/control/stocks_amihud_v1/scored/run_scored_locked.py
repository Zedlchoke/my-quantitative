"""STOCKS-AMIHUD-V1 scored-cell launcher (control-plane, NOT engine code).

Executes the frozen engine under the machine-wide heavy lock, on the clean
tree at the authorized code freeze. Verifies before running: clean tree,
exact HEAD, freeze-chain (code delta vs b87c1ea7 = audit artifacts only).
Releases the lock in finally with status + note. The engine package
(samv1) is untouched by this launcher (A7 prelaunch L-7 honored).
"""
from __future__ import annotations

import subprocess
import sys
import traceback
from pathlib import Path

REPO = Path("/Users/hoangminhlong/my-quantitative")
sys.path.insert(0, str(REPO))
from research.governance import heavy_lock  # noqa: E402

WT = REPO / ".worktrees/stocks-amihud-v1/integration"
CODE_FREEZE = "b87c1ea74447b51aaa0efacca9a864628639341e"
RUN_CELLS = WT / "research/control/stocks_amihud_v1/impl/samv1/run_cells.py"
PY = REPO / ".venv/bin/python"


def sh(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True,
                          check=True).stdout.strip()


def main() -> int:
    head = sh("git", "-C", str(WT), "rev-parse", "HEAD")
    dirty = sh("git", "-C", str(WT), "status", "--porcelain=v1")
    if dirty:
        print(f"REFUSED: dirty tree: {dirty}", file=sys.stderr)
        return 4
    # freeze-chain law: since the audited code freeze, ONLY control-plane /
    # audit artifacts may differ — any engine or test change refuses.
    changed = [p for p in sh("git", "-C", str(WT), "diff", "--name-only",
                             f"{CODE_FREEZE}..{head}").split("\n") if p]
    engine_changed = [p for p in changed
                      if "/impl/samv1/" in f"/{p}" or "/impl/tests/" in f"/{p}"]
    if engine_changed:
        print(f"REFUSED: engine/test delta since freeze: {engine_changed}",
              file=sys.stderr)
        return 4
    print(f"freeze-chain OK: HEAD {head}; non-engine delta since "
          f"{CODE_FREEZE[:8]}: {changed}", flush=True)
    handle = heavy_lock.acquire(
        cycle_id="STOCKS-AMIHUD-V1",
        role="scored-cells",
        worktree=str(WT),
        command=[str(PY), str(Path(__file__))],
        expected_artifacts=[str(WT / "research/control/stocks_amihud_v1/"
                                "scored/scored_records.json")],
    )
    try:
        r = subprocess.run([str(PY), str(RUN_CELLS), "--mode", "scored"],
                           cwd=str(WT))
        if r.returncode != 0:
            handle.release(status="FAILED",
                           note=f"run_cells scored exit {r.returncode}")
            return r.returncode
        handle.release(status="FINISHED",
                       note="3 frozen cells computed; scored_records.json written")
        return 0
    except Exception:
        tail = traceback.format_exc()[-1200:]
        handle.release(status="TECHABORT", note=f"stderr_tail={tail[-600:]}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
