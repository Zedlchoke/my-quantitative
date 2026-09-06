"""Frozen feature primitives for A5-V15-F1-ELITE-SIZE-ASYM.

Transcribed verbatim from proposal_P1 ``features_and_lags`` (nothing tuned):

* clip rule: ratio inputs clipped to ``[0.01, 100]`` before log;
* ``s_daily(t) = ln(clip(sum_toptrader_long_short_ratio))
  - ln(clip(count_toptrader_long_short_ratio))`` at metrics_date ``t``
  (the 00:00 UTC labeled row; the labeled-T snapshot time is T+5min
  archive-wide per probe_verdict_v15 -- irrelevant to availability under
  MEASURED_BOUND_LAG_3D);
* ``C_daily(t) = ln(clip(count_toptrader_long_short_ratio))`` -- the causal
  control's elite HEADCOUNT lean LEVEL alone (no sum component);
* window: median of the daily values over the usable daily rows in
  ``[D - lookback, D - 3]`` (anchor/control lookback 7 -> 5 daily rows;
  neighbour lookback 12 -> 10 daily rows); every window day satisfies
  ``metrics_date <= D - 3`` by construction (MEASURED_BOUND_LAG_3D, hard);
* hole rule (p3_freeze_amendment_1): if the window contains MORE than 10%
  missing metrics-day cells for that symbol, every decision for that
  symbol-date is REFUSED (refusal registry; no position; never a fill).
  The median is otherwise computed over the available staged rows only
  ("feature windows compute over available staged rows only").

No price, return, volatility, volume, OI, funding or basis input anywhere.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, Optional, Tuple

from research.v15.families.elite_size_asym.frozen_identity import (
    ANCHOR_WINDOW_LOOKBACK_DAYS,
    CLIP_HIGH,
    CLIP_LOW,
    MEASURED_BOUND_LAG_DAYS,
    NEIGHBOR_WINDOW_LOOKBACK_DAYS,
    WINDOW_HOLE_MAX_FRACTION,
)


@dataclass(frozen=True)
class FeatureOutcome:
    """The frozen feature outcome for one (symbol, decision date)."""

    signal: Optional[float]
    n_window_days: int
    n_usable: int
    n_missing: int
    refused: bool
    refusal_reason: Optional[str]


def clip_ratio(value: float) -> float:
    """The frozen clip rule ``[0.01, 100]`` applied before ``ln``."""
    if not math.isfinite(value):
        raise ValueError(f"clip_ratio expects a finite ratio, got {value!r}")
    return min(max(float(value), CLIP_LOW), CLIP_HIGH)


def s_daily(sum_ratio: float, count_ratio: float) -> float:
    """Within-elite size asymmetry daily value at one metrics_date."""
    return math.log(clip_ratio(sum_ratio)) - math.log(clip_ratio(count_ratio))


def c_daily(count_ratio: float) -> float:
    """Elite headcount lean LEVEL daily value at one metrics_date."""
    return math.log(clip_ratio(count_ratio))


def window_days(decision_date: date, lookback_days: int) -> Tuple[date, ...]:
    """The calendar window ``[D - lookback, D - 3]``, oldest first."""
    if lookback_days <= MEASURED_BOUND_LAG_DAYS:
        raise ValueError(
            f"lookback {lookback_days}d leaves no lag margin "
            f"(MEASURED_BOUND_LAG_{MEASURED_BOUND_LAG_DAYS}D)"
        )
    oldest = decision_date - timedelta(days=lookback_days)
    newest = decision_date - timedelta(days=MEASURED_BOUND_LAG_DAYS)
    n_days = (newest - oldest).days + 1
    return tuple(oldest + timedelta(days=i) for i in range(n_days))


def feature_outcome(
    *,
    decision_date: date,
    lookback_days: int,
    daily_values: Dict[date, Optional[float]],
) -> FeatureOutcome:
    """Median daily value over the window, with the frozen hole rule.

    ``daily_values`` maps each metrics_date to its daily value, or ``None``
    when the staged cell for that day is missing/not ok (holes).  Days the
    loader dropped entirely (global defect dates) must also be ``None``.

    Refusal condition (frozen): ``n_missing / n_window_days > 0.10``.  The
    anchor/control window has 5 cells -> any missing cell refuses; the
    neighbour window has 10 cells -> 1 missing cell (exactly 10%) is
    tolerated, 2 refuse.  The median is computed over the USABLE rows only.
    """
    window = window_days(decision_date, lookback_days)
    usable: list[float] = []
    missing = 0
    for day in window:
        value = daily_values.get(day)
        if value is None or not math.isfinite(value):
            missing += 1
        else:
            usable.append(float(value))
    n_days = len(window)
    hole_fraction = missing / n_days
    if hole_fraction > WINDOW_HOLE_MAX_FRACTION:
        return FeatureOutcome(
            signal=None,
            n_window_days=n_days,
            n_usable=len(usable),
            n_missing=missing,
            refused=True,
            refusal_reason=(
                f"window_hole: {missing}/{n_days} missing metrics-day cells "
                f"({hole_fraction:.2%}) > "
                f"{WINDOW_HOLE_MAX_FRACTION:.0%} for window "
                f"[{window[0].isoformat()}, {window[-1].isoformat()}]"
            ),
        )
    if not usable:
        # Unreachable under the rule above (0 usable => 100% missing), kept
        # as an explicit fail-closed guard, never a synthesized signal.
        raise ValueError(
            f"no usable feature rows in window for {decision_date.isoformat()}"
        )
    signal = float(statistics.median(usable))
    if not math.isfinite(signal):
        raise ValueError("non-finite feature median")
    return FeatureOutcome(
        signal=signal,
        n_window_days=n_days,
        n_usable=len(usable),
        n_missing=missing,
        refused=False,
        refusal_reason=None,
    )


__all__ = [
    "FeatureOutcome",
    "c_daily",
    "clip_ratio",
    "feature_outcome",
    "s_daily",
    "window_days",
]
