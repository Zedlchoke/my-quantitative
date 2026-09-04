# A13-V13-A8-TCH — Turnover-Concentration Herfindahl (participation-structure conditioning)

Lane: a8 | Cycle: CRYPTO-V13 | Phase: D1 | Outcome-blind proposal (no returns,
PnL, metrics, rankings or backtests computed; no outcome files seen).
Written against the frozen blind input packet
(`research/proposals/v13/blind_input_packet.md`), the V13 forbidden family
inventory and the run contract only. Conditioning space: positioning/liquidity
information — depth/turnover structure (mission Q2).

---

## 1. Hypothesis ID and mechanism

**Hypothesis ID: `A13-V13-A8-TCH`** (lexicographically comparable, uppercase,
no spaces; sorts before `A13-V13-A8-OITD`'s lane-mate by pure chance of
naming — both are independent families).

**Mechanism (one paragraph).** The temporal SHAPE of a symbol's participation —
whether its dollar turnover is spread evenly across days or packed into a few
episodic bursts — is a structural property of who is trading. TCH measures it
as the Herfindahl index of daily dollar-turnover shares over the trailing 28
days: `H_s = sum_i (t_i / sum_j t_j)^2`, `t_i` = day-i dollar turnover from
completed 15m bars (`H = 1/28` when turnover is perfectly even; `H = 1` when it
all lands on one day; scale-invariant to the LEVEL of turnover by
construction). Economic counterparty: in high-H (burst-churned) symbols the
marginal price is set during episodic thin-book episodes dominated by impatient
directional takers, against liquidity providers who must re-quote after each
burst; in low-H (steady-participation) symbols continuous two-sided flow keeps
books populated and price discovery orderly (Admati & Pfleiderer 1988:
participation clustering is endogenous and has price effects). Why the edge
exists: episodic burst flow arrives disproportionately after information has
already diffused (attention-driven participation), so the burst-churned
symbol's marginal prices embed late, impatient taker prints taken from
temporarily thin books, while the steady symbol's prices are set against
standing liquidity; over the following week the thin-book prints are
progressively re-priced relative to the orderly book. **Expected sign: symbols
with LOW turnover concentration (steady participation) outperform symbols with
HIGH concentration (burst participation) over the following week**; the anchor
is long the lowest-H tercile, short the highest-H tercile.

TCH conditions on the **temporal structure of liquidity provision/participation
(depth/turnover structure)**. Its signal contains no price return, no turnover
level or growth term, no open interest, no mark price and no funding term.

## 2. Falsifiable prediction

The anchor arm, after base costs on the blind-S0 screen window
(2025-08-22..2026-08-21, folds F0/F1/F2 chronological with 1-day purge), passes:
after-cost expectancy > 0, position PF >= 1.10, at least 2/3 chronological
folds positive; excess over BTC buy-and-hold AND over the BTC-beta context is
positive in >= 2/3 folds; and the volatility-level causal control arm fails at
least one of the anchor's three gates.

**FALSIFIED if any of:**
1. the anchor fails any of the three gates above (the participation-structure
   premium is absent or sign-wrong after costs);
2. the anchor passes but CTL-VOLLEVEL also passes all three gates (the edge is
   a volatility-level effect — matching the documented vol-level sorting shadow
   observation — and the participation-SHAPE claim is redundant);
3. excess vs the BTC-beta context is non-positive in >= 2 folds (beta
   repackaging, not incremental);
4. the 56d neighbour contradicts the anchor's sign or is unstable across folds
   (the Herfindahl statistic is window-fragile, not a robust mechanism);
5. the largest fold-positive share of PnL exceeds 50% (single-regime artifact);
6. post-hoc diagnostics show the anchor's book is mechanically equivalent to a
   past-return sort (a forbidden reversal variant in disguise — the signal is
   return-free by construction, so any such equivalence means the construct is
   not what it claims);
7. A7-N measures |rho| > 0.20 vs the frozen OILEV-V2 anchor OR its inverted
   control on the common window (voluntary novelty commitment, section 12).

