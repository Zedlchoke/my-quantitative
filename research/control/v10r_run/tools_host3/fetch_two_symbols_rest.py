"""Host-3 bootstrap: REST+writer path for the two overflow symbols.

1000PEPEUSDT / BOMEUSDT crash nautilus 1.230.0 AND 1.231.0 request_bars
("invalid raw quantity value exceeds max", volume parsed at fixed precision 9
overflows u64 for 15m volumes > 1.84e10 tokens). These are 2 of 20
preregistered panel symbols, so the set cannot be reduced (PLAN §7/§8).

This tool fetches the same fapi klines endpoint the Binance adapter itself
uses (public, paginated) and writes bars through nautilus's own catalog
writer API (ParquetDataCatalog.write_data with BinanceBar), matching the
engine's serialisation: Price at exchangeInfo pricePrecision, Quantity at
quantityPrecision, Decimals for quote/taker fields, ts_event/ts_init = kline
close time in ns. Inclusion rule mirrors the engine (complete bars only:
open >= start AND close <= end) and is cross-checked against a same-range
symbol that fetched normally (AAVEUSDT, identical baseline name-range).

Deviation is recorded in the host-3 report; content is verified digit-exact
against live klines by verify_staging_content.py and shape-checked against
D2's recorded numbers.
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.request import urlopen

sys.path.insert(0, r"C:\Users\ROYAL\my-quantitative")

import pyarrow.parquet as pq
from nautilus_trader.adapters.binance.common.types import BinanceBar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.persistence.catalog import ParquetDataCatalog

REPO = Path(r"C:\Users\ROYAL\my-quantitative")
STAGING = REPO / "research/control/v10r_run/staging/catalog/data/binance_bar"
BOOT = Path(r"C:\Users\ROYAL\v10r_host3_bootstrap")
# request range replicated from the baseline manifest filename for the
# single-part symbols (2024-08-23T04:58:53.044096Z -> 2026-08-23T...)
_START = "2024-08-23T04:58:53.044096Z"
_END = "2026-08-23T04:58:53.044096Z"
import pandas as pd  # noqa: E402

START_MS = int(pd.Timestamp(_START).value // 10**6)
END_MS = int(pd.Timestamp(_END).value // 10**6)
SYM_PREC = {}  # symbol -> (price_precision, size_precision)


def exchange_precision(symbol: str) -> tuple[int, int]:
    if symbol in SYM_PREC:
        return SYM_PREC[symbol]
    with urlopen("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=30) as r:
        info = json.loads(r.read())
    for s in info["symbols"]:
        if s["symbol"] == symbol:
            SYM_PREC[symbol] = (s["pricePrecision"], s["quantityPrecision"])
            return SYM_PREC[symbol]
    raise RuntimeError(f"symbol {symbol} not in exchangeInfo")


def klines(symbol: str, start_ms: int, end_ms: int) -> list[list]:
    out: list[list] = []
    cur = start_ms
    while cur < end_ms:
        url = (
            f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=15m"
            f"&startTime={cur}&endTime={end_ms}&limit=1500"
        )
        for attempt in range(3):
            try:
                with urlopen(url, timeout=30) as r:
                    batch = json.loads(r.read())
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
        if not batch:
            break
        out.extend(batch)
        cur = batch[-1][0] + 1
        if len(batch) < 1500:
            break
    # engine semantics: complete bars only, within [start, end]
    return [k for k in out if k[0] >= start_ms and k[6] <= end_ms]


def main() -> int:
    report = {
        "artifact": "host3_fetch_two_symbols_rest",
        "producer_role": "A1",
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "reason": "request_bars u64 volume overflow on 1000PEPEUSDT/BOMEUSDT "
        "(nautilus 1.230.0 and 1.231.0 identical); fapi klines + nautilus "
        "catalog writer used so the preregistered 20-symbol set stays intact",
        "symbols": {},
    }
    for sym in ("1000PEPEUSDT", "BOMEUSDT"):
        pp, sp = exchange_precision(sym)
        bt = BarType.from_str(f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL")
        rows = klines(sym, START_MS, END_MS)
        work = BOOT / f"writer_{sym}"
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True)
        catalog = ParquetDataCatalog(path=str(work))
        bars = [
            BinanceBar(
                bar_type=bt,
                open=Price(Decimal(k[1]), precision=pp),
                high=Price(Decimal(k[2]), precision=pp),
                low=Price(Decimal(k[3]), precision=pp),
                close=Price(Decimal(k[4]), precision=pp),
                # volume exceeds the Python-level Quantity value cap, so write
                # via from_raw (raw = value * 10^precision, still far below the
                # u64 storage bound) — exactly what the old host's stack stored
                volume=Quantity.from_raw(
                    int(Decimal(k[5]).scaleb(sp)), sp
                ),
                quote_volume=Decimal(k[7]),
                count=int(k[8]),
                taker_buy_base_volume=Decimal(k[9]),
                taker_buy_quote_volume=Decimal(k[10]),
                ts_event=int(k[6]) * 1_000_000,
                ts_init=int(k[6]) * 1_000_000,
            )
            for k in rows
        ]
        for i in range(0, len(bars), 5000):
            catalog.write_data(bars[i : i + 5000])
        written = sorted((work / "data/binance_bar").glob("*/*.parquet"))
        if not written:
            report["symbols"][sym] = {
                "status": "UNAVAILABLE_FAIL_CLOSED",
                "files": [],
            }
            continue
        n_rows = 0
        first_ts = last_ts = None
        for src in written:
            dst = STAGING / f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL" / src.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            t = pq.read_table(dst, columns=["ts_event"])
            n_rows += t.num_rows
            f_ts = int(t["ts_event"][0]) / 1e9
            l_ts = int(t["ts_event"][-1]) / 1e9
            first_ts = f_ts if first_ts is None else min(first_ts, f_ts)
            last_ts = l_ts if last_ts is None else max(last_ts, l_ts)
        report["symbols"][sym] = {
            "status": "written",
            "n_bars": len(bars),
            "n_parts_written": len(written),
            "n_rows_staged": n_rows,
            "price_precision": pp,
            "size_precision": sp,
            "first_ts_utc": datetime.fromtimestamp(first_ts, tz=timezone.utc).isoformat(),
            "last_ts_utc": datetime.fromtimestamp(last_ts, tz=timezone.utc).isoformat(),
        }
        print(f"[written] {sym}: n={len(bars)} parts={len(written)} pp={pp} sp={sp}", flush=True)
    (REPO / "research/control/v10r_run/host3_fetch_two_symbols_rest_report.json").write_text(
        json.dumps(report, indent=1)
    )
    ok = all(v.get("status") == "written" for v in report["symbols"].values())
    print("SUMMARY:", "OK" if ok else "FAIL_CLOSED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
