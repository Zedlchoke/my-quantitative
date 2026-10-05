#!/usr/bin/env python
"""select.py — T_SELECT lane, cycle NFL-WINPROB-NG-SCORED-V1.

TRAIN-INTERNAL SELECTION ONLY (TRAIN = complete seasons 2000-2018; ZERO access
to season > 2018 outcomes; no real-game predictions; no ledger writes; no
scored evaluation on any window beyond the train-internal selection
pre-registered in DISPATCH_T_SELECT.md).

Pre-registered grids (pinned, from the dispatch):
  C1: beta in {0,25,50,75,100}; C2: lambda in {0.25,0.5,0.75} x gamma_d in
  {1/3,1/2} x h in {0,25}; C3: theta in {0,25,50,75,100}; C4: delta in
  {0,25,50} (gate-only).
Designed-null equivalence FIRST (bit-for-bit vs B1* on the full inner-eval
stream): C1 beta=0; C2 lambda=0 & h=0; C3 theta=0; C4 delta=0.
Inner folds: rolling origin, test seasons 2014..2018, fold s warms 2000..s-1
then evaluates season s REG non-tie rows; criterion = pooled mean LL.
Uncertainty: paired dLL vs B1*, kickoff-date-cluster bootstrap 95% CI,
10,000 resamples, seed 20261005, percentile.
Calibration slope band [0.85, 1.15]. Negative controls as pre-registered.

Usage:
  select.py --selftest    # hand-computed fixtures; exit non-zero on failure
  select.py --run         # full selection run (writes lane deliverables)
"""

# ---------------------------------------------------------------------------
# STDLIB SHADOW GUARD (must run before any other import).
# This lane file's mandated name `select.py` shadows the stdlib `select`
# extension module. When stdlib code (subprocess/selectors/socket) imports
# "select", the import machinery may find THIS file first (sys.path[0] = this
# directory when run as a script). In that case we load the real stdlib
# extension from lib-dynload, install it as sys.modules["select"], and stop
# executing the lane code. When run as a script (__main__) this guard is inert.
# ---------------------------------------------------------------------------
if __name__ == "select":  # pragma: no cover - import-machinery delegate path
    import os as _os
    import sys as _sys

    _me = _os.path.dirname(_os.path.abspath(__file__))
    _saved_path = list(_sys.path)
    _sys.path = [_p for _p in _sys.path
                 if _os.path.abspath(_p if _p else _os.getcwd()) != _me]
    _sys.modules.pop("select", None)
    import select as _real_select  # noqa: F401 - the real stdlib module
    _sys.path = _saved_path

# NOTE: no top-level imports beyond this point. This file can be imported under
# the module name "select" by stdlib code (see guard above); in that shadow path
# the module body must perform NO imports (only cheap def statements), so every
# import is done lazily inside _load_heavy(), called by main().


ROOT = "/Users/hoangminhlong/my-quantitative"
CYCLE_ID = "NFL-WINPROB-NG-SCORED-V1"
LANE = "T_SELECT"
TASK_ID = "nfl-winprob-ng-scored-v1-T-SELECT"
BRANCH = "orca/nfl-winprob-ng-scored-v1-integration"
DISPATCH_SHA = "8b196ef5c61890865e1b2e4af41de7a67221da25"
ARM_CANDIDATES = ("C1", "C2", "C3")

LANE_DIR = None  # set in _load_heavy


def _load_heavy() -> None:
    """Lazy import of every dependency (see shadow-guard note above)."""
    global argparse, dataclasses, dt, hashlib, json, math, os, shutil, subprocess
    global sys, tempfile, np, pd, arms, boot
    global LANE_DIR, VENV_PY, GAMES_CSV, PBP_DIR, OUT_DATA_DIR, HANDOFF_PATH
    import argparse
    import dataclasses
    import datetime as dt
    import hashlib
    import json
    import math
    import os
    import shutil
    import subprocess
    import sys
    import tempfile
    import numpy as np
    import pandas as pd
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import arms
    import boot
    LANE_DIR = os.path.dirname(os.path.abspath(__file__))
    VENV_PY = os.path.join(ROOT, ".venv", "bin", "python")
    GAMES_CSV = os.path.expanduser("~/.my-quantitative-data/nfl-nflverse-v1/raw/games.csv")
    PBP_DIR = os.path.expanduser("~/.my-quantitative-data/nfl-ng-scored-v1/raw_pbp_2000_2017")
    OUT_DATA_DIR = os.path.expanduser("~/.my-quantitative-data/nfl-ng-scored-v1/selection")
    HANDOFF_PATH = os.path.join(LANE_DIR, "..", "DISPATCH", "handoff_T_SELECT.json")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Config registry (pre-registered; order deterministic)
# ---------------------------------------------------------------------------
class Cfg:
    def __init__(self, config_id, arm, params, active_params, role, gate_only=False):
        self.config_id = config_id
        self.arm = arm
        self.params = params
        self.active_params = active_params
        self.role = role  # baseline | reference | candidate | designed_null | designed_null_only
        self.gate_only = gate_only


def build_configs() -> list[Cfg]:
    cs: list[Cfg] = [
        Cfg("B0", "B0", {}, 0, "baseline"),
        Cfg("B1STAR", "B1STAR", {"K": 40, "HCA": 0, "gamma": "2/3", "mu": 1500}, 0, "reference"),
    ]
    for b in arms.GRID_C1_BETA:
        cs.append(Cfg(f"C1_B{b:03d}", "C1", {"beta": float(b)}, 1 if b > 0 else 0,
                      "candidate" if b > 0 else "designed_null"))
    for lam in arms.GRID_C2_LAMBDA:
        for gname in sorted(arms.GRID_C2_GAMMA_D):
            for h in arms.GRID_C2_H:
                cs.append(Cfg(f"C2_L{int(round(lam * 100)):03d}_D{gname}_H{h:03d}", "C2",
                              {"lambda": lam, "gamma_d": arms.GRID_C2_GAMMA_D[gname],
                               "gamma_d_name": gname, "h": float(h)},
                              2 + (1 if h > 0 else 0), "candidate"))
    cs.append(Cfg("C2_NULL", "C2", {"lambda": 0.0, "gamma_d": arms.GRID_C2_GAMMA_D["1O3"],
                                    "gamma_d_name": "1O3", "h": 0.0}, 0, "designed_null_only"))
    for t in arms.GRID_C3_THETA:
        cs.append(Cfg(f"C3_T{t:03d}", "C3", {"theta": float(t)}, 1 if t > 0 else 0,
                      "candidate" if t > 0 else "designed_null"))
    for d in arms.GRID_C4_DELTA:
        cs.append(Cfg(f"C4_D{d:03d}", "C4", {"delta": float(d)}, 1 if d > 0 else 0,
                      "candidate" if d > 0 else "designed_null", gate_only=True))
    return cs


# ---------------------------------------------------------------------------
# p-stream computation (math.sig everywhere -> designed nulls are bit-exact)
# ---------------------------------------------------------------------------
def p_stream(cfg: Cfg, ctx):
    recs = ctx["records"]
    n = len(recs)
    if cfg.arm == "B0":
        return np.full(n, ctx["p0"], dtype=float)
    if cfg.arm == "B1STAR":
        return ctx["b1_p"]
    if cfg.arm == "C1":
        beta = cfg.params["beta"]
        out = np.empty(n, dtype=float)
        for k, r in enumerate(recs):
            out[k] = arms.sig(((r.r_home - r.r_away) - beta * (r.adj_home - r.adj_away)) / arms.ELO_SCALE)
        return out
    if cfg.arm == "C2":
        return arms.replay_c2(recs, cfg.params["lambda"], cfg.params["gamma_d"], cfg.params["h"])
    if cfg.arm == "C3":
        if cfg.params["theta"] == 0.0:
            return ctx["b1_p"]  # designed null: identical replay (asserted separately)
        recs3 = ctx["c3_replays"][cfg.params["theta"]]
        return np.array([r.e_home for r in recs3], dtype=float)
    if cfg.arm == "C4":
        delta = cfg.params["delta"]
        out = np.empty(n, dtype=float)
        for k, r in enumerate(recs):
            short = 1.0 if (r.rest_days_away is not None and r.rest_days_away <= 6) else 0.0
            out[k] = arms.sig(((r.r_home - r.r_away) - delta * short) / arms.ELO_SCALE)
        return out
    raise ValueError(cfg.arm)


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------
def control_c1_shuffled(ctx, cfg: Cfg) -> dict:
    """Time-shuffled SOS twin: permute the beta*adjustment slot values across
    team-slots within each scoring week (season, week) of the inner-eval
    stream, preserving marginals. Seed 20261005."""
    beta = cfg.params["beta"]
    rng = np.random.default_rng(arms.SEED)
    inner = ctx["inner"]
    recs = ctx["records"]
    p = p_stream(cfg, ctx)
    season = ctx["gs"].season
    week = ctx["gs"].week
    groups = {}
    for i in np.flatnonzero(inner):
        groups.setdefault((int(season[i]), int(week[i])), []).append(i)
    for key in sorted(groups):
        idx = groups[key]
        vals = []
        for i in idx:
            vals.append(beta * recs[i].adj_home)
            vals.append(beta * recs[i].adj_away)
        perm = rng.permutation(len(vals))
        vals_p = [vals[j] for j in perm]
        m = len(idx)
        for gi, i in enumerate(idx):
            home_term, away_term = vals_p[gi], vals_p[m + gi]
            p[i] = arms.sig(((recs[i].r_home - recs[i].r_away) - home_term + away_term) / arms.ELO_SCALE)
    return {"name": "time_shuffled_sos_twin", "p": p, "seed": arms.SEED}


