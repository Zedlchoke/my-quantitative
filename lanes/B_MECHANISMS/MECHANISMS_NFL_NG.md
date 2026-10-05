# MECHANISMS_NFL_NG — Lane B, NFL-WINPROB-NG-PREP-V1 (mechanism re-adjudication, design only)

- lane: B_MECHANISMS · task: nflng-b-mech · date: 2026-10-05 · owner round 2026-10-05
- scope: design/research ONLY. No data downloads, no outcome computation, no metrics on real
  outcomes. This document proposes candidate mechanisms for the successor protocol lane; it
  authorizes nothing, registers nothing scored, consumes no GO.
- language law (inherited): calibration/forecasting vocabulary only — no PnL/betting/edge.

## 0. Evidence base (read from bytes this lane; not from memory)

- Terminal cycle: `NFL-WINPROB-SCORED-V1` (TERMINAL, INCONCLUSIVE=true),
  `.../integration/research/control/NFL-WINPROB-SCORED-V1/results/scored_summary.json` +
  `TRIAL_LEDGER.jsonl` (same control dir, 9/9 arms PREREGISTERED then COMPUTED).
- Baseline law: **B1\* = B1-c, own-Elo K=40, HCA=0, γ=2/3**; pooled regular-season LL
  0.6407 (n=1865) vs B0 0.6935; ΔLL(B1\*, B0) = −0.0528 [−0.0676, −0.0380]. Any new
  mechanism must beat B1\*, not merely B0.
- Rejected in 2019–2025 (immutable, never re-fit):
  - H2 league-constant HCA: B1-d vs B1-c = +0.0046 [−0.0035, +0.0125] (K=20 pair +0.0049
    [−0.0031, +0.0128]) → REJECT. Note the frozen protocol's own reading: a reject means
    "constant HCA does not calibrate in the test window", not "no home effect exists".
  - H3 rest/short-week MAIN effects: B2-a vs B2-b = +0.0001 [−0.0011, +0.0012] → REJECT.
  - Logistic rest/form layer over elo_diff: B2-a vs B1\* = +0.0017 [−0.0053, +0.0088],
    3/7 folds negative → T1 FAIL. **The additive-feature-over-elo_diff shape is DEAD in
    both terminal cycles (NBA and NFL).**
- Spent-window law: TEST 2019..2025 is spent for K/HCA/rest/form mains and for reuse as a
  new hypothesis-testing window. Genuinely new NFL evidence = 2026 forward, PROSPECTIVE
  ONLY from a real freeze/prediction timestamp. TRAIN-INTERNAL work on the 2000–2018+
  train seasons is design-admissible now (rolling-origin inside train; no test-window
  peeking; this PREP cycle runs none of it — scoring belongs to a future gated cycle).
- Frozen semantics inherited verbatim (PROTOCOL_EVAL_NFL, NFL-WINPROB-PREP-V1): kickoff-
  grain as-of law (admissible set = completed games with kickoff strictly < kickoff(G);
  simultaneous kickoffs never inform each other); TIE LAW (binary label, ties excluded
  from primary scoring/training with disclosed counts, S=0.5 update convention);
  neutral-site law (§8.4, conditional on a Lane A flag); fallback law (§0); leakage laws
  (own-data only, no shipped ratings/odds ever as inputs, quarantined at load);
  franchise-lineage continuity; trial accounting (every evaluated config counts).

## 1. Shape law for new signal (binding on every candidate below)

1. **Replacement-rating or rating-input shape only.** New signal enters INSIDE the rating
   argument (`/400` logistic argument) as a modification of the B1\* stream or its
   season-start state — never as an additive logistic feature stapled to `elo_diff`
   (dead shape, §0). Any candidate arm must reduce EXACTLY to B1\* at a designated null
   parameter value (designed null parent; built-in capacity check).
2. **One new information source or one re-weighting of the existing source per arm.** No
   term-fishing: each arm carries at most 1–3 frozen scalars, fit train-internally, then
   frozen at registration. All fit configurations count into trial accounting.
