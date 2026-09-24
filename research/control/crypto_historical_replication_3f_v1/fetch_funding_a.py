"""INC-3 remediation: re-fetch funding for the A window (2024-08-20..2026-08-22)
into a SEPARATE root funding_data_scan/scan_2026_a (B stays in scan_2026)."""
import json, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path
CD = Path("/Users/hoangminhlong/my-quantitative/.worktrees/crypto-historical-replication-3f-v1/integration/research/control/crypto_historical_replication_3f_v1")
OUT = CD / "funding_data_scan/scan_2026_a"
SYMS = ["1000PEPEUSDT","AAVEUSDT","ACEUSDT","ADAUSDT","AVAXUSDT","BCHUSDT","BNBUSDT",
        "BOMEUSDT","BTCUSDT","DOGEUSDT","ENAUSDT","ETHUSDT","LINKUSDT","NEARUSDT",
        "ONGUSDT","SOLUSDT","SUIUSDT","WLDUSDT","XRPUSDT","ZECUSDT"]
W0 = 1724112000000  # 2024-08-20
W1 = 1787355900000  # 2026-08-21T23:45Z-ish upper bound
UA = {"User-Agent": "chr3f-funding/1"}
def get(url):
    req = urllib.request.Request(url, headers=UA)
    for i in range(8):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return 200, json.loads(r.read())
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception as e:
            code = repr(e)[:40]
        time.sleep(20 * (i + 1))
    return "fail", []
n = 0
for sym in SYMS:
    rows, cur = {}, W0
    while cur < W1:
        st, batch = get(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={sym}&startTime={cur}&endTime={W1}&limit=1000")
        if st != 200 or not batch: break
        for r_ in batch: rows[r_["fundingTime"]] = r_
        if len(batch) < 1000: break
        cur = max(int(r["fundingTime"]) for r in batch) + 1
        time.sleep(10.0)
    dst = OUT / sym / "funding.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    ordered = [rows[k] for k in sorted(rows)]
    dst.write_text(json.dumps({"requested_start_ms": W0, "requested_end_ms": W1,
                               "captured_at": datetime.now(timezone.utc).isoformat(),
                               "symbol": sym, "rows": ordered}, indent=2))
    n += 1
    print(sym, len(ordered), flush=True)
print("A-window funding re-staged:", n, "symbols")
