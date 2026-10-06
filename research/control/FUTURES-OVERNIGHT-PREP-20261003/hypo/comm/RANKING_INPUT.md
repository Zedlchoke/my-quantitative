# RANKING_INPUT — Outcome-blind rubric + trial-identity census contingency for CL/NG/GC/SI families

Task **FUTURES-OVERNIGHT-PREP-20261003**, lane **P1-COMM**. Generated UTC
2026-10-04. Companion to `COMM_HYPOTHESES.md` / `comm_hypotheses.json`
(same directory). **Outcome-blind by construction: NO return statistic, NO
PnL, NO backtest output exists or is used anywhere below.** Ranking is a
mechanical function of evidence/registration quality only. The same rubric
sibling lanes use (evidence-coverage × mechanism-specificity ×
falsifiability, 0-3 anchors, mechanical).

---

## 1. The rubric (stated before any application — identical anchors to siblings)

Three axes, integer 0-3 each, summed to 0-9. Each anchor is a mechanical
test against this lane's verified citations (COMM_HYPOTHESES.md §0/§7;
`captures/source_sha256.tsv`).

### Axis A — Evidence-coverage (does committed, symbol-specific anatomy constrain the mechanism?)
- **3** = the family's constraining anatomy is measured ON THE TARGET
  SYMBOL, spans ≥2 eras or a multi-era full sample, and lives in a
  committed artifact this lane re-verified at 72c9bc5b.
- **2** = anatomy is committed and symbol-specific but (a) confined to a
  single era/window, or (b) computed on a series with a known defect
  (settlement-derived bars), or (c) the family-specific interaction is
  NOT_RUN while only family-linked adjacent anatomy exists.
- **1** = only indirect evidence (PIT calendar/feature archive + adjacent
  statistics that are not family-linked).
- **0** = no artifact-backed anatomy.

### Axis B — Mechanism-specificity (is the causal story pinned to actors, timing, symbol?)
- **3** = named microstructure actors + exact timing + a symbol/era reason,
  AND a family-specific negative control that shows NOTHING if the
  mechanism is fake.
- **2** = mechanism and timing named, but actors vague or the measured
  anatomy (daily/horizon aggregates) maps to the claim only by INFERENCE.
- **1** = generic behavioral story, no distinguishing observable.
- **0** = no distinct falsifiable content.

### Axis C — Falsifiability (are the kills pre-registered and observable?)
- **3** = pre-registered mechanism-level kills (era instability, placebo
  reproduction, anatomy pre-gate, concentration window), delay-pair
  adjudication **where applicable**, AND an explicit cost-tier survival
  statement (S2 default + S1/S3 flanks, MODELED, fees UNDER REVIEW).
- **2** = kills named but missing one element (no delay axis — the
  binding case for all four comm symbols: intraday is
  NOT_RUN_DATA_ABSENT, and stage-1-gated families defer their directional
  kills to a stage that cannot start).
- **1** = informal kill conditions only.
- **0** = none.

### Tie-break law (mechanical)
Equal totals → higher Axis B; still tied → higher Axis A; still tied →
listed TIED with the symbol-gate status disclosed (all four symbols:
NOT_QUALIFIED_V2, no registration path until the owner data decision).

---

## 2. Application (scores with one-line justifications)

