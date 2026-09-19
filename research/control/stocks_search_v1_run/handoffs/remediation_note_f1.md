# remediation_note_f1 — STOCKS-SEARCH-V1 / ssearch-remediation-f1

Schema: remediation_note@1 | Cycle: STOCKS-SEARCH-V1 (store label
ZCODE-ORCHESTRATION-V3) | Role: quant-implementer | Lane: ssearch-remediation-f1
Base: c9d2fc706c7da612f4ce5c1f3d3c7028f60e0457 on
`orca/stocks-search-v1-integration` (worktree
`.worktrees/stocks-search-v1/integration`; HEAD verified == base before work).

## Finding (A7 prelaunch audit, F-1, HIGH)

`research/control/stocks_search_v1_run/audits/a7_prelaunch_stocks_search_v1.json`
verdict BLOCKED_PRELAUNCH. The scored E-run data plane (live gitignored bytes
under `p0/raw/eod_cache`) had NO load-time control binding it to the frozen
chain: `load_real_data()` accepted caller-supplied `cache_dir` and
`retrieval_manifest_path` while verifying neither

- the committed retrieval manifest sha (`2c4283c2…`, pinned in
  `s/selection_freeze.json` `data_manifests_sha256`),
- the frozen pooled position-series digests of the 3 S-selected arms
  (`6fd58cc9…` GAP / `495d9bca…` 52W-HIGH / `f55a14ba…` VOL-REGIME,
  `pooled_series_stats.series_sha256`), nor
- the rebuilt fired/bookable_fired census cells against the frozen
  `p0_census.json` rows (141 (config, fold) cells; 282 with fired+bookable).

A drifted/backfilled cache would have flowed straight into scored numbers.
GO condition C-2 requires this preflight to exist, run and pass before the
owner GO gate re-opens.

## Fix (narrow, exactly this)

1. **`verify_data_plane(cache_dir, retrieval_manifest_path, *, …)` in
   `i/i_engine.py`** — mandatory fail-closed preflight; returns a PASS
   verdict artifact (`stocks_search_v1_data_plane_preflight@1`) or raises
   `DataPlaneMismatch` (STOP label INPUT_MISMATCH) carrying the full verdict.
   Checks, in order:
   1. freeze identity — production uses the committed S freeze byte-pinned
      by `verify_freeze` (FREEZE_SHA256 + `arm_identity_sha256` x3 + params +
      family, audit item ii); injected freeze paths (synthetic tests only)
      must still be `SELECTION_FROZEN` and carry the 3 frozen arms verbatim.
   2. consumed-artifact sha pins vs `data_manifests_sha256` — `p0_lib.py`
      (via `load_p0_lib(expected_sha=…)`), `p0_run.py` (newly pinned import),
      `census_configs.json`, `p0_census.json`, `p0_census_cohort.json.gz`,
      `retrieval_manifest.json`.
   3. retrieval-manifest commitment — any caller path ≠ the committed
      `p0/retrieval_manifest.json` is REFUSED
      (`retrieval_manifest_substitution_refused`); the committed file must
      hash to the freeze pin (`retrieval_manifest_sha_pin`); schema/cycle_id
      must match the freeze.
   4. retrieval completeness — every pull status 200; pull set ==
      cohort-census set (both directions); SPY present (F7 benchmark pin).
   5. calendar + folds — SPY-pinned S0-window calendar re-derived from the
      cache and matched to the freeze calendar pin (n/first/last/sha256);
      freeze B1/B2 == the `p0_lib.fold_boundaries` calendar-thirds law.
   6. per-pull identity — cache file present for every status-200 pull;
      manifest per-pull digest pins (`sha256_gz`/`sha256_raw`, the fresh-pull
      record class) verified where carried; parsed served count == the
      digest-pinned cohort census `served` count for EVERY name
      (`names_served0` = parse→None with census served==0; `names_short` =
      parsed <3 sessions — s_select.heavy_pass counter laws, verified too).
   7. pooled-series digests — the 3 arms' pooled daily position-COUNT series
      rebuilt by `_rebuild_data_plane` (the s_select r3 heavy pass, READ-ONLY
      reuse of `p0_run.parse_name` + `p0_lib.run_config_census` in P0 census
      space: full served history, warm gate in served-session index space,
      fold-by-decision-DATE, full-history med60, per-name bincount pooling by
      held-session DATE onto the SPY-pinned calendar) and compared EXACTLY —
      `positions_used`, `position_days`, `death_censored_legs`, `pooled_max`,
      `pooled_nonzero_days`, `series_sha256` — to the S freeze's
      `pooled_series_stats`.
   8. census cross-check — rebuilt per-config per-fold `fired` /
      `bookable_fired` == frozen `p0_census.json` rows EXACTLY for every
      census config sharing the 3 rebuilt states (s_select r3 282-cell gate
      comparison form, restricted to the arms' states: 9 arm cells minimum,
      H-variant cells included), plus the freeze's embedded
      `p0_census_per_fold_verbatim` == census rows for the 3 arm cells
      (canonical-JSON equality, the s_select `input_census_rows_equal_141`
      approach).
