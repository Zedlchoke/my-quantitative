# FOREX-FREE-V3 — MACRO-CONDITIONED, LOW-FREQUENCY DISCOVERY AFTER TWO REJECT-ALL CYCLES

> Owner plan for the next Forex research cycle, dated 2026-09-04.
>
> `PLAN_forex.md` (F1) and `PLAN_forex_v2.md` (V2) are closed historical
> authorities and must not be rewritten. This file starts V3 only. A correct
> `FOREX_FREE_V3_REJECT_ALL` is a successful research run.

## 0. Frozen starting point

Measured terminal authority (A1 must remeasure; drift affecting identity,
counters, data authority or S1 is an intake blocker):

```text
completed branch       orca/forex-free-v2-integration
cycle-close SHA        2d68c81c5b4aae9b5ad67025b948598db3ba5695
terminal verdict       FOREX_FREE_V2_REJECT_ALL
terminal A7            FOREX_FREE_V2_TERMINAL_AUDIT_PASS (C1..C8; 1 MEDIUM
                       + 3 LOW + 2 INFO, none verdict-changing)
terminal report SHA    a86e3f794a025e327b670c2c5fecc5e9abfd3431
V2 cells               6 observed / 6 published / 6 reproduced byte-identical
V2 W2                  a68764d8f1501b27d07840de6a8fce11ec8eaa5b (twins intact)
forex denominators     12 observed / 12 published (V1 6 + V2 6)
survivors              0 across the whole forex program
S1                     SEALED_UNTOUCHED
paper/live/orders      none
workers at close       0
Data Fusion V1 core    FROZEN at MULTISOURCE_DATA_CORE_SHA
                       c6a0576ef98dd4392e90805c8ba33821da62eabc
                       (A3-macro lane cba3549: ECB SDMX + BIS WS_CBPOL
                       keyless adapters; A4-forex lane 8a3187f: TrueFX
                       monthly tick archive adapter, CANDIDATE_NOT_AUTHORIZED)
```

## 1. What is closed and may not be rescued

Cumulative ancestry veto, in addition to the V2 forbidden inventory:

1. session-open momentum continuation and late-session fade at intraday
   clocks (V1: 11k+ trades, PF 0.849, cost-dominated);
2. Tokyo-range compression → London-morning expansion (V2 family1);
3. London-AM range break with retest-hold confirmation (V2 family2);
4. any session/clock/instrument tweak, cost exemption, pair subset or
   threshold relaxation whose purpose is to rescue any row above.

Scientific basis: V1 died to costs (positive-gross families would still have
needed break-even headroom they lacked); V2 died **before costs** — all six
cells had negative break-even bps, i.e. negative gross edge, with USD-drift
ruled out (|corr| <= 0.072). Session-structure information in free G10
bid/mid data is exhausted at these frequencies: 12 mechanisms, 0 survivors.

### 1.1 Front-door note (no confirmatory region exists in forex)

Unlike crypto/stocks, forex has **no shadow effect to re-enter**: no control
arm in V1/V2 earned positive raw PnL. Therefore no confirmatory-region
exception applies. Every V3 proposal must be a genuinely new mechanism with
measured decorrelation against the forbidden set; A7-N applies the standard
ancestry veto with rank/feature comparison where data permits.

## 2. Mission and allowed scope

V3 asks one question:

> Can a lower-frequency (daily-or-slower), macro-conditioned mechanism —
> using point-in-time policy-rate and official-rate series adopted through
> Data Fusion — produce incremental after-cost information on the authorized
> 7-pair free-data universe?

Scope rules, frozen:

- **Decision clock is daily or slower.** No intraday decision clocks. This
  is the structural response to two cost-dominated/high-noise intraday
  cycles; it is chosen ex ante, not after seeing V3 data.
- **Adopted sources**: the fusion A3-macro lane (ECB SDMX, BIS WS_CBPOL
  policy rates with effective-date semantics) cherry-picked before the data
  and selection freeze, plus the existing authorized Twelve-Data-derived
  daily research series. TrueFX ticks stay CANDIDATE_NOT_AUTHORIZED unless
  a separate owner license decision says otherwise; no signup, no download
  outside the authorized set.
