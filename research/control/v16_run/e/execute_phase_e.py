"""CRYPTO-V16 phase E runner: two-key assertion + heavy lock + serial scored cells.

Refuses to run unless BOTH keys exist on disk:
  1. research/control/v16_run/q_a7_prelaunch/a7_prelaunch_v16.json
     final_verdict == CRYPTO_V16_S0_LAUNCH_AUTHORIZED, zero_unresolved_high_critical
  2. research/control/v16_run/e/go_consumed_2026-09-07.json (this GO's own record)

Cells: the six frozen arms, SERIAL, scored mode, against the real staged panels.
Emits an inventory artifact; gate evaluation happens in the terminal step.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from research.governance import heavy_lock

WORKTREE = Path(__file__).resolve().parents[4]
RUN = WORKTREE / "research" / "control" / "v16_run"
DRIVER = RUN / "driver" / "run_v16_cell.py"
PY = sys.executable

FAMILIES = ("CLOSE-DISPLACE-FADE", "RUNPERSIST")
ARMS = ("anchor", "neighbour", "control")


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def assert_keys() -> None:
    a7 = json.load(open(RUN / "q_a7_prelaunch" / "a7_prelaunch_v16.json"))
    assert a7["final_verdict"] == "CRYPTO_V16_S0_LAUNCH_AUTHORIZED", a7["final_verdict"]
    assert a7["zero_unresolved_high_critical"] is True
    go = json.load(open(RUN / "e" / "go_consumed_2026-09-07.json"))
    assert go["artifact"] == "owner_go_consumed" and go["form_check"]["match"] is True


def main() -> None:
    assert_keys()
    command = [PY, str(DRIVER)]
    inventory = {"schema": "v16_run_artifact_v1", "artifact": "e_cells_inventory",
                 "generated_utc": utcnow(), "cells": []}
    with heavy_lock.acquire(
        cycle_id="CRYPTO-V16", role="E_SCORED_CELLS", worktree=str(WORKTREE),
        command=command, expected_artifacts=[str(RUN / "e" / "cells_inventory.json")],
    ) as lock:
        for family in FAMILIES:
            for arm in ARMS:
                proc = subprocess.run(
                    [PY, str(DRIVER), "--family", family, "--arm-id", arm],
                    capture_output=True, text=True, cwd=str(WORKTREE))
                cell = {"family": family, "arm": arm, "exit_code": proc.returncode,
                        "stderr_tail": proc.stderr[-500:] if proc.returncode else ""}
                art_dir = WORKTREE / "results" / "v16" / family / arm
                cell["artifacts"] = {p.name: sum(1 for _ in open(p))
                                     for p in sorted(art_dir.glob("*.jsonl"))} \
                    if art_dir.exists() else {}
                inventory["cells"].append(cell)
                lock.heartbeat(extra={"last_cell": f"{family}/{arm}"})
                print(f"{family}/{arm}: exit {proc.returncode}, "
                      f"{sum(cell['artifacts'].values())} records", flush=True)
                if proc.returncode != 0:
                    print(cell["stderr_tail"], file=sys.stderr)
                    break
            else:
                continue
            break
    (RUN / "e" / "cells_inventory.json").write_text(json.dumps(inventory, indent=1) + "\n")
    ok = all(c["exit_code"] == 0 for c in inventory["cells"])
    print(f"ALL_CELLS_EXIT_0: {ok}; cells run: {len(inventory['cells'])}")


if __name__ == "__main__":
    main()
