# MECHANISMS — Lane C, WINPROB-NG-PREP-V1 (new-mechanism research for pre-game win probability)

- lane: C_MECHANISMS · task: wng-c-mech · date: 2026-10-05 · owner round 2026-10-05
- scope: research + protocol design ONLY. No data downloads, no outcome computation, no git,
  no edits to any terminal-cycle artifact. This document proposes; it authorizes nothing.
- language law (inherited): calibration language only — no PnL/betting/edge vocabulary.

## 0. Evidence base (immutable history, read from bytes)

Artifacts (read, not re-run):

- NBA: `/Users/hoangminhlong/my-quantitative/.worktrees/nba-winprob-scored-v1/integration/research/control/NBA-WINPROB-SCORED-V1/results/scored_summary.json`
- NFL: `/Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-scored-v1/integration/research/control/NFL-WINPROB-SCORED-V1/results/scored_summary.json`

Facts this lane builds on (pooled regular-season, log-loss primary, paired date-cluster CIs;
"negative ΔLL favors the arm"):

| quantity | NBA (2009–2015, n=8369) | NFL (2019–2025, n=1865) |
|---|---|---|
| B0 (constant) LL | 0.6769 | 0.6935 |
| B1* (best own-Elo) | B1-d, K=32, HCA=100, LL 0.5987 | B1-c, K=40, HCA=0, LL 0.6407 |
| B1* vs B0 ΔLL | −0.0782 [−0.0875, −0.0687] | −0.0528 [−0.0676, −0.0380] |
| HCA=100 vs HCA=0 | alive: −0.0215 [−0.0271, −0.0157] at K=32 | REJECTED: +0.0046 [−0.0035, +0.0125]; K=20 also ≥0 |
| rest/form layer vs B1* | T1 FAIL: −0.0010 [−0.0033, +0.0013], 5/7 folds neg. | T1 FAIL: +0.0017 [−0.0053, +0.0088], 3/7 folds neg. |
| rest vs form-only | −0.0012 [−0.0024, −0.0000022] (excludes 0, negligible) | REJECTED: +0.0001 [−0.0011, +0.0012] |
| calibration slope | 0.989 PASS | 0.977 PASS |
| program outcome | PROGRAM_PASS=false (T1 fail; H1/H2 alive) | INCONCLUSIVE=true (H1 alive; H2/H3 rejected) |

Consequences binding on this lane:

1. **Baseline for all new work = the own-Elo family** (B1* per league). Any new mechanism must
   beat B1* — not merely B0 — under the frozen comparison machinery.
2. The old NBA window 2009–2015 is SPENT: K/HCA/rest/form were grid-searched and scored there;
   re-gridding on it is forbidden. NBA evaluation happens on NEW windows only (2016+).
3. NFL rest/short-week MAIN effects are rejected in 2019–2025; re-testing them as main effects
   anywhere is dead weight. Only interaction framings with a distinct mechanism are candidates,
   and only on genuinely new NFL windows (2026 forward).
4. A logistic layer of rest/form features OVER Elo added ~nothing in both leagues. New signal
   must therefore enter as a REPLACEMENT rating (rating-input mechanism) or as a genuinely new
   pre-game information source — not as additive features stapled to elo_diff.

## 1. PIT feature matrix

"PIT" = knowable strictly BEFORE the game (pre-game timestamp precedes tip/kick).
Rights statuses as of this lane: verified in lane C only where stated; everything else is
NOT_RUN_PIT or PENDING another lane's verdict. Sources verified this lane (4 web checks,
feature-source verification only):

- (V1) nflverse/nflfastR-data: CC-BY-4.0; data auto-pushed to GitHub releases
  (nflverse/nflverse-data); page does not state intra-week latency; consistent with the
  dispatch verdict "post-game compiled". → train-only use under as-of law; NEVER current-game.
- (V2) wehoop (sportsdataverse): MIT license; WNBA play-by-play 2002–2026 (ESPN-backed
  `load_wnba_*` + WNBA Stats API loaders; rosters/standings/crosswalks); release assets rebuilt
  nightly/daily via GitHub Actions. Data-quality/as-of verdict is Lane B's.
