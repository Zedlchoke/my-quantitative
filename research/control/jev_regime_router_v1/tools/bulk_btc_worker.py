#!/usr/bin/env python3
"""JRV1 bulk replay worker — BTCUSDT leg (owner instruction 2026-09-22
'chạy BTC thử trước đi' after canary evidence + revised cost disclosure).

Acquires the machine-wide heavy lock, runs the sequential live replay for
all BTCUSDT decision states (cache-first: the 94 canary states are skipped),
heartbeats while polling, releases the lock in finally. The TYPESAFE_API_KEY
is read from the repo .env INSIDE this process and never printed.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import threading
import time

REPO = pathlib.Path("/Users/hoangminhlong/my-quantitative")
CYCLE_DIR = REPO / ".worktrees/jev-regime-router-v1/integration/research/control/jev_regime_router_v1"
sys.path.insert(0, str(REPO / "research"))
sys.path.insert(0, str(CYCLE_DIR))

from governance import heavy_lock  # noqa: E402

PY = str(REPO / ".venv/bin/python")
LOG = CYCLE_DIR / "runtime" / "bulk_btc.log"


def load_key_silently() -> None:
    for line in (REPO / ".env").read_text().splitlines():
        if line.startswith("TYPESAFE_API_KEY="):
            val = line.split("=", 1)[1].strip().strip('"').strip("'")
            if val:
                import os

                os.environ["TYPESAFE_API_KEY"] = val
            return
    raise SystemExit("BLOCKED_CREDENTIAL: TYPESAFE_API_KEY absent in .env")


def main() -> int:
    load_key_silently()
    cmd = [PY, "-c",
           "import sys; sys.path.insert(0, '.'); from jrv1 import run; "
           "sys.argv = ['run.py', 'replay', '--asset', 'btcusdt']; run.main()"]
    handle = heavy_lock.acquire(
        cycle_id="JEV-REGIME-ROUTER-V1",
        role="quant-implementer/jrv1-bulk-btc",
        worktree=str(REPO / ".worktrees/jev-regime-router-v1/integration"),
        command=cmd,
        expected_artifacts=[
            str(CYCLE_DIR / "runtime/replay/btcusdt/decisions_btcusdt.jsonl"),
        ],
    )
    print(f"lock acquired; starting bulk BTC replay", flush=True)
    proc = subprocess.Popen(cmd, cwd=str(CYCLE_DIR), stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    stop = threading.Event()

    def hb() -> None:
        while not stop.wait(30):
            try:
                dec = CYCLE_DIR / "runtime/replay/btcusdt/decisions_btcusdt.jsonl"
                n = sum(1 for _ in dec.open()) if dec.exists() else 0
                handle.heartbeat(extra={"decisions_ingested": n})
            except Exception:
                pass

    t = threading.Thread(target=hb, daemon=True)
    t.start()
    rc = None
    try:
        out, _ = proc.communicate()
        rc = proc.returncode
        LOG.parent.mkdir(parents=True, exist_ok=True)
        LOG.write_text(out or "")
        print(f"replay exit={rc}; log at {LOG}", flush=True)
        handle.release(status="FINISHED" if rc == 0 else "TECHABORT",
                       note=f"jrv1-bulk-btc replay exit {rc}")
    except BaseException:
        proc.kill()
        handle.release(status="TECHABORT", note="worker exception; replay kill")
        raise
    finally:
        stop.set()
    return rc or 1


if __name__ == "__main__":
    sys.exit(main())
