# S2 A3 — outcome-blind family discovery (data/PIT lane) — working notes

Branch: `orca/stocks-s2-prop-a3`, HEAD at work: `3a00fd7653dd5ff51ca4b9be51b494638bbb6df9`.
Owner: A3. Outcome-blind: no scored PnL/PF/Sharpe/ranking computed; no other
proposal lane's files read. Documents only; no production code changes.

## Deliverables

- `research/proposals/stocks/a3_family1.{json,md}` — `EQ_S2_A3_F1_PIT_RECON_FLOW`
- `research/proposals/stocks/a3_family2.{json,md}` — `EQ_S2_A3_F2_LISTING_AGE`

## How the two families were chosen (A3 lens)

The mandate is diversity through the data/PIT lens: mechanisms whose edge lives
in point-in-time universe construction, survivorship/delisting handling,
ticker-history identity, listing-age effects, or PIT membership reconstitution —
spaces where naive data handling silently fakes the effect. The two picked are
the two priority-adjacent spaces where the A3-owned contracts
(`SecurityMaster`, `MembershipTable`, `build_rebalance_snapshot`,
`evaluate_delisting_retention`, `SealedWindows`, `BarLoader`, `provider.py`
entitlement policy) are not just plumbing but the *load-bearing* ingredient:

1. **F1 PIT reconstitution flow** — only measurable with effective-dated
   membership (`members_as_of` only; structural no-backfill ban) plus PIT
   announcement/effective timestamps. A current-membership backfill cannot even
   express the object. Mechanism: mandate-forced, price-inelastic benchmark
   flows at effective dates (Shleifer 1986; Harris & Gurel 1986; Greenwood 2005;
   Chang-Hong-Liskovich 2015). Counterparty: index-tracking/benchmarked funds.
   Arms: anchor (announced adds/deletes, sector-neutral), neighbour
   (rule-based threshold recon), control (matched no-tracking-AUM index changes —
   severs forced flow, keeps observable/clock identical).
2. **F2 listing-age overpricing** — anchor signal is literally
   `decision_date - listed_date` off the PIT security master, and the family is
   the canonical victim of survivorship + delisting bias (Shumway 1997;
   Shumway & Warther 1999), which the A3 floors (`evaluate_delisting_retention`)
   forbid. Mechanism: divergence-of-opinion overpricing under short-sale
   constraints with thin locked float (Miller 1977; Ritter 1991; Loughran &
   Ritter 1995; Nagel 2005; Kumar 2009; Ofek & Richardson 2003). Arms: anchor
   (monthly sector-neutral young<=12m vs seasoned>=5y), neighbour
   (constraint-gradient young short leg via PIT borrow fee), control
   (aged-entry cohort clock shift — same securities re-entered only after the
   age threshold; expressible today via `EligibilityInput.history_days`).

Distinctness between the two: different observables (membership events vs
listing age), counterparties (index funds vs constrained optimists), clocks
(event-driven announcement->effective vs monthly next-open roll), causal
controls (no-flow index vs aged-entry shift), and literature bases. Both differ
from the rejected crypto families on observable AND counterparty AND clock AND
causal control (attested per-family in the JSON `ineligibility_attestation`).

## Trial budget

Each family: exactly 3 computed cells (anchor, neighbour, negative control);
no grids; all window/threshold constants declared ex ante and frozen.

## Data readiness (honest)

No provider entitlement exists (`NO_ENTITLEMENT_FAIL_CLOSED`). Both proposals
are implementable against the synthetic-fixture factory now; real-data readiness
is BLOCKED pending owner-authorized entitlement covering
`REQUIRED_LICENSE_SCOPE` (PIT_SECURITY_MASTER, DELISTINGS, CORPORATE_ACTIONS,
HISTORY_WITH_ADJUSTMENTS). Fields specifically pending entitlement are marked
`UNAVAILABLE_PENDING_ENTITLEMENT` in each JSON.

## Literature honesty

All citations marked `MODEL_INTERNAL_UNVERIFIED` at bibliographic-detail level:
authors/year/journal stated only where internally confident; no DOIs, no
quotes; retrieval marking present in both JSONs.

## Factory surface consulted (read-only)

`research/assets/stocks/universe.py`, `provider.py`, `loader.py`,
`corporate_actions.py`, `execution.py`;
`research/assets/common/trial_identity.py`, `contracts.py`, `calendar.py`;
`PLAN_stocks.md` §7 (data contract, floors) and §9 (proposal contract,
priority spaces, ineligibility).
