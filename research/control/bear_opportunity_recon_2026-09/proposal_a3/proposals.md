# PROPOSAL_A3 — outcome-blind mechanism proposals

cycle: BTC-BEAR-OPPORTUNITY-RECON · lane A3 · 2026-09-23 · HEAD 66d58e2a7292418ba09cec997d3df3ecc04cec5c

Outcome-blindness: no forbidden artifact opened (full path audit in
`../handoffs/handoff_proposal_a3.json`). Inputs used: the four A2 data
authority files only, plus the sanitized ancestry class list and house-law
excerpts supplied in the dispatch. No backtests, no parameter sweeps, no PnL
anywhere in this lane; every number below is either an A2 published aggregate
or closed-form arithmetic on such aggregates.

---

## 0. Shared arithmetic groundwork (identities on A2 aggregates, no PnL)

1. **Lens containment identity.** From three published aggregates
   (P(SMA-down)=0.4642, P(DOWNTREND)=0.2010, agreement=0.736), the joint
   P(SMA-down ∧ DOWNTREND) solves x + (1−0.4642−0.2010+x) = 0.736, giving
   x = 0.2006 ≈ P(DOWNTREND). Therefore:
   - P(DOWNTREND ∧ ¬SMA-down) ≈ 0.0004 — the frozen label is, to within
     ~6 bars of 14,589, a **subset** of the SMA200-down state.
   - P(SMA-down ∧ ¬DOWNTREND) = 0.2636 — a **pre-confirmation region**
     covering ~26.4% of the window where the fast lens has turned but the
     label has not yet confirmed. The label is the stricter and later state
     variable. (TRANSITION_UNKNOWN alone is 6506 bars ≈ 44.6% of window.)
   No return magnitude is used anywhere in this derivation.

2. **Carry cannot pay for churn.** In-DT mean funding +3.709e-5/8h = 0.371 bps
   of notional per settlement = +4.06%/yr annualized to a short; × DT
   occupancy 0.2010 × ~6.56y ⇒ implied cumulative ≈ +5.36%, reconciling with
   A2's measured +5.46% (difference = exact settlement counts). One round
   trip costs 12 bps. Carry alone is 32× below the fee per settlement, so any
   proposal whose edge is funding carry is dead on arithmetic before PnL —
   consistent with ancestry class 8 being dead. The only funding-scale event
   that matters at hours-scale holds is the cap-binding settlement
   (−0.30% = 30 bps ≈ 2.5 round trips).

3. **Margin reality (A2 short_feasibility §3) is inherited by both proposals**
   as mandatory accounting addenda: 1x notional leverage declared; bar-open
   gap liquidation check (conservative: bar-high touch bound for a short);
   funding cashflows at 00/08/16 UTC on mark notional; ADL/partial-liquidation
   and collateral-yield remain disclosed placeholders.

4. **Funding accounting number declared before scoring (feasibility §2
   requirement):** both proposals account funding with **per-settlement
   measured archive rates** (in-DT expectation +3.709e-5/8h, actuals per
   settlement), NOT the frozen PSV1 constant 1.377e-5.

---

## PROPOSAL A — "Confirmation-Lag Front-Run" (PRIMARY)

**Mechanism class:** harvest of rule-compelled, structurally late systematic
flow (state-variable timing), not price prediction.

**One-line forced-counterparty story.** WHO: label-following systematic short
capital — any book whose state variable IS the frozen PSV1 DOWNTREND label
(and its SMA-lens siblings). WHY late/forced: house law compels bar-close
decisions and next-open fills, and the containment identity shows their label
confirms strictly later than the SMA lens (label ⊂ SMA-down; the pre-state
region is 26.4% of all bars) — they are not slow-witted, they are
**rule-structurally late by construction**: until their state flips they may
not act, and when it flips they MUST sell at the next open. I position inside
their pre-confirmation window and harvest the flow their own mandate creates
at confirmation.

**PIT observable (all PIT_USABLE, already sha-pinned by A2/PSV1):**
- SMA200 lens state and DOWNTREND label state on the H4 grid, each computed
  at H4 bar close under the frozen preregistered census rules
  (`downtrend_census_rules_preregistered.json`, sha 62e4df5c…, counted one-shot).
- Decision grid: H4 close; fills next H4 open (frozen convention).
- No new data staging required.

