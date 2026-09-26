# SKEPTIC_cohort1_REPORT — ERP-TRACKB-PROGRAM-V1 cohort-1 F-0 mechanism-class court (pre-PnL)

- Lane: trackb-cohort1-skeptic (economic skeptic, pre-PnL VETO per umbrella §5.1/§5.4 Track B,
  trackb plan §3/§6). Outcome-blind: no scored-result file read beyond FAMILY_FAILURES.jsonl
  summaries + umbrella §4.5 context, per dispatch. Read-only except the two deliverables.
- Measured intake: root `main` @ `e4e3b9159685b9da0bafeed6814f0a73c872cbcb` (== dispatch_sha).
- Verdict in one line: exactly ONE mechanism class is admissible to cohort consideration
  (funding-level-gated, low-turnover, breakeven-horizon cash-and-carry — conditional on one-shot
  ancestry rho); every other plausible class is VETOED or BLOCKED pre-PnL; prior that this cohort
  is killed pre-PnL ≈ 0.70–0.80.

## 1. F-0 adjudication criteria (skeleton; applied to every proposal BEFORE rho, BEFORE PnL — P-27 law)

Each proposal must pass all four tests. Failure of any one = VETO; "passes with a new gate" is
not a pass (TRACKA2 precedent: "adding an observable is measured NOT to create a new mechanism").

1. **Skeleton test (structural distinctness).** Strip every newly added observable, gate and
   regime variable from the proposed decision law. If the residual trigger/direction/exit is the
   decision law of a dead ancestry family, the proposal is a VARIANT of that family, not a
   mechanism. Ancestor preconditions on this surface: CARRY-1D/3D/7D (V6), BAB-LOWBETA (V12),
   OITD (V13), BASISLV-PREMFADE-28D (V14), H-FUNDCROWD-MR-v2, XSECT-FUND-CARRY-7D (retired,
   cost:carry 77:1). This surface's aggravating fact: the ONLY scoreable form (unlevered long
   spot + short perp) has one skeleton by construction — "hold the carry book while expected
   carry clears cost." Distinctness can therefore live only in the ENTRY/EXIT information law
   and the payer, never in the book's shape.
2. **Payer test (who is forced to pay, why not arbitraged away).** Must name an identifiable
   counterparty with a structural constraint who pays the carry, and why capital cannot close
   the gap. "Market drifted up", "momentum", or unnamed-flow payers fail. Note for this surface:
   the payer test is nearly always passable (levered perp long demand is real and structural) —
   a pass here must NOT be read as mechanism novelty; P-27 lesson 3: novelty does not fund
   the bill.
3. **Information test (new observable or dead observable re-gated?).** The proposal's observable
   must not be a monotone transform, percentile rank, windowed average, change-of, or gate on an
   observable that a dead family already consumed. Measured precedents that bind THIS axis:
   V17 FUNDJUMP — the funding-announcement CHANGE form still carried the forbidden funding
   LEVEL (pooled |rho| 0.2439, D2 kill); V16 RUNPERSIST — cleared the funding-proxy razor by
   only 0.0073 (0.1927 vs 0.20). Transforms of funding/basis are not new information.
4. **Cadence test (re-clocking launders nothing).** Q-3: cadence is part of family identity;
   a cost-gate failure at one cadence is not evidence about another, and moving a dead law to a
   faster/slower clock (1D→28D, daily→8h-settlement-count, weekly→monthly) is an ancestry veto
   (P-27 lesson 4, confirmed in cohort-2). The class vetoes of umbrella §6 (re-clock, calendar
   geometry, displaced-fade, nominal-level, vol-level, premium-fade −0.418/−0.515) apply
   regardless of any measured rho.

## 2. Ancestry rho plan (one-shot, skeptic lane; computed once, no re-specification)

