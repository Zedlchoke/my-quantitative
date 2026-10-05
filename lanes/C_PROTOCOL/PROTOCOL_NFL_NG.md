# PROTOCOL_NFL_NG — successor NFL win-probability protocol (DESIGN ONLY)

- Cycle: `NFL-WINPROB-NG-PREP-V1` · Lane: `C_PROTOCOL` · Task: `nflng-c-proto` · Date: 2026-10-05
- Status: **DESIGN / PREREGISTRATION DRAFT.** No evaluation executed, no data downloaded, no
  metric computed on any real outcome in this cycle. Every constant below is a design
  preregistration for the successor scored cycle's freeze packet, not a result.
- Authority chain: owner direction 2026-10-05 (plan `plans/PLAN_nfl_winprob_ng_prep_v1.md`) →
  this packet `lanes/DISPATCH/DISPATCH_C_PROTOCOL.md` → frozen semantics of
  `NFL-WINPROB-PREP-V1` / `NFL-WINPROB-SCORED-V1` (read-only, cited below).
- Frozen-semantics source (read-only evidence, inherited where still valid):
  `integration/lanes/NFL_C_protocol/PROTOCOL_EVAL_NFL.md` of worktree
  `nfl-winprob-prep-v1` (hereafter **FROZEN-PROTO**). Terminal evidence:
  `research/control/NFL-WINPROB-SCORED-V1/results/scored_summary.json` of worktree
  `nfl-winprob-scored-v1` (hereafter **TERMINAL**). Prior-cycle protocol sketch §3:
  `integration/lanes/C_MECHANISMS/MECHANISMS.md` of worktree `winprob-ng-prep-v1`.
- Language law: calibration/forecasting vocabulary only. No PnL, no betting or market
  comparison, no "edge" vocabulary anywhere in this document or any successor output.

## 0. Binding laws inherited (restated, NOT redefined)

The following laws of FROZEN-PROTO §0 are inherited **verbatim in meaning**; the successor
freeze packet must restate them before any prospective row is recorded. Nothing here amends
them; where this document clarifies application to the prospective regime, it says so
explicitly.

1. **AS-OF LAW v1 (KICKOFF GRAIN).** Admissible information set for game G = {all completed
   games with `kickoff(G')` strictly < `kickoff(G)`} + static identity mappings (franchise
   lineage map). Games with identical kickoff timestamps never inform each other
   (identical-kickoff exclusion). Same-day later kickoffs DO inform earlier kickoffs.
2. **FALLBACK LAW (kickoff reliability).** If Lane A measures kickoff timestamps unreliable
   before some season X, the kickoff-grain law applies as primary only from X forward;
   pre-X seasons serve only as Elo warmup under a documented degraded ordering. The value of
   X (or "not activated") is a Lane-A fact, frozen in the successor freeze packet before any
   scoring; never chosen after seeing outcomes.
3. **GRAIN FLOOR.** Week-grain features only if kickoff AND day grain both fail → then the
   protocol is declared `NOT_RUN_PIT` rather than weakened.
4. **LEAKAGE LAWS.** Own-Elo only; no precomputed rating/projection/forecast/spread/total
   column ever an input; odds/probability columns quarantined at load (cross-check fixtures
   at most); franchise continuity (one lineage = one rating stream); all features derive from
   COMPLETED games only; score columns are realized outcomes only (labels, updates) under the
   as-of law. `PRE` rows dropped at load with count disclosed.
5. **TIE LAW.** Binary label `y = 1{home team wins}`. Ties are EXCLUDED from primary scoring
   sets and from training rows, with tie count disclosed per season and pooled — never
   silently dropped. No 3-outcome tie model is invented anywhere. Ties count in the rating
   stream as `S = 0.5` for both teams and as half a win in form windows (update conventions,
   not predictive models).
6. **NEUTRAL-SITE LAW.** Games flagged neutral-site (Lane-A-validated venue mapping, or
   venue/city column crossed with a static home-venue map — a static mapping permitted by the
   as-of law) are scored with **HCA=0** and reported as a separate segment, never pooled
   silently. B1* already runs HCA=0 so it is unaffected; any candidate carrying an
   HCA-like term must zero it on flagged games. Super Bowl rows inside the playoff report
   additionally carry the neutral-site caveat.
