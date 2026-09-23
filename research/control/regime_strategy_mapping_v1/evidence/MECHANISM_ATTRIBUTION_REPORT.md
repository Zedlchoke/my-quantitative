# P1 — V2 MECHANISM ATTRIBUTION Report (A2 lane)

**Cycle:** REGIME-STRATEGY-MAPPING-V1 · **Phase:** P1 mechanism attribution (A2)
**Schema:** `rsmv1_mechanism_attribution@1` · **Machine evidence:**
`evidence/mechanism_attribution.json` · **Run:** `tools/run_diagnostics.py attribution`
(exit 0; **51/51 checks PASS** over BTC_H1 / BTC_H4 / SPY_D1)
**Date:** 2026-09-23 · **Inputs (read-only):** V2 tier-1 trade ledgers
(`jev_regime_router_v2/runtime/scored/…`), rebuilt regime timelines (verified vs V2:
switches 90/31/34), V2 frozen mapping/fold contracts. Zero provider calls; nothing
written into the V2 worktree.

> **Disclosure (verbatim from the module docstring):** "Outcome-observed diagnostics
> on the terminal V2 corpus. Nothing here is a validated configuration;
> counterfactuals locate the failure mechanism only. No strategy design, no parameter
> selection, and no counterfactual may be read as a proposal (plan section 3)."

