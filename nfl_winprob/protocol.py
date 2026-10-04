"""FROZEN protocol constants + metric implementations (lane C PROTOCOL_EVAL_NFL.md)."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

# --- frozen split (lane B measured: release spans 1999..2026; gametime 100%
# missing in 1999 -> kickoff-grain law active from season 2000; last complete
# season 2025; test = final 7 complete seasons per placeholder rule) --------
TEST_SEASONS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
TRAIN_SEASONS_RANGE = (2000, 2018)  # inclusive
KICKOFF_GRAIN_SAFE_FROM_SEASON = 2000

# --- frozen Elo constants (B1 arms) ----------------------------------------
ELO_INIT = 1500.0
ELO_GAMMA = 2.0 / 3.0  # season-boundary reversion toward 1500 (fixed, not gridded)
NEUTRAL_HCA_ZERO = True  # neutral-site games: HCA = 0 in prediction AND update


@dataclass(frozen=True)
class Arm:
    arm_id: str
    kind: str
    K: float | None = None
    HCA: float | None = None
    features: tuple[str, ...] = ()


ARMS: tuple[Arm, ...] = (
    Arm("B0", "B0"),
    Arm("B1-a", "B1", K=20, HCA=0),
    Arm("B1-b", "B1", K=20, HCA=65),
    Arm("B1-c", "B1", K=40, HCA=0),
    Arm("B1-d", "B1", K=40, HCA=65),
    Arm("B2-a", "B2", features=("elo_diff", "rest_diff", "short_week_home", "short_week_away", "form_home", "form_away")),
    Arm("B2-b", "B2", features=("elo_diff", "form_home", "form_away")),
    Arm("B2-c", "B2", features=("elo_diff", "rest_diff", "short_week_home", "short_week_away")),
    Arm("B2-d", "B2", features=("elo_diff",)),
)
assert len(ARMS) == 9

LOGIT_L2 = 1.0
LOGIT_TOL = 1e-8
LOGIT_MAX_ITER = 100
RNG_SEED = 20261005

REST_CAP = 20          # days; byes stay uncapped (13-14 day rest < 20)
SHORT_WEEK_DAYS = 6    # rest <= 6 days => short_week flag
FORM_WINDOW = 4        # last <=4 completed regular-season games, current season
P_CLAMP = 1e-15

SUCCESSOR_GO_PHRASE = "GO NFL WINPROB SCORED V1 EVALUATION"


def clamp_p(p: float) -> float:
    return min(max(p, P_CLAMP), 1.0 - P_CLAMP)


def log_loss(ps, ys) -> float:
    tot = 0.0
    n = 0
    for p, y in zip(ps, ys):
        p = clamp_p(p)
        tot += -(y * math.log(p) + (1 - y) * math.log(1 - p))
        n += 1
    if n == 0:
        raise ValueError("empty evaluation set")
    return tot / n


def brier(ps, ys) -> float:
    tot = 0.0
    n = 0
    for p, y in zip(ps, ys):
        tot += (p - y) ** 2
        n += 1
    if n == 0:
        raise ValueError("empty evaluation set")
    return tot / n


def reliability_bins(ps, ys, n_bins: int = 10):
    bins = [[0, 0.0, 0] for _ in range(n_bins)]
    for p, y in zip(ps, ys):
        b = min(n_bins - 1, int(p * n_bins))
        bins[b][0] += 1
        bins[b][1] += p
        bins[b][2] += y
    return [(b, n, (s / n) if n else None, (y / n) if n else None)
            for b, (n, s, y) in enumerate(bins)]


def _sigmoid(z: float) -> float:
    if z >= 0:
        e = math.exp(-z)
        return 1.0 / (1.0 + e)
    e = math.exp(z) if z > -700 else 0.0
    return e / (1.0 + e)


def _penalized_nll(w, X, y, pen) -> float:
    tot = 0.0
    for xi, yi in zip(X, y):
        mu = _sigmoid(sum(w[j] * xi[j] for j in range(len(w))))
        mu = min(max(mu, 1e-12), 1 - 1e-12)
        tot += -(yi * math.log(mu) + (1 - yi) * math.log(1 - mu))
    tot += 0.5 * sum(pen[j] * w[j] * w[j] for j in range(len(w)))
    return tot


def fit_logistic(X, y, l2: float = LOGIT_L2, tol: float = LOGIT_TOL, max_iter: int = LOGIT_MAX_ITER):
    """Deterministic damped-Newton logistic regression; l2 skips intercept (idx 0)."""
    n = len(X)
    if n == 0:
        raise ValueError("empty training set")
    d = len(X[0])
    w = [0.0] * d
    pen = [0.0] + [l2] * (d - 1)
    obj = _penalized_nll(w, X, y, pen)
    for _ in range(max_iter):
        grad = [pen[j] * w[j] for j in range(d)]
        hess = [[pen[j] if i == j else 0.0 for j in range(d)] for i in range(d)]
        for xi, yi in zip(X, y):
            mu = _sigmoid(sum(w[j] * xi[j] for j in range(d)))
            r = mu * (1 - mu)
            for j in range(d):
                grad[j] += xi[j] * (mu - yi)
                for k in range(d):
                    hess[j][k] += r * xi[j] * xi[k]
        m = d
        A = [row[:] + [grad[i]] for i, row in enumerate(hess)]
        for col in range(m):
            piv = max(range(col, m), key=lambda r: abs(A[r][col]))
            if abs(A[piv][col]) < 1e-14:
                break
            A[col], A[piv] = A[piv], A[col]
            inv = 1.0 / A[col][col]
            for r in range(m):
                if r != col and A[r][col] != 0.0:
                    f = A[r][col] * inv
                    for c in range(col, m + 1):
                        A[r][c] -= f * A[col][c]
        dw = [A[i][m] * (1.0 / A[i][i]) if abs(A[i][i]) > 1e-14 else 0.0 for i in range(m)]
        step, improved = 1.0, False
        for _ls in range(40):
            w_new = [w[j] - step * dw[j] for j in range(d)]
            obj_new = _penalized_nll(w_new, X, y, pen)
            if obj_new <= obj + 1e-12:
                delta = max(abs(w_new[j] - w[j]) for j in range(d))
                w, obj = w_new, obj_new
                improved = True
                break
            step *= 0.5
        if not improved or max(abs(v) for v in dw) * step < tol:
            break
    return w


def predict_logistic(w, x) -> float:
    return _sigmoid(sum(w[j] * x[j] for j in range(len(w))))


def calibration_slope(ps, ys) -> float:
    xs, yv = [], []
    for p, y in zip(ps, ys):
        p = clamp_p(p)
        xs.append([1.0, math.log(p / (1 - p))])
        yv.append(float(y))
    return fit_logistic(xs, yv, l2=0.0)[1]


def paired_block_bootstrap_delta(ps_arm, ps_ref, ys, dates, n_resamples: int = 10_000,
                                 seed: int = RNG_SEED, alpha: float = 0.05):
    """Clusters = kickoff dates. Returns (mean_delta, lo, hi); delta<0 favors arm."""
    if not (len(ps_arm) == len(ps_ref) == len(ys) == len(dates)):
        raise ValueError("length mismatch")
    by_date = {}
    for p, q, y, d in zip(ps_arm, ps_ref, ys, dates):
        p, q = clamp_p(p), clamp_p(q)
        row = -(y * math.log(p) + (1 - y) * math.log(1 - p)) + (y * math.log(q) + (1 - y) * math.log(1 - q))
        by_date.setdefault(d, []).append(row)
    keys = sorted(by_date)
    sums = {d: sum(v) for d, v in by_date.items()}
    sizes = {d: len(v) for d, v in by_date.items()}
    rng = random.Random(seed)
    means = []
    for _ in range(n_resamples):
        tot = n_rows = 0
        for _k in range(len(keys)):
            d = keys[rng.randrange(len(keys))]
            tot += sums[d]
            n_rows += sizes[d]
        means.append(tot / n_rows if n_rows else 0.0)
    means.sort()

    def pct(q):
        return means[min(len(means) - 1, max(0, int(round(q * (len(means) - 1)))))]

    direct = sum(sums.values()) / sum(sizes.values())
    return direct, pct(alpha / 2), pct(1 - alpha / 2)
