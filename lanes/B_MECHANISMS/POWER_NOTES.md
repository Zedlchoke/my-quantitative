# POWER_NOTES — Lane B, NFL-WINPROB-NG-PREP-V1 (analytic power/capacity arithmetic only)

- lane: B_MECHANISMS · task: nflng-b-mech · date: 2026-10-05
- ANALYTIC ARITHMETIC ONLY. No data downloaded, no outcome computed, no metric evaluated.
  All calibration constants are re-measured from the terminal cycle's bytes
  (`NFL-WINPROB-SCORED-V1/results/scored_summary.json`, `comparisons` and per-fold blocks).
- Sign convention: ΔLL < 0 favors the arm. "Detected" = paired 95% CI excludes 0.

## 1. Calibration constants measured from the terminal cycle (n = 1865 pooled RS)

| paired comparison | ΔLL | 95% CI | half-width h |
|---|---|---|---|
| B1\* vs B0 (the full dynamic-strength gain) | −0.0528 | [−0.0676, −0.0380] | 0.0148 |
| B1-d vs B1-c (league-constant HCA) | +0.0046 | [−0.0035, +0.0125] | 0.0080 |
| B2-a vs B1\* (rest/form layer) | +0.0017 | [−0.0053, +0.0088] | 0.0070 |
| B2-a vs B2-b (rest mains) | +0.0001 | [−0.0011, +0.0012] | 0.0012 |

Per-game paired-difference SD implied by each (s = h·√n / 1.96, √1865 = 43.19):

- **s_small ≈ 0.154** (from B2-a vs B1\*: the honest reference class for a NEW candidate
  vs B1\* — small per-game prediction differences).
- **s_large ≈ 0.326** (from B1\* vs B0 — a large-effect comparison; conservative upper
  reference for arms whose predictions diverge more from the reference).

Scaling law: h(n) = 1.96 · s / √n.

**Empirical validation of the scaling law.** The terminal cycle's measured PER-FOLD
half-widths for B2-a vs B1\* (n ≈ 255–272) are 0.0162–0.0228 (mean 0.0188); the law
predicts h(270, s=0.154) = 0.0184. Agreement within ~2% on the mean; per-fold spread
(±20%) reflects year-to-year variance variation. The sqrt(n) scaling is confirmed
against measured bytes, not assumed.

## 2. CI half-width and minimum detectable ΔLL by window size

MDD = smallest true |ΔLL| detected with ≈80% power by a two-sided 95% paired CI:
MDD ≈ 2.80 · s / √n. Two reference classes bracket the honest range.

| window | n | h (s=0.154) | MDD (s=0.154) | h (s=0.326) | MDD (s=0.326) |
|---|---|---|---|---|---|
| 1 NFL regular season (~270 games; measured folds 255–272) | 270 | 0.018 | **0.026** | 0.039 | **0.056** |
| 2 seasons | 540 | 0.013 | **0.019** | 0.028 | **0.039** |
| 7 seasons (= terminal TEST window) | 1865 | 0.007 | **0.010** | 0.015 | **0.021** |
| Train-internal pool (2000–2018, ~19 seasons) | ~4839 (measured fold-2019 n_train) | 0.004 | **0.006** | 0.009 | **0.013** |

Games needed at s = 0.154 (80% power): n = (2.80 · 0.154 / Δ)² —

| true ΔLL vs B1\* | games needed | NFL seasons @ ~270 |
|---|---|---|
| 0.005 | ≈ 7,400 | ≈ 27 |
| 0.010 | ≈ 1,860 | ≈ 7 |
| 0.015 | ≈ 830 | ≈ 3 |
| 0.020 | ≈ 470 | ≈ 2 |
| 0.026 | ≈ 275 | ≈ 1 (the 1-season MDD by construction) |

## 3. Plausible effect sizes vs B1\* (measured anchors)

- The ENTIRE dynamic-strength mechanism (Elo vs constant) is worth 0.053 pooled.
- The largest measured arm-vs-parent refinements in the terminal cycles are 0.002–0.007
  (K=20→40 worth 0.0074; every B2 layer ≤ 0.002; NBA T1 blocks ~0.001–0.003).
- A single NEW mechanism layered on an already-strong B1\* is plausibly worth
  **0.002–0.010 pooled, central estimate ~0.005.** Anything claimed much larger should
  be suspected (mis-specification or leakage) before celebrated.

## 4. Verdicts per candidate arm (single-mechanism arms)

