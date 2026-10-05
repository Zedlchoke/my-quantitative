# DISPATCH — Lane A7_NEGVERIFY (NBA-PLAYERFEAT-SCORED-V1) — INDEPENDENT VERIFICATION OF THE NEGATIVE

ROLE: A7-role fresh-context verifier of a NEGATIVE selection verdict. Positives need strict
audit; negatives too — they kill directions. Never repairs; never edits T_SELECT files.
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nba-playerfeat-scored-v1/integration
BRANCH: orca/nba-playerfeat-scored-v1-integration · DISPATCH SHA: bf86afce88ebe6ac16cafb6a81af5dc1f824ad0d
ALLOWED PATHS (write): lanes/A7_PRELAUNCH/** (+tmp) + lanes/DISPATCH/handoff_A7_NEGVERIFY.json.
TASKS:
1. Recompute from raw bytes with OWN code: B1* replay (K=32 HCA=100 γ=0.75) on folds
   2018–2021 → pooled LL (lane claims 0.638327, slope 0.7801) — match within 1e-9.
2. Recompute ≥2 PF grid points (e.g. PF-A φ=−25 ΔLL +0.00504 CI[+0.0017,+0.0084]; PF-B φ=+25
   +0.00425) with own replay + own bootstrap (10k, seed 20261005, tip-date clusters) — CI
   bounds within tolerance; verify the grid-minimum-is-null claim across all 15 configs from
   the ledger.
3. Designed-null independent re-run (φ=0 ≡ B1* byte-identity on your own stream).
4. Cap audit: code-read the SEASON_MAX_REAL=2021 enforcement; doctored 2022-row probe aborts;
   evaluate-oos refuses real data (prove).
5. Ledger completeness: 18 rows; every pre-registered grid point present; no un-counted fits.
6. Honesty audit: the SELECTION_REPORT discloses twins-winning diagnostics; confirm no
   post-hoc grid tampering (grid constants in code == dispatch packet).
7. VERDICT: NEGATIVE_VERIFIED (the clean negative stands) | NEGATIVE_UNSOUND (name the defect).
   A7_VERIFICATION_REPORT.md + VERDICT_TABLE.md + OWNER_NOTE.md (≤10 lines: what the negative
   means; the precise owner decision left — accept negative; optional NG successor path).
HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_A7_NEGVERIFY.json (task_id
nba-playerfeat-scored-v1-A7-NEGVERIFY, dispatch_sha=actual_start_sha=bf86afce…, commit_sha=null).
