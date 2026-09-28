# EVALUATION_PROTOCOL_DRAFT — PORTFOLIO-ROUTER-12ASSETS-100K-V1 (Lane L4, 2026-09-28)

**Status:** PRE-GO research design draft, companion to
`router/ROUTER_POLICY_DESIGN_DRAFT.md` (the "policy" whose falsification this
protocol defines). No cycle registered; no backtest run in this lane; all
1,200 corpus ideas remain HYPOTHESIS/NOT_RUN. Baseline-battery precedent:
`plans/DRAFT_regime_gated_combo_v1.md` §3 (the dispatch's primary fallback —
`plans/PLAN_daytrader_100_v1.md` contains no §baselines section) plus the
DAYTRADER-100-V1 ALWAYS_ON_6/ORACLE diagnostic
(`research/control/DAYTRADER-100-V1/DIAGNOSTIC_REGIME_COMBO_2026-09-28.md`).
Dead-ancestry citations: MAP 1278–1342 (JEV/RSM), 1429–1460 (ERP track-a),
292–327 (two-regime floors); LESSONS Q-5/Q-7/Q-11/P-20/P-24/P-27/P-28/P-29.

**Design philosophy:** falsification-first. The protocol is built so that the
most likely outcome — the router adding nothing over its baselines after
costs — is cheap, typed, and terminal. A negative terminal outcome is a
first-class close (REJECT is valid), exactly like ILLIQ-REG-V1's executed
negative bar (MAP 1399–1427).

---

## 1. Data window, warmup, and the calendar floor

- **Intersection window T:** the span over which ALL 12 symbol panels AND
  all three state series (V1 EFFR, V2 VIX, V3 Brent–WTI) are PIT-evidenced
  by L1/L3 artifacts. Energy panels are PUBLIC_UNEVIDENCED today
  (CENSUS_PROTOCOL §4), so T is plausibly bounded by the shortest energy or
  metals panel, not by the macro series (EFFR 2000s→, VIX 1990→, EIA spot
  1986/87→ — all longer than any plausible panel).
- **Warmup W = 52 weeks** (252-trading-day percentile lookbacks for V2/V3 +
  63-business-day V1 delta + sleeve warmups), consumed before fold 1; no
  decision, no entry during warmup.
- **Calendar floor (preregistered):** usable weeks U = T − W must host
  **≥ 6 outer test folds** (§2). If U < 6×27 weeks (≈ 3.2y of testable
  calendar), the program closes `NOT_RUN_INSUFFICIENT_CALENDAR` — folds are
  NOT shortened and warmup is NOT trimmed to manufacture fold count
  (the RSM thin-sample lesson applied to the fold grid itself).

## 2. Nested walk-forward fold scheme (calendar-based)

```text
Decision clock: weekly (Friday 17:00 ET state decision, Monday execution).
Outer test folds: consecutive 26-week (half-year) calendar windows.
Train fold i  = all calendar strictly before test fold i start, minus a
                1-week embargo (state staleness T−1 + weekly clock).
Selection rule = gates/thresholds chosen ONLY on Train i, frozen VERBATIM,
                applied unchanged to Test i. Re-selection between folds
                (expanding train) is allowed; each re-selection is a new
                ledger row (§3).
```

- **Frozen payload per fold:** the state-engine config (bands, dwell, merge,
  priority ladder), the ON/OFF table, allocation constants, and every
  sleeve-internal threshold that was tuned on Train i. Nothing may be edited
  with knowledge of Test i — code-level enforcement: the engine consumes a
  config blob hashed into the fold manifest (BASE→WAVE→SELECTION→CODE_FREEZE
  ceremony, Q-9).
- **Fold count arithmetic:** with U = 260 usable weeks (≈ a 6.2-year
  intersection window), K = 10 outer folds; report per-fold and pooled.
