# A14-V14-A8-OICYC — Positioning-Cycle Beta (market-leverage-cycle co-movement conditioning)

Lane: a8 | Cycle: CRYPTO-V14 | Phase: D1 | Wave SHA `c3e3c90561efc972c487a99951ca0f6031ab4fa34907d1c10890d1795b4da4a8` |
Outcome-blind proposal (no returns, PnL, metrics, rankings or backtests computed; no outcome
files seen). Written against `PLAN_crypto_v14.md` (Sections 1, 1.1, 2, 7, 12), CLAUDE.md,
`research/control/v14_run/run_contract.json` (incl. `shadow_region_rule`), `p_freeze_v14.json`
(incl. `staged_oi_axis_authority`), `d1_wave_contract.json` (AXIS-3), the V14 forbidden-family
inventory and lessons register. Assigned axis: AXIS-3, inverted-OI-flow shadow front door on
the ARCHIVED staged OI captures `v11_oi_staging_v1` (daily clock). This proposal is a
shadow-region entry and carries the plan Section 1.1 disclosures in full (section 12).

---

## 1. Hypothesis ID and mechanism

**Hypothesis ID: `A14-V14-A8-OICYC`** (lexicographically comparable, uppercase, no spaces).

**Mechanism (one paragraph).** A symbol's open-interest FLOW can be decomposed, by a simple
regression, into the part that co-moves with the MARKET-WIDE leverage cycle and the part that
is idiosyncratic. OICYC measures the first part: `CYC_s(T)` is the trailing OLS slope of the
symbol's daily log open-interest changes on the contemporaneous LEAVE-ONE-OUT aggregate of
the other 18 tradeable symbols' daily log OI changes, over the 28 most recent daily changes
whose end-row stamps are <= T — a market-RELATIVE co-movement SLOPE, not an own-path
difference: a symbol that doubles its OI while the market doubles is cycle-riding (high
slope) while a symbol that doubles against a flat market is idiosyncratic accumulation (low
slope), even though both show identical absolute OI growth. Economic counterparty: high
cycle-beta books are where leveraged capital expresses market-wide risk appetite — allocation
chased into waves and dumped out of synchronized unwinds; their entries cluster near wave
peaks at the worst prices and their exits are correlated, so unwind costs land together
(Adrian & Shin 2010: leverage is procyclical — balance sheets expand in booms and contract in
busts; Brunnermeier & Pedersen 2009: correlated forced exits amplify moves; De Long,
Shleifer, Summers & Waldmann 1990: crowd-dominated books carry sentiment-cycle risk that the
crowd itself deepens). Low cycle-beta books reflect symbol-specific hedging or conviction
demand that does not unwind with the market. Why the edge exists: cycle-chasing positioning
buys transient crowding at wave peaks and suffers correlated forced exits when the cycle
turns, while cycle-orthogonal positioning is set by information or hedging needs, not by the
cycle's price path. **Predicted sign: symbols with LOW positioning-cycle beta outperform
symbols with HIGH positioning-cycle beta over the following week**; the anchor is long the
lowest-CYC tercile and short the highest-CYC tercile. **Null that kills it:** the after-cost
low-minus-high cycle-beta spread is non-positive in this universe/window, or the spread is
reproduced by a pure open-interest DOMINANCE sort that contains no co-movement information
(section 6).

OICYC conditions on the **cross-symbol co-movement structure of positioning flows** (a
regression slope against a market factor). Its signal contains no own-path two-point growth,
no OI level or percentile (the aggregate exists only as the regression's regressor), no price
return, no turnover term and no funding term anywhere in the feature.

## 2. Falsifiable prediction (confirmatory status recorded)

The anchor arm, after base costs on the blind-S0 screen window (2025-08-22..2026-08-21, folds
F0/F1/F2 chronological with 1-day purge), passes: after-cost expectancy > 0, position PF
>= 1.10, at least 2/3 chronological folds positive; excess over BTC buy-and-hold AND over the
BTC-beta context is positive in >= 2/3 folds; and the OI-dominance causal control arm fails
at least one of the anchor's three gates.

**This family is preregistered CONFIRMATORY** (shadow-region entry, plan Section 1.1): if
selected at D1, all three of its scored cells carry that status in the verdict record and in
the observed/published denominator accounting, and every Stage-A gate applies unrelaxed.

**FALSIFIED if any of:**
1. the anchor fails any of the three gates above (the cycle-participation discount is absent
   or sign-wrong in this universe/window after costs);
2. the anchor passes but CTL-OISHARE also passes all three gates (the edge is an
   open-interest dominance/size effect — large-OI-share symbols mechanically load on the
   aggregate — and the co-movement information is redundant);
3. excess vs the BTC-beta context is non-positive in >= 2 folds (beta repackaging — here the
   PRICE beta — not positioning-cycle information);
4. the 14d neighbour contradicts the anchor's sign or is unstable across folds (the slope
   estimate is window-fragile, not a robust mechanism);
