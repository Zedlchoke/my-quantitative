"""Bounded IBKR read-only acquisition. No orders. No eligibility edits.

Pacing: 10.5s between HMDS calls. Raw bars go outside the git checkout.
Stops at a 38-minute deadline and writes a checkpoint.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ib_insync import Contract, IB

CONTROL = Path(__file__).resolve().parent
RAW = Path.home() / ".my-quantitative-data" / "portfolio-composite-12assets-100k-v1" / "ibkr_acq_20260930"
RAW.mkdir(parents=True, exist_ok=True)
HOST, PORT, CLIENT_ID = "127.0.0.1", 7497, 9049
PACE_S = 10.5
DEADLINE = time.monotonic() + 38 * 60
REDACT = re.compile(r"\b[A-Z]{1,3}\d{4,}\b")
INFO = set(range(2100, 2200))

logging.basicConfig(level=logging.ERROR)
logging.getLogger("ib_insync").addFilter(
    type("R", (logging.Filter,), {"filter": lambda self, rec: (setattr(rec, "msg", REDACT.sub("[REDACTED]", str(rec.msg))) or True)})()
)

SPOTS = [
    {"asset": "NZDUSD", "conId": 39453441, "symbol": "NZD", "secType": "CASH", "exchange": "IDEALPRO", "currency": "USD"},
    {"asset": "USDCHF", "conId": 12087820, "symbol": "USD", "secType": "CASH", "exchange": "IDEALPRO", "currency": "CHF"},
    {"asset": "XAUUSD", "conId": 69067924, "symbol": "XAUUSD", "secType": "CMDTY", "exchange": "SMART", "currency": "USD"},
    {"asset": "XAGUSD", "conId": 77124483, "symbol": "XAGUSD", "secType": "CMDTY", "exchange": "SMART", "currency": "USD"},
]
DAILY_ENDS = [
    "20260930 23:59:59 UTC", "20250930 23:59:59 UTC", "20240930 23:59:59 UTC",
    "20230930 23:59:59 UTC", "20220930 23:59:59 UTC", "20210930 23:59:59 UTC",
]
M1_ENDS = ["20210115 23:59:59 UTC", "20230615 23:59:59 UTC", "20260928 23:59:59 UTC"]
HOUR_ENDS = [f"{y}0331 23:59:59 UTC" for y in range(2021, 2027)]
ARCHIVE = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng6/integration/research/control/forex_ng6_run/p0/staging/XAUUSD_1day_full.json")
ARCHIVE_SHA = "49c2684ebb045302acf0c452b5aa9a3b96dff73eb3bc6f5add1801d6817fb33d"


def redact(s: str) -> str:
    return REDACT.sub("[REDACTED]", s)


def contract_from(spec: dict) -> Contract:
    c = Contract()
    c.conId = spec["conId"]
    c.exchange = spec["exchange"]
    return c


def bar_date(bar) -> str:
    d = bar.date
    if hasattr(d, "strftime"):
        return d.strftime("%Y-%m-%d")
    text = str(d)
    if len(text) >= 8 and text[:8].isdigit() and (len(text) == 8 or text[8] in " -T"):
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    return text[:10]


def dump_bars(bars) -> list[dict]:
    out = []
    for b in bars or []:
        out.append({
            "date": str(b.date),
            "session_date": bar_date(b),
            "open": b.open, "high": b.high, "low": b.low, "close": b.close,
            "volume": b.volume,
        })
    return out


def sha_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def main() -> None:
    errors: list[dict] = []
    ib = IB()
    ib.RequestTimeout = 40
    ib.RaiseRequestErrors = True
    ib.errorEvent += lambda reqId, code, msg, contract: errors.append(
        {"code": int(code), "msg": redact(str(msg))[:300]}
    )
    report: dict = {
        "probe": "IBKR-BOUNDED-ACQ-2026-09-30",
        "erratum": "ERRATUM_LABELS_2026-09-30.md",
        "readonly": True,
        "orders_placed": 0,
        "eligibility_modified": False,
        "registry_modified": False,
        "go_consumed": False,
        "s1_opened": False,
        "heavy_lock_acquired": False,
        "raw_dir": str(RAW),
        "pace_seconds": PACE_S,
        "assets": [],
    }
    try:
        ib.connect(HOST, PORT, clientId=CLIENT_ID, timeout=20, readonly=True)
    except Exception as exc:
        report["handshake"] = {"status": "FAIL", "error": redact(str(exc))[:300]}
        _finish(report)
        return
    accounts = list(ib.managedAccounts())
    paper = bool(accounts) and all(a.startswith("DU") for a in accounts)
    report["handshake"] = {
        "status": "PASS" if paper else "FAIL",
        "server_time": str(ib.reqCurrentTime()),
        "paper_du_prefix": paper,
        "managed_accounts_count": len(accounts),
    }
    if not paper:
        ib.disconnect()
        _finish(report)
        return
    try:
        for spec in SPOTS:
            print("ASSET", spec["asset"], flush=True)
            report["assets"].append(acquire_spot(ib, spec, errors))
            _finish(report)
        print("ASSET BRENT", flush=True)
        report["assets"].append(acquire_future(
            ib, errors, asset="BRENT", symbol="COIL", exchange="IPE",
            front_conid=361002948, note="pre-declared ICE Brent outright; BZ not requested",
        ))
        _finish(report)
        print("ASSET WTI", flush=True)
        report["assets"].append(acquire_future(
            ib, errors, asset="WTI", symbol="CL", exchange="NYMEX", front_conid=304037511,
            note="354 classified, then delayed and HMDS",
        ))
        _finish(report)
        print("ASSET NATGAS", flush=True)
        report["assets"].append(acquire_future(
            ib, errors, asset="NATGAS", symbol="NG", exchange="NYMEX", front_conid=269460170,
            note="354 classified, then delayed and HMDS; weather not fetched",
        ))
    finally:
        if ib.isConnected():
            ib.disconnect()
        report["disconnected"] = True
        _finish(report)
    print("ACQ_DONE", flush=True)


def timed_out() -> bool:
    return time.monotonic() > DEADLINE


def since(errors, mark):
    return [e for e in errors[mark:] if e["code"] not in INFO and e["code"] != 366]


def hist(ib, errors, contract, end, duration, bar_size, what):
    if timed_out():
        return [], [{"code": None, "msg": "NOT_RUN_TIME_CAP"}]
    mark = len(errors)
    try:
        bars = ib.reqHistoricalData(
            contract, end, duration, bar_size, what, False, 1, False, [], 35
        )
        err = since(errors, mark)
    except Exception as exc:
        bars = []
        err = since(errors, mark) or [{"code": getattr(exc, "code", None), "msg": redact(str(exc))[:300]}]
    time.sleep(PACE_S)
    return dump_bars(bars), err[:2]


def write_chunk(asset, tag, rows) -> dict:
    blob = (json.dumps(rows, separators=(",", ":")) + "\n").encode()
    path = RAW / f"{asset}_{tag}.json"
    path.write_bytes(blob)
    return {"path": str(path), "n": len(rows), "sha256": sha_bytes(blob), "bytes": len(blob)}


def acquire_spot(ib, spec, errors) -> dict:
    row = {"asset": spec["asset"], "identity": None, "chunks": [], "gates": {}}
    if timed_out():
        row["gates"] = {"all": "NOT_RUN_TIME_CAP"}
        return row
    c = contract_from(spec)
    mark = len(errors)
    try:
        details = ib.reqContractDetails(c)
    except Exception as exc:
        row["identity_error"] = redact(str(exc))[:300]
        row["gates"]["contract_venue"] = "FAIL"
        return row
    if not details or details[0].contract.conId != spec["conId"]:
        row["gates"]["contract_venue"] = "FAIL"
        row["identity_error"] = "conId mismatch or empty details"
        return row
    cd = details[0]
    cc = cd.contract
    row["identity"] = {
        "conId": cc.conId, "symbol": cc.symbol, "localSymbol": cc.localSymbol,
        "secType": cc.secType, "exchange": cc.exchange, "currency": cc.currency,
        "minTick": cd.minTick, "timeZoneId": cd.timeZoneId, "longName": cd.longName,
    }
    row["identity_error_noise"] = since(errors, mark)[:2]
    row["gates"]["contract_venue"] = "PASS"
    daily = {"BID": [], "ASK": []}
    for what in ("BID", "ASK"):
        for end in DAILY_ENDS:
            tag = f"1d_{what}_{end[:8]}"
            bars, err = hist(ib, errors, cc, end, "1 Y", "1 day", what)
            meta = write_chunk(spec["asset"], tag, bars)
            meta.update({"what": what, "bar": "1 day", "end": end, "error": err})
            if bars:
                meta["first"] = bars[0]["session_date"]
                meta["last"] = bars[-1]["session_date"]
            row["chunks"].append(meta)
            daily[what].extend(bars)
            if any("pacing" in (e.get("msg") or "").lower() for e in err):
                row["gates"]["pacing"] = "HIT"
                time.sleep(120)
    row["daily_coverage"] = {
        "BID": coverage(daily["BID"]),
        "ASK": coverage(daily["ASK"]),
    }
    both_pass = row["daily_coverage"]["BID"]["span_gate"] == "PASS" and row["daily_coverage"]["ASK"]["span_gate"] == "PASS"
    row["gates"]["daily_bid_ask_2021_now"] = "PASS" if both_pass else "FAIL"
    row["spread_daily"] = spread_summary(daily["BID"], daily["ASK"])
    samples = []
    for what in ("BID", "ASK"):
        for end in M1_ENDS + HOUR_ENDS:
            if timed_out():
                samples.append({"end": end, "what": what, "status": "NOT_RUN_TIME_CAP"})
                continue
            bar_size = "1 min" if end in M1_ENDS else "1 hour"
            duration = "1 D" if bar_size == "1 min" else "1 M"
            tag = f"{'m1' if bar_size == '1 min' else 'h1'}_{what}_{end[:8]}"
            bars, err = hist(ib, errors, cc, end, duration, bar_size, what)
            meta = write_chunk(spec["asset"], tag, bars)
            meta.update({"what": what, "bar": bar_size, "end": end, "error": err,
                         "first": bars[0]["date"] if bars else None,
                         "last": bars[-1]["date"] if bars else None})
            samples.append(meta)
    row["samples"] = [{k: s.get(k) for k in ("what", "bar", "end", "n", "first", "last", "sha256", "error", "status")} for s in samples]
    row["gates"]["interior_gaps"] = "NOT_RUN_INTERIOR_GAPS"
    m1 = [s for s in samples if s.get("bar") == "1 min"]
    row["gates"]["m1_sample_days"] = "PASS" if m1 and all((s.get("n") or 0) > 0 for s in m1) else "FAIL"
    row["gates"]["m1_full_corpus"] = "NOT_RUN_SIZE_CAP"
    if spec["asset"] == "XAUUSD":
        row["xau_overlap"] = xau_overlap(daily["BID"], daily["ASK"])
    return row


def coverage(bars: list[dict]) -> dict:
    days = sorted({b["session_date"] for b in bars if b.get("session_date")})
    if not days:
        return {"n_days": 0, "span_gate": "FAIL", "first": None, "last": None, "holes": []}
    holes = []
    for a, b in zip(days, days[1:]):
        da = datetime.fromisoformat(a)
        db = datetime.fromisoformat(b)
        gap = (db - da).days
        if gap > 5:
            holes.append({"after": a, "before": b, "calendar_days": gap})
    span_ok = days[0] <= "2021-01-08" and days[-1] >= "2026-09-26" and not holes
    return {
        "n_days": len(days),
        "first": days[0],
        "last": days[-1],
        "hole_count": len(holes),
        "holes_first5": holes[:5],
        "span_gate": "PASS" if span_ok else "FAIL",
    }


def spread_summary(bid_bars, ask_bars) -> dict:
    bid = {b["session_date"]: b["close"] for b in bid_bars}
    ask = {b["session_date"]: b["close"] for b in ask_bars}
    keys = sorted(set(bid) & set(ask))
    spreads = []
    for k in keys:
        b, a = bid[k], ask[k]
        if b and a and a >= b > 0:
            mid = (a + b) / 2
            spreads.append((a - b) / mid * 1e4)
    if not spreads:
        return {"n": 0}
    spreads.sort()
    def pct(q):
        return round(spreads[min(len(spreads) - 1, int(q * (len(spreads) - 1)))], 4)
    return {"n": len(spreads), "p50_bps": pct(0.50), "p90_bps": pct(0.90), "max_bps": round(spreads[-1], 4)}


def xau_overlap(bid_bars, ask_bars) -> dict:
    out = {"archive_sha_expected": ARCHIVE_SHA}
    if not ARCHIVE.exists():
        out["status"] = "NOT_RUN"
        out["reason"] = "archive missing"
        return out
    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    out["archive_sha"] = digest
    if digest != ARCHIVE_SHA:
        out["status"] = "FAIL"
        out["reason"] = "archive sha mismatch; overlap aborted"
        return out
    td = json.loads(ARCHIVE.read_text())
    td_close = {row["datetime"]: float(row["close"]) for row in td["values"]}
    bid = {b["session_date"]: b["close"] for b in bid_bars}
    ask = {b["session_date"]: b["close"] for b in ask_bars}
    days = sorted(set(bid) & set(ask) & set(td_close))
    basis = []
    for d in days:
        b, a, t = bid[d], ask[d], td_close[d]
        if b and a and a >= b > 0 and t > 0:
            mid = (a + b) / 2
            basis.append((d, mid - t, abs(mid - t) / t * 1e4))
    out["n_aligned"] = len(basis)
    out["overlap_count_gate"] = "PASS" if len(basis) >= 20 else "FAIL"
    out["definition"] = "HMDS daily (BID close + ASK close) / 2 minus TD close; not the frozen 17:00 ET window mid"
    out["pit_lag"] = "ASSUMED_NEXT_BUSINESS_DAY"
    out["pit_status"] = "NOT_MEASURED"
    out["basis_acceptance"] = "NOT_RUN_THRESHOLDS_UNFROZEN"
    if basis:
        bps = sorted(x[2] for x in basis)
        signed = [x[1] for x in basis]
        out["first"] = basis[0][0]
        out["last"] = basis[-1][0]
        out["abs_basis_p50_bps"] = round(bps[len(bps) // 2], 4)
        out["abs_basis_p95_bps"] = round(bps[min(len(bps) - 1, int(0.95 * (len(bps) - 1)))], 4)
        out["signed_mean_usd"] = round(sum(signed) / len(signed), 4)
    return out


def acquire_future(ib, errors, asset, symbol, exchange, front_conid, note) -> dict:
    row = {
        "asset": asset, "note": note, "symbol": symbol, "exchange": exchange,
        "tradable_chain": "FUT", "contfut_is_not_the_tradable_chain": True,
        "gates": {}, "chunks": [],
    }
    if timed_out():
        row["gates"]["all"] = "NOT_RUN_TIME_CAP"
        return row
    front = Contract()
    front.conId = front_conid
    front.exchange = exchange
    try:
        details = ib.reqContractDetails(front)
    except Exception as exc:
        details = []
        row["conid_lookup_error"] = redact(str(exc))[:240]
    if not details:
        bare = Contract()
        bare.symbol = symbol
        bare.secType = "FUT"
        bare.exchange = exchange
        bare.currency = "USD"
        try:
            details = ib.reqContractDetails(bare)
        except Exception as exc:
            row["gates"]["contract_venue"] = "FAIL"
            row["identity_error"] = redact(str(exc))[:240]
            return row
        if not details:
            row["gates"]["contract_venue"] = "FAIL"
            row["identity_error"] = "no FUT details"
            return row
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        def _exp(cd):
            return cd.realExpirationDate or cd.contract.lastTradeDateOrContractMonth or "99999999"
        future = [d for d in details if _exp(d) >= today] or details
        details = [sorted(future, key=_exp)[0]]
        row["front_resolved_by"] = "nearest listed FUT; pinned conId did not resolve"
    fc = details[0].contract
    row["front"] = {
        "conId": fc.conId, "localSymbol": fc.localSymbol, "secType": fc.secType,
        "lastTradeDateOrContractMonth": fc.lastTradeDateOrContractMonth,
        "exchange": fc.exchange, "minTick": details[0].minTick,
        "timeZoneId": details[0].timeZoneId, "longName": details[0].longName,
    }
    row["gates"]["contract_venue"] = "PASS" if fc.secType == "FUT" and fc.symbol == symbol and fc.exchange == exchange else "FAIL"
    boundary = {}
    for month in ("202507", "202508", "202509", "202510", "202511", "202512", "202601"):
        c = Contract()
        c.symbol = symbol
        c.secType = "FUT"
        c.exchange = exchange
        c.currency = "USD"
        c.lastTradeDateOrContractMonth = month
        c.includeExpired = True
        mark = len(errors)
        try:
            ds = ib.reqContractDetails(c)
        except Exception:
            ds = []
        err = since(errors, mark)
        boundary[month] = {
            "n": len(ds),
            "localSymbol": ds[0].contract.localSymbol if ds else None,
            "lastTrade": ds[0].contract.lastTradeDateOrContractMonth if ds else None,
            "error": err[:1],
        }
        time.sleep(0.2)
    row["month_boundary"] = boundary
    resolved = [m for m, v in boundary.items() if v["n"] > 0]
    row["gates"]["expired_2021_now"] = "FAIL"
    row["expired_note"] = (
        f"prior quarters 202103-202506 are error 200 in FOLLOWUP; "
        f"this pass boundary resolved {resolved}"
    )
    cont = Contract()
    cont.symbol = symbol
    cont.secType = "CONTFUT"
    cont.exchange = exchange
    cont.currency = "USD"
    try:
        cds = ib.reqContractDetails(cont)
    except Exception:
        cds = []
    if cds:
        cc = cds[0].contract
        row["contfut"] = {
            "conId": cc.conId, "secType": cc.secType, "localSymbol": cc.localSymbol,
            "same_conid_as_front": cc.conId == front_conid,
            "longName": cds[0].longName,
        }
    else:
        row["contfut"] = None
    row["gates"]["roll_rule"] = "FAIL"
    row["roll_rule_reason"] = "adjustment method not in contract details; CONTFUT localSymbol is one month"
    row["entitlement"] = entitlement(ib, errors, fc)
    live = row["entitlement"].get("live_type1")
    delayed = row["entitlement"].get("delayed_type3")
    row["gates"]["live_market_data"] = "PASS" if live == "QUOTE" else "FAIL"
    row["gates"]["delayed_market_data"] = "PASS" if delayed == "QUOTE" else (
        "FAIL" if delayed else "NOT_RUN"
    )
    # Owner asked to try a valid historical path after classifying 354.
    targets = [("front", fc)]
    if cds:
        targets.append(("contfut", cds[0].contract))
    hist_rows = []
    for name, contract in targets:
        for what, end, duration, bar_size in (
            ("TRADES", "", "1 Y", "1 day"),
            ("TRADES", "20220115 00:00:00 UTC", "1 M", "1 day"),
            ("BID", "", "5 D", "1 day"),
            ("ASK", "", "5 D", "1 day"),
        ):
            if timed_out():
                hist_rows.append({"target": name, "what": what, "status": "NOT_RUN_TIME_CAP"})
                continue
            bars, err = hist(ib, errors, contract, end, duration, bar_size, what)
            meta = write_chunk(asset, f"{name}_{what}_{bar_size.replace(' ', '')}_{end[:8] or 'now'}", bars)
            meta.update({"target": name, "what": what, "end": end or "now", "bar": bar_size, "error": err,
                         "first": bars[0]["session_date"] if bars else None,
                         "last": bars[-1]["session_date"] if bars else None})
            hist_rows.append({k: meta.get(k) for k in ("target", "what", "bar", "end", "n", "first", "last", "sha256", "error", "status")})
            if bars and what == "TRADES" and end == "":
                row.setdefault("trades_recent_span", {})[name] = {"n": len(bars), "first": bars[0]["session_date"], "last": bars[-1]["session_date"]}
    row["history"] = hist_rows
    recent = [h for h in hist_rows if h.get("target") == "front" and h.get("what") == "TRADES" and h.get("end") == "now"]
    back = [h for h in hist_rows if h.get("what") == "TRADES" and str(h.get("end", "")).startswith("2022")]
    row["gates"]["historical_sample"] = "PASS" if recent and (recent[0].get("n") or 0) > 0 else "FAIL"
    reached_2022 = any((h.get("n") or 0) > 0 and (h.get("first") or "9999") <= "2022-01-15" for h in back)
    row["gates"]["history_reaches_2022_sample"] = "PASS" if reached_2022 else "FAIL"
    row["gates"]["interior_gaps"] = "NOT_RUN_INTERIOR_GAPS"
    row["gates"]["cost"] = "NOT_RUN"
    row["cost_reason"] = "no Activity/Flex statement at ~/.my-quantitative-data/ibkr_statement/"
    if asset == "NATGAS":
        row["gates"]["weather_pit_archive"] = "NOT_REQUIRED_FOR_CURRENT_RUNNABLE_LEGS"
        row["weather_note"] = (
            "mechanization_triage_292.tsv has 0 NATGAS rows; weather ideas in "
            "PORTFOLIO_ELIGIBILITY_1200.tsv (S001 S024 S058 S074 S094) stay BLOCKED_NO_PRICE_DATA"
        )
    return row


def entitlement(ib, errors, contract) -> dict:
    out = {}
    for mdt, name in ((1, "live_type1"), (3, "delayed_type3")):
        if timed_out():
            out[name] = "NOT_RUN_TIME_CAP"
            continue
        ib.reqMarketDataType(mdt)
        mark = len(errors)
        ticker = ib.reqMktData(contract, "", True, False)
        ib.sleep(6)
        try:
            ib.cancelMktData(contract)
        except Exception:
            pass
        err = since(errors, mark)
        bid = float(ticker.bid or 0)
        ask = float(ticker.ask or 0)
        quoted = int(ticker.marketDataType or 0) in (1, 2, 3, 4) and bid > 0 and ask >= bid
        out[name] = "QUOTE" if quoted else "NO_QUOTE"
        out[name + "_detail"] = {
            "marketDataType": int(ticker.marketDataType or 0),
            "bid_positive": bid > 0,
            "ask_positive": ask > 0,
            "errors": err[:3],
        }
    return out


def _finish(report: dict) -> None:
    path = CONTROL / "ACQUISITION_REPORT.json"
    path.write_text(json.dumps(report, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
