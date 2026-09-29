# PASS_BARS_V2 — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (pre-GO, Lane P)

The owner's exact requirement (directive 2026-09-29), restated as law:

> **PRIMARY success criterion: net PnL after ALL costs STRICTLY HIGHER **AND**
> max drawdown STRICTLY LOWER than the designated baseline.**

This is AND-semantics on BOTH quantities, simultaneously, evaluated net of the
full cost kernel (measured spread cells C1–C3 + declared components U2/U3/U4 at
the governing tier). **OR-semantics are repealed.** V1 of the bars
(`PORTFOLIO_POLICY_ARCHITECTURE.md` §10) is superseded by this document
wherever they conflict; that file is not modified by this lane (write-ban) —
this document is the V2 authority for every PASS bar a survivor claim is
evaluated against. V1 defects being fixed here: (i) P1 allowed an OR-path
("net PnL ≥ baseline AND maxDD strictly lower") — repealed, both legs are now
strict AND; (ii) P6 was referenced by P2 ("survives ×1.5 (P6)") but never
defined — P6 is now fully defined in §6; (iii) P1–P8 now each carry
formula-level precision, their baseline, pass condition, fail close-code and
edge cases.

**Revision 2026-09-29 (remediation of the independent skeptic's
REVISE_BEFORE_OWNER verdict, applied by Lane P under A1 dispatch; provenance
noted per finding):** **F-1 (CRITICAL)** P5a's "DSR > 0" was vacuous — Φ(·)
is strictly positive for any finite argument, so the condition could never
fail on the DSR side — the pass condition is now **DSR > 0.95** with the
equivalence stated in §5. **F-2 (HIGH)** B2 EQUAL_WEIGHT's "0.5/N of the
per-leg cap" allocation was degenerate (total book 0.1875% regardless of N;
contradicted P2's N=1 edge case) — B2 now deploys the policy's realized total
heat target split equally across active legs (§1, §3). **F-3 (HIGH)** the
≥100-seed B4 battery (~140 arm-executions) would have self-triggered STOP-2
against the plan's ≤48 cap — the budget counting unit is now defined:
IDENTITIES vs seeded sub-runs (E-Law 8, §4; A1 is amending the plan's budget
table to 48 identities + B4 battery ≤128 seed sub-runs as a separate line).
**F-6/F-7/F-11/F-17 (MEDIUM/LOW):** IS/OOS double-correction disclosure with
the PSR value reported alongside DSR (§5); fold-edge force-flat
differential-charging disclosure and per-arm companion report (E-Law 2);
cluster-adjusted N_eff and byte-identical-arm dedup for P5 (§5); B3 selection
statistic formula and tie-break record frozen (§1).

Status: pre-GO design artifact. No scored cell exists (T0); nothing here is a
PnL claim. Every number a bar consumes must come from a Stage-C scored run
under a frozen freeze-SHA, fold calendar (campaign §3) and cost-kernel digest
— else the bar is `NOT_RUN_*`, never inferred PASS.

---

## 0. Common evaluation laws (apply to every bar)

**E-Law 1 — Quantities.** For any arm X (policy or baseline) run over the test
folds:

- `netPnL(X) = Σ_{f ∈ TEST} netPnL_f(X)` — pooled over ALL test folds, where
  `netPnL_f` is the fold's realized net PnL from the FILL_ACCOUNTING_SPEC book
  identity (all costs at the governing tier: spread-once, slippage,
  commission, swap; nothing amortized, nothing waived).
- `maxDD(X) = max_{t ∈ TEST-window} ( peak_t(X) − equity_t(X) )` in **USD**,
  where `peak_t` is the running max of the equity path from the start of the
  pooled test window and `equity_t` is marked per the book identity
  (mid_close marks; UNAVAILABLE never read as 0). The percentage form
  `maxDD%(X) = max_t (peak_t − equity_t)/peak_t` is REPORTED alongside but is
  NON-governing. One frozen definition (USD) governs so there is no
  division-by-zero or peak-denomination ambiguity between arms.

**E-Law 2 — Pooled vs per-fold.** Unless a bar says otherwise, both quantities
are POOLED (one concatenated equity path across all test folds). P7 is the
only per-fold bar. Fold boundaries: each test fold ends at its last decision;
all positions are force-flatted at that decision (exit fills at next-bar-open,
full kernel charged, booked inside the closing fold) — BTC-COMBO6 fold-edge
force-flat precedent. Equity carries across folds (one $100k book for the
whole campaign; no re-capitalization between folds).