5. the largest fold-positive share of PnL exceeds 50% (single-regime artifact);
6. A7-N measures |rho| > 0.20 vs the frozen OILEV-V2 anchor OR its inverted control on the
   common window (Section 1.1 gate; INELIGIBLE and withdrawn — see section 12).

No parameter retune, sign flip, cap change, universe carve-out or floor relaxation may be
used to rescue any failure mode above.

## 3. Literature (pass completed BEFORE mechanism finalization)

Search log (web search; batch window 2026-09-05T00:20Z..00:38Z; queries executed in the order
listed; per-query batch stamps minute-level; literature retrieval completed before any
candidate-return computation — none was ever computed).

| # | Query | Retrieval UTC | Verdict | Reason |
|---|-------|---------------|---------|--------|
| L1 | "Adrian Shin 2010 \"liquidity and leverage\" procyclical leverage financial intermediaries" | 2026-09-05T00:21Z | ACCEPT | Adrian & Shin (2010), *JFI* 19(3) 418–437 — leverage is procyclical; intermediary balance sheets expand in booms, contract in busts, and balance-sheet GROWTH co-moves across the sector. Primary anchor: leveraged positioning is a cycle variable, so a book's sensitivity to the aggregate leverage cycle identifies cycle-chasing capital. |
| L2 | "De Long Shleifer Summers Waldmann 1990 \"noise trader risk\" journal of political economy" | 2026-09-05T00:21Z | ACCEPT | De Long, Shleifer, Summers & Waldmann (1990), *JPE* 98(4) 703–738 — noise-trader sentiment creates cycle risk borne by whoever holds crowd-dominated books; sentiment cycles deepen because arbitrage is limited. Supports the crowding/discount channel for high cycle-beta books. |
| L3 | "Brunnermeier Pedersen 2009 \"market liquidity and funding liquidity\" Review of Financial Studies margin spirals" | 2026-09-05T00:22Z | ACCEPT | Brunnermeier & Pedersen (2009), *RFS* 22(6) 2201–2238 — margins are destabilizing and liquidity spirals are mutually reinforcing: correlated forced exits (the synchronized unwind OICYC's high-beta side is exposed to) amplify moves. Caveat: crisis-era marginated markets; transfer to 24/7 instant-margin perps is qualitative. |
| L4 | "bitcoin perpetual futures open interest deleveraging liquidation cascade price impact study" | 2026-09-05T00:23Z | ACCEPT (caveat) | Crypto liquidation/OI-cascade evidence (arXiv 2102.04591 — BitMEX liquidations; SSRN 6920018 — auto-deleveraging) plus the documented 2025 single-day BTC OI drop of ~$12B (CoinDesk 2025-10-15): market-wide OI contractions arrive as sharp synchronized events. Caveat: event studies; OICYC claims an ex-ante co-movement association, not a cascade-timing prediction. |
| L5 | "Karpoff 1987 \"relation between price changes and trading volume\"" | 2026-09-05T00:37Z | ACCEPT (context) | Karpoff (1987), *JFQA* 22(1) 109–126 — activity and price-change dispersion co-move. Context for why the anchor must be armed against non-OI co-exposures (the price-beta context gate, section 7); the anchor itself contains no price or volume quantity. |
| L6 | "data.binance.vision futures um daily metrics zip files sum_open_interest documentation" | 2026-09-05T00:38Z | ACCEPT (venue semantics) | Binance public data collection (`data.binance.vision`, `data/futures/um/daily/metrics/`; `github.com/binance/binance-public-data`) — daily metrics ZIPs carrying `create_time` and `sum_open_interest` at 5-minute rows. Matches the staged capture pinned by `research/control/v11_run/oi_staging_manifest.json`; availability stamps follow the frozen `p_freeze_v14` PIT authority (staged OI at the daily metrics date stamp). The aggregate factor is built ONLY from the same staged records (no new source). |

**Primary-source claims used:** (i) leveraged positioning is procyclical and its growth
co-moves across the sector (L1); (ii) crowd-dominated books carry sentiment-cycle risk with
correlated exits (L2, L3); (iii) market-wide OI contractions in crypto arrive as sharp,
synchronized events (L4).

**Crypto-perpetual transfer caveats.** (a) Adrian–Shin evidence is intermediary balance-sheet
data; a perp symbol's aggregate OI is a venue-wide positioning stock, and the "leverage
cycle" here is Binance USD-M-only — cross-venue and spot positioning is invisible, so
"market-wide" means "the staged universe's aggregate". (b) The slope is estimated on 28 (or
14) daily observations: noisy by construction; the design answers with cross-symbol RANKING
(slope order, not magnitude), fold and drop-one gates, and the preregistered window-fragility
falsifier. (c) The leave-one-out aggregate reduces but does not eliminate mechanical
load-inflation for large-OI symbols — that residual channel is exactly what CTL-OISHARE is
preregistered to expose. (d) OI statistics on some venues are misquoted (Giagkiozis 2024,
*Ledger*, carried from the lane's V13 packet): only owner-staged archived records with native
snapshot stamps are read, failing closed on missing rows. (e) One 52-week window may be
regime-specific; fold and drop-one gates are the preregistered guard.

## 4. PIT observable (staged OI daily-metrics availability semantics)

Decision at stamp T reads ONLY records with `available_time_utc <= T` — a decision at T can
never read data dated after T (frozen `p_freeze_v14` PIT authority: staged OI is available at
its daily metrics date stamp; pinned by `research/data_fusion/crypto_compat.py`
`_map_open_interest`, which sets `available_time = create_time`).

| Record | available_time_utc | Use |
|---|---|---|
| `v11_oi_staging_v1` daily OI row per symbol (`oi_data/consolidated/<SYM>_oi.parquet`: `create_time` + `sum_open_interest`; per-file SHA-256 pinned in `research/control/v11_run/oi_staging_manifest.json`) | the row's own `create_time` (the day's LAST 5-minute metrics snapshot — typically 23:55:00Z, occasionally earlier on partial days; stamps are read per row, never assumed) | the daily OI paths of all 19 tradeable symbols: `dlog_s`, the leave-one-out aggregate, `CYC_s`, `SH_s` |
| staged 15m bars (`close`) | bar close time | daily closes for the 90d BTC-beta context |
| `crypto_funding.funding_rate` | funding settlement stamp | **COST ONLY** while held; never read by any signal, ranking or eligibility rule |
| instrument tick size (`price_increment`) | instrument metadata | adverse-tick slippage in base/stress costs |

Derived quantities at stamp T (all from records with stamps <= T):
- Daily log change `dlog_s(d) = ln(OI_s(d)/OI_s(d-1))` over consecutive daily rows; defined
  iff `OI_s(d-1) > 0`, both rows present and finite. For every day d in a window, ALL 19
  tradeable symbols must have rows (the aggregate needs a complete cross-section); any
  missing row fails the window CLOSED (symbol INELIGIBLE at that stamp, no back-fill, no
  partial aggregate) — the manifest pins 417/417 rows per symbol with zero internal gaps, so
  the guard is expected never to fire, but it is enforced.
- Aggregate factor `M(d) = mean over the 18 symbols j != s of dlog_j(d)` (LEAVE-ONE-OUT — s
  excluded so the regressand never appears in the regressor).
- `CYC_s(T)` (anchor `CYC-28D`) = OLS slope of `dlog_s` on `M` over the **28 most recent**
  paired daily changes whose end-row stamps <= T: `Cov(dlog_s, M)/Var(M)`, defined iff
  `Var(M) > 0` (requires 29 consecutive daily rows).
- `CYC_s(T)` (neighbour `CYC-14D`) = same slope over the **14 most recent** paired changes
  (15 rows).
- `SH_s(T)` (control quantity) = mean over the 28 most recent daily rows <= T of
  `OI_s(d) / sum over the 19 tradeable symbols of OI_j(d)` (own share of the staged-universe
  aggregate OI).

**Feasible warmup (stated explicitly).** Staged OI history starts 2025-07-01T23:55Z and the
blind-S0 screen window starts 2025-08-22. First decision stamp is Monday 2025-08-25T00:00Z;
the pre-screen OI warmup pool is 2025-07-01..2025-08-21 (52 daily rows) plus 2025-08-22..24,
i.e. **55 daily rows = 54 daily changes available at the first stamp**. The anchor needs 29
rows and the neighbour 15 — both fit with margin at every stamp. Any construction needing
more (e.g. the ancestor's 56d stock-style window, 57 rows) is **arithmetically infeasible at
the first stamp and is excluded by construction** — a 56d OI window cannot be traded honestly
on this source. The 90d beta-context warmup draws on authorized staged bars from 2024-08-20
(not OI) and is satisfiable.

## 5. Universe, warmup, decision clock, holding, rebalance/fill schedule

- **Universe:** the 19 tradeable symbols = frozen `REQUIRED_SYMBOLS` of
  `research/v12/data_contract.py` MINUS `BTCUSDT` (exactly the 20 staged OI symbols minus the
  benchmark; manifest 20/20 zero gaps). The aggregate factor uses ONLY those 19 symbols.
  BTCUSDT is the context benchmark only and is never ranked, held, or included in the
  aggregate.
- **Window:** blind-S0 screen window 2025-08-22..2026-08-21; OI warmup as section 4 (55 rows
  at the first stamp; anchor 29, neighbour 15); beta warmup from staged bars.
- **Conditioning clock vs decision clock (disclosed reconciliation).** The lane axis mandates
  a DAILY conditioning clock funded by the staged OI cadence: the family feature is a
  regression on the DAILY OI path, refreshed at every daily stamp, which is where the daily
  cadence is load-bearing. The DISCRETIONARY DECISION clock remains the frozen weekly
  schedule — every Monday 00:00:00Z, 52 decisions/365d — because the frozen pre-score
  feasibility floor caps discretionary decisions at 60 per 365d
  (`research/v11/cost_feasibility.py` `FLOOR_MAX_DISCRETIONARY_DECISIONS_PER_365D = 60.0`);
  a literal every-day decision schedule (≈365 decisions) would FAIL that floor, and floors
  cannot be weakened at D1 without an owner amendment. First stamp 2025-08-25T00:00Z; last
  stamp 2026-08-17T00:00Z. Fold-terminal force-flat actions are counted and reported
  separately from discretionary decisions.
- **Folds:** F0 2025-08-22..2025-12-21, F1 2025-12-22..2026-04-21, F2 2026-04-22..2026-08-21;
  1-day purge; force-flat at boundaries (frozen V12 fold contract).
- **Execution lag (ONE, declared):** orders released at T + 15 minutes; fill reference = the
  OPEN price of the first completed 15m bar whose slot-open instant >= T + 15m (the 00:15Z
  bar; its open instant coincides with order release, so no look-ahead). Stress "+1 event
  delay" shifts the fill to the next 15m bar's open.
- **Book construction (hysteresis):** rank eligible symbols by CYC ascending; long tercile =
  lowest 6 (cycle-orthogonal positioning), short tercile = highest 6 (cycle-chasing
  positioning), middle 7 = buffer. Enter a side when the rank enters the tercile; EXIT only
  when the rank crosses beyond the median. Equal weights within a side
  `w = min(0.5/n_side, 0.30)`; `n_side < 2` -> that side's budget stays in cash (no
  renormalization). Gross <= 1.0; `|w| <= 0.30` at every stamp by construction. Side
  membership < 4 at a stamp -> that stamp's rebalance is skipped, previous book held
  (fail-closed). Intended holding spans >= one full week (7d) by construction — satisfies the
  >= 3d median-holding floor.

## 6. Arms (exactly three: anchor + neighbour + causal negative control)

| Arm | ID | Signal | Justification |
|---|---|---|---|
| Anchor | `CYC-28D` | `CYC_s` = 28-change OLS slope of the symbol's daily log OI change on the leave-one-out market aggregate's daily log OI change; long lowest-CYC tercile, short highest-CYC tercile | the mechanism as stated |
| Neighbour | `CYC-14D` | identical construction over the 14 most recent paired daily changes | same mechanism, different justified parameter: halves estimator lag so a leverage-cycle turn two weeks old is reflected in the slope now rather than averaged away, while keeping 14 paired observations; 15-row warmup is feasible at the first stamp whereas any 56d-style horizon is arithmetically infeasible on this source (section 4) |
| Causal negative control | `CTL-OISHARE` | rank DESCENDING on `SH_s` (28-row mean own share of the staged-universe aggregate OI); long lowest-share tercile, short highest-share tercile | the mechanical dominance channel of the anchor: large-OI-share symbols (ETH, SOL, ...) dominate the aggregate mean and load on it by construction, so high cycle-beta partially proxies dominance; this control retains the dominance exposure and deletes every co-movement estimate — it separates the family from a size/dominance artifact |

**Preregistered control rule (the control MUST NOT reproduce the anchor):** IF the anchor
`CYC-28D` passes {after-cost expectancy > 0, position PF >= 1.10, >= 2/3 folds positive},
THEN `CTL-OISHARE` must fail at least one of those three gates. If `CTL-OISHARE` also passes
all three, the edge is an OI-dominance effect and `A14-V14-A8-OICYC` is FALSIFIED as a
cycle-participation mechanism. The control contains no differencing, no regression and no OI
flow direction — it cannot re-run the ancestor's OI-flow sign (see section 11). It uses no
funding signal and is evaluated under the identical clock, costs, folds and gates as the
anchor.

## 7. Incremental test vs buy-and-hold AND BTC-beta context

Per chronological fold f in {F0, F1, F2}, on the anchor's net (after-cost,
funding-cost-inclusive) arm return:
- `excess_bh_f = arm_net_f − BTC_buy_and_hold_f` (BTCUSDT perp, same fold window, identical
  force-flat convention);
