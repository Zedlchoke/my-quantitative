# S3 A7 — Structural-orthogonality matrix and rescue-veto record (all six proposals)

Numeric prewindow correlation is **NOT_IMPLEMENTABLE_NO_REAL_DATA** (no real
price history exists in this sprint; synthetic fixtures only; PLAN_stocks sets
no numeric rho threshold). Orthogonality below is structural only:
observable / clock / counterparty / causal control.

## 1. Full 6x6 structural distinctions

Legend — Obs: observable; Clk: clock; Ctp: counterparty; Ctrl: causal control.
A pair is FULLY DISTINGUISHABLE when all four axes differ; PARTIAL when one or
more axes genuinely coincide.

| pair | axes differing | assessment |
|---|---|---|
| A3F1 x A3F2 | Obs (membership announcements vs listed_age), Ctp (index funds vs constrained optimists), Clk (event-anchored multi-week vs monthly roll), Ctrl (no-flow index vs aged-entry cohort) | FULLY DISTINGUISHABLE |
| A3F1 x A4F1 | Obs (membership events vs earnings SUE), Ctp (index funds vs attention-constrained traders), Clk (announcement schedule vs release-anchored open), Ctrl (no-flow index vs sign-flip) | FULLY DISTINGUISHABLE |
| A3F1 x A4F2 | Obs (membership events vs session-decomposed capture), Ctp (index funds vs auction rebalancers), Clk (multi-week event vs daily double-auction), Ctrl | FULLY DISTINGUISHABLE |
| A3F1 x A5F1 | Obs (membership events vs lending fee/utilization), Ctp (index funds vs lending desks/sentiment longs), Clk (announcement schedule vs month-end), Ctrl (no-flow index vs GC placebo) | FULLY DISTINGUISHABLE. Soft overlap: an index deletion is often borrow-constrained, so the two short legs can share names episodically; mechanism, clock and control remain distinct |
| A3F1 x A5F2 | Obs, Ctp, Clk, Ctrl all differ | FULLY DISTINGUISHABLE |
| A3F2 x A4F1 | Obs (listed_age vs SUE), Ctp, Clk (monthly calendar roll vs event-anchored), Ctrl | FULLY DISTINGUISHABLE |
| A3F2 x A4F2 | Obs, Ctp, Clk (monthly vs daily), Ctrl | FULLY DISTINGUISHABLE |
| A3F2 x A5F1 | Obs (listed_age vs borrow fee) — **except A3F2's NEIGHBOUR arm, whose short leg is borrow-fee-selected**; Ctp partially shared (short-sale-constraint overpricing); Clk both monthly; Ctrl differ | PARTIAL via one arm: A3F2-neighbour <-> A5F1-anchor share the fee-scarcity observable and a monthly cadence. Family-level anchors remain distinct. If both families are selected, A1 should record this overlap in the freeze |
| A3F2 x A5F2 | Obs, Ctp, Clk, Ctrl differ | FULLY DISTINGUISHABLE |
| A4F1 x A4F2 | Obs (accounting surprise vs return decomposition), Ctp, Clk (event-anchored vs calendar-anchored), Ctrl (sign-flip vs interval swap); information sets declared disjoint (A4F2 uses no earnings data) | FULLY DISTINGUISHABLE |
| A4F1 x A5F1 | Obs, Ctp, Clk (release-anchored vs month-end), Ctrl | FULLY DISTINGUISHABLE. Soft overlap: SUE quintile tails and fee-constrained tails both tilt toward small/glamour names |
| A4F1 x A5F2 | Obs, Ctp, Clk, Ctrl differ; A5F2 explicitly excludes earnings windows, removing event coincidence | FULLY DISTINGUISHABLE |
| A4F2 x A5F1 | Obs, Ctp, Clk (daily vs monthly), Ctrl; A4F2 has no short leg at all | FULLY DISTINGUISHABLE |
| A4F2 x A5F2 | Obs, Ctp, Clk (daily overnight vs ~6–7-session event), Ctrl | FULLY DISTINGUISHABLE. Soft overlap: both buy named books at fixed events with market exposure (A4F2 by design, A5F2 unhedged core); beta context differs |
| A5F1 x A5F2 | Obs (lending fee vs dividend/tax calendar), Ctp (lending desks vs taxable sellers), Clk (monthly vs ex-date event), Ctrl (GC placebo vs qualified placebo) | FULLY DISTINGUISHABLE at family level |

