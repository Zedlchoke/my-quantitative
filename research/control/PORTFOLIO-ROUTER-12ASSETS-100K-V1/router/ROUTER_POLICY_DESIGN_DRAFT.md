# ROUTER_POLICY_DESIGN_DRAFT — PORTFOLIO-ROUTER-12ASSETS-100K-V1 (Lane L4, 2026-09-28)

**Status:** PRE-GO research design draft. No cycle registered, no scored run,
no backtest executed in this lane (LANE_CHARTER law 1: DESIGN only). All
1,200 corpus ideas remain HYPOTHESIS/NOT_RUN. Nothing in this file is a PnL
claim; every number below is either (a) quoted from a file read this session
(path cited) or (b) a preregistration candidate to be frozen by A1/owner at
cycle registration — never a measured fact.

**Inputs read this session (authority for citations below):**
`LANE_CHARTER.md` (this program) ·
`research/control/FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/UNIFIED_STRATEGY.md` (full)
· `macro/CURRENCIES_CORE.md` · `macro/CURRENCIES_BLOC.md` ·
`research/wayfinder/MAP.md` lines 1278–1342 (JEV-REGIME-ROUTER-V2,
REGIME-STRATEGY-MAPPING-V1) and 1429–1460 (ERP1-TRACKA-COHORT-1 PIT seam) and
292–327 (BTC-H4-TWO-REGIME-V1) and 424+ (PHASE-STRATEGY-V1) ·
`research/wayfinder/LESSONS.md` Q-5/Q-7/Q-11/P-20/P-24/P-27/P-28/P-29 ·
`plans/PLAN_btc_h4_two_regime_v1.md` §1.5 (floors triplet) ·
`plans/DRAFT_regime_gated_combo_v1.md` (baseline battery precedent; the
dispatch's fallback — `plans/PLAN_daytrader_100_v1.md` has no §baselines
section, only a CTRL battery at lines 74–85) ·
`census/CENSUS_PROTOCOL.md` (families, verdict order, data cheat sheet) ·
`research/control/DATA-FOUNDATION-SIXSOURCE-V1/FINAL_REPORT.md` (PIT facts) ·
`research/control/DAYTRADER-100-V1/DIAGNOSTIC_REGIME_COMBO_2026-09-28.md`
(ALWAYS_ON_6 / ORACLE precedent) ·
`ancestry/FAMILY_FAILURES_DIGEST.tsv` (dead families).

---

## 0. Design constraints, verbatim from owner + dead ancestry (binding)

Owner constraints (dispatch packet, LANE_CHARTER §mission):

1. Policy = gated sleeves + shared state identifier + ON/OFF/FLAT table +
   capital allocation + cluster risk limits + execution + kill-switch.
2. State engine: MAX 3 PIT variables with economic basis; MAX 4 states with
   adequate preregistered sample floors; unseen/uncertain state ⇒ FLAT.
3. No 5-dimensional multi-branch matrices for plausible-sounding stories.
4. Gates locked from data available BEFORE the decision; no future PnL, no
   late-confirmed events, no regime labels drawn after seeing charts.
5. Gate learning/selection ONLY on training fold, applied unchanged to the
   next fold (nested walk-forward); every gate/threshold try counts in a
   trial ledger.
6. Sleeves individually pass mechanism + after-cost credibility BEFORE
   router assembly; a losing sleeve may not be "rescued" by a gate found
   from loss segments already seen.

Dead-ancestry laws this design must survive (each maps to a mechanism below):

