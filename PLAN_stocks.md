# PLAN_STOCKS — STOCKS-FREE-V2 RECONCILIATION AND STOCKS-FREE-V3 DISCOVERY

> Owner authority for a fresh A1 Stocks coding-agent context.
>
> Read this document in full before committing files, creating worktrees,
> dispatching agents or computing a scored result. This plan replaces the prior
> `PLAN_stocks.md` operationally. Historical stock plans, freezes, ledgers and
> scored artifacts remain immutable evidence.

## 0. Measured entry state and authority order

Measured on 2026-09-03 in `/Users/hoangminhlong/my-quantitative`:

```text
root branch / HEAD             main @ 0dcd569
origin/main                    b8876ef8e0f7dd235d66f5cae5bfd8fd9034147f
root relation                  main is one local commit ahead (PLAN_crypto.md only)
untracked owner path           .v2c/ — preserve, never add or modify
V2 integration path            .worktrees/stocks-free-v2/integration
V2 integration branch          orca/stocks-free-v2-integration
V2 terminal HEAD               efb89a6aa99e130440c00830903990878d607dcb
V2 sprint verdict              STOCKS_FREE_V1_REJECT_ALL
V2 base cells                  6/6 computed and published
V2 reproduction               6/6 EXACT_MATCH
V2 S1                         SEALED, never opened
V2 workers                    0
remote V2 branch              not assumed; verify before any push claim
```

Primary V2 authority files at `efb89a6`:

- `research/control/stocks_free_v2_run/terminal_report.json`;
- `research/control/stocks_free_v2_run/family_verdicts.json`;
- `research/control/stocks_free_v2_run/family_verdicts_amendment.json`;
- `research/control/stocks_free_v2_run/z9_reproduction.json`;
- `research/control/stocks_free_v2_run/ledger.json`;
- `research/audits/stocks_free_v2/z9_a7_terminal/AUDIT_REPORT.md`;
- `research/wayfinder/MAP.md`.

Authority order:

1. this owner-approved `PLAN_stocks.md` for V2R and V3;
2. the immutable V2 selection/W1 contracts for interpreting V2;
3. terminal A7 independent recomputation;
4. V2 amendment artifacts;
5. original pre-amendment reports, state, heartbeat and prose.

The original conservative `INCOMPLETE_NOT_PROMOTABLE` label is historical.
Terminal A7 proved the sidecar attribution mismatch was a bookkeeping defect,
not missing scientific evidence; the effective terminal verdict is
`STOCKS_FREE_V1_REJECT_ALL`.

A1 MUST re-measure all paths, SHAs, dirty files, worktrees, workers, counters
and remote refs. If a value differs, preserve this snapshot, write an intake
delta and never silently force/reset a branch.

## 1. Frozen reading of STOCKS-FREE-V2

### 1.1 A4 relative momentum is closed REJECT

```text
anchor MOM121 top-3             total PnL +137.2%, PF 1.896, 3/3 folds
neighbour vol-adjusted          total PnL +130.3%, PF 1.905, 3/3 folds
bottom-3 negative control       total PnL +114.8%, PF 1.559, 2/3 folds
anchor maximum fold MDD         30.36% > frozen 15% limit
control expectancy              96.5% of anchor expectancy
```

The bottom-ranked control reproduced most of the anchor. Market/sector beta,
not the momentum ranking, dominates the result in this cohort/window. V3 MUST
NOT rescue A4 through a new lookback, top-K, chosen ETF subset, relaxed MDD or
post-result SPY hedge on the same window.

### 1.2 A5 trend/defensive is closed REJECT

```text
anchor TSM12 + vol target       total PnL +39.8%, PF 1.649, 3/3 folds
neighbour SMA200 weekly         total PnL +18.5%, PF 1.169, 2/3 folds
inverted control               total PnL +15.5%, PF 1.417, 2/3 folds
anchor maximum fold MDD         23.22% > frozen 15% limit
drop-one-ETF minimum expectancy -3.05% < 0
```

Terminal A7 found that the runner sidecar counted `CASH` in turnover and added
cost twice. Independent corrected attribution matched the canonical harness at
approximately `1e-15`; symbol concentration was available and passed. A5 still
fails MDD and drop-one robustness, so its clean REJECT does not depend on the
sidecar defect or the disputed fold-share presentation.

### 1.3 V2 results are not live-ready evidence

