#!/usr/bin/env python3
"""Wave 3: earliest funding settlement per symbol (endTime-paged), S3 XML dataset naming,
basis 2019 depth, klines monthly contiguity spot-check."""
import json, time, urllib.request, urllib.error, datetime as dt
from pathlib import Path
OUT = Path(__file__).parent
UA = {"User-Agent": "research-p0-census/1 (read-only probes)"}
def get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, r.read()
    except urllib.error.HTTPError as e: return e.code, b""
    except Exception as e: return f"ERR:{type(e).__name__}", b""

res = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
SYMS = ["BTCUSDT","ETHUSDT","XRPUSDT","LINKUSDT","ADAUSDT","BNBUSDT","DOGEUSDT",
        "BCHUSDT","ZECUSDT","AAVEUSDT","AVAXUSDT","SOLUSDT","NEARUSDT",
        "1000PEPEUSDT","SUIUSDT","WLDUSDT","ONGUSDT","ACEUSDT","BOMEUSDT","ENAUSDT"]
END = int(dt.datetime(2021,1,1,tzinfo=dt.timezone.utc).timestamp()*1000)
res["funding_earliest_by_symbol"] = {}
for s in SYMS:
    st, b = get(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={s}&startTime=0&endTime={END}&limit=1000")
    time.sleep(1.2)
    if st == 200 and b:
        rows = json.loads(b)
        res["funding_earliest_by_symbol"][s] = {
            "n_rows_le_2021": len(rows),
            "first_funding_time": rows[0]["fundingTime"] if rows else None,
            "first_iso": dt.datetime.fromtimestamp(rows[0]["fundingTime"]/1000, dt.timezone.utc).isoformat() if rows else None}
    else:
        res["funding_earliest_by_symbol"][s] = {"status": st, "note": "no rows <= 2021-01-01 or error"}
    print("FUND", s, res["funding_earliest_by_symbol"][s], flush=True)

# S3 XML listing to identify mark/index/funding monthly dataset naming (static S3, no fapi weight)
for ds in ("markPriceKlines", "indexPriceKlines", "fundingRate"):
    st, b = get(f"https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?list-type=2&prefix=data/futures/um/monthly/{ds}/&delimiter=/&max-keys=5")
    res[f"s3_prefix_{ds}"] = {"status": st, "body_head": b[:600].decode('utf-8','replace')}
    print("S3", ds, st, b[:200], flush=True); time.sleep(0.5)

# basis endpoint earliest probes
FAPI="https://fapi.binance.com"
def jget(u):
    st, b = get(u); time.sleep(1.3)
    try: return st, json.loads(b)
    except Exception: return st, []
ms = lambda y,m,d: int(dt.datetime(y,m,d,tzinfo=dt.timezone.utc).timestamp()*1000)
st, b = jget(f"{FAPI}/futures/data/basis?pair=BTCUSDT&contractType=PERPETUAL&period=15m&startTime={ms(2019,11,25)}&endTime={ms(2019,11,26)}&limit=3")
res["basis_btcusdt_20191125"] = {"status": st, "n": len(b) if isinstance(b,list) else 0, "first": b[0] if isinstance(b,list) and b else None}
st, b = jget(f"{FAPI}/futures/data/basis?pair=SOLUSDT&contractType=PERPETUAL&period=15m&startTime={ms(2020,10,1)}&endTime={ms(2020,10,2)}&limit=3")
res["basis_solusdt_20201001"] = {"status": st, "n": len(b) if isinstance(b,list) else 0, "first": b[0] if isinstance(b,list) and b else None}
print("basis probes done", flush=True)
# klines monthly contiguity spot check (BTCUSDT 15m): 4 months across years
res["btcusdt_klines_month_spot"] = {}
for y,m in ((2020,6),(2021,12),(2023,6),(2024,7)):
    st = get(f"https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/15m/BTCUSDT-15m-{y}-{m:02d}.zip", timeout=15)[0]
    res["btcusdt_klines_month_spot"][f"{y}-{m:02d}"] = st
    time.sleep(0.4)
(OUT/"vision_fapi_wave3.json").write_text(json.dumps(res, indent=1))
print("WROTE wave3")