No parameter retune, sign flip, cap change or universe carve-out may be used to
rescue any failure mode above.

## 3. Literature (pass completed BEFORE mechanism finalization)

Search log (web search; batch window 2026-09-04T10:55Z..11:16Z; queries executed
sequentially in the order listed; per-query stamps minute-level, +-3 min;
literature retrieval completed before any candidate-return computation — none
was ever computed).

| # | Query | Retrieval UTC | Verdict | Reason |
|---|-------|---------------|---------|--------|
| L1 | "Admati Pfleiderer 1988 theory of intraday patterns volume price variability trading clustering" | 2026-09-04T11:14Z | ACCEPT | Admati & Pfleiderer (1988), *RFS* 1(1) 3–53 — trading clusters endogenously via strategic liquidity-trader timing; concentration of participation is a structural, price-relevant regime variable. Primary anchor for conditioning on turnover shape. |
| L2 | "Nagel 2012 evaporating liquidity returns to liquidity provision short-term reversal" | 2026-09-04T11:09Z | ACCEPT (strong caveat) | Nagel (2012), *RFS* 25(7) 2005–2053 — ST-reversal strategy returns proxy liquidity-provision compensation. Caveat: TCH is NOT a reversal implementation — its signal contains no past-return term and ranks on turnover shape; the vol-level control and the reversal-in-disguise falsifier (section 2, item 6) arm the family against this reading; reversal families are forbidden. |
| L3 | "turnover ratio share turnover expected stock returns Datar Naik Radcliffe liquidity" | 2026-09-04T11:04Z | ACCEPT (caveat) | Datar, Naik & Radcliffe (1998) — turnover LEVEL is priced in equities. TCH is scale-invariant to turnover level by construction (Herfindahl of within-window shares), which is the design answer to this confound; the vol-level control arms the remaining correlation channel. |
| L4 | "Brunnermeier Pedersen \"Market Liquidity and Funding Liquidity\" Review of Financial Studies 2009" | 2026-09-04T11:05Z | ACCEPT | Liquidity spirals: thin-book episodes amplify transient price impact; supports the burst-vs-steady book-quality channel. Caveat: crisis-era equities; transfer to 24/7 crypto perps is qualitative. |
| L5 | "Bessembinder 1992 hedging pressure risk premiums futures markets open interest" | 2026-09-04T11:01Z | ACCEPT (context only) | Positioning structure is priced in futures beyond beta. Context anchor for the lane's conditioning space; TCH itself uses no OI. |
| L6 | "cryptocurrency perpetual futures open interest predict returns crowding study" | 2026-09-04T11:02Z | ACCEPT (caveat) | Crypto perp market-quality literature (Cornell 2025; Giagkiozis 2024 *Ledger*): perps dominate crypto notional volume; data-quality discipline required. Supports the premise that participation structure in perps is economically central. |
| L7 | "Binance USDT-M futures open interest history API statistics interval 1d official documentation" | 2026-09-04T11:07Z | ACCEPT (venue semantics) | Official Binance USDⓈ-M docs; confirms the staged row shapes and stamp semantics mapped in `research/data_fusion/crypto_compat.py` (bar close stamps for klines) used by TCH's turnover series. |
| L8 | "bitcoin futures open interest decline deleveraging liquidation cascade price impact research" | 2026-09-04T11:11Z | ACCEPT (boundary caveat) | Burst/liquidation episodes in crypto are documented price-moving events; TCH's high-H side is an ex-ante STRUCTURAL proxy of burst-prone participation, not an event detector — no liquidation trigger, no OI input. |

**Primary-source claims used:** (i) participation clustering is endogenous and
price-relevant (L1); (ii) thin-book episodes amplify transient impact and
liquidity providers withdraw/widen under episodic pressure (L4, L2-mechanism);
(iii) turnover LEVEL is a priced liquidity proxy in equities — a confound TCH's
scale-invariance explicitly addresses (L3).

