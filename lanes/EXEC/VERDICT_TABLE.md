# VERDICT TABLE — lane EXEC · WNBA-PLAYERFEAT-SCORED-V1 · 2026-10-06

| # | item | verdict | evidence |
|---|---|---|---|
| 1 | Window raw-bytes re-verification | **CONFIRMED — no freeze contradiction** | `lanes/EXEC/WINDOW_RESOLUTION.md`; raw 2026 schedule 343 post (max tip 2026-10-03T01:00Z, 0 future) − Postponed − All-Star = 341 == feature table exactly; 15 future raw rows are `pre` TBD placeholders excluded by the frozen universe law; roster_audit 342 ids = 341 + All-Star extra |
| 2 | OOS window (final law) | **[2020, 2021, 2022, 2023, 2024, 2025, 2026]** — exactly as frozen | 2026 COMPLETE at freeze (341/341 games, last tip < earliest anchor 2026-10-05T09:26:30Z); measurement schedule-facts-only |
| 3 | Runner G1 AUTHORITY | **PROVEN** — real registry refuses pre-read, exit 2, 0 real-data reads (audit hook) | fixture (a) + (k); real row state `REGISTERED_NOT_CONSUMED` → GO-NOT-TYPED-LIVE |
| 4 | Runner G2 FREEZE | **PROVEN** — HEAD/sha pins + law-literal constants + φ-arming refusals | fixtures (d) HEAD-MISMATCH exit 3, (e) B1 HCA=51 → B1-CONSTANT-DRIFT exit 3, (f) PHI-ARMING-REFUSED exit 3 (CLI + programmatic) |
| 5 | Runner G3 LOCK | **PROVEN** — FREE_PROVEN measured; conflict injection refuses exit 4 | fixture (g) LOCK-NOT-FREE (NOT_RUN_RESOURCE_CONFLICT, disclosed injection) |
| 6 | Runner G4 WINDOW | **PROVEN** — seasons law, run-time tip law, census no-silent-shrink | fixtures (h) wrong seasons exit 5, (i) future-tipped exit 5, (j) empty season exit 5 with census |
| 7 | Runner G5 BATCH | **PROVEN** — single batch, identical sets, distinct ids, non-vacuous | fixture (b) full pass: 2 arms × 112 scored rows, per-season 56/56 |
| 8 | Fixture matrix (a)–(j) | **10/10 PASS** (13/13 case-groups incl. c1/c2/c3 + default-registry k), 0 FAIL | `exec_sandbox/gate_matrix/gate_matrix_results.json` |
| 9 | Hand-fixture cross-check | **PASS to 1e-12** (14 checks: per-game p/LL/Brier, means, paired ΔLL vs the frozen S_SYNTH closed-form truth) | fixture (b), byte-copied `exec_fixtures/hand_fixture/` |
| 10 | Bootstrap + determinism | **PASS** — CSV-recomputed CI == results.json (1e-12), fixed-seed rerun equal; double run byte-identical | fixture (b) |
| 11 | Standing suites re-run | **GREEN** — T_SELECT selftest 14/14 exit 0; S_SYNTH dryrun exit 0 (identical frozen numbers); S_SYNTH lock probes all PASS exit 0; T_SELECT shas unchanged | re-run 2026-10-06 |
| 12 | ERRATUM_R1 | **DRAFTED + PINNED** — authority ruling, runner sha pins, RUNNER_FREEZE_SHA=PENDING_CONTROLLER_ADDENDUM, canonical GO convention (NFL ERRATUM_R3 law), G1–G5 spec, window binding | `lanes/FREEZE_ERRATUM_R1/{ERRATUM_R1.md, freeze_digests_r1.json}` |
| 13 | Hard-boundary compliance | **HELD** — no real OOS metric under any fixture; no git write; T_SELECT/S_SYNTH files untouched (shas verified); schedule-facts-only window; no betting vocabulary; $0 | this lane's audit trail |

**LANE VERDICT: EXEC_COMPLETE** — REAL OOS runner built and authority-gated (G1–G5,
distinct exits, nothing-computed-on-refusal), window settled from raw bytes with the
frozen pin standing, synthetic-only proof green across the full matrix, ERRATUM_R1
recorded. Real-data scoring remains locked until the owner types GO and the controller
records the canonical state.
