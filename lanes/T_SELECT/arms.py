# arms.py — WNBA-PLAYERFEAT-SCORED-V1 · lane T_SELECT · 2026-10-05
#
# Rating-stream engine + arm definitions for TRAIN-INTERNAL selection.
# Language law: calibration/forecasting vocabulary only (no PnL/betting terms).
# Independence law: no NBA parameter is WNBA evidence; the grid is selected on
# WNBA train-internal data only.
#
# ENGINE LAW (frozen here, before any scored look):
#   p_home = 1 / (1 + 10^(-(R_h - R_a + HCA_eff) / 400)),  logistic scale 400.
#   Update (both sides):  R <- R + K * (outcome - p).      Outcome = home win indicator.
#   Season boundary:      R <- 1500 + gamma * (R_end - 1500)  (league mean fixed 1500).
#   New franchise entry:  R = 1500.
#   Tip batching: games sharing an exact tip_utc are ALL predicted from the same
#   rating snapshot, then updates applied (strict-inequality as-of law
#   tip_utc_strict_lt_v1: a simultaneous game is never an input to another).
#   Neutral-site rows: HCA_eff = 0 (ESPN neutral_site flag; corpus carries 6 such
#   rows overall, 2 inside the train window; stats-side warm-up carries no flag —
#   absence disclosed).
#
# ARM DEFINITIONS (dispatch-frozen; designed null == parent bit-for-bit):
#   B0        constant p = TRAIN-window home-win rate (frozen scalar).
#   B1-WNBA   fresh own-Elo, grid K in {8,16,32} x HCA in {0,50,100} x gamma in
#             {0.65,0.75,0.85} (27 fits, all counted); carryover c == 1.
#   WF-A      continuity-modulated carryover: season-start prior for season s is
#             R_start(s) = 1500 + gamma_sel * c_i(s) * (R_end(s-1) - 1500) from
#             game 2 of season s onward (v2 law: game-1 rows use c=1 = parent);
#             expansion/missing/neutral-reason -> c=1. NO free scalar.
#   WF-B      argument += phi_B * (xH - xA), x = standardized b5_minutes_hhi
#             (rotation concentration, k=5 window; k chosen a priori, NOT
#             outcome-selected — k-selection stays deferred per FEATURE_SPEC §3).
#   WF-C      argument += phi_C * (xH - xA), x = standardized c_absence_share
#             (top-5 absence proxy, uniform null-minutes reading).
#   Era floor: rows with season < 2013 (minutes-quality floor) or a non-empty
#             neutral reason get x = 0 + a flag (era_floor / neutral_reason).
#   Designed null: c == 1 and phi == 0 reproduce the parent p_home stream
#   bit-for-bit (same code path; adding 0.0*(finite) and multiplying by 1.0 are
#   exact float identities).
#
# Determinism: no wall-clock inside results; all stochastic steps seeded 20261005.

import math

SEED = 20261005
LEAGUE_MEAN = 1500.0
SCALE = 400.0
LL_EPS = 1e-15

GRID_K = (8, 16, 32)
GRID_HCA = (0.0, 50.0, 100.0)
GRID_GAMMA = (0.65, 0.75, 0.85)
GRID_PHI = (-50.0, -25.0, 0.0, 25.0, 50.0)

SLOPE_BAND = (0.85, 1.15)


def sigmoid_elo(diff):
    """Logistic Elo probability. diff = R_h - R_a + HCA_eff (+ feature argument)."""
    return 1.0 / (1.0 + 10.0 ** (-diff / SCALE))


def elo_update(rating, k, outcome, p):
    """Both-side update law: R <- R + K*(outcome - p)."""
    return rating + k * (outcome - p)


def gamma_reversion(r_end, gamma):
    """Season-boundary carryover (parent law, c=1): 1500 + gamma*(R_end-1500)."""
    return LEAGUE_MEAN + gamma * (r_end - LEAGUE_MEAN)


def continuity_start(r_end, gamma, c):
    """WF-A season-start prior: 1500 + gamma*c*(R_end-1500); c=1 -> parent exactly."""
    return LEAGUE_MEAN + gamma * c * (r_end - LEAGUE_MEAN)


