"""EOSV2 STOP-1 scored-execution harness (orchestration ONLY — NOT frozen
engine code; frozen files eosv2_engine.py / run_scored.py / stage_all.py /
test_fixtures.py are byte-untouched, freeze digests unchanged).

Law implemented here (mission + cycle precedent):
  1. take the MACHINE-WIDE heavy lock (research/governance/heavy_lock.py)
     after verifying FREE; hold end-to-end across all compute; release
     FINISHED with disclosure;
  2. invoke the frozen runner scripts/run_scored.py in `scored` mode via
     the ROOT .venv interpreter (never another python); capture its stdout
     artifact verbatim; non-zero exit = TECHABORT path (no rescue);
  3. determinism precedent: after the battery, re-run scored cell EOSV2-B1
     in TWO fresh processes and assert the canonical dumps are
     byte-identical (sha256 equal), then cross-check the rounded nets
     against scored/scored_summary.json (the battery's own B1 numbers).

Outputs (engine outputs are never reformatted):
  scored/scored_summary.json          (written by the frozen runner)
  scored/run_scored_stdout.json       (the frozen runner's verdict print, verbatim)
  scored/determinism_b1.json          (determinism assertion record)
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

WORKTREE = pathlib.Path(__file__).resolve().parents[4]
CTRL = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = CTRL / "scripts"
SCORED = CTRL / "scored"

sys.path.insert(0, str(WORKTREE))
from research.governance import heavy_lock  # noqa: E402

ROOT_PY = pathlib.Path("/Users/hoangminhlong/my-quantitative/.venv/bin/python")

DET_CODE = """
import json, pathlib, sys
sys.path.insert(0, path_scripts)
import eosv2_engine as E
data = E.build_all_series()
targets = E.build_targets(data)
out = {"cell": "EOSV2-B1"}
for tier in E.TIERS:
    res = E.run_book(targets["EOSV2-B1"], data["eth_h4"], data["funding"], tier, data["px_settle"])
    out[str(tier)] = {"folds": res["folds"], "fills_total": res["fills_total"],
                      "net_total": res["net_total"], "avg_raw_fill_px": res["avg_raw_fill_px"]}
print(json.dumps(out, sort_keys=True))
"""


def main() -> int:
    SCORED.mkdir(exist_ok=True)
    lock = heavy_lock.acquire(
        cycle_id="ETHUSDT-OPEN-SEARCH-V2",
        role="stop1-scored-execution",
        worktree=str(WORKTREE),
        command=sys.argv,
        expected_artifacts=[
            "research/control/ethusdt_open_search_v2/scored/scored_summary.json",
            "research/control/ethusdt_open_search_v2/scored/determinism_b1.json",
        ],
    )
    print(f"[lock] TAKEN {heavy_lock.RUNTIME_DIRNAME} pid={lock.owner['pid']}")
    try:
        lock.heartbeat({"phase": "scored battery (frozen run_scored.py)"})
        battery = subprocess.run(
            [str(ROOT_PY), str(SCRIPTS / "run_scored.py"), "scored"],
            capture_output=True, text=True, timeout=3600)
        (SCORED / "run_scored_stdout.json").write_text(battery.stdout)
        if battery.returncode != 0:
            print(battery.stdout)
            print(battery.stderr, file=sys.stderr)
            lock.release(status="FAILED",
                         note=f"frozen runner exited {battery.returncode}: "
                              f"{battery.stderr[-500:]}")
            return battery.returncode or 1
        print("[battery] frozen runner scored mode exit 0; verdict print captured")

        lock.heartbeat({"phase": "determinism re-run EOSV2-B1 (2 fresh processes)"})
        runs = []
        for i in (1, 2):
            p = subprocess.run(
                [str(ROOT_PY), "-c", DET_CODE.replace("path_scripts", repr(str(SCRIPTS)))],
                capture_output=True, text=True, timeout=1800)
            if p.returncode != 0:
                lock.release(status="FAILED",
                             note=f"determinism run {i} exited {p.returncode}: {p.stderr[-500:]}")
                return 2
            runs.append(p.stdout.encode("utf-8"))

        import hashlib
        digests = [hashlib.sha256(r).hexdigest() for r in runs]
        byte_identical = runs[0] == runs[1]

        summary = json.loads((SCORED / "scored_summary.json").read_text())
        b1_battery = summary["cells"]["EOSV2-B1"]
        det1 = json.loads(runs[0])
        cross = {
            "net_at_tiers": all(
                b1_battery["net_at_tiers"][t] == round(det1[t]["net_total"], 2)
                for t in ("1.0", "1.5", "2.0")),
            "fold_nets": all(
                b1_battery["fold_nets"][f] == round(det1[t]["folds"][f]["net"], 2)
                for t in ("1.0",) for f in ("F1", "F2", "F3", "F4")),
        }
        det_out = {
            "schema": "eosv2.determinism_b1@1",
            "protocol": "post-battery re-run of cell EOSV2-B1 in two fresh "
                        "processes (ROOT .venv python, frozen engine, stdlib-only); "
                        "canonical JSON dumps compared byte-wise",
            "sha256_run1": digests[0], "sha256_run2": digests[1],
            "byte_identical": byte_identical,
            "cross_check_vs_scored_summary": cross,
            "compared_fields": "folds(net,gross,fees,funding,trades,fills,"
                               "funding_events) x3 tiers + fills_total + "
                               "net_total + avg_raw_fill_px",
            "pass": byte_identical and all(cross.values()),
        }
        (SCORED / "determinism_b1.json").write_text(
            json.dumps(det_out, indent=1, sort_keys=True) + "\n")
        print(f"[determinism] byte_identical={byte_identical} cross={cross}")
        if not det_out["pass"]:
            lock.release(status="FAILED", note="determinism assertion failed")
            return 3
        lock.release(status="FINISHED", note=(
            "STOP-1 scored battery (48 computations: 4 lane-B cells x3 tiers, "
            "4 references x3 tiers, 4 cells x2 controls x3 tiers) + B1 "
            "determinism double re-run byte-identical; engine outputs captured "
            "verbatim under scored/"))
        print("[lock] RELEASED FINISHED")
        return 0
    except Exception as e:  # noqa: BLE001
        lock.release(status="FAILED", note=f"{type(e).__name__}: {e}") 
        raise


if __name__ == "__main__":
    sys.exit(main())
