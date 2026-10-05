# MECHANISMS_NBA_NG — Lane B, NBA-WINPROB-NG-PREP-V1 (NBA-adjudicated mechanisms for the 2016+ window)

- lane: B_MECHANISMS · task: nbang-b-mech · date: 2026-10-05 · cycle: NBA-WINPROB-NG-PREP-V1 (ACTIVE_LIGHT, budget 0 scored, NO GO phrase)
- scope: research + protocol design ONLY. No data downloads, no outcome computation, no metric of
  any kind, no git writes. This document proposes; it authorizes nothing and consumes no GO.
- language law (inherited): calibration/forecasting vocabulary only — no PnL/betting/edge words.
- Lane A dependency: the dispatch's named Lane A artifacts were ABSENT at task start
  (`lanes/A_DATA/` empty); a Lane A measurement artifact (`measure_schedule_corpus.json`) landed
  mid-task and its measured counts are adopted (§0, §2). Rights/PIT verdict artifacts remain
  absent — dependent items stay gated (§7).

## 0. Evidence base (immutable history, cited from bytes — never re-run) and binding laws

Terminal facts — NBA-WINPROB-SCORED-V1, `research/control/NBA-WINPROB-SCORED-V1/results/scored_summary.json`
(pooled regular season, log loss primary, paired date-cluster CIs; negative ΔLL favors the arm):

| quantity | value (terminal, 2009–2015, n=8369 RS) |
|---|---|
| B0 (constant) LL | 0.6769 |
| B1* = B1-d own-Elo | K=32, HCA=100, LL 0.5987 |
| B1* vs B0 ΔLL | −0.0782 [−0.0875, −0.0687] |
| HCA=100 vs HCA=0 at K=32 | alive: −0.0215 [−0.0271, −0.0157] |
| T1 rest/form layer (additive over Elo) | FAIL: −0.0010 [−0.0033, +0.0013] |
| recorded calibration slope | 0.989 PASS |
| playoffs (reported separately) | pooled_po n=587 |

Byte-read notes (read directly from the JSON, no re-run): the 0.989 pooled slope corresponds to the
T1 arm B2-a (features `elo_diff, rest_diff, b2b_home, b2b_away, form_home, form_away`; pooled RS
slope 0.9894); the B1* arm's own pooled RS slope reads 0.8606 — both inside the [0.85, 1.15] band.
Fold sizes 2009–2015: 1230 except 2012 (990, lockout) and 2013 (1229).

HARD LAWS binding every hypothesis below (restated verbatim in intent):

1. **Baseline law.** NBA B1* = B1-d own-Elo K=32/HCA=100 is the mandatory baseline. Any new
   mechanism must beat B1*, not merely B0, under the frozen comparison machinery. B1* constants
   are FROZEN — carried verbatim, never re-tuned.
2. **Spent-window law.** TEST seasons 2009–2015 are SPENT (K/HCA/rest/form were grid-searched and
   scored there). No re-grid of K/HCA/rest/form on 2009–2015, ever, in any lane. New evaluation
   window = NBA seasons 2016+ (hoopR corpus) only; 2026–27 games not yet played are PROSPECTIVE ONLY.
3. **Banned families.** Additive logistic-over-Elo feature layers (dead in BOTH terminal cycles);
   MOV/blowout-weighted Elo (re-grid of a dead update family with no new information source);
   538 forecasts; closing/market odds; current-game box scores.
4. **Replacement-rating shape preferred.** New signal enters as a rating-input mechanism
   (initialization, read-time decomposition, venue-constant modulation) — never as features
   stapled to `elo_diff` next to a refit logistic.
5. **Interactions must beat their null parents** (owner law). Any added-parameter estimator is
   scored against the parent with the added parameters constrained to their null values.
6. **Train-only selection.** Every free parameter is fit on a train-internal rolling-origin
   time-split inside the TRAIN sub-window of 2016+, then frozen at registration — no test-window
   peeking before the frozen walk-forward evaluation.