**Fold-edge force-flat asymmetry disclosure (skeptic F-7).** Force-flat
charges arms DIFFERENTIALLY by their fold-edge holdings — an arm holding
more or larger positions at a fold edge pays more exit cost
(turnover-dependent). This is a SYSTEMATIC asymmetry between the policy and
the always-on baselines (B1/B2 hold at every fold edge by construction; the
policy may already be flat there and pays nothing). The asymmetry is
ACCEPTED (force-flat is the frozen fold-isolation law and applies
identically to every arm's own holdings) but it must be VISIBLE: every
Stage-C report carries a companion table of **per-arm fold-edge force-flat
cost totals** (exit crossing + commission, per arm, per fold), so P1's PnL
leg can be read net of the asymmetry.

**E-Law 3 — Comparability.** A bar is evaluable only if policy arm and
baseline arm share: same freeze SHA, same fold calendar, same cost-kernel
`defaults_digest`, same stress tier, same fill model (FILL_ACCOUNTING_SPEC),
same initial cash ($100,000.00) and same vehicle set. Any mismatch → the bar
is `NOT_RUN_*` (e.g. `NOT_RUN_BASELINE_B1`), never a pass by default.

**E-Law 4 — Strictness.** Every comparison is a STRICT inequality. Ties FAIL.
There is no tolerance band on the bars (the 1e-9 tolerance lives only in the
accounting reconciliation, not here): `netPnL(P) == netPnL(B)` or
`maxDD(P) == maxDD(B)` is a fail of that bar.

**E-Law 5 — Calendar floor.** ≥6 executed test folds or the whole battery is
`NOT_RUN_INSUFFICIENT_CALENDAR` (campaign §3).

**E-Law 6 — Book integrity precondition.** Any arm whose journal fails the
FILL_ACCOUNTING_SPEC reconciliation (per-bar cash/position/equity, residual
≤1e-9; UNAVAILABLE≠0 law) is void (`NOT_RUN_INTEGRITY`, STOP-3) and every bar
referencing it is `NOT_RUN_*`. A void baseline is never treated as a beaten
baseline.

**E-Law 7 — Ordering.** All bars are necessary conditions. P1 is the PRIMARY
bar (the owner's sentence, verbatim semantics); P2–P8 are additional
governing conditions except where marked REPORTING/DISCLOSURE in §9. A
survivor claim requires every governing bar to PASS; one fail → the typed
close; missing evidence → `NOT_RUN_*` (never PASS).

**E-Law 8 — Budget counting unit (skeptic F-3).** Campaign
scored-arm-execution caps count baseline IDENTITIES, not raw executions. The
B4 battery is ONE baseline identity executed as ≥100 seeded sub-runs: it
counts as ONE identity on the scored-arm line, and its compute and
trial-ledger rows are disclosed on their OWN budget line (per the A1 plan
amendment: 48 identities + the B4 battery ≤128 seed sub-runs as a separate
line). Running the lawful P3 battery can therefore never self-trigger
STOP-2; only an identity-count overflow can. Leave-one-leg re-runs (P8) and
stress-tier re-runs (P6) are likewise identity-classified per the campaign
budget table, never counted as raw executions.

---

## 1. Baseline realization laws (frozen; extends architecture §9)

Each baseline re-runs the SAME legs under the SAME kernel/tier/calendar as the
policy; only the named layer changes. All are pooled over the same test folds
(E-Law 2).

| id | realization (the ONLY difference vs the policy) |
|---|---|
| B0 FLAT | no orders ever; equity constant $100,000; `netPnL=0`, `maxDD=0` by construction |
| B1 ALWAYS_ON | eligibility layer (L2, E1–E5) pinned ON for every leg at every decision; L3–L6 identical to the policy |
| B2 EQUAL_WEIGHT | eligibility pinned ON **and** L3 vol-targeted risk weights replaced by an equal split of the SAME total risk budget the policy deploys at that decision: B2 reads the policy arm's realized per-decision TOTAL HEAT TARGET (the frozen schedule recorded from the policy run over the same fold calendar), divides it equally across its active legs, and caps each leg's allocation at the frozen per-leg cap; L4–L6 identical. (Skeptic F-2: the earlier "0.5/N of the per-leg cap each" rule was degenerate — total book 0.1875% regardless of N — and contradicted P2's N=1 edge case; repealed. Under the corrected definition N=1 coincides with B1/leg-alone naturally.) |
| B3 BEST_SINGLE | the single best TRAIN leg, run ALONE through the same L2–L6 machinery. Selection statistic (FROZEN, skeptic F-17): `obj_B3(leg) = DSR_T(leg)` — the §5 DSR construction applied to the leg's TRAIN decision-cycle NET returns at cost tier ×2.0 (full kernel), with `SR₀`/`N_eff` taken from the full discovery ledger exactly as in P5. Selection happens at Stage-B freeze, TRAIN only, before any test PnL exists. Tie-break (FROZEN): (1) higher TRAIN net PnL at ×2.0; (2) lower TRAIN maxDD (USD); (3) lower TRAIN turnover (USD); (4) earlier trial-ledger row id (deterministic). The full tie-break record — every candidate's `obj_B3` and the values at each tie-break step — is written into the Stage-C trial identity |
| B4 RANDOM-GATE | eligibility replaced by duty+turnover-matched randomization: per leg, a seeded RNG toggles ON/OFF with marginal duty and flip rate matched to the policy's TRAIN-realized eligibility path; ≥100 seeds, seed list frozen in the trial identity |
| B5 CLOCK-GATE | eligibility replaced by a deterministic clock schedule per leg with the leg's duty matched to its policy-realized TRAIN duty (e.g. every k-th decision, k = round(1/duty), phase 0); frozen at Stage-B |
| B6 INVERTED | eligibility states collapsed to binary (ON or PROBATION → active; OFF → inactive) then COMPLEMENTED (active↔inactive); reactivated legs run at full L3 vol-targeted size (PROBATION half-size does not carry through the complement) |
| B7 LAGGED | the policy's own eligibility decision for each leg delayed by one fold (fold k uses the eligibility computed for fold k−1; the first test fold uses the last TRAIN fold's state) |
| B8 ORACLE-legs | perfect next-fold eligibility (upper bound); REPORTING ONLY, never governing |
| B9 INCUMBENT | FLAT-by-authority (nothing runnable today); the exposed RGC reading is historical context only; REPORTING ONLY |

---

## 2. P1 — PRIMARY bar, vs B1 ALWAYS_ON (same legs)

**Claim under test:** the policy's deciding layers (eligibility + sizing +
netting + risk budget + cost guard) add net PnL **and** reduce drawdown versus
running the SAME legs always-eligible under the same everything-else.

**Formula (pooled test folds, governing tier ×1.0):**

```
P1 = PASS  iff  netPnL(P)  >  netPnL(B1)        [strictly higher]
          AND maxDD(P)    <  maxDD(B1)          [strictly lower]
```

**Baseline:** B1 ALWAYS_ON (same legs, same L3–L6, eligibility pinned ON).

**P1-B0 sub-bar (mandatory, evaluated first):** `netPnL(P) > 0` pooled over
test folds at the governing tier. Rationale — drawdown vs FLAT is DEGENERATE:
B0 never trades, so its equity path is the constant $100,000 and
`maxDD(B0) = 0` by construction; demanding `maxDD(P) < 0` is impossible
(maxDD ≥ 0 by definition) and demanding `maxDD(P) < maxDD(B0) = 0` is the same
impossibility. The DD leg of the AND therefore cannot carry information vs
FLAT and is replaced by the absolute positivity requirement: a policy that
cannot beat idle cash after all costs has no claim to test against any other
baseline. (A policy with `maxDD(P) = 0` and `netPnL(P) > 0` passes P1-B0.)

**Fail close-codes:**
- P1-B0 fail (`netPnL(P) ≤ 0`) → `POLICY_NO_INCREMENTAL_VALUE` (sub-tag
  `P1_B0_ABSOLUTE`: no absolute net edge after all costs).
- P1 main fail (either leg vs B1) → `POLICY_NO_INCREMENTAL_VALUE` (sub-tag
  `P1_B1_PNL` / `P1_B1_DD` naming the failing leg).
- B1 not run / not comparable → `NOT_RUN_BASELINE_B1`; P1 unevaluable.

**Edge cases:**
- Tie on either quantity → FAIL (E-Law 4). This includes the pathological
  `maxDD(P) = maxDD(B1) = 0` (both monotone): the DD leg `0 < 0` is false.
- `netPnL(P) > netPnL(B1)` but DD worse → FAIL, sub-tag `P1_B1_DD`. The V1
  escape hatch ("DD-reduction path": PnL ≥ with DD <) is REPEALED — both legs
  strict, always.
- Policy FLAT the whole window (0 eligible legs ever): then `netPnL(P)=0`,
  P1-B0 fails → close `POLICY_NO_INCREMENTAL_VALUE` (`P1_B0_ABSOLUTE`). A
  never-trading policy is not a survivor.
- Fold-count floor (E-Law 5) and integrity precondition (E-Law 6) apply.

---

## 3. P2 — vs B2 EQUAL_WEIGHT and B3 BEST_SINGLE(train)

**Claim under test:** the increment survives against naive equal-risk
allocation of the same legs, and against just running the single best TRAIN
leg alone (is the portfolio more than its best member?).

**Formulas (pooled test folds, governing tier ×1.0), two sub-bars:**

```
P2a = PASS iff  netPnL(P) > netPnL(B2) AND maxDD(P) < maxDD(B2)
P2b = PASS iff  netPnL(P) > netPnL(B3) AND maxDD(P) < maxDD(B3)
P2  = PASS iff  P2a AND P2b
```

**Baselines:** B2 EQUAL_WEIGHT (same legs, equal risk, always eligible);
B3 BEST_SINGLE (best deflated ×2.0-cost-stressed TRAIN leg, alone — TRAIN-only
selection, frozen before any test PnL; the selection statistic never touches
test folds).

**Fail close-code:** `POLICY_NO_INCREMENTAL_VALUE`, sub-tags `P2_B2_PNL` /
`P2_B2_DD` / `P2_B3_PNL` / `P2_B3_DD`. Missing baselines → `NOT_RUN_BASELINE_B2`
/ `NOT_RUN_BASELINE_B3`.

**Edge cases:**
- Single admitted leg (N=1): B1 = B2 = B3 coincide NATURALLY with the leg run
  always-on — under the F-2 B2 definition the policy's total heat target at
  each decision IS the single leg's size, so the equal split allocates exactly
  that size (the repealed 0.5/N rule broke this coincidence); P2a/P2b then
  reduce to P1 and are still evaluated (they must hold).
- B3 selection tie → the frozen §1 tie-break; the tie-break record is part of
  the Stage-C trial identity.
- B2 total-heat schedule dependency: B2 is executed after (or jointly with)
  the policy arm in the same batch, reading the policy's recorded per-decision
  total heat target — a frozen input, never re-fit; if the policy arm is void
  (E-Law 6), B2 is `NOT_RUN_BASELINE_B2` with it.
- Tie on any quantity → FAIL (E-Law 4).

---

## 4. P3 — vs B4 RANDOM-GATE battery (≥100 seeds)

**Claim under test:** the eligibility layer's decisions are better than
duty+turnover-matched random gating — the value is in WHICH decisions, not in
the cadence.

**Formulas (pooled test folds, governing tier ×1.0).** Let `obj(·)` be the
Stage-B TRAIN-fitted frozen objective (deflated net PnL with DD penalty — the
same objective the Stage-B winner was selected on; frozen at Stage-B freeze,
never re-fit on test). Let `S_1..S_N` be the seed arms (N ≥ 100).

```
P3-clause-1 = PASS iff  #{ i : obj(P) > obj(S_i) } ≥ 0.95 × N
P3-clause-2 = PASS iff  netPnL(P) > median_i netPnL(S_i)
                 AND    maxDD(P)   < median_i maxDD(S_i)
P3 = PASS iff  P3-clause-1 AND P3-clause-2
```

`median` over N seeds: for even N the average of the two central order
statistics; the strict inequality is evaluated against that value.

**Baseline:** the full B4 battery (all seeds), each seed an independent
duty+turnover-matched randomization with its seed recorded. **Counting unit
(skeptic F-3, E-Law 8):** the battery is ONE baseline identity executed as
≥100 seeded sub-runs — it counts as ONE identity on the scored-arm budget
line, its seed sub-runs (≤128 per the A1 plan amendment) disclosed on the
battery's own budget line; running the lawful battery can never self-trigger
STOP-2.

**Fail close-code:** `POLICY_NO_INCREMENTAL_VALUE` (sub-tag `P3_B4_RANDOM`),
naming which clause failed. Battery with <100 seeds or non-frozen seed list →
`NOT_RUN_RANDOM_BATTERY` (P3 unevaluable; no partial battery passes).

**Edge cases:**
- Exactly 95/100 seeds below → clause-1 passes (≥ 95%).
- Ties with a seed count as NOT below (the policy must strictly exceed).
- Clause-1 can pass while clause-2 fails (e.g. objective dominated by one
  seed cluster) → P3 FAILS; both clauses are required precisely because the
  composite objective can hide a DD regression that the raw quantities expose.

---

## 5. P5 — deflation and overfit bars over the full discovery ledger

**Claim under test:** the survivor is not a multiple-testing artefact of the
discovery process that produced it.

**Inputs (all from `TRIAL_LEDGER.jsonl`, campaign §5):**
- `N` — number of COMPLETED, DEDUPED trials in the full discovery ledger at
  Stage-C (every Stage-A try, every Stage-B grid node and policy variant,
  every Stage-C arm; failed publications count — P-9 observed-denominator
  law). **Dedup rule (skeptic F-11):** byte-identical arms — identical
  `arm_config_digest` AND `data_snapshot_digest` AND `code_freeze_sha`
  (re-runs, reproduction twins) — count as ONE trial for N, for V[SR] and in
  the CSCV matrix; duplicates are listed, never double-counted.
- `N_eff` — the CLUSTER-ADJUSTED trial count (skeptic F-11): trials that are
  shape/pair/grid variants of ONE family count as ONE family cluster for
  N-efficiency. Cluster key = the frozen family identity
  (`family_id` + `class_candidate_id`); e.g. 3 VOLPROF shapes × 3 pairs =
  9 ledger rows = ONE cluster. `N_eff` = number of distinct clusters among
  the completed, deduped trials; **E[max] and SR₀ use N_eff.** Both N and
  N_eff are reported, and the DSR computed at raw N (the more-deflated,
  conservative value) is REPORTED alongside the governing N_eff DSR — the
  cluster adjustment may never hide deflation.
- `V` — cross-trial variance of trial Sharpes `{SR_n}` computed on the
  discovery (TRAIN) side over the deduped trials, common evaluation window
  per the CSCV matrix.
- The surviving policy's evaluation returns `{r_t, t=1..n}` on the pooled
  test folds (per-decision-cycle, i.e. weekly, NON-annualized Sharpe
  `SR̂ = mean(r)/stdev(r)`), with sample skewness `γ̂₃` and kurtosis `γ̂₄`
  (normal = 3).

**P5a — DSR > 0.95 (deflated Sharpe, Bailey & López de Prado construction).
Corrected per skeptic F-1: the earlier "DSR > 0" was VACUOUS — Φ(·) is
strictly positive for any finite argument, so it could never fail on the DSR
side:**

```
E[max]    = (1−γ)·Φ⁻¹(1 − 1/N_eff) + γ·Φ⁻¹(1 − 1/(N_eff·e))
            γ = Euler–Mascheroni ≈ 0.5772156649, e ≈ 2.7182818284
SR₀       = sqrt(V) · E[max]                       # expected max Sharpe under the null
DSR       = Φ( (SR̂ − SR₀)·sqrt(n−1)
              / sqrt(1 − γ̂₃·SR̂ + ((γ̂₄ − 1)/4)·SR̂²) )
P5a = PASS iff  DSR > 0.95
```

**Equivalence (what the bar means):** `DSR > 0.95` ⟺

```
SR̂  >  SR₀ + Φ⁻¹(0.95) · sqrt(1 − γ̂₃·SR̂ + ((γ̂₄−1)/4)·SR̂²) / sqrt(n−1)
      (Φ⁻¹(0.95) ≈ 1.6449)
```

i.e. **the policy's Sharpe must exceed the expected maximum of the N_eff null
Sharpes at the 95% confidence level**, with the standard error adjusted for
skewness, kurtosis and sample length. The edge must clear the
multiple-testing bar with 95% confidence — a point-estimate win over SR₀ is
not enough.

**IS/OOS double-correction disclosure (skeptic F-6).** `SR̂` is measured on
TEST-fold returns while `SR₀` is built from the discovery ledger's TRAIN
Sharpes — the bar therefore applies a TRAIN-side multiple-testing correction
to an OUT-OF-SAMPLE statistic, which is conservative beyond calibration (the
test folds have already survived a second, non-overlapping selection filter).
Every P5 report must carry the **PSR (no-deflation) value** alongside the DSR
so the calibration cost is visible:

```
PSR = Φ( SR̂·sqrt(n−1) / sqrt(1 − γ̂₃·SR̂ + ((γ̂₄−1)/4)·SR̂²) )     # SR₀ = 0
```

PSR is REPORTING-only; P5a governs on DSR at N_eff.

**P5b — PBO ≤ 0.5 (CSCV):** build the N×T trial-return matrix M on the
discovery side (deduped trials); partition T into S = 16 contiguous blocks
(trim leading periods if T mod S ≠ 0); for every combination c of S/2 blocks
as TRAIN (there are C(16,8) = 12,870): rank trials by Sharpe on c's TRAIN
blocks, take the top trial n*(c), compute its out-of-sample rank fraction
ω_c on c's TEST blocks, `λ_c = logit(ω_c) = ln(ω_c / (1−ω_c))` (λ = −∞ if
ω_c = 0, +∞ if ω_c = 1):

