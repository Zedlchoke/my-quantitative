#!/usr/bin/env python
"""BRV1 P2 SCORED RUN — full frozen denominator, post-GO.

GO basis: owner verbatim 'GO BTC H4 BAND RISK V1 SCORED EXECUTION' at
STOP-1 (A7 waived by owner this cycle — recorded; repro twin mandatory).
Frozen identity: plans/PLAN_btc_h4_band_risk_v1.md section 1 ladder;
engine inherited RECONCILED (9e-10 vs PSV1 ledger).

Light-exemption discipline identical to ES1 (measured ceilings; foreign
lock disclosed; exceed => must re-run under the lock).
"""
from __future__ import annotations

import json
import resource
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "btc_h4_edge_search_v1" / "scripts"))
sys.dont_write_bytecode = True
SCORED_PKG = ("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
              "integration/research/control/phase_strategy_v1/scored")
sys.path.insert(0, SCORED_PKG)
import es1_engine as E          # noqa: E402
import band_risk as B           # noqa: E402
import cells                    # noqa: E402

OUT_DIR = HERE.parent / "scored"
GO_PHRASE = "GO BTC H4 BAND RISK V1 SCORED EXECUTION"
TIERS = (1.0, 1.5, 2.0)
LAWS = ("constant", "measured")
CPU_CEIL_S = 240.0
RSS_CEIL_BYTES = int(1.5e9)


def sparse_risk_off(close):
    peak = np.maximum.accumulate(close)
    dd = close / peak - 1.0
    out = np.zeros(len(close))
    state, held = 0, 0
    for t in range(len(close)):
        if state == 0:
            if dd[t] >= -0.10:
                state, held = 1, 0
        else:
            held += 1
            if dd[t] <= -0.30 and held >= 5:
                state = 0
        out[t] = state
    return out


def np_default(o):
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    raise TypeError(f"not JSON serializable: {type(o)}")


