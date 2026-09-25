# SKEPTIC_track_falsification_REPORT — ECONOMIC-ROBUSTNESS-PROGRAM-V1 (plan_review lane)

- Role: economic-mechanism skeptic (read-only). Task `erp1-skeptic-tracks`.
- Measured base: root checkout `main` @ `7343dde57fe86b38d205b0bec5e8af92a4c4404d`
  (== dispatch sha; tree clean except the 5 known untracked paths, none touched).
- Scope: attempt to FALSIFY, pre-PnL, the three candidate tracks (A: FX
  RANGEFADE, B: delta-neutral crypto basis/carry, C: forced-flow/event
  premiums) at the economic-mechanism layer, and check the owner's
  adjudication direction against measured repo evidence.
- Method: every claim below cites a committed artifact (plan, terminal
  report, failure-registry row, control-tree review). No scored computation
  was run in this lane; all numbers are quoted from artifacts. The failure
  census used: `research/wayfinder/FAMILY_FAILURES.jsonl` (124 entries),
  `research/wayfinder/MAP.md`, `plans/PLAN_prospective_shadow_v1.md` (§3/§14),
  `research/control/SHADOW-PAPER-REVIEW-V1/REVIEW.md` + both lane REPORTs,
  `research/control/bear_opportunity_recon_2026-09/` (ANCESTRY_TABLE +
  RECON_ADJUDICATION), `plans/PLAN_eurusd_rangeexp_scored_v1.md`,
  `plans/PLAN_ethusdt_open_search_v1.md` §1.

---

## TRACK A — FX liquidity provision / RANGEFADE (wide-prior-day-range fade)

### A.1 Mechanism steelman (3 sentences)

The payer is the breakout/stop-flow crowd: buy-stops stacked above the prior
day's high and sell-stops below its low are triggered mechanically when a
wide-range day extends, and retail/momentum breakout traders chase the
extension; they are "forced" by order placement, not by opinion, and they
transact at the worst inside prices of the session. The premium is the
reversal premium of failed breakouts — the fader provides liquidity against
stop-flow and is compensated for wearing the tail risk that the breakout is
real (news/central-bank days, where the fade loses largest). Persistence
requires only that intraday FX spot lacks persistent one-way flow on most
days and that stop-cluster geometry (prior-day extremes) is publicly known —
a structural feature, but one that decays exactly when trend regimes cluster.

### A.2 Strongest falsification argument FROM REPO EVIDENCE

The strongest repo evidence against Track A is not a veto but a measured
confound plus a family precedent of dev-positive/OOS-negative fade books:

1. **The EURUSD holdout net is not separable from short-USD drift.**
   `EURUSD-OPEN-SEARCH-V2` terminal (MAP.md bullet, 2026-09-23): fresh
   holdout C3 +274.0 pips PF 1.31 / C4 +217.1 PF 1.24 — but
   **SHORT_ALWAYS +314.0 on the same window beats both** (holdout margins
   −17.3/−17.6 pips), and "SHORT-beta control mandatory" is preregistered
   in the terminal; `plans/PLAN_eurusd_rangeexp_scored_v1.md` S6 makes the
   drift flag mechanical, and the scored close
   (`EURUSD_RANGEEXP_SCORED_V1_SCORED_RECONCILED_NO_DRIFT_FLAG`, MAP.md
   2026-09-24) cleared dev only (short share 42–48% < 50%); the holdout
   margin vs SHORT_ALWAYS remains −17.3/−17.6 pips on 87 trades — well
   inside one bad week. On this evidence, part or all of the EURUSD holdout
   net is beta, not liquidity provision.
2. **The fade family has already produced one selection-luck kill.**
   Registry row 120 (`EURUSD-OPEN-SEARCH-V1|FXOS-04`,
   `research/wayfinder/FAMILY_FAILURES.jsonl`): dev +1,203.6 pips PF 1.1445
   (5/48 trials positive) → holdout −134.4 @1.0x / −585.1 @1.5x,
   `HOLDOUT_NET_NEGATIVE`, "dev edge attributed to selection luck."
   Adjacent range books also died mechanism-free: row 35
   (`FXFV2-A4-P2` London-AM range break) `CONTROL_REPRODUCED_MECHANISM`
   (placebo −3.093/trade ≈ anchor); row 34 (`FXFV2-A4-P1` Tokyo-range
   compression) `EXPECTANCY_NONPOSITIVE`, cost-dominated (break-even
   −0.40 bps); row 33 (`FXFV1-A3-P2` late-NY fade) negative.