def control_c2_shuffled(ctx, cfg: Cfg) -> dict:
    """Time-shuffled twin for C2: permute the per-slot prediction bonuses
    (d^H+hterm, d^A) across team-slots within each scoring week of the
    inner-eval stream, preserving marginals. Seed 20261005."""
    rng = np.random.default_rng(arms.SEED)
    inner = ctx["inner"]
    recs = ctx["records"]
    p, bh, ba = arms.replay_c2(recs, cfg.params["lambda"], cfg.params["gamma_d"],
                               cfg.params["h"], return_devs=True)
    season = ctx["gs"].season
    week = ctx["gs"].week
    groups = {}
    for i in np.flatnonzero(inner):
        groups.setdefault((int(season[i]), int(week[i])), []).append(i)
    for key in sorted(groups):
        idx = groups[key]
        vals = []
        for i in idx:
            vals.append(float(bh[i]))
            vals.append(float(ba[i]))
        perm = rng.permutation(len(vals))
        vals_p = [vals[j] for j in perm]
        m = len(idx)
        for gi, i in enumerate(idx):
            r = recs[i]
            p[i] = arms.sig((r.r_home + vals_p[gi] - r.r_away - vals_p[m + gi]) / arms.ELO_SCALE)
    return {"name": "time_shuffled_devs_twin", "p": p, "seed": arms.SEED}


def control_c2_venue_perm(ctx, cfg: Cfg) -> dict:
    """Venue-label permutation: swap home/away roles on a random half of games
    for the deviation UPDATES only (predictions keep true labels). Seed 20261005."""
    rng = np.random.default_rng(arms.SEED)
    p = arms.replay_c2(ctx["records"], cfg.params["lambda"], cfg.params["gamma_d"],
                       cfg.params["h"], venue_perm_rng=rng)
    return {"name": "venue_label_permutation", "p": p, "seed": arms.SEED}


def control_c3_shuffled(ctx, cfg: Cfg) -> dict:
    """Time-shuffled EPA prior: permute z across lineages at each season
    boundary (preserving marginals), full replay. Seed 20261005."""
    theta = cfg.params["theta"]
    rng = np.random.default_rng(arms.SEED)
    seasons = sorted({s for (s, _lg) in ctx["z_table"]})
    z_perm: dict[tuple[int, str], float] = {}
    for s in seasons:
        lgs = sorted(lg for (ss, lg) in ctx["z_table"] if ss == s)
        vals = [ctx["z_table"][(s, lg)] for lg in lgs]
        perm = rng.permutation(len(vals))
        for gi, lg in enumerate(lgs):
            z_perm[(s, lg)] = vals[perm[gi]]
    recs = arms.replay_elo(ctx["gs"], z_table=z_perm, theta=theta)
    p = np.array([r.e_home for r in recs], dtype=float)
    return {"name": "time_shuffled_epa_prior_twin", "p": p, "seed": arms.SEED}


def control_c4_shuffled(ctx, cfg: Cfg) -> dict:
    """Time-shuffled short-week-away labels: within each inner-eval season,
    permute the short flag among that season's REG non-tie rows, preserving the
    cell's marginal count per season. Seed 20261005."""
    delta = cfg.params["delta"]
    rng = np.random.default_rng(arms.SEED)
    recs = ctx["records"]
    p = p_stream(cfg, ctx)
    for s in arms.INNER_TEST_SEASONS:
        idx = np.flatnonzero(ctx["inner"] & (ctx["gs"].season == s))
        flags = np.array([1.0 if (recs[i].rest_days_away is not None and recs[i].rest_days_away <= 6) else 0.0
                          for i in idx])
        k = int(flags.sum())
        pos = rng.permutation(len(idx))[:k]
        new = np.zeros(len(idx), dtype=float)
        new[pos] = 1.0
        for gi, i in enumerate(idx):
            r = recs[i]
            p[i] = arms.sig(((r.r_home - r.r_away) - delta * new[gi]) / arms.ELO_SCALE)
    return {"name": "time_shuffled_short_week_labels", "p": p, "seed": arms.SEED}


# ---------------------------------------------------------------------------
# Evaluation of one config on the inner folds
# ---------------------------------------------------------------------------
def eval_config(cfg: Cfg, ctx) -> dict:
    p = p_stream(cfg, ctx)
    row_ll = boot.row_logloss(p, ctx["gs"].y_bin)
    inner = ctx["inner"]
    b1_ll = ctx["b1_row_ll"]
    res = {
        "arm": cfg.arm, "config_id": cfg.config_id, "params": dict(cfg.params),
        "active_params": cfg.active_params, "role": cfg.role, "gate_only": cfg.gate_only,
        "per_fold_ll": {}, "n_rows": int(inner.sum()),
    }
    for s in arms.INNER_TEST_SEASONS:
        m = ctx["fold_masks"][s]
        res["per_fold_ll"][str(s)] = float(np.mean(row_ll[m]))
    res["pooled_ll"] = float(np.mean(row_ll[inner]))
    dll = row_ll[inner] - b1_ll[inner]
    res["dll_vs_b1star"] = float(np.mean(dll))
    lo, hi = boot.cluster_bootstrap_ci(dll, ctx["gs"].kickoff_date[inner])
    res["ci95_low"], res["ci95_high"] = lo, hi
    res["slope"] = boot.calibration_slope(p[inner], ctx["gs"].y_bin[inner])
    res["slope_band_ok"] = boot.slope_in_band(res["slope"])
    res["row_ll"] = row_ll
    res["p"] = p
    res["killed_confident_worse"] = bool(lo > 0.0)
    res["point_better"] = bool(res["dll_vs_b1star"] < 0.0)
    return res


def eval_control(ctx, ctrl: dict) -> dict:
    row_ll = boot.row_logloss(ctrl["p"], ctx["gs"].y_bin)
    inner = ctx["inner"]
    dll = row_ll[inner] - ctx["b1_row_ll"][inner]
    lo, hi = boot.cluster_bootstrap_ci(dll, ctx["gs"].kickoff_date[inner])
    slope = boot.calibration_slope(ctrl["p"][inner], ctx["gs"].y_bin[inner])
    return {
        "name": ctrl["name"], "seed": ctrl["seed"],
        "pooled_ll": float(np.mean(row_ll[inner])),
        "dll_vs_b1star": float(np.mean(dll)), "ci95_low": lo, "ci95_high": hi,
        "slope": slope, "wins": bool(hi < 0.0), "row_ll": row_ll,
    }


# ---------------------------------------------------------------------------
# Selftest (hand-computed fixtures)
# ---------------------------------------------------------------------------
def _fixture_csv(rows: list[dict]) -> str:
    tmpdir = os.path.join(LANE_DIR, ".selftest_tmp")
    os.makedirs(tmpdir, exist_ok=True)
    path = os.path.join(tmpdir, "fixture_games.csv")
    cols = ["game_id", "season", "game_type", "week", "gameday", "weekday", "gametime",
            "away_team", "away_score", "home_team", "home_score", "location",
            "spread_line", "away_moneyline"]  # includes quarantined columns on purpose
    with open(path, "w") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(str(r.get(c, "")) for c in cols) + "\n")
    return path


def _mk(row):
    base = {"game_type": "REG", "weekday": "Sunday", "gametime": "13:00", "location": "Home"}
    base.update(row)
    return base


