"""One ILLIQ scored cell in the v11 context. Args: --fold --window-start --window-end --arm-id --out"""
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
V11 = Path(__file__).resolve().parent / "recovered/v11_root"
sys.path.insert(0, str(V11))
from research.hyp_a8_m01 import read_bars_15m  # noqa: E402
from research.adapter_v10.protocol import SettlementPoint  # noqa: E402
from research.adapter_v10.runner import run_strategy  # noqa: E402
from chr3f_illiq_plugin import Chr3fIlliqPlugin  # noqa: E402

CD = V11.parent
ap = argparse.ArgumentParser()
ap.add_argument("--fold", required=True)
ap.add_argument("--window-start", required=True)
ap.add_argument("--window-end", required=True)
ap.add_argument("--arm-id", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
SYMS = ["1000PEPEUSDT","AAVEUSDT","ACEUSDT","ADAUSDT","AVAXUSDT","BCHUSDT","BNBUSDT",
        "BOMEUSDT","BTCUSDT","DOGEUSDT","ENAUSDT","ETHUSDT","LINKUSDT","NEARUSDT",
        "ONGUSDT","SOLUSDT","SUIUSDT","WLDUSDT","XRPUSDT","ZECUSDT"]
CATALOG = str(CD / "catalog_live_crypto_b20")
SCAN = str(CD / "funding_data_scan/scan_2026")
st = datetime.fromisoformat(a.window_start.replace("Z", "+00:00"))
pre = datetime.fromtimestamp(st.timestamp() - 125*86400, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
bars = {s: read_bars_15m(CATALOG, s, pre, a.window_end) for s in SYMS}
settles = {}
for s in SYMS:
    doc = json.loads((Path(SCAN) / s / "funding.json").read_text())
    pts = [SettlementPoint(publish_ts_ns=int(r["fundingTime"])*1_000_000,
                           value=float(r["fundingRate"]), kind="info") for r in doc["rows"]]
    pts.sort(key=lambda p_: p_.publish_ts_ns)
    settles[s] = tuple(pts)
plugin = Chr3fIlliqPlugin(bars_by_symbol=bars, arm_id=a.arm_id,
                          tick_sizes={s: 1e-07 for s in SYMS},
                          settle_points_by_symbol=settles,
                          window_start_iso=a.window_start, window_end_iso=a.window_end)
plugin.bind_window((a.window_start, a.window_end))
payload = run_strategy(plugin, out_dir=a.out, write_artifact_file=True)
m = payload.get("portfolio_metrics") or {}
print(json.dumps({"fold": a.fold, "arm_id": a.arm_id,
                  "net_return_sum": m.get("net_return_sum"),
                  "position_pf": m.get("position_pf"),
                  "max_drawdown": m.get("max_drawdown"),
                  "n_positions": m.get("n_positions")}))
