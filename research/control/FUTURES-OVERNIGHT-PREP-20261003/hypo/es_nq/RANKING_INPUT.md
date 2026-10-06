# RANKING_INPUT — Outcome-blind rubric + trial-identity census for ES/NQ families

Task **FUTURES-OVERNIGHT-PREP-20261003**, lane **P1-ESNQ**. Generated UTC
2026-10-04. Companion to `ESNQ_HYPOTHESES.md` / `esnq_hypotheses.json`
(same directory). **Outcome-blind by construction: NO return statistic, NO
PnL, NO backtest output exists or is used anywhere below.** Ranking is a
mechanical function of evidence/registration quality only.

---

## 1. The rubric (stated before any application)

Three axes, integer 0-3 each, summed to 0-9. Each anchor is a mechanical
test against this lane's verified citations — no judgment call after the
anchors are agreed.

### Axis A — Evidence-coverage (does committed, symbol-specific anatomy constrain the mechanism?)
- **3** = the family's constraining anatomy is measured ON THE TARGET
  SYMBOL, spans ≥2 eras or a multi-era full sample, and lives in a
  committed artifact this lane re-verified at 72c9bc5b (sha256 in
  `esnq_hypotheses.json`).
- **2** = anatomy is committed and symbol-specific but (a) confined to a
  single era/window, or (b) computed on a series with a known defect
  (pre-recovery NQ aggregates), or (c) the family-specific interaction is
  NOT_RUN while only adjacent anatomy exists.
- **1** = only indirect evidence (PIT calendar + cross-symbol or
  calendar-free adjacent statistics).
- **0** = no artifact-backed anatomy.

### Axis B — Mechanism-specificity (is the causal story pinned to actors, timing, symbol?)
- **3** = named microstructure actors + exact timing + a symbol/era reason,
  AND a family-specific negative control that shows NOTHING if the
  mechanism is fake (NC-1…NC-8 in ESNQ_HYPOTHESES.md).
- **2** = mechanism and timing named, but actors vague or the measured
  anatomy (daily/horizon aggregates) maps to the session-level claim only
  by INFERENCE.
- **1** = generic behavioral story, no distinguishing observable.
- **0** = no distinct falsifiable content.

### Axis C — Falsifiability (are the kills pre-registered and observable?)
- **3** = pre-registered mechanism-level kills (era instability, placebo
  reproduction, anatomy pre-gate, concentration window), delay-pair
  adjudication where applicable, AND an explicit cost-tier survival
  statement (S2 default + S1/S3 flanks, MODELED, fees UNDER REVIEW).
- **2** = kills named but missing one element (no anatomy pre-gate, or no
  delay axis).
- **1** = informal kill conditions only.
- **0** = none.

### Tie-break law (mechanical)
Equal totals → higher Axis B wins; still tied → higher Axis A; still tied →
both listed tied and the symbol-gate status disclosed (ES = BLOCKED_
TRIAL_BUDGET now; NQ = contingent-after-gates).

---

## 2. Application (scores with one-line justifications)

| family | A | B | C | total | justification (mechanical) |
|---|---|---|---|---|---|
| **ES-F1 FOMC-RES** | 3 | 3 | 3 | **9** | 91 timed events, multi-era bucket profile + era tables committed (ES_fomc_stats.json verified); actors (stand-aside crowd / returning RTH book) + exact minute timing + NC-1; full kill set incl. anatomy pre-gate F1-K6 and S2-survival |
| **ES-F2 MACRO-0730** | 2 | 3 | 3 | **8** | calendar PIT multi-era (204+204) but ES-side spike anatomy concentrated in the modern era; per-era spike NOT_RUN ⇒ A2. Actors + NC-2/NC-2b canceled-day falsifier; full kill set + F2-K6 anatomy gate |
| **ES-F3 COT-CROWD** | 2 | 2 | 3 | **7** | 922 releases multi-era committed but session-granularity mapping NOT_RUN ⇒ A2; directional actor (stop-cascade) is INFERENCE on a vol-only measurement ⇒ B2; vol leg cleanly killable + gated stage ⇒ C3 |
| **ES-F4 RUN-REV** | 3 | 2 | 3 | **8** | acf1/VR committed across ALL 7 eras (verified) ⇒ A3; daily-close aggregates → session-level claim is INFERENCE, actors vague ⇒ B2; full kill set incl. F4-K6 placement gate ⇒ C3 |
| **NQ-F1 FOMC-ERA** | 3 | 3 | 3 | **9** | 84 clean events + era table committed (verified); mechanism pinned to the measured era shift (info-ratio stable / volume diluted); NC-5; full kill set |
| **NQ-F2 MACRO-0730-NQ** | 2 | 3 | 3 | **8** | two contrast eras committed (2017-20 null, 2023-26 spike) but scoring window single-era and 2010-16 NOT_RUN ⇒ A2; participation-era mechanism with the null era as built-in control (NC-6/6b) ⇒ B3; full kill set incl. K7 inverted-mechanism kill |
| **NQ-F3 RUN-REV-NQ** | 2 | 2 | 3 | **7** | VR/ACF multi-era BUT computed on the pre-recovery series; full-era rebuild = hard precondition ⇒ A2; daily→session INFERENCE ⇒ B2; kills + rebuild gate ⇒ C3 |
| **NQ-F4 ROLLWK** | 1 | 2 | 3 | **6** | the family-specific interaction (roll-week × session) is NOT_RUN; only adjacent roll anatomy ⇒ A1; Role B actors named but unmeasured (Role A is construction law, not a family) ⇒ B2; K6 gate + NC-8 + standing Role-A audit ⇒ C3 |

