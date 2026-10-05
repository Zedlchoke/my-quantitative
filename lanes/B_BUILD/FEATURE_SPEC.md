# FEATURE_SPEC — B_BUILD · NFL-PLAYERFEAT-PREP-V1 · FROZEN v1.0.0 (2026-10-05)

Frozen before the table build (spec-first law). Exact scalars per (game_id, team side).
PREP only: strictly prior-game aggregates of player stats/snaps. NO outcome columns, NO
target-game status fields (target-game injury/active/DNP/starter status = **NOT_RUN_PIT**, a
LAW inherited from the predecessor D_VERIFY adjudication and restated here). No win-prob /
calibration-on-outcomes / betting vocabulary anywhere in this cycle.

## 0. Inputs (sha256-pinned, verified 6/6 at build start)

| input | path | sha256 (prefix) |
|---|---|---|
| stats_player_week_2024 | `~/.my-quantitative-data/playerdata-prep-v1/nfl/raw_stats_player/` | `847569d1…55c1` |
| stats_player_week_2025 | 〃 | `2a461bec…ff10` |
| stats_player_week_2026 | 〃 | `49bc644e…6179` |
| snap_counts_2025 | `~/.my-quantitative-data/playerdata-prep-v1/nfl/raw_snap_counts/` | `47220218…ce20` |
| snap_counts_2026 | 〃 | `fae0627d…8273` |
| players.parquet (crosswalk) | `~/.my-quantitative-data/playerfeat-prep-v1/nfl/raw_players/` | `485b1980…885e2` |
| games.csv | `~/.my-quantitative-data/nfl-ng-prep-v1/raw_schedules_r1_20261005/` | measured at manifest time |

Mismatch vs predecessor manifests ⇒ BLOCKED_DATA (stop). All 6 verified OK 2026-10-05.

## 1. Row universe and keys

- One row per **(game_id, side)**, side ∈ {away, home}, for **played games with weekly-stats
  data**: game_id present in the three stats_player_week files AND in games.csv (re-measured:
  0 orphan stats game_ids). Seasons 2024, 2025, 2026 → 285 + 285 + 63 = **633 games → 1,266
  rows**.
- The 209 future 2026 games have no stats rows → **no rows by design** (disclosed in the
  manifest; earliest future 2026 kickoff re-measured 2026-10-06T00:15Z).
- Key columns: `game_id, season, week, game_type, side, team, opponent`
  (team = away_team/home_team by side; opponent = the other side).
- NaN-player placeholder rows in stats (1 per week: 22 in 2024, 22 in 2025, 4 in 2026 = 48
  rows) are **excluded** before any aggregation (inherited predecessor law).

## 2. As-of law (applies to every feature)

- `kickoff_utc` = games.csv `gameday` + `gametime`, localized **America/New_York**, converted
  to UTC (canonical predecessor law). Stored ISO-8601 `YYYY-MM-DDTHH:MM:SSZ`.
- **Kickoff strict inequality**: a game is prior iff `kickoff_utc(prior) < kickoff_utc(target)`
  (strict `<` on the UTC timestamp, never on gameday). Same-day earlier games count as prior;
  same-kickoff is never prior.
- **Same-season scope**: prior pools are restricted to the target's `season` (REG+POST both
  eligible if in-season in the corpus). No cross-season carry-in (season openers are
  no-prior rows by construction; this is the frozen neutral rule).
- `n_prior_games_used` = number of the team's same-season prior games in the stats corpus
  (the G1/G2 as-of support). `asof_rule_version = "asof-1.0.0-nfl-playerfeat-prep-v1"`
  (constant column, embedded in every row).
- Prior-game order: ascending `kickoff_utc`, tie-break ascending `game_id` (deterministic;
  a team cannot play twice at one kickoff).

## 3. Bye weeks and rest

- `rest_days` = (target kickoff_utc − kickoff_utc of the team's most recent same-season prior
  game) / 86400 s, float; **NaN** if no prior game. A bye week is simply "no game that week":
  the prior-k windows skip it automatically (the most recent k priors are the k games before
  the bye), and `rest_days` after a bye is ≈12–14 d instead of ≈6–8 d. Bye is never an
  imputed or synthetic row. Fixture frozen for selftest: KC 2024 (bye wk6) → target
  `2024_07_KC_SF` window = {2024_05_NO_KC, 2024_04_KC_LAC, 2024_03_KC_ATL}, rest ≈ 12.8 d.

## 4. G1 — QB form / availability (source: stats_player_week, position == 'QB', team side)

Per target row, with P = team's same-season prior games (kickoff-ordered), W_k = last k games
of P, n_used(k) = min(k, |P|). Scalars per k ∈ {3, 5} (sums over ALL QB rows of the team in
the window; passing_epa NaN occurs only when attempts = 0 (measured: 76 QB rows, none with
attempts > 0), so NaN→0 in sums is exact):

- `qb_yds_k{k}` = Σ passing_yards · `qb_td_k{k}` = Σ passing_tds ·
  `qb_int_k{k}` = Σ passing_interceptions · `qb_att_k{k}` = Σ attempts ·
  `qb_epa_k{k}` = Σ passing_epa (NaN→0)
- `qb_ypa_k{k}` = qb_yds_k{k} / qb_att_k{k} (NaN if att = 0) ·
  `qb_epa_pa_k{k}` = qb_epa_k{k} / qb_att_k{k} (NaN if att = 0)