| family | A | B | C | total | justification (mechanical) |
|---|---|---|---|---|---|
| **NG-F1 WNGSR-DESK** | 2 | 2 | 2 | **6** | release clock FACT + Thu-10:00 bucket 25.3% volume share = family-linked adjacent anatomy committed (NG_DOSSIER §3/§4) but interaction NOT_RUN and single era ⇒ A2; actors/timing named, daily-only mapping by INFERENCE ⇒ B2; full kill set + cost tiers + r-1 blocker pre-registered, but no intraday delay axis possible ⇒ C2 |
| **NG-F2 CPC-REVISION** | 1 | 2 | 2 | **5** | feature archive (4,555 issued vintages, sha256 per file) is committed and multi-era but NOT symbol anatomy; no NG-side family-linked stat ⇒ A1; mechanism+vintage clock named, effect maps by INFERENCE, vol-normalization-class controls absent on feature side ⇒ B2; kills incl. mandatory seasonal placebo; error-leg NOT_RUN_DATA_ABSENT declared; no delay axis ⇒ C2 |
| **CL-F1 WPSR-NAIVE** | 1 | 2 | 2 | **5** | 790 vintages committed (feature side); on-symbol anatomy only calendar-free weekday |ret| (not family-linked) and interaction NOT_RUN ⇒ A1; actors/timing named, naive-proxy blocker declared, daily INFERENCE ⇒ B2; double-proxy robustness + Tuesday negative control + cost tiers; no delay axis ⇒ C2 |
| **CL-F2 CONFLICT-REV** | 1 | 2 | 2 | **5** | conflict inputs measured (Cushing 790/790) but conflict-conditional path NOT_RUN and no family-linked adjacent stat ⇒ A1; distinguishing observable (conflict sign) named; INFERENCE mapping ⇒ B2; adjudicated on one frozen event set; no delay axis ⇒ C2 |
| **GC-F1 CURVE-COMPRESS** | 2 | 2 | 2 | **6** | curve anatomy IS the family's conditioning variable, measured on-symbol and committed (contango 99.8-100%, 7 gaps) — single era + settlement-derived defect ⇒ A2; urgency-bid vs rate-mechanical competitor named; stage-1 descriptive gating means directional kill deferred ⇒ B2/C2 |
| **GC-F2 ROLL-MIGRATION** | 2 | 2 | 2 | **6** | the family's own observable measured on-symbol (crossover 1-2 sessions pre-roll, 5/6+1 rolls committed) — single era + vendor volume defect ⇒ A2; LP actors named but cost claim unmeasured (no synchronous book) ⇒ B2; timing placebo band + retire conditions; construction-class ceiling declared ⇒ C2 |
| **SI-F1 BETA-CONVEX** | 2 | 2 | 2 | **6** | the family's own observable measured on-symbol (corr 0.828, elasticity ~1.9, ratio 44→93, 1 decoupling) — single squeeze regime ⇒ A2; convexity POSTULATED with vol-artifact competitor as the mechanical NC ⇒ B2; single-regime auto-kill law + 2-leg cost tiers; stage-gated ⇒ C2 |
| **SI-F2 CURVE-FLIP** | 2 | 2 | 2 | **6** | 6/6 gaps measured on-symbol (family's own observable) — single era, flip never observed in-window ⇒ A2; scarcity-vs-staleness competitors named with mandatory thin-leg control ⇒ B2; retire-to-construction kill + lease-floor sensitivity; stage-gated ⇒ C2 |

### Resulting order (tie-breaks applied)
- **Five families tied at 6 (identical A2/B2/C2 profiles — listed tied,
  no fake ordering): NG-F1, GC-F1, GC-F2, SI-F1, SI-F2.**
  Within the tie the only disclosed ordering input is registration-class
  readiness, NOT rank: NG-F1 is the sole family whose surprise state is
  fully computable today (modulo r-1) but is **NOT_RUN_BLOCKED_R1**;
  GC-F1/SI-F1/SI-F2 stage-1 legs are computable today on 14-22-month
  data with power declared NOT_RUN; GC-F2 is construction-class (never
  registerable as alpha).
- **Three families tied at 5 (A1/B2/C2): CL-F1, CL-F2, NG-F2** — CL pair
  gated by the naive-proxy freeze (no free consensus, measured);
  NG-F2 revision-leg computable, error-leg NOT_RUN_DATA_ABSENT.
- Construction declarations NG-F3 / SI-F3 and the CL cost-law are **not
  ranked** (construction law, not hypotheses).

No return statistic participated in any cell; every justification cites
an artifact field or a registration property.

---

## 3. Candidate trial-identity census (arms × tails × delays × tiers) — CONTINGENCY ONLY

**Standing law, stated plainly: there is NO registration path for any
family below today.** All four symbols are NOT_QUALIFIED_V2
(DATACONTRACT_QUALIFICATION §2); price depth = 14-22 months IBKR legacy
with zero intraday beyond RTH-H1 windows; the owner data decision
(vendor depth incl. O1M/BBO, consensus licensing, slippage declaration)
gates everything. The census enumerates what a future packet WOULD
demand — nothing is registered, scheduled, or scored by this document.

Convention (follows PLAYBOOKS §1/A-r4): every scored cell = one
identity; mandatory scored controls = C1 seeded clock placebo + C2
always-in baseline + the family-specific negative control (NC);
descriptive/stage-1 legs = 0 identities (evaluation views); event
families' arms = {with-state, fade-state} (the two competitor
directions), tails = {positive, negative} state sign; delay = daily
delay-pair {close t, close t+1} (the ONLY delay axis available on
daily bars — intraday delay variants NOT_RUN_DATA_ABSENT); tiers =
slippage S1/S2/S3 on the §0.1 MODELED table.