- `excess_beta_f = arm_net_f − beta_p * BTC_f`, `beta_p` = trailing 90d daily regression beta
  of the arm's mark-to-market daily returns vs BTCUSDT daily returns (daily closes from
  completed 15m bars), estimated PIT at the fold's first decision stamp and held fixed over
  the fold.

**Gate (Stage-A, unrelaxed):** both excess series positive in >= 2/3 folds. This gate is
decisive for OICYC's identity: its factor is a POSITIONING cycle, and any residual
explanation via the PRICE cycle (market beta) is a falsification, not a finding.

## 8. Costs, floors, concentration, drop-one (remediated kernel)

- **Base costs (remediated kernel, L-V14-0):** charged on FILLS ONLY — never per
  holding-day, never per stamp on open positions — using the frozen adapter arithmetic
  (`GenericStrategyBase.rebalance_cost_between`): taker fee bps per side + adverse tick
  slippage floor with REAL per-instrument tick sizes from perp metadata (no uniform stubs);
  native funding settlements accrue exactly ONCE per settlement inside `[ts_opened,
  ts_closed]` at the symbol's own cadence (8h/4h/1h mixed) — COST ONLY. Scored cells report
  cost broken out by fills vs holding terms.
- **Stress costs:** frozen cell — fee x1.5, +2 adverse ticks, +1 event delay (tiers differ
  from base and from each other under the remediated kernel).
