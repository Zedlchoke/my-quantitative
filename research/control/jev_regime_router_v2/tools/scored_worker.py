#!/usr/bin/env python3
"""JRV2 scored worker — the ONE atomic run of the 18 frozen scored cells
under the machine-wide heavy lock. Owner GO 'GO JEV REGIME V2 SCORED
BACKTEST' (authority SCORED_GO.json committed at code freeze 13ecc2e6).
Zero provider calls; cached decisions only."""
from __future__ import annotations

import pathlib
import signal
import subprocess
import sys
import threading

REPO = pathlib.Path("/Users/hoangminhlong/my-quantitative")
CYCLE_DIR = REPO / ".worktrees/jev-regime-router-v2/integration/research/control/jev_regime_router_v2"
sys.path.insert(0, str(REPO / "research"))

from governance import heavy_lock  # noqa: E402

PY = str(REPO / ".venv/bin/python")
TOKEN = "GO JEV REGIME V2 SCORED BACKTEST"
CMD = [PY, "-c",
       "import sys; sys.path.insert(0, '.'); from jrv2 import run; "
       "sys.argv = ['run.py', 'backtest', '--scored-go-token', "
       "'GO JEV REGIME V2 SCORED BACKTEST']; run.main()"]


def main() -> int:
    handle = heavy_lock.acquire(
        cycle_id="JEV-REGIME-ROUTER-V2",
        role="quant-implementer/jrv2-scored",
        worktree=str(REPO / ".worktrees/jev-regime-router-v2/integration"),
        command=CMD,
        expected_artifacts=[str(CYCLE_DIR / "runtime/scored/scored_summary.json")],
    )
    print("lock acquired; scored run starting", flush=True)
    child: dict = {"proc": None}

    def on_term(signum, frame):
        p = child.get("proc")
        if p is not None and p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=30)
            except Exception:
                pass
        handle.release(status="TECHABORT", note=f"signal {signum} during scored run")
        raise SystemExit(143)

    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_term)

    stop = threading.Event()

    def hb() -> None:
        n = 0
        while not stop.wait(30):
            n += 1
            try:
                handle.heartbeat(extra={"phase": "scored", "ticks": n})
            except Exception:
                pass

    t = threading.Thread(target=hb, daemon=True)
    t.start()
    log = CYCLE_DIR / "runtime" / "scored_run.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    try:
        with log.open("w") as lf:
            proc = subprocess.Popen(CMD, cwd=str(CYCLE_DIR), stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
            child["proc"] = proc
            out, _ = proc.communicate()
            child["proc"] = None
            lf.write(out or "")
            rc = proc.returncode
        print(f"scored run exit={rc}; log {log}", flush=True)
        handle.release(status="FINISHED" if rc == 0 else "TECHABORT",
                       note=f"jrv2 scored run exit {rc}")
        return rc
    except BaseException as e:
        p = child.get("proc")
        if p is not None and p.poll() is None:
            p.terminate()
        handle.release(status="TECHABORT", note=f"worker exception {type(e).__name__}")
        raise
    finally:
        stop.set()


if __name__ == "__main__":
    sys.exit(main())
