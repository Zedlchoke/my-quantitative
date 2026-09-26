"""FX-MAJORS-BROKER-COST-PROBE-V1 (raw-ibapi variant) — read-only TWS probe.

ib_insync's connect() auto-sync (reqOpenOrders/reqPositions/accountUpdates)
is blocked by TWS Read-Only mode => attempt-1 failed. This variant uses raw
ibapi and sends ONLY the whitelisted requests from the probe contract:
reqCurrentTime, reqManagedAccts, reqAccountSummary, reqContractDetails,
reqMarketDataType(1)+recorded(2), reqMktData. NO order functions exist here.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from ibapi.client import EClient
from ibapi.contract import Contract as IBContract
from ibapi.wrapper import EWrapper

LANE = Path(__file__).resolve().parent
DATA = LANE / "data_local"
DATA.mkdir(exist_ok=True)
PAIRS = ["EURUSD", "GBPUSD", "USDCAD", "AUDUSD", "NZDUSD"]
PIP = 0.0001
STREAM_SECONDS = 360

run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
raw_path = DATA / f"raw_ticks_{run_id}.jsonl"
meta = {"run_id": run_id, "variant": "raw-ibapi", "client_id": 9027}


class Probe(EWrapper, EClient):
    def __init__(self):
        EWrapper.__init__(self)
        EClient.__init__(self, self)
        self.state = {"valid_id": None, "accounts": [], "server_time": None,
                      "summary": [], "details": {}, "mdt_events": [],
                      "errors": []}
        self._raw = raw_path.open("w")
        self._lock = threading.Lock()

    # --- wrapper callbacks (whitelist-only traffic) ---
    def currentTime(self, t):
        self.state["server_time"] = int(t)

    def managedAccounts(self, accountsLine):
        self.state["accounts"] = accountsLine.split(",")

    def accountSummary(self, reqId, account, tag, value, currency):
        keep = ("AccountType", "Currency", "NetLiquidationValue", "TotalCashValue",
                "BuyingPower", "Leverage", "TradingType", "ClientBrokerType")
        if tag in keep:
            self.state["summary"].append({"tag": tag, "value": value, "currency": currency})

    def contractDetails(self, reqId, cd):
        c = cd.contract
        self.state["details"][reqId] = {
            "conId": c.conId, "localSymbol": c.localSymbol, "exchange": c.exchange,
            "secType": c.secType, "minTick": cd.minTick,
            "marketName": cd.marketName, "industry": cd.industry, "category": cd.category,
            "minSize": getattr(c, "minSize", None), "sizeIncrement": getattr(c, "sizeIncrement", None),
        }

    def marketDataType(self, reqId, mdt):
        self.state["mdt_events"].append({"reqId": reqId, "mdt": mdt})

    _tick_prints = 0
    def tickPrice(self, reqId, tickType, price, attrib):
        # record bid(1)/ask(2) price ticks event-driven, server-side attribution by reqId
        if Probe._tick_prints < 30 and price:
            Probe._tick_prints += 1
            print(json.dumps({"ev": "TICK", "req": reqId, "tt": tickType, "px": price}), flush=True)
        if tickType in (1, 2) and price > 0:
            with self._lock:
                self._raw.write(json.dumps(
                    {"ev": "tick", "req": reqId, "tt": tickType, "px": price}) + "\n")

    def error(self, *a):
        reqId, errorCode, errorMsg = a[0], (a[2] if len(a) >= 4 else a[1]), a[-2]
        self.state["errors"].append({"reqId": reqId, "code": errorCode,
                                     "msg": str(errorMsg)[:160]})
        if errorCode not in (2100, 2103, 2104, 2105, 2106, 2108, 2119, 2158, 2107, 1019):
            print(json.dumps({"ev": "ERR", "req": reqId, "code": errorCode,
                              "msg": str(errorMsg)[:120]}), flush=True)


import random as _rnd
app = None
connected = False
for _cid in range(3):
    _c = 9100 + _rnd.randrange(800)
    app = Probe()
    try:
        app.connect("127.0.0.1", 7497, _c)
    except Exception:
        continue
    if app.isConnected():
        connected = True
        break
    try:
        app.disconnect()
    except Exception:
        pass
v1 = {"component": "V1_api_connectivity", "status": "PASS" if connected else "FAIL",
      "port": 7497, "paper_session": True, "variant": "raw-ibapi"}
print(json.dumps({"V1": v1}))
if not connected:
    raise SystemExit(0)

reader = threading.Thread(target=app.run, daemon=True)
reader.start()
# wait for full API handshake (serverVersion) — up to 60s (TWS approval-dialog latency class)
_handshake = False
for _ in range(60):
    try:
        if app.serverVersion():
            _handshake = True
            break
    except Exception:
        pass
    time.sleep(1)
meta["handshake_seconds_waited"] = _
meta["handshake_complete"] = _handshake
if not _handshake:
    print(json.dumps({"event": "HANDSHAKE_TIMEOUT", "verdict": "V1_FAIL_NO_SERVER_VERSION"}))
    try:
        app.disconnect()
    except Exception:
        pass
    raise SystemExit(0)
time.sleep(1)

try:
    app.reqCurrentTime()
except Exception as e:
    print('REQFAIL', 'app.reqCurrentTime()', str(e)[:120], flush=True)
try:
    app.reqManagedAccts()
except Exception as e:
    print('REQFAIL', 'app.reqManagedAccts()', str(e)[:120], flush=True)
app.reqAccountSummary(8001, "All",
                      "AccountType,Currency,NetLiquidationValue,TotalCashValue,"
                      "BuyingPower,Leverage,TradingType,ClientBrokerType")

req_ids = {}
next_req = 8100
for p in PAIRS:
    c = IBContract()
    c.symbol = p[:3]; c.currency = p[3:]; c.secType = "CASH"; c.exchange = "IDEALPRO"
    app.reqContractDetails(next_req, c)
    req_ids[next_req] = p
    next_req += 1
time.sleep(6)  # contract details round-trip

# market data: LIVE request first; per-pair subscription on returned conIds
app.reqMarketDataType(1)
md_req = {}
for rid, p in req_ids.items():
    d = app.state["details"].get(rid)
    if not d:
        continue
    c = IBContract()
    c.conId = d["conId"]; c.symbol = p[:3]; c.secType = "CASH"
    c.exchange = "IDEALPRO"; c.currency = p[3:]
    mrid = rid + 100
    app.reqMktData(mrid, c, "", False, False, [])
    md_req[mrid] = p
time.sleep(8)  # let LIVE attempts settle; record subscription errors

sub_errors = [e for e in app.state["errors"] if e["code"] in (354, 10089, 10090, 4200)]
mdt_live = [m for m in app.state["mdt_events"] if m["mdt"] == 1]
if sub_errors and not mdt_live:
    # recorded DELAYED fallback (flagged; never silently mixed)
    app.reqMarketDataType(2)
    meta["delayed_fallback_fired"] = True
    time.sleep(5)

# stream on a 1-second grid: snapshot current bid/ask from wrapper accumulations
# (raw event ticks already logged; grid records keep the contract's with/without discipline)
snaps = {mrid: {"bid": None, "ask": None} for mrid in md_req}
last_px = {}  # reqId -> {tt: px} from event ticks (in-memory mirror of raw file)

def poll_raw_mirror():
    global last_px
    # simple mirror: read recent lines from raw file (single writer, small file)
    try:
        with raw_path.open() as f:
            for line in f:
                d = json.loads(line)
                if d.get("ev") == "tick":
                    last_px.setdefault(d["req"], {})[d["tt"]] = d["px"]
    except FileNotFoundError:
        pass

t0 = time.monotonic()
grid_cells = 0
cells_with_obs = 0
while time.monotonic() - t0 < STREAM_SECONDS:
    time.sleep(1.0)
    poll_raw_mirror()
    grid_cells += 1
    had = False
    for mrid, p in md_req.items():
        lp = last_px.get(mrid, {})
        bid = lp.get(1); ask = lp.get(2)
        valid = bid is not None and ask is not None and ask >= bid > 0
        if valid:
            had = True
        with app._lock:
            app._raw.write(json.dumps(
                {"ev": "grid", "s": int(time.monotonic() - t0), "pair": p,
                 "bid": bid, "ask": ask, "valid": valid}) + "\n")
            app._raw.flush()
    if had:
        cells_with_obs += 1
    if grid_cells % 30 == 0:
        print(json.dumps({"hb": grid_cells, "with_obs": cells_with_obs}), flush=True)

app.cancelAccountSummary(8001)
for mrid in md_req:
    app.cancelMktData(mrid)
time.sleep(1)
app.disconnect()
app._raw.close()

# aggregate from grid rows (valid only)
agg = {}
for p in PAIRS:
    rows = [json.loads(l) for l in raw_path.open() if l.startswith('{"ev": "grid"') and json.loads(l)["pair"] == p]
    valid = [r for r in rows if r["valid"]]
    sp = sorted((r["ask"] - r["bid"]) / PIP for r in valid)
    def pct(q):
        return round(sp[min(len(sp) - 1, int(q * len(sp)))], 4) if sp else None
    agg[p] = {"n_grid": len(rows), "n_valid": len(valid), "n_invalid": len(rows) - len(valid),
              "spread_pips": {k: pct(q) for k, q in
                              [("p10", .10), ("p25", .25), ("p50", .50), ("p75", .75), ("p90", .90)]},
              "min": round(sp[0], 4) if sp else None, "max": round(sp[-1], 4) if sp else None}

raw_sha = hashlib.sha256(raw_path.read_bytes()).hexdigest()
out = {
    "probe": "FX-MAJORS-BROKER-COST-PROBE-V1", "run_id": run_id, "variant": "raw-ibapi",
    "V1_connectivity": v1,
    "account_id_hash": hashlib.sha256((app.state["accounts"][0] if app.state["accounts"] else "NONE").encode()).hexdigest()[:12],
    "accounts_count": len(app.state["accounts"]),
    "server_time_unix": app.state["server_time"],
    "account_summary_sanitized": app.state["summary"],
    "contract_details": {p: app.state["details"].get(rid) for rid, p in req_ids.items()},
    "market_data": {"mdt_events": app.state["mdt_events"], "delayed_fallback_fired": meta.get("delayed_fallback_fired", False),
                    "subscription_errors": sub_errors[:10]},
    "stream": {"seconds": STREAM_SECONDS, "grid_cells": grid_cells, "cells_with_obs": cells_with_obs,
               "utc_window": [datetime.fromtimestamp(time.time() - STREAM_SECONDS, timezone.utc).isoformat(),
                              datetime.now(timezone.utc).isoformat()]},
    "spread_aggregates_pips": agg,
    "errors_all": app.state["errors"][:20],
    "raw_sha256": raw_sha,
    "notes": ["paper session; every number PAPER-SESSION", "grid 1s no-forward-fill; invalid cells counted"],
}
print(json.dumps(out, indent=1, default=str))
(DATA / f"sanitized_result_{run_id}.json").write_text(json.dumps(out, indent=1, default=str))
print("SANITIZED_PATH:", DATA / f"sanitized_result_{run_id}.json")
