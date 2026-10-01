#!/usr/bin/env python
"""IBKR TWS 7497 READ-ONLY probe, session 2 of PC12A-7ASSET-DATA-UNBLOCK-2026-10-01.

Owner authorization 2026-10-01: "IBKR 7497 read-only". Hard limits honored:
NO orders (no placeOrder/cancelOrder/whatIf), NO account data requests, NO
credential transmission (localhost socket needs none), paced HMDS pulls
(PC12A-probe precedent: no heavy-lock acquisition for a paced pull).

Sections:
  D0 connect + server clock (availability evidence anchor)
  D1 access-time availability point-1: last D1 bar per instrument vs
     wall-clock now (second point = tomorrow's re-run of this same script,
     PREPARED but not self-scheduled; owner/successor runs it)
  D2 expired-month outright resolution test (includeExpired=True) for
     CL/NG/COIL months 2020-2025 + D1 bars for the first resolved ones
     -> decides whether a self-built documented outright chain is possible
  D3 energy front BID/ASK D1 last 30d (lands raw; replaces F-3 REPORT_ONLY)
  D4 entitlement re-measure: delayed(3) snapshots for 4 spot/metals + 3
     energy fronts (weekday session, timestamped)
  D5 CONTFUT contractDetails dump (roll/adjustment metadata check)

All outputs -> ~/.my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/
raw/ibkr_ro_20261001/ + MANIFEST_IBKR_RO.json (sha256 per file) in the
control dir. Fail-closed on connection refusal (BLOCKED_RESOURCE_CONFLICT).
"""
from __future__ import annotations
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from ib_insync import IB, Contract, Future, util
from zoneinfo import ZoneInfo

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/pc12a-7asset-unblock-20261001")
CTL = WT / "research/control/PC12A-7ASSET-DATA-UNBLOCK-2026-10-01"
RAW = Path.home() / ".my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/raw/ibkr_ro_20261001"
RAW.mkdir(parents=True, exist_ok=True)
ET = ZoneInfo("America/New_York")
now_utc = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
now_et = lambda: datetime.now(ET).strftime("%Y-%m-%dT%H:%M:%S %Z")
manifest = []


