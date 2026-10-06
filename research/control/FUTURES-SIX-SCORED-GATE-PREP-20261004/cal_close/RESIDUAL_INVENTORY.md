# RESIDUAL_INVENTORY — CAL-CLOSE lane, round FUTURES-SIX-SCORED-GATE-PREP-20261004

Pre-fetch enumeration (written BEFORE any network attempt of this lane). Generated 2026-10-04.
Worktree HEAD (measured at lane start, bare 40-hex): `893db28cd1b3299c914369ec08cb33f68bf5798a`.

Sources read (all committed in THIS worktree, cited OBSERVED file:field):
- `research/control/FUTURES-SIX-ADOPT-PREP-20261004/cal_eb/calendar_delta.json` (+ CAL_EB_REPORT.md, captures/)
- `research/control/FUTURES-SIX-ADOPT-PREP-20261004/cal_janq/calendar_delta.json` (+ CAL_JANQ_REPORT.md, captures/)
- `research/control/FUTURES-SIX-READINESS-20261004/es/es_session_holiday.json`, `es/q5_independent_verify/verify_report.json`, `es/es_expiry_recheck.json`

Law: a cell is CLOSED only with documented absence evidence (PROVEN-ABSENT) or hash-verified dated
official capture (OBTAINED). Aged-out archive windows are INCONCLUSIVE, never counted. No rule
derivation (IMM/3rd-Wednesday) is used anywhere in this lane.

---

## A. FX quarterly expiry grid (68 cells × 4 codes = 272; round-2 cumulative 256/272)

Open cells after round 2 = 16. Classification:

### A1. PROVEN-ABSENT (archived) — CLOSED, no fetch

| # | cell | identity | decisive absence evidence (cited) |
|---|------|----------|-----------------------------------|
| 1 | 6E 2026Q3 | ECU26 | cal_eb open_cells_status.6E_expiry_2026Q3: Future/58 max capture 2021-07-03 (rows end Jun-2026); Download.xls?productId=58 single capture @2017-09-21; Quotes/58/G max @2021-03-13; cspecs = prose rules (derivation forbidden); live blocked |
| 2 | 6E 2026Q4 | ECZ26 | same chain as ECU26 (cal_eb 6E_expiry_2026Q4) |
| 3 | 6B 2023Q1 | BPH23 | cal_eb 6B_expiry_2023Q1: all 4 archived Download.xls=42 captures ≥ 2024-09-03; expired-contract drop PROVEN (BPU24 present @0903 sheet, gone @1108 sheet); Future/42 max 2018-04-08 |
| 4 | 6B 2023Q2 | BPM23 | same service-drop chain (cal_eb 6B_expiry_2023Q2) |
| 5 | 6B 2023Q3 | BPU23 | same chain (cal_eb 6B_expiry_2023Q3) |
| 6 | 6B 2023Q4 | BPZ23 | same chain (cal_eb 6B_expiry_2023Q4) |
| 7 | 6B 2024Q1 | BPH24 | same chain (cal_eb 6B_expiry_2024Q1) |
| 8 | 6B 2024Q2 | BPM24 | same chain (cal_eb 6B_expiry_2024Q2) |
| 9 | 6J 2023Q1 | J1H23 | cal_janq absence_and_blocks.6J_2023_quarters: complete no-collapse CDX — Future/69 = 2015/2017 only (pre-span); Download.xls=69 = 2024-09-04, 2025-11-04 only (post-expiry; earliest row Sep-2024) |
| 10 | 6J 2023Q2 | J1M23 | same chain (cal_janq J1_expiry.quarters_2023.2023Q2) |
| 11 | 6J 2023Q3 | J1U23 | same chain (cal_janq J1_expiry.quarters_2023.2023Q3) |
| 12 | 6J 2023Q4 | J1Z23 | same chain (cal_janq J1_expiry.quarters_2023.2023Q4) |
| 13 | 6A 2023Q1 | ADH23 | cal_janq AD_expiry.quarters_2023H1.2023Q1: Future/37 = 2016/2018 pre-span + 2023-09-16 post-expiry (first row ADU23); Download.xls=37 = ZERO archived captures |
| 14 | 6A 2023Q2 | ADM23 | same chain (cal_janq 2023Q2) |

