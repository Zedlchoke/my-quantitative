#!/usr/bin/env python
"""RSMV1 diagnostic entry points (Phase 1 + Phase 2; NO scored runs).

Usage:
  python tools/run_diagnostics.py timeline   # rebuild + verify all cells
  python tools/run_diagnostics.py census     # Phase 2 sample census (no PnL)
  python tools/run_diagnostics.py attribution  # Phase 1 (A2 lane owns this)

Exit code 0 only if every check passes. The scored backtest lives elsewhere
and is GO-gated; this tool can never trigger it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CYCLE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CYCLE_DIR))


def cmd_timeline() -> int:
    from rsmv1.regime_timeline import rebuild_cell_timeline, save_timeline_json

    for cell in ("BTC_H1", "BTC_H4", "SPY_D1"):
        ct = rebuild_cell_timeline(CYCLE_DIR, cell)
        save_timeline_json(ct, CYCLE_DIR / "runtime" / f"regime_timeline_{cell}.json")
        print(f"{cell}: switches={ct.stats['switches']} OK")
    return 0


def cmd_census() -> int:
    from rsmv1.feasibility import run_all

    out = run_all(CYCLE_DIR, CYCLE_DIR / "evidence")
    print(json.dumps({c: {r: v["verdict"] for r, v in b["per_regime"].items()}
                      for c, b in out["cells"].items()}, indent=1))
    return 0


def cmd_attribution() -> int:
    from rsmv1.attribution import run_all

    out = run_all(CYCLE_DIR, CYCLE_DIR / "evidence")
    print("all_checks_pass:", out["all_checks_pass"])
    return 0 if out["all_checks_pass"] else 1


if __name__ == "__main__":
    cmds = {"timeline": cmd_timeline, "census": cmd_census,
            "attribution": cmd_attribution}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(cmds[sys.argv[1]]())
