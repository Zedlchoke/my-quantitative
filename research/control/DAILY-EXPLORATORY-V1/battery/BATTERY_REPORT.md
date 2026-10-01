# BATTERY_REPORT — DAILY-EXPLORATORY-V1 exploratory battery

> **EXPLORATORY-ONLY under DECLARED costs (x1.0 / 1.5 / 2.0). NO edge
> claim; NO after-cost PASS is readable from this battery (OI-2
> statement NOT_RUN); validation = prospective surface only
> (post-registration accumulation, earliest honest evaluation ~2029-09
> for a 2026-10 registration). Negative or positive exploratory
> numbers are equally informative and are reported plainly.**

- Cycle: `DAILY-EXPLORATORY-V1` — GO consumed 2026-10-01T08:36:23Z
  (`auth/GO_RECORDED.json`); executed in worktree
  `.worktrees/pc12a-daily-exploratory-prep` @ `2f7bc832`.
- Slate (FREEZE.md item 5): **DS-03** (`USDJPY-S065`, xasset_energy_lng)
  + **DS-05** (`EURUSD-S006`, usdbasket_rank); 5 candidates parked by owner law.
- Budget: **10 identities / 83 trial rows used of the 10 / 83 cap**
  (80 fold rows + 3 LEARN grid rows; STOP-at-cap respected).
- Calendar: warmup 2020-10-02..2021-09-30 | LEARN 2021-10-01..2022-09-22 |
  embargo 2022-09-23..09-29 | 8 x 26w EXPLORATORY folds 2022-09-30..2026-09-24
  with fold-edge force-flat; every fold is EXPLORATORY / hypothesis-generating
  (exposure-adjacent inputs; PC12A-exposed vehicles).
- Engine: G9 quote-CCY book + journal_row@1 writer + DECLARED cost kernel
  (commit 09fb1b74, 13/13 tests leak-clean) + the battery extension
  (`research/daily_exploratory/{datainputs,rules,battery,run_battery}.py`),
  tests 32/32 green (`tests/test_daily_exploratory.py`).

## 1. Result summary (all fields EXPLORATORY_DECLARED_COSTS)

| arm | tier | pooled net USD | pooled maxDD USD* | gross-vs-mid USD | costs USD | trades |
|---|---|---:|---:|---:|---:|---:|
| SLATE | x1.0 | -1,088.08 | 1,331.71 | -36.66 | 625.01 | 59 |
| B0_FLAT | x1.0 | 0.00 | 0.00 | 0.00 | 0.00 | 0 |
| B1S_ALWAYS_ON | x1.0 | -1,088.08 | 1,331.71 | -36.66 | 625.01 | 59 |
| B2_EQUAL_WEIGHT | x1.0 | -1,088.08 | 1,331.71 | -36.66 | 625.01 | 59 |
| B3_BEST_SINGLE | x1.0 | -355.40 | 111.55 | 426.49 | 355.48 | 34 |
| LORO_EX_DS03 | x1.0 | -732.67 | 1,331.71 | -463.14 | 269.53 | 25 |
| LORO_EX_DS05 | x1.0 | -355.40 | 111.55 | 426.49 | 355.48 | 34 |
| STRESS15_SLATE | x1.5 | -1,400.54 | 1,336.98 | -36.66 | 937.51 | 59 |
| STRESS15_B1S | x1.5 | -1,400.54 | 1,336.98 | -36.66 | 937.51 | 59 |
| REPORT20_PAIR_SLATE | x2.0 | -1,713.01 | 1,342.25 | -36.66 | 1,250.02 | 59 |
| REPORT20_PAIR_B1S | x2.0 | -1,713.01 | 1,342.25 | -36.66 | 1,250.02 | 59 |

\* pooled maxDD = max of per-fold maxDD (fold-edge force-flat restarts each
fold's books at the fixed opening; the pooled equity is not one continuous
compounding curve — disclosed). Gross/cost USD components are converted at
each symbol's final-mark rate (REPORTING-CONVENTION@1); the governing USD
figures are the realized-event net and the realized-curve maxDD.

