# PROPOSER4 — Blind Open-Call Proposals — ERP1-TRACKA-COHORT-2

- Lane: `proposer4-open-call` · Role: `blind-proposer` · Date: 2026-09-26 (UTC)
- Measured HEAD at proposal time: `3de439ab988d82cd246731ae6c277a688f6e2c31` (branch `main`)
- Outcome-blind lane. Independent of lane P3. No lane-P3 artifact was sought, read, or inferred from.

## 0. Blindness statement

**Taint: NONE.** The complete information diet consumed for this proposal is:

1. `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort2/PACKET_dead_family_labels.json`
   (schema `erp1_tracka_cohort2_blind_packet_deadfamilies_labels@1`, 129 families, labels only) — read in full.
2. The dispatch context inlined in the task (binding execution frame + dead-family description).
3. Git HEAD measurement (sha only).

Not opened, not grepped for content, not inferred from: cohort plans, shadow journals, series
files, trial ledgers, MAP outcome bullets, scored reports, plan ancestry-number sections, lane P3
outputs, or any file whose content contains PnL / PF / win-rate / margin numbers. No outcome
number entered this lane's context. No accidental exposure occurred; therefore no
TAINTED marking is required.

## 1. Family selection rationale

Per dispatch, fertile ground = mechanisms whose **payer is identifiable** and is **not
stop-flow-at-range-edges**. Two families are proposed:

- **P4-A `FIXCERT-01`** — benchmark-fixing certainty premium (payer: WM/Reuters-fix-bound
  participants paying for deadline execution certainty).
- **P4-B `QSKEW-01`** — dealer quote-skew inventory migration in the bid/ask data layer
  (payer: urgency-paying liquidity takers whose flow forces sector-wide quote shading).

Both live entirely inside the authorized substrate (Dukascopy M1 BID/ASK, AUDUSD + USDCAD,
2021-01..2026-06; 15m/H1 derivable), use strictly closed bars, and require no external file,
calendar of releases, or cross-pair input.

Binding execution frame assumed for both (from dispatch): H1/traded-day clock; closed-bar
signals; taker fills at the opposite quote of the fill bar's open (PAYS spread); flat 20:00 UTC
+ weekends; cost = fill bar's measured spread × k, k ∈ {1.0, 1.5, 2.0}.

## 2. Dead-family clearance (labels checked against the 129-family packet)

Nearest labels, with the one-line distinction recorded for the skeptic lane:

| Nearest packet label | Why the proposal is NOT that family |
|---|---|
| `FXFV1-A3-P1` "London-open session continuation" | FIXCERT-01's window is the London **close/fix** (16:00 Europe/London), not the open; the law is deadline-flow pressure gated by a PIT observable, not session continuation. |
| `FXFV1-A3-P2` "Late-NY fade" | Different window (fix at 15:00–16:00 UTC vs late NY) and a continuation (ride) law, not a fade. |
| `FXNG1-A5-P1` "Opening-follower print drift (16:00-NY grid)" | That family is keyed to economy **release order** on a 16:00-**NY** grid; FIXCERT-01 uses no release calendar at all and is keyed to 16:00 **London local**. |
| `FXFV5-A6-P1` "pre-release avoidance (counter-trend spanning CPI instant)" | No release calendar anywhere in either proposal; gates are pressure/quote-state observables only. |
| `CNG1-A4-P2`, `CNG1-A5-P1`, `CNG2-A5-P1/P2` (crypto pre-expiry / settlement drift) | Nearest conceptual neighbors to "pre-event drift": different asset class (crypto), different event (futures/options settlement vs a daily FX benchmark fix). Flagged for skeptic adjudication. |
| `TRACKA1-M3-QSTATE` "Quote-state-gated edge absorption" | Nearest label to QSKEW-01 because both touch the bid/ask layer. QSTATE's law is **prev-day-band-break fading with spread as a gate**. QSKEW-01 contains no band, no break, no edge, no prev-day geometry: the signal is within-bar asymmetric bid/ask migration and the primary sign is RIDE, not fade. Stripping the QSKEW observable leaves no range law at all (self-check (a) passes trivially). |
| `TRACKA1-M2-XCONF` cross-leg attribution gate | QSKEW-01 is deliberately single-pair: no cross-pair input of any kind (also avoids `FXFV7-A6-P2` lead-lag diffusion and `FXFV6-A6-P2` PC1 cross-pair reversal). |
| `M01-AGGRESSOR-ABSORPTION-PANEL` (crypto aggressor flow) | Different asset class and different data layer: Dukascopy M1 has no aggressor/trade-direction field; QSKEW uses only bid/ask OHLC quote migration. Flagged as conceptual neighbor. |
| `FXOS-04` Bollinger MR fade (15m) | Oscillator-of-price fade; QSKEW is not an oscillator of price; FIXCERT is not a fade. |
| `FXFV2-A4-P2` "London-AM range break + retest-hold" (range-edge family, incl. provenance/reclaim/probe-count gates per dispatch) | Neither proposal references prior-day bands, band extremes, breaks, reclaims, or probe counts anywhere. |
| Dispatch dead classes: day-of-week geometry, hour-reversal | Both proposals carry an explicit clock-only shadow control that must NOT reproduce (fields 9 below). |

