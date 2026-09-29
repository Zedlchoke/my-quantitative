# CLASS_SPEC — VOLPROF-M1 (preregistered class spec, Pool B / P_B_VOLUME_PROFILE)

- Program: PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (pre-GO, unregistered; LANE_CHARTER
  session 2, 2026-09-29). Lane M (mechanism/corpus), read-only session; no git, no
  backtest, no PnL, no scoring, no network.
- Author / measured-at: Lane M, 2026-09-29T08:51Z (root checkout, owner dirty tree
  preserved).
- Status: **DRAFT_PREREGISTERED — CONDITIONAL_RESOLVED_AUDIT_CLEAN** (Lane D
  physical audit landed 2026-09-29: 12,552 files, 0 missing / 0 undecodable /
  0 anomalies, coverage 2021-01-01..2026-09-23 — see section 10).
  **Revision r1 (2026-09-29, same day)**: section 3 rewritten on Lane D's
  MATERIAL finding — the M1 volume column is a **size-weighted per-tick
  volume sum (Dukascopy unit, unit-basis unverifiable), NOT a tick count**;
  all arm constructions verified unit-invariant (new section 3.3); observable
  renamed accordingly throughout.
  **Revision r2 (2026-09-29, remediation of skeptic finding F-9 MEDIUM)**:
  CTRL-B redefined as a TWO-ARM placebo family — day-blocked B1 (retained as
  decomposition diagnostic; preserves the cross-day volume↔price-range
  association, stated exactly) + full-window B2 (governs the kill; provably
  breaks the volume↔price-level assignment at every granularity) — see 7b.
  Every idea in this spec is
  **HYPOTHESIS / NOT_RUN**. No backtest has been run on
  this class or on any corpus row cited here; nothing below implies otherwise.
- Amendment in force (owner directive 2026-09-29, relayed by A1 mid-session):
  **novelty/ancestry is no longer an admission gate.** Previously-rejected ideas and
  old families are diagnostic candidates carrying their failure history as an
  outcome-exposed label; admission is by **implementability only** (mechanical rule,
  data, PIT, costs, decision count). Consequences applied throughout this spec:
  - Section 8 (ancestry) is **INFORMATIVE, NOT GATING** — it is a
    measured-and-disclosed representation-rho protocol feeding redundancy,
    diversification and the multiple-testing narrative.
  - Section 9's former "rho>0.20 ⇒ ancestry kill" is demoted to a disclosed
    redundancy label (the causal controls and cost/floor kills in section 9 remain
    gating — they are falsification, not ancestry).
  - The closing self-assessment (section 12) addresses **implementability and
    diagnostic value**, not ancestry escape.
  - Historical fence texts are quoted verbatim below as recorded law of their time;
  they are context and labels, not current gates.

---

## 1. CLASS_ID + scope

**CLASS_ID: `VOLPROF-M1`** — the volume-profile strategy class on the three
FX M1 Dukascopy panels: **{EURUSD, GBPUSD, USDJPY}** (bid+ask `.bi5`, volume
column present; the only pairs with a declared M1 execution clock and a
volume column — F0 court data-ceiling note, SLEEVE-FX5-100K-V1/f0/F0_VERDICTS.md
§authorities item 6). The class's observable is a **size-weighted volume**
column (declared and corrected in section 3); the campaign's historical
shorthand "tick-volume" is **retired** after the Lane D audit refuted the
tick-count premise.

### 1.1 Preregistered candidate arms (frozen set, no grids)

3 arm shapes x 3 pairs = **9 class candidates** — exactly the campaign cap
("≤9 fresh class candidates (class spec cap)", BACKTEST_CAMPAIGN_DESIGN §6 / plan
draft §4). The plan's 54 TRAIN-only class-parameter grid-node budget is **not
invoked** by this spec: every parameter below is a single frozen value, named, not
tuned. Any grid use would require its own preregistration; there is none.

| CLASS_CANDIDATE id | shape | pair | one-line identity | own falsifier (primary) |
|---|---|---|---|---|
| `VC1-VAEDGE-EURUSD` | VA-edge rejection fade | EURUSD | fade a fresh excursion one bin beyond the Value Area edge into a frozen-profile low-acceptance region, target POC | two-arm volume-placebo (7b): edge must vanish under the B2 full-window permutation (the arm that governs the kill) |
| `VC1-VAEDGE-GBPUSD` | same | GBPUSD | | |
| `VC1-VAEDGE-USDJPY` | same | USDJPY | | |
| `VC2-LVNFAIL-EURUSD` | LVN traverse-failure fade | EURUSD | fade a failed traverse of a low-volume node (price broke through, failed to hold, returned), target POC | two-arm volume-placebo (7b): the node must vanish under the B2 full-window permutation |
| `VC2-LVNFAIL-GBPUSD` | same | GBPUSD | | |
| `VC2-LVNFAIL-USDJPY` | same | USDJPY | | |
| `VC3-POCMAG-EURUSD` | POC-magnet reversion | EURUSD | from inside the Value Area, deviated ≥3 ATR60 from POC while parked in a high-acceptance (≥P80) bin, revert to POC | two-arm volume-placebo (B2 governs) + uniform-weight control: if the profile structure is not load-bearing, the arm is a slow band-fade re-label (disclosed, section 8) |
| `VC3-POCMAG-GBPUSD` | same | GBPUSD | | |
| `VC3-POCMAG-USDJPY` | same | USDJPY | | |

Why these three shapes (justification, frozen):

1. They are the three canonical level-acceptance decision types of the
   volume-profile method (edge rejection / node-traverse failure / anchor
   reversion) — the minimal set that exercises all three profile features
   (VA edge, LVN, POC) without overlapping each other.
2. Each shape's trigger level is **undefined without the volume-by-price
   distribution** (strip test): remove the profile and there is no VA edge, no
   LVN, no POC. VC1/VC2 pass this structurally; VC3 passes only conditionally
   (its P80 acceptance condition is profile-derived, but a price-only anchor
   could stand in — that residual risk is disclosed in section 8 and is the
   reason VC3 carries the two-arm volume-placebo (7b, B2 governs) and the
   uniform-weight control as its
   designated primary falsifiers).
3. All three are fade-side (mean-reverting) because that is the direction the
   payer hypothesis (section 2) actually funds. The complementary join-side
   (acceptance outside the VA) is deliberately NOT preregistered: it is an
   own-price continuation shape, and its failure history
   (TRACKA2-P3B-DINV-1D standing veto; DTP playbook breakout-continuation
   11/11 dead) makes it the weakest diagnostic candidate — under the amendment
   it could in principle be added later as a labeled diagnostic, but it is not
   in this frozen set.

Position/entry/exit mechanics per shape are in section 5. **No sizing cleverness
in this spec**: every candidate trades a fixed UNIT position (1 unit = 10,000
base-currency units); sizing, vol-targeting and caps are Stage-B portfolio
policy, never per-arm.

### 1.2 Disposition of the three Pool-B corpus rows (not preregistered as-is)

Pool B = P_B_VOLUME_PROFILE contains exactly three census rows
(PORTFOLIO_ELIGIBILITY_1200.tsv): EURUSD-S010, USDJPY-S030, USDJPY-S056. Their
volume/tick-feature DATA blocker is what this class resolves via the M1
size-weighted volume column (corrected semantics, section 3);
**none of the three is preregistered as an arm as-written**,
for implementability reasons (the current admission criterion), each stated from
the census row + source text:

- **EURUSD-S010** (EURUSD.md:275-277, "Vol-expansion-confirmed trend entry"):
  D1 close beyond EMA50 with range ≥1.3x ATR20 and tick-volume ≥1.5x 20d mean;
  event-day exclusion requires a PIT release calendar the repo does not carry
  (census `required_pit_data`: "EURUSD D bars; tick-volume history; release
  calendar for exclusions"; verdict PIT_UNPROVEN). Also its trigger is a
  volume-GATED trend entry — a gate over the trend law, labeled accordingly in
  section 8. Not mechanizable as specified (calendar absent); not preregistered.
- **USDJPY-S030** (USDJPY.md:163, "Round-number barrier cascade"): H1 close
  through a round number + CME futures volume >2x 20d median. The volume input
  is CME 6J futures volume/OI — transport-blocked (census BLOCKED_DATA); the
  Dukascopy size-weighted volume column is a different observable in a
  different unit (section 3) and the
  source's own mechanism (barrier-defense option writers) needs barrier
  intelligence the sleeve does not carry. Not preregistered.
- **USDJPY-S056** (USDJPY.md:221, "Realtime intervention join"): MOF
  intervention footprint join. The mechanism is the intervention EVENT; the
  census verdict is BLOCKED_DATA ("M1/CME/news confirmation unevidenced"),
  and the source's own coupling requires same-day Mimura/Kato statements plus
  ex-post MOF disclosure to label — an unevidenced PIT event calendar. The
  volume-burst component alone is not the mechanism. Not preregistered.

The class therefore enters, per campaign design §1, as **fresh class candidates
with new CLASS_CANDIDATE ids — no anonymous arms**. The corpus rows remain
labeled candidates in the pool; if a future owner action evidences their missing
PIT inputs, they would need their own rows under this same class spec.

### 1.3 Identity tuple (campaign §1, instantiated)

Every candidate carries, frozen before any computation, the tuple
`(cycle_id=PORTFOLIO-COMPOSITE-12ASSETS-100K-V1, sleeve_id=POOL_B_VOLPROF,
CLASS_CANDIDATE_id=<table above>, family_id=VOLPROF-M1-<shape>,
mech_key=<vc1_vaedge|vc2_lvnfail|vc3_pocmag>,
mechanism_payer=<section 2 string>, clock=<section 4 string>,
entry_rule=<section 5 string>, exit_rule=<section 5 string>,
size_rule_key=UNIT_FIXED_10K, pit_join_list=<section 4 list>,
cost_tier=PANEL_VENUE_C1_MEASURED_PLUS_U2U3U4U5_DECLARED,
causal_control_id=<CTRL-A/B/C/D per section 7>,
ancestry_fence_result=<LABEL from section 8 protocol — informative>,
arm_config_digest=<sha of the frozen parameter block>)`.

---

## 2. PAYER (who pays, and why on FX spot specifically)

**Primary payer hypothesis: impatient, price-insensitive execution flow pays
resting liquidity at activity-accepted price levels.**

- The economic agents on each side:
  - **Paying side**: (i) liquidity-seeking momentum/breakout chasers who push
    price beyond the Value Area edge into regions where the frozen profile shows
    little accepted two-way business — they transact at the worst quotes of the
    move and must re-trade when price re-enters value; (ii) forced/flow-driven
    execution (corporate hedgers, FX-overlay rebalancing, fixing-related flows
    such as the London 16:00 WMR fixing and month-end rolls) that must complete
    near reference levels and pays the spread wherever price stands when the
    obligation fires.
  - **Receiving side**: dealers / liquidity providers who replenish resting
    quotes at levels where the activity distribution shows dense two-sided
    business (acceptance). The microstructure premise: at accepted levels the
    flow is two-sided and adverse-selection-per-quote is lowest, so a provider
    can fade one-sided excursions away from acceptance profitably as flow
    reverts into the accepted region.
- Why FX spot specifically: spot FX is a decentralized, quote-driven market
  with no central book; recurring session structure (Tokyo fix, London open and
  fix, NY session) generates repeating execution demand at similar price levels
  day after day, so a multi-day **size-weighted** activity-by-price histogram
  (per-tick sizes summed — section 3) concentrates exactly where that
  recurring business transacted, weighted by the size of the business. The
  class's session clock (section
  4) targets the two deepest sessions (London, NY) where this two-sided
  business concentrates.