**Crypto-perpetual transfer caveats.** (a) The equity evidence on participation
shape is intraday and session-structured; TCH re-expresses it as a weekly
Herfindahl over UTC days on a 24/7 market with no open/close clustering clock —
the analog level of the construct is an assumption, not a measurement. (b)
Crypto bursts are frequently liquidation-driven (L8); a high-H reading may
reflect past forced-flow rather than standing participant mix — TCH claims only
a structure/attention association, not a cascade prediction, and holds no
directional event view. (c) Nagel's liquidity-provision proxy is a REVERSAL
strategy; in this factory reversal families are forbidden, so TCH must stand
purely on its shape signal — if its edge cannot be separated from a return-sort
equivalent, the family is falsified (section 2, item 6). (d) Herfindahl over
28 daily aggregates has a small-sample floor (1/28); cross-symbol comparisons
are valid only among symbols with complete 28-day coverage (fail-closed
eligibility). (e) One 52-week window may be regime-specific; fold and drop-one
gates are the preregistered guard.

## 4. PIT observable (fusion-record availability semantics)

Decision at stamp T reads ONLY fusion records with
`available_time_utc <= T` (PIT authority: retrieval time never substitutes for
availability; pinned by `research/data_fusion/crypto_compat.py` and
`research/data_fusion/pit.py`):

| Record (dataset_id.field) | available_time_utc | Use |
|---|---|---|
| `crypto_bars.close`, `crypto_bars.volume` (15m) | bar close time (`ts_event` boundary) | daily dollar turnover `t_i = sum(close x volume)` per UTC day over the trailing 28d (anchor) / 56d (neighbour) window; daily closes for the vol-level control and the 90d beta context |
| `crypto_funding.funding_rate` | funding settlement stamp | **COST ONLY** while held; never read by any signal, ranking or eligibility rule |
| instrument tick size | instrument metadata | adverse-tick slippage in base/stress cost arithmetic |

Derived quantity at stamp T (all from bar records with close stamps <= T):
- `H_s(T) = sum_{i=1..28} (t_i / sum_j t_j)^2` — Herfindahl of daily dollar
  turnover shares over the trailing 28 UTC days; every day must be fully
  covered by completed 15m bars (completed-bar integrity, no gap-filling;
  fewer than 28 complete daily aggregates -> symbol INELIGIBLE, fail-closed).
- `H_s` is invariant to the LEVEL of turnover (a scalar multiplication of all
  `t_i` leaves `H_s` unchanged): the family's exposure to the priced
  turnover-level channel (L3) is structurally minimized by construction.

**Not used by this family:** `crypto_open_interest.*`, `crypto_mark_price.*`
(read zero records; declared so the source-to-test map is complete and the
novelty argument is checkable).

## 5. Universe, warmup, decision clock, holding, rebalance/fill schedule

- **Universe:** the 19 tradeable symbols = frozen `REQUIRED_SYMBOLS` of
  `research/v12/data_contract.py` MINUS `BTCUSDT`. BTCUSDT is the context
  benchmark only and is never ranked or held.
- **Window:** blind-S0 screen window 2025-08-22..2026-08-21; warmup from the
  authorized window (from 2024-08-20). Binding warmup at the first stamp: 90d
  completed bars (beta context), 28d (anchor/control) / 56d (neighbour)
  turnover windows — all satisfiable from the authorized window.
- **Decision clock:** weekly, every Monday 00:00:00Z (52 discretionary
  decisions/365d <= 60 floor). First stamp 2025-08-25T00:00:00Z; last stamp
  2026-08-17T00:00:00Z. Fold-terminal force-flat actions counted separately
  from discretionary decisions (frozen A3 vocabulary).
- **Folds:** F0/F1/F2 chronological with 1-day purge, imported unchanged from
  the frozen V12 fold contract (per `v13_p_freeze`); force-flat at fold
  boundaries.
