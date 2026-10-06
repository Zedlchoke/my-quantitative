#!/usr/bin/env python
"""A7-DEEP-ES audit R3: INDEPENDENT recompute of A4 FOMC anatomy + statement
evidence-basis check.

Checks (dossier sec 0.6 / sec 5):
  - statement inventory: 132 a-files 2011-01-26..2026-09-16; 92 with parsed
    clock times (85 at 14:00 ET + 7 irregular); 40 untimed 2011-2015; 131
    in-data; 91 timed with 1m data
  - release bucket ratios: pre-release (-120..-15) 0.72-0.81 flat; release
    bucket 2.91x (|1m ret| 3.19x); +30m 2.65x; elevation 1.3-2.7 for 3h+
  - reaction timing: median peak minute +1; 55% at 0-1; 76% within 5
  - day-level: RTH vol x1.14 (n=131), range x1.38 vs baseline x0.98 (n=3,913)
  - EVIDENCE BASIS: reconcile statement files vs fed calendar HTM files
    (meetings listed vs statements present; count 2011-2015 meetings)

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python a7_r3_fomc.py
"""
import glob
import json
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
VEND = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet"
STMT = os.path.expanduser(
    "~/.my-quantitative-data/futures-nonprice-10syms/fed/statements")
CALD = os.path.expanduser("~/.my-quantitative-data/futures-nonprice-10syms/fed")
NS = 1_000_000_000.0
PAT = re.compile(r"^ES[HMUZ][0-9]$")
MCODE = {"H": 3, "M": 6, "U": 9, "Z": 12}

# ------------------------------------------------------------- statements
files = sorted(glob.glob(os.path.join(STMT, "*.html")))
a_files = [f for f in files if re.search(r"monetary\d{8}a\.html$", f)]
bc_files = [f for f in files if re.search(r"monetary\d{8}[bc]\.html$", f)]
print(f"statement files: total={len(files)} a={len(a_files)} b/c={len(bc_files)}")

evs = []
for f in a_files:
    date = re.search(r"monetary(\d{8})a", f).group(1)
    txt = open(f, encoding="utf-8", errors="ignore").read()
    mt = re.search(r"For release at\s+(\d{1,2}):(\d{2})\s*([ap])\.m\.\s*(E[DS]T)", txt)
    time_et = None
    if mt:
        h = int(mt.group(1)) % 12 + (12 if mt.group(3) == "p" else 0)
        time_et = (h, int(mt.group(2)))
    evs.append({"date": f"{date[:4]}-{date[4:6]}-{date[6:]}", "time_et": time_et})
E = pd.DataFrame(evs)
E["sess"] = pd.to_datetime(E["date"])
timed = E[E["time_et"].notna()]
at_1400 = timed[timed["time_et"].apply(lambda t: t == (14, 0))]
irregular = timed[timed["time_et"].apply(lambda t: t != (14, 0))]
print(f"a-files: {len(E)} | timed: {len(timed)} | at 14:00 ET: {len(at_1400)} | "
      f"irregular: {len(irregular)}")
print("irregular:", [(r.date, r.time_et) for r in irregular.itertuples()])

# b/c files time scan (evidence basis for '106 of 147 files carry times')
bc_timed = 0
for f in bc_files:
    txt = open(f, encoding="utf-8", errors="ignore").read()
    if re.search(r"For release at\s+\d{1,2}:\d{2}", txt):
        bc_timed += 1
all_timed = 0
for f in files:
    txt = open(f, encoding="utf-8", errors="ignore").read()
    if re.search(r"For release at\s+\d{1,2}:\d{2}", txt):
        all_timed += 1
print(f"files carrying clock-time text: all={all_timed}/{len(files)} "
      f"(a={len(timed)}/{len(a_files)}, b/c={bc_timed}/{len(bc_files)})")

# ------------------------------------------------------ calendar reconciliation
cal_txt = ""
for f in sorted(glob.glob(os.path.join(CALD, "fomc*.htm"))):
    cal_txt += open(f, encoding="utf-8", errors="ignore").read()
# meeting dates: look for YYYY-MM-DD or "January 24-25, 2012" styles is messy;
# instead extract all 8-digit or explicit dates near 'Meeting'
dates = re.findall(r"(\d{4})-(\d{2})-(\d{2})", cal_txt)
cal_dates = sorted({f"{a}-{b}-{c}" for a, b, c in dates if 2010 <= int(a) <= 2026})
mtgs_2011_2026 = [d for d in cal_dates if "2011-01-01" <= d <= "2026-10-01"]
mtgs_2011_2015 = [d for d in cal_dates if d <= "2015-12-31"]
stmt_dates = set(E["date"])
missing = [d for d in mtgs_2011_2026 if d not in stmt_dates]
extra = [d for d in sorted(stmt_dates) if d not in set(mtgs_2011_2026)]
print(f"calendar-listed dates 2011-2026: {len(mtgs_2011_2026)} | "
      f"2011-2015: {len(mtgs_2011_2015)}")
