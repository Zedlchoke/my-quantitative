# VERDICT_TABLE — Lane PIPE, cycle NFL-WINPROB-NG-SCORED-V1

| item | verdict | basis |
|---|---|---|
| Task 1 — pbp 2018/2019/2020 download + provenance | **DONE — 3/3 OK** | HTTP 200 ×3, PAR1 ×3, 57,478,285 B; 2019/2020 sha256 byte-match cached GitHub API digests, 2018 size-match; manifest `raw_pbp_2018_2020/DOWNLOAD_MANIFEST.{md,json}`; 0/1 GitHub API calls used |
| Rights gate (license re-fetch, once) | **PASS — no BLOCKED_DATA_RIGHTS** | sha256 `2a82ac9b…` == pin exactly (11:57Z, HTTP 200, 18,651 B); stop condition NOT triggered |
| pbp pins (whole state-carry input set) | **VERIFIED 26/26** | 2000–2017 vs A_DATA manifest 18/18 MATCH; 2018–2025 vs PIPE pins (freeze_digests_r2) |
| Recorder implemented (a–e) | **DONE** | sha-pinned snapshot load (fresh-pull implemented, never executed); state warmup via frozen arms with future-with-score ABORT + param-equality asserts + no metric on any warmup game; batch predict with frozen identical-kickoff exclusion; ≥6h margin gate fail-loud before any write; ledger append via ported `nfl_ng_ledger@1` to a TARGET PATH (sandbox only) |
| `--selftest` | **PASS — 10/10 checks** | hand-computed margin/DST/Elo/prior arithmetic; exclusion canaries; abort; format guard; fresh-pull guard; prefix equivalence; digest law |
| `--mode e2e-synth` (SYNTHETIC ONLY) | **PASS — 3/3 scenarios + determinism** | nominal week: 24 rows (8 SYNTH games × B0/B1_STAR/C3), 192 completed synthetic games, C3 priors exercise (32 z/target season), chain intact, scoring rehearsal 24×VALID_PROSPECTIVE; margin violation (5.98h) refused, nothing written; future-score abort, nothing written; double-run byte-identical |
| `--mode warmup-check` (REAL, stages a+b ONLY) | **PASS — aggregates only, 0 probabilities** | 7,080 completed games 2000–2026 absorbed (2026 = 63 == registration audit); 209 future; 0 future-with-score; 32 lineages; 830 C3 z-entries applied 1:1 per (season, lineage); 26/26 pbp pins verified |
| ABSOLUTE — no p_home for any real game | **HELD** | predict stage refuses non-`SYNTH_` ids (`_assert_synth_only`); warmup-check never calls it; only synthetic probabilities exist in any lane artifact |
| ABSOLUTE — no real ledger / no 2019+ evaluation / no betting vocabulary | **HELD** | real-ledger paths asserted absent; warmup updates are state-carry only (ERRATUM §2); no LL/metric anywhere |
| Task 3 — FREEZE_ERRATUM_R2 | **DRAFTED** | ATL@NO Option B enforced (week-5-from-2026-10-09Z only; pre-week-5 NOT_RUN forever); STATE-CARRY LAW written; RECORDER FREEZE (5 module sha256s + PENDING_CONTROLLER_ADDENDUM); GENESIS_PAYLOAD_DIGEST_R2 `bd94eb77d35077ac7bc1761a2c61031a1cdf2f53c6d8be181de5ddfcefd51483` pins R2, supersedes `ae99a803…` with reason; R1 recomputation cross-check exact |
| Task 4 — suites re-run on current tree | **GREEN — 42/42 + 16/16 (+3 new)** | predecessor ledger suite 42 PASS; successor suite 16 PASS; lanes/PIPE/test_recorder_synthetic.py 3 PASS (additions only, nothing weakened) |
| Heavy-lock discipline | **FREE_PROVEN (read-only inspect)** | no foreign worker observed/touched; controller takes the lock for real batches |
| Handoff | **WRITTEN** | `lanes/DISPATCH/handoff_PIPE.json`, schema `zcode_orch_v3_handoff@1`, commit_sha null (uncommitted-by-design) |

Stop conditions: none triggered (license matched; no real-game probability ever produced;
ledger tool suite green). Verdict: **PIPE COMPLETE — recorder ready for controller
integration; prospective capture remains gated on owner typed GO + the ≥6h batch margin
within the week-5-onward window.**
