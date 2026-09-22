# A7-1 Pre-Bulk Audit — JEV-REGIME-ROUTER-V2

- Auditor: A7 independent fresh-context (pre-bulk)
- Audited HEAD: `3b0f82f31bdad21a2969cea7f2eb7ce34d8bc885` (branch `orca/jev-regime-router-v2-integration`, clean tree)
- Machine-readable verdict: `audits/a7_1_pre_bulk_audit.json` (schema `jrv2_a7_1_pre_bulk_audit@1`)
- Verdict: **AUTHORIZED_FOR_STOP1_REPORT** (`zero_unresolved_high_critical: true`)

## What was independently re-measured

Every claim below was reproduced by the auditor, not accepted from the lane:

- **Runs.** pytest **127 passed**; adapter `tsc --noEmit` clean; `node --test` **47 passed / 0 failed**; `verify-freezes` ok (10/10 freezes, zero security/V1-isolation findings); census re-run equals the freeze (BTC 35,039 rows; H1 8,759 complete / 0 gaps; H4 2,189 / 0 gaps; SPY 2,943 sessions). The audit made **zero** live API calls.
- **A. No lookahead.** All feature windows strictly trailing; `rv_pctile` ranks against exclusive past; warmup 192 enforced (`vector_at` returns None below it); H4 bucket complete iff exactly 16 aligned 15m bars; prior fields of state *t* come only from the persisted state in force at *t−1*.
- **B/C. Forced choice + code-owned UNKNOWN.** Exactly 4 phase options on both sides (Python and TS); static test proves the built criteria contain no UNKNOWN-equivalent; a fifth label is rejected to SCHEMA_ERROR at ingest (both languages). Every trigger in `safety_persistence_contract.json` maps to a distinct code path in `safety.py`; auditor probed the boundaries (conf 0.50 passes / 0.4999 abstains; margin 0.1999 abstains); thresholds come only from the frozen params.
- **D. Consistency matrix.** Auditor encoded the AMENDED freeze law as an independent truth table and compared against `evaluate_consistency` over all 96 combinations (2×3×4 phases×priors incl. `none` — superset of the mandated 72): **zero mismatches**. The implementation matches the amended (trial-1) law text exactly.
- **E. Digest laws.** Producer digest recomputed for **all 78** cached canary requests: all match; response echo matches 78/78; a random sample of 10 was recomputed on **both** sides (Python and TS) and agrees. Cache key = sha256(model‖state_id‖input_digest‖prompt_digest): trial-1 keys recompute exactly with the live prompt digest (`a5ae1644…`).
- **F. Sequential replay.** Strict order; prior recomputed from the persistence machine after every merged response; one adapter call per state with exactly-one-response-line enforcement; adapter exit ≠ 0 hard-fails; cache-first resume re-validates cached lines against freshly recomputed digests; decision store append-only.
- **G. Fold reconciliation.** Contiguous exec-bar fold partition, hard no-span invariants, and |Σ fold_net − net_pnl| ≤ 1e-9 asserted after every run; all tested.
- **H. Model pin.** `VERIFIED_LIVE jev-1.13.0` (pinned 08:29:44Z, G0 probe recorded); `jev-latest` and missing pin refused (exit 3, tested); response model ≠ pin → SCHEMA_ERROR (tested both sides). All live evidence echoes the pin.
- **I. Cost projection (measured, not estimated).** From 78 live adapter summaries (39 trial-0 + 39 trial-1): per call ≈ **4,070 input / 130.5 output tokens** (trial-1 mean; trial-0 within 1.1%), mean latency ≈ 1,076 ms. Projection: **BTC_H1 8,567** → ≈34.9M in / 1.12M out; **BTC_H4 1,997** → ≈8.1M in / 0.26M out; **SPY_D1 2,751** → ≈11.2M in / 0.36M out. **Total 13,315 calls ≈ 54.2M input / 1.74M output tokens ≈ 4.0 h sequential.**
- **J. No broker/order surface.** Static scans clean (17 files); independent grep clean; adapter's only network surface is the TypeSafe `systemOne` call; `backtest` subcommand is quarantined fail-closed.
- **K. V1 isolation.** V1 paths refused at open time; SPY read from the sha-verified v2 `data_local` copy; salt recompute by hand: V1 `sha256('JRV1'…)[:16]` vs V2 `sha256('JRV2'…)[:16]` (`a3eed5b621f2ac2a`; hand-built state id `e32f0aa80bf5f543`), fixture ids in a separate `JRV2-fixture:` namespace — disjoint by construction and by test.
- **L. Design-trial discipline — HELD.** (1) The live cache's 39 state_ids are all fixture-salt ids; auditor enumerated **11,702** historical state_ids across the three cells: **zero overlap** — no historical state has ever been called; the only non-fixture live touch is the G0 `models.list` probe. (2) All 3 freeze amendments carry old shas that the auditor verified against the actual pre-amendment git blobs — all match. (3) No PnL exists anywhere in runtime. (4) The canary FAIL is recorded honestly and no historical preview was run (no live preview artifacts in any namespace). (5) Revision budget: **1 of 2** used, both trials pre-historical.
- **M. Canary verdict reproduced.** From the trial-1 raw cached responses the auditor regenerated fixtures + seeded perturbations, recomputed digests, and re-derived all 10 acceptance checks: identical to the recorded result — **9 PASS / 1 FAIL**, fail at "ambiguous fixtures ARE code-abstained" (C5 → UPTREND, C7 → DOWNTREND, both `reason: ok`; C6 correctly abstained; perturbations 8/8 × 4 families). The recorded verdict matches the raw evidence.
- **N. Nondeterminism is real.** C7's two cached responses share an identical `request_sha256` yet disagree on structure (RANGE in trial-0 vs TREND in trial-1) — the provider nondeterminism claim is evidence-backed, and the two answers correctly map to different effective labels under the same law.

## Findings

| # | Severity | Finding |
|---|---|---|
| F1 | **MEDIUM** | The trial-1 disclosure clause **"no prompt change" is inaccurate**: the amended consistency law is embedded verbatim in the prompt and hashed into the prompt digest. Proof: identical requests across trials (`request_sha256 49a7da22…`) have different cache keys; trial-1 keys recompute with the current prompt digest, trial-0 keys do not. Not a law breach — the change *is* disclosed revision 1/2, pre-historical, and the prompt-freeze law only engages after the first historical preview — but the STOP-1 report must describe trial-1 as a prompt-identity change. |
| F2 | LOW | Trial-0's aggregated canary result JSON was overwritten by trial-1 at the same path; trial-0 remains reconstructable from its 39 raw cache entries + the first 39 summary lines, but no standalone trial-0 result artifact exists. |
| F3 | LOW | The frozen state_id law has no regime-clock dimension: all 2,189 BTC H4 closes coincide with H1 closes, so H1/H4 states at the same timestamp share a state_id. No contamination path today (per-cell decision stores; input_digest in the adapter cache key), but A7-2 must keep per-cell stores segregated. |
| F4 | LOW | PLAN §1.4's original consistency-law wording no longer matches the operative amended freeze (sanctioned trial-1 change); freeze/code/tests all agree with each other — documentation-level only. |

## Gate note

The canary FAIL (C5/C7 not code-abstained) is an **owner decision at the canary gate**, not an audit item: this audit verifies the verdict is honestly recorded and exactly reproducible. The preview collapse criteria (>90% single label / >80% UNKNOWN) are separate and untested. The audit expresses no opinion on canary GO.

**Verdict: AUTHORIZED_FOR_STOP1_REPORT** — zero unresolved HIGH/CRITICAL; the four findings above carry into the STOP-1 report.
