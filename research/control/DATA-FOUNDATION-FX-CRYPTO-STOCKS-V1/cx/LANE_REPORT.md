# LANE_REPORT — L-CX (crypto data census + validation)

Cycle `DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1`, lane L-CX, branch
`orca/dfv1-lane-cx`, worktree `.../.worktrees/data-foundation-v1/lane-cx`,
base/dispatch SHA `189c6d23ab2a6f50475819cf6df2e2e4def92820` (verified
`git rev-parse HEAD` before and after work). OFFLINE lane: zero network
requests made. Rows are per DATASET FAMILY (not per cycle). Artifact:
`inventory_rows.jsonl` — 21 rows: 6 AVAILABLE_VALIDATED, 2
AVAILABLE_UNVALIDATED, 13 NOT_RUN.

**Owner prohibition, verbatim (binding on every OI / liquidation / L2 row
above and below):**

> Không suy ra order book hay forced flow từ nến

(no order book or forced flow inferred from candles). Rows
`oi_history_usdm`, `liquidation_history`, `l2_orderbook_history` each carry
this line in their status_evidence.

## 1. What exists (families, canonical location + duplicates)

| family | status | canonical | duplicates / notes |
|---|---|---|---|
| binance_vision_klines_um_1h_panel (BTC/ETH/BNB/XRP/ADA/SOL) | AVAILABLE_VALIDATED | ethusdt-open-search-v2 data_local/vision (committed per-zip sha manifest, 572 entries) | srlv-cx-c1 (80/80/79/72), ethusdt-v1, pws-cx-solusdt-c1 (72, byte-identical), pws-cx-bnbusdt-c1 (79, LIVE owner) |
| funding_settled_8h_usdm (fapi) | AVAILABLE_VALIDATED | per-symbol: SOL pws-sol (6,580), BNB pws-bnb (7,261, committed at HEAD), BTC srlv census (7,643 rows from 2019-09-10), trackb bundle (6,819, sha-pinned) | ETH 7,305 (EOSV2 census) |
| funding_rate_vision_monthly_crosscheck | AVAILABLE_VALIDATED | EOSV2 fundingRate_um_ETHUSDT (80) | trackb (80), srlv, btc-h4-edge-search |
| bookticker_spread_census_solusdt_um | AVAILABLE_VALIDATED | pws-cx-solusdt-c1 (6 zips ≈12G, p50 0.469 bps) | none — only measured spread authority in program |
| ws_collectors_coinbase_kraken_deribit | AVAILABLE_VALIDATED | ~/.my-quantitative-data/crypto-ng4-ws (146 shards, 2.17G, sha-chained) + data-edge-unlock-v1 (19 shards, 440M) | depth = 8.25h + 42min TOTAL, PROSPECTIVE-only |
| erp1_trackb_spot_perp_1h_planes | AVAILABLE_VALIDATED | erp1-trackb-cohort-1 (spot 109 zips from 2017-08, perp 80, per-file sha manifest) | spot floor predates everything else in program |
| catalog_binance_perp_bar_15m_btc_eth | AVAILABLE_UNVALIDATED | root catalog/ (4 parquets, 2024-08..2026-08, 10M) | no manifest |
| jrv_regime_decisions_btc_h1_h4 | AVAILABLE_UNVALIDATED | regime-strategy-mapping-v1 (committed manifests, cache_integrity_ok) | derived; upstream raw absent (next row) |
| binance_vision_klines_btc_h4_raw | NOT_RUN | raw 4h bytes NOT located in any surviving tree | BTC-H4-* cycles consumed transient bytes via market-data-plane |

Live-owner metadata-only (F5, no bytes read/hashed):
- pws-cx-bnbusdt-c1 (GO-1 in flight): committed HEAD records only — 79 kline
  zips 2020-02..2026-08, funding 7,261 rows, spread census
  NOT_RUN_DISK_CONSTRAINT (7GB < 25GB required, fail-closed).
- crypto-historical-replication-3f-v1: committed p0_feasibility_table.md —
  measured floors: funding global 2020-07-18T08:00:00.001Z, basis 15m
  BTCUSDT 2020-06-01 (EMPTY 2019-11-25), indexPriceKlines 2020-06-01,
  vision mark/index archives from 2020-01, 20-symbol 15m kline floors.
- LIVE-DATA-GATEWAY-V1: G1 evidence (2026-09-21) — canary legs A/B;
  corroboration of Binance fapi HTTP 418/403 ban episode on the shared IP
  (cost/limit fact for any future REST campaign).

## 2. What is validated (this cycle's own re-measurement)

- crypto-ng4-ws: 12/12 sampled shards sha256+bytes ALL_MATCH vs
  `raw/manifest.jsonl`; span measured from boundary lines
  2026-09-16T16:36:12Z → 2026-09-17T00:51:11Z; manifest totals 146 rows /
  2,168,295,455 B; 3 rows carry gap_count>0 (disclosed in manifest).
- data-edge-unlock-v1 raw: 19/19 manifest rows; 8/8 sample ALL_MATCH;
  span 2026-09-17T02:49:32Z → 03:31:43Z.
