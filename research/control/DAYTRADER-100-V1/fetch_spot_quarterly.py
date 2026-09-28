"""DT100 addendum fetch: Binance SPOT 1m + quarterly-delivery futures 1m (BTC).

Unlocked by owner order 2026-09-28 after the keyless channel was proven
(288/288 premium+funding). Quarterly symbols = last-Friday of Mar/Jun/Sep/Dec;
misses recorded (delisted/unlisted quarters are expected).
"""
from __future__ import annotations

import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

BASE = Path("/Users/hoangminhlong/my-quantitative/.worktrees/daytrader-100-v1/integration/research/control/DAYTRADER-100-V1/data_staging")


def last_friday(y: int, m: int) -> date:
    d = date(y, m, 1)
    nxt = date(y + (m == 12), (m % 12) + 1, 1)
    d = nxt - timedelta(days=1)
    while d.weekday() != 4:
        d -= timedelta(days=1)
    return d


def fetch(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "dt100-staging/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            blob = r.read()
        if not blob:
            return False
        dest.write_bytes(blob)
        return True
    except Exception:
        return False


ok = miss = 0
# SPOT 1m BTCUSDT 2020-09..2026-08
spot_dir = BASE / "spot" / "BTCUSDT"
spot_dir.mkdir(parents=True, exist_ok=True)
for y in range(2020, 2027):
    for mth in range(1, 13):
        if (y, mth) < (2020, 9) or (y, mth) > (2026, 8):
            continue
        url = f"https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-{y}-{mth:02d}.zip"
        if fetch(url, spot_dir / f"BTCUSDT-spot-{y}-{mth:02d}.zip"):
            ok += 1
            time.sleep(0.2)
        else:
            miss += 1

# QUARTERLY futures 1m: continuous chain of last-Friday contracts
q_dir = BASE / "quarterly" / "BTCUSDT"
q_dir.mkdir(parents=True, exist_ok=True)
quarters = []
for y in range(2020, 2027):
    for mth in (3, 6, 9, 12):
        d = last_friday(y, mth)
        if date(2020, 9, 1) <= d <= date(2026, 6, 30):
            quarters.append(d)
for d in quarters:
    sym = f"BTCUSDT_{d.strftime('%y%m%d')}"
    # months where this contract was the active quarter: expiry-12m .. expiry
    for t in range(12):
        y = d.year if (d.month - t) > 0 else d.year - 1
        mth = (d.month - t - 1) % 12 + 1
        url = f"https://data.binance.vision/data/futures/um/monthly/klines/{sym}/1m/{sym}-1m-{y}-{mth:02d}.zip"
        if fetch(url, q_dir / f"{sym}-1m-{y}-{mth:02d}.zip"):
            ok += 1
            time.sleep(0.2)
        else:
            miss += 1
print(f"DONE ok={ok} miss={miss}")