3. **The running shadow's cost book is optimistic and its decisive control
   is unmounted.** `research/control/SHADOW-PAPER-REVIEW-V1/REVIEW.md`
   (A1/A2, lane_fx_gold REPORT §2.1–2.2): fills price at TrueFX indicative
   opposite-quote only (measured 0.4/0.7 pips vs Dukascopy census p50
   0.3/0.8) — top-of-book, not tradeable; and **no short-beta/SHORT_ALWAYS
   control arm exists anywhere in the daemon code** despite the ancestor
   law being MANDATORY — so prospective FX PnL cannot separate range-fade
   edge from short-beta exactly when the market falls, which is the one
   question the preregistration was written to answer.

### A.3 Verdict: SURVIVES_AS_HYPOTHESIS (conditional, controls already named)

This is the only track whose ancestor survived a **fresh, one-look holdout
under measured two-sided costs at 2.0x stress** and **replicated
cross-pair**:

- GBPUSD is the cleanest anti-drift evidence in the program (MAP.md,
  FX-MAJORS-SEARCH-V1, 2026-09-24): dev +8,525.2 pips PF 1.642 **6/6 folds
  positive**; holdout +164.2/+105.3/+46.4 @1x/1.5x/2x in a window where
  **every baseline lost** (LONG −132.9, SHORT −47.1, RANDOM −1,546.9) — the
  mechanism earned in a directionless half-year, which is precisely the
  liquidity-provision signature.
- EURUSD-OPEN-SEARCH-V1 precedent (row 120) is distinguished, not
  re-labeled: FXOS-04 was a single survivor of 48 trials that never passed
  a fresh holdout; FX2-RANGEEXP C3/C4 passed one (C3 +274.0 / C4 +217.1,
  alive at 2.0x, MAP.md 2026-09-23), and the scored decomposition shows
  both legs profitable in both windows (C3 dev +3,783L/+3,364S; holdout
  +154.6L/+119.4S).

**Specific falsifier a child plan must freeze (pre-PnL):** a matched
SHORT_ALWAYS arm (same sizing, windows, force-flat, cost book) run in the
same journal, per pair; EURUSD passes only if prospective C3 net > matched
SHORT_ALWAYS net over a preregistered decision count; GBPUSD adds no
short-beta pass (its holdout baselines were all negative) but must still
carry the arm for symmetry. A JPY carry-beta control (LONG_ALWAYS on the
carry-rally window) is MANDATORY before any USDJPY sleeve (MAP.md:
USDJPY thin, die at 2x, LONG_ALWAYS +532.5 dominates). The control must be
mounted BEFORE further prospective accumulation — today it is not
(REVIEW.md A1), which is the largest live compliance gap on this track.

### A.4 Ancestry-veto risk: LOW–MODERATE

No ancestry rho veto exists against the FX2-RANGEEXP construction itself
(the dead fade rows — late-NY fade, Bollinger 15m z-fade, Tokyo compression,
London-AM break — are different representations; none was rho-measured
against it, and the V2/SCORED cycles passed A7 with this disclosed). The
residual risk is class-level: it shares the "fade" class with three
registry deaths and one holdout death, and its EURUSD economics are one
thin holdout margin away from being a short-beta book. It is a live
`CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION`, not a rejected family
re-labeled — but a child plan that drops the short-beta control would
instantly become one.

---

## TRACK B — delta-neutral crypto basis/carry (perp funding + spot-perp basis)

### B.1 Mechanism steelman (3 sentences)

The payer is the leveraged directional perp crowd: when longs are crowded,
they pay funding to shorts (and vice versa), so a position supplying the
scarce side collects an insurance-like premium for bearing squeeze risk and
capital lock-up; a spot-perp basis harvester earns the same premium
integrated over the basis convergence. Persistence relies on leverage
crowding recurring cycle after cycle and on limits-to-arbitrage (margin,
liquidation, venue risk) keeping capacity-constrained harvesters
compensated. The kill condition is arithmetic: the premium is a few bps per
8h settlement, so any taker-turnover cost stack larger than the harvest
turns the book into a price book with a negative carry overlay.

### B.2 Strongest falsification argument FROM REPO EVIDENCE

The repo has already measured the kill arithmetic, in the running shadow,
under frozen costs:

