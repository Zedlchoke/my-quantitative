# PLAN — SOCCER-1X2-POSTHOC-ANALYSIS-V1 (POST-HOC DESCRIPTIVE feasibility of the closed B1/V1 model for 1X2 odds; $0, zero scored cells)

- cycle_id: SOCCER-1X2-POSTHOC-ANALYSIS-V1 · asset: shared · ACTIVE_LIGHT ·
  **budget 0/0 by law** (descriptive analysis of an ALREADY-EXPOSED window;
  computes no new claim, opens no verdict) · GO phrase registered, NOT typed:
  `GO SOCCER 1X2 POSTHOC ANALYSIS V1 DESCRIPTIVE`.
- Owner authority 2026-10-09 (this chat): clarify whether the recorded
  SOCCER-INTL-WINPROB-SCORED-V1 (TERMINAL 21ae40f8) model can serve 1X2 odds
  use. Every number this cycle emits carries the label
  **POST_HOC_DESCRIPTIVE_EXPOSED_WINDOW**. The closed LL/RPS verdicts
  (B0 1.049906 / B1 0.912037 / V1 0.909325 on chrono OOS [2001,2023),
  n=20,708; slices competitive n=13,563, friendly n=7,145) are **unchanged
  history** — this cycle never re-opens, re-weights or re-interprets them. No
  betting/edge language anywhere; accuracy and log-loss are calibration
  descriptors, never evidence of exploitable edge.

## Frozen inputs (read-only)

- Corpus `~/.my-quantitative-data/soccer-intl-winprob-prep-v1/corpus/`
  (results.csv sha256 df35268f… + shootouts.csv + former_names.csv; CC0-1.0).
- Engine bytes: `research/control/SOCCER-INTL-WINPROB-SCORED-V1/lanes/
  L_ENGINE/engine/` at branch `orca/soccer-intl-winprob-scored-v1-integration`
  (engine byte-unchanged since the scored run per TERMINAL_REPORT; extract
  with per-file sha256 provenance pins; the TERMINAL cycle itself stays
  read-only).
- Arm configs of record: `prego/SELECTION.json` (B1 K=48, ν=0.6, HCA=65;
  V1 per co-selected HCA) + recorded metrics `runs/SCORED_postgo-1.json`.

## Tasks

1. **REPRODUCTION GATE (before any analysis number exists):** drive the frozen
   engine's `DayBatchReplay` with `score_windows=[("chrono_oos",
   "2001-01-01","2023-01-01")]` ONLY — the held-out window is never scored,
   never emitted, never opened (its ERRATUM partial-revelation status stands;
   2023+ is NOT a clean holdout). Gate: pooled + slice LL/RPS for B0/B1/V1
   must equal the recorded `SCORED_postgo-1.json` windows block exactly
   (float-exact) — mismatch ⇒ **NOT_RUN_REPRODUCTION, halt**.
2. **POST-HOC DESCRIPTIVE ACCURACY:** per arm (B1, V1; B0 for context):
   frequency with which the highest-probability outcome equals the realized
   corpus label, by ALL / friendly (tournament == "Friendly") / competitive,
   and per calendar year 2001–2022; plus mean predicted max-probability and
   hit-rate by probability decile (calibration-flavored descriptors). All
   tables carry the POST-HOC label + reproduction-gate digest.
3. **CORPUS-TARGET vs 90-MINUTE 1X2 GAME-BY-GAME AUDIT:** deterministic
   classification of all 20,708 OOS rows: corpus-label DRAW ⇒ 90-min outcome
   DRAW with certainty (level after 90 in both the draw and the
   shootout-decided cases) ⇒ COMPATIBLE_CERTAIN; corpus-label H/A ⇒ 90-min
   outcome is UNDERDETERMINED from the corpus alone (regulation-decided H/A
   vs level-after-90-then-ET-decided are indistinguishable) ⇒
   **NOT_RUN_TARGET_NO_ET_FLAG**; stratified by tournament structure (major
   final-tournament knockout rounds and named two-leg playoffs where extra
   time is structurally possible, vs group/qualifier/friendly where it is
   not expected) with counts disclosed. Record: compatible counts, ambiguous
   counts, and the law that resolving ambiguity requires an external 90-minute
   results source. The corpus target law "90/120-min recorded score,
   shootout winners never modify the target" is quoted verbatim next to the
   1X2 market's 90-minute convention.
4. **PROSPECTIVE SOURCE SURVEY (documentation only, $0, no API calls, no
   standing-key use):** future men's-international fixtures; 90-minute
   results with explicit ET/shootout flags; historical AND future 1X2 odds
   with pre-match snapshot timestamps. Per source: rights (primary quote),
   cost, coverage, timestamp semantics, 90-min convention, join certainty.
   Classify Class A/B/C per the WNBA-ODDS-DISCOVERY qualification law.
   Anything unqualified ⇒ NOT_RUN_SOURCE / NOT_RUN_ODDS language, never
   assumed coverage.
5. Controller artifacts + comparison-table inputs; verifier re-derives the
   accuracy tables and audit counts from bytes.

## Boundaries

$0; no purchases; no accounts; no S1; no push/merge/rebase; registry via
researchctl CAS; corpus/ledger/engine of the TERMINAL cycle read-only; no
modification of any other cycle; heavy lock for the replay (short, bounded);
missing evidence = NOT_RUN_*; worktree
`.worktrees/soccer-1x2-posthoc-v1/integration` on
`orca/soccer-1x2-posthoc-v1-integration`; artifacts under
`research/control/SOCCER-1X2-POSTHOC-ANALYSIS-V1/`.

## Terminal outcomes (negative-first)

**POSTHOC_DESCRIPTIVE_COMPLETE** (reproduction gate PASS, tables + audit +
survey delivered; no verdict changed) | NOT_RUN_REPRODUCTION (engine does not
reproduce recorded metrics exactly) | NOT_RUN_RESOURCE_CONFLICT |
BLOCKED_TOOLING | TECHABORT_*. The GO phrase stays unconsumed.
