"""V12P A4 -- OILEV-V2 schedule/spec DRAFT (PLAN_crypto.md section 8.2).

This is a schedule/spec draft only: it freezes nothing centrally and scores
nothing.  The identity follows PLAN section 8.2 verbatim:

* mechanism unchanged -- deleveraging/crowding through PIT OI flow/stock;
* book = the cap-compatible diversified construction fixed in A4
  (:mod:`research.v12.oilev_v2_book`);
* arms: 28-day OI-flow anchor; 56-day OI-stock neighbour; sign-inverted
  28-day control;
* if coverage, PIT staleness, breadth or cap feasibility fails, the family
  is ``BLOCKED_PRE_SCORE`` and its three slots are not reassigned.

The stamp calendar reuses the V11 OILEV plugin's weekly-Monday convention
for the STAMP CALENDAR ONLY (A4 directive); the V11 DV-median eligibility is
deliberately NOT reused.  The PIT ranking feature remains frozen by the A1
brief; the feasibility run in this lane uses the provisional PIT OI feature
scores below purely as the injected ranking -- book mechanics and the
feasibility verdict are ranking-value-independent given >= 9 finite scores.
"""

from __future__ import annotations

import bisect
import math
from typing import Any, Mapping, Optional, Sequence

from research.adapter_v10.protocol import ContractViolation

SCHEMA_VERSION = "v12.oilev_v2.spec.draft.v1"

DAY_NS = 86_400_000_000_000
HOUR_NS = 3_600_000_000_000

#: V11 S0 snapshot window (the OILEV-V2 stamps live inside it; PLAN A3.4).
WINDOW_START_ISO = "2025-08-22T00:00:00Z"
WINDOW_END_ISO = "2026-08-21T00:00:00Z"

#: Stamp calendar convention (V11 OILEV, reused for the calendar only).
STAMP_CONVENTION = (
    "weekly Monday 00:00:00Z decision stamps over the V11 S0 window "
    "2025-08-22..2026-08-21 (research.v11.families.oilever_delev.strategy."
    "weekly_mondays, reused for the stamp calendar ONLY)"
)

#: OI PIT anchor gate (V11-consistent; fail closed per symbol per stamp).
OI_MAX_STALENESS_HOURS = 48

#: The three frozen arms (PLAN section 8.2). ``invert`` flips the whole book
#: end-to-end for the causal negative control.
OILEV_V2_ARMS: tuple[dict[str, Any], ...] = (
    {
        "arm_id": "OILEV-V2-FLOW-28D",
        "role": "anchor",
        "feature_kind": "oi_flow",
        "formation_days": 28,
        "invert": False,
    },
    {
        "arm_id": "OILEV-V2-STOCK-56D",
        "role": "neighbour",
        "feature_kind": "oi_stock",
        "formation_days": 56,
        "invert": False,
    },
    {
        "arm_id": "OILEV-V2-FLOW-28D-INV",
        "role": "causal_negative_control",
        "feature_kind": "oi_flow",
        "formation_days": 28,
        "invert": True,
    },
)

#: Pre-score block rule (PLAN section 8.2, verbatim semantics).
BLOCKED_PRE_SCORE_RULE = (
    "if coverage, PIT staleness, breadth or cap feasibility fails, the family "
    "is BLOCKED_PRE_SCORE and its three slots are not reassigned"
)


def stamp_calendar(
    *,
    window_start_iso: str = WINDOW_START_ISO,
    window_end_iso: str = WINDOW_END_ISO,
) -> tuple[int, ...]:
    """Weekly Monday 00:00:00Z decision stamps (V11 calendar convention)."""
    from research.v11.families.oilever_delev.strategy import weekly_mondays

    return weekly_mondays(
        window_start_iso=window_start_iso, window_end_iso=window_end_iso
    )


