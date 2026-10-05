# ROSTER PIT AUDIT — WNBA game_rosters + player_box (task wbap-a-data-r2, W-H2 gate)

- task `wbap-a-data-r2` · cycle `WNBA-WINPROB-PREP-V1` · role quant-explorer · 2026-10-05
- worktree `/Users/hoangminhlong/my-quantitative/.worktrees/wnba-winprob-prep-v1/integration`,
  branch `orca/wnba-winprob-prep-v1-integration` · dispatch_sha = actual_start_sha =
  `6681486d356d04690873f25badf05500ed22f430` (measured `git rev-parse HEAD` at lane start; no git
  operations performed by this lane — controller lands).
- Owner order 2026-10-05: adjudicate the roster/lineup PIT question for **W-H2**
  (continuity-modulated rating carryover) on measured evidence, per-league data only.
- Machine output (re-runnable): `~/.my-quantitative-data/wnba-prep-v1/roster_audit/measurements_r2.json`
  (script `lanes/A_DATA/measure_r2_roster.py`; downloads by `lanes/A_DATA/measure_r2_download.py`).
- Schema/coverage counting ONLY — no win-prob metric, no Elo run, no scored computation anywhere
  in this audit. **WNBA data only; no NBA number, parameter or verdict entered any claim below.**

---

## 1. VERDICT (read this first)

**PIT_PASS_BY_CONSTRUCTION** for the game-linked prior-season continuity construction, under the
as-of law of §7 — with a measured eligibility-window constraint that the successor design MUST
carry (§5): minutes-weighted continuity is computable for 100% of teams only from season **T=2006**
onward; roster-membership continuity is computable from **T=2003**; 2003–2004 are excluded (or
structural-missing) for the minutes-weighted variant because the 2002 player_box asset is a stub
(16 of 271 games, minutes column 100% `--`).

**W-H2 keep-or-drop recommendation: KEEP** W-H2 in the scored-successor proposal. The PIT gate
clears — W-H2 does **not** leave as NOT_RUN_PIT. The continuity arm's eligible evaluation window is
fixed by measurement at **T ≥ 2006** (minutes-weighted, 100% of non-expansion team-seasons) or
**T ≥ 2003** (roster-share variant), to be frozen by Lane C at protocol registration.

Why PASS is fail-closed here: every input of the audited construction is a post-game fact of a
strictly prior game, so pre-tip knowability of season-T predictions holds **by construction** —
no publication-timestamp reconstruction is needed or claimed. What had to be measured (and now is):
(a) rows are genuinely keyed to prior games, (b) coverage is sufficient, (c) no retro-fill hazard.
All three measured PASS within the stated window; the two input-availability gaps (2002 box stub,
2003–2008 partial box) are coverage facts, not PIT failures, and they shrink the window instead of
silently contaminating it.

---

## 2. Download manifest (rights-cleared GitHub release assets, no auth, $0)

- Source: public release store `sportsdataverse/sportsdataverse-data` (data badge CC BY 4.0, repo
  code MIT — nflverse-family pattern already verified by the prior cycle; internal research use
  with attribution). **No** wnba.com / stats.wnba.com / ESPN / Sports Reference access; no auth,
  no account, no purchase.
- Full verbatim manifest: `~/.my-quantitative-data/wnba-prep-v1/roster_audit/download_manifest_r2.json`
  (per-file URL, bytes, local sha256, GitHub digest, digest-match, per-file pull UTC, asset
  `updated_at`). Raw API responses: `roster_audit/release_meta_r2.json`.
- Pulls (machine UTC): roster files 2026-10-05T06:57:52Z; player_box files 2026-10-05T06:58:28–29Z.

