# F0_VERDICTS — SLEEVE-FX5-100K-V1 (Lane F0: independent MECHANISM/ANCESTRY COURT)

- Court: Lane F0, pre-GO sleeve-only program SLEEVE-FX5-100K-V1 (cycle_id
  `SLEEVE-FX5-100K-V1-PREGO`).
- Measured-at (UTC, `date -u`): 2026-09-29T01:32:19Z. Read-only session: no git
  commands, no backtests, no PnL, no scoring. Owner dirty tree preserved.
- Input: `research/control/SLEEVE-FX5-100K-V1/f0/DISTINCT15_INPUT.tsv` (15
  DISTINCT_TESTABLE census rows, all HYPOTHESIS/NOT_RUN). The census
  `priority_score` column is IGNORED BY LAW; nothing in this file ranks by it.
- Successor law: predecessor TERMINAL PORTFOLIO-ROUTER-12ASSETS-100K-V1 closed
  ROUTER_STATES_THIN and is NOT rescued here; nothing in these verdicts reopens it.

## Authorities applied

1. `HOW_TO_BE_A_LEAD_ENGINEER.md` §14.3 — a rejected family re-delivered with
   changed timeframe / threshold / symbols / sign / name / session is NOT a new
   mechanism; mechanism + information source + causal control unchanged ⇒ reject
   before scoring; cross-horizon rescue is an ancestry violation (Q-3).
2. `research/wayfinder/LESSONS.md` — P-27 (F-0 court before rho before PnL;
   "adding an observable/gate to a dead law is a variant"), P-28 (inverted control
   is the cheapest kill; sign-flip adjudication), P-29 (gate states on
   autocorrelated chains are the dead level-window; pair-swap reopens nothing),
   Q-3 (cadence is family identity; re-clocking launders nothing), Q-7
   (event-conditioning carries a clock-only shadow), Q-11 (a permutation is a
   null only if it moves the signal).
3. Ancestry: `research/wayfinder/FAMILY_FAILURES.jsonl` (169 records). Every id
   cited below was read in full from that file; skeleton / payer / information
   source of each ancestor is taken from the record text, not from the census's
   `ancestry_hits` column. The census column `none-found` was independently
   re-searched across all 169 records and is OVERTURNED where noted.
4. Idea source text: `research/control/FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/
   symbols/*.md` at the `source_ref` lines (read with context).
5. Cost bands: `research/control/PORTFOLIO-ROUTER-12ASSETS-100K-V1/cost/
   COST_ACCOUNTING_SPEC.md` (see SLATE_PROPOSAL).
6. Data ceiling (dispatch law): EURUSD/GBPUSD/USDJPY = M1 Dukascopy `.bi5`
   (bid/ask, per-bar spread measurable, volume column present — verified in
   `duka_lib.py` ">5if" = sec,o,c,l,h,vol_f32); AUDUSD/USDCAD = H1/15m ANC
   derived planes, NO M1 execution clock, NO volume column (verified schema in
   ERP1-TRACKA-COHORT-2 `PITDATA_cohort2_REPORT.md`: 15m/1h parquets carry
   `ts, b_*, a_o/a_c, s_open, s_close` only).

## The standing class veto this court must apply

`TRACKA2-P3B-DINV-1D` (FAMILY_FAILURES.jsonl line 131, ERP1-TRACKA-COHORT-2,
forex, CLOSED/SELECTION_REJECTION, ANCESTRY_RHO_BLOCK): a 1-day continuation
book on AUDUSD/USDCAD was measured to BE the dead FX H1 momentum/donchian class
re-clocked (pooled worst |rho| 0.3032 USDCAD vs `FX2-H1TSMOM-C1`, 0.3103 AUDUSD
vs `FX2-H1DONCH-C1`, bar 0.20), with secondary failure text verbatim:
"REOPENING_CONDITION: none — momentum re-label at day clock joins the standing
class veto; re-clocking is ancestry violation (Q-3/umbrella §6)". This is a
closed door with NO reopening condition: every own-price momentum/continuation
re-label at H4/D1 clock on the sleeve's FX pairs is the dead class.

---

## Per-row verdicts (15/15)

Verdict codes: ADMIT_MECHANISM_NOVEL | REJECT_VARIANT_SAME_FAMILY |
REJECT_NOT_STANDALONE | REJECT_DATA_OR_COST. "Census" = the DISTINCT15 census
verdict being re-adjudicated (confirm/overturn).

### 1. GBPUSD-S079 — cta_unwind_join (Systematic-Flow Unwind Anticipation)

