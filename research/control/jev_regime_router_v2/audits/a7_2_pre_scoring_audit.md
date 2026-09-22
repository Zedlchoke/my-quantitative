# A7-2 Pre-Scoring Audit — JEV-REGIME-ROUTER-V2

**Verdict: AUTHORIZED_FOR_STOP2_REPORT** (zero unresolved HIGH/CRITICAL)
**Audited HEAD:** `8416d2817f49d28e2c2f18b334817240c12f0444` on `orca/jev-regime-router-v2-integration`
**Auditor:** A7 independent fresh-context (A7-2, plan §9 — after bulk, before any scored backtest)
**Machine-readable authority:** `audits/a7_2_pre_scoring_audit.json` (schema `jrv2_a7_2_pre_scoring_audit@1`)

## Scope and method

Bulk decision corpus under owner GO `GO JEV REGIME V2 BULK HISTORICAL REPLAY`:
13,315 decisions = BTC_H1 8,567 + BTC_H4 1,997 + SPY_D1 2,751; worker heavy-lock
lease 10:51:20Z → 15:42:29Z (FINISHED, cell counts in the release note).

Every verdict was recomputed from RAW evidence, not manifests: the auditor
independently re-ran the strict sequential state-builder walk per cell from the
sha-verified frozen data and compared **100% of all 13,315 decision lines**
(stronger than every mandated sample) on state_id sequence, producer
`input_digest`, prior echoes, schema validation, effective mapping and the
persisted timeline; all cache keys were recomputed from an independently
recomputed active prompt digest; usage was decomposed used-vs-leftover from
cache bytes. The audit made **zero live API calls**, ran **no preview, no
replay, no backtest**; the only backtest-surface touch was the quarantine
refusal check, which computes nothing. **No PnL was computed or viewed.**

## Checklist one-liners (all PASS)

1. **Completeness** — 8,567/1,997/2,751 lines == fold contract (fold sums
   reconcile); state_ids unique; file order equals the independently recomputed
   builder sequence for 100% of states (0 mismatches). `LOCAL_INVALID` count 0.
2. **Cache integrity** — all 13,315 (state_id, digest) pairs present in their
   own cell's cache; no cross-cell mixing (0 shared pairs across cells;
   1,997/1,997 H1/H4 shared-sid contents digest-disjoint; 0 foreign sids).
   BTC_H1 8,638 entries = 8,567 used + **71 stale leftovers**, all belonging to
   the 100 preview seeds and all stored **before** bulk start; the other 29
   preview seeds were legitimately reused (byte-identical requests, `cached:true`
   lines). Zero contamination.
3. **Error handling** — non-OK recomputed exactly: H1 17 (6 SCHEMA_ERROR +
   8 TIMEOUT + 3 PROVIDER_ERROR), H4 3, SPY 1; **every** non-OK maps fail-closed
   to code-UNKNOWN (checked on all 13,315 lines); full timeline recompute
   reproduces switches **90/31/34**, max UNKNOWN runs **6/7/14**, persisted
   counts, effective counts and dwell distributions to the digit.
4. **Model pin** — every OK response in every cache (incl. unused and preview)
   echoes exactly `jev-1.13.0`; zero drift.
5. **Prompt freeze** — active digest `a5ae1644…` recomputed via the frozen TS
   module keys **all** replay + preview cache entries (0 bad) and trial-1
   canary entries; the only superseded-digest keys are the 39 disclosed
   pre-historical trial-0 canaries; git shows no prompt/freeze/adapter/source
   change after design trial 1 (08:41:52Z) — i.e. none after the first
   historical call (10:43:15Z).
6. **Budget honesty** — cache totals recompute byte-equal: 58,360,983 in /
   1,744,755 out (the disclosed 58.4M/1.745M); formula 4,369×13,315 = 58,173,235
   registered in registry history; **85% checkpoint confirmed disclosed mid-run**
   (registry commit `37c190a6`, 14:55:05Z, 49.4M/58M, cap-watcher armed).
   Used-only spend 58.05M (−0.21% vs formula) — see F5.
7. **No outcome leakage** — zero PnL/equity/trade-pattern hits anywhere under
   `runtime/` or `evidence/`; the only namespace-wide matches are the frozen
   metric-name list and audit prose; backtest CLI refuses fail-closed
   (`REFUSED_BACKTEST_QUARANTINE`, exit 20, even with a presented token);
   `SCORED_GO.json` does not exist.
8. **Freeze integrity** — `verify-freezes` ok=true now (10/10 incl. amendments;
   security + V1-isolation scans 0 findings); `freezes/` untouched since
   08:41:52Z, before preview and bulk; tracked cycle paths clean.
9. **S1 / broker / credentials** — S1 `SEALED_UNTOUCHED`; broker/order surface
   scan clean; the live API key value appears in **zero** files (tracked or
   runtime); zero `sk-` patterns; name-only references per the env-only law.
10. **Prior-state law** — 50 deterministic-random consecutive pairs per cell
    (150 total): t+1's request carries exactly the persisted prior computed
    from t's response (echo equality + digest equality, which pins the whole
    named payload including `prior_structure`); 150/150 PASS — and the 100%
    digest-equality check extends the law to every state.

## Findings

- **F5 (LOW) usage-accounting convention.** Manifests sum **all** cache
  entries, so the headline "58.4M (+0.3% vs 58.2M)" includes 310,109 input
  tokens of *preview-billable* stale leftovers, and 29 preview responses
  (126,745 input) are counted in both the preview and bulk disclosures.
  Used-only = 58,050,872 (−0.21% vs formula); distinct-new bulk = 57,924,127.
  No convention breaches the registered cap; the disclosure was conservative
  (overstated). STOP-2 report should quote used-only/distinct-new alongside.
- **F6 (LOW, carry-forward of A7-1 F3, measured closed at this phase).**
  state_id law has no regime-clock dimension (1,997 H1/H4 shared sids). A7-2
  verified the required segregation: separate per-cell decision stores and
  cache dirs, zero shared (sid, digest) pairs, 1,997/1,997 digest-disjoint
  content. Residual rule for the scored phase: keep per-cell indexing.

Observations: bulk tools committed post-bulk (verification-only, off the
provenance path); the registry's "+0.3%" headline is the all-cache convention
(F5); H1 effective UNKNOWN 0.427 recorded as measured context for the owner
(classification quality is a STOP-2 concern, not an audit defect).

## Runs (all by the auditor, this audit)

pytest **127 passed**; adapter `tsc --noEmit` clean; adapter tests **47/47**;
`verify-freezes` ok (10/10, scans zero); census ok (35,039 rows; H1 8,759 /
H4 2,189 / SPY 2,943 — equal freeze); backtest quarantine refusal verified;
heavy lock free; live calls by audit **0**.

## Authorization

The bulk decision corpus is **complete, honest, frozen and untainted**. This
audit authorizes proceeding to the **STOP-2 V2 owner report**. It expresses no
opinion on the scored-backtest GO itself: that remains the owner's
phrase-gated decision at STOP-2.
