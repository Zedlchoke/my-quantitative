#!/usr/bin/env python
"""G6 addendum pull: the 2026-07-01 session bar.

Reason (measured): a '1 M' chunk anchored at 20260731 23:59:59 UTC starts
after the 2026-07-01 session closes, so the Jul 1 bar was absent from the
main pass (sole missing weekday). The Jul 1 close is load-bearing: under
the NOT_RUN_INPUT_END fallback typing, 2026-07-02 is the first decision
that consumes the 2026-07-01 close. Same laws as g6_pull.py: read-only,
paced 10.5 s, end-bounded closed bars only, sha-frozen, no interpolation.
Appends to MANIFEST.json / VERIFICATION.json.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from ib_insync import IB, Contract

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
HOST, PORT = "127.0.0.1", 7497
CLIENT_IDS = (69, 70)
PACE_S = 10.5
INFO = set(range(2100, 2200))
END = "20260701 23:59:59 UTC"          # covers ~Jun 1 -> Jul 1 inclusive of the Jul 1 session close
TAG = "202607a"
IDENT = {  # conIds resolved by g6_pull.py main pass (re-verified below)
    "AUDUSD": {"conId": 14433401, "exchange": "IDEALPRO", "spec": dict(secType="CASH", symbol="AUD", exchange="IDEALPRO", currency="USD")},
    "USDCAD": {"conId": 15016062, "exchange": "IDEALPRO", "spec": dict(secType="CASH", symbol="USD", exchange="IDEALPRO", currency="CAD")},
}
REDACT = re.compile(r"\b[A-Z]{1,3}\d{4,}\b")
logging.basicConfig(level=logging.ERROR)
logging.getLogger("ib_insync").addFilter(
    type("R", (logging.Filter,), {"filter": lambda self, rec: (setattr(rec, "msg", REDACT.sub("[REDACTED]", str(rec.msg))) or True)})()
)
errors: list[dict] = []
now_utc = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def since(mark):
    return [e for e in errors[mark:] if e["code"] not in INFO and e["code"] != 366]


ib = IB()
ib.RequestTimeout = 40
ib.RaiseRequestErrors = True
ib.errorEvent += lambda reqId, code, msg, contract: errors.append({"code": int(code), "msg": REDACT.sub("[REDACTED]", str(msg))[:300]})
connected = None
for cid in CLIENT_IDS:
    try:
        ib.connect(HOST, PORT, clientId=cid, timeout=15, readonly=True)
        connected = cid
        break
    except Exception as exc:
        errors.append({"code": None, "msg": f"connect cid={cid}: {type(exc).__name__}: {REDACT.sub('[REDACTED]', str(exc))[:200]}"})
if connected is None:
    (HERE / "VERIFICATION.json").write_text(json.dumps(
        {**json.loads((HERE / "VERIFICATION.json").read_text()),
         "addendum_jul1": {"status": "BLOCKED", "reason": "connection refused", "errors": [e["msg"] for e in errors[-3:]]}, "finished_at_utc": now_utc()}, indent=1) + "\n")
    raise SystemExit("BLOCKED: connection refused")

man = json.loads((HERE / "MANIFEST.json").read_text())
ver = json.loads((HERE / "VERIFICATION.json").read_text())
print(f"connected clientId={connected} readonly=True server={ib.reqCurrentTime()}")

identities = {}
for sym, rec in IDENT.items():
    c = Contract()
    for k, v in rec["spec"].items():
        setattr(c, k, v)
    dets = ib.reqContractDetails(c)
    time.sleep(2.5)
    ok = bool(dets) and dets[0].contract.conId == rec["conId"]
    identities[sym] = {"reverified_conId": dets[0].contract.conId if dets else None,
                       "matches_main_pass": ok}
    if not ok:
        print(f"identity re-verify FAILED for {sym}; skipping its addendum pulls")

files_added, chunk_status = [], {}
for sym, rec in IDENT.items():
    if not identities[sym]["matches_main_pass"]:
        continue
    for what in ("BID", "ASK"):
        c = Contract()
        c.conId = rec["conId"]
        c.exchange = rec["exchange"]
        mark = len(errors)
        try:
            raw = ib.reqHistoricalData(c, endDateTime=END, durationStr="1 M",
                                       barSizeSetting="1 day", whatToShow=what,
                                       useRTH=False, formatDate=1, keepUpToDate=False,
                                       chartOptions=[], timeout=40)
            rows = [{"date": str(b.date),
                     "session_date": (b.date.strftime("%Y-%m-%d") if hasattr(b.date, "strftime") else str(b.date)[:10]),
                     "open": b.open, "high": b.high, "low": b.low, "close": b.close,
                     "volume": b.volume} for b in raw or []]
            err = since(mark)[:3]
        except Exception as exc:
            rows, err = [], since(mark) or [{"code": getattr(exc, "code", None), "msg": REDACT.sub("[REDACTED]", str(exc))[:300]}]
        time.sleep(PACE_S)
        name = f"{sym}_1d_{what}_{TAG}.json"
        blob = (json.dumps(rows, separators=(",", ":")) + "\n").encode()
        (RAW / name).write_bytes(blob)
        meta = {"file": name, "path": str(RAW / name), "n_bars": len(rows), "bytes": len(blob),
                "sha256": hashlib.sha256(blob).hexdigest(), "whatToShow": what,
                "barSizeSetting": "1 day", "durationStr": "1 M", "endDateTime": END,
                "useRTH": False, "formatDate": 1, "retrieved_at_utc": now_utc(),
                "api_errors": err, "first": rows[0]["session_date"] if rows else None,
                "last": rows[-1]["session_date"] if rows else None,
                "purpose": "addendum: recover the 2026-07-01 session bar missing from the 20260731-anchored chunk",
                "in_window_dates": [r["session_date"] for r in rows if "2026-07-01" <= r["session_date"] <= "2026-09-30"]}
        files_added.append(meta)
        has_jul1 = "2026-07-01" in meta["in_window_dates"]
        chunk_status[f"{sym}_{what}_{TAG}"] = {"status": "OK" if has_jul1 else ("EMPTY" if not rows else "NO_JUL1"), "n": len(rows)}
        print(f"addendum {sym} {what}: n={len(rows)} has_2026-07-01={has_jul1}")

ib.disconnect()

man["files"] = [f for f in man["files"] if f["file"] not in {m["file"] for m in files_added}] + files_added
man["addendum"] = {"generated_at_utc": now_utc(),
                   "reason": "20260731-anchored '1 M' chunk starts after the 2026-07-01 session close; Jul 1 bar recovered via a 20260701-anchored chunk",
                   "identities_reverified": identities, "files_added": [m["file"] for m in files_added]}
(HERE / "MANIFEST.json").write_text(json.dumps(man, indent=1) + "\n")
ver["addendum_jul1"] = {"status": "OK" if all(v["status"] == "OK" for v in chunk_status.values()) and chunk_status else "PARTIAL_OR_FAILED",
                        "chunks": chunk_status, "identities": identities}
(HERE / "VERIFICATION.json").write_text(json.dumps(ver, indent=1) + "\n")
print("ADDENDUM_DONE " + json.dumps(chunk_status))
