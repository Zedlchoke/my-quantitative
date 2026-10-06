"""6B v2 a6 — gilt-curve coupling (BoE GLC nominal spot curve 2016-2024 local
copy): mini-budget 2022 episode anatomy, era drift of 6B-vs-gilt correlation.
DECLARED_LAG caveat: gilt data PIT-known only >=1 business day after obs date;
descriptive contemporaneous associations only. Emits 6B_a6_gilts.json."""
from __future__ import annotations

import importlib.util
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "six_b_deep_lib", os.path.join(HERE, "6B_deep_lib.py"))
lib = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lib)

OUT = {}

g = lib.load_gilt_curve()
g["d"] = pd.to_datetime(g["date"])
wide = g.pivot_table(index="d", columns="tenor", values="yield")
for t in (1.0, 2.0, 5.0, 10.0):
    if t in wide.columns:
        wide[f"g{int(t)}"] = wide[t]
gilts = wide[[c for c in ("g1", "g2", "g5", "g10") if c in wide.columns]].copy()
OUT["gilt_coverage"] = {
    "span": [str(gilts.index.min().date()), str(gilts.index.max().date())],
    "n_days": int(len(gilts)),
    "source_file": "glcnominalddata.zip -> GLC Nominal daily data_2016 to 2024.xlsx "
                   "(sheet '4. spot curve'), local copy updated 2025-01-21",
    "declared_lag_note": "BoE yield-curve data published with declared lag; "
                         "PIT-usable only >=1 business day after observation",
}

chain = pd.read_parquet(os.path.join(lib.CACHE, "chain_calendar.parquet"))
chain["d"] = pd.to_datetime(chain["session_date"])
c = chain[["d", "close", "ret", "volume"]].dropna(subset=["ret"])

m = c.merge(gilts[["g2", "g10"]], left_on="d", right_index=True, how="inner")
m["dg2"] = m["g2"].diff()
m["dg10"] = m["g10"].diff()
m = m.dropna(subset=["dg10"])

# era correlations: 6B daily ret vs gilt yield changes (descriptive)
OUT["era_corr_6b_vs_gilts"] = {}
for y0, y1, name in [(2020, 2020, "2020"), (2021, 2021, "2021"),
                     (2022, 2022, "2022"), (2023, 2023, "2023"),
                     (2024, 2024, "2024")]:
    s = m[(m["d"].dt.year >= y0) & (m["d"].dt.year <= y1)]
    OUT["era_corr_6b_vs_gilts"][name] = {
        "n": int(len(s)),
        "corr_ret_dg2": float(s["ret"].corr(s["dg2"])),
        "corr_ret_dg10": float(s["ret"].corr(s["dg10"])),
    }
# full-sample and rolling 63d corr of ret vs dg10
OUT["full_corr_ret_dg10"] = float(m["ret"].corr(m["dg10"]))
m["rc63"] = m["ret"].rolling(63).corr(m["dg10"])
rc = m["rc63"].dropna()
OUT["rolling63_corr_ret_dg10"] = {
    "min": float(rc.min()), "q25": float(rc.quantile(.25)),
    "median": float(rc.median()), "q75": float(rc.quantile(.75)),
    "max": float(rc.max()),
    "min_date": str(m.loc[rc.idxmin(), "d"].date()),
    "max_date": str(m.loc[rc.idxmax(), "d"].date()),
}

# ---- mini-budget episode table -------------------------------------------------
ep = m[(m["d"] >= "2022-09-20") & (m["d"] <= "2022-10-17")]
OUT["mini_budget_episode"] = [
    {"date": str(t.d.date()), "ret_pct": round(float(t.ret) * 100, 3),
     "dg2_bp": round(float(t.dg2) * 100, 1), "dg10_bp": round(float(t.dg10) * 100, 1),
     "g2_lvl": round(float(t.g2), 3), "g10_lvl": round(float(t.g10), 3),
     "volume": int(t.volume)}
    for t in ep.itertuples()]
ep2 = ep[(ep["d"] >= "2022-09-23") & (ep["d"] <= "2022-09-28")]
OUT["mini_budget_coupling"] = {
    "n_days": int(len(ep2)),
    "corr_ret_dg10": float(ep2["ret"].corr(ep2["dg10"])) if len(ep2) > 2 else None,
    "note": "2022-09-23 (mini-budget Friday) through 2022-09-28",
}
# gilt-curve stress days (|dg10| > 3 sd of 2022) vs 6B same-day |ret|
sd10 = m[m["d"].dt.year == 2022]["dg10"].std()
stress = m[(m["d"].dt.year == 2022) & (m["dg10"].abs() > 2 * sd10)]
calm = m[(m["d"].dt.year == 2022) & (m["dg10"].abs() < 0.5 * sd10)]
OUT["gilt_stress_days_2022"] = {
    "sd_dg10_bp": float(sd10 * 100),
    "n_stress": int(len(stress)), "n_calm": int(len(calm)),
    "median_absret_stress_pct": float(stress["ret"].abs().median() * 100),
    "median_absret_calm_pct": float(calm["ret"].abs().median() * 100),
    "stress_dates": [str(x.date()) for x in stress["d"]],
}

lib.jdump(OUT, os.path.join(HERE, "6B_a6_gilts.json"))
print("a6 done. era corr dg10:", {k: round(v['corr_ret_dg10'], 3)
      for k, v in OUT['era_corr_6b_vs_gilts'].items()})
print("rolling63 min/max:", OUT["rolling63_corr_ret_dg10"]["min"],
      OUT["rolling63_corr_ret_dg10"]["max"])
