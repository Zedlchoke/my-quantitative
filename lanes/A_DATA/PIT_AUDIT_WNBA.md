# PIT AUDIT — WNBA corpus (Lane A, WNBA-WINPROB-PREP-V1)

- task `wbap-a-data` · cycle `WNBA-WINPROB-PREP-V1` · 2026-10-05
- Scope: point-in-time (pre-game knowability) verdict for every candidate feature class in the
  WNBA corpus (`~/.my-quantitative-data/wnba-v1/raw/` + `~/.my-quantitative-data/wnba-prep-v1/extensions/`).
  Evidence: `measurements_a2.json` (`ts_*` blocks), GAME_UNIVERSE_SPEC §3, prior memo §3.7 (context).
- Language law: pre-game knowability only; no outcome metrics computed anywhere in this audit.

## 0. The PIT problem in this corpus (measured)

All release assets are **current-state snapshots with NO publication timestamps**: no column in any
schedule/box/pbp file records when a row first became known. Publisher sidecars give only the last
build time (`timestamp.txt`: ESPN schedules "2026-10-04 06:40:29 EDT", stats "10:36:31 EDT", pbp
"06:39:20", team_box "06:39:35", player_box "06:39:51"; refresh cadence daily 07:00/14:00 UTC
in-season per producer READMEs). Therefore **no row-level "as-of" can be reconstructed from the
snapshot corpus alone**, and every feature must be built **pre-game-safe by construction**:

> ROLLING LAW: any feature for game G may use only inputs from games with `tip_utc` strictly
> < `tip_utc(G)` under the canonical clock (GAME_UNIVERSE_SPEC §3). Same-day, same-window, and
> "last row of the snapshot" inputs are forbidden unless their strict-prior property is proven.

## 1. Verdicts by feature class

