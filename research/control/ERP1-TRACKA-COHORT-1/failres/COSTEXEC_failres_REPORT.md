# COSTEXEC_failres_REPORT — cost/execution decomposition (Phase A, cost reading)

Cycle: ERP1-TRACKA-COHORT-1 · Lane: failres-cost · Role: COST/EXECUTION
Base: 3b1c29fa (failres-attrib final commit; its artifacts are inputs, read-only)
Date: 2026-09-26 · Python: .venv 3.12.14 · Seed (sample verification): 20260926

**Labels (every table/number in this report):**
`DIAGNOSTIC_OUTCOME_EXPOSED · SINGLE_SOURCE_PANEL · FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK · PAPER_TIER · FAILURE_ROOT_CAUSE_RESEARCH`
Nothing here is promotable evidence regardless of result. Audit and
decomposition only — no strategy proposal, no tuning, no shadow contact.

**Honest cost sentence (program wording law):** every fill is a taker fill
at the opposite quote plus the fill bar's own measured per-bar spread x k
(one spread crossing per side); commission and slippage-beyond-spread are
`DECLARED_UNMEASURED`, stress-covered by k ∈ {1.5, 2.0}. The strategy PAYS
the spread. Cost decomposition = the SAME book re-run at k=0.0 (the engine
state machine is price-independent, so the trade schedule is identical);
gross := net(k=0), cost := net(k=1.0) − net(k=0).

---

## 1. Per-fold gross vs cost vs net — R-DAEMON, k=1.0 primary

`DIAGNOSTIC_OUTCOME_EXPOSED · SINGLE_SOURCE_PANEL · FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK · PAPER_TIER · FAILURE_ROOT_CAUSE_RESEARCH`

Sums re-derived from the per-trade attribution rows and cross-checked
against the attribution agg (k-decay B.10 k=1.0 and reconciliation
per-fold nets; max |residual| 0.00 — see tests). Fold = falsifier
FOLD_TABLE, keyed by ENTRY ts (imported, never redefined).

### EURUSD (fold rows 976 RT; gross +1025.1 / cost −634.7 / net +390.4)

| Fold | RT | gross (k=0) | cost (k1−k0) | net (k=1) | mean cost/RT | verdict (losing folds) |
|---|---|---|---|---|---|---|
| F1 | 164 | −94.8 | −94.0 | −188.8 | 0.5732 | **GROSS_NEGATIVE** (borderline, see below) |
| F2 | 166 | −769.1 | −115.3 | −884.4 | 0.6946 | **GROSS_NEGATIVE** |
| F3 | 164 | +1181.1 | −131.3 | +1049.8 | 0.8006 | — (winning) |
| F4 | 166 | +428.3 | −80.0 | +348.3 | 0.4819 | — (winning) |
| F5 | 159 | −113.0 | −78.5 | −191.5 | 0.4937 | **GROSS_NEGATIVE** |
| F6 | 157 | +392.6 | −135.6 | +257.0 | 0.8637 | — (winning) |

Verdict arithmetic (loss = −net; shares of the loss):
- F1: −188.8 = −94.8 (gross) + −94.0 (cost) → gross share 0.5021, cost
  share 0.4979. Mechanical label GROSS_NEGATIVE, but the split is 50.2/49.8
  — a 0.4 pp margin inside the row-rounding noise; treat F1 as an even
  split (MIXED-equivalent), not a clean gross story.
- F2: −884.4 = −769.1 + −115.3 → gross share 0.870, cost share 0.130.
  GROSS_NEGATIVE by a wide margin.
- F5: −191.5 = −113.0 + −78.5 → gross share 0.590, cost share 0.410.
  GROSS_NEGATIVE; cost is a material minority contributor.

k-decay restated from the attribution agg (B.10), EURUSD R-DAEMON net at
k=1.0/1.5/2.0: F1 −188.8/−235.8/−282.8 · F2 −884.4/−942.05/−999.7 ·
F3 +1049.8/+984.15/+918.5 · F4 +348.3/+308.3/+268.3 ·
F5 −191.5/−230.75/−270.0 · F6 +257.0/+189.2/+121.4. No EURUSD fold changes
net sign anywhere on the k grid.

### GBPUSD (fold rows 973 RT; gross −6.8 / cost −1622.3 / net −1629.1)

