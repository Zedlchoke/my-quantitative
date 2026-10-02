# TRADE_FORENSICS_BRIEF — successor_design_2026-10-02 / TRADE-FORENSICS lane

**STATUS HEADER.** ANALYSIS ONLY: journal-row counting/arithmetic over COMMITTED
artifacts. No engine run, no new PnL replay (no excursion reconstruction was
redone here), no sealed/S1 bytes, no network. Round-trip W/L/BE numbers are
CARRIED FORWARD from the 2026-10-01 docket reconstructions (cited per row);
this lane re-verified the underlying reconciliation arithmetic to the cent
(§2 and `verification_checks.json`) and found one quantified defect in docket
A's swap convention (§2.3). Machine evidence (all produced by
`forensics_build.py`, deterministic, read-only over inputs):
`trade_inventory.json`, `verification_checks.json`,
`guard_spend_band_histogram.json`, `session_dst_alignment.json` (this dir).

Sources: PC12A Stage-C committed journals/metrics
(`research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/diagnostics/stagec/ARMS/{POLICY,B1_ALWAYS_ON}/`),
prior dockets (`terminal_review_2026-10-01/symbol_docket/{USDJPY_DOCKET.md,EURGBP_DOCKET.md}`),
packet analyses (`../JOURNAL_CENSUS_AND_RECONCILIATION.md`, `../SYMBOL_DOSSIERS.md`,
`../COMPLEMENTARITY_AND_FAILURE_MAP.md`, `../analysis/census.json`).

**COST LABEL attached to every dollar number in this brief (unless a row says
otherwise):**
- Costs are **DECLARED bands** under `PROVISIONAL_PENDING_COST_AUTHORITY`
  (never measured against a broker statement), EXCEPT the measured spread
  cells C1–C3: C1 general 0.5/0.9 pips p50/p90; C2 Mon–Thu (21:00,22:00] roll
  2.1/7.4 (n=64,892 corrected cell); C2 Fri 0.8/1.8; C3 Sunday reopen
  11.0/22.0 `[M: DATA_AUDIT §D]`. Slip U3 0.2 pip non-event / 1.0 event;
  commission U2 0.35 bps/side; swap U4/U5 1 pip/night, Wed ×3 (DECLARED).
- **USDJPY PAR-CONVENTION CAVEAT:** USDJPY `cash_delta_usd` on fills is
  carried at par from the JPY notional (10,000 units × 115.63 → 1,156,299.65;
  no ÷rate) while SWAP rows are rate-converted (docket A units caveat). Every
  absolute USDJPY magnitude here scales by ≈1/USDJPY-rate under explicit FX
  conversion; all relative statements (POLICY vs B1, W vs L, rule deltas) are
  invariant. Cross-symbol sums of USDJPY with EUR/GBP numbers are
  convention-limited (DP §13).
- EURUSD/GBPUSD numbers are true USD. Swap is a **cost, never income**
  (FILL_ACCOUNTING_SPEC / INVENTORY_AND_DESIGN §6); journals carry swap as
  positive-outflow (all 2,059 SWAP rows positive across both arms — measured
  this lane).

---

## 1. Inventory: round trips, outcomes, and the not-taken inventory

Dedup law (census §1): POLICY and B1_ALWAYS_ON are the only two
portfolio-realized scored books at ×1.0; tier arms re-price the same corpus;
nothing below is summed across arms as if independent — pooled figures are
explicitly labeled. Round-trip units differ by symbol (USDJPY = flat-to-flat
netted-position excursions, docket A §0; EUR/GBP = FIFO-matched lots, docket
B §Method) — counts are not cross-symbol comparable units.

### 1.1 Round trips and outcomes `[M: prior dockets, carried forward]`

Breakeven law (frozen convention): per-pair median round-trip cost `c`
(USDJPY $239.54; EURUSD $3.35/3.37; GBPUSD $2.12); WINNER net > +c, LOSER
net < −c, BREAKEVEN otherwise — the fee band, not a free parameter.