- (V3) hoopR (sportsdataverse): NBA play-by-play 2002–2026; NBA Stats API + ESPN upstream;
  `load_*` reads sportsdataverse-data release assets rebuilt nightly. License type NOT
  identified on the page → the rights verdict itself is Lane A's.

| # | candidate feature | mechanism | knowable BEFORE game? | $0 source + rights status | publish-timestamp story | leakage risk | kill test |
|---|---|---|---|---|---|---|---|
| F1 | SOS-adjusted Elo (schedule-strength decomposition of the rating itself) | raw Elo conflates team strength with opponent quality under unbalanced schedules; soft schedules inflate ratings faster than Elo decays | YES — computed from completed games only | game-results feed already in hand from terminal cycles ($0); NBA results from the terminal cycle's own inputs (538 nbaallelo), NFL results/schedules nflverse (CC BY 4.0, V1) | each game's inputs frozen at prior tip | LOW if β is fit train-only; HIGH if β tuned on test window | frozen ΔLL CI vs B1* on train-internal time-split; negative control = time-shuffled SOS |
| F2 | home/away split ratings (two ratings per team, venue-role-updated, shrunk toward common) | team quality is venue-dependent beyond one league-wide HCA constant; NFL's rejected constant HCA is consistent with heterogeneous, team-specific home effects | YES — completed games only | same results feed as F1 ($0) | each game's inputs frozen at prior tip | MEDIUM: role-label orientation bugs look like signal | CI vs B1*; capacity check (split degenerates to parent ⇒ designed null); permutation of venue labels must destroy any gain |
| F3 | pre-game availability score, NBA (minutes-weighted Out/Doubtful aggregation from official injury report) | point-based ratings lag abrupt roster shocks (stars out, load management); availability is direct pre-game information | YES in principle (official report publishes pre-tip); NO verified historical $0 archive → **NOT_RUN_PIT** | candidates found, none proven: p1ho/nba-injuries (Fox-Sports-sourced, unmaintained), Kaggle "NBA Injuries 2010–2020" (media-sourced, rights unclear), mxufc29/nbainjuries (official-report pull, recent seasons, rights/coverage unverified). NBA official standardized reports have no verified historical bulk archive | would require per-record publication timestamp ≤ tip − report cadence; media-aggregated sets have NO trustworthy timestamps | HIGH: retro-filled "injury" rows from post-game news are look-ahead by construction | provenance audit FIRST (rights + timestamps); then frozen ΔLL vs B1* with shuffled-availability control; team-constant score (no variance) ⇒ drop |
| F4 | pre-game availability score, NFL | same mechanism, weekly report cadence | YES in principle; **NOT_RUN_PIT** | a candidate `injuries` asset inside nflverse-data releases is UNVERIFIED in this lane (web budget spent); treat as unverified | same requirement as F3 | HIGH (same as F3) | same as F3 |
| F5 | rest/b2b/3-in-4 × away interactions (NBA) | fatigue costs are paid primarily by the ROAD team; main-effect tests parameterized the mechanism away | YES — schedule-derived | public season schedules + the game-dates already inside the results feed ($0) | schedule published pre-season; postponements amend it — must track as-of amendments | LOW–MEDIUM (postponement as-of handling) | interaction BLOCK ΔLL vs its null parent B1* (per owner rule: interactions must beat null parents); train-internal first |
| F6 | travel-distance / timezone-shift buckets × away (NBA, NFL) | long-haul road trips + timezone shifts degrade road performance; buckets capture circadian load the raw rest count misses | YES — schedule × static venue geography | venue coordinates = static public facts; schedule as F5 ($0) | static; only the schedule part has timestamps | LOW | same as F5; time-shuffled bucket control mandatory |
| F7 | short-week × away interaction (NFL) | same fatigue mechanism, weekly cadence | YES | nflverse games/schedules (CC BY 4.0, downloaded in terminal cycle) | schedule release + flex amendments | LOW | 2026+ prospective ONLY (main effects rejected in 2019–2025); expect starvation (~272 games/season) — state honestly; kill if train-internal shows nothing |
| F8 | pace/efficiency train-only aggregates (NBA 2016+ box scores) as rating INITIALIZATION/prior | prior-season efficiency priors shorten Elo's cold-start path each season; must be a rating-input mechanism (additive logistic features over Elo are already dead, §0.4) | YES — computed strictly from games completed before the cutoff | **PENDING_LANE_A** — hoopR exists (V3: NBA pbp 2002–2026, nightly release builds, NBA Stats API/ESPN upstream) but the rights verdict on redistribution is Lane A's | aggregates recomputed under strict expanding-window as-of cutoffs | HIGH if any aggregate crosses the prediction cutoff — enforce expanding-window computation in code | prior-seeded Elo vs B1* on train-internal split; shuffled-prior control |
| F9 | NFL efficiency priors (train-only EPA/possession from pbp) → offseason rating prior | same cold-start mechanism; richer than win/loss alone | YES — train-only (pbp is post-game compiled: NEVER a current-game feature) | nflverse pbp — downloaded + CC BY 4.0 (V1); as-of law permits train-only role | aggregates from completed prior seasons only | HIGH if used in-season; restrict to season-start priors | same as F8 |
| F10 | WNBA roster-continuity-modulated rating carryover | 40-game season + heavy roster churn weakens prior-season rating priors; continuity should modulate how much prior rating survives the offseason | YES — rosters knowable at season start | **PENDING_LANE_B** — wehoop MIT package verified (V2); Lane B owns the PASS/FAIL verdict on coverage/as-of/renames/neutral sites | continuity computed from season-start rosters (timestamp = opening night) | MEDIUM (roster-file as-of discipline) | vs fresh WNBA Elo baseline; continuity index must show cross-team variance early seasons |
| F11 | negative controls: time-shuffled twin of every candidate (same marginals, no info) | protocol feature, not a mechanism | n/a | free | n/a | — | control must NOT beat its parent beyond noise; a "winning" control invalidates the paired comparison for that hypothesis |