**Reading (honest): every arm is NET-NEGATIVE at every cost tier.** The
slate nets -1,088.08 USD pooled at x1.0; the loss
deepens monotonically under stress (-1,400.54 at x1.5, -1,713.01 at x2.0) — the
battery is signal- and cost-dominated negative, not cost-rescued. B0 FLAT
(0 USD, 0 DD by construction) dominates every arm on both quantities.

## 2. Fold table — SLATE @ x1.0 (EXPLORATORY)

| fold | window | net USD | maxDD USD | trades | DS-03 fires | DS-05 fires | floor typing |
|---|---|---:|---:|---:|---:|---:|---|
| FOLD-1 | 2022-09-30..2023-03-30 | -67.13 | 581.61 | 7 | 3 | 4 | OK |
| FOLD-2 | 2023-03-31..2023-09-28 | -97.97 | 741.90 | 8 | 3 | 5 | OK |
| FOLD-3 | 2023-09-29..2024-03-28 | -96.76 | 1,035.82 | 9 | 3 | 6 | OK |
| FOLD-4 | 2024-03-29..2024-09-26 | -75.82 | 75.82 | 7 | 7 | 1 | DS-05 NOT_RUN_THIN (FLAT) |
| FOLD-5 | 2024-09-27..2025-03-27 | -524.93 | 940.37 | 15 | 11 | 4 | OK |
| FOLD-6 | 2025-03-28..2025-09-25 | -79.22 | 895.51 | 3 | 0 | 3 | DS-03 NOT_RUN_THIN (FLAT) |
| FOLD-7 | 2025-09-26..2026-03-26 | -78.54 | 78.54 | 7 | 7 | 1 | DS-05 NOT_RUN_THIN (FLAT) |
| FOLD-8 | 2026-03-27..2026-09-24 | -67.71 | 1,331.71 | 3 | 0 | 3 | DS-03 NOT_RUN_THIN (FLAT) |

Fold 8's vehicle sessions end 2026-09-23 (the frozen M1 panels end there;
the calendar's 2026-09-24 target date has no panel session — disclosed,
not interpolated). AUD/CAD D1 inputs run to 2026-09-30 via the G6 pull;
no `NOT_RUN_INPUT_END` truncation was needed (the G6 extension landed).

## 3. Cost decomposition — DECLARED tiers (EXPLORATORY)

| tier | spread_once (JPY + USD) | slip_beyond | commission | swap | total cost USD | net USD |
|---|---:|---:|---:|---:|---:|---:|
| x1.0 | 27,105 + 64 | 1,527 + 7 | 4,030 + 13 | 20,833 + 186 | 625.01 | -1,088.08 |
| x1.5 | 27,105 + 64 | 15,844 + 42 | 6,044 + 19 | 31,249 + 278 | 937.51 | -1,400.54 |
| x2.0 | 27,105 + 64 | 30,160 + 78 | 8,059 + 26 | 41,665 + 371 | 1,250.02 | -1,713.01 |

(JPY amounts are JPY quote-CCY, EUR amounts are USD quote-CCY; swap = 1
pip per night against the position, Wed x3, the frozen DECLARED calendar;
commission 0.35 bps/side; stress scales variable components only —
spread_once is the bar-quoted market fact and does not scale.)

## 4. LEARN selections (TRAIN-side only, before any fold data)

- **Grid G1 (DS-03 Brent-flat)**: LEARN fires B=6, C=10 (>=3: not thin). The frozen selection objective (net improvement vs B1S on LEARN, maxDD not worse) is identically 0.0 on both nodes — B1S is mechanically the SLATE here (no eligibility layer exists on the daily slate; disclosed degeneracy) — so the frozen tie-break chain applies and the **G7 default node B (|RBRTE 10d ret| < 3%)** is selected. Node A (gate OFF) is reported as the null-control only (LEARN net -388.49 USD vs B -190.74 / C -253.24).
- **B3 BEST_SINGLE**: obj_B3 = DSR on LEARN per-trade NET USD at x2.0 (N_eff=2 clusters, SR0=0.0684). DSR DS-03=0.0498 vs DS-05=0.0381 -> **DS-03 selected** (DSR); the full tie-break record is in `BATTERY_SUMMARY.json`.

