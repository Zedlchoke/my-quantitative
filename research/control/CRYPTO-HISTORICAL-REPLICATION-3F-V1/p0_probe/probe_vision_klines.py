#!/usr/bin/env python3
"""Light earliest-archive census for data.binance.vision um futures (read-only).
Politeness: static CDN HEAD requests, 0.35s spacing, fapi calls <=8 with 1.2s spacing."""
import json, time, urllib.request, urllib.error, datetime as dt
from pathlib import Path

OUT = Path(__file__).parent
UA = {"User-Agent": "research-p0-census/1 (read-only HEAD probes)"}
VISION = "https://data.binance.vision/data/futures/um/monthly"

def head(url):
    req = urllib.request.Request(url, headers=UA, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return f"ERR:{type(e).__name__}"

def earliest_month(sym, dataset, interval=None, months=None):
    """Coarse bracket then refine: returns first month with HTTP 200."""
    def probe(y, m):
        if dataset == "klines":
            url = f"{VISION}/klines/{sym}/{interval}/{sym}-{interval}-{y}-{m:02d}.zip"
        else:
            url = f"{VISION}/{dataset}/{sym}/{sym}-{dataset}-{y}-{m:02d}.zip"
        s = head(url); time.sleep(0.35)
        return s == 200
    # bracket by year 2019..2025 (Jan probes)
    lo = None
    for y in range(2019, 2026):
        if probe(y, 1): lo = (y, 1); break
    if lo is None: return None
    # refine within the found year.. next year boundary
    y, _ = lo
    ms = months if months else range(1, 13)
    for m in ms:
        if probe(y, m): return f"{y}-{m:02d}"
    return f"{y+1}-01"

SYMS = ["BTCUSDT","ETHUSDT","XRPUSDT","LINKUSDT","ADAUSDT","BNBUSDT","DOGEUSDT",
        "BCHUSDT","ZECUSDT","AAVEUSDT","AVAXUSDT","SOLUSDT","NEARUSDT",
        "1000PEPEUSDT","SUIUSDT","WLDUSDT","ONGUSDT","ACEUSDT","BOMEUSDT","ENAUSDT"]
res = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
       "method": "HEAD probes against static CDN; 200=archive exists; spacing 0.35s",
       "klines_15m_first_month": {}}
for s in SYMS:
    res["klines_15m_first_month"][s] = earliest_month(s, "klines", "15m")
    print(s, res["klines_15m_first_month"][s], flush=True)
# dataset-level depth questions on BTCUSDT
res["btcusdt_markPriceKlines_15m_first"] = earliest_month("BTCUSDT", "markPriceKlines", "15m")
print("markPriceKlines BTC", res["btcusdt_markPriceKlines_15m_first"], flush=True)
res["btcusdt_indexPriceKlines_15m_first"] = earliest_month("BTCUSDT", "indexPriceKlines", "15m")
print("indexPriceKlines BTC", res["btcusdt_indexPriceKlines_15m_first"], flush=True)
res["btcusdt_fundingRate_monthly_first"] = earliest_month("BTCUSDT", "fundingRate")
print("fundingRate monthly BTC", res["btcusdt_fundingRate_monthly_first"], flush=True)
res["btcusdt_daily_kline_2019_probe"] = head(f"{VISION}/klines/BTCUSDT/15m/BTCUSDT-15m-2019-12-25.zip")
(OUT / "vision_census_wave1.json").write_text(json.dumps(res, indent=1))
print("WROTE", OUT / "vision_census_wave1.json")