Banned sources (plan, restated): 538 forecasts, closing/market odds, current-game box scores,
any re-grid of K/HCA/rest/form on the old NBA test seasons.

## 2. Prioritized hypotheses

Owner directions adjudicated: (a) SOS → **ACCEPT** (H-C1). (b) roster/availability →
**ACCEPT conditionally**, hard-gated on NOT_RUN_PIT clearance (H-C3). (c) home/travel/rest
interactions → **ACCEPT, narrow** (H-C4/H-C5-NFL row). (d) pace/efficiency train-only
aggregates → **ACCEPT only as rating initialization/prior** (H-C2a folded into F8/F9 protocol);
home/away-split strength → **ACCEPT** (H-C2); blowout/MOV-weighted Elo variants → **REJECT**
(a MOV re-grid of the dead Elo-update family with no new information source; would burn trial
budget re-litigating a spent mechanism). (e) WNBA → **ACCEPT conditional on Lane B** (H-C5).

### H-C1 — SOS-adjusted Elo (schedule-strength decomposition) — priority 1

- Mechanism. Elo's update magnitude already scales with opponent rating, but a team's LEVEL
  still reflects who it happened to play: a soft early schedule inflates a rating and Elo
  decays it too slowly (NBA: 82 unbalanced, division-weighted games; NFL: 17-game schedules
  with large SOS dispersion). The effect should be largest early in the season, when
  schedule imbalance is least washed out, and fade by late season — a pre-registered
  heterogeneity prediction.
- Operationalization (exact, allowed data only). From the completed-games-only results feed:
  `SOS_i(t) = mean over i's completed games of opp_Elo_at_tip`; input rating
  `R̃_i = R_i − β·(SOS_i − league_mean_SOS)`, game prediction
  `p = σ((R̃_home − R̃_away + HCA)/s)` with HCA/s at the league's frozen B1* values;
  β chosen on a train-internal rolling-origin split, then frozen. NOT an additive feature
  next to elo_diff (dead shape, §0.4).
- Falsifier (frozen language). REJECT iff pooled 95% CI of ΔLL(arm, B1*) includes 0 or
  favors B1*, or if fewer than half of test folds are negative; plus the shuffled-SOS
  negative control must not achieve a CI excluding 0 — if it does, the comparison machinery
  (not the hypothesis) is at fault and the hypothesis is un-scored, not PASS.
