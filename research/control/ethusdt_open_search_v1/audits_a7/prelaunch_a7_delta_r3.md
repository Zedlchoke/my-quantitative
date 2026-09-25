# A7 prelaunch delta audit r3 — cycle ETHUSDT-OPEN-SEARCH-V1

- Auditor: A7 (fresh context; recomputed from bytes, nothing trusted)
- Worktree: /Users/hoangminhlong/my-quantitative/.worktrees/ethusdt-open-search-v1/integration
- HEAD verified: 0b92ee65e8f2aaf0f9cff1b2ba45de9cb826637c, branch
  orca/ethusdt-open-search-v1-integration, working tree clean (and left clean; all
  non-audit bytes restored after probes)
- Audited remediation commit: 0b92ee65 (single commit in range 6d5797d0..0b92ee65;
  6d5797d0 is the r2-audit commit that recorded AUTHORIZED_FOR_SCORED_RERUN and fixed
  both r2 LOW doc-lag findings)
- Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python
- Machine-wide heavy-job lock inspected before compute runs: FREE_PROVEN

## Background being audited

Scored attempt 2 TECHABORTed pre-publication: NameError (`v`) in `run_scored.gates()`
at the TREND_LF fold-nets line — the old comprehension
`tr = {k: v["res"]["folds"][k]["net"] for k in folds}` referenced `v`, which is not in
scope (comprehension variables do not leak in Python 3). Claim: zero outcome exposure
(scored/ empty, no PnL surfaced, 10.45s CPU), remediation r3 = the tr line now reads
`refs["BASE_TREND_LF"][1.0]["res"]["folds"][k]["net"]` + hardening fixture 11 calling
gates() end-to-end on a synthetic tier_table, freeze v3 -> SUPERSEDED_BLOCKED, v4 built.

## Checks