- pws-cx-solusdt-c1 (TERMINAL): 8/8 sampled files ALL_MATCH vs committed
  INVENTORY.md — funding JSONs x2, klines zips x4, bookTicker zips x2
  (7.24s wall under /usr/bin/time). The cycle's own committed recount
  (52,145 bars, 120 missing bars = 2 maintenance windows; funding n=6,580
  with 101 FTX-week non-8h spacings; spread p50 0.469 bps) is inherited.
- ethusdt-open-search-v2: 7/7 sampled zips ALL_MATCH vs committed
  freezes/staged_manifest.json (one random month per series, 572 entries);
  census build_pass=true, funding 7,305 settlements.
- erp1-trackb-cohort-1: 3/3 sampled zips ALL_MATCH vs committed
  staging_manifest_v1.json.

## 3. What is missing — gap candidates

Each row: why needed / hypothesis class opened / prior kill it fixes /
falsifying control / priority / cost estimate. "Không suy ra order book hay
forced flow từ nến" applies to every OI/liquidation/L2 item below.

### G1. PIT OI / liquidation / L2 multi-year corpus (BLOCKED_DATA class)
- Why: 4 crypto families died on exactly this lever (OILEV V11, OILEV-V2
  V12, OITD V13, OICYC V14 — negative, DSR≈0) but they ran on
  PROSPECTIVE/rolling windows, never multi-year PIT. A real PIT corpus
  re-opens the whole forced-flow class honestly. V14 once staged OI bytes;
  the archive is now ABSENT (see I-1) — even the historical copy is gone.
- Class: forced-flow / liquidation-cascade mechanisms.
- Prior kill: OILEV/OITD/OICYC negative results are UNDETERMINED w.r.t.
  PIT data quality, not evidence of absence of edge.
- Falsifying control: licensed PIT vendor sample cross-checked against
  Binance rolling openInterestHist over an overlap month; disagreement
  beyond tolerance kills the corpus before any scoring.
- Priority: HIGH (owner decision + money — no keyless path; also requires
  L-PIT license screen first, P-25). Cost: vendor-dependent; own-capture
  alternative ≈ 250MB/day/market and years of waiting. Absolutely no
  candle-implied substitute (prohibition above).

### G2. Spot–perp basis + mark/index PIT corpus for majors (partial: CHR3F)
- Why: basis families (BASISLV-PREMFADE) need PIT mark/index/basis;
  CHR3F measured floors (basis 2020-06-01, mark/index archives 2020-01)
  but its full staging is in-flight and owned by a live cycle.
- Class: carry/premium-fade; cost-model mark price realism.
- Prior kill: 2019 NOT_RUN verdict (basis endpoint empty at 2019-11-25,
  funding floor 2020-07-18, universe unsatisfiable) — now measured, not
  assumed.
- Falsifying control: CHR3F's own stamp-level P0 census (any failed
  scheduled stamp folds partial to NOT_RUN_IDENTITY).
