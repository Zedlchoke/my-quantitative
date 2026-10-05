# arms.py — NBA-PLAYERFEAT-SCORED-V1 · Lane T_SELECT
# Arm definitions + Elo replay engine + metrics machinery.
#
# Inherited laws (read from, and carried VERBATIM where stated):
#  - PLAN_nba_playerfeat_scored_v1.md (this cycle): B1* = B1-d own-Elo K=32 HCA=100
#    gamma=0.75 carried VERBATIM from NBA-WINPROB-SCORED-V1 (mandatory, never re-tuned).
#  - Terminal protocol semantics: lanes/C_protocol/PROTOCOL_EVAL.md of
#    NBA-WINPROB-SCORED-V1 (worktree .worktrees/nba-winprob-scored-v1/integration):
#      * AS-OF LAW v1: admissible information set for game G = all completed games
#        with date STRICTLY BEFORE G's date; same-day games never inform each other;
#        all updates for date d are applied only AFTER all predictions for date d.
#        (Applied here on the UTC date of tip; NBA slates sit inside one UTC date.)
#      * Prediction: p_home = 1 / (1 + 10^-(R_H + HCA - R_A)/400).
#      * Update after completion, binary result only (no margin multiplier):
#        R <- R + K*(S - E) per team, E = expected score from the prediction formula.
#      * Season boundary: before a lineage's first PREDICTION of a new season label,
#        R <- 1500 + 0.75*(R - 1500). gamma = 0.75 FIXED, not gridded.
#      * New lineage starts at R = 1500 at its first game.
#      * Stream updates on EVERY completed game (regular + playoff). In this corpus
#        season_type=5 (play-in) is its own type outside {regular, playoff} and is
#        excluded from updates (matches the frozen feature-table prior law);
#        exhibition games (is_exhibition=1, event team ids) are excluded.
#      * Neutral-site handling (frozen protocol section 8.4): default HCA applied
#        everywhere (declared limitation); counts disclosed, never conditionally
#        switched (that would be a new trial).
#  - Metrics (protocol section 4): LL primary, clamp [1e-15, 1-1e-15]; Brier;
#    calibration slope = binomial-GLM (logit link) coefficient of logit(p) in
#    outcome ~ 1 + logit(p); paired dLL = LL(arm) - LL(reference), d < 0 favors arm;
#    tip-DATE-clustered bootstrap, 10,000 resamples, seed 20261005, percentile CI.
#  - No betting vocabulary anywhere. Determinism: seed 20261005, fixed orders.

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

# ------------------------------------------------------------------ constants
SEED = 20261005
ELO_K = 32.0            # B1* VERBATIM, never re-tuned
ELO_HCA = 100.0         # B1* VERBATIM, never re-tuned
ELO_GAMMA = 0.75        # B1* VERBATIM, never re-tuned
ELO_INIT = 1500.0
LL_CLAMP = 1e-15
BOOTSTRAP_N = 10_000
SLOPE_BAND = (0.85, 1.15)

PHI_GRID = (-50.0, -25.0, 0.0, 25.0, 50.0)   # immutable, pre-registered
PF_GROUPS = ("PF-A", "PF-B", "PF-C")

# Group scalar composition (single phi per arm; multi-column groups enter as the
# sum of their standardized columns — design decision recorded in the report):
#   PF-A: z(a_top5_share_k5) + z(a_load_top5_k5)   (Group A: rotation concentration
#         + load-vs-own-norm deviation, the frozen non-degenerate carriers)
#   PF-B: z(b_form_top3)                            (Group B: top-3 form scalar)
#   PF-C: z(c_abs_out) + z(c_abs_streak)            (Group C: absence scalars)
GROUP_COLUMNS = {
    "PF-A": ("a_top5_share_k5", "a_load_top5_k5"),
    "PF-B": ("b_form_top3",),
    "PF-C": ("c_abs_out", "c_abs_streak"),
}


class TechAbort(Exception):
    """Loud technical abort (designed-null mismatch, cap violation, data corruption)."""


# ------------------------------------------------------------------ math core
def sigmoid_elo(arg: np.ndarray) -> np.ndarray:
    """1 / (1 + 10^(-arg/400)) — the protocol prediction map (vectorized)."""
    return 1.0 / (1.0 + np.power(10.0, -np.asarray(arg, dtype=np.float64) / 400.0))


def sigmoid_elo_scalar(arg: float) -> float:
    return 1.0 / (1.0 + math.pow(10.0, -arg / 400.0))


def gamma_revert(r: float, gamma: float = ELO_GAMMA, init: float = ELO_INIT) -> float:
    """Season-boundary reversion: R <- init + gamma*(R - init)."""
    return init + gamma * (r - init)


