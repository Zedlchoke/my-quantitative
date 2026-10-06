#!/usr/bin/env python
"""ES deep-research v2 — A5 CoT positioning vs subsequent realized vol/drawdown
(lane DEEP-ES).

CFTC CoT legacy "E-MINI S&P 500" (COT_LEGACY_ES) as-published weekly table
(positions as of Tuesday, released Friday 15:30 ET — PIT lag honored: forward
windows start the session AFTER the release session). 2006-12 -> 2026-09.

DESCRIPTIVE ONLY and NO forward-return tables: outcomes are subsequent
realized VOLATILITY and DRAWDOWN (risk anatomy), never mean returns; nothing
is ranked as a signal. Positioning percentile/z-scores use TRAILING windows
only (strict past).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python ES_cot.py
"""
import json
import os
from datetime import datetime

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "ES_cache")

cot = pd.read_parquet(os.path.expanduser(
    "~/.my-quantitative-data/futures-nonprice-10syms/normalized/cftc_legacy_tidy.parquet"))
cot = cot[cot["series_id"] == "COT_LEGACY_ES"].copy()
# DATA-QUALITY (found 2026-10-02): series_id COT_LEGACY_ES in the normalized
# tidy table mixes 3 CFTC markets whose names contain "E-MINI S&P 500" or the
# consolidated complex (contaminants OI ~100-460k vs true ES ~1.4-3.0M).
# Keep ONLY the exact E-mini outright market names:
cot["mn"] = cot["market_name"].str.strip()
cot = cot[cot["mn"].isin([
    "E-MINI S&P 500 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE",
    "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE"])]
assert cot.duplicated("observation_period").sum() == 0, "weekly dup after filter"
cot["obs"] = pd.to_datetime(cot["observation_period"])
cot["rel"] = pd.to_datetime(cot["released_at"].str.split("/").str[0])
cot = cot.sort_values("rel").reset_index(drop=True)
cot["net_noncomm"] = cot["noncomm_long"] - cot["noncomm_short"]
cot["net_comm"] = cot["comm_long"] - cot["comm_short"]
cot["net_spec_share"] = cot["net_noncomm"] / cot["open_interest_all"]
print("CoT rows:", len(cot), cot["obs"].min().date(), "->", cot["obs"].max().date())

# chain for forward outcomes
ch = pd.read_parquet(os.path.join(CACHE, "es_chain_VOL.parquet")).sort_index()
ch["lret"] = np.log(ch["close_adj"]).diff()
sess = list(ch.index)
pos_of = {s.date(): i for i, s in enumerate(sess)}

def fwd_window(rel_ts, n):
    """sessions strictly after the release session, next n of them."""
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
    rv21 = float(np.sqrt((r["lret"] ** 2).sum() * 252 / len(win)) * 100)
    px = r["close_adj"]
    dd = float((px / px.cummax() - 1).min() * 100)
    return rv21, dd

# trailing percentile (strict past: prior releases only), 3y window
rows = []
vals = cot["net_noncomm"].values.astype(float)
rels = cot["rel"]
for k in range(len(cot)):
    if k < 156:                       # need >=3y of history
        continue
    w = vals[max(0, k - 156):k]
    v = vals[k]
    pct = float((w < v).mean())
    mu, sd = float(np.mean(w)), float(np.std(w))
    win21 = fwd_window(rels.iloc[k], 21)
    win63 = fwd_window(rels.iloc[k], 63)
    if win21 is None:
        continue
    rv21, dd21 = outcome(win21)
    rv63, dd63 = outcome(win63) if win63 is not None else (None, None)
    rows.append({
        "rel": rels.iloc[k].date().isoformat(),
        "net_noncomm": int(v),
        "oi": int(cot["open_interest_all"].iloc[k]),
        "trailing_pctl": pct,
        "trailing_z": (v - mu) / sd if sd > 0 else None,
        "fwd_rv21_pct": rv21, "fwd_dd21_pct": dd21,
        "fwd_rv63_pct": rv63, "fwd_dd63_pct": dd63,
    })
F = pd.DataFrame(rows)
print("usable releases:", len(F))

# quintile buckets on trailing percentile
F["q"] = pd.cut(F["trailing_pctl"], [0, .2, .4, .6, .8, 1.0],
               labels=["Q1 most-short", "Q2", "Q3", "Q4", "Q5 most-long"])
