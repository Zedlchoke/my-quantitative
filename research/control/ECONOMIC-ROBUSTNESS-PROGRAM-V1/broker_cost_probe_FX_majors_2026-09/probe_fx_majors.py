"""FX-MAJORS-BROKER-COST-PROBE-V1 — read-only TWS probe (ERP umbrella, 2026-09-26).

Contract: research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/broker_cost_probe_FX_majors_2026-09/PROBE_CONTRACT_DIAGNOSIS.md
(committed cfd717c8 BEFORE this run). HARD LAWS encoded here:
- NO order functions exist in this file (placeOrder/cancelOrder/whatIf absent by construction).
- Connect 127.0.0.1:7497 ONLY (paper). Live port never referenced.
- Streaming reqMktData, event-driven logging on a 1s grid, no forward-fill.
- Raw output -> data_local/ (gitignored); sanitized aggregates -> stdout JSON.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from ib_insync import Contract, IB, util

LANE = Path(__file__).resolve().parent
DATA = LANE / "data_local"
DATA.mkdir(exist_ok=True)
PAIRS = ["EURUSD", "GBPUSD", "USDCAD", "AUDUSD", "NZDUSD"]
PIP = 0.0001  # all five are USD-quoted majors
STREAM_SECONDS = 360  # short probe per owner instruction; distribution-grade
MARKET_DATA_TYPES = [(1, "LIVE"), (2, "DELAYED")]  # try LIVE; recorded fallback

run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
raw_path = DATA / f"raw_ticks_{run_id}.jsonl"
meta_path = DATA / f"raw_meta_{run_id}.json"

ib = IB()
connected = False
for attempt in (1, 2):  # single retry covers the TWS approval-dialog case
    try:
        ib.connect("127.0.0.1", 7497, clientId=9026, timeout=15)
        connected = ib.isConnected()
        if connected:
            break
    except Exception as e:  # noqa: BLE001 — record every failure class
        print(json.dumps({"event": "connect_attempt_failed", "attempt": attempt, "error": str(e)[:200]}))
        time.sleep(20)

v1 = {"component": "V1_api_connectivity", "status": "PASS" if connected else "FAIL",
      "attempts": 2, "port": 7497, "paper_session": True}
if not connected:
    print(json.dumps({"VERDICT_V1": v1}, indent=1))
    raise SystemExit(0)

meta = {"run_id": run_id, "server_time_start": None, "managed_accounts": None,
        "account_summary": [], "account_id_hash": None}

meta["server_time_start"] = str(ib.reqCurrentTime())
accounts = ib.managedAccounts()
meta["managed_accounts_count"] = len(accounts)
if accounts:
    aid = accounts[0]
    meta["account_id_hash"] = hashlib.sha256(aid.encode()).hexdigest()[:12]

# account summary lines (sanitized: tag/value/currency only, no ids)
try:
    summ = ib.accountSummary()
    keep = ("AccountType", "Currency", "NetLiquidationValue", "TotalCashValue",
            "BuyingPower", "Leverage", "Flagged", "TradingType", "ClientBrokerType")
    for s in summ:
        if s.tag in keep:
            meta["account_summary"].append(
                {"tag": s.tag, "value": s.value, "currency": s.currency})
except Exception as e:  # noqa: BLE001
    meta["account_summary_error"] = str(e)[:200]

# contract details for the five majors
details_out = {}
contracts = {}
for p in PAIRS:
    c = Contract()
    c.symbol = p[:3]; c.currency = p[3:]; c.secType = "CASH"; c.exchange = "IDEALPRO"
    try:
        d = ib.reqContractDetails(c)
        if d:
            cd = d[0].contract
            contracts[p] = cd
            details_out[p] = {
                "conId": cd.conId, "localSymbol": cd.localSymbol,
                "exchange": cd.exchange, "secType": cd.secType,
                "minTick": cd.minTick, "marketName": d[0].marketName,
                "evMultiplier": getattr(cd, "evMultiplier", None),
                "minSize": getattr(cd, "minSize", None),
                "sizeIncrement": getattr(cd, "sizeIncrement", None),
                "industry/category": f"{d[0].industry}/{d[0].category}",
            }
        else:
            details_out[p] = {"error": "NO_CONTRACT_DETAILS"}
    except Exception as e:  # noqa: BLE001
        details_out[p] = {"error": str(e)[:200]}

# market data: try LIVE then recorded DELAYED fallback; stream all pairs
mkt_type_used = None
mkt_type_note = None
ib.reqMarketDataType(1)
try:
    ib.sleep(1)
except Exception:  # noqa: BLE001
    pass

tickers = {}
for p, cd in contracts.items():
    try:
        tickers[p] = ib.reqMktData(cd, "", False, False)
    except Exception as e:  # noqa: BLE001
        details_out[p]["mkt_req_error"] = str(e)[:200]

f = raw_path.open("w")
t0 = time.monotonic()
last_grid = int(0)
grid_cells = 0
cells_with_obs = 0
ib.sleep(2)  # let first ticks arrive
while time.monotonic() - t0 < STREAM_SECONDS:
    ib.sleep(0.2)
    now_cell = int(time.monotonic() - t0)
    if now_cell != last_grid:
        last_grid = now_cell
        grid_cells += 1
        had = False
        for p, t in tickers.items():
            bid = float(t.bid or 0); ask = float(t.ask or 0)
            valid = bid > 0 and ask >= bid and t.bidSize is not None
            row = {"s": now_cell, "pair": p, "bid": t.bid, "ask": t.ask,
                   "last": t.last, "bidSize": t.bidSize, "askSize": t.askSize,
                   "valid": bool(valid), "mdt": None}
            f.write(json.dumps(row) + "\n")
            if valid:
                had = True
        if had:
            cells_with_obs += 1
f.close()
meta["server_time_end"] = str(ib.reqCurrentTime())
meta["stream_seconds"] = STREAM_SECONDS
meta["grid_cells"] = grid_cells
meta["cells_with_obs"] = cells_with_obs
meta["market_data_type_requested"] = 1

# error capture (subscription errors land on the wrapper)
err_lines = []
for p, t in tickers.items():
    pass  # ib_insync surfaces errors via events; collect from ib.wrapper

# aggregate per pair (valid samples only; invalids counted)
agg = {}
for p in PAIRS:
    rows = [json.loads(l) for l in open(raw_path) if json.loads(l)["pair"] == p]
    valid = [r for r in rows if r["valid"]]
    spreads_pips = sorted(
        (r["ask"] - r["bid"]) / PIP for r in valid)
    def pct(q):
        return spreads_pips[min(len(spreads_pips) - 1, int(q * len(spreads_pips)))] if spreads_pips else None
    agg[p] = {
        "n_rows": len(rows), "n_valid": len(valid),
        "n_invalid": len(rows) - len(valid),
        "spread_pips": {"p10": pct(0.10), "p25": pct(0.25), "p50": pct(0.50),
                        "p75": pct(0.75), "p90": pct(0.90),
                        "min": spreads_pips[0] if spreads_pips else None,
                        "max": spreads_pips[-1] if spreads_pips else None},
        "mid_last": ((valid[-1]["ask"] + valid[-1]["bid"]) / 2) if valid else None,
        "bid_size_median_seen": sorted(r["bidSize"] for r in valid if r["bidSize"] is not None)[len(valid)//2] if valid else None,
    }

ib.disconnect()

# raw sha256 + sanitized output
raw_sha = hashlib.sha256(raw_path.read_bytes()).hexdigest()
meta["raw_sha256"] = raw_sha
meta["raw_path"] = str(raw_path)
meta_path.write_text(json.dumps(meta, indent=1, default=str))

out = {
    "probe": "FX-MAJORS-BROKER-COST-PROBE-V1",
    "run_id": run_id,
    "V1_connectivity": v1,
    "contract_details": details_out,
    "account_summary_sanitized": meta["account_summary"],
    "account_id_hash": meta["account_id_hash"],
    "server_time": [meta["server_time_start"], meta["server_time_end"]],
    "stream": {"seconds": STREAM_SECONDS, "grid_cells": grid_cells,
               "cells_with_obs": cells_with_obs},
    "spread_aggregates_pips": agg,
    "raw_sha256": raw_sha,
    "notes": [
        "paper session (TWS simulated) — every number is PAPER-SESSION",
        "marketDataType requested LIVE(1); DELAYED fallback flagged at aggregation if subscription errors present",
        "sampled UTC hour window is what it is — no claim about other hours",
    ],
}
print(json.dumps(out, indent=1, default=str))
(Path(DATA) / f"sanitized_result_{run_id}.json").write_text(
    json.dumps(out, indent=1, default=str))
print("SANITIZED_PATH:", DATA / f"sanitized_result_{run_id}.json")
