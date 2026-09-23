#!/usr/bin/env python
"""ES1 sanitized dry-run (plan §6): every scored cell's DECISION path is
built and counted — fills, entries, exposure — with NO returns, NO equity,
NO PnL anywhere (recursive guarantee: this script never touches prices for
accounting; it only counts decision changes).

Non-vacuous gate: every cell must produce fills > 0 and a valid record ID;
the COMPARATOR must produce exactly 86 entries (identity with the frozen
ancestor). Output: freezes/dry_run_counts.json.
"""
from __future__ import annotations

import hashlib
import json
import sys
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
import cells  # noqa: E402  (PSV1 loader: re-derives labels via classify)

W = E.WARMUP


def counts(name: str, dec: np.ndarray, folds: np.ndarray) -> dict:
    d = np.asarray(dec, dtype=float)
    d = np.where(np.isfinite(d), d, 0.0)
    d = np.minimum(1.0, np.maximum(0.0, d))
    delta = np.diff(d, prepend=0.0)
    fills = int(np.sum(np.abs(delta) > 1e-12))
    entries = int(np.sum((delta > 1e-12) & (np.concatenate([[0.0], d[:-1]]) == 0)))
    return {"record_id": hashlib.sha256(
                f"{name}|{d.tobytes()}".encode()).hexdigest()[:16],
            "decision_bars": int(len(d)), "fills": fills, "entries": entries,
            "mean_exposure": round(float(d.mean()), 4),
            "per_fold_decision_bars": {f"F{i+1}": int(np.sum(folds == i)) for i in range(4)}}


def main():
    h4, _ = E.load_panel()
    data = cells.load_btc_h4()
    labels_w = np.asarray([str(x) for x in data["labels"]])
    panel_w = h4.iloc[W:].reset_index(drop=True)
    close_w = panel_w["close"].to_numpy(float)
    folds = E.fold_ids(panel_w["bucket_ms"].to_numpy())

    spec = pe.BookSpec(name="PSV1", phase="UPTREND", trigger="donchian_breakout",
                       donch_entry=pc.DONCH_ENTRY, donch_stop=pc.DONCH_STOP,
                       exit_buffer=pc.EXIT_BUFFER_BARS, min_hold=pc.MIN_HOLD_BARS,
                       max_hold=pc.MAX_HOLD_BARS, direction=1)
    trades, _ = run_book_instrumented(labels_w, close_w, spec, folds)
    comp_dec, _ = decision_series(trades, len(close_w))

    sma200 = np.isfinite(pd_rolling(close_w))
    rvol = E.rvol_series(panel_w)

    out = {"schema": "es1.dry_run@1", "sanitized": True,
           "note": "counts only; no returns/equity/PnL exist in this artifact",
           "cells": {}}
    cells_def = {
        "A1": E.sig_vol_managed(np.ones_like(close_w), rvol, 0.60),
        "A2": E.sig_vol_managed(E.sig_trend_lf(panel_w, 0.0), rvol, 0.60),
        "A3": E.sig_vol_managed(comp_dec, rvol, 0.60),
        "A4": E.sig_vol_managed(E.sig_trend_lf(panel_w, 0.0), rvol, 0.40),
        "C1": E.sig_trend_lf(panel_w, 0.01),
        "C2": E.sig_trend_lf(panel_w, 0.02),
        "C3": E.sig_trend_lf(panel_w, 0.03),
        "C4": E.sig_trend_lf(panel_w, 0.005),
        "COMPARATOR": comp_dec,
        "BASE_ALWAYS_ON": np.ones_like(close_w),
        "BASE_TREND_LF": E.sig_trend_lf(panel_w, 0.0),
        "G6A_SHUFFLED_SCALE_BASE_TREND": E.sig_vol_managed(
            E.sig_trend_lf(panel_w, 0.0), E.block_shuffle(rvol), 0.60),
        "G6C_SHUFFLED_STATE_BAND": E.block_shuffle(E.sig_trend_lf(panel_w, 0.01)),
    }
    vacuous = []
    for name, dec in cells_def.items():
        c = counts(name, dec, folds)
        out["cells"][name] = c
        if c["fills"] == 0:
            vacuous.append(name)
    # SPARSE_RISK_OFF baseline (PSV1 §8 law, causal state machine)
    peak = np.maximum.accumulate(close_w)
    dd = close_w / peak - 1.0
    sparse = np.zeros(len(close_w))
    state = 0
    held = 0
    for t in range(len(close_w)):
        if state == 0:
            if dd[t] >= -0.10:
                state, held = 1, 0
        else:
            held += 1
            if dd[t] <= -0.30 and held >= 5:
                state = 0
        sparse[t] = state
    out["cells"]["BASE_SPARSE_RISK_OFF"] = counts("BASE_SPARSE_RISK_OFF", sparse, folds)

    comp_entries = out["cells"]["COMPARATOR"]["entries"]
    out["non_vacuous_gate"] = "PASS" if not vacuous else f"FAIL {vacuous}"
    out["comparator_identity_entries_86"] = (comp_entries == 86)
    out["scale_bounds_ok"] = all(
        np.all(np.isfinite(np.asarray(cells_def[k]))) and np.nanmax(np.abs(cells_def[k])) <= 1.0 + 1e-12
        for k in cells_def)
    out["verdict"] = ("DRY_RUN_PASS" if (not vacuous and comp_entries == 86 and out["scale_bounds_ok"])
                      else "DRY_RUN_FAIL")
    (HERE.parent / "freezes" / "dry_run_counts.json").write_text(json.dumps(out, indent=1))
    summary = {k: {"fills": v["fills"], "entries": v["entries"], "exp": v["mean_exposure"]}
               for k, v in out["cells"].items()}
    print(json.dumps(summary, indent=1))
    print("verdict:", out["verdict"])
    sys.exit(0 if out["verdict"] == "DRY_RUN_PASS" else 2)


def pd_rolling(x):
    import pandas as pd
    return pd.Series(x).rolling(200).mean().to_numpy()


if __name__ == "__main__":
    main()
