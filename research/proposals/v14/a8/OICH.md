# A14-V14-A8-OICH — Open-Interest Churn Dispersion (positioning-stability conditioning)

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

**Hypothesis ID: `A14-V14-A8-OICH`** (lexicographically comparable, uppercase, no spaces).

**Mechanism (one paragraph).** The STABILITY of a symbol's aggregate position book — how
violently its open interest swings day to day, regardless of direction — is a measurable
property of who holds it. OICH measures it as the trailing dispersion of the symbol's DAILY
open-interest path: `CH_s(T) = std(ddof=1){ dlog_s(d) }` over the 28 most recent daily log
open-interest changes whose end-row stamps are <= T (the second moment of the OI path — a
direction-free transform: a book that round-trips wildly with zero net monthly change scores
HIGH, and a book that grows monotonically by a steady daily drip scores LOW). Economic
counterparty: in high-churn books the marginal holder is short-horizon leveraged traffic that
opens and closes wholesale (hot money); in low-churn books the inventory is sticky,
conviction- or hedge-driven capital. Why the edge exists: hot-money books repeatedly set the
marginal price during impatient, one-sided bursts taken from thin temporary books, and the
transient impact of those bursts reverts once the churn passes (Admati & Pfleiderer 1988
participation clustering; De Long, Shleifer, Summers & Waldmann 1990: noise-trader-dominated
assets carry the risk that the crowd exits together); crypto liquidation-cascade evidence
shows leveraged position swings convert into forced, price-moving exits (arXiv 2102.04591,
BitMEX liquidation data; SSRN 6920018 auto-deleveraging). **Predicted sign: symbols with LOW
open-interest churn outperform symbols with HIGH churn over the following week**; the anchor
is long the lowest-CH tercile and short the highest-CH tercile. **Null that kills it:** the
after-cost low-minus-high churn spread is non-positive in this universe/window, or the spread
is reproduced by a pure price-volatility sort that contains no OI information (section 6).

OICH conditions on the **second moment of the daily OI path** (positioning-flow stability).
Its signal contains no two-point OI growth, no OI level or percentile, no price return, no
turnover term and no funding term anywhere in the feature.

## 2. Falsifiable prediction (confirmatory status recorded)

The anchor arm, after base costs on the blind-S0 screen window (2025-08-22..2026-08-21, folds
F0/F1/F2 chronological with 1-day purge), passes: after-cost expectancy > 0, position PF
>= 1.10, at least 2/3 chronological folds positive; excess over BTC buy-and-hold AND over the
BTC-beta context is positive in >= 2/3 folds; and the price-volatility causal control arm
fails at least one of the anchor's three gates.

**This family is preregistered CONFIRMATORY** (shadow-region entry, plan Section 1.1): if
selected at D1, all three of its scored cells carry that status in the verdict record and in
the observed/published denominator accounting, and every Stage-A gate applies unrelaxed.

**FALSIFIED if any of:**
1. the anchor fails any of the three gates above (the positioning-stability premium is
   absent or sign-wrong in this universe/window after costs);
2. the anchor passes but CTL-PRICEVOL also passes all three gates (the edge is the documented
   volatility-LEVEL effect — the measured vol-level sorting shadow — and the OI-churn
   information is redundant);
3. excess vs the BTC-beta context is non-positive in >= 2 folds (beta repackaging, not
   incremental information);
