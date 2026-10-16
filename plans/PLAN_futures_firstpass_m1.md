# PLAN — FUTURES-FIRSTPASS-M1 (first-passage forecast model experiment)

Status: REGISTERED (owner dispatch 2026-10-16 "OWNER DECISION —
FIRST-PASSAGE MODEL EXPERIMENT: CHỌN M-A", verbatim materiality decision
recorded in the cycle control dir `AUTH_MA.md`). One Lead session owns
this cycle (P-17). Plan + registry registered atomically via
`researchctl cycle register`.

Lineage: PREP-FORECAST-DESIGN-20261016 → TARGET-CENSUS-20261016 (the
authorized one-shot outcome census; verifier CONFIRM_WITH_FINDINGS,
9,746/9,746 rebuild 0 disagreements) → FIRSTPASS-MODEL-PREP-20261016
(design/code/tests; verifier CONFIRM_WITH_FINDINGS 1H/7L corrected) →
THIS cycle (the bounded run). All of it exploratory on the
DEVELOPMENT_OUTCOME_EXPOSED 2010-06→2022-12 surface.

## 1. Frozen contract (no deviation permitted; source of truth = PREP docs)

Design, laws, hashes and execution order are EXACTLY those committed in
`research/control/FIRSTPASS-MODEL-PREP-20261016/` at branch tip
`eb491bd6…` (runner digest `1fd92dea…`): estimand unconditional-at-
decision 4-class {UPPER_FIRST, LOWER_FIRST, TIMEOUT, AMBIGUOUS}; specs
S0/S1/S2; softmax L2 λ=1.0 deterministic zero-init; single pre-declared
fallback; folds train ≤ y−4, eval years 2014–2022 (2011–2013 are frozen
NOT_EVALUABLE_EMPTY_TRAIN); session grouping; census rows reused by
digest; k=0.06 / 30-min wall-clock / A0 / PIT laws inherited unchanged;
barrier≤cost rows NOT excluded. NO new k/horizon/anchor/filter/feature/
seed/threshold; no fold change; M-B is dead for this run.

## 2. Materiality — OWNER-PINNED M-A (verbatim in AUTH_MA.md)

PASS (ES z0.10) iff: mean paired Δlogloss(S2−S1) ≤ −0.010 nats AND
Δlogloss ≤ −0.005 in ≥2/3 era buckets, on the frozen CI/sample/stability/
NOT_EVALUABLE grammar (METRICS_AND_MATERIALITY_PACKET §2). FAIL otherwise.
NOT_EVALUABLE per §2 triggers. NQ/z0.05/S2−S0/S1−S0 = DIAGNOSTIC, never
rescue. M-A PASS = exploratory forecast increment ONLY — not a strategy,
not a policy license.

## 3. Identity and budget

108 planned fits (3 specs × 9 evaluable folds × 4 datasets) + 12 frozen
NOT_EVALUABLE_EMPTY_TRAIN records; every fit individually ledgered;
planned/attempted/computed/failed/published accounted separately;
retry/reproduction never hidden. Search budget: 0 (no hyperparameter/
feature/seed/fold/threshold search; the frozen fallback is not a search
axis). Registry budget-max = 108 (computed fits).

## 4. Scope and hard boundaries

Outcome access = frozen census artifacts ONLY (4 input CSVs + 4 census
output row files, digests pinned); NO parquet, NO 2023+/S1, no FX
outcomes, no prospective activation. No policy/PnL/orders; no LONG/SHORT
mapping; the economics layer is the frozen reporting diagnostic only.
Labels: EXPLORATORY_OUTCOME_EXPOSED on every artifact.

## 5. Gates (all before any historical fit)

(a) AUTH_MA recorded; (b) document-consistency check PASS (done, no
discrepancy); (c) run driver committed and exercised end-to-end on
SYNTHETIC data (non-vacuous dry-run producing every output artifact);
(d) independent prelaunch audit of the frozen contract + driver;
(e) canonical heavy lock acquired legitimately (foreign holder →
NOT_RUN_RESOURCE_CONFLICT checkpoint, no kill/contention); (f) input
digest check at run start (drift → abort). Failure discipline: FAIL
record before any fix; exposure-preserving accounting; no design change
passed off as a bug fix.

## 6. Terminal outcomes (preregistered)

- RUN_COMPLETE_M-A_PASS / RUN_COMPLETE_M-A_FAIL / RUN_COMPLETE_M-A_NOT_
  EVALUABLE / NOT_RUN_RESOURCE_CONFLICT / BLOCKED_<cause> — each closes
  the cycle with full ledgers, independent verifier report, REPORT_VI,
  NEXT_DECISION_PACKET and structured handoff. A FAIL/INSUFFICIENT is a
  valid terminal result; it opens NO search wave.
- Post-experiment promotion (policy layer, prospective, scored
  economics) requires a NEW owner decision with its own P-8 typed GO.
  This cycle never enters that territory.