- **Candidate representation (exact):** per-mechanism decision-state series `d_c(t)` on the
  PIT-clean funding-settlement grid (8h; settled `fundingRate` values only — the next interval's
  rate is PREDICTED and excluded) unioned with the synchronized daily spot–perp basis grid where
  the mechanism reads basis. State alphabet {FLAT, LONG_CARRY} (+ transition epochs). Values
  enter only at their available time (truncation proofs M-class P-18 apply to every regime
  variable before rho is computed; a day-boundary or same-bar look leak voids the rho, not
  the bar).
- **Dead-family reconstructions (same grids, overlapping window):** CARRY-1D/3D/7D funding-level
  carry state (V6); CARRY-BAB funding proxy (the V16 razor reference); XSECT-FUND-CARRY-7D
  decision state (retired PSV1 sleeve 3, single-symbol projection); H-FUNDCROWD-MR-v2 funding-
  percentile state; BASISLV-PREMFADE-28D basis-level state (V14). FOREX-V4 carry class
  (rho 0.997–1.000) is cross-asset — recorded as CLASS precedent, not pooled.
- **Statistic:** pooled Spearman |rho| per observable axis (funding-level axis; basis-level
  axis), candidate vs each dead state, pooled across overlapping window; bar |rho| ≤ 0.20,
  immovable. Computed ONCE by this lane after council freeze; a candidate failing dies with no
  rescue by re-gating (§6 no-rescue law).
- **Class vetoes that apply regardless of rho:** premium-fade ancestry −0.418/−0.515
  (bear-recon measured; binds any short-premium/basis-fade entry); carry-class 0.997–1.000
  precedent (any decision state ~monotone in carry level inherits the closed class); re-clock
  (Q-3); calendar geometry (COMMODITIES-NG1: bare release-clock control out-earned all anchors;
  PSV1 block-shuffle kills); nominal-level and vol-level exposure vetoes.
- **Honest calibration:** on this exact axis the realistic rho outcomes are NOT near zero —
  V16 cleared by 0.0073, V17 measured 0.2439. Any class whose entry is a monotone function of
  funding level over a horizon should be expected to measure > 0.20 vs the pooled funding-level
  proxy. Proposers should pre-register why their state is NOT monotone in funding level, or
  accept the kill.

## 3. The economics, adversarially (cash-and-carry premium, BTCUSDT)

- **Who actually pays.** Perp longs pay funding to perp shorts whenever perp trades above the
  premium index. Aggregate payer = levered long demand that cannot or will not hold spot:
  margin-constrained speculators, capital-efficiency seekers (perp = no custody, no venue split,
  1:5–1:10 notional per margin dollar), jurisdiction/KYC-frictioned flow, and size classes below
  spot-logistics economics. Secondary: hedgers shorting perp against inventory pay at premium
  peaks. This is a genuine convenience-yield payment for synthetic exposure — it survives.
- **Why the premium persists.** The arbitrage that would compress it is balance-sheet-costly:
  full-notional spot lockup (return on capital ≈ funding − costs; institutional hurdles leave
  the premium wide at low/normal funding), venue counterparty risk (FTX-class), margin/liquidation
  management cost of the short leg, and tail-gap risk. The carry IS rent for bearing exactly
  these — which means a backtest that models none of the venue/tail costs is modeling the
  counterparty's payment without the reason they pay it. Price-only disclosure clause (law c)
  is therefore not cosmetic here.
- **What erodes it.** (i) Endogenous compression: the entry signal peaks exactly when basis-
  trader capacity is scaling fastest; realized forward funding over an 18–34 day hold must be
  evidenced, not assumed equal to entry funding (F-5 must use the measured settlement-path
  distribution, per §5 stress law). (ii) Venue fee-schedule changes — dated cost-regime
  boundaries only, never in-place rewrites (§8). (iii) Regime flip: 24.7% of in-downtrend
  settlements NEGATIVE (worst −0.30%/8h ≈ 2.5 fee round-trips per plan §5 anchor); the book
  pays to stay hedged precisely when its exit costs a full RT.
