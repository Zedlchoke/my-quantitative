# PORTFOLIO_POLICY_ARCHITECTURE — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (pre-GO draft)

One deciding policy over 12 asset columns × N admitted sub-strategies.
0, 1, … N legs per asset — the count is an OUTPUT of frozen admission
conditions and evidence, never a target. Draft status: architecture only;
no leg, no PnL, no registration yet.

## 0. What this policy is — and is not (changed-axis statement, amended 2026-09-29)

**IS:** a portfolio-CONSTRUCTION and TIMING mechanism. Its claimed payer is
diversification, risk budgeting, and the timing of legs using only
pre-trade-available information: combining imperfectly-correlated legs
(many with disclosed KNOWN-NEGATIVE individual history, per the owner's
diagnostic amendment) under exposure caps, netting conflicts, and paying
state changes only inside a frozen cost budget, such that portfolio net
PnL rises AND drawdown falls versus running the same legs under naive
allocation — measured on folds not used to select the policy, after
counting missed profitable trades and ALL switching costs.

**IS NOT:** an information mechanism. The policy does not predict which leg
will work next via market state (the dead router class: JEV-V2, RSM-V1,
PSV1, PR12A — four terminals). It contains NO regime-prediction layer, NO
macro-state engine, NO LLM labels, NO vol-percentile representation (P-29
rho law). Eligibility conditions are RISK/STATISTICS-driven only (§2).

| Dead ancestor | what killed it | how this design differs (or inherits) |
|---|---|---|
| JEV-REGIME-ROUTER-V2 | regime labels add no value | no labels; allocation only |
| REGIME-STRATEGY-MAPPING-V1 | no regime→strategy increment | no regime→family map exists here |
| PHASE-STRATEGY-V1 | phase gating no value | no phase/state variable at all |
| PORTFOLIO-ROUTER-12ASSETS | states too thin + representation rho | no state engine; weekly eligibility from leg's OWN running statistics |
| REGIME-GATED-COMBO-V1 (pending a/b) | gating dead legs — exposed negative reading | **owner has explicitly authorized the diagnostic reopening** (amendment 2026-09-29): dead-history legs enter as labeled diagnostic candidates; the increment must survive missed-profit + full switching-cost accounting on untouched folds — the honest prior stays negative and this row is the one A7 will scrutinize hardest |
| BTC-COMBO6-SCORED-V1 | fixed 6-leg TA combo, no increment, legs dead | legs now admitted by implementability with labels (not owner-pinned); count variable 0..N; allocation risk-budgeted with netting + cost-budget + switching economics first-class; acceptance AND-semantics (PnL AND drawdown) |

The per-leg diagnostic question (owner's words): can a policy using only
information available BEFORE the trade choose the right ON/OFF moments,
after counting missed profitable trades and every state-switching cost?
Legs whose answer is NO are disabled by their own frozen degradation bars
— the policy cannot rescue them, only stop paying for them.

## 1. Layer map

```
L1  LEG POOL      admitted sub-strategies (Stage-A survivors), each with
                  frozen identity + own falsifier + causal control
L2  ELIGIBILITY   per-leg ON/OFF/PROBATION from mechanical, PIT-computable
                  statistics (§2)
L3  TARGETS       per-leg desired signed exposure in risk units (§3)
L4  NETTING       per-asset conflict resolution → ONE net position/asset (§4)
L5  RISK BUDGET   asset/cluster/portfolio caps → final sizes (§5)
L6  EXECUTION     Friday-20:00-UTC clock, next-bar-open fills, cost guard (§6)
L7  STANDING OUT  kill-switches + abstain rules (§7)
```

## 2. L2 — eligibility (when a leg may be ON)

Frozen, mechanical, computed from data available at decision time:

- E1 floors: rolling decision-count ≥3/26w (else `NOT_RUN_THIN` FLAT row).
- E2 degradation: leg's TRAIN-admission statistic (deflated, cost-stressed)
  recomputed on a trailing window; drop below its frozen admission bar →
  PROBATION (half size) for one fold, then OFF. The bar is set on TRAIN
  only; the trailing statistic is walk-forward causal.
- E3 staleness: any PIT input older than its frozen max-age → OFF
  (fail-closed, never last-known-value).
- E4 cost budget: leg's trailing cost-bill share of portfolio cost budget
  exceeds its frozen cap → OFF until budget resets (monthly).
- E5 no look-inside: eligibility NEVER conditions on the leg's own or the
  portfolio's realized PnL inside the current fold (no PnL-feedback sizing;
  drawdown switches live only at L7 typed thresholds).

Explicitly forbidden in L2: regime variables, macro percentiles, symbol
swaps of dead gates, anything claiming information about future returns.

## 3. L3 — direction and per-leg size

- Direction: the leg's own frozen rule (±1 or 0).
- Base unit: vol-targeted — 1 unit = target risk (e.g. 10 bps equity/week)
  divided by leg's trailing realized vol (52w, computed causally).
- Per-leg cap: 0.375% equity risk per decision (0.25–0.5% preregistered
  band, frozen at Stage-B); no intra-fold re-sizing.

## 4. L4 — conflict handling (same asset, disagreeing legs)

- Legs on one asset are risk-weight VOTERS: net target = Σ (sign_i ×
  risk-weight_i) truncated to ±1. Partial agreement ⇒ reduced net size
  (diversity of opinion = smaller bet, mechanically).
