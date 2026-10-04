# PREP_SUMMARY — NBA-WINPROB-PREP-V1 controller synthesis (2026-10-04)

- cycle: NBA-WINPROB-PREP-V1 (ACTIVE_LIGHT, budget 0 scored cells, no GO phrase by law)
- branch: orca/nba-winprob-prep-v1-integration · base: main @ d8cf8eca
- root control-plane commit: c7611803 (plan + registry row + projection)
- owner directive: PREP + implementation authorized, explicitly NOT a typed GO (2026-10-04)

## Gate verdicts

- G0 bootstrap: PASS (plan, registry, worktree, lane dirs).
- G1 data authority: PASS_WITH_CONDITIONS — lane A memo (lanes/A_rights_audit/RIGHTS_MEMO_NBA.md).
  538 nbaallelo.csv: CC BY 4.0, $0, no signup, sha256-verified download; internal-research-only
  with attribution + provenance disclosure; restrictive reading documented; owner veto retained.
  balldontlie: BLOCKED_NO_KEY (owner-only signup; free tier confirmed Teams/Players/Games only,
  5 req/min). NBA.com/Stats: FAIL. Sports Reference direct: FAIL for ML (ToU 5(11)).
- G2 dataset audit: PASS — lane B (lanes/B_dataset/DATASET_AUDIT.md) + controller build.
  63,157 games / 69 seasons 1947..2015, data ends 2015-06-16; mirror integrity 0 violations;
  53 lineages, 0 identity collisions; 12 team-date doubles (6 dates).
- G3 protocol frozen: PASS — lane C (lanes/C_protocol/PROTOCOL_EVAL.md): 3 hypotheses (H1 dynamic
  strength / H2 HCA / H3 rest), 9-arm frozen budget, walk-forward, metrics, PASS/REJECT gates,
  negative terminal outcomes, NOT_RUN register.
- G4 implementation: PASS — nba_winprob/ package; 20/20 synthetic fixture tests PASS (golden
  hand-computed Elo incl. HCA=0.640065 correction, no-lookahead mutation property, same-day
  exclusion law, doubleheader leg-exclusion, rename continuity, static leakage grep, deterministic
  damped-Newton logistic, seeded block bootstrap). Real-data build executed as deterministic
  transform ONLY (no metric computed anywhere): derived games/lineages/participants/f538_reference
  + features.csv for the 4 B1 arms. Raw + derived bytes live OUTSIDE git under
  ~/.my-quantitative-data/nba-538-v1/ (ATTRIBUTION.md + manifests carry sha256 + license).
- G5 verification: see lanes/D_verify/VERIFICATION_REPORT.md (landed after this summary).

## Controller cross-checks and corrections (chat prose never used as authority)

1. AS-OF LAW reconciliation: lane C froze "strictly-before date + date-batched updates"
   (sec0/sec2); lane B's schema proposed (date, gameorder) tie-breaking. Controller adopted
   C's STRICTER law: same-day games never inform each other, updates apply after each date
   batch. The 12 team-date-double games lose leg-1 information for leg-2 — conservative,
   provably leakage-free, deterministic. B's ordering survives only as file/state ordering.
2. SAME-PAIR-DATE COUNT CORRECTED: lane B schema asserted pair-repeats == 6; controller
   measured 5 same-pair days (4 protested-game completions + genuine 1954-03-08 MLH
   doubleheader) + 1 team-double day with different opponents (2008-03-07 Hawks & Heat).
   B's "6" is the team-double DATE count. Build asserts the measured 5 + 12.
3. TEST SEASONS FROZEN: C's placeholder rule ("final 7 complete seasons") resolves to
   2009..2015 (8,956 games; 8,369 RS + 587 PO), train 1947..2008 — data ends 2015-06-16,
   NOT 2023 as C assumed; C's assumption 10.2 corrected accordingly.
4. ELO INIT: C froze 1500 (B suggested mirroring 538's 1300 expansion convention — frozen
   protocol wins; uniform 1500 is the documented conservative choice).
5. BUBBLE SENSITIVITY N/A: C's sec8.4 segment [2020-08, 2020-10] cannot exist in data ending
   2015; recorded as N/A (no COVID era in this file). 2012 lockout season sits inside TEST —
   kept, documented (lane B A12).

## Exact stop point (owner's instruction)

No typed GO exists for any scored evaluation (owner 2026-10-04 explicitly NOT a GO; this cycle
registers none and has budget 0). Everything up to the owner gate is DONE:
rights memo, audited dataset, frozen protocol, tested implementation, frozen derived inputs.
NOT_RUN by construction: any log loss / Brier / calibration on real outcomes; any injury or
odds feature (NOT_RUN_PIT); any PnL/betting language.

Successor path (owner decisions): (1) register NBA-WINPROB-SCORED-V1 inheriting
PROTOCOL_EVAL.md sections 2-6, 9 verbatim + the frozen split 2009..2015; (2) A7 prelaunch;
(3) owner types at that cycle's own gate the phrase:
    GO NBA WINPROB SCORED V1 EVALUATION

## Incident log (honest)

- Prior-turn (pre-cycle) plan-mode hook denials: 3 compound bash commands + researchctl
  python execution were refused by the read-only guard during the feasibility study; re-run
  simplified/after mode change. No repo state was affected.
- Lane A reported an out-of-band truncated pseudo-tool-output arriving via the chat channel
  mid-audit; treated as untrusted, all quotes re-fetched first-party (see their memo sec1).
- Development test fixes before any commit: golden literal 0.640175→0.640065 (test
  arithmetic, engine correct); feature rows briefly embedded the label (home_win) — removed
  (features must be label-free); reliability-bin tuple indices; Newton logistic needed
  damping (line search) for separable fixtures; two vestigial loops removed after review.
- Background heredoc script self-terminated (accidental O(n^2)); killed, rerun clean O(n).
  No artifacts depended on it.
- No S1 access, no orders, no purchases/trials, no accounts/keys, no push/merge, no other
  cycle touched. Heavy lock never acquired (all work light).
