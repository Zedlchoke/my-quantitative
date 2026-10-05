"""probe_main.py — INV_C2 read-only reproduction + hypothesis probes.

Imports the T_SELECT lane's own select.py (under module name "tsel" so the
stdlib-shadow guard is inert) and re-assembles ctx exactly as select.main()
does. All outputs written to lanes/INV_C2/tmp/probe_results.json. No writes
outside lanes/INV_C2/**.
"""
import importlib.util
import json
import math
import os
import sys

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

print("[probe] loading games + B1* replay ...")
gs = arms.load_games(tsel.GAMES_CSV)
records = arms.replay_elo(gs)
b1_p = np.array([r.e_home for r in records], dtype=float)
fold_masks = {s: ((gs.season == s) & gs.is_reg & ~gs.is_tie) for s in arms.INNER_TEST_SEASONS}
inner = np.logical_or.reduce([fold_masks[s] for s in arms.INNER_TEST_SEASONS])
y = gs.y_bin
b1_row_ll = boot.row_logloss(b1_p, y)
b1_slope = boot.calibration_slope(b1_p[inner], y[inner])
print(f"[probe] rows={len(records)} inner={int(inner.sum())} B1* slope={b1_slope}")

print("[probe] building z_table (pbp <=2017) ...")
z_table = arms.build_z_table(tsel.PBP_DIR)
ctx = {"gs": gs, "records": records, "b1_p": b1_p, "b1_row_ll": b1_row_ll,
       "fold_masks": fold_masks, "inner": inner, "z_table": z_table}

RESULTS = {"b1_pooled_inner_ll": float(np.mean(b1_row_ll[inner])), "b1_slope": b1_slope,
           "n_inner": int(inner.sum())}


def eval_p(p, name):
    row_ll = boot.row_logloss(p, y)
    dll = row_ll[inner] - b1_row_ll[inner]
    lo, hi = boot.cluster_bootstrap_ci(dll, gs.kickoff_date[inner])
    slope = boot.calibration_slope(p[inner], y[inner])
    r = {"name": name, "pooled_inner_ll": float(np.mean(row_ll[inner])),
         "dll_vs_b1star": float(np.mean(dll)), "ci95": [float(lo), float(hi)],
         "slope": None if slope is None else float(slope), "wins": bool(hi < 0.0)}
    print(f"[eval] {name}: dll={r['dll_vs_b1star']:+.6f} ci=[{lo:+.6f},{hi:+.6f}] "
          f"slope={r['slope'] if r['slope'] is None else round(r['slope'], 4)} wins={r['wins']}")
    RESULTS[name] = r
    return r


BEST = {"lambda": 0.75, "gamma_d": 0.5, "gamma_d_name": "1O2", "h": 25.0}
cfg_best = tsel.Cfg("C2_L075_D1O2_H025", "C2", dict(BEST), 3, "candidate")

# ---------- P1a: parent reproduction ----------
p_parent = tsel.p_stream(cfg_best, ctx)
eval_p(p_parent, "P1a_parent_C2_L075_D1O2_H025")

# ---------- P1b: venue-perm control reproduction (lane code verbatim) ----------
ctrl = tsel.control_c2_venue_perm(ctx, cfg_best)
eval_p(ctrl["p"], "P1b_venue_perm_control_lane_code")
RESULTS["P1b_control_name_seed"] = (ctrl["name"], ctrl["seed"])

# ---------- P1c: shuffled-devs twin reproduction (lane code verbatim) ----------
ctrl2 = tsel.control_c2_shuffled(ctx, cfg_best)
eval_p(ctrl2["p"], "P1c_shuffled_devs_twin_lane_code")

# ---------- P2: strength-only variant (single shared deviation, no roles) ----------
def replay_strength(recs, lam, gamma_d, h):
    dev, decayed = {}, {}
    out = np.empty(len(recs), dtype=float)
    for k, r in enumerate(recs):
        for lg in (r.home, r.away):
            if lg not in dev:
                dev[lg] = 0.0
                decayed[lg] = r.season
            elif decayed[lg] < r.season:
                dev[lg] *= gamma_d
                decayed[lg] = r.season
        hterm = 0.0 if r.is_neutral else h
        p = arms.sig((r.r_home + dev[r.home] - r.r_away - dev[r.away] + hterm) / arms.ELO_SCALE)
        out[k] = p
        if not r.is_neutral:
            dev[r.home] += lam * arms.K_BASE * (r.s_home - p)
            dev[r.away] += lam * arms.K_BASE * ((1.0 - r.s_home) - (1.0 - p))
    return out


