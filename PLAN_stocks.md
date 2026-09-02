# PLAN_STOCKS — US CASH-EQUITY RESEARCH FACTORY

> Owner-requested implementation plan. This document designs a separate research
> track for **real US cash equities and ETFs**, not Binance TradFi perpetuals.
> It authorizes planning and safe local engineering only; it does not authorize
> paid data purchases, credentials, paper/live orders, remote push or main merge.

## 0. Outcome and entry boundary

Build a stocks research track by reusing the existing scientific factory while
replacing every crypto-specific market assumption with an equity contract.

The reusable core includes hypothesis/family identity, immutable manifests,
trial accounting, chronological folds, gates, shared-capital replay, stress,
reproduction and independent audit. The following are **not reusable as-is**:
Binance symbols, `CryptoPerpetual`, 24/7 calendars, funding cashflows, 15m path
names, USDT accounting, crypto universe selection and crypto fee/fill models.

Entry measurements required before any agent is dispatched:

- root branch/SHA and dirty/untracked files;
- exact source SHA containing the reusable research core;
- whether a shared multi-asset abstraction SHA already exists;
- installed NautilusTrader version and available equity adapters;
- provider/data entitlements available **without buying anything**;
- CPU, RAM and safe heavy-worker count;
- proof that no stock scored ledger or S1 artifact already exists.

If data/provider authority is absent, engineering may finish with synthetic
goldens, but scored research closes `STOCKS_BLOCKED_DATA_AUTHORITY`.

## 1. Scope

### In scope

- US-listed common stocks and ETFs represented as true cash equities;
- USD base account, long and short research with borrow-aware feasibility;
- regular trading session as the canonical first baseline;
- daily signals with next-session or intraday execution events;
- point-in-time universe, security master and corporate actions;
- after-cost shared-capital research only;
- S0 screening followed by a separately sealed future S1.

### Explicitly out of scope

- Binance `TRADIFI_PERPETUAL` and tokenized-equity products;
- options, futures, CFDs, fractional-share assumptions and leverage deployment;
- live/paper orders, credentials or broker account mutation;
- paid dataset acquisition without owner approval;
- mixing stock trials with crypto/forex PBO populations;
- using adjusted prices for fills or raw prices for total-return signals without
  a declared transformation;
- post-score universe, parameter or corporate-action corrections that change
  results without creating a new trial identity.

## 2. Source and adapter policy

NautilusTrader already models `Equity` instruments and supports modular data/
execution adapters. Preferred provider order:

1. an owner-authorized point-in-time provider with delistings, security master,
   corporate actions and bid/ask or trade data;
2. Databento for historical US equities when entitlement is available;
3. Interactive Brokers for instrument/reference data and a future separate
   paper-execution phase;
4. owner-supplied Parquet/CSV through a tested read-only adapter.

Provider choice is frozen before data inspection. Data from free convenience
APIs is `DIAGNOSTIC_ONLY` unless it proves timestamps, adjustments, delistings
and corporate actions. Official references to pin in the contract:

- `https://nautilustrader.io/docs/latest/concepts/instruments/equity/`;
- `https://nautilustrader.io/docs/latest/integrations/`;
- `https://www.nyse.com/trade/hours-calendars`;
- provider-specific schema and adjustment documentation.

## 3. Shared architecture

Create or consume this boundary:

```text
research/assets/common/
  contracts.py          # asset-neutral experiment and data contracts
  calendar.py           # session interface, never a 24/7 default
  carrying_cost.py      # funding / borrow-dividend / FX rollover interface
  instrument.py         # normalized instrument metadata
  execution_cost.py     # commission, spread, impact and slippage interface
  trial_identity.py     # asset_class + venue + universe + arm digest

research/assets/stocks/
  provider.py
  calendar.py
  corporate_actions.py
  universe.py
  loader.py
  accounting.py
  execution.py
  data_audit.py
  portfolio.py
  reproduce.py
```

Existing crypto modules remain unchanged except for minimal imports into the
new common interface. A stock test must not write crypto artifacts or ledgers.

Stock experiment identity includes at minimum:

