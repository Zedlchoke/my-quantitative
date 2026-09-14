# PROSPECTIVE-SHADOW-V1 — FORWARD PAPER OBSERVATION OF THREE CRYPTO NEAR-MISSES

> Owner-requested draft, 2026-09-14.
>
> **Current status: `DRAFT_NOT_REGISTERED / NOT_AUTHORIZED / NOT_RUNNING`.**
> This file defines a future cycle; it does not register the cycle, start a
> worker, open S1, create a broker account, or authorize paper/testnet/live
> orders. Registration and execution are separate gated actions below.

## 0. One-sentence mission

Run the historically frozen anchor form of exactly three rejected crypto
families in a forward-only internal shadow ledger, so we can learn whether
their old near-miss behaviour continues without risking money or changing the
old rules after seeing new results.

```text
ILLIQ-AMIHUD-28D-W
BASISLV-PREMFADE-28D
XSECT-FUND-CARRY-7D
```

There are three active virtual sleeves, not three newly approved strategies.
All three retain their historical rejection labels throughout this cycle.

## 1. Measured starting point and blockers

Measured in the root owner checkout on 2026-09-14:

```text
cwd                 /Users/hoangminhlong/my-quantitative
branch              main
HEAD                41d1da6d130b8320ccf95a5ed64a2ce6d78ff456
owner change        .zcode/ is untracked and must be preserved
registered cycles   all currently TERMINAL
S1                  SEALED_UNTOUCHED everywhere
heavy-lock verdict  CONTROL_STATE_DRIFT
shadow worker       NOT RUN
broker/testnet      NOT REQUESTED / NOT AUTHORIZED
```

The heavy-lock/control-state drift and the cycle-doctor findings must be
resolved by the control-plane owner before registration or dispatch. This plan
must not be used to route around those findings.

## 2. Meaning of “shadow” in this plan

Shadow means:

1. Read newly available market data only after the activation timestamp.
2. Compute the position each family would want.
3. Simulate fills, fees, slippage, funding, equity and drawdown in an internal
   append-only virtual ledger.
4. Send **no order** to Binance, a broker, testnet or any external account.
5. Require no API key or broker account for phase V1.

The engine may emit `TARGET_INTENT` records. It must have no order-routing
credential, broker client, API write permission or callable deployment path.
Adding any of those changes the activity from internal shadow to external
paper/testnet and requires a separate owner-approved plan.

Forward-only means no historical backfill may be counted as prospective
performance. Historical data may be replayed only for deterministic tests and
identity recovery, under a namespace visibly marked `REPLAY_NOT_PROSPECTIVE`.

## 3. Historical truth that may not be rewritten

### 3.1 `ILLIQ-AMIHUD-28D-W`

- Historical family: `A8-V11-ILLIQ-AMIHUD`.
- Frozen mechanism: trailing 28-day daily Amihud measure
  `abs(daily return) / daily dollar volume`; weekly Monday decision; long the
  most illiquid quintile and short the most liquid quintile; equal-weight,
  dollar-neutral and BTC-beta-neutral; intended holding period seven days.
- Signal inputs: completed 15-minute close and quote-volume bars. Funding is an
  accounting cost/credit only, never a signal input.
- Historical result: positive expectancy, PF `1.354841`, MDD `9.182%`, and
  `3/3` positive folds; stress cells remained positive.
- Historical failure: symbol concentration `0.705497`; only `12/13` gates
  passed. The family remains `V11_FAMILY_REJECT`.
- The V12 earlier-window replication was `BLOCKED_DATA`; it must not be
  silently described as run or failed on performance.
- Historical identity authority to recover byte-exactly before implementation:
  terminal commit `c97283e0d1681c24ee9a637a4fb1628d0334b7e1`, especially
  `research/control/v11_run/selection_freeze_specs/A8-V11-ILLIQ-AMIHUD.json`
  and the corresponding family implementation/tests.

