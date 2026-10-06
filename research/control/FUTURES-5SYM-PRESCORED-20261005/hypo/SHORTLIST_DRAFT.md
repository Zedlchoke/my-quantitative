# SHORTLIST_DRAFT — per-symbol shortlist proposal for FUTURES-5SYM-PRESCORED-20261005 (lane HYPO)

- Round: **FUTURES-5SYM-PRESCORED-20261005**, lane **HYPO**. A PREP
  deliverable: registers nothing, schedules nothing, scores nothing,
  ratifies nothing.
- **Label (carried from prior rounds): this is PACKAGE-QUALITY, NOT
  SCHEDULABILITY.** Ranking uses the existing 5-dim mechanical rubric
  (`FUTURES-OVERNIGHT-PREP-20261003/hypo/cross/RANKING_FRAMEWORK.md`:
  D1 evidence-coverage, D2 mechanism-specificity, D3 falsifiability,
  D4 PIT-availability, D5 cost-survivability floor; 0–15; tie-break D3
  desc → D2 desc → D1 desc → D4 desc → id asc). **NO return statistic,
  no profitability claim, and no PnL-derived preference enters any
  cell or any ordering.** D-totals are CARRIED VERBATIM from the
  committed rankings (RANKING_AGGREGATION/FINAL_RANKING §2,
  OUTCOME_BLIND_RANKING_R3, HYPOTHESES_R2 §7, ESNQ_R3 §2c) — none
  recomputed; the disclosed FXJA stricter-pass divergence (JF3/AF3 11
  vs baseline 12) is noted, never silently adopted.
- **Standing gates respected in every line**: `SCORED_LEGAL_NOW =
  none`. PB2 HOLD (6E/6B), PB3 PARK (6A), EXPWITCH dead-at-gate
  (excluded everywhere), D2 fee A7 open (all cost numbers MODELED /
  UNDER REVIEW), BBO NOT_RUN, D9 cache_v3 + cease-guard pending,
  D8 6A tick-era law pending, no NQ/6J/FX cap exists (owner ceiling
  REQUIRED before any registration), P3 quarantine untouched.

## 0. Headline (package-quality only)

Per-symbol leaders by carried package score, and the census's honest
shape: **5 PREP_ABLE, 10 NEEDS_EVIDENCE, 8 HOLD (PB2), 5 PARK (PB3),
1 REJECT (dead-at-gate); 0 new families; 0 scored trials exist on
these five symbols.**

| symbol | package-quality leader(s) | binding reason it is not schedulable today |
|---|---|---|
| NQ | NQ-F1 FOMC-ERA (11) and NQ-F2 MACRO-0730-NQ (11) — both K6 PASSED | D2 fee A7 + D9 cache_v3 + calendar-2026 + owner NQ ceiling (none self-ratifiable) |
| 6E | FX-F3 US-8:30 / FX-F1 London-Range / FX-F2 Policy-Decision (12 each) | **PB2 HOLD** + D2 + owner FX ceiling |
| 6B | FX-F2 Policy-Decision MPC (12) and FX-F3 US-8:30 (12) | **PB2 HOLD** + D2 + ceiling + owner power acceptance (MDE 20.6bp class) |
| 6J | JF3 Tokyo-Morning (12), then JF1 (11) | orientation re-adjudication + BBO + D2 + owner 6J ceiling (no cap exists) |
| 6A | AF3 Bimodal (12) — every 6A line | **PB3 PARK** + D8 (+ D9 for RMM/cease-guard) |

## 1. NQ shortlist (carried D; K6 outcomes this round are descriptive preconditions)