3. **Each candidate is evaluated train-internally on 2000–2018+ BEFORE any prospective
   window is spent** (kill-fast law, §4). Prospective 2026+ windows confirm pre-registered
   direction; they never power initial detection (power arithmetic in POWER_NOTES.md:
   a single ~270-game season has minimum detectable ΔLL ≈ 0.026–0.056 vs B1\*, far above
   every plausible effect size).

## 2. Candidates (3 proposed + 1 conditional interaction)

Rights preamble (measured this lane): Lane A's audit is NOT yet on disk —
`~/.my-quantitative-data/nfl-ng-prep-v1/` does not exist and
`.worktrees/nfl-winprob-ng-prep-v1/lane-a-data/lanes/` contains only DISPATCH packets.
Every source status below is therefore **PENDING_LANE_A**; the prior lane C web
verifications (V1: nflverse/nflfastR-data CC BY 4.0, post-game-compiled; cycle plan
inheritance) are cited as prior-lane evidence only, not as this cycle's rights verdict.
No candidate's feasibility is asserted ahead of that verdict; STOP CONDITION honored.

---

### C1 — SOS-adjusted Elo (schedule-composited rating) — priority 1

**Mechanism story.** B1\* treats every completed game as identical evidence about a
lineage's level: the update magnitude scales with the opponent's rating through the
expected-score term, but the LEVEL still absorbs schedule composition. In a 17-game
season with large schedule-strength dispersion (division loops + place rotation), a team
that compiled its record against a soft slate carries an inflated rating, and K=40 decays
the error slowly. **Who is mispriced:** teams whose early-season opponents were unusually
weak (or strong) — their next-game probability is biased toward their schedule luck.
**Why now:** the effect should be largest in weeks 1–8, when within-season schedule
imbalance is least washed out, and fade late — a pre-registered heterogeneity prediction
that the evaluation can check as a diagnostic slice (not a gate).

**Operationalization (exact; allowed data only — the audited games/schedule feed).**
All quantities as-of at kickoff grain, strictly-prior completed games only.

- For each completed game g (home i, away j) the B1\* stream yields pre-game expected
  scores E_i(g) = σ((R_i − R_j)/400) (HCA=0 under B1\*), E_j(g) = 1 − E_i(g), at ratings
  as of kickoff(g).
- For lineage i at prediction time t, over i's completed games **of the current season**
  with kickoff < t:
  `SOS_i(t) = (1/n_i) · Σ_g E_i(g)`  (n_i = 0 at season openers ⇒ adjustment ≡ 0).
  `S̄(t) = league mean of SOS_i(t)` across all 32 lineages (keeps the adjustment
  zero-sum; no new data beyond the existing stream).
- Adjusted rating at prediction time: `R̃_i = R_i − β · (SOS_i(t) − S̄(t))`.
- Prediction: `p_home = σ((R̃_H − R̃_A)/400)`, HCA frozen at B1\*'s 0.
- **Update law unchanged:** standard K=40 binary update on the RAW R stream, γ=2/3
  offseason reversion on R. β enters prediction only — the arm is a pure re-weighting of
  the same information set; no double counting, no new update dynamics.
- β: single scalar in Elo points per expected-score unit (SOS ∈ [0,1]); fit train-
  internally (rolling origin inside 2000–2018) on a small pre-registered grid
  (β ∈ {0, 25, 50, 75, 100} — bracketing convention, all fits counted), then frozen.
  **β = 0 reproduces B1\* exactly (designed null).**
- NOT an additive feature next to elo_diff (dead shape, §1.1). Across-season SOS variants
  are a DIFFERENT trial, not registered here.

**$0 source + rights.** Same completed-games feed the terminal cycle already audited
(nflverse games/schedule file; prior lane C verification V1: CC BY 4.0). No new asset.
Rights verdict for this cycle: **PENDING_LANE_A**.