| # | feature class | source | verdict | reasoning (measured) |
|---|---|---|---|---|
| 1 | Historical results of strictly-prior games (win/loss, margins as *inputs* to a rating or rolling window) | schedules both sides | **PIT_SAFE by construction** | Results exist only for `status_type_state=='post'` games; pairing with strictly-prior `tip_utc` makes leakage impossible even without publish timestamps. Filter law of SPEC §4 mandatory (0–0 prefill, forfeit/postponed, ASG, TBD). |
| 2 | Rolling team form (last-k games, rest days, schedule density) on canonical `tip_utc`/`local_date` | schedules | **PIT_SAFE by construction** | Same clock law; rest-day math must use `tip_utc` deltas, not naive dates (late ET games cross midnight UTC — measured 53.5% of games have UTC date != ET date). |
| 3 | Season-start rating carryover / continuity (e.g. roster-continuity-modulated Elo) | schedules + `espn_wnba_game_rosters` (2002–2026) | **PIT_SAFE with conditions** | Rosters are per-game snapshots keyed by `game_id` with `starter/did_not_play/active` — POST-GAME facts per game. Continuity must be computed from **strictly-prior-game** rosters only (e.g. prior-season finale, or prior game in season); the current game's roster file row is forbidden. Coverage: asset-level census shows rosters exist 2002+ (2013 sample verified: 4,961 rows/22 cols); 1997–2001 has no rosters → any continuity feature is 2002+ only, or carries a structural missing-flag for 1997–2001. |
| 4 | Elo/rating updated game-by-game | schedules | **PIT_SAFE by construction** | Standard strictly-prior update under `tip_utc`; fresh WNBA K/HCA selection must be train-internal per plan (mechanism lane's job, not a data verdict). |
| 5 | `player_box` per-game fields: `active` / `did_not_play` / `starter` / `ejected` / `reason` / minutes / stats | espn_wnba_player_boxscores | **POST_GAME_FACT — FORBIDDEN as pre-game features** | These describe the game being predicted (2025 sample: active 3,119 True/4,021 False rows; DNP 1,224; starter 3,120; reasons incl. "COACH'S DECISION"). They may only be used (a) as strictly-prior-game aggregates (e.g. games-missed streak entering game G from games < G), or (b) as labels. |
| 6 | `team_box` per-game team stats (four factors, rebounds, …) | espn_wnba_team_boxscores | **POST_GAME_FACT — FORBIDDEN for the current game**; PIT_SAFE as strictly-prior rolling aggregates | Same law; note schema drift: `points_in_paint`/`fast_break_points`/`turnover_points` are absent in 2013 (measured) — depth-stat rolling windows have an era-availability boundary that must be handled as missingness, not zeros. |
| 7 | PBP-derived features (pace, lineup net ratings, clutch splits) | espn_wnba_pbp / wnba_stats_pbp | **PIT_SAFE only as strictly-prior aggregates**; `wallclock`/`sequenceNumber` of the CURRENT game are in-game, not pre-game | PBP `wallclock` is 100% UTC (F3) — usable to order events; never usable to know anything "before tip" beyond what schedules give. |
| 8 | Lineups (`wnba_stats_lineups`) | release 2026 only | **NOT_RUN_PIT for history; unavailable pre-2026** | 1-season coverage (2026, 8 assets) — cannot support a historical train window; any lineup feature would be 2026-only with no train era. Not a viable feature class for this program absent more seasons. |
| 9 | Injury reports / availability feeds | — | **NOT_RUN_PIT — no rights-verified source exists in this corpus** | No dedicated injury feed in any wehoop-family release (memo §3.7). Nearest proxies: `player_box.did_not_play` + `reason` (2025 sample 1,224 DNP rows, reasons incl. "RIGHT KNEE", "ACL", "INJURY/ILLNESS", "COACH'S DECISION") — but these are **post-game observations**, not pre-game reports; using them as "injury status before game G" is leakage by construction. A true injury feature needs an archive with real publication timestamps (e.g. dated news/transaction logs) proven rights-cleared — none identified; any candidate must show publish-time provenance before leaving NOT_RUN_PIT. |
| 10 | `wnba_crosswalk` schedule crosswalk | wnba_crosswalk release | **PIT_SAFE as an ID map** (identity only, no outcomes) | 2026-only; contains ids/team pairs, `match_confidence`; no outcome fields. |
| 11 | Betting/market odds | — | **OUT OF SCOPE / banned by plan** | No odds source in corpus; plan bans market odds for the fresh program. Listed for completeness. |
| 12 | Standings/records derived features | schedules | **PIT_SAFE by construction** | Derivable from strictly-prior played games under the filter law; never from "current" snapshot aggregates that include the game being predicted. |

## 2. Candidate PIT hazards found while measuring (recording, per dispatch)

- **0–0 prefill trap**: unplayed rows are 0–0 with `status_type_state=='pre'` (17 rows, all 2026).
  Any feature code that filters "played" via `home_score>0` or score presence will silently ingest
  fake zeros in future windows. Mandate: filter law SPEC §4.
- **Suspended-game trap**: the 2019 WAS@LVA suspension is keyed 2019-07-05 on stats side but
  2019-08-05 (completion) on ESPN side. Rolling windows built independently per source can
  double-count or mis-order this game. Mandate: use the canonical union table (SPEC §6/§7) with one
  game per real-world game (ESPN status side authoritative for 2002+; the stats-side date is the
  suspension date, not the completion date).
- **Back-to-back series ambiguity**: pass-1 window joins of same-team pairs within 3 days are
  ambiguous (24 measured pairs) — any feature builder that joins game-level tables must use the
  score-fallback disambiguation (SPEC §7 pass 2) or game ids within one source only.
- **Cup finals asymmetry**: 6 Cup finals (2021–2026) exist only on ESPN side. A stats-spine universe
  silently drops them; an ESPN-spine universe must not expect stats-side ids for them. Decide and
  freeze the spine in the protocol (recommendation: ESPN spine 2002+, stats side 1997–2001 only,
  union 7,017 rows documented).
- **Era boundary facts**: box scores start 2003 (ESPN side), PBP/player_box 2002, rosters 2002,
  schedules 1997 (stats only pre-2002); depth box columns (`points_in_paint` etc.) modern-era only
  (absent 2013, measured). Every rolling feature must carry an explicit era-availability guard.

## 3. Bottom line

- PIT verdict for the corpus as a whole: **PIT_SAFE_BY_CONSTRUCTION is achievable** for
  results/rating/rest/rolling/continuity feature classes under the ROLLING LAW + filter law +
  canonical clock; no snapshot publication-time reconstruction is required for those.
- **NOT_RUN_PIT stands** for injury/availability-as-reported and anything requiring real publish
  timestamps; the only candidate archives (raw-JSON season bundles) are also undated snapshots and
  do not fix PIT for injuries.
- `player_box` active/DNP/starter, `team_box` stats, and PBP events of game G are POST-GAME facts —
  they enter features only from strictly-prior games, or as labels.

## 4. Reproduction

`measurements_a2.json` blocks: `ts_espn_schedule_instant_equality_fixed`, `ts_box_flavor_2025`,
`ts_pbp_wallclock`, `sample2025` (player_box active/DNP/starter counts), `recon_rowlevel`
(suspended game, score fallback), `release_depth_census.json` (era coverage). No outcome metrics
were computed; every number here is a schema/coverage fact.