- Source: symbols/GBPUSD.md:487-489 (S79): composite 20d/60d vol-scaled
  trend-factor "estimates" CTA positioning; when large and near flip, join the
  unwind direction 2-3 days at the flip; stop re-flip. Data: "spot daily
  (rebuild factor) + public CTA notes nếu có" — positioning is NOT observed,
  it is estimated from own price.
- Verdict: **REJECT_VARIANT_SAME_FAMILY** (census CONFIRMED-rejected in effect;
  census said DISTINCT_TESTABLE — OVERTURNED).
- Dead ancestor (primary): `TRACKA2-P3B-DINV-1D` — skeleton match: enter in the
  direction of a fresh momentum sign at day clock, hold days = the momentum
  continuation class under the standing no-reopening veto; information source
  match: own price (the "positioning estimate" is a deterministic transform of
  own-price momentum — P-29: a gate/estimate built on an autocorrelated chain is
  the dead level-window). Payer: the forced-deleveraging payer is asserted, not
  observed — and the observed-positioning version of this exact story is already
  dead: `COMMNG1-A4-P2-ARM1-NEUTRAL` (COMMODITIES-NG1, CoT crowd-carry
  persistence) died CONTROL_OUT_EARNS_RELEASE_CLOCK — the bare release-clock
  control beat every positioning arm; an own-price proxy for positioning is
  strictly weaker than the CoT data that already failed. Class twins:
  `CRYPTO-V9::XSECT-TSTREND-L14/L28` (TSMOM 5/5 rejected), `DT100-80-TSMOMH`
  (TSMOM re-clocked, exp -10.59 bps PF 0.83, 0/4 folds).
- §14.3 axes moved: none. Skeleton = momentum; payer = story-only; information =
  own price.

### 2. USDJPY-S012 — tokyo_range_fade (Tokyo session range fade)

- Source: symbols/USDJPY.md:125 (S12): Tokyo range 00:00-09:00 JST > 0.7xATR(H1
  20) without Japan news ⇒ fade at London-open false break; stop outside Tokyo
  extreme; target 50% range.
- Verdict: **REJECT_VARIANT_SAME_FAMILY** (census DISTINCT_TESTABLE —
  OVERTURNED).
- Dead ancestors: `FXFV2-A4-P1` (FOREX-FREE-V2, "Tokyo-range compression ->
  London-morning expansion", EXPECTANCY_NONPOSITIVE anchor -3.804/trade PF 0.593,
  COST_DOMINATED, 1,541 trades) — same skeleton: condition on the Tokyo-range
  state at the London transition and trade the London reaction; same information
  source: the Tokyo-session-range/ATR observable; the compression-vs-extension
  conditioning is the other tail of the SAME state variable and the
  fade-vs-join is a sign flip — §14.3 sign/threshold swap is not novelty.
  `FXFV2-A4-P2` ("London-AM range break + retest-hold", CONTROL_REPRODUCED_
  MECHANISM: placebo ≈ anchor) closes the complementary sign of the same
  session-transition family. `FXFV1-A3-P1` / `FXFV1-A3-P2` (London-open session
  continuation -2.35/trade across 7 pairs, 11,459 trades; Late-NY fade) close
  the session-transition class measured-wide. Class twin: `DT100-09-ASIANRANGE`
  (Asian-range class, PF_BELOW_THRESHOLD, dead). Payer identity: "fakeout
  chasers" is the same session-transition chaser pool the FXFV family
  hypothesized — no new payer.
- The clock-shadow control the census proposed (entry window +3h) is exactly the
  control shape that killed FXFV2-A4-P2; a court does not run it, but the
  ancestry outcome is already measured.

### 3. EURUSD-S027 — vol_expansion_onset (ATR-ratio expansion onset)

- Source: symbols/EURUSD.md:333-334 (S27): ATR(5)/ATR(50) on H4 crosses 1.5
  from below 1.0 within 10 sessions ⇒ enter direction of the expansion candle,
  stop 1xATR(5), trail.
- Verdict: **REJECT_VARIANT_SAME_FAMILY** (census DISTINCT_TESTABLE —
  OVERTURNED).
