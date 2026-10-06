# RANKING_AGGREGATION — master outcome-blind ranking + SCHEDULABILITY flags for all 31 existing families

- Task `FUTURES-TEN-HYPO-PREP-20261004`, lane **CROSS**, 2026-10-04 UTC.
  Worktree @ `a4a882658e09092b5b282b666b30a3cfc5ac3418`.
- Law consumed: `hypo/cross/RANKING_FRAMEWORK.md` (D1–D5 anchors 0–3 each,
  sum 0–15; tie-break total→D3→D2→D1→D4→id asc, leg asc; registration
  status DISPLAYED, never an ordering key; **no return statistic enters any
  cell**) and `synth/FINAL_RANKING.md` (consolidated table + standing
  rulings). R2 carries: `HYPOTHESES_R2.md` §7.
- Carry rule (per dispatch): D-scores carried verbatim from FINAL_RANKING
  §2 where present (leg-level, cited per row); R2 families RMM/AF4 carried
  from HYPOTHESES_R2 §7; PB1 carried as the reference row (RF §2 worked
  example; FINAL_RANKING §2 note). **No score recomputed. No cell contains
  a return statistic.**

## 1. SCHEDULABILITY flag set (separate from package score)

`SCORED_LEGAL_NOW | GATED:<gate list> | CAP_BLOCKED | PB_HOLD | PB_PARK |
DATA_BLOCKED | CONSTRUCTION_ONLY`

Mechanical mapping from standing rulings:
- **CAP_BLOCKED** = symbol cap frozen with headroom 0 (ES cap 24, CENSUS_FINAL §3; launch D4 default).
- **GATED:<…>** = CTG class: no cap defined but named preconditions open (cost A7/D2, calendar, rebuild/D9, anatomy gates, owner rulings).
- **PB_HOLD** = PB2 Co-Owner HOLD (FX-F1 both legs).
- **PB_PARK** = PB3 PARK (all 6A lines; contingency only).
- **DATA_BLOCKED** = NOT_QUALIFIED_V2 / no registration path (all COMM).
- **CONSTRUCTION_ONLY** = never registered as alpha (GC-F2).
- **SCORED_LEGAL_NOW = awarded to NO family**: NO_GO_REGISTER / NO_GO_SCORE /
  NO_GO_ORDER stand end-to-end (FINAL_RANKING §4; launch §7 — the owner
  "cho agent làm đi" PREP directive ratifies none of D2/D3/D4/D8/D9 and no
  typed GO).

## 2. Master ranking table (mechanical order carried from the baselines)

D1–D5 listed as (D1,D2,D3,D4,D5); total = sum 0–15. Rank columns carry the
baseline's own rank where it published one. Tie-break law not re-run here —
the baseline order is authority; this table is the controller's index.

