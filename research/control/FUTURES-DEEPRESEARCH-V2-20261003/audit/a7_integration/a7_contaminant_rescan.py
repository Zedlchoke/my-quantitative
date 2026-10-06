#!/usr/bin/env python3
"""A7-INTEGRATION audit script 2: independent full rescan of the six roots'
vendor ohlcv-1m parquet, reproducing contaminant_scan.py's measurement with an
auditor-written classifier, plus a FULL distinct raw_symbol census per root to
adjudicate the canonical regex ^{ROOT}[FGHJKMNQUVXZ][0-9]$ against every
observed symbol (wrong exclusions/inclusions, decade-wrap years, etc.).
READ-ONLY. Writes only under audit/a7_integration/.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

PQ_ROOT = Path("/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet")
HERE = Path(__file__).resolve().parent

ROOT_DIRS = {
    "NQ": ["AV1T-O1M-NQ", "AV1R-O1M-NQ-DELTA"],
    "ES": ["AV1T-O1M-ES", "AV1R-O1M-ES-DELTA"],
    "6E": ["AV1T-O1M-6E", "AV1R-O1M-6E-BACKFILL", "AV1B-O1M-6E-BACKFILL2"],
    "6J": ["AV1T-O1M-6J", "AV1R-O1M-6J-BACKFILL", "AV1B-O1M-6J-BACKFILL2"],
    "6B": ["AV1T-O1M-6B", "AV1R-O1M-6B-BACKFILL", "AV1B-O1M-6B-BACKFILL2"],
    "6A": ["AV1T-O1M-6A", "AV1R-O1M-6A-BACKFILL", "AV1B-O1M-6A-BACKFILL2"],
}
MONTHS = "FGHJKMNQUVXZ"


def classify(symbol: str, root: str) -> str:
    if re.fullmatch(rf"{re.escape(root)}[{MONTHS}][0-9]", symbol):
        return "outright_root_family"
    if "-" in symbol:
        return "spread_strip"
    if re.fullmatch(r"[A-Z0-9]{1,3}[FGHJKMNQUVXZ][0-9]", symbol):
        return "foreign_outright"
    return "other"


def main() -> None:
    results = {}
    for root, dirs in ROOT_DIRS.items():
        files = []
        for d in dirs:
            files += sorted((PQ_ROOT / d).glob("*.parquet"))
        frames = [pq.ParquetFile(f).read(columns=["raw_symbol", "volume", "ts_event"]).to_pandas()
                  for f in files]
        big = pd.concat(frames, ignore_index=True)
        big["date"] = pd.to_datetime(big["ts_event"], unit="ns", utc=True).dt.date.astype(str)
        big["cls"] = [classify(s, root) for s in big["raw_symbol"]]

        rep = {"files": [f.name for f in files], "total_rows": int(len(big)), "classes": {}}
        for cls in ("outright_root_family", "spread_strip", "foreign_outright", "other"):
            g = big[big.cls == cls]
            agg = (g.groupby("raw_symbol")
                   .agg(bars=("raw_symbol", "size"), volume=("volume", "sum"),
                        first=("date", "min"), last=("date", "max")))
            rep["classes"][cls] = {
                "bars": int(len(g)), "volume": int(g["volume"].sum()),
                "distinct_symbols": int(agg.shape[0]),
                "symbols": {s: {"bars": int(r.bars), "volume": int(r.volume),
                                "first": r.first, "last": r.last} for s, r in agg.iterrows()},
            }
        # regex audit: census of ALL distinct symbols; find (a) symbols matching
        # canonical regex, (b) non-dash symbols failing any outright pattern
        census = big.groupby("raw_symbol").size().to_dict()
        odd = {s: n for s, n in census.items()
               if "-" not in s and not re.fullmatch(r"[A-Z0-9]{1,3}[FGHJKMNQUVXZ][0-9]", s)}
        dash_nonspread_like = sorted({s for s in census if "-" in s
                                      and not re.fullmatch(r"[A-Z0-9]{1,3}[FGHJKMNQUVXZ][0-9]-[A-Z0-9]{1,3}[FGHJKMNQUVXZ][0-9]", s)})
        two_digit_year = sorted(s for s in census if re.search(r"[FGHJKMNQUVXZ][0-9]{2,}$", s))
        rep["census_distinct_total"] = len(census)
        rep["non_dash_not_outright_pattern"] = odd
        rep["dash_symbols_not_NN-NN_shape"] = dash_nonspread_like[:40]
        rep["symbols_with_multi_digit_year_tail"] = two_digit_year
        results[root] = rep
        print(f"[{root}] rows={rep['total_rows']} " +
              " ".join(f"{c}={v['bars']}" for c, v in rep["classes"].items()) +
              f" | distinct_syms={len(census)} non_outright_nodash={len(odd)} "
              f"multi_digit_year={len(two_digit_year)}")

    (HERE / "a7_contaminant_rescan.json").write_text(json.dumps(results, indent=1))
    print("wrote", HERE / "a7_contaminant_rescan.json")


if __name__ == "__main__":
    main()
