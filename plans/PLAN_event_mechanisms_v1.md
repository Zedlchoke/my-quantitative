# PLAN — EVENT-MECHANISMS-V1 (2026-09-27)

Cycle: `EVENT-MECHANISMS-V1` — asset `shared` — event-driven, falsifiable
mechanisms on stocks / crypto / FX. Separate from the closed DTP program
(master DAYTRADE-PLAYBOOKS-PROGRAM-V1 stays TERMINAL; nothing inherited from
it except evidence).

Owner directive verbatim: `research/control/EVENT-MECHANISMS-V1/OWNER_DIRECTIVE.md`.
Intake: `research/control/EVENT-MECHANISMS-V1/INTAKE_2026-09-27.md`.

## 0. Identity

```text
cycle_id            EVENT-MECHANISMS-V1
theme               event-driven mechanisms with a named payer, a PIT
                    observable at decision time, and a preregistered
                    falsifier — across stocks (priority), crypto, FX
authority           plan + owner directive (above); registry via researchctl
worktree            .worktrees/event-mechanisms-v1/integration
branch              orca/event-mechanisms-v1-integration
budget              0/6 scored cells at registration (scored cells consumed
                    only after A7 prelaunch PASS + owner GO at this cycle's
                    own gate)
S1                  SEALED_UNTOUCHED throughout this plan
GO phrase (scored)  GO EVENT MECHANISMS V1 SCORED EXECUTION
GO phrase (OOS)     GO EVENT MECHANISMS V1 SEALED OOS   (separate, later gate)
```

## 1. Objective and success definition

Find at most three event-driven identities whose mechanism (who pays, why
they must pay, what is observable when) survives the falsification battery
BEFORE any PnL, then (only after owner GO) a preregistered scored
walk-forward vs baselines/controls with cost stress, stopping at a separate
sealed-OOS gate.

**A negative result is success**: `NO_ELIGIBLE_PROPOSAL` with measured
evidence and a concrete owner data-action list is a first-class outcome
(DTP/ERP1 precedent). Fabricating profitable strategies is forbidden and
impossible under these gates by construction.

## 2. Non-goals / hard boundaries

- No GO consumption by this plan alone; two separate owner gates (scored,
  OOS). No S1 opening. No orders/paper/live. No shadow/dashboard/worker
  changes (owner: out of scope). No push, no merge to `main` from lanes.