def logloss_rows(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    pc = np.clip(p, LL_CLAMP, 1.0 - LL_CLAMP)
    return -(y * np.log(pc) + (1.0 - y) * np.log(1.0 - pc))


def brier_rows(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    return (np.asarray(p, dtype=np.float64) - y) ** 2


def calibration_slope(p: np.ndarray, y: np.ndarray) -> float | None:
    """Binomial-GLM (logit link) coefficient of logit(p) in outcome ~ 1 + logit(p).

    Deterministic IRLS, no penalty, convergence tol 1e-12 on beta, max 200 iters.
    Returns None when the design is (numerically) singular (e.g. constant p).
    """
    q = np.clip(np.asarray(p, dtype=np.float64), LL_CLAMP, 1.0 - LL_CLAMP)
    eta = np.log(q) - np.log1p(-q)
    if float(np.ptp(eta)) == 0.0:
        return None  # constant p: slope undefined (rank-deficient design)
    X = np.column_stack([np.ones_like(eta), eta])
    yv = np.asarray(y, dtype=np.float64)
    beta = np.zeros(2, dtype=np.float64)
    for _ in range(200):
        lin = X @ beta
        lin = np.clip(lin, -700.0, 700.0)
        mu = 1.0 / (1.0 + np.exp(-lin))
        w = np.maximum(mu * (1.0 - mu), 1e-12)
        z = lin + (yv - mu) / w
        XtW = X.T * w
        A = XtW @ X
        try:
            beta_new = np.linalg.solve(A, XtW @ z)
        except np.linalg.LinAlgError:
            return None
        if not np.all(np.isfinite(beta_new)):
            return None
        delta = np.max(np.abs(beta_new - beta))
        beta = beta_new
        if delta < 1e-12:
            break
    return float(beta[1])


def paired_delta_ci(
    ll_arm: np.ndarray,
    ll_ref: np.ndarray,
    cluster_ids: np.ndarray,
    n_boot: int = BOOTSTRAP_N,
    seed: int = SEED,
) -> dict:
    """Paired per-row dLL = LL(arm) - LL(ref); tip-date-clustered percentile CI.

    Clusters resampled with replacement; cluster order = sorted unique ids.
    Sign convention (protocol section 4): d < 0 favors the arm.
    """
    d = np.asarray(ll_arm, dtype=np.float64) - np.asarray(ll_ref, dtype=np.float64)
    uniq, inv = np.unique(np.asarray(cluster_ids), return_inverse=True)
    ssum = np.zeros(len(uniq), dtype=np.float64)
    scnt = np.zeros(len(uniq), dtype=np.float64)
    np.add.at(ssum, inv, d)
    np.add.at(scnt, inv, 1.0)
    rng = np.random.default_rng(seed)
    point = float(d.mean())
    n_cl = len(uniq)
    means = np.empty(n_boot, dtype=np.float64)
    step = 1000
    for s in range(0, n_boot, step):
        b = min(step, n_boot - s)
        idx = rng.integers(0, n_cl, size=(b, n_cl))
        means[s : s + b] = ssum[idx].sum(axis=1) / scnt[idx].sum(axis=1)
    lo = float(np.percentile(means, 2.5))
    hi = float(np.percentile(means, 97.5))
    return {"point": point, "ci95_lo": lo, "ci95_hi": hi}


# ------------------------------------------------------------- Elo replay
@dataclass
class ReplayResult:
    """Per-game pre-game predictions from an own-Elo replay.

    p_home / elo_arg arrays are aligned 1:1 with the input frame order
    (the caller must pass the fixed order: (tip_date, game_id) sort).
    """

    game_ids: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=np.int64))
    p_home: np.ndarray = field(default_factory=lambda: np.empty(0))
    elo_arg: np.ndarray = field(default_factory=lambda: np.empty(0))
    final_ratings: dict = field(default_factory=dict)
    n_updates: int = 0
    n_season_reversions: int = 0


