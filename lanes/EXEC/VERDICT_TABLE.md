# VERDICT_TABLE — EXEC lane, cycle NFL-WINPROB-NG-SCORED-V1

Lane: EXEC · Dispatch SHA = actual start HEAD `876845e01932393319fcca05924dca0e8243744a` ·
Branch `orca/nfl-winprob-ng-scored-v1-integration` · Written 2026-10-05 · $0 ·
No GO typed or consumed · No real-game probability computed · No 2019+ outcome evaluation.

| # | item | verdict | basis |
|---|---|---|---|
| 1 | Executor `execute_post_go.py` implements G1–G8 in order, each audited, distinct exits, nothing written on refusal | **DONE** | gate table in EXECUTOR_REPORT.md §2; gate logs in `~/.my-quantitative-data/nfl-ng-scored-v1/exec_sandbox/` |
| 2 | G1 registry authority (lifecycle + canonical `OWNER_GO_TYPED_LIVE` state + phrase equality; registry-only) | **PROVEN** | cases a/c/d/e refuse 11; pass case accepts the fixture canonical form |
| 3 | G2 freeze coherence (HEAD lineage ×3; arm/recorder/import/executor pins; freeze-packet sha; GENESIS R2 recompute `bd94eb77…`) | **PROVEN** | cases f/g/h refuse 12; pass case G2 PASS with all pins equal |
| 4 | G3 heavy lock (real `researchctl locks inspect`, 3×60 s) | **PROVEN** | real FREE_PROVEN observed on the pass path; HELD_PROVEN observed mid-lane (executor refused 13, nothing written, foreign worker untouched); held-sim via injection (case i, NOT_RUN_LOCK_SIM disclosed) |
| 5 | G4 snapshot (sha pin + manifest presence + future-with-score abort + kickoff parse) | **PROVEN** | cases j/k refuse 14; pass case G4 PASS |
| 6 | G5 week ≥ 5 Option B law + `2026_04_ATL_NO` canary | **PROVEN** | case l refuses 15 (week law + by-name canary before any computation) |
| 7 | G6 margin ≥ 6 h | **PROVEN** | case m refuses 16 at 5.99 h; boundary 6 h passes (PIPE law re-verified) |
| 8 | G7 exactly 3 frozen arms by import; config digests; no 4th arm | **PROVEN** | case n refuses 17; pass case appends exactly B0/B1_STAR/C3 |
| 9 | G8 ledger via ported tool; GENESIS substitution asserted pre-write; chain validates; recorded<kickoff | **PROVEN** | case o refuses 18 on a pre-broken chain (bytes untouched); pass case: 24 rows, chain valid, substitution == exactly {created_at, recorder_freeze_sha} |
| 10 | Fixture matrix 15 cases (a–o) | **15/15 PASS, 83/83 checks** | `lanes/EXEC/gate_matrix_evidence.json` |
| 11 | Real-registry refusal with zero-read proof | **PROVEN** | case a: exit 11; audit hook shows opens = registry + sandbox gate log ONLY; nothing else written |
| 12 | Pass path end-to-end on synthetic fixtures | **PROVEN** | case b: 24 rows (8 games × 3 arms), chain valid, 24 VALID_PROSPECTIVE, double-run BYTE-IDENTICAL, real digests absent from sandbox bytes |
| 13 | Existing suites re-run at final tree | **ALL GREEN** | ledger 42/42 · successor 16/16 · PIPE selftest 10 checks · PIPE e2e-synth 3 scenarios (evidence write redirected; lanes/PIPE untouched) |
| 14 | ERRATUM_R3 drafted (authority ruling, executor pins, two-step EXECUTOR_FREEZE_SHA, GO-recording convention, G1–G8 contract, GENESIS R2 unchanged) | **DRAFTED** | `lanes/FREEZE_ERRATUM_R3/{ERRATUM_R3.md, freeze_digests_r3.json}` |
| 15 | Frozen-surface non-interference | **HELD** | `git status --porcelain` = only lanes/EXEC, lanes/FREEZE_ERRATUM_R3, the one new executor module (+ pre-existing untracked dispatch packet); T_SELECT/F_FREEZE/PIPE/S_SYNTH untouched |

**Lane verdict: COMPLETE — no BLOCKED_TOOLING, no regression.** The executor must refuse
today's REAL registry (it does, exit 11) and is ready for the controller's post-GO use
after the ERRATUM_R3 two-step addendum re-pins `EXECUTOR_FREEZE_SHA` +
`head_lineage.expected_sha` at the integration HEAD.