| symbol | arm | round trips | W / L / B | book net (journal identity, §2.1) | c | citation |
|---|---|---:|---|---:|---:|---|
| USDJPY (par units) | POLICY | 393 | 157 / 224 / 12 | **+600,082.92** (docket A printed 602,943.11 — see §2.3 defect) | 239.54 | docket A §0, §2 |
| USDJPY (par units) | B1 | 310 | 135 / 163 / 12 | **+687,284.31** (docket A printed 689,713.59 — §2.3) | 239.54 | docket A §0, §2 |
| USDJPY pooled | both | 703 | 292 / 387 / 24 | +1,287,367.23 (engine sum) | 239.54 | docket A §2 |
| EURUSD | POLICY | 182 | 92 / 85 / 5 | +2,315.24 | 3.35 | docket B §2.1 |
| EURUSD | B1 | 250 | 121 / 119 / 10 | +600.97 | 3.37 | docket B §2.1 |
| GBPUSD | POLICY | 273 | 125 / 136 / 12 | +942.44 | 2.12 | docket B §2.2 |
| GBPUSD | B1 | 284 | 128 / 138 / 18 | +718.75 | 2.12 | docket B §2.2 |
| **total reconstructed round trips, both primary books** | | **1,692** | | | | census §2.3 |

Fold detail available from the dockets (per-arm-per-fold W/L/B was not
committed as a prior artifact and was NOT recomputed here — that would be a
new PnL replay):

- **USDJPY pooled per-fold W/L/B** (docket A §2): f0 42/56/6 · f1 38/46/2 ·
  f2 33/48/1 · f3 37/51/3 · f4 24/33/4 · f5 42/57/0 · f6 37/58/3 ·
  f7 39/38/5 — losers outnumber winners in every fold; internal-sum check
  PASSED against arm totals (verification check 9).
- **EURUSD per-fold nets $** (docket B §2.1): POLICY +999, +1,216, +110,
  +96, +301, −346, −134, +74; B1 +999, +1,402, −431, +85, −67, +186,
  **−1,696**, +123 (B1 f6 = the long-carry netting channel). Engine
  cross-check: all 16 cells within integer-printing tolerance (worst $1.11,
  §2.2).
- **GBPUSD per-fold nets $** (docket B §2.2): POLICY +166, +176, +196, −48,
  +143, −249, +343, +216; B1 +166, +176, +196, −48, +143, −351, +199, +238.

### 1.2 Blocked / deferred / netted inventory (opportunities NOT taken) `[M]`

Per-leg journal-row recount by this lane; agrees with
`../analysis/census.json` `per_leg_inventory` on every leg (verification
check 2). POLICY column = the policy's own overlay; B1 shows what always-on
still defers (its own spend path differs).

| leg | POLICY decisions / blocked-E1 / deferred / netted-zero | B1 decisions / deferred / netted-zero |
|---|---|---|
| USDJPY-S026 | 1,891 / 0 / **299** / 3 | 1,891 / 262 / 3 |
| USDJPY-S014 | 288 / 0 / 27 / 4 | 288 / 21 / 4 |
| USDJPY-S003 | 10 / 37 / 1 / 0 | 47 / 7 / 0 |
| USDJPY-S023 | 0 / 16 / 0 / 0 | 16 / 0 / 0 |
| USDJPY-S002 | 4 / 79 / 0 / 0 | 83 / 3 / 0 |
| VC2-LVNFAIL-USDJPY | 20 / 22 / 4 / 1 | 42 / 3 / 1 |
| EURUSD-S009 | 3 / **123** / 0 / 0 | 126 / 0 / 11 |
| EURUSD-S013 | 238 / 0 / 0 / 16 | 238 / 0 / 50 |
| EURUSD-S046 | 94 / 0 / 0 / 8 | 94 / 0 / 19 |
| VC2-LVNFAIL-EURUSD | 30 / 44 / 0 / 2 | 74 / 0 / 11 |
| GBPUSD-S002 | 490 / 0 / 0 / 1 | 490 / 0 / 2 |
| GBPUSD-S017 | 56 / 22 / 0 / 0 | 78 / 0 / 0 |
| **portfolio totals** | **3,124 / 343 / 331 / 35** | **3,467 / 296 / 101** |

