# Data snapshot evidence — 2026-08-22 review

This is a read-only audit of the local snapshot captured on 2026-08-21. It is
not a new OOS result.

## Bar catalog

Catalog: `catalog_live_crypto`; interval: Binance USD-M 15-minute bars.

| Symbol | Rows | First event | Last event | Duplicates | Non-15m gaps | OHLC/volume check |
| --- | ---: | --- | --- | ---: | ---: | --- |
| SOLUSDT | 70,079 | 2024-08-21 14:14:59.999Z | 2026-08-21 13:44:59.999Z | 0 | 0 | pass |
| BNBUSDT | 70,079 | 2024-08-21 14:14:59.999Z | 2026-08-21 13:44:59.999Z | 0 | 0 | pass |
| XRPUSDT | 70,079 | 2024-08-21 14:14:59.999Z | 2026-08-21 13:44:59.999Z | 0 | 0 | pass |
| DOGEUSDT | 70,079 | 2024-08-21 14:14:59.999Z | 2026-08-21 13:44:59.999Z | 0 | 0 | pass |
| LINKUSDT | 70,079 | 2024-08-21 14:14:59.999Z | 2026-08-21 13:44:59.999Z | 0 | 0 | pass |
| ADAUSDT | 70,079 | 2024-08-21 14:14:59.999Z | 2026-08-21 13:44:59.999Z | 0 | 0 | pass |
| ETHUSDT | 35,039 | 2025-08-21 14:29:59.999Z | 2026-08-21 13:59:59.999Z | 0 | 0 | pass |

All seven instruments are present and marked `TRADING`; catalog precision and
maker/taker metadata are available. The exact common bar intersection is 35,038
bars, from 2025-08-21 14:29:59.999Z through 2026-08-21 13:44:59.999Z. Therefore
the two-year altcoin history must not be presented as a two-year multi-asset
sample: the cross-symbol research window is one year unless ETH history is
refreshed.

## Funding and derivative overlays

- Funding bundles exist for all seven symbols, 2,195 settlements each, with
  requested coverage 2024-08-20 through 2026-08-21 and no duplicate settlement
  timestamps.
- The 30-day derivatives snapshot at `derivatives_data/20260821` now contains
  2,880 OI rows and 2,880 mark-price rows for all seven symbols. Both series
  have 15-minute spacing and no duplicate timestamps. ETH was backfilled from
  the identical requested historical interval after the initial audit.
- The capture manifest and ETH file hashes are recorded at
  `derivatives_data/20260821/manifest.json`.
- OI and mark klines use interval-open timestamps (for example 14:15:00Z),
  while Nautilus bars are event-stamped at the interval close (14:29:59.999Z).
  Feature joins must map open → close deterministically and use only completed
  data; a one-bar lag is the safe default for entry features.

## Split and OOS decision

The common one-year window is retained as reproducible **S0 screening data**:

- train: 2025-08-21 14:29:59.999Z (inclusive) → 2026-02-21 14:29:59.999Z
  (exclusive);
- validation: 2026-02-21 14:29:59.999Z → 2026-05-22 14:29:59.999Z;
- 2026-05-22 onward is historical context only, not an untouched holdout,
  because the existing baseline research already inspected the full common
  window.

Any promotion attempt must use **S1**, a newly captured future window beginning
after the parameter-lock timestamp. S1 must contain at least six chronological
folds (or the Stage B low-frequency exception), complete funding coverage for
every closed position, and a separately stored capture manifest. No result from
S0 may be called untouched OOS.

## Decision

S0 is clean enough for descriptive feature research and reproducible screening,
including ETH crowding inputs after the backfill. It is not sufficient for
promotion. Before any promotion, capture S1 after parameters are frozen.
