# PLAN_FOREX — G10 SPOT-FX RESEARCH FACTORY

> Owner-requested implementation plan for spot foreign exchange. This is a
> separate asset-class track. It reuses the scientific research core but never
> reuses crypto funding, 24/7 calendars, Binance volume, USDT accounting or
> equity corporate-action assumptions. No credentials, paid data, paper/live
> orders, remote push or main merge are authorized by this document.

## 0. Outcome and dependency

Create a reproducible G10 spot-FX research factory with bid/ask-aware execution,
multi-currency accounting, session/DST correctness and rollover costs.

Preferred dependency:

```text
MULTIASSET_CORE_SHA from PLAN_stocks Phase M0
```

If stocks has not run, the forex owner may explicitly assign A2 to create the
same shared core. Stocks and forex must never edit `research/assets/common/**`
concurrently. The first accepted common-core commit becomes the sole bootstrap
for both tracks.

Entry checks:

- root/current integration SHA and dirty files;
- shared-core ownership and compatibility status;
- approved data/broker provider and entitlement status;
- timestamp, bid/ask and rollover availability;
- base account currency and conversion graph;
- CPU/RAM/heavy-worker cap;
- no existing forex score or S1 access.

Without authoritative bid/ask and rollover evidence, only synthetic engineering
is allowed; scoring closes `FOREX_BLOCKED_DATA_OR_ROLLOVER_AUTHORITY`.

## 1. Scope

### In scope

- spot G10 FX, initial frozen candidates:
  `EURUSD`, `GBPUSD`, `USDJPY`, `AUDUSD`, `USDCAD`, `USDCHF`, `NZDUSD`;
- optional liquid crosses only after point-in-time coverage and conversion gates;
- USD reporting account with explicit base/quote conversions;
- 1h base event clock and daily/weekly low-turnover signals by default;
- 24/5 session model, DST, weekend closure and New York rollover;
- bid/ask fills, spread, commission and swap/rollover accounting;
- S0 screening and separately sealed future S1;
- shared-capital portfolio with currency exposure caps.

### Out of scope

- CFDs presented as spot without an explicit instrument/financing contract;
- crypto pairs, commodities, futures and NDFs;
- centralized-volume claims from a single dealer feed;
- 1m/2m HFT without quote/order-book evidence;
- leverage deployment, paper/live orders and credentials;
- paid data purchase without owner approval;
- mixing FX trial statistics with crypto or stocks;
- tuning around NFP/FOMC outcomes after observing returns.

## 2. Provider and market model

NautilusTrader supports `CurrencyPair`, simulated FX venues and modular
adapters. Provider candidates:

1. owner-authorized institutional bid/ask quote provider;
2. Interactive Brokers historical/reference data and future separate paper
   adapter, subject to entitlement and pacing limits;
3. owner-supplied normalized Parquet with provider documentation;
4. midpoint-only public data for `DIAGNOSTIC_ONLY`, never promotable evidence.

Freeze one provider before inspecting candidate PnL. Record venue/dealer scope:
FX is decentralized, so one feed is not labeled “the global FX market”.

Official references to freeze:

- `https://nautilustrader.io/docs/latest/concepts/instruments/`;
- `https://nautilustrader.io/docs/latest/integrations/interactive_brokers/`
  or the stable equivalent available at launch;
- provider timestamp, quote, commission and financing documentation;
- authoritative holiday/DST/rate sources for every currency.

## 3. Architecture

Reuse `research/assets/common/**` and add:

```text
research/assets/forex/
  provider.py
  instruments.py
  calendar.py
  sessions.py
  conversion.py
  rollover.py
  loader.py
  data_audit.py
  accounting.py
  execution.py
  portfolio.py
  reproduce.py
```

FX trial identity includes:

```text
asset_class=G10_SPOT_FX
provider/dealer id + schema digest
instrument and quote convention digest
calendar/session/DST digest
base-currency conversion digest
spread/commission/rollover digests
universe + family + arm_config digests
window/folds/purge/benchmark digests
```