- Dead ancestors: `DT100-71-RVREGIME` (DAYTRADER-100-V1, census #71 "RV-break
  regime switch", NEGATIVE_EXPECTANCY exp -11.37 bps PF 0.703, 4581 trades, 0/4
  folds) — the conditioning layer is the dead realized-vol-regime class; onset
  (rising edge) vs regime level is an edge-vs-level rename of the same vol-ratio
  state on an autocorrelated chain (P-29: the gate state does not escape the
  dead level-window). `H-VOLCOMP-BRKOUT-v1` (SPRINT-CRYPTO, vol-compression
  breakout, 26/28 cells negative) is the complementary tail of the same
  vol-state breakout skeleton. `TRACKA2-P3B-DINV-1D` standing veto: the entry
  leg is own-price breakout continuation on FX at H4 clock — a re-clock of the
  dead `FX2-H1DONCH-C1` class (H1 -> H4 clock swap, §14.3). Payer
  ("vol-regime transitions carry persistent continuation") is a restatement of
  the signal, not an external payer.

### 4. AUDUSD-S001 — ema_stack_trend (EMA-stack multi-TF trend)

- Source: symbols/AUDUSD.md:241-243 (S1): H4 EMA20>EMA50>EMA200 + price above
  EMA200-D1 defines trend; pullback entries, trail EMA50-H4; long-only when
  China credit impulse not negative (coupling).
- Verdict: **REJECT_VARIANT_SAME_FAMILY** (census DISTINCT_TESTABLE —
  OVERTURNED).
- Dead ancestors: `TRACKA2-P3B-DINV-1D` standing veto via `FX2-H1TSMOM-C1` —
  an EMA stack is a smoothed momentum state on own price at H4/D1 clock; the
  veto text ("momentum re-label at day clock joins the standing class veto")
  covers this exactly. `ES1-BAND-TREND` (BTC-H4-EDGE-SEARCH-V1: SMA200 dead-band
  MA-trend filter, CLOSED SCIENTIFIC_REJECTION by G5 fold concentration) is the
  MA-filter skeleton twin at the same H4 clock on another asset — asset swap is
  not novelty (§14.3). `CRYPTO-V9::XSECT-TSTREND-L14/L28` (TSMOM class) is the
  payer-class twin ("trend-following allocation flows pay momentum premium" is
  the same momentum-premium payer story the dead class claimed). Information
  source: own price only.

### 5. AUDUSD-S003 — adx_macd_persistence (ADX-filtered momentum persistence)

- Source: symbols/AUDUSD.md:247-249 (S3): ADX14-D1>25 + MACD histogram
  same-sign 3 bars gates momentum-persistence entries; exit ADX<20; coupling
  VIX<25.
- Verdict: **REJECT_VARIANT_SAME_FAMILY** (census DISTINCT_TESTABLE —
  OVERTURNED).
- Dead ancestors: `TRACKA2-P3B-DINV-1D` standing veto — the underlying law is
  momentum persistence at day clock on FX; the ADX/MACD gate is precisely
  "adding a gate to a dead law" (P-27), and the ADX trend-strength state is
  itself a momentum state (P-29 representation: the gate IS the ancestor).
  Twins: `FX2-H1TSMOM-C1` (information source: own price), `ES1-BAND-TREND`
  (indicator-gated MA trend skeleton). The census's "distinct from EMA stack"
  argument compares this row to ANOTHER PROPOSED ROW, not to the ancestry —
  intra-slate distinctness is not novelty vs the dead class.

### 6. AUDUSD-S017 — td_sequential_fade (DeMark TD-Sequential exhaustion fade)

- Source: symbols/AUDUSD.md:291-293 (S17): TD 9/13 completion + RSI divergence
  fades exhausted driver waves at stop-reversal clusters; stop beyond bar-9
  extreme; target opposite TD level.
- Verdict: **REJECT_VARIANT_SAME_FAMILY** (census DISTINCT_TESTABLE —
  OVERTURNED).
- Dead ancestors: `FXOS-04` (EURUSD-OPEN-SEARCH-V1: Bollinger MR fade on 15m
  EURUSD with measured bid/ask costs; HOLDOUT_NET_NEGATIVE, dev +1203.6 pips ->
  holdout -134.4 pips; 5/48 dev-positive trials attributed to selection) —
  skeleton match: own-price oscillator exhaustion fade on an FX major; the TD
  count is a renamed oscillator (a deterministic price-pattern transform),
  §14.3 rename is not novelty. `mean-reversion-transfer` (SPRINT-CRYPTO:
  Bollinger+RSI frozen-rule transfer FAILED) closes the oscillator-fade
  transfer class. The dead FX shadow `FX2-STOCH-C4` (oscillator-fade class,
  listed among the standing blocks in ERP1-TRACKA-COHORT-2
  SKEPTIC_F1_cohort2_REPORT.md) confirms the class is closed on these very
  pairs. Clock: 15m -> H4/D1 is a cross-horizon rescue (§14.3/Q-3). Payer
  ("stop-cluster crowd at exhaustion counts") = the same stop-cluster payer the
  dead MR-fade family claimed.