| family | grid (arms×tails×delays×tiers) | full-grid IDs | minimal-core IDs | + scored controls | minimal total | class |
|---|---|---|---|---|---|---|
| NG-F1 | 2×2×2×3 | 24 | 8 (S2) | 3 (C1, C2, NC=NG-F2 state) | **11** | blocked: r-1 rule freeze + price depth |
| NG-F2 | 2×2×2×3 | 24 | 8 (S2) | 3 (C1, C2, NC=seasonal placebo) | **11** | blocked: degree-day aggregation rule + price depth |
| CL-F1 | 2×2×2×3 | 24 | 8 (S2) | 3 (C1, C2, NC=API-Tuesday) | **11** | blocked: naive-proxy freeze + price depth |
| CL-F2 | 2 (conflict-only)×2×2×3 | 24 (shared grid w/ CL-F1 arm split) | 8 | 3 (C1, C2, NC=agreeing-sign contrast) | **11** (joint w/ CL-F1 = ONE frozen event set, split arms) | blocked: same |
| GC-F1 | directional 2×2×1 (daily close)×3 = 12; stage-1 = 0 | 12 | 4 (S2) | 3 (C1, C2, NC=rate-control subset) | **7** | blocked: serial re-fetch + power (≥2y real-volume curve) |
| GC-F2 | 0 (execution study; produces cost inputs) | 0 | 0 | 0 (placebo band = evaluation view) | **0** | construction class — never scored as alpha |
| SI-F1 | directional 2×2×1×3 = 12; stage-1 = 0 | 12 | 4 (S2) | 3 (C1, C2, NC=vol-normalization) | **7** | blocked: two-leg depth ≥2y + regime split |
| SI-F2 | directional 2×2×1×3 = 12; stage-1 = 0 | 12 | 4 (S2) | 3 (C1, C2, NC=thin-leg exclusion) | **7** | blocked: flip observation + lease-rate hole + depth |

### Standing-budget + gate adjudication
- **No comm identity enters the 24-ceiling arithmetic of any registered
  cycle** — that ceiling belongs to the PB1-ES scope (frozen A-r4); comm
  families have no cycle, no packet, no owner GO. Aggregate minimal
  demand if ALL families were ever legalized: 11+11+11(joint CL)+7+0+7+7
  = **54 > 24 ⇒ would be BLOCKED_TRIAL_BUDGET on any single-cycle
  attempt** — enumerated here precisely so a future packet cannot
  discover this late.
- **0-cost legs executable TODAY as prep-class evidence gathering**
  (evaluation views, no PnL paths): r-1 signed-surprise rule draft +
  verification on the 369-row survey panel; naive-expectation freeze
  drafts for CL; CPC degree-day aggregation-rule derivation;
  descriptive stage-1 panels (GC-F1 curve compression counts, SI-F1
  vol-normalized elasticity by trailing regime, SI-F2 gap-vs-floor
  panel); GC-F2 roll-cost comparison table. Each is a measurement, not a
  scored identity.

### Recommended candidate ordering for a future owner decision (rank + class only)
1. NG-F1 (tied-6; only family with a release-embedded free consensus;
   cheapest to legalize relative to evidence once r-1 + depth land);
2. GC-F1 / SI-F1 (tied-6; free/official daily legs exist — Treasury
   real-yield, LBMA auctions, CoT — but need depth for power);
3. GC-F2 (tied-6 but construction-class: feed the cost model, never
   register) and SI-F2 (tied-6; weakest observability — flip never yet
   seen);
4. CL-F1/CL-F2 (tied-5; joint packet, one frozen event set) and NG-F2
   (tied-5; error-leg permanently NOT_RUN_DATA_ABSENT without daily
   observed temps).

— End of RANKING_INPUT.md. Mechanical, outcome-blind, no return
statistics.
