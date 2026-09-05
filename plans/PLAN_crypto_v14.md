# CRYPTO V14 — POSITIONING/FLOW INFORMATION SET WITH EVIDENCED AVAILABILITY

> Owner plan for the next Crypto research cycle, dated 2026-09-05.
>
> `PLAN.md` (V11/V12) and the V13 cycle record are closed historical
> authorities and must not be rewritten. This file starts V14 only. A correct
> `V14_REJECT_ALL` is a successful research run.

## 0. Frozen starting point

Measured terminal authority (A1 must remeasure; drift affecting identity,
counters, data authority or S1 is an intake blocker):

```text
completed branch       orca/v13-integration
terminal SHA           96833a8c9d616d5ee28a6eb2dbd1d50f94b4f58b
terminal A7            V13_TERMINAL_APPROVED_0_FAIL (4222a38 integrated)
V13 cells              6 observed / 6 published / 6 reproduced ALL_MATCH
V13 budget             6/9 (no third family; no slots reassigned)
V13 outcome            OITD REJECT (anchor -0.285, PF 0.879, MDD 30.5%);
                       LIQEPIS REJECT (price-only negative; COST ANOMALY:
                       per-stamp accrual charged ~3-4 orders above the
                       frozen per-fill schedule — verdict-invariant, but a
                       latent cost-once violation in the kernel)
crypto denominators    137 published / 140 observed logical
survivors              0 in the crypto program
S1                     SEALED_UNTOUCHED
paper/live/orders      none
workers at close       0
Data Fusion core       adopted byte-identical in V13 and proven live in a
                       scored cycle (MULTISOURCE_DATA_CORE_SHA c6a0576e...)
```

## 1. What is closed and may not be rescued

Cumulative ancestry veto — everything in the V12/V13 forbidden inventories,
plus the V13 additions:

1. OI term-structure / positioning-duration families (OITD and its
   near-duplicates EXITCAP, CAPVEL at rho +0.97/-0.91);
2. liquidity-episodicity families (LIQEPIS and duplicates LIQPRO rho +1.00,
   TCH rho +0.65);
3. any sign-flip, window tweak, cost exemption or granularity change whose
   purpose is to rescue a row above.

### 1.1 Shadow-effect region — front door remains open, measured

The inverted-OI-flow shadow (+0.758 raw, V12 OILEV-V2-INV control arm)
remains untested as a front-door family (V13 did not enter it). A V14
proposal may enter ONLY per the V13 terms: a new economic mechanism in its
own words; disclosure that the sign was observed in a V12 control;
confirmatory status recorded in the verdict and denominator; its own
falsification control; |rho| <= 0.20 vs the OILEV-V2 anchor AND its inverted
control; no gate relaxation.

### 1.2 Wave-diversity rule (new — V13 lesson)

V13's six blind proposals collapsed into two mechanism clusters (two pairs at
|rho| > 0.9). V14 D1 assigns each proposal lane a DISTINCT information axis
before any proposal is written (for example: positioning ratios; funding /
flow microstructure; cross-leg basis structure), and A7-N measures
cross-cluster rank correlation. Two selected families must come from
different clusters; a second family inside a selected cluster is ineligible
even if otherwise clean.

## 2. Mission and allowed scope

V14 asks one question:

> Do positioning and order-flow conditioning variables — from free, keyless
> Binance public datasets not yet used in any scored cycle — carry
> incremental after-cost information beyond benchmark context on the
> authorized universe and window?

Candidate new datasets (registered, not yet authorized):

- open-interest history at finer granularity than the staged OI set, if
  coverage suffices;
- taker buy/sell volume ratios; global and top-trader long/short account and
  position ratios (crowding indicators);
- basis / mark-index structure derivable from authorized fields.

Binding data rules, learned from V5 (SEC coverage collapse) and V3R
(inferred availability):

1. **Coverage first**: P2 probes each candidate's history depth against the
   S0 window BEFORE any proposal is invited. A source whose coverage cannot
   fund a stated conditioning clock is recorded
   `COVERAGE_INSUFFICIENT_FAIL_CLOSED` in P2 and is excluded from proposal
   briefs — never discovered at D2 after proposals are written.
2. **Evidenced availability, never inferred**: every adopted row carries an
   availability stamp backed by provider documentation or archived evidence
   (endpoint semantics, publication lag), recorded in a P2
   availability-evidence table. An asserted upper bound without evidence is
   `CANDIDATE_NOT_AUTHORIZED` for scored use. (The forex V3 downgrade exists
   because this rule did not exist there.)
3. No signup, no credentials, no paid source. The ILLIQ replication
   re-opening rule from V13 carries forward unchanged (owner data decision
   required).