- Six cells and their reproductions are immutable.
- V2 observed and published counters both equal 6.
- Raw percentage PnL is not proof of incremental edge over SPY or sector beta.
- No V2 family is a Stage-A survivor.
- S1 `2025-08-01..2026-07-31` remains sealed.
- No paper, testnet, live or order authority exists.

## 2. Mission and allowed outcomes

This plan has two missions:

1. Reconcile V2 terminal metadata and fix the non-scoring sidecar/fold-gate
   implementation without changing any V2 scored artifact or verdict.
2. Run an outcome-blind STOCKS-FREE-V3 discovery cycle using only the already
   authorized zero-cost daily ETF data, selecting at most two genuinely new
   families with three frozen arms each.

V3 is a screening cycle on reused S0. It is not OOS. Every computation expands
the Stocks multiple-testing population.

Allowed terminal sprint outcomes:

- `STOCKS_FREE_V3_REJECT_ALL`;
- `STOCKS_FREE_V3_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1`;
- `STOCKS_FREE_V3_BLOCKED_SELECTION_OR_DATA`;
- `STOCKS_FREE_V3_BLOCKED_PRELAUNCH`;
- `STOCKS_FREE_V3_INCOMPLETE_NOT_PROMOTABLE`.

No outcome authorizes opening S1, paper/live trading, credentials, orders,
leverage, a paid provider or a broker connection.

## 3. Scope and hard boundaries

### In scope

- US cash-market ETF research using the frozen eleven-symbol cohort:
  `SPY, XLK, XLE, XLF, XLV, XLI, XLP, XLY, XLU, XLB, XLRE`;
- daily raw OHLCV from the already authorized Twelve Data Basic account;
- official issuer distributions and split-factor reconciliation already frozen;
- the repository's US-equity regular-session calendar;
- long/cash target books unless a short leg has separate PIT borrow authority;
- flat, SPY total return, equal-weight sectors and risk-matched SPY context;
- schedule-only cost/turnover/capacity checks, scored S0, reproduction and A7.

### Out of scope

- individual-stock universes, earnings surprise, borrow utilization, short
  interest or institutional holdings without new PIT data authority;
- options, futures, CFDs, Binance TradFi perpetuals and tokenized stocks;
- new provider accounts, paid upgrades or data purchases;
- raw-data redistribution or raw provider payload commits;
- fabricated historical quotes, borrow rates, early closes or corporate actions;
- using S1 for proposal choice, debugging, tuning, scoring or diagnostics;
- A4/A5 parameter rescue, selected-ETF rescue or relabeling;
- score-driven grids, Bayesian/ML optimization or manual threshold tuning;
- mixing Stocks counters or conclusions with crypto/forex ledgers;
- push, merge to `main`, branch/worktree deletion or history rewrite without a
  new explicit owner instruction.

Missing evidence is `UNAVAILABLE_FAIL_CLOSED`, never an inferred PASS.

## 4. Data, windows, identities and counters

### 4.1 Frozen data authority

V3 may reuse only the provider/data surfaces already authorized in V2:

```text
provider tier        Twelve Data Basic, USD 0, existing owner account
use                  internal non-commercial research only
redistribution       prohibited
raw data             gitignored and local
cohort               11 ETFs listed above; XLC remains excluded
common coverage      2018-01-02..2026-08-27
warmup               2018-01-02..2018-04-03
S0                   2018-04-04..2025-07-31
S1                   2025-08-01..2026-07-31 SEALED
```

A3 must revalidate hashes, entitlement/terms evidence, session coverage,
corporate-action inputs and S1 path denial. Revalidation may not expose S1
returns. If the existing local snapshot is absent or hashes differ, V3 is
blocked; no automatic network fetch is allowed by this plan.

### 4.2 V3 identity

Every V3 trial key/digest includes:

```text
asset_class=US_ETF_CASH
cycle=STOCKS_FREE_V3
provider/data/calendar/corporate-action digests
cohort and eligibility digest
S0/fold/warmup/purge digests
family_id, arm_id and complete arm_config_digest
signal and execution clocks
raw-fill and total-return transformation policy
cost, cash-rate and cap digests
flat/SPY/equal-sector/risk-matched benchmark digests
control and falsification contract digests
```

### 4.3 Counters and budget

V3 begins:

```text
historical Stocks observed      6
historical Stocks published     6
V3 observed                     0
V3 published                    0
V3 maximum scored base cells    6
S1                              SEALED_UNTOUCHED
```

Every computed base score increments the V3 observed counter exactly once,
including a result whose publication fails. Exact replay increments neither.
Stress diagnostics belong to their frozen base arm and do not silently create
extra parameter trials. Statistical claims use at least six historical Stocks
observations plus every V3 computed result.