| release tag | files pulled | bytes | URL pattern | integrity |
|---|---|---:|---|---|
| `espn_wnba_game_rosters` (published 2026-05-11T23:02:07Z) | 25 season csv (`game_rosters_2002.csv` … `game_rosters_2026.csv`) | 28,162,804 | `github.com/sportsdataverse/sportsdataverse-data/releases/download/espn_wnba_game_rosters/espn_wnba_game_rosters/<file>` | 25/25 sha256 == GitHub API `digest` |
| `espn_wnba_player_boxscores` | 25 season csv (`player_box_2002.csv` … `player_box_2026.csv`) | 58,409,287 | same pattern, tag `espn_wnba_player_boxscores` | 23/25 sha256 == GitHub digest; `player_box_2002.csv`, `player_box_2023.csv` predate GitHub's digest field (API `digest: null`) — byte size verified against API metadata instead |
| total | 50 files | 86,572,091 | | 0 true mismatches |

- Destination: `~/.my-quantitative-data/wnba-prep-v1/roster_audit/` (outside git, per write scope).
  Corpus `~/.my-quantitative-data/wnba-v1/` untouched (EXTEND-ONLY).
- Release-body claim "25 seasons 2002–2026, 80 assets, 29.0 MB" verified: 25 season CSVs + 25
  parquet + 25 rds + 5 index/aux assets = 80 assets; csv subset 28.2 MB.
- The 2026 files are an **in-progress-season snapshot** (asset `updated_at` 2026-10-04T10:41:55Z;
  season in playoffs at owner round). All 2026 counts below are as-of-snapshot.

## 3. Game linkage — how a roster row is tied to a prior game (measured)

- Roster schema is **identical across all 25 seasons** (22 columns; `season, game_id, team_id,
  team_slug, team_abbreviation, team_display_name, home_away, athlete_id, …, starter,
  did_not_play, active, ejected, reason`).
- Rows carry **`game_id` but NO date column in any season** (measured `roster_has_date_column:
  false`). Linkage to time is **join-based, not embedded**: every roster `game_id` was looked up
  in the ESPN schedules; **0 roster game_ids are absent from the ESPN schedule**; ESPN `game_id`
  is verified 1-row-per-id by lane A (GAME_UNIVERSE_SPEC §1). Date/tip comes from the canonical
  `tip_utc` law (SPEC §3) via that join. This satisfies "genuinely keyed to those prior games":
  the key is total, deterministic, and dated on the schedule side.
- **These are per-game rows, not undated season aggregates**: 5,988 filter-law universe games →
  5,983 with roster rows (§4); rows-per-game median 22–25; exactly-10-starter games in 99.6%
  of covered games (§6); the 2025 file alone has 311 distinct game keys with 23 median rows each.
- **Trap documented**: the raw roster files ALSO contain rows for (i) All-Star games — 20 of 21
  ASG seasons 2002–2026 (EAST/WEST/USA/Team-X formats) — and (ii) the **2018-08-03 forfeited game
  `401018942`** (WAS vs LVA, never played, zero `starter` flags). All are excluded by the lane A
  filter law (SPEC §4) via the mandatory inner join to the universe. Any successor that skips the
  filter law would ingest an unplayed game's roster.

## 4. Per-season roster coverage vs the filter-law game universe (2002–2026)

Universe = lane A filter law (ESPN `status_type_state=='post'`, drop Forfeit/Postponed, drop
All-Star alias rows, drop TBD; SPEC §4). "cov" = universe games with roster rows; "zero-st" =
games whose roster rows carry NO `starter=True` at all; "st≠10" = games with starter count ≠ 10
(count in parens).

