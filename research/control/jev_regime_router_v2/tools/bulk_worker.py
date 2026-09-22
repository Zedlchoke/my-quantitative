#!/usr/bin/env python3
"""JRV2 bulk replay worker — all 3 cells under one heavy-lock lease
(owner GO 'GO JEV REGIME V2 BULK HISTORICAL REPLAY' 2026-09-22).

V1 lessons applied:
- SIGTERM handling: the replay child runs in THIS process's process group
  via a session-boundary; on SIGTERM/INT we terminate the child FIRST,
  wait, then release the lock honestly (never orphan an appender).
- Heartbeat every 30 s carrying per-cell decision counts.
- Cells sequential: BTC_H1 -> BTC_H4 -> SPY_D1; cache-first (the 100
  preview states are pre-seeded into the BTC_H1 cache by the launcher).
"""
from __future__ import annotations

import json
import os
import pathlib
import signal
import subprocess
import sys
import threading
import time

REPO = pathlib.Path("/Users/hoangminhlong/my-quantitative")
CYCLE_DIR = REPO / ".worktrees/jev-regime-router-v2/integration/research/control/jev_regime_router_v2"
sys.path.insert(0, str(REPO / "research"))

from governance import heavy_lock  # noqa: E402

PY = str(REPO / ".venv/bin/python")
CELLS = ["BTC_H1", "BTC_H4", "SPY_D1"]
RUN_CMD = (
    "import sys; sys.path.insert(0, '.'); from jrv2 import run; "
    "sys.argv = ['run.py', 'replay', '--cell', '{cell}']; run.main()"
)


def load_key_silently() -> None:
    for line in (REPO / ".env").read_text().splitlines():
        if line.startswith("TYPESAFE_API_KEY="):
            val = line.split("=", 1)[1].strip().strip('"').strip("'")
            if val:
                os.environ["TYPESAFE_API_KEY"] = val
            return
    raise SystemExit("BLOCKED_CREDENTIAL: TYPESAFE_API_KEY absent in .env")


def cell_decisions_path(cell: str) -> pathlib.Path:
    name = {"BTC_H1": "btcusdt_h1", "BTC_H4": "btcusdt_h4", "SPY_D1": "spy_d1"}.get(cell, cell.lower())
    for cand in (f"decisions_{cell}.jsonl", f"decisions_{name}.jsonl"):
        p = CYCLE_DIR / "runtime" / "replay" / cell / cand
        glob = list((CYCLE_DIR / "runtime" / "replay" / cell).glob(cand)) if (CYCLE_DIR / "runtime" / "replay" / cell).exists() else []
        if p.exists() or glob:
            return (glob[0] if glob else p)
    return CYCLE_DIR / "runtime" / "replay" / cell / f"decisions_{cell}.jsonl"


def main() -> int:
    load_key_silently()
    cmd = [PY, "-c", RUN_CMD.format(cell=CELLS[0])]
    handle = heavy_lock.acquire(
        cycle_id="JEV-REGIME-ROUTER-V2",
        role="quant-implementer/jrv2-bulk",
        worktree=str(REPO / ".worktrees/jev-regime-router-v2/integration"),
        command=cmd,
        expected_artifacts=[str(cell_decisions_path(c)) for c in CELLS],
    )
    print("lock acquired; bulk V2 starting", flush=True)

    child: dict[str, subprocess.Popen | None] = {"proc": None}
    stop = threading.Event()
    cur = {"cell": "-"}

    def _hb() -> None:
        cells_n = {}
        for c in CELLS:
            d = CYCLE_DIR / "runtime" / "replay" / c
            n = 0
            if d.exists():
                for f in d.glob("decisions_*.jsonl"):
                    n = sum(1 for _ in f.open())
            cells_n[c] = n
        handle.heartbeat(extra={"cells": cells_n, "current": cur["cell"]})

    def hb_loop() -> None:
        while not stop.wait(30):
            try:
                _hb()
            except Exception:
                pass

    def on_term(signum, frame):
        print(f"signal {signum} received: terminating replay child first", flush=True)
        p = child.get("proc")
        if p is not None and p.poll() is None:
            try:
                p.terminate()
                p.wait(timeout=30)
            except Exception:
                pass
        stop.set()
        handle.release(status="TECHABORT", note=f"owner/graceful stop during {cur['cell']}")
        os._exit(0)

    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_term)

    results: dict[str, int] = {}
    t = threading.Thread(target=hb_loop, daemon=True)
    t.start()
    log = CYCLE_DIR / "runtime" / "bulk_v2.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    overall = 0
    try:
        with log.open("a") as lf:
            for cell in CELLS:
                cur["cell"] = cell
                print(f"=== cell {cell} start {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} ===", flush=True)
                proc = subprocess.Popen(
                    [PY, "-c", RUN_CMD.format(cell=cell)],
                    cwd=str(CYCLE_DIR), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                )
                child["proc"] = proc
                out, _ = proc.communicate()
                child["proc"] = None
                rc = proc.returncode
                lf.write(f"=== {cell} exit {rc} at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} ===\n")
                lf.write((out or "")[-8000:])
                lf.flush()
                d = cell_decisions_path(cell)
                n = sum(1 for _ in d.open()) if d.exists() else 0
                results[cell] = n
                overall += n
                print(f"cell {cell} exit={rc} decisions={n}", flush=True)
                if rc != 0:
                    handle.release(status="TECHABORT", note=f"cell {cell} replay exit {rc}")
                    return rc
        handle.release(status="FINISHED", note=f"jrv2 bulk complete: {json.dumps(results)}")
        print(f"BULK DONE {json.dumps(results)}", flush=True)
        return 0
    except BaseException as e:
        p = child.get("proc")
        if p is not None and p.poll() is None:
            p.terminate()
        handle.release(status="TECHABORT", note=f"worker exception: {type(e).__name__}")
        raise
    finally:
        stop.set()


if __name__ == "__main__":
    sys.exit(main())