Only the 28-day anchor is an active sleeve. The 56-day neighbour and inverted
28-day book are mandatory counterfactual diagnostics, not extra active
families and never promotable.

### 3.2 `BASISLV-PREMFADE-28D`

- Historical family: `A14-V14-A5-BASISLV-PREMFADE`.
- Frozen mechanism: mean perpetual-futures versus index premium over 28 days;
  weekly Monday `00:00Z` decision; long the low/discount-premium tercile and
  short the high/premium tercile; equal weight, gross `1.0`, minimum 12
  eligible names, intended holding seven days.
- PIT rule: only fully completed 15-minute basis buckets available by the
  decision timestamp; the historical fill rule uses the first completed
  15-minute bar strictly after the decision.
- Funding is booked once as a cost/credit while held, but is never a signal.
  Price-only expectancy must remain positive; otherwise the supposed premium
  fade is merely carry harvesting.
- Historical result: net `+0.700216`, position PF `1.360047`, MDD `11.585%`,
  `3/3` folds positive, stress variants positive, neighbour supportive and
  inverted control negative.
- Historical failure: largest positive-fold share `0.511024 > 0.50`; program
  DSR `0.002240` over 146 observed trials. It remains `V14_FAMILY_REJECT`.
- Historical identity authority to recover byte-exactly before implementation:
  terminal commit `183554add4db82444d3e71beb24fb247c6b420b2`, especially
  `research/control/v14_run/selection_freeze_v14.json`,
  `research/v14/families/basislv_premfade/`, and its terminal report.

Only the 28-day anchor is an active sleeve. The 56-day neighbour and exact
sign-inverted 28-day book remain mandatory counterfactual diagnostics.

### 3.3 `XSECT-FUND-CARRY-7D`

- Historical family: `H-XSECT-FUNDING-CARRY-v1` / V6 funding carry.
- Frozen mechanism: trailing mean of already published and settled funding
  over seven days; daily `00:00Z` decision; long the bottom-two funding names
  and short the top-two; 24-hour rebalance; target gross `0.80`, hard gross
  cap `1.00`, hard absolute-net cap `0.10`, maximum absolute symbol weight
  `0.20`.
- Frozen traded universe: ETH, SOL, BNB, XRP, DOGE, LINK and ADA perpetuals;
  BTC is benchmark context only.
- Historical near-one-year result on a 100,000-USDT baseline: net
  `+20,580.87 USDT`, approximately `+20.58%` total or `+20.63%` annualized;
  PF `1.1570`; MDD `8.835%`; funding `+2,277.23`; fold PnLs approximately
  `+10,866 / +10,169 / -454`.
- Historical failure: largest positive-fold share `51.66% > 50%`; robustness
  gate remained inconclusive and DSR was unavailable. It remains
  `CANDIDATE_FAIL`, with no locked candidate.
- Historical identity authority: current
  `research/hypotheses/H-XSECT-FUNDING-CARRY-v1/candidate.yaml`, corrected V6
  closure addendum, and the V6 audit. Missing old result roots must be recovered
  from a verified archive or treated as unavailable; their contents must not
  be reconstructed from prose.

Only the 7-day directional anchor is an active sleeve. The historically
declared reverse control remains a mandatory diagnostic and never a family.

## 4. Fixed scope and forbidden changes

The cycle contains exactly the three anchors above. It must not:

- add a fourth family because one sleeve performs badly;
- retune 28/56/7-day windows, ranks, long/short direction, universe, clock,
  holding period or concentration thresholds after activation;
- use the latest winners only, drop losing symbols, or lower costs;
- backfill missing prospective signals and call them live observations;
- relabel any historical `REJECT`, `CANDIDATE_FAIL` or `BLOCKED_DATA` result;
- count a diagnostic control as a candidate;
- open or inspect S1;
- place orders, use leverage, create an account, accept terms, purchase data,
  or request credentials;
- claim that shadow profit proves a deployable edge.

