"""One ILLIQ-LOSS-MECH-V1 phase-1 cell. Runs ONLY as a subprocess of
phase1_cells.py with sys.path = frozen v11_root (package-isolation pattern
from ILLIQ-REG-V1: the root checkout's `research` package must not shadow the
engine's). Args: --window-start --window-end --arm-id --variant --out
[--catalog CATALOG_ROOT --funding-scan SCAN_ROOT]

GO authorization: phase-1 census of Amendment A1 A1-7 (8 cells, scored=False).
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

V11 = Path("/Users/hoangminhlong/my-quantitative/.worktrees/crypto-historical-replication-3f-v1"
           "/integration/research/control/crypto_historical_replication_3f_v1/recovered/v11_root")
sys.path.insert(0, str(V11))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from research.hyp_a8_m01 import read_bars_15m  # noqa: E402
from research.adapter_v10.protocol import SettlementPoint  # noqa: E402
from research.adapter_v10.runner import run_strategy  # noqa: E402
from loss_mech_plugin import LossMechPlugin  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--window-start", required=True)
ap.add_argument("--window-end", required=True)
ap.add_argument("--arm-id", required=True)
ap.add_argument("--variant", required=True, choices=["BASELINE", "V2_AGE", "V2_HEDGE"])
ap.add_argument("--out", required=True)
ap.add_argument("--catalog", required=True)
ap.add_argument("--funding-scan", required=True)
a = ap.parse_args()

SYMS = ["1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT", "BCHUSDT", "BNBUSDT",
        "BOMEUSDT", "BTCUSDT", "DOGEUSDT", "ENAUSDT", "ETHUSDT", "LINKUSDT", "NEARUSDT",
        "ONGUSDT", "SOLUSDT", "SUIUSDT", "WLDUSDT", "XRPUSDT", "ZECUSDT"]

st = datetime.fromisoformat(a.window_start.replace("Z", "+00:00"))
pre = datetime.fromtimestamp(st.timestamp() - 125 * 86400, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
end_ext = (datetime.fromisoformat(a.window_end.replace("Z", "+00:00"))
           + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
bars = {s: read_bars_15m(a.catalog, s, pre, end_ext) for s in SYMS}
settles = {}
for s in SYMS:
    doc = json.loads((Path(a.funding_scan) / s / "funding.json").read_text())
    pts = [SettlementPoint(publish_ts_ns=int(r["fundingTime"]) * 1_000_000,
                           value=float(r["fundingRate"]), kind="info") for r in doc["rows"]]
    pts.sort(key=lambda p: p.publish_ts_ns)
    settles[s] = tuple(pts)

plugin = LossMechPlugin(variant=a.variant, bars_by_symbol=bars, arm_id=a.arm_id,
                        tick_sizes={s: 1e-07 for s in SYMS},
                        settle_points_by_symbol=settles,
                        window_start_iso=a.window_start, window_end_iso=a.window_end)
payload = run_strategy(plugin, out_dir=a.out, write_artifact_file=True)
m = payload.get("portfolio_metrics") or {}
print(json.dumps({"variant": a.variant, "arm_id": a.arm_id,
                  "window": [a.window_start, a.window_end],
                  "net_return_sum": m.get("net_return_sum"),
                  "position_pf": m.get("position_pf"),
                  "max_drawdown": m.get("max_drawdown"),
                  "n_positions": m.get("n_positions")}))
