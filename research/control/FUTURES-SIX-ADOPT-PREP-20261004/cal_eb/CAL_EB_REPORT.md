# CAL_EB_REPORT — bounded $0 permitted-route calendar search (6B priority, then 6E)

Cycle: FUTURES-SIX-ADOPT-PREP-20261004 · lane CAL-EB · generated 2026-10-04T05:03:24Z
Worktree HEAD: 9fb66c88d464fd90748bc04d78280c2d87939cd3 (rev-parse once; verified == dispatch base)

## Method
- Transport: plain curl to web.archive.org ONLY (CDX + id_ snapshots). No live cmegroup.com; no proxies/SNI tricks/logins. <=2 attempts/URL/method honored. **Budget used: 10/35 attempts; zero BLOCKED_TRANSPORT events.**
- Sources enumerated fresh this lane: full trading-hours-by-product CDX (709 rows), full ProductCalendar/Download.xls CDX (23 rows), ProductCalendar/Future/58 CDX (10 rows), Quotes/Future/58/G CDX (24 rows), holiday-calendar files CDX 2009-2027 (500+500 rows), plus round-1 and sibling CDX inventories (read-only).
- Content inspection: holiday advisory PDF (2023 MLK) and holiday settlement-times PDF (2025 MLK) fetched and text-extracted — neither family carries per-product trading hours.

## Headline result
**0 new grid cells.** Every open cell remains NOT_OBTAINED (or INCONCLUSIVE_AGED_OUT for the 8 known 6E windows) — but each now carries fresh primary absence evidence, and the 6B structural-absence proof is materially stronger (two-vintage XLS drop demonstration).

## Before/after per code
| grid | before | after |
|---|---|---|
| 6E expiry | 66/68 (14/16 in 2023-2026) | 66/68 — unchanged; ECU26/ECZ26 NOT_OBTAINED |
| 6B expiry | 62/68 (10/16 in 2023-2026) | 62/68 — unchanged; 2023Q1-2024Q2 NOT_OBTAINED (structural) |
| 6E holidays | 34/42 documented, 8 INCONCLUSIVE | 34/42 — unchanged; 8 windows proven single-capture out-of-bracket |
| 6B holidays | 0/42 | 0/42 — unchanged; zero id=42 across fresh 709-row CDX + PDF families carry no product hours |

## Open-cell table (all NOT_OBTAINED / INCONCLUSIVE)
| cell | status | decisive absence evidence |
|---|---|---|
| 6E ECU26 (2026Q3) | NOT_OBTAINED | Future/58 max capture 2021-07-03 (rows end Jun-2026); Download.xls=58 only @2017-09-21; Quotes/58/G max @2021-03-13; cspecs = prose rule text (forbidden); live BLOCKED (sibling) |
| 6E ECZ26 (2026Q4) | NOT_OBTAINED | same chain as ECU26 |
| 6B BPH23..BPM24 (2023Q1-2024Q2, 6 cells) | NOT_OBTAINED | all 4 archived Download.xls=42 captures >= 2024-09-03; expired-contract drop PROVEN (BPU24 in @0903 sheet, gone @1108 sheet); Future/42 max 2018-04-08; live BLOCKED (sibling) |
| 6B holidays 2023-2026 (42 windows) | NOT_OBTAINED | fresh 709-row CDX: id lists = {10-id list, empty, 5224, 133, 318, 133,219, 167,133}; standalone id=42 = 0 rows; advisory/settlement PDFs = clearing memos, zero product trading hours |
| 6E holidays 2023H1 x7 + 2025-01-05 | INCONCLUSIVE_AGED_OUT | each window has exactly ONE archived 200-capture of ANY overlapping window URL, at +369d..+629d (bracket 307d-in / 369d-out); no forward-horizon captures exist |

## Honest absences / limits
- The dispatch named 6B holidays as PRIORITY: the priority target is **not achievable by any permitted route** — the archived per-product holiday-hours service never includes 6B, and the holiday-calendar PDF families are clearing/settlement memos without product trading hours. This is documented absence, not a gap in effort.
- 2026 holiday windows for 6B: 2026 clearing advisories ARE archived (mlk/presidents/good-friday/memorial/juneteenth/4july/labor/columbus/veterans/thanksgiving/christmas/new-years) but carry no product trading hours (family inspected); 2026 windows for 6E were already 10/10 via the service in round-1.
- New dated official rows this lane, OUTSIDE the quarterly grid (recorded for completeness, not counted as cells): BPG25 last trade 2025-02-14 (Fri, as published for a serial month), BPJ25 2025-04-14 (Mon), BPU29 2029-09-17 (Mon) — the rows present in this lane's @2024-11-08 capture and absent from round-1's @2024-09-03 capture (captures/pcal_42_6b_dl_20241108.xls, sha256 b38ef64e...). Serial-month rows BPX24/BPF25/BPJ25 were already present in the round-1 Sep-03 vintage.
- One 404 at attempt 7: my URL reconstruction dropped the /2025/ path segment; corrected on the next attempt (different URL, fresh attempt budget). Not a transport block.

## Validations
- T1 hashes: 13 consumed captures re-hashed, 0 mismatches (covers this lane's 9 captures + round-1's XLS + 3 CDX inventories).
- T2 6B cross-vintage QA: 21 shared quarterly rows @2024-09-03 vs @2024-11-08 — 0 disagreements; rows dropped by later vintage = ['BPU24', 'BPV24'] (drop behavior demonstrated); new rows = ['BPG25', 'BPJ25', 'BPU29'].
- T3 expiry legality: 24 carried cells — weekday Monday, day in [9,21], inside contract month, DST-regime annotated; 0 violations.
- T4 holiday legality: 34 documented windows re-checked (event dates within window+4d, HH:MM) — 0 violations; 8 aged-out windows re-checked in fresh CDX — 0 recoverable.
- T6 absence enumerations: trading-hours 709 rows / 0 id=42; Download.xls 23 rows; Future/58 max 2021-07-03; Quotes/58/G max 20210313102336.

## Transport compliance statement
Permitted routes only; 10/35 attempts; max 1 attempt per URL; zero connection-level blocks (no BLOCKED_TRANSPORT recorded); live cmegroup.com never contacted; no bypass techniques. All fetches logged to fetch_log.jsonl with url/method/status/bytes/sha256/utc; all captures under captures/ with sha256 in SHA256SUMS_lane.txt.