| season | roster rows | roster games | universe games | cov | missing | teams | athletes | rows/game med | games w/ 10 starters | zero-st | st≠10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2002 | 5,936 | 270 | 271 | 270 | 1 | 16 | 208 | 22 | 263 | 7 | 0 |
| 2003 | 5,582 | 255 | 255 | 255 | 0 | 14 | 180 | 22 | 254 | 1 | 0 |
| 2004 | 5,194 | 237 | 237 | 237 | 0 | 13 | 167 | 22 | 237 | 0 | 0 |
| 2005 | 5,266 | 238 | 238 | 238 | 0 | 13 | 184 | 22 | 236 | 2 | 0 |
| 2006 | 6,054 | 255 | 257 | 255 | 2 | 14 | 187 | 24 | 254 | 1 | 0 |
| 2007 | 5,947 | 242 | 242 | 242 | 0 | 13 | 176 | 25 | 242 | 0 | 0 |
| 2008 | 6,400 | 258 | 259 | 258 | 1 | 14 | 199 | 25 | 257 | 1 | 0 |
| 2009 | 5,326 | 242 | 242 | 242 | 0 | 13 | 163 | 22 | 240 | 2 | 0 |
| 2010 | 4,832 | 220 | 220 | 220 | 0 | 12 | 144 | 22 | 220 | 0 | 0 |
| 2011 | 4,931 | 224 | 224 | 224 | 0 | 12 | 146 | 22 | 223 | 1 | 0 |
| 2012 | 4,934 | 223 | 223 | 223 | 0 | 12 | 152 | 22 | 221 | 2 | 0 |
| 2013 | 4,939 | 221 | 221 | 221 | 0 | 12 | 151 | 22 | 221 | 0 | 0 |
| 2014 | 5,204 | 222 | 222 | 222 | 0 | 12 | 156 | 24 | 222 | 0 | 0 |
| 2015 | 5,357 | 225 | 225 | 225 | 0 | 12 | 163 | 24 | 225 | 0 | 0 |
| 2016 | 5,199 | 219 | 220 | 219 | 1 | 12 | 163 | 24 | 218 | 0 | 1 (11) |
| 2017 | 5,161 | 219 | 219 | 219 | 0 | 12 | 164 | 24 | 218 | 0 | 1 (9) |
| 2018 | 5,188 | 221 | 220 | 220 | 0 | 12 | 161 | 24 | 220 | 1 (forfeit) | 0 |
| 2019 | 5,188 | 220 | 220 | 220 | 0 | 12 | 162 | 24 | 220 | 0 | 0 |
| 2020 | 3,544 | 147 | 147 | 147 | 0 | 12 | 153 | 24 | 146 | 0 | 1 (9) |
| 2021 | 4,602 | 210 | 210 | 210 | 0 | 12 | 159 | 22 | 210 | 0 | 0 |
| 2022 | 5,285 | 240 | 240 | 240 | 0 | 12 | 168 | 22 | 240 | 0 | 0 |
| 2023 | 5,774 | 261 | 261 | 261 | 0 | 12 | 164 | 22 | 261 | 0 | 0 |
| 2024 | 5,905 | 263 | 263 | 263 | 0 | 12 | 157 | 23 | 263 | 0 | 0 |
| 2025 | 7,115 | 311 | 311 | 311 | 0 | 13 | 185 | 23 | 311 | 0 | 0 |
| 2026* | 8,271 | 341 | 341 | 341 | 0 | 15 | 245 | 24 | 341 | 0 | 0 |