- **Tails the book actually eats (honest list).** 1) Venue counterparty — both legs, one venue
  (§5.15 concentration; the 2026-09-21 shared-IP 418 precedent kills both legs jointly). 2)
  Liquidation-cascade gap on the short perp leg: an up-move drains perp margin while the offsetting
  spot gain is not instantly movable across accounts — unlevered does not mean margin-unmanaged.
  3) Funding sign flips / extended negative funding inside the mandatory ≥18–34 day hold. 4)
  Basis blowout AFTER entry at signal peaks — max adverse MTM coincides with max signal. 5)
  Forced unwind: margin event closes the perp leg at the worst print, unmasking naked spot or
  realizing the gap. 6) Hedge drift/tracking error two-leg (booked per §5.2). 7) Entry-basis
  reversal: entering at wide premium is only profit if premium converges within hold — that
  income leg is premium-fade by construction (disclose, don't hide it in "funding").

## 4. Mechanism-class adjudication NOW (no-rescue law applied strictly)

| # | Class | Verdict | Reason (F-0 test that kills/admits) |
|---|---|---|---|
| A | Funding-level-gated low-turnover cash-and-carry: enter when expected carry over the declared holding period ≥ full RT stress cost; hold ≥ breakeven horizon | **ADMIT (conditional)** | Umbrella §5.4(a–c) carves exactly this form as the lawful successor; payer test passes (levered longs); the cost-arithmetic entry law is the one candidate non-dead element. Binding: new strategy ID; one anchor + ≤2 holding-period neighbours (no post-outcome gate re-parameterization); funding-path stress; price-only disclosure; dies at F-1 if pooled rho > 0.20 vs funding-level proxy, at F-5 if compression makes the ceiling negative. |
| B | Basis-level-conditioned entry (enter when spot–perp basis > threshold; harvest convergence + funding) | **VETO** | Skeleton test: strips to BASISLV-PREMFADE-28D's observable and decision law (V14 dead, fold conc 0.5110); premium-fade ancestry class veto −0.418/−0.515 applies regardless of rho. "28D basis fade is BASISLV re-incarnated" — dispatch law verbatim. |
| C | Funding-momentum / sign-persistence carry (k consecutive positive settlements, rising funding) | **VETO** | Information test + measured precedent: V17 FUNDJUMP change-transform carried the forbidden funding LEVEL (rho 0.2439, killed at D2). Sign-persistence is a re-gating of the dead observable; no new payer. |
| D | Volatility-of-funding gated carry (enter when funding variance low) | **VETO** | Vol-level class veto (umbrella §6); information test fails (variance of funding = transform of funding); no new payer; arithmetic: a second gate on a 3.2 bps/day gross stream can only cut occupancy, never raise per-day carry. |
| E | Calendar/session-conditioned carry (settlement-tick geometry, day-of-week funding) | **VETO** | Re-clock + calendar-geometry class vetoes; COMMODITIES-NG1 measured: bare release-clock control out-earned every anchor; PSV1 block-shuffle. The 8h settlement clock is the most-arbitraged calendar in crypto; PIT-fragile besides (predicted ≠ settled, §2). |
| F | Negative-funding inverse (short spot + long perp when funding < 0) | **VETO-STRUCTURAL** | Not scoreable: spot borrow/short is BLOCKED data (Track B law (e)). It is also, by construction, the mandatory INVERTED-CONTROL arm of class A — a control, not a mechanism. |
| G | Cross-sectional funding carry / funding-percentile gate (multi-symbol) | **VETO** | Dead ancestry re-gated (XSECT-FUND-CARRY retired at 77:1 cost:carry; FUNDCROWD-MR-v2 killed at 68–81% fold concentration); percentile gate named dead by dispatch verbatim; also out-of-surface (home surface = ONE pair). |
| H | OI / basis-term-structure-conditioned carry | **VETO + BLOCKED** | OITD dead (V13 EXPECTANCY_NONPOSITIVE); multi-year PIT OI absent (overwritten ~41.6h, Track C measured) — the conditioning variable does not exist PIT. |
| I | Funding-spike entry after liquidation cascades ("forced-flow carry") | **VETO** | Liquidation tape BLOCKED (Track C: zero coverage) — the causal variable is unavailable; funding-spike entry degenerates to funding level (information test); Track C flow wearing Track B clothes. |

Net: the admissible mechanism-class space is ONE class (A) whose honest variants are holding-
period/horizon neighbours of a single law. A cohort freezing "3 mechanisms" here would be
freezing 3 parameterizations of one mechanism — the council should freeze fewer and say so.

## 5. Six economic questions — adversarial answers at the measured anchors

1. **Who pays?** Levered perp longs (funding when premium > 0); structurally leverage-demanding,
   custody-averse, capital-efficiency-seeking flow. They are the demand; they cannot arbitrage
   themselves away.
2. **Why are they forced/eager?** The perp exists because this cohort prefers synthetic exposure:
   no custody ops, no venue split, higher notional per margin dollar, access friction. The
   premium is their convenience yield.
3. **Premium (expected bps/period).** Mean 2020–2026 ≈ 3.23 bps/day (11.798%/yr); in-downtrend
   mean 1.11 bps/day; conditional entry states above mean — with UNKNOWN forward persistence.
   Income only accrues while held; 24.7% of in-downtrend settlements are negative.
4. **How long does it persist / what erodes it?** Persistence = balance-sheet cost + venue-risk
   premium of the arbitrage crowd. Erosion: endogenous compression (entry at max crowding),
   fee-schedule changes, regime flips to negative funding. The book's ≥18–34 day minimum hold
   spans exactly the episodes where compression is fastest.
5. **What risk do we take for it?** The tails in §3 (venue counterparty both-legs, cascade-gap
   margin, funding sign flip, entry-basis blowout, forced unwind, drift, outage). A backtest
   that omits venue/tail costs books the counterparty's payment without the reason they pay.
6. **When does the fee bill exceed the premium?** Breakeven days = RT stress ÷ realized daily
   carry: mean funding 6.2–7.7d; downtrend 18–23d; ×1.5 stress 27–34d; ×2.0 stress 36–45d
   (derived). One −0.30%/8h settlement = 30 bps ≈ 1.2–1.5 full RTs (2.5 fee-only RTs per §5
   anchor) repaid in one tick. **Class-A unfundability arithmetic:** if post-entry compression
   halves realized funding (c = 0.5 of entry level), realized breakeven doubles to 12–46d,
   exceeding typical compressed-episode length → F-5 CEILING_NEGATIVE. A single hold spanning
   a funding sign flip is gross-negative before drift at any stress tier. If the entry gate
   selects states whose forward 18–34d funding does not STAY above RT/hold, the class is dead
   by its own entry law — which is the correct, expected kill.

## 6. Skeptic verdict

- ADMIT to cohort consideration: class A only, with the five binding conditions of §4/A.
- VETO: B, C, D, E, G, H, I; structural: F. Any proposer variant of B–I arriving with a "new
  gate" is dead on arrival at F-0 (no-rescue law; P-27 precedent applied by measurement in
  ERP1-TRACKA-COHORT-2).
- Most dangerous ancestry-collision risk: class A's decision state is monotone in funding level
  over the holding horizon; the one-shot rho vs the pooled funding-level carry proxy should be
  expected to breach 0.20 (V16 cleared by 0.0073; V17 0.2439). The F-1 rho, not the economics,
  is the modal pre-PnL killer — and if it kills, the cohort closes NO_ELIGIBLE_PROPOSAL /
  REJECT_ALL-at-F-stage with 0 scored cells, which is a first-class outcome (Q-16).
- Prior cohort killed pre-PnL by cost arithmetic and/or court: **0.70–0.80** (rho ≈ 0.35 of the
  mass; F-5 compression ceiling ≈ 0.25; PIT/data gate ≈ 0.10; survival to GO-2 ≈ 0.20–0.30).
