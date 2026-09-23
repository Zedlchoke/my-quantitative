# REGIME-STRATEGY-MAPPING-V1 — DISCOVERY BACKTEST REPORT (terminal)

GO `GO REGIME STRATEGY MAPPING V1 DISCOVERY BACKTEST` (owner 2026-09-23,
token sha `47ee5e6f…`; owner additionally instructed the floor comparison —
frozen pre-outcome in `freezes/go_authority_and_floor_sensitivity_freeze.json`).
Runs under the machine-wide heavy lock. Reproduction **69/69 MATCH**
(byte for A1/A2/B; content-minus-extra for the remediated arms).
S1 `SEALED_UNTOUCHED`. Zero provider calls (cached V2 decisions only).
V2 artifacts byte-untouched (`0c277a94`, clean).

## Trial accounting (honest, all runs counted)

| Run | Cells | Class |
|---|---|---|
| Run 1 | 27 (21 primary + 6 sensitivity) | 15 valid (A1/A2/B ×3 kept; D/E superseded), 12 INVALID (C*/F* degenerate — INC-1 direction-dispatch bug) |
| Run 2 (remediation, final mechanism) | 18 (C, C_RELAXED, D, E, F, F_RELAXED ×3) | valid; D/E recomputed so the whole report uses ONE routing law (INC-1b deferral) |
| **Total observed** | **45** | multiple-testing disclosed; verdict reads run-2 C*/D/E/F* + run-1 A1/A2/B |

Four scored-launch TECHABORT attempts before run 1 completed (lock param,
module path, registry-stop dispatch) — zero outcome exposure, no partials
(disclosed in the incident log). Incident chain RSMV1-INC-1..1e in
`incidents/incident_run1.json` + commit log; run-1 artifacts preserved
byte-exact under `runtime/scored_run1_invalid/`.

## Base-tier (1.0x) results — net PnL, equity 100,000

### BTC_H1 (evaluable; buy-hold trend-exit ref −132)
| Arm | Net | 1.5x | Trades | Folds |
|---|---|---|---|---|
| **C REGIME_SPECIALIST_ROUTER (candidate, frozen floors)** | **−49,661** | −60,377 | 398 | 0 / −36,655 / −3,932 / −9,074 |
| C_RELAXED (floors 10/2/50) | −49,661 | −60,377 | 398 | identical — floors not binding on this cell |
| D SPARSE_JEV_RISK_OFF_VETO | −23,551 | −33,179 | 224 | −6,276 / −8,543 / −1,113 / −7,619 |
| A1 ALWAYS_ON_MR | −53,132 | −62,950 | 391 | all negative |
| A2 ALWAYS_ON_TREND | −91,535 | −96,320 | 1,386 | all negative |
| B ORIGINAL_V2_MAPPING | −88,140 | −93,415 | 978 | = V2 JEV_ONLY (equivalence <1e-6) |
| E DETERMINISTIC_PLUS_JEV_VETO | −65,185 | −72,650 | 401 | — |
| F matched null | NOT_RUN_CONTROL_MATCHING (fail-closed; Q-11 movement + tolerances never jointly satisfied) | | | |

### BTC_H4 (frozen floors: every regime THIN → C routes FLAT by law)
| Arm | Net | 1.5x | Trades |
|---|---|---|---|
| **C (frozen)** | 0 | 0 | 0 (NOT_RUN_THIN_REGIME ×4 regimes) |
| C_RELAXED | −4,997 | −6,751 | 31 (fold 4 only) |
| D | −12,921 | −20,760 | 157 |
| A1 / A2 / B / E | −53,901 / −89,499 / −85,274 / −56,968 | | |

### SPY_D1 (frozen floors: every regime THIN → C routes FLAT by law)
| Arm | Net | 1.5x | Trades |
|---|---|---|---|
| **C (frozen)** | 0 | 0 | 0 (NOT_RUN_THIN_REGIME ×4 regimes) |
| C_RELAXED | **+2,529** | **−803** | 33 (fold 4 only) |
| D | −21,134 | −38,055 | 241 |
| A1 / A2 / B / E | −924 / +19,813 / −51,623 / −18,561 | | |

SPY ALWAYS_ON_TREND +19,813 remains the V2 posterior BASELINE with
concentration 0.69 > 0.50 kill — never a candidate, never citable as edge.