- **FX: no scored cell this cycle.** FX after-cost frontier is
  BLOCKED_BROKER_COST_AUTHORITY (DFV1 census #4; ERP1 3.6/4.4-pip floor);
  macro release-clock class measured-dead (P-24); FOREX-NG1 re-entry needs a
  materially new evidenced source. FX directions may be screened, vetoed, or
  recorded BLOCKED with owner actions — never scored.
- **Crypto: separate data/cost authority** (measured books only; no
  forced-flow/order-book inference from candles — owner law 2026-09-26).
  Funding/basis/settlement-adjacent planes are closed by identity
  (TRACKB1 rho 1.0000; SRLV both directions; PWS P-29 representation math).
- No parameter sweeps. Per identity: 1 anchor + ≤2 neighbours + 1
  same-direction control + 1 sign-flip control + 1 preregistered baseline.
  One proposal-revision round before freeze, then frozen.
- No substituted/backfilled timestamps or prices when a source is missing:
  record `BLOCKED_DATA` + owner action (owner directive verbatim).

## 3. The eight directions under screening (provenance-labeled)

The owner's prior enumeration of "tám hướng" is not in the repo; this set is
reconstructed from written owner guidance and each direction carries its
provenance. The owner may swap any direction before G3 freeze; screening
re-runs cheaply (paper court).

| ID | Direction | Asset | Provenance |
|---|---|---|---|
| D1 | EDGAR **acceptance-timestamp filing-flow** (announcement-timing/PEAD-class on minute-precision clock; day-session boundary conditioning) | stocks | owner instruction 2026-09-27 verbatim ("EDGAR acceptance timestamp"); DFV1 gap N2; frontier F1 |
| D2 | **Form 4 insider event flow** on acceptance clock (role/value conditioning; NOT 10b5-1 plan-cadence re-label) | stocks | owner instruction 2026-09-27 verbatim ("Form 4"); frontier F1 |
| D3 | **Corporate-action PIT rebuild** → honestly-adjusted state + ex-date event book (fixes L-SAMV1-1; dated identity joins N4) | stocks | owner instruction 2026-09-27 verbatim ("corporate-action PIT"); DFV1 gaps N3/N4 |
| D4 | **FTD (fails-to-deliver) × price** cross | stocks | DFV1 frontier F1 (stocks filing-flow family); control-plane precedent DEU Lane S |
| D5 | Crypto **funding settlement / forecast-funding surprise** events | crypto | plan_at.md §3C — **DRAFT, owner approval UNVERIFIED** (erratum E-P1; only D1/D2/D3 are owner-verbatim today) |
| D6 | Crypto **liquidation / forced-flow cascade** events | crypto | plan_at.md §3C — DRAFT, approval UNVERIFIED (E-P1); DFV1 O2 |
| D7 | Crypto **delta-neutral basis/carry convergence** events | crypto | plan_at.md §3B — DRAFT, approval UNVERIFIED (E-P1); ERP1-TRACKB ancestry |
| D8 | FX **after-cost event families** (macro-release clock, session/liquidity events) | fx | plan_at.md §3A (DRAFT, approval UNVERIFIED — E-P1; §3A is liquidity provision, partial label mismatch) + DFV1 F3 (BLOCKED on R1) |

Screening law (per direction, owner's eight required fields): payer; why
they must pay; PIT observable at decision time; when the edge expires; cost
ceiling; the simple control that could replicate it; falsifier; collision
with dead families (FAMILY_FAILURES 139 rows + DTP death ledger 38 ids).

## 4. Gate chain (each gate PASS/FAIL/NOT_RUN/BLOCKED with margin-to-fail)

```text
G0  intake (done)                    measured state; dirty tree classified;
                                     prior-session liveness excluded (P-17)
G1  screening court                  A1 writes SCREENING_MATRIX (8 directions
                                     × 8 fields); INDEPENDENT SKEPTIC
                                     (fresh-context subagent) has VETO;
                                     skeleton-merge collapses same-shape ideas;
                                     outcome-blind (no PnL surfaces exist)
G2  data authority (fail-closed)     per surviving direction: authority rows,
                                     measured availability, license, coverage,
                                     canary; stocks priority per owner;
                                     BLOCKED_DATA discipline; crypto/FX
                                     separate authority; FX never scored
G3  identity freeze (≤3)             F-0 mechanism-class court vs dead set
                                     (≥2/3 axes new; representation-rho;
                                     no parameter sweeps); freeze hypotheses,
                                     arms, folds, budget, ceilings
G4  falsification battery pre-PnL    (a) PIT battery incl. unfinished-window
                                     guard (RANGEFADE class); (b) future-
                                     mutation test; (c) panel-truncation replay
                                     byte-identical; (d) control validity
                                     (Q-11: null must move the signal;
                                     clock-only shadow per Q-7)
G5  independent implementation       second implementation from frozen spec,
                                     different context; agreement tolerance
                                     preregistered (P-4 law)
G6  cost ceiling (paper, frozen)     Q-2 conditional cost + L-SAMV1-3 X1/X2
                                     fill-feasibility (stocks); gross must
                                     clear ceiling at 1.0× and survive
                                     1.5×/2.0× stress — arithmetic before
                                     implementation
G7  A7 prelaunch (independent)       hashes, identity, dry-run hygiene,
                                     denominator seed, ledger integrity;
                                     0 unresolved HIGH/CRITICAL
STOP→ owner packet: exactly which cells qualify → owner types
     GO EVENT MECHANISMS V1 SCORED EXECUTION at this gate
G8  scored S0 walk-forward           ≤6 cells per frozen arms; record ALL
                                     failures; baselines/controls; cost
                                     stress; append-only ledger (observed
                                     counter)
STOP→ sealed-OOS gate (separate owner decision; S1 laws; nothing in this
     plan opens it)
```

Trial ledger + outcome-exposure map exist from bootstrap — BEFORE any PnL
(`TRIAL_LEDGER.jsonl`). Every scored computation enters the observed
denominator even if publication fails (P-9/P-15).

## 5. Gate verdicts so far

| Gate | Verdict | Evidence |
|---|---|---|
| G0 intake | PASS | `INTAKE_2026-09-27.md` (this file references measured state; lock FREE_PROVEN; 0 workers; dirty tree preserved/landed with attribution) |
| G1..G7 | per reports in `research/control/EVENT-MECHANISMS-V1/` | see each gate artifact |

## 6. Lesson-to-gate matrix

`research/control/EVENT-MECHANISMS-V1/LESSON_TO_GATE_MATRIX.md` — the six
owner-named error classes (RANGEFADE lookahead; same-implementation-same-bug;
variant multiplication; cost-eats-edge; data/timestamp-without-authority;
prospective/OOS-not-from-backtest) each mapped to a machine-enforced gate.
A listed gate not run is NOT_RUN.

## 7. Stop conditions

- Any CONTROL_STATE_DRIFT / unexplained dirty tree / foreign worker
  conflict → stop, record, preserve.
- SEC sources (data.sec.gov) become unreachable → D1/D2 record
  `BLOCKED_NETWORK` with the L-FIBV1-1/L-FXFF-1 estate-block precedent;
  owner action = network unblock (one action covers www.sec.gov +
  Dukascopy + CME estates). **www.sec.gov/Archives is ALREADY measured
  403-blocked at G0** (intake) — raw-XML re-fetch is not available; on-disk
  archives (P-13 restorable) + data.sec.gov submissions JSON are the lawful
  surfaces.
- Substrate archives unrestorable / digests mismatch → `BLOCKED_DATA` +
  owner action list (re-acquisition procedure), never substituted data.
- All directions die at G1/G3 → `NO_ELIGIBLE_PROPOSAL` close with evidence
  + data-needed list (valid terminal per owner directive).
- Resource: heavy jobs under the machine-wide lock only; conflict →
  `NOT_RUN_RESOURCE_CONFLICT`, yield, never kill foreign workers.

## 8. Handover deliverables (owner directive)

1. This plan; 2. data-gap / owner-action matrix; 3. vetoed-identity list
with reasons; 4. trial ledger; 5. A7 report(s); 6. GO/OOS gate status
(stopped-at-gate by construction until owner types the phrase); 7. clear
recommended decision.