- **Floors (pre-score schedule-only feasibility gate `research/v11/cost_feasibility.py` must
  PASS before any scoring):** base drag <= 8%/yr of average gross; stressed <= 12%/yr; <= 60
  discretionary decisions/365d (weekly = 52); median intended holding >= 3d (>= 7d by
  construction); no single symbol > 25% of total one-way turnover (hysteresis keeps
  membership churn inside the floors).
- **Concentration:** `|w| <= 0.30` at every stamp by construction; gross <= 1.0;
  largest-symbol positive-PnL share <= 0.70 is a Stage-A outcome gate (not designed around).
- **Sample floors:** 52 weekly decisions on the screen window (>= 15 per fold); per-side
  membership >= 4 at >= 95% of stamps; signal availability >= 95% of stamps.
- **Zero-position refusal:** an arm that would publish zero positions or fewer than 30
  completed decisions is REFUSED at publication, never scored as a zero baseline (L-V11-4 /
  minimum-activity freeze).
- **Drop-one design:** at every decision stamp, drop the HELD symbol with maximum `|weight|`
  (tie-break: ascending symbol name); remaining weights UNCHANGED — no post-score
  renormalization; full schedule rerun. Non-vacuous iff the dropped book differs from the
  anchor book at >= 50% of stamps with the dropped symbol held at those stamps. Drop-one may
  not flip any family verdict to PASS and is reported per Stage-A gate.

