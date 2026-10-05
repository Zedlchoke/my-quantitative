# COVERAGE_AUDIT — B_BUILD · NFL-PLAYERFEAT-PREP-V1 · 2026-10-05

All numbers re-measured from bytes by `build_features.py` (manifest `FEATURE_TABLE_MANIFEST.json`
is the machine authority). Interpreter: `.venv/bin/python` only.

## 1. Universe

- games.csv 2024–2026: 842 games (285 + 285 + 272). Unique stats game_ids on disk: 633;
  0 orphan stats game_ids vs games.csv → **row universe = 633 games × 2 sides = 1,266 rows**.
- 2026: 63 played games in stats (weeks 1–4) → 126 rows; **209 future 2026 games → no rows
  by design** (no stats; earliest future kickoff re-measured 2026-10-06T00:15:00Z).
- Duplicate (game_id, side): 0. Scores/outcome fields of games.csv never read into the table
  (only keys, gameday, gametime, week, game_type, teams).

## 2. Per-season coverage

| season | rows | G1/G2 with ≥1 prior | no-prior (openers) | G3 computable | G3 no-snap | G3 pfr-null flag | trunc k3 | trunc k5 |
|---|---|---|---|---|---|---|---|---|
| 2024 | 570 | 538 (94.4%) | 32 | 0 | 570 | 0 | 64 | 128 |
| 2025 | 570 | 538 (94.4%) | 32 | 538 | 32 | 74 | 64 | 128 |
| 2026 | 126 | 94 (74.6%) | 32 | 94 | 32 | 8 | 64 | 94 |
| total | 1,266 | 1,170 | 96 | 632 | 634 | 82 | 192 | 350 |

- Season openers (week 1, 32 team-rows/season) are structurally no-prior under the
  same-season as-of law → G1/G2 NaN + `flag_no_prior_in_corpus` (neutral rule, spec §7).
- 2024 has no snap_counts corpus on disk (2025+ only) → **G3 is NaN for all 2024 rows**
  (`flag_g3_no_snap_prior`), disclosed, not imputed.
- `flag_g2_zero_usage` = 0 rows (no zero-usage team windows observed in 2024–26).
- `flag_g3_pfr_null_excluded` = 82 rows (74 in 2025, 8 in 2026): ≥1 pfr-null/unresolved snap
  row sat inside the team's G3 window and was excluded from the candidate pool per the
  frozen rule (spec §6).

## 3. Window disclosure (first computable game-dates, measured)

| group | requirement | first kickoff_utc |
|---|---|---|
| G1 QB form / G2 usage | ≥1 same-season prior game | 2024-09-13T00:15:00Z |
| G1 k5 window full | ≥5 priors | 2024-10-11T00:15:00Z |
| G3 absence proxy | ≥1 snap-prior game | 2025-09-12T00:15:00Z |
| G3 k3 window full | ≥3 snap-priors | 2025-09-26T00:15:00Z |

Reading: prior-game windows for G1/G2 are fully computable from the 2024 season onward
(week-2 teams onward; k5 fills in by week 6). G3 only exists where snap_counts exists
(2025–2026); its own season openers are no-prior. This is exactly the inherited release-
cadence caveat (release-level availability, frozen sha256s as evidence anchors) — no
row-level inference was made to fill it.

## 4. Crosswalk join rates (re-measured with this lane's own code)

| join | season | rate | detail |
|---|---|---|---|
| stats player_id → crosswalk gsis_id | 2024 | 2001/2001 = 1.0 | placeholder row excluded first |
| 〃 | 2025 | 2024/2024 = 1.0 | |
| 〃 | 2026 | 1512/1512 = 1.0 | |
| snap pfr_player_id → crosswalk pfr_id | 2025 | 2183/2189 = 0.997259 | unresolved: AndeAl01, CartNa00, HallGa01, JohnIs03, OkoyCJ00, WhitCo05 |
| 〃 | 2026 | 1676/1679 = 0.998213 | unresolved: AndeAl01, OkoyCJ00, WhitCo05 |

Censuses match predecessor D_VERIFY exactly (0.9972590 / 0.9982132 and the same id lists).
WhitCo05 (Cody White, gsis 00-0035891, crosswalk pfr_id NULL) is the frozen canary (S4).

## 5. Value-range sanity (non-null rows)

| column | n | min | max | note |
|---|---|---|---|---|
| qb_ypa_k3 | 1,170 | 3.207 | 12.960 | plausible |
| qb_epa_pa_k3 | 1,170 | −0.756 | 0.827 | plausible |
| skill_top3_share_k3 | 1,170 | 0.420 | 0.913 | ∈ (0,1] |
| skill_hhi_k3 | 1,170 | 0.103 | 0.431 | ≥ 1/n_players floor |
| skill_top5_share_k5 | 1,170 | 0.597 | 1.000 | ∈ (0,1] |
| g3_top5_absent_share_recent | 632 | 0.0 | 0.6 | ≤1 |
| g3_top5_newly_absent_count | 632 | 0 | 5 | ≤ top-N |
| rest_days | 1,170 | 3.854 | 15.375 | short-week floor to post-bye ceiling |

All ranges sane; no negative shares, no >1 shares, no negative rest_days.

## 6. Boundary compliance

- Writes: `lanes/B_BUILD/**` + `~/.my-quantitative-data/nfl-playerfeat-prep-v1/**` only.
  Predecessor data dirs read-only. No git commands run. No writes to NFL-WINPROB-NG-SCORED-V1
  or any other cycle's worktree/artifacts.
- 0 scored computation; 0 outcome columns (S8 banned-vocabulary scan); no betting vocabulary.
