#!/usr/bin/env python
"""DTP-CX-SOLUSDT-C1 data gate T2a — HEAD probe of Binance Vision archives.

Polite keyless probe (HEAD, ~0.4s spacing) of monthly zips for
klines 1m/15m, markPriceKlines 1m, indexPriceKlines 1m over 2020-09..2026-08,
plus 3 aggTrades sample months (2024-01, 2025-06, 2026-06) for feasibility.
No bytes downloaded (except trivial HTTP headers).
"""
import json, os, time
import requests

OUT = ("/Users/hoangminhlong/my-quantitative/.worktrees/dtp-cx-solusdt-c1/"
       "integration/research/control/DTP-CX-SOLUSDT-C1/data_gate/"
       "C1_machine_VISION_PROBE_SOLUSDT.json")
BASE = "https://data.binance.vision/data/futures/um/monthly"
UA = {"User-Agent": "dtp-cx-solusdt-c1-data-gate/1.0 (research, keyless public archives)"}

def months():
    out = []
    for y in range(2020, 2027):
        for m in range(1, 13):
            tag = f"{y}-{m:02d}"
            if "2020-09" <= tag <= "2026-08":
                out.append(tag)
    return out

def head(url):
    for attempt in range(3):
        try:
            r = requests.head(url, headers=UA, timeout=30, allow_redirects=True)
            return {"url": url, "status": r.status_code,
                    "content_length": int(r.headers.get("Content-Length") or -1),
                    "last_modified": r.headers.get("Last-Modified")}
        except Exception as e:
            if attempt == 2:
                return {"url": url, "status": -1, "error": repr(e),
                        "content_length": -1, "last_modified": None}
            time.sleep(2.0 * (attempt + 1))

def main():
    probes = {}
    probes["aggTrades"] = []
    for tag in ["2024-01", "2025-06", "2026-06"]:
        probes["aggTrades"].append(head(f"{BASE}/aggTrades/SOLUSDT/SOLUSDT-aggTrades-{tag}.zip"))
        time.sleep(0.4)
    for ds, fname, freq in [
        ("klines_1m", "klines", "1m"),
        ("klines_15m", "klines", "15m"),
        ("markPriceKlines_1m", "markPriceKlines", "1m"),
        ("indexPriceKlines_1m", "indexPriceKlines", "1m"),
    ]:
        rows = []
        for tag in months():
            url = f"{BASE}/{fname}/SOLUSDT/{freq}/SOLUSDT-{freq}-{tag}.zip"
            rows.append(head(url))
            time.sleep(0.4)
        probes[ds] = rows
        ok = sum(1 for r in rows if r["status"] == 200)
        total = sum(r["content_length"] for r in rows if r["status"] == 200)
        print(f"{ds}: {ok}/{len(rows)} HTTP200, total {total/1e6:.1f} MB", flush=True)
    ok3 = sum(1 for r in probes["aggTrades"] if r["status"] == 200)
    tot3 = sum(r["content_length"] for r in probes["aggTrades"] if r["status"] == 200)
    print(f"aggTrades samples: {ok3}/3 HTTP200, total {tot3/1e6:.1f} MB", flush=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"schema": "dtp/dg_vision_probe@1",
                   "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "base": BASE, "probes": probes}, fh, indent=1)

if __name__ == "__main__":
    main()
