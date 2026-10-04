"""FROZEN protocol constants + metric implementations (lane C PROTOCOL_EVAL.md).

Every constant here is a PREREGISTRATION, not a result. The successor scored
cycle (NBA-WINPROB-SCORED-V1) must inherit sections 2-6 and 9 of
lanes/C_protocol/PROTOCOL_EVAL.md verbatim before any outcome is observed.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

# --- frozen data split (lane B measured end of data: 2015-06-16) -----------
TEST_SEASONS = (2009, 2010, 2011, 2012, 2013, 2014, 2015)  # 2008-09 .. 2014-15
TRAIN_SEASONS_RANGE = (1947, 2008)  # inclusive

# --- frozen Elo constants (B1 arms) ----------------------------------------
ELO_INIT = 1500.0
ELO_GAMMA = 0.75  # season-boundary reversion toward 1500 (fixed, not gridded)

@dataclass(frozen=True)
class Arm:
    arm_id: str
    kind: str  # "B0" | "B1" | "B2"
    K: float | None = None
    HCA: float | None = None
    features: tuple[str, ...] = ()

# Trial budget: 9 arms TOTAL, binding (PROTOCOL_EVAL.md sec5).
ARMS: tuple[Arm, ...] = (
    Arm("B0", "B0"),
    Arm("B1-a", "B1", K=16, HCA=0),
    Arm("B1-b", "B1", K=16, HCA=100),
    Arm("B1-c", "B1", K=32, HCA=0),
    Arm("B1-d", "B1", K=32, HCA=100),
    Arm("B2-a", "B2", features=("elo_diff", "rest_diff", "b2b_home", "b2b_away", "form_home", "form_away")),
    Arm("B2-b", "B2", features=("elo_diff", "form_home", "form_away")),
    Arm("B2-c", "B2", features=("elo_diff", "rest_diff", "b2b_home", "b2b_away")),
    Arm("B2-d", "B2", features=("elo_diff",)),
)
assert len(ARMS) == 9

# --- frozen B2 estimator constants -----------------------------------------
LOGIT_L2 = 1.0          # penalty on standardized features, intercept unpenalized
LOGIT_TOL = 1e-8
LOGIT_MAX_ITER = 100
RNG_SEED = 20261004     # protocol seed (bootstrap + any stochastic step)

# --- frozen feature constants (PROTOCOL_EVAL.md sec2) ----------------------
REST_CAP = 10           # rest_days cap == "no prior game" sentinel
FORM_WINDOW = 10        # last <=10 completed regular-season games, current season
P_CLAMP = 1e-15

SUCCESSOR_GO_PHRASE = "GO NBA WINPROB SCORED V1 EVALUATION"


def clamp_p(p: float) -> float:
    return min(max(p, P_CLAMP), 1.0 - P_CLAMP)


def log_loss(ps, ys) -> float:
    n = 0
    tot = 0.0
    for p, y in zip(ps, ys):
        p = clamp_p(p)
        tot += -(y * math.log(p) + (1 - y) * math.log(1 - p))
        n += 1
    if n == 0:
        raise ValueError("empty evaluation set")
    return tot / n


def brier(ps, ys) -> float:
    n = 0
    tot = 0.0
    for p, y in zip(ps, ys):
        tot += (p - y) ** 2
        n += 1
    if n == 0:
        raise ValueError("empty evaluation set")
    return tot / n


def reliability_bins(ps, ys, n_bins: int = 10):
    """10 equal-width bins on p -> (n, mean_p, observed_rate) per bin."""
    bins = [[0, 0.0, 0] for _ in range(n_bins)]
    for p, y in zip(ps, ys):
        b = min(n_bins - 1, int(p * n_bins))
        bins[b][0] += 1
        bins[b][1] += p
        bins[b][2] += y
    out = []
    for b, (n, sump, sumy) in enumerate(bins):
        out.append((b, n, (sump / n) if n else None, (sumy / n) if n else None))
    return out


def calibration_slope(ps, ys) -> float:
    """Binomial-GLM coefficient of logit(p) in outcome ~ 1 + logit(p)."""
    xs, yv = [], []
    for p, y in zip(ps, ys):
        p = clamp_p(p)
        x = math.log(p / (1 - p))
        xs.append([1.0, x])  # intercept + slope
        yv.append(float(y))
    w = fit_logistic(xs, yv, l2=0.0)
    return w[1]


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
    """Deterministic damped Newton-Raphson logistic regression.

    l2 penalizes all coefficients EXCEPT the intercept (index 0); the
    intercept column is expected to be a leading constant 1.0. Backtracking
    line search on the penalized objective keeps separable/skewed data from
    diverging. Small dense solver; feature counts here are <= 7.
    """
    n = len(X)
    if n == 0:
        raise ValueError("empty training set")
    d = len(X[0])
    w = [0.0] * d
    pen = [0.0] + [l2] * (d - 1)  # intercept unpenalized
    obj = _penalized_nll(w, X, y, pen)
    for _ in range(max_iter):
        grad = [pen[j] * w[j] for j in range(d)]
        hess = [[pen[j] if i == j else 0.0 for j in range(d)] for i in range(d)]
        for xi, yi in zip(X, y):
            z = sum(w[j] * xi[j] for j in range(d))
            mu = _sigmoid(z)
            r = mu * (1 - mu)
            for j in range(d):
                grad[j] += xi[j] * (mu - yi)
                for k in range(d):
                    hess[j][k] += r * xi[j] * xi[k]
        # solve H dw = grad (Gauss-Jordan with partial pivoting)
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
        step = 1.0
        improved = False
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
    z = sum(w[j] * x[j] for j in range(len(w)))
    if z >= 0:
        e = math.exp(-z); return 1.0 / (1.0 + e)
    e = math.exp(z); return e / (1.0 + e)


def paired_block_bootstrap_delta(ps_arm, ps_ref, ys, dates, n_resamples: int = 10_000, seed: int = RNG_SEED, alpha: float = 0.05):
    """Date-clustered block bootstrap CI for mean ΔLL = LL(arm) − LL(ref).

    Resamples game DATES with replacement; all same-date rows move together.
    Returns (mean_delta, lo, hi) percentile CI. Δ < 0 favors the arm.
    """
    if not (len(ps_arm) == len(ps_ref) == len(ys) == len(dates)):
        raise ValueError("length mismatch")
    by_date = {}
    for p, q, y, d in zip(ps_arm, ps_ref, ys, dates):
        p, q = clamp_p(p), clamp_p(q)
        row = -(y * math.log(p) + (1 - y) * math.log(1 - p)) + (y * math.log(q) + (1 - y) * math.log(1 - q))
        by_date.setdefault(d, []).append(row)
    cluster_sums = {d: sum(rows) for d, rows in by_date.items()}
    cluster_keys = sorted(cluster_sums)
    sizes = {d: len(by_date[d]) for d in cluster_keys}
    total_rows = sum(sizes.values())
    rng = random.Random(seed)
    means = []
    for _ in range(n_resamples):
        tot = 0.0
        n_rows = 0
        for __ in range(len(cluster_keys)):
            d = cluster_keys[rng.randrange(len(cluster_keys))]
            tot += cluster_sums[d]
            n_rows += sizes[d]
        means.append(tot / n_rows if n_rows else 0.0)
    means.sort()
    def pct(q):
        idx = min(len(means) - 1, max(0, int(round(q * (len(means) - 1)))))
        return means[idx]
    direct = sum(sum(rows) for rows in by_date.values()) / total_rows
    return direct, pct(alpha / 2), pct(1 - alpha / 2)
