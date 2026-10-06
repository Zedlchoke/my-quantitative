"""A4 — 6J intervention + BoJ MPM-day anatomy 2020-2026 (DEEP-6J).

DESCRIPTIVE EVENT ANATOMY ONLY (no conditional mean-return tables, no PnL,
no signal ranking — anything PnL-linked selection is NOT_RUN by law).

MOF FX intervention ops (primary MOF record via nonprice tidy, 81 ops
1991-2026; 9 JPY-buying ops 2022-2026 inside the 1m window): per op session —
session return, volume vs trailing-21-session median (STRICT PAST), true-range
percentile vs trailing-126 (STRICT PAST), which center window carried the
range/volume, the 5 largest 1m volume bursts with timestamps + center labels,
and the next-1..5-session close path (descriptive path, not a signal).

BoJ MPM decision dates (day-2 statements, 54 in 2020-2026): descriptive
distribution of session |return|, volume ratio, and BoJ-decision-window
(12:00-15:30 JST = Tokyo afternoon, US overnight) share of range vs all-days
baseline. Regime-change meetings flagged from mpmdeci titles where available.

PIT disclosure: MOF amounts publish with ~1-month/quarter lag — NO same-day
signal exists from the op record; all op-day stats are descriptions of
disclosed operations.
"""
from __future__ import annotations

import os
import sys

import importlib

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
L = importlib.import_module("6J_deep_lib")

OUT = os.path.join(L.HERE, "6J_a4_events.json")


def center_label(row):
    labs = []
    for name in ("tokyo_am", "tokyo_lunch", "tokyo_pm", "tokyo_fix",
                 "london_am", "london_pm", "ny_am", "ny_pm", "ny_post"):
        if row[f"w_{name}"]:
            labs.append(name)
    return labs