7. **COMPLETED-GAMES LAW.** Playoff games never enter candidate training rows but DO update
   the rating stream feeding features (completed games, at actual kickoffs).
8. **DOCTRINE.** Trial accounting (every evaluated config counts into the observed
   denominator); freeze before any outcome; negative terminal outcomes preregistered; missing
   evidence is `NOT_RUN`, never inferred `PASS`.
9. **DEAD-ARM LAW** (plan Inheritance; MECHANISMS §3.8). Rejected/dead arms stay dead:
   NFL constant-HCA mains and rest/short-week mains are REJECTED (TERMINAL, H2/H3), the
   logistic-over-Elo additive layer is dead in both terminal cycles. They may be **cited,
   never re-fit**; no re-grid of K/HCA/rest/form mains on any window, ever.
10. **BASELINE LAW.** Any new mechanism must beat **B1\*** (= B1-c own-Elo K=40, HCA=0,
    γ=2/3), not merely B0. Prior evidence (TERMINAL, cited, not re-used): B1* pooled
    regular-season LL 0.6407 vs B0 0.6935, ΔLL −0.0528 [−0.0676, −0.0380]; H2 (HCA constant)
    and H3 (rest/short-week mains) REJECTED; cycle terminal INCONCLUSIVE.

## 1. Window law (SPENT / TRAIN / PROSPECTIVE)

This is the successor's central structural decision and is binding on every later section.

### 1.1 SPENT window — 2019..2025

- The TEST window 2019–2025 of NFL-WINPROB-SCORED-V1 is **SPENT**. It may be **cited** as
  prior evidence (with source path and values, as in §0.10) but may never again serve as:
  a hypothesis-testing window, a selection window, a re-scoring target, a K/HCA/rest/form
  re-grid surface, or a pooling partner for prospective aggregates.
- Any arm, feature, fold, metric or threshold evaluated on 2019–2025 ever again is a NEW
  registered trial outside any inherited budget, and — per the spent-window law — is not
  merely a new trial but a prohibited re-use. Continuation language lives in the successor
  plan, not here.

### 1.2 TRAIN window — all complete seasons strictly before 2019 ("2000–2018-equivalent")

- TRAIN = every complete season in the Lane-A-audited data with season < 2019. Design
  placeholder: **2000–2018** (19 seasons). The exact list is a Lane-A coverage fact
  (dataset start, completeness, fallback season X if activated) and is frozen in the
  successor freeze packet; this lane fixes only the RULE (all complete seasons < 2019) and
  the placeholder.
- A season that starts earlier than the audited coverage (e.g. 1999 if present) may serve as
  **Elo warmup only** under FROZEN-PROTO's fallback/warmup discipline (rating updates under a
  documented ordering; never training rows, never scoring rows, never selection rows) unless
  Lane A certifies it complete and reliable, in which case it is an ordinary TRAIN season.
- TRAIN is the **only** territory in which selection, grid search, gate evaluation, and any
  outcome-informed design choice may occur for the successor program.

### 1.3 PROSPECTIVE window — 2026 forward

- All genuinely new NFL evidence is 2026 forward, and 2026+ is **PROSPECTIVE ONLY**:
  admissible evaluation rows are exclusively prediction-ledger rows recorded strictly before
  kickoff (Section 4). There is no retrospective arm of the prospective window.
- **Played-before-record law.** Any 2026+ game whose actual kickoff precedes the successor
  cycle's freeze/prediction timestamps — i.e., any game already played when the program
  starts — is `NOT_RUN` prospective, permanently. It is never backfilled, never presented as
  a pre-game forecast, and never pooled into prospective aggregates. If the successor
  launches mid-season, weeks already played are written off in the freeze packet with the
  count disclosed.
- Per-season size: ~270 regular-season games (disclosed exactly per season at scoring,
  tie-excluded count disclosed). One NFL season is thin by design; see the ≥2-season rule
  (Section 7).

## 2. Train-internal selection (frozen before any prospective look)

Every free parameter of every arm — SOS coefficient β, home/away split strength λ, rating
carryover ρ, EPA-prior blend weight, interaction block membership and bucket edges, any
threshold or grid point — is selected **inside TRAIN only**, by a rolling-origin scheme, and
frozen in the successor freeze packet **before the first prospective row is recorded**. No
test-window peeking exists in this design because the only evaluation window accrues in the
future.

