# CYCLE VERDICT — EURUSD-RANGEEXP-SCORED-V1 (TERMINAL, 2026-09-24)

- Branch: `orca/eurusd-rangeexp-scored-v1-integration` @ terminal anchor;
  plan `plans/PLAN_eurusd_rangeexp_scored_v1.md`; owner option "1" opened
  the cycle; owner typed the verbatim `GO EURUSD RANGEEXP SCORED V1` at this
  gate (consumed; machine-recorded in registry phase) after A7 round-2
  AUTHORIZED.

## VERDICT: `SCORED_RECONCILED_NO_DRIFT_FLAG`

Exactly one enum per plan §3. S1 reproduction gate PASS (12/12 byte-exact
vs V2's committed references) and the mechanical S6 drift rule returned
NO_DRIFT_FLAG on all four (candidate × window) books.

## Cell results (budget 6/6 consumed, each executed once)

**S1 reproduction gate — PASS.** All 12 metric blocks (2 candidates ×
dev/holdout × k∈{1.0,1.5,2.0}) reconcile with
`EURUSD-OPEN-SEARCH-V2/outcomes/{campaign_dev_v2.jsonl,holdout_check_v2.json}`
on all five metrics (trades, net_pips, pf, hit, maxdd on real equity).

**S2–S5 leg decompositions (k=1.0):**

| book | long net | short net | short share | long PF | short PF |
|---|---|---|---|---|---|
| C3 DEV | +3,783.0 | +3,364.1 | 47.1% | 1.786 | 1.674 |
| C3 HOLDOUT | +154.6 | +119.4 | 43.6% | 1.395 | 1.241 |
| C4 DEV | +3,423.1 | +3,138.0 | 47.8% | 1.700 | 1.603 |
| C4 HOLDOUT | +125.8 | +91.3 | 42.1% | 1.306 | 1.181 |

**S6 drift flags: NO_DRIFT_FLAG ×4.** Short legs are positive but below the
50% share threshold (margin −209.5/−17.6/−142.6/−17.3 pips). Substantively:
**the long leg was profitable even inside the falling 2026-H1 holdout**
(+154.6 / +125.8 pips) — the mechanism is two-sided, not short-beta.

Baselines (k=1.0): DEV {CASH 0, LONG_ALWAYS −1,743.2, SHORT_ALWAYS +811.3,
RANDOM −6,199.7}; HOLDOUT {CASH 0, LONG_ALWAYS −395.4, SHORT_ALWAYS +314.0,
RANDOM −267.7}. The candidates out-earn every naive direction baseline on
dev by an order of magnitude.

## Disclosures

- RANDOM_MATCHED holdout here is −267.7 vs V2's −353.5: one
  `default_rng(20260923)` instance is shared across DEV (27,748 draws) then
  HOLDOUT (continuation draws); a fresh-generator holdout draw reproduces
  V2's −353.5 (A7 counterfactual). Both are valid cost-drag realizations;
  no gate depends on the choice.
- S6 margins on the holdout books are modest (−17.6/−17.3 pips below the
  50% line): the **short-beta control remains MANDATORY in the paper-forward
  successor** — this cycle strengthens but does not close that question.
- This cycle changes nothing about any strategy's status: FX2-RANGEEXP
  remains `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION` (V2 verdict
  untouched); what is new is that its edge is now SCORED, reconciled, and
  measured two-sided in the program ledger.

## Governance state

- A7 prelaunch round-1 REFUSED (F1 unregistered + F2–F5 cell gaps) →
  remediated (registry row, five-metric S1 gate, per-leg PF, full baselines,
  plan-literal S6) → round-2 AUTHORIZED (key 1). Owner GO consumed (key 2).
- A7 terminal: **CONFIRM_SCORED_RECONCILED_NO_DRIFT_FLAG**, 0 blocking
  (independent recompute of all books + rng counterfactual) —
  `audits/a7_terminal_verdict.json`.
- S1 counted as reproduction (+0 trials); S2–S6 are new scored observables
  (+5). S1 SEALED_UNTOUCHED; no orders/paper/live; engine sha `cc868402…`
  unchanged end-to-end.