### 7. AUDUSD-S087 — volume_profile_poc (Volume-profile POC acceptance)

- Source: symbols/AUDUSD.md:516-518 (S87): 20-day volume profile; at
  value-area edge, low-volume => fade to POC, high-volume + hold outside =>
  join break; M5/tick volume; stop 0.7x value-area width.
- Verdict: **REJECT_DATA_OR_COST** (census DISTINCT_TESTABLE — OVERTURNED on
  data grounds).
- Missing authorities (named): (a) VOLUME — the AUDUSD sleeve panel is the
  H1/15m ANC derived plane whose verified schema is
  `ts, b_o,b_h,b_l,b_c, a_o,a_c, s_open, s_close` with NO volume column
  (ERP1-TRACKA-COHORT-2 PITDATA_cohort2_REPORT.md); every conditional in this
  idea ("volume ngày thấp" / "volume cao") is unimplementable on the declared
  panel; (b) CLOCK — M5 execution precision on an H1/15m-only pair is below the
  sleeve's declared data ceiling (dispatch law; the intraday value-area
  acceptance/rejection decision is sub-H1 by construction).
- Ancestry note (honest): NO dead volume-profile ancestor was found in the 169
  records — the kill is data, not ancestry. Salvage observation recorded in
  SLATE_PROPOSAL §B(3): the observable class is only feasible on the three M1
  pairs (Dukascopy volume_f32 verified) — a future cohort would have to propose
  it there as a NEW row; per P-29 pair-swap does not reopen THIS row.

### 8. AUDUSD-S088 — round_number_defense (Round-number defense fade)

- Source: symbols/AUDUSD.md:519-521 (S88): slow non-event approach to big
  figures with RISING TICK VOLUME and stalled progress fades from 8-12 pips
  before the level; stop 6 pips through; target 20 pips; M5 + levels (option
  expiry calendar optional).
- Verdict: **REJECT_DATA_OR_COST** (census DISTINCT_TESTABLE — OVERTURNED on
  data grounds).
- Missing authorities: same as S087 — M5 clock below the AUDUSD ceiling and a
  tick-volume CONDITIONAL ("tick volume tăng") on a panel with no volume
  column; the 8-12-pip approach band and 6-pip stop are sub-H1 geometry and
  cannot be resolved on H1 bars (a single H1 bar spans the whole approach).
- Secondary ancestry: `TRACKA2-C1C2C3-REGATED-RANGEFADE` (ERP1-TRACKA-
  COHORT-2) fenced range-ADJACENT triggers permanently against gate variants:
  "only a mechanism with a NEW payer + new information layer (F-0 three tests)
  can carry a range-adjacent trigger". A big figure is a price-level trigger;
  the claimed new payer (barrier gamma defense) would need the option-expiry
  calendar, which the source itself marks optional and the sleeve does not
  carry — so the payer is unevidenced and the information layer collapses to
  own price at a level (same class as the fenced family).

### 9. AUDUSD-S002 — donchian_breakout (Donchian 20/55 Turtle, D1) [MANDATORY DEEP-DIVE]

- Source: symbols/AUDUSD.md:244-246 (S2): D1 close through 20-day high (entry)
  / 55-day (stop-and-reverse), two-sided, ATR14 sizing; coupling "gate
  ADX14>20" (note: the census called this row "ungated"; the source text
  carries an ADX-gate coupling — immaterial to the verdict, see below).
- Verdict: **REJECT_VARIANT_SAME_FAMILY** (census DISTINCT_TESTABLE —
  OVERTURNED).
