"""V12P A4 -- pre-score feasibility layer (schedule-only diagnostics).

This package computes NO PnL, no returns and no scored metric of any kind.
It contains:

* :mod:`research.v12.feasibility` -- the pre-score target-book validator
  (fail-closed, per-stamp reason codes) and schedule-only diagnostics;
* :mod:`research.v12.oilev_v2_book` -- the fixed OILEV-V2 diversified book
  (>=9 eligible, 4 lowest / 4 highest, equal weight per leg, frozen BTC
  beta-hedge context semantics, uniform whole-book scale to the frozen 0.30
  adapter cap; the cap holds by construction);
* :mod:`research.v12.oilev_v2_spec` -- the OILEV-V2 schedule/spec draft
  (PLAN_crypto.md section 8.2 identity; the ranking feature itself is
  injected and remains frozen by the A1 brief, not here).
"""

from research.v12.feasibility import (
    REASON_DUPLICATE_SYMBOL,
    REASON_EMPTY_BOOK,
    REASON_LEG_COUNT_MISMATCH,
    REASON_OK,
    REASON_WEIGHT_ABOVE_CAP,
    REASON_WEIGHT_NOT_FINITE,
    schedule_diagnostics,
    validate_stamp_schedule,
    validate_target_book,
)
from research.v12.oilev_v2_book import (
    BENCHMARK_SYMBOL,
    BETA_HEDGE_SEMANTICS,
    CAP_MAX,
    LEG_NAMES,
    MIN_ELIGIBLE,
    EligibilityShortfall,
    build_oilev_v2_book,
)
from research.v12.oilev_v2_spec import OILEV_V2_ARMS, oilev_v2_spec_payload, stamp_calendar

__all__ = [
    "BENCHMARK_SYMBOL",
    "BETA_HEDGE_SEMANTICS",
    "CAP_MAX",
    "EligibilityShortfall",
    "LEG_NAMES",
    "MIN_ELIGIBLE",
    "OILEV_V2_ARMS",
    "REASON_DUPLICATE_SYMBOL",
    "REASON_EMPTY_BOOK",
    "REASON_LEG_COUNT_MISMATCH",
    "REASON_OK",
    "REASON_WEIGHT_ABOVE_CAP",
    "REASON_WEIGHT_NOT_FINITE",
    "build_oilev_v2_book",
    "oilev_v2_spec_payload",
    "schedule_diagnostics",
    "stamp_calendar",
    "validate_stamp_schedule",
    "validate_target_book",
]