**As-of/PIT discipline.** Pure function of completed games under the kickoff-grain law;
SOS uses the opponent's rating as-of each completed game's kickoff (strictly prior to G);
season-opener rows carry zero adjustment; no retro-corrected tables involved (game
results only). TIE LAW inherited. No shipped rating/odds columns anywhere.

**Frozen falsifier language.** REJECT iff (a) pooled 95% CI of ΔLL(arm, B1\*) on the
primary regular-season set includes 0 or lies entirely > 0, AND/OR (b) fewer than half
of test folds have Δ_f < 0; PLUS the negative control: the **time-shuffled-SOS twin**
(shuffle the SOS adjustment across lineages within each scoring week, preserving
marginals) must NOT achieve a CI excluding 0 — **a "winning" shuffled control un-scores
the candidate** (comparison-machinery fault; candidate returns to design, not scored
PASS). Inherited gates T2 (calibration slope band) and T3 (floor safety vs B0) apply.

**Capacity / power (~270 regular-season games/season).** One scalar; zero-sum
adjustment keeps levels identified; designed null at β=0. Plausible effect vs B1\*:
0.002–0.010 pooled (large: the whole B1\*-vs-B0 dynamic-strength mechanism is 0.053).
Minimum detectable ΔLL (80% power, paired date-cluster bootstrap): ≈ 0.026 at n≈270
(1 season), ≈ 0.019 at n≈540 (2 seasons), ≈ 0.006 train-internally (n≈4800). Single
prospective seasons are starved by construction (POWER_NOTES.md); adjudication lives
train-internally first.

**Kill-fast rule.** No train-internal gain (train-internal ΔLL CI includes 0 or favors
B1\*) ⇒ never register a prospective window; slot released, not reallocated mid-program.
Gain appearing ONLY where B1\* is already strong (late-season slices) ⇒ redundant, drop.

**Train-internal evaluability on 2000–2018+ (before any prospective spend): YES.** Pure
function of the existing games feed; rolling-origin inside train; zero marginal data
cost; cheapest hypothesis to test end-to-end.

---

### C2 — Home/away split rating (venue-role shrunk deviations) — priority 2

**Mechanism story.** The terminal cycle rejected a LEAGUE-CONSTANT HCA, and the frozen
protocol's expected-failure interpretation says exactly what that means: the constant is
mis-specified, not necessarily the effect. Home advantage in the NFL is plausibly
team-heterogeneous (outdoor weather exposure vs domes, altitude, west-to-east early
windows, crowd/operation idiosyncrasies). A league constant is the mean of a heterogeneous
distribution whose spread is large relative to its mean — adding the mean without the
spread slightly HURT calibration (+0.0046 [−0.0035, +0.0125]). **Who is mispriced:**
extreme-profile teams (dome team on the road outdoors; high-altitude hosts) whose
venue-role strength diverges from their common rating. The split rating carries the
spread; the shrunk league scalar h re-estimates the mean jointly with it.

**Operationalization (exact; same games feed, home/away labels only).**
All quantities as-of at kickoff grain.

- State per lineage i: common `R_i` (exactly the B1\* stream: K=40 binary updates,
  γ=2/3 offseason reversion — unchanged), plus two role deviations
  `d_i^H, d_i^A`, initialized 0 at lineage start.
- Prediction: `p_home = σ((R_i + d_i^H − R_j − d_j^A + h)/400)`, where `h` is ONE
  league scalar (train-fit, frozen; re-estimates the league-level home term jointly
  with the deviations).
- Updates after each completed game: R updates exactly per B1\*; deviations update
  in-role:
  `d_i^H ← d_i^H + λ · K · (S_i − E_i)` (home role),
  `d_j^A ← d_j^A + λ · K · (S_j − E_j)` (away role),
  with E from the prediction formula (h and both deviations included).
