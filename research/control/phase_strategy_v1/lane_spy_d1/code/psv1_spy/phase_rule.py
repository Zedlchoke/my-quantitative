"""Frozen phase rule for cell SPY_D1 (PSV1-SPYD1-QUAD-SMA200-SLOPE20).

The rule, its parameters and its notches were frozen in
freezes/phase_rule_freeze.json BEFORE any label was computed on the real
snapshot. Deterministic and causal: label at t uses only closes with index
<= t. Five outputs exactly. TRANSITION_UNKNOWN is code-owned by explicit
margin/insufficiency conditions.

There is no weekday, date or external-decision input anywhere in this rule:
labels are a pure function of the ordered adjusted-close series. The
weekday-rotation gate (gates.py) asserts this invariance directly.
"""

from dataclasses import dataclass
from typing import List, Sequence

ACCUMULATION = "ACCUMULATION"
UPTREND = "UPTREND"
DISTRIBUTION = "DISTRIBUTION"
DOWNTREND = "DOWNTREND"
UNKNOWN = "TRANSITION_UNKNOWN"

PHASES = (ACCUMULATION, UPTREND, DISTRIBUTION, DOWNTREND, UNKNOWN)


@dataclass(frozen=True)
class RuleParams:
    sma_n: int = 200
    slope_k: int = 20
    p_band: float = 0.01
    s_band: float = 0.005

    @property
    def warmup(self) -> int:
        # SMA needs sma_n closes; slope needs SMA at t - slope_k, i.e. the
        # SMA itself needs to exist at index t - slope_k, which requires
        # t - slope_k >= sma_n - 1  =>  t >= sma_n + slope_k - 1.
        return self.sma_n + self.slope_k - 1


def rolling_sma(closes: Sequence[float], n: int) -> List[float]:
    """Causal rolling mean; entries before index n-1 are NaN-free via float('nan')."""
    out: List[float] = [float("nan")] * len(closes)
    if len(closes) < n:
        return out
    window = sum(closes[:n])
    out[n - 1] = window / n
    for t in range(n, len(closes)):
        window += closes[t] - closes[t - n]
        out[t] = window / n
    return out


def label_from_observables(r: float, s: float, p_band: float, s_band: float) -> str:
    """Pure quadrant law (boundary semantics frozen):
    r >= +band and s >= +band -> UPTREND; r >= +band and s <= -band ->
    DISTRIBUTION; r <= -band and s >= +band -> ACCUMULATION; r <= -band and
    s <= -band -> DOWNTREND; otherwise TRANSITION_UNKNOWN (|r| < band or
    |s| < band)."""
    if r >= p_band and s >= s_band:
        return UPTREND
    if r >= p_band and s <= -s_band:
        return DISTRIBUTION
    if r <= -p_band and s >= s_band:
        return ACCUMULATION
    if r <= -p_band and s <= -s_band:
        return DOWNTREND
    return UNKNOWN


def compute_labels(
    closes: Sequence[float], params: RuleParams = RuleParams()
) -> List[str]:
    """Phase label per bar, causal, five outputs exactly.

    Bars with insufficient history (index < warmup) are TRANSITION_UNKNOWN
    (explicit insufficiency condition) and are excluded from eras/floors
    downstream by the frozen warmup law.
    """
    n = params.sma_n
    k = params.slope_k
    sma = rolling_sma(closes, n)
    labels: List[str] = [UNKNOWN] * len(closes)
    for t in range(len(closes)):
        if t < params.warmup:
            labels[t] = UNKNOWN  # insufficient evidence (warmup)
            continue
        base = sma[t - k]
        if base != base or sma[t] != sma[t]:  # NaN guard (defensive)
            labels[t] = UNKNOWN
            continue
        r = closes[t] / sma[t] - 1.0
        s = (sma[t] - base) / base
        labels[t] = label_from_observables(r, s, params.p_band, params.s_band)
    return labels


NOTCHED_PARAMS = {
    "sma_n_down": RuleParams(sma_n=175),
    "sma_n_up": RuleParams(sma_n=225),
    "slope_k_down": RuleParams(slope_k=15),
    "slope_k_up": RuleParams(slope_k=25),
    "p_band_down": RuleParams(p_band=0.005),
    "p_band_up": RuleParams(p_band=0.015),
    "s_band_down": RuleParams(s_band=0.0025),
    "s_band_up": RuleParams(s_band=0.0075),
}


def label_agreement(base: Sequence[str], other: Sequence[str], start: int = 0) -> float:
    """Fraction of post-`start` sessions with identical labels (report only)."""
    if len(base) != len(other):
        raise ValueError("label streams differ in length")
    total = len(base) - start
    if total <= 0:
        raise ValueError("empty comparison window")
    same = sum(1 for i in range(start, len(base)) if base[i] == other[i])
    return round(same / total, 6)


def sensitivity_table(
    closes: Sequence[float], params: RuleParams = RuleParams()
) -> dict:
    """Single-notch label-agreement table. REPORTED, never optimized."""
    base = compute_labels(closes, params)
    warm = params.warmup
    out = {}
    for name, notched in NOTCHED_PARAMS.items():
        # keep every other parameter at base; NOTCHED_PARAMS already varies one
        merged = RuleParams(
            sma_n=notched.sma_n if name.startswith("sma_n") else params.sma_n,
            slope_k=notched.slope_k if name.startswith("slope_k") else params.slope_k,
            p_band=notched.p_band if name.startswith("p_band") else params.p_band,
            s_band=notched.s_band if name.startswith("s_band") else params.s_band,
        )
        # recompute with the merged params (guards against accidental multi-notch)
        alt = compute_labels(closes, merged)
        # warmup may differ for notched sma_n/slope_k; compare from the max warmup
        start = max(warm, merged.warmup)
        out[name] = {
            "params": {
                "sma_n": merged.sma_n,
                "slope_k": merged.slope_k,
                "p_band": merged.p_band,
                "s_band": merged.s_band,
            },
            "label_agreement_post_warmup": label_agreement(base, alt, start=start),
        }
    return out