bucket = F.groupby("q", observed=True).agg(
    n=("net_noncomm", "size"),
    net_pos_median=("net_noncomm", "median"),
    fwd_rv21_median=("fwd_rv21_pct", "median"),
    fwd_rv63_median=("fwd_rv63_pct", "median"),
    fwd_dd21_median=("fwd_dd21_pct", "median"),
    fwd_dd63_median=("fwd_dd63_pct", "median"),
).round(2)

# extreme tails (trailing deciles)
t_low = F[F["trailing_pctl"] <= 0.1]
t_high = F[F["trailing_pctl"] >= 0.9]
tails = {
    "most_short_decile": {"n": len(t_low),
        "net_pos_median": float(t_low["net_noncomm"].median()),
        "fwd_rv21_median": float(t_low["fwd_rv21_pct"].median()),
        "fwd_dd21_median": float(t_low["fwd_dd21_pct"].median()),
        "fwd_dd63_median": float(t_low["fwd_dd63_pct"].median()),
        "example_releases": list(t_low.nsmallest(5, "trailing_pctl")["rel"])},
    "most_long_decile": {"n": len(t_high),
        "net_pos_median": float(t_high["net_noncomm"].median()),
        "fwd_rv21_median": float(t_high["fwd_rv21_pct"].median()),
        "fwd_dd21_median": float(t_high["fwd_dd21_pct"].median()),
        "fwd_dd63_median": float(t_high["fwd_dd63_pct"].median()),
        "example_releases": list(t_high.nlargest(5, "trailing_pctl")["rel"])},
}

# positioning level by year (descriptive drift of hedging structure)
cot["year"] = cot["obs"].dt.year
by_year = cot.groupby("year").agg(
    n=("net_noncomm", "size"),
    net_noncomm_median=("net_noncomm", "median"),
    net_comm_median=("net_comm", "median"),
    oi_median=("open_interest_all", "median"),
).round(0).reset_index()

# crisis anchors: trailing percentile at notable stress onsets
anchors = {}
for label, d in [("GFC tail 2009", "2009-03-01"), ("Aug-2011", "2011-08-01"),
                 ("COVID 2020-03", "2020-03-01"), ("2022 bear", "2022-01-01"),
                 ("2025-04 tariff", "2025-04-01")]:
    sub = F[F["rel"] >= d].head(1)
    if len(sub):
        anchors[label] = {"rel": sub["rel"].iloc[0],
                          "trailing_pctl": round(float(sub["trailing_pctl"].iloc[0]), 3),
                          "fwd_rv21": sub["fwd_rv21_pct"].iloc[0]}

# rank correlation positioning-vs-forward-vol (descriptive, NOT a signal);
# Spearman = Pearson on ranks (pandas corr on rank series; no scipy needed)
if F["fwd_rv63_pct"].notna().sum() > 100:
    rho_rv = float(F["trailing_pctl"].rank().corr(F["fwd_rv63_pct"].rank()))
else:
    rho_rv = None

out = {
    "generated_utc": datetime.utcnow().isoformat() + "+00:00",
    "series": "COT legacy E-MINI S&P 500 (CME), as_published_no_revision",
    "pit": "positions Tuesday; released Friday 15:30 ET; forward windows start next session",
    "n_usable_releases": int(len(F)),
    "window": [F["rel"].min(), F["rel"].max()],
    "quintile_buckets": bucket.reset_index().to_dict(orient="records"),
    "extreme_deciles": tails,
    "net_position_by_year": by_year.to_dict(orient="records"),
    "crisis_anchors": anchors,
    "spearman_trailingpctl_fwd_rv63": {"rho": None if rho_rv is None else float(rho_rv),
                                        "n": int(F["fwd_rv63_pct"].notna().sum())},
    "law_compliance": ("forward VOLATILITY/DRAWDOWN outcomes only; no forward "
                       "mean-return tables; trailing percentiles strict-past"),
}
with open(os.path.join(HERE, "ES_cot_stats.json"), "w") as f:
    json.dump(out, f, indent=1, default=str)
print(bucket.to_string())
print(json.dumps(tails, indent=1))
print("spearman:", out["spearman_trailingpctl_fwd_rv63"])
print("WROTE ES_cot_stats.json")
