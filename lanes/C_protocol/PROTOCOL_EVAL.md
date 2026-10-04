# PROTOCOL_EVAL — NBA-WINPROB-PREP-V1 · Lane C (Evaluation Protocol)

- Cycle: `NBA-WINPROB-PREP-V1` · Lane: `C_protocol` · Task: `nwp-c-protocol` · Date: 2026-10-04
- Status: DESIGN / PREREGISTRATION ONLY. No evaluation was executed in this prep cycle; every constant below is a preregistration, not a result.
- Scope: v1 = pre-game win probability for NBA games, calibration-only. No betting, no PnL, no market comparison. Accuracy is never called edge.
- Binding effect: the successor scored cycle's plan must inherit Sections 2, 3, 4, 5, 6 and 9 verbatim BEFORE any outcome is observed (freeze-before-scoring doctrine).

## 0. Binding laws inherited (restated, not redefined)

- AS-OF LAW v1: admissible information set for game G = {all completed games with `date_game` strictly < `date_game`(G)} + static identity mappings. Same-day games never inform each other. No time-of-day grain exists in the data.
- LEAKAGE LAWS: own-Elo only (538 `elo_i`, `opp_elo_i`, `elo_n`, `opp_elo_n`, `forecast` are cross-check fixtures, never inputs); franchise continuity (one lineage = one rating stream); neutral-site games cannot be flagged (limitation + sensitivity segment); all features derive from COMPLETED games only (dates of games actually played).
- Doctrine: trial accounting (every evaluated config counts into the observed denominator); freeze before scoring; negative terminal outcomes preregistered; missing evidence is `NOT_RUN`, never inferred `PASS`.

## 1. Hypotheses (max 3, mechanism-first)

### H1 — Dynamic team strength (Elo persistence + slow mean reversion)
- Mechanism: NBA team quality is persistent (rosters and cohorts carry across seasons) but decays toward the league mean through roster turnover, coaching change, and regression. A rating stream that persists across seasons with partial reversion to 1500 should calibrate better than any static assumption.
- Operationalization: own-Elo stream per franchise lineage (exact spec, Section 2 B1): carried over season-to-season, boundary rule `R <- 1500 + 0.75·(R − 1500)`, K-updates after every completed game.
- Control/ablation that could kill it: B0 (constant home-win probability, train-only) is the no-strength floor; the four B1 arms vs B0 is the registered kill comparison.
- Falsification rule: H1 REJECT iff all four 95% CIs of pooled ΔLL(B1-arm, B0) include 0 or lie entirely > 0 (no Elo arm beats the constant baseline out-of-sample).
- Expected failure interpretation: (a) own-Elo implementation bug — run Section 8 tests 1–3 first; (b) both grid endpoints mis-fit for the test era; (c) genuinely no exploitable strength persistence at game grain — itself a notable negative result, not a protocol failure.

### H2 — Home-court advantage (positive, roughly stable magnitude)
- Mechanism: travel, crowd effects, familiarity, and officiating bias push in the same direction era-over-era; a positive, approximately constant HCA in Elo points should improve calibrated probability for near-equal matchups.
- Operationalization: B1 arms add HCA ∈ {0, 100} Elo points to the home rating inside both prediction and update; the HCA=0 arms ARE the ablation (no extra trial cost).
- Control/ablation: paired ΔLL(B1(K,100), B1(K,0)) for K ∈ {16, 32}, plus the Aug–Oct 2020 bubble sensitivity segment (Section 8.4) to separate "HCA shrank" from "neutral-site contamination".
- Falsification rule: H2 REJECT iff, for both K values, the 95% CI of ΔLL(B1(K,100), B1(K,0)) includes 0 or lies > 0, after the bubble sensitivity check.
- Expected failure interpretation: documented modern HCA shrinkage, or neutral-site games polluting "home" rows. A reject means "constant HCA does not calibrate in the test window", not "no home effect exists".

### H3 — Rest / schedule adds information beyond Elo
- Mechanism: fatigue and travel load (rest-day differential, back-to-backs) and short-horizon form (last-K wins) shift win probability conditional on long-run strength; these move faster than any rating stream can absorb.
- Operationalization (B2-a features, exact formulas Section 2): `rest_diff`, `b2b_home`, `b2b_away`, `form_home`, `form_away` on top of `elo_diff`.
- Control/ablation: B2-b drops rest/B2B features (H3 kill test); B2-c drops form features. B2-a vs B2-b isolates rest; B2-a vs B2-c isolates form.
- Falsification rule: H3 REJECT iff the 95% CI of pooled ΔLL(B2-a, B2-b) includes 0 or lies > 0 (rest/schedule carries no incremental signal beyond own-Elo + form).
- Expected failure interpretation: rest effects already priced into Elo dynamics (K partially absorbs them), or date-grain rest is too noisy (postponements, compressed schedules) — clear Section 8.5 before concluding.