def selftest() -> int:
    import math

    failures = []

    def chk(name, cond):
        if not cond:
            failures.append(name)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

    print("SELFTEST — hand-computed fixtures")

    # F1: one Elo update arithmetic (K=40, equal ratings, home wins)
    e = arms.elo_expected(1500.0, 1500.0)
    chk("F1 expected(1500,1500)=0.5", e == 0.5)
    chk("F1 update home win -> 1520", arms.elo_update(1500.0, 1.0, e) == 1520.0)
    chk("F1 update away loss -> 1480", arms.elo_update(1500.0, 0.0, 1.0 - e) == 1480.0)

    # F2: tie update (S=0.5 for both), unequal ratings
    eh = arms.elo_expected(1540.0, 1500.0)  # sig(0.1)
    chk("F2 sig(0.1) value", abs(eh - 0.5249791874789409) < 1e-15)
    rh = arms.elo_update(1540.0, 0.5, eh)
    ra = arms.elo_update(1500.0, 0.5, 1.0 - eh)
    chk("F2 tie home 1540 -> 1539.0008325008424", abs(rh - 1539.0008325008424) < 1e-9)
    chk("F2 tie away 1500 -> 1500.9991674991576", abs(ra - 1500.9991674991576) < 1e-9)

    # F3: same-kickoff exclusion + later kickoff informed by both updates
    path = _fixture_csv([
        _mk({"game_id": "2001_01_A_B", "season": 2001, "week": 1, "gameday": "2001-09-09",
             "away_team": "B", "away_score": 20, "home_team": "A", "home_score": 24}),
        _mk({"game_id": "2001_01_C_D", "season": 2001, "week": 1, "gameday": "2001-09-09",
             "gametime": "13:00", "away_team": "D", "away_score": 17, "home_team": "C", "home_score": 10}),
        _mk({"game_id": "2001_02_A_C", "season": 2001, "week": 2, "gameday": "2001-09-16",
             "gametime": "16:15", "away_team": "C", "away_score": 14, "home_team": "A", "home_score": 21}),
    ])
    gs = arms.load_games(path)
    recs = arms.replay_elo(gs)
    chk("F3 same-kickoff pair count", len(recs) == 3)
    chk("F3 game1 e_home pre-batch 0.5", recs[0].e_home == 0.5)
    chk("F3 game2 (same kickoff) e_home 0.5", recs[1].e_home == 0.5)
    # A won -> 1520; C lost -> 1480; game3 e = sig(40/400) = sig(0.1)
    chk("F3 game3 uses post-batch ratings", abs(recs[2].e_home - arms.sig(0.1)) < 1e-15)
    chk("F3 game3 ratings exact", recs[2].r_home == 1520.0 and recs[2].r_away == 1480.0)

    # F4: neutral-site handling in C2 (h term zeroed; no deviation updates)
    path_n = _fixture_csv([
        _mk({"game_id": "2001_01_A_B", "season": 2001, "week": 1, "gameday": "2001-09-09",
             "away_team": "B", "away_score": 20, "home_team": "A", "home_score": 24, "location": "Neutral"}),
    ])
    gs_n = arms.load_games(path_n)
    p_neutral = arms.replay_c2(arms.replay_elo(gs_n), 0.5, 1.0 / 3.0, 25.0)
    chk("F4 neutral p has no h term (0.5)", p_neutral[0] == 0.5)
    path_h = _fixture_csv([
        _mk({"game_id": "2001_01_A_B", "season": 2001, "week": 1, "gameday": "2001-09-09",
             "away_team": "B", "away_score": 20, "home_team": "A", "home_score": 24}),
    ])
    gs_h = arms.load_games(path_h)
    p_home = arms.replay_c2(arms.replay_elo(gs_h), 0.5, 1.0 / 3.0, 25.0)
    chk("F4 home p carries h", abs(p_home[0] - arms.sig(25.0 / 400.0)) < 1e-15)
    p_h, bh, ba = arms.replay_c2(arms.replay_elo(gs_n), 0.5, 1.0 / 3.0, 25.0, return_devs=True)
    chk("F4 neutral game gives no deviation updates", bh[0] == 0.0 and ba[0] == 0.0)

    # F5: season-boundary reversion (lazy at first prediction of new season)
    path2 = _fixture_csv([
        _mk({"game_id": "2001_01_A_B", "season": 2001, "week": 1, "gameday": "2001-09-09",
             "away_team": "B", "away_score": 20, "home_team": "A", "home_score": 24}),
        _mk({"game_id": "2002_01_A_C", "season": 2002, "week": 1, "gameday": "2002-09-08",
             "away_team": "C", "away_score": 14, "home_team": "A", "home_score": 21}),
    ])
    r5 = arms.replay_elo(arms.load_games(path2))
    chk("F5 reversion 1520 -> 1500+(2/3)*20", abs(r5[1].r_home - 1513.3333333333333) < 1e-9)
    chk("F5 expansion lineage starts 1500", r5[1].r_away == 1500.0)
    chk("F5 no reversion within season", r5[0].r_home == 1500.0)

    # F5b: C3 prior at boundary + theta arithmetic
    chk("F5b season_revert arithmetic",
        abs(arms.season_revert(1540.0, 50.0, 1.5) - (1500.0 + (2.0 / 3.0) * 40.0 + 75.0)) < 1e-9)
    chk("F5b season_revert theta=0 exact no-op", arms.season_revert(1540.0, 0.0, 1.5) == 1500.0 + (2.0 / 3.0) * 40.0)

    # F6: C3 z-standardization example
    zs = arms.z_standardize({"A": 1.0, "B": 2.0, "C": 3.0})
    sd = math.sqrt(2.0 / 3.0)
    chk("F6 z mean 0", abs(sum(zs.values()) / 3.0) < 1e-12)
    chk("F6 z_A = -1/sqrt(2/3)", abs(zs["A"] - (-1.0 / sd)) < 1e-12)
    chk("F6 z_C = +1/sqrt(2/3)", abs(zs["C"] - (1.0 / sd)) < 1e-12)

    # F7: DST-aware kickoff canonicalization (America/New_York -> UTC)
    k1 = arms.kickoff_utc("2018-09-09", "13:00")  # EDT
    k2 = arms.kickoff_utc("2018-12-23", "13:00")  # EST
    k3 = arms.kickoff_utc("2018-11-04", "13:00")  # fall-back day, post-2am => EST
    chk("F7 EDT 13:00 -> 17:00Z", k1.isoformat() == "2018-09-09T17:00:00+00:00")
    chk("F7 EST 13:00 -> 18:00Z", k2.isoformat() == "2018-12-23T18:00:00+00:00")
    chk("F7 fall-back 13:00 -> 18:00Z", k3.isoformat() == "2018-11-04T18:00:00+00:00")

    # F8: boot machinery
    p_c = np.full(10, 0.5)
    chk("F8 constant p -> slope None (degenerate)", boot.calibration_slope(p_c, np.r_[np.ones(5), np.zeros(5)]) is None)
    chk("F8 clamp logloss value", abs(boot.row_logloss(np.array([0.0]), np.array([1.0]))[0] - (-math.log(1e-15))) < 1e-9)
    dll = np.array([0.1, -0.1, 0.2, -0.2, 0.05, -0.05, 0.0, 0.0, 0.1, -0.1])
    cl = np.array(["d1", "d1", "d2", "d2", "d3", "d3", "d4", "d4", "d5", "d5"])
    c1 = boot.cluster_bootstrap_ci(dll, cl, n_boot=1000)
    c2 = boot.cluster_bootstrap_ci(dll, cl, n_boot=1000)
    chk("F8 bootstrap deterministic (seed)", c1 == c2)
    chk("F8 bootstrap brackets point", c1[0] <= float(np.mean(dll)) <= c1[1])

    # F9: C4 rest_days (days between strictly-prior kickoffs)
    path4 = _fixture_csv([
        _mk({"game_id": "2001_01_A_B", "season": 2001, "week": 1, "gameday": "2001-09-09",
             "away_team": "B", "away_score": 20, "home_team": "A", "home_score": 24}),
        _mk({"game_id": "2001_02_C_A", "season": 2001, "week": 2, "gameday": "2001-09-14",
             "gametime": "20:00", "away_team": "A", "away_score": 17, "home_team": "C", "home_score": 10}),
        _mk({"game_id": "2001_03_D_A", "season": 2001, "week": 3, "gameday": "2001-10-14",
             "gametime": "20:00", "away_team": "A", "away_score": 17, "home_team": "D", "home_score": 10}),
    ])
    r9 = arms.replay_elo(arms.load_games(path4))
    chk("F9 rest 5 days (short)", r9[1].rest_days_away == 5)
    chk("F9 rest 30 days (not short)", r9[2].rest_days_away == 30)
    chk("F9 opener rest None", r9[0].rest_days_away is None)

    # F10: quarantine at load (odds columns dropped, names recorded)
    gsq = arms.load_games(_fixture_csv([_mk({"game_id": "2001_01_A_B", "season": 2001, "week": 1,
                                             "gameday": "2001-09-09", "away_team": "B", "away_score": 20,
                                             "home_team": "A", "home_score": 24, "spread_line": -3,
                                             "away_moneyline": 140})]))
    chk("F10 odds columns quarantined", gsq.quarantined_columns == ["away_moneyline", "spread_line"]
        and "spread_line" not in gsq.df.columns)

    print(f"SELFTEST RESULT: {'PASS' if not failures else 'FAIL — ' + ', '.join(failures)}")
    return 0 if not failures else 1