4. the 14d neighbour contradicts the anchor's sign or is unstable across folds (the churn
   statistic is window-fragile, not a robust mechanism);
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
| L1 | "De Long Shleifer Summers Waldmann 1990 \"noise trader risk\" journal of political economy" | 2026-09-05T00:21Z | ACCEPT | De Long, Shleifer, Summers & Waldmann (1990), *JPE* 98(4) 703–738 — noise-trader-created risk deters arbitrage and lets crowd-driven assets carry a sentiment-cycle premium/risk. Primary anchor for the hot-money-book mechanism. |
| L2 | "Adrian Shin 2010 \"liquidity and leverage\" procyclical leverage financial intermediaries" | 2026-09-05T00:21Z | ACCEPT (context) | Adrian & Shin (2010), *JFI* 19(3) 418–437 — leverage is procyclical; balance sheets expand in booms and contract in busts. Context: leveraged-book dynamics are cycle-shaped, which motivates the lane-mate cycle construct (OICYC) and contrasts with OICH's own-path stability question. |
| L3 | "Brunnermeier Pedersen 2009 \"market liquidity and funding liquidity\" Review of Financial Studies margin spirals" | 2026-09-05T00:22Z | ACCEPT | Brunnermeier & Pedersen (2009), *RFS* 22(6) 2201–2238 — liquidity spirals: forced exits amplify moves. Supports the churn->forced-exit->transient-impact channel. Caveat: crisis-era marginated markets; transfer to 24/7 instant-margin perps is qualitative. |
| L4 | "bitcoin perpetual futures open interest deleveraging liquidation cascade price impact study" | 2026-09-05T00:23Z | ACCEPT (caveat) | Liquidation/leverage in crypto futures measured on venue data (arXiv 2102.04591 — BitMEX liquidations and optimal margin; SSRN 6920018 — auto-deleveraging and solvency fragility). Documents that violent position-book swings convert into forced, price-moving exits. Caveat: single-venue studies; OICH claims an ex-ante stability association, not a cascade event prediction. |
| L5 | "Karpoff 1987 \"relation between price changes and trading volume\"" | 2026-09-05T00:37Z | ACCEPT (confound warning) | Karpoff (1987), *JFQA* 22(1) 109–126 — activity/volume and price-change dispersion co-move. This is exactly the churn-vs-volatility confound; motivates CTL-PRICEVOL as the causal negative control. |
| L6 | "data.binance.vision futures um daily metrics zip files sum_open_interest documentation" | 2026-09-05T00:38Z | ACCEPT (venue semantics) | Binance public data collection (`data.binance.vision`, `data/futures/um/daily/metrics/`; `github.com/binance/binance-public-data`) — daily metrics ZIPs carrying `create_time` and `sum_open_interest` at 5-minute rows, mirroring the `openInterestHist` fields. Matches the staged capture pinned by `research/control/v11_run/oi_staging_manifest.json`; availability stamps follow the frozen `p_freeze_v14` PIT authority (staged OI at the daily metrics date stamp). |

**Primary-source claims used:** (i) crowd/hot-money dominance creates risk and transient
price pressure that reverts (L1, L3); (ii) violent position-book swings produce forced,
price-moving exits in crypto perps (L4); (iii) activity dispersion and price dispersion
co-move, so a price-volatility control must arm the family (L5).

**Crypto-perpetual transfer caveats.** (a) The noise-trader and spiral literatures are
session-structured and equity/intermediary-based; a 24/7 instant-margin perp book has no
margin cycle — the analog is qualitative. (b) sum_open_interest counts BASE units and is
venue-wide for the symbol on Binance USD-M only; cross-venue positioning (spot holders,
other exchanges) is invisible, so "book stability" is a Binance-perp-book property. (c) OI
statistics on some venues are misquoted (Giagkiozis 2024, *Ledger*, carried from the lane's
V13 packet): the design reads only owner-staged archived records with native snapshot stamps
and fails closed on missing rows. (d) Churn measured from daily rows cannot distinguish
one large account's round-trip from many small ones — the statistic measures aggregate
instability, not participant count. (e) One 52-week window may be regime-specific; fold and
drop-one gates are the preregistered guard.

## 4. PIT observable (staged OI daily-metrics availability semantics)

Decision at stamp T reads ONLY records with `available_time_utc <= T` — a decision at T can
never read data dated after T (frozen `p_freeze_v14` PIT authority: staged OI is available at
its daily metrics date stamp; pinned by `research/data_fusion/crypto_compat.py`
`_map_open_interest`, which sets `available_time = create_time`).

