"""FOREX-FREE-V4 family-module package.

Implements the SELECTED, FROZEN proposals of the D1 A6 lane against the
inherited V3 kernel architecture (family API contract of
:mod:`research.assets.forex_free_v3.scored_runner`):

* ``family1`` -- FXFV4-A6-P1 commodity-bloc risk-off event basket
  (research/proposals/forex_free_v4/d1-a6-proposals/PROPOSAL_FXFV4-A6-P1.json).
* ``family2`` -- FXFV4-A6-P2 policy-change underreaction drift
  (research/proposals/forex_free_v4/d1-a6-proposals/PROPOSAL_FXFV4-A6-P2.json).

Factory-only namespace mirroring the inherited V3 family-module discovery
pattern (``research/assets/forex_free_v3/exec_driver.py``: families are
registered as ``family_id=module.path`` and must expose
``run_arm(arm, data_paths, macro_reader, freeze_token)``).  No V3 frozen
file is modified; the V3 kernel (research/assets/forex_free_v3/accounting.py,
the inherited P1 accounting kernel) is imported READ-ONLY for booking.

Factory-only lanes: synthetic fixtures in tests, no scored PnL on real data,
no network, no new data authority.
"""
