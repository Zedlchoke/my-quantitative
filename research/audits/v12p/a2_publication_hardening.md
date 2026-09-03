# V12P Lane A2 — publication and ledger hardening (audit)

Branch `orca/v12p-a2-ledger`, bootstrap `8bfbae5073d0d2079a18863d060084cc929ba7a4`.
Factory repairs only: no PnL computed, no family strategy code touched,
`research/control/v12_run/*` opened READ-ONLY.

## Deliverable verdicts

| # | Deliverable | Verdict |
|---|-------------|---------|
| 1 | Zero-position publication guard (L-V11-4) | DONE |
| 2 | Refusals are accounting events (observed exactly once, never publishable) | DONE |
| 3 | Exact replay idempotence (same trial_key incl. arm_config_digest) | DONE |
| 4 | Family-contract cell guard (L-V11-1 generic superset) | DONE |
| 5 | Portable ledger transfer + manifest regeneration (L-V11-5) | DONE |
| 6 | Dedicated tests (refusal/idempotence/superset/manifest/concurrency/migration) | DONE |

## What changed

- `research/adapter_v10/publish.py` (+27/−3): `evaluate_pre_score_gate` gains an
  opt-in `position_evidence` flag that delegates to the V12 validator;
  `publish_trial` gains `require_position_evidence`. Defaults preserve the exact
  historical behavior — the legacy path refuses only when the caller opts in,
  so V10/V11 semantics only get stronger, never weaker.
- `research/v12/accounting.py` (new): the always-guarded V12 publication entry
  point `publish_v12_cell` plus the V12 ledger package machinery
  (`read_v12_ledger`, `append_v12_row`, `v12_denominator_view`), the
  position/decision-fill evidence gate, the trial-key builder, and the
  family-contract cell guard (`freeze_family_cell_contract`,
  `validate_family_contract_cells`, `enforce_family_contract_cells`).
- `research/v12/ledger_transfer.py` (new): `verify_transfer_manifest`
  (recomputed sha256/bytes/rows per file, fail-closed `TRANSFER_MANIFEST_*`
  reason codes, root-escape guard), `regenerate_transfer_manifest`,
  `write_transfer_manifest` (atomic, no silent overwrite), `verify_or_refuse`.
- `tests/test_v12p_a2_publication.py` (new, 13 tests): every ledger lives under
  `tmp_path`; the frozen `schema.json` and tracked `transfer_manifest.json` are
  pinned READ-ONLY.
- `research/v11/publication_identity.py`: UNTOUCHED — no identity change was
  required (the v2 `arm_config_digest` already covers deliverable 3's key
  material; V12 reuses it via `publication_identity.arm_config_digest`).

## Calling convention for V12 drivers (deliverable 4 documentation)

1. Freeze the per-family cell list from the family contract (probe the frozen
   folds contract — the derivation itself is lane A4's) and pass it as
   `family_contract_cells` (StressSpec instances or signature mappings).
2. Publish each computed cell exactly once via
   `research.v12.accounting.publish_v12_cell(...)` with the identity fields
   including `arm_config_digest`.
3. Outcomes are honest and mutually exclusive: all gates pass → one
   `CELL_RESULT` row (published +1); any refusal (superset cell, pre-score,
   zero positions, no valid decision/fill) → one `OBSERVATION` row (observed
   +1, never publishable); exact replay of the same `trial_key` → no row, both
   counters unchanged (`stage=IDEMPOTENT_REPLAY_SKIPPED`).
4. Read counters only via `v12_denominator_view`.

## Reason codes (stable)

`REFUSED_ZERO_POSITIONS`, `REFUSED_NO_VALID_DECISION_FILL`,
`REFUSED_POSITION_COUNT_ABSENT`, `REFUSED_POSITION_COUNT_INVALID`,
`REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT`, `REFUSED_PRESCORE_FLAG_FALSE`,
`REFUSED_PRESCORE_FIELD_ABSENT|NON_FINITE|NOT_NUMERIC`,
`REFUSED_TRIAL_KEY_ALREADY_PRESENT`;
transfer: `TRANSFER_MANIFEST_{SCHEMA_MISMATCH,NO_FILES,FILE_MISSING,
SHA256_MISMATCH,BYTES_MISMATCH,ROWS_MISMATCH,PATH_ESCAPE,EMPTY_SEED_MISMATCH}`.

## Required command results

- `pytest tests/test_v12p_a2_publication.py tests/test_v11p_a2_publication.py -q`
  → **30 passed** (13 + 17), 0 failed.
- `compileall research/v12 research/adapter_v10` → OK.
- `git diff --check` → clean.
- Extra regression insurance (A1 owns the full suite): `test_adapter_v10_g1`,
  `test_acceptance`, `test_adapter_acceptance_v10_g3`, `test_fault_injection_v10`
  → 65 passed, 0 failed.

## Preservation guarantees

- Historical V10/V11 ledger keys remain readable (`legacy_v1_key` regression
  pinned in the new suite); no old ledger byte is rewritten anywhere — V12
  writes go to the separate `results/registry/experiments_v12.jsonl` package
  ledger only.
- Exactly-once / fail-closed semantics only get stronger: trial_key uniqueness
  and row-schema validity are verified on every read AND append; a corrupt or
  violating ledger refuses all further appends.

## Assumptions

See `a2_publication_hardening.json` (`assumptions`): V12 entry point scoping,
schema.json row-format coexistence with the historical global ledger,
driver-supplied frozen cell lists, and the honest `UNAVAILABLE_GIT_HEAD`
fallback for `producer_head_sha`.

Blockers: none.
