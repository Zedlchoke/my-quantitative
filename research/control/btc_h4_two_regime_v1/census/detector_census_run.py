#!/usr/bin/env python
"""BTC-H4-TWO-REGIME-V1 P1 detector census — ONE run against the frozen PSV1
BTC_H4 panel.

Counts/audits only (outcome-blind): states / transitions / dwell / occupancy
/ episodes / floors / lag / agreement / fixtures. NO strategy PnL, NO tuning,
NO parameter search. Rule frozen in detector_preregistration.json (hashed at
count time) and in plans/PLAN_btc_h4_two_regime_v1.md section 1 (113e0c2d).
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
PREREG = HERE / "detector_preregistration.json"
OUT = HERE / "detector_census.json"

L2_STAGE = Path("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
                "lane-btc-h4/research/control/phase_strategy_v1/lane_btc_h4/data_staging")
PSV1_MANIFEST = Path("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
                     "integration/research/control/phase_strategy_v1/lane_btc_h4/data/manifest.json")
SCORED_PKG = Path("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
                  "integration/research/control/phase_strategy_v1/scored")

DD_BEAR = -0.30
DD_RECOVER = -0.10
BULL_DWELL = 90
STATES = ["BULL", "BEAR", "UNCERTAIN"]


def utc(ms: float) -> str:
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def run_machine(close: np.ndarray, dd_bear: float = DD_BEAR,
                dd_rec: float = DD_RECOVER, dwell: int = BULL_DWELL) -> np.ndarray:
    """Plan section 1.3 state machine, evaluated bar by bar (causal)."""
    n = len(close)
    runmax = np.maximum.accumulate(close)
    dd = close / runmax - 1.0
    states = np.empty(n, dtype=object)
    state = "UNCERTAIN"
    streak = 0
    for t in range(n):
        d = dd[t]
        if d <= dd_bear:
            state, streak = "BEAR", 0
        elif state == "BEAR" and d >= dd_rec:
            state, streak = "UNCERTAIN", 1
        elif state == "UNCERTAIN":
            if d >= dd_rec:
                streak += 1
                if streak >= dwell:
                    state, streak = "BULL", 0
            else:
                streak = 0
        states[t] = state
    return states


def runs_of(labels: np.ndarray, value):
    out, n, t = [], len(labels), 0
    while t < n:
        if labels[t] == value:
            s = t
            while t + 1 < n and labels[t + 1] == value:
                t += 1
            out.append((s, t))
        t += 1
    return out


def merge_runs(rr, max_gap=12):
    if not rr:
        return []
    merged, (cs, ce) = [], rr[0]
    for (s, e) in rr[1:]:
        if 0 < s - ce - 1 < max_gap:
            ce = e
        else:
            merged.append((cs, ce))
            cs, ce = s, e
    merged.append((cs, ce))
    return merged


def state_census(states, fold_ids, fold_names, open_ms, close):
    res = {}
    for st in STATES:
        mask = states == st
        rr = runs_of(states, st)
        merged = merge_runs(rr)
        lengths = [e - s + 1 for s, e in rr]
        m_lengths = [e - s + 1 for s, e in merged]
        per_fold = {}
        for fi, fname in enumerate(fold_names):
            idx = np.where(fold_ids == fi)[0]
            fm = mask[idx]
            fr = runs_of(fm, True)
            fmerged = merge_runs(fr)
            per_fold[fname] = {
                "bars_in_fold": int(len(idx)),
                "state_bars": int(fm.sum()),
                "occupancy_share_of_fold": round(float(fm.sum()) / max(1, len(idx)), 6),
                "episodes_raw_fold_clipped": len(fr),
                "episodes_merged_independent_estimate": len(fmerged),
                "decisions_state_bars": int(fm.sum()),
            }
        per_run = [{
            "start_open_utc": utc(open_ms[s]), "end_open_utc": utc(open_ms[e]),
            "bars": int(e - s + 1), "days": round((e - s + 1) * 4 / 24.0, 2),
            "left_censored": bool(s == 0), "right_censored": bool(e == len(states) - 1),
        } for (s, e) in rr]
        res[st] = {
            "bars": int(mask.sum()),
            "occupancy_share_of_window": round(float(mask.sum()) / max(1, len(states)), 6),
            "runs_raw": len(rr),
            "runs_merged_independent_estimate": len(merged),
            "run_lengths_raw": {"min": int(min(lengths)) if lengths else None,
                                "median": float(np.median(lengths)) if lengths else None,
                                "max": int(max(lengths)) if lengths else None},
            "run_lengths_merged": {"min": int(min(m_lengths)) if m_lengths else None,
                                   "median": float(np.median(m_lengths)) if m_lengths else None,
                                   "max": int(max(m_lengths)) if m_lengths else None},
            "per_fold": per_fold,
            "per_run_raw": per_run,
        }
    # transition matrix (state-pair counts over consecutive bars)
    tm = {a: {b: 0 for b in STATES} for a in STATES}
    for t in range(1, len(states)):
        if states[t] != states[t - 1]:
            tm[states[t - 1]][states[t]] += 1
    transitions_total = sum(sum(row.values()) for row in tm.values())
    return res, tm, transitions_total


def floors(res):
    out = {}
    for st in STATES:
        r = res[st]
        merged = r["runs_merged_independent_estimate"]
        raw_all_folds = all(r["per_fold"][f]["episodes_raw_fold_clipped"] >= 3 for f in r["per_fold"])
        dec_all_folds = all(r["per_fold"][f]["decisions_state_bars"] >= 100 for f in r["per_fold"])
        out[st] = {
            "episodes_cell_merged": merged, "floor_cell_20": merged >= 20,
            "margin_vs_20": merged - 20,
            "all_folds_episodes_ge3_raw": raw_all_folds,
            "all_folds_decisions_ge100": dec_all_folds,
            "state_floors_pass": bool(merged >= 20 and raw_all_folds and dec_all_folds),
        }
    return out


def contingency(a: np.ndarray, b: np.ndarray):
    return {"a_true_b_true": int((a & b).sum()), "a_true_b_false": int((a & ~b).sum()),
            "a_false_b_true": int((~a & b).sum()), "a_false_b_false": int((~a & ~b).sum()),
            "agreement_share": round(float((a == b).mean()), 6)}


def sensitivity(close: np.ndarray, central: np.ndarray):
    table = {}
    for db in (-0.25, -0.30, -0.35):
        for dr in (-0.05, -0.10, -0.15):
            for dw in (60, 90, 120):
                s = run_machine(close, db, dr, dw)
                table[f"DD_BEAR={db}|DD_RECOVER={dr}|DWELL={dw}"] = round(
                    float((s == central).mean()), 6)
    return table


def main():
    prereg_bytes = PREREG.read_bytes()
    prereg = json.loads(prereg_bytes)
    prereg_sha = hashlib.sha256(prereg_bytes).hexdigest()
    assert prereg["constants"]["DD_BEAR"] == DD_BEAR
    assert prereg["constants"]["DD_RECOVER"] == DD_RECOVER
    assert prereg["constants"]["BULL_DWELL_BARS"] == BULL_DWELL

    manifest_sha = hashlib.sha256(PSV1_MANIFEST.read_bytes()).hexdigest()
    assert manifest_sha == prereg["panel"]["expected_manifest_sha256"], (
        f"manifest drift: {manifest_sha}")

    sys.dont_write_bytecode = True
    sys.path.insert(0, str(SCORED_PKG))
    import cells  # PSV1 scored namespace, verbatim read-only
    data = cells.load_btc_h4()
    from pipeline import config as cfg  # noqa: registered by load_btc_h4
    W = int(cfg.WARMUP)

    h4 = pd.read_parquet(L2_STAGE / "scored_h4.parquet")
    full_close = h4["close"].to_numpy(float)
    full_open_ms = h4["bucket_ms"].to_numpy()
    n = len(full_close)

    states_full = run_machine(full_close)
    states = states_full[W:]
    close_w = full_close[W:]
    open_w = full_open_ms[W:]
    fold_ids = np.asarray(data["fold_ids"])
    fold_names = [f"F{i+1}" for i in range(4)]
    assert len(states) == len(fold_ids)

    res, tm, ntrans = state_census(states, fold_ids, fold_names, open_w, close_w)

    # detection lag (DESCRIPTIVE ONLY vs public calendar anchors)
    open_dt = pd.to_datetime(open_w, unit="ms", utc=True)
    top_anchor = pd.Timestamp("2021-04-30 00:00", tz="UTC")
    bot_anchor = pd.Timestamp("2022-12-31 00:00", tz="UTC")
    i_top = int(np.searchsorted(open_dt.values, np.datetime64(top_anchor.tz_convert(None))))
    i_bot = int(np.searchsorted(open_dt.values, np.datetime64(bot_anchor.tz_convert(None))))
    first_bear_after_top = next((i for i in range(i_top, len(states)) if states[i] == "BEAR"), None)
    first_bull_after_bot = next((i for i in range(i_bot, len(states)) if states[i] == "BULL"), None)
    lag = {
        "anchor_top_2021_04_30": {
            "first_BEAR_entry_utc": utc(open_w[first_bear_after_top]) if first_bear_after_top is not None else None,
            "lag_bars": (first_bear_after_top - i_top) if first_bear_after_top is not None else None,
            "lag_days": round((first_bear_after_top - i_top) * 4 / 24.0, 1) if first_bear_after_top is not None else None,
        },
        "anchor_bottom_2022_12_31": {
            "first_BULL_entry_utc": utc(open_w[first_bull_after_bot]) if first_bull_after_bot is not None else None,
            "lag_bars": (first_bull_after_bot - i_bot) if first_bull_after_bot is not None else None,
            "lag_days": round((first_bull_after_bot - i_bot) * 4 / 24.0, 1) if first_bull_after_bot is not None else None,
        },
        "law": "descriptive measurement only; never a rule input (plan section 1.4)",
    }

    # audit vs PSV1 UPTREND label and SMA200(H4) lens
    psv1_labels = np.asarray([str(x) for x in data["labels"]])
    uptrend = psv1_labels == "UPTREND"
    bull = states == "BULL"
    bear = states == "BEAR"
    sma200_full = pd.Series(full_close).rolling(200).mean().to_numpy()
    lens_defined = np.isfinite(sma200_full[W:])
    lens_up = np.where(lens_defined, full_close[W:] > sma200_full[W:], False).astype(bool)

    audits = {
        "BULL_vs_PSV1_UPTREND": contingency(bull, uptrend),
        "BEAR_vs_PSV1_DOWNTREND": contingency(bear, psv1_labels == "DOWNTREND"),
        "BULL_vs_SMA200H4_lens": contingency(bull[lens_defined], lens_up[lens_defined]),
        "state_bars_where_lens_undefined": int((~lens_defined).sum()),
        "note": "V2 forensic fact carried: the PSV1 UPTREND/SMA200 gate bound 0/86 entry bars; "
                "identity or near-identity of the new BULL law with either label is ancestry evidence.",
    }

    # fixtures: no-lookahead mutation + hysteresis behavior
    mut = full_close.copy()
    mut[-1] = mut[-1] * 1.5
    states_mut = run_machine(mut)
    nolook_prefix_identical = bool(np.array_equal(states_full[:-1], states_mut[:-1]))
    fixtures = {
        "no_lookahead_mutation_last_bar_x1.5_prefix_identical": nolook_prefix_identical,
        "note": "perturbing the LAST bar must not change ANY earlier state",
    }
    if not nolook_prefix_identical:
        raise SystemExit("FIXTURE FAIL: no-lookahead mutation changed past states")

    out = {
        "schema": "trv1_detector_census@1",
        "cycle_id": "BTC-H4-TWO-REGIME-V1",
        "preregistration": {
            "path": str(PREREG), "sha256_at_count_time": prereg_sha,
            "counted_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "one_shot": True,
            "plan_authority": "plans/PLAN_btc_h4_two_regime_v1.md section 1 (commit 113e0c2d)"},
        "panel": {
            "manifest_sha256": manifest_sha,
            "full_panel_bars": int(n),
            "window_first_open_utc": utc(open_w[0]),
            "window_last_open_utc": utc(open_w[-1]),
            "window_bars": int(len(states)),
            "warmup_truncated_bars": int(W),
            "fold_law": "F_i = ERA-Bi (PSV1 plan 4.1/4.3), post-warmup"},
        "central_machine_states": res,
        "transition_matrix_counts": tm,
        "transitions_total": ntrans,
        "detection_lag_descriptive": lag,
        "audits_vs_old_labels": audits,
        "floors": floors(res),
        "sensitivity_ladder_report_only": sensitivity(full_close, states_full),
        "fixtures": fixtures,
        "outcome_blindness": "states/transitions/dwell/occupancy/floors/lag/agreement ONLY. "
                             "No strategy PnL, positions, costs or tuning exist in this artifact.",
    }
    OUT.write_text(json.dumps(out, indent=2))
    print("WROTE", OUT)
    print("window:", out["panel"]["window_first_open_utc"], "->", out["panel"]["window_last_open_utc"],
          f"({out['panel']['window_bars']} bars)")
    for st in STATES:
        f = floors(res)[st]
        print(f"{st:9s} bars={res[st]['bars']:6d} occ={res[st]['occupancy_share_of_window']:.3f} "
              f"raw_runs={res[st]['runs_raw']:3d} merged={res[st]['runs_merged_independent_estimate']:3d} "
              f"floors_pass={f['state_floors_pass']} (margin_vs_20={f['margin_vs_20']})")
    print("transitions_total:", ntrans, "| matrix:", json.dumps(tm))
    print("lag_top->BEAR:", lag["anchor_top_2021_04_30"], )
    print("lag_bottom->BULL:", lag["anchor_bottom_2022_12_31"])
    print("audit BULL~UPTREND:", audits["BULL_vs_PSV1_UPTREND"]["agreement_share"],
          "| BULL~SMA200:", audits["BULL_vs_SMA200H4_lens"]["agreement_share"],
          "| BEAR~DOWNTREND:", audits["BEAR_vs_PSV1_DOWNTREND"]["agreement_share"])


if __name__ == "__main__":
    main()
