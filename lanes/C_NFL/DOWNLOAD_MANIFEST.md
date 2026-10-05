# DOWNLOAD MANIFEST — Lane C (NFL PLAYER DATA) · WINPROB-PLAYERDATA-PREP-V1

All downloads 2026-10-05, unauthenticated GitHub release browser URLs, HTTP 200.
Data dir (outside git): `~/.my-quantitative-data/playerdata-prep-v1/nfl/`
Machine-readable log: `download_log_attempt1.json` (+ `download_log_redownload.json`).
ATTRIBUTION.md present in the data dir. Cost: $0.

## Files

| # | file (rel to data dir) | release tag | URL (browser_download_url) | HTTP | downloaded UTC | bytes | sha256 |
|---|---|---|---|---|---|---|---|
| 1 | raw_stats_player/stats_player_week_2024.parquet | stats_player | https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2024.parquet | 200 | 2026-10-05T07:18:37Z | 849,243 | 847569d194ca3d96b5efcf91e6eac5e18780fc47568a713fd545a82d29d155c1 |
| 2 | raw_stats_player/stats_player_week_2025.parquet | stats_player | https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2025.parquet | 200 | 2026-10-05T07:18:38Z | 855,077 | 2a461becaa9adb3c93a3074a3a31f1e960162a50163371a2d34e28393b5fff10 |
| 3 | raw_stats_player/stats_player_week_2026.parquet | stats_player | https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2026.parquet | 200 | 2026-10-05T07:18:39Z | 303,597 | 49bc644ed4bf10546b399ce177045f09ef278a562fc894074311c8afa6b26179 |
| 4 | raw_stats_player/stats_player_regpost_2025.parquet | stats_player | https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_regpost_2025.parquet | 200 | 2026-10-05T07:18:40Z | 289,427 | 4459100761b252f11509bce334dc48b6ab8d2f89ae26138436b17efc09235669 |
| 5 | raw_stats_player/timestamp_stats_player.json | stats_player | https://github.com/nflverse/nflverse-data/releases/download/stats_player/timestamp.json | 200 | 2026-10-05T07:18:41Z | 43 | 437d1a70bb9a7fac3fda39174ddbbfbe21d3ba43f4a391799021187e1c8e6115 |
| 6 | raw_snap_counts/snap_counts_2025.parquet | snap_counts | https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_2025.parquet | 200 | 2026-10-05T07:18:42Z | 242,046 | 47220218fecda7af7ee5b0272a8ecce7c1bfb1f4e1f0a2c8c90047571728ce20 |
| 7 | raw_snap_counts/snap_counts_2026.parquet | snap_counts | https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_2026.parquet | 200 | 2026-10-05T07:18:43Z | 72,945 | fae0627d81f4ffa1802263ac0fad1a29f5c1986d5749a711bde7c50651498273 |
| 8 | raw_snap_counts/timestamp_snap_counts.json | snap_counts | https://github.com/nflverse/nflverse-data/releases/download/snap_counts/timestamp.json | 200 | 2026-10-05T07:18:44Z | 43 | 36a66624cf4967e5c8e4c9d90d27b80c43664f4491e96bbe67bb4a0dcc16e5bd |

Total: 2,612,367 bytes (~2.5 MiB). All byte sizes equal the GitHub API asset `size` metadata in
the cached release listing (cross-checked per asset).

## Release as-of markers (downloaded timestamp.json contents)

- `stats_player`: `{"last_updated":"2026-10-05 01:30:28 EDT"}` = 2026-10-05T05:30:28Z — the
  release build captured by this session's weekly-stats download. This is the **release date
  taken**: nflverse re-releases whole-history files, so any future re-pull of season files
  (e.g. 2024/2025) may differ from these hashes. Offseason re-cut caveat applies.
- `snap_counts`: `{"last_updated":"2026-10-02 07:01:49 EDT"}` = 2026-10-02T11:01:49Z.

Note: `stats_player_week_2025.parquet` / `_2024.parquet` were last asset-updated
2026-08-13T16:51Z (season finalized); `stats_player_week_2026.parquet` is in-season (updated
2026-10-05T05:30:11Z, minutes before this session's download).

## Re-download determinism (re-downloadability proof)

Re-downloaded file #2 (`stats_player_week_2025.parquet`) at 2026-10-05T07:19:04Z:

- first pull: 855,077 B, sha256 `2a461becaa9adb3c93a3074a3a31f1e960162a50163371a2d34e28393b5fff10` (07:18:38Z)
- second pull: 855,077 B, sha256 `2a461becaa9adb3c93a3074a3a31f1e960162a50163371a2d34e28393b5fff10` (07:19:04Z)
- **BYTE-IDENTICAL: True**

(2025 season file is post-finalization, hence stable; in-season 2026 assets change between
release builds — re-pull during season yields new bytes by design.)

## Not downloaded (documented from release listing only)

`pbp_participation_{2016..2025}.parquet` (per-play participation; 2025 parquet 4,741,443 B),
`players.parquet` (id crosswalk), `weekly_rosters` 2002+, legacy `player_stats` release assets
(frozen 2025-05-07). All published under the same CC BY 4.0 store (see RIGHTS.md).