- **Carry-adjacent proposals** (rate-differential positioning) are
  admissible only with the financing authority resolved honestly: financing
  modelled from policy-rate differentials with effective-date PIT semantics
  frozen ex ante and the approximation disclosed in the proposal, or an
  owner-authorized financing source. Every scored book must carry BOTH a
  price-only PnL and a financing-adjusted PnL so A7 can verify the financing
  term does not manufacture the edge.
- **Mandatory F1 remediation (V2 terminal MEDIUM)**: stress-tier cost
  multipliers must be applied to booked stress PnL. Regression-pinned in
  P1 before any proposal selection.
- **Break-even cost reporting** (the V2 innovation) is mandatory per cell:
  publish break-even bps so a reject is attributable to cost vs absence of
  gross edge.
- The USD-drift diagnostic gate frozen in V2 carries forward unchanged.

Allowed terminal outcomes:

```text
FOREX_FREE_V3_REJECT_ALL
FOREX_FREE_V3_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
FOREX_FREE_V3_BLOCKED_DATA_OR_SELECTION
FOREX_FREE_V3_BLOCKED_PRELAUNCH
FOREX_FREE_V3_INCOMPLETE_NOT_PROMOTABLE
```

## 3. Branch and worktree topology

```text
branch    orca/forex-free-v3-integration
worktree  .worktrees/forex-free-v3/integration
base      measured cycle-close SHA 2d68c81... unless intake records a newer
          owner-authorized reconciliation descendant
lanes     .worktrees/forex-free-v3/{p0-a2-fusion,p1-a2-accounting,
          p1-a3-data,d1-a4-proposals,d1-a5-proposals,d1-a6-proposals,
          d2-a7-novelty,d2-a9-feasibility,i-family-1,i-family-2,
          q-a7-prelaunch,e-exec-1,r-reproduce,r-a7-terminal}
```

Never check out one branch in two worktrees. Every lane records path, branch,
base SHA, head SHA, ownership and disposition in
`research/control/forex_free_v3_run/worktree_manifest.json`.

## 4. Agent allocation and concurrency

- A1: controller, only integrator, freezer, counter owner, publisher;
- A2: fusion adoption, accounting/publication regression, F1 remediation;
- A3: PIT data, calendar/DST, window, macro-series and financing authority;
- A4/A5/A6: two blind proposals each, six total;
- A7: independent novelty, prelaunch and terminal audits; never repairs;
- A8/A9: family implementation or feasibility as assigned.

Concurrency: A1 plus at most three light lanes; full pytest alone; on the
8 GB Mac the default heavy cap is one; scored arms serial; only A1 appends
the canonical ledger. One cycle = one A1 thread; A1 verifies no cycle branch
exists before creating anything (V5 dispatch lesson L8).

## 5. Phase V3-R — terminal reconciliation

A1 verifies: V2 cycle-close SHA and A7 ancestry; 6/6 V2 artifacts with
byte-identical twin ledgers; denominator 12/12; budget fully consumed 6/6;
S1 seal, workers zero, clean trees, no active scorer; twins intact at W2;
forbidden inventory intact; the V2 MEDIUM F1 and LOW findings carried into
the new lessons register. Create
`research/control/forex_free_v3_run/{run_contract,state,heartbeat,event_log,
forbidden_family_inventory,worktree_manifest,lessons_register}` with budget
`0/6`, V3 counters at zero, historical 12/12 preserved separately.

## 6. Phase V3-P — adoption, factory and data gates

### P0 — Data Fusion macro adoption

A2 cherry-picks the frozen core plus the A3-macro adapters (path-limited,
byte-identical code to the lane heads), then proves: policy-rate rows map
onto the record schema with true effective/availability semantics; a
decision at T can never read a row whose `available_time_utc > T`
(regression-pinned); rate-change events surface as dated vintages; no V2
frozen artifact, digest, counter or ledger byte changes.

### P1 — accounting regression with F1 remediation

