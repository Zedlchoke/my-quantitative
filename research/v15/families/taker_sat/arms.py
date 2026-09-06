"""Frozen arm registry for TAKER-SAT (exactly the three selected arms).

The arm ids are the SELECTION-FREEZE names (binding);
``PROPOSAL_ARM_IDS`` records the proposal-internal ids for provenance.
The causal control ``A6-F1-CTL-RAWSAT`` is the anchor's pipeline with the
positioning-churn denominator DELETED: the same window, ranking, weights,
rules and costs on the raw daily aggression intensity ``A_bar``.  It is
structurally distinct from the anchor BY CONSTRUCTION (no OI input at all),
which is exactly what makes it able to kill the flow-reversal relabel
explanation.
"""

from __future__ import annotations

from typing import Any, Mapping

from research.adapter_v10.protocol import ContractViolation
from research.v15.families.taker_sat.frozen_identity import (
    ANCHOR_ARM,
    ARM_IDS,
    ARM_ROLES,
    CONTROL_ARM,
    NEIGHBOUR_ARM,
    PROPOSAL_ARM_IDS,
    WINDOW_DAYS_ANCHOR,
    WINDOW_DAYS_NEIGHBOUR,
)

#: arm id -> frozen evaluation spec.
#:   ``window_days``  -- n of the lookback window W = [D-3-(n-1), D-3];
#:   ``with_churn``   -- whether the OI-churn denominator is consumed;
#:   ``feature``      -- frozen feature expression (identity payload echo).
ARM_SPECS: dict[str, dict[str, Any]] = {
    ANCHOR_ARM: {
        "role": ARM_ROLES[ANCHOR_ARM],
        "window_days": WINDOW_DAYS_ANCHOR,
        "with_churn": True,
        "feature": "S = A_bar / (O + 0.02), W = [D-12, D-3]",
        "proposal_arm_id": PROPOSAL_ARM_IDS[ANCHOR_ARM],
    },
    NEIGHBOUR_ARM: {
        "role": ARM_ROLES[NEIGHBOUR_ARM],
        "window_days": WINDOW_DAYS_NEIGHBOUR,
        "with_churn": True,
        "feature": "S = A_bar / (O + 0.02), W = 21 daily aggregates [D-23, D-3]",
        "proposal_arm_id": PROPOSAL_ARM_IDS[NEIGHBOUR_ARM],
    },
    CONTROL_ARM: {
        "role": ARM_ROLES[CONTROL_ARM],
        "window_days": WINDOW_DAYS_ANCHOR,
        "with_churn": False,
        "feature": "raw A_bar (NO positioning-churn denominator), W = [D-12, D-3]",
        "proposal_arm_id": PROPOSAL_ARM_IDS[CONTROL_ARM],
    },
}


def arm_spec(arm_id: str) -> dict[str, Any]:
    """The frozen evaluation spec of one arm (fail-closed on unknown ids)."""
    arm_id = str(arm_id)
    if arm_id not in ARM_SPECS:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    return dict(ARM_SPECS[arm_id])


def is_control_arm(arm_id: str) -> bool:
    return str(arm_id) == CONTROL_ARM


def arm_ids() -> tuple[str, ...]:
    """The three frozen arm ids (sorted, deterministic)."""
    return tuple(sorted(ARM_IDS))


def spec_digest_inputs() -> Mapping[str, Mapping[str, Any]]:
    """All three arm specs (for preflight/audit payloads)."""
    return {arm: arm_spec(arm) for arm in arm_ids()}


__all__ = [
    "ARM_SPECS",
    "arm_ids",
    "arm_spec",
    "is_control_arm",
    "spec_digest_inputs",
]
