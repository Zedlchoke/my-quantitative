# STOCKS-FREE-V6 — SINGLE-NAME PIT EQUITY PANEL: F1 REMEDIATION AND FUNDAMENTALS-CONDITIONED DISCOVERY

> Owner plan for the next Stocks research cycle, dated 2026-09-05.
>
> `PLAN_stocks.md` (V2/V2R/V3), `PLAN_stocks_v4.md` (V4) and the V5 cycle
> record are closed historical authorities and must not be rewritten. This
> file starts V6 only. A correct `STOCKS_FREE_V6_REJECT_ALL` — or an honest
> `STOCKS_FREE_V6_BLOCKED_DATA_AUTHORITY` — is a successful research run.

## 0. Frozen starting point

Measured terminal authority (A1 must remeasure; drift affecting identity,
counters, data authority or S1 is an intake blocker):

```text
completed branch       orca/stocks-free-v5-integration
terminal SHA           436050ad6c2b7eb94579b43f7dcff25f90cbd889
terminal verdict       STOCKS_FREE_V5_REJECT_ALL
terminal A7            STOCKS_FREE_V5_REJECT_ALL_CONFIRMED
                       (audit bc5827e6a494333fca7191a793d8aa2cc86f9cd7;
                       independent recompute, 0 HIGH/CRITICAL)
V5 cells               3 observed / 3 published / 3 reproduced EXACT_MATCH
stocks denominators    21 observed / 21 published (V2 6 + V3 6 + V4 6 + V5 3)
survivors              0
S1                     SEALED_UNTOUCHED
paper/live/orders      none
workers at close       0
inherited assets       Data Fusion core c6a0576e... adopted byte-identical;
                       SEC EDGAR authority: 410 filers / 3.82M records
                       through audits A1–A8; pit_conditioning.py canonical
                       bridge (conditioning-lag + survivorship-aware
                       aggregation); the F1 coverage-collapse finding
                       preregistered for this cycle
```

## 1. What is closed and may not be rescued

Cumulative ancestry veto — the V3/V4/V5 forbidden inventories in full, plus:

1. sector relative-strength / 12-1 momentum and inversions (V2);
2. long-only trend / SMA200 / vol-targeted trend-defense (V2);
3. idiosyncratic shock reversal, turn-of-month and calendar variants (V3);
4. participation-shift and semivariance-shape pricing (V4);
5. cross-sector coupling at quarterly clocks (V5);
6. the vol-level shadow region stays **measured-closed** (V5: rho 0.319 >
   0.20 at the Section 1.1 front door). Re-entry requires a formulation
   whose anchor rank decorrelates below 0.20 vs BOTH the V4 semivariance
   anchor and the V4 vol-level control — measured before selection, never
   argued in prose.

## 2. Mission and allowed scope

V5 could not test its core question: all four SEC-conditioned proposals died
at F1 (single-vintage coverage collapse). V6 asks the question properly:

> On a survivorship-aware single-name PIT equity panel — fundamentals with
> evidenced multi-vintage coverage, prices from an authorized free source —
> do PIT-fundamentals-conditioned mechanisms produce incremental after-cost
> information beyond SPY/sector beta?

Three data legs, each fail-closed:

1. **F1 remediation (binding, first)**: diagnose why single-vintage coverage
   collapsed against the S0 window; rebuild the fundamentals panel as
   MULTI-VINTAGE point-in-time facts (SEC company-facts filing history /
   submissions clocks) with a per-field coverage census published BEFORE any
   proposal is invited. The conditioning clocks a proposal may cite are
   exactly those the census funds.
2. **Single-name price authority**: the 12-ETF snapshot does not carry
   single-name prices. Registered candidates: Stooq daily OHLCV (free,
   keyless), Massive Basic (cross-check only, 2-year depth). Each source
   must pass license capture, PIT/availability evidence (per handbook §11:
   retrieved_time never substitutes for availability), corporate-action
   reconciliation against issuer distributions (L7), and the coverage census
   — or is recorded UNAVAILABLE_FAIL_CLOSED / CANDIDATE_NOT_AUTHORIZED.
   Mixing sources into one series requires a frozen conflict policy with
   per-row provenance.
3. **Survivorship-aware cohort**: constructed from SEC submissions status
   history (ticker changes, delistings) with identity mapping valid at each
   decision time; delisted names keep their history and are never silently
   dropped.

Scoring scope (conditional on the data gates passing):

- universe: the authorized filer panel with a frozen liquidity floor chosen
  BEFORE returns are examined;
- decision clocks: weekly or slower rebalances; a frozen turnover ceiling
  with an equity cost model re-derived for single names (spread/impact by
  liquidity band, stress tiers applied to booked PnL — F1-forex lesson);
- at least three of six blind proposals must condition on PIT fundamentals;
  the remainder may use authorized price/volume fields within the
  non-forbidden space;
- wave diversity: each proposal lane is assigned a distinct information axis
  before writing (V13 lesson), and two selected families must come from
  different clusters.

Allowed terminal outcomes:

```text
STOCKS_FREE_V6_REJECT_ALL
STOCKS_FREE_V6_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
STOCKS_FREE_V6_BLOCKED_DATA_AUTHORITY
STOCKS_FREE_V6_BLOCKED_SELECTION_INSUFFICIENT
STOCKS_FREE_V6_BLOCKED_PRELAUNCH
STOCKS_FREE_V6_INCOMPLETE_NOT_PROMOTABLE
```

`BLOCKED_DATA_AUTHORITY` with full evidence is a legitimate close (handbook
§32): if the price source or the F1 remediation fails, closing blocked is
preferable to scoring a degraded panel.

## 3. Branch and worktree topology

```text
branch    orca/stocks-free-v6-integration
worktree  .worktrees/stocks-free-v6/integration
base      measured terminal SHA 436050ad... unless intake records a newer
          owner-authorized reconciliation descendant
lanes     .worktrees/stocks-free-v6/{p0-a2-f1remedy,p0-a3-prices,
          p1-a2-accounting,d1-a4-proposals,d1-a5-proposals,d1-a6-proposals,
          d2-a7-novelty,d2-a9-feasibility,i-family-1,i-family-2,
          q-a7-prelaunch,e-exec-1,r-reproduce,r-a7-terminal}
```

`pwd` before every `git worktree add` (L8-adjacent discipline); never one
branch in two worktrees; every lane records itself in the manifest.

## 4. Agent allocation and concurrency

Standard roles: A1 controller/sole integrator; A2 F1 remediation +
accounting (inherit the V4/V5 P1 suite including L9 publisher-convention
regression); A3 price authority + coverage census + availability evidence;
A4/A5/A6 blind proposals on assigned distinct axes; A7 independent
novelty/prelaunch/terminal (never repairs, recomputes from bytes); A8/A9
implementation/feasibility. Concurrency: A1 + at most three light lanes;
full pytest alone; heavy cap from a fresh probe; scored arms serial; one
cycle = one A1 thread (verify no v6 branch exists first).

## 5. Phase V6-R — terminal reconciliation

A1 verifies the V5 chain (terminal SHA, A7T ancestry, 3/3 artifacts,
EXACT_MATCH reproduction, denominator 21/21, budget 3/6 with 3 slots
permanently unused, S1 seal, workers zero, clean trees, forbidden
inventories intact), then creates
`research/control/stocks_free_v6_run/{run_contract,state,heartbeat,event_log,
forbidden_family_inventory,worktree_manifest,lessons_register}` with budget
`0/6`, V6 counters at zero, historical 21/21 preserved separately, and L1–L9
seeded.

## 6. Phase V6-P — data authority first, factory second

### P0a — F1 remediation (A2)

Reproduce the F1 census on the inherited panel; identify the collapse
mechanism (vintage rule, sanitizer, filer coverage, window edges); rebuild
as multi-vintage PIT facts; publish the per-field coverage census and the
list of fundable conditioning clocks. No proposal may cite an unfunded
clock.

### P0b — single-name price authority (A3)

Per source: license/entitlement capture; availability-evidence table
(evidenced vs asserted vs unevidenced — asserted bounds are never
authorized, the forex-V3 lesson); download hygiene (fail-loud, resumable,
hash-pinned raw bytes; no download beside a heavy worker); corporate-action
cross-check against issuer distributions (L7); coverage census vs the S0
window; a frozen conflict policy if more than one source is authorized.

### P1 — accounting/publication regression

Inherit the full V4/V5 suite: CASH exclusion, cost-once, one turnover
convention, byte-exact digests, append-only corrections, observed-once,
zero-position refusal, A1 serialization, the L9 ledger-publisher convention
regression, and the equity cost model with stress multipliers applied to
booked PnL.

### P2 — coverage-first gating

Every adopted dataset: hashes, window coverage, warmup vs every proposed
clock, calendar/DST, identity/delisting mapping, vintages, and an explicit
AUTHORIZED / CANDIDATE_NOT_AUTHORIZED / UNAVAILABLE_FAIL_CLOSED per source
and per field — published BEFORE D1. The V5 lesson is binding: coverage
collapse is discovered at P2, never at D2.

### P3 — baseline invariants

Book/cash accounting; fills and the frozen equity cost schedule by liquidity
band; force-flat fold boundaries; SPY and sector-factor residual treatment;
concentration, drop-one (name AND fold), stress conventions; minimum
decisions/positions; resource formula and timeout. No PnL in Phase P.

## 7. Phase V6-D1 — blind proposal generation

Three lanes from the same `V6_PROPOSAL_WAVE_SHA`, each pre-assigned a
distinct information axis from the P2-funded set. Full packet discipline
(mechanism + falsifiable prediction; literature; PIT observable with
EVIDENCED availability; universe/warmup/clock/holding/fills; anchor, one
neighbour, one causal negative control — placebo-style controls that
reproduce the book shape without the mechanism are the house standard after
seven falsification-by-control rejections; incremental test vs SPY/sector
context; base and stress costs; turnover and sample floor; drop-one design;
failure interpretation; source-to-test map; signed outcome-blind
attestation). Proposal agents receive the forbidden packet and no per-arm
outcome files.

