"""Family SFV4-A5-H1-PARTICIPATION-SHIFT (V4-I lane A8).

Relative dollar-volume participation-shift premium over the frozen 11 sector
ETF cohort: 63-session anchored decision clock, long top-3 / short bottom-3 by
21d-vs-252d dollar-volume shock ratio (+-1/6 legs, gross 1.0 net 0.0), 63-session
holding, next-allowed-session fills, force-flat at fold boundaries.

Arms (selection_freeze.json selected_families[0]):

* ``SFV4-A5-H1-A`` anchor;
* ``SFV4-A5-H1-N`` neighbour (63-session numerator);
* ``SFV4-A5-H1-C`` causal negative control (one-quarter-stale ranks).

This lane produces SCHEDULE-ONLY real-data evidence: no scored PnL, no
backtest of returns on real data, zero scored metrics.
"""

from research.stocks_free_v4.family_participation.config import (
    ANCHOR_SESSION,
    ARM_KEY_ANCHOR,
    ARM_KEY_CONTROL,
    ARM_KEY_NEIGHBOUR,
    FAMILY_ID,
    FAMILY_SCHEMA,
    FOLDS,
    SHOCK_WINDOWS,
    ArmConfig,
    ArmConfigError,
    build_arm_configs,
)
from research.stocks_free_v4.family_participation.features import (
    build_targets,
    cross_sectional_shocks,
    decide_at,
    dollar_volume,
    eligibility,
    ew_sector_factor,
    rank_by_shock_desc,
    rebuild_targets_excluding,
    risk_matched_context,
    shock_ratio,
)
from research.stocks_free_v4.family_participation.schedule import (
    ArmSchedule,
    build_arm_schedule_blockwise,
    build_arm_schedule_walk,
    schedule_feasibility,
    schedules_equal,
)

__all__ = [
    "ANCHOR_SESSION",
    "ARM_KEY_ANCHOR",
    "ARM_KEY_CONTROL",
    "ARM_KEY_NEIGHBOUR",
    "ArmConfig",
    "ArmConfigError",
    "ArmSchedule",
    "FAMILY_ID",
    "FAMILY_SCHEMA",
    "FOLDS",
    "SHOCK_WINDOWS",
    "build_arm_configs",
    "build_arm_schedule_blockwise",
    "build_arm_schedule_walk",
    "build_targets",
    "cross_sectional_shocks",
    "decide_at",
    "dollar_volume",
    "eligibility",
    "ew_sector_factor",
    "rank_by_shock_desc",
    "rebuild_targets_excluding",
    "risk_matched_context",
    "schedule_feasibility",
    "schedules_equal",
    "shock_ratio",
]
