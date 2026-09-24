"""CHR3F ILLIQ census + sanitized traversal (engine-authored eligibility).
Census per fold: for every weekly stamp, targets_at(...) status OK vs skip —
the frozen engine's own MIN_ELIGIBLE/quintile law decides. Shape only, no PnL."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path

R = Path("/Users/hoangminhlong/my-quantitative")
CD = R / ".worktrees/crypto-historical-replication-3f-v1/integration/research/control/crypto_historical_replication_3f_v1"
V11 = CD / "recovered/v11_root"
sys.path.insert(0, str(V11))
from research.hyp_a8_m01 import read_bars_15m  # noqa: E402
import sys as _sys
_sys.path.insert(0, str(CD))
from chr3f_illiq_plugin import Chr3fIlliqPlugin  # noqa: E402

CATALOG = str(CD / "catalog_live_crypto_b20")
SYMS = ["1000PEPEUSDT","AAVEUSDT","ACEUSDT","ADAUSDT","AVAXUSDT","BCHUSDT","BNBUSDT",
        "BOMEUSDT","BTCUSDT","DOGEUSDT","ENAUSDT","ETHUSDT","LINKUSDT","NEARUSDT",
        "ONGUSDT","SOLUSDT","SUIUSDT","WLDUSDT","XRPUSDT","ZECUSDT"]
FOLDS = {"Y2024P": ("2024-01-01T00:00:00Z", "2024-08-19T00:00:00Z")}

def load(fold):
    w0, w1 = FOLDS[fold]
    st = datetime.fromisoformat(w0.replace("Z","+00:00"))
    pre = datetime.fromtimestamp(st.timestamp()-125*86400, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {s: read_bars_15m(CATALOG, s, pre, w1) for s in SYMS}

def main() -> int:
    out = {"census": {}, "utc": datetime.now(timezone.utc).isoformat(),
           "note": "engine-authored eligibility (targets_at status); shape-only"}
    for fold, (w0, w1) in FOLDS.items():
        bars = load(fold)
        plugin = Chr3fIlliqPlugin(bars_by_symbol=bars, arm_id="ILLIQ-AMIHUD-28D-W",
                                  tick_sizes={s: 1e-07 for s in SYMS},
                                  window_start_iso=w0, window_end_iso=w1)
        plugin.bind_window((w0, w1))
        stress = plugin.baseline_stress()
        universe = plugin.universe(stress)
        stamps = plugin.schedule().instants
        ok = 0; bad = []; weights_n = []
        for st in stamps:
            t = plugin.targets_at(st, universe=universe, stress=stress)
            if t.get("status") == "OK":
                ok += 1; weights_n.append(len(t.get("weights") or {}))
            else:
                bad.append(datetime.fromtimestamp(st/1e9, tz=timezone.utc).strftime("%Y-%m-%d"))
        out["census"][fold] = {"stamps": len(stamps), "ok": ok,
                               "skipped": len(bad), "skipped_dates_head": bad[:8],
                               "weights_per_ok_stamp_head": weights_n[:5]}
        print(fold, out["census"][fold], flush=True)
    (CD / "illiq_census_y2024p.json").write_text(json.dumps(out, indent=1))
    return 0

if __name__ == "__main__":
    sys.exit(main())