- **PIT lock inside folds:** every decision consumes only data with
  publication timestamp ≤ decision time (T−1 rule, policy §3.4); the
  truncation-replay check (ERP track-b M-1..M-5 precedent) reruns a random
  sample of decision points with the data store truncated at decision time —
  byte-identical state output required, else fold voided and logged as
  incident (the track-a PIT-seam killer, MAP 1429–1447, turned into a
  standing fixture).
- **S1:** SEALED throughout; no holdout reads before terminal (charter).

## 3. Trial ledger (owner constraint 5: EVERY try counts)

One append-only ledger (JSONL), rows written at try-time, immutable:

```json
{"trial_id": "TR-0007", "fold": 3, "stage": "state_engine|table|allocation|
 sleeve_admission|baseline|robustness", "what": {"knob": "V2_band_p80",
 "value": "p70"}, "selected_on": "TRAIN-3", "applied_to": "TEST-3",
 "outcome_label": null, "utc": "<measured date -u, P-30 stamp law>"}
```

Laws:
- EVERY gate/threshold try is a row — including the preregistered primary
  config (trial 1), every grid node ever evaluated on any train fold, every
  sleeve admission decision, every kill-switch constant, and every robustness
  variant. "We looked at it" = "we ledgered it".
- Preregistered search space (frozen before any evaluation): V1 band
  {±9, ±12.5, ±25} bp · V2 band {p70, p80, p90} · V3 band {p75, p85, p95} ·
  dwell {2, 4} weeks — 3×3×3×2 = 54 nodes max, ≥ 8 guaranteed (RGC §3 PBO
  precedent requires ≥ 8 configs else NOT_RUN). Ladder priority order is NOT
  searched (economic preregistration, policy §3.3).
- DSR and PBO (§7) are computed over ALL ledger rows — no "exploratory
  doesn't count" exemption.
- No try may be deleted or re-ranked after outcomes are seen; an abandoned
  configuration keeps its rows.

## 4. Pre-PnL battery (order frozen; failure at any step is terminal-cheap)

P-27 law: the mechanism-class court runs BEFORE rho, and rho BEFORE PnL.

1. **State-engine census (no PnL):** episodes/dwell/occupancy/transition
   matrix/margin-to-floor per state per train fold, against floors F1–F3
   (policy §3.5). Failure ⇒ NOT_RUN_THIN ⇒ permanent FLAT rows. If ≥ 2 of 4
   states fail ⇒ close `ROUTER_STATES_THIN`.
2. **Representation-rho battery (P-29):** state indicators vs dead-ancestor
   observables (RGC G2 vol-percentile; FXFV3-A6 RV-gated differential
   conditioning; two-regime drawdown-hysteresis on each traded symbol;
   FXFV8-A5 inflation-compensation slope if TIPS gated). Bar |rho| ≤ 0.20
   pooled, immovable. Failure kills the offending variable's state layer.
3. **Arm-distinctness (P-20):** router state vs each sleeve's conditioning
   observable; disagreement fraction measured, fail-closed `None` → NOT_RUN.
4. **Sleeve admissions (policy §2.2):** census verdict → F-0 court → PIT
   battery → measured conditional cost ceiling (worst-fill grading, Q-5;
   ×2.0 bill must clear on TRAIN folds) → sample floors. Failure ⇒
   SLOT_LEFT_EMPTY.
5. **Clock-shadow validity (Q-7, Q-11):** the random/clock controls are
   themselves checked — the null must MOVE (duty/turnover distribution of
   the null must differ measurably from the arm's schedule; autocorrelation
   of the permuted series reported). An invalid null is labeled
   `INVALID_NULL`, never scored as a mechanism kill (Q-11 law).
6. **Inverted router (P-28 cheapest kill):** run BEFORE any tuning is
   allowed anywhere — if the inverted table performs within noise of the
   primary on train folds, the table content is noise and the cycle closes
   `ROUTER_TABLE_UNINFORMATIVE` at zero scored test folds.

## 5. Baseline battery (identical risk budget, allocation engine, costs)

All baselines share the router's allocation/risk/cost/execution plumbing;
they differ ONLY in the enable/disable rule. Missing any baseline = NOT_RUN
(RGC §3 law).