```text
asset_class=US_CASH_EQUITY
provider_id + provider_schema_digest
calendar_id + calendar_version
price_adjustment_policy
corporate_action_manifest_digest
universe_snapshot_digest
borrow_model_digest
commission_spread_impact_digest
family_id + arm_id + arm_config_digest
window/fold/purge/benchmark digests
```

## 4. Agent topology and concurrency

Use **8 logical agents total**, with **at most A1 + 3 other agents active**.
Heavy backtest workers are processes, not extra agents.

| Role | Responsibility | May write |
|---|---|---|
| A1 | controller, integration, manifests, freeze, publishing | authority/control files only |
| A2 | shared multi-asset contracts and compatibility | `research/assets/common/**`, dedicated tests |
| A3 | stock provider, PIT security master and universe | `research/assets/stocks/{provider,universe,loader,data_audit}.py`, tests |
| A4 | exchange calendar, sessions and corporate actions | `research/assets/stocks/{calendar,corporate_actions}.py`, tests |
| A5 | accounting, borrow/dividend and execution costs | `research/assets/stocks/{accounting,execution,portfolio}.py`, tests |
| A6 | selected family 1 implementation | one frozen plugin + tests/goldens |
| A7 | independent novelty, prelaunch and terminal audit | `research/audits/stocks/**` only |
| A8 | selected family 2 implementation | one frozen plugin + tests/goldens |

No agent except A1 merges, rebases, pushes, edits the central ledger or edits
another lane. A7 never implements production code.

Optimized waves:

```text
Wave M0: A1 + A2
Wave S1: A1 + A3 + A4 + A5
Wave S2: A1 + A3 + A4 + A5  # independent proposals, read-only production
Wave S3: A1 + A7             # audit and selection freeze
Wave S4: A1 + A6 + A8        # two family implementations
Wave S5: A1 + A7             # prelaunch audit; full suite alone
Wave S6: A1 + heavy workers  # scoring/reproduction; no coding agents
Wave S7: A1 + A7             # terminal audit
```

## 5. Worktrees and branches

> **Owner-approved amendment (2026-09-02):** for this sprint only, the top-level
> A1 integration branch is `stocks`, replacing `orca/stocks-integration` above.
> All subordinate lane branches keep their `orca/stocks-*` names. Measured at
> bootstrap: branch `stocks` already existed at the frozen
> `STOCKS_OWNER_SHA=b8876ef8e0f7dd235d66f5cae5bfd8fd9034147f` with no worktree
> attached; A1 attached it with `git worktree add <path> stocks` instead of
> force-creating a branch. Recorded in
> `research/control/stocks_run/intake.json`.

All paths stay inside the repo permission boundary:

```text
.worktrees/stocks/integration       stocks
.worktrees/stocks/m0-common         orca/stocks-m0-common
.worktrees/stocks/s1-data           orca/stocks-s1-data
.worktrees/stocks/s1-calendar       orca/stocks-s1-calendar
.worktrees/stocks/s1-accounting     orca/stocks-s1-accounting
.worktrees/stocks/s3-a7-audit       orca/stocks-s3-a7-audit
.worktrees/stocks/s4-family-1       orca/stocks-s4-family-1
.worktrees/stocks/s4-family-2       orca/stocks-s4-family-2
.worktrees/stocks/s6-exec-1         detached at STOCKS_W1
.worktrees/stocks/s6-exec-2         detached at STOCKS_W1
.worktrees/stocks/s6-reproduce      detached at STOCKS_W1
```

A1 creates every worktree from an explicit 40-character bootstrap SHA, verifies
HEAD/branch/clean status and records it in
`research/control/stocks_run/worktree_manifest.json` before dispatch.

### 5.1 A1 Stocks integration-worktree bootstrap

The root checkout
`/Users/hoangminhlong/my-quantitative` is the owner/bootstrap checkout, not A1's
working directory. A1 Stocks MUST run only in:

```text
path:   /Users/hoangminhlong/my-quantitative/.worktrees/stocks/integration
branch: stocks
```

Before creating A1, the owner/controller freezes `STOCKS_OWNER_SHA` as a full
40-character commit SHA containing the approved PLAN files. The root checkout
must be on the expected owner branch and `git status --porcelain=v1` must be
empty. Uncommitted PLAN edits are not a bootstrap SHA.

