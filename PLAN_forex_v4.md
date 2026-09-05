# FOREX-FREE-V4 — MACRO-CONDITIONED DISCOVERY ON EVIDENCED AVAILABILITY, WITH THE CARRY FRONT DOOR

> Owner plan for the next Forex research cycle, dated 2026-09-05.
>
> `PLAN_forex.md` (F1), `PLAN_forex_v2.md` (V2), `PLAN_forex_v3.md` (V3)
> and the V3R remediation record are closed historical authorities and must
> not be rewritten. This file starts V4 only. A correct
> `FOREX_FREE_V4_REJECT_ALL` is a successful research run.

## 0. Frozen starting point

Measured terminal authority (A1 must remeasure; drift affecting identity,
counters, data authority or S1 is an intake blocker):

```text
completed branch       orca/forex-free-v3r-integration
terminal SHA           c356813f4a6ed2c3917f315e13c1261c022f30ed
terminal verdict       FOREX_FREE_V3_DATA_AUTHORITY_INVALIDATED
V3 cycle close         8f674f1... (survivor locked, later invalidated)
A7 R3                  PASS 9/9, 0 blocking (87f7fa7)
announcement ledger    pinned sha256 169b9e447f01ba0114396a3f26f208f5
                       761008a6ce6e30873e3b6642f8cf895 — 159 rows:
                       47 EVIDENCED (US 22/22 INSTANT, GB 21/22 DAY,
                       JP 4/5 DAY), 112 conservative-unevidenced (LATER
                       bound, never earlier)
forex denominators     18 observed / 18 published; budget 0/6 for V4
survivors              0 confirmed; 1 economic observation on record:
                       FXFV3-A6-P1 policy carry — PF 1.2825 fin-adj /
                       expectancy +20.72 per trade under EVIDENCED
                       availability; contract-invalidated (STRESS_TIER_2.0
                       fail; control arm irreproducible)
S1                     SEALED_UNTOUCHED
paper/live/orders      none
workers at close       0
inherited machinery    announcement_ledger_builder / build_evidenced_
                       vintages / recompute_v3r scripts; dual-book
                       financing machinery; DST 16:00-NY calendar; USD-drift
                       gate; break-even bps reporting; fusion core c6a0576e
                       + A3-macro adapters (ECB SDMX, BIS WS_CBPOL)
```

## 1. What is closed and may not be rescued

Cumulative ancestry veto — the V2/V3 forbidden inventories plus the V3R
addition:

1. session-open momentum continuation and late-session fade (V1);
2. Tokyo-range compression and London-AM break/retest structures (V2);
3. FXFV3-A5-P1 (V3 family1) — rejected on expectancy;
4. FXFV3-A6-P1 (V3 family2) — DATA_AUTHORITY_INVALIDATED. Re-grading it,
   its evidenced-availability recompute, or any stress-relaxed, window-
   tweaked, control-swapped or threshold-adjusted descendant is rescue.

### 1.1 The carry front door — sanctioned re-entry, measured

The invalidated family left a genuine economic observation: under honest
availability the effect is still present (PF 1.2825) but failed the frozen
stress tier and its control could not run. A V4 proposal may re-enter this
region ONLY through the front door, with all of:

- a NEW mechanism framing in its own words — e.g. how the family's risk
  construction survives doubled costs BY DESIGN (financing-aware sizing,
  unwind rules that shorten exposure in cost-stressed states) — never "the
  V3 anchor with evidenced data";
- explicit disclosure that it is a **confirmatory re-entry** of an
  invalidated ancestor, recorded in the family verdict and denominator;
- availability evidence built in from day one (the V3R announcement ledger
  and vintage pipeline; no inferred stamps anywhere);