| ID | Baseline | What it falsifies |
|---|---|---|
| B0 | **FLAT** (zero book) | The "just don't trade" floor: router pooled after-cost net must clear zero |
| B1 | **ALWAYS_ON** — all admitted sleeves, always enabled | The JEV law: gating must beat no gating (MAP 1292–1299 precedent) |
| B2 | **BEST_LEG** — single best sleeve by TRAIN-fold net only, frozen into the test fold | Maybe one sleeve carries everything; the router is redundancy |
| B3 | **ABSTAIN-ONLY** — always-eligible class only (macro rows permanently FLAT) | The macro state adds nothing beyond the macro-independent book (router ≈ B3 ⇒ states are decoration) |
| B4 | **RANDOM_GATE** — 100 frozen-seed random enable schedules MATCHED to the router's duty cycle AND turnover (same number of ON-weeks and same switch count, randomized placement) | Any value must come from WHERE the ON-weeks sit, not from being selectively absent (JEV random law) |
| B5 | **CLOCK_GATE** — calendar-shadow: keeps the router's state-change calendar geometry, destroys state identity (payload removal, Q-7) | Value must survive removing WHAT the states are while keeping WHEN they switch |
| B6 | **INVERTED_ROUTER** — table ON↔OFF swapped, states unchanged (P-28) | If inversion is as good, the table is noise |
| B7 | **LAGGED_ROUTER** — state from 4 and 8 weeks ago applied today | If lagged ≈ live, value is slow exposure, not information (Q-7 staleness discipline) |
| B8 | **ORACLE ceiling** — perfect next-week state knowledge (diagnostic only, NON-GOVERNING, disclosed as ceiling — RGC §5 / DAYTRADER diagnostic precedent) | Sizes the maximum the state layer could ever be worth; never a pass bar |

Reporting for B4/B5: full distribution (not just median) of the 100 seeds;
the router must beat the distribution's upper tail consideration explicitly
(reported as percentile of router net within the null distribution).

## 6. Attribution (descriptive only, DEV side only)

- Attribution artifacts decompose net PnL by fold × state × cluster × family
  (when positive, when negative), plus duty cycle, FLAT-week count, switch
  counts, and switching-cost drag — computed on TRAIN (DEV) folds for
  diagnosis and at TERMINAL (post-verdict, non-governing) for the record.
- **Never post-hoc segment selection:** no attribution cell may feed back
  into thresholds, table cells, or sleeve selection within this program. A
  promising segment observed in attribution is NEW-ANCESTRY material for a
  FUTURE cycle with its own trial ledger (P-24 compounding discipline).
