# CAL_JANQ_REPORT — bounded $0 permitted-route calendar search (6J / 6A / NQ)

Round FUTURES-SIX-ADOPT-PREP-20261004, lane CAL-JANQ (task 2, owner "Việc 2" / D12 continuation).
Generated: 2026-10-04. Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-adopt/prep`,
branch `codex/futures-six-adopt-prep-20261004`, actual_start_sha = dispatch_sha = `9fb66c88d464fd90748bc04d78280c2d87939cd3` (measured, equal).

## 1. Before → after

| Code / dimension | Before (dispatch baseline) | After (measured this lane) | Delta source |
|---|---|---|---|
| 6J expiry (68-cell grid 2010-2026) | 58/68 | **62/68** | +4: J1H26/M26/U26/Z26 2026 quarters, dual vintage |
| 6A expiry (same grid) | 62/68 | **66/68** | +4: ADH26/M26/U26/Z26 from re-verified Sep-2023 capture |
| NQ 2026 holiday-deviation windows (product-code level) | 0 | **0/10** | all 5 routes exhausted; absence evidence recorded |
| NQ 2026 windows (advisory class-level, separate register) | — | **5/10 windows** carry dated class rows (verbatim, NOT mapped to codes) | 2026 settlement-times advisories |
| NQ 2026 expiry cells (bonus register) | — | **4/4** (NQH26 20 Mar, NQM26 18 Jun, NQU26 18 Sep, NQZ26 18 Dec 2026), triple-vintage | ProductCalendar/Future/146 @3 timestamps |
| 6J/6A holiday windows 2023-2026 (product-code level) | — | **0/42** each | no archived trading-hours capture carries id 69/37 |

Residuals: 6J 6 not-obtained cells = 4 × 2023 quarters + 2 cells whose identity is not determinable from
this lane's captures (dispatch says 10 missing; bounded scope was 8; the other 2 are flagged to the owner,
NOT inferred). 6A residual = exactly 2023Q1/Q2.

## 2. What was obtained, and from which bytes

All values below were read by this lane's own parsers from bytes whose sha256 this lane verified
(`extract_cells.py` hard-fails on mismatch; see `legality_validation.json`).

- **6J 2026 quarters — dual vintage agreement:**
  - `pcal_69_6j_dl_20240904.xls` (sibling Q5 capture, re-verified sha `09a85ef7…` vs sibling fetch log line 77;
    own xlrd parse): J1H26 `2026-03-16`, J1M26 `2026-06-15`, J1U26 `2026-09-14`, J1Z26 `2026-12-14`.
  - `captures/pcal_69_6j_dl_20251104.xls` (this lane's new fetch, Wayback `20251104084217`, sha `f4ed4513…`):
    identical values. Sheet "Product Calendar Nov 4 2025".
- **6A 2026 quarters (single vintage):** `pcal_37_6a_20230916051415.json` (sibling Q5, re-verified sha `dad89c31…`,
  own json parse): ADH26 `16 Mar 2026`, ADM26 `15 Jun 2026`, ADU26 `14 Sep 2026`, ADZ26 `14 Dec 2026`.
- **NQ 2026 expiry:** three new Wayback replays of `CmeWS/mvc/ProductCalendar/Future/146`
  (@20260304044204, @20260414104010, @20260710162138; bodies gzip-decoded locally, sha-pinned). Values agree
  across all vintages carrying each row; NQH26 appears only in the Mar-2026 capture (dropped after expiry).
- **2026 holiday-deviation advisories (class-level):** nine archived official CME
  `tools-information/holiday-calendar/files/2026/*settlement-times-2026.pdf` captures (Oct-2025 crawl).
  Deviation rows exist for Memorial (IR 12:00 CT 5/22), July-4-observed (IR 12:00 CT 7/2),
  Christmas-Eve (Ag/IR/**FX**/RE&Weather/**Equity & Crypto** 12:00 CT + Metals/Energy 12/24), NYE (IR 12:00/12:01 CT, Yield 10am CT 12/31).
  Good-Friday advisory is "Pending" at the only archived vintage → that window NOT_OBTAINED.
  MLK / Presidents / Juneteenth / Labor advisories document normal pre-holiday settlement + holiday closure
  (no early-close row). **No advisory contains any product code (NQ/J1/JPY/AD/AUD): zero occurrences,
  full-text scanned.** Class rows are recorded verbatim and are NOT mapped to product codes
  (family-transplant prohibition).

## 3. Corrections to round-1 / dispatch claims (evidence-first, stated with capture proof)

1. "6J 2026 quarters CONFIRMED ABSENT from `pcal_69_6j_dl_*.xls`" — **contradicted**: the 2026 quarter rows
   with dates ARE in the re-verified Q5 XLS (and corroborated by the new Nov-2025 XLS). Only the 2023 quarters
   are absent (expired-contract drop by the Download service; earliest row Sep-2024).
2. "`pcal_37_6a_*.json` exhausted" — accurate for 2023Q1/Q2, **incomplete for 2026**: the Sep-2023 capture
   carries full 2026 last-trade dates; those 4 cells were not previously credited.

## 4. Absence evidence (why NOT_OBTAINED, never inferred)

- **6J 2023 quarters:** complete no-collapse CDX enumeration of every 6J product-calendar URL:
  `Future/69` = 2015-09-18 / 2017-05-06 / 2017-07-28 only (pre-span), `Download.xls?productId=69` =
  2024-09-04 / 2025-11-04 only (post-expiry). No capture crawled between 2017-07-28 and 2024-09-04.
  Evidence: `captures/cdx_future69.txt`, `captures/cdx_dl69.txt`.
- **6A 2023Q1/Q2:** `Future/37` = 2016-05-18 / 2018-02-27 / 2018-06-23 (pre-span) + 2023-09-16 (post-expiry;
  first row ADU23). `Download.xls?productId=37` = **zero** archived captures (0-byte CDX result, 2 attempts).
  Evidence: `captures/cdx_future37.txt`, `captures/cdx_dl37.txt`.
- **NQ / 6J / 6A trading-hours deviations (product-code level):** zero archived
  `services/trading-hours-by-product` captures carry ids 146/69/37 (fresh CDX regex probe 0 rows; sibling Q5
  799-urlkey enumeration corroborates — id variants contain only ZN/ES/ZC/CL/6E/GC/LE/CSC/BTC/LBR sets).
  The `ProductCalendar` JSONs (3 NQ vintages parsed) carry contract rows only — no holiday/deviation keys;
  NQ ContractSpecs (sibling, re-verified) likewise weekly-template only.
- **`services/trading-hours-holiday-download`:** two CDX records exist (2025-04-22, 2025-08-29) but every
  replay is HTTP 403 at the Wayback edge (id_ curl, standard curl, WebFetch). Route stopped per transport law.
- **Live www.cmegroup.com:** standing BLOCKED (round-1/Q5 ECONNREFUSED evidence); not re-attempted.

## 5. Budget and legality

- **28 / 35 attempts used** (8 CDX probes, 19 snapshot fetches, 1 WebFetch method check). Per-URL/method cap
  ≤2 enforced throughout; `fetch_log.jsonl` (27 HTTP records + 0 skipped-record lines) is the audit trail.
- Methods: plain curl against web.archive.org (CDX + `id_`/standard replays) and one WebFetch — all permitted.
- No PnL, no S1, no GO/scoring/order, no registry/ledger writes, exactly one git command
  (`rev-parse HEAD`). Writes confined to `cal_janq/**` + `dispatch/handoff_CAL-JANQ.json`.
- No rule derivation (IMM/3rd-Wednesday), no current-calendar inference, no family transplants.
- commit_sha = null; per dispatch commit_policy the controller stages/commits — see handoff
  `no_commit_disclosure`.

## 6. Artifacts

- `calendar_delta.json` — per-cell OBTAINED (capture + sha + log line) / NOT_OBTAINED (absence) /
  BLOCKED_TRANSPORT; before→after accounting; corrections register.
- `legality_validation.json` — transport-law compliance, capture chain (15 hash-pinned captures),
  Q5 per-use re-verification records, derivation prohibitions.
- `fetch_log.jsonl` + `captures/` (19 files) — raw evidence.
- `fetch_lane.py`, `extract_cells.py` — deterministic fetch/extract tools (reproducible).

## 7. Recommended next action for owner/controller

Accept the +8 expiry cells (6J 2026 ×4 dual-vintage; 6A 2026 ×4 single-vintage) into the cumulative FX
calendar matrix (248 → 256/272 for the 4-code grid per round-1 accounting convention) and adjudicate the
class-level advisory register (5/10 NQ-relevant 2026 windows) — product-code deviation rows remain
NOT_OBTAINED and would require either an archive-reachable `trading-hours-holiday-download` or live
`trading-hours-by-product` access, both currently transport-blocked.
