# STAGE-B ASSEMBLY — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (TRAIN-ONLY)

Stage-B portfolio assembly of the Stage-A survivor slate into ONE frozen
portfolio policy. Every number here is computed on the TRAIN side of the
frozen 8-fold expanding walk-forward (longest stream ends at fold 7's
train_end 2025-06-20; test folds start 2025-07-04; sealed tail 2026-01-02
untouched — partition proven in `tests/test_pc12a_stageB.py` and
`tests/test_pc12a_stageA_wave2.py`). All artifacts carry label
`TRAIN-ONLY`; this document is outcome-bearing TRAIN-side evidence, like
the wave-2 diagnostics.

Freeze artifact: `policy/POLICY_FROZEN.json`
(policy_digest `93077163796abddc237a227267161a48b6397c3fc339738f493965db45cbbbc`,
winner variant **V3**, deterministic byte-identical re-run).

Engine: `research/pc12a/run_stageb.py` (extends the wave-2 solo book
machinery: staged-fill discipline, FoldSnapshot prefix aggregates,
per-fold residual asserted ≤ 1e-6 on every symbol × fold).

## 1. Survivor set (reconciled from TRIAL_LEDGER.jsonl, 796 rows at entry)

62 legs reached Stage-A diagnostics − 43 COST_DOMINATED kills − 7
NO_ENTRIES_TRAIN = **12 survivors** (62−43−7 arithmetic exact; no
selection-priority cut needed; ≥3 → no BLOCKED_NO_SLATE). FLOOR_FAIL (14
A-MECH) and PARKED (9) legs never reached diagnostics and stay out.

| leg | symbol | family | config cluster | outcome_exposed_label | fold-7 TRAIN net USD | cost USD | trades |
|---|---|---|---|---|---|---|---|
| EURUSD-S009 | EURUSD | A-TREND | trend_daily | F0_INDIVIDUAL_REJECT | +975.7 | 382.8 | 21 |
| EURUSD-S013 | EURUSD | B-MEANREV | meanrev_daily | FAMILY_HISTORY_NEGATIVE | +2,431.4 | 656.9 | 133 |
| EURUSD-S046 | EURUSD | E-SESSION | calendar_daily | FAMILY_HISTORY_NEGATIVE | +312.7 | 279.1 | 51 |
| GBPUSD-S002 | GBPUSD | A-TREND | trend_intraday | FAMILY_HISTORY_NEGATIVE | +878.2 | 572.2 | 266 |
| GBPUSD-S017 | GBPUSD | B-MEANREV | meanrev_intraday | FAMILY_HISTORY_NEGATIVE | +24.2 | 15.2 | 6 |
| USDJPY-S002 | USDJPY | A-TREND | trend_multimonth | FAMILY_HISTORY_NEGATIVE | +82,363.0 | 3,042.0 | 20 |
| USDJPY-S003 | USDJPY | A-TREND | trend_multimonth | FAMILY_HISTORY_NEGATIVE | +217,608.0 | 2,090.9 | 1 |
| USDJPY-S014 | USDJPY | B-MEANREV | meanrev_daily | FAMILY_HISTORY_NEGATIVE | +91,712.1 | 14,377.9 | 144 |
| USDJPY-S023 | USDJPY | C-BREAKOUT | breakout_daily | FAMILY_HISTORY_NEGATIVE | +288,816.0 | 974.0 | 2 |
| USDJPY-S026 | USDJPY | C-BREAKOUT | breakout_intraday | FAMILY_HISTORY_NEGATIVE | +27,240.0 | 102,535.0 | 1,055 |
| VC2-LVNFAIL-EURUSD | EURUSD | VOLPROF-M1-LVNFAIL | volprof_vc2_lvnfail | CLASS_CANDIDATE_ANCESTRY_RHO_LABELLED | +113.1 | 29.8 | 20 |
| VC2-LVNFAIL-USDJPY | USDJPY | VOLPROF-M1-LVNFAIL | volprof_vc2_lvnfail | CLASS_CANDIDATE_ANCESTRY_RHO_LABELLED | +2,646.0 | 2,194.0 | 20 |

Per-leg fold-7 TRAIN nets are the ledger's A-DIAG MAIN rows (TRAIN-side,
lawful to see now). arm_config_digests per leg live in POLICY_FROZEN.json.

## 2. Cluster map (frozen from TRAIN co-movement only)

Rule (frozen before any variant ran): `|corr| >= 0.5` on the fold-7 TRAIN
pairwise weekly-equity correlations (`COMPLEMENTARITY_TRAIN.json`), union-
find over survivor pairs; otherwise singleton. Result: **10 clusters —
one 3-leg co-movement cluster + 9 singletons**:

- `CM:USDJPY-S002` = {USDJPY-S002, USDJPY-S003, USDJPY-S023}
  (pairwise TRAIN rho +0.6341 / +0.7800 / +0.8435; the JPY trend trio)
- singletons: EURUSD-S009, EURUSD-S013, EURUSD-S046, GBPUSD-S002,
  GBPUSD-S017, USDJPY-S014, USDJPY-S026, VC2-LVNFAIL-EURUSD,
  VC2-LVNFAIL-USDJPY