print("meetings without statement in archive:", missing)
print("statements not matching calendar date (offset ok):", extra[:12],
      f"(n={len(extra)})")

# ------------------------------------------------------------- 1m front data
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
m["minute_of_day"] = chi.hour * 60 + chi.minute

# daily volume pivot + VOL chain (strict past)
dv = m.groupby(["instrument_id", "sess"])["volume"].sum().reset_index()
piv = dv.pivot_table(index="sess", columns="instrument_id", values="volume")
piv.index = pd.DatetimeIndex(piv.index)
sym = m.groupby("instrument_id")["raw_symbol"].first()
maxday = dv.groupby("instrument_id")["volume"].max()
real_iids = maxday[maxday >= 100_000].index
last_sess = dv.groupby("instrument_id")["sess"].max()
data_end = dv["sess"].max()
dmap = {}
for iid in real_iids:
    mo = MCODE[sym[iid][2]]
    ls = last_sess[iid]
    yy = ls.year + (1 if mo < ls.month else 0)
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
front = pd.Series(front, index=piv.index)
m = m[m["instrument_id"].map(dmap) == m["sess"].map(dict(zip(piv.index, front)))]
m = m.sort_values(["sess", "minute_of_day"], kind="stable")
m["close"] = m["close"] / NS
m["lret"] = np.log(m["close"]).groupby(m["sess"]).diff()
mind = m.set_index(["sess", "minute_of_day"])[["volume", "lret"]]
have_sessions = set(mind.index.get_level_values(0))

# day-level table (RTH vol + range needs highs/lows -> reload minimal)
rows2 = []
for fp in chunks:
    d = pd.read_parquet(fp, columns=["instrument_id", "raw_symbol", "ts_event",
                                     "high", "low", "volume"])
    rows2.append(d[d["raw_symbol"].str.match(PAT)])
h = pd.concat(rows2, ignore_index=True)
del rows2
chi2 = pd.DatetimeIndex(pd.to_datetime(h["ts_event"].to_numpy(), utc=True)) \
        .tz_convert("America/Chicago")
h["hhmm"] = chi2.hour * 100 + chi2.minute
h["sess"] = chi2 + pd.to_timedelta((chi2.hour >= 17).astype("int32"), unit="D")
h["sess"] = pd.DatetimeIndex(h["sess"]).normalize().tz_localize(None)
h = h[(h["hhmm"] >= 830) & (h["hhmm"] < 1600)]
h = h[h["instrument_id"].map(dmap) == h["sess"].map(dict(zip(piv.index, front)))]
rthd = h.groupby("sess").agg(vol_rth=("volume", "sum"), hi=("high", "max"),
                             lo=("low", "min")).reset_index().set_index("sess")
rthd["range"] = (rthd["hi"] - rthd["lo"]) / NS
rthd["vol_med20"] = rthd["vol_rth"].rolling(20, min_periods=10).median().shift(1)
rthd["range_med20"] = rthd["range"].rolling(20, min_periods=10).median().shift(1)

# --------------------------------------------------------------- events
fomc_days = set(E["sess"])
E["in_data"] = E["sess"].isin(set(piv.index))
ev_timed = E[E["in_data"] & E["time_et"].notna()].copy()
ev_timed["rel_min_chi"] = ev_timed["time_et"].apply(
    lambda t: (t[0] - 1) * 60 + t[1])
print(f"in-data statements: {int(E['in_data'].sum())} | timed in-data: {len(ev_timed)} "
      f"| untimed in-data: {int((E['in_data'] & E['time_et'].isna()).sum())}")

BINS = list(range(-120, 181, 15))

def bucket_profile(sess_list, anchor_rel):
    prof = {b: {"vol": [], "absr": []} for b in BINS[:-1]}
    for s in sess_list:
        if s not in have_sessions:
            continue
        day = mind.xs(s)
        rel = anchor_rel(s)
        off = day.index - rel
        for b in BINS[:-1]:
            sel = (off >= b) & (off < b + 15)
            if sel.sum() == 0:
                continue
            prof[b]["vol"].append(float(day.loc[sel, "volume"].sum()))
            prof[b]["absr"].append(float(day.loc[sel, "lret"].abs().sum()))
    return {b: {"vol_median": float(np.median(v["vol"])) if v["vol"] else None,
                "absret_median": float(np.median(v["absr"])) if v["absr"] else None,
                "n": len(v["vol"])} for b, v in prof.items()}

ev_sessions = [s for s in ev_timed["sess"] if s in have_sessions]
print("timed event sessions with 1m data:", len(ev_sessions))
rel_map = dict(zip(ev_timed["sess"], ev_timed["rel_min_chi"]))
prof_fomc = bucket_profile(ev_sessions, lambda s: int(rel_map[s]))

