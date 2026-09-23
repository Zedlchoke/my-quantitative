#!/usr/bin/env python3
"""Wave 2: corrected mid-year refinement + proper mark/index kline paths + fapi REST depth probes."""
import json, time, urllib.request, urllib.error, datetime as dt
from pathlib import Path

OUT = Path(__file__).parent
UA = {"User-Agent": "research-p0-census/1 (read-only probes)"}
VISION = "https://data.binance.vision/data/futures/um/monthly"

def get(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return f"ERR:{type(e).__name__}", b""

def head(url):
    s, _ = get(url, timeout=15)
    return s

def probe_kl(sym, ds, itv, y, m):
    if ds == "klines":
        url = f"{VISION}/klines/{sym}/{itv}/{sym}-{itv}-{y}-{m:02d}.zip"
    else:
        url = f"{VISION}/{ds}/{sym}/{itv}/{sym}-{ds}-{itv}-{y}-{m:02d}.zip"
    s = head(url); time.sleep(0.35); return s == 200

def earliest(sym, ds="klines", itv="15m"):
    hit = None; y = None
    for yy in range(2019, 2026):
        if probe_kl(sym, ds, itv, yy, 1): y = yy; break
    if y is None: return None
    for mm in range(2, 13):
        if probe_kl(sym, ds, itv, y - 1, mm): return f"{y-1}-{mm:02d}"
    for mm in range(1, 13):
        if probe_kl(sym, ds, itv, y, mm): return f"{y}-{mm:02d}"
    return None

SYMS = ["BTCUSDT","ETHUSDT","XRPUSDT","LINKUSDT","ADAUSDT","BNBUSDT","DOGEUSDT",
        "BCHUSDT","ZECUSDT","AAVEUSDT","AVAXUSDT","SOLUSDT","NEARUSDT",
        "1000PEPEUSDT","SUIUSDT","WLDUSDT","ONGUSDT","ACEUSDT","BOMEUSDT","ENAUSDT"]
res = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
       "wave1_note": "wave1 bracketed at January granularity; wave2 refines mid-year listing months",
       "klines_15m_first_month_v2": {}}
for s in SYMS:
    r = earliest(s, "klines", "15m")
    res["klines_15m_first_month_v2"][s] = r
    print("KL", s, r, flush=True)
res["btcusdt_markPriceKlines_15m_first_v2"] = earliest("BTCUSDT", "markPriceKlines", "15m")
print("mark BTC", res["btcusdt_markPriceKlines_15m_first_v2"], flush=True)
res["btcusdt_indexPriceKlines_15m_first_v2"] = earliest("BTCUSDT", "indexPriceKlines", "15m")
print("idx BTC", res["btcusdt_indexPriceKlines_15m_first_v2"], flush=True)
# dataset depth on one late symbol to see whether mark/index families track klines depth
res["solusdt_markPriceKlines_15m_first_v2"] = earliest("SOLUSDT", "markPriceKlines", "15m")
print("mark SOL", res["solusdt_markPriceKlines_15m_first_v2"], flush=True)
res["solusdt_indexPriceKlines_15m_first_v2"] = earliest("SOLUSDT", "indexPriceKlines", "15m")
print("idx SOL", res["solusdt_indexPriceKlines_15m_first_v2"], flush=True)
res["btcusdt_fundingRate_monthly_first"] = earliest("BTCUSDT", "fundingRate", "15m")
print("funding monthly BTC", res["btcusdt_fundingRate_monthly_first"], flush=True)
(OUT / "vision_census_wave2.json").write_text(json.dumps(res, indent=1))
print("WROTE wave2 vision", flush=True)

# ---- fapi REST depth probes (8 calls, spaced) ----
FAPI = "https://fapi.binance.com"
def jget(url):
    s, b = get(url, timeout=20); time.sleep(1.3)
    try: return s, json.loads(b)
    except Exception: return s, b[:200].decode("utf-8", "replace")
fres = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
ms = lambda y,m,d: int(dt.datetime(y,m,d,tzinfo=dt.timezone.utc).timestamp()*1000)
s, b = jget(f"{FAPI}/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=0&limit=3")
fres["funding_btcusdt_earliest"] = {"status": s, "rows": b if isinstance(b, list) else str(b)[:300]}
s, b = jget(f"{FAPI}/fapi/v1/fundingRate?symbol=SOLUSDT&startTime=0&limit=3")
fres["funding_solusdt_earliest"] = {"status": s, "rows": b if isinstance(b, list) else str(b)[:300]}
s, b = jget(f"{FAPI}/fapi/v1/klines?symbol=BTCUSDT&interval=15m&startTime={ms(2019,9,9)}&endTime={ms(2019,9,10)}&limit=3")
fres["klines_btcusdt_20190909"] = {"status": s, "n": len(b) if isinstance(b, list) else 0, "first": b[0][:6] if isinstance(b, list) and b else None}
s, b = jget(f"{FAPI}/futures/data/basis?pair=BTCUSDT&contractType=PERPETUAL&period=15m&startTime={ms(2020,6,1)}&endTime={ms(2020,6,2)}&limit=5")
fres["basis_btcusdt_20200601"] = {"status": s, "n": len(b) if isinstance(b, list) else 0, "first": b[0] if isinstance(b, list) and b else None}
s, b = jget(f"{FAPI}/futures/data/basis?pair=BTCUSDT&contractType=PERPETUAL&period=15m&startTime={ms(2024,8,22)}&endTime={ms(2024,8,23)}&limit=5")
fres["basis_btcusdt_20240822"] = {"status": s, "n": len(b) if isinstance(b, list) else 0, "first": b[0] if isinstance(b, list) and b else None}
s, b = jget(f"{FAPI}/fapi/v1/indexPriceKlines?pair=BTCUSDT&interval=15m&startTime={ms(2020,6,1)}&endTime={ms(2020,6,2)}&limit=3")
fres["indexPriceKlines_btcusdt_20200601"] = {"status": s, "n": len(b) if isinstance(b, list) else 0, "first": b[0][:6] if isinstance(b, list) and b else None}
s, b = jget(f"{FAPI}/fapi/v1/exchangeInfo")
if isinstance(b, dict):
    want = set(SYMS)
    fres["exchangeInfo_onboard"] = {x["symbol"]: x.get("onboardDate") for x in b.get("symbols", []) if x["symbol"] in want}
    fres["exchangeInfo_note"] = "onboardDate is CURRENT metadata (not PIT); archive census is the measured PIT proxy"
else:
    fres["exchangeInfo_onboard"] = f"status {s}"
print("fapi probes done", flush=True)
(OUT / "fapi_depth_probe.json").write_text(json.dumps(fres, indent=1))
print("WROTE fapi_depth_probe.json")
