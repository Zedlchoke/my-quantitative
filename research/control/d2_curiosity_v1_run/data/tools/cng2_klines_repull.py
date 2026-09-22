"""DATA-GATE lane D2-CURIOSITY-V1: CNG2-A5-P1 H1 klines re-pull (supplementary).

NOTE ON SOURCE CLASS: the pinned S4 H1 panels (pins 111c1a2d/ebd487a6/c4ca0b6e)
were built from Binance VISION monthly aggTrades, NOT from fapi klines; they
are bound separately via the CADS content-addressed store (verify-on-read
digest).  THIS script performs the dispatch-mandated fapi/v1/klines re-pull as
UPSTREAM AVAILABILITY + CONTENT CROSS-CHECK evidence only: 8,760 H1 bars per
symbol over 2025-08-22T00:00Z..2026-08-21T23:00Z (limit=1500, paginated,
1 s etiquette), row/time-grid invariants on all bars, and an all-bars price
cross-check against the CADS panel (open/high/low/close vs
first/high/low/last price; price columns are 1-decimal rounded in the panel).

NO outcome computation anywhere.
"""
from __future__ import annotations

import csv
import hashlib
import json
import time
import urllib.request
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[1] / "cng2" / "klines_repull"
CADS = Path("/Users/hoangminhlong/my-quantitative/.runtime/v3_cads_store/objects")

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
PANEL_PIN = {
    "BTCUSDT": ("11", "111c1a2d6d62e26c1874bb428c10216e4926ae37ab0102ca098849ca25f5e7b1"),
    "ETHUSDT": ("eb", "ebd487a69404a1104d9123584c93af044a2796c338185d8466599b9f34bb440b"),
    "SOLUSDT": ("c4", "c4ca0b6eb719122054abec2a03fcac20d3f7794c5bf6d3c546ee6db1cb6e2107"),
}
START_MS = 1755820800000          # 2025-08-22T00:00:00Z (first bar open)
END_MS = 1787356799000            # 2025-08-21T23:00:00Z window; last bar open = 1787353200000
LAST_OPEN_MS = 1787353200000      # 2026-08-21T23:00:00Z
EXPECTED_BARS = 8760
LIMIT = 1500
SLEEP_S = 1.0


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def get_json(url: str) -> list:
    req = urllib.request.Request(url, headers={"User-Agent": "d2-curiosity-v1-data-gate/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def pull_symbol(sym: str) -> list:
    rows = []
    cursor = START_MS
    while cursor <= LAST_OPEN_MS:
        url = (f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}"
               f"&interval=1h&startTime={cursor}&endTime={END_MS}&limit={LIMIT}")
        batch = None
        for attempt in range(3):
            try:
                batch = get_json(url)
                break
            except Exception:
                time.sleep(5.0 * (attempt + 1))
        if batch is None:
            raise RuntimeError(f"klines pull failed {sym} cursor {cursor}")
        if not batch:
            break
        rows.extend(batch)
        cursor = int(batch[-1][0]) + 3_600_000
        if int(batch[-1][0]) >= LAST_OPEN_MS:
            break
        time.sleep(SLEEP_S)
    # dedupe on open time, keep first
    seen, out = set(), []
    for r in rows:
        if r[0] not in seen:
            seen.add(r[0])
            out.append(r)
    out.sort(key=lambda r: r[0])
    return out


def panel_rows(sym: str) -> list[dict]:
    shard, digest = PANEL_PIN[sym]
    p = CADS / shard / digest
    with p.open() as f:
        return list(csv.DictReader(f))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {}
    for sym in SYMBOLS:
        rows = pull_symbol(sym)
        f = OUT_DIR / f"klines_{sym}_1h.json"
        f.write_text(json.dumps(rows, separators=(",", ":")) + "\n")
        opens = [int(r[0]) for r in rows]
        contiguous = all(b - a == 3_600_000 for a, b in zip(opens, opens[1:]))
        # all-bars price cross-check against the pinned CADS panel
        panel = panel_rows(sym)
        n = min(len(rows), len(panel))
        mism = []
        for i in range(n):
            k = rows[i]
            p = panel[i]
            if (p["hour_utc"] != time.strftime("%Y-%m-%dT%H", time.gmtime(k[0] / 1000))):
                mism.append({"i": i, "field": "hour_utc"})
                continue
            checks = [
                (p["first_price"], k[1]),   # open
                (p["high_price"], k[2]),    # high
                (p["low_price"], k[3]),     # low
                (p["last_price"], k[4]),    # close
            ]
            for field, (pv, kv) in zip(["open", "high", "low", "close"], checks):
                if abs(float(pv) - float(kv)) > 5e-9:
                    mism.append({"i": i, "field": field, "panel": pv, "kline": kv})
        summary[sym] = {
            "bars_pulled": len(rows),
            "expected_bars": EXPECTED_BARS,
            "first_open_ms": opens[0] if opens else None,
            "last_open_ms": opens[-1] if opens else None,
            "expected_span_ms": [START_MS, LAST_OPEN_MS],
            "contiguous_hourly": contiguous,
            "panel_rows": len(panel),
            "price_mismatches_vs_panel": len(mism),
            "price_mismatch_head": mism[:5],
            "klines_sha256": sha256_file(f),
        }
        print(sym, json.dumps(summary[sym]))
        time.sleep(SLEEP_S)
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