| Ancestor | Terminal code | Binding lesson for this design |
|---|---|---|
| JEV-REGIME-ROUTER-V2 (MAP 1278–1308) | `JEV_NO_INCREMENTAL_VALUE` | Router lost to ALWAYS_ON and RANDOM on every cell; switching-cost attrition was decisive and monotonic under ×1.0/1.5/2.0 cost ladders. ⇒ weekly decision clock, preregistered anti-churn (min-dwell + episode merge), switching cost as a first-class reported line item, and the JEV law as PASS bar. |
| REGIME-STRATEGY-MAPPING-V1 (MAP 1310–1340) | `NO_REGIME_STRATEGY_INCREMENTAL_VALUE` | Floors 20/3/100; the owner-relaxed 10/2/50 comparison produced a thin-sample mirage (+2,529 at 1.0x, dead at 1.5x). ⇒ floors frozen pre-PnL, never relaxed post-PnL; margin-to-floor table published BEFORE any PnL. |
| PHASE-STRATEGY-V1 (MAP 424+) | `PHASE_STRATEGY_V1_NO_INCREMENTAL_VALUE` | Price-derived phase labels on one asset add nothing. ⇒ state variables must be exogenous published macro series, not functions of the traded tape. |
| REGIME-GATED-COMBO-V1 (charter; `plans/DRAFT_regime_gated_combo_v1.md`) | exposed reading: GATED loses all baselines; pending owner | Gate variables were price/funding-derived (funding z, RV percentile, \|r\|/vol, rolling corr) on dead legs. ⇒ our state engine uses none of those observables; sleeves must be credible BEFORE gating (that draft gated 6 individually-dead anchors — the exact anti-pattern). |
| BTC-H4-TWO-REGIME-V1 (MAP 292–327; plan §1.5) | `BTC_H4_TWO_REGIME_V1_NO_ELIGIBLE_PROPOSAL` | Died on preregistered floors 20/3/100 with 5/6/5 episodes. ⇒ a state census (episodes, dwell, margin-to-floor) runs PRE-PnL; failure ⇒ NOT_RUN_THIN ⇒ permanent FLAT rows, first-class outcome. |
| ERP1-TRACKA-COHORT-1 (MAP 1429–1447) | REJECT_ALL | Whole-day-mode lookahead PIT seam killed the "edge" (PF 1.03–1.05 clean vs leaky twin). ⇒ decision-time lock is publication-timestamp-based, with a T−1 rule and machine-checkable staleness (see §3.4). |
| FXFV3-A6 (digest) | SCIENTIFIC_REJECTION | "Realized-vol regime-gated policy-rate-differential carry" — the nearest dead forex router-class family. ⇒ representation-rho battery (§3.6) and per-sleeve F-0 court (P-27) are mandatory; our V2 (VIX index percentile) is deliberately NOT the traded asset's own realized vol. |

Standing workspace lessons wired in: Q-5 (grade on worst fill; size-collapse is
information), Q-7 (clock-only shadow for any conditioning), Q-11 (a null is
only a null if it moves the signal), P-20 (a control/state sharing its source
with the arm is tautological — must be measured, fail-closed), P-24 (controls
declared before measurement; kills compound), P-27 (F-0 mechanism-class court
before rho and before PnL; measured conditional cost ceiling), P-28 (inverted
control is the cheapest kill), P-29 (representation-rho of gate states vs
dead ancestors, bar 0.20, before granting any "new information layer").

---

## 1. Architecture — separation of powers

```
[Layer A] SLEEVES (family × cluster execution units)
          own entry/exit logic + own coupling gates + own event discipline
          admission: mechanism + PIT + after-cost credibility, individually
          DEFAULT: FLAT (a slot may stay empty — SLOT_LEFT_EMPTY, P-27)
    ↑ enabled/disabled per week by
[Layer B] ROUTER (this document)
          state engine (3 PIT vars → ≤4 states, weekly, abstain⇒FLAT)
          ON/OFF/FLAT table (state × cluster → families)
          capital allocation + cluster risk caps
          execution guardrails + typed kill-switches
    ↑ constrained by
[Layer C] EVALUATION PROTOCOL (Deliverable 2)
          nested walk-forward, trial ledger, baseline battery, DSR/PBO
```

Golden rule inherited from UNIFIED_STRATEGY §4 (layer 2): **the router only
decides WHICH family door is open per cluster; the coupling condition of each
idea (per census `mechanism`/`signal_available_at` columns) decides the entry
inside the door. The router cannot bypass a sleeve-internal coupling gate.**
Conversely, a sleeve may not reach around the router's OFF: an OFF family has
zero entries that week.

---

## 2. Sleeve layer — how a sleeve earns a slot

### 2.1 Definition

A sleeve = one canonical census family (A-TREND, B-MEANREV, C-BREAKOUT,
D-CARRY_TERM, E-SESSION, F-EVENT, G-XASSET, H-POSITIONING, I-STATARB,
J-REGIME_OPT — CENSUS_PROTOCOL §2) instantiated on ONE cluster, taking the
per-symbol exemplar rows (census `exemplar_ref`/mech_key dedup) as its
implementation hypotheses. Bounded slate: at most 2 families per cluster
admitted initially (≤10 sleeves), to keep the trial ledger and PBO
interpretation honest; expansion is a new preregistration, not a mid-run edit.

### 2.2 Admission gates (all must pass BEFORE router assembly; order frozen)