- **Stop-cluster fuel at low-volume nodes is DECLARED SECONDARY, not primary.**
  Stops clustering just beyond obvious levels, and trapped breakout exits
  fueling the return through an LVN, is a plausible accelerant — but "stop-flow
  pays" is the payer family the fenced range-fade class claimed
  (TRACKA2-C1C2C3-REGATED-RANGEFADE: "same stop-flow payer"). This class does
  NOT rest its case on that payer; it is named here only because a hostile
  reviewer will ask, and the causal controls (section 7) are designed so the
  class must earn its edge from the acceptance structure, not from stop
  cascades.
- **Session-flow cyclicality** is part of the payer story (recurring execution
  demand), which is exactly why the clock-only shadow control (7c) is mandatory:
  if the session pattern alone reproduces the arm, the clock did the work (Q-7)
  and the payer story is unfalsified window-dressing.
- **Honesty limits**: no order book, no FIX/flow tape, no positioning data is
  observed. The payer is a hypothesis. The program's own history sets the bar:
  `COMMNG1-A4-P2` shows even OBSERVED positioning (CoT) lost to its bare
  release-clock shadow; so a fortiori this class must beat a clock-only shadow
  with the volume observable doing measurable work (Q-11) before any payer
  claim is credited. A negative result's interpretation is in section 9.5.

---

## 3. OBSERVABLE + PROXY DISCLOSURE

### 3.1 The observable and what it actually is (CORRECTED by Lane D audit, r1)

Observable = **M1 size-weighted volume of the Dukascopy feed**: the `.bi5`
volume column (`vol_f32`; record format empirically pinned by Lane D as
24-byte big-endian `>u4 x5 + >f4` = sec-offset, open, close, low, high,
volume_f32; prices ÷1e5 for EURUSD/GBPUSD, ÷1e3 for USDJPY).