def main():
    ann = pd.read_parquet(os.path.join(L.CACHE, "6j_annotated_1m.parquet"))
    sess = pd.read_parquet(os.path.join(L.CACHE, "6j_sessions.parquet"))
    held = pd.read_parquet(os.path.join(L.CACHE, "held_volume_k5.parquet"))
    hmap = dict(zip(held["session_date"], held["held"]))
    hh = sess[sess["session_date"].map(hmap).notna()].merge(
        held.rename(columns={"held": "contract"}), on=["session_date", "contract"])
    hh = hh.sort_values("session_date").reset_index(drop=True)
    hh["d"] = pd.to_datetime(hh["session_date"])
    hh["ret_within"] = np.log(hh["close"]) - hh.groupby("contract")["close"].shift(1).pipe(np.log)
    # strict-past baselines
    hh["vol_med21_past"] = hh["volume"].shift(1).rolling(21, min_periods=10).median()
    hh["tr_pctile126_past"] = [
        (hh["true_range"].iloc[max(0, i - 126):i] <
         hh["true_range"].iloc[i]).mean() if i > 20 else np.nan
        for i in range(len(hh))]
    ann_h = ann[ann["session_date"].map(hmap).notna()].copy()
    ann_h = ann_h[ann_h["contract"] == ann_h["session_date"].map(hmap)]
    ann_h["range_px"] = (ann_h["high"].astype(float)
                         - ann_h["low"].astype(float)) * L.PX_SCALE

    res = {"schema": "6J_a4_events@1",
           "pit_disclosure": ("MOF op amounts publish ~1 month (monthly) / quarter "
                              "(daily detail) AFTER the fact — no same-day PIT "
                              "signal; every stat here is description of a "
                              "disclosed operation")}

    # ---------------- MOF ops ----------------
    mof = L.load_mof_intervention()
    ops = mof[(mof["op_date"] >= "2020-01-01") & (mof["direction"] == "JPY_buying")]
    res["mof_ops_total_81op_history"] = {
        "history_span": f"{mof['op_date'].min().date()}..{mof['op_date'].max().date()}",
        "n_ops_total": int(len(mof)),
        "n_jpy_buying": int((mof["direction"] == "JPY_buying").sum()),
        "ops_in_1m_window": int(len(ops))}
    op_rows = []
    for _, op in ops.iterrows():
        ds = str(op["op_date"].date())
        row = hh[hh["session_date"].astype(str) == ds]
        if not len(row):
            op_rows.append({"op_date": ds, "note": "no held session (holiday)"})
            continue
        r = row.iloc[0]
        bar = ann_h[ann_h["session_date"].astype(str) == ds]
        tot_rng = float(bar["range_px"].sum())  # sum of 1m bar ranges (overlap-adjusted denominator)
        top5 = bar.nlargest(5, "volume")
        bursts = []
        for _, b in top5.iterrows():
            bursts.append({
                "ts_utc": str(b["dt"]), "volume": int(b["volume"]),
                "ct": f"{int(b['minute_ct'])//60:02d}:{int(b['minute_ct'])%60:02d}",
                "center_windows": center_label(b)})
        maxrng = (bar["high"].astype(float) - bar["low"].astype(float)).idxmax()
        mr = bar.loc[maxrng]
        # descriptive close path next 5 sessions
        idx = row.index[0]
        path = {}
        for k in range(1, 6):
            if idx + k < len(hh):
                rr = hh.iloc[idx + k]
                path[f"d+{k}"] = {
                    "date": str(rr["session_date"]),
                    "ret_within_pct": (float(100 * rr["ret_within"])
                                       if pd.notna(rr["ret_within"]) else None)}
        op_rows.append({
            "op_date": ds, "amount_yen_bn": float(op["value_yen_100m"]) / 10.0,
            "held_contract": r["contract"],
            "session_ret_within_pct": (float(100 * r["ret_within"])
                                       if pd.notna(r["ret_within"]) else None),
            "session_volume": int(r["volume"]),
            "volume_vs_past21_median_x": (float(r["volume"] / r["vol_med21_past"])
                                          if pd.notna(r["vol_med21_past"]) else None),
            "true_range_pctile_vs_past126": float(r["tr_pctile126_past"]),
            "range_by_center_window_pct": {
                n: float(100 * r[f"rng_{n}"] / tot_rng) for n in
                ("tokyo_am", "tokyo_lunch", "tokyo_pm", "tokyo_fix",
                 "london_am", "london_pm", "ny_am", "ny_pm", "ny_post")},
            "range_share_note": "share of the session's summed 1m bar-range; windows overlap (london_pm ∩ ny_am)",
            "top5_volume_minutes": bursts,
            "largest_1m_range_bar": {
                "ts_utc": str(mr["dt"]),
                "center_windows": center_label(mr),
                "range_bp": float(1e4 * (mr["high"].astype(float)
                                         - mr["low"].astype(float)) * L.PX_SCALE
                                  / (mr["close"].astype(float) * L.PX_SCALE))},
            "next5_close_path": path})
    res["mof_ops_anatomy"] = op_rows

    # unverified 2026 Jul-Aug window (record pending MOF Q3 page) — describe
    # the biggest 2026 session as context, flagged NOT-MOF-VERIFIED
    ds = "2026-07-30"
    row = hh[hh["session_date"].astype(str) == ds]
    if len(row):
        r = row.iloc[0]
        bar = ann_h[ann_h["session_date"].astype(str) == ds]
        top1 = bar.nlargest(1, "volume").iloc[0]
        res["pending_window_context_2026_07_30"] = {
            "note": ("press-cited record intervention window Jul 30-Aug 26 2026; "
                     "MOF Q3-2026 daily detail NOT published at data access "
                     "(2026-10-02) — op status NOT MOF-VERIFIED, price anatomy only"),
            "session_ret_within_pct": float(100 * r["ret_within"]),
            "session_volume": int(r["volume"]),
            "volume_vs_past21_median_x": float(r["volume"] / r["vol_med21_past"]),
            "largest_1m_volume_burst": {"ts_utc": str(top1["dt"]),
                                        "volume": int(top1["volume"]),
                                        "center_windows": center_label(top1)}}

    # ---------------- BoJ MPM days ----------------
    mpm = L.load_boj_mpm()
    mpm = mpm[(mpm["date"].astype(str) >= "2020-01-01")
              & (mpm["date"].astype(str) <= "2026-09-30")]
    mdays = []
    for _, m in mpm.iterrows():
        ds = str(m["date"])
        row = hh[hh["session_date"].astype(str) == ds]
        if not len(row):
            mdays.append({"date": ds, "note": "no held session"})
            continue
        r = row.iloc[0]
        bar = ann_h[ann_h["session_date"].astype(str) == ds]
        tot_rng = float(bar["range_px"].sum())
        boj_rng = r["rng_tokyo_pm"] + r["rng_tokyo_fix"]
        mdays.append({
            "date": ds,
            "title_regime_change": (m["title"] if m["is_regime_change"] else None),
            "is_regime_change": (bool(m["is_regime_change"])
                                 if m["is_regime_change"] is not None else None),
            "session_ret_within_pct": (float(100 * r["ret_within"])
                                       if pd.notna(r["ret_within"]) else None),
            "abs_ret_pct": (float(abs(100 * r["ret_within"]))
                            if pd.notna(r["ret_within"]) else None),
            "volume_vs_past21_median_x": (float(r["volume"] / r["vol_med21_past"])
                                          if pd.notna(r["vol_med21_past"]) else None),
            "boj_window_range_share_pct": (float(100 * boj_rng / tot_rng)
                                           if tot_rng > 0 else None),
            "boj_window_volume_share_pct": float(
                100 * (r["vol_tokyo_pm"] + r["vol_tokyo_fix"]) / r["volume"])})
    res["boj_mpm_days"] = mdays
    mdf = pd.DataFrame([x for x in mdays if "abs_ret_pct" in x])
    # all-days baselines for comparison
    ses_tot = ann_h.groupby(ann_h["session_date"].astype(str))["range_px"].sum()
    hh_idx = hh.set_index(hh["session_date"].astype(str))
    boj_share_all = (100 * (hh_idx["rng_tokyo_pm"] + hh_idx["rng_tokyo_fix"])
                     / ses_tot.reindex(hh_idx.index)).median()
    res["boj_mpm_vs_alldays"] = {
        "n_mpm_days_measured": int(len(mdf)),
        "mpm_median_abs_ret_pct": float(mdf["abs_ret_pct"].median()),
        "alldays_median_abs_ret_pct": float(
            100 * hh["ret_within"].abs().median()),
        "mpm_median_volume_ratio": float(mdf["volume_vs_past21_median_x"].median()),
        "alldays_median_volume_ratio": float(
            (hh["volume"] / hh["vol_med21_past"]).median()),
        "mpm_median_boj_window_range_share_pct": float(
            mdf["boj_window_range_share_pct"].median()),
        "alldays_median_boj_window_range_share_pct": float(boj_share_all),
        "note": ("descriptive comparison only; decision releases land in the "
                 "12:00-15:30 JST window (US overnight) which v1 could not see")}

    L.jdump(res, OUT)
    print("A4 complete ->", OUT)


if __name__ == "__main__":
    main()
