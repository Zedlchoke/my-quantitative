# A7 prelaunch delta audit r2 — cycle ETHUSDT-OPEN-SEARCH-V1

- Auditor: A7 (fresh context, recomputed from bytes; nothing trusted from the dispatch beyond where to look)
- Worktree: /Users/hoangminhlong/my-quantitative/.worktrees/ethusdt-open-search-v1/integration
- HEAD verified: 54f2b4f5f9eac993b6fb4a2359885e6485c8df43, branch orca/ethusdt-open-search-v1-integration, working tree clean (and left clean; every non-audit byte restored after probes)
- Audited remediation commit: 54f2b4f5 (single commit between GO-consumption commit 37629434 and HEAD)
- Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python
- Machine-wide heavy-job lock inspected before compute runs: FREE_PROVEN

## Background being audited

Scored attempt 1 TECHABORTed pre-publication: control-book record IDs such as
`EOS1|EOS1-E1-A1|G6-SHUF|tier1.0` contain `|` in the book name, and
`run_scored.scored()` did a 3-way `rid.split("|")` unpack -> ValueError. Claim: zero
outcome exposure (no artifact written, no PnL surfaced), 1-line parse fix at 54f2b4f5,
freeze v2 -> SUPERSEDED_BLOCKED, freeze v3 built, GO remains consumed/valid.

## Checks

### 1. Diff scope 37629434..54f2b4f5 — PASS
`git show 37629434..54f2b4f5 --stat`: exactly one commit, exactly four paths:
- `research/control/ethusdt_open_search_v1/scripts/run_scored.py` (+3/-2): the ONLY code
  change, inside `scored()` at the tier_table construction — `_, book, t = rid.split("|")`
  replaced by `parts = rid.split("|"); book = "|".join(parts[1:-1]); ... float(parts[-1].strip("tier"))`.
  Nothing else in the file changed (no mode, arg, gate, cost, or PnL-accumulation edits).
- `research/control/ethusdt_open_search_v1/freezes/eos1_freeze.v2_SUPERSEDED_BLOCKED.json`
  (new file): byte-identical (sha256-verified) to the pre-diff `eos1_freeze.json` blob —
  v2 is preserved exactly, renamed SUPERSEDED_BLOCKED.
- `research/control/ethusdt_open_search_v1/freezes/eos1_freeze.json`: supersession edits
  only — `run_scored.py` hash updated to 536d7e1e..., `frozen_utc` -> 2026-09-25T01:29:53Z,
  `remediation_r1` block replaced by `remediation_r2` string, `supersedes` now points at the
  v2 file, `tree.head` -> 37629434, `tree.dirty_paths` reduced to the three touched paths.
  All other sections (arms, budget, gates_verbatim, references, verdict_enum, evidence
  hashes) untouched.
- `research/control/ethusdt_open_search_v1/events.jsonl`: one appended line
  (`SCORED_ATTEMPT_1_TECHABORT_PRE_PUBLICATION`).
Engine, tests, plan, and all other freezes: zero diff. Independently confirmed by hash
identity of eos1_engine.py (4728850b...) and test_fixtures.py (20a1ec10...) between the
v2 and v3 freeze manifests.

### 2. scored/ absence, zero outcome exposure — PASS
`research/control/ethusdt_open_search_v1/scored/` exists but is EMPTY (0 entries,
directory untracked in git). No `scored_summary.json` anywhere under the cycle namespace
(including untracked files). Full recursive enumeration of the namespace: only audits_a7/,
events.jsonl, manifest.json, state.json, scripts (source + pycache), tests_py, data_local
zips, and freezes (census/dry_run/feasibility/staged_manifest — all pre-attempt, hashes
still matching the freeze). The dry-run artifact's own hygiene fields: `published=false`,
`scored=false`, `real_pnl=false`, `denominator_delta=0`. No PnL-bearing artifact exists;
budget 0/8 intact (state.json budget used=0).

### 3. Freezes — PASS
- `eos1_freeze.v2_SUPERSEDED_BLOCKED.json` present.
- v3 (`eos1_freeze.json`) `code_freeze`: 4/4 files re-hashed by me and MATCH
  (eos1_engine.py 4728850b..., run_scored.py 536d7e1e..., stage_all.py c9ef1c87...,
  test_fixtures.py 20a1ec10...).
- v3 `evidence_freeze`: 4/4 re-hashed and MATCH (census.json 90c1b234...,
  dry_run.json fd616f62..., feasibility.json 440b5b8a..., staged_manifest.json 18911c16...).