```
PBO = #{ c : λ_c < 0 } / C(S, S/2)      # fraction where the train-best is OOS-below-median
P5b = PASS iff  PBO ≤ 0.5
P5  = PASS iff  P5a AND P5b
```

**Fail close-codes:** `POLICY_DEFLATION_FAIL` (DSR ≤ 0.95);
`POLICY_OVERFIT_SUSPECT` (PBO > 0.5). Ledger incomplete/not hash-chained →
`NOT_RUN_DISCOVERY_LEDGER`.

**Edge cases:**
- N_eff = 1 (single family cluster): V is undefined → SR₀ := 0 and DSR
  reduces to PSR (state this in the report; the deflation term carries no
  information for a single cluster). PBO is undefined → P5b =
  `NOT_RUN_PBO_SINGLE_TRIAL` (recorded, not promoted; P5 then cannot pass on
  P5b alone — P5 requires P5b PASS or the typed NOT_RUN with owner
  disclosure).
- V = 0 (all trials identical Sharpe): SR₀ = 0, same reduction as N_eff = 1.
- Trials with no returns in a CSCV block (not runnable in that period) are
  excluded from that combination's ranking; exclusions are counted and
  reported; if >10% of the matrix is excluded → `NOT_RUN_CSCV_SPARSE`.