1. **The live book is cost-dominated by ~6x.** XSECT-FUND-CARRY-7D booked
   **−298.22 USDT** in 10 decisions (fee 246.43 + slip 56.40 = 302.83 vs
   funding **+4.60**) — cost run-rate ~11%/yr vs funding capture ~1.7%/yr;
   the shadow is "paying the spread, not harvesting the premium"
   (`research/control/SHADOW-PAPER-REVIEW-V1/REVIEW.md` §1 + lane_crypto
   REPORT §3.1, from ledger bytes at
   `.worktrees/prospective-shadow-v1/integration/results/prospective_shadow_v1/`).
2. **The historical profit was lineage-cost-soft and fold-concentrated.**
   V6 CARRY-7D +20,580.87 PF 1.157 with top-positive-fold share **51.66% >
   50%** (`CANDIDATE_FAIL`, registry row 1); funding contributed only
   +2,277 of the +20,580 (~11%) under the softer lineage cost book
   (`plans/PLAN_prospective_shadow_v1.md` §3.3); SPRINT-CRYPTO
   H-FUNDCROWD-MR-v2 died at 68–81% single-fold+symbol concentration
   (row 42).
3. **"Basis fade" is measured to BE carry harvest.** BASISLV-PREMFADE-28D's
   identity manifest records the price-only failure clause **binding**: the
   +0.700/PF 1.360 V14 book's positive expectancy was mainly funding
   credit, not premium convergence; it was rejected on fold share **0.5110
   > 0.50** with program DSR **0.00224** over 146 trials
   (`PLAN_prospective_shadow_v1.md` §3.2; registry row 14; lane_crypto
   §4.3: "hai sleeve gần như là cùng một trade với hai mặt nạ").
4. **The carry front door is ancestry-closed across asset classes.** FOREX
   carry closed at D2 by measured rho **0.997–1.000** vs invalidated
   ancestors (registry row 38 / MAP FOREX-V4); funding-LEVEL is itself an
   active dead shadow (V17 FUNDJUMP rho **0.2439**, row 59); BAB-LOWBETA
   died `COST_DOMINATED` (row 10); VOL-NG1 died
   `COST_CEILING_FAMILY_KILL` (rows 101–103).
5. **Cost realism law already fired once.** Funding measured
   **11.798%/yr = 7.8x the frozen constant** (BTC-H4-EDGE-SEARCH-V1,
   `feasibility_census.json`, cited in REVIEW.md §2.5) — any historical
   carry/basis number computed with funding constants is unreliable, and
   the current shadow's own cost book is a DECLARED fallback
   (`UNAVAILABLE_FAIL_CLOSED_FALLBACK_DECLARED`, lane_crypto §2).

### B.3 Verdict: VETO_RISK_HIGH (as stated; one narrow lawful reframe)

As stated — "delta-neutral crypto basis/carry" harvested at the repo's
retail taker cost stack — the track is measured cost-dominated in the only
live measurement that exists, and its two scored ancestors are rejected
(51.66% and 0.5110 fold concentration; DSR ~0.002). Note what is NOT
scored-dead: a true spot+short-perp basis book (hold-to-convergence,
maker-only) is a different (info-source, vehicle) tuple from
funding-LEVEL carry and cross-sectional premium fade; but its PnL identity
is funding capture − borrow/margin/venue costs, and the repo has **zero
measured authority** for borrow, margin tiers, or venue risk (cost book
is declared, not measured — lane_crypto §2; broker cost authority was
BLOCKED fail-closed in DATA-EDGE-UNLOCK-V1 lane F, MAP.md).

**Specific falsifier a child plan must freeze (pre-PnL):** (i) a
**cost-survivability ceiling** — preregister that the book is viable only
if trailing funding dispersion premium at the decision frequency exceeds
2x(fee+slip) per rebalance at the FROZEN measured cost book, measured
before any PnL claim; (ii) a **maker-entry diagnostic book** parallel to
the taker book (lane_crypto Ý 6) with an explicit no-fill probability
model — if the maker view is also negative, the premium is dead in this
regime, not mis-costed; (iii) for any BASISLV-lineage child, the
**price-only expectancy clause** (must remain positive, else it is carry
harvest — §3.2 verbatim) as the causal/inverted control; (iv) turnover
hysteresis bands as a preregistered structural amendment, not a tweak
(REVIEW.md A2). Without (i)–(iv) frozen first, the track re-runs a
measured kill.

### B.4 Ancestry-veto risk: HIGH