2. **Wiring** — `i/adjudicate.py` `load_real_data()` now calls
   `verify_data_plane(cache_dir, retrieval_manifest_path)` immediately after
   the exact-phrase GO gate + `verify_freeze()` + `load_p0_lib()` and the
   existing cache-dir existence check, BEFORE any cohort byte is parsed; a
   `DataPlaneMismatch` refuses the E run (nothing loads). The loader now
   parses the COMMITTED manifest path itself (the only path the preflight
   can ever verify) and attaches the PASS verdict artifact to its return as
   `data_plane_preflight`.
3. **F-4 fold-in (MEDIUM, cheap)** — new i_engine constant
   `RETRIEVAL_EMPTY_COUNT_DISCLOSURE_VERBATIM` (n_empty_or_no_series=0
   counts FRESH pulls only; authoritative zero-served count is 7,476 names)
   is carried on every `adjudicate_candidate` report as
   `retrieval_empty_count_disclosure` (the E-run verdict skeleton) and on
   the preflight verdict.

Static identity proof against the REAL chain (read-only, no execution): the
committed manifest hashes to `2c4283c2…` == the freeze pin; all 10
`data_manifests_sha256` pins match disk; SPY is a status-200 pull with
served==2943 == the freeze calendar `n_sessions`; fold law reproduces
B1/B2 = 2018-11-27/2022-10-22.

## Test evidence (synthetic fixtures ONLY; NO real-data execution)

`tests/test_stocks_search_v1_i.py` — new section builds a fabricated
consistent mini data plane (cache, retrieval manifest with one
digest-carrying fresh-pull record, cohort census, census configs with one
H-variant per state, p0 census, freeze) generated by the SAME rebuild
machinery the preflight verifies with:

- `test_data_plane_preflight_pass_on_consistent_fixture` — PASS verdict;
  all checks pass; 3 arm digests verified; 18 census cells checked (>= 9
  arm cells); fires land in more than one fold; F-4 disclosure present.
- `test_data_plane_preflight_refuses_manifest_substitution` — (a)
  byte-identical manifest copy at another path →
  `retrieval_manifest_substitution_refused`; (b) doctored manifest at the
  REDIRECTED committed path → `retrieval_manifest_sha_pin`; (c) the real
  committed manifest under a fixture freeze → `retrieval_manifest_sha_pin`.
- `test_data_plane_preflight_refuses_positions_digest_mismatch` — tampered
  `series_sha256` → `pooled_series_digests`; tampered `positions_used`
  stat → same gate.
- `test_data_plane_preflight_refuses_census_count_mismatch` — drifted
  `fired` (+1) with census sha re-pinned and freeze excerpt synced →
  `census_cells_equal_p0_census` naming `{cell}` with got == want-1.
- `test_data_plane_preflight_refuses_cache_drift` — tampered cache bytes →
  `per_pull_digest_gz`; missing cache file → `cache_file_present`;
  served-count drift → `served_count_vs_cohort_census`.
- `test_load_real_data_runs_preflight_inside_the_go_gate` — wiring: with
  the exact GO phrase and the real committed control artifacts, an unbound
  cache dir is refused INSIDE `load_real_data`
  (`spy_cache_present` → INPUT_MISMATCH); reads committed artifacts only.
- `test_adjudicate_verdict_skeleton_carries_retrieval_disclosure` — F-4
  disclosure line carried verbatim on every verdict skeleton.

Suite results (root venv): `test_stocks_search_v1_i.py` **51 passed** (44
pre-existing + 7 new; the pre-existing GO-gate test is unchanged and green —
the FileNotFoundError branch fires before the preflight);
`test_stocks_search_v1_p0.py` **25 passed**;
`research/control/stocks_search_v1_run/m0/test_m0_golden.py` **M0 PASS
(10 gates)**, exit 0 (byte-exact lineage untouched).

## Scope discipline

Changed files: `i/i_engine.py`, `i/adjudicate.py`,
`tests/test_stocks_search_v1_i.py`, this note. No scored execution, no
scored outputs, D2 SKIPPED per §3b, no real-data reads (only committed
control artifacts), budget remains 0/3, no push/merge/rebase, no writes
outside the allowlist. The F-1 remediation item "correct all GO-facing
digest references (remove the forex 85c8f875/57eed8b9/7eee7cf0 citations)"
is NOT a file this lane may write (dispatch packet / owner GO documentation);
the correct stocks digests are restated here and in the handoff for the
orchestrator to carry into the GO-facing packet.