7. **PIT law.** Inputs frozen at the prior tip (knowable strictly before tip-UTC); no retro-fill
   from post-game information, ever.

Corpus facts ($0): hoopR/sportsdataverse releases are rights-cleared per
WINPROB-NG-PREP-V1 lane D (producer LICENSE.md CC BY 4.0 covering "data, code, and documentation"
+ MIT on the sportsdataverse-data release store); 14,254 schedule rows 2016–2026 already at
`~/.my-quantitative-data/nba-hoopr-v1/` (EXTEND-ONLY). Per-season capacity — MEASURED, from
`lanes/A_DATA/measure_schedule_corpus.json` (Lane A measurement artifact that landed mid-task,
2026-10-05T03:40Z; unique_game_id = 14,254, zero duplicate game_ids, 67 postponed rows excluded,
3 All-Star rows excluded): regular-season (season_type=2) played counts — 2016: 1230, 2017: 1230,
2018: 1232, 2019: 1232, 2020: 1061, 2021: 1081, 2022: 1231, 2023: 1231, 2024: 1231 (1164 non-Cup
+ 67 Cup), 2025: 1234 (1166 + 68), 2026: 1235 (1167 + 68). CROSS-LANE NOTE: the dispatch packet
stated 2020 = 1059 / 2021 = 1080 — a small discrepancy vs the measured 1061/1081; this lane uses
the MEASURED figures and flags the mismatch for Lane D adjudication.

## 1. Adjudication summary

| prior proposal | verdict | disposition here |
|---|---|---|
| (a) H-C1 SOS-adjusted Elo | **ADVANCE** | NB-H1, §3.1 |
| (b) H-C2 home/away split ratings | **ADVANCE** | NB-H2, §3.2 |
| (c) H-C4 fatigue×venue interaction block | **ADVANCE, narrow** | NB-H3, §3.3 — away-restricted modulated-HCA shape only |
| (d) F8 pace/efficiency train-only aggregates as rating INITIALIZATION | **ADVANCE, gated** | NB-H4, §3.4 — design-only until Lane A rights verdict |
| H-C3 pre-game availability (injury) | **KEEP NOT_RUN_PIT** | §4 — provenance-audit spec supplied, no source cleared |
| additive logistic rest/form layer over Elo | **REJECT** | dead shape, terminal T1 FAIL in both leagues |
| MOV/blowout-weighted Elo | **REJECT** | re-grid of dead family |
| 538 / closing odds / current-game box scores | **REJECT** | banned by plan |
| K/HCA re-grid on 2009–2015 | **REJECT** | banned spent window |
| rest/form MAIN effects re-tests | **REJECT** | dead mains (NBA T1; NFL rejected) |

Exactly four hypotheses advance — the maximum the dispatch allows.

## 2. Capacity and power on the 2016+ window (arithmetic only; no bootstrap run here)

- Window total (measured, season_type=2 played, Lane A measurement artifact): seasons 2016…2024
  = **10,759 RS games**; through 2024–25 (+1234) ≈ 11,993; the full landed corpus through 2026
  (+1235) ≈ 13,228, of which 13,025 non-Cup regular-season. Cup rows (203, season_type=2,
  2024–2026, 7 with neutral_site = true) plus playoffs (type3) and play-in (type5) are reported
  separately, never pooled into the regular-season headline (terminal precedent: pooled_po n=587).
  2016+-specific fact the venue arms must pre-register: neutral-site Cup games carry NO home
  advantage — `neutral_site == true` rows must have HCA forced to 0 in NB-H2/NB-H3 (PIT-safe,
  knowable from the schedule before tip).