| arm | plausible ΔLL vs B1\* | 1-season MDD | 2-season MDD | train-internal MDD (~4839) | verdict |
|---|---|---|---|---|---|
| C1 SOS-adjusted Elo | 0.002–0.010 | 0.026–0.056 | 0.019–0.039 | 0.006–0.013 | train-internal evaluable; prospective starved at 1 season; 2 seasons adjudicates only top-of-range (≥~0.02) effects |
| C2 split rating | 0.001–0.005 (low end) | 0.026–0.056 | 0.019–0.039 | 0.006–0.013 | same; prospective default INCONCLUSIVE even at 2 seasons |
| C3 offseason EPA prior | 0.002–0.008 | 0.026–0.056 | 0.019–0.039 | 0.006–0.013 (shortens if Lane A pbp coverage starts mid-train) | same; Lane A coverage gates the train-internal MDD |
| C4 short-week×away (conditional) | 0.01–0.03 on the SLICE | slice n≈18 ⇒ hopeless | slice n≈90 (5 seasons) ⇒ MDD ≈ 0.15 | slice n≈340 ⇒ MDD ≈ 0.08 (slice-paired SD ≈ 0.5) | starved BY DESIGN; the train-internal gate is expected to release the slot |

**Single-mechanism viability:**
- **A 1-season NFL arm is starved for every candidate** (MDD ≥ 0.026 is 2.6×–28× every
  plausible effect). A 1-season OOS report can never PASS or REJECT a single mechanism
  vs B1\* except under a freak effect ≥ ~0.026 — treat any such 1-season "result" as
  noise until replicated.
- **2 seasons (n≈540) is a necessary floor, not a sufficiency guarantee**: MDD 0.019–0.039
  still exceeds the central plausible range (0.002–0.010) by ~2–4×. At 2 seasons only
  top-of-range effects (≥ ~0.02) are adjudicable; the honest default outcome for a
  central-range mechanism at 2 seasons is INCONCLUSIVE.
- **Prospective-only detection of a central ~0.005 effect needs ≈ 7,400 games ≈ 27
  seasons — impractical.** Therefore the power-bearing stage for new mechanisms is the
  TRAIN-INTERNAL evaluation (n≈4839 ⇒ MDD 0.006–0.013, overlapping the central plausible
  range). Every proposed candidate (MECHANISMS_NFL_NG.md §2) is train-internally
  evaluable on 2000–2018+ BEFORE any prospective window is spent; C3's MDD shortens only
  if Lane A's pbp snapshot covers less than the full train window (recomputed at
  registration).

## 5. Quantitative basis for the ≥2-season rule (restated, binding on the successor protocol)

1. One season is never sufficient: MDD(270) = 0.026–0.056 > all plausible single-
   mechanism effects. (Hard floor, proven.)
2. Two seasons is the MINIMUM for any strong conclusion and still only detects
   effects ≥ ~0.019–0.039 — i.e., 2 seasons suffices only for large effects; for
   central-range effects the 2-season default is INCONCLUSIVE, and adjudication must
   lean on the train-internal stage.
3. Any multi-season accrual must be pre-registered with direction and controls before
   the first prospective look (append-only prediction ledger, timestamps strictly before
   kickoff UTC; already-played 2026 games are NOT_RUN for prospective scoring).
4. Design consequence: a mechanism that cannot show a train-internal gain at MDD ≈ 0.006
   should not consume a prospective arm slot at all — its prospective detection horizon
   (≥27 seasons at central effects) makes it un-decidable this decade.

## 6. Trial-budget and attribution note (capacity)

- The successor protocol's ≤9-arm budget (inherited shape): B0 + B1\* mandatory; the
  surviving candidates enter as SEPARATE arms (one mechanism per arm — pooling several
  mechanisms into one block arm destroys attribution and is not permitted); shuffled
  negative controls are diagnostic arms, reported but never counted as candidate wins;
  C4 enters only if its train-internal gate passes; one reserve slot, specified in the
  freeze document before any test look, unused = released.
- Designed-null equivalence (β = λ = θ = δ = 0 reproduces B1\* bit-for-bit) is a
  capacity precondition to verify in any scored successor before any other number is
  believed.
- Slice-level heterogeneity reports (early-season vs late-season for C1; first-6-weeks
  for C3) are DIAGNOSTICS, never gates — gates live at the pooled level with the fold
  rule, per the frozen falsifier language.
