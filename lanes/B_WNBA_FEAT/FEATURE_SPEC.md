# FEATURE SPEC — Lane B_WNBA_FEAT · WINPROB-PLAYERFEAT-PREP-V1 · 2026-10-05

FROZEN definitions for the WNBA player-feature table built by `build_features.py` from the
read-only corpus `~/.my-quantitative-data/wnba-prep-v1/roster_audit/` (2002–2026,
hash-verified), ESPN schedules `~/.my-quantitative-data/wnba-v1/raw/espn_schedules/`
(game universe), and the 20-key lineage table `~/.my-quantitative-data/wnba-prep-v1/
team_key_table.csv`. FEATURE CONSTRUCTION ONLY — no scored computation, no win-prob or
calibration metric anywhere in this lane; calibration/forecasting vocabulary only.

Groups A/B/C follow the predecessor proposals
(`winprob-playerdata-prep-v1/integration/lanes/B_WNBA/FEATURE_PROPOSALS.md`); W-H2
(`wnba-winprob-prep-v1/integration/lanes/B_MECHANISMS/MECHANISMS_WNBA.md`) is continuity
REFERENCE ONLY — never re-derived here.

## 0. Output row law

- One row per (ESPN `game_id`, team side ∈ {home, away}) for **every** game of the re-derived
  ESPN-side universe 2002–2026 (5,988 games → **11,976 rows**; row exists even when all
  features are neutral). Sorted by (`game_id`, `team_side`); deterministic.
- Key columns: `game_id` (string), `season`, `team_side`, `team_id` (ESPN, stable franchise
  entity), `team_display_name`, `franchise_key` (lineage table), `tip_utc`
  (`%Y-%m-%dT%H:%M:%SZ`, scheduled fact), `is_team_game1` (bool), `asof_rule_version`
  (constant `tip_utc_strict_lt_v1`).
- **NO outcome columns anywhere.** Column whitelist is asserted in `--selftest`
  (`EXPECTED_COLUMNS`); no column name contains score/winner/outcome/result/margin.
- **Determinism law:** no wall-clock/run timestamps inside the table. The `tip_utc`,
  `b{k}_window_first_tip`, `b{k}_window_last_tip`, `c_recent_game_tip` columns are REQUIRED
  as-of metadata (scheduled facts), not run timestamps — they carry the audit trail of the
  strict-inequality join. Measured: two independent full builds produce the identical
  parquet sha256 `ceaf10ba33e705b9569a11cec2aa33e1875e372c35d643ed5d80d5e757ffc7bf`
  (826,415 bytes).

## 1. As-of law (frozen, `tip_utc_strict_lt_v1`)

`tip_utc := pd.to_datetime(espn_schedule.date, utc=True, format="ISO8601")`.
For a target game G, **every** input game must satisfy `tip_utc(input) < tip_utc(G)`
(strict inequality). Windows for Groups B and C are confined to the **same season** as G
(frozen decision: season-start games are neutral by construction, consistent with Group C's
"trailing-season baseline" law; no cross-season pooling). Group A uses the strictly prior
SEASON (s−1) wholesale (§2). The law is enforced in construction AND asserted per row in
`--selftest` (max window tip strictly < row tip; 0 violations across 11,976 rows).

## 2. Group A — roster continuity `c_i(s)` (W-H2 linkage, v2 as-of law)

`c_i(s)` = minutes-weighted share of team i's PRIOR-SEASON (s−1) player-minutes attributable
to players on i's season-s opening roster.

- Prior-season minutes: sum of `player_box.minutes` (numeric `m`; nulls = non-players,
  excluded) over the franchise's athletes in season **s−1**, restricted to UNIVERSE games,
  aggregated at FRANCHISE level (a relocation keeps continuity: UTA 2002 → SAN 2003–2017 →
  LVA 2018+ all under franchise `LVA`; DET 2002–2009 → TUL 2010–2015 → DAL 2016+ all under
  `DAL`).
- Opening roster: distinct `athlete_id`s on the team's game-1 sheet in `game_rosters` of
  season s (game 1 = earliest-tip universe game of that team-season; tie-break lexicographic
  `game_id`). All rows of the sheet count as membership (no starter/DNP/active semantics —
  those are post-game facts, §6).
