#!/usr/bin/env python
"""ES1 P4 SCORED RUN — full frozen denominator, post-GO.

GO basis: A7 prelaunch AUTHORIZED_FOR_DISCOVERY_STOP (delta r1) + owner
verbatim GO 'GO BTC H4 EDGE SEARCH V1 SCORED EXECUTION' typed at the STOP-1
gate. Frozen identity: freezes/es1_freeze.json (plan PLAN_btc_h4_edge_
search_v1.md §3/§4; branch head 4005284f at GO time).

Heavy-lock note: the machine-wide lock is HELD_PROVEN by a foreign cycle
(CRYPTO-HISTORICAL-REPLICATION-3F-V1, pid 77456 — never killed). This run
executes under the plan §9 LIGHT-JOB EXEMPTION with enforced, measured
ceilings (<240 s CPU, <1.5 GB RSS) — identical resource class to the
already-exempt census; if the ceilings were exceeded the run must be
treated as heavy and re-run under the lock. The exemption and its
measurements are recorded in the artifact.

No mid-run stop on ugly numbers; no parameter edit after this run.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
SCORED_PKG = ("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
              "integration/research/control/phase_strategy_v1/scored")
sys.path.insert(0, SCORED_PKG)
import es1_engine as E  # noqa: E402
from es1_reconcile_comparator import run_book_instrumented, decision_series  # noqa: E402
from pipeline import config as pc, events as pe  # noqa: E402
import cells  # noqa: E402

OUT_DIR = HERE.parent / "scored"
GO_PHRASE = "GO BTC H4 EDGE SEARCH V1 SCORED EXECUTION"
TIERS = (1.0, 1.5, 2.0)
LAWS = ("constant", "measured")
CPU_CEIL_S = 240.0
RSS_CEIL_BYTES = int(1.5e9)


def sparse_risk_off(close: np.ndarray) -> np.ndarray:
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


def main():
    t0 = time.time()
    h4, _ = E.load_panel()
    data = cells.load_btc_h4()
    labels_w = np.asarray([str(x) for x in data["labels"]])
    panel_w = h4.iloc[E.WARMUP:].reset_index(drop=True)
    close_w = panel_w["close"].to_numpy(float)
    folds = E.fold_ids(panel_w["bucket_ms"].to_numpy())
    funding_df = E.load_funding_measured()

    spec = pe.BookSpec(name="PSV1", phase="UPTREND", trigger="donchian_breakout",
                       donch_entry=pc.DONCH_ENTRY, donch_stop=pc.DONCH_STOP,
                       exit_buffer=pc.EXIT_BUFFER_BARS, min_hold=pc.MIN_HOLD_BARS,
                       max_hold=pc.MAX_HOLD_BARS, direction=1)
    trades, _ = run_book_instrumented(labels_w, close_w, spec, folds)
    comp_dec, _ = decision_series(trades, len(close_w))

    rvol = E.rvol_series(panel_w)
    books = {
        # budget cells (8)
        "A1": E.sig_vol_managed(np.ones_like(close_w), rvol, 0.60),
        "A2": E.sig_vol_managed(E.sig_trend_lf(panel_w, 0.0), rvol, 0.60),
        "A3": E.sig_vol_managed(comp_dec, rvol, 0.60),
        "A4": E.sig_vol_managed(E.sig_trend_lf(panel_w, 0.0), rvol, 0.40),
        "C1": E.sig_trend_lf(panel_w, 0.01),
        "C2": E.sig_trend_lf(panel_w, 0.02),
        "C3": E.sig_trend_lf(panel_w, 0.03),
        "C4": E.sig_trend_lf(panel_w, 0.005),
        # reference set
        "COMPARATOR": comp_dec,
        "BASE_ALWAYS_ON": np.ones_like(close_w),
        "BASE_TREND_LF": E.sig_trend_lf(panel_w, 0.0),
        "BASE_SPARSE": sparse_risk_off(close_w),
        "BASE_CASH": np.zeros_like(close_w),
        "G6A_SHUFFLED_SCALE": E.sig_vol_managed(
            E.sig_trend_lf(panel_w, 0.0), E.block_shuffle(rvol), 0.60),
        "G6C_SHUFFLED_STATE": E.block_shuffle(E.sig_trend_lf(panel_w, 0.01)),
    }

    grid = {}
    for name, dec in books.items():
        for tier in TIERS:
            for law in LAWS:
                r = E.simulate(dec, panel_w, folds, tier=tier,
                               funding_law=law, funding_df=funding_df)
                grid[f"{name}|{tier}|{law}"] = r.as_dict()

    def net(name, tier, law):
        return grid[f"{name}|{tier}|{law}"]["net"]

    def folds_net(name, tier, law):
        return grid[f"{name}|{tier}|{law}"]["fold_net"]

    base_names = ["BASE_ALWAYS_ON", "BASE_TREND_LF", "BASE_SPARSE", "BASE_CASH"]
    g6_pairs = {"A2": "G6A_SHUFFLED_SCALE", "C1": "G6C_SHUFFLED_STATE"}
    ref = {"A1": "BASE_ALWAYS_ON", "A2": "BASE_TREND_LF", "A3": "COMPARATOR",
           "A4": "BASE_TREND_LF", "C1": "BASE_TREND_LF", "C2": "BASE_TREND_LF",
           "C3": "BASE_TREND_LF", "C4": "BASE_TREND_LF"}

    results = {}
    for cell in [f"A{i}" for i in range(1, 5)] + [f"C{i}" for i in range(1, 5)]:
        g = {"G1": {}, "G2": {}, "G3": {}, "G4": {}, "G5": {}, "G6": {}, "G7": {}, "G10": {}}
        for law in LAWS:
            g["G1"][law] = net(cell, 1.0, law) > 0
            g["G2"][law] = net(cell, 1.5, law) > 0
            base_max = max(net(b, 1.0, law) for b in base_names)
            g["G3"][law] = {"pass": net(cell, 1.0, law) > base_max,
                            "margin": round(net(cell, 1.0, law) - base_max, 2)}
            fn = folds_net(cell, 1.0, law)
            pos_folds = sum(1 for v in fn.values() if v > 0)
            best_removed = min(
                (sum(v for k, v in fn.items() if k != k2) for k2 in fn), default=0.0)
            g["G4"][law] = {"positive_folds": pos_folds, "best_fold_removed_net": round(best_removed, 2),
                            "pass": pos_folds >= 3 or best_removed > 0}
            pos_total = sum(v for v in fn.values() if v > 0)
            conc = (max(v for v in fn.values() if v > 0) / pos_total) if pos_total > 0 else None
            g["G5"][law] = {"fold_concentration": round(conc, 4) if conc is not None else None,
                            "pass": conc is not None and conc <= 0.50}
            if cell in g6_pairs:
                g["G6"][law] = {"anchor": round(net(cell, 1.0, law), 2),
                                "control": round(net(g6_pairs[cell], 1.0, law), 2),
                                "pass": net(cell, 1.0, law) > net(g6_pairs[cell], 1.0, law)}
            # G7: per-trade cost ceiling at 1.5x (fills->round trips) + no zero-length trades
            fills15 = grid[f"{cell}|1.5|{law}"]["fills"]
            rts = max(1, fills15 // 2)
            cost_per_rt_bps = (grid[f"{cell}|1.5|{law}"]["fees"] / rts) / max(1e-9, grid[f"{cell}|1.5|{law}"]["net"] + 100_000) * 1e4
            g["G7"][law] = {"fills_1_5x": fills15, "cost_per_roundtrip_bps": round(cost_per_rt_bps, 2),
                            "pass": cost_per_rt_bps <= 100.0}
            # G10 fold trade-off vs reference
            r = ref[cell]
            fn_ref = folds_net(r, 1.0, law)
            d = {k: round(fn[k] - fn_ref[k], 2) for k in fn}
            flips = [k for k in fn if fn_ref[k] > 0 and fn[k] < 0]
            g["G10"][law] = {"delta_folds": d, "combined_increase": net(cell, 1.0, law) > net(r, 1.0, law),
                             "fold_flips_pos_to_neg": flips,
                             "pass": net(cell, 1.0, law) > net(r, 1.0, law) and not flips}
        checks = [all(g["G1"].values()), all(g["G2"].values()),
                  all(g["G3"][l]["pass"] for l in LAWS),
                  all(g["G4"][l]["pass"] for l in LAWS),
                  all(g["G5"][l]["pass"] for l in LAWS)]
        if cell in g6_pairs:
            checks.append(all(g["G6"][l]["pass"] for l in LAWS))
        checks += [all(g["G7"][l]["pass"] for l in LAWS), all(g["G10"][l]["pass"] for l in LAWS)]
        results[cell] = {"gates": g,
                         "all_pass": bool(all(checks)),
                         "failed": [n for n, c in zip(
                             ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G10"], checks) if not c]}

    cpu_s = time.time() - t0
    rss_raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS reports ru_maxrss in BYTES; Linux in KB
    rss = rss_raw * (1 if sys.platform == 'darwin' else 1024)
    light_ok = cpu_s < CPU_CEIL_S and rss < RSS_CEIL_BYTES

    candidates = [c for c, r in results.items() if r["all_pass"]]

    def np_default(o):
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        raise TypeError(f"not JSON serializable: {type(o)}")

    summary = {
        "schema": "es1.scored_run@1",
        "go": {"phrase": GO_PHRASE,
               "received_utc": "2026-09-23T19:55:00Z (owner verbatim at STOP-1)",
               "a7_prelaunch": "AUTHORIZED_FOR_DISCOVERY_STOP (delta r1, 0 blocking)"},
        "frozen_head_at_go": "4005284f1ca4fc6e7e60a8d6bb006b74aeabdbab",
        "lock_state": "HELD_PROVEN by foreign cycle CRYPTO-HISTORICAL-REPLICATION-3F-V1 (pid 77456) — never killed",
        "light_exemption": {"basis": "plan §9; enforced ceilings", "cpu_s": round(cpu_s, 2),
                             "peak_rss_gb": round(rss / 1e9, 3),
                             "within_ceilings": light_ok},
        "denominator": {"scored_cells": 8, "budget_max": 12,
                         "arm_tier_law_computations": len(grid),
                         "reference_books": ["COMPARATOR"] + base_names +
                                            ["G6A_SHUFFLED_SCALE", "G6C_SHUFFLED_STATE"]},
        "cells": results,
        "candidates": candidates,
        "grid": grid,
        "verdict": ("BTC_H4_EDGE_SEARCH_V1_POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION"
                    if candidates else "BTC_H4_EDGE_SEARCH_V1_NO_INCREMENTAL_VALUE"),
        "ceiling_note": "2020-2026 is outcome-observed; a candidate is a discovery candidate pending prospective validation, never OOS, never deployable",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "scored_summary.json").write_text(json.dumps(summary, indent=1, default=np_default))
    head = subprocess.run(["git", "-C", str(HERE.parents[2]), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    summary["run_head"] = head
    (OUT_DIR / "scored_summary.json").write_text(json.dumps(summary, indent=1, default=np_default))

    print("light exemption:", summary["light_exemption"])
    for c, r in results.items():
        print(f"{c}: all_pass={r['all_pass']} failed={r['failed']} "
              f"net@1.0 const={grid[f'{c}|1.0|constant']['net']:.0f} "
              f"meas={grid[f'{c}|1.0|measured']['net']:.0f}")
    print("baselines @1.0 measured:",
          {b: round(net(b, 1.0, "measured"), 0) for b in base_names})
    print("candidates:", candidates)
    print("VERDICT:", summary["verdict"])
    if not light_ok:
        print("WARNING: light ceilings EXCEEDED — must re-run under the heavy lock")
        sys.exit(3)


if __name__ == "__main__":
    main()