| rank | family | D (tot) | select/reject rationale (package-quality; gates cited) |
|---|---|---|---|
| 1 | **NQ-F1 FOMC-ERA** | (3,3,2,2,1) = **11** | SELECT. K6 anatomy gate PASSED this round (release 2.230× ≥2.0, pre 0.686× ≤0.85, n=85; `nq/m1_fomc_anatomy_v3.json`) — the only NQ family whose pre-scoring anatomy gate is closed on the repaired chain; deepest committed era table. Remaining: D2, D9, calendar-2026, owner NQ ceiling. n=84 thin-power honesty carried. |
| 2 | **NQ-F2 MACRO-0730-NQ** | (2,3,2,3,1) = **11** | SELECT. K6 PASSED both measured eras (4.51× / 4.39×; canceled-day falsifier clean; `nq/m5_0730_era_v3.json`); best PIT axis in the program (BLS vintage law). Constraint owned: scoring era confined to 2023-26 (~160 days; K7 thin-era kill pre-registered). Same signature set as NQ-F1. |
| 3 | **NQ-F3 RUN-REV-NQ** | (2,2,2,3,1) = **10** | SELECT (conditional). Rebuild precondition DONE descriptively (`nq/nq_f3_rebuild_a1a2.json`); K3 2020-concentration now honestly measurable. Still needs its F4-K6 intraday-placement gate (0-ID PREP) before any freeze; same signature set. |
| 4 | **NQ-F4 ROLLWK Role-B** | (1,2,2,3,1) = **9** | HOLD-BACK (NEEDS_EVIDENCE). The roll-week × session-type interaction is NOT_RUN — the measurement IS the K6 gate; Role-A standing audit law unchanged. The NQ lane can close the measurement at 0 identities; until then the family cannot form. |
| — | EXPWITCH NQ leg | (2,2,2,3,2) = 11 | **REJECT — dead at its pre-declared F5-K6** (part (ii) FAIL; anti-cherry-pick). Excluded from every slate. Re-adjudication = P5-OD-1 (owner; default stays dead). |

**NQ slate shape (proposal only)**: minimum = NQ-F1 only, once
D2+D9+ceiling+calendar land; extended = +NQ-F2 (+NQ-F3 after its
placement gate). CONV-B arithmetic: F1 11 + F2 11 + F3 7 (+F4 7) —
standing minimal census 36; owner ceiling REQUIRED (no cap exists);
no silent raise of anything.

## 2. 6E shortlist (EVERY line behind PB2 HOLD — nothing here proposes a lift)

| rank | family | D (tot) | rationale |
|---|---|---|---|
| 1 | **FX-F3 US-8:30** | (2,3,2,3,2) = **12** | SELECT (post-PB2). Best power/cost posture in the FX portfolio (MDE ≈10.1 bp at pooled n≈165 vs RT 3.6–6.3); BLS vintage machinery landed; latency NOT_RUN declared, not blocking. Mandatory: sham-calendar control (row 40 standard) + unclassified-8:30 weaker-sign requirement (near-miss row 51 disclosed). |
| 2 | **FX-F1 London-Range** | (3,2,2,3,2) = **12** | SELECT (post-PB2, census-gated). The named PB2 pair leg; court census PASSED (1,362 triggers ≥500; `fx_f1_f4_census.json`) — the court's descriptive instruments are delivered; MDE≈cost at n≈500 honesty carried. First action under any lift remains the court's census, never a scored cell. |
| 3 | **FX-F2 Policy-Decision (6E FOMC)** | (3,3,1,2,3) = **12** | SELECT (post-PB2, power-accepted). Strongest mechanism score (×17.24 vs ×1.73 intensity ordering); D3=1 is the court's own power finding (MDE ≈17.0 bp at n=58 — only tail-scale effects detectable); spendable only if the owner explicitly accepts tail-effect-only detection. |
| 4 | **FX-F4 Reopen-Gap 6E** | (2,2,2,3,2) = **11** | SELECT-BEHIND (post-PB2, census + corrected arithmetic first). **M2c erratum consumed**: the doc's 0.3778% baseline was the 08:30-CT RTH-open gap; true reopen gaps 2.3–5× smaller (ratio ≈0.16) — any freeze re-derives r = RT/MDE on the corrected scale first (`FXEB_K6_GATES.md` finding 1). Trigger census delivered descriptively (n=1,282 weekday). |
| 5 | **FX-F6 CoT overlay** | (3,2,2,3,1) = **11** | HOLD-BACK (NEEDS_EVIDENCE). The fwd-21d-vol → intraday transfer is NOT_RUN — that transfer IS the hypothesis; COMMNG1-A4-P2 precedent (rows 107–109) makes the release-clock control mandatory. 0-cost PREP item. |
| 6 | **RMM Role-B 6E** | (2,3,2,3,1) = **11** | HOLD-BACK (NEEDS_EVIDENCE + rulings). Mode ledger CLOSED (22/5; Role-A guaranteed deliverable); the mode × post-switch-drift interaction is NOT_RUN; DC §1.3 boundary ruling required before any Role-B freeze; MDE ≈12.5 bp-class at n≈108 — power-marginal by committed statement. |
| 7 | **FX-F5 CIP overlay** | (2,3,1,1,1) = **8** | LAST. Vintage quantification + owner real-time SOFR decision mandatory before any F5-conditioned registration (court §d row 7); the 0.20 rho bar vs the V8/V9 nominal/PPP shadows re-measured first. |

