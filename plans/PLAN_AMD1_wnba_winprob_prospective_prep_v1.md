# PLAN AMENDMENT 1 (AMD1) — WNBA-WINPROB-PROSPECTIVE-PREP-V1 · Diagnostic Annex R

**RETROSPECTIVE DIAGNOSTIC — NOT OOS EVIDENCE** (labeling law: every artifact, file,
figure and headline produced under this annex carries this label or an explicit
reference to it).

- Amendment id: PLAN_AMD1_wnba_winprob_prospective_prep_v1
- Cycle: WNBA-WINPROB-PROSPECTIVE-PREP-V1 · branch
  `orca/wnba-winprob-prospective-prep-v1-integration` · worktree
  `.worktrees/wnba-winprob-prospective-prep-v1/integration`
- Authority chain: owner instruction **2026-10-06 (this chat)** — authority #1,
  supersedes plan text where they conflict — authorizes amending THIS PREP cycle's
  authority to add a retrospective-diagnostic annex under owner goal (A): research how
  to reduce WNBA log loss below the immutable baseline
  **B1-WNBA pooled LL 0.611603 (OOS 2020–2026, n=1,773)**. Base plan:
  `plans/PLAN_wnba_winprob_prospective_prep_v1.md` at root HEAD
  `95ba89ab61c88ad8c935e2566ce20551b1a5cb71` (measured 2026-10-06). This amendment is
  written and committed BEFORE any diagnostic run (pre-registration law).
- Budget law: this annex computes **ZERO scored cells**; the PREP registry row's
  budget stays 0/0. Diagnostic trial counts live in the annex's own
  `DIAGNOSTIC_TRIAL_LEDGER.jsonl` (append-only), never in the scored counter.

## R.1 Purpose and scope

Compute **RETROSPECTIVE DIAGNOSTICS ONLY** on the wnba-v1 corpus + the closed cycle's
frozen feature table, to characterize where B1-WNBA (own-Elo K=32/HCA=50/γ=0.65) loses
log loss and whether pre-registered candidate mechanisms look promising under honest
per-origin selection. The annex NEVER produces: scored cells, OOS-claim evidence,
candidate wins, slot reallocations, a re-run/challenge of the closed cycle
WNBA-PLAYERFEAT-SCORED-V1's OOS 2020–2026 verdict, or any change to its frozen budget
(2/9 FINAL — cited as frozen inheritance, never recomputed as a verdict). No real-game
probability is computed for any 2027+ game anywhere under this annex.

## R.2 Frozen comparators (byte-carried, never re-tuned)

- **B1-WNBA verbatim**: own-Elo K=32, HCA=50, γ=0.65, binary updates, frozen engine
  `arms.py` sha256 `82263eab713258b09ef920500a56d1fbf36ef9b9b8ea20965c6b4fd99b04cdd3`,
  `harness.py` sha256 `b9446f7699ce2e29c8ce66490fc0f9941cc38dda0ed02e8e7fc108e65373485e`
  (ERRATUM_R1 pins; re-hashed against live bytes at every diagnostic run start).
