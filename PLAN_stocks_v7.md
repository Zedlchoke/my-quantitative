# STOCKS-FREE-V7 — PRICE-AUTHORITY PROBE UNDER THE EXISTING ENTITLEMENT, THEN FUNDAMENTALS-CONDITIONED DISCOVERY

> Owner plan for the next Stocks research cycle, dated 2026-09-05.
>
> `PLAN_stocks.md` (V2–V3), `PLAN_stocks_v4.md` (V4), `PLAN_stocks_v5.md`
> (V5) and the V6 cycle record are closed historical authorities and must not
> be rewritten. This file starts V7 only. A correct
> `STOCKS_FREE_V7_REJECT_ALL` — or an honest fast
> `STOCKS_FREE_V7_BLOCKED_DATA_AUTHORITY` at the probe — is a successful
> research run.

## 0. Frozen starting point

Measured terminal authority (A1 must remeasure; drift affecting identity,
counters, data authority or S1 is an intake blocker):

```text
completed branch       orca/stocks-free-v6-integration
terminal SHA           39250b7bb30c73f4108192add45ac9b32171bc99
terminal verdict       STOCKS_FREE_V6_BLOCKED_DATA_AUTHORITY
owner decision         ACCEPT_CLOSE recorded via Lead Engineer at
                       9fafdf2d327326bab2a3936d3683d46b5fb64bb0
                       (option A void; option B STANDING: any owner-entitled
                       source re-opens the program through this plan's gates)
GO status              the V6 standing GO is EXTINGUISHED UNCONSUMED (Lead
                       ruling, ledger 7720ee3). V7 requires its own owner GO
                       at its own prelaunch. No GO carries across cycles.
stocks denominators    21 observed / 21 published; budget 0/6 for V7
survivors              0
S1                     SEALED_UNTOUCHED
paper/live/orders      none
workers at close       0
inherited assets       multi-vintage SEC PIT panel (3,817,158 records / 410
                       filers / coverage 0.946..0.998 on Assets), the frozen
                       154-clock fundable set (p0a_clock_freeze.json),
                       pit_conditioning.py canonical bridge, Data Fusion
                       core c6a0576e..., P0b evidence packets (Stooq
                       disqualified, Massive unauthorized), lessons L1–L9
existing entitlement   Twelve Data free Basic — licensed to this program by
                       the forex F1 data authority (internal non-commercial
                       research; persistent local snapshots permitted with
                       recorded conditions); the fusion registry already
                       carries TWELVE_DATA for domains ("stocks","forex"),
                       data ("prices","reference_data")
```

## 1. What is closed and may not be rescued

Unchanged from the V6 forbidden inventory, carried byte-forward: the eight
rejected families (V2 momentum/trend-defense, V3 idio-shock/TOM, V4
participation/semivariance, V5 cross-sector coupling), all rescue variants,
and the vol-level shadow region **measured-closed** (rho 0.319 > 0.20 at the
front door). V7 adds nothing to this list until it scores.

## 2. Mission and allowed scope

V6 closed blocked because both registered price candidates failed. V7 asks:

> 1. (Probe) Does the program's EXISTING Twelve Data entitlement serve US
>    single-name daily prices well enough to be the price authority — depth,
>    delisted-name coverage, raw/adjusted clarity, corporate-action
>    reconciliation, documented availability — under the same non-commercial
>    research license the forex program already operates?
> 2. (Conditional) If a price authority passes: on a survivorship-aware
>    single-name panel, do PIT-fundamentals-conditioned mechanisms from the
>    frozen 154-clock set produce incremental after-cost information beyond
>    SPY/sector beta?

Binding rules:

- **The probe is cheap and terminal**: every gate below is measurable within
  hours and a small request budget. Any failure closes V7 as
  `STOCKS_FREE_V7_BLOCKED_DATA_AUTHORITY` with evidence — no degraded panel
  is ever scored.
- **No new signup, key or purchase.** The existing key is used from the
  environment (never in prompts, logs, JSON or git — handbook §27). Any
  owner-provided source (option B) enters through the same gate suite in
  parallel or later.
- **Snapshot discipline as the forex program practices**: persistent local
  snapshot, raw bytes hash-pinned at fetch, license conditions recorded per
  file, retrieval deterministic and resumable.
- Scoring scope if the probe passes: universe = authorized filer panel with
  a liquidity floor frozen before returns are examined; weekly-or-slower
  rebalances; equity cost model with liquidity-band stress multipliers
  applied to booked PnL; at least 3 of 6 blind proposals conditioned on the
  frozen clocks; wave diversity by assigned axis.

Allowed terminal outcomes:

```text
STOCKS_FREE_V7_REJECT_ALL
STOCKS_FREE_V7_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
STOCKS_FREE_V7_BLOCKED_DATA_AUTHORITY
STOCKS_FREE_V7_BLOCKED_SELECTION_INSUFFICIENT
STOCKS_FREE_V7_BLOCKED_PRELAUNCH
STOCKS_FREE_V7_INCOMPLETE_NOT_PROMOTABLE
```

