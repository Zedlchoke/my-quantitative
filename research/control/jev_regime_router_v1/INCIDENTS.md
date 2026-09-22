# JEV-REGIME-ROUTER-V1 — incident log (append-only)

## INCIDENT-JRV1-1 — ungated real-data arm computations by A1 (2026-09-22, phase I smoke/integration validation)

What happened: during post-integration plumbing validation, A1 executed:

1. `jrv1/run.py smoke --asset btcusdt --mock` and `--asset spy --mock`
   (intended MOCK_SMOKE namespace; the command also computes arm D — the
   deterministic router — which does NOT depend on mock decisions and
   therefore produced real-data net-PnL numbers for BTCUSDT and SPY).
2. `jrv1/run.py backtest --asset spy --arm A`, `--arm B`, `--arm C`
   (explicit real-data arm backtests, run to verify the CLI paths — these
   SHOULD have been deferred to the gated scored phase).

Ungated observed computations on real frozen data (5 total):

| # | computation | data | output artifact (preserved) |
|---|---|---|---|
| 1 | arm D deterministic router | BTCUSDT full frozen window | runtime/smoke/btcusdt/smoke_result.json |
| 2 | arm D deterministic router | SPY full frozen window | runtime/smoke/spy/smoke_result.json |
| 3 | arm A buy-hold benchmark | SPY | stdout (2026-09-22, worktree integration @ 255fcc7c) |
| 4 | arm B always-on trend | SPY | stdout (same) |
| 5 | arm C always-on mean-reversion | SPY | stdout (same) |

Classification: process-discipline breach (computations performed outside
the plan §9 gates: scored arms belong in phase E under heavy lock + owner
GO `GO JEV REGIME V1 SCORED BACKTEST`, all arms of an instrument in ONE
atomic run). NOT a data/S1/credential breach; no S1 touched; no external
API called; no file outside the cycle namespace written.

Exposure: aggregate net-PnL / trades / win-rate figures of 5 arm-runs were
rendered to A1's terminal. A1 has NOT used, and will not use, any of these
numbers to alter: the Jev prompt, feature contract, persistence parameters,
strategy mapping, folds, cost contract, arm definitions, or the evaluation
contract. All 12 planned scored cells remain to be computed atomically in
phase E from the same frozen contracts; the 5 ungated computations will be
recomputed identically there (deterministic engine) and the scored-phase
artifacts are the authority. The 5 ungated numbers enter the OBSERVED
counter as extra observations (they were computed; they do not disappear),
disclosed here and to A7-1 and to the owner at STOP-1.

Root cause: (a) the smoke command's scope (arm D included) was not
re-checked against the gating intent before running; (b) A1 ran explicit
arm backtests for CLI-path validation instead of limiting validation to
synthetic fixtures / census / freeze verification.

Prevention (effective immediately): NO real-data arm/backtest execution of
any kind before phase E GO. Remaining pre-GO validation is limited to:
tests (synthetic fixtures), census, freeze verification, mock-namespace
decision plumbing (arm E mock), and the cross-boundary request/response
round trip (mock). `backtest` subcommand is quarantined until GO.

## AMENDMENT-2 WINDOW RECORD — prior Lead session ended mid-work; inherited by new Lead session (2026-09-22, phase pre-BULK)

What happened: the previous Lead session (same cycle, same owner GO
instruction) ran the post-STOP-1 G0 sequence with the owner-provided key:
model probe -> pin jev-1.13.0 VERIFIED_LIVE (commit f71d9baf, 06:43:17Z),
live synthetic canary on the pinned model -> 5/5 FAIL (prompt carried no
feature-vector schema; FIX1 CLEAR_UPTREND answered TRANSITION_UNKNOWN at
confidence 0.82), authored amendment_2 (feature schema embedded verbatim
from freezes/feature_contract.json; prompt digest hashed into the cache
key; PROMPT_VERSION V1_amendment_2), re-ran the canary -> FIX1/FIX2 not
inverted, then ran a bounded LIVE replay validation of 94 BTCUSDT states
(13:52-13:53 +0700, adapter cache runtime/replay/btcusdt/, all mode "live",
model jev-1.13.0). The session ended (context exhausted) leaving amendment_2
UNCOMMITTED in the working tree.

Authority analysis (by the new Lead session): the 94-state live replay is
within the plan section 0a canary budget law ("<=100 historical states in
canary even with a key") and is cache-first reusable for BULK; the GO phrase
remains REGISTERED_NOT_CONSUMED (verified in the registry); no scored PnL or
arm computation ran in this window. The canary FAIL -> amendment_2 -> re-run
follows the cycle's established pre-scoring amendment pattern (amendment_1
precedent; HOW_TO_BE_A_LEAD_ENGINEER section 24: amendment + minimal scope +
tests + fresh A7 delta audit before proceeding). The new Lead session
performed the P-17 activity check before touching the surface: no jrv1/adapter
process alive, heavy lock FREE_PROVEN, decision file byte-stable over a 12s
watch, last artifact 5 minutes old (session dead, not mid-flight).

New-session completion of the inherited work (all pre-outcome, pre-GO):
- tests re-verified green on the working tree: 110 py + 63 TS + typecheck
- replay.py amendment_2 cost-evidence capture: adapter stdout summaries
  (input token usage, per-run counters) persisted one-line-per-call to
  runtime/<ns>/adapter_summaries_<asset>.jsonl; new test
  test_replay_captures_adapter_summaries (mock; cache hits add zero lines)
- freeze digest re-verification: 12/12 intact vs freeze_manifest.json;
  amended list preserves old shas (amendment_1, model_pin, amendment_2)
- credential scan: 118 live artifacts, 0 leaks (value compared in memory,
  never printed)
- canary verdict reconstructed from stored bytes (zero new API calls):
  runtime/canary_amendment_2_verdict.json — frozen pass_criteria PASS
  (FIX1 UPTREND 0.41 / FIX2 DOWNTREND 0.63), with mandatory disclosure that
  FIX3/FIX4/FIX5 sit outside their recorded expected_acceptable soft sets
  (2/5); A7-1-r2 must adjudicate BEFORE the GO is consumed. If A7 rules the
  soft sets binding -> canary FAIL -> bulk stays BLOCKED for the owner.

Live-call accounting to date: 1 models probe + 15 synthetic canary calls +
94 historical states = 110 billable calls; historical budget 94/100 OK;
token usage for these calls NOT captured (disclosed); BULK usage will be.

Prevention: G0/canary phase must persist adapter summaries from the first
live call (now enforced by the replay capture + test); sessions must commit
amendment work incrementally.
