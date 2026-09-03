# Data-authority requirements — US cash-equity/ETF research factory

> Provider-neutral handoff packet. Machine-readable authority:
> `requirements.json` (same directory). This file is the human narrative and
> does not override it. Status of every real-data requirement at generation:
> **UNAVAILABLE_FAIL_CLOSED** — nothing here may be inferred as satisfied.
>
> This packet authorizes NO purchase, NO account creation, NO credential
> request and NO unapproved download. It states what must be supplied and
> proven before scored stocks research may run.

## Why this exists

The stocks sprint closed `STOCKS_BLOCKED_DATA_AUTHORITY`: engineering (M0 core,
S1 correctness lanes, S2 proposals, S3 audit + selection freeze) is complete
and gate-clean, but every remaining phase (window freezing, S4/S5 validation on
real data, S6 scored cells) consumes point-in-time facts no free convenience API
can prove. Two families are frozen and waiting:

| Family | Data it lives or dies on |
|---|---|
| `EQ_S2_A3_F1_PIT_RECON_FLOW` | index maintenance events with **announcement** vs **effective** timestamps, effective-dated membership, survivorship-safe snapshots |
| `A5-S2-F1-LENDING-CONSTRAINT-PREMIUM` | borrow availability, fee/rate (declared accrual basis), utilization, recalls; honest dividend liability |

The shared factory additionally requires security master, identifier history,
corporate actions, raw+adjusted prices, executable price/volume fields, SPY
total-return inputs, calendar reconciliation, checksums, and license terms.

## Requirement map (summary — authority is requirements.json)

| ID | Area | Obligation | Critical for | Synthetic fixture today |
|---|---|---|---|---|
| R01 | PIT security master | required | factory + both families | yes (A3) |
| R02 | historical index/universe membership, effective-dated | required | F1 recon-flow | yes (A3) |
| R03 | ticker/identifier changes | required | factory + F2 | yes (A3) |
| R04 | listings and delistings | required | factory + both | yes (A3) |
| R05 | splits/dividends/other corporate actions | required | factory + F2 | yes (A4) |
| R06 | announcement vs effective timestamps | required | F1 recon-flow | no |
| R07 | survivorship-bias controls | required | F1 recon-flow | yes (A3) |
| R08 | adjusted AND unadjusted prices | required | factory + F2 | partial (A4) |
| R09 | volume and executable price fields | required | factory + F2 | yes (A5 semantics) |
| R10 | SPY total-return benchmark inputs | required | factory | no |
| R11 | borrow availability (locate) | required | F2 | yes (A5 fail-closed semantics) |
| R12 | borrow fee/rate + utilization | required | F2 | yes (A5 accrual semantics) |
| R13 | timestamps/timezone/calendar conventions | required | factory + both | yes (A4 US_EQUITY_REGULAR_V1) |
| R14 | revision/vintage behavior | required | factory + both | no (process) |
| R15 | API/export format | required | factory + both | yes (loader schema) |
| R16 | history floor and coverage (>=8y daily, >=30 names/decision) | required | factory + both | yes (A3 floor validators) |
| R17 | checksum and immutable snapshots | required | factory + both | yes (A3 checksum goldens) |
| R18 | license / storage / research-use / redistribution | required | factory + both | no (legal) |
| R19 | missing-data and correction policy | required | factory + both | partial (gap classification) |

## Non-negotiable evaluation rules

1. **Fail closed.** Missing evidence is `UNAVAILABLE_FAIL_CLOSED`, never an
   inferred PASS. A provider without proven announcement-vs-effective
   separation (R06) or PIT borrow fields (R11/R12) cannot serve the frozen
   families, whatever its price or brand.
2. **No convenience-API authority.** Free convenience sources remain
   `DIAGNOSTIC_ONLY` unless they independently prove timestamps, adjustments,
   delistings and corporate actions per `requirements.json`.
3. **Evidence, not claims.** Each requirement's `evidence_needed_for_PASS`
   column defines what earns PASS. Evaluation happens in
   `provider_evaluation_template.json`; physical acceptance via
   `ingestion_acceptance_checklist.md`.
4. **Calendar anchor.** Delivered session data must reconcile against the
   frozen `US_EQUITY_REGULAR_V1` calendar (manifest digest `028a7b21…`),
   including the half-day table; unexplained deviations create a new calendar
   version and a new data manifest, never a silent patch.
5. **No payloads in Git.** Licensed raw data stays outside the repository; only
   manifests and checksums are tracked (R17/R18).

## After a provider is approved

Fill `provider_evaluation_template.json` with evidence per requirement, then
execute `ingestion_acceptance_checklist.md` end to end. Only then may S0/S1
windows be frozen from actual coverage and S4/S5/S6 proceed under
PLAN_stocks.md §10–13.
