"""probe_decomp.py — INV_C2 decomposition probes.

P10: B1* + constant home bonus c curve (pure league-HCA term, no mechanism).
P11: venue-control logit-argument decomposition (constant vs team-varying part).
P12: mean p_inner diagnostics for B1*/parent/control/placebo.
P13: C3 parent reproduction (theta=50) — completes the taint probe set.
Outputs appended into probe_results.json as a second file probe_results2.json.
"""
import importlib.util
import json
import os

import numpy as np

ROOT = "/Users/hoangminhlong/my-quantitative"
WT = os.path.join(ROOT, ".worktrees", "nfl-winprob-ng-scored-v1", "integration")
TSEL = os.path.join(WT, "lanes", "T_SELECT")
OUT = os.path.join(WT, "lanes", "INV_C2", "tmp")

spec = importlib.util.spec_from_file_location("tsel", os.path.join(TSEL, "select.py"))
tsel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tsel)
tsel._load_heavy()
arms, boot = tsel.arms, tsel.boot

gs = arms.load_games(tsel.GAMES_CSV)
records = arms.replay_elo(gs)
b1_p = np.array([r.e_home for r in records], dtype=float)
fold_masks = {s: ((gs.season == s) & gs.is_reg & ~gs.is_tie) for s in arms.INNER_TEST_SEASONS}
inner = np.logical_or.reduce([fold_masks[s] for s in arms.INNER_TEST_SEASONS])
y = gs.y_bin
b1_row_ll = boot.row_logloss(b1_p, y)
z_table = arms.build_z_table(tsel.PBP_DIR)
ctx = {"gs": gs, "records": records, "b1_p": b1_p, "b1_row_ll": b1_row_ll,
       "fold_masks": fold_masks, "inner": inner, "z_table": z_table}

R = {}


def eval_p(p, name):
    row_ll = boot.row_logloss(p, y)
    dll = row_ll[inner] - b1_row_ll[inner]
    lo, hi = boot.cluster_bootstrap_ci(dll, gs.kickoff_date[inner])
    slope = boot.calibration_slope(p[inner], y[inner])
    r = {"name": name, "pooled_inner_ll": float(np.mean(row_ll[inner])),
         "dll_vs_b1star": float(np.mean(dll)), "ci95": [float(lo), float(hi)],
         "slope": None if slope is None else float(slope), "wins": bool(hi < 0.0),
         "mean_p_inner": float(np.mean(p[inner]))}
    print(f"[eval] {name}: dll={r['dll_vs_b1star']:+.6f} ci=[{lo:+.6f},{hi:+.6f}] "
          f"slope={r['slope'] if r['slope'] is None else round(r['slope'], 4)} mean_p={r['mean_p_inner']:.4f}")
    R[name] = r
    return r


# ---------- P10: B1* + constant home bonus (pure league home term) ----------
for c in (0, 15, 25, 35, 50, 68, 75, 100, 125):
    p = arms.sig((np.array([r.r_home - r.r_away for r in records]) + c) / arms.ELO_SCALE)
    eval_p(p, f"P10_b1star_plus_home_bonus_{c}")

# ---------- P11: venue-control logit-argument decomposition ----------
lam, gd, h = 0.75, 0.5, 25.0
rng = np.random.default_rng(arms.SEED)
dev, decayed = {}, {}
pred_bonus = np.empty(len(records), dtype=float)  # d_h0 - d_a1 actually used in scoring
for k, r in enumerate(records):
    for lg in (r.home, r.away):
        if lg not in dev:
            dev[lg] = [0.0, 0.0]
            decayed[lg] = r.season
        elif decayed[lg] < r.season:
            dev[lg][0] *= gd
            dev[lg][1] *= gd
            decayed[lg] = r.season
    hterm = 0.0 if r.is_neutral else h
    pred_bonus[k] = dev[r.home][0] - dev[r.away][1]
    p = arms.sig((r.r_home + dev[r.home][0] - r.r_away - dev[r.away][1] + hterm) / arms.ELO_SCALE)
    if not r.is_neutral:
        if rng.random() < 0.5:
            ps = arms.sig((r.r_home + dev[r.home][1] - r.r_away - dev[r.away][0] + hterm) / arms.ELO_SCALE)
            dev[r.home][1] += lam * arms.K_BASE * (r.s_home - ps)
            dev[r.away][0] += lam * arms.K_BASE * ((1.0 - r.s_home) - (1.0 - ps))
        else:
            dev[r.home][0] += lam * arms.K_BASE * (r.s_home - p)
            dev[r.away][1] += lam * arms.K_BASE * ((1.0 - r.s_home) - (1.0 - p))

pb_inner = pred_bonus[inner]
R["P11_ctrl_bonus_mean_inner"] = float(np.mean(pb_inner))
R["P11_ctrl_bonus_std_inner"] = float(np.std(pb_inner))
R["P11_ctrl_bonus_in_elo_mean"] = float(np.mean(pb_inner))
R["P11_ctrl_hterm_is_constant"] = h
# constant-only variant: keep mean bonus, drop team variation
p_const = arms.sig((np.array([r.r_home - r.r_away for r in records])
                    + float(np.mean(pred_bonus)) + h) / arms.ELO_SCALE)
eval_p(p_const, "P11_ctrl_constant_part_only")

# team-varying-only variant: zero-mean the bonus
p_tv = arms.sig((np.array([r.r_home - r.r_away for r in records])
                 + (pred_bonus - float(np.mean(pred_bonus))) + h) / arms.ELO_SCALE)
eval_p(p_tv, "P11_ctrl_team_varying_part_only")

# ---------- P12: mean p diagnostics ----------
eval_p(b1_p, "P12_b1star")
p_parent = tsel.p_stream(tsel.Cfg("C2_L075_D1O2_H025", "C2",
                                  {"lambda": 0.75, "gamma_d": 0.5, "gamma_d_name": "1O2", "h": 25.0},
                                  3, "candidate"), ctx)
eval_p(p_parent, "P12_parent")

# ---------- P13: C3 parent + designed-null bit-identity re-verified on this probe ----------
cfg_c3 = tsel.Cfg("C3_T050", "C3", {"theta": 50.0}, 1, "candidate")
ctx["c3_replays"] = {50.0: arms.replay_elo(gs, z_table=z_table, theta=50.0)}
p_c3 = tsel.p_stream(cfg_c3, ctx)
eval_p(p_c3, "P13_parent_C3_T050")
recs0 = arms.replay_elo(gs, z_table=z_table, theta=0.0)
R["P13_c3_theta0_bit_identical"] = bool(all(
    a.r_home == b.r_home and a.r_away == b.r_away and a.e_home == b.e_home
    for a, b in zip(recs0, records)))

with open(os.path.join(OUT, "probe_results2.json"), "w") as f:
    json.dump(R, f, indent=2, default=float)
print("[probe] wrote", os.path.join(OUT, "probe_results2.json"))
