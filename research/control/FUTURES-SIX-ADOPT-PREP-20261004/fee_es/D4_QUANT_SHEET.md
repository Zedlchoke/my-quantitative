# D4_QUANT_SHEET — ES trial budget: 36 minimal vs 24 frozen (FEE-ES lane, 2026-10-04)

**Decision requested (owner D4, carried): the ES identity ceiling. Frozen cap = 24 (SPEC_PB1_ES r3
§6, A-r4), fully consumed by the PB1 cycle, headroom 0. New-family minimal demand = 36 (census
recount 11+11+7+7, `es_trial_census.json`, `RANKING_INPUT.md` §3, `CENSUS_FINAL.md` §3). Every
ES family is BLOCKED_TRIAL_BUDGET today. This sheet quantifies the options. Nothing here is a
ruling; any cap change = owner amendment + explicit ceiling re-check.**

## 1. The 36 minimal identities, by family (minimal-core + 3 scored controls each)

| family (rank, rubric) | full grid | minimal-core | scored controls | minimal total |
|---|---|---|---|---|
| **ES-F1 FOMC-RES** (9 = A3/B3/C3) | 24 | 8 (S2) | 3 (C1, C2, NC-1) | **11** |
| **ES-F2 MACRO-0730** (8) | 48 (CPI+NFP) | 8 (CPI, S2) | 3 (C1, C2, NC-2) | **11** |
| **ES-F3 COT-CROWD** (7) | 4 (+0-cost stage-1 vol leg) | 4 | 3 (C1, C2, NC-3) | **7** |
| **ES-F4 RUN-REV** (8; tie-break over F3) | 8 (k∈{3,5}) | 4 (k=5, S2) | 3 (C1, C2, NC-4) | **7** |
| **Aggregate** | | | | **36** |

Frozen 24 (occupied, headroom 0): P-A delay pair 8 + P-B tier pair 8 + FOMCIN 4 + controls 4
(FBES1-PLA-D0-S2 / ALW-D0-S2 / FLAT / DOSE-D0-S2). Frozen ranking: **F1 (9) > F2 (8) > F4 (8) >
F3 (7)** — the only legal scheduling order (package-quality only, outcome-blind).

## 2. Option A — raise to 36 (new-family ceiling; total ES ceiling 24 + 36 = 60)

- **Unblocks**: all four families schedulable under the frozen ranking (22 = F1+F2; +F4 = 29;
  +F3 = 36 — exact fit, zero slack).
- **Multiple-testing exposure, quantified**: +12 scored identities vs the frozen 24 = **+50%** ES
  ceiling. Against program-level trial history: the v7p global trial ledger carries **513** scored
  trial rows program-wide → +12 = **+2.3%** of all scored trials the program has ever ledgered,
  concentrated in one symbol; the ES round itself would run 36 scored IDs vs the A-r4 capped-scope
  precedent of 24 (and historical full-rigor pairs D1=52/D2=53 — census hygiene rule 3 pairs).
  12 of the 36 are scored controls (3 per family) — one third of the increment buys control power,
  not arms.
- **Open interplay**: the placebo-budget ruling (§5) can multiply control identities after the fact
  (multi-seed-as-identities ⇒ ≥1,800 placebo IDs across the 18 returned legs program-wide), so 36
  is a floor, not a final number, until that ruling lands.

## 3. Option A′ — intermediate caps 28 / 30 / 32 (greedy packing under the frozen ranking)

Cap scale = new-family ceiling on top of the frozen, occupied 24:

| cap | packed set (by rank) | IDs used | cut (blocked) |
|---|---|---|---|
| **28** | F1 + F2 | 22 | **F3 + F4 cut** (14 IDs out; next family F4 needs 7 > 6 left) |
| **30** | F1 + F2 + F4 | 29 | **F3 cut** (7 IDs out) |
| **32** | F1 + F2 + F4 | 29 | **F3 cut** — identical family set to 30 |

Binding steps: ≤21 → {F1} only; 22-28 → {F1, F2}; 29-35 → {F1, F2, F4}; ≥36 → all four. **Caps 30
and 32 are indistinguishable in family coverage** — the owner is effectively choosing between
2-family (28), 3-family (29-35), and full (36) schedules; there is no cap that buys a partial
family (families are atomic under the census convention: core + its 3 scored controls).

## 4. Option B — keep 24

- **Fits: none.** Headroom 0 ⇒ all four families stay **BLOCKED_TRIAL_BUDGET** (F1, F2, F3, F4
  named individually blocked in `CENSUS_FINAL.md` §1).
- Still executable at 0 identities: ES-F3 stage-1 vol leg (0 IDs by class), ES-F1/F2/F4 anatomy
  pre-gates (F1-K6 / F2-K6 / F4-K6, descriptive), X-1..X-5 cross diagnostics (0 IDs by class).
- Consequence: the ESNQ lane's ES ranking work remains contingency-only; ES program time goes to
  0-cost prep legs until D4 rules.

## 5. Placebo-budget pointer (parent-round proposal, ruling slot still EMPTY)

`CENSUS_PROPOSAL.md` §3 — "The placebo-budget question (owner-decision, framed)"
(`research/control/FUTURES-OVERNIGHT-PREP-20261003/hypo/cross/CENSUS_PROPOSAL.md`), carried to the
owner by `CENSUS_FINAL.md` §5 with the ruling slot empty. Three inconsistent control-counting
conventions hold simultaneously: (a) PLAYBOOKS law — C1/C2/C4 are scored identities; (b) ESNQ /
6J6A / COMM censuses — minimal totals include 3 scored controls each; (c) FX census — controls not
counted, PB2 court §c4 demands ≥100-seed bands (Co-Owner ruling pending). Forcing arithmetic:
multi-seed-as-identities ⇒ **≥1,800 placebo identities** for the 18 returned legs alone;
multi-seed-as-diagnostics ⇒ program-wide "single-seed, no permutation-robustness claim" publication
law until funded. D4's number (24/28/30/32/36) is not final until this is ruled.

## 6. Fail-closed default if undecided

Cap stays 24, headroom 0; every ES family BLOCKED_TRIAL_BUDGET; only the 0-identity legs run.
No registration path opens without an owner amendment in writing.

— Proposals only. FEE-ES raises no gate, registers nothing, and grants no GO.