### 1. Diff scope 6d5797d0..0b92ee65 — PASS
Exactly one commit, exactly five paths:
- `scripts/run_scored.py` (+1/-2), ONLY inside `gates()`: the broken `tr` comprehension
  replaced by `tr = {k: refs["BASE_TREND_LF"][1.0]["res"]["folds"][k]["net"] for k in folds}`
  and the dead `tr_pos` line removed. I verified `tr_pos` has ZERO remaining references
  anywhere in the file (it was dead code; nothing downstream consumes it), that `folds`
  (line 121) is the cell's own fold nets (correct for the G10 flip test), and that the
  G10 semantics now match the frozen gate text ("vs BASE_TREND_LF: combined net increases
  AND no fold flips positive->negative"). No other function touched.
- `tests_py/test_fixtures.py` (+45): fixture 11 `test_gates_synthetic`, wired into
  `main()`; strong-cell ALL-PASS path (incl. exact G5 arithmetic 140/320 = 0.4375), G4
  4/4 positive folds, all-G-keys presence, and the below-wall G3-fail / not-all_pass path.
- `freezes/eos1_freeze.v3_SUPERSEDED_BLOCKED.json` (new): byte-identical (sha256-verified)
  to the pre-diff `eos1_freeze.json` blob (ee0bd787) — v3 preserved exactly.
- `freezes/eos1_freeze.json`: v4 supersession edits only — run_scored.py hash ->
  1e081a91..., test_fixtures.py hash -> 9306cf83..., frozen_utc -> 2026-09-25T01:40:17Z,
  `remediation_r3` replaces `remediation_r2`, `supersedes` -> v3 file, `tree.head` ->
  6d5797d0, dirty_paths updated. Arms/budget/gates_verbatim/references/verdict_enum and
  evidence hashes untouched.
- `events.jsonl`: one appended line
  (`SCORED_ATTEMPT_2_TECHABORT_PRE_PUBLICATION_AND_R3`, utc 2026-09-25T01:40:17Z).
Engine byte-untouched: eos1_engine.py hash 4728850b... identical in v3 and v4 and
recomputed-matching on disk; stage_all.py untouched (c9ef1c87...).

### 2. scored/ absence, zero outcome exposure — PASS
`scored/` exists but is EMPTY (0 entries, untracked). No `scored_summary.json` and no
PnL-bearing artifact anywhere under the cycle namespace. state.json: budget used=0/8,
`scored_pnl_seen: false`. Both TECHABORTs are pre-publication, zero outcome exposure.

### 3. Freezes — PASS
- v1, v2, v3 SUPERSEDED_BLOCKED files all present in freezes/.
- v4 (`eos1_freeze.json`): 4/4 code_freeze + 4/4 evidence_freeze hashes recomputed by me
  and MATCH (eos1_engine.py 4728850b..., run_scored.py 1e081a91..., stage_all.py
  c9ef1c87..., test_fixtures.py 9306cf83..., census.json 90c1b234..., dry_run.json
  fd616f62..., feasibility.json 440b5b8a..., staged_manifest.json 18911c16...).
- v3 file byte-identical to `git show 6d5797d0:eos1_freeze.json`.
- v4 contains `remediation_r3` and `supersedes` pointing at the v3 file; tree.head =
  6d5797d022cf3a30c006b81c159fb543f96c6fab.

### 4. Fixtures — PASS (count nuance noted)
`tests_py/test_fixtures.py`: exit 0, final line `ALL FIXTURES PASS`, 46 PASS lines,
0 failures (the single grep hit for "fail" is the PASS check name "weak synthetic cell
fails G3"). Test 11 present with 6 PASS checks covering both required paths: strong
synthetic cell ALL-PASS (all G keys present, G4 4/4 positive, exact G5 concentration
140/320 = 0.4375) and below-wall cell G3-fail + all_pass=false.
NOTE: the dispatch said "44 checks"; the actual total is 46 (40 pre-existing + 6 new).
The actual coverage exceeds the stated number; substantive requirement (exit 0, ALL
PASS, test 11 with both paths) fully met.

### 5. Dry run (allowed; scored mode NOT executed) — PASS
`scripts/run_scored.py dryrun`: exit 0; stdout `dry_run_pass=true`, 84/84 computations,
`record_ids_pairwise_distinct=true`, leak_scan 15 checked / 0 leaked. Reproducibility
probe: recomputed `freezes/dry_run.json` differs from the frozen bytes in EXACTLY one
structural field (`built_utc` 15:24:54Z vs 01:43:26Z). Frozen bytes restored afterwards
(sha256 again fd616f62...); `git status` clean.

### 6. go_authorization.json — PASS
Present; `git diff 37629434..HEAD` on the path is empty (0 lines); worktree sha256
2814b4b0... equals the `git show 37629434:` blob. GO remains consumed and valid.

## Root-cause and plumbing verification (beyond the 6 checks)
- Old line reproduced in isolation: `NameError: name 'v' is not defined` (the `v` in the
  failed comprehension is not the leaked comprehension variable of `pos_folds` — Python 3
  comprehension scopes do not leak).
- Fixture 11 exercises `gates()` end-to-end via `import run_scored`, i.e. the scored-mode
  gate path that BOTH TECHABORTs hit is now under automated test (attempt 1's tier_table
  construction is covered by the dry-run's 84 pairwise-distinct book keys; attempt 2's
  gates() by fixture 11).
- I additionally cross-checked the remaining scored()-only plumbing surface:
  `scored()` loads `refs` (incl. BASE_TREND_LF at tier 1.0 with all tiers) from the
  tier_table and `feas` from freezes/feasibility.json — the key
  `g11_spearman_vs_trend_lf` EXISTS there and covers all 8 arms (spot values e.g.
  EOS1-E1-A1 0.709206), so gates() cannot KeyError on the disclosure line. The
  go-authorization refusal guard remains the first statement of scored().
- Residual note (informational): `dryrun()` does not execute gates(), so fixture 11 is
  currently the only automated coverage of the gate path; it covers both pass and fail
  branches. Acceptable.

## Continuity from r2
Both r2 LOW findings were fixed at 6d5797d0 and verified: state.json refreshed
(phase P4_SCORED_EXECUTION_AUTHORIZED_RERUN, go_phrase_state CONSUMED_AT_STOP1,
updated_utc 2026-09-25, budget 0/8, scored_pnl_seen false) and the event date-label
correction recorded (CORRECTION_AND_A7_DELTA_R2; new event lines carry full UTC
timestamps). The r2 audit artifact itself was committed at 6d5797d0
(audits_a7/prelaunch_a7_delta_r2.md/.json).

## Timeline consistency
GO received 2026-09-25T01:28:23Z (37629434) -> attempt 1 TECHABORT -> r2 fix commit
54f2b4f5 01:30:02Z -> r2 audit committed 6d5797d0 01:37:37Z -> attempt 2 TECHABORT
(10.45s CPU) -> v4 frozen 01:40:17Z -> r3 remediation commit 0b92ee65 01:40:17Z.
Ordered and plausible; budget 0/8 throughout.

## Findings

- F-4R3 LOW (informational, non-blocking): the dispatch expectation stated "44 checks"
  for the fixture suite; the actual suite emits 46 PASS lines (40 pre-existing + 6 in
  fixture 11). The cycles' artifact is correct; the request text undercounted. No
  defect in code, freeze, or evidence.
- No blocking findings. Both prior TECHABORT root causes are now under automated test,
  the remaining scored-only plumbing surface (feas g11 key, refs construction) was
  independently verified, and zero outcome exposure is maintained (budget 0/8).

## Verdict

AUTHORIZED_FOR_SCORED_RERUN — the r3 remediation is exactly as claimed and byte-scoped
(gates() tr fix + dead-line removal + fixture 11), attempt 2 left zero outcome exposure,
the freeze chain v1/v2/v3/v4 is intact with all 8 v4 hashes recomputed-matching,
fixtures exit 0 ALL PASS (46/46) with test 11 covering both gate branches, the dry run
passes 84/84 with distinct IDs and a clean leak scan reproducing the frozen artifact
modulo built_utc, GO authorization remains byte-unmodified, and the scored()-only
plumbing was independently verified consistent (feasibility g11 key present for all 8
arms). Scored mode may be re-run under the already-consumed GO.
