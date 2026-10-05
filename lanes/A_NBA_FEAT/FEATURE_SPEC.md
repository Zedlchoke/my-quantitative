# FEATURE SPEC — NBA frozen player-feature table (Lane A_NBA_FEAT, WINPROB-PLAYERFEAT-PREP-V1)

Frozen definitions for `~/.my-quantitative-data/playerfeat-prep-v1/nba/features/`.
Feature construction ONLY — no outcome column exists in the table, no scored metric
is computed anywhere in this lane. Hypothesis families are the 3 pre-registered
groups of predecessor `lanes/A_NBA/FEATURE_PROPOSALS.md` (ancestry warning respected:
no calendar rest, no team win/loss form anywhere).

## 0. As-of law (PIT)

- Authoritative tip time = schedule corpus `game_date_time` parsed as UTC
  (`pd.to_datetime(..., utc=True, format='mixed')`). Measured on all 11 seasons:
  0 parse failures; `game_date_time` (local+offset) equals `start_date` (UTC) after
  UTC normalization on 14,254/14,254 schedule rows (100%, every season) — semantics:
  `game_date_time` is arena-local time with offset; `start_date` is the same instant
  in UTC. Predecessor worked example tip 2021-03-15T23:00Z for game 401307387
  reproduces from these bytes (PIT_AUDIT.md §2).
- **Every** feature for team-game G uses ONLY box rows of games with tip STRICTLY
  earlier (`<`, never `<=`) than G's tip. Same-game rows are never read by the
  builder for feature inputs (the target's own box rows are only committed AFTER
  the target row is emitted). Target-game DNP/starter/injury/active status is NOT
  used (NOT_RUN_PIT, predecessor law).
- Evidence columns embedded per row: `tip_utc`, `n_prior_games_used`,
  `asof_rule_version` (`asof_v1_strict_tip_utc`).

## 1. Universe and keys

- Seasons 2016–2026, ESPN **ending-year** labels (2016 = 2015-16 season; verified
  per season from bytes, COVERAGE_AUDIT.md).
- Target rows: one per (game_id, team side) for every PLAYED game — played =
  schedule `status_type_name == STATUS_FINAL` AND both scores present. 14,187
  played games → 28,374 rows. Play-in games (schedule `season_type=5`) that were
  played ARE emitted as targets (they are played games); they never enter any
  team's prior sequence.
- **Exhibition disclosure law (measured):** the played universe contains 19
  exhibition games (NBA All-Star formats + Rising Stars, all carrying
  `season_type=2` in the schedule; game list in
  `provenance/exhibition_games.txt`). Both sides of such games carry
  event-specific ESPN team ids (e.g. 31/32, 111353, 130579–130581, 132374/132375),
  NOT franchise ids. Franchise ids are the ESPN league-46 ids {1..30}, measured
  stable across all 11 seasons (franchise team-games per season 64–107; exhibition
  entities 1–8, so the ≥40 team-games classifier has a wide deterministic margin).
  These 19 games stay in the table (dispatch law: every played game) and are
  flagged `is_exhibition=1` (pre-game derivable from the team ids). Because BOTH
  sides are event ids, exhibition games can never enter a franchise team's prior
  sequence; their own later event games (2025/2026 multi-game formats) compute
  scalars only from the same event's earlier games — contained and disclosed.
