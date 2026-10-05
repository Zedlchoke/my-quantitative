# DISPATCH — Lane D · INDEPENDENT VERIFIER (task nbang-d-verify, cycle NBA-WINPROB-NG-PREP-V1)

ROLE: quant-auditor (A7-equivalent, fresh context). Runs ONLY after controller synthesis of
lanes A/B/C. Writes ONLY in this lane directory. NEVER repairs anything, never asks lanes
how to pass; recompute from bytes; hunt for disconfirmation.

ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nba-winprob-ng-prep-v1/integration
BRANCH: orca/nba-winprob-ng-prep-v1-integration (no commits by you)
CYCLE: NBA-WINPROB-NG-PREP-V1 · ACTIVE_LIGHT · budget 0 scored · NO GO phrase

ALLOWED PATHS (write): lanes/D_VERIFY/** only. FORBIDDEN: everything else (all other lanes,
plans/**, research/control/**, any frozen artifact of any cycle, registry files, push/merge/
commit, credentials, purchases).

REQUIRED INPUTS (read-only): lanes/A_DATA/**, lanes/B_MECHANISMS/**, lanes/C_PROTOCOL/**
(landed artifacts), lanes/DISPATCH/**, the plan (plans/PLAN_nba_winprob_ng_prep_v1.md),
the corpus at ~/.my-quantitative-data/nba-hoopr-v1/ + nba-ng-prep-v1/, registry at root
plans/CYCLE_REGISTRY.json (read-only).

DELIVERABLE (lanes/D_VERIFY/VERIFICATION_REPORT.md + handoff_D.json) — checks, each PASS/
FAIL/NOT_RUN with re-measured evidence:
1. Bytes vs claims: re-run the load-bearing counts of lane A (rows per season file, unique
   game_id, dedupe-law counts on ≥3 sampled seasons, tip-UTC canonicalization on ≥9 sampled
   rows incl. DST boundaries); re-hash ≥3 downloaded files; verify BDL cross-check artifacts
   (request count ≤25, throttle evidence, no key value anywhere).
2. Rights: license/attribution chain re-verified from the artifacts (CC BY 4.0 producer +
   MIT release store; BDL usage is cross-check-only and key-handling is fail-closed).
3. PIT: every feature verdict in PIT_AUDIT_NBA.md checked for pre-game knowability;
   injury/roster stays NOT_RUN_PIT unless evidence; post-game fields never pre-game features.
4. Mechanisms/protocol: falsifiers frozen and CI-based; negative controls present per
   hypothesis; no banned source (538 forecasts, closing odds, current-game box) anywhere;
   B1* constants verbatim; no re-grid of K/HCA/rest/form on 2009–2015 anywhere.
5. Trial accounting: 0 scored outcomes in this cycle (no sklearn/metrics/fit/predict on real
   outcomes anywhere in lanes/), budget 0/0, no GO phrase registered/consumed.
6. Boundaries: no S1 references; no push (branches have no upstream); no credentials;
   NFL-WINPROB-NG-PREP-V1 + WINPROB-NG-PREP-V1 + terminal cycles untouched; registry row of
   this cycle coherent (lifecycle/branch/worktree/head vs measured).
7. Defects table (severity) + final verdict VERIFICATION_PASS | VERIFICATION_FAIL.
8. handoff_D.json — schema zcode_orch_v3_handoff@1 at lanes/D_VERIFY/handoff_D.json
   (task_id "nbang-d-verify", commit_sha "NOT_COMMITTED_CONTROLLER_LANDED", ...).

STOP CONDITIONS: lane artifacts missing → NOT_RUN with paths listed; evidence contradicts a
claim → FAIL that check with the measured numbers (never repair).