No proposal relabels, re-tunes, or re-clocks any of the 129 listed families.

---

## 3. PROPOSAL P4-A — `FIXCERT-01` · London fixing-window certainty premium

**Family:** benchmark-fixing flow pressure (pre-fix continuation into the WM/Reuters 16:00
London fix). Mechanism: participants whose mandates are benchmarked to the 16:00 London fix
submit large, one-sided, deadline-bound orders; because certainty dominates price at a deadline,
they cross the spread and tolerate pre-fix adverse drift. Dealers pre-position ahead of the
predictable deadline flow, which is visible as drift in the final pre-fix hour in the direction
of the net fix flow. We ride that pressure into the fix.

### 3.1 The ten fields

1. **Payer.** Benchmark-referencing institutional participants — passive index/bond funds
   rebalancing at the fix, NAV-marked hedgers, corporates converting at the benchmark — who pay
   (spread + pre-fix adverse drift) for execution certainty at a deadline. Secondarily, dealers
   who pre-positioned into the fix and must unwind into thinner post-fix liquidity.
2. **Premium (declared band, bps).** Gross per-event drift capture on gated events
   (|z| ≥ 1.0): **1.0–3.0 bps (AUDUSD), 0.8–2.5 bps (USDCAD)**. Ungated fix days declared
   ≤ 0.5 bps (this floor is what makes the gate meaningful). Reference cost band to be measured
   from the censused data (declared hypothesis): fill-bar measured spread 0.3–0.9 bps AUDUSD /
   0.5–1.2 bps USDCAD per taker crossing. If the measured median gross lands below the k=1.0
   round-trip cost, the premium claim fails its own declared band → reject.
3. **Persistence.** Motive is structural, not informational: mandates benchmarked to the WM/R
   4pm London fix (passive tracking, NAV marking, hedged index portfolios) renew on institutional
   timescales (years). Erosion vectors: benchmark-execution algos slicing fix orders; FX Global
   Code conduct norms on pre-hedging; dealer competition. Sample 2021-01..2026-06 is
   post-Code era, so any residual is already the survived premium. Persistence test:
   two disjoint calendar halves must both show same-sign net expectancy at k=1.0; monthly-block
   bootstrap 95% CI excludes zero on the pooled window.
4. **Risk transferred.** (i) Deadline/timing risk: the fix participant pays to transact at a
   known instant rather than an unknown price; we carry the directional exposure across the fix
   instant. (ii) Dealer pre-position inventory risk into the fix. Not an arbitrage: on
   news-dominated fix days the pressure sign flips (declared tail: worst-decile gated events to
   −8 bps), bounded by a pre-registered per-event stop at 2 × ATR(1h, trailing 20 fix days) and
   the 1-bar horizon.
5. **Observable (exact PIT computation from closed bars).**
   - Data: Dukascopy M1 BID/ASK for pair p. Per closed M1 minute bar i covering
     [t_i, t_i+1min) UTC: `mid_i = (bidClose_i + askClose_i)/2`.
   - Fix instant F(d) for traded day d: the minute whose **Europe/London local time is 16:00**
     on d (deterministic tz arithmetic from UTC timestamps; F = 15:00 UTC in BST, 16:00 UTC in
     GMT). No external calendar needed.
   - Pressure `P(d) = (mid[F−60min] − mid[F−120min]) / mid[F−120min]` — both endpoints are
     closes of strictly completed H1 bars at decision time t = F−60min.
   - Gate: `z(d) = (P(d) − μ) / σ` over the trailing 60 fix days (strictly earlier; expanding
     from the first 60). Trade only if `|z(d)| ≥ 1.0`.
   - Entry: fill at the **open of the H1 bar [F−1h, F)** at the opposite quote (buy at ask if
     long). Exit: deterministic time-based exit decided at entry — fill at the **open of the H1
     bar [F, F+1h)** at the opposite quote. Exposure = exactly the final pre-fix hour including
     the fix instant; exit open ≤ 16:00/17:00 UTC, trivially inside the 20:00-UTC flat.
   - Both DST conventions run as **separate sub-books (BST days, GMT days); each must
     independently pass** (kills a DST-misalignment artifact).
