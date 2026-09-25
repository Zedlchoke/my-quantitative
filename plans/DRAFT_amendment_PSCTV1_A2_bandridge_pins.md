# DRAFT AMENDMENT A2 — PROSPECTIVE-SHADOW-V1: BTC4H-BANDRIDGE pre-fill pins

> **Status: DRAFT_FOR_OWNER_GO — NOT REGISTERED, NOT EXECUTED.** Owner
> decision D3 (2026-09-25): approve the law-pinning NOW, before the first
> fill. This draft carries that decision to its GO gate. Parent laws:
> plans/PLAN_prospective_shadow_v1.md + amendment A1 (sleeve 4 mount) +
> plans/PLAN_economic_robustness_program_v1.md §4.3 (C-BR-1..4).

## 0. Owner decision encoded (verbatim intent, 2026-09-25)

- **Sizing B** (cost-aware, realized fraction ≈ 0.99946).
- **Fill law A** — fill documented at the FIRST COMPLETED 15m bar after
  the H4 decision.
- **Cost identity: 6 bps/side STAYS in the identity manifest.** The
  executor must be made to charge exactly 6 bps/side and be HASH-MATCHED
  to the identity before any fill may carry evaluability. Two cost laws
  are forbidden from coexisting: a fill produced while executor ≠
  identity-cost is labelled `UNPINNED_COST_LAW — NOT PROMOTABLE` and can
  never be promoted, only disclosed.

## 1. Pins (freeze before the first fillable decision produces a fill)

| Pin | Value | Freezes |
|---|---|---|
| P-1 sizing | B (cost-aware; realized ≈ 0.99946) | replaces the open A/B/C packet; packet owner-field closed with digest |
| P-2 fill law | A: first completed 15m bar after H4 decision close | deterministic, PIT-safe, matches sleeve-2 precedent law |
| P-3 cost law | identity 6 bps/side; executor re-pinned to 6 bps/side **for the BANDRIDGE family only — via a per-family cost override, NOT by changing any module-global constant** (verified in production bytes: `FEE_RATE_CURRENT = 0.0005` at `e/shadow_worker.py` L180 is module-global and feeds `cost_books_for()` for ALL FOUR families — flipping it would silently move the live cost law of XSECT (52 booked fills) and BASISLV mid-run, which is OUT OF SCOPE of D3 and forbidden by PSV1 §6); `cost_regime_digest` override row created (dated hash boundary) scoped to BANDRIDGE records only; the current shared digest `130d2e7e…` stops applying to NEW BANDRIDGE records from the boundary timestamp (other families' rows untouched) | measured funding per settlement unchanged |
| P-4 executor hash match | identity manifest records the BANDRIDGE executor cost-code sha256 (the per-family override path); mismatch = automatic `UNPINNED_COST_LAW` labelling (fail-closed, no silent average) | reconciliation proof artifact before first evaluability fill |

Sequence law: P-3/P-4 land TOGETHER in one change-set. **The dated
cost-regime boundary timestamp is `T_act` — the ACTIVATION moment when the
per-family override is actually live on the worker — NOT the GO typing
moment.** Backfill is forbidden. Any BANDRIDGE fill recorded before
`T_act` (under the old shared digest `130d2e7e…`) is labelled
`TRANSITION_OLD_LAW → UNPINNED_COST_LAW — NOT PROMOTABLE` permanently;
it is disclosed evidence, never promoted, never backfilled.

### 1b. Lifecycle & authority phases (binding — resolves GO-vs-tests ordering)

```text
Phase G  GO typed at this amendment's gate
         → authorizes ONE thing only: the implementation cycle may WRITE
           CODE in its worktree. NO worker change. A typed GO is NEVER
           evidence that any worker changed.
Phase I  Implementation: bounded change-set written; zero worker impact;
         production executor untouched until Phase A.
Phase V  Verification: ALL fixtures (a)–(e) below pass + A7 prelaunch arc
         AUTHORIZED. Tests gate ACTIVATION, not the GO — the GO does not
         skip, pre-satisfy or substitute for this phase.
Phase A  Activation: deploy/restart per the cycle's own procedure; the
         ACTIVATION MOMENT T_act is recorded to the second (UTC) in an
         activation artifact (timestamp + cost-override digest + executor
         hash-match proof). T_act — not the GO — is the cost-regime
         boundary and the first moment any fill can carry evaluability.
```

Transition window (G → A): every decision/fill occurs under the OLD law
and is recorded as such (`TRANSITION_OLD_LAW`); no backfill, no re-costing,
no deletion.

## 2. Disclosure carried forward (unchanged by this amendment)

S0 characterization: F3 fold share ≈ 65% (single-regime money). At any
future adjudication, the 0.50 concentration law applies without waiver
(umbrella §4.3 C-BR-4). CONDITIONAL_KEEP never waives gates.

## 3. Implementation boundary

- Home: the sleeve's computation home under the
  `btc-h4-band-risk-v1` worktree shadow_bandridge namespace + the
  PSV1 **production executor files** (`e/shadow_worker.py`,
  `cost_books_for()` and the per-family cost-book construction) and the
  PSV1 ledger adapter (documented cross-worktree mount, P-13 convention).
- One bounded change-set: sizing constant → B; fill recorder → law A;
  **per-family BANDRIDGE cost override → 6 bps/side** (other families'
  cost books byte-identical — proven by regression fixture (e));
  cost-regime boundary row + digest; hash-match assertion.
  Strategy/schedule/risk caps byte-untouched.
- Tests before ACTIVATION (Phase V — none may be waived by the GO): (a)
  synthetic H4 sequence with a band-ON
  gate produces a fill at first completed 15m bar with exactly 6 bps/side
  (hand-computed fixture); (b) hash-mismatch fixture labels
  UNPINNED_COST_LAW fail-closed; (c) pre-boundary BANDRIDGE rows parse
  unchanged AND non-BANDRIDGE families' cost books reproduce identically
  (regression: XSECT/BASISLV/ILLIQ cost constants untouched); (d) no-diff
  proof on the frozen band/bridge/Donchian logic; (e) cost-book
  construction fixture proving the override is keyed to the BANDRIDGE
  family id only.
- Worker restart belongs to Phase A only, per the implementation cycle's
  own procedure, with restart-idempotence proof (forward-only law; no
  backfill of the 56 fail-closed rows). The GO phrase alone never
  restarts anything.

## 4. GO gate

`GO PSCTV1 AMENDMENT A2 BANDRIDGE PINS` (draft phrase; exact, fresh, at
this amendment's own gate after independent review; P-8). Per §1b: this
GO authorizes code-writing in the implementation cycle ONLY; activation
(`T_act`) is a later, separately-recorded event gated on Phase V tests +
A7; the gap between them is `TRANSITION_OLD_LAW` territory.

## 5. Non-objectives

No change to band/bridge/Donchian parameters, H4 clock, fraction beyond
P-1, risk caps, or the forward-only law; no promotion claim; no orders;
no S1; no scored cells.