1. **Census admission:** every constituent idea row is `DISTINCT_TESTABLE`
   or an in-file exemplar of such; rows verdicted VARIANT_OR_DUPLICATE against
   a dead family do not enter (P-27 F-0 court: "adding a gate to a dead law
   is a variant, not a mechanism").
2. **F-0 mechanism-class court:** payer named + plausible (census
   `payer_or_flow` ≠ UNCLEAR), skeleton distinct from every
   `ancestry_hits` entry; skeleton/payer/information tests per P-27.
3. **PIT battery:** `signal_available_at` is machine-decidable; the sleeve's
   decision inputs are locked to data published before the weekly decision
   time (§3.4 T−1 rule applies to sleeves too); a truncation-replay check
   (ERP1-TRACKB M-1..M-5 precedent) is green.
4. **After-cost credibility:** measured cost ceiling on the conditional
   fill-hour distribution of the sleeve's own book (P-27: declared priors are
   hypotheses — Q-8); the sleeve's training-fold expectancy must clear its
   ×2.0 all-in cost bill BEFORE any router assembly. Sleeves failing here are
   SLOT_LEFT_EMPTY. Vehicles/costs come from L1/L3
   (`datacost/DATA_COST_MATRIX_DRAFT.md`, `cost/COST_ACCOUNTING_SPEC.md`);
   UNMEASURED stacks are treated at the WORST declared band (Q-5), never an
   optimistic fill.
5. **Sample floors:** enough independent entries/episodes on the training
   fold set (fold-clipped), reported with margin-to-floor.
6. **No-loss-segment rescue (owner constraint 6):** a sleeve that fails 2–5
   stays failed. Any proposed "gate" whose threshold was informed by the
   sleeve's already-seen loss segments is rejected at design review: all
   router thresholds in §3 are functions of the MACRO SERIES ONLY
   (percentiles of V1/V2/V3, half-hike rounding), none of sleeve PnL. This is
   a structural guarantee, not a promise.

### 2.3 FLAT default

A cluster with no admitted sleeve runs FLAT. A sleeve admits no entries
while its router cell says OFF or the state is FLAT/abstain (except the
always-eligible class, §4). Sleeve-level veto conditions (its own coupling
gates, spread guardrail, blackout calendar) can force FLAT at any time
independently of the router.

### 2.4 Family exemplars per cluster (from census class + UNIFIED_STRATEGY §10)

| Cluster | Symbols | Most likely family candidates (final set from census merge) |
|---|---|---|
| USD-bloc | EURUSD GBPUSD USDJPY USDCHF | D-CARRY_TERM (differential carry toward USD), A-TREND (policy-divergence trend), E-SESSION (London/NY execution edges — always-eligible class) |
| Commodity-FX | USDCAD AUDUSD NZDUSD | D-CARRY_TERM (differential + funding legs), F-EVENT (net-surprise drift), E-SESSION (always-eligible) |
| Precious | XAUUSD XAGUSD | A-TREND (real-yield-conditioned trend), I-STATARB (GSR ratio / XAG squeeze 3-gate, market-neutral inside cluster) |
| Energy | BRENT WTI | D-CARRY_TERM (term-structure/backwardation tilt), F-EVENT (EIA composite surprise; weekend-gap continuation) |
| NATGAS | NATGAS | F-EVENT (EIA NG surprise drift), B-MEANREV (storage×weather dispatcher) — always-eligible class (weather/storage drivers are state-orthogonal; UNIFIED §9 NATGAS row) |

J-REGIME_OPT ideas are NOT admitted as sleeves (they are router-class by
construction and inherit the dead-router ancestry directly; any J-row
admission would need its own cycle).

---

## 3. State engine — 3 PIT variables, 4 states, abstain ⇒ FLAT

### 3.1 Compression of the 6-layer architecture (how ~60 coupling rules collapse)

UNIFIED_STRATEGY layer 1 defined five axes (R, K, E, I, V) and
CURRENCIES_CORE/BLOC defined ~60 coupling rules. Compression map (this is the
whole justification of variable choice; anything not listed here is DEMOTED
to sleeve-internal gates or dropped):

