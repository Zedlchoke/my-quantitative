"""6B v2 a3 — term structure + roll: all quarterly rolls 2020-2026 (27),
liquidity migration (old-side now fully observable — dissolves v1's fetch-cut
NOT_RUN), roll-gap distribution vs BoE-Fed policy differential (CIP check,
vintage caveats), OI-based roll from GLBX statistics (2023-10+).
Emits 6B_a3_term.json."""
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
TICK = 0.0001

sess = pd.read_parquet(os.path.join(lib.CACHE, "6b_sessions.parquet"))
sess["d"] = pd.to_datetime(sess["session_date"])
reg_rows = lib.build_contract_registry(
    pd.read_parquet(os.path.join(lib.CACHE, "6b_outright_1m.parquet")))
reg = reg_rows[~reg_rows["stray"]].set_index("contract")["expiry"].to_dict()

contracts = [c for c in sess["contract"].unique() if lib._QRE.match(c)]
contracts.sort(key=lambda c: reg[c])
contracts = [c for c in contracts if reg.get(c)]

# ---- roll table ---------------------------------------------------------------
rolls = []
for i in range(len(contracts) - 1):
    old, new = contracts[i], contracts[i + 1]
    exp_old = pd.Timestamp(reg[old])
    dm_start = exp_old.replace(day=1)
    o = sess[sess["contract"] == old].sort_values("d")
    n = sess[sess["contract"] == new].sort_values("d")
    o_pre = o[o["d"] < dm_start]
    roll_date = o_pre["d"].max() if len(o_pre) else None
    if roll_date is None:
        continue
    o_close = float(o.loc[o["d"] == roll_date, "close"].iloc[0])
    nrow = n[n["d"] == roll_date]
    if not len(nrow):
        continue
    n_close = float(nrow["close"].iloc[0])
    gap = n_close - o_close
    # volume crossover: first session (>= roll_date-40) where next's trailing
    # 5-session mean volume > old's trailing 5-session mean (PIT at close)
    ov = o.set_index("d")["volume"]
    nv = n.set_index("d")["volume"]
    idx = ov.index.union(nv.index)
    wide = pd.DataFrame({"old": ov.reindex(idx), "new": nv.reindex(idx)}).fillna(0)
    roll5 = wide.rolling(5, min_periods=1).mean()
    cross = roll5[roll5["new"] > roll5["old"]].index
    cross = [c for c in cross if c >= dm_start - pd.Timedelta(days=40)]
    cross_date = min(cross) if cross else None
    # old contract's last session + total volume inside its delivery month
    old_last = o["d"].max()
    o_dm = o[o["d"] >= dm_start]
    sessions_after_declared = None
    if cross_date is not None:
        sessions_after_declared = int(
            (o[(o["d"] > roll_date) & (o["d"] <= cross_date)]["d"].nunique())
            if cross_date > roll_date else 0)
    # both-sides real-activity check at roll session
    rolls.append({
        "old": old, "new": new,
        "declared_roll_session": str(roll_date.date()),
        "old_close": o_close, "new_close": n_close,
        "gap_usd": gap, "gap_ticks": round(gap / TICK, 1),
        "gap_pct_of_level": float(gap / o_close * 100),
        "old_vol_roll_session": int(ov.loc[roll_date]),
        "new_vol_roll_session": int(nv.loc[roll_date]),
        "volume_crossover_session": str(cross_date.date()) if cross_date is not None else None,
        "sessions_declared_to_crossover": sessions_after_declared,
        "old_last_session": str(old_last.date()),
        "old_vol_in_delivery_month": int(o_dm["volume"].sum()),
        "old_days_in_delivery_month": int(o_dm["d"].nunique()),
        "n_bars_old_at_roll": int(o.loc[o["d"] == roll_date, "n_bars"].iloc[0]),
        "n_bars_new_at_roll": int(nrow["n_bars"].iloc[0]),
    })

rolls = [r for r in rolls
         if r["declared_roll_session"] >= "2020-01-01"
         # genuine front-chain rolls only: old contract must have been a real
         # front (>=1000 contracts on the roll session, >=40 sessions of life)
         and r["old_vol_roll_session"] >= 1000
         and r["n_bars_old_at_roll"] >= 300]
OUT["n_rolls"] = len(rolls)
OUT["roll_table"] = rolls

