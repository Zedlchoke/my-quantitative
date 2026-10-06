#!/usr/bin/env python
"""ES deep-research v2 — A3 term structure + roll descriptives (lane DEEP-ES).

Consumes ES_cache/es_roll_table.json (66 completed quarterly rolls 2010-06 ->
2026-09, from full per-contract 1m data: BOTH contracts' volumes observed
every session, unlike the v1 snapshot where the expired contract's file was
truncated at the declared roll date).

Adds: DECL-rule thin-window length per roll, T5-vs-crossover deviation,
carry-premium sign vs FRED DFF (latest-revised caveat disclosed; dividend
yield NOT in repo -> mechanism link stays POSTULATED), June-Juneteenth check,
chain-rule comparison stats.

DESCRIPTIVE ONLY. Outputs ES_roll_stats.json.

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python ES_roll_stats.py
"""
import json
import os
from datetime import datetime

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "ES_cache")

roll = pd.DataFrame(json.load(open(os.path.join(CACHE, "es_roll_table.json"))))
roll = roll[roll["volume_crossover_session"].notna()].copy()
roll["year"] = roll["old"].str[:4].astype(int)

# chain sessions for rule comparisons
vol = pd.read_parquet(os.path.join(CACHE, "es_chain_VOL.parquet")).sort_index()
t5 = pd.read_parquet(os.path.join(CACHE, "es_chain_T5.parquet")).sort_index()
dec = pd.read_parquet(os.path.join(CACHE, "es_chain_DECL.parquet")).sort_index()
sess = list(vol.index)
pos = {s.date(): i for i, s in enumerate(sess)}

def pday(x):
    return pd.Timestamp(x).date()

# per-roll derived quantities
rows = []
for _, r in roll.iterrows():
    cross = pday(r["volume_crossover_session"])
    sw_vol = pday(r["vol_chain_switch_session"])
    expd = pday(r["expiry_session"])
    # DECL switch session for this old delivery: first session where DECL
    # chain leaves this delivery
    dswitch = dec.index[(dec["front"] == r["new"]) &
                        (dec["front"].shift() == r["old"])]
    dswitch = pday(dswitch[0]) if len(dswitch) else None
    t5switch = t5.index[(t5["front"] == r["new"]) &
                        (t5["front"].shift() == r["old"])]
    t5switch = pday(t5switch[0]) if len(t5switch) else None
    thin_len = None
    if dswitch is not None:
        thin_len = pos[cross] - pos[dswitch] if cross in pos and dswitch in pos else None
    rows.append({
        "old": r["old"], "new": r["new"], "year": r["year"],
        "quarter": r["old"][5:7],
        "expiry": r["expiry_session"],
        "volume_crossover": r["volume_crossover_session"],
        "sessions_cross_before_expiry": (pos[expd] - pos[cross]) if expd in pos and cross in pos else None,
        "spread_pts": r["calendar_spread_at_crossover"],
        "spread_pct_quarter": (r["calendar_spread_at_crossover"] /
                               r.get("old_level", np.nan)) if pd.notna(r["calendar_spread_at_crossover"]) else None,
        "unadjusted_jump": r["unadjusted_switch_jump"],
        "new_share_last8": r["new_share_last8_mean"],
        "oi_crossover": r["oi_crossover_session"],
        "decl_switch": dswitch.isoformat() if dswitch else None,
        "decl_thin_window_sessions": thin_len,
        "t5_switch": t5switch.isoformat() if t5switch else None,
        "t5_minus_crossover_sessions": (pos[t5switch] - pos[cross]) if t5switch and t5switch in pos and cross in pos else None,
    })
R = pd.DataFrame(rows)

# old contract level (for % premium): close of old at crossover-1 from cd
cd = pd.read_parquet(os.path.join(CACHE, "es_contract_daily.parquet"))
cd["sess"] = pd.to_datetime(cd["sess"])
lvl = {}
for _, r in R.iterrows():
    if not r["volume_crossover"]:
        continue
    d = pd.Timestamp(r["volume_crossover"])
    sub = cd[(cd["delivery"] == r["old"]) & (cd["sess"] < d)].sort_values("sess")
    if len(sub):
        lvl[r["old"]] = float(sub["sess_close"].iloc[-1])
R["old_level_at_roll"] = R["old"].map(lvl)
R["spread_pct_quarter"] = R["spread_pts"] / R["old_level_at_roll"] * 100
R["spread_pct_annualized"] = R["spread_pct_quarter"] * 4