Mid, bid and ask are distinct fields. No function may silently substitute mid
for an executable side.

## 4. Agent topology

Use **8 logical agents**, at most **A1 + 3 other active agents**. Heavy scoring
workers are controlled processes and run without unrelated coding agents.

| Role | Responsibility | Write ownership |
|---|---|---|
| A1 | controller, integration, freeze, ledgers and reports | forex authority files |
| A2 | shared core or forex compatibility adapter | `research/assets/common/**` only when assigned, compatibility tests |
| A3 | provider, instruments, quote loader and data audit | forex provider/loader/audit modules |
| A4 | sessions, holidays, DST and event clocks | forex calendar/session modules |
| A5 | conversion, rollover, accounting and execution costs | forex conversion/rollover/accounting/execution modules |
| A6 | selected family 1 implementation | one plugin + tests/goldens |
| A7 | independent novelty/prelaunch/terminal audit | `research/audits/forex/**` only |
| A8 | selected family 2 implementation | one plugin + tests/goldens |

Optimized waves:

```text
Wave F0: A1 + A2                         # consume/create shared core
Wave F1: A1 + A3 + A4 + A5              # correctness lanes
Wave F2: A1 + A3 + A4 + A5              # six independent proposals
Wave F3: A1 + A7                         # feasibility/novelty and freeze
Wave F4: A1 + A6 + A8                    # implementations
Wave F5: A1 + A7                         # prelaunch; full suite alone
Wave F6: A1 + measured heavy workers     # score/reproduce
Wave F7: A1 + A7                         # terminal audit
```

A7 never writes production code. Only A1 may merge or publish.

## 5. Worktree topology

```text
.worktrees/forex/integration       orca/forex-integration
.worktrees/forex/f0-common         orca/forex-f0-common
.worktrees/forex/f1-data           orca/forex-f1-data
.worktrees/forex/f1-calendar       orca/forex-f1-calendar
.worktrees/forex/f1-accounting     orca/forex-f1-accounting
.worktrees/forex/f3-a7-audit       orca/forex-f3-a7-audit
.worktrees/forex/f4-family-1       orca/forex-f4-family-1
.worktrees/forex/f4-family-2       orca/forex-f4-family-2
.worktrees/forex/f6-exec-1         detached at FOREX_W1
.worktrees/forex/f6-exec-2         detached at FOREX_W1
.worktrees/forex/f6-reproduce      detached at FOREX_W1
```

A1 creates and verifies paths/branch/full SHA/clean status before dispatch and
records non-overlapping allowlists in
`research/control/forex_run/worktree_manifest.json`.

### 5.1 A1 Forex integration-worktree bootstrap

The root checkout
`/Users/hoangminhlong/my-quantitative` is the owner/bootstrap checkout, not A1's
working directory. A1 Forex MUST run only in:

```text
path:   /Users/hoangminhlong/my-quantitative/.worktrees/forex/integration
branch: forex
```

Before creating A1, the owner/controller freezes `FOREX_OWNER_SHA` as a full
40-character commit SHA containing the approved PLAN files. The root checkout
must be on the expected owner branch and `git status --porcelain=v1` must be
empty. Uncommitted PLAN edits are not an authorized bootstrap.

Fresh creation uses:

```bash
git -C /Users/hoangminhlong/my-quantitative rev-parse HEAD
git -C /Users/hoangminhlong/my-quantitative branch --show-current
git -C /Users/hoangminhlong/my-quantitative status --porcelain=v1
git -C /Users/hoangminhlong/my-quantitative worktree list --porcelain
git -C /Users/hoangminhlong/my-quantitative worktree add \
  -b orca/forex-integration \
  /Users/hoangminhlong/my-quantitative/.worktrees/forex/integration \
  FOREX_OWNER_SHA
```

`FOREX_OWNER_SHA` is a placeholder and MUST be replaced by the measured full
SHA. Never pass the literal placeholder to Git. If the path or branch already
exists, do not rerun creation, force, delete or reset it. Inspect it:

```bash
git -C /Users/hoangminhlong/my-quantitative worktree list --porcelain
git -C /Users/hoangminhlong/my-quantitative/.worktrees/forex/integration rev-parse HEAD
git -C /Users/hoangminhlong/my-quantitative/.worktrees/forex/integration branch --show-current
git -C /Users/hoangminhlong/my-quantitative/.worktrees/forex/integration status --porcelain=v1
```

Resume only if path, branch, expected ancestry and recorded manifest agree. A
dirty tree, missing path, unexpected branch or unexplained SHA is
`FOREX_A1_WORKTREE_IDENTITY_MISMATCH`; stop before writing.

The A1 launch prompt MUST contain:

```text
ROLE: A1 Forex controller and sole integration authority
WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/forex/integration
BRANCH: orca/forex-integration
OWNER_SHA: <full 40-character FOREX_OWNER_SHA>
SHARED_CORE_SHA: <full MULTIASSET_CORE_SHA, or BLOCKED_PENDING_CORE>
READ FIRST: PLAN_forex.md, PLAN_stocks.md, PLAN.md, NOTES.md
ROOT CHECKOUT: read-only after bootstrap; never implement from root/main
AUTHORITY: create forex lane worktrees, manifests, freezes and gate records
FORBIDDEN: implement a competing common core, edit stocks/V11 ledgers,
           run scored S1, merge main, push, delete or reset
FIRST ACTION: print pwd, HEAD, branch and porcelain status; stop on mismatch
```

Launch the A1 agent with the absolute integration path as `cwd`. An IDE tab or
terminal opened at repo root does not authorize A1 to work there. Never launch
A1 Forex and another A1 into the same worktree.

If `MULTIASSET_CORE_SHA` is not frozen, A1 records
`BLOCKED_PENDING_CORE`. It may perform read-only intake/provider checks, but it
must not dispatch A2 to create a competing `research/assets/common/**`. Once
the owner-authorized core SHA is available, A1 integrates that exact commit,
runs F0 compatibility and records the resulting full `FOREX_F0_SHA` before F1.

### 5.2 A1 creation of Forex lane worktrees

For each wave, A1 commits the controlling manifest on integration and freezes
a full `FOREX_WAVE_SHA`. Every lane in that wave starts from that SHA, not from
moving `main`, the Stocks integration tip or an uncommitted shared-core tree.
Example for the F1 data lane:

```bash
git -C /Users/hoangminhlong/my-quantitative worktree add \
  -b orca/forex-f1-data \
  /Users/hoangminhlong/my-quantitative/.worktrees/forex/f1-data \
  FOREX_WAVE_SHA
git -C /Users/hoangminhlong/my-quantitative/.worktrees/forex/f1-data rev-parse HEAD
git -C /Users/hoangminhlong/my-quantitative/.worktrees/forex/f1-data branch --show-current
git -C /Users/hoangminhlong/my-quantitative/.worktrees/forex/f1-data status --porcelain=v1
```

Replace `FOREX_WAVE_SHA` with the measured full SHA. Required output is that
SHA, branch `orca/forex-f1-data` and empty status. A1 records identity,
allowed/forbidden globs, tests, deliverables and merge order in
`worktree_manifest.json`, commits it, then dispatches the lane. Apply the same
pattern to every listed Forex worktree.

Only A1 cherry-picks one lane commit at a time and tests after each pick.
Subagents never merge, rebase, amend, push, edit central ledgers or reuse a
completed worktree for a different task.

When Stocks and Forex share one host, concurrency is machine-wide. Two A1
controllers may remain active, but light-agent, full-pytest and heavy-worker
caps are divided across the host based on a fresh resource probe; they are not
doubled merely because two PLAN files each state a cap.

## 6. Phase F0 — common-core compatibility

Consume the frozen `MULTIASSET_CORE_SHA` and prove:

- crypto manifests remain readable and immutable;
- stocks fields, when present, do not leak into FX requirements;
- carrying-cost interface accepts FX rollover without calling it funding;
- execution-cost interface supports side-specific bid/ask fills;
- trial identity includes asset class and cannot collide with crypto/stocks;
- separate forex published and observed denominators;
- one global read-only index references all asset ledgers without combining
  incomparable PBO samples.

If no common core exists, A2 implements these items once and produces the
shared SHA before F1 begins.

## 7. Phase F1 — three correctness lanes

### A3 — provider, instruments and data audit

Required fields:

- event and ingest timestamps in UTC;
- bid/ask OHLC or quotes, plus midpoint derived explicitly;
- symbol/base/quote, pip/tick, size increment and trading status;
- provider/dealer identity and timezone convention;
- accepted/rejected pairs at every decision;
- missing/duplicate/stale quote evidence;
- checksum manifest and exact provider query.

Initial data floors:

- at least 8 years of 1h bid/ask history for the seven initial pairs;
- common interval includes multiple volatility and rate regimes;
- no silent weekend bar synthesis;
- stale quotes and crossed/negative spreads fail closed;
- provider gaps classified by session calendar rather than fixed 24/7 cadence.

S0 end is frozen no later than twelve months before latest complete coverage.
The next non-overlapping period is sealed S1 and not opened in this sprint.

### A4 — sessions, holidays, DST and macro clocks

Implement:

- trading week open/close with provider-specific Sunday/Monday convention;
- Sydney/Tokyo/London/New York session labels;
- DST transitions by named timezones, never fixed UTC offsets;
- weekend and major currency holiday closures;
- New York rollover boundary and shortened/illiquid sessions;
- scheduled macro-event timestamps from an authoritative PIT source when used;
- no post-release timestamp backfill into pre-release features.

Session labels are context unless preregistered as a signal. A session filter
added after PnL observation is a new family/trial.

### A5 — multi-currency accounting, rollover and execution

Canonical USD identity:

```text
ending_USD - starting_USD
= realized_price_pnl_USD + terminal_pnl_USD
 + rollover_cashflows_USD + explicit_interest_USD
 - commissions_USD - spread_USD - slippage_USD
 - market_impact_USD - rejection_costs_USD
```

Required correctness:

- PnL in quote currency converted through a timestamp-aligned conversion graph;
- inverse pairs and JPY pip conventions tested by hand-computed goldens;
- bid used to sell/close longs, ask used to buy/close shorts;
- variable spread by pair/session, not one global pip;
- swap/rollover from provider/broker schedule with long/short asymmetry;
- triple-roll and holiday adjustments explicitly modeled;
- margin/exposure reported by underlying currency, not only by pair;
- terminal close uses an executable quote, never midpoint by default;
- unavailable conversion or rollover data fails closed.

## 8. F1 integration and correctness gates

A1 cherry-picks A3, A4, A5 in that order and runs:

```bash
.venv/bin/python -m pytest tests/assets/forex -q
.venv/bin/python -m pytest tests/test_protocol_contracts.py tests/test_protocol_metrics.py -q
.venv/bin/python -m compileall research/assets/forex research/assets/common
git diff --check
```

Required gates:

- `FX0_QUOTE_DATA_PASS`;
- `FX1_SESSION_DST_PASS`;
- `FX2_BID_ASK_EXECUTION_PASS`;
- `FX3_CONVERSION_GRAPH_PASS`;
- `FX4_ROLLOVER_PASS`;
- `FX5_ACCOUNTING_IDENTITY_PASS`;
- `FX6_CRYPTO_STOCK_COMPATIBILITY_PASS`;
- tests leave tracked files unchanged.

## 9. Phase F2 — outcome-blind family discovery

A3/A4/A5 each propose exactly two mechanisms, six total. They may use academic
and central-bank literature plus official provider documentation, but may not
compute scored PnL or see another proposal lane.

Every proposal declares:

- economic mechanism and expected counterparty;
- signal fields and publication clock;
- formation/holding/rebalance horizon;
- pair universe and currency-neutralization method;
- expected spread, rollover and turnover;
- anchor, justified neighbour and causal negative control;
- expected regimes and falsification;
- macro/session external-validity risks;
- exact trial count and no post-score replacement.

Priority spaces:

- slow time-series trend with volatility targeting;
- rate-differential/carry only with authoritative rollover inputs;
- cross-sectional value or real-rate differential with PIT macro vintages;
- session/overnight risk premium with correct DST clocks;
- defensive USD/regime exposure with explicit benchmark decomposition.

Prohibited shortcuts:

- RSI/EMA parameter grids without mechanism;
- single-provider volume treated as global FX volume;
- carry computed from today's rate applied historically;
- session filters selected after seeing profitable hours;
- midpoint backtests labeled executable.

A7 audits source authority, novelty, data/rollover feasibility, similarity to
old crypto families and prewindow signal correlations. A1 selects exactly two
eligible families by frozen rubric. Fewer than two closes
`FOREX_BLOCKED_SELECTION_INSUFFICIENT`.

## 10. Freeze and implementations

Freeze per selected family:

- immutable hypothesis/spec and literature mapping;
- exact family, anchor, neighbour and negative-control ids/digests;
- provider/instrument/calendar/session/conversion/rollover/cost hashes;
- S0 window/folds/warmup/purge and terminal policy;
- flat, cash-rate and declared FX benchmark context;
- pair and currency exposure limits;
- total budget `0/6`.

A6 and A8 implement one family each with non-overlapping plugins. Required:

- PIT features and publication-lag tests;
- hand-calculated bid/ask, JPY, inverse and rollover goldens;
- deterministic schedule/targets;
- currency exposure and conversion tests;
- schedule-only cost/turnover gate;
- anchor/neighbour/control identity uniqueness;
- exact-arm dry run to temporary ledger;
- clean single-commit handoff.

## 11. Integrated QA and A7 authorization

A1 integrates one family at a time, then:

- targeted adapter/family tests;
- six-arm temporary-ledger dry run and idempotent replay;
- full suite alone;
- loader-resolved quote/session/rollover/conversion audit;
- freeze `FOREX_W1` and detached exec/reproduction trees;
- byte-identical staged manifests.

A7 independently recomputes all pins and gates. Scoring requires
`FOREX_S0_LAUNCH_AUTHORIZED`, budget `0/6`, no S1 access, no unresolved
HIGH/CRITICAL and enough measured resources/time for complete family chains.

## 12. Scoring and stresses

Each family runs anchor -> neighbour -> negative control serially. Two family
chains may run concurrently only with isolated outputs and heavy cap >=2.

Mandatory stresses:

- spread x1.5 and x2 during illiquid-session scenario;
- one-event execution delay;
- commission/slippage increase;
- rollover x1.5 and adverse long/short schedule;
- DST-boundary and weekend-gap subsets;
- remove one pair, one currency and one fold;
- London-only, New-York-only and full-declared-session context reports;
- conversion-path and stale-quote failure injection;
- currency, pair and USD-regime concentration.

Every computed cell increments the forex observed counter once regardless of
publication success.

## 13. FX Stage-A gates

All applicable requirements:

- after-cost/rollover expectancy > 0 and position PF >=1.10;
- at least 2/3 chronological folds positive;
- no populated fold PF <0.80;
- MDD <=12%;
- no fold >50% of positive PnL;
- no pair >30% and no underlying currency >40% of risk/PnL contribution;
- stressed PnL >0 and stressed PF >=1.00;
- positive result not explained solely by USD direction unless preregistered;
- neighbour supports anchor and negative control weakens mechanism;
- drop-one-pair/currency/fold survival;
- bid/ask, rollover, session and conversion reconciliation PASS;
- exact reproduction and terminal A7 PASS.

The strongest allowed label is
`FOREX_STAGE_A_SURVIVOR_LOCKED_FOR_FUTURE_S1`; no paper/live authority follows.

## 14. Control artifacts

