#!/usr/bin/env python3
"""contaminant_scan.py — cross-root contaminant scan over vendor ohlcv-1m parquet.

Lane INTEGRATION-FIX-V2 (task FUTURES-DEEPRESEARCH-V2-20261003), 2026-10-03.

Motivation (sibling-lane findings): DEEP-6A found 1,584 '6BU5' bars inside the
6A vendor response; DEEP-6E found '6JZ7' (4,831) + 'SIJ5' (1,869) strays and
calendar-spread instrument rows; DEEP-6B quarantined 'GCQ4' gold prints. This
scan measures the SAME defect classes across ALL six roots' full vendor panel
(every line dir owned by that root: AV1T original + AV1R delta/backfill +
AV1B backfill2), read-only.

Classification of every bar by raw_symbol:
  - outright_root_family : ^{ROOT}[FGHJKMNQUVXZ][0-9]$  (the canonical filter)
  - spread_strip         : contains '-' (calendar spreads; any dash instrument)
  - foreign_outright     : matches ^[A-Z0-9]{2,}[FGHJKMNQUVXZ][0-9]$ outright
                           pattern but root prefix != this root's family
                           (e.g. 6BU5 inside 6A, 6JZ7 inside 6E)
  - other                : anything else (documented, counted)

Vendor parquet/raw is IMMUTABLE — no rewrites. The output is a documented VIEW
RULE: downstream consumers must filter raw_symbol by the per-root canonical
regex before any per-contract analysis.

Outputs: contaminant_scan.json + contaminant_scan.md (same directory).
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

# every ohlcv-1m line dir per root (definitions/statistics excluded: different
# schema, no bars)
ROOT_DIRS = {
    "NQ": ["AV1T-O1M-NQ", "AV1R-O1M-NQ-DELTA"],
    "ES": ["AV1T-O1M-ES", "AV1R-O1M-ES-DELTA"],
    "6E": ["AV1T-O1M-6E", "AV1R-O1M-6E-BACKFILL", "AV1B-O1M-6E-BACKFILL2"],
    "6J": ["AV1T-O1M-6J", "AV1R-O1M-6J-BACKFILL", "AV1B-O1M-6J-BACKFILL2"],
    "6B": ["AV1T-O1M-6B", "AV1R-O1M-6B-BACKFILL", "AV1B-O1M-6B-BACKFILL2"],
    "6A": ["AV1T-O1M-6A", "AV1R-O1M-6A-BACKFILL", "AV1B-O1M-6A-BACKFILL2"],
}

MONTH_CODES = "FGHJKMNQUVXZ"
OUTRIGHT_RE = re.compile(r"^[A-Z0-9]{1,3}[FGHJKMNQUVXZ][0-9]$")


def classify(symbol: str, root: str) -> str:
    if "-" in symbol:
        return "spread_strip"
    canon = re.compile(rf"^{re.escape(root)}[{MONTH_CODES}][0-9]$")
    if canon.match(symbol):
        return "outright_root_family"
    if OUTRIGHT_RE.match(symbol):
        return "foreign_outright"
    return "other"


def main() -> None:
    results = {}
    for root, dirs in ROOT_DIRS.items():
        files = []
        for d in dirs:
            files += sorted((PQ_ROOT / d).glob("*.parquet"))
        frames = []
        for f in files:
            t = pq.ParquetFile(f)
            df = t.read(columns=["raw_symbol", "volume", "ts_event"]).to_pandas()
            frames.append(df)
        big = pd.concat(frames, ignore_index=True)
        big["cls"] = big["raw_symbol"].map(lambda s: classify(s, root))
        big["date"] = pd.to_datetime(big["ts_event"], unit="ns", utc=True).dt.date.astype(str)

        root_rep = {"line_dirs": dirs, "files": [f.name for f in files],
                    "total_rows": int(len(big)), "classes": {}}
        for cls, g in big.groupby("cls"):
            sym_agg = (g.groupby("raw_symbol")
                       .agg(bars=("raw_symbol", "size"), volume=("volume", "sum"),
                            first=("date", "min"), last=("date", "max"))
                       .sort_values("bars", ascending=False))
            entry = {"bars": int(len(g)), "volume": int(g["volume"].sum()),
                     "distinct_symbols": int(sym_agg.shape[0]),
                     "symbols": {s: {"bars": int(r.bars), "volume": int(r.volume),
                                     "first": r.first, "last": r.last}
                                 for s, r in sym_agg.iterrows()}}
            root_rep["classes"][cls] = entry
        results[root] = root_rep
        print(f"[{root}] rows={len(big)} " +
              " ".join(f"{c}={v['bars']}" for c, v in root_rep["classes"].items()))

    # ---- canonical filter recommendation + cross-lane reconciliation ----
    canon_filter = {r: f"^{re.escape(r)}[{MONTH_CODES}][0-9]$" for r in ROOT_DIRS}
    recon = {
        "DEEP-6A reported 6BU5 bars in 6A": results["6A"]["classes"]["foreign_outright"]["symbols"].get("6BU5"),
        "DEEP-6E reported 6JZ7 bars in 6E": results["6E"]["classes"]["foreign_outright"]["symbols"].get("6JZ7"),
        "DEEP-6E reported SIJ5 bars in 6E": results["6E"]["classes"]["foreign_outright"]["symbols"].get("SIJ5"),
        "DEEP-6B reported GCQ4 gold prints in 6B": results["6B"]["classes"]["foreign_outright"]["symbols"].get("GCQ4"),
    }
    out = {
        "schema": "contaminant_scan@1",
        "lane": "INTEGRATION-FIX-V2",
        "task_id": "FUTURES-DEEPRESEARCH-V2-20261003",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source": "vendor parquet at /Users/hoangminhlong/my-quantitative-data/"
                  "futures-databento-av1trim/parquet (READ-ONLY; raw dbn.zst immutable)",
        "method": "every bar classified by raw_symbol: spread_strip (dash), "
                  "outright_root_family (^ROOT+month+year exact), foreign_outright "
                  "(outright pattern, other root), other",
        "canonical_view_rule": {
            "law": "downstream consumers of ohlcv-1m vendor parquet MUST filter "
                   "raw_symbol by their root's regex below (outright + root-family "
                   "exact) and quarantine everything else; vendor parquet/raw is "
                   "immutable and NOT rewritten",
            "per_root_regex": canon_filter,
        },
        "per_root": results,
        "sibling_lane_reconciliation": recon,
    }
    (HERE / "contaminant_scan.json").write_text(json.dumps(out, indent=1))
    print("wrote", HERE / "contaminant_scan.json")


if __name__ == "__main__":
    main()
