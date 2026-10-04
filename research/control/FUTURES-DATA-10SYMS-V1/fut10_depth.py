"""FUTURES-DATA-10SYMS-V1 — depth probe for ACTIVE contracts (run after bulk).

For each symbol's FRONT (and a next-quarter contract), probe how deep
intraday and BID/ASK history goes by requesting with historical end dates.
Expired contracts measured separately (daily only, error 162 intraday).
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from ib_insync import IB, util

logging.basicConfig(level=logging.WARNING)
util.patchAsyncio()

CTL = Path(__file__).resolve().parent
HOST, PORT = "127.0.0.1", 7497

ENDS = ["20260101 00:00:00", "20240101 00:00:00", "20220101 00:00:00"]
PROBES = [
    ("TRADES", "1 min", "7 D"),
    ("TRADES", "1 hour", "30 D"),
    ("TRADES", "1 day", "6 Y"),
    ("BID", "1 day", "6 Y"),
]


def main() -> None:
    ib = IB()
    ib.connect(HOST, PORT, clientId=9218, readonly=True, timeout=15)
    ident = json.loads((CTL / "S1_IDENTITY.json").read_text())
    out = {"measured_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "endpoint": f"TWSAPI {HOST}:{PORT} readonly client 9218", "symbols": {}}
    try:
        for sym, entry in ident["symbols"].items():
            front = entry.get("front")
            if not front:
                continue
            row = {"front_localSymbol": front["localSymbol"], "conId": front["conId"],
                   "probes": []}
            from ib_insync import Contract
            for end in ENDS:
                for wu, bs, dur in PROBES:
                    ct = Contract()
                    ct.conId = front["conId"]
                    ct.exchange = front["exchange"]
                    try:
                        bars = ib.reqHistoricalData(
                            ct, endDateTime=end, durationStr=dur,
                            barSizeSetting=bs, whatToShow=wu, useRTH=True,
                            formatDate=1)
                        row["probes"].append({
                            "end": end, "whatUse": wu, "barSize": bs, "dur": dur,
                            "n": len(bars),
                            "first": str(bars[0].date)[:19] if bars else None,
                            "last": str(bars[-1].date)[:19] if bars else None,
                            "v0": sum(1 for b in bars if not b.volume) if bars else None})
                    except Exception as e:  # noqa: BLE001
                        row["probes"].append({"end": end, "whatUse": wu, "barSize": bs,
                                              "dur": dur, "error": str(e)[:120]})
                    time.sleep(2.5)
            out["symbols"][sym] = row
            ok1m = [p for p in row["probes"]
                    if p.get("whatUse") == "TRADES" and p.get("barSize") == "1 min" and p.get("n")]
            print(f"[depth] {sym} {front['localSymbol']}: "
                  f"1min windows with data={len(ok1m)}/3 "
                  f"deepest_1min_first={min((p['first'] for p in ok1m), default=None)}",
                  flush=True)
    finally:
        ib.disconnect()
    (CTL / "S7_DEPTH_ACTIVE.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
