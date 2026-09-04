"""Family module SFV4-A4-H1-SEMIVARIANCE-SHARE (STOCKS-FREE-V4 family 2, A9).

Downside-vs-total semivariance-share risk pricing, market-neutral shape
spread.  Implements the frozen contract in
``research/control/stocks_free_v4_run/selection_freeze.json``
(selected_families[1]) from the proposal
``research/control/stocks_free_v4_run/proposals/a4_h1.json`` and the frozen
conventions in ``research/control/stocks_free_v4_run/baseline_invariants.json``.

Submodules (config / signals / schedule, mirroring the V3 family pattern):

* :mod:`research.stocks_free_v4.family_semivar.config` — frozen constants and
  the three digest-pinned arm heads (anchor / neighbour / control) with the
  frozen ex-ante kappa fallback;
* :mod:`research.stocks_free_v4.family_semivar.signals` — pure, synthetic-
  testable mechanics: semivariance-share and variance-level statistics,
  lexicographic-tie ranking, the hysteresis book automaton, target weights,
  the frozen kappa fallback rule and the equal-weight sector factor;
* :mod:`research.stocks_free_v4.family_semivar.schedule` — the byte-exact
  anchored 21-session decision clock, next-session fill mapping, per-fold
  force-flat, double-generation schedule builders, and the SCHEDULE-ONLY
  (dates/counts, zero returns) real-calendar feasibility entry point.

HARD RULE of this lane: real-data runs are schedule-only.  No scored PnL, no
backtest of returns on real data; dummy/synthetic finite metrics are allowed
only with scored=false and real_pnl=false.
"""

from research.stocks_free_v4.family_semivar.config import (
    ARM_KEY_ANCHOR,
    ARM_KEY_CONTROL,
    ARM_KEY_NEIGHBOUR,
    FAMILY_ID,
    FAMILY_SCHEMA,
    FOLDS,
    SECTOR_SYMBOLS,
    ArmConfig,
    ArmConfigError,
    arm_config_digests,
    build_arm_configs,
)
from research.stocks_free_v4.family_semivar.schedule import (
    ArmSchedule,
    ScheduleError,
    ScheduledFill,
    build_arm_schedule,
    build_arm_schedule_by_folds,
    clock_anchor_index,
    decision_indices,
    fold_of,
    fold_sessions,
    next_session,
    schedule_only_feasibility,
    schedules_equal,
)
from research.stocks_free_v4.family_semivar.signals import (
    SignalError,
    eligibility,
    ew_sector_return,
    feature_value,
    kappa_frozen,
    rank_symbols,
    seed_book,
    semivariance_share,
    step_book,
    target_weights,
    total_sum_sq,
)

__all__ = [
    "ARM_KEY_ANCHOR",
    "ARM_KEY_CONTROL",
    "ARM_KEY_NEIGHBOUR",
    "FAMILY_ID",
    "FAMILY_SCHEMA",
    "FOLDS",
    "SECTOR_SYMBOLS",
    "ArmConfig",
    "ArmConfigError",
    "ArmSchedule",
    "ScheduleError",
    "ScheduledFill",
    "SignalError",
    "arm_config_digests",
    "build_arm_configs",
    "build_arm_schedule",
    "build_arm_schedule_by_folds",
    "clock_anchor_index",
    "decision_indices",
    "eligibility",
    "ew_sector_return",
    "feature_value",
    "fold_of",
    "fold_sessions",
    "kappa_frozen",
    "next_session",
    "rank_symbols",
    "schedule_only_feasibility",
    "schedules_equal",
    "seed_book",
    "semivariance_share",
    "step_book",
    "target_weights",
    "total_sum_sq",
]
