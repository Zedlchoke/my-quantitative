# INVENTORY — Lane B (WNBA PLAYER DATA) · cycle WINPROB-PLAYERDATA-PREP-V1 · 2026-10-05

- Corpus: `~/.my-quantitative-data/wnba-prep-v1/roster_audit/` — **READ-ONLY** (EXTEND-ONLY law).
  Pre-existing from cycle WNBA-WINPROB-PREP-V1 (lane A, pulled 2026-10-05T06:57–07:04Z from the
  public release store `sportsdataverse/sportsdataverse-data`, tags `espn_wnba_player_boxscores`
  and `espn_wnba_game_rosters`, no auth, $0). **This session downloaded nothing** (0 new files,
  $0 spent) — per dispatch, the corpus was verified by re-hash instead.
- Measurement: script `lanes/B_WNBA/measure_b.py` (re-runnable, read-only), machine output
  `lanes/B_WNBA/measurements_b.json`. Schema/coverage counting only — no scored computation.

## 1. File list and integrity (re-hashed EVERY file this session)

Command: sha256 over every `player_box_2002..2026.csv` and `game_rosters_2002..2026.csv`,
compared against `sha256_local` recorded in the prior cycle's
`~/.my-quantitative-data/wnba-prep-v1/roster_audit/download_manifest_r2.json`
(manifest covers all 50 files; per-file pull URLs and GitHub asset digests recorded there).

**Result: 50 / 50 files hash-match. 0 mismatches, 0 size mismatches, 0 missing files.
Total on-disk: 86,572,091 bytes (~86.6 MB).**

| class | count | note |
|---|---:|---|
| already on disk, sha256 re-verified this session | 50 | all 25 seasons × both families |
| downloaded this session | 0 | corpus pre-existing; hash verification only |
| of which GitHub-digest-verified (prior cycle, vs api.github.com `digest`) | 48 | status `already_present_digest_match` |
| of which no GitHub digest existed (local sha256 only) | 2 | `player_box_2002.csv`, `game_rosters_2002.csv` — 2023-era assets predate the digest field |

## 2. Per-season row counts and bytes (measured from bytes on disk)

| season | player_box rows | player_box bytes | rosters rows | rosters bytes |
|---|---:|---:|---:|---:|
| 2002 | 344 | 71,853 | 5,959 | 976,386 |
| 2003 | 4,279 | 1,715,124 | 5,605 | 932,946 |
| 2004 | 4,694 | 1,930,915 | 5,194 | 868,245 |
| 2005 | 5,079 | 2,081,047 | 5,288 | 883,748 |
| 2006 | 6,076 | 2,483,443 | 6,076 | 1,015,909 |
| 2007 | 5,919 | 2,414,344 | 5,969 | 997,383 |
| 2008 | 6,245 | 2,561,178 | 6,400 | 1,078,548 |
| 2009 | 5,348 | 2,224,445 | 5,348 | 918,719 |
| 2010 | 4,831 | 2,009,365 | 4,854 | 838,192 |
| 2011 | 4,953 | 2,072,581 | 4,953 | 872,012 |
| 2012 | 4,889 | 2,069,258 | 4,934 | 891,902 |
| 2013 | 4,961 | 2,181,243 | 4,961 | 982,809 |
| 2014 | 5,228 | 2,297,246 | 5,228 | 1,051,084 |
| 2015 | 5,379 | 2,389,377 | 5,379 | 1,109,360 |
| 2016 | 5,176 | 2,364,853 | 5,199 | 1,097,273 |
| 2017 | 5,183 | 2,405,507 | 5,183 | 1,129,408 |
| 2018 | 5,187 | 2,485,228 | 5,211 | 1,180,832 |
| 2019 | 5,211 | 2,519,132 | 5,211 | 1,207,803 |
| 2020 | 3,544 | 1,736,549 | 3,544 | 847,872 |
| 2021 | 4,626 | 2,303,478 | 4,626 | 1,142,838 |
| 2022 | 5,307 | 2,625,450 | 5,307 | 1,292,551 |
| 2023 | 5,796 | 2,816,138 | 5,796 | 1,457,707 |
| 2024 | 5,929 | 2,947,793 | 5,929 | 1,501,074 |
| 2025 | 7,140 | 3,559,371 | 7,140 | 1,811,300 |
| 2026 | 8,293 | 4,144,369 | 8,293 | 2,076,903 |
| **total** | **129,617** | **58,203,833** | **137,587** | **28,368,258** |

Header observations: 2025–2026 rows jump with league expansion (13 teams 2025, 15 franchise-keys
in ESPN schedules 2026 incl. TOR/PDX); 2020 is the COVID "Wubble" short season (147 games).
`player_box_2002.csv` is a **stub**: 344 rows covering 16 games (details in COVERAGE_SCHEMA.md).

## 3. "Source publishes but not downloaded" (kept NOT-downloaded, per etiquette/$0 budget)

From the prior cycle's archived release census
(`~/.my-quantitative-data/wnba-prep-v1/release_depth_census.json`, GitHub API, 2026-10-05):

| release tag | seasons | size | status |
|---|---|---:|---|
| `espn_wnba_player_boxscores` | 2002–2026 | 64.3 MB all formats | **on disk** (csv only, this corpus) |
| `espn_wnba_game_rosters` | 2002–2026 | 30.4 MB all formats | **on disk** (csv only, this corpus) |
| `espn_wnba_pbp` | 2002–2026 | 1,065.7 MB | deliberately NOT downloaded (kept not-downloaded) |
| `wnba_stats_pbp` | 1997–2026 | 213.9 MB | deliberately NOT downloaded |
| `espn_wnba_shots` | 2002–2026 | 147.4 MB | deliberately NOT downloaded |
| `wnba_stats_lineups` | 2026 only | 19.5 MB | NOT downloaded |
| `wnba_stats_team_boxscores` | 2026 only | 0.1 MB | NOT downloaded |
| `espn_wnba_team_boxscores` | 2003–2026 | 6.4 MB | sample only (`team_box_2013.csv` in `extensions/`) |
| `wnba_crosswalk` | 2026 only | 0.1 MB | downloaded (3 csv in `extensions/`) |

**Era coverage of the store itself:** no player-level release covers 1997–2001 —
`espn_wnba_player_boxscores` and `espn_wnba_game_rosters` both start at 2002. The only
pre-2002 player-adjacent asset is `wnba_stats_pbp` (PBP, not player box). The 1997–2001
era gap is a property of the source store, not of our downloads.

## 4. Parquet/RDS duplicates

The store also publishes `.parquet` and `.rds` renderings of each season; only the `.csv`
rendering is on disk (by design of the prior cycle). Parquet/rds are byte-different
renderings of the same release assets, not new information.
