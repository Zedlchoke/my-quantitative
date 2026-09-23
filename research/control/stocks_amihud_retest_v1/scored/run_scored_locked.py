"""RETEST-V1 scored launcher (control-plane). Owner standing directive 2026-09-23
(§0a) + A7 prelaunch AUTHORIZED (both keys) substitute the interactive GO for
THIS cycle only (adjudication B1..B8). Freeze-verified, heavy-locked."""
from __future__ import annotations
import subprocess, sys, traceback
from pathlib import Path
REPO = Path("/Users/hoangminhlong/my-quantitative")
sys.path.insert(0, str(REPO))
from research.governance import heavy_lock  # noqa: E402
WT = REPO / ".worktrees/stocks-amihud-retest-v1/integration"
CODE_FREEZE = "fc233dc028d840f1a51637eb9339adeaa1b60931"
RUN = WT / "research/control/stocks_amihud_retest_v1/impl/samv1r/run_cells.py"
PY = REPO / ".venv/bin/python"
def sh(*a):
    return subprocess.run(a, capture_output=True, text=True, check=True).stdout.strip()
def main() -> int:
    head = sh("git", "-C", str(WT), "rev-parse", "HEAD")
    dirty = sh("git", "-C", str(WT), "status", "--porcelain=v1")
    if dirty:
        print(f"REFUSED: dirty tree: {dirty}", file=sys.stderr); return 4
    changed = [p for p in sh("git", "-C", str(WT), "diff", "--name-only",
                             f"{CODE_FREEZE}..{head}").split("\n") if p]
    engine_changed = [p for p in changed if "/impl/samv1r/" in f"/{p}"
                      or "/impl/tests/" in f"/{p}"]
    if engine_changed:
        print(f"REFUSED: engine/test delta since freeze: {engine_changed}",
              file=sys.stderr); return 4
    print(f"freeze-chain OK: HEAD {head}; non-engine delta: {changed}", flush=True)
    handle = heavy_lock.acquire(
        cycle_id="STOCKS-AMIHUD-RETEST-V1", role="scored-cells",
        worktree=str(WT), command=[str(PY), str(Path(__file__))],
        expected_artifacts=[str(WT / "research/control/stocks_amihud_retest_v1/"
                                "scored/scored_records_retest.json")])
    try:
        r = subprocess.run([str(PY), str(RUN), "--mode", "scored"], cwd=str(WT))
        if r.returncode != 0:
            handle.release(status="FAILED", note=f"exit {r.returncode}")
            return r.returncode
        handle.release(status="FINISHED",
                       note="3 RETEST cells computed under the owner standing "
                            "directive + A7 prelaunch substitution (B1..B8)")
        return 0
    except Exception:
        tail = traceback.format_exc()[-1000:]
        handle.release(status="TECHABORT", note=f"stderr_tail={tail[-600:]}")
        return 3
if __name__ == "__main__":
    raise SystemExit(main())
