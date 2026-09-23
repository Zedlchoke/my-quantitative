#!/usr/bin/env python
"""A2 downtrend census — ONE run against the frozen PSV1 BTC_H4 panel.

Counts only (outcome-blind): runs / dwell / occupancy / merges / floors /
descriptive price returns. NO strategy PnL, NO tuning, NO parameter search.

Primary label: PSV1 phase rule (imported verbatim, read-only, via
scored.cells.load_btc_h4). Secondary lens: close < SMA200(H4) (causal).
Counting rule: downtrend_census_rules_preregistered.json (written before this
run; its sha256 at count time is embedded in the output).
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PREREG = HERE / "downtrend_census_rules_preregistered.json"
OUT = HERE / "downtrend_census.json"

L2_STAGE = Path("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
                "lane-btc-h4/research/control/phase_strategy_v1/lane_btc_h4/data_staging")
SCORED_PKG = Path("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
                  "integration/research/control/phase_strategy_v1/scored")
sys.dont_write_bytecode = True          # never write .pyc into read-only PSV1 trees
sys.path.insert(0, str(SCORED_PKG))
import cells  # PSV1 scored namespace, read-only import (loader convention)


def runs_of(mask: np.ndarray):
    out = []
    n = len(mask)
    t = 0
    while t < n:
        if mask[t]:
            s = t
            while t + 1 < n and mask[t + 1]:
                t += 1
            out.append((s, t))
        t += 1
    return out


def merge_runs(rr, gap_flags, max_gap=12, gap_only_unknown=True):
    """Left-to-right merge of adjacent runs iff gap < max_gap and (for the
    primary label) every gap bar is TRANSITION_UNKNOWN. gap_flags: array of
    labels (primary) or None (lens -> any gap content merges)."""
    if not rr:
        return []
    merged = []
    cs, ce = rr[0]
    for (s, e) in rr[1:]:
        gap = s - ce - 1
        ok = 0 < gap < max_gap
        if ok and gap_only_unknown:
            ok = bool((gap_flags[ce + 1:s] == "TRANSITION_UNKNOWN").all())
        if ok:
            ce = e
        else:
            merged.append((cs, ce))
            cs, ce = s, e
    merged.append((cs, ce))
    return merged


def utc(ms):
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def census(mask: np.ndarray, labels_arr, close: np.ndarray, open_ms: np.ndarray,
           fold_ids: np.ndarray, gap_only_unknown: bool, fold_names):
    rr = runs_of(mask)
    merged = merge_runs(rr, labels_arr, max_gap=12, gap_only_unknown=gap_only_unknown)
    lengths = [e - s + 1 for s, e in rr]
    merged_lengths = [e - s + 1 for s, e in merged]

    per_run = []
    for (s, e) in rr:
        ret = float(close[e] / close[s] - 1.0)
        per_run.append({
            "start_open_utc": utc(open_ms[s]),
            "end_open_utc": utc(open_ms[e]),
            "end_close_utc": utc(open_ms[e] + 4 * 3600 * 1000 - 1),
            "bars": int(e - s + 1),
            "days": round((e - s + 1) * 4 / 24.0, 2),
            "left_censored": bool(s == 0),
            "right_censored": bool(e == len(mask) - 1),
            "folds_spanned": sorted({fold_names[f] for f in set(fold_ids[s:e + 1].tolist())}),
            "btc_close_to_close_return_over_run": round(ret, 6),
        })

    per_fold = {}
    for fi, fname in enumerate(fold_names):
        fm = mask & (fold_ids == fi)
        fr = runs_of(fm)
        fmerged = merge_runs(fr, labels_arr, max_gap=12, gap_only_unknown=gap_only_unknown)
        per_fold[fname] = {
            "bars_in_fold": int((fold_ids == fi).sum()),
            "label_bars": int(fm.sum()),
            "occupancy_share_of_fold": round(float(fm.sum()) / max(1, int((fold_ids == fi).sum())), 6),
            "episodes_raw_fold_clipped": len(fr),
            "episodes_merged_independent_estimate": len(fmerged),
            "decisions_label_bars": int(fm.sum()),
        }
    return {
        "window_bars": int(len(mask)),
        "label_bars": int(mask.sum()),
        "occupancy_share_of_window": round(float(mask.sum()) / max(1, len(mask)), 6),
        "runs_raw": len(rr),
        "run_lengths": {"min": int(min(lengths)) if lengths else None,
                        "median": float(np.median(lengths)) if lengths else None,
                        "max": int(max(lengths)) if lengths else None},
        "runs_ge_6_bars": int(sum(1 for L in lengths if L >= 6)),
        "runs_ge_24_bars": int(sum(1 for L in lengths if L >= 24)),
        "runs_ge_72_bars": int(sum(1 for L in lengths if L >= 72)),
        "runs_merged_independent_estimate": len(merged),
        "merged_lengths": {"min": int(min(merged_lengths)) if merged_lengths else None,
                           "median": float(np.median(merged_lengths)) if merged_lengths else None,
                           "max": int(max(merged_lengths)) if merged_lengths else None},
        "total_decisions_label_bars": int(mask.sum()),
        "per_fold": per_fold,
        "per_run": per_run,
    }


def main():
    prereg = json.loads(PREREG.read_text())
    prereg_sha = hashlib.sha256(PREREG.read_bytes()).hexdigest()

    data = cells.load_btc_h4()   # PSV1 loader verbatim: warmup truncated inside
    from pipeline import config as cfg2  # noqa: pipeline pkg registered by load_btc_h4
    W = int(cfg2.WARMUP)
    labels = np.asarray([str(x) for x in data["labels"]])
    close = data["close"]
    open_ms = data["open_ms"]
    fold_ids = data["fold_ids"]
    fold_names = [f"F{i+1}" for i in range(4)]

    # phase occupancy context (all labels, window only)
    uniq, cnts = np.unique(labels, return_counts=True)
    occupancy_all = {str(u): int(c) for u, c in zip(uniq, cnts)}

    # ---------------- primary: PSV1 DOWNTREND ----------------
    primary = census(labels == "DOWNTREND", labels, close, open_ms, fold_ids,
                     gap_only_unknown=True, fold_names=fold_names)

    # ---------------- secondary lens: close < SMA200(H4) ----------------
    # SMA200 needs bars BEFORE the window: compute on the full staged panel.
    h4 = pd.read_parquet(L2_STAGE / "scored_h4.parquet")
    full_close = h4["close"].to_numpy(float)
    sma200_full = pd.Series(full_close).rolling(200).mean().to_numpy()
    lens_full = np.where(np.isfinite(sma200_full),
                         full_close < sma200_full, np.zeros_like(full_close, dtype=bool))
    lens_win = lens_full[W:].astype(bool)
    lens_valid_win = np.isfinite(sma200_full[W:])
    assert len(lens_win) == len(labels)

    lens_close = full_close[W:]
    lens_open_ms = h4["bucket_ms"].to_numpy()[W:]
    lens = census(lens_win, None, lens_close, lens_open_ms, fold_ids,
                  gap_only_unknown=False, fold_names=fold_names)
    lens["bars_where_lens_undefined_in_window"] = int((~lens_valid_win).sum())

    # agreement on the overlap (window indices where the lens is defined)
    ov = lens_valid_win
    a = labels[ov] == "DOWNTREND"
    b = lens_win[ov]
    agree = float((a == b).mean())
    tp = int((a & b).sum()); tn = int(((~a) & (~b)).sum())
    fp = int((b & ~a).sum()); fn_ = int((a & ~b).sum())
    agreement = {
        "overlap_bars": int(ov.sum()),
        "excluded_bars_lens_warmup": int((~ov).sum()),
        "identical_down_vs_not_share": round(agree, 6),
        "contingency": {"both_down": tp, "lens_only_down": fp,
                        "phase_only_down": fn_, "both_not_down": tn},
    }

    # ---------------- floors (PSV1 config, verbatim) ----------------
    F_CELL, F_FOLD, F_DEC = 20, 3, 100
    floors = {
        "floor_episodes_per_phase_cell": F_CELL,
        "floor_episodes_per_phase_fold": F_FOLD,
        "floor_decisions_per_phase_fold": F_DEC,
        "floor_source": "PSV1 lane_btc_h4 pipeline/config.py (plan section 4.3); verbatim",
        "primary_DOWNTREND": {
            "episodes_cell_total_raw": primary["runs_raw"],
            "episodes_cell_total_merged_independent_estimate": primary["runs_merged_independent_estimate"],
            "margin_vs_20_raw": primary["runs_raw"] - F_CELL,
            "margin_vs_20_merged": primary["runs_merged_independent_estimate"] - F_CELL,
            "floor_cell_raw": primary["runs_raw"] >= F_CELL,
            "floor_cell_merged": primary["runs_merged_independent_estimate"] >= F_CELL,
            "per_fold": {f: {
                "episodes_raw": primary["per_fold"][f]["episodes_raw_fold_clipped"],
                "episodes_merged": primary["per_fold"][f]["episodes_merged_independent_estimate"],
                "decisions": primary["per_fold"][f]["decisions_label_bars"],
                "floor_episodes_fold": primary["per_fold"][f]["episodes_raw_fold_clipped"] >= F_FOLD,
                "floor_decisions_fold": primary["per_fold"][f]["decisions_label_bars"] >= F_DEC,
            } for f in fold_names},
            "all_folds_meet_episodes_fold": all(
                primary["per_fold"][f]["episodes_raw_fold_clipped"] >= F_FOLD for f in fold_names),
            "all_folds_meet_decisions_fold": all(
                primary["per_fold"][f]["decisions_label_bars"] >= F_DEC for f in fold_names),
        },
        "secondary_lens_descriptive_not_adjudicated": {
            f: {"episodes_raw": lens["per_fold"][f]["episodes_raw_fold_clipped"],
                "episodes_merged": lens["per_fold"][f]["episodes_merged_independent_estimate"],
                "decisions": lens["per_fold"][f]["decisions_label_bars"]}
            for f in fold_names},
    }

    out = {
        "schema": "a2_downtrend_census@1",
        "cell": "BTC_H4",
        "preregistration": {
            "path": str(PREREG), "sha256_at_count_time": prereg_sha,
            "preregistered_utc": prereg["preregistered_utc"],
            "counted_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "one_shot": True},
        "panel": {
            "window_first_open_utc": utc(open_ms[0]),
            "window_last_open_utc": utc(open_ms[-1]),
            "window_last_close_utc": utc(open_ms[-1] + 4 * 3600 * 1000 - 1),
            "window_bars": int(len(labels)),
            "warmup_truncated_bars": W,
            "fold_law": "F_i = ERA-Bi (PSV1 plan 4.1/4.3), post-warmup"},
        "label_occupancy_all_phases_window": occupancy_all,
        "primary_psv1_phase_rule": primary,
        "secondary_sma200_lens": lens,
        "primary_vs_lens_agreement": agreement,
        "floors": floors,
        "outcome_blindness": "counts/dwell/occupancy/merges/floors + descriptive BTC price returns over runs ONLY. No strategy PnL, positions, costs or tuning exist in this artifact.",
    }
    OUT.write_text(json.dumps(out, indent=2))
    print("WROTE", OUT)
    # console headline
    print("window:", out["panel"]["window_first_open_utc"], "->", out["panel"]["window_last_close_utc"],
          f"({out['panel']['window_bars']} bars)")
    print("DOWNTREND occupancy:", primary["occupancy_share_of_window"],
          "| raw runs:", primary["runs_raw"], "| merged:", primary["runs_merged_independent_estimate"])
    print("lens occupancy:", lens["occupancy_share_of_window"],
          "| raw runs:", lens["runs_raw"], "| merged:", lens["runs_merged_independent_estimate"])
    print("agreement:", agreement["identical_down_vs_not_share"])
    print("floors cell raw/merged:", floors["primary_DOWNTREND"]["floor_cell_raw"],
          floors["primary_DOWNTREND"]["floor_cell_merged"],
          "| folds episodes/decisions:",
          floors["primary_DOWNTREND"]["all_folds_meet_episodes_fold"],
          floors["primary_DOWNTREND"]["all_folds_meet_decisions_fold"])


if __name__ == "__main__":
    main()
