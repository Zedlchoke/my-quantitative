"""FOREX-FREE-V4 family-module package.

Factory-only namespace mirroring the inherited V3 family-module discovery
pattern (``research/assets/forex_free_v3/exec_driver.py``: families are
registered as ``family_id=module.path`` and must expose
``run_arm(arm, data_paths, macro_reader, freeze_token)``).  No V3 frozen
file is modified; the V3 kernel (research/assets/forex_free_v3/accounting.py,
the inherited P1 accounting kernel) is imported READ-ONLY for booking.
"""
