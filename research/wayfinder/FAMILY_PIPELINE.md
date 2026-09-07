# FAMILY PIPELINE — the research-family lifecycle protocol

> Governance protocol dated 2026-09-07, adopting the owner's
> "APPROVED WITH AMENDMENTS" directive. **Merge-candidate status**: this
> file lives on branch `orca/governance-family-pipeline` and becomes the
> standing factory standard ONLY when the owner merges that branch to
> main; until then it is normative for nothing except its own branch and
> plans that explicitly preregister it. It merges the owner's
> 8-phase/40-step pipeline proposal into the existing factory machinery;
> it replaces nothing. Order of authority is unchanged
> (RULES.md §0): owner instruction > live plan > CLAUDE.md > frozen
> contracts > historical plans > prose. Where this file and a live plan
> disagree, the LIVE PLAN of the running cycle wins; this file governs
> future plans and Lead review.
>
> Implementation status of the four mechanisms born here (registry,
> diagnostic gate, heavy lock, failure memory) is tracked in RULES.md §9;
> until then every mechanism is `DOCUMENTED_NOT_IMPLEMENTED`.

## 0. The lifecycle in one page

```text
Phase 1  choose unexplored territory     (failure memory -> causal claim)
Phase 2  data before strategy            (PIT/coverage/revision audit)
Phase 3  blind discovery                 (3 lanes x 2 proposals, 3 arms)
Phase 4  cheap-kill                      (measured, no PnL, six kills)
Phase 5  selection                       (freeze everything score-affecting)
Phase 6  implementation                  (frozen contract -> twin)
Phase 7  launch                          (A7 fresh-context -> owner GO)
Phase 8  learning                        (reproduce -> audit -> memory)
```

## 1. Phase 1 — choose unexplored territory

1. Read the forbidden inventory (`HYPOTHESIS_LEDGER.md`) AND the failure
   memory (`FAMILY_FAILURES.jsonl`): every dead family carries machine-
   readable failure signatures (§6) — a new proposal must not recreate a
   recorded signature pattern on the same information set.
2. Choose a NEW information set — "new information, not new arithmetic"
   (the S-1 lesson). A new transform of an already-mined source is not a
   new territory.
3. Write the causal claim as ONE sentence: who is forced to trade or slow
   to react, why, and when the mechanism must fail. This sentence is a
   frozen proposal field (§7 `causal_claim_one_sentence`).
4. State what would prove the claim wrong — the falsification rule is a
   frozen proposal field (§7 `falsification_rule`), not a post-hoc
   narrative.

## 2. Phase 2 — data before strategy

5. Audit license, coverage, PIT and revision integrity BEFORE any
   proposal exists. A source that cannot fund the S0 window is
   `COVERAGE_INSUFFICIENT_FAIL_CLOSED` — it dies here, cheaply.
6. Freeze the decision timestamp semantics per observable: event /
   effective / available / retrieved are four different clocks; every
   conditioning field carries an availability-lag mutation contract (a
   value arriving late must move the decision exactly one period).
7. **Archive rewrites are a first-class verdict, never a footnote.**
   Publication lag does NOT prove revision integrity. Three verdicts,
   per handbook §11.7, are mandatory for every archive axis:
   `PASS_PIT_EVIDENCED` / `RETROSPECTIVE_ONLY` / `BLOCKED_DATA`.
   A measured publication lag plus a rewritten span (no original listing,
   checksum or independent snapshot) is at best `RETROSPECTIVE_ONLY`;
   asserting it as PIT evidence is forbidden. This exists because a
   plausible-sounding lag assumption passed every review once (P-1) and
   because a rewritten-span archive was nearly treated as PIT (V15's
   `MEASURED_BOUND_LAG_3D` + `REWRITTEN_SPAN` caveat: the lag is honest
   ABOUT THE CURRENT BYTES; it says nothing about what the bytes said at
   decision time).
8. No proposal is created until the data axis is FUNDED (coverage census
   published). Unfunded axes are carried as `DATA_BLOCKED_VALID`, never
   speculated around.

## 3. Phase 3 — blind discovery

9. Three independent lanes from one wave SHA, maximum two proposals per
   lane, each lane on a DISTINCT sanctioned axis.
10. No lane ever sees scored outcomes; outcome-blind attestations are
    signed on the wave SHA. (Re-)proposals of a prior cycle's
    eligible-but-never-scored ideas are legal (no scored ancestry) and
    must be written fresh and blind from the new wave.
11. Every proposal carries exactly three arms: anchor, neighbour (same
    mechanism, different parameters) and control (placebo/causal — the
    convenient explanation that must NOT reproduce the anchor).
    Control CLASSES are mandatory per mechanism type and data semantics:
    calendar-conditioned mechanisms carry a sham-calendar/sham-event
    placebo (V5 lesson); mechanism claims about a conditioning variable
    carry a raw-level/exposure-form control; a control that cannot run
    under evidenced semantics is a design failure (P-3), not a pass.
