# PLAN_STOCKS_FREE_V1 — ZERO-COST US ETF RESEARCH FACTORY

> **Owner authority for a new, separate research cycle. Read this file in full
> before creating agents, worktrees, commits, datasets or scored artifacts.**
>
> This plan does not reopen, rewrite or rescue the closed
> `STOCKS_BLOCKED_DATA_AUTHORITY` sprint. It preserves the two frozen paid-data
> families unchanged and starts a new zero-monetary-cost ETF-only cycle.

## 0. Entry state and source of truth

Measured entry authority on branch `stocks`:

```text
STOCKS_PAID_DATA_TERMINAL_SHA = 84aa904578325f82955ddf195f1bc9eab86e3df7
terminal verdict              = STOCKS_BLOCKED_DATA_AUTHORITY
old scored budget             = 0/6
old published/observed        = 0/0
old S1                        = SEALED_UNTOUCHED
```

The previous families remain append-only historical evidence:

- `EQ_S2_A3_F1_PIT_RECON_FLOW`;
- `A5-S2-F1-LENDING-CONSTRAINT-PREMIUM`.

They are not candidates in this cycle. Do not modify their proposals, hashes,
selection, gates, counters or terminal artifacts. No result from this cycle may
be described as evidence for or against them.

Before launch, the owner commits this plan alone (plus a minimal authority-file
pointer if required) on `stocks` and freezes the full 40-character commit as
`STOCKS_FREE_OWNER_SHA`. A1 re-measures all branches, worktrees, dirty files,
active processes and provider state. Any difference from this snapshot is
recorded as a delta; history is never silently rewritten.

## 1. Mission and strongest allowed claim

Build and evaluate a small, reproducible US-listed ETF research cycle using
only data that is legally accessible at zero monetary cost at acquisition time.

The cycle has two owner-seeded mechanism directions:

1. cross-sectional ETF relative momentum / sector rotation;
2. time-series ETF trend with volatility-aware defensive allocation.

Both directions are **long-only or cash**. They may not short, borrow, use
options, use leverage, or depend on single-stock membership, securities
lending, fundamentals, earnings, analyst estimates or paid index archives.

The strongest possible scientific outcome is:

```text
STOCKS_FREE_V1_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
```

A survivor is not live-ready, not paper-ready and not proven profitable. S0 is
screening. S1 remains sealed for a later owner-authorized cycle.

## 2. Hard boundaries

- Zero monetary cost means no purchase, subscription charge, paid trial,
  automatic billing, cloud bill or commercial entitlement.
- Agents may inspect public official documentation and public downloads that
  do not require credentials. Account creation, accepting new license terms or
  entering payment details requires separate owner authorization even when the
  listed price is zero.
- Provider marketing is not data authority. License, timestamps, field
  semantics, coverage and reproducible download evidence must be recorded.
- Raw/provider payloads live outside Git. Git stores only manifests, checksums,
  small legal test fixtures and derived aggregate evidence permitted by terms.
- No convenience API receives automatic PASS. Missing evidence is
  `UNAVAILABLE_FAIL_CLOSED` or `NOT_RUN`.
- No scored return, PnL, PF, Sharpe or ranking before data, cohort, family,
  arms, windows, costs and execution rules are frozen and A7 authorizes launch.
- No grids, Bayesian optimization, genetic search, post-score threshold edits,
  family replacement or reduced-universe rescue.
- No inspection or scoring of S1.
- No paper, testnet, live, credentials, orders or leverage.
- No push or merge into `main` without a separate owner checkpoint.
- Historical Stocks, Forex and Crypto artifacts/worktrees are append-only and
  out of scope.

## 3. Research object and inference boundary

### 3.1 Instrument cohort

The cycle studies a **frozen cohort of long-lived, liquid US-listed ETFs**, not
the historical US stock market and not a survivorship-free single-stock
universe. Claims must be limited to the actual frozen ETF cohort.

