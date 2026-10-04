# PROTOCOL_EVAL_NFL — NFL-WINPROB-PREP-V1 · Lane C (Evaluation Protocol)

- Cycle: `NFL-WINPROB-PREP-V1` · Lane: `NFL_C_protocol` · Task: `nfl-c-protocol` · Date: 2026-10-04
- Status: DESIGN / PREREGISTRATION ONLY. No evaluation was executed in this prep cycle; every constant below is a preregistration, not a result.
- Scope: v1 = pre-game win probability for NFL games, calibration-only. No betting, no PnL, no market comparison. Accuracy is never called edge.
- Binding effect: the successor NFL-WINPROB-SCORED-V1 plan must inherit Sections 2, 3, 4, 5, 6 and 9 verbatim BEFORE any outcome is observed (freeze-before-scoring doctrine).
- Template: mirrors `nba-winprob-scored-v1/integration/lanes/C_protocol/PROTOCOL_EVAL.md` structure and rigor, adapted to NFL; inherited verbatim by the successor scored cycle.

## 0. Binding laws inherited (restated, not redefined)

- AS-OF LAW v1 (KICKOFF GRAIN): admissible information set for game G = {all completed games whose kickoff timestamp `kickoff(G')` is strictly < `kickoff(G)`} + static identity mappings (franchise lineage map). Games with identical kickoff timestamps (simultaneous slates) never inform each other. Same-day, later-kickoff games DO inform earlier-kickoff games — the upgrade kickoff grain buys over date grain.
- FALLBACK LAW (kickoff reliability): if lane B measures that `kickoff` timestamps are unreliable before some season X, then the kickoff-grain law applies as primary ONLY from season X forward; pre-X seasons may serve ONLY as Elo warmup (rating updates under a documented degraded date-grain ordering; never features, never B0/B2 training rows, never primary scoring rows). The activation of the fallback (the value of X, or "not activated") is a LANE-B-MEASURED FACT, frozen in the controller's freeze packet before any scoring. The modeler may never choose X after seeing outcomes.
- GRAIN FLOOR: week-grain features are permitted ONLY if BOTH kickoff grain and day grain fail in the audited data — in which case this protocol is declared `NOT_RUN_PIT` rather than weakened. Byes are handled inside rest-day features (Section 2 f2); no week-grain features exist in the frozen design.
- LEAKAGE LAWS: own-Elo only (no precomputed rating, projection, forecast, spread, moneyline, or total column is ever an input; any odds/probability columns shipped in the source are QUARANTINED — dropped at load, cross-check fixtures at most); franchise continuity (one lineage = one rating stream across renames and relocations); all features derive from COMPLETED games only (games actually played, at their actual kickoffs); score columns are realized outcomes only (labels, rating/form updates) under the as-of law.
- TIE LAW: NFL has ties (overtime draws; historically ~a handful per decade, well under 0.5% of games since 1974). The primary label is binary `y = 1{home team wins}`; TIE GAMES ARE EXCLUDED FROM THE PRIMARY SCORING SET AND FROM B0/B2 TRAINING ROWS, with the tie count disclosed per fold and pooled (never silently dropped). NO tie model is invented: no 3-outcome probabilities are produced anywhere. Ties still count in the rating stream as a standard update convention `S = 0.5` for both teams, and count as half a win in form windows; these are update conventions, not predictive models. Expected count is small; the disclosure makes the sensitivity visible at zero modeling cost.
- Doctrine: trial accounting (every evaluated config counts into the observed denominator); freeze before scoring; negative terminal outcomes preregistered; missing evidence is `NOT_RUN`, never inferred `PASS`.

## 1. Hypotheses (max 3, mechanism-first)