- `team_id`/`opponent_id`/`is_home` from the schedule row (`home_id`/`away_id`);
  `season`, `season_type` (target's own; pre-game calendar metadata) likewise.
- No outcome columns: no scores, no winner flags, no margin, nothing derived from
  the target game's result. Column whitelist asserted in `build_features.py --selftest`.

## 2. Prior pool per (season, team)

A game h is a PRIOR of target G for team t iff all hold:
1. h in same season label; 2. h played (status final + scores); 3. h `season_type != 5`
(play-in excluded from priors AND from the team-game sequence); 4. tip(h) < tip(G)
strictly; 5. (for stat aggregation) h has "usable box rows" for t — rows with
`athlete_id` NOT NULL and `did_not_play == False`. Identity-less rows (NULL
`athlete_id`, all 33 in 2026) and DNP rows are excluded from every stat aggregate;
counts reported in COVERAGE_AUDIT.md.

Per prior game h and team t, from usable rows:
- `minutes_filled` = `minutes` with NaN → 0.0 (predecessor §6: NaN minutes of a
  non-DNP row = played <1 min; DNP rows excluded entirely).
- `mass(h,t)` = Σ minutes_filled; `top5_share(h,t)` = Σ minutes of the 5 largest
  minutes_filled rows / mass (ties broken by ascending `athlete_id`; 0.0 if mass=0).
- per-player: `points`, `minutes_filled` for the ppm aggregates.

`team_games_so_far` = number of prior team-games in the sequence (rules 1–4,
regardless of box presence). `n_prior_games_used` = number of those priors with
usable box rows (the ones that entered the aggregates). `feature_neutral = 1` iff
`n_prior_games_used < 5` OR `b_form_top3_n == 0`; neutral rows carry 0.0 in ALL
group scalars.

## 3. Measured degeneracy law and Group A scalars (the substitution)

Measurement (all 11 seasons, `provenance/degeneracy_measurements.txt`): raw
team-game minutes mass `mass(h,t)` is constant-by-construction up to OT and ≤~1
minute accounting noise — per season mean 240.3–242.0, 39.6–42.3% of team-games
exactly 240.0, ~95% within [239, 266] (= 240+25k ± noise), std 6.3–18.4 driven
almost entirely by the OT indicator mix. The predecessor's warned scalar
`mass_k = mean prior-5 mass` (and the difference `mass_k − mass_stdate`, whose
carrier inherits the same 25·OT steps) is therefore **degenerate as a level**.
Also measured and rejected: OT-normalized mass `mass/(240+25·OT)` ≈ 1 ± 0.005 by
construction (even more degenerate; drops the only real variation). HHI measured
(mean 0.113–0.117, std 0.012–0.013) — informative but highly correlated with
top5_share; kept OUT of the frozen table to respect the 2-scalar cap (recorded
here as the documented alternative).

**Frozen Group A scalars (2, non-degenerate carriers of the same
rotation-intensity hypothesis family):**

- `a_top5_share_k5` = mean of `top5_share(h,t)` over the last ≤5 priors with
  usable rows (level of rotation concentration).
- `a_load_top5_k5` = `a_top5_share_k5` − (mean of `top5_share(h,t)` over ALL
  priors with usable rows) — the "load vs own season-to-date norm" deviation
  carried by the non-degenerate share instead of the degenerate mass level.

Hypothesis family unchanged (Group A: rotation-intensity/load deviations);
only the carrier is substituted, per the measured law, and recorded here.

## 4. Group B scalar (1 + count)

- Player season-to-date state (all priors with usable rows, same team):
  `tot_min`, `tot_pts`, plus each player's last ≤5 per-game
  `ppm = points/minutes_filled` (games with minutes_filled=0 contribute ppm 0.0).
- Top-3 set: players with `tot_min ≥ 24` (minimum-minutes guard, frozen), ranked
  by (`tot_min` desc, `athlete_id` asc), take 3.
- Per player: `form = mean(last ≤5 ppm) − (tot_pts/tot_min)` (minutes-weighted
  season-to-date baseline).
- `b_form_top3` = mean of `form` over the top-3 set; `b_form_top3_n` = set size
  actually averaged (1..3; 0 triggers the neutral rule).

## 5. Group C scalars (2)

- Same top-3 set as Group B (top-1 = its first member).
- **Trade guard (frozen):** an absence of player p in prior game h counts ONLY if
  p has a usable row for the SAME team in at least one of the 10 team-games of t
  immediately preceding h (so a just-traded-in player's history, or a long-gone
  player's stale DNP scaffold, can never fabricate an absence).
- `c_abs_out` = 1 iff some top-3 player has a `did_not_play=True` row in either of
  the 2 most recent prior team-games AND passes the trade guard for that game.
- `c_abs_streak` = number of consecutive most-recent prior team-games missed
  (DNP=True + guard) by the top-1 player; the walk stops at the first game where
  he has a usable row (played) or no row at all (no evidence, incl. box-less
  games). 0 if top-1 undefined or he played the most recent prior game.
- Target-game DNP/injury/active: NOT used (NOT_RUN_PIT).

## 6. Determinism and outputs

- Fixed ordering: rows sorted by (`season`, `tip_utc`, `game_id`, `team_id`).
- No run timestamps inside data files; run metadata lives in
  `FEATURE_TABLE_MANIFEST.{md,json}`. CSV.gz written with mtime=0 (byte-stable).
- Parquet + csv.gz at `~/.my-quantitative-data/playerfeat-prep-v1/nba/features/`,
  sha256 + row counts pinned in `FEATURE_TABLE_MANIFEST.md`.
- `build_features.py --selftest` asserts: leak guards on 3 sample games (strict
  tip inequality, target absent from inputs, reproduction of the predecessor MIL
  prior-5 example 401307387 → mean mass 239.4 over exactly the 5 documented
  game_ids), 0 duplicate (game_id, team_id), neutral-rule behavior both ways,
  trade-guard property + worked example, column whitelist (no outcome columns),
  and on-disk byte equality with the in-memory build. Non-zero exit on failure.

## 7. Column list (frozen, in order)

`game_id` i64 · `season` i64 · `season_type` i64 (target's own) · `team_id` i64 ·
`opponent_id` i64 · `is_home` i8 · `is_exhibition` i8 · `tip_utc` ts[UTC] ·
`team_games_so_far` i64 · `n_prior_games_used` i64 · `feature_neutral` i8 ·
`a_top5_share_k5` f64 · `a_load_top5_k5` f64 · `b_form_top3` f64 ·
`b_form_top3_n` i64 · `c_abs_out` i8 · `c_abs_streak` i64 ·
`asof_rule_version` utf8.
