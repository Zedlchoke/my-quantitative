# COVERAGE NOTE — FX data plane (Lane I1a, PORTFOLIO-ROUTER-12ASSETS-100K-V1)

Measured 2026-09-28 directly on disk (decode/scan, not copied from prior docs).
All numbers also live in `data_manifest_fx.json` (machine-readable, with sha256s).

## Per-panel measured ranges

| symbol | granularity | files | total bytes | measured first ts (UTC) | measured last ts (UTC) | source cycle |
|--------|-------------|-------|-------------|-------------------------|------------------------|--------------|
| EURUSD | M1 bid+ask (.bi5) | 2x2092 | 36,722,777  | 2021-01-03 22:00 | 2026-09-23 23:59 | FX-RANGEFADE-2M-SHADOW-V1 |
| GBPUSD | M1 bid+ask (.bi5) | 2x2092 | 36,601,602  | 2021-01-03 22:00 | 2026-09-23 23:59 | FX-MAJORS-SEARCH-V1 |
| USDJPY | M1 bid+ask (.bi5) | 2x2092 | 38,433,187  | 2021-01-03 22:00 | 2026-09-23 23:59 | FX-MAJORS-SEARCH-V1 |
| USDCAD | H1 ANC parquet   | 1     | 1,306,817   | 2021-01-03 23:00* | 2026-06-30 23:00*  | ERP1-TRACKA-COHORT-1 |
| AUDUSD | H1 ANC parquet   | 1     | 1,215,240   | 2021-01-03 23:00* | 2026-06-30 20:00*  | ERP1-TRACKA-COHORT-1 |

\* ANC stamps are open-time in the source; in loader space (close-stamped,
  +1h) the ranges are 2021-01-04 00:00 → 2026-07-01 00:00 (USDCAD) and
  → 2026-06-30 21:00 (AUDUSD).

File-name ranges start 2021-01-01, but the first *active* (volume>0) quote in
all five panels is Sunday 2021-01-03 22:00 UTC — the FX weekly open after the
New Year holiday weekend. 2021-01-01/02 files exist but contain only flat
zero-volume carry-forward records.

## Walk-forward calendar support

- **5-pair intersection window**: 2021-01-03 22:00 UTC → 2026-06-30 (last
  ANC tradable hour). = 2,005 calendar days.
- **Mon-aligned full weeks inside the intersection** (weeks Mon 2021-01-04 …
  Sun 2026-06-28): **286 weeks**. This is the calendar a 5-pair walk-forward
  can support with every symbol on the same completed-bar clock.
- **M1-only extension** (EURUSD/GBPUSD/USDJPY continue to 2026-09-23):
  298 Mon-aligned weeks — 12 extra weeks usable only for the 3 M1 pairs.
- Practical budget if the router splits IS/OOS: e.g. 200 IS + 80 OOS weeks
  fits with room for a 6-week embargo inside the 286-week intersection.

## Gaps (measured)

| panel | missing calendar days | gap runs | largest gap | character |
|-------|----------------------|----------|-------------|-----------|
| EURUSD M1 | 0 | 0 missing-day; largest tradable-minute run **4,321 min (~3.0 d)** across New Year 2024 | every file exactly 1440 records |
| GBPUSD M1 | 0 | 0 missing-day; largest tradable-minute run **4,321 min** (2024-01-01) | same |
| USDJPY M1 | 0 | 0 missing-day; largest tradable-minute run **4,321 min** (2024-01-01) | same |
| USDCAD H1 | n/a (sparse by construction) | 2,061 runs vs full hourly grid | 75 h | weekends + rollover hour absent (tradable filter) |
| AUDUSD H1 | n/a (sparse by construction) | 1,948 runs vs full hourly grid | 76 h | same |

- M1 corpora: **no missing days, no short files** (all 2092 daily files per
  side decode to exactly 1440 records; 0 OHLC invariant violations on the
  full BID scan). Weekends are flat zero-volume records — present but
  flagged `tradable=False` by the loader. Only one weekday in 5.7 years has
  zero tradable minutes: 2021-01-01 (New Year holiday). Standard weekends
  are ~2,880 tradable-minute gap; the 4,321-min maximum spans the
  Christmas→New-Year holiday week.
- ANC panels: 17,711 (USDCAD) / 17,674 (AUDUSD) hours absent vs a full
  hourly grid, in ~2k runs. This is **structural, not data loss**: the panels
  contain only tradable hours (volume>0, registered price band, ask>=bid,
  strictly consecutive source minutes). Saturdays: 0 rows. Weekday median
  21 rows/day; the ~21:00–22:00 UTC rollover hour is mostly absent; largest
  gaps are holiday weekends (e.g. 2021-01-08 22:00 → 2021-01-10 21:00 UTC).