### 2.1 Rolling-origin scheme inside TRAIN

- Unit = season. Folds = expanding window by season over the **tail of TRAIN**: the freeze
  packet pins the exact inner-fold list (design placeholder: inner test seasons = the last 5
  TRAIN seasons, e.g. 2014..2018 under the placeholder; inner train = all complete TRAIN
  seasons strictly before each inner test season). Inner folds are pinned before any
  selection run.
- Selection criterion: mean log loss over the inner test seasons, pooled across inner folds
  (same clamp as Section 5). Tie-break: the simpler config (fewer active parameters; if
  still tied, the lexicographically smaller config id). Per-fold tables are recorded for the
  winner AND for every evaluated grid point (trial accounting extends to train-internal
  trials: every evaluated config enters a **selection ledger** disclosed in the freeze
  packet).
- Deterministic solver and standardization exactly as FROZEN-PROTO §2-B2 (L2 = 1.0 on
  standardized features, intercept unpenalized, tolerance 1e-8, seed 20261005) wherever a
  fitted estimator is used. L2 = 1.0 stays a preregistered stability constant, not a tuned
  value; changing it is a new trial.
- **B1\* is exempt from selection** by law: K=40, HCA=0, γ=2/3 are frozen from the terminal
  cycle (BASELINE LAW). Re-tuning B1\* on TRAIN or anywhere is prohibited (dead-arm
  discipline for the HCA grid; the K=40/HCA=0 point is the inherited baseline, not a grid
  candidate). B0 is exempt (intercept-only refit is its entire spec).

### 2.2 What freezes

The successor freeze packet must contain, before the first prospective row:
(a) exact TRAIN season list and inner-fold list; (b) for every arm with free parameters: the
full grid, the selection-ledger row per evaluated config, and the selected config; (c) the
final arm enumeration of Section 3 including the reserve arm's identity or its explicit
release; (d) fallback status X (or "not activated"); (e) neutral-site flag status;
(f) recorder role, cadence and safety margin (Section 8); (g) ledger GENESIS digest
(LEDGER_SCHEMA.md §Validation R1); (h) pooling plan if any (Section 7.3); (i) the frozen
T/R thresholds restated verbatim (Section 5.3). After this freeze, selection is closed; any
post-freeze config change is a new registered trial.

## 3. Frozen arm budget (≤9, binding)

Registered before any prospective row. Slots are **released, never reallocated**: a slot
whose arm is not fielded stays empty for the life of the cycle.

| Slot | Arm | Spec | Role |
|---|---|---|---|
| 1 | B0 | constant home-win rate, TRAIN-only refit (per Section 5 fold definition) | floor; registered reference |
| 2 | **B1\*** | own-Elo K=40, HCA=0, γ=2/3, carried across seasons with one-third reversion — FROZEN from terminal cycle, not selectable | mandatory baseline; all candidate comparisons primary vs B1* |
| 3 | C1 | Lane-B candidate mechanism #1 (plan priority: SOS-adjusted Elo) — binds to Lane B's handoff | candidate |
| 4 | C2 | Lane-B candidate mechanism #2 (plan priority: home/away split rating) — binds to Lane B's handoff | candidate |
| 5 | C3 | Lane-B candidate mechanism #3 (plan priority: offseason EPA prior, train-only) — binds to Lane B's handoff; runs ONLY if Lane A proves PIT-proven as-of availability, else released `NOT_RUN_PIT` | candidate |
| 6 | C-INT | conditional interaction arm (plan: short-week×away interaction; final identity from Lane B) — fielded ONLY if gate G-INT passes (Section 6.3); else slot released | conditional candidate |
| 7 | RESERVE | ONE pre-registered reserve — must be named in the freeze packet before any prospective row; unused at freeze ⇒ slot released, never reallocated | reserve |
| 8 | — | RELEASED | — |
| 9 | — | RELEASED | — |

- Worst case fielded: 7 arms (B0, B1*, 3 candidates, interaction, reserve). The enumeration
  above is the freeze-doc binding form; the ≤3 Lane-B candidate slots bind to Lane B's
  handoff (which had not landed when this lane closed — open question OQ-1). If Lane B
  proposes fewer than 3 mechanisms, the unused slots are released.