- T < 16 periods → `NOT_RUN_CSCV_SHORT` (S reduced to 8 or 4 is a declared
  amendment, never silent).

---

## 6. P6 — COST-STRESS SURVIVAL (the formerly missing bar; now fully defined)

**Claim under test:** the survivor is not an artefact of cost assumptions —
the P1 increment survives a 1.5× all-in cost regime, and its cost
sensitivity is disclosed at 2.0×.

**Stress semantics (all sub-bars):** at tier τ ∈ {1.5, 2.0}, EVERY variable
cost component is multiplied by τ — the measured spread cells C1/C2/C3 (both
p50 and p90 of each cell) AND every DECLARED component (U2 commission 0.35
bps, U3 slippage 0.2/1.0 pip, U4 swap 1.0 pip/night with Wed×3 preserved,
U14 conversion). Fills re-price accordingly:
`fill = mid_at_fill ± τ·(half_spread_at_fill + slip_band)`; commission
`τ·0.000035·|Δ|·fill`; swap `τ·1.0 pip/night` (per FILL_ACCOUNTING_SPEC §5,
which keeps the spread-once law intact at every tier). Non-variable fences
(margin U12, gross caps) are NOT scaled — they are capital fences, not costs.
The baseline in every P6 comparison is re-run under the SAME tier τ (a
stressed policy is only ever compared to the same-stressed baseline).

