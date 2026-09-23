#!/usr/bin/env python
"""Heavy-lock wrapper: acquire machine-wide lock, run the GO-gated scored
discovery, release in finally (FINISHED/FAILED). Pure launcher — no
computation lives here."""
import subprocess
import sys
from pathlib import Path

CYCLE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "research"))

from governance.heavy_lock import acquire, LockBusyError  # noqa: E402


def main() -> int:
    cmd = [sys.executable, str(CYCLE_DIR / "tools" / "cmd_scored.py")]
    try:
        handle = acquire(
            cycle_id="REGIME-STRATEGY-MAPPING-V1",
            role="scored-discovery",
            worktree=str(CYCLE_DIR),
            command=cmd,
        )
    except LockBusyError as exc:
        print("NOT_RUN_RESOURCE_CONFLICT:", exc)
        return 3
    try:
        proc = subprocess.run(cmd, cwd=str(CYCLE_DIR))
        handle.release(status="FINISHED" if proc.returncode == 0 else "FAILED",
                       note="rsmv1 scored discovery (primary + floor sensitivity)")
        return proc.returncode
    except BaseException:
        handle.release(status="FAILED", note="exception in scored worker")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