Candidate roles may include:

- a broad US equity benchmark;
- liquid US sector ETFs;
- defensive diversifiers such as Treasury or gold ETFs only when inception,
  liquidity, price, distributions and calendar coverage pass the same gates.

No ticker is admitted because its historical return looked attractive. A2/A3
freeze an eligibility rule before returns are computed. At minimum:

- exchange-listed ETF with stable identifier evidence;
- inception before the S0 start plus required warmup;
- complete daily raw and total-return inputs over the common window;
- adequate dollar volume under a predeclared floor;
- no unresolved ticker, liquidation, split or distribution event;
- executable next-session price semantics.

Current-survivor selection is disclosed as a cohort limitation. The cycle may
not generalize results to delisted ETFs or all US equities.

### 3.2 Clock

- Daily completed bars are the fastest allowed signal input.
- Decisions are weekly or monthly, frozen before scoring.
- A signal uses only data completed before the decision timestamp.
- Orders fill at the next allowed event using raw executable-price semantics,
  never on the signal close.
- Features using adjusted/total-return series must be separated from raw fill
  prices and reconciled through distribution/split factors.

### 3.3 Portfolio

- Long-only selected ETFs plus explicit cash.
- Gross exposure `<= 1.0`; leverage forbidden.
- Weighting method frozen before scoring: equal weight or deterministic inverse
  volatility, with a declared cap per ETF.
- Cash return is zero unless a free, authoritative cash-rate series passes PIT
  and license gates; no inferred interest.
- SPY total return is the primary benchmark when its inputs pass.

## 4. Data authority before strategy authority

No proposal lane starts until A2/A3 produce `FREE_DATA_AUTHORITY_PASS`.

### 4.1 Required free-data evidence

The accepted source or source stack must prove:

1. provider/source identity and direct official URLs;
2. zero monetary cost and no automatic billing;
3. terms allowing personal research, local storage and derived research;
4. deterministic download/export with versioned schema;
5. timezone-aware daily timestamps and session convention;
6. raw OHLCV with unit semantics;
7. distributions, splits and adjustment-factor provenance, or independently
   reconstructable total return;
8. ETF inception/liquidation/ticker-event evidence;
9. at least eight years of common daily history plus warmup;
10. SPY price, distributions and total-return reconciliation;
11. missing-data and correction policy, or explicit absence recorded;
12. immutable local snapshot with SHA-256 manifest;
13. two-pull determinism or a documented revision delta;
14. comparison against an independent source on sampled dates/events;
15. loader-resolved coverage, not merely file presence.

An official issuer distribution page may complement, but not silently override,
a price provider. Conflicts are recorded and block affected instruments.

### 4.2 S0/S1 partition

After accepted coverage is known, A1 freezes exact UTC dates:

- S0: historical screening window, at least six complete years where possible;
- S1: the most recent non-overlapping twelve complete months, sealed;
- warmup: precedes S0 and may not contribute scored trades;
- three chronological S0 folds with force-flat boundaries and declared purge.

The staging layer may hash the complete delivery, but research processes get an
allowlist that makes S1 unreadable. A data operator may verify coverage/counts
without exposing S1 returns to proposal, implementation or scoring agents.

If a valid sealed twelve-month S1 cannot be formed, the cycle closes
`STOCKS_FREE_V1_BLOCKED_S1_ISOLATION` before proposals.

## 5. Reused architecture and new namespaces

Reuse only after compatibility tests:

```text
research/assets/common/**
research/assets/stocks/**
contracts/**
research/protocol/**
```

New cycle-specific paths:

```text
research/stocks_free_v1/
research/control/stocks_free_v1_run/
research/audits/stocks_free_v1/
research/proposals/stocks_free_v1/
results/registry/stocks_free_v1/
tests/stocks_free_v1/
```

Trial identity must include at least:

```text
asset_class=US_ETF_CASH
cycle=STOCKS_FREE_V1
family_id
arm_id
cohort_digest
data_manifest_digest
window_digest
cost_digest
```

Old and new denominators are separate. A read-only global index may reference
both, but DSR/PBO samples may not combine scientifically incomparable trials.

## 6. Agents, ownership and concurrency

Use eight logical roles, with at most A1 plus three light agents active on one
host. Full suites run alone. Heavy scoring concurrency is set only after a
measured pilot.

| Role | Responsibility | Writes |
|---|---|---|
| A1 | controller, integration, manifests, freezes, publication | central control only |
| A2 | free-source/license/schema/data intake | data adapter + data audit |
| A3 | cohort, calendar, distributions, S0/S1 isolation | cohort/calendar evidence |
| A4 | blind literature/spec lane for relative momentum | proposal files only |
| A5 | blind literature/spec lane for trend/defensive | proposal files only |
| A6 | implement frozen family 1 | family-1 code/tests only |
| A8 | implement frozen family 2 | family-2 code/tests only |
| A7 | independent data, prelaunch and terminal audit | audit files only |

A7 never repairs code. Only A1 merges, freezes, edits central manifests or
publishes scored ledgers. Lane agents do not spawn children unless A1 records
the exact delegation in `worktree_manifest.json`.

Waves:

```text
Z0  A1                           measured intake and bootstrap
Z1  A1 + A2 + A3                free-data and cohort authority
Z2  A1 + A7                     independent data audit
Z3  A1 + A4 + A5                two outcome-blind proposal lanes
Z4  A1 + A7                     novelty/feasibility audit + selection freeze
Z5  A1 + A6 + A8                two family implementations
Z6  A1 alone                    integration, dry run, full suite, W1 freeze
Z7  A1 + A7                     independent prelaunch audit
Z8  A1 + measured heavy workers scored execution
Z9  A1 + independent reproduction + A7 terminal audit
```

## 7. Exact worktree topology

```text
.worktrees/stocks-free-v1/integration      orca/stocks-free-v1-integration
.worktrees/stocks-free-v1/z1-data          orca/stocks-free-v1-z1-data
.worktrees/stocks-free-v1/z1-cohort        orca/stocks-free-v1-z1-cohort
.worktrees/stocks-free-v1/z2-a7-data       orca/stocks-free-v1-z2-a7-data
.worktrees/stocks-free-v1/z3-momentum      orca/stocks-free-v1-z3-momentum
.worktrees/stocks-free-v1/z3-trend         orca/stocks-free-v1-z3-trend
.worktrees/stocks-free-v1/z4-a7-selection  orca/stocks-free-v1-z4-a7-selection
.worktrees/stocks-free-v1/z5-family-1      orca/stocks-free-v1-z5-family-1
.worktrees/stocks-free-v1/z5-family-2      orca/stocks-free-v1-z5-family-2
.worktrees/stocks-free-v1/z7-a7-prelaunch  orca/stocks-free-v1-z7-a7-prelaunch
.worktrees/stocks-free-v1/z8-exec-1        detached at STOCKS_FREE_W1
.worktrees/stocks-free-v1/z8-exec-2        detached at STOCKS_FREE_W1
.worktrees/stocks-free-v1/z9-reproduce     detached at STOCKS_FREE_W1
```

Bootstrap only after `STOCKS_FREE_OWNER_SHA` is committed:

```bash
git -C /Users/hoangminhlong/my-quantitative/.worktrees/stocks/integration \
  worktree add \
  -b orca/stocks-free-v1-integration \
  /Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v1/integration \
  STOCKS_FREE_OWNER_SHA
```

`STOCKS_FREE_OWNER_SHA` is a placeholder. Replace it with the measured full
40-character SHA; never pass the literal placeholder to Git.

For every lane A1:

1. commits the controlling manifest on integration;
2. freezes a full wave SHA;
3. creates the named branch/worktree from that SHA;
4. verifies `pwd`, HEAD, branch and empty porcelain;
5. records allowed/forbidden globs, tests, deliverables and merge order;
6. dispatches only after the manifest commit;
7. cherry-picks one lane commit at a time and tests after each pick.

No worktree deletion, reset, force-create or branch reuse without owner
authorization.

## 8. Z0 — intake and control plane

A1 creates under `research/control/stocks_free_v1_run/`:

```text
run_contract.json
state.json
heartbeat.json
event_log.jsonl
worktree_manifest.json
historical_boundary.json
```

Required intake facts:

- root, old Stocks terminal and new integration full SHAs;
- clean/dirty state of every owned worktree;
- active agents/processes and machine-wide resource cap;
- old family/counter hashes proving no mutation;
- zero-cost/no-account/no-purchase authority boundary;
- new published/observed counters `0/0` and budget `0/6`;
- S1 not yet formed and therefore no scored permission;
- absolute operational deadline for the current non-scored wave.

Z0 may close `BLOCKED` without failure if no credible free-data source can be
evaluated.

## 9. Z1/Z2 — free data, cohort and independent audit

### A2 deliverables

- official-source evidence and license matrix;
- zero-cost attestation with captured terms/date;
- deterministic downloader/export adapter with rate limiting;
- raw-outside-Git storage contract;
- schema and timestamp contract;
- checksum manifest and two-pull revision comparison;
- raw/adjusted/distribution reconciliation;
- missing/duplicate/gap audit;
- small synthetic and legally permitted golden fixtures.

### A3 deliverables

- pre-return cohort eligibility rule;
- accepted/rejected ETF census with reasons;
- inception/ticker/liquidation event audit;
- exchange calendar reconciliation;
- distribution/split audit;
- SPY total-return benchmark reconciliation;
- exact S0/warmup/S1 partitions and access allowlists;
- disclosure limiting inference to the frozen cohort.

### Required Z1 gates

```text
FD0_ZERO_COST_LICENSE_PASS
FD1_SCHEMA_TIMESTAMP_PASS
FD2_RAW_ADJUSTED_CA_PASS
FD3_COHORT_INCEPTION_PASS
FD4_COVERAGE_GAP_PASS
FD5_CALENDAR_EXECUTION_PASS
FD6_SPY_TOTAL_RETURN_PASS
FD7_S1_ISOLATION_PASS
FD8_CRYPTO_STOCK_COMPATIBILITY_PASS
FREE_DATA_AUTHORITY_PASS
```

A7 recomputes the claims in a detached audit worktree. Launch of proposal lanes
requires `STOCKS_FREE_DATA_AUTHORIZED`, zero HIGH/CRITICAL objections and every
required FD gate PASS. Documentation-only or synthetic-only evidence cannot
earn this authorization.

If the free stack cannot pass, close:

```text
STOCKS_FREE_V1_BLOCKED_FREE_DATA_AUTHORITY
```

Do not weaken gates, substitute paid data or continue to proposals.

## 10. Z3/Z4 — outcome-blind family specifications

A4 sees the frozen data/cohort contract and literature for relative momentum.
A5 sees the same contract and literature for trend/defensive allocation. They
must not see each other's work or compute candidate returns.

Each lane returns exactly one family with three preregistered arms:

1. literature-backed anchor;
2. one theoretically justified neighbour;
3. one causal negative control.

Each spec freezes:

- feature definitions and lookbacks;
- weekly/monthly decision clock;
- eligible ETF cohort;
- long/cash portfolio construction and caps;
- warmup, folds, purge and terminal close;
- benchmark and exposure diagnostics;
- transaction-cost and delay assumptions;
- minimum evidence count;
- falsification rule;
- exact data/window/code digests;
- no-tuning declaration.