- The macro-gated book and the always-eligible book are attributed SEPARATELY
  (the router's measurable effect lives only in the former; B3 comparison).

## 7. Robustness battery

1. **Costs:** full rerun at ×1.0, ×1.5, ×2.0 all-in costs (P-21/Q-5 worst-fill
   doctrine). For states with < 20 merged episodes (policy §3.5 disclosure),
   surviving ×1.5 is a BINDING pass condition, not a sensitivity.
2. **Switching-cost attrition ladder:** switching costs alone scaled
   ×1.0/1.5/2.0 (the exact JEV monotonic degradation axis, MAP 1296–1297).
3. **Leave-one-asset-out:** 12 reruns (drop each symbol). Router must remain
   net-positive vs B1 — no single-asset story (STOCKS-AMIHUD-V1's HTV 99.7%
   lesson; the RGC concentration kill at 0.69 > 0.50).
4. **Leave-one-cluster-out:** 5 reruns. Same bar at cluster granularity.
5. **Fold concentration:** no single test fold may carry > 50% of pooled net
   (JEV/RSM fold fragility; the SPY +19,813 concentration kill, MAP 1298).
6. **Drawdown/tail:** MDD, CVaR(5%) weekly, worst fold, worst state-episode;
   kill-switch fire counts and post-fire PnL (do the switches actually cut
   tail? UNIFIED §8 question).
7. **Capacity/liquidity:** per-instrument notional vs the measured cost band
   tiers; NATGAS/XAG (2–3× cost instruments, UNIFIED §7) get an explicit
   "does the sleeve survive its own expensive venue" line.
8. **DSR/PBO:** Deflated Sharpe Ratio and PBO (CSCV) computed over ALL trial
   ledger rows (§3). Preregistered bars: PBO ≤ 0.5; DSR > 0 at 95%
   confidence on pooled test-fold Sharpe of the selected config.
9. **State misidentification error rate (reported separately, not blended):**
   (a) corruption simulation — state labels flipped with p ∈ {5%, 10%, 20%}
   at decision time, router PnL path sensitivity reported per p; (b) vintage
   divergence — EFFR as-first-published vs revised (revisionIndicator
   machine-served, sixsource row 6b) state disagreement rate on train folds;
   (c) recomputation divergence — state computed at Friday-decision vs
   recomputed Monday-open: any disagreement counts as an error instance.
10. **FLAT-count and duty-cycle reporting:** fraction of decision weeks in
    each state and in ABSTAIN; entries skipped by staleness/blackout/
    spread-guardrail; the "gate that only reduces trades" audit (see PASS
    bar P6).

## 8. PASS bar for the ROUTER (typed, all must hold; else FAIL)

- **P1 (absolute floor):** pooled after-cost net > B0 (FLAT) across test
  folds.
- **P2 (baseline sweep):** pooled after-cost net beats B1, B2, B3, B6, B7,
  and the median of B4/B5; AND beats B1 on ≥ 60% of individual test folds —
  not one year, one asset, one event.
- **P3 (drop-one survival):** remains > B1 in every leave-one-asset and
  leave-one-cluster rerun; no fold > 50% of pooled net.
- **P4 (cost survival):** P2 holds at ×1.5 all-in (×2.0 disclosed either
  way); switching-cost ladder monotonicity disclosed.
- **P5 (multiple-testing survival):** PBO ≤ 0.5 and DSR > 0 (95%) over the
  full ledger.
- **P6 (the JEV/RGC anti-decoration bar):** per-trade after-cost expectancy
  of the macro-gated book ≥ ALWAYS_ON's per-trade expectancy AND pooled net
  > B1. A gate that only reduces trade count without adding after-cost value
  = FAIL, typed `ROUTER_TRADE_COUNT_ONLY`.
- **P7 (state-error tolerance):** P2 direction survives 10% state-label
  corruption (sign, not magnitude, of the B1 comparison).

Close codes (preregistered, non-exhaustive): `ROUTER_NO_INCREMENTAL_VALUE`
(loses baselines), `ROUTER_TRADE_COUNT_ONLY` (P6), `ROUTER_STATES_THIN`
(floors), `ROUTER_TABLE_UNINFORMATIVE` (inverted-Router kill), 
`NOT_RUN_INSUFFICIENT_CALENDAR`, `NOT_RUN_PIT_GATE_FAILED` (V2/V3),
`NOT_RUN_INVALID_NULL` (controls fail Q-11 validity). Negative terminal
outcomes are first-class: the cycle closes with full artifacts, and the
closing entry states its reopening condition once (Q-10): a router-class
reopen on this universe requires a changed mechanism axis
(payer/information/risk — P-29 law), never threshold iteration.

## 9. What this protocol deliberately refuses

- No post-hoc floor relaxation, fold moves, or threshold edits after any PnL
  (owner law, MAP 302–305).
- No sleeve rescue from loss-segment gates (policy §2.2.6; structural).
- No attribution-driven reselection (§6).
- No ORACLE number anywhere near a claim (B8 non-governing).
- No scoring of a control that failed its own validity check (§4.5).
- No blending of state-error sensitivity into the headline PnL (reported
  separately, §7.9).

— End EVALUATION_PROTOCOL_DRAFT. Lane L4, read-only session, no git writes.
