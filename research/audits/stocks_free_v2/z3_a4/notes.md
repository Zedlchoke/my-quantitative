# Z3 A4 audit notes — outcome-blind family specification

Lane: A4 / Z3 momentum. Worktree
`/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z3-momentum`,
branch `orca/stocks-free-v2-z3-momentum`, bootstrap `b345de4` (identity verified
before any write; status clean).

## Inputs read (read-only)

- `PLAN_stocks_free.md` §2/§3 (cohort, clock, portfolio), §10 (Z3 requirements), §14 (Stage-A gates).
- `research/control/stocks_free_v2_run/cohort_census.json` (digest c9d4e88a…bc96, 11 accepted, XLC rejected, TLT/GLD excluded pre-census).
- `research/control/stocks_free_v2_run/partition.json` (warmup 2018-01-02..2018-04-03, S0 2018-04-04..2025-07-31, 3 folds with scored ends 2020-09-01 / 2023-02-09 / 2025-07-24, purge 5, S1 SEALED).
- `research/control/stocks_free_v2_run/run_contract.json`, `split_factors.json` (five 2:1 issuer splits effective 2025-12-05, inside sealed S1; S0 unaffected; amended FD2 TR formula).
- `research/audits/stocks_free_v2/da2/da2_evidence.json` (PASS_WITH_RECORDED_LIMITATIONS; SPY TR vs SSGA NAV-TR 0.39% cumulative divergence; a priori tolerances).

Not read, by rule: the A5 (z3-trend) lane's work or files. No branch switch. Historical V1 files
under `research/proposals/stocks/` were only listed (existence check for namespace collisions);
none opened.

## What was produced

- `research/proposals/stocks_free_v2/a4_z3_relative_momentum_spec.json` — canonical frozen spec.
- `research/proposals/stocks_free_v2/a4_z3_relative_momentum_spec.md` — human-readable twin.
- `research/audits/stocks_free_v2/z3_a4/digests.json`, this `notes.md`.

## Digests

- Canonical spec JSON sha256: `98d5307c3c3810a236f230475b190b34bd38461461cc7ea0a5ebdf38741416fa`
  (sha256 of exact file bytes after final write; see digests.json for the full set including the
  .md and these audit files).
- Recompute: `/Users/hoangminhlong/my-quantitative/.venv/bin/python -c "import hashlib;print(hashlib.sha256(open('<spec.json>','rb').read()).hexdigest())"`

## Design decisions and their justification (outcome-blind)

1. **Rankable cross-section = 10 sector ETFs; SPY benchmark-only.** Census assigns SPY the role
   BROAD_US_EQUITY_BENCHMARK; including the broad index in a sector cross-section double-counts
   beta and blurs the tested mechanism. The eligible universe remains "the 11 + cash" as frozen;
   the role restriction is declared, not a silent exclusion.
2. **Monthly clock.** 12-1 cross-sectional momentum is documented at monthly rebalancing; weekly
   imports short-horizon reversal/microstructure contamination and ~3-4x turnover. Frozen a priori,
   identical across all three arms (required for control symmetry).
3. **Session-count lookbacks (252/21).** 252 regular sessions ~ 12 months, 21 ~ 1-month skip
   (Carhart/Jegadeesh-Titman convention; the skip addresses documented 1-month reversal,
   Lehmann 1990 / Jegadeesh 1990, MODEL_INTERNAL_UNVERIFIED).
4. **Warmup extension, declared.** Vendor coverage begins 2018-01-02; a full 253-session window
   first exists at the 2019-01-31 month-end. Slots 2018-04..2018-12 are unscored warmup-extension.
   The alternative (truncated expanding lookback) was rejected a priori: it makes the first-year
   feature heterogeneous and smuggles in a design choice. Cost: 12 unscored monthly slots; the
   fold minima (>= 15/fold) still hold with calendar slots 20/28/29 = 77 total.
5. **No rank buffers.** Buffers (hysteresis) would break the requirement that the negative control
   differ from the anchor by the ranking sign alone. Turnover consequences are absorbed by the
   cost assumptions instead.
6. **Neighbour lever = risk normalization.** Same lookback family; score divided by
   formation-window realized vol and inverse-vol weights, targeting the momentum-crash channel
   (Barroso & Santa-Clara 2015 JFE; Daniel & Moskowitz 2016 JFE). This is a mechanism lever, not a
   grid point: no alternative lookback/rank-count was considered or scored.
7. **Negative control = reversed sign.** Bottom-3 by the identical 12-1 score, identical clock,
   construction, costs. Its falsification rule is asymmetric and explicit: control passing both
   primary Stage-A gates, or matching/beating the anchor in >= 2/3 folds, destroys the mechanism
   claim (then the family is rejected regardless of anchor results). Known residual confound:
   the control keeps long-only equity beta, so the operative read is anchor-vs-control pairing;
   Grundy & Martin (2001 RFS, MODEL_INTERNAL_UNVERIFIED) support that momentum profits are not
   static factor exposures.
8. **Costs.** 7 bps one-way base (2 spread + 3 slippage + 2 commission/ops buffer) and 12 bps
   stress. Spread/slippage figures are regime knowledge for top-tier sector ETF liquidity
   (MODEL_INTERNAL_UNVERIFIED) and are used conservatively; no commission evidence exists, so a
   2 bps buffer is carried rather than claiming free trading. Cash yield 0 per run contract.
9. **Evidence count.** 60 total / 15 per fold minimum independent (non-overlapping monthly holds);
   expected 77 calendar slots (20/28/29) derived arithmetically from the frozen partition — this
   counts sessions/month-ends, never outcomes.
10. **Force-flat and terminal close.** At each fold scored_end and the S0 terminal close the book
    flattens with a costed exit; the 2025-06-30 decision therefore holds a partial month
    (2025-07-01..2025-07-24). The book is flat across the S0/S1 boundary; S1 never referenced
    beyond that boundary rule.

## Assumptions and limitations to carry forward

- Cohort is a current-survivor SPDR seed list; claims restricted to the frozen cohort.
- Fill-price convention: "next-session raw executable price" under the shared adapter; the exact
  fill field (raw close) must be confirmed against the shared execution adapter contract at Z5/Z6;
  the one-event delay and never-signal-close invariants are the binding constraints.
- 2025-12-05 splits lie inside sealed S1; S0 features unaffected; TR formula frozen per amended
  FD2 for the full coverage nonetheless.
- Turnover and capacity numbers above are prior expectations/ceilings; realized values are measured
  at Z6 from the schedule-only dry run, never tuned against them.

## Attestation

No returns, PnL, PF, Sharpe, ranking or backtest of the proposed strategy was computed. No scored
artifact exists or was created. S1 was not inspected. The A5 lane was not opened. All writes are
inside `research/proposals/stocks_free_v2/a4_*` and `research/audits/stocks_free_v2/z3_a4/**`.
