# PROTOCOL_DRAFT_NBA_NG — successor scored-cycle protocol DRAFT (Lane C, NBA-WINPROB-NG-PREP-V1)

- Cycle: `NBA-WINPROB-NG-PREP-V1` · Lane: `C_PROTOCOL` · Task: `nbang-c-proto` · Date: 2026-10-05
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/nba-winprob-ng-prep-v1/integration`
  (branch `orca/nba-winprob-ng-prep-v1-integration`, dispatch_sha = `01e747e74303f06e5432b68b5a19180b5635501f`)
- Status: **DESIGN / DRAFT PREREGISTRATION ONLY.** No evaluation was executed, no outcome
  metric computed, no data touched, no git operation performed in this lane. Every constant
  below is a preregistration sketch for a successor cycle, not a result.
- Proposed successor cycle id: **`NBA-WINPROB-NG-SCORED-V1`** (registration, freeze, A7 and
  owner GO for it are FUTURE events; this cycle registers no GO phrase and consumes none).
- Binding effect: the successor scored cycle's plan must inherit Sections 1–12 of this
  document **verbatim** BEFORE any outcome is observed (freeze-before-scoring doctrine).
- Language law (inherited): calibration/forecasting vocabulary only. No PnL, no betting, no
  market comparison, no "edge" vocabulary anywhere in any output of the successor.

## 0. Binding laws inherited (restated, not redefined)

From terminal cycle `NBA-WINPROB-SCORED-V1` (TERMINAL, NO_PROGRAM_PASS; A7 terminal CONFIRM;
GO consumed at its own gate 2026-10-05T00:26:44Z then extinguished at close — no GO survives
from any earlier cycle):

- **Baseline law.** NBA B1\* = own-Elo **K=32, HCA=100**, γ=0.75, binary updates (B1-d of the
  terminal cycle). Spent-window evidence (citable context only): pooled RS LL 0.5987
  (n=8369) vs B0 0.6769; ΔLL −0.0782 [−0.0875, −0.0687]; HCA alive: B1-d vs B1-c −0.0215
  [−0.0271, −0.0157]; calibration slopes B2-a 0.9894, B1-d 0.8606 (both inside [0.85, 1.15]).
  B1\* constants are FROZEN — carried verbatim, never re-tuned. Any new mechanism must beat
  **B1\***, not merely B0.
- **Spent-window law.** NBA seasons 2009–2015 (538 nbaallelo test window) are **SPENT**:
  K/HCA/rest/form were grid-searched and scored there by the terminal cycle. No re-grid of
  K/HCA/rest/form on 2009–2015, ever, in any lane. The window is citable context, never
  scoreable. New evaluation window = NBA seasons **2016+** (hoopR corpus) only.
- **Dead-mechanism law.** Additive logistic-over-Elo feature layers (rest/form) are DEAD
  (terminal T1 FAIL: B2-a vs B1\* CI [−0.00326, +0.00128], 5/7 folds negative; H3 borderline
  at CI hi −0.0000022). NFL HCA constant and NFL rest/short-week mains are REJECTED in their
  windows. Dead arms may be CITED, never re-fit. MOV/blowout-weighted Elo is a re-grid of a
  dead family — banned. Replacement-rating shapes are the preferred mechanism form.
- **Trial law.** Every evaluated configuration counts into the observed denominator; freeze
  before scoring; negative terminal outcomes preregistered; missing evidence is `NOT_RUN`,
  never inferred `PASS`. Any arm, feature, fold, metric, or threshold introduced after any
  real outcome is observed is a NEW registered trial outside the budget, no exceptions.
- **Bootstrap machinery.** Paired per-game ΔLL; 95% CI by block bootstrap resampling game
  DATES with replacement (clusters = dates: same-date games share rating state and schedule
  context); 10,000 resamples; percentile CI; per fold AND pooled; Δ < 0 favors the arm.
- **As-of law v2 (this draft, restated in §4.1).** Admissible information for game G =
  {all completed games with LOCAL game date strictly < local game date(G)} + static identity
  mappings. Same-day games never inform each other.
- **Playoff separation law.** Regular season is the only headline. Playoffs, play-in, and
  the NBA Cup final are scored with the same frozen fold models and reported SEPARATELY;
  never pooled into primary aggregates; never silently dropped.
- **Terminal-cycle precedent values** (for comparability, citable only): B0 LL 0.6769,
  B1\* LL 0.5987, playoff segment n=587, ledger 9 PREREGISTERED + 9 COMPUTED rows, repro twin
  byte-identical (sha256 `8aa680ed…de52b`).

## 1. Split design (FROZEN at this draft; the successor may not alter it)

### 1.1 Eras and the cutoff

All season keys are ESPN **ending-year** keys (2016 = 2015-16 season), per the lane A data
contract (WINPROB-NG-PREP-V1 `A_NBA_POST2015/NBA_POST2015_SOURCES.md`) and this cycle's
PLAN task 1. The hoopR corpus spans seasons 2016–2026 (14,254 schedule rows measured;
2026 Finals ended 2026-06-14 < cycle epoch 2026-10-05; season 2027 unplayed at epoch).

- **Spent era:** seasons ≤ 2015 (538 corpus, ends 2015-06-16). Citable context, never
  scoreable, never re-gridded.
- **WARM-UP era:** seasons **2016, 2017** (2015-10-28 … 2017-06-13). Rating streams run and
  update under each arm's own frozen constants; predictions are computed for stream
  maintenance but are **NEVER scored, NEVER used in any selection metric, NEVER reported**.
  Warm-up outcomes remain legal TRAINING rows for refit arms (B0) — the restriction is on
  scoring/selection metrics, not training data.
- **SELECTION era (train-internal):** seasons **2018, 2019, 2020, 2021**.
- **OOS era (walk-forward):** seasons **2022, 2023, 2024, 2025, 2026**.

**FROZEN SPLIT CUTOFF: `2021-08-01T00:00:00Z` (tip-UTC instant).**
Season 2021's last completed game is 2021-07-21; season 2022's first is 2021-10-19 — the
cutoff sits inside the off-season gap. Every game with tip-UTC `< 2021-08-01T00:00:00Z` is
selection-era; every game at or after it is OOS-era. The cutoff is frozen by this document;
the successor inherits it verbatim and may not move it.

### 1.2 Selection folds (train-internal rolling-origin)

- Selection fold S_k (k = 1..4): test season = 2017+k (i.e. **2018, 2019, 2020, 2021**);
  train = all completed seasons strictly before the test season (warm-up seasons contribute
  training rows and stream history, never scored rows).
- Every free parameter of every candidate arm — SOS coefficient β; split weight λ; prior
  strength ρ; interaction-block membership and bucket edges; any prior-seed scale — is fit
  ONLY on S1–S4 under a **frozen selection rule**: minimize pooled selection-era log loss
  over the pre-registered candidate values, tie-broken by fold-majority, then by smaller
  parameter value. The chosen value is frozen at the successor's registration. No OOS-era
  game may inform selection; no selection metric may be computed on any OOS-era outcome.
- Anomaly seasons 2020 (COVID, ends 2020-10-11, incl. bubble) and 2021 (72-game, empty
  arenas early) sit INSIDE the selection era by design: selection must be robust to them,
  and sensitivity columns (§9) must be produced for them at selection time too.
- Train-internal kill tests (one per mechanism, frozen by Lane B / §3) run on S1–S4 only.
  A mechanism that fails its train-internal kill test is **NOT_RUN at OOS**, its slot is
  **RELEASED** (never reallocated), and the ledger row records the kill — the release is
  itself a registered selection event on train-internal data, which is legal precisely
  because it never touches OOS-era outcomes.

### 1.3 OOS walk-forward folds (frozen lists)

- OOS fold k (k = 1..5): test season = 2021+k; test rows = every deduped completed
  REGULAR-SEASON game of that season; train = all completed seasons strictly before it
  (expanding window; selection-era seasons are legal training data — standard walk-forward;
  the test seasons themselves were never seen by selection).
- **FROZEN OOS season list: [2022, 2023, 2024, 2025, 2026]** — all five complete at the
  cycle epoch (2026 Finals ended 2026-06-14). The successor's byte audit re-verifies
  per-season completeness (`status_type_completed`, dedupe law); any season found
  incomplete in the audited bytes drops from the list automatically (placeholder rule) —
  the modeler may never add, remove, or reorder test seasons after seeing outcomes.
- B1\*-family rating streams are fully determined by the as-of law and frozen constants
  (not "refit"); B0 refits per fold on train regular-season rows.
- Fold counts: 5 OOS folds ⇒ T1's fold-majority bar is **≥ 3 of 5 folds negative**.
- Expected OOS volume (citable design estimate, not a result): ≈ 6,100 RS games (≈1,230/season),
  comparable in kind to the terminal cycle's 8,369. Honest power caveat: mechanisms with
  expected ΔLL ≲ 0.002 vs B1\* may land INCONCLUSIVE at this n. INCONCLUSIVE is a valid
  pre-registered terminal; no threshold relaxation exists.

### 1.4 2026-27 (season 2027) = PROSPECTIVE ONLY

Games of season 2027 are unplayed at the cycle epoch. They are **never** part of the
historical walk-forward. They accrue only under the prospective append-only ledger law
(§8): rows timestamped strictly before tip UTC. **Every game already played before the
successor's freeze is NOT_RUN prospective** — it belongs to historical OOS scoring only and
may never be claimed as prospective validation.

## 2. Arm budget sketch (≤ 9 frozen arms incl. B0; frozen BEFORE any test look)

Two ledger classes, one budget. `class=PRIMARY` arms can produce PASS; `class=DIAGNOSTIC`
arms (negative-control twins, baseline-validity ablation) are registered pre-look, ledgered,
reported — and **never counted as candidate wins** (diagnostics sit outside the 9-slot
candidate budget, mirroring the NG sketch §3.3, and cannot pass any T-gate by construction
of §6).

| Slot | Arm | Class | Status at draft | Role |
|---|---|---|---|---|
| 1 | **B0** — constant home-win rate, per-fold train-only refit | PRIMARY | FROZEN | floor; premise reference |
| 2 | **B1\*** — own-Elo K=32, HCA=100, γ=0.75, binary updates (verbatim §3.2) | PRIMARY | FROZEN | mandatory baseline; never re-tuned |
| 3 | **M1** — H-C1 SOS-adjusted Elo (replacement rating) | PRIMARY | CONDITIONAL — Lane B gate | candidate |
| 4 | **M2** — H-C2 home/away split ratings | PRIMARY | CONDITIONAL — Lane B gate | candidate |
| 5 | **M3** — H-C4 fatigue×venue interaction block (b2b_away / 3in4_away / travel_bucket_away / tz_shift_away; joint block) | PRIMARY | CONDITIONAL — Lane B gate | candidate |
| 6 | **M4** — F8 pace/efficiency train-only prior as rating INITIALIZATION | PRIMARY | CONDITIONAL — Lane B gate + Lane A rights/PIT gate | candidate |
| 7 | H-C3 pre-game availability-adjusted rating | PRIMARY | **NOT_RUN_PIT** (no rights+timestamp-proven $0 source; expected RELEASED) | conditional candidate |
| 8 | Reserve | — | **RELEASED** at draft | reserve rule §2.2 |
| 9 | Reserve | — | **RELEASED** at draft | reserve rule §2.2 |

- Expected used budget: ≤ 6 PRIMARY arms. Budget is binding at ≤ 9; a smaller frozen roster
  is a feature, not slack.
- CONDITIONAL means: the arm exists in the successor freeze ONLY IF (a) Lane B of THIS cycle
  advances the mechanism (≤ 3–4 mechanisms per PLAN task 2), and (b) its $0-source /
  rights / PIT verdict clears (Lane A for M4's hoopR-derived aggregates; provenance audit
  for H-C3). A mechanism that fails train-internal kill or loses its gate is NOT_RUN /
  RELEASED. **Released slots are never reallocated.** No mechanism not named above may be
  swapped in after any outcome is observed.
- Banned arm shapes (would be new trials outside this budget if introduced): additive
  logistic-over-Elo layers; MOV/blowout-weighted Elo; any K/HCA/rest/form re-grid (on any
  window); 538 `forecast`-derived arms; market-line arms (`game_spread`, `home_favorite` —
  banned market data per PLAN, also timestamp-semantics UNVERIFIED); current-game box scores.

### 2.2 Reserve-slot rule (specified pre-look)

Slots 8–9 are RELEASED by this draft. The successor's freeze document MAY bind a released
slot to exactly one pre-specified arm BEFORE any OOS-era outcome is observed — binding after
any look is forbidden; an unbound reserve stays released; a released slot is never
reallocated to an ad-hoc arm. The first pre-specified candidate for a reserve binding, should
the successor choose one, is the HCA ablation below (then it is class DIAGNOSTIC and the
slot remains released — a diagnostic binding consumes nothing).

### 2.3 Diagnostic arms (registered pre-look; class DIAGNOSTIC; outside the 9)

- **NC-M1** time-shuffled-SOS twin of M1; **NC-M2** venue-label-permuted twin of M2;
  **NC-M3** time-shuffled travel-bucket twin of M3; **NC-M4** shuffled-prior twin of M4.
  Twins preserve per-team/per-season marginals exactly (verified pre-look, pitfall §11.12).
- **B1-HCA0** — own-Elo K=32, **HCA=0**, γ=0.75: baseline-validity ablation for the new
  window (HCA shrinkage post-2015 is documented league-wide; if HCA=100 stopped helping,
  B1\* would be a mis-specified baseline and every ΔLL(·, B1\*) mis-attributed). Registered
  comparison: ΔLL(B1\*, B1-HCA0) pooled CI. This is a byproduct re-test of H2 on 2016+ —
  it can never PASS the program; if the CI favors B1-HCA0 or includes 0, B1\*'s baseline
  status on the new window is flagged in the verdict report (does NOT by itself void the
  cycle; it modulates interpretation, §7.3).

## 3. Arm specifications

### 3.1 B0 — constant home-win probability (floor)

`p̂_fold = mean(y)` over the fold's TRAIN regular-season rows (intercept-only logistic =
train home-win rate). Refit per fold (selection and OOS folds both refit). No inputs.
Exclusions follow the game-universe law (§4.2): completed, deduped, non-All-Star,
RS-only rows.

### 3.2 B1\* — own-Elo, FROZEN VERBATIM (never re-tuned)

Inherited byte-for-byte from the terminal protocol (its §2 B1-d) + PLAN baseline law:

- Stream: one rating per franchise lineage (one lineage = one rating stream; static identity
  mapping, census-tested). Every lineage starts at R=1500 at its first completed game in the
  audited corpus (see burn-in law below). The stream updates on EVERY completed game —
  regular season, playoffs, play-in, Cup final (completed-games law; all update, only RS
  rows are ever scored in primary).
- Season-boundary rule: before a lineage's first PREDICTION of a new season key,
  `R ← 1500 + 0.75·(R − 1500)`. γ = 0.75 FIXED.
- Prediction: `p_home = 1 / (1 + 10^{−(R_H + 100 − R_A)/400})`, R as of the close of all
  games with local game date strictly < game date(G).
- Update: `R ← R + 32·(S − E)`, S ∈ {1,0} realized, E = expected score. Binary result only,
  NO margin-of-victory multiplier. All updates for date d applied only AFTER all predictions
  for date d.
- HCA = 100 applied inside both prediction and update, everywhere (declared limitation re
  neutral sites; bubble sensitivity segment §9).
- **Burn-in law (this draft's addition, pre-registered):** the stream cold-starts at 1500 on
  the first hoopR completed game (2015-10-28) and the WARM-UP era (2016–2017, ≈164 completed
  games per lineage before the first scored selection fold) exists precisely so that no
  scored prediction is made from a cold stream. Adequacy of warm-up length is re-arguable
  ONLY in the successor's freeze document, pre-look. **538-era warm-start of the stream is
  NOT_RUN** (design decision, §12): it would require carrying ratings across a source seam
  (538→hoopR) and invites spent-window contamination arguments; the conservative cold-start
  + warm-up design is adopted instead.
- Any change to any constant above (K, HCA, γ, update rule, lineage map semantics) = a NEW
  registered trial outside this budget, no exceptions.

### 3.3 M1 — SOS-adjusted Elo (H-C1), replacement-rating shape

From the completed-games-only results feed:
`SOS_i(t) = mean over i's completed games of opp_Elo_at_tip`;
input rating `R̃_i = R_i − β·(SOS_i − league_mean_SOS)`;
`p = σ((R̃_home − R̃_away + 100)/400)` (B1\*'s frozen HCA/scale).
β selected on S1–S4 over a pre-registered candidate grid (successor freeze pins the grid,
pre-look), then frozen. NOT an additive feature next to elo_diff. Frozen falsifier: §6.
Train-internal kill test (Lane B pins exactly, pre-look; sketch): no selection-era gain vs
B1\* on early-season games (games 1–20 of season) ⇒ kill.
Negative control NC-M1: time-shuffled SOS twin (same marginals).

### 3.4 M2 — home/away split ratings (H-C2)

Two ratings per lineage: `R_home`, `R_away`; the venue-role rating is the one updated at each
game, shrunk toward the common rating with weight λ
(`R_role ← (1−λ)·R_role + λ·(R_common + K·outcome_term)` shape; exact update frozen at the
successor's registration); prediction `p = σ((R_home_i − R_away_j + 100)/400)`.
λ selected on S1–S4, then frozen. Extreme λ reproduces B1\* — the designed null parent.
Kill tests (sketch; Lane B pins): venue-label permutation within selection era must destroy
any gain; rating-split collapse (‖R_home − R_away‖ ≈ 0) = capacity failure ⇒ drop.
Negative control NC-M2.

### 3.5 M3 — fatigue×venue interaction block (H-C4), joint block only

ONE frozen block, never term-fished: `b2b_away`, `3in4_away`, `travel_bucket_away`
(miles since last game: 0–1000 / 1000–2000 / 2000+), `tz_shift_away` (≥2 timezone crossings
on road trip), as interactions with (or restricted to) away games, entering the frozen B1\*
shape. Block membership and bucket edges selected jointly on S1–S4, then frozen. Tested
jointly (ONE ΔLL), never per-term. Per the dead-mechanism law this is a DIFFERENT
hypothesis from the rejected main effects (sign structure: cost lands on the ROAD team),
not a re-test. Postponement as-of handling: rest/travel derive from games actually played
at actual dates (§4.1); announced-but-unplayed postponements contribute nothing.
Kill test (sketch): no selection-era block gain vs B1\* ⇒ kill, and the NFL interaction slot
analogy is moot here (NBA-only cycle; NFL belongs to the other owner chat's cycle).
Negative control NC-M3: time-shuffled travel buckets.

### 3.6 M4 — pace/efficiency prior-seeded Elo (F8), initialization only

Prior-season pace/efficiency aggregates (hoopR-derived, train-only, expanding-window as-of
computation enforced in code) serve as the season-start rating INITIALIZATION/prior — a
replacement-rating mechanism (e.g. season-boundary reversion target tilted toward the
prior), never an in-season feature and never an additive logistic layer (dead shape).
**Gates:** (a) Lane B advances it; (b) Lane A of this cycle verifies rights + coverage +
PIT for every underlying aggregate (prior aggregates must use ONLY games completed before
the season-start cutoff; any aggregate crossing the prediction cutoff = leakage = kill).
Kill test (sketch): shuffled-prior control NC-M4 and no selection-era gain ⇒ kill.

### 3.7 H-C3 — availability-adjusted rating: NOT_RUN_PIT

No $0 source with verified rights AND per-record publish timestamps ≤ tip − report cadence
is known (WINPROB-NG-PREP-V1 lane C verification log). It stays NOT_RUN_PIT unless a source
clears a provenance audit BEFORE the successor's freeze. If it never clears: slot 7 RELEASED,
never reallocated. NO retro-filling from post-game box-score minutes (leakage by
construction).

## 4. Scoring rules, as-of law, game universe

### 4.1 As-of law v2 and time grain

- Admissible information set for game G = {all completed games with LOCAL game date strictly
  < local game date(G)} + static identity mappings. Same-day games never inform each other,
  even where true tip times differ (conservative, terminal-comparable; finer tip-time as-of
  is NOT_RUN_SCOPE, §12 — the data supports it, adopting it is a law change that must be
  pre-registered in a future freeze before any look).
- Canonical fields (from Lane A contract, subject to this cycle's Lane A confirmation):
  `game_id` (ESPN event id) primary key; tip instant `game_date_time` (local-with-offset)
  with UTC twin `start_date`; `game_date` = local date used by the as-of law; tip-UTC is
  authoritative for the prospective ledger (§8) and the split cutoff (§1.1).

### 4.2 Game-universe law (dedupe/exclusion)

One prediction row per `game_id`. Include `status_type_completed == True`; exclude All-Star
EAST/WEST pseudo-team rows; flag and separately report the 2023+ NBA Cup final
(`notes_headline` "NBA In-Season Tournament Championship"); account postponed duplicate
listings (makeups keep their own game_id and their ACTUAL played date governs as-of);
re-derive per-season PLAYED counts after dedupe (raw file counts over-count). Scoring row =
home perspective, `y = 1{home win}` from `home_score`/`away_score`. This cycle's Lane A
(NOT_RUN at draft time, §13) owns the byte-level confirmation; until it lands, the
predecessor lane A contract + PLAN task 1 are the authority of record.

### 4.3 Training rows

Refit arms (B0; any successor refit variant) train on REGULAR-SEASON completed rows of train
seasons only. Playoff/play-in/Cup rows never enter training, but DO update rating streams
(completed-games law). Zero non-RS rows in any training set and any primary aggregate
(tested, §11.6).

## 5. Metrics + uncertainty (inherited verbatim)

- Probabilities clamped to [1e-15, 1−1e-15].
- PRIMARY: mean log loss `LL = −mean[y·ln p + (1−y)·ln(1−p)]`, per fold and pooled OOS RS.
- Secondary: Brier `mean[(p−y)²]`; reliability = 10 equal-width bins on p with (n, mean p,
  observed rate); calibration slope = binomial-GLM (logit link) coefficient of `logit(p)` in
  `outcome ~ 1 + logit(p)`. Slope 1 = calibrated; <1 overconfident; >1 underconfident.
  Pooled and per fold.
- Paired comparisons: per-game `ΔLL = LL(arm) − LL(reference)` on identical game sets;
  95% CI by date-cluster block bootstrap (clusters = local game dates), **10,000 resamples,
  seed 20261005** (this draft's pre-registration; the successor freeze may pin a different
  seed pre-look only), percentile method. Per fold AND pooled.
- Sign convention: Δ < 0 favors the arm; Δ > 0 favors the reference.

## 6. Gates (T1/T2/T3 shapes inherited) and terminal predicates

For a scored candidate arm M (references: B1\*, B0; "CI" = date-cluster bootstrap 95% CI;
F = 5 OOS folds; fold-majority = ≥ 3 of 5):

Program PASS for M requires ALL of:
- **T1 (discriminative gain over B1\*):** pooled ΔLL(M, B1\*) CI entirely < 0 AND
  Δ_f(M, B1\*) < 0 on ≥ 3 of 5 folds.
- **T2 (calibration):** pooled calibration slope of M ∈ [0.85, 1.15].
- **T3 (floor safety):** no fold where Brier(M) > Brier(B0), AND pooled ΔLL(M, B0) CI
  entirely < 0.

REJECT (negative terminal for the program) if ANY of:
- **R1:** CI of pooled ΔLL(B1\*, B0) includes 0 or lies entirely > 0 on the NEW window → the
  inherited baseline adds nothing over the constant baseline on 2016+ → program premise
  fails at this grain. (This is a genuinely open possibility: H1/H2 were adjudicated alive
  on the SPENT window only.)
- **R2:** every scored candidate's pooled ΔLL(·, B0) CI lies entirely > 0.
- **R3:** for a candidate M: pooled ΔLL(M, B1\*) CI entirely > 0 AND T2 violated for M.

INCONCLUSIVE: all decision CIs include 0 while T2 holds for the best candidate → no PASS;
no re-tuning, no threshold relaxation, no metric substitution; continuation requires a new
registered cycle with a NEW mechanism claim.

Hypothesis-level verdicts (exactly, per mechanism, from the NG sketch falsifiers):
- M1 REJECT iff pooled CI of ΔLL(M1, B1\*) includes 0 or favors B1\*, or < 3 of 5 folds
  negative — OR its shuffled-SOS control achieves a CI excluding 0 (machinery fault ⇒
  un-scored, §6.1).
- M2 REJECT iff pooled CI of ΔLL(M2, B1\*) includes 0 or ≥ 3 of 5 folds non-negative — OR
  the rating split collapses (‖R_home − R_away‖ ≈ 0).
- M3 REJECT iff pooled CI of the joint-block ΔLL(M3, B1\*) includes 0 (block never
  decomposed post hoc).
- M4 REJECT iff pooled CI of ΔLL(M4, B1\*) includes 0 or ≥ 3 of 5 folds non-negative.

### 6.1 Negative-control law (per hypothesis)

- Each scored mechanism carries exactly one pre-registered time-shuffled/permuted twin
  (§2.3) with preserved marginals, run in the SAME single scored batch.
- **Control-beats-parent ⇒ machinery audit; hypothesis UN-SCORED.** If a twin also beats
  its parent (CI excluding 0 in the twin's favor), the comparison machinery — not the
  hypothesis — is at fault: freeze all scoring, audit; the hypothesis is un-scored, not
  PASS, not REJECT.
- If the audit finds a real machinery defect (leak, mis-pairing, cluster violation), every
  decision CI computed with the defective machinery is VOID and the cycle terminates
  **NEGATIVE-TERMINAL (MACHINERY)**; continuation = a new registered cycle.

## 7. Stop rules + interpretation law (negative-first)

### 7.1 Peeking / batching law

One scored run. All arms, all folds, one batch, at the successor's gate — mirroring the
terminal cycle (single COMPUTED ledger batch, repro twin byte-identical). No interim OOS
metrics, no adaptive early stopping, no per-fold incremental looks. The ONLY permitted
pre-batch outcome-adjacent events are train-internal (selection-era) computations, which
are legal by §1.2. Any OOS-era metric computed before the freeze+A7+GO chain completes is a
protocol violation ⇒ terminal NOT_RUN.

### 7.2 Stop rules

1. Budget exhausted (≤ 9 PRIMARY arms registered; released slots stay released).
2. Any of R1–R3 obtains ⇒ terminal REJECT (negative), program over for this mechanism
   family on this window.
3. Control-beats-parent on any hypothesis ⇒ halt that hypothesis, machinery audit (§6.1).
4. Data audit failure (Lane A/D byte audit, dedupe law, PIT verdicts) ⇒ scored phase
   NOT_RUN; missing evidence is NOT_RUN, never inferred PASS.
5. INCONCLUSIVE (§6) is a terminal outcome; no re-roll with new constants under the same
   registration.

### 7.3 Interpretation law

- Preregistered negative terminal outcomes, verbatim obligations for the successor plan:
  - **NEGATIVE-TERMINAL (calibration):** if any REJECT condition R1–R3 obtains, the program
    terminates as a negative calibration result. Prohibited responses: re-gridding any
    constant, adding or mutating features/mechanisms, changing folds/metrics/thresholds,
    relaxing CI or slope gates, substituting baselines, reframing via accuracy or market
    vocabulary. Continuation requires a new registered cycle with a NEW mechanism claim.
  - **NEGATIVE-TERMINAL (audit):** if the data/code audit fails, the scored phase is
    NOT_RUN.
  - **NEGATIVE-TERMINAL (control):** control-beats-parent with a failed machinery audit ⇒
    NEGATIVE-TERMINAL (MACHINERY).
- B1-HCA0 baseline flag (§2.3): if the new-window HCA diagnostic fails, the report states
  that candidate gains may partially reflect baseline mis-specification; it does NOT
  authorize swapping the baseline (that would be a new trial).
- PASS/REJECT is calibration language only. Language law grep is a launch and exit gate.
- Dead arms stay dead. No post-hoc tuning of rejected arms; they may be cited, never re-fit.

## 8. Prospective append-only prediction ledger law (season 2027+)

- Schema (proposed): `nba_winprob_prospective_ledger@1`; one JSONL file per successor cycle,
  append-only, never edited or deleted.
- Row (minimum): `{schema, cycle_id, arm_id, class, game_id, season, tip_utc,
  written_at_utc, p_home, model_freeze_ref}` — one row per (arm, game) for EVERY registered
  arm (B0, B1\*, scored candidates, diagnostics as configured).
- **Timestamp law: `written_at_utc` STRICTLY < `tip_utc`** on every row, verified on every
  append; a row failing the check is INVALID, logged as invalid, never silently kept, never
  backfilled. Missed-tip games are NOT_RUN for that (arm, game) — backfilling after tip
  breaks the evidentiary chain and is forbidden.
- Outcome columns NEVER written by the predictor process; outcomes join only at scoring
  time from the frozen, deduped game universe.
- Prospectively-accrued games are reported as a SEPARATE segment (per season and pooled),
  never pooled into the historical OOS headline (no pooling rule is pre-registered in this
  draft; pooling would need its own future pre-registration).
- Every game already played before the successor's freeze is NOT_RUN prospective
  (historical OOS only, §1.4).

## 9. Season-composition reporting law

- **PRIMARY headline = regular-season OOS games only** (deduped, completed, non-All-Star,
  non-Cup-final, season_type=2).
- Separately reported, same frozen fold models, never pooled into primary, never dropped:
  playoffs (`season_type=3`), play-in (`season_type=5`), NBA Cup final (2023+ flagged row).
- Anomaly sensitivity segments, reported with AND without, never silently excluded in
  either direction: (a) 2020-season bubble segment (tips 2020-08-01 … 2020-10-31), re-scored
  with HCA=0 for all Elo arms (terminal §8.4 precedent); (b) 2020-21 early empty-arena
  segment (tips through 2021-03-31); (c) per-fold tables always flag seasons 2020/2021 in
  the selection era and any OOS anomaly cluster so anomalies cannot hide in pooled means.
- Play-in/Cup rows still update rating streams (completed-games law); they only never enter
  the RS headline or training sets.

## 10. Freeze / A7 / GO law for the successor (verbatim obligations)

- `NBA-WINPROB-NG-SCORED-V1` (proposed) may be registered ONLY on: this cycle's
  PREP_COMPLETE verdict + owner instruction + fresh registration. Registration requires:
  1. **Fresh registration** in the cycle registry via researchctl (CAS; never overwrite).
  2. **Data + code freeze manifest** (pattern `nba_winprob_scored_freeze@2` → successor
     bumps schema): pinned input paths + sha256 for the hoopR corpus (`~/.my-quantitative-data/nba-hoopr-v1/`,
     EXTEND-ONLY), the derived normalized game universe, this protocol document (digest),
     the final arm roster with per-arm specs, the frozen split (§1), seeds, and the
     preregistered-comparison list. Freeze BEFORE any outcome is observed.
  3. **A7 prelaunch audit AUTHORIZED** (independent, fresh-session, no repairs): clean tree,
     freeze pins byte-verified, ledger PREREGISTERED rows complete with timestamps strictly
     before any COMPUTED row, spent-window non-violation grep, language-law grep,
     dead-arm non-reference grep, PIT verdicts in place for every feature in every arm.
  4. **Owner typed GO at that cycle's own gate** (two-key chain, in git order: freeze →
     A7 AUTHORIZED → GO recorded). **No GO survives from any earlier cycle** —
     NBA-WINPROB-SCORED-V1's GO was consumed 2026-10-05 and extinguished at close (P-8);
     THIS prep cycle registers no GO phrase and consumes none. The successor's GO phrase is
     registered in ITS plan and is null until recorded at its own gate.
- Immutable history: frozen sources, results, and ledgers of NBA-WINPROB-PREP-V1 /
  NBA-WINPROB-SCORED-V1 / WINPROB-NG-PREP-V1 (and all other cycles) are never edited by
  this cycle or the successor.

## 11. Pitfalls checklist (exact test per pitfall; inherited + new)

1. **Precomputed-Elo / banned-input leakage.** Grep-level: feature/stream code must not
   reference 538 `elo_i`/`opp_elo_i`/`elo_n`/`opp_elo_n`/`forecast`/`win_equiv` (the 538
   corpus is not even in the 2016+ window; it remains cross-check/citation only), nor
   `game_spread`/`home_favorite`/`home_team_spread` (banned market lines), nor any
   current-game box-score field. Behavioral: two independent full-pipeline runs of the
   rating streams must be byte-identical (determinism test).
2. **Same-day ordering.** Unit test: synthetic same-date pair — the "second" game is
   predicted from state excluding the first game's result. Property test: every
   feature-source game has local game date strictly < target's; any equal-date source fails.
3. **Franchise continuity.** Census: every hoopR team identity maps to exactly one lineage;
   no lineage gap or split 2016–2026; stream resets to 1500 ONLY at first corpus game and
   otherwise changes only via updates + season-boundary reversion.
4. **Neutral-site / bubble.** Sensitivity segments per §9; default HCA=100 everywhere is a
   declared limitation.
5. **Postponements.** Rest/travel derive only from games actually played at actual dates;
   `rest_days ∈ {1..10}` (no 0/negative except investigated anomalies); known postponement
   clusters produce rest spikes, not negative gaps; duplicate listings deduped per §4.2.
6. **Playoff/play-in/Cup leakage.** Assert zero non-RS rows in any training set and any
   primary aggregate; non-RS rows appear only in separately labeled reports.
7. **Anomaly seasons.** 2020/2021 sensitivity columns; per-fold flags (§9).
8. **Row double-counting.** Exactly one prediction row per `game_id`; All-Star rows
   excluded; y consistent with scores on every row.
9. **Outcome-column contamination.** Scores used solely as realized outcomes (targets,
   updates); never predictors.
10. **Tip-UTC ledger integrity** (prospective rows): `written_at_utc < tip_utc` verified on
    append; no backfill (§8).
11. **Spent-window non-violation.** Audit grep: no scoring, selection, or grid computation
    touches seasons ≤ 2015; no K/HCA/rest/form grid anywhere (Lane D verifier owns).
12. **Control-twin validity.** Each shuffled/permuted twin preserves per-team and
    per-season marginals exactly (checked pre-look); an invalid twin is regenerated
    pre-look or the hypothesis runs uncontrolled and is reported as such (never as PASS).

## 12. NOT_RUN register (draft state)

| Item | Status | Reason |
|---|---|---|
| Seasons 2009–2015 | SPENT | terminal-cycle law; citable context, never scoreable |
| Lane A (this cycle) game-universe spec | NOT_RUN (not landed at draft) | dependency placeholder; §13 |
| Lane B (this cycle) mechanism adjudication | NOT_RUN (not landed at draft) | dependency placeholder; §13 |
| H-C3 availability arm | NOT_RUN_PIT | no rights+timestamp-proven $0 source |
| Spread features (`game_spread`, `home_favorite`) | BANNED + NOT_RUN | market line per PLAN; ESPN timestamp semantics UNVERIFIED; 99.7% coverage measured on 2026 sample only |
| Tip-time intraday as-of | NOT_RUN_SCOPE | supported by data; law change must be pre-registered pre-look in a future freeze |
| 538-era warm-start of rating stream | NOT_RUN | cross-source seam + anti-contamination; cold start + 2016–17 warm-up adopted |
| K / HCA / γ grids | NOT_RUN_SCOPE | constants frozen verbatim; widening = new trial |
| MOV/blowout-weighted Elo | BANNED | re-grid of dead family |
| Additive logistic-over-Elo layer | BANNED | dead per both terminal cycles |
| 538 forecasts / market odds / current-game box scores | BANNED | plan law |
| Prospective 2026-27 scoring in THIS cycle | NOT_RUN | prep cycle, budget 0 scored, no GO |
| NFL / WNBA arms | OUT OF SCOPE | other cycles / other owner chat |

## 13. Dependencies and reconciliation duty (NOT_RUN placeholders at draft time)

Lanes A (`../A_DATA/`) and B (`../B_MECHANISMS/`) of THIS cycle were **absent at draft
write time** (only `lanes/DISPATCH/` exists in the worktree). Late note at finalization:
`A_DATA/measure_schedule_corpus.{json,py}` appeared mid-task (a raw schema/coverage
measurement — 14,254 rows, unique `game_id`, season_type counts and 67 not-completed rows
all consistent with the predecessor lane A contract cited in §4.2); its full spec/handoff
had not landed, so this draft still proceeds from the PLAN + predecessor contract.
Consequences, by design:

- The split (§1), budget shape (§2), gates (§6), laws (§0, §7, §8, §10) are frozen by THIS
  document from the PLAN + predecessor artifacts and do NOT wait for A/B.
- Lane A: when it lands, its dedupe/as-of/season-composition verdicts are authoritative and
  must be reconciled against §4.2/§9; any conflict is recorded as a plan-conflict finding
  for the controller (protocol does not silently bend).
- Lane B: when it lands, its adjudicated mechanism set (≤ 3–4 of M1–M4, possibly none)
  populates conditional slots within §2's release rule; if Lane B advances a mechanism NOT
  named in §3, it enters ONLY via a released slot bound in the successor freeze pre-look,
  with its own falsifier + negative control, never by displacing a frozen arm.
- If A/B never land, the successor inherits this draft as-is with the conditional slots
  NOT_RUN — that is a valid, honest terminal for the prep cycle.

## 14. Assumptions & limitations (successor must confirm)

1. Season 2026 completeness in the audited bytes (Finals ended 2026-06-14 per predecessor
   lane A measurement) — byte audit re-verifies; incomplete ⇒ auto-drop from OOS list.
2. HoopR schedule rows carry true tip instants usable for the §1.1 cutoff and §8 law
   (predecessor lane A: `game_date_time` local-with-offset + `start_date` UTC twin).
3. ESPN↔provider crosswalk exists only for 2026–2027; the as-of/stream machinery needs no
   cross-source game-id join inside 2016–2026 (single corpus), and the 538 seam join law
   (LOCAL date + home team, never the UTC-shifted 538 `game_id` date) applies only if a
   successor ever cites 538-era context.
4. No NBA team plays two games on the same LOCAL date (assumed, terminal precedent);
   violations are investigation triggers, not silent rows.
5. Franchise identity: no NBA relocation/expansion/rename affected lineages 2016–2026
   (assumed; census test §11.3 verifies from bytes).
6. Bootstrap seed 20261005 and any solver seeds are preregistrations; final values pinned
   in the successor freeze pre-look only.
7. No evaluation was executed in this lane: every number here is a design constant or a
   citation of terminal-cycle bytes, not a new result.

*End of draft. Frozen split cutoff: `2021-08-01T00:00:00Z`. Frozen OOS list:
[2022, 2023, 2024, 2025, 2026]. Budget sketch: ≤ 9 PRIMARY arms, ≤ 6 expected used
(B0, B1\* verbatim, up to 4 conditional mechanisms), H-C3 expected NOT_RUN_PIT, two reserve
slots released; shuffled twins + B1-HCA0 ablation as class-DIAGNOSTIC arms outside the
candidate budget.*
