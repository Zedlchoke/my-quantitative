# DISPATCH — Lane A7_PRELAUNCH (WNBA-PLAYERFEAT-SCORED-V1) — INDEPENDENT PRELAUNCH AUDIT

ROLE: A7 independent auditor, fresh context; never repairs; recompute from bytes.
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/wnba-playerfeat-scored-v1/integration
BRANCH: orca/wnba-playerfeat-scored-v1-integration · DISPATCH SHA: 12e05508de30de61da3825b10a6df8a87291f796
ALLOWED PATHS (write): lanes/A7_PRELAUNCH/** (+tmp) + lanes/DISPATCH/handoff_A7_PRELAUNCH.json.
CHECKLIST (command + exit code + evidence):
A7-1 SHA chain: base 03cc27f7 → bootstrap 8130de5a → T_SELECT 5a1d0618 → S_SYNTH 12e05508;
   linear; clean tree; read-only git.
A7-2 B1-WNBA selection recompute: own-code replay of the frozen winner K=32/HCA=50/γ=0.65 on
   its validation blocks → pooled LL 0.623498 within 1e-9; kill-test ΔLL −0.054386
   [−0.070150,−0.038275] direction; spot-recompute ≥2 other grid points (e.g. K=16/HCA=100/
   γ=0.75) matching the ledger.
A7-3 Designed-null: c≡1 and φ=0 ≡ parent byte-identity on your own synthetic stream.
A7-4 Cap/lock: SEASON_MAX_REAL=2018 code-read + doctored 2019 probe aborts; evaluate-oos
   refuses real data pre-read; fabricated tokens rejected.
A7-5 Ledger completeness: 49 rows; 27 grid + WF arms + diagnostics; grids == dispatch packet
   constants; no un-counted fits; deterministic rerun claim corroborated (ledger sha).
A7-6 S_SYNTH dry-run evidence: hand-fixture 1e-12; OOS lock zero-real-read; determinism.
A7-7 Honesty: WF-A MACHINERY_SUSPECT recorded (twin beat OWN parent, slope in band — not
   exempt); WF-B/C releases justified by φ=0 optimality; warm-up 1997–2001 usage = stream-only.
A7-8 Boundaries: 0/9 scored; no real OOS values anywhere; GO registered-not-typed; no push.
A7-9 Freeze completeness for the post-GO read: fielded arms (B0 0.603755 + B1-WNBA frozen) +
   released slots; OOS window [2020..2026] frozen; metrics/falsifiers/neutral law stated;
   single-batch OOS law; standardization/moments not applicable (no φ admitted) — verify.
VERDICT: A7_PRELAUNCH_PASS | REFUSED (blockers named). OWNER_GATE_BRIEF.md (≤20 lines: the GO
decision = run the 2-arm B0-vs-B1-WNBA OOS evaluation 2020–2026 post-GO; WF-A machinery audit
owed before any continuity re-proposal; what stays forbidden).
HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_A7_PRELAUNCH.json (task_id
wnba-playerfeat-scored-v1-A7-PRELAUNCH, dispatch_sha=actual_start_sha=12e05508…, commit_sha=null).