12. Every proposal declares its expected failure mode (how it most
    plausibly dies: costs, crowding, sector beta, fold concentration,
    coverage, PIT) — the hypothesis the family is willing to lose to.

## 4. Phase 4 — cheap-kill (measured, no PnL anywhere)

Six kills, all measured pre-selection; any one is terminal for the
proposal:

13. **Ancestry correlation** — pooled |rho| > 0.20 vs every forbidden
    inventory entry and measured shadow (asset-specific veto sets).
14. **Control identifiability** — anchor-vs-control exposure correlation
    high enough that the control cannot falsify (V8-a5 lesson), or a
    control that is unrunnable by construction.
15. **Event count per fold** — decisions, not signals: enough bookable
    entity-decision pairs per fold to populate every gate.
16. **Turnover/cost ceiling** — projected fills vs the frozen cost
    schedule; cost-dominated designs die here.
17. **Weight/concentration feasibility** — leg weights compatible with
    the frozen adapter/portfolio caps (OILEV died exactly here).
18. **Runtime/resource feasibility** — measured compute envelope on the
    target host (an O(N^2) design dies on paper, not mid-run — INC of
    V10 P0).

## 5. Phase 5 — selection

19. Maximum two families per cycle (plan may bind lower).
20. Exactly three arms per family.
21. Unused slots are DEAD — never reassigned, never lent.
22. Freeze, in one selection artifact: proposal hashes, arm identities,
    arm_config_digest, data snapshot digest, costs, folds, gates AND
    every diagnostic output contract (§8). Nothing score-affecting may
    change after this point without a remediation cycle.

## 6. Phase 6 — implementation

23. A8 implements the frozen contract verbatim; ambiguities return to
    A1 — never "improved" in lane.
24. Synthetic hand-computed fixtures: golden features, one-bar lags,
    no-lookahead mutations, DST boundaries, fold force-flat, cost-once,
    control-differs-from-anchor, deterministic double-run, malformed
    data fails closed.