This is the closest to "a rejected family re-labeled" of the three tracks:
funding-LEVEL carry (V6, V17 rho 0.2439), premium/basis-level fade (V14
0.5110, DSR 0.00224), funding-crowding MR (68–81% concentration),
BAB (cost-dominated), forex carry (rho 0.997–1.000) are all the same
premium at different representations, and the bear-recon ANCESTRY_TABLE
rows 7–8 mark both classes DEAD/DEAD-ADJACENT with "same-mechanism
re-parameters are NOT new (Q-3)". A delta-neutral basis book escapes a
mechanical rho veto only by changing the vehicle (spot leg), not the
mechanism; under the repo's own law that is a veto-prone posture and any
child must rho-test against the funding-LEVEL and basis-premium-fade dead
shadows at its decision frequency before anything else.

---

## TRACK C — forced-flow / event premiums with DIRECTLY OBSERVABLE flow

### C.1 Mechanism steelman (3 sentences)

The payers are genuinely forced: leveraged positions crossed by
liquidation engines, index trackers trading at rebalance effective times
regardless of price, and deleveraging cascades that must sell into
declining liquidity — their timing is set by contract or engine, not by
view. The premium is the temporary price pressure they create, harvested
by providing the other side or front-running the scheduled flow.
Persistence is structural (leverage cycles and index mechanics recur), but
the premium exists only if the flow is observable before the decision at
PIT, and only net of the crash risk of standing against cascades.

### C.2 Strongest falsification argument FROM REPO EVIDENCE

The track fails on its PRECONDITION before any mechanism question is
reached: **the directly observable flow does not exist in the authorized
evidence space, and every proxy used in its place is measured-dead.**

1. **Data authority measured absent (fail-closed).**
   `research/control/bear_opportunity_recon_2026-09/RECON_ADJUDICATION.md`
   (A7-confirmed): liquidation prints **ZERO coverage**; multi-year PIT
   OI/order-book **none** (metrics retrospective-only daily; REST OI
   ≈41.6h lookback). BTC-H4-TWO-REGIME-V1 (MAP.md 2026-09-23): liquidation
   tape **404 UNAVAILABLE_FAIL_CLOSED**; the DOWN leg found **zero**
   survivors. DATA-EDGE-UNLOCK-V1 lane C: cross-venue collectors ran
   **34 minutes << the 14-day cycle floors** → `WAITING_COVERAGE`
   (MAP.md, 2026-09-17); FREE-DATA-FRONTIER-V1: keyless crypto WS streams
   are **RETRIEVAL_TIME_ONLY / prospective-only — nothing authorizes
   historical scored joins** (MAP.md 2026-09-16).
2. **Every proxy already tried is measured-dead (ANCESTRY_TABLE rows 3–6,
   9, 14).** Price-defined liquidation episodes: V13 LIQEPIS negative
   (−0.31, verdict-invariant). OI-derived cascade: V17 OICASCADE — the
   randomized-event-time sham **out-earns the anchor** (+0.00149 vs
   −0.00266/trip). OI level/share/term-structure: V11 infeasible, V13
   expectancy-nonpositive, NG1 rho **0.3904** vs v17_oi_level.
   Premium-displacement stand-ins: V16 close-displace-fade PF **1.06356**
   razor (fold share 1.0, MDD 0.20643); CNG1 A4-P2 rho **0.3988** vs
   v16_close_displace_fade.
3. **The recon's two mechanisms were vetoed pre-PnL with reproduced
   numbers.** Confirmation-Lag Front-Run → `VETOED_FICTIONAL_COUNTERPARTY`
   (the "forced seller" was the repo's own label; its timing measured
   informationless — PSV1 G6 block-shuffle +190,392 > candidate +177,692;
   284 entries vs ≤59 claimed, 88% fake-outs). Mark-Trigger Catch-Down →
   vetoed x3: preregistered neighbour control fires OPPOSITE (−4.87% mean
   gross per short on wide-spread events vs matched crashes); power
   collapse (13 clusters, **91.1% of events in one COVID week**); ancestry
   rho **0.369 full / 0.542 event-conditional** vs the dead
   basis-premium-fade shadow, construction identity −0.68 (A7 recompute
   EXACT, RECON_ADJUDICATION.md).
4. **Event-clock lessons transfer.** Falsification-by-control #14
   (FXFV8: DGS10-LEVEL control out-earns anchor 4.01x) and #16
   (RATES-NG1: clock-only shadow +94.16 > AGGRESSIVE +78.08;
   COMMODITIES-NG1: bare release-clock control out-earned every anchor) —
   in this program, "event premium" designs have repeatedly measured as
   calendar geometry, not information; any rebalance/deleveraging event
   book must beat its own sham-clock control, which OICASCADE already
   failed.

