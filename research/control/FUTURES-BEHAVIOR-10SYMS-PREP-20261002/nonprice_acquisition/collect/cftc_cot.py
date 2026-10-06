#!/usr/bin/env python
"""CFTC Commitments of Traders collector (NONPRICE-DATA-ACQUISITION).

Sources (all official cftc.gov, access 2026-10-02):
- Futures-only legacy annual archives: https://www.cftc.gov/files/dea/history/deacot{YYYY}.zip
- TFF annual archives:                   https://www.cftc.gov/files/dea/history/fut_fin_txt_{YYYY}.zip
- Disaggregated annual archives:         pattern probed (dea/history, variants)
- Site documentation for market mappings: HistoricalCompressed page + SOTS/MarketCodes

PIT law encoded: positions as-of Tuesday, released Friday 15:30 ET (schedule
FACT per RESEARCH_MATRIX CoT note); legacy as-published files are not revised;
TFF/disagg compressed histories are classification-backcasts (flagged, must NOT
be treated as true vintages).

Usage:
  python cftc_cot.py --smoke     # 1 small request + verify parse + mapping check
  python cftc_cot.py             # full 2006..2026 for all three products
"""
from __future__ import annotations
import argparse
import io
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common

FAMILY = "cftc"
START_YEAR = 2006   # NQ-H2 config floor: "CoT historical archive 2006+"
END_YEAR = 2026

# Market names to verify inside the archives (CFTC "Market" strings contain
# exchange suffix; we match case-insensitively on the commodity part).
SYMBOL_MARKET_PATTERNS = {
    "NQ": ["nasdaq-100", "nasdaq100"],
    "ES": ["s&p 500", "s&p500 consolidated"],
    "CL": ["crude oil, light sweet", "light sweet crude"],
    "NG": ["natural gas"],
    "GC": ["gold"],
    "SI": ["silver"],
    "6E": ["euro fx", "eurodollar euro fx"],
    "6J": ["japanese yen"],
    "6B": ["british pound", "british pound is"],
    "6A": ["australian dollar"],
}


def fetch_legacy(year: int) -> dict:
    url = f"https://www.cftc.gov/files/dea/history/deacot{year}.zip"
    return common.http_get(url, family=FAMILY, rel_path=f"cftc/legacy_futures_only/deacot{year}.zip",
                           rate_limit_s=0.6, max_bytes=80 * 1024**2)


def fetch_tff(year: int) -> dict:
    # Official pattern (cftc.gov HistoricalCompressed page, access 2026-10-02):
    # futures-only TFF: fut_fin_txt_{YYYY}.zip for 2010+; 2006-2016 covered by the
    # historical bundle fin_fut_txt_2006_2016.zip (page label "fin_fut_txt_YYYY")
    if year >= 2010:
        url = f"https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"
        rel = f"cftc/tff/fut_fin_txt_{year}.zip"
    else:
        url = "https://www.cftc.gov/files/dea/history/fin_fut_txt_2006_2016.zip"
        rel = "cftc/tff/fin_fut_txt_2006_2016.zip"
    return common.http_get(url, family=FAMILY, rel_path=rel,
                           rate_limit_s=0.6, max_bytes=80 * 1024**2)


def fetch_disagg(year: int) -> dict:
    # Official pattern: futures-only disaggregated fut_disagg_txt_{YYYY}.zip 2010+;
    # 2006-2016 historical bundle fut_disagg_txt_hist_2006_2016.zip
    if year >= 2010:
        url = f"https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"
        rel = f"cftc/disaggregated/fut_disagg_txt_{year}.zip"
    else:
        url = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_hist_2006_2016.zip"
        rel = "cftc/disaggregated/fut_disagg_txt_hist_2006_2016.zip"
    return common.http_get(url, family=FAMILY, rel_path=rel,
                           rate_limit_s=0.6, max_bytes=80 * 1024**2)


def fetch_reference_pages() -> list[dict]:
    out = []
    for name, url in [
        ("cftc_cot_index", "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm"),
        ("cftc_cot_historical_compressed", "https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm"),
    ]:
        out.append(common.http_get(url, family=FAMILY, rel_path=f"cftc/docs/{name}.html",
                                   rate_limit_s=0.8, max_bytes=5 * 1024**2))
    return out


def peek_markets(rec: dict) -> dict:
    """Open the downloaded legacy zip, read the inner text file, list distinct
    market names matching our 10 symbols (mapping verification step)."""
    p = common.RAW_ROOT / rec["path"]
    try:
        with zipfile.ZipFile(p) as zf:
            inner = [n for n in zf.namelist() if n.lower().endswith(".txt")][0]
            with zf.open(inner) as f:
                text = io.TextIOWrapper(f, encoding="latin-1").read()
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}
    lines = text.splitlines()
    import csv as _csv
    markets = {}
    nrec = 0
    header = None
    for row in _csv.reader(io.StringIO(text)):
        if not row:
            continue
        if header is None and row[0].startswith("Market and Exchange Names"):
            header = row
            continue
        m = row[0].strip()
        markets[m] = markets.get(m, 0) + 1
        nrec += 1
    hits = {}
    low_map = {m.lower(): m for m in markets}
    for sym, pats in SYMBOL_MARKET_PATTERNS.items():
        found = []
        for pat in pats:
            for lm, orig in low_map.items():
                if pat in lm:
                    found.append(orig)
        hits[sym] = sorted(set(found))[:6]
    return {"distinct_markets": len(markets), "records": nrec,
            "symbol_market_hits": hits}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--verify-only", action="store_true",
                    help="only run mapping verification on already-downloaded files")
    args = ap.parse_args()

    if args.verify_only:
        recs = [r for r in common._IDX.values()
                if r.get("family") == FAMILY and r.get("status") == "ok"
                and "legacy_futures_only" in r.get("path", "")]
        for rec in sorted(recs, key=lambda r: r["path"])[-3:]:
            print(json.dumps(peek_markets(rec), indent=1))
        return 0

    results = {"reference": [], "legacy": [], "tff": [], "disagg": []}
    results["reference"] = fetch_reference_pages()

    if args.smoke:
        results["legacy"].append(fetch_legacy(2024))
    else:
        for y in range(START_YEAR, END_YEAR + 1):
            results["legacy"].append(fetch_legacy(y))
        for y in range(START_YEAR, END_YEAR + 1):
            results["tff"].append(fetch_tff(y))
        for y in range(START_YEAR, END_YEAR + 1):
            results["disagg"].append(fetch_disagg(y))

    # mapping verification on the newest legacy file we have
    ok_legacy = [r for r in results["legacy"] if r.get("status") == "ok"]
    if not ok_legacy:
        ok_legacy = [r for r in common._IDX.values()
                     if r.get("family") == FAMILY and r.get("status") == "ok"
                     and "legacy" in r.get("path", "")]
    if ok_legacy:
        newest = sorted(ok_legacy, key=lambda r: r["path"])[-1]
        print("market-mapping peek on", newest["path"])
        print(json.dumps(peek_markets(newest), indent=1))

    def stat(lst):
        return {"ok": sum(1 for r in lst if r.get("status") == "ok"),
                "err": sum(1 for r in lst if r.get("status") == "http_error"),
                "wait": sum(1 for r in lst if r.get("status") == "wait_storage"),
                "bytes": sum(int(r.get("bytes", 0)) for r in lst if r.get("status") == "ok")}

    print(json.dumps({"legacy": stat(results["legacy"]), "tff": stat(results["tff"]),
                      "disagg": stat(results["disagg"]),
                      "summary": common.summary()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
