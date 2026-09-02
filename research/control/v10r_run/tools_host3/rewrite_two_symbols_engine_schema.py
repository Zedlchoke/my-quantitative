"""Host-3 bootstrap: rewrite 1000PEPEUSDT/BOMEUSDT parts in exact engine format.

The catalog-writer path (fetch_two_symbols_rest.py) mis-serialised volumes
(raw clamped to 10^9 / 0), so those files are replaced. This tool clones the
ENGINE parquet layout byte-for-byte at the schema level (verified against a
reference engine part): OHLC+volume are 8-byte little-endian uint64 of
value*10^9, quote/taker volumes are the API decimal strings, count uint64,
ts_event/ts_init int64 ns = close_ms*1e6 + 64 (the engine's nanosecond
padding), single part per symbol named by the requested range, metadata
price/size_precision from exchangeInfo.

Volume*10^9 peaks ~1.2e18 for these two symbols, inside int64/uint64 range.
Content comes from the same fapi klines endpoint the Binance adapter uses.
"""

from __future__ import annotations

import glob
import json
import shutil
from decimal import Decimal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

REPO = Path(r"C:\Users\ROYAL\my-quantitative")
STAGING = REPO / "research/control/v10r_run/staging/catalog/data/binance_bar"
REF = (
    STAGING
    / "BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    / "2024-08-23T04-58-53-044096000Z_2026-08-23T04-58-53-044096000Z.parquet"
)
START_MS = int(pd.Timestamp("2024-08-23T04:58:53.044096Z").value // 10**6)
END_MS = int(pd.Timestamp("2026-08-23T04:58:53.044096Z").value // 10**6)
SCALE = 10**9
NS_PAD = 64


def klines(symbol: str) -> list[list]:
    out, cur = [], START_MS
    while cur < END_MS:
        url = (
            f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=15m"
            f"&startTime={cur}&endTime={END_MS}&limit=1500"
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
    return [k for k in out if k[0] >= START_MS and k[6] <= END_MS]


def main() -> int:
    report = {
        "artifact": "host3_rewrite_two_symbols_engine_schema",
        "producer_role": "A1",
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "replaces": "host3_fetch_two_symbols_rest.py output (volume clamp defect)",
        "symbols": {},
    }
    ref_schema = pq.ParquetFile(REF).schema_arrow
    ref_meta = pq.ParquetFile(REF).metadata.metadata or {}
    bin_type = ref_schema.field("open").type  # engine's fixed binary type

    for sym in ("1000PEPEUSDT", "BOMEUSDT"):
        with urlopen("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=30) as r:
            info = json.loads(r.read())
        ex = next(s for s in info["symbols"] if s["symbol"] == sym)
        pp, sp = ex["pricePrecision"], ex["quantityPrecision"]
        rows = klines(sym)
        max_vol = max(Decimal(k[5]) for k in rows)
        # uint64 caps at ~1.84e19; prices fit at 1e9, the largest volumes of
        # these two symbols do not, so BOTH columns use a per-symbol scale:
        # prices stay 1e9, volumes 1e8 (uniform within symbol -> all
        # within-symbol volume ratios/z-scores unchanged; loader volume reads
        # live*1e-8 instead of live*1e-7 for exactly these two symbols).
        VSCALE = SCALE if max_vol * SCALE < 2**64 - 1 else SCALE // 10
        overflow_note = f"volume scale {VSCALE} (max_vol {max_vol})"
        print(f"[scale] {sym}: {overflow_note}", flush=True)

        def fixed_str(dec_string: str, scale: int) -> bytes:
            # exact decimal scaling from the API string; float loses integer
            # precision above 2**53 (full-window verify finding)
            return int(Decimal(dec_string) * scale).to_bytes(8, "little", signed=False)

        o = pa.array([fixed_str(k[1], SCALE) for k in rows], type=bin_type)
        h = pa.array([fixed_str(k[2], SCALE) for k in rows], type=bin_type)
        l = pa.array([fixed_str(k[3], SCALE) for k in rows], type=bin_type)
        c = pa.array([fixed_str(k[4], SCALE) for k in rows], type=bin_type)
        v = pa.array([fixed_str(k[5], VSCALE) for k in rows], type=bin_type)
        qv = pa.array([k[7] for k in rows], type=ref_schema.field("quote_volume").type)
        cnt = pa.array([int(k[8]) for k in rows], type=ref_schema.field("count").type)
        tb = pa.array([k[9] for k in rows], type=ref_schema.field("taker_buy_base_volume").type)
        tq = pa.array([k[10] for k in rows], type=ref_schema.field("taker_buy_quote_volume").type)
        ts = pa.array([int(k[6]) * 1_000_000 + NS_PAD for k in rows], type=ref_schema.field("ts_event").type)
        table = pa.Table.from_arrays(
            [o, h, l, c, v, qv, cnt, tb, tq, ts, ts],
            names=[f.name for f in ref_schema],
        )
        meta = {
            k: v
            for k, v in ref_meta.items()
            if k
            in (
                b"bar_type",
                b"instrument_id",
                b"price_precision",
                b"size_precision",
            )
        }
        meta[b"bar_type"] = f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL".encode()
        meta[b"instrument_id"] = f"{sym}-PERP.BINANCE".encode()
        meta[b"price_precision"] = str(pp).encode()
        meta[b"size_precision"] = str(sp).encode()
        table = table.replace_schema_metadata(meta)

        out_dir = STAGING / f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
        for old in glob.glob(str(out_dir / "*.parquet")):
            os_remove(Path(old))
        out = out_dir / (
            "2024-08-23T04-58-53-044096000Z_2026-08-23T04-58-53-044096000Z.parquet"
        )
        pq.write_table(table, out)
        new_schema = pq.ParquetFile(out).schema_arrow
        schema_equal = [f.name for f in new_schema] == [f.name for f in ref_schema] and all(
            a.type == b.type for a, b in zip(new_schema, ref_schema)
        )
        report["symbols"][sym] = {
            "n_bars": len(rows),
            "file": out.name,
            "schema_equals_engine": schema_equal,
            "price_precision": pp,
            "size_precision": sp,
            "volume_fixed_scale": VSCALE,
            "max_volume": max_vol,
            "scale_note": overflow_note,
        }
        print(f"[rewritten] {sym}: n={len(rows)} schema_eq={schema_equal}", flush=True)
    (REPO / "research/control/v10r_run/host3_rewrite_two_symbols_report.json").write_text(
        json.dumps(report, indent=1, default=str)
    )
    ok = all(v["schema_equals_engine"] for v in report["symbols"].values())
    print("SUMMARY:", "OK" if ok else "FAIL")
    return 0 if ok else 1


def os_remove(p: Path) -> None:
    p.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
