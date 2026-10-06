#!/usr/bin/env python
"""A7-DEEP-ES audit R4: INDEPENDENT recompute of A5 CoT claims.

Local nonprice root was EMPTIED during the audit window (incident); the fixed
cftc_legacy_tidy.parquet only existed locally and is gone. The iCloud mirror
holds (a) the PRE-FIX tidy (contaminated: COT_LEGACY_ES 2,208 rows / 1,126
dup weeks) and (b) the immutable raw annual zips. This script therefore:

  1. applies the dossier's exact-name filter to the PRE-FIX mirror tidy
     (reproduces the DEEP-ES lane's own pipeline);
  2. rebuilds the canonical exact-name union straight from the RAW deacot
     zips (source truth == what the FIXED tidy encodes, per the normalizer's
     mapping) and asserts equality with (1);
  3. recomputes the CoT claims on that canonical series with an INDEPENDENT
     ratio-adjusted front chain built from the vendor parquet:
     U-shape quintiles, extreme deciles, crisis anchors, Spearman, by-year.

Checks (dossier sec 0.7 / sec 6):
  - 1,082 weekly rows 2006-01-03..2026-09-22, 0 duplicate weeks, 922 usable
  - U-shape: Q1 14.9 / Q5 14.4 vs Q2-Q4 11.9-12.7 fwd 21d vol; +~2pp tails
  - deciles most-short -227k -> 16.8%; most-long +180k -> 15.9%
  - COVID 13th pctl fwd rv 90.5; 2022 bear 94th; Aug-2011 58th; 2025-04 78th
  - Spearman(trailing pctl, fwd rv63) = -0.07
  - OI by year: 1.40M 2006 -> 2.95M 2016 peak -> 1.98M 2026

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python a7_r4_cot.py
"""
import glob
import io
import json
import os
import re
import zipfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
MIR = "/Users/hoangminhlong/Library/Mobile Documents/com~apple~CloudDocs/my-quantitative-futures/nonprice"
VEND = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet"
NS = 1_000_000_000.0
PAT = re.compile(r"^ES[HMUZ][0-9]$")
MCODE = {"H": 3, "M": 6, "U": 9, "Z": 12}
EXACT = {"E-MINI S&P 500 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE",
         "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE"}

# ------------------------- (1) dossier pipeline: pre-fix tidy + exact filter
td = pd.read_parquet(os.path.join(MIR, "normalized/cftc_legacy_tidy.parquet"))
td = td[td["series_id"] == "COT_LEGACY_ES"].copy()
print("pre-fix COT_LEGACY_ES rows:", len(td),
      "dup weeks:", td.duplicated("observation_period").sum(),
      "distinct market names:", td["market_name"].str.strip().nunique())
td["mn"] = td["market_name"].str.strip()
cot = td[td["mn"].isin(EXACT)].copy()
print("after exact-name filter:", len(cot),
      "dup:", cot.duplicated("observation_period").sum(),
      cot["observation_period"].min(), "->", cot["observation_period"].max())

# ------------------------- (2) canonical union from RAW annual zips
raw_rows = []
for zp in sorted(glob.glob(os.path.join(MIR, "cftc/legacy_futures_only/deacot*.zip"))):
    with zipfile.ZipFile(zp) as z:
        name = [n for n in z.namelist() if n.lower().endswith(".txt")][0]
        with z.open(name) as fh:
            df = pd.read_csv(io.TextIOWrapper(fh, encoding="latin-1"))
    df.columns = [c.strip() for c in df.columns]
    mn = df["Market and Exchange Names"].str.strip()
    sub = df[mn.isin(EXACT)]
    raw_rows.append(sub[["Market and Exchange Names",
                         "As of Date in Form YYYY-MM-DD",
                         "Open Interest (All)",
                         "Noncommercial Positions-Long (All)",
                         "Noncommercial Positions-Short (All)"]])
R = pd.concat(raw_rows, ignore_index=True)
R.columns = ["name", "date", "Open_Interest_All", "NonComm_Long", "NonComm_Short"]
R["obs"] = pd.to_datetime(R["date"])
R = R.sort_values("obs").reset_index(drop=True)
print("raw-zip canonical union rows:", len(R), "dup dates:", R.duplicated("obs").sum())

