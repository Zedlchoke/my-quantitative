# OUTCOME_BLIND_RANKING_R3 — consolidated 10-symbol ranking (controller)

Rubric: RANKING_FRAMEWORK.md 5-dim 0-3 (D1 evidence-coverage, D2
mechanism-specificity, D3 falsifiability, D4 PIT-availability, D5
cost-survivability floor) — **package-quality ONLY**; no return statistic
enters any cell. Tie-break: D3 desc → D2 desc → D1 desc → D4 desc → id asc.
**Schedulability is a separate flag column, never an ordering key.**
Carried rows: FINAL_RANKING §2 (baseline authority) + HYPOTHESES_R2 §7
(RMM/AF4). NEW rows: lane provisional dims (this round).

## 1. Top of the combined table (≥11)

| # | family | leg(s) | (D1,D2,D3,D4,D5) | total | sched | origin |
|---|---|---|---|---|---|---|
| 1 | AF3 bimodal | 6A | (3,3,2,3,1) | 12 | PB_PARK | baseline r1 |
| 2 | JF3 Tokyo-morning | 6J | (3,3,2,3,1) | 12 | GATED | baseline r2 |
| 3 | FX-F2 Policy-Decision | 6B | (3,3,2,2,2) | 12 | GATED (MDE 20.6bp) | baseline r3 |
| 4 | FX-F3 US-8:30 | 6B | (2,3,2,3,2) | 12 | GATED | baseline r4 |
| 5 | FX-F3 US-8:30 | 6E | (2,3,2,3,2) | 12 | GATED | baseline r5 |
| 6 | FX-F1 London-Range | 6E | (3,2,2,3,2) | 12 | PB_HOLD | baseline r6 |
| 7 | FX-F2 Policy-Decision | 6E | (3,3,1,2,3) | 12 | GATED (MDE 17.0bp) | baseline r7 |
| 8 | RMM roll-migration | 6E/6B/6J/6A | (2,3,2,3,1) | 11 | GATED: Role-B owner DC§1.3 ruling | R2 |
| 9 | **ESNQ-F5 EXPWITCH** | ES+NQ | (2,2,2,3,2) | **11** | ES: CAP_BLOCKED · NQ: GATED | **NEW this round** |
| 10-16 | ES-F1, NQ-F1, ES-F2, NQ-F2, ES-F4, FX-F1(6B), FX-F6 | — | 11 each | — | CAP_BLOCKED / GATED / PB_HOLD | baseline r8-r16 |

Full carried tail (10 and below) = cross/RANKING_AGGREGATION.md verbatim
(GC-F1/NG-F1/NQ-F3/SI-F1/SI-F2 10 · CL-F1/F2, FX-F4-6B, NQ-F4, JF2 9 ·
NG-F2/AF2/FX-F5 8 · AF4 10).

## 2. NEW families ranked (this round only)

| rank | family | legs | (D1,D2,D3,D4,D5) | total | sched |
|---|---|---|---|---|---|
| 1 | ESNQ-F5 EXPWITCH | ES+NQ | (2,2,2,3,2) | **11** | ES CAP_BLOCKED; NQ GATED (A7, calendar-2026, D9, owner ceiling) |
| 2 | R3-F1 COT-CROWD | GC+SI | (1,3,2,2,1) | **9** | DATA_BLOCKED (NOT_RUN_DATA_ABSENT) |
| 3 | CL-F3 OPEC-DEC-FLOW | CL | (1,2,2,2,1) | **8** | DATA_BLOCKED |
| 4 | CLNG-F4 STEO-REV | CL+NG | (1,2,2,2,1) | **8** | DATA_BLOCKED |
| 5 | R3-F2 VAULT-FLOW | GC+SI | (1,2,2,2,1) | **8** | DATA_BLOCKED + K6 boundary (construction-adjacent) |

Reading: the ONLY new executable-class proposal (EXPWITCH) ties the
baseline's strong tier at 11 while being born blocked on ES and gated on
NQ — its near-term value is the 0-cost F5-K6 anatomy gate, not scheduling.
The 4 commodity dossiers rank as packages (8-9) but are data-absent;
their D2=3 (R3-F1) shows the court values the captured CFTC clock
evidence even where data blocks execution.

## 3. Divergences disclosed (never silently merged)

1. **FXJA provisional D2 divergence**: FXJA re-scored the baseline 6J6A
   rows with the dead-corpus clause applied conservatively (JF3 3,2,2,3,1
   = 11; AF3 3,2,2,3,1 = 11 vs FINAL_RANKING's 3,3,2,3,1 = 12). The
   baseline FINAL_RANKING remains the authority for carried rows; FXJA's
   stricter pass is recorded as a disclosed divergence (one point on D2
   for JF3/AF3/JF1 if the stricter clause were adopted program-wide).
2. **ESNQ-F5 D2 cap**: 2 not 3 (CNG1-A5-P2 nearest-name + options-side
   BLOCKED_TRANSPORT) — self-capped by its own lane, disclosed in its
   dims basis.
3. **COMM carried 3-axis → 5-dim**: comm lanes carried the baseline's
   3-axis totals (5-6/6) and only scored the NEW families on the 5-dim
   rubric; the 5-dim append for carried COMM families belongs to a future
   synthesis if the owner ever unblocks commodity data (OD-2).

## 4. Schedulability flags (mechanical mapping; SCORED_LEGAL_NOW = none)

- CAP_BLOCKED: every ES family (24 FROZEN, headroom 0; now 43 hypothetical).
- PB_HOLD: FX-F1 (6E/6B legs). PB_PARK: every 6A line.
- GATED (named gates): NQ legs — cost A7 (D2), calendar-2026, D9
  cache_v3 ratification, owner NQ ceiling; 6J — orientation proof done,
  BBO ruling, cost A7, owner 6J ceiling; FX others — power floors,
  vintage laws, anatomy gates per FINAL_RANKING.
- DATA_BLOCKED: all CL/NG/GC/SI lines (no vendor O1M; IBKR corpus
  14-month true-volume + settlement-derived depth; M1 ~10 months, NG 2.2
  years). Registration path does not exist until OD-2 + ceiling rulings.
- CONSTRUCTION_ONLY: ESNQ close-era experiment; FXEB C-02 settle-anchor;
  GC-F2 / NG-F3 / SI-F3 / NQ-F4 Role A (standing).

— End OUTCOME_BLIND_RANKING_R3.md.
