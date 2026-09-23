# CENSUS — PSV1 / L2_BTC_H4

Cycle `PHASE-STRATEGY-V1`, cell **BTC_H4** (BTCUSDT-PERP, 4-hour UTC buckets,
derived from Binance Vision 1h klines — the aggregated-from-1h representation
is the scored one). Dispatch SHA `6e6ffa3bb1c6ad82fb1771b99abdecfb0bedf849`.
Machine-readable companions: `census.json`, `../data/data_gate.json`,
`../freezes/*.json`.

**Outcome-blindness (plan §7.3):** this census contains counts, occupancy,
dwell, transitions and floor margins ONLY. No strategy returns, equity or PnL
of any kind exists anywhere in this lane.

## 1. Data gate verdict (plan §9.1)

**`PASS_WITH_DISCLOSURES`**, retrieval deterministic.

- Source: Binance Vision keyless USDT-M futures klines, `BTCUSDT` perp.
  Window 2020-01 (2019-12 monthly is 404) → **data_end = 2026-09-22T23:59:59Z**
  (close of the 23:00–23:59 1h bar; the 2026-09-23 daily zip is 404 at
  retrieval; last complete H4 bucket opens 2026-09-22T20:00Z). 182 files
  sha256-pinned in `../data/manifest.json`
  (80 monthly 1h + 22 daily 1h tail-stitch + 80 monthly 4h shadow).
  Deterministic re-retrieval verified on 3 samples — all digests match.
- Volume: 58,968 1h bars → **14,742 complete H4 buckets** (binding law:
  bucket = floor(open/4h) UTC, complete iff exactly 4 aligned 1h bars;
  **0 partial buckets excluded** — the feed is gap-free within tolerance).
- Integrity law: OHLC sanity clean on 1h and H4; zero duplicate timestamps;
  interior 1h gap fraction 0.0000 (0 of 58,968 calendar slots; longest run
  0h ≤ 4h tolerance); zero-volume bars flagged, not dropped (1h: 1; H4: 0).
- **Mandatory native-4h shadow:** `MATCH_EXCEPT_3_DISCLOSED_BUCKETS` —
  14,607/14,610 buckets match EXACTLY (tolerance 1e-9). Disclosed snapshot
  revisions (aggregated-from-1h stays the scored representation; nothing
  smoothed): `2024-10-28T20:00Z` open (69,566.1 vs 69,650.0);
  `2023-11-10T12:00Z` close + volume (37,092.6/80,360 vs 37,118.4/68,307);
  `2022-07-16T04:00Z` volume (62,207.6 vs 62,235.7).
- **Optional frozen 15m catalog cross-check (sha `81d4f147…`, verified):**
  `CATALOG_NOT_CORROBORATIVE_MISMATCH_DISCLOSED`. The catalog is a uniform,
  monotonic 15m grid but its OHLCV content differs materially from the Vision
  series on all 2,189 shared 4h buckets (median hourly-boundary close
  rel-diff ≈ 41 bps, p99 ≈ 327 bps, 0/8,760 hourly closes match at 1e-6;
  volume mismatches on 2,189/2,189 buckets). Cause is not determinable from
  inside this lane. Finding disclosed, never smoothed; the scored
  representation stands on the mandatory native-4h shadow.
- **PIT disclosure (in every artifact):** Vision klines are retrospective
  exchange snapshots (retrieved 2026-09; no per-bar publication timestamps).
  Frozen convention: a bar is knowable at its close; first executable fill at
  the NEXT H4 bucket open.

## 2. Phase rule (frozen; `../freezes/phase_rule_freeze.json`)

Deterministic causal rule on H4 closes (UTC): `sma = SMA(close, 120)`,
`slope = sma_t/sma_(t-30) − 1`, `side = close_t/sma_t − 1`. Quadrants with
explicit uncertainty conditions — U1 warmup (<153 bars), U2 `|slope| < 1%`,
U3 `|side| < 1%`, U4 raw state must repeat 3 consecutive bars — map to exactly
five outputs: ACCUMULATION (below rising average), UPTREND, DISTRIBUTION
(above falling average), DOWNTREND, TRANSITION_UNKNOWN. Round constants fixed
before any history-wide measurement. No Jev input anywhere.

