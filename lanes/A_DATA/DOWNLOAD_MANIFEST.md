# DOWNLOAD_MANIFEST — Lane A · DATA (nflng-a-data), cycle NFL-WINPROB-NG-PREP-V1

All downloads 2026-10-05, $0 only (anonymous HTTP GET to free public GitHub
release URLs / raw.githubusercontent / GitHub REST contents+releases API; no
accounts, no API keys, no purchases). All bytes under
`~/.my-quantitative-data/nfl-ng-prep-v1/` (outside git). The pre-existing
archive `~/.my-quantitative-data/nfl-nflverse-v1/` was NOT modified — its 9
files were only re-hashed (all values matched the recorded inventory).

Pull session times (UTC): license/docs 03:20:40Z; schedules+injuries 03:23:53Z
(release metadata API 03:23:32Z); teams 03:25:50Z (releases list API).

## A. New downloads (this cycle)

| # | local path (under nfl-ng-prep-v1/) | source URL | version / release tag | asset updated_at (GitHub) | bytes | sha256 | license note |
|---|---|---|---|---|---|---|---|
| 1 | rights/nflverse-data_LICENSE.md | https://raw.githubusercontent.com/nflverse/nflverse-data/main/LICENSE.md | repo main @ pull time | — | 18,651 | 2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111 | this IS the CC BY 4.0 license text |
| 2 | rights/nfldata_DATASETS.md | https://raw.githubusercontent.com/nflverse/nfldata/master/DATASETS.md | repo master @ pull time | — | 17,642 | 8835ca9c15784a2cdc04c2c599c54b373629f8fbe91117acd5b7d0c615e03bf4 | documentation only; nfldata repo has NO LICENSE → no data pulled from it |
| 3 | rights/nfldata_repo_root_api.json | https://api.github.com/repos/nflverse/nfldata/contents/ | REST contents API | — | 11,031 | 1b583e07aa856962842988ec093c94b179ee6b4dc3ec7b8fe45b97fd1a10dc7a | metadata: proves no LICENSE file at nfldata root |
| 4 | raw_schedules_20261005/games.csv | https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv | tag `schedules` | 2026-10-05T03:16:30Z | 2,182,476 | 338d7fe01d803916b2d5ed31fb4e5405914a8030ae2296ed449e27471d5b594f | CC BY 4.0 |
| 5 | raw_schedules_20261005/timestamp.json | https://github.com/nflverse/nflverse-data/releases/download/schedules/timestamp.json | tag `schedules` | 2026-10-05T03:16:31Z | 43 | fa921041b1d3c504c4fa4f44d2d14b9adbdc660b45b86289e30a013e7a4bd119 | content: {"last_updated":"2026-10-04 23:16:28 EDT"} |
| 6 | raw_schedules_20261005/release_api_schedules.json | https://api.github.com/repos/nflverse/nflverse-data/releases/tags/schedules | REST releases API | — | 14,817 | a18a6e6268cd78f1c8e47513f9453305aa068db0790a9e8f8b533fddf8e8d35c | release/asset metadata evidence |
| 7 | raw_injuries_20261005/injuries_2026.csv | https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_2026.csv | tag `injuries` | 2026-10-04T13:08:58Z | 120,160 | 5af782489dd0f9a7009663248ffa9be814a670eb194580ed5e7c10a63453466b | CC BY 4.0 (PIT verdict separate: NOT_RUN_PIT) |
| 8 | raw_injuries_20261005/injuries_2025.csv | https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_2025.csv | tag `injuries` | 2026-09-07T12:23:41Z | 696,006 | 873ca1606dd575bd01152508a243ef6b3a0f8f97b90b707217e62ee8c7ceb735 | CC BY 4.0 (NOT_RUN_PIT) |
| 9 | raw_injuries_20261005/timestamp.json | https://github.com/nflverse/nflverse-data/releases/download/injuries/timestamp.json | tag `injuries` | 2026-10-04T13:08:59Z | 43 | a55f0c129dc3b97d747eb8e48f2a823c1d23e41a61a66879401bc87ccf07214a | content: {"last_updated":"2026-10-04 09:08:56 EDT"} |
| 10 | raw_injuries_20261005/release_api_injuries.json | https://api.github.com/repos/nflverse/nflverse-data/releases/tags/injuries | REST releases API | — | 138,883 | 25e32c89eaa4beab9eb56969849dbc76d1b8a6e2d95c04291a75c6936924a1a1 | full asset inventory 2009–2026 |
| 11 | raw_teams_20261005/teams_colors_logos.csv | https://github.com/nflverse/nflverse-data/releases/download/teams/teams_colors_logos.csv | tag `teams` | (asset list; release ts content below) | 18,919 | 4eab559fcf89cb4eaf61cb63a88abc47b01b6c9049187c59f3efe95888c3d048 | CC BY 4.0 |
| 12 | raw_teams_20261005/timestamp.json | https://github.com/nflverse/nflverse-data/releases/download/teams/timestamp.json | tag `teams` | — | 43 | 5596a6d485b3a55d10f115f532a9f89ae9949abe2afe17838bfc9613b32c34b2 | content: {"last_updated":"2026-03-27 11:49:45 EDT"} |
| 13 | raw_teams_20261005/release_api_teams_colors_logos.json | https://api.github.com/repos/nflverse/nflverse-data/releases/tags/teams_colors_logos | REST releases API | — | 147 | e6fa3955395b2945df66f9729a57f8884e9388e275389539561dcb03aeb4f05b | 404 "Not Found" — wrong tag guess; retained as incident evidence; correct tag `teams` found via releases list |
| 14 | audit_coverage.py | (this lane's own audit script, written locally; not downloaded) | — | — | 6,211 | 5d9c01ee9dfff0aa02878c673bec0dff7b2c604716108b5107cd98911ed39007 | lane-authored measurement script (schema/coverage only) |

Retries: none needed — every curl succeeded on first attempt (dispatch budget
allowed 2; stop condition NOT_RUN_DOWNLOAD not triggered).

## B. Existing archive re-verification (read-only; ~/.my-quantitative-data/nfl-nflverse-v1/)

Re-hashed 2026-10-05 with `shasum -a 256`; every value matches
`raw/ATTRIBUTION.md` inventory and the terminal-cycle FREEZE_MANIFEST chain:

| file | sha256 (recomputed) | bytes | match |
|---|---|---|---|
| raw/games.csv | f1e8fe781400c12874de639b10ce9f3badf7ad48640dfd7fff085c6f5e85248e | 2,182,449 | YES |
| raw/play_by_play_2021.parquet | 333ad34378e5339d5172717cc83378e908daf02c8699416ab3e17c2ec10f78d8 | 20,249,925 | YES |
| raw/play_by_play_2022.parquet | 931121d8897779d7944e2a293e92ed8799c8e5cceef84096ac42339003fedc09 | 20,426,548 | YES |
| raw/play_by_play_2023.parquet | bd3484731408def6b0ec93225bba2bd7b2c65769ca707a2b9444d891abdc6776 | 20,534,088 | YES |
| raw/play_by_play_2024.parquet | 3fd2896bc0b911b615142d2f1fabae54a4bbba5ab7b73b28187b118ef8af6a3b | 20,597,560 | YES |
| raw/play_by_play_2025.parquet | c6ecedd6d678cc37ed316b23ef84ee1ec6abb69c514bb11868a7ebd5a367df29 | 20,337,029 | YES |
| raw/timestamp_pbp.json | 818e5e52dba5dc27982cbd74bf715eb0c28ec83da95a8464c8a993f0cc25fe23 | 43 | YES |
| raw/timestamp_schedules.json | 78733422aaa0f4fa0661fa8145192cb0dd602500e7d3b42dce351e8645ce7937 | 43 | YES |
| raw/ATTRIBUTION.md | b18529758d62284a1711ce1ecbb9061ff1fee735a35c8a8aeac346d7e103aedc | 4,792 | YES |

Derived subdir (games_nfl.csv / lineages_nfl.csv / features_nfl.csv /
manifests) left untouched — those are the pinned inputs of the TERMINAL cycle.

## C. Attribution obligation

Any use of rows 4, 5, 7, 8, 9, 11 carries: "Data: nflverse/nflverse-data
releases (CC BY 4.0), https://github.com/nflverse/nflverse-data".