- v3 contains `remediation_r2` (declares the rid.split -> parts[1:-1] join fix) and
  `supersedes` record pointing at freezes/eos1_freeze.v2_SUPERSEDED_BLOCKED.json;
  `tree.head` = 37629434d8ba97906ed7d90c24ec5e80af0aa716.

### 4. Fixtures — PASS
`tests_py/test_fixtures.py`: exit 0, final line `ALL FIXTURES PASS`, 40 PASS lines,
0 FAIL lines (incl. fixture 10 settlement PIT cases and the tier-scaling suite).

### 5. Dry run (allowed; scored mode NOT executed) — PASS
`scripts/run_scored.py dryrun`: exit 0; stdout `dry_run_pass=true`,
expected 84 / actual 84, `record_ids_pairwise_distinct=true`,
leak_scan 15 forbidden substrings checked / 0 leaked.
Reproducibility probe: the recomputed `freezes/dry_run.json` differs from the frozen
bytes in EXACTLY one structural field, `built_utc` (2026-09-24T15:24:54Z ->
2026-09-25T01:33:16Z); all 84 book entries and all hygiene fields are identical.
I restored the frozen bytes afterwards — `dry_run.json` sha256 again fd616f62...,
`git status` clean.

### 6. go_authorization.json — PASS
Present at `audits_a7/go_authorization.json`. `git log --follow` shows exactly one
commit touching it (37629434, "GO consumed at STOP-1"); `git diff 37629434..HEAD` on the
path is empty; worktree sha256 2814b4b0... equals `git show 37629434:` blob byte-for-byte.
Content: go_phrase "GO ETHUSDT OPEN SEARCH V1 SCORED EXECUTION", received_utc
2026-09-25T01:28:23Z, budget gate 8 cells, no mid-run stop.

### 7. Parse-fix sanity — PASS
Root cause reproduced from bytes on the exact reported ID: old 3-way unpack raises
`ValueError: too many values to unpack (expected 3)` on `EOS1|EOS1-E1-A1|G6-SHUF|tier1.0`.
New parse yields book `EOS1-E1-A1|G6-SHUF`, tier 1.0 (float of `parts[-1].strip("tier")`).
Simple reference IDs still parse to plain book names (BASE_CASH, BASE_TREND_LF spot-checked).
All 84 dry-run book keys are pairwise distinct and every key matches the grammar
`<...>|tierN.M`; control-ID spot-checks: `EOS1|EOS1-E1-A1|G6-INV|tier{1.0,1.5,2.0}` and
`EOS1|EOS1-E1-A1|G6-SHUF|tier{1.0,1.5,2.0}` each split into a distinct inner book plus the
correct tier suffix.

## Timeline consistency
GO received 2026-09-25T01:28:23Z (commit 37629434) -> attempt 1 TECHABORT ->
freeze v3 frozen 2026-09-25T01:29:53Z -> remediation commit 54f2b4f5 authored
2026-09-25T08:30:02+07:00 (= 01:30:02Z). Ordered and plausible.

## Findings

- F-2R2 LOW (non-blocking): `state.json` is stale — phase
  `STOP1_AWAITING_OWNER_GO`, `go_phrase_state` `REGISTERED_NOT_CONSUMED`,
  `updated_utc` 2026-09-24 — while GO was in fact consumed at 37629434
  (2026-09-25T01:28:23Z). Authority for GO-consumed is `audits_a7/go_authorization.json`
  (per dispatch, and it is the artifact committed with the consumption). Neither
  `run_scored.py` nor `eos1_engine.py` reads `state.json`, so there is no functional
  impact on a scored re-run; documentation lag only.
- F-3R2 LOW (non-blocking, cosmetic): the TECHABORT line in `events.jsonl` is
  date-labeled `2026-09-24`, but the attempt necessarily occurred
  2026-09-25T01:28–01:30Z (after GO received 01:28:23Z, before the fix commit at
  01:30:02Z). Date-only label is one UTC day early.

Neither finding touches computation, gates, evidence hashes, or outcome exposure.

## Verdict

AUTHORIZED_FOR_SCORED_RERUN — the remediation is exactly as claimed (single-purpose
parse fix, byte-scoped), attempt 1 left zero outcome exposure, the freeze chain v1/v2/v3
is intact with all 8 v3 hashes recomputed-matching, fixtures pass, the dry run passes
84/84 with distinct IDs and a clean leak scan, GO authorization is preserved byte-exact,
and the parse fix demonstrably resolves the reported failure while keeping all 84 record
IDs pairwise distinct. Scored mode may be re-run under the already-consumed GO.
