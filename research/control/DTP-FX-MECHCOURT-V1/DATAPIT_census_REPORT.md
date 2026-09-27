# DATAPIT census REPORT — DTP-FX-MECHCOURT-V1 — Lane D (data/PIT + cost census)

- Lane: D (data/PIT + cost census), cycle `DTP-FX-MECHCOURT-V1`
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/dtp-fx-mechcourt-v1/integration`
  (branch `orca/dtp-fx-mechcourt-v1-integration`)
- Measured/run: 2026-09-27 (all bytes re-verified fresh by Lane D, independent of Lead's §1 sketch)
- `actual_start_sha` = `051aaae002615a68a0ee1af0d50e97325c69a930`
- Scope guard honored: ONLY open-spread cost quantities (s_open) computed. No
  price-drift, return, premium or PnL statistic appears anywhere in this census.
  AUDUSD/USDCAD parquets NOT opened beyond parquet footer metadata (sealed
  2026-H1 rows untouched). Shadow worktree read-only.

## 0. Verdict summary (data plane)

| # | Item | Status | One-line evidence |
|---|---|---|---|
| 1 | FX corpora (EURUSD/GBPUSD/USDJPY bars15 + raw M1 bi5) | **PASS** | 3 parquets sha-pinned below; raw 2092 BID + 2092 ASK bi5 per pair |
| 2 | AUDUSD/USDCAD raw absence + sealed ANC only | **PASS** | 0 bi5 anywhere; data_local = manifests + census/probe JSONs + 2×1H ANC parquet (footer-read only) |
| 3 | Rates daily-only; intraday rates = 0; futures = 0 | **PASS** | NY Fed + OFR files last obs 2026-09-14, all `frequency: Daily`; futures raw = 5×0-byte html stubs; 0 market bytes in fx_futures control dirs |
| 4 | Venue-2 (second feed) = 0 bytes; IBKR probe evidence | **PASS** | sanitized_result: 5 pairs, n_valid=0/357 cells, minTick 0.5 pip, BID=-1/ASK=-1 UNSET (VERDICT_session2.md) |
| 5 | PIT macro ledger (131 events) | **PASS (with honesty ceiling)** | 131 events 2021-01-13→2025-12-18; minute-exact page-verified = 10/131; structured consensus vintages = ABSENT; revision vintages = ABSENT (retrospective consensus mentions exist in free text only) |
| 6 | Cost artifacts on disk (session curve + ERP1 census) | **PASS** | session_spread_curve.json PINNED sha-pinned; ERP1 census headline p50s reconcile with INTAKE pinned numbers |

## 1. FX corpora — byte verification (Item 1: PASS)

### bars15.parquet (derived, s_open source for the census)

| Pair | Path | Bytes | sha256 | Rows | First ts (UTC) | Last ts (UTC) |
|---|---|---|---|---|---|---|
| EURUSD | `/Users/hoangminhlong/my-quantitative/.worktrees/fx-rangefade-2m-shadow-v1/research/control/FX-RANGEFADE-2M-SHADOW-V1/data_local/EURUSD/derived/bars15.parquet` | 4,827,229 | `9fe9e4b1598345d1b40b5d325b1faf5f9938bbb5ab2aa379a812bfcba5c9f2bd` | 136,485 | 2021-01-03 22:15 | 2026-09-23 23:45 |
| GBPUSD | `/Users/hoangminhlong/my-quantitative/.worktrees/fx-majors-search-v1/integration/research/control/FX-MAJORS-SEARCH-V1/data_local/GBPUSD/derived/bars15.parquet` | 5,081,111 | `fe90677e74fc0f09ff5561e72fbd31c65d71dd17fe7c64b7bcad41ed0c11a978` | 137,135 | 2021-01-03 22:00 | 2026-09-23 23:45 |
| USDJPY | `/Users/hoangminhlong/my-quantitative/.worktrees/fx-majors-search-v1/integration/research/control/FX-MAJORS-SEARCH-V1/data_local/USDJPY/derived/bars15.parquet` | 4,954,026 | `99e276df92faaf232ff9314c9f96abc171675ff7a67b14e95c93c4390da9de7c` | 137,376 | 2021-01-03 22:00 | 2026-09-23 23:45 |

Column schema (identical all three): `ts (timestamp[ms, tz=UTC])`, `b_o b_h b_l
b_c a_o a_h a_l a_c s_open s_close` (double). EURUSD row count 136,485 matches
INTAKE.md exactly. All three corpora end 2026-09-23 23:45 UTC (through
2026-09-23 as INTAKE states).

### Raw M1 bi5 corpus (alongside, per pair)

`M1/BID/` and `M1/ASK/` exist for all three pairs: **2092 .bi5 files each side**
(4,184 per pair, 12,552 total). Directory sizes: EURUSD M1 = 41 MB, GBPUSD M1 =
41 MB, USDJPY M1 = 44 MB. `m1_manifest.json` present per pair. Provenance:
Dukascopy M1 bid/ask (ERP-FOREX §2 authority source; SINGLE_SOURCE_PANEL).

## 2. AUDUSD/USDCAD raw absence (Item 2: PASS)

- `find` for directories named AUDUSD/USDCAD under `/Users/hoangminhlong/my-quantitative/.worktrees`:
  **0 matches; 0 .bi5 files**. No AUDUSD/USDCAD .bi5 anywhere under
  `~/.my-quantitative-data` either.
- `data_local/` at
  `/Users/hoangminhlong/my-quantitative/.worktrees/erp1-tracka-cohort-1/repro_twin/research/control/ERP1-TRACKA-COHORT-1/data_local/`
  contains ONLY (bytes):
  - `derived/bars1h_ANC_AUDUSD.parquet` 1,215,240 B; `derived/bars1h_ANC_USDCAD.parquet` 1,306,817 B
  - `derived/census_AUDUSD.json` 120,145 B; `derived/census_USDCAD.json` 120,024 B
  - `derived/probe_AUDUSD.json` 65,264 B; `derived/probe_USDCAD.json` 65,336 B
  - `derived/plane_diff_AUDUSD.json` 800 B; `derived/plane_diff_USDCAD.json` 799 B
  - `duka/m1_manifest_AUDUSD.json` 813,612 B; `duka/m1_manifest_USDCAD.json` 813,757 B (manifests only — raw bi5 excluded by committed `.gitignore`)
  - `probe/.gitignore` only (probe raw bytes machine-local, none present)
- Sealed ANC parquets: read via **parquet footer metadata ONLY** (no row
  contents opened): AUDUSD rows=30,420, ts footer_min=2021-01-03 23:00 UTC,
  footer_max=**2026-06-30 20:00 UTC**; USDCAD rows=30,386, footer_max=**2026-06-30
  23:00 UTC**. The sealed 2026-H1 rows are present inside these files and were
  NOT accessed beyond footer statistics (one-look lineage preserved).

## 3. Rates plane (Item 3: PASS — daily only, zero intraday, zero futures)

Daily files present (last observation 2026-09-14 in every series, i.e. EFFR/SOFR through 2026-09-14 as INTAKE says):

- `~/.my-quantitative-data/free-data-frontier-v1/raw/nyfed_markets/` (20 KB total):
  `rate_bgcr.json`, `rate_effr.json`, `rate_obfr.json`, `rate_sofr.json`,
  `rate_tgcr.json` — each a small JSON whose latest record has
  `effectiveDate: 2026-09-14` (BGCR 3.60, EFFR 3.63, OBFR 3.63, SOFR 3.62, TGCR 3.60).
- `~/.my-quantitative-data/free-data-frontier-v1r1/raw/ofr_stfm/` (276 KB total):
  `inventory_mnemonics.json` + `series/FNYR-{BGCR,EFFR,OBFR,SOFR,TGCR}-A.json`
  — each series declares `"frequency": "Daily"`; last date 2026-09-14 (EFFR/OBFR
  from 2016-03-01; BGCR/SOFR/TGCR from 2018-04-02).

ZERO intraday rates bytes: no other rates file exists on the rates plane; the
OFR/NY-Fed corpora are daily-only by declaration and by file inventory.

ZERO futures bytes: `~/.my-quantitative-data/fx-futures-frontier-v1/raw/` holds
exactly 5 files — `lane-a2/{M6E,M6B,MCD,MJY,M6A}/product_page.html`, **each
0 bytes** (empty stubs from the 2026-09-17 BLOCKED_TRANSPORT attempt; no market
bytes). All `fx_futures_frontier_v1` control dirs (root + every worktree):
**0 files matching *.bi5/*.parquet/*.csv**. No uppercase `FX-FUTURES-FRONTIER-V1`
market-data dir exists. CME SNI-block evidence (L-FXFF-1) stands; intraday fed
funds/SOFR futures for mechanism B remain 0 bytes.

## 4. Venue-2 (Item 4: PASS — second feed = 0 bytes; probe evidence recorded)

Probe dir `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/broker_cost_probe_FX_majors_2026-09/`:
committed evidence = `EVIDENCE_sanitized_2026-09-26.json` (7,549 B),
`PROBE_CONTRACT_DIAGNOSIS.md`, `probe_fx_majors.py`, `probe_fx_majors_raw.py`,
`SESSION_REPORT_1_BLOCKED.md`, `VERDICT_session2.md`. Machine-local
`data_local/` (root checkout) holds exactly: `sanitized_result_20260926T054652Z.json`
(4,742 B), `sanitized_result_20260926T055513Z.json` (4,742 B),
`raw_ticks_20260926T055513Z.jsonl` (151,185 B; raw sha256 in-sanitize
`18422a56e1641498efd20ee85862df512d8c5cfd708c804228b82311834166b0` re-verified on disk).

Sanitized result (`20260926T055513Z`, paper session, raw-ibapi): five pairs
EURUSD/GBPUSD/USDCAD/AUDUSD/NZDUSD, exchange IDEALPRO, **minTick 5e-05 = 0.5
pip** each; stream 360 s, 357 grid cells, **cells_with_obs = 0**, per pair
**n_valid = 0 / n_invalid = 357**, every spread percentile null. The IBKR tick
sentinel on the wire is **BID=-1, ASK=-1 (UNSET)** per `VERDICT_session2.md`
("bid/ask=-1 ×5 pairs; 0 valid obs"); the stored jsonl normalizes the sentinel
to `null` (1,785/1,785 rows `"bid": null, "ask": null, "valid": false`).
`BLOCKED_BROKER_COST_AUTHORITY` stands. Second venue = 0 bytes; mechanism C's
two-leg requirement is unmet.

## 5. PIT macro ledger (Item 5: PASS with honesty ceiling)

File:
`research/control/ERP1-TRACKA-COHORT-1/failres/failres_events_PROVENANCE.json`
(schema `failres_events/provenance@1`, 42,725 B; twin timeline
`failres_events_timeline.jsonl`, 1 header + 131 event rows).

- **Event count: 131** (F1 2021-01-13 → F5; last event_time_utc 2025-12-18T13:15Z).
- **Span: 2021-01-13T13:30:00Z → 2025-12-18T13:15:00Z** (5 calendar years; 2021:30, 2022:45, 2023:11, 2024:24, 2025:21).
- **Minute-exact verified honesty ceiling: 10/131** — events with
  `fetch_status = FETCHED` (primary page retrieved and verified this session):
  FOMC 2021-06-16, FOMC 2021-11-03, CPI 2021-11-10, CPI 2022-01-12, CPI
  2022-06-10, FOMC 2022-06-15, ECB 2022-07-21, FOMC 2022-07-27, FOMC 2022-12-14,
  FOMC 2024-09-18. (11th `PRIMARY_PAGE_VERIFIED` row, HICP flash 2022-07-29, is
  SEARCH_SURFACED, not FETCHED.) The timeline legend marks 106 events "EXACT"
  but that label means minute-level *from source or canonical schedule* — the
  page-verified subset is 10, and 84 events are NOT_FETCHED_CANONICAL
  (schedule-derived). For mechanism-B purposes the usable PIT floor is 10/131.
- **Consensus vintages: ABSENT** as structured PIT fields (no consensus value
  available at release time). Caveat recorded for A7: 92 events mention
  consensus retrospectively inside free-text `expected_vs_actual` (e.g.
  "consensus: hold", "vs consensus ~1.7% (Reuters poll, secondary)") — these
  are post-hoc annotations, not vintages with `available_at`, and cannot serve
  as entry conditioning.
- **Revision vintages: ABSENT** (zero occurrences of revision fields anywhere in
  provenance or timeline).
- Labels carried: `DIAGNOSTIC_OUTCOME_EXPOSED`,
  `FAILURE_ROOT_CAUSE_RESEARCH`, `EVENTS_OVERLAY_ONLY_NOT_CAUSAL_EVIDENCE`.
  source_class: PRIMARY 110 / SECONDARY_RECONSTRUCTION 12 / WIRE_CONTEMPORANEOUS 9.

## 6. Cost artifacts on disk (Item 6: PASS)

### EURUSD session spread curve (pinned)

`/Users/hoangminhlong/my-quantitative/.worktrees/fx-rangefade-2m-shadow-v1/research/control/FX-RANGEFADE-2M-SHADOW-V1/session_spread_curve.json`
(4,305 B, sha256 `de02abf16b142a6eab0b41bd92fdc4a0c04994fa50a0a5842dba3dad809e3d74`,
schema `phorec.session_spread_curve@1`, status `PINNED_CENSUS_OWNER_OPTION_1_2026-09-25`,
pinned 2026-09-25T05:05Z). Pinned census values (pips, session medians,
UTC-hour buckets, stress ×2.0):

- EURUSD: Asia 0.3, London 0.3, Overlap 0.3, NY 0.3, Rollover 0.9
- GBPUSD: Asia 0.9, London 0.8, Overlap 0.8, NY 0.8, Rollover 2.3
- Declared schedule (DECLARED class): fee 0.2 bps/side, slip 0.1 pips/side;
  fill quality declared unmeasurable on M1/15s corpora (stress-covered ×2.0).

### ERP1 census JSONs (sealed-plane cost authority; headline only)

- `census_AUDUSD.json` sha256 `d337ff2c4e499238f6552c525cebf2027bbd5f2b876babc4e3e086fd09233473`:
  overall_open p50 1.0; session-open p50s: asia 1.0, london 1.0, ny_overlap 1.0,
  ny_late 1.0, **rollover_21_22 2.0 (p99 12.304)**, **sunday 4.6**.
- `census_USDCAD.json` sha256 `27958f5a6b67ae017dea8bf35cf006868249926b03ff518ceb7663725ff35758`:
  overall_open p50 1.2; session-open p50s: asia 1.3, london 1.2, ny_overlap 1.2,
  ny_late 1.2, **rollover_21_22 2.3 (p99 16.7)**, **sunday 6.8**.
- These reconcile with the INTAKE pinned numbers (rollover p50 2.0/2.3,
  p99 12.3/16.7; sunday 4.6/6.8). Stressed RT ×2.0 = 3.6/4.4 pips stands.

## 7. Fix-window spread census (plan §6 preregistration, executed exactly)

- Script: `research/control/DTP-FX-MECHCOURT-V1/fixwindow_census.py`
  (sha256 `3c3b7b29cdc10b31b8dd5475cc8e616dec919d9e50d69c8d66d590b573de9d6e`)
- Output: `research/control/DTP-FX-MECHCOURT-V1/fixwindow_spread_census.json`
  (schema `dtpfx1/fixwindow_spread_census@1`, sha256
  `15efee6ac2f58375fb47a22ca30389b3d85f155dec9d03ae7de19d7db5cf38e0`)
- Census labels (carried in JSON and here): **SINGLE_SOURCE_PANEL · PAPER_TIER ·
  FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK**
- Quantity: s_open = a_open − b_open at 15m bar open, pips (pip=0.0001
  EURUSD/GBPUSD; 0.01 USDJPY). London hour = bar-open instant in Europe/London
  via stdlib zoneinfo (BST/GMT verified: 2026-03-29T01:00Z→02 London, 2026-10-25T01:00Z→01 London).
- Day-sets (per pair, per corpus, 69 months each): ME1 = 69 days, ME2 = 138
  days, MID (days 13–16) = 236 days. Percentile convention: linear
  interpolation on sorted sample (numpy 'linear'); reported pips rounded 4dp.
- Verification: every published bucket n>0 (non-vacuous); 5 buckets per pair
  independently recomputed via a second code path (pure-stdlib zoneinfo + own
  percentile) — all MATCH. n_nonpos = 0 in every published bucket
  (11,609 + 11,695 + 11,411 published observations, zero non-positive spreads).

### Census tables

#### EURUSD

London-local hour (bar open) x day-set; s_open in pips.

| hour | set | n | p25 | p50 | p75 | p90 | p99 | n<=0 |
|---|---|---|---|---|---|---|---|---|
| 13 | ME1 | 232 | 0.2 | 0.3 | 0.5 | 0.99 | 2.907 | 0 |
| 13 | ME2 | 472 | 0.2 | 0.3 | 0.5 | 0.9 | 2.787 | 0 |
| 13 | MID | 788 | 0.2 | 0.3 | 0.5 | 0.8 | 3.026 | 0 |
| 14 | ME1 | 232 | 0.2 | 0.3 | 0.4 | 0.5 | 0.769 | 0 |
| 14 | ME2 | 470 | 0.2 | 0.3 | 0.4 | 0.5 | 0.8 | 0 |
| 14 | MID | 788 | 0.2 | 0.3 | 0.4 | 0.5 | 0.9 | 0 |
| 15 | ME1 | 232 | 0.2 | 0.3 | 0.4 | 0.5 | 0.9 | 0 |
| 15 | ME2 | 472 | 0.2 | 0.3 | 0.4 | 0.5 | 1.058 | 0 |
| 15 | MID | 787 | 0.2 | 0.3 | 0.4 | 0.5 | 1.014 | 0 |
| 16 | ME1 | 232 | 0.2 | 0.3 | 0.4 | 0.5 | 0.7 | 0 |
| 16 | ME2 | 470 | 0.2 | 0.3 | 0.3 | 0.5 | 0.631 | 0 |
| 16 | MID | 786 | 0.2 | 0.3 | 0.4 | 0.5 | 0.7 | 0 |
| 17 | ME1 | 231 | 0.2 | 0.3 | 0.4 | 0.5 | 0.67 | 0 |
| 17 | ME2 | 471 | 0.2 | 0.3 | 0.4 | 0.5 | 0.7 | 0 |
| 17 | MID | 787 | 0.2 | 0.3 | 0.4 | 0.5 | 0.7 | 0 |
| 21-22 UTC (all days) | ROLLOVER | 4159 | 0.4 | 1.0 | 2.45 | 4.1 | 7.8 | 0 |

#### GBPUSD

London-local hour (bar open) x day-set; s_open in pips.

| hour | set | n | p25 | p50 | p75 | p90 | p99 | n<=0 |
|---|---|---|---|---|---|---|---|---|
| 13 | ME1 | 232 | 0.6 | 0.8 | 1.025 | 1.6 | 3.638 | 0 |
| 13 | ME2 | 471 | 0.6 | 0.8 | 1.0 | 1.6 | 3.36 | 0 |
| 13 | MID | 788 | 0.6 | 0.8 | 1.1 | 1.6 | 4.513 | 0 |
| 14 | ME1 | 232 | 0.6 | 0.8 | 1.0 | 1.2 | 1.869 | 0 |
| 14 | ME2 | 469 | 0.6 | 0.8 | 1.0 | 1.1 | 1.732 | 0 |
| 14 | MID | 788 | 0.6 | 0.7 | 0.9 | 1.1 | 1.913 | 0 |
| 15 | ME1 | 232 | 0.6 | 0.8 | 1.0 | 1.2 | 2.238 | 0 |
| 15 | ME2 | 471 | 0.6 | 0.8 | 1.0 | 1.2 | 2.3 | 0 |
| 15 | MID | 787 | 0.6 | 0.7 | 0.9 | 1.1 | 1.9 | 0 |
| 16 | ME1 | 232 | 0.6 | 0.7 | 0.9 | 1.1 | 1.469 | 0 |
| 16 | ME2 | 470 | 0.6 | 0.7 | 0.9 | 1.1 | 1.5 | 0 |
| 16 | MID | 787 | 0.6 | 0.7 | 0.9 | 1.0 | 1.614 | 0 |
| 17 | ME1 | 232 | 0.6 | 0.8 | 1.0 | 1.2 | 1.6 | 0 |
| 17 | ME2 | 469 | 0.6 | 0.8 | 1.0 | 1.2 | 1.6 | 0 |
| 17 | MID | 786 | 0.6 | 0.8 | 0.9 | 1.1 | 1.815 | 0 |
| 21-22 UTC (all days) | ROLLOVER | 4249 | 1.0 | 2.3 | 5.0 | 8.1 | 15.952 | 0 |

#### USDJPY

London-local hour (bar open) x day-set; s_open in pips.

| hour | set | n | p25 | p50 | p75 | p90 | p99 | n<=0 |
|---|---|---|---|---|---|---|---|---|
| 13 | ME1 | 232 | 0.4 | 0.5 | 0.7 | 1.4 | 3.769 | 0 |
| 13 | ME2 | 472 | 0.3 | 0.5 | 0.7 | 1.39 | 3.858 | 0 |
| 13 | MID | 788 | 0.3 | 0.5 | 0.7 | 1.4 | 7.126 | 0 |
| 14 | ME1 | 232 | 0.375 | 0.5 | 0.7 | 0.9 | 1.269 | 0 |
| 14 | ME2 | 469 | 0.3 | 0.5 | 0.7 | 0.9 | 1.332 | 0 |
| 14 | MID | 788 | 0.3 | 0.5 | 0.6 | 0.8 | 1.7 | 0 |
| 15 | ME1 | 231 | 0.3 | 0.5 | 0.7 | 0.9 | 2.18 | 0 |
| 15 | ME2 | 471 | 0.3 | 0.5 | 0.7 | 0.9 | 2.09 | 0 |
| 15 | MID | 787 | 0.3 | 0.5 | 0.6 | 0.8 | 2.014 | 0 |
| 16 | ME1 | 231 | 0.3 | 0.5 | 0.6 | 0.8 | 1.1 | 0 |
| 16 | ME2 | 471 | 0.3 | 0.5 | 0.6 | 0.8 | 1.13 | 0 |
| 16 | MID | 786 | 0.3 | 0.4 | 0.6 | 0.7 | 1.1 | 0 |
| 17 | ME1 | 229 | 0.3 | 0.5 | 0.6 | 0.8 | 1.0 | 0 |
| 17 | ME2 | 463 | 0.3 | 0.5 | 0.6 | 0.8 | 1.3 | 0 |
| 17 | MID | 776 | 0.3 | 0.5 | 0.6 | 0.8 | 1.025 | 0 |
| 21-22 UTC (all days) | ROLLOVER | 3985 | 0.6 | 1.6 | 4.0 | 7.3 | 16.116 | 0 |

### FIXCERT fill-hour composite (per pair, ME1|ME2 days only)

| Pair | Leg | n | p50 | p90 | n<=0 |
|---|---|---|---|---|---|
| EURUSD | entry F−1h: London 14:00–15:59 bar-open | 942 | 0.3 | 0.5 | 0 |
| EURUSD | exit at fix: 16:00-London bar-open | 470 | 0.3 | 0.5 | 0 |
| GBPUSD | entry F−1h: London 14:00–15:59 bar-open | 940 | 0.8 | 1.2 | 0 |
| GBPUSD | exit at fix: 16:00-London bar-open | 470 | 0.7 | 1.1 | 0 |
| USDJPY | entry F−1h: London 14:00–15:59 bar-open | 940 | 0.5 | 0.9 | 0 |
| USDJPY | exit at fix: 16:00-London bar-open | 471 | 0.5 | 0.8 | 0 |

(Full stat set for the exit leg — p25/p75/p99 — is in the JSON `fixcert` node.)

### Headline read (owner-packet sharpening only — does NOT change any verdict)

- At the fix window (London 14–16) the month-end day-sets (ME1/ME2) price the
  SAME spread as mid-month controls at p50 for all three pairs
  (EURUSD 0.3/0.3/0.3; GBPUSD +0.1 vs MID at 14–15, equal at 16;
  USDJPY +0.1 vs MID at 14–15, +0.1 at 16). p90 similarly flat
  (EURUSD 0.5 across all sets; GBPUSD 1.1–1.2 vs 1.0–1.1; USDJPY 0.8–0.9 vs 0.7–0.8).
- The only bucket that reprices materially is the ROLLOVER reference
  (21–22 UTC, all days): p50 1.0/2.3/1.6 pips, p99 7.8/16.0/16.1 pips —
  an order of magnitude above the fix window, consistent with the pinned
  session curve (EURUSD Rollover 0.9, GBPUSD 2.3).
- Cost-law consequence (Q-2/Q-8): for a fix-window fill distribution the
  crossing cost is the ordinary London-session spread (p50 0.3/0.8/0.5 pips,
  p90 0.5/1.2/0.9), NOT a month-end premium bucket; commission/slippage remain
  DECLARED_UNMEASURED. Fill quality remains unmeasurable on M1 bid/ask
  (no volume/depth/tape) — the fix-instant fill itself cannot be certified
  better than bar-open opposite-quote spread.
- Plan §6 legal purpose: this converts the FIXCERT session-bucket proxy into a
  measured fix-window bucket for the owner packet. It does NOT rescue
  mechanism A (kill is ancestry/class + frontier; plan §4 freezes this).

## 8. Mechanism A/B/C — data legs present/absent

### A — `DTPFX-A1` month-end London fix rebalancing
- PRESENT: FX M1 bid/ask price panel (EURUSD/GBPUSD/USDJPY, 2021-01→2026-09-23,
  single source, paper tier); month-end cost bucket NOW MEASURED (this census);
  fix calendar is public.
- ABSENT: PIT information layer for fix order-flow / benchmark rebalancing
  estimates (no license source on disk); direction leg = historical price only
  (already-dead skeleton per plan §4); a non-exposed premium-measurement
  surface (USDCHF 0 bytes; AUDUSD/USDCAD sealed); broker-grade execution cost
  authority (R1/R2 reopener bytes absent). Fill quality at the fix unmeasurable
  on M1 bid/ask (label FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK).

### B — `DTPFX-B1` news → rate repricing → FX lag
- PRESENT: daily reference rates (EFFR/SOFR/OBFR/BGCR/TGCR through 2026-09-14);
  131-event macro timeline with provisional `available_at` (10/131
  minute-exact-verified ceiling); FX M1 bid/ask panel.
- ABSENT (blocking): **intraday rates-market series (CME ZQ/ZZT tick/minute) = 0
  bytes** — "observed rate reaction before entry" cannot be constructed from
  daily prints; **consensus vintages = absent; revision vintages = absent**;
  timeline is diagnostic/outcome-exposed labeled. Verdict support: BLOCKED_DATA
  (plan §4(b) expectation), with adjacency class-7 records secondary.

### C — `DTPFX-C1` two-venue synchronous quote divergence
- PRESENT: ONE two-sided feed (Dukascopy bid/ask, single venue).
- ABSENT (blocking): second venue feed = 0 bytes (IBKR probe 2026-09-26: 0
  two-sided obs, bid/ask=-1 UNSET ×5 pairs, minTick 0.5 pip, paper session;
  Dukascopy re-download BLOCKED_TRANSPORT; TrueFX/OANDA owner-gated EDQ1);
  broker-grade two-leg books for both taker legs. Verdict support: BLOCKED_DATA
  (plan §4(b) expectation).

## 9. Surprises / deltas vs INTAKE.md facts

1. **futures raw dir is not literally empty** — 5 × 0-byte
   `product_page.html` stubs exist under
   `~/.my-quantitative-data/fx-futures-frontier-v1/raw/lane-a2/`. Zero market
   bytes confirmed (the INTAKE claim holds in substance; recorded here for A7
   precision).
2. **PIT ledger nuance**: 92/131 events carry retrospective consensus
   references inside free-text `expected_vs_actual` (e.g. "consensus: hold").
   INTAKE's "no consensus vintages" is correct in the PIT sense (no structured,
   available-at consensus values), but A7 should not read "zero mentions".
   Minute-exact page-verified ceiling = 10/131 exactly as INTAKE states.
3. **Venue-2 probe raw jsonl normalizes the IBKR -1 sentinel to null**
   (1,785/1,785 rows `"bid": null`); the "-1" finding is documented in
   `VERDICT_session2.md`. Substance unchanged: 0 valid observations.
4. Everything else re-measured equal to INTAKE: EURUSD 136,485 rows; corpus end
   2026-09-23; rates last obs 2026-09-14; ERP1 census rollover/sunday headline
   numbers reconcile exactly; no new reopener bytes appeared during the cycle
   (stop-condition (b) not triggered).

## 10. Labels carried forward

- `SINGLE_SOURCE_PANEL` — all FX price evidence is the one Dukascopy bid/ask
  panel; no second source exists to cross it.
- `PAPER_TIER` — corpora are paper/demo-tier quotes (Dukascopy public feed;
  IBKR probe paper session); no live-tier cost authority exists.
- `FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK` — no volume/depth/tape on M1; fill
  quality (queue, pick-off, fix-auction participation) cannot be measured from
  these bytes and is stress-covered (×2.0) or declared, never assumed measured.

— Lane D, DTP-FX-MECHCOURT-V1, 2026-09-27