- BLOCKED_FLOOR (E1, "0–2 decisions in trailing 26w"): fires structurally on
  calendar-sparse legs (S009 123, S002-JPY 79, S003 37, VC2-EUR 44, VC2-JPY
  22, S023 16, S017 22) — floor-vs-clock mismatch, failure mode F3.
- DEFERRED_COST_GUARD (L6, cap $2,836.97, trailing 28d spend): 331 POLICY
  (S026 299) / 296 B1 (S026 262) — guard spend-band histogram and grid-node
  feasibility counts in `GUARD_AND_SESSION_FORENSICS.md` §1.
- NETTED_TO_ZERO (L4 tie): 35 POLICY / 101 B1 — $0 divergence by
  construction (ties net to zero in both arms).
- **SUPERMAJORITY_BLOCK: metrics-only, no journal rows in either arm**
  (census §3.2): portfolio totals POLICY 659 vs B1 1,021; per-leg (B1
  `fills_by_outcome`): S026 706 · S014 186 · S002(JPY) 55 · S003 20 ·
  VC2-JPY 22. The largest blocked channel; PnL attribution `[NR]` (closest
  proxy `pathdown_policy_sizing_netting` −$31,686 `[derived]`).
- All 331+296 guard defers carry cap exactly $2,836.97 (constant, verified)
  and `blocked_reason_detail` parses 100% with X,Y matching the structured
  `guard` field (verification check 3).

---

## 2. Reconciliation statements (what reconciles to what, and one defect)

### 2.1 Journal net identity — EXACT, all six cells `[M: this lane]`

**Σ(NET_ORDER cash_delta_usd) − Σ(SWAP swap_usd) = engine
`per_symbol_fold_records` Σ(cash_end − cash_start)**, residual **$0.000** on
every arm × symbol cell (USDJPY POLICY 600,082.92 / B1 687,284.31; EURUSD
2,315.24 / 600.97; GBPUSD 942.44 / 718.75). Swap rows are positive-outflow
in the journals (963 POLICY + 1,096 B1 rows, zero negative), consistent with
the GATING_VS_SIZING fold cash law "Σ(fills − swaps) = cash_end −
cash_start, worst $1e-6". This is the strongest reconciliation on file: the
committed journals, the engine rollup, and the weekly identity agree to the
cent without any residual convention story.

### 2.2 Inherited reconciliations re-verified `[M]`

| inherited claim | this lane's verification | verdict |
|---|---|---|
| USDJPY friction (docket A §0) = metrics `cost_bill_totals_usd` exactly (POLICY 128,073.06 / B1 106,651.05) | commission+cross_cost from journal fills + \|swap\| = cost bill within $0.02 on both arms; per-fill identity spread_once+slip == cross_cost holds on all 4,799 fills | PASS |
| EUR/GBP per-fold reconstruction vs engine records, 32 cells, ≤$1 (docket B §Method) | engine fold deltas vs docket-printed integers: worst $1.11 (B1 EURUSD f2); docket prints integers, so a true ≤$1.0 reconstruction delta can show up to $1.5 — claim neither falsified nor exactly verifiable from printed integers | PASS (tolerance) |
| Fold cash identity / weekly nets / known totals (census §4, GATING_VS_SIZING V1–V4) | identity convention confirmed against journals (§2.1); known totals USDJPY −87,201.39 / EURUSD +1,714.26 / GBPUSD +223.70 reproduce from engine fold records | PASS |
| Row census and per-leg inventory vs `census.json` | full recount: all row kinds and all legs agree (verification checks 1–2) | PASS |
| Force-flats: USDJPY POLICY 4 / B1 5 (docket A §0); portfolio n_force_flat POLICY 6 / B1 11 (metrics) | consistent (4+2 EUR = 6; 5 + 6 other-symbol = 11) | PASS |

