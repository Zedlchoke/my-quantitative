# Verify the next data snapshot and split contract

**Type:** task  
**Status:** closed  
**Blocked by:** none

## Question

Is the next dataset complete and clean enough that a new result is genuinely
out-of-sample rather than a catalog or precision artifact?

## Decision needed

Lock the snapshot date, symbol universe, bar interval, history gate, funding/OI/
mark-price coverage, TradFi schedule coverage, and train/validation/holdout
boundaries before running any candidate.

## Evidence to collect

- Parquet row counts, duplicate/gap checks, instrument precision and delisting
  checks for every symbol.
- Funding settlement coverage spanning every position window.
- BTC, basis, OI, mark/index and liquidation-proxy timestamps aligned to bars.

## Resolution

The local snapshot audit is recorded in
[data-snapshot-20260822.md](../evidence/data-snapshot-20260822.md).

- The seven crypto bar series pass OHLC/positive-volume checks, have no duplicate
  timestamps or non-15-minute gaps, and share 35,038 exact timestamps.
- The valid cross-symbol window is therefore the common one-year interval
  `2025-08-21T14:29:59.999Z` through `2026-08-21T13:44:59.999Z`. The additional
  altcoin year is archive/warmup only; it cannot support a two-year multi-asset
  claim while ETH has only one year.
- Funding bundles cover all seven symbols. OI and mark-price overlays now cover
  all seven symbols after the follow-up ETH capture documented in
  `capture-eth-derivatives-snapshot.md`.
- S0 is frozen as screening data: train is the first six months and validation
  is the following roughly three months. The remainder is historical context,
  not untouched OOS, because existing baseline work inspected the full common
  window. Promotion requires a newly captured S1 after parameter lock, with no
  overlap and complete funding coverage.

**Decision:** close this audit as a reproducible S0 contract, but keep promotion
blocked until the future S1 holdout task is complete. OI/mark interval-open
timestamps must be mapped to completed bar-close timestamps with a deterministic
one-bar-lag rule before they can enter features.
