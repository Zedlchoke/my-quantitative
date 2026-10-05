# DOWNLOAD MANIFEST — Lane A extensions (WNBA-WINPROB-PREP-V1)

- task `wbap-a-data` · pulled 2026-10-05T04:08Z (machine UTC) by lane A
- Source: public GitHub release store `sportsdataverse/sportsdataverse-data` (no auth, no account,
  $0). Data license: CC BY 4.0 badge on the store README; code MIT (same nflverse-family pattern
  already verified by WINPROB-NG-PREP-V1 lane B — see `ATTRIBUTION.md` in the corpus and the prior
  memo §1a). No wnba.com / stats.wnba.com / ESPN / Sports Reference access; no balldontlie.
- Destination: `~/.my-quantitative-data/wnba-prep-v1/extensions/` (outside git). Existing corpus
  bytes under `~/.my-quantitative-data/wnba-v1/` untouched (EXTEND-ONLY respected).
- Release metadata (asset lists incl. GitHub `digest` fields) fetched via api.github.com for 9 tags
  and archived verbatim at `~/.my-quantitative-data/wnba-prep-v1/release_depth_census.json`
  (sha256 adf01fecec2deccedc7fb0ccfa9d1eda9fe8d9623a4ae7ba55b12e47a6f2d54d).

## Files downloaded (5 files, 1,240,676 bytes total)

| file | release tag | URL asset | bytes | sha256 | GitHub digest match | pull UTC |
|---|---|---|---:|---|---|---|
| wnba_team_crosswalk_2026.csv | `wnba_crosswalk` | …/download/wnba_crosswalk/wnba_team_crosswalk_2026.csv | 2,126 | e0d1cbaea3d934aa8c6311f65ea24fff6bd397ff7b6fc9b1f13b64792bd39129 | n/a (asset predates digest field) | 2026-10-05T04:08Z |
| wnba_schedule_crosswalk_2026.csv | `wnba_crosswalk` | …/download/wnba_crosswalk/wnba_schedule_crosswalk_2026.csv | 42,098 | e4115f04d45d3bc7fb9b43eca9c5babd26185e2ecf51e65bc3b66bf02aa6eea6 | n/a | 2026-10-05T04:08Z |
| wnba_player_crosswalk_2026.csv | `wnba_crosswalk` | …/download/wnba_crosswalk/wnba_player_crosswalk_2026.csv | 28,006 | 3055534cf9526c0af3bea8cd5e776722dcf503a800bbc636afbaa4cfa09bedd5 | n/a | 2026-10-05T04:08Z |
| team_box_2013.csv | `espn_wnba_team_boxscores` | …/download/espn_wnba_team_boxscores/team_box_2013.csv | 181,740 | e2f7510a5b6c64863eb0e8c9f95f8dc7865141a3a5ba6d95ab9ef24072d2c597 | **MATCH** (`sha256:e2f7510a…`) | 2026-10-05T04:08Z |
| game_rosters_2013.csv | `espn_wnba_game_rosters` | …/download/espn_wnba_game_rosters/game_rosters_2013.csv | 982,809 | 49571374e18ac2ca37c2b9ccd1d8606337d7ea329f48e832e871f722cdf36670 | **MATCH** (`sha256:49571374…`) | 2026-10-05T04:08Z |

- Integrity: `shasum -a 256` over the downloaded files recorded in
  `extensions/sha256_extensions.txt`; the two assets carrying GitHub API digests verify byte-exact.
- Asset `updated_at` (publisher, from the archived API metadata): crosswalk assets 2026-06-13,
  team_box_2013 2026-07-16T21:54:07Z, game_rosters_2013 2026-07-16T21:54:56Z.
- Purpose (census-only, per dispatch 1f): crosswalks validate the §2/§7 join law for 2026;
  team_box_2013 verifies mid-era box schema (no `points_in_paint` — modern-era column);
  game_rosters_2013 verifies roster depth (starter/DNP/reason back to 2002) for a PIT-safe
  continuity mechanism. **Not** a full mirror: no PBP, no shots, no full-history box pulled.
- Not downloaded (deliberate, within etiquette/owner budget): full-history PBP (ESPN 1,065.7 MB;
  stats 213.9 MB), player_box history (64.3 MB), shots (147.4 MB), lineups (19.5 MB), stats-side
  team box (0.1 MB, 2026 only). Total remaining optional mirror ≈ +1.5 GB.
- Attribution required on any use: "Data from SportsDataverse (wehoop), sportsdataverse-data
  release store, CC BY 4.0; underlying statistics sourced from ESPN WNBA API and stats.wnba.com."