- **B0 constant** p = 0.603755 (closed cycle's train-internal floor), carried verbatim.
- **Identity law before any use**: the feature table
  `~/.my-quantitative-data/playerfeat-prep-v1/wnba/features/wnba_player_features_2002_2026.parquet`
  must hash to `ceaf10ba33e705b9569a11cec2aa33e1875e372c35d643ed5d80d5e757ffc7bf`
  (826,415 B) and the crosswalk
  `~/.my-quantitative-data/wnba-prep-v1/extensions/wnba_schedule_crosswalk_2026.csv` to
  `e4115f04d45d3bc7fb9b43eca9c5babd26185e2ecf51e65bc3b66bf02aa6eea6`. Any mismatch ⇒
  **BLOCKED_TOOLING**, nothing runs. Additionally: the diagnostic stream's B1-verbatim
  predictions for 2020–2026 must match the closed run's frozen
  `predictions_b1_wnba.csv` **p_home_hex bit-for-bit** (same for B0 vs
  `predictions_b0.csv`); mismatch ⇒ BLOCKED_TOOLING.

## R.3 Design: rolling-origin nested walk-forward

Corpus: warm-up 1997–2001 (1,022 rows, stats-side) + universe 2002–2026 (5,988 rows)
under the frozen filter law (status post; no Forfeit/Postponed; no All-Star aliases;
census law `FROZEN_CENSUS` per `run_oos.py`). Rating stream order: (tip, game_id)
ascending; tip-batched snapshot law (same-tip games all predicted from one state).

**Origins (pinned)**: s ∈ {2006, 2007, …, 2026} — 21 origins. Earliest feasible origin
is 2006: it leaves ≥4 prior universe seasons (2002–2005) for the honest selection
window after the 2002+ stream start (the 1997–2001 side is warm-up only and never a
selection or evaluation window).

At each origin s:
1. **Fit/select using seasons < s ONLY.** Each pre-registered family selects among its
   own specs + the null parent B1-verbatim, by mean LL over the **selection window =
   the 4 immediately-prior universe seasons [max(2002, s−4), s−1]** (train-internal;
   fewer seasons near 2006 — window is what exists). Ties break to B1-verbatim
   (simplest). No wall-clock; deterministic.
2. **Predict season s** from the rating state replayed through s−1 (stream continues
   from 1997 warm-up; no reset between origins — the state at origin s is exactly the
   chronological stream state).
3. **Record per-origin** n, B1-verbatim LL, selected-arm LL, paired ΔLL, CI, Brier,
   calibration slope, coverage counts.

## R.4 Hypotheses (owner-ordered; HARD CAP 24 diagnostic trials total)

**H1 — error decomposition (ANALYSIS, 0 trials)**: decompose B1-verbatim per-game LL
(descriptive only, full stream 2002–2026 and the 2020–2026 subset reported separately):
(a) season-start/early-season: either side's season game-index ≤ 3 vs > 3;
(b) expansion/new teams: game involves a franchise whose corpus-first season == the
game's season;
(c) close-strength pairs: |R_h − R_a| pre-game (HCA excluded) ≤ 25 (primary bin),
25 < |·| ≤ 50 (secondary);
(d) home won vs home lost (home_win=1 vs 0); neutral-site rows disclosed separately.
No claim, no selection, no candidate status.

**H2 — ≤12 trials, null parent = B1-WNBA verbatim** (mechanism families):
- H2-MOV (6): margin-of-victory update weighting — absorb game g with step
  K·m(margin)·(outcome − p), m(margin) = 1 + w·min(|margin|, cap)/cap (binary
  prediction/update law otherwise unchanged);
  (w, cap) ∈ {(0.5,8),(0.5,16),(0.5,32),(1.0,8),(1.0,16),(1.0,32)}.
- H2-REC (6): strength carry-over using only the previous game — effective pre-game
  rating R_eff = R + m·δ_last(fk), δ_last(fk) = that franchise's most recent in-season
  update step (0 at season start), m ∈ {0.25, 0.5, 1.0, 2.0, 4.0}; plus one sign-dummy
  variant: arg += 25·s_last, s_last ∈ {+1 won previous, −1 lost previous, 0 none}
  (within-season only).
Honest per-origin selection per §R.3 step 1.

**CAL — ≤4 variants (calibration check, separate)**: applied as post-hoc monotone
transforms of B1-verbatim p_home, parameters fit per-origin on the §R.3 selection
window only. The closed cycle's slope 1.0467 is near 1 — recalibration is NOT presumed
to help; this is a diagnostic:
- CAL-1: slope-only, p' = sigmoid(a·logit p), a ∈ [0.50, 2.00] grid step 0.01 by LL;
- CAL-2: Platt (slope+intercept), a × b, a ∈ [0.50, 2.00] step 0.05, b ∈ [−0.50, 0.50]
  step 0.05 by LL;
- CAL-3: shrink to 0.5, λ = 0.10 fixed;
- CAL-4: shrink to B0, p' = (1−0.10)·p + 0.10·0.603755 fixed.

**H3 — ≤8 trials, GATED**: roster/player prior **strictly pre-tip**. BEFORE any H3
trial runs: (i) data rights proven from LOCAL stores only, $0 — ATTRIBUTION.md
sha256 == `1068e5c7aae614347550266da94d067f38c7c2cc9b569e685cfed3aced301f5a`;
(ii) point-in-time availability proven per column class. If either fails ⇒
**H3 = NOT_RUN_RIGHTS_PIT**, skipped, disclosed. Pre-registered H3 specs (all use the
closed cycle's frozen feature-table columns, 0 outcome columns):
- H3-C1 (1): continuity-modulated season-start carryover, v2 law: R_start = 1500 +
  γ·c_i·(R_end−1500) applied from each team's season game 2 onward; c from
  `continuity_c`; game-1/expansion/missing/neutral-reason rows use c=1 (parent).
- H3-C2 (2): additive continuity argument arg += φ·(c_H − c_A), φ ∈ {+25, −25}
  (selectable per-origin among {+25, −25, 0=parent}).
- H3-C3 (2): rotation-concentration argument φ·(x_H − x_A), x = standardized
  `b5_minutes_hhi` (era floor: season ≥ 2013 and empty reason, else x=0), φ ∈ {+25, −25}.
- H3-C4 (2): top-5 absence argument φ·(x_H − x_A), x = standardized `c_absence_share`
  (same era floor), φ ∈ {+25, −25}.
Total pre-registered: 12 (H2) + 4 (CAL) + 7 (H3) = **23 ≤ 24 cap**.

**Trial accounting**: each trial = one pre-registered spec id (above), logged once in
`DIAGNOSTIC_TRIAL_LEDGER.jsonl` (append-only, in this lane) at first execution with
family, spec, params, selection outcome per origin, verdict vs parent. No silent
retries; any deviation = a NEW logged trial (24-cap enforced: the cap counts logged
trials; with 23 pre-registered, at most 1 deviation trial is possible).

## R.5 Metrics + uncertainty law

- Paired per-game ΔLL = LL(arm) − LL(B1-verbatim); **negative favors the arm**; report
  with the closed cycle's **date-cluster block bootstrap law**: 10,000 resamples,
  clusters = canonical tip UTC date, **seed 20261006 pinned ONCE for the whole annex**,
  95% percentile CI, per-origin AND pooled (pooled over all 21 origin-seasons; the
  2006–2019 honest subset and the 2020–2026 exposed subset also reported separately).
- Brier score, 10-bin reliability, calibration slope (frozen `arms.calibration_slope`),
  coverage counts per origin.
- Effects smaller than ~0.01 pooled ΔLL at this origin coverage are INCONCLUSIVE —
  stated, not stretched (capacity note; closed-cycle pooled CI half-width was ±0.0179
  on n=1,773).

## R.6 Labeling + disclosure law

1. Every artifact/file/figure headline carries "RETROSPECTIVE DIAGNOSTIC — NOT OOS
   EVIDENCE".
2. **Exposure disclosure**: 2020–2026 outcomes are already exposed via the closed
   cycle; any figure touching them can never be called independent OOS.
3. **Selection-asymmetry disclosure**: B1-WNBA's constants (K=32/HCA=50/γ=0.65) were
   selected in the closed cycle with knowledge of seasons up to 2018+ — i.e., with
   lookahead relative to origins ≤ 2018 — while annex variants select per-origin on
   prior seasons only. Early-origin comparisons are therefore biased AGAINST the
   honest variants; the pooled numbers inherit that asymmetry and are stated as
   diagnostic, not fair tests.
4. **Hypothesis-vs-confirmation law**: nothing in this annex can confirm improvement
   below 0.611603. Any positive signal is reported as "HYPOTHESIS — supported/not
   supported by retrospective diagnostics; NOT confirmed (no fresh unselected data)".
   Confirmation exists ONLY through a registered gate on data truly unused for
   selection — in practice prospective 2027+ under the successor cycle's own typed GO.

## R.7 Boundary compliance (restated)

No typed/paraphrased GO; no scored cells; no prospective forecast rows; no real ledger
file; no registry writes (needed mutations recorded in the handoff); root checkout
read-only; other cycles' trees read-only; $0; no credentials; calibration/forecasting
vocabulary only; heavy runs take the machine-wide lock (NOT_RUN_RESOURCE_CONFLICT if
never acquired, per retry discipline); missing evidence = NOT_RUN, never inferred PASS.