- `c = (Σ prior minutes of roster athletes) / (Σ prior minutes of all franchise athletes)`.
- **v2 as-of law (frozen, the only defensible default):** the value is emitted only for games
  with `tip_utc` STRICTLY greater than the team's game-1 tip. The game-1 row itself (and any
  same-tip row) is neutral with reason `game1_v2_not_usable`. **v1 (opening roster applied to
  game 1 or all season) = NOT_RUN_PIT, restated** — the asset carries no publish timestamps.
- Eligibility gates (in precedence order; all neutral-value + reason-flag otherwise):
  1. `expansion_no_prior` — packet/W-H2 expansion law: CHI 2006, ATL 2008, GSV 2025,
     TOR 2026, POR_PDX 2026 (+ every 2002 team-season = `no_prior_in_corpus`; the corpus
     starts 2002). Neutral in BOTH arms; these team-seasons contribute no continuity
     contrast. NOTE: the lineage table merges Portland 2026 under `POR_PDX` (with the
     2000–2002 Fire); the expansion law nonetheless forces neutral — a 24-year gap is a new
     franchise entity in the world, and the packet names TOR/PDX 2026 expansion seasons.
  2. `no_prior_season_s1` — franchise absent in exactly s−1 (none occurred beyond the lists
     above).
  3. `prior_minutes_floor_pre2013` — packet minutes-quality floor: prior season s−1 < 2013
     carries degraded minutes (2003–2008 backfill era team-minute totals are systematically
     incomplete; see COVERAGE_AUDIT §3) ⇒ continuity neutral for s ≤ 2013. Usable c starts
     season **2014** (5,907 computed rows, 2014–2026).
  4. `prior_coverage_below_90pct` — prior-season game coverage < 90% (belt-and-braces; all
     2013+ seasons are 100%).
  5. `no_game1_roster` — team's game-1 sheet missing/empty (0 cases occurred in eligible
     seasons).
  6. `game1_v2_not_usable` — v2 as-of law (§2 above).
- Companion columns: `continuity_prior_minutes_matched`, `continuity_prior_minutes_total`,
  `continuity_roster_size`. Measured range of computed c: [0.124, 0.974], median 0.619.
- 2020 Wubble handling: the 147-game 2020 season IS the prior season for 2021 continuity
  (a real season; disclosed as an outlier prior with fewer games). No special-casing.

## 3. Group B — minutes-mass / load (rolling prior k ∈ {3, 5}, BOTH computed)

For each k ∈ {3,5} independently, over the team's k most recent same-season strictly-prior
games that carry a `player_box` row for the team (`b{k}_games_played` = window size used;
computed only when it equals k):

- `b{k}_minutes_total` — pooled team minutes over the window (Σ per-player minutes; ESPN
  integer-rounded per player).
- `b{k}_minutes_hhi` — rotation concentration: Σ_p (min_p / total)² over players pooled in
  the window.
- `b{k}_top5_share` — share of pooled minutes from the top-5 minute-getters (ties broken by
  ascending `athlete_id`; deterministic).
- `b{k}_games_played` — games in the window (= k when computed).
- `b{k}_minutes_per_day` — rest-adjusted variant: pooled minutes ÷ calendar-day span of the
  window (`(last window tip date − first window tip date).days + 1`, UTC dates).
- `b{k}_window_first_tip` / `b{k}_window_last_tip` — as-of audit metadata.
- k-selection is DEFERRED to a future gated successor: both k are emitted, nothing selects
  between them in this lane.
- Eligibility gates (precedence): `coverage_floor_pre_2004` (season < 2004 — game-coverage
  floor ≥90% applies 2004+), `minutes_quality_floor_pre2013` (2004–2012), `no_prior_games`
  (0 prior same-season games with box rows), `insufficient_history` (1..k−1 games),
  `zero_minutes_window` (0 cases in eligible seasons).

## 4. Group C — top-player form + absence proxy

- **Top-5 rotation** (`c_top5_athlete_ids`, sorted `;`-joined): athletes with the largest
  pooled minutes over the team's trailing up-to-10 same-season strictly-prior games
  (`c_trailing_games_used`); gate ≥5 games else `insufficient_history`.