- its own falsification control whose book RUNS under evidenced semantics
  (V3R's lesson: a control that cannot execute has null evidentiary value);
- A7-N measures anchor rank correlation BOTH vs the V3 anchor as scored AND
  vs its evidenced-availability corrected books (they differ: 158 decisions,
  19 sign flips); eligibility is an audit decision on those numbers, not a
  prose argument;
- **margin-to-fail reported per gate** (program lesson P-2): a re-entering
  family that passes any gate at knife-edge is recorded as such — the V3
  arc died on exactly one thin gate.

## 2. Mission and allowed scope

V4 asks one question:

> On daily-or-slower clocks over the authorized 7-pair universe, do
> macro-conditioned mechanisms — policy-rate structure, inflation/real-rate
> structure, or the sanctioned carry re-entry — produce incremental
> after-cost information under fully evidenced availability?

Scope rules, frozen:

- **Three sanctioned information axes** (one proposal lane each, wave
  diversity binding):
  1. policy-rate / carry region (Section 1.1 conditions apply);
  2. inflation and real-rate structure — CPI/price-level differentials via
     the adopted ECB SDMX adapters (PPP-deviation and real-differential
     class mechanisms), each series carrying its own availability evidence
     (release calendars, per P-1);
  3. open axis — any literature-backed mechanism using authorized data
     within the non-forbidden space.
- **Availability evidence is absolute**: every conditioning row carries an
  evidenced stamp or the conservative LATER bound from the announcement
  ledger pattern; asserted bounds are never authorized (P-1). P0 extends
  the announcement ledger where official static sources permit (RBA, RBNZ,
  SNB, ECB were conservative-unevidenced in V3R) — extension is append-only
  and re-pinned.
- **Decision clocks daily or slower** (unchanged structural choice);
  break-even bps per cell mandatory; USD-drift gate inherited; dual books
  (price-only and financing-adjusted) with the financing term never
  manufacturing the edge (price-only sign must not invert).
- Stress multipliers applied to booked PnL (F1-fixed since V3); TECHABORT
  discipline; placebo-style controls are the house standard.
- Cost-side lesson from V3R: a family whose economics survive only because
  stress tiers were unapplied is not a survivor — the tier-2.0 book is part
  of the primary gate set, and margin-to-fail is reported per gate.

Allowed terminal outcomes:

```text
FOREX_FREE_V4_REJECT_ALL
FOREX_FREE_V4_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
FOREX_FREE_V4_BLOCKED_DATA_OR_SELECTION
FOREX_FREE_V4_BLOCKED_PRELAUNCH
FOREX_FREE_V4_INCOMPLETE_NOT_PROMOTABLE
```

## 3. Branch and worktree topology

```text
branch    orca/forex-free-v4-integration
worktree  .worktrees/forex-free-v4/integration
base      measured V3R terminal c356813f... unless intake records a newer
          owner-authorized reconciliation descendant
lanes     .worktrees/forex-free-v4/{p0-a2-avail,p0-a3-data,
          d1-a4-proposals,d1-a5-proposals,d1-a6-proposals,
          d2-a7-novelty,d2-a9-feasibility,i-family-1,i-family-2,
          q-a7-prelaunch,e-exec-1,r-reproduce,r-a7-terminal}
```

`pwd` before every `git worktree add`; never one branch in two worktrees;
one cycle = one A1 thread (verify no forex-free-v4 branch exists first).

## 4. Agent allocation and concurrency

A1 controller/sole integrator; A2 availability-evidence extension +
accounting kernel (inherit V3's, including publisher-convention
regression); A3 data authority (price series, macro series, calendars);
A4/A5/A6 one blind proposal lane each on an assigned axis, two proposals
per lane; A7 independent novelty/prelaunch/terminal (never repairs,
recomputes from bytes, audits positive results stricter); A8/A9
implementation and feasibility. Concurrency: A1 + at most three light
lanes; full pytest alone; heavy cap from a fresh probe; scored arms
serial; foreign cycles respected — `NOT_RUN_RESOURCE_CONFLICT` rather than
contention.

## 5. Phase V4-R — terminal reconciliation

A1 verifies the V3R chain (terminal SHA, A7 ancestry, verdict artifacts,
announcement-ledger pin re-hashed, denominators 18/18, S1 seal, workers
zero, clean trees, forbidden inventory including the invalidated entry),
then seeds `research/control/forex_free_v4_run/{run_contract,state,
heartbeat,event_log,forbidden_family_inventory,worktree_manifest,
lessons_register}` with the program lessons P-1..P-6 seeded alongside
cycle lessons.

## 6. Phase V4-P — availability, factory, data gates

### P0a — availability-evidence extension (A2)

Re-verify the pinned announcement ledger byte-identical; extend it
append-only with any additional officially evidenced events (RBA, RBNZ,
SNB, ECB static listings were conservative in V3R); re-pin; regenerate
evidenced vintages through the inherited pipeline with the
only-availability-differs invariant. Every macro series used downstream
carries the same per-series availability evidence (ECB release calendars;
no retrieval-time substitution).

### P1 — accounting/publication regression

Inherit the full V3/V3R kernel: cost once per fill, stress multipliers
applied to booked PnL, dual-book columns, break-even derivation,
observed-once/replay-never, zero-position refusal, A1 serialization.

### P2 — data authority replay and coverage-first gating

Price series byte-replay (V3 snapshot convention), DST calendar re-check,
macro series coverage vs every proposed conditioning clock — published
BEFORE D1. A proposal may cite only evidenced-availability series with
funded coverage. S1 never listed, opened, hashed or copied.

### P3 — baseline invariants

Book/cash accounting; fills and frozen cost schedule; financing formula;
force-flat folds; concentration/drop-one/stress conventions; minimum
decisions; resource formula and timeout; the daily-or-slower clock rule.
No PnL in Phase P.

## 7. Phase V4-D1 — blind proposal generation

Three lanes from the same `V4_PROPOSAL_WAVE_SHA`, one assigned axis each.
Full packet discipline (mechanism + falsifiable prediction; literature;
PIT observable with EVIDENCED availability; universe/warmup/clock/holding/
fills; anchor, one neighbour, one placebo-style causal control RUNNABLE
under evidenced semantics; incremental test; base and stress costs;
turnover and sample floor; drop-one design; failure interpretation;
source-to-test map; margin-to-fail expectations stated ex ante; signed
outcome-blind attestation). Proposal agents receive the forbidden packet
(including the invalidated-entry conditions) and no per-arm outcome files.

## 8. Phase V4-D2 — independent audit and selection

A7-N: novelty/anti-rescue with measured rank correlations against every
forbidden family, BOTH V3 family2 anchor variants (as-scored and
corrected), and the V1/V2 ancestors; the Section 1.1 re-entry decision is
made on those numbers. A9-F: per-proposal availability-evidence audit,
coverage, schedule breadth, cost arithmetic with tier-2.0 explicitly in
the primary set, control runnability under evidenced semantics, drop-one
meaningfulness, implementation risk — no PnL. Frozen rubric as V3; exactly
three arms per family; maximum six scored cells; unused slots never
reassigned.

## 9. Phase V4-I — implementation

Full V3 evidence list, plus: availability-lag mutation tests per
conditioning series; stress-tier scaling tests proving multipliers reach
booked PnL; control-runs-under-evidenced-semantics tests (a control whose
book cannot execute is a design failure, not a pass); margin-to-fail
computed and frozen per gate at implementation time. A1 integrates one
family at a time.

## 10. Phase V4-Q — freeze and prelaunch

Full V3 sequence: all suites; six-arm dummy dry-run into a temporary
ledger with recursive PnL-leak scanning (handbook §17.2); digests pairwise
unique; data/availability/announcement-ledger hashes; budget 0/6; full
pytest alone; compileall; `git diff --check`; fresh resource probe; freeze
`FOREX_FREE_V4_W4`; detached equal twins; byte-identical read-only data
and empty ledger authority. Independent A7 recomputes; only
`FOREX_FREE_V4_S0_LAUNCH_AUTHORIZED` with zero unresolved HIGH/CRITICAL
reaches the owner. HARD STOP until the owner types:

```text
GO FOREX V4 SCORED EXECUTION
```

## 11. Phase V4-E — maximum six scored cells

Serial per family (anchor, neighbour, control); TECHABORT discipline;
per-cell reporting per handbook §18.3 including margin-to-fail per gate.
Any crash before a scored metric exists is a TECHABORT (zero budget,
driver-only fix, A7 delta authorization); after a metric exists it is
observed and published whatever its value.

## 12. Stage-A gates (frozen ex ante; V3 set with margin reporting)

After-cost anchor expectancy > 0 (financing-adjusted book governs;
price-only reported and must not invert sign); PF >= 1.10; >= 2/3 folds
positive; MDD within the frozen USD ceiling; fold-positive share <= 50%;
pair concentration within the frozen ceiling; stress positive WITH tier
multipliers applied — **tier 2.0 is a primary gate, not an appendix**;
meaningful drop-one pair and fold; USD-drift within bounds; overall
incremental alpha > 0; neighbour supports; the placebo/causal control does
not reproduce under its preregistered rule AND runs to completion under
evidenced semantics; reproduction ALL_MATCH (self-consistency only — P-4);
zero unresolved HIGH/CRITICAL. Positive raw PnL never overrides failed
incremental alpha or a firing control.

## 13. Reproduction, terminal closeout and program statistics

Reproduce every cell from the detached twin; exact match except volatile
metadata. Terminal A7 recomputes the C-chain, audits POSITIVE results
STRICTER than negative (§20.2), and the four-layer test (mechanical/data/
statistical/economic) precedes any SURVIVORS.md entry — a PIT-unevidenced
survivor is recorded provisional, never PIT-audited. The terminal report
updates the program statement (18 + V4 cells) with DSR/PBO where the
per-period series permit. S1 stays sealed; no paper/live.

## 14. Required commands and reporting

`.venv/bin/python`; forex asset suites, protocol contracts, data-fusion
compatibility suite, full `pytest -q` alone, `compileall`, `git diff
--check`, `git status --porcelain=v1`. Every gate reports command, exit
code, stdout/stderr paths, full HEAD, input/output hashes, expected/
observed, verdict, blocker, tree status. Owner checkpoints: intake; P
gates incl. announcement-ledger extension; proposals and audits (including
any carry re-entry decision, reported to the owner with the measured rho
numbers); selection freeze; implementations and W4; A7 prelaunch; family
completions after GO; reproduction and terminal A7.

## 15. Hard boundaries

- No new signup, key or purchase; adopted keyless sources only; asserted
  availability never authorized.
- No S1 access, paper, live, orders or credentials.
- No raw-data commit; snapshots gitignored with hash manifests.
- No optimizer, scored grid, threshold weakening, family substitution,
  cluster-padding, or re-grading of the invalidated family in any form.
- No rewriting prior ledgers, artifacts or terminal reports.
- No push, main merge, history rewrite or worktree deletion without owner
  instruction.
- Gates report PASS/FAIL/NOT_RUN/BLOCKED. A correct negative result is
  preferable to a fabricated or thin survivor.

## 16. First report from a fresh A1

```text
measured UTC
root path / branch / full HEAD / porcelain
V3R terminal SHA + verdict ancestry + announcement-ledger pin re-hashed
forex denominator 18/18, budget 0/6, S1 seal, workers
price-series + calendar + macro-series availability-evidence status
integration worktree path / branch / base SHA
RAM / CPU / disk / preliminary heavy cap / foreign-cycle status
GO/NO_GO for reconciliation and factory-only phases
```

A1 continues autonomously through prelaunch and stops before the first
scored V4 cell unless a real blocker occurs earlier.