6. **Horizon + clock.** H1 clock; one pre-fix H1 bar of exposure per event; traded-day clock
   only; no weekend exposure; never interacts with the 20:00 UTC flat.
7. **Capacity.** The London fix is among the deepest minutes of the FX day (documented
   multi-billion fixing turnover). Declared institutional capacity ≥ USD 25m per event per pair
   before impact exceeds the measured-spread assumption; non-binding at research scale.
8. **Costs base + stress.** 2 taker crossings/event (entry at F−1h bar open, exit at F bar
   open), each = fill bar's measured spread × k, k ∈ {1.0, 1.5, 2.0}. Kill rule: at k=2.0, if
   the bootstrap-95% upper bound of mean net per-event return ≤ 0 → family dead.
9. **Falsifier + controls that must NOT reproduce.**
   - **Sign-flip control:** fade the same gated pressure at identical gates/times must NOT show
     ≥ 0 net expectancy at k=1.0. If both signs survive → execution artifact → discard.
   - **Clock-only shadow:** the same window traded every fix day **without** the pressure gate
     must NOT reproduce the gated book's net expectancy (match within noise ⇒ the law is
     calendar geometry ⇒ dead clock family).
   - **Placebo window:** identical z-gate applied to a pre-registered 60-min window anchored at
     05:00 UTC on the same days must NOT reproduce.
   - **Dose-response:** net expectancy monotone in |z| quintiles.
10. **Controls & beta-matched baseline.** All results reported as excess over the standing
    beta-matched baselines **SHORT_ALWAYS(AUDUSD)** and **LONG_ALWAYS(USDCAD)** under the
    identical cost model; event-day beta contribution of those baselines subtracted from the
    gated events before any expectancy claim.

### 3.2 Six economic questions

- **Q1 Payer / non-arbitrage.** Fix-bound participants paying a certainty premium for deadline
  execution; dealers earn it only by carrying inventory + pre-hedge capacity. Genuine risk
  transfer (timing/inventory risk), not a free lunch.
- **Q2 Premium + tail.** Declared band 1.0–3.0 bps gross per gated event (AUDUSD) / 0.8–2.5
  (USDCAD); tail: news-dominated fix windows flip sign, worst decile ≈ −8 bps, bounded by the
  ATR stop + 1-bar horizon.
- **Q3 Persistence / erosion.** Structural mandate motive (years-scale); erosion via fix algos
  and conduct norms; halves + monthly-block bootstrap required both-positive.
- **Q4 PIT observable + source.** `P(d)` from Dukascopy M1 bid/ask midpoint closes at
  F−60/F−120 min, Europe/London deterministic tz conversion; z from trailing 60 fix days only;
  no external calendar, no contemporaneous-bar inputs.
- **Q5 Falsifier + control prediction.** Sign-flip must lose at k=1.0; clock-only shadow and
  05:00-UTC placebo window must NOT reproduce; monotone dose-response in |z|; BST/GMT sub-books
  must each pass. Predicted control outcomes: fade book ≤ 0 net; clock-only ≪ gated book.
- **Q6 Cost-survivability ceiling at ×2.0.** Ceiling ≈ 2 × 2.0 × E[fill-bar measured spread]
  ≈ 1.2–3.6 bps (AUDUSD band). The declared premium band straddles this ceiling: only its upper
  part survives ×2.0 by construction. Honest expectation: ×2.0 survivability is the primary
  screening question; kill rule in field 8 applies mechanically.

### 3.3 Self-check

- **(a) Strip the new observable → dead-family law?** Stripping `P(d)`/z leaves "trade every
  fix window 1h-into-fix" = a pure clock law, which the clock-only control must show does NOT
  reproduce. The family is defined by the gate, not the clock. Not a relabel of London-open
  continuation, late-NY fade, or any release family.
- **(b) Clock-only shadow reproducible?** Addressed head-on: dedicated shadow control + 05:00
  UTC placebo + BST/GMT sub-book split (§3.1 field 9).
- **(c) Strictly-closed bars?** Decision at t = F−60min uses closes at F−60 and F−120 min
  (both strictly past); z-window strictly trailing; all fills at bar **opens** at opposite
  quotes. Pass.

---