Any material strategy change requires a new identity and a new plan. It may
not inherit the prospective history of the old identity as if nothing changed.

## 5. Capital and comparison contract

Each anchor receives an isolated virtual subaccount initialized at exactly
`100,000 USDT` at activation:

```text
sleeve_illiq_amihud        100,000 USDT
sleeve_basislv_premfade    100,000 USDT
sleeve_xsect_fund_carry    100,000 USDT
```

No sleeve may consume another sleeve's cash or risk allowance. A read-only
combined dashboard may show an equal-capital one-third blend, but that combined
view must never feed positions back into the sleeves. Report both:

- each isolated sleeve;
- the equal-capital combined view;
- pairwise return correlation;
- same-symbol and same-direction overlap;
- gross, net and BTC-beta exposure after hypothetical combination.

This prevents two similar crypto books from appearing diversified merely
because they have different family names.

## 6. Two cost ledgers, frozen before activation

Every virtual fill is evaluated twice:

1. `LINEAGE_COST`: the exact cost/funding convention of that historical
   family, for continuity with its old result.
2. `CURRENT_CONSERVATIVE_COST`: a pre-activation frozen current fee schedule,
   per-symbol tick/slippage model, funding settlement convention and latency
   assumption measured from authorized bytes.

The current-cost ledger is the primary shadow reality check. The lineage
ledger is diagnostic. Cost assumptions cannot move during the run; a genuine
venue fee change creates a dated cost-regime boundary and a new frozen hash,
not an in-place rewrite.

## 7. Prospective clock and minimum observation period

`SHADOW_START_UTC` is written once only after the independent prelaunch audit
and the fresh owner GO. The first valid feature cutoff must be at or after that
timestamp. Warmup data may precede it, but PnL may not.

Checkpoints:

| Checkpoint | Allowed conclusion |
|---|---|
| 7 calendar days | operational health only |
| 13 weeks | early diagnostic; no pass/promotion claim |
| 26 weeks | interim evidence; still no promotion |
| 52 weeks | first complete shadow evaluation over three chronological forward folds |

Early stopping is allowed for data corruption, leakage, accounting mismatch,
identity drift, risk breach or broken controls. Early profit is never a reason
to stop and promote.

## 8. Per-event evidence contract

Every scheduled decision emits one append-only record even when no trade is
possible. Required fields:

```text
schema, cycle_id, family_id, arm_id, event_id
scheduled_decision_utc, observed_at_utc, feature_cutoff_utc
data_snapshot_digest, code_freeze_sha, config_digest, cost_regime_digest
eligible_symbols, rejected_symbols_with_reason
signal_values, target_weights, previous_weights
virtual_fill_events, fee, slippage, funding_cashflow
price_pnl, total_pnl, cash, equity, gross, net, btc_beta
data_status, accounting_status, risk_status, no_order_proof
```

`event_id` is deterministic from family identity plus scheduled timestamp.
Restarting a worker must reproduce or resume the same event, never duplicate
it. Atomic append and read-back verification are mandatory.

If required data is late or missing, emit `DATA_BLOCKED` and do not synthesize
a price, reuse an old rank, or silently skip the event. If valuation of an open
virtual position becomes impossible, performance reporting for that interval
is `UNAVAILABLE_FAIL_CLOSED` until reconciled.

## 9. Owner dashboard contract

The cycle must provide a read-only dashboard intended for a non-technical
owner. The append-only shadow ledgers remain the authority; the dashboard is a
view over those bytes and may never rewrite trades, equity or verdicts.

### 9.1 Top-level account view

The first screen shows, without requiring a click:

```text
Starting virtual capital                 300,000 USDT
Current combined virtual equity          amount and timestamp
Today PnL                                USDT and percent
Total PnL since SHADOW_START_UTC          USDT and percent
Realized / unrealized PnL                 separate values
Fees / slippage / funding                 separate values
Current gross / net / BTC-beta exposure   measured values
Maximum drawdown                          amount and percent
Open positions / trades today / all trades
Last successful update / data freshness / system status
```