## Timezone / DST verification

Two independent lines of evidence, both measured:

1. **Record-count test**: the US spring-forward day 2021-03-14 file has 1440
   records spanning sec 0→86,340 (full 24 h); fall-back 2021-11-07 also
   1440. A US/EU-local-stamped feed would show 1380/1500 records on those
   days.
2. **Seasonal boundary-shift test** (measured_panels.json `dst_utc_probe`):
   the last *tradable* minute of winter Fridays (EST) is 21:59 UTC and of
   summer Fridays (EDT) 20:59 UTC — i.e. the NY 17:00 close shifts by one
   hour *inside* the files across seasons, which is exactly what a UTC-stamped
   feed of a New-York-closed market must show. Sunday first tradable minute:
   22:00 UTC winter vs 21:00 UTC summer.

Conclusion: source stamps are **UTC** for all M1 panels; ANC parquet `ts` is
tz-aware UTC. Loader bar stamping: **close time, UTC** everywhere. A bar
labeled T aggregates (T−rule, T]. At decision time T every bar stamped ≤T is
completed — no lookahead by construction. The DST unit test pins the
resampler to count 23/25 buckets if an hour is ever missing/duplicated
(guards against a future local-time feed); real panels show 24.

## Cross-measurement note

`measure_panels.py` (left by a prior interrupted I1a attempt; reviewed,
one units bug fixed — see handoff incidents) re-measures everything
independently and writes `measured_panels.json`. Every overlapping number
agrees with `data_manifest_fx.json` (file counts, bytes, first/last ts, H1
rows/sha256, manifest hashes). Digest formulations differ slightly and are
each documented: the manifest uses per-side `filename,size` digests; the
script uses a combined-side `side/filename size` digest. Tradable-minute
census (M1): EURUSD 2,130,647 / GBPUSD 2,130,680 / USDJPY 2,131,564 of
3,004,800 total minutes.

## H1-vs-M1 ceiling (USDCAD / AUDUSD)

- The ERP1 worktree retained only the derived H1 planes for USDCAD/AUDUSD —
  the raw M1 .bi5 corpus is **not** on disk (duka manifests only). So:
  - intraday M1 features, tick-close H/L, sub-hour execution modeling:
    **NOT_RUN / impossible** on these two pairs within this data plane;
  - their `bid_h`/`bid_l` follow the *ancestor convention* (max/min of M1
    **closes**, not intrabar extremes) — understates true range; range-based
    signals on these pairs are biased low relative to the M1 pairs;
  - no ask H/L (only ask open/close) — spread dynamics limited to bar
    endpoints;
  - tradable-hour sparsity means H1 bar *absence* carries information
    (weekend/rollover) — the engine must not treat absent bars as zero
    return or as stale-carry without an explicit rule.
- Consequence for the router: treat USDCAD/AUDUSD as H1-close-driven
  assets; EURUSD/GBPUSD/USDJPY can additionally support M1-derived features.
  Cross-pair feature parity is only achievable at H1-or-coarser.

## Macro inputs

No fredgraph CSV / NY Fed EFFR JSON staged anywhere in the repo yet
(searched). `loaders.load_macro_series` implements both formats (unit-tested
on synthetic fixtures: '.' missing handling, revision flags) — the macro lane
must stage the real files before use.

## Loader API summary

`research/pr12a100k/loaders.py` (pure, no network, fail-closed):

- `load_macro_series(path, fmt)` → `(pd.Series, metadata)`; fmt ∈
  {fredgraph_csv, nyfed_effr_json}.
- `asof(series, decision_ts, rule='T+Nd')` → PIT value; available_at =
  obs_date + N days; value published T+1 never visible at T (unit-tested).
- `load_fx_m1(symbol, start, end, root=None, tradable_only=False)` →
  per-day file union, bid/ask/mid + spreads, `tradable` flag, UTC
  close-stamped minute index.
- `resample_bars(m1, 'h' | 'd')` → close-stamped H1/D1 OHLC + spread
  open/close/mean + volume + n_minutes; empty buckets dropped, never
  fabricated.
- `load_fx_h1(symbol)` → ANC parquet, open→close stamp conversion, mid and
  spreads derived.
- `corpus_digest(side_dir)` → sha256 of sorted (filename,size) lines
  (documented strategy).