## 2. Baselines / models

Common rules. Scoring rows: exactly ONE row per GAME (home perspective), `y = 1{home win}`; the two per-team source rows collapse to one. All arms see identical rows and folds; every paired comparison uses an identical game set; no post hoc row filtering (sensitivity segments are reported alongside, never substituted). Never used as features: `forecast`, `elo_i`, `opp_elo_i`, `elo_n`, `opp_elo_n`, `win_equiv`. `pts`/`opp_pts`/`game_result` are realized outcomes only (targets, rating/form updates) under the as-of law.

### B0 — Constant home-win probability (floor), 1 arm
- `p̂_fold = mean(y)` over the fold's TRAIN regular-season rows (intercept-only logistic = train home-win rate). Refit per fold. No inputs, no features.

### B1 — Own-Elo → logistic of rating diff, 4 arms
Exact Elo spec (all constants preregistered; nothing tuned on outcomes):
- Stream: one rating per franchise lineage (Section 8.3 census). Every lineage starts at R=1500 at its first completed game in the audited data; the stream updates on EVERY completed game (regular + playoff) from dataset start forward.
- Choice — CARRIED-OVER with mean reversion toward 1500 (NOT per-season re-init at 1500). Justification: (i) NBA quality is persistent across seasons — this is H1's own mechanism, and re-initializing discards exactly that signal; (ii) re-init forces the model to relearn team strength from ~20 games each season, visibly degrading early-season calibration; (iii) reversion to the league prior 1500 bounds drift under roster turnover. Season-boundary rule: before a lineage's first PREDICTION of a new `year_id`, `R <- 1500 + 0.75·(R − 1500)`. γ = 0.75 is FIXED, not gridded (budget); γ sensitivity is out of scope for v1.
- Prediction for game G (home H, away A): `p_home = 1 / (1 + 10^{−(R_H + HCA − R_A)/400})`, with R as of the close of all games with `date_game` strictly < `date_game`(G).
- Update after completion — binary result only, NO margin-of-victory multiplier in v1: for each team `R <- R + K·(S − E)`, `S ∈ {1,0}` realized, `E` = expected score from the prediction formula. All updates for date d are applied only AFTER all predictions for date d (same-day exclusion law).
- Preregistered grid (2×2 = 4 arms): K ∈ {16, 32} Elo points (brackets the canonical NBA operating point ≈20 from slow and fast sides); HCA ∈ {0, 100} Elo points (0 = H2 ablation; 100 = canonical FiveThirtyEight-style magnitude). Locating an interior optimum HCA ∈ (0,100) is explicitly NOT a v1 question — no outcome-driven tuning is permitted.

### B2 — Logistic regression on PIT features, 4 variants
Feature formulas (all strictly as-of; own-Elo only; completed games only):
- f1 `elo_diff` = R_home − R_away (as-of own ratings; HCA deliberately NOT added — the home effect is carried by the intercept, making it interpretable for H2).
- f2 `rest_diff` = rest_days(home) − rest_days(away), where `rest_days(team, G) = min(10, date_game(G) − date(team's most recent completed game strictly before date_game(G)))`; no prior completed game in the data → 10 (cap).
- f3 `b2b_home` = 1{rest_days(home) ≤ 1}; f4 `b2b_away` = 1{rest_days(away) ≤ 1}. (rest_days = 0 rows should not exist; if found: count as B2B and investigate, Section 8.5.)
- f5 `form_home` = (wins/games − 0.5) over the home team's last ≤10 completed REGULAR-SEASON games of the current `year_id` strictly before `date_game`(G); zero such games → 0. f6 `form_away` analogous.
- Estimator: logistic regression, L2 penalty 1.0 on standardized features (z-score mean/std fitted on TRAIN rows of the fold only; intercept unpenalized), deterministic solver to tolerance 1e-8, fixed seed 20261004. Refit per fold. (L2=1.0 is a preregistered stability constant, not a tuned value; changing it = new trial.)
- Frozen variants:
  - B2-a (full): f1–f6. H3 live arm; program candidate.
  - B2-b (no-rest): f1, f5, f6. H3 KILL TEST.
  - B2-c (no-form): f1, f2, f3, f4. Form ablation.
  - B2-d (elo-only): f1. Bridge diagnostic between B1 and B2 (same input, fitted slope instead of parametric transform).
