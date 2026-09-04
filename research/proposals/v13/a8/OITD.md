# A13-V13-A8-OITD — Open-Interest-to-Turnover Unwind Duration (cross-sectional positioning structure)

Lane: a8 | Cycle: CRYPTO-V13 | Phase: D1 | Outcome-blind proposal (no returns, PnL,
metrics, rankings or backtests computed; no outcome files seen).
Written against the frozen blind input packet
(`research/proposals/v13/blind_input_packet.md`), the V13 forbidden family
inventory and the run contract only. Conditioning space: positioning/liquidity
information (mission Q2).

---

## 1. Hypothesis ID and mechanism

**Hypothesis ID: `A13-V13-A8-OITD`** (lexicographically comparable, uppercase,
no spaces).

**Mechanism (one paragraph).** The aggregate position book of a Binance USD-M
perpetual is a standing inventory that must eventually be transferred between
traders. OITD measures how large that standing inventory is relative to the
market's capacity to absorb its exit: `D_s = notional_open_interest_s /
avg_daily_dollar_turnover_s(28d)` — the number of days of typical turnover
needed to unwind the symbol's standing open interest (notional OI = 7-stamp
trailing mean of daily OI snapshots, converted to USDT at the latest available
mark price). Economic counterparty: the crowded sticky-inventory holder — slow,
conviction-driven capital that accumulated positions and now faces a
capacity-constrained exit — trading against faster arbitrage capital that can
absorb that unwind. Why the edge exists: when standing inventory is large
relative to daily flow, the marginal holder's exit takes many days of normal
volume; per the liquidity-spiral / predatory-trading logic of Brunnermeier &
Pedersen (2009) and the limits-of-arbitrage argument of Shleifer & Vishny
(1997), such positions are vulnerable to anticipatory trading ahead of their
unwind and to spiral amplification, while the accumulation that built the
position already paid the good entry prices. The futures hedging-pressure
literature (Bessembinder 1992; de Roon, Nijman & Veld 2000) establishes that
structural positioning pressure — not just systematic beta — is priced in
futures markets; OITD is the crypto-perpetual-measurable structural proxy
(no COT-style hedger labels exist there). **Expected sign: symbols with LOW
unwind duration outperform symbols with HIGH unwind duration over the following
week**; the anchor is long the lowest-D tercile, short the highest-D tercile.

OITD conditions on the **stock/flow structure of positioning** (an OI *level*
relative to a turnover *level*). It contains no OI differencing, no OI
direction, no price-return term and no funding term anywhere in its signal.

## 2. Falsifiable prediction

The anchor arm, after base costs on the blind-S0 screen window
(2025-08-22..2026-08-21, folds F0/F1/F2 chronological with 1-day purge), passes:
after-cost expectancy > 0, position PF >= 1.10, at least 2/3 chronological
folds positive; excess over BTC buy-and-hold AND over the BTC-beta context is
positive in >= 2/3 folds; and the pure-turnover causal control arm fails at
least one of the anchor's three gates.

**FALSIFIED if any of:**
1. the anchor fails any of the three gates above (the duration-crowding premium
   is absent or sign-wrong in this universe/window after costs);
2. the anchor passes but CTL-FLOW-ONLY also passes all three gates (the edge is
   a pure turnover-level effect; the OI stock contributes nothing);
3. excess vs the BTC-beta context is non-positive in >= 2 folds (returns are
   beta repackaging, not incremental information);
4. the 56d neighbour contradicts the anchor's sign or is unstable across folds
   (the duration statistic is horizon-fragile, not a robust mechanism);
5. the largest fold-positive share of PnL exceeds 50% (single-regime artifact);
6. A7-N measures |rho| > 0.20 vs the frozen OILEV-V2 anchor OR its inverted
   control on the common window (voluntary novelty commitment, see section 12).

No parameter retune, sign flip, cap change or universe carve-out may be used to
rescue any failure mode above.

## 3. Literature (pass completed BEFORE mechanism finalization)

Search log (web search; batch window 2026-09-04T10:55Z..11:16Z; queries executed
sequentially in the order listed; per-query stamps minute-level, +-3 min;
logged per the packet requirement that literature retrieval precede any
candidate-return computation — none was ever computed).

| # | Query | Retrieval UTC | Verdict | Reason |
|---|-------|---------------|---------|--------|
| L1 | "Bessembinder 1992 hedging pressure risk premiums futures markets open interest" | 2026-09-04T11:01Z | ACCEPT | Primary source: Bessembinder (1992), *RFS* 5(4) 637–667 — hedging pressure (net positioning of hedgers vs speculators) is priced in futures beyond CAPM beta; de Roon, Nijman & Veld (2000), *JF* — cross-market hedging pressure. Anchors the claim that positioning structure is priced. |
| L2 | "cryptocurrency perpetual futures open interest predict returns crowding study" | 2026-09-04T11:02Z | ACCEPT (caveat) | Giagkiozis (2024), *Ledger* — OI is systematically misquoted on some large exchanges: motivates fail-closed OI eligibility and PIT stamp discipline. REJECTED: Coin Metrics docs, Cube/MetaMask explainers — non-primary marketing/educational. |
| L3 | "Brunnermeier Pedersen \"Market Liquidity and Funding Liquidity\" Review of Financial Studies 2009" | 2026-09-04T11:05Z | ACCEPT | Brunnermeier & Pedersen (2009), *RFS* 22(6) 2201–2238 — liquidity spirals, destabilizing margins; supports exit-capacity/crowded-exit mechanism. Caveat: crisis-era marginated markets; transfer to 24/7 instant-margin crypto perps is qualitative. |
| L4 | "turnover ratio share turnover expected stock returns Datar Naik Radcliffe liquidity" | 2026-09-04T11:04Z | ACCEPT (confound warning) | Datar, Naik & Radcliffe (1998), *JFM* 1(2) 203–219 — negative turnover–return relation in equities. This is exactly the turnover-level confound; motivates CTL-FLOW-ONLY as the causal negative control. |
| L5 | "Binance USDT-M futures open interest history API statistics interval 1d official documentation" | 2026-09-04T11:07Z | ACCEPT | Official Binance USDⓈ-M REST API docs — `openInterestHist` supports `1d` period, response field `sumOpenInterest` (matches the staged shape `timestamp`/`sumOpenInterest` mapped by `research/data_fusion/crypto_compat.py`); availability = snapshot stamp. |
| L6 | "bitcoin futures open interest decline deleveraging liquidation cascade price impact research" | 2026-09-04T11:11Z | ACCEPT (boundary caveat) | Liquidation-cascade literature (e.g. *RAPS* 13(1) 53; SSRN 6891658; Bank of Canada WP 2025-12) studies OI *dynamics*/forced deleveraging. OITD deliberately uses OI *level structure* — no differencing, no direction — a different construct; also documents that the OI-flow sign region is falsified-family territory OITD does not enter. |
| L7 | "Nagel 2012 evaporating liquidity returns to liquidity provision short-term reversal" | 2026-09-04T11:09Z | ACCEPT (caveat) | Nagel (2012), *RFS* 25(7) 2005–2053 — ST-reversal profits proxy liquidity-provision returns. Transfer caveat: OITD contains no past-return term and is not a reversal implementation; reversal families are forbidden. |
| L8 | "Admati Pfleiderer 1988 theory of intraday patterns volume price variability trading clustering" | 2026-09-04T11:14Z | ACCEPT | Admati & Pfleiderer (1988), *RFS* 1(1) 3–53 — trading clusters endogenously; concentration of participation is a structural regime variable. Primary anchor for the companion TCH proposal; supports turnover *shape* as economically meaningful. |

**Primary-source claims used:** (i) structural positioning pressure is priced in
futures markets beyond beta (L1); (ii) positions whose exit requires many days
of normal volume are exposed to anticipatory/spiral dynamics (L3); (iii) OI
data quality varies and must be handled fail-closed (L2, L5).

**Crypto-perpetual transfer caveats.** (a) Hedging-pressure premia were
measured with CFTC hedger labels; Binance perps have no trader-classification,
so OITD is a structural proxy, not a hedging-pressure measurement, and the
sign/oracle strength may differ. (b) Equity turnover-premium evidence (L4)
means a low-turnover premium may exist independently of OI; the causal control
arms this family against that reading. (c) OI snapshots on some exchanges are
misquoted (L2): the design reads only owner-staged OI records with native
snapshot stamps, uses a 7-stamp mean to denoise, and refuses symbols with
insufficient OI history instead of inferring. (d) 24/7 trading with instant
margin has no closing auctions or margin cycles; "days of turnover to unwind"
is an abstract capacity unit, not a session-structured quantity. (e) Results in
one 52-week crypto window may be regime-specific; the fold and drop-one gates
are the preregistered guard against that reading.

## 4. PIT observable (fusion-record availability semantics)

Decision at stamp T reads ONLY fusion records with
`available_time_utc <= T` (PIT authority: retrieval time never substitutes for
availability; pinned by `research/data_fusion/crypto_compat.py` and
`research/data_fusion/pit.py`):

| Record (dataset_id.field) | available_time_utc | Use |
|---|---|---|
| `crypto_bars.close`, `crypto_bars.volume` (15m) | bar close time (`ts_event` boundary) | daily dollar turnover = sum(close x volume) per UTC day; 90d daily closes for beta context |
| `crypto_open_interest.open_interest` | OI snapshot stamp (`timestamp` / `create_time`) | 7-stamp trailing mean numerator (unit BASE) |
| `crypto_mark_price.mark_price` | mark kline close / snapshot stamp | notional conversion of OI to USDT |
| `crypto_funding.funding_rate` | funding settlement stamp | **COST ONLY** while held; never read by any signal, ranking or eligibility rule |

Derived quantities at stamp T (all from records above, all stamps <= T):
- `OI7_s(T)` = mean of the latest 7 daily OI records with stamp <= T (stamps
  within trailing 10 days; fewer than 7 -> symbol INELIGIBLE, fail-closed, no
  back-fill);
- `MK_s(T)` = latest mark record with stamp <= T (within trailing 24h; else
  ineligible);
- `TO_s(T,W)` = sum over completed 15m bars with close stamp in (T-W, T] of
  close x volume, divided by W_days = mean daily dollar turnover over the
  window W (anchor W = 28d, neighbour W = 56d); every UTC day in the window
  must be fully covered by completed bars (no gaps — completed-bar integrity
  per `research/v12/load_validation.py`; gaps are failures, never filled);
- `D_s(T)` = `OI7_s(T) * MK_s(T) / TO_s(T, 28d)` — days of average turnover to
  unwind standing notional OI.

## 5. Universe, warmup, decision clock, holding, rebalance/fill schedule

- **Universe:** the 19 tradeable symbols = the frozen `REQUIRED_SYMBOLS` of
  `research/v12/data_contract.py` MINUS `BTCUSDT`. BTCUSDT is the context
  benchmark only and is never ranked or held.
- **Window:** blind-S0 screen window 2025-08-22T00:00:00Z..2026-08-21T00:00:00Z;
  warmup drawn from the authorized window (from 2024-08-20). Binding warmup at
  the first stamp: 90d of completed bars (beta context, per the frozen
  `beta_90d` convention), 28d (anchor) / 56d (neighbour) turnover windows, 7
  daily OI stamps — all satisfiable from the authorized window.
- **Decision clock:** weekly, every Monday 00:00:00Z (52 discretionary
  decisions/365d <= 60 floor). First stamp 2025-08-25T00:00:00Z; last stamp
  2026-08-17T00:00:00Z. Fold-terminal force-flat actions are counted and
  reported separately from discretionary decisions (frozen A3 vocabulary).
- **Folds:** F0/F1/F2 chronological with 1-day purge, imported unchanged from
  the frozen V12 fold contract (per `v13_p_freeze`); force-flat at fold
  boundaries.
- **Execution lag (ONE, declared):** orders are released at T + 15 minutes;
  fill reference = the OPEN price of the first completed 15m bar whose slot-open
  instant >= T + 15m (the 00:15Z bar; its open instant coincides with order
  release, so no look-ahead — the bar RECORD becomes available at its close,
  but the transaction reference is the bar open at release time). Stress
  "+1 event delay" shifts the fill to the next 15m bar's open.
- **Book construction (hysteresis):** rank eligible symbols by D ascending;
  long tercile = lowest 6, short tercile = highest 6, middle 7 = buffer.
  Enter a side when the symbol's rank enters its tercile; EXIT only when the
  rank crosses beyond the median (buffer zone). Within a side, equal weights
  `w = min(0.5 / n_side, 0.30)`; if `n_side < 2`, that side's budget stays in
  cash (no renormalization). Gross <= 1.0; `|w| <= 0.30` at every stamp by
  construction. If a side has fewer than 4 members at a stamp, that stamp's
  rebalance is skipped and the previous book is held (fail-closed, no
  position-zeroing inference). A held symbol's intended holding span is >= one
  full week (7d) by construction — satisfies the >= 3d median-holding floor.

## 6. Arms (exactly three: anchor + neighbour + causal negative control)

| Arm | ID | Signal | Justification |
|---|---|---|---|
| Anchor | `OITD-28D` | `D_s` with 28d turnover denominator; long lowest-D tercile, short highest-D tercile | the mechanism as stated |
| Neighbour | `OITD-56D` | identical construction with a 56d turnover denominator | same mechanism, different justified parameter: a single burst week shifts the 28d denominator by ~25% but a 56d denominator by ~12%, halving estimator sensitivity while measuring the same duration concept; 56d warmup is inside the authorized window |
| Causal negative control | `CTL-FLOW-ONLY` | rank on 28d mean daily dollar turnover ALONE, DESCENDING (long highest-turnover tercile, short lowest-turnover tercile); OI numerator removed (numerator constant across symbols) | the flow-level shadow of the anchor's mechanical exposure: for fixed OI, low D == high turnover, so this control retains the anchor's turnover-level exposure and deletes the OI stock that the mechanism claims is doing the work |

**Preregistered control rule (the control MUST NOT reproduce the anchor):**
IF the anchor `OITD-28D` passes {after-cost expectancy > 0, position PF >= 1.10,
>= 2/3 folds positive}, THEN `CTL-FLOW-ONLY` must fail at least one of those
three gates. If `CTL-FLOW-ONLY` also passes all three, the edge is a pure
turnover-level (flow) effect, the OI stock is redundant, and
`A13-V13-A8-OITD` is FALSIFIED as a distinct positioning-structure mechanism.
The control uses no funding signal and is evaluated under the identical clock,
costs, folds and gates as the anchor.

## 7. Incremental test vs buy-and-hold AND BTC-beta context

Per chronological fold f in {F0, F1, F2}, on the anchor's net (after-cost,
funding-cost-inclusive) arm return:
- `excess_bh_f = arm_net_f − BTC_buy_and_hold_f` (BTCUSDT perp, same fold
  window, force-flat convention identical);
- `excess_beta_f = arm_net_f − beta_p * BTC_f`, where `beta_p` is the trailing
  90d daily regression beta of the arm's mark-to-market daily returns vs BTCUSDT
  daily returns (daily closes built from completed 15m bars), estimated PIT at
  the fold's first decision stamp and held fixed over the fold.

**Gate (Stage-A, unrelaxed):** both excess series positive in >= 2/3 folds.
Failure of either benchmark-context excess in >= 2 folds falsifies the
family's Q2 claim (returns are beta/benchmark repackaging, not incremental
information).

## 8. Costs, floors, concentration, drop-one

- **Base costs:** frozen adapter arithmetic
  (`GenericStrategyBase.rebalance_cost_between`): taker fee bps per side +
  adverse tick slippage floor (tick size from instrument metadata);
  native funding settlements accrue exactly ONCE per settlement inside
  `[ts_opened, ts_closed]` at the symbol's own cadence (8h/4h/1h mixed) —
  COST ONLY.
- **Stress costs:** frozen cell — fee x1.5, +2 adverse ticks, +1 event delay.
- **Floors (pre-score, schedule-only feasibility gate
  `research/v11/cost_feasibility.py` must PASS before any scoring):** annual
  base cost drag <= 8%/yr of average gross; stressed <= 12%/yr; <= 60
  discretionary decisions/365d (weekly = 52); median intended holding >= 3d
  (>= 7d by construction here); no single symbol > 25% of total one-way
  turnover; the hysteresis book exists precisely to keep membership churn (and
  hence drag) inside these floors.
- **Concentration:** `|w| <= 0.30` at every stamp by construction; gross <= 1.0;
  largest-symbol positive-PnL share <= 0.70 is a Stage-A outcome gate (not
  designed around).
- **Sample floors:** 52 weekly decisions on the screen window (>= 15 per fold);
  per-side membership >= 4 at >= 95% of stamps; signal availability >= 95% of
  stamps; arms with < 30 completed decisions refused at publication
  (minimum-activity freeze).
- **Drop-one design:** at every decision stamp, drop the HELD symbol with
  maximum `|weight|` (tie-break: ascending symbol name); remaining weights
  UNCHANGED — no post-score renormalization; full schedule rerun. Non-vacuous
  iff the dropped book differs from the anchor book at >= 50% of stamps with
  the dropped symbol held at those stamps. Drop-one may not flip any family
  verdict to PASS and must be reported per Stage-A gate ("non-vacuous drop-one
  symbol and fold survival").

## 9. Failure interpretation

1. **Anchor fails expectancy/PF:** the unwind-duration premium is absent or
   sign-wrong in this universe/window after costs -> family falsified; no
   rescue, no horizon/parameter search.
2. **Anchor passes, CTL-FLOW-ONLY passes too:** the edge is a generic
   turnover-level effect (DNR-style); the OI stock adds nothing -> falsified
   as a positioning-structure mechanism.
3. **Anchor passes, neighbour contradicts:** the duration statistic is
   horizon-fragile -> not a robust mechanism; falsified.
4. **Beta-context excess non-positive in >= 2 folds:** BTC-beta repackaging ->
   not incremental; falsified for Q2.
5. **Largest fold-positive share > 50%:** single-regime artifact; not
   generalizable; falsified.
6. **Feasibility floors FAIL:** schedule redesign allowed pre-score only; if
   unachievable without weakening any frozen floor -> withdraw, do not score.
7. **Drop-one vacuous:** the max-|w| symbol was not actually held -> arm
   invalid, rerun refused.
8. **A7-N |rho| > 0.20 vs frozen OILEV-V2 anchor or its inverted control:**
   INELIGIBLE under the voluntarily adopted novelty bound (section 12).
9. **Signal availability < 95%:** data insufficiency -> selection/BLOCKED
   refusal, NOT a mechanism verdict.

## 10. Source-to-test map (every input field -> exact test use)

| Input field (fusion record) | Exact test use |
|---|---|
| `crypto_bars.close` (15m) | daily dollar turnover denominator (28d anchor / 56d neighbour / 28d control); daily closes for 90d beta context and fold benchmark series |
| `crypto_bars.volume` (15m) | turnover products `close x volume` above |
| `crypto_open_interest.open_interest` (daily snapshots) | 7-stamp trailing-mean numerator of `D_s` (anchor + neighbour); >= 7 stamps eligibility rule |
| `crypto_mark_price.mark_price` | notional conversion `OI7 x MK` of the numerator to USDT |
| `crypto_funding.funding_rate` (settlements) | COST ONLY, accrued once per settlement while held; excluded from every signal, rank and eligibility rule |
| instrument tick size (`price_increment`) | adverse-tick slippage in base costs and the +2-tick stress |
| BTCUSDT bars | benchmark/context only (buy-and-hold and beta leg); never ranked, never held |

## 11. Ancestry map vs the forbidden inventory

| Inventory class | Why OITD is NOT a variant/inversion/rescue/renaming |
|---|---|
| `V12-OILEV-V2`, `V11-OILEVER-DELEV` (OI-deleveraging) | OILEV conditions on OI *change* (deleveraging flow direction). OITD conditions on an OI *level* relative to a turnover *level*; it contains no differencing, no OI sign, no horizon over which OI moves. A sign flip / horizon tweak / cap raise / carve-out of OILEV is undefined for a stock/flow ratio with no direction term. The mechanism's null (exit-capacity crowding) differs from the ancestor's (deleveraging flow). Voluntarily adopts the A7-N \|rho\| <= 0.20 bound vs the frozen OILEV-V2 anchor AND its inverted control; exceeding it -> ineligible, withdrawn. |
| `V6/V1-CARRY-FUNDING` | funding never appears in any signal, ranking or eligibility rule; it enters only as a native settlement cost while held (cost-only discipline). |
| `V4-XSECT-MOM`, `V8R-XSECT-REVERSAL`, `WEEKLY-REVERSAL/MR-RESCUE` | no past-return term exists anywhere in the signal; the ranking is return-free by construction. |
| `V1-VOLCOMP`, `V9-TS-TREND` / dollar-volume shock | no breakout/continuation rule, no volume-growth or shock term; the denominator is a mean level over a trailing window, not a spike/growth detector. |
| `V11-LOTTERY-MAX-SKEW` | no LOT/MAX/idiosyncratic-skew feature. |
| `V11-ILLIQ-AMIHUD`, `V12-ILLIQ-REPLICATION` | no `|r|/dollar-volume` impact measure anywhere; the turnover term in the denominator is a capacity scale, not a price-impact estimate, and the Amihud replication brief is not re-opened. |
| `V10-M01-AGGRESSOR-ABSORPTION` | no aggressor/taker-flow panel; bars carry no aggressor side and none is constructed. |
| `V12-BAB-LOWBETA` | no beta-sorted anchor; beta appears only as benchmark context (section 7). |
| `DATA-GATED` | uses only the four authorized fields + instrument tick size; no new source, key, signup or download. |

## 12. Shadow-region determination (section 1.1 front door)

**Determination: NOT a shadow-region entry.** The mechanism is stated in its
own words (exit-capacity crowding of standing inventory), never as "the
inverted anchor". Its conditioning construct (OI stock / turnover flow level)
and its sign region (long short-duration) are novel: none of the three measured
shadow observations (inverted OI-flow +0.758; V11 LOT inversion; stocks-program
vol-level sorting) involves a stock/flow duration ranking, and OITD is not an
inversion, rescue or renaming of any listed family (section 11). No front-door
disclosure of a previously observed identical sign is claimed, because no such
observation exists for this construct.

**Voluntary disciplines adopted regardless:** (i) the full A7-N novelty bound —
if \|rho\| > 0.20 vs the frozen OILEV-V2 anchor OR its inverted control on the
common window, this proposal is INELIGIBLE and withdrawn; (ii) its own causal
negative control (CTL-FLOW-ONLY) separates the mechanism from the
turnover-level confound, and the section 7 gate separates it from beta; funding
is cost-only by construction, separating it from funding carry; (iii) Stage-A
gates apply with no relaxation; (iv) if A7-N or A9-F nonetheless classifies this
family as shadow-region, it is preregistered CONFIRMATORY and that status is
recorded in the verdict and denominator, with all gates unrelaxed.

## 13. Family / budget note

This proposal is ONE family (`OITD`); if selected at D1 it consumes 3 scored
cells (anchor, neighbour, control) of the 6-cell sprint ceiling across the
<= 2-family selection. Exactly three arms; no fourth arm may be added post-hoc.

---

OUTCOME-BLIND ATTESTATION
lane: a8  proposal: A13-V13-A8-OITD
I wrote this mechanism and its falsification conditions before computing any
return, metric or ranking, and without access to any scored artifact or
outcome file.
utc: 2026-09-04T11:16:00Z  agent: a8