cot["obs"] = pd.to_datetime(cot["observation_period"])
mg = cot.merge(R, on="obs", how="outer", indicator=True)
both = mg[mg["_merge"] == "both"]
oi_eq = (both["open_interest_all"] == both["Open_Interest_All"]).mean()
nl_eq = (both["noncomm_long"] == both["NonComm_Long"]).mean()
ns_eq = (both["noncomm_short"] == both["NonComm_Short"]).mean()
print(f"filter-vs-raw equality: rows matched {len(both)}/{len(mg)} "
      f"(left-only {(mg['_merge']=='left_only').sum()}, right-only {(mg['_merge']=='right_only').sum()}); "
      f"OI equal {oi_eq:.4f}, noncomm_long {nl_eq:.4f}, noncomm_short {ns_eq:.4f}")

cot["rel"] = pd.to_datetime(cot["released_at"].astype(str).str.split("/").str[0])
cot = cot.sort_values("rel").reset_index(drop=True)
cot["net_noncomm"] = cot["noncomm_long"] - cot["noncomm_short"]

# ------------------------- (3) independent ratio-adjusted front chain
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
m = m.sort_values(["instrument_id", "sess", "mkey"], kind="stable")
cd = m.groupby(["instrument_id", "sess"], sort=True).agg(
    vol=("volume", "sum"), close=("close", "last")).reset_index()
cd["close"] = cd["close"] / NS
sym = m.groupby("instrument_id")["raw_symbol"].first()
maxday = cd.groupby("instrument_id")["vol"].max()
real_iids = maxday[maxday >= 100_000].index
last_sess = cd.groupby("instrument_id")["sess"].max()
dmap = {}
for iid in real_iids:
    mo = MCODE[sym[iid][2]]
    yy = last_sess[iid].year + (1 if mo < last_sess[iid].month else 0)
    dmap[iid] = f"{yy:04d}-{mo:02d}"
dl = sorted(set(dmap.values()))
iid_of = {v: k for k, v in sorted(dmap.items(), key=lambda kv: kv[1])}
piv = cd.pivot_table(index="sess", columns="instrument_id", values="vol")
piv.index = pd.DatetimeIndex(piv.index)
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
FR = pd.Series(front, index=piv.index)
cd["front"] = cd["sess"].map(dict(zip(piv.index, front)))
cdf = cd[cd["instrument_id"].map(dmap) == cd["front"]].set_index("sess").sort_index()
cdf["switch"] = FR != FR.shift()
adj, adjc, prev_close = 1.0, [], None
cdi = cd.set_index(["sess", "instrument_id"])
for i, (s, r) in enumerate(cdf.iterrows()):
    if i > 0 and r["switch"]:
        old_close = prev_close
        try:
            new_on_prev = cdi.loc[(cdf.index[i - 1], r["instrument_id"]), "close"]
        except KeyError:
            new_on_prev = np.nan
        if pd.notna(old_close) and pd.notna(new_on_prev) and new_on_prev:
            adj *= old_close / new_on_prev
    adjc.append(adj)
    prev_close = r["close"]
cdf["close_adj"] = cdf["close"] * pd.Series(adjc, index=cdf.index, dtype=float)
ch = cdf[["front", "close_adj"]].copy()
ch["lret"] = np.log(ch["close_adj"]).diff()
sess = list(ch.index)

# ------------------------- (4) trailing percentiles + forward outcomes
def fwd_window(rel_ts, n):
    d = rel_ts.date()
    i = None
    for j, s in enumerate(sess):
        if s.date() > d:
            i = j
            break
    if i is None or i + n > len(sess):
        return None
    return sess[i:i + n]

def outcome(win):
    r = ch.loc[win]
    rv = float(np.sqrt((r["lret"] ** 2).sum() * 252 / len(win)) * 100)
    px = r["close_adj"]
    dd = float((px / px.cummax() - 1).min() * 100)
    return rv, dd

