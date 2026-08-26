# SPRINT V9P → V9 — MULTI-FAMILY CRYPTO DISCOVERY (S0 exploratory only)

> Owner: A1 controller/integrator/scientific owner. Frozen lineage:
> `research/control/v9_multifamily_run/manifest.json`
> (start 2026-08-26T03:41:37Z, hard deadline 15:41:37Z, bootstrap 99afc59).
> Parent: V8R closed `V8_REJECT_ALL` (main f72c152; A7 evidence integrated 99afc59).

## 1. Mission

Test up to three economically DISTINCT mechanisms on a fixed 10-altcoin cohort.
No rescue of rejected families. No parameter grids. Everything S0 exploratory;
positive results may only be labelled `STAGE_A_PASS_EXPLORATORY` or
`LOCK_FOR_FUTURE_S1`. `EDGE_CONFIRMED` / `PRODUCTION_READY` / `LIVE_READY` are
forbidden labels. No S1/paper/live/orders ever in this sprint.

## 2. Forbidden rescues (global historical trial ledger is authoritative)

weekly_reversal (V8 REJECT_ALL) · funding_carry (V6) · funding_crowding_MR ·
volatility-compression breakout (rejected variant) · funding_price_divergence
(V7) · any other family with a terminal rejection in the ledger.
`H-XSECT-REVERSAL-BREADTH-CRYPTO-v1` stays read-only frozen; A7 judges novelty.
Default outcome if not materially distinct from weekly reversal: archive
`NOT_RUN_RESCUE_OF_REJECTED_FAMILY`, never scored.

## 3. Cohort (frozen input, re-pinned for V9)

Corrected A8 deterministic selection rule (pre-window median daily quote volume,
BTC benchmark-only, exact 15m census, held-exposure funding completeness).
V9 contract must re-pin SHA-256 of `data/v8x_manifests/crypto_universe_selection.json`
and re-audit coverage on the scored window. No symbol changes for any
performance reason.

## 4. Families (materially distinct mechanisms only)

| ID | Mechanism | Notes |
|----|-----------|-------|
| F1 TS-TREND | Time-series trend/momentum per symbol (own trailing return sign), independent of cross-sectional ranking | Distinct from XSC reversal |
| F2 RESIDUAL-MR | Market-neutral mean reversion on BTC-residualized alt returns | Distinct: residual/relative + reversion |
| F3 LIQ-SHOCK | Volume-shock conditioned short-horizon continuation among shocked names | Distinct: liquidity/volume conditioning |

Fewer than three families is acceptable; INCONCLUSIVE/BLOCKED is an honest
outcome. Weak families must not be invented to fill slots.

Each family spec must carry: hypothesis.md/candidate.yaml/status.yaml,
economic mechanism, expected counterparty, regime expectations, exact signal +
execution clock (Monday 00:00 UTC completed bars, next-15m-event fill),
PIT feature rules, no-lookahead tests, fixed universe, fixed parameters,
costs (5bp taker + 1 tick adverse), native funding, 3 chronological folds with
purge/embargo ≥ holding horizon, negative control, allowed outcomes, forbidden
promotion labels.

## 5. Trial budget (frozen)

Max 9 scored trials total. Planned structure per family: ≤2 candidate variants
+ exactly 1 negative control. Any published scored metric consumes budget.
Forbidden: performance retry, replacement trials, extra lookbacks, universe
changes, post-result filters, ledger deletions.

## 6. Gates P01–P15 (machine-readable, all must PASS before any scored launch)

P01 V8R A7 evidence in main ancestry, main clean · P02 sprint start/deadline/
bootstrap frozen · P03 universe+hashes frozen · P04 PIT price/funding/metadata
coverage PASS · P05 historical trial ledger complete · P06 candidate novelty/
independence PASS · P07 no rejected family silently retried · P08 exact budget
frozen · P09 specs contain no placeholders · P10 runner supports selected
families · P11 golden vectors byte-identical twice · P12 cost/funding/accounting
tests PASS · P13 baseline/contract/manifest pins agree · P14 detached execution
heads clean and identical · P15 A7 prelaunch PASS zero HIGH/CRITICAL → then and
only then `V9_LAUNCH_AUTHORIZED`.

## 7. Execution & validation

Waves ≤2 heavy workers. Unique experiment IDs/output dirs/shards; exact frozen
command; PID/log/start/end/exit; provenance enforcement; completed-bar
semantics; next-event fills; fees/slippage/native funding; 3 folds purge/
embargo; stress (fee×1.5, +2 ticks, +1 event delay, drop-one-symbol/fold);
terminal liquidation reconciliation. After all trials: independent reproduction
(all-match), concentration checks, shared-capital replay if multiple pass,
DSR/PBO or honest insufficiency, multiple-testing adjustment over the global
ledger, hard gates + scorecard, A7 terminal audit.

Stage-A floor: after-cost expectancy > 0 · PF ≥ 1.10 · ≥2/3 folds positive ·
no populated fold PF < 0.80 · risk within contract · no concentration cap breach
· stress survives edge · reproduction all-match.

## 8. Equity

A9 prepares readiness contract ONLY. No stock scored backtest this sprint.
Outcome: `V8X_EQUITY_NOT_STARTED_PROVIDER_AND_SPEC_BLOCKED` unless owner later
provides provider/credentials/calendar/corporate-action policy. Equity v1 stays
frozen untouched; v2 draft only with correct session mapping (never
15/25/50 sessions ≡ 3/7/14 days).

## 9. Fail-safe

Remaining <300min: no new family/wave. <120min: no new scored wave. <45min:
terminate workers, reconcile, close honestly. Every worker has PID+log+output
contract. No push remote.
