"""Exhaustive 8-field, full-window digit-exact verification of the recomposed
staging series (dedupe winners) against live fapi klines.

For every universe symbol, every scored-window bar (2025-08-21T00:00Z ->
2026-08-21T00:00Z) plus the prewindow (2025-07-22 -> window start) is compared
against live Binance data on ALL fields the loader/M01 consume: open/high/low/
close/volume (fixed-point raw ints, expected live*1e9 except PEPE/BOME volume
live*1e8), quote_volume / taker_buy_quote_volume (exact decimal strings),
trade count (exact int).
"""

from __future__ import annotations

import glob
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import pandas as pd
import pyarrow.parquet as pq
from decimal import Decimal

REPO = Path(r"C:\Users\ROYAL\my-quantitative")
STAGING = REPO / "research/control/v10r_run/staging/catalog/data/binance_bar"
OUT = REPO / "research/control/v10r_run/host3_full_window_8field_report.json"
START_MS = int(pd.Timestamp("2025-07-22T00:00:00Z").value // 10**6)  # prewindow start
END_MS = int(pd.Timestamp("2026-08-21T00:00:00Z").value // 10**6)  # window end
SCALE = 10**9
VOL_SCALE = {"1000PEPEUSDT": 10**8, "BOMEUSDT": 10**8}


def live_map(symbol: str) -> dict[int, list]:
    out: dict[int, list] = {}
    cur = START_MS
    while cur < END_MS:
        url = (
            f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=15m"
            f"&startTime={cur}&endTime={END_MS - 1}&limit=1500"
        )
        for attempt in range(4):
            try:
                with urlopen(url, timeout=30) as r:
                    batch = json.loads(r.read())
                break
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(2 * (attempt + 1))
        if not batch:
            break
        for k in batch:
            out[int(k[0])] = k
        cur = batch[-1][0] + 1
        if len(batch) < 1500:
            break
    return out


def staged_series(symbol: str) -> dict[int, dict]:
    files = sorted(glob.glob(str(STAGING / f"{symbol}-PERP*/*.parquet")))
    by_ts: dict[int, dict] = {}
    for path in files:  # lexically last wins, mirroring research.panel._read_bars
        t = pq.read_table(path).to_pandas()
        for i in range(len(t)):
            ts = int(t["ts_event"].iloc[i])
            open_ms = ts // 10**6 - 899_999
            by_ts[open_ms] = {
                "open": int.from_bytes(t["open"].iloc[i], "little"),
                "high": int.from_bytes(t["high"].iloc[i], "little"),
                "low": int.from_bytes(t["low"].iloc[i], "little"),
                "close": int.from_bytes(t["close"].iloc[i], "little"),
                "volume": int.from_bytes(t["volume"].iloc[i], "little"),
                "quote_volume": str(t["quote_volume"].iloc[i]),
                "count": int(t["count"].iloc[i]),
                "taker_buy_base_volume": str(t["taker_buy_base_volume"].iloc[i]),
                "taker_buy_quote_volume": str(t["taker_buy_quote_volume"].iloc[i]),
            }
    return by_ts


def main() -> int:
    sys.path.insert(0, str(REPO))
    import yaml

    cfg = yaml.safe_load((REPO / "config/research_scan_top20.yaml").read_text())
    symbols = list(cfg["market"]["symbols"])
    report = {
        "artifact": "host3_full_window_8field_report",
        "producer_role": "A1",
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "prewindow+scored window, dedupe winners, all consumed fields",
        "per_symbol": {},
        "failures": [],
    }
    for sym in symbols:
        live = live_map(sym)
        staged_full = staged_series(sym)
        vs = VOL_SCALE.get(sym, SCALE)
        staged = {t: r for t, r in staged_full.items() if START_MS <= t < END_MS}
        mism = []
        missing = sorted(set(live) - set(staged))
        extra = sorted(set(staged) - set(live))
        for open_ms, k in live.items():
            row = staged.get(open_ms)
            if row is None:
                continue
            # exact decimal arithmetic: float64 loses integer precision above
            # 2**53 (XRP-class volumes x1e9), so expected raw ints are built
            # from the API's own decimal STRINGS, never via float
            checks = [
                row["open"] == int(Decimal(k[1]) * SCALE),
                row["high"] == int(Decimal(k[2]) * SCALE),
                row["low"] == int(Decimal(k[3]) * SCALE),
                row["close"] == int(Decimal(k[4]) * SCALE),
                row["volume"] == int(Decimal(k[5]) * vs),
                row["quote_volume"] == str(k[7]),
                row["count"] == int(k[8]),
                row["taker_buy_base_volume"] == str(k[9]),
                row["taker_buy_quote_volume"] == str(k[10]),
            ]
            if not all(checks):
                mism.append({"open_ms": open_ms, "bad_fields": [
                    n for n, ok in zip(
                        ["open", "high", "low", "close", "volume", "quote_volume",
                         "count", "taker_base", "taker_quote"], checks) if not ok
                ]})
        report["per_symbol"][sym] = {
            "live_bars": len(live), "staged_bars_in_scope": len(staged),
            "staged_bars_total": len(staged_full),
            "missing_in_staging": len(missing), "extra_in_staging": len(extra),
            "field_mismatches": len(mism),
            "mismatch_sample": mism[:3],
            "verdict": "PASS" if not mism and not missing and not extra else "FAIL",
        }
        print(f"[{report['per_symbol'][sym]['verdict']}] {sym}: live={len(live)} "
              f"staged={len(staged)} missing={len(missing)} mism={len(mism)}", flush=True)
        if mism or missing or extra:
            report["failures"].append(sym)
        (OUT).write_text(json.dumps(report, indent=1))  # incremental save
    report["summary"] = {
        "symbols_pass": sum(1 for v in report["per_symbol"].values() if v["verdict"] == "PASS"),
        "symbols_total": len(symbols),
        "all_pass": not report["failures"],
    }
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(report, indent=1))
    print("SUMMARY:", json.dumps(report["summary"]))
    return 0 if report["summary"]["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