**6E slate shape**: EMPTY unless PB2 is lifted — stated plainly. After
a lift: FX-F3 + FX-F1 (census-gated) + FX-F2 (power-accepted) core;
FX-F4 behind its corrected-arithmetic refresh; overlays/RMM behind
their named PREP items. CONV-D reference arithmetic (owner-signed
convention): FX-A 44 (F2+F3 both legs); full native all-in ≈648
uncapped — ceiling created by the owner, never assumed.

## 3. 6B shortlist (PB2 HOLD binds every line)

| rank | family | D (tot) | rationale |
|---|---|---|---|
| 1 | **FX-F2 Policy-Decision (6B MPC)** | (3,3,2,2,2) = **12** | SELECT (post-PB2, power-accepted). Minute-720 London anchor stable across 8 DST-mismatch dates; MPC 2020→2027 PASS_EVIDENCED; MDE ≈20.6 bp at n=56 vs RT 6.3–11.2 — tail-scale only, the owner-acceptance question is binding. |
| 2 | **FX-F3 US-8:30 6B** | (2,3,2,3,2) = **12** | SELECT (post-PB2). Same landed BLS machinery; 6B thin k=5 coverage rule load-bearing; MDE ≈12.0 bp needs ~1.6–2× cost effects. |
| 3 | **FX-F1 London-Range 6B** | (3,2,2,3,1) = **11** | SELECT (post-PB2, census-gated). Census PASSED (1,342 ≥500); London-share-drift 28.7→23.7% built-in falsifier; the leg is cost-marginal even at n≈500 — honesty carried. |
| 4 | **RMM Role-B 6B** | (2,3,2,3,1) = **11** | HOLD-BACK (NEEDS_EVIDENCE + rulings). Mode 23/4 derived; interaction NOT_RUN; DC §1.3 ruling; holiday-adjacent switches EXCLUDE fail-closed (0/42 grid). |
| 5 | **FX-F4 Reopen-Gap 6B** | (1,2,2,3,1) = **9** | SELECT-BEHIND. **6B gap-std anatomy gate satisfied descriptively this round** (weekday std 0.0400%; dispersion 0.0486→0.0306% by era — `fx_f1_f4_census.json`); but the leg keeps the portfolio's cost-viability doubt (RT 6.3–11.2, 2.1–3.7× the dead proxy) and the M2c-corrected premise. Lowest standalone priority. |
| 6 | **FX-F5 CIP overlay 6B** | (2,3,1,1,1) = **8** | LAST (as 6E row). |

**6B slate shape**: EMPTY unless PB2 lifted; after a lift: FX-F2 +
FX-F3 core, FX-F1 census-gated, FX-F4 last among standalones.

## 4. 6J shortlist (owner ceiling REQUIRED — no cap exists; orientation re-adjudication + BBO + D2 gate every line)

| rank | family | D (tot) | rationale |
|---|---|---|---|
| 1 | **JF3 Tokyo-Morning** | (3,3,2,3,1) = **12** (FXJA stricter 11 disclosed) | SELECT. Zero external-data dependencies; era-stable anatomy; the only 6J line whose gate list is purely signatures. Dead adjacency (row 34) disclosed — its placebo set binds; stricter D2 pass noted, never adopted. |
| 2 | **JF1 BoJ MPM** | (3,2,2,2,2) = **11** | SELECT. K3 anchor-robustness DELIVERED (ANCHOR_INSENSITIVE_AT_45MIN, 7 variants, 54 days — `fx_ja/jf1_k3_anchor.json`); window-convention anchor lawful; K2 power honesty owned (MDE 13–19 bp ≈ RT 8.5–14.7). BoJ minute-stamp acquisition = optional upgrade (P5-OD-2), not a blocker. |
| 3 | **RMM Role-B 6J** | (2,3,2,3,1) = **11** | HOLD-BACK (NEEDS_EVIDENCE + rulings). Mode 19/8 derived; interaction NOT_RUN; D9 cease-guard adoption + DC §1.3 ruling + orientation/BBO/D2/ceiling. 2022-09-20 exemplar = flagged stratum, never base. |
| 4 | **JF2 MOF overlay** | (2,3,1,2,1) = **9** | HOLD-BACK (owner constant P5-OD-4; lag law; 0 own identities). |
| 5 | AU-REL / CN-REL | n/a | OUT (NEEDS_EVIDENCE: data; P5-OD-3 class). |

