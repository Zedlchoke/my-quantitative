# FEATURE PROPOSALS — Lane B (WNBA PLAYER DATA) · cycle WINPROB-PLAYERDATA-PREP-V1 · 2026-10-05

DESIGN ONLY. No comparison was run this cycle (0 scored). Nothing here is authority to
compute win-prob metrics on real outcomes; a successor needs this cycle's PREP verdict +
owner instruction + fresh registration, and any scored step needs its own gate.

**Common evaluation DESIGN (never run here):** primary = log loss vs the frozen WNBA
baseline (B1-WNBA parent law, W-H1/W-H2 machinery as drafted in
`wnba-winprob-prep-v1/lanes/B_MECHANISMS/MECHANISMS_WNBA.md` — reference, never re-derive);
paired **date-cluster** bootstrap CIs; train-internal rolling-origin selection only; frozen
falsifier = REJECT iff pooled 95% CI of ΔLL(arm, parent) includes 0 or ≥ half of test folds
non-negative; **time-shuffled negative control** (permute the player feature across teams
within season) must not beat its parent. Player features may arm-split only on train-internal
windows; a single comparison at the frozen WNBA baseline on a held-out-internal window.

---

## Group A — Roster continuity / turnover (minutes-based), linked to W-H2

- **Linkage.** W-H2 (already drafted, GATED on Lane A) defines continuity
  `c_i(s)` = minutes-weighted share of team i's season (s−1) player-minutes attributable to
  players on i's season-s opening roster. This corpus now supplies both inputs at full
  depth: prior-season minutes from `player_box` (team_id × athlete_id × minutes) and
  membership from `game_rosters` (game-1 sheet per team-season). The W-H2 draft's census
  gate is answered here: roster coverage ≥99.9% of team-seasons 2003+ (COVERAGE_SCHEMA §2).
- **Hypothesis (testable vs baseline).** Continuity-modulated rating carryover
  (`R_start = league_mean + ρ·c_i(s)·(R_end − league_mean)`) beats the scalar-ρ0 parent on
  season-boundary games (first ~8–10 games/season) in pooled ΔLL, with the shuffled-
  continuity control failing to beat the parent.
- **PIT basis.** Prior-season minutes: strictly completed prior-season games (clean).
  Opening roster: **v2 only** (game-1 membership from game 2 onward) — v1 is NOT_RUN_PIT
  (PIT_AUDIT §3). No post-game roster field enters.
- **Join keys.** Franchise-level: canonical 20-key lineage table
  (`~/.my-quantitative-data/wnba-prep-v1/team_key_table.csv`; LVA=UTA→SAN, DAL=DET→TUL,
  CON=ORL→CON). Never join on raw ESPN abbreviations (ESPN labels ALL Detroit 2002–2009 as
  `TUL`). Player-level: `athlete_id` (stable ESPN ids in-corpus), `team_id`, `game_id`.
- **Risks.** 12-team league / small n per season; franchise relocations forcing the lineage
  keys; 2020 Wubble (147 games) as an outlier prior-season; expansion team-seasons (CHI 2006,
  ATL 2008, GSV 2025, TOR/PDX 2026) have no prior season — start at league mean in BOTH arms
  (W-H2 law, they contribute no contrast); trades mid-season are invisible to a season-start
  continuity measure; 2002–2003 minutes/coverage holes push the eligible window to 2003+
  (minutes-quality floor realistically 2013+ for the minutes-weighted variant); overfit on
  ~23 season folds.

## Group B — Team minutes-mass / load from prior k games

- **Definition (design).** For each team-game G: rolling over the prior k games (k ∈ {3,5},
  train-selected): total minutes mass, minutes HHI (rotation concentration), share of
  minutes from the top-5 minute-getters, games-played counts (attendance proxies), and a
  rest-adjusted variant (minutes per available day). All inputs = `player_box.minutes` of
  strictly-prior games by `tip_utc`.
- **Hypothesis.** Rotation concentration/mass over the prior k games carries win-prob signal
  beyond the team rating baseline (e.g., fatigue/load proxy in condensed stretches);
  ΔLL(Group B arm, frozen baseline) < 0 pooled.
- **PIT basis.** PASS_CONSTRUCTIBLE — proven by the worked as-of join (PIT_AUDIT §2,
  Connecticut Sun 2013, prior-5 minutes by tip time, team totals ≈ 200 min/game).
- **Join keys.** `game_id` → ESPN schedule `tip_utc`; `team_id` per row (never abbreviation —
  §2 artifacts); game set = ESPN-side universe rows (5,988), Cup flagged not dropped.
- **Risks.** Signal likely small vs Elo baseline; 2020 Wubble and Commissioner's Cup
  clustering distort rest calculations; backfill holes 2002–2012 force a coverage floor
  guard (use 2013+ or accept ≥96% floor 2004+); minutes 100% null in 2002 (exclude);
  expansion seasons with tiny history; overfit on k.

## Group C — Top-player recent form vs own baseline

- **Definition (design).** Identify each team's minutes-weighted top-N rotation (N=5) from
  the trailing window (e.g., prior 10 games); compute their prior-k-game production
  (pts/reb/ast per-minute or per-game z-score vs their own trailing-season baseline) and an
  **absence proxy** (share of top-N minutes missing in the most recent prior game(s) via
  null-minutes rows / `did_not_play` 2012+). All strictly prior.
- **Hypothesis.** Deviations of top-player form/availability from their own baseline improve
  win-prob calibration vs the team baseline, especially in the first half of seasons before
  the rating baseline absorbs personnel changes.
- **PIT basis.** PASS_CONSTRUCTIBLE via the same as-of join; the absence proxy uses only
  **prior-game** null-minutes/DNP rows — target-game DNP stays NOT_RUN_PIT and banned.
- **Join keys.** `athlete_id` × `team_id` × `game_id`; player identity across seasons via
  `athlete_id` (ESPN id); trades = a player's history splits by `team_id` (within-season
  trade handling must be frozen before evaluation).
- **Risks.** Same as B, plus: star-player baseline is noisy early-season (small samples);
  trades and overseas absences create mid-season structural breaks; DNP flag only exists
  2012+ (pre-2012 absence must proxy on null minutes); 12 teams ⇒ pooled effects are small —
  the pre-frozen capacity floor (W-H2 machinery) should be applied; strong overfit risk with
  N and k free — freeze both train-only.

---

## What is deliberately NOT proposed

- Anything consuming target-game roster/starter/DNP/active/reason (NOT_RUN_PIT).
- Any usage of `active` as availability (measured defective, COVERAGE_SCHEMA §6).
- Any NBA input (WNBA-only law); any market/odds data (banned by plan).
