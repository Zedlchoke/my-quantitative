"""CRYPTO V15 implementation-lane family packages (Phase V15-I).

One subpackage per selected family per
``research/control/v15_run/selection_freeze_v15.json``: family
``A5-V15-F1-ELITE-SIZE-ASYM`` (AXIS-2 crowding ratios) lives in
``research.v15.families.elite_size_asym``.

``research/v15/families`` is an implicit (PEP 420) namespace package on
purpose: the A8-I lane's allowed write paths cover ``research/v15/__init__.py``
and ``research/v15/families/elite_size_asym/**`` only, so no ``__init__.py``
is created at the ``families`` level.  Python 3 resolves the namespace
portion transparently; the V14 precedent (regular ``families`` package) is
functionally equivalent for imports.

No scored metric exists for any V15 cell; nothing in this package computes
PnL on real data (the lane's obligation), and no module here mutates any
frozen control artifact under ``research/control/v15_run/``.
"""
