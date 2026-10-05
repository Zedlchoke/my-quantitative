#!/usr/bin/env python
"""probe_c2.py — INV_C2 lane, read-only diagnostic probes.

Imports lanes/T_SELECT/{arms,boot} unmodified. All outputs written to
lanes/INV_C2/probes/. No writes anywhere else. TRAIN slice only (games.csv
hard-filtered to seasons 2000..2018 by arms.load_games).

Probes:
  P0  reproduce T_SELECT's venue_label_permutation control + parent config
  P1  h-only synthetic arm (lambda=0, h=25) — the "retained signal" null
  P2  half-speed arm (lambda/2, no perm) — hypothesis (c)
  P3  always-crossed variant (perm prob 1.0) — role-mixing at full rate
  P4  full label-swap control (home/away dataset swapped incl. h orientation)
  P5  deviation magnitudes parent vs control (hypothesis (a) damping)
  P6  calibration slopes (hypothesis (f) direction test) + pure 0.5-jitter arm
  P7  row alignment + determinism asserts
"""
import json
import math
import os
import sys

import numpy as np

ROOT = "/Users/hoangminhlong/my-quantitative"
WT = f"{ROOT}/.worktrees/nfl-winprob-ng-scored-v1/integration"
TSEL = f"{WT}/lanes/T_SELECT"
OUTDIR = f"{WT}/lanes/INV_C2/probes"

sys.path.insert(0, TSEL)
import arms  # noqa: E402
import boot  # noqa: E402

GAMES_CSV = os.path.expanduser("~/.my-quantitative-data/nfl-nflverse-v1/raw/games.csv")

results = {}


def dll_stats(p, y, inner, kickoff_date, b1_row_ll):
    row_ll = boot.row_logloss(p, y)
    dll = row_ll[inner] - b1_row_ll[inner]
    lo, hi = boot.cluster_bootstrap_ci(dll, kickoff_date[inner])
    return {
        "pooled_ll": float(np.mean(row_ll[inner])),
        "dll_vs_b1star": float(np.mean(dll)),
        "ci95": [lo, hi],
        "slope": boot.calibration_slope(p[inner], y[inner]),
    }


