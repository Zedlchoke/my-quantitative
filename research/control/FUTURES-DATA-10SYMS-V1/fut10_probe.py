"""FUTURES-DATA-10SYMS-V1 — read-only IBKR TWS paper probe + bounded collector.

10 symbols: NQ ES CL NG GC SI 6E 6J 6B 6A. Port 127.0.0.1:7497 only,
readonly=True, unique client ids. No orders, no account endpoints, no
subscriptions. Account-like strings redacted from logs. Byte cap enforced.
Missing evidence = NOT_RUN, never inferred PASS.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from ib_insync import Contract, IB, util

CTL = Path(__file__).resolve().parent
RAW_ROOT = Path.home() / ".my-quantitative-data" / "futures-10syms-v1" / "raw"
MANIFEST = CTL / "raw_manifest.jsonl"
BYTE_CAP = 2_000_000_000  # 2.0 GiB published ceiling for new raw bytes
PACING_S = 3.0            # >=3s between historical requests (~20/10min, far under 60/10min)

HOST, PORT = "127.0.0.1", 7497

# symbol -> (exchange, active month codes, currency, tradingClass)
SYMBOLS = {
    "NQ": ("CME", "HMUZ", "USD", "NQ"),
    "ES": ("CME", "HMUZ", "USD", "ES"),
    "CL": ("NYMEX", "FGHJKMNQUVXZ", "USD", "CL"),
    "NG": ("NYMEX", "FGHJKMNQUVXZ", "USD", "NG"),
    "GC": ("COMEX", "GJMQVZ", "USD", "GC"),
    "SI": ("COMEX", "HKN UZ".replace(" ", ""), "USD", "SI"),  # SI 5000oz, NOT SIL 1000oz
    "6E": ("CME", "HMUZ", "USD", "6E"),
    "6J": ("CME", "HMUZ", "USD", "6J"),
    "6B": ("CME", "HMUZ", "USD", "6B"),
    "6A": ("CME", "HMUZ", "USD", "6A"),
}
MONTH_CODE = "FGHJKMNQUVXZ"
MONTH_NUM = {c: i + 1 for i, c in enumerate(MONTH_CODE)}

REDACT = re.compile(r"\b[A-Z]{1,3}\d{4,}\b")
logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(message)s")


def redact(text: str) -> str:
    return REDACT.sub("[REDACTED]", text)


class _Redact(logging.Filter):
    def filter(self, record):
        record.msg = redact(str(record.msg))
        if record.args:
            record.args = tuple(redact(str(a)) for a in record.args)
        return True


logging.getLogger("ib_insync").addFilter(_Redact())
util.patchAsyncio()


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect(client_id: int) -> IB:
    ib = IB()
    ib.connect(HOST, PORT, clientId=client_id, readonly=True, timeout=15)
    return ib


class ErrCollector:
    """Collect error events (code, msg) so failures are recorded, not swallowed."""

    def __init__(self, ib: IB):
        self.events = []
        ib.errorEvent.connect(self._on_error)

    def _on_error(self, req_id, code, msg, contract):
        if code < 2100 or code > 2200:  # info-ish codes excluded
            self.events.append(
                {"code": int(code), "msg": redact(str(msg)),
                 "contract": str(getattr(contract, "localSymbol", "") or "")}
            )

    def drain(self):
        ev, self.events = self.events, []
        return ev


def fut_contract(symbol: str, exchange: str, month: str = "", expired: bool = False,
                 trading_class: str = "") -> Contract:
    c = Contract()
    c.symbol = symbol
    c.secType = "FUT"
    c.exchange = exchange
    if trading_class:
        c.tradingClass = trading_class
    if month:
        c.lastTradeDateOrContractMonth = month
    if expired:
        c.includeExpired = True
    return c


def details_row(cd) -> dict:
    ct = cd.contract
    g = lambda obj, k, d="": getattr(obj, k, d)  # noqa: E731
    return {
        "conId": ct.conId,
        "symbol": ct.symbol,
        "secType": ct.secType,
        "exchange": ct.exchange if ct.exchange != "" else g(cd, "validExchanges", ",").split(",")[0],
        "localSymbol": ct.localSymbol,
        "localName": g(ct, "localName"),
        "tradingClass": ct.tradingClass,
        "lastTradeDateOrContractMonth": ct.lastTradeDateOrContractMonth,
        "expiry_date": g(cd, "contractMonth"),
        "multiplier": ct.multiplier,
        "minTick": g(cd, "minTick"),
        "currency": ct.currency,
        "timeZoneId": g(cd, "timeZoneId"),
        "tradingHours": g(cd, "tradingHours"),
        "liquidHours": g(cd, "liquidHours"),
        "lastTradeTime": g(cd, "lastTradeTime"),
        "realExpirationDate": g(cd, "realExpirationDate"),
        "underConId": g(cd, "underConId"),
        "longName": redact(g(cd, "longName")),
        "category": g(cd, "category"),
        "industry": g(cd, "industry"),
        "ev_rule": g(cd, "evRule"),
        "validExchanges": g(cd, "validExchanges"),
        "marketName": g(cd, "marketName"),
    }


def months_back(cycle: str, years: int) -> list[str]:
    """List YYYYMM strings from most-recent past month backwards within cycle."""
    now = datetime.now(timezone.utc)
    out = []
    y, m = now.year, now.month
    total = years * 12
    for _ in range(total):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        code = MONTH_CODE[m - 1]
        if code in cycle:
            out.append(f"{y}{m:02d}")
    return out


def stage_identity(client_id: int, walk_years: int = 6) -> None:
    ib = connect(client_id)
    errs = ErrCollector(ib)
    out = {"fetched_utc": now_utc(), "endpoint": f"TWSAPI {HOST}:{PORT} readonly client {client_id}",
           "symbols": {}}
    try:
        for sym, (exch, cycle, _cur, tc) in SYMBOLS.items():
            entry = {"exchange": exch, "tradingClass": tc, "active_chain": [],
                     "expired_walk": [], "deepest_resolved": None,
                     "consecutive_misses_at_stop": None}
            # active chain (non-expired): no month filter -> all listings
            errs.drain()
            cds = ib.reqContractDetails(fut_contract(sym, exch, trading_class=tc))
            entry["active_chain_errors"] = errs.drain()
            rows = sorted((details_row(cd) for cd in cds),
                          key=lambda r: r["lastTradeDateOrContractMonth"])
            entry["active_chain"] = rows
            if rows:
                entry["front"] = rows[0]
                entry["next"] = rows[1] if len(rows) > 1 else None
            # expired walk-back
            miss = 0
            for ym in months_back(cycle, walk_years):
                if miss >= 6:
                    break
                errs.drain()
                try:
                    cds = ib.reqContractDetails(
                        fut_contract(sym, exch, ym, expired=True, trading_class=tc))
                except Exception as e:  # noqa: BLE001
                    cds = []
                    entry["expired_walk"].append({"month": ym, "error": redact(str(e))})
                ev = errs.drain()
                if cds:
                    miss = 0
                    row = details_row(cds[0])
                    row["walk_errors"] = ev
                    entry["expired_walk"].append(row)
                    entry["deepest_resolved"] = ym
                else:
                    miss += 1
                    entry["expired_walk"].append({"month": ym, "miss": True, "errors": ev})
                time.sleep(0.4)
            entry["consecutive_misses_at_stop"] = miss
            out["symbols"][sym] = entry
            print(f"[identity] {sym}: active={len(entry['active_chain'])} "
                  f"deepest_expired={entry['deepest_resolved']}", flush=True)
    finally:
        ib.disconnect()
    (CTL / "S1_IDENTITY.json").write_text(json.dumps(out, indent=1))


def stage_quotes(client_id: int) -> None:
    ib = connect(client_id)
    errs = ErrCollector(ib)
    ident = json.loads((CTL / "S1_IDENTITY.json").read_text())
    out = {"fetched_utc": now_utc(), "endpoint": f"TWSAPI {HOST}:{PORT} readonly client {client_id}",
           "symbols": {}}
    try:
        for sym, entry in ident["symbols"].items():
            front = entry.get("front")
            if not front:
                out["symbols"][sym] = {"error": "NO_FRONT_RESOLVED"}
                continue
            c = Contract()
            c.conId = front["conId"]
            c.exchange = front["exchange"]
            qrow = {"front_localSymbol": front["localSymbol"], "conId": front["conId"]}
            for label, mdt in (("live_type1", 1), ("delayed_type3", 3)):
                ib.reqMarketDataType(mdt)
                errs.drain()
                try:
                    ticker = ib.reqMktData(c, "", False, False)
                    ib.sleep(8.0)  # bounded wait, never indefinite
                    ib.cancelMktData(c)
                    qrow[label] = {
                        "marketDataType": getattr(ticker, "marketDataType", None),
                        "bid": ticker.bid if ticker.bid == ticker.bid else None,  # NaN->None
                        "ask": ticker.ask if ticker.ask == ticker.ask else None,
                        "last": ticker.last if ticker.last == ticker.last else None,
                        "close": ticker.close if ticker.close == ticker.close else None,
                        "volume": ticker.volume if ticker.volume == ticker.volume else None,
                        "bidSize": ticker.bidSize if ticker.bidSize == ticker.bidSize else None,
                        "askSize": ticker.askSize if ticker.askSize == ticker.askSize else None,
                        "errors": errs.drain(),
                    }
                except Exception as e:  # noqa: BLE001
                    qrow[label] = {"exception": redact(str(e)), "errors": errs.drain()}
                time.sleep(1.0)
            out["symbols"][sym] = qrow
            print(f"[quotes] {sym}: live={qrow.get('live_type1', {}).get('bid')}/"
                  f"{qrow.get('live_type1', {}).get('ask')} delayed="
                  f"{qrow.get('delayed_type3', {}).get('bid')}/"
                  f"{qrow.get('delayed_type3', {}).get('ask')}", flush=True)
    finally:
        ib.reqMarketDataType(1)
        ib.disconnect()
    (CTL / "S2_QUOTES.json").write_text(json.dumps(out, indent=1))


def bars_to_rows(bars) -> list[dict]:
    rows = []
    for b in bars:
        dt = b.date
        rows.append({
            "t": dt.isoformat() if hasattr(dt, "isoformat") else str(dt),
            "o": float(b.open), "h": float(b.high), "l": float(b.low),
            "c": float(b.close), "v": int(b.volume),
            "wap": float(b.average) if getattr(b, "average", None) else None,
            "n": int(b.barCount) if b.barCount is not None else None,
        })
    return rows


def hist_request(ib, errs, contract, what_use, bar_size, duration, end="", fmt=1):
    errs.drain()
    try:
        bars = ib.reqHistoricalData(
            contract, endDateTime=end or "", durationStr=duration,
            barSizeSetting=bar_size, whatToShow=what_use, useRTH=True,
            formatDate=fmt, keepUpToDate=False)
        return {"ok": True, "rows": bars_to_rows(bars), "errors": errs.drain()}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "exception": redact(str(e)), "errors": errs.drain()}


def by_conid(con_id: int, exchange: str) -> Contract:
    c = Contract()
    c.conId = con_id
    c.exchange = exchange
    return c


PROBES = [
    ("TRADES", "1 day", "3 D", ""),
    ("TRADES", "1 hour", "3 D", ""),
    ("TRADES", "1 min", "1800 S", ""),
    ("BID", "1 day", "3 D", ""),
    ("ASK", "1 day", "3 D", ""),
    ("TRADES", "1 min", "7 D", ""),   # duration-limit probe
    ("TRADES", "1 hour", "30 D", ""),  # duration-limit probe
]


def stage_histprobe(client_id: int) -> None:
    ib = connect(client_id)
    errs = ErrCollector(ib)
    ident = json.loads((CTL / "S1_IDENTITY.json").read_text())
    out = {"fetched_utc": now_utc(), "endpoint": f"TWSAPI {HOST}:{PORT} readonly client {client_id}",
           "symbols": {}}
    try:
        for sym, entry in ident["symbols"].items():
            front = entry.get("front")
            if not front:
                out["symbols"][sym] = {"error": "NO_FRONT"}
                continue
            c = by_conid(front["conId"], front["exchange"])
            row = {"front_localSymbol": front["localSymbol"], "probes": {}}
            try:
                head = ib.reqHeadTimeStamp(c, "TRADES", True, 1)
                row["head_trades"] = head.isoformat() if head else None
            except Exception as e:  # noqa: BLE001
                row["head_trades"] = None
                row["head_error"] = redact(str(e))
            for wu, bs, dur, end in PROBES:
                key = f"{wu}|{bs}|{dur}"
                r = hist_request(ib, errs, c, wu, bs, dur, end)
                row["probes"][key] = {"ok": r["ok"], "n": len(r.get("rows", [])),
                                      "errors": r.get("errors", []),
                                      "exception": r.get("exception")}
                time.sleep(PACING_S)
            out["symbols"][sym] = row
            print(f"[histprobe] {sym}: head={row.get('head_trades')} "
                  f"probes_ok={sum(1 for p in row['probes'].values() if p['ok'])}/{len(PROBES)}",
                  flush=True)
    finally:
        ib.disconnect()
    (CTL / "S3_HISTPROBE.json").write_text(json.dumps(out, indent=1))


def stage_sample(client_id: int) -> None:
    """Bounded samples: front, next, nearest expired, an old expired (~2y back)."""
    ib = connect(client_id)
    errs = ErrCollector(ib)
    ident = json.loads((CTL / "S1_IDENTITY.json").read_text())
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    out = {"fetched_utc": now_utc(), "endpoint": f"TWSAPI {HOST}:{PORT} readonly client {client_id}",
           "files": []}

    def fetch(sym, cd, role, wu, bs, dur, end=""):
        c = by_conid(cd["conId"], cd["exchange"])
        c.includeExpired = True
        r = hist_request(ib, errs, c, wu, bs, dur, end)
        name = (f"{sym}_{cd['localSymbol'].replace(' ', '')}_{cd['conId']}_{role}_"
                f"{wu}_{bs.replace(' ', '')}_{dur.replace(' ', '')}.json")
        path = RAW_ROOT / name
        payload = {
            "fetched_utc": now_utc(), "symbol": sym, "conId": cd["conId"],
            "localSymbol": cd["localSymbol"], "role": role,
            "expiry_month": cd["lastTradeDateOrContractMonth"],
            "exchange": cd["exchange"], "whatUse": wu, "barSize": bs,
            "durationStr": dur, "endDateTime": end or "", "useRTH": True,
            "endpoint": f"TWSAPI {HOST}:{PORT} readonly client {client_id}",
            "timeZoneId": cd.get("timeZoneId"), "contract_tz_note":
                "IB intraday bar 't' values carry the exchange tz offset per ISO8601; "
                "daily rows are dates in exchange tz; storage keeps original strings",
            "ok": r["ok"], "errors": r.get("errors", []),
            "exception": r.get("exception"),
            "n_rows": len(r.get("rows", [])), "bars": r.get("rows", []),
        }
        data = json.dumps(payload, separators=(",", ":")).encode()
        path.write_bytes(data)
        sha = hashlib.sha256(data).hexdigest()
        rec = {"path": str(path), "bytes": len(data), "sha256": sha,
               "symbol": sym, "conId": cd["conId"], "localSymbol": cd["localSymbol"],
               "role": role, "whatUse": wu, "barSize": bs, "durationStr": dur,
               "n_rows": payload["n_rows"], "fetched_utc": payload["fetched_utc"]}
        with open(MANIFEST, "a") as f:
            f.write(json.dumps(rec) + "\n")
        out["files"].append(rec)
        time.sleep(PACING_S)
        return payload

    SAMPLES = [
        ("TRADES", "1 day", "3 D"),
        ("TRADES", "1 hour", "3 D"),
        ("TRADES", "1 min", "1800 S"),
        ("BID", "1 day", "3 D"),
        ("ASK", "1 day", "3 D"),
    ]
    try:
        for sym, entry in ident["symbols"].items():
            front = entry.get("front")
            if not front:
                continue
            expired_rows = [r for r in entry.get("expired_walk", [])
                            if isinstance(r, dict) and "conId" in r]
            targets = [("front", front)]
            if entry.get("next"):
                targets.append(("next", entry["next"]))
            if expired_rows:
                targets.append(("nearest_expired", expired_rows[0]))
                old_pool = [r for r in expired_rows
                            if r["lastTradeDateOrContractMonth"] <= "202406"]
                if old_pool:
                    targets.append(("old_expired", old_pool[len(old_pool) // 2]))
            for role, cd in targets:
                for wu, bs, dur in SAMPLES:
                    p = fetch(sym, cd, role, wu, bs, dur)
                    print(f"[sample] {sym} {cd['localSymbol']} {role} {wu}/{bs}: "
                          f"ok={p['ok']} n={p['n_rows']}", flush=True)
    finally:
        ib.disconnect()
    (CTL / "S4_SAMPLES.json").write_text(json.dumps(out, indent=1))


def bytes_used() -> int:
    if not MANIFEST.exists():
        return 0
    tot = 0
    for line in MANIFEST.read_text().splitlines():
        try:
            tot += json.loads(line)["bytes"]
        except Exception:  # noqa: BLE001
            pass
    return tot


def stage_bulk(client_id: int, hours_window: str = "30 D", m1_window: str = "2 D") -> None:
    """Checkpointed batch: per resolvable contract — full-life daily TRADES,
    bounded hourly, bounded 1-min; daily BID/ASK where entitled.

    Expired contracts REQUIRE endDateTime inside their trading life (measured
    in S4: no end -> 0 bars). Active chain filtered to <=15 months out (near
    strip that carries roll+liquidity; far-out serials are pre-listing thin).
    """
    ib = connect(client_id)
    errs = ErrCollector(ib)
    ident = json.loads((CTL / "S1_IDENTITY.json").read_text())
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    done = set()
    if MANIFEST.exists():
        for line in MANIFEST.read_text().splitlines():
            try:
                r = json.loads(line)
                done.add((r["symbol"], r["conId"], r["whatUse"], r["barSize"],
                          r["durationStr"], r.get("endDateTime", "")))
            except Exception:  # noqa: BLE001
                pass
    now = datetime.now(timezone.utc)
    hy, hm = now.year, now.month + 15
    while hm > 12:
        hm -= 12
        hy += 1
    horizon = hy * 100 + hm
    now6 = int(now.strftime("%Y%m"))
    log = {"started_utc": now_utc(), "requests": [], "byte_cap": BYTE_CAP,
           "skipped_done": 0, "aborted": None, "active_horizon_month": horizon}
    try:
        for sym, entry in ident["symbols"].items():
            contracts = {}
            for cd in entry.get("active_chain", []):
                if int(cd["lastTradeDateOrContractMonth"][:6]) <= horizon:
                    contracts[cd["conId"]] = cd
            for r in entry.get("expired_walk", []):
                if isinstance(r, dict) and "conId" in r:
                    contracts[r["conId"]] = r
            ordered = sorted(contracts.values(),
                             key=lambda r: r["lastTradeDateOrContractMonth"])
            for cd in ordered:
                ym = cd["lastTradeDateOrContractMonth"][:6]
                expired = int(ym) < now6
                end = f"{ym[:4]}{ym[4:]}01 00:00:00" if expired else ""
                jobs = [
                    ("TRADES", "1 day", "6 Y", end),
                    ("TRADES", "1 hour", hours_window, end),
                    ("TRADES", "1 min", m1_window, end),
                    ("BID", "1 day", "1 Y", end),
                    ("ASK", "1 day", "1 Y", end),
                ]
                for wu, bs, dur, end_dt in jobs:
                    key = (sym, cd["conId"], wu, bs, dur, end_dt)
                    if key in done:
                        log["skipped_done"] += 1
                        continue
                    used = bytes_used()
                    if used > BYTE_CAP:
                        log["aborted"] = {"reason": "BYTE_CAP", "used": used}
                        (CTL / "S5_BULK_LOG.json").write_text(json.dumps(log, indent=1))
                        ib.disconnect()
                        return
                    c = by_conid(cd["conId"], cd["exchange"])
                    c.includeExpired = True
                    r = hist_request(ib, errs, c, wu, bs, dur, end_dt)
                    name = (f"{sym}_{cd['localSymbol'].replace(' ', '')}_{cd['conId']}_"
                            f"{wu}_{bs.replace(' ', '')}_{dur.replace(' ', '')}.json")
                    path = RAW_ROOT / name
                    payload = {
                        "fetched_utc": now_utc(), "symbol": sym, "conId": cd["conId"],
                        "localSymbol": cd["localSymbol"],
                        "expiry_month": cd["lastTradeDateOrContractMonth"],
                        "exchange": cd["exchange"], "whatUse": wu, "barSize": bs,
                        "durationStr": dur, "endDateTime": end_dt, "useRTH": True,
                        "endpoint": f"TWSAPI {HOST}:{PORT} readonly client {client_id}",
                        "timeZoneId": cd.get("timeZoneId"),
                        "ok": r["ok"], "errors": r.get("errors", []),
                        "exception": r.get("exception"),
                        "n_rows": len(r.get("rows", [])), "bars": r.get("rows", []),
                    }
                    data = json.dumps(payload, separators=(",", ":")).encode()
                    path.write_bytes(data)
                    sha = hashlib.sha256(data).hexdigest()
                    rec = {"path": str(path), "bytes": len(data), "sha256": sha,
                           "symbol": sym, "conId": cd["conId"],
                           "localSymbol": cd["localSymbol"],
                           "whatUse": wu, "barSize": bs, "durationStr": dur,
                           "endDateTime": end_dt,
                           "n_rows": payload["n_rows"], "fetched_utc": payload["fetched_utc"],
                           "ok": r["ok"]}
                    with open(MANIFEST, "a") as f:
                        f.write(json.dumps(rec) + "\n")
                    log["requests"].append(rec)
                    print(f"[bulk] {sym} {cd['localSymbol']} {wu}/{bs}: ok={r['ok']} "
                          f"n={payload['n_rows']} used={used + len(data)}", flush=True)
                    time.sleep(PACING_S)
    finally:
        log["finished_utc"] = now_utc()
        (CTL / "S5_BULK_LOG.json").write_text(json.dumps(log, indent=1))
        try:
            ib.disconnect()
        except Exception:  # noqa: BLE001
            pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["identity", "quotes", "histprobe", "sample",
                                      "bulk"])
    ap.add_argument("--client-id", type=int, default=9210)
    ap.add_argument("--walk-years", type=int, default=6)
    ap.add_argument("--hours-window", default="30 D")
    ap.add_argument("--m1-window", default="2 D")
    a = ap.parse_args()
    if a.stage == "identity":
        stage_identity(a.client_id, a.walk_years)
    elif a.stage == "quotes":
        stage_quotes(a.client_id)
    elif a.stage == "histprobe":
        stage_histprobe(a.client_id)
    elif a.stage == "sample":
        stage_sample(a.client_id)
    elif a.stage == "bulk":
        stage_bulk(a.client_id, a.hours_window, a.m1_window)


if __name__ == "__main__":
    sys.exit(main())