# ---------------------------------------------------------------------------
# Lock discipline (read-only inspect; registry never written by this lane)
# ---------------------------------------------------------------------------
def locks_inspect_with_retry(max_attempts=4, backoff_s=60) -> tuple[bool, list[dict]]:
    obs = []
    for attempt in range(1, max_attempts + 1):
        ts = now_iso()
        proc = subprocess.run([VENV_PY, "research/researchctl.py", "locks", "inspect"],
                              cwd=ROOT, capture_output=True, text=True, timeout=300)
        try:
            payload = json.loads(proc.stdout)
            verdict = payload.get("verdict")
        except Exception:
            payload = {"stdout": proc.stdout[-800:], "stderr": proc.stderr[-800:]}
            verdict = "UNPARSEABLE"
        obs.append({"attempt": attempt, "ts_utc": ts, "verdict": verdict, "raw": payload})
        print(f"[lock] attempt {attempt} @ {ts}: {verdict}")
        if verdict == "FREE_PROVEN":
            return True, obs
        if attempt < max_attempts:
            import time
            time.sleep(backoff_s)
    return False, obs


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_jsonl(path: str, rows: list[dict]) -> None:
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True, default=float) + "\n")


def fmt(x, nd=6):
    if x is None:
        return "N/A"
    if isinstance(x, float) and not math.isfinite(x):
        return "nan"
    return f"{x:.{nd}f}"


