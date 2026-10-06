"""A7 audit R6 — verify the INTEGRATION-FIX-V2 alias adjudication for the NQ
2020 'vendor hole' directly against the raw delivered vendor parquet (read-only).

Claims under test (nq2020_hole_probe.{md,json}):
  1. instrument_id 16908 carries the NQ June-2020 future under raw_symbol
     'NQU8-NQM9' 2018-08-15..2020-05-31 (92,075 bars) and 'NQM0'
     2020-06-01..06-19 (19,406 bars).
  2. In-window (2020-03-01..2020-06-30) id-16908 bars = 80,628 under the dash
     alias; raw NQM0 window records (alias + relabeled) = 100,034.
  3. Delivered parent NQ.FUT records in 2020-03-01..2020-06-30 = 169,992 (all
     symbols), matching the live-vendor metadata quote in the probe.
  4. Hole window 2020-03-23..2020-05-29 is FULLY present on id 16908: 58
     trading dates, volume 21,824,572 (Mar-23 alone 625,650).
  5. Therefore the dossier's 'THE 2020 VENDOR HOLE ... entirely absent' wording
     is an alias artifact, not absence: with the view rule (relabel id 16908
     date<2020-06-01 -> NQM0), the front contract resolves complete.
Also re-check the a7-quality claim that pre-hole degradation started 03-16
(front volume 505k -> 85k by 03-19).
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAWDIR = ("/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim"
          "/parquet/AV1R-O1M-NQ-DELTA")
OUT = os.path.join(HERE, "r6_alias_verify.json")

d = pd.concat([
    pd.read_parquet(f"{RAWDIR}/AV1R-O1M-NQ-DELTA__2018-06-01_2020-06-01.parquet"),
    pd.read_parquet(f"{RAWDIR}/AV1R-O1M-NQ-DELTA__2020-06-01_2022-06-01.parquet"),
], ignore_index=True)
d["dt"] = pd.to_datetime(d["ts_event"], unit="ns", utc=True)
res = {"schema": "a7_nq_r6_alias_verify@1",
       "files": ["AV1R-O1M-NQ-DELTA__2018-06-01_2020-06-01.parquet",
                 "AV1R-O1M-NQ-DELTA__2020-06-01_2022-06-01.parquet"],
       "rows_delivered_chunks_2018_2022": int(len(d))}
_chunk1 = pd.read_parquet(
    f"{RAWDIR}/AV1R-O1M-NQ-DELTA__2018-06-01_2020-06-01.parquet")
res["rows_delivered_chunk_2018_2020_quoted_944290"] = int(len(_chunk1))
del _chunk1

w = d[(d["dt"] >= "2020-03-01") & (d["dt"] < "2020-07-01")]
res["window_2020_03_06_all_symbol_rows"] = int(len(w))

# 1. instrument 16908 label windows
i16908 = d[d["instrument_id"] == 16908]
lab = {}
for sym, g in i16908.groupby("raw_symbol"):
    lab[sym] = {"bars": int(len(g)), "volume": int(g["volume"].sum()),
                "first": str(g["dt"].min()), "last": str(g["dt"].max())}
res["instrument_16908_labels"] = lab

# 2. window split
wi = i16908[(i16908["dt"] >= "2020-03-01") & (i16908["dt"] < "2020-07-01")]
res["id16908_window_rows"] = int(len(wi))
res["id16908_window_rows_by_symbol"] = {
    str(k): int(v) for k, v in wi.groupby("raw_symbol").size().items()}
res["id16908_window_total_records_alias_plus_relabeled"] = int(len(wi))

# 3. per-symbol delivered counts in window vs probe
sym_counts = {}
for sym, g in w.groupby("raw_symbol"):
    sym_counts[str(sym)] = int(len(g))
res["window_rows_by_symbol"] = sym_counts

# 4. hole window completeness on id 16908
hole = i16908[(i16908["dt"] >= "2020-03-23") & (i16908["dt"] < "2020-05-30")]
dates = sorted(set(hole["dt"].dt.date))
res["hole_window_on_16908"] = {
    "n_trading_dates": len(dates), "first": str(dates[0]), "last": str(dates[-1]),
    "volume_total": int(hole["volume"].sum()),
    "mar23_volume": int(
        hole[hole["dt"].dt.date == pd.Timestamp("2020-03-23").date()]["volume"].sum()),
    "weekday_count": int(np.busday_count("2020-03-23", "2020-05-30")),
    "daily_volume_min_max": [int(hole.groupby(hole["dt"].dt.date)["volume"].sum().min()),
                             int(hole.groupby(hole["dt"].dt.date)["volume"].sum().max())]}

# calendar-day gaps inside hole window (trading dates should be Mon-Fri + no gaps)
all_dates = pd.date_range("2020-03-23", "2020-05-29", freq="D").date
gaps = [str(x) for x in all_dates
        if x not in set(dates) and pd.Timestamp(x).dayofweek < 5]
res["hole_window_on_16908"]["weekday_calendar_gaps"] = gaps

# 5. view-rule check: relabeled NQM0 covers 2020-03-23..2020-06-19 continuously
vr = i16908.copy()
# include the relabeled post-2020-06-01 'NQM0' bars (second chunk)
vr_dates = sorted(set(vr["dt"].dt.date))
n_may_to_jun = [str(x) for x in vr_dates if str(x) >= "2020-03-01"]
res["view_rule_NQM0_series"] = {
    "alias_span_first_last": [str(vr_dates[0]), str(vr_dates[-1])],
    "n_dates_total": len(vr_dates),
    "n_dates_after_2020_03_01": len(n_may_to_jun)}
# post-2020-06-01 NQM0 rows (true relabeled side) for the label-window claim
m0 = d[(d["instrument_id"] == 16908) & (d["raw_symbol"] == "NQM0")]
res["instrument_16908_NQM0_relabel_side"] = {
    "bars": int(len(m0)), "volume": int(m0["volume"].sum()),
    "first": str(m0["dt"].min()), "last": str(m0["dt"].max())}

# 6. pre-hole degradation (a7 claim: front 505k -> 85k by 03-19)
front = d[(d["raw_symbol"] == "NQH0")]
dv = front[(front["dt"] >= "2020-03-09") & (front["dt"] < "2020-03-24")
           ].groupby(front["dt"].dt.date)["volume"].sum()
res["front_NQH0_daily_volume_mar10_23"] = {str(k): int(v) for k, v in dv.items()}
alias_dv = i16908[(i16908["dt"] >= "2020-03-09") & (i16908["dt"] < "2020-03-24")
                  ].groupby(i16908["dt"].dt.date)["volume"].sum()
res["alias_16908_daily_volume_mar10_23"] = {str(k): int(v) for k, v in alias_dv.items()}

# any OTHER dash symbol with front-scale volume in the full NQ panel?
dash = d[d["raw_symbol"].str.contains("-")]
dash_vol = dash.groupby("raw_symbol")["volume"].sum().sort_values(ascending=False)
res["dash_symbols_by_total_volume_top5"] = {
    str(k): int(v) for k, v in dash_vol.head(5).items()}

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
