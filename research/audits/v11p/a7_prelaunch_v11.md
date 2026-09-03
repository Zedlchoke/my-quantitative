# A7 Prelaunch Audit — Sprint V11

- Producer: A7 (independent prelaunch auditor, read-only on production)
- Generated: 2026-09-03T03:20:00Z
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/v11/a7-prelaunch`
- Branch: `orca/v11-a7-prelaunch`, HEAD `44fc57d575a94010007fa08435702952d63ccf2c` (matches plan), tree clean
- W11 code-bearing freeze: `befbd20` — `git diff --stat befbd20..44fc57d` touches only control-plane evidence (event_log, heartbeat, staged_manifest_w11, worktree_manifest); **no code paths changed**

## VERDICT: V11_LAUNCH_AUTHORIZED (strong-host launch conditions SC1–SC6 below)

Unresolved HIGH: **0**. Unresolved CRITICAL: **0**. Blockers: **none**.

## Per-item recomputation

| # | Item | Verdict | Key evidence |
|---|------|---------|--------------|
| 1 | Pin chain | PASS | b8876ef → e6fa2b1 → 0a96bf2 → 7566ca2 → 0684914 → 903ed49 → 01139a8 → befbd20 all reachable; sequential ancestry verified via `git merge-base --is-ancestor` |
| 2 | Publication identity / 119-120 | PASS | `pytest tests/test_v11p_a2_publication.py` 17 passed; M01 terminal sha256 `b5d1c39e…` byte-identical between `e6fa2b1` blob and worktree file; `M01_FROZEN_PUBLISHED_DENOMINATOR == 119` |
| 3 | Dry-run uniqueness/idempotence | PASS | Fresh temp ledger rerun: ok=true, scored=false, real_pnl=false, 3 arms (anchor/neighbour/causal_control) pairwise-distinct keys, replay-stable, publish_delta=1, replay_delta=0, 0 blocking findings |
| 4 | PIT/no-leak tests | PASS | test_v11i_*: 54 passed; test_v11p_*: 84 passed (matches 7566ca2 "84/84 targeted"); 0 failures |
| 5 | Data/funding/instrument/tick coverage | PASS | 3 C1 artifacts PASS (OILEV per-arm OK + q_phase c1_verdict PASS, OI max staleness 8.08h disclosed); q_phase all_ok=true; staged manifest: exec==repro byte_identical; **full manifest verify 91/91 files hash MATCH** (OI parquet + bar shard spot checks included) |
| 6 | Schedule-only cost feasibility | PASS | 3 A3 gates PASS, schedule_artifacts_only=true; specs pin window 2025-08-22..2026-08-21 Monday 00:00Z; independent recount = 52 Mondays; ILLIQ/OILEV schedules 52 instants; LOT 53 = 52 decisions + terminal force-flat edge (per `build_schedule_instants`) |
| 7 | Novelty/rescue + orthogonality | PASS | Frozen set pairwise: LOT\|ILLIQ 0.3098, LOT\|OI 0.0919, ILLIQ\|OI −0.1168 — all < 0.35; OI thin-stamp caveat (7 stamps) disclosed; A7N CONDITIONAL_PROCEED → sole HIGH (OI re-audit) resolved by a9f2 verdict PASS blockers=[]; DEF **BLOCKED_PRE_SCORE** stands (3 slots unused, NOT reassigned); OI momentum-orthogonalisation mandated by a9f2 verified present in OILEV frozen spec |
| 8 | Negative controls | PASS | All 3 frozen specs define sign-inverted `causal_negative_control` arms; 9/9 frozen cells carry v2 digests incl. controls |
| 9 | Stress matrix | PASS | All 3 specs pin `stress = fee x1.5, +2 ticks, +1 event delay` |
| 10 | Resource cap / ownership | PASS | Fresh probe 2026-09-03T03:08:25Z: 45% free (3.87/8.6 GB), cap rule min(3, floor((free−1.5)/2)) → **measured_safe_cap=1 on this host now** (state.json recorded 0 under heavier Q-time load); owned_workers=0; swap 3080/4096 MB; a non-V11 session shares the host (disclosed) |
| 11 | Budget / no scored artifacts | PASS | selection_freeze.json: plan_max 12, eligible 9, consumed **0**, def_blocked 3, 9 frozen cells with v2 digests; registry sweep: 533 rows, **0 V11 matches**, no v11 shards; state: v11_scored_artifacts_exist=false |
| 12 | Test evidence gates | PASS | `gates/V11P_FULL_SUITE.json` PASS exit 0 tree-clean (sha 913f6d9, ancestor verified); `gates/V11_Q_FULL_SUITE.json` PASS exit 0 tree-clean (sha e853e70, ancestor verified); trees clean: a7-prelaunch 44fc57d, exec-v11-1 befbd20, repro-v11-1 befbd20, main checkout b8876ef — all 0 dirty |
| 13 | Deadline | PASS (relieved) | V11-AMEND-OI-STAGING-20260902 + V11-AMEND-DEADLINE-RELIEF-20260903; event log: V11_INCOMPLETE_NOT_PROMOTABLE superseded by OWNER_DEADLINE_RELIEF_SPRINT_REOPENED; clock superseded by owner-supervised continuation |

## Disclosed flags (not blocking)

1. **Carried HIGH (a9f2, explicitly "not a floor fail")**: OILEV weekly quintile book can trade 1 name/leg on the 9-symbol DV-above-median eligible set — Stage-A concentration gates are the binding downstream risk at scored time.
2. **OI thin stamps**: OI prewindow rho pairs rest on 7 Monday stamps (2025-07-07..2025-08-18); disclosed in addendum + freeze.
3. q_phase_checks records bootstrap 7d4a874 (intermediate commit at Q time); artifacts regenerated fresh at Q, all_ok.
4. OILEV C1 uses per-arm status=OK schema (no single top-level verdict); covered by q_phase c1_verdict=PASS.

## Strong-host launch conditions (required for scored Phase E)

- **SC1 re-probe**: on the launch host, run the resource probe; require `measured_safe_cap >= 1` under the frozen rule; record probe JSON into `research/control/v11_run/` before opening any scored window.
- **SC2 byte-identical re-staging**: re-stage catalog + funding + OI + staged_data on the launch host; regenerate `staged_manifest_.json`; exec/repro manifests must hash equal with `byte_identical=true`.
- **SC3 launch-time hash check**: full-manifest verification (91/91 here; repeat in full, not spot checks) plus `git diff --stat befbd20..HEAD` showing control-plane-only deltas and HEAD descending from 44fc57d.
- **SC4 identity**: verify all 9 cells against `selection_freeze.json` arm_config_digests (A2 v2) before each publish; first-publish + replay-zero semantics; observed denominator (conservative) governs DSR/PBO.
- **SC5 guardrails**: Stage-A concentration gates binding for OILEV; sign-inverted controls must publish for all 3 families; stress cells (fee ×1.5, +2 ticks, +1 event delay) per frozen specs.
- **SC6 budget**: eligible=9, consumed starts 0, 3 DEF slots stay unused and unassigned (no_discretion_rule); DEF remains BLOCKED_PRE_SCORE.
