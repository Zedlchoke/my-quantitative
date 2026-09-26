# Phase C1 — Data gate report — PWS-CX-SOLUSDT-C1 (SOLUSDT data plane)

- Cycle: `PWS-CX-SOLUSDT-C1` · Lane: PIT/DATA AUDITOR COMPLETION
  (`c1c2-data-pit-recovery`) · Date: 2026-09-26.
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/pws-cx-solusdt-c1/integration`,
  branch `orca/pws-cx-solusdt-c1-integration`, HEAD `5aadae7a515962feb85f523e73410d30ae907296`.
- Recovery arc: the machine restart of 2026-09-26 ~18:4x local killed the
  original C1/C2 lane mid-run. The three machine files, `data_local/` and the
  license pdf survived **uncommitted**; P2 council handoff (18:36) predates the
  spread census (18:46). This lane **verified the surviving machine files
  against raw bytes by independent recomputation** before completing the
  reports — nothing was taken on schema trust.
- Evidence integrity: every number below was recomputed by this lane from the
  raw artifacts (`/tmp/pws_cx_verify_klines_funding.py`,
  `/tmp/pws_cx_verify_spread2.py`; commands + results recorded in the lane
  handoff). No downloads were performed (budget spent by prior lane).

## 0. Verdict table

| Component | Verdict | Evidence anchor |
|---|---|---|
| Klines corpus (Vision um 1h, 72 months) | **PASS** | 72/72 zip sha256 re-verified; full recount 52,145 bars = machine; 0 duplicate open times; floor exact |
| Funding series (fapi merged H1+H2) | **PASS WITH CAVEATS** | n=6,580 and all headline stats reproduced to machine precision; caveats: Vision cross-check NOT_RUN, 10.3-day tail, FTX-week cadence anomaly |
| Spread census (Vision bookTicker, 6 sampled months) | **PASS WITH CAVEATS** | 2 sample months recomputed from raw zips: p50 bit-exact ×48, max-spread bit-exact ×2, p99 ≤1.6e-4 bps; caveats: 6-month stratified coverage only, 2023-24 regime, stride bookkeeping ±≤30 rows disclosed |
| License posture | **PASS** | Binance Vision keyless public archive + ToU pdf captured (sha-pinned); fapi public endpoint; no authenticated source touched |

Gate conclusion: data plane is usable for cost-book and freeze work **with the
disclosed caveats binding**. Any component left NOT_RUN stays fail-closed: the
funding Vision cross-check is NOT_RUN ⇒ the funding series may not be claimed
"dual-source verified" anywhere downstream; a freeze that consumes the spread
census must disclose its sampling (§3.5).

## 1. Klines corpus — PASS

Source: Binance Vision keyless public archive, futures/um monthly klines 1h
SOLUSDT, `data_local/vision/klines_um_SOLUSDT_1h/` (72 zips, 2.4 MB total,
untracked; sha256 for every zip in `data_local/INVENTORY.md` and inside the
machine census).

Independent verification (full recount, not spot check — the corpus is small):

| Claim (machine) | Recounted | Match |
|---|---|---|
| n_zips 72 | 72 | YES |
| total_bars 52,145 | 52,145 | YES |
| duplicate_open_times 0 | 0 | YES |
| first_open 2020-09-14T07:00:00Z | 2020-09-14T07:00:00.000Z | YES |
| last_open 2026-08-31T23:00:00Z | 2026-08-31T23:00:00.000Z | YES |
| ideal_grid 52,265 / missing 120 | 52,265 / 120 | YES |
| monthly_bars (72 months) | all 72 identical | YES |
| zip sha256 manifest | 72/72 byte-identical | YES |

- **Floor confirmed**: first bar 2020-09-14T07:00Z = first full hourly bar after
  the 2020-09-14 listing; `floor_match: true` is correct.
- **The 120 missing bars — characterized, disclosed, NOT repaired** (two
  contiguous venue maintenance windows, all 24 hours of whole days; nothing
  SOL-idiosyncratic in shape):
  1. **2022-02-26T00:00Z .. 2022-02-28T23:00Z — 72 bars** (3 full days),
     month 2022-02 has 600/672 bars;
  2. **2022-04-01T00:00Z .. 2022-04-02T23:00Z — 48 bars** (2 full days),
     month 2022-04 has 672/720 bars.
  Both windows are consistent with Binance futures exchange-maintenance
  outages (late-Feb and early-Apr 2022); consistent with venue-wide gaps, not
  symbol dropout (single-symbol attribution to venue maintenance is an
  inference from shape and dates, disclosed as such). Any bar-grid consumer
  must treat these as genuine missing data; no forward-fill exists in the
  corpus.
- Cross-corpus: prior lane verified 72/72 zips byte-identical to the copy in
  the ETHUSDT-OPEN-SEARCH-V2 worktree (read-only comparison; disclosed in
  INVENTORY).
- Power-analysis input: **8,760 bars/year nominal** (744/month full months);
  8,785/year average over the 5.936-year span including the partial first
  month.

## 2. Funding series — PASS WITH CAVEATS

Source: Binance fapi `/fapi/v1/fundingRate` public endpoint. H1 scan
(2020-07-01..2024-08-20 window request, 4,385 rows) + H2 scan
(2024-08-20..2026-08-21T23:45 request, 2,196 rows) = 6,581 raw, **1 exact
boundary duplicate dropped → 6,580** (recounted identically).

Independent recomputation from `data_local/funding/SOLUSDT_funding.json` (the
4,385-row merged H1 copy — verified row-identical to the H1 scan) and from the
two scan files directly:

| Statistic (overall, machine) | Recomputed | Match |
|---|---|---|
| n | 6,580 | 6,580 YES |
| mean_rate | 1.37616869300912e-06 | 1.37616869300912e-06 YES (bit-exact) |
| median_rate | 8.5755e-05 | 8.5755e-05 YES |
| sum_rate | 0.00905519000000001 | 0.00905519000000001 YES |
| neg_share | 0.28617021276595744 | identical YES |
| worst | −0.02 | −0.02 YES |
| max | 0.00332469 | 0.00332469 YES |
| per-year 2022.all / 2026.all blocks | reproduced within 1e-9 tolerance | YES |
| extremes timestamps | 2022-11-09T20:00:00.018Z (−0.02); 2021-02-10T08:00:00.014Z (+0.00332469) | YES |
| first / last fundingTime | 2020-09-13T16:00:00.004Z / 2026-08-21T16:00:00.001Z | YES |

- **Floor confirmed**: first settlement 2020-09-13T16:00:00.004Z;
  `floor_match: true` correct (funding starts one day before the first 1h bar —
  different feeds, disclosed).
- **FTX-week interval anomaly — verified exactly.** The whole 6-year series has
  **exactly 101 non-8h spacings**, all confined to
  **2022-11-09T16:00:00.004Z .. 2022-11-18T08:00:00.016Z** (first anomalous
  spacing start = machine window start; last anomalous spacing end = machine
  window end). Composition: **99 spacings of 1-4h + 2 spacings of 5-7h** — the
  machine's phrase "101 spacings of 1-4h" is loose by those 2 (5-7h) rows; the
  count 101 and the window confinement are exact. This is the venue's emergency
  funding-interval increase around the FTX collapse (cadence moved to a 2h/4h
  grid; anomalous spacing end-hours are the even hours 00..22). **Consequence
  (binding): per-settlement path accounting must use actual timestamps, never
  the nominal 8h grid** — the machine file's `annualized_mean_note` already
  says this; it is restated here as a gate condition. The 2,039 spacings in
  (7h, 8h) elsewhere in the series are ms-offset artifacts of the normal 8h
  cadence, not gaps (verified).
- Downtrend SMA200 state definition (cost statistic only): independently
  recomputed — insufficient-history settlements 27 (2020-09-13T16:00Z ..
  2020-09-22T08:00Z), n_downtrend_months 37, and all 37 month labels match the
  machine file exactly.
- **Caveats (all disclosed, none repaired):**
  1. `cross_check_vision: NOT_RUN` — **kept NOT_RUN, not fabricated.** No local
     Vision fundingRate_um_SOLUSDT archive exists; the download budget was
     allocated to the spread census. The H1+H2 scans are one campaign
     (CHR3F staging 2026-09-23/24), not independent sources. Downstream may use
     the series as the measured cost authority but must not describe it as
     cross-source verified. The conflict rule (any row diff ⇒ symbol-month
     EXCLUDED) stays applicable if a Vision series is staged later.
  2. **Funding tail uncovered**: series ends 2026-08-21T16:00Z vs klines
     2026-08-31T23:00Z → 10.3-day funding tail without settlements.
  3. FTX-week anomaly as above; also the worst settlement −0.02 (−200 bps of
     notional) sits inside it — concentration risk for any payer-side tail.

## 3. Spread census — PASS WITH CAVEATS

Source: Binance Vision keyless public archive, futures/um **monthly bookTicker**
SOLUSDT (best bid/ask snapshots; fields
update_id, bid, bid_qty, ask, ask_qty, transaction_time, event_time).
Machine file: `C1_machine_SPREAD_CENSUS_SOLUSDT.json`.

### 3.1 Units (stated explicitly)

**All spread values in the census are in basis points of mid price**:
`spread_bps = (ask − bid) / mid × 1e4`, `mid = (bid + ask)/2`, computed per
snapshot on the **transaction_time base** (exchange matching engine, ms, UTC —
the PIT choice; event_time is the archive-receive stamp and is not used). The
machine file's `calibration` block is **not** a unit calibration — it is the
K-selection heuristic (`rows_per_MB_zip_used_for_K = 77,000`, plus the measured
2023-05 full row count 27,234,787, which this lane confirmed exactly). Pooled
p50 0.469 bps ≈ 0.0047% of price — sane for a 2023-24 major perp, corroborating
the bps reading.

### 3.2 Coverage and stratification

- Keyless monthly bookTicker exists **only for 2023-05..2024-04** (12 months;
  everything else 404, daily likewise only 2023-05-16..2024-03-30). Months
  2020-09..2023-04 and 2024-05..2026-08 are **unmeasurable** from keyless
  public archives.
- The census samples **every odd-position month of the 12 available**:
  2023-05, 2023-07, 2023-09, 2023-11, 2024-01, 2024-03 — systematic, no regime
  cherry-picking; per-month K (13/56/32/94/135/145) targets ~2M samples each;
  13,805,136 sampled rows total (sum of per-month sampled_rows: arithmetic
  verified). Per-month meta (zip_bytes, K, sampled_rows, invalid=0, first/last
  transaction_time, max spread, elapsed_s) is recorded in
  `per_month_meta` and carried.
- Archive-content facts disclosed in per_month_meta: 2023-05 starts mid-month
  (May 16 11:49 — first archive month); 2023-07 content ends Jul 15; 2023-09
  ends Sep 28 02:39; 2023-11 ends Nov 6; 2024-01's meta lists first>last
  sampled timestamp (non-chronological on-disk ordering for that month —
  systematic-stride coverage is still uniform, but "chronological stream" is
  not literally true for that file). Only the two months below were
  independently recomputed; the other four months' stats are carried from the
  prior lane's machine file, not independently verified by this lane.

### 3.3 Independent recomputation (2 sample months from raw zips)

Method: full stream of the zip CSV, systematic 1-in-K stride (K=13 for
2023-05, K=32 for 2023-09), spread_bps per snapshot, per-hour (transaction_time
UTC hour) p25/p50/p75/p99, linear-interpolation percentiles — recomputed under
two candidate stride offsets (0 and 164) to bound bookkeeping sensitivity.

| Check | 2023-05 | 2023-09 |
|---|---|---|
| Data rows in zip | 27,234,787 (machine calibration: 27,234,787 — exact) | 70,830,384 |
| Sampled n (machine) | 2,094,971 | 2,213,420 |
| Sampled n (recount, offset 0) | 2,094,984 (+13, +6.2e-6 rel.) | 2,213,450 (+30, +1.4e-5 rel.) |
| **p50, all 24 hour-blocks** | **bit-exact ×24** | **bit-exact ×24** |
| **max_spread_bps_sampled** | **bit-exact (96.86896223169141)** | **bit-exact (57.7224375360748)** |
| p99 | exact in 12/24 blocks; rest within **1.6e-4 bps** (max abs 1.59e-4) | exact in 15/24 blocks; rest within **7.7e-5 bps** |
| invalid rows sampled | 0 (= machine) | 0 (= machine) |
| last sampled transaction_time | exact match | exact match |
| first sampled transaction_time | differs ~2.2 s (≤K-row warm-up at stream start) | differs 0.15 s (same cause) |

Residual: the census's stride enumeration skipped a few rows at stream start
(≤K warm-up), giving ±13/+30 total-row differences (≤1.4e-5 relative) and
one-tick p99 position shifts ≤1.6e-4 bps on ~1-2 bps values. **Immaterial to
any cost conclusion; offset-0 reproduction of p50/max is bit-exact, so the
census statistics are genuine functions of the raw bytes.** Offset 164 (worst
case) perturbs p50 by up to 0.39 bps in isolated tail-hours, bounding stride
sensitivity; the machine's own counts sit between the two, confirming offset 0
plus warm-up as the true scheme.

### 3.4 Census numbers (carried + verified anchor points)

- Pooled overall: n=13,805,136, p25 0.109 / **p50 0.469** / p75 0.515 /
  **p99 2.350** / mean 0.442 (all bps).
- Pooled by hour: p50 range 0.437 (h07) .. 0.486 (h15); p99 range 1.57 (h05) ..
  3.89 (h00); mean range 0.376 .. 0.536 bps. US hours (13-18 UTC) are the
  widest and busiest — relevant for fill-hour conditioning.
- Regime shift visible across months: 2024-03 p50 ≈ 0.068 bps vs 2023-05
  p50 ≈ 0.49 bps — the tick-cost base fell ~7× over the sampled stratum.
- Sampled monthly max spread: 96.9 (2023-05) .. 223.8 bps (2023-11) — tail
  crossings are two orders of magnitude above p50.

### 3.5 Caveats (binding)

1. **The census is the CURRENT evidence class for spread.** It covers 6 of 72
   corpus months, all inside 2023-05..2024-04. **Early-2020/2021 conditions
   were very likely wider** (younger book, lower SOL price, thinner depth) and
   2025-26 narrower; neither is measured. Any freeze using these numbers must
   disclose: 6-month stratified sampling, odd-month stride, 2023-24 regime, and
   the unmeasurable months. A cost stress case must not use pooled p50 as a
   floor for the unmeasured era.
2. The four un-recomputed months (2023-07, 2023-11, 2024-01, 2024-03) carry
   prior-lane stats only; the two recomputed months validate the method, not
   every row of every month.
3. Archive content truncations and the 2024-01 ordering quirk (§3.2) are
   properties of the keyless archive, disclosed, not repairable locally.
4. bookTicker is best-quote snapshot, not executed fills: commission and
   slippage-beyond-touch are **not measured** by this census (same
   `PAPER_TIER/FILL_QUALITY` posture as the FX book).

## 4. License posture — PASS

- Klines + bookTicker: **Binance Vision keyless public archive**; Terms of Use
  captured at `licenses/Binance_Vision-Terms_of_Use.pdf`
  (sha256 `94d6f61a39b5f821ef1d38f968aea1f2aa136e374f2061a2131db9a6af96bc3b`).
- Funding: **fapi public endpoint** (`/fapi/v1/fundingRate`), keyless, captured
  under the CHR3F staging campaign — no credentials used, none recorded.
- No authenticated or paid source was touched; no API key material exists in
  any artifact of this lane.

## 5. Power-analysis inputs (for trial sizing downstream)

| Quantity | Value |
|---|---|
| 1h bars total / per year | 52,145 / 8,760 nominal (8,785 avg over span) |
| Funding settlements total / per year | 6,580 / 1,095 nominal 8h (1,108.6 actual avg — FTX-week extra settlements included; **use actual timestamps per path, not 1095**) |
| Funding span | 2020-09-13 .. 2026-08-21 (5.936 y; 10.3-day tail gap to klines end) |
| Spread samples | 13,805,136 over 6 stratified months (2023-05..2024-04) |
| Downtrend-state share (SMA200 def) | 3,354/6,580 settlements; 37/72 months |

## 6. Fail-closed items

- `cross_check_vision` = **NOT_RUN** (reason preserved verbatim in the machine
  file): funding series stays single-campaign until a Vision fundingRate
  archive is staged; the symbol-month EXCLUSION conflict rule stays armed.
- Spread census months 2020-09..2023-04 and 2024-05..2026-08: **BLOCKED**
  (keyless archive 404) — cannot be measured without new authorization; treat
  unmeasured-era spread as UNKNOWN_WIDER, not as pooled p50.
- No other component is NOT_RUN/BLOCKED. The gate overall is
  **PASS WITH BINDING CAVEATS**; the caveats in §2/§3/§6 are conditions, not
  decorations.

— Lane `c1c2-data-pit-recovery`, PIT/DATA AUDITOR COMPLETION, 2026-09-26.