- **Execution lag (ONE, declared):** orders released at T + 15 minutes; fill
  reference = the OPEN price of the first completed 15m bar whose slot-open
  instant >= T + 15m (the 00:15Z bar; open instant coincides with order
  release — no look-ahead; the bar RECORD's availability at its close is
  irrelevant to the transaction reference). Stress "+1 event delay" shifts the
  fill to the next 15m bar's open.
- **Book construction (hysteresis):** rank eligible symbols by H ascending;
  long tercile = lowest 6 (steady participation), short tercile = highest 6
  (burst participation), middle 7 = buffer. Enter a side when rank enters the
  tercile; EXIT only when rank crosses beyond the median (buffer zone). Equal
  weights within a side `w = min(0.5 / n_side, 0.30)`; `n_side < 2` -> that
  side's budget stays in cash. Gross <= 1.0; `|w| <= 0.30` at every stamp by
  construction. Side membership < 4 at a stamp -> that stamp's rebalance is
  skipped, previous book held (fail-closed). Intended holding spans are >= one
  full week (7d) by construction — satisfies the >= 3d median-holding floor.

## 6. Arms (exactly three: anchor + neighbour + causal negative control)

| Arm | ID | Signal | Justification |
|---|---|---|---|
| Anchor | `TCH-28D` | `H_s` over 28d daily turnover shares; long lowest-H tercile, short highest-H tercile | the mechanism as stated |
| Neighbour | `TCH-56D` | identical construction with a 56d window (Herfindahl over 56 daily shares) | same mechanism, different justified parameter: a single burst day moves a 28d Herfindahl by ~3.6 percentage points of mass but a 56d one by ~1.8, halving single-episode sensitivity while measuring the same participation-shape concept; 56d warmup inside the authorized window |
| Causal negative control | `CTL-VOLLEVEL` | rank ASCENDING on trailing 28d realized volatility of daily log returns (daily closes from completed 15m bars); long lowest-vol tercile, short highest-vol tercile | the mechanical vol-level shadow of the anchor's exposure: bursty turnover co-occurs with volatile days, so low-H mechanically correlates with low realized vol; this control retains that exposure and deletes the turnover-SHAPE information |

**Preregistered control rule (the control MUST NOT reproduce the anchor):**
IF the anchor `TCH-28D` passes {after-cost expectancy > 0, position PF >= 1.10,
>= 2/3 folds positive}, THEN `CTL-VOLLEVEL` must fail at least one of those
three gates. If `CTL-VOLLEVEL` also passes all three, the edge is a
volatility-level effect — the pattern of the documented vol-level sorting
shadow observation — and `A13-V13-A8-TCH` is FALSIFIED as a
participation-structure mechanism. The control uses no funding signal and no
return term in its own ranking (realized vol of daily closes is a risk level,
not a momentum/reversal sort), and is evaluated under the identical clock,
costs, folds and gates as the anchor.

## 7. Incremental test vs buy-and-hold AND BTC-beta context

Per chronological fold f in {F0, F1, F2}, on the anchor's net (after-cost,
funding-cost-inclusive) arm return:
- `excess_bh_f = arm_net_f − BTC_buy_and_hold_f` (BTCUSDT perp, same fold
  window, identical force-flat convention);
- `excess_beta_f = arm_net_f − beta_p * BTC_f`, `beta_p` = trailing 90d daily
  regression beta of the arm's mark-to-market daily returns vs BTCUSDT daily
  returns (daily closes from completed 15m bars), estimated PIT at the fold's
  first decision stamp and held fixed over the fold.

**Gate (Stage-A, unrelaxed):** both excess series positive in >= 2/3 folds.
Failure of either in >= 2 folds falsifies the family's Q2 claim.

## 8. Costs, floors, concentration, drop-one

- **Base costs:** frozen adapter arithmetic
  (`GenericStrategyBase.rebalance_cost_between`): taker fee bps per side +
  adverse tick slippage floor (tick size from instrument metadata); native
  funding settlements accrue exactly ONCE per settlement inside
  `[ts_opened, ts_closed]` at the symbol's own cadence (8h/4h/1h mixed) —
  COST ONLY.