No pair of ANCHOR mechanisms shares all four axes with any other; the only
cross-family structural coincidence of substance is A3F2's neighbour arm vs
A5F1's anchor (documented above).

## 2. Top-ranked candidates (expected selection)

`EQ_S2_A3_F1_PIT_RECON_FLOW` vs `A5-S2-F1-LENDING-CONSTRAINT-PREMIUM`:

| axis | A3F1 | A5F1 |
|---|---|---|
| Observable | PIT index announcement/effective membership events | PIT securities-lending fee and utilization |
| Clock | announcement -> next-close entry -> effective+20 sessions (event schedule) | month-end formation, ~21-session holds, daily fee accrual |
| Counterparty | tracking-mandate index funds (inelastic forced flow) | securities-lending desks and sentiment longs (constraint pricing) |
| Causal control | membership changes of a matched no-tracking-AUM index | fee-rank placebo inside general-collateral tercile |

FULLY DISTINGUISHABLE on all four axes. Residual overlap: short legs can
co-hold individual names episodically (deletions are often special); clocks,
observables and controls do not coincide, so simultaneous selection does not
create a hidden duplicate bet at the mechanism level.

## 3. Rescue-veto record vs rejected crypto families

Rejected inventory (evidence): M01 aggressor-flow absorption
`M01_FAMILY_REJECT` (root PLAN.md §1: anchor PF 2.42e-08, "placebo
approximately equals mechanism; no incremental flow information"; forbidden:
"M01-adjacent aggressor-flow proposal unless the novelty audit proves a
different observable, counterparty, holding clock and causal control");
funding-carry lineages (MAP.md: V6 CARRY-1D mechanism_failure, CARRY-3D
edge_too_weak, CARRY-7D concentration reject); weekly reversal (REVERSE-3D
failed as designed; `weekly_reversal.py` lineage abandoned across V1–V11).

| proposal | vs M01 (flow absorption) | vs funding-carry | vs weekly reversal | veto? |
|---|---|---|---|---|
| A3F1 recon flow | different Obs/Ctp/Clk/Ctrl (mandate flow != aggressor flow; the causal control removes tracking money, not flow information) | no funding term | event-driven, not periodic | PASS |
| A3F2 listing age | different Obs/Ctp/Clk/Ctrl | borrow fee is a cost (anchor), constraint gradient (neighbour) — never a carry signal | not return-conditioned | PASS |
| A4F1 PEAD | different Obs (accounting surprise)/Ctp/Clk/Ctrl | no funding observable | weekly cadence is cohort aggregation only | PASS |
| A4F2 overnight | no order-flow observable | no funding cashflow; US cash equities | daily session clock, no reversal score | PASS |
| A5F1 lending premium | different on all four axes | fee is paid, not collected; equity lending, not perp funding; GC placebo has no crypto analog | monthly, not reversal | PASS |
| A5F2 ex-date capture | different on all four axes | carry-shaped but different Obs/Ctp/Clk/Ctrl on every axis (see audit_a5_family2 §1) | ex-date keyed, not reversal | PASS |

## 4. Clocks, counterparties, controls at a glance

| family | clock | counterparty | control that severs |
|---|---|---|---|
| A3F1 | announcement->effective schedule, +20 sessions | index funds (tracking mandate) | no-tracking-AUM index (removes forced money, keeps observable) |
| A3F2 | monthly next-open, 1-month roll | constrained optimists / float distributors | aged-entry cohort clock (removes youngness, keeps names) |
| A4F1 | release-anchored next open, 60-session cohorts | attention-constrained news traders | sign-flipped SUE (removes news direction; see O1 limit) |
| A4F2 | daily close->open double auction | auction-concentrated rebalancers | intraday leg of same book (removes interval, keeps names) |
| A5F1 | month-end, ~21 sessions | lending desks + sentiment longs | GC-tercile placebo (removes constraint, keeps machinery) |
| A5F2 | T−5 -> ex-date -> T+1 event | taxable cum-date sellers, dealers | qualified low-yield placebo (removes tax penalty, keeps clock) |
