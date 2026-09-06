"""CRYPTO V15 implementation-lane family packages (Phase V15-I).

One subpackage per selected family per
``research/control/v15_run/selection_freeze_v15.json``: family
``A5-V15-F1-ELITE-SIZE-ASYM`` (AXIS-2 crowding ratios) lives in
``research.v15.families.elite_size_asym`` and family
``A6-V15-F1-TAKER-SAT`` (AXIS-3 taker flow ratio-of-ratio) in
``research.v15.families.taker_sat``.

The A8-I lane for family 1 left ``research/v15/families`` an implicit
(PEP 420) namespace package (its write paths did not cover that level);
the family-2 lane added a regular-package ``__init__.py`` here. Both
resolve identically for imports; the merged state is A1's semantic
resolution of the integration conflict (recorded in the pick commit).

No scored metric exists for any V15 cell; nothing in this package computes
PnL on real data (the lanes' obligation), and no module here mutates any
frozen control artifact under ``research/control/v15_run/``.
"""
