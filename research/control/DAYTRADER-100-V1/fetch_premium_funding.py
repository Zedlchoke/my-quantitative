"""DT100 keyless fetch: premiumIndexKlines + fundingRate monthly zips (BTC/SOL).

Channel measured reachable this session (HTTP 200 on premium sample). Etiquette:
sequential, 1 req/file, no auth. Output -> worktree data_staging/premium|funding.
"""
from __future__ import annotations

import io
import time
import urllib.request
import zipfile
from pathlib import Path

BASE = Path("/Users/hoangminhlong/my-quantitative/.worktrees/daytrader-100-v1/integration/research/control/DAYTRADER-100-V1/data_staging")
SYMBOLS = ["BTCUSDT", "SOLUSDT"]
MONTHS = [(y, m) for y in range(2020, 2027) for m in range(1, 13)
          if (y, m) >= (2020, 9) and (y, m) <= (2026, 8)]

KINDS = {
    "premium": "https://data.binance.vision/data/futures/um/monthly/premiumIndexKlines/{sym}/1m/{sym}-1m-{y}-{m:02d}.zip",
    "funding": "https://data.binance.vision/data/futures/um/monthly/fundingRate/{sym}/{sym}-fundingRate-{y}-{m:02d}.zip",
}

ok = miss = 0
for kind, tpl in KINDS.items():
    for sym in SYMBOLS:
        outdir = BASE / kind / sym
        outdir.mkdir(parents=True, exist_ok=True)
        for y, m in MONTHS:
            dest = outdir / f"{sym}-{kind}-{y}-{m:02d}.zip"
            if dest.exists() and dest.stat().st_size > 0:
                ok += 1
                continue
            url = tpl.format(sym=sym, y=y, m=m)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "dt100-staging/1.0"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    blob = r.read()
                if not blob:
                    miss += 1
                    continue
                dest.write_bytes(blob)
                ok += 1
                time.sleep(0.2)
            except Exception as e:  # noqa: BLE001
                miss += 1
                print(f"MISS {kind} {sym} {y}-{m:02d}: {str(e)[:60]}")
print(f"DONE ok={ok} miss={miss}")
