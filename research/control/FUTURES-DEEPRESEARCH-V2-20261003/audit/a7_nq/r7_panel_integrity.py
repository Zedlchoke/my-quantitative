"""A7 audit R7 — recompute NQ_DEEP_v2 panel-integrity numbers from RAW vendor
parquet (both NQ dirs, 13 files, read-only):
  * parent rows 7,330,320; calendar-spread rows 641,787; outright 6,688,533
  * first/last bar 2010-06-06 22:00Z -> 2026-09-30 23:59Z
  * dash-symbol exclusion is the outright filter the DEEP lanes used
  * duplicates (symbol, ts_event) on the outright panel = 0
"""
from __future__ import annotations

import glob
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = ("/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim"
        "/parquet")
OUT = os.path.join(HERE, "r7_panel_integrity.json")

files = sorted(glob.glob(f"{ROOT}/AV1R-O1M-NQ-DELTA/*.parquet")) + sorted(
    glob.glob(f"{ROOT}/AV1T-O1M-NQ/*.parquet"))
tot = spread = outright = 0
first = last = None
dup = 0
per_file = {}
for f in files:
    d = pd.read_parquet(f, columns=["raw_symbol", "ts_event"])
    is_spread = d["raw_symbol"].str.contains("-")
    n, s = len(d), int(is_spread.sum())
    tot += n
    spread += s
    outright += n - s
    o = d[~is_spread]
    dup += int(o.duplicated(subset=["raw_symbol", "ts_event"]).sum())
    f0, f1 = o["ts_event"].min(), o["ts_event"].max()
    first = f0 if first is None else min(first, f0)
    last = f1 if last is None else max(last, f1)
    per_file[os.path.basename(f)] = {"rows": n, "spread_rows": s}

res = {
    "schema": "a7_nq_r7_panel_integrity@1", "n_files": len(files),
    "parent_rows_total": tot, "calendar_spread_rows": spread,
    "outright_rows": outright,
    "outright_first_ts_utc": str(pd.to_datetime(first, unit="ns", utc=True)),
    "outright_last_ts_utc": str(pd.to_datetime(last, unit="ns", utc=True)),
    "outright_duplicate_symbol_tsevent_rows": dup,
    "per_file": per_file}
with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1, default=float)
print(json.dumps({k: v for k, v in res.items() if k != "per_file"}, indent=1))