A7 audits novelty, hidden lookahead, overlap, data feasibility, turnover,
concentration, benchmark fairness and whether the control can falsify the
mechanism. Both families must be eligible before implementation. A blocked
family's three slots stay unused and may not be reassigned in this cycle.

A1 freezes `selection_freeze.json`, six unique arm keys and budget `0/6`.

## 11. Z5/Z6 — implementation, dry run and W1

A6 and A8 implement only their frozen family through the shared asset adapter.
They may not modify common contracts, the other family, control manifests or
historical artifacts.

Required implementation tests:

- hand-computed feature vectors;
- one-event lag and no-lookahead;
- raw-fill versus total-return-signal separation;
- cash-state and no-short/no-leverage invariants;
- deterministic target books;
- expected-sign and negative-control destruction fixtures;
- calendar, distribution and terminal-close goldens;
- identity/config digest stability;
- double-generation equality.

A1 integrates one commit at a time. Then it runs:

- targeted family suites;
- all `tests/stocks_free_v1/`;
- shared Stocks/common compatibility tests;
- six-arm temporary-ledger dry run: six first publications, six idempotent
  replays, zero permanent denominator delta;
- schedule-only turnover/cost feasibility;
- full suite alone;
- `compileall` and `git diff --check`;
- tracked-tree mutation check before/after.

If all pass, A1 freezes `STOCKS_FREE_W1` with code, data, cohort, window, costs,
calendar, family, arm and environment hashes. Execution and reproduction
worktrees are detached at exactly W1 with read-only staged data.

## 12. Z7 — independent prelaunch

A7 independently verifies:

- every pin resolves to W1;
- data authority and license evidence;
- S0/S1 filesystem isolation;
- PIT ordering and next-event fills;
- raw/adjusted/distribution reconciliation;
- six trial identities and dry-run idempotence;
- costs, turnover and benchmark assumptions;
- family/control immutability;
- test evidence and clean trees;
- budget `0/6`, denominators `0/0` and zero scored artifacts;
- measured heavy-worker cap and sufficient time.

Scored launch requires exact verdict:

```text
STOCKS_FREE_V1_S0_LAUNCH_AUTHORIZED
```

Anything else is NO_GO.

## 13. Z8 — six scored cells

Family order is frozen. Each family runs serially:

```text
anchor -> neighbour -> causal negative control
```

Two families may run concurrently only if the fresh measured heavy cap is at
least two and their output/ledger shards are isolated. Otherwise run one cell
at a time. No tests run while a scored worker is active.

Per-cell path:

```text
verify pins and S1 denial
-> generate schedule/target book
-> three chronological folds
-> next-event raw fills
-> commissions + spread/slippage + regulatory fees where applicable
-> base result
-> cost x1.5
-> +1 event delay
-> adverse spread/slippage stress
-> drop-one-ETF and drop-one-fold
-> benchmark/concentration diagnostics
-> canonical artifacts
-> observed counter +1
-> append-only publication exactly once
```

Every computed scored metric increments the observed denominator even if
publication fails. A technical abort consumes zero only with forensic evidence
showing no scored metric was computed.

## 14. Stage-A gates

Per family, all applicable gates must pass:

- after-cost expectancy `> 0`;
- position-level PF `>= 1.10`;
- at least `2/3` chronological folds positive;
- no populated fold PF `< 0.80`;
- MDD `<= 15%`;
- no fold contributes more than `50%` of positive PnL;
- no ETF contributes more than `35%` of positive PnL/risk;
- adequate independent weekly/monthly decisions;
- drop-one-ETF and drop-one-fold survival;
- stressed PnL `> 0` and stressed PF `>= 1.00`;
- neighbour supports the anchor;
- causal negative control does not reproduce the claimed mechanism;
- turnover/capacity remain feasible;
- SPY total-return comparison is reported without replacing the flat hard
  benchmark;
- exact independent reproduction;
- zero unresolved HIGH/CRITICAL;
- DSR/PBO use the complete cycle denominator or remain
  `UNAVAILABLE_FAIL_CLOSED` with zero credit.

