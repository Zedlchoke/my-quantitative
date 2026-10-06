#!/usr/bin/env python
"""Lane FXJA-K6, FUTURES-K6GATE-PREP-20261004 — M1: JF1 K3 anchor-robustness.

Unconditional session-segment anatomy of the 12:00-15:30 JST window
convention under ±45-min anchor shifts (K3, JPY_AUD_HYPOTHESES.md JF1 f7),
plus the secondary ±30/±15 ladder. Dispersion / volume / bar-count /
range-share structure only. NO directional returns, NO BoJ-stamp inference
(stamps NOT_IN_CORPUS stands). NO PnL.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

HERE = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-k6gate/prep"
        "/research/control/FUTURES-K6GATE-PREP-20261004/fx_ja")
SIXWRK = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness"
          "/prep/research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis")
RDY = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-k6gate/prep"
       "/research/control/FUTURES-SIX-READINESS-20261004")
TOKYO = "Asia/Tokyo"

VARIANTS = [(-45, "W-45"), (-30, "W-30"), (-15, "W-15"), (0, "W0_convention"),
            (+15, "W+15"), (+30, "W+30"), (+45, "W+45")]
PRIMARY = ("W-45", "W0_convention", "W+45")


def main():
    d = pd.read_parquet(f"{SIXWRK}/6J_cache/6j_annotated_1m.parquet",
                        columns=["dt", "close", "volume", "high", "low",
                                 "contract", "session_date"])
    held = pd.read_parquet(f"{SIXWRK}/6J_cache/held_volume_k5.parquet")
    heldmap = dict(zip(held["session_date"], held["held"]))
    d = d[d["contract"] == d["session_date"].map(heldmap)]
    d = d.sort_values("ts_event" if "ts_event" in d.columns else "dt").reset_index(drop=True)

    tok = d["dt"].dt.tz_convert(TOKYO)
    d["tmin"] = tok.dt.hour * 60 + tok.dt.minute
    d["prev_close"] = d.groupby("session_date")["close"].shift(1)
    d["absret_bp"] = ((d["close"] / d["prev_close"] - 1.0).abs() * 1e4
                      ).replace([np.inf, -np.inf], np.nan)

    mpm = json.load(open(f"{SIXWRK}/6J_a4_events.json"))["boj_mpm_days"]
    mpm_dates = set(str(r["date"]) for r in mpm)

    g = d.groupby("session_date")
    sess = pd.DataFrame({
        "n_bars": g.size(),
        "vol": g["volume"].sum(),
        "hi": g["high"].max(),
        "lo": g["low"].min(),
    })
    sess["is_mpm"] = [str(s) in mpm_dates for s in sess.index]

    results = {"variants": {}, "mpm_per_day": []}
    for delta, name in VARIANTS:
        lo_m, hi_m = 720 + delta, 930 + delta
        inw = d[(d["tmin"] >= lo_m) & (d["tmin"] < hi_m)]
        gw = inw.groupby("session_date")
        w = pd.DataFrame({
            "n_bars_w": gw.size(),
            "vol_w": gw["volume"].sum(),
            "hi_w": gw["high"].max(),
            "lo_w": gw["low"].min(),
            "med_absret_bp_w": gw["absret_bp"].median(),
            "mean_absret_bp_w": gw["absret_bp"].mean(),
            "p90_absret_bp_w": gw["absret_bp"].quantile(0.9),
        })
        w = w.join(sess, how="left")
        w = w[w["n_bars"] > 0]
        w["vol_share"] = w["vol_w"] / w["vol"] * 100.0
        w["range_share"] = ((w["hi_w"] - w["lo_w"])
                            / (w["hi"] - w["lo"]).replace(0, np.nan) * 100.0)

        def agg(sub):
            return {
                "n_sessions": int(len(sub)),
                "median_absret_bp_w": float(sub["med_absret_bp_w"].median()),
                "mean_absret_bp_w": float(sub["mean_absret_bp_w"].mean()),
                "p90_absret_bp_w": float(sub["p90_absret_bp_w"].median()),
                "median_volume_share_pct": float(sub["vol_share"].median()),
                "median_range_share_pct": float(sub["range_share"].median()),
                "median_bars_per_session_w": float(sub["n_bars_w"].median()),
            }

        v = {"window_jst": f"[{lo_m//60:02d}:{lo_m%60:02d}, {hi_m//60:02d}:{hi_m%60:02d})",
             "mpm_days": agg(w[w["is_mpm"]]),
             "all_sessions": agg(w[~w["is_mpm"]])}
        results["variants"][name] = v

        if name in PRIMARY or name in ("W-30", "W+30"):
            for s, row in w[w["is_mpm"]].iterrows():
                results["mpm_per_day"].append({
                    "date": str(s), "variant": name,
                    "range_share_pct": None if pd.isna(row["range_share"]) else float(row["range_share"]),
                    "volume_share_pct": None if pd.isna(row["vol_share"]) else float(row["vol_share"]),
                    "median_absret_bp_w": None if pd.isna(row["med_absret_bp_w"]) else float(row["med_absret_bp_w"]),
                    "bars_w": int(row["n_bars_w"]),
                })

    # pre-declared K3-ANATOMY descriptive condition (§0.2): W0 lead over the
    # better of its ±45 neighbours on range-share and volume-share medians
    def lead(metric, stratum):
        w0 = results["variants"]["W0_convention"][stratum][metric]
        nb = max(results["variants"]["W-45"][stratum][metric],
                 results["variants"]["W+45"][stratum][metric])
        return {"W0": w0, "best_plusminus45": nb, "lead_pp": w0 - nb}

    k3 = {
        "mpm_days_range_share": lead("median_range_share_pct", "mpm_days"),
        "mpm_days_volume_share": lead("median_volume_share_pct", "mpm_days"),
        "all_sessions_range_share": lead("median_range_share_pct", "all_sessions"),
        "all_sessions_volume_share": lead("median_volume_share_pct", "all_sessions"),
        "condition": ("lead < 0.5 pp on MPM days => ANCHOR_INSENSITIVE_AT_45MIN; "
                      ">= 0.5 pp => ANCHOR_SENSITIVE_AT_45MIN (§0.2)"),
    }
    mpm_lead = k3["mpm_days_range_share"]["lead_pp"]
    k3["verdict"] = ("ANCHOR_INSENSITIVE_AT_45MIN" if mpm_lead < 0.5
                     else "ANCHOR_SENSITIVE_AT_45MIN")
    results["k3_anatomy_condition"] = k3

    # level reconciliation vs the on-record convention statistic (§0.2 delta
    # law): the a4 lane's per-day range/volume-share convention is NOT
    # identical to this lane's (probe: 2020-01-21 — this lane 18.18% range /
    # 8.77% vol under [12:00,15:30) held-chain bars; a4 stores 9.60% / 7.87%;
    # the cache w_tokyo_pm flag [12:30,15:00) gives 16.88% / 5.30% — neither
    # reproduces a4). The LEVEL delta is disclosed and left unresolved
    # (reverse-engineering a4's exact window/session convention = considered
    # and NOT_RUN); the K3 anchor comparison is unaffected because all seven
    # variants use the identical statistic definition on identical bars.
    results["level_reconciliation"] = {
        "on_record": {
            "mpm_median_range_share_pct": 13.43, "alldays_median_range_share_pct": 10.35,
            "source": "JPY_AUD_HYPOTHESES.md JF1 f1 quoting 6J_a4_events.json:boj_mpm_vs_alldays"},
        "this_lane_W0": {
            "mpm_median_range_share_pct": results["variants"]["W0_convention"]["mpm_days"]["median_range_share_pct"],
            "alldays_median_range_share_pct": results["variants"]["W0_convention"]["all_sessions"]["median_range_share_pct"],
            "mpm_median_volume_share_pct": results["variants"]["W0_convention"]["mpm_days"]["median_volume_share_pct"]},
        "status": "LEVEL_NON_IDENTITY_DISCLOSED — a4's exact per-day window/session "
                  "convention not reverse-engineered (NOT_RUN, anti-cherry-pick); "
                  "variant comparison internally consistent (identical definition "
                  "across all variants)",
        "probe_2020_01_21": {"this_lane_range_pct": 18.1818, "a4_range_pct": 9.602649,
                             "this_lane_vol_pct": 8.7666, "a4_vol_pct": 7.8704,
                             "pm_flag_range_pct": 16.8831, "pm_flag_vol_pct": 5.2994},
    }

    out = {
        "schema": "jf1_k3_anchor@1",
        "lane": "FXJA-K6", "round": "FUTURES-K6GATE-PREP-20261004",
        "predeclaration": "FXJA_K6_GATES.md §0.2 (written before compute)",
        "owning_definition": ("JPY_AUD_HYPOTHESES.md JF1 field 7 K3 (window-"
                              "artifact): if the effect vanishes when the anchor "
                              "moves ±45 min within the 12:00-15:30 JST window "
                              "(no minute-stamped release exists — the anchor-"
                              "robustness test is the substitute), it is a "
                              "bucketing artifact"),
        "boundary": ("anatomy ONLY; the K3 kill itself requires the scored "
                     "conditional effect — NOT_RUN here, never inferred; BoJ "
                     "stamps NOT_IN_CORPUS stands; no directional returns"),
        "inputs": {
            "panel": f"{SIXWRK}/6J_cache/6j_annotated_1m.parquet (2,843,938 rows, panel of record)",
            "held_chain": f"{SIXWRK}/6J_cache/held_volume_k5.parquet (baseline k=5 chain of record)",
            "mpm_dates": f"{SIXWRK}/6J_a4_events.json:boj_mpm_days (54 dates, FACT)",
            "disclosed": ("2022-09-20 baseline chain holds ceased U2 with zero "
                          "held bars — enters no within-session statistic"),
        },
        "results": results,
        "no_pnl_note": "dispersion/volume/range/bar-count only",
    }
    os.makedirs(HERE, exist_ok=True)
    with open(os.path.join(HERE, "jf1_k3_anchor.json"), "w") as fh:
        json.dump(out, fh, indent=1, default=str, allow_nan=False)
    print("wrote", os.path.join(HERE, "jf1_k3_anchor.json"))
    for name in results["variants"]:
        v = results["variants"][name]
        print(f"{name:14s} MPM n={v['mpm_days']['n_sessions']:3d} "
              f"range%={v['mpm_days']['median_range_share_pct']:.2f} "
              f"vol%={v['mpm_days']['median_volume_share_pct']:.2f} "
              f"|ret|bp={v['mpm_days']['median_absret_bp_w']:.2f} "
              f"bars={v['mpm_days']['median_bars_per_session_w']:.0f} || "
              f"ALL n={v['all_sessions']['n_sessions']} "
              f"range%={v['all_sessions']['median_range_share_pct']:.2f} "
              f"vol%={v['all_sessions']['median_volume_share_pct']:.2f} "
              f"|ret|bp={v['all_sessions']['median_absret_bp_w']:.2f}")
    print(json.dumps(k3, indent=1))


if __name__ == "__main__":
    main()