## Candidate gates (frozen evaluation contract; base tier)

**BTC_H1 (the only evaluable cell under frozen floors):**
- G1 net-positive: **FAIL** (−49,661)
- G2 survives 1.5x: **FAIL** (−60,377)
- G3 beats better always-on: PASS (−49,661 > −53,132)
- G4 beats original V2 mapping: PASS (−49,661 > −88,140)
- G5 no single-fold dependency: **FAIL** (0 positive folds; sum−max = −13,006)
- G6 not merely trading less: **FAIL** (D −23,551 beats C; F invalid →
  F_INVALID_REST_ON_ABDE recorded, gate rests on D)
- G7 reproduction: PASS (69/69)
- G8 A7 terminal: this report's companion audit

**BTC_H4 / SPY under frozen floors:** NOT_RUN_THIN_REGIME (all regimes
below the preregistered sample floors; C is lawfully FLAT — not vacuous
evidence FOR anything, just no sample).

## The owner's floor question (frozen-vs-relaxed, both preregistered)

Relaxing the outer floors 20/3/100 → 10/2/50 changes eligibility only on
BTC_H4 (UPTREND, DOWNTREND) and SPY (UPTREND, DOWNTREND):
- **BTC_H1: zero effect** (ACC/UP/DOWN pass both; DIST fails both).
- **BTC_H4: FLAT → −4,997** — 31 trades, single fold, still net-negative.
- **SPY: FLAT → +2,529 at 1.0x** — but **dies at 1.5x (−803)**, is
  single-fold (fold 4 only), and does not beat the better always-on
  baseline (+19,813). This is the classic thin-sample mirage the stress
  tier exists to kill; it is reported, not promoted.

**Relaxing floors produces no validated value anywhere.** It only admits
thinner samples whose signs flip under cost stress.

## Mechanism findings (secondary, diagnostic value)

1. **The anti-churn turnover law works as a cost mechanism**: arm E (the
   V2 confirm design rerun under the churn law) improves on V2's CONFIRM
   arm by +16.6k (BTC_H1), +20.7k (BTC_H4), +13.8k (SPY): −65,185 / −56,968
   / −18,561 vs V2's −81,761 / −77,672 / −32,384. SPY D likewise improved
   +32k vs its fixed-point draft. The law reduces fee bleed exactly as
   designed — but cannot rescue routing that is net-negative before churn.
2. **Regime intelligence used sparsely beats using it fully** (on BTC):
   D (risk-off veto only) −23,551 beats C (full specialist routing)
   −49,661 on BTC_H1 — consistent with A2's attribution that the damage
   was in what Jev DID trade, not what it skipped.
3. On the one cell with adequate sample, the specialist library's inner
   selections (breakout-long in UPTREND, cascade-short in DOWNTREND,
   spring-long in ACCUMULATION) still lose after costs; the best Jev-aware
   arm anywhere is D and the best arm overall is a simple always-on.

## Verdict (frozen vocabulary)

Gates fail on the only evaluable cell (G1/G2/G5/G6); not all cells thin
(BTC_H1 evaluable), so not BLOCKED_THIN_REGIME_SAMPLE; cost/control
authority intact; reproduction MATCH.

# **`NO_REGIME_STRATEGY_INCREMENTAL_VALUE`**

Contamination ceiling applies regardless: this whole corpus is
outcome-observed; even a passing result could only have been
DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION. Nothing here is
live-ready or profitable; no shadow/promotion; no paper/live/orders.
The V2 terminal verdict `JEV_NO_INCREMENTAL_VALUE` is unchanged.

## Five-year-old summary

Đổi chiến lược theo "thời tiết" của Jev — kể cả với đội chuyên gia từng
regime và luật chống giật — vẫn thua bậc thang đơn giản nhất trên cell duy
nhất đủ dữ liệu để xét. Nới floor chỉ thêm mẫu mỏng: SPY ra thêm +2.5k
nhưng chết ngay khi phí x1.5. Luật chống giật THẬT tiết kiệm được tiền
(+16–33k mỗi cell) — nhưng chỉ khiến việc giao dịch theo Jev lỗ ít hơn,
không làm nó có lãi. Không đáng mở prospective cho hướng này.
