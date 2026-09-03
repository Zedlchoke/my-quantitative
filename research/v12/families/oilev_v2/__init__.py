"""V12 I lane -- frozen OILEV-V2 family package (A12-V12-OILEVER-V2-DELEV).

Modules:

* :mod:`research.v12.families.oilev_v2.strategy` -- frozen identity + the
  PIT OI-flow/OI-stock feature definitions inherited UNCHANGED from the V11
  OILEV strategy, feeding the frozen diversified book;
* :mod:`research.v12.families.oilev_v2.plugin` -- the GenericStrategyBase
  adapter plugin (one instance per frozen arm);
* :mod:`research.v12.families.oilev_v2.audits` -- read-only evidence
  builders (PIT field verification, funding-events-while-held resolution,
  52-stamp schedule feasibility, double-generation determinism, drop-one
  diagnostic, exact-arm dummy dry-run).

No module here computes a scored PnL on real data.
"""

from research.v12.families.oilev_v2.strategy import (
    ANCHOR_ARM,
    ARM_IDS,
    ARM_ROLES,
    BENCHMARK_SYMBOL,
    CONTROL_ARM,
    FAMILY_ID,
    NEIGHBOUR_ARM,
    STRATEGY_ID,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    compute_targets_at,
    frozen_arm_config,
    frozen_identity,
    frozen_arm_digest_report,
    signal_scores_at,
)

__all__ = [
    "ANCHOR_ARM",
    "ARM_IDS",
    "ARM_ROLES",
    "BENCHMARK_SYMBOL",
    "CONTROL_ARM",
    "FAMILY_ID",
    "NEIGHBOUR_ARM",
    "STRATEGY_ID",
    "WINDOW_END_ISO",
    "WINDOW_START_ISO",
    "compute_targets_at",
    "frozen_arm_config",
    "frozen_arm_digest_report",
    "frozen_identity",
    "signal_scores_at",
]