- Expected direction. ΔLL < 0 vs B1*, concentrated in early-season folds (games 1–20).
- Kills it fast. No gain on the train-internal split ⇒ never spend an OOS window. Gain that
  appears only where B1* is already strong ⇒ redundant, drop. Costs one β fit + one Elo
  re-run on existing $0 data — cheapest hypothesis to test end-to-end.

### H-C2 — Home/away split ratings — priority 2

- Mechanism. Team quality is venue-dependent beyond one constant: construction (rebounding/
  transition defense), style, altitude, travel patterns. NBA's alive HCA constant
  (−0.0215) shows venue matters at league level; NFL's REJECTED constant is exactly what
  team-heterogeneous home effects predict — a constant is mis-specified, not necessarily
  absent. This is genuinely new signal extracted from the SAME results feed (no new rights).
- Operationalization. Two ratings per team: `R_home`, `R_away`; the venue-role rating is the
  one updated at each game, shrunk toward the common rating with weight λ
  (`R_role ← (1−λ)·R_role + λ·(R_common + K·outcome_term)` shape; exact update frozen at
  registration); prediction `p = σ((R_home_i − R_away_j + h)/s)`. λ frozen from the
  train-internal split. Extreme λ reproduces B1* — the designed null parent.
- Falsifier. REJECT iff pooled CI of ΔLL vs B1* includes 0 or ≥ half folds non-negative;
  ALSO reject if the rating split collapses (‖R_home − R_away‖ ≈ 0) — capacity evidence the
  data cannot support the extra parameter.
- Expected direction. ΔLL < 0; stronger case in NFL (heterogeneous home effects) and for
  extreme-travel teams; should fail cleanly to parent if heterogeneity is noise.
- Kills it fast. Venue-label permutation within train must destroy the gain (else
  implementation/leak); if the train-internal split shows nothing, stop before OOS.

### H-C3 — Availability-adjusted rating (injury/roster PIT) — priority 3, HARD-GATED

- Mechanism. Point-based ratings respond to shocks only after they show up in results;
  the official pre-game injury report is direct information about current strength. NBA
  2016+ load-management makes this the strongest candidate for genuinely NEW pre-game
  information — and it is the only hypothesis here that can move the information frontier
  rather than re-weight existing results data.
- Status. **NOT_RUN_PIT.** No $0 historical source with verified rights AND trustworthy
  publish timestamps is known (§1 F3/F4). This lane does not declare it impossible; it
  declares it unproven. A successor cycle may spend prep effort on a provenance audit
  (per-row publication timestamps, rights text, official-report provenance) BEFORE any
  modeling.
- Operationalization (if and only if a source clears). `avail_i(g) = Σ_players
  expected_minutes_share · 1_status∈{Questionable,Probable,Doubtful→partial, Out→0}`
  at the report's publication time; arm = replacement-rating form
  `R̃_i = R_i + γ·(avail_i − 1)` or additive-on-split-rating, frozen at registration;
  NO retro-filling from post-game box-score minutes (that is leakage by construction).
- Falsifier. Same frozen CI language vs B1*; plus a no-leak audit: every availability
  record's timestamp must precede tip by ≥ the report cadence; shuffled-availability
  negative control mandatory.
- Expected direction. ΔLL < 0 vs B1*, concentrated in games where a high-minutes player is
  Out; near-zero otherwise.
- Kills it fast. Rights/timestamp audit fails ⇒ stays NOT_RUN_PIT, slot released (never
  reallocated mid-program). Score ≈ team-constant ⇒ no within-team variance ⇒ drop.

### H-C4 — Fatigue × venue interaction block — priority 4 (NBA-first; NFL prospective-only)

- Mechanism. The terminal cycles tested rest/form/b2b/short-week as MAIN effects and got
  ~nothing (NBA) / rejection (NFL). The fatigue theory actually predicts the cost lands on
  the ROAD team (home b2b is cushioned by familiarity, routine, and no travel): the main
  effects diluted the mechanism with the wrong parameterization. Interactions are a
  different hypothesis with a different sign structure — not a re-test of the dead mains.