Inherit the V2 kernel (cost once per side, cash != pair, publish flock
once-only) and add: **stress-tier cost multipliers applied to booked stress
PnL with a hand-computed fixture proving tier 1.5 and tier 2.0 differ from
base**; price-only and financing-adjusted PnL carried as separate immutable
columns; break-even bps derived from the same cost kernel.

### P2 — data authority: series, calendar, financing disposition

A3 replays the authorized price series byte-for-byte (156-file snapshot
convention), re-verifies the DST-aware 16:00-NY flat-bar calendar across
marches, then extends authority to macro series: per-series license
evidence, availability stamps, warmup coverage for daily/weekly clocks, and
an explicit AUTHORIZED / CANDIDATE_NOT_AUTHORIZED disposition. If a
proposal's economics depend on financing precision beyond policy-rate
differentials, mark it ineligible unless the owner authorizes a source.

### P3 — baseline invariants

Freeze before proposals: book/cash accounting; fills and the frozen cost
schedule; financing adjustment formula (for carry-adjacent arms); force-flat
fold boundaries; concentration, drop-one-pair, drop-one-fold and stress
conventions; minimum decisions/positions; resource formula and timeout; the
daily-or-slower decision-clock rule as a hard precondition. No PnL is
computed in Phase P.

## 7. Phase V3-D1 — blind proposal generation

A4, A5 and A6 branch from the same `V3_PROPOSAL_WAVE_SHA`. Each writes
exactly two outcome-blind proposals under the full packet discipline
(mechanism and falsifiable prediction; literature; PIT observable with
availability semantics; universe/warmup/clock/holding/fills; anchor, one
neighbour, one causal negative control; incremental test; base and stress
costs with the F1-fixed multiplier application; expected turnover and sample
floor; drop-one design; failure interpretation; source-to-test map; signed
outcome-blind attestation). At least three of the six proposals must
condition on adopted macro series. Proposal agents receive the forbidden
packet and no per-arm outcome files.

## 8. Phase V3-D2 — independent audit and selection

A7-N: novelty and anti-rescue with measured rank/feature similarity against
every forbidden family; renamed or inverted old signals are INELIGIBLE. A9-F:
PIT coverage and warmup on the real snapshot, schedule count and breadth,
cap/gross/net feasibility, frozen-cost turnover arithmetic with break-even
headroom check (a proposal whose expected turnover cannot clear its own
cost band at plausible gross edges is infeasible), control identifiability,
drop-one meaningfulness, implementation risk — all without PnL.

A1 selects at most two families with the frozen rubric: no novelty/rescue
veto; authorized data PASS; identifiable control test; feasibility PASS;
strongest source-to-test trace; lowest implementation risk; lexicographic
hypothesis-ID tie-break. Exactly three arms per family; maximum six scored
cells; unused slots never reassigned.

## 9. Phase V3-I — implementation

One lane per selected family from the selection-freeze SHA, with the full
evidence list: hand-computed feature/target goldens; PIT/no-lookahead
mutation tests including macro availability lag; next-session fills;
deterministic double generation; DST calendar correctness; control-cannot-
equal-anchor; cap/gross/net/cash invariants; cost-once plus stress-
multiplier application checks; price-only vs financing-adjusted separation
tests; schedule-only feasibility on the real snapshot; non-vacuous drop-one;
dummy publication/refusal/replay with zero scored metrics. A1 integrates one
family at a time, targeted tests after each pick.

## 10. Phase V3-Q — freeze and prelaunch

A1 runs: forex V3 and compatibility suites; six-arm dummy dry-run into a
temporary ledger; exact arm digests, pairwise unique; data, calendar and
macro-series hashes; zero real scored artifacts, budget 0/6; full pytest
alone, compileall, `git diff --check`; fresh resource probe; freeze
code-bearing `FOREX_FREE_V3_W3`; detached equal-twin execution/reproduction
trees; byte-identical read-only data (price snapshot plus macro series) and
empty ledger authority.

Independent A7 recomputes the chain; only
`FOREX_FREE_V3_S0_LAUNCH_AUTHORIZED` with zero unresolved HIGH/CRITICAL
reaches the owner. A1 stops before the first scored cell until the owner
types:

```text
GO FOREX V3 SCORED EXECUTION
```

