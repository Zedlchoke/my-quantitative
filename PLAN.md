# SPRINT V9H-R → V10 — RECOVER, AUTHORIZE, THEN DISCOVER

> **Authority:** continuation contract for a fresh coding-agent context. Do not
> restart V9H or recreate completed work.
>
> Root: `main=e5b0bab`, `origin/main=425843d`. Integration:
> `orca/v10-integration=b7c39a2`, clean. Immutable V9 execution SHA:
> `206faf8aac5b3f7136001a45d3e7a3e85cb923e5`.
>
> The old deadline `2026-08-26T23:51:56Z` is expired. It must never be silently
> extended. Freeze a new recovery contract before continuing.

## 1. Mission

1. **V9H-R:** finish and independently audit the research-machine hardening
   already integrated at `b7c39a2`.
2. **V10:** only after `V9H_PASS_V10_AUTHORIZED`, propose genuinely new crypto
   mechanisms, preregister at most six trials, walk-forward, stress, reproduce
   and score them honestly.

The objective is trustworthy evidence, not forced profit. `REJECT_ALL` and
`NO_ELIGIBLE_FAMILY_NOT_RUN` are valid scientific outcomes.

## 2. Measured intake

### Completed

- V9 terminal: `V9_REJECT_ALL_MULTI_FAMILY`; historical denominator **117**.
- V9 archive: 356 files, 231,797,462 bytes, bundle SHA-256
  `b5ce4097e09f8de1f99b67a4bc0dbf4b2390daad78cc594591907b9a60a12b12`.
- Restore: 356/356; five trials readable; reproduction 5/5 `all_match`; two
  TECHABORT archives have zero scored metrics.
- H1 integrated: A2 evidence, A3 controller/governor, A4 streaming repro/cache.
- H2 integrated: A5 contract/statistics, A6 data/PIT, A10 adversarial/golden.
- TS-TREND and VOLSHOCK real-path report: `byte_identical=true`.
- Integration is clean at `b7c39a2`.
- A8/A9 have not started; V10 budget consumed = 0.

### Missing or stale

- No committed A7 V9H verdict or final H01–H14 ledger.
- No committed final full-suite/resource-cap report for integration.
- Control manifest records H1 but not the completed H2 merge state.
- Worktree manifest still has H2/audit/proposal `TBD_*` fields.
- Existing A7 worktree has an uncommitted rerun of A10's golden report. The
  observed diff changes temporary paths/runtime only, but A7 must not commit an
  A10-owned artifact.
- The previous control window expired.

Current valid state:

```text
V9H_RECOVERY_REQUIRED
V10_NOT_AUTHORIZED
V10_BUDGET_CONSUMED = 0
```

## 3. Boundaries

- A1 alone creates worktrees, merges, freezes, launches and closes the sprint.
- A7 writes only `research/audits/v10/a7_*`; never production/A10 evidence.
- No agent edits root/main or another role's worktree.
- No push, worktree deletion, credentials, S1, equity score, paper/testnet/live,
  orders or leverage changes.
- Current crypto data is inspected **S0 screening**, not untouched OOS.
- Crypto perpetual and equity/TradFi contracts remain separate.
- V1–V9 rejected families remain forbidden rescue targets. A rename, lookback,
  threshold, cadence, symbol, cap, direction or post-result filter is not a new
  mechanism. Do not tune or rescue `TSTREND-L28`.
- Do not view new PnL before proposals, specs and budget are frozen.

## 4. Agents and worktrees

Reuse `/Users/hoangminhlong/my-quantitative-v10-wt/`; do not recreate completed
clean worktrees.

| Role | Worktree | Next responsibility |
|---|---|---|
| A1 | `integration-v10` | recovery contract, reconciliation, merge/freeze/launch/close |
| A2 | `a2-evidence` | archive support only for a specific failed gate |
| A3 | `a3-runtime` | controller/governor remediation only if a gate fails |
| A4 | `a4-reproduction` | streaming/cache remediation only if a gate fails |
| A5 | `a5-contracts-stats` | manifest reconciliation; later novelty/statistics |
| A6 | `a6-data-pit` | manifest reconciliation; later PIT/data hooks |
| A7-R | new `a7-v9h-reaudit` | independent H01–H14 audit from `b7c39a2` |
| A8 | `a8-hypothesis-1` | proposals only after V9H PASS |
| A9 | `a9-hypothesis-2` | proposals only after V9H PASS |
| A10 | `a10-qa` | evidence reconciliation/remediation only |
| R1/R2 | created after final V10 SHA | detached execution/reproduction |

Rules:

- Maximum **four light agents total including A1**.
- Heavy workers = `min(2, measured_governor_cap)`.
- Never run full suite with heavy backtests.
- Silent-death/memory-pressure work runs sequentially unless three consecutive
  two-worker unscored probes pass.
- No grandchildren/new worktrees unless A1 first records delegation, path,
  branch and allowlist.
