# DATASET_SCHEMA — nba-538-v1 normalized dataset (Lane B design, NBA-WINPROB-PREP-V1)

Design basis: DATASET_AUDIT.md (same dir, all numbers measured 2026-10-04 on
sha256 `d46ed354...d616bc`). The controller implements; lane B designed. Every
design choice below cites the audit finding that motivates it (A-numbers refer
to the anomaly register in DATASET_AUDIT.md).

## 1. Design principles

1. **One canonical row per game.** The source has exactly 2 rows per game
   (verified: 63,157 games, rows-per-game_id = {2: 63157}). The canonical table
   collapses them; both perspectives are derivable by swapping.
2. **Lineage, not city, is the rating unit.** Ratings follow the franchise
   through relocations (SEA->OKC, VAN->MEM, ...). Key = `lineage_id` = source
   `fran_id` (53 lineages; all verified single connected on-court lineages,
   audit §4). The NBA's official 2014 Charlotte history attribution is NOT used
   (A13).
3. **Strict as-of (date-grain) derivations.** Any feature for game g may use
   only games with `(date, gameorder) < (g.date, g.gameorder)` (A9 — same-team
   same-day double games exist, so gameorder breaks ties). 538's elo/forecast
   columns are quarantined into a side table (A15).
4. **Era awareness is explicit.** `lg_id`, `season`, and note-derived flags
   travel with each game so the protocol/model can gate eras (A2, A3, A4).

## 2. Source -> canonical transformation (dedup rule)

Given the 2 source rows of each game_id (g0 with `_iscopy=0`, g1 with
`_iscopy=1`; verified exactly one of each per game):

1. **Anchor row = `_iscopy=0` row.** For all 63,138 H/A games it is the home
   row (crosstab verified). For the 19 N games it is the designated row.
2. `site = g0.game_location`; if `H`: `home_team = g0.team_id`,
   `away_team = g1.team_id`; if `N`: `home_team = g0.team_id`,
   `away_team = g1.team_id` (designated, `site='N'`; the labels mean
   "designated team", not venue — A7).
3. `home_pts = g0.pts`, `away_pts = g1.pts` (mirror-equal to the reverse row;
   0 violations). `home_win = (home_pts > away_pts)` (no ties; verified 0 rows
   with pts==opp_pts, 0 result/pts inconsistencies).
4. `date = to_iso(g0.date_game, "%m/%d/%Y")`. **Never parse the date from
   game_id** (A8: 2 games have +1-day prefixes).
5. `season = g0.year_id`, `lg = g0.lg_id`, `is_playoffs = g0.is_playoffs`,
   `gameorder = g0.gameorder`, `src_game_id = game_id` (opaque string).
6. `home_seasongame = g0.seasongame`, `away_seasongame = g1.seasongame`
   (per-perspective; seasongame includes playoffs, A16).
7. Perspective fields from BOTH rows: elo/forecast/etc go to the quarantined
   side table `f538_reference` keyed by (src_game_id, perspective).

**Build-time assertions (must all PASS or the build fails):**
- A1: n_rows_source == 2 x n_games == 2 x n_canonical (expect 126,314 / 63,157).
- A2: per game exactly one `_iscopy=0` and one `_iscopy=1` row.
- A3: mirror checks (pts, opp_pts, elo_i, opp_elo_i, id swap, location
  inversion, result inversion) — 0 violations (audit §2.3).
- A4: `(home_pts > away_pts)` consistent with source `game_result` — 0
  violations.
- A5: row count of canonical table == 63,157; PK unique, no nulls in key cols.
- A6: months present are Oct..Jun only; `date.year ∈ {season−1, season}` for
  100% of rows (verified).
- A7: per (team lineage, season): `home_seasongame`/`away_seasongame` sequences
  start at 1 and step by 1 (verified 1,487/1,487 team-seasons).
- A8: sha256 of source == manifest value before every build (byte re-check).

## 3. Canonical table `games` (63,157 rows)

| column | dtype | constraint | source / derivation |
|---|---|---|---|
| src_game_id | string | PK, unique, `^\d{9}[A-Z]{3}$` | game_id (opaque; A8) |
| gameorder | int32 | unique, dense 1..63157, strictly increasing with (date) | gameorder |
| date | date (ISO) | indexed | date_game parsed |
| season | int16 | 1947..2015 | year_id |
| lg | enum {NBA, ABA} | | lg_id (A3) |
| is_playoffs | bool | | is_playoffs |
| site | enum {H, N} | | game_location (H/A->H; N kept) |
| home_lineage | string | FK lineages.lineage_id | fran_id of home-designated row |
| away_lineage | string | FK lineages.lineage_id | fran_id of away row |
| home_team_id | string | FK lineages.team_ids (historical code) | team_id |
| away_team_id | string | FK lineages.team_ids | team_id (opp_id) |
| home_seasongame | int16 | >=1 | seasongame of home row |
| away_seasongame | int16 | >=1 | seasongame of away row |
| home_pts | int16 | 0..186 | pts |
| away_pts | int16 | 0..186 | opp_pts / mirrored |
| home_win | bool | not null (no ties) | home_pts > away_pts |
| margin_home | int16 (derived) | -186..186 | home_pts − away_pts |
| total_pts | int16 (derived) | | home_pts + away_pts |
| is_forfeit | bool (derived) | | notes contains "forfeit" (exactly 1 row, A10) |
| is_protest_completion | bool (derived) | | notes contains "rotested"/"ompletion" (4 games) |
| is_tiebreaker | bool (derived) | | notes == "Tiebreaker" (11 games) |
| is_round_robin | bool (derived) | | notes == "Round Robin" (11 games) |
| alt_venue | bool (derived) | | notes startswith "at " on the home row (2,673 games; A7) |
| note | string, nullable | | verbatim notes (95.7% null) |