## 8. Phase V6-D2 — independent audit and selection

A7-N: novelty/anti-rescue with measured rank correlation against every
forbidden family AND the V4 control arms; cross-cluster measurement (two
selected families from different clusters); the shadow-region rho gate.
A9-F: PIT coverage per proposal, schedule breadth, liquidity-band cost
arithmetic with break-even headroom, control identifiability (a control
rank-identical to its anchor cannot identify anything), drop-one
meaningfulness, implementation risk — no PnL. Frozen rubric and selection
freeze as V4/V5; exactly three arms per family; maximum six scored cells;
unused slots never reassigned.

## 9. Phase V6-I — implementation

One lane per selected family with the full evidence list inherited from
V4/V5, plus: multi-vintage availability-lag mutation tests; liquidity-band
cost-scaling tests (cost linear in fills, never in holding days — L-V14-0);
placebo-control-cannot-equal-anchor; deterministic double generation. A1
integrates one family at a time with targeted tests after each pick.

## 10. Phase V6-Q — freeze and prelaunch

Full V5 sequence: all suites; six-arm dummy dry-run into a temporary ledger
with recursive PnL-leak scanning (handbook §17.2); digests pairwise unique;
data/coverage/availability hashes; budget 0/6; full pytest alone; compileall;
`git diff --check`; fresh resource probe; freeze `STOCKS_FREE_V6_W1`;
detached equal twins; byte-identical read-only data and empty ledger
authority. Independent A7 recomputes; only
`STOCKS_FREE_V6_S0_LAUNCH_AUTHORIZED` with zero unresolved HIGH/CRITICAL
reaches the owner. HARD STOP until the owner types:

```text
GO STOCKS V6 SCORED EXECUTION
```

## 11. Phase V6-E — maximum six scored cells

Serial per family (anchor, neighbour, control); TECHABORT discipline;
per-cell reporting per handbook §18.3. Each score records the full V5 field
set plus liquidity-band cost breakdown and fundamentals-vintage provenance
per decision.

## 12. Stage-A gates (frozen ex ante; V4/V5 set carried forward)

After-cost anchor expectancy > 0; PF >= 1.10; >= 2/3 folds positive;
MDD <= 15%; largest fold-positive share <= 50%; name positive-PnL share
within the frozen ceiling (single-name books: no one name carries the
book); stress positive with multipliers applied; meaningful drop-one name
and fold; risk-matched excess positive in >= 2/3 folds; overall incremental
alpha > 0; neighbour supports; the placebo/causal control does not
reproduce; reproduction ALL_MATCH; zero unresolved HIGH/CRITICAL. Positive
raw PnL never overrides failed incremental alpha or a firing control.

## 13. Reproduction, terminal closeout and program statistics

Reproduce every cell from the detached twin; exact match except volatile
metadata. Terminal A7 recomputes the C-chain and audits POSITIVE results
STRICTER than negative ones (handbook §20.2). The terminal report updates
the program statement (21 + V6 cells) and reports DSR / PBO over the
published stocks program. Any survivor is evaluated through the four-layer
test (mechanical / data / statistical / economic) BEFORE any
SURVIVORS.md entry; a survivor without evidenced PIT authority is recorded
provisional, never PIT-audited. S1 stays sealed; no paper/live.

## 14. Required commands and reporting

`.venv/bin/python`; stocks asset suites, protocol contracts, data-fusion
compatibility suite, full `pytest -q` alone, `compileall`, `git diff
--check`, `git status --porcelain=v1`. Every gate reports command, exit
code, stdout/stderr paths, full HEAD, input/output hashes, expected/
observed, verdict, blocker, tree status. Owner checkpoints: intake; P
gates incl. F1 remediation census and price-source authority; proposals
and audits; selection freeze; implementations and W1; A7 prelaunch; family
completions after GO; reproduction and terminal A7.

## 15. Hard boundaries

- No paid data; no key/signup (Stooq or otherwise) without an owner
  data-authority decision; asserted availability is never authorized.
- No S1 access, paper, live, orders or credentials.
- No raw-data commit (staged panels stay gitignored with hash manifests).
- No optimizer, scored grid, threshold weakening, family substitution,
  cluster-padding or result-aware retrofit of Data Fusion.
- No rewriting prior ledgers, artifacts or terminal reports.
- No push, main merge, history rewrite or worktree deletion without owner
  instruction (this plan does not authorize the owner-directed pushes).
- Gates report PASS/FAIL/NOT_RUN/BLOCKED. A correct blocked close is
  preferable to scoring a degraded panel.

## 16. First report from a fresh A1

```text
measured UTC
root path / branch / full HEAD / porcelain
V5 terminal SHA + A7T ancestry
stocks denominator 21/21 and budget 0/6
S1 seal and active worker scan
inherited SEC panel + F1 census plan + price-source candidate statuses
integration worktree path / branch / base SHA
RAM / CPU / disk / preliminary heavy cap
GO/NO_GO for reconciliation and factory-only phases
```

A1 continues autonomously through prelaunch and stops before the first scored
V6 cell unless a real blocker occurs earlier.
