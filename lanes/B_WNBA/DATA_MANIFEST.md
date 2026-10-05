# WNBA v1 RAW DATA MANIFEST — Lane B (WINPROB-NG-PREP-V1)

- Pulled (UTC): 2026-10-05, audit run `2026-10-05T01:51:07Z`
- Location: `~/.my-quantitative-data/wnba-v1/raw/` (98 data files + `audit_results.json`)
- Total bytes: 77,686,677
- Integrity: sha256 computed for every file; **19 files byte-verified against GitHub release-asset digests (`digest` field, where the API publishes one); 0 mismatches.** 73 older assets carry no published digest (GitHub started populating `digest` in 2024) — sha256 recorded here is the only fingerprint for those.

## Download groups

### `espn_schedules/`

ESPN WNBA schedules full history — tag `espn_wnba_schedules` (upstream: ESPN WNBA API), release last refreshed 2026-10-04T10:40Z (sidecar `timestamp.txt`: 2026-10-04 06:40:29 EDT). 25 seasons 2002-2026, per-season csv+parquet + master + games-in-data-repo catalog + publisher sidecars.

| file | bytes | sha256 | github digest match |
|---|---:|---|---|
| espn_schedules/package_function.txt | 29 | `3653be1c98884f9b…` | n/a (no published digest) |
| espn_schedules/timestamp.txt | 24 | `6fb1df849fffee25…` | n/a (no published digest) |
| espn_schedules/wnba_games_in_data_repo.csv | 7072229 | `3c39960951874c7b…` | verified |
| espn_schedules/wnba_games_in_data_repo.parquet | 469570 | `bd18568558341e86…` | verified |
| espn_schedules/wnba_schedule_2002.csv | 167142 | `82a32b2bd54307a8…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2002.parquet | 59258 | `45c76a398c15a060…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2003.csv | 157057 | `2213274bf904a7ee…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2003.parquet | 56582 | `162b79b7a2fdf5a3…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2004.csv | 154787 | `10f228d743558a04…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2004.parquet | 55866 | `cdb6704406fbad70…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2005.csv | 153634 | `9fbc61afb3f4843d…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2005.parquet | 55338 | `ca3669184ba56777…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2006.csv | 164836 | `32855982cb32972b…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2006.parquet | 57415 | `4b3f54a2014864df…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2007.csv | 155796 | `d91f4e8848053ed1…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2007.parquet | 56611 | `a9fa62807675f66a…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2008.csv | 166407 | `3800ee74f4e6310f…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2008.parquet | 58028 | `1576bd512152ba00…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2009.csv | 157122 | `f33d687d555d999c…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2009.parquet | 57038 | `fa232d1050978c7b…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2010.csv | 142439 | `b3803d03df22b9c5…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2010.parquet | 55089 | `aab58747c85104b2…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2011.csv | 144869 | `4057733233c71019…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2011.parquet | 55498 | `31d118cbeceae1a5…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2012.csv | 144473 | `989e28c1e71aa922…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2012.parquet | 55735 | `ba6da1db701337b3…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2013.csv | 148526 | `0f23272988184420…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2013.parquet | 57035 | `f53e3807c557e1ac…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2014.csv | 148538 | `55866e03f1033628…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2014.parquet | 57093 | `93b4e05db6938d4c…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2015.csv | 150620 | `c05fb012d03d6b35…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2015.parquet | 57028 | `749e6de5c80e8188…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2016.csv | 148231 | `85d513c119f7f346…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2016.parquet | 56571 | `9f99787a0618c60c…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2017.csv | 148643 | `aea35c763301ab75…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2017.parquet | 56816 | `b0b6650c140d61fe…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2018.csv | 151534 | `4f79fe57e818304e…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2018.parquet | 56906 | `94f36fe79be563f3…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2019.csv | 151187 | `83e98d9b8e64fd3b…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2019.parquet | 56756 | `7ceacdd2d3672589…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2020.csv | 98943 | `07241edec53a98d5…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2020.parquet | 49341 | `3499d19a2cd88771…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2021.csv | 145585 | `a9f112e5e1c14a6c…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2021.parquet | 56023 | `0edcf93bed89cad8…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2022.csv | 166007 | `4cad1b73ee418bd5…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2022.parquet | 58429 | `74e9881812e04301…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2023.csv | 343106 | `3e3ab7181f1c5ef7…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2023.parquet | 85480 | `1f8cae8268afe4bf…` | n/a (no published digest) |
| espn_schedules/wnba_schedule_2024.csv | 426630 | `62994931d49303ab…` | verified |
| espn_schedules/wnba_schedule_2024.parquet | 85259 | `4c4b8f8dc4290996…` | verified |
| espn_schedules/wnba_schedule_2025.csv | 529430 | `b1fe7187113b9336…` | verified |
| espn_schedules/wnba_schedule_2025.parquet | 99293 | `c7cc5144a0d4bd84…` | verified |
| espn_schedules/wnba_schedule_2026.csv | 2516876 | `685a9256350e356d…` | verified |
| espn_schedules/wnba_schedule_2026.parquet | 165119 | `58aba80e5814e9f0…` | verified |
| espn_schedules/wnba_schedule_master.parquet | 476041 | `05d35418c3b7ccc0…` | verified |

### `wnba_stats_schedules/`

WNBA Stats (stats.wnba.com) schedules full history — tag `wnba_stats_schedules` (upstream: stats.wnba.com official endpoints), release last refreshed 2026-10-04T14:36Z (sidecar: 2026-10-04 10:36:31 EDT). 30 seasons 1997-2026 csv.gz + master + 2025 csv + sidecar.

| file | bytes | sha256 | github digest match |
|---|---:|---|---|
| wnba_stats_schedules/timestamp.txt | 24 | `d48b9f81afc5c00f…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_1997.csv.gz | 2001 | `7ca1e5737a048676…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_1998.csv.gz | 2671 | `492e00f7ae843450…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_1999.csv.gz | 3427 | `c17448d86ab82d09…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2000.csv.gz | 4599 | `80730884a148d980…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2001.csv.gz | 4600 | `29dd882d216ccf3b…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2002.csv.gz | 4605 | `5d075b258e6aafcc…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2003.csv.gz | 4252 | `a647fca1cc01319f…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2004.csv.gz | 3976 | `f3c62047eff825ec…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2005.csv.gz | 3952 | `1cab01beb650fbf6…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2006.csv.gz | 4300 | `d620e1650c3bd91b…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2007.csv.gz | 4020 | `8b0211dbfc6587e7…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2008.csv.gz | 4361 | `0a1d51ba16d0d724…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2009.csv.gz | 4075 | `877b8b7d69664249…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2010.csv.gz | 3702 | `7be98f5415ba7f48…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2011.csv.gz | 3686 | `5972612123343aed…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2012.csv.gz | 3684 | `1258a55bd7cdf528…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2013.csv.gz | 3663 | `0c5333059e338a70…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2014.csv.gz | 3624 | `c331886401af78f5…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2015.csv.gz | 3678 | `137db70fe4e4ef99…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2016.csv.gz | 3655 | `7c952f33fa7db3cd…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2017.csv.gz | 3623 | `d681df23598c1cf1…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2018.csv.gz | 3619 | `b5d2cec1211794b1…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2019.csv.gz | 3633 | `c0ab89405bbf0d25…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2020.csv.gz | 2718 | `6fa8b34f845ebaf1…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2021.csv.gz | 3494 | `a9349baed174ab81…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2022.csv.gz | 3856 | `fdeafb4f40ca8b17…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2023.csv.gz | 4125 | `86da5c3c48d2aa73…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2024.csv.gz | 4155 | `47875ed1e4a6b156…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_schedule_2025.csv.gz | 4909 | `094dc7e91eb0cf3f…` | verified |
| wnba_stats_schedules/wnba_schedule_2026.csv.gz | 5513 | `2ec5d5c8844777e7…` | n/a (no published digest) |
| wnba_stats_schedules/wnba_stats_schedule_2025.csv | 89162 | `28508741d64c445f…` | verified |
| wnba_stats_schedules/wnba_stats_schedule_master.csv | 51786 | `32d86a60124cfcfa…` | verified |
| wnba_stats_schedules/wnba_stats_schedule_master.parquet | 25284 | `93dc80e0cbe73003…` | verified |

