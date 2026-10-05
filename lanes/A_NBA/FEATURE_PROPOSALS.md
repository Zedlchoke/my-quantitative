# FEATURE PROPOSALS — NBA player-level signals (Lane A, WINPROB-PLAYERDATA-PREP-V1)

PROPOSALS ONLY. Nothing here is computed against outcomes this cycle; no scored
run is authorized by this document. Target baseline: **B1\*** = B1-d own-Elo
K=32 HCA=100 (frozen, NBA-WINPROB-SCORED-V1). Any successor must beat B1\*, not
B0. At most 3 groups; each is deliberately low-dimensional (1–4 scalars per
team-game) to respect the overfit risk of player-level data.

## ANCESTRY WARNING (mandatory reading before any successor)

Team-level rest/form layer **T1 FAILED** in NBA-WINPROB-SCORED-V1
(TERMINAL, NO_PROGRAM_PASS; H1/H2 alive). T1's family = schedule-derived
rest days + team recent-form reweighting at team granularity. The proposals
below are flagged as **ancestry-risk: PARTIAL** and must argue the difference:

- **What is genuinely new (not a T1 re-grid):** T1 had no access to WHO played.
  Player-level data adds (a) *composition* information (which minute-mass is
  on the floor, which specific high-minute players are out) and (b)
  *availability events* (DNP-with-reason) that team box/schedule data cannot
  represent. Rest-days-as-calendar is NOT re-proposed anywhere below.
- **What is ancestry-adjacent (must not silently re-enter):** any feature that
  collapses to "team played N games in M days" or "team won/lost last k" is
  T1 re-gridded with extra steps. Group A below is deliberately restricted to
  minutes-mass deviations vs own season-to-date norm (rotation-intensity
  proxy), NOT calendar rest, NOT win/loss form. If a future implementation
  cannot keep those apart, the group must be dropped as ancestry-contaminated.
- Negative-control discipline below (time-shuffled features) is the design
  guard: a feature that only re-discovers rest/form should die under the same
  shuffle that killed T1's marginal value.

## Group A — team minutes-mass / rotation-intensity load

- **Feature:** per team-game, `mass_k = mean(minutes played by team's players
  over prior k=5 games)`, then `load = mass_k − mass_season_to_date`; optionally
  also `top5_share = share of minutes logged by the 5 highest-minute players
  (prior k)`. 2 scalars per team-game.
- **Hypothesis (testable):** B1\* treats a team as the same entity every game;
  rotation-intensity deviations (shortened rotations, uncharacteristic minute
  concentration) mark transient team states (fatigue-by-usage, not calendar
  rest) that shift true win probability at fixed Elo. If so, adding `load`
  improves calibration vs B1\* on 2016+ internal window.
- **PIT basis:** prior-5-by-tip_utc as-of join — proven constructible
  (PIT_AUDIT.md §3). No same-game inputs.
- **Join keys:** `game_id` → schedule (`game_date_time`→tip_utc, `home_id`/
  `away_id`→team side); box rows by `game_id`+`team_id`+`athlete_id`.
- **Risks:** (i) minutes-mass is near-constant by construction (240 regulation)
  — the informative part is the small deviation; weak signal-to-noise;
  (ii) OT games inflate mass; must normalize by game length;
  (iii) ancestry drift toward T1 if reduced to "games played" proxies.

## Group B — top-player recent form vs own baseline

- **Feature:** for each team's top-N (N≈3) minute-mass players (season-to-date,
  trailing), `form = mean(points_per_minute, prior k=5) − season_to_date_mean`,
  averaged over the N players. 1–2 scalars per team-game.
- **Hypothesis (testable):** B1\* ratings move on results only; a team whose
  top-minute players are under/over-performing their own scoring baseline
  carries information about current strength that Elo adapts to slowly
  (K=32). If incremental, it should improve log-loss most in mid-season
  (small Elo adjustment lag).
- **PIT basis:** same as-of join; only prior games' per-player stats; target
  game's player stats BANNED.
- **Join keys:** as Group A; player identity by `athlete_id` (stability across
  the season verified: id + name both present; 2026 has 33 identity-less rows
  to exclude).
- **Risks:** (i) shooting-variance noise in 5-game windows (points/minute is
  high-variance); (ii) per-minute denominator small for low-minute players —
  restrict to top-minute players by construction; (iii) many-player columns
  invite overfit — this group is capped at an N=3 aggregate, NOT per-player
  columns; (iv) is ancestry-adjacent to "team recent form" (T1) — the defense
  is that the deviation is player-relative-to-self, not team-relative-to-league;
  the negative control must confirm.

## Group C — key-player absence indicator (prior-games evidence only)

- **Feature:** `abs_out = 1 if any of the team's top-N minute-mass players
  (season-to-date) missed either of the prior 2 team games with
  `did_not_play=True``; plus `abs_streak = count of consecutive prior games
  missed by the highest-minute player`. 1–2 scalars per team-game.
  **Target-game DNP/injury status is NOT used (NOT_RUN_PIT).**
- **Hypothesis (testable):** absences cluster (injuries span multiple games)
  and the previous game's observed absence predicts the *current* game's
  weakened rotation better than Elo alone; if true, `abs_out` adds calibration
  value precisely because it is lagged observed behavior, not a prediction.
- **PIT basis:** uses only `did_not_play`/`reason` from prior games (post-game
  facts of *earlier* games) — PIT-safe under the proven as-of join. Target-game
  availability remains NOT_RUN_PIT (PIT_AUDIT.md §1).
- **Join keys:** as Group A; DNP rows by `game_id`+`athlete_id`+`did_not_play`+
  `reason`.
- **Risks:** (i) **trades / mid-season team changes** — a player traded away
  stops appearing for team X; naive "missed game" logic would count his
  departure as an absence. Mitigation for design: require the player to have
  appeared for the SAME team within the trailing 10 team-games before counting
  an absence; verification of this guard is NOT run this cycle (design note).
  (ii) load management is "COACH'S DECISION" in `reason` — indistinguishable
  from tactical DNP without injury semantics; treat all DNP uniformly in v1.
  (iii) small early-season samples: season-to-date "top players" undefined in
  week 1 — freeze a minimum-games gate (e.g. ≥5 team games) and emit
  neutral values before it; (iv) 2021 play-in boxes unpopulated — exclude
  `season_type=5` from priors.

## Comparison DESIGN (pre-registered for a future FEATURE-PREP successor)

- **Win condition:** calibration improvement vs B1\* — mean log-loss on game
  outcomes, NBA 2016+ window (store labels per COVERAGE_SCHEMA §2 note),
  train-internal (no future information in fitting; hyperparameters fixed on an
  earlier sub-window, evaluated on a later sub-window; no test-set reuse).
- **Controls:** (1) B1\* frozen baseline; (2) **time-shuffled negative control**
  — each feature column shuffled across games within season before scoring;
  a group that still "improves" under shuffle indicates leakage/mechanics
  artifact, not signal; (3) each group added ALONE (not stacked) first.
- **No-run note:** this cycle computes none of the above. Successor needs
  fresh registration + owner instruction per plan; any scored run additionally
  needs its own gate + typed GO.
- **Drop rules (pre-registered):** any group whose live improvement is within
  the shuffle noise band is discarded; ancestry rule of the header applies
  throughout.