*2026 as-of-snapshot (season in progress). **Missing-roster games: 5 total in 25 seasons**
(all listed with schedule detail in `measurements_r2.json → universe_games_without_roster_detail`):
2002-06-08 UTA–CHA; 2006-05-23 and 2006-05-26 CHI (expansion Sky's first week); 2008-05-23 ATL–DET
(expansion Dream's second game); 2016-09-28 LAS–CHI **playoff semifinal G1**. None is a team's
game 1, so opening-roster reads are unaffected (§5). **Duplicate (game, team, athlete) rows: 0
across all 25 seasons.** Starter-flag anomalies: 17 zero-starter games + 3 games with 9/9/11
starters = 20 games ≈ 0.33% (game_ids in `measurements_r2.json`); starter-SET derivation is
impossible for exactly those games — membership derivation is not.
Team-key note: the ESPN abbreviation artifact reproduces in roster files — **every** Detroit Shock
row 2002–2009 is labeled `TUL` (e.g. 2002: 356/356, 2009: 432/432); joins must use
`team_display_name` → franchise key (GAME_UNIVERSE_SPEC §2); measured 0 unmapped display names
after the ASG drop, across all 25 seasons.

## 5. Opening-roster (game-1) availability — the W-H2 v1 input

Definition: team i's first filter-law game of season T (by `tip_utc`, GAME_UNIVERSE_SPEC §3).

- **100% of team-seasons 2002–2026 have a game-1 roster with ≥10 rows** (measured per season:
  `opening_roster_game1` in `measurements_r2.json`; e.g. 2003: 14/14, 2016: 12/12, 2025: 13/13,
  2026: 15/15 as-of-snapshot). Minimum game-1 rows per game across all seasons: 10.
- Cross-era consistency: game-1 rows are normal per-game rows (10 starters where flags exist),
  not aggregates — same schema, same key law as every other game.

## 6. W-H2 input sufficiency — computable-continuity fraction per season T

Two inputs: (i) **season-T opening roster** (game-1 membership, §5) and (ii) **season-(T−1)
player minutes** (`player_box` rows with `minutes > 0`). Sufficiency for (ii) measured as the
franchise's T−1 box game-coverage ratio = box games with rows / franchise universe games.

**Player_box coverage gradient (the binding constraint):**

| T−1 season | box games w/ rows / universe | notes |
|---|---|---|
| 2002 | 16 / 271 | **STUB**: 344 rows, `minutes` 100% `--` → no minutes exist in this asset |
| 2003 | 194 / 255 | 61 games missing |
| 2004 | 214 / 237 | 23 missing |
| 2005 | 229 / 238 | 9 missing |
| 2006–2008 | 240–255 / 242–259 | 2–7 missing |
| 2009–2025 | complete (0 missing) | |
| 2026* | 341 / 341 | as-of-snapshot |

*in-progress. Box schema: 2002 = old short schema (`min`, … — the stub); 2003+ = modern (`minutes` numeric);
`reason` from 2012; DNP flags 0 before 2012 (irrelevant for minutes).

**Computable-continuity fraction by season T** (non-expansion team-seasons; expansion
team-seasons — CHI 2006, ATL 2008, GSV 2025, POR/TOR 2026 — start at league mean in both arms per
the B-lane law and are excluded from the denominator):

| T | roster gate (game-1 roster present) | prior-season box ratio (min team) | minutes-weighted computable ≥0.8 ratio | minutes-weighted computable at 1.0 | missing at ≥0.8 |
|---:|---:|---:|---:|---:|---|
| 2003 | **100% (14/14)** | 0.00 | **0% (0/14)** | 0 | all 14 (2002 box stub) |
| 2004 | 100% (13/13) | 0.62 | **38.5% (5/13)** | 0 | CON HOU LAS LVA MIN NYL PHO WAS |
| 2005 | 100% (13/13) | 0.74 | **92.3% (12/13)** | 1 | NYL |
| 2006 | 100% (13/13) | 0.88 | **100% (13/13)** | 3 | — |
| 2007 | 100% (13/13) | 0.94 | 100% (13/13) | 10 | — |
| 2008 | 100% (13/13) | 0.97 | 100% (13/13) | 9 | — |
| 2009 | 100% (13/13) | 0.94 | 100% (13/13) | 3 | — |
| 2010 | 100% (12/12) | 1.00 | 100% (12/12) | 12 | — |
| 2011–2025 | 100% (12–13/12–13) | 0.97–1.00 | 100% every season | 8–12/12–13 | — |
| 2026* | 100% (15/15) | 1.00 | 100% (13/13 non-exp) | 13 | — |

- **B-lane gate ("≥ ~90% of team-seasons 2003+ present") measured: 23/23 seasons PASS on the
  roster gate** (roster coverage is 100% in every season 2003–2025).
- **Earliest adequate season, by continuity input:**
  - roster-membership (game-1) continuity or games-played-share continuity: **T = 2003**
    (2002 rosters are complete even though 2002 box is a stub).
  - **minutes-weighted continuity (the exact W-H2 operationalization): T = 2006** (first season
    with 100% of teams at ≥0.8 prior-box coverage; 2005 is marginal at 92.3%, 2004 fails at
    38.5%, 2003 impossible). Every team at full 1.0 box coverage is guaranteed from **T = 2010**.
- Sensitive-window capacity at the T≥2006 window (B-lane shape: effects concentrate in the first
  ~8–10 games of each season): ~60–70 games/season × ~20 folds ≈ 1.2–1.4k boundary-window games,
  inside the B-lane's stated resolvable range (~1.4–1.6k for 2003+; the paired-correlated-arm CI
  machinery is unchanged).

## 7. Retro-fill and data-quality hazards (measured)

1. **Duplicates: 0** `(game_id, team, athlete)` duplicate rows in 25 seasons.
2. **Roster rows with NO same-team-season box row** (the dispatch's retro-addition probe):
   2002: 1,061 rows (412 starter) — **fully explained by the 2002 box stub** (rosters cover 270
   games, box only 16; e.g. Houston Comets starters Thompson/Swoopes/Arcain have roster rows and
   no box rows because their games' box rows do not exist anywhere in the asset);
   2003: 10 rows (4 starter, e.g. Cynthia Cooper); 2004: 1; 2005: 9; **2006–2026: 0**.
   → **No measurable retro-addition signal from 2006 onward; 20 stray rows total in 2003–2005
   (≈0.1%).** The residual check direction (box-earlier-than-roster) below confirms the roster
   file's failure mode is under-inclusion, never retro-addition.
3. **First-appearance ordering** (roster-first game ordinal minus box-first ordinal, per player
   with minutes>0): median 0 in every season 2004–2026; 0 players with roster-earlier-by->10 in
   any season except 2013 (5) and 2016 (18). The >10 clusters are **roster UNDER-inclusion**
   (box shows the player playing many games before the roster file first lists them — e.g.
   Betnijah Laney CHI 2016 box-first game 1 vs roster-first game 27), affecting 23 players across
   2 seasons (game-level detail in `measurements_r2.json → first_appearance_gap_gt10_detail`).
   Consequence, bounded: game-1 membership reads may miss such players for CON/IND/NYL 2013 and
   5 teams 2016 — a slight continuity understatement for those team-seasons; carry as structural
   missingness note, not zeros. 2003's −3 median gap is the 61-game box gap, not a roster defect.
4. **Starter-flag anomalies** (§4): 20 games (≈0.33%), all identified by id. The 2018 forfeit is
   one of them (legitimately flagless — never played).
5. **Cross-source starter identity, 2025 (full season, dispatch asked ≥20 games):**
   `game_rosters_2025` vs `player_box_2025` — **311/311 games; 622/622 team-games derive exactly
   5 starters per side and the 5-name sets are IDENTICAL; 7,115/7,115 row-level `starter` flags
   agree; 0 disagreements.** The two assets encode the same game-day fact; roster rows are genuine
   per-game lists, not retro-assembled aggregates.
6. **DNP/starter trap (binding statement, from MECHANISMS_WNBA §5):** `starter`, `did_not_play`,
   `active`, `ejected`, `reason` are **post-game-recorded facts of THAT game** (2025 sample:
   starter 3,120; DNP 1,224 with free-text reasons). Fine as inputs to season-(T−1) derivation;
   **forbidden as same-season pre-game features** in any arm, any cycle — including the current
   game's own roster rows.

## 8. THE AS-OF LAW for the successor (verbatim, binding)

> **W-H2 CONTINUITY AS-OF LAW (WNBA-WINPROB-PREP-V1 successor, frozen by this audit):**
> 1. `continuity_i(T)` may consume ONLY facts of season T−1 games: (a) `espn_wnba_game_rosters`
>    rows of T−1 games, and (b) `espn_wnba_player_boxscores` `minutes` rows of T−1 games. Every
>    such row is a post-game fact of a strictly prior game; season T−1 precedes T's first tip; the
>    feature is therefore knowable before T's first tip **by construction**.
> 2. Season-T roster rows are NEVER inputs to T's own predictions. Membership only: `continuity_i(T)`
>    uses the NAME SET of team i's game-1 roster rows of season T (variant v1), or applies
>    continuity from game 2 with league-default carryover for game 1 (variant v2). Game-night
>    availability fields (`starter`/`did_not_play`/`active`/`ejected`/`reason`) of ANY season-T
>    game are forbidden as pre-game features; v1/v2 selection is train-internal (Lane C freezes).
> 3. All roster/box rows are inner-joined to the lane A filter-law universe (SPEC §4) before any
>    use — this alone removes the 21 All-Star game files and the 2018-08-03 forfeited game that
>    exist in the raw assets. Time ordering uses the canonical `tip_utc` law (SPEC §3).
> 4. Eligibility window (measured, not negotiable upward): minutes-weighted `continuity_i(T)`
>    only for **T ≥ 2006** (100% of non-expansion teams; 2005 marginal 92.3%; 2003–2004 excluded
>    or structural-missing — the 2002 box asset carries no minutes at all). A roster-share
>    continuity variant may start at **T = 2003**. 2026 counts are as-of-snapshot.
> 5. Franchise joins via `team_display_name` → lane A franchise keys; never ESPN abbreviations
>    (roster files label all Detroit rows `TUL` 2002–2009, measured). Expansion team-seasons start
>    at league mean in both arms. The 5 roster-missing universe games and the 20 starter-flag
>    anomaly games are handled as structural missing, never zeros.
> 6. Prior-season minutes of strictly prior games are post-game facts and allowed; nothing in this
>    law authorizes any current-game box/pbp/roster field as a pre-game feature.

## 9. Independence, scope, reproduction

- **Independence law**: WNBA data only. No NBA schedule, box, roster, parameter or verdict was
  read or used; every number above is measured from the WNBA corpus + the two WNBA release tags.
- No win-prob metric computed: counts, ratios and set-equality checks only.
- Reproduction:
  ```
  .venv/bin/python lanes/A_DATA/measure_r2_download.py espn_wnba_game_rosters game_rosters_ roster_audit
  .venv/bin/python lanes/A_DATA/measure_r2_download.py espn_wnba_player_boxscores player_box_ roster_audit
  .venv/bin/python lanes/A_DATA/measure_r2_roster.py     # read-only over corpus + roster_audit; rewrites measurements_r2.json
  ```
- Attribution (required on any use): "Data from SportsDataverse (wehoop), sportsdataverse-data
  release store, CC BY 4.0; underlying statistics sourced from ESPN WNBA API and stats.wnba.com."

## 10. What remains NOT_RUN / limitations

- **1997–2001: no rosters, no box** (ESPN assets start 2002) — continuity is structurally
  impossible there; unchanged from SPEC §8.
- 2002 minutes do not exist in any rights-cleared ESPN-side asset measured (box stub). If the
  successor ever needs T=2003 minutes-weighted continuity, it would need a different source —
  none identified in-corpus; treat as NOT_RUN, not inferred.
- 2026 is an in-progress snapshot (rosters 341/341 played games covered as of 2026-10-04 asset);
  final 2026 numbers will differ.
- The `espn_wnba_game_rosters`/`espn_wnba_player_boxscores` assets carry no publish timestamps;
  this audit does not claim row-level publication times — the PASS rests on the by-construction
  argument (§8), which is why the law above is written narrowly.
- GitHub could not provide digests for 2 pre-2025 box assets (API field absent); sizes verified
  against API metadata instead — no integrity ambiguity for the audit's numbers.