**Downtrend gate.** Entry state = SMA200-lens-down ∧ label-not-DOWN
(edge-triggered on the first bar the conjunction becomes true). This state
necessarily includes label-TRANSITION_UNKNOWN bars — a **conscious, flagged
deviation** from the default "TRANSITION_UNKNOWN → FLAT" law: the uncertainty
is not noise here, it is the countdown of a rule-compelled counterparty, and
exposure to it is bounded by the abandonment constant below. Everywhere else
the flat law is obeyed (see exits). Owner sign-off on this deviation is
required; without it, Proposal A does not exist in the form specified.

**Direction.** Short BTCUSDT um perp only. Market-neutral is NOT constructible
from the PIT_USABLE set as staged (indexPriceKlines is synthetic and
untradeable; no spot kline panel is staged) — **data-gate flagged**: staging
spot klines would enable spot-perp neutral legs and must be an explicit owner
decision, not an assumption.

**Entry/exit sketch with round constants and non-PnL rationale.**
- **Enter short** at the open following the first H4 close where
  SMA-down ∧ ¬label-DOWN becomes true (edge-triggered; one entry per episode).
- **K_ABANDON = 12 H4 bars (2 calendar days).** If the label has not confirmed
  DOWN after 12 bars in the pre-state, the forced flow never arrives —
  mechanism declared absent, exit next open, episode closed as fake-out.
  Rationale: 2 days is a round calendar convention, fixed pre-data; not tuned.
- **On label confirmation to DOWN:** hold **H_HOLD = 6 H4 bars (1 calendar
  day)** through the confirmation flow, then exit at that bar's close (fill
  next open). Rationale: 1 day, round calendar constant. Deliberately exits
  long before the label ends — the trade harvests the *entry* flow of the
  late cohort, not the downtrend itself (this is also what keeps rho vs class
  1 structurally low).
- **Invalidation exits (flat-law compliance):** SMA lens flips UP before
  confirmation → exit next open; label re-enters TRANSITION_UNKNOWN after
  confirmation → exit next open (uncertain → FLAT); hard cap = K_ABANDON +
  H_HOLD = 18 H4 bars (3 days); fold-end force-flat.
- **Churn/no-op law:** max 1 concurrent position, no pyramiding; re-arm
  requires the conjunction to be false for ≥ 1 H4 bar and true again;
  flat-to-flat transitions generate no orders; no re-entry inside the same
  episode after any exit.
- **Holding bounds:** 1 to 18 H4 bars.
- **Cost survival story:** ~≤59 events per 6.5y (bounded by the 59 merged
  independent DOWNTREND episodes — every label onset passes through the
  pre-state by the containment identity), so churn ≈ 12 bps/event; the flow
  harvested is an entire cohort's compelled market entry spread over the
  confirmation window, the only flow in this data regime that is both large
  and timestamped. Funding while holding: ≤ 9 in-DT settlements in the max
  hold at +0.37 bps mean received; worst measured squeeze settlement −30 bps
  possible within any hold — disclosed, bounded, accounted per settlement.

**Preregistered falsification control (ONE): NEIGHBOUR — the fake-out arm.**
Episodes with the identical visible state (SMA-down ∧ ¬label-DOWN) whose label
NEVER confirms within K_ABANDON are the natural anti-signal: same regime, same
lens state, but the compelled cohort never arrives. Preregistered prediction:
traded (confirming) episodes must outperform fake-out episodes net of fees at
the episode level; if the two arms are indistinguishable, the convenient
explanation ("it's just downtrend drift") kills the mechanism. This control
moves the signal by construction (it is the partition of the same state), per
Q-11. Phase-shuffle was rejected: it can only test "any drift", not the
forced-flow claim.

**Expected failure mode (mechanism absent).** The world where the label cohort
is too small to move price, or already positioned via other signals:
confirming and fake-out episodes show the same forward return; confirmation
lags are sub-bar (no exploitable window); or the pre-state is dominated by
1-bar wobble (few clean episodes). All three are detectable before any PnL.

**Rho-exposure self-declaration (|rho| ≤ 0.20 claim, same H4 binary entry
representation).**
- Class 1 (SHORT-in-DOWNTREND label, DEAD): entry region is **disjoint from
  label-DOWN bars** by construction; overlap limited to the 1-day
  post-confirmation coda → expected |rho| far below 0.20.
- Class 2 (breakdown-continuation short, DEAD): **largest residual risk** —
  both are shorts in a falling tape. Mitigation: breakdown triggers are local
  displacement events (frequent, price-threshold); A's entries are a slow
  state conjunction, edge-triggered ≤ ~59 times in 6.5y; the abandonment and
  lens-flip exits make the entry series time-structured, not
  displacement-triggered. A4 must measure rho vs a breakdown-trigger series;
  I claim ≤ 0.20 on sparsity and edge-triggering grounds, and accept the veto.