eval_p(replay_strength(records, 0.75, 0.5, 25.0), "P2_strength_only_lam075")
eval_p(replay_strength(records, 0.25, 0.5, 25.0), "P2_strength_only_lam025")

# ---------- P3: FULL venue-perm (updates AND scoring both use swapped roles) ----------
def replay_full_perm(recs, lam, gamma_d, h, seed=arms.SEED):
    rng = np.random.default_rng(seed)
    dev, decayed = {}, {}
    out = np.empty(len(recs), dtype=float)
    for k, r in enumerate(recs):
        for lg in (r.home, r.away):
            if lg not in dev:
                dev[lg] = [0.0, 0.0]
                decayed[lg] = r.season
            elif decayed[lg] < r.season:
                dev[lg][0] *= gamma_d
                dev[lg][1] *= gamma_d
                decayed[lg] = r.season
        hterm = 0.0 if r.is_neutral else h
        if not r.is_neutral and rng.random() < 0.5:
            # swapped roles for scoring too
            p = arms.sig((r.r_home + dev[r.home][1] - r.r_away - dev[r.away][0] + hterm) / arms.ELO_SCALE)
            out[k] = p
            dev[r.home][1] += lam * arms.K_BASE * (r.s_home - p)
            dev[r.away][0] += lam * arms.K_BASE * ((1.0 - r.s_home) - (1.0 - p))
        else:
            p = arms.sig((r.r_home + dev[r.home][0] - r.r_away - dev[r.away][1] + hterm) / arms.ELO_SCALE)
            out[k] = p
            dev[r.home][0] += lam * arms.K_BASE * (r.s_home - p)
            dev[r.away][1] += lam * arms.K_BASE * ((1.0 - r.s_home) - (1.0 - p))
    return out


eval_p(replay_full_perm(records, 0.75, 0.5, 25.0), "P3_full_perm_score_and_update")

# ---------- P4: outcome-permutation placebo (in-role updates, outcomes shuffled) ----------
def replay_outcome_perm(recs, lam, gamma_d, h, seed=arms.SEED):
    rng = np.random.default_rng(seed)
    nn = np.array([not r.is_neutral for r in recs])
    s_nn = np.array([r.s_home for r in recs])[nn]
    s_perm = s_nn.copy()
    rng.shuffle(s_perm)
    s_use = np.array([r.s_home for r in recs], dtype=float)
    s_use[nn] = s_perm
    dev, decayed = {}, {}
    out = np.empty(len(recs), dtype=float)
    for k, r in enumerate(recs):
        for lg in (r.home, r.away):
            if lg not in dev:
                dev[lg] = [0.0, 0.0]
                decayed[lg] = r.season
            elif decayed[lg] < r.season:
                dev[lg][0] *= gamma_d
                dev[lg][1] *= gamma_d
                decayed[lg] = r.season
        hterm = 0.0 if r.is_neutral else h
        p = arms.sig((r.r_home + dev[r.home][0] - r.r_away - dev[r.away][1] + hterm) / arms.ELO_SCALE)
        out[k] = p
        if not r.is_neutral:
            dev[r.home][0] += lam * arms.K_BASE * (s_use[k] - p)
            dev[r.away][1] += lam * arms.K_BASE * ((1.0 - s_use[k]) - (1.0 - p))
    return out


eval_p(replay_outcome_perm(records, 0.75, 0.5, 25.0), "P4_outcome_perm_placebo_lam075")

# ---------- P5: lambda_eff mapping (in-role parent path, gamma_d=0.5, h=25) ----------
for lam in (0.125, 0.1875, 0.25, 0.375, 0.5):
    eval_p(arms.replay_c2(records, lam, 0.5, 25.0), f"P5_inrole_lam{lam}")

# ---------- P6: C3 time-shuffled EPA-prior twin reproduction (lane code verbatim) ----------
cfg_c3 = tsel.Cfg("C3_T050", "C3", {"theta": 50.0}, 1, "candidate")
ctrl3 = tsel.control_c3_shuffled(ctx, cfg_c3)
eval_p(ctrl3["p"], "P6_c3_shuffled_epa_twin_theta50")