## 3. Branch and worktree topology

```text
branch    orca/stocks-free-v7-integration
worktree  .worktrees/stocks-free-v7/integration
base      measured terminal SHA 39250b7... unless intake records a newer
          owner-authorized reconciliation descendant
lanes     .worktrees/stocks-free-v7/{p0-a2-panel-verify,p0-a3-price-probe,
          p0-a4-cohort,d1-a4-proposals,d1-a5-proposals,d1-a6-proposals,
          d2-a7-novelty,d2-a9-feasibility,i-family-1,i-family-2,
          q-a7-prelaunch,e-exec-1,r-reproduce,r-a7-terminal}
```

`pwd` before every `git worktree add`; never one branch in two worktrees;
one cycle = one A1 thread (verify no v7 branch exists first).

## 4. Agent allocation and concurrency

A1 controller/sole integrator; A2 panel re-verification and accounting
(inherit the V5/V6 P1 suite incl. L9 regression); A3 price probe + data
authority; A4 cohort/survivorship construction (SEC submissions status
history); A4b/A5/A6 blind proposal lanes on assigned axes; A7 independent
audits (never repairs, recomputes from bytes); A8/A9 implementation and
feasibility. Concurrency: A1 + at most three light lanes; full pytest
alone; heavy cap from a fresh probe; scored arms serial; foreign cycles
(V3R/V14 if alive) are respected — record `NOT_RUN_RESOURCE_CONFLICT`
rather than contending.

## 5. Phase V7-R — terminal reconciliation

A1 verifies the V6 chain (terminal SHA, the ACCEPT_CLOSE decision record
9fafdf2 as the expected post-terminal commit, budget 0/6, denominator
21/21, S1 seal, workers zero, clean trees, forbidden inventory intact,
panel + clocks present and hash-verified), then seeds
`research/control/stocks_free_v7_run/{run_contract,state,heartbeat,event_log,
forbidden_family_inventory,worktree_manifest,lessons_register}` with L1–L9.

## 6. Phase V7-P — probe, cohort, factory

### P0a — inherited panel re-verification (light)

A2 re-hashes the inherited PIT store against its pin and re-confirms the
154-clock freeze unchanged. Any byte drift is an intake blocker.

### P0b-2 — Twelve Data price probe (the cycle's first decision)

A3 measures, under the existing entitlement, each gate fail-closed:

1. **License scope**: equities endpoints covered by the recorded
   non-commercial research conditions; snapshot permissions confirmed for
   equities data specifically.
2. **Depth**: >= 7 years of daily OHLCV for a stratified sample, then the
   full authorized universe if the sample passes; request arithmetic within
   the free-tier rate limits, deterministic and resumable fetch plan.
3. **Delisted names (the make-or-break gate)**: probe the cohort's known
   delisted filers by ticker AND by identity-mapped aliases; a name that
   cannot be served is recorded; if delisted coverage is materially
   incomplete the probe FAILS — a survivorship-biased panel is never scored.
4. **Raw vs adjusted**: both series available or reconstructable; adjusted
   history consistent with the SEC-recorded distributions (L7 cross-check on
   a sample with known splits/dividends).
5. **Availability evidence**: daily-bar publication semantics documented
   (evidenced vs asserted — asserted bounds are never authorized); decisions
   read a bar no earlier than its close plus one session.
6. **Integrity**: OHLC consistency checks on the sample (the Stooq lesson).

Disposition per gate: PASS / FAIL with artifacts; the owner-provided-source
path (option B) runs the identical suite when a source arrives.

### P0c — survivorship cohort (parallel, light)

A4 builds the cohort from SEC submissions status history: per filer,
listing/delisting dates, ticker-change lineage, identity mapping valid at
each decision time; delisted names keep history; the cohort census is
published before D1 and reconciled against the price probe's servable set.

### P1–P3 — accounting, coverage-first, invariants

Inherit the full V5/V6 suites (CASH, cost-once, turnover convention, L9,
liquidity-band stress multipliers on booked PnL). P2 publishes per-field
coverage AND per-name price coverage BEFORE any proposal brief; a proposal
may cite only funded clocks and servable names. P3 freezes book/cost/
fold/concentration/drop-one/stress/minimum invariants. No PnL in Phase P.

## 7. Phase V7-D1 — blind proposal generation

Three lanes from the same `V7_PROPOSAL_WAVE_SHA`, each pre-assigned a
distinct axis from the funded set (at least one fundamentals axis, at least
one non-fundamentals axis within the non-forbidden space). Full packet
discipline inherited from V6 §7 (mechanism + falsifiable prediction;
literature; PIT observable with EVIDENCED availability; clocks from the
frozen 154; anchor, one neighbour, one placebo-style causal control; SPY/
sector incremental test; base and stress costs; turnover and sample floor;
drop-one design; failure interpretation; source-to-test map; signed
outcome-blind attestation). Proposal agents receive the forbidden packet
and no per-arm outcome files.

