#!/usr/bin/env python
"""ES deep-research v2 — A4 FOMC event-day anatomy (lane DEEP-ES).

Release-time-anchored volume/vol/range TIMING descriptives on FOMC statement
days using the as-issued statements downloaded to
~/.my-quantitative-data/futures-nonprice-10syms/fed/statements/ (primary
artifact, as-downloaded 2026-10-02).

LAWS COMPLIANCE: NO conditional mean-return tables; nothing here ranks or
selects signals; no returns are averaged or compared across event subsets.
Only volume / volatility / range timing anatomy.

Release times: parsed from "For release at H:MM p.m. EST/EDT" in the
statement HTML (2016-01-27 onward, 92 statements incl. 7 intermeeting/irregular
times; each anchored at its OWN parsed time). 2011-2015 statements carry
"For immediate release" with no clock time in the artifact -> minute-anchored
anatomy NOT_RUN for those 40; day-level anatomy still computed.

Baseline: same-year Wednesdays (and the same weekday as the event when not
Wednesday) excluding FOMC-statement days and the session after them. Front
contract = VOL chain (strict past).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python ES_fomc.py
"""
import glob
import json
import os
import re
from datetime import datetime

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "ES_cache")
STMT = os.path.expanduser(
    "~/.my-quantitative-data/futures-nonprice-10syms/fed/statements")

m = pd.read_parquet(os.path.join(CACHE, "es_1m_seg.parquet"))
ch = pd.read_parquet(os.path.join(CACHE, "es_chain_VOL.parquet")).sort_index()
m = m.merge(ch.reset_index()[["sess", "front"]], on="sess")
m = m[m["delivery"] == m["front"]]
m["minute_of_day"] = m["chi"].dt.hour * 60 + m["chi"].dt.minute
m["lret"] = np.log(m["close"]).diff()          # within-session contiguous
m = m.sort_values(["sess", "minute_of_day"])

# ------------------------------------------------------------- statements
evs = []
for f in sorted(glob.glob(os.path.join(STMT, "monetary*a.html"))):
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
# FOMC statement session must exist in the trading calendar
have = set(ch.index)
E["in_data"] = E["sess"].isin(have)
# release minute in Chicago clock: ET is always CT+1h (both shift DST together)
E["rel_min_chi"] = E["time_et"].apply(
    lambda t: None if t is None else (t[0] - 1) * 60 + t[1])
E["dow"] = E["sess"].dt.dayofweek

fomc_days = set(E.loc[E["in_data"], "sess"])
ev_timed = E[E["in_data"] & E["rel_min_chi"].notna()].copy()
print("statements in data:", int(E["in_data"].sum()),
      "| timed (2016+):", len(ev_timed),
      "| untimed (2011-15):", int((E["in_data"] & E["rel_min_chi"].isna()).sum()))

sess_minutes = dict(tuple(g[["minute_of_day", "volume", "lret", "high", "low"]]
                          .set_index("minute_of_day").itertuples(name=None))
                    for g in m.groupby("sess")) if False else None

# minute-level frame indexed (sess, minute_of_day)
mind = m.set_index(["sess", "minute_of_day"])[["volume", "lret", "high", "low"]]
have_sessions = set(mind.index.get_level_values(0))

# --------------------------------------------- day-level anatomy (all 132)
cd = pd.read_parquet(os.path.join(CACHE, "es_contract_daily.parquet"))
cd["sess"] = pd.to_datetime(cd["sess"])
cd = cd.merge(ch.reset_index()[["sess", "front"]], on="sess")
cdf = cd[cd["delivery"] == cd["front"]].set_index("sess").sort_index()
cdf["rth_vol_med20"] = cdf["vol_rth"].rolling(20, min_periods=10).median().shift(1)
cdf["range"] = cdf["hi_rth"] - cdf["lo_rth"]
cdf["range_med20"] = cdf["range"].rolling(20, min_periods=10).median().shift(1)
cdf["day"] = cdf.index
cdf["is_fomc"] = cdf.index.isin(fomc_days)
cdf["year"] = cdf.index.year

day_rows = []
for sess, r in cdf[cdf["is_fomc"]].iterrows():
    day_rows.append({
        "date": sess.date().isoformat(),
        "timed": bool(sess in set(ev_timed["sess"])),
        "rth_vol_ratio": float(r["vol_rth"] / r["rth_vol_med20"]),
        "range_ratio": float(r["range"] / r["range_med20"]),
    })
DD = pd.DataFrame(day_rows)
base = cdf[~cdf["is_fomc"] & (cdf.index >= "2011-01-01")]
def ratio_stats(x):
    x = x.dropna()
    return {"n": int(len(x)), "median": float(x.median()),
            "p25": float(x.quantile(.25)), "p75": float(x.quantile(.75))}
day_level = {
    "fomc_rth_vol_ratio": ratio_stats(DD["rth_vol_ratio"]),
    "fomc_range_ratio": ratio_stats(DD["range_ratio"]),
    "baseline_rth_vol_ratio": ratio_stats(base["vol_rth"] / base["rth_vol_med20"]),
    "baseline_range_ratio": ratio_stats(base["range"] / base["range_med20"]),
    "fomc_timed_only_rth_vol_ratio": ratio_stats(DD.loc[DD["timed"], "rth_vol_ratio"]),
    "fomc_2011_2015_rth_vol_ratio": ratio_stats(DD.loc[~DD["timed"], "rth_vol_ratio"]),
}

# ------------------------------- minute-anchored anatomy (timed, 2016-2026)
BINS = list(range(-120, 181, 15))          # 15-minute buckets around release