“Today” is frozen as `00:00 Asia/Ho_Chi_Minh` through the latest valid mark.
The dashboard also exposes a UTC toggle and always prints the exact start/end
timestamps used for the calculation. If the midnight mark or any required
input is unavailable, today's PnL is `UNAVAILABLE_FAIL_CLOSED`, never silently
computed from a convenient later point.

### 9.2 Per-family cards and comparison table

Show one card and one comparison row for each active sleeve:

```text
ILLIQ-AMIHUD-28D-W       starting equity 100,000 USDT
BASISLV-PREMFADE-28D     starting equity 100,000 USDT
XSECT-FUND-CARRY-7D      starting equity 100,000 USDT
```

Each card/row shows:

- current equity;
- today PnL in USDT and percent;
- total PnL in USDT and percent;
- realized and unrealized PnL;
- fees, slippage and funding separately;
- number of virtual fills today and since activation;
- number of open positions, winners, losers and blocked decisions;
- gross, net and BTC-beta exposure;
- current drawdown and maximum drawdown;
- last signal time, last successful fill time and next scheduled decision;
- `RUNNING`, `STALE`, `DATA_BLOCKED`, `RISK_BLOCKED` or `STOPPED` status with
  a plain-language reason.

The UI must not rank the families by profit or add celebratory “winner” labels.
It reports evidence; it does not change allocation or research status.

### 9.3 Combined 300,000-USDT account chart

Provide an interactive equity chart whose starting point is exactly
`300,000 USDT`, representing the sum of the three isolated 100,000-USDT
sleeves. Required behaviour:

- combined equity line in USDT;
- optional normalized return-percent view from the 300,000-USDT baseline;
- toggles for the three individual sleeve equity lines;
- baseline/reference line at 300,000 USDT;
- hover tooltip with timestamp, combined equity, daily PnL, cumulative PnL,
  and each sleeve contribution;
- range selectors `1D`, `7D`, `30D`, `13W`, `26W`, `ALL`;
- drawdown subplot or toggle;
- markers for entries, exits, blocked events, cost-regime boundaries and
  incidents;
- no interpolation across missing/invalid valuation intervals; show a visible
  gap and the reason instead.

The combined chart is read-only and equal-capital. It must not net one
sleeve's position against another before the isolated ledgers reconcile.

### 9.4 Orders/trades table

Show a searchable, sortable and filterable table of every virtual fill. Filters
include family, asset, side, open/closed status, date range and event status.
The default columns are:

```text
virtual_trade_id, family, asset, side, status
signal_time, intended_fill_time, actual_virtual_fill_time
entry_price, current_mark_or_exit_price
quantity, notional, fee, slippage, funding
realized_pnl, unrealized_pnl, return_pct
stop_loss_price, take_profit_price, exit_policy
```

One strategy decision may produce several symbol-level fills. The dashboard
must distinguish `decision_count`, `order_intent_count`, `fill_count` and
`closed_position_count`; it may not label all four as “number of trades”.

### 9.5 Click-through trade detail

Clicking a row opens a detail drawer/page containing:

- family, arm, asset, long/short side and virtual status;
- strategy decision timestamp, feature cutoff and data availability timestamp;
- signal value, cross-sectional rank, eligible universe and target weight;
- previous weight, requested quantity/notional and virtual filled quantity;
- intended price, virtual average fill price, current mark and exit price;
- fee, slippage, every funding cashflow and total transaction cost;
- realized/unrealized PnL in USDT and percent;
- entry reason and exit reason in plain Vietnamese;
- linked `event_id`, config/data/cost digests and source-ledger location;
- accounting, data, risk and no-order-proof statuses;
- a small asset-price chart with entry, rebalance/exit and blocked-event markers.

### 9.6 Stop-loss and take-profit honesty

These three frozen cross-sectional families do **not** have native fixed-price
stop-loss or take-profit rules. The dashboard must therefore show:

```text
stop_loss_price    N/A — frozen family has no native fixed stop
take_profit_price  N/A — frozen family has no native fixed target
exit_policy        the actual frozen rule, such as scheduled rebalance,
                   rank removal, fold force-flat or risk-cap block
```

Never invent an SL/TP number for display. If a future plan adds SL/TP, it is a
new strategy identity and cannot rewrite this shadow history. The detail view
may show a diagnostic “distance to risk cap”, clearly labelled as diagnostic
and not as an order.

### 9.7 Dashboard data quality and refresh

- Read-only queries only; no order, strategy-edit or ledger-edit control.
- Every metric links to its latest source timestamp and ledger digest.
- Refresh is idempotent and leaves tracked files unchanged.
- Show stale-data age and the last completed scheduler heartbeat.
- A red banner appears for accounting mismatch, stale data, identity drift,
  risk block or failed reproduction; green is allowed only for measured PASS.
- Empty states say `NOT_RUN`, `NO_TRADES_YET` or `UNAVAILABLE`, never `0`
  when zero has not been established.
- Export the current filtered trades and equity series as sanitized CSV/JSON;
  exports contain no credentials and do not become authority over the ledger.
- Desktop and mobile layouts require browser render checks before G8; visual
  evidence is `NOT_RUN` until screenshots and interaction checks are recorded.

### 9.8 Dashboard acceptance tests

At minimum, tests must prove:

- three 100,000-USDT sleeves sum to a 300,000-USDT initial chart point;
- today's USDT and percent PnL reconcile to the frozen local-day boundary;
- combined equity equals the sum of isolated equities at every valid mark;
- family/order/fill/closed-position counters cannot be conflated;
- clicking a fill resolves the correct immutable event and all cost rows;
- missing marks create a visible gap and `UNAVAILABLE_FAIL_CLOSED`;
- every current family displays SL/TP as `N/A` and its true exit policy;
- restart/refresh creates no duplicate events or changed ledger bytes;
- the dashboard exposes no write endpoint capable of placing an order.

## 10. Gates before activation

### G0 — control plane

- cycle doctor has zero unresolved HIGH/CRITICAL findings affecting this
  cycle;
- heavy lock is `FREE_PROVEN` or held by this cycle for the bounded heavy
  operation;
- root owner changes are preserved;
- one live Lead/A1 session only.

### G1 — exact historical identity

- all three source commits resolve;
- frozen specifications and implementations are recovered with hashes;
- every score-affecting parameter is listed and compared;
- ambiguity is `BLOCKED`, never resolved by guessing;
- historical verdict labels are pinned into every shadow report.

### G2 — prospective data authority and PIT

- venue/license/coverage/schema identities are authorized;
- event/effective/available/retrieved timestamps are separated;
- completed-bar and settled-funding cutoffs are tested by mutation;
- every symbol needed for each native family universe passes coverage;
- no common-universe shortcut changes a family.

### G3 — accounting and current costs

- cash/equity identity reconciles from hand-computed fixtures;
- fees and slippage are charged once per virtual fill;
- funding is charged once per settled event with the correct side;
- fold boundaries, terminal marks and virtual force-flat rules are explicit;
- isolated and combined books reconcile independently.

### G4 — no-order safety boundary

- no broker/exchange write client is imported or instantiated;
- no credential is required or read;
- recursive output scan contains no secret or order response;
- an adversarial test attempting to route an order fails closed;
- emitted action type is limited to `TARGET_INTENT`.

### G5 — scheduler and restart safety

- exact decision timestamps for daily and weekly families are generated;
- duplicate launch/restart produces zero duplicate event IDs;
- late-data and process-crash fixtures recover without rewriting history;
- heartbeat contains last scheduled event, last completed event and byte count.

### G6 — virtual risk

- historical family caps are applied before each virtual fill;
- no margin or leverage path exists;
- combined exposure is measured but cannot alter isolated sleeves;
- any cap violation blocks that event and records the pre/post target.