## 9. Failure interpretation

1. **Anchor fails expectancy/PF/folds:** the cycle-participation discount is absent or
   sign-wrong in this universe/window after costs -> family falsified; no rescue, no window
   or parameter search.
2. **Anchor passes, CTL-OISHARE passes too:** the edge is an OI-dominance/size artifact, not
   co-movement information -> falsified as a cycle-participation mechanism.
3. **Beta-context excess non-positive in >= 2 folds:** the returns are PRICE-beta
   repackaging -> not incremental; falsified.
4. **Neighbour contradicts or is fold-unstable:** the slope estimate is window-fragile ->
   falsified.
5. **Largest fold-positive share > 50%:** single-regime artifact; falsified.
6. **A7-N |rho| > 0.20 vs the frozen OILEV-V2 anchor OR its inverted control:** INELIGIBLE
   under the Section 1.1 gate (selection ineligibility, not a scored mechanism verdict);
   proposal withdrawn.
7. **Feasibility floors FAIL:** schedule redesign allowed pre-score only; if unachievable
   without weakening a frozen floor -> withdraw, do not score.
8. **Drop-one vacuous:** max-|w| symbol not actually held -> arm invalid, rerun refused.
9. **Signal availability < 95%:** data insufficiency -> selection/BLOCKED refusal, NOT a
   mechanism verdict.
