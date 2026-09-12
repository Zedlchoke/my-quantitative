"""VOL-NG1: first-ever `vol` asset family (P0 data authority lane).

Plan: ``plans/PLAN_vol_ng1.md`` (section 3).  Information source: the
OFFICIAL CBOE volatility-index term structure (VIX9D/VIX/VIX3M, +VIX6M
census) and EODHD family-1 daily EOD for US volatility ETP legs, plus
the EODHD US delisted channel for the dead inverse-vol proof.

Modules:
- ``ingest``       bounded network pulls (keyless CBOE + keyed EODHD),
                   sha-pinned manifests; the EODHD key is loaded
                   programmatically from the gitignored root ``.env``
                   and NEVER echoed (V13 law);
- ``census``       fail-closed parsers + the frozen-floor measurements
                   (common term-structure coverage, living ETP legs,
                   delisted-channel proof) and the P-7 canaries;
- ``plane_adapter`` platform-v3 adoption: cycle-scoped authority
                   registry + CADS store + ``consume_via_plane`` +
                   bounded shadow-parity pilot (plane read vs raw
                   bytes, digest equality).
"""

#: Cycle identity (plan header).
CYCLE_ID = "VOL-NG1"

#: Frozen per-asset consumption-set schema (plan section 3).
SCHEMA = "vol_ng1/plane_adapter@1"
