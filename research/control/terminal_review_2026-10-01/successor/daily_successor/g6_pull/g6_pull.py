#!/usr/bin/env python
"""G6 DATA-ACQUISITION lane: IBKR HMDS daily BID/ASK pull for AUDUSD/USDCAD.

Owner-authorized 2026-10-01 (G6 lane dispatch). Implements option (a) of
G5_G6_SPREADS_INPUTEND.md section 2.2: extend the AUD/CA D1 input side
2026-07-01 -> 2026-09-30 via the same read-only 7497 session pattern and
the acquire_bounded.py method (identity resolution first, bounded 1-day
BID/ASK chunks, sha-frozen, acquisition-report pattern).

LAWS honored (from the dispatch):
  READ-ONLY: ib.connect(..., readonly=True); NO orders, NO whatIf, NO
  account-data requests (managedAccounts arrives in the handshake; only a
  count + DU-paper boolean is recorded, never the ids); no market-data
  subscription requests beyond HMDS historical (no reqMktData at all).
  PACED: 10.5 s between HMDS calls (acquire_bounded.py fetch discipline;
  exceeds the >=3 s dispatch minimum), 2.5 s after contractDetails calls.
  PIT: every request end-bounded at "2026093? 23:59:59 UTC" <= 2026-09-30,
  keepUpToDate=False -> closed historical bars only, no forming bar.
  FAIL-CLOSED: on connection refusal one clean reconnect pass, then
  BLOCKED (fallback typing is A1's act, not this lane's); no fill/gap
  interpolation anywhere.

Outputs (ALL under this g6_pull/ dir):
  raw/<SYM>_1d_{BID,ASK}_<YYYYMM>.json  verbatim per-session bar rows
  MANIFEST.json                         per-file sha256 + request params
  VERIFICATION.json                     coverage/gap/spread/PIT results
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from datetime import date, datetime, timezone
from pathlib import Path

from ib_insync import IB, Contract

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
RAW.mkdir(parents=True, exist_ok=True)
HOST, PORT = "127.0.0.1", 7497
CLIENT_IDS = (66, 67, 68)
PACE_HMDS_S = 10.5          # acquire_bounded.py proven fetch pace
PACE_DETAILS_S = 2.5        # ro_probe detail pace
DEADLINE = time.monotonic() + 25 * 60
INFO = set(range(2100, 2200))

WINDOW = ("2026-07-01", "2026-09-30")
PIP = {"AUDUSD": 0.0001, "USDCAD": 0.0001}
C1_ANCHOR = {  # close-side H1 C1 cells (p50/p90 pips), sanity anchors only
    "AUDUSD": (1.0, 1.3),
    "USDCAD": (1.2, 1.6),
}
CONTRACT_SPECS = {
    "AUDUSD": dict(secType="CASH", symbol="AUD", exchange="IDEALPRO", currency="USD"),
    "USDCAD": dict(secType="CASH", symbol="USD", exchange="IDEALPRO", currency="CAD"),
}
# '1 M' chunks anchored at month ends (acquire_bounded DAILY_ENDS pattern)
CHUNKS = [
    ("202607", "20260731 23:59:59 UTC"),
    ("202608", "20260831 23:59:59 UTC"),
    ("202609", "20260930 23:59:59 UTC"),
]

REDACT = re.compile(r"\b[A-Z]{1,3}\d{4,}\b")
logging.basicConfig(level=logging.ERROR)
logging.getLogger("ib_insync").addFilter(
    type("R", (logging.Filter,), {"filter": lambda self, rec: (setattr(rec, "msg", REDACT.sub("[REDACTED]", str(rec.msg))) or True)})()
)


def redact(s) -> str:
    return REDACT.sub("[REDACTED]", str(s))


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


errors: list[dict] = []


def since(mark: int) -> list[dict]:
    return [e for e in errors[mark:] if e["code"] not in INFO and e["code"] != 366]


def connect_once() -> tuple[IB | None, dict]:
    ib = IB()
    ib.RequestTimeout = 40
    ib.RaiseRequestErrors = True
    ib.errorEvent += lambda reqId, code, msg, contract: errors.append(
        {"code": int(code), "msg": redact(msg)[:300]}
    )
    for cid in CLIENT_IDS:
        try:
            ib.connect(HOST, PORT, clientId=cid, timeout=15, readonly=True)
            return ib, {"connected": True, "clientId": cid, "readonly": True}
        except Exception as exc:
            errors.append({"code": None, "msg": f"connect cid={cid}: {type(exc).__name__}: {redact(exc)[:200]}"})
    return None, {"connected": False, "errors": [e["msg"] for e in errors[-3:]]}


def session_date(bar) -> str:
    d = bar.date
    if hasattr(d, "strftime"):
        return d.strftime("%Y-%m-%d")
    text = str(d)
    if len(text) >= 8 and text[:8].isdigit() and (len(text) == 8 or text[8] in " -T"):
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    return text[:10]


def hist(ib: IB, contract, end: str, what: str) -> tuple[list[dict], list[dict]]:
    """One paced HMDS '1 M' x '1 day' BID/ASK request; bars dumped verbatim."""
    mark = len(errors)
    bars = []
    err: list[dict] = []
    try:
        raw = ib.reqHistoricalData(
            contract, endDateTime=end, durationStr="1 M", barSizeSetting="1 day",
            whatToShow=what, useRTH=False, formatDate=1, keepUpToDate=False,
            chartOptions=[], timeout=40,
        )
        bars = [{"date": str(b.date), "session_date": session_date(b),
                 "open": b.open, "high": b.high, "low": b.low, "close": b.close,
                 "volume": b.volume} for b in raw or []]
        err = since(mark)
    except Exception as exc:
        err = since(mark) or [{"code": getattr(exc, "code", None), "msg": redact(exc)[:300]}]
    time.sleep(PACE_HMDS_S)
    return bars, err[:3]


def land_rows(symbol: str, what: str, month: str, rows: list[dict], err: list[dict], end: str) -> dict:
    blob = (json.dumps(rows, separators=(",", ":")) + "\n").encode()
    name = f"{symbol}_1d_{what}_{month}.json"
    (RAW / name).write_bytes(blob)
    return {
        "file": name, "path": str(RAW / name), "n_bars": len(rows),
        "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
        "whatToShow": what, "barSizeSetting": "1 day", "durationStr": "1 M",
        "endDateTime": end, "useRTH": False, "formatDate": 1,
        "retrieved_at_utc": now_utc(), "api_errors": err,
        "first": rows[0]["session_date"] if rows else None,
        "last": rows[-1]["session_date"] if rows else None,
    }


def weekdays(lo: str, hi: str) -> list[str]:
    a, b = date.fromisoformat(lo), date.fromisoformat(hi)
    days = []
    while a <= b:
        if a.weekday() < 5:
            days.append(a.isoformat())
        a = date.fromordinal(a.toordinal() + 1)
    return days


def quantile_lower(xs: list[float], q: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * (len(xs) - 1)))] if xs else float("nan")


def main() -> None:
    status: dict = {"schema": "g6_pull_status@1", "label": "PREPARATION (feeds a not-yet-registered cycle; nothing scores)",
                    "probe": "G6-INPUT-COMPLETION-IBKR-D1-2026-10-01", "started_at_utc": now_utc(),
                    "orders_placed": 0, "market_data_subscriptions": 0, "readonly": True}
    files: list[dict] = []

    # ---- connect (one clean reconnect allowed) ----
    ib, conn = connect_once()
    if ib is None:
        time.sleep(30)
        ib, conn2 = connect_once()
        conn = {"attempt_1": conn, "attempt_2_clean_reconnect": conn2}
    if ib is None:
        status.update({"verdict": "BLOCKED",
                       "blocked_reason": "TWS API connection refused on 127.0.0.1:7497 (both passes, all clientIds)",
                       "connection": conn, "finished_at_utc": now_utc()})
        (HERE / "VERIFICATION.json").write_text(json.dumps(status, indent=1) + "\n")
        print("BLOCKED: connection refused")
        return

    accounts = list(ib.managedAccounts())  # handshake payload; ids never written
    srv_time = ib.reqCurrentTime()
    status["connection"] = {**conn, "server_time_utc": str(srv_time), "local_utc": now_utc(),
                            "managed_accounts_count": len(accounts),
                            "paper_du_prefix_only": bool(accounts) and all(a.startswith("DU") for a in accounts),
                            "account_ids": "REDACTED-NOT-RECORDED"}
    print(f"connected clientId={conn.get('clientId')} readonly=True server={srv_time}")

    # ---- identity resolution (no AUD/CA identity is on file) ----
    identities: dict[str, dict] = {}
    for symbol, spec in CONTRACT_SPECS.items():
        c = Contract()
        for k, v in spec.items():
            setattr(c, k, v)
        mark = len(errors)
        try:
            details = ib.reqContractDetails(c)
        except Exception as exc:
            identities[symbol] = {"status": "RESOLVE_FAIL", "error": redact(exc)[:300]}
            details = []
        time.sleep(PACE_DETAILS_S)
        if not details:
            identities[symbol].setdefault("status", "RESOLVE_EMPTY")
            continue
        cd, cc = details[0], details[0].contract
        identities[symbol] = {
            "status": "RESOLVED", "conId": cc.conId, "symbol": cc.symbol,
            "localSymbol": cc.localSymbol, "secType": cc.secType,
            "exchange": cc.exchange, "currency": cc.currency,
            "minTick": cd.minTick, "timeZoneId": cd.timeZoneId,
            "longName": cd.longName, "validExchanges": cd.validExchanges,
            "detail_noise_errors": since(mark)[:2],
            "qualified_contract": {"conId": cc.conId, "exchange": cc.exchange},
        }
        print(f"identity {symbol}: conId={cc.conId} localSymbol={cc.localSymbol} minTick={cd.minTick} tz={cd.timeZoneId}")

    # ---- bounded pulls: 2 symbols x {BID,ASK} x 3 month chunks ----
    chunk_status: dict[str, dict] = {}
    queue = [(sym, what, mo, end)
             for sym in CONTRACT_SPECS
             if identities.get(sym, {}).get("status") == "RESOLVED"
             for what in ("BID", "ASK") for mo, end in CHUNKS]
    for sym, what, mo, end in queue:
        if time.monotonic() > DEADLINE:
            chunk_status[f"{sym}_{what}_{mo}"] = {"status": "NOT_RUN_TIME_CAP"}
            continue
        c = Contract()
        c.conId = identities[sym]["conId"]
        c.exchange = identities[sym]["exchange"]
        rows, err = hist(ib, c, end, what)
        meta = land_rows(sym, what, mo, rows, err, end)
        meta["status"] = "OK" if rows else "EMPTY"
        files.append(meta)
        chunk_status[f"{sym}_{what}_{mo}"] = {"status": meta["status"], "n": meta["n_bars"], "errors": err}
        print(f"chunk {sym} {what} {mo}: n={meta['n_bars']} err={err[:1]}")
        if any("pacing" in (e.get("msg") or "").lower() for e in err):
            print("  pacing hit -> cooling 120s")
            time.sleep(120)

    # ---- one bounded retry pass for failed/empty chunks ----
    retry_targets = [k for k, v in chunk_status.items() if v.get("status") in ("EMPTY", "ERROR")]
    if retry_targets and time.monotonic() < DEADLINE:
        print(f"retry pass (one) for: {retry_targets}")
        time.sleep(60)
        if not ib.isConnected():
            ib, rc = connect_once()
            status["connection"]["retry_reconnect"] = rc.get("connected", False)
        if ib is not None and ib.isConnected():
            for key in retry_targets:
                if time.monotonic() > DEADLINE:
                    break
                sym, what, mo = key.split("_")
                end = dict(CHUNKS)[mo]
                c = Contract()
                c.conId = identities[sym]["conId"]
                c.exchange = identities[sym]["exchange"]
                rows, err = hist(ib, c, end, what)
                meta = land_rows(sym, what, mo, rows, err, end)
                meta["status"] = "OK_RETRY" if rows else "EMPTY_RETRY"
                meta["replaces"] = key
                files = [f for f in files if f["file"] != meta["file"]] + [meta]
                chunk_status[key] = {"status": meta["status"], "n": meta["n_bars"], "errors": err}
                print(f"retry {key}: n={meta['n_bars']}")

    if ib.isConnected():
        ib.disconnect()
    status["disconnected"] = True

    manifest = {
        "schema": "g6_pull_manifest@1",
        "label": "PREPARATION (feeds a not-yet-registered cycle; nothing scores)",
        "probe": "G6-INPUT-COMPLETION-IBKR-D1-2026-10-01",
        "generated_at_utc": now_utc(),
        "authorization": "G6 lane dispatch 2026-10-01 (co-owner authorized); read-only TWS API 127.0.0.1:7497",
        "method": "ib_insync reqHistoricalData, '1 M' x '1 day' BID/ASK chunks anchored at month ends (acquire_bounded.py discipline, pace 10.5s); identity via reqContractDetails",
        "window_requested": {"start": WINDOW[0], "end": WINDOW[1], "end_inclusive_bound": "20260930 23:59:59 UTC"},
        "raw_dir": str(RAW),
        "orders_placed": 0, "market_data_subscriptions": 0,
        "pit_property": {"keepUpToDate": False, "all_requests_end_bounded_at_or_before": "20260930 23:59:59 UTC",
                         "retrieved_on": now_utc()[:10], "note": "closed historical bars only; no forming bar; server_time in status"},
        "identities": identities,
        "files": files,
    }
    (HERE / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n")
    status["manifest_path"] = str(HERE / "MANIFEST.json")
    status["chunk_status"] = chunk_status
    status["finished_at_utc"] = now_utc()
    status["verdict_raw_pull"] = "OK" if all(v.get("status", "").startswith("OK") for v in chunk_status.values()) and chunk_status else "PARTIAL_OR_FAILED"
    (HERE / "VERIFICATION.json").write_text(json.dumps(status, indent=1) + "\n")
    print("PULL_DONE verdict_raw_pull=" + status["verdict_raw_pull"])


if __name__ == "__main__":
    main()
