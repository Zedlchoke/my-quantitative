#!/usr/bin/env python
"""A7-DEEP-ES audit R5: INDEPENDENT recompute of the >2% 1m-jump claim.

Dossier sec 7: "Extreme 1m jumps (>2%): exactly 10 in 16.4y, all at
identifiable macro minutes - 2011-08-05 (US downgrade), 2020-03-03/09/16
(COVID; the 2020-03-16 08:45 CT halt-reopen minute moved -5.67%), 2022-09-13,
10-13, 11-10 (all three at the 07:30 CT CPI release minute), 2025-04-07/09
(tariff-pause cluster)". Per-era ledger counts: E1=1 E2=0 E3=0 E4=0 E5=4 E6=3
E7=2. NOTE: listed dates = 9 -> check the 10th.

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python a7_r5_quality.py
"""
import glob
import json
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
VEND = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet"
NS = 1_000_000_000.0
PAT = re.compile(r"^ES[HMUZ][0-9]$")
MCODE = {"H": 3, "M": 6, "U": 9, "Z": 12}

chunks = sorted(glob.glob(f"{VEND}/AV1R-O1M-ES-DELTA/*.parquet")) + \
         sorted(glob.glob(f"{VEND}/AV1T-O1M-ES/*.parquet"))
rows = []
for fp in chunks:
    d = pd.read_parquet(fp, columns=["instrument_id", "raw_symbol", "ts_event",
                                     "close", "volume"])
    rows.append(d[d["raw_symbol"].str.match(PAT)])
m = pd.concat(rows, ignore_index=True)
del rows
chi = pd.DatetimeIndex(pd.to_datetime(m["ts_event"].to_numpy(), utc=True)) \
        .tz_convert("America/Chicago")
m["sess"] = chi + pd.to_timedelta((chi.hour >= 17).astype("int32"), unit="D")
m["sess"] = pd.DatetimeIndex(m["sess"]).normalize().tz_localize(None)
m["mkey"] = np.where(chi.hour >= 17, (chi.hour - 17) * 60 + chi.minute,
                     (chi.hour + 7) * 60 + chi.minute)

dv = m.groupby(["instrument_id", "sess"])["volume"].sum().reset_index()
piv = dv.pivot_table(index="sess", columns="instrument_id", values="volume")
piv.index = pd.DatetimeIndex(piv.index)
sym = m.groupby("instrument_id")["raw_symbol"].first()
maxday = dv.groupby("instrument_id")["volume"].max()
real_iids = maxday[maxday >= 100_000].index
last_sess = dv.groupby("instrument_id")["sess"].max()
dmap = {}
for iid in real_iids:
    mo = MCODE[sym[iid][2]]
    yy = last_sess[iid].year + (1 if mo < last_sess[iid].month else 0)
    dmap[iid] = f"{yy:04d}-{mo:02d}"
dl = sorted(set(dmap.values()))
iid_of = {v: k for k, v in sorted(dmap.items(), key=lambda kv: kv[1])}
sess_ix = list(piv.index)
cur = dl[0]
front = []
for i, s in enumerate(sess_ix):
    if i > 0:
        cands = [d for d in dl if d >= cur][:2]
        pv = piv.loc[sess_ix[i - 1]]
        vols = {d: pv.get(iid_of[d], np.nan) for d in cands}
        vols = {k: v for k, v in vols.items() if pd.notna(v)}
        if vols:
            best = max(vols, key=lambda d: (vols[d], -dl.index(d)))
            if best != cur and dl.index(best) > dl.index(cur):
                cur = best
    front.append(cur)
m = m[m["instrument_id"].map(dmap) == m["sess"].map(dict(zip(piv.index, front)))]
m = m.sort_values(["sess", "mkey"], kind="stable")
m["close"] = m["close"] / NS
m["lret"] = np.log(m["close"]).groupby(m["sess"]).diff()
j = m[m["lret"].abs() > 0.02].copy()
j["chi_str"] = [str(t) for t in chi[m.index.isin(j.index)]] if False else None
chi_j = pd.DatetimeIndex(pd.to_datetime(
    m.loc[j.index, "sess"].index.map(lambda x: x)) ) if False else None
# attach Chicago timestamps for the jump rows
jrows = []
for idx in j.index:
    r = m.loc[idx]
    # ts_event was dropped; recover Chicago time from sess+mkey
    base = pd.Timestamp(r["sess"]) - pd.Timedelta(days=1)
    tod = (int(r["mkey"]) + 17 * 60) % (24 * 60)
    t = base + pd.Timedelta(minutes=tod)
    jrows.append({"session": str(pd.Timestamp(r["sess"]).date()),
                  "time_chi": str(t.time()),
                  "lret_pct": round(float(r["lret"]) * 100, 2),
                  "volume": int(r["volume"])})
print("total front-contract 1m |ret|>2%:", len(jrows))
for r in jrows:
    print(" ", r)
out = {"n_jumps_gt2pct": len(jrows), "jumps": jrows,
       "n_gt1pct": int((m["lret"].abs() > 0.01).sum())}
with open(os.path.join(HERE, "r5_jumps.json"), "w") as f:
    json.dump(out, f, indent=1)
print("n |ret|>1%:", out["n_gt1pct"])
print("WROTE r5_jumps.json")