**±1-notch label agreement (reported, never optimized):** N_SMA±10 → 90.2/90.5%;
M_SLOPE±5 → 95.4/95.8%; DEADBAND_SLOPE−0.5pp/+0.5pp → 88.8/91.1%;
DEADBAND_SIDE±0.5pp → 96.7/96.7%; CONFIRM±1 → 97.7/98.1%.

## 3. Occupancy and episodes (post-warmup 14,589 H4 buckets)

| Phase | Bars | Share | Episodes (cell) | Margin vs ≥20 |
|---|---|---|---|---|
| ACCUMULATION | 435 | 3.0% | 57 | +37 |
| UPTREND | 4,421 | 30.3% | 94 | +74 |
| DISTRIBUTION | 430 | 2.9% | 48 | +28 |
| DOWNTREND | 2,932 | 20.1% | 85 | +65 |
| TRANSITION_UNKNOWN | 6,524 | 44.7% | 284 | +264 |

UNKNOWN share by fold: F1 34.4%, F2 37.6%, F3 45.2%, F4 54.6% (longest
UNKNOWN runs 127/141/147/240 bars). The UNKNOWN share grows toward the present
— the rule explicitly declines to phase low-conviction stretches (dead-bands
and confirmation), it never abstains via any model.

## 4. Floors per phase × fold (immutable 20/3/100)

Eligible decisions = bars with that label in the fold; episodes = maximal
contiguous runs. Full detail in `census.json`.

| Phase | F1 eps/dec | F2 eps/dec | F3 eps/dec | F4 eps/dec | Verdict |
|---|---|---|---|---|---|
| ACCUMULATION | 19/140 | 12/111 | 14/113 | 12/**71** | **NOT_RUN_THIN_PHASE** (F4 decisions −29) |
| UPTREND | 21/1,299 | 20/695 | 35/1,617 | 18/810 | **DATA_SUFFICIENT** (all margins ≥ +15 eps, +595 dec) |
| DISTRIBUTION | 7/**66** | 17/194 | 14/117 | 10/**53** | **NOT_RUN_THIN_PHASE** (F1 −34, F4 −47) |
| DOWNTREND | 12/308 | 29/1,285 | 20/556 | 25/783 | **DATA_SUFFICIENT** (all margins ≥ +9 eps, +208 dec) |
| TRANSITION_UNKNOWN | 60/950 | 79/1,375 | 83/1,983 | 64/2,063 | gate state, not tradable |

Median dwell (bars): UPTREND 26/20/26/27; DOWNTREND 7.5/24/23/11 across
F1–F4. ACCUMULATION and DISTRIBUTION have adequate cell-level episode counts
(57/48 ≥ 20) but fail the per-fold decision floor — reported with margin, NOT
pooled with BTC_H1 or any other cell, never silently relaxed.

## 5. Era × fold mapping

Fold = era (4 eras ⇒ boundaries on era edges, plan §4.3): F1=ERA-B1
2020-01-01→2021-04-30 (post-warmup), F2=ERA-B2 2021-05-01→2022-12-31,
F3=ERA-B3 2023-01-01→2024-12-31, F4=ERA-B4 2025-01-01→data_end. Fold ends
force-flat for signal segmentation. The sub-window 2025-08-20→2026-08-20
overlaps the outcome-observed frozen V2 15m catalog — disclosed (and that
catalog proved non-corroborative, §1).

## 6. Cell independence

BTC_H4 is a separate cell from BTC_H1 on the SAME asset: own labels, own
folds, own trial accounting. Nothing here pools with BTC_H1, and any future
cross-cell agreement is one-asset corroboration with a shared-data caveat,
never two independent confirmations.