### 2.3 DEFECT FOUND IN DOCKET A (quantified; all readings unaffected)

Docket A §0 states: "POLICY 393 trades, Σnet = +602,943.11 = journal symbol
net (fills 601,513.02 **+ swap** 1,430.10)" and explains the 2,860.19 gap to
the engine fold records (600,082.92) as "fold-edge mark convention in the
rollup; 0.48%". **Measured: the gap is exactly 2 × Σswap in both arms**
(POLICY 2,860.19 = 2×1,430.10; B1 2,429.28 = 2×1,214.64) and the correct
identity fills − swap reconciles to the engine at $0.000 (§2.1). The docket
added a positive-cost swap into its excursion net convention; there is no
fold-edge residual. Consequences:

- Every ABSOLUTE USDJPY "Σnet" printed in docket A — per-arm sums (602,943.11
  / 689,713.59), the pooled outcome-table sums (W +6,417,355.58 / L
  −5,124,559.15 / B −139.73, which total exactly 602,943.11+689,713.59), and
  derived means — is **overstated by exactly 1× swap** (+1,430.10 POLICY /
  +1,214.64 B1; 0.2–0.5%).
- W/L/B classification (c = friction median $239.54), fold W/L splits,
  medians, and every relative POLICY-vs-B1 statement are unaffected.
- Propagation: `JOURNAL_CENSUS_AND_RECONCILIATION.md` §4 row "USDJPY
  excursion Σnet = journal symbol net … exact" inherits the wording;
  `SYMBOL_DOSSIERS.md` §7 and `COMPLEMENTARITY_AND_FAILURE_MAP.md` §3 quote
  the correct engine numbers (600,083/687,284) — no other packet document is
  affected.
- Docket B (EUR/GBP) uses the correct convention (net = gross − spread −
  slip − commission − swap) and its nets reconcile to the journals under
  §2.1's identity.

---

## 3. Feature-at-entry vs post-exit diagnostics: field-coverage table

Two-column split of every diagnostic used in the prior work. "Feature-at-
entry" = knowable at decision time from journal fields; "post-outcome" =
computed only after the excursion closes. Attribution laws (trig / pfold /
solo) are a separate axis and are named in §5.

| feature-at-entry (journal-recorded) | post-outcome (post-exit only) |
|---|---|
| `onoff_features.decision_count_trailing` (dct; docket A §3 δ=0.028 null; docket B §3 medians) | holding time (W 24h vs L 7h med; docket A §4) |
| `direction_vote` (long/short splits; docket A §3; docket B §3) | MFE/MAE — **NOT_RUN_INPUT_MISSING** (no journal field) |
| entry hour/session (derived from `ts_decision_utc`; NY bucket, Tokyo bucket, hour 12/16 gates) | exit class (SIG-ENTRY 650/703 netting exits; SL/TP/TIME/FORCEFLAT; docket A §4, docket B §4) |
| `leg_id` / `cluster_id` / `family_id` (cluster PnL table, docket A §3) | net / gross per trade; friction decomposition (docket A §5; docket B §5) |
| `eligibility_state` / `eligibility_rule_id` (E1 floor behavior) | W/L/B grouping (c = median round-trip cost — a post-outcome statistic of the cost distribution) |
| `portfolio_state.n_eligible` (constant per pair — no contrast, docket A §3) | force-flat tags at fold edges (docket A §0) |
| `entry_reason_code` at the entry trigger (M1_STOP_HIT vs H1_PDH_BREAK etc.) | swap allocation per excursion (docket A/B cost anatomy) |
| guard state on DEFER rows: `guard.trailing_spend_usd` / `cap_usd` (this packet, guard histogram) | rule-sensitivity off/on tables (retrospective suppression on the exposed path — post-outcome BY CONSTRUCTION) |
| `estimate.est_*` cost estimates on DEFER rows (admission-side ex-ante cost view) | co-loss weeks / heat events / weekly correlations (complementarity §1 — cash-basis post-hoc) |
| `outcome_exposed_label` (label only — no contrast possible except VC2 CLASS_CANDIDATE) | attribution tables (trig/pfold/solo) — post-outcome bookkeeping of closed trades |

