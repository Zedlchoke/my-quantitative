# CYCLE VERDICT — EURUSD-OPEN-SEARCH-V1 (TERMINAL, 2026-09-23)

- Branch: `orca/eurusd-open-search-v1-integration` (worktree
  `.worktrees/eurusd-open-search-v1/integration`); terminal HEAD recorded in
  registry. Plan: `plans/PLAN_eurusd_open_search_v1.md` + Amendment A1 (§8).
- Data authority: Dukascopy public M1 bid/ask candles 2021-01-01..2025-12-31
  UTC (3,652/3,652 day files, 0 missing; probe PROBE_PASS: 24-byte layout
  proven against tick ground truth; census BUILD_PASS: 119,038 valid 15m
  bars, 0 non-positive-spread minutes, spread p50 0.3 pips). Recorded as
  `OWNER_DIRECTIVE_SOURCE_AUTHORIZATION` + `TCU_RISK_DISCLOSED` per owner
  directive 2026-09-23 #2; no account, no ToS acceptance, no purchase; raw
  bytes machine-local (gitignored), only SHA manifests committed.

## VERDICT: `NO_CANDIDATE_NO_VALUE`

Exactly one enum per plan §6. The single frozen candidate failed its ONE
preregistered holdout check; per plan §5 the failure is final — no
re-tuning, no second look, holdout not rescued.

## What was tried (the actual denominator)

- **48 of 96 budgeted exploratory trials computed** (12 families × 4
  configs; FXOS-01..24 census in plan §2, implemented set + NOT_RUN reasons
  frozen in `selection_freeze.json` BEFORE any outcome).
- **After measured costs (k=1.0): 5/48 profitable** (median trial −1,497
  pips — costs dominate this market at 15m granularity).
- **At stress 1.5×: 4/48 survive; at 2.0×: 1/48 stays positive.**
- 1 trial passed all gates → frozen: **FXOS-04-C4** (Bollinger mean
  reversion, N=192×15m, z=2.5): dev +1,203.6 pips, PF 1.1445, 609 trades,
  folds −162/+545/+497, positive even at 2.0× (+204.3).
- Near-miss disclosed, NOT frozen: FXOS-10-C3 (London OR breakout) failed
  G2 by 0.0081 PF.

## The holdout answer (the owner's question)

**The best candidate did NOT stay profitable on untouched data.**
FXOS-04-C4 on 2023-07-01..2025-12-31 (59,885 bars, 630 trades), one look,
criteria preregistered before opening:

| tier | net pips | PF | hit |
|---|---|---|---|
| k=1.0 | **−134.4** | 0.9816 | 0.584 |
| k=1.5 | −585.1 | 0.9225 | 0.570 |
| k=2.0 | −1,035.9 | 0.8676 | 0.556 |

Success criteria (net>0 @1.0 AND @1.5) → **NOT MET**. Baselines on the same
window: LONG_ALWAYS +286.7@1.0 but −542.1@1.5 (naive long dies at stress);
SHORT_ALWAYS −1,944; RANDOM_MATCHED −8,948 (engine cost honesty check).
Conclusion: the dev-period edge was selection luck/regime fit across 48
trials, not a durable after-cost edge. **No strategy found this campaign is
worth prospective capital.**

## Governance state

- A7 prelaunch: **AUTHORIZED** (independent 48/48 trial recompute, byte-exact
  match; fixtures 7/7; freeze chain verified) — `audits/a7_prelaunch_audit.*`.
- Leak guards held: dev runner loaded only bars < 2023-07-01 (physically);
  holdout plane built only at P3; no holdout metric existed before the check.
- Incidents disclosed: (1) probe layout bug 20B-vs-24B caught by fail-closed
  probe BEFORE corpus build; (2) pandas-3 datetime-unit bug broke force-flat
  calendar — caught by hand-computed fixture BEFORE any outcome; (3) a
  hand-typed config digest was wrong — caught by recompute, corrected in
  `candidates_frozen.json` (INC-DEU-1 class).
- D2 = OWNER_WAIVED_EXPLORATORY in every record; never evaluated, never PASS.
- S1 SEALED_UNTOUCHED; no orders/paper/live anywhere; no secrets printed.
- Owner GO `GO EURUSD OPEN SEARCH V1 EXPLORATORY SCORED`: registered,
  never consumed → extinguished UNCONSUMED at close (P-8; no scored
  execution happened: nothing survived to execute).
- Observed trial denominator: 48/96 budget used. EURUSD-DATA-QUALIFICATION-V1
  verdict and all historical forex verdicts untouched.
