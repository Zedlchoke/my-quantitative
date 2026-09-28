# STATE BATTERY REPORT — I1b (PORTFOLIO-ROUTER-12ASSETS-100K-V1)

Pre-PnL state census + representation-rho battery. NO PnL computed.
Engine: `research/pr12a100k/state_engine.py`; battery: `research/pr12a100k/battery_state.py`.

- Command: `/Users/hoangminhlong/my-quantitative/.venv/bin/python /Users/hoangminhlong/my-quantitative/.worktrees/portfolio-router-12assets-100k-v1/integration/research/pr12a100k/battery_state.py`
- Total runtime: 62.1s; payload_sha256 `4a5f0fc581995d2b9083ee11bf4a1b91ee37f5ce6eaf5d8e542f79ac07ef587a` (deterministic core; re-runs must reproduce it)
- Calendar: 2021-01-08 .. 2026-06-26 (286 Fridays, 5-pair intersection, COVERAGE_NOTE)
- Fold grid: 9 folds -> `/Users/hoangminhlong/my-quantitative/.worktrees/portfolio-router-12assets-100k-v1/integration/research/pr12a100k/fold_grid.json`

## (a) State census and floors

| state | merged ep | raw runs | occupancy w | dwell mean/med w | F1 marg | F2 min (fold) marg | F3 min w marg | verdict |
|---|---|---|---|---|---|---|---|---|
| WAR_ENERGY | 10 | 12 | 55 | 6.0/4.0 | 10 (0) | 0 (-2) | 0 (-26) | NOT_RUN_THIN |
| RISK_STRESS | 7 | 7 | 24 | 3.4/3.0 | 7 (-3) | 0 (-2) | 0 (-26) | NOT_RUN_THIN |
| TIGHTENING | 2 | 3 | 59 | 31.0/31.0 | 2 (-8) | 0 (-2) | 0 (-26) | NOT_RUN_THIN |
| EASING | 3 | 3 | 30 | 10.0/12.0 | 3 (-7) | 0 (-2) | 0 (-26) | NOT_RUN_THIN |
| ABSTAIN | 5 | 13 | 118 | 26.4/19.0 | 5 (-5) | 0 (-2) | 0 (-26) | NOT_RUN_THIN |

Floors: F1 >= 10 merged episodes (total); F2 >= 2 raw episodes per 26-week fold; F3 >= 26 state-true weeks per fold. Any failure => NOT_RUN_THIN (permanent FLAT rows downstream).

Transitions matrix (effective, rows=from): see JSON `state_census.transitions_matrix_effective`.

## (b) Representation-rho battery (P-29 bar |rho| <= 0.20)

| comparison | rho | n | verdict |
|---|---|---|---|
| rho(v2_pct, eurusd_rv30_pct) [continuous] | 0.4828 | 271 | FAIL_RHO_BAR |
| rho(v2_STRESS, eurusd_rv_p80) [indicator] | 0.3034 | 271 | FAIL_RHO_BAR |
| rho(state_RISK_STRESS, eurusd_rv_p80) [indicator] | 0.2179 | 271 | FAIL_RHO_BAR |
| rho(V1 or state, tips_slope_z252) | n/a | 0 | NOT_RUN |

Per-symbol PSV1-style drawdown-hysteresis (−30%/−10%, 90-bar dwell):

| symbol | rho(state RISK_STRESS, RISK_OFF) | risk-off weeks | verdict |
|---|---|---|---|
| EURUSD | n/a | 0 | degenerate_constant_series |
| GBPUSD | n/a | 0 | degenerate_constant_series |
| USDJPY | n/a | 0 | degenerate_constant_series |
| USDCAD | n/a | 0 | degenerate_constant_series |
| AUDUSD | n/a | 0 | degenerate_constant_series |

P-20 distinctness: fraction of Fridays where V2_band differs from the ATR14-expansion indicator = 0.219 (n=274); V3 vs 20d-backwardation proxy SKIPPED_CIRCULAR (the proxy IS the Brent−WTI spread — documented, not measured).

## Interpretation notes / disclosures

- V2 consumes THURSDAY's VIX close at a Friday decision (design draft §3.4 uniform T−1 buffer + PIT_DOSSIER G-PIT-V2 application sentence); the bare available_at formula (d 16:15 ET) would also admit the Friday close — interpretation documented in state_engine.py, conservative direction (costs staleness, never lookahead).
- Percentile convention: weak/inclusive rank over the trailing 252 usable observations INCLUDING the current one (documented in state_engine.py); a constant series ranks p100 — an intentional property, irrelevant on real data.
- Episode merge is an episode-accounting convention only: it assigns shared episode_ids to same-state runs separated by <4 weekly observations and never rewrites weekly effective_state values (fabricating state during intervening weeks would violate the fail-closed ABSTAIN law).
- ABSTAIN bypasses min-dwell (effective immediately): holding a prior tradeable state through a stale week would be carrying state forward — forbidden by the frozen contract.
- ages_days['v2'] is business days (Mon–Fri, holidays counted — conservative); v1/v3 are calendar days; each var is reported in the unit its own staleness law uses.
- D1 tape observables (RV/ATR/drawdown) are sampled at the last COMPLETED D1 bar before each Friday 17:00 ET decision (= Thursday's bar) — same T−1 discipline as the engine.
- USDCAD/AUDUSD D1 close comes from the sparse ANC H1 panels (tradable-filtered; bid_h/bid_l are ancestor-convention minute-close aggregates per COVERAGE_NOTE) — closes exact, H/L not used.
- XAUUSD/XAGUSD/BRENT/WTI/NATGAS tapes are not in this data plane (L1 scope): the drawdown-hysteresis battery covers the 5 FX symbols only, disclosed.
- Floors are the dispatch-frozen weekly adaptation of the PSV1 triplet; F3 >= 26 state-true weeks per 26-week fold requires full-fold occupancy — structurally brutal by design; margins are reported, never relaxed post-hoc.