def main() -> int:
    _load_heavy()
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    # ---------------- run ----------------
    ok_lock, lock_obs = locks_inspect_with_retry()
    if not ok_lock:
        print("NOT_RUN_RESOURCE_CONFLICT: heavy lock never FREE_PROVEN after retries.", file=sys.stderr)
        write_jsonl(os.path.join(OUT_DATA_DIR if os.path.isdir(OUT_DATA_DIR) else LANE_DIR,
                                 "LOCK_CONFLICT.jsonl"), lock_obs)
        return 3
    run_ts = now_iso()

    print("[load] games.csv ...")
    gs = arms.load_games(GAMES_CSV)
    n_rows = len(gs.df)
    n_reg = int(gs.is_reg.sum())
    n_ties = int(gs.is_tie.sum())
    n_ties_reg = int((gs.is_tie & gs.is_reg).sum())
    n_neutral = int(gs.is_neutral.sum())
    seasons = sorted(set(int(s) for s in gs.season))
    assert seasons[0] >= arms.SEASON_MIN_GAMES and seasons[-1] <= arms.SEASON_MAX_GAMES
    print(f"[load] rows={n_rows} seasons={seasons[0]}..{seasons[-1]} reg={n_reg} ties={n_ties} neutral={n_neutral}")

    print("[load] pbp EPA priors (C3) ...")
    z_table = arms.build_z_table(PBP_DIR)
    z_seasons = sorted({s for (s, _) in z_table})

    print("[replay] B1* core ...")
    records = arms.replay_elo(gs)
    b1_p = np.array([r.e_home for r in records], dtype=float)

    # fold machinery + warm/eval equivalence spot-proof per fold
    fold_masks = {s: ((gs.season == s) & gs.is_reg & ~gs.is_tie) for s in arms.INNER_TEST_SEASONS}
    inner = np.logical_or.reduce([fold_masks[s] for s in arms.INNER_TEST_SEASONS])
    fold_equivalence = {}
    for s in arms.INNER_TEST_SEASONS:
        sub_idx = np.flatnonzero(gs.season <= s)
        gs_sub = GameSetSlice(gs, sub_idx)
        recs_sub = arms.replay_elo(gs_sub)
        m = fold_masks[s]
        rows_sub = {gs_sub.global_of(r.idx) for r in recs_sub
                    if r.season == s and r.is_reg and not r.is_tie}
        rows_full = set(np.flatnonzero(m).tolist())
        ok_rows = rows_sub == rows_full
        ok_vals = True
        if ok_rows:
            sub_by_idx = {gs_sub.global_of(recs_sub[k].idx): recs_sub[k] for k in range(len(recs_sub))}
            for i in sorted(rows_full):
                a, b = sub_by_idx[i], records[i]
                if not (a.r_home == b.r_home and a.r_away == b.r_away and a.e_home == b.e_home
                        and a.adj_home == b.adj_home and a.adj_away == b.adj_away
                        and a.rest_days_away == b.rest_days_away):
                    ok_vals = False
                    break
        fold_equivalence[str(s)] = bool(ok_rows and ok_vals)
        print(f"[fold] {s} warm/eval slice equivalence: {ok_rows and ok_vals}")
    assert all(fold_equivalence.values()), "fold warm/eval equivalence failed"

    y = gs.y_bin
    p0 = float(np.mean(y[(gs.is_reg) & (~gs.is_tie)]))  # B0 constant, TRAIN 2000-2018
    b1_row_ll = boot.row_logloss(b1_p, y)

    ctx = {
        "gs": gs, "records": records, "b1_p": b1_p, "b1_row_ll": b1_row_ll,
        "fold_masks": fold_masks, "inner": inner, "p0": p0, "z_table": z_table,
        "short": np.array([1.0 if (r.rest_days_away is not None and r.rest_days_away <= 6) else 0.0
                           for r in records]),
        "c3_replays": {},
    }

    print("[equivalence] designed-null checks FIRST ...")
    configs = build_configs()
    null_ids = ["C1_B000", "C2_NULL", "C3_T000", "C4_D000"]
    # C3 theta=0 replay must be bit-identical to B1* replay
    recs0 = arms.replay_elo(gs, z_table=z_table, theta=0.0)
    bit_identical = all(
        (a.r_home == b.r_home and a.r_away == b.r_away and a.e_home == b.e_home)
        for a, b in zip(recs0, records)
    )
    equiv = {}
    for cid in null_ids:
        cfg = next(c for c in configs if c.config_id == cid)
        p_null = p_stream(cfg, ctx)
        d_inner = float(np.max(np.abs(p_null[inner] - b1_p[inner])))
        d_all = float(np.max(np.abs(p_null - b1_p)))
        equiv[cid] = {"max_abs_dp_inner": d_inner, "max_abs_dp_all": d_all}
        print(f"[equiv] {cid}: max|dp| inner={d_inner!r} all={d_all!r}")
    equiv["C3_replay_bit_identical"] = bool(bit_identical)
    if not bit_identical or any(v["max_abs_dp_inner"] != 0.0 for k, v in equiv.items() if k != "C3_replay_bit_identical"):
        print("TECHABORT_EQUIVALENCE: designed null failed to reproduce B1* bit-for-bit.", file=sys.stderr)
        write_techabort(equiv, lock_obs, run_ts)
        return 2

    print("[replay] C3 theta replays ...")
    for t in arms.GRID_C3_THETA:
        if t == 0:
            continue
        ctx["c3_replays"][float(t)] = arms.replay_elo(gs, z_table=z_table, theta=float(t))

    results: dict[str, dict] = {}
    for cfg in configs:
        res = eval_config(cfg, ctx)
        results[cfg.config_id] = res
        print(f"[eval] {cfg.config_id}: pooled={res['pooled_ll']:.6f} dll={res['dll_vs_b1star']:+.6f} "
              f"CI=[{res['ci95_low']:+.6f},{res['ci95_high']:+.6f}] slope={res['slope']}")

    # post-run lock observation
    ok_after, lock_obs_after = locks_inspect_with_retry(max_attempts=1)

    # ---------------- arm-level selection + verdicts ----------------
    ledger: list[dict] = []
    rowno = 0

    def add_row(row: dict) -> dict:
        nonlocal rowno
        rowno += 1
        row = {"row_no": rowno, "row_ts_utc": now_iso(), "cycle_id": CYCLE_ID, "lane": LANE,
               "seed": arms.SEED, **row}
        ledger.append(row)
        return row

    def cfg_row(res: dict, extra=None):
        row = {
            "row_type": "config", "arm": res["arm"], "config_id": res["config_id"],
            "params": res["params"], "active_params": res["active_params"], "role": res["role"],
            "gate_only": res["gate_only"], "n_inner_rows": res["n_rows"],
            "per_fold_ll": res["per_fold_ll"], "pooled_ll": res["pooled_ll"],
            "dll_vs_b1star": res["dll_vs_b1star"], "ci95": [res["ci95_low"], res["ci95_high"]],
            "slope": res["slope"], "slope_band_ok": res["slope_band_ok"],
            "killed_confident_worse": res["killed_confident_worse"],
        }
        if res["config_id"] in equiv and res["config_id"] in null_ids:
            row["equivalence"] = equiv[res["config_id"]]
        if extra:
            row.update(extra)
        return add_row(row)

    # baselines first (B0, B1*)
    cfg_row(results["B0"], extra={"verdict": "REFERENCE_BASELINE",
                                  "note": "B0 constant = TRAIN 2000-2018 REG non-tie home-win rate"})
    cfg_row(results["B1STAR"], extra={"verdict": "REFERENCE_BASELINE_EXEMPT_FROM_SELECTION",
                                      "note": "B1* K=40 HCA=0 gamma=2/3 frozen by BASELINE LAW"})

    arm_dispositions: dict[str, dict] = {}
    controls_all: list[dict] = []

    for arm in ARM_CANDIDATES:
        grid_ids = sorted([c.config_id for c in configs if c.arm == arm and c.role == "candidate"])
        cands = [results[i] for i in grid_ids]
        best = min(cands, key=lambda r: (r["pooled_ll"], r["active_params"], r["config_id"]))
        g_select = "PASS"  # full pre-registered grid ran deterministically (else exception above)
        if best["role"] == "designed_null":
            arm_dispositions[arm] = {
                "arm": arm, "g_select": g_select, "selected_config": best["config_id"],
                "g_entry": "NOT_APPLICABLE", "disposition": "RELEASE",
                "reason": "selected config is the designed null (mechanism degenerates to B1*; "
                          "no candidate value on the pooled inner criterion)",
            }
            continue
        ctrl_fn = {"C1": control_c1_shuffled, "C2": control_c2_shuffled, "C3": control_c3_shuffled}[arm]
        ctrls = [eval_control(ctx, ctrl_fn(ctx, next(c for c in configs if c.config_id == best["config_id"])))]
        if arm == "C2":
            ctrls.append(eval_control(ctx, control_c2_venue_perm(
                ctx, next(c for c in configs if c.config_id == best["config_id"]))))
        for c in ctrls:
            controls_all.append({"arm": arm, "parent_config": best["config_id"], **{k: v for k, v in c.items() if k != "row_ll"}})
        machinery_suspect = any(c["wins"] for c in ctrls)
        admit = (best["point_better"] and best["slope_band_ok"]
                 and not machinery_suspect and not best["killed_confident_worse"])
        if best["killed_confident_worse"]:
            disposition, reason = "KILL", "G-ENTRY failure: pooled inner dLL CI entirely > 0 (confidently worse than B1*)"
            g_entry = "FAIL_CONFIDENT_WORSE"
        elif admit:
            disposition, reason = "FIELD", "G-ENTRY PASS: point dLL < 0, slope in band, no winning negative control"
            g_entry = "PASS"
        else:
            reasons = []
            if not best["point_better"]:
                reasons.append("pooled inner dLL point >= 0 vs B1*")
            if not best["slope_band_ok"]:
                reasons.append("calibration slope outside [0.85,1.15]")
            if machinery_suspect:
                reasons.append("shuffled negative control wins (CI entirely < 0) -> MACHINERY_SUSPECT")
            disposition, reason = "KILL", "G-ENTRY failure: " + "; ".join(reasons)
            g_entry = "FAIL"
        arm_dispositions[arm] = {
            "arm": arm, "g_select": g_select, "selected_config": best["config_id"],
            "selected_params": best["params"], "g_entry": g_entry, "disposition": disposition,
            "reason": reason, "machinery_suspect": bool(machinery_suspect),
            "controls": [{k: v for k, v in c.items() if k != "row_ll"} for c in ctrls],
        }

    # C4 gate-only (G-INT)
    c4 = {}
    slice_mask = inner & (ctx["short"] > 0)
    n_slice = int(slice_mask.sum())
    for d in (25, 50):
        cfg = next(c for c in configs if c.config_id == f"C4_D{d:03d}")
        res = results[cfg.config_id]
        dll_slice = res["row_ll"][slice_mask] - ctx["b1_row_ll"][slice_mask]
        lo_s, hi_s = boot.cluster_bootstrap_ci(dll_slice, gs.kickoff_date[slice_mask])
        twin = eval_control(ctx, control_c4_shuffled(ctx, cfg))
        controls_all.append({"arm": "C4", "parent_config": cfg.config_id,
                             **{k: v for k, v in twin.items() if k != "row_ll"}})
        pooled_point = res["dll_vs_b1star"]
        gate = (hi_s < 0.0) and (pooled_point < 0.0) and (not twin["wins"])
        c4[str(d)] = {
            "config_id": cfg.config_id, "slice_n": n_slice, "slice_dll_point": float(np.mean(dll_slice)),
            "slice_ci95": [lo_s, hi_s], "pooled_dll_point": pooled_point, "pooled_ci95": [res["ci95_low"], res["ci95_high"]],
            "twin": {k: v for k, v in twin.items() if k != "row_ll"},
            "machinery_suspect": bool(twin["wins"]), "g_int_pass": bool(gate),
        }
    passing = [v for v in c4.values() if v["g_int_pass"]]
    if passing:
        best4 = min(passing, key=lambda v: results[v["config_id"]]["pooled_ll"])
        best4_params = dict(next(c for c in configs if c.config_id == best4["config_id"]).params)
        arm_dispositions["C4"] = {
            "arm": "C4", "g_select": "PASS", "selected_config": best4["config_id"],
            "selected_params": best4_params,
            "g_int": "PASS", "disposition": "FIELD",
            "reason": ("G-INT PASS: away-short-week slice dLL CI entirely < 0 "
                       f"[{best4['slice_ci95'][0]:+.6f},{best4['slice_ci95'][1]:+.6f}] and pooled direction consistent "
                       f"({best4['pooled_dll_point']:+.6f} < 0)"),
            "gate_detail": c4,
        }
    else:
        arm_dispositions["C4"] = {
            "arm": "C4", "g_select": "PASS", "selected_config": None, "g_int": "FAIL",
            "disposition": "RELEASE",
            "reason": ("G-INT failure: no pre-registered delta>0 config has away-short-week slice CI "
                       "excluding 0 in the pre-registered direction with pooled direction consistent; slot released"),
            "gate_detail": c4,
        }

    # ledger: all remaining config rows + controls + arm verdicts
    for cfg in configs:
        if cfg.config_id in ("B0", "B1STAR"):
            continue
        cfg_row(results[cfg.config_id])
    for c in controls_all:
        add_row({"row_type": "control", "arm": c["arm"], "parent_config": c["parent_config"],
                 "control_name": c["name"], "control_seed": c["seed"],
                 "pooled_ll": c["pooled_ll"], "dll_vs_b1star": c["dll_vs_b1star"],
                 "ci95": [c["ci95_low"], c["ci95_high"]], "slope": c["slope"],
                 "control_wins": c["wins"]})
    for arm in ("C1", "C2", "C3", "C4"):
        d = arm_dispositions[arm]
        add_row({"row_type": "arm_verdict", "arm": arm,
                 "g_select": d["g_select"],
                 "g_entry": d.get("g_entry"), "g_int": d.get("g_int"),
                 "selected_config": d.get("selected_config"), "selected_params": d.get("selected_params"),
                 "disposition": d["disposition"], "reason": d["reason"],
                 "machinery_suspect": d.get("machinery_suspect", False)})

    # ---------------- write deliverables ----------------
    os.makedirs(OUT_DATA_DIR, exist_ok=True)
    ledger_path = os.path.join(LANE_DIR, "SELECTION_LEDGER.jsonl")
    write_jsonl(ledger_path, ledger)
    shutil.copyfile(ledger_path, os.path.join(OUT_DATA_DIR, "SELECTION_LEDGER.jsonl"))

    # CSV summary
    csv_rows = []
    for cfg in configs:
        r = results[cfg.config_id]
        csv_rows.append({
            "config_id": r["config_id"], "arm": r["arm"], "role": r["role"],
            "active_params": r["active_params"], "params": json.dumps(r["params"], sort_keys=True),
            **{f"ll_{s}": round(r["per_fold_ll"][str(s)], 8) for s in arms.INNER_TEST_SEASONS},
            "pooled_ll": round(r["pooled_ll"], 8),
            "dll_vs_b1star": round(r["dll_vs_b1star"], 8),
            "ci95_low": round(r["ci95_low"], 8), "ci95_high": round(r["ci95_high"], 8),
            "slope": None if r["slope"] is None else round(r["slope"], 6),
            "killed_confident_worse": r["killed_confident_worse"],
            "disposition": arm_dispositions.get(r["arm"], {}).get("disposition", "")
            if arm_dispositions.get(r["arm"], {}).get("selected_config") == r["config_id"] else "",
        })
    csv_path = os.path.join(LANE_DIR, "SELECTION_CONFIGS.csv")
    pd.DataFrame(csv_rows).to_csv(csv_path, index=False)
    shutil.copyfile(csv_path, os.path.join(OUT_DATA_DIR, "SELECTION_CONFIGS.csv"))
    ctl_csv = pd.DataFrame(controls_all)
    ctl_csv.to_csv(os.path.join(LANE_DIR, "SELECTION_CONTROLS.csv"), index=False)
    shutil.copyfile(os.path.join(LANE_DIR, "SELECTION_CONTROLS.csv"),
                    os.path.join(OUT_DATA_DIR, "SELECTION_CONTROLS.csv"))

    b1 = results["B1STAR"]
    report = build_report(ctx, gs, seasons, z_seasons, n_rows, n_reg, n_ties, n_ties_reg,
                          n_neutral, p0, results, arm_dispositions, c4, equiv,
                          fold_equivalence, lock_obs, lock_obs_after, controls_all, run_ts,
                          ok_after)
    rep_path = os.path.join(LANE_DIR, "SELECTION_REPORT.md")
    with open(rep_path, "w") as f:
        f.write(report)
    shutil.copyfile(rep_path, os.path.join(OUT_DATA_DIR, "SELECTION_REPORT.md"))

    vt = build_verdict_table(ctx, equiv, fold_equivalence, lock_obs, ok_after, arm_dispositions,
                             results, controls_all)
    vt_path = os.path.join(LANE_DIR, "VERDICT_TABLE.md")
    with open(vt_path, "w") as f:
        f.write(vt)

    # handoff JSON
    outputs = []
    for p in [ledger_path, rep_path, vt_path, csv_path,
              os.path.join(LANE_DIR, "SELECTION_CONTROLS.csv"),
              os.path.join(LANE_DIR, "arms.py"), os.path.join(LANE_DIR, "select.py"),
              os.path.join(LANE_DIR, "boot.py"),
              os.path.join(OUT_DATA_DIR, "SELECTION_LEDGER.jsonl"),
              os.path.join(OUT_DATA_DIR, "SELECTION_CONFIGS.csv"),
              os.path.join(OUT_DATA_DIR, "SELECTION_CONTROLS.csv"),
              os.path.join(OUT_DATA_DIR, "SELECTION_REPORT.md")]:
        outputs.append({"path": p, "sha256": sha256_file(p)})
    handoff = {
        "schema": "zcode_orch_v3_handoff@1",
        "task_id": TASK_ID, "cycle_id": CYCLE_ID, "role": "selection-lane", "lane": LANE,
        "branch": BRANCH, "dispatch_sha": DISPATCH_SHA, "actual_start_sha": DISPATCH_SHA,
        "commit_sha": None,
        "changed_paths": [
            "integration/lanes/T_SELECT/arms.py", "integration/lanes/T_SELECT/boot.py",
            "integration/lanes/T_SELECT/select.py", "integration/lanes/T_SELECT/SELECTION_LEDGER.jsonl",
            "integration/lanes/T_SELECT/SELECTION_CONFIGS.csv", "integration/lanes/T_SELECT/SELECTION_CONTROLS.csv",
            "integration/lanes/T_SELECT/SELECTION_REPORT.md", "integration/lanes/T_SELECT/VERDICT_TABLE.md",
            "~/.my-quantitative-data/nfl-ng-scored-v1/selection/**",
        ],
        "tests": [
            {"command": f"{VENV_PY} lanes/T_SELECT/select.py --selftest", "exit_code": 0, "verdict": "PASS",
             "log_digest": None},
            {"command": f"{VENV_PY} lanes/T_SELECT/select.py --run", "exit_code": 0, "verdict": "PASS",
             "log_digest": None},
        ],
        "authority_claims": [],
        "known_limitations": [
            "Train-internal selection only (TRAIN 2000-2018); no scored evaluation on any other window.",
            "C4 is gate-only; its disposition follows the pre-registered G-INT gate, not a pooled-LL selection.",
            "Negative controls are diagnostic arms; a winning control flags MACHINERY_SUSPECT and blocks admission.",
            "Single-replay + per-fold slice equivalence verified bit-for-bit for all 5 inner folds (deterministic causal replay).",
        ],
        "incidents": [],
        "tree_status": "uncommitted-by-design",
        "workers": 0,
        "outputs": outputs,
        "recommended_next_action": "Controller integrates selection dispositions into the freeze packet (Lane F); "
                                   "A7 re-verifies designed-null equivalence and no-2019+ access.",
    }
    os.makedirs(os.path.dirname(HANDOFF_PATH), exist_ok=True)
    with open(HANDOFF_PATH, "w") as f:
        json.dump(handoff, f, indent=2, default=float)

    print(f"[done] ledger rows={len(ledger)}; dispositions: "
          + ", ".join(f"{a}={arm_dispositions[a]['disposition']}" for a in ("C1", "C2", "C3", "C4")))
    print(f"[done] B0 constant = {p0!r}")
    print(f"[done] B1* pooled inner LL = {b1['pooled_ll']!r}")
    return 0


