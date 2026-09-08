"""V8 P0a leg 3b: OHLC/volume/date integrity scan over the staged EODHD
panel pull (G6 style, full panel). Fail-closed: any violation is listed;
the scan never repairs.

Checks per symbol file (RAW series):
  high >= low; high >= open, close >= low; close within [low, high]
  volume >= 0; dates strictly ascending; no duplicate dates
Adjusted series continuity is NOT re-derived here (probe G4 evidence +
corporate-actions module cover it; scoring uses RAW primary).

Usage:
  python -m research.assets.stocks.p0a_v8_integrity_scan scan
"""

import json
import os

RAW_DIR = ".staging_prices_v8/eod"
OUT = "research/control/stocks_free_v8_run/p0a_integrity_scan.json"


def scan():
    per_symbol = {}
    total_bars = 0
    total_violations = 0
    for fn in sorted(os.listdir(RAW_DIR)):
        if not fn.endswith(".json"):
            continue
        bars = json.load(open(f"{RAW_DIR}/{fn}"))
        violations = []
        prev_date = None
        for i, b in enumerate(bars):
            total_bars += 1
            o, h, l, c, v = b["open"], b["high"], b["low"], b["close"], b["volume"]
            d = b["date"]
            if h < l:
                violations.append([d, "high_lt_low"])
            if h < o or h < c or l > o or l > c:
                violations.append([d, "oc_outside_hl"])
            if v is None or v < 0:
                violations.append([d, "negative_volume"])
            if prev_date is not None and d <= prev_date:
                violations.append([d, "date_order"])
            prev_date = d
        if violations:
            per_symbol[fn] = violations
            total_violations += len(violations)
    art = {
        "schema": "stocks_free_v8_run/p0a_integrity_scan@1",
        "files_scanned": len([f for f in os.listdir(RAW_DIR) if f.endswith(".json")]),
        "bars_scanned": total_bars,
        "violations_total": total_violations,
        "violating_symbols": per_symbol if per_symbol else {},
        "checks": "high>=low; O/C within [L,H]; volume>=0; strict date order (RAW series)",
        "verdict": "PASS" if total_violations == 0 else "FAIL",
    }
    json.dump(art, open(OUT, "w"), indent=1)
    print(json.dumps({k: art[k] for k in ("files_scanned", "bars_scanned", "violations_total", "verdict")}))


if __name__ == "__main__":
    scan()
