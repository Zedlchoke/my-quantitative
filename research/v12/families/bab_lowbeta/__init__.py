"""A12-V12-BAB-LOWBETA -- V12 blind family implementation (Phase I lane).

Selected proposal ``V12-A5-P1-BAB-LOWBETA`` (frozen contract
``research/control/v12_run/selection_freeze_specs/A12-V12-BAB-LOWBETA.json``):

* anchor   ``BAB-90D-W``          -- long the 4 lowest / short the 4 highest
  trailing 90-day daily BTC-beta eligible names, weekly Monday 00:00:00Z;
* neighbour``BAB-DOWNCORR-90D-W`` -- same book sorted on the trailing 90-day
  downside-correlation with BTC (BTC-down days only);
* control  ``BAB-90D-W-INV``      -- sign-inverted anchor (causal negative
  control: a positive after-cost spread destroys the mechanism).

This lane computes NO scored PnL on real data: synthetic fixtures and
schedule-only diagnostics only.
"""

from research.v12.families.bab_lowbeta.plugin import BabLowBetaPlugin
from research.v12.families.bab_lowbeta.strategy import (
    ARM_IDS,
    BENCHMARK_SYMBOL_EXCLUDED,
    FAMILY_ID,
    STRATEGY_ID,
    build_frozen_identity,
    frozen_arm_config_digest,
    frozen_arm_ids,
)

__all__ = [
    "ARM_IDS",
    "BENCHMARK_SYMBOL_EXCLUDED",
    "BabLowBetaPlugin",
    "FAMILY_ID",
    "STRATEGY_ID",
    "build_frozen_identity",
    "frozen_arm_config_digest",
    "frozen_arm_ids",
]