All 14 remain un-fetchable by any permitted route as of the 2026-10-04 CDX state: the only surfaces
that could carry them (Future/{37,42,58,69}, Download.xls?productId={37,42,58,69}, Quotes/58/G,
ContractSpecs) are either pre-span, post-expiry-drop, prose-rule-only, or live-blocked. A future
Wayback crawl could in principle change this; at the next freeze these are DOCUMENTED EXCLUSIONS,
not hidden gaps.

### A2. NOT_RUN (identity not determinable) — flagged to owner, never inferred

| # | cell | identity | status |
|---|------|----------|--------|
| 15 | 6J missing cell A | undetermined | cal_janq J1_expiry.attempted_scope_note: dispatch accounting says 10 missing 6J cells; bounded scope covered 8; the other 2 are flagged to the owner, NOT inferred. Fetching is impossible without an identity; deriving identity from grid arithmetic is forbidden. |
| 16 | 6J missing cell B | undetermined | same |

Note: with 6J at 62/68 and 4×2023 open, 272−256−14 = 2 — the arithmetic is consistent with exactly
2 undetermined 6J cells, but the identity itself is NOT derived here (derivation prohibition).

## B. Holiday-deviation windows

### B1. 6B holidays 2022-12-31 .. 2026 (42 windows) — PROVEN-ABSENT (structural) — CLOSED
cal_eb 6B_holiday_* (42 entries, all NOT_OBTAINED with fresh 709-row CDX evidence): archived
trading-hours-by-product captures carry id lists {316,133,425,300,58,437,22,8478,5201,10191},
{"", "5224"} only; standalone id=42 rows = 0. Holiday advisory/settlement PDF families carry no
per-product trading hours (two-PDF family inspection). MY OWN LOCAL RE-VERIFICATION this lane
(no fetch): exact id-token parse of committed
`FUTURES-SIX-ADOPT-PREP-20261004/cal_eb/captures/cdx_th_full.txt` (709 rows, 80 distinct capture
timestamps): id=42 → 0 rows (id=58 → 685, id=133 → 688 rows as sanity anchors). Absence CONFIRMED.

### B2. 6J holidays 2023-2026 (42 windows), 6A holidays 2023-2026 (42 windows) — PROVEN-ABSENT (structural) — CLOSED
cal_janq sixJ_holiday_windows_2023_2026: NOT_OBTAINED 0/42 for BOTH codes; same id-list evidence.
MY OWN LOCAL RE-VERIFICATION this lane: id=69 → 0 rows, id=37 → 0 rows in the same committed CDX
inventory. Absence CONFIRMED.

### B3. 6E holidays — 34/42 OBTAINED (prior rounds); 8 windows INCONCLUSIVE_AGED_OUT — CLOSED-as-excluded
cal_eb 6E_holiday_2022-12-31, 2023-01-15, 2023-02-19, 2023-04-06, 2023-05-28, 2023-06-18,
2023-07-03, 2025-01-05: each window has exactly ONE archived 200-capture of any overlapping window
URL at +369d..+629d out-of-bracket (service ≈365d lookback, empirically bracketed 307d in / 369d
out); no forward-horizon captures exist. INCONCLUSIVE_AGED_OUT — not counted, documented exclusion.

### B4. ES holidays — CLOSED (round-1, verified)
2026 calendar-year: `FUTURES-SIX-READINESS-20261004/es/es_session_holiday.json`
holiday_deviation_windows_2017_2026[year=2026]: `es_product_globex_times` =
"OBTAINED_PERMITTED_AND_INDEPENDENTLY_VERIFIED ... weekly template + all 11 deviation windows
(23 dated trading cells)"; independent verification committed at
`es/q5_independent_verify/verify_report.json`: `es_2026_holiday_deviation_cells.n_claimed_cells=23,
n_match=23, n_mismatch=0`; verdict `VERIFIED_WITH_RESIDUALS` (8 of 23 Q5 captures missing from disk;
all present captures reproduce claimed cells). Citation level in THIS worktree: OBSERVED (committed
verification outputs); the raw capture bytes live in the P3-quarantined worktree which this lane is
FORBIDDEN to access. 2011-2025 ES product-level early-close times: NOT_TRANSCRIBED
(`es_session_holiday.json` not_obtained_register[0]) — unchanged, fail-closed law applies.
ES expiry: 68/68 (`es_expiry_recheck.json` rederivation.count_68_complete=true).

