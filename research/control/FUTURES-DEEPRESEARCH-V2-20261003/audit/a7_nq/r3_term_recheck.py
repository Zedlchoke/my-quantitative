"""A7 audit R3 — independent recompute of NQ_DEEP_v2 §3 term-structure numbers.

Fresh implementation from NQ_cache (nq_sessions, held_volume_k5,
contract_registry):
  * 66 rolls; roll-day gap distribution (median -0.8, p10 -8.5, p90 +238.9,
    min -14, max +302; 49.2% positive)
  * corr(roll-day gap, trailing-10-session spread median) = 0.999
  * unadjusted-chain embedded pts/yr: 2023 +723, 2024 +1,014, 2025 +907, 2026 +810
  * daily-volume-crossover DTE: median 7 (p10 4, p90 7, min 3, max 7; n=62)
  * calendar-rule thin window: median 1.4% of market-front volume (n=650)
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.dirname(os.path.dirname(HERE)) + "/analysis/NQ_cache"
OUT = os.path.join(HERE, "r3_term_recheck.json")

MONTH_CODE = {"H": 3, "M": 6, "U": 9, "Z": 12}


def third_friday(y: int, m: int) -> dt.date:
    d = dt.date(y, m, 1)
    off = (4 - d.weekday()) % 7
    return d + dt.timedelta(days=off + 14)


sess = pd.read_parquet(f"{CACHE}/nq_sessions.parquet")
# real quarterly contracts only
sess = sess[sess["contract"].str.match(r"^NQ[HMUZ]\d_\d{4}$")].copy()
held = pd.read_parquet(f"{CACHE}/held_volume_k5.parquet").sort_values(
    "session_date").reset_index(drop=True)
held["prev"] = held["held"].shift()
rolls = held[held["held"].ne(held["prev"]) & held["prev"].notna()].copy()
res = {"schema": "a7_nq_r3_term_recheck@1", "n_rolls": int(len(rolls))}

closes = sess.pivot_table(index="session_date", columns="contract", values="close")
vols = sess.pivot_table(index="session_date", columns="contract", values="volume")

# expiry map from symbol_year key
def expiry_of(c: str) -> dt.date:
    m = re.fullmatch(r"NQ([HMUZ])(\d)_(\d{4})", c)
    return third_friday(int(m.group(3)), MONTH_CODE[m.group(1)])

rows = []
for r in rolls.itertuples():
    old, new, dstr = r.prev, r.held, r.session_date
    di = closes.index.get_loc(dstr)
    window = closes.index[max(0, di - 12):di + 1]
    sp = ((closes.loc[window, new] - closes.loc[window, old]) / 1e9).dropna()
    gap = float(sp.iloc[-1]) if len(sp) else np.nan
    med10 = float(sp.iloc[:-1].median()) if len(sp) > 2 else np.nan
    oldv = float(vols.at[dstr, old]) if not pd.isna(vols.at[dstr, old]) else 0.0
    rows.append({"roll_session": str(dstr), "old": old, "new": new,
                 "gap": gap, "spread_med10": med10, "old_vol": oldv,
                 "year": pd.Timestamp(dstr).year})
rdf = pd.DataFrame(rows)
ok = rdf.dropna(subset=["gap"])
ok = ok[ok["old_vol"] > 0]
res["roll_gap"] = {
    "n": int(len(ok)),
    "median": float(ok["gap"].median()),
    "p10": float(ok["gap"].quantile(.1)),
    "p90": float(ok["gap"].quantile(.9)),
    "min": float(ok["gap"].min()),
    "max": float(ok["gap"].max()),
    "share_positive": float((ok["gap"] > 0).mean())}
res["corr_gap_vs_spreadmed10"] = float(ok["gap"].corr(ok["spread_med10"]))

embed = ok.groupby("year")["gap"].sum()
res["embedded_pts_per_year"] = {str(int(k)): float(v) for k, v in embed.items()}

# daily-volume crossover DTE (persistent 3-session new>old), dte<=45 filter
dte_list = []
for r in rolls.itertuples():
    old, new = r.prev, r.held
    if old not in vols.columns or new not in vols.columns:
        continue
    pair = vols[[old, new]].dropna(how="all")
    both = pair.dropna()
    both = both[both[old] > 0]
    nb = (both[new] > both[old]).values
    cross = None
    for i in range(len(nb) - 2):
        if nb[i] and nb[i + 1] and nb[i + 2]:
            cross = both.index[i]
            break
    if cross is not None:
        e = expiry_of(old)
        dte = (e - pd.Timestamp(cross).date()).days
        if 0 <= dte <= 45:
            dte_list.append(dte)
res["daily_volume_crossover_dte"] = {
    "n": len(dte_list), "median": float(np.median(dte_list)),
    "p10": float(np.percentile(dte_list, 10)),
    "p90": float(np.percentile(dte_list, 90)),
    "min": int(min(dte_list)), "max": int(max(dte_list))}

# calendar-rule thin window: first 10 sessions of each calendar hold window
hc = pd.read_parquet(f"{CACHE}/held_calendar.parquet").rename(
    columns={"held": "contract"}).sort_values("session_date")
hc["chg"] = hc["contract"].ne(hc["contract"].shift())
hc["seq"] = hc.groupby(hc["chg"].cumsum()).cumcount()
early = set(hc[hc["seq"] < 10]["session_date"])
mcal = sess.merge(hc[["session_date", "contract"]], on=["session_date", "contract"])
cal_vol = mcal.set_index("session_date")["volume"]
mk = sess[sess["session_date"].isin(set(held["session_date"]))]
mk_vol = mk.groupby("session_date")["volume"].sum()
cmp = pd.DataFrame({"cal": cal_vol, "mkt": mk_vol}).dropna()
cmp = cmp[cmp.index.isin(early)]
cmp["ratio"] = cmp["cal"] / cmp["mkt"]
res["calendar_rule_thin_window"] = {
    "n": int(len(cmp)), "median_ratio": float(cmp["ratio"].median()),
    "p10": float(cmp["ratio"].quantile(.1)),
    "share_below_50pct": float((cmp["ratio"] < 0.5).mean())}

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
