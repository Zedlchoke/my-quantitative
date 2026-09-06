"""Frozen TAKER-SAT family (A6-V15-F1-TAKER-SAT, AXIS-3 aggression saturation).

Implementation-lane package for the selected V15 family.  Every constant is
quoted from the frozen authorities (see ``frozen_identity.py``); the public
surface is the frozen identity + digests, the feature primitives, the book
and schedule machinery, the refusal registry and ``runner.run_arm``.
"""

from research.v15.families.taker_sat.frozen_identity import (
    ANCHOR_ARM,
    ARM_IDS,
    ARM_ROLES,
    CONTROL_ARM,
    FAMILY_ID,
    NEIGHBOUR_ARM,
    UNIVERSE,
    frozen_arm_digest_report,
    frozen_identity,
)

__all__ = [
    "ANCHOR_ARM",
    "ARM_IDS",
    "ARM_ROLES",
    "CONTROL_ARM",
    "FAMILY_ID",
    "NEIGHBOUR_ARM",
    "UNIVERSE",
    "frozen_arm_digest_report",
    "frozen_identity",
]
