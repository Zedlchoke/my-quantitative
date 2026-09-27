# LANE S REPORT — EVENT-MECHANISMS-V1 data authority (2026-09-27)

Lane: S (data), worktree
`.worktrees/event-mechanisms-v1/integration`, branch
`orca/event-mechanisms-v1-integration`, started at HEAD `656c106a` (verified).
Network: `data.sec.gov/submissions/**` ONLY, UA
`MyQuantitative Research hoangminhlong@localhost (event-mechanisms lane S)`,
≤8 req/s (0.15 s spacing) + 2 s pause every 50 requests, no 4xx retries.

## Headline numbers

| Task | Verdict | Key numbers |
|---|---|---|
| S1 form-4 layer | **PASS** | stream pin `6ac2cd5b…742b2` EXACT; 546,039 rows; manifest pin `5d351623…` EXACT; 345,150 XMLs restored; sample 25/25 EXACT |
| S2 price panel | **PASS** | NG6 panel chosen: RAW OHLCV present; 2,169 files; 3,209,972 rows; per-file digest manifest committed |
| S3 div/splits | **PASS** | 2,168 + 2,168 files; samples 25/25 + 25/25 EXACT; schema recorded |
| S4 N4 identity map | **PASS** | 2,178 rows / 2,168 tickers; 0 unresolved; 1,898 form4-corroborated; 12/12 alive ticker-verified at SEC; 13/13 dead served w/ empty tickers[] + consistent names |
| S5 submissions staging | **PASS** | 2,178/2,178 CIKs fetched (100% ≥ 95% bar); 54,941 A1 events; 2,156 issuers with ≥1 event (98.99%) |
| S6 mutation check | **PASS** | 20/20 byte-identical re-fetches; 0 acceptance mutations → NO_MUTATION |
| S7 fixtures | **DONE** | 3 fixtures (after-close, pre-open, DST fall-back) with expected strata + sequencing |

**Network budget: 3,063 / 6,000 requests used** (25 N4-verify + 2,508 staging
+ 330 page recovery + 20 mutation; counter reconciles 1:1 with the 3,063-line
fetch_log). Shards: 2,688 files under `submissions/` (gitignored).

## Digest verification results (all recomputed, never trusted)

| Artifact | sha256 | vs authority |
|---|---|---|
| stocks-free-v13_integration.tar.gz | `57a9d42c…3fefc` | EXACT vs SHA256SUMS.txt.cleanup_2026-09-17 |
| stocks-ng6_integration.tar.gz | `808ca4f1…3824a` | EXACT (dispatch pin) |
| form4_stream.jsonl | `6ac2cd5bdd62566efe106b46de715030e9a8a940cb90f5a991df5f05ba6742b2` | **EXACT vs G2 pin** (fail-closed gate passed) |
| substrate_manifest.json | `5d351623675f71a9950d0e290b1fafff89901265f18bf6c687660e96285ea26b` | EXACT vs G2 manifest pin |
| substrate_manifest_digest.json | `941ba6c3…b9c9c` | self-consistent |
| form4_xml full extraction | 345,150 files | count EXACT; seed-99 sample 25/25 sha EXACT (`form4_xml_sample25.csv`) |
| cohort_v9.json (lineage source) | `6a95401ff84bff2144ac3c0b9426a6fa86daf3dde8d478195666249e3fa2aa62` | EXACT vs NG6 cohort_manifest expected_sha256 |
| eodhd_div / eodhd_splits | seed-7 samples 25/25 + 25/25 | EXACT vs substrate_manifest |
| a1_events.jsonl (staged product) | `a6a5bb6eb39981685f2caf9b3dc1ce5e0c683926facbe2d778014e14ec979401` | recorded in SHA256SUMS.staged.txt |
| n4_map_v1.jsonl | `537cd5afe67dd5a280b377213a69f77747df6ff0b8f55329038bbf105b665fd8` | recorded |

## Price-plane choice (R2-5 law)

NG6 panel (`data_raw/stocks_ng6_eod/`, restored from the NG6 archive) carries
RAW OHLCV (`date, open, high, low, close, volume`; vendor `adjusted_close`
PRESENT and FORBIDDEN per R2-1 — not used anywhere). 20-ticker sample
(seed 42) spans 2015-01-02..2026-09-15 with death-inclusive short histories
(e.g. HRLLL 5 rows). **Chosen plane: NG6 panel.** The eod_cache fallback was
NOT needed and NOT touched (read-only rule respected); the N9 re-pin is
therefore discharged only for the CHOSEN surface (this panel, digest
manifest `ng6_panel_digest.txt`) — the cache-level N9 stays closed-by-choice,
not re-pinned. Consequence recorded: any future re-open of the cache surface
must re-pin before use.