**P6a — governing, ×1.5:**

```
P6a = PASS iff  netPnL(P@1.5)  >  netPnL(B1@1.5)
           AND  maxDD(P@1.5)    <  maxDD(B1@1.5)          [pooled test folds]
```

**P6b — REPORTING only, ×2.0 (non-governing):** compute and report

```
report: netPnL(P@2.0) − netPnL(B1@2.0)   and   maxDD(B1@2.0) − maxDD(P@2.0)
```

alongside the P1/P6a numbers in every Stage-C report. A ×2.0 failure does NOT
fail the survivor claim by itself; it is mandatory disclosure content.

**P6c — COST_DOMINATED disclosure trigger (mandatory label, not a bar pass/fail):**
if at ×2.0 the policy's pooled net expectancy sign-flips to NEGATIVE
(`netPnL(P@2.0) < 0`), the typed disclosure `POLICY_COST_DOMINATED` is
ATTACHED to the survivor claim — **even if P1 and P6a held at ×1.0/×1.5**.
The claim survives only carrying the label; the label is a first-class row in
the trial record and the Stage-C report. Suppressing it is a STOP-3 integrity
trip, not a judgment call. (Distinction: the Stage-A LEG-level rule — a leg
whose TRAIN expectancy dies at ×1.5 is a typed KILL — remains unchanged,
campaign §4; P6c is the POLICY-level ×2.0 disclosure.)