- The mandatory question: is a D1 donchian breakout on AUDUSD the same
  mechanism class as the dead PSV1 donchians? YES — and the closer ancestor is
  not even PSV1. Adjudication:
  - Skeleton: channel-breakout trend continuation, always-in stop-and-reverse.
    Identical to the dead FX class `FX2-H1DONCH-C1` (the H1 donchian shadow
    family whose rho killed TRACKA2-P3B) — clock swapped H1 -> D1. §14.3:
    timeframe swap is not novelty; Q-3/umbrella §6 (carried verbatim in
    `TRACKA2-P3B-DINV-1D`): "momentum re-label at day clock joins the standing
    class veto; re-clocking is ancestry violation", REOPENING_CONDITION: none.
    Symbol is irrelevant to class identity (AUDUSD is one of the two pairs the
    veto was measured ON).
  - The PSV1 twins `PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION` (CONTROL_
    OUTEARNED_ANCHOR: block-shuffled phase-gate control +190,392 out-earned the
    anchor +177,692 — phase timing carried no information) and
    `PSV1-BTC_H1-UPTREND-BREAKOUT_CONT` (FOLD_CONCENTRATION: no incremental
    value over ALWAYS_ON_LONG) are the same skeleton on BTC — long-only,
    regime-gated. The census's novelty claim ("ungated two-sided Turtle; dead
    PSV1 Donchians were regime-gated single-direction variants") is a GATE
    difference: adding OR removing a gate to a dead law is a variant (P-27,
    first adjudication law 2026-09-26; also `TRACKA2-C1C2C3-REGATED-RANGEFADE`:
    "stripping each new observable degenerates to the dead decision law").
  - Payer: "breakout-chasing crowd; late entrants pay" — the same stop-flow
    payer the dead donchian/momentum class claimed. Information source: own-price
    channel extremes — unchanged. 0/3 F-0 axes move.

### 10. USDCAD-S002 — donchian_breakout (Donchian 20/55 classic, D1) [MANDATORY DEEP-DIVE]

- Source: symbols/USDCAD.md:197-199 (S2): always-in-market Donchian 20/55
  entry + stop-and-reverse on daily closes; "không filter gì thêm (baseline
  sạch để benchmark)"; payer column in census: "UNCLEAR (no forced payer
  claimed)".
- Verdict: **REJECT_VARIANT_SAME_FAMILY** (census DISTINCT_TESTABLE —
  OVERTURNED).
- Same adjudication as row 9, on the OTHER pair the standing veto was measured
  on (USDCAD's worst shadow was `FX2-H1TSMOM-C1` at rho 0.3032, and
  `FX2-H1DONCH-C1` also blocked at 0.3001). "Deliberately unfiltered baseline"
  is a framing, not a mechanism: an ungated instance of a dead class is still
  the dead class (and if anything, dies identically — the PSV1 H1 variant's
  failure was that trivial long exposure out-earned it). Dead ancestors cited:
  `FX2-H1DONCH-C1` / `FX2-H1TSMOM-C1` via `TRACKA2-P3B-DINV-1D` standing veto
  (reopening: none); `PSV1-BTC_H1-UPTREND-BREAKOUT_CONT`;
  `PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION`; `DT100-80-TSMOMH` as the
  momentum-class twin the census itself listed.

### 11. AUDUSD-S046 — weekday_seasonality (Day-of-week seasonality)

- Source: symbols/AUDUSD.md:385-387 (S46): Monday Asia range-extension and
  Friday NY post-18:00-UTC reversal as weekday priors; source text verbatim:
  "chỉ dùng như prior, không standalone" (usable as a prior only, NOT
  standalone).
- Verdict: **REJECT_NOT_STANDALONE** (census DISTINCT_TESTABLE — OVERTURNED).
- Grounds: the idea's own source declares it cannot form its own book; the
  census mechanism column itself carries "not standalone". A prior that must
  modulate other entries is an overlay, not a sleeve mechanism.
- Ancestry (payer analysis as instructed): vs `STOCKS-FREE-V3::SFV3-A6-TOM-
  SETTLE` — the payer IS arguably different (weekly re-entry/squaring FX flows
  vs equity month-end settlement flows; a different payer could in principle
  survive), BUT the information class is the same: calendar-clock conditioning
  on the asset's own tape, and the class twins are dead on that information
  class alone: `DT100-34-WEEKEND` (calendar conditioning, NEGATIVE_EXPECTANCY),
  `V17-A4-P1-WKNDLIQ` (ANCESTRY_RHO_BLOCK: the weekend book was measurably a
  low-liquidity-period exposure — Q-7: the clock did the work). Payer
  difference cannot rescue a non-book.

### 12. USDCAD-S047 — winter_seasonality (Winter CAD strength seasonality)

- Source: symbols/USDCAD.md:393-395 (S47): short USDCAD half-size mid-Nov to
  mid-Feb with an OIL-HEDGE leg; risk note: war-regime oil years fold the
  season into trend; required data per census: "multi-year USDCAD D1 history
  plus WTI hedge leg".