| Source axis / rules | Disposition |
|---|---|
| R — rate/hike regime (TIPS Δ/week, priced hikes, differential direction; rules C01, C06, C07, C08, C11, C18, C23, BLOC rules 1/13/15/28) | **Variable V1** (policy momentum from EFFR). TIPS real-yield slope deliberately NOT used: PIT_UNPROVEN per census cheat sheet AND the dead FXFV8-A5 family used inflation-compensation term-structure dispersion as a regime gate — choosing TIPS would walk representation-rho straight into a dead observable (P-29). Policy direction drives nominal AND real yields in hiking cycles (CURRENCIES_CORE §1.1, §5.4), so EFFR momentum is the evidenced PIT proxy for the R axis. |
| K/V — risk + volatility regimes (VIX level/term, carry-unwind, haven hierarchy; rules C03, C20, C21, C26, BLOC rules 11/21) | **Variable V2** (VIX level percentile). The single most-wired cross-asset observable in the corpus (C03/C20/C21, BLOC 11/21, kill-switch in UNIFIED §6). |
| E — energy/geopolitical regime (war premium, backwardation, headline intensity; rules C04, C05, C11, C22, BLOC rules 2/3/27) | **Variable V3** (Brent–WTI spread percentile). UNIFIED §3-E names this spread as THE war-premium gauge ($3–6 normal, $11–14 war). Headline-intensity feeds are `MISSING` (census cheat sheet) so they cannot be a state variable; the spread is their PIT-clean tradable shadow. |
| I — intervention map (JPY warning track 158–160, SNB sight deposits ≥ +5bn CHF WoW; rules C02, C16, C19, BLOC 20–23) | DEMOTED to sleeve-internal hard gates on the USDJPY/USDCHF sleeves. Rationale: MOF intervention scale is disclosed ex-post monthly (the "classic lookahead bias" CURRENCIES_CORE §4.2 explicitly warns about); SNB sight deposits are PIT_UNPROVEN until L1 gates them. A state built on late-confirmed events would violate owner constraint 4. Sleeves carrying these gates run them at their own PIT risk; if a sleeve's admission depended on an unevidenced intervention feed, the sleeve is not admitted. |

Net: 5 axes → 3 variables; intervention → sleeves; per-cluster V-regime
percentiles → vol-targeted sizing (§5), not state.

### 3.2 The three variables (MAX 3 — exactly 3 chosen)

