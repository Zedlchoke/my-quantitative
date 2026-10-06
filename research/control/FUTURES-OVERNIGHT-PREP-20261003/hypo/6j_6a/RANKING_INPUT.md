# RANKING_INPUT — 6J/6A hypothesis families, outcome-blind prioritization input (P1-6J6A)

- Task `FUTURES-OVERNIGHT-PREP-20261003`, lane **P1-6J6A**, 2026-10-04 UTC.
- Companion to `JPY_AUD_HYPOTHESES.md` / `jpy_aud_hypotheses.json` (same
  directory; all facts re-verified at HEAD `72c9bc5b`, sources sha256-pinned
  in `captures/source_sha256.tsv`).
- **Rubric: evidence-coverage × mechanism-specificity × falsifiability** —
  the same three axes and 0-3 anchors the sibling lanes (P1-ESNQ, P1-6E6B)
  use. Mechanical: each axis scored 0-3 against pre-stated anchors; score =
  **product (0-27)** (P1-6E6B convention; the P1-ESNQ sum-convention gives
  the same ordering here and is disclosed as equivalent). **No return
  statistic, no PnL, no expectancy, no hit-rate enters any score — nothing
  has been run.** Scores describe the QUALITY OF THE PRE-REGISTRATION
  PACKAGE ONLY.
- Symbol gates, restated: **6J secondary** (orientation/BBO/cost gates open);
  **6A = PB3 PARK** — every 6A score is bookkeeping for a future packet
  draft; **no scheduling action is proposed for either symbol**.

## Axis anchors (fixed before scoring)

**Evidence-coverage (EC)** — measured evidence available NOW:
- 3 = the family's constraining anatomy is measured ON THE TARGET SYMBOL at
  the family's own trigger/window, multi-era, in a committed artifact this
  lane re-verified at `72c9bc5b`.
- 2 = anatomy measured at adjacent windows, or symbol-specific but
  single-aspect, or a declared dependency/latency hole remains (calendar
  partial, definition gap).
- 1 = mechanism-level analogies/conditioning basis only.
- 0 = nothing measured.

**Mechanism-specificity (MS)** — is the causal story pinned to named actors,
exact timing, and a symbol/venue reason the generic-FX-corpus class could
not represent?
- 3 = named microstructure actors + exact timing + symbol/era reason AND a
  family-specific negative control that shows NOTHING if the mechanism is
  fake.
- 2 = mechanism and timing named, but actors vague or the measured anatomy
  (session/day aggregates) maps to the trigger-level claim only by
  INFERENCE.
- 1 = generic behavioral story, no distinguishing observable.
- 0 = unspecified mechanism.

**Falsifiability (FA)** — can a future registered cycle refute it sharply?
- 3 = pre-registerable mechanism-level kills (placebo, reclassification,
  clock-law falsifier) + honest power statement at realistic n + explicit
  cost-tier survival statement (MODELED, UNDER REVIEW).
- 2 = kills named but power-limited (MDE at/above modeled cost at realistic
  n) or one required kill still NOT_RUN.
- 1 = heavily power-starved (MDE ≥ ~3× cost) or blocked on an owner-gated
  dependency.
- 0 = unfalsifiable.

## Scores