- Offseason: deviations decay faster than the common stream:
  `d^{H,A} ← γ_d · d^{H,A}`, γ_d < 2/3 (train-fit, frozen).
- Free parameters: λ ∈ [0,1] (deviation learning rate), γ_d, h — three scalars, fit
  train-internally (small pre-registered bracketing grids, all fits counted), then
  frozen. **λ = 0 (equivalently h = 0 with deviations ≡ 0) reproduces B1\* exactly
  (designed null).**
- NOT an additive feature over elo_diff: deviations live inside the rating argument.

**$0 source + rights.** Same games feed; venue role = home/away labels already audited
in the terminal cycle. No new asset. **PENDING_LANE_A** for the cycle's rights verdict
and for the neutral-site flag verdict (inherited §8.4 law: IF a validated neutral-site
flag exists, flagged games are scored with h = 0, receive no deviation updates, and are
excluded from the h-estimation segment, reported separately; ELSE the declared-limitation
branch applies, documented, never silently pooled or dropped).

**As-of/PIT discipline.** Deviations are functions of completed games only, strictly-
prior kickoffs; no new data; TIE LAW inherited (ties update deviations with S=0.5 as an
update convention, excluded from primary scoring/training rows).

**Frozen falsifier language.** REJECT iff (a) pooled 95% CI of ΔLL(arm, B1\*) includes 0
or > 0, AND/OR (b) fewer than half of folds negative; PLUS capacity rejection: if the
train-internal cross-sectional dispersion of (d_i^H − d_i^A) collapses toward 0 after
shrinkage, the data cannot support the extra parameters — drop WITHOUT spending any
window (designed null engaged). Negative controls: **venue-label permutation within
train** (swap labels on a random half of train games for the deviation updates only)
must destroy the train-internal gain (else implementation/leakage, not signal); and the
**time-shuffled twin** rule — a "winning" shuffled control un-scores the candidate.

**Capacity / power.** 64 extra state values (32 lineages × 2 roles) + 3 scalars; the
honest capacity concern is thin per-role samples (~8 home and ~8 away games per team per
season), which mandates fast γ_d shrinkage and makes the degeneracy check the primary
capacity test. Plausible effect vs B1\*: 0.001–0.005 (low end); MDD as in POWER_NOTES —
single seasons starved; train-internal MDD ≈ 0.006 (n≈4800) makes train-internal
adjudication the only realistic path.

**Kill-fast rule.** Train-internal degeneracy (‖d‖ ≈ 0) or no train-internal gain ⇒
stop before any OOS. Venue-permutation control failing inside train ⇒ implementation
audit, not more windows.

**Train-internal evaluability on 2000–2018+: YES** (same feed; degeneracy check runs
first; nothing prospective is spent on this arm before both checks pass train-internally).

---

### C3 — Offseason EPA prior (season-start rating prior, train-only) — priority 3

**Mechanism story.** B1\* carries ratings across season boundaries with a UNIFORM 2/3
reversion — a win/loss-only prior. But 17-game win/loss records are a low-dimensional,
noisy measure of team quality (close-game variance, turnover luck), while prior-season
play-by-play efficiency measures the same underlying quality with far larger effective
sample (≈ 2,000+ plays per team-season). **Who is mispriced:** teams whose W-L record
diverged from their process — a team that won many close games carries an Elo level its
efficiency does not support, and the uniform reversion ignores the divergence; symmetric
for unlucky teams. An efficiency-anchored term at the season boundary moves the season-
start level toward the efficiency-implied level, then lets K=40 take over in-season.