- Class 12: not a sign flip of Donchian-long — the state variables are A2's
  frozen lenses, not Donchian channels.
- Class 13: no run-imbalance / flow-persistence features anywhere in the
  signal. Classes 3/4/5/6/7/8/9/10/11/14: no OI, no reversal-fade, no vol, no
  premium/basis level, no funding feature, no price-defined liquidation
  episode, no order-flow, no pairs, no calendar/attention conditioning.

**Statistical-power honesty.** Event supply is bounded by ~59 merged
episodes; realistically 40–59 entries (unknown until A4 counts). At σ ≈ 2%
per 1-day-hold event, 80% power (two-sided 5%) detects only ≥ ~1.0%/event net
edges (N=31) — a 50 bps/event edge needs N≈125 and is **undetectable** here.
Consequences preregistered: (i) the primary inference is an EPISODE-LEVEL
paired comparison vs the fake-out arm (shared regime component removed), not
a bar-level mean; (ii) independence unit = episode (no bar pooling);
(iii) if N < 30 confirming episodes, the mechanism is declared
NOT_TESTABLE_AT_POWER (NOT_RUN), never "failed".

---

## PROPOSAL B — "Mark-Trigger Catch-Down" (SECONDARY)

**Mechanism class:** margin-engine flow clock (contractual forced-flow
timing), not price prediction and not a level fade.

**One-line forced-counterparty story.** WHO: leveraged perp longs facing
Binance's risk engine. WHY maximally forced: liquidation is contractual — the
engine closes them **at market, on MARK price**, whatever their will. WHY
late: mark = index + smoothed premium lags a fast crash (index itself is a
multi-venue spot composite that lags the leading venue), so the forced
market-sell flow is **timestamped by the mark's convergence toward last**: a
fast down-move that leaves last far below mark has liquidations *pending, not
spent*. I short at the wide spread, ahead of the contractual flow, and exit
when the spread closes (flow spent).

**PIT observable (all PIT_USABLE per A2, all 12 intervals measured):**
- um klines (last) 5m, markPriceKlines 5m, indexPriceKlines 5m,
  2020-01 → 2026-09 daily tail; frozen convention adapted: a 5m bar is
  knowable at its close, first fill at next 5m open.
- Signal S_t = (mark_close_t − last_close_t) / index_close_t.
- H4 DOWNTREND label from the frozen census rules as the gate.
- Liquidation prints are NOT used and NOT needed (um tape absent — A2
  decisive finding); the mechanism consumes the exchange's own trigger
  surface, which is exactly the part that is PIT.

**Downtrend gate.** DOWNTREND label = DOWN at the last closed H4 (evaluated
PIT inside each 5m decision). Label ∈ {TRANSITION_UNKNOWN or any non-DOWN
state} → no new entries; if holding, exit next 5m open (uncertain → FLAT law,
no deviation needed for B). Onset-crash events outside labeled downtrends are
out of scope by design (conservative).

**Direction.** Short BTCUSDT um perp only; same market-neutral data-gate flag
as Proposal A.

**Entry/exit sketch with round constants and non-PnL rationale.**
- **Enter short** at the next 5m open after S_t ≥ θ = **0.12%** for
  **2 consecutive 5m closes**. Rationale: θ = exactly one round trip of fees —
  a cost-floor constant (a dislocation smaller than the fee cannot pay for
  itself by construction), rounded to a clean decimal; persistence = 2 is the
  minimal double-close confirmation convention; the 5m grid is Binance's
  native event-export interval. None of these is tuned to returns.
- **Exit** at the next 5m open after the first close with S_t ≤ 0 (mark has
  caught down; the pending forced flow is spent), or at the hard time stop.
- **T_MAX = 144 bars = 12h** (half a settlement day; bounds exposure to ≤ 2
  funding settlements per trade).
- **Margin addenda (feasibility §3):** 1x notional; bar-open gap liquidation
  check for the short (conservative bar-high bound); funding cashflows at
  00/08/16 UTC; ADL placeholder disclosed.
- **Churn/no-op law:** one position at a time; no re-entry within the same H4
  window after an exit; flat-to-flat no-ops; fold-end force-flat.
