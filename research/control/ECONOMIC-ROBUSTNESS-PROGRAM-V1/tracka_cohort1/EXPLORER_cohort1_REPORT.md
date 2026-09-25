# EXPLORER_cohort1_REPORT — ERP1-TRACKA-COHORT-1 (outcome-blind council, explorer lane)

- Lane: `tracka-cohort1-explorer` (role `quant-explorer`)
- Cycle: `ECONOMIC-ROBUSTNESS-PROGRAM-V1` → proposed child `ERP1-TRACKA-COHORT-1` (DRAFT_FOR_OWNER_GO — not registered; registry grep for `TRACKA-COHORT` = 0 hits, measured)
- Measured `actual_start_sha` = `dispatch_sha` = `69ddc60447d223249319f82b71b21e26ab941203` (git rev-parse HEAD on root main, measured 2026-09-25). The dispatch packet's prose carried `…f826…` — a typo; the packet's own JSON template and the measured HEAD agree on `…f82b…`, which is used here per the verify instruction.
- Binding contract: `plans/DRAFT_ERP1_TRACKA_COHORT_1.md` (§3 disclosure, §4 frozen law, §5.2 slate criteria, §7.2 cohort law, §7.3 proposal format + six economic questions, §7.4 novelty law). Nothing in this report was measured by any PnL/backtest; every count below is clock/session arithmetic or an explicitly labelled expectation.

**Outcome-blindness certification: honored.** No scored outcome, winner information, PnL/PF/win-rate/trade-count result, shadow journal/state/dashboard, or adjudication number was read or requested. Forbidden surfaces untouched (signed block at §5). This report carries the binding ancestry disclosure of draft §3 in full (§5 below).

---

## 1. Pair slate (Task-1 replication surfaces; exactly two ordered + one spare)

Slate criteria applied (draft §5.2): top liquidity; expected full Dukascopy M1 bid/ask coverage 2021-01..2026-06; economic bloc distinct from the consumed EUR (EURUSD) and GBP (GBPUSD) surfaces; pip-scale probed per pair, never assumed; outcome-free surface (never searched in any program cycle — verified against the 12-family census exposure statement, which covers EURUSD/GBPUSD/USDJPY only).

### 1.1 Ordered slate

**Pair 1 — AUDUSD** (Australian dollar / US dollar)

- **Economic-bloc rationale:** Pacific commodity bloc (Australia: bulk-commodity terms-of-trade and China-demand beta) — a factor orthogonal to both consumed European bases (EUR, GBP) and to the consumed JPY leg. USD stays the **quote** currency, so the always-on beta arm keeps the same base/quote semantics as the consumed EURUSD/GBPUSD surfaces and the `anchor_minus_beta_control` comparison transfers without reinterpretation. Diversification of the short-USD-beta confound: the pair carries the shared USD factor plus one genuinely new bloc factor (commodities/China), so a law that survives here is not merely re-echoing European-bloc microstructure.
- **Liquidity/coverage expectation (to be probed in-cycle):** among the most-traded pairs globally (top-6 class); expectation is full Dukascopy bi5 M1 bid/ask coverage 2021-01..2026-06 at the ancestry standard (tradable-minute share > 0.90; non-positive-spread minutes ≈ 0; gap census clean), with spread p50 ≈ 0.3–0.6 pips class (between EURUSD and GBPUSD classes). **Expectation only — the data gate (bi5-vs-tick probe, census, spread curve, gap census, DST/rollover fixtures) adjudicates before any outcome.**
- **Pip-scale convention (probe required, never assumed):** raw bi5 decode scale expected 1e-5 (5-decimal quoting), conventional pip 0.0001 — **expectation only**. Precedent: USDJPY was probe-proven at 1e-3 in the ancestry census (draft §5.1); EDQ1's probe established the 1e-5 raw scaling for 5-decimal EURUSD. Per-pair point-value probe against tick ground truth is a mandatory pre-outcome gate for every slate entry.
- **Beta-control direction (always-on side replicating the dominant USD/bloc beta):** **SHORT_ALWAYS** — always short AUDUSD = always long USD vs AUD — replicating the window's dominant funding-differential/USD-strength drift (Fed above RBA through the 2022–24 hiking cycle) plus the AUD's structural risk-off sensitivity. Council-named expectation, frozen at GO-1 pre-outcome; F-4 reports `anchor_minus_SHORT_ALWAYS` for this pair.

**Pair 2 — USDCAD** (US dollar / Canadian dollar)

