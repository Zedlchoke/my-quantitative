"""A8-V11-ILLIQ-AMIHUD family package (V11 phase I, lane I-family-2).

Implements the FROZEN selection-freeze spec
``research/control/v11_run/selection_freeze_specs/A8-V11-ILLIQ-AMIHUD.json``
verbatim through the generic V10 adapter (``research.adapter_v10``).  No
adapter module is forked or edited; the family supplies only:

* :mod:`.strategy` -- frozen constants + PIT Amihud feature/book primitives;
* :mod:`.plugin`   -- :class:`IlliqAmihudPlugin` joining the family to the
  generic adapter through :class:`research.adapter_v10.base.GenericStrategyBase`;
* :mod:`.audits`   -- C1 field verification, A3 schedule-only cost gate and
  A4 exact-arm dry-run artifact builders (schedule/diagnostic artifacts only,
  never scored PnL).

Frozen identity digests (``research/control/v11_run/selection_freeze.json``):

* ``ILLIQ-AMIHUD-28D-W``     -> 76729187a8a94980c08c30ae741a1ae0dd0e4da3d682037012ed7c04016fa8e0
* ``ILLIQ-AMIHUD-56D-W``     -> 286cef34b8b520843608737e45f0a3175719dde5099724f33c299c14eaf44571
* ``ILLIQ-AMIHUD-28D-W-INV`` -> d4d32ed62153ae5c9cee69230fc35de92bed64fe560e80f1902cc90f505fc913
"""

from research.v11.families.illiq_amihud.plugin import IlliqAmihudPlugin
from research.v11.families.illiq_amihud.strategy import (
    ADVERSE_TICK_SLIP_FLOOR,
    ARMS,
    BENCHMARK_SYMBOL_EXCLUDED,
    DECISION_CLOCK_TEXT,
    FAMILY_ID,
    FOLD_F0_END_ISO,
    FOLD_F0_START_ISO,
    FOLD_F1_END_ISO,
    FOLD_F1_START_ISO,
    FOLD_F2_END_ISO,
    FOLD_F2_START_ISO,
    MIN_ELIGIBLE,
    QUINTILES,
    STRATEGY_ID,
    TAKER_FEE_FLOOR_BPS,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    build_frozen_identity,
    frozen_arm_config_digest,
    frozen_arm_ids,
)

__all__ = [
    "ADVERSE_TICK_SLIP_FLOOR",
    "ARMS",
    "BENCHMARK_SYMBOL_EXCLUDED",
    "DECISION_CLOCK_TEXT",
    "FAMILY_ID",
    "FOLD_F0_END_ISO",
    "FOLD_F0_START_ISO",
    "FOLD_F1_END_ISO",
    "FOLD_F1_START_ISO",
    "FOLD_F2_END_ISO",
    "FOLD_F2_START_ISO",
    "MIN_ELIGIBLE",
    "QUINTILES",
    "STRATEGY_ID",
    "TAKER_FEE_FLOOR_BPS",
    "WINDOW_END_ISO",
    "WINDOW_START_ISO",
    "IlliqAmihudPlugin",
    "build_frozen_identity",
    "frozen_arm_config_digest",
    "frozen_arm_ids",
]