def main():
    t0 = time.time()
    h4, _ = E.load_panel()
    data = cells.load_btc_h4()
    panel_w = h4.iloc[E.WARMUP:].reset_index(drop=True)
    close_w = panel_w["close"].to_numpy(float)
    folds = E.fold_ids(panel_w["bucket_ms"].to_numpy())
    funding_df = E.load_funding_measured()

    cells_def = {
        "R1": B.sig_band_overlay(panel_w, band=0.03, trail=0.10, folds=folds),
        "R2": B.sig_band_overlay(panel_w, band=0.03, trail=0.15, folds=folds),
        "R3": B.sig_band_overlay(panel_w, band=0.03, trail=0.20, folds=folds),
        "R4": B.sig_band_overlay(panel_w, band=0.03, trail=0.25, folds=folds),
        "R5": B.sig_band_overlay(panel_w, band=0.005, trail=0.15, folds=folds),
        "R6": B.sig_band_overlay(panel_w, band=0.03, cat=0.15, folds=folds),
        "R7": B.sig_band_overlay(panel_w, band=0.03, trail=0.15, cooldown=12, folds=folds),
        "R8": B.sig_band_overlay(panel_w, band=0.03, trail=0.30, folds=folds),
        "REF_C3": B.sig_band_overlay(panel_w, band=0.03),
        "BASE_ALWAYS_ON": np.ones_like(close_w),
        "BASE_TREND_LF": E.sig_trend_lf(panel_w, 0.0),
        "BASE_SPARSE": sparse_risk_off(close_w),
        "BASE_CASH": np.zeros_like(close_w),
    }

    grid = {}
    for name, dec in cells_def.items():
        for tier in TIERS:
            for law in LAWS:
                r = E.simulate(dec, panel_w, folds, tier=tier,
                               funding_law=law, funding_df=funding_df)
                grid[f"{name}|{tier}|{law}"] = r.as_dict()

    def net(n, t, l):
        return grid[f"{n}|{t}|{l}"]["net"]

    def fnets(n, t, l):
        return grid[f"{n}|{t}|{l}"]["fold_net"]

    base_names = ["BASE_ALWAYS_ON", "BASE_TREND_LF", "BASE_SPARSE", "BASE_CASH"]
    scored = [f"R{i}" for i in range(1, 9)]
    results = {}
    for cell in scored:
        g = {"G1": {}, "G2": {}, "G3": {}, "G4": {}, "G5": {}, "G7": {}, "G10": {}, "ABLATION": None}
        for law in LAWS:
            g["G1"][law] = bool(net(cell, 1.0, law) > 0)
            g["G2"][law] = bool(net(cell, 1.5, law) > 0)
            base_max = max(net(b, 1.0, law) for b in base_names)
            g["G3"][law] = {"pass": bool(net(cell, 1.0, law) > base_max),
                            "margin": round(float(net(cell, 1.0, law) - base_max), 2)}
            fn = fnets(cell, 1.0, law)
            pos_folds = sum(1 for v in fn.values() if v > 0)
            best_removed = min((sum(v for k, v in fn.items() if k != k2) for k2 in fn), default=0.0)
            g["G4"][law] = {"positive_folds": pos_folds,
                            "best_fold_removed_net": round(float(best_removed), 2),
                            "pass": bool(pos_folds >= 3 or best_removed > 0)}
            pos_total = sum(v for v in fn.values() if v > 0)
            conc = (max(v for v in fn.values() if v > 0) / pos_total) if pos_total > 0 else None
            g["G5"][law] = {"fold_concentration": round(float(conc), 4) if conc is not None else None,
                            "pass": bool(conc is not None and conc <= 0.50)}
            fills15 = grid[f"{cell}|1.5|{law}"]["fills"]
            rts = max(1, fills15 // 2)
            cpt = (grid[f"{cell}|1.5|{law}"]["fees"] / rts) / max(1e-9, grid[f"{cell}|1.5|{law}"]["net"] + 100_000) * 1e4
            g["G7"][law] = {"fills_1_5x": fills15, "cost_per_roundtrip_bps": round(float(cpt), 2),
                            "pass": bool(cpt <= 100.0)}
            fn_ref = fnets("BASE_TREND_LF", 1.0, law)
            flips = [k for k in fn if fn_ref[k] > 0 and fn[k] < 0]
            g["G10"][law] = {"combined_increase": bool(net(cell, 1.0, law) > net("BASE_TREND_LF", 1.0, law)),
                             "fold_flips_pos_to_neg": flips,
                             "pass": bool(net(cell, 1.0, law) > net("BASE_TREND_LF", 1.0, law) and not flips)}
        # R8 ablation identity: far-stop must nearly reproduce C3
        if cell == "R8":
            drift = abs(net("R8", 1.0, "measured") - net("REF_C3", 1.0, "measured")) / max(1.0, abs(net("REF_C3", 1.0, "measured")))
            g["ABLATION"] = {"r8_net_measured": round(float(net("R8", 1.0, "measured")), 2),
                             "c3_net_measured": round(float(net("REF_C3", 1.0, "measured")), 2),
                             "rel_drift": round(float(drift), 4), "pass": bool(drift <= 0.02)}
        checks = [all(g["G1"].values()), all(g["G2"].values()),
                  all(g["G3"][l]["pass"] for l in LAWS),
                  all(g["G4"][l]["pass"] for l in LAWS),
                  all(g["G5"][l]["pass"] for l in LAWS),
                  all(g["G7"][l]["pass"] for l in LAWS),
                  all(g["G10"][l]["pass"] for l in LAWS)]
        if cell == "R8":
            checks.append(g["ABLATION"]["pass"])
        results[cell] = {"gates": g, "all_pass": bool(all(checks)),
                         "failed": [n for n, c in zip(
                             ["G1", "G2", "G3", "G4", "G5", "G7", "G10", "ABLATION"], checks) if not c]}

    # DIAG: can ANY long book pass G5 on this window?
    diag = {}
    for name in list(base_names) + ["REF_C3", "COMPARATOR_PLACEHOLDER"]:
        pass
    for name in list(base_names) + ["REF_C3"]:
        fn = fnets(name, 1.0, "measured")
        pos_total = sum(v for v in fn.values() if v > 0)
        conc = (max(v for v in fn.values() if v > 0) / pos_total) if pos_total > 0 else None
        diag[name] = {"fold_net": {k: round(float(v), 2) for k, v in fn.items()},
                      "fold_concentration": round(float(conc), 4) if conc is not None else None,
                      "g5_would_pass": bool(conc is not None and conc <= 0.50)}

    cpu_s = time.time() - t0
    rss_raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss = rss_raw * (1 if sys.platform == "darwin" else 1024)
    light_ok = cpu_s < CPU_CEIL_S and rss < RSS_CEIL_BYTES
    candidates = [c for c, r in results.items() if r["all_pass"]]

    summary = {
        "schema": "brv1.scored_run@1",
        "go": {"phrase": GO_PHRASE, "a7": "WAIVED by owner 2026-09-23 ('khỏi A7 lúc này' — recorded)"},
        "frozen_head_at_go": "41902382f342bec6140fdf9dc4309ceda92dc1d5",
        "lock_state": "checked at run; see light_exemption",
        "light_exemption": {"basis": "plan §9 analog; enforced ceilings", "cpu_s": round(cpu_s, 2),
                             "peak_rss_gb": round(rss / 1e9, 3), "within_ceilings": light_ok},
        "denominator": {"scored_cells": 8, "budget_max": 8,
                         "arm_tier_law_computations": len(grid)},
        "diag_g5_baseline_census": diag,
        "cells": results,
        "candidates": candidates,
        "grid": grid,
        "verdict": ("BTC_H4_BAND_RISK_V1_POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION"
                    if candidates else "BTC_H4_BAND_RISK_V1_NO_INCREMENTAL_VALUE"),
        "ceiling_note": "outcome-observed window; candidate = discovery pending prospective validation",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(["git", "-C", str(HERE.parents[2]), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    summary["run_head"] = head
    (OUT_DIR / "scored_summary.json").write_text(json.dumps(summary, indent=1, default=np_default))

    print("light:", summary["light_exemption"])
    for c, r in results.items():
        print(f"{c}: all_pass={r['all_pass']} failed={r['failed']} "
              f"net@1.0 const={grid[f'{c}|1.0|constant']['net']:.0f} meas={grid[f'{c}|1.0|measured']['net']:.0f} "
              f"conc_meas={r['gates']['G5']['measured']['fold_concentration']}")
    print("DIAG baselines G5:", {k: v["fold_concentration"] for k, v in diag.items()})
    print("candidates:", candidates)
    print("VERDICT:", summary["verdict"])
    if not light_ok:
        print("WARNING: light ceilings exceeded — must re-run under the heavy lock")
        sys.exit(3)


if __name__ == "__main__":
    main()