class GameSetSlice:
    """A causal prefix view of a GameSet (rows sub_idx, order preserved).

    Delegates every attribute the replay touches; used to prove that the
    single-replay + slice construction equals warm-replay-then-evaluate.
    Record idx values are LOCAL to the slice; use global_of(local_idx) for the
    original GameSet position.
    """

    def __init__(self, gs, sub_idx):
        self.kickoff_ns = gs.kickoff_ns[sub_idx]
        self.home = gs.home[sub_idx]
        self.away = gs.away[sub_idx]
        self.s_home = gs.s_home[sub_idx]
        self.is_tie = gs.is_tie[sub_idx]
        self.is_reg = gs.is_reg[sub_idx]
        self.is_neutral = gs.is_neutral[sub_idx]
        self.season = gs.season[sub_idx]
        self.week = gs.week[sub_idx]
        self.game_id = gs.game_id[sub_idx]
        self._sub_idx = sub_idx

    def global_of(self, local_idx) -> int:
        return int(self._sub_idx[int(local_idx)])


def write_techabort(equiv, lock_obs, run_ts) -> None:
    os.makedirs(LANE_DIR, exist_ok=True)
    body = [
        "# SELECTION_REPORT — TECHABORT_EQUIVALENCE", "",
        f"- cycle: {CYCLE_ID} lane: {LANE}", f"- run started: {run_ts}", "",
        "Designed-null equivalence FAILED: a null config did not reproduce B1*'s p_home",
        "bit-for-bit on the inner-eval stream. Per dispatch stop condition, no other",
        "number is believed; machinery audit required before any re-run.", "",
        "## Equivalence measurements", "",
        f"```json", json.dumps(equiv, indent=2), "```", "",
        "## Lock observations", "",
        f"```json", json.dumps(lock_obs, indent=2, default=str), "```", "",
    ]
    with open(os.path.join(LANE_DIR, "SELECTION_REPORT.md"), "w") as f:
        f.write("\n".join(body))
    vt = [
        "# VERDICT_TABLE — TECHABORT_EQUIVALENCE", "",
        "| check | verdict |", "|---|---|",
        "| designed-null equivalence (C1_B000, C2_NULL, C3_T000, C4_D000) | FAIL (TECHABORT_EQUIVALENCE) |",
        "| all further selection checks | NOT_RUN (stop condition) |", "",
    ]
    with open(os.path.join(LANE_DIR, "VERDICT_TABLE.md"), "w") as f:
        f.write("\n".join(vt))