## 5. Agent roles, concurrency and ownership

Use nine logical roles, with at most A1 plus three light agents active.

| Role | Responsibility | Write scope |
|---|---|---|
| A1 | controller, integration, central control, freezes, ledger, publisher | central V2R/V3 authority files |
| A2 | sidecar, canonical attribution and trial accounting repairs | shared Stocks harness/sidecar and dedicated tests |
| A3 | zero-cost data, S0/S1 isolation, benchmark/risk-context authority | V3 data/benchmark modules, manifests and tests |
| A4 | blind proposal lane 1, exactly two proposals | own proposal prefix only |
| A5 | blind proposal lane 2, exactly two proposals | own proposal prefix only |
| A6 | blind proposal lane 3, exactly two proposals | own proposal prefix only |
| A7 | independent reconciliation, novelty, prelaunch and terminal audits | audit paths only |
| A8 | selected family 1 implementation | one family module/plugin/tests |
| A9 | selected family 2 implementation | one family module/plugin/tests |

Rules:

- A1 alone creates worktrees, integrates, freezes, publishes and updates
  counters/central ledgers.
- A7 never repairs production code it audits.
- A lane begins at one recorded full 40-character wave SHA.
- Every lane owns non-overlapping globs and returns one focused clean commit.
- Subagents never merge, rebase, push, amend another lane or edit central files.
- Full suites run alone with zero heavy worker.
- Scored cells within a family are serial.
- On the owner's 8 GB Mac, the operative heavy cap is at most one; all six
  scored cells and reproduction run serially.
- A higher cap on another host requires a fresh resource probe; never infer it.

## 6. Branch and worktree topology

### 6.1 Owner plan commit

The root checkout is owner/bootstrap space. The existing untracked `.v2c/`
belongs to another process/owner and must remain byte-untouched and untracked.
If the only tracked change is this `PLAN_stocks.md`, A1 is authorized to commit
only this file as `STOCKS_V3_OWNER_PLAN_SHA`. Do not include `.v2c/` or any other
path. The pre-existing `PLAN_crypto.md` commit remains unchanged.

### 6.2 V2R reconciliation integration

```text
path:   /Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2r/integration
branch: orca/stocks-free-v2r-integration
base:   orca/stocks-free-v2-integration@efb89a6aa99e130440c00830903990878d607dcb
```

Create this worktree from the measured local V2 terminal, then cherry-pick only
`STOCKS_V3_OWNER_PLAN_SHA`. Do not merge moving `main`.

### 6.3 V3 integration and lanes

After V2R freezes `STOCKS_FREE_V2R_TERMINAL_SHA`:

```text
.worktrees/stocks-free-v3/integration       orca/stocks-free-v3-integration
.worktrees/stocks-free-v3/p1-a2-factory    orca/stocks-free-v3-p1-a2-factory
.worktrees/stocks-free-v3/p1-a3-data       orca/stocks-free-v3-p1-a3-data
.worktrees/stocks-free-v3/d1-a4-proposals  orca/stocks-free-v3-d1-a4-proposals
.worktrees/stocks-free-v3/d1-a5-proposals  orca/stocks-free-v3-d1-a5-proposals
.worktrees/stocks-free-v3/d1-a6-proposals  orca/stocks-free-v3-d1-a6-proposals
.worktrees/stocks-free-v3/d2-a7-audit      orca/stocks-free-v3-d2-a7-audit
.worktrees/stocks-free-v3/i-a8-family-1    orca/stocks-free-v3-i-a8-family-1
.worktrees/stocks-free-v3/i-a9-family-2    orca/stocks-free-v3-i-a9-family-2
.worktrees/stocks-free-v3/q-a7-prelaunch   orca/stocks-free-v3-q-a7-prelaunch
.worktrees/stocks-free-v3/e-exec-1         detached at STOCKS_FREE_V3_W1
.worktrees/stocks-free-v3/r-reproduce      detached at STOCKS_FREE_V3_W1
.worktrees/stocks-free-v3/r-a7-terminal    fresh audit branch after reproduction
```

Literal SHA placeholders must never be passed to Git. A1 records for every
lane in `research/control/stocks_free_v3_run/worktree_manifest.json`:

```text
role, mission, absolute_path, branch, full_bootstrap_sha,
allowed_globs, forbidden_globs, deliverables, required_tests,
commit_sha, status, merge_order, model, requested_effort,
effective_effort_or_unverified, delegation_allowed
```

