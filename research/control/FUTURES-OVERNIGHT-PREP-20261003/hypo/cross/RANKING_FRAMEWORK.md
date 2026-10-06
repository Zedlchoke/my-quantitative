# RANKING_FRAMEWORK — outcome-blind consolidation rubric for ALL families (P1-CROSS)

- Task: **FUTURES-OVERNIGHT-PREP-20261003**, lane **P1-CROSS**. Generated UTC
  2026-10-04. Worktree @ `72c9bc5b1d94b812044a9bd21768c53b4d378436`
  (re-measured; no tracked drift), branch `prep/futures-behavior-10syms-20261002`.
- Purpose: ONE rubric consolidating every hypothesis family in the program —
  single-symbol families from returned sibling lanes P1-ESNQ (8 families,
  `hypo/es_nq/`) and P1-6E6B (6 families / 10 symbol legs, `hypo/6e_6b/`),
  the cross-symbol diagnostics of this lane (`CROSS_HYPOTHESES.md`), and —
  PENDING — the concurrent lanes P1-6J6A and P1-COMM (not read; synthesis
  lane appends them with this rubric).
- **Outcome-blind by construction: NO return statistic, no PnL, no
  expectancy, no hit-rate, no backtest output exists or enters any
  dimension.** Scores describe the QUALITY OF THE PRE-REGISTRATION PACKAGE
  ONLY. Ranking is a mechanical function of evidence/registration facts.
- Inputs are ARTIFACTS ONLY: the two sibling hypothesis docs + RANKING_INPUTs
  (sha256 in `cross_hypotheses.json`), the dossiers/addenda/court/playbooks
  they cite, and the batch-1 fact files. Nothing was measured this lane.

---

## 1. The rubric (anchors fixed BEFORE any application)

Five dimensions, integer 0-3 each, **summed to 0-15**. Every anchor is a
mechanical test against committed artifacts — no judgment call after the
anchors are agreed.

### D1 — Evidence-coverage (does committed, symbol-specific anatomy constrain the mechanism?)
- **3** = the family's constraining anatomy is measured ON THE TARGET
  SYMBOL(S), spans ≥2 eras or the full multi-era panel, and lives in a
  committed artifact re-verified at 72c9bc5b.
- **2** = committed and symbol-specific but (a) confined to a single
  era/window, or (b) computed on a series with a known defect
  (pre-recovery NQ aggregates), or (c) the family-specific interaction is
  NOT_RUN while only adjacent anatomy exists, or (d) a same-kind
  prerequisite cell is missing (cross diagnostics).
- **1** = only indirect evidence (adjacent-window anatomy, calendar-plus-
  analogy, machinery specifications without pooled output).
- **0** = no artifact-backed anatomy.

### D2 — Mechanism-specificity (is the causal story pinned to actors, timing, symbol/venue?)
- **3** = named microstructure actors + exact timing + a symbol/venue/era
  reason, AND a family-specific negative control that shows NOTHING if the
  mechanism is fake. (For FX families: additionally a mechanism class the
  dead FOREX-FREE-V1/V2 corpus could NOT represent — court §b
  distinguishability.)
- **2** = mechanism and timing named, but actors vague, or the measured
  anatomy (daily/horizon aggregates, 21d-vol descriptives, other-window
  ratios) maps to the session-level claim only by INFERENCE; or partially
  overlapping a dead family's signal class.
- **1** = generic behavioral story, no distinguishing observable.
- **0** = no distinct falsifiable content.

### D3 — Falsifiability (are the kills pre-registered, and is a court-method power statement available?)
- **3** = pre-registered mechanism-level kills (era instability, placebo
  reproduction, anatomy pre-gate, concentration window, delay-pair
  adjudication where applicable) AND a court-method power statement at
  documented realistic n with **MDE ≤ modeled cost scale** (S2-mid RT).
- **2** = kills complete but (a) MDE at/above cost scale at realistic n, or
  (b) the power arithmetic is NOT_RUN and disclosed (index event families:
  no court-style MDE computed; per-cell thinness published).
