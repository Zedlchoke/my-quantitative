"""CHR3F ILLIQ scored launcher (A2+A3 authority, post-A7-AUTHORIZED only).
8 cells = {Y2021,Y2022,Y2023,Y2024P} x {anchor 28D-W, INV 28D-W-INV}.
Bars loaded once; heavy lock held for the sweep (disclosed); cycle-local
outputs under illiq_scored_out/; labels EQUIVALENCE_DATA_RESTAGE_UNPROVEN."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path

R = Path("/Users/hoangminhlong/my-quantitative")
sys.path.insert(0, str(R))
from research.governance import heavy_lock  # noqa: E402

CD = R / ".worktrees/crypto-historical-replication-3f-v1/integration/research/control/crypto_historical_replication_3f_v1"
V11 = CD / "recovered/v11_root"
sys.path.insert(0, str(V11))
sys.path.insert(0, str(CD))
from research.hyp_a8_m01 import read_bars_15m  # noqa: E402
from research.adapter_v10.runner import run_strategy  # noqa: E402
from chr3f_illiq_plugin import Chr3fIlliqPlugin  # noqa: E402

CATALOG = str(CD / "catalog_live_crypto_b20")
SCAN = str(CD / "funding_data_scan/scan_2026")  # B window (INC-3 layout law)
SYMS = ["1000PEPEUSDT","AAVEUSDT","ACEUSDT","ADAUSDT","AVAXUSDT","BCHUSDT","BNBUSDT",
        "BOMEUSDT","BTCUSDT","DOGEUSDT","ENAUSDT","ETHUSDT","LINKUSDT","NEARUSDT",
        "ONGUSDT","SOLUSDT","SUIUSDT","WLDUSDT","XRPUSDT","ZECUSDT"]
FOLDS = [("Y2021", "2021-01-01T00:00:00Z", "2022-01-01T00:00:00Z"),
         ("Y2022", "2022-01-01T00:00:00Z", "2023-01-01T00:00:00Z"),
         ("Y2023", "2023-01-01T00:00:00Z", "2024-01-01T00:00:00Z"),
         ("Y2024P", "2024-01-01T00:00:00Z", "2024-08-19T00:00:00Z")]
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
        bars = None
        for fold, w0, w1 in FOLDS:
            if bars is None:
                st = datetime.fromisoformat(w0.replace("Z", "+00:00"))
                pre_iso = datetime.fromtimestamp(st.timestamp() - 125*86400, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                print("loading bars...", flush=True)
                bars = {s: read_bars_15m(CATALOG, s, pre_iso, FOLDS[-1][2]) for s in SYMS}
                print("bars loaded", flush=True)
            settles = {}
            for s in SYMS:
                doc = json.loads((Path(SCAN) / s / "funding.json").read_text())
                from research.adapter_v10.protocol import SettlementPoint
                pts = [SettlementPoint(publish_ts_ns=int(r["fundingTime"])*1_000_000,
                                       value=float(r["fundingRate"]), kind="info")
                       for r in doc["rows"]]
                pts.sort(key=lambda p_: p_.publish_ts_ns)
                settles[s] = tuple(pts)
            for arm_label, arm_id in ARMS:
                cell_id = f"CHR3F-ILLIQ-{fold}-{arm_label}"
                if cell_id in done:
                    continue
                t0 = time.time()
                plugin = Chr3fIlliqPlugin(bars_by_symbol=bars, arm_id=arm_id,
                                          tick_sizes={s: 1e-07 for s in SYMS},
                                          settle_points_by_symbol=settles,
                                          window_start_iso=w0, window_end_iso=w1)
                plugin.bind_window((w0, w1))
                out_dir = CD / "illiq_scored_out" / cell_id
                payload = run_strategy(plugin, out_dir=str(out_dir), write_artifact_file=True)
                m = payload.get("portfolio_metrics") or {}
                row = {"cell_id": cell_id, "fold": fold, "arm": arm_label,
                       "rc": 0, "runtime_s": round(time.time()-t0, 1),
                       "utc": datetime.now(timezone.utc).isoformat(),
                       "namespace": "REPLICATION_NOT_PROSPECTIVE",
                       "label": "EQUIVALENCE_DATA_RESTAGE_UNPROVEN",
                       "authority": "A2+A3 (owner) + A7 prelaunch",
                       "net_return_sum": m.get("net_return_sum"),
                       "position_pf": m.get("position_pf"),
                       "max_drawdown": m.get("max_drawdown"),
                       "n_positions": m.get("n_positions")}
                status["cells"].append(row)
                status_path.write_text(json.dumps(status, indent=1))
                print("CELL", cell_id, "net", row["net_return_sum"], "pf", row["position_pf"], flush=True)
    finally:
        handle.release()
    print("ILLIQ SCORED SWEEP COMPLETE", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
