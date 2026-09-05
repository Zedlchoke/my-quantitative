"""FOREX-FREE-V4 family package (cycle FOREX-FREE-V4).

Implements the SELECTED, FROZEN proposals of the D1 A6 lane against the
inherited V3 kernel architecture (family API contract of
:mod:`research.assets.forex_free_v3.scored_runner`):

* ``family1`` -- FXFV4-A6-P1 commodity-bloc risk-off event basket
  (research/proposals/forex_free_v4/d1-a6-proposals/PROPOSAL_FXFV4-A6-P1.json,
  sha256 e827c904183c13e503441bd252004963027d03c792e7e6ca2c5a7fc65ee7eb0c).

Factory-only lane: synthetic fixtures in tests, no scored PnL on real data,
no network, no new data authority.  The V3 frozen files are never modified;
a V4 family module is registered with the runner exactly the way V3 family
modules are (exec_driver ``--family family1=research.assets.forex_free_v4.family1``).
"""
