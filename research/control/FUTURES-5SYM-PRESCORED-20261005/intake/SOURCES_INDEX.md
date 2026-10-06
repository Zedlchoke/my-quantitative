# SOURCES_INDEX — LANE-INTAKE, round FUTURES-5SYM-PRESCORED-20261005

- Maps every dossier/round relevant to NQ, 6E, 6B, 6J, 6A → what it proves,
  per-symbol relevance, canonical path, and top-level sha256 of its 2–3
  load-bearing files. **All sha256 below were computed by THIS lane** with
  `shasum -a 256` at HEAD `ffed828f73fa19fa0ff4aee3ac1b441909a43940` unless
  marked otherwise (out-of-tree artifacts cannot be hashed here and are marked
  NOT_OBTAINED-locally).
- Ancestry facts (verified by this lane with `git -C <worktree> ...`):
  - `b583c33a` (branch `prep/futures-behavior-10syms-20261002`, commit
    "FUTURES-P3-QUARANTINE-20261004: P3 containment + fixes…") is **NOT an
    ancestor** of this branch (`git merge-base --is-ancestor` exit 1). Its
    captures stay **quarantined / never-read** (owner D1 pending; dispatch
    absolute_prohibitions).
  - `FUTURES-DATA-10SYMS-V1` is **not present in this worktree**; it is cited
    as a root-readonly corpus at "root main `d8cf8eca`"
    (K6GATE DISPATCH_MANIFEST resources.root_readonly).

