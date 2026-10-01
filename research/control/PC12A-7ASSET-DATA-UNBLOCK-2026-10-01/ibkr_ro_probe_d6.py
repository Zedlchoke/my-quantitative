#!/usr/bin/env python
"""Mini-probe 3 (after my stuck worker was killed): the pieces that matter.
D6 CONTFUT ADJUSTED_LAST (decisive channel test), D1-spot redo on the BID
channel (TRADES is empty for CASH/CMDTY - channel property, PC12A used
BID/ASK), D4 entitlement with a hard 25s timeout guard. Read-only, paced.
"""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from ib_insync import IB, Contract

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/pc12a-7asset-unblock-20261001")
CTL = WT / "research/control/PC12A-7ASSET-DATA-UNBLOCK-2026-10-01"
RAW = Path.home() / ".my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/raw/ibkr_ro_20261001"
ET = ZoneInfo("America/New_York")
now_utc = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

ib = IB()
ok = False
for cid in (51, 52):
    try:
        ib.connect("127.0.0.1", 7497, clientId=cid, timeout=12, readonly=True)
        ok = True
        break
    except Exception:
        pass
if not ok:
    raise SystemExit("BLOCKED_RESOURCE_CONFLICT")

manifest_path = CTL / "MANIFEST_IBKR_RO.json"


def land(name, payload):
    b = json.dumps(payload, indent=1, default=str).encode()
    (RAW / name).write_bytes(b)
    m = json.loads(manifest_path.read_text())
    m["files"].append({"file": name, "path": str(RAW / name),
                       "retrieved_at_utc": now_utc(), "bytes": len(b),
                       "sha256": hashlib.sha256(b).hexdigest()})
    manifest_path.write_text(json.dumps(m, indent=1))
    print("LANDED", name, len(b), "B")


def mk(d):
    c = Contract()
    for k, v in d.items():
        setattr(c, k, v)
    return c

# ---- D6: CONTFUT ADJUSTED_LAST ----
d6 = {"at_utc": now_utc(), "definition": "CONTFUT whatToShow=ADJUSTED_LAST, 6Y D1"}
for name, conid in [("WTI_CONTFUT", 304037511), ("NATGAS_CONTFUT", 269460170),
                    ("BRENT_CONTFUT", 361002955)]:
    c = mk(dict(secType="CONTFUT", conId=conid))
    if not ib.qualifyContracts(c):
        d6[name] = {"status": "NOT_QUALIFIED"}
        continue
    try:
        bars = ib.reqHistoricalData(c, endDateTime="", durationStr="6 Y",
                                    barSizeSetting="1 day",
                                    whatToShow="ADJUSTED_LAST", useRTH=True,
                                    formatDate=1, keepUpToDate=False)
        rows = [{"date": b.date.strftime("%Y-%m-%d"), "close": b.close} for b in bars]
        d6[name] = {"n": len(rows), "first": rows[0]["date"] if rows else None,
                    "last": rows[-1]["date"] if rows else None,
                    "sample": rows[:3] + rows[-3:]}
    except Exception as e:
        d6[name] = {"error": f"{type(e).__name__}: {str(e)[:200]}"}
    time.sleep(3.0)
land("d6_contfut_adjusted_last.json", d6)

# ---- D1 spot/metals redo on BID channel ----
d1b = {"at_utc": now_utc(), "at_et": datetime.now(ET).strftime("%Y-%m-%dT%H:%M:%S %Z"),
       "definition": ("availability point-1 for spot/metals on the BID channel "
                      "(TRADES is empty for CASH/CMDTY HMDS - channel property; "
                      "PC12A probe used BID/ASK)")}
for name, spec in {
    "NZDUSD": dict(secType="CASH", symbol="NZD", exchange="IDEALPRO", currency="USD"),
    "USDCHF": dict(secType="CASH", symbol="USD", exchange="IDEALPRO", currency="CHF"),
    "XAUUSD": dict(secType="CMDTY", symbol="XAUUSD", exchange="SMART", currency="USD"),
    "XAGUSD": dict(secType="CMDTY", symbol="XAGUSD", exchange="SMART", currency="USD"),
}.items():
    try:
        c = mk(spec)
        if not ib.qualifyContracts(c):
            d1b[name] = {"status": "NOT_QUALIFIED"}
            continue
        bars = ib.reqHistoricalData(c, endDateTime="", durationStr="30 D",
                                    barSizeSetting="1 day", whatToShow="BID",
                                    useRTH=True, formatDate=1)
        dates = [b.date.strftime("%Y-%m-%d") for b in bars]
        today_et = datetime.now(ET).strftime("%Y-%m-%d")
        d1b[name] = {"n_last30": len(bars),
                     "last_bar_date": dates[-1] if dates else None,
                     "today_et": today_et, "has_current_et_day_bar": today_et in dates,
                     "last5": dates[-5:]}
    except Exception as e:
        d1b[name] = {"error": f"{type(e).__name__}: {str(e)[:160]}"}
    time.sleep(2.5)
land("d1b_spot_metals_bid_channel.json", d1b)

# ---- D4: entitlement with hard timeout (thread guard) ----
import concurrent.futures
d4 = {"at_utc": now_utc(), "marketDataType": 3,
      "definition": "delayed(3) reqTickers with 25s hard timeout (prior attempt hung - no entitlement ticks arrive)"}
ib.reqMarketDataType(3)
time.sleep(1)


def snap():
    return ib.reqTickers(*[mk(dict(secType=s, symbol=sym, exchange=e, currency=cur))
                            for s, sym, e, cur in [
                                ("CASH", "NZD", "IDEALPRO", "USD"),
                                ("CASH", "USD", "IDEALPRO", "CHF"),
                                ("CMDTY", "XAUUSD", "SMART", "USD"),
                                ("CMDTY", "XAGUSD", "SMART", "USD")]])
    # energy fronts omitted: conId-based FUT qualification inside thread adds risk; prior D3/PC12A evidence stands


try:
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(snap)
        tickers = fut.result(timeout=25)
    for t in tickers:
        def num(x):
            return None if x is None or x != x else x
        d4[f"{t.contract.localSymbol}"] = {
            "bid": num(t.bid), "ask": num(t.ask),
            "marketDataType": t.marketDataType}
except concurrent.futures.TimeoutError:
    d4["status"] = "TIMEOUT_25S_NO_TICKS (consistent with delayed-entitlement absent; prior session hung here indefinitely)"
except Exception as e:
    d4["error"] = f"{type(e).__name__}: {str(e)[:200]}"
land("d4_entitlement_timeout_guarded.json", d4)

ib.disconnect()
print("done")
