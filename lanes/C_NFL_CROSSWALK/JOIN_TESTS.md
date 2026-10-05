# JOIN TESTS — Lane C_NFL_CROSSWALK · WINPROB-PLAYERFEAT-PREP-V1

All rates measured from bytes 2026-10-05; raw evidence `logs/join_tests_raw.json`.
Inputs: predecessor weekly stats + snap_counts (sha-verified at lane start, see
DOWNLOAD_MANIFEST.md) × `players.parquet` (sha `485b1980…304885e2`, build 2026-10-04T15:06:29Z).
No scored computation; join/coverage only.

## 1. Weekly stats (`player_id` GSIS ↔ `players.gsis_id`)

| season | file rows | null-player_id rows | distinct GSIS | matched | **match rate** | unmatched ids | unmatched rows | dup (player_id,game_id) |
|---|---|---|---|---|---|---|---|---|
| 2024 | 18,983 | 22 | 2,001 | 2,001 | **1.000000 (100.00%)** | 0 | 0 | 0 |
| 2025 | 19,422 | 22 | 2,024 | 2,024 | **1.000000 (100.00%)** | 0 | 0 | 0 |
| 2026 | 4,379 | 4 | 1,512 | 1,512 | **1.000000 (100.00%)** | 0 | 0 | 0 |

Unmatched census: **empty in all three seasons.** The null-player_id rows are the known
1-per-week all-zero placeholder artifact (22/22/4, matches predecessor COVERAGE_SCHEMA §2
exactly). Duplicate-key check: 0 in every file. **The crosswalk covers 100% of GSIS ids
observed in weekly stats 2024–2026.**

## 2. snap_counts (`pfr_player_id` ↔ `players.pfr_id`)

| season | file rows | null-pfr rows | distinct PFR | matched | **match rate** | unmatched ids | unmatched rows | dup (pfr_player_id,game_id) |
|---|---|---|---|---|---|---|---|---|
| 2025 | 26,613 | 0 | 2,189 | 2,183 | **0.997259 (99.73%)** | 6 | 54 | 0 |
| 2026 | 4,579 | 0 | 1,679 | 1,676 | **0.998213 (99.82%)** | 3 | 8 | 0 |

Unmatched census (deep-roster fringe; all statuses/snap counts low):

| pfr_id | player | pos | teams (file) | rows 2025/2026 | crosswalk state |
|---|---|---|---|---|---|
| AndeAl01 | Alec Anderson | T/C | BUF | 19 / 3 | in crosswalk, `pfr_id` **NULL** (gsis 00-0037428, ACT) |
| CartNa00 | Nathan Carter | RB | ATL | 7 / – | no crosswalk pfr_id |
| HallGa01 | Gabe Hall | DT | PHI | 2 / – | no crosswalk pfr_id |
| JohnIs03 | Isaiah Johnson | CB | MIA | 4 / – | no crosswalk pfr_id |
| OkoyCJ00 | Basil (CJ) Okoye | DT/DL | BAL→NYG | 12 / 2 | no crosswalk row under that pfr_id (name "Basil Okoye" also pfr-null) |
| WhitCo05 | Cody White | WR | SEA→LV | 10 / 3 | 2026-ACT Cody White row has `pfr_id` NULL (gsis 00-0035891); other Cody White = WhitCo02 (different person) |

The same 3 ids unmatched in 2026 were already unmatched in 2025 — **deterministic
crosswalk-side pfr gaps on a fringe cohort**, not season-specific corruption. Max impact:
8 of 4,579 snap rows (0.17%) in 2026.

## 3. Round-trip: 2026 weekly-stats players reachable into snap_counts_2026

Path: stats `player_id` (GSIS) → crosswalk `pfr_id` → membership in snap_counts_2026 PFR set.

| quantity | value |
|---|---|
| distinct GSIS in stats_player_week_2026 | 1,512 |
| …with a crosswalk `pfr_id` | 1,508 (99.74%) |
| …with crosswalk `pfr_id` NULL | 4 (Cody White, Alec Anderson, Basil Okoye, Peter Woods — all ACT, last_season 2026) |
| …crosswalk `pfr_id` present in snap_counts_2026 | 1,475 |
| **round-trip rate vs all stats-2026 players** | **0.975529 (97.55%)** |
| round-trip rate vs pfr-holders only | 0.978117 (97.81%) |

The 33 pfr-holders not in snap_counts_2026 are consistent with the documented snap-file
lag (snap build 2026-10-02 covers 49/63 games at predecessor pull; week-4 games missing) —
they are ACT-status players across ordinary positions (WR 7, CB 4, DT/DE/RB/LB 3 each…),
not an id-system failure. This share should rise when snap_counts_2026 catches up.

**Verdict: the player-level stats+snaps join IS constructible today for ~97.6% of 2026
weekly-stats players (99.7–100% per-direction), with a named, tiny, stable residual
(pfr-null fringe cohort).**
