# DISPATCH — Lane T_SELECT (NBA-PLAYERFEAT-SCORED-V1) — IMPLEMENTATION + TRAIN-INTERNAL SELECTION

ROLE: implementation/selection lane. TRAIN-INTERNAL ONLY (real data hard-capped at season
≤2021; warm-up 2016–2017). OOS 2022–2026 NEVER touched (evaluate-oos mode refuses real data
without a GO token that does not exist).
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nba-playerfeat-scored-v1/integration
BRANCH: orca/nba-playerfeat-scored-v1-integration · DISPATCH SHA: fcb2a1273d91e64f710468466b8d11ac654e6098
ALLOWED PATHS (write): lanes/T_SELECT/** + lanes/DISPATCH/handoff_T_SELECT.json + outputs under
~/.my-quantitative-data/nba-playerfeat-scored-v1/selection/. READ-ONLY: everything else.
FORBIDDEN: git; OOS computation; GO typing; betting vocabulary; modifying the frozen feature
table or any prior-cycle artifact.

## Inputs (read-only)
- Feature table: ~/.my-quantitative-data/playerfeat-prep-v1/nba/features/ (28,374 rows;
  spec + manifest in .worktrees/winprob-playerfeat-prep-v1/integration/lanes/A_NBA_FEAT/
  {FEATURE_SPEC.md, FEATURE_TABLE_MANIFEST.md, COVERAGE_AUDIT.md, PIT_AUDIT.md}).
- Schedule corpus: ~/.my-quantitative-data/nba-hoopr-v1/raw/nba_schedule_20{16..26}.csv
  (14,254 rows, ESPN game_id, game_date_time UTC; played = final/post + scores).
- Baseline law + windows + metrics: plans/PLAN_nba_playerfeat_scored_v1.md (this cycle);
  predecessor packet .worktrees/nba-winprob-ng-prep-v1/integration/research/control/
  NBA-WINPROB-NG-PREP-V1/SUCCESSOR_PACKET_SCORED.md; frozen protocol semantics of the
  terminal cycle in .worktrees/nba-winprob-scored-v1/integration/ (locate the protocol/
  results dir; inherit as-of/neutral/playoff semantics verbatim where applicable).

## Arms (all inside the rating argument; designed-null ≡ B1* bit-for-bit)
- B0 constant (emit TRAIN-window home-win rate as frozen constant, refit law per packet);
- B1* own-Elo K=32 HCA=100 γ=0.75 VERBATIM (mandatory, never re-tuned);
- PF-A rotation concentration: argument += φ_A·(x_H − x_A), x = standardized (warm-up+
  early-train moments, pinned) top5_share/load deviation (Group A frozen scalars);
- PF-B top-3 form: argument += φ_B·(form_H − form_A) standardized;
- PF-C lagged absence: argument += φ_C·(abs_H − abs_A) standardized;
- GRIDS (pre-registered, immutable): φ_A, φ_B, φ_C ∈ {−50,−25,0,25,50} (15 configs, all
  counted); tie-break fewer active params then lexicographic;
- Diagnostics (outside budget): time-shuffled twin per PF arm (shuffle the feature pair
  across team-sides within game-date, preserving marginals; seed 20261005); B1-HCA0 ablation.
- Selection: 4 rolling-origin folds over 2018–2021 (expanding); criterion pooled mean LL on
  fold rows (REG played games, exhibition rows excluded with counts, box-less games carry
  neutral features and REMAIN in rows); G-ENTRY per arm (ADMIT: pooled inner ΔLL point <0
  AND slope ∈ [0.85,1.15] AND twin not winning; CI entirely >0 ⇒ kill).
- Uncertainty: paired ΔLL vs B1*; tip-date-clustered bootstrap 10,000 resamples seed 20261005.

## Deliverables
lanes/T_SELECT/{harness.py,arms.py (+helpers), --selftest hand-computed fixtures (Elo update,
HCA=100 argument, γ=0.75 boundary reversion, designed-null ≡ B1* byte-identity on ≥3 synthetic
streams, standardization, neutral-rule, leakage canaries incl. a doctored 2022-row ABORT),
SELECTION_LEDGER.jsonl (every config), SELECTION_REPORT.md (frozen φ per arm or release;
standardization moments pinned; fit counts), VERDICT_TABLE.md}.
HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_T_SELECT.json (task_id
nba-playerfeat-scored-v1-T-SELECT, dispatch_sha=actual_start_sha=fcb2a127…, commit_sha=null).
STOP CONDITIONS: designed-null mismatch (TECHABORT); feature-table sha mismatch vs manifest
(stop, BLOCKED_DATA); lock not FREE_PROVEN at run start (inspect via researchctl from root;
retry 3×60s; else NOT_RUN_RESOURCE_CONFLICT).
