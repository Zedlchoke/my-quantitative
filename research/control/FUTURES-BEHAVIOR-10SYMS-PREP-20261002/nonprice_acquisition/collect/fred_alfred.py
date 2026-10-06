#!/usr/bin/env python
"""FRED/ALFRED collector (NONPRICE-DATA-ACQUISITION).

Route behavior MEASURED 2026-10-02:
- fred.stlouisfed.org/graph/fredgraph.csv?id=X      -> FAST, key-free, LATEST
  vintage only (revised-latest; descriptive/cross-check class).
- alfred.stlouisfed.org/graph/alfredgraph.csv       -> key-free but heavily
  rate-limited (~14s/req when warm); realtime_start/realtime_end params are
  IGNORED by this endpoint (column suffix always = today).
- alfredgraph.csv + &vintage_date=YYYY-MM-DD        -> the vintage route; it
  HANGS (>4.5 min, connection reset) under current throttling. Attempts are
  patience-bounded; failures are typed OWNER_KEY_WAIT (FRED/ALFRED API key
  route via owner) - never fabricated.
- api.stlouisfed.org without key -> HTTP 400 immediately (evidence recorded).

BLS 403 fallback: CPIAUCSL + PAYEMS latest (first prints via ALFRED vintages
are the PIT-grade route - typed with the same vintage limitation).

Usage:
  python fred_alfred.py --smoke
  python fred_alfred.py                # all latest series
  python fred_alfred.py --vintages     # + patient year-end vintage attempts (gating series)
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common

FAMILY = "fred_alfred"
SERIES = {
    "DFII10": "10y TIPS real yield (NQ-H1, GC-H5, GC-H2)",
    "DGS10": "10y nominal yield (NQ-H1, GC-H5)",
    "DGS2": "2y nominal yield (rates-repricing context)",
    "T10YIE": "10y breakeven (GC-H5, GC-H2)",
    "DTB3": "3M T-bill (ES-H2 ~3M rate, SI-H3)",
    "SOFR": "SOFR (SI-H3, 6E-H2)",
    "DFF": "effective fed funds daily (6J-H3, 6A-H5)",
    "FEDFUNDS": "effective fed funds monthly (6A-H5)",
    "DFEDTARU": "fed funds target upper (6A-H5 policy)",
    "DTWEXBGS": "broad trade-weighted USD (CL-H4; DXY itself is ICE-licensed)",
    "CPIAUCSL": "CPI NSA (BLS-403 fallback; latest = revised)",
    "PAYEMS": "total nonfarm payrolls (BLS-403 fallback; latest = revised)",
}
GATING_FOR_VINTAGE = ["DFII10", "DGS10", "T10YIE", "DTWEXBGS", "SOFR", "DFF", "DTB3",
                      "CPIAUCSL", "PAYEMS"]  # CPI/PAYEMS = BLS-403 fallback first prints


def fetch_latest(series: str) -> dict:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
    return common.http_get(url, family=FAMILY,
                           rel_path=f"fred_alfred/latest/{series}_latest.csv",
                           rate_limit_s=0.5, max_bytes=8 * 1024**2)


def fetch_vintage_attempt(series: str, date: str) -> dict:
    """One patience-bounded ALFRED vintage_date attempt (may take minutes)."""
    url = (f"https://alfred.stlouisfed.org/graph/alfredgraph.csv?id={series}"
           f"&vintage_date={date}")
    return common.http_get(url, family=FAMILY,
                           rel_path=f"fred_alfred/vintage_attempts/{series}_{date}.csv",
                           rate_limit_s=20.0, retries=1, timeout=300,
                           max_bytes=8 * 1024**2)


def peek_csv(rec: dict) -> dict:
    p = common.RAW_ROOT / rec["path"]
    try:
        rows = list(csv.reader(io.TextIOWrapper(open(p, "rb"), encoding="utf-8-sig")))
    except Exception as exc:
        return {"error": str(exc)}
    if not rows:
        return {"rows": 0}
    return {"header": rows[0][:3], "rows": len(rows) - 1,
            "first": rows[1][:2] if len(rows) > 1 else [],
            "last": rows[-1][:2]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--vintages", action="store_true")
    args = ap.parse_args()

    results = []
    if args.smoke:
        results.append(fetch_latest("DFII10"))
        print(json.dumps(peek_csv(results[-1])))
    else:
        for s in SERIES:
            results.append(fetch_latest(s))
        if args.vintages:
            # year-end PIT snapshot dates for gating series (bounded patience).
            # 404 = series start later than the date (expected; keep going);
            # only persistent non-404 failures are treated as a route problem.
            dates = [f"{y}-12-31" for y in range(2010, 2025)] + ["2026-09-30"]
            for s in GATING_FOR_VINTAGE:
                fails = 0
                for d in dates:
                    rec = fetch_vintage_attempt(s, d)
                    results.append(rec)
                    if rec.get("status") != "ok":
                        code = str(rec.get("http_status"))
                        print(f"vintage attempt not-ok for {s} at {d}: {rec.get('status')} {code}")
                        if code != "404":
                            fails += 1
                            if fails >= 2:
                                print(f"route problem for {s}; skipping rest of this series")
                                break
                    else:
                        print(f"vintage ok {s} {d}")

    ok = [r for r in results if r.get("status") == "ok"]
    er = [r for r in results if r.get("status") == "http_error"]
    ws = [r for r in results if r.get("status") == "wait_storage"]
    print(json.dumps({"ok": len(ok), "http_error": len(er), "wait_storage": len(ws),
                      "error_samples": [{"p": r["path"], "s": r.get("http_status")} for r in er[:8]],
                      "bytes": sum(int(r.get("bytes", 0)) for r in ok),
                      "summary": common.summary()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