## 5. Decision floors (typed, never silently widened)

- Full-window fires: DS-03 34 (>=20 OK); DS-05 27 (>=20 OK).
- Per-fold floor (>=3): **DS-03 folds 6 and 8 = 0 fires -> NOT_RUN_THIN, DS-03 FLAT in those folds in EVERY arm**; **DS-05 folds 4 and 7 = 1 fire -> NOT_RUN_THIN, DS-05 FLAT in those folds in EVERY arm** (24 BLOCKED_FLOOR journal rows).
- Aggregate fires 61 < 100 -> **NOT_RUN_THIN_AGGREGATE** (battery continues; disclosed per the dispatch's floor law).

## 6. LORO / P-MW two-sided tables (EXPLORATORY reporting; both sides shown)

**DS-03 added trades (SLATE vs SLATE \ DS-03 = LORO arm):**

| fold | n added | sum added-winners USD | sum added-losers USD | largest winner USD | winner-concentration |
|---|---:|---:|---:|---:|---:|
| FOLD-1 | 3 | 82.62 | -135.04 | 82.62 | 100% |
| FOLD-2 | 3 | 305.12 | -252.12 | 221.75 | 73% |
| FOLD-3 | 3 | 239.33 | -100.91 | 150.63 | 63% |
| FOLD-4 | 7 | 236.81 | -387.85 | 144.09 | 61% |
| FOLD-5 | 11 | 519.88 | -776.32 | 218.85 | 42% |
| FOLD-6 | 0 | 0.00 | 0.00 | 0.00 | n/a |
| FOLD-7 | 7 | 477.29 | -263.95 | 241.97 | 51% |
| FOLD-8 | 0 | 0.00 | 0.00 | 0.00 | n/a |

**DS-05 added trades (SLATE vs SLATE \ DS-05 = LORO arm):**

| fold | n added | sum added-winners USD | sum added-losers USD | largest winner USD | winner-concentration |
|---|---:|---:|---:|---:|---:|
| FOLD-1 | 4 | 68.65 | -127.49 | 68.65 | 100% |
| FOLD-2 | 5 | 48.85 | -120.95 | 43.77 | 90% |
| FOLD-3 | 6 | 271.13 | -350.27 | 201.76 | 74% |
| FOLD-4 | 0 | 0.00 | 0.00 | 0.00 | n/a |
| FOLD-5 | 4 | 0.00 | -429.80 | 0.00 | n/a |
| FOLD-6 | 3 | 0.00 | -88.56 | 0.00 | n/a |
| FOLD-7 | 0 | 0.00 | 0.00 | 0.00 | n/a |
| FOLD-8 | 3 | 47.43 | -122.76 | 47.43 | 100% |

P-MW deltas: net(SLATE) - net(SLATE minus DS-03) = -355.40 USD; net(SLATE) - net(SLATE minus DS-05) = -732.67 USD — both legs REDUCE slate net in this exploratory window (a P-MW bar would not clear; no PASS is claimed anywhere in this battery — exploratory reporting only).

## 7. Degeneracies (byte-identical arms, disclosed)

- B1S_ALWAYS_ON == SLATE (no eligibility layer on the daily slate; PB2 B1 pins an L2 that does not exist)
- B2_EQUAL_WEIGHT == SLATE (equal-split of the same total budget at symmetric per-leg risk)
- B3_BEST_SINGLE (DS-03) == LORO_EX_DS05 (the same leg alone)
- The netting law is implemented (same-symbol offsetting intents would
  journal NETTED_TO_ZERO) but cannot trigger: the two legs trade different
  symbols (USDJPY / EURUSD) and are long-only — zero NETTED_TO_ZERO rows
  exist by construction.

## 8. Inputs, provenance and integrity

- EIA RNGWHHD/RBRTE: sha-verified vs `MANIFEST_RAW.json@pc12a-7asset`
  (RNGWHHD 1,940 rows / RBRTE 1,961 rows to 2026-09-29); OI-5 signal-only,
  1bd declared serving, never fill prices.
- IBKR NZDUSD/USDCHF panels-of-record: 12-chunk aggregate sha verified
  (NZDUSD `c681402b...`, USDCHF `7fbd3a80...`; 1,553 sessions each).
- G6 AUD/CAD D1 extension: 16 files sha-verified; 66/66 weekdays
  2026-07-01..2026-09-30; forming 2026-10-01 bar excluded.
- H1 ANC parquets: CAD pin matches exactly; **AUD pin erratum disclosed**
  (`PIN_ERRATUM_DISCLOSED@1`: the G5 doc pin reads hex char 48 'b' where
  the unique machine-wide artifact (mtime 2026-09-26) hashes 'a'; both
  values recorded — nothing silently trusted, nothing silently edited).
- M1 panels EURUSD/GBPUSD/USDJPY: every .bi5 (4,184 file-hashes per pair)
  sha-verified against its frozen manifest before decode; aggregated by
  the declared 17:00-ET session law (`D1_SESSION_1700ET@1`).
- **G5 vehicle-side freeze act executed**: D1 band cells for EURUSD and
  USDJPY derived (MEASURED-DERIVED,
  `inputs/VEHICLE_BANDS_G5_FREEZE_ACT.json`, 12 cells O/C x
  FULL/EVAL/FOLDS) — validation bands only; fills price at the bar's own
  quoted side.
- Holiday calendar named: `DECLARED-PANEL-CALENDAR@1` (each frozen panel's
  own recorded session calendar; no synthetic holiday model).

## 9. Journal + bookkeeping verification

- 85 journal files (80 fold + 3 LEARN-grid + 2 B3-selection), 1,225 data
  rows; every hash-chain verified (tamper check OK); outcomes: 1,128
  FILLED, 73 BLOCKED_STALE (source-holiday/panel-gap freshness blocks,
  typed), 24 BLOCKED_FLOOR (NOT_RUN_THIN folds).
- Quote-CCY identity (FILL_ACCOUNTING_SPEC section 6) holds to 1e-9 on
  every book of every arm/window (observed residual ~1e-21); par-replay
  divergence within the disclosed bound everywhere.
- Journals are leak-clean by construction (RGC-INC-1 writer law): every
  PnL field lives in the metrics/report outputs, each labeled
  EXPLORATORY_DECLARED_COSTS.

## 10. Declared battery conventions (frozen for this run)

`RISK_UNIT_100USD@1`; `STOP_K_ATR@1` (stop = fill - k x ATR-14 Wilder,
breach on the D1 mid low, exit at the next session open; k=1 DS-03, k=2
DS-05); `FRESHNESS_1BD_TOLERANCE@1`; hold 5 sessions (DS-03, corpus);
rank window 20d, entry EUR rank 1-2 with 5-session (2-consecutive-week)
consistency, exit on rank>3 (DS-05, corpus); `INVERSE_RET@1` for
USD-quoted pairs; `FORCE_FLAT_LAST_BAR_OPEN@1`; `SWAP_CONV_CLOSE_MID@1`;
realized-USD equity (REALIZATION_SAME_BAR@1 per event + open position at
the same-bar rate). Full details in the module docstrings under
`research/daily_exploratory/`.

## 11. Honest close

No rescue, no tuning: the exploratory battery is negative at every tier,
both legs reduce slate net, and the thin-fold typings stand (DS-03 folds
6/8, DS-05 folds 4/7, aggregate 61 < 100). This file asserts NO pass, NO
GO and NO after-cost claim of any kind. Prospective validation remains
the only readable surface (post-registration accumulation, >=6 x 26w,
earliest ~2029-09).