### P-20 pairwise rho among co-admitted legs (TRAIN, 232 weeks)

Top pairs by |rho| (full 66-pair evidence in POLICY_INPUTS.json):

| pair | rho | co-loss weeks |
|---|---|---|
| USDJPY-S002 \| USDJPY-S023 | +0.8435 | 51/232 |
| USDJPY-S003 \| USDJPY-S023 | +0.7800 | 60/232 |
| USDJPY-S002 \| USDJPY-S003 | +0.6341 | 47/232 |
| USDJPY-S014 \| VC2-LVNFAIL-EURUSD | +0.3165 | 3/232 |
| EURUSD-S046 \| USDJPY-S023 | +0.2496 | 17/232 |
| EURUSD-S046 \| USDJPY-S002 | +0.2261 | 14/232 |
| EURUSD-S046 \| USDJPY-S003 | +0.1884 | 17/232 |
| USDJPY-S003 \| USDJPY-S026 | +0.1811 | 43/232 |
| EURUSD-S009 \| VC2-LVNFAIL-EURUSD | −0.1704 | 3/232 |
| USDJPY-S002 \| USDJPY-S026 | +0.1691 | 37/232 |

Max |rho| outside the cluster trio: 0.3165 — the slate is genuinely
weakly correlated outside the JPY trend concentration (which the cluster
map + caps police).

## 3. L5 caps + L6 guard freeze (TRAIN evidence)

**Caps.** Architecture §5 unit-space starting points = per-asset one-way
net 1 lot (100,000 units; the registered skeleton cap). TRAIN-tightened
rule (frozen before variants): a multi-leg cluster whose max pairwise
TRAIN co-loss rate ≥ 15% of TRAIN weeks → per-asset net cap 50,000 units
on its asset + cluster net cap 50,000. Evidence: `CM:USDJPY-S002` max
co-loss 60/232 = 25.9% ≥ 15% (worst pair USDJPY-S003|USDJPY-S023) → tight
caps = USDJPY 50k, EURUSD/GBPUSD 100k. Cluster-combined vs sum-of-DDs
(solo TRAIN paths): combined $821,070 < sum $881,375 — modest within-
cluster diversification, consistent with tightening.

**Caps-axis honesty note:** the cap axis proved NON-BINDING on TRAIN.
All 12 legs vote in 0.1-lot units (`unit_base_units` 10,000), so the
per-asset net never exceeded the 50k tight cap (fold-end books: EURUSD
10k, GBPUSD 0, USDJPY 10k; zero BLOCKED_RISK_CAP events; V1≡V2 and
V3≡V4 byte-identical economics). The tight cap would bind only under
full 6-leg USDJPY agreement (60k), which never occurred on TRAIN. No
post-hoc re-tightening was performed — the grid is closed.

**L6 guard cap.** TRAIN switching-cost ladder: LADDER pass (base
eligibility, full netting, default caps, guard disabled), 3,394
state-change events, trailing-28d spend series p50 $1,770.51 / **p90
$2,836.97** → guard cap frozen at **$2,836.97 / 28d** (p90 of the ladder,
echoing the P6d p90 switching-cost convention). In the winner the guard
deferred 48 non-urgent changes (total state-change spend $115,341 over
TRAIN); risk-reducing closes always allowed (R1).

## 4. Variant grid (all 8 trained; frozen grid, no iteration beyond it)

Objective (frozen, PASS_BARS_V2 §4 obj semantics): weekly portfolio
equity over the fold-7 TRAIN prefix —
`obj = netPnL − W·SR0·σ_w − 1.0·maxDD`, with SR0 from the FULL ledger to
date. DSR inputs: N = 85 deduped arms (796 ledger rows; arms not rows),
N_eff = 28 clusters (27 (sleeve, cluster) families + 1 policy-variant
family), V = 0.024414 (population variance of 55 computable weekly
Sharpes of the 62 diag legs on the fold-7 TRAIN prefix), E[max] = 2.0448
→ **SR0 = 0.319497** (weekly, non-annualized).

| id | eligibility | netting | caps | objective USD | net PnL USD | maxDD USD | SR̂ (wk) | deflation USD | note |
|---|---|---|---|---|---|---|---|---|---|
| V3 | base | supermajority | default | **−1,054,702.2** | +138,256.2 | 129,550.1 | 0.0415 | 1,063,408.3 | **WINNER** |
| V4 | base | supermajority | tight | −1,054,702.2 | +138,256.2 | 129,550.1 | 0.0415 | 1,063,408.3 | ≡V3 (caps non-binding) |
| V1 | base | full | default | −1,055,788.9 | +137,081.5 | 129,550.1 | 0.0412 | 1,063,320.4 | |
| V2 | base | full | tight | −1,055,788.9 | +137,081.5 | 129,550.1 | 0.0412 | 1,063,320.4 | ≡V1 (caps non-binding) |
| V7 | e2strict | super | default | −1,371,711.4 | −31,373.9 | 233,036.9 | −0.0091 | 1,338,049 | |
| V8 | e2strict | super | tight | −1,371,711.4 | −31,373.9 | 233,036.9 | −0.0091 | 1,338,049 | ≡V7 |
| V5 | e2strict | full | default | −1,372,661.9 | −32,397.9 | 233,036.9 | −0.0093 | 1,337,468 | |
| V6 | e2strict | full | tight | −1,372,661.9 | −32,397.9 | 233,036.9 | −0.0093 | 1,337,468 | ≡V5 |