- A frozen walk-forward OOS span of ~6,000–7,000 RS games (Lane C's split design decides) is
  comparable to the terminal window's 8,369. Terminal pooled ΔLL CI half-width was ±0.0094 at
  n=8369; scaling by √(n): expect **±~0.010–0.011 pooled, ±~0.024 per fold (n≈1230)**, ±~0.020 for
  an early-season sub-pool (~2,300–2,600 games).
- Consequence, stated honestly so Lane C can price arms: **a mechanism whose true pooled ΔLL is
  smaller in magnitude than ~0.01 will almost certainly REJECT under the frozen falsifier even if
  its direction is right.** That is the gate working as designed, not a machinery failure. Arms
  with plausibly tiny effects (NB-H3 especially) are kept only in train-kill-first posture and
  priced accordingly in the trial budget (§6).
- Per-term effective n for NB-H3 terms (order-of-magnitude planning ESTIMATES from league-typical
  scheduling rates — to be re-derived from Lane A's normalized corpus before any power claim is
  frozen): away back-to-backs ≈ 400 games/season (~3.3%) → ~3.6k over the window; 3-in-4 away,
  long-travel bucket, and ≥2-zone tz shift away are each rarer (~0.5–1.5 per team-season). Only
  `b2b_away` approaches the counts needed to move a pooled CI.

## 3. Advanced hypotheses (full specifications)

Each carries: mechanism (who is mispriced and why) · exact operationalization on the 2016+ corpus
(allowed data only) · $0 source + rights pointer · as-of law (inputs frozen at prior tip) · frozen
falsifier (REJECT iff pooled 95% CI of ΔLL vs B1* includes 0 OR ≥ half folds non-negative; CI
machinery = paired date-cluster bootstrap, identical to the terminal cycle) · negative control
(time-shuffled twin) · capacity/power estimate on 2016+ · train-internal kill test · designed-null
parent (what result proves the extra parameter is empty).

### 3.1 NB-H1 — SOS-adjusted Elo (read-time schedule-strength decomposition) — from H-C1, priority 1

- **Mechanism.** Raw Elo conflates team strength with opponent quality under the NBA's 82-game
  unbalanced, division-weighted schedule: a soft early schedule inflates a rating faster than the
  K=32 update decays it. Mispriced teams = those whose early opponents were far from league-average
  strength (soft-schedule teams overrated, hard-schedule teams underrated). Pre-registered
  heterogeneity: the effect concentrates in games 1–20 of each season and fades by late season as
  the schedule washes out.
- **Operationalization (allowed data only).** From Lane A's normalized game universe (ESPN
  `game_id` primary key, tip-UTC ordering, `status_type_completed == True`, dedupe law): with R the
  frozen B1* rating stream (K=32/HCA=100 update carried verbatim), compute
  `SOS_i(t) = mean over i's completed games (current season) of opp_Elo_at_tip`, league-mean
  centered; input rating `R̃_i = R_i − β·(SOS_i − mean_SOS)`; prediction
  `p = σ((R̃_home − R̃_away + HCA)/s)` with HCA/s at the frozen B1* values. β is the ONLY new free
  parameter, chosen on the train-internal rolling-origin split, then frozen. This is a read-time
  decomposition of the rating itself — NOT an additive feature next to `elo_diff` (dead shape).
  Zero completed games ⇒ SOS ≡ league mean ⇒ adjustment 0 (well-defined opening night).
- **$0 source + rights.** Game results already in hand: hoopR corpus at
  `~/.my-quantitative-data/nba-hoopr-v1/` (CC BY 4.0 + MIT per WINPROB-NG-PREP-V1 lane D verdict).
  No new downloads; no new rights surface.
- **As-of law.** SOS inputs = games with tip-UTC strictly before the current game's tip-UTC and
  completed status; rating state frozen at the prior tip (B1* update rule untouched — only the
  prediction-time read is modified).
- **Frozen falsifier.** REJECT iff pooled 95% CI of ΔLL(arm, B1*) on the frozen walk-forward OOS
  includes 0 or ≥ half the folds are non-negative (paired date-cluster bootstrap). Control guard:
  the shuffled-SOS twin must NOT produce a CI excluding 0; if it does, the comparison machinery is
  at fault and the hypothesis is UN-SCORED, not PASS.