Before dispatch:

```bash
git -C <exact-path> rev-parse HEAD
git -C <exact-path> branch --show-current
git -C <exact-path> status --porcelain=v1
```

Any mismatch is `WORKTREE_IDENTITY_MISMATCH`; stop before writing. Never delete
or reset an existing path to solve a mismatch.

## 7. Phase R0/R1 — reconcile V2 terminal metadata

V2 science and scored artifacts are immutable. This phase changes only
authority metadata and regression tests.

### R0 — intake

A1 creates:

```text
research/control/stocks_free_v2_run/v2r_reconciliation_intake.json
```

Record full SHAs/hashes, terminal A7 commit, 6/6 counters, reproduction 6/6,
workers zero, S1 seal and the exact stale fields.

Known fields to reconcile:

- `state.json` still records obsolete W1 `5046a87...`; the canonical corrected
  W1 is `106378230abecbaefff4248eeb373794f1b73038`;
- `state.json` still labels FD2 as A7 re-audit pending although the recheck is
  complete;
- `heartbeat.json` has `verdict: null` and an obsolete current-cell value;
- `terminal_report.json` retains the original conservative verdict as history
  and the amendment separately; consumers need an unambiguous effective
  verdict without deleting the original record;
- `family_verdicts.json` is historical pre-amendment evidence and must not be
  silently rewritten; its amendment remains authoritative.

### R1 — corrections

Required:

1. Create a canonical `terminal_effective_verdict.json` pointing to the
   original report, A7 audit and amendment hashes.
2. Update state/heartbeat/MAP/CONTINUE surfaces to agree on:
   `STOCKS_FREE_V1_REJECT_ALL`, 6/6, exact W1, S1 sealed and workers zero.
3. Preserve original report/verdict files byte-for-byte where they document the
   history; use explicit supersession fields rather than erasing the incident.
4. Append one reconciliation event. Never edit prior JSONL events.
5. Add `tests/stocks_free_v2/test_terminal_metadata.py` asserting agreement and
   rejecting stale in-progress/current-cell/pending-audit fields.

### R2 — independent audit

A7 receives a fresh worktree from the reconciliation candidate and writes only:

```text
research/audits/stocks_free_v2/v2r_terminal_reconciliation.{json,md}
```

Required verdict:

```text
STOCKS_FREE_V2R_METADATA_RECONCILED
```

A7 must independently verify that no scored artifact, ledger event, metric,
selection freeze, W1 code/data input or V2 verdict basis changed.

Required gates:

```bash
.venv/bin/python -m pytest tests/stocks_free_v2/test_terminal_metadata.py -q
.venv/bin/python -m pytest tests/stocks_free_v2 -q
.venv/bin/python -m pytest tests/assets/stocks -q
.venv/bin/python -m pytest tests/test_protocol_contracts.py tests/test_protocol_metrics.py -q
.venv/bin/python -m compileall research/stocks_free_v2 research/assets/stocks research/assets/common
git diff --check
git status --porcelain=v1
```

A1 integrates A7 and freezes `STOCKS_FREE_V2R_TERMINAL_SHA`.

## 8. Phase P0 — V3 control plane

Create under `research/control/stocks_free_v3_run/`:

- `run_contract.json`;
- `state.json`;
- `heartbeat.json`;
- append-only `event_log.jsonl`;
- `worktree_manifest.json`;
- `historical_boundary.json`;
- `data_manifest.json` initially pending;
- `benchmark_contract.json` initially pending;
- `lessons_register.json`;
- `forbidden_family_inventory.json`.

Required initial state:

```text
phase                          P0_INTAKE
historical observed/published 6/6
V3 observed/published         0/0
budget                        0/6
S1                            SEALED_UNTOUCHED
workers                       0
deployment                    NO_PAPER_NO_LIVE_NO_ORDERS
```

The operational engineering phases are gate-based, not forced by a short
deadline. A separate 12-hour scoring clock begins only after prelaunch A7 and
an explicit owner `GO STOCKS V3 SCORED EXECUTION`. Start no cell with less than
120 minutes remaining; with less than 45 minutes, stop safely and reconcile.

## 9. Phase P1 — repair measurement and data/benchmark authority

A1 dispatches A2 and A3 concurrently from `STOCKS_FREE_V3_BOOTSTRAP_SHA`.

### A2 — sidecar and canonical metric repair

```text
path:   .worktrees/stocks-free-v3/p1-a2-factory
branch: orca/stocks-free-v3-p1-a2-factory
```

Deliverables:

1. One canonical portfolio valuation source or a sidecar proven equivalent.
2. `CASH` excluded from tradable-leg turnover everywhere.
3. Every cost charged exactly once.
4. Hand-computed fixtures covering A4-style books without explicit CASH and
   A5-style books with explicit CASH.
5. Attribution components reconcile to canonical equity/PnL within a frozen
   tolerance of `1e-12` on synthetic fixtures and approximately machine
   precision on the V2 diagnostic replay.
6. A single fold-concentration definition: per-arm positive fold contribution
   divided by that same arm's total positive fold contribution. No family pool,
   neighbour substitution or mixed gross/net denominator.
7. Drop-one-ETF selects a held ETF with the largest realized absolute-weight
   contribution; deterministic tie-break.
8. Trial publication refuses zero-event/zero-position results and preserves
   observed-versus-published semantics.

The V2 diagnostic replay proves repair but may not rewrite V2 result artifacts
or produce a new V2 trial.

Allowed writes: shared Stocks harness/sidecar/accounting helpers, dedicated
tests and `research/audits/stocks_free_v3/p1_a2_*`. No V3 family code.

### A3 — data, S1 isolation and benchmark contract

```text
path:   .worktrees/stocks-free-v3/p1-a3-data
branch: orca/stocks-free-v3-p1-a3-data
```

Deliverables:

1. Revalidate the V2 zero-cost license/terms and existing snapshot hashes
   without printing credentials or making network calls.
2. Verify all 11 ETFs, raw OHLCV schema, corporate actions, issuer total-return
   inputs and regular-session calendar.
3. Prove S0 reads are allowed and every S1 path/date access is denied.
4. Freeze benchmark semantics before proposals:
   - flat hard benchmark;
   - SPY total return;
   - equal-weight sector ETF total return;
   - risk-matched SPY context scaled ex ante by the arm's frozen gross/vol rule.
5. Define incremental mechanism metrics separately from raw PnL. A family
   cannot pass merely because long equity beta rose.
6. Verify no family requires earnings/borrow/quotes unavailable in the free
   snapshot.

Allowed writes: V3 data/benchmark modules, manifests, tests and
`research/audits/stocks_free_v3/p1_a3_*`. Never commit raw data or secrets.

### P1 integration gate

A1 cherry-picks A2 then A3, running targeted tests after each. Then run all V2
regressions, V3P tests and the full suite alone. Test execution may not mutate
tracked artifacts. Freeze `STOCKS_FREE_V3_P1_SHA` only with zero unresolved
HIGH/CRITICAL and a clean integration tree.

## 10. Phase D0 — blind input packet

A1 creates and freezes:

```text
research/proposals/stocks_free_v3/blind_input_packet.json
research/proposals/stocks_free_v3/blind_input_packet.md
research/control/stocks_free_v3_run/forbidden_family_inventory.json
```

The packet contains only:

- available fields and PIT clocks;
- cohort, S0 folds, warmup/purge and calendar;
- costs, capacity and long/cash constraint;
- benchmark and incremental-alpha contract;
- Stage-A gates and six-cell maximum;
- prior mechanism-level lessons and forbidden ancestry;
- no V2 arm PnL table, ETF ranking or winning-period diagnostics.

Proposal lanes may consult primary academic sources and official provider/
exchange/issuer documentation. Sources are priors, not profitability evidence.

## 11. Phase D1 — three blind proposal lanes

Create from `STOCKS_FREE_V3_BLIND_PACKET_SHA`:

```text
.worktrees/stocks-free-v3/d1-a4-proposals  orca/stocks-free-v3-d1-a4-proposals
.worktrees/stocks-free-v3/d1-a5-proposals  orca/stocks-free-v3-d1-a5-proposals
.worktrees/stocks-free-v3/d1-a6-proposals  orca/stocks-free-v3-d1-a6-proposals
```

Each agent proposes exactly two mechanisms; total exactly six. Agents cannot
read another lane's proposals or V2 scored outcomes.

Each proposal specifies before any scoring:

- primary-source claim and ETF-market mechanism;
- expected counterparty and falsifiable expected sign;
- required fields and PIT availability;
- universe, formation, holding, decision and execution clocks;
- long/cash target construction and cash semantics;
- turnover, capacity, costs, distributions and split handling;
- flat, SPY, equal-sector and risk-matched benchmark behavior;
- anchor, justified neighbour and causal negative control;
- incremental mechanism test that distinguishes alpha from equity beta;
- drop-one-ETF and drop-one-fold expectations;
- exact falsification rule and implementation estimate;
- ancestry comparison and why it is not an A4/A5 rescue.