- Operationalization. ONE frozen block, never term-fished:
  NBA — `b2b_away`, `3in4_away`, `travel_bucket_away` (miles since last game: 0–1000 /
  1000–2000 / 2000+), `tz_shift_away` (count of ≥2 timezone crossings on road trip), all
  as interactions with (or restricted to) away games, entering the frozen B1* shape;
  NFL — `short_week_away`, `travel_bucket_away`, prospective 2026+ only.
- Falsifier. Per owner rule: interactions must beat their NULL PARENTS. REJECT iff pooled
  CI of ΔLL(block arm, B1*) includes 0; the block is tested jointly (one ΔLL), never
  per-term; time-shuffled travel buckets = negative control.
- Expected direction. Small ΔLL < 0, concentrated in b2b_away / long-travel_away games
  (NBA ~1230 games/season gives the block room; NFL ~272 does not — say so).
- Kills it fast. NBA train-internal split fails ⇒ do NOT spend the NFL slot (thin data,
  starvation risk is the default outcome). This is the lowest-priority use of a scored
  window.

### H-C5 — WNBA fresh program: continuity-modulated rating carryover — priority 5, gated on Lane B

- Mechanism. 40-game season + high roster churn (free agency, overseas conflicts,
  retirements) ⇒ (i) prior-season rating priors are weaker than the NBA's, so offseason
  shrinkage should be team-specific; (ii) in-season convergence is faster. Continuity —
  the share of prior-season rotation minutes returning — is the natural moderator and is
  PIT-safe (rosters are set before opening night).
- Operationalization. Fresh WNBA Elo (own K/HCA calibrated inside the fresh program's
  train-only selection — this is a NEW league, the spent-window prohibition does not apply
  to it, but the same train-only discipline does); offseason carryover
  `R_start_i = league_mean + ρ·(continuity_i)·(R_end_i,prev − league_mean)`;
  `continuity_i` from season-start rosters (wehoop rosters, V2, pending Lane B verdict).
- Falsifier. Frozen CI language vs the fresh WNBA Elo baseline (carryover ρ ≡ league
  default); continuity index must exhibit cross-team variance in the early seasons — a
  near-constant index is an automatic drop.
- Expected direction. ΔLL < 0 vs plain fresh Elo, concentrated in the first ~10 games of
  each season (where priors dominate) and for high-churn teams.
- Kills it fast. Lane B verdict FAIL/insufficient ⇒ NOT_RUN, no NBA evidence may be
  imported as WNBA evidence (plan §3). Continuity no-variance ⇒ drop.

## 3. Protocol sketch for the successor scored cycle(s)

1. **Train-only selection.** Every free parameter (SOS β; split λ; carryover ρ; interaction
   block membership and bucket edges; availability γ) is fit on a train-INTERNAL
   rolling-origin time-split, then frozen at registration. No test-window peeking at any
   point before the frozen walk-forward evaluation.
2. **Windows (new only).**
   - NBA: 2016+ via Lane A (only if the rights verdict clears). The 2009–2015 window is
     SPENT — no K/HCA/rest/form re-grid there, ever.
   - NFL: only 2026 forward is genuinely new. That is thin (~270 regular-season games/yr);
     the honest design is train-internal validation now + PROSPECTIVE accrual of 2026+
     windows, with any NFL OOS report deferred until ≥2 new seasons exist. Do not present
     a 1-season NFL OOS as decisive.
   - WNBA: full fresh program on its own data (pending Lane B), independent splits.
3. **Frozen trial budget: ≤9 arms total**, registered before any test-window look:
   (1) B0 constant; (2) league B1* own-Elo (NBA K=32/HCA=100, NFL K=40/HCA=0 — frozen from
   the terminal cycles, mandatory baseline); (3) H-C1 SOS-adjusted Elo; (4) H-C2 split-Elo;
   (5) H-C3 availability arm (only if the source clears; else slot released, NOT reallocated);
   (6) H-C4 NBA interaction block; (7) H-C4/H-C7 NFL interaction arm (prospective);
   (8) H-C5 WNBA continuity arm; (9) ONE reserve slot, must be specified in the freeze
   document before any test look; unused = released. Shuffled negative controls are
   diagnostic arms: reported, never counted as candidate wins.
