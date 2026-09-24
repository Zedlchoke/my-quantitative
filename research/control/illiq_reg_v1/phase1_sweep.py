"""ILLIQ-REG-V1 phase-1 scored sweep (plan SS8/§10.7; post-GO only).

4 cells on the S0R falsification surface, all `scored=False` diagnostics in
namespace REPLICATION_NOT_PROSPECTIVE, each counting one budget unit
(registry cap 4):

  P1-C1  ANCHOR (ILLIQ-AMIHUD-28D-W)  baseline  <- falsification cell
  P1-C2  ANCHOR                        fee x1.5  (frozen named cell)
  P1-C3  ANCHOR                        fee x2.0  (prereg spec, plan SS7)
  P1-C4  INV    (ILLIQ-AMIHUD-28D-W-INV) baseline (causal control)

PROCESS ISOLATION (chr3f illiq_scored.py pattern): this launcher imports
ONLY root-repo + cycle-local modules (heavy_lock, wiring, gate_module) and
runs every cell as a SUBPROCESS of illiq_reg_cell.py, which owns the
v11-side imports — mixing both in one process binds the `research` package
to v11_root and breaks `research.governance` (observed & fixed 2026-09-24).

Refuses to run unless ALL hold (fail-closed): A7 verdict AUTHORIZED;
AUTH/GO_RECORDED.json with the registered phrase; registry lifecycle
ACTIVE_HEAVY; gate_series.json digest == audited digest; budget 0/4; S0R
funding coverage (scan_2026_a, 20/20). Machine-wide heavy lock held for the
whole sweep; per-cell status written incrementally; verdict written at end.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True

R = Path("/Users/hoangminhlong/my-quantitative")
sys.path.insert(0, str(R))
from research.governance import heavy_lock  # noqa: E402  (root paths FIRST)

sys.path.insert(0, str(HERE))
import wiring  # noqa: E402  (cycle-local; imports no v11 modules)
from gate_module import falsification_verdict  # noqa: E402

CYCLE = "ILLIQ-REG-V1"
FOLD = "S0R"
FALSIFICATION_CELL = "P1-C1"
AUDITED_GATE_SERIES_SHA256 = ("e09187f925e761cfabe94e0766ca2104b3b45f5def76f"
                              "adc061cdbc09c51702d")
REGISTERED_PHRASE = "GO ILLIQ REG V1 SCORED EXECUTION"
PY = R / ".venv" / "bin" / "python"
CELLS = [("P1-C1", "ANCHOR", "baseline"),
         ("P1-C2", "ANCHOR", "fee_x1_5"),
         ("P1-C3", "ANCHOR", "fee_x2_0"),
         ("P1-C4", "INV", "baseline")]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def preconditions() -> dict:
    a7 = json.loads((HERE / "a7_prelaunch" / "a7_prelaunch_illiq_reg_v1.json")
                    .read_text())
    if a7.get("verdict") != "AUTHORIZED":
        raise wiring.WiringError(f"REFUSED: A7 verdict {a7.get('verdict')!r}")
    go = json.loads((HERE / "AUTH" / "GO_RECORDED.json").read_text())
    if go.get("go_phrase") != REGISTERED_PHRASE or not go.get(
            "received_after_a7_prelaunch") or not go.get(
            "registered_phrase_matches"):
        raise wiring.WiringError("REFUSED: GO record invalid")
    gs_bytes = (HERE / "gate_series.json").read_bytes()
    if sha256_bytes(gs_bytes) != AUDITED_GATE_SERIES_SHA256:
        raise wiring.WiringError("REFUSED: gate_series digest != audited")
    reg = json.loads((R / "plans" / "CYCLE_REGISTRY.json").read_text())
    row = next(c for c in reg["cycles"] if c["cycle_id"] == CYCLE)
    if row.get("lifecycle") != "ACTIVE_HEAVY":
        raise wiring.WiringError(
            f"REFUSED: lifecycle {row.get('lifecycle')!r} != ACTIVE_HEAVY")
    budget = row.get("budget") or {}
    if int(budget.get("used", 0)) != 0 or int(budget.get("max", 4)) < 4:
        raise wiring.WiringError(
            f"REFUSED: budget {budget} != 0/4")
    w0, w1 = wiring.FOLD_WINDOWS[FOLD]
    wiring.verify_funding_scan_coverage(
        wiring.FOLD_WIRING[FOLD]["funding_scan"], wiring.SYMS, w0, w1)
    return {"a7_verdict": a7["verdict"], "go": True,
            "gate_series_sha256": sha256_bytes(gs_bytes),
            "registry_lifecycle": row["lifecycle"],
            "budget": f"{budget.get('used', 0)}/{budget.get('max', 4)}"}


def main() -> int:
    pre = preconditions()
    print(json.dumps({"preconditions": "OK", **pre}), flush=True)

    handle = heavy_lock.acquire(
        cycle_id=CYCLE, role="scored-cells", worktree=str(HERE.parents[2]),
        command=[str(PY), str(Path(__file__))],
        expected_artifacts=[str(HERE / "phase1_status.json"),
                            str(HERE / "phase1_verdict.json")])
    cells = []
    release_status, release_note = "FINISHED", ""
    try:
        for cell_id, arm, stress in CELLS:
            out_dir = HERE / "phase1" / cell_id
            cmd = [str(PY), str(HERE / "illiq_reg_cell.py"),
                   "--cell-id", cell_id, "--arm", arm,
                   "--stress", stress, "--out", str(out_dir)]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                tail = (proc.stderr or "")[-800:]
                release_status, release_note = "FAILED", f"cell {cell_id} rc={proc.returncode}"
                raise wiring.WiringError(
                    f"cell {cell_id} rc={proc.returncode}: {tail}")
            summary = json.loads(proc.stdout.strip().splitlines()[-1])
            wiring.validate_labels(summary["labels"])
            cells.append(summary)
            handle.heartbeat({"cell_done": cell_id})
            print(json.dumps({k: summary[k] for k in (
                "cell_id", "arm", "stress", "net_return_sum", "max_drawdown",
                "position_pf", "n_positions", "gate_counts")}), flush=True)
            (HERE / "phase1_status.json").write_text(json.dumps(
                {"cycle_id": CYCLE, "fold": FOLD, "cells": cells}, indent=1))
    finally:
        handle.release(release_status, release_note)

    base_cell = next(c for c in cells if c["cell_id"] == FALSIFICATION_CELL)
    verdict = falsification_verdict(base_cell["net_return_sum"],
                                    base_cell["max_drawdown"])
    inv_cell = next(c for c in cells if c["arm"] == "INV")
    doc = {
        "schema": "illiq_reg_v1.phase1_verdict@1",
        "cycle_id": CYCLE, "fold": FOLD,
        "falsification_cell": FALSIFICATION_CELL,
        "labels_base_cell": base_cell["labels"],
        "verdict": verdict,
        "inv_coherence": {
            "inv_gated_net_sum": inv_cell["net_return_sum"],
            "note": "plan SS7: on a losing anchor window INV-gated is "
                    "expected positive; sign reported, not a rescue path",
        },
        "cells": cells,
        "budget_used": f"{len(cells)}/4",
        "phase_2": "NOT AUTHORIZED — owner amendment required (plan SS8)",
        "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    (HERE / "phase1_verdict.json").write_text(json.dumps(doc, indent=1))
    print(json.dumps({"verdict": verdict["verdict"],
                      "gated_net_sum": base_cell["net_return_sum"],
                      "gated_mdd": base_cell["max_drawdown"],
                      "net_margin": verdict["net_margin"],
                      "mdd_margin": verdict["mdd_margin"],
                      "inv_gated_net_sum": inv_cell["net_return_sum"]}),
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
