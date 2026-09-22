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