## A1 event set (staged, pre-GO boundary respected)

- `a1_events.jsonl`: **54,941 rows** = {cik (CIK##########), ticker, form,
  accession, acceptance_utc, filing_date, report_date}; forms EXACTLY
  `10-Q` (40,926) / `10-K` (14,015); acceptance window measured
  2015-01-05..2026-06-29 (all inside 2015-01-01..2026-06-30); 0 duplicates.
- Per-fold populations: F1 2015-2018: 23,918; F2 2018-2021: 16,224;
  F3 2021-2023: 9,022; F4 2023-2026H1: 5,777 (well above the ≥100/fold,
  ≥400/anchor floor feasibility bars — population numbers only, no
  expectancy/PnL computed, per R2-6).
- 2,156/2,178 cohort CIKs (98.99%) have ≥1 window event; the 22 without are
  post-window registrations / shells (gap census in n4 rows; not a fetch gap).
- Form-string census: 326 distinct form strings observed across cohort
  filings (`form_string_distribution.txt`); variant forms
  (`10-Q/A` 2,279 all-time / 1,016 in-window; `10-K/A` 3,161 / 1,955;
  `10-KT`, `10-QT`, `10-K405`, …) EXCLUDED per R2-3 exact-match law.

## Coverage & gaps

- CIK fetch coverage: **100%** (2,178/2,178; bar was 95%). No 403s on
  data.sec.gov; the only 404s were my own malformed page URLs (fixed and
  recovered — incident S5-I1 below); residual gap census is EMPTY.
- Identity coverage: 0 unresolved rows; 10 tickers carry 2 members each
  (`ticker_reuse_risk`, never silently merged per cohort identity law).
- Panel: every cohort ticker has a price file; `SPY` is the sole extra
  panel series (benchmark).

## Incidents

1. **S5-I1 (fixed in-lane):** first pagination pass built paged-file URLs as
   `CIK…-CIK…-submissions-00N.json` (the `files[].name` field already
   contains the CIK prefix) → 330 clean 404s, logged, no retries. Impact:
   window rows for 330 CIKs whose `recent` block does not reach 2015 were
   incomplete. Recovery pass (`recover_pages.py`) with corrected URLs fetched
   all 330 (0 residual gaps) and appended the missing rows; events file then
   normalized + deduped (0 duplicates found). Evidence: `gap_census.json`
   (original 404s), `gap_census_recovery.json` (empty), `fetch_log.jsonl`.
2. **S5-I2 (fixed in-lane):** initial `a1_events` rows carried `cik` as int;
   post-run normalization rewrote to `CIK##########` string form (matching
   n4_map + shard naming). Digest of the final file is the pinned one.
3. No other incidents. No 4xx besides I1; no retries; no forbidden hosts.

## Known limitations (for engine lane + G-gates)

1. Price plane carries vendor `adjusted_close` on disk; it is FORBIDDEN
   (R2-1). The engine must read only `open/high/low/close/volume`. (Pinned by
   digest; enforcement is a code-review concern, not a data concern.)
2. EODHD availability timing (post-close posting) remains DECLARED-not-
   verified (G2 R3 carries it); decision-at-next-session-open law unchanged.
3. `tickers[]`-based verification is only meaningful for alive issuers (dead
   issuers serve empty arrays by SEC design) — dead-name identity rests on
   the sha-pinned census lineage (verified `6a95401f…`) + name consistency.
4. Cost plane remains PROXY-PRIOR (G2 R5); untouched this lane.
5. `www.sec.gov` raw-doc estate stays BLOCKED_NETWORK_403 (owner action
   GA-1); nothing in this lane needs it.
6. Sessions/holidays: fixtures pin ET/DST logic; the actual holiday calendar
   is implied by per-name bar dates (R2-4: a session date = a date on which
   the name has a bar) — engine must use bar dates, not a hardcoded calendar.

## Outputs

- `.staging_eventmech/` (worktree root): `n4_map_v1.jsonl`, `a1_events.jsonl`,
  `n4_verification.json`, `fetch_log.jsonl`, `net_budget.json`,
  `form_string_distribution.txt`, `gap_census.json`,
  `gap_census_recovery.json`, `mutation_check_raw.json`,
  `ng6_panel_digest.txt`, `divsplits_SHA256_sample.csv`,
  `form4_stream.sha256`, `substrate_manifest_digest.json`,
  `SHA256SUMS.staged.txt`, `fixtures/` (3), plus gitignored raw restorations
  (form4 stream+XMLs, NG6 panel, div/splits, submissions shards).
- `lane_s/`: `RESTORE_EVIDENCE.md`, `N4_REPORT.md`, `MUTATION_CHECK.md`,
  `S7_FIXTURES_README.md`, `form4_xml_sample25.csv`, this `REPORT.md`.