Fresh creation uses this exact pattern:

```bash
git -C /Users/hoangminhlong/my-quantitative rev-parse HEAD
git -C /Users/hoangminhlong/my-quantitative branch --show-current
git -C /Users/hoangminhlong/my-quantitative status --porcelain=v1
git -C /Users/hoangminhlong/my-quantitative worktree list --porcelain
git -C /Users/hoangminhlong/my-quantitative worktree add \
  -b stocks \
  /Users/hoangminhlong/my-quantitative/.worktrees/stocks/integration \
  STOCKS_OWNER_SHA
```

`STOCKS_OWNER_SHA` is a document placeholder. Replace it with the measured full
SHA; never pass the literal name to Git. If the path or branch already exists,
do not rerun `worktree add`, delete it, reset it or force-create a branch.
Inspect it instead:

```bash
git -C /Users/hoangminhlong/my-quantitative worktree list --porcelain
git -C /Users/hoangminhlong/my-quantitative/.worktrees/stocks/integration rev-parse HEAD
git -C /Users/hoangminhlong/my-quantitative/.worktrees/stocks/integration branch --show-current
git -C /Users/hoangminhlong/my-quantitative/.worktrees/stocks/integration status --porcelain=v1
```

Resume only if path, branch, expected ancestry and manifest identity agree. A
dirty tree, missing path, unexpected branch or unexplained SHA is
`STOCKS_A1_WORKTREE_IDENTITY_MISMATCH`; stop before writing and report it.

The A1 launch prompt MUST include:

```text
ROLE: A1 Stocks controller and sole integration authority
WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/stocks/integration
BRANCH: stocks
OWNER_SHA: <full 40-character STOCKS_OWNER_SHA>
READ FIRST: PLAN_stocks.md, PLAN.md, NOTES.md, research/wayfinder/MAP.md
ROOT CHECKOUT: read-only after bootstrap; never implement from root/main
AUTHORITY: create lane worktrees, manifests, freezes and gate records
FORBIDDEN: edit forex/V11 ledgers, run scored S1, merge main, push, delete/reset
FIRST ACTION: print pwd, HEAD, branch and porcelain status; stop on mismatch
```

The controller launches the A1 agent with the absolute integration path as its
`cwd`; opening a PLAN in the root IDE does not change that `cwd`. Never launch
A1 Stocks and A1 Forex into the same worktree or tell either agent to choose a
worktree for itself.

### 5.2 A1 creation of Stocks lane worktrees

A1 first commits the intake manifest on `stocks` and freezes a
full `STOCKS_WAVE_SHA`. Every lane in that wave branches from that exact SHA,
not from moving `main` and not automatically from `STOCKS_OWNER_SHA`. Example
for M0:

```bash
git -C /Users/hoangminhlong/my-quantitative worktree add \
  -b orca/stocks-m0-common \
  /Users/hoangminhlong/my-quantitative/.worktrees/stocks/m0-common \
  STOCKS_WAVE_SHA
git -C /Users/hoangminhlong/my-quantitative/.worktrees/stocks/m0-common rev-parse HEAD
git -C /Users/hoangminhlong/my-quantitative/.worktrees/stocks/m0-common branch --show-current
git -C /Users/hoangminhlong/my-quantitative/.worktrees/stocks/m0-common status --porcelain=v1
```

Again, replace `STOCKS_WAVE_SHA` with the measured full SHA. Required output is
that SHA, branch `orca/stocks-m0-common` and an empty status. A1 writes those
values plus allowed/forbidden globs, tests, deliverables and merge order into
`worktree_manifest.json`, commits the manifest on integration, and only then
dispatches A2. Apply the same pattern to every path/branch in Section 5.

Only A1 cherry-picks lane commits, one at a time, in the declared order. It
runs targeted tests after every pick. Subagents never merge, rebase, amend,
push, edit central ledgers or reuse a completed lane for unrelated work.

When Stocks and Forex A1 run on the same host, the resource limit is
machine-wide: do not interpret each PLAN's `A1 + 3` as permission for eight
simultaneous agents. Full pytest and heavy scoring remain exclusive according
to the fresh host resource probe.