- **Negative controls are diagnostic arms, not budget arms.** Each candidate mechanism Cm
  carries exactly one time-shuffled twin (preserved marginals, per MECHANISMS §1-F11 /
  §3.5), reported alongside its parent in a diagnostics table. A negative control can never
  win: it is never counted as a candidate win and never enters PASS/REJECT logic. If a
  candidate's shuffled twin also beats its reference (train-internal or prospective), the
  candidate is **UN-SCORED pending machinery audit** — a fail of the comparison machinery,
  not a pass of the mechanism.
- Replacement-rating shapes are preferred per plan; additive logistic-over-Elo layers are
  dead (§0.10) and are ineligible as candidate mechanisms.

## 4. Prospective prediction ledger (design; exact schema in LEDGER_SCHEMA.md)

- **Append-only JSONL**, one row per (game, arm). The ledger contains **no outcome columns
  of any kind** (no scores, no results): it is a pure pre-game prediction record. Outcomes
  are joined at scoring time from the Lane-A-audited final data, never written back.
- **TIMESTAMP LAW.** Every row carries `recorded_at_utc` (ISO 8601 UTC) and
  `kickoff_utc` (scheduled kickoff as known at record time). The validator enforces
  `recorded_at_utc < kickoff_utc` strictly at append time AND re-validates at scoring time
  against the **actual** kickoff from final data. A row failing either check is
  `INVALID_PROSPECTIVE`: excluded from all aggregates, count disclosed, never deleted,
  never patched.
- **Retro-injection impossibility.** Rows are hash-chained: `row_hash` = SHA-256 over the
  canonical serialization of the row including `prev_row_hash`; the first row anchors to the
  freeze packet's GENESIS digest. The file is opened append-only; any backfill, edit, or
  reorder breaks the chain and invalidates every row from the break forward (disclosed as a
  ledger-integrity failure — a program-level stop event, Section 6.4).
- **No retrospective injection.** Because each row is timestamped and chained, a prediction
  made after kickoff cannot masquerade as pre-game: the scoring-time re-validation against
  actual kickoffs classifies it `INVALID_PROSPECTIVE`. Games with no row are simply
  `NOT_RUN` (missing evidence, never inferred PASS).
- **Immutability.** No row is ever edited or deleted. A config error discovered after
  recording invalidates the entire arm's prospective stream (all its rows classified
  `INVALID_PROSPECTIVE`, disclosed); rows are never patched in place.