# FRED DFF (effective fed funds) — latest-revised, NOT PIT; era-sign check only
fr = pd.read_parquet(os.path.expanduser(
    "~/.my-quantitative-data/futures-nonprice-10syms/normalized/fred_latest_tidy.parquet"))
dff = fr[fr["series_id"] == "FRED_DFF"].copy()
dff["date"] = pd.to_datetime(dff["observation_period"])
dff = dff.set_index("date")["value"].astype(float)
R["dff_at_roll"] = [float(dff.asof(pd.Timestamp(c))) if c else None
                    for c in R["volume_crossover"]]
R["sign_match_dff"] = [
    (np.sign(s) == np.sign(d - 1.8)) if pd.notna(s) and d is not None else None
    for s, d in zip(R["spread_pts"], R["dff_at_roll"])]

# ---------------------------------------------------------------- summaries
def dist(x):
    x = pd.Series(x).dropna()
    if len(x) == 0:
        return None
    return {"n": int(len(x)), "mean": float(x.mean()), "median": float(x.median()),
            "min": float(x.min()), "max": float(x.max()),
            "p10": float(x.quantile(0.10)), "p90": float(x.quantile(0.90))}

by_year_spread = R.groupby("year").agg(
    n=("old", "size"),
    spread_median=("spread_pts", "median"),
    spread_min=("spread_pts", "min"),
    spread_max=("spread_pts", "max"),
    n_positive=("spread_pts", lambda s: int((s > 0).sum())),
    spread_ann_med=("spread_pct_annualized", "median"),
    dff_median=("dff_at_roll", "median"),
).reset_index()

june = R[R["quarter"] == "06"]
out = {
    "generated_utc": datetime.utcnow().isoformat() + "+00:00",
    "n_rolls": int(len(R)),
    "window": [R["old"].min(), R["old"].max()],
    "crossover_sessions_before_expiry": dist(R["sessions_cross_before_expiry"]),
    "t5_minus_crossover_sessions": dist(R["t5_minus_crossover_sessions"]),
    "abs_t5_dev_gt3_sessions": int((R["t5_minus_crossover_sessions"].abs() > 3).sum()),
    "decl_thin_window_sessions": dist(R["decl_thin_window_sessions"]),
    "spread_pts": dist(R["spread_pts"]),
    "spread_pct_annualized": dist(R["spread_pct_annualized"]),
    "n_spread_positive": int((R["spread_pts"] > 0).sum()),
    "n_spread_negative": int((R["spread_pts"] < 0).sum()),
    "sign_match_vs_DFF_minus_1p8": {
        "n": int(R["sign_match_dff"].dropna().astype(bool).count()),
        "n_match": int(R["sign_match_dff"].fillna(False).astype(bool).sum()),
        "note": ("DFF latest-revised NOT PIT; 1.8pp dividend-yield proxy is "
                 "a declared constant, NOT measured"),
    },
    "new_share_last8": dist(R["new_share_last8"]),
    "by_year": by_year_spread.to_dict(orient="records"),
    "june_rolls": june[["old", "expiry", "volume_crossover",
                        "sessions_cross_before_expiry"]].to_dict(orient="records"),
    "oi_crossover_vs_volume": R[R["oi_crossover"].notna()]
        [["old", "volume_crossover", "oi_crossover"]].to_dict(orient="records"),
    "rolls": R.drop(columns=["sign_match_dff"]).to_dict(orient="records"),
}
with open(os.path.join(HERE, "ES_roll_stats.json"), "w") as f:
    json.dump(out, f, indent=1, default=str)

print("rolls:", len(R))
print("crossover sessions before expiry:", out["crossover_sessions_before_expiry"])
print("t5 deviation:", out["t5_minus_crossover_sessions"],
      "| >3 sessions:", out["abs_t5_dev_gt3_sessions"])
print("decl thin window:", out["decl_thin_window_sessions"])
print("spread pts:", out["spread_pts"], "| pos/neg:", out["n_spread_positive"],
      "/", out["n_spread_negative"])
print("spread ann%:", out["spread_pct_annualized"])
print("sign match vs DFF-1.8:", out["sign_match_vs_DFF_minus_1p8"])
print(R[["old", "spread_pts", "spread_pct_annualized", "dff_at_roll"]].head(8).to_string())
print(R[["old", "spread_pts", "spread_pct_annualized", "dff_at_roll"]].tail(8).to_string())
print("WROTE ES_roll_stats.json")
