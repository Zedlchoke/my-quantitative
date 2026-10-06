#!/usr/bin/env python3
"""A7-INTEGRATION audit script 3: independent verification of the NQ 2020
alias adjudication, using ONLY our delivered vendor parquet (no network).

Verifies (probe claims in parentheses):
 A. instrument_id 16908: 'NQU8-NQM9' label 2018-08-15..2020-05-31, 92,075 bars,
    24,686,121 volume; 'NQM0' label 2020-06-01..2020-06-19, 19,406 bars,
    5,159,596 volume; monthly volume ramp.
 B. hole window 2020-03-23..2020-05-29 on id 16908: 58 distinct trading dates,
    volume 21,824,572, 0 missing sessions (re-derive expected CME Globex
    session calendar: Sun-Thu opens + Fri, minus holidays), Mar-23 = 625,650.
 C. probe window 2020-03-01..2020-06-30 all-symbols total 169,992;
    NQM0-equiv (id 16908) 100,034 = 80,628 alias + 19,406 NQM0; NQH0 17,932;
    NQU0 30,204; NQJ0 absent.
 D. alias uniqueness: scan ALL instrument_ids in all six roots for a dash->outright
    label transition on one instrument_id (the "only such alias" claim).
 E. outright-filter blindness: symbols matching ^NQ[FGHJKMNQUVXZ][0-9]$ carry
    no id-16908 bars before 2020-06-01 (why DEEP-NQ saw a hole).
Writes only under audit/a7_integration/.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

PQ_ROOT = Path("/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet")
HERE = Path(__file__).resolve().parent
NQ_FILES = [PQ_ROOT / "AV1R-O1M-NQ-DELTA" / n for n in
            ("AV1R-O1M-NQ-DELTA__2018-06-01_2020-06-01.parquet",
             "AV1R-O1M-NQ-DELTA__2020-06-01_2022-06-01.parquet")]
HOLE = ("2020-03-23", "2020-05-29")
WIN = ("2020-03-01", "2020-06-30")
OUTRIGHT = re.compile(r"^NQ[FGHJKMNQUVXZ][0-9]$")

out = {}

df = pd.concat([pd.read_parquet(p, columns=["raw_symbol", "instrument_id", "volume", "ts_event"])
                for p in NQ_FILES], ignore_index=True)
df["date"] = pd.to_datetime(df.ts_event, unit="ns", utc=True).dt.date.astype(str)

# A. instrument 16908 label windows
i = df[df.instrument_id == 16908]
lab = []
for s, g in i.groupby("raw_symbol"):
    lab.append({"raw_symbol": s, "first": g.date.min(), "last": g.date.max(),
                "bars": int(len(g)), "volume": int(g.volume.sum())})
monthly = {m: int(g.volume.sum()) for m, g in i.groupby(i.date.str[:7])}
out["A_16908_label_windows"] = lab
out["A_monthly_volume"] = monthly
print("A. id16908 labels:", json.dumps(lab))
print("   monthly:", {k: v for k, v in sorted(monthly.items()) if v > 1000})

# B. hole window sessions
hole = i[(i.date >= HOLE[0]) & (i.date <= HOLE[1])]
dates = sorted(hole.date.unique())
out["B_hole"] = {"n_dates": len(dates), "volume": int(hole.volume.sum()),
                 "first": dates[0], "last": dates[-1], "dates": dates,
                 "mar23_volume": int(hole[hole.date == "2020-03-23"].volume.sum())}
print(f"B. hole: {len(dates)} dates, vol={hole.volume.sum():,}, mar23={out['B_hole']['mar23_volume']:,}")
# expected CME session calendar: every Mon-Fri plus Sundays (Globex open), minus
# Good Friday (2020-04-10) and Memorial Day Monday (2020-05-25) closures
exp = []
d = pd.Timestamp(HOLE[0]).date()
end = pd.Timestamp(HOLE[1]).date()
import datetime as dt
while d <= end:
    if d.weekday() < 5 or d.weekday() == 6:  # Mon-Fri or Sun
        exp.append(d.isoformat())
    d += dt.timedelta(days=1)
holidays = {"2020-04-10"}  # Good Friday (CME closed)
# Memorial Day 2020-05-25: check empirically below instead of assuming
missing = [d for d in exp if d not in dates and d not in holidays]
extra = [d for d in dates if d not in exp]
out["B_calendar_check"] = {"expected_sun_thu_plus_weekdays": len(exp), "holidays_assumed": sorted(holidays),
                           "missing_from_data": missing, "extra_in_data": extra,
                           "may25_present": "2020-05-25" in dates, "apr10_present": "2020-04-10" in dates}
print("   calendar: missing:", missing, "| extra:", extra,
      "| 5/25 present:", "2020-05-25" in dates, "| 4/10 present:", "2020-04-10" in dates)

# C. probe window reconciliation (LOCAL side only; vendor side from probe json)
w = df[(df.date >= WIN[0]) & (df.date <= WIN[1])]
per_sym = w.groupby("raw_symbol").agg(bars=("raw_symbol", "size"), volume=("volume", "sum"))
nqm0_equiv = int(w[w.instrument_id == 16908].shape[0])
out["C_window"] = {"all_symbols_total": int(len(w)),
                   "nqm0_equiv_id16908": nqm0_equiv,
                   "alias_bars_in_window": int((w[w.instrument_id == 16908].raw_symbol == "NQU8-NQM9").sum()),
                   "nqm0_label_bars_in_window": int((w[w.instrument_id == 16908].raw_symbol == "NQM0").sum()),
                   "NQH0": int(per_sym.loc["NQH0", "bars"]) if "NQH0" in per_sym.index else None,
                   "NQU0": int(per_sym.loc["NQU0", "bars"]) if "NQU0" in per_sym.index else None,
                   "NQJ0_present": "NQJ0" in per_sym.index}
print("C. window total:", len(w), "| id16908:", nqm0_equiv,
      "| NQH0:", out["C_window"]["NQH0"], "| NQU0:", out["C_window"]["NQU0"],
      "| NQJ0:", out["C_window"]["NQJ0_present"])

# E. outright-filter blindness in hole window
o = w[w.raw_symbol.map(lambda s: bool(OUTRIGHT.match(s)))]
front_like = o[(o.date >= HOLE[0]) & (o.date <= HOLE[1])]
per = front_like.groupby("raw_symbol").agg(bars=("raw_symbol", "size"), vol=("volume", "sum"))
out["E_outright_filter_view_hole"] = {s: {"bars": int(r.bars), "vol": int(r.vol)} for s, r in per.iterrows()}
print("E. regex-visible symbols in hole window:", out["E_outright_filter_view_hole"])

# D. alias uniqueness across six roots
ROOT_DIRS = {"NQ": ["AV1T-O1M-NQ", "AV1R-O1M-NQ-DELTA"], "ES": ["AV1T-O1M-ES", "AV1R-O1M-ES-DELTA"],
             "6E": ["AV1T-O1M-6E", "AV1R-O1M-6E-BACKFILL", "AV1B-O1M-6E-BACKFILL2"],
             "6J": ["AV1T-O1M-6J", "AV1R-O1M-6J-BACKFILL", "AV1B-O1M-6J-BACKFILL2"],
             "6B": ["AV1T-O1M-6B", "AV1R-O1M-6B-BACKFILL", "AV1B-O1M-6B-BACKFILL2"],
             "6A": ["AV1T-O1M-6A", "AV1R-O1M-6A-BACKFILL", "AV1B-O1M-6A-BACKFILL2"]}
multi = {}
for root, dirs in ROOT_DIRS.items():
    frames = [pq.ParquetFile(PQ_ROOT / d / f).read(columns=["raw_symbol", "instrument_id"]).to_pandas()
              for d in dirs for f in sorted((PQ_ROOT / d).glob("*.parquet"))]
    t = pd.concat(frames, ignore_index=True)
    g = t.groupby("instrument_id")["raw_symbol"].agg(["nunique", "unique"])
    for iid, row in g[g["nunique"] > 1].iterrows():
        syms = sorted(row["unique"])
        has_dash = any("-" in s for s in syms)
        has_outright = any(re.fullmatch(rf"{re.escape(root)}[FGHJKMNQUVXZ][0-9]", s) for s in syms)
        if has_dash and has_outright:  # dash -> outright transition on one instrument
            multi[f"{root}:{iid}"] = syms
out["D_dash_to_outright_aliases"] = multi
print("D. instruments with BOTH dash and root-outright labels:", json.dumps(multi))

(HERE / "a7_nq2020_verify.json").write_text(json.dumps(out, indent=1))
print("wrote", HERE / "a7_nq2020_verify.json")
