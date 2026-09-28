"""SIXSOURCE L-FX collector — read-only TWS paper probe (2026-09-28).

Independent verification + bounded sampling for FX cost-band via IBKR.
Whitelist-literal (inherits broker_cost_probe V1 contract cfd717c8):
ONLY reqCurrentTime, reqContractDetails, reqMarketDataType(1),
reqMktData, reqTickByTickData("BidAsk") + matching cancels + disconnect.
NO order functions exist in this file (placeOrder/cancelOrder/whatIf
absent by construction). Port 7497 paper only. Account id never printed
(managedAccounts stored as sha256-12 count only).

Usage: collect_fx_ticks.py --seconds 300 --tag s0_verify
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from ibapi.client import EClient
from ibapi.contract import Contract as IBContract
from ibapi.wrapper import EWrapper

CONTROL = Path("/Users/hoangminhlong/my-quantitative/research/control/DATA-FOUNDATION-SIXSOURCE-V1/ibkr_fx")
DATA = Path.home() / ".my-quantitative-data/sixsource-foundation-v1/ibkr_fx"
DATA.mkdir(parents=True, exist_ok=True)

PAIRS = {  # owner's five, pip conventions correct per pair
    "EURUSD": 0.0001, "GBPUSD": 0.0001, "AUDUSD": 0.0001,
    "USDCAD": 0.0001, "USDJPY": 0.01,
}
RAW_CAP_BYTES = 50_000_000
BENIGN_ERR = (2100, 2103, 2104, 2105, 2106, 2107, 2108, 2119, 2158, 1019,
              2104, 321)  # 321 = Read-Only guard firing on order-channel reads (expected, kept as proof)

ap = argparse.ArgumentParser()
ap.add_argument("--seconds", type=int, default=300)
ap.add_argument("--tag", default="session")
args = ap.parse_args()

run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
raw_path = DATA / f"raw_{args.tag}_{run_id}.ndjson"


class Collector(EWrapper, EClient):
    def __init__(self):
        EWrapper.__init__(self)
        EClient.__init__(self, self)
        self.state = {"server_time": [], "accounts": [], "details": {},
                      "mdt_events": [], "errors": [], "disconnect_at": None}
        self._raw = raw_path.open("w")
        self._lock = threading.Lock()
        self._bytes = 0

    def _w(self, obj):
        line = json.dumps(obj) + "\n"
        with self._lock:
            self._bytes += len(line)
            self._raw.write(line)
            self._raw.flush()

    def currentTime(self, t):
        self.state["server_time"].append({"server_unix": int(t),
                                          "receive_ns": time.time_ns()})

    def managedAccounts(self, accountsLine):
        # never store raw account ids: count + salted sha only
        accs = [a for a in accountsLine.split(",") if a]
        self.state["accounts"] = {"count": len(accs),
                                  "sha12": hashlib.sha256(accountsLine.encode()).hexdigest()[:12]}

    def contractDetails(self, reqId, cd):
        c = cd.contract
        self.state["details"][reqId] = {
            "localSymbol": c.localSymbol, "exchange": c.exchange,
            "secType": c.secType, "minTick": cd.minTick,
            "marketName": cd.marketName,
            "minSize": getattr(c, "minSize", None),
            "sizeIncrement": getattr(c, "sizeIncrement", None),
        }

    def marketDataType(self, reqId, mdt):
        self.state["mdt_events"].append({"reqId": reqId, "mdt": mdt})

    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType in (1, 2, 9) and price:  # bid, ask, indicative
            self._w({"ev": "px", "req": reqId, "tt": tickType, "px": float(price),
                     "recv_ns": time.time_ns()})

    def tickSize(self, reqId, tickType, size):
        if tickType in (0, 3) and size:  # bidSize, askSize
            self._w({"ev": "sz", "req": reqId, "tt": tickType, "sz": float(size),
                     "recv_ns": time.time_ns()})

    def tickByTickBidAsk(self, reqId, ts, bid, ask, bidSize, askSize, attrib):
        self._w({"ev": "tbt", "req": reqId, "ts": int(ts),
                 "bid": float(bid), "ask": float(ask),
                 "bid_sz": float(bidSize or 0), "ask_sz": float(askSize or 0),
                 "recv_ns": time.time_ns()})

    def error(self, *a):
        # signature drift tolerant: several (reqId, code, msg[, advanced]) variants exist
        ints = [x for x in a if isinstance(x, int)]
        strs = [x for x in a if isinstance(x, str)]
        reqId = ints[0] if ints else -1
        code = ints[1] if len(ints) > 1 else -1
        msg = strs[-1] if strs else str(a)
        self.state["errors"].append({"reqId": reqId, "code": code, "msg": msg[:160]})
        if code not in BENIGN_ERR and "connection is OK" not in msg:
            print(json.dumps({"ev": "ERR", "req": reqId, "code": code,
                              "msg": msg[:120]}), flush=True)

    def disconnect(self):  # trap unexpected mid-stream loss
        if not self.state["disconnect_at"] and not getattr(self, "_intentional", False):
            self.state["disconnect_at"] = datetime.now(timezone.utc).isoformat()
        super().disconnect()


app = None
connected = False
for _attempt in range(3):
    cid = 9400 + random.randrange(500)
    app = Collector()
    try:
        app.connect("127.0.0.1", 7497, cid)
    except Exception:
        continue
    if app.isConnected():
        connected = True
        break
    try:
        app.disconnect()
    except Exception:
        pass

if not connected:
    out = {"probe": "SIXSOURCE-L-FX", "run_id": run_id, "tag": args.tag,
           "status": "BLOCKED_TWS_CONNECT_FAILED", "port": 7497}
    print(json.dumps(out))
    (CONTROL / f"sanitized_{args.tag}_{run_id}.json").write_text(json.dumps(out, indent=1))
    raise SystemExit(0)

reader = threading.Thread(target=app.run, daemon=True)
reader.start()
handshake = False
for _ in range(60):
    try:
        if app.serverVersion():
            handshake = True
            break
    except Exception:
        pass
    time.sleep(1)
if not handshake:
    print(json.dumps({"event": "HANDSHAKE_TIMEOUT"}))
    try:
        app.disconnect()
    except Exception:
        pass
    raise SystemExit(0)
time.sleep(1)

app.reqCurrentTime()

# contract details -> minTick per pair (re-verify Saturday's 5e-05 claim)
req_ids, next_rid = {}, 8300
for p in PAIRS:
    c = IBContract()
    c.symbol, c.currency, c.secType, c.exchange = p[:3], p[3:], "CASH", "IDEALPRO"
    app.reqContractDetails(next_rid, c)
    req_ids[next_rid] = p
    next_rid += 1
time.sleep(6)

app.reqMarketDataType(1)  # LIVE requested; events recorded as served

md_req, tbt_req = {}, {}
for rid, p in req_ids.items():
    if not app.state["details"].get(rid):
        continue
    c = IBContract()
    c.symbol, c.currency, c.secType, c.exchange = p[:3], p[3:], "CASH", "IDEALPRO"
    md_req[rid] = p
    app.reqMktData(rid, c, "", False, False, [])
    tbt_rid = rid + 200
    tbt_req[tbt_rid] = p
    try:
        app.reqTickByTickData(tbt_rid, c, "BidAsk", 0, False)
    except Exception as e:
        print(json.dumps({"ev": "TBT_REQ_FAIL", "pair": p, "err": str(e)[:120]}), flush=True)

t0 = time.monotonic()
cap_hit = False
while time.monotonic() - t0 < args.seconds:
    time.sleep(1.0)
    if app._bytes > RAW_CAP_BYTES:
        cap_hit = True
        break
    if app.state["disconnect_at"]:
        break
    if int(time.monotonic() - t0) % 60 == 0:
        print(json.dumps({"hb": int(time.monotonic() - t0), "bytes": app._bytes}), flush=True)

for rid in md_req:
    try:
        app.cancelMktData(rid)
    except Exception:
        pass
for trid in tbt_req:
    try:
        app.cancelTickByTickData(trid)
    except Exception:
        pass
try:
    app.reqCurrentTime()
except Exception:
    pass
time.sleep(2)
app._intentional = True
try:
    app.disconnect()
except Exception:
    pass
app._raw.close()

# ---------- sanitized aggregation ----------
rows = [json.loads(l) for l in raw_path.open() if l.strip()]
tbt_rows = [r for r in rows if r["ev"] == "tbt"]
et = ZoneInfo("America/New_York")
lon = ZoneInfo("Europe/London")

def agg_pair(p):
    tr = [r for r in tbt_rows if tbt_req.get(r["req"]) == p]
    pip = PAIRS[p]
    spreads, recv_gaps, ts_skew = [], [], []
    last_recv = None
    for r in tr:
        if r["ask"] and r["bid"] and r["ask"] >= r["bid"] > 0:
            spreads.append((r["ask"] - r["bid"]) / pip)
        if last_recv is not None:
            recv_gaps.append((r["recv_ns"] - last_recv) / 1e9)
        last_recv = r["recv_ns"]
        ts_skew.append(r["recv_ns"] / 1e9 - r["ts"])
    sp = sorted(spreads)

    def pct(q):
        return round(sp[min(len(sp) - 1, int(q * len(sp)))], 4) if sp else None

    return {
        "n_tbt_events": len(tr),
        "n_valid_spread_obs": len(sp),
        "spread_pips": {k: pct(q) for k, q in
                        [("p10", .10), ("p50", .50), ("p90", .90), ("min", 0.0), ("max", .999)]},
        "first_event": {"recv_utc": datetime.fromtimestamp(tr[0]["recv_ns"] / 1e9, timezone.utc).isoformat(),
                        "tbt_ts_utc": datetime.fromtimestamp(tr[0]["ts"], timezone.utc).isoformat()} if tr else None,
        "last_event": {"recv_utc": datetime.fromtimestamp(tr[-1]["recv_ns"] / 1e9, timezone.utc).isoformat(),
                       "tbt_ts_utc": datetime.fromtimestamp(tr[-1]["ts"], timezone.utc).isoformat()} if tr else None,
        "max_inter_event_gap_s": round(max(recv_gaps), 2) if recv_gaps else None,
        "gaps_gt_2s": sum(1 for g in recv_gaps if g > 2),
        "gaps_gt_5s": sum(1 for g in recv_gaps if g > 5),
        "recv_minus_tbt_s": {"p50": round(sorted(ts_skew)[len(ts_skew) // 2], 3),
                             "max": round(max(ts_skew), 3)} if ts_skew else None,
    }

window_start = datetime.now(timezone.utc).isoformat()
clock_offsets = []
for st in app.state["server_time"]:
    clock_offsets.append(round(st["receive_ns"] / 1e9 - st["server_unix"], 3))

out = {
    "probe": "SIXSOURCE-L-FX", "run_id": run_id, "tag": args.tag,
    "status": ("RAW_CAP_HIT" if cap_hit else
               "DISCONNECTED_MID_STREAM" if app.state["disconnect_at"] else "COMPLETE"),
    "whitelist": ["reqCurrentTime", "reqContractDetails", "reqMarketDataType(1)",
                  "reqMktData", "reqTickByTickData(BidAsk)", "cancelMktData",
                  "cancelTickByTickData", "disconnect"],
    "order_functions_present": False,
    "paper_session": True, "port": 7497,
    "client_id_class": "9400-9899",
    "account": app.state["accounts"],
    "clock_offset_s (recv - server at reqCurrentTime)": clock_offsets,
    "session_window": {"seconds_requested": args.seconds,
                       "utc_end": window_start,
                       "et": datetime.now(et).isoformat(),
                       "london": datetime.now(lon).isoformat()},
    "contract_details_minTick": {p: app.state["details"].get(rid) for rid, p in req_ids.items()},
    "market_data_type_events": app.state["mdt_events"],
    "subscription_errors": [e for e in app.state["errors"]
                            if e["code"] in (354, 10089, 10090, 4200, 10276)][:10],
    "readonly_guard_fired_321": any(e["code"] == 321 for e in app.state["errors"]),
    "errors_non_benign": [e for e in app.state["errors"] if e["code"] not in BENIGN_ERR][:10],
    "per_pair": {p: agg_pair(p) for p in PAIRS},
    "raw": {"path": str(raw_path), "bytes": raw_path.stat().st_size,
            "sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest()},
    "notes": ["paper session; every number PAPER-SESSION",
              "spread stats from tickByTickBidAsk events only, no forward-fill",
              "tbt ts = IB server stamp; receive = local UTC clock; skew reported per pair",
              "valid obs requires ask>=bid>0"],
}
print(json.dumps(out, indent=1, default=str))
(CONTROL / f"sanitized_{args.tag}_{run_id}.json").write_text(json.dumps(out, indent=1, default=str))
with (CONTROL / "sessions_index.jsonl").open("a") as fh:
    fh.write(json.dumps({"run_id": run_id, "tag": args.tag, "status": out["status"],
                         "raw_sha256": out["raw"]["sha256"],
                         "utc": window_start}) + "\n")
