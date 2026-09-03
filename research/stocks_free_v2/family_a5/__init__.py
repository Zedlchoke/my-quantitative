"""A5-SFV2-TREND-DEFENSIVE — frozen trend/defensive ETF family (Z5 lane).

Schedule-only implementation of the three preregistered arms in
``research/proposals/stocks_free_v2/a5_family_manifest.json``:

* ``A5-SFV2-ARM1-TSM12-VOLTARGET`` — literature-backed anchor (252-session
  TSMOM sign gate, monthly clock).
* ``A5-SFV2-ARM2-SMA200-WEEKLY`` — theoretically justified neighbour
  (200-session SMA filter, weekly clock).
* ``A5-SFV2-ARM3-TSM12-INVERTED-CONTROL`` — causal negative control (exact
  sign inversion of the anchor, monthly clock).

This lane computes decision/target books and schedule diagnostics ONLY:
no returns, PnL, profit factor, Sharpe, ranking or scored artifact of any arm
exists here (outcome-blind contract; budget stays with Z8).

Modules:
* ``signals``  — frozen feature gates + realized-vol estimator (pure).
* ``portfolio`` — deterministic vol-target-to-cash weight mapping (pure).
* ``schedule`` — frozen arm configs, clocks, fold/terminal handling,
  target-book generation and schedule summaries.
"""

from research.stocks_free_v2.family_a5.portfolio import (  # noqa: F401
    CASH_SYMBOL,
    PER_ETF_CAP,
    TARGET_VOL_ANNUAL,
    base_equal_weights,
    book_gross,
    defensive_target_weights,
    gross_scalar,
    two_way_turnover,
)
from research.stocks_free_v2.family_a5.schedule import (  # noqa: F401
    ARM_CONFIGS,
    ARM_CONFIG_ANCHOR,
    ARM_CONFIG_CONTROL,
    ARM_CONFIG_NEIGHBOUR,
    ArmConfig,
    ArmScheduleResult,
    COHORT_SYMBOLS,
    FAMILY_ID,
    FoldScheduleSummary,
    FoldWindow,
    SPEC_FILE_SHA256,
    TURNOVER_CEILING_TWO_WAY_ANNUAL,
    TargetBook,
    arm_config_digest,
    control_is_pure_sign_mutation,
    decision_dates_for,
    decision_dates_monthly,
    decision_dates_weekly,
    generate_arm_schedule,
)

__all__ = [
    "ARM_CONFIGS",
    "ARM_CONFIG_ANCHOR",
    "ARM_CONFIG_CONTROL",
    "ARM_CONFIG_NEIGHBOUR",
    "ArmConfig",
    "ArmScheduleResult",
    "CASH_SYMBOL",
    "COHORT_SYMBOLS",
    "FAMILY_ID",
    "FoldScheduleSummary",
    "FoldWindow",
    "PER_ETF_CAP",
    "SPEC_FILE_SHA256",
    "TURNOVER_CEILING_TWO_WAY_ANNUAL",
    "TARGET_VOL_ANNUAL",
    "TargetBook",
    "arm_config_digest",
    "base_equal_weights",
    "book_gross",
    "control_is_pure_sign_mutation",
    "decision_dates_for",
    "decision_dates_monthly",
    "decision_dates_weekly",
    "defensive_target_weights",
    "generate_arm_schedule",
    "gross_scalar",
    "two_way_turnover",
]