### Resulting order (tie-breaks applied)
- **ES**: **F1 (9) > F2 (8) > F4 (8, tie-break: B3>B2) > F3 (7)**
- **NQ**: **F1 (9) > F2 (8) > F3 (7) > F4 (6)**
- **Overall top-3 (single-symbol families)**: **ES-F1 (9), NQ-F1 (9),
  ES-F2 (8 — tie-break over ES-F4 by Axis B; NQ-F2 also 8 and is disclosed
  tied with ES-F2 at the same A/B/C profile, ordered after ES-F2 solely
  because its register is contingent-after-gates).**

No return statistic participated in any cell; every justification cites
either an artifact field or a registration property.

---

## 3. Candidate trial-identity census (arms × tails × delays × tiers)

Convention (follows SPEC_PB1_ES §6 / PLAYBOOKS A-r4): every scored cell is
an identity; mandatory scored controls = C1 seeded clock placebo + C2
always-in baseline + the family-specific negative control (NC) where
scored; descriptive legs (stage-1 of ES-F3, Role-B of NQ-F4, canceled-day
falsifier subsets, era/K-views) cost **0** identities (evaluation views on
existing paths, per the K1/NEW-1 precedent).

| family | grid (arms×tails×delays×tiers) | full-grid IDs | minimal-core IDs | + scored controls | minimal total |
|---|---|---|---|---|---|
| ES-F1 | 2×2×2 (D+1m,D+30m) ×3 tiers | 24 | 8 (S2 only) | 3 (C1,C2,NC-1) | **11** |
| ES-F2 | (CPI) 2×2×2×3 = 24; (CPI+NFP) 48 | 48 | 8 (CPI, S2) | 3 (C1,C2,NC-2) | **11** |
| ES-F3 | gated directional 2×2×1×1 | 4 (stage-1 vol leg = 0) | 4 | 3 (C1,C2,NC-3) | **7** |
| ES-F4 | 2×2×1×1 (k=5) | 8 (k∈{3,5}) | 4 (k=5, S2) | 3 (C1,C2,NC-4) | **7** |
| NQ-F1 | 2×2×2×3 | 24 | 8 (S2) | 3 (C1,C2,NC-5) | **11** |
| NQ-F2 | (CPI+NFP, S2) 2 series×2×2×2 = 16; ×3 tiers = 48 | 48 | 8 (CPI, S2, 2023-26 era) | 3 (C1,C2,NC-6) | **11** |
| NQ-F3 | 2×2×1×1 (k=5) | 8 (k∈{3,5}) | 4 | 3 (C1,C2,NC-4-analog) | **7** |
| NQ-F4 | gated differential 2×2×1×1 | 4 (Role-B stage-1 = 0) | 4 | 3 (C1,C2,NC-8) | **7** |

### Standing-budget adjudication
- **ES: the 24-identity A-r4 scope is FROZEN (SPEC_PB1_ES r3, untouched).**
  Available headroom for new ES identities = **0**. Therefore EVERY ES
  family above is **BLOCKED_TRIAL_BUDGET** (minimal demands: F1 11, F2 11,
  F3 7, F4 7; aggregate minimal 36). Any ES family entering a future cycle
  requires an owner amendment + explicit ceiling re-check; until then only
  their **0-cost legs are executable**: ES-F3 stage-1 vol leg, ES-F4/ES-F1
  anatomy pre-gates (F4-K6/F1-K6/F2-K6 descriptive measurements) as prep-
  class evidence gathering.
- **NQ: sibling-after-cost/clock-gate.** Cost statement now quotable in
  principle (2.24/side MODELED, UNDER REVIEW until A7 re-audit); calendar
  17/17 + 68/68 landed but 2026 Globex times NOT_OBTAINED and early-close
  times 2011/2021-25 NOT_TRANSCRIBED; full-era rebuild outstanding. The
  census above is therefore **CONTINGENCY ONLY** — no NQ identity is
  registered, enumerated for packet drafting, or scheduled by this
  document; a future NQ packet must mirror A-r4 discipline (explicit
  identity table, scored C1-C4, ceiling arithmetic, no hidden cells).

### Recommended candidate ordering for a future owner decision
1. ES-F1 (rank 9) — cheapest to legalize relative to evidence (already
   PIT-timed events; zero overlap with PB1 armed days);
2. NQ-F1 (rank 9) — first NQ packet candidate once gates + rebuild land;
3. ES-F2 (rank 8) — benefits from the vintage-law falsifier NC-2b;
4. then NQ-F2 / ES-F4 (8), NQ-F3 (7), NQ-F4 (6, Role A mandatory
   regardless of ranking).

— End of RANKING_INPUT.md. Mechanical, outcome-blind, no return statistics.
