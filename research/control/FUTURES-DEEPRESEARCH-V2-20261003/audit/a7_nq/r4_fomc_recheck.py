"""A7 audit R4 — independent recompute of NQ_DEEP_v2 §4 FOMC anatomy numbers.

Fresh implementation from NQ_cache + the archived federalreserve.gov HTML:
  * statement counts: files in archive, `a` statements, release-time-proven,
    2:00 p.m. ET, clean day-level n, clean 2pm release-window n
    (dossier text says 147/106/98/84; the lane's JSON says 132/92/85/84)
  * day-level medians: session vol x1.06, RTH vol x1.11, true range x1.12
  * release-window medians: -60..0 0.68x lull, 0..+30 2.26x, +30..+60 2.64x,
    release minute x3.5
"""
from __future__ import annotations

import glob
import json
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.dirname(os.path.dirname(HERE)) + "/analysis/NQ_cache"
STMT = "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms/fed/statements"
OUT = os.path.join(HERE, "r4_fomc_recheck.json")

rows = []
for f in sorted(glob.glob(f"{STMT}/monetary*.html")):
    base = os.path.basename(f)
    m = re.fullmatch(r"monetary(\d{8})a\.html", base)
    if not m:
        continue
    txt = open(f, encoding="utf-8", errors="replace").read()
    mt = re.search(r"For release at\s*(\d{1,2}):(\d{2})\s*([ap])\.m\.\s*(E[SD]T)", txt)
    time_et = None
    if mt:
        hh = int(mt.group(1)) % 12 + (12 if mt.group(3) == "p" else 0)
        time_et = f"{hh:02d}:{mt.group(2)}"
    rows.append({"date": pd.Timestamp(m.group(1)), "time_et": time_et})
fomc = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)

res = {"schema": "a7_nq_r4_fomc_recheck@1",
       "n_statement_files_all": len(glob.glob(f"{STMT}/monetary*.html")),
       "n_a_statements": int(len(fomc)),
       "n_with_release_time_proof": int(fomc["time_et"].notna().sum()),
       "n_2pm": int((fomc["time_et"] == "14:00").sum()),
       "first": str(fomc["date"].min().date()), "last": str(fomc["date"].max().date())}

sess = pd.read_parquet(f"{CACHE}/nq_sessions.parquet")
held = pd.read_parquet(f"{CACHE}/held_volume_k5.parquet")
hs = sess.merge(held.rename(columns={"held": "contract"}),
                on=["session_date", "contract"], how="inner")
hs["d"] = pd.to_datetime(hs["session_date"])
hs = hs.set_index("d")

df = pd.read_parquet(f"{CACHE}/nq_annotated_1m.parquet",
                     columns=["dt", "close", "volume", "high", "low",
                              "contract", "session_date", "minute_of_day"])
dfh = df.merge(held.rename(columns={"held": "contract"}),
               on=["contract", "session_date"], how="inner")
del df
dfh["d"] = pd.to_datetime(dfh["session_date"])
dfh = dfh.sort_values(["contract", "dt"]).reset_index(drop=True)
dfh["r1"] = dfh.groupby("contract")["close"].transform(
    lambda s: np.log(s.astype(float)).diff())
dfh.loc[dfh["contract"].ne(dfh["contract"].shift()), "r1"] = np.nan

ev_dates = set(fomc["date"])

# ---- day level ----
day_rows = []
for d in sorted(ev_dates):
    if d not in hs.index:
        continue
    row = hs.loc[d]
    pool = hs[(hs.index >= d - pd.Timedelta(days=21))
              & (hs.index <= d + pd.Timedelta(days=21))]
    pool = pool[(pool.index.dayofweek == d.dayofweek)
                & (~pool.index.isin(ev_dates))
                & (pool["rth_coverage"].fillna(0) >= 0.6)]
    if pd.isna(row["rth_coverage"]) or row["rth_coverage"] < 0.6 or not len(pool):
        continue
    day_rows.append({"vol": row["volume"] / pool["volume"].median(),
                     "rth": row["rth_volume"] / pool["rth_volume"].median(),
                     "tr": row["true_range"] / pool["true_range"].median()})
dd = pd.DataFrame(day_rows)
res["day_level"] = {"n": len(dd),
                    "vol_ratio_median": float(dd["vol"].median()),
                    "rth_ratio_median": float(dd["rth"].median()),
                    "tr_ratio_median": float(dd["tr"].median()),
                    "share_vol_gt1": float((dd["vol"] > 1).mean()),
                    "share_tr_gt1": float((dd["tr"] > 1).mean())}

# ---- release windows (2pm ET = 13:00 CT) ----
ev2 = fomc[fomc["time_et"] == "14:00"]
WINS = [("m120_60", -120, -60), ("m60_0", -60, 0), ("h0_30", 0, 30),
        ("h30_60", 30, 60), ("h60_120", 60, 120), ("h120_180", 120, 180)]
recs = []
for d in ev2["date"]:
    day = d.normalize()
    if day not in hs.index or pd.isna(hs.loc[day, "rth_coverage"]) \
            or hs.loc[day, "rth_coverage"] < 0.6:
        continue
    bars = dfh[dfh["d"] == day]
    if not len(bars):
        continue
    pool_dates = hs[(hs.index >= day - pd.Timedelta(days=21))
                    & (hs.index <= day + pd.Timedelta(days=21))
                    & (hs.index.dayofweek == day.dayofweek)
                    & (~hs.index.isin(ev_dates))
                    & (hs["rth_coverage"].fillna(0) >= 0.6)].index
    pbars = dfh[dfh["d"].isin(pool_dates)]
    rec = {}
    for name, a, b in WINS:
        m0, m1 = 13 * 60 + a, 13 * 60 + b
        eb = bars[(bars["minute_of_day"] >= m0) & (bars["minute_of_day"] < m1)]
        cb = pbars[(pbars["minute_of_day"] >= m0) & (pbars["minute_of_day"] < m1)]
        ev_vol = eb["volume"].sum()
        cv = cb.groupby("d")["volume"].sum().median()
        rec[f"vol_{name}"] = ev_vol / cv if cv else np.nan
        ev_ar = eb["r1"].abs().mean()
        ca = cb.assign(a=cb["r1"].abs()).groupby("d")["a"].mean().median()
        rec[f"ar_{name}"] = ev_ar / ca if ca else np.nan
    em = bars[bars["minute_of_day"] == 780]
    cm = pbars[pbars["minute_of_day"] == 780]
    if len(em) and len(cm):
        rec["relmin"] = float(em["volume"].iloc[0] / cm["volume"].median())
    recs.append(rec)
wd = pd.DataFrame(recs)
out = {"n": len(wd)}
for name, _a, _b in WINS:
    out[name] = {"vol": float(wd[f"vol_{name}"].median()),
                 "absr": float(wd[f"ar_{name}"].median())}
out["release_minute_vol_median"] = float(wd["relmin"].median())
res["release_windows_2pm"] = out

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
