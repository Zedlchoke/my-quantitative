"""RATES-NG1 asset family: US Treasury curve + auction-supply clocks.

First ``rates`` asset family in program history (cycle RATES-NG1,
registered 2026-09-12).  This package carries the P0 data-authority and
platform-v3 adoption layer only:

- ``plane_adapter``: the frozen ``consume_via_plane`` surface.  Every
  consumption goes through a sha256-pinned substrate manifest + the
  manifest-verified query plane; unknown entries, drifted bytes and
  non-granted platform authority are refused (fail-closed).
- ``substrate``: deterministic pullers + census builders for the frozen
  consumption set (plan section 3): Treasury.gov daily par-yield curve
  per-year CSVs 1990..2026, FRED granted-set re-pin, EODHD family-1 US
  Treasury ETP EOD census, TreasuryDirect TA_WS auction calendar.

LAW (plan RATES-NG1 section 3): nothing outside the frozen consumption
set is consumed; keys are loaded programmatically from the environment /
.env and NEVER echoed into any artifact, log or commit; a source that
fails after bounded retries is recorded fail-closed (BLOCKED evidence),
never fabricated.  Raw pulled bytes stay untracked under
``raw_substrate/`` (P-13 law: manifests pin the bytes, bytes are not
committed).  No signals, no scoring, no outcome numbers live here.
"""

RATES_NG1_RAW_GITIGNORE = """# Raw substrate bytes are machine-local (P-13: committed sha256
# manifests at research/control/rates_ng1_run/ pin every file; bytes are
# never committed).
raw_substrate/
"""