No scorecard points can rescue a failed hard gate.

## 15. Z9 — reproduction and terminal audit

Reproduce every computed cell in fresh processes at W1. Require exact/all-match
for schedules, targets, trades, positions, costs, folds, stresses, metrics,
hashes, counters and verdict inputs.

A7 performs the terminal audit. Allowed family outcomes:

```text
STOCKS_FREE_V1_FAMILY_REJECT
STOCKS_FREE_V1_STAGE_A_SURVIVOR_LOCKED_FOR_FUTURE_S1
STOCKS_FREE_V1_FAMILY_BLOCKED
STOCKS_FREE_V1_FAMILY_INCOMPLETE_NOT_PROMOTABLE
```

Allowed sprint outcomes:

```text
STOCKS_FREE_V1_REJECT_ALL
STOCKS_FREE_V1_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
STOCKS_FREE_V1_BLOCKED_FREE_DATA_AUTHORITY
STOCKS_FREE_V1_BLOCKED_PRELAUNCH
STOCKS_FREE_V1_INCOMPLETE_NOT_PROMOTABLE
```

No terminal PASS exists without reproduction, A7, clean trees and reconciled
counters. No outcome authorizes S1, paper or live trading.

## 16. Gate evidence and commands

Every gate record contains:

```text
gate_id
measured_at_utc
owner
integration_sha
command
exit_code
status = PASS | FAIL | NOT_RUN | BLOCKED
expected
observed
input/output digests
pre/post tree status
blockers and corrective action
evidence paths
```

Minimum command families, resolved after files exist:

```bash
.venv/bin/python -m pytest tests/stocks_free_v1 -q
.venv/bin/python -m pytest tests/assets/common tests/assets/stocks -q
.venv/bin/python -m pytest tests/test_protocol_contracts.py tests/test_protocol_metrics.py -q
.venv/bin/python -m compileall research/stocks_free_v1 research/assets/common research/assets/stocks
git diff --check
git status --porcelain=v1
```

Absent planned tests are `NOT_RUN`, never silently skipped. A1 records exact
commands/counts from the integration worktree. Lane-local claims are not
integration evidence.

## 17. Mandatory checkpoints

A1 reports:

1. Z0: SHAs, branches, dirty state, agents, resources and authority boundary;
2. Z1: source/license/schema and cohort audit with FD0–FD8;
3. Z2: A7 data verdict and exact S0/S1 partition without S1 returns;
4. Z3: two blind proposal commits;
5. Z4: A7 selection verdict, six arm IDs and budget `0/6`;
6. Z5/Z6: implementation commits, tests, dry run and W1;
7. Z7: A7 prelaunch verdict and measured heavy cap;
8. Z8: every computed cell, observed/published counters and worker status;
9. Z9: reproduction, terminal verdict, clean trees and workers zero.

Stop for owner input only at purchase/account/license acceptance, credentials,
external-state ambiguity, data terms requiring judgment, push/main merge,
deletion/reset, S1/live, or scientific-threshold changes. Safe local work within
the frozen plan continues automatically.

## 18. First A1 report

Before creating lanes, a fresh A1 reports:

```text
measured UTC
root/main SHA and dirty files
old Stocks terminal SHA and immutable-hash check
STOCKS_FREE_OWNER_SHA
integration path/branch/bootstrap SHA
zero-cost authority boundary
candidate free-source state
new denominators 0/0 and budget 0/6
S1 status = NOT_YET_PARTITIONED_NO_SCORE_PERMISSION
active agents/workers and machine-wide cap
Z1 lane paths, branches and allowlists
GO/NO_GO for Z1 read-only/light work
```

The first response does not claim data PASS. After reporting, A1 continues
through Z1 safe read-only/light work. It stops rather than substitutes paid,
unlicensed, undocumented or scientifically inadequate data.
