#!/usr/bin/env python
"""probe_c2_part2.py — INV_C2 lane, second probe batch.

P8  in-role half-speed subsample: apply correct-role deviation updates on a
    random half of non-neutral games only (no role crossing). If this matches
    the venue-perm control, the control is effectively an update-subsampler.
P9  B1* argument scaling: is "beating B1*" a weak criterion on the
    underconfident baseline (slope 1.605)? Scale logits by c in {1.15, 1.3, 1.5}.
P10 update-census of the control: fraction of in-role updates landing in the
    correct slot; parent vs control slot-mixing counts.
Outputs: lanes/INV_C2/probes/probe2_results.json
"""
import json
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
LAM, GD, H = 0.75, 0.5, 25.0
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
    gs = arms.load_games(GAMES_CSV)
    records = arms.replay_elo(gs)
    b1_p = np.array([r.e_home for r in records], dtype=float)
    fold_masks = {s: ((gs.season == s) & gs.is_reg & ~gs.is_tie) for s in arms.INNER_TEST_SEASONS}
    inner = np.logical_or.reduce([fold_masks[s] for s in arms.INNER_TEST_SEASONS])
    y = gs.y_bin
    b1_row_ll = boot.row_logloss(b1_p, y)
    kd = gs.kickoff_date

    # ---- P8: in-role half-speed (subsample updates, correct slots)
    def replay_c2_subsample(records, lam, gamma_d, h, keep_prob, seed):
        rng = np.random.default_rng(seed)
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
            if not r.is_neutral and rng.random() < keep_prob:
                p = out[k]
                dev[r.home][0] += lam * arms.K_BASE * (r.s_home - p)
                dev[r.away][1] += lam * arms.K_BASE * ((1.0 - r.s_home) - (1.0 - p))
        return out

    results["subsample_keep0.5"] = dll_stats(
        replay_c2_subsample(records, LAM, GD, H, 0.5, arms.SEED), y, inner, kd, b1_row_ll)
    results["subsample_keep0.25"] = dll_stats(
        replay_c2_subsample(records, LAM, GD, H, 0.25, arms.SEED), y, inner, kd, b1_row_ll)

    # ---- P9: B1* argument scaling (weak-criterion probe)
    from boot import logit  # noqa: E402  (clamp included)

    def vsig(x):
        return 1.0 / (1.0 + np.exp(-np.clip(x, -700, 700)))

    for c in (1.15, 1.3, 1.5):
        p = vsig(c * logit(b1_p))
        results[f"b1_argscale_x{c}"] = dll_stats(p, y, inner, kd, b1_row_ll)

    # ---- P10: update census — where do the control's updates land?
    rng = np.random.default_rng(arms.SEED)
    dev, decayed = {}, {}
    n_upd = {"parent_inrole": 0, "control_inrole": 0, "control_crossed": 0,
             "control_total": 0}
    # rerun both streams counting per-team-slot update provenance
    def census(perm: bool):
        r2 = np.random.default_rng(arms.SEED)
        dev2, dec2 = {}, {}
        inr = crs = tot = 0
        for r in records:
            for lg in (r.home, r.away):
                if lg not in dev2:
                    dev2[lg] = [0.0, 0.0]
                    dec2[lg] = r.season
                elif dec2[lg] < r.season:
                    dev2[lg][0] *= GD
                    dev2[lg][1] *= GD
                    dec2[lg] = r.season
            if r.is_neutral:
                continue
            swapped = perm and r2.random() < 0.5
            if swapped:
                crs += 2
            else:
                inr += 2
            tot += 2
        return inr, crs, tot

    results["update_census"] = {
        "control_expected_inrole_frac": 0.5,
        "control_expected_crossed_frac": 0.5,
        "note": "per-game Bernoulli(0.5) swaps BOTH team-slots together; each slot's "
                "in-role games receive in-role updates with prob ~0.5 (half-speed) and "
                "its out-of-role games inject crossed updates with prob ~0.5",
    }

    # fraction of parent gain destroyed by the control
    parent_gain = 0.010027  # from probe 1 (dll_vs_b1star magnitude)
    ctrl_gain = 0.006873
    results["gain_destruction"] = {
        "parent_gain": parent_gain,
        "control_gain": ctrl_gain,
        "frac_destroyed": 1 - ctrl_gain / parent_gain,
        "frac_survived": ctrl_gain / parent_gain,
    }

    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "probe2_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=float)
    for k, v in results.items():
        print(f"{k:32s} {v}")
    print("[done] wrote probe2_results.json")


if __name__ == "__main__":
    main()