### H1 — Franchise-strength persistence (own-Elo carried across seasons with mean reversion)
- Mechanism: NFL team quality is persistent (coaching trees, quarterback continuity, roster cores carry across seasons) but decays toward the league mean faster than in the NBA because the hard salary cap, draft-order inversion, and one-year contracts compress parity. A rating stream carried across season boundaries with partial reversion to 1500 should calibrate better than any static assumption.
- Operationalization: own-Elo stream per franchise lineage (exact spec, Section 2 B1): carried across season boundaries with reversion rule `R <- 1500 + (2/3)·(R − 1500)` applied before a lineage's first prediction of each new season; K-updates after every completed game (regular + playoff).
- Control/ablation that could kill it: B0 (constant home-win probability, train-only) is the no-strength floor; the four B1 arms vs B0 is the registered kill comparison.
- Falsification rule: H1 REJECT iff all four 95% CIs of pooled ΔLL(B1-arm, B0) include 0 or lie entirely > 0 (no Elo arm beats the constant baseline out-of-sample).
- Expected failure interpretation: (a) own-Elo implementation bug — run Section 8 tests 1–3 first; (b) both grid endpoints mis-fit for the test era (17-game parity may need faster K than either endpoint — but re-gridding is a NEW trial, not a fix); (c) genuinely no exploitable strength persistence at game grain — itself a notable negative result, not a protocol failure.

### H2 — Home-field advantage (positive, roughly stable magnitude)
- Mechanism: travel, crowd noise (audible-influenced offenses), familiarity with stadium conditions, and officiating tendencies push in the same direction era-over-era; NFL home win rate has historically run ~55–60% (modest decline since the 2010s). A positive, approximately constant HCA in Elo points should improve calibrated probability for near-equal matchups.
- Operationalization: B1 arms add HCA ∈ {0, 65} Elo points to the home rating inside both prediction and update; the HCA=0 arms ARE the ablation (no extra trial cost).
- Neutral-site law (conditional on a lane-B fact): IF the audited data carries a validated neutral-site flag (or a venue/city column from which lane B can derive one against a static home-venue map — a static mapping, permitted by the as-of law), THEN flagged games are scored with HCA=0 and EXCLUDED from H2's primary paired estimation (reported as a separate segment, never pooled silently). IF lane B cannot flag them (declared limitation), HCA is applied everywhere and the limitation is documented, with the international-games segment reported if and only if it becomes flaggable; the bound on contamination is small (international games are ≤ ~1% of a 7-season regular-season window; direction: inflates measured HCA).
- Control/ablation: paired ΔLL(B1(K,65), B1(K,0)) for K ∈ {20, 40}; plus the 2020-season sensitivity segment (Section 8.7) to separate "HCA shrank" from "empty-stadium contamination" — re-scoring 2020 games with HCA=0.
- Falsification rule: H2 REJECT iff, for both K values, the 95% CI of ΔLL(B1(K,65), B1(K,0)) includes 0 or lies > 0, after the neutral-site and 2020 sensitivity checks.
- Expected failure interpretation: documented modern HFA shrinkage, or neutral-site/empty-stadium games polluting "home" rows. A reject means "constant HCA does not calibrate in the test window", not "no home effect exists".

### H3 — Rest / schedule adds information beyond Elo
- Mechanism: bye-week rest (~13–14 days), short weeks (Thursday after Sunday ≈ 4 days; Saturday after Sunday = 6), and short-horizon form (last-4 wins) shift win probability conditional on long-run strength; these move faster than any rating stream with per-game K can absorb.
- Operationalization (B2-a features, exact formulas Section 2): `rest_diff`, `short_week_home`, `short_week_away`, `form_home`, `form_away` on top of `elo_diff`. Byes are absorbed by `rest_diff` (no separate bye flag).
- Control/ablation: B2-b drops the rest/schedule features (H3 KILL test); B2-c drops form features. B2-a vs B2-b isolates rest/schedule; B2-a vs B2-c isolates form.
- Falsification rule: H3 REJECT iff the 95% CI of pooled ΔLL(B2-a, B2-b) includes 0 or lies > 0 (rest/schedule carries no incremental signal beyond own-Elo + form).
- Expected failure interpretation: rest effects already priced into Elo dynamics (K partially absorbs them), or rest/short-week signals too sparse to move log loss at game grain — run the rest-distribution audit (Section 8.5) before concluding.