| family | symbol | EC | MS | FA | product | one-line basis (every fact OBSERVED/FACT/DERIVED, cited in JPY_AUD_HYPOTHESES.md) |
|---|---|---|---|---|---|---|
| JF1 BoJ MPM window | 6J | 3 | 2 | 2 | **12** | MPM-day anatomy ×1.87/1.27× + thin-window 34-vs-53 measured on-symbol multi-era; MS 2: decision-minute anchor NOT evidenced (window convention — statement timestamps NOT_RUN), actors inferred; FA 2: n=54, MDE ≈13–19bp ≥ RT 8.5–14.7bp |
| JF2 MOF regime conditioning | 6J | 2 | 3 | 2 | **12** | anatomy measured but the conditioning claim itself (post-disclosure gradients) NOT_RUN ⇒ EC 2; MS 3: named actor (MOF official-risk regime changing hedging asymmetry), disclosure-lag law, shuffled-label placebo + null-era control; FA 2: only 10 in-window ops, threshold constant owner-gated |
| JF3 Tokyo-morning structure | 6J | 3 | 3 | 2 | **18** | 18.1%/15.2% extrema + 11%/13% shares + 59-vs-120 depth measured on-symbol, era-stable ⇒ EC 3; named home-session actors + DST falsifier + weekday negative ⇒ MS 3; FA 2: RT 8.5–14.7bp vs per-trigger scale — tail-only plausibility stated |
| AF1 RBA decision minute | 6A | 3 | 2 | 1 | **6** | ±5' 9.0×/4.8× + change/hold 59/29 measured, calendar PASS_EVIDENCED 1990→2026-09 ⇒ EC 3; MS 2: weak surprise proxy (change-vs-hold), actors inferred; FA 1: K0 thin-n kill PRE-REGISTERED (n=67, fold floor likely fails) + ±5' scale 4.35bp BELOW one RT 8.2bp — power-starved by construction |
| AF2 differential regime overlay | 6A | 2 | 3 | 2 | **12** | 16/16 material-roll sign law measured (EC 2: conditioning gradients NOT_RUN + DFF vintage-fragile); MS 3: CIP input with H-F/H-G law + block-shuffle placebo + 6E vintage-flip precedent as the stated kill bar; FA 2: K2 vintage test runnable from corpus, ~16 material observations |
| AF3 bimodal session structure | 6A | 3 | 3 | 2 | **18** | bimodal U-curve + hub shares + 11:30 modal slot measured on-symbol, all three eras ⇒ EC 3; two-hemisphere actors + opposite-DST-month natural experiment + Shanghai-cluster kill ⇒ MS 3; FA 2: RT 8.2bp vs 1.2–1.5bp per-minute scale — tail-only plausibility stated |

Tie-break (mechanical, pre-stated): (1) product; (2) MS desc; (3) EC desc;
(4) FA desc; (5) family id asc.

## Resulting order (per symbol)

- **6J: JF3 (18) > JF2 (12) > JF1 (12)** — the JF1/JF2 tie (both product
  12) breaks on MS: JF2 MS 3 > JF1 MS 2. The JF1-vs-JF2 order is a rubric
  artifact worth stating: JF1 has the stronger measured event anatomy
  (54 measured decision days with ×1.87 |ret| / ×1.27 volume vs 10
  disclosed ops) but loses MS because its event anchor is a window
  convention (BoJ statement timestamps NOT evidenced) and its actors are
  inferred — if the owner values anatomy completeness over anchor
  specificity, JF1 and JF2 swap. Disclosed, not hidden.
- **6A (PB3 PARK — bookkeeping only): AF3 (18) > AF2 (12) > AF1 (6)**.
  AF1's last place is NOT a judgment that the RBA effect is smaller — its
  ±5' anatomy is the single strongest measurement in this dossier — it is
  the pre-registered K0 thin-n kill (n=67) plus the 4.35bp-vs-8.2bp
  power arithmetic. If PB3 ever reopens with pooled-identity relief, AF1's
  FA re-scores mechanically.

**Top-3 overall (outcome-blind): 1) JF3 Tokyo-Morning Session Structure
(18); 2) AF3 Bimodal US+Sydney Session Structure (18); 3) JF2 MOF
Intervention-Regime Conditioning (12, MS tie-break over JF1).** The
JF3/AF3 tie is dead-even on every mechanical axis (A=3/B=3/C=2 both); the
raw 5th tie-break (family-id asc) would list AF3 first — the stated
override is registration posture: JF3 sits on a secondary-gated symbol
(gates closeable by evidence work), AF3 on a PARK-gated one (reopen is an
owner decision). This override is a choice, not a fact; flagged for the
Co-Owner.