## 4. PROPOSAL P4-B — `QSKEW-01` · Dealer quote-skew inventory migration (bid/ask layer)

**Family:** dealer inventory management visible in the quote layer. Mechanism: one-sided
urgent flow leaves sector-wide inventory imbalance; market makers shade both quotes toward the
inventory-correcting side (raising the bid faster than the ask when correcting short inventory,
dragging the ask down faster when correcting long inventory). Because inventory is
sector-wide, the correction persists: the mid migrates over the following hours as slower
dealers and late takers reprice. The within-bar **asymmetric bid/ask migration** — computable
from Dukascopy M1 bid/ask OHLC, which contains no trade direction — is the observable; we RIDE
the dominant migration for two bars. Payer: liquidity takers whose urgency forces the shading,
and subsequent takers who transact while the imbalance persists.

### 4.1 The ten fields

1. **Payer.** Urgency-paying liquidity takers whose one-sided flow forces sector-wide quote
   shading, plus slower participants who transact during the multi-hour mid-price adjustment;
   they pay the migration we ride.
2. **Premium (declared band, bps).** Gross per gated event (|Z| ≥ 1.5): **0.6–2.0 bps
   (AUDUSD), 0.5–1.6 bps (USDCAD)** over the 2-bar hold. Reference fill-bar spread band
   (hypothesis to be measured): 0.3–0.9 bps AUDUSD / 0.5–1.2 bps USDCAD. Declared honestly: the
   band's lower half is non-survivable at ×2.0 by construction; survival requires the upper band.
3. **Persistence.** Dealer inventory management is structural to market-making (capital, VaR
   limits) — the constraint does not disappear with electronification; erosion vector is faster
   dealer re-hedging shrinking drift per unit of skew (slow decay). Persistence test: two
   disjoint calendar halves same-sign at k=1.0; monthly-block bootstrap 95% CI excludes zero.
4. **Risk transferred.** Short-horizon adverse-selection risk: some skew events are informed
   (building news) and extend into a liquidity spiral that snaps back after our 2-bar horizon
   (declared tail: worst decile −6 to −10 bps), bounded by 2-bar horizon + pre-registered stop
   at 2 × ATR(1h, trailing 250 H1 bars). We effectively provide inventory services as takers —
   genuine risk transfer, not arbitrage.
5. **Observable (exact PIT computation from closed bars).**
   - Per closed M1 bar i: `q_i = [(askClose_i − askOpen_i) − (bidClose_i − bidOpen_i)] /
     (askClose_{i−1} − bidClose_{i−1})` — normalized by the **previous closed bar's** closing
     spread (strictly past). Units: fraction of one spread. q_i > 0 ⇒ ask side migrated up
     faster (upward quote pressure).
   - H1 aggregation: `Q_t = Σ_{i ∈ H1 bar t} q_i` (12 minutes), known at the H1 close t.
   - Standardize: `Z_t = (Q_t − μ)/σ` over the trailing 250 H1 bars of the **same pair only**
     (no cross-pair input — deliberately outside lead-lag/diffusion and PC1 reversal dead
     classes).
   - Gate `|Z_t| ≥ 1.5` → enter **sign(Z_t)** (RIDE the dominant migration — pre-registered
     primary sign) at the open of bar [t, t+1h) at the opposite quote; deterministic exit
     decided at entry: fill at the open of bar [t+2h, t+3h). Pre-registered calendar guard: no
     entry whose deterministic exit open is at/after 20:00 UTC (those events are skipped) —
     this is an execution-frame constraint, not a signal.
6. **Horizon + clock.** H1 clock; 2-bar exposure; intraday only; flat by 20:00 UTC by rule;
   no weekend exposure.
7. **Capacity.** Intraday majors liquidity; declared ≥ USD 10m per event per pair at research
   fidelity; non-binding at research scale.
8. **Costs base + stress.** 2 taker crossings/event; fill-bar measured spread × k,
   k ∈ {1.0, 1.5, 2.0}. Kill rule: at k=2.0, bootstrap-95% upper bound of mean net per-event
   return ≤ 0 → family dead. Declared ceiling: mean gross gated-event must exceed
   4.0 × E[fill-bar measured spread] ≈ 1.2–3.6 bps (AUDUSD) vs declared band 0.6–2.0 bps —
   marginal by construction; ×2.0 verdict is the primary screening question.