| Fold | RT | gross (k=0) | cost (k1−k0) | net (k=1) | mean cost/RT | verdict (losing folds) |
|---|---|---|---|---|---|---|
| F1 | 156 | +106.5 | −228.0 | −121.5 | 1.4615 | COST_DOMINATED (outside the designated losing set; cost share 1.877) |
| F2 | 172 | +409.9 | −298.7 | +111.2 | 1.7366 | — (winning at k=1; flips under stress, see below) |
| F3 | 160 | −921.1 | −351.6 | −1272.7 | 2.1975 | **GROSS_NEGATIVE** |
| F4 | 159 | +1057.7 | −267.9 | +789.8 | 1.6849 | — (winning) |
| F5 | 165 | −157.1 | −250.0 | −407.1 | 1.5152 | **COST_DOMINATED** |
| F6 | 161 | −502.7 | −226.1 | −728.8 | 1.4043 | **GROSS_NEGATIVE** |

Verdict arithmetic:
- F3: −1272.7 = −921.1 + −351.6 → gross share 0.724, cost share 0.276.
  GROSS_NEGATIVE.
- F5: −407.1 = −157.1 + −250.0 → cost share 0.614, gross share 0.386.
  COST_DOMINATED (cost > 50% of the loss).
- F6: −728.8 = −502.7 + −226.1 → gross share 0.690, cost share 0.310.
  GROSS_NEGATIVE.
- F1 (context, not in the dispatch's losing list): gross is POSITIVE
  (+106.5) and cost (−228.0) is 187.7% of the loss — the only fold on
  either pair whose net sign would flip at zero cost (see §6).

k-decay, GBPUSD R-DAEMON net at k=1.0/1.5/2.0: F1 −121.5/−235.5/−349.5 ·
F2 +111.2/−38.15/−187.5 · F3 −1272.7/−1448.5/−1624.3 ·
F4 +789.8/+655.85/+521.9 · F5 −407.1/−532.1/−657.1 ·
F6 −728.8/−841.85/−954.9. GBPUSD F2 flips sign already at k=1.5; every
GBPUSD losing fold deepens monotonically with stress.

---

## 2. Spread-at-fill regime — did losing folds fill at wider spreads?

`DIAGNOSTIC_OUTCOME_EXPOSED · SINGLE_SOURCE_PANEL · FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK · PAPER_TIER · FAILURE_ROOT_CAUSE_RESEARCH`

Entry-bar spread (pips) for R-DAEMON trades actually taken; "ratio" is the
per-trade entry spread divided by the SAME DAY's spread p50 (daily table);
panel p50 context from the committed census overall_open: EURUSD 0.3,
GBPUSD 0.8.

### EURUSD per fold

| Fold | n | p25 | p50 | p75 | p99 | median ratio to day p50 | share filled above day p50 |
|---|---|---|---|---|---|---|---|
| F1 | 164 | 0.2 | 0.3 | 0.3 | 0.50 | 1.00 | 0.244 |
| **F2** | 166 | 0.2 | **0.3** | 0.4 | **0.77** | **1.00** | 0.265 |
| F3 | 164 | 0.3 | 0.4 | 0.5 | 0.87 | 1.00 | 0.317 |
| F4 | 166 | 0.2 | 0.2 | 0.3 | 0.74 | 1.00 | 0.265 |
| F5 | 159 | 0.1 | 0.2 | 0.3 | 0.74 | 1.00 | 0.289 |
| F6 | 157 | 0.2 | 0.4 | 0.5 | 1.34 | 1.00 | 0.395 |

**F2 finding (war/energy weeks 2021-11..2022-08): NO adverse spread
timing.** F2's entry-fill spread p50 is 0.3 pips — exactly the panel p50 —
and its p99 is 0.77 pips (99% of F2 fills at or below 0.77 pips). The
median F2 fill lands at its own day's p50 (ratio 1.00) and only 26.5% of
F2 fills are above their day's p50. F2's mean cost per RT (0.6946) is only
+0.04 pips above its panel mean (0.6503). F2's −884.4 loss is a gross-side
fact (−769.1 at k=0), not a spread-timing fact. Notably the WINNING folds
F3/F6 filled at WIDER p50 (0.4) than the losing F1/F2 (0.3).

### GBPUSD per fold

| Fold | n | p25 | p50 | p75 | p99 | median ratio to day p50 | share filled above day p50 |
|---|---|---|---|---|---|---|---|
| F1 | 156 | 0.6 | 0.7 | 0.8 | 1.28 | 1.00 | 0.321 |
| F2 | 172 | 0.7 | 0.8 | 1.0 | 1.60 | 0.98 | 0.326 |
| **F3** | 160 | 0.8 | **1.05** | 1.3 | 2.29 | **0.95** | 0.313 |
| F4 | 159 | 0.7 | 0.8 | 0.9 | 3.28 | 1.00 | 0.296 |
| **F5** | 165 | 0.6 | **0.7** | 0.9 | 1.65 | 1.00 | 0.388 |
| **F6** | 161 | 0.5 | **0.7** | 0.8 | 1.50 | 1.00 | 0.416 |

GBPUSD overall: fills sit at the panel book (p50 0.7–1.05 across folds vs
census 0.8); losing folds are NOT systematically wider — F5/F6 filled at
p50 0.7 (NARROWER than panel), and F3's wider 1.05 comes with a
ratio-to-day of 0.95, i.e. F3's whole daily book was wider (2022-09..2023-06
of the GBPUSD book), not the fill timing. Across all 12 folds of both
pairs the median ratio-to-day is 0.95–1.00 and most fills are at or below
their day's median.

