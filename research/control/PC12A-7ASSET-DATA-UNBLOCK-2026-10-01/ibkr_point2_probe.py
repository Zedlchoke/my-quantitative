#!/usr/bin/env python
"""IBKR D1 point-2 persistence probe (next-business-day re-run of D1b/D1).

Validity gate: ET calendar date must be >= 2026-10-01 (Thursday) — i.e. UTC
>= 2026-10-01T04:00Z. If not valid: prints NOT_RUN_TIME_WINDOW + next time
and exits 0 WITHOUT connecting. Bounded: connect timeout 12s, readonly=True,
clientId 61/62, no orders/account. Lands d1_point2_*.json + manifest append.
Compares vs point-1 files and emits a machine comparison block.
"""
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

CTL = Path("/Users/hoangminhlong/my-quantitative/.worktrees/pc12a-7asset-unblock-20261001/research/control/PC12A-7ASSET-DATA-UNBLOCK-2026-10-01")
RAW = Path.home() / ".my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/raw/ibkr_ro_20261001"
ET = ZoneInfo("America/New_York")
now_utc = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

et_now = datetime.now(ET)
if et_now.strftime("%Y-%m-%d") < "2026-10-01":
    print(json.dumps({
        "verdict": "NOT_RUN_TIME_WINDOW",
        "measured_at_utc": now_utc(),
        "reason": f"ET calendar date is {et_now.strftime('%Y-%m-%d')} (< 2026-10-01 Thursday)",
        "next_observation_time_utc": "2026-10-01T04:00:00Z (= 2026-10-01 00:00 EDT, Thursday ET)",
        "note": "no connector self-scheduled; run this script again at/after that time"}, indent=1))
    sys.exit(0)

from ib_insync import IB, Contract
ib = IB()
connected = False
err = ""
for cid in (61, 62):
    try:
        ib.connect("127.0.0.1", 7497, clientId=cid, timeout=12, readonly=True)
        connected = True
        break
    except Exception as e:
        err = f"{type(e).__name__}: {str(e)[:140]}"
if not connected:
    rec = {"verdict": "NOT_RUN_TWS_HANDSHAKE", "measured_at_utc": now_utc(),
           "at_et": et_now.strftime("%Y-%m-%dT%H:%M:%S %Z"),
           "handshake_error": err,
           "note": "port listener state is NOT entitlement evidence; handshake outcome recorded verbatim; re-run when TWS serves API clients",
           "script": "ibkr_point2_probe.py (identical re-run)"}
    (RAW / "d1_point2_status.json").write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec, indent=1))
    sys.exit(0)

srv = ib.reqCurrentTime()
out = {"verdict": "RUN", "at_utc": now_utc(),
       "at_et": et_now.strftime("%Y-%m-%dT%H:%M:%S %Z"),
       "server_time_utc": str(srv), "clientId": cid, "readonly": True}

def mk(d):
    c = Contract()
    for k, v in d.items():
        setattr(c, k, v)
    return c

TARGETS = {
    "NZDUSD": (dict(secType="CASH", symbol="NZD", exchange="IDEALPRO", currency="USD"), "BID"),
    "USDCHF": (dict(secType="CASH", symbol="USD", exchange="IDEALPRO", currency="CHF"), "BID"),
    "XAUUSD": (dict(secType="CMDTY", symbol="XAUUSD", exchange="SMART", currency="USD"), "BID"),
    "XAGUSD": (dict(secType="CMDTY", symbol="XAGUSD", exchange="SMART", currency="USD"), "BID"),
    "BRENT_COIL_front": (dict(secType="FUT", conId=361002948), "TRADES"),
    "WTI_CL_front": (dict(secType="FUT", conId=304037511), "TRADES"),
    "NATGAS_NG_front": (dict(secType="FUT", conId=269460170), "TRADES"),
}
for name, (spec, chan) in TARGETS.items():
    try:
        c = mk(spec)
        if not ib.qualifyContracts(c):
            out[name] = {"status": "NOT_QUALIFIED"}
            continue
        bars = ib.reqHistoricalData(c, endDateTime="", durationStr="10 D",
                                    barSizeSetting="1 day", whatToShow=chan,
                                    useRTH=True, formatDate=1)
        out[name] = {"channel": chan, "n": len(bars),
                     "bars": [{"date": b.date.strftime("%Y-%m-%d"),
                               "close": b.close} for b in bars]}
        time.sleep(2.5)
    except Exception as e:
        out[name] = {"error": f"{type(e).__name__}: {str(e)[:160]}"}
        time.sleep(2.5)
ib.disconnect()

# ---- comparison vs point-1 ----
cmp = {"definition": "persistence: does the 2026-09-30 closed bar persist with the same close; is a 2026-10-01 bar present now (closed at 17:00 ET if queried after)"}
p1_fx = json.loads((RAW / "d1b_spot_metals_bid_channel.json").read_text())
p1_en = json.loads((RAW / "d1_lastbars_availability_point1_FIXED.json").read_text())
for name in TARGETS:
    row = out.get(name, {})
    bars = row.get("bars") or []
    closes = {b["date"]: b["close"] for b in bars}
    sep30 = closes.get("2026-09-30")
    oct01 = closes.get("2026-10-01")
    # point-1 references
    if name in p1_fx and "last5" in p1_fx[name]:
        p1_dates = p1_fx[name]["last5"]
    elif name in p1_en and "last5" in p1_en.get(name, {}):
        p1_dates = p1_en[name]["last5"]
    else:
        p1_dates = None
    cmp[name] = {"sep30_present": sep30 is not None, "sep30_close": sep30,
                 "oct01_present": oct01 is not None, "oct01_close": oct01,
                 "p1_last5": p1_dates,
                 "oct01_is_closed_session": et_now.strftime("%H:%M") >= "17:00" or None}
out["comparison_vs_point1"] = cmp

b = json.dumps(out, indent=1).encode()
(RAW / "d1_point2_result.json").write_bytes(b)
mp = CTL / "MANIFEST_IBKR_RO.json"
m = json.loads(mp.read_text())
m["files"].append({"file": "d1_point2_result.json", "path": str(RAW / "d1_point2_result.json"),
                   "retrieved_at_utc": now_utc(), "bytes": len(b),
                   "sha256": hashlib.sha256(b).hexdigest(),
                   "note": "point-2 next-business-day persistence probe (owner-authorized 7497 read-only)"})
m["generated_at_utc"] = now_utc()
mp.write_text(json.dumps(m, indent=1))
print(json.dumps(cmp, indent=1))