def replay_elo(
    games: "object",
    K: float = ELO_K,
    HCA: float = ELO_HCA,
    gamma: float = ELO_GAMMA,
    init: float = ELO_INIT,
) -> ReplayResult:
    """Own-Elo replay over played, update-eligible games.

    games: pandas DataFrame with columns
        game_id, season, tip_date (UTC date, sortable), home_id, away_id, y
        in the FIXED order (tip_date, game_id) ascending.
    Laws: same-day exclusion (predictions of date d from state before date d;
    updates applied after all predictions of date d); gamma reversion before a
    lineage's first prediction of a new season; new lineages start at `init`;
    binary-result update R += K*(S - E).
    """
    import pandas as pd  # local import keeps the module importable without pandas use

    if not isinstance(games, pd.DataFrame) or len(games) == 0:
        raise TechAbort("REPLAY_EMPTY: no update-eligible games passed to replay_elo")
    order_ok = games[["tip_date", "game_id"]].equals(
        games[["tip_date", "game_id"]].sort_values(["tip_date", "game_id"]).reset_index(drop=True)
    )
    if not order_ok:
        raise TechAbort("REPLAY_ORDER: games not in fixed (tip_date, game_id) order")

    ratings: dict[int, float] = {}
    rev_season: dict[int, int] = {}
    n_upd = 0
    n_rev = 0
    p_out = np.empty(len(games), dtype=np.float64)
    arg_out = np.empty(len(games), dtype=np.float64)
    gids = games["game_id"].to_numpy()

    pos_of = {int(g): i for i, g in enumerate(gids)}
    games = games.reset_index(drop=True)
    for _date, day in games.groupby("tip_date", sort=True):
        day = day.sort_values("game_id", kind="mergesort")
        preds: dict[int, tuple[float, float]] = {}
        # ---- prediction phase (gamma reversion before a lineage's first
        # prediction of a new season; new lineages start at init)
        for row in day.itertuples(index=False):
            h, a, season = int(row.home_id), int(row.away_id), int(row.season)
            for t in (h, a):
                if t not in ratings:
                    ratings[t] = init
                    rev_season[t] = None
            for t in (h, a):
                if rev_season[t] != season:
                    ratings[t] = gamma_revert(ratings[t], gamma, init)
                    rev_season[t] = season
                    n_rev += 1
            arg = ratings[h] + HCA - ratings[a]
            p = sigmoid_elo_scalar(arg)
            preds[int(row.game_id)] = (p, arg)
        # ---- update phase (after ALL predictions of the date)
        for row in day.itertuples(index=False):
            gid = int(row.game_id)
            p, arg = preds[gid]
            y = float(row.y)
            s_h = y
            s_a = 1.0 - y
            e_h = p
            e_a = 1.0 - p
            ratings[int(row.home_id)] += K * (s_h - e_h)
            ratings[int(row.away_id)] += K * (s_a - e_a)
            n_upd += 1
            i = pos_of[gid]
            p_out[i] = p
            arg_out[i] = arg
    return ReplayResult(
        game_ids=gids,
        p_home=p_out,
        elo_arg=arg_out,
        final_ratings={k: v for k, v in ratings.items()},
        n_updates=n_upd,
        n_season_reversions=n_rev,
    )


# ------------------------------------------------------------- PF arguments
def standardize(raw: np.ndarray, mu: float, sd: float) -> np.ndarray:
    if not (sd > 0.0) or not math.isfinite(sd):
        raise TechAbort(f"STANDARDIZE_BAD_SD: sd={sd!r}")
    return (np.asarray(raw, dtype=np.float64) - mu) / sd


@dataclass
class Moments:
    """Standardization moments (mean / population sd), pinned in the report."""

    mu: dict
    sd: dict


def moments_from_frame(df, columns) -> Moments:
    mu, sd = {}, {}
    for c in columns:
        v = np.asarray(df[c], dtype=np.float64)
        if not np.all(np.isfinite(v)):
            raise TechAbort(f"MOMENTS_NONFINITE: column {c}")
        mu[c] = float(v.mean())
        s = float(v.std(ddof=0))
        if not (s > 0.0):
            raise TechAbort(f"MOMENTS_ZERO_SD: column {c}")
        sd[c] = s
    return Moments(mu=mu, sd=sd)


def group_x(side_frame, group: str, mom: Moments) -> np.ndarray:
    """Standardized group scalar x for one team-side frame (sum over group columns)."""
    x = None
    for col in GROUP_COLUMNS[group]:
        z = standardize(np.asarray(side_frame[col], dtype=np.float64), mom.mu[col], mom.sd[col])
        x = z if x is None else x + z
    return x


def pf_p_home(elo_arg: np.ndarray, x_home: np.ndarray, x_away: np.ndarray, phi: float) -> np.ndarray:
    """p_home under a PF arm: identical expression shape for every phi so that
    phi=0.0 reproduces the B1* probability bit-for-bit (arg + 0.0*xdiff == arg)."""
    return sigmoid_elo(elo_arg + phi * (x_home - x_away))


# ------------------------------------------------------------- grids / ids
def config_id(arm: str, phi: float) -> str:
    return f"{arm}|phi={phi:g}"


def grid_configs() -> list:
    """All 15 pre-registered configs, fixed order (arm asc, phi asc)."""
    out = []
    for arm in PF_GROUPS:
        for phi in PHI_GRID:
            out.append((arm, float(phi)))
    return out


def active_params(phi: float) -> int:
    return 0 if phi == 0.0 else 1


# ------------------------------------------------- synthetic stream builder
def synthetic_stream(seed: int, n_days: int, games_per_day: int, n_teams: int,
                     season_len_days: int = 40, start_season: int = 2016):
    """Deterministic synthetic schedule for fixtures: random matchups, random y,
    multiple season labels so gamma reversion and same-day exclusion engage."""
    import pandas as pd

    rng = np.random.default_rng(seed)
    rows = []
    gid = 9_000_000_000 + seed
    for d in range(n_days):
        season = start_season + d // season_len_days
        date = pd.Timestamp("2000-01-01") + pd.Timedelta(days=d)
        for _ in range(games_per_day):
            h, a = rng.choice(n_teams, size=2, replace=False)
            y = int(rng.random() < 0.6)  # mild home advantage in the generator
            rows.append(
                {
                    "game_id": gid,
                    "season": season,
                    "tip_date": date,
                    "tip_utc": date,
                    "home_id": int(h),
                    "away_id": int(a),
                    "y": y,
                }
            )
            gid += 1
    return pd.DataFrame(rows)