**Measured semantics (Lane D, `poolB/data_audit/DATA_AUDIT_REPORT.md` §C —
the audit's main strategy-semantics finding): the column is a SIZE-WEIGHTED
SUM OF PER-TICK VOLUMES per minute per side, in Dukascopy volume units — NOT
a tick count, and NOT confirmed to any absolute unit.** Evidence (quoted
from the audit): only 2.49% (EURUSD) / 3.50% (GBPUSD) / 3.71% (USDJPY) of
active minutes have integral volume — a per-minute tick count must be
integral, and float32 represents integers exactly to 2^24, so non-integrality
refutes the count premise; the raw 4 bytes are float32 bit patterns encoding
values 0.09–2,985 (reading them as a uint "count" would give ~10^9 ticks per
minute — absurd); 86–97% of positive values are multiples of 0.01 at small
sizes (two-decimal quantization, finer fractional parts from float
accumulation in large sums). The field honestly tracks activity: 92.05–92.33%
of weekday minutes active; London/NY-core vs Asia-lull mean-volume ratio
1.97–3.17×; Pearson corr with per-minute H−L range 0.52–0.67; BID/ASK volume
corr 0.72–0.91 with identical tradable masks and ASK/BID total ratio
0.93–0.96.

Declared as a **proxy**, with the direction of the correction stated
honestly: **this is CLOSER to a true volume profile than the tick-count
proxy this spec originally declared.** Per-tick SIZE information is present
(the field sums sizes, not counts), so a bin's accumulated value measures
size-weighted activity, not mere quote-update density — which STRENGTHENS
the level-acceptance claim: acceptance is now measured in the quantity the
payer story (section 2) actually needs — the size of the two-sided business
that transacted at a level — subject to the unit caveat that the absolute
basis of that size is unverifiable from the candles (absolute unit =
NOT_RUN in the audit's verdict table; pinning it would need instrument
metadata or tick files, neither of which exists in these panels).

What this class CANNOT claim (hard limits, rewritten r1):

- **No absolute notional semantics.** The Dukascopy unit (lots? base
  currency? millions?) is opaque — unit basis NOT_RUN. No conversion of
  volume values to lots, base-currency units, or quote-currency notional is
  legal anywhere in the class; no "size defended a level" statement
  denominated in currency may be made.
- **No cross-pair volume comparability.** Absolute volume levels are
  comparable across pairs only if the unit is confirmed — it is not.
  Within-pair relative constructions (argmax, percentile ranks, ratios) are
  unit-invariant and safe (3.3); any cross-pair pooling or comparison of
  RAW volume values is forbidden.
- **No count semantics.** Nothing may depend on integrality, on exact
  arithmetic identities of volume values, or on a "number of prints"
  interpretation; the field is a float accumulation with two-decimal
  quantization at small sizes.
- **No cross-venue generalization.** This is one pool's size-weighted
  activity (Dukascopy), a proxy for global FX flow — unverified on any
  other venue.
- **Volatility/time-of-day contamination persists.** The field correlates
  0.52–0.67 with per-minute range and carries a ~2–3× session cycle, so the
  profile still partially proxies "turbulence and time spent at price";
  control 7d (uniform-weight profile) measures exactly this residual and
  remains gating.

### 3.2 Volume-profile construction rule (all frozen)

- **Freeze stamp**: every Friday 20:00 UTC (the campaign master clock). The
  profile governing the following week (Sunday reopen through Friday 19:55 UTC)
  is computed once, from data ≤ stamp only. 286 weekly freezes on the campaign
  calendar (52-week warmup consumed before the first tradeable week).
- **Lookback `L_PROFILE = 20` trading days** ending at the stamp. A trading day
  = a UTC weekday having ≥ 360 tradable M1 minutes (tradable = bid and ask both
  present with volume > 0 both sides, per PIT_COST_FREEZE_DRAFT Appendix B
  convention). Weekends/holidays excluded by this rule, not by a hardcoded
  calendar.
- **Price bin width `W_BIN = 0.25 x ATR20d`**, where ATR20d = mean daily true
  range over the same 20 days (daily bars aggregated from M1: high = max M1
  BID high, low = min M1 BID low, close = last M1 mid close of the day; TR
  standard formula). W_BIN quantized DOWN to the 0.1-pip grid (pip = 1e-4 for
  EURUSD/GBPUSD, 1e-2 for USDJPY; spread quantum 0.1 pip exactly on all three
  pairs per Appendix B). Floor: W_BIN ≥ 0.1 pip.
- **Assignment**: each tradable M1 bar's volume is assigned to the bin
  containing its **mid close** `m_t = (bid_close + ask_close)/2`. The volume
  value used is the **BID-side column** (frozen r1: the audit shows BID and
  ASK volumes are two slightly different measures of the same flow — corr
  0.72–0.91, ASK/BID total ratio 0.93–0.96, identical tradable masks — so
  one side must be frozen; the ASK column is declared and NOT used; the
  choice is deterministic and recorded in the arm_config_digest).
- **POC** = bin with maximum total assigned activity; tie → lowest bin index.
- **Value Area (VA)** = the minimal set of consecutive bins containing POC
  whose cumulative activity ≥ **`VA_SHARE = 0.70`** of window total; built
  greedily: start {POC}, repeatedly add the adjacent bin (up or down) with the
  greater activity (tie → up), stop at the first crossing of 70%.
  `VAH` / `VAL` = upper/lower boundary prices of the extreme bins.
- **HVNs/LVNs**: `P20` = 20th percentile of activity across populated bins. An
  **LVN run** = a maximal contiguous run of populated bins each with activity
  ≤ P20 that is bounded above AND below by populated bins with activity > P20
  (a hole between acceptance regions; runs touching the profile extremes are
  tails, not nodes). **Node level `N`** = midpoint of the run's price span.
- All thresholds are single frozen values; no per-pair tuning, no grid.

### 3.3 Unit-invariance check (arm constructions vs the corrected semantics)

The r1 correction changes the MEANING of the profile (size-weighted
acceptance, not activity-count acceptance) — it is now verified that it
changes NO frozen parameter and NO trigger definition: every construction
in this spec is ratio/ordinal-based, hence invariant under any positive
affine rescaling of the volume unit (the only freedom an opaque unit
allows). Clause-by-clause:

| construction (section) | dependence on volume | unit-invariant? |
|---|---|---|
| tradable-minute rule, vol > 0 both sides (3.2, 4.2) | sign only | yes — BID/ASK tradable masks measured identical |
| POC = argmax total bin activity (3.2) | ordinal | yes — argmax preserved under positive affine maps |
| VA = minimal bin set around POC ≥ 70% of window total (3.2) | ratio of the window total | yes — 70% of a rescaled total is the same set |
| LVN threshold = P20 of populated bins' activity (3.2) | percentile | yes — percentile ranks invariant under monotone maps |
| VC1 beyond-edge condition: two bins beyond edge ≤ P20 (5.1) | percentile | yes |
| VC3 acceptance condition: current bin ≥ P80 (5.3) | percentile | yes |
| CTRL-B1/B2 placebos, within-day / full-window volume permutations (7b) | permutation of values | yes — preserve the value multiset; unit-agnostic |
| CTRL-D uniform-weight profile, volume := 1 (7d) | removes weighting | yes — unit-free by construction |

No arm rule uses absolute volume magnitudes, integrality, or cross-pair
volume levels. The one place raw volume values could have leaked in —
cross-pair aggregation — is explicitly forbidden (3.1); each candidate's
profile is built and used strictly within its own pair.

---

## 4. CLOCK + PIT

### 4.1 Clocks

- **Master weekly decision**: Friday 20:00 UTC (unambiguous UTC stamp). At the
  stamp the class freezes the week's profile, W_BIN, ATR20d, P20/P80 and all
  arm parameters. Nothing computed after the stamp may enter the week's state.
- **Intraday session clock** (all arms are intraday session-class legs; the
  campaign design §1 explicitly admits this class of clock): entries are
  permitted only inside
  `ENTRY_WINDOW = [08:00, 12:00) Europe/London  ∪  [09:30, 16:00) America/New_York`
  converted to UTC per calendar date from a **pinned IANA tzdata version**
  (data dependency, section 10). **No hardcoded DST offsets** — the conversion
  is the only place offset knowledge lives, and it is calendar-rebuilt. A
  session window containing zero tradable M1 minutes is a holiday: that
  session's entries are skipped that day (panels are the holiday authority).
- **No-trade window**: 21:00–23:00 UTC daily (declared rollover event window).
  **Hard flat**: 19:55 UTC daily; from Friday 19:55 UTC through Sunday reopen
  no position may exist (weekend gap and Sunday-reopen spread C3 are
  structurally avoided — GBPUSD/USDJPY reopen medians 13.4/11.0 pips make any
  reopen exposure non-viable).

### 4.2 Available-time rules (every input)

| input | available at |
|---|---|
| M1 bar (bid/ask o,c,l,h + volume) | its close minute + 1 minute (the next bar's open); decisions at a bar use only bars closed ≤ that bar |
| weekly profile (POC/VA/LVN/W_BIN/ATR20d/P20/P80) | the Friday 20:00 UTC freeze stamp |
| ATR60 (mean true range, last 60 M1 bars, bid h/l + mid close) | the decision bar close |
| session marks | pinned tzdata calendar — deterministic, known ≥1 year ahead |
| spread at fill | the fill bar's own bid/ask quotes (panel-venue measured) |

**Staleness fail-closed**: at any decision instant, if the newest available M1
bar is older than 90 seconds, that instant is NOT_RUN — no decision, no fill,
no interpolation, no state carry-forward — until fresh data resumes.

### 4.3 Fill model (PIT freeze R3)

- All fills at **next-bar-open at the quoted side**: buys at the next bar's
  ask open, sells at the next bar's bid open.
- Per-side cost = the **full observed spread at the fill bar** (panel venue)
  **+ U3 slippage band (0.2 pip non-event; 1.0 pip inside event windows)**.
  By design no fill can occur inside 21:00–23:00 UTC (flat by 19:55); any
  in-window fill is a spec violation → campaign STOP-3 integrity stop, not a
  priced event.
- Stops are evaluated on bar data (quoted-side extremes: bid for long
  exits, ask for short exits) and fill at the NEXT bar open at the quoted
  side — gap-through is charged honestly, never assumed filled at the stop
  price.
- Truncation-replay no-lookahead verification (campaign §8.1) applies verbatim:
  fold k recomputed on truncated data must be prefix-identical.

---

## 5. ENTRY / EXIT per arm (mechanical, frozen parameters)

Common state (weekly-frozen): POC, VAH, VAL, W_BIN, P20, P80, node set {N},
ATR20d; live state: M1 mid closes, ATR60, session windows. All triggers
evaluated on M1 bar closes inside ENTRY_WINDOW; entries fill next bar open
(ask for longs, bid for shorts); one position per candidate at a time;
**cooldown `COOLDOWN_MIN = 60` minutes** after any exit before the same
candidate may re-enter; unit position size (10,000 base units), no pyramiding,
no sizing rules here.

### 5.1 VC1 — VA-EDGE-REJECT (value-area-edge rejection fade)

- **Trigger** (all conditions on one bar): previous bar mid close was inside
  [VAL, VAH]; current mid close < `VAL − 1.0 x W_BIN` (fresh downside
  excursion) or > `VAH + 1.0 x W_BIN`; AND the frozen-profile activity of the
  two bins immediately beyond that edge (below VAL / above VAH) is **≤ P20**
  (the region beyond the edge is low-acceptance).
- **Direction**: long from the lower edge, short from the upper edge
  (fade back into value).
- **Entry**: next bar open (ask / bid).
- **Exits** (first to fire):
  1. **Take-profit**: next-bar-open exit when mid close crosses the POC level.
  2. **ATR stop**: `STOP_ATR = 1.0 x ATR60` from entry; triggered when the
     quoted-side adverse extreme (bid low for longs / ask high for shorts)
     touches the level; exit next bar open.
  3. **Time stop**: hard flat at 19:55 UTC the same trading day.
- **Falsifier (own)**: control 7b — under the B2 full-window permutation the
  edge level and the low-acceptance condition both degenerate; if the arm's
  measured behavior does not degrade vs the B2 placebo ensemble, the edge is
  not from the acceptance structure.

### 5.2 VC2 — LVN-TRAVERSE-FAIL (low-volume-node traverse failure)

- **Trigger**: during ENTRY_WINDOW, mid close crosses a node N downward
  (previous ≥ N, current < N) or upward; then within the following
  `TRAVERSE_CONFIRM_MIN = 60` minutes a mid close returns to the origin side
  of N by ≥ 1.0 x W_BIN (the traverse failed to hold the far side). Entry on
  the bar after the confirming return.
- **Direction**: long after a failed DOWN-traverse (price returning into the
  acceptance region above N), short after a failed UP-traverse.
- **Exits** (first to fire):
  1. **Take-profit**: next-bar-open exit on mid close touching the POC level.
  2. **ATR stop**: 1.0 x ATR60 beyond N on the traverse side (i.e., for a
     failed down-traverse, stop is N − 1.0 x ATR60); exit next bar open.
  3. **Time stop**: `TMAX_MIN = 240` minutes from entry, and hard flat 19:55
     UTC in all cases.
- **Falsifier (own)**: control 7b — the node set {N} is profile-derived; if
  the B2 placebo ensemble (full-window permuted volume) reproduces the arm,
  the LVN is decoration on a generic failed-breakout rule.

### 5.3 VC3 — POC-MAGNET (POC reversion inside value)

- **Trigger**: mid close strictly inside (VAL, VAH);
  |mid close − POC| ≥ `DEV_K = 3.0` x ATR60; AND the frozen-profile activity
  of the bin containing the current mid close is **≥ P80** of populated bins
  (price is parked in an accepted node, deviated from the mode).
- **Direction**: toward POC (long below POC, short above).
- **Exits** (first to fire):
  1. **Take-profit**: next-bar-open exit when |mid close − POC| ≤
     `TP_POC_TOL = 0.5 x W_BIN`.
  2. **ATR stop**: 1.0 x ATR60 beyond entry; exit next bar open.
  3. **Time stop**: 240 minutes, and hard flat 19:55 UTC.
- **Falsifier (own)**: controls 7b AND 7d. This is the arm whose anchor could
  be replaced by a price-only statistic (a slow band); the two-arm placebo
  (B2 governs, r2) and the
  uniform-weight profile are its designated primary falsifiers, and the
  representation-rho vs DT100-13-VWAPMR / DT100-15-BOLLFADE (section 8.4) is
  its mandatory disclosure. Designated likeliest casualty of the class
  (section 12).

Position direction summary: all three shapes are two-sided, mean-reverting,
intraday, flat-by-19:55-UTC; no overnight holds, no weekend holds.

---

## 6. COSTS (per COST_AUTHORITY_TABLE — SLEEVE-FX5-100K-V1/pitcost)

Measured-vs-declared status per component (verdict law: MEASURED beats stated;
a load-bearing component with no measurement is DECLARED_PESSIMISTIC and caps
every survivor at PROVISIONAL):

| comp | content | status | how it prices THIS class |
|---|---|---|---|
| C1 | spread at fill hours | **MEASURED** (panel venue) — full per-hour p50/p90 schedule, 24 UTC hours x 3 pairs (PIT_COST_FREEZE_DRAFT Appendix A) | each side charged the observed spread at the fill bar; audit baseline = the arm's fill-hour cells (London/NY hours, e.g. 13h–16h UTC: EURUSD 0.3/0.5, GBPUSD 0.8/1.1, USDJPY 0.5/0.8 p50/p90 pips); Friday-20:00 cells EURUSD 0.3/0.5, GBPUSD 0.8/1.3, USDJPY 0.5/0.9 (n=286/286) |
| C2 | rollover-window spread (21:00–22:00) | **MEASURED** (panel venue) — **Lane D r1 FLAG**: the table's Mon–Thu cell was measured on the wrong hour (22–23Z vs its declared (21:00,22:00]) and understates the declared window ~1.3–2× (true p50/p90: EURUSD 1.2/3.7, GBPUSD 2.8/7.8, USDJPY 2.1/7.4) | structurally unused — no fills 21:00–23:00 UTC by design; any in-window fill = STOP-3 integrity stop, not a priced path. The C2 correction is a CROSS-LANE action item (COST_AUTHORITY_TABLE owner) before any roll-window-sensitive trial program-wide is costed; immaterial to this class by construction |
| C3 | Sunday-reopen spread | **MEASURED** (panel venue) | structurally unused — no weekend positions (GBPUSD 13.4/23.8, USDJPY 11.0/22.0 p50/p90 pips are why reopen exposure is design-forbidden) |
| C4 | commission per side | **DECLARED_PESSIMISTIC (U2)** | 0.35 bps of notional per side (≈ $3.5 per $100k lot/side); load-bearing, unmeasured workspace-wide |
| C6 | slippage beyond spread | **DECLARED_PESSIMISTIC (U3)** | 0.2 pip per side non-event / 1.0 pip inside event windows; event band structurally unused |
| C5 | swap / financing | **DECLARED_PESSIMISTIC (U4, U5)** | 1.0 pip/night charged AGAINST the position both directions, Wednesday x3, accrual boundary 22:00 UTC, never income |

**Hold-length design consequence (mandatory statement)**: every arm is
intraday with hard flat at 19:55 UTC, so **no position ever crosses the 22:00
UTC accrual boundary — the swap bill is 0 by construction**. The class is
therefore swap-INDEPENDENT: neither swap-receiving (which would be
BLOCKED_COST under the pessimistic-symmetry law) nor swap-paying. Any future
amendment allowing holds past 22:00 UTC reopens the swap bill at 1.0 pip/night
against (Wed x3) and must re-clear the whole cost section.

- Stress tiers **x1.0 / x1.5 / x2.0 on ALL cost components** (spread charge,
  U2, U3; U4/U5 structurally zero).
- **GROSS and NET dual books**; every NET number carries the mandatory label
  **`NET_DEFAULT_COST`**; every survivor carries
  **`PROVISIONAL_PENDING_COST_AUTHORITY`**; every trial's `cost_tier` labels
  the **panel-venue** basis (Dukascopy-feed spreads; the panel↔IBKR transfer
  is UNMEASURED — the n=1-day paper windows are not cost authority per owner
  directive 2026-09-29).
- Venue-transfer caveat (inherited verbatim from COST_AUTHORITY_TABLE C1):
  measured cells are Dukascopy-feed; execution-venue spreads enter only
  through the SIXSOURCE bounded-session accumulation path (≥200 valid
  two-sided obs per pair-hour bucket), which does not exist today.

---

## 7. CAUSAL / PLACEBO CONTROLS (null-validity per Q-11 / Q-7)

Four control ids (CTRL-B is a TWO-ARM placebo family since r2 — the
stronger arm B2 governs its kill, B1 is a decomposition diagnostic), each
defined with its kill condition and its null-vacuous
condition. Controls are re-evaluations of the SAME frozen arm rule (zero extra
scored cells) and are gating (section 9). Q-11 law applied throughout: a
permutation is a null only if it moves the signal — every control below ships
with a movement diagnostic, and a control that cannot move the signal is
itself a finding.

### 7a. CTRL-A — dwell-matched random-entry control

- **Design**: same pair, same calendar. For each of the arm's realized trades,
  generate a control trade with the SAME holding length (entry-to-exit
  duration, preserving the signal's dwell profile), entering at a uniformly
  random minute drawn from the arm's own entry-window occupancy (same
  hour-of-day x weekday distribution), direction = random ±1 drawn from the
  arm's realized long/short ratio, same cost bill. Same number of trades.
- **What kills the arm**: control NET expectancy ≥ arm NET expectancy on the
  same window (the entry information adds nothing over dwell + calendar
  occupancy) → `CONTROL_OUTEARNED_ANCHOR` / `CONTROL_REPRODUCED_MECHANISM`
  kill (precedents: FXFV2-A4-P2 placebo ≈ anchor; V17-A4-P1-WKNDLIQ
  clock-shadow).
- **Null-vacuous**: if the arm itself is below floors (< 20 decisions) the
  control cannot be populated meaningfully → the arm is `NOT_RUN_THIN`
  (section 9), NOT a pass.

### 7b. CTRL-B — volume-placebo control (the decisive one) — TWO-ARM FAMILY (r2)

Remediation r2 (skeptic finding F-9 MEDIUM, 2026-09-29): the r0/r1 design —
a day-blocked within-day shuffle, now **CTRL-B1** — preserves the
**cross-day volume↔price-range association** (each day's TOTAL volume stays
inside that day's price range, whatever the within-day assignment), so on
its own it did not warrant this section's "destroys the level-acceptance
structure" claim. CTRL-B is therefore redefined as a **two-arm placebo
family**: the STRONGER arm (**CTRL-B2**) governs the kill; CTRL-B1 is
retained as a decomposition diagnostic. Both arms run the SAME frozen arm
rule on placebo profiles (permutations of size-weighted values; unit-agnostic,
3.3); `N_SHUFFLE = 20` seeds minimum per arm per candidate.

- **CTRL-B1 — day-blocked within-day minute permutation** (the r0/r1
  construction): within each trading day of the 20-day lookback, permute the
  minute→volume assignment across that day's minutes; price path unchanged;
  each day's volume multiset unchanged.
  - **Survives BY CONSTRUCTION (stated exactly, per F-9)**: the price path;
    each day's volume multiset and total; and the association between each
    day's TOTAL volume and that day's price range — the day's aggregate
    volume is scattered within the day's own range and never outside it. The
    intraday seasonal shape is destroyed (within-day time↔volume decoupled).
  - Tests therefore ONLY the within-day covariation of volume and price
    level. NOT a valid null for the full level-acceptance claim on its own:
    a profile whose mode is driven by WHICH DAYS were heavy (cross-day
    structure) survives B1 intact.
- **CTRL-B2 — full-window minute permutation (the stronger arm; GOVERNS THE
  KILL)**: permute the minute→volume assignment across ALL tradable minutes
  of the 20-day lookback in ONE global permutation (no day blocking); price
  path unchanged; the window's volume multiset unchanged.
  - **Survives BY CONSTRUCTION — exactly two things**: (i) the multiset of
    per-minute size-weighted volume magnitudes (window-wide), and (ii) the
    price path. Nothing else survives: intraday seasonal shape destroyed,
    day totals dissociated from day ranges, and every volume↔price-level
    pairing — within-day AND cross-day — broken.
  - **Why the surviving structure CANNOT produce a POC at an acceptance
    level**: under the global permutation the placebo profile's sampling
    distribution is a function of exactly two objects — the time-at-price
    histogram and the volume magnitude multiset — and of nothing else in
    the real data; in particular it is INDEPENDENT of the real
    volume↔price-level assignment. Its expectation is
    (total volume / N minutes) x (minutes spent per bin) — a rescaled
    time-at-price histogram, i.e. CTRL-D's profile up to scale — and each
    seed's deviation from that expectation is exchangeable assignment
    noise. A mode created by WHERE volume concentrated cannot arise from a
    magnitude multiset plus a price path; only the time-at-price mode plus
    noise can. B2 is therefore the warranted null for the claim "the edge
    is not from the volume-by-price assignment at any granularity".
- **Movement diagnostic (Q-11, gating — keyed to B2)**: across B2 seeds,
  median |POC_B2 − POC_real| ≥ 1.0 x W_BIN. If B2 cannot move the POC by a
  bin, the real POC coincides with the time-at-price mode — the volume
  weighting is not doing identifiable work on that pair-week
  (`OBSERVABLE_NOT_IDENTIFIABLE`; the CTRL-D TIMEPROF-M1 relabel applies).
  **B1's failure to move the POC is NOT a kill and NOT vacuity** — it is
  the decomposition finding that the POC is cross-day driven, disclosed as
  the label `POC_CROSSDAY_DRIVEN`.
- **What kills the arm (B2 governs)**: arm TRAIN NET expectancy ≤ the B2
  ensemble's 90th-percentile NET expectancy (`CONTROL_PLACEBO_NOT_DEGRADED`)
  — if the strategy's edge survives the stronger placebo, **the edge is NOT
  from the volume-by-price assignment at any granularity** (within-day or
  cross-day), and the arm is a re-labeled price-only law (the disclosure in
  section 8 then names which one).
- **Decomposition disclosure (B1, informative — not a kill)**: if the arm
  passes B2 (arm > B2 p90) but is not degraded vs B1 (arm ≤ B1 p90), the
  profile's information is carried by the cross-day / day-level component
  rather than the within-day covariation. That is still volume-by-price
  information (the 20-day histogram is built from day-level assignment
  too), so it is NOT a kill — but the label
  `EDGE_CROSSDAY_COMPONENT_ONLY` is carried into the identity tuple, the
  trial ledger and the complementarity narrative: it changes WHERE the edge
  sits, sharpens the CTRL-C/CTRL-D interpretations, and is exactly the
  distinction F-9 demanded the placebo family be able to see.

### 7c. CTRL-C — clock-only shadow (Q-7)

- **Design**: identical entry calendar — same session windows (London ∪ NY,
  tzdata-rebuilt), same weekday/session occupancy, same number of entries,
  same holding-length distribution as the arm — with ALL volume/level
  information removed: entry times sampled to match the arm's hour-of-day x
  weekday histogram, direction sampled from the arm's realized long/short
  ratio, exits at the arm's realized hold quantiles. The clock does
  everything the level structure did, or doesn't.
- **What kills the arm**: shadow NET expectancy ≥ arm NET expectancy → the
  clock did the work (Q-7; precedents: FXFV2-A4-P2, COMMNG1 release-clock
  control out-earning every positioning arm, V17 WKNDLIQ) → kill.
- **Null-vacuous**: if the arm's entry occupancy is itself near-uniform across
  the session windows (no clock signature to strip), the shadow degenerates to
  CTRL-A — disclosed, and CTRL-A remains the operative control; the Q-7
  question is then answered by CTRL-A.

### 7d. CTRL-D — uniform-weight profile control (proxy honesty)

- **Design**: rebuild the profile with every tradable minute's volume set to 1
  (a pure TIME-AT-PRICE histogram — level structure kept, volume weighting
  removed); run the same frozen arm rule.
- **What it adjudicates**: how much of any edge is "time spent at price"
  rather than "size-weighted activity concentrated at price" (post-r1 the
  contrast is sharper: it separates size-weighted acceptance from pure
  time-at-price — exactly the increment the corrected observable claims to
  carry). If the arm on the real
  profile does not beat the arm on the uniform-weight profile (TRAIN NET),
  the volume weighting adds nothing beyond dwell-at-level: the class is
  thereby re-labeled **TIMEPROF-M1** in every artifact, the proxy disclosure
  (section 3) becomes the whole truth of the observable, and the payer story
  (section 2) loses its size-weighted-acceptance premise — an honest
  downgrade, recorded as a
  label; if the uniform-weight version EARNS MORE, the volume weighting is
  actively harmful and the class's observable claim is falsified → kill
  (`PROXY_WEIGHTING_NEGATIVE`).
- **Null-vacuous**: if the real and uniform profiles coincide (activity
  uniform across populated bins), the two arms are identical — the
  observation itself proves the volume axis is vacuous on that pair-week
  (feeds the `OBSERVABLE_NOT_IDENTIFIABLE` finding of 7b).

---

## 8. ANCESTRY DISCLOSURE — MEASURED-AND-DISCLOSED, **INFORMATIVE, NOT GATING**

> **Under owner amendment 2026-09-29 this section is informative, not gating.**
> It exists to (i) carry the failure history of adjacent dead families as an
> outcome-exposed label on every candidate, (ii) define the representation-rho
> protocol whose output feeds the redundancy / diversification analysis and the
> multiple-testing narrative (a candidate that is a rho-twin of a dead family
> contributes no diversification and any positive it produces is attributed to
> the dead family's exposure in the discovery ledger), and (iii) preserve the
> verbatim fence texts as recorded history. It does NOT block admission.

### 8.1 The primary neighbor: DT100-13-VWAPMR — full death record

**FAMILY_FAILURES.jsonl line 146 (verbatim):**

```json
{"schema": "family_failures/entry@1", "cycle_id": "DAYTRADER-100-V1", "asset": "crypto", "family_id": "DT100-13-VWAPMR", "family_title": "DT100 rescore anchor (owner order 2026-09-28)", "status": "CLOSED", "verdict_class": "SCIENTIFIC_REJECTION", "no_quality_evidence": false, "primary_failure": {"code": "NEGATIVE_EXPECTANCY", "detail": "exp -2.18 bps, PF 0.835, trades 2002, folds+ 0/4"}, "secondary_failures": [], "measured_summary": "owner-ordered ancestry-relaxed rescore; non-independent trial by construction", "evidence": {"terminal_sha": "b554f52d654f34ea097121e19ffc590066f9f1fe", "evidence_path": "research/control/DAYTRADER-100-V1/scored/SCORED_REPORT.md", "ledger_row": "research/wayfinder/HYPOTHESIS_LEDGER.md (DAYTRADER-100-V1 row)"}, "recorded_by": "Lead", "recorded_utc": "2026-09-28T12:00:00Z"}
```

**What it actually was (reconstructed from primary artifacts — two corrections
to the ledger row, both material):**

- **Universe/clock**: the DT100 engine config
  (`.worktrees/daytrader-100-v1/integration/research/daytrader100/dt100/arms.py`,
  FX section) shows `dict(family="DT100-13-VWAPMR", asset="fx", symbol="EURUSD",
  res="1m", anchor=band 2.0/hold 120, n1=band 1.5/hold 120, n2=band 2.5/hold
  180)` — i.e. **EURUSD M1**, tradable window 07:00–20:00 UTC, fixed hold.
  The FAMILY_FAILURES `asset: "crypto"` label is **wrong** for this record
  (uniform DT100-row labeling; the same defect affects DT100-07-PDHLSWEEPFX,
  also EURUSD 1m). The neighbor is therefore **same pair, same bar size** as
  one of this class's panels — closer than the F0 salvage note 1 implied.
  Recorded as incident I-1 in the handoff.
- **The rule** (`dt100/signals.py::vwap_mr`, verbatim logic): anchor = UTC-day
  cumulative mean of the CLOSE price (`tp = df["c"]`; `vwap = cumsum(tp)/count`
  within day); band = 60-bar rolling std of close; enter long when
  `(c − vwap)/sd < −band`, short when `> +band` (previous-bar value), inside
  07:00–20:00 UTC; hold fixed 120/180 bars. **Despite the name, the anchor is
  volume-BLIND — a running mean of price, no volume field anywhere.** The
  skeptic's M-3 note called it a "volume-weighted-anchor neighbor"; the
  implementation shows it is an unweighted day-anchored price mean. Recorded
  as incident I-2.
- **Why it died**: NEGATIVE_EXPECTANCY exp −2.18 bps, PF 0.835, 2,002 trades,
  0/4 folds positive (anchor arm; n1 identical, n2 −1.89 bps PF 0.86); at
  x1.5/x2.0 stress −3.21/−4.24 bps (SCORED_REPORT.md). Doubly recorded: the
  census matrix had already verdicted the family AV (ANCESTRY_VETOED,
  "Range-fade/MR class (2026-09-26 PIT-seam)"), and the rescore was an
  owner-ordered, explicitly non-independent trial.
- **Provenance of the reopen condition this spec answers**: SKEPTIC_NOREVIEW
  M-3 (verbatim): "any future M1-pair volume-profile row must clear it and
  declare the tick-count volume proxy." Under the 2026-09-29 amendment
  "clear" is no longer a gate; the clearing evidence is still produced (the
  rho protocol below) and carried as a label. The proxy duty is discharged
  **with the Lane D r1 correction**: the declared observable is
  size-weighted volume in an unverifiable Dukascopy unit (section 3) — NOT
  the tick count the M-3 note assumed; the disclosure obligation is met, and
  the semantics it assumed were wrong (handoff incident I-3).

### 8.2 Neighbor comparison table (skeleton / information source / clock / payer / what differs here)

| dead family (record) | skeleton | information source | clock / universe | payer claimed | what differs in VOLPROF-M1 |
|---|---|---|---|---|---|
| **DT100-13-VWAPMR** (L146; EURUSD 1m; exp −2.18 bps PF 0.835 0/4) | deviation fade toward an intraday anchor | own price only — day-anchored cumulative mean of close; volume-blind | 1m EURUSD, 07:00–20:00 UTC, fixed 120/180-bar hold | none named (generic MR) | observable = size-weighted volume-by-price distribution (20-day, weekly-frozen; unit-invariant constructions, 3.3); anchor = size-weighted activity mode, not time-average of price; payer named (resting liquidity at accepted levels); session clock tzdata-rebuilt; placebo battery that did not exist for the dead rule. VC3 is the same skeleton — the rho protocol measures the separation |
| **DT100-15-BOLLFADE** (L147; EURUSD 1m, win 60 k 2.0 hold 180; exp −0.16 bps PF 0.957 0/4) | band fade | own price (rolling mean/std) | 1m EURUSD | none named | the band/levels here are activity-distribution quantiles, not price-rolling-statistic bands |
| **FXOS-04** (L120; EURUSD 15m Bollinger MR fade, measured bid/ask costs) | oscillator band MR fade | own price (Bollinger) | 15m EURUSD, force-flat pre-rollover | none named | different level definition (activity structure vs price bands); this class additionally ships the placebo/clock controls whose absence let FXOS-04's dev-edge survive to a holdout; LONG_ALWAYS-baseline comparison inherited into section 9 |
| **TRACKA1-M1-RANGEFADE-PIT** (L127; prev-day H/L fade 07–18 UTC on AUDUSD+USDCAD 2021-2025) | range-edge fade | own price (prev-day extremes) | M1, two pairs | stop-flow at range edges | level = VA edge (activity-defined), not price extreme; payer claim is resting-liquidity/exec-flow, NOT stop-flow; EURUSD/GBPUSD/USDJPY surfaces are exactly the ones that family's fence said were "consumed" — a successor there needs a new identity, which is precisely the claim this spec makes and submits for measurement |
| **TRACKA2-C1C2C3-REGATED-RANGEFADE** (L134; gated range-edge fade: provenance/retest/probe gates) | range-edge fade + gate | own price + own-price-derived gates | M1 AUDUSD/USDCAD | stop-flow (fence names it) | the "gate" here (P20 low-acceptance beyond the edge) is derived from the volume-by-price observable — a new information layer, not an own-price gate; whether it does measurable work is exactly what CTRL-B/CTRL-D decide (the C1C2C3 precedent — "stripping each new observable degenerates to the dead decision law" — is the disclosed risk) |
| **DT100-83-FAILBRK** (L166; BTCUSDT 1m fail_breakout rwin 60 confirm 15 hold 60; exp −10.56 bps PF 0.569 0/4) | failed-breakout reversal | own price (rolling extremes) | 1m BTC | none named | VC2's node is an activity hole, not a rolling price extreme; failure confirmation is vs the node, profile-frozen weekly |
| **FXFV2-A4-P2** (L35; London-AM range break + retest-hold) | break + retest | own price (session range) | intraday FX, 7 pairs | none named (session chasers implied) | retest object is the LVN (activity hole) not a session-range boundary; placebo≈anchor kill of the dead family is the exact control shape this spec preregisters as CTRL-B |
| **FXFV2-A4-P1** (L34; Tokyo-range→London expansion, −3.804/trade PF 0.593) | session-transition conditional | own price (session range/ATR) | intraday FX | session chasers | no session-transition conditioning; entries allowed across the whole London∪NY window; clock-only shadow (CTRL-C) is the standing guard |
| **FXFV1-A3-P1 / A3-P2** (L32/33; London-open continuation −2.35/trade across 7 pairs, 11,459 trades; late-NY fade, 6/6 reject) | session-clock book | own price | intraday FX, 7 pairs | none named | no fixed session-open event trigger; the session windows are exposure windows, not triggers; CTRL-C guards the residual |
| **DT100-09-ASIANRANGE** (L144; EURUSD 1m asian_range edge_frac 0.10; PF 1.066 < threshold) | session-range conditional | own price (Asian-range extremes) | 1m EURUSD, London window | none named | as FXFV2-A4-P1 |
| **DT100-07-PDHLSWEEPFX** (L143; EURUSD 1m pdhl_sweep reclaim 0.0004; exp −0.52 bps PF 0.96 2/4) | prev-day-extreme sweep fade | own price (prev-day H/L) | 1m EURUSD | stop clusters | as TRACKA1 (level definition differs); nearest FX-M1 price-level fade on the same pair — mandatory rho counterpart |
| **DT100-31-JPYFADE** (L150; USDJPY 1m hourclock_fade hours 15–22 UTC zwin 30d band 1.5 hold 60; exp −0.71 bps PF 0.85 1/4) | clock-window z-score fade | own price (30-day rolling z) | 1m USDJPY, 15–22 UTC | none named | the only dead neighbor on USDJPY M1; its clock overlaps this class's NY window — rho counterpart for the USDJPY candidates; CTRL-C is its skeleton's standing guard |
| **TRACKA2-P3B-DINV-1D** (L131; spread-percentile day continuation; standing class veto on momentum re-labels, reopening NONE) | continuation | own price + quote-liquidity gate | D1 AUDUSD/USDCAD | dealer-inventory (continuation side) | no continuation arm is preregistered (the join-side was deliberately excluded, §1.1); if any future variant adds one, this veto is its first label |
| **SRLVCX1-M1-SETTLE-RESOLVE** (L136; BTC/ETH 1h sweep-then-absorption at pivot levels; all dev gates fail, inverted control out-earns, rho 0.25–0.26) | level-absorption fade | own price at pivot levels; PROXY_NOT_ORDERBOOK | 1h crypto | carry-forced deleveraging (claimed) | the closest "absorption at level" ancestor; died with its revival clause exercised in full — the lesson carried here: a granted information layer is not an edge; the placebo/inverted logic is built into CTRL-B |
| **A6-V16-F1 CLOSE-DISPLACE-FADE** (L54; BTC/ETH daily close-to-VWAP displacement fade; PF 1.064 razor) | VWAP-displacement fade | aggTrades daily VWAP (crypto, size-weighted in a known currency unit) | daily crypto | none named | FX spot, M1, size-weighted volume in an UNVERIFIABLE Dukascopy unit (r1) — same weighting kind, opaque basis, coarser (minute) granularity; different clock and construction |
| **DTPCX1-I001-PLAYBOOK-CORPUS** (L139; 11/11 codified day-trading rules dead by skeleton collision) | corpus-level fence incl. "range-fade → FXOS-04/TRACKA1-M1/TRACKA2-C1C2C3/A6-V16-F1" | — | — | — | the corpus-level death rate is the prior this class carries; under the amendment it is a label on the class, not a gate |
| **XSECT-VOLSHK-S15 / SFV4-A5-H1-PARTICIPATION-SHIFT / M01-AGGRESSOR-ABSORPTION-PANEL** (L4/L20/L5) | volume-observable books (dollar-volume shock, participation shift, aggressor absorption) — all dead on crypto/stocks at other clocks | volume (aggregate or order-flow) | daily/quarterly/other | various | these are the volume-observable neighbors; NONE used volume-by-price level structure — the F0 court's finding ("no dead volume-profile ancestor in the 169 records", with the skeptic's M-3 VWAPMR correction) is the claim this table documents |

### 8.3 What §14.3 would have said (and now labels instead)

HOW_TO_BE_A_LEAD_ENGINEER §14.3 (verbatim, historical law): "Family mới
không được là family đã reject đổi timeframe/threshold/vài-symbol/phí/tên/hướng
dấu/session nhỏ. Cơ chế + information source + causal control không mới ⇒
reject trước scoring." Under the amendment this rejects nothing by itself;
the spec states it plainly so the label is honest:

- **Symbol swap** (EURUSD→GBPUSD/USDJPY), **timeframe swap** (1m↔15m↔H1),
  **threshold change** (band 2.0→3.0; P20→P30), **sign flip**, **session-window
  rename** — each alone would make a candidate a re-labeled dead family, and
  the rho protocol below is expected to expose exactly that by producing high
  rho.
- The only axes on which this class claims separation from the neighbors are:
  **(i) the observable** — level-acceptance structure (activity-by-price
  distribution, weekly-frozen) vs time-average-of-price / own-price
  band/level statistics; and **(ii) the payer** — resting liquidity and
  recurring execution flow at accepted levels (named agents, section 2) vs
  unnamed generic MR or the fenced stop-flow family. Both claims are submitted
  to measurement (rho protocol; CTRL-B/C/D), and the measured outcome is
  carried as the candidate's label whatever it says.

### 8.4 Representation-rho protocol (P-29 method, informative output)

For every candidate (9) and every dead neighbor reconstructable on FX M1
panels, the campaign's Stage-A battery computes, before any PnL:

- **Reconstructions** (neighbor's own frozen rule, run on the SAME panel,
  same window as the candidate):
  - DT100-13-VWAPMR: day-anchored cumulative mean of M1 close, 60-bar rolling
    std, band {2.0, 1.5, 2.5}, hold {120, 120, 180}, 07:00–20:00 UTC
    (all three arms reconstructed).
  - DT100-15-BOLLFADE: win 60, k {2.0, 1.5}, hold 180 (and win 120, k 2.5,
    hold 240), M1.
  - FXOS-04: 15m Bollinger MR fade per its frozen cycle rule (EURUSD native;
    same rule applied to GBPUSD/USDJPY for those candidates' reconstructions).
  - TRACKA1 R-ANCHOR: prev-day H/L fade 07–18 UTC, next-open opposite quote,
    flat 20:00 (PIT-clean semantics — the seam-law limbs of the dead record
    are the anti-pattern this spec's freeze rules exist to avoid).
  - DT100-07-PDHLSWEEPFX: pdhl_sweep reclaim_frac 0.0004, M1.
  - DT100-31-JPYFADE: hourclock_fade hours 15–22 UTC, zwin 30d, band 1.5,
    hold 60, USDJPY M1.
  - DT100-83-FAILBRK: fail_breakout rwin 60 / confirm 15 / hold 60, M1
    (crypto-native rule applied to the FX panel for representation purposes —
    labeled as such).
  - FXFV2-A4-P2 / FXFV1-A3-P1/P2 / DT100-09-ASIANRANGE: session/range books
    per their recorded rules on the same panels.
  - Not reconstructable on FX M1 (skeleton-table label only, disclosed):
    A6-V16-F1 (daily crypto aggTrades), SRLVCX1 (1h crypto), XSECT-VOLSHK-S15,
    SFV4-A5, M01 (non-FX clocks/assets).
- **Metrics**: (i) **indicator-rho** — Pearson and Spearman on the ±1/0
  position series at decision points, pooled per pair and pooled class;
  (ii) **continuous rho** — on signed signal strength (e.g., signed
  distance-to-anchor in ATR units). Zero-excluded diagnostics reported
  alongside (TRACKA2-P3B precedent).
- **Bar**: the immovable 0.20 remains the REFERENCE bar for interpretation.
  Under the amendment its breach is not a kill; it is a **redundancy label**:
  `RHO_TWIN_OF_<family>` — the candidate contributes no diversification vs the
  dead family's exposure, any positive is attributed to that exposure in the
  discovery ledger and the multiple-testing arithmetic, and the Stage-B
  complementarity step treats it accordingly. The measurement runs BEFORE PnL
  regardless (P-27 ordering preserved: label first, evidence second).
- **Output location**: each candidate's `ancestry_fence_result` identity field
  (section 1.3) carries the full label vector (per-neighbor rho, indicator and
  continuous, per pair) — machine-readable, into the trial ledger.

### 8.5 Verbatim fence texts preserved (historical law, now labels)

Kept verbatim because a skeptic will check the spec knows them:

- TRACKA1-M1-RANGEFADE-PIT ANCESTRY_FENCE (L127): "EURUSD/GBPUSD/USDJPY
  consumed surfaces may not re-score this family as fresh evidence; any
  successor needs a new identity + forward evidence; holdout 2026-H1 on
  AUDUSD/USDCAD remains UNREAD."
- TRACKA2-C1C2C3-REGATED-RANGEFADE REOPENING_CONDITION (L134): "permanently
  closed against gate variants; only a mechanism with a NEW payer + new
  information layer (F-0 three tests) can carry a range-adjacent trigger."
- TRACKA2-P3B-DINV-1D REOPENING_CONDITION (L131): "none — momentum re-label at
  day clock joins the standing class veto; re-clocking is ancestry violation
  (Q-3/umbrella §6)."
- SRLVCX1 REOPENING_CONDITION (L136): "...the F-0 revival clause 'settlement
  schedule = new information layer' was granted in full and died at measured
  outcome; reopening needs a NEW payer + genuinely new information layer
  (order-book/depth PIT — BLOCKED today), not parameter rescue."

The class invokes, and discloses that it invokes, exactly the C1C2C3 escape
clause (new payer + new information layer) for its range-adjacent triggers
(VC1 edge, VC2 node). Under the amendment the court no longer rules on that
invocation as a gate; the controls (section 7) measure whether it holds, and
the rho labels (8.4) measure what it is worth.

---

## 9. FALSIFICATION + floors (gating)

All kills below are typed before any scored PnL (campaign §7 stop rules);
Stage-A TRAIN-window results are discovery, never publication evidence.

1. **COST_DOMINATED kill**: TRAIN-window NET expectancy (measured C1 spread at
   the arm's actual fill bars + DECLARED U2 commission + U3 slippage; U4/U5
   structurally zero) **≤ 0 at x1.5 stress** ⇒ `COST_DOMINATED` (campaign §4
   law; this subsumes the dispatch's x2.0 floor — x2.0 ≤ 0 is the terminal
   confirmation of the same kill). Gross-of-cost positivity with net
   negativity is the same kill, not a rescue.
2. **Floors 20/3/100** (per candidate, counted on executed entries; frozen
   BEFORE Stage-A, no post-hoc relaxation — RSM mirage law): **≥ 20 decisions
   on the full window, ≥ 3 per fold, ≥ 100 aggregate** — else typed
   `NOT_RUN_THIN`, permanent FLAT leg row. The P-29 ceiling-x-power doctrine
   applies: a candidate whose frozen conditions fire too rarely is a silent
   design kill; the feasibility bill must estimate decision counts per
   candidate BEFORE the battery (expected order: VA-edge fresh excursions
   with the low-acceptance condition — tens to hundreds per pair over 286
   weeks; LVN traverse-failures — similar; POC deviations ≥3 ATR60 inside VA
   with the P80 condition — the tightest filter; all estimates are
   HYPOTHESIS, to be measured at Stage-A admission, never tuned after).
3. **Placebo kill (r2 — the stronger arm governs)**: CTRL-B result per
   section 7b: arm ≤ **CTRL-B2** (full-window permutation) ensemble p90 ⇒
   `CONTROL_PLACEBO_NOT_DEGRADED` kill — the edge is not from the
   volume-by-price assignment at any granularity (within-day or cross-day);
   B2 cannot move the POC by ≥ 1 bin ⇒ `OBSERVABLE_NOT_IDENTIFIABLE` kill
   (the POC is the time-at-price mode; TIMEPROF-M1 relabel applies).
   **CTRL-B1 outcome is NOT a kill** (r2): B1 failure to degrade the arm
   while B2 does degrade it produces the informative label
   `EDGE_CROSSDAY_COMPONENT_ONLY` (the profile's information is carried by
   the day-level volume↔range component — still volume-by-price, disclosed
   in the identity tuple); B1 failure to move the POC produces
   `POC_CROSSDAY_DRIVEN`.
4. **Control kills**: CTRL-A (dwell-matched) or CTRL-C (clock-only) NET
   expectancy ≥ arm ⇒ kill (`CONTROL_OUTEARNED_ANCHOR` /
   `CONTROL_REPRODUCED_MECHANISM`). CTRL-D per 7d (uniform-weight earns more ⇒
   `PROXY_WEIGHTING_NEGATIVE` kill; uniform-weight ≈ real ⇒ TIMEPROF-M1
   relabel, disclosed everywhere).
5. **Ancestry label (NOT a kill, per amendment)**: rho > 0.20 vs any
   reconstructable dead neighbor (indicator or continuous, pooled per pair)
   ⇒ `RHO_TWIN_OF_<family>` redundancy label per section 8.4 — carried into
   the identity tuple, the trial ledger, the DSR/PBO denominators and the
   Stage-B complementarity measurement. It prices the multiple-testing
   narrative; it does not block the run.
6. **Expected-failure interpretation** (what a negative result MEANS about the
   payer hypothesis — preregistered so a failure cannot be re-narrated):
   - Arm negative AND the B2 placebo ensemble also flat/negative ⇒ the
     level-acceptance
     structure carries no extractable edge on these panels at this cost
     level; the payer hypothesis (resting liquidity at accepted levels) is
     unsupported AT M1 GRANULARITY WITH THIS PROXY — not disproved in
     general (notional volume, order-book depth, or other venues remain
     untested, and are BLOCKED today).
   - Arm negative but price-only reconstructions of the dead neighbors
     equally negative on the same window ⇒ consistent with the
     dead-MR-class prior; the diagnostic value is the added rho/measurement
     row, priced at ~zero cells.
   - Arm positive but CTRL-A/C/D equal or better ⇒ the clock/dwell did the
     work; the payer story is dead as told; no re-narration permitted
     (pre-registered here).
   - Arm positive, controls degraded (B2 ensemble clearly below the arm),
     rho ≤ 0.20 vs all
     neighbors ⇒ the observable did measurable work — the strongest
     diagnostic outcome this class can produce pre-holdout, and still NOT
     edge evidence until Stage-C test folds. If the arm passes B2 but not
     B1, add the `EDGE_CROSSDAY_COMPONENT_ONLY` reading (7b): the work sits
     in the day-level component of the profile.
   - All outcomes are HYPOTHESIS/NOT_RUN until produced; nothing in this
     spec asserts any of them has occurred.

---

## 10. DATA DEPENDENCIES — Lane D audit RESOLVED (r1)

Lane D's physical audit landed 2026-09-29 (`poolB/data_audit/
DATA_AUDIT_REPORT.md` + `audit_summary.json` + `panel_hashes_{EURUSD,GBPUSD,
USDJPY}.jsonl`; every one of the 12,552 files read, sha256-hashed and
lzma-decoded; overall digest of all 12,552 files
`d8d9807fbdad8f6ecd253382520a0c33907dd75ef26bb653a2df1c66e58690f3` — the
DATA_FREEZE input). Resolution of this spec's checklist, item by item:

1. **Bid+ask M1 `.bi5` coverage — RESOLVED, CLEAN**: 2,092 files per side
   per pair (12,552 total, 111,757,566 bytes), span 2021-01-01..2026-09-23;
   0 missing weekday files, 0 missing weekend files, 0 zero-byte, 0
   undecodable, 0 non-conforming names, every file exactly 1,440 records,
   0 OHLC-invariant violations, 0 negative-spread minutes across all ~6.02M
   minute-slots per pair; BID/ASK tradable masks identical. Campaign
   calendar end 2026-06-26 is covered with margin (the M1 tail beyond is
   out-of-calendar and unused). The single zero-tradable weekday
   (2021-01-01) is a genuine market closure handled by the spec's holiday
   rule (3.2 / 4.1).
2. **Volume-column nonzero fraction — RESOLVED**: weekday active fraction
   (vol > 0) 92.05–92.33% per pair; weekends ~6.7–6.9% carry-forward; first
   tradable minute 2021-01-03T22:00Z, last 2026-09-23T23:59Z. The 20-day
   profile windows are well-fed (~1,320 tradable minutes per weekday). The
   entry-window availability requirement (≥ 95% of London/NY entry-window
   minutes tradable) is RETAINED as a Stage-A admission check computed from
   the audited panels — the audit's hour-of-day vectors show London/NY is
   the measured peak-activity window, but the exact entry-window fraction
   is Stage-A arithmetic and is not asserted here.
3. **Volume-field behavior and semantics — RESOLVED, WITH THE MATERIAL r1
   CORRECTION**: the column is a size-weighted per-tick volume sum in
   Dukascopy units, NOT a tick count (only 2.49/3.50/3.71% of active
   minutes integral; float32 encodings of 0.09–2,985; 86–97% of positive
   values multiples of 0.01 at small sizes); absolute unit NOT_RUN —
   unverifiable from the candles. Activity diagnostics: corr with
   per-minute range 0.52–0.67; London/NY-core vs Asia-lull ratio
   1.97–3.17×; BID/ASK volume corr 0.72–0.91. Section 3 rewritten on this
   finding; all constructions verified unit-invariant (3.3). **Zero-volume
   runs that could fake LVNs are excluded by construction**: the tradable
   (vol > 0 both sides) mask is applied before binning, so a fake-LVN
   weekend/holiday run contributes no populated bins at all.
4. **Per-hour spread cells — RESOLVED**: C1 Friday-20:00 fill cells
   reproduce the COST_AUTHORITY_TABLE EXACTLY on all three pairs (EURUSD
   0.3/0.5, GBPUSD 0.8/1.3, USDJPY 0.5/0.9 pips p50/p90, n=286/286 each);
   liquid-hour spot checks (02:00/12:00/20:00Z) flat-tight on 20 evenly
   spaced weekdays; both quote sides present on every tradable minute
   (0 negative spreads panel-wide). **Cross-lane flag carried (immaterial
   here)**: Lane D found the table's C2 Mon–Thu roll cell was measured on
   the wrong hour (22–23Z instead of its declared (21:00,22:00]) and
   understates the declared window ~1.3–2× — a COST_AUTHORITY_TABLE
   correction is required before any roll-window-sensitive trial anywhere
   in the program is costed; this class has zero in-window fills by design
   (section 6).
5. **tzdata version pin — NOT Lane D scope; remains an engine freeze
   item**: the audit verified panel stamps are UTC and the NY-close/open
   boundary shifts with US DST exactly as expected (winter Sundays reopen
   22:00–22:05Z, the summer Sunday 21:00–21:04Z), but the IANA tzdata
   version for the session-mark rebuild (Europe/London, America/New_York)
   must be pinned in the engine manifest at Stage-A. This is the only
   remaining freeze action before the admission battery.
6. **Record-format confirmation — RESOLVED**: 24-byte big-endian
   `>u4 x5 + >f4` (sec-offset, open, close, low, high, volume_f32), price
   scales ÷1e5 (EURUSD, GBPUSD) / ÷1e3 (USDJPY), empirically pinned on all
   12,552 files, both sides (68-day structured sample per pair + full-panel
   invariant checks; the F0/PC ">5if" reading is confirmed, the 30-byte
   alternative refuted).

With items 1–4 and 6 resolved clean and 5 an engine-side freeze action, the
spec's status moves from CONDITIONAL_PENDING_DATA_AUDIT to
**CONDITIONAL_RESOLVED_AUDIT_CLEAN** — runnable at Stage-A under the
volume-semantics correction of section 3, carrying the C2 cross-lane flag
and the tzdata pin as its two open external items (neither blocks the
battery).

---

## 11. COMPLEMENTARITY NOTES (mechanism-level reasoning only — no data claims)

Which census families/rows would this class's loss/win behavior most
plausibly complement, reasoned from mechanism (all referenced rows are
HYPOTHESIS/NOT_RUN; nothing here is a measurement):

- **Trend / continuation legs (census A-TREND family, e.g. the EMA-stack,
  donchian and momentum rows across symbols; historically also the
  TRACKA2-P3B-style day-continuation shape)**: natural first complement. A
  level-acceptance fade book earns when price oscillates within accepted
  value and bleeds when price one-directionally migrates out of value —
  exactly the regime in which trend legs earn (migration = acceptance
  breakdown; a profile that splits or walks is the fade book's losing state).
  Mechanically: VC1/VC3 losses concentrate in persistent excursions; a trend
  leg's gains concentrate there. The volume-profile state itself (single
  peaked vs migrating/bimodal) is the shared regime variable — the portfolio
  policy's conflict rules (Stage-B) would see negative conditional
  co-movement by construction. Caveat: this class contains no join/continuation
  arm (deliberately, §1.1), so the complementarity must be funded by a
  separate trend leg, not by a sign-flip of this class's arms.
- **Event legs (F-EVENT family — the intervention/fix/auction rows, e.g.
  USDJPY-S56-style calendar-event books IF their PIT inputs are ever
  evidenced)**: event legs are conditioned on forced information-migration
  moments; this class's weekly-frozen profile is by construction stale on
  exactly those days (a post-event level structure the frozen profile does
  not know). The fade arms' worst hours should cluster on event migrations;
  an event leg active only in those windows is the mechanistic hedge. No
  event leg is currently admissible (PIT calendars unevidenced) — noted as
  the conditional complement.
- **Carry / rate-differential legs (census D family on USDJPY and the
  cross-pair carry rows)**: carry books hold days-to-weeks and earn
  slowly with their risk in fast unwinds; this class is flat every night
  with zero funding exposure. Different loss clocks (overnight gap/rollover
  vs intraday acceptance), near-zero mechanism overlap — a diversification
  complement by exposure geometry rather than by payer.
- **Session/calendar legs (C family)**: NOT complements — the highest
  correlation risk inside the slate. Any co-admitted session-conditioned leg
  shares this class's clock axis (CTRL-C exists because of that shared
  axis); Stage-B's P-20 arm-distinctness measurement must treat
  session-class legs and VOLPROF-M1 legs as suspect-adjacent until measured.
- **Other volume/tick-feature rows (the remaining pool-B rows and any future
  P_C re-adjudicated rows, e.g. value-area acceptance rows on AUDUSD/USDCAD
  if the ERP1 M1 re-fetch ever lands)**: same observable family — partial
  redundancy risk, not complementarity; they would enter the same
  complementarity measurement as same-family candidates.
- Scope note: the campaign's Stage-B does complementarity empirically
  (measured, on TRAIN folds only); this section is the mechanism-level prior
  that says WHICH measurements are worth running, nothing more.

---

## 12. VERDICT_SELF_ASSESSMENT (post-amendment: implementability + diagnostic value)

**Implementable?** Yes — audit-resolved as of r1:

- Every rule in sections 3–5 is a deterministic, compilable transform of
  panel columns (mid close, bid/ask quotes, BID-side vol_f32, tzdata
  calendar); no
  unevidenced PIT input remains (the three corpus rows that carried such
  inputs are not preregistered, §1.2).
- Cost authority: spread cells are MEASURED at the fill hours (C1 per-hour
  schedule, reproduced EXACTLY by Lane D); commission/slippage/swap are
  DECLARED with the swap structurally
  zero by hold design — the class is fully cost-RUNNABLE under the
  PROVISIONAL_PENDING_COST_AUTHORITY + NET_DEFAULT_COST labels today.
- Decision counts: plausibly above the 20/3/100 floors for VC1/VC2; VC3 is
  the tightest filter and the most likely `NOT_RUN_THIN` — measured at
  Stage-A, never tuned.
- **Lane D's audit landed CLEAN** (section 10): panels complete (12,552
  files, 0 gaps/0 anomalies, coverage 2021-01-01..2026-09-23), format
  pinned, C1 fill-hour cells reproduced exactly, volume semantics measured
  and corrected (size-weighted, unit-opaque) — absorbed with ZERO parameter
  changes (3.3). Remaining external items, neither blocking the battery:
  the engine-side tzdata pin and the program-wide C2 cross-lane correction.

**Worth diagnostic runs?** Yes — as the only observable surface on the M1
pairs with no dead ancestor that used it (F0 salvage note 1, with the
skeptic's M-3 correction): the class converts an unclaimed input axis into
falsifiable arms with cheap, decisive controls (placebo/dwell/clock/uniform
— all re-evaluations, zero extra scored cells), so the information value per
cell is high whether the outcome is positive or negative. **The Lane D r1
correction strengthens rather than weakens the case**: the observable
carries per-tick size, not just counts, so level acceptance is measured in
size-weighted activity — the quantity the payer story needs — within an
opaque unit that the unit-invariant constructions (3.3) never touch. The
expected
outcome, stated honestly under the program's own prior (every adjacent
skeleton on FX is dead; the corpus-level death rate is 11/11): NEGATIVE —
and a negative here is cheap and informative (section 9.6).

**Labels this class carries into every artifact** (informative, per
amendment): skeleton-adjacent to four dead FX families
(DT100-13-VWAPMR — same pair and bar size on EURUSD, DT100-15-BOLLFADE,
the TRACKA range-fade fence, DT100-83-FAILBRK); payer hypothesis unobserved;
observable is a one-pool **size-weighted volume sum in an unverifiable
Dukascopy unit** (section 3 limits: no notional semantics, no cross-pair
volume comparability, no count semantics); **VC3-POCMAG is
the designated likeliest casualty** (its anchor admits a price-only
substitute; its survival depends on CTRL-B/CTRL-D doing the work the
amendment no longer asks ancestry to do). This spec does not claim, and must
not be cited as claiming, novelty, edge, or any backtested result.

**Incidents recorded for the handoff** (data-label defects found while
drafting, verdict-neutral to this spec): I-1 — FAMILY_FAILURES DT100 FX rows
carry asset:"crypto" though the engine ran them on EURUSD/USDJPY 1m (checked:
arms.py FX section; also affects DT100-07/09/10/15/31); I-2 — the dead
neighbor's "VWAP" is a close-only running mean (volume-blind), closer to this
class's price-only controls than its observable; the F0 salvage note's "no
dead volume-profile ancestor" needed precisely the M-3 correction it got;
**I-3 (r1) — the observable's declared semantics were wrong until Lane D's
audit: the M1 volume column is a size-weighted per-tick volume sum in an
unverifiable Dukascopy unit, NOT a tick count (only 2.5–3.7% of active
minutes integral). Section 3 rewritten; the correction STRENGTHENS the
level-acceptance claim (per-tick size present) while tightening its limits
(no notional semantics, no cross-pair comparability); all constructions
verified unit-invariant (3.3) — zero parameter changes; spec status moved to
CONDITIONAL_RESOLVED_AUDIT_CLEAN.**

— END OF SPEC —
