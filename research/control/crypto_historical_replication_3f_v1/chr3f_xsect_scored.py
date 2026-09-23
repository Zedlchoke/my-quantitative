"""CHR3F XSECT scored-cell launcher (A2 authority, post-A7-AUTHORIZED only).
8 cells = 4 primary folds x {anchor 7D, INV --reverse}, one heavy-lock
acquisition per cell, cycle-local registry/outputs, per-cell status row."""
from __future__ import annotations
import json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

R = Path("/Users/hoangminhlong/my-quantitative")
sys.path.insert(0, str(R))
from research.governance import heavy_lock  # noqa: E402

CD = R / ".worktrees/crypto-historical-replication-3f-v1/integration/research/control/crypto_historical_replication_3f_v1"
V6 = CD / "recovered/v6_root"
RUN = CD / "chr3f_xsect_run"
PY = R / ".venv/bin/python"
CYCLE = "CRYPTO-HISTORICAL-REPLICATION-3F-V1"

FOLDS = [("Y2021", "2021-01-01T00:00Z", "2022-01-01T00:00Z"),
         ("Y2022", "2022-01-01T00:00Z", "2023-01-01T00:00Z"),
         ("Y2023", "2023-01-01T00:00Z", "2024-01-01T00:00Z"),
         ("Y2020P", "2020-10-05T00:00Z", "2021-01-01T00:00Z")]
ARMS = [("ANCHOR", []), ("INV", ["--reverse"])]

def ensure_links():
    for link, target in (("catalog_live_crypto", "../catalog_live_crypto_b"),
                         ("funding_data", "../funding_data_scan")):
        d = RUN / link
        if not d.exists():
            os.symlink(target, d)
    (RUN / "funding_data/scan_2026").exists() or sys.exit("funding link broken")

def main() -> int:
    prelaunch = CD / "a7_prelaunch_xsect/a7_prelaunch_xsect_r2.json"
    v = json.loads(prelaunch.read_text()) if prelaunch.exists() else {}
    if v.get("verdict") != "AUTHORIZED":
        print(f"REFUSED: A7 r2 verdict = {v.get('verdict', 'MISSING')}")
        return 5
    ensure_links()
    status_path = CD / "xsect_scored_status.json"
    status = json.loads(status_path.read_text()) if status_path.exists() else {"cells": []}
    done = {c["cell_id"] for c in status["cells"] if c["rc"] == 0}
    for fold, w0, w1 in FOLDS:
        for arm, extra in ARMS:
            cell_id = f"CHR3F-XSECT-{fold}-{arm}-7D"
            if cell_id in done:
                continue
            handle = heavy_lock.acquire(cycle_id=CYCLE, role="scored-cells",
                                        worktree=str(R / ".worktrees/crypto-historical-replication-3f-v1/integration"),
                                        command=[str(PY), str(Path(__file__))],
                                        expected_artifacts=[str(status_path)])
            t0 = time.time()
            try:
                argv = [str(PY), str(V6 / "research/portfolio_runner.py"),
                        "--experiment-id", cell_id,
                        "--lookback-days", "7",
                        "--window-start", w0, "--window-end", w1,
                        "--folds", "3",
                        "--signal-family", "funding_carry",
                        "--hypothesis-dir", str(RUN / "research/hypotheses/H-XSECT-FUNDING-CARRY-v1"),
                        "--registry-path", "results/registry/chr3f_scored.jsonl",
                        "--output-root", str(RUN / "results/chr3f_scored")] + extra
                env = dict(os.environ, PYTHONPATH=str(V6))
                r = subprocess.run(argv, cwd=str(RUN), capture_output=True, text=True, env=env)
                (RUN / "results/chr3f_scored" / f"{cell_id}.log").parent.mkdir(parents=True, exist_ok=True)
                (RUN / "results/chr3f_scored" / f"{cell_id}.log").write_text(r.stdout + "\n" + r.stderr)
                status["cells"].append({
                    "cell_id": cell_id, "fold": fold, "arm": arm,
                    "rc": r.returncode, "runtime_s": round(time.time() - t0, 1),
                    "utc": datetime.now(timezone.utc).isoformat(),
                    "namespace": "REPLICATION_NOT_PROSPECTIVE",
                    "authority": "A2 (owner 2026-09-23) + A7 r2 AUTHORIZED"})
                status_path.write_text(json.dumps(status, indent=1))
                print(f"CELL {cell_id} rc={r.returncode} {round(time.time()-t0,1)}s", flush=True)
            finally:
                handle.release()
    print("SCORED SWEEP COMPLETE", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