10. **Zero positions / < 30 completed decisions:** publication refused (not a PASS).

## 10. Source-to-test map (staged parquet -> field -> join plan; NO downloads)

| Source (machine-local, archived) | Field | Exact test use |
|---|---|---|
| `oi_data/consolidated/<SYM>_oi.parquet` (SHA-256 per file pinned in `research/control/v11_run/oi_staging_manifest.json`; provenance `oi_data/metrics_daily/<SYM>/<SYM>-metrics-<date>.zip`, 417 daily files/symbol) | `create_time`, `sum_open_interest` | the 19 symbols' daily OI paths: `dlog_s`, leave-one-out aggregate `M(d)`, `CYC_s` (anchor + neighbour) and `SH_s` (control); availability stamp = `create_time`; join by symbol x day-row (complete cross-section required per window); **no re-fetch from Binance Vision is performed or permitted — the staged set is closed at 2026-08-21 and already covers the screen window end** |
| staged 15m bars (`crypto_bars.close`) | close | daily closes for the 90d beta context; fill references and turnover accounting |
| staged funding settlements | `funding_rate` | COST ONLY, accrued once per settlement while held; excluded from every signal, rank and eligibility rule |
| instrument metadata | `price_increment` | adverse-tick slippage in base costs and the +2-tick stress |
| BTCUSDT bars | close | benchmark/context only (buy-and-hold and beta leg); never ranked, never held, never inside the aggregate factor |

Declared non-use: the metrics ZIPs carry additional columns
(`sum_open_interest_value`, long/short and taker ratio columns). **This family reads ONLY
`sum_open_interest`**; the other columns are not loaded, and the P2-closed
`/futures/data/*` ratio sources are not touched (no downloads, no new source, no keys).

