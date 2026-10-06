# RUNNER REPORT — lane EXEC · WNBA-PLAYERFEAT-SCORED-V1 · 2026-10-06

Mission: complete the REAL OOS runner (post-GO authority-gated), settle the OOS window
from schedule facts, prove everything on synthetic data with exactly the 2 frozen arms
(B0 + B1-WNBA), draft ERRATUM_R1. Interpreter
`/Users/hoangminhlong/my-quantitative/.venv/bin/python` only; no git write commands; no
real OOS metric computed under any fixture; $0.

## 1. Window verdict (Task 1) — CONFIRMED, no contradiction

Full determination: `lanes/EXEC/WINDOW_RESOLUTION.md` (binding, echoed by ERRATUM_R1 §5).

- Re-verified from RAW bytes: raw ESPN schedule 2026 = 360 rows → 343 `post` (max tip
  **2026-10-03T01:00Z**, 0 after any freeze anchor) − 1 Postponed (`401857072`, 0–0
  prefill; dropped by the frozen drop-Postponed law) − 1 All-Star (`401857320`) = **341 =
  frozen feature table exactly** (set identity, feature-table-only = 0). The 15
  future-dated raw rows (through 2026-11-01) are `pre` TBD placeholders that the frozen
  universe law has always excluded ("placeholder TBD rows never games") — **not**
  future-tipped games, therefore **not** a freeze contradiction.
- roster_audit cross-check: `game_rosters_2026` = 342 unique ids = 341 universe + the
  All-Star extra; `player_box_2026` max ET game date 2026-10-02.
- Feature table re-measurement matches the controller's pre-measurement EXACTLY
  (2026 = 682 rows / 341 games; 2026-05-08T23:30Z → 2026-10-03T01:00Z; zero future tips).
- **2026 COMPLETE at freeze ⇒ OOS = [2020, 2021, 2022, 2023, 2024, 2025, 2026] exactly as
  frozen.** Per-season max tips: 2024 → 2024-10-21T00:00Z, 2025 → 2025-10-11T00:00Z,
  2026 → 2026-10-03T01:00Z; future-tip counts 0 everywhere.
- Schedule facts only; no outcome value read; measurement provenance in the lane sandbox
  (`window_measure.py`, `window_measurements.json`).

## 2. Runner (Task 2) — `research/control/WNBA-PLAYERFEAT-SCORED-V1/runner/run_oos.py`

Argument-driven (`--registry` defaults to the REAL read-only
`plans/CYCLE_REGISTRY.json`; `--source real|synth`; `--seasons`; `--data-root`; `--arm`;
`--out`). Gate chain, each audited with distinct exit codes, nothing computed on refusal
(every refusal writes only `run_audit.json`; fixtures assert no results/predictions):

| gate | law | exit |
|---|---|---|
| G1 AUTHORITY | row `WNBA-PLAYERFEAT-SCORED-V1`; lifecycle `ACTIVE_*`; `go_phrase` == `GO WNBA PLAYERFEAT SCORED V1 EVALUATION` exact; `go_phrase_state` matches canonical `OWNER_GO_TYPED_LIVE <utc-iso> at head <40-hex>`; GO-head == row-head. Fires BEFORE any data byte is read (and before any code-file hash) | 2 |
| G2 FREEZE | worktree HEAD == registry head; arms.py sha `82263eab…` + harness.py sha `b9446f76…` pins; B1 == (32.0, 50.0, 0.65) and B0 == 0.603755 asserted against law literals INSIDE the gate; arm set == exactly `B0,B1-WNBA`; `arm_feature_phi()` refuses unconditionally (no φ-arming acceptance path) | 3 |
| G3 LOCK | `researchctl locks inspect` FREE_PROVEN, 3×60s retry | 4 |
| G4 WINDOW | seasons law (real == 2020..2026 exactly; synth ≥ 2027 == manifest); every scored-window game `tip_utc < run time`; frozen census (2020→147 … 2026→341; warm-up 1022; universe 5,988) — refuse on any missing game (no silent shrink); schedule/feature-table set identity | 5 |
| G5 BATCH | single batch, both arms on the identical game list; exact-arm record ids pairwise distinct; non-vacuous; per-season counts == census | 6 |

All-PASS `--source real` path (never executed pre-GO): warm-up 1997–2001 (1022 rows) +
stream 2002–2019 feed the frozen rating stream; OOS 2020–2026 predicted with B0 (constant
0.603755) and B1-WNBA (K=32, HCA=50, γ=0.65) via the sha-pinned `arms.run_stream`; frozen
metrics (LL primary; Brier; 10-bin reliability; calibration slope, band [0.85,1.15]; B0
slope = honest nan; paired ΔLL tip-date-cluster bootstrap 10,000 resamples seed 20261005);
frozen falsifier applied verbatim (REJECT-vs-B0 iff CI includes 0 OR ≥ half of the season
folds non-negative; 7 folds ⇒ threshold 4); results JSON + RESULTS.md + per-arm
prediction CSVs to `--out`. Exit 0.

## 3. Fixture matrix (Task 3) — `lanes/EXEC/test_runner_gates.py` — ALL GREEN

