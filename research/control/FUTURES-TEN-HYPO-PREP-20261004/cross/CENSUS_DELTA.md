# CENSUS_DELTA — trial-identity census recomputed from CENSUS_FINAL + the R2 delta

- Task `FUTURES-TEN-HYPO-PREP-20261004`, lane **CROSS**, 2026-10-04 UTC.
  Worktree @ `a4a882658e09092b5b282b666b30a3cfc5ac3418`.
- Inputs: `research/control/FUTURES-OVERNIGHT-PREP-20261003/synth/CENSUS_FINAL.md`
  (full table, carried verbatim where cited) + R2 delta
  (`research/control/FUTURES-SIX-ADOPT-PREP-20261004/hypo/HYPOTHESES_R2.md` §8).
- **Denominator planning only.** No registration, no GO, no family
  selection. Outcome-blind; 0 return statistics.

## 1. Census conventions (stated once; mixed conventions NOT summed)

Per CENSUS_FINAL preamble + §4/§5:
- Census unit = one scored trial identity (family × leg × arm × tail ×
  delay × tier) with its own PnL path; controls counted where the row's
  convention says so.
- Three control-counting conventions hold simultaneously and are **NOT
  summed**: (a) PLAYBOOKS law (C1/C2/C4 = scored identities); (b) ESNQ /
  6J6A / COMM minimal totals include 3 scored controls; (c) FX census
  counts 0 scored controls (court §c4 ≥100-seed ruling pending — owner
  slot EMPTY, CENSUS_FINAL §5).
- Program-hypothetical totals (≈1,068 pre-R2; ESNQ 168 + FX ≈648 + 6J6A
  96+8 + COMM 132 + PB1 24) are INFERENCE, not proposals, and mix
  conventions — never quote a program-wide denominator without
  normalization (CENSUS_FINAL §2).

## 2. Per-symbol census table (post-R2)

| symbol | family → minimal IDs | minimal aggregate | cap / status (source) |
|---|---|---|---|
| ES | PB1 24 FROZEN; ES-F1 11; ES-F2 11; ES-F3 7; ES-F4 7 | **36 minimal vs 24 frozen** | cap 24 frozen (A-r4, Co-Owner r5), headroom 0 ⇒ every ES family BLOCKED_TRIAL_BUDGET; executable at 0 IDs: ES-F3 stage-1 vol leg + anatomy pre-gates (CENSUS_FINAL §1/§3; launch D4 default: 24 stands) |
| NQ | NQ-F1 11; NQ-F2 11; NQ-F3 7; NQ-F4 7 | **36 minimal CTG** | no NQ cap defined; contingency only behind cost A7 + calendar 2026 + full-era rebuild (CENSUS_FINAL §4; launch D9 for chain canonicalization) |
| FX 6E/6B | FX-F1..F4 census-gated 36/leg full-grid; FX-F5/F6 overlays 0 standalone | **program-hypothetical ≈648 uncapped** (convention c: 0 scored controls) | no ceiling defined anywhere; PB2 HOLD on FX-F1; all FX rows CTG (CENSUS_FINAL §1/§4; FX §8) |
| 6J | JF1 11; JF2 7/host; JF3 11 | **≈29–36 minimal** | no 6J cap; explicit owner ceiling required before any registration (CENSUS_FINAL §4; R2 §8) |
| 6A | AF1 11; AF2 0; AF3 11; AF4 0 | **PB3 PARK — 0 budget** | census contingency only; K0 thin-n inherited (CENSUS_FINAL §4; JPY_AUD park law) |
| COMM NG/CL/GC/SI | NG-F1 11; NG-F2 11; CL-F1/CL-F2 11 joint; GC-F1 7; GC-F2 0; SI-F1 7; SI-F2 7 | **54 minimal, data-blocked** | NOT_QUALIFIED_V2: no registration path until owner data decision; 54 > 24 ⇒ BLOCKED_TRIAL_BUDGET on any single-cycle attempt (CENSUS_FINAL §1/§4; COMM RI §3) |
| 6F | — | **0 (NOT_RUN_DATA_ABSENT)** | no data owned; no census exists (CENSUS_FINAL §1 last row) |

## 3. R2 delta (HYPOTHESES_R2 §8, carried verbatim)

- **+12 IDs**: RMM Role B — 6E 4 + 6B 4 + 6J 4 (NQ excluded by
  anti-duplication cross-reference to NQ-F4). FX program-hypothetical
  648 → **656** if ever legalized; 6J minimal surface ≈ 33–40.
- **+4 contingency-only 6A IDs**: RMM-6A leg (PB3 PARK — census line
  only, K0-class laws carry over).
- +0 ES, +0 NQ. AF4: 0 standalone (host × 2 strata only). Diagnostics
  D-1/D-2: 0 identities, 0-cost.
- Controls: NOT counted as trial identities in the R2 delta (court §c4
  convention inherited).

## 4. THIS ROUND'S NEW PROPOSALS — column EMPTY by design

| symbol | existing minimal (post-R2) | **this round's NEW proposals** |
|---|---|---|
| ES | 36 minimal / 24 frozen | **(EMPTY — controller fills from es_nq lane output)** |
| NQ | 36 minimal CTG | **(EMPTY — controller fills from es_nq lane output)** |
| FX 6E/6B | ≈656 program-hypothetical uncapped | **(EMPTY — controller fills from fx_eb lane output)** |
| 6J | ≈29–36 (+4 RMM surface) | **(EMPTY — controller fills from fx_ja lane output)** |
| 6A | 0 (PARK) + 4 contingency-only | **(EMPTY — controller fills from fx_ja lane output)** |
| COMM | 54 minimal data-blocked | **(EMPTY — controller fills from comm_energy/comm_metal lane outputs)** |
| 6F | 0 NOT_RUN_DATA_ABSENT | **(EMPTY)** |

The CROSS lane itself proposes **0 new families, 0 new identities** — this
lane builds court infrastructure and consolidates census/ranking only.

## 5. Standing census law carried unchanged

- NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER end-to-end (FINAL_RANKING §4;
  launch §7).
- Placebo-budget question remains open at the owner (CENSUS_FINAL §5):
  multi-seed-as-identities ⇒ ≥1,800 placebo identities for the 18 returned
  legs alone; multi-seed-as-diagnostics ⇒ program-wide single-seed
  publication law until funded. No side taken.
- Fees: MODELED COST, UNDER REVIEW until a new A7 (launch D2 — the hardest
  dependency; every cost number in every census row is contingent on it).

— End CENSUS_DELTA.md. Denominator planning only; nothing registered,
scheduled, or recommended; every number traces to a lane artifact or is
labeled INFERENCE.