- Parallel agents must have non-overlapping outputs.
- Each agent returns branch, commit, files, tests, limitations and clean state.
- A1 cherry-picks narrow commits and runs targeted tests after every pick.
- Never auto-resolve conflicts involving clocks, fills, costs, funding, folds,
  metrics or scoring.

## 5. R0 — recovery freeze

Before modifying integration, A1 must:

1. Verify root/integration/all V10 HEADs and tree states.
2. Verify no owned worker using the authoritative controller. Broad `pgrep -f`
   and `pkill -f` are not ownership evidence.
3. Create `research/control/v10_hardened_run/recovery_contract.json` with intake
   SHAs, old deadline marked `EXPIRED_NO_AUTO_EXTENSION`, new V9H-R start and
   maximum four-hour deadline, zero V10 consumption, roles and outcomes.
4. Create a clean A7-R worktree from `b7c39a2`. Preserve old dirty A7 untouched.
5. Reconcile `manifest.json` and `worktree_manifest.json` with actual H2 commits,
   merge SHAs, tests, clean states and A7-R identity. No stale `TBD_*` for a
   completed or active V9H role.

Material intake mismatch must be recorded and handled fail-closed.

## 6. R1 — finish V9H evidence

Do not refactor passing code. Remediate only an explicitly failed gate.

Required artifacts:

- `research/control/v10_hardened_run/test_report_v9h.json`
- `research/control/v10_hardened_run/resource_cap_report.json`
- `research/control/v10_hardened_run/gate_ledger_v9h.json`
- `research/audits/v10/a7_v9h_hardening_audit.json`
- `research/audits/v10/v9h_closeout.{json,md}`

Required measurements:

1. Targeted A2/A3/A4/A5/A6/A10 tests on clean integration.
2. Full suite once, alone, with `.venv/bin/python -m pytest`.
3. Timeout/orphan isolation for ten consecutive rounds.
4. Heartbeat and streaming-log visibility while a synthetic worker is alive.
5. Three consecutive two-worker unscored resource probes. Freeze cap=2 only if
   all are safe with at least 2 GB reserved; otherwise cap=1.
6. Enabled cache on/off byte parity and fresh-process reproduction. Disable
   cache if proof is incomplete.
7. Both real-path golden tests from two temporary roots. Exclude only declared
   ephemeral paths/timing from semantic equality.
8. Denominator=117, funding sign, direction, return matrix, warmup,
   purge/embargo, completed-bar signal and next-event fill clocks.

### H01–H14: all required

1. V9 authority ancestry.
2. V9 archive/restore PASS.
3. No owned V9/V10 worker at audit intake.
4. Atomic controller/status; no broad process-name ownership.
5. Exact process-group timeout; ten rounds, zero orphan.
6. Current, unambiguous heartbeat/terminal truth.
7. Non-null frozen timeout at worker/harness/rerun layers.
8. Enforced measured resource cap.
9. Logs readable before completion.
10. Enabled cache byte parity plus fresh-process repro.
11. Denominator/direction/funding/return-matrix contracts.
12. TS-TREND/VOLSHOCK real-path determinism.
13. Targeted and full suite PASS on clean integration.
14. A7-R PASS with zero unresolved HIGH/CRITICAL.

One failed or unverifiable gate closes
`V9H_BLOCKED_V10_NOT_AUTHORIZED`; no score. After a named code remediation,
freeze a new integration SHA and rerun affected gates plus A7-R.

## 7. V9H transition

`V9H_PASS_V10_AUTHORIZED` requires H01–H14 PASS, one clean pinned integration
SHA, owned workers=0, V10 budget=0 and integrated A7-R evidence without
production changes. Then A1 freezes a separate V10 contract and fresh **12-hour
V10 clock**. The recovery clock alone never authorizes V10.

## 8. N — blinded proposal firewall

Only after V9H PASS, dispatch A8/A9 in parallel from the same authorized SHA.
Each proposes at most three mechanisms and writes evidence only—no strategy code
or backtest.

Each proposal states economic source/counterparty, PIT inputs, causal sign,
signal/fill clocks, horizon, construction, success/failure regimes,
falsification, negative control, nearest historical families, structural delta,
sample feasibility, audit cost, one anchor and one justified neighbor.

A5 builds a blinded novelty matrix; A7 challenges rescue risk. Novelty must be
material in at least four dimensions: economic source, observable construction,
selection/payoff geometry, counterparty/regime prediction.

| Pre-score component | Points |
|---|---:|
| Novelty/independence | 35 |
| Mechanism/falsifiability | 25 |
| PIT/data readiness | 15 |
| Negative control | 10 |
| Sample feasibility | 10 |
| Auditability | 5 |

Select at most two families with total ≥75, novelty ≥28, no hard/data fail
and A7 no-rescue concurrence. Tie-break by frozen hypothesis ID. If none pass,
close `V10_NO_ELIGIBLE_FAMILY_NOT_RUN` with zero trials.

## 9. I — implementation and preregistration

