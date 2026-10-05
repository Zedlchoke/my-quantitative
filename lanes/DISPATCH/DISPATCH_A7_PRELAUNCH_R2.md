# DISPATCH — Lane A7_PRELAUNCH_R2 (NFL-WINPROB-NG-SCORED-V1) — RE-AUDIT AT POST-ERRATUM SHA

ROLE: A7 independent auditor, FRESH re-audit. The prior A7 PASS (10/10 at ecf8371a) is NOT
inherited: the tree changed (INV_C2 + PIPE + ERRATUM_R2 + recorder + controller addendum).
Never repairs; recompute from bytes; look for reasons claims could be wrong.
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration
BRANCH: orca/nfl-winprob-ng-scored-v1-integration · DISPATCH SHA: 1e41b8dd2cc7888b41bdb412ba882896376b65c2
ALLOWED PATHS (write): lanes/A7_PRELAUNCH_R2/** (+tmp) + lanes/DISPATCH/handoff_A7_PRELAUNCH_R2.json.
CHECKLIST (command + exit code + evidence each):
R2-1 SHA chain: base f55dab66 → … → ecf8371a (prior A7) → INV_C2 3e52b7b1^ → PIPE → ERRATUM
   addendum 1e41b8dd; linear, clean tree now; verify with read-only git log/cat-file.
R2-2 ERRATUM_R2 coherence: ATL@NO resolution matches the registered Option B (week-5 first
   window; pre-week-5 NOT_RUN forever) AND the OWNER_GATE_BRIEF text (which now governs
   consistently); the registered window itself unchanged (no silent widening).
R2-3 State-carry law: selection caps (2018/2017) intact in T_SELECT; recorder is separate;
   recorder warmup consumes completed games only with future-score ABORT; NO metric computed
   during warmup (code-read + probe); pbp 2018–2020 provenance complete (3 files + license pin).
R2-4 Recorder tests: re-run recorder --selftest + --mode e2e-synth yourself (all 3 fixture
   scenarios) + verify warmup-check emits ZERO per-game probabilities (grep its output files).
R2-5 GENESIS R2: recompute the canonical payload digest bd94eb77… from the erratum's stated
   canonical form (placeholders as specified) — must match; R1 supersession documented.
R2-6 INV_C2 verdict integration: controller addendum discloses the twin-adjudication guidance
   WITHOUT changing gates/arms/windows; C2 stays out; C3 ADMIT untouched.
R2-7 Full suites re-run: ledger 42/42 + successor 16/16 + PIPE tests — green at THIS SHA.
R2-8 Boundaries: real ledger absent; zero real-game probabilities anywhere (grep sandbox +
   recorder outputs for real game_ids like 2026_04/2026_05 with probability values — none);
   GO registered-not-typed; budget 0/9; no push (branch local).
R2-9 Designed-null + cap probes: independent re-run of one designed-null via arms.py on your
   own stream; doctored 2019-row abort probe.
VERDICT: A7_PRELAUNCH_R2_PASS | REFUSED (blockers named). Update OWNER_GATE_BRIEF.md ONLY via
a NEW file lanes/A7_PRELAUNCH_R2/OWNER_GATE_BRIEF_R2.md (≤25 lines; ATL@NO forfeit-by-design
language consistent with the erratum; GO deadline for week-5 capture 2026-10-08T18:15Z).
HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_A7_PRELAUNCH_R2.json (task_id
nfl-winprob-ng-scored-v1-A7-R2, dispatch_sha=actual_start_sha=1e41b8dd…, commit_sha=null).