## 11. Phase V3-E — maximum six scored cells

Serial per family: anchor, neighbour, causal control. No tests beside a
heavy worker; A1 serializes publication. Any crash before a scored metric
exists is a TECHABORT (forensics, zero budget, driver-only fix, A7 delta
authorization); after a metric exists it is observed and published whatever
its value. Each score records input/code/arm hashes, positions, fills,
costs, turnover, financing adjustment, price-only AND financing-adjusted
PnL, break-even bps, folds, concentration, stresses (multipliers applied),
drop-one, observed/publication events and the canonical digest.

## 12. Stage-A gates (frozen ex ante)

A family must satisfy every applicable gate:

- after-cost anchor expectancy > 0 (financing-adjusted book; price-only book
  also reported);
- PF >= 1.10;
- at least 2/3 chronological folds positive;
- MDD within the frozen USD ceiling;
- largest fold-positive share <= 50%;
- pair positive-PnL share within the frozen ceiling; no single pair carries
  the book;
- stress PnL > 0 with tier multipliers actually applied (F1-fixed);
- meaningful drop-one pair and fold survival;
- USD-drift diagnostic within the frozen bound (inherited from V2);
- overall incremental alpha > 0 vs the frozen benchmark treatment;
- neighbour supports the same mechanism;
- the causal control does not reproduce it under its preregistered rule;
- financing term does not manufacture the edge (price-only book must not
  invert the sign of the anchor's expectancy);
- independent reproduction ALL_MATCH;
- zero unresolved HIGH/CRITICAL.

Positive raw PnL never overrides failed incremental alpha or a firing
control.

## 13. Reproduction and terminal closeout

Reproduce every computed cell from the detached twin in fresh processes;
exact match except volatile metadata. Terminal A7 independently checks the
C1..C8 chain (pin/twin integrity, digest recomputation, gates recomputed
from runner source, trade reconciliation vs schedule counts, V1/V2 ledgers
unchanged, denominator math, S1 seal, deployment boundaries, workers zero,
clean trees). The terminal report updates the program statement: observed
12 + V3 cells, published 12 + V3 cells. If a survivor exists, freeze it for
a future owner-approved S1 plan; do not open S1 and do not paper/live trade
in V3.

## 14. Required commands and reporting

Use `.venv/bin/python`. A1 discovers exact test names after implementation;
at minimum the forex asset suites, protocol contracts, data-fusion
compatibility suite, full `pytest -q` alone, `compileall`, `git diff
--check`, `git status --porcelain=v1`. Every gate reports command, exit
code, stdout/stderr paths, full HEAD, input/output hashes, expected/
observed, verdict, blocker, tree status.

Owner checkpoints: intake/reconciliation; P gates incl. fusion adoption and
F1 remediation; six proposals and audits; selection freeze; implementations
and W3; A7 prelaunch; each completed family after GO; reproduction and
terminal A7.

## 15. Hard boundaries

- No paid data; no key/signup or new download without an owner
  data-authority decision; TrueFX stays unauthorized absent one.
- No S1 access, paper, live, orders or credentials.
- No raw-data commit.
- No optimizer, scored grid, threshold weakening, family substitution or
  result-aware retrofit of Data Fusion.
- No rewriting prior ledgers, artifacts or terminal reports.
- No push, main merge, history rewrite or worktree deletion without owner
  instruction.
- No percentage-complete claims; gates report PASS/FAIL/NOT_RUN/BLOCKED.
- A correct negative result is preferable to a fabricated survivor.

## 16. First report from a fresh A1

```text
measured UTC
root path / branch / full HEAD / porcelain
V2 cycle-close SHA + terminal A7 ancestry
forex denominator 12/12 and budget 0/6
S1 seal and active worker scan (foreign-cycle workers noted)
price-series + calendar authority + fusion-core SHA + macro lane heads
integration worktree path / branch / base SHA
RAM / CPU / disk / preliminary heavy cap
GO/NO_GO for reconciliation and factory-only phases
```

A1 continues autonomously through prelaunch and stops before the first scored
V3 cell unless a real blocker occurs earlier.
