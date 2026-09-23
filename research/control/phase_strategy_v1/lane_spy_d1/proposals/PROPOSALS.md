# PROPOSALS — SPY_D1 (lane L3, cycle PHASE-STRATEGY-V1)

Direction law: **SPY long/flat ONLY** (no short/leverage authority).

## Outcome: ZERO proposals frozen (proposal_count = 0)

| phase | floors met | slot |
|---|---|---|
| ACCUMULATION | False | **NOT_RUN_THIN_PHASE** |
| UPTREND | True | **NO_ELIGIBLE_PROPOSAL** |
| DISTRIBUTION | False | **NOT_RUN_THIN_PHASE** |
| DOWNTREND | False | **NOT_RUN_THIN_PHASE** |
| TRANSITION_UNKNOWN | None | **NO_ELIGIBLE_PROPOSAL** |

### Why the single data-sufficient phase (UPTREND) still carries no proposal

Floors ARE met (margin +3 episodes; thin, F3 exactly at the fold floor). No strategy is proposed because every economic-mechanism class expressible as a long/flat book from this cell's own data (single-asset SPY OHLCV daily) is forbidden or measured dead on this program: (1) trend participation = phase-gated always-on-trend class, plan section 7.1 (UP_TREND_SLOW_LONG; dead stocks family A5-SFV2-TREND-DEFENSIVE); (2) mean-reversion = always-on-MR class, plan section 7.1 (ACC_RANGE_MR; dead family SFV3-A5-IDIO-SHOCK-REVERSAL); (3) calendar month-settle timing = measured-dead family SFV3-A6-TOM-SETTLE (SCIENTIFIC_REJECTION, FAMILY_FAILURES.jsonl) - proposing it is a reopening, independent of rho; (4) quarter-anchored calendar timing (opex/buyback-window/dividend-transition) = measured rho +0.559 vs the cell-reconstructed dividend ex-date window dummy (> 0.20 bar) against the plan section 7.2 dead class dividend-transition books; (5) volatility-state or participation conditioning = plan section 7.2 dead classes and measured-dead families SFV4-A4-H1-SEMIVARIANCE-SHARE and SFV4-A5-H1-PARTICIPATION-SHIFT; (6) breadth/relative-rotation = plan section 7.2 dead class and requires QQQ (not in this cell); (7) single-name earnings/filing mechanisms = data-dead in this cell. A phase-gated variant of any of these is the same mapping class (plan section 7.1) and would be vetoed at integration; the lane declines rather than hazards it.

### Thin phases

- **ACCUMULATION**: below immutable floors (15 fold-local episodes < 20; fold decisions max 24 < 100). NOT_RUN_THIN_PHASE is a valid result; not pooled with any other cell.
- **DISTRIBUTION**: below immutable floors (5 episodes < 20; fold decisions max 22 < 100); additionally the plan section 6 stricter default applies: no short authority on SPY and no evidenced forced-counterparty long mechanism, so DISTRIBUTION defaults FLAT regardless.
- **DOWNTREND**: below immutable floors (11 episodes < 20; fold decisions 26/32/141/7, three folds < 100). Long/flat only: there is no long-side thesis in a markdown phase; short books are forbidden (DOWN_SHORT_BTC class / no SPY short authority) and risk-off-exit books are the SPARSE_RISK_OFF baseline class and DOWN_FLAT_RISKOFF specialist class, both forbidden as candidates.
- **TRANSITION_UNKNOWN**: uncertainty state maps to FLAT by construction (plan section 5).

### Ancestry self-check (plan section 7; A1 adjudicates)

- `relative_breadth_rotation`: rho NOT_MEASURED_WITH_REASON: shadow requires QQQ/SPY ratio; QQQ is not in this cell (single-asset snapshot); no candidate signal series exists in this lane to correlate.
- `vol_state_bear_trap_books`: rho NOT_MEASURED_WITH_REASON: no frozen shadow series accessible to lanes; no candidate exists. Class distance: the frozen phase rule uses SMA level/slope only - no volatility conditioning anywhere in the rule or in any proposal.
- `filing_event_amendment_cadence`: rho NOT_MEASURED_WITH_REASON: data-dead class; filing events are absent from the cell's data; no candidate exists.
- `dividend_transition_books`: MEASURED (cell-constructed proxy): ex-date window dummy reconstructed from the 46 measured adjustment steps; rho(quarter-opex dummy, ex-div dummy) = +0.559 > 0.20, so any quarter-anchored calendar book would inherit the dead class's information and be ancestry-vetoed. Additionally the label input itself (adjusted_close) structurally contains ZERO dividend steps, so the dead class's signal is absent from this lane's own pipeline.

Measured calendar-class cohesion rho (dates-only, pre-PnL): month-settle↔quarter-opex -0.141, month-settle↔ex-div -0.142, quarter-opex↔ex-div +0.559.

§7.1 check: no RSM-V1 specialist, V2 arm, always-on MR/trend, or phase-gated variant of these was proposed or renamed. The lane's negative is a mechanism-foreclosure result, not a PnL observation: no returns path exists in lane code.

