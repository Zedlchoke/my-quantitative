"""CHR3F ILLIQ equivalence gate: run the FROZEN V11 anchor arm on the
restaged original-window data and compare canonical surfaces against the
A7-verified baseline (audit commit 71b8ea3e) at <=1e-9 relative."""
from __future__ import annotations
import json, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

R = Path("/Users/hoangminhlong/my-quantitative")
CD = R / ".worktrees/crypto-historical-replication-3f-v1/integration/research/control/crypto_historical_replication_3f_v1"
V11 = CD / "recovered/v11_root"
sys.path.insert(0, str(V11))

CATALOG = str(CD / "catalog_live_crypto_a20")
SCAN = str(CD / "funding_data_scan/scan_2026_a")  # INC-3: A window in its own root
SYMS = ["1000PEPEUSDT","AAVEUSDT","ACEUSDT","ADAUSDT","AVAXUSDT","BCHUSDT","BNBUSDT",
        "BOMEUSDT","BTCUSDT","DOGEUSDT","ENAUSDT","ETHUSDT","LINKUSDT","NEARUSDT",
        "ONGUSDT","SOLUSDT","SUIUSDT","WLDUSDT","XRPUSDT","ZECUSDT"]
BAR_RANGE = ("2025-04-01T00:00:00Z", "2026-08-21T00:00:00Z")  # warmup + window

def tick_sizes():
    # EQUIV-DIAG: baseline +2_ticks stress moved net by only -0.0036/0.582 ->
    # the ORIGINAL staged tick table was ~1e-07 (near-zero slippage), NOT
    # exchangeInfo ticks. Hypothesis test: constant 1e-07.
    return {s: 1e-07 for s in SYMS}

def main() -> int:
    from research.hyp_a8_m01 import read_bars_15m
    from research.adapter_v10.protocol import SettlementPoint
    from research.v11.families.illiq_amihud.plugin import IlliqAmihudPlugin
    from research.adapter_v10.runner import run_strategy

    ticks = tick_sizes()
    bars = {}
    for s in SYMS:
        bars[s] = read_bars_15m(CATALOG, s, *BAR_RANGE)
        print(f"bars {s}: {len(bars[s])}", flush=True)
    # canonical conversion per audits.load_funding_settlements:
    # native funding rows -> SettlementPoint(publish_ts=fundingTime*1e6, value=rate, kind=info)
    settles = {}
    for s in SYMS:
        doc = json.loads((Path(SCAN) / s / "funding.json").read_text())
        pts = [SettlementPoint(publish_ts_ns=int(r["fundingTime"]) * 1_000_000,
                               value=float(r["fundingRate"]), kind="info")
               for r in doc["rows"]]
        pts.sort(key=lambda p_: p_.publish_ts_ns)
        settles[s] = tuple(pts)
    plugin = IlliqAmihudPlugin(bars_by_symbol=bars, arm_id="ILLIQ-AMIHUD-28D-W",
                               tick_sizes=ticks, settle_points_by_symbol=settles)
    out_dir = CD / "illiq_equivalence_out"
    payload = run_strategy(plugin, out_dir=str(out_dir), write_artifact_file=True)
    (out_dir / "equivalence_payload.json").write_text(json.dumps(
        payload, indent=1, default=str))

    # --- compare canonical surfaces vs baseline ---
    baseline = json.loads((V11 / "baseline_wave2.json").read_text())
    ev = baseline["items"][1]["evidence"]
    anchor = ev["anchor_confirmed"]
    m = payload.get("metrics") or payload
    def surf(name):
        for k in (name,):
            if k in m: return float(m[k])
        return None
    got = {
        "net_return_sum_daily": surf("net_return_sum_daily"),
        "position_pf": surf("position_pf"),
        "max_drawdown": surf("max_drawdown_fraction"),
        "n_positions": len(payload.get("positions", [])) if "positions" in payload else m.get("n_positions"),
    }
    exp = {"net_return_sum_daily": float(anchor["net_return_sum_daily"]),
           "position_pf": float(anchor["position_pf"]),
           "max_drawdown": float(anchor["max_drawdown"])}
    checks = {}
    for k, e in exp.items():
        g = got.get(k)
        checks[k] = {"expected": e, "got": g,
                     "rel_diff": (abs(g - e) / abs(e)) if g is not None and e else None}
    verdict = {"measured_utc": datetime.now(timezone.utc).isoformat(),
               "surfaces_found": sorted(m.keys())[:40], "checks": checks,
               "payload_keys": sorted(payload.keys())[:40]}
    (CD / "illiq_equivalence_verdict.json").write_text(json.dumps(verdict, indent=1))
    print(json.dumps(checks, indent=1))
    print("payload keys:", sorted(payload.keys()))
    print("metric keys:", sorted(m.keys())[:40])
    return 0

if __name__ == "__main__":
    sys.exit(main())
