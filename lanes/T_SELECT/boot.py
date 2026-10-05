"""boot.py — T_SELECT lane: log loss, paired ΔLL, kickoff-date-cluster bootstrap,
calibration slope (binomial GLM logit). Deterministic; seed 20261005 inherited.

Clamp law (PROTOCOL §5.1): probabilities clamped to [1e-15, 1-1e-15] before any
log/logit. Slope = coefficient of logit(p) in outcome ~ 1 + logit(p) (Newton-IRLS).
"""

from __future__ import annotations

import math

import numpy as np

SEED = 20261005
N_BOOT = 10_000
CLAMP_LO = 1e-15
CLAMP_HI = 1.0 - 1e-15
SLOPE_BAND = (0.85, 1.15)


def clamp(p: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(p, dtype=float), CLAMP_LO, CLAMP_HI)


def row_logloss(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Per-row log loss -(y ln p + (1-y) ln(1-p)) with the frozen clamp."""
    pc = clamp(p)
    y = np.asarray(y, dtype=float)
    return -(y * np.log(pc) + (1.0 - y) * np.log(1.0 - pc))


def mean_ll(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean(row_logloss(p, y)))


def paired_dll(p_arm: np.ndarray, p_ref: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Per-row LL(arm) - LL(reference) on identical rows (Δ<0 favors the arm)."""
    return row_logloss(p_arm, y) - row_logloss(p_ref, y)


def cluster_bootstrap_ci(dll: np.ndarray, clusters: np.ndarray, seed: int = SEED,
                         n_boot: int = N_BOOT, level: float = 0.95) -> tuple[float, float]:
    """Percentile CI for mean(dll) resampling kickoff-calendar-date clusters with
    replacement. Deterministic: np.random.default_rng(seed); clusters iterated in
    first-appearance order. Each resample draws len(clusters) clusters i.i.d.
    uniformly (multinomial counts over clusters — equivalent to resampling
    indices with replacement), then reweights rows by cluster counts."""
    dll = np.asarray(dll, dtype=float)
    uniq, inv = np.unique(clusters, return_inverse=True)
    n_c = len(uniq)
    sums = np.bincount(inv, weights=dll, minlength=n_c).astype(float)
    cnts = np.bincount(inv, minlength=n_c).astype(float)
    rng = np.random.default_rng(seed)
    counts = rng.multinomial(n_c, np.full(n_c, 1.0 / n_c), size=n_boot).astype(float)
    boot_means = (counts @ sums) / (counts @ cnts)
    alpha = (1.0 - level) / 2.0
    lo, hi = np.percentile(boot_means, [100 * alpha, 100 * (1.0 - alpha)])
    return float(lo), float(hi)


def logit(p: np.ndarray) -> np.ndarray:
    pc = clamp(p)
    return np.log(pc / (1.0 - pc))


def calibration_slope(p: np.ndarray, y: np.ndarray) -> float | None:
    """Binomial GLM (logit link) coefficient of logit(p). Returns None when
    degenerate (constant p). Newton-IRLS, no penalty, tolerance 1e-10."""
    p = np.asarray(p, dtype=float)
    if float(np.ptp(p)) == 0.0:
        return None
    X = np.column_stack([np.ones(len(p)), logit(p)])
    yv = np.asarray(y, dtype=float)
    beta = np.zeros(2)
    for _ in range(200):
        eta = X @ beta
        # stable sigmoid
        mu = np.where(eta >= 0, 1.0 / (1.0 + np.exp(-np.clip(eta, -700, 700))),
                      np.exp(np.clip(eta, -700, 700)) / (1.0 + np.exp(np.clip(eta, -700, 700))))
        w = np.maximum(mu * (1.0 - mu), 1e-12)
        grad = X.T @ (yv - mu)
        hess = X.T @ (X * w[:, None])
        try:
            step = np.linalg.solve(hess, grad)
        except np.linalg.LinAlgError:
            return float("nan")
        beta_new = beta + step
        if float(np.max(np.abs(step))) < 1e-10:
            beta = beta_new
            break
        beta = beta_new
    return float(beta[1])


def slope_in_band(slope: float | None) -> bool:
    return slope is not None and math.isfinite(slope) and SLOPE_BAND[0] <= slope <= SLOPE_BAND[1]
