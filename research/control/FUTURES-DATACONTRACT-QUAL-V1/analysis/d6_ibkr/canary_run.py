"""D6-IBKRREFETCH canary — ONE request through the same code path as fut10_probe.py.

Imports the root probe module read-only and reuses its library functions only
(connect / hist_request / by_conid). fut10_probe stage functions (which write
into raw/ and append to the root manifest) are NOT invoked. This script writes
only its own result JSON under analysis/d6_ibkr/.
"""
import json
import sys
from pathlib import Path

CTL_ROOT = "/Users/hoangminhlong/my-quantitative/research/control/FUTURES-DATA-10SYMS-V1"
OUT_DIR = Path("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/"
               "research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d6_ibkr")

sys.path.insert(0, CTL_ROOT)
import fut10_probe as fp  # noqa: E402  (read-only import; module-level code is inert)

CLIENT_ID = 9261
# ES front per 2026-10-02 S1_IDENTITY baseline: ESZ6, conId 515416632, CME
ES_FRONT_CONID, ES_FRONT_EXCH, ES_FRONT_SYM = 515416632, "CME", "ESZ6"

result = {"canary_utc": fp.now_utc(),
          "endpoint": f"TWSAPI {fp.HOST}:{fp.PORT} readonly client {CLIENT_ID}",
          "request": {"conId": ES_FRONT_CONID, "localSymbol": ES_FRONT_SYM,
                      "exchange": ES_FRONT_EXCH, "whatToShow": "TRADES",
                      "barSizeSetting": "1 day", "durationStr": "3 D",
                      "useRTH": True, "keepUpToDate": False, "formatDate": 1},
          "connection": {}, "verdict": None}

ib = None
try:
    ib = fp.connect(CLIENT_ID)
    result["connection"] = {"connected": ib.isConnected(),
                            "serverVersion": ib.client.serverVersion(),
                            "client_id": CLIENT_ID, "readonly": True}
    errs = fp.ErrCollector(ib)
    c = fp.by_conid(ES_FRONT_CONID, ES_FRONT_EXCH)
    r = fp.hist_request(ib, errs, c, "TRADES", "1 day", "3 D", "")
    rows = r.get("rows", [])
    result["http_equivalent"] = "TWS-API-socket-connected"
    result["ok"] = bool(r.get("ok"))
    result["n_rows"] = len(rows)
    result["first_bar"] = rows[0]["t"] if rows else None
    result["last_bar"] = rows[-1]["t"] if rows else None
    result["errors"] = r.get("errors", [])
    result["exception"] = r.get("exception")
    result["verdict"] = "CANARY_PASS" if (r.get("ok") and rows) else "CANARY_FAIL"
except Exception as e:  # noqa: BLE001
    result["verdict"] = "CANARY_FAIL"
    result["exception"] = fp.redact(str(e))
finally:
    if ib is not None:
        try:
            ib.disconnect()
        except Exception:  # noqa: BLE001
            pass

(OUT_DIR / "canary.json").write_text(json.dumps(result, indent=1))
print(json.dumps({"verdict": result["verdict"], "ok": result.get("ok"),
                  "n_rows": result.get("n_rows"),
                  "first_bar": result.get("first_bar"), "last_bar": result.get("last_bar"),
                  "serverVersion": result.get("connection", {}).get("serverVersion"),
                  "errors": result.get("errors")[:3] if result.get("errors") else [],
                  "exception": result.get("exception")}))