- **Stress costs:** frozen cell — fee x1.5, +2 adverse ticks, +1 event delay.
- **Floors (pre-score schedule-only feasibility gate
  `research/v11/cost_feasibility.py` must PASS before any scoring):** base
  drag <= 8%/yr of average gross; stressed <= 12%/yr; <= 60 discretionary
  decisions/365d (weekly = 52); median intended holding >= 3d (>= 7d by
  construction); no single symbol > 25% of total one-way turnover (hysteresis
  exists to keep membership churn inside the floors).
- **Concentration:** `|w| <= 0.30` at every stamp by construction; gross <= 1.0;
  largest-symbol positive-PnL share <= 0.70 is a Stage-A outcome gate.
- **Sample floors:** 52 weekly decisions on the screen window (>= 15 per fold);
  per-side membership >= 4 at >= 95% of stamps; signal availability >= 95% of
  stamps; arms with < 30 completed decisions refused at publication.
- **Drop-one design:** at every decision stamp, drop the HELD symbol with
  maximum `|weight|` (tie-break: ascending symbol name); remaining weights
  UNCHANGED — no post-score renormalization; full schedule rerun. Non-vacuous
  iff the dropped book differs from the anchor book at >= 50% of stamps with
  the dropped symbol held at those stamps. Drop-one may not flip any family
  verdict to PASS and is reported per Stage-A gate.

## 9. Failure interpretation

1. **Anchor fails expectancy/PF:** the steady-participation premium is absent
   or sign-wrong after costs -> family falsified; no rescue, no window/parameter
   search.
2. **Anchor passes, CTL-VOLLEVEL passes too:** the edge is a volatility-level
   effect (shadow-observation pattern), not participation shape -> falsified
   as a structure mechanism.
3. **Anchor passes, neighbour contradicts:** the Herfindahl is window-fragile
   -> not a robust mechanism; falsified.
4. **Beta-context excess non-positive in >= 2 folds:** BTC-beta repackaging
   -> not incremental; falsified for Q2.
5. **Largest fold-positive share > 50%:** single-regime artifact; falsified.
6. **Return-sort equivalence:** post-hoc diagnostics show the anchor book is
   mechanically a past-return sort -> the construct is a forbidden reversal
   variant in disguise; falsified and ineligible regardless of results.
7. **Feasibility floors FAIL:** schedule redesign allowed pre-score only; if
   unachievable without weakening any frozen floor -> withdraw.
8. **Drop-one vacuous:** max-|w| symbol not actually held -> arm invalid.
9. **A7-N |rho| > 0.20 vs frozen OILEV-V2 anchor or its inverted control:**
   INELIGIBLE under the voluntarily adopted novelty bound (section 12).
10. **Signal availability < 95%:** data insufficiency -> selection/BLOCKED
    refusal, NOT a mechanism verdict.

## 10. Source-to-test map (every input field -> exact test use)

| Input field (fusion record) | Exact test use |
|---|---|
| `crypto_bars.close` (15m) | daily dollar turnover `t_i` (`close x volume` aggregation, 28d anchor / 56d neighbour / 28d control window); daily closes for the vol-level control's realized volatility and the 90d beta context |
| `crypto_bars.volume` (15m) | turnover products above |
| `crypto_open_interest.*` | NOT USED (zero records read; declared explicitly) |
| `crypto_mark_price.*` | NOT USED (zero records read; declared explicitly) |
| `crypto_funding.funding_rate` (settlements) | COST ONLY, accrued once per settlement while held; excluded from every signal, rank and eligibility rule |
| instrument tick size (`price_increment`) | adverse-tick slippage in base costs and the +2-tick stress |
| BTCUSDT bars | benchmark/context only (buy-and-hold and beta leg); never ranked, never held |

## 11. Ancestry map vs the forbidden inventory

