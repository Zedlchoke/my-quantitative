# S9 — Independent Verification Report (FUTURES-DATA-10SYMS-V1)

- Verifier role: independent (A7-style); did NOT produce the data; all checks re-derived from raw files with `.venv/bin/python`.
- Verified at: 2026-10-02 (local). Raw root: `~/.my-quantitative-data/futures-10syms-v1/raw/` (1,150 files).
- Claim files: `S1_IDENTITY.json`, `S6_VALIDATION.json`, `raw_manifest.jsonl` (same directory as this report).
- No file was modified by this verification other than this report.

## Verdict table

| # | Check | Verdict | Key numbers |
|---|-------|---------|-------------|
| 1 | SHA-SPOT (10 random files vs manifest) | **PASS** | 10/10 match the latest manifest row; corroborating full sweep: 1150/1150 files match |
| 2 | IDENTITY (S1 front vs raw metadata) | **PASS w/ caveats** | conId/localSymbol/expiry consistent on 10 files per front, all 10 symbols; month code = delivery month 10/10; multiplier/minTick NOT present in raw metadata (not re-derivable from raw); S1-internal multiplier/minTick uniform on all resolved contracts |
| 3 | COVERAGE (vs S6_VALIDATION) | **PASS** | 200/200 per-contract rows identical (n, first, last, flat, dup); all per-symbol aggregates identical |
| 4 | ROLL CHAIN (real-volume months) | **PASS w/ findings** | 7/10 symbols: no missing cycle month in span. NQ missing 2027-09 (NQU7 all-flat); CL & NG missing 2026-10 (CLV6/NGV26 not fetched) |
| 5 | TIMEZONE (NQ/CL/6J 1-min) | **PASS** | 50 non-empty 1-min files checked; 100% ISO-8601 offsets; every offset matches its timeZoneId (or family tz at bar date for empty-tz files); DST-correct at each bar's own date |
| 6 | 6J QUOTE | **PASS** | Front 6JV6 last 5 closes 0.006332–0.006374; zero closes >1.0 across all 6J daily files; multiplier 12500000 on 42/42 resolved S1 contracts |
| 7 | DUPLICATES (front daily dates) | **PASS** | 0 duplicate dates on all 10 fronts (6Y file and 3D probe file), all sorted; matches S6 `dup_dates=0` |

**Overall: PASS** — no fabrication, no coverage misstatement, no quote-scale error found. Findings below are factual observations (2 chain holes with identified causes, 2 metadata caveats), none of which contradicts the claim files.

---

## 1. SHA-SPOT — PASS

Method: `random.seed(20261002)`, 10 files sampled from the raw dir; sha256 recomputed and compared to the manifest rows for that path. The manifest has 1,460 rows for 1,150 files (310 paths have 2 rows: an early fetch ~02:07–02:38 UTC and a re-fetch ~02:34–03:46 UTC); the current on-disk file is required to match the **latest** row.

| File | manifest rows | match latest row |
|------|---------------|------------------|
| 6E_6EX7_881167133_TRADES_1min_2D.json | 1 | yes |
| 6E_6EU6_513880717_TRADES_1min_2D.json | 2 | yes |
| SI_SIV6_760200581_TRADES_1hour_30D.json | 1 | yes |
| GC_GCV5_668631614_TRADES_1hour_30D.json | 2 | yes |
| NG_NGG28_269460014_BID_1day_1Y.json | 1 | yes |
| GC_GCM6_430360630_TRADES_1hour_30D.json | 2 | yes |
| 6B_6BV6_881167030_front_BID_1day_3D.json | 1 | yes |
| NQ_NQZ7_586139864_ASK_1day_1Y.json | 1 | yes |
| ES_ESU6_649180671_TRADES_1hour_30D.json | 2 | yes |
| CL_CLU6_304037484_nearest_expired_TRADES_1day_3D.json | 1 | yes |

Corroboration (beyond the required spot sample): all 1,150 files were swept — sha256 matches the latest manifest row for every file (0 stale), and metadata `n_rows` == manifest `n_rows` == `len(bars)` for every file.

## 2. IDENTITY — PASS with caveats

For each symbol, the S1 `front` was compared against every raw file carrying that conId (10 files per front: 5 series x 6Y/1Y + 5 x 3D/1800S probes).

