# DISPATCH — Lane B · MECHANISMS (task nflng-b-mech, cycle NFL-WINPROB-NG-PREP-V1)

ROLE: quant-explorer (mechanism research; proposal lane). Design/research ONLY.
OBJECTIVE: propose AT MOST 2–3 genuinely new NFL mechanisms on top of the B1* own-Elo baseline,
each with $0 source + rights, as-of law, falsifier, negative control, power estimate. NO data
downloads, NO outcome computation, NO metrics on real outcomes (PREP is design-only).

ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-prep-v1/lane-b-mech
BRANCH: orca/nfl-ngprep-b-mech
EXPECTED BASE SHA: the HEAD of your worktree at spawn (controller-created from the bootstrap commit; record git rev-parse HEAD output in your handoff as dispatch_sha) (verify before starting)
CYCLE: NFL-WINPROB-NG-PREP-V1 · ACTIVE_LIGHT · budget 0 scored · NO GO phrase

ALLOWED PATHS (write): lanes/B_MECHANISMS/** (this worktree) ONLY.
FORBIDDEN: everything else; downloads; edits to any frozen artifact/ledger of any cycle;
push/merge/rebase; push; git add -A. Reads of other worktrees are allowed (read-only).

REQUIRED INPUTS (read-only evidence, re-measure from bytes):
- /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-scored-v1/integration/research/control/NFL-WINPROB-SCORED-V1/results/scored_summary.json
  and TRIAL_LEDGER.jsonl (same dir) — 9/9 arms, baseline B1* = B1-c K=40 HCA=0 LL 0.6407 vs
  B0 0.6935, H2/H3 rejected, exact CIs.
- /Users/hoangminhlong/my-quantitative/.worktrees/winprob-ng-prep-v1/integration/lanes/C_MECHANISMS/MECHANISMS.md
  (NBA-cycle mechanism menu incl. NFL rows F7/F9, H-C1 SOS-Elo, H-C2 split-Elo — proposals to
  re-adjudicate, not authority)
- Old protocol (frozen semantics): /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-prep-v1/integration/lanes/NFL_C_protocol/PROTOCOL_EVAL_NFL.md
- Cycle plan: plans/PLAN_nfl_winprob_ng_prep_v1.md (in-tree)

DELIVERABLES (under lanes/B_MECHANISMS/):
1. MECHANISMS_NFL_NG.md — owner priorities re-adjudicated for NFL:
   (a) SOS-adjusted Elo (schedule-strength decomposition of the rating; replacement-rating
   shape, NOT additive feature over elo_diff), (b) home/away split rating (two roles per team,
   shrunk; explains NFL's rejected constant HCA as mis-specification), (c) offseason EPA prior
   train-only (pbp-derived efficiency as season-start rating prior; pbp is post-game compiled —
   train-only role mandatory). short-week×away interaction ONLY as conditional candidate gated
   on pre-registered train-internal strength evidence (no outcome runs here). REJECT list with
   reasons (any re-grid of K/HCA/rest mains on 2019–2025 is forbidden; MOV-weighted Elo out
   per ancestry). MAX 3 candidate mechanisms + the conditional interaction.
   For EACH candidate: mechanism story (who is mispriced, why), exact operationalization on
   allowed data only, $0 source + rights status (cite Lane A audit if already on disk; else
   PENDING_LANE_A), as-of/PIT discipline, frozen falsifier language (ΔLL vs B1*, CI + fold
   rule, negative control = time-shuffled twin), capacity/power estimate at ~270
   regular-season games/season (state minimum detectable ΔLL scale honestly; ≥2 seasons for
   strong conclusions), kill-fast rule.
2. POWER_NOTES.md — arithmetic power/capacity analysis for each candidate (analytic only;
   no outcome computation): expected ΔLL scale vs CI width at n≈270/season and n≈540 (2
   seasons), using the terminal cycle's measured CI widths as calibration.
3. handoff_B.json — schema zcode_orch_v3_handoff@1 at lanes/B_MECHANISMS/handoff_B.json
   (task_id "nflng-b-mech", fields as per schema; commit_sha = your commit).

STOP CONDITIONS: if evidence base contradicts a mechanism's premise (e.g. data cannot support
split ratings), record the rejection instead of forcing the proposal; if Lane A data verdicts
are prerequisites you cannot verify from disk, mark PENDING_LANE_A and continue.

COMMIT RULES: exactly ONE clean commit on your branch (message prefix "NFL-NG-PREP lane B:"),
stage by pathspec, never push/merge.