Priority search spaces, not mandatory selections:

- month-end/quarter-end institutional rebalancing seasonality;
- overnight-gap versus intraday-return decomposition;
- idiosyncratic sector-shock reversal with market return removed before rank;
- sector dispersion/breadth state transitions;
- volume/liquidity seasonality available from daily OHLCV;
- volatility-event recovery with predeclared event and holding clocks.

Ineligible proposals:

- ordinary cross-sectional momentum, time-series trend, SMA/EMA trend,
  vol-targeted defensive rotation or parameter variants of A4/A5;
- selecting top/bottom ETFs or thresholds after reading V2 outcomes;
- a result whose expected profit is simply long SPY/sector beta;
- earnings surprise, analyst revisions, fundamentals, institutional flows,
  borrow/short interest or quote-spread mechanisms without current data;
- daily-indicator grids without a distinct economic mechanism;
- any proposal requiring a new account, paid data or network fetch.

No proposal agent may compute returns, PnL, PF, Sharpe, rankings or correlations
on the scored S0 window.

## 12. Phase D2/D3 — A7 audit, feasibility and selection

A1 integrates only the six frozen proposal documents, producing
`STOCKS_FREE_V3_PROPOSAL_POOL_SHA`, then creates a fresh A7 lane.

A7 independently audits:

- exactly six proposals and outcome-blind access logs;
- source identity and source-to-test mapping;
- novelty against all prior Stocks and crypto family inventories;
- hidden A4/A5 rescue;
- field/PIT/calendar/corporate-action readiness;
- long/cash and capacity feasibility;
- schedule-only turnover/base/stress cost;
- benchmark and beta-confounding falsification;
- negative-control informativeness;
- minimum event/decision evidence;
- unresolved HIGH/CRITICAL objections.

A7 writes objections only and never repairs proposals.

### Frozen selection rubric

A1 selects exactly two eligible families by:

1. no novelty/rescue veto;
2. complete free-data readiness;
3. schedule/cost/capacity PASS;
4. control capable of separating the mechanism from beta;
5. sufficient decision/event count across all three folds;
6. lowest implementation risk;
7. strongest primary-source trace;
8. lexicographically smallest family ID as final tie-break.

If fewer than two are eligible, close
`STOCKS_FREE_V3_BLOCKED_SELECTION_OR_DATA`; do not lower thresholds or fill an
empty slot with a third-ranked ineligible proposal.

Freeze in `research/control/stocks_free_v3_run/selection_freeze.json`:

- exactly two families and six arms when selection succeeds;
- family/arm IDs and complete config digests;
- provider/data/calendar/action/cohort/window/fold hashes;
- schedules, target books, costs, cash and capacity;
- all four benchmarks and incremental-alpha calculations;
- anchor, neighbour, negative control and falsification rules;
- stress/drop-one definitions;
- budget 0/6 and counters 0/0 for V3;
- observed historical Stocks denominator 6;
- implementation ownership and file allowlists.

After the first scored metric, no freeze amendment or substitute arm is allowed.

## 13. Phase I — two isolated family implementations

A1 creates from `STOCKS_FREE_V3_SELECTION_SHA`:

```text
.worktrees/stocks-free-v3/i-a8-family-1
.worktrees/stocks-free-v3/i-a9-family-2
```

A8 and A9 each own exactly one family module/plugin, dedicated tests, golden
feature vectors and audit handoff. They do not edit shared accounting, central
registry, freeze or the other family.

Required implementation evidence:

- completed-session and PIT-correct features;
- signal strictly precedes the next executable session event;
- raw prices for fills and frozen issuer-TR path for signals/accounting;
- deterministic long/cash weights, caps and cash treatment;
- no future cohort membership or corporate actions;
- exact distribution/split treatment;
- canonical costs charged once and CASH excluded from turnover;
- anchor/neighbour/control identities distinct and stable;
- hand-computed expected-sign/control fixtures;
- schedule-only feasibility without scored returns;
- dummy exact-arm dry-run into a temporary ledger;
- double-generation equality and clean targeted-test commit.

A1 cherry-picks one family at a time and runs targeted tests after each. A1 may
make one minimal central wiring commit after both plugins pass.

## 14. Phase Q — integrated QA, W3 and independent prelaunch

Before scoring, A1 must:

