"""V13 I lane -- frozen OITD family package (A13-V13-A8-OITD).

Modules:

* :mod:`research.v13.families.oitd.strategy` -- frozen identity (per-arm
  ``arm_config_digest``), the PIT unwind-duration signal (fusion
  availability semantics), the preregistered causal-control gate and the
  PINNED next-allowed-fill convention (A9-F engine pin);
* :mod:`research.v13.families.oitd.book` -- the frozen hysteresis tercile
  book builder and the drop-one design;
* :mod:`research.v13.families.oitd.plugin` -- the GenericStrategyBase
  adapter plugin (one instance per frozen arm);
* :mod:`research.v13.families.oitd.audits` -- read-only evidence builders
  (identity, schedule-only feasibility on the real snapshot, drop-one,
  dummy publication dry-run into a temporary ledger).

No module here computes a scored PnL on real data.
"""

from research.v13.families.oitd.book import (
    EligibilityShortfall,
    build_hysteresis_book,
    drop_one_book,
    held_max_abs_weight_symbol,
)
from research.v13.families.oitd.strategy import (
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
    evaluate_control_gate,
    frozen_arm_config,
    frozen_arm_digest_report,
    frozen_identity,
    next_allowed_fill,
    signal_scores_at,
    stamp_calendar,
)

__all__ = [
    "ANCHOR_ARM",
    "ARM_IDS",
    "ARM_ROLES",
    "BENCHMARK_SYMBOL",
    "CONTROL_ARM",
    "EligibilityShortfall",
    "FAMILY_ID",
    "NEIGHBOUR_ARM",
    "STRATEGY_ID",
    "WINDOW_END_ISO",
    "WINDOW_START_ISO",
    "build_hysteresis_book",
    "compute_targets_at",
    "drop_one_book",
    "evaluate_control_gate",
    "frozen_arm_config",
    "frozen_arm_digest_report",
    "frozen_identity",
    "held_max_abs_weight_symbol",
    "next_allowed_fill",
    "signal_scores_at",
    "stamp_calendar",
]
