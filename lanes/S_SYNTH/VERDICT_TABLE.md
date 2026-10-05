# VERDICT_TABLE — S_SYNTH lane, cycle NFL-WINPROB-NG-SCORED-V1

All checks SYNTHETIC-only. Exit codes 0 unless stated. Evidence: DRYRUN_REPORT.md,
PORT_NOTES.md, `~/.my-quantitative-data/nfl-ng-scored-v1/sandbox/dryrun_evidence.json`.

| # | check | verdict | evidence |
|---|---|---|---|
| 1 | Port byte-identical (3 files, sha256 pre == post == freeze pins) | **PASS** | cmp silent ×3; sha256 `6fb0a1d4…` / `93d3e248…` / `d44e945f…` |
| 2 | Predecessor synthetic suite on ported copy | **PASS 42/42, exit 0** | pytest run, DRYRUN_REPORT §2 cmd 1 |
| 3 | Designed-null equivalence C1 β=0 ≡ B1\* | **PASS** (max \|Δp\| == 0.0, bit-identical) | streams A–D, `test_designed_null_equivalence_vs_b1_star[*]` |
| 4 | Designed-null equivalence C2 λ=0∧h=0 ≡ B1\* | **PASS** (max \|Δp\| == 0.0, bit-identical) | same tests |
| 5 | Designed-null equivalence C3 θ=0 ≡ B1\* (nonzero synthetic z present) | **PASS** (max \|Δp\| == 0.0, bit-identical) | same tests |
| 6 | Designed-null equivalence C4 δ=0 ≡ B1\* | **PASS** (max \|Δp\| == 0.0, bit-identical) | same tests |
| 7 | Null comparisons not vacuous (β=25/λ,h/θ=50/δ=25 differ) | **PASS** | `test_designed_null_is_not_vacuous_nonzero_configs_differ` |
| 8 | Frozen-config determinism: C3 θ=50 twice → byte-identical | **PASS** | `test_c3_theta50_determinism_run_twice_byte_identical` |
| 9 | As-of canary, same-kickoff result absent from prediction inputs | **PASS** | `test_asof_same_kickoff_canary_absent_from_prediction_inputs` |
| 10 | As-of canary, later-kickoff result absent from prediction inputs | **PASS** | `test_asof_later_kickoff_canary_absent_from_prediction_inputs` |
| 11 | As-of input assembly: kickoff ≥ prediction time excluded | **PASS** | `test_asof_input_builder_excludes_kickoff_at_or_after_prediction_time` |
| 12 | Timestamp law: recorded_at == / > kickoff rejected | **PASS** | `test_tool_rejects_recorded_at_at_or_after_kickoff` |
| 13 | Tool-level ≥6h margin config | **NOT_RUN_MARGIN_CONFIG** — the ported `nfl_ng_ledger@1` exposes no margin knob (only strict R2); the only "margin" token in the source is the R8 OUTCOME_BLOCKLIST vocabulary | `test_tool_has_no_margin_config_not_run_margin_config` |
| 14 | Capture margin ≥6h, caller-side (freeze §4 law) | **PASS** (exact 6h accepted; 5h59m and post-kickoff rejected; dry-run batch margin 173.0 h) | `test_caller_side_six_hour_capture_margin_enforced`; dryrun_evidence `capture_margin_hours` |
| 15 | Hash-chain tamper: one flipped byte → loud failure | **PASS** (verify_chain flags exactly the tampered row; append + validate_for_scoring fail closed) | `test_single_byte_flip_breaks_chain_loudly_last_row` / `…_first_row` |
| 16 | Sandbox dry-run rows via PORTED tool | **PASS** — 45 rows = 15 SYNTH games × 3 fielded arms (B0, B1\*, C3), frozen arm_config_digests | dryrun_evidence.json |
| 17 | (game, arm) uniqueness + row count | **PASS** — 45/45 distinct pairs; count == 15×3 | dryrun_evidence.json |
| 18 | Chain validity (incl. expected sandbox genesis) | **PASS** — `[]` broken indices both walks | dryrun_evidence.json |
| 19 | Sandbox GENESIS ≠ freeze GENESIS; freeze digest absent from sandbox bytes | **PASS** — sandbox `e59ec10c…` ≠ freeze `ae99a803…`; byte-scan clean | dryrun_evidence.json; `test_sandbox_genesis_digest_is_64hex_and_never_the_freeze_genesis` |
| 20 | Zero non-SYNTH_ game ids; synthetic-only inputs; kickoffs 2027+ | **PASS** — all ids `SYNTH_*`; kickoffs 2028–2030 | dryrun_evidence.json |
| 21 | Dry-run determinism (two full executions) | **PASS** — byte-identical ledger sha256 `77029ae6…` | DRYRUN_REPORT §2 cmd 5 |
| 22 | REAL prediction-ledger path absence | **PASS** — 6 explicit paths + worktree-wide find: no real ledger anywhere; sandbox ledger only under `sandbox/` | DRYRUN_REPORT §5 |

Overall lane verdict: **ALL CHECKS PASS or explicitly NOT_RUN_MARGIN_CONFIG (tool has no
margin config; caller-side ≥6h margin enforced and PASS).** No STOP/TECHABORT condition
triggered; no incident; the real prediction ledger does not exist.