**Journal fields that DO NOT EXIST (all typed NOT_RUN_INPUT_MISSING, docket
A §3/§9, docket B §9):** MAE/MFE and any intrabar path (TB-LABELS producer
not yet run over the committed M1 panels); per-fill quoted spread at the
entry bar (journals carry only the charged model `spread_once_usd` plus the
C-cell band tag — the quoted spread of the bar was not recorded); realized
volatility at entry and trend/regime state (`feature_pit_snapshot` carries
only value digests of D1/M1 closes, not numeric features); cross-pair state
beyond `n_eligible`. Adapter specs for the successor journal:
`GUARD_AND_SESSION_FORENSICS.md` §4.

---

## 4. Per-leg "what killed it" (or saved it) — from the dockets, cited

"Killer" classes: **cost** (fee/swap-dominated), **signal** (wrong-side
mechanism), **exit-geometry** (stop/target structure), **netting**
(path-dependence of the one-position-per-symbol voter), **floor/guard**
(admission governance). All TEST-fold, exposure-labeled, hypothesis-generating.

| leg | verdict from prior work | killer class | evidence (cited) |
|---|---|---|---|
| USDJPY-S026 pdhl_stop_sweep | blend-dependent cascade; solo it is churn (+9,203 solo vs +825k/+822k trig, 178× spread) | **netting** (+ guard interaction) | docket A §2 decomposition; census §5; H1 guard defers 299 rows |
| USDJPY-S014 rsi2_fade | fades the macro trend; RSI2_MID_CROSS family −470,441.67 (n=33); sign flips by attribution law (solo +109k vs portfolio −222k/−320k) | **signal** (+ attribution ambiguity) | docket A §3, §7 H4; census §5 |
| USDJPY-S003 tsmom_12_1skip | blocked by E1 in POLICY (37 blocks); trend core — B1 paper +225,631 | **floor** (sparsity mis-read as dead) | docket A §6 E-floor OFF; dossier §1 |
| USDJPY-S023 vol_regime_breakout | E1-blocked (16); B1 paper +230,099, realized entries +187,084 | **floor** | docket A §6; dossier §1 |
| USDJPY-S002 ma_regime_gate | E1-blocked (79); solo always-on **−248,990** but POLICY's floored 34 fills +137,883 — the floor was load-bearing | **floor (beneficial)** | dossier §1; census solo arms |
| VC2-LVNFAIL-USDJPY | noise-level (−385 solo B1 / +280 floored POLICY); E1 22 blocks | **floor** (neutral) | dossier §1 |
| EURUSD-S009 macd_divergence_exit | E1 floor SAVED the pair: 123/126 decisions blocked; B1 book −587.8; missed-set −504.0 | **floor (beneficial)** + signal (TRAIN +7.2k did not transfer) | docket B R-E1, H-E1; dossier §2 |
| EURUSD-S013 bb_zscore_fade | workhorse by count (103/182) but median net −$4.3 (fee band); SL fires 3× per TP and costs 2× the median TP win (SL 49 → −1,528.8 vs TP 35 → +1,866.8); net is 5 tail trades (+1,389) | **exit-geometry** + cost + tail dependence | docket B §2.1, §4 |
| EURUSD-S046 monthend_fix_flow | TIME-only exits neutral (+38.9); real PnL via other legs' closes of its lots (+962.4) | benign (netting-carried winner) | docket B §4 |
| VC2-LVNFAIL-EURUSD | E1 floor COST admission: missed +227.4; B1 book +653.0/26 positive 6/8 folds, cost-light | **floor (harmful)** | docket B R-E3, H-E3 |
| GBPUSD-S002 session_open_cont | edge = survive to 16:00 London exit (+3,852.9 on 177 TIME exits) vs ±2-pip stop (−2,864.6, 27.0% stop rate; one stop erases 2.7 median time-exit wins) | **exit-geometry** | docket B §4, H-G2 |
| GBPUSD-S017 vwap_reversion_fade | stop inside entry-bar noise: 20 SL : 6 TP; 15/28 close within 1 minute; both arms negative (−47.6/−212.9) | **exit-geometry** (retire candidate) | docket B §4, R-G1 |
| (symbol-level) USDJPY NY-session longs | only sign-consistent negative bucket in BOTH arms, all 8 folds (POLICY −281,460 n=91 / B1 −83,684 n=74; pooled long×NY −384,747) | **session admission** | docket A §3, §6; dossier §1; DST composition in GUARD_AND_SESSION §2 |
| (symbol-level) EURUSD hours 12/16z | worst entry hours both arms (hour 16 POLICY −264.2 n44 / B1 −210.4 n39; hour 12 B1 −826.7 n20, 13/20 netting artifacts) | **session admission** (+ netting artifact in h12 cell) | docket B §3, R-E2 |