Allowed terminal outcomes:

```text
V14_REJECT_ALL
V14_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
V14_BLOCKED_DATA_OR_SELECTION
V14_BLOCKED_PRELAUNCH
V14_INCOMPLETE_NOT_PROMOTABLE
```

## 3. Branch and worktree topology

```text
branch    orca/v14-integration
worktree  .worktrees/crypto/v14/integration
base      measured V13 terminal 96833a8... unless intake records a newer
          owner-authorized reconciliation descendant
lanes     .worktrees/crypto/v14/{p1-a2-accounting,p1-a3-data,
          d1-a5-proposals,d1-a6-proposals,d1-a8-proposals,
          d2-a7n-novelty,d2-a9f-feasibility,i-family-1,i-family-2,
          q-a7-prelaunch,e-exec-1,r-reproduce,r-a7-terminal}
```

Never check out one branch in two worktrees; every lane records itself in
`research/control/v14_run/worktree_manifest.json`.

## 4. Agent allocation and concurrency

- A1: controller, only integrator, freezer, counter owner, publisher;
- A2: accounting kernel remediation and publication regression;
- A3: candidate-source probes, coverage census, availability-evidence table,
  data authority;
- A5/A6/A8: two blind proposals each on DISTINCT assigned axes, six total;
- A7: independent novelty, prelaunch, terminal audits; never repairs;
- A9: feasibility and family implementation as assigned.

Concurrency: A1 plus at most three light lanes; full pytest alone; heavy cap
from a fresh probe; scored arms serial; only A1 appends the canonical
ledger. One cycle = one A1 thread (verify no v14 branch exists first).

## 5. Phase V14-R — terminal reconciliation

A1 verifies the V13 chain (terminal SHA, A7 ancestry, 6/6 artifacts, ALL_MATCH
reproduction, denominators 137/140, budget 6/9, S1 seal, workers zero, clean
trees), reads the V13 cost-anomaly adjudication into the new lessons
register as L-V14-0 (mandatory fix), and creates
`research/control/v14_run/{run_contract,state,heartbeat,event_log,
forbidden_family_inventory,worktree_manifest,lessons_register}` with budget
`0/9`, V14 counters at zero, historical 137/140 preserved separately.

## 6. Phase V14-P — remediation, factory and data gates

### P1 — cost-kernel remediation and accounting regression (binding)

A2 fixes the per-stamp accrual defect so cost is charged exactly once per
fill — never per holding-day, never per stamp on open positions — and pins
it with hand-computed fixtures including: a many-small-positions long-hold
book whose cost scales with fills, not holding days; stress tiers that
differ from base and from each other; cost-once across replay; observed-once
/ replay-never counters; zero-position refusal; A1 append serialization.
The frozen V13 scorer is re-run on the V13 inputs and must reproduce the
V13 published numbers EXCEPT the LIQEPIS cost column, whose corrected value
is recorded as an append-only adjudication (verdict unchanged — price-only
was already negative).

### P2 — candidate-source probes and availability evidence

A3 measures, per candidate source: endpoint semantics, retrievable history
depth vs the S0 window, granularity, publication lag, license/entitlement;
produces the availability-evidence table (evidenced vs asserted vs
unevidenced) and the coverage census. The D1 proposal brief may only cite
sources marked EVIDENCED-AVAILABLE with sufficient coverage. Existing
authorized datasets are re-keyed with availability evidence to the same
standard (bar close, funding settlement, OI snapshot publication semantics).

### P3 — baseline invariants

Freeze before proposals: book/cash accounting; fills and the remediated cost
schedule; funding settlement; force-flat fold boundaries; benchmark and
BTC-beta context; concentration, drop-one, stress conventions; minimum
decisions/positions; resource formula and timeout. No PnL in Phase P.

## 7. Phase V14-D1 — blind proposal generation on assigned axes

Three lanes branch from the same `V14_PROPOSAL_WAVE_SHA`. A1 assigns each
lane a distinct information axis drawn from the EVIDENCED-AVAILABLE set.
Each lane writes exactly two proposals under the full V13 packet discipline
(mechanism and falsifiable prediction; literature; PIT observable with
EVIDENCED availability; universe/warmup/clock/holding/fills; anchor, one
neighbour, one causal negative control; incremental test; base and stress
costs under the remediated kernel; turnover and sample floor; drop-one
design; failure interpretation; source-to-test map; signed outcome-blind
attestation). Proposal agents receive the forbidden packet and no per-arm
outcome files.

## 8. Phase V14-D2 — independent audit and selection