### B5. NQ 2026 holiday-deviation windows (10 windows) — STILL-OPEN at product-code level (dispatch target)
cal_janq NQ_holiday_deviation_windows_2026 status register:
- 4 windows OBTAINED_ADVISORY_NORMAL_OR_CLOSURE_ONLY (2026-01-18 MLK, 02-15 Presidents, 06-17
  Juneteenth, 09-06 Labor): advisory documents normal pre-holiday settlement + holiday closure, no
  early-close row.
- 5 windows OBTAINED_ADVISORY_CLASS_LEVEL (05-24 Memorial, 07-02 July-4-observed, 12-23 Christmas,
  12-24 Christmas-Eve, 12-30 NYE): dated class rows (IR/Metals/Energy/FX/Equity&Crypto), verbatim,
  NOT mapped to product codes (family-transplant prohibition).
- 1 window NOT_OBTAINED (2026-04-01 Good Friday): settlement-times advisory "Pending" at the only
  archived vintage @20251013214632 → **STILL-OPEN, fetchable in principle** (newer Wayback crawls may
  exist after Feb-2026; a CDX row for 2026-good-friday-clearing-advisory.pdf @20260202002306 already
  exists in cal_janq/captures/cdx_holiday_files_2026.txt, but that is the clearing-memo family, not
  the settlement-times family).
- Product-code level (id=146) for ALL 10 windows: NOT_OBTAINED. MY OWN LOCAL RE-VERIFICATION this
  lane: id=146 → 0 rows in committed cdx_th_full.txt (repairs cal_janq's probe, whose in-log attempt
  failed curl rc=3). Remaining permitted routes: `services/trading-hours-holiday-download` (2
  archived captures @20250422003144, @20250829195952 — BOTH returned HTTP 403 at the Wayback edge in
  round 2) and live cmegroup.com (standing ECONNREFUSED). **This lane will attempt 1 replay of the
  holiday-download capture (the round-2 BLOCKED_TRANSPORT 403 case named by the dispatch) and record
  the honest status.**

### B6. ES 2026 holiday-deviation spot-upgrade — THIS LANE TARGET
ES 2026 is closed via committed round-1 verification (B4), but the raw captures are not present in
this worktree. This lane will fetch 3 archived `trading-hours-by-product` 2026-window captures
(fromEventDate 2026-01-18, 2026-04-01, 2026-07-02; id list includes 133=ES; URLs read from committed
cdx_th_full.txt, latest-ts 200 captures) to hold direct FACT-grade evidence in THIS worktree and to
demonstrate at content level that the id list of this capture family never includes 146.

## C. D5 — BLS CPI Jan-2026 announcement pin — STILL-OPEN (fetchable, official domain direct)
No BLS evidence exists anywhere in the adopted captures. Target: bls.gov CPI release-schedule page
(official domain, direct fetch permitted). Pin required: the announcement date (and time if published)
of the CPI release covering January 2026. If unobtainable: NOT_OBTAINED with evidence.
Note: the D5 item definition itself is not present in committed artifacts in this worktree (grep for
D5/D12 in FUTURES-SIX-* rounds returns nothing); this lane takes the dispatch packet text as the
definition of the work item.

## D. Fetch plan (bounded: ≤30 attempts, ≤2 per (url,method), all logged to fetch_log.jsonl)

| # | target | route | planned attempts |
|---|--------|-------|------------------|
| 1 | ES 2026 spot windows ×3 (01-18, 04-01, 07-02) | web.archive.org id_ replays of trading-hours-by-product | 3 |
| 2 | Good-Friday-2026 settlement-times advisory: all timestamps | CDX no-collapse probe | 1 |
| 2b | Good-Friday-2026 advisory newer vintage (if probe finds one) | web.archive.org id_ | ≤1 |
| 3 | holiday-download @20250829195952 (round-2 403 case) | web.archive.org id_ retry | 1 (+1 only if transient-looking) |
| 4 | BLS CPI release schedule page | bls.gov direct | 1 |
| 4b | BLS Jan-2026 CPI news-release page (if schedule page pins the date) | bls.gov direct | ≤2 |

Everything else in this inventory is CLOSED with no fetch, per sections A/B.