- Training rows: REGULAR-SEASON games of train seasons only. Playoff games never enter B2 training, but DO update the rating stream feeding f1 (completed-games law). This choice is justified in Section 8.6.

## 3. Walk-forward design

- Unit = season (`year_id`). Folds = expanding window by season.
- PLACEHOLDER RULE (binding): **test = final 7 complete seasons in the lane-B-audited data, frozen after B.** The controller fixes the exact list after the byte audit; the modeler may never choose test seasons after seeing outcomes. If the data ends with the 2022-23 season, the placeholder list is 2016-17 … 2022-23.
- Fold k (k = 1..7): train = all complete seasons strictly before test season k; predict every REGULAR-SEASON game of test season k. B1 rating streams are not "refit" (they are fully determined by the as-of law and the arm's constants); B0 and B2 refit per fold.
- PRIMARY evaluation set = regular-season games of the 7 test seasons. Playoff games of test seasons are scored with the SAME frozen fold model, reported SEPARATELY per fold; never pooled into primary aggregates; never silently dropped.
- Anomaly-era folds: 2019-20 (bubble) and 2020-21 (empty arenas) stay in primary by default; the Aug–Oct 2020 segment is additionally reported WITHOUT as a sensitivity column (Section 8.4/8.7). No silent exclusion in either direction.

## 4. Metrics

Computed on identical game sets per comparison; probabilities clamped to [1e-15, 1−1e-15].
- PRIMARY: mean log loss `LL = −mean[y·ln p + (1−y)·ln(1−p)]`.
- Secondary: Brier score `mean[(p − y)²]`.
- Reliability: 10 equal-width bins on p ([0,0.1),…,[0.9,1.0]); report (n, mean p, observed rate) per bin. Calibration slope = binomial-GLM (logit link) coefficient of `logit(p)` in `outcome ~ 1 + logit(p)`. Slope 1 = calibrated; <1 overconfident; >1 underconfident. Report pooled and per fold.
- Paired comparisons: per-game `ΔLL = LL(arm) − LL(reference)`. 95% CI by block bootstrap resampling game DATES with replacement — clusters = dates, because same-date games share rating state and schedule context (correlated errors). 10,000 resamples, seed 20261004, percentile CI. Report per fold AND pooled (pooled = all 7 test seasons' regular-season games).
- Sign convention: Δ < 0 favors the arm; Δ > 0 favors the reference.

## 5. Trial budget (FROZEN; total ≤ 9 arms)

| # | Arm  | Spec | Role / registered comparison |
|---|------|------|------------------------------|
| 1 | B0   | constant home-win rate, train-only refit | floor; H1/H2 reference |
| 2 | B1-a | K=16, HCA=0,   γ=0.75 | H1 live; H2 ablation |
| 3 | B1-b | K=16, HCA=100, γ=0.75 | H1 live; H2 live |
| 4 | B1-c | K=32, HCA=0,   γ=0.75 | H1 live; H2 ablation |
| 5 | B1-d | K=32, HCA=100, γ=0.75 | H1 live; H2 live |
| 6 | B2-a | f1–f6 (full) | H3 live; program candidate |
| 7 | B2-b | f1,f5,f6 (no rest) | H3 kill test |
| 8 | B2-c | f1,f2,f3,f4 (no form) | form ablation |
| 9 | B2-d | f1 only (elo-only) | B1↔B2 bridge diagnostic |

- TOTAL = 9 arms (B0 = 1; B1 grid = 4; B2 variants = 4 incl. H3 ablation). Budget is binding.
- FREEZE LAW: grid, features, folds, metrics, and thresholds must be preregistered in the successor scored cycle's plan BEFORE any evaluation on real outcomes. Any arm, feature, fold, metric, or threshold added after seeing any outcome = a NEW registered trial outside this budget, no exceptions. Retuning γ, widening the K/HCA grid, adding margin-of-victory or momentum features, or changing the fold count are all new trials.

## 6. PASS/FAIL thresholds for the scored phase (calibration-only)

Sign convention per Section 4; "CI" = date-block bootstrap 95% CI.

Program PASS for B2-a requires ALL of:
- T1 (discriminative gain over best Elo): pooled ΔLL(B2-a, B1*) has CI entirely < 0 AND Δ_f(B2-a, B1*) < 0 on ≥ 4 of 7 folds (≥ half), where B1* = the B1 arm with the lowest pooled primary LL. (Selecting B1* on pooled test LL is itself registered and stays inside the frozen arm set.)
- T2 (calibration): pooled calibration slope of B2-a ∈ [0.85, 1.15].
- T3 (floor safety): no fold where Brier(B2-a) > Brier(B0), AND pooled ΔLL(B2-a, B0) has CI entirely < 0.

REJECT (negative terminal) if ANY of:
- R1: CI of pooled ΔLL(B1*, B0) includes 0 or lies entirely > 0 → own-Elo dynamic strength adds nothing over the constant baseline → program premise fails at this grain.
- R2: pooled ΔLL(B2-a, B0) CI entirely > 0 → candidate is worse than the constant baseline.
- R3: pooled ΔLL(B2-a, B1*) CI entirely > 0 AND T2 violated → both degradation vs Elo and miscalibration.

INCONCLUSIVE: all decision CIs include 0 while T2 holds → no PASS; no re-tuning, no threshold relaxation, no metric substitution; continuation requires a new registered cycle with a NEW mechanism claim.

Hypothesis-level verdicts are exactly the falsification rules in Section 1 (H1: B1 arms vs B0; H2: B1(K,100) vs B1(K,0) paired; H3: B2-a vs B2-b paired).

Language law: PASS/REJECT is calibration language only. No PnL, no betting or market comparison, no "edge" vocabulary anywhere in outputs.

## 7. NOT_RUN register

| Item | Status | Reason | v1 handling |
|---|---|---|---|
| Injury reports | NOT_RUN_PIT | no $0 source with historical publish timestamps | excluded; successor needs PIT-provenance |
| Betting / closing odds | NOT_RUN_PIT (+scope: v1 has no betting) | no timestamped $0 archive; PnL out of scope | excluded |
| Lineups / rotations | NOT_RUN_PIT | same PIT provenance gap | excluded |
| Time-of-day as-of (intraday ordering) | NOT_RUN_PIT | `date_game` has no reliable time | date-strictly-before law only |
| Seasons after 2022-23 | NOT_RUN_SCOPE | sports freeze 2023-06-13 | data ends ~2022-23 |
| Margin-of-victory Elo multiplier | NOT_RUN_SCOPE | excluded from frozen grid | binary update only |
| γ (season-reversion) grid | NOT_RUN_SCOPE | ≤4-arm B1 budget | fixed at 0.75 |
| Neutral-site flagging | NOT_RUN_PIT | not derivable from nbaallelo.csv | sensitivity segment only (Sec 8.4) |
| Schedule-snapshot features (pre-announced postponements, published schedules) | NOT_RUN_PIT | requires historical snapshot sources | features from completed games only |
| Playoff-specific model | NOT_RUN_SCOPE | budget + distribution shift | frozen-model playoff report only (Sec 8.6) |

## 8. Pitfalls checklist (exact test per pitfall)

1. **Precomputed-Elo leakage** (538 `elo_i`/`forecast` as hidden input). Static test: feature-construction code must not reference `elo_i`, `opp_elo_i`, `elo_n`, `opp_elo_n`, `forecast`, `win_equiv` (grep-level check in the scored cycle). Behavioral test: per fold, report mean|own-Elo implied p̂ − 538 `forecast`| and rank correlation on test games. Near-exact agreement (mean |Δ| < 5 Elo-equivalent points, or ρ > 0.999 with mean |Δ| < 1 point) → INVESTIGATE implementation for accidental copying. Large divergence (ρ < 0.9) → also investigate (likely bug in K/HCA/γ or lineage map). Investigate, never copy: 538 values must never be patched in to close a gap; `forecast` is a cross-check fixture only.
2. **Same-day ordering** (violation of the exclusion law). Unit test: synthetic same-date pair — a team's "second" game on date d must be predicted from ratings/features that exclude the first game's result. Property test over all rows: every feature-source game has `date_game` strictly < target `date_game`; any equal-date source fails the audit.
3. **Team rename / franchise continuity**. Census test: enumerate all distinct (team_id, fran_id, year_id) triples; assert the lineage map assigns every team_id to exactly one franchise lineage; assert a lineage's rating stream resets to 1500 ONLY at dataset start, and is otherwise continuous except the season-boundary reversion rule. Any team_id under two lineages, or any lineage gap, fails the audit (one lineage = one rating stream).
4. **Neutral-site games** (unflaggable in this data). Default: HCA applied everywhere (declared limitation). Sensitivity test: re-score test games with `date_game` ∈ [2020-08-01, 2020-10-31] (bubble) with HCA = 0 for all B1 arms; report every arm's calibration on this segment with AND without the segment in aggregates. Never silently pooled, never silently dropped.
5. **Postponed games** (handled by completed-only construction). Rating updates, rest, and form derive ONLY from games actually played, at their actual dates. Tests: (a) post-cap rest_days ∈ {1..10} — no negative values, and no 0 values except investigated anomalies; (b) no feature references a date on which that team had no completed game; (c) known postponement clusters (e.g., Jan 2022 COVID pauses) produce rest spikes, not negative gaps.
6. **Playoff leakage** — DECISION (adopted recommendation): fit and test on the REGULAR SEASON; playoffs are ONLY a separately reported scored segment using the same frozen fold model. Justification: playoff games differ structurally (rest patterns, selection/matching, intensity), so pooling them into primary distorts calibration claims, while excluding completed playoff games from the rating stream would violate the completed-games law and waste information (they still update B1/B2 ratings for later games). Test: assert zero playoff rows in any B2 training set and zero playoff rows in any primary aggregate; playoff rows appear only in the separately labeled report, never pooled silently.
7. **COVID-season anomalies** (2019-20 bubble; 2020-21 empty arenas): both remain in primary by default (they sit inside the test window; default exclusion is forbidden and would itself need a new registered trial). Sensitivity columns with/without the Aug–Oct 2020 segment; per-fold tables always flag these two seasons so anomalies cannot hide inside a pooled mean.
8. **Row double-counting** (two rows per game in nbaallelo). Test: exactly one prediction row per game_id; y consistent with `pts` vs `opp_pts` and `game_result` on every row.
9. **Outcome-column contamination**: `forecast`/`elo_i`/`win_equiv` never in any feature set (cross-check only); `pts`/`opp_pts` used solely as realized outcomes for rating/form updates and y, never as predictors.

## 9. GO gate for the successor scored cycle

GO phrase (exact): **`GO NBA WINPROB SCORED V1 EVALUATION`**

The controller may issue it only after: (a) lane-B byte/schema audit lands clean; (b) the final 7 test-season list is frozen; (c) Sections 2–6 and this section are inherited verbatim into the scored cycle's plan.

Preregistered negative terminal outcomes (must appear verbatim in the successor plan):
- NEGATIVE-TERMINAL (calibration): If any REJECT condition R1–R3 (Section 6) obtains on the frozen protocol, NBA-WINPROB v1 terminates as a negative calibration result. Prohibited responses: re-gridding K/HCA/γ, adding or mutating features, changing folds, metrics, or thresholds, relaxing CI or slope gates, substituting baselines, or reframing via accuracy/PnL. Continuation requires a new registered cycle with a NEW mechanism claim.
- NEGATIVE-TERMINAL (audit): If the lane-B audit fails, the scored phase is NOT_RUN. Missing evidence is NOT_RUN, never inferred PASS.
- TRIAL LAW: Any arm, feature, fold, metric, or threshold introduced after any real outcome is observed is a NEW registered trial outside this budget, no exceptions.

## 10. Assumptions & limitations (lane B / controller must confirm)

1. Column semantics per upstream README as restated in the dispatch: `year_id` = season; `date_game` parseable to a date; `game_location` ∈ {H, A}; `game_result` ∈ {W, L} consistent with `pts`/`opp_pts`; `is_playoffs` ∈ {0, 1}; one row per team per game; `game_id` unique per game. Lane B must confirm byte-level.
2. 2022-23 is COMPLETE in the data (Finals ended ~2023-06-12 < freeze 2023-06-13). Confirm the last `date_game`. If the final season is incomplete, the "final 7 complete seasons" rule drops it automatically.
3. No NBA team plays two games on the same date (assumed). `rest_days = 0` rows, if found, are anomalies to investigate (Section 8.5), not silently kept.
4. Franchise continuity is assumed derivable from `fran_id` lineage in the data alone. If renames/moves break lineage, the controller must supply the static identity mapping (permitted by the as-of law as a static mapping).
5. `notes` is not machine-reliable for neutral-site flagging; not used.
6. `forecast` is 538's own pre-game probability: cross-check fixture only, never an input or target.
7. Test seasons = 2016-17 … 2022-23 IF the data ends at 2022-23 — a placeholder; the controller freezes the exact list after lane B.
8. No evaluation was executed in this prep cycle: every number here is a design constant, not a result. H2 grid endpoints bracket rather than fine-tune; locating an interior optimal HCA is explicitly out of scope (no outcome-driven tuning in v1).
9. B2 uses L2 = 1.0 on standardized features — a preregistered stability choice, not a tuned value; changing it is a new trial.
10. Elo streams initialize at dataset start (~1946-47); the first expanding-window fold is decades later, so burn-in is immaterial in practice. If the controller trims history, burn-in adequacy must be re-argued before freezing.
