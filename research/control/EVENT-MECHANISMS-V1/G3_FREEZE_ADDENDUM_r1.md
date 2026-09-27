# G3 FREEZE ADDENDUM r1 — EVENT-MECHANISMS-V1 (2026-09-27)

Remediation of A7 PLAN_REVIEW finding F-2 (MEDIUM): preregister numeric
bands for the two falsifiers that were prose-banded in `G3_FREEZE.md`.
Landed BEFORE any G4 lane dispatch; nothing else changes. Band conventions
reuse repo precedents — no new tuning surface; both bands are fixed here
a priori, before any outcome exists on these planes.

## Band 1 — date-only control kill (shared battery control 1)

For each identity, pooled across folds at ×1.0 cost:

```
identity DIES if  net_expectancy(date-only control)
                  >= 0.50 × net_expectancy(anchor)
```

- 0.50 is the ILLIQ-REG-V1 improvement-bar convention (repo precedent:
  38.6% < 50% = FAIL there).
- If the anchor's net expectancy is ≤ 0, the identity is already dead by
  the PF/fold bars; Band 1 only adjudicates the redundant-clock question
  for positive anchors.
- Margin-to-fail reported (Q-12): the ratio itself, e.g. "control/anchor =
  0.47, bar 0.50, margin −0.03" (thin bands are labeled thin).

## Band 2 — strata-spread falsifier (EMV1-A1 §falsifiers)

Per-event GROSS expectancy spread between strata (pooled, ×1.0 cost law
inputs, before costs):

```
identity DIES if  ( E[unmonitored S1∪S3∪S4] − E[monitored S2] )
                  <=  round-trip cost at ×2.0 stress
```

- "≈ 0 after costs" is hereby operationalized: a spread that does not
  clear even the doubled round-trip band is zero for all decision purposes.
- The cost figure is read from the frozen STOCKS-AMIHUD-RETEST-V1 band
  contract (Q-2 conditional open band × L-SAMV1-3 X1/X2 feasibility) —
  measured by the lane, never negotiated after outcomes.

## Disposition of remaining A7 findings

- F-1 (cohort-wide depth on 4-entity sample): disclosed and carried as a
  G2 lane condition — full cohort staging with per-CIK depth census before
  any panel build; identity freeze stays conditional (G1 court wording).
- F-3 (evidence uncommitted): remediated by landing this addendum +
  committing all G1–G3 artifacts in the same control-plane commit.
- F-4 (D3 event-book veto vs owner-verbatim priority): NOT remediable by
  agents — explicit ratify/override decision item in the owner packet;
  the N3/N4 data-plane repair is retained either way.