# --------------------------------------------------------------------------- #
# Provisional PIT OI feature scores (injected ranking for the feasibility run)
# --------------------------------------------------------------------------- #
def _oi_anchor_before(
    series: Sequence[tuple[int, float]],
    stamp_ns: int,
    *,
    max_staleness_ns: int = OI_MAX_STALENESS_HOURS * HOUR_NS,
) -> Optional[float]:
    """Last COMPLETED OI row STRICTLY BEFORE the stamp, fresh and positive."""
    if not series:
        return None
    times = [int(t) for t, _ in series]
    idx = bisect.bisect_left(times, int(stamp_ns)) - 1
    if idx < 0:
        return None
    ts, value = series[idx]
    if int(stamp_ns) - int(ts) > max_staleness_ns:
        return None
    value = float(value)
    if not math.isfinite(value) or value <= 0.0:
        return None
    return value


def provisional_oi_feature_scores(
    oi_by_symbol: Mapping[str, Sequence[tuple[int, float]]],
    stamp_ns: int,
    *,
    feature_kind: str,
    formation_days: int,
) -> dict[str, float]:
    """Provisional PIT ranking scores from daily OI snapshots (A1 brief pending).

    ``oi_flow``: 28d/56d log OI-growth from the fresh daily-last anchor.
    ``oi_stock``: percentile of the current OI level within its own trailing
    window (needs >= 2 window points).  A symbol whose PIT anchor is stale,
    non-positive or whose feature is not computable is simply INELIGIBLE at
    the stamp (fail-closed, never guessed) -- recorded by the book builder.
    """
    stamp = int(stamp_ns)
    if feature_kind not in ("oi_flow", "oi_stock"):
        raise ContractViolation(f"unknown feature_kind {feature_kind!r}")
    if int(formation_days) < 1:
        raise ContractViolation("formation_days must be >= 1")
    scores: dict[str, float] = {}
    for sym in sorted(oi_by_symbol):
        series = oi_by_symbol[sym]
        now = _oi_anchor_before(series, stamp)
        if now is None:
            continue
        if feature_kind == "oi_flow":
            past = _oi_anchor_before(series, stamp - int(formation_days) * DAY_NS)
            if past is None or past <= 0.0:
                continue
            value = math.log(now / past)
        else:
            lo = stamp - int(formation_days) * DAY_NS
            window = [float(v) for t, v in series if lo <= int(t) < stamp]
            if len(window) < 2:
                continue
            rank = sum(1 for v in window if v <= now)
            value = rank / len(window)
        if math.isfinite(value):
            scores[sym] = value
    return scores


def oilev_v2_spec_payload() -> dict[str, Any]:
    """The JSON-safe draft spec payload (no scored result, no central freeze)."""
    return {
        "schema": SCHEMA_VERSION,
        "family_draft_id": "OILEV-V2",
        "window_start_iso": WINDOW_START_ISO,
        "window_end_iso": WINDOW_END_ISO,
        "stamp_convention": STAMP_CONVENTION,
        "book_policy": {
            "min_eligible": 9,
            "legs_per_side": 4,
            "equal_weight_per_leg": True,
            "cap_max": 0.30,
            "scaling_policy": (
                "uniform whole-book scale when needed; never clip or "
                "renormalise individual names; cap holds by construction"
            ),
        },
        "beta_hedge": "frozen BTC beta hedge, V11 family semantics (context-only)",
        "arms": [dict(arm) for arm in OILEV_V2_ARMS],
        "ranking_feature_status": (
            "provisional PIT OI flow/stock scores in this lane; the frozen "
            "ranking is fixed by the A1 brief (oilever_v2_brief)"
        ),
        "blocked_pre_score_rule": BLOCKED_PRE_SCORE_RULE,
    }


__all__ = [
    "BLOCKED_PRE_SCORE_RULE",
    "DAY_NS",
    "OI_MAX_STALENESS_HOURS",
    "OILEV_V2_ARMS",
    "SCHEMA_VERSION",
    "STAMP_CONVENTION",
    "WINDOW_END_ISO",
    "WINDOW_START_ISO",
    "oilev_v2_spec_payload",
    "provisional_oi_feature_scores",
    "stamp_calendar",
]
