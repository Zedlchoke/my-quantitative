# PLAN — REGIME-GATED-COMBO-V1 (conditional allocation over rescored legs)

- cycle_id: `REGIME-GATED-COMBO-V1`
- asset: `shared` (legs: EURUSD M1 Dukascopy, BTC 1m Binance, ETH 1h Binance)
- plan: `plans/PLAN_regime_gated_combo_v1.md` (this file; supersedes
  `plans/DRAFT_regime_gated_combo_v1.md` 22a5e32e which stays as evidence)
- registered: 2026-09-28 by owner instruction "đăng ký REGIME-GATED-COMBO-V1"
- diagnostic basis: `research/control/DAYTRADER-100-V1/DIAGNOSTIC_REGIME_COMBO_2026-09-28.md`
  (DIAGNOSTIC_OUTCOME_EXPOSED; the 4-proposition reading there is binding here)
- branch: `orca/regime-gated-combo-v1-integration`
- budget: **0/3 scored cells** (anchor combo + 2 neighbours; baselines/controls
  are re-evaluations, zero cells)
- GO phrase (registered, NOT consumed; typed only at this cycle's own gate, P-8):
  `GO REGIME GATED COMBO V1 SCORED EXECUTION`
- S1: `SEALED_UNTOUCHED`.

## 1. Mechanism (new identity)

Conditional allocation: a frozen gate table over four PIT-measurable external
state variables reallocates notional weekly across six S0-rescored legs
(individually dead — disclosed, never re-labeled by this cycle):
EURUSD PDHLSWEEPFX / ASIANRANGE / LONDONMOM; BTC WEEKEND / FUNDCONTRA;
ETH CORRBREAK. The mechanism claimed: regime state carries allocation
information beyond clock and beyond always-on diversification.

## 2. Gate variables (frozen at G3 BEFORE any combo evaluation)

- G1 funding-regime: z(30d) of BTC 8h funding (measured bytes, DTP fetch).
- G2 vol-regime: 30d percentile of BTC RV and EURUSD RV (from leg data itself).
- G3 trend-state: |BTC 120h return| / vol(120h).
- G4 corr-regime: 168h rolling corr ETH–BTC (the CORRBREAK observable).

Thresholds are MECHANICAL (median / tercile cuts of each variable's own
distribution on the warmup window 2020-09-01..2021-03-31 — computed WITHOUT
reference to any leg or combo outcome). Allocation table: frozen mapping
(state cell → weights over 6 legs; default equal-weight; gate inactive cells →
ALWAYS_ON behavior). Weekly reallocation only (Mondays 00:00 UTC), switching
costs charged per reallocation at the leg's frozen cost model (DT100 G3).

## 3. Anti-overfit constraints (the JEV price)

- Must beat ALL baselines or verdict is fail: ALWAYS_ON_6 equal-weight;
  random-gate (seed frozen); best-single-leg; clock-shadow gate (Q-7).
- Switching-cost budget: reallocation ≤ 1/week; each switch pays full RT costs
  on weight deltas.
- PBO ≥ 8 configs else NOT_RUN; sub-power = INCONCLUSIVE.
- Ancestry rho ≤ 0.20 (immovable) vs dead router observables: JEV V1/V2
  regime labels, phase-router states, BTC two-regime hysteresis.
- Folds: GĐ1 2021-04-01..2022-06-30 · GĐ2 2022-07-01..2023-09-30 · GĐ3
  2023-10-01..2024-12-31 · GĐ4 2025-01-01..2026-08-31 (FX legs use P1..P4
  same calendar, P4 ends 2026-09-23 — disclosed 23-day tail difference).
- Floors: combo net expectancy > 0 at ×1.0 AND ≥ 0 at ×1.5; PF ≥ 1.10 vs
  ALWAYS_ON_6's PF (relative bar); ≥ 3/4 folds beat ALWAYS_ON_6 per-fold;
  concentration ≤ 50%; no tuning after combo output is visible.

## 4. Neighbours (budget)

- N1: gate thresholds widened one tercile (fewer switches).
- N2: gate thresholds tightened one tercile (more switches).
- Never a grid; no third neighbour.

## 5. Preregistered terminal outcomes

- `REGIME_COMBO_NO_INCREMENTAL_VALUE` — fails any baseline or floors. This
  CLOSES the router/combo class over dead legs for the program (6th and final).
- `REGIME_COMBO_POSITIVE_VS_ALL_BASELINES` — opens ONE next step only:
  paper-forward on SHARED-PORTFOLIO-100K-V1 (forward-only; no historical
  claims). No S1 consumption without a separate owner gate.
- TECHABORT / BLOCKED rows per house law.

## 6. Execution order

G0 intake (this registration) → G1 leg-inheritance audit (verify the six legs'
frozen configs from DT100 arms.py byte-match) → G3 gate-table freeze (thresholds
from warmup-window distributions only) → implementation in worktree → fixtures
(golden allocation math, no-lookahead on gate variables, switching-cost
exactly-once, determinism) → exact-arm dry-run (non-vacuous, no PnL) → A7
prelaunch (two-key #1) → owner GO at gate (two-key #2) → ≤3 cells under heavy
lock → reproduction → terminal A7 → two-half close.

## 7. Honest prior (binding)

Five dead router precedents; four folds of evidence; six dead legs. Expected
outcome is NO_INCREMENTAL_VALUE. The cycle's value is measuring the question
closed. No survivor of this cycle may be described as an edge without the
baseline table showing it beat all four baselines after switching costs.