**Admissibility ruling required of the successor protocol (explicit).** The frozen
protocol §7 declares play-by-play-derived IN-SEASON features NOT_RUN_PIT (post-game
compiled, retro-corrected). This candidate does NOT touch an in-season information set:
the ONLY permitted role is a **season-start prior** computed from PRIOR-season completed
games, whose input set is fully determined at each season boundary (last prior-season
kickoff precedes the first prediction of the new season by months — kickoff-grain law
satisfied with maximal margin; retrieval-time snapshot semantics disclosed per protocol
§10.2 precedent, with the pbp snapshot frozen and sha-disclosed at registration; retro-
corrections landing after the freeze are out of scope and disclosed). NEVER an in-season
feature; NEVER a within-season aggregate. "Train-only" in the owner direction is honored
twice: the mapping is fit on train seasons only, and pbp usage is restricted to the
offseason-prior role. If Lane A's pbp audit fails (rights, coverage, snapshot story),
this candidate is **NOT_RUN_PIT** and the slot is released.

**Operationalization (exact).**

- Input: frozen nflverse pbp snapshot (prior lane C verification V1: CC BY 4.0;
  **PENDING_LANE_A** for coverage/versions/snapshot story). Registered team-efficiency
  formula (ONE form, never re-fished):
  `E_i(s−1) = 0.5 · ( off_EPA_per_play_i + def_EPA_per_play_allowed_i )`,
  where `def_EPA_per_play_allowed_i = −(opponents' EPA on plays against i's defense) /
  (those plays)`, both over prior-season regular-season plays of completed games.
- Standardize across the 32 lineages: `z_i(s) = (E_i(s−1) − mean) / sd`.
- Season-start prior: before lineage i's first prediction of season s,
  `R_i ← 1500 + γ·(R_i − 1500) + θ · z_i(s)` with γ = 2/3 frozen (B1\* value) and θ a
  single scalar in Elo points per SD of EPA z (train-fit, frozen; pre-registered
  bracketing grid, all fits counted). **θ = 0 reproduces B1\* exactly (designed null).**
  First season in data and expansion lineages: no term (z undefined ⇒ 0 contribution).
- In-season: UNCHANGED B1\* (K=40 binary updates). No pbp-derived quantity ever enters a
  within-season prediction or update.

**$0 source + rights.** nflverse pbp (nflfastR-data releases), $0; prior lane C
verification V1 says CC BY 4.0 and post-game-compiled (which is exactly why the role is
restricted to season-start priors). **PENDING_LANE_A** — the pbp snapshot audit
(coverage back through the train window, version/sha, attribution chain) is a
prerequisite; until it lands, this arm is design-only and NOT_RUN_PIT.

**As-of/PIT discipline.** Season-grain prior only; input set = prior-season completed
games; mapping θ train-only; snapshot frozen + sha-disclosed at registration; no
current-game or in-season pbp usage anywhere (grep-level and behavioral tests inherited
from protocol §8.9 apply to the prior-computation code as well).

**Frozen falsifier language.** REJECT iff pooled 95% CI of ΔLL(arm, B1\*) includes 0 or
> 0, AND/OR fewer than half of folds negative; PLUS the negative control: **time-shuffled
EPA prior** (shuffle z across lineages at each season boundary, preserving marginals)
must NOT produce a CI excluding 0 — a "winning" shuffled control un-scores the candidate.
Pre-registered diagnostic slice (not a gate): gain concentrated in the first ~6 weeks of
each season, where the prior dominates before K=40 washes it out.

**Capacity / power.** ONE scalar — the cheapest possible new-information arm; θ=0
designed null; degenerate check: if cross-team z dispersion in train ≈ 0 ⇒ drop.
Plausible effect vs B1\*: 0.002–0.008 pooled. MDD arithmetic as POWER_NOTES: single
prospective seasons starved; train-internal MDD ≈ 0.006 at n≈4800 (shortens honestly if
Lane A's pbp coverage starts mid-train — the overlapping window's MDD is recomputed at
registration).

**Kill-fast rule.** Lane A pbp audit fails ⇒ NOT_RUN_PIT, slot released (never
reallocated mid-program). Train-internal rolling-origin fails ⇒ never prospective.