class StreamState:
    """Per-franchise rating state with explicit season-segment bookkeeping.

    One rating per franchise_key (relocation-safe: UTA->SAN->LVA and
    DET->TUL->DAL share one stream via the 20-key lineage table only).

    Segment bookkeeping (exact float arithmetic, no subtraction recovery):
      base[fk] : season-start prior of the current segment (parent law at open).
      acc[fk]  : sum of in-season updates in the current segment.
      r[fk]    == base[fk] + acc[fk] always.
    WF-A revises base between game 1 and game 2 (v2 law) by re-deriving it from
    R_end with the now-knowable c; acc is preserved on top.
    """

    def __init__(self):
        self.base = {}
        self.acc = {}
        self.r = {}
        self.r_end = {}
        self.season = {}

    def _entry(self, fk, gamma):
        """Parent-law season-start prior; fresh franchise entry = league mean."""
        if fk not in self.r_end:
            return LEAGUE_MEAN
        return gamma_reversion(self.r_end[fk], gamma)

    def pre_game_rating(self, fk, season, gamma, c=1.0):
        """Effective rating for a prediction, opening the season segment lazily."""
        if self.season.get(fk) != season:
            if fk in self.r:
                self.r_end[fk] = self.r[fk]
            self.base[fk] = self._entry(fk, gamma)
            self.acc[fk] = 0.0
            self.r[fk] = self.base[fk]
            self.season[fk] = season
        if c != 1.0:
            # WF-A: revise the segment prior with continuity (callers pass c=1.0
            # for game-1 / neutral-reason rows, so the parent law holds there).
            self.base[fk] = continuity_start(self.r_end.get(fk, LEAGUE_MEAN), gamma, c)
            self.r[fk] = self.base[fk] + self.acc[fk]
        return self.r[fk]

    def apply_update(self, fk, k, outcome, p):
        step = k * (outcome - p)
        self.acc[fk] += step
        self.r[fk] = self.base[fk] + self.acc[fk]

    def end_of_stream(self):
        """Freeze r_end for every open segment (for tests/diagnostics)."""
        for fk, r in self.r.items():
            self.r_end[fk] = r
        return self.r_end


def run_stream(games, k=0.0, hca=0.0, gamma=1.0, phi=0.0, x_fn=None, c_fn=None, p0=None):
    """Walk-forward rating stream over chronologically sorted games.

    games: list of dicts with keys
        tip (datetime), game_id (str), season (int),
        fk_home, fk_away (franchise keys), home_win (0/1), neutral (bool),
        row_home, row_away (opaque per-side feature-table rows or None).
    x_fn(row, season) -> (x, flag_or_None): standardized feature for WF-B/WF-C.
    c_fn(row, season) -> c: continuity for WF-A (None -> parent c=1 everywhere).
    p0: if not None, B0 constant mode — predictions are the constant, stream inert.

    Returns (predictions, meta); predictions sorted identically to `games`.
    """
    st = StreamState()
    preds = []
    i = 0
    n = len(games)
    while i < n:
        # tip-batched snapshot: all games at this exact tip predicted from one state
        tip = games[i]["tip"]
        j = i
        batch = []
        while j < n and games[j]["tip"] == tip:
            batch.append(games[j])
            j += 1
        batch_ctx = []
        for g in batch:
            flags = []
            hca_eff = 0.0 if g["neutral"] else hca
            if g["neutral"]:
                flags.append("neutral_hca0")
            c_h = c_fn(g["row_home"], g["season"]) if c_fn is not None else 1.0
            c_a = c_fn(g["row_away"], g["season"]) if c_fn is not None else 1.0
            if c_h != 1.0 or c_a != 1.0:
                flags.append("c_modulated")
            r_h = st.pre_game_rating(g["fk_home"], g["season"], gamma, c_h)
            r_a = st.pre_game_rating(g["fk_away"], g["season"], gamma, c_a)
            arg = (r_h - r_a) + hca_eff
            if x_fn is not None:
                xh, fl_h = x_fn(g["row_home"], g["season"])
                xa, fl_a = x_fn(g["row_away"], g["season"])
                for fl in (fl_h, fl_a):
                    if fl:
                        flags.append(fl)
                arg = arg + phi * (xh - xa)
            p_home = p0 if p0 is not None else sigmoid_elo(arg)
            batch_ctx.append((g, p_home))
            preds.append({
                "game_id": g["game_id"], "tip": g["tip"], "season": g["season"],
                "p_home": p_home, "home_win": g["home_win"],
                "neutral": g["neutral"], "flags": tuple(sorted(set(flags))),
            })
        if p0 is None:
            for g, p_home in batch_ctx:
                hw = float(g["home_win"])
                # update law: R <- R + K*(outcome - expected), expectation of the
                # away side is 1 - p_home (zero-sum pair update)
                st.apply_update(g["fk_home"], k, hw, p_home)
                st.apply_update(g["fk_away"], k, 1.0 - hw, 1.0 - p_home)
        i = j
    return preds, {"n_games": n, "final_ratings": dict(st.end_of_stream())}


# ---------------------------------------------------------------- log loss etc.
def log_loss(p, y):
    """Per-game log loss; p clipped to [1e-15, 1-1e-15] to bound numerics."""
    pc = min(max(p, LL_EPS), 1.0 - LL_EPS)
    return -(y * math.log(pc) + (1 - y) * math.log(1 - pc))