- Verdict: **REJECT_DATA_OR_COST** (census DISTINCT_TESTABLE — OVERTURNED).
- Missing authorities (named): (a) the WTI hedge leg — the FX5 sleeve carries
  no WTI panel; "winter swap UNMEASURED; hedge roll" is unpriceable without an
  oil series, and unhedged the mechanism is not the one proposed (it is a
  naked 3-month directional short whose variance is dominated by oil-regime
  years per the source's own risk note); (b) decision power — one entry per
  year against the repo D grid (2021-2026 measured panels) gives ~5 winter
  episodes; under the P-29 ceiling-x-power doctrine an arithmetically
  underpowered family is a silent design kill (no fold can populate).
- Ancestry (payer analysis as instructed): vs `SFV3-A6-TOM-SETTLE` the payer
  genuinely differs (seasonal energy-conversion + repatriation flows vs equity
  settlement) — acknowledged, and it is why this row is NOT killed as a
  TOM-SETTLE variant — but a different payer does not conjure the missing
  hedge instrument or the missing decades. `DT100-34-WEEKEND` /
  `V17-A4-P1-WKNDLIQ` stand as the calendar-conditioning twins for the clock
  shadow that would have to be beaten.

### 13. EURUSD-S009 — macd_divergence_exit (MACD-histogram exhaustion exit)

- Source: symbols/EURUSD.md:273-274 (S9): enter on EMA alignment; exit two-
  thirds on two MACD-histogram divergences vs price; vol-percentile filter on
  the rule; census payer column: "UNCLEAR; exit-timing overlay saves trend
  giveback without own premium".
- Verdict: **REJECT_NOT_STANDALONE** (census DISTINCT_TESTABLE — OVERTURNED).
- Grounds: an exit rule riding an entry law cannot form its own book — there
  is no position without the entry, and the entry leg (EMA alignment) is
  itself the dead momentum class (`TRACKA2-P3B-DINV-1D` standing veto /
  `FX2-H1TSMOM-C1`). The exit-overlay class is separately dead:
  `BRV1-RISK-OVERLAY` (BTC-H4-BAND-RISK-V1: TRAIL/CAT/COOLDOWN exit-side
  overlays, CLOSED — overlays cut winners and losers proportionally,
  de-concentration by exit law impossible). Skeleton match on the overlay
  axis: exit-law modification on a trend book; payer: none of its own (the
  census's own UNCLEAR).

### 14. USDCAD-S025 — range_retest_continuation (Multi-week range retest continuation)

- Source: symbols/USDCAD.md:297-299 (S25): break of a >=15-day range, first
  retest + rejection candle on D1 close enters continuation; OI confirmation
  optional; payer: institutional reallocation stop-flow pays the retest.
- Verdict: **REJECT_VARIANT_SAME_FAMILY** (census DISTINCT_TESTABLE —
  OVERTURNED).
- Dead ancestors: `FXFV2-A4-P2` (FOREX-FREE-V2, "London-AM range break +
  retest-hold", CONTROL_REPRODUCED_MECHANISM — placebo ≈ anchor -3.093/trade:
  the break+retest skeleton on FX is measured-dead; S25 is the same skeleton
  re-clocked intraday->D1, §14.3). `TRACKA2-C1C2C3-REGATED-RANGEFADE`
  (ERP1-TRACKA-COHORT-2: RECLAIM-ABSORB retest-gated range-edge fade,
  VARIANT_SAME_FAMILY — "stripping each new observable degenerates to the dead
  R-ANCHOR/RANGEFADE decision law (same trigger-direction-exit, same
  stop-flow payer)"; fence: range-adjacent triggers permanently closed against
  gate variants, reopening only for NEW payer + NEW information layer). S25's
  trigger is range-adjacent (the broken range boundary), its payer is stop-flow
  ("institutional reallocation stop-flow") — the same payer family the fence
  names — and its information layer is own-price levels + a rejection candle.
  The continuation-vs-fade sign difference vs the fenced family is a sign flip
  (§14.3; P-28 inverted-control doctrine: sign-flip is adjudicated as the same
  family, and here BOTH signs are already dead: fade side
  TRACKA2-C1C2C3/`TRACKA1-M1-RANGEFADE-PIT`, continuation side FXFV2-A4-P2).
  `DT100-83-FAILBRK` (failed-breakout reversal, census #83 "Range-fade class",
  exp -10.56 bps PF 0.569, 32586 trades) — the same breakout-retest skeleton,
  opposite sign, dead. The census's own ancestry_hits listed FAILBRK and still
  called the row DISTINCT_TESTABLE; that call is overturned.

### 15. USDCAD-S004 — tsmom_20d (200DMA dislocation momentum) [MANDATORY DEEP-DIVE]

- Source: symbols/USDCAD.md:205-207 (S4): |price - 200DMA|/ATR200 > 2 with
  same-sign 20D momentum => join dislocation direction; stop halfway back to
  the 200DMA; payer column: "UNCLEAR (slow structural repricing flows)".
- Verdict: **REJECT_VARIANT_SAME_FAMILY** (census DISTINCT_TESTABLE —
  OVERTURNED).
- The mandatory question: does a 200DMA-dislocation-gated 20d momentum on one
  FX pair survive, or is it the dead TSMOM class re-clocked? It does not
  survive. Adjudication:
  - `TRACKA2-P3B-DINV-1D` standing veto (measured ON USDCAD: worst shadow
    `FX2-H1TSMOM-C1` rho 0.3032): a day-clock own-price continuation book on
    USDCAD IS the dead H1 TSMOM class; reopening condition NONE. The
    200DMA-dislocation condition is a GATE on that law; per P-29 the gate
    state (distance from a 200-day moving average, normalized) is itself a
    slow momentum level-window — the gate IS the ancestor, not a new
    information layer.
  - `CRYPTO-V9::XSECT-TSTREND-L14/L28` (TSMOM, 10-alt weekly clock, V9_REJECT_
    ALL_MULTI_FAMILY 5/5 frozen trials rejected, denominator 117) and
    `DT100-80-TSMOMH` (TSMOM re-clocked hourly, exp -10.59 bps PF 0.83, 0/4
    folds; census #80 verdict "XSECT-TSTREND L14/L28 5/5 NOT_ELIGIBLE") are the
    named class twins the census itself listed. A third clock (D1) and a fifth
    symbol do not move any §14.3 axis.
  - The census's distinctness claim ("deviation-continuation skeleton distinct
    from S2 breakout") compares rows WITHIN the slate; being distinct from
    another dead-family row is not novelty against the TSMOM ancestor.

---

## Verdict table (15 lines)

| # | gid | mech_key | Verdict | Dead ancestor (primary) | Axes matched |
|---|-----|----------|---------|--------------------------|--------------|
| 1 | GBPUSD-S079 | cta_unwind_join | REJECT_VARIANT_SAME_FAMILY | TRACKA2-P3B-DINV-1D (+COMMNG1-A4-P2-ARM1-NEUTRAL, XSECT-TSTREND-L14/L28, DT100-80-TSMOMH) | skeleton (momentum continuation), information (own price) |
| 2 | USDJPY-S012 | tokyo_range_fade | REJECT_VARIANT_SAME_FAMILY | FXFV2-A4-P1 (+FXFV2-A4-P2, FXFV1-A3-P1/P2, DT100-09-ASIANRANGE) | skeleton (session-range conditioned London entry, sign-flipped), information (Tokyo-range/ATR), payer (session chasers) |
| 3 | EURUSD-S027 | vol_expansion_onset | REJECT_VARIANT_SAME_FAMILY | DT100-71-RVREGIME (+H-VOLCOMP-BRKOUT-v1, FX2-H1DONCH-C1 via TRACKA2-P3B) | skeleton (vol-state breakout continuation), information (own-price vol ratio) |
| 4 | AUDUSD-S001 | ema_stack_trend | REJECT_VARIANT_SAME_FAMILY | TRACKA2-P3B-DINV-1D / FX2-H1TSMOM-C1 (+ES1-BAND-TREND) | skeleton (MA trend state), information (own price), payer (momentum premium) |
| 5 | AUDUSD-S003 | adx_macd_persistence | REJECT_VARIANT_SAME_FAMILY | TRACKA2-P3B-DINV-1D (gate on dead law; P-27/P-29) | skeleton (momentum persistence + gate), information (own price) |
| 6 | AUDUSD-S017 | td_sequential_fade | REJECT_VARIANT_SAME_FAMILY | FXOS-04 (+mean-reversion-transfer, FX2-STOCH-C4 shadow) | skeleton (oscillator exhaustion fade), information (own price), payer (stop cluster) |
| 7 | AUDUSD-S087 | volume_profile_poc | REJECT_DATA_OR_COST | none (data kill): volume column absent on AUDUSD panels; M5 below H1 ceiling | n/a — missing authority named |
| 8 | AUDUSD-S088 | round_number_defense | REJECT_DATA_OR_COST | secondary TRACKA2-C1C2C3-REGATED-RANGEFADE fence | data: M5 + tick volume absent; fence: range-adjacent trigger |
| 9 | AUDUSD-S002 | donchian_breakout | REJECT_VARIANT_SAME_FAMILY | FX2-H1DONCH-C1 via TRACKA2-P3B-DINV-1D standing veto (+PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION, PSV1-BTC_H1-UPTREND-BREAKOUT_CONT) | skeleton (channel breakout), information (own price), payer (stop flow); gate difference is a variant |
| 10 | USDCAD-S002 | donchian_breakout | REJECT_VARIANT_SAME_FAMILY | FX2-H1DONCH-C1/FX2-H1TSMOM-C1 via TRACKA2-P3B-DINV-1D (+PSV1 pair, DT100-80-TSMOMH) | skeleton (channel breakout), information (own price) |
| 11 | AUDUSD-S046 | weekday_seasonality | REJECT_NOT_STANDALONE | source-declared non-standalone (+DT100-34-WEEKEND, V17-A4-P1-WKNDLIQ as class twins; payer DOES differ from SFV3-A6-TOM-SETTLE — cannot rescue a non-book) | bookability |
| 12 | USDCAD-S047 | winter_seasonality | REJECT_DATA_OR_COST | none as variant (payer genuinely differs from SFV3-A6-TOM-SETTLE); missing: WTI hedge panel + decision power (~5 episodes) | n/a — missing authorities named |
| 13 | EURUSD-S009 | macd_divergence_exit | REJECT_NOT_STANDALONE | BRV1-RISK-OVERLAY (exit-overlay class dead; entry leg = dead momentum class) | skeleton (exit overlay), bookability |
| 14 | USDCAD-S025 | range_retest_continuation | REJECT_VARIANT_SAME_FAMILY | FXFV2-A4-P2 (+TRACKA2-C1C2C3-REGATED-RANGEFADE fence, DT100-83-FAILBRK sign twin) | skeleton (breakout-retest), information (own-price levels), payer (stop flow) |
| 15 | USDCAD-S004 | tsmom_20d | REJECT_VARIANT_SAME_FAMILY | TRACKA2-P3B-DINV-1D / FX2-H1TSMOM-C1 (+XSECT-TSTREND-L14/L28, DT100-80-TSMOMH) | skeleton (gated momentum continuation), information (own price; gate IS a momentum state) |

Census re-adjudication summary: 15 DISTINCT_TESTABLE -> 0 ADMIT, 11
REJECT_VARIANT_SAME_FAMILY, 2 REJECT_NOT_STANDALONE, 2 REJECT_DATA_OR_COST.
All 15 census DISTINCT_TESTABLE verdicts are OVERTURNED.

## Incidents / notes for the record

- N-1 (census defect, MEDIUM): the census `ancestry_hits` column reported
  "none-found" for GBPUSD-S079, USDJPY-S012, AUDUSD-S001/S003/S017/S087/S088
  while at least nine applicable CLOSED forex ancestors exist in
  FAMILY_FAILURES.jsonl (FXFV1-A3-P1/P2, FXFV2-A4-P1/P2, FXOS-04, the TRACKA1/
  TRACKA2 families measured on AUDUSD+USDCAD 2021-2025). The census's ancestry
  search appears keyed to the families named in the 12 non-distinct rows
  (PSV1/DT100/SFV3/BRV1/XSECT) rather than to a full family-class scan. Every
  "none-found" claim in the input TSV should be treated as unverified.
- N-2 (census defect, LOW): census verdict_reason for AUDUSD-S002 says "ungated
  two-sided Turtle" while the source text (AUDUSD.md S2 coupling) carries
  "gate ADX14>20". Immaterial: gated or ungated, the row is the dead class
  (gate differences are variants per P-27).
- N-3 (data-ceiling nuance, recorded for the data lane, not a verdict change):
  the ERP1-TRACKA-COHORT-1 corpus physically holds RAW Dukascopy M1 BID+ASK
  day-files for AUDUSD and USDCAD (2,007 files/side/pair, 2021-01..2026-06,
  with volume_f32 in the .bi5 records per duka_lib.py) — but the SLEEVE
  declares AUDUSD/USDCAD as H1/15m-only, and this court adjudicates against
  the declared ceiling. If the sleeve's data authority is ever extended to
  those raws, rows 7-8's data kills would need re-adjudication; the ancestry
  fences in rows 9/10/14/15 would NOT change (pair data was never their
  basis).