1. Run all adapter, data, benchmark, family and V2 regression suites.
2. Execute a six-arm dummy dry-run into a fresh empty temporary ledger.
3. Prove six distinct identities, six first publications and six exact replays
   with zero denominator delta.
4. Prove a zero-event result cannot publish.
5. Prove sidecar attribution equals harness and costs occur once.
6. Prove each control can falsify beta/mechanism in synthetic fixtures.
7. Resolve data through actual loaders and verify hashes, not file existence.
8. Run full pytest alone; tree must be unchanged.
9. Measure RAM/CPU/disk; freeze operative heavy cap.
10. Freeze final code-bearing `STOCKS_FREE_V3_W1`.
11. Create detached execution and reproduction trees at exactly W1.
12. Stage equal-twin read-only data and require byte-identical manifests.

A fresh A7 prelaunch audit independently recomputes:

- V2R pin and effective terminal verdict;
- 6/6 historical counters and V3 0/0;
- all selection/arm/data/code hashes;
- S0/S1 isolation and absence of S1 reads;
- six-arm identity and idempotence;
- canonical sidecar/harness equality;
- costs, CASH turnover, benchmarks and controls;
- schedule-only cost/capacity;
- execution/reproduction equal-twin staging;
- resource cap, workers zero and clean trees;
- absence of real V3 scored artifacts.

Only this exact verdict authorizes a later scored run:

```text
STOCKS_FREE_V3_S0_LAUNCH_AUTHORIZED
```

The implementation agent governed by this plan MUST stop immediately after
integrating prelaunch evidence. It may not start the first scored cell without
a new explicit owner instruction: `GO STOCKS V3 SCORED EXECUTION`.

## 15. Phase E — six scored cells, separate owner GO required

This phase is specified but not authorized by the initial implementation
prompt. On the 8 GB Mac, run all cells serially with heavy cap one.

Family order is frozen lexicographically; within each family:

1. anchor;
2. neighbour;
3. causal negative control.

Per-cell path:

```text
verify W1/data/spec/arm pins
-> build PIT schedule and targets
-> chronological folds with warmup/purge
-> next-session executable fills
-> canonical costs and corporate actions
-> base metrics plus frozen benchmark context
-> stress and meaningful drop-one diagnostics
-> canonical immutable artifact
-> observed +1 exactly once
-> A1 publication exactly once
-> replay zero-delta check
-> counters/heartbeat checkpoint
```

No pytest while a scored worker runs. One result cannot modify a later frozen
cell. Technical abort consumes zero budget only when no scored metric exists
and a forensic TECHABORT artifact proves it.

## 16. Stage-A gates

Every selected family must pass all applicable gates:

- after-cost expectancy > 0;
- position PF >= 1.10;
- at least 2/3 folds positive;
- no populated fold PF < 0.80;
- MDD <= 15%;
- per-arm largest positive-fold share <= 50%;
- no ETF contributes >35% of positive PnL/risk;
- sufficient decisions/positions for the frozen family clock;
- stress PnL > 0 and stress PF >= 1.00;
- realised turnover and capacity remain inside the frozen schedule gate;
- anchor risk-matched excess performance over SPY is positive in at least 2/3
  folds;
- anchor incremental mechanism alpha is positive;
- neighbour supports the anchor's mechanism direction;
- control either has the opposite incremental-alpha sign or absolute control
  alpha is less than 50% of absolute anchor alpha;
- drop-one-largest-held-ETF survival;
- drop-one-fold survival;
- exact independent reproduction;
- zero unresolved HIGH/CRITICAL;
- statistical claims use observed Stocks denominator >=6 plus all computed V3
  trials, or remain `UNAVAILABLE_FAIL_CLOSED` with zero credit.

Raw PnL, PF or 3/3 positive folds cannot override a failed beta/control,
drawdown, concentration or robustness gate.

Allowed family verdicts:

- `STOCKS_FREE_V3_FAMILY_REJECT`;
- `STOCKS_FREE_V3_STAGE_A_SURVIVOR_LOCKED_FOR_FUTURE_S1`;
- `STOCKS_FREE_V3_FAMILY_BLOCKED`;
- `STOCKS_FREE_V3_FAMILY_INCOMPLETE_NOT_PROMOTABLE`.

## 17. Reproduction and terminal A7

Reproduce every computed cell in fresh processes from the detached reproduction
tree at W1. Require equality for:

- features, schedules, targets and fills;
- raw/TR transformations, distributions and splits;
- turnover, costs, CASH and equity curve;
- folds, metrics, benchmarks, stresses and drop-one outputs;
- identity, input/output hashes and verdict inputs.