Caveats stated plainly: (i) both 18-scores are session-structure families —
if the Co-Owner wants event-window diversity in the first scored wave, JF2
(12) is the highest-MS event/regime family; the rubric's product mechanic
does not encode diversity, that is an owner choice. (ii) Every 6A score is
contingency bookkeeping under PB3 PARK. (iii) All cost floors are MODELED
and UNDER REVIEW (fee layer corrected; spread high-biased proxy; BBO
NOT_RUN; 6A tick conflict unadjudicated) — any FA score moves if the A7
re-audit or tick adjudication changes the floor.

## Candidate trial-identity census (arms × tails × delays × tiers)

Convention (mirrors SPEC_PB1_ES §6 / P1-ESNQ §3): every scored cell is an
identity; mandatory scored controls C1 (seeded clock placebo) + C2
(always-in) + family-specific negative (C3/C3′) where scored; descriptive
legs (anatomy pre-gates, regime-shuffle placebo diagnostics, overlay views
on existing paths, era views) cost **0 identities**. Tiers = S2 default +
S1/S3 flanks (MODELED cost scenarios); tails = {TP 2×SL / time-exit};
delays = {+1 bar, +30m}.

| family | grid (arms×tails×delays×tiers) | full-grid IDs | minimal-core IDs (S2, 1 delay) | + scored controls | minimal total | n (day-set) |
|---|---|---|---|---|---|---|
| JF1 | 2×2×2×3 | 24 | 8 | 3 (C1,C2,C3) | **11** | 54 MPM days |
| JF1-regime-subset | descriptive only (fold floor fails: 4+2 titled dates) | 0 | 0 | 0 | **0** | 6–7 |
| JF2 | overlay on JF1/JF3 hosts: 2×2×1×1 per host if scored separately | 4/host (8 for both hosts) | 4 | 3 (C1,C2,C3′ shuffled-label) | **7/host** | 10 ops label |
| JF3 | 2×2×2×3 | 24 | 8 | 3 (C1,C2,C3) | **11** | ~1,600 sessions |
| AF1 | 2×2×2×3 | 24 | 8 | 3 (C1,C2,C3) | **11** | 67 meetings (K0: fold floor fails) |
| AF2 | overlay: evaluation views on host paths | 0 | 0 | 0 | **0** | regime labels |
| AF3 | 2×2×2×3 | 24 | 8 | 3 (C1,C2,C3) | **11** | ~1,600 sessions |

### Standing-budget / registration adjudication

- **6J: NO trial cap is defined for 6J anywhere in the corpus (NOT_RUN —
  no ceiling arithmetic exists to check).** Standing symbol status:
  **SECONDARY** — before any identity is registered, the three open gates
  must close: (a) quote-orientation transform implemented + verified in the
  scored engine (orientation law is contract law, the gate is the
  implementation proof); (b) BBO or an accepted spread proxy ruling; (c)
  cost A7 re-audit. The census above is therefore **CONTINGENCY ONLY** —
  enumerated for packet drafting, not registered or scheduled by this
  document. If a future 6J packet mirrors A-r4 discipline, the minimal
  aggregate is JF3 11 + JF2 7/host + JF1 11 ≈ **29–36 identities**, and an
  explicit owner ceiling must be set first.
- **6A: PB3 PARK — census CONTINGENCY ONLY.** No registration, no budget
  request. AF1 additionally carries the **K0 thin-n kill pre-registered**
  (fold floor ≥5 fails at n=67 with any standard fold count; single-stratum
  or pooled-era only) — a future reopen inherits this, it is not
  negotiable. Pre-scored requirements inherited by any 6A packet: k=5 roll
  rule measurement (declared-extrapolation law), tick-size adjudication
  (1e-4 vs 5e-5), both still NOT_RUN.

— End RANKING_INPUT. No outcome data existed to be blind to; none was used.