## 6. Phase M0 — extract the reusable multi-asset core

A2 replaces crypto-only names in new interfaces without changing historical
crypto artifact bytes or verdicts.

Required deliverables:

- asset-neutral carrying-cost and execution-cost interfaces;
- `asset_class`, `venue`, `calendar_id`, `cost_model_id` in new manifests;
- explicit migration adapter for old crypto manifests;
- separate asset-class ledgers plus one read-only global trial index;
- position-PnL PF kept separate from return-series PF;
- exact arm identity and observed-vs-published counters;
- compatibility tests proving old crypto results parse identically.

Gate `M0_PASS` requires targeted compatibility PASS, double serialization
determinism and zero mutation of tracked historical artifacts.

Default ownership: this stocks sprint creates `MULTIASSET_CORE_SHA`. If forex
runs first, the owner must explicitly transfer M0 ownership; both sprints may
not implement the same common files concurrently.

## 7. Phase S1 — stock market correctness lanes

### A3 — data, security master and point-in-time universe

Required data contract:

- raw OHLCV/trades or quotes with exchange timestamps and ingest timestamps;
- stable security identifier plus ticker-history mapping;
- listing/delisting dates and exchange/primary-listing identity;
- dividends, splits and other mandatory actions with ex/effective timestamps;
- accepted and rejected universe rows at each rebalance;
- no current-index-membership backfill into history;
- checksum manifest and provider query/entitlement record.

Initial S0 floors:

- at least 8 years of daily history across the common eligible population;
- at least 3 years of intraday data if intraday fills are scored;
- at least 30 eligible liquid names per decision for cross-sectional families;
- no unexplained regular-session gap after applying the official calendar;
- delisted observations retained through their final valid event.

Dates are frozen at intake from actual coverage. S0 ends no later than twelve
months before the latest complete provider date. The following non-overlapping
period is sealed as S1 and never opened during this sprint.

### A4 — calendar, sessions and corporate actions

Implement and test:

- NYSE/Nasdaq regular session, holidays, DST and early closes;
- pre/post-market represented separately, disabled in baseline scoring;
- opening/closing auction flags when provider supports them;
- overnight gaps are returns, not fabricated missing bars;
- suspension/halt and no-print intervals fail closed or carry explicit reason;
- raw-price fill path and total-return/adjusted research path reconciliation;
- split/dividend application at the correct ex/effective event;
- earnings timestamps are PIT and classified before/after market.

Never manufacture a weekly calendar and call it an official historical
calendar. Calendar/version drift creates a new data manifest.

### A5 — accounting, borrow and execution

Canonical identity:

```text
ending_equity - starting_equity
= realized_price_pnl + terminal_pnl + cash_dividends
 - commissions - spread - slippage - market_impact
 - short_borrow_fees - short_dividend_liability - rejection_costs
```

Required models:

- venue/broker commission schedule;
- bid/ask spread from quotes or a conservative evidenced proxy;
- participation/ADV market impact and order-size caps;
- locate availability and point-in-time borrow rate for every short;
- short dividend liability;
- cash dividend receipt for longs;
- no fill on halt/closed session/missing quote;
- terminal valuation on the last observable executable event.

Unavailable borrow means the short is rejected, never filled for free.

## 8. S1 integration gates

A1 cherry-picks A3, then A4, then A5. After each pick run targeted tests. Then:

```bash
.venv/bin/python -m pytest tests/assets/stocks -q
.venv/bin/python -m pytest tests/test_protocol_contracts.py tests/test_protocol_metrics.py -q
.venv/bin/python -m compileall research/assets/stocks research/assets/common
git diff --check
```

Required stock factory gates:

- `SD0_DATA_PIT_PASS`;
- `SD1_CALENDAR_PASS`;
- `SD2_CORPORATE_ACTION_PASS`;
- `SD3_ACCOUNTING_IDENTITY_PASS`;
- `SD4_BORROW_DIVIDEND_PASS`;
- `SD5_EXECUTION_COST_PASS`;
- `SD6_CRYPTO_COMPATIBILITY_PASS`;
- clean tree before/after tests.

