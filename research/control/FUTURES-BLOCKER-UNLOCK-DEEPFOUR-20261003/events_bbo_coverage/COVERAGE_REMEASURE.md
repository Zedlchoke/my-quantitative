# Coverage Re-Measure (light) — IBKR staleness + vendor parquet windows

Task FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003, lane A5-EVENTS-BBO-COVERAGE,
dimension 3. Generated 2026-10-03. All claims below are **OBSERVED(script +
window)**: `coverage_remeasure_meta.py` (this directory), run 2026-10-03
12:55:59Z, runtime 0.11 s, output `coverage_remeasure.json`. Data roots
touched READ-ONLY (PATH LAW: vendor root has NO leading dot); parquet reads
are **footer metadata + row-group statistics only — zero data scans**; no
re-fetch was performed (D6 already ran 2026-10-03 AM).

## 1. IBKR raw staleness (max mtime per symbol group vs 2026-10-03T00:00Z)

Root: `~/.my-quantitative-data/futures-10syms-v1/raw/` (1,160 files total).

| symbol | n_files | max mtime (UTC) | age_days |
|---|---|---|---|
| NQ | 65 | 2026-10-02T02:37:14Z | 0.891 |
| ES | 65 | 2026-10-02T02:40:27Z | 0.889 |
| 6E | 115 | 2026-10-02T03:24:23Z | 0.858 |
| 6J | 115 | 2026-10-02T03:31:40Z | 0.853 |
| 6B | 115 | 2026-10-02T03:39:03Z | 0.848 |
| 6A | 115 | 2026-10-02T03:46:20Z | 0.843 |
| GC | 125 | 2026-10-02T03:10:25Z | 0.868 |
| SI | 125 | 2026-10-02T03:17:31Z | 0.863 |
| CL | 160 | 2026-10-02T04:11:33Z | 0.825 |
| NG | 160 | 2026-10-02T04:11:54Z | 0.825 |

Min mtimes all 2026-10-02T01:55–02:04Z (bulk start). Every group's newest
file is from the 2026-10-02 serial bulk — consistent with the
DATACONTRACT_QUALIFICATION §1.5 prior measure (local-time 09:37–10:46 span ==
UTC 01:55–04:12 window observed here).

## 2. D6 staging state (documented, NOT re-fetched)

`staging_refetch_20261003/` present with 6 probe files (3-row TRADES_1day_3D
per front: ESZ6/NQZ6/6EV6/6BV6/6AV6/6JV6), mtimes 2026-10-03T07:55:57–
07:56:58Z, 661–705 bytes each. Weekly-cadence state: D6 (2026-10-03, PASS)
established the serial re-fetch path; its 1-day wall probe showed expired
walls (ES/NQ=202509, FX=202512) did NOT recede — the discriminating re-probe
is due at the next weekly boundary. Raw/ untouched since (no file newer than
2026-10-02T04:11:54Z — the §1 table is the proof).

## 3. Vendor parquet coverage windows (footer + row-group stats only)

Root: `/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet/`
— 70 files, 930 MB, groups `AV1B/AV1R/AV1T-O1M-*`, `AV1T-definition-ALL10`,
`AV1T-statistics-ALL10`.

| symbol (ohlcv-1m) | files | rows | ts_event window (UTC) |
|---|---|---|---|
| ES | 13 | 8,710,520 | 2010-06-06T22:00 → 2026-09-30T23:59 |
| NQ | 13 | 7,330,320 | 2010-06-06T22:00 → 2026-09-30T23:59 |
| 6E | 5 | 3,436,733 | 2020-01-01T23:00 → 2026-09-30T23:59 |
| 6B | 5 | 2,738,672 | 2020-01-01T23:00 → 2026-09-30T23:58 |
| 6A | 5 | 2,876,268 | 2020-01-01T23:00 → 2026-09-30T23:59 |
| 6J | 5 | 3,120,241 | 2020-01-01T23:00 → 2026-09-30T23:59 |
| CL / NG / GC / SI | 0 | 0 | **NO ohlcv-1m files on disk** (ALL10 definition/statistics only) |

ALL10 shared schemas: `definition` 12 files, 12,157,041 rows, 2023-10-01T11:03
→ 2026-09-30T13:20; `statistics` 18 files, 69,065,041 rows, 2023-10-01T11:03
→ 2026-09-30T23:59:58.

Caveats: (a) windows are min/max of row-group statistics per file — they
evidence footer-level coverage, not row-level continuity (row-level gap scan
out of scope for a light re-measure); (b) ts_event convention per D5: ns
epoch stamped at bar-interval START in exchange time America/Chicago — the
UTC rendering above therefore shifts with DST (e.g. 22:00 UTC == 17:00 CT
open under CDT); (c) group naming carries campaign provenance
(BACKFILL2 2020–2022, BACKFILL 2022–2026Q1, DELTA 2010-06→2023-10,
AV1T 2023-10→2026-10); boundary duplicate checks across groups remain
NOT_RUN (D5 §7), unchanged.

## 4. Verdict

- IBKR raw: staleness 0.82–0.89 days at the 2026-10-03 reference — as
  expected one day after the serial bulk; the weekly D6 cadence is the
  governing control (owner item 4 in DATACONTRACT_QUALIFICATION §3).
- Vendor: O1M windows unchanged in shape from the qualification dossier
  (ES/NQ 2010-06→, FX4 2020-01→, both through 2026-09-30); CL/NG/GC/SI have
  no owned price schema; no BBO/MBP/MBO anywhere (ties dimension 2).