### G7 — independent reproduction

A detached reproducer at the exact code/data/config hashes recreates a fixed
prospective interval and matches signals, fills, costs, funding, equity,
events and report bytes except explicitly listed wall-clock fields.

### G8 — independent prelaunch audit

A fresh-context A7 recomputes G0-G7, searches for historical identity drift,
future leakage, accidental order paths and vacuous tests. Required verdict:

```text
PROSPECTIVE_SHADOW_V1_START_AUTHORIZED
```

with zero unresolved HIGH/CRITICAL findings.

## 11. Two-key start rule

After G8 passes, the owner must type the following exact fresh phrase:

```text
GO PROSPECTIVE SHADOW V1 START
```

The phrase in this plan and the present request are intent, not a consumed GO.
A phrase typed before the G8 artifact exists dies unconsumed. It never
authorizes external paper/testnet/live orders.

## 12. Cycle phases and ownership

### P0 — control-plane repair and registration

1. Resolve the measured `CONTROL_STATE_DRIFT`; do not reclaim an unknown lock
   without proven ownership/liveness evidence.
2. Re-run cycle list, cycle doctor, lock inspect and program counters.
3. Register only after this plan is committed and the tree is clean:

```text
.venv/bin/python research/researchctl.py cycle register \
  --cycle PROSPECTIVE-SHADOW-V1 \
  --asset crypto \
  --plan plans/PLAN_prospective_shadow_v1.md \
  --branch orca/prospective-shadow-v1-integration \
  --worktree /Users/hoangminhlong/my-quantitative/.worktrees/prospective-shadow-v1/integration \
  --budget-max 0 \
  --go-phrase "GO PROSPECTIVE SHADOW V1 START" \
  --lifecycle PLANNED_NOT_STARTED
```

Registration must go through `researchctl`; never edit the registry manually.

### P1 — identity recovery and freeze

- A1: controller/integrator and only registry/freeze writer.
- Explorer lane: recover and hash the exact three historical identities.
- A7: independently compare recovered identities to historical commits and
  verdicts.
- Output under
  `research/control/prospective_shadow_v1/identity/`.

If any anchor identity cannot be recovered unambiguously, that sleeve becomes
`BLOCKED_IDENTITY`; the other two may proceed only if the selection was frozen
as three named independent observations and no replacement is introduced.

### P2 — data/PIT and cost freeze

- A3 owns prospective data authority, coverage, clocks and current cost inputs.
- Output one data manifest and one cost-regime manifest with per-file hashes.
- No network purchase, signup or key. Public/keyless acquisition still needs
  license and availability evidence.

### I — shadow implementation

- A2 owns shared virtual accounting, idempotency and combined read-only view.
- A8 owns the three thin family adapters around recovered historical logic.
- A dashboard lane owns the read-only owner UI and its reconciliation tests;
  it consumes public shadow-read models only and cannot import an order client.
- Allowed implementation paths are frozen in dispatch packets; lanes do not
  share files.
- Historical family code is not edited in place. Adapters call pinned code or
  carry a byte-accounted extraction with equivalence tests.

Planned runtime namespaces:

```text
research/shadow_v1/                         tracked code
research/control/prospective_shadow_v1/    tracked manifests/audits/state
results/prospective_shadow_v1/             append-only runtime outputs, gitignored
```

### Q — verification and prelaunch

- targeted unit and contract tests;
- deterministic double-run on synthetic hand-computed fixtures;
- exact historical replay for identity only, visibly non-prospective;
- full suite alone with no heavy worker;
- detached reproduction;
- A7 G8 audit;
- then wait for the fresh owner GO.

### E — forward observation

- Start from the first eligible event after `SHADOW_START_UTC`.
- Daily CARRY and weekly ILLIQ/PREMFADE schedules coexist, but a single
  scheduler serializes ledger writes.
- Lightweight polling must not hold the global heavy lock. Any bulk catch-up,
  full replay or full suite acquires the one machine-wide heavy slot.
