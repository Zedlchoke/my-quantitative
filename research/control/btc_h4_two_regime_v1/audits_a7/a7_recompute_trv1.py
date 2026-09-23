#!/usr/bin/env python
"""A7 INDEPENDENT recompute for BTC-H4-TWO-REGIME-V1 terminal audit.

Written fresh by A7 from plans/PLAN_btc_h4_two_regime_v1.md section 1 (the
law), NOT from the census implementation. Recomputes the census numbers from
the staged panel bytes and compares them to the committed
detector_census.json within 1e-6. Counts/audits only — NO strategy PnL.

Usage: /Users/hoangminhlong/my-quantitative/.venv/bin/python a7_recompute_trv1.py
Writes: a7_recompute_result.json next to this file.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/btc-h4-two-regime-v1/integration")
CTRL = WT / "research/control/btc_h4_two_regime_v1"
HERE = Path(__file__).resolve().parent
PREREG = CTRL / "census/detector_preregistration.json"
CENSUS = CTRL / "census/detector_census.json"
STAGED = Path("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
              "lane-btc-h4/research/control/phase_strategy_v1/lane_btc_h4/data_staging/scored_h4.parquet")
MANIFEST = Path("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
                "integration/research/control/phase_strategy_v1/lane_btc_h4/data/manifest.json")
SCORED_PKG = Path("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
                  "integration/research/control/phase_strategy_v1/scored")
ROOT = Path("/Users/hoangminhlong/my-quantitative")

# ---- A7's own reading of plan section 1 (hardcoded from the PLAN text) ----
DD_BEAR = -0.30
DD_RECOVER = -0.10
BULL_DWELL = 90
WARMUP = 153                      # PSV1 lane convention (plan section 0)
FOLD_EDGES = ["2021-05-01", "2023-01-01", "2025-01-01"]
MERGE_GAP_BARS = 12
FLOORS = {"cell_episodes": 20, "fold_episodes_raw": 3, "fold_decisions": 100}
ANCHOR_TOP = "2021-04-30 00:00"   # public calendar anchor, descriptive only
ANCHOR_BOT = "2022-12-31 00:00"

checks: list[dict] = []


def chk(name, mine, theirs, tol=1e-6):
    if isinstance(mine, float) or isinstance(theirs, float):
        try:
            ok = abs(float(mine) - float(theirs)) <= tol
        except (TypeError, ValueError):
            ok = mine == theirs
    else:
        ok = mine == theirs
    checks.append({"metric": name, "a7": mine, "census": theirs, "ok": bool(ok)})
    return ok


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---------------- state machine, written from plan section 1.3 -------------
def run_machine(close: np.ndarray, start: int = 0, runmax_full: np.ndarray | None = None,
                dd_bear: float = DD_BEAR, dd_rec: float = DD_RECOVER,
                dwell: int = BULL_DWELL) -> np.ndarray:
    """Causal three-state machine. Rules in order at each close t:
    1) dd <= DD_BEAR                -> BEAR (any state, immediate)
    2) BEAR and dd >= DD_RECOVER    -> UNCERTAIN
    3) UNCERTAIN and dd >= DD_RECOVER sustained for BULL_DWELL consecutive
       bars (streak reset by any dd < DD_RECOVER bar and by entering BEAR)
                                    -> BULL
    4) otherwise hold. Initial state UNCERTAIN. BULL exits only via rule 1.
    start>0 begins evaluation at bar `start` with initial UNCERTAIN (variant b);
    runmax_full supplies the panel-wide running max for that variant."""
    seg = close[start:]
    runmax = runmax_full[start:] if runmax_full is not None else np.maximum.accumulate(seg)
    dd = seg / runmax - 1.0
    states = np.empty(len(seg), dtype=object)
    state, streak = "UNCERTAIN", 0
    for t in range(len(seg)):
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


def runs_of(mask_or_labels, value):
    lab = mask_or_labels
    out, n, t = [], len(lab), 0
    while t < n:
        if lab[t] == value:
            s = t
            while t + 1 < n and lab[t + 1] == value:
                t += 1
            out.append((s, t))
        t += 1
    return out


def merge_runs(rr, max_gap=MERGE_GAP_BARS):
    if not rr:
        return []
    merged, (cs, ce) = [], rr[0]
    for (s, e) in rr[1:]:
        gap = s - ce - 1                     # bars strictly between the runs
        if 0 < gap < max_gap:
            ce = e
        else:
            merged.append((cs, ce))
            cs, ce = s, e
    merged.append((cs, ce))
    return merged


def fmt_utc(ms) -> str:
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def main() -> int:
    # ---------- STEP 0: identity + hash chain ----------
    head = subprocess.run(["git", "-C", str(WT), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    blob = subprocess.run(["git", "-C", str(WT), "show", f"HEAD:research/control/"
                           f"btc_h4_two_regime_v1/census/detector_preregistration.json"],
                          capture_output=True, check=True).stdout
    prereg_wt_sha = sha256_file(PREREG)
    prereg_head_sha = hashlib.sha256(blob).hexdigest()
    census = json.loads(CENSUS.read_text())
    prereg = json.loads(PREREG.read_text())
    manifest_sha = sha256_file(MANIFEST)

    chk("head_is_dispatch_sha", head, "b34741952086cf04a00e363da78a2a96da9bf4bd", tol=0)
    chk("prereg_sha_worktree", prereg_wt_sha,
        census["preregistration"]["sha256_at_count_time"], tol=0)
    chk("prereg_sha_git_head_blob", prereg_head_sha, prereg_wt_sha, tol=0)
    chk("prereg_constants", [prereg["constants"]["DD_BEAR"], prereg["constants"]["DD_RECOVER"],
                             prereg["constants"]["BULL_DWELL_BARS"]],
        [DD_BEAR, DD_RECOVER, BULL_DWELL], tol=0)
    chk("manifest_sha256", manifest_sha,
        "3f1a668798c82fbfe7311fadf65a300a583043cdbeba226164bd28c81885b66d", tol=0)
    chk("staged_panel_exists", STAGED.exists(), True, tol=0)

    # ---------- STEP 1: panel + own fold assignment ----------
    h4 = pd.read_parquet(STAGED)
    close_full = h4["close"].to_numpy(float)
    open_ms_full = h4["bucket_ms"].to_numpy(np.int64)
    n = len(close_full)
    runmax_full = np.maximum.accumulate(close_full)

    states_full = run_machine(close_full)               # machine from panel bar 0
    states = states_full[WARMUP:]
    open_ms = open_ms_full[WARMUP:]
    W = len(states)

    ts = pd.to_datetime(open_ms_full, unit="ms", utc=True)
    edges = [pd.Timestamp(e, tz="UTC") for e in FOLD_EDGES]
    fold_own = np.empty(n, dtype=int)
    fold_own[:] = 0
    fold_own[ts.values >= np.datetime64(edges[0].tz_convert(None))] = 1
    fold_own[ts.values >= np.datetime64(edges[1].tz_convert(None))] = 2
    fold_own[ts.values >= np.datetime64(edges[2].tz_convert(None))] = 3
    fold_own = fold_own[WARMUP:]

    # PSV1 labels/folds imported VERBATIM read-only (audit path only)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(SCORED_PKG))
    import cells  # noqa: E402  (read-only import of the PSV1 scored namespace)
    data = cells.load_btc_h4()
    fold_psv1 = np.asarray(data["fold_ids"], dtype=int)
    labels = np.asarray([str(x) for x in data["labels"]])
    chk("warmup_is_153", WARMUP, 153, tol=0)
    chk("fold_own_vs_psv1_mismatches", int((fold_own != fold_psv1).sum()), 0, tol=0)
    chk("full_panel_bars", n, census["panel"]["full_panel_bars"], tol=0)
    chk("window_bars", W, census["panel"]["window_bars"], tol=0)
    chk("window_first_open_utc", fmt_utc(open_ms[0]), census["panel"]["window_first_open_utc"], tol=0)
    chk("window_last_open_utc", fmt_utc(open_ms[-1]), census["panel"]["window_last_open_utc"], tol=0)

    # ---------- STEP 2: per-state census on the window ----------
    STATES = ["BULL", "BEAR", "UNCERTAIN"]
    res = {}
    for st in STATES:
        mask = states == st
        rr = runs_of(states, st)
        merged = merge_runs(rr)
        per_fold = {}
        for fi, fname in enumerate(["F1", "F2", "F3", "F4"]):
            idx = np.where(fold_own == fi)[0]
            fm = mask[idx]
            fr = runs_of(fm, True)
            per_fold[fname] = {
                "bars_in_fold": int(len(idx)),
                "state_bars": int(fm.sum()),
                "occupancy_share_of_fold": round(float(fm.sum()) / max(1, len(idx)), 6),
                "episodes_raw_fold_clipped": len(fr),
                "episodes_merged_fold": len(merge_runs(fr)),
                "decisions_state_bars": int(fm.sum()),
            }
        res[st] = {
            "bars": int(mask.sum()),
            "occupancy_share_of_window": round(float(mask.sum()) / max(1, W), 6),
            "runs_raw": len(rr),
            "runs_merged": len(merged),
            "run_lengths_raw": {"min": int(min(e - s + 1 for s, e in rr)) if rr else None,
                                "median": float(np.median([e - s + 1 for s, e in rr])) if rr else None,
                                "max": int(max(e - s + 1 for s, e in rr)) if rr else None},
            "per_fold": per_fold,
            "per_run_raw": [{"start_open_utc": fmt_utc(open_ms[s]), "end_open_utc": fmt_utc(open_ms[e]),
                             "bars": int(e - s + 1), "days": round((e - s + 1) * 4 / 24.0, 2),
                             "left_censored": bool(s == 0),
                             "right_censored": bool(e == W - 1)} for (s, e) in rr],
        }
        cc = census["central_machine_states"][st]
        chk(f"{st}.bars", res[st]["bars"], cc["bars"], tol=0)
        chk(f"{st}.occupancy", res[st]["occupancy_share_of_window"],
            cc["occupancy_share_of_window"])
        chk(f"{st}.runs_raw", res[st]["runs_raw"], cc["runs_raw"], tol=0)
        chk(f"{st}.runs_merged", res[st]["runs_merged"],
            cc["runs_merged_independent_estimate"], tol=0)
        for k in ("min", "median", "max"):
            chk(f"{st}.runlen_raw.{k}", res[st]["run_lengths_raw"][k],
                cc["run_lengths_raw"][k], tol=0)
        for f in ("F1", "F2", "F3", "F4"):
            for k in ("bars_in_fold", "state_bars", "episodes_raw_fold_clipped",
                      "decisions_state_bars"):
                chk(f"{st}.{f}.{k}", res[st]["per_fold"][f][k], cc["per_fold"][f][k], tol=0)
            chk(f"{st}.{f}.occupancy", res[st]["per_fold"][f]["occupancy_share_of_fold"],
                cc["per_fold"][f]["occupancy_share_of_fold"])
        chk(f"{st}.n_runs_listed", len(res[st]["per_run_raw"]), len(cc["per_run_raw"]), tol=0)
        for i, (a, b) in enumerate(zip(res[st]["per_run_raw"], cc["per_run_raw"])):
            chk(f"{st}.run{i}.span", [a["start_open_utc"], a["end_open_utc"], a["bars"],
                                      a["left_censored"], a["right_censored"]],
                [b["start_open_utc"], b["end_open_utc"], b["bars"],
                 b["left_censored"], b["right_censored"]], tol=0)

    # transitions
    tm = {a: {b: 0 for b in STATES} for a in STATES}
    for t in range(1, W):
        if states[t] != states[t - 1]:
            tm[states[t - 1]][states[t]] += 1
    ntrans = sum(sum(r.values()) for r in tm.values())
    chk("transitions_total", ntrans, census["transitions_total"], tol=0)
    for a in STATES:
        for b in STATES:
            chk(f"tm.{a}->{b}", tm[a][b], census["transition_matrix_counts"][a][b], tol=0)

    # detection lag (descriptive)
    top_ms = int(pd.Timestamp(ANCHOR_TOP, tz="UTC").timestamp() * 1000)
    bot_ms = int(pd.Timestamp(ANCHOR_BOT, tz="UTC").timestamp() * 1000)
    i_top = int(np.searchsorted(open_ms, top_ms))
    i_bot = int(np.searchsorted(open_ms, bot_ms))
    fb = next(i for i in range(i_top, W) if states[i] == "BEAR")
    fu = next(i for i in range(i_bot, W) if states[i] == "BULL")
    chk("lag_top.first_BEAR_utc", fmt_utc(open_ms[fb]),
        census["detection_lag_descriptive"]["anchor_top_2021_04_30"]["first_BEAR_entry_utc"], tol=0)
    chk("lag_top.lag_bars", fb - i_top,
        census["detection_lag_descriptive"]["anchor_top_2021_04_30"]["lag_bars"], tol=0)
    chk("lag_top.lag_days", round((fb - i_top) * 4 / 24.0, 1),
        census["detection_lag_descriptive"]["anchor_top_2021_04_30"]["lag_days"])
    chk("lag_bot.first_BULL_utc", fmt_utc(open_ms[fu]),
        census["detection_lag_descriptive"]["anchor_bottom_2022_12_31"]["first_BULL_entry_utc"], tol=0)
    chk("lag_bot.lag_bars", fu - i_bot,
        census["detection_lag_descriptive"]["anchor_bottom_2022_12_31"]["lag_bars"], tol=0)
    chk("lag_bot.lag_days", round((fu - i_bot) * 4 / 24.0, 1),
        census["detection_lag_descriptive"]["anchor_bottom_2022_12_31"]["lag_days"])

    # ---------- STEP 3: floors per plan section 1.5 ----------
    floors = {}
    for st in STATES:
        merged_cell = res[st]["runs_merged"]
        raw_ok = all(res[st]["per_fold"][f]["episodes_raw_fold_clipped"] >= FLOORS["fold_episodes_raw"]
                     for f in ("F1", "F2", "F3", "F4"))
        dec_ok = all(res[st]["per_fold"][f]["decisions_state_bars"] >= FLOORS["fold_decisions"]
                     for f in ("F1", "F2", "F3", "F4"))
        # harsher PSV1 4.3 literal reading: fold floor on merged (independent) episodes
        mrg_ok = all(res[st]["per_fold"][f]["episodes_merged_fold"] >= FLOORS["fold_episodes_raw"]
                     for f in ("F1", "F2", "F3", "F4"))
        floors[st] = {
            "episodes_cell_merged": merged_cell,
            "cell_ge_20": merged_cell >= FLOORS["cell_episodes"],
            "all_folds_raw_ge_3": raw_ok,
            "all_folds_merged_ge_3_psv1_literal": mrg_ok,
            "all_folds_decisions_ge_100": dec_ok,
            "state_floors_pass": bool(merged_cell >= FLOORS["cell_episodes"] and raw_ok and dec_ok),
        }
        chk(f"floors.{st}.state_floors_pass", floors[st]["state_floors_pass"],
            census["floors"][st]["state_floors_pass"], tol=0)
        chk(f"floors.{st}.episodes_cell_merged", floors[st]["episodes_cell_merged"],
            census["floors"][st]["episodes_cell_merged"], tol=0)

    # ---------- STEP 4: audits vs PSV1 labels + SMA200 lens ----------
    bull = states == "BULL"
    bear = states == "BEAR"
    uptrend = labels == "UPTREND"


    def cont(a, b):
        return {"a_true_b_true": int((a & b).sum()), "a_true_b_false": int((a & ~b).sum()),
                "a_false_b_true": int((~a & b).sum()), "a_false_b_false": int((~a & ~b).sum()),
                "agreement_share": round(float((a == b).mean()), 6)}


    au = cont(bull, uptrend)
    ad = cont(bear, labels == "DOWNTREND")
    sma200_full = pd.Series(close_full).rolling(200).mean().to_numpy()
    lens_def = np.isfinite(sma200_full[WARMUP:])
    lens_up = np.where(lens_def, close_full[WARMUP:] > sma200_full[WARMUP:], False)
    al = cont(bull[lens_def], lens_up[lens_def])
    chk("audit.BULL_vs_UPTREND.agreement", au["agreement_share"],
        census["audits_vs_old_labels"]["BULL_vs_PSV1_UPTREND"]["agreement_share"])
    for k in ("a_true_b_true", "a_true_b_false", "a_false_b_true", "a_false_b_false"):
        chk(f"audit.BULL_vs_UPTREND.{k}", au[k],
            census["audits_vs_old_labels"]["BULL_vs_PSV1_UPTREND"][k], tol=0)
    chk("audit.BEAR_vs_DOWNTREND.agreement", ad["agreement_share"],
        census["audits_vs_old_labels"]["BEAR_vs_PSV1_DOWNTREND"]["agreement_share"])
    chk("audit.BULL_vs_SMA200.agreement", al["agreement_share"],
        census["audits_vs_old_labels"]["BULL_vs_SMA200H4_lens"]["agreement_share"])
    chk("audit.lens_undefined_bars", int((~lens_def).sum()),
        census["audits_vs_old_labels"]["state_bars_where_lens_undefined"], tol=0)

    # ---------- STEP 5: sensitivity ladder (report-only) ----------
    ladder = {}
    for db in (-0.25, -0.30, -0.35):
        for dr in (-0.05, -0.10, -0.15):
            for dw in (60, 90, 120):
                s = run_machine(close_full, dd_bear=db, dd_rec=dr, dwell=dw)
                ladder[f"DD_BEAR={db}|DD_RECOVER={dr}|DWELL={dw}"] = round(
                    float((s == states_full).mean()), 6)
    lad_bad = [k for k, v in ladder.items()
               if abs(v - census["sensitivity_ladder_report_only"].get(k, -9)) > 1e-6]
    chk("sensitivity_ladder_all_27_match", len(lad_bad), 0, tol=0)

    # ---------- STEP 6: no-lookahead fixture ----------
    mut = close_full.copy()
    mut[-1] = mut[-1] * 1.5
    states_mut = run_machine(mut)
    nolook = bool(np.array_equal(states_full[:-1], states_mut[:-1]))
    chk("fixture.no_lookahead_prefix_identical", nolook,
        census["fixtures"]["no_lookahead_mutation_last_bar_x1.5_prefix_identical"], tol=0)

    # ---------- STEP 7: preregistration-reading robustness (A7 probe) ----------
    # plan section 1.3 parenthetical says the window opens in UNCERTAIN; the
    # implemented machine (prereg: runmax over FULL staged panel, machine from
    # panel bar 0) actually opens the window in whatever state warmup produced.
    open_state_full_machine = states[0]
    # variant (b): machine starts AT the window open (initial UNCERTAIN there),
    # runmax still panel-wide — the only alternative preregistration reading.
    states_b = run_machine(close_full, start=WARMUP, runmax_full=runmax_full)
    rob = {}
    for st in STATES:
        m = states_b == st
        rob[st] = {"bars": int(m.sum()),
                   "occupancy": round(float(m.sum()) / W, 6),
                   "runs_raw": len(runs_of(states_b, st)),
                   "merged": len(merge_runs(runs_of(states_b, st)))}
    rob["transitions_total"] = int(sum(
        1 for t in range(1, W) if states_b[t] != states_b[t - 1]))
    rob_floors_pass = {st: bool(rob[st]["merged"] >= 20) for st in STATES}

    result = {
        "schema": "a7_recompute_trv1@1",
        "cycle_id": "BTC-H4-TWO-REGIME-V1",
        "measured_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "a7_git_head": head,
        "authority": "plans/PLAN_btc_h4_two_regime_v1.md section 1 (commit 113e0c2d); "
                     "independent of the census implementation",
        "identity": {
            "prereg_sha256_worktree": prereg_wt_sha,
            "prereg_sha256_head_blob": prereg_head_sha,
            "prereg_sha256_at_count_time": census["preregistration"]["sha256_at_count_time"],
            "manifest_sha256": manifest_sha,
        },
        "recompute": {
            "window_bars": W,
            "episodes_merged": {st: res[st]["runs_merged"] for st in STATES},
            "runs_raw": {st: res[st]["runs_raw"] for st in STATES},
            "occupancy": {st: res[st]["occupancy_share_of_window"] for st in STATES},
            "transitions_total": ntrans,
            "transition_matrix": tm,
            "floors": floors,
            "detection_lag": {
                "top_anchor": ANCHOR_TOP, "first_BEAR": fmt_utc(open_ms[fb]),
                "lag_days": round((fb - i_top) * 4 / 24.0, 1),
                "bottom_anchor": ANCHOR_BOT, "first_BULL": fmt_utc(open_ms[fu]),
                "lag_days_bull": round((fu - i_bot) * 4 / 24.0, 1)},
            "agreements": {"BULL_vs_PSV1_UPTREND": au["agreement_share"],
                           "BEAR_vs_PSV1_DOWNTREND": ad["agreement_share"],
                           "BULL_vs_SMA200H4_lens": al["agreement_share"]},
            "window_open_state_full_panel_machine": str(open_state_full_machine),
            "prereg_reading_robustness_variant_b_machine_from_window_open": {
                "occupancy": {st: rob[st]["occupancy"] for st in STATES},
                "episodes_merged": {st: rob[st]["merged"] for st in STATES},
                "transitions_total": rob["transitions_total"],
                "cell_floor_20_pass_any_state": any(rob_floors_pass.values())},
            "sensitivity_ladder": ladder,
        },
        "claim_checks_vs_census": checks,
        "n_checks": len(checks),
        "n_failed": int(sum(1 for c in checks if not c["ok"])),
        "failed_metrics": [c["metric"] for c in checks if not c["ok"]],
    }
    out = HERE / "a7_recompute_result.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"WROTE {out}")
    print(f"checks: {result['n_checks']} total, {result['n_failed']} FAILED")
    if result["failed_metrics"]:
        print("FAILED:", result["failed_metrics"])
    print("episodes_merged:", result["recompute"]["episodes_merged"])
    print("occupancy:", result["recompute"]["occupancy"])
    print("transitions_total:", ntrans)
    print("floors_pass:", {st: floors[st]["state_floors_pass"] for st in STATES})
    print("window_open_state:", open_state_full_machine,
          "| variant_b floors pass any state:", any(rob_floors_pass.values()))
    return 0 if result["n_failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