## 9. Phase S2 — outcome-blind family discovery

A3, A4 and A5 each produce exactly two literature-backed mechanism proposals,
six total, without computing scored-window PnL and without seeing other lanes.

Each proposal declares:

- economic mechanism and expected counterparty;
- PIT fields and source authority;
- universe/sector neutralization and benchmark;
- formation, holding and execution clocks;
- expected turnover and capacity;
- anchor, justified neighbour and causal negative control;
- corporate-action, earnings, borrow and dividend treatment;
- falsification rule and external-validity caveats;
- exact maximum trial count.

Priority spaces, not automatic selections:

- sector-neutral residual/downside-risk or quality-risk factors;
- post-earnings drift with timestamp-safe surprise data;
- slow cross-sectional momentum with sector/beta neutrality;
- defensive overnight/intraday decomposition;
- liquidity provision only if quotes and impact data are sufficient.

Simple indicator/lookback grids without a mechanism are ineligible.

A7 independently audits six proposals for novelty, source quality, correlation,
data readiness, cost/borrow feasibility and hidden crypto-family rescue. A1
selects exactly two eligible families by frozen rubric; fewer than two closes
`STOCKS_BLOCKED_SELECTION_INSUFFICIENT`.

## 10. Phase S3/S4 — freeze and implementation

Freeze for each selected family:

- immutable JSON+Markdown spec;
- exact family/arm ids and config digests;
- anchor, neighbour, negative control;
- provider/calendar/universe/action/cost hashes;
- S0 folds, warmup, purge/embargo and terminal policy;
- benchmark set: flat, SPY total return and declared factor-neutral context;
- budget `0/6` total computed cells.

A6 and A8 implement one family each through the shared adapter. They may not
edit common contracts, central registry or each other's files. Required tests:

- PIT feature vectors and no future membership/actions;
- synthetic expected-sign and control-destruction tests;
- deterministic schedules and target books;
- borrow/dividend/corporate-action goldens;
- schedule-only turnover and cost feasibility;
- exact-arm temporary-ledger dry run;
- double-generation equality and clean handoff commit.

## 11. Phase S5 — integrated QA and A7 prelaunch

A1 integrates family commits one at a time, adds minimal central wiring, then:

- targeted family and adapter tests;
- six-arm dry run into an empty temporary stock ledger;
- six distinct keys, six first publications, six idempotent replays;
- full suite alone with no heavy worker;
- coverage/corporate-action/borrow audit against loader-resolved values;
- freeze `STOCKS_W1` and detached execution/reproduction trees;
- byte-identical staged-data manifests.

A7 independently recomputes the entire pin chain. Launch requires explicit
`STOCKS_S0_LAUNCH_AUTHORIZED`, zero unresolved HIGH/CRITICAL, budget `0/6`, no
S1 access and enough time/resources to finish at least one complete family.

## 12. Phase S6 — scored cells and stress

Each family runs serially: anchor, neighbour, negative control. Two families
may run concurrently only when the measured heavy cap is at least two and
outputs/ledger shards are isolated.

Per-cell mandatory stresses:

- commission and spread x1.5;
- one-event entry delay;
- impact at declared ADV participation caps;
- borrow rate x2 and borrow-unavailable scenario;
- dividend and corporate-action reconciliation;
- drop-one-symbol, drop-one-sector and drop-one-fold;
- regular-session-only versus declared alternate session context;
- benchmark and concentration decomposition.

Every computed score increments the stock observed counter even if publication
fails. No result may modify later frozen cells.

## 13. Stock Stage-A gates

Per family, all applicable gates must pass:

- after-cost expectancy > 0 and position PF >= 1.10;
- at least 2/3 chronological folds positive;
- no populated fold PF < 0.80;
- MDD <= 15%;
- no fold > 50% of positive PnL;
- no symbol > 25% and no sector > 35% of positive PnL/risk;
- stress PnL > 0 and stress PF >= 1.00;
- neighbour supports anchor;
- negative control destroys or materially weakens the mechanism;
- drop-one-symbol/sector/fold survival;
- capacity, turnover, borrow and corporate-action gates remain valid;
- exact reproduction and A7 terminal PASS.

