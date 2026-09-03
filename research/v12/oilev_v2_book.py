"""V12P A4 -- the fixed OILEV-V2 deterministic diversified book (draft).

PLAN_crypto.md section 8.2 / A4 deliverable 3 (lesson L-V11-2 repair): the
OILEV mechanism (deleveraging/crowding through PIT OI flow/stock) keeps its
identity, but the book becomes cap-compatible BY CONSTRUCTION:

1. rank the eligible universe by the injected PIT signal (the ranking
   feature itself is frozen by the A1 brief -- this module is deliberately
   ranking-agnostic and accepts any finite ``symbol -> score`` mapping);
2. when at least ``MIN_ELIGIBLE`` (9) names are eligible, take the
   ``LEG_NAMES`` (4) LOWEST scores as the long leg and the ``LEG_NAMES`` (4)
   HIGHEST scores as the short leg (deterministic: score order, exact ties
   broken by lexicographically smallest symbol id);
3. equal weight per leg (``gross / 2`` split evenly inside each leg);
4. apply the frozen BTC beta hedge with the V11 family semantics -- a
   CONTEXT semantic only (90d daily beta vs BTCUSDT as identity context;
   BTCUSDT is benchmark-excluded and can NEVER appear as a position);
5. uniformly scale the ENTIRE book when needed so every final absolute
   weight is <= the frozen 0.30 adapter cap.  Individual names are NEVER
   clipped and NEVER renormalised.

The cap holds by construction and is asserted after scaling.  Fewer than
``MIN_ELIGIBLE`` eligible names raises :class:`EligibilityShortfall`
(fail-closed): a stamp without sufficient breadth has NO book.

This module computes no PnL, no returns, no scored metric.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Optional

from research.adapter_v10.protocol import (
    AdapterError,
    ContractViolation,
    DEFAULT_WEIGHT_CAP_MAX,
    WEIGHT_TOL,
)

SCHEMA_VERSION = "v12.oilev_v2.book.v1"

#: The frozen adapter cap (unchanged since V10 scored runs; never loosened).
CAP_MAX = DEFAULT_WEIGHT_CAP_MAX

#: Minimum eligible breadth per stamp (PLAN section 7 A4 / L-V11-2).
MIN_ELIGIBLE = 9

#: Names per signal leg (four lowest / four highest).
LEG_NAMES = 4

#: Gross notional target of the whole book.
GROSS_TARGET = 1.0

#: Pinned context-only benchmark leg (V11 family semantics; never a position).
BENCHMARK_SYMBOL = "BTCUSDT"

#: The frozen BTC beta hedge, verbatim V11 semantics (context-only).
BETA_HEDGE_SEMANTICS = (
    "context-only 90d daily BTC beta hedge (V11 family semantics): "
    "BTCUSDT is benchmark-excluded and can never appear as a position; "
    "the hedge never adds a traded leg or alters leg weights"
)


class EligibilityShortfall(AdapterError):
    """A stamp has fewer than ``MIN_ELIGIBLE`` eligible names -- no book."""


def build_oilev_v2_book(
    scores: Mapping[str, Any],
    *,
    invert: bool = False,
    legs_per_side: int = LEG_NAMES,
    min_eligible: int = MIN_ELIGIBLE,
    gross: float = GROSS_TARGET,
    cap_max: float = CAP_MAX,
    beta_hedge_ratios: Optional[Mapping[str, float]] = None,
) -> dict[str, Any]:
    """The deterministic diversified OILEV-V2 book for one decision stamp.

    ``scores`` maps PIT-eligible-candidate symbols to their signal value
    (higher = more crowded; the A1 brief freezes the feature).  Entries that
    are not finite floats are INELIGIBLE and recorded -- never guessed.
    ``invert=True`` flips the whole book end-to-end (the causal negative
    control arm).  Returns the book payload; the post-scale cap is asserted,
    not assumed.
    """
    cap = float(cap_max)
    if cap <= 0.0:
        raise ContractViolation("cap_max must be positive")
    if int(legs_per_side) < 1:
        raise ContractViolation("legs_per_side must be >= 1")
    if not math.isfinite(float(gross)) or float(gross) <= 0.0:
        raise ContractViolation("gross must be finite positive")

    cleaned: dict[str, float] = {}
    ineligible: dict[str, str] = {}
    for raw_sym, raw_value in dict(scores).items():
        sym = str(raw_sym)
        if sym == BENCHMARK_SYMBOL:
            raise ContractViolation(
                "the pinned benchmark leg can never enter the tradeable book"
            )
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            ineligible[sym] = "NON_NUMERIC_SCORE"
            continue
        if not math.isfinite(value):
            ineligible[sym] = "NON_FINITE_SCORE"
            continue
        cleaned[sym] = value

    eligible = sorted(cleaned)
    if len(eligible) < int(min_eligible):
        raise EligibilityShortfall(
            f"only {len(eligible)} eligible names at this stamp; "
            f"the diversified book requires >= {int(min_eligible)} (fail-closed)"
        )

    sign = -1.0 if invert else 1.0
    ordered = sorted((sign * cleaned[sym], sym) for sym in eligible)
    k = int(legs_per_side)
    longs = [sym for _value, sym in ordered[:k]]
    shorts = [sym for _value, sym in ordered[len(ordered) - k :]]
    overlap = sorted(set(longs) & set(shorts))
    if overlap:
        raise ContractViolation(f"long/short legs overlap: {overlap}")

    per_name = (float(gross) / 2.0) / float(k)
    weights: dict[str, float] = {sym: per_name for sym in longs}
    for sym in shorts:
        weights[sym] = weights.get(sym, 0.0) - per_name

    max_abs = max(abs(w) for w in weights.values())
    scale = 1.0
    if max_abs > cap:
        scale = cap / max_abs  # uniform WHOLE-BOOK scale; never per-name clipping
        weights = {sym: w * scale for sym, w in weights.items()}

    rounded = {sym: round(w, 12) for sym, w in sorted(weights.items())}
    post_max = max(abs(w) for w in rounded.values())
    assert post_max <= cap + WEIGHT_TOL, (
        f"cap must hold by construction: max|w|={post_max} > {cap}"
    )

    hedge_context: dict[str, Any] = {
        "semantics": BETA_HEDGE_SEMANTICS,
        "benchmark_symbol": BENCHMARK_SYMBOL,
        "ratios": None,
    }
    if beta_hedge_ratios is not None:
        ratios: dict[str, float] = {}
        for raw_sym, raw_ratio in dict(beta_hedge_ratios).items():
            sym = str(raw_sym)
            try:
                ratio = float(raw_ratio)
            except (TypeError, ValueError):
                raise ContractViolation(f"beta hedge ratio for {sym} is not numeric")
            if not math.isfinite(ratio):
                raise ContractViolation(f"beta hedge ratio for {sym} is not finite")
            ratios[sym] = round(ratio, 12)
        hedge_context["ratios"] = {sym: ratios[sym] for sym in sorted(ratios)}

    return {
        "schema": SCHEMA_VERSION,
        "status": "OK",
        "weights": [[sym, rounded[sym]] for sym in sorted(rounded)],
        "longs": sorted(longs),
        "shorts": sorted(shorts),
        "n_eligible": len(eligible),
        "n_longs": len(longs),
        "n_shorts": len(shorts),
        "per_name_weight_before_scale": round(per_name, 12),
        "scale_applied": round(scale, 12),
        "max_abs_weight": round(post_max, 12),
        "cap_max": cap,
        "gross_after_scale": round(math.fsum(abs(w) for w in rounded.values()), 12),
        "beta_hedge": hedge_context,
        "diagnostics": {
            "ineligible": ineligible,
            "ranking_rule": (
                "long = 4 lowest scores, short = 4 highest scores; exact score "
                "ties broken by lexicographically smallest symbol id"
            ),
            "invert": bool(invert),
            "scaling_policy": (
                "uniform whole-book scale to cap when needed; individual names "
                "are never clipped or renormalised"
            ),
        },
    }


__all__ = [
    "BENCHMARK_SYMBOL",
    "BETA_HEDGE_SEMANTICS",
    "CAP_MAX",
    "EligibilityShortfall",
    "GROSS_TARGET",
    "LEG_NAMES",
    "MIN_ELIGIBLE",
    "SCHEMA_VERSION",
    "build_oilev_v2_book",
]