| Symbol | front conId | localSymbol | S1 mult | S1 minTick | raw files | symbol ok | localSymbol ok | raw expiry_month == S1 lastTradeDate | month code == delivery month |
|--------|-------------|-------------|---------|------------|-----------|------------|----------------|--------------------------------------|------------------------------|
| NQ | 563947726 | NQZ6 | 20 | 0.25 | 10 | yes | yes | 20261218, yes | Z=12, yes |
| ES | 515416632 | ESZ6 | 50 | 0.25 | 10 | yes | yes | 20261218, yes | Z=12, yes |
| CL | 304037511 | CLX6 | 1000 | 0.01 | 10 | yes | yes | 20261020, yes | X=11, yes (delivery) |
| NG | 269460170 | NGX26 | 10000 | 0.001 | 10 | yes | yes | 20261028, yes | X=11, yes (delivery) |
| GC | 744880148 | GCV6 | 100 | 0.1 | 10 | yes | yes | 20261028, yes | V=10, yes |
| SI | 760200581 | SIV6 | 5000 | 0.005 | 10 | yes | yes | 20261028, yes | V=10, yes |
| 6E | 881167137 | 6EV6 | 125000 | 5e-05 | 10 | yes | yes | 20261019, yes | V=10, yes |
| 6J | 881167175 | 6JV6 | 12500000 | 5e-07 | 10 | yes | yes | 20261019, yes | V=10, yes |
| 6B | 881167030 | 6BV6 | 62500 | 0.0001 | 10 | yes | yes | 20261019, yes | V=10, yes |
| 6A | 881166970 | 6AV6 | 100000 | 5e-05 | 10 | yes | yes | 20261019, yes | V=10, yes |

Caveats (factual, none a contradiction):

- **Multiplier/minTick are not in raw metadata.** Raw JSON carries `symbol, conId, localSymbol, expiry_month, exchange, whatUse, barSize, durationStr, endDateTime, useRTH, endpoint, timeZoneId, ok, errors, n_rows, bars` — no multiplier/minTick. Raw-vs-S1 consistency for these two fields is therefore NOT re-derivable from raw. Substitute check performed: within S1, every resolved contract of a symbol (active_chain + front + next + resolved expired_walk entries) carries the identical multiplier/minTick as the front (e.g. 6J: 12500000 / 5e-07 on 42/42 resolved contracts). The only non-uniform entries are the 6 walk-stop `{"month": ..., "miss": true}` marker rows per symbol, which are not contracts.
- **Two month conventions coexist.** The raw field named `expiry_month` holds the full `lastTradeDateOrContractMonth` (e.g. CLX6 -> `20261020`), while S1's `expiry_date` is the delivery month (`202611` for CLX6). Month code vs raw field month: consistent for 8/10 symbols; for CL and NG the last-trade month is one month before the delivery month (CLX6 Nov contract last trades 2026-10-20; NGX26 2026-10-28) — the standard NYMEX energy convention, internally coherent, but the field name `expiry_month` is a mislabel risk for CL/NG consumers.

## 3. COVERAGE — PASS

Recomputed from raw daily TRADES files (per conId, the longest file wins; the 30 `front_*_3D` probe files are subsets of the 6Y files). Real-volume = any bar with `v>0`; all-flat = every bar has `v==0` and `o==h==l==c`.

| Symbol | distinct conIds w/ non-empty daily bars | earliest bar | latest bar | contracts ALL volume-0 | contracts w/ real volume | S6 agreement |
|--------|------------------------------------------|--------------|------------|------------------------|--------------------------|--------------|
| NQ | 10 | 2022-05-24 | 2026-10-01 | 1 (NQU7) | 9 | exact |
| ES | 10 | 2021-06-07 | 2026-10-01 | 0 | 10 | exact |
| CL | 28 | 2019-09-03 | 2026-10-01 | 0 | 28 | exact |
| NG | 28 | 2019-09-03 | 2026-10-01 | 0 | 28 | exact |
| GC | 22 | 2019-12-31 | 2026-10-01 | 0 | 22 | exact |
| SI | 22 | 2020-12-31 | 2026-10-01 | 3 (SIQ7, SIV7, SIX7) | 19 | exact |
| 6E | 20 | 2020-12-15 | 2026-10-01 | 7 (6EJ7 6EK7 6EN7 6EQ7 6EV7 6EX7 6EF8) | 13 | exact |
| 6J | 20 | 2020-12-15 | 2026-10-01 | 9 (6JF7 6JG7 6JJ7 6JK7 6JN7 6JQ7 6JV7 6JX7 6JF8) | 11 | exact |
| 6B | 20 | 2020-12-15 | 2026-10-01 | 7 (6BJ7 6BK7 6BN7 6BQ7 6BV7 6BX7 6BF8) | 13 | exact |
| 6A | 20 | 2021-09-14 | 2026-10-01 | 9 (6AF7 6AG7 6AJ7 6AK7 6AN7 6AQ7 6AV7 6AX7 6AF8) | 11 | exact |

