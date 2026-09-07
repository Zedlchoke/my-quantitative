# CRYPTO V16 — THE BOUNDED MICROSTRUCTURE PROBE: AGGTRADES, THE LAST KEYLESS FAMILY

> Owner plan dated 2026-09-07, drafted by the Lead Engineer from V15's
> measured terminal. Activates on owner dispatch; nothing starts on its
> own. A correct `V16_REJECT_ALL` — and an equally correct early
> `BLOCKED_DATA` — are successful research runs.
>
> `plans/PLAN_crypto_v15.md` and all earlier crypto plans/records are
> closed historical authorities.

## 0. Frozen starting point

```text
V15 terminal            10792a2 (branch orca/v15-integration; closeout
                        ad61fca + terminal-line merge 503d93c; code freeze
                        824190c; A7 terminal V15_TERMINAL_APPROVED_0_FAIL;
                        reproduction ALL_MATCH 61,633 leaves)
V15 outcome             both families dead on frozen rule order #1:
                        ELITE-SIZE-ASYM −0.00173/day (PF 0.897, MDD 65.9%)
                        with falsification-by-control instance #11 — the
                        control CTL-ELITELEVEL (+0.00196/day, PF 1.131,
                        MDD 10.3%) OUT-EARNED the anchor, then failed G4
                        concentration 0.5298 itself: a measured falsification
                        artifact, never promotable; TAKER-SAT −0.00380/day
                        (PF 0.842), control not reproducing. A4's OI-axis
                        pair novelty-blocked pre-score (rho 0.431 vs
                        CTL-OISHARE, 0.253 vs OICYC-STOCH28).
V15's measured frontier the API endpoints were coverage-killed in V14;
                        the bulk daily-metrics family is now mined to
                        rejection in V15. The ONE keyless family never
                        touched: aggTrades-class bulk — excluded from V15
                        §2 as "cannot fit a bounded extraction design on
                        an 8 GB host". V16 either fits a BOUNDED design
                        or measures the free frontier closed, cheaply.
denominators            crypto 149/152 (ledger authority, P-9); budget 0/6
                        for V16; S1 SEALED_UNTOUCHED
durable assets          108-file sha256-pinned bulk-metrics staging with
                        MEASURED_BOUND_LAG_3D availability semantics +
                        LAG_3D-compliant observables (reusable as context
                        or controls; pins re-verified if touched)
governance adoption     V16 is the FIRST cycle past the adoption boundary
                        (FAMILY_PIPELINE §11) and therefore ADOPTS the three
                        governance mechanisms — see §3 (mandatory)
```

## 1. What is closed and may not be rescued