| Inventory class | Why TCH is NOT a variant/inversion/rescue/renaming |
|---|---|
| `V12-OILEV-V2`, `V11-OILEVER-DELEV` | TCH reads zero OI records; no OI construct, direction or level enters the signal anywhere. Voluntarily adopts the A7-N \|rho\| <= 0.20 bound vs the frozen OILEV-V2 anchor AND its inverted control; exceeding it -> ineligible, withdrawn. |
| `V6/V1-CARRY-FUNDING` | funding never appears in any signal; cost-only while held. No crowding-premium/carry rescue — the signal cannot see funding at all. |
| `V8R-XSECT-REVERSAL`, `WEEKLY-REVERSAL/MR-RESCUE`, `V4-XSECT-MOM` | the signal is return-free by construction (only bar close x volume shapes); no past-return term at any horizon. The reversal-in-disguise risk is preregistered as falsifier #6. |
| `V1-VOLCOMP` (compression breakout), `V9` dollar-volume shock continuation | no breakout/continuation rule; the Herfindahl is a within-window distribution SHAPE, invariant to turnover LEVEL and to turnover GROWTH (a scalar multiple or a monotone rescaling of all days' turnover leaves H unchanged); it is not a spike/shock detector and triggers on no threshold crossing. |
| `V11-LOTTERY-MAX-SKEW` | no LOT/MAX/skew feature (no returns in the signal at all). |
| `V11-ILLIQ-AMIHUD`, `V12-ILLIQ-REPLICATION` | no `|r|/dollar-volume` impact measure; H is scale-free and return-free; the Amihud replication brief is not re-opened. |
| `V10-M01-AGGRESSOR-ABSORPTION` | no aggressor/taker-flow panel; bar rows carry no aggressor side and none is constructed. |
| `V12-BAB-LOWBETA` | no beta-sorted anchor; the vol-level quantity appears ONLY inside the control arm designed to be refuted, and beta only as benchmark context. |
| `DATA-GATED` | uses only authorized bar fields + tick size; no new data source. |

## 12. Shadow-region determination (section 1.1 front door)

**Determination: NOT a shadow-region entry.** The mechanism is stated in its
own words (endogenous participation clustering and thin-book price setting),
never as "the inverted anchor". Its conditioning construct — the temporal
concentration of dollar turnover — is read by no forbidden family, and none of
the three measured shadow observations (inverted OI-flow +0.758; V11 LOT
inversion; stocks-program vol-level sorting) involves a turnover-shape ranking;
TCH is not an inversion, rescue or renaming of any listed family (section 11).
No front-door disclosure of a previously observed identical sign is claimed,
because no such observation exists for this construct; the vol-level control
exists precisely because a CONFOUND (not the mechanism) resembles one of the
shadow observations.

**Voluntary disciplines adopted regardless:** (i) the full A7-N novelty bound —
if \|rho\| > 0.20 vs the frozen OILEV-V2 anchor OR its inverted control on the
common window, this proposal is INELIGIBLE and withdrawn; (ii) its own causal
negative control (CTL-VOLLEVEL) separates the mechanism from the vol-level
shadow, and the section 7 gate separates it from beta; funding is cost-only by
construction, separating it from funding carry; (iii) Stage-A gates apply with
no relaxation; (iv) if A7-N or A9-F nonetheless classifies this family as
shadow-region, it is preregistered CONFIRMATORY and that status is recorded in
the verdict and denominator, with all gates unrelaxed.

## 13. Family / budget note

This proposal is ONE family (`TCH`), distinct from `OITD` (different
conditioning construct, different inputs, different control); if selected at
D1 it consumes 3 scored cells (anchor, neighbour, control) of the 6-cell sprint
ceiling across the <= 2-family selection. Exactly three arms; no fourth arm may
be added post-hoc.

---

OUTCOME-BLIND ATTESTATION
lane: a8  proposal: A13-V13-A8-TCH
I wrote this mechanism and its falsification conditions before computing any
return, metric or ranking, and without access to any scored artifact or
outcome file.
utc: 2026-09-04T11:16:00Z  agent: a8