## 8. Phase V7-D2 — independent audit and selection

A7-N: novelty/anti-rescue with measured rank correlation against every
forbidden family and the V4 control arms; cross-cluster measurement; the
shadow-region rho gate. A9-F: per-proposal PIT and price coverage, schedule
breadth, liquidity-band cost arithmetic with break-even headroom, control
identifiability, drop-one meaningfulness, implementation risk — no PnL.
Frozen rubric as V4/V5/V6; exactly three arms per family; maximum six
scored cells; unused slots never reassigned.

## 9. Phase V7-I — implementation

Full V6 evidence list inherited, plus: price-availability-lag mutation
tests; liquidity-band cost-scaling tests (cost linear in fills — L-V14-0);
placebo-control-cannot-equal-anchor; deterministic double generation. A1
integrates one family at a time.

## 10. Phase V7-Q — freeze and prelaunch

Full V6 sequence: all suites; six-arm dummy dry-run into a temporary ledger
with recursive PnL-leak scanning (handbook §17.2); digests pairwise unique;
data/coverage/availability hashes; budget 0/6; full pytest alone; compileall;
`git diff --check`; fresh resource probe; freeze `STOCKS_FREE_V7_W1`;
detached equal twins; byte-identical read-only data and empty ledger
authority. Independent A7 recomputes; only
`STOCKS_FREE_V7_S0_LAUNCH_AUTHORIZED` with zero unresolved HIGH/CRITICAL
reaches the owner. HARD STOP until the owner types:

```text
GO STOCKS V7 SCORED EXECUTION
```

## 11. Phase V7-E — maximum six scored cells

Serial per family (anchor, neighbour, control); TECHABORT discipline;
per-cell reporting per handbook §18.3; each score records the full V6 field
set plus liquidity-band cost breakdown and per-decision vintage provenance.

## 12. Stage-A gates (frozen ex ante; V6 set carried forward)

After-cost anchor expectancy > 0; PF >= 1.10; >= 2/3 folds positive;
MDD <= 15%; largest fold-positive share <= 50%; name positive-PnL share
within the frozen ceiling; stress positive with multipliers applied;
meaningful drop-one name and fold; risk-matched excess positive in >= 2/3
folds; overall incremental alpha > 0; neighbour supports; the placebo/causal
control does not reproduce; reproduction ALL_MATCH; zero unresolved
HIGH/CRITICAL. Positive raw PnL never overrides failed incremental alpha or
a firing control.

## 13. Reproduction, terminal closeout and program statistics

Reproduce every cell from the detached twin; exact match except volatile
metadata. Terminal A7 recomputes the C-chain, audits POSITIVE results
STRICTER than negative (§20.2), and the terminal report updates the program
statement (21 + V7 cells) with DSR/PBO over the published stocks program.
Any survivor passes the four-layer test (mechanical/data/statistical/
economic) before any SURVIVORS.md entry; PIT-unevidenced survivors are
recorded provisional, never PIT-audited. S1 stays sealed; no paper/live.

## 14. Required commands and reporting

`.venv/bin/python`; stocks asset suites, protocol contracts, data-fusion
compatibility suite, full `pytest -q` alone, `compileall`, `git diff
--check`, `git status --porcelain=v1`. Every gate reports command, exit
code, stdout/stderr paths, full HEAD, input/output hashes, expected/
observed, verdict, blocker, tree status. Owner checkpoints: intake; probe
verdict (the first decision); cohort census; P gates; proposals and audits;
selection freeze; implementations and W1; A7 prelaunch; family completions
after GO; reproduction and terminal A7.

## 15. Hard boundaries

- No new signup, key or purchase; the existing entitlement only; any
  owner-provided source goes through the same gates.
- API keys live in the environment; never in prompts, logs, JSON or git.
- No S1 access, paper, live, orders or credentials.
- No raw-data commit (snapshots stay gitignored with hash manifests).
- No optimizer, scored grid, threshold weakening, family substitution,
  cluster-padding or result-aware retrofit.
- No rewriting prior ledgers, artifacts or terminal reports.
- No push, main merge, history rewrite or worktree deletion without owner
  instruction.
- Gates report PASS/FAIL/NOT_RUN/BLOCKED. A fast honest blocked close is
  preferable to a slow degraded one.

## 16. First report from a fresh A1

```text
measured UTC
root path / branch / full HEAD / porcelain
V6 terminal SHA + ACCEPT_CLOSE decision record verified
stocks denominator 21/21, budget 0/6, S1 seal, workers
inherited panel + 154-clock freeze hashes re-verified
Twelve Data entitlement authority chain + probe plan (gates 1–6)
integration worktree path / branch / base SHA
RAM / CPU / disk / preliminary heavy cap / foreign-cycle status
GO/NO_GO for reconciliation and the probe
```

A1 continues autonomously through the probe and, if it passes, through the
factory to prelaunch; it stops before the first scored V7 cell unless a
real blocker occurs earlier. The probe verdict itself is reported to the
owner at the first checkpoint either way.