| Record | available_time_utc | Use |
|---|---|---|
| `v11_oi_staging_v1` daily OI row per symbol (`oi_data/consolidated/<SYM>_oi.parquet`: `create_time` + `sum_open_interest`; per-file SHA-256 pinned in `research/control/v11_run/oi_staging_manifest.json`) | the row's own `create_time` (the day's LAST 5-minute metrics snapshot — typically 23:55:00Z, occasionally earlier on partial days; stamps are read per row, never assumed) | the daily OI path: all churn statistics |
| staged 15m bars (`close`) | bar close time | daily closes for CTL-PRICEVOL and the 90d BTC-beta context |
| `crypto_funding.funding_rate` | funding settlement stamp | **COST ONLY** while held; never read by any signal, ranking or eligibility rule |
| instrument tick size (`price_increment`) | instrument metadata | adverse-tick slippage in base/stress costs |

Derived quantities at stamp T (all from records with stamps <= T):
- Daily log change `dlog_s(d) = ln(OI_s(d)/OI_s(d-1))` over consecutive daily rows of symbol
  s; defined iff `OI_s(d-1) > 0` and both rows present and finite. Consecutive-ness is by
  day-row index; a missing or malformed row fails the window CLOSED (symbol INELIGIBLE at
  that stamp, no back-fill) — the manifest pins 417/417 rows per symbol with zero internal
  gaps for the staged window, so the guard is expected never to fire, but it is enforced.
- `CH_s(T)` (anchor `CH-28D`) = sample std (ddof=1) of the **28 most recent** `dlog_s`
  whose end-row stamps <= T (requires 29 consecutive daily rows).
- `CH_s(T)` (neighbour `CH-14D`) = same over the **14 most recent** (15 rows).

**Feasible warmup (stated explicitly).** Staged OI history starts 2025-07-01T23:55Z and the
blind-S0 screen window starts 2025-08-22. First decision stamp is Monday 2025-08-25T00:00Z;
the pre-screen OI warmup pool is 2025-07-01..2025-08-21 (52 daily rows) plus the three
screen-start days before the first stamp (2025-08-22..24), i.e. **55 daily rows = 54 daily
changes available at the first stamp**. The anchor needs 29 rows and the neighbour 15 — both
fit with margin at every stamp. Any construction needing more (e.g. the ancestor's 56d
stock-style window, 57 rows) is **arithmetically infeasible at the first stamp and is
excluded by construction** — a 56d OI window cannot be traded honestly on this source. The
90d beta-context warmup draws on authorized staged bars from 2024-08-20 (not OI) and is
satisfiable.

## 5. Universe, warmup, decision clock, holding, rebalance/fill schedule

- **Universe:** the 19 tradeable symbols = frozen `REQUIRED_SYMBOLS` of
  `research/v12/data_contract.py` MINUS `BTCUSDT` (exactly the 20 staged OI symbols minus the
  benchmark; manifest 20/20 zero gaps). BTCUSDT is the context benchmark only and is never
  ranked or held.
- **Window:** blind-S0 screen window 2025-08-22..2026-08-21; OI warmup as section 4 (55 rows
  at the first stamp; anchor 29, neighbour 15); beta warmup from staged bars.
- **Conditioning clock vs decision clock (disclosed reconciliation).** The lane axis mandates
  a DAILY conditioning clock funded by the staged OI cadence: the family feature is defined
  on the DAILY OI path and is refreshed at every daily stamp, which is where the daily
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
- **Book construction (hysteresis):** rank eligible symbols by CH ascending; long tercile =
  lowest 6 (stable books), short tercile = highest 6 (churned books), middle 7 = buffer.
  Enter a side when the rank enters the tercile; EXIT only when the rank crosses beyond the
  median. Equal weights within a side `w = min(0.5/n_side, 0.30)`; `n_side < 2` -> that
  side's budget stays in cash (no renormalization). Gross <= 1.0; `|w| <= 0.30` at every
  stamp by construction. Side membership < 4 at a stamp -> that stamp's rebalance is skipped,
  previous book held (fail-closed). Intended holding spans >= one full week (7d) by
  construction — satisfies the >= 3d median-holding floor.