**6J slate shape**: EMPTY today (orientation/BBO/D2/ceiling block all).
Nearest after signatures: JF3-only, then JF1. CONV-B arithmetic: JF3 11
+ JF1 11 + JF2 7/host (+RMM 4) ⇒ 29–40 minimal depending on host and
RMM rulings; explicit owner ceiling REQUIRED first (IDENTITY_TABLES §5).

## 5. 6A shortlist (PB3 PARK — every line contingency-only; this shortlist PROPOSES NO LIFT)

| rank | family | D (tot) | rationale |
|---|---|---|---|
| 1 | **AF3 Bimodal US+Sydney** | (3,3,2,3,1) = **12** (stricter 11 disclosed) | Contingency lead. The only 6A standalone with full-session power (n≈1,600); opposite-DST-month clock falsifier is the program's cleanest; China-window K4 boundary owned (data NOT_RUN). Needs PB3 lift + D8. |
| 2 | **RMM Role-B 6A** | (2,3,2,3,1) = **11** | Contingency. The only leg with the mode label MEASURED (21/6); interaction NOT_RUN; D8+D9+DC §1.3. |
| 3 | **AF1 RBA decision-minute** | (3,2,1,3,1) = **10** | Contingency, K0-compatible structure required (single stratum / pooled eras); K2 expected by the family's own committed honesty (4.35 bp signal scale < 1 RT). |
| 4 | **AF4 tick-regime overlay** | (2,3,2,2,1) = **10** | Contingency overlay; D-2 audit DELIVERED (era-1 15.18 bp vs era-2 8.20 bp MODELED; 6E/6B constancy CONSTANT closes its secondary control); 0 standalone identities. |
| 5 | **AF2 differential overlay** | (2,3,1,1,1) = **8** | Last; K2 vintage-flip test + owner rates decision. |

**6A slate shape**: EMPTY — PB3 PARK blocks all (+ D8/D9). The only
6A-first action this census endorses is the already-delivered D-2
descriptive audit feeding every 6A cost field. Contingency bookkeeping:
AF1 11 + AF3 11 + RMM 4 (+AF4/AF2 0) — 0 budget today.

## 6. Cross-symbol summary (the two framings, gates first)

| symbol | (a) minimum-signature slate | signatures required | (b) extended slate (all signatures + gates) |
|---|---|---|---|
| NQ | EMPTY today; nearest = NQ-F1-only | D2, D9, calendar-2026, owner NQ ceiling, registration + A7 + typed GO | NQ-F1 + NQ-F2 (+NQ-F3 after placement gate; +NQ-F4 after interaction gate) |
| 6E | **EMPTY unless PB2 lifted** | PB2 lift + D2 + owner ceiling + registration/A7/GO | FX-F3 + FX-F1 (census) + FX-F2 (power-accepted); FX-F4 behind corrected arithmetic; F6/F5/RMM behind named items |
| 6B | **EMPTY unless PB2 lifted** | same set | FX-F2 + FX-F3 core; FX-F1 census-gated; FX-F4 last; RMM/F5 behind rulings |
| 6J | EMPTY today; nearest = JF3-only | orientation re-adjudication + BBO + D2 + owner 6J ceiling | JF3 + JF1 + JF2 (owner constant) + RMM (D9+DC §1.3) |
| 6A | **EMPTY — PB3 PARK** | PB3 lift + D8 (+D9) | D-2 descriptive first (done); AF3 lead; RMM; AF1 (K0 structure); AF4/AF2 overlays |

**Round constant**: `SCORED_LEGAL_NOW = none`; this draft contains 0
return statistics; every power/cost figure is the family docs' own
committed MODELED band or court-method MDE, cited in CENSUS_5SYM.md;
the ranking is package-quality only and is not a recommendation to
schedule, register, or score anything.

— End SHORTLIST_DRAFT.md.
