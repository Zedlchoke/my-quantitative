# EVAL_V3 — FUTURES-ES-PB1-V1 / lane Y2016-AUDIT (M4)

- Cycle FUTURES-ES-PB1-V1, lane Y2016-AUDIT. Generated 2026-10-05.
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`,
  branch `prep/futures-es-reg-20261004`, HEAD **`456dac6bc75f84ea860a977068568f9688053743`**
  (single bare `rev-parse` at lane start; status EMPTY at start; no commit/stage/push).
- Owner-audit trigger: the v2 verdict "2016 FAIL_CLOSED_BASIS_PROVEN" rested on
  "every candidate-named 2016 session is absent or truncated, ZERO ambiguous rows".
  The audit correctly rejected the underlying inference — **"full 390 bars" is not
  evidence of no-early-close** (2015-07-02 falsified it: a scheduled early-close day
  carried a complete, real-volume 390-bar session). This lane re-derives the 2016
  candidate windows from the committed 2011-2015 PDF patterns, sweeps ALL in-panel
  years for the same defect, and excludes every unproven candidate fail-closed.
- Machine deliverables: `y2016/sweep_candidates_v3.json` (202 candidate rows
  2010-2026), `y2016/exclude_2016_failclosed.json` (the v3 addition, sha
  `1b846b1714dd1c8f…` full value in `eval_v3.json`), `y2016/eval_v3.json`
  (this document's machine source). This file is the human projection; the JSON
  files are authority.

---

## 1. Method (v2-reproduced, then v3 applied)

eval surface = fold sessions − warmup (first 252 sessions of each fold) −
**union**(v2 in-panel exclusion classes, v3 `HOLIDAY_2016_UNPROVEN_FAILCLOSED`).
The v2 arithmetic was reproduced **EXACTLY** first (fold counts, base exclusions
38/75/72/85, eval 375/949/711/890, eval bounds identical to
`repair/FREEZE_DIFF.md` §6) before any v3 change was applied. Bars per session
come from the committed session universe (`session_dispersion_es.json`, sha
`e56c4a53…`) — no panel parquet read, zero network.

## 2. Evaluation surface: 2,925 → 2,921 (−4)

| fold | window | sessions | base excl old→new | warmup | eval n old→new | eval bounds |
|---|---|---|---|---|---|---|
| F1 | 2010-06-01..2012-12-31 | 665 | 38→38 | 252 | **375→375** | 2011-06-10..2012-12-31 (unchanged) |
| F2 | 2013-01-01..2017-12-31 | 1276 | 75→**76** | 252 | **949→948** | 2014-01-17..2017-12-29 (unchanged) |
| F3 | 2018-01-01..2021-12-31 | 1035 | 72→**75** | 252 | **711→708** | 2019-01-18..**2021-12-30** (eval-last moved off 2021-12-31) |
| F4 | 2022-01-01..2026-09-30 | 1227 | 85→85 | 252 | **890→890** | 2023-01-18..2026-09-30 (unchanged) |
| **total** | | 4204 | | | **2925→2921** | |

## 3. Every added exclusion (class `HOLIDAY_2016_UNPROVEN_FAILCLOSED`, 11 entries)

### 3a. NEW set members — 4 (each a COMPLETE 390-bar session on an unproven candidate date)

| session | fold | v2 status | basis |
|---|---|---|---|
| **2016-07-01** (held ESU6, 390 bars, cov 1.0) | F2 eval | eval-eligible survivor | July-4 Monday-config day-before — owner directive names it a candidate; no 2016 day-level proof exists; the 2011 analog (2011-07-01) is PDF-adjudicated REGULAR but binds 2011 only. **The audit-predicted 2015-07-02-shaped exposure.** |
| **2020-07-02** (ESU0, 390) | F3 eval | eval-eligible survivor | July-4 Sat-config day-before (Thu before observed Fri Jul 3); pattern AMBIGUOUS (2015 Sat config: Thu EC-1215; 2020 note: "NO equities early-close entry Jul 2", floor-tier) |
| **2021-07-02** (ESU1, 390) | F3 eval | eval-eligible survivor | July-4 Sun-config day-before (owner directive); 2010 analog PDF-REGULAR binds 2010 only |
| **2021-12-31** (ESH2, 390) | F3 eval (was eval-last) | eval-eligible survivor | New-Year Sat-config observed-closure position; 2022-page row names it a floor EC (generic, equity-silent); no equity day-level proof |

### 3b. Relabels — 7 (2016 candidates already excluded by COVERAGE_LT60; set unchanged, evidence label upgraded)

2016-01-18 (210), 2016-02-15 (210), 2016-05-30 (209), 2016-07-04 (210),
2016-09-05 (209), 2016-11-24 (210), 2016-11-25 (225). Each is a
pattern-derived 2016 candidate window date (MLK, Presidents, Memorial,
July 4, Labor, Thanksgiving, Black Friday) with ZERO committed 2016 day-level
Globex-equity evidence; 2016-11-25 carries a floor-tier equity naming only
("Equities floor close 12:15 CT … Globex equity times NOT transcribed").

### 3c. Kept WITH day-level proof (never excluded)

- **2010-07-02** — 2010 PDF p18 equity "Regular CME Globex close" (session sits
  in F1 warmup anyway).
- **2010-12-31** — PDF-proven REGULAR by two committed PDFs (2011-new-years.pdf;
  2010 PDF p36) (F1 warmup anyway).
- **2026-07-02** — product-level FACT cell (ES id=133): normal daily template
  (16:00 closed / 17:00 open) vs the actual deviation on 2026-07-03 (12:00
  closed); panel agrees (390 bars). **Stays F4-eval-eligible.** This is the only
  product-level day-level Globex evidence in the entire corpus, 2026-only.

### 3d. Unproven candidate whose exposure is already closed

- **2022-07-01** (390 bars) — the 2022 analog of 2016-07-01 — sits inside the
  frozen F4 warmup window; the v2 WARMUP entry stands; no additional entry.
  Recorded for any future re-fold.

## 4. What the corpus-wide sweep found (202 candidate dates, 2010-2026)

- **2011-2015**: zero unproven candidates (all 56 PDF candidates truncated/closed;
  106 regulars) — v2 PASS stands unchanged.
- **2016**: 8 in-panel candidate sessions (7 truncated + 1 FULL = 2016-07-01),
  3 candidate closures absent from the panel (01-01, 03-25, 12-26). **The
  enumeration itself remains NOT_RUN at the evidence level** — no 2016 day-level
  artifact exists anywhere in the committed corpus (M1 sweep: every round dir —
  cme_cal_gap, DEEPFOUR cme_cal, cal_eb, cal_janq, cal_close, DATACONTRACT,
  readiness, 10SYMS root corpus — contains zero 2016 schedule PDFs/XLS/HTML;
  the archived 2016 page is floor/ClearPort-tier only). What closes is the
  EXPOSURE: all 8 sessions now excluded fail-closed.
- **2017-2025**: every floor-EQUITIES-named day (2017 Jul 3 + Nov 24; 2018
  Jul 3 + Nov 23 + Dec 24; 2019 Nov 29 + Dec 24; 2020 Nov 27 + Dec 24) and every
  family main day was already excluded (HOLIDAY_UNCERTAIN / COVERAGE_LT60).
  Exactly 3 full-bar unproven candidates existed — 2020-07-02, 2021-07-02,
  2021-12-31 — all now excluded. 2022-07-01 unproven but warmup-closed.
- **2010**: the 2010 official PDF equity sections were extracted this lane
  (sha `808ced0d…`, page-cited). M1 register gap found: 2010-11-26 (Black
  Friday, EC 1215 CT) was omitted from the v1 FACT legality list — but its
  panel session is truncated and was COVERAGE_LT60-excluded since v1
  (exposure closed; register corrected here).
- **Non-candidate adjacent positions** (Fri-before-MLK/Presidents/Memorial/Labor,
  Wed-before-Thanksgiving, Mon-after-Good-Friday, Dec 23, Dec 30, Columbus,
  Veterans — including all 2016 instances): machine-verified 390-bar sessions
  with no holiday class in every corpus year, with day-level PDF REGULAR
  adjudications for the same weekday configurations (5/5 families; 1/1
  Sun-config analogs for Dec 23 / Dec 30) and explicit 2016 floor-table equity
  clearance. **They stay eval-eligible** — no holiday question arises for them
  under the 2011-15 pattern basis. Candidacy is NOT extended to them.

## 5. Invariants

- **Identity table 24 unchanged** (P-A 8 + P-B 8 + FOMC 4 + C1-C4 4); budgets 24.
- **Donor law honored** (`repair/DONOR_LAW_CARRYOVER.md`): the SL-donor
  exclusion SESSION SET remains the v1 set (139 sessions) on v1 labels. The 4
  new exclusions were v1 donor-admitted and REMAIN donor-admitted; these
  additions alter EVAL membership only. The D-V2-1 failure mode cannot recur.
- Panel parquet untouched (universe JSON only); raw data untouched; no PnL or
  quarantined-numeric read; zero network; heavy lock FREE_PROVEN at start.

## 6. Honest status (M5)

| epoch | verdict |
|---|---|
| 2010 | Covered with one register gap closed — 2010 PDF equity sections day-level; the 2010-11-26 omission from the v1 FACT list is register-corrected; its exposure was already closed by truncation. No unproven in-span candidates remain. |
| 2011-2015 | PASS (unchanged from v2) — every candidate session PDF-adjudicated. |
| 2016 | **EXCLUDED_FAILCLOSED.** Candidate windows enumerated from the 2011-15 patterns; all 8 in-panel candidate sessions now carry `HOLIDAY_2016_UNPROVEN_FAILCLOSED`; the one full-bar candidate (2016-07-01) is excluded. **The 2016 day-level enumeration itself remains NOT_RUN** (NOT_RUN_OBTAIN — zero network; resolving it requires owner-authorized retrieval of 2016 per-holiday schedule artifacts, route: web.archive CDX of the holiday-calendar files family, 2016 vintages). |
| 2017-2025 | No new exposure except the 3 now-excluded full-bar candidates (2020-07-02, 2021-07-02, 2021-12-31); everything else already excluded. |
| 2026 | FACT-covered in span; 2026-07-02 proven regular at product level and kept. |

**No pattern-candidacy was converted into "proven regular" anywhere.** The only
"proven regular" keeps rest on committed day-level artifacts naming that exact
date (two 2010 PDFs; one 2026 product-level FACT cell).

— End EVAL_V3 (FUTURES-ES-PB1-V1 / Y2016-AUDIT).