def land(name, payload):
    b = (json.dumps(payload, indent=1, default=str)).encode()
    p = RAW / name
    p.write_bytes(b)
    manifest.append({"file": name, "path": str(p), "retrieved_at_utc": now_utc(),
                     "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
    print(f"LANDED {name} ({len(b)}B)")


# ------------------------------------------------------------------- D0 ----
ib = IB()
connected = False
for cid in (47, 48, 49):
    try:
        ib.connect("127.0.0.1", 7497, clientId=cid, timeout=12, readonly=True)
        connected = True
        print(f"connected clientId={cid} readonly=True")
        break
    except Exception as e:
        print(f"connect cid={cid} failed: {type(e).__name__}: {str(e)[:120]}")
if not connected:
    land("conn_refused.json", {"status": "BLOCKED_RESOURCE_CONFLICT",
                               "at_utc": now_utc(), "port": 7497,
                               "note": "TWS listening but API client refused (busy/disabled); fail-closed"})
    raise SystemExit(0)

srv_time = ib.reqCurrentTime()
land("conn_and_clock.json", {
    "connected": True, "clientId": cid, "readonly": True,
    "server_time_utc": str(srv_time), "local_utc": now_utc(), "local_et": now_et(),
    "ib_insync_version": util.__version__ if hasattr(util, "__version__") else "n/a",
    "note": "read-only socket; no orders; no account data requested"})

SPOT = {
    "NZDUSD": dict(secType="CASH", symbol="NZD", exchange="IDEALPRO", currency="USD"),
    "USDCHF": dict(secType="CASH", symbol="USD", exchange="IDEALPRO", currency="CHF"),
    "XAUUSD": dict(secType="CMDTY", symbol="XAUUSD", exchange="SMART", currency="USD"),
    "XAGUSD": dict(secType="CMDTY", symbol="XAGUSD", exchange="SMART", currency="USD"),
}
FRONTS = {
    "BRENT_COIL_front": dict(secType="FUT", conId=361002948),   # COILX6, PC12A probe
    "WTI_CL_front": dict(secType="FUT", conId=304037511),       # CLX6
    "NATGAS_NG_front": dict(secType="FUT", conId=269460170),    # NGX26
}
CONTFUT = {
    "BRENT_CONTFUT": dict(secType="CONTFUT", conId=361002955),
    "WTI_CONTFUT": dict(secType="CONTFUT", conId=304037511),
    "NATGAS_CONTFUT": dict(secType="CONTFUT", conId=269460170),
}


def mk(d):
    c = Contract()
    for k, v in d.items():
        setattr(c, k, v)
    return c


def qual(d):
    c = mk(d)
    qs = ib.qualifyContracts(c)
    return c if qs else None

# ------------------------------------------------------------------- D1 ----
d1 = {"at_utc": now_utc(), "at_et": now_et(),
      "definition": ("access-time availability point-1: last retrievable D1 "
                     "bar per instrument at wall-clock now; point-2 = re-run "
                     "next business day (script identical) closes the bracket")}
for name, spec in {**SPOT, **FRONTS}.items():
    try:
        c = qual(spec)
        if not c:
            d1[name] = {"status": "NOT_QUALIFIED"}
            continue
        head = ib.reqHeadTimeStamp(c)
        bars = ib.reqHistoricalData(c, endDateTime="", durationStr="30 D",
                                    barSizeSetting="1 day", whatToShow="TRADES",
                                    useRTH=True, formatDate=1)
        dates = [b.date.strftime("%Y-%m-%d") for b in bars]
        today = datetime.now(ET).strftime("%Y-%m-%d")
        d1[name] = {"conId": c.conId, "localSymbol": c.localSymbol,
                    "head_ts": str(head)[:19], "n_last30": len(bars),
                    "last_bar_date": dates[-1] if dates else None,
                    "has_today_bar": today in dates,
                    "last5": dates[-5:]}
        time.sleep(2.5)
    except Exception as e:
        d1[name] = {"status": "ERROR", "error": f"{type(e).__name__}: {str(e)[:160]}"}
        time.sleep(2.5)
land("d1_lastbars_availability_point1.json", d1)

# ------------------------------------------------------------------- D2 ----
EXPIRED = {
    "WTI": [("CL", "NYMEX", m) for m in ["CLZ20", "CLF21", "CLG21", "CLZ21", "CLZ22", "CLZ23", "CLZ24", "CLF25"]],
    "NATGAS": [("NG", "NYMEX", m) for m in ["NGZ20", "NGF21", "NGZ23", "NGF25"]],
    "BRENT": [("COIL", "IPE", m) for m in ["COILZ20", "COILF21", "COILZ23", "COILF25"]],
}
res = {"at_utc": now_utc(),
       "definition": ("reqContractDetails includeExpired=True per expired "
                      "localSymbol; resolved conIds then get D1 TRADES bars "
                      "to test outright-chain self-construction")}
resolved_any = []
for fam, rows in EXPIRED.items():
    for sym, exch, loc in rows:
        f = Future(symbol=sym, exchange=exch, localSymbol=loc, includeExpired=True)
        try:
            dets = ib.reqContractDetails(f)
            if dets:
                cd = dets[0].contract
                key = f"{fam}:{loc}"
                res[key] = {"resolved": True, "conId": cd.conId,
                            "lastTradeDateOrContractMonth": cd.lastTradeDateOrContractMonth,
                            "expiry_detail": dets[0].liquidHours is not None}
                resolved_any.append((fam, loc, cd))
            else:
                res[f"{fam}:{loc}"] = {"resolved": False, "note": "empty details"}
        except Exception as e:
            res[f"{fam}:{loc}"] = {"resolved": False,
                                    "error": f"{type(e).__name__}: {str(e)[:120]}"}
        time.sleep(2.0)
land("d2_expired_month_resolution.json", res)

hist_out = {"at_utc": now_utc(),
            "definition": "D1 TRADES for resolved expired months; bars inline"}
for fam, loc, cd in resolved_any[:8]:
    try:
        bars = ib.reqHistoricalData(cd, endDateTime="", durationStr="3 Y",
                                    barSizeSetting="1 day", whatToShow="TRADES",
                                    useRTH=True, formatDate=1, includeExpired=True)
        rows = [{"date": b.date.strftime("%Y-%m-%d"), "open": b.open, "high": b.high,
                 "low": b.low, "close": b.close, "volume": b.volume} for b in bars]
        hist_out[f"{fam}:{loc}"] = {"n": len(rows),
                                    "first": rows[0]["date"] if rows else None,
                                    "last": rows[-1]["date"] if rows else None,
                                    "bars": rows}
        print(f"  expired hist {fam}:{loc} n={len(rows)}")
        time.sleep(3.0)
    except Exception as e:
        hist_out[f"{fam}:{loc}"] = {"error": f"{type(e).__name__}: {str(e)[:160]}"}
        time.sleep(3.0)
land("d2_expired_month_hist.json", hist_out)

# ------------------------------------------------------------------- D3 ----
d3 = {"at_utc": now_utc(), "definition": "front BID/ASK D1 last 30d, both sides"}
for name, spec in FRONTS.items():
    try:
        c = qual(spec)
        row = {}
        for side in ("BID", "ASK"):
            bars = ib.reqHistoricalData(c, endDateTime="", durationStr="30 D",
                                        barSizeSetting="1 day", whatToShow=side,
                                        useRTH=True, formatDate=1)
            row[side] = [{"date": b.date.strftime("%Y-%m-%d"), "close": b.close}
                         for b in bars]
            time.sleep(2.5)
        d3[name] = row
    except Exception as e:
        d3[name] = {"error": f"{type(e).__name__}: {str(e)[:160]}"}
        time.sleep(2.5)
land("d3_energy_front_bidask_30d.json", d3)

# ------------------------------------------------------------------- D4 ----
ib.reqMarketDataType(3)  # delayed
time.sleep(1)
d4 = {"at_utc": now_utc(), "at_et": now_et(), "marketDataType": 3,
      "definition": "delayed snapshot entitlement probe (8s wait), weekday"}
snap_targets = {}
for name, spec in {**SPOT, **FRONTS}.items():
    c = qual(spec)
    if c:
        snap_targets[name] = c
try:
    tickers = ib.reqMktDataSnapshots(list(snap_targets.values()))
    time.sleep(8)
    tickers = ib.reqMktDataSnapshots(list(snap_targets.values()))
    for name, c in snap_targets.items():
        t = next((x for x in tickers if x.contract.conId == c.conId), None)
        if t is None:
            d4[name] = {"status": "NO_TICKER"}
            continue
        d4[name] = {"conId": c.conId,
                    "bid": t.bid if t.bid != t.bid else None,
                    "ask": t.ask if t.ask != t.ask else None,
                    "last": t.last if t.last != t.last else None,
                    "marketDataType": t.marketDataType,
                    "snapshot_read_at_utc": now_utc()}
        time.sleep(1.0)
except Exception as e:
    d4["error"] = f"{type(e).__name__}: {str(e)[:200]}"
land("d4_entitlement_delayed_snapshots.json", d4)

# ------------------------------------------------------------------- D5 ----
d5 = {"at_utc": now_utc(), "definition": "CONTFUT contractDetails full dump (roll/adjustment metadata search)"}
for name, spec in CONTFUT.items():
    try:
        c = qual(spec)
        if not c:
            d5[name] = {"status": "NOT_QUALIFIED"}
            continue
        dets = ib.reqContractDetails(c)
        if dets:
            dd = dets[0]
            d5[name] = {"conId": c.conId, "localSymbol": c.localSymbol,
                        "secType": c.secType, "exchange": c.exchange,
                        "longName": dd.longName, "validExchanges": dd.validExchanges,
                        "timeZoneId": dd.timeZoneId,
                        "adjustment_method_present": any(
                            k for k in dir(dd) if "adjust" in k.lower() and getattr(dd, k, None)),
                        "all_nonnull_fields": {k: str(getattr(dd, k))
                                               for k in dir(dd)
                                               if not k.startswith("_")
                                               and not callable(getattr(dd, k, None))
                                               and getattr(dd, k, None) not in (None, "", [], -1)}}
        time.sleep(2.0)
    except Exception as e:
        d5[name] = {"error": f"{type(e).__name__}: {str(e)[:160]}"}
        time.sleep(2.0)
land("d5_contfut_details_rollcheck.json", d5)

ib.disconnect()
print("disconnected cleanly")

(CTL / "MANIFEST_IBKR_RO.json").write_text(json.dumps({
    "schema": "pc12a_7asset_ibkr_ro_manifest@1",
    "session": "PC12A-7ASSET-DATA-UNBLOCK-2026-10-01 (session 2, owner-directed lane continuation)",
    "generated_at_utc": now_utc(),
    "authorization": "owner instruction 2026-10-01: IBKR 7497 read-only; no orders/account/keys",
    "raw_dir": str(RAW),
    "files": manifest}, indent=1))
print(f"MANIFEST_IBKR_RO.json written ({len(manifest)} files)")