9. **Falsifier + controls that must NOT reproduce.**
   - **Sign-flip control:** the FADE sign at identical gates/times must NOT survive at k=1.0.
     If both signs survive → execution artifact → discard. If only the fade side survives, the
     mechanism interpretation is invalid and the family is rejected as specified (no silent
     sign flip).
   - **Clock-only shadow:** trade the same H1 hours as the gated book every day without the
     Z-gate must NOT reproduce the gated expectancy.
   - **Placebo (shuffle):** recompute Z after shuffling within-day M1 bar order (pre-registered
     seed family); the dose-response monotonicity of Z-quintiles → next-2-bar return must hold
     in real data and vanish under shuffling.
   - **Cross-pair placebo:** Z computed from the OTHER pair must not predict this pair's gated
     returns (guards a global-market confound and the lead-lag dead family).
10. **Controls & beta-matched baseline.** All results as excess over
    **SHORT_ALWAYS(AUDUSD)** / **LONG_ALWAYS(USDCAD)** with identical cost model; event-day
    beta contribution subtracted; dose-response monotonicity in Z-quintiles required.

### 4.2 Six economic questions

- **Q1 Payer / non-arbitrage.** Urgency-paying takers and late repricers pay the migration;
  we absorb short-horizon inventory-adjustment and adverse-selection risk. No riskless profit
  claimed; the premium compensates holding risk across the adjustment.
- **Q2 Premium + tail.** Band 0.6–2.0 bps gross (AUDUSD) / 0.5–1.6 (USDCAD) per gated 2-bar
  event; tail: stop-cascade over-extension, worst decile −6 to −10 bps, bounded by ATR stop +
  2-bar horizon.
- **Q3 Persistence / erosion.** Structural market-making constraint; erosion via faster
  re-hedging; halves + monthly-block bootstrap both required positive at k=1.0.
- **Q4 PIT observable + source.** `q_i` from Dukascopy M1 bid/ask OHLC (no aggressor field
  used or needed), normalized by the previous closed bar's spread; H1 sum; Z from trailing 250
  same-pair H1 bars; fills at subsequent bar opens only.
- **Q5 Falsifier + control prediction.** Fade sign must lose at k=1.0; clock-only shadow must
  not reproduce; shuffled-bar placebo must destroy the Z→return monotonicity; other-pair Z must
  not predict. Predicted control outcomes: fade ≤ 0 net; shadow ≪ gated; shuffle destroys
  dose-response.
- **Q6 Cost-survivability ceiling at ×2.0.** Ceiling = 4.0 × E[fill-bar measured spread]
  ≈ 1.2–3.6 bps (AUDUSD). Declared band's lower half fails by construction; family survives
  only if gated events realize the upper band. Kill rule in field 8 applies mechanically; no
  re-tuning after the ×2.0 verdict.

### 4.3 Self-check

- **(a) Strip the new observable → dead-family law?** Stripping `q_i`/`Z_t` leaves nothing:
  no calendar, no band, no break, no session geometry, no oscillator of price. The nearest
  label (`TRACKA1-M3-QSTATE`) is a range-fade family whose spread term was a *gate*; here the
  quote layer *is the signal*, and the primary sign is RIDE. Pass.
- **(b) Clock-only shadow?** Dedicated shadow control + shuffle placebo + cross-pair placebo
  (§4.1 field 9). The law's content is the gated quote-state, not the clock. Pass.
- **(c) Strictly-closed bars?** `q_i` uses bar i and bar i−1 (both closed before H1 close t);
  Z-window strictly trailing; fills at bar opens after the decision close. The spread
  normalizer is the previous closed bar — never the contemporaneous one. Pass.

---

## 5. Joint limitations (declared for the skeptic/validation lanes)

1. All bps bands are **declared hypotheses**; the validation lane must measure actual
   fill-bar spreads from the censused Dukascopy data before adjudicating the cost ceilings.
2. Europe/London DST conversion must be implemented via a tz database in validation; the
   BST/GMT sub-book requirement (P4-A) is the designed guard against misalignment artifacts.
3. Dukascopy M1 BID/ASK layout (per-minute bid OHLC + ask OHLC) is assumed from the factory's
   censused substrate; validation must confirm field availability before implementation.
4. Both proposals are event-gated and thin-premium by construction; the ×2.0 cost stress is
   expected to be the binding gate. No band may be widened after the cost verdict (no
   re-tune).
5. No code was executed in this lane (proposal-only). All falsification tests are specified,
   not run.

## 6. Closing statement

Proposals P4-A (`FIXCERT-01`) and P4-B (`QSKEW-01`) are submitted blind, outcome-blind, and
independently of lane P3. **Taint: NONE.** Handoff artifact:
`HANDOFF_proposer4_cohort2.json` (schema `zcode_orch_v3_handoff@1`), same directory.