- **Negative control.** Time-shuffled SOS twin: per-team SOS values permuted across teams within
  each evaluation date, preserving marginals.
- **Capacity/power.** Window n per §2 (10.7k train-side, OOS span per Lane C). Expect pooled CI
  ±~0.010–0.011; early-season sub-pool (~2,300–2,600 games) ±~0.020. Directional sub-analysis by
  games-since-opening-night is reported, but the pooled gate governs.
- **Train-internal kill test.** On the train sub-window rolling origins: if the best ΔLL(β) >
  −0.001 (negligible) or the β response surface is flat/sign-flipping across origins, KILL before
  spending any OOS fold. Cheapest hypothesis end-to-end: one β fit + one Elo re-run on existing $0 data.
- **Designed-null parent.** B1* itself: β = 0 reproduces the parent exactly. A non-zero β that
  fails to beat the parent proves the SOS decomposition carries no incremental log-loss information
  in this shape — the extra parameter is empty.

### 3.2 NB-H2 — Home/away split ratings (shrunk venue-role Elo) — from H-C2, priority 2

- **Mechanism.** Team quality is venue-dependent beyond one league-wide constant: construction
  (rebounding/transition defense), style, altitude, travel patterns. The alive NBA HCA constant
  (−0.0215) shows venue matters at league level; team-heterogeneous home effects predict a constant
  is mis-specified, not necessarily absent (contrast: the NFL constant was rejected outright).
  Mispriced teams = extreme home/away asymmetry teams, priced by B1* with one blended rating.
- **Operationalization.** Two ratings per team (`R_home`, `R_away`) plus a common rating; the
  venue-role rating is the one updated at each game, shrunk toward the common rating with weight λ:
  `R_role ← (1−λ)·R_role + λ·(R_common + K·outcome_term)` — the exact update form MUST be written
  verbatim in the freeze document at registration. Prediction `p = σ((R_home_i − R_away_j + HCA)/s)`,
  HCA/s frozen at B1* values. λ ∈ [0,1] is the only new parameter, fit train-internal, frozen.
  λ = 0 ⇒ exact B1* parent.
- **$0 source + rights.** Same results feed as NB-H1 (hoopR corpus, CC BY 4.0 + MIT). Genuinely new
  signal extracted from the same $0 bytes; no new rights surface.
- **As-of law.** Both role and common ratings updated only on completed games strictly before tip;
  no current-game information.
- **Frozen falsifier.** REJECT iff pooled 95% CI of ΔLL vs B1* includes 0 or ≥ half folds
  non-negative; ADDITIONAL capacity reject: if the realized rating split collapses — pre-registered
  threshold: mean absolute `|R_home − R_away|` across teams < 10 Elo points — the data cannot
  support the extra parameter; reject on capacity grounds regardless of CI.
- **Negative control.** Venue-label permutation twin within train: permute the venue-role
  assignment across each team's games preserving counts. Any gain surviving permutation =
  implementation/leak bug, not signal.
- **Capacity/power.** Same window n as NB-H1. The shrinkage λ bounds variance, so the arm loses
  little if heterogeneity is noise — but the gate is unchanged; small true effects reject by design.
- **Train-internal kill test.** If argmax λ ≈ 0 (within the frozen grid resolution) or train ΔLL >
  −0.001, KILL before OOS. Venue permutation must erase the train gain (else stop — bug, not signal).
- **Designed-null parent.** B1* (λ = 0). A fail proves the two-rating parameterization extracts no
  venue-heterogeneity information the single rating does not already carry.

### 3.3 NB-H3 — Fatigue×venue interaction block as modulated HCA (away-restricted) — from H-C4, priority 3 (lowest)

