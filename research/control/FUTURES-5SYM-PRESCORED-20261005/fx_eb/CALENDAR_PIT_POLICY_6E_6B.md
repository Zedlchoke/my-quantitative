# CALENDAR_PIT_POLICY_6E_6B — expiry coverage, holiday grids, early-close exclusions, vintage law, D12 posture

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **FXEB**, 2026-10-05. PREP-only;
  0 PnL; 0 fetches by this lane (all cells inherited from committed captures, re-hashed
  read-only in this worktree; locks FREE_PROVEN).
- **CONDITIONAL-ON-PB2-LIFT DRAFT — PB2 HOLD (6E/6B) stands**; this document is the
  calendar/PIT annex a lifted cycle would consume. It changes no cell status; it states
  the fail-closed posture a freeze would inherit.
- Per-symbol law: 6E and 6B carry **separate** tables throughout. Provenance law: only
  dated official values from hash-verified archived captures; **IMM-rule / current-
  calendar derivation FORBIDDEN and never used**; NOT_OBTAINED is never inferred.

## 1. Expiry coverage state (per symbol)

### 1.1 6E — 66/68 cumulative (2010-2026 grid); 14/16 inside 2023-2026

All OBTAINED cells below from the archived official ProductCalendar/Future/58 capture
@2021-07-03 (sha256 of the capture recorded per cell in the source JSON) with Q5
independent verify PASS 13/13, plus ECH26/ECM26 extracted this cycle-family. Machine
source: `FUTURES-SIX-READINESS-20261004/fx_eb/calendar/fx_eb_expiry_2023_2026.json`
(sha256 `cf07d4e2…1ef07`).

| quarter | contract | last_trade_date | status |
|---|---|---|---|
| 2023Q1 | ECH23 | 2023-03-13 | OBTAINED |
| 2023Q2 | ECM23 | 2023-06-19 | OBTAINED |
| 2023Q3 | ECU23 | 2023-09-18 | OBTAINED |
| 2023Q4 | ECZ23 | 2023-12-18 | OBTAINED |
| 2024Q1 | ECH24 | 2024-03-18 | OBTAINED |
| 2024Q2 | ECM24 | 2024-06-17 | OBTAINED |
| 2024Q3 | ECU24 | 2024-09-16 | OBTAINED |
| 2024Q4 | ECZ24 | 2024-12-16 | OBTAINED |
| 2025Q1 | ECH25 | 2025-03-17 | OBTAINED |
| 2025Q2 | ECM25 | 2025-06-16 | OBTAINED |
| 2025Q3 | ECU25 | 2025-09-15 | OBTAINED |
| 2025Q4 | ECZ25 | 2025-12-15 | OBTAINED |
| 2026Q1 | ECH26 | 2026-03-16 | OBTAINED (recovered this cycle-family) |
| 2026Q2 | ECM26 | 2026-06-15 | OBTAINED (recovered this cycle-family) |
| 2026Q3 | ECU26 | — | **NOT_OBTAINED** |
| 2026Q4 | ECZ26 | — | **NOT_OBTAINED** |

**ECU26/ECZ26 proven-absent chain (date-by-date)** [FACT, same JSON + CAL_EB_REPORT]:
archived Future/58 max capture = **2021-07-03** with rows ending Jun-2026 (CDX
`captures/cdx_future58_prefix.txt` sha256 `52f97696…e14bdd2`, this worktree re-hash);
ProductCalendar/Download.xls = 58 only @2017-09-21; Quotes/Future/58/G max
@20210313102336; cspec pages = prose rule text (derivation forbidden); live service
BLOCKED_TRANSPORT (sibling measurement). CAL-EB's bounded re-search (budget 10/35, zero
new cells) confirms non-recoverability by any permitted route.

### 1.2 6B — 62/68 cumulative; 10/16 inside 2023-2026

OBTAINED cells from the Wayback capture of
`ProductCalendar/Download.xls?productId=42` @2024-09-03 vintage (16,896 wire bytes,
fetch-log line, own xlrd parser). Cross-vintage QA vs the @2024-11-08 capture: **21/21
shared rows exact**; later vintage drops BPU24/BPV24 (expired-contract drop DEMONSTRATED)
and adds BPG25/BPJ25/BPU29 (outside grid, recorded for completeness). Machine source:
same JSON; captures `pcal_42_6b_dl_20240903.xls` sha256 `ea9b129e…f9910e`,
`pcal_42_6b_dl_20241108.xls` sha256 `b38ef64e…fb105`.