- **1** = MDE ≥ 3× cost scale (S2-mid) — only tail-scale effects detectable
  (the court's FX-F2 finding) — or a required gate/owner-gated dependency
  blocks freezing.
- **0** = informal kill conditions only, or none.

### D4 — PIT-availability (are all conditioners point-in-time honest?)
- **3** = every conditioner is PIT with per-year and/or minute-level
  verifiers (PASS_EVIDENCED calendars, vintage law applied where relevant,
  strict-past in-repo construction); look-ahead structurally excluded.
- **2** = calendars PIT but surprise/decision-content conditioning NOT_RUN
  (schedule-time anchoring only), and/or minute-level anchors exist for
  only part of the claimed window.
- **1** = conditioning rests on latest-vintage external series (NOT
  PIT-strict) or an owner-gated dependency.
- **0** = conditioning NOT_RUN/absent.

### D5 — Cost-survivability proxy (MECHANICAL floor; NOT a PnL estimate)
Definition: **floor ratio r = RT(S2-mid) ÷ MDE(n)**, where RT(S2-mid) is the
modeled round-trip at the middle tier built ONLY from corrected fees +
close-proxy spread + 1-tick-pair slippage (FEES_CORRECTED @72c9bc5b; all
MODELED COST, account verification NOT_RUN, UNDER REVIEW), and MDE(n) is the
court-method minimum detectable effect (two-sided α=0.05, power 80%, z=2.80;
dispersion proxy = committed daily-return σ, an upper bound) at the family's
documented realistic event/trigger density. Where MDE is NOT_RUN, that fact
is scored, never inferred.
- **3** = r ≤ 1/3 (a detectable effect clears the floor ≥3×).
- **2** = r ≤ 1.
- **1** = r ≤ 3, **or** floor computed but MDE NOT_RUN (survivorship
  unproven — never an inferred pass).
- **0** = r > 3, or the floor itself is not computable from committed inputs.
- **Prohibition restated**: the floor is arithmetic on fees/spread/slippage
  tiers and committed dispersion proxies. It is NOT an expectancy, NOT a
  breakeven-win-rate claim, NOT a PnL estimate, and no return statistic of
  any conditioned construction enters it. Words "measured/complete cost"
  FORBIDDEN.

### Aggregation + tie-break law (mechanical, pre-stated)
**Score = D1+D2+D3+D4+D5 (0-15).** Equal totals → **D3 desc** (sharpest
kill-set first) → **D2 desc** → **D1 desc** → **D4 desc** → id asc
(family id, then symbol leg). Registration status is a DISPLAYED column,
never an ordering key — the synthesis lane reads rank and flags together.

### Standing prohibition (applies to every cell of every table below)
NO return statistic enters any dimension. The only numerics used are:
artifact-backed coverage facts, registration properties (kill lists, control
lists, gates), calendar verdicts, committed descriptive anatomy
(volume/|ret| ratios, variance shares, spread signs), and the §D5 mechanical
floor arithmetic. If a future reader cannot reproduce a score from cited
artifacts + these anchors, the score is void.

---

## 2. Worked example — PB1 H-A (OVN→RTH continuation, ES-first; parent family, NOT one of the returned 18)

Source: PLAYBOOKS_DRAFT §1 (spec table + identity census) + ES addendum
§8-§11 (M-A/M-B, K1-K5, NEW-1..4) + ES_DEEP_v2 §3. Every input below is a
committed fact.

| dim | score | mechanical basis |
|---|---|---|
| D1 | **3** | OVN/session anatomy measured on ES across ALL 7 eras (Var(ON) share E1-E7 table; ON volume share ~15-17% across 16y; OVN-share eras are K1's constraining anatomy) — committed and re-verified |
| D2 | **3** | M-A/M-B name actors (Globex information accumulators vs thin-crowd over-extension; RTH liquidity providers opening books slowly vs fading), exact timing (17:00→08:30 CT tail, q80 strict-past, 08:30 entry, era-correct close exit), symbol reason (ES OVN carries 21-54% of variance by era), and family-specific negatives exist (C1 seeded clock placebo, C4 dose-response, NEW-2 FOMCIN information-source test) |
| D3 | **2** | kills pre-registered and complete (K1 era instability, K2 both-arms-floor, K3 drop-window, K4 delay flip on scored pair, K5 NQ-vs-ES; NEW-1..4) — but the court-method MDE for this family's armed days (q80 tails ≈ 20% of 4,204 sessions ≈ 840) is **NOT_RUN** (never computed; per-cell thinness only published) |
| D4 | **3** | m = log(open_0830 / C_prev-era-correct) fully in-repo strict-past; FOMC day-level EXCLUDE on public dates; calendar-uncertain EXCLUDE/NOT_RUN; no external conditioner |
| D5 | **1** | floor computed: ES S2 33.49 USD/side = 2.68 ticks/side (RT 5.36 ticks; composition §ESNQ 0.1) — but MDE NOT_RUN ⇒ anchor "floor computed, MDE NOT_RUN" = 1 |
| **Total** | **12** | package-quality score only. Status flags: SPEC_PB1_ES r3 A-r4 scope **24 identities FROZEN**; NO_GO_REGISTER/SCORE/ORDER stands; freeze preconditions (fees-account D2, calendar D3, A7 review) open |

Reading of the worked example: the rubric scores the COMPLETENESS of the
pre-registration package — the program's most completely specified family
scores 12 — and says nothing about whether any edge exists. It also shows
the rubric's honest penalties: even the flagship family loses a point each
for a missing power statement (D3) and the un-proven cost survivorship (D5).

---

## 3. Consolidated PRELIMINARY ranking — returned families only (outcome-blind)

Rows: the 8 ESNQ families + the 6E6B families' 10 symbol legs (F5/F6 are
overlays, listed with their own rows and 0 standalone identities). Parent
PB1 H-A shown as reference only. **P1-6J6A and P1-COMM: PENDING — rows to
be appended by the synthesis lane under this rubric.** Cross diagnostics
X-1..X-5 follow separately (excluded from registration ordering by class).

Flags: `BLK` = BLOCKED_TRIAL_BUDGET (ES: cap headroom 0; ESNQ aggregate
minimal 36). `CTG` = contingent register (NQ: cost/clock gates + full-era
rebuild; no NQ cap defined yet). `HOLD` = PB2 Co-Owner HOLD (not schedulable;
census contingency only). `GATE` = owner-gated dependency (FX-F5 vintage
decision). `OV` = overlay (no standalone identities).

| rank | family | leg | D1 | D2 | D3 | D4 | D5 | total | status | one-line mechanical basis (artifacts only) |
|---|---|---|---|---|---|---|---|---|---|---|
| ref | PB1 H-A/H-B (parent) | ES | 3 | 3 | 2 | 3 | 1 | **12** | registered, A-r4 24 FROZEN | §2 above |
| 1 | FX-F2 Policy-Decision | 6B | 3 | 3 | 2 | 2 | 2 | **12** | CTG (no FX cap) | 18.7× minute-720 DST-stable anatomy + 56/58 PIT; kills sharp; MDE 20.6bp = 2.3× S2-mid RT 9.0 ⇒ D3=2; r=0.37-0.50 ⇒ D5=2 |
| 2 | FX-F3 US-8:30 Spillover | 6B | 2 | 3 | 2 | 3 | 2 | **12** | CTG | ×1.95-class anatomy adjacent + BLS PIT + vintage falsifier; type-census/latency NOT_RUN ⇒ D1=2; dead-corpus-distinguishable ⇒ D2=3; MDE 12.0 vs RT 9.0 ⇒ D3=2, r≈0.75 ⇒ D5=2 |
| 3 | FX-F3 | 6E | 2 | 3 | 2 | 3 | 2 | **12** | CTG | same as 6B leg on 6E numbers (MDE 10.1 vs RT 5.0 ⇒ D3=2; r≈0.5 ⇒ D5=2) |
| 4 | FX-F1 London-Range | 6E | 3 | 2* | 2 | 3 | 2 | **12** | **HOLD** | full anatomy + DST proof + court package (D1=3); ancestry overlap V2-A4-P2 (court honest category) ⇒ D2=2; census gate declared, MDE≈cost at n 300-900 ⇒ D3=2; r≈0.9 ⇒ D5=2 |
| 5 | FX-F2 | 6E | 3 | 3 | 1 | 2 | 3 | **12** | CTG | ×17.2 + 58/58 minute-proof; MDE 17.0bp = 3.4× S2-mid RT 5.0 ⇒ D3=1 (court power finding); r≈0.29 ⇒ D5=3 (floor low — detectability, not floor, binds) |
| 6 | ES-F1 FOMC-RES | ES | 3 | 3 | 2 | 2 | 1 | **11** | **BLK** | 91 timed events multi-era (D1=3); actors+NC-1 (D2=3); kills complete, court-MDE NOT_RUN (D3=2); minute-proof 2016+ only + surprise NOT_RUN (D4=2); floor 2.68 tk/side, MDE NOT_RUN (D5=1) |
| 7 | NQ-F1 FOMC-ERA | NQ | 3 | 3 | 2 | 2 | 1 | **11** | CTG+rebuild | era-table-pinned mechanism + NC-5; same D3/D4/D5 pattern as ES-F1; rebuild precondition inherited |
| 8 | ES-F2 MACRO-0730 | ES | 2 | 3 | 2 | 3 | 1 | **11** | **BLK** | BLS PASS_EVIDENCED + vintage law + canceled-day falsifier (best PIT in program ⇒ D4=3); anatomy concentrated modern era, per-era NOT_RUN ⇒ D1=2 |
| 9 | NQ-F2 MACRO-0730-NQ | NQ | 2 | 3 | 2 | 3 | 1 | **11** | CTG+rebuild | null-era built-in control + K7 inverted-mechanism kill (D2=3); two contrast eras only, 2010-16 NOT_RUN ⇒ D1=2 |
| 10 | ES-F4 RUN-REV | ES | 3 | 2 | 2 | 3 | 1 | **11** | **BLK** | acf1/VR all 7 eras (D1=3); daily→session mapping INFERENCE ⇒ D2=2; fully in-repo strict-past ⇒ D4=3 |
| 11 | FX-F1 | 6B | 3 | 2 | 2 | 3 | 1 | **11** | **HOLD** | as 6E leg; RT 7.6-10.4bp vs MDE 6.28@n600 ⇒ r≈1.2-1.7 ⇒ D5=1 (court's 6B cost finding) |
| 12 | FX-F6 CoT-Conditioning | 6E | 3 | 2 | 2 | 3 | 1 | **11** | OV | 1,082wk + vol-descriptive + 6B near-zero falsifier (D1=3); 21d-vol→intraday transfer INFERENCE ⇒ D2=2; overlay: host floor, own MDE NOT_RUN ⇒ D5=1 |
| 13 | FX-F4 Reopen-Gap | 6E | 2 | 2 | 2 | 3 | 2 | **11** | CTG | gap-std 0.378% + DST natural experiment measured; no trigger census ⇒ D1=2; dead session-momentum overlap ⇒ D2=2; r≈0.94 ⇒ D5=2 |
| 14 | ES-F3 COT-CROWD | ES | 2 | 2 | 2 | 3 | 1 | **10** | **BLK** | 922 releases multi-era but session mapping NOT_RUN ⇒ D1=2; directional leg INFERENCE ⇒ D2=2; CoT PIT clean ⇒ D4=3 |
| 15 | NQ-F3 RUN-REV-NQ | NQ | 2 | 2 | 2 | 3 | 1 | **10** | CTG+rebuild | VR/ACF on pre-recovery series; rebuild = the K6 gate ⇒ D1=2 |
| 16 | NQ-F4 ROLLWK | NQ | 1 | 2 | 2 | 3 | 1 | **9** | CTG | family-specific interaction NOT_RUN; only adjacent roll anatomy ⇒ D1=1; Role A standing chain audit (K6 gate + NC-8) keeps D3=2 |
| 17 | FX-F4 | 6B | 1 | 2 | 2 | 3 | 1 | **9** | CTG | **gap anatomy NOT_RUN on 6B (declared gate)** ⇒ D1=1; RT 9.0 vs MDE 6.28 ⇒ r=1.4 ⇒ D5=1 |
| 18 | FX-F5 CIP-Regime-Cond. | overlay | 2 | 3 | 1 | 1 | 1 | **8** | **GATE** | 6B corr +0.84 measured (D1=2, 6E fragile); conditioning genuinely two-sided (D2=3); owner-gated + vintage-flip measured ⇒ D3=1; rates NOT PIT-strict ⇒ D4=1 |

\* FX-F1 D2 basis: mechanism/timing named with family-specific falsifiers,
but court §b places it in the honest "partially overlapping with a dead
family's signal class" category (FOREX-FREE-V1/V2 London failures) — anchor
D2=2. Disclosed as the single most consequential anchor choice in this
table: at D2=3 FX-F1-6E would tie FX-F2-6B's profile and order first by id.
The ancestry court, not this rubric, settles it.

**PENDING (append under this rubric): 6J6A families (lane P1-6J6A,
concurrent — expected themes per dossiers: BoJ MPM conditioning, MOF
intervention-threshold, RBA decision-window PB3-PARK ancestry, 6A regime
beta) and COMM families (lane P1-COMM, concurrent). No score is inferred
for unreturned lanes.**

### How to read the top of this table (flags are load-bearing)
- Rank 1 (FX-F2-6B) and rank 5 (FX-F2-6E) are the **court's power-starved
  families**: they need 17-21 bp/trade — 2-3× (6B) to 3-5× (6E) their full
  modeled cost — to be detectable at n=56-58. Their rank reflects package
  quality (complete anatomy, perfect PIT, sharp kills), and the D3/D5 cells
  carry the court finding verbatim. No schedulability claim is made.
- Rank 4 (FX-F1-6E) is **PB2 HOLD** — first schedulable action is the
  court's descriptive census (≥500-trigger gate), never a scored cell.
- Every ES row is **BLOCKED_TRIAL_BUDGET** (cap 24 FROZEN, headroom 0;
  ESNQ minimal aggregate 36). Every NQ row is contingent-after-gates. No
  FX cap is defined anywhere (CENSUS_PROPOSAL §2 states this plainly).
- Divergence from sibling orderings is expected and disclosed: ESNQ used a
  3-axis sum (0-9) with no PIT/cost axes and no MDE arithmetic; 6E6B used a
  3-axis product (0-27) with power inside falsifiability. This program
  rubric splits power (D3) from floor-survival (D5) and adds PIT (D4);
  e.g. ES-F1 falls from sibling rank 9/9-equivalent to 11/15 here solely
  through the NOT_RUN power statement (D3=2) and un-proven D5 — an honest
  program-level correction, not a re-litigation of their work.

---

## 4. Cross-symbol diagnostics (this lane's X-1..X-5) — scored, NOT registration-ranked

Class = falsification diagnostics; 0 scored identities; D5 = N/A (no cost
charged, no double-counting). Ranked among themselves by the same anchors
for sequencing the 0-cost descriptive passes only.

| diag | D1 | D2 | D3 | D4 | sum(0-12) | sequencing note |
|---|---|---|---|---|---|---|
| X-5 ERA-SYNC | 3 | 3 | 3 | 2 | **11** | cheapest first pass: pure arithmetic on committed series; relabels era clocks program-wide |
| X-1 OVN-COMOVE | 2 | 3 | 3 | 3 | **11** | falsifier for the OVN family; blocked on NQ same-kind recompute (+rebuild precondition) |
| X-2 RELMIN-SIG | 2 | 3 | 3 | 3 | **11** | blocked on common-window re-measure; biggest mechanism re-scoping blast radius (4 families) |
| X-3 FX-BASKET | 2 | 3 | 3 | 2 | **10** | needs u-series construction; 6J thin-book stratum pre-degraded |
| X-4 PLACEBO-POOL | 1 | 2 | 3 | 3 | **9** | harvest-only: runs when first registered families run their mandatory control legs; zero cost |

Ordering rule among diagnostics: sum desc, then D1 desc, then id asc. X-5
leads on D1=3; X-1 precedes X-2 by id asc (both sum 11, D1=2); X-4 last
(sum 9). All are prep-legal descriptive passes; none may gate or rescue a
family except through its own pre-declared refutation conditions in
CROSS_HYPOTHESES §X-K rules.

— End of RANKING_FRAMEWORK.md. Mechanical, outcome-blind, artifacts-only;
no return statistic entered any cell; missing evidence scored as its
NOT_RUN anchor, never as PASS.