# ---------- P7: taint audit for C3 twin ----------
# 7a: permuted z vs true z correlation per season (should be ~0)
seasons = sorted({s for (s, _lg) in z_table})
rng = np.random.default_rng(arms.SEED)
cors = []
for s in seasons:
    lgs = sorted(lg for (ss, lg) in z_table if ss == s)
    vals = np.array([z_table[(s, lg)] for lg in lgs])
    perm = rng.permutation(len(vals))
    zp = vals[perm]
    if np.std(vals) > 0:
        cors.append(float(np.corrcoef(vals, zp)[0, 1]))
# NOTE: control_c3_shuffled iterates sorted(seasons) drawing one permutation per season
# from its own rng — same consumption order as this audit loop.
RESULTS["P7a_zperm_truez_corr_absmax"] = float(np.max(np.abs(cors)))
RESULTS["P7a_zperm_truez_corr_mean"] = float(np.mean(cors))

# 7b: does the C3 twin actually differ from B1*?
dp = np.max(np.abs(ctrl3["p"][inner] - b1_p[inner]))
RESULTS["P7b_c3twin_max_abs_dp_inner"] = float(dp)

# 7c: C3 parent reproduction (theta=50)
p_c3 = tsel.p_stream(cfg_c3, ctx)
eval_p(p_c3, "P7c_parent_C3_T050")

# ---------- P8: deviation-stream diagnostics (control vs parent) ----------
def collect_devs(recs, lam, gamma_d, h, mode, seed=arms.SEED):
    rng = np.random.default_rng(seed)
    dev, decayed = {}, {}
    for k, r in enumerate(recs):
        for lg in (r.home, r.away):
            if lg not in dev:
                dev[lg] = [0.0, 0.0]
                decayed[lg] = r.season
            elif decayed[lg] < r.season:
                dev[lg][0] *= gamma_d
                dev[lg][1] *= gamma_d
                decayed[lg] = r.season
        hterm = 0.0 if r.is_neutral else h
        p = arms.sig((r.r_home + dev[r.home][0] - r.r_away - dev[r.away][1] + hterm) / arms.ELO_SCALE)
        if not r.is_neutral:
            if mode == "perm" and rng.random() < 0.5:
                ps = arms.sig((r.r_home + dev[r.home][1] - r.r_away - dev[r.away][0] + hterm) / arms.ELO_SCALE)
                dev[r.home][1] += lam * arms.K_BASE * (r.s_home - ps)
                dev[r.away][0] += lam * arms.K_BASE * ((1.0 - r.s_home) - (1.0 - ps))
            else:
                dev[r.home][0] += lam * arms.K_BASE * (r.s_home - p)
                dev[r.away][1] += lam * arms.K_BASE * ((1.0 - r.s_home) - (1.0 - p))
    return dev


dev_parent = collect_devs(records, 0.75, 0.5, 25.0, "inrole")
dev_ctrl = collect_devs(records, 0.75, 0.5, 25.0, "perm")
for tag, dev in (("parent", dev_parent), ("control", dev_ctrl)):
    h0 = np.array([v[0] for v in dev.values()])
    h1 = np.array([v[1] for v in dev.values()])
    RESULTS[f"P8_dev_{tag}_mean_abs_slotH"] = float(np.mean(np.abs(h0)))
    RESULTS[f"P8_dev_{tag}_mean_abs_slotA"] = float(np.mean(np.abs(h1)))
    RESULTS[f"P8_dev_{tag}_corr_slotH_slotA"] = float(np.corrcoef(h0, h1)[0, 1])
    RESULTS[f"P8_dev_{tag}_mean_abs_crossrole_diff"] = float(np.mean(np.abs(h0 - h1)))

# ---------- P9: pairing / row-set sanity ----------
row_ll_ctrl = boot.row_logloss(ctrl["p"], y)
RESULTS["P9_ctrl_pooled_inner_ll_direct"] = float(np.mean(row_ll_ctrl[inner]))
RESULTS["P9_ctrl_dll_direct"] = float(np.mean(row_ll_ctrl[inner] - b1_row_ll[inner]))
RESULTS["P9_inner_rowcount"] = int(inner.sum())
RESULTS["P9_ybin_identical_rows"] = True  # same arrays used for both sides by construction

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "probe_results.json"), "w") as f:
    json.dump(RESULTS, f, indent=2, default=float)
print("[probe] wrote", os.path.join(OUT, "probe_results.json"))
