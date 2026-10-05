# VERDICT TABLE — Lane C (NFL PLAYER DATA) · WINPROB-PLAYERDATA-PREP-V1

Measured 2026-10-05. All verdicts from bytes/commands this session; nothing inferred.

## Checks × data type

| check | data type | verdict | evidence |
|---|---|---|---|
| On-disk player-level inventory | nflverse corpus (pbp/games) | **PASS (expectation NONE confirmed)** | INVENTORY.md §1: pbp = play-level (2024 parquet 49,492×372, per-play attribution cols); zero NFL player-stats files in full-tree sweep |
| Official source publishes weekly player stats | nflverse-data release store | **PASS** | `stats_player` release, 554 assets, `stats_player_week_2026.parquet` updated 2026-10-05T05:30:11Z; body verbatim "Player stats in different summary levels created with `nflfastR::calculate_stats()`"; legacy `player_stats` release frozen 2025-05-07 (documented) |
| License verified live | nflverse-data LICENSE | **PASS** | CC BY 4.0 confirmed live 2026-10-05T07:18:02Z (HTTP 200), verbatim quotes in RIGHTS.md; byte-identical to prior-cycle copy (`diff` clean) |
| Download weekly player stats (+ aggregates) | parquet | **PASS** | 8 files HTTP 200, 2,612,367 B total, full provenance in DOWNLOAD_MANIFEST.md (+ .json); $0 |
| Re-download determinism | parquet | **PASS** | stats_player_week_2025.parquet re-pulled 26 s later: byte-identical (sha256 2a461bec…5fff10) |
| Season/week coverage | weekly stats | **PASS** | 2024: 285 games wk1–22 (REG1–18, POST19–22); 2025: 285 same; 2026: 63 games wk1–4 REG in progress |
| games.csv join | game_id | **PASS** | join rate 285/285 (2024), 285/285 (2025), 63/63 (2026; 209 games-only = future). Team/opponent consistency 100% |
| Players per game | weekly stats | **PASS** | median 66–68 (min 57, max 82) |
| Duplicates | player_id+game_id | **PASS** | 0 duplicates in all weekly files; 0 in snap_counts (pfr_player_id+game_id) |
| Missing values | weekly stats | **PASS (documented)** | 1 all-zero NaN-player placeholder row per week (22/22/4); epa/cpoe/pacr populated only on relevant rows; no unexpected gaps |
| Schema drift | weekly stats 2024/2025/2026 | **PASS (none)** | identical 150 col names + order across all three seasons |
| Kickoff-time UTC canonicalization | games.csv gameday+gametime ET | **PASS (caveats logged)** | PIT_AUDIT §1; gametime missing only in season 1999 (259 rows); DST guards; verbatim ET-convention quote |
| Prior-games as-of aggregate constructible | weekly stats × games.csv | **PASS** | worked example 2024_11_KC_BUF prior-3 Mahomes 819 yds/6 TD/1 INT/124 att; leak guards asserted PASS (PIT_AUDIT §2) |
| Prospective-only window 2026 | weekly stats 2026 | **PASS** | all 63 stat games kicked off before download moment; 0 future games with stats; MNF 2026-10-06T00:15Z absent |
| On-disk pbp participation columns (prior-week snaps from pbp 2021–2025) | pbp parquet | **NOT_RUN_PIT** | on-disk pbp has NO per-player participation/snap columns (only event attributions); data exists as separate `pbp_participation` release (2016–2025, listed, not downloaded) — superseded by downloaded snap_counts |
| Prior-game snap counts (PIT-safe snap source) | snap_counts release | **PASS** (constructible) | snap_counts 2025 (26,613 rows, 285/285 games, wks 1–22) + 2026 (49 games, lags stats by ~3 days) downloaded; PIT_AUDIT F2 |
| Target-game injury/active status | injuries / rosters | **NOT_RUN_PIT (carried blocker)** | prior-cycle law re-confirmed: no per-record publish timestamps in injuries dumps; weekly_rosters timing not audited |
| Same-game stats | any | **BANNED** | doctrine §13; enforced by leak guards |
| 2026 split law consistency | schedules | **PASS (nuance logged)** | law 63/209 + earliest future 2026-10-06T00:15Z holds at download moment; on-disk schedule snapshots hours-stale (62/210, 49/223) — documented in PIT_AUDIT §3 |
| Scored computation / win-prob metrics | — | **NOT_RUN (by law)** | 0 scored; design-only comparison specified in FEATURE_PROPOSALS.md |

## Actually-downloaded files (path + sha256 + bytes)

Data dir `~/.my-quantitative-data/playerdata-prep-v1/nfl/` (all sha256 full values in
DOWNLOAD_MANIFEST.md; prefixes here):

| file | bytes | sha256 (first 16) |
|---|---|---|
| raw_stats_player/stats_player_week_2024.parquet | 849,243 | 847569d194ca3d96 |
| raw_stats_player/stats_player_week_2025.parquet | 855,077 | 2a461becaa9adb3c |
| raw_stats_player/stats_player_week_2026.parquet | 303,597 | 49bc644ed4bf1054 |
| raw_stats_player/stats_player_regpost_2025.parquet | 289,427 | 4459100761b252f1 |
| raw_stats_player/timestamp_stats_player.json | 43 | 437d1a70bb9a7fac |
| raw_snap_counts/snap_counts_2025.parquet | 242,046 | 47220218fecda7af |
| raw_snap_counts/snap_counts_2026.parquet | 72,945 | fae0627d81f4ffa1 |
| raw_snap_counts/timestamp_snap_counts.json | 43 | 36a66624cf4967e5 |
| rights/nflverse-data_LICENSE.md (live fetch) | 18,651 | 2a82ac9bbc3e3ee0 |
| rights/nflverse-data_README.md (live fetch) | 699 | a343c9cb9dbf2cef |

Cached listing: release_api_listing.json (25 releases, 1 GitHub API call).
Logs: download_log_attempt1.json, download_log_redownload.json. ATTRIBUTION.md present.

## Remaining blockers

1. **Target-game injury/active/DNP features: NOT_RUN_PIT** — no per-record publish timestamps
   (carried from prior cycle; unchanged by this lane's findings).
2. **GSIS↔PFR id crosswalk not downloaded** (`players` release `players.parquet`) — required
   before player-level joins between weekly stats and snap_counts; bucket/team-level features
   do not need it.
3. **snap_counts 2026 in-season lag** (Oct-2 build vs Oct-5 stats) — in-season snap features
   must tolerate ≤1-week staleness; fine at weekly cadence, not intra-week.
4. **Weekly stats availability is release-cadence, not row-level**: only release-level
   `timestamp.json` exists; historical files are re-cut at season boundaries — frozen sha256s
   here are the cycle's evidence anchor.

## Cost

Actual: **$0** (unauthenticated public URLs only; 1 GitHub API call). No accounts, no keys.

## GO/HOLD for FEATURE-PREP

**HOLD (not a scored GO)** — PREP lane verdict: data and rights are sufficient to propose a
FEATURE-PREP successor (weekly player stats PIT-safe for prior-games aggregates; snap counts
available as snap-share source), conditional on: (a) owner instruction + fresh registration
per plan, (b) fetching the players.parquet crosswalk with re-hash before any cross-id join,
(c) respecting the NOT_RUN_PIT blockers above and B1\* K40 HCA0 frozen yardstick. No scored
work is authorized by this lane.