A survivor is only `STOCKS_STAGE_A_SURVIVOR_LOCKED_FOR_FUTURE_S1`. It is not
live-ready and S1 remains sealed.

## 14. Artifacts and ledgers

Tracked authority artifacts:

```text
research/control/stocks_run/run_contract.json
research/control/stocks_run/state.json
research/control/stocks_run/heartbeat.json
research/control/stocks_run/event_log.jsonl
research/control/stocks_run/worktree_manifest.json
research/control/stocks_run/data_manifest.json
research/control/stocks_run/calendar_manifest.json
research/control/stocks_run/corporate_action_manifest.json
research/control/stocks_run/selection_freeze.json
research/control/stocks_run/prelaunch_verdict.json
research/control/stocks_run/terminal_report.json
research/audits/stocks/**
```

Large provider data stays outside Git. Stock ledgers live under
`results/registry/stocks/`; crypto/forex ledger bytes are read-only.

## 15. Error-check and gate-evidence matrix

Every gate is a machine-readable record under
`research/control/stocks_run/gates/`. Each record MUST contain:

```text
gate_id, measured_at_utc, owner, integration_sha, command
exit_code, status=PASS|FAIL|NOT_RUN, expected, observed
stdout_log, stderr_log, input_digests, output_digests
blockers, corrective_action, auditor, auditor_verdict
```

Rules:

- A1 runs the command from the clean integration worktree; an agent's claimed
  result is not integration evidence.
- A7 checks evidence and hashes independently; A7 does not repair failures.
- A missing test, missing input, missing output, interrupted command or stale
  SHA is `NOT_RUN`, never `PASS`.
- A non-zero exit, digest mismatch, unresolved warning affecting correctness or
  unexpected tracked-file mutation is `FAIL`.
- Every required `FAIL` or `NOT_RUN` blocks the next dependent wave. A1 records
  the failure before dispatching a repair lane.
- The test paths below are part of the implementation contract. If they do not
  exist yet, their owning lane must create them before requesting integration.