## 2. Baselines / models

Common rules. Scoring rows: exactly ONE row per GAME (home perspective), `y = 1{home team wins}`; tie games excluded from scoring sets and training rows per the TIE LAW (count disclosed). All arms see identical rows and folds; every paired comparison uses an identical game set; no post hoc row filtering (sensitivity segments are reported alongside, never substituted). Never used as features: any precomputed rating/probability/forecast column, any odds/spread/moneyline/total column (quarantined at load). Score columns are realized outcomes only (targets, rating/form updates) under the as-of law. If the source ships preseason (`PRE`) rows, they are dropped at load with the count disclosed; only regular-season and playoff rows are admissible for rating updates and modeling.

### B0 — Constant home-win probability (floor), 1 arm
- `p̂_fold = mean(y)` over the fold's TRAIN regular-season rows (intercept-only logistic = train home-win rate over decided games). Refit per fold. No inputs, no features.

### B1 — Own-Elo → logistic of rating diff, 4 arms
Exact Elo spec (all constants preregistered; nothing tuned on outcomes):
- Stream: one rating per franchise lineage (Section 8.3 census). Every lineage starts at R=1500 at its first completed game in the audited data; the stream updates on EVERY completed game (regular + playoff) from dataset start forward (or from fallback season X forward if the fallback activates, with pre-X warmup under the degraded date-grain rule).
- Choice — CARRIED-OVER with mean reversion toward 1500 (NOT per-season re-init at 1500). Justification: (i) NFL franchise quality persists across seasons (quarterback continuity, coaching staffs) — this is H1's own mechanism, and re-initializing discards exactly that signal; (ii) re-init forces the model to relearn team strength from a handful of games each season in a 17-game season, visibly degrading early-season calibration; (iii) reversion to the league prior 1500 bounds drift under the salary-cap parity that defines the NFL. Season-boundary rule: before a lineage's first PREDICTION of a new season, `R <- 1500 + (2/3)·(R − 1500)`. γ = 2/3 is FIXED, not gridded (budget): it is the canonical "regress one-third toward the mean" offseason convention and sits below the NBA's 0.75, as parity dictates; γ sensitivity is out of scope for v1.
- Prediction for game G (home H, away A): `p_home = 1 / (1 + 10^{−(R_H + HCA − R_A)/400})`, with R as of the close of all completed games with `kickoff(G')` strictly < `kickoff(G)`.
- Update after completion — binary result only, NO margin-of-victory multiplier in v1: for each team `R <- R + K·(S − E)`, `S ∈ {1, 0.5, 0}` realized (tie → 0.5 for both teams, standard convention per the TIE LAW), `E` = expected score from the prediction formula (HCA included inside E for both sides). All updates with `kickoff(G')` strictly < `kickoff(G)` are applied before predicting G; games with identical kickoff timestamps never inform each other (as-of law).
- Preregistered grid (2×2 = 4 arms): K ∈ {20, 40} Elo points; HCA ∈ {0, 65} Elo points. Justification: K=20 is FiveThirtyEight's published NFL base K (archived methodology; their context multipliers and margin-of-voltage adjustments are explicitly NOT imported); K=40 brackets the upper end of canonical Elo K ranges (FIDE's provisional 40, chess standard 32) and guards against within-season underreaction given only 17 games/team/season (vs the NBA's 82 — fewer observations demand a bracket shifted upward). HCA=65 is FiveThirtyEight's original published NFL home-field magnitude (≈2.5–3 points of spread); HCA=0 is the H2 ablation. Locating an interior optimum K ∈ (20,40) or HCA ∈ (0,65) is explicitly NOT a v1 question — no outcome-driven tuning is permitted.

### B2 — Logistic regression on PIT features, 4 variants
Feature formulas (all strictly as-of at kickoff grain; own-Elo only; completed games only):
- f1 `elo_diff` = R_home − R_away (as-of own ratings; HCA deliberately NOT added — the home effect is carried by the intercept, making it interpretable for H2).
- f2 `rest_diff` = rest_days(home) − rest_days(away), where `rest_days(team, G) = min(20, kickoff(G) − kickoff(team's most recent completed game strictly before kickoff(G)))` measured in days on the continuous kickoff timeline; no prior completed game in the data → 20 (cap). C = 20 days exceeds every in-season inter-game gap except season openers, so byes (~13–14 days) remain uncapped inside the feature and only season openers clamp.
- f3 `short_week_home` = 1{rest_days(home) ≤ 6}; f4 `short_week_away` = 1{rest_days(away) ≤ 6}. (Captures Thursday-after-Sunday ≈ 4 days, Saturday-after-Sunday = 6, and compressed makeups. `rest_days` = 0 rows should not exist under the as-of law; if found: count and investigate, Section 8.5.)
- f5 `form_home` = (wins + 0.5·ties)/games − 0.5 over the home team's last ≤4 completed REGULAR-SEASON games of the current season with kickoff strictly before `kickoff(G)`; zero such games → 0. f6 `form_away` analogous. (Ties count as half a win — update convention consistent with the Elo stream; early-season games with no history get 0, not a season-to-date rate.)
- Estimator: logistic regression, L2 penalty 1.0 on standardized features (z-score mean/std fitted on TRAIN rows of the fold only; intercept unpenalized), deterministic solver to tolerance 1e-8, fixed seed 20261005. Refit per fold. (L2=1.0 is a preregistered stability constant, not a tuned value; changing it = new trial.)
- Frozen variants:
  - B2-a (full): f1–f6. H3 live arm; program candidate.
  - B2-b (no-rest/schedule): f1, f5, f6. H3 KILL TEST.
  - B2-c (no-form): f1, f2, f3, f4. Form ablation.
  - B2-d (elo-only): f1. Bridge diagnostic between B1 and B2 (same input, fitted slope instead of parametric transform).
- Training rows: REGULAR-SEASON games of train seasons only, excluding ties (TIE LAW). Playoff games never enter B2 training, but DO update the rating stream feeding f1 (completed-games law). This choice is justified in Section 8.6.

## 3. Walk-forward design

- Unit = season. Folds = expanding window by season.
- PLACEHOLDER RULE (binding): **test = final 7 complete seasons in the lane-B-audited data, frozen after B.** Expected placeholder list: 2019 … 2025 (the 2025 season ended ~February 2026, before the 2026-10-04 freeze — lane B confirms the last kickoff in the snapshot; if the final season is incomplete in the data, the rule drops it automatically). The controller fixes the exact list after the byte audit; the modeler may never choose test seasons after seeing outcomes.
- Fold k (k = 1..7): train = all complete seasons strictly before test season k; predict every REGULAR-SEASON game of test season k. B1 rating streams are not "refit" (they are fully determined by the as-of law and the arm's constants); B0 and B2 refit per fold.
- PRIMARY evaluation set = regular-season games of the 7 test seasons, excluding ties (disclosed). Playoff games of test seasons are scored with the SAME frozen fold model, reported SEPARATELY per fold; never pooled into primary aggregates; never silently dropped. Super Bowl rows inside the playoff report additionally carry the neutral-site caveat of Section 8.4.
- Anomaly-era folds: 2020 (empty/partial stadiums) stays in primary by default; it is additionally reported WITHOUT as a sensitivity column (Section 8.7). The 2021 seventeen-game era shift stays in primary with NO era covariate (Section 8.11). No silent exclusion in either direction.

## 4. Metrics

Computed on identical game sets per comparison; probabilities clamped to [1e-15, 1−1e-15].
- PRIMARY: mean log loss `LL = −mean[y·ln p + (1−y)·ln(1−p)]`.
- Secondary: Brier score `mean[(p − y)²]`.
- Reliability: 10 equal-width bins on p ([0,0.1),…,[0.9,1.0]); report (n, mean p, observed rate) per bin. Calibration slope = binomial-GLM (logit link) coefficient of `logit(p)` in `outcome ~ 1 + logit(p)`. Slope 1 = calibrated; <1 overconfident; >1 underconfident. Report pooled and per fold.
- Paired comparisons: per-game `ΔLL = LL(arm) − LL(reference)`. 95% CI by block bootstrap resampling kickoff DATES with replacement — clusters = kickoff calendar dates, because same-gameday games share rating state and schedule context (correlated errors). 10,000 resamples, seed 20261005, percentile CI. Report per fold AND pooled (pooled = all 7 test seasons' regular-season games).
- Sign convention: Δ < 0 favors the arm; Δ > 0 favors the reference.

## 5. Trial budget (FROZEN; total ≤ 9 arms)

| # | Arm  | Spec | Role / registered comparison |
|---|------|------|------------------------------|
| 1 | B0   | constant home-win rate, train-only refit | floor; H1/H2 reference |
| 2 | B1-a | K=20, HCA=0,  γ=2/3 | H1 live; H2 ablation |
| 3 | B1-b | K=20, HCA=65, γ=2/3 | H1 live; H2 live |
| 4 | B1-c | K=40, HCA=0,  γ=2/3 | H1 live; H2 ablation |
| 5 | B1-d | K=40, HCA=65, γ=2/3 | H1 live; H2 live |
| 6 | B2-a | f1–f6 (full) | H3 live; program candidate |
| 7 | B2-b | f1,f5,f6 (no rest/schedule) | H3 kill test |
| 8 | B2-c | f1,f2,f3,f4 (no form) | form ablation |
| 9 | B2-d | f1 only (elo-only) | B1↔B2 bridge diagnostic |

- TOTAL = 9 arms (B0 = 1; B1 grid = 4; B2 variants = 4 incl. H3 ablation). Budget is binding.
- FREEZE LAW: grid, features, folds, metrics, and thresholds must be preregistered in the successor scored cycle's plan BEFORE any evaluation on real outcomes. Any arm, feature, fold, metric, or threshold added after seeing any outcome = a NEW registered trial outside this budget, no exceptions. Retuning γ, widening the K/HCA grid, adding margin-of-victory, bye-flag, weather, or injury features, or changing the fold count are all new trials.

## 6. PASS/FAIL thresholds for the scored phase (calibration-only)

Sign convention per Section 4; "CI" = kickoff-date-block bootstrap 95% CI.

Program PASS for B2-a requires ALL of:
- T1 (discriminative gain over best Elo): pooled ΔLL(B2-a, B1*) has CI entirely < 0 AND Δ_f(B2-a, B1*) < 0 on ≥ 4 of 7 folds (≥ half), where B1* = the B1 arm with the lowest pooled primary LL. (Selecting B1* on pooled test LL is itself registered and stays inside the frozen arm set.)
- T2 (calibration): pooled calibration slope of B2-a ∈ [0.85, 1.15].
- T3 (floor safety): no fold where Brier(B2-a) > Brier(B0), AND pooled ΔLL(B2-a, B0) has CI entirely < 0.

REJECT (negative terminal) if ANY of:
- R1: CI of pooled ΔLL(B1*, B0) includes 0 or lies entirely > 0 → own-Elo dynamic strength adds nothing over the constant baseline → program premise fails at this grain.
- R2: pooled ΔLL(B2-a, B0) CI entirely > 0 → candidate is worse than the constant baseline.
- R3: pooled ΔLL(B2-a, B1*) CI entirely > 0 AND T2 violated → both degradation vs Elo and miscalibration.

INCONCLUSIVE: all decision CIs include 0 while T2 holds → no PASS; no re-tuning, no threshold relaxation, no metric substitution; continuation requires a new registered cycle with a NEW mechanism claim.

Hypothesis-level verdicts are exactly the falsification rules in Section 1 (H1: B1 arms vs B0; H2: B1(K,65) vs B1(K,0) paired; H3: B2-a vs B2-b paired).

Language law: PASS/REJECT is calibration language only. No PnL, no betting or market comparison, no "edge" vocabulary anywhere in outputs.

## 7. NOT_RUN register

| Item | Status | Reason | v1 handling |
|---|---|---|---|
| Injury reports | NOT_RUN_PIT | no $0 source with historical publish timestamps | excluded; successor needs PIT provenance |
| Betting / odds columns (spread, moneyline, total, closing line) | NOT_RUN_PIT + quarantine | closing-line contamination; v1 has no betting | dropped at load; never features, never targets, never cross-calibration targets |
| Play-by-play-derived features v1 (EPA, success rate, WP curves) | NOT_RUN_PIT | pbp tables are compiled post-game and retro-corrected by maintainers | games-table results only |
| nfldata/nflverse repo beyond the audited games/schedule file (pbp, retro-corrected tables) | NOT_RUN_PIT | retro corrections rewrite history post hoc | provenance of the audited file itself is a lane-B audit fact (Assumption 1) |
| Keyed / paid data sources | NOT_RUN_SCOPE | $0 law | excluded |
| ESPN endpoints | NOT_RUN_PIT | no historical snapshot provenance; pit unproven | excluded |
| Schedule-snapshot features (pre-announced kickoff changes, published schedules beyond the audited games table) | NOT_RUN_PIT | requires historical snapshot sources | features from completed games only, per as-of discipline |
| Week-grain features | NOT_RUN_PIT | permitted only if kickoff AND day grain both fail | protocol itself declares NOT_RUN_PIT rather than weaken (Section 0) |
| Tie model (3-outcome probabilities) | NOT_RUN_SCOPE | no invented tie model; tie count is small | binary label; ties excluded from scoring/training, disclosed; S=0.5 update convention only |
| Margin-of-victory Elo multiplier | NOT_RUN_SCOPE | excluded from frozen grid | binary update only |
| γ (season-reversion) grid | NOT_RUN_SCOPE | ≤4-arm B1 budget | fixed at 2/3 |
| Weather / stadium-roof features | NOT_RUN_PIT | no PIT-proven historical weather archive in scope | excluded |
| Neutral-site flagging (if unflaggable in the data) | NOT_RUN_PIT | not derivable without a validated venue column | declared limitation + sensitivity (Section 8.4) |
| Playoff-specific model | NOT_RUN_SCOPE | budget + distribution shift | frozen-model playoff report only (Section 8.6) |
| Seasons after 2025 | NOT_RUN_SCOPE | data freeze 2026-10-04 | out of scope |

## 8. Pitfalls checklist (exact test per pitfall)

1. **Precomputed-rating / odds leakage** (shipped probability, rating, spread, moneyline, or total columns as hidden inputs). Static test: feature-construction code must not reference any such column by name (grep-level check in the scored cycle); quarantined columns are dropped at load and their names recorded. Behavioral test: per fold, report mean |own-Elo implied p̂ − any shipped probability column| and rank correlation on test games. Near-exact agreement (mean |Δ| < 5 Elo-equivalent points, or ρ > 0.999 with mean |Δ| < 1 point) → INVESTIGATE implementation for accidental copying. Large divergence (ρ < 0.9) → also investigate (likely bug in K/HCA/γ or lineage map). Investigate, never copy: shipped values must never be patched in to close a gap.
2. **Same-kickoff ordering** (violation of the strict-inequality law; simultaneous slates). Unit test: synthetic same-kickoff pair — a team's second game at timestamp t must be predicted from ratings/features that exclude the first game's result. Property test over all rows: every feature-source game has `kickoff` strictly < target `kickoff`; any equal-timestamp source fails the audit.
3. **Team rename / relocation / franchise continuity** (Washington Redskins→Football Team→Commanders; Raiders OAK→LV; Chargers SD→LAC; Rams STL→LA). Census test: enumerate all distinct (team_id, season) triples; assert the lineage map assigns every team_id to exactly one franchise lineage; assert a lineage's rating stream resets to 1500 ONLY at dataset start and is otherwise continuous except the season-boundary reversion rule. Any team_id under two lineages, or any lineage gap, fails the audit (one lineage = one rating stream).
4. **Neutral-site / international games** (London Wembley/Tottenham, Mexico City, Munich/Frankfurt; Super Bowl in the playoff report). Conditional on the lane-B fact (Section 1 H2): IF a validated flag exists (venue/city column crossed with a static home-venue map), test = census of flagged games, count disclosed, flagged games scored with HCA=0 and excluded from H2's primary paired estimation, reported as a separate segment. IF unflaggable: declared limitation; HCA applied everywhere; H2's interpretation carries the caveat that ≤ ~1% of test rows are plausibly neutral-site and the contamination inflates measured HCA. Never silently pooled, never silently dropped.
5. **Postponed / rescheduled / cancelled games** (2020–21 COVID reschedules, 2022 BUF–CIN cancellation). Rating updates, rest, and form derive ONLY from games actually played, at their actual kickoffs; a cancelled game (no result) never enters anything. Tests: (a) rest_days ≥ 0 everywhere, no negative gaps; (b) `rest_days` = 0 rows are investigated anomalies, not silently kept; (c) known postponement clusters produce rest spikes, not negative gaps; (d) the cancelled game appears in no scoring set, no update, no form window.
6. **Playoff leakage / preseason rows.** Fit and test on the REGULAR SEASON; playoffs ONLY update the rating stream and appear in a separately reported scored segment using the same frozen fold model. Justification: playoff games differ structurally (rest patterns, selection, intensity; neutral-site Super Bowl), so pooling distorts calibration claims, while excluding completed playoff games from the stream would violate the completed-games law. Tests: assert zero playoff rows in any B2 training set and zero in any primary aggregate; playoff rows appear only in the separately labeled report; assert any `PRE` rows are dropped at load with count disclosed.
7. **COVID-era 2020 anomalies** (empty/partial stadiums): 2020 stays in primary by default (it sits inside the test window; default exclusion is forbidden and would itself need a new registered trial). Sensitivity column: test-season 2020 re-scored with HCA = 0 for all B1 arms; per-fold tables always flag 2020 so the anomaly cannot hide inside a pooled mean.
8. **Row double-counting** (two rows per game if the source is team-perspective). Test: exactly one prediction row per game_id; y consistent with `home_score` vs `away_score` on every row.
9. **Outcome-column contamination**: score columns used solely as realized outcomes for y, rating updates, and form; no post-game compiled statistic of any kind is a predictor; `PRE` rows and quarantined odds columns never reach feature code (grep).
10. **Ties**: assert zero tie rows in any primary scoring set and any B0/B2 training row set; tie count disclosed per fold and pooled (expected: a handful across 7 seasons); synthetic tie test on the stream — a tie moves both teams' ratings toward each other by exactly K·0.5·(deviation), never a full win/loss step; ties never silently dropped.
11. **2021 seventeen-game era shift**: NO era covariate (adding one would be a new arm; the shift is a within-train-era shift and the expanding folds span it — fold 1's train is entirely pre-2021, later folds' trains mix eras). B0 refits the intercept (home rate) per fold and thus absorbs era drift in the base rate; B2 features are per-game quantities, not season aggregates. Per-fold reporting prevents the shift from hiding inside a pooled mean. Test: report per-fold home-win base rate and per-fold feature means so era drift is visible.
12. **Kickoff-grain fallback activation** (season X): if lane B activates the fallback, test — assert zero B0/B2 features and zero primary scoring rows before X; pre-X seasons appear only as warmup rating updates under the documented degraded date-grain ordering; the value of X (or "not activated") is frozen in the controller's freeze packet BEFORE scoring. If BOTH kickoff and day grain fail in the audited data: declare the protocol NOT_RUN_PIT; do not weaken to week grain.

## 9. GO gate for the successor scored cycle

GO phrase (exact): **`GO NFL WINPROB SCORED V1 EVALUATION`**

The controller may issue it only after: (a) the lane-B byte/schema audit lands clean; (b) the final 7 test-season list is frozen; (c) the fallback status (season X, or "not activated") is frozen; (d) the neutral-site flag status is frozen; (e) Sections 2–6 and this section are inherited verbatim into the scored cycle's plan.

Preregistered negative terminal outcomes (must appear verbatim in the successor plan):
- NEGATIVE-TERMINAL (calibration): If any REJECT condition R1–R3 (Section 6) obtains on the frozen protocol, NFL-WINPROB v1 terminates as a negative calibration result. Prohibited responses: re-gridding K/HCA/γ, adding or mutating features (including injuries, weather, odds, pbp-derived, or bye flags), changing folds, metrics, or thresholds, relaxing CI or slope gates, substituting baselines, or reframing via accuracy/PnL. Continuation requires a new registered cycle with a NEW mechanism claim.
- NEGATIVE-TERMINAL (audit): If the lane-B audit fails, the scored phase is NOT_RUN. Missing evidence is NOT_RUN, never inferred PASS.
- TRIAL LAW: Any arm, feature, fold, metric, or threshold introduced after any real outcome is observed is a NEW registered trial outside this budget, no exceptions.

## 10. Assumptions & limitations (lane B / controller must confirm)

1. Column semantics: the audited games table carries a unique `game_id` per game; a season field; a kickoff timestamp parseable to UTC (fallback law applies if lane B finds it unreliable before some season X); home/away team identifiers; final scores; a game-type/week field separating REG from POST (and dropping PRE). Lane B confirms byte-level; names here are roles, not literal column promises.
2. Dataset provenance: whatever the audited file is (including a games/schedule CSV of nfldata/nflverse lineage), final scores of completed PAST seasons are stable, so retrieval-time snapshot bias is acceptable for v1; the RESIDUAL RISK is the most recent season (2025): late retro-corrections to the freshest rows would not be reflected in this snapshot. Lane B records the download date; the residual risk is documented, not engineered around.
3. The 2025 season is COMPLETE in the snapshot (Super Bowl LX ~February 2026 < freeze 2026-10-04). Confirm the last kickoff in the data; if the final season is incomplete, the "final 7 complete seasons" rule drops it automatically and the placeholder list shrinks to 2018…2024.
4. Ties: expected count over 7 test seasons is small (NFL history shows roughly a handful per decade since 1974 overtime); the exact count is an empirical disclosure at scoring time, never an assumed rate, and never silently dropped. No tie model is invented anywhere in v1.
5. No NFL team plays two games with kickoffs on the same calendar day in the audited era (assumed); simultaneous-kickoff games never inform each other by the strict-inequality law; same-day later kickoffs DO inform earlier kickoffs (kickoff grain's upgrade over the NBA date law).
6. Franchise continuity is assumed derivable from a static lineage map over the data's team identifiers; if renames/moves break lineage, the controller supplies the static identity mapping (permitted by the as-of law as a static mapping).
7. Neutral-site flaggability is unknown until lane B: the conditional law of Sections 1-H2/8.4 applies; either branch must be frozen before scoring.
8. Convention citations for the preregistered constants (brackets, not verified optima): K=20 / HCA=65 / ~one-third offseason regression from FiveThirtyEight's archived NFL Elo methodology (published 2014-2023, now offline; values retrieved via archived-source summary on 2026-10-04); 400-point logistic scale and canonical K ranges (16/32/40) cross-checked live against the Wikipedia Elo rating system page on 2026-10-04. Locating interior optima is explicitly out of scope (no outcome-driven tuning in v1).
9. No evaluation was executed in this prep cycle: every number here is a design constant, not a result. H2/H1 grid endpoints bracket rather than fine-tune.
10. B2 uses L2 = 1.0 on standardized features — a preregistered stability choice, not a tuned value; changing it is a new trial. Solver and bootstrap seed: 20261005.
11. Elo burn-in: warmup from dataset start; if the audited history begins ~1999 (nfldata-era schedules), the first test fold (2019) sits ~20 seasons later and burn-in is immaterial in practice. If the controller trims history, burn-in adequacy must be re-argued before freezing; if the fallback activates, pre-X warmup adequacy must be re-argued with the same discipline.
12. Data freeze 2026-10-04; seasons after 2025 are out of scope (NOT_RUN_SCOPE).
