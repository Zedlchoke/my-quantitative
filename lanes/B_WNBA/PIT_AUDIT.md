# PIT AUDIT — Lane B (WNBA PLAYER DATA) · cycle WINPROB-PLAYERDATA-PREP-V1 · 2026-10-05

Doctrine §13 law: every field has three times (event / effective / **available**);
`retrieved_time` never substitutes `available_time`. A field may enter a pre-game feature
only if its `available_time` ≤ forecast time is **evidenced**; otherwise `NOT_RUN_PIT`.
Same-game stats of the target game are banned, always.

## 1. Verdict table (per candidate field)

| candidate field (source) | event time | available time evidence | PIT verdict |
|---|---|---|---|
| prior-games minutes aggregate (player_box `minutes`, prior k games) | game tip (ESPN schedule `date` = canonical `tip_utc`) | construction: only games with `tip_utc` strictly < target tip enter; **worked example below** | **PASS_CONSTRUCTIBLE** (as-of join proven) |
| prior-games starts / starter share (player_box `starter`) | same | same as-of join; starter flag is a same-game post fact but only *prior games'* flags are read | **PASS_CONSTRUCTIBLE** (same proof) |
| prior-games form (player_box pts/reb/ast etc., prior k games) | same | same as-of join | **PASS_CONSTRUCTIBLE** (same proof) |
| prior-games minutes-mass / rotation concentration (distribution of prior-game minutes) | same | same as-of join | **PASS_CONSTRUCTIBLE** (same proof) |
| target-game `starter` / `did_not_play` / `active` / `ejected` / `reason` (game_rosters or player_box of the target game) | target-game roster sheet | release assets are **current-state snapshots with no publication timestamps**; no evidence the sheet existed pre-tip; also `active`/`reason` semantics are defective (COVERAGE_SCHEMA §6) | **NOT_RUN_PIT** (and quality-barred even post-game) |
| season-opening roster (game-1 membership) used for **all** games of the season (W-H2 variant v1) | team's game 1 | no publish timestamps; cannot prove the game-1 sheet was knowable before game 2's tip **for all seasons** | **NOT_RUN_PIT** (v1) |
| season-opening roster used **from game 2 onward** (W-H2 variant v2) | team's game 1 | by construction: game-1 sheet enters features only for forecasts with `tip_utc` strictly after game 1's tip — a strictly-prior completed game, same as any prior-game input | **PASS by construction** (v2, design-level; the successor must freeze v2 or find new evidence for v1) |
| injuries / availability feed | n/a | no dated availability archive exists in any rights-cleared WNBA corpus on disk | **NOT_RUN_PIT** |
| same-game (target game) player stats — any field | target game | banned by doctrine | **FORBIDDEN** |

## 2. Worked example (the one required proof): prior-5-games minutes by tip time

As-of law (identical to the rolling law in the prior cycle's handoff): *features for game G
may use only games with `tip_utc` strictly less than `tip_utc(G)`*, with
`tip_utc := pd.to_datetime(espn.date, utc=True, format="ISO8601")`.

Measured example (from `measurements_b.json` → `pit_worked_example`; re-runnable):

- Team: **Connecticut Sun** (franchise CON), `team_id = 18`, season 2013, 34 team-games
  resolved to ESPN tips by `game_id`.
- Target game: `400445816`, tip_utc **2013-07-06T23:00:00Z**.
- Prior 5 games selected **strictly by tip time** (tips 2013-06-14 … 2013-07-02, all < target):

| prior game_id | tip_utc | team minutes total | players with minutes | top-3 player minutes (athlete_id: min) |
|---|---|---:|---:|---|
| 400445826 | 2013-06-14 23:30Z | 200.0 | 9 | 485:36, 916:34, 928:29 |
| 400445854 | 2013-06-16 21:00Z | 201.0 | 9 | 916:35, 918:34, 928:33 |
| 400445709 | 2013-06-23 19:00Z | 200.0 | 9 | 918:35, 928:32, 124:26 |
| 400445771 | 2013-06-29 23:00Z | 199.0 | 9 | 918:35, 916:31, 124:26 |
| 400445798 | 2013-07-02 23:00Z | 202.0 | 9 | 918:34, 928:32, 124:29 |

Sanity: team minutes per game ≈ 200 (= 5 starters × 40 min), per-player extraction clean.
**Verdict: PASS_CONSTRUCTIBLE** — the as-of join over ESPN schedule tip times × player_box
`minutes` rows (keyed `game_id` × `team_id`) works; prior-k minutes mass, per-player minutes
and rotation shares are constructible without any same-game information.

Coverage guard (from COVERAGE_SCHEMA §2/§6): this construct is data-clean from **2013
onward**; usable ≥2004 with per-season coverage floors; **unusable in 2002** (minutes 100%
null) and degraded 2003 (76.1% game coverage, no DNP flag).

## 3. The opening-roster law (spelled out, per dispatch)

W-H2 (B_MECHANISMS/MECHANISMS_WNBA.md) uses "season-s opening roster = membership attached
to a team's first recorded game of season s". The PIT law for this lane:

1. The game-1 roster sheet of team i in season s is a fact about the world at game 1's tip.
   The **asset carries no publish timestamps** — it is a current-state snapshot. Whether the
   game-1 sheet was knowable *before later tips* is therefore not auditable from the corpus.
2. **v2 (frozen as the only defensible default):** use game-1 membership only for forecasts
   of games with `tip_utc` strictly greater than game 1's tip (from game 2 onward). This is
   just the ordinary strictly-prior rule — game 1 is then simply a completed game.
3. **v1 (game-1 membership applied to game 1 itself, or all-season):** **NOT_RUN_PIT** — no
   evidence of pre-tip availability; a successor may adopt v1 only with new evidence or an
   explicitly frozen, documented assumption (never silently).
4. Post-game roster fields (`starter`, `did_not_play`, `active`, `ejected`, `reason`) of the
   *target* game remain forbidden inputs in every variant.

## 4. NOT_RUN_PIT register (explicit)

- Target-game starter/active/DNP/reason/ejected — **NOT_RUN_PIT** (no pre-game publish
  timestamp evidenced; `active`/`reason` additionally quality-barred, COVERAGE_SCHEMA §6).
- Opening-roster variant v1 — **NOT_RUN_PIT**.
- Any injury/availability timeline — **NOT_RUN_PIT** (no dated archive exists in the corpus).
- Nothing in this lane computed a forecast, a log loss, or any win-prob quantity (no scored
  computation occurred; the worked example is an aggregate-counting demonstration only).