| family | leg | (D1,D2,D3,D4,D5) | total | baseline rank | SCHEDULABILITY | carry source |
|---|---|---|---|---|---|---|
| AF3 bimodal US+Sydney | 6A | (3,3,2,3,1) | **12** | 1 / 31 | PB_PARK | FINAL_RANKING §2 r1 |
| JF3 Tokyo-morning | 6J | (3,3,2,3,1) | **12** | 2 / 31 | GATED:orientation-proof,BBO-ruling,cost-A7,6J-ceiling | FINAL_RANKING §2 r2 |
| FX-F2 Policy-Decision | 6B | (3,3,2,2,2) | **12** | 3 / 31 | GATED:power-honesty(MDE 20.6bp) | FINAL_RANKING §2 r3 |
| FX-F3 US-8:30 | 6B | (2,3,2,3,2) | **12** | 4 / 31 | GATED:vintage-law,latency-NOT_RUN | FINAL_RANKING §2 r4 |
| FX-F3 US-8:30 | 6E | (2,3,2,3,2) | **12** | 5 / 31 | GATED:vintage-law,latency-NOT_RUN | FINAL_RANKING §2 r5 |
| FX-F1 London-Range | 6E | (3,2,2,3,2) | **12** | 6 / 31 | PB_HOLD | FINAL_RANKING §2 r6 |
| FX-F2 Policy-Decision | 6E | (3,3,1,2,3) | **12** | 7 / 31 | GATED:power-honesty(MDE 17.0bp) | FINAL_RANKING §2 r7 |
| ES-F1 FOMC-RES | ES | (3,3,2,2,1) | **11** | 8 / 31 | CAP_BLOCKED | FINAL_RANKING §2 r8 |
| NQ-F1 FOMC-ERA | NQ | (3,3,2,2,1) | **11** | 9 / 31 | GATED:cost-A7,calendar-2026,full-era-rebuild | FINAL_RANKING §2 r9 |
| ES-F2 MACRO-0730 | ES | (2,3,2,3,1) | **11** | 10 / 31 | CAP_BLOCKED | FINAL_RANKING §2 r10 |
| NQ-F2 MACRO-0730-NQ | NQ | (2,3,2,3,1) | **11** | 11 / 31 | GATED:cost-A7,calendar-2026,rebuild,anatomy-2023-26 | FINAL_RANKING §2 r11 |
| ES-F4 RUN-REV | ES | (3,2,2,3,1) | **11** | 12 / 31 | CAP_BLOCKED | FINAL_RANKING §2 r12 |
| FX-F1 London-Range | 6B | (3,2,2,3,1) | **11** | 13 / 31 | PB_HOLD | FINAL_RANKING §2 r13 |
| FX-F6 CoT-Conditioning | 6E | (3,2,2,3,1) | **11** | 14 / 31 | GATED:intraday-transfer-NOT_RUN,overlay | FINAL_RANKING §2 r14 |
| JF1 BoJ MPM window | 6J | (3,2,2,2,2) | **11** | 15 / 31 | GATED:orientation-proof,BBO-ruling,cost-A7,6J-ceiling | FINAL_RANKING §2 r15 |
| FX-F4 Reopen-Gap | 6E | (2,2,2,3,2) | **11** | 16 / 31 | GATED:trigger-census | FINAL_RANKING §2 r16 |
| ES-F3 COT-CROWD | ES | (2,2,2,3,1) | **10** | 17 / 31 | CAP_BLOCKED | FINAL_RANKING §2 r17 |
| GC-F1 curve-compression | GC | (2,2,2,3,1) | **10** | 18 / 31 | DATA_BLOCKED | FINAL_RANKING §2 r18 |
| NG-F1 WNGSR-DESK | NG | (2,2,2,3,1) | **10** | 19 / 31 | DATA_BLOCKED(r-1 signed-survey block) | FINAL_RANKING §2 r19 |
| NQ-F3 RUN-REV-NQ | NQ | (2,2,2,3,1) | **10** | 20 / 31 | GATED:cost-A7,calendar-2026,rebuild(executable-in-principle,R2 §4.2) | FINAL_RANKING §2 r20 |
| SI-F1 beta-convexity | SI | (2,2,2,3,1) | **10** | 21 / 31 | DATA_BLOCKED | FINAL_RANKING §2 r21 |
| SI-F2 curve-flip | SI | (2,2,2,3,1) | **10** | 22 / 31 | DATA_BLOCKED | FINAL_RANKING §2 r22 |
| AF1 RBA decision-minute | 6A | (3,2,1,3,1) | **10** | 23 / 31 | PB_PARK(K0 pre-registered) | FINAL_RANKING §2 r23 |
| CL-F1 WPSR-naive | CL | (1,2,2,3,1) | **9** | 24 / 31 | DATA_BLOCKED | FINAL_RANKING §2 r24 |
| CL-F2 conflict-reversal | CL | (1,2,2,3,1) | **9** | 25 / 31 | DATA_BLOCKED | FINAL_RANKING §2 r25 |
| FX-F4 Reopen-Gap | 6B | (1,2,2,3,1) | **9** | 26 / 31 | GATED:6B-gap-std-anatomy-gate(NOT_RUN) | FINAL_RANKING §2 r26 |
| NQ-F4 ROLLWK | NQ | (1,2,2,3,1) | **9** | 27 / 31 | GATED:Role-A-audit,K6-interaction-NOT_RUN | FINAL_RANKING §2 r27 |
| JF2 MOF regime conditioning | 6J | (2,3,1,2,1) | **9** | 28 / 31 | GATED:owner-gated-constant,overlay | FINAL_RANKING §2 r28 |
| NG-F2 CPC-revision | NG | (1,2,2,2,1) | **8** | 29 / 31 | DATA_BLOCKED(error-leg-NOT_RUN_DATA_ABSENT) | FINAL_RANKING §2 r29 |
| AF2 differential overlay | 6A | (2,3,1,1,1) | **8** | 30 / 31 | PB_PARK(DFF-vintage-fragile,overlay) | FINAL_RANKING §2 r30 |
| FX-F5 CIP-Regime | overlay | (2,3,1,1,1) | **8** | 31 / 31 | GATED:owner-vintage-decision,rates-NOT-PIT-strict | FINAL_RANKING §2 r31 |
| R2-F1 RMM | 6E/6B/6J/6A | (2,3,2,3,1) | **11** | 1 (R2 table) | GATED:Role-B-owner-DC§1.3-ruling,Role-A-ledger-NOT_RUN | HYPOTHESES_R2 §7 |
| R2-F2 AF4 TRC | 6A overlay | (2,3,2,2,1) | **10** | 2 (R2 table) | PB_PARK(overlay,contingency-only) | HYPOTHESES_R2 §7 |