- **Shape ruling first (banned-shape guard).** The dead B2 shape — rest/form features added to
  `elo_diff` under a refit logistic, with home+away MAIN effects — is banned and stays dead (T1
  FAIL −0.0010 [−0.0033, +0.0013]). NB-H3 is NOT that shape: the away-only fatigue block enters as
  a **modulation of the venue constant**, replacing the single frozen HCA with
  `HCA_eff = HCA − Σ_j θ_j·x_j` where `x_j ∈ {b2b_away, 3in4_away, travel_bucket_away
  (miles since last game: 0–1000 / 1000–2000 / 2000+), tz_shift_away (≥2 zone crossings on the
  road trip)}` and θ is fit train-only, frozen, and scored as ONE joint block. θ ≡ 0 ⇒ exactly
  B1*. This keeps the arm inside the replacement-rating preference (venue-constant modulation) and
  honors the owner law that interactions must beat their null parent.
- **Mechanism.** Fatigue costs are paid primarily by the ROAD team — home back-to-backs are
  cushioned by routine and no travel. The terminal mains averaged home+away and thereby diluted the
  mechanism away; the interaction parameterization is a different sign structure with a different
  prediction (penalties appear only in away games), not a re-test of the dead mains.
- **Operationalization.** Inputs are schedule-derived from Lane A's normalized corpus: rest-day
  gaps from tip-UTC sequences per team; travel buckets from great-circle venue coordinates (static
  public geography); tz crossings from venue timezones. Neutral-site Cup rows: HCA forced to 0
  (§2). Block membership and bucket edges are frozen at registration (no term fishing, no post-hoc
  edge tuning); block tested jointly (one ΔLL), never per-term.
- **$0 source + rights.** Schedule structure + venue geography already inside the hoopR corpus
  (CC BY 4.0 + MIT). No new downloads.
- **As-of law.** Schedule is published pre-season and amended by postponements — as-of handling
  must follow Lane A's postponement/duplicate law; all rest/travel/tz inputs frozen at tip-UTC.
- **Frozen falsifier.** REJECT iff pooled 95% CI of ΔLL(block arm vs its NULL PARENT B1*) includes
  0 or ≥ half folds non-negative. Joint block only. Control guard as for all arms.
- **Negative control.** Time-shuffled travel/rest twins: permute each indicator across team-games
  within season, preserving marginals; must show nothing.
- **Capacity/power.** Honest: this is the arm most likely to REJECT on power grounds. Effective n
  per term is thin (§2): only `b2b_away` (~3.6k games over the window, estimate) approaches CI-
  moving counts; the other terms are decorative unless the train split says otherwise. Pooled gate
  ±~0.010–0.011 on ~half the window's game set (away-gated terms fire on a subset, but the pooled
  ΔLL is computed over all OOS games).
- **Train-internal kill test.** If the train-internal joint ΔLL > −0.001, or θ·x nets to ≈ 0 with
  sign-flipping coefficients across rolling origins, KILL before OOS. If the NBA train kill fails,
  no NFL prospective slot is created (thin ~272 games/season — starvation is the default outcome
  there); this lane advances NBA only.
- **Designed-null parent.** B1* (θ ≡ 0). A fail proves the away-restricted fatigue structure adds
  no incremental log loss beyond the constant HCA — i.e., the interaction parameterization is empty
  in this corpus/window.

### 3.4 NB-H4 — Pace/efficiency train-only aggregates as rating INITIALIZATION — from F8, priority 4, GATED ON LANE A

- **Gate.** DESIGN-ONLY until Lane A records (i) the NBA redistribution-rights verdict for
  hoopR-derived box-score aggregates and (ii) PIT/coverage for the aggregate inputs. Lane A's
  artifacts were absent from this worktree at task close; the inherited WINPROB-NG-PREP-V1 lane D
  verdict (CC BY 4.0 + MIT) is necessary but this cycle's Lane A owns the verdict. If Lane A
  returns FAIL or silence, NB-H4 → NOT_RUN_RIGHTS; the slot is released, never reallocated.