## 11. Forbidden-packet self-check (mapping vs the inventory, distinctions stated plainly)

| Inventory class | Why OICYC is NOT a variant/inversion/rescue/renaming |
|---|---|
| `V12-OILEV-V2` (CRITICAL — the ancestor whose inverted control defines this region) | The ancestor's feature is a two-point cumulative first moment: 28d log OI GROWTH `log(OI_T/OI_{T-28d})` — the net DIRECTION of the symbol's OWN book. OICYC's feature is a market-RELATIVE regression SLOPE: sensitivity of the symbol's daily OI flow to the other 18 symbols' flow. The two orderings disagree by construction: identical absolute growth can carry any slope (doubling WITH the market vs AGAINST a flat market), and a zero-growth book can carry a high slope (co-moving churn around a flat level). No parameter of OICYC reproduces the ancestor's statistic, and the ancestor's inversion (long shrinking OI) is not expressible as a cycle-beta sort. The predicted sign (long LOW cycle-beta) is derived from the procyclical-leverage/crowded-unwind mechanism, not copied from the V12 control arm; whether the books coincide is exactly what the preregistered D2 gate decides (|rho| <= 0.20 vs the anchor AND its inverted control, else INELIGIBLE). The conditioning QUESTION differs: not "which way is this book drifting" but "whose positioning rides the market-wide leverage cycle". |
| `V11-OILEVER-DELEV` (reserved; blocked pre-score) | Same ancestor class as V12-OILEV-V2 (weekly quintiles of OI growth); the same transform distinction applies; the 0.30 cap is respected by construction and never raised. |
| `V13-OITD-TERM-STRUCTURE` (+ near-duplicates EXITCAP, CAPVEL) | OITD ranks an OI LEVEL relative to a TURNOVER LEVEL (unwind duration). OICYC's anchors use only OI CHANGES (the aggregate is a mean of changes, not a level) — no OI level, no turnover term, no duration construct in the family signal. `SH_s` (an OI-level share) appears ONLY inside the control designed to be refuted — the same control discipline V13's OITD used for its turnover term. |
| `V13-LIQEPIS` (+ duplicates LIQPRO, TCH) | No liquidity-episode or turnover-shape construct; the anchor reads ZERO bar records (bars enter only the beta context and cost accounting). |
| `V12-BAB-LOWBETA` | The anchor is a POSITIONING-flow slope, not a price-beta sort; no price return enters the feature anywhere, and no beta model is retuned. The price beta of the BOOK appears only as the benchmark-context gate (section 7), where failure falsifies. |
| `V6/V1-CARRY-FUNDING` | Funding never appears in any signal, ranking or eligibility rule; cost-only while held. No crowding-premium/carry rescue — the signal cannot see funding. |
| `V4-XSECT-MOM`, `V8R-XSECT-REVERSAL`, `V9-TS-TREND`, `WEEKLY-REVERSAL/MR-RESCUE` | No past-price-return term exists in any anchor feature — the ranking is return-free by construction. |
| `V1-VOLCOMP`, `V9` dollar-volume shock continuation | No breakout/continuation rule, no threshold crossing, no volume term; the slope is a within-window co-moment, not a spike or shock detector. |
| `V11-LOTTERY-MAX-SKEW` | No LOT/MAX/idiosyncratic-skew feature. |
| `V11-ILLIQ-AMIHUD`, `V12-ILLIQ-REPLICATION` | No `|r|/dollar-volume` impact measure; the Amihud replication brief is not re-opened. |
| `V10-M01-AGGRESSOR-ABSORPTION` | No aggressor/taker-flow panel; the staged metrics' taker-ratio columns are declared NOT-read (section 10). |
| `V12-ILLIQ-REPLICATION`, `DATA-GATED` | Only machine-local archived staged files are read; no new source, no credentials, no downloads, no network fetches. |

**Control sanity (own falsification control, not an ancestor re-run):** CTL-OISHARE contains
no differencing and no OI-flow direction — it is an OI-level share sort — so it cannot
re-run the anchor's or the ancestor's OI-flow sign; its preregistered role is to be refuted
if the anchor is genuine.