For each selected family freeze one anchor, one neighbor and one negative
control. One family = exactly 3 scored slots; two = exactly 6. Unused slots
cannot be replaced after any metric is visible. No grids, rescue lookbacks,
substitute symbols, post-result filters or performance retries.

- A8/A9 own isolated family modules/tests.
- A6 owns shared PIT/data hooks.
- A5 owns statistics/finalizer/ledger.
- A10 owns golden/parity/anti-leak/adversarial tests.
- A1 merges modules → hooks → statistics → tests.

Freeze code SHA `W`, data/universe/spec hashes, IDs/commands, budget, contract,
baseline and manifest. Create clean detached R1/R2 at `W`. A7 prelaunch PASS is
mandatory.

## 10. G01–G20 prelaunch

All PASS: V9 ancestry; archive restore; V9H authorization; clean/no worker;
universe/window/hash freeze; PIT coverage; denominator=117; proposal firewall;
novelty; no rescue; families≤2; exact budget 3/6; complete specs;
lookahead/warmup/purge; cost/funding/direction/accounting; golden twice;
governor/timeouts/retry; provenance pins; clean R1/R2 at `W`; A7 PASS with zero
HIGH/CRITICAL. Any failure means `V10_BLOCKED_PRELAUNCH` and no score.

## 11. V10 execution

- At least three chronological folds; warmup outside scored OOS.
- Purge/embargo ≥ holding horizon; completed-bar feature, next-event fill.
- Costs: 5 bp taker + one adverse tick + native funding unless stricter frozen.
- Stress every cell: fee/slippage ×1.5, +2 ticks, +1 event delay,
  drop-one-symbol and drop-one-fold.
- Flat hard benchmark; buy-and-hold/BTC-beta-neutral only context.
- Unique output/shard/log per worker; reproduce every cell fresh/clean.
- One technical retry only with proof of zero scored metric. A published score
  consumes budget even if the process later crashes.
- Heavy execution in waves at `min(2, frozen_governor_cap)`.

## 12. Stage-A decision

Hard gates: after-cost expectancy >0; PF≥1.10; at least 2/3 positive folds; no
populated fold PF<0.80; fold contribution≤50%; MDD≤10%; symbol
contribution/risk≤40%; sample floor; no drop-one dependency; stressed PnL>0
and PF≥1.00; neighbor supports anchor; control preserves causal sign; repro
`all_match`; multiple-testing proof or honest `UNAVAILABLE_FAIL_CLOSED`; zero
HIGH/CRITICAL.

Only hard-gate passers are ranked: validity 20, return 20, fold/regime 20,
stress/concentration 25, statistics 15. Score cannot rescue failure; controls
cannot be promoted.

## 13. Outcomes and S1 boundary

V9H outcome: `V9H_PASS_V10_AUTHORIZED` or
`V9H_BLOCKED_V10_NOT_AUTHORIZED`.

V10 outcome: `V10_NO_ELIGIBLE_FAMILY_NOT_RUN`, `V10_BLOCKED_PRELAUNCH`,
`V10_INCOMPLETE_NOT_PROMOTABLE`, `V10_REJECT_ALL`, or
`V10_STAGE_A_SURVIVOR_LOCKED_FOR_FUTURE_S1`.

Never label `EDGE_CONFIRMED`, `PRODUCTION_READY`, `PAPER_READY`,
`TESTNET_READY` or `LIVE_READY`. V10 cannot inspect S1. A survivor is only
locked for a later non-overlapping Stage-B sprint (PF≥1.15, MDD≤10%, stability,
shared-capital/stress and 6–8 weeks signal-only).

## 14. Fail-safe

- V9H-R maximum four hours; failure closes blocked with evidence.
- V10 maximum twelve hours from its own authorization/freeze.
- <120 minutes: no new scored wave. <45 minutes: stop exact owned groups,
  reconcile and close.
- Missing reproduction/A7 terminal audit = `V10_INCOMPLETE_NOT_PROMOTABLE`.
- Do not bypass permission controls. On an external-path denial, record
  `PERMISSION_BLOCKED`, stop before scoring and report exact path/action.
- No destructive cleanup or push without separate owner authorization.

## 15. Definition of Done and reports

Required: recovery contract; reconciled manifests; H01–H14 ledger; test/resource
reports; A7-R audit; V9H verdict; and, if authorized, proposal/novelty inventory,
exact budget, frozen prelaunch artifacts, scored/stress/repro evidence, return
matrix/statistics, family summary, challenge memo, A7 terminal audit and master
`.md` + `.json`. Synchronize `PLAN.md`, `CONTINUE.md` and Wayfinder map; finish
with clean integration, owned workers=0 and one terminal verdict.

A1 reports at intake/deadline, manifest reconciliation, V9H gate/A7 result,
transition, selection, prelaunch, each execution wave and terminal closeout. A1
continues through safe non-destructive steps and stops only for a real gate,
permission/deadline, cleanup/push, credential, S1 or live/order boundary.