| Gate | Exact command from integration root | Expected result | Evidence | Owner | Failure action |
|---|---|---|---|---|---|
| `M0_PASS` | `.venv/bin/python -m pytest tests/assets/common tests/test_protocol_contracts.py tests/test_protocol_metrics.py -q` | old manifests parse identically; asset-class identities cannot collide | `gates/M0_PASS.json` plus pytest log | A2, verified A1/A7 | stop M0; do not create S1 lanes |
| `SD0_DATA_PIT_PASS` | `.venv/bin/python -m pytest tests/assets/stocks/test_data_pit.py tests/assets/stocks/test_universe.py -q` | PIT membership, identifiers, gaps and delistings PASS | `gates/SD0_DATA_PIT_PASS.json` and `data_manifest.json` | A3 | quarantine bad partitions; no family proposals |
| `SD1_CALENDAR_PASS` | `.venv/bin/python -m pytest tests/assets/stocks/test_calendar.py -q` | holidays, DST, early close, halt and overnight goldens PASS | `gates/SD1_CALENDAR_PASS.json` and `calendar_manifest.json` | A4 | freeze calendar lane; classify calendar/version defect |
| `SD2_CORPORATE_ACTION_PASS` | `.venv/bin/python -m pytest tests/assets/stocks/test_corporate_actions.py -q` | split, dividend and earnings timestamps reconcile | `gates/SD2_CORPORATE_ACTION_PASS.json` and `corporate_action_manifest.json` | A4 | block accounting and scoring; repair event mapping |
| `SD3_ACCOUNTING_IDENTITY_PASS` | `.venv/bin/python -m pytest tests/assets/stocks/test_accounting.py -q` | every hand-computed long/short identity closes within frozen tolerance | `gates/SD3_ACCOUNTING_IDENTITY_PASS.json` | A5 | no dry run; isolate first mismatching ledger row |
| `SD4_BORROW_DIVIDEND_PASS` | `.venv/bin/python -m pytest tests/assets/stocks/test_borrow_dividend.py -q` | unavailable locate rejects; borrow and dividend cashflows match goldens | `gates/SD4_BORROW_DIVIDEND_PASS.json` | A5 | reject all affected shorts; no free-borrow fallback |
| `SD5_EXECUTION_COST_PASS` | `.venv/bin/python -m pytest tests/assets/stocks/test_execution.py -q` | side, spread, slippage, impact, halt and terminal-fill tests PASS | `gates/SD5_EXECUTION_COST_PASS.json` | A5 | block cost-feasibility and all scored cells |
| `SD6_CRYPTO_COMPATIBILITY_PASS` | `.venv/bin/python -m pytest tests/test_protocol_contracts.py tests/test_protocol_metrics.py tests/test_protocol_registry.py tests/test_protocol_reproduce.py -q` | historical crypto fixtures parse and reproduce without byte mutation | `gates/SD6_CRYPTO_COMPATIBILITY_PASS.json` | A2 | revert shared-interface delta; stocks cannot proceed |
| `STOCKS_FREEZE_PASS` | `.venv/bin/python -m pytest tests/assets/stocks/test_selection_freeze.py -q` | exactly two families, six unique arm keys, immutable hashes, budget `0/6` | `gates/STOCKS_FREEZE_PASS.json` and `selection_freeze.json` | A1/A7 | invalidate selection; do not spawn A6/A8 |
| `STOCKS_DRYRUN_PASS` | `.venv/bin/python -m pytest tests/assets/stocks/test_six_arm_dryrun.py -q` | six first publications, six idempotent replays, no scored-window access | `gates/STOCKS_DRYRUN_PASS.json` plus temporary-ledger digest | A1/A7 | delete only temporary outputs; repair before W1 |
| `STOCKS_STRESS_PASS` | `.venv/bin/python -m pytest tests/assets/stocks/test_stage_a_stresses.py -q` | every mandatory stress exists and reconciles to its scored cell | `gates/STOCKS_STRESS_PASS.json` | A1/A7 | family is non-promotable; no replacement arm |
| `STOCKS_REPRO_PASS` | `.venv/bin/python -m pytest tests/assets/stocks/test_reproduction.py -q` | clean-process reproduction is exact for all 6/6 computed cells and canonical artifacts | `gates/STOCKS_REPRO_PASS.json` plus comparison manifest | reproduce worker/A7 | terminal result is `INCOMPLETE_NOT_PROMOTABLE` or `REJECT_ALL` |
| `STOCKS_A7_TERMINAL_PASS` | `.venv/bin/python -m pytest tests/assets/stocks/test_terminal_contract.py -q` | pins, counters, ledger, Stage-A decisions and unresolved findings reconcile | `gates/STOCKS_A7_TERMINAL_PASS.json` and `terminal_report.json` | A7 | no delivery label stronger than `BLOCKED` |

Before every row, A1 records the exact SHA and tree state:

```bash
git rev-parse HEAD
git status --short --branch
git diff --check
```

The SHA in the evidence must equal the tested `HEAD`. `git status --porcelain=v1`
must be empty before a result is accepted, except for explicitly declared,
ignored provider data outside Git. After the command, A1 runs it again; any new
tracked or untracked authority artifact not listed in the gate record is a
failure.

## 16. Final delivery gate

After terminal artifacts are committed, A1 freezes `STOCKS_DELIVERY_SHA`. Run
this only from a fresh detached worktree pinned to that SHA, with no scoring
worker or other pytest process active. The source/config/input pin recorded by
the delivery commit must still equal `STOCKS_W1`; terminal evidence must not
silently change scored code or inputs. Commands are serial:

```bash
git rev-parse HEAD
git status --porcelain=v1
.venv/bin/python -m pytest tests/assets/common tests/assets/stocks -q
.venv/bin/python -m pytest tests/test_protocol_contracts.py tests/test_protocol_metrics.py tests/test_protocol_registry.py tests/test_protocol_reproduce.py -q
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall research/assets/common research/assets/stocks
git diff --check
git status --porcelain=v1
```

The first and last status commands must print nothing. The full suite runs once
and alone. A failure in a targeted test or the full suite cannot be waived by a
later passing subset.