13/13 case-groups PASS, 0 FAIL (10 dispatch cases (a)–(j); (c) runs as 3 sub-variants;
+1 extra default-registry check). Evidence:
`~/.my-quantitative-data/wnba-playerfeat-scored-v1/exec_sandbox/gate_matrix/gate_matrix_results.json`
(+ per-case out dirs with `run_audit.json`).

| case | scenario | result |
|---|---|---|
| a | REAL registry as-is (`REGISTERED_NOT_CONSUMED`), `--source real` | G1 refuse exit 2; **audit hook observed 0 real-data reads** (all 5 real roots present); nothing computed |
| b | fixture GO-typed-live + `--source synth` seasons [2027,2028] | FULL PASS exit 0: 2 arms, identical game sets, 112 scored rows/arm, hand-fixture cross-check 1e-12 (per-game p/LL/Brier, means, paired ΔLL — 14 checks), bootstrap smoke (CSV-recomputed CI == results.json; fixed-seed rerun equal), determinism (double run byte-identical) |
| c1/c2/c3 | CONSUMED / DEAD / wrong-phrase registries | G1 refuse exit 2 each (GO-NOT-TYPED-LIVE / LIFECYCLE-NOT-ACTIVE / REGISTERED-PHRASE-MISMATCH) |
| d | registry head 000…0 | G2 refuse exit 3 HEAD-MISMATCH |
| e | B1 tamper HCA=51 (module constant mutated in-process) | G2 refuse exit 3 B1-CONSTANT-DRIFT (law literals live inside the gate) |
| f | φ-arming attempt (`--arm WF-B` CLI + `arm_feature_phi()` programmatic) | G2 refuse exit 3 PHI-ARMING-REFUSED; no acceptance path |
| g | lock-conflict injection (NOT_RUN_RESOURCE_CONFLICT probe) | G3 refuse exit 4 LOCK-NOT-FREE; injection disclosed in audit |
| h | wrong seasons 2019..2025 (synth) + gate-order variant (real registry) | G4 refuse exit 5 SEASONS-LAW-SYNTH; order proof: real registry refuses earlier at G1 exit 2 |
| i | future-tipped synthetic game (tip 2099) | G4 refuse exit 5 FUTURE-TIPPED-GAME-AT-RUN-TIME |
| j | empty season (2028 declared 56, 0 universe games) | G4 refuse exit 5 CENSUS-MISMATCH-NO-SILENT-SHRINK (got null vs law 56) |
| k | runner DEFAULT registry is the REAL one; default-arg run | G1 refuse exit 2 (default behavior is the safe one) |

Machinery honesty: the case-(b) synthetic corpus is a MACHINERY fixture (planted random
strengths; ids `SYNTH_`; synthetic historical tips). Its B1-vs-B0 numbers (pooled ΔLL
+0.003141 [-0.033941, +0.039677], falsifier fired on this draw) prove the machinery runs
and the falsifier applies — they are NOT a performance claim about any arm.

## 4. Standing suites re-run (Task 5) — GREEN, zero regression

- `lanes/T_SELECT/harness.py --selftest` → **14/14 PASS**, exit 0; `arms.py`/`harness.py`
  shas unchanged (`82263eab…` / `b9446f76…`).
- `lanes/S_SYNTH/dryrun.py` → REHEARSAL ok (identical frozen numbers), exit 0.
- `lanes/S_SYNTH/lock_probe.py` → all probes PASS, exit 0.

## 5. ERRATUM_R1 (Task 4)

`lanes/FREEZE_ERRATUM_R1/ERRATUM_R1.md` + `freeze_digests_r1.json`: authority ruling
(execution-surface addition; arm code untouched — T_SELECT bytes verified unchanged);
runner sha pins; **RUNNER_FREEZE_SHA = PENDING_CONTROLLER_ADDENDUM** (two-step: controller
sets it at its own freeze step; per-file pins already enforced by G2); canonical
GO-recording convention `OWNER_GO_TYPED_LIVE <utc-iso> at head <40-hex>` (identical law to
the NFL ERRATUM_R3 convention); G1–G5 spec; WINDOW_RESOLUTION binding.

## 6. Known limitations / disclosures

1. The real-path loaders (warm-up/stream/OOS corpus, census laws) are written and
   census-pinned but were NEVER executed in this round (reachable only post-G1+G2+G3+G4;
   the real registry refuses at G1). They are structural code, proven only by the census
   constants' provenance (COVERAGE_AUDIT row-by-row) and mirrored through the synthetic
   loader, which runs the same law code.
2. "B0 refit per fold" (predecessor packet §1 placeholder) is superseded by the registered
   freeze: B0 is the single frozen scalar 0.603755 (dispatch G2 asserts exactly this);
   single-batch law therefore holds for both arms.
3. The falsifier's "≥ half of ~24 season folds" packet phrasing is applied to the 7 OOS
   folds as `≥ (7+1)//2 = 4` (stated per run with the actual fold count and threshold).
4. G3 in the test suite runs the REAL lock probe exactly once (FREE_PROVEN measured
   2026-10-06); all other G3 coverage uses the injected probe (disclosed in audits).
5. Synthetic fixtures use season labels 2027/2028 with synthetic historical tip instants
   (2024/2025) so the `tip_utc < run time` law is exercisable and passable on the synth
   path; season labels are never derived from tips on the synthetic side (manifest law).
6. Tree status: uncommitted-by-design (lane writes only; commit authority is the
   controller's).