Costs as the primary killer appear only below the M1 majors: USDCAD/AUDUSD
legs are COST_DOMINATED at ×2.0 (9/9, docket C) and the DAILY cohort is
net-negative at every tier under DECLARED costs — neither has scored
journals, so no trade-level row exists for them (dossier §4, §6).

---

## 5. What this brief does NOT establish

- **No causal claims.** Every bucket contrast here (NY-longs, hour gates,
  floor saves/costs, guard effects) is a retrospective read of ONE exposed
  scored path (8 TEST folds 2022-01-07→2025-12-26, POST_OUTCOME labels).
  Nothing is out-of-sample; nothing validates a rule.
- **No counterfactuals.** Suppression tables are ATTRIBUTION-on-exposed-path
  ("what the trades that this rule would have denied did on the path that
  traded"), not marginal PnL of the rule. Re-admitting deferred/blocked
  signals changes the netting path itself (650/703 USDJPY exits are netting
  SIG-ENTRYs), so admitted-set PnL is measurable only by full-path replay —
  never by arithmetic on these journals. Portfolio-minus-one-leg does not
  exist (solo ≠ minus-one; census §5).
- **Attribution laws are named and not interchangeable.** `trig` (portfolio
  entry-trigger), `pfold` (paper_fold_net_by_leg), `solo` (single-leg arm)
  disagree in SIGN for S014 and by 178× for S026 (census §5; complementarity
  §3). Any successor rule keyed to "a leg's PnL" must name its law.
- **No MAE/MFE, no intrabar paths, no per-fill quoted spreads, no realized
  vol at entry** — NOT_RUN_INPUT_MISSING; exit-law questions (S002 stop
  widening, S013/S017 stop ordering) need TB-LABELS/TB-EXIT-OVERLAY lanes,
  not journal recomputation.
- **USDJPY absolute magnitudes are par-convention** (§ COST LABEL); the
  pooled −$85,263 POLICY−B1 differential and cross-symbol sums inherit that
  convention (quote-CCY restatement is a required successor item, F9).
- **Costs are DECLARED bands** pending owner cost authority; C1–C3 cells are
  the only measured spread cells. True swap/commission have never been
  checked against a broker statement.
- **DST/session composition is descriptive counts only** (decision rows);
  PnL-by-DST-phase is NOT_RUN under this lane's no-replay constraint
  (GUARD_AND_SESSION_FORENSICS §2, §4).

— end brief —
