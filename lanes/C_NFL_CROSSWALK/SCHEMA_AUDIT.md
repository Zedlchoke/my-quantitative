# SCHEMA AUDIT — `players.parquet` · Lane C_NFL_CROSSWALK · WINPROB-PLAYERFEAT-PREP-V1

Measured from bytes 2026-10-05 (Python 3.12.14 / pandas 3.0.5 / pyarrow 25.0.1).
File: `~/.my-quantitative-data/playerfeat-prep-v1/nfl/raw_players/players.parquet`
sha256 `485b198070f831ed3a9098b991cd4b5dd97407e23a08fe31629d18dc304885e2`,
release build 2026-10-04T15:06:29Z. Raw evidence: `logs/schema_audit_raw.json`.

## 1. Shape

**24,844 rows × 39 columns.** Player universe file (all players, not roster snapshot).

## 2. Columns (verified from bytes)

Identity / crosswalk: `gsis_id`, `esb_id`, `nfl_id`, `pfr_id`, `pff_id`, `otc_id`,
`espn_id`, `smart_id` (8 id systems).
Name fields: `display_name`, `common_first_name`, `first_name`, `last_name`, `short_name`,
`football_name`, `suffix`.
Meta: `birth_date`, `position_group`, `position`, `ngs_position_group`, `ngs_position`,
`height`, `weight`, `headshot`, `college_name`, `college_conference`, `jersey_number`,
`rookie_season`, `last_season`, `latest_team`, `status`, `ngs_status`,
`ngs_status_short_description`, `years_of_experience`, `pff_position`, `pff_status`,
`draft_year`, `draft_round`, `draft_pick`, `draft_team`.

Dispatch expectation met: gsis_id ✓, pfr_id ✓, name/first/last ✓, position ✓,
team (`latest_team`) ✓, status ✓. Note: team column is named **`latest_team`**, not `team`.

## 3. Key columns (null rates, uniqueness)

| column | non-null | null | null rate | unique (non-null) |
|---|---|---|---|---|
| `gsis_id` | 24,844 | 0 | 0.000000 | 24,844 (**primary key, no dups**) |
| `pfr_id` | 22,679 | 2,165 | 0.087144 | 22,679 (unique) |
| `nfl_id` | 11,914 | 12,930 | 0.520448 | 11,914 |
| `espn_id` | 16,578 | 8,266 | 0.332716 | 16,578 |
| `display_name` | 24,844 | 0 | 0.000000 | 23,803 (name collisions exist) |

**The 2,165 pfr-nulls are the only crosswalk gap.** They are spread across all rookie
classes (2017: 21, 2018: 26, … 2025: 13, 2026: 11) — NOT a current-season refresh lag;
only 27 have `last_season == 2026`. 2026 rookie class pfr coverage: 477/488 = 97.75%.

## 4. Status distribution

ACT 13,928 · RES 3,476 · CUT 3,444 · DEV 3,380 · RSN 161 · PUP 148 · NWT 120 · RSR 100 ·
SUS 41 · RET 33 · EXE 9 · INA 3 · RLS 1. (13 statuses; ACT includes prior-year ACT players
still tagged — see §6 for the current-season roster proxy.)

## 5. Position distribution (25 distinct)

WR 3,252 · LB 2,612 · RB 2,453 · DB 2,313 · DE 1,754 · OT 1,695 · TE 1,586 · G 1,581 ·
DT 1,482 · CB 1,206 · QB 1,008 · C 787 · OLB 471 · K 378 · P 350 · SAF 328 · S 325 ·
FS 283 · NT 247 · FB 210 · ILB 201 · MLB 153 · LS 122 · OL 30 · DL 17.
Mixed granularity (generic DB/LB/OL/DL plus specific S/CB/ILB etc.) — position-specific
filters should prefer `position_group`/`ngs_position` and test both.

## 6. Team domain

`latest_team` — **0 nulls, exactly 32 distinct values**, all 32 NFL franchises:
ARI ATL BAL BUF CAR CHI CIN CLE DAL DEN DET GB HOU IND JAX KC LA LAC LV MIA MIN NE NO
NYG NYJ PHI PIT SEA SF TB TEN WAS. All-team share range 531–978 (all statuses).
Current-season roster proxy (`status == "ACT"` AND `last_season == 2026`): **1,731
players across all 32 teams, 52–55 per team** — consistent with 53-man rosters.

## 7. Cross-season applicability

`rookie_season` spans 53 distinct values; `last_season` 2026 count = 2,586 players — the
file is forward-maintained for the current season (see FRESHNESS_2026.md).