- Publish a daily operational report and a weekly performance/risk report.
- Refresh the owner dashboard from reconciled ledger snapshots; dashboard
  failure does not stop ledger capture, but is reported `DASHBOARD_STALE`.

### R — ongoing reproduction and audit

- Reproduce each completed calendar month from frozen event inputs.
- A7 audits at 13, 26 and 52 weeks, or immediately after an incident.
- A1 alone lands append-only state and registry transitions.

### T — terminal close

At 52 weeks, or at an earlier hard safety stop, publish:

- each sleeve's after-current-cost and lineage-cost return, PF, MDD, turnover,
  funding and fold/symbol concentration;
- combined equal-capital exposure, correlation and overlap;
- missing/blocked event census;
- control and neighbour diagnostics;
- reproduction verdict and incidents;
- explicit statement that historical rejects remain rejects;
- `S1 = SEALED_UNTOUCHED`, `external orders = NONE`.

Terminal outcomes are limited to:

```text
SHADOW_V1_COMPLETED_OBSERVATION_ONLY
SHADOW_V1_BLOCKED_IDENTITY
SHADOW_V1_BLOCKED_DATA
SHADOW_V1_BLOCKED_CONTROL_STATE
SHADOW_V1_TECHABORT_PRESERVED
```

There is deliberately no `SURVIVOR`, `PRODUCTION_READY` or `LIVE_READY`
terminal outcome in this plan.

## 13. Evaluation at 52 weeks

The report re-applies each family's original gates for comparison and also
shows a common dashboard. Original thresholds are not relaxed. At minimum:

- after-current-cost total return and expectancy;
- PF and MDD;
- three forward chronological folds and largest positive-fold share;
- largest symbol positive-PnL share;
- base versus lineage/current-cost difference;
- adverse fee/slippage/delay stresses;
- neighbour sign support;
- causal/reverse control behaviour;
- decision count, blocked-event rate and data completeness;
- correlation and position overlap among the three anchors.

Passing these observations does not resurrect a rejected family. It creates
evidence for an owner decision about whether to write a separate confirmatory
plan. Failing them closes the observation without rescue.

## 14. Trial accounting and contamination

This cycle has `budget-max = 0` because it launches no retrospective scored
research cells. Its three anchors are recorded in a separate prospective
shadow-exposure ledger exactly once each. They do not increment the scored-cell
denominator, but all future proposals must disclose that their outcomes were
observed; they become forbidden outcome-exposed ancestry for blind discovery.

Diagnostic neighbours, controls, cost views, stresses and replays are labelled
as such and are never counted as independent discoveries.

## 15. Multi-agent orchestration contract

Use orchestration v3 only after registration and worktree bootstrap:

```text
A1 / Lead            controller, integration, registry, freezes
quant-explorer       historical identity plus data evidence only
quant-implementer    one bounded adapter/accounting task per worktree
quant-reproducer     detached exact-hash monthly reproduction
quant-auditor        fresh-context prelaunch and checkpoint audits
```

Every dispatch packet names exact base SHA, absolute worktree, branch,
allowed/forbidden paths, inputs, tests, stop conditions and handoff path.
Every delegated task ends with a valid `zcode_orch_v3_handoff@1` JSON.
Lanes never merge, rebase, push, edit the registry/central ledgers, or inspect
another lane's working files. A1 integrates one handoff at a time and tests
after every integration.

## 16. Immediate next action

The immediate action is **not to run the three families**. It is:

```text
1. commit/review this draft without touching the owner's .zcode files;
2. repair and independently verify the control-plane drift;
3. bootstrap and register PROSPECTIVE-SHADOW-V1;
4. recover and freeze the three exact historical identities;
5. build/audit the no-order shadow engine;
6. obtain the fresh post-audit owner GO;
7. start forward observation.
```

Until steps 1-6 are evidenced, status remains `NOT_RUNNING`.
