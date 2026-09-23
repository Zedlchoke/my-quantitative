# A6 — Controls and evaluation design memo (RSMV1-A6-CONTROLS)

Cycle `REGIME-STRATEGY-MAPPING-V1`, S0 discovery. Role A6, fresh context.
This memo justifies the four PROPOSED freeze contracts this lane owns:

- `freezes/rsmv1_arms_freeze.proposal.json`
- `freezes/rsmv1_selection_freeze.proposal.json`
- `freezes/rsmv1_turnover_freeze.proposal.json`
- `freezes/rsmv1_evaluation_freeze.proposal.json`

Knowledge-boundary compliance: this lane computed no PnL, read no outcome
data, and used exactly one predecessor outcome fact — the V2 terminal
verdict `JEV_NO_INCREMENTAL_VALUE`. Every V2 number the freezes need (stored
tier-1 totals, trade counts) is left as an explicit `TO_PIN_AT_FREEZE_BY_A1`
obligation with its source law, so the proposals contain no outcomes and A1
can freeze them without a design change.

---

## 1. What each arm isolates (identification logic)

The design is a difference-of-differences ladder. Each scored arm removes or
adds exactly one design element, so any gate failure names the missing
ingredient:

| Arm | Isolates | Consumed by |
|---|---|---|
| A1 ALWAYS_ON_MR | mean reversion with **zero regime information** | G3 bar |
| A2 ALWAYS_ON_TREND | trend-long with **zero regime information** | G3 bar |
| B ORIGINAL_V2_MAPPING_REFERENCE | the predecessor mapping under **predecessor mechanics** (attrition included) | G4 bar |
| C REGIME_SPECIALIST_ROUTER | the full hypothesis: regime-conditional specialists + nested selection + anti-churn law | the candidate |
| D SPARSE_JEV_RISK_OFF_VETO | **standing aside in risk-off only** — no specialist structure | G6 anti-"trades less" bar |
| E DETERMINISTIC_PROPOSAL_PLUS_JEV_VETO | the V2 CONFIRM design re-run under the **new turnover law** (churn-law value on V2's mechanism) | mechanism-vs-attrition decomposition |
| F EPISODE_SHUFFLED_MATCHED_CONTROL | the **null**: same occupancy/churn/dwell/exposure, destroyed label→return alignment | G6 null bar |

Readings the ladder licenses:

- **C vs max(A1,A2)** (G3): does regime *conditioning* beat the best blind
  baseline, or is the router just repackaging one always-on arm?
- **C vs B** (G4): the honest predecessor comparison. It is only legitimate
  because of B's engine-equivalence gate: B must reproduce the V2 JEV_ONLY
  tier-1 stored totals to <1e-6 **before any C outcome exists**. Without that
  gate, "we beat our re-implementation of V2" would be unfalsifiable
  re-implementation risk; with it, the comparison is against V2 itself.
- **C vs D** (G6a): V2's router lost heavily after costs; a router could
  "improve" merely by trading less. D is the sparse, outcome-informed
  risk-off control: if C cannot beat *standing aside in bad regimes*, the
  specialist library added nothing. D's outcome-informed base (BTC: MR,
  SPY: TREND) is disclosed in the freeze; controls may be outcome-informed,
  the candidate C never is.
- **E**: keeps V2's deterministic proposer + Jev veto but runs the new
  turnover law. E vs B isolates the churn law's contribution on an otherwise
  V2-identical mechanism — the arm-level half of the "mechanism vs attrition"
  question. E is a control: it is never a candidate and never promoted.
- **F vs C** (G6b): the null. If label-shuffled routing with matched
  structure earns a similar net, C's edge is not regime information.

FLAT and BUY_AND_HOLD are reported references, never scored, never gates
(FLAT is the degenerate router; buy-and-hold is market context).

## 2. Why each F-matching tolerance

F reuses the V1/V2 segment-permutation machinery byte-for-byte (seeds
20260901..20260921, ≤200 rejection-sampling attempts per seed) and its frozen
tolerances:

- **occupancy ±2pp per label** — parity of regime *composition*. 2pp is
  tight relative to the smallest regime share a router can trade on, so the
  null cannot win by meeting a different market mix. It is simultaneously
  loose enough that rejection sampling terminates (measured V2 experience:
  the machinery accepts within budget).
- **switches ±10% and mean dwell ±10% (relative)** — parity of *churn*. The
  null must pay a comparable number of round-trip costs; 10% relative keeps
  the cost burden within ~10% of C's while leaving the sampler a feasible
  target. Matching both jointly is what makes "C beats F" a statement about
  label→return alignment rather than about paying less friction.
- **invested fraction ±2pp** — parity of *exposure*. Without it a lucky null
  with half the market exposure could look indistinguishable.

All four tolerances are carried over unchanged from the frozen V1/V2
machinery deliberately: reusing them adds zero new researcher degrees of
freedom, and this cycle's contribution is the candidate, not a new null
design.

The one definitional adaptation is disclosed in the freeze: invested
fraction is measured on **routed targets per fold** (C's actual non-FLAT
target bars vs the seed path routed through C's frozen per-fold selection
maps), which is the correct analogue now that C's mapping is fold-dependent,
rather than a single global label set.

## 3. Why the Q-11 movement checks are mandatory — and fail-closed

The predecessor's shuffled null was `null_invalid` on **all 9** cell×tier
combinations: the permutation machinery preserved label→forward-return
association, so the "null" was not a no-information baseline and no
conclusion could rest on it. That failure was only *detected* post hoc.

This design makes silent repetition structurally impossible:

1. Movement is an **acceptance criterion inside the loop**: a candidate path
   must move BOTH Q-11 statistics (lag-1 autocorr of the label stream AND
   label→forward-return association) by >0.02 absolute vs C's actual path,
   in addition to the structural match, within the 200 attempts.
2. Failure is **fail-closed at the whole-cell level**: any seed that cannot
   produce a matched-and-moved path makes the entire F control for that cell
   `NOT_RUN_CONTROL_MATCHING` — all 21 seeds discarded, no partial null, no
   median computed from a broken ensemble. Gate 6 then rests on A/B/D/E with
   `F_INVALID_REST_ON_ABDE` recorded. There is no code path in which an
   unmoved null contributes to a verdict.

0.02 absolute is the frozen V1/V2 magnitude (carried, not tuned).

## 4. How the trial budget is counted

- **21 = 3 cells × 7 arm instances** (A1, A2, B, C, D, E, F). Fixed before
  the scored run; all 21 reach a terminal state (scored, `NOT_RUN_*`-labeled,
  or hard-blocked) before any verdict.
- **References excluded**: FLAT and BUY_AND_HOLD consume no budget and are
  never gates.
- **Seeds are not trials**: F's 21 seeds are one scored arm instance per
  cell; the median is the headline, all seeds reported.
- **Publication failure ≠ un-trialed**: any computed outcome counts even if
  its artifact fails to publish. Otherwise a losing outcome could be
  "lost" by an I/O failure — the classic optional-stopping loophole.
- **Zero-cost variants are diagnostics inside the same trial** and can never
  support a PASS (a candidate that survives only at zero cost FAILs per the
  turnover freeze T7).
- P1 attribution and P2 feasibility are diagnostic (pre-registered in the
  plan) and consume no scored trials.

## 5. Selection law: totality

The nested law (outer folds 1–4 at the V2 boundaries; inner = folds 1..k−1;
fold 1 ⇒ FLAT everywhere; inner floors 5 episodes / 150 eligible decisions;
≤2 specialists per regime; pooled inner NET at 1.0x inside regime windows;
stability `ceil(2|S|/3)` wins on comparative folds S; exact-tie order FLAT >
BTC-only-short > long-capable) is encoded as an **ordered first-match-wins
rule list** with an exhaustive reason-code vocabulary (11 codes). Every
(cell, regime, fold) terminates in exactly one outcome with exactly one
code; the test suite walks the rule list and the stability table and asserts
no unspecified tie or uncovered branch exists. `ceil(2|S|/3)` reproduces the
plan's "every fold when ≤2 inner folds, else ≥2/3" exactly: |S|=1→1, |S|=2→2,
|S|=3→2, |S|=0→FLAT (no comparative evidence).

