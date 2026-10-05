# PLAN — WINPROB-PLAYERDATA-PREP-V1 (player-data audit for NBA/WNBA/NFL win-prob, $0)

- cycle_id: WINPROB-PLAYERDATA-PREP-V1 · asset: shared · ACTIVE_LIGHT, budget 0 scored, NO GO phrase
- owner authority 2026-10-05 (this chat): PREP/data-research ONLY — audit whether NBA, WNBA and
  NFL **player-level** data can improve team win-probability baselines. Explicitly NOT a GO for
  any scored backtest, NOT authority to run win-prob metrics on real outcomes, no S1, no
  paper/live/betting, no purchases (budget 0 USD — free sources only), no push, no merge.
  Owner additionally instructed: maximize parallel subagent lanes; controller cross-checks.
- Immutable history: all frozen sources, results and ledgers of every prior cycle (incl.
  NBA-WINPROB-PREP-V1/SCORED-V1, NFL-WINPROB-PREP-V1/SCORED-V1, WINPROB-NG-PREP-V1,
  NBA-WINPROB-NG-PREP-V1, WNBA-WINPROB-PREP-V1, NFL-WINPROB-NG-PREP-V1) are read-only evidence.

## Inheritance (from registry + disk, re-measured 2026-10-05)

- NBA baseline law: B1* = B1-d own-Elo K=32 HCA=100 FROZEN (NBA-WINPROB-SCORED-V1 TERMINAL,
  NO_PROGRAM_PASS; H1/H2 alive, T1 team-rest/form FAIL). Spent window 2009–2015 (never re-grid).
  New evaluation window = NBA 2016+; game universe 14,254 rows keyed by ESPN `game_id` at
  `~/.my-quantitative-data/nba-hoopr-v1/` (EXTEND-ONLY); PBP 2016–2025 at
  `~/.my-quantitative-data/nba-ng-prep-v1/pbp_2016_2025/`. **No NBA player box scores on disk.**
- WNBA: game universe 7,017 (ESPN 5,988 + stats 7,008; 20-key lineage; era 1997–2001
  warm-up-only). **Player-level ALREADY on disk**: `~/.my-quantitative-data/wnba-prep-v1/
  roster_audit/` holds `player_box_2002..2026.csv` + `game_rosters_2002..2026.csv`
  (sha256-verified vs release store by WNBA-WINPROB-PREP-V1 lane A; EXTEND-ONLY, read-only
  here). W-H2 roster-continuity mechanism already drafted there — reference, never re-derive.
- NFL: nflverse corpus at `~/.my-quantitative-data/nfl-nflverse-v1/` (pbp 2021–2025, games.csv)
  and `~/.my-quantitative-data/nfl-ng-prep-v1/` (injuries 2025/2026 — NOT_RUN_PIT no timestamp
  schema; schedules; teams; rights/ with nflverse-data LICENSE CC BY 4.0 copy). **No weekly
  player stats on disk.** 2026 split law: 63 played / 209 future / earliest future kickoff
  2026-10-06T00:15Z (prospective-only).
- Rights precedent (WINPROB-NG-PREP-V1 lane A): sportsdataverse data repos carry CC BY 4.0
  LICENSE.md verbatim; distribution repo sportsdataverse/sportsdataverse-data carries MIT on
  the store. nflverse-data carries CC BY 4.0. balldontlie Free: Teams/Players/Games endpoints
  only per prior verification — do NOT assume Free player stats (verify from public docs only).
- PIT law (doctrine §13): three times (event/effective/available); retrieved_time never
  substitutes available_time. Same-game player stats of the target game are banned as features.
  Target-game roster/active/starter/DNP/injury status = NOT_RUN_PIT unless a pre-game publish
  timestamp is evidenced. Prior-games aggregates are PIT-safe only via a proven as-of join on
  tip/kickoff time UTC.

## Tasks (owner round 2026-10-05)

1. Lane A — NBA PLAYER DATA (hoopR NBA player box): on-disk inventory (expect none); verify
   from official docs which hoopR/sportsdataverse store publishes NBA player box scores; quote
   LICENSE verbatim with URLs; download sample seasons (≥1 early/mid/latest of 2016+) to
   `~/.my-quantitative-data/playerdata-prep-v1/nba/` with URL+version+timestamp+bytes+sha256
   per file + ATTRIBUTION.md; schema/coverage audit (seasons, games vs schedule corpus join on
   ESPN game_id, players/game, duplicates game_id+athlete, missing, schema drift, DNP rows);
   re-download determinism note; PIT audit per candidate field (as-of tip-time join proof);
   2–3 feature groups + testable hypotheses + risks (trades, load management, small sample,
   overfit, ancestry vs dead T1 team rest/form); PASS/FAIL/NOT_RUN table.