Per entry-hour bucket (both pairs, fold rows): EURUSD london_07_12 p50 0.3
(n=519), ny_13_18 0.3 (n=442), asia_00_06 0.3 (n=15, ratio 1.33);
GBPUSD london 0.8 (n=556), ny 0.8 (n=405), asia 0.95 (n=12, ratio 1.18).
No bucket shows an adverse-fill signature; asia buckets are tiny-n.

---

## 3. Independent sample verification (50 trades/pair, seed 20260926)

`DIAGNOSTIC_OUTCOME_EXPOSED · SINGLE_SOURCE_PANEL · FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK · PAPER_TIER · FAILURE_ROOT_CAUSE_RESEARCH`

Method: `random.Random(20260926).sample` over the sorted R-DAEMON
attribution rows; each sampled trade's fills recomputed from the parquet
byte-copy (sha256-pinned to the attribution provenance) plus the committed
charging law: entry at b_o + k·s_o / a_o − k·s_o; exits at bar-open
effective prices, except force-flat exits which settle at the CLOSE of
the day-close bar (SignalPlane semantics: s := a − b recomputed from the
quote columns; day-close = last tradable bar, hour ≤ 19). gross := k=0
pnl; cost := k=1 pnl − k=0 pnl.

| Pair | n | max abs deviation | Tolerance | Verdict |
|---|---|---|---|---|
| EURUSD | 50 | 3.0e−12 pips | 0.01 | **PASS** |
| GBPUSD | 50 | 2.3e−12 pips | 0.01 | **PASS** |

The attribution tables reconcile EXACTLY with an independent recompute —
no FINDING against the attribution lane.

Incident (disclosed): the FIRST recompute attempt reported DEVIATION up to
17.9 pips (EURUSD) / 14.5 pips (GBPUSD). Root cause was in THIS lane's
recompute, not in the attribution artifacts: it read the parquet's stored
s_open/s_close columns (which differ from a−b by ~0.1–0.2 pips) and
treated the calendar-last bar as the day-close bar, whereas the committed
SignalPlane recomputes spreads as a−b and marks the last TRADABLE bar
(hour ≤ 19) as day-close. After matching SignalPlane semantics the
deviation collapsed to float noise. No artifact of the attribution lane
was edited.

---

## 4. F-5-style ceiling arithmetic — any future intraday taker identity, measured book

`DIAGNOSTIC_OUTCOME_EXPOSED · SINGLE_SOURCE_PANEL · FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK · PAPER_TIER · FAILURE_ROOT_CAUSE_RESEARCH`

Source: committed census session spread curves (`census_{pair}.json`,
spread_pips.by_session_open — CONDITIONAL spreads, per program law, never
the global p50). A round trip = two spread crossings (entry + exit);
stress = ×2.0 on every crossing. Non-fragility line = the viability
council's frozen precedent: a declared band must clear ~2× the STRESSED
round trip.

### EURUSD (crossing p50 / RT base k=1.0 / RT ×2.0 stress / non-fragile line = 2× stress)

| Census bucket | crossing p50 | RT base | RT stress | non-fragile line |
|---|---|---|---|---|
| asia_00_07 | 0.3 | 0.6 | 1.2 | 2.4 |
| london_07_12 | 0.3 | 0.6 | 1.2 | 2.4 |
| ny_overlap_12_16 | 0.3 | 0.6 | 1.2 | 2.4 |
| ny_late_16_21 (day-close exit book) | 0.3 | 0.6 | 1.2 | 2.4 |
| late_22_24 (break) | 0.6 | 1.2 | 2.4 | 4.8 |
| rollover_21_22 (break) | 0.9 | 1.8 | 3.6 | 7.2 |
| friday_20_23_open (break) | 0.4 | 0.8 | 1.6 | 3.2 |
| sunday_open_21_22 (break) | 3.0 | 6.0 | 12.0 | 24.0 |