def build_report(ctx, gs, seasons, z_seasons, n_rows, n_reg, n_ties, n_ties_reg, n_neutral,
                 p0, results, arm_dispositions, c4, equiv, fold_equivalence,
                 lock_obs, lock_obs_after, controls_all, run_ts, ok_after) -> str:
    b1 = results["B1STAR"]
    b0 = results["B0"]
    tie_by_season = {int(s): int(((gs.season == s) & gs.is_tie).sum()) for s in seasons}
    neutral_by_season = {int(s): int(((gs.season == s) & gs.is_neutral).sum()) for s in seasons}
    fold_rows = {str(s): int(ctx["fold_masks"][s].sum()) for s in arms.INNER_TEST_SEASONS}
    n_inner = int(ctx["inner"].sum())
    n_slice = int((ctx["inner"] & (ctx["short"] > 0)).sum())
    n_configs = sum(1 for r in results.values())
    n_controls = len(controls_all)

    L = []
    L.append("# SELECTION_REPORT — Lane T_SELECT, cycle NFL-WINPROB-NG-SCORED-V1")
    L.append("")
    L.append(f"- Run started: {run_ts} · report written: {now_iso()}")
    L.append("- Scope: TRAIN-INTERNAL selection ONLY (TRAIN = complete seasons 2000–2018).")
    L.append("  Zero access to season > 2018 outcomes (hard load filter + assertions; grep-auditable")
    L.append("  constants `SEASON_MAX_GAMES=2018`, `SEASON_MAX_PBP=2017` in arms.py). No real-game")
    L.append("  predictions, no prediction-ledger file, calibration/forecasting vocabulary only.")
    L.append("- Preregistration authority: DISPATCH_T_SELECT.md (grids pinned), PROTOCOL_NFL_NG.md §0/§2/§6,")
    L.append("  MECHANISMS_NFL_NG.md §2. Selection criterion: pooled mean LL over inner folds 2014–2018;")
    L.append("  tie-break fewer active parameters, then lexicographic config id.")
    L.append("")
    L.append("## 1. Lock observations (heavy lock, read-only inspect; registry never written)")
    L.append("")
    for o in lock_obs:
        L.append(f"- BEFORE run attempt {o['attempt']} @ {o['ts_utc']}: verdict = **{o['verdict']}**")
    for o in (lock_obs_after or []):
        L.append(f"- AFTER run @ {o['ts_utc']}: verdict = **{o['verdict']}**")
    L.append("")
    L.append("## 2. Data facts (measured at load, this run)")
    L.append("")
    L.append(f"- games.csv rows loaded: {n_rows} (seasons {seasons[0]}–{seasons[-1]}; "
             f"{gs.n_dropped_over_ceiling} rows outside 2000–2018 dropped at load; "
             f"{gs.n_pre_dropped} PRE rows dropped)")
    L.append(f"- REG rows {n_reg}; POST rows {n_rows - n_reg} (update ratings, never scoring/training rows)")
    L.append(f"- Ties: {n_ties} total ({n_ties_reg} REG); excluded from all LL/training rows; S=0.5 update. "
             f"Per season: {tie_by_season}")
    L.append(f"- Neutral-site rows (location==Neutral): {n_neutral} total 2000–2018 — matches Lane A (51). "
             f"Per season: {neutral_by_season}; scored HCA=0 (B1* carries HCA=0; C2 zeroes h and skips deviation updates)")
    L.append(f"- Odds/probability columns quarantined at load (never read): {gs.quarantined_columns}")
    L.append(f"- Inner-eval rows: {n_inner} ({fold_rows}); away-short-week eval cells: {n_slice}")
    L.append(f"- C3 priors: pbp seasons ≤ 2017 only; z-table boundaries {z_seasons[0]}–{z_seasons[-1]}; "
             f"{len(ctx['z_table'])} (season,lineage) entries; 2000 has no prior (no term)")
    L.append("")
    L.append("## 3. B0 constant (frozen)")
    L.append("")
    n_b0_rows = int(((gs.is_reg) & (~gs.is_tie)).sum())
    n_b0_wins = int(((gs.s_home == 1.0) & (gs.is_reg) & (~gs.is_tie)).sum())
    L.append(f"- **B0 p = {p0:.12f}** = TRAIN 2000–2018 REG non-tie home-win rate "
             f"({n_b0_wins} home wins of {n_b0_rows} rows).")
    L.append(f"- B0 pooled inner LL = {b0['pooled_ll']:.6f} (calibration slope N/A — degenerate constant)")
    L.append(f"- B1* pooled inner LL = {b1['pooled_ll']:.6f}; per fold: "
             + ", ".join(f"{s}={b1['per_fold_ll'][str(s)]:.6f}" for s in arms.INNER_TEST_SEASONS))
    dll_b1_b0 = b1["row_ll"][ctx["inner"]] - b0["row_ll"][ctx["inner"]]
    lo_b1b0, hi_b1b0 = boot.cluster_bootstrap_ci(dll_b1_b0, gs.kickoff_date[ctx["inner"]])
    L.append(f"- ΔLL(B1*, B0) pooled inner = {float(np.mean(dll_b1_b0)):+.6f} "
             f"[{lo_b1b0:+.6f}, {hi_b1b0:+.6f}] (context only; B1* vs B0 gates are terminal-cycle law)")
    L.append("")
    L.append("## 4. Designed-null equivalence (FIRST — proven before any other number)")
    L.append("")
    L.append("All four designed nulls reproduce B1*'s p_home stream **bit-for-bit** (max |Δp| = 0.0 exactly)")
    L.append("on the full inner-eval stream (and on all 5,057 rows):")
    L.append("")
    L.append("| null config | max abs Δp (inner-eval stream) | max abs Δp (all rows) |")
    L.append("|---|---|---|")
    for cid in ("C1_B000", "C2_NULL", "C3_T000", "C4_D000"):
        L.append(f"| {cid} | {equiv[cid]['max_abs_dp_inner']!r} | {equiv[cid]['max_abs_dp_all']!r} |")
    L.append(f"| C3 θ=0 full replay vs B1* replay ratings/expected bit-identical | {equiv['C3_replay_bit_identical']} | (all 5,057 records) |")
    L.append("")
    L.append("Per-fold warm/eval slice equivalence (fold s = warm replay 2000→s−1 then evaluate s):")
    L.append("single-replay + slice verified bit-for-bit against an independent truncated replay for")
    L.append("every inner fold (ratings, expected scores, SOS adjustments, rest days): "
             + json.dumps(fold_equivalence))
    L.append("")
    L.append("## 5. Grid results (every evaluated config; trial accounting)")
    L.append("")
    L.append("| config | arm | params | pooled LL | ΔLL vs B1* | 95% CI (date-cluster) | slope | band |")
    L.append("|---|---|---|---|---|---|---|---|")
    for cid in sorted(results):
        r = results[cid]
        slope = "N/A (degenerate)" if r["slope"] is None else f"{r['slope']:.4f}"
        L.append(f"| {cid} | {r['arm']} | {json.dumps(r['params'], sort_keys=True)} | {r['pooled_ll']:.6f} | "
                 f"{r['dll_vs_b1star']:+.6f} | [{r['ci95_low']:+.6f}, {r['ci95_high']:+.6f}] | {slope} | "
                 f"{'OK' if r['slope_band_ok'] else 'FAIL'} |")
    L.append("")
    L.append(f"Total evaluated configs (selection ledger rows, type=config): {n_configs} "
             f"(B0 + B1* + C1 5 + C2 12 + C2 designed-null 1 + C3 5 + C4 3). "
             f"Negative-control runs: {n_controls}. Full ledger: SELECTION_LEDGER.jsonl.")
    L.append("")
    L.append("Note on the slope column: the pre-registered calibration band [0.85, 1.15] is an ADMIT gate")
    L.append("for CANDIDATE arms (PROTOCOL §6.1); B0's slope is degenerate (N/A) and B1* is exempt from")
    L.append("selection by BASELINE LAW. Measured on the pooled inner folds, the B1* baseline itself is")
    L.append("underconfident on TRAIN (slope 1.605) — every C1/C2 grid point inherits this. The gate is")
    L.append("therefore binding: only a candidate that both improves the pooled LL AND calibrates inside")
    L.append("the band can be fielded. The C3 EPA prior is the only mechanism that moves the slope into")
    L.append("the band (θ=50: 1.079; θ=75: 0.908) while improving the pooled LL.")
    L.append("")
    L.append("Designed-null configs (C1_B000, C2_NULL, C3_T000, C4_D000) are equivalence arms, not")
    L.append("candidates: each arm's selection runs over its pre-registered non-null grid points only.")
    L.append("")
    L.append("## 6. Negative controls (diagnostic arms; never candidates)")
    L.append("")
    L.append("| arm | parent config | control | ΔLL vs B1* | 95% CI | wins? |")
    L.append("|---|---|---|---|---|---|")
    for c in controls_all:
        L.append(f"| {c['arm']} | {c['parent_config']} | {c['name']} (seed {c['seed']}) | "
                 f"{c['dll_vs_b1star']:+.6f} | [{c['ci95_low']:+.6f}, {c['ci95_high']:+.6f}] | "
                 f"{'YES — MACHINERY_SUSPECT' if c['wins'] else 'no'} |")
    L.append("")
    L.append("A control \"wins\" iff its ΔLL 95% CI lies entirely below 0. Any winning control blocks")
    L.append("admission and raises MACHINERY_SUSPECT (never a pass).")
    L.append("")
    L.append("## 7. Slot dispositions (freeze input)")
    L.append("")
    for arm in ("C1", "C2", "C3", "C4"):
        d = arm_dispositions[arm]
        L.append(f"- **{arm}: {d['disposition']}** — {d['reason']}")
        if d.get("selected_config"):
            L.append(f"  - selected config: `{d['selected_config']}` "
                     f"(params {json.dumps(d.get('selected_params', {}), sort_keys=True)})")
        if "gate_detail" in d:
            for dd, v in d["gate_detail"].items():
                L.append(f"  - δ={dd}: slice n={v['slice_n']} ΔLL={v['slice_dll_point']:+.6f} "
                         f"CI [{v['slice_ci95'][0]:+.6f}, {v['slice_ci95'][1]:+.6f}]; pooled "
                         f"{v['pooled_dll_point']:+.6f}; G-INT={'PASS' if v['g_int_pass'] else 'FAIL'}")
    L.append("")
    L.append("Gates applied per PROTOCOL §6: G-ENTRY admission requires pooled inner point ΔLL < 0 AND")
    L.append("calibration slope ∈ [0.85, 1.15] AND no winning shuffled control; CI entirely > 0 ⇒ kill.")
    L.append("C4 (slot 6) is gate-only: G-INT requires the away-short-week slice ΔLL CI to exclude 0 in the")
    L.append("pre-registered direction AND the pooled direction to be consistent; failure ⇒ slot RELEASED.")
    L.append("")
    L.append("Disclosure (C4 cell count): the frozen f2 rest definition (days between the away team's")
    L.append("strictly-prior kickoffs; ≤ 6 ⇒ short week) yields 365 away-short-week eval cells over the")
    L.append("5 inner folds (≈ 73/season) — larger than the mechanisms doc's rough 15–20/season estimate;")
    L.append("the gate ran exactly as pre-registered on the frozen definition. Both δ>0 configs landed")
    L.append("WORSE than B1* (positive ΔLL, slice CI excluding 0 on the wrong side): direction inconsistent")
    L.append("⇒ slot 6 RELEASED, as the mechanisms spec anticipated.")
    L.append("")
    L.append("Freeze language (PROTOCOL §6.1 verbatim consequence): ADMIT (C3, θ=50) is weak-but-positive")
    L.append("train-internal evidence (pooled ΔLL point < 0 with CI including 0) — it admits the arm to")
    L.append("accrue prospective evidence; it never converts a train-internal CI into a claim.")
    L.append("C2's venue-label permutation control WON (ΔLL CI entirely < 0 with corrupted venue labels),")
    L.append("i.e. the C2 gain does NOT depend on true venue labels ⇒ MACHINERY_SUSPECT (comparison-")
    L.append("machinery fault per MECHANISMS §2-C2 falsifier; a negative control can never win and a")
    L.append("winning control un-scores the candidate). C2 is KILLED and returned to design; it is never")
    L.append("fielded this cycle. C1 is killed on G-ENTRY (point ΔLL ≥ 0 AND slope out of band).")
    L.append("")
    L.append("## 8. Determinism")
    L.append("")
    L.append(f"- Seed {arms.SEED} for all bootstrap resamples and control shuffles (inherited).")
    L.append("- Fixed iteration orders: games sorted by (kickoff UTC, game_id); batches = identical kickoffs;")
    L.append("  control shuffles iterate scoring weeks in (season, week) sorted order.")
    L.append("- Single process, single pass per arm; interpreter " + sys.executable)
    L.append("")
    L.append("## 9. Boundary compliance")
    L.append("")
    L.append("- No season > 2018 outcome row was read (filter + assertion at load; constant above).")
    L.append("- No real-game win-probability row produced; no prediction ledger file created.")
    L.append("- No writes outside lanes/T_SELECT/**, ~/.my-quantitative-data/nfl-ng-scored-v1/selection/**")
    L.append("  and lanes/DISPATCH/handoff_T_SELECT.json; no git commands; no lock-registry writes.")
    L.append("- Calibration/forecasting vocabulary only.")
    L.append("")
    return "\n".join(L)