- `qb_yds_form_k{k}` = qb_yds_k{k}/n_used(k) − qb_yds_std_pg ·
  `qb_epa_form_k{k}` = qb_epa_k{k}/n_used(k) − qb_epa_std_pg

Season-to-date (STD) per-game means over the full P (NaN if |P| = 0):
`qb_yds_std_pg` = Σyds(P)/|P| · `qb_epa_std_pg` = Σepa(P)/|P|.

Availability is expressed by n_prior_games_used + window flags (no team-level QB-identity
continuity column in v1 — snap_counts has no 2024 coverage; documented limitation, not a
silent omission).

## 5. G2 — Skill-player usage mass (stats_player_week, position_group ∈ {WR,RB,TE})

Per target row, over W_k: player usage u = Σ(targets + carries) by player_id.

- `skill_top3_share_k3` = Σ(top-3 u)/U_tot, k=3 · `skill_top5_share_k5` = Σ(top-5 u)/U_tot, k=5
- `skill_hhi_k3` = Σ (u/U_tot)² over all skill players in W_3 ·
  `skill_usage_pg_k3` = U_tot(k=3) / n_used(3)
- Top-N tie-break: (−u, player_id) ascending — deterministic.
- U_tot = 0 → NaN + `flag_g2_zero_usage` = 1 (never share-on-zero).

## 6. G3 — Absence proxy (snap_counts 2025–2026 via crosswalk)

Per target row, PS = team's same-season prior games **present in the snap corpus**
(kickoff strict inequality; kickoffs from games.csv by game_id). `g3_n_snap_prior_games` =
|PS|. Window = last min(3, |PS|) games of PS.

- Canonical player identity: snap `pfr_player_id` → crosswalk `pfr_id` → `gsis_id`.
- **pfr-null rule (frozen): EXCLUDE.** Snap rows whose `pfr_player_id` is null OR unresolved
  via the crosswalk are excluded from the candidate pool (they cannot be tied to the
  stats-side canonical identity; tracking them across games would fabricate absence). The
  exclusion is disclosed: `flag_g3_pfr_null_excluded` = 1 iff ≥1 excluded row belonged to
  this team's G3 window. Measured unresolved cohort (whole files): 2025 {AndeAl01, CartNa00,
  HallGa01, JohnIs03, OkoyCJ00, WhitCo05}, 2026 {AndeAl01, OkoyCJ00, WhitCo05}
  (WhitCo05 = Cody White, crosswalk gsis 00-0035891 has pfr_id NULL — selftest canary).
- Pool per (team, window): total snaps s = Σ(offense_snaps + defense_snaps) by resolved
  player over the window; **top-5** by (−s, gsis_id).
- `present` = s > 0; window mean m = s / n_w (n_w = window length; zeros included —
  availability-adjusted by design).
- `g3_top5_absent_share_recent` = (#top-5 players with recent-game snaps < 0.5·m AND
  present) / (#present top-5); NaN if no present player. n_w = 1 ⇒ 0.0 by construction
  (recent game IS the mean) — documented, not a bug.
- `g3_top5_newly_absent_count` = #top-5 players with recent-game snaps = 0 AND present.
- |PS| = 0 → all G3 values NaN + `flag_g3_no_snap_prior` = 1 (all 2024 rows; 2025 W1).
- **In-game-injury lag (documented by law)**: a player injured mid-game still logs that
  game's snaps/production, so "absent in the most recent prior game" conflates true absence
  with in-game injury in the *prior* game. The proxy is deliberately lagged and noisy; it
  must not be read as target-game availability (NOT_RUN_PIT).

## 7. Neutral rules and flags (int8 0/1, every row)

- `flag_no_prior_in_corpus` (|P| = 0): G1/G2 all NaN, rest_days NaN. G3 governed separately
  by `flag_g3_no_snap_prior`.
- `flag_g1_window_truncated_k3` / `flag_g1_window_truncated_k5` (|P| < k): windows computed
  over n_used < k games (still ≥1 prior; disclosure, not neutrality).
- `flag_g2_zero_usage`, `flag_g3_no_snap_prior`, `flag_g3_pfr_null_excluded` as above.
- NaN means "not computable", never 0 (except documented G3 n_w=1 case). Zero is only ever a
  measured zero.

## 8. Window disclosure (measured, restated)

Stats corpus on disk = 2024–2026 (2026 in-season, weeks 1–4; snap 2026 weeks 1–4, 2025 full
season). First game-dates each group is computable with ≥1 prior game: G1/G2 — first 2024
week-2 team-game; G3 — first 2025 week-2 team-game (2024 has no snap corpus ⇒ G3 NaN for all
2024 rows). Full per-season coverage in COVERAGE_AUDIT.md / FEATURE_TABLE_MANIFEST.md.

## 9. Output, determinism, bans

- Parquet `features/nfl_playerfeat_table_v1.parquet` under
  `~/.my-quantitative-data/nfl-playerfeat-prep-v1/`; rows sorted by
  (kickoff_utc, game_id, side); index=False; pyarrow default (snappy).
- Determinism: double-run byte-identical parquet sha256 (selftest).
- Column whitelist = keys (7) + as-of (4) + G1 (20) + G2 (4) + G3 (3) + flags (6) = **44
  columns**. Banned vocabulary (score/result/winner/margin/spread/moneyline/total/odds/win/
  lose/prob…) rejected by selftest scan. No wall-clock timestamps in the table.
