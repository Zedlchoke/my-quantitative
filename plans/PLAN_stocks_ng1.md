# PLAN STOCKS-NG1 — next-generation stocks cycle on platform v3

> Status: `PLANNED_NOT_STARTED` (registered 2026-09-11).
>
> Generation note: first stocks cycle on the research platform v3 data
> plane; `ng1` generation opened by the owner's standing directive of
> 2026-09-11. A correct `STOCKS_NG1_REJECT_ALL` is a successful research
> run.

## 0. Owner directive and authority

Owner instruction, verbatim (2026-09-11): identical standing directive as
`plans/PLAN_crypto_ng1.md` §0 (open crypto_ng1/forex_ng1/stocks_ng1 on the
new system + old lessons; full Lead autonomy; one-shot run; terminal
output).

Standing GO delegation (P-8 adaptation, recorded here and in the registry):
at this cycle's own prelaunch gate, AFTER independent A7 publishes
`STOCKS_NG1_S0_LAUNCH_AUTHORIZED` with zero unresolved HIGH/CRITICAL, the
Lead (A1) types the GO decision under the owner's standing delegation.
Scope excludes S1 opening, push/merge to `main`, purchases, NEW EODHD
entitlements beyond the already-used field families, keyed signups,
credentials, live/paper/testnet. A7 REFUSED => no GO.

