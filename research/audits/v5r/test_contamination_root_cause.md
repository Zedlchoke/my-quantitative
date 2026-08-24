# Test Contamination Root Cause — V5-C02 (immutable V3 provenance drift)

Sprint: V5R/V6 Orca 2026-08-24 · Author: A2 (provenance) via A1 integration · Status: PROVEN (mechanism), historical mutation NOT restored

## 1. What drifted

Frozen baseline `research/audits/v5/v3_v4_source_hashes.json` (frozen_at_utc 2026-08-24T04:24:29Z,
baseline commit e00c5351) records SHA-256 for 1474 paths. Independent recomputations
(pre-test and post-test this sprint; plus A6's independent full-population sweep)
all agree on exactly 7 differences:

| path | class |
|---|---|
| results/stage_a_v3/EXP-20260824-0001/execution_evidence.json | UNEXPECTED_MUTATION |
| results/stage_a_v3/EXP-20260824-0001/frozen/candidate.yaml | UNEXPECTED_MUTATION |
| results/stage_a_v3/EXP-20260824-0001/launch_manifest.yaml | UNEXPECTED_MUTATION |
| results/stage_a_v3/EXP-20260824-0002/execution_evidence.json | UNEXPECTED_MUTATION |
| results/stage_a_v3/EXP-20260824-0002/frozen/candidate.yaml | UNEXPECTED_MUTATION |
| results/stage_a_v3/EXP-20260824-0002/launch_manifest.yaml | UNEXPECTED_MUTATION |
| results/registry/experiments.jsonl | EXPECTED_APPEND_ONLY |

Evidence: `research/audits/v5/source_hash_recheck_v5.json` (prior agent),
`research/audits/v5r/source_hash_recheck_v5r_pretest.json`,
`research/audits/v5r/source_hash_recheck_v5r_posttest.json`.

## 2. Root cause (proven from code + mechanism demo)

`run_matrix()` declared `stage_a_root: str | Path = DEFAULT_V3_STAGE_A_ROOT`.
Python binds default arguments **once, at function definition time**, so the
signature held a live reference to the real immutable zone
(`results/stage_a_v3`, resolved against CWD = repo root). The autouse fixture in
`tests/test_matrix_runner.py` monkeypatched registry/data-contract paths into
`tmp_path` but did not redirect `stage_a_root`; even if it had patched the module
attribute `DEFAULT_V3_STAGE_A_ROOT`, the already-bound parameter default would
keep targeting the real directory (stale-binding semantics). Consequently every
test exercising the launch-provenance wrapper wrote real
`launch_manifest.yaml`, `execution_evidence.json`, and frozen snapshots into
`results/stage_a_v3/EXP-20260824-000{1,2}` — the exact three files that drifted,
in exactly the two experiments referenced by those tests.

Mechanism demonstration (no repository writes): scratch script
`b1_mechanism_proof.py` output:

```json
{
  "module_default_points_into_real_results": "/Users/hoangminhlong/my-quantitative/results/stage_a_v3",
  "patched_signature_default": "None",
  "late_bound_resolution_under_monkeypatch": ".../tmp.../redirected",
  "stale_binding_still_targets": "/Users/hoangminhlong/my-quantitative/results/stage_a_v3"
}
```

## 3. Fix under test (uncommitted defensive patch, now reviewed)

1. `run_matrix(..., stage_a_root=None)` — late-binds the module default at call
   time so monkeypatching takes effect.
2. Autouse fixture additionally redirects `DEFAULT_V3_STAGE_A_ROOT` to
   `tmp_path / "stage_a_v3"` so no test can write the real zone.

Regression evidence this sprint:

```text
command : .venv/bin/python -m pytest tests/ -q
start   : 2026-08-24T10:47:50Z  end: 2026-08-24T10:48:00Z  exit_code=0
summary : 557 passed, 16 warnings in 9.38s   (0 failed, 0 xfailed)
pre-test  recheck: MATCH=1467 EXPECTED_APPEND_ONLY=1 UNEXPECTED_MUTATION=6 MISSING=0
post-test recheck: identical counts and identical diff set (no new mutations)
```

The patch prevents recurrence. It does NOT restore original bytes and does not
change the V5-C02 verdict.

## 4. Exact-byte recovery outcome (bounded search per PLAN §7 C2)

Sources searched read-only: current repo results tree, all 18 old-worktree
result trees (5726 files hashed), full git object store (445 blobs, all history),
local archives (none found within repo depth 2; no backup dirs beside repo).

Outcome: **0 of 6 target files found byte-identical anywhere**.
Evidence: `research/audits/v5r/exact_recovery_search.json`,
`research/audits/v5r/exact_recovery_git_object_sweep.json`.

## 5. Consequence (PLAN §7 C3 decision fork)

Not all six files restored byte-identically ⇒ **V5-C02 = FAIL** ⇒ legacy V5 is
permanently closed as **V5_FAIL**; the compromised experiments are quarantined
(metadata-only, nothing deleted) and the clean-lineage **V5R** protocol
(PLAN §12) governs all further validation work.