vals = cot["net_noncomm"].to_numpy(dtype=float)
rels = cot["rel"]
rowsF = []
for k in range(len(cot)):
    if k < 156:
        continue
    w = vals[max(0, k - 156):k]
    v = vals[k]
    pct = float((w < v).mean())
    win21 = fwd_window(rels.iloc[k], 21)
    win63 = fwd_window(rels.iloc[k], 63)
    if win21 is None:
        continue
    rv21, dd21 = outcome(win21)
    rv63, dd63 = outcome(win63) if win63 is not None else (None, None)
    rowsF.append({"rel": rels.iloc[k].date().isoformat(), "net": int(v),
                  "oi": int(cot["open_interest_all"].iloc[k]), "pctl": pct,
                  "rv21": rv21, "dd21": dd21, "rv63": rv63, "dd63": dd63})
F = pd.DataFrame(rowsF)
print("usable releases:", len(F), F["rel"].min(), "->", F["rel"].max())

F["q"] = pd.cut(F["pctl"], [0, .2, .4, .6, .8, 1.0],
                labels=["Q1", "Q2", "Q3", "Q4", "Q5"])
bucket = F.groupby("q", observed=True).agg(
    n=("net", "size"), net_med=("net", "median"),
    rv21_med=("rv21", "median"), rv63_med=("rv63", "median"),
    dd21_med=("dd21", "median"), dd63_med=("dd63", "median")).round(2)
t_low = F[F["pctl"] <= 0.1]
t_high = F[F["pctl"] >= 0.9]
rho = float(F["pctl"].rank().corr(F["rv63"].rank()))
anchors = {}
for label, d in [("Aug-2011", "2011-08-01"), ("COVID 2020-03", "2020-03-01"),
                 ("2022 bear", "2022-01-01"), ("2025-04 tariff", "2025-04-01")]:
    sub = F[F["rel"] >= d].head(1)
    if len(sub):
        anchors[label] = {"rel": sub["rel"].iloc[0],
                          "pctl": round(float(sub["pctl"].iloc[0]), 3),
                          "rv21": round(float(sub["rv21"].iloc[0]), 1)}
cot["year"] = cot["obs"].dt.year
by_year = cot.groupby("year").agg(n=("net_noncomm", "size"),
                                  net_med=("net_noncomm", "median"),
                                  oi_med=("open_interest_all", "median")).round(0)

out = {
    "pre_fix_tidy_state": {"rows": int(len(td)),
                           "dup_weeks": int(td.duplicated("observation_period").sum()),
                           "market_names": int(td["mn"].nunique())},
    "dossier_filter_series": {"rows": int(len(cot)),
                              "dup": int(cot.duplicated("observation_period").sum()),
                              "window": [str(cot["obs"].min().date()),
                                         str(cot["obs"].max().date())]},
    "raw_zip_canonical": {"rows": int(len(R)), "dup_dates": int(R.duplicated("obs").sum())},
    "filter_vs_raw": {"matched": int(len(both)),
                      "left_only": int((mg["_merge"] == "left_only").sum()),
                      "right_only": int((mg["_merge"] == "right_only").sum()),
                      "oi_equal_frac": float(oi_eq),
                      "noncomm_long_equal_frac": float(nl_eq),
                      "noncomm_short_equal_frac": float(ns_eq)},
    "n_usable": int(len(F)),
    "quintiles": bucket.reset_index().to_dict(orient="records"),
    "deciles": {
        "most_short": {"n": int(len(t_low)), "net_med": float(t_low["net"].median()),
                       "rv21_med": float(t_low["rv21"].median()),
                       "dd63_med": float(t_low["dd63"].median())},
        "most_long": {"n": int(len(t_high)), "net_med": float(t_high["net"].median()),
                      "rv21_med": float(t_high["rv21"].median()),
                      "dd63_med": float(t_high["dd63"].median())}},
    "spearman_pctl_rv63": rho,
    "anchors": anchors,
    "by_year": by_year.reset_index().to_dict(orient="records"),
}
with open(os.path.join(HERE, "r4_cot.json"), "w") as f:
    json.dump(out, f, indent=1, default=str)
print(bucket.to_string())
print("deciles:", json.dumps(out["deciles"], indent=1))
print("spearman:", rho)
print("anchors:", json.dumps(anchors, indent=1))
print("WROTE r4_cot.json")
