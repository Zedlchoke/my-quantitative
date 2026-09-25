# DRAFT AMENDMENT A3 — PROSPECTIVE-SHADOW-V1: XSECT-FUND-CARRY-7D identity retirement

> **Status: DRAFT_FOR_OWNER_GO — NOT REGISTERED, NOT EXECUTED.** Owner
> decision D4 (2026-09-25): approve PLANNING the retirement; the worker is
> NOT stopped by the decision itself — the stop-open law takes effect only
> at the recorded ACTIVATION moment `T_ret` (Phase A, §1 lifecycle), not at
> the GO. Parent laws: plans/PLAN_prospective_shadow_
> v1.md §3.3/§14 + plans/PLAN_economic_robustness_program_v1.md §4.5
> (C-XS-1..3).

## 0. Measured basis (2026-09-25 bytes; explorer report authority)

11 daily decisions, 52 fills, booked −349.85 USDT (fee 286.43 + slip 68.02
vs funding +4.60 → cost:carry ≈ 77:1); turnover ~0.62×/day; cost run-rate
~11%/yr vs funding capture ~1.7%/yr. Historical label `CANDIDATE_FAIL`
(top-fold 51.66%) unchanged and pinned. The sleeve is measuring cost, not
edge.

## 1. Retirement law (takes effect at ACTIVATION, not at the GO typing)

**Lifecycle (binding).** Phase G: the GO phrase authorizes ONE thing — the
implementation cycle may write the stop-open change-set. Phase I: code
written, worker untouched. Phase V: all fixtures pass + A7 prelaunch
AUTHORIZED. Phase A: **activation** — the stop-open flag is actually live
on the worker, and THAT moment (recorded to the second, UTC, in an
activation artifact) is `T_ret`. The GO typing time is NOT `T_ret`; a
typed GO is never evidence the worker changed.

- **R-1 Stop-open law (from `T_ret`).** From `T_ret` the sleeve opens NO
  new virtual position and rebalances nothing; **existing virtual holdings
  MUST still be closable** — they run to their natural frozen-law expiry
  (24h rebalance law → book to flat at the next daily boundary per the
  frozen exit policy; force-flat at fold boundary law). Closing fills are
  lawful and REQUIRED; only opening is forbidden.
- **R-1b Transition window (GO → `T_ret`).** Decisions and fills
  continuing under the old law in this window are recorded
  `TRANSITION_OLD_LAW` — honestly counted, never backfilled, never
  re-labelled; the retirement does not retroactively start at the GO.
- **R-2 Terminal row.** Emitted ONLY when the sleeve is measured ACTUALLY
  FLAT (flat-condition checked at a decision boundary — a state condition,
  never a timestamp assumption): append one terminal record
  `IDENTITY_RETIRED_COST_DOMINATED` with full decomposition (price/fee/
  slip/funding/equity), decision count, blocked count, `T_ret`, and the
  pinned historical verdict label.
- **R-3 Evidence preservation.** Ledger, manifests, dashboards history:
  append-only, byte-untouched, never rewritten. Dashboard card moves to a
  retired-history view (display change only).
- **R-4 Successor law (binding on any future carry proposal).** New
  strategy ID required; no inheritance of this sleeve's prospective
  history; rebalance only when expected carry over the intended holding
  period ≥ full round-trip stress cost (measured anchors: two-leg taker RT
  ≈ 20–25 bps; in-downtrend funding ≈ 1.11 bps/day → breakeven ≈ 18–23
  days, 27–34 at 1.5× stress → ≥3–5 week low-turnover holds; maker-only
  execution must be measured, not assumed). Umbrella §4.5 C-XS-2 applies
  verbatim.

## 2. What this amendment does NOT do

- Does not stop/restart the worker process (owner D4 explicit); the
  sleeve's scheduler keeps emitting `NO_NEW_POSITIONS_RETired` decision
  rows after `T_ret` (operational continuity, zero exposure).
- Does not touch the other three sleeves (ILLIQ/BASISLV/BANDRIDGE) or any
  ledger bytes.
- Does not delete or relabel any historical verdict; `CANDIDATE_FAIL`
  stays the label of record.

## 3. Implementation boundary

- Home: PSV1 worktree sleeve-3 adapter + ledger writer; one bounded
  change-set (stop-open flag with timestamp + terminal-row emitter +
  retired dashboard state). Frozen family logic byte-untouched.
- Tests before ACTIVATION (Phase V — the GO cannot waive them), with the
  two laws tested SEPARATELY:
  (a1) **no-new-opens fixture** — post-`T_ret` decision rows emit
  NO_NEW_POSITIONS_RETired with ZERO opening fills;
  (a2) **closing-permitted fixture** — pre-`T_ret` holdings still produce
  their R-1 book-to-flat closing fills (closing ≠ opening; closings are
  asserted PRESENT, not absent);
  (b) terminal-row fixture: emission fires ONLY on the measured-flat
  condition (state check at a decision boundary), with hand-computed
  decomposition;
  (c) restart-idempotence (no duplicate event_ids);
  (d) pre-`T_ret` rows parse unchanged.
- Terminal-row equity MUST name its basis (decision-row ledger basis vs
  valuation-mark basis — e.g. 99,948 ledger vs 99,094 mark class gap;
  umbrella §4.7 vocabulary).
- Worker restart belongs to Phase A only (per the implementation cycle's
  own procedure); the GO phrase alone restarts nothing.

## 4. GO gate

`GO PSCTV1 AMENDMENT A3 XSECT RETIRE` (draft phrase; exact, fresh, at this
amendment's own gate after independent review; P-8). Per §1 lifecycle:
this GO authorizes code-writing ONLY; `T_ret` is the later, separately
recorded ACTIVATION moment (Phase A artifact), and the window between is
`TRANSITION_OLD_LAW`.

## 5. Non-objectives

No ledger rewrite; no other sleeve touched; no scored cells; no orders;
no S1; no promotion or demotion of any historical verdict.