- **Holding bounds:** 1 to 144 5m bars.
- **Cost survival story:** the harvested flow is a liquidation cascade leg —
  the one recurring flow in this market that is price-insensitive market
  orders by definition and multi-percent in aggregate during cascades; 12 bps
  is small relative to that flow IF entry timing works. Funding while
  holding: mean in-DT +0.37 bps/8h received, but 24.7% of in-DT settlements
  are negative and the tail is −30 bps (2.5 round trips) — bounded to ≤ 2
  settlements by T_MAX and accounted per settlement, not by any frozen mean.

**Preregistered falsification control (ONE): NEIGHBOUR — narrow-spread matched
crashes.** Events with a similar 5m down-move but S_t < θ at decision time
(mark already converged; liquidation clock already spent) are the control:
same crash, same downtrend regime, no pending forced flow. Preregistered
prediction: wide-spread (traded) events drift further down post-entry than
matched narrow-spread events; if both behave identically, the convenient
explanation ("crashes continue regardless of the mark clock") kills the
mechanism. Events are paired within ±7 days and similar move magnitude so the
regime component cancels.

**Expected failure mode (mechanism absent).** Mark converges within a single
5m bar (the lag is sub-grid; nothing left after the next-open fill) —
mechanism untradable at bar-close law; or wide-spread events are squeeze
ignitions that resolve UP, flipping conditional sign; or narrow- and
wide-spread crashes are statistically identical.

**Rho-exposure self-declaration (|rho| ≤ 0.20 claim).**
- Class 9 (price-defined liquidation-episode books, DEAD): **main declared
  risk** — both fire in crash contexts. Mitigation by construction: the entry
  requires the contractual spread S_t (mark−last), which conditional on a
  crash is governed by index staleness + premium smoothing, near-orthogonal
  to price-path shape; A4 must measure rho of the entry series vs a
  price-threshold crash series, and I accept the veto.
- Class 5 (displacement fade, DEAD): opposite sign — B shorts INTO
  displacement, class 5 faded it; expected rho ≈ 0 or negative.
- Class 7 (premium-LEVEL fade, DEAD-ADJACENT): S_t is the premium's fast
  component (deviation of last-vs-mark from its own smoothed state), not a
  level; entries occur on large NEGATIVE fast-premium where level-fade logic
  is silent or opposite; expected |rho| low, A4 to verify.
- Class 8: no funding feature in the signal (funding only in accounting).
  Classes 1/2/3/4/6/10/11/12/13/14: no overlap of signal construction; class 2
  shares crash environments — same declared residual as in A, smaller because
  B's events are an order of magnitude sparser.

**Statistical-power honesty.** Event count is unknown until measured; wide
spread events are plausibly dozens to low hundreds across ~1.3 in-gate years
(20.1% × 6.5y). Preregistered: N < 40 events ⇒ NOT_TESTABLE_AT_POWER
(NOT_RUN), never "failed". The neighbour pairing roughly halves the required
sample by differencing out the common crash drift; detecting ≥ ~1%/event
conditional edges still needs the upper end of the plausible range —
underpower is the expected state, and is reported as such.

---

## Ordering and kill-evidence

**PRIMARY = Proposal A** (cleanest structural rho control — disjoint from the
dead label region by the containment identity; bounded, known-scale event
supply ≤ ~59; zero new data staging). **SECONDARY = Proposal B** (strongest
forced-counterparty story in the set — a contractual, price-insensitive
flow — but it carries two live NOT_RUN risks: spread half-life at 5m
resolution and event scarcity, plus the class-9 rho veto).

**What kills A before any PnL exists:** (i) pre-confirmation episodes number
< 30 (underpowered → NOT_RUN); (ii) median SMA-down-to-label-confirmation lag
is < 1 H4 bar (no exploitable window — checkable from the census rules
alone); (iii) the fake-out neighbour arm shows the same forward drift as the
confirming arm (mechanism = drift, killed by the control without scoring the
strategy); (iv) A4 measures entry-series rho vs breakdown-continuation
(class 2) > 0.20; (v) owner rejects the TRANSITION_UNKNOWN deviation and no
fallback exists.

**What kills B before any PnL exists:** (i) empirical (mark−last) half-life
after a θ-crossing is < 2 5m bars (untradable at bar-close law — a
mechanism-level measurement A4 makes from PIT series, not a backtest);
(ii) fewer than 40 θ-events inside DOWNTREND windows over the frozen window;
(iii) narrow-spread matched crashes behave identically to wide-spread ones;
(iv) A4 measures entry-series rho vs class 9 shadows > 0.20.
