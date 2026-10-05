# ERRATUM — PBP GAP + MANIFEST HYGIENE, R1 — Lane A_DATA, NBA-WINPROB-NG-PREP-V1

Cycle NBA-WINPROB-NG-PREP-V1 · lane A_DATA · task `nbang-a-data-r1` · role
quant-implementer · 2026-10-05 (UTC). Owner order 2026-10-05: fix verifier
defect D1 everywhere it appears (plus same-erratum-scope hygiene D3/D4/D5).
The verifier never repairs; lane A fixes its own artifact from data. NO
COMMITS (controller lands). Schema/coverage counting only — no win-prob
metric was computed on real outcomes.

## 1. What was wrong (verifier quotes)

Source: `lanes/D_VERIFY/VERIFICATION_REPORT.md` (READ-ONLY evidence; verdict
VERIFICATION_PASS with defects).

- **D1 (MEDIUM)** — check #16 **FAIL**: "Spec §5 / handoff_A / dispatch claim
  **4** played games lack pbp (2016×3 + 2026×1, 'All other seasons: 0').
  Re-measured from the 11 parquets: **14** played games lack pbp — 2016×3
  (`400828893`, `400828600`, `400828393`), **2018×4** (`400974444`,
  `400974773`, `400975617`, `400975670`), **2020×6** (`401161490`,
  `401161505`, `401161528`, `401161530`, `401161533`, `401161536`), 2026×1
  (`401810469`). Absence verified under int32/str/float interpretations of
  pbp `game_id` (column int32, 0 nulls); all [newly found] are real completed
  RS games with final scores … No data corruption — a data-contract
  understatement."
- **D3 (LOW)** — `DOWNLOAD_MANIFEST.md`: "Total new bytes stated
  **268,642,536 (~256 MiB)**; the sum of its own 10 per-file sizes is
  **248,642,536 (~237 MiB)** (off by exactly 20,000,000). Per-file sizes and
  all 10 sha256s are correct (re-hashed)."
- **D4 (LOW)** — "Session BDL request total: manifest says **26**, cross-check
  doc says **36 (16+9+11)**. The 36 breakdown is internally consistent with
  the documented run history and adopted as correct."
- **D5 (LOW)** — spec §5: "Exhibition-pbp enumeration lists only 2016:1,
  2021:1, 2022:1, 2025:3, 2026:4; measured **all 19 exhibitions have pbp**
  (also 2017:1, 2018:2, 2019:2, 2020:2, 2023:1, 2024:1)."

## 2. What was re-measured (independent, from parquet/CSV bytes)

Script (throwaway, /tmp, reads only): load each season's
`nba_schedule_{2016..2026}.csv` (`~/.my-quantitative-data/nba-hoopr-v1/raw/`),
keep `status_type_completed == "true"`, exclude `notes_headline` containing
`all-star`/`rising stars` (spec §4.2 law), then subtract the unique pbp
`game_id` set from `play_by_play_{season}.parquet` (2026 in-corpus; 2016–2025
under `~/.my-quantitative-data/nba-ng-prep-v1/pbp_2016_2025/`). Absence
checked under BOTH str and int64 keys of pbp `game_id` (dtype int32, 0 nulls
every season) — identical result either way.

Measured played counts per season reproduce spec §4 exactly (1,316 / 1,309 /
1,312 / 1,312 / 1,143 / 1,171 / 1,323 / 1,320 / 1,319 / 1,321 / 1,322; total
14,168) — measurement validated against a known-good census before reading
the gap.

**MEASURED GAP = 14 played games without pbp — matches verifier
`played_missing_pbp` game-for-game:**

| season | game_id | matchup (home–away) | date | final |
|---|---|---|---|---|
| 2016 | 400828893 | WSH–CHI | 2016-03-16 | 117–96 |
| 2016 | 400828600 | CLE–SA | 2016-01-30 | 117–103 |
| 2016 | 400828393 | NY–ATL | 2016-01-03 | 111–97 |
| 2018 | 400974444 | NO–GS | 2017-10-20 | 120–128 |
| 2018 | 400974773 | WSH–DET | 2017-10-20 | 115–111 |
| 2018 | 400975617 | SAC–OKC | 2018-02-22 | 107–110 |
| 2018 | 400975670 | SAC–BKN | 2018-03-01 | 116–111 |
| 2020 | 401161490 | POR–DET | 2020-02-24 | 107–104 |
| 2020 | 401161505 | GS–SAC | 2020-02-25 | 94–112 |
| 2020 | 401161528 | LAC–DEN | 2020-02-29 | 132–103 |
| 2020 | 401161533 | MEM–LAL | 2020-02-29 | 105–88 |
| 2020 | 401161530 | ATL–POR | 2020-03-01 | 129–117 |
| 2020 | 401161536 | PHX–GS | 2020-03-01 | 99–115 |
| 2026 | 401810469 | CHI–LAC | 2026-01-20 | 138–110 |