**P6d — switching-cost ladder sub-bar (governing, ×1.0):** re-run policy and
B1 with the cost of EVERY state change (any position change: open, close,
resize) charged at the measured p90 of its applicable spread cell —
`fill = mid ± (p90_cell/2 + slip_band)` — instead of the base bar-quoted
charge (which realizes the cells' p50 level across the sleeve window; C1
EURUSD p50 0.3 / p90 0.5 pips is the canonical pair).

```
P6d = PASS iff  netPnL(P@p90)  >  netPnL(B1@p90)
           AND  maxDD(P@p90)    <  maxDD(B1@p90)
```

**Fail close-codes:** P6a or P6d fail → `POLICY_COST_DOMINATED` (sub-tags
`P6A_STRESS_1_5` / `P6D_SWITCH_P90`). Missing stressed runs →
`NOT_RUN_COST_STRESS_1_5` / `NOT_RUN_SWITCH_LADDER_P90`. P6c label omitted →
`NOT_RUN_INTEGRITY` (STOP-3).

**Edge cases:**
- B1 not re-run at the tier → `NOT_RUN_*` (never assume the baseline's
  stress response).
- `netPnL(P@1.5) > netPnL(B1@1.5)` with DD worse at ×1.5 → P6a FAILS
  (AND-semantics; the PnL leg alone rescues nothing).