## 6. Arms (exactly three: anchor + neighbour + causal negative control)

| Arm | ID | Signal | Justification |
|---|---|---|---|
| Anchor | `OICH-28D` | `CH_s` = 28-change daily OI-churn dispersion; long lowest-CH tercile, short highest-CH tercile | the mechanism as stated |
| Neighbour | `OICH-14D` | identical construction over the 14 most recent daily changes | same mechanism, different justified parameter: halves estimator lag so a participation-regime shift two weeks old is reflected now rather than averaged away, while still using 14 daily observations; 15-row warmup is feasible at the first stamp whereas any 56d-style horizon is arithmetically infeasible on this source (section 4) |
| Causal negative control | `CTL-PRICEVOL` | rank ASCENDING on the sample std (ddof=1) of the 28 most recent DAILY log close returns (daily closes from completed 15m bars); long lowest-vol tercile, short highest-vol tercile | the mechanical co-exposure of the anchor: churned OI co-occurs with volatile price action (Karpoff 1987 activity-dispersion relation), so a low-churn book mechanically correlates with low realized vol; this control retains that exposure and deletes every OI quantity — it separates the family from the documented vol-level sorting shadow observation |

**Preregistered control rule (the control MUST NOT reproduce the anchor):** IF the anchor
`OICH-28D` passes {after-cost expectancy > 0, position PF >= 1.10, >= 2/3 folds positive},
THEN `CTL-PRICEVOL` must fail at least one of those three gates. If `CTL-PRICEVOL` also
passes all three, the edge is a volatility-level effect and `A14-V14-A8-OICH` is FALSIFIED as
a positioning-stability mechanism. The control contains no OI input at all and therefore does
not — and cannot — re-run the ancestor's OI-flow sign (see section 11). It uses no funding
signal and is evaluated under the identical clock, costs, folds and gates as the anchor.

## 7. Incremental test vs buy-and-hold AND BTC-beta context

Per chronological fold f in {F0, F1, F2}, on the anchor's net (after-cost,
funding-cost-inclusive) arm return:
- `excess_bh_f = arm_net_f − BTC_buy_and_hold_f` (BTCUSDT perp, same fold window, identical
  force-flat convention);
- `excess_beta_f = arm_net_f − beta_p * BTC_f`, `beta_p` = trailing 90d daily regression beta
  of the arm's mark-to-market daily returns vs BTCUSDT daily returns (daily closes from
  completed 15m bars), estimated PIT at the fold's first decision stamp and held fixed over
  the fold.

**Gate (Stage-A, unrelaxed):** both excess series positive in >= 2/3 folds. Failure of either
in >= 2 folds falsifies the family's incremental-information claim.

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

1. **Anchor fails expectancy/PF/folds:** the positioning-stability premium is absent or
   sign-wrong in this universe/window after costs -> family falsified; no rescue, no window
   or parameter search.
2. **Anchor passes, CTL-PRICEVOL passes too:** the edge is the volatility-level effect (the
   documented shadow), not OI churn -> falsified as a positioning-stability mechanism.
3. **Beta-context excess non-positive in >= 2 folds:** BTC-beta repackaging -> not
   incremental; falsified.