def main():
    print("[load] games.csv ...")
    gs = arms.load_games(GAMES_CSV)
    print(f"[load] rows={len(gs.df)} seasons={gs.season.min()}..{gs.season.max()}")
    records = arms.replay_elo(gs)
    b1_p = np.array([r.e_home for r in records], dtype=float)

    fold_masks = {s: ((gs.season == s) & gs.is_reg & ~gs.is_tie) for s in arms.INNER_TEST_SEASONS}
    inner = np.logical_or.reduce([fold_masks[s] for s in arms.INNER_TEST_SEASONS])
    y = gs.y_bin
    b1_row_ll = boot.row_logloss(b1_p, y)
    n_inner = int(inner.sum())
    print(f"[setup] inner rows={n_inner}")

    LAM, GD, H = 0.75, 0.5, 25.0  # parent C2_L075_D1O2_H025

    # ---- P0: reproduce parent + venue-perm control exactly as T_SELECT ran them
    p_parent = arms.replay_c2(records, LAM, GD, H)
    results["parent_C2_L075_D1O2_H025"] = dll_stats(p_parent, y, inner, gs.kickoff_date, b1_row_ll)

    rng = np.random.default_rng(arms.SEED)
    p_ctrl = arms.replay_c2(records, LAM, GD, H, venue_perm_rng=rng)
    results["control_venue_perm"] = dll_stats(p_ctrl, y, inner, gs.kickoff_date, b1_row_ll)

    rng2 = np.random.default_rng(arms.SEED)
    p_ctrl2 = arms.replay_c2(records, LAM, GD, H, venue_perm_rng=rng2)
    results["control_venue_perm_rerun_bit_identical"] = bool(np.array_equal(p_ctrl, p_ctrl2))
    results["row_alignment_ok"] = bool(len(p_ctrl) == len(b1_p) == len(records))

    # B1* stats for context
    results["B1STAR"] = {
        "pooled_ll": float(np.mean(b1_row_ll[inner])),
        "slope": boot.calibration_slope(b1_p[inner], y[inner]),
    }

    # ---- P1: h-only arm (lambda=0): predictions = B1* + h, deviations never learn
    p_honly = arms.replay_c2(records, 0.0, GD, H)
    results["h_only_lam0_H25"] = dll_stats(p_honly, y, inner, gs.kickoff_date, b1_row_ll)

    # h-only WITHOUT the h term at all == B1* (sanity: replay_c2 lam=0 h=0)
    p_null = arms.replay_c2(records, 0.0, GD, 0.0)
    results["null_lam0_H0_maxdp_vs_b1"] = float(np.max(np.abs(p_null - b1_p)))

    # ---- P2: half-speed arm (lambda/2, no permutation)
    p_half = arms.replay_c2(records, LAM / 2.0, GD, H)
    results["half_speed_lam0375"] = dll_stats(p_half, y, inner, gs.kickoff_date, b1_row_ll)

    # ---- P3: always-crossed variant (perm probability 1.0) — local reimplementation
    def replay_c2_always_crossed(records, lam, gamma_d, h):
        dev, decayed = {}, {}
        out = np.empty(len(records), dtype=float)
        for k, r in enumerate(records):
            for lg in (r.home, r.away):
                if lg not in dev:
                    dev[lg] = [0.0, 0.0]
                    decayed[lg] = r.season
                elif decayed[lg] < r.season:
                    dev[lg][0] *= gamma_d
                    dev[lg][1] *= gamma_d
                    decayed[lg] = r.season
            d_h, d_a = dev[r.home][0], dev[r.away][1]
            hterm = 0.0 if r.is_neutral else h
            out[k] = arms.sig((r.r_home + d_h - r.r_away - d_a + hterm) / arms.ELO_SCALE)
            if not r.is_neutral:
                p_swap = arms.sig((r.r_home + dev[r.home][1] - r.r_away - dev[r.away][0] + hterm) / arms.ELO_SCALE)
                dev[r.home][1] += lam * arms.K_BASE * (r.s_home - p_swap)
                dev[r.away][0] += lam * arms.K_BASE * ((1.0 - r.s_home) - (1.0 - p_swap))
        return out

    p_cross = replay_c2_always_crossed(records, LAM, GD, H)
    results["always_crossed_prob1"] = dll_stats(p_cross, y, inner, gs.kickoff_date, b1_row_ll)

    # ---- P4: full venue-label swap (labels swapped for prediction AND updates,
    # including h orientation). Scored with p_true_home = 1 - p_swapped_home.
    class SwappedSet:
        pass

    sw = SwappedSet()
    sw.kickoff_ns = gs.kickoff_ns
    sw.home = gs.away
    sw.away = gs.home
    sw.s_home = 1.0 - gs.s_home
    sw.is_tie = gs.is_tie
    sw.is_reg = gs.is_reg
    sw.is_neutral = gs.is_neutral
    sw.season = gs.season
    sw.week = gs.week
    sw.game_id = gs.game_id
    recs_sw = arms.replay_elo(sw)
    p_sw_home = arms.replay_c2(recs_sw, LAM, GD, H)
    p_fullswap = 1.0 - p_sw_home
    results["full_label_swap"] = dll_stats(p_fullswap, y, inner, gs.kickoff_date, b1_row_ll)

    # ---- P5: deviation magnitudes (inner rows), parent vs control
    _, bh_p, ba_p = arms.replay_c2(records, LAM, GD, H, return_devs=True)
    _, bh_c, ba_c = arms.replay_c2(records, LAM, GD, H, return_devs=True,
                                   venue_perm_rng=np.random.default_rng(arms.SEED))
    results["deviation_magnitudes_inner"] = {
        "parent_mean_abs_bh": float(np.mean(np.abs(bh_p[inner]))),
        "parent_mean_abs_ba": float(np.mean(np.abs(ba_p[inner]))),
        "control_mean_abs_bh": float(np.mean(np.abs(bh_c[inner]))),
        "control_mean_abs_ba": float(np.mean(np.abs(ba_c[inner]))),
        "corr_control_bh_parent_bh": float(np.corrcoef(bh_c[inner], bh_p[inner])[0, 1]),
        "control_mean_bh": float(np.mean(bh_c[inner])),
        "control_mean_ba": float(np.mean(ba_c[inner])),
    }
    # within-week dispersion of the control's bonuses (is there real per-team signal?)
    results["deviation_ratio_control_over_parent"] = (
        results["deviation_magnitudes_inner"]["control_mean_abs_bh"]
        / max(results["deviation_magnitudes_inner"]["parent_mean_abs_bh"], 1e-12))

    # ---- P6: hypothesis (f) direction test: pure 0.5-ward jitter of B1*
    p_jit = 0.5 * (b1_p + 0.5)
    results["b1_jitter_toward_05"] = dll_stats(p_jit, y, inner, gs.kickoff_date, b1_row_ll)

    # ---- print table
    def fmt(r):
        if r is None:
            return "N/A"
        s = r.get("slope")
        dll = r.get("dll_vs_b1star")
        ci = r.get("ci95")
        dll_s = "dll=N/A" if dll is None else f"dll={dll:+.6f}"
        ci_s = "CI=N/A" if ci is None else f"CI=[{ci[0]:+.6f},{ci[1]:+.6f}]"
        return (f"pooled={r['pooled_ll']:.6f} {dll_s} {ci_s} "
                f"slope={s if s is None else round(s, 4)}")

    print("\n=== RESULTS (inner folds 2014-2018, n=%d) ===" % n_inner)
    for k, v in results.items():
        if isinstance(v, dict) and "pooled_ll" in v:
            print(f"{k:38s} {fmt(v)}")
        else:
            print(f"{k:38s} {v}")

    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "probe_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=float)
    print(f"\n[done] wrote {OUTDIR}/probe_results.json")


if __name__ == "__main__":
    main()