- P6b numbers must be reported even when P6a already failed (post-mortem
  content).
- Commission scales on the stressed fill price (second-order; declared, not
  approximated away).

---

## 7. P7 — fold concentration (per-fold bar)

**Claim under test:** the pooled result is not one fold wearing an 8-fold
costume, and the risk is not one episode.

**Definitions:** `netPnL_f` = fold f's net PnL (force-flat at fold edge
included, E-Law 2). `maxDD_f` = max drawdown in USD of the equity path
restricted to fold f's window, measured from the running peak WITHIN the fold
(peak resets at fold start, consistent with fold-edge force-flat).
`pooled-equivalent DD share` for fold f:

```
DD_pooled_equiv(f) = maxDD(P) × ( duration(f) / duration(pooled test window) )
```

(the pooled maxDD expressed pro-rata on fold f's time scale; equal-length
folds → `maxDD(P)/n_folds`).

**Formula:**

```
P7 = PASS iff  ∀ f ∈ TEST:  netPnL_f  ≤  0.50 × netPnL(P)        [PnL concentration]
           AND  ∀ f ∈ TEST:  maxDD_f   ≤  2 × DD_pooled_equiv(f)  [DD concentration]
```

**Baseline:** the policy arm itself (self-bar; no external baseline).

**Fail close-code:** `POLICY_FOLD_CONCENTRATION` (sub-tags `P7_PNL_SHARE` /
`P7_DD_SHARE`, naming the offending fold). Pooled integrity precondition
E-Law 6 → `NOT_RUN_INTEGRITY`.

**Edge cases:**
- `netPnL(P) ≤ 0`: P1-B0 already failed (close there); P7 is then not
  evaluable and is recorded `NOT_RUN_P7_NO_POSITIVE_PNL` (never a pass).
- A fold with negative `netPnL_f` cannot breach the ≤50% share (its share is
  negative); it is still fully visible in the report — P7's PnL clause is an
  upside-concentration guard, the DD clause is the downside guard.
- `maxDD(P) = 0` (monotone pooled path): then every `maxDD_f = 0` (any
  within-fold drawdown would be a pooled drawdown), so `0 ≤ 0` holds; P7 DD
  clause passes trivially — by construction, not by leniency.
- `netPnL_f` exactly equal to 50.000…% of pooled → PASS (the bar is ≤, not <;
  concentration at exactly half is the declared boundary).
- Unequal fold durations (calendar amendments): the pro-rata denominator uses
  actual durations; the formula above is the frozen definition.

---

## 8. P8 — leave-one-leg robustness

**Claim under test:** the increment is not one leg wearing a portfolio
costume.

**Formula.** For EVERY admitted leg i (N legs → N re-runs): re-run the policy
WITHOUT leg i and re-run B1 without leg i (B1_{−i}: the remaining legs,
always-on, same everything-else). Then

```
P8 = PASS iff  ∀ i ∈ legs:  netPnL(P_{−i}) > netPnL(B1_{−i})
                        AND maxDD(P_{−i})   < maxDD(B1_{−i})      [pooled test folds]
```

Each removal re-runs BOTH arms (removing a leg changes B1's book too — the
netting, caps and cost budget all shift).

**Fail close-codes:**
- EXACTLY ONE leg's removal breaks P1-semantics → close
  `POLICY_ONE_LEG_CARRIER` (the increment is that leg; the portfolio added a
  costume, not value).
- TWO OR MORE removals break → close `POLICY_NO_INCREMENTAL_VALUE` (sub-tag
  `P8_COALITION`: the increment needs a minimal coalition, not the full
  portfolio — the full removal matrix is reported).