Blocked-signal census (winner V3): NETTED_TO_ZERO 228,
SUPERMAJORITY_BLOCK 4, BLOCKED_FLOOR (E1) 435, DEFERRED_COST_GUARD 48.
E2-strict variants: 1,316 E2_STAND_ASIDE events (11/12 legs gated off
after early-fold paper losses and never re-earned their way on) —
**E2-strict was value-destroying on TRAIN** (net −31.4k vs +138.3k, DD
233k vs 130k): the degradation bar stood the trend legs aside exactly
before their recovery. Honest result, recorded; the winner uses baseline
eligibility.

Winner selection tie-break (frozen): higher objective → higher net →
lower maxDD → variant id. V3 vs V4 tie on all quantities → V3 by id.
Determinism: the winner's full variant JSON re-run is **byte-identical**
(`VARIANT_V3_REPRO.json`).

## 5. Honest reading of the winner (mandated label)

The winner's TRAIN objective is **NEGATIVE** (−1.05M USD): the portfolio's
weekly Sharpe on TRAIN (SR̂ 0.0415; ≈0.30 annualized) is far below the
multiple-testing null SR0 0.3195 (≈2.30 annualized) implied by 28
effective trial families in the discovery ledger — the deflation term
($1.06M) dwarfs the raw TRAIN net PnL (+$138.3k). The slate's known-
negative history is priced exactly as designed: no TRAIN-side claim of
edge is being made. Per the dispatch's honest bar the winner is frozen
ANYWAY with the negative label; Stage-C closes the cycle on test evidence
under the PASS_BARS_V2 battery.

Decomposition of the winner's TRAIN book: USDJPY +$133,504 (the trend
trio + S014/S026/VC2 netted), EURUSD +$3,850, GBPUSD +$902; 1,585 net
entries, 3,292 fills. Expanding-prefix fold nets: f0 −31.6k, f1 +128.5k,
f2 +93.5k, f3 +102.2k, f4 +131.3k, f5 +170.8k, f6 +160.6k, f7 +138.3k
(prefix aggregates, not disjoint windows).

## 6. Engine semantics (disclosed)

- Ties (full netting) and supermajority blocks mean "asset FLAT this
  decision" and the flatten **EXECUTES** (architecture §4; risk-reducing,
  guard-exempt). This deviates from the dry-run engine's early-return,
  which left the book unchanged on ties (a no-PnL engine; never fired in
  solo diagnostics where ties are impossible).
- No eligible leg at a decision → no action (frozen run_dry law kept);
  blocked legs' standing desires persist (frozen law kept).
- E1 arms 26w after the SYMBOL engine's first decision (multi-leg
  semantic; wave-2 disclosure inherited).
- E2-strict (dead variants): fold-boundary recompute over trailing ≤2
  COMPLETED folds of the leg's paper (sum-of-legs) expectancy —
  prior-fold data only, never current-fold PnL (E5; GROUPING_PROPOSAL
  3.6; feature ids pass `FEATURES_BLACKLIST`, asserted in-engine and
  unit-tested).
- Supermajority agreeing share is computed on the RAW vote sum
  (|Σd|/Σ|d| ≥ 2/3); the ±1-lot truncation is sizing, not disagreement.
- Books: one virtual $100k sub-account per symbol (wave-2 book law);
  portfolio equity = 100k + Σ sub-account PnL; guard shared across the
  symbol engines (PIT-windowed spend list, campaign §8.1).
- Dry-run outputs remain leak-clean (RGC-INC-1): Stage-B PnL lives only
  in these TRAIN-ONLY artifacts.

## 7. Evidence index

- `diagnostics/stageb/POLICY_INPUTS.json` — survivors, cluster map + full
  66-pair evidence, caps + DD evidence, SR0 inputs, guard ladder, grid.
- `diagnostics/stageb/LADDER.json` — switching-cost ladder pass.
- `diagnostics/stageb/VARIANT_V1..V8.json` (+`VARIANT_V3_REPRO.json`) —
  per-variant folds, weekly equity, objectives, blocked histograms.
- `diagnostics/stageb/SELECTION.json` — ranking + tie-break.
- `policy/POLICY_FROZEN.json` — the freeze.
- `TRIAL_LEDGER.jsonl` rows `BSTG-W1-0797..0805` (8 B-VARIANT + 1
  B-FREEZE; ledger 805/1500, stop line 1400 respected).
- Tests: `tests/test_pc12a_stageB.py` (18 laws: partition, grid closure,
  blacklist, netting/caps/E2 units, objective + SR0 math, ladder
  percentile/PIT, engine determinism + caps on synthetic panels, ledger
  budget). Suite state at freeze: 18/18 pass; neighboring pc12a suites
  34/34 pass.