GO phrase (typed only at this cycle's own gate):

```text
GO STOCKS NG1 SCORED EXECUTION
```

## 1. Prior verdicts and forbidden ancestry

- STOCKS-V11 `STOCKS_FREE_V11_REJECT_ALL_CONFIRMED` (3/6): cadence-latency
  falsified-by-control (shuffled-chain reproduces alpha, cluster #13);
  filing-event lane dead at D2 vs momentum_63s.
- STOCKS-FREE-V12 `…BLOCKED_DATA_OR_SELECTION` (0/6): every proposal died
  MEASURED at D2 — axis-1 chain-structure rho-contaminated by cluster #13;
  axis-2 death-event self-subsumption 0.9923; H2 control unrunnable.
- STOCKS-FREE-V13 `STOCKS_FREE_V13_REJECT_ALL` (3/6, mechanical, label
  adjudicated by A7 F-A7T-1): dividend-policy transition scored and
  mechanically rejected (informative near-miss, NOT rescuable); insider
  net-direction concentration and routine-vs-opportunistic (CMP-style)
  flow INELIGIBLE_NOVELTY vs vol_level; macro-axis forms dead (DGS10
  exposure-form 0.9059; wc_stock_intensity 0.2667); splits 0/15 vetoes
  fail-closed.
- THE 15-ENTRY VETO SET (14-entry cross-asset set + A6-P1) is the binding
  ancestry gate for every proposal; enumerated by name in
  `stocks_free_v13_run/audits/d2_v13_novelty_feasibility.json` L1194-1213.
- Re-entry law (V13 terminal): requires MATERIALLY NEW mechanism — new
  observable on the Form-4/EODHD substrate that the veto set has not
  measured, with new causal control.
- Canonical inventory: `research/wayfinder/FAMILY_FAILURES.jsonl` +
  `research/wayfinder/HYPOTHESIS_LEDGER.md`, pooled with H0 hygiene rows.

## 2. Objective and terminal outcomes (frozen before any proposal)

Objective: test whether DECLARED-INTENT and REVISION-STRUCTURE observables
on the frozen Form-4 substrate — information fields never measured by the
dead families — carry after-cost expectancy in bookable post-filing
windows.

Terminal outcomes (preregistered, negative-first):

```text
STOCKS_NG1_REJECT_ALL
STOCKS_NG1_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
STOCKS_NG1_BLOCKED_DATA_OR_SELECTION
STOCKS_NG1_BLOCKED_PRELAUNCH
STOCKS_NG1_INCOMPLETE_NOT_PROMOTABLE
```

`BLOCKED_DATA is live and cheap`: if the S1 CADS re-pin or plane adoption
fails verification, or the new observables are ABSENT/under-covered in the
pinned substrate (schema census below frozen floors), the cycle dies in
P0/P2 before any proposal is requested.

## 3. Data authority and platform v3 adoption (P0)

Frozen consumption set (exactly the GRANTED S1 series, nothing else):

- `form4-xml-substrate`: 345,150 XML docs, substrate manifest digest
  `5d351623…` (the `78c4fb1a` vintage is pre-F-1 evidence, not current).
- `form4-stream`: 546,039 rows re-pinned `6ac2cd5b…`.
- `eodhd-corp-actions`: EODHD div 2,168 + splits 2,168 files.
- Price/return authority: the EODHD price family already used by V13 under
  the owner's existing entitlement — NO new EODHD field family is consumed
  by this cycle without a separate owner grant (any proposal needing one
  dies at P2 as BLOCKED_DATA, honestly).
- Clock/PIT: filing accession timestamps via the V13-proven EDGAR
  multi-vintage machinery (declared UA `Research my-quantitative@example.com`);
  `available_time` = accession timestamp of the correct vintage (P-13
  archive discipline; inherited pins re-verified at P0).

Observable censuses (P0/P2, fail-closed, from the PINNED substrate only —
no re-download):

- 10b5-1 declared-plan flag: presence in the Form-4 XML schema of the
  pinned vintage + coverage count post-2023 (compliance window) + dead-name
  canaries (P-7 channel law). Below frozen floor => lane A4 dies P2.
- Amendment/late-arrival structure: `4/A` amendment documents and
  original-vs-amendment accession lags inside the pinned substrate; below
  frozen floor => lane A5 dies P2.

Adoption law: one per-asset adoption commit; consumption ONLY via
`consume_via_plane`; bounded shadow-parity pilot (plane-read vs
V13-direct-read digest equality on a sampled entity window) must PASS
before downstream lanes consume.

## 4. Phases and gates

```text
P0  data authority + platform adoption (S1 re-pin verify, UA machinery
    re-proof, shadow parity pilot)                    -> P0_GATE
P1  kernel/accounting inheritance (V13 dividend-transition machinery
    pattern; dual-book; cost-once)                    -> P1_GATE
P2  observable censuses + feasibility (Q-6 recent-window bookable
    windows; dead-share cohort; decision floors)      -> P2_GATE
D1  blind proposal lanes (A4, A5) from one wave SHA
D2  novelty + feasibility MEASURED; code AND representation committed
    before any number is cited (P-12)
S   selection freeze (rubric §6 frozen BEFORE D1 dispatch)
I   implementation lanes (only if selection non-empty)
Z   exact-arm sanitized dry-run
A7  independent prelaunch audit
GO  Lead types GO under owner standing delegation
E   scored cells under machine-wide heavy lock (budget 6)
R   detached-twin reproduction
T   terminal A7 + two-half close
```

## 5. Cost, kernel and clock identity

- Clock: daily close decision grid on EODHD prices; post-filing windows
  bookable per V13 census (1960 entities / 27,454 pairs / dead-share
  0.6218 — re-measured at P2 on the current substrate).
- Costs: measured commissions+spread at stress tier; delisted/dead-share
  handling explicit; cost once per fill.
- Kernel: V13 exposure machinery pattern inherited with compatibility
  tests; diagnostics + prospective DSR (P-11); PBO fail-closed when
  cells < 8.

## 6. Proposal lanes (blind) and frozen selection rubric

Lane A4 — declared-plan disposition structure: the 10b5-1 plan flag is a
DECLARED intent field (materially different information source from the
dead CMP-style INFERRED routine/opportunistic classification). Mechanism
must name who is forced/late; mandatory controls: sham-insider (V13-built),
filing-arrival clock shadow, vol_level veto check, one falsification rule.

Lane A5 — amendment/revision structure: amendment-revealed corrections and
original-vs-amendment arrival lags as observables (no dead family measured
amendments). Mandatory controls: same-baseline sham amendments (matched
cohort), clock-only shadow, vol_level check, falsification rule.

Frozen rubric (before D1 returns; no threshold moves after any scored
number is seen):

1. Mechanism with forced/late participant; pass/fail.
2. Ancestry: pooled |rho| <= 0.20 vs the 15-entry veto set + full
   inventory (H0-augmented); margin recorded (P-2).
3. Feasibility without PnL: bookable-window decision count vs frozen
   floor on the RECENT window (Q-6); turnover/cost ceiling kill before
   selection.
4. Controls runnable on the frozen representation; invalid-null
   distinction (Q-11).
5. Max 2 families x 3 arms = 6 cells; budget 6; pairwise distinct
   arm_config_digest.
6. Ranking by preregistered evidence strength only; smoke kills +
   discloses, never selects (P-15).

## 7. Dry-run, prelaunch, GO, scored execution, reproduction

Identical structure to `plans/PLAN_crypto_ng1.md` §7 with
`STOCKS_NG1_S0_LAUNCH_AUTHORIZED` as the A7 verdict key; heavy lock
serialized machine-wide across the ng1 generation; reproduction detached
twin; ALL_MATCH proves self-consistency only (P-4).

## 8. Orchestration and evidence channel

Same law as `plans/PLAN_crypto_ng1.md` §8 with handoffs at
`research/control/STOCKS-NG1/orchestration/handoffs/` inside this cycle's
worktree; single-cycle MCP store untouched; Flash pin disclosed (35ce190).

## 9. Hard boundaries

Same as `plans/PLAN_crypto_ng1.md` §9. Additionally: no new EODHD field
family without a separate owner grant; amendment observables come from the
pinned substrate + provenance machinery only.