- **Economic-bloc rationale:** North American oil bloc (CAD as petrocurrency; WTI/energy terms-of-trade beta) — independent of the European and Pacific factors, and independent of the JPY safe-haven factor. USD is the **base** currency: the slate deliberately includes one mirrored-convention pair so that replication tests the law under inverted base/quote geometry (spread asymmetry, rollover side, pip geometry all flip). This is a structural generalization, not a cosmetic swap.
- **Liquidity/coverage expectation (to be probed in-cycle):** top-6-class liquidity; expectation full bi5 M1 bid/ask coverage 2021-01..2026-06 at the same ancestry standard; spread p50 expectation ≈ 0.6–1.0 pips (wider than the EUR class — expectation, measured by the per-session spread curve before any scoring). Wider base cost is accepted **knowingly**: it raises the F-5 cost-survivability bar for this pair (see §3.4 kill-first note).
- **Pip-scale convention (probe required, never assumed):** expected 1e-5 raw / 0.0001 conventional pip — **probe mandatory**, same discipline as AUDUSD.
- **Beta-control direction:** **LONG_ALWAYS** — always long USDCAD = always long USD vs CAD. Because USD is the base, the always-on arm that replicates the dominant USD-strength beta **flips sign** relative to AUDUSD. F-4 reports `anchor_minus_LONG_ALWAYS` for this pair. This per-pair direction naming is exactly the draft §7.2 requirement for pairs whose quote convention differs.

**Spare 3 — USDCHF** (US dollar / Swiss franc) — spare, promoted only by owner amendment at GO-1

- **Rationale and why it is spare, not core:** distinct sovereign/monetary bloc (CH), but its risk-off leg correlates with the consumed JPY safe-haven factor, weakening the "new bloc" claim; more decisively, its **dominant beta direction is window-dependent** (2022 USD spike vs 2024–25 CHF strength): the always-on control's sign is not stable across folds, which degrades F-4's interpretability. If promoted, the beta direction must be frozen pre-outcome by an explicit rule (council recommendation: full-window drift sign = SHORT_ALWAYS, i.e., long CHF vs USD, with the mid-window sign inversion disclosed in every F-4 artifact).
- Liquidity/coverage expectation: top-7-class liquidity, full bi5 coverage expected at the same standard; spread p50 expectation ≈ 0.6–1.0 pips; pip scale expected 1e-5/0.0001 — probe mandatory.

