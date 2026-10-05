# DISPATCH — Lane S_SYNTH (WNBA-PLAYERFEAT-SCORED-V1) — SYNTHETIC FIXTURES + EXACT-ARM DRY-RUN

ROLE: test/dry-run lane. Prove the frozen 2-arm evaluation (B0 const 0.603755 + B1-WNBA
K=32/HCA=50/γ=0.65) runs end-to-end on SYNTHETIC OOS-like streams with identical game sets,
exact-arm identity, and the OOS lock holding (evaluate-oos refuses real data without GO
token). Sandbox outputs only; nothing real is scored.
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/wnba-playerfeat-scored-v1/integration
BRANCH: orca/wnba-playerfeat-scored-v1-integration · DISPATCH SHA: 5a1d0618e344844303d282923979cd949768368e
ALLOWED PATHS (write): lanes/S_SYNTH/** + lanes/DISPATCH/handoff_S_SYNTH.json + sandbox
~/.my-quantitative-data/wnba-playerfeat-scored-v1/sandbox/**.
FORBIDDEN: git; touching lanes/T_SELECT code (test as-frozen); real OOS data; betting vocabulary.
TASKS:
1. Re-run lanes/T_SELECT --selftest on the frozen tree (must stay green; record).
2. Synthetic OOS-like rehearsal: ≥2 synthetic seasons in the corpus format (SYNTH_ ids, 2027+
   seasons) with synthetic feature-neutral columns; run the FULL evaluation path in evaluate-oos
   mode on synthetic data: B0 + B1-WNBA predictions, identical-game-set law, per-fold LL/Brier/
   reliability/slope computed on hand-computed fixtures, paired ΔLL bootstrap machinery smoke
   (10k resamples on synthetic), exact-arm record ids pairwise distinct, non-vacuous (≥1 row).
3. OOS lock tests: evaluate-oos mode + real data + no GO token ⇒ loud refusal (prove with a
   probe pointing at a real corpus path — the refusal must fire BEFORE any data is read);
   with a fake GO token file ⇒ also refused (token validation must fail — the real token law:
   typed GO exists only post-owner-GO; no token may be fabricated — document how the mode will
   be unlocked after GO per plan).
4. Determinism: full synthetic rehearsal double-run byte-identical.
5. DRYRUN_REPORT.md (commands + exit codes + counts) + VERDICT_TABLE.md.
HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_S_SYNTH.json (task_id
wnba-playerfeat-scored-v1-S-SYNTH, dispatch_sha=actual_start_sha=5a1d0618…, commit_sha=null).
STOP CONDITIONS: frozen selftest regression; OOS lock failure (fix nothing — report TECHABORT).