- **Form z-scores** `c_form_z_pts` / `c_form_z_reb` / `c_form_z_ast`: for each top-5 player,
  baseline = that player's own same-season prior games within the trailing window **with
  minutes > 0** (per-MINUTE production rates, era-stable); require baseline n ≥ 3 and
  population of rates with sd (ddof=1) > 0 else the player is skipped. Form window = the
  player's last 3 baseline games. z = (mean form rate − baseline mean) / baseline sd.
  Team-level value = minutes-weighted mean of valid player z's (weights = baseline minutes);
  require ≥3 valid players else `no_valid_player_z`.
- **Absence proxy** `c_absence_share`: expected_i = player's baseline mean minutes;
  actual_i = minutes in the most recent prior game (`c_recent_game_id`, `c_recent_game_tip`;
  0 if the player has no row there or null minutes); share = Σ max(0, expected_i − actual_i)
  ÷ Σ expected_i ∈ [0, 1]. 0.0 is a legitimate value (no top-5 minutes missing).
- **DNP era law:** the absence proxy uses the **null-minutes** reading uniformly in all
  eligible seasons (2013+). The `did_not_play` flag exists only 2012+ (measured: 0 True rows
  2002–2011; 180–1,461 rows/season 2012–2026) and is cross-checked in COVERAGE_AUDIT §4, but
  the proxy definition stays uniform for era comparability.
- **`active` / `reason` are UNUSABLE** (predecessor measured them defective: `active=True`
  covers ~half of both starters and bench in every era sampled; `reason` is the default
  string `COACH'S DECISION` on 2,220 of 2,220 starter rows in 2013). Restated: **no feature
  in this table reads `active` or `reason`**; `EXPECTED_COLUMNS` contains no such column.
- Eligibility gates: `minutes_quality_floor_pre2013` (<2013), `no_prior_games`,
  `insufficient_history` (<5 trailing games), `no_valid_player_z` (<3 valid players).

## 5. Join law (franchise + player)

- **Franchise joins ONLY via `team_key_table.csv`** (ESPN display names + stable ESPN
  `team_id`); raw ESPN abbreviations are NEVER a join key. Measured reason: ESPN labels ALL
  Detroit 2002–2009 rows `TUL` — the same abbreviation as Tulsa 2010–2015 — while `team_id`
  3 is one stable entity spanning DET/TUL/DAL (asserted in `--selftest`:
  `lineage_DAL_tree`); similarly UTA 2002 is `team_id` 15 while SAN/LVA is `team_id` 17, both
  under franchise `LVA` (`lineage_LVA_tree`). Every universe team-season maps to exactly one
  franchise; 0 unmapped, 0 multi-franchise violations.
- Player-level key: ESPN `athlete_id` (stable in-corpus), with a mandatory
  `drop_duplicates(['game_id','athlete_id'])`-equivalent guard: the corpus's single known
  duplicate (game `250521017`, athlete 30, one row under HOU one under SAS) cannot collide
  here because all aggregation is within (game_id, team_id).

## 6. PIT basis (summary; full audit in PIT_AUDIT.md)

PASS_CONSTRUCTIBLE inputs: strictly-prior aggregates over `player_box` keyed
(`game_id`, `team_id`) joined to schedule tips under strict inequality (worked example
reproduced from bytes, PIT_AUDIT §2). Opening-roster v1 = NOT_RUN_PIT (restated); v2 frozen.
Target-game roster/starter/DNP/active/reason/ejected: FORBIDDEN (never read). Same-game
(target-game) player stats: FORBIDDEN. No injury/availability feed exists — NOT_RUN_PIT.

## 7. Missing-data rules (frozen vocabulary)

`continuity_neutral_reason` / `b3_neutral_reason` / `b5_neutral_reason` / `c_neutral_reason`
are `""` iff the value is computed, else one of: `expansion_no_prior`, `no_prior_in_corpus`,
`no_prior_season_s1`, `prior_minutes_floor_pre2013`, `prior_coverage_below_90pct`,
`no_game1_roster`, `game1_v2_not_usable`, `coverage_floor_pre_2004`,
`minutes_quality_floor_pre2013`, `no_prior_games`, `insufficient_history`,
`zero_minutes_window`, `no_valid_player_z`. Invariant asserted per row: value NA ⇔ reason
non-empty (for every gated value column).
