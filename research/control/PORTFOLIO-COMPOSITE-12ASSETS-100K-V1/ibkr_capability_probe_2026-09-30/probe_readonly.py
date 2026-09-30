"""Read-only IBKR paper capability probe for seven blocked portfolio columns.

Port 127.0.0.1:7497 only. readonly=True. No orders, no bulk history,
no scored computation. Account ids are never written.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from ib_insync import Contract, IB

OUT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 7497
CLIENT_ID = 9047
XAU_CONID = 69067924
INFO_CODES = set(range(2100, 2200))
REDACT = re.compile(r"\b[A-Z]{1,3}\d{4,}\b")

logging.basicConfig(level=logging.WARNING)


def redact(text: str) -> str:
    return REDACT.sub("[REDACTED]", text)


class _Redact(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(str(record.msg))
        if record.args:
            record.args = tuple(redact(str(a)) for a in record.args)
        return True


logging.getLogger("ib_insync").addFilter(_Redact())


def cash(symbol: str, currency: str) -> Contract:
    c = Contract()
    c.symbol = symbol
    c.secType = "CASH"
    c.exchange = "IDEALPRO"
    c.currency = currency
    return c


def cmdty(symbol: str, exchange: str = "SMART") -> Contract:
    c = Contract()
    c.symbol = symbol
    c.secType = "CMDTY"
    c.exchange = exchange
    c.currency = "USD"
    return c


def fut(symbol: str, exchange: str, month: str = "", expired: bool = False) -> Contract:
    c = Contract()
    c.symbol = symbol
    c.secType = "FUT"
    c.exchange = exchange
    c.currency = "USD"
    if month:
        c.lastTradeDateOrContractMonth = month
    if expired:
        c.includeExpired = True
    return c


def contfut(symbol: str, exchange: str) -> Contract:
    c = Contract()
    c.symbol = symbol
    c.secType = "CONTFUT"
    c.exchange = exchange
    c.currency = "USD"
    return c


# Candidates are named public IB venues. A second hit is ambiguity, not a choice.
ASSETS = [
    {
        "asset": "NZDUSD",
        "kind": "fx",
        "candidates": [("IDEALPRO CASH NZD/USD", cash("NZD", "USD"))],
    },
    {
        "asset": "USDCHF",
        "kind": "fx",
        "candidates": [("IDEALPRO CASH USD/CHF", cash("USD", "CHF"))],
    },
    {
        "asset": "XAUUSD",
        "kind": "metal",
        "frozen_conid": XAU_CONID,
        "candidates": [("CMDTY SMART conId 69067924", None)],
    },
    {
        "asset": "XAGUSD",
        "kind": "metal",
        "candidates": [("CMDTY SMART XAGUSD", cmdty("XAGUSD"))],
    },
    {
        "asset": "BRENT",
        "kind": "future",
        "candidates": [
            ("FUT COIL IPE", fut("COIL", "IPE")),
            ("FUT BZ NYMEX", fut("BZ", "NYMEX")),
            ("FUT BRN IPE", fut("BRN", "IPE")),
        ],
    },
    {
        "asset": "WTI",
        "kind": "future",
        "candidates": [("FUT CL NYMEX", fut("CL", "NYMEX"))],
    },
    {
        "asset": "NATGAS",
        "kind": "future",
        "candidates": [("FUT NG NYMEX", fut("NG", "NYMEX"))],
    },
]


def detail_brief(cd) -> dict:
    c = cd.contract
    return {
        "conId": c.conId,
        "symbol": c.symbol,
        "localSymbol": c.localSymbol,
        "secType": c.secType,
        "exchange": c.exchange,
        "primaryExchange": c.primaryExchange,
        "currency": c.currency,
        "tradingClass": c.tradingClass,
        "lastTradeDateOrContractMonth": c.lastTradeDateOrContractMonth,
        "multiplier": c.multiplier,
        "minTick": cd.minTick,
        "marketName": cd.marketName,
        "longName": cd.longName,
        "timeZoneId": cd.timeZoneId,
        "realExpirationDate": cd.realExpirationDate,
        "underConId": cd.underConId or None,
        "underSymbol": cd.underSymbol or None,
    }


def main() -> None:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    errors: list[dict] = []
    ib = IB()
    ib.RequestTimeout = 25
    ib.RaiseRequestErrors = True

    def on_error(reqId, code, msg, contract):
        errors.append(
            {
                "reqId": reqId,
                "code": int(code),
                "msg": redact(str(msg))[:400],
                "conId": getattr(contract, "conId", None) if contract else None,
                "t": time.time(),
            }
        )

    ib.errorEvent += on_error
    report: dict = {
        "probe": "IBKR-PAPER-CAPABILITY-READONLY-2026-09-30",
        "run_id": run_id,
        "host": HOST,
        "port": PORT,
        "readonly": True,
        "client_id": CLIENT_ID,
        "orders_placed": 0,
        "bulk_download": False,
        "eligibility_modified": False,
        "registry_modified": False,
        "heavy_lock_acquired": False,
        "s1_opened": False,
        "scored_cell": False,
        "handshake": {},
        "assets": [],
    }

    connected = False
    connect_error = None
    for attempt in (1, 2):
        try:
            ib.connect(HOST, PORT, clientId=CLIENT_ID, timeout=20, readonly=True)
            connected = ib.isConnected()
            if connected:
                break
        except Exception as exc:  # noqa: BLE001
            connect_error = redact(str(exc))[:300]
            time.sleep(5)
    if not connected:
        report["handshake"] = {
            "status": "FAIL",
            "error": connect_error or "connect returned not connected",
            "attempts": 2,
        }
        for spec in ASSETS:
            report["assets"].append(_blocked(spec["asset"], "FAIL", "handshake FAIL"))
        _write(report)
        return

    accounts = list(ib.managedAccounts())
    prefixes = sorted({(a[:2] if len(a) >= 2 else "?") for a in accounts})
    paper = bool(accounts) and all(a.startswith("DU") for a in accounts)
    try:
        server_time = str(ib.reqCurrentTime())
    except Exception as exc:  # noqa: BLE001
        server_time = None
        connect_error = redact(str(exc))[:300]
    report["handshake"] = {
        "status": "PASS" if paper and server_time else "FAIL",
        "server_time": server_time,
        "managed_accounts_count": len(accounts),
        "account_prefix_class": prefixes,
        "paper_du_prefix": paper,
        "readonly_api": True,
        "error": None if paper and server_time else (
            connect_error or "account prefix is not paper DU"
        ),
    }
    if not paper or not server_time:
        for spec in ASSETS:
            report["assets"].append(
                _blocked(spec["asset"], "FAIL", report["handshake"]["error"])
            )
        ib.disconnect()
        _write(report)
        return

    ib.reqMarketDataType(1)
    ib.sleep(0.5)

    try:
        for spec in ASSETS:
            print(f"PROBE {spec['asset']}", flush=True)
            report["assets"].append(_probe_asset(ib, spec, errors))
    finally:
        if ib.isConnected():
            ib.disconnect()
        report["disconnected"] = True
        _write(report)


def _blocked(asset: str, status: str, reason: str) -> dict:
    return {
        "asset": asset,
        "handshake": status,
        "contract_venue": "NOT_RUN",
        "market_data_permission": "NOT_RUN",
        "historical_sample": "NOT_RUN",
        "futures_expired_coverage": "NOT_RUN" if asset in {"BRENT", "WTI", "NATGAS"} else "NA",
        "roll_data": "NOT_RUN" if asset in {"BRENT", "WTI", "NATGAS"} else "NA",
        "gaps_2021_now": "NOT_RUN",
        "data_reached": None,
        "primary_error": reason,
        "consider_unlock": False,
        "still_required": ["prior gate failed: " + reason],
    }


def _since(errors: list[dict], mark: int) -> list[dict]:
    out = []
    for row in errors[mark:]:
        if row["code"] in INFO_CODES or row["code"] == 366:
            continue
        out.append({"code": row["code"], "msg": row["msg"]})
    return out


def _call(ib: IB, fn, errors: list[dict]):
    mark = len(errors)
    try:
        value = fn()
        return value, _since(errors, mark), None
    except Exception as exc:  # noqa: BLE001
        err = _since(errors, mark)
        text = redact(str(exc))[:400]
        if not err:
            err = [{"code": getattr(exc, "code", None), "msg": text}]
        return None, err, text


def _probe_asset(ib: IB, spec: dict, errors: list[dict]) -> dict:
    asset = spec["asset"]
    kind = spec["kind"]
    row = {
        "asset": asset,
        "kind": kind,
        "handshake": "PASS",
        "candidates": [],
        "contract_venue": "FAIL",
        "market_data_permission": "NOT_RUN",
        "historical_sample": "NOT_RUN",
        "futures_expired_coverage": "NA" if kind != "future" else "NOT_RUN",
        "roll_data": "NA" if kind != "future" else "NOT_RUN",
        "gaps_2021_now": "NOT_RUN",
        "data_reached": None,
        "primary_error": None,
        "resolved": None,
        "consider_unlock": False,
        "still_required": [],
    }
    hits = []
    for label, contract in spec["candidates"]:
        if asset == "XAUUSD" and contract is None:
            contract = Contract()
            contract.conId = XAU_CONID
            contract.exchange = "SMART"
        details, err, text = _call(ib, lambda c=contract: ib.reqContractDetails(c), errors)
        brief = {
            "label": label,
            "n": 0 if not details else len(details),
            "error": err[:3],
            "sample": [detail_brief(d) for d in (details or [])[:8]],
            "truncated": bool(details and len(details) > 8),
        }
        row["candidates"].append(brief)
        if details:
            hits.append((label, details))
        time.sleep(0.2)

    if asset == "XAUUSD" and not hits:
        alt, err, _ = _call(ib, lambda: ib.reqContractDetails(cmdty("XAUUSD", "SMART")), errors)
        row["frozen_conid_miss_symbol_retry"] = {
            "n": 0 if not alt else len(alt),
            "error": err[:3],
            "sample": [detail_brief(d) for d in (alt or [])[:3]],
        }
        if alt and any(d.contract.conId == XAU_CONID for d in alt):
            hits.append(("CMDTY SMART symbol matched frozen conId", alt))
        elif alt:
            row["primary_error"] = (
                f"frozen conId {XAU_CONID} did not resolve; symbol retry "
                f"returned different conId {alt[0].contract.conId}"
            )

    if not hits:
        row["primary_error"] = row["primary_error"] or _first_err(row["candidates"])
        row["still_required"].append("a contract that resolves on this paper session")
        return row

    if kind == "future":
        if len(hits) != 1:
            row["contract_venue"] = "FAIL"
            row["primary_error"] = "AMBIGUOUS_VENUE: " + ", ".join(
                f"{label} n={len(details)}" for label, details in hits
            )
            row["still_required"].append(
                "owner/main agent must name one energy venue before any fetch is treated as the column"
            )
            # Identity metadata per candidate only. No price history while the venue is ambiguous.
            row["futures_expired_coverage"] = "NOT_RUN"
            row["roll_data"] = "NOT_RUN"
            row["candidate_identity"] = []
            for label, details in hits:
                front = _front(details)
                c = front.contract
                row["candidate_identity"].append({
                    "label": label,
                    "front": detail_brief(front),
                    "listed_nonexpired_n": len(details),
                    "expired_coverage": _expired_coverage(ib, c.symbol, c.exchange, errors),
                    "roll": _roll_meta(ib, c, errors),
                })
            return row
        label, details = hits[0]
        front = _front(details)
        c = front.contract
        row["resolved"] = {"label": label, **detail_brief(front)}
        row["listed_nonexpired_n"] = len(details)
        row["contract_venue"] = "PASS"
        cov = _expired_coverage(ib, c.symbol, c.exchange, errors)
        roll = _roll_meta(ib, c, errors)
        row["expired_coverage_detail"] = cov
        row["roll_detail"] = roll
        row["futures_expired_coverage"] = cov["status"]
        row["roll_data"] = roll["status"]
        _permission_and_history(ib, row, c, errors, what="TRADES", kind=kind, cont=roll.get("qualified_contract"))
        return row

    # FX / metals: one candidate family. Multiple details with different conIds fail.
    label, details = hits[0]
    conids = {d.contract.conId for d in details}
    if asset == "XAUUSD" and XAU_CONID not in conids:
        row["primary_error"] = f"resolved conIds {sorted(conids)} != frozen {XAU_CONID}"
        row["still_required"].append("frozen London gold conId 69067924")
        return row
    if len(conids) != 1:
        row["primary_error"] = f"AMBIGUOUS_CONTRACT conIds={sorted(conids)}"
        row["still_required"].append("a single contract identity")
        return row
    chosen = next(d for d in details if d.contract.conId == (XAU_CONID if asset == "XAUUSD" else next(iter(conids))))
    row["resolved"] = {"label": label, **detail_brief(chosen)}
    if asset == "XAUUSD":
        ok = (
            chosen.contract.conId == XAU_CONID
            and chosen.contract.symbol == "XAUUSD"
            and chosen.contract.secType == "CMDTY"
            and chosen.contract.currency == "USD"
        )
        row["contract_venue"] = "PASS" if ok else "FAIL"
        if not ok:
            row["primary_error"] = "XAUUSD fields diverged from frozen CMDTY/SMART/USD identity"
            return row
    else:
        row["contract_venue"] = "PASS"
    what = "MIDPOINT"
    _permission_and_history(ib, row, chosen.contract, errors, what=what, kind=kind, cont=None)
    return row


def _first_err(candidates: list[dict]) -> str:
    for c in candidates:
        if c["error"]:
            e = c["error"][0]
            return f"{c['label']}: {e.get('code')} {e.get('msg')}"
    return "NO_CONTRACT_DETAILS"


def _front(details: list):
    def key(cd):
        return cd.realExpirationDate or cd.contract.lastTradeDateOrContractMonth or "99999999"

    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    future = [d for d in details if key(d) >= today]
    pool = future or details
    return sorted(pool, key=key)[0]


def _expired_coverage(ib: IB, symbol: str, exchange: str, errors: list[dict]) -> dict:
    years = {}
    for year in ("2021", "2022", "2023", "2024", "2025", "2026"):
        details, err, _ = _call(
            ib,
            lambda y=year: ib.reqContractDetails(fut(symbol, exchange, y, expired=True)),
            errors,
        )
        months = []
        if details:
            months = sorted({
                (d.contract.lastTradeDateOrContractMonth or d.realExpirationDate or "")[:6]
                for d in details
            })
        years[year] = {
            "n": 0 if not details else len(details),
            "months": months,
            "error": err[:2],
        }
        time.sleep(0.25)
    nonempty = [y for y, v in years.items() if v["n"] > 0]
    if len(nonempty) == 6:
        status = "PASS"
    elif nonempty:
        status = "FAIL"
    else:
        status = "FAIL"
    return {
        "status": status,
        "years_with_contracts": nonempty,
        "years": years,
        "note": "contract identity only; not a price history",
    }


def _roll_meta(ib: IB, front: Contract, errors: list[dict]) -> dict:
    details, err, _ = _call(
        ib,
        lambda: ib.reqContractDetails(contfut(front.symbol, front.exchange)),
        errors,
    )
    if not details:
        return {
            "status": "FAIL",
            "error": err[:2] or [{"code": None, "msg": "NO_CONTFUT"}],
            "adjustment_method": "NOT_RETURNED",
        }
    if len({d.contract.conId for d in details}) != 1:
        return {
            "status": "FAIL",
            "error": [{"code": None, "msg": "AMBIGUOUS_CONTFUT"}],
            "n": len(details),
            "adjustment_method": "NOT_RETURNED",
        }
    brief = detail_brief(details[0])
    long_name = (brief.get("longName") or "") + " " + (brief.get("marketName") or "")
    method = "NOT_RETURNED_BY_CONTRACT_DETAILS"
    for token in ("back-adjust", "back adjust", "ratio", "panama", "non-adjusted", "unadjusted"):
        if token in long_name.lower():
            method = token
    return {
        "status": "PASS",
        "qualified_contract": {
            "conId": brief["conId"],
            "symbol": brief["symbol"],
            "exchange": brief["exchange"],
            "secType": "CONTFUT",
            "localSymbol": brief["localSymbol"],
            "tradingClass": brief["tradingClass"],
        },
        "longName": brief["longName"],
        "marketName": brief["marketName"],
        "adjustment_method": method,
    }


def _permission_and_history(ib, row, contract, errors, what, kind, cont):
    mark = len(errors)
    ticker = ib.reqMktData(contract, "", True, False)
    ib.sleep(8)
    try:
        ib.cancelMktData(contract)
    except Exception:
        pass
    perm_err = _since(errors, mark)
    bid = float(ticker.bid or 0)
    ask = float(ticker.ask or 0)
    mdt = int(ticker.marketDataType or 0)
    live = mdt == 1 and bid > 0 and ask >= bid
    row["market_data"] = {
        "marketDataType": mdt,
        "bid_positive": bid > 0,
        "ask_positive": ask > 0,
        "ask_ge_bid": ask >= bid if bid > 0 else False,
        "errors": perm_err[:4],
    }
    if live:
        row["market_data_permission"] = "PASS"
    else:
        row["market_data_permission"] = "FAIL"
        row["primary_error"] = (
            f"live permission failed mdt={mdt} bid_pos={bid > 0} ask_pos={ask > 0} "
            + (f"{perm_err[0]['code']} {perm_err[0]['msg']}" if perm_err else "no error code")
        )
        row["historical_sample"] = "NOT_RUN"
        row["gaps_2021_now"] = "NOT_RUN"
        row["still_required"].append("paper-account live market-data entitlement for this conId")
        if kind == "future":
            row["still_required"].append("historical gap/roll price sample not requested: permission gate failed")
        return

    head, err, _ = _call(
        ib,
        lambda: ib.reqHeadTimeStamp(contract, what, False, 2),
        errors,
    )
    time.sleep(1.1)
    bars, berr, _ = _call(
        ib,
        lambda: ib.reqHistoricalData(
            contract, "", "2 D", "1 hour", what, False, 1, False, [], 25
        ),
        errors,
    )
    time.sleep(1.1)
    if kind == "future":
        anchor, aerr = None, []
    else:
        anchor, aerr, _ = _call(
            ib,
            lambda: ib.reqHistoricalData(
                contract, "20210120 00:00:00 UTC", "5 D", "1 day", what, False, 1, False, [], 25
            ),
            errors,
        )
    sample = {
        "whatToShow": what,
        "contract": "front" if kind == "future" else "spot",
        "head_timestamp": str(head) if head else None,
        "head_error": err[:2],
        "recent_2d_1h": _bars(bars),
        "recent_error": berr[:2],
        "anchor_2021_01_5d": _bars(anchor) if kind != "future" else {"n": 0, "skipped": "front month cannot cover 2021"},
        "anchor_error": aerr[:2],
    }
    row["historical_sample_detail"] = sample
    recent_n = sample["recent_2d_1h"]["n"]
    if recent_n > 0 and head:
        row["historical_sample"] = "PASS"
        row["data_reached"] = f"head {head}; recent hourly n={recent_n}"
    elif recent_n > 0:
        row["historical_sample"] = "FAIL"
        row["data_reached"] = f"recent hourly n={recent_n}; head timestamp missing"
        row["primary_error"] = _err_text(err) or "head timestamp missing"
    else:
        row["historical_sample"] = "FAIL"
        row["primary_error"] = _err_text(berr) or _err_text(err) or "historical sample empty"
        row["data_reached"] = None

    if kind != "future":
        head_ok = _head_covers_2021(head)
        anchor_ok = sample["anchor_2021_01_5d"]["n"] > 0
        if head_ok and anchor_ok:
            row["gaps_2021_now"] = "PASS"
            row["gap_note"] = (
                "head timestamp on/before 2021-01-01 and a 5-day daily anchor in "
                "Jan 2021 returned bars; interior gaps were not scanned"
            )
        else:
            row["gaps_2021_now"] = "FAIL"
            row["gap_note"] = (
                "small sample does not show continuous coverage from 2021; no bulk scan was run"
            )
        _fx_metal_consider(row, head_ok, anchor_ok)
        return

    # Front-month 2021 anchors would be empty by construction. Coverage is read
    # from CONTFUT and from expired months that actually traded then.
    anchors = {}
    pacing = False
    cont_sample = {"status": "NOT_RUN"}
    if not cont:
        row["roll_data"] = "FAIL"
        row["gaps_2021_now"] = "NOT_RUN"
        row["gap_note"] = "CONTFUT did not qualify; yearly anchors not requested"
    else:
        cc = Contract()
        cc.conId = cont["conId"]
        cc.exchange = cont["exchange"]
        cc.secType = "CONTFUT"
        head_c, herr, _ = _call(
            ib, lambda: ib.reqHeadTimeStamp(cc, what, False, 2), errors
        )
        time.sleep(1.1)
        got, gerr, _ = _call(
            ib,
            lambda: ib.reqHistoricalData(
                cc, "", "5 D", "1 day", what, False, 1, False, [], 25
            ),
            errors,
        )
        cont_sample = {
            "head_timestamp": str(head_c) if head_c else None,
            "head_error": herr[:2],
            "recent_5d": _bars(got),
            "error": gerr[:2],
        }
        if any("pacing" in (e.get("msg") or "").lower() for e in gerr + herr):
            pacing = True
        if cont_sample["recent_5d"]["n"] <= 0:
            row["roll_data"] = "FAIL"
            row["roll_detail"]["status_reason"] = _err_text(gerr) or "CONTFUT recent sample empty"
        else:
            row["roll_data"] = "PASS"
            row["roll_detail"]["price_sample"] = {
                "n": cont_sample["recent_5d"]["n"],
                "first": cont_sample["recent_5d"]["first"],
                "last": cont_sample["recent_5d"]["last"],
            }
            row["roll_detail"]["status_reason"] = (
                "CONTFUT series returned bars; adjustment method was not in contract details"
                if row["roll_detail"].get("adjustment_method") == "NOT_RETURNED_BY_CONTRACT_DETAILS"
                else "CONTFUT series returned bars"
            )
        for year in ("2021", "2022", "2023", "2024", "2025", "2026"):
            if pacing:
                anchors[year] = {"status": "NOT_RUN", "reason": "pacing stop"}
                continue
            end = f"{year}0701 00:00:00 UTC"
            got_y, gerr_y, _ = _call(
                ib,
                lambda e=end, c=cc: ib.reqHistoricalData(
                    c, e, "5 D", "1 day", what, False, 1, False, [], 25
                ),
                errors,
            )
            anchors[year] = {"bars": _bars(got_y), "error": gerr_y[:2]}
            if any("pacing" in (e.get("msg") or "").lower() for e in gerr_y):
                pacing = True
            time.sleep(1.1)
        row["contfut_head"] = cont_sample["head_timestamp"]

    expired_sample = []
    cov = row.get("expired_coverage_detail") or {}
    picked = []
    for year in ("2021", "2023", "2025"):
        months = ((cov.get("years") or {}).get(year) or {}).get("months") or []
        if months:
            picked.append(months[0])
    if not pacing:
        for month in picked:
            exp_c = fut(contract.symbol, contract.exchange, month, expired=True)
            qualified, qerr, _ = _call(ib, lambda c=exp_c: ib.reqContractDetails(c), errors)
            if not qualified:
                expired_sample.append({"month": month, "error": qerr[:2], "bars": {"n": 0}})
                continue
            qc = qualified[0].contract
            end = (qc.lastTradeDateOrContractMonth or (month + "15"))[:8]
            if len(end) == 6:
                end = end + "15"
            got_e, gerr_e, _ = _call(
                ib,
                lambda c=qc, e=end: ib.reqHistoricalData(
                    c, f"{e} 00:00:00 UTC", "5 D", "1 day", what, False, 1, False, [], 25
                ),
                errors,
            )
            expired_sample.append({
                "month": month,
                "conId": qc.conId,
                "localSymbol": qc.localSymbol,
                "lastTradeDateOrContractMonth": qc.lastTradeDateOrContractMonth,
                "bars": _bars(got_e),
                "error": gerr_e[:2],
            })
            if any("pacing" in (e.get("msg") or "").lower() for e in gerr_e):
                pacing = True
                break
            time.sleep(1.1)
    row["futures_price_anchors"] = anchors
    row["expired_price_sample"] = expired_sample
    row["contfut_price_sample"] = cont_sample
    empty_years = [y for y, v in anchors.items() if v.get("bars", {}).get("n", 0) <= 0]
    cont_head = _parse_head(cont_sample.get("head_timestamp")) if cont else None
    if not cont:
        pass
    elif pacing:
        row["gaps_2021_now"] = "NOT_RUN"
        row["gap_note"] = "stopped after HMDS pacing; remaining anchors NOT_RUN"
    elif anchors and not empty_years and _head_covers_2021(cont_head):
        row["gaps_2021_now"] = "PASS"
        row["gap_note"] = (
            "six mid-year 5-day CONTFUT anchors returned bars and the CONTFUT head "
            "timestamp is on/before 2021-01-01; interior days were not scanned"
        )
    else:
        row["gaps_2021_now"] = "FAIL"
        row["gap_note"] = (
            f"empty anchors {empty_years}; contfut head {cont_sample.get('head_timestamp')}"
        )
    _future_consider(row, empty_years, expired_sample, cont_sample, cont_head)


def _bars(bars) -> dict:
    if not bars:
        return {"n": 0}
    payload = [
        (str(b.date), b.open, b.high, b.low, b.close, b.volume)
        for b in bars
    ]
    digest = hashlib.sha256(repr(payload).encode()).hexdigest()[:16]
    return {
        "n": len(bars),
        "first": str(bars[0].date),
        "last": str(bars[-1].date),
        "sha256_16": digest,
    }


def _head_covers_2021(head) -> bool:
    if head is None:
        return False
    if hasattr(head, "year"):
        return (head.year, head.month, head.day) <= (2021, 1, 1)
    text = str(head)
    return text[:10] <= "2021-01-01"


def _err_text(err: list[dict]) -> str | None:
    if not err:
        return None
    return f"{err[0].get('code')} {err[0].get('msg')}"


def _fx_metal_consider(row, head_ok: bool, anchor_ok: bool) -> None:
    ready = (
        row["contract_venue"] == "PASS"
        and row["market_data_permission"] == "PASS"
        and row["historical_sample"] == "PASS"
        and head_ok
        and anchor_ok
    )
    row["consider_unlock"] = ready
    row["still_required"] = [
        "owner unblock decision; this probe does not change eligibility",
        "M1 bid/ask corpus 2021-now was not downloaded",
        "IBKR Activity/Flex statement for commission/swap (plan P_A)",
        "PIT/cost gate after any later acquisition",
    ]
    if row["asset"] == "XAUUSD":
        row["still_required"].append("≥20-day IBKR overlap vs the archive (matrix unblock) was not measured")
    if row["asset"] == "XAGUSD":
        row["still_required"].append("conId measured here is not a frozen identity until the main agent freezes it")
    if not ready:
        row["still_required"].insert(0, "price path is not deep enough or a prior gate failed")


def _future_consider(row, empty_years, expired_sample, cont_sample, head) -> None:
    expired_ok = bool(expired_sample) and all(
        (item.get("bars") or {}).get("n", 0) > 0 for item in expired_sample
    )
    cont_ok = (cont_sample.get("recent_5d") or {}).get("n", 0) > 0 and _head_covers_2021(
        _parse_head(cont_sample.get("head_timestamp"))
    )
    ready = (
        row["contract_venue"] == "PASS"
        and row["market_data_permission"] == "PASS"
        and row["historical_sample"] == "PASS"
        and row["futures_expired_coverage"] == "PASS"
        and row["roll_data"] == "PASS"
        and row["gaps_2021_now"] == "PASS"
        and expired_ok
        and cont_ok
        and _head_covers_2021(head)
        and not empty_years
    )
    row["consider_unlock"] = ready
    row["still_required"] = [
        "owner unblock plus a named continuous-futures identity; this probe does not change eligibility",
        "full 2021-now series was not downloaded",
        "roll adjustment method was not returned by contract details and must be declared before any vehicle freeze",
        "PIT/cost gate",
    ]
    if row["asset"] == "NATGAS":
        row["still_required"].append("weather-forecast PIT archive (matrix unblock) was not checked")
        if ready:
            row["consider_unlock"] = False
            row["consider_note"] = (
                "price channel would be reviewable, but NATGAS stays short of the matrix "
                "unblock until the weather archive exists; consider_unlock left false"
            )
    if not ready and "consider_note" not in row:
        row["still_required"].insert(0, "futures price/roll/coverage gate incomplete")


def _parse_head(text):
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text


def _write(report: dict) -> None:
    path = OUT / "PROBE_RESULT.json"
    path.write_text(json.dumps(report, indent=1, default=str) + "\n")
    print(json.dumps({
        "wrote": str(path),
        "handshake": report.get("handshake", {}).get("status"),
        "assets": [
            {
                "asset": a["asset"],
                "contract_venue": a.get("contract_venue"),
                "market_data_permission": a.get("market_data_permission"),
                "historical_sample": a.get("historical_sample"),
                "consider_unlock": a.get("consider_unlock"),
                "primary_error": a.get("primary_error"),
            }
            for a in report.get("assets", [])
        ],
    }, indent=1))


if __name__ == "__main__":
    main()