def mean_ll(preds):
    if not preds:
        return float("nan")
    return sum(log_loss(d["p_home"], d["home_win"]) for d in preds) / len(preds)


def ll_delta(arm_preds, parent_preds):
    """Paired per-game dLL = LL(arm) - LL(parent); negative favors the arm."""
    return [log_loss(a["p_home"], a["home_win"]) - log_loss(b["p_home"], b["home_win"])
            for a, b in zip(arm_preds, parent_preds)]


def calibration_slope(preds):
    """Calibration slope: logistic refit y ~ a + b*logit(p). Band [0.85, 1.15].

    Newton-Raphson, deterministic, no external dependencies.
    """
    eps = 1e-12
    xs, ys = [], []
    for d in preds:
        p = min(max(d["p_home"], eps), 1.0 - eps)
        xs.append(math.log(p / (1 - p)))
        ys.append(float(d["home_win"]))
    n = len(xs)
    if n < 10 or all(y == ys[0] for y in ys):
        return float("nan")
    if max(xs) - min(xs) < 1e-12:
        return float("nan")  # constant predictor: slope unidentifiable (honest nan)
    a, b = 0.0, 1.0
    for _ in range(200):
        mu = []
        w = []
        for x in xs:
            eta = a + b * x
            m = 1.0 / (1.0 + math.exp(-eta))
            mu.append(m)
            w.append(max(m * (1 - m), 1e-12))
        gaa = sum(w)
        gab = sum(wi * x for wi, x in zip(w, xs))
        gbb = sum(wi * x * x for wi, x in zip(w, xs))
        ga = sum(yi - mi for yi, mi in zip(ys, mu))
        gb = sum((yi - mi) * x for yi, mi, x in zip(ys, mu, xs))
        det = gaa * gbb - gab * gab
        if abs(det) < 1e-18:
            break
        da = (gbb * ga - gab * gb) / det
        db = (gaa * gb - gab * ga) / det
        a += da
        b += db
        if abs(da) < 1e-10 and abs(db) < 1e-10:
            break
    return b


def date_cluster_bootstrap_ci(delta_ll, clusters, n_resamples=10000, seed=SEED):
    """Paired dLL CI, tip-date-cluster bootstrap (canonical tip UTC date).

    delta_ll[i] paired to clusters[i]. Resamples date clusters with replacement;
    CI = 2.5/97.5 percentiles of the resampled mean dLL. Returns (point, lo, hi).
    """
    import numpy as np
    d = np.asarray(delta_ll, dtype=np.float64)
    c = np.asarray(clusters)
    uniq, inv = np.unique(c, return_inverse=True)
    sums = np.zeros(len(uniq))
    counts = np.zeros(len(uniq))
    np.add.at(sums, inv, d)
    np.add.at(counts, inv, 1.0)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(uniq), size=(n_resamples, len(uniq)))
    means = sums[idx].sum(axis=1) / counts[idx].sum(axis=1)
    point = float(d.mean())
    lo, hi = np.percentile(means, [2.5, 97.5])
    return point, float(lo), float(hi)


def season_permuted_games(games, seed=SEED):
    """Time-shuffled twin corpus: permute the home-win outcome across games
    WITHIN each season (preserves per-team game counts and per-season home-win
    counts / date marginals; destroys the outcome-ratings alignment).
    A single global seeded permutation is shared by all twin runs.
    """
    import random
    rng = random.Random(seed)
    by_season = {}
    for g in games:
        by_season.setdefault(g["season"], []).append(g)
    out = []
    for season in sorted(by_season):
        gs = by_season[season]
        outcomes = [g["home_win"] for g in gs]
        rng.shuffle(outcomes)
        for g, o in zip(gs, outcomes):
            g2 = dict(g)
            g2["home_win"] = o
            out.append(g2)
    out.sort(key=lambda g: (g["tip"], g["game_id"]))
    return out


# ------------------------------------------------------------------ B1 grid
def b1_configs():
    cfgs = []
    for k in GRID_K:
        for hca in GRID_HCA:
            for gamma in GRID_GAMMA:
                cfgs.append({"k": float(k), "hca": float(hca), "gamma": float(gamma)})
    return cfgs


def config_simpler_key(cfg):
    """Deterministic tie-break: simpler = less movement/state (K, HCA, gamma asc)."""
    return (cfg.get("k", 0.0), cfg.get("hca", 0.0), cfg.get("gamma", 0.0))


def phi_simpler_key(phi):
    """Tie-break for phi: simpler = closer to the designed null (|phi| asc, phi asc)."""
    return (abs(phi), phi)


def select_best(candidates):
    """candidates: list of (mean_ll, simpler_key, payload). LOG LOSS: LOWER is
    better. Pick min mean_ll; ties broken by ascending simpler_key. Deterministic."""
    return min(candidates, key=lambda t: (t[0], t[1]))