```text
research/control/forex_run/run_contract.json
research/control/forex_run/state.json
research/control/forex_run/heartbeat.json
research/control/forex_run/event_log.jsonl
research/control/forex_run/worktree_manifest.json
research/control/forex_run/data_manifest.json
research/control/forex_run/session_calendar_manifest.json
research/control/forex_run/rollover_manifest.json
research/control/forex_run/conversion_manifest.json
research/control/forex_run/selection_freeze.json
research/control/forex_run/prelaunch_verdict.json
research/control/forex_run/terminal_report.json
research/audits/forex/**
```

Large quote data stays outside Git. Forex ledgers live at
`results/registry/forex/`; crypto/stocks ledgers remain read-only.

## 15. Error-check and gate-evidence matrix

Every gate is a machine-readable record under
`research/control/forex_run/gates/`. Each record MUST contain:

```text
gate_id, measured_at_utc, owner, integration_sha, command
exit_code, status=PASS|FAIL|NOT_RUN, expected, observed
stdout_log, stderr_log, input_digests, output_digests
blockers, corrective_action, auditor, auditor_verdict
```

Rules:

- A1 runs commands from the clean integration worktree; lane-local output is
  supporting evidence only.
- A7 independently checks hashes and conclusions and never repairs production
  code.
- Missing tests, inputs, quote sides, rollover schedules, outputs or logs are
  `NOT_RUN`, never inferred PASS.
- A non-zero exit, stale SHA, digest mismatch, accounting mismatch or unexpected
  tracked-file mutation is `FAIL`.
- Every required FAIL/NOT_RUN blocks the dependent wave and is appended to the
  event log before a repair is dispatched.
- The test paths below are required deliverables. Their absence means the gate
  cannot run.