**Train-internal evaluability on 2000–2018+: YES, conditional on Lane A's pbp snapshot
covering (most of) the train window.** nflfastR pbp is publicly documented back to 1999
(prior verification V1); if the audited snapshot starts later, the train-internal
evaluation shortens to the overlap and the shortened power is stated at registration. If
coverage or rights fail ⇒ NOT_RUN_PIT.

---

### C4 (CONDITIONAL) — short-week × away interaction — design-level only; gated on train-internal strength

**Status: CONDITIONAL CANDIDATE. No outcome runs in PREP; may only enter a successor
registration if its pre-registered train-internal gate passes. Default expected
disposition: slot released (starvation arithmetic below).**

**Mechanism story.** The fatigue theory predicts the cost of a ≤6-day week lands
primarily on the ROAD team (compressed travel and preparation; home short-week games are
cushioned by routine and no travel). The terminal cycle tested SYMMETRIC mains
(`short_week_home`, `short_week_away` as separate fitted terms, B2-a/B2-c) — under this
theory the two cells carry OPPOSITE signs, so symmetric mains dilute toward zero; the
H3 rejection (+0.0001 [−0.0011, +0.0012]) is evidence against the symmetric
parameterization, not strictly against the away-cell-only effect. This is why a ONE-CELL
arm is a different hypothesis — but it is adjacent to rejected territory, so it is
conditional and gated, never a free slot.

**Operationalization (exact, IF the gate ever passes).** ONE frozen term inside the B1\*
shape (a restricted-constant adjustment, NOT a fitted logistic layer, NOT a re-grid of
the dead mains):
`p_home = σ((R_i − R_j − δ)/400)` applied ONLY to games where the away team's
rest_days ≤ 6 (rest_days per frozen protocol f2 definition; δ ≥ 0 is the pre-registered
direction: short-week road teams carry a penalty). δ: single scalar, train-fit, frozen.
**δ = 0 reproduces B1\* exactly.** The block is tested jointly (one ΔLL), never
term-fished. HCA/rest MAIN effects are never re-tested anywhere (ancestry veto).

**Gate (pre-registered, binding).** This arm may be REGISTERED for a prospective window
only if BOTH hold on train-internal rolling-origin evidence (2000–2018):
(i) the away-short-week-slice ΔLL CI excludes 0 in the pre-registered direction; and
(ii) the pooled train ΔLL does not contradict the direction. Any failure ⇒ slot released.

**$0 source + rights.** Same games feed (kickoff timestamps already audited in the
terminal cycle). **PENDING_LANE_A** for the cycle's rights verdict and the kickoff-
reliability/fallback finding (§0 fallback law; if the fallback activates at some season
X, the gate window shortens accordingly).

**As-of/PIT.** Schedule-derived (days between strictly-prior kickoffs); postponement
handling inherited (rest_days ≥ 0 checks, protocol §8.5); no new data.