All numbers below are USD on the V2 base cost tier (BTC 5+1 bps/side + funding;
SPY 10 bps/fill). "JEV" = `JEV_ONLY_ROUTER` (the terminal corpus's regime-driven arm).

---

## 0. Baseline reproduction (foundation for everything below)

Before any decomposition, the forked V2 engine was rerun on the REBUILT JEV target
series (persisted timeline recomputed from the frozen decision cache) and compared to
the V2 stored ledger:

| Cell | rerun net | stored net | rerun trades | stored trades | fold nets | A7 audit folds |
|---|---|---|---|---|---|---|
| BTC_H1 | −88,140.39 | −88,140.39 | 978 | 978 | identical <1e-6 | match (±0.5) |
| BTC_H4 | −85,274.07 | −85,274.07 | 1,060 | 1,060 | identical <1e-6 | match (±0.5) |
| SPY_D1 | −51,623.26 | −51,623.26 | 343 | 343 | identical <1e-6 | match (±0.5) |

The reproduction is **bit-exact** (max abs diff 0.0 on every totals component and every
fold net; engine identity `100000 + net == equity[-1]` and
`|Σ fold_net − net| < 1e-9` hold on every rerun). Every decomposition below is
therefore measured on the same mechanics that produced the V2 terminal numbers.

---

## 1. (a) Gross signal loss vs costs

**Both components are large on BTC; on SPY the loss is almost entirely cost churn.**

| Cell | JEV net | Gross PnL | Total costs (fee + slip + funding) | Cost share of gross loss |
|---|---|---|---|---|
| BTC_H1 | −88,140.39 | −40,010.74 | 48,129.66 (fee 40,104.97 + slip 8,020.99 + funding 3.69) | 55% of the loss is costs; gross signal itself lost −40,011 |
| BTC_H4 | −85,274.07 | −32,207.76 | 53,066.31 (fee 44,265.50 + slip 8,853.10 + funding −52.28) | 62% costs; gross −32,208 |
| SPY_D1 | −51,623.26 | −2,931.90 | 48,691.35 (all fee; no slip/funding) | **94% costs**; gross ≈ break-even |

Reading: on BTC the JEV mapping lost money **twice over** — the underlying strategy
signals lost gross AND the trading they generated paid ~48–53k in costs. On SPY the
signal was roughly gross-neutral but the corpus paid 48.7k of fees to access it —
churn, not direction, is the SPY failure mode.

---

## 2. (b) Cost attribution by cause (frozen per-trade classification)

Frozen rule (module docstring, unit-tested): `fold_flat → fold_force_flat`;
`stop | strategy_exit → strategy_native`; `regime_off` → `unnecessary_close_reopen`
iff the next same-fold entry resumes the SAME direction and the governing target never
mapped opposite in between, else `regime_switch`. JEV_ONLY:

| Cell | Cause | Trades | Net | Costs (fee+slip+funding) |
|---|---|---|---|---|
| BTC_H1 | strategy_native | 971 | −87,999.63 | 47,839.08 |
| BTC_H1 | regime_switch | 4 | −1,148.19 | 186.05 |
| BTC_H1 | fold_force_flat | 3 | +1,007.44 | 104.53 |
| BTC_H4 | strategy_native | 1,056 | −85,345.01 | 52,916.11 |
| BTC_H4 | regime_switch | 4 | +70.94 | 150.20 |
| SPY_D1 | unnecessary_close_reopen | 271 | +19,621.98 | 38,449.26 |
| SPY_D1 | strategy_native | 69 | −72,216.14 | 9,857.56 |
| SPY_D1 | regime_switch | 2 | +113.34 | 226.24 |
| SPY_D1 | fold_force_flat | 1 | +857.56 | 158.29 |

Plain language:

- **BTC: the loss is ~99.8% strategy-native.** Only 4 of 978 (H1) / 4 of 1,060 (H4)
  exits were regime_off at all; the regime-switching machinery itself contributed
  ≤186 of ~48–53k cost. The corpus lost money because the mapped strategies
  (TREND_SHORT in DOWNTREND, TREND_LONG/MR_LONG elsewhere) churned unprofitably on
  their own signals — not because the router switched.
- **SPY: the dominant cost class is `unnecessary_close_reopen`** — 271 positions
  closed by a regime-driven flat and re-entered in the same direction, paying 38.4k
  in fees while their gross was positive (+19.6k). The remaining 69 strategy-native
  trades lost −72.2k net. Where those reopens came from is quantified in §3–§4.

---

## 3. (c) PnL by regime and stable-vs-transition windows

**By governing regime (bar-level equity deltas, JEV_ONLY):**

| Cell | UPTREND | ACCUMULATION | DOWNTREND | DISTRIBUTION | TRANSITION_UNKNOWN | STALE |
|---|---|---|---|---|---|---|
| BTC_H1 | −32,833.40 | −4,766.66 | **−50,540.33** | 0.00 | 0.00 | — |
| BTC_H4 | −15,492.96 | −1,827.75 | **−67,920.07** | −33.29 | 0.00 | — |
| SPY_D1 | −26,854.79 | 0.00 | 0.00 | +57.42 | 0.00 | **−24,825.88** |

- BTC: the DOWNTREND mapping (TREND_SHORT) is the single worst bucket — 459 (H1) /
  626 (H4) short trades with net −50.5k / −67.9k (gross −26.5k / −31.7k + costs).
  The label was often "right" about downtrends, but 15-minute short churn at 6 bps/side
  destroyed any edge. UPTREND longs add another −32.8k / −15.5k.
- SPY: every one of the 343 trades was entered under UPTREND (the only SPY label that
  maps to a strategy). The **STALE bucket (−24.8k)** is a discovered sub-mechanism:
  under the frozen SPY timestamp convention (session close stamped next-midnight) the
  staleness law (`> 2 regime periods → FLAT`) makes **every Tuesday bar's governing
  decision 3 days old**, so V2 force-flattened open positions every Tuesday open and
  re-entered after. This is reproduced bit-exactly from V2's own stored ledger — it is
  a property of the V2 corpus, not of this rebuild.

**Stable vs transition windows (±k regime bars around each of the 90/31/34 persisted
switches; JEV_ONLY, plus ALWAYS_ON_MR as a regime-independent control):**

| Cell | window | bars inside | JEV PnL inside | JEV PnL outside | MR-always-on inside |
|---|---|---|---|---|---|
| BTC_H1 | ±1 | 810 | −4,920.49 | −83,219.90 | +968.39 |
| BTC_H1 | ±2 | 1,530 | −5,925.40 | −82,214.99 | +3,524.32 |
| BTC_H1 | ±3 | 2,250 | −6,226.98 | −81,913.41 | +3,886.76 |
| BTC_H4 | ±1 | 1,023 | −1,519.66 | −83,754.41 | −2,668.09 |
| BTC_H4 | ±3 | 3,007 | −10,832.72 | −74,441.35 | −1,660.33 |
| SPY_D1 | ±1 | 75 | **+222.42** | −51,845.67 | −3,242.80 |
| SPY_D1 | ±3 | 164 | −1,560.89 | −50,062.37 | −1,803.56 |

Plain language: **transition windows are NOT where the corpus loses.** On BTC_H1 only
5.6–7.1% of the loss occurs within ±1–3 regime bars of a switch (roughly proportional
to the window's bar share). On SPY the ±1 windows are actually mildly POSITIVE for
JEV while 100% of the loss accrues in steady-state holding — the bleeding is the
strategy carrying positions, not the switching.

---

## 4. Activity, holding, and no-op counts (JEV_ONLY)

| Metric | BTC_H1 | BTC_H4 | SPY_D1 |
|---|---|---|---|
| Entries | 978 | 1,060 | 343 |
| Exits: strategy_exit / stop / regime_off / fold_flat | 853 / 118 / 4 / 3 | 987 / 69 / 4 / 0 | 62 / 7 / 273 / 1 |
| Direction reversals | 68 | 27 | 0 |
| Same-direction re-entries | 909 | 1,032 | 342 |
| Median / mean holding (exec bars) | 4 / 7.15 | 4 / 8.01 | 3 / 2.26 |
| Turnover (V2 stored: entered notional / avg equity / year) | 1,061.2 | 1,047.8 | 30.3 |
| Target-series changes | 90 | 31 | 824 |
| — of which direction-preserving ("no-op") label changes | 16 | 1 | 1 |

Median holding of 4 × 15m bars (BTC) and ~3 sessions (SPY) with ~1,000× annual
turnover on BTC shows the corpus was churning at the cost model's full bandwidth.
Direction-preserving label churn (the `cf_a` mechanism) is rare on BTC_H1 (16) and
near-zero elsewhere — consistent with the small `cf_a` savings below.

---

## 5. (d) Counterfactual families — what each would have saved

**DIAGNOSTIC ONLY.** Each family reruns the identical forked V2 engine on a transformed
target series; deltas locate the failure mechanism. **No counterfactual here is a
proposal, and none reaches profitability on BTC.** `delta = counterfactual net − JEV net`
(positive = loss avoided).

| Family (target transform) | BTC_H1 | BTC_H4 | SPY_D1 |
|---|---|---|---|
| Baseline JEV net | −88,140.39 | −85,274.07 | −51,623.26 |
| (a) no-op: hold same direction | **+4,014.53** | +1,321.31 | 0.00 |
| (b) transition buffer 1 regime bar | +1,696.20 | +565.35 | −1,978.44 |
| (b) transition buffer 2 | +1,721.80 | +1,304.96 | −400.80 |
| (b) transition buffer 3 | +1,743.53 | +1,927.73 | −770.57 |
| (c) minimum hold 2 / 4 / 8 regime bars | 0.00 / 0.00 / 0.00 | 0.00 / 0.00 / 0.00 | −3,380.31 / −3,500.21 / **+7,173.74** |
| (d) risk-off veto only, MR_LONG base | +57,561.32 | +71,339.31 | +49,556.11 |
| (d) risk-off veto only, TREND_LONG base | +9,161.07 | +45,293.89 | +1,063.94 |
| (d) reference: always-on MR_LONG (no veto) | +35,008.27 | +31,373.09 | +50,699.56 |
| (d) reference: always-on TREND_LONG (no veto) | −3,394.90 | −4,224.58 | +71,435.95 |

Resulting absolute nets (baseline + delta): **every measured BTC variant stays deeply
negative** — the least-bad is the risk-off veto on the MR_LONG base at ≈ −30.6k (H1)
/ −13.9k (H4). On SPY the veto variants land at ≈ −2.1k (MR base) and ≈ **−50.6k
(TREND base)**: overlaying the JEV-style flat-in-DISTRIBUTION/DOWNTREND mapping on an
always-on base **reproduces the churn collapse** — always-on TREND falls from
+19.8k to ≈ −50.6k once the label machinery is allowed to force it flat and re-enter.
That is the sharpest single result in this audit: on SPY the fee bleed is generated by
the label-driven flat/re-enter machinery itself, not by any market view in the labels.

Plain-language mechanism readings:

1. **BTC: nothing timing-related moves the needle.** Buffers (≤+1.9k), no-op holding
   (≤+4.0k) and minimum holds (+0.0 — the transform never binds; positions rarely span
   a target change) recover ≤5% of an 85–88k loss. The failure is the mapped
   strategies' own gross churn plus their costs, not switch timing.
2. **SPY: the churn is real but suppressing it trades fee savings against lost gross
   at unfavorable terms** — buffers and short min-holds are NEGATIVE deltas; only the
   very long 8-bar min-hold (which suppresses most re-entries outright) recovers
   +7.2k — by not trading, not by timing better.
3. **The veto family separates signal from machinery.** On BTC, veto-on-MR improves on
   always-on MR itself (−53.1k → ≈ −30.6k on H1; −53.9k → ≈ −13.9k on H4), so the
   DIST/DOWN veto does remove some BTC MR losses — but the result remains far below
   any viability threshold. On SPY the same veto destroys the only profitable baseline
   (TREND +19.8k → ≈ −50.6k) by injecting churn. **No family produces a validated
   configuration, and none is proposed.**

---

## 6. (e) Reconciliation table — every arm, every cell (18/18 PASS)

Recomputed from per-trade ledger rows vs V2 stored totals; verdict PASS requires
count match and <1e-6 on gross/fee/slip/funding/net (plus stored engine identity and
fold-sum identity per arm).

| Cell | Arm | Trades | Net (stored) | Gross | Fee | Slip | Funding | Verdict |
|---|---|---|---|---|---|---|---|---|
| BTC_H1 | ALWAYS_ON_MEAN_REVERSION | 391 | −53,132.13 | −22,035.94 | 25,832.56 | 5,166.51 | 97.11 | PASS |
| BTC_H1 | ALWAYS_ON_TREND | 1,386 | −91,535.29 | −30,850.20 | 50,420.87 | 10,084.17 | 180.04 | PASS |
| BTC_H1 | DETERMINISTIC_REGIME_ROUTER | 1,793 | −96,654.04 | −39,684.66 | 47,477.05 | 9,495.41 | −3.08 | PASS |
| BTC_H1 | JEV_ONLY_ROUTER | 978 | −88,140.39 | −40,010.74 | 40,104.97 | 8,020.99 | 3.69 | PASS |
| BTC_H1 | DETERMINISTIC_PLUS_JEV_CONFIRMATION | 760 | −81,761.30 | −39,164.96 | 35,507.26 | 7,101.45 | −12.38 | PASS |
| BTC_H1 | RANDOM_MATCHED_ROUTER | 820 | −74,277.18 | −20,471.71 | 44,807.23 | 8,961.45 | 36.79 | PASS |
| BTC_H4 | ALWAYS_ON_MEAN_REVERSION | 374 | −53,900.99 | −24,921.89 | 24,077.11 | 4,815.42 | 86.56 | PASS |
| BTC_H4 | ALWAYS_ON_TREND | 1,269 | −89,498.66 | −29,802.80 | 49,601.89 | 9,920.38 | 173.59 | PASS |
| BTC_H4 | DETERMINISTIC_REGIME_ROUTER | 1,175 | −88,145.12 | −36,903.94 | 42,755.92 | 8,551.18 | −65.93 | PASS |
| BTC_H4 | JEV_ONLY_ROUTER | 1,060 | −85,274.07 | −32,207.76 | 44,265.50 | 8,853.10 | −52.28 | PASS |
| BTC_H4 | DETERMINISTIC_PLUS_JEV_CONFIRMATION | 859 | −77,672.32 | −26,634.27 | 42,582.41 | 8,516.48 | −60.84 | PASS |
| BTC_H4 | RANDOM_MATCHED_ROUTER | 992 | −83,956.66 | −33,207.01 | 42,316.11 | 8,463.22 | −29.69 | PASS |
| SPY_D1 | ALWAYS_ON_MEAN_REVERSION | 18 | −923.70 | +2,433.56 | 3,357.26 | 0.00 | 0.00 | PASS |
| SPY_D1 | ALWAYS_ON_TREND | 143 | +19,812.69 | +51,734.65 | 31,921.95 | 0.00 | 0.00 | PASS |
| SPY_D1 | DETERMINISTIC_REGIME_ROUTER | 213 | −31,876.58 | +3,122.62 | 34,999.20 | 0.00 | 0.00 | PASS |
| SPY_D1 | JEV_ONLY_ROUTER | 343 | −51,623.26 | −2,931.90 | 48,691.35 | 0.00 | 0.00 | PASS |
| SPY_D1 | DETERMINISTIC_PLUS_JEV_CONFIRMATION | 194 | −32,383.97 | −1,152.09 | 31,231.89 | 0.00 | 0.00 | PASS |
| SPY_D1 | RANDOM_MATCHED_ROUTER | 275 | −30,015.38 | +16,502.25 | 46,517.63 | 0.00 | 0.00 | PASS |

Check inventory per cell (17 checks × 3 cells = 51): 6× ledger reconciliation, 6×
stored engine identity, 6× bar-attribution identity, 1× cost-attribution
reconciliation (JEV), 1× baseline-rerun totals, 1× baseline-rerun fold nets, 1× A7
fold-net cross-check. **51/51 PASS** (`all_checks_pass: true` in the JSON).

---

## 7. Mechanism summary (what the terminal corpus actually died of)

- **BTC_H1 / BTC_H4:** gross signal loss (−40.0k / −32.2k) PLUS strategy-native cost
  churn (47.8k / 52.9k of cost). DOWNTREND→TREND_SHORT is the worst single bucket
  (−50.5k / −67.9k net). Regime-transition handling is a rounding error: 4 regime_off
  exits per cell, ≤+1.9k recoverable from any buffer/hold/no-op counterfactual.
- **SPY_D1:** a cost-churn collapse (−51.6k net on ≈ gross-neutral signal). 79% of
  trades were same-direction reopen churn paying 38.4k in fees; a discovered frozen-law
  interaction — the staleness rule force-flattens every Tuesday open under SPY's
  next-midnight close convention (STALE bucket −24.8k) — feeds that churn, together
  with ACC/UPT↔UNK label flapping. The 69 strategy-native trades separately lost
  −72.2k net.

## 8. Scope, limitations, and non-claims

- Outcome-observed diagnostics on ONE terminal corpus (3 cells, 4 folds each, base
  cost tier). No statistical inference, no out-of-sample claim, no parameter search.
- Counterfactual deltas are single-path reruns of the same frozen engine; they locate
  mechanisms, they do not estimate achievable improvements (no re-optimization of
  anything was performed or allowed).
- Cause classification is the frozen per-trade rule above; `regime_switch` on BTC is
  small by construction because JEV's BTC exits are 99%+ strategy-internal.
- The SPY Tuesday-staleness observation is a description of the frozen V2 law as run;
  it is reproduced bit-exactly from V2's own stored ledger and verified by the 51/51
  reconciliation. It is not a defect finding about this cycle's rebuild.
- SPY ALWAYS_ON_TREND +19,812.69 (concentration 0.69 > 0.50 kill at V2) remains a
  reported baseline, NOT a promotion — this cycle has no promotion authority.

## 9. Artifacts and code

- Machine evidence: `research/control/regime_strategy_mapping_v1/evidence/mechanism_attribution.json`
- Module (frozen rules in docstring; all pure helpers unit-tested):
  `research/control/regime_strategy_mapping_v1/rsmv1/attribution.py`
- Tests: `research/control/regime_strategy_mapping_v1/tests_py/test_attribution.py`
  (16 tests) + `tests_py/test_regime_timeline.py` (5) — `pytest tests_py -q`: 21 passed.
- Run entry: `tools/run_diagnostics.py attribution` (exit 0 = every check PASS).
- Read-only inputs: V2 `runtime/scored/{cell}/{arm}/tier_1.json`;
  `data_local/decisions_*.jsonl`; freezes (`mapping_arms_freeze`, `fold_contract`,
  `data_identity_freeze`).