| Gate | Exact command from integration root | Expected result | Evidence | Owner | Failure action |
|---|---|---|---|---|---|
| `F0_PASS` | `.venv/bin/python -m pytest tests/assets/common tests/test_protocol_contracts.py tests/test_protocol_metrics.py -q` | shared identities remain asset-safe; crypto/stocks fixtures remain readable | `gates/F0_PASS.json` plus pytest log | A2, verified A1/A7 | stop F0; do not create F1 lanes |
| `FX0_QUOTE_DATA_PASS` | `.venv/bin/python -m pytest tests/assets/forex/test_quote_data.py tests/assets/forex/test_instruments.py -q` | bid/ask integrity, timestamps, gaps, staleness and pair metadata PASS | `gates/FX0_QUOTE_DATA_PASS.json` and `data_manifest.json` | A3 | quarantine affected partitions; no proposals |
| `FX1_SESSION_DST_PASS` | `.venv/bin/python -m pytest tests/assets/forex/test_sessions_dst.py -q` | weekly boundary, named-zone DST, holidays and rollover clocks PASS | `gates/FX1_SESSION_DST_PASS.json` and `session_calendar_manifest.json` | A4 | block features, fills and scoring |
| `FX2_BID_ASK_EXECUTION_PASS` | `.venv/bin/python -m pytest tests/assets/forex/test_execution.py -q` | executable side, variable spread, stale/crossed quote and terminal-fill goldens PASS | `gates/FX2_BID_ASK_EXECUTION_PASS.json` | A5 | prohibit midpoint fallback; repair execution lane |
| `FX3_CONVERSION_GRAPH_PASS` | `.venv/bin/python -m pytest tests/assets/forex/test_conversion.py -q` | USD conversion, inverse pair, JPY pip and missing-path goldens PASS | `gates/FX3_CONVERSION_GRAPH_PASS.json` and `conversion_manifest.json` | A5 | no USD metrics or scored cells |
| `FX4_ROLLOVER_PASS` | `.venv/bin/python -m pytest tests/assets/forex/test_rollover.py -q` | long/short asymmetry, triple-roll and holiday adjustments match authoritative schedule | `gates/FX4_ROLLOVER_PASS.json` and `rollover_manifest.json` | A5 | block carry families and terminal accounting |
| `FX5_ACCOUNTING_IDENTITY_PASS` | `.venv/bin/python -m pytest tests/assets/forex/test_accounting.py -q` | hand-computed price PnL, conversion, rollover, costs and equity identity close | `gates/FX5_ACCOUNTING_IDENTITY_PASS.json` | A5 | isolate first mismatching ledger row; no dry run |
| `FX6_CRYPTO_STOCK_COMPATIBILITY_PASS` | `.venv/bin/python -m pytest tests/test_protocol_contracts.py tests/test_protocol_metrics.py tests/test_protocol_registry.py tests/test_protocol_reproduce.py -q` | historical ledgers remain readable and immutable; trial ids cannot collide | `gates/FX6_CRYPTO_STOCK_COMPATIBILITY_PASS.json` | A2 | revert shared-core delta; forex cannot proceed |
| `FOREX_FREEZE_PASS` | `.venv/bin/python -m pytest tests/assets/forex/test_selection_freeze.py -q` | exactly two families, six unique arm keys, immutable hashes, budget `0/6` | `gates/FOREX_FREEZE_PASS.json` and `selection_freeze.json` | A1/A7 | invalidate selection; do not spawn A6/A8 |
| `FOREX_DRYRUN_PASS` | `.venv/bin/python -m pytest tests/assets/forex/test_six_arm_dryrun.py -q` | six first publications, six idempotent replays and zero S1 access | `gates/FOREX_DRYRUN_PASS.json` plus temporary-ledger digest | A1/A7 | delete only temporary outputs; repair before W1 |
| `FOREX_STRESS_PASS` | `.venv/bin/python -m pytest tests/assets/forex/test_stage_a_stresses.py -q` | all spread, rollover, delay, DST and drop-one stresses reconcile | `gates/FOREX_STRESS_PASS.json` | A1/A7 | affected family is non-promotable; no replacement arm |
| `FOREX_REPRO_PASS` | `.venv/bin/python -m pytest tests/assets/forex/test_reproduction.py -q` | clean-process reproduction is exact for all 6/6 cells and canonical artifacts | `gates/FOREX_REPRO_PASS.json` plus comparison manifest | reproduce worker/A7 | terminal result is `INCOMPLETE_NOT_PROMOTABLE` or `REJECT_ALL` |
| `FOREX_A7_TERMINAL_PASS` | `.venv/bin/python -m pytest tests/assets/forex/test_terminal_contract.py -q` | pins, counters, ledgers, Stage-A decisions and findings reconcile | `gates/FOREX_A7_TERMINAL_PASS.json` and `terminal_report.json` | A7 | no delivery label stronger than `BLOCKED` |

Before and after every row A1 runs:

```bash
git rev-parse HEAD
git status --short --branch
git diff --check
```

Evidence is valid only when its `integration_sha` equals the tested HEAD and
`git status --porcelain=v1` is empty before and after. Explicit ignored provider
data remains outside Git. Any undeclared authority artifact is a failure.

## 16. Final delivery gate

After terminal artifacts are committed, A1 freezes `FOREX_DELIVERY_SHA`. Run
serially from a fresh detached worktree at that SHA, with no scoring worker or
other pytest process active. Its recorded scored source/config/input pin must
remain `FOREX_W1`; terminal evidence cannot change scored code or inputs:

```bash
git rev-parse HEAD
git status --porcelain=v1
.venv/bin/python -m pytest tests/assets/common tests/assets/forex -q
.venv/bin/python -m pytest tests/test_protocol_contracts.py tests/test_protocol_metrics.py tests/test_protocol_registry.py tests/test_protocol_reproduce.py -q
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall research/assets/common research/assets/forex
git diff --check
git status --porcelain=v1
```

Both status commands must print nothing. The full suite runs once and alone. A
failed complete check cannot be waived by a passing subset or an older log.

A1 completes `research/control/forex_run/final_delivery_checklist.json`:

| Check | PASS condition | If FAIL or NOT RUN |
|---|---|---|
| SHA and worktree | detached HEAD equals `FOREX_DELIVERY_SHA`; scored source/config/input pin equals `FOREX_W1`; tree clean before/after | stop delivery and regenerate evidence at the correct SHA |
| Test evidence | all commands above exit 0; exact counts and logs recorded | `INCOMPLETE_NOT_PROMOTABLE` |
| Gate completeness | all Section 15 required gates PASS at an allowed SHA | block terminal PASS |
| Data authority | provider entitlement, bid/ask coverage and timestamp manifests exist and match input hashes | `BLOCKED_DATA_AUTHORITY` |
| Session correctness | DST, holidays, weekend and New York rollover calendars reconcile | reject affected outputs; do not infer continuous 24/5 bars |
| Accounting | executable quote, conversion, rollover, costs and terminal equity reconcile | reject affected family; no midpoint/free-rollover fallback |
| Trial accounting | observed count includes every computation; published count/collisions reconcile; exactly `6/6` planned cells accounted for | block finalization until ledger reconciliation |
| S1 isolation | no process, log or manifest proves S1 access; sealed hashes unchanged | invalidate sprint; no Stage-A survivor label |
| Reproduction | fresh-process rerun matches every canonical digest and metric | `INCOMPLETE_NOT_PROMOTABLE` |
| Repository hygiene | no secret, credential, licensed quote payload or oversized raw data is tracked; allowlists reconcile | remove/quarantine unauthorized files and rerun affected gates |
| Worker shutdown | registry reports zero owned workers and no owned PID remains alive | stop workers, reconcile partial output, rerun terminal audit |
| Independent audit | A7 signs the exact SHA with zero unresolved HIGH/CRITICAL | no delivery authorization |
| Product boundary | no live, paper, testnet or order authority; survivor remains Stage-A only | correct all reports before delivery |

Use the repository-configured secret scanner when available. If none is
installed/configured, record `NOT_RUN` and perform a changed-file allowlist
review; never report automated secret-scan PASS. Licensed quote data remains
outside Git; only manifests and checksums are tracked.

Final verdict rules:

- `PASS`: every required check passes at the frozen SHA, reproduction is exact,
  A7 signs and the tree remains clean.
- `FAIL`: a completed check disproves correctness, integrity or a Stage-A gate.
- `NOT_RUN`: evidence is missing; a required NOT_RUN blocks PASS.
- `BLOCKED`: an external dependency such as entitlement, authoritative quote
  sides or rollover history prevents execution.

The delivery packet contains the frozen SHA, gate records/logs, data/session/
conversion/rollover hashes, both denominators, six cell verdicts, reproduction
comparison, A7 terminal report, limitations and the exact strongest label.
Pushing, merging `main`, purchasing data or starting paper/live execution needs
separate owner authorization.

## 17. Checkpoints and Definition of Done

A1 reports:

1. intake/shared-core/provider authority;
2. F0 compatibility;
3. F1 data/calendar/accounting commits and gates;
4. six proposals and A7 audit;
5. two-family freeze, budget `0/6`;
6. implementations, dry run, full suite and W1;
7. A7 prelaunch;
8. each scored cell and both counters;
9. reproduction and terminal audit.

Done requires 6/6 exact reproduction and terminal evidence, or an honest
`BLOCKED`, `REJECT_ALL` or `INCOMPLETE_NOT_PROMOTABLE` closeout with workers
zero. Missing quote sides, DST, rollover, conversion or provider evidence is
never inferred PASS.

## 18. First A1 report

```text
measured UTC
root/integration SHA and dirty files
MULTIASSET_CORE_SHA and owner
forex integration path/branch/bootstrap SHA
provider/dealer and entitlement status
quote/bid-ask/rollover coverage
base account currency and conversion authority
forex published/observed denominators
budget 0/6
agent slots: 8 logical, max A1 + 3 active
heavy-worker cap
GO/NO_GO for F0/F1 light lanes
```
