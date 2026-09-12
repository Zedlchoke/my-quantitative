"""RATES-NG1 D2 correlation + verdict law (P-12 commit-1 artifact).

Pure functions: paired decision-STATE correlations only.  No outcome,
no PnL, and no storage of measurement values happens here.
"""

from __future__ import annotations

import math
from typing import Mapping, Sequence

from research.control.rates_ng1_run.d2 import d2_frozen_defaults as fd

SCHEMA = "rates_ng1_run/d2_correlation@1"

MEASURED = "MEASURED"
UNMEASURABLE = "UNMEASURABLE"

ELIGIBLE = "ELIGIBLE"
VETO = "VETO"
VETO_PENDING = "VETO_PENDING"


def _mean(v: Sequence[float]) -> float:
    return sum(v) / len(v)


def pearson(x: Sequence[float], y: Sequence[float]) -> float | None:
    """Pearson product-moment correlation of two equal-length paired
    series; None when n < 2 or either series has zero variance."""
    n = len(x)
    if n != len(y) or n < 2:
        return None
    mx, my = _mean(x), _mean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx <= 0.0 or syy <= 0.0:
        return None
    return sxy / math.sqrt(sxx * syy)


def average_ranks(v: Sequence[float]) -> list[float]:
    """Ranks (1-based) with average ranks assigned to ties."""
    order = sorted(range(len(v)), key=lambda i: v[i])
    ranks = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    """Spearman rank correlation = Pearson on average ranks (tie-
    corrected form); None under the same degeneracy rules as
    ``pearson``."""
    return pearson(average_ranks(x), average_ranks(y))


def paired_defined(a: Sequence[float | None],
                   b: Sequence[float | None]) -> tuple[list[float],
                                                       list[float]]:
    """Align two state series on instants where BOTH are defined."""
    xa: list[float] = []
    yb: list[float] = []
    for va, vb in zip(a, b):
        if va is None or vb is None:
            continue
        xa.append(float(va))
        yb.append(float(vb))
    return xa, yb


def shadow_screen(a: Sequence[float | None],
                  b: Sequence[float | None]) -> dict:
    """One proposal x shadow screen: Spearman AND Pearson on the
    both-defined instants, pooled per-shadow value
    max(|spearman|, |pearson|), and MEASURED/UNMEASURABLE status
    (UNMEASURABLE when fewer than 2 defined pairs or either side is
    degenerate on them -- never a silent zero)."""
    xa, yb = paired_defined(a, b)
    n_used = len(xa)
    sp = spearman(xa, yb)
    pe = pearson(xa, yb)
    if n_used < 2 or sp is None or pe is None:
        return {
            "status": UNMEASURABLE,
            "n_used": n_used,
            "spearman": None,
            "pearson": None,
            "pooled_abs_max": None,
            "reason": ("insufficient_defined_pairs" if n_used < 2
                       else "zero_variance_series_on_defined_pairs"),
        }
    return {
        "status": MEASURED,
        "n_used": n_used,
        "spearman": sp,
        "pearson": pe,
        "pooled_abs_max": max(abs(sp), abs(pe)),
        "reason": None,
    }


def margin_to_ceiling(pooled: float | None) -> float | None:
    """P-2 margin record: ceiling minus the proposal pooled |rho|
    (negative when the ceiling is breached)."""
    if pooled is None:
        return None
    return float(fd.NOVELTY_ABS_RHO_CEILING) - pooled


def proposal_verdict(screens: Mapping[str, dict]) -> dict:
    """Frozen verdict law: proposal pooled = max over MEASURED shadows;
    all five measured -> ELIGIBLE iff proposal_pooled <= ceiling else
    VETO; any UNMEASURABLE shadow -> VETO_PENDING (fail-closed,
    never-PASS-by-absence)."""
    missing = [k for k in fd.SHADOW_KEYS if k not in screens]
    if missing:
        raise ValueError(f"missing shadow screens: {missing}")
    unmeasured = [k for k in fd.SHADOW_KEYS
                  if screens[k]["status"] != MEASURED]
    measured_pooled = [screens[k]["pooled_abs_max"]
                       for k in fd.SHADOW_KEYS
                       if screens[k]["status"] == MEASURED]
    pooled = max(measured_pooled) if measured_pooled else None
    if unmeasured:
        verdict = VETO_PENDING
    elif pooled is not None and pooled <= float(
            fd.NOVELTY_ABS_RHO_CEILING):
        verdict = ELIGIBLE
    else:
        verdict = VETO
    return {
        "proposal_pooled_abs_rho": pooled,
        "margin_to_ceiling": margin_to_ceiling(pooled),
        "unmeasurable_shadows": unmeasured,
        "verdict": verdict,
    }
