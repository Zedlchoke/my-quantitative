# DISPATCH — Lane D_VERIFY (NFL-PLAYERFEAT-PREP-V1) — INDEPENDENT VERIFIER

ROLE: independent verifier (A7-role). Never repairs; writes only its dir + handoff; recomputes
from bytes with its OWN code.
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-playerfeat-prep-v1/integration
BRANCH: orca/nfl-playerfeat-prep-v1-integration · DISPATCH SHA: b0febecac4551bb211c1b16385bd1dc6e2b73982
ALLOWED PATHS (write): lanes/D_VERIFY/** + lanes/DISPATCH/handoff_D_VERIFY.json.
TASKS:
1. Re-hash inputs + output table vs FEATURE_TABLE_MANIFEST (players.parquet, weekly stats,
   snap_counts, output parquet sha f1bc6b4a…).
2. Re-join rates with own code (GSIS weekly 2024/2025/2026; snap PFR 2025/2026).
3. Independently recompute ≥6 sampled rows with own as-of implementation (kickoff strict
   inequality; include ≥1 bye-week case, ≥1 pfr-null G3 exclusion, ≥1 neutral opener row, the
   KC 2024_11_KC_BUF Mahomes prior-3 worked example).
4. Missing-data rule behavior spot-checks (neutral flags, g3_no_snap rows); verify 0 outcome
   columns; determinism re-run (rebuild into temp, sha compare).
5. Boundary audit: 0 scored computation (grep); write-scope (git status read-only observation);
   isolation — the NFL-WINPROB-NG-SCORED-V1 worktree clean and untouched.
6. VERIFICATION_REPORT.md + VERIFY_MATRIX.md + discrepancy register (BLOCKER/MAJOR/MINOR/INFO);
   overall verdict VERIFIED | VERIFIED_WITH_MINOR | DISCREPANCY_MAJOR.
HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_D_VERIFY.json (task_id
nfl-playerfeat-prep-v1-D-VERIFY, dispatch_sha=actual_start_sha=b0febeca…, commit_sha=null).
