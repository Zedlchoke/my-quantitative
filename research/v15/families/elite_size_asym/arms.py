"""Frozen arm registry for A5-V15-F1-ELITE-SIZE-ASYM.

The three frozen arms of ``research/control/v15_run/selection_freeze_v15.json``
with their proposal_P1 definitions -- the STRUCTURE is shared (identical
tercile portfolio machinery, folds, fills, costs), only the feature and the
window/side shape differ, exactly as frozen:

* ``A5-F1-ANCHOR-ASYM`` (anchor, ``ELITE-SIZE-ASYM-ANCHOR``): signal
  ``S_i(D)`` = median over t in [D-7, D-3] of ``s_daily`` (5 usable daily
  rows); sides 7/6/7 by asymmetry rank; long bottom-7 / short top-7.
* ``A5-F1-NEIGHBOR`` (neighbour, ``ELITE-SIZE-ASYM-NB10Q``): same mechanism,
  same direction, same machinery except ``S_i(D)`` = median over t in
  [D-12, D-3] (10 usable daily rows) and sides are the frozen 5/10/5 with
  per-name weight 0.10.
* ``A5-F1-CTL-ELITELEVEL`` (causal negative control, ``CTL-ELITELEVEL``):
  identical portfolio machinery (terciles 7/6/7, daily, same folds, costs,
  fills) with signal ``C_i(D)`` = median over t in [D-7, D-3] of
  ``ln(clip(count_toptrader_long_short_ratio))`` -- the elite HEADCOUNT lean
  LEVEL alone; SHORT top tercile (most elite-long), LONG bottom tercile
  (most elite-short).  Structurally the SAME book on the level feature: it
  never reads ``sum_toptrader_long_short_ratio``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from research.v15.families.elite_size_asym.book import ANCHOR_BOOK, NEIGHBOR_BOOK, BookSpec
from research.v15.families.elite_size_asym.frozen_identity import (
    ANCHOR_ARM,
    ANCHOR_WINDOW_LOOKBACK_DAYS,
    CONTROL_ARM,
    NEIGHBOR_ARM,
    NEIGHBOR_WINDOW_LOOKBACK_DAYS,
)


@dataclass(frozen=True)
class ArmSpec:
    """The frozen per-arm feature/window/book binding."""

    arm_id: str
    name: str
    role: str
    #: "asym" = ln(sum_toptrader) - ln(count_toptrader) (anchor + neighbour);
    #: "level" = ln(count_toptrader) alone (causal control; never reads sum).
    feature: str
    window_lookback_days: int
    book_spec: BookSpec
    #: long the LOW-signal side (bottom tercile), short the HIGH-signal side.
    direction_statement: str


ANCHOR_SPEC = ArmSpec(
    arm_id=ANCHOR_ARM,
    name="ELITE-SIZE-ASYM-ANCHOR",
    role="anchor",
    feature="asym",
    window_lookback_days=ANCHOR_WINDOW_LOOKBACK_DAYS,
    book_spec=ANCHOR_BOOK,
    direction_statement=(
        "long bottom-7 S (elite size leans most short), short top-7 S "
        "(fade the size-heavy side); preregistered, no post-hoc flip"
    ),
)

NEIGHBOR_SPEC = ArmSpec(
    arm_id=NEIGHBOR_ARM,
    name="ELITE-SIZE-ASYM-NB10Q",
    role="neighbour",
    feature="asym",
    window_lookback_days=NEIGHBOR_WINDOW_LOOKBACK_DAYS,
    book_spec=NEIGHBOR_BOOK,
    direction_statement=(
        "same mechanism and direction as the anchor; window [D-12, D-3] "
        "(10 usable daily rows), sides 5/10/5, per-name weight 0.10"
    ),
)

CONTROL_SPEC = ArmSpec(
    arm_id=CONTROL_ARM,
    name="CTL-ELITELEVEL",
    role="causal_negative_control",
    feature="level",
    window_lookback_days=ANCHOR_WINDOW_LOOKBACK_DAYS,
    book_spec=ANCHOR_BOOK,
    direction_statement=(
        "identical tercile machinery on the elite HEADCOUNT level alone: "
        "short top tercile (most elite-long), long bottom tercile (most "
        "elite-short); never promotable"
    ),
)

ARM_SPECS: Dict[str, ArmSpec] = {
    ANCHOR_SPEC.arm_id: ANCHOR_SPEC,
    NEIGHBOR_SPEC.arm_id: NEIGHBOR_SPEC,
    CONTROL_SPEC.arm_id: CONTROL_SPEC,
}


def arm_spec(arm_id: str) -> ArmSpec:
    try:
        return ARM_SPECS[str(arm_id)]
    except KeyError:
        raise KeyError(
            f"unknown arm_id {arm_id!r}; frozen arms are {tuple(ARM_SPECS)}"
        ) from None


def arm_ids() -> Tuple[str, ...]:
    return tuple(ARM_SPECS)


__all__ = [
    "ANCHOR_SPEC",
    "ARM_SPECS",
    "ArmSpec",
    "CONTROL_SPEC",
    "NEIGHBOR_SPEC",
    "arm_ids",
    "arm_spec",
]