**V1 — Policy momentum (rates axis).** `PM = EFFR(t) − EFFR(t−63 business days)`,
in bp (63bd ≈ one quarter). Source: NY Fed EFFR daily, status
AVAILABLE_VALIDATED per sixsource FINAL_REPORT row 6b ("effectiveDate +
revisionIndicator machine-served", publication-day granularity) — the ONE
evidenced macro daily in the repo today. Bands: TIGHT ≥ +12.5bp; EASE ≤
−12.5bp; else MID. 12.5bp = half a standard 25bp hike per quarter — a
rounding-level preregistration, not a tuned threshold.

**V2 — Risk/vol stress (risk axis).** `RV = percentile of latest usable VIX
close within the trailing 252 trading days of usable VIX closes` (level, not
term structure — term-structure futures history is a separate PIT gate, see
kill-switch KS1 fallback). Source: VIXCLS (FRED/CBOE), currently
PUBLIC_UNEVIDENCED per census cheat sheet → requires L1 PIT gate; the cheap
evidence path is ALFRED vintage stamps (first-available timestamps), recorded
in `datacost/PIT_SOURCE_TABLE.md`. Band: STRESS ≥ p80; else CALM.

**V3 — Energy term premium (energy/term axis).** `ES = percentile of
(Brent spot − WTI spot) within its trailing 252 trading days`. Source:
EIA Europe Brent / WTI spot daily (FRED DCOILBRENTEU / DCOILWTW) or the
panels L1 acquires, whichever passes its PIT gate first (ALFRED vintages for
the FRED path). This is computed from EXOGENOUS spot series, NOT from our
energy CFD execution quotes, to keep the state variable decoupled from the
energy sleeves' own book (P-20 hygiene; residual overlap measured, §3.6).
Band: WAR ≥ p85; else BASE.

**If the PIT gate fails for V2 or V3, the state engine is NOT_RUN — no
post-hoc variable substitution** (a substitute variable chosen after seeing
which one is available is a redesign and needs a new preregistration).

### 3.3 The four states — pure function, priority ladder, weekly clock

State(t) = first match, evaluated in this frozen priority order:

```text
1. WAR_ENERGY     if V3(t) = WAR                      (energy supply-premium regime)
2. RISK_STRESS    elif V2(t) = STRESS                 (cross-asset stress / carry-unwind risk)
3. TIGHTENING     elif V1(t) = TIGHT                  (hawkish policy regime)
4. EASING         elif V1(t) = EASE                   (dovish policy regime)
5. ABSTAIN        else (V1 = MID with V2 CALM and V3 BASE)  ⇒ macro-conditioned families FLAT
```

Priority justification (economic, preregistered): an energy supply premium is
the rarest regime and re-prices an entire cluster plus commodity-FX terms of
trade regardless of the policy cycle (C22, C04; UNIFIED §4 WAR_ON rows and
§9 worked example) — it wins ties. Cross-asset stress is the fastest
contagion channel (carry-unwind cascades, C03/C20; UNIFIED §6 kill-switch
wiring) — second. Policy direction is the slow background — third. The
Sep-2026 snapshot (CURRENCIES_CORE §0: hikes + oil war + expanded vol all
live simultaneously) maps to WAR_ENERGY; the rate-channel nuances that
snapshot also exhibits (gold not a haven under hiking) are handled INSIDE the
precious sleeve's coupling gates, not by a 5th state.

The ladder yields exactly 4 tradeable states + one explicit ABSTAIN branch
(owner constraint: "unseen/uncertain state ⇒ FLAT"). MID policy is BY DESIGN
uncertain — between cycles the policy axis carries no conditioning
information the sleeves' own gates don't have, and pretending otherwise is
how RGC-style gates reduce trade count without value.

Anti-churn (preregistered, each counts in the trial ledger):
- **Min-dwell:** a candidate state must hold for 2 consecutive weekly
  observations before it becomes effective (state effective at the 2nd
  observation).
- **Episode merge:** adjacent same-state runs separated by < 4 weeks merge
  into one episode (episode census convention, BTC-H4-TWO-REGIME §1.2-style).
- **Max flip guard:** see KS3 (kill-switch), which treats excess flipping as
  detector failure, not as information.

### 3.4 Decision clock and PIT lock (ERP track-a seam, closed)

- **Decision time:** Friday 17:00 ET. **Usable data = published ≤ Thursday
  close buffers**: EFFR through Thursday (Friday's EFFR prints Monday ~09:00
  ET — NY Fed next-business-day publication), VIX Thursday close (Friday's
  VIX print lands after CBOE close 16:15 ET, inside the decision hour), EIA
  spot through Thursday. This uniform **T−1 rule** is machine-checkable and
  errs conservative.
- **Execution:** next Monday, in-session windows (§6). Decision-to-trade
  delay ≤ 1 trading week by construction.
- **Staleness fail-closed:** V1 stale > 5 business days, or V2/V3 stale
  > 2 business days, or any panel missing at decision time ⇒ that variable
  UNAVAILABLE ⇒ state not computable ⇒ ABSTAIN (FLAT for macro families;
  always-eligible class unaffected). Never carry the last known state
  forward.
- **No late-confirmed events:** intervention disclosures (MOF monthly), COT
  (Fri 15:30 ET, Tuesday data), GDT, SNB weekly deposits are NEVER state
  inputs — they live only inside sleeves and only behind their own PIT gates.
- **No chart-drawn labels:** state is a pure function of V1/V2/V3 series
  values at T−1; there is no discretionary label step anywhere in the
  pipeline (the PSV1/JEV failure surface).

### 3.5 Sample floors — preregistered, never relaxed after any PnL

Operative floors (weekly-clock adaptation of the PSV1 §4.3 triplet
`≥20 merged episodes/state/cell total; ≥3 raw episodes/state/outer fold;
≥100 state-true decision bars/state/outer fold` —
`plans/PLAN_btc_h4_two_regime_v1.md` §1.5):

```text
F1: ≥ 10 merged independent episodes / state / full fold set (total)
F2: ≥  2 fold-clipped raw episodes / state / outer fold
F3: ≥ 26 state-true decision weeks / state / outer fold
```

Justification for the adaptation (and the honesty it demands): the ancestral
triplet was calibrated on H4 decision bars of a single asset (a 100-bar
floor ≈ 16.7 days of H4 opportunities; 6.7y of H4 ≈ 11,700 bars). A weekly
macro clock has 5.25× fewer decision points per year than a DAILY clock and
~42× fewer than H4; a literal "≥100 state-true weeks per state per outer
fold" is structurally impossible for any 4-state partition on folds shorter
than ~8 years (100 weeks would require >64% occupancy per state per fold).
Macro policy episodes are months-long by nature (EFFR hiking phases 2022–23,
cuts 2024–25 — CURRENCIES_CORE §0/§5.4), so the binding power constraint is
EPISODES, not weeks; evaluation power is pooled across 5 clusters × multiple
sleeves per state-week rather than resting on one asset as in the ancestor.
F1=10 is the floor the RSM postmortem flags as mirage territory
(owner-relaxed 10/2/50 → "+2,529 at 1.0x dies at 1.5x", MAP 1326–1328):
therefore, for any state passing F1–F3 with < 20 merged episodes, the ×1.5/×2
cost stress and drop-one battery are BINDING pass conditions (Deliverable 2
§7), and the margin-to-floor table must publish the shortfall to the
ancestral 20-episode bar explicitly.

**State census runs PRE-PnL** (episode counts, dwell distribution, transition
matrix, occupancy, margin-to-floor per state, on the training fold set):
any state failing any floor ⇒ that state's table rows are NOT_RUN_THIN ⇒
permanent FLAT rows for the remainder of the cycle. No relaxation after any
PnL (owner law, charter). If ≥2 of 4 states fail floors, the router
degenerates toward the always-eligible book and the cycle closes
`ROUTER_STATES_THIN` — a first-class outcome, not a design emergency.

### 3.6 Representation-rho and tautology battery (P-29 / P-20, pre-PnL)

Before any PnL, measure (training data only):

1. **Representation-rho vs dead ancestors (bar ≤ 0.20, immovable — RGC §3
   precedent):** the derived state INDICATOR series vs (a) RGC G2's vol
   percentile observable (30d RV percentile of BTC/EURUSD — computable on
   the EURUSD repo panel over the overlap window; our V2 is VIX index
   252d percentile, a different series in the same class, so this rho MUST
   be measured, not assumed small); (b) FXFV3-A6's RV-gated differential
   conditioning class (same test); (c) two-regime drawdown-hysteresis
   constants applied to each traded symbol (price-derived ancestor — must
   stay decorrelated to prove V1/V2/V3 are not laundering tape state);
   (d) FXFV8-A5's inflation-compensation slope z252 (only if L1 gates TIPS —
   otherwise NOT_RUN, disclosed). Any rho > 0.20 kills the offending
   variable's state layer (P-29 law: the gate lives only when its state
   escapes the dead ancestor's representation).