25. Sanitized real-data dry-run: no PnL, PF, stress, break-even or
    outcome-shaped field at ANY record depth — AND non-vacuous
    (real decision counts above a frozen sampling floor; zero-decision
    passes are failures — V8's F-A7-1).
26. **Diagnostic persistability gate** (§8): prove BEFORE launch that
    every mandatory terminal diagnostic has an output contract in the
    run contract, and that the twin can re-emit them. Status:
    `DOCUMENTED_NOT_IMPLEMENTED` until the validator is adopted by a
    future cycle.
27. Detached reproduction twin created at the code freeze.

## 7. Phase 7 — launch

28. A7 fresh-context prelaunch (never the A1's own thread; V8 lesson).
29. Blockers found before any scored outcome are fixed via remediation
    lane; after scored outcomes exist, §22 of the handbook applies.
30. A7 re-audits the delta; authorization requires zero unresolved
    HIGH/CRITICAL.
31. Owner GO is the SECOND key, turned AFTER reading the A7 verdict:
    fresh, exact-phrase, at its own gate (P-8). A GO typed early is
    recorded intent, extinguished unconsumed; phrases never cross cycles.
32. Scored cells run serially under the GLOBAL heavy lock (machine-wide
    `fcntl.flock`, §9): if the lock is not acquireable the verdict is
    `NOT_RUN_RESOURCE_CONFLICT` — never contention, never silent
    overlap.

## 8. Phase 8 — learning

33. Independent reproduction from the detached twin, byte-compare
    excluding pre-declared runtime fields.
34. A7 terminal recomputes from bytes; POSITIVE results audited
    stricter than negatives (§20.2).
35. Record the failure signature(s) into `FAMILY_FAILURES.jsonl`
    (primary vs secondary; §-taxonomy below) with evidence path and
    terminal SHA. Nothing is inferred; unrecoverable fields are
    `null` / `UNKNOWN_NOT_RECOVERABLE`.
36. Record forbidden descendants in the ledger's ground rules.
37. Record durable assets built (panels, censuses, calendars,
    observable layers) — they outlive their cycles.
38. Record which questions remain open (owner doors: keys, data
    decisions, unblocked-but-unfunded axes).
39. Update BOTH denominators — observed (every computed outcome, even
    if publication failed) and published — in the Lead-maintained
    ledger only (P-9).
40. Only a survivor that passes EVERY frozen gate — with margin-to-fail
    reported per gate (P-2) — is locked awaiting a future owner-approved
    S1 plan, after the four-layer test (mechanical/data/statistical/
    economic). DSR/PBO terminal accounting is mandatory where computable;
    `NOT_RUN` is fail-closed and must say WHY (§8.1).

### 8.1 The two incidents that made §8 (diagnostic persistability) necessary

- **V3R (forex)**: at terminal, DSR/PBO could not be computed —
  `NOT_RUN fail-closed, no per-period series in the program ledger`.
  The runner had never persisted per-period returns; the statistic that
  prices multiple testing was unreachable on the exact family that
  needed it most.
- **V15 (crypto)**: `TERMINAL_PENDING` at governance intake (phase E,
  budget 0/6). Measured at the p3 freeze: the frozen output contract
  carries no per-period-returns fields, and the stage-A gate table's
  per-symbol class is not covered by an output contract. Owner-reported
  at dispatch (verify and link at canonical close): gates G6–G9 NOT_RUN
  for absent per-period returns, DSR/PBO NOT_RUN, and a terminal rerun
  producing a metadata TECHABORT. Cited here as the design pressure for
  the gate, pending V15's terminal artifacts.

## 9. Failure taxonomy (registry `FAMILY_FAILURES.jsonl`)

Verdict classes — five, per owner amendment 2026-09-07, plus lifecycle
statuses:

```text
SCIENTIFIC_REJECTION   ran to a valid scored verdict and failed frozen gates
DATA_BLOCK             axis unfundable / license / PIT unevidenced (no PnL exists)
SELECTION_REJECTION    killed pre-selection by a measured cheap-kill
TECHABORT              computation invalid/unfinished — CARRIES NO FAMILY-
                       QUALITY EVIDENCE EITHER WAY (never cited as the
                       family being good or bad)
PROCESS_INCIDENT       governance failure (leak, vacuous dry-run, quota death,
                       control-state drift) — recorded, adjudicated separately
TERMINAL_PENDING       cycle not yet canonically closed (Lead ledger row absent);
                       no failure fields may be finalized under this status
NOT_RUN_SUPERSEDED     preregistered but never scored; cycle superseded —
                       carries no family-quality evidence
```

`primary_failure` is the ONE decisive failure (the gate that killed it);
`secondary_failures` are corroborating observations. Both use the
signature codes below (extensible; new codes require a Lead note in the
registry changelog):

```text
EXPECTANCY_NONPOSITIVE            PF_BELOW_THRESHOLD
STRESS_TIER_FAIL                  FOLD_CONCENTRATION_OVER_LIMIT
FOLD_POPULATION_UNDER             CONTROL_REPRODUCED_MECHANISM
CONTROL_OUTEARNED_ANCHOR          MECHANISM_SANITY_NULL
ANCESTRY_RHO_BLOCK                CONTROL_IDENTIFIABILITY_FAIL
COVERAGE_INSUFFICIENT             PIT_UNEVIDENCED
DATA_AUTHORITY_INVALIDATED        COST_DOMINATED
MDD_OVER_CEILING                  INCREMENTAL_ALPHA_NEGATIVE
ETF_SHARE_SECTOR_DROWNING         SPY_EXCESS_ZERO_FOLDS
ADAPTER_WEIGHT_INFEASIBLE         VACUOUS_DRYRUN
RESOURCE_QUOTA_BLOCK              DIAGNOSTIC_CONTRACT_GAP
```

## 10. Proposal template (frozen fields, D1)

```text
proposal_id / lane / axis
causal_claim_one_sentence      ONE sentence: forced trader + why + failure state
falsification_rule             what observed result proves the claim wrong
control_class                  mandatory-by-mechanism (sham-calendar, exposure-form, ...)
expected_failure_mode          the hypothesis the family is willing to lose to
universe / clock / warmup / decision timestamp semantics
features + availability evidence per field (EVIDENCED/ASSERTED/UNEVIDENCED)
anchor / neighbour / control arm specifications
costs / folds / gates referenced (frozen at P3)
outcome_blind_attestation      signed on the wave SHA
```

## 11. Mechanism implementation status

```text
FAMILY_PIPELINE protocol             DOCUMENTED (merge candidate on this branch —
                                     standing standard only upon owner merge)
FAMILY_FAILURES registry + validator IMPLEMENTED/TESTED at commit 2 of this branch
diagnostic persistability gate       IMPLEMENTED/TESTED at commit 3 + remediation
                                     (adoption: future cycles)
global heavy lock                    IMPLEMENTED/TESTED at commit 4 + remediation
                                     (adoption: future cycles)
```

RULES.md §9 carries the live status table. The authoritative ladder is:
`DOCUMENTED -> IMPLEMENTED -> TESTED -> ADOPTED_BY_ACTIVE_CYCLE`.
Mechanisms here are adopted ONLY by cycles whose plans preregister them;
frozen/running cycles (V15, forex V6, stocks V11 at dispatch time) are
explicitly NOT retrofitted — adoption boundary: crypto V16+, forex V7+,
stocks V12+.