The cumulative forbidden inventory through V15: OITD + near-duplicates;
LIQEPIS + duplicates; OILEV-V2 anchor AND inverted control (the §1.1
shadow region closed by OICYC's confirmatory reject); basis-level fade
(PREMFADE at any parameter/universe variant); BAB; carry families; ILLIQ
(owner-data-gated); and the V15 additions — the elite-size-ASYMMETRY form,
the taker-saturation form, and the elite-LEVEL measured shadow (re-entry
of the shadow only as a brand-new preregistered family with its own
falsification control and measured decorrelation vs every ancestor AND
the CTL-ELITELEVEL exposure; the falsification artifact itself is never
promotable). Cross-asset falsification-cluster method applies unchanged.

## 2. Mission and allowed scope

V16 asks one bounded question:

> Do trade-level microstructure observables — aggressor-flow imbalance
> and trade-arrival structure extracted from a BOUNDED, hash-pinned
> aggTrades design on a small symbol set — carry incremental after-cost
> information beyond benchmark context, at daily-or-slower clocks?

The binding word is BOUNDED. The 8 GB host constraint is a frozen input,
not a preference:

- symbol set: at most 2-3 symbols chosen by P0 coverage + size census;
- window: the S0 window only, no history maximization;
- extraction: streaming aggregation to bounded daily (or coarser)
  observables; raw bytes may be downloaded month-by-month, sha256-pinned,
  reduced, and the reduction hash-recorded — raw archives are DELETED
  after reduction unless total footprint stays under a frozen disk
  ceiling measured in P0;
- **P0 hard gates (measured, before any proposal exists)**: projected
  peak disk, peak RSS, and end-to-end runtime per symbol-month — any
  ceiling breach = `BLOCKED_DATA` and the crypto program goes dormant
  pending an owner data decision, with the free-keyless-frontier map
  complete.

Three sanctioned axes (wave diversity binding):

1. **aggressor-flow imbalance** (mandatory lane): signed trade-flow
   concentration and imbalance at bounded sampling granularity.
2. **trade-arrival structure**: inter-arrival/intensity/clustering shape.
3. **open axis**: any literature-backed mechanism on authorized data in
   the non-forbidden space (the staged V15 bulk-metrics observables may
   serve as CONTEXT or CONTROL legs, pins re-verified, never as rescued
   families).

Binding rules carried: coverage-first vs the S0 window; availability
evidence from repository publication semantics only (dated files,
listing-page evidence, sha256 pins) — publication lag never proves
revision integrity; archive-rewrite checks per the three-verdict rule
(PASS_PIT_EVIDENCED / RETROSPECTIVE_ONLY / BLOCKED_DATA); cost charged
exactly once per fill (L-V14-0); stress multipliers on booked PnL; |rho|
<= 0.20 pooled vs the full forbidden inventory incl. the V15 additions;
exactly three arms; max six cells; unused slots never reassigned.

Allowed terminal outcomes:

```text
V16_REJECT_ALL
V16_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
V16_BLOCKED_DATA_OR_SELECTION
V16_BLOCKED_PRELAUNCH
V16_INCOMPLETE_NOT_PROMOTABLE
```

## 3. Governance adoption (mandatory in V16 — first cycle past the boundary)

V16 preregisters and therefore ADOPTS the three mechanisms from branch
`orca/governance-family-pipeline` (validator modules at cffaeb9/a01d4a2/
f31598d; if not yet on main at dispatch, the A1 cherry-picks those
commits into the cycle branch first — cycle-branch integration, not a
main merge):

1. **Diagnostic persistability gate** (P-11 — bought by V3R and V15's
   own DSR/PBO NOT_RUN): the run contract carries a
   `diagnostic_output_contract` block validated BEFORE A7 launch
   authorization — per-period series (DSR/PBO), per-symbol breakdown,
   margins per gate, identity fields, reproduction inputs mandatory;
   conditionals require frozen applicability predicates;
   `BLOCKED_PRELAUNCH` on any gap. No V16 driver runs a scored cell
   without per-period series in its output contract.
2. **Global heavy lock**: every heavy phase (download, extraction, full
   pytest, scored cells, reproduction) acquires
   `.runtime/heavy_worker.lock` (fcntl.flock) with the PID +
   process-start-token registry; refusal is NOT_RUN_RESOURCE_CONFLICT,
   never contention.
3. **Failure memory**: at close, the A1/Lead appends the cycle's
   families to `research/wayfinder/FAMILY_FAILURES.jsonl` (schema +
   validator run green; primary vs secondary separated; TECHABORT
   carries no quality evidence).

## 4. Cycle structure (standard, deltas only)

- **P0 (A3)**: aggTrades feasibility census — per symbol-month: file
  sizes, expected RSS under the streaming reduction, runtime estimate on
  THIS host, publication/listing semantics, license scope of the public
  bulk repository; freeze the bounded design (symbols, window, ceilings)
  or close BLOCKED_DATA. Publish BEFORE D1.
- **P1**: kernel regression (cost-once fixtures; stress on booked PnL).
- **P2**: coverage-first per proposal clock (funded clocks count).
- **P3**: invariants freeze incl. diagnostic_output_contract (§3.1) and
  margin-to-fail scaffolding; no PnL.
- **D1/D2**: three blind lanes from one wave SHA; packet discipline with
  causal_claim_one_sentence + falsification_rule + expected_failure_mode
  fields; novelty vs the full inventory measured pre-selection; control
  identifiability measured pre-selection.
- **I/Q**: availability-lag mutation per conditioning field; exact-arm
  sanitized dry-run, non-vacuous, recursive leak scan; twins at freeze;
  heavy phases under the lock; twin smoke-rerun proves every declared
  diagnostic is emitted.
- **E**: max six serial cells after the two-key HARD STOP — A7
  fresh-context independent first (with the diagnostic gate in its
  scope), then the owner types, fresh and informed:

```text
GO CRYPTO V16 SCORED EXECUTION
```

- **Terminal**: reproduction from the twin (per-period series now
  exist); DSR over the updated crypto history (N = 152 + V16 cells);
  PBO fail-closed below 8 configurations; margins per gate; failure
  registry append; program totals as-of-intake (P-9).

## 5. Hard boundaries

Unchanged from V15 §4: no S1/paper/live/orders/credentials; no new keyed
or paid source; no optimizer/rescue/threshold weakening; no rewriting of
prior ledgers/terminals; pushes only on owner instruction; gates report
PASS/FAIL/NOT_RUN/BLOCKED with commands, exit codes, SHAs and margins;
heavy jobs serialized machine-wide UNDER THE LOCK (sibling cycles
respected with NOT_RUN_RESOURCE_CONFLICT; note stocks V11 may still be
running — coordinate, never contend).

## 6. First report from a fresh A1

```text
measured UTC / root / branch / HEAD / porcelain
V15 terminal + A7T chain verified; crypto 149/152, budget 0/6, S1 seal
governance mechanisms cherry-picked/verified (validator imports green)
aggTrades feasibility pre-check (per symbol-month size/RSS/runtime census)
GO/NO_GO for the bounded P0 design (or BLOCKED_DATA recommendation)
```