2. **Arm-vs-state distinctness (P-20):** for every sleeve, measure
   representation overlap between the router state variable(s) gating it and
   the sleeve's own conditioning observable (e.g., V3 vs the energy sleeve's
   backwardation gate; V1 vs the D-carry sleeve's differential series).
   Overlap is MEASURED (`books_distinct` analogue: fraction of decision
   weeks where router and sleeve would disagree), fail-closed `None` →
   NOT_RUN when unmeasurable, never an inferred PASS. A sleeve whose own
   gate replicates the router state is redundant with the router and its
   router-cell stays OFF (dedup at assembly).

---

## 4. ON/OFF/FLAT table — state × cluster → families

Two row classes (owner constraint: coupling gates stay inside sleeves):

- **Macro-conditioned rows** — governed by the state.
- **Always-eligible rows** — families whose census mechanism is calendar/
  storage/weather-driven (E-SESSION, I-STATARB hedged inside a cluster,
  NATGAS F/B families). They run per their OWN sleeve gates in every state
  INCLUDING ABSTAIN (turning off a session edge because policy is mid-course
  has no economic story and is exactly the "reduces trades without value"
  failure). The router-vs-baseline comparison must therefore isolate the
  macro-gated book via attribution (Deliverable 2 §6).

Preregistered table (families listed are CANDIDATE classes per census;
final ON set = admitted sleeves from §2):

