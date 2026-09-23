"""CHR3F real-data-path shape audit (A7 r1 remediation): feed the FROZEN
funding_pit.FundingPIT + funding_carry kernel with the converted staged
bundles and compute target weights at every fold stamp. Emits SHAPE ONLY
(stamp counts, skip counts, weight-map digest) — zero PnL, zero orders."""
from __future__ import annotations
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path

R = Path("/Users/hoangminhlong/my-quantitative")
CD = R / ".worktrees/crypto-historical-replication-3f-v1/integration/research/control/crypto_historical_replication_3f_v1"
V6 = CD / "recovered/v6_root"
sys.path.insert(0, str(V6))
from research.funding_carry import compute_target_weights_funding_carry  # noqa: E402

SCAN = str(CD / "funding_data_scan/scan_2026")
SYMS = ["ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","LINKUSDT","ADAUSDT"]
BENCH = "BTCUSDT"
FOLDS = {"Y2021": ("2021-01-04","2022-01-01"), "Y2022": ("2022-01-03","2023-01-01"),
         "Y2023": ("2023-01-02","2024-01-01"), "Y2020P": ("2020-10-05","2021-01-01")}
ms = lambda s: int(datetime.fromisoformat(s+"T00:00:00+00:00").timestamp()*1000)

out = {"measured_utc": datetime.now(timezone.utc).isoformat(), "folds": {}}
for fold, (a, b) in FOLDS.items():
    a_ms, b_ms = ms(a), ms(b)
    stamps, skips, digests = [], 0, []
    cur = a_ms
    while cur < b_ms:
        stamps.append(cur)
        w = compute_target_weights_funding_carry(
            signal_cutoff_ns=cur * 1_000_000, lookback_days=7,
            reverse=False, funding_bundles_dir=SCAN, traded_symbols=SYMS,
            target_gross=0.80)
        if str(w.get("status", "OK")) != "OK":
            skips += 1
        else:
            digests.append(hashlib.sha256(json.dumps(
                {"l": w.get("longs"), "s": w.get("shorts")}, sort_keys=True,
                default=str).encode()).hexdigest()[:12])
        cur += 86400_000
    out["folds"][fold] = {"stamps": len(stamps), "skips": skips,
                          "ok": len(stamps) - skips,
                          "distinct_weight_digests": len(set(digests)),
                          "first_stamp": stamps[0], "last_stamp": stamps[-1]}
out["verdict"] = ("PASS" if all(f["skips"] == 0 and f["ok"] > 0 and
                                f["distinct_weight_digests"] > 1
                                for f in out["folds"].values()) else "FAIL")
out["note"] = ("shape-only: no PnL/orders/equity computed; digests prove the "
               "kernel emits non-constant weights from the staged bundles")
(CD / "xsect_realpath_shape_verdict.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out["folds"], indent=1)); print("VERDICT:", out["verdict"])
