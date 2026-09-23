# PIT DISCLOSURES — A2 data inventory (BTC-BEAR-OPPORTUNITY-RECON)

measured: 2026-09-23 (UTC), keyless probes of data.binance.vision + REST fapi.
Evidence: `data_inventory.json` (curated), `vision_probe1_raw.json` (HEAD/Range
walk + sample decodes), `s3_structure.json` (authoritative S3 key listing),
`funding_sha256.json` (per-month digests), probe scripts in this directory.
No coverage claim below is taken from documentation; every window was probed
or key-listed.

## 1. Retrieved vs available time per source

| source | available (TRUE, measured) | retrieved (this recon) | publication lag / finality evidence |
|---|---|---|---|
| um klines 4h & 1h monthly (+ all 12 intervals of klines / markPriceKlines / indexPriceKlines / premiumIndexKlines) | 2020-01 → 2026-08 monthly; daily tail 2019-12-31 → 2026-09-22 (2026-09-23 not yet published at probe time) | 2026-09-23 | Last-Modified ≈ month end + 2–3 weeks (4h 2024-06: LM 2024-07-17); daily tail T+1 |
| um fundingRate monthly | 2020-01 → 2026-08 (80 files contiguous; 2019-09..2019-12 NOT in archive) | 2026-09-23 | LM ≈ month end + ~2 weeks (2024-06: 2024-07-16); 2020-01 file REWRITTEN 2023-05-09 |
| fapi REST fundingRate | 2019-09-10 08:00 UTC → now (forward pagination, limit 1000) | 2026-09-23 (sample pages) | live mutable endpoint |
| um metrics (OI, L/S ratios) — DAILY ONLY | 2020-09-01 → 2026-09-22 at 5-minute grain (n=2213 files) | 2026-09-23 (2 files decoded) | daily file, T+1-style publication; whole history appears retrospectively |
| fapi REST openInterestHist | ~41.6 h lookback only (500×5m measured); older startTime → HTTP 400 | 2026-09-23 | live endpoint |
| um bookTicker (tick top-of-book) | 2023-05-16 → 2024-04 ONLY (monthly 2023-05..2024-04; daily ends 2024-03-30) | 2026-09-23 (range-sample decode) | export DISCONTINUED after 2024-04 |
| um bookDepth (relative-depth snapshots) — DAILY ONLY | 2023-01-01 → 2026-09-22 (n=1358) | 2026-09-23 (range-sample decode) | 2026-09-22 file LM 2026-09-23 07:27 (T+1); 2023-01-01 file backfilled as late as 2023-07-11 |
| um liquidationSnapshot (BTCUSDT-PERP) | NOTHING — no prefix under um/, all legacy-month HEADs (2020-01..2021-06) 404 | 2026-09-23 | exchange removed the um export entirely, including 2020–2021 history |
| cm liquidationSnapshot (BTCUSD_PERP, COIN-M sibling) | 2023-06-25 → 2024-10-14 (472 daily files, 6 missing days), DISCONTINUED | 2026-09-23 (1 file range-decoded) | T+1 LM; ended 2024-10-14 |
| futures/bm/ (as named in dispatch) | prefix DOES NOT EXIST — bucket root has only `um/` and `cm/` | 2026-09-23 | naming correction, not a data loss |
| aggTrades / trades (um) | families exist monthly+daily (listing); depth NOT measured | not retrieved | — |

## 2. Retrospective-only flags (MANDATORY reading before any live book)

- **All Vision files are retrospective exchange snapshots.** There are NO
  per-bar publication timestamps. PSV1's frozen convention (bar knowable at
  its close; first executable fill at the NEXT H4 open) is what makes the
  kline panel decision-causal; it is a convention, not an exchange guarantee.
- **fundingRate**: PIT_USABLE as settled event history (rate fixed at
  calc_time). RETROSPECTIVE_ONLY as a live tail — current-month funding does
  not exist on Vision until month end + processing; live funding must come
  from REST and be row-pinned at retrieval.
- **metrics (OI)**: RETROSPECTIVE_ONLY. Rows are event-time-stamped so
  decision-time causality is reconstructible at 5m grain from 2020-09-01,
  but a live decision cannot see this source with < T+1 lag. It is also the
  ONLY multi-year OI history that exists on Binance keyless surfaces, and it
  starts 2020-09-01 — not at perp launch (2019-09). OI research windows
  before 2020-09 are NOT MEASURABLE.
- **bookDepth**: RETROSPECTIVE_ONLY, 2023+ only, T+1 publication.
- **bookTicker / liquidationSnapshot**: UNAVAILABLE for any current-cycle
  use (discontinued exports; islands only).
- **Archive rewrite evidence (measured)**: klines 1h 2020-01 Last-Modified
  2021-06-14 (rewritten ~17 months after month end); fundingRate 2020-01
  rewritten 2023-05-09 (schema migration); bookDepth 2023-01-01 backfilled
  2023-07-11. Monthly files are byte-stable over short horizons (double
  downloads byte-identical; klines 1h 2020-01 sha256 re-matches the frozen
  PSV1 manifest entry `512a1d72…` exactly), but immutability is NOT
  guaranteed across years. **Consequence: pin sha256 at retrieval and
  re-verify on every reuse (PSV1 manifest law).**

## 3. Determinism evidence

- fundingRate 2024-06: downloaded twice, byte-identical (sha `43fc4473…`).
- klines 1h 2020-01: downloaded twice, byte-identical, sha256
  `512a1d725c8df97a…` == frozen PSV1 manifest entry (retrieved independently
  earlier the same day by PSV1).
- License/terms: data.binance.vision is Binance's free, keyless public
  export (no API key; no auth headers used in any probe). License text was
  not re-derived in this recon; treat as source-licensed research input.

## 4. What this means for "what is even measurable" (data authority only)

1. Price/phase work on the frozen PSV1 window (2020-01-26 → 2026-09-22):
   fully supported, PIT_USABLE, floors PASS.
2. Funding-signed work over the same window: fully supported (archive + REST
   back to 2019-09-10).
3. OI/positioning work: only from 2020-09-01, 5m grain, retrospective-only;
   nothing before that date exists anywhere keyless.
4. Liquidation-print work on BTCUSDT-PERP: NOT MEASURABLE (um tape removed
   entirely). The ancestry "honest gap" for liquidation-print-conditioned
   dislocation is answered at the data layer: UNAVAILABLE. The only print
   tape that ever existed on Vision (cm island 2023-06..2024-10) is a
   sibling instrument and stale >13 months.
5. Tick/order-book work: no current source; 2023-05..2024-04 bookTicker
   island only.
