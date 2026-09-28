"""DT100 TWS bid/ask cost probe — read-only, paper 7497 (2026-09-28).

Owner reminder this session: "đã thiết lập bid/ask cho forex ở TWS. port 7497."
This probe MEASURES rather than trusts: streams EURUSD/GBPUSD/USDJPY quotes,
records per-pair spread distribution for the DT100 G3 freeze FX cost bill.

HARD LAWS (inherited from ERP broker_cost_probe V1 contract, cfd717c8):
- NO order functions in this file (placeOrder/cancelOrder/whatIf absent).
- Connect 127.0.0.1:7497 ONLY (paper).
- Streaming reqMktData, event-driven change-detection, no forward-fill.
- Raw -> data_local/ (not committed); sanitized aggregates -> stdout JSON.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from ib_insync import Forex, IB

LANE = Path(__file__).resolve().parent
DATA = LANE / "data_local"
DATA.mkdir(exist_ok=True)

PAIRS = {"EURUSD": 0.0001, "GBPUSD": 0.0001, "USDJPY": 0.01}
STREAM_SECONDS = 360
run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
raw_path = DATA / f"raw_ticks_{run_id}.jsonl"

ib = IB()
connected = False
try:
    ib.connect("127.0.0.1", 7497, clientId=9031, timeout=15)
    connected = ib.isConnected()
except Exception as e:  # noqa: BLE001 — record every failure class
    print(json.dumps({"event": "connect_failed", "error": str(e)[:200]}))

out = {"run_id": run_id, "component": "V1_api_connectivity",
       "status": "PASS" if connected else "FAIL", "port": 7497,
       "paper_session": True, "server_time": None}
if not connected:
    print(json.dumps(out, indent=1))
    raise SystemExit(0)

out["server_time"] = str(ib.reqCurrentTime())
out["managed_accounts_count"] = len(ib.managedAccounts())

tickers = {}
for px in PAIRS:
    c = Forex(px)
    ib.qualifyContracts(c)
    tickers[px] = ib.reqMktData(c, "", False, False)

last = {px: (None, None) for px in PAIRS}
rows = 0
t0 = time.monotonic()
with open(raw_path, "w") as fh:
    while time.monotonic() - t0 < STREAM_SECONDS:
        ib.sleep(1)
        for px, t in tickers.items():
            b, a = t.bid, t.ask
            if b and a and a > b > 0 and (b, a) != last[px]:
                last[px] = (b, a)
                pip = PAIRS[px]
                fh.write(json.dumps({"t": datetime.now(timezone.utc).isoformat(),
                                     "px": px, "bid": b, "ask": a,
                                     "spread_pips": (a - b) / pip,
                                     "spread_bps": (a - b) / ((a + b) / 2) * 1e4}) + "\n")
                rows += 1

ib.disconnect()

# sanitized aggregates
agg = {}
for px in PAIRS:
    vals = []
    with open(raw_path) as fh:
        for line in fh:
            r = json.loads(line)
            if r["px"] == px:
                vals.append(r["spread_bps"])
    if vals:
        sv = sorted(vals)
        agg[px] = {
            "quotes": len(vals),
            "median_bps": round(sv[len(sv) // 2], 3),
            "p90_bps": round(sv[int(len(sv) * 0.9)], 3),
            "max_bps": round(sv[-1], 3),
            "first_quote_utc": None,
        }
    else:
        agg[px] = {"quotes": 0, "verdict": "NO_QUOTES_NO_FFORWARD"}

out.update({"component": "V2_fx_spread_distribution", "rows_raw": rows,
            "stream_seconds": STREAM_SECONDS, "pairs": agg,
            "note": "retrieval-time live measurement (paper account); used ONLY "
                    "as broker-realizability floor cross-check for the historical "
                    "Dukascopy M1 per-bar spread bill; not a historical series."})
print(json.dumps(out, indent=1))
(LANE / f"TWS_SPREAD_PROBE_{run_id}.json").write_text(json.dumps(out, indent=1))