Per-contract comparison: conId sets identical for all 10 symbols; all 200 contracts compared on `n`, `first`, `last`, `flat_zero_vol_rows`, `dup_dates` — 200/200 rows match S6 exactly.

## 4. ROLL CHAIN — PASS with findings

Delivery month parsed from localSymbol month code (F=Jan … Z=Dec); a month counts if any daily bar has `v>0`. Cycles: HMUZ (NQ, ES, 6E, 6J, 6B, 6A); monthly (CL, NG); GJMQVZ (GC); H,K,N,U,Z = Mar/May/Jul/Sep/Dec (SI).

| Symbol | real-volume delivery months | span | missing cycle month(s) in span | earliest continuous real-volume chain |
|--------|-----------------------------|------|-------------------------------|---------------------------------------|
| NQ | 2025-09 12 2026-03 06 09 12 2027-03 06 12 | 2025-09..2027-12 | **2027-09** (NQU7 exists, 134 bars, all v=0) | 2025-09..2027-06 continuous; broken at 2027-09; isolated 2027-12 (see note) |
| ES | 2025-09 .. 2027-12 all 10 quarterlies | 2025-09..2027-12 | none | 2025-09 |
| CL | 2025-10..2028-02, 28 months | 2025-10..2028-02 | **2026-10** (CLV6 not in dataset) | 2026-11 |
| NG | 2025-10..2028-02, 28 months | 2025-10..2028-02 | **2026-10** (NGV26 not in dataset) | 2026-11 |
| GC | 2025-10..2028-01, 22 months (all 6 cycle months present) | 2025-10..2028-01 | none | 2025-10 |
| SI | 2025-09..2028-01, 19 months (all 5 cycle months present) | 2025-09..2028-01 | none | 2025-09 |
| 6E | 2025-12..2027-12 (all 4 cycle months/yr present) | 2025-12..2027-12 | none | 2025-12 |
| 6J | 2025-12..2027-12 (all 4 cycle months/yr present) | 2025-12..2027-12 | none | 2025-12 |
| 6B | 2025-12..2027-12 (all 4 cycle months/yr present) | 2025-12..2027-12 | none | 2025-12 |
| 6A | 2025-12..2027-12 (all 4 cycle months/yr present) | 2025-12..2027-12 | none | 2025-12 |

Findings (factual):

- **NQ 2027-09**: NQU7 is in the raw set with 134 daily bars, every one flat with v=0 (contract not yet trading, ~1 year out). NQZ7 (2027-12) shows only 2 real-volume bars in 6Y (2025-05-30 v=1 and 2025-09-15 v=1 — single-lot prints), which is why 2027-12 registers as "real volume". The dependable continuous quarterly NQ chain is 2025-09 through 2027-06.
- **CL/NG 2026-10**: CLV6 / NGV26 (delivery 2026-10; last trade 2026-09-21 / 2026-09-28, i.e. expired days before the 2026-10-02 fetch) are absent from both the raw set and S1's `expired_walk`, whose resolved months jump from the front (CLX6 202611) straight back to 202609 (CLU6). The most recently expired contract on each of CL and NG was skipped by the backward walk. The continuous real-volume chain therefore starts 2026-11.
- Far-out non-cycle / deferred months with zero-volume-only files (not missing, just not yet trading): NQ none beyond 2027-09 note; SI 2027-08/10/11 (SIQ7/SIV7/SIX7); 6E/6B 2027-04,05,07,08,10,11 + 2028-01; 6J/6A 2027-01,02,04,05,07,08,10,11 + 2028-01.

## 5. TIMEZONE — PASS

