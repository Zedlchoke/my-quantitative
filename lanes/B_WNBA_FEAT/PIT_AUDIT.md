# PIT AUDIT — Lane B_WNBA_FEAT · WINPROB-PLAYERFEAT-PREP-V1 · 2026-10-05

Doctrine §13 law carried: every field has event / effective / **available** times;
`available_time ≤ forecast time` must be EVIDENCED, else `NOT_RUN_PIT`. This lane builds
features only; no forecast, log loss, or any win-prob quantity was computed. The worked
examples below are aggregate-counting demonstrations from bytes.

## 1. Verdict table (restated + this lane's construction)

| input | available-time evidence | PIT verdict |
|---|---|---|
| prior-game / prior-season aggregates (player_box minutes, pts, reb, ast) | construction: only rows with `tip_utc` strictly < target tip enter; per-row assertion in `--selftest` (0 violations / 11,976 rows) | **PASS_CONSTRUCTIBLE** (worked examples §2–§3) |
| season-opening roster MEMBERSHIP from game-1 sheet, applied from game 2 onward (v2) | by construction the sheet is a strictly-completed prior game's record; no outcome information in membership | **PASS by construction (v2, frozen)** |
| season-opening roster applied to game 1 / all season (v1) | asset has no publish timestamps; cannot evidence pre-tip knowability | **NOT_RUN_PIT (restated; v2 is the only built variant)** |
| target-game `starter` / `did_not_play` / `active` / `ejected` / `reason` | post-game facts; `active`/`reason` additionally quality-barred (predecessor COVERAGE_SCHEMA §6) | **FORBIDDEN / NOT_RUN_PIT — never read by any feature** |
| `active` / `reason` fields, any use | measured defective (default `COACH'S DECISION` on all 2,220 starter rows 2013; `active=True` on ~half of starters AND bench in every era) | **UNUSABLE — restated; absent from the table schema** |
| injury / availability timeline | no dated archive exists in any rights-cleared corpus on disk | **NOT_RUN_PIT** |
| same-game (target game) player stats, any field | banned by doctrine | **FORBIDDEN** |

## 2. Worked example 1 (required reproduction): CON prior-5 team minutes, target `400445816`

Predecessor `measurements_b.json → pit_worked_example` (Connecticut Sun, franchise CON,
`team_id` 18, season 2013; target tip 2013-07-06T23:00Z) re-derived from bytes by
`build_features.py --selftest` — **all assertions PASS**:

| prior game_id | tip_utc | team minutes | in window (tips) |
|---|---|---:|---|
| 400445826 | 2013-06-14 23:30Z | 200 | k=3, k=5 |
| 400445854 | 2013-06-16 21:00Z | 201 | k=3, k=5 |
| 400445709 | 2013-06-23 19:00Z | 200 | k=3, k=5 |
| 400445771 | 2013-06-29 23:00Z | 199 | k=3, k=5 |
| 400445798 | 2013-07-02 23:00Z | 202 | k=3, k=5 |

Asserted in the built table row (`game_id=400445816`, `team_id=18`): `tip_utc =
2013-07-06T23:00:00Z`; `b5_minutes_total = 1002.0`; `b3_minutes_total = 601.0`;
`b5_window_last_tip = 2013-07-02T23:00:00Z` (strictly < target tip). Each of the 5 prior
tips is strictly less than the target tip; the 6th-most-recent game (tip 2013-06-11) is
correctly excluded. Verdict: **PASS_CONSTRUCTIBLE — reproduced exactly.**

## 3. Worked example 2: opening-roster v2 law (CON 2014)

Team 18 (CON), season 2014. Game 1 = `400539461` (tip 2014-05-16T23:00Z): continuity is
**neutral** (`continuity_c` NA, reason `game1_v2_not_usable`), `is_team_game1 = True`, while
the inputs are still recorded (`continuity_prior_minutes_matched = 2769`,
`continuity_prior_minutes_total = 6829`, `continuity_roster_size = 12` — prior season 2013
franchise minutes). Game 2 = `400539470` (tip 2014-05-18T21:00Z, strictly after game-1 tip):
`continuity_c = 0.405477 = 2769/6829`. Asserted for every team-season: game-1 rows are
ALWAYS neutral; the v2 flag appears ONLY on game-1 rows; continuity is never emitted for a
tip ≤ game-1 tip. Verdict: **v2 PASS by construction; v1 NOT_RUN_PIT restated** (game-1
membership is never applied to the game-1 forecast).

## 4. Worked example 3: expansion neutrality (GSV 2025)

Golden State Valkyries (franchise GSV), season 2025 — 46 rows (23 games), all with
`continuity_c` NA and reason `expansion_no_prior` in BOTH team sides (W-H2 law: expansion
team-seasons start at league mean in both arms, contributing no continuity contrast). Same
behavior asserted and PASSing for CHI 2006, ATL 2008, TOR 2026, POR_PDX 2026; all 2002
team-seasons carry `no_prior_in_corpus` (542 rows). Note: POR_PDX 2026 would find a lineage
prior (Portland Fire 2002) but the packet/W-H2 expansion law forces neutral — a 24-year gap
is a new franchise entity; documented in FEATURE_SPEC §2.

## 5. Worked example 4: absence proxy (numbers)

Row (`game_id=400496780`, IND away, tip 2013-09-20T23:00Z): top-5 rotation
`125;803;851;860;1003` from trailing 10 prior games; most recent prior game `400445897`
(tip 2013-09-15T17:00Z, strictly prior); `c_absence_share = 0.644` — i.e. 64.4% of the
top-5's expected minutes (baseline means over their own trailing games) were missing in that
most recent game (null/absent minutes rows; the uniform null-minutes proxy — DNP flag
exists in 2013 and is consistent, but the proxy definition is era-uniform). The strict
inequality `recent tip < target tip` is asserted for all 5,778 computed C rows.

## 6. Leak guards enforced in `--selftest` (exit non-zero on failure)

1. Column whitelist exact match; no outcome-bearing column names; no wall-clock columns.
2. Strict as-of inequality asserted per row per group: `b3_window_last_tip`,
   `b5_window_last_tip`, `c_recent_game_tip` all strictly < `tip_utc` (0 violations).
3. NA ⇔ neutral-reason invariant per gated value column (both directions, 11,976 rows).
4. Game-1 v2 behavior; expansion neutrality; 2002 minutes exclusion; pre-2013 Group B/C
   floor; continuity prior-season floor (computed starts 2014).
5. Lineage coverage: every universe team-season → exactly one franchise; DAL tree (DET
   2002–2009 + TUL 2010–2015 + DAL under `team_id` 3) and LVA tree (UTA `team_id` 15 2002,
   SAN/LVA `team_id` 17 2003+) asserted; no abbreviation ever a join key.
6. Value bounds: continuity, HHI, top-5 shares, absence ∈ [0,1].
7. Determinism: two independent full builds → identical parquet sha256
   (`ceaf10ba…f7bf`); the worked example (§2) pins one cell's bytes.

## 7. NOT_RUN / FORBIDDEN register (explicit, this lane)

- Opening-roster variant v1 — NOT_RUN_PIT (restated; not built).
- Target-game starter/DNP/active/ejected/reason — NOT_RUN_PIT and FORBIDDEN as inputs.
- Injury/availability timeline — NOT_RUN_PIT (no dated archive).
- Any scored computation, win-prob or calibration metric — NOT RUN (out of this lane's
  authority; feature construction only).
- 1997–2001 era — out of corpus scope (no player-level data exists; law restated).
