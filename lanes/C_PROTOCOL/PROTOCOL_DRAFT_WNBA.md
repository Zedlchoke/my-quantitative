# PROTOCOL_DRAFT_WNBA — WNBA-WINPROB-PREP-V1 · Lane C (successor scored-cycle protocol DRAFT)

- Cycle: `WNBA-WINPROB-PREP-V1` · Lane: `C_PROTOCOL` · Task: `wbap-c-proto` · Date: 2026-10-05
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/wnba-winprob-prep-v1/integration` ·
  Branch: `orca/wnba-winprob-prep-v1-integration` · dispatch_sha = actual_start_sha =
  `673b4f27e4abdefc5c54839febac29185dd6e794` (HEAD measured at lane start; tree clean)
- Status: DESIGN / PREREGISTRATION ONLY. No evaluation executed, no metric computed on any real
  WNBA outcome; every constant below is a preregistration, not a result. Budget 0 scored. This
  document authorizes nothing and consumes no GO phrase.
- Scope of the successor (proposed `WNBA-WINPROB-SCORED-V1`): pre-game win probability for WNBA
  games, calibration-only. No betting, no PnL, no market comparison. Accuracy is never called edge.
- FRESH PROGRAM LAW: WNBA is a new program on its own data. No NBA datum, hypothesis, parameter,
  verdict, or split is WNBA evidence. NBA/NFL numbers may be CITED as cross-league context, never
  imported as proof or as defaults. The NBA spent-window prohibition does not bind WNBA windows;
  the same train-only discipline does.
- Machinery inheritance: this draft inherits the TERMINAL MACHINERY of
  `nba-winprob-scored-v1` lanes/C_protocol/PROTOCOL_EVAL.md (fold law, paired date-cluster
  bootstrap, T1/T2/T3 gate shapes, trial-ledger law, negative-first terminal outcomes) and the
  WNBA adaptations sketched in `winprob-ng-prep-v1` lanes/C_MECHANISMS/MECHANISMS.md §3 + the
  data facts of lanes/B_WNBA/WNBA_SOURCE_AUDIT.md. It inherits NO NBA parameter as a WNBA value.
- Binding effect: the successor scored cycle's plan must inherit Sections 2, 3, 4, 5, 6, 7, 10
  and 11 verbatim BEFORE any outcome is observed (freeze-before-scoring doctrine).

## 0. Binding laws inherited (restated, not redefined)

- AS-OF LAW v1 (WNBA form): admissible information set for game G = {all completed, filter-legal
  games with canonical game date strictly < canonical game date(G)} + static identity mappings
  (franchise lineage map, crosswalk). Same-date games never inform each other; all rating-stream
  updates for date d are applied only AFTER all predictions for date d.
- COMPLETED-GAMES LAW: rating streams update on EVERY completed filter-legal game from data start
  forward (regular season, Commissioner's Cup, playoffs — all real competitive games), regardless
  of what is scored or trained on. Playoffs/Cup are not scored into primary but they are history.
- IDENTICAL-ROWS LAW: exactly ONE scoring row per game (home perspective, `y = 1{home win}`);
  all arms see identical rows, folds, and training sets; every paired comparison uses an identical
  game set; no post hoc row filtering (pre-registered segments are reported alongside, never
  substituted).
- TRIAL-ACCOUNTING LAW: every config evaluated on OOS data counts into the observed denominator.
  Train-internal selection sweeps (Section 3.2) never touch OOS and are not scored trials, but
  their grids and procedures are themselves frozen here. Any arm, feature, fold, metric, season
  window, or threshold introduced after ANY OOS outcome is observed = a NEW registered trial
  outside the budget, no exceptions.
- FREEZE-BEFORE-SCORING: grids, folds, metrics, seeds, gates, and the negative-control spec must
  be preregistered in the successor's registration before any OOS look.
- MISSING EVIDENCE IS `NOT_RUN`, NEVER INFERRED `PASS`.
- LANGUAGE LAW: calibration/forecasting vocabulary only. No PnL, betting, market-comparison, or
  "edge" vocabulary anywhere in outputs.

## 1. Hypotheses (max 3, mechanism-first; Lane B of this cycle owns the full adjudication)

Lane B (`wbap-b-mech`) had not landed at this lane's start (measured: only DISPATCH packets exist
in `lanes/`). Per the plan's Lane B mandate, at most 3 hypotheses may be advanced; the protocol
reserves their shapes and freezes the falsifier machinery. Lane B's registration in the successor
cycle fills slots H2-W/H3-W exactly; nothing here pre-judges their verdicts.

### H1-W — Dynamic team strength on a fresh WNBA Elo (Lane B mechanism (a))
- Mechanism: WNBA team quality is persistent within and across seasons (roster cores, coaching)
  but reverts toward the league mean through heavy roster churn (free agency, overseas conflicts,
  retirements) and short seasons. A fresh WNBA rating stream with own train-selected constants
  should calibrate better than any constant assumption. This is a FRESH league: the NBA's frozen
  K=32/HCA=100 and γ=0.75 are citable context, NOT WNBA values; everything is selected
  train-internally inside the WNBA program (Section 3.2).
- Operationalization: arm B1 (Section 4): one rating per franchise lineage; carried over seasons
  with boundary reversion `R <- 1500 + γ·(R − 1500)`; binary-result updates `R <- R + K·(S − E)`;
  prediction `p_home = 1/(1 + 10^{−(R_H + HCA − R_A)/400})`; constants (K*, HCA*, γ*) from the
  frozen train-internal selection grid.
- Reference: B0 (constant home-win rate, train-only refit per fold) is the no-strength floor.
- FROZEN falsifier: H1-W REJECT iff the 95% paired date-cluster bootstrap CI of pooled
  ΔLL(B1, B0) includes 0 or lies entirely > 0 on the OOS window.
- Expected failure interpretation: (a) own-Elo implementation bug — run Section 8 tests 1–3
  first; (b) the train-selected constants mis-fit the OOS era; (c) genuinely no exploitable
  strength persistence at game grain in a 40-game league — itself a notable negative result, not
  a protocol failure.

### H2-W — Continuity-modulated rating carryover (Lane B mechanism (b) = H-C5 from WINPROB-NG-PREP-V1)
- Mechanism: short season + high churn weakens prior-season priors; how much prior rating
  survives the offseason should be team-specific, moderated by roster continuity (share of
  prior-season rotation returning). PIT-safe: season-start rosters are fixed before opening
  night; the continuity index is known at the season boundary.
- Operationalization (sketch; Lane B fixes the exact spec at registration): season-boundary rule
  `R_start_i = 1500 + ρ·continuity_i·(R_end_i,prev − 1500)` replacing B1's uniform γ for this
  arm; `continuity_i` from season-start rosters (wehoop `espn_wnba_game_rosters` 2002–2026;
  rights per lane-B audit §1a). ρ selected train-internally, then frozen.
- Designed-null parent: B1 (a constant `ρ·continuity_i ≡ γ` reproduces B1's boundary rule).
- Preconditions (auto-drop, no OOS spend): continuity index must exhibit cross-team variance in
  early seasons (near-constant index ⇒ drop); roster coverage must clear Lane A's census; a
  train-internal kill test must show gain over B1 before any OOS look (Section 3.4).
- FROZEN falsifier: H2-W REJECT iff the pooled 95% CI of ΔLL(arm, B1) includes 0 or ≥ half of
  OOS folds are non-negative; plus the twin check of Section 7 must not fail.

### H3-W — At most ONE additional WNBA-structure-specific mechanism (Lane B mechanism (c))
- STATUS: NOT_RUN placeholder at this lane's start — Lane B had not landed. The arm slot
  (Section 4, arm 4) is CONDITIONAL: it exists only if Lane B advances a mechanism that survives
  mechanism-first scrutiny AND its data layer clears Lane A's PIT/census audit; otherwise the
  slot is RELEASED, never reallocated (Section 4 reserve law).
- Whatever Lane B advances inherits the frozen gate shape: REJECT iff pooled 95% CI of
  ΔLL(arm, its designed-null parent) includes 0 or ≥ half of OOS folds non-negative, twin check
  clean, train-internal kill test passed before OOS.

BANNED for WNBA (plan law, restated): additive logistic-over-Elo feature layers (dead shape per
both terminal cycles — cited as context for the ban, not as WNBA evidence); MOV-weighted Elo
re-grids; 538 forecasts; closing/market odds; current-game box scores; any NBA-derived parameter
presented as WNBA evidence; player_box active/DNP/starter fields as pre-game features (post-game
facts). Rejected/dead arms of other leagues may be CITED, never re-fit on WNBA data as if the
rejection were WNBA evidence — WNBA rejections happen only under this protocol's own gates.

## 2. Data universe, as-of law, and the ERA LAW (FROZEN)

### 2.1 Universe and filter law (mandatory, from the lane-B audit §3.3/§3.5; Lane A re-measures)
- Sources: sportsdataverse release store only (ESPN schedules 2002–2026; stats-side schedules
  1997–2026; ESPN box/pbp 2002/2003+). No direct scraping of wnba.com / stats.wnba.com / ESPN.
- Scoring rows: exactly one row per game_id; keep only `status_type_state=='post'`; drop
  `status_type_detail ∈ {Forfeit, Postponed}` (exactly 1 forfeit: 2018-08-03, recorded 0–0);
  drop All-Star rows (alias teams EAST/WEST/ALL/DEL/PAR/CLA/COOP/WNBASTARS);
  drop TBD/if-necessary placeholders; NEVER filter on score presence (unplayed rows are
  pre-filled 0–0). Assertion: every scored row has y ∈ {0,1} from team scores; WNBA has no ties.
- Identity: join teams via display_name / the `wnba_crosswalk` release, NEVER raw ESPN
  abbreviations (measured unreliable pre-2011; 2002 DET/TUL artifact).
- Canonical time: one canonical tip-UTC law per Lane A's timestamp canonicalization (4 measured
  flavors: ESPN schedule UTC instant; ESPN box venue-local+offset; ESPN pbp UTC wallclock;
  stats-side naive local date). As-of ordering uses the canonical game DATE (date-grain),
  Section 8 test 2.

### 2.2 ERA LAW for 1997–2001 (stats-side-schedules-only era) — CHOICE MADE AND FROZEN
The dispatch requires one of two handlings: era excluded from feature arms, or era used as
schedules-only baseline usage. **FROZEN CHOICE: schedules-only baseline usage, in the narrow
form of rating-stream warm-up ONLY.**

- Admissible uses of 1997–2001 rows (stats-side schedules only; exactly 1,022 schedule rows,
  5 seasons, all with populated scores):
  1. B1-family rating-stream warm-up: Elo updates on completed 1997–2001 games under the
     completed-games law, so 2002-season predictions start from informed, not cold, ratings.
- FORBIDDEN uses of 1997–2001 rows:
  1. As arm training rows (B0 intercept and any fitted mechanism component fit on 2002+ only) —
     keeps training sets identical across arms;
  2. As OOS or selection-scoring rows (no fold may score on the era);
  3. As feature-arm inputs (no box/pbp-derived features exist for the era in the verified
     corpus anyway — ESPN box starts 2003, pbp 2002);
  4. In any sensitivity segment.
- Rationale (frozen): schedules rows lawfully carry final scores (100% populated per audit
  §3.3), so excluding the era from the rating stream would discard real completed games and
  violate the completed-games law; but the era is single-source (no cross-source reconciliation
  possible), carries only naive venue-local dates (weakest timestamp flavor, audit §3.4), and
  has structurally different league composition (8→16 teams, 28–34-game seasons). Admitting it
  beyond stream warm-up would either break the identical-rows law or score folds the data layer
  cannot audit. Feature arms cannot use it regardless, so only the warm-up use is asymmetric —
  and that asymmetry is inherent to any rating stream and identical for every arm that consumes
  ratings (B1, H2-W, H3-W, and any feature derived from them).
- WARM-UP SENSITIVITY (diagnostic, not an arm, never counted as a candidate win): re-run B1 with
  the stream re-initialized at 2002 (cold start) and report the ΔLL difference on the TRAIN
  sub-window selection folds. If warm-up materially changes selection outcomes, the successor
  must disclose it in the registration before any OOS look.
- 2020 Wubble (147 rows, 22-game season) is a REAL season, never treated as a gap or anomaly
  exclusion; it stays wherever the season windows put it, flagged, with a with/without
  sensitivity column (Section 3.3).

### 2.3 Segmentation law (frozen before any look)
- PRIMARY headline set: regular-season (`season_type=2`) filter-legal rows MINUS
  Commissioner's-Cup-flagged rows (2021+, embedded in RS; flag per Lane A) — playoffs, Cup, and
  All-Star are SEPARATE from the RS headline, per dispatch.
- Cup segment: Cup-flagged rows scored with the same frozen fold models, reported in a labeled
  separate table; never pooled silently into the headline in either direction. A "RS incl. Cup"
  sensitivity column is reported alongside.
- Playoffs (`season_type=3`): scored with the same frozen fold models, reported separately per
  fold; never pooled into primary; never silently dropped. Playoff and Cup rows still update the
  rating stream and appear in training rows (completed-games law; they are real competitive
  games; training-row law in Section 3.1).
- All-Star rows: excluded from everything (exhibition; alias rosters); count reported.
- Neutral-site rows (15 rows, 2013–2026, flag exists in this data — better than the NBA
  situation): B1-family predictions for neutral-site rows use HCA = 0 (and the same expected
  score inside the update); a with-HCA-everywhere variant is reported as a diagnostic, both ways
  shown, nothing hidden.

## 3. Split design (FROZEN shapes; exact lists frozen by the controller after Lane A)

### 3.1 Windows
- Unit = season (`year_id`, single-calendar-year league). Folds = expanding window by season.
- TRAIN sub-window: seasons 2002 … (first OOS season − 1) — 2002 is the first cross-source-
  verified ESPN era; the 1997–2001 era participates ONLY via stream warm-up (Section 2.2).
  Under the placeholder OOS list below, TRAIN = 2002–2018 (17 seasons ≈ 3.6–3.8k RS games).
- OOS test window: the FINAL 7 COMPLETE seasons in the audited data at the successor's data
  freeze. PLACEHOLDER RULE (binding, inherited shape): **test = final 7 complete seasons,
  frozen by the controller after Lane A's byte audit; the modeler may never choose test seasons
  after seeing outcomes.** If 2026 is incomplete at freeze (playoffs run to ~mid-October), the
  placeholder list is 2019–2025; if complete, 2020–2026. Completeness law: a season is complete
  iff every non-placeholder scheduled game has `status_type_state=='post'` (Lane A census
  supplies the per-season played counts). A season dropped by the completeness rule is excluded
  from V1 scoring entirely; scoring it later requires an amended registration (new trial). No
  retro-fitting dropped seasons into any window, ever.
- Fold k (k = 1..7): train = all complete, filter-legal seasons strictly before test season k
  (expanding through the OOS window); predict every primary-set game of test season k. B1
  rating streams are fully determined by the as-of law + frozen arm constants (no refit); B0
  refits per fold; fitted mechanism components refit per fold on strictly-prior rows using the
  frozen procedure (inherited walk-forward law).
- TRAINING-ROW law: training rows for B0 and all fitted components = regular-season (`season_type=2`)
  filter-legal rows of train seasons INCLUDING Cup-flagged rows (real competitive games,
  identical across arms); playoffs never enter training but update the rating stream. (This
  mirrors the inherited NBA justification: structural difference ⇒ not scored into primary;
  information value ⇒ still history.)

### 3.2 Train-internal rolling-origin selection (all free parameters; before any OOS contact)
- Every free parameter (B1 K, HCA, γ; H2-W ρ; any H3-W constant; any bucket edge or block
  membership) is selected INSIDE the TRAIN sub-window by a rolling-origin procedure, then
  frozen at registration. No OOS window is touched during selection.
- FROZEN selection procedure: 4 expanding-origin validation blocks inside TRAIN:
  | block | train seasons | validation seasons | ≈ validation games |
  |---|---|---|---|
  | S1 | 2002–2010 | 2011–2012 | ~440 |
  | S2 | 2002–2012 | 2013–2014 | ~440 |
  | S3 | 2002–2014 | 2015–2016 | ~440 |
  | S4 | 2002–2016 | 2017–2018 | ~440 |
  (exact game counts come from Lane A's census; ~230 RS games/season is the planning number.)
- Selection metric: mean log loss over the validation blocks' PRIMARY-set rows (type-2, post,
  non-forfeit, non-All-Star, non-Cup); ties within 1e-6 resolved mechanically: smaller K, then
  larger γ (stronger reversion, the churn prior), then smaller HCA.
- FROZEN selection grids (train-internal only; reported in a selection appendix):
  - B1: K ∈ {8, 16, 32} × HCA ∈ {0, 50, 100} × γ ∈ {0.65, 0.75, 0.85} (27 configs; bracketing
    grid — NBA's operating points appear only as citable context; the data picks).
  - H2-W: ρ on a pre-registered grid fixed by Lane B at registration (constraint: the arm must
    reduce to B1 at its null boundary, and the continuity-variance precondition of Section 1
    must hold before the sweep runs).
  - H3-W: per Lane B's registration, same law.
- HCA existence is a TRAIN-INTERNAL outcome of this selection (HCA* > 0 or HCA* = 0), reported
  as a selection finding; it is not an OOS-scored hypothesis in V1 and burns no arm. The B1
  arm is ONE arm regardless of which grid point wins.
- Burn-in: with stream warm-up from 1997 (or 2002 under the cold-start diagnostic), the first
  selection block has ≥ 8 prior seasons of history; burn-in adequacy is re-argued only if the
  controller trims history, before freezing.

### 3.3 OOS evaluation (walk-forward, inherited shapes)
- PRIMARY evaluation set = primary-set games of the 7 OOS seasons (Section 2.3). Expected pooled
  n ≈ 1,500–1,700 RS games (~230/season × 7, plus 2025's expanded slate; exact = Lane A census).
- Per-fold tables are mandatory: every fold reports n, LL, Brier, calibration slope per arm;
  folds flagged LOW_POWER if n < 150 (2020 under the 2019–2025 placeholder will be ~130 and
  MUST be flagged, kept in primary, with with/without-2020 sensitivity columns — the Wubble is a
  real season; default exclusion is forbidden and would itself be a new trial).
- Playoff and Cup games of OOS seasons: same frozen fold models, separate labeled tables.

### 3.4 Train-internal kill tests (before OOS spend)
A mechanism arm whose train-internal selection shows no log-loss gain over its designed-null
parent (H2-W vs B1; H3-W vs its parent) on the Section 3.2 blocks NEVER reaches OOS; its slot is
RELEASED, never reallocated. Report the kill in the selection appendix.

### 3.5 Future seasons — PROSPECTIVE ONLY (append-only ledger law)
- Any season after the OOS window is PROSPECTIVE ONLY. Predictions are appended to an
  append-only ledger, one row per game per arm, with frozen fields: arm_id, game_id, canonical
  tip_utc, model_version, registration digest, p_home, and prediction_written_utc — each row
  must be written (timestamped) STRICTLY BEFORE tip_utc; no edits, no deletes; the outcome y is
  appended later as a separate record referencing the prediction row.
- Prospective accrual: no OOS-style report on prospective seasons until ≥ 2 complete prospective
  seasons have accrued; a single-season prospective report is never presented as decisive
  (inherited NG-sketch law, stated for the thin-window case).
- No retrospective re-scoring of prospective rows under changed specs; spec changes start a new
  registration.

## 4. Arm budget (FROZEN BEFORE ANY TEST LOOK; cap ≤ 9; this draft allocates 5)

| # | Arm | Spec | Role / registered comparison |
|---|-----|------|------------------------------|
| 1 | B0 | constant home-win probability; intercept-only train-win-rate, refit per fold on train RS rows | floor; H1-W reference; T3 reference |
| 2 | B1 | fresh WNBA own-Elo, constants (K*, HCA*, γ*) from the Section 3.2 frozen selection; 1997–2001 warm-up per ERA LAW; binary updates; no MOV | H1-W live arm; designed-null parent of H2-W; T1 reference |
| 3 | B-C5 | H2-W continuity-modulated carryover (ρ train-selected); continuity index from season-start rosters; auto-drop preconditions | H2-W live; program candidate (default) |
| 4 | B-C | H3-W: at most ONE additional Lane-B mechanism — CONDITIONAL on Lane B advancement + Lane A data-layer clearance | H3-W live; else slot RELEASED |
| 5 | RESERVE | must be fully specified (mechanism, exact spec, falsifier, twin, capacity estimate) in the successor's registration freeze document BEFORE any OOS look; unused = RELEASED | contingency only |

- TOTAL BUDGET = 9 (cycle ceiling, per dispatch). This draft ALLOCATES 5 and PERMANENTLY RELEASES
  the remaining 4 slots of headroom to V1: the successor registration may not exceed 5 arms, may
  not refill released slots, and may not reallocate the arm-4 slot if its conditions fail.
  Tightening was chosen deliberately: ~230 games/season cannot power a wide grid, and every
  added arm widens every paired CI denominator honestly (trial accounting).
- Negative-control twins (Section 7) are diagnostic runs OUTSIDE this budget: pre-registered
  1:1 with their hypotheses, reported, NEVER counted as candidate wins.
- FREEZE LAW (verbatim inheritance): grid, features, folds, metrics, and thresholds must be
  preregistered in the successor scored cycle's plan BEFORE any evaluation on real outcomes. Any
  arm, feature, fold, metric, or threshold added after seeing any outcome = a NEW registered
  trial outside this budget, no exceptions. Retuning any selected constant, widening any grid,
  or changing fold count/season windows are all new trials.
- Program candidate: AT MOST ONE arm is nominated at registration for the T1/T2/T3 program gate
  (default: B-C5 if advanced). Never more than one.

## 5. Metrics + uncertainty (inherited machinery)

- Identical game sets per comparison; probabilities clamped to [1e-15, 1−1e-15].
- PRIMARY: mean log loss `LL = −mean[y·ln p + (1−y)·ln(1−p)]` on the primary set.
- Secondary: Brier score `mean[(p − y)²]`; reliability = 10 equal-width bins on p with
  (n, mean p, observed rate) per bin; calibration slope = binomial-GLM (logit link) coefficient
  of `logit(p)` in `outcome ~ 1 + logit(p)`. Slope 1 = calibrated; <1 overconfident; >1
  underconfident. Report pooled and per fold.
- Paired comparisons: per-game `ΔLL = LL(arm) − LL(reference)`; 95% CI by block bootstrap
  resampling game DATES with replacement — clusters = canonical game dates (same-date WNBA games
  share rating state and schedule context). 10,000 resamples, percentile CI, seed 20261005.
  Report per fold AND pooled.
- Sign convention: Δ < 0 favors the arm; Δ > 0 favors the reference.
- Capacity honesty (stated now, binding on interpretation): ~230 RS games/season ⇒ pooled OOS
  n ≈ 1.5–1.7k resolves ΔLL effects of roughly ≥ 0.003–0.005 under date-cluster CIs (terminal
  cycles resolved ~0.001 at n ≈ 8.4k); effects below that scale are expected to be
  INCONCLUSIVE, not PASS. This is a reported limitation, never a gate relaxation.

## 6. Gates for the scored phase (calibration-only; shapes inherited verbatim)

Sign convention per Section 5; "CI" = paired date-cluster bootstrap 95% CI. Reference baseline
for all mechanism comparisons is B1 (the fresh WNBA Elo), not merely B0: a mechanism must beat
the strength baseline, not only the floor. (Inherited NG law §0.1; WNBA has a SINGLE frozen B1,
so unlike the NBA cycle there is no test-time selection of a best-Elo arm — T1 references B1
directly.)

Program PASS for the nominated candidate arm requires ALL of:
- T1 (discriminative gain over the strength baseline): pooled ΔLL(candidate, B1) has CI entirely
  < 0 AND Δ_f(candidate, B1) < 0 on ≥ half of the 7 OOS folds.
- T2 (calibration): pooled calibration slope of the candidate ∈ [0.85, 1.15].
- T3 (floor safety): no OOS fold where Brier(candidate) > Brier(B0), AND pooled ΔLL(candidate,
  B0) has CI entirely < 0.

REJECT (negative terminal) if ANY of:
- R1: CI of pooled ΔLL(B1, B0) includes 0 or lies entirely > 0 ⇒ dynamic strength adds nothing
  over the constant baseline in the WNBA at game grain ⇒ program premise fails.
- R2: pooled ΔLL(candidate, B0) CI entirely > 0 ⇒ candidate worse than the constant floor.
- R3: pooled ΔLL(candidate, B1) CI entirely > 0 AND T2 violated ⇒ both degradation vs Elo and
  miscalibration.

INCONCLUSIVE: all decision CIs include 0 while T2 holds ⇒ no PASS; no re-tuning, no threshold
relaxation, no metric substitution; continuation requires a new registered cycle with a NEW
mechanism claim (or, for the continuity program, a registered prospective-accrual extension).

Hypothesis-level verdicts are exactly the falsifiers in Section 1 (H1-W: B1 vs B0; H2-W: B-C5
vs B1; H3-W: B-C vs its parent).

Language law: PASS/REJECT is calibration language only. No PnL, no betting or market comparison,
no "edge" vocabulary anywhere in outputs.

## 7. Negative-control law (per hypothesis; diagnostic arms, never candidate wins)

- Each mechanism hypothesis carries exactly ONE pre-registered time-shuffled twin with preserved
  marginals and no mechanism information: T-B1 (team-identity permutation of the rating streams
  — machinery check: must lose to B1), T-C5 (continuity index permuted across teams within
  season, marginals preserved), T-C (time-shuffled twin of the H3-W mechanism input, per its
  registration). B0 has no twin (no information input to shuffle).
- LAW: a twin that beats its parent beyond noise (95% CI of ΔLL(twin, parent) entirely < 0)
  invalidates the PAIRED COMPARISON MACHINERY for that hypothesis: the hypothesis is UN-SCORED
  pending a machinery audit; it is never counted as a candidate win, and the parent's apparent
  gain is not claimed. A machinery audit failure is reported as an incident in the scored cycle.
- Twins are reported in every results table alongside their parents, visibly marked diagnostic.

## 8. Pitfalls checklist (exact test per pitfall)

1. **Hidden-input leakage**: feature/construction code must not reference any post-game field
   (`points`, winner columns, player_box `active`/`did_not_play`/`starter`/`reason` — all
   POST-GAME facts) as pre-game inputs; grep-level static check + behavioral as-of audit
   (Section 8 test 2). No 538-equivalent exists for WNBA; any foreign "forecast" column in the
   corpus is banned as input by plan law and checked the same way.
2. **Same-day ordering**: property test over all rows — every feature-source game has canonical
   date strictly < target date; equal-date sources fail the audit. ADDITIONAL WNBA ASSERTION
   (hard dependency): verify no team plays two games on one canonical date (expected true in
   WNBA; the 2020 Wubble must be explicitly checked). If any same-team same-date pair exists,
   the date-grain as-of law is INSUFFICIENT for that pair: stop, amend to intraday ordering via
   canonical tip_utc BEFORE freezing, record as an incident. Never silently score such pairs.
3. **Franchise lineage / merge integrity** (WNBA-specific, load-bearing): CONFLICT FLAGGED —
   the lane-B audit §3.6 (measured from abbreviations) reads `SAN→DAL 2016`, `LAS→LVA 2018`,
   `TUL merges into DAL 2016`, while franchise-license history and the plan's own lines read
   `TUL→DAL 2016`, `SAN→LVA 2018`, Sparks never move. Lane A MUST resolve the lineage map from
   crosswalk + display_name + venue/city fields with season boundaries. Tests: every team_key
   maps to exactly one lineage; a lineage's stream is continuous except (i) birth at 1500
   (expansion: CHI 2006, ATL 2008, GSV 2025, TOR/PDX 2026, plus 1997–2002 defunct births) and
   (ii) the frozen season-boundary reversion rule. MERGE RULE (frozen pending Lane A's map):
   at a franchise merge, the surviving stream is the line of the franchise license designated
   by Lane A's verified map; the other line terminates and is NOT averaged in (a
   mean-of-merging-streams variant may be reported as a diagnostic only). B1 cannot be frozen
   before this map is resolved.
4. **Neutral-site rows** (15 rows, flagged in-data): predicted with HCA = 0 by default
   (Section 2.3); with/without-HCA diagnostic reported; never silently pooled either way.
5. **Forfeits / postponements / 0–0 prefills**: filter law (Section 2.1); tests: (a) zero rows
   with `status_type_state != 'post'` in any scored set; (b) zero Forfeit/Postponed rows
   (exactly the 1 known forfeit excluded and counted); (c) no scored row with 0–0; (d) no
   feature references an unplayed row; (e) 2026 TBD placeholders absent everywhere.
6. **All-Star alias contamination**: assertion that no scored/training row carries an alias
   team key (EAST/WEST/ALL/DEL/PAR/CLA/COOP/WNBASTARS); the 14 All-Star rows are counted and
   excluded everywhere.
7. **Cup segmentation leakage**: assertion that Cup-flagged rows appear in the Cup table and
   the with/without sensitivity columns but NOT in the primary headline aggregates; and that
   they DO update streams and appear in training rows (completed-games law) — both directions
   asserted, nothing silent.
8. **Row double-counting**: exactly one scoring row per game_id after normalization; y
   consistent with team scores on every row (Lane A's one-row-per-game finding re-asserted on
   the normalized universe).
9. **Abbreviation traps**: no raw ESPN abbreviation used as a join key anywhere (display_name /
   crosswalk only); the 2002 DET/TUL artifact is the standing regression test.
10. **Era-law violations**: assertion that no 1997–2001 row appears in any training set,
   selection-validation set, OOS fold, or sensitivity segment; stream warm-up consumption only
   (Section 2.2). The warm-up diagnostic (cold-start rerun) is reported, never counted.
11. **Anomaly-season hiding**: 2020 (and 2025's expanded format if in-window) flagged in every
   per-fold table; with/without sensitivity columns mandatory; pooled means never presented
   without the per-fold table.
12. **Prospective-ledger integrity**: every ledger row's prediction_written_utc < tip_utc
   (asserted over all rows, both arms and twins); no edits/deletes (hash-chain or append-only
   store); y appended separately.

## 9. NOT_RUN register (v1, frozen at draft)

| Item | Status | Reason | v1 handling |
|---|---|---|---|
| Injury/availability features | NOT_RUN_PIT | no dedicated injury feed in any wehoop-family release (audit §3.7); no rights-verified archive with publish timestamps | excluded; successor needs PIT-proven provenance first |
| Lineups/rotations as pre-game features | NOT_RUN_PIT | player_box lineup fields are post-game facts; `espn_wnba_game_rosters` usable ONLY at season-start granularity (H2-W) | season-start rosters only, per H2-W as-of law |
| Lane-B mechanism (c) arm | NOT_RUN (dependency) | Lane B had not landed at this lane's start | conditional slot 4; else released |
| Exact OOS season list | NOT_RUN (dependency) | requires Lane A byte audit + completeness census | placeholder rule (Section 3.1); controller freezes |
| Lineage map (SAN/LAS/TUL→DAL/LVA) | NOT_RUN (dependency, conflict flagged) | audit §3.6 vs license-history conflict | Lane A must resolve; B1 freeze blocked on it |
| Intraday as-of ordering | NOT_RUN unless 8.2 trips | date-grain law inherited; no need if no same-team same-date pairs | escalation path in Section 8 test 2 |
| Box/pbp-derived feature arms | NOT_RUN_SCOPE | additive-over-Elo shape banned; no mechanism advanced for them this cycle | may be proposed as NEW mechanisms in a future cycle |
| MOV-weighted Elo | OUT (banned family re-grid) | plan ban | never in V1 |
| 538/market odds | OUT (banned) | plan ban; no $0 WNBA source anyway | never |
| Full-history PBP mirror (+~1.0–1.4 GB) | NOT_RUN (owner-budget-bound optional) | default is schedules + depth census, not a mirror | successor may extend under its own budget |
| 2026 season scoring | NOT_RUN (pending completeness at freeze) | playoffs in progress at draft date | completeness rule, Section 3.1 |
| Post-2026 seasons | PROSPECTIVE ONLY | ledger law Section 3.5 | append-only, ≥2 seasons before any report |

## 10. Stop rules + negative-first terminal outcomes for the successor (must appear verbatim in the successor plan)

- NEGATIVE-TERMINAL (calibration): If any REJECT condition R1–R3 (Section 6) obtains on the
  frozen protocol, the WNBA program terminates as a negative calibration result. Prohibited
  responses: re-gridding K/HCA/γ/ρ, adding or mutating features or mechanisms, changing folds,
  season windows, metrics, or thresholds, relaxing CI or slope gates, substituting baselines, or
  reframing via accuracy/PnL. Continuation requires a new registered cycle with a NEW mechanism
  claim.
- NEGATIVE-TERMINAL (audit): If the successor's data-layer audit fails (lineage map unresolved,
  filter-law violations, PIT violation), the scored phase is NOT_RUN. Missing evidence is
  NOT_RUN, never inferred PASS.
- NEGATIVE-TERMINAL (machinery): any twin-beats-parent event (Section 7) un-scores that
  hypothesis pending audit; if the audit cannot clear the machinery, the affected comparison is
  NOT_RUN and the cycle reports honestly without it.
- CAPACITY STOPS: pooled OOS n < 1,200 primary games ⇒ no program PASS may be issued
  (INCONCLUSIVE-by-capacity); selection-validation block < 300 games ⇒ that block is excluded
  from selection and the exclusion is reported; an OOS fold < 100 games cannot carry any
  decision alone.
- INCONCLUSIVE: all decision CIs include 0 while T2 holds ⇒ no PASS; prohibited responses as in
  NEGATIVE-TERMINAL; prospective accrual may continue ONLY under the Section 3.5 ledger law.
- TRIAL LAW: Any arm, feature, fold, metric, season window, or threshold introduced after any
  real outcome is observed is a NEW registered trial outside this budget, no exceptions.

## 11. Freeze / A7 / GO law (plan language, binding, verbatim)

From the cycle plan (Terminal outcomes): "A successor scored cycle (proposed name
WNBA-WINPROB-SCORED-V1) may be registered later ONLY on: this cycle's PREP_COMPLETE verdict +
owner instruction + fresh registration with data/code freeze, A7 prelaunch, and owner typed GO
at that cycle's own gate. This cycle registers no GO phrase and consumes none."

Restated for the successor's plan (must appear verbatim there): the successor requires (a) this
cycle's PREP_COMPLETE verdict, (b) explicit owner instruction, (c) FRESH registration with data
freeze and code freeze, (d) A7 prelaunch AUTHORIZED, and (e) owner TYPED GO issued at the
successor's OWN gate. No GO phrase exists in this document; this lane registers nothing and
consumes nothing. This document's Sections 2, 3, 4, 5, 6, 7, 10 and 11 must be inherited
verbatim into the successor's plan before any outcome is observed.

## 12. Dependencies and assumptions (measured at lane start)

1. Lanes A and B of THIS cycle had NOT landed at this lane's start (measured: `lanes/` contains
   only DISPATCH packets). All Lane-A-dependent constants (exact OOS list, per-season census,
   lineage map, canonical tip law, Cup/neutral flags) and all Lane-B-dependent specs
   (H2-W exact operationalization, H3-W existence) are explicit NOT_RUN placeholders. The
   protocol is written to be complete regardless: every placeholder has a frozen rule for how
   the controller/Lane A/B fills it BEFORE any outcome look.
2. Lineage-map conflict (Section 8 test 3) is the single highest-risk dependency: B1's stream
   continuity is undefined until Lane A resolves SAN/LAS/TUL → DAL/LVA. If Lane A cannot
   resolve it from the data, the successor is BLOCKED_DATA_RIGHTS-class (identity integrity),
   not a protocol failure.
3. ~230 RS games/season and ≈5.5–6k total RS games (2002–2025) are planning numbers from the
   dispatch/plan; Lane A's census is authoritative for all counts. Game-level season counts in
   this draft (e.g., ~440 per selection block) are capacity sketches, not measurements.
4. The successor must re-verify (not assume): season completeness, the 1-forfeit count, alias
   row counts, neutral-site row count, and Cup-flag completeness — all measurable from Lane A's
   normalized universe.
5. No outcome was computed and no data was downloaded in this lane. Every number herein is
   either an inherited machinery constant, a frozen design constant, or a planning sketch
   explicitly marked as such.
