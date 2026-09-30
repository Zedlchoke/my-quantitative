# G8 REPRODUCTION-TWIN REPORT — ETHUSDT-OPEN-SEARCH-V2 (STOP-1 scored run)

Lane: G8 REPRODUCTION-TWIN (P5). Gate G8 verbatim (freezes/eosv2_freeze.json):
"reproduction byte-match (detached twin at code-freeze SHA)".

Verdict line (see root-cause section before contesting):

**G8: ALL_MATCH — every deterministic outcome byte reproduces exactly:
`run_scored_stdout.json` and `determinism_b1.json` byte-identical (sha256-equal);
`scored_summary.json` identical in 168/169 leaves with the sole divergence the
by-construction wall-clock journal field `built_utc` (field-level diff + root cause
below — disclosed, not smoothed).**

## 1. Protocol (what was run)

1. Integration worktree verified at commit `1908b0756b382204bb585eb0ba0af6d2e208856c`
   on branch `orca/ethusdt-open-search-v2-integration`, tree clean (this is the
   STOP-1 scored-execution commit; the scored artifacts are committed in it).
2. Detached twin created: `git -C /Users/hoangminhlong/my-quantitative worktree add
   --detach .worktrees/eosv2-repro-twin 1908b075`. HEAD verified == 1908b075,
   detached (no branch), tree clean, 2137 files checked out.
3. Twin integrity pre-verified against `freezes/eosv2_freeze.json`:
   - `scripts/eosv2_engine.py`  cf1f36d52af2b343799480053bc01f0bebb62d5d4d89b803329f252733e85db9 (== code_freeze)
   - `scripts/run_scored.py`    28f0ff88dffc5e3e2daf5b442ac4e5c3fe72769bee8a18415b374a3b1aac572f (== code_freeze, r1-remediated digest)
   - `scripts/stage_all.py`     5d96cad6a6be2efa9674878715119b20c3fee16a74f36671d05abc9b6275e061 (== code_freeze)
   - `tests_py/test_fixtures.py` c43077015876fcc4710967bb3ab72c1a4d3a919cc2c93e122008cdd9cedb7139 (== code_freeze)
   - evidence freezes (feasibility/dry_run/census/staged_manifest) sha256 == evidence_freeze block
   - data: 551 files under `data_local/vision/` all git-tracked (identical bytes by
     checkout of the same commit the STOP-1 lane ran on)
   - `audits_a7/go_authorization.json` present in tree (scored mode authorized; the
     twin consumed the same committed GO record — no new GO minted)
4. Because the scored artifacts ARE committed at 1908b075, the frozen outputs were
   copied aside (`/tmp/eosv2_g8_frozen_aside/`, sha256s verified equal to the
   integration worktree's committed files) and removed in the TWIN ONLY, then
   re-run — comparison is re-run bytes vs copied-aside frozen bytes.
5. Re-run used the SAME invocation the STOP-1 lane used (via its harness
   `scripts/stop1_execute.py`: subprocess `[ROOT_PY, scripts/run_scored.py, scored]`,
   stdout captured verbatim, then the harness's DET_CODE B1 determinism double
   re-run in two fresh processes):
   - battery: `/Users/hoangminhlong/my-quantitative/.venv/bin/python <twin>/scripts/run_scored.py scored` → exit 0 in ~15 s
   - stdout written verbatim to `scored/run_scored_stdout.json` (harness-identical)
   - determinism: harness DET_CODE reproduced exactly (same code text, same ROOT_PY
     `-c` subprocess form, same cross-check, same `json.dumps(indent=1, sort_keys=True)+"\n"`
     serialization) → `scored/determinism_b1.json`
   - supplementary (beyond STOP-1 scope, read-only): canonical dumps of ALL 4 scored
     cells in fresh processes for per-cell byte evidence
6. Twin removed with `git worktree remove --force` after capturing all results.
   No engine edit, no parameter change, no commit (A1 integrates).

Lock: total compute ~76 s (battery 14.9 s + determinism 20.0 s + per-cell 40.6 s) —
well under the 10-minute threshold, so per dispatch the heavy lock was NOT taken;
`researchctl locks inspect` verified FREE_PROVEN immediately before and after. No
foreign worker touched.

Budget: zero new scored cells — this lane re-derived already-counted artifacts at
the same SHA (STOP-1 recorded 8/8 consumed; the re-run's own denominator reproduced
identically: scored_cells 4, computations 12, controls 24, references 12).

## 2. Byte-level comparison table (sha256)

| artifact (scored/) | frozen @1908b075 | twin re-run | result |
|---|---|---|---|
| run_scored_stdout.json | 5a4df6a2d9c1adcb7a96ba446289aafef3fc53a7ffbc34d90ad4e0d15496465e | 5a4df6a2d9c1adcb7a96ba446289aafef3fc53a7ffbc34d90ad4e0d15496465e | ALL_MATCH (byte-identical) |
| determinism_b1.json | 955a82483aee1a3364505ce07cb7b740141805dfbad2b5296e7f9918ec526d19 | 955a82483aee1a3364505ce07cb7b740141805dfbad2b5296e7f9918ec526d19 | ALL_MATCH (byte-identical) |
| scored_summary.json | b18c3c7f44d075bbfed8ae26e8dd7ce80183f38652046579e858c6a428a1ac19 | 8452b7580f6846f6d2276dbc14ae442501326280cb97701deb9990a4a68b2147 | MISMATCH — exactly 1 field (`built_utc`), root-caused below; all outcome bytes identical |
| STOP1_SCORED_REPORT.md | 8f84b6dbe7c55eb255ac51fc6adc35b84c825c2e5cd7fd95b9f04fa5e9636e00 | n/a | not re-runnable (hand-authored lane report; anchored by the artifacts above) |

The twin's git status after the full re-run showed exactly one modified file
(`scored/scored_summary.json`); `git diff --unified=0` is a single one-line hunk:

```diff
- "built_utc": "2026-09-30T21:25:46Z",
+ "built_utc": "2026-09-30T21:32:24Z",
```

## 3. Per-cell byte-level evidence

Canonical dump = the frozen determinism protocol's dump shape (folds(net,gross,
fees,funding,trades,fills,funding_events) x3 tiers + fills_total + net_total +
avg_raw_fill_px), computed in fresh ROOT-.venv processes from the twin's frozen
engine:

| cell | canonical dump sha256 (twin re-run) | vs frozen |
|---|---|---|
| EOSV2-B1 | 0287ea234bceb69d92a98cb3b72553f542f707b30c4e144c340d394cb9cc1401 | == frozen determinism_b1.json sha256_run1/run2 (direct byte evidence) |
| EOSV2-B2 | 8cb0f3321384096b600d124c0d15ff0e22f2bd719ddf1c64551905f8ca5c511a | no frozen canonical counterpart (STOP-1 canonicalized B1 only); all rounded fields cross-check vs frozen summary: true |
| EOSV2-B3 | de64fa82d645af2a5a1ca3437af353a30f0c3ab0f063058353c28a6cc86a7ce8 | same — cross-check true |
| EOSV2-B4 | 468846b4150cf872aa62acb4d196b2da35f0c6241cb0fce882df299645dc2288 | same — cross-check true |

B1 determinism inside the twin: both fresh processes byte-identical to each other
AND to the frozen digest `0287ea23...`; cross_check_vs_scored_summary
(net_at_tiers, fold_nets) true — `determinism_b1.json` re-serialized byte-identical.

References reproduced inside the summary leaf comparison (to the cent):
BASE_ALWAYS_ON_LONG 1653470.33 / BASE_TREND_LF 472864.82 / REF_SHORT_ALWAYS
-1656451.03 / BASE_CASH 0.0 @1.0x (and @1.5x/@2.0x), verdict
`ETHUSDT_OPEN_SEARCH_V2_NO_INCREMENTAL_VALUE`, all_pass_cells [] — all identical.

## 4. Root cause of the single-field divergence (PC12A-precedent treatment)

- Field-level recursive diff over the whole artifact: **169 leaves compared,
  exactly 1 differing path — `$.built_utc`** (frozen `2026-09-30T21:25:46Z`,
  re-run `2026-09-30T21:32:24Z`). No other leaf, key, list length, or type differs.
- Root cause (source-provable, not inferred): frozen `scripts/run_scored.py` line
  35 `def now(): return dt.datetime.now(dt.timezone.utc).strftime(...)` embedded
  at line 203 as `"built_utc": now()` — a wall-clock journal field stamped when
  the artifact is assembled, before serialization. It records WHEN the run
  happened, carries no outcome data, and can never repeat across runs by
  construction. Same class as the PC12A "embedded digest of a live directory"
  precedent: journal metadata, not metrics.
- Proof that nothing else moved: with `built_utc` normalized to a constant in
  both files, canonical re-dumps are byte-equal —
  sha256 `bd8875aea83fc8fc5f5851ba20d099eb48e570e674e155435a91a160406323ea` on
  BOTH sides. Every gate value, fold net, tier net, G3 margin, G6 control net,
  G7 fills/cost, G10 delta/flip list, G11 spearman, the embedded GO authorization
  record, denominator block and verdict reproduce byte-for-byte.
- Not smoothed: the raw sha256s differ and are reported as such in the table
  above; the divergence is fully accounted for by one timestamp field.

## 5. Reproduction environment

- Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python (ROOT venv,
  same as STOP-1 harness requirement)
- Code state: detached twin at 1908b075 (STOP-1 scored-execution commit,
  code-freeze digests verified in-twin before running, including the r1-remediated
  run_scored.py 28f0ff88..)
- Data: identical bytes via git checkout of the same commit (551 vision files)
- Compute: ~76 s total; machine-wide heavy lock FREE_PROVEN before/after (not
  taken — sub-10-minute job per dispatch rule)

G8: ALL_MATCH