2. Lane B — WNBA PLAYER DATA (wehoop player box): verify on-disk player_box/game_rosters
   2002–2026 corpus (re-hash sample vs recorded sha256; sizes; row counts); verify rights from
   release store + wehoop official docs; coverage vs 7,017 game universe (ESPN game_id join;
   era gap 1997–2001 disclosed); duplicates/missing/schema drift; starter=5 and roster-depth
   checks; PIT audit (target-game active/DNP = NOT_RUN_PIT expected; prior-game aggregates
   PIT-safe proof); 2–3 feature groups (continuity/turnover linkage to W-H2, minutes-mass,
   top-player form) + hypotheses + risks (12-team league, franchise lineage, 2020 COVID,
   expansion GSV/TOR); PASS/FAIL/NOT_RUN table.
3. Lane C — NFL PLAYER DATA (nflverse weekly player stats): on-disk inventory (expect none);
   verify nflverse-data release store publishes weekly player_stats (+ which variants); quote
   LICENSE verbatim; download to `~/.my-quantitative-data/playerdata-prep-v1/nfl/` with full
   provenance; schema/coverage (seasons, weeks, games join vs games.csv game_id, positions,
   duplicates, missing, schema drift); PIT audit (kickoff-time as-of join; injuries remain
   NOT_RUN_PIT; pbp participation prior-week snap counts as PIT-safe alternative on-disk);
   2–3 feature groups (QB form/availability, skill-player usage mass, absence proxy) +
   hypotheses + risks (bye weeks, in-game injuries, 17-game n, roster churn, overfit);
   PASS/FAIL/NOT_RUN table.
4. Lane R — RIGHTS CROSS-LEAGUE: verify licensing from official sources for hoopR ecosystem,
   wehoop ecosystem, nflverse-data, sportsdataverse-data distribution store; distinguish data
   license vs underlying-data rights (ESPN/league APIs); document explicitly what remains
   unclear for publication/commercial use (fail-closed wording, no legal advice); verify from
   public docs whether balldontlie Free offers player stats (no key usage, no assumption).
5. Lane D — INDEPENDENT VERIFIER (after A/B/C/R land; never repairs): re-measure claims vs
   bytes (spot re-hash, re-count, re-join), rights-quote honesty, PIT verdict logic, trial
   accounting (0 scored), boundaries compliance; discrepancy report.

## Boundaries

- No scored computation, no win-prob metrics on real outcomes (schema/coverage counting and
  PIT audits allowed), no S1, no paper/live, no betting language, no purchases, no accounts,
  no keyed signups, no push, no merge, no edits to frozen artifacts/ledgers/registries by
  lanes. Registry writes only via researchctl from root (controller). No API key values in
  any prompt/log/artifact.
- Root checkout = control plane only. Lanes write ONLY inside
  `.worktrees/winprob-playerdata-prep-v1/integration/lanes/<their-dir>/` (+ handoff JSON at
  their dispatch handoff_path) and data outside git under
  `~/.my-quantitative-data/playerdata-prep-v1/`. Existing data dirs are EXTEND-ONLY/read-only.
- Lane artifacts land uncommitted; the controller inspects and commits (one semantic commit
  per lane). Language law: calibration/forecasting vocabulary only.

## Artifacts

`lanes/A_NBA/ · lanes/B_WNBA/ · lanes/C_NFL/ · lanes/R_RIGHTS/ · lanes/D_VERIFY/ ·
lanes/DISPATCH/` under the integration worktree; each lane ends with handoff JSON
`zcode_orch_v3_handoff@1` at its handoff_path. Data: `~/.my-quantitative-data/
playerdata-prep-v1/{nba,nfl}/` (+ no WNBA downloads expected — corpus exists).

## Terminal outcomes (negative-first)

PREP_COMPLETE_PENDING_OWNER_DECISIONS | BLOCKED_DATA_RIGHTS | BLOCKED_TOOLING | TECHABORT_*.
This cycle registers no GO phrase and consumes none. A feature-prep successor step (building
frozen player-feature tables) may be proposed ONLY on this cycle's PREP_COMPLETE verdict +
owner instruction + fresh registration. Any scored successor additionally needs data/code
freeze, A7 prelaunch and owner typed GO at its own gate.
