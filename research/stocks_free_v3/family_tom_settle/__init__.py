"""Family SFV3-A6-TOM-SETTLE: turn-of-month settlement-flow seasonality.

Owner: lane A9 (implementer of ``selection_freeze.json`` families[1]),
STOCKS-FREE-V3.  Mechanism source:
``research/proposals/stocks_free_v3/a6_family_SFV3-A6-TOM-SETTLE.md``
(Ogden 1990 turn-of-month settlement liquidity; Lakonishok & Smidt 1988;
Lakonishok, Shleifer, Thaler & Vishny 1991 window dressing).

What lives here (SCHEDULE AND CONFIGURATION ONLY — no data access, no disk
writes, no network, and NO PnL / scored metric of any kind):

* :mod:`.config` — the three frozen arm heads A/N/C (window rules, the two
  frozen books TOM gross 0.50 / BASE gross 0.30 with the explicit CASH
  residual leg, canonical close-fill clock T -> T+1, shared costs, the frozen
  ex-ante risk-matched rule) with complete sha256 config digests;
* :mod:`.schedule` — regular-session month ordinals, per-arm window
  membership, deterministic target-book emission as
  ``(fill_session, targets_with_explicit_CASH, turnover_one_way)`` via two
  independent code paths that must agree byte-identically, and schedule-only
  feasibility (24 transitions and 4.80 two-way per complete calendar year,
  gross envelope [0.30, 0.50]) reported WITHOUT computing any PnL;
* :mod:`.dryrun` — the exact-arm dry run: schedule build (double generation)
  + canonical ``factory.value_book`` accounting + the ``GatedTrialLedger``
  publication gate on a CALLER-OWNED temporary ledger; valuation numbers are
  consumed internally by the reconciliation assert and never returned,
  printed, or persisted.

The frozen window rules (regular-session month ordinals, never calendar
dates): anchor = last 3 sessions of month M + first 2 of M+1; neighbour =
first 3 of month M; causal negative control = ordinals 8-12 of each month
(disjoint from the anchor window for every month length >= 15; real US months
have 19-23 sessions).
"""

from research.stocks_free_v3.family_tom_settle.config import (
    ARM_KEY_ANCHOR,
    ARM_KEY_CONTROL,
    ARM_KEY_NEIGHBOUR,
    BASE_COST_BPS,
    BASE_GROSS,
    BOOK_BASE,
    BOOK_TOM,
    DECISION_LAG_SESSIONS,
    EXPECTED_TRANSITIONS_PER_YEAR,
    EXPECTED_TWO_WAY_TURNOVER_PER_YEAR,
    FAMILY_ID,
    FAMILY_SCHEMA,
    FROZEN_VOL_SCALING_RULE,
    MIN_MONTH_SESSIONS,
    MIN_MONTH_SESSIONS_ANCHOR_CONTROL_DISJOINT,
    STRESS_COST_BPS,
    TOM_GROSS,
    TURNOVER_CEILING_TWO_WAY_PER_YEAR,
    WINDOW_RULES,
    ArmConfig,
    ArmConfigError,
    WindowRule,
    arm_config_digests,
    build_arm_configs,
)
from research.stocks_free_v3.family_tom_settle.schedule import (
    ArmSchedule,
    ScheduleError,
    ScheduledFill,
    SessionOrdinal,
    anchor_control_disjoint,
    assert_anchor_control_disjoint,
    base_targets,
    build_schedule,
    build_schedule_from_windows,
    complete_calendar_years,
    is_window_session,
    month_ordinals,
    schedule_feasibility,
    schedules_equal,
    sessions_by_month,
    tom_targets,
    year_turnover,
)
from research.stocks_free_v3.family_tom_settle.dryrun import (
    DryRunError,
    DryRunReport,
    run_exact_arm_dry_run,
    schedule_book_entries,
)

__all__ = [
    "ARM_KEY_ANCHOR",
    "ARM_KEY_CONTROL",
    "ARM_KEY_NEIGHBOUR",
    "ArmConfig",
    "ArmConfigError",
    "ArmSchedule",
    "BASE_COST_BPS",
    "BASE_GROSS",
    "BOOK_BASE",
    "BOOK_TOM",
    "DECISION_LAG_SESSIONS",
    "DryRunError",
    "DryRunReport",
    "EXPECTED_TRANSITIONS_PER_YEAR",
    "EXPECTED_TWO_WAY_TURNOVER_PER_YEAR",
    "FAMILY_ID",
    "FAMILY_SCHEMA",
    "FROZEN_VOL_SCALING_RULE",
    "MIN_MONTH_SESSIONS",
    "MIN_MONTH_SESSIONS_ANCHOR_CONTROL_DISJOINT",
    "ScheduledFill",
    "SessionOrdinal",
    "STRESS_COST_BPS",
    "TOM_GROSS",
    "TURNOVER_CEILING_TWO_WAY_PER_YEAR",
    "WindowRule",
    "WINDOW_RULES",
    "anchor_control_disjoint",
    "arm_config_digests",
    "assert_anchor_control_disjoint",
    "base_targets",
    "build_arm_configs",
    "build_schedule",
    "build_schedule_from_windows",
    "complete_calendar_years",
    "is_window_session",
    "month_ordinals",
    "run_exact_arm_dry_run",
    "schedule_book_entries",
    "schedule_feasibility",
    "ScheduleError",
    "schedules_equal",
    "sessions_by_month",
    "tom_targets",
    "year_turnover",
]