A1 then completes `research/control/stocks_run/final_delivery_checklist.json`:

| Check | PASS condition | If FAIL or NOT RUN |
|---|---|---|
| SHA and worktree | detached HEAD equals `STOCKS_DELIVERY_SHA`; scored source/config/input pin equals `STOCKS_W1`; tree clean before/after | stop delivery and rebuild evidence from the correct SHA |
| Test evidence | all commands above exit 0; exact counts and logs recorded | `INCOMPLETE_NOT_PROMOTABLE` |
| Gate completeness | every required gate in Section 15 is `PASS` at an allowed SHA | block terminal PASS |
| Data authority | entitlement, PIT universe, calendar and action manifests exist and hashes match resolved inputs | `BLOCKED_DATA_AUTHORITY` |
| Accounting | price PnL, cashflows, costs, borrow, dividends and terminal equity reconcile | reject affected family; no inferred values |
| Trial accounting | observed count includes every computation; published count and collisions reconcile; exactly `6/6` planned cells accounted for | block finalization until ledger repair/reconciliation |
| S1 isolation | no process, log or manifest proves S1 access; S1 hashes remain sealed | invalidate sprint; no Stage-A survivor label |
| Reproduction | fresh-process rerun matches every canonical digest and metric | `INCOMPLETE_NOT_PROMOTABLE` |
| Repository hygiene | no secrets, credentials, provider payloads or oversized raw data are added to Git; changed-file allowlists reconcile | remove/quarantine unauthorized files and rerun all affected gates |
| Worker shutdown | worker registry reports zero owned workers and no owned PID is alive | stop workers, reconcile partial outputs, rerun terminal audit |
| Independent audit | A7 records zero unresolved HIGH/CRITICAL and signs the exact delivery SHA | no delivery authorization |
| Product boundary | no live, paper, testnet or order authority; survivor label is Stage-A only | correct report and artifacts before delivery |

Secret scanning uses the repository's configured scanner when one exists. If no
scanner is installed/configured, record `NOT_RUN` and perform a changed-file
allowlist review; do not claim an automated secret-scan PASS. Large licensed
provider payloads remain outside Git and only their manifest/checksums may be
tracked.

Final verdict rules:

- `PASS`: every required row is PASS, reproduction is exact, A7 signs the frozen
  SHA and the tree remains clean.
- `FAIL`: a completed check disproves correctness, integrity or a Stage-A gate.
- `NOT_RUN`: evidence was not produced; any required NOT_RUN blocks PASS.
- `BLOCKED`: an external dependency such as entitlement or authoritative data
  prevents execution; it is not converted to FAIL or PASS.

The delivery packet contains the frozen SHA, all gate records and logs, manifest
digests, both denominator counts, six cell verdicts, reproduction comparison,
A7 terminal report, known limitations and the exact strongest allowed label.
Pushing, merging `main`, purchasing data or starting paper/live execution still
requires separate owner authorization.

## 17. Checkpoints and Definition of Done

A1 reports:

1. intake, provider authority and shared-core SHA;
2. M0 compatibility verdict;
3. S1 three-lane commits and correctness gates;
4. six proposals and A7 selection audit;
5. two-family freeze and budget `0/6`;
6. implementation/full-suite/W1 pins;
7. A7 prelaunch verdict;
8. every scored cell and counters;
9. reproduction and terminal outcome.

Done means either:

- two families completed 6/6 with exact reproduction and terminal audit; or
- the sprint closed truthfully as `BLOCKED`, `REJECT_ALL` or
  `INCOMPLETE_NOT_PROMOTABLE`, with workers zero and evidence reconciled.

No completion claim is allowed if provider entitlement, calendar, corporate
actions, borrow, costs, S1 isolation or reproduction is inferred rather than
proven.

## 18. First A1 report

```text
measured UTC
root branch/SHA and dirty files
MULTIASSET_CORE_SHA or M0 plan
stock integration path/branch/bootstrap SHA
provider/data entitlement status
calendar and corporate-action authority
stock published/observed denominators
budget 0/6
agent slots: 8 logical, max A1 + 3 active
heavy-worker cap
GO/NO_GO for M0 and S1 light lanes
```
