# PLAN — WINPROB-NG-PREP-V1 (next-gen win-prob research PREP, $0)

- cycle_id: WINPROB-NG-PREP-V1 · asset: shared · ACTIVE_LIGHT, budget 0 scored, NO GO phrase
- owner authority 2026-10-05: research/PREP + bookkeeping ONLY — explicitly NOT a typed GO
  for any new scored cycle and NOT authority to run scored on real outcomes. No S1/paper/
  live/push/merge/accounts/keys/purchases. Futures threads untouched. Frozen sources,
  results, and ledgers of the TERMINAL cycles NBA-WINPROB-SCORED-V1 / NFL-WINPROB-SCORED-V1
  are immutable history — this cycle never edits them; 2016+ extension of the old NBA
  folds is NOT_RUN by definition (a NEW cycle would carry any new-window evaluation).

## Tasks (owner round 2026-10-05)

1. CLOSEOUT RECONCILIATION (done at bootstrap, recorded here): registry typed fields of the
   two scored cycles reconciled from bytes. Fixed via legal CAS transition: lifecycle
   ACTIVE_LIGHT→TERMINAL; go_phrase_state REGISTERED_NOT_CONSUMED→DEAD (P-8 writer-enforced
   at close). NOT fixable by any existing CAS path: budget.used (truth = 9 per TRIAL_LEDGER,
   P-9) and s0. BLOCKER artifact + TESTED tool-fix proposal (researchctl/governance patch +
   unit tests) delivered in lanes/T1_CLOSEOUT/ — proposal only, NOT applied to the root tool
   without owner decision. The ledger is never edited to legitimize anything.
2. Lane A — NBA post-2015 $0 sources: rights-verified candidates only (license/ToS text,
   provenance, API/key/rate limits, measured coverage, ID crosswalk to 538 nbaallelo).
   hoopR/nflverse-family releases are the primary candidate to verify. balldontlie stays
   BLOCKED_NO_KEY (owner-only signup). Download ONLY if rights clear; data outside git with
   URL/attribution/hash/version/pull-time.
3. Lane B — WNBA independent branch: source inventory (official + community, e.g.
   wehoop/nflverse-family), rights + upstream, coverage years, games/box/PBP availability,
   as-of schedule, franchise renames, neutral-site, playoffs, tie/cancel/forfeit, timezone,
   injury/lineup PIT. Sample/full download ONLY with verified rights; audit rows/IDs/
   missingness/mirror/chronology/hash/operating cost. PASS/FAIL/NOT_RUN verdict for win-prob
   modeling. No NBA data/hypotheses used as WNBA evidence.
4. Lane C — new mechanisms/features (NBA + NFL, + WNBA if data sufficient): baseline = the
   strong own-Elo already evidenced; propose NEW mechanisms with clear domain basis, $0
   feature source + rights + publish-timestamp story, falsifiers, coverage, leakage risk.
   Pre-game-knowable only; no post-hoc re-grid of K/HCA/rest/form on the old 7 test seasons;
   no 538 forecast / closing odds / current-game box scores. Train-only selection +
   validation design, small frozen trial budget, walk-forward OOS on NEW seasons, log loss
   primary + Brier/calibration, paired uncertainty, Elo baseline, negative controls,
   playoffs separate.
5. Lane D — independent verifier (after controller synthesis; never repairs).

## Artifacts
lanes/T1_CLOSEOUT/ (blocker + tool-fix proposal + tests) · lanes/A_NBA_POST2015/ ·
lanes/B_WNBA/ · lanes/C_MECHANISMS/ · lanes/D_VERIFY/ — each with handoff JSON
zcode_orch_v3_handoff@1. New data (if any) outside git under ~/.my-quantitative-data/.

## Terminal outcomes (negative-first)
PREP_COMPLETE_PENDING_OWNER_CYCLES | BLOCKED_DATA_RIGHTS | BLOCKED_TOOLING (if the registry
sync proposal is rejected and closeout fields must stay stale) | TECHABORT_*.
Any new scored cycle requires fresh registration + freeze + A7 + owner GO at its own gate.