- **Mechanism.** Each October the frozen Elo stream re-learns from results what prior-season
  efficiency already knows; offseason roster moves move true strength while the carried rating
  lags. Seeding opening-night ratings with a prior-season efficiency composite shortens cold-start
  and reduces early-season loss, where B1* is weakest. Mispriced teams: big-offseason-change and
  breakout-young teams whose Elo level lags their true early strength.
- **Operationalization (never a feature layer).** Aggregates (e.g., prior-season net rating per 100
  possessions, z-scored across teams, rescaled to Elo points by a frozen map) enter ONLY as
  season-start initialization: `R_i(opening night) = (1−w)·R_carry_i + w·prior_eff_i`. In-season
  updates are exactly the frozen B1* update (K=32/HCA=100). The offseason treatment of the frozen
  B1* implementation is carried verbatim (mean-reversion/reset is part of the frozen constants,
  never re-inspected or re-tuned here); the prior enters as the documented additional term with w
  the only new parameter. ONE shape frozen at registration; no same-season aggregate, ever.
- **$0 source + rights.** hoopR box scores/pbp via sportsdataverse-data releases (CC BY 4.0 + MIT,
  inherited) — rights verdict for this cycle PENDING Lane A (gate above).
- **As-of law.** Aggregates computed under strict expanding-window cutoffs from games with tip-UTC
  strictly before the prediction season's opening night; every aggregate reproducible from data
  timestamped before the cutoff; expanding-window computation enforced in code (leakage guard).
- **Frozen falsifier.** REJECT iff pooled 95% CI of ΔLL vs B1* includes 0 or ≥ half folds
  non-negative; pre-registered heterogeneity: gain concentrated in October–December folds.
- **Negative control.** Shuffled-prior twin: permute prior_eff across teams within the season,
  preserving marginals; must not beat the parent (train and OOS).
- **Capacity/power.** Same window n; the arm's expected gain lives in ~24% of the window
  (early-season games ≈ 2,600 over 9 seasons) — early-season sub-pool MDE ≈ ±0.020; pooled gate
  governs.
- **Train-internal kill test.** If argmax w ≈ 0 on train-internal rolling origins or train ΔLL >
  −0.001, KILL. Shuffled-prior must show nothing on train as well.
- **Designed-null parent.** B1* with w = 0. A fail proves prior-season efficiency adds no
  cold-start information beyond the frozen carryover — the initialization parameter is empty.

## 4. H-C3 pre-game availability (injury/roster) — KEEP NOT_RUN_PIT, with the audit that must precede any arm

Status: **NOT_RUN_PIT** stands. Lane A's PIT audit was not readable in this worktree at task close;
the prior lane's source survey found no $0 historical archive with verified rights AND trustworthy
per-record publish timestamps (p1ho/nba-injuries: Fox-Sports-sourced, unmaintained; Kaggle
"NBA Injuries 2010–2020": media-sourced, rights unclear; mxufc29/nbainjuries: official-report pull,
recent seasons, rights/coverage unverified). Media-aggregated sets have no trustworthy timestamps —
retro-filled "injury" rows are look-ahead by construction.

If and only if Lane A (or a successor prep task) clears a source, the following provenance audit
must precede ANY modeling arm:

1. **Rights.** License text naming redistribution of the injury-report-derived records; verified
   provenance chain to the NBA official standardized injury report — not media aggregation.
2. **Timestamps.** Per-record publication timestamp field; independently verify ≥100 records via
   archive lookups; every record must be knowable at tip minus the report cadence (game-day report
   publishes ~early afternoon local; previous-day reports for the first of a b2b).
3. **Coverage.** Per-season record counts vs games; missing-report rate; status vocabulary
   stability across 2016+ (Out/Doubtful/Questionable/Probable and legacy labels).
4. **No-retro-fill check.** Rows must not be back-populated from post-game news; spot-check
   injured-player rows against box-score absence — a row whose only evidence is post-game absence
   is leakage by construction and disqualifies the source.