def bucket_profile(sess_list, anchor="rel"):
    """median per-bucket volume and |lret| across sessions, anchored at each
    session's release minute (or 13:00 CT for baselines)."""
    prof = {b: {"vol": [], "absr": []} for b in BINS[:-1]}
    for s in sess_list:
        if s not in have_sessions:
            continue
        day = mind.xs(s)
        rel = int(ev_timed.loc[ev_timed["sess"] == s, "rel_min_chi"].iloc[0]) \
            if anchor == "rel" else 13 * 60
        off = day.index - rel
        for b in BINS[:-1]:
            sel = (off >= b) & (off < b + 15)
            if sel.sum() == 0:
                continue
            prof[b]["vol"].append(float(day.loc[sel, "volume"].sum()))
            prof[b]["absr"].append(float(day.loc[sel, "lret"].abs().sum()))
    return {b: {"vol_median": float(np.median(v["vol"])) if v["vol"] else None,
                "absret_median": float(np.median(v["absr"])) if v["absr"] else None,
                "n": len(v["vol"])}
            for b, v in prof.items()}

ev_sessions = [s for s in ev_timed["sess"]]
ev_sessions = [s for s in ev_sessions if s in have_sessions]
print("timed event sessions with 1m data:", len(ev_sessions))
prof_fomc = bucket_profile(ev_sessions, "rel")

# baseline: same weekday, same year, non-FOMC, excluding day-after-FOMC
fomc_plus1 = set(pd.Series(sorted(fomc_days)) + pd.Timedelta(days=1))
base_sessions = [s for s in ch.index
                 if s.weekday() in (1, 2, 3) and s not in fomc_days
                 and s not in fomc_plus1 and s >= pd.Timestamp("2016-01-27")]
prof_base = bucket_profile(base_sessions, "fixed13")

minute_profile = {
    "event": {str(b): v for b, v in prof_fomc.items()},
    "baseline_wed13": {str(b): v for b, v in prof_base.items()},
    "ratio_vol": {str(b): (prof_fomc[b]["vol_median"] / prof_base[b]["vol_median"]
                           if prof_fomc[b]["vol_median"] and prof_base[b]["vol_median"]
                           else None) for b in BINS[:-1]},
    "ratio_absret": {str(b): (prof_fomc[b]["absret_median"] / prof_base[b]["absret_median"]
                              if prof_fomc[b]["absret_median"] and prof_base[b]["absret_median"]
                              else None) for b in BINS[:-1]},
}

# reaction-minute timing: minute of max volume within [+0,+30] per event
react = []
for s in ev_sessions:
    day = mind.xs(s)
    rel = int(ev_timed.loc[ev_timed["sess"] == s, "rel_min_chi"].iloc[0])
    off = day.index - rel
    sel = day[(off >= 0) & (off <= 30)]
    if len(sel):
        react.append(int(sel["volume"].idxmax() - rel))
react_stats = {
    "n": len(react),
    "median_argmax_vol_offset_min": float(np.median(react)),
    "share_argmax_within_5min": float(np.mean([r <= 5 for r in react])),
    "share_argmax_at_0_or_1": float(np.mean([r in (0, 1) for r in react])),
}

# pre-release quieting: [-30,0) volume vs [-120,-30) volume per event
quiet = []
for s in ev_sessions:
    day = mind.xs(s)
    rel = int(ev_timed.loc[ev_timed["sess"] == s, "rel_min_chi"].iloc[0])
    off = day.index - rel
    a = day.loc[(off >= -30) & (off < 0), "volume"].sum()
    b = day.loc[(off >= -120) & (off < -30), "volume"].sum()
    if b > 0:
        quiet.append(float(a / (b / 90 * 30)))   # rate-normalized ratio
quiet_stats = {"n": len(quiet), "median_30min_before_vs_prior90_rate": float(np.median(quiet))}

out = {
    "generated_utc": datetime.utcnow().isoformat() + "+00:00",
    "n_statements_total": int(len(E)),
    "n_in_data": int(E["in_data"].sum()),
    "n_timed_2016_2026": int(len(ev_timed)),
    "n_untimed_2011_2015_NOT_RUN_minute": int((E["in_data"] & E["rel_min_chi"].isna()).sum()),
    "release_time_note": ("times parsed from as-issued statement HTML 'For "
                          "release at'; 85 scheduled at 14:00 ET, 7 irregular "
                          "(2019-10-11 11:00, 2020-03-03 10:00, 2020-03-15 "
                          "17:00 Sun, 2020-03-23 08:00, 2020-03-31 08:30, "
                          "2020-08-27 09:10, 2025-08-22 10:00)"),
    "day_level": day_level,
    "minute_profile_15min_buckets": minute_profile,
    "reaction_timing": react_stats,
    "pre_release_quieting": quiet_stats,
    "law_compliance": ("volume/vol/range timing only; NO mean-return tables; "
                       "no signal ranking; thresholds strict-past (20-session "
                       "trailing medians)"),
    "per_event_day_level": day_rows,
}
with open(os.path.join(HERE, "ES_fomc_stats.json"), "w") as f:
    json.dump(out, f, indent=1)

print(json.dumps(day_level, indent=1))
print("reaction:", react_stats)
print("quiet:", quiet_stats)
for b in BINS[:-1]:
    print(f"bucket {b:+4d}: vol_med={prof_fomc[b]['vol_median']:8.0f} "
          f"base={prof_base[b]['vol_median']:8.0f} "
          f"ratio={minute_profile['ratio_vol'][str(b)]:6.2f} "
          f"|r| ratio={minute_profile['ratio_absret'][str(b)] if minute_profile['ratio_absret'][str(b)] else float('nan'):6.2f}")
print("WROTE ES_fomc_stats.json")