**Excluded from the slate (reasons on record):** NZDUSD (bloc redundant with AUDUSD — fails the diversification criterion); EURJPY / GBPJPY / EURGBP (both legs' blocs already consumed; no USD leg so the beta-control framework loses its named anchor; structurally wider spreads); AUD-crosses and Scandies (liquidity and coverage depth materially below the top-6 class).

---

## 2. Task-2 mechanism proposals (at most two; both offered are NEW under the §7.4 novelty law)

### 2.0 Ancestry-veto pass first (required; failure memory = `research/wayfinder/FAMILY_FAILURES.jsonl`, read in full, 127 entries)

**Candidate considered and VETOED by this lane before proposal: "second-probe / failed-break retest absorption"** (fade the retest of prev-day high/low after a first break has failed). Veto reasoning:

- `FXFV2-A4-P2` (FOREX-FREE-V2, "London-AM range break + retest-hold") — closed SCIENTIFIC_REJECTION, primary failure `CONTROL_REPRODUCED_MECHANISM`: a placebo control reproduced the behaviour "without the mechanism". The break→fail→retest **sequence shape** in FX was already measured to carry no incremental content beyond its exposure form. My candidate's identifying content is the same sequence class.
- `CRYPTO-V16 A6-V16-F1` CLOSE-DISPLACE-FADE (dead, multi-gate) and `CNG1-A4-P2` (rho 0.3988 vs the displaced-fade shadow) — establish the **displaced-fade class veto** the draft names (§3.4); a second-probe trigger is sequence-displacement-flavored.
- Census adjacency: trigger level = prev-day H/L (shared with census `PDHLOC` and the ancestor `RANGEEXP`'s edge source), trigger = intraday reversion (shared with census `HOURREV`).

Conclusion: high probability of failing the F-1 pooled |rho| ≤ 0.20 gate and/or the class veto; the cohort's ≤2 Task-2 slots are not spent on it. The two mechanisms below are what remains after this self-veto.

**Standing veto-relevant map for the two proposals below** (dead FX families that bound the design space):

- Re-clock / calendar geometry class: `FXFV1-A3-P1` (London-open continuation), `FXFV1-A3-P2` (late-NY fade), `FXFV2-A4-P1` (Tokyo compression → London expansion), `FXNG4-A4-P1/P2` and `FXNG4-A5-P1/P2` (day-of-week geometry collapses), `FXNG3-A5-P2` (calendar-day collapse). **Consequence:** both proposals inherit the ancestor's clock verbatim (07:00–18:00 UTC window, closed-H1 decisions, next-open opposite-quote fills, force-flat 20:00) and add **no** calendar/release conditioning. Sham/shuffle controls are included anyway per the house standard established by `FXFV5-A6-P1` ("sham-calendar control now MANDATORY for calendar mechanisms") and re-confirmed by `FXFV7-A4-P1` (sham ≈ anchor).
- Nominal-level class: `FXFV8-A5-P1` and `FXNG1-A4-P2` (the DGS10 nominal-yield-level shadow — "the most lethal control in the forex program"). **Consequence:** neither proposal touches any macro/nominal series; the information sources are intra-corpus only.
- Premium-fade ancestry: `FXFV3-A6-P1-family2` (realized-vol regime-gated carry, invalidated), `FXFV4-A6-P1` (carry front door closed at rho 0.997–1.000 vs invalidated ancestor). **Consequence:** no carry/funding content anywhere in either proposal (also structurally excluded by the no-overnight, no-swap law).
- Cross-pair information: `FXFV7-A6-P2` (EURUSD lead-lag diffusion) is the only FX dead family using cross-pair information — it died with the own-lag control OUT-earning the lead-lag anchor. **This is proposal M2's pre-declared kill candidate** (see below): M2 uses cross-pair information, so the F-1 rho measurement against that family's shadow is declared in advance as the likely firing site; if it fires, M2 dies pre-PnL honestly (`NOT_SCORED_FALSIFIED`), and no re-parameterization loop opens.
- Liquidity-state class awareness: `CRYPTO-V13 LIQEPIS` (liquidity-episode conditioning, crypto, plain-negative price-only) and `CRYPTO-NG1/V17` rho blocks on liquidity-proxy exposures. **This is proposal M3's class-warning:** a liquidity-state gate can collapse into a plain session/liquidity exposure; M3's F-3 clock-only control is the named executioner.

Census-family relationship disclosure (mandatory, draft §3.5): both proposals' **trigger level source is the previous day's high/low band** — the same level source as census family `PDHLOC` (and the edge source of `RANGEEXP`). Neither proposal reuses any census-family function or signal (the 12 census functions are visible in the code-authority file `v2_lib.py`: `f_gap`, `f_pdhloc`, `f_dow_simple`, `f_asiafade`, `f_sessma`, `f_h1tsmom`, `f_h1donch`, `f_daymom`, `f_rangeexp`, `f_stoch`, `f_roundnum`, `f_hourrev` — none is imported, re-tuned, re-clocked, re-sessioned, blended, or sign-flipped). The NEW content of each proposal is its **gate**, and each gate's information source is unused by the ancestor and by all 12 census families. The in-cycle rho measurement (F-1) adjudicates; this lane's reasoning does not substitute for it.

---

### 2.1 Proposal M2 — **XCONF-ABSORB: cross-leg attribution–gated edge absorption**

One-sentence mechanism: when the home pair closes an H1 bar beyond its previous-day band, absorb the break **only if the shared-USD reference pair's same-clock closed bar does not confirm it** — a non-confirmed break is idiosyncratic to the bloc leg (one-pair stop-cascade / forced flow), hence transient; a common-factor-confirmed break is potentially informed, hence stood down.

- Home pair: **AUDUSD**; reference leg: **USDCAD** (both in the Task-1 corpora — no new downloads).
- Novelty audit (§7.4): new mechanism (attribution-gated conditional absorption vs the ancestor's unconditional regime-gated fade) + new information source (cross-pair common-vs-idiosyncratic decomposition; unused by ancestor and all 12 census families) + new causal control (the confirmed-subset book). Not a lo_q/hi_q re-tune, not a re-session/re-clock, not an indicator blend on one series, not a sign-flip.

**Ten mandatory fields**

1. **Payer:** leveraged stop-cascade and breakout-chasing flow concentrated on one bloc leg whose forced prints beyond the prev-day edge are not justified by the shared USD factor. Non-arbitrage reason: the flow is mandatory (risk stops, margin mechanics), behavioral (breakout chasing), dispersed and anonymous — no single payer can internalize it, and makers quote rather than initiate.
2. **Premium (expected bps/decision):** hypothesis 0.5–1.5 pips gross per decision on AUDUSD session hours ≈ **0.8–2.3 bps/decision** (1 pip ≈ 1.5 bps at AUDUSD ~0.65). **Stated plainly:** the stress round-trip ceiling for this pair is ≈ 1.2 pips (§2.1 field 7), so the hypothesis must sit at the TOP of its band for the book to survive F-5; F-5 is expected to be the binding gate, and a negative ceiling kills M2 pre-PnL.
3. **Risk transferred incl. tail:** the book is short *break-continuation risk*: it loses when an "idiosyncratic-looking" break is actually early informed flow. Named tail: a one-sided runway day on the bloc leg (e.g., a central-bank surprise on AUD while CAD/USD are quiet) where the absorption position rides the dislocation with no stop — bounded only by the middle-quarter exit and the 20:00 UTC force-flat; the loss distribution is negatively skewed by construction.
4. **PIT observable (event/effective/available separated):** event = H1 close of AUDUSD beyond its previous-day high/low (event time = bar close); effective = the same instant; available = fill at the NEXT H1 open at the opposite quote (buy@ask / sell@bid). Gate = USDCAD's **same-clock already-closed** H1 bar evaluated against its own previous-day band; the PIT audit must prove reference-bar close timestamp ≤ home decision instant on every decision (explicit alignment fixture; DST offset differences between the two blocs are absorbed by the common UTC clock). Data authority: both pairs' Dukascopy M1 bid/ask corpora downloaded in this cycle under the §5.1 posture (license posture inherited; EDQ1 facts in §4).
5. **Holding horizon + decision clock:** intraday, minutes-to-hours (enter next H1 open; exit on return into the middle quarter of the prev-day range; no fills on/after the 19:00 bar; force-flat before 20:00 UTC; weekend flat; no overnight, no swap — executor fixtures). Clock inherited verbatim from the family execution law; the novelty claim does not rest on the clock.
6. **Capacity (order of magnitude):** single-pair, session-hours retail-liquid FX; realistic clip size ~$1M notional (order $1–10M before impact competes with a sub-2-pip premium). This is a premium-harvest book, not a scale strategy.
7. **Costs (base + stress):** base = measured per-session spread curve charged at event time (entry+exit at opposite quotes ⇒ ≈ 2× session median) + the declared venue-free fee buffer component; stress = ×2.0 on per-regime medians (×1.5 and ×2.0 both reported). AUDUSD expectation: base round trip ≈ 0.6 pips; **stress ceiling ≈ 1.2 pips**. Adverse selection/fill quality declared unmeasurable and stress-covered (draft §6.4); taker fills pay the spread — no maker-capture claims anywhere.
8. **Falsifier (with the control that must NOT reproduce it):** (a) F-1 ancestry — pooled |rho| ≤ 0.20 vs the dead-family shadows; **pre-declared kill candidate: the `FXFV7-A6-P2` cross-pair lead-lag shadow** (M2 uses cross-pair information; if the rho fires, M2 is `NOT_SCORED_FALSIFIED` and dead on this identity). (b) Causal control = the **confirmed-subset book** (same trigger, fade only USD-confirmed breaks): its net must NOT reach ≥ 0.5× anchor net @ ×1.0, else `KILL_CONTROL_REPRODUCED` (§9.4 band) — the edge would be generic break-fading, not attribution. (c) Sham = **within-day alignment-shuffled reference leg** (house sham standard): must NOT reproduce. (d) `anchor_minus_SHORT_ALWAYS` ≤ 0 ⇒ `KILL_BETA_EXPLAINED`. (e) F-3 clock-only shadow must not reproduce the conditional exposure. (f) F-5 negative ceiling ⇒ veto pre-PnL.
9. **Controls/baseline:** baseline set = FLAT + day-session SHORT_ALWAYS + day-session LONG_ALWAYS (SHORT_ALWAYS is the named AUDUSD beta control); causal control = confirmed-subset book; inverted control = same trigger+gate, opposite sign; neighbours (≤2, support-checks, never selectable, no grid): N1 = confirmation tested against the reference pair's own session midpoint (tighter attribution test); N2 = non-confirmation required on the break bar AND the immediately prior bar (persistence-of-idiosyncrasy).
10. **Feasibility anchors:** see §3.2.

**Six economic questions (§7.3), explicit**

1. *Payer + non-arbitrage:* answered in field 1 — mandatory stop/margin flow and behavioral breakout chasing on one bloc leg; cannot be arbitraged away because it is dispersed, anonymous and non-volitional.
2. *Premium + risk + tail:* 0.5–1.5 pips/decision gross hypothesis (≈0.8–2.3 bps); the risk is short break-continuation; the tail is the one-leg runway day against the position until force-flat (field 3).
3. *Persistence + erosion:* persistence is structural — stop-cluster geometry at prev-day extremes and breakout-chasing behavior regenerate as long as leveraged flow concentrates at visible levels. Erosion vectors: (i) bloc correlation rising toward 1 makes the gate rarely fire (book empties — no harm, no premium); (ii) bloc decoupling makes the common-factor attribution noisy; (iii) if stop cascades thin out as flow algorithmizes, the payer pool shrinks.
4. *Observable + data authority:* home/reference closed-H1 bars and prev-day bands from the two authorized Dukascopy M1 bid/ask corpora, with the alignment fixture proving reference availability at decision time (field 4).
5. *Falsifier + control prediction:* confirmed-subset and shuffled-reference books must NOT reproduce (prediction: both ≤ 0.5× anchor, ideally ≤ 0); if either reproduces, the attribution content is dead and M2 is killed regardless of the anchor's absolute performance.
6. *Cost-survivability ceiling:* stress round trip ≈ 1.2 pips on AUDUSD; expected gross premium must exceed it per decision after the F-5 arithmetic — the honest ceiling statement is that M2's hypothesis band only clears the stress ceiling at its top; F-5 adjudicates before any scored cell.

---

### 2.2 Proposal M3 — **QSTATE-ABSORB: provider-quote-state–gated edge absorption**

One-sentence mechanism: absorb the previous-day-band break **only when the maker community's quotes stayed calm through the break hour** — the just-closed break hour's median bid/ask spread at or below its trailing same-hour p60 — because a break that prints against stable quotes is a non-informed cascade (absorbable), while a break accompanied by quote-widening is informed/rollover/news flow (stand down).

- Home pair: **USDCAD** (the pair with the richer, wider spread dynamics gives the gate the most information to read; it also makes the cost fragility explicit rather than hidden — see field 7 and the kill-first note).
- Novelty audit (§7.4): new mechanism (liquidity-provider-state conditional provision vs unconditional absorption) + new information source (**the bid/ask spread path** — a direct component of the authorized corpus that the ancestor and all 12 census families leave unused; all of them are mid-price constructions — verified against the function inventory in `v2_lib.py`) + new causal control (the spread-wide complement book). Not a re-tune, not a clock/session move, not an indicator blend, not a sign-flip.

**Ten mandatory fields**

1. **Payer:** forced stop/liquidation flow crossing the book at edges during quote-stable hours. They pay via price dislocation, not via the spread (which never widened). Non-arbitrage: the flow is mandatory and anonymous; makers' inventory/latency constraints leave them quoting, not initiating, so the post-cascade recovery is left to liquidity-takers like this book.
2. **Premium (expected bps/decision):** hypothesis 0.5–1.5 pips gross per decision on USDCAD ≈ **0.5–1.5 bps/decision** (USDCAD pip ≈ 1.0 bp at ~1.00–1.40). The stress cost ceiling on this pair is the cohort's highest (field 7), so the same plain statement as M2 applies with more force: **F-5 is the expected binding gate and M3 is the cohort's most cost-fragile cell.**
3. **Risk transferred incl. tail:** short *informed-break* risk. The gate excludes fast information (quote-widening) but **cannot see slow informed accumulation that deliberately executes in calm hours** — that is the named tail: repeated calm-looking runway days against the position until force-flat. Secondary tail: rollover-adjacent spread misclassification (mitigated structurally: the 07:00–18:00 UTC window excludes the 21:00–22:00 UTC NY rollover band; the 15:00–16:00 London-fix hour remains inside and is handled by the per-session spread curve, not by an assumption).
4. **PIT observable (event/effective/available separated):** decision state = median bid/ask spread over the **just-closed** H1 bar vs the trailing 20-trading-day same-hour distribution, threshold p60 frozen pre-outcome; event = H1 close beyond the prev-day band (event time = bar close); effective = same instant (the state is computed exclusively from the closed bar — PIT-clean by construction); available = fill at next H1 open at the opposite quote. Data authority: Dukascopy M1 bid/ask — the spread series is a direct component (`duka_lib.py` stores per-day per-side BID and ASK M1 candle files); the session/rollover spread-curve infrastructure already exists from the ancestry cost book.
5. **Holding horizon + decision clock:** identical family execution law to M2 and to the ancestor (next-open opposite-quote fill, middle-quarter exit, no fills on/after the 19:00 bar, force-flat 20:00 UTC, weekend flat, structural-zero financing enforced by fixtures).
6. **Capacity:** as M2 — order $1M notional/pair; premium-harvest scale.
7. **Costs (base + stress):** base = USDCAD session spread curve (entry+exit ≈ 2× session median) + declared fee buffer; expectation base round trip ≈ 1.2–2.0 pips, **stress ×2.0 ≈ 2.4–4.0 pips — the cohort's widest ceiling**. Declared consequence: if the calm-hour per-decision recovery hypothesis is sub-2-pip (likely a priori), F-5 kills M3 pre-PnL; this is disclosed as the design, not hidden.
8. **Falsifier (with the control that must NOT reproduce it):** (a) causal control = the **spread-WIDE complement book** (same trigger, fade only where the break hour's median spread exceeded p60): must NOT reach ≥ 0.5× anchor net, else the quote-state carries nothing (`KILL_CONTROL_REPRODUCED` band). (b) Mutation/vacuity: shifting the spread state by one day (same hour) MUST move the book, else the gate is vacuous and the arm set is re-derived before scoring. (c) F-3 clock-only shadow must NOT reproduce — the named executioner for the "gate collapses into session geometry" failure mode warned by the liquidity-state class (`CRYPTO-V13 LIQEPIS`; `CRYPTO-NG1/V17` liquidity-proxy rho blocks). (d) `anchor_minus_LONG_ALWAYS` ≤ 0 ⇒ `KILL_BETA_EXPLAINED`. (e) F-1 rho vs dead-family shadows — expectation near-orthogonal (dead FX families are mid-price constructions; the LIQEPIS shadow is a different asset and information source) — measured, not assumed. (f) F-5 ceiling first of all.
9. **Controls/baseline:** baseline set = FLAT + day-session LONG_ALWAYS + day-session SHORT_ALWAYS (**LONG_ALWAYS is the named USDCAD beta control** — USD-base pair); causal control = spread-wide complement; inverted control = same trigger+gate, opposite sign; neighbours (≤2, support-checks, never selectable, no grid): N1 = trailing state window 60 trading days (state-robustness); N2 = 3-bar median spread state (smoothing robustness).
10. **Feasibility anchors:** see §3.3.

**Six economic questions (§7.3), explicit**

1. *Payer + non-arbitrage:* forced, anonymous, dispersed stop/liquidation flow during quote-calm hours (field 1); no arb because the flow cannot time itself and makers do not initiate.
2. *Premium + risk + tail:* 0.5–1.5 pips/decision hypothesis (≈0.5–1.5 bps); risk = short informed-break; tail = slow, calm-hour informed accumulation invisible to the gate (field 3).
3. *Persistence + erosion:* persistence = market-makers' structural quote-stability at non-informed hours (inventory management normality); erosion = (i) internalization/technology compressing spread dynamics until the state series loses contrast; (ii) informed flow migrating deliberately into calm hours, inverting the gate into a trap; (iii) fee/commission regime shifts moving the ceiling.
4. *Observable + data authority:* same-hour spread percentile of the closed break bar, from the authorized bid/ask corpus; separation event/effective/available = bar close / same instant / next open (field 4).
5. *Falsifier + control prediction:* the spread-WIDE complement must NOT reproduce (prediction ≤ 0.5× anchor); one-day-shifted state must move the book; clock-only shadow must not reproduce. Any reproduction ⇒ dead regardless of anchor performance.
6. *Cost-survivability ceiling:* stress round trip ≈ 2.4–4.0 pips on USDCAD — the cohort's widest; the calm-hour selection is cost-favorable but the base spread is not, and the honest expectation is that F-5 is more likely to kill M3 than any other cell.

---

## 3. Structural feasibility notes (clock/session arithmetic only — no backtest, no measurement)

Common arithmetic: FX trades ≈ 250–260 weekdays/year; the 07:00–18:00 UTC window contains 12 H1 bars of which ≤ 11 are decision/fill-capable (no fills on/after the 19:00 bar; force-flat 20:00). Dev window 2021-01..2025-12 ≈ 5 years ≈ 1,280 traded days; holdout 2026-01..2026-06 ≈ 128 days. G5 adjudication floor ≥ 100 closed round trips (smoke floor 30 = eligibility only); G3 needs ≥ 4/6 folds net > 0 with ≈ 1-year folds.

### 3.1 Task-1 R-ANCHOR / R-ORIG / R-NEIGH per pair

- **Expected decision counts/year:** trigger = closed-H1 close-through of either prev-day extreme inside the window, in the not-extremely-wide mode. Structural expectation 0.5–1.2 trigger-events/day/pair (a major's intraday session routinely revisits the prior day's extremes) ⇒ ≈ **125–300 decisions/pair/year**; over the dev window ≈ 600–1,500 per pair — comfortably above the G5 floor; per-fold populations ≈ 100–300 (adequate for G3's fold arithmetic). Verified at F-6 on the **last 6 months** (not archive average), per the plan.
- **Warmup:** trailing ≤ 60-day range-percentile window + prev-day stats ⇒ ≈ 61 traded days ≈ 3 months; first decisions ≈ 2021-03 from a 2021-01 data start (fold F1 thinned at its head — disclosed, not patched).
- **Data components per pair:** M1 bid/ask bi5 day files (expectation: census of the same shape as the GBPUSD/USDJPY corpus — ≈ 4,000 files/pair, 0 missing tolerance); bi5-vs-tick ground-truth probe; pip-scale probe (per §1); gap census; tradable-minute census; per-session/rollover spread-curve build (the cost book); DST/rollover calendar fixtures. Engine: ancestry engine reused with pip-size parametrization + new pair-scale fixtures; parity self-test on consumed pairs is FIXTURE-only.
- **Structural note carried into F-PIT-1 (code-structure fact, structure-only reading):** in `f_rangeexp` (`v2_lib.py:265`) the mode percentile `pct[d]` is ranked from `ranges[d][0]` = day d's **own full-day high−low**, appended to the trailing history within the same day-loop iteration that later trades day d — i.e., the draft §4.2 PIT suspect is visible in the code structure exactly as the draft describes: the day's fade/breakout mode is not known at that day's start. This is adjudicated by F-PIT-1 before any PnL; this lane adds only that the structural read supports the draft's suspicion.

### 3.2 M2 XCONF-ABSORB (home AUDUSD, reference USDCAD)

- **Expected decision counts/year:** same trigger set as §3.1, gated by non-confirmation. Structural expectation of the non-confirmed fraction 40–70% ⇒ ≈ **100–400 decisions/year**. This straddles the G5 floor: at the low end, per-fold populations approach the smoke floor — **declared binding feasibility risk**; F-6 on the recent 6 months adjudicates before scoring.
- **Warmup:** prev-day bands on both pairs + alignment fixtures ⇒ ≈ 2 traded days of warmup after both corpora start (plus the family's fold-boundary discipline). No percentile window.
- **Data components:** both pairs' §3.1 components (already required by Task 1 — **no new downloads**) + the synchronized two-pair closed-H1 panel with an explicit alignment/availability fixture (reference close ≤ decision instant) and a parity self-test of the panel join.
- **Kill-first honesty (single biggest reason NOT to open on M2's account):** cross-pair information in FX has exactly one dead ancestor (`FXFV7-A6-P2`, killed by its own control) and M2 pre-declares that shadow as its likely F-1 firing site. The owner should expect M2 to die at F-1 or F-5 with meaningful probability; the slot is worth it only because the attribution gate is the one information source in the family that no dead or census family has ever used.

### 3.3 M3 QSTATE-ABSORB (home USDCAD)

- **Expected decision counts/year:** same trigger set, gated by quote-calm. Structural expectation of calm fraction 50–75% ⇒ ≈ **125–450 decisions/year** (adequate); the causal control's book (wide complement, 25–50%) must still clear the smoke floor (30) — if it does not, the control is vacuous and the arm set is re-derived **before any PnL**, never after.
- **Warmup:** 20-trading-day same-hour spread history + prev-day bands ⇒ ≈ 1 month.
- **Data components:** USDCAD's §3.1 components (no new downloads) + the same-hour spread-percentile state series (a deterministic transform of the spread curve already built for the cost book).
- **Kill-first honesty (single biggest reason NOT to open on M3's account):** the stress cost ceiling on USDCAD (≈ 2.4–4.0 pips round trip) is the widest in the cohort and the per-decision recovery hypothesis is a fraction of a dislocation — F-5 is more likely than not to kill M3 pre-PnL. M3 earns its slot only as the family's first genuine microstructure-dimension test (the quote path), with the honest expectation that the cost book may be the answer.

### 3.4 Cohort-level kill-first (the single biggest reason the owner should NOT open this cohort)

**The PIT seam.** The ancestor law that produced every ancestry result (R-ORIG semantics) computes its mode from the same day's own full-day range — future information at the day boundary (draft §4.2; structurally supported by the code read in §3.1). The honest replication target (R-ANCHOR, mode from `pct[d−1]`) has therefore **never been the thing that produced any prior result**. If F-PIT-1's preregistered comparison fires (|R-ORIG − R-ANCHOR| beyond the seam band), the family's economics ARE the seam on that pair and the correct outcome is falsification with zero PnL — before Task 2 spends a cell. Secondary kill-first risks, in order: (i) the family carries three dead absorption/fade cousins in FX/cross-asset failure memory (`FXFV1-A3-P2`, `FXFV2-A4-P2`, `A6-V16-F1`) — the prior that a same-family variant carries incremental content is weak; (ii) both Task-2 hypotheses only clear their stress cost ceilings at the top of their bands — F-5 is the modal killer; (iii) per §1.2/§9.3, `REJECT_ALL` and `BLOCKED_*` are expected, valid terminal verdicts and the 24-cell budget exists to spend on honest confirmation of deadness, not on finding a winner.

---

## 4. What this lane did NOT do (bounds of the work)

Read-only session except this report and its handoff JSON. No commits, no registry writes, no downloads, no backtests, no PnL computation of any kind, no shadow/worker/journal access, no S1, no sibling-lane handoff reads (council independence). Files read: the draft plan (binding contract); `research/wayfinder/FAMILY_FAILURES.jsonl` (full, 127 entries — failure memory only); `plans/CYCLE_REGISTRY.json` lifecycle fields only (child cycle absent: grep 0); EDQ1 `CYCLE_VERDICT.md` + `owner_packet_source_survey_2026-09-22.md` (**license facts only**: verdict `BLOCKED_SOURCE_LICENSE`, Dukascopy TCU posture — personal non-commercial use, no automated acquisition without prior express written consent, no-database clause, applicability to the datafeed host unstated; Twelve Data internal-research-clear but no bid/ask (reconciliation-only); three owner unblock paths — TrueFX registration / Dukascopy written consent / OANDA v20 practice; no storage terms accepted by anyone); code structure of `v2_lib.py` (function inventory incl. `f_rangeexp:265` and the 12 census-family functions) and `duka_lib.py` (per-day per-side BID/ASK M1 candle corpus, fetch/decode paths) in the named scripts directory. The EDQ1 verdict's own boundary statement confirms it contains no profitability or edge statement.

## 5. Signed disclosure block (binding, draft §3 — carried verbatim in substance)

> **ANCESTRY DISCLOSURE — OUTCOME-EXPOSED.** The RANGEFADE ancestry
> `EURUSD-OPEN-SEARCH-V1 → EURUSD-OPEN-SEARCH-V2 → EURUSD-RANGEEXP-SCORED-V1
> → FX-MAJORS-SEARCH-V1 → FX-RANGEFADE-2M-SHADOW-V1` is OUTCOME-EXPOSED:
> its dev campaigns, holdout results and the running shadow journal have been
> seen by humans and agents. **EURUSD, GBPUSD and USDJPY full scored windows
> (2021-01 .. 2026-06 holdout inclusive) are consumed surfaces** — no cell of
> this cycle scores them as evidence. A **12-family census (GAP, PDHLOC, DOW,
> ASIAFADE, SESSMA, H1TSMOM, H1DONCH, DAYMOM, RANGEEXP, STOCH, ROUNDNUM,
> HOURREV) has dev-window outcome exposure on those pairs** — this lane does
> not know, and must not seek, which families looked good. This explorer
> packet contains **no** PnL, PF, win-rate, trade-count outcome, shadow
> journal content, or any ranked/selected/winner information from any scored
> or shadow surface. All pair surfaces proposed in §1 are outside the exposed
> set; the EURUSD/GBPUSD/USDJPY surfaces appear here only as (a) disclosed
> ancestry and (b) the excluded-from-slate list. Outcome-blindness was
> respected in every step of this lane; forbidden files and directories were
> not read or requested (list in §4).

*Signed: EXPLORER lane (`tracka-cohort1-explorer`), 2026-09-25, at root main `69ddc60447d223249319f82b71b21e26ab941203`.*