| State | USD-bloc | Commodity-FX | Precious | Energy | NATGAS (always-elig.) |
|---|---|---|---|---|---|
| **WAR_ENERGY** | D ON (toward USD: oil→CPI→hawkish channel, C22), A ON | D ON (differential + trade-war; ToT-pure OFF — BLOC rule 2/25), F ON | OFF (rate channel dominates haven under supply shock — C01/C21 fade branch) | D ON (backwardation long-tilt), F ON (EIA/gap families; headline fade only with sleeve-internal multi-source confirm); B OFF | F/B per sleeve gates |
| **RISK_STRESS** | D OFF (carry unwind risk, C03/C20), G ON if an admitted haven-basket sleeve exists, E per always-elig. | OFF (risk beta dies first — BLOC 5.4), F ON | OFF (stress under unknown policy direction is not gold's regime — UNIFIED §3 K-axis finding) | OFF except F | F/B per sleeve gates |
| **TIGHTENING** | D ON (differential toward USD), A ON (policy-divergence trend); B OFF | D ON (funding legs), F ON; ToT families OFF (rate regime overrides ToT — UNIFIED §4) | A OFF / short-bias only via sleeve's two-factor matrix; I ON only with its 3-gate confirm | D ON, F ON | F/B per sleeve gates |
| **EASING** | A ON (dollar-weak trend), B ON (fade USD extremes), D OFF | A ON (ToT families resume), D ON toward bloc, F ON | A ON (trend-long precious, real yields falling — mirror row, UNIFIED §4) | A ON, D ON | F/B per sleeve gates |
| **ABSTAIN (MID+CALM+BASE) or UNSEEN/STALE** | macro rows FLAT; E ON | macro rows FLAT; E ON | macro rows FLAT | macro rows FLAT | F/B per sleeve gates |

Symmetry note: TIGHTENING and EASING rows are economic mirror images
(UNIFIED §4 "EASING + PEACE_BASELINE" row) — the design does not know which
side, if either, has value; the protocol falsifies both.

---

## 5. Capital allocation & risk limits ($100,000 simulated account)

- **Per-trade risk:** 0.25–0.5% of equity per position (owner verbatim;
  preregister default 0.375% midpoint, count 1 trial).
- **Equal risk budget per enabled sleeve:** each enabled macro-conditioned
  sleeve receives an equal share of the cluster's risk budget; no performance-
  weighted sizing (no feedback from realized PnL into allocation — that would
  be a hidden optimizer, Q-5).
- **Cluster caps (one-way total portfolio risk):** any cluster ≤ 2%;
  USD-bloc counts as ONE exposure (4 highly-correlated symbols — UNIFIED
  layer 0); NATGAS ≤ 1% AND tail-sized (size off p95 vol, not mean vol —
  the widow-maker paradox, UNIFIED §6).
- **Portfolio aggregate cap:** total one-way open risk ≤ 6% (three full
  cluster caps); preregistered, count 1 trial.
- **Vol-targeted sizing:** position size set so (stop distance × position)
  = per-trade risk budget, with stop = ATR-based (never static round
  numbers — UNIFIED §6); instrument vol estimated from the sleeve's panel
  with the same T−1 lock.
- **Leverage/margin:** no leverage beyond broker margin rules; margin
  utilization ≤ 30% of equity at all times (preregistered, 1 trial). FX
  conversion and margin accounting per L3 `COST_ACCOUNTING_SPEC.md`
  (UNMEASURED = worst declared band).
- **Switching:** risk budgets reallocate only at the weekly decision point;
  no intra-week state-driven resizing (kill-switches excepted).

---

## 6. Execution & guardrails

- **Decision:** Friday 17:00 ET (state from T−1 published data, §3.4).
- **Execution window:** Monday 08:00–17:00 UTC, subject to per-cluster
  session filters: majors London+NY overlap; AUD/NZD Asia session;
  XAU/XAG London AM + COMEX open; energy NY morning (UNIFIED §7). No new
  entries Friday close; avoid 21:00–23:00 UTC rollover.
- **Spread guardrail:** skip entry if live spread > 2× the measured p50 for
  that instrument (sixsource FX cost band p50 0.1–0.6 pip in ONE 02Z bucket —
  FINAL_REPORT row 1 — and L3's stack for metals/energy; UNMEASURED ⇒ worst
  declared band, Q-8/Q-5).
- **Event blackouts (calendar, typed):** CB meetings (FOMC/ECB/BoE/BoJ/SNB/
  RBA/RBNZ/BoC): no NEW entries 24h before → 2h after; top-tier data (NFP,
  CPI US + quote-country, PCE): macro-family size halved, event families
  (F) exempt by design; energy: OPEC+ meetings, EIA Wed (crude) / Thu (gas)
  10:30 ET, monthly EIA/OPEC/IEA reports — F-family sleeves own these
  windows (that IS their mechanism), others blackout. Calendar sources and
  their PIT evidence are L1 scope.
- **Weekend gap policy:** energy + precious carry no full size through
  weekends in WAR_ENERGY (half size or flat per family spec; UNIFIED §7 —
  WTI releases 48h of event risk in one tick).
- **Futures roll:** roll calendar + roll cost booked per L3; term-structure
  carry is an explicit sleeve (D family), not a hidden subsidy.

## 7. Kill-switches (typed; each fires mechanically, logged, and is reported)

| ID | Trigger | Action |
|---|---|---|
| KS1 | Carry unwind: VIX term inversion (M1>M3) — PRIMARY only if the futures-history PIT gate passes; else preregistered fallback `VIX ≥ p95(252d)` AND `ΔVIX(5d) ≥ +6 points` (declared BEFORE any run; choice by data availability only, never by performance) | Exit ALL D-family positions next session; 48h re-entry lock on D family (UNIFIED §6 verbatim intent) |
| KS2 | Cluster drawdown > 4% within the current state EPISODE | That cluster FLAT until the state changes (UNIFIED §6) |
| KS3 | Whipsaw: > 4 completed state flips in trailing 8 weeks | Whole system FLAT for 4 weeks; state-engine audit incident logged; auto-resume only if no variable STALE (UNIFIED §8.2) |
| KS4 | Unseen/STALE state (§3.4 staleness limits) | Macro families FLAT; always-eligible class unaffected |
| KS5 | Account equity drawdown > 10% from high-water mark | All flat; terminal review by owner (out of research hands) |
| KS6 | Intervention events (JPY warning-track breach, confirmed MOF/SNB action) | Sleeve-level (NOT router): flat the affected symbol 48h — lives inside USDJPY/USDCHF sleeves with their own PIT-evidenced triggers; unevidenced trigger ⇒ sleeve not admitted with that gate (§3.1) |

---

## 8. How this differs in mechanism class from JEV / RSM / PSV1 / RGC (the A7 novelty axis)

1. **State source class:** JEV/PSV1/RGC states were LLM-classifier labels or
   functions of the traded tape (price drawdown-hysteresis, funding z,
   RV percentile of the traded asset, rolling corr — MAP 1278–1342, RGC §2).
   Our states are pure functions of three EXOGENOUS published macro series
   with machine-served publication timestamps (EFFR evidenced; VIX/Brent–WTI
   via ALFRED-vintage PIT gates). No classifier, no judgment step, no tape
   feedback. P-29 representation-rho vs each dead observable is measured
   pre-PnL, bar 0.20.
2. **Asset universe:** all four ancestors ran BTC/ETH/SPY single-asset-class
   legs. This program is a 12-asset FX+metals+energy portfolio with
   cluster-level risk architecture — a universe the dead router classes never
   touched (energy/metals have no router ancestry in
   FAMILY_FAILURES_DIGEST.tsv).
3. **Sleeve falsification first:** RGC gated six individually-dead anchors
   ("Mọi số chân kế thừa verdict CELL_FAIL gốc" — RGC §1); JEV/RSM gated
   already-net-negative cells. Here NO sleeve enters the router without its
   own mechanism + after-cost credibility on training folds (§2.2), and a
   losing sleeve cannot be rescued by loss-segment-derived gates (structural:
   router thresholds are functions of macro series only). The router question
   is "does macro state add value ON TOP of credible sleeves", which is the
   question the ancestors never actually isolated.
4. **Switching economics:** weekly clock + min-dwell + episode merge +
  switching-cost reporting + the ×1.0/1.5/2.0 attrition ladder reproduce the
   exact dimension that killed JEV, as a preregistered measurement rather
   than a postmortem.
5. **Abstain by design:** MID-policy weeks are FLAT for macro families —
   a forced-choice 4-phase provider (JEV V2's design) is explicitly NOT
   rebuilt; uncertainty is expressed as no exposure, not as a guessed label.

What is NOT novel (disclosed, so A7 cannot "discover" it): conditional
allocation as an identity is the RGC mechanism ("conditional allocation …
phân bổ notional giữa các chân đã rescore", RGC §0); the novel axes are
1–4 above. Prior probability stays negative: five router-class ancestors
died; this design's value claim is measurable only against the battery in
Deliverable 2.

---

## 9. Honest limitations (preregistered)

- Every threshold (12.5bp, p80, p85, 252d windows, dwell 2w, merge 4w, caps)
  is a preregistration candidate — numbers chosen for economic roundness and
  clock-scale reasons BEFORE any PnL exists; they are starting points for the
  frozen grid, not knowledge.
- State occupancy risk is the #1 kill point: policy-direction states are
  structurally episode-poor (§3.5); the design will likely lose ≥1 state to
  floors, and that is the system working.
- V2/V3 PIT gates are unproven until L1 evidences them; the engine has zero
  evidenced fallback beyond FLAT (deliberate).
- The always-eligible class dilutes measured router effect; attribution must
  separate the books or the PASS bar is unmeasurable.
- Backtest span is bounded by the shortest panel (energy PUBLIC_UNEVIDENCED
  today); if the intersection window cannot host ≥6 outer folds, the program
  closes NOT_RUN_INSUFFICIENT_CALENDAR rather than shrinking folds.
- Single-decision-clock (weekly) means the router cannot express intraweek
  regime turns; intraweek risk is delegated to kill-switches and sleeve
  stops, not prediction.

— End ROUTER_POLICY_DESIGN_DRAFT. Lane L4, read-only session, no git writes.