**Frozen falsifier.** Same CI + fold rule vs B1\*; negative control = time-shuffled
short-week-away labels (preserve the cell's marginal count per season) — a "winning"
shuffled control un-scores the candidate.

**Capacity / power — the honest arithmetic.** The away-short-week cell is ~15–20
games/season (mostly Thursday games). Train-internal slice ≈ 340 cells (19 seasons):
MDD ≈ 0.08 (slice-paired SD ≈ 0.5) — likely ABOVE any plausible interaction effect
(0.01–0.03) ⇒ the gate itself will probably fail. Prospective slices are worse (5
seasons ≈ 90 cells ⇒ MDD ≈ 0.15). **This candidate is starved BY DESIGN; it is recorded
because the owner asked for it as a conditional, and the gate is expected to release the
slot.** Only a freak train-internal effect ≥ ~0.08 on the slice keeps it alive.

**Kill-fast rule.** The gate IS the kill-fast rule. No prospective spend before the gate;
no gate re-fitting after any outcome is observed.

**Train-internal evaluability: YES** (that evaluation is the gate; it precedes and
replaces any prospective decision).

## 3. REJECT section (ancestry vetoes and dead shapes — cited, never re-fit)

1. **MOV / blowout-weighted Elo** — OUT per ancestry: a re-grid of the dead Elo-update
   family with no new information source; the frozen protocol already excluded margin
   multipliers (§7 NOT_RUN_SCOPE). Re-litigating it would burn trial budget on a spent
   mechanism.
2. **Any re-grid of K, league-constant HCA, rest/short-week/form MAIN effects** on
   2019–2025 or any other window — rejected in the terminal cycle (H2 +0.0046
   [−0.0035, +0.0125]; H3 +0.0001 [−0.0011, +0.0012]); the window is spent; mains stay
   dead. C1–C3 do not touch these parameters (frozen at B1\* values); C4 is a one-cell
   restricted constant, gated, not a main-effect re-test.
3. **Additive logistic features over elo_diff (any new B2-style features)** — DEAD in
   both terminal cycles (NFL B2-a vs B1\* T1 FAIL; NBA equivalent). No candidate uses
   this shape.
4. **γ (season-reversion) re-tune** — protocol §7 NOT_RUN_SCOPE; fixed 2/3; re-tuning on
   any window = a new trial on spent mechanisms. C3 keeps γ frozen and adds a separate
   prior term.
5. **In-season pbp-derived features (EPA/success rate/WP as within-season predictors)** —
   NOT_RUN_PIT per frozen protocol §7 (post-game compiled, retro-corrected by
   maintainers). Only the offseason-prior role survives, as C3.
6. **Pre-game availability/injury features (NFL)** — NOT_RUN_PIT (prior menu F4: no $0
   source with verified rights AND per-record publish timestamps); not an owner priority
   this round; stays unproven, needs a provenance audit before any modeling.
7. **538 forecasts, closing/market odds, current-game box scores** — banned by the cycle
   plan; quarantined at load per leakage laws.
8. **Travel-distance / timezone buckets × away (prior menu F6)** — AVAILABLE but
   UNSELECTED: not an owner priority; the owner's ≤3 candidate slots are filled by
   C1–C3; slice starvation similar to C4 without the conditional mandate; historical
   schedule-snapshot amendments add as-of risk (protocol §7). Recorded as a possible
   future conditional arm with the same gate discipline as C4.

## 4. Evaluation-order law (train-internal first; applies to every candidate)

1. Lane A data verdicts land (rights, coverage, as-of story, neutral-site flag,
   kickoff reliability). Any failure ⇒ PENDING_LANE_A / NOT_RUN_PIT as designated; slots
   released, never reallocated mid-program.
2. Train-internal rolling-origin adjudication inside 2000–2018+ (fit + validate on train
   seasons only; every grid fit counted into trial accounting). Designed-null arms
   (β=λ=θ=δ=0) are checked to reproduce B1\* bit-for-bit before any other number is
   believed.
3. Only candidates with a train-internal CI excluding 0 in the pre-registered direction
   graduate to a prospective registration; the successor protocol lane freezes the arm
   set (≤9 arms incl. B0 + B1\*), the negative controls, the gates, and the ≥2-new-season
   reporting rule BEFORE any 2026+ look.
4. Prospective 2026+ accrual is append-only, timestamps strictly before kickoff UTC;
   already-played 2026 games are NOT_RUN for prospective scoring and never presented as
   pre-game forecasts. A 1-season OOS report is never decisive (POWER_NOTES.md); strong
   conclusions require ≥2 new seasons AND effects at or above the detectable scale.

## 5. What remains NOT_RUN / PENDING in this lane

- **PENDING_LANE_A (all candidates):** rights/coverage/as-of verdicts; neutral-site flag
  verdict; kickoff-reliability/fallback finding; pbp snapshot audit (C3).
- **NOT_RUN (this lane, by design):** all train-internal fits and scorings; all
  prospective computations; any metric on real outcomes. No data downloaded; no outcome
  computed; no frozen artifact of any cycle touched.
