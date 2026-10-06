# RESIDUAL_BASELINE — CAL-COST lane, round FUTURES-5SYM-PRESCORED-20261005 (PREP-only)

Written BEFORE any network attempt of this lane (pre-fetch enumeration). Generated 2026-10-05.
Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep`,
branch `prep/futures-5sym-prescored-20261005`. HEAD at lane start (measured once):
`b051d61e3a8d061412e1837bfc046a419e16dd10`.

Symbols in scope: **NQ, 6E, 6B, 6J, 6A.** Prior attempt of this lane died to infrastructure
rate-limiting before writing anything — this file is written fresh (no prior lane artifacts exist).

## Committed baseline sources (all read in THIS worktree, cited OBSERVED file:section)

- `research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/cal_close/` —
  `RESIDUAL_INVENTORY.md` (§A1, §B3–B6), `CAL_CLOSE_REPORT.md` (§1, §3, §5),
  `calendar_close_delta.json` (classification_changes, cells_blocked, coverage).
- `research/control/FUTURES-SIX-ADOPT-PREP-20261004/cal_eb/` — `CAL_EB_REPORT.md`,
  `calendar_delta.json` (6E/6B grids + holidays).
- `research/control/FUTURES-SIX-ADOPT-PREP-20261004/cal_janq/` — `CAL_JANQ_REPORT.md`,
  `calendar_delta.json` (6J/6A/NQ grids, holidays, advisories).
- Event-calendar corpus check (this lane, local grep): FOMC 2026 dates present through
  2026-09-16 only in `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_fomc_stats.json`
  (2026-01-28, 03-18, 04-29, 06-17, 07-29, 09-16); BoE MPC calendars 2020→2027 described as
  "assembled" in `FUTURES-DEEPRESEARCH-V2-20261003/dossiers_v2/6B_DEEP_v2.md` §L40-41 (corpus
  provenance, NOT official-capture grade in this worktree); no committed BoJ MPM / RBA 2026
  schedule evidence found in this worktree.

## Law (carried forward)

A cell is CLOSED only with (a) hash-verified dated official capture (OBTAINED) or (b) documented
absence evidence (PROVEN_ABSENT). Aged-out archive windows are INCONCLUSIVE_AGED_OUT, never
counted. NO rule derivation (IMM dates / 3rd-Wednesday / calendar arithmetic) anywhere; official
per-product content only. Fail-closed: unprovable cells become DOCUMENTED EXCLUSIONS at freeze.
Transport law this lane: permitted routes = WebFetch tool, web_reader, web.archive.org archived
pages, plain curl; MAX 2 attempts per URL; total fetch budget ≤40, every fetch logged to
`fetch_log.jsonl`; captures under `captures/` hashed in `SHA256SUMS_calcost.txt`.

---

## Per-symbol still-open matrix (baseline BEFORE this lane's attempts)

### NQ — 10 open cells (one dimension)

| # | cell | dimension | state | provenance |
|---|------|-----------|-------|------------|
| NQ-1..10 | NQ 2026 holiday-deviation windows, **product-code level** (id=146), 10 windows: 01-18 MLK, 02-15 Presidents, 04-01 Good Friday, 05-24 Memorial, 06-17 Juneteenth, 07-02 July-4-obs, 09-06 Labor, 12-23 Christmas, 12-24 Christmas-Eve, 12-30 NYE | holiday session times, product code | **NOT_OBTAINED 0/10** | cal_janq NQ_holiday_deviation_windows_2026 (0/10); cal_close §2: id=146 = 0 rows in committed 709-row CDX (`FUTURES-SIX-ADOPT-PREP-20261004/cal_eb/captures/cdx_th_full.txt`); cal_close §1: only service route (`services/trading-hours-holiday-download` @20250422003144 / @20250829195952) = 403 at Wayback edge (round-2 four 403s + cal_close 403, 42-byte body sha `f249b63c…`), live cmegroup.com standing ECONNREFUSED |

NOT open at NQ (recorded to prevent double-counting): 2026 advisory class-level 10/10 OBTAINED
(cal_close closed the last window, Good-Friday, via `adv_gf_2026_20260913.pdf` sha `a14a3284…`);
NQ 2026 quarterly expiry 4/4 OBTAINED (cal_janq, triple vintage `pcal_146_nq_*.json`).

### 6E — 8 open cells (one dimension)

| # | cell | dimension | state | provenance |
|---|------|-----------|-------|------------|
| 6E-1..8 | 6E holiday windows 2022-12-31, 2023-01-15, 2023-02-19, 2023-04-06, 2023-05-28, 2023-06-18, 2023-07-03, 2025-01-05 | holiday session times | **INCONCLUSIVE_AGED_OUT (8)** — each window has exactly ONE archived 200-capture of any overlapping window URL, at +369d..+629d out-of-bracket; no forward-horizon captures | cal_close calendar_close_delta.json `INCONCLUSIVE_AGED_OUT_closed_as_excluded`; cal_eb CAL_EB_REPORT open-cell table. Aged-out cells are never counted; attempt ONLY if an archived vintage plausibly covers (i.e. a fresh capture of the per-product service covering these windows appears) |

NOT open at 6E: expiry 66/68 — ECU26 (2026Q3), ECZ26 (2026Q4) upgraded to
CLOSED_PROVEN_ABSENT in cal_close (Future/58 max capture 2021-07-03 rows-end-Jun-2026;
Download.xls=58 single @2017-09-21; Quotes/58/G max @2021-03-13). Holidays otherwise 34/42
OBTAINED (prior rounds; ×3 corroborated FACT-grade in cal_close via id=58 rows in svc captures).

### 6B — 6 expiry cells + 42 holiday windows

| # | cell | dimension | state | provenance |
|---|------|-----------|-------|------------|
| 6B-1..6 | expiry BPH23 (2023Q1), BPM23 (2023Q2), BPU23 (2023Q3), BPZ23 (2023Q4), BPH24 (2024Q1), BPM24 (2024Q2) | quarterly last-trade dates | **PROVEN_ABSENT at 2026-10-04 CDX state** (documented exclusion): all 4 archived Download.xls=42 captures ≥ 2024-09-03; expired-contract drop PROVEN two-vintage (BPU24 present @0903 sheet, gone @1108 sheet); Future/42 max 2018-04-08 | cal_eb CAL_EB_REPORT open-cell table; cal_close classification_changes. Dispatch target this lane: hunt EARLIER Wayback snapshots of the CME product-calendar URL (2023-01..2024-09); a pre-expiry vintage would flip these to OBTAINED |
| 6B-7..48 | holidays, all 42 windows 2022-12-31..2026 | holiday session times, product level | **PROVEN_ABSENT (structural)** — archived per-product holiday-hours captures never carry id=42 (0 rows across the 709-row committed CDX, 80 timestamps; anchors id=58=685, id=133=688); advisory/settlement PDF families carry no product hours (two-PDF family inspection) | cal_close §2 local re-verification; cal_eb 6B_holiday_* ×42 |

### 6J — 6 expiry cells + 42 holiday windows

| # | cell | dimension | state | provenance |
|---|------|-----------|-------|------------|
| 6J-1..4 | expiry J1H23, J1M23, J1U23, J1Z23 (2023 quarters) | quarterly last-trade dates | **PROVEN_ABSENT at 2026-10-04 CDX state** — complete no-collapse CDX: Future/69 = 2015/2017 only (pre-span); Download.xls=69 = 2024-09-04 + 2025-11-04 only (post-expiry; earliest row Sep-2024) | cal_janq absence_and_blocks.6J_2023_quarters (`captures/cdx_future69.txt`, `cdx_dl69.txt`); cal_close classification_changes |
| 6J-5,6 | expiry: 2 cells, identity undetermined | quarterly last-trade dates | **NOT_RUN — identity not determinable without forbidden derivation; flagged to owner** | cal_janq J1_expiry.attempted_scope_note; cal_close NOT_RUN_flagged |
| 6J-7..48 | holidays, all 42 windows 2023-2026 | holiday session times, product level | **PROVEN_ABSENT (structural)** — id=69 = 0 rows in committed 709-row CDX | cal_close §2 (re-derived from committed bytes after cal_janq's in-log probe failed curl rc=3; conclusion confirmed) |

### 6A — 2 expiry cells + 42 holiday windows

| # | cell | dimension | state | provenance |
|---|------|-----------|-------|------------|
| 6A-1,2 | expiry ADH23 (2023Q1), ADM23 (2023Q2) | quarterly last-trade dates | **PROVEN_ABSENT at 2026-10-04 CDX state** — Future/37 = 2016/2018 (pre-span) + 2023-09-16 (post-expiry, first row ADU23); Download.xls=37 = ZERO archived captures | cal_janq AD_expiry.quarters_2023H1 (`captures/cdx_future37.txt`, `cdx_dl37.txt`); cal_close classification_changes |
| 6A-3..44 | holidays, all 42 windows 2023-2026 | holiday session times, product level | **PROVEN_ABSENT (structural)** — id=37 = 0 rows in committed 709-row CDX | cal_close §2 |

### Event calendars (decision-time-knowable; new register this lane)

| # | cell | state | provenance |
|---|------|-------|------------|
| EV-1 | BoE MPC remaining-2026 decision dates | OPEN (corpus-assembled only, not official-capture grade in this worktree) | 6B_DEEP_v2.md L40-41 describes 2020→2027 MPC calendars assembled from bankofengland.co.uk; no hash-pinned official capture of the 2026 dates exists in this worktree |
| EV-2 | BoJ MPM remaining-2026 decision dates (dates only; intraday stamps stay NOT_IN_CORPUS) | OPEN | no committed BoJ 2026 schedule evidence located |
| EV-3 | RBA 2026 decision dates (6A contingency) | OPEN | no committed RBA 2026 schedule evidence located |
| EV-4 | FOMC remaining-2026 decision dates (post-2026-09-16) | OPEN (corpus carries through Sep only) | ES_fomc_stats.json per_event_day_level 2026 rows end at 2026-09-16 |

## Closure attempt plan (bounded; ≤2 attempts per URL; every attempt logged)

| priority | target | route class | planned attempts |
|---|--------|-------------|------------------|
| 1 | NQ 2026 product-level holiday times | fresh no-collapse CDX of `services/trading-hours*`; re-attempt holiday-download archived replays ×2 timestamps; CME holiday-calendar page archived vintages | ~6 |
| 2 | 6B product calendar 2023Q1-2024Q2 | fresh no-collapse CDX of `CmeWS/mvc/ProductCalendar*` (hunt pre-2024-09 productId=42 vintages); alternate surface CDX `Quotes/Future/42*` | ~2 (+replays if found) |
| 3 | 6J/6A 2023-quarter expiries | covered by the same ProductCalendar* CDX probe (productIds 69/37) | 0 extra |
| 4 | 6E 8 aged-out windows | only if a fresh vintage plausibly covers; else stay INCONCLUSIVE | 0-2 |
| 5 | BoE/BoJ/RBA/FOMC remaining-2026 | official pages direct (curl/WebFetch), archive fallback | ~4-8 |

Everything else in this inventory is CLOSED with no fetch; this lane does not re-open proven-absent
cells except where a permitted route plausibly serves the value (priority 2 earlier-vintage hunt,
priority 1 fresh-CDX check for post-2026-10-04 crawls).