| dossier / round | what it proves | per-symbol relevance | canonical path | load-bearing file sha256 (this lane) |
|---|---|---|---|---|
| **FUTURES-DATA-10SYMS-V1** | the 10-symbol data acquisition round: Databento GLBX O1M purchases, S1 identity per instrument, request packets; basis of the av1trim corpus lineage | all 5 (+5 non-mission) — source of raw vendor panels consumed read-only by every later round | **NOT in this worktree**; cite root main `d8cf8eca` (per K6GATE DISPATCH root_readonly). Local hash: NOT_OBTAINED-locally | n/a (out of tree) |
| **FUTURES-BEHAVIOR-10SYMS-PREP-20261002** (P3-behavior round) | 10-symbol behavior research; its final commit `b583c33a` IS the P3-QUARANTINE containment commit (QUARANTINE_NOTICE; 0225b3c2 preserved verbatim). Directory content at earlier commits IS in this branch's ancestry; **round tip b583c33a is NOT an ancestor**; P3-obtained captures quarantined, never read (owner D1 pending) | all 5: carried D1–D7 origin; Q5 sibling captures carry the per-use-reverify condition; databento request packet = S1 identity lineage | `research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002/` (committed pre-P3 content); tip `b583c33a` not in ancestry | REPORT_VI.md `0c3aeb6a…be0d`; DATABENTO_REQUEST_PACKET.md `69ad8032…07d0a` |
| **FUTURES-OVERNIGHT-PREP-20261003** | baseline hypothesis census over 6 symbols (families, ES 36>24 block, no-cap findings for NQ/6J/FX); fee erratum wave (glued-superscript adjudication; corrected fees) — the CENSUS_FINAL that IDENTITY_TABLES draws its arithmetic from | NQ 4 families; 6E/6B FX census 648 no-ceiling; 6J/6A census ~29–36 / AF1+AF3; ES cap context | `research/control/FUTURES-OVERNIGHT-PREP-20261003/` | synth/CENSUS_FINAL.md `0eabce3d…f5c85`; synth/REPORT_VI.md `b3bb2d49…bc69d`; fees_erratum/source/FEES_CORRECTED.md `006d6372…d1bef` (== packet pin) |
| **FUTURES-DEEPRESEARCH-V2-20261003** | deep per-symbol v2 dossiers (~40–50 headline numbers each, A7-recomputed), roll-spread era physics, session anatomy, event archives (NQ_a4_events, 6E_a4, 6J_a2…), the six `_cache/` panels — **NQ_cache is DEPRECATED for consumption** (v2 defects measured; superseded by cache_v3) | NQ (v2 cache deprecated; a4 event archive live), 6E/6B/6J/6A (annotated panels + identity packs of record) | `research/control/FUTURES-DEEPRESEARCH-V2-20261003/` | REPORT_VI_DEEPRESEARCH_V2.md `0e6b04e7…bbe4`; dossiers_v2/NQ_DEEP_v2.md `d3cf621c…e32b`; dossiers_v2/6J_DEEP_v2.md `ef95ad8d…b92f` |
| **FUTURES-ES-V1-PACKET** (`SPEC_PB1_ES.md` = THE SPEC precedent) | the executable-specification format precedent (FREEZE-READY r3; universe/data-contract/roll-T-5-PIT/session-era/cost/fold/gate structure; ES cap 24 identity table; single-seed C1 law) that all futures packet drafts must mirror; two-key GO gate precedent via PLAN + audit | ES only directly (registered parent PB1; out of this round's scored scope) — but its structure is the binding template for any NQ/6E/6B/6J/6A packet | `research/control/FUTURES-ES-V1-PACKET/` | SPEC_PB1_ES.md `445f7499…b7073` (== lane pin, re-verified); PLAN_futures_es_v1.md `06140882…a06b` |
| **FUTURES-SIX-READINESS-20261004** | the four-lane readiness repair round: NQ alias-hole rebuild (cache_v3), 6E/6B calendar closure, 6J identity/orientation, 6A tick-era + roll measurement; VERIFY-A7READY; **OWNER_DECISIONS D1–D12 = the decision source of record**; SIX_SYMBOL_CENSUS index | all 5 (primary readiness evidence) | `research/control/FUTURES-SIX-READINESS-20261004/` | synth/OWNER_DECISIONS.md `d14e436f…ad93`; synth/SIX_SYMBOL_CENSUS.md `7c006db6…fe35`; nq/DATA_READINESS_NQ.md `fc14b69c…c097`; fx_eb/DATA_READINESS_6E.md `c7ea807b…cd05`; fx_eb/DATA_READINESS_6B.md `555ab253…c4cf7`; fx_ja/DATA_READINESS_6J.md `2e322ef2…3ef7`; fx_ja/DATA_READINESS_6A.md `28ea9093…9a8e` |
| **FUTURES-SIX-ADOPT-PREP-20261004** — incl. **NQ v3 adoption + v2 deprecation records** | made D8/D9 CONCRETE: `adopt/6A_TICK_ERA_LAW.md` (PROPOSED), `adopt/CEASE_GUARD_STANDARD.md` (PROPOSED), `adopt/CACHE_V3_PIT_STATEMENT.md` (canonical-CANDIDATE; PIT_CLEAN_BY_CONSTRUCTION), `adopt/DEPRECATION_NQ_V2_CACHES.md` (v2 SUPERSEDED — deprecation in force), `adopt/cache_v3_hashes.json` (all v3 file hashes); the owner launch packet CYCLE_LAUNCH_DRAFT + machine mirror open_decisions_dependency.json; cal_eb/cal_janq calendar closure (6B 2024Q3–2026Q4 cells; absence inventories); fee_es A7 execution packet; hypo/HYPOTHESES_R2 (RMM Role-B +4 law, 6J 29–36+4, AF4 0) | NQ (adoption records), 6A (tick law), 6J/6A (cease-guard standard), all (launch packet) | `research/control/FUTURES-SIX-ADOPT-PREP-20261004/` | adopt/D8_D9_DECISION_SHEET.md `b1d6079f…f8ae`; adopt/DEPRECATION_NQ_V2_CACHES.md `29790cd1…16b0`; adopt/cache_v3_hashes.json `6cad549d…894d3`; packet/CYCLE_LAUNCH_DRAFT.md `bc2b6488…bcb03`; packet/open_decisions_dependency.json `7229fd31…7327`; cal_eb/CAL_EB_REPORT.md `25678890…ef77`; cal_janq/CAL_JANQ_REPORT.md `066c1217…1038` |
| **FUTURES-SIX-SCORED-GATE-PREP-20261004** | executed the fee A7 (AUTHORIZED_WITH_FINDINGS, 0 HIGH/CRIT); CAL-CLOSE (D5 CPI pin obtained 2026-02-13; NQ Good-Friday advisory class-level; 14 FX residuals CLOSED_PROVEN_ABSENT); IDENTITY_TABLES budget options (ES-0..4, NQ-A..D 22/29/36/43, J-A..C 29/36/33–40, FX-A..C 44/66/96 CONV-D, clock-shadow (a)/(b), placebo slot); OWNER_DECISION_PACKET OD-1..OD-7; **COST_FREEZE_ERRATUM (correction of record: 1.38 evidence-settled; stale 21.006/33.506/46.006 never consumable; dual-variant table; CYCLE-1 BLOCKED_COST_FREEZE)** | all 5 (cost/ceiling/calendar closure) | `research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/` | synth/COST_FREEZE_ERRATUM.md `cf83bc2d…9ae8`; synth/OWNER_DECISION_PACKET.md `3366776e…423b`; synth/CYCLE_PROPOSAL.md `e8e45492…6550`; budget/IDENTITY_TABLES.md `750858ab…f6e6`; fee_a7/A7_FEE_REAUDIT.md `2c1095d6…11ad`; cal_close/CAL_CLOSE_REPORT.md `338cf4e8…a56f`; cal_close/RESIDUAL_INVENTORY.md `29fea296…f81dc`. NOTE: shortlist/** is consumed only through the K6GATE stale-cost erratum (F-4/F-5/F-6 superseded) |
| **FUTURES-TEN-HYPO-PREP-20261004** | 10-symbol candidate census + dossiers + ancestry court + outcome-blind ranking; OWNER_DECISION_PACKET OD-1..OD-4 (EXPWITCH admission; commodity data path; 6J ceiling + RMM DC §1.3; D1–D12 pointer); EXPWITCH +7/+12 per leg, MDE 23.6bp ES / 38.7bp NQ power honesty; ES/NQ hypothetical aggregates 43 (ESNQ-lane basis) / 67 (PB1-inclusive) | NQ + ES legs of EXPWITCH (both later DEAD at F5-K6); 6J ceiling slot; carried family scores | `research/control/FUTURES-TEN-HYPO-PREP-20261004/` | synth/OWNER_DECISION_PACKET.md `4fb20a63…7cf9`; synth/CANDIDATE_CENSUS_10SYM.md `47dc0e82…0006`; synth/OUTCOME_BLIND_RANKING_R3.md `ae29254a…9ea2` |
| **FUTURES-K6GATE-PREP-20261004** | pre-registered 0-cost anatomy gates: NQ F1/F2 PASS + F3 rebuild DONE + EXPWITCH-NQ FAIL (35/66 vendor gaps); ES EXPWITCH FAIL (T3 1.220<1.25) + F1/F2 PASS; FX-F1 court census PASS (6E 1,362 / 6B 1,342 ≥500 triggers; MDE-at-n ≈3.5/4.2bp); 6B gap-std MEASURED; tick constancy CONSTANT 6E/6B; JF1-K3 ANCHOR_INSENSITIVE_AT_45MIN; RMM mode ledger (6E 22/5, 6B 23/4, 6J 19/8 exact 27/27, 6A 21/6); 6A D-2 era cost audit; **SHORTLIST_STALE_COST_ERRATUM (supersedes six-gate shortlist residue)** | all 5 (gate verdicts + refreshed anatomy) | `research/control/FUTURES-K6GATE-PREP-20261004/` | synth/SYNTHESIS_K6.md `03a8e77e…8237`; synth/SHORTLIST_STALE_COST_ERRATUM.md `7fe438c2…72a0`; fx_eb/tick_constancy_6e6b.json `b6b9927e…efca2`; fx_ja/aud_d2_tickera.json `14426cfb…3729`; nq/NQ_K6_GATES.md `364f0412…2781`; REPORT_VI.md `d55d00a5…a83c` |
| **FUTURES-P3-QUARANTINE-20261004** (origin round of D1–D7) | P3 containment + permitted continuation (Q1–Q6 lanes): QUARANTINE_NOTICE; SAFE_BLOCKER_MATRIX (28 P3 cells NOT_OBTAINED/PENDING); Q5 permitted-route captures (ES 2026 session times, FX 2023-25 28/48, GC/SI 2024-26); OWNER_DECISIONS D1–D7 separated | all 5: D1 governs P3-capture admissibility; D2–D7 carried | **NOT in this worktree**; tip = `b583c33a` on `prep/futures-behavior-10syms-20261002`, NOT an ancestor; consumed here ONLY via carried restatements in SIX-READINESS/OWNER_DECISIONS.md | out-of-tree; carried text pinned via `synth/OWNER_DECISIONS.md d14e436f…ad93` |
| **FUTURES-5SYM-PRESCORED-20261005** (this round) | owner instruction 2026-10-05: PREP + hypothesis research on the 5 symbols; P5- namespace law; lanes INTAKE/NQ/FXEB/FXJA/EXEC/HYPO/CALCOST + wave-2 SYNTH/VERIFY | all 5 | `research/control/FUTURES-5SYM-PRESCORED-20261005/` | dispatch/DISPATCH_MANIFEST.json `f9e7b400…9ca7a` |
| **FUTURES-DATACONTRACT-QUAL-V1** (supplementary) | data-contract qualification (cost authority table §1.7: spread close-proxy 6E/6B 18.75, 6A 20, 6J 25; BBO NOT_RUN) + PLAYBOOKS draft + its own owner decision packet | all 5 (cost-authority table cited by FXJA-K6) | `research/control/FUTURES-DATACONTRACT-QUAL-V1/` | DATACONTRACT_QUALIFICATION.md `df175a2d…6e3fd` |
| **FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003** (supplementary) | cme_cal/nq_es expiry coverage (nq_es 68/68 pointer consumed by NQ readiness), events_bbo_coverage, DEEPFOUR fee erratum wave | NQ (expiry calendar), ES/NQ fee context | `research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/` | cme_cal/nq_es/nq_cal_coverage.json `ad7f4b3a…bf93` (matches NQ_K6_GATES citation) |
| **DAILY-EXPLORATORY-V1** (gate precedent) | the two-key GO gate precedent: `auth/GO_RECORDED.json` (exact-phrase consumption format adopted by CYCLE_LAUNCH_DRAFT §6/§7) | all (gate mechanics) | `research/control/DAILY-EXPLORATORY-V1/` | auth/GO_RECORDED.json `ef88fd80…07df` (== packet pin) |

## Rounds NOT in this branch's ancestry (verified)

1. **`b583c33a`** — FUTURES-P3-QUARANTINE-20261004 (tip of branch
   `prep/futures-behavior-10syms-20261002`). `git merge-base --is-ancestor
   b583c33a HEAD` → exit 1 (NOT an ancestor). Its captures are
   **quarantined / never-read** (owner D1 pending; dispatch absolute
   prohibition "no reads of P3-quarantined captures"). The pre-P3 content of
   FUTURES-BEHAVIOR-10SYMS-PREP-20261002 is committed in this tree and is
   readable; the P3-era additions (0225b3c2 content, Q-lane quarantine
   artifacts) are not consumed by this lane.
2. **FUTURES-DATA-10SYMS-V1** — round content not in this worktree; cited
   read-only at root main `d8cf8eca` (K6GATE DISPATCH_MANIFEST
   `resources.root_readonly`). No local hash possible.
3. **ES finalize cycle** — worktree `futures-es-reg` / branch
   `prep/futures-es-reg-20261004` is READ-ONLY evidence per dispatch
   (extract via `git show` only; never write there). Out of this round's scope.

## Cross-checks performed by this lane (all PASS)

- `SPEC_PB1_ES.md` sha `445f7499…b7073` == six-adopt packet §9 pin.
- `FEES_CORRECTED.md` sha `006d6372…d1bef` == DATA_READINESS_6E/6B pins.
- `OWNER_DECISIONS.md` `d14e436f…ad93`, `SIX_SYMBOL_CENSUS.md` `7c006db6…fe35`,
  `six_symbol_census.json` `6296df9e…9107`, and all five DATA_READINESS_*.md
  hashes == CYCLE_LAUNCH_DRAFT §9 pins.
- `COST_FREEZE_ERRATUM.md` sha `cf83bc2d…9ae8` == NQ_K6_GATES citation.
- `GO_RECORDED.json` sha `ef88fd80…07df` == packet pin.
- `nq_cal_coverage.json` sha `ad7f4b3a…bf93` == NQ_K6_GATES citation.

— End SOURCES_INDEX.md.