fomc_plus1 = set(pd.Series(sorted(fomc_days & set(piv.index))) + pd.Timedelta(days=1))
base_sessions = [s for s in piv.index
                 if s.weekday() in (1, 2, 3) and s not in fomc_days
                 and s not in fomc_plus1 and s >= pd.Timestamp("2016-01-27")]
prof_base = bucket_profile(base_sessions, lambda s: 13 * 60)

ratio_vol = {b: (prof_fomc[b]["vol_median"] / prof_base[b]["vol_median"]
                 if prof_fomc[b]["vol_median"] and prof_base[b]["vol_median"] else None)
             for b in BINS[:-1]}
ratio_abs = {b: (prof_fomc[b]["absret_median"] / prof_base[b]["absret_median"]
                 if prof_fomc[b]["absret_median"] and prof_base[b]["absret_median"] else None)
             for b in BINS[:-1]}

# reaction timing
react = []
for s in ev_sessions:
    day = mind.xs(s)
    rel = int(rel_map[s])
    off = day.index - rel
    sel = day[(off >= 0) & (off <= 30)]
    if len(sel):
        react.append(int(sel["volume"].idxmax() - rel))
react_stats = {"n": len(react),
               "median": float(np.median(react)),
               "share_0_1": float(np.mean([r in (0, 1) for r in react])),
               "share_le5": float(np.mean([r <= 5 for r in react]))}

# quieting
quiet = []
for s in ev_sessions:
    day = mind.xs(s)
    rel = int(rel_map[s])
    off = day.index - rel
    a = day.loc[(off >= -30) & (off < 0), "volume"].sum()
    b = day.loc[(off >= -120) & (off < -30), "volume"].sum()
    if b > 0:
        quiet.append(float(a / (b / 90 * 30)))

# day-level
dd = rthd[rthd.index.isin(fomc_days)].dropna(subset=["vol_med20"])
base_d = rthd[~rthd.index.isin(fomc_days) & (rthd.index >= "2011-01-01")].dropna(
    subset=["vol_med20"])
day_level = {
    "fomc_rth_vol_ratio": {"n": int(len(dd)),
        "median": float((dd["vol_rth"] / dd["vol_med20"]).median()),
        "p25": float((dd["vol_rth"] / dd["vol_med20"]).quantile(.25)),
        "p75": float((dd["vol_rth"] / dd["vol_med20"]).quantile(.75))},
    "fomc_range_ratio": {"n": int(len(dd)),
        "median": float((dd["range"] / dd["range_med20"]).median())},
    "baseline_rth_vol_ratio": {"n": int(len(base_d)),
        "median": float((base_d["vol_rth"] / base_d["vol_med20"]).median())},
    "baseline_range_ratio": {"n": int(len(base_d)),
        "median": float((base_d["range"] / base_d["range_med20"]).median())},
}

pre = [ratio_vol[b] for b in (-120, -105, -90, -75, -60, -45, -30, -15)]
out = {
    "statement_inventory": {
        "total_files": len(files), "a_files": len(a_files), "bc_files": len(bc_files),
        "a_timed": int(len(timed)), "a_untimed": int(len(E) - len(timed)),
        "at_1400ET": int(len(at_1400)),
        "irregular": [{"date": r.date, "time_et": list(r.time_et)} for r in irregular.itertuples()],
        "in_data": int(E["in_data"].sum()),
        "timed_in_data_with_1m": len(ev_sessions),
        "files_with_clock_text_all": all_timed,
        "bc_with_clock_text": bc_timed},
    "calendar_reconciliation": {
        "calendar_dates_2011_2026": len(mtgs_2011_2026),
        "calendar_dates_2011_2015": len(mtgs_2011_2015),
        "meetings_missing_statement": missing,
        "statements_off_calendar": len(extra)},
    "minute_ratios": {
        "ratio_vol": {str(b): (round(v, 3) if v else None) for b, v in ratio_vol.items()},
        "ratio_absret": {str(b): (round(v, 3) if v else None) for b, v in ratio_abs.items()},
        "pre_release_range_120_to_15": [round(min(pre), 3), round(max(pre), 3)],
        "release_bucket": round(ratio_vol[0], 3),
        "release_absret": round(ratio_abs[0], 3),
        "bucket_30": round(ratio_vol[30], 3)},
    "reaction": react_stats,
    "quiet_median": float(np.median(quiet)),
    "day_level": day_level,
}
with open(os.path.join(HERE, "r3_fomc.json"), "w") as f:
    json.dump(out, f, indent=1)
print(json.dumps({k: out[k] for k in ("minute_ratios", "reaction", "day_level")},
                 indent=1))
print("quiet median:", out["quiet_median"])
print("WROTE r3_fomc.json")