g = np.array([r["gap_ticks"] for r in rolls])
OUT["roll_gap_dist_ticks"] = {
    "n": int(len(g)), "mean": float(g.mean()), "median": float(np.median(g)),
    "std": float(g.std()), "q05": float(np.quantile(g, .05)),
    "q25": float(np.quantile(g, .25)), "q75": float(np.quantile(g, .75)),
    "q95": float(np.quantile(g, .95)), "min": float(g.min()), "max": float(g.max()),
    "n_pos": int((g > 0).sum()), "n_neg": int((g < 0).sum()), "n_zero": int((g == 0).sum()),
}
gpct = np.array([r["gap_pct_of_level"] for r in rolls])
OUT["roll_gap_dist_pct"] = {
    "mean_pct": float(gpct.mean()), "std_pct": float(gpct.std()),
    "ann_per_roll_x4_pct": float(gpct.mean() * 4),
    "abs_mean_pct": float(np.abs(gpct).mean()),
}

# ---- policy differential at each roll (BoE latest vs Fed target upper) ---------
boe = lib.load_boe_bank_rate()[["obs", "value"]].rename(
    columns={"obs": "date", "value": "boe_rate"})
fed = lib.load_fred_latest("FRED_DFEDTARU")[["obs", "value"]].rename(
    columns={"obs": "date", "value": "fed_target_upper"})
fed["date"] = fed["date"].dt.tz_localize(None) if fed["date"].dt.tz is not None else fed["date"]
boe_step = boe.set_index("date")["boe_rate"].reindex(
    pd.date_range("2019-01-01", "2026-10-01"), method="ffill")
fed_step = fed.set_index("date")["fed_target_upper"].reindex(
    pd.date_range("2019-01-01", "2026-10-01"), method="ffill")
diff = (fed_step - boe_step)  # positive = US rates above UK

for r in rolls:
    dd = pd.Timestamp(r["declared_roll_session"])
    r["boe_rate"] = float(boe_step.loc[dd])
    r["fed_target_upper"] = float(fed_step.loc[dd])
    r["policy_diff_fed_minus_boe"] = float(diff.loc[dd])

x = np.array([r["policy_diff_fed_minus_boe"] for r in rolls])
ok = np.isfinite(x) & np.isfinite(g)
OUT["gap_vs_policy_diff"] = {
    "pearson_corr": float(np.corrcoef(x[ok], g[ok])[0, 1]),
    "spearman_corr": float(pd.Series(x[ok]).rank().corr(pd.Series(g[ok]).rank())),
    "mean_gap_ticks_when_diff_pos": float(g[ok & (x > 0)].mean()) if (ok & (x > 0)).any() else None,
    "mean_gap_ticks_when_diff_neg": float(g[ok & (x < 0)].mean()) if (ok & (x < 0)).any() else None,
    "n_diff_pos": int((ok & (x > 0)).sum()), "n_diff_neg": int((ok & (x < 0)).sum()),
    "vintage_note": ("BoE official_history_latest (revision-free levels); Fed "
                     "DFEDTARU FRED latest (not vintage-true PIT; ALFRED "
                     "year-end vintages exist only); levels are policy targets "
                     "known same-day, benign for descriptive CIP mapping"),
}
# CIP magnitude regression: gap_pct = a + b * diff; theory b ~ +1 per year of
# carry spread => per ~91d roll gap ≈ level * diff * 91/360 (ticks).
lvl = np.array([r["old_close"] for r in rolls])
b, a = np.polyfit(x[ok], gpct[ok], 1)
# FRED DFEDTARU is in PERCENT units -> /100 for fraction; theory ticks:
# gap = level * (r_US - r_UK) * (T_new - T_old)/360, ~91d quarter
theory = lvl[ok] * (x[ok] / 100.0) * (91 / 360) / TICK
OUT["cip_check"] = {
    "regression_gap_pct_on_diff_pp": {"slope_pct_per_pp": float(b), "intercept_pct": float(a)},
    "theory_pct_per_pp": float(100 * 91 / 360 * 0.01),
    "mean_realized_gap_ticks": float(g[ok].mean()),
    "mean_cip_predicted_gap_ticks": float(theory.mean()),
    "corr_realized_vs_cip_ticks": float(np.corrcoef(g[ok], theory)[0, 1]),
    "note": ("theory: next-quarterly premium = level*(r_US-r_UK)*(T_new-T_old)/360 "
             "approximated with 91d quarter; r_US=DFEDTARU (percent units, /100 "
             "applied), r_UK=Bank Rate (percent units, /100 applied)"),
}

# ---- migration timing distribution --------------------------------------------
sa = [r["sessions_declared_to_crossover"] for r in rolls if r["sessions_declared_to_crossover"] is not None]
OUT["migration"] = {
    "n": len(sa),
    "median_sessions_declared_to_crossover": float(np.median(sa)),
    "min": int(min(sa)), "max": int(max(sa)),
    "q25": float(np.quantile(sa, .25)), "q75": float(np.quantile(sa, .75)),
    "crossover_inside_delivery_month_frac": float(np.mean([
        pd.Timestamp(r["volume_crossover_session"]) >= pd.Timestamp(reg[r["old"]]).replace(day=1)
        for r in rolls if r["volume_crossover_session"]])),
    "old_vol_in_delivery_month_median": float(np.median(
        [r["old_vol_in_delivery_month"] for r in rolls])),
}
# old contract still trading at declared roll vs new: ratio distribution
ratios = [r["old_vol_roll_session"] / max(r["new_vol_roll_session"], 1) for r in rolls]
OUT["migration"]["old_over_new_vol_at_declared_roll_median"] = float(np.median(ratios))

