#!/usr/bin/env python
"""Fix-up probe for session-2 IBKR RO (corrected API signatures) + one new
channel test: D6 CONTFUT whatToShow='ADJUSTED_LAST' (P-7 bundle!=endpoint:
ADJUSTED_LAST is a distinct HMDS channel never tested by the PC12A probe).
Read-only, paced, no orders/account. Appends to MANIFEST_IBKR_RO.json.
"""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from ib_insync import IB, Contract
from zoneinfo import ZoneInfo

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/pc12a-7asset-unblock-20261001")
CTL = WT / "research/control/PC12A-7ASSET-DATA-UNBLOCK-2026-10-01"
RAW = Path.home() / ".my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/raw/ibkr_ro_20261001"
ET = ZoneInfo("America/New_York")
now_utc = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

ib = IB()
ok = False
for cid in (47, 48, 49):
    try:
        ib.connect("127.0.0.1", 7497, clientId=cid, timeout=12, readonly=True)
        ok = True
        break
    except Exception as e:
        print("connect fail", type(e).__name__)
if not ok:
    raise SystemExit("BLOCKED_RESOURCE_CONFLICT")

SPOT = {
    "NZDUSD": dict(secType="CASH", symbol="NZD", exchange="IDEALPRO", currency="USD"),
    "USDCHF": dict(secType="CASH", symbol="USD", exchange="IDEALPRO", currency="CHF"),
    "XAUUSD": dict(secType="CMDTY", symbol="XAUUSD", exchange="SMART", currency="USD"),
    "XAGUSD": dict(secType="CMDTY", symbol="XAGUSD", exchange="SMART", currency="USD"),
}
FRONTS = {
    "BRENT_COIL_front": dict(secType="FUT", conId=361002948),
    "WTI_CL_front": dict(secType="FUT", conId=304037511),
    "NATGAS_NG_front": dict(secType="FUT", conId=269460170),
}
CONTFUT = {
    "WTI_CONTFUT": dict(secType="CONTFUT", conId=304037511),
    "NATGAS_CONTFUT": dict(secType="CONTFUT", conId=269460170),
    "BRENT_CONTFUT": dict(secType="CONTFUT", conId=361002955),
}

def mk(d):
    c = Contract()
    for k, v in d.items():
        setattr(c, k, v)
    return c

manifest_path = CTL / "MANIFEST_IBKR_RO.json"
manifest = json.loads(manifest_path.read_text())["files"]

def land(name, payload):
    global manifest
    b = json.dumps(payload, indent=1, default=str).encode()
    (RAW / name).write_bytes(b)
    manifest.append({"file": name, "path": str(RAW / name),
                     "retrieved_at_utc": now_utc(), "bytes": len(b),
                     "sha256": hashlib.sha256(b).hexdigest()})
    print("LANDED", name, len(b), "B")

# ---- D1 fixed: availability point-1 (correct reqHeadTimeStamp signature) ----
d1 = {"at_utc": now_utc(), "at_et": datetime.now(ET).strftime("%Y-%m-%dT%H:%M:%S %Z"),
      "definition": "access-time availability point-1 (fixed signatures); point-2 = identical re-run next business day"}
for name, spec in {**SPOT, **FRONTS}.items():
    try:
        c = mk(spec)
        if not ib.qualifyContracts(c):
            d1[name] = {"status": "NOT_QUALIFIED"}
            continue
        try:
            head = ib.reqHeadTimeStamp(c, "TRADES", True)
        except TypeError:
            head = ib.reqHeadTimeStamp(c)
        bars = ib.reqHistoricalData(c, endDateTime="", durationStr="30 D",
                                    barSizeSetting="1 day", whatToShow="TRADES",
                                    useRTH=True, formatDate=1)
        dates = [b.date.strftime("%Y-%m-%d") for b in bars]
        today_et = datetime.now(ET).strftime("%Y-%m-%d")
        d1[name] = {"conId": c.conId, "localSymbol": c.localSymbol,
                    "head_ts": str(head)[:19], "n_last30": len(bars),
                    "last_bar_date": dates[-1] if dates else None,
                    "today_et": today_et, "has_current_et_day_bar": today_et in dates,
                    "last5": dates[-5:]}
        time.sleep(2.5)
    except Exception as e:
        d1[name] = {"status": "ERROR", "error": f"{type(e).__name__}: {str(e)[:160]}"}
        time.sleep(2.5)
land("d1_lastbars_availability_point1_FIXED.json", d1)

# ---- D4 fixed: delayed entitlement via reqTickers ----
ib.reqMarketDataType(3)
time.sleep(1)
d4 = {"at_utc": now_utc(), "at_et": datetime.now(ET).strftime("%Y-%m-%dT%H:%M:%S %Z"),
      "marketDataType": 3, "definition": "delayed(3) snapshot entitlement probe via reqTickers, 8s settle"}
try:
    targets = {}
    for name, spec in {**SPOT, **FRONTS}.items():
        c = mk(spec)
        if ib.qualifyContracts(c):
            targets[name] = c
    time.sleep(2)
    tickers = ib.reqTickers(*targets.values())
    for name, c in targets.items():
        t = next((x for x in tickers if x.contract.conId == c.conId), None)
        if t is None:
            d4[name] = {"status": "NO_TICKER"}
            continue
        def num(x):
            return None if x is None or x != x else x
        d4[name] = {"conId": c.conId, "bid": num(t.bid), "ask": num(t.ask),
                    "last": num(t.last), "close": num(t.close),
                    "marketDataType": t.marketDataType,
                    "snapshot_read_at_utc": now_utc()}
except Exception as e:
    d4["error"] = f"{type(e).__name__}: {str(e)[:200]}"
land("d4_entitlement_delayed_FIXED.json", d4)

# ---- D6 NEW channel: CONTFUT ADJUSTED_LAST ----
d6 = {"at_utc": now_utc(),
      "definition": ("whatToShow='ADJUSTED_LAST' on CONTFUT - distinct HMDS "
                     "channel never tested by the PC12A probe (P-7); if it "
                     "returns 6Y dailies, IBKR serves its own back-adjusted "
                     "continuous series and the roll-rule question changes")}
for name, spec in CONTFUT.items():
    try:
        c = mk(spec)
        if not ib.qualifyContracts(c):
            d6[name] = {"status": "NOT_QUALIFIED"}
            continue
        bars = ib.reqHistoricalData(c, endDateTime="", durationStr="6 Y",
                                    barSizeSetting="1 day",
                                    whatToShow="ADJUSTED_LAST", useRTH=True,
                                    formatDate=1, keepUpToDate=False)
        rows = [{"date": b.date.strftime("%Y-%m-%d"), "open": b.open,
                 "high": b.high, "low": b.low, "close": b.close,
                 "volume": b.volume} for b in bars]
        d6[name] = {"n": len(rows), "first": rows[0]["date"] if rows else None,
                    "last": rows[-1]["date"] if rows else None, "bars": rows}
        print(f"  D6 {name} n={len(rows)}")
        time.sleep(3.0)
    except Exception as e:
        d6[name] = {"error": f"{type(e).__name__}: {str(e)[:200]}"}
        time.sleep(3.0)
land("d6_contfut_adjusted_last.json", d6)

ib.disconnect()
m = json.loads(manifest_path.read_text())
m["files"] = manifest
m["fixup_note"] = "session-2 fix-ups: corrected reqHeadTimeStamp/reqTickers signatures + D6 ADJUSTED_LAST channel test"
manifest_path.write_text(json.dumps(m, indent=1))
print("manifest updated:", len(manifest), "files")