4. **Neighbour contradicts or is fold-unstable:** the churn statistic is window-fragile ->
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
| `oi_data/consolidated/<SYM>_oi.parquet` (SHA-256 per file pinned in `research/control/v11_run/oi_staging_manifest.json`; provenance `oi_data/metrics_daily/<SYM>/<SYM>-metrics-<date>.zip`, 417 daily files/symbol) | `create_time`, `sum_open_interest` | the daily OI path for `dlog_s`, `CH_s` (anchor + neighbour); availability stamp = `create_time`; join by symbol x day-row; **no re-fetch from Binance Vision is performed or permitted — the staged set is closed at 2026-08-21 and already covers the screen window end** |
| staged 15m bars (`crypto_bars.close`) | close | daily closes for CTL-PRICEVOL's realized volatility and the 90d beta context; fill references and turnover accounting |
| staged funding settlements | `funding_rate` | COST ONLY, accrued once per settlement while held; excluded from every signal, rank and eligibility rule |
| instrument metadata | `price_increment` | adverse-tick slippage in base costs and the +2-tick stress |
| BTCUSDT bars | close | benchmark/context only (buy-and-hold and beta leg); never ranked, never held |

Declared non-use: the metrics ZIPs carry additional columns
(`sum_open_interest_value`, long/short and taker ratio columns). **This family reads ONLY
`sum_open_interest`**; the other columns are not loaded, and the P2-closed
`/futures/data/*` ratio sources are not touched (no downloads, no new source, no keys).

## 11. Forbidden-packet self-check (mapping vs the inventory, distinctions stated plainly)

| Inventory class | Why OICH is NOT a variant/inversion/rescue/renaming |
|---|---|
| `V12-OILEV-V2` (CRITICAL — the ancestor whose inverted control defines this region) | The ancestor's feature is a two-point cumulative first moment: 28d log OI GROWTH `log(OI_T/OI_{T-28d})` — the net DIRECTION of the book over a month. OICH's feature is the second moment of the DAILY path — the DISPERSION of day-to-day changes, direction-free by construction. No parameter of OICH reproduces the ancestor's statistic: setting any window of a std of daily changes yields a dispersion, never a two-point endpoint ratio; the ancestor's inversion (long shrinking OI) is not expressible as a churn sort. The predicted sign (long LOW churn) is derived from the hot-money/transient-impact mechanism, not copied from the V12 control arm; whether the books coincide is exactly what the preregistered D2 gate decides (|rho| <= 0.20 vs the anchor AND its inverted control, else INELIGIBLE). The conditioning QUESTION differs: not "which way is the book drifting" but "whose book is churned by short-horizon traffic". |
| `V11-OILEVER-DELEV` (reserved; blocked pre-score) | Same ancestor class as V12-OILEV-V2 (weekly quintiles of OI growth); the same transform distinction applies; the 0.30 cap is respected by construction and never raised. |
| `V13-OITD-TERM-STRUCTURE` (+ near-duplicates EXITCAP, CAPVEL) | OITD ranks an OI LEVEL relative to a TURNOVER LEVEL (unwind duration). OICH's anchors use only OI CHANGES — no OI level, no turnover term, no duration construct anywhere in the signal. |
| `V13-LIQEPIS` (+ duplicates LIQPRO, TCH) | No liquidity-episode or turnover-shape construct; the anchor reads ZERO bar records (bars enter only the control designed to be refuted, the beta context and cost accounting). |
| `V12-BAB-LOWBETA` | No price-beta sort; beta appears only as benchmark context (section 7). |
| `V6/V1-CARRY-FUNDING` | Funding never appears in any signal, ranking or eligibility rule; cost-only while held. No crowding-premium/carry rescue — the signal cannot see funding. |
| `V4-XSECT-MOM`, `V8R-XSECT-REVERSAL`, `V9-TS-TREND`, `WEEKLY-REVERSAL/MR-RESCUE` | No past-price-return term exists in any anchor feature — the ranking is return-free by construction (price closes enter only the control, the beta context and accounting). |
| `V1-VOLCOMP`, `V9` dollar-volume shock continuation | No breakout/continuation rule, no threshold crossing, no volume term; the churn statistic is a within-window dispersion, invariant to the LEVEL and net DIRECTION of OI. |
| `V11-LOTTERY-MAX-SKEW` | No LOT/MAX/idiosyncratic-skew feature. |
| `V11-ILLIQ-AMIHUD`, `V12-ILLIQ-REPLICATION` | No `|r|/dollar-volume` impact measure; the Amihud replication brief is not re-opened. |
| `V10-M01-AGGRESSOR-ABSORPTION` | No aggressor/taker-flow panel; the staged metrics' taker-ratio columns are declared NOT-read (section 10). |
| `V12-ILLIQ-REPLICATION`, `DATA-GATED` | Only machine-local archived staged files are read; no new source, no credentials, no downloads, no network fetches. |