# ---- OI-based roll vs volume crossover (statistics, 2023-10+) -------------------
stats = lib.load_statistics_6b()
stats["rd"] = pd.to_datetime(stats["ref_date"])
oi = stats[stats["stat_type"] == 9].copy()
oi_roll = []
for r in rolls:
    dd = pd.Timestamp(r["declared_roll_session"])
    if dd < pd.Timestamp("2023-12-01"):
        continue
    oo = oi[oi["raw_symbol"] == r["old"].split("_")[0]].sort_values("dt")
    oo = oo.drop_duplicates("rd", keep="last")
    nn = oi[oi["raw_symbol"] == r["new"].split("_")[0]].sort_values("dt")
    nn = nn.drop_duplicates("rd", keep="last")
    if not len(oo) or not len(nn):
        continue
    oi_o = oo.set_index("rd")["quantity"].sort_index()
    oi_n = nn.set_index("rd")["quantity"].sort_index()
    if oi_o.index.min() > dd or not len(oi_o):
        continue
    j = pd.DataFrame({
        "old_oi": oi_o.reindex(
            pd.date_range(dd - pd.Timedelta(days=45), dd + pd.Timedelta(days=30)),
            method="ffill"),
        "new_oi": oi_n.reindex(
            pd.date_range(dd - pd.Timedelta(days=45), dd + pd.Timedelta(days=30)),
            method="ffill")}).dropna()
    if not len(j):
        continue
    cross = j[j["new_oi"] > j["old_oi"]].index
    oi_roll.append({
        "old": r["old"], "new": r["new"],
        "oi_crossover": str(min(cross).date()) if len(cross) else None,
        "volume_crossover": r["volume_crossover_session"],
        "declared_roll": r["declared_roll_session"],
    })
OUT["oi_vs_volume_crossover"] = oi_roll
lag = [(pd.Timestamp(o["oi_crossover"]) - pd.Timestamp(o["volume_crossover"])).days
       for o in oi_roll if o["oi_crossover"] and o["volume_crossover"]]
OUT["oi_crossover_minus_volume_crossover_days"] = {
    "n": len(lag), "median": float(np.median(lag)), "min": int(min(lag)), "max": int(max(lag))}

# ---- calendar spread series (front minus next quarterly, real-activity days) ---
front = pd.read_parquet(os.path.join(lib.CACHE, "held_calendar.parquet"))
spread_rows = []
for i in range(len(contracts) - 1):
    old, new = contracts[i], contracts[i + 1]
    exp_old = pd.Timestamp(reg[old])
    o = sess[sess["contract"] == old].sort_values("d")
    n = sess[sess["contract"] == new].sort_values("d")
    dm = o[o["d"] >= exp_old - pd.Timedelta(days=120)]
    nn = n.set_index("d")
    for t in dm.itertuples():
        if t.d in nn.index and t.n_bars >= 30 and nn.loc[t.d, "n_bars"] >= 30:
            spread_rows.append({
                "date": t.d, "old": old, "new": new,
                "spread_usd": float(nn.loc[t.d, "close"] - t.close),
                "days_to_old_expiry": int((exp_old - t.d).days),
            })
sp = pd.DataFrame(spread_rows).sort_values("date")
sp.to_parquet(os.path.join(lib.CACHE, "calendar_spread_120d.parquet"), index=False)
OUT["calendar_spread_series"] = {
    "n_days": int(len(sp)),
    "span": [str(sp["date"].min().date()), str(sp["date"].max().date())],
    "median_abs_spread_ticks": float((sp["spread_usd"] / TICK).abs().median()),
    "corr_spread_with_policy_diff": float(
        sp.set_index("date")["spread_usd"].corr(
            diff.reindex(sp["date"]).reset_index(drop=True)))
    if len(sp) else None,
}
# by-year median spread sign
sp["year"] = sp["date"].dt.year
OUT["calendar_spread_median_ticks_by_year"] = {
    str(y): float(vv) for y, vv in (sp.groupby("year")["spread_usd"].median() / TICK).items()}

lib.jdump(OUT, os.path.join(HERE, "6B_a3_term.json"))
print("a3 done. rolls:", OUT["n_rolls"], "| gap dist:", OUT["roll_gap_dist_ticks"])
print("gap vs diff corr:", OUT["gap_vs_policy_diff"]["pearson_corr"],
      "| migration:", OUT["migration"])