| quarter | contract | last_trade_date | status |
|---|---|---|---|
| 2023Q1 | BPH23 | — | **NOT_OBTAINED** |
| 2023Q2 | BPM23 | — | **NOT_OBTAINED** |
| 2023Q3 | BPU23 | — | **NOT_OBTAINED** |
| 2023Q4 | BPZ23 | — | **NOT_OBTAINED** |
| 2024Q1 | BPH24 | — | **NOT_OBTAINED** |
| 2024Q2 | BPM24 | — | **NOT_OBTAINED** |
| 2024Q3 | BPU24 | 2024-09-16 | OBTAINED |
| 2024Q4 | BPZ24 | 2024-12-16 | OBTAINED |
| 2025Q1 | BPH25 | 2025-03-17 | OBTAINED |
| 2025Q2 | BPM25 | 2025-06-16 | OBTAINED |
| 2025Q3 | BPU25 | 2025-09-15 | OBTAINED |
| 2025Q4 | BPZ25 | 2025-12-15 | OBTAINED |
| 2026Q1 | BPH26 | 2026-03-16 | OBTAINED |
| 2026Q2 | BPM26 | 2026-06-15 | OBTAINED |
| 2026Q3 | BPU26 | 2026-09-14 | OBTAINED |
| 2026Q4 | BPZ26 | 2026-12-14 | OBTAINED |

**2023Q1–2024Q2 NOT_OBTAINED proven-absent chain (date-by-date)** [FACT]: archived 6B
calendars = Future/42 max **2018-04-08** (pre-span) and Download.xls=42 earliest
**2024-09-03** (service drops expired contracts; drop demonstrated cross-vintage);
CDX inventories `captures/cdx_future42_prefix.txt` sha256 `9c5151b1…fa522` +
`captures/cdx_downloadxls42.txt` sha256 `8c6b4be2…b3534ef`; live BLOCKED_TRANSPORT.
Structural: **no permitted route can ever produce these cells.** Forward rows in the
same captures, outside the grid (completeness): BPH27 2027-03-15, BPM27 2027-06-14,
BPU27 2027-09-13, BPZ27 2027-12-13, BPH28 2028-03-13, BPM28 2028-06-16, BPU28 2028-09-18,
BPZ28 2028-12-18, BPH29 2029-03-19, BPM29 2029-06-15.

## 2. Roll / chain law (per symbol)

MEASURED (both symbols, `cost_roll_events_fxeb.json` sha256 `a99a6983…40052`): **27
switches / 28 contracts / 1,746 sessions each**; switch dates + per-switch leads in the
machine file (6E leads 13–19 days where cells obtained; 6B 17 days on 2024Q4→2026Q3
switches vs official cells, 14 days into the 2026Q4 contract).

LAW-PENDING (declared): the freeze-time binding of a PIT roll rule to official dates —
draft (binding only post-lift): **roll at the close of T-5 sessions before the official
last-trade date, with cease-guard** (never roll into a dead contract; naive-vs-guarded
switch reconciliation on cease-guard event days per CYCLE_LAUNCH_DRAFT §5). NOT_OBTAINED
quarters (6E ECU26/ECZ26; 6B 2023Q1–24Q2) carry NO official roll anchor ⇒ **fail-closed
per-quarter exclusion** at freeze (D12 posture below). The 6B k=5 thin-window measurement
(1,069..13,222 contracts/day) is carried; the 6E cease-guard event-day inventory is
NOT_RUN (6E registry exists but event-day reconciliation was not run by any lane).

## 3. Holiday grids + early-close exclusions (per symbol, fail-closed)

### 3.1 6E — 34/42 windows OBTAINED (+ 8 INCONCLUSIVE_AGED_OUT, never counted)

Machine source: `FUTURES-SIX-READINESS-20261004/fx_eb/holiday/holiday_deviation_6e_6b.json`
(sha256 `07d60a7e…c4821`). By year: 2023 4/11 documented, 2024 10/10, 2025 10/11, 2026
10/10. Aged-out law: the by-product service returns deviations only within ~1y of crawl
(empirical bracket 307d/369d); the 8 aged-out windows (2022-12-31, 2023-01-15,
2023-02-19, 2023-04-06, 2023-05-28, 2023-06-18, 2023-07-03, 2025-01-05) are
INCONCLUSIVE — **zero-grids from aged captures are never evidence of normal hours**.

**Fail-closed early-close/holiday exclusion lists** (K6GATE §2 holiday layer, adopted
here as the standing posture):