All 1-min files with non-empty bars for NQ, CL, 6J were checked (NQ: 9 files, CL: 30, 6J: 11 — 50 files total). Every one of their bar timestamps matches `YYYY-MM-DDTHH:MM:SS±HH:MM` (ISO offset present, 100%).

| Symbol | files w/ bars | files with timeZoneId in metadata | offset observed | expected from timeZoneId | match |
|--------|---------------|-----------------------------------|-----------------|--------------------------|-------|
| NQ | 9 | 4 (NQZ6, NQH7: `US/Central`) | -05:00 on all bars dated 2026-09/10 | -05:00 (CDT; DST change 2026-11-01 not crossed) | yes |
| CL | 30 | 18 (`US/Eastern`) | -04:00 on all bars dated 2026-09/10 | -04:00 (EDT) | yes |
| 6J | 11 | 7 (`US/Central`) | -05:00 on all bars dated 2026-09/10 | -05:00 (CDT) | yes |

Files with empty `timeZoneId` in metadata (expired contracts — S1's `expired_walk` entries also carry `timeZoneId=""`, so the gap originates in contract-detail resolution, not in the bars): 5 for NQ, 12 for CL, 4 for 6J. For each of these, every bar's offset was checked against the symbol's exchange timezone **at the bar's own date**: all consistent, DST-correct — e.g. NQZ5 bars dated 2025-11-26..28 carry -06:00 (CST), NQM6 2026-05 bars -05:00 (CDT), CLH6 2026-01 bars -05:00 (EST), CLV5 2025-08 bars -04:00 (EDT), 6JH6 2026-02 bars -06:00 (CST). Zero mismatches.

## 6. 6J QUOTE — PASS

- Front 6JV6 last 5 daily closes: 0.006374, 0.006364, 0.006371, 0.006365, 0.006332 — inside the claimed ~0.0063–0.0065 USD-per-JPY band; identical to S6 `quote_convention.6J.recent_close_range` [0.006332, 0.00643].
- Across ALL 6J daily TRADES files (20 contracts, 9,136 bars) the minimum close is 0.006127 and NO close exceeds 1.0 — nothing anywhere near a 150–160 quote (the USD/JPY direction). Full-history max per contract reaches ~0.0102 (6JZ5, older periods when the yen was weaker), consistent with the JPY/USD listing convention, minTick 5e-07.
- Multiplier: 12500000 on all 42 resolved 6J contracts in S1 (front, next, active_chain, expired_walk). Raw files do not carry a multiplier field (see Check 2 caveat).

## 7. DUPLICATES — PASS

Daily TRADES bars of each symbol's front contract (both the 6Y file and the 3D front-probe file): 0 duplicate dates in all 20 files, all strictly sorted; matches S6 `daily_diag.dup_dates = 0` for every front contract. (Beyond the fronts, the Check 3 per-contract sweep confirmed `dup_dates` = 0 recomputed == S6 for all 200 contracts.)

---

## Discrepancy / caveat register

| # | Observation | Severity | Suggested owner action (not taken by verifier) |
|---|-------------|----------|-------------------------------------------------|
| C1 | CLV6 / NGV26 (delivery 2026-10, expired days before fetch) absent from raw set and S1 expired_walk — real-volume roll chain hole at 2026-10 for CL and NG; continuous chain starts 2026-11 | Medium (affects backtest roll continuity on CL/NG for the current cycle) | Re-fetch the just-expired contract or document the walk's first-backward-step skip |
| C2 | NQU7 all-flat (2027-09); NQZ7's only real volume is 2 one-lot prints — NQ deferred chain beyond 2027-06 carries no usable liquidity | Low (expected for deferred quarters) | No action; note for roll design |
| C3 | Raw `expiry_month` field holds lastTradeDate, which for CL/NG is one month before the delivery month implied by the localSymbol code; S1 `expiry_date` uses the delivery month | Low (naming/convention risk for downstream consumers) | Document both conventions in one place |
| C4 | Raw metadata has no multiplier/minTick; expired-contract raw files (and their S1 walk entries) have empty `timeZoneId`/`tradingHours` | Low (limits raw-only re-derivation of identity; bars' own offsets remain verifiable) | None required for this cycle; note for future captures |

Method note: all numbers above were computed directly from the raw JSON files and the two claim files; no producer script output was trusted. Verification code ran under `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.
