# DISPATCH — Lane D · INDEPENDENT VERIFIER (task wbap-d-verify, cycle WNBA-WINPROB-PREP-V1)

ROLE: quant-auditor (A7-equivalent, fresh context). Runs ONLY after controller synthesis of
lanes A/B/C. Writes ONLY in this lane directory. NEVER repairs; recompute from bytes; hunt
for disconfirmation.

ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/wnba-winprob-prep-v1/integration
BRANCH: orca/wnba-winprob-prep-v1-integration (no commits by you)
CYCLE: WNBA-WINPROB-PREP-V1 · ACTIVE_LIGHT · budget 0 scored · NO GO phrase

ALLOWED PATHS (write): lanes/D_VERIFY/** only. FORBIDDEN: everything else (all other lanes,
plans/**, research/control/**, any frozen artifact of any cycle, registry files, push/merge/
commit, credentials, purchases).

REQUIRED INPUTS (read-only): lanes/A_DATA/**, lanes/B_MECHANISMS/**, lanes/C_PROTOCOL/**
(landed artifacts), lanes/DISPATCH/**, the plan (plans/PLAN_wnba_winprob_prep_v1.md), the
corpora at ~/.my-quantitative-data/wnba-v1/ + wnba-prep-v1/, registry at root
plans/CYCLE_REGISTRY.json (read-only).

DELIVERABLE (lanes/D_VERIFY/VERIFICATION_REPORT.md + handoff_D.json) — checks, each PASS/
FAIL/NOT_RUN with re-measured evidence:
1. Bytes vs claims: re-run load-bearing counts of lane A (per-season rows 1997–2026 both
   sides, unique ids, filter-law counts on ≥3 sampled seasons incl. the 2018 forfeit row
   and 2026 TBD placeholders, timestamp canonicalization on ≥9 sampled rows, rename-map
   boundaries on ≥4 franchise events); re-hash ≥3 corpus/new files.
2. Rights: license/attribution chain re-verified (CC BY 4.0 badge + MIT release store,
   nflverse-family pattern; wnba.com/stats/SR/balldontlie exclusions intact); no direct
   scraping occurred (no scraper code run against those hosts).
3. PIT: every feature verdict checked for pre-game knowability; post-game DNP/starter
   fields never pre-game features; injury/lineup NOT_RUN_PIT unless cleared; rolling-window
   features use strictly-prior-game inputs.
4. Independence law: NO NBA data/parameter/verdict presented as WNBA evidence anywhere in
   the lanes (citations as context allowed; imports are violations).
5. Mechanisms/protocol: falsifiers frozen and CI-based; negative controls present; banned
   sources absent (538 forecasts, closing odds, current-game box, MOV re-grid, additive
   logistic-over-Elo); arm budget ≤9 with B0 + fresh WNBA B1 mandatory; era handling frozen.
6. Trial accounting: 0 scored outcomes (no sklearn/metrics/fit/predict on real outcomes in
   lanes/), budget 0/0, no GO phrase registered/consumed.
7. Boundaries: no S1 references; no push; no credentials; foreign cycles (NFL-NG-PREP live
   chat, WINPROB-NG-PREP-V1, terminal cycles) untouched; registry row coherent.
8. Defects table (severity) + final verdict VERIFICATION_PASS | VERIFICATION_FAIL.
9. handoff_D.json — schema zcode_orch_v3_handoff@1 at lanes/D_VERIFY/handoff_D.json
   (task_id "wbap-d-verify", commit_sha "NOT_COMMITTED_CONTROLLER_LANDED", ...).

STOP CONDITIONS: lane artifacts missing → NOT_RUN with paths listed; evidence contradicts a
claim → FAIL that check with measured numbers (never repair).