### C.3 Verdict: VETO as a pre-PnL strategy track; lawful child = DATA-AUTHORITY cycle only

The mechanism class is respectable and the reopening law is already frozen:
"a NEW PIT-authorized data source with true multi-year coverage (e.g., real
liquidation/OI tape) or an owner plan naming a mechanism outside
ANCESTRY_TABLE.md's classes" (RECON_ADJUDICATION.md; MAP.md BTC-BEAR
bullet). Until that precondition is met, any Track C child is either (a) a
proxy book from a dead class, or (b) underpowered prospective collection —
and the only lawful first child is the data-authority lane: resume the
cross-venue collectors to their frozen 14-day floors (DATA-EDGE-UNLOCK-V1
lane C resumable state), or authorize a new PIT liquidation/OI source via
its own data-authority cycle.

**Specific falsifier/causal control the eventual mechanism child must
freeze (noted now, armed only post-data-authority):** the forced-flow
observable must be PIT-measurable BEFORE the decision; the sham control is
a randomized-event-time (block-shuffled event clock) book which must NOT
out-earn; the ancestry bar is |rho| ≤ 0.20 vs rows 3/7/9/14 shadows at the
decision frequency; and any release-clock-driven event definition must
beat its own geometry-only placebo (kills #14/#16 precedent).

### C.4 Ancestry-veto risk: HIGH (class-level, 6 of 14 rows)

Index-rebalancing specifically has no direct crypto kill in the registry
(no measured row), but it has no data authority either (SEC N-PORT is a
one-quarter cap with SPY measured-absent, MAP FREE-DATA-FRONTIER bullet)
and sits adjacent to the event-clock kill pattern. Liquidation/OI/cascade
sub-lanes are class-dead with reproduced veto numbers (above). This is
the track most likely to be rejected at D2/A7 without a scored cell —
which is exactly what happened to its ancestors (0/9 in the
three-cycle program; bear recon NO_ELIGIBLE_PROPOSAL).

---

## OWNER ADJUDICATION DIRECTION vs MEASURED REPO EVIDENCE

Directions checked: KEEP_PROSPECTIVE FX RANGEFADE (w/ short-beta control);
KEEP_PROSPECTIVE_LOW_FREQUENCY BASISLV; CONDITIONAL_KEEP BTC4H-BANDRIDGE;
DIAGNOSTIC_ONLY ILLIQ; RETIRE_CURRENT_IDENTITY XSECT.

| Direction | Conflict? | Notes with citations |
|---|---|---|
| KEEP_PROSPECTIVE FX RANGEFADE w/ short-beta control | **NO** | Matches the preregistered ancestor law (V2 terminal T1; scored terminal "short-beta control stays mandatory", MAP.md 2026-09-24). ONE live compliance flag: the running shadow has **not mounted** the control arm (REVIEW.md A1; lane_fx_gold §2.2 — no control code exists in the daemon) — the adjudication condition is currently unmet in the artifact that is supposed to deliver the evidence. |
| KEEP_PROSPECTIVE_LOW_FREQUENCY BASISLV | **TENSION (not a hard conflict)** | (a) Identity manifest records the price-only failure clause BINDING: the historical positive expectancy was funding credit, i.e. the mechanism measured as carry harvest (`PLAN_prospective_shadow_v1.md` §3.2; lane_crypto §4.3) — the same premium as the XSECT identity being retired; keeping one and retiring the other is internally consistent ONLY via the turnover argument (weekly ≈ 1/7 of daily-turnover cost run-rate: ~11%/yr → ~1.6%/yr vs ~1.7%/yr measured capture — marginal, unmeasured). (b) Power conflict: REVIEW.md §2.2 measures that weekly cadence (n≈52 decisions/yr) cannot distinguish a PF 1.3–1.5 edge at 2-sigma within 52 weeks — so this keep cannot be expected to self-adjudicate within a year; PSV1 §7 forbids promotion claims before 52 weeks regardless. The keep is lawful as observation-only; the preregistered falsifier (price-only expectancy positive; weekly cost run-rate vs funding capture) must be frozen now. |
| CONDITIONAL_KEEP BTC4H-BANDRIDGE | **NO, if "conditional" = the three pre-fill pins** | Measured open before any fill: sizing A/B/C packet unresolved (w=1.0 structurally cannot fill under positive costs — 56 UNAVAILABLE_FAIL_CLOSED, 0 fills), fill law (H4-open doc vs first-completed-15m executor), and the NEW 6bps/side SPEC vs 5bps+tick executor cost-law discrepancy — all must be pinned forward-only before the first fill (lane_crypto §3.4, REVIEW.md O1/O2). Evidence-symmetry duty: BANDRIDGE S0 has F3 fold share **65% > 50%** and a GATE_SHUFFLE control of +137,080 — it would FAIL the same concentration gate that killed both of its composite ancestors (PSV1 Donchian G6-killed; ES1-BAND-TREND G5-killed 0.7294); its lawful status is exactly POSTHOC_DISCOVERY_CANDIDATE / prospective observation only, never OOS evidence (lane_crypto §2, §4.4, Ý 7). |
| DIAGNOSTIC_ONLY ILLIQ | **NO** | Repo evidence goes further than the direction: V11 reject 0.7055 concentration; STOCKS-AMIHUD-RETEST-V1 measured NO premium (2021-22 PF 0.646; matched-characteristic book out-earns the anchor); ILLIQ-REG-V1 gate `FALSIFIED` with INV-gated +0.3297 coherent sign flip ("the gate is regime-selective, not loss-selective", registry row 124); standing OUTCOME_EXPOSED_ANCESTRY with zero confirmation weight on all history (MAP ILLIQ-REG bullet; `plans/PLAN_illiq_reg_gate_v1.md` §2). DIAGNOSTIC_ONLY is consistent — arguably generous. |
| RETIRE_CURRENT_IDENTITY XSECT | **NO (strongly supported)** | Booked NEGATIVE under frozen costs (−298.22; fee 246.43 + slip 56.40 vs funding +4.60 — cost-dominated, REVIEW.md §1); V6 `CANDIDATE_FAIL` top-fold 51.66% (row 1); funding-LEVEL is an active dead shadow (V17 rho 0.2439); forex carry front door closed rho 0.997–1.000. Retiring the identity (not the premium question) is the one direction with a live, measured, negative booking behind it. |

**One cross-direction inconsistency to flag:** retiring XSECT as
"cost-dominated carry" while keeping BASISLV requires the turnover/cost
argument to be made explicitly and preregistered — as written, the two
directions point at the same premium (lane_crypto §4.3; PSV1 plan §5
already warns the two books "must never appear diversified merely because
they have different family names"). Similarly, KEEP_PROSPECTIVE FX is
conditional on a control that is not yet mounted; the direction is right
but the artifact does not yet satisfy its own condition.

---

## Summary verdicts

| Track | Verdict | Single strongest reason |
|---|---|---|
| A — FX RANGEFADE | **SURVIVES_AS_HYPOTHESIS** | Only track whose ancestor survived a fresh one-look holdout at 2.0x cost stress and replicated cross-pair in a directionless window (GBPUSD 6/6 folds, all baselines negative) — but its EURUSD net is not yet separable from short-beta (SHORT_ALWAYS +314 > C3 +274) and the mandated control arm is not mounted in the running shadow. |
| B — delta-neutral crypto basis/carry | **VETO_RISK_HIGH** | The only live measurement of the mechanism (the running XSECT shadow under frozen costs) books it cost-dominated ~6x (funding +4.60 vs fee+slip 302.83 per 10 days), and the repo's own identity manifest records "basis fade" as carry harvest — the same premium already rejected at 51.66% / 0.5110 fold concentration with DSR 0.00224 and ancestry rho up to 1.000. |
| C — forced-flow/event premiums | **VETO (as strategy track; lawful child = data-authority cycle)** | The required PIT observable is measured absent (liquidationSnapshot ZERO coverage; 404 UNAVAILABLE_FAIL_CLOSED; multi-year OI none; cross-venue 34min << 14-day floors) and every proxy class standing in for it is measured-dead (OICASCADE sham out-earns; LIQEPIS negative; rho 0.369–0.542 vs dead basis-fade; bear-recon double veto). |

## Honest limitations of this report

- No scored computation, no rho measurement, no network was performed here;
  every number is quoted from committed artifacts and the failure registry.
- The owner adjudication direction was taken as given from the dispatch
  packet; no document in the repo states the five verdicts verbatim, so the
  conflict check is against the directions as stated in the packet.
- Shadow ledger statistics are quoted from the 2026-09-24 review artifacts
  (REVIEW.md + lane reports); sleeves are running, so numbers are a
  snapshot, not a verdict.
- HANDOFF/handoff-schema compliance: see
  `HANDOFF_skeptic_track_falsification.json` in this directory.