A7-N measures novelty/anti-rescue INCLUDING cross-cluster correlation: a
proposal inside a selected family's cluster is ineligible (Section 1.2), and
the Section 1.1 shadow-region rho gate applies to any inverted-OI-flow
entry. A9-F re-verifies coverage and availability evidence per proposal,
schedule feasibility on the real snapshot, cost arithmetic under the
remediated kernel, control identifiability, drop-one meaningfulness —
without PnL. A1 selects at most two families from DIFFERENT clusters with
the frozen rubric; exactly three arms each; maximum six scored cells;
unused slots never reassigned.

## 9. Phase V14-I — implementation

One lane per selected family from the selection-freeze SHA with the full V13
evidence list, plus: a per-family cost-scaling test proving cost is linear
in fills (the L-V14-0 regression), and availability-lag mutation tests for
every adopted conditioning field. A1 integrates one family at a time.

## 10. Phase V14-Q — freeze and prelaunch

Full V13 sequence: all suites; six-arm dummy dry-run into a temporary
ledger; exact digests pairwise unique; data and availability-evidence
hashes; budget 0/9; full pytest alone; compileall; `git diff --check`; fresh
resource probe; freeze `V14_W1`; detached equal twins; byte-identical
read-only data and empty ledger authority. Independent A7 recomputes; only
`V14_S0_LAUNCH_AUTHORIZED` with zero unresolved HIGH/CRITICAL reaches the
owner. HARD STOP until the owner types:

```text
GO V14 SCORED EXECUTION
```

## 11. Phase V14-E — maximum six scored cells

Serial per family (anchor, neighbour, control); TECHABORT discipline for
pre-metric crashes (zero budget, driver-only fix, A7 delta authorization);
post-metric values are observed and published whatever they are. Each score
records the full V13 field set under the remediated cost kernel, with cost
broken out by fills vs holding terms.

## 12. Stage-A gates (frozen ex ante; V13 set unchanged)

After-cost anchor expectancy > 0; position PF >= 1.10; >= 2/3 folds
positive; largest fold-positive share <= 50%; MDD <= 20%; largest symbol
positive-PnL share <= 0.70; stress set positive with multipliers applied;
non-vacuous drop-one symbol and fold; benchmark/BTC-beta excess positive in
>= 2/3 folds; neighbour supports; the causal control does not reproduce
under its preregistered rule; reproduction ALL_MATCH; zero unresolved
HIGH/CRITICAL. Positive raw PnL never overrides failed incremental context
or a firing control.

## 13. Reproduction, terminal closeout and program statistics

Reproduce every cell from the detached twin; exact match except volatile
metadata. Terminal A7 rechecks the C-chain (pins, digests, gates from source,
trade reconciliation, unchanged historical ledgers, denominator math, S1
seal, boundaries). The terminal report updates the multiple-testing
statement — observed 140 + V14 cells — and, new for V14, reports Deflated
Sharpe Ratio and Probability of Backtest Overfitting over the published
crypto program history (S1 remains the arbiter). Any survivor is locked for
a future owner-approved S1 plan; S1 stays sealed; no paper/live.

## 14. Required commands and reporting

`.venv/bin/python`; crypto asset suites, protocol contracts, data-fusion
compatibility suite, full `pytest -q` alone, `compileall`, `git diff
--check`, `git status --porcelain=v1`. Every gate reports command, exit
code, stdout/stderr paths, full HEAD, input/output hashes, expected/
observed, verdict, blocker, tree status. Owner checkpoints: intake; P gates
incl. remediation and coverage/availability table; proposals and audits;
selection freeze; implementations and W1; A7 prelaunch; family completions
after GO; reproduction and terminal A7.

## 15. Hard boundaries

- No S1 access, paper, live, orders, credentials.
- No new source beyond registered free keyless Binance public datasets; no
  signup; asserted-without-evidence availability is never authorized.
- No optimizer, scored grid, threshold weakening, family substitution,
  cluster-padding or result-aware retrofit.
- No rewriting prior ledgers, artifacts or terminal reports; the V13 cost
  adjudication is append-only.
- No push, main merge, history rewrite or worktree deletion without owner
  instruction.
- Gates report PASS/FAIL/NOT_RUN/BLOCKED. A correct negative result is
  preferable to a fabricated survivor.

## 16. First report from a fresh A1

```text
measured UTC
root path / branch / full HEAD / porcelain
V13 terminal SHA + A7 ancestry
crypto denominators 137/140, budget 0/9
S1 seal and active worker scan
data authority + availability-evidence status per candidate source
integration worktree path / branch / base SHA
RAM / CPU / disk / preliminary heavy cap
GO/NO_GO for reconciliation and factory-only phases
```

A1 continues autonomously through prelaunch and stops before the first scored
V14 cell unless a real blocker occurs earlier.
