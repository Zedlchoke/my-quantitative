"""STOCKS-FREE-V3 zero-cost data, S0/S1 isolation and benchmark authority.

Owner: lane A3 (PLAN_stocks.md section 9, deliverable block ``A3``).

This package re-authorizes, WITHOUT any network fetch and WITHOUT touching the
sealed S1, the frozen zero-cost stack inherited from STOCKS-FREE-V2:

* :mod:`research.stocks_free_v3.authority` — sha256 revalidation of the V2
  staged snapshot against the committed pins (transcribed from the V2 control
  artifact ``w1_freeze.json``) and revalidation of the license/terms evidence
  by READING the V2 control artifacts (never by re-fetching terms);
* :mod:`research.stocks_free_v3.isolation` — S1 seal (path-level and
  date-level denial, in the style of the V2 harness ``s1_denied``) plus the
  sealed S0-only snapshot reader used by every V3 consumer;
* :mod:`research.stocks_free_v3.cohort` — the 11-ETF cohort verification:
  raw OHLCV schema, corporate-action inputs (five 2025-12-05 2:1 sector-ETF
  splits + issuer distribution records), issuer total-return reconstruction
  inputs and the regular-session calendar;
* :mod:`research.stocks_free_v3.benchmarks` — the four frozen benchmark
  series builders (flat, SPY total return, equal-weight sector total return,
  risk-matched SPY context scaled EX ANTE by an arm's frozen gross/vol rule);
  deterministic semantics only, never scored runs;
* :mod:`research.stocks_free_v3.incremental` — the incremental mechanism
  alpha metric (after-cost strategy return minus the risk-matched benchmark,
  per fold) and the falsification contract fields;
* :mod:`research.stocks_free_v3.data_policy` — the unavailable-data
  whitelist: V3 families may require only daily OHLCV, volume, split factors,
  distributions and the calendar; anything else is rejected at
  config-validation time.

The snapshot itself stays OUTSIDE this repository (V2 staging, referenced by
absolute path); raw payloads are never copied into git.  S1
(2025-08-01..2026-07-31) is SEALED: no module here returns or accepts an
S1-dated observation.
"""

from research.stocks_free_v3.authority import (
    CALENDAR_DIGEST,
    COHORT_DIGEST,
    COHORT_SYMBOLS,
    EXCLUDED_SYMBOLS,
    ISSUER_DISTRIBUTION_RECORDS_SHA256,
    PARTITION_DIGEST,
    S0_END,
    S0_START,
    S1_END,
    S1_START,
    SNAPSHOT_PINS,
    SNAPSHOT_STAGING_PATH,
    WARMUP_END,
    WARMUP_START,
    verify_snapshot_pins,
)
from research.stocks_free_v3.isolation import S0WindowPolicy, S1Seal, SealedSnapshotReader

__all__ = [
    "CALENDAR_DIGEST",
    "COHORT_DIGEST",
    "COHORT_SYMBOLS",
    "EXCLUDED_SYMBOLS",
    "ISSUER_DISTRIBUTION_RECORDS_SHA256",
    "PARTITION_DIGEST",
    "S0_END",
    "S0_START",
    "S1_END",
    "S1_START",
    "SNAPSHOT_PINS",
    "SNAPSHOT_STAGING_PATH",
    "WARMUP_END",
    "WARMUP_START",
    "S0WindowPolicy",
    "S1Seal",
    "SealedSnapshotReader",
    "verify_snapshot_pins",
]
