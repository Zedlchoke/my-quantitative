#!/usr/bin/env python
"""Addendum acquisition (entitled, zero-cost) for PC12A-7ASSET-DATA-UNBLOCK.

1) EIA v2 API (owner key EIA_API_KEY in .env, FREE-DATA-FRONTIER precedent):
   official daily spot RWTCL (WTI Cushing), RNGWHHD (Henry Hub), RBRTE (Brent)
   from the PRIMARY source - supersedes the FRED-mirror provenance for numbers.
2) EODHD (owner key EODHD_API_KEY, stocks-cycles precedent /api/eod/):
   SLV.US + GLD.US daily closes as exchange-traded PROXY archives for silver/
   gold spot cross-checks (TwelveData XAG/USD is plan-blocked: Grow/Venture
   only - no purchase permitted this session).

Keys are read from .env inside the process and never echoed into logs or the
manifest (urls recorded with [REDACTED]).
Appends to MANIFEST_RAW.json (same schema) in a separate 'addendum_files' list.
"""
from __future__ import annotations
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/pc12a-7asset-unblock-20261001")
CTL = WT / "research/control/PC12A-7ASSET-DATA-UNBLOCK-2026-10-01"
RAW = Path.home() / ".my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/raw"
now = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

env = {}
for line in Path("/Users/hoangminhlong/my-quantitative/.env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")


def curl_get(url: str, timeout: int = 90) -> tuple[int, bytes]:
    # EIA api.eia.gov proved reachable via curl; python-requests TLS is filtered
    # on some CDNs this session - use curl default UA uniformly.
    cp = subprocess.run(["curl", "-sS", "-g", "--http1.1", "-L", "--max-time", str(timeout),
                         "-w", "\n%{http_code}", url], capture_output=True)
    body, _, code = cp.stdout.rpartition(b"\n")
    return int(code or 0), body


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


rows = []

# ------------------------------------------------------------- EIA v2 API ---
# v2 route corrections measured this session: petroleum/spt invalid ->
# petroleum/pri/spt; WTI series id is RWTC (not RWTCL); Henry Hub lives under
# natural-gas/pri/fut (futures after 2024-04-05 unavailable there, spot full).
EIA_SERIES = {
    ("petroleum/pri/spt", "RWTC"): "Cushing OK WTI spot price FOB, USD/bbl, daily (official primary source; v2 id RWTC)",
    ("natural-gas/pri/fut", "RNGWHHD"): "Henry Hub natural gas spot price, USD/MMBtu, daily (official primary source)",
    ("petroleum/pri/spt", "RBRTE"): "Europe Brent spot price FOB, USD/bbl, daily (official primary source)",
}
for (route, series), desc in EIA_SERIES.items():
    pages = []
    offset = 0
    while True:
        url = (f"https://api.eia.gov/v2/{route}/data/"
               f"?api_key={env['EIA_API_KEY']}&frequency=daily&data[0]=value"
               f"&facets[series][]={series}&start=2019-01-01&length=5000&offset={offset}"
               "&sort[0][column]=period&sort[0][direction]=asc")
        code, body = curl_get(url)
        if code != 200:
            # never print stderr/url: keyed URLs echo credentials on curl errors (INC-1)
            print(f"EIA {series} page FAIL http={code} bytes={len(body)}")
            pages = None
            break
        j = json.loads(body)
        data = j["response"]["data"]
        pages.extend(data)
        total = int(j["response"]["total"])
        offset += len(data)
        if offset >= total or not data:
            break
        time.sleep(3)
    if pages is None:
        continue
    payload = json.dumps({"series": series, "retrieved_at_utc": now(),
                          "n_rows": len(pages), "rows": pages},
                         separators=(",", ":")).encode()
    p = RAW / f"eia_v2_{series}_daily.json"
    p.write_bytes(payload)
    rows.append({
        "file": p.name, "path": str(p),
        "url": f"https://api.eia.gov/v2/{route}/data/?api_key=[REDACTED]&frequency=daily&facets[series][]={series}&start=2019-01-01",
        "retrieved_at_utc": now(), "bytes": len(payload), "sha256": sha(payload),
        "http_status": 200,
        "license_note": "EIA API: U.S. Government open data; key is owner-provided in .env (FREE-DATA-FRONTIER-V1 precedent)",
        "authority_status": "DOCUMENTED_CANDIDATE",
        "note": desc + f"; n_rows={len(pages)}",
    })
    print(f"LANDED {p.name}: {len(pages)} rows sha={sha(payload)[:12]}...")
    time.sleep(5)

# ------------------------------------------------------------------ EODHD ---
for ticker, metal in [("SLV.US", "silver"), ("GLD.US", "gold")]:
    url = (f"https://eodhd.com/api/eod/{ticker}"
           f"?api_token={env['EODHD_API_KEY']}&period=d&order=d&fmt=json")
    code, body = curl_get(url)
    if code != 200:
        print(f"EODHD {ticker} FAIL http={code} bytes={len(body)}")
        continue
    n = len(json.loads(body))
    p = RAW / f"eodhd_{ticker.replace('.', '_')}_eod.json"
    p.write_bytes(body)
    rows.append({
        "file": p.name, "path": str(p),
        "url": f"https://eodhd.com/api/eod/{ticker}?api_token=[REDACTED]&period=d&order=d&fmt=json",
        "retrieved_at_utc": now(), "bytes": len(body), "sha256": sha(body),
        "http_status": 200,
        "license_note": "EODHD under owner entitlement (stocks cycles precedent, /api/eod/ channel verified alive STOCKS-NG3/NG6); key never echoed",
        "authority_status": "CANDIDATE_NOT_AUTHORIZED",
        "note": f"{metal} spot PROXY via US-listed ETF close (exchange-traded wrapper; NAV tracking + NYSE close vs London spot = structural basis); n={n} rows; NOT spot itself",
    })
    print(f"LANDED {p.name}: {n} rows sha={sha(body)[:12]}...")
    time.sleep(5)

man_path = CTL / "MANIFEST_RAW.json"
man = json.loads(man_path.read_text())
man["addendum_files"] = rows
man["addendum_note"] = ("entitled zero-cost addendum after TwelveData XAG/USD "
                        "plan-block (Grow/Venture only; no purchase permitted): "
                        "EIA v2 primary-source energy dailies + EODHD ETF proxies")
man_path.write_text(json.dumps(man, indent=1))
print(f"\nMANIFEST updated: {len(rows)} addendum files, {len(man['files']) + len(rows)} total")