**Control sanity (own falsification control, not an ancestor re-run):** CTL-PRICEVOL contains
no OI quantity whatsoever, so it cannot re-run the anchor's or the ancestor's OI-flow sign;
its preregistered role is to be refuted if the anchor is genuine.

**Lane-cluster note (wave diversity):** OICH and its lane-mate OICYC are both AXIS-3
proposals; under the Section 1.2 wave-diversity rule at most ONE of them can ever be
selected (a second family inside a selected cluster is ineligible even if otherwise clean).
Neither proposal requests otherwise.

## 12. Plan Section 1.1 disclosures (shadow-effect region — required verbatim items a–f)

`run_contract.shadow_region_rule`: "inverted-OI-flow shadow (+0.758 raw, V12 OILEV-V2-INV
control arm) front door measured-open under the V13 terms: new economic mechanism in its own
words; disclosure that the sign was observed in a V12 control; confirmatory status recorded
in verdict and denominator; own falsification control; |rho| <= 0.20 vs the OILEV-V2 anchor
AND its inverted control; no gate relaxation."

- **(a) New economic mechanism in its own words.** OICH conditions on the stability of the
  position book (second moment of the daily OI path) with the hot-money churn mechanism of
  section 1 — it is NOT a sign-flip, renaming or parameter rescue of OILEV-V2 (see section
  11, critical row). The `V12-OILEV-V2` class in the forbidden inventory forbids "sign flip,
  horizon tweak, cost exemption, universe carve-out, threshold relaxation, renaming as a new
  mechanism"; none of these is used, and the transform distinction is stated mathematically.
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
- **(d) Own falsification control.** CTL-PRICEVOL (section 6) is preregistered here, is
  family-specific (it arms against the vol-level co-exposure), and does not merely re-run the
  anchor sign — it contains no OI term at all.
- **(e) D2 decorrelation gate.** At D2, A7-N will measure |rho| between this family and BOTH
  the OILEV-V2 anchor AND its inverted control on the common window; the proposal is
  INELIGIBLE unless |rho| <= 0.20 vs BOTH. This gate is stated here as binding and is
  repeated as falsifier #6; it is measured by A7-N, not self-attested.
- **(f) No gate relaxation.** Every frozen Stage-A gate (plan Section 12;
  `run_contract.stage_a_gates`) and every frozen pre-score feasibility floor applies
  unchanged; no threshold, fold, cost or universe adjustment of any kind is requested.

## 13. Family / budget note

This proposal is ONE family (`OICH`); if selected at D1 it consumes 3 scored cells (anchor,
neighbour, control) of the 6-cell ceiling across the <= 2-family selection (budget 9, unused
slots never reassigned). Exactly three arms; no fourth arm may be added post-hoc. All cells
preregistered CONFIRMATORY (item c above).

---

OUTCOME-BLIND ATTESTATION
lane: a8  proposal: A14-V14-A8-OICH  cycle: CRYPTO-V14
wave_sha: c3e3c90561efc972c487a99951ca0f6031ab4fa34907d1c10890d1795b4da4a8
I wrote this mechanism and its falsification conditions before computing any return, metric
or ranking, and without access to any scored artifact or outcome file. No per-arm outcome
data was provided or read; no post-outcome modification of this proposal is permitted.
utc: 2026-09-05T00:39:27Z  agent: a8 (d1-a8-proposals, branch orca/v14-d1-a8-proposals)