- **Duplicates.** At most one row per (game_id, arm_id); validator enforces.
- **Information-set honesty.** A weekly batch necessarily predicts later-in-week games from
  an earlier rating/feature state. The as-of law is an upper bound on the legal information
  set; using a strictly smaller, fixed, pre-declared subset is admissible. Each arm's frozen
  config must declare its recording-time information-set rule (e.g., "ratings/features as of
  the last completed game strictly before the batch timestamp"), and identical-kickoff
  exclusion still holds inside the pipeline (each game's p computed from the state excluding
  its own and simultaneous games' results).
- **Postponement / flex / cancellation.**
  - Postponed or flexed to a LATER time: the row remains `VALID_PROSPECTIVE` if
    `recorded_at_utc < actual kickoff` (the prediction was made before the game was played);
    moved-game count disclosed.
  - Moved EARLIER past `recorded_at_utc`: `INVALID_PROSPECTIVE`.
  - Cancelled (no result): `NOT_SCORED_CANCELLED`, disclosed, no outcome join.
- Model version pinning: each row carries `model_version` (pipeline commit sha) and
  `inputs_digest` (sha256 over the versioned input-snapshot manifest used at record time),
  so any row is reproducible against archived inputs (LEDGER_SCHEMA.md).

## 5. Metrics and uncertainty

### 5.1 Metrics (identical game sets per comparison; clamp [1e-15, 1−1e-15])

- **PRIMARY: mean log loss** `LL = −mean[y·ln p + (1−y)·ln(1−p)]` on `VALID_PROSPECTIVE`
  regular-season rows, ties excluded per TIE LAW (count disclosed).
- Secondary: Brier score `mean[(p−y)²]`; 10 equal-width reliability bins on p with
  (n, mean p, observed rate) per bin; **calibration slope** = binomial-GLM (logit link)
  coefficient of `logit(p)` in `outcome ~ 1 + logit(p)`. Slope 1 = calibrated; <1
  overconfident; >1 underconfident. **Band: [0.85, 1.15]** (inherited).
  Note (clarification, not amendment): B0's slope is degenerate (constant p ⇒ constant
  logit(p) ⇒ GLM unidentifiable); B0's calibration slope is reported `N/A (degenerate)` in
  all successor tables. The terminal cycle's B0 slope values (e.g. −4.278 pooled) exhibit
  exactly this degeneracy (TERMINAL, cited).
- **Playoffs separate.** Playoff rows are scored with the same frozen config, reported
  separately per season and pooled-separately; NEVER pooled into regular-season headline
  aggregates, never silently dropped (inherited; TERMINAL precedent: pooled_rs n=1865 vs
  separate playoff n=89). Super Bowl rows carry the neutral-site caveat.

### 5.2 Paired uncertainty

- Per-game paired `ΔLL = LL(arm) − LL(reference)` on identical game sets. 95% CI by block
  bootstrap resampling **kickoff calendar dates** with replacement (clusters = kickoff
  dates: same-day games share rating state and schedule context). 10,000 resamples,
  percentile CI.
- **Seed decision: INHERIT 20261005.** Rationale: the seed is not a tuning knob, no outcome
  was ever selected with it, and keeping it preserves comparability of machinery with both
  terminal cycles. Registering a new seed would add a free choice without information.
- Sign convention: Δ < 0 favors the arm; Δ > 0 favors the reference.
- Reporting: per prospective season AND pooled across completed prospective seasons
  (pooled = all completed prospective seasons' regular-season VALID rows).

### 5.3 Gates (T-shape inherited) and negative terminals (R1–R3 re-stated)

"CI" = kickoff-date-clustered bootstrap 95% CI of Section 5.2. Let C = program candidate
(best candidate arm per the pre-registered candidate-ranking rule: lowest pooled
prospective LL among slots 3–6; ranking rule registered in the freeze packet).

Program PASS for C requires ALL of:
- **T1 (discriminative gain over B1\*)**: pooled ΔLL(C, B1*) has CI entirely < 0 AND
  per-season ΔLL(C, B1*) < 0 on ≥ half of completed prospective seasons.
- **T2 (calibration)**: pooled calibration slope of C ∈ [0.85, 1.15].
- **T3 (floor safety)**: no completed prospective season where Brier(C) > Brier(B0), AND
  pooled ΔLL(C, B0) has CI entirely < 0.

REJECT (negative terminal) if ANY of:
- **R1**: CI of pooled ΔLL(B1*, B0) includes 0 or lies entirely > 0 → own-Elo dynamic
  strength adds nothing over the constant baseline at this grain → program premise fails.
- **R2**: pooled ΔLL(C, B0) CI entirely > 0 → candidate is worse than the constant baseline.
- **R3**: pooled ΔLL(C, B1*) CI entirely > 0 AND T2 violated → both degradation vs the
  dynamic baseline and miscalibration.

INCONCLUSIVE: all decision CIs include 0 while T2 holds → no PASS; no re-tuning, no
threshold relaxation, no metric substitution, no baseline substitution; continuation
requires a new registered cycle with a NEW mechanism claim (verbatim inheritance).
Single-season results are never PASS/REJECT terminals regardless of gates (Section 7).

## 6. Stop rules

### 6.1 Per-arm early-kill (train-internal only — never spend the prospective window)

An arm is killed before the prospective window opens if ANY of:
- **G-SELECT failure**: its free parameters could not be selected inside TRAIN under §2
  (empty or degenerate grid, non-convergence, or selection-ledger evidence that the chosen
  config does not run deterministically).
- **G-ENTRY failure**: train-internal rolling-origin pooled ΔLL(arm, B1*) has CI entirely
  > 0 (confidently worse than the mandatory baseline on TRAIN's own OOS folds), OR
  train-internal calibration slope outside [0.85, 1.15], OR its shuffled negative control
  also improves over the same reference (machinery suspect, §3).
- **G-PIT failure** (C3 specifically): Lane A does not prove per-record publish timestamps
  → `NOT_RUN_PIT`, slot released.

Killed arms never record a prospective row. ADMIT (fielded prospectively) requires:
train-internal pooled ΔLL(arm, B1*) point estimate < 0 AND slope in band. Weak-but-positive
train-internal evidence admits an arm to accrue prospective evidence; it never converts a
train-internal CI into a claim.

### 6.2 Interaction-arm gate (stricter, per plan)

**G-INT** (slot 6): train-internal pooled ΔLL(arm, B1*) CI entirely < 0 AND per-inner-fold
ΔLL < 0 on ≥ half of inner folds. G-INT failure ⇒ slot released; the interaction claim is
recorded as train-internal-only evidence with its selection-ledger row.

### 6.3 Program-level stops

- **Program stop (selection)**: if ALL candidate slots (3–6) fail G-ENTRY/G-PIT/G-INT, no
  prospective scored cycle launches; the program terminates as a negative/NOT_RUN prep
  result with the selection ledgers as evidence. B0 and B1* are not "candidates" and cannot
  keep a program alive alone.
- **Program stop (operational)**: Lane-A data-supply failure, or ledger integrity failure
  (chain break / validator failure), or owner decision. These are the ONLY prospective-window
  aborts.
- **No outcome-based early kill.** Once the prospective window is open, metric readings do
  NOT stop arms: mid-window stopping on the primary metric is optional stopping and is
  prohibited. Interim per-week metrics may be computed for monitoring and are non-binding;
  decision reads happen once per completed prospective season. An arm fielded prospectively
  runs to the end of the pre-registered evaluation horizon (Section 7) unless an operational
  stop fires.

## 7. The ≥2-new-season rule

- **No single-season NFL OOS result is decisive or terminal.** ~270 regular-season games per
  season (tie-excluded exact count disclosed) cannot support program-level PASS/REJECT at
  the CI widths this machinery produces.
- **Strong conclusions require ≥2 completed prospective seasons** (≈ ≥540 regular-season
  games, ties excluded with disclosure), each evaluated under the identical frozen protocol,
  with per-season columns always shown alongside any pooled aggregate. Only then may T1–T3
  PASS or R1–R3 REJECT be asserted at program level.
- **Pooling plan**: if only partial seasons can accrue (late launch, operational stop), any
  cross-season pooling must be pre-registered in the freeze packet BEFORE the second season's
  first row is recorded; per-season tables are still mandatory; pooled aggregates never
  include the SPENT window (§1.1) and never mix partial-season rows into a "completed
  seasons" claim.
- Single-season outputs are labelled **descriptive** (per-season LL/Brier/reliability/
  slope/ΔLL CIs) and carry the ≥2-season caveat verbatim.

## 8. Operational prediction plan

- **WHO records — controller role.** The successor scored cycle's **controller** (or a
  single designated recorder role it appoints) is the ONLY writer of the ledger file. Lane
  workers never write it. Every append session records `recorded_by` (recorder session id)
  in each row (LEDGER_SCHEMA.md).
- **WHEN — weekly cadence.** One batch per NFL week: all rows for all games of the upcoming
  week (REG and POST) are appended in a single session, strictly before the week's FIRST
  kickoff UTC (typically a Thursday game; UTC ≈ Friday 00:15–00:20 UTC for 2026-format
  Thursday nights — the exact value comes from the audited schedule, never from this
  document). **Safety margin**: the freeze packet pins a margin; design placeholder — batch
  completes ≥ 6 hours before the week's first scheduled kickoff (i.e., by ~18:00 UTC
  Wednesday against a Thursday-night opener), or earlier whenever the schedule demands.
  Playoff weeks follow the same per-round cadence before each round's first kickoff.
- **Kickoff UTC source.** `kickoff_utc` is taken from the Lane-A-audited, versioned,
  frozen schedule snapshot (the same source the rating pipeline consumes); the snapshot id
  enters `inputs_digest`. At scoring, actual kickoffs from the final audited data are
  cross-checked against every row (played-vs-future validation, §4); discrepancies
  (postponements, flexes) are handled per §4 and disclosed.
- **Played-vs-future validation.** Scoring-time validator: for every row,
  `actual_kickoff_utc > recorded_at_utc` AND `actual_kickoff_utc ≥ successor cycle freeze
  timestamp`; violations ⇒ `INVALID_PROSPECTIVE` / `NOT_RUN` with counts disclosed
  (§1.3, §4).
- **Configuration changes mid-season.** None. No arm config, no feature, no threshold
  changes after the first prospective row; the model_version and arm_config_digest in each
  row must match the freeze packet throughout the pre-registered horizon.
- **Late news (scratches, weather).** Arms do not consume quarantined inputs (Section 9);
  no re-prediction is permitted after recording; the recorded row stands. This is a feature
  of the design: predictions are fixed before the week, full stop.

## 9. Quarantine inheritance (NOT_RUN register, carried forward)

| Item | Status | Handling |
|---|---|---|
| Odds columns (spread, moneyline, total, closing line, any shipped probability) | QUARANTINED | dropped at load, names recorded; never features, targets, or cross-calibration targets |
| pbp-derived CURRENT-GAME features (EPA, success rate, WP curves of the game being predicted) | `NOT_RUN_PIT` | pbp is post-game compiled and retro-corrected; never a current-game input |
| Offseason EPA PRIOR (previous-season aggregate, used train-only) | CONDITIONAL | admissible ONLY IF Lane A proves as-of/PIT availability of the compiled source; else `NOT_RUN_PIT` and slot 5 released |
| Injuries / availability | `NOT_RUN_PIT` unless Lane A clears PIT | excluded unless per-record publish timestamps are proven; quarantine stands until Lane A's verdict |
| Historical schedule snapshots / announced kickoff changes | `NOT_RUN_PIT` | features from completed games only; kickoff source per §8 |
| Weather / stadium roof | `NOT_RUN_PIT` | no PIT-proven archive in scope |
| Margin-of-victory multiplier | OUT | re-grid of dead family (§0.10) |
| Tie model (3-outcome) | `NOT_RUN_SCOPE` | TIE LAW inherited |
| 538 / any external forecast | BANNED | leakage by construction |
| Seasons 2019–2025 as evaluation surface | SPENT | cite-only (§1.1) |
| Pre-2019 seasons before audited coverage start | warmup-only | fallback/warmup discipline (§0.2, §1.2) |

## 10. Open questions for the successor freeze doc / owner (stop-condition register)

- **OQ-1 (controller)**: final Lane-B candidate enumeration for slots 3–5 — binds to Lane
  B's handoff, which had not landed when this lane closed. The plan's priorities
  (SOS-Elo, home/away split, offseason EPA prior) are placeholders pending that handoff.
- **OQ-2 (controller + Lane A)**: exact TRAIN season list (dataset start, completeness,
  fallback season X or "not activated"), and neutral-site flaggability status.
- **OQ-3 (owner/controller)**: identity of the RESERVE arm (slot 7) — must be named in the
  freeze packet before any prospective row, or the slot is released.
- **OQ-4 (owner)**: pooling plan shape if the successor cannot secure ≥2 complete
  prospective seasons (Section 7.3), and the launch date (which fixes how much of 2026 is
  written off under the played-before-record law).
- **OQ-5 (controller)**: recorder role assignment and the exact batch margin (§8
  placeholder: ≥6 h).
- **OQ-6 (controller)**: candidate-ranking rule that names C for the T/R gates (design
  placeholder: lowest pooled prospective LL among slots 3–6; must be registered in the
  freeze packet).

## 11. Assumptions and limitations

1. Design-only: no selection run, no metric, no download occurred in this lane; all
   Section 2 machinery is specified, not executed. The selection ledgers referenced do not
   exist yet by construction.
2. TRAIN placeholder 2000–2018 and inner-fold placeholder 2014..2018 are rules-plus-
   placeholders; Lane A's audit can shrink the list (never grow it beyond complete,
   certified seasons < 2019).
3. Prospective accrual is uncertain by nature (late launch, postponements, operational
   stops); the ≥2-season rule and pooling discipline exist precisely because the window is
   thin (~270 games/season).
4. Terminal numbers cited (B0 0.6935, B1* 0.6407, ΔLL −0.0528 [−0.0676, −0.0380], playoff
   n=89, B0 slope degeneracy) are prior evidence from TERMINAL, cited under the spent-window
   law — they are context, never a new evaluation surface.
5. The two-commit procedure for this lane's handoff (commit, measure sha, backfill
   handoff_C.json, tiny second commit) was explicitly authorized by the task instruction and
   supersedes the dispatch packet's single-commit line; recorded here for the audit trail.