### `espn_sample_2025/`

ONE-SEASON SAMPLE (2025) — tags `espn_wnba_team_boxscores` / `espn_wnba_player_boxscores` / `espn_wnba_pbp` (upstream: ESPN WNBA API). team_box + player_box + play_by_play, csv+parquet each, + publisher sidecars.

| file | bytes | sha256 | github digest match |
|---|---:|---|---|
| espn_sample_2025/play_by_play_2025.csv | 52665227 | `01493a7f6c7e368d…` | verified |
| espn_sample_2025/play_by_play_2025.parquet | 4060185 | `d4c8a43b3700ec5a…` | verified |
| espn_sample_2025/player_box_2025.csv | 3559371 | `dd0496590397a72d…` | verified |
| espn_sample_2025/player_box_2025.parquet | 173938 | `9a416f637b7e95af…` | verified |
| espn_sample_2025/team_box_2025.csv | 276125 | `f32d9ebefa40632f…` | verified |
| espn_sample_2025/team_box_2025.parquet | 49409 | `b241743395be6808…` | verified |
| espn_sample_2025/timestamp_pbp.txt | 24 | `f2ee19653c661742…` | n/a (no published digest) |
| espn_sample_2025/timestamp_player_box.txt | 24 | `0b4cafc92c2150f6…` | n/a (no published digest) |
| espn_sample_2025/timestamp_team_box.txt | 24 | `ff3fce85c180fddc…` | n/a (no published digest) |

| audit_results.json | machine-readable census output of `audit_script.py` (also in lane B) | | |

## NOT downloaded (deliberate, audit-only scope)

- `espn_wnba_pbp` / `wnba_stats_pbp` for seasons != 2025 (full-history PBP = 1,015.9 MB ESPN + 203.6 MB stats.wnba.com — download in a future cycle if the modeling lane wants 1997-2024 PBP).
- `espn_wnba_shots` (140.6 MB, 2002-2026), `espn_wnba_game_rosters` (29.0 MB, 2002-2026), `wnba_stats_lineups` (2026 only), `espn_wnba_officials`, `espn_wnba_draft`, rosters/season-stats releases, `wnba_stats_possessions` (37.2 MB).
- `wnba-stats-raw-json` season bundles (whole-season raw JSON from stats.wnba.com).
