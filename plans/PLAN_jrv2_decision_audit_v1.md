# PLAN JRV2-DECISION-AUDIT-V1 — independent diagnostic audit of JEV-REGIME-ROUTER-V2 decisions

> Status: `PLANNED_NOT_STARTED` → `ACTIVE_LIGHT` on registration. Owner
> instruction 2026-09-23. Diagnostic ONLY: it evaluates whether JEV V2's
> persisted regime decisions were consistent and reasonable given the
> information available at each decision time. It is NOT a strategy cycle,
> does NOT modify JEV V2, and CANNOT overturn the terminal verdict
> `JEV_NO_INCREMENTAL_VALUE`. V2 corpus is outcome-observed; nothing here
> demonstrates profitability or authorizes paper/live.

## 0. Cycle identity

```text
cycle_id     JRV2-DECISION-AUDIT-V1
class        S0 DIAGNOSTIC AUDIT (read-only over JEV-REGIME-ROUTER-V2
             terminal evidence; all writes confined to this audit worktree)
budget       0 scored cells; 0 billable provider calls; 0 PnL computations
S1           SEALED_UNTOUCHED (never opened)
orders       NONE
go_phrase    none (no gate consumes a GO: zero provider calls, zero scored
             computation, zero writes outside the audit worktree)
forbidden    research/control/SANDBOX-OVERFIT-3ASSETS/ (never read);
             JEV V1 artifacts as inputs (V2 artifacts only);
             any write into the JEV-REGIME-ROUTER-V2 worktree or the root
             checkout other than the registry (via researchctl only)
```

## 1. Subject

The frozen V2 decision corpus on the V2 integration worktree
(`.worktrees/jev-regime-router-v2/integration`, measured HEAD recorded at
intake): 13,315 decision lines in `runtime/replay/{BTC_H1,BTC_H4,SPY_D1}/
decisions_*.jsonl` (8,567 + 1,997 + 2,751), the frozen `jrv2` code package,
the 10 freeze contracts, the classification/backtest reports and the A7
terminal audit. Evidence tier: V2 data is outcome-observed (2025-08→2026-08
BTC, 2015→2026-09 SPY).

## 2. Method

### 2.1 Full census (by code, every decision)
- Recompute the authoritative timeline with the FROZEN V2 code path
  (`jrv2.data.load_cell` + `jrv2.features` + `jrv2.questionio.sequential_timeline`
  + `jrv2.safety`), cache-only: no provider call is possible (the census
  imports only `CacheProvider`).
- Reconcile against artifacts: per-cell counts, status census
  (OK/SCHEMA_ERROR/TIMEOUT/PROVIDER_ERROR), effective-label share,
  persisted occupancy, switches, longest UNKNOWN runs vs
  `REGIME_CLASSIFICATION_REPORT.md`; usage totals vs
  `bulk_response_manifest_*.json` and the A7-2 used-only totals.
- Independent per-line checks beyond the V2 validator ( violations of these
  are census findings; anything the frozen contracts do NOT define is
  recorded as `ANOMALY_REVIEW`, never auto-FAIL):
  state_id recomputation; input_digest recomputation from reconstructed
  states (staleness/lookahead proxy at the state level); schema field;
  model pin echo; probability option sets, non-negativity, sum-1 drift
  (validator tolerance ±0.01 recorded exactly); choice == argmax(probabilities);
  confidence vs top1-probability relationship (contract silent → measured
  and reported); phase-margin recompute vs the safety gate; contradiction
  reason census; duplicate state_ids; request_id uniqueness; usage
  presence/absence rules; monotonic bar order vs state_id order.
- Anomaly ledger: every anomaly row carries (cell, state_id, bar_index,
  check, observed, expected-or-UNSPECIFIED, disposition).

### 2.2 Blind market-meaning review (label-masked)
- RUBRIC LOCKED FIRST (file committed before any case sheet is rendered):
  phase definitions in market terms over the state's named fields only;
  allowed blind verdicts: ACCUMULATION | UPTREND | DISTRIBUTION | DOWNTREND
  | UNDETERMINED (explicit "cannot determine" is legitimate and never forced).
- SAMPLING LOCKED SECOND (seeded, stratified, script committed before
  unblinding): strata = cell × effective label (4 phases + UNKNOWN);
  within strata: confidence/margin high-low halves, transition zones
  (±3 bars of a persisted switch), fold coverage; rare phases sampled at
  100% with counts disclosed; target 200–240 cases.
- CASE SHEETS carry ONLY the state the model saw (9 named bins, 14 named
  numerics, prior_structure/prior_direction, cell, regime clock). No JEV
  label, no stratum, no PnL, no future bars, no outcome.
- The reviewer judges every sheet under the locked rubric; then (and only
  then) JEV labels are joined. The measured quantity is BLIND–JEV
  agreement/disagreement by stratum — it is NOT called accuracy (no
  pre-registered independent ground truth exists).

### 2.3 Independent methodological check
- An independent fresh-context checker (subagent, read-only) verifies:
  sampling reproducibility from the committed seed, label-masking of the
  case sheets (grep-level + structural), census-number reproduction, and
  internal consistency of the conclusions. Its verdict is recorded
  verbatim; it does NOT edit the audit. If unavailable → NOT_RUN recorded.

## 3. Conclusions the report must answer (owner's questions)

1. How many decisions pass/fail the safety filter and why (reason census)?
2. Does JEV contradict itself hierarchically, or show high confidence on
   ambiguous states?
3. Which phases are crisply identified; which are thin or confused?
4. Does code-owned UNKNOWN protect against bad decisions or hide
   identifiable ones?
5. Is there evidence to justify a NEW non-JEV rule experiment? If yes:
   only a prospective proposal with pre-registered rules + future
   validation; no threshold tuning on the outcome-observed V2 corpus.

## 4. Deliverables (all inside this audit worktree)

- `research/control/jrv2_decision_audit_v1/census/census_*.json|csv`
  (machine-readable full census + anomaly ledger)
- `research/control/jrv2_decision_audit_v1/blind/{rubric.md,sampling.json,
  cases.jsonl,blind_reviews.jsonl,unblinded_agreement.json}`
- `research/control/jrv2_decision_audit_v1/AUDIT_REPORT.md` (owner-readable)
- `research/control/jrv2_decision_audit_v1/manifest.json` (sha256 of every
  artifact + input digests) + reproduction commands
- PASS/FAIL/NOT_RUN verdict per check; registry events via researchctl only.

## 5. Boundaries

No push, no merge to main, no V2 writes, no V1 reads, no S1, no orders, no
credentials, one heavy worker rule respected (this audit is not heavy:
JSONL parsing + cached-feature recomputation, minutes of CPU). Root
checkout is bootstrap space; all audit artifacts live in
`.worktrees/jrv2-decision-audit-v1/integration`.