Only volatile UTC/PID/path fields may be normalized, using a rule frozen before
scoring. A7 independently recomputes ledger/counters, representative scientific
metrics, gate truth, S1 isolation and boundaries before signing the strongest
allowed terminal verdict.

## 18. Gate-evidence contract and test routing

Every machine-readable gate contains:

```text
gate_id, measured_utc, producer_role, full_head_sha, command, exit_code,
stdout_path, stderr_path, expected, observed, verdict,
input_hashes, output_hashes, blockers, corrective_action, tree_status
```

Gate verdicts are only `PASS`, `FAIL`, `NOT_RUN` or `BLOCKED`. A missing test,
input, output, hash or authoritative provider fact is not PASS.

Minimum commands, routed when their owning phase has created the paths:

```bash
.venv/bin/python -m pytest tests/stocks_free_v2/test_terminal_metadata.py -q
.venv/bin/python -m pytest tests/stocks_free_v2 -q
.venv/bin/python -m pytest tests/stocks_free_v3 -q
.venv/bin/python -m pytest tests/assets/stocks -q
.venv/bin/python -m pytest tests/test_protocol_contracts.py tests/test_protocol_metrics.py tests/test_protocol_registry.py tests/test_protocol_reproduce.py -q
.venv/bin/python -m pytest tests -q
.venv/bin/python -m compileall research/stocks_free_v2 research/stocks_free_v3 research/assets/stocks research/assets/common
git diff --check
git status --porcelain=v1
```

Full pytest runs once per integration wave, alone. A later passing subset cannot
waive an earlier failing required test.

## 19. Required checkpoints

A1 reports:

1. measured root/V2 intake, dirty paths, workers and owner-plan SHA;
2. V2R corrections, tests and A7 reconciliation verdict;
3. V3 P0 counters/data/budget/S1 state;
4. A2/A3 repair commits and P1 gates;
5. six blind proposal IDs and pool SHA;
6. A7 objections and exact two-family selection or blocker;
7. implementation commits, six-arm dry-run and W1;
8. A7 prelaunch verdict and stopped-before-score proof;
9. after each scored cell only following a later owner GO;
10. reproduction and terminal A7 verdict.

Each checkpoint includes full SHA, absolute worktree, branch, clean state,
commands/test counts, counters, budget, S1 seal, workers and exact blockers.

## 20. Definition of Done for the initial implementation prompt

The fresh implementation agent is done only when:

- V2 effective verdict remains `STOCKS_FREE_V1_REJECT_ALL`;
- V2 metadata agrees on 6/6, exact W1, S1 sealed and workers zero;
- A7 returns `STOCKS_FREE_V2R_METADATA_RECONCILED`;
- V2 result/ledger/scored artifact hashes are unchanged;
- A2 fixes sidecar CASH/cost/fold definitions with regression proof;
- A3 reauthorizes existing zero-cost data, S1 isolation and benchmarks;
- V3 begins at historical Stocks 6/6, V3 0/0 and budget 0/6;
- exactly six blind proposals are frozen;
- A7 audits novelty/data/controls without repairing proposals;
- exactly two eligible families are selected or the run closes blocked;
- every eligible family has three immutable implemented arms;
- six-arm dummy dry-run is unique/idempotent and real counters remain 0/0;
- W1 and equal-twin staging are frozen;
- A7 returns `STOCKS_FREE_V3_S0_LAUNCH_AUTHORIZED`, or an honest blocker;
- no scored V3 metric has been computed;
- S1 remains sealed;
- no paper/live/order/credential/purchase/network-fetch activity occurred;
- no push/main merge/worktree deletion/history rewrite occurred;
- all owned workers are zero and the integration tree is clean.

## 21. First report required from fresh A1

Before dispatch or writes beyond the exact plan-only commit, report:

```text
measured UTC
root absolute path / branch / full HEAD / porcelain
owner PLAN_stocks commit SHA
untracked .v2c disposition (preserved, not added)
local V2 integration path / branch / full HEAD / clean status
V2 effective verdict / A7 verdict / 6/6 reproduction
V2 observed/published counters and S1 seal
V2R worktree path / branch / bootstrap SHA
active workers and PIDs
RAM / CPU / disk / preliminary heavy cap
GO/NO_GO for V2R metadata-only reconciliation
```

After the first report A1 continues autonomously through safe local phases. It
stops only for identity/data/scientific blockers, credentials or purchases,
push/main merge/deletion, S1/live boundaries, or immediately before the first
V3 scored cell.
