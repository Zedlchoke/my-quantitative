# FEATURE_TABLE_MANIFEST — B_BUILD · NFL-PLAYERFEAT-PREP-V1 · 2026-10-05

Machine authority: `FEATURE_TABLE_MANIFEST.json` (this dir; canonical copy beside the
parquet). Builder: `build_features.py` (single command, `--selftest` runs the 8 leak/fixture
checks). All inputs re-hashed at build start; mismatch would abort BLOCKED_DATA (none).

## Output

| item | value |
|---|---|
| parquet | `~/.my-quantitative-data/nfl-playerfeat-prep-v1/features/nfl_playerfeat_table_v1.parquet` |
| sha256 | `f1bc6b4a8c7f5c36457aaa393666ca90cc446cc6f934c3ea55f739b5de7c4f57` (double-run byte-identical, incl. fresh-process rerun) |
| rows × cols | 1,266 × 44 |
| games | 633 (one row per (game_id, side): away + home) |
| schema | keys 7 + as-of 4 + G1 20 + G2 4 + G3 3 + flags 6 = 44 (whitelist, spec §9) |
| outcome columns | 0 (banned-vocabulary scan clean, S8) |
| as-of columns | `kickoff_utc`, `rest_days`, `n_prior_games_used`, `asof_rule_version` = `asof-1.0.0-nfl-playerfeat-prep-v1` |

## Input sha256 (verified 6/6 vs predecessor manifests)

| input | sha256 |
|---|---|
| stats_player_week_2024.parquet | `847569d194ca3d96b5efcf91e6eac5e18780fc47568a713fd545a82d29d155c1` |
| stats_player_week_2025.parquet | `2a461becaa9adb3c93a3074a3a31f1e960162a50163371a2d34e28393b5fff10` |
| stats_player_week_2026.parquet | `49bc644ed4bf10546b399ce177045f09ef278a562fc894074311c8afa6b26179` |
| snap_counts_2025.parquet | `47220218fecda7af7ee5b0272a8ecce7c1bfb1f4e1f0a2c8c90047571728ce20` |
| snap_counts_2026.parquet | `fae0627d81f4ffa1802263ac0fad1a29f5c1986d5749a711bde7c50651498273` |
| players.parquet (crosswalk) | `485b198070f831ed3a9098b991cd4b5dd97407e23a08fe31629d18dc304885e2` |

games.csv (`nfl-ng-prep-v1/raw_schedules_r1_20261005/`) read for kickoffs/keys (kickoff UTC
law: gameday+gametime America/New_York → UTC).

## Row counts / per-season coverage (re-measured)

| season | games | rows | G1/G2 with ≥1 prior | flag_no_prior | G3 computable | flag_g3_no_snap | flag_g3_pfr_null | trunc k3 / k5 |
|---|---|---|---|---|---|---|---|---|
| 2024 | 285 | 570 | 538 | 32 | 0 (no snap corpus) | 570 | 0 | 64 / 128 |
| 2025 | 285 | 570 | 538 | 32 | 538 | 32 | 74 | 64 / 128 |
| 2026 | 63 | 126 | 94 | 32 | 94 | 32 | 8 | 64 / 94 |
| total | 633 | 1,266 | 1,170 | 96 | 632 | 634 | 82 | 192 / 350 |

- 209 future 2026 games: no stats rows → **no table rows by design** (earliest future
  kickoff re-measured at build: **2026-10-06T00:15:00Z**; 63 played 2026 games are in).
- NaN-player placeholder rows excluded before aggregation: 48 (22+22+4 = 1/week, inherited
  predecessor law; S7).
- 0 duplicate (game_id, side); 0 orphan stats game_ids vs games.csv.

## Window disclosure (measured)

| first | kickoff_utc |
|---|---|
| G1/G2 computable (≥1 prior game) | 2024-09-13T00:15:00Z |
| G1 k5 window full (≥5 priors) | 2024-10-11T00:15:00Z |
| G3 computable (≥1 snap-prior) | 2025-09-12T00:15:00Z |
| G3 k3 window full (≥3 snap-priors) | 2025-09-26T00:15:00Z |

## Crosswalk join rates (re-measured by this lane's code)

| join | 2024 | 2025 | 2026 |
|---|---|---|---|
| stats player_id (GSIS) → crosswalk | 2001/2001 = 1.0 | 2024/2024 = 1.0 | 1512/1512 = 1.0 |
| snap pfr_player_id → crosswalk | n/a | 2183/2189 = 0.997259 | 1676/1679 = 0.998213 |

Unresolved snap cohort (pfr-null rule: EXCLUDE from G3 pool, flagged per row): 2025
{AndeAl01, CartNa00, HallGa01, JohnIs03, OkoyCJ00, WhitCo05}; 2026 {AndeAl01, OkoyCJ00,
WhitCo05}. WhitCo05 = Cody White (crosswalk gsis 00-0035891 has pfr_id NULL) — selftest
canary S4. Matches predecessor D_VERIFY censuses exactly.

## Missing-data rule outcomes (spec §7)

- `flag_no_prior_in_corpus` = 96 rows (season openers ×3 seasons): G1/G2 NaN, rest_days NaN.
- `flag_g3_no_snap_prior` = 634 rows: G3 NaN (all 2024 + season openers 2025/2026).
- `flag_g2_zero_usage` = 0 rows observed.
- NaN = not computable, never imputed 0 (documented G3 n_w=1 exception: absent share = 0.0
  by construction).

## Law restated

Target-game injury/active/DNP/starter status = **NOT_RUN_PIT** (no row, column, or field in
this table encodes target-game availability; G3 is a lagged prior-game snap proxy only).