Additional pair-level integrity: `(home_lineage, away_lineage, date)` may
repeat only for the 6 double-game days (A9); assert the count of such
same-lineage-pair same-date repeats == 6.

## 4. Dimension table `lineages` (53 rows)

| column | dtype | notes |
|---|---|---|
| lineage_id | string PK | fran_id (e.g., "Thunder", "Pelicans") |
| team_ids | array<string> | ordered historical codes, e.g. SEA->OKC |
| first_season, last_season | int16 | from data (audit §4.1 map) |
| n_games | int32 | |
| notes | string | free text (naming traps: "Hornets"=Bobcats lineage etc., A13) |

Ratings (538 or ours) key on `lineage_id`, never on team_id (A4/A13). The full
continuity map (audit §4.1) is the authority for lineage membership; freeze it
as a fixture at build time so any upstream source change fails loudly.

## 5. Quarantined side table `f538_reference` (126,314 rows = source rows)

| column | dtype |
|---|---|
| src_game_id | string (FK) |
| perspective | enum {designated(H/N), other} i.e. _iscopy 0/1 |
| lineage | string (fran_id of that row) |
| elo_i, elo_n, opp_elo_i, opp_elo_n | float32 |
| win_equiv | float32 |
| forecast | float32 |

Usage law: readable for baseline comparison and cross-checks only; the model's
feature pipeline MUST NOT join it into training features (A15). Measured facts
for our own Elo design (from audit §9): expansion cold start 1300.0 (A5);
season-boundary reversion median 0.7542 toward 1500 (A6).

## 6. As-of derivable fields (v1 date-grain law)

For each game g, all derived state uses only games with
`(date, gameorder) < (g.date, g.gameorder)`.

- **Physical layout / indexes** (parity between pandas and any SQL backing):
  - primary sort: `(date, gameorder)` — the file order is already exactly this
    (verified monotone; gameorder 1..63157 dense), so file order = as-of order.
  - per-lineage index: `(lineage, date, gameorder)` for both
    `home_lineage` and `away_lineage` (or a long-format `game_participants`
    view: one row per game per lineage — recommended for feature building).
  - date index for "all games strictly before date d" scans (rolling league
    aggregates: rest days, games yesterday, etc.).
- **Recommended derived per-game-perspective frame** `participants`
  (126,314 rows): (src_game_id, gameorder, date, season, lg, is_playoffs,
  lineage, role ∈ {home, away}, opp_lineage, pts_for, pts_against, win,
  seasongame, site, alt_venue, is_forfeit). Team-level as-of features
  (rest, B2B, form, prior meetings, Elo state) join here by lineage.
- **Elo state**: our own Elo carries (lineage -> rating) through the lineage
  table across relocations; iterate games in `(date, gameorder)` order;
  update K and HCA as protocol decides; cold start 1300.0 on first game
  (A5); optional season-boundary reversion ~0.75 toward 1500 (A6); N-site
  games: apply neutral HCA term or zero HCA (19 games — negligible either
  way, pick one and document).

## 7. FROZEN train/test split (lane C placeholder rule: "test = final 7 complete seasons")

Measured last complete season = **year_id 2015** (2014-15; 1,230 RS + 81
playoff games, ends 2015-06-16). Therefore:

- **TEST (frozen): seasons year_id 2009, 2010, 2011, 2012, 2013, 2014, 2015**
  (i.e., 2008-09 .. 2014-15) — **8,956 games** (8,369 RS + 587 playoff).
- **TRAIN: year_id 1947..2008 — 54,201 games.**
- Per test-season games: 2009: 1,315; 2010: 1,312; 2011: 1,311; 2012: 1,074
  (66-game lockout — documented, kept, A12); 2013: 1,314 (1,229 RS — cancelled
  game, A11); 2014: 1,319; 2015: 1,311.
- Freeze note: this proposal becomes frozen once the controller lands it; any
  change afterwards requires a new cycle decision. Nothing after 2015-06-16
  exists in the source, so there is no future-leakage surface beyond the
  538-derived columns (quarantined, A15).

## 8. Assumptions and protocol obligations (consolidated pointer)

All anomalies A1-A18 are listed in DATASET_AUDIT.md §"Anomaly / assumption
register". The ones the controller/protocol MUST decide or handle explicitly:
- A2/A3: era gating (3PT line 1980; NBA/ABA dual seasons 1968-1976) — define
  the modeling universe (recommend NBA-only default with lg flag available).
- A5/A6: our Elo cold start + season reversion — fix constants in the model
  plan, not in the dataset.
- A9: as-of ordering law (date, gameorder) — implemented in §6.
- A10: forfeit exclusion switch (1 game) — protocol flag, default keep.
- A12: 2012 lockout inside TEST — keep; document.
- A13: lineage table fixture freeze (53 rows) — build gate.
- A15: f538_reference quarantine — enforced by build (feature code must not
  import the table; CI check recommended).

## 9. Out of scope / open items

- Seasons after 2015-06-16 (needs a different source; A1).
- Venue identity/strength (not present; A7).
- Overtime flag (not present; A14).
- Rotation/injury data (not present).