**Lane-cluster note (wave diversity):** OICYC and its lane-mate OICH are both AXIS-3
proposals; under the Section 1.2 wave-diversity rule at most ONE of them can ever be
selected (a second family inside a selected cluster is ineligible even if otherwise clean).
Neither proposal requests otherwise.

## 12. Plan Section 1.1 disclosures (shadow-effect region — required verbatim items a–f)

`run_contract.shadow_region_rule`: "inverted-OI-flow shadow (+0.758 raw, V12 OILEV-V2-INV
control arm) front door measured-open under the V13 terms: new economic mechanism in its own
words; disclosure that the sign was observed in a V12 control; confirmatory status recorded
in verdict and denominator; own falsification control; |rho| <= 0.20 vs the OILEV-V2 anchor
AND its inverted control; no gate relaxation."

- **(a) New economic mechanism in its own words.** OICYC conditions on the market-relative
  co-movement of positioning flow (regression slope vs the leave-one-out aggregate) with the
  procyclical-leverage / crowded-unwind mechanism of section 1 — it is NOT a sign-flip,
  renaming or parameter rescue of OILEV-V2 (see section 11, critical row). The
  `V12-OILEV-V2` class in the forbidden inventory forbids "sign flip, horizon tweak, cost
  exemption, universe carve-out, threshold relaxation, renaming as a new mechanism"; none of
  these is used, and the transform distinction is stated mathematically.
- **(b) Explicit disclosure of the control-arm observation.** The sign region was observed in
  the V12 `OILEV-V2-28D-FLOW-W-INV` causal control arm, which earned +0.758 raw while the
  anchor lost (-0.821) — a measured shadow effect from a control arm (L-V12-1), recorded in
  the hypothesis ledger's falsification-by-control cluster. It is untested as a front-door
  family; V13 did not enter it. This proposal enters that region and carries the disclosure.
- **(c) Confirmatory status recorded in verdict and denominator.** Section 2 preregisters the
  family CONFIRMATORY: if selected, every scored cell of this family is marked confirmatory
  in the verdict record and in the observed/published denominator accounting, with all
  Stage-A gates unrelaxed. Positive raw PnL never overrides failed incremental context or a
  firing control.
- **(d) Own falsification control.** CTL-OISHARE (section 6) is preregistered here, is
  family-specific (it arms against the mechanical dominance channel of the slope), and does
  not merely re-run the anchor sign — it contains no OI-flow direction at all.
- **(e) D2 decorrelation gate.** At D2, A7-N will measure |rho| between this family and BOTH
  the OILEV-V2 anchor AND its inverted control on the common window; the proposal is
  INELIGIBLE unless |rho| <= 0.20 vs BOTH. This gate is stated here as binding and is
  repeated as falsifier #6; it is measured by A7-N, not self-attested.
- **(f) No gate relaxation.** Every frozen Stage-A gate (plan Section 12;
  `run_contract.stage_a_gates`) and every frozen pre-score feasibility floor applies
  unchanged; no threshold, fold, cost or universe adjustment of any kind is requested.

## 13. Family / budget note

This proposal is ONE family (`OICYC`), distinct from its lane-mate `OICH` (different
conditioning construct — cross-symbol slope vs own-path dispersion; different control); if
selected at D1 it consumes 3 scored cells (anchor, neighbour, control) of the 6-cell ceiling
across the <= 2-family selection (budget 9, unused slots never reassigned). Exactly three
arms; no fourth arm may be added post-hoc. All cells preregistered CONFIRMATORY (item c
above).

---

OUTCOME-BLIND ATTESTATION
lane: a8  proposal: A14-V14-A8-OICYC  cycle: CRYPTO-V14
wave_sha: c3e3c90561efc972c487a99951ca0f6031ab4fa34907d1c10890d1795b4da4a8
I wrote this mechanism and its falsification conditions before computing any return, metric
or ranking, and without access to any scored artifact or outcome file. No per-arm outcome
data was provided or read; no post-outcome modification of this proposal is permitted.
utc: 2026-09-05T00:39:27Z  agent: a8 (d1-a8-proposals, branch orca/v14-d1-a8-proposals)