Cohort-law mixed case (session entry at best regular-session p50 +
force-flat exit at the day-close ny_late_16_21 p50): **RT 0.6 base / 1.2
stressed; non-fragile line 2.4 pips per round trip.**

### GBPUSD

| Census bucket | crossing p50 | RT base | RT stress | non-fragile line |
|---|---|---|---|---|
| london_07_12 / ny buckets | 0.8 | 1.6 | 3.2 | 6.4 |
| late_22_24 (break) | 1.4 | 2.8 | 5.6 | 11.2 |
| rollover_21_22 (break) | 2.1 | 4.2 | 8.4 | 16.8 |
| friday_20_23_open (break) | 1.0 | 2.0 | 4.0 | 8.0 |
| sunday_open_21_22 (break) | 7.1 | 14.2 | 28.4 | 56.8 |

Cohort-law mixed case GBPUSD: RT 1.6 base / 3.2 stressed; line 6.4 pips.

Stated per program law: **a candidate must declare a gross premium per
round trip above 0.6 pips at base / 2.4 pips at ×2.0 stress to be
non-fragile on EURUSD at the regular-session book (1.6 / 6.4 on GBPUSD);
identities whose fills can land in the break buckets face 1.8–6.0 base
(7.2–24.0 line) on EURUSD and 2.0–14.2 base (8.0–56.8 line) on GBPUSD.**

Cross-pair placement (program floor context, VIABILITY_cohort3 §A):
the council's measured floor pairs AUDUSD/USDCAD carry ×2.0-stressed RT of
3.6/4.4 pips and a ~7–9-pip intraday non-fragility line. EURUSD's
stressed in-session RT (1.2) sits ~3× BELOW those pairs — a 0.3-pip book —
so its non-fragility line (2.4 pips/RT) is the lowest in the program's
measured set; GBPUSD (3.2) sits at AUDUSD's level. Caveats, per the F-5
law: these are p50-conditional OPTIMISTIC bounds (the executor charges the
fill bar's own spread unconditionally — selecting tight minutes does not
lower the charged book); commission and slippage-beyond-spread are
DECLARED_UNMEASURED, stress-covered; fill quality is unmeasurable on M1
bid/ask. The R-DAEMON's realized mean cost per RT (EURUSD 0.6503, GBPUSD
1.6673 over fold rows) confirms the book actually pays ≈ the conditional
p50 mixed RT.

---

## 5. Exit-type × cost interaction — FORCE_FLAT vs TARGET_EXIT pools

`DIAGNOSTIC_OUTCOME_EXPOSED · SINGLE_SOURCE_PANEL · FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK · PAPER_TIER · FAILURE_ROOT_CAUSE_RESEARCH`

Mean cost per RT (pips, k=1.0). REVERSAL pools are EMPTY in every fold
(R-DAEMON never reverses through a bar-open exit; 0 RT both pairs).

| Pair | fold | FORCE_FLAT n | FF mean cost/RT | TARGET_EXIT n | TE mean cost/RT |
|---|---|---|---|---|---|
| EURUSD | F1 | 121 | 0.5719 | 43 | 0.5767 |
| EURUSD | F2 | 128 | 0.6945 | 38 | 0.6947 |
| EURUSD | F3 | 120 | 0.8133 | 44 | 0.7659 |
| EURUSD | F4 | 129 | 0.4667 | 37 | 0.5351 |
| EURUSD | F5 | 135 | 0.4830 | 24 | 0.5542 |
| EURUSD | F6 | 133 | 0.8729 | 24 | 0.8125 |
| GBPUSD | F1 | 121 | 1.4554 | 35 | 1.4829 |
| GBPUSD | F2 | 131 | 1.7534 | 41 | 1.6829 |
| GBPUSD | F3 | 134 | 2.2157 | 26 | 2.1038 |
| GBPUSD | F4 | 119 | 1.6815 | 40 | 1.6950 |
| GBPUSD | F5 | 129 | 1.5426 | 36 | 1.4167 |
| GBPUSD | F6 | 131 | 1.4160 | 30 | 1.3533 |