- Priority: HIGH (already funded/running — mostly an A1 integration item
  to inventory CHR3F's output when it lands). Cost: already being paid.

### G3. Settled vs FORECAST funding (premiumIndex history) — true gap
- Why: the owner directive names "funding đã settle so với funding dự báo".
  Settled exists and is validated (8h); no forecast/premium-index history
  is staged anywhere (verified). Without it, funding-crowding strategies
  cannot separate the predictable component from the realized surprise.
- Class: funding-crowding / premium-mean-reversion.
- Prior kill: none — family never attempted for lack of data.
- Falsifying control: stage premiumIndexKlines 15m for BTC/ETH over 6
  months; verify realized premium at fundingTime == settled rate to
  tolerance; if the channel's history floor is < 2 years, cap the class.
- Priority: HIGH (cheap: keyless REST probe + staging ≈ a few hundred MB
  for majors; fits the ≤2.0GB cycle budget if A1 chooses to probe).
- Cost: probe ≈ ≤300 requests (probe-budget class); storage ≈ 200-500MB.

### G4. BTC/BNB spread census gaps (cost authority holes)
- Why: only SOL has a measured spread census (p50 0.469 bps). BNB census
  is NOT_RUN_DISK_CONSTRAINT (needs ≥25GB free; 6.9GiB free today). BTC/ETH
  spread rests on DECLARED 5bps+1tick, not measurement — the exact
  class of assumption that killed three generations at broker-cost
  authority.
- Class: after-cost realism for every crypto scored cell.
- Prior kill: broker-cost-authority kill class (BTC/ETH still exposed).
- Falsifying control: 2-month bookTicker census per symbol recomputed
  like SOL's; if p50 >> 5bps declared, BTC/ETH cost book is wrong.
- Priority: HIGH for BTC/ETH (owner action: free ≥25-40GB disk), MEDIUM
  for BNB. Cost: ≈2GB/month/symbol compressed; 2 months ≈ 4GB×2 symbols.

### G5. Exchange fee/rules history over time — true gap
- Why: fees changed across 2020-2026 eras (VIP tiers, promos); the program
  prices every era at a flat declared 5bps+1tick. Any regime-era family
  inherits an unmodeled cost drift.
- Class: cost-model realism; survivorship of high-turnover families.
- Prior kill: none (never attempted).
- Falsifying control: reconstruct a dated fee timeline from announcements;
  test whether any terminal family's verdict flips under tier shifts.
- Priority: MEDIUM (manual capture, no clean API; owner/legal posture
  needed for page archiving).
- Cost: low bytes; high human-time; archive-ToU screening by L-PIT first.

### G6. Cross-venue (Coinbase/Kraken/Deribit) historical depth — WAITING_COVERAGE
- Why: only 8.5h of forward capture exists (validated). Lead-lag /
  cross-venue basis families need months. The 14-day floors contract
  (DEU-V1 Lane C) is the recorded gate; it is not yet satisfied.
- Class: cross-venue lead-lag, venue fragmentation.
- Prior kill: DEU Lane C coverage-floor verdict.
- Falsifying control: run the collector 14 continuous days; recount
  floors; if still unmet, family stays WAITING_COVERAGE (not FAILED).
- Priority: MEDIUM (cheap to start — collector exists and is validated —
  but slow to pay off; disk 250MB/day/market must fit the owner's
  storage plan). Cost: ≈3.5GB per 14-day run at current venue mix.

### G7. aggTrades microstructure corpus (V16 revival candidate)
- Why: V16's P0 precheck ran once (232s FINISHED) but the worktree was
  removed and no archive exists; the "last keyless family" is unmeasured.
- Class: after-cost incremental / trade-flow.
- Prior kill: V16's own BLOCKED_DATA-or-selection fork — never resolved.
- Falsifying control: re-run the V16 per symbol-month size/RSS census
  under today's disk (6.9GiB free) — expected BLOCKED_STORAGE.
- Priority: LOW until disk is freed (blocked by the same constraint as G4).

## 4. Incidents / findings for A1

- **I-1 (report to owner): P-13 manifest-vs-disk drift.**
  `~/staging_backups/SHA256SUMS.txt` (14 entries, committed reference in
  `research/control/staging_backups_manifest.md`) lists 8 archives that
  are ABSENT from disk, including `crypto-v14_full.tar.gz` ("V14 full
  forest (staged basis/OI/klines)") and — in the empty
  `cleanup_2026-09-07/` — `legacy_root_data.tar.gz` (337M, contained
  oi_data/ 98M, funding_data/ 11M, derivatives_data/ 8.4M,
  catalog_live_crypto/ 129M) and `forex-free-v5_full.tar.gz` (224M).
  Absence measured by `[ -f ]` checks; cause not attributable from this
  lane. Consequence: the historical OI copy is unrecoverable locally.
  Owner decision needed (accept loss + annotate ledger, or restore from
  origin branches where possible — staged data was gitignored, so
  restoration via `git worktree add` is NOT possible for these bytes).
- **I-2 (minor, self-reported): transcription slip during SOL sampling.**
  My first sample list mis-aligned one inventory row (checked 2022-01.zip's
  sha against 2022-02.zip). Caught and corrected by independent `shasum
  -a 256` re-hash + duplicate-copy cross-check; final verdict for all 8
  files is ALL_MATCH. No data was misjudged.
- **I-3 (evidence note): BNB data_local is untracked in its worktree right
  now** (live GO-1 session writing). All BNB numbers cited here come from
  COMMITTED files at HEAD `acdd4649` (C1_machine_*), per F5; the untracked
  INVENTORY.md was read as metadata only and is so labeled.

## 5. Measured-cost pointers carried for L-COST (from committed artifacts)

- BTC funding measured 11.798%/yr = 7.824× frozen constant (BTC-H4-EDGE
  record, carried per packet); SRLV 11.81 / 13.96 %/yr; SOL funding sign
  autocorr +0.853.
- BTC settled funding earliest row 2019-09-10T08:00Z (srlv census, 7,643
  rows); global 7-symbol floor 2020-07-18T08:00:00.001Z (CHR3F p0).
- Spread: SOL p50 0.469 bps (measured, 12G corpus); BNB NOT_RUN
  (disk-constraint); BTC/ETH DECLARED 5bps+1tick (not measured).
- Binance fapi shared-IP ban episodes (HTTP 418→403→418) observed
  2026-09-21 (LIVE-DATA-GATEWAY-V1 G1 evidence) — budget REST campaigns
  accordingly.

## 6. Compliance

- Zero network requests. No `.env`/secrets read. No sealed/holdout content
  read. Writes confined to `research/control/DATA-FOUNDATION-FX-CRYPTO-
  STOCKS-V1/cx/` in this worktree. No heavy job (largest chunk: 12GB-hash
  of 2 zips, 7.24s wall, measured under /usr/bin/time; all chunks
  <<10min CPU / <<1GB temp). Other cycles' control dirs read-only; plans/
  read-only. ps checked before touching ETHUSDT dirs (no writer process;
  inherited manifests preferred, sampling permitted by packet).