5. **Then (and only then) the arm:** `avail_i(g) = Σ_players expected_minutes_share · status_weight`
   at report publication time; replacement-rating form `R̃_i = R_i + γ·(avail_i − 1)`, γ
   train-only, frozen. Falsifier: identical frozen CI language vs B1*; shuffled-availability
   negative control mandatory; a team-constant score (no within-team variance) is an automatic drop.

Until the audit passes, the H-C3 trial slot is RESERVED (released, never reallocated, §6).

## 5. Interactions-must-beat-null-parents rule (restated, per owner law)

Any hypothesis whose estimator adds parameters on top of a parent estimator is tested against ITS
NULL PARENT — the parent with the added parameters constrained to their null values: NB-H3's θ ≡ 0,
NB-H2's λ = 0, NB-H4's w = 0, NB-H1's β = 0. For every NBA arm here the null parent is B1*
(K=32/HCA=100). Passing B0 is never sufficient; passing a weaker parent is never sufficient. Each
block/parameter set is scored as ONE joint ΔLL on the frozen walk-forward OOS; per-term or
post-hoc cherry-picking after seeing test results is prohibited — the freeze document pins block
membership, bucket edges, and grid resolutions before any test look.

## 6. Trial-budget interface for Lane C (non-binding mapping into the ≤9-arm sketch)

1. B0 constant; 2. **B1* frozen (K=32/HCA=100, mandatory)**; 3. NB-H1 SOS-adjusted Elo; 4. NB-H2
split ratings; 5. NB-H3 modulated-HCA fatigue block (joint); 6. NB-H4 prior-initialization (gated
on Lane A; else released); 7. H-C3 availability slot — RESERVED, activates only if the §4 audit
passes, else released, never reallocated; 8–9. remaining slots are Lane C's jurisdiction (e.g.,
WNBA/other-league arms and the pre-specified reserve). Negative controls are diagnostic arms:
reported, never counted as candidate wins. Train-internal kill tests run before any OOS spend;
a killed hypothesis releases its slot to the freeze document's pre-specified reserve.

## 7. NOT_RUN register and dependency notes (negative-first)

- **Lane A status at task close**: the dispatch's named artifacts (`GAME_UNIVERSE_SPEC_NBA_2016PLUS.md`,
  `PIT_AUDIT_NBA.md`) were ABSENT when this task began (`lanes/A_DATA/` empty); per the dispatch
  stop condition this lane proceeded from the plan. Mid-task (2026-10-05T03:40Z) Lane A landed a
  measurement artifact (`measure_schedule_corpus.json` + `.py`), and its MEASURED played counts
  were adopted here (§0, §2). STILL ABSENT / still gating: the game-universe spec narrative, the
  PIT audit, this cycle's hoopR rights verdict (gates NB-H4), the PIT verdict (gates H-C3), and
  the spread-feature (`game_spread`/`home_favorite`) coverage re-verification. The
  dispatch-vs-measured played-count discrepancy (stated 1059/1080 vs measured 1061/1081) is
  flagged for Lane D — not adjudicated in this lane.
- **Scheduling-feature frequencies** (b2b/3-in-4/travel/tz rates in §2, §3.3) are order-of-magnitude
  planning estimates from league-typical values — NOT measured here (document lane, no corpus
  processing); must be re-derived from Lane A's normalized corpus before any power claim freezes.
- **CI half-width power figures** are arithmetic scalings of the terminal cycle's measured pooled
  CI — not bootstrap computations.
- **B1* offseason rating treatment** never re-inspected (carried verbatim; NB-H4 pinned to
  "frozen constants + documented modification only").
- **NFL arms**: out of scope for this NBA lane; NFL interactions are prospective 2026+ only in
  their own cycle — noted to prevent slot leakage.
- **538 / closing odds / current-game box scores**: banned, not adjudicated further.
- No data was downloaded, no outcome computed, no metric run, and no git write performed in this
  lane. Artifacts land uncommitted; the controller lands them.
