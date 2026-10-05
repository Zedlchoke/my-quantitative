# FEATURE TABLE MANIFEST — NBA player features 2016–2026 (Lane A_NBA_FEAT, WINPROB-PLAYERFEAT-PREP-V1)

Built 2026-10-05 by `build_features.py` (deterministic; run metadata only here,
no timestamps inside the data files). Frozen definitions: `FEATURE_SPEC.md`.
Machine-readable twin: `FEATURE_TABLE_MANIFEST.json` (this directory) and
`~/.my-quantitative-data/playerfeat-prep-v1/nba/features/build_manifest.json`.

## Outputs

| file | sha256 | bytes |
|---|---|---|
| `~/.my-quantitative-data/playerfeat-prep-v1/nba/features/nba_player_features_2016_2026.parquet` | `b3ca0e3b2eff1d1c918d56fb626e06998903c0f69253b41b67166dc8859885cb` | 1,108,480 |
| `~/.my-quantitative-data/playerfeat-prep-v1/nba/features/nba_player_features_2016_2026.csv.gz` | `9368ad76e12efd4e3df2ca270427763d3a436dbe645edac6da94af361ce458ab` | 1,054,566 |

- Rows: **28,374** = 2 × 14,187 played games (one home-side + one away-side row
  each). Columns: 18, frozen order in FEATURE_SPEC §7. **No outcome columns**
  (whitelist-asserted: no score/winner/margin/result anywhere).
- `asof_rule_version` = `asof_v1_strict_tip_utc` on every row.
- csv.gz written with gzip mtime=0 → byte-stable for the same table content.

## Row counts per season

| season | rows | neutral rows | season | rows | neutral rows |
|---|---|---|---|---|---|
| 2016 | 2,634 | 152 | 2022 | 2,648 | 152 |
| 2017 | 2,620 | 152 | 2023 | 2,642 | 152 |
| 2018 | 2,628 | 154 | 2024 | 2,640 | 152 |
| 2019 | 2,628 | 154 | 2025 | 2,648 | 156 |
| 2020 | 2,290 | 154 | 2026 | 2,652 | 158 |
| 2021 | 2,344 | 152 | **Σ** | **28,374** | **1,688** |

Neutral = `feature_neutral=1` (n_prior_games_used < 5 or top-3 set empty):
all group scalars 0.0 on those rows (asserted both directions).

## Missing-data rule outcomes (measured on the built table)

- Neutral rows: 1,688 (5.95%) — season openers + first 4 team-games of every
  team + 19-game exhibition entities + the 6 rows of the 3 box-less played
  games' own sides (their later games unaffected).
- Identity-less rows: 33 (all 2026) excluded from all aggregates (counts in
  COVERAGE_AUDIT §1).
- `season_type=5` (play-in) rows: 0 enter any prior window (law), play-in
  targets present as rows (their box rows, where populated, are only committed
  after their own emission — and play-in games are never committed at all).
- Trade guard (`provenance/` + PIT_AUDIT §4): measured real case — Patty Mills
  2025 UTAH(26)→LAC(12): last UTAH appearance 2025-01-28 (game 401705227); the
  store carries ONE stale UTAH DNP scaffold row for him thereafter
  (game 401705243, "COACH'S DECISION") — he was NOT in UTAH's top-3 minute-mass
  at the affected targets (260 season-to-date minutes vs ≥1,112 for the actual
  top-3), so no absence was fabricated; the trailing-10 guard bounds any such
  exposure to ≤10 team-games (synthetic logic tests in `--selftest`).

## Frozen scalar distributions (non-neutral rows, n=26,686)

| scalar | mean | std | p5 | p95 |
|---|---|---|---|---|
| `a_top5_share_k5` | 0.6589 | 0.0401 | 0.595 | 0.726 |
| `a_load_top5_k5` | 0.0037 | 0.0281 | −0.0416 | 0.0503 |
| `b_form_top3` | 0.0008 | 0.0486 | −0.078 | 0.081 |

`c_abs_out` rate 0.1077; `c_abs_streak` distribution: 0→26,136, 1→417, 2→77,
3→29, 4→10, 5→7, 6..10→2 each (long-injury tail). All three frozen scalars
carry real variation — the degenerate raw minutes-mass level was substituted
per the measured law (FEATURE_SPEC §3).

## Input sha256 (all verified at build time; equals download manifests)

player_box (11): 2016 `ffd09dec…`, 2017 `45d6fe8b…`, 2018 `c963c9ac…`,
2019 `5df73407…`, 2020 `f822c3cf…`, 2021 `86b12342…`, 2022 `1a639a8c…`,
2023 `1b797107…`, 2024 `c52a708a…`, 2025 `8e34c5b1…`, 2026 `7a4868da…`
(full 64-hex values in `FEATURE_TABLE_MANIFEST.json` → `inputs_sha256`;
box hashes equal `~/.my-quantitative-data/playerdata-prep-v1/nba/download_manifest.json`
and `~/.my-quantitative-data/playerfeat-prep-v1/nba/download_manifest.json`).
nba_schedule (11): 2016 `3373fb4a…`, 2017 `d17829cb…`, 2018 `ce772be7…`,
2019 `b99913f6…`, 2020 `af35fed1…`, 2021 `1857bb44…`, 2022 `8cd13a11…`,
2023 `71aad62f…`, 2024 `ae89a6e5…`, 2025 `a7a5b660…`, 2026 `5a4a7473…`.

## Selftest

`build_features.py --selftest` → 42/42 PASS (exit 0); checks cover: frozen
columns + no outcome columns, 0 duplicate (game_id, team_id), row count
= 2× played, neutral rule both directions, strict tip inequality + target
absent from inputs on 8 sample team-rows across 2016/2021/2026, independent
recomputation match on all scalars for those rows, predecessor MIL worked
example reproduction (prior-5 ids + mean mass 239.4 + tip 2021-03-15T23:00Z),
synthetic trade-guard logic (counting, expiry at >10, streak walk), global
streak ≤ team_games_so_far, exhibition disclosure law. Log:
`~/.my-quantitative-data/playerfeat-prep-v1/nba/provenance/selftest_checks.txt`.