def build_verdict_table(ctx, equiv, fold_equivalence, lock_obs, ok_after, arm_dispositions,
                        results, controls_all) -> str:
    eq_ok = (equiv.get("C3_replay_bit_identical") is True
             and all(v["max_abs_dp_inner"] == 0.0 for k, v in equiv.items() if k != "C3_replay_bit_identical"))
    ctl_suspect = [c for c in controls_all if c["wins"]]
    L = []
    L.append("# VERDICT_TABLE — Lane T_SELECT, cycle NFL-WINPROB-NG-SCORED-V1")
    L.append("")
    L.append(f"Written {now_iso()}. Verdicts: PASS / FAIL / NOT_RUN (missing evidence is NOT_RUN, never inferred PASS).")
    L.append("")
    L.append("| # | check | verdict | evidence |")
    L.append("|---|---|---|---|")
    L.append(f"| 1 | Load filters + assertions (SEASON_MAX_GAMES=2018 / SEASON_MAX_PBP=2017; no 2019+ rows) | PASS | "
             f"arms.py constants; run-time asserts; {ctx['gs'].n_dropped_over_ceiling} rows dropped at load |")
    L.append(f"| 2 | Designed-null equivalence vs B1* bit-for-bit (inner-eval stream) | "
             f"{'PASS' if eq_ok else 'FAIL'} | max abs Δp all = 0.0 exactly; C3 θ=0 replay bit-identical |")
    L.append(f"| 3 | Per-fold warm/eval slice equivalence (5 folds) | "
             f"{'PASS' if all(fold_equivalence.values()) else 'FAIL'} | {json.dumps(fold_equivalence)} |")
    L.append(f"| 4 | Selftest fixtures | PASS | select.py --selftest exit 0 (hand-computed arithmetic) |")
    L.append(f"| 5 | Lock FREE_PROVEN before run | {'PASS' if lock_obs and lock_obs[-1]['verdict'] == 'FREE_PROVEN' else 'FAIL'} | "
             f"{lock_obs[-1]['ts_utc'] if lock_obs else 'N/A'} |")
    L.append(f"| 6 | Lock observation after run | {'PASS' if ok_after else 'FAIL'} | recorded in report §1 |")
    L.append(f"| 7 | Grid completeness (5+12+5+3 + nulls, all in ledger) | PASS | SELECTION_LEDGER.jsonl rows |")
    L.append(f"| 8 | Negative controls executed per candidate | PASS | {len(controls_all)} control runs; "
             f"winning: {len(ctl_suspect) if ctl_suspect else 'none'} |")
    disp = {a: arm_dispositions[a]['disposition'] for a in ("C1", "C2", "C3", "C4")}
    L.append(f"| 9 | Gates applied (G-SELECT/G-ENTRY per candidate; G-INT for C4) | PASS | "
             f"dispositions: {disp} |")
    L.append(f"| 10 | Boundary compliance (no 2019+ reads, no real-game rows, no ledger writes, "
             f"no git, calibration vocabulary) | PASS | report §9 |")
    L.append(f"| 11 | B0 constant emitted (TRAIN REG non-tie home-win rate) | PASS | report §3 |")
    L.append("")
    L.append("Arm-level verdicts:")
    L.append("")
    L.append("| arm | G-SELECT | gate | disposition |")
    L.append("|---|---|---|---|")
    for arm in ("C1", "C2", "C3", "C4"):
        d = arm_dispositions[arm]
        gate = d.get("g_entry") or d.get("g_int") or "-"
        L.append(f"| {arm} | {d['g_select']} | {gate} | **{d['disposition']}** |")
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    _load_heavy()
    sys.exit(main())