Outer floors (20/3/100) label thin regimes `NOT_RUN_THIN_REGIME` per
(cell, regime, fold), route them FLAT, and propagate the label into the
evaluation denominator. Cells are never pooled; H1 vs H4 is never selected
by PnL.

## 6. Turnover law as attrition control

The turnover freeze applies to C, D, E (not B — B must reproduce V2's
attrition for the equivalence gate; not A1/A2 — no regime-driven switching).
Chain: persisted machine (confirm 2 / dwell 6 / cooldown 3, pinned) →
transition buffer k=1 regime bar → min-dwell floor 6 (specialists may extend,
never shorten) → no-op law (same direction ⇒ zero fills; specialist switch
only at flat or direction change) → reversals charge close+open →
`regime_switch_count` and `position_switch_count` reported separately with
single-cause fill tags. The rejection law (T7) is the freeze's teeth:
C fails the cell if `position_switch_count ≥ ` the pinned V2 JEV_ONLY trade
count, and any candidate surviving only at zero cost fails outright. The
`unnecessary_close_reopen` counter must be identically zero — if it ever
fires, that is a hard `TURNOVER_LAW_VIOLATION`, not a statistic.

## 7. Evaluation: gates, ladder, ceiling

Gates G1–G8 are the plan's §11 gates with exact comparators (G5 fold law:
≥3/4 positive folds OR positive with best fold removed; G6 falls back to
D-only with an explicit `F_INVALID_REST_ON_ABDE` record when F is invalid).
The verdict ladder is total and ordered TECHABORT →
BLOCKED_THIN_REGIME_SAMPLE → BLOCKED_COST_OR_CONTROL_AUTHORITY → candidate
verdict, so every terminal state maps to exactly one of the five vocabulary
strings. The contamination law is baked in: the corpus is wholly
outcome-observed, so **even an all-gates-PASS cycle earns only
`DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION`**; no promotion, no shadow,
successor must be prospective, S1 `SEALED_UNTOUCHED`.

## 8. Honest decision table

| Gate pattern | Verdict |
|---|---|
| timeline/equivalence/reproduction/law-violation mechanical failure | TECHABORT |
| all cells thin (C ≡ FLAT by floor law) | BLOCKED_THIN_REGIME_SAMPLE |
| cost identity or D/E control authority broken, ≥1 cell evaluable | BLOCKED_COST_OR_CONTROL_AUTHORITY |
| all 8 gates PASS on all evaluable cells | DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION (the ceiling) |
| positive at 1.0x but ≤ 0 at 1.5x | NO_REGIME_STRATEGY_INCREMENTAL_VALUE (G2) |
| beats B but not the better always-on | NO_REGIME_STRATEGY_INCREMENTAL_VALUE (G3) |
| profitable only through one fold | NO_REGIME_STRATEGY_INCREMENTAL_VALUE (G5) |
| beats A/B but not D or a valid F median | NO_REGIME_STRATEGY_INCREMENTAL_VALUE (G6) |
| economics pass, reproduction or A7 fails | TECHABORT |
| anything else after ≥1 evaluable cell | NO_REGIME_STRATEGY_INCREMENTAL_VALUE |

## 9. Decisions A1 must arbitrate at freeze time

1. **Pin V2 reference quantities** (stored JEV_ONLY tier-1 totals for the B
   equivalence gate; per-cell trade counts + their ledger definition for T7)
   into `v2_reference_pins` / `v2_trade_count_pins`, with artifact digests.
   If V2's trade-count definition is round-trip- or exit-based, A1 records
   the exact mapping to `position_switch_count` pre-outcome; the T7 law is
   unchanged.
2. **Specialist library landing**: `freezes/specialist_library_freeze.json`
   (P3) must exist before any candidate PnL; C is not executable without it.
3. **F invested-fraction definition**: confirm the forked matching code is
   adapted to the routed-targets-per-fold measurement (freeze §F).
4. **A7 floor adjustments**: numeric sample floors may be adjusted by A7
   pre-outcome only, with rationale recorded in the selection freeze.

No other design latitude is left open: everything else in these four files
is a constant, an ordered rule, or a pinned digest.