Reference rows (NOT re-ranked, carried as published):
- **PB1 H-A/H-B (ES)** = (3,3,2,3,1) = 12 — registered parent, A-r4 24
  FROZEN, headroom 0 → **CAP_BLOCKED** (RF §2; FINAL_RANKING §2 note).
- **GC-F2 roll-migration (GC)** — construction class, 0 identities by
  class, feeds cost inputs → **CONSTRUCTION_ONLY** (FINAL_RANKING §2
  construction note). No D-scores published (not ranked by design).
- **Cross diagnostics**: X-5/X-1/X-2 = 11, X-3 = 10, X-4 = 9 (0–12 scale,
  0 identities; sequencing X-5→X-1→X-2→X-3, X-4 harvest-only;
  RANKING_FRAMEWORK §4); R2 D-1 CEASE-SYNC 11, D-2 TICK-ERA AUDIT 9
  (HYPOTHESES_R2 §5; D-1 leads).

## 3. Controller reading law (carried from FINAL_RANKING §3)

- The order is **package-quality, not schedulability**: rank 1 sits on a
  PARK symbol; rank 2 behind three 6J gates; the highest rows whose gates
  are closable by evidence work alone are the FX trio (ranks 3–5, all CTG,
  court power findings 17–21 bp carried verbatim in D3/D5).
- Every ES row CAP_BLOCKED (cap 24 frozen, headroom 0; minimal aggregate
  36 > 24). Every NQ row GATED + full-era rebuild. Every COMM row
  DATA_BLOCKED (NOT_QUALIFIED_V2). Both R2 rows are PROPOSALS — nothing
  registered.
- Rubric divergence (ESNQ 0–9 sum, 6E6B/6J6A 0–27 product vs program 0–15)
  is disclosed and intentional (RANKING_FRAMEWORK §3 footnote; FINAL_RANKING
  §3) — scores are not comparable across sibling rubrics, only within the
  program rubric.

— End RANKING_AGGREGATION.md. Mechanical, outcome-blind, artifacts-only;
no return statistic entered any cell; missing evidence NOT_RUN, never PASS.