Seasons 2017/2019/2021/2022/2023/2024/2025: 0. All 14 rows are completed
regular-season games with final scores in the schedule CSV.

**D5 re-measurement**: exhibitions with pbp per season = 2016:1, 2017:1,
2018:2, 2019:2, 2020:2, 2021:1, 2022:1, 2023:1, 2024:1, 2025:3, 2026:4 —
**19/19**, all exhibitions carry pbp. Matches verifier.

**D3 re-measurement**: `os.path.getsize` over the 10 parquets
`play_by_play_2016..2025.parquet` = 248,642,536 bytes (~237.1 MiB),
identical to the sum of the manifest's own per-file sizes and to verifier
`pbp_total_bytes`. The prior "268,642,536" was +20,000,000 arithmetic error.

**D4 re-measurement (document-level)**: `BDL_CROSSCHECK_NBA.md` records runs
1–3 as 16 + 9 + 11 = **36** requests, grand-total line verbatim "36 BDL
requests (16 + 9 + 11), every one ≥13 s". Adopted as correct.

**Discrepancy check**: lane-A R1 measurement agrees with the verifier on all
four defects — no conflict, no STOP condition triggered.

## 3. What changed, in which files (all edits surgical, ERRATUM-pointed)

1. `lanes/A_DATA/GAME_UNIVERSE_SPEC_NBA_2016PLUS.md` §5 — played-games-
   without-pbp bullet replaced: 4-game list + "All other seasons: 0" →
   measured 14-game list with season breakdown (D1); exhibition-pbp bullet
   corrected to all 19/19 seasons (D5). Both bullets carry ERRATUM R1 / D1/D5
   pointers to this file. §6 census table untouched (its per-season unique
   pbp-game counts were already correct and imply the gap).
2. `lanes/A_DATA/PIT_AUDIT_NBA.md` §3 — "4 played games without pbp,
   2016×3 + 2026×1" → "14 played games without pbp … 2016×3, 2018×4, 2020×6,
   2026×1" with ERRATUM pointer; tolerance law (never silently impute) restated.
3. `lanes/A_DATA/handoff_A.json` — known_limitations gap entry corrected to
   the 14-game statement with full game-id list (D1); exhibition-pbp entry
   corrected to 19/19 (D5); one R1-correction note appended (prior entries
   kept). No other field altered; schema `zcode_orch_v3_handoff@1` preserved.
4. `lanes/A_DATA/DOWNLOAD_MANIFEST.md` — total bytes 268,642,536 →
   248,642,536 (~237 MiB) with D3 note; session BDL request total 26 → 36
   (16+9+11) with D4 note.
5. NEW `lanes/A_DATA/ERRATUM_PBP_GAP_R1.md` (this file).
6. NEW `lanes/A_DATA/handoff_A_r1.json` — remediation handoff, schema
   `zcode_orch_v3_handoff@1`, task `nbang-a-data-r1`.

## 4. Impact statement

- The 14-game hole affects **pbp-derived features on those 14 games only**:
  any prior-state aggregate that would consume those games must tolerate
  their absence (smaller initial windows), never impute silently. Feature
  code keys tolerance by the explicit game-id list in spec §5.
- **Spread features from schedules are unaffected on the feature side as
  claimed**: the §6 spread census is schedule/pbp-attached coverage measured
  on unique pbp `game_id` and stays 100% non-null per season — but those 14
  games carry NO spread value in the pbp release (they have no pbp rows), so
  any consumer joining spread by game-id must expect null on exactly these
  14 ids. No census number in §6 changes.
- **No selection law changes**: the game universe (14,254 raw = 14,168
  played + 19 exhibitions + 67 postponed) re-verified intact; the gap is a
  coverage property of the pbp release, not a universe defect.
- **No game-universe law changes**: §4 dedupe/exclusion law untouched.
- **No BDL result changes**: the 22/22 MATCH cross-check and its 36-request
  run history were correct; only the manifest's summary line was wrong.
- The error was self-refuting inside the spec (its own §6 census contradicted
  §5), so no load-bearing law was derived from the wrong number (verifier's
  D1 corrective note, concurred).

## 5. Authority / scope

- Written under owner order 2026-10-05 for task `nbang-a-data-r1`; write
  scope `lanes/A_DATA/**` only; `lanes/D_VERIFY/**` consumed read-only.
- No commits — controller lands. Worktree HEAD at edit time:
  `4d387a2a4ec71636be3602269efda0f7ea87a4fb`.
- Data attribution unchanged: hoopR/sportsdataverse, CC BY 4.0 / MIT,
  upstream ESPN NBA API (see ATTRIBUTION.md law in spec header).
