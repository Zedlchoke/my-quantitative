"""V11-SEED-LOTTERY-MAX-SKEW family implementation (I-family-1).

Frozen selection-freeze contract:
``research/control/v11_run/selection_freeze_specs/V11-SEED-LOTTERY-MAX-SKEW.json``.

The package contains only family-owned code: pure feature/schedule
computation (:mod:`research.v11.families.lottery_max_skew.strategy`), the
adapter plugin (:mod:`research.v11.families.lottery_max_skew.plugin`) and
read-only staged-data loaders
(:mod:`research.v11.families.lottery_max_skew.data`).  All shared adapter,
publication, cost-gate and dry-run primitives are imported from their frozen
modules; nothing here forks them.
"""

from research.v11.families.lottery_max_skew.plugin import (
    ARM_IDS,
    ANCHOR_ARM,
    BENCHMARK_EXCLUDED,
    CONTROL_ARM,
    FAMILY_ID,
    NEIGHBOUR_ARM,
    LotteryMaxSkewPlugin,
    build_arm_plugin,
    frozen_identity,
)

__all__ = [
    "ANCHOR_ARM",
    "ARM_IDS",
    "BENCHMARK_EXCLUDED",
    "CONTROL_ARM",
    "FAMILY_ID",
    "NEIGHBOUR_ARM",
    "LotteryMaxSkewPlugin",
    "build_arm_plugin",
    "frozen_identity",
]