| exclusion class | sessions | grounds |
|---|---|---|
| Evidence-based deviation exclusion | 1 session: **2023-11-24** (early close; the only committed id-58 capture showing deviant held hours among the 5 windows whose captures are in the committed tree: 2023-09-03, 2023-11-22, 2023-12-24, 2023-12-31, 2025-08-31) | OBTAINED id-58 deviation event (≠17:00 open / ≠16:00 close on tradingDate) |
| Fail-closed neighborhood cells | **93 sessions across 37 windows** (29 OBTAINED + 8 aged-out windows whose capture files are absent from the committed tree; sessions in [window_first_event_date, +3d]) | deviant-session identification NOT_RUN ⇒ neighborhood excluded, never counted clean |
| 2022 Monday-halt regime change | pre-2022 Monday-holiday reopen structure differs (12:00 CT halt 2017-2021 GONE by 2022) | year-aware pipeline mandatory; pre-2022 Monday-holiday sessions handled by era view, never silently pooled |

### 3.2 6B — 0/42 windows NOT_OBTAINED (documented structural absence)

Product id 42 appears in NO archived by-product capture: fresh 709-row CDX id lists =
{10-id list, empty, 5224, 133, 318, 133,219, 167,133} with standalone id=42 = 0 rows;
advisory + settlement-times PDF families are clearing memos carrying zero product trading
hours (2023 MLK + 2025 MLK PDFs inspected); two-vintage XLS drop demonstrated; live
service BLOCKED_TRANSPORT. [FACT, CAL_EB_REPORT + holiday JSON `6B` block.]

**Fail-closed posture**: NO holiday-adjacent exclusion is implementable for 6B — 6B
results carry the hole declared; any future 6B spec's holiday stand-aside (FX_HYPOTHESES
§4.5 (ii)) stays **BLOCKED on the grid**; holiday-adjacent 6B sessions are neither
excluded nor certified clean, and every 6B freeze must print this posture verbatim.

## 4. Event PIT / vintage law

- **FOMC**: 30 rate-decision statements 2023→2026-09-30 (8/8/8/6); 31st statement
  2025-08-22 = framework review (10:00 EDT), not a decision. In-panel 2020-2026: 58
  statements with in-file release-time proof (53 at 13:00 CT; 2020 emergency timings
  disclosed, base-EXCLUDED). Anchor 13:00 CT / minute 780.
- **BoE MPC**: 32 listed dates 2023-2026, **30 in panel** (8/8/8/6); **11 rate-change
  decisions in panel** (5/2/4/0 by year 2023/2024/2025/2026), cross-checked vs
  `normalized/boe_bank_rate_tidy.parquet` (official Bank Rate history through 2025-12-18);
  19 hold decisions; 2026-11-05/2026-12-17 forward-scheduled, never counted as decisions.
  In-panel 2020-2026 MPC: 56 dates. Decision-time-knowable stamps = Bank Rate decision +
  minutes at 12:00 Europe/London (minute-720, DST-proven across 8 mismatch dates).
- **ECB GC (6E stratum)**: 55/55 meetings 2020-2026.9, decision 14:15 CET/CEST.
- **BLS (F3)**: CPI/EMPSIT 204/204 @08:30 ET 2010-2026; vintage law BLSV §5 (2025:
  11 CPI / 10 EMPSIT actual; canceled-expected days = negative-control strata).
- Vintage law (all events): calendars keyed to vintage as-of decision date;
  current-calendar inference FORBIDDEN; 2025 lapse-in-appropriations BLS anomalies
  resolved in baseline bls_vintage artifacts (cited, not refetched).

## 5. D12 residual-cell posture

D12 (six-adopt packet, `open_decisions_dependency.json` id D12; CYCLE_LAUNCH_DRAFT §8
row D12) governs: residual NOT_OBTAINED calendar cells — **bounded permitted-route
extension vs leave**. This lane's inherited posture, binding on any future FX freeze:
cells stay NOT_OBTAINED (6E ECU26/ECZ26; 6B BPH23..BPM24; 6B holiday grid 0/42; 6E 8
aged-out windows); affected windows/sessions excluded **fail-closed** per §3; no
purchase/signup proposed anywhere; CAL_COST may attempt permitted-route closure but this
lane neither assumes nor waits for it. Any quarter whose status cannot be proven is
excluded per-quarter for roll-integrity cells.

— End CALENDAR_PIT_POLICY_6E_6B.md. Conditional-on-PB2-lift; changes no standing ruling.