4. **Metrics + uncertainty.** Log loss primary; Brier + reliability curve + calibration
   slope secondary (slope band [0.85, 1.15] as in the terminal protocols); CIs from the
   same paired date-cluster bootstrap machinery as the terminal cycles; T1/T2/T3 gate shape
   inherited (T1: pooled CI excludes 0 AND ≥ half folds negative; T2: slope in band;
   T3: no fold's Brier worse than B0 AND pooled CI vs B0 excludes 0).
5. **Negative controls per hypothesis** (§1 F11): time-shuffled twin with preserved
   marginals. A candidate whose shuffled twin also beats the parent is UN-SCORED pending
   machinery audit — that is a fail of the comparison, not a pass of the mechanism.
6. **Playoffs reported separately**, never pooled into the regular-season headline
   (terminal-cycle precedent: NBA pooled_po n=587, NFL po excluded from the 1865).
7. **Any new scored cycle requires fresh registration + freeze + A7 + owner typed GO at its
   own gate** (plan, Terminal outcomes). This document consumes no GO.
8. **No post-hoc tuning of the dead arms**: rejected/dead arms (NFL HCA constant, NFL
   rest/short-week mains, NBA logistic rest/form layer over Elo) stay dead; they may be
   CITED, never re-fit.

## 4. What remains NOT_RUN and why

- **Pre-game availability/injury features (NBA + NFL): NOT_RUN_PIT.** Candidate archives
  exist (p1ho/nba-injuries, Kaggle 2010–2020, nbainjuries package, a possible nflverse-data
  injuries asset) but none has verified rights, verified official-report provenance, and
  per-record publish timestamps in this lane. Provenance audit is the gate; modeling before
  the audit would be leakage-exposed by construction.
- **NBA 2016+ box-score-derived features: PENDING_LANE_A.** hoopR/sportsdataverse releases
  exist (pbp 2002–2026, nightly builds); the redistribution-rights verdict is Lane A's, not
  this lane's.
- **WNBA features: PENDING_LANE_B.** wehoop (MIT) verified as a package; Lane B owns the
  data-quality/as-of PASS/FAIL verdict. No WNBA mechanism is asserted as feasible before it.
- **NFL interactions on a historical window: NOT_RUN.** 2019–2025 mains are rejected and the
  only truly new NFL data (2026+) accrues prospectively; running interactions on thin
  windows would be underpowered by design.
- **Old NBA window 2009–2015: SPENT** for K/HCA/rest/form — immutable history, closed.
- **MOV/blowout-weighted Elo: OUT** (re-grid of a dead family, no new information source).
- **538 forecasts / closing odds / current-game box scores: banned** by the cycle plan.
- No data was downloaded and no outcome was computed in this lane.

## 5. Source verification log (lane C web budget: 4/4 used)

1. Web search — NBA injury-report archives: [p1ho/nba-injuries-scraper](https://github.com/p1ho/nba-injuries-scraper), [p1ho/nba-injuries](https://github.com/p1ho/nba-injuries) (Fox-Sports-sourced, unmaintained archive), [mxufc29/nbainjuries](https://github.com/mxufc29/nbainjuries), Kaggle "NBA Injuries 2010–2020" — none rights/timestamp-proven ⇒ NOT_RUN_PIT stands.
2. [nflverse/nflfastR-data](https://github.com/nflverse/nflfastR-data) — CC-BY-4.0; data auto-pushed to [nflverse/nflverse-data](https://github.com/nflverse/nflverse-data) releases; post-game-compiled verdict from dispatch upheld.
3. [sportsdataverse/wehoop](https://github.com/sportsdataverse/wehoop) — MIT; WNBA pbp 2002–2026 (ESPN-backed); rosters/standings/crosswalks; nightly/daily rebuilds.
4. [sportsdataverse/hoopR](https://github.com/sportsdataverse/hoopR) — NBA pbp 2002–2026; NBA Stats API + ESPN upstream; release assets rebuilt nightly; license type not stated on page ⇒ rights verdict deferred to Lane A.