- A leg may not offset itself; hedges across assets are handled at L5 as
  cluster netting, never as paired trades (no pairing assumption — the
  owner's constraint; pairs emerge only as risk accounting).
- Ties (net = 0 with nonzero votes) ⇒ asset FLAT that decision; the tie and
  both votes are journaled (blocked-signal rows).

## 5. L5 — exposure limits (the risk spine)

- Per-asset gross ≤ 1.2% equity risk; per-asset one-way net ≤ 0.75%.
- Cluster caps (UNIFIED_STRATEGY Lớp 0 clusters, priors re-measured at
  registration from panels — prior ≠ measurement): USD-bloc ONE exposure
  ≤2.0% one-way; Commodity-FX ≤2.0%; Precious ≤1.5%; Energy ≤1.5%; NATGAS
  ≤1.0% tail-sized. Cluster assignment frozen at registration from
  measured correlation, not from the brainstorm text.
- Portfolio: total heat ≤6.0% equity risk; gross notional ≤250% of $100k;
  margin utilization ≤30%.
- Cross-cluster netting allowed only inside the frozen cluster map.

## 6. L6 — execution & cost guard

- Weekly clock Friday 20:00 UTC (the cadence with full measured spread
  authority); intraday legs declare their session clock from M1 with
  calendar-rebuilt session marks.
- Fills: next-bar-open at quoted side + half-spread; roll-window and
  Sunday-reopen fills priced at C2/C3 measured schedules.
- Cost guard: per-state-change cost estimate before committing a size
  change; if trailing cost budget exhausted → defer non-urgent changes to
  next decision (journaled as deferred).

## 7. L7 — when the policy stands outside (typed, no judgment)

- W1 no eligible legs (all OFF/PROBATION-exhausted) → portfolio FLAT.
- W2 account drawdown >10% from running peak → all FLAT, typed event,
  resume only after fold boundary + owner-visible report.
- W3 whipsaw: eligibility flipped >N times in M folds (N,M frozen at Stage-B
  from TRAIN switching ladder) → the flipping legs OFF for the fold.
- W4 unseen structure: any input outside frozen domain (new DST anomaly,
  missing calendar, unbound value) → fail-closed FLAT for that asset.
- W5 integrity: staleness/audit trip → everything FLAT until re-verified.
- ABSTAIN is a first-class state, journaled with reason codes.

## 8. Stage-B learning protocol (TRAIN-only, then freeze)

- Fit on expanding TRAIN folds: cluster map re-measured; caps assigned from
  TRAIN co-drawdown analysis; switching ladder fitted; ≤8 policy variants
  (frozen grid over {eligibility strictness × netting aggressiveness × cap
  tightness}) compared by deflated TRAIN objective (net PnL with DD
  penalty). ONE winner frozen; others die as ledger rows.
- Complementarity evidence required at freeze: pairwise leg-PnL correlation
  matrix, joint-loss episode census, order-overlap and common-exposure
  stats, turnover and state-switch cost, portfolio vs sum-of-legs DD.

## 9. Baseline / control battery (Stage-C)

B0 FLAT · B1 ALWAYS_ON (same legs, always eligible) · B2 EQUAL_WEIGHT
(same legs, equal risk) · B3 BEST_SINGLE (best TRAIN leg run alone) ·
B4 RANDOM-GATE (duty+turnover-matched eligibility randomization, ≥100
seeds, governs at ≤5% seeds-beat) · B5 CLOCK-GATE (eligibility by clock
only) · B6 INVERTED (eligibility complement) · B7 LAGGED (eligibility
delayed one fold) · B8 ORACLE-legs (perfect next-fold eligibility,
non-governing bound) · B9 INCUMBENT (FLAT-by-authority today; and the
exposed RGC reading as historical context only).

## 10. PASS bars — SUPERSEDED BY `policy/PASS_BARS_V2.md` (A1, 2026-09-29)

The binding bar authority is **`PASS_BARS_V2.md`** (Lane P, same dir):
owner AND-semantics on BOTH quantities (net PnL strictly higher AND maxDD
strictly lower), full P1–P8 with the formerly missing P6 (cost-stress
survival: P6a ×1.5 governing, P6b ×2.0 reporting, P6c COST_DOMINATED
disclosure trigger, P6d switching-cost p90 ladder), E-Laws 1–7, and the
closing governing/reporting matrix. The V1 text below is retained as
history; wherever it conflicts with V2 (notably: V1's OR-path in P1, its
looser P2/P3 wording, and its undefined P6 reference), **V2 governs**.
Baseline realization laws (B0–B9) are likewise refined by V2 §1.

### V1 text (historical, superseded where conflicting)

- P1 net PnL > max(B0..B3,B5..B7) AND maxDD ≤ that baseline's maxDD, or
  net PnL ≥ baseline AND maxDD strictly lower (the DD-reduction path).
- P2 beats B1 and B2 after ALL costs at stress ×1.0; survives ×1.5 (P6).
- P3 ≥95% of B4 seeds below the policy on the TRAIN-fitted objective.
- P4 value is not trade-count (B5) and not inversion (B6).
- P5 DSR>0 and PBO≤0.5 over the full discovery ledger.
- P7 fold-concentration ≤50% of net PnL in any single fold.
- P8 leave-one-leg: policy survives (P1 vs B1) with any single leg removed;
  else the increment is one leg wearing a portfolio costume.
Failure of any → typed close (`POLICY_NO_INCREMENTAL_VALUE`,
`POLICY_COST_DOMINATED`, `POLICY_ONE_LEG_CARRIER`, `NOT_RUN_*`).
