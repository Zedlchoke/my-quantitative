"""CHR3F ILLIQ scored launcher (A2+A3 authority, post-A7-AUTHORIZED only).
8 cells = {Y2021,Y2022,Y2023,Y2024P} x {anchor 28D-W, INV 28D-W-INV}.
Bars loaded once; heavy lock held for the sweep (disclosed); cycle-local
outputs under illiq_scored_out/; labels EQUIVALENCE_DATA_RESTAGE_UNPROVEN."""
from __future__ import annotations
import json, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

R = Path("/Users/hoangminhlong/my-quantitative")
sys.path.insert(0, str(R))
from research.governance import heavy_lock  # noqa: E402

CD = R / ".worktrees/crypto-historical-replication-3f-v1/integration/research/control/crypto_historical_replication_3f_v1"
V11 = CD / "recovered/v11_root"

CATALOG = str(CD / "catalog_live_crypto_b20")
SCAN = str(CD / "funding_data_scan/scan_2026")  # B window (INC-3 layout law)
SYMS = ["1000PEPEUSDT","AAVEUSDT","ACEUSDT","ADAUSDT","AVAXUSDT","BCHUSDT","BNBUSDT",
        "BOMEUSDT","BTCUSDT","DOGEUSDT","ENAUSDT","ETHUSDT","LINKUSDT","NEARUSDT",
        "ONGUSDT","SOLUSDT","SUIUSDT","WLDUSDT","XRPUSDT","ZECUSDT"]
FOLDS = [("Y2024P", "2024-01-01T00:00:00Z", "2024-08-19T00:00:00Z")]  # A4b: owner "chạy từ 2024"
ARMS = [("ANCHOR", "ILLIQ-AMIHUD-28D-W"), ("INV", "ILLIQ-AMIHUD-28D-W-INV")]
CYCLE = "CRYPTO-HISTORICAL-REPLICATION-3F-V1"

def main() -> int:
    pre = CD / "a7_prelaunch_illiq/a7_prelaunch_illiq.json"
    v = json.loads(pre.read_text()) if pre.exists() else {}
    if v.get("verdict") != "AUTHORIZED":
        print(f"REFUSED: A7 ILLIQ verdict = {v.get('verdict','MISSING')}")
        return 5
    status_path = CD / "illiq_scored_status.json"
    status = json.loads(status_path.read_text()) if status_path.exists() else {"cells": []}
    done = {c["cell_id"] for c in status["cells"] if c.get("rc") == 0 and "outcome_class" not in c}
    handle = heavy_lock.acquire(cycle_id=CYCLE, role="scored-cells",
                                worktree=str(R / ".worktrees/crypto-historical-replication-3f-v1/integration"),
                                command=[str(PY := R / ".venv/bin/python"), str(Path(__file__))],
                                expected_artifacts=[str(status_path)])
    try:
        import os
        for fold, w0, w1 in FOLDS:
            for arm_label, arm_id in ARMS:
                cell_id = f"CHR3F-ILLIQ-{fold}-{arm_label}"
                if cell_id in done:
                    continue
                t0 = time.time()
                env = dict(os.environ, PYTHONPATH=str(V11))
                r = subprocess.run([str(PY), str(CD / "illiq_cell_runner.py"),
                                    "--fold", fold, "--window-start", w0,
                                    "--window-end", w1, "--arm-id", arm_id,
                                    "--out", str(CD / "illiq_scored_out" / cell_id)],
                                   cwd=str(V11), capture_output=True, text=True, env=env)
                (CD / "illiq_scored_out").mkdir(parents=True, exist_ok=True)
                (CD / "illiq_scored_out" / f"{cell_id}.log").write_text(r.stdout + "\n" + r.stderr)
                metrics = {}
                if r.returncode == 0:
                    try:
                        metrics = json.loads(r.stdout.strip().splitlines()[-1])
                    except Exception:
                        metrics = {}
                row = {"cell_id": cell_id, "fold": fold, "arm": arm_label,
                       "rc": 0, "runtime_s": round(time.time()-t0, 1),
                       "utc": datetime.now(timezone.utc).isoformat(),
                       "namespace": "REPLICATION_NOT_PROSPECTIVE",
                       "label": "EQUIVALENCE_DATA_RESTAGE_UNPROVEN",
                       "authority": "A2+A3 (owner) + A7 prelaunch",
                       "rc": r.returncode,
                       "net_return_sum": metrics.get("net_return_sum"),
                       "position_pf": metrics.get("position_pf"),
                       "max_drawdown": metrics.get("max_drawdown"),
                       "n_positions": metrics.get("n_positions")}
                status["cells"].append(row)
                print("CELL", cell_id, "rc", r.returncode, "net", row["net_return_sum"], flush=True)
                status_path.write_text(json.dumps(status, indent=1))
                print("CELL", cell_id, "net", row["net_return_sum"], "pf", row["position_pf"], flush=True)
    finally:
        handle.release()
    print("ILLIQ SCORED SWEEP COMPLETE", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
