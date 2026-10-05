# FEATURE PROPOSALS — Lane C (NFL PLAYER DATA) · WINPROB-PLAYERDATA-PREP-V1

DESIGN ONLY — nothing run this cycle (no scored computation, no win-prob metrics on real
outcomes). Comparison design below defines how any successor FEATURE-PREP/SCORED step must be
evaluated. At most 3 groups per dispatch.

Frozen yardstick: the NFL team baseline **B1\* (K40 HCA0 family)** frozen by the prior cycle.
New mechanisms must beat THAT, not B0.

## Group F1 — QB recent form / availability

- **Features**: prior-k-game (kickoff-ordered, k∈{3,5}) QB aggregates: pass yards, TD, INT,
  attempts, yards/attempt, INT rate; plus "starter continuity" = share of prior k games in
  which the team's lead QB (max offense_snaps among QBs that game, from snap_counts) is the
  same player as in the game before. Backup-QB flag: lead-QB offense_pct < 0.55 in the most
  recent prior game (injury replacement in progress).
- **Testable hypothesis**: H_C1 — conditioning on the B1\* baseline state (Elo/HCA/spread-free),
  teams whose lead QB has prior-3 yards/attempt above their trailing season median win more
  often than the baseline predicts; a recalibration adding F1 reduces out-of-sample log-loss
  on the train-internal window beyond noise (Diebold-Mariano / bootstrap CI).
- **PIT basis**: PIT_AUDIT F1/F2 PASS (kickoff-time as-of join proven; worked example
  2024_11_KC_BUF prior-3 = 819 yds/6 TD/1 INT/124 att).
- **Join keys**: games.csv `game_id` ↔ stats `game_id`; team = games.csv home/away ↔ stats
  `team`; kickoff_utc ordering; player_id (GSIS) for QB identity; snap_counts via
  position=='QB' + offense_snaps argmax per team-game (no crosswalk needed for the team-level
  share).
- **Risks**: 17-game season → tiny n per team-season (k=3 windows overlap heavily; effective
  sample small); QB in-game injuries make "lead QB of the last game" noisy; roster churn
  (trades/FA) breaks player-stationarity; backup-QB flag rare events (~a few dozen
  team-games/season) → high variance; multiplicity across k values — pre-register k∈{3,5}
  only.

## Group F2 — Skill-player usage mass

- **Features**: team-level prior-k usage concentration: Herfindahl of targets share across
  receivers, Herfindahl of carries share across RBs (weekly `target_share`, `air_yards_share`,
  `wopr` ship in-file; aggregate by summing shares weighted by team pass attempts); usage
  delta = prior-k mean target_share of the team's top-1 receiver minus season-to-date mean.
- **Testable hypothesis**: H_C2 — teams with *stable-or-rising* top-receiver usage mass
  (delta ≥ 0) are under-calibrated by B1\* relative to teams with collapsing usage (WR1
  shadowed/injured); adding the delta term reduces log-loss on the internal window.
- **PIT basis**: PIT_AUDIT F3 PASS (same as-of join).
- **Join keys**: as F1; aggregation within (game_id, team) over `position_group` ∈ {WR,RB,TE}.
- **Risks**: usage shares depend on game script (blowouts deflate targets) — correlated with
  the same Elo state the baseline already encodes, so marginal information may be small;
  target_share is 0 for non-appearing players (missing vs zero ambiguity after the weekly
  placeholder-row exclusion); many positions × windows → multiple-testing; garbage-time
  noise; small n again (17 games).

## Group F3 — Key-position absence proxy (PIT-safe substitute for injury data)

- **Features**: for each position bucket (QB, OL, WR1/2, TE, EDGE/CB by snap mass): binary
  "absent in prior game" = position bucket's total offense/defense snaps in the last prior
  game < 0.5 × its prior-3 mean; "newly absent" = absent in last prior game but present in
  prior-3 mean; count of newly-absent buckets per team.
- **Testable hypothesis**: H_C3 — teams entering a game with ≥1 newly-absent key bucket are
  overrated by B1\* (baseline sees Elo only); an absence-count adjustment reduces log-loss.
  NOTE this is a PROXY for injury-driven absence: actual injury features remain NOT_RUN_PIT.
- **PIT basis**: PIT_AUDIT F4 PASS (prior completed games only); F5 (true target-game
  injury/active status) NOT_RUN_PIT — carried blocker, must not be bypassed through this
  proxy's interpretation.
- **Join keys**: snap_counts (pfr_player_id OK at bucket level: aggregate by position within
  team-game before any id join); games.csv as-of ordering.
- **Risks**: in-game injuries corrupt "last-game absence" (a player hurt mid-game shows low
  snaps → false absence signal, and their absence carries into the *next* game — the proxy is
  deliberately lagged but noisy); rest/scrubbed week-18 lineups (playoff-clinched teams rest
  starters — absence signal inverts); bye weeks must be excluded (kickoff-ordered window
  handles gap > 10 days as "no prior game"); snap_counts release lags stats in-season (2026:
  3 days) — still pre-kickoff; OL buckets aggregate across positions with different snap
  meanings; multiplicity.

## Comparison DESIGN (no runs this cycle)

1. **Window**: train-internal only (seasons on disk 2021–2025 pbp/stats + any already-frozen
   team feature tables); 2026 season is prospective-only and untouched.
2. **Metric**: out-of-sample log-loss (calibration law) of {B1\* frozen} vs {B1\* + feature
   group}, walk-forward by kickoff_utc; report per-group and stacked deltas with block
   bootstrap CIs (cluster = team-week).
3. **Negative control**: time-shuffled feature panel (features randomly permuted across
   team-games within season) must produce Δlog-loss ≈ 0 — any "improvement" from the shuffled
   panel invalidates the pipeline (leak check).
4. **Acceptance gate (future cycle, not this one)**: pre-registered single primary contrast
   per group; improvement must clear the CI AND survive the shuffled-control; else NOT
   adopted. No re-gridding K/HCA; B1\* stays frozen.
5. **Boundary**: this file designs only; any execution requires fresh registration + owner
   instruction per plan §Terminal outcomes.