Full-panel fold rows: EURUSD FF 0.6491 vs TE 0.6548 (Δ −0.006);
GBPUSD FF 1.6827 vs TE 1.6106 (Δ +0.072). **The day-close force-flat does
NOT systematically pay wider close spreads**: the 19:00 day-close bar sits
in the ny_late_16_21 census bucket whose conditional p50 (0.3 EURUSD /
0.8 GBPUSD) equals the session book, and per-fold FF−TE differences are
±0.09 pips with mixed signs.

---

## 6. Facts-only reading (no strategy proposals)

`DIAGNOSTIC_OUTCOME_EXPOSED · SINGLE_SOURCE_PANEL · FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK · PAPER_TIER · FAILURE_ROOT_CAUSE_RESEARCH`

1. **Cost story vs gross story.** Of the six designated losing folds only
   ONE is cost-dominated: GBPUSD F5 (cost 61.4% of the loss). EURUSD
   F1/F2/F5 and GBPUSD F3/F6 are gross-negative (gross side 50.2%–87.0%
   of the loss; EURUSD F1 is a borderline 50.2/49.8 split).
2. **Zero-cost sign test (k=0 gross per fold, verified by summation).**
   EURUSD: no fold flips — F1/F2/F5 are already negative before cost
   (−94.8/−769.1/−113.0) and F3/F4/F6 stay positive. GBPUSD: F1 is the
   only fold whose net sign flips at zero cost (+106.5 gross → −121.5
   net); F2 stays positive at k=1.0 but flips under ×1.5 stress (agg
   k-decay −38.15); F3/F5/F6 are negative before cost.
3. **Spread-at-fill is exonerated.** No losing fold filled at
   systematically wider spreads than its own day's book (median
   ratio-to-day 0.95–1.00 in all 12 folds) or than the panel p50
   (EURUSD F2 exactly 0.3; F5 0.2; GBPUSD F5/F6 0.7). Where a losing
   fold's book was wider (GBPUSD F3), the WIDER book is the whole day's
   condition, and the fold still loses 72% of its loss on the gross side.
4. **EURUSD aggregate cost reading.** Over the 2021–2025 fold rows the
   R-DAEMON is gross-POSITIVE (+1025.1 pips) and cost takes 61.9% of it
   (−634.7 → +390.4): on EURUSD the failure is a thin-premium problem —
   mean gross ≈ +1.05 pips/RT against a 0.6-pip/RT base book (2.4-pip
   non-fragile line) — not a gross-earning problem. 2026 (outside the
   folds) contributes +421.8 pips net (86 RT), which is where the full
   panel's +812.2 comes from.
5. **GBPUSD aggregate cost reading.** Over the fold rows gross is
   essentially ZERO (−6.8 pips over 973 RT) and the entire −1629.1 net is
   the −1622.3 cost: at the measured GBPUSD book (1.67 pips/RT realized)
   the book's gross never clears the toll in aggregate.
6. **Cost-survivability implication for any thin-premium intraday taker
   identity on EURUSD at the measured book** (facts, not proposals): the
   base toll is ~0.6 pips/RT in-session (1.2 stressed; 2.4 non-fragile
   line; 1.8–6.0 base and 7.2–24.0 line if fills can land in break
   buckets), and realized books confirm ≈ p50 conditional. An identity
   whose gross premium per RT is O(1 pip) — like R-DAEMON's +1.05 —
   survives the base toll only marginally and sits BELOW the council's
   non-fragility line at stress; three of its six EURUSD folds are
   gross-negative before cost, so cost is not the root cause there, but
   the same arithmetic that convicts R-DAEMON's thin premium defines the
   ceiling every future intraday identity on this book must clear.

---

## 7. Artifacts, provenance, limitations

- Machine-readable: `failres_costexec_agg.json` (schema
  `failres_costexec_agg@1`, T1–T6 per pair incl. per-sample recompute
  details).
- Provenance: `failres_costexec_PROVENANCE.json` (input sha256s, base,
  lock verdicts, seed).
- Tests: `tests/test_failres_costexec.py` — 6 passed (summation
  identities, verdict arithmetic, 50-trade sample check; absolute venv
  python 3.12.14).
- Limitations carried from the attribution lane: SINGLE_SOURCE_PANEL
  (one M1 corpus per pair); FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK
  (per-fill spread state inside the bar is unmeasured — the executor
  charges the bar's own spread; commission/slippage-beyond-spread
  DECLARED_UNMEASURED, stress-covered); DIAGNOSTIC_OUTCOME_EXPOSED (fold
  surfaces are the family's dev surfaces); correlation != causation; no
  event overlay performed in this lane. The census ceiling numbers are
  p50-conditional optimistic bounds by construction.