- Any re-run missing → `NOT_RUN_LEAVE_ONE_LEG` (partial matrices never pass;
  every leg requires its re-run pair).

**Edge cases:**
- N = 1 (single-leg portfolio): removing the only leg leaves an empty policy
  and B1_{−1} = B0 = FLAT, so `netPnL(P_{−1}) = 0 > 0 = netPnL(B0)` is false
  → P8 fails → `POLICY_ONE_LEG_CARRIER` (a single-leg portfolio can never
  pass P8; use B3/P2b language instead — the design must admit it).
- N = 0: P8 vacuous `NOT_RUN_LEAVE_ONE_LEG_NO_LEGS`; the policy is FLAT and
  P1-B0 governs.
- A removal that leaves 0 ELIGIBLE legs in some folds is legitimate (the
  re-run just goes FLAT those folds — W1); it is not a NOT_RUN.
- The DD leg applies per removal with the same strictness (E-Law 4).

---

## 9. Closing matrix — bar × baseline × quantity × governing status

| bar | baseline | net PnL condition | maxDD condition | status |
|---|---|---|---|---|
| P1-B0 (sub) | B0 FLAT | `netPnL(P) > 0` | degenerate (FLAT maxDD ≡ 0; §2) | **GOVERNING** |
| P1 (PRIMARY) | B1 ALWAYS_ON | `> B1` strict | `< B1` strict | **GOVERNING** |
| P2a | B2 EQUAL_WEIGHT | `> B2` strict | `< B2` strict | **GOVERNING** |
| P2b | B3 BEST_SINGLE(train) | `> B3` strict | `< B3` strict | **GOVERNING** |
| P3 clause-1 | B4 battery (≥100 seeds) | `obj(P)` exceeds ≥95% of seed `obj` | — (composite objective) | **GOVERNING** |
| P3 clause-2 | B4 median seed | `> median` strict | `< median` strict | **GOVERNING** |
| P4a | B5 CLOCK-GATE | `> B5` strict | `< B5` strict | **GOVERNING** |
| P4b | B6 INVERTED | `> B6` strict | `< B6` strict | **GOVERNING** |
| P4c | B7 LAGGED | `> B7` strict | `< B7` strict | **GOVERNING** |
| P5a | discovery ledger (N_eff clusters, V[SR]) | `DSR > 0.95` (≡ SR̂ > SR₀ at 95% confidence, §5) | — | **GOVERNING** (skeptic F-1 correction) |
| P5b | discovery ledger (CSCV) | `PBO ≤ 0.5` | — | **GOVERNING** |
| P5-disclosure | test returns + discovery ledger | PSR (no-deflation) and raw-N DSR reported alongside the governing N_eff DSR | — | REPORTING (calibration-cost visibility, skeptics F-6/F-11) |
| P6a | B1 @ tier ×1.5 | `> B1@1.5` strict | `< B1@1.5` strict | **GOVERNING** |
| P6b | B1 @ tier ×2.0 | report ΔPnL | report ΔDD | REPORTING (non-governing) |
| P6c | policy @ tier ×2.0 | `netPnL(P@2.0) < 0` → attach `POLICY_COST_DOMINATED` label | — | DISCLOSURE TRIGGER (mandatory label; suppression = STOP-3) |
| P6d | B1 @ p90 switching ladder | `> B1@p90` strict | `< B1@p90` strict | **GOVERNING** |
| P7 PnL share | self (per fold) | each fold ≤ 50% of pooled net PnL | — | **GOVERNING** |
| P7 DD share | self (per fold) | — | each fold `maxDD_f ≤ 2 × DD_pooled_equiv(f)` | **GOVERNING** |
| P8 ∀ legs | B1_{−i} per removal | `> B1_{−i}` strict, every i | `< B1_{−i}` strict, every i | **GOVERNING** (exactly-one break → `POLICY_ONE_LEG_CARRIER`) |
| — | B8 ORACLE-legs | report | report | REPORTING (bound only) |
| — | B9 INCUMBENT | report | report | REPORTING (context only) |

Every "strict" cell is a strict inequality with ties failing (E-Law 4). Every
governing row is a necessary condition for a survivor claim (E-Law 7). All
quantities are net of ALL costs at the governing tier from the
FILL_ACCOUNTING_SPEC book identity; every arm in a comparison shares freeze
SHA, calendar, kernel digest, tier and fill model (E-Law 3). Missing evidence
is `NOT_RUN_*` — never an inferred PASS.
