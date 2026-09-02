# S1 A3 — PIT security master, universe, loader, data audit (implementation notes)

Branch: `orca/stocks-s1-data`, base: `a04b8d1b90a3cc079ddf6a726eea9cff86a0a9df` (bootstrap).
Owner: A3. All fixtures are SYNTHETIC — no provider entitlement exists, so no real
provider implementation was written (and none may be added without an entitlement record).

## What was built (PLAN_stocks.md §7 A3, §8 SD0 row)

### provider.py — interface + entitlement policy
- `NO_ENTITLEMENT_FAIL_CLOSED` is the default `entitlement_status` of every
  `ProviderAdapter`; `data_tier()` is `DIAGNOSTIC_ONLY` unless a verified
  `EntitlementRecord` is attached to an authority-capable source class.
- Free convenience sources (`SOURCE_FREE_CONVENIENCE`, e.g. the shipped
  `UnentitledDiagnosticStub`) are structurally barred: even a forged attached
  record cannot promote them (`DiagnosticDataCannotSatisfyAuthorityError`).
- `EntitlementRequirement` is the strict record of what a REAL check requires:
  credentials, permissions, verification procedure, licensed scope, vendor docs.
  `EntitlementRecord` must cover `REQUIRED_LICENSE_SCOPE`
  (PIT_SECURITY_MASTER, DELISTINGS, CORPORATE_ACTIONS, HISTORY_WITH_ADJUSTMENTS).
- `provider_id` + `provider_schema_digest` (sha256 hex) are mandatory identity
  fields, validated with `research.assets.common.contracts` validators, matching
  the optional contract fields of `AssetExperimentContract`.
- The adapter interface deliberately has NO fetch method: no entitled transport
  can be smuggled in behind a diagnostic facade this sprint.

### universe.py — PIT security master + universe
- `SecurityMaster`: stable unique `security_id`, primary exchange, listing and
  delisting dates, `last_valid_event` (final valid event for delisted names);
  ticker history as contiguous inclusive effective ranges starting at the
  listing date and (for delisted names) ending exactly on the delisting date.
  All lookups are `*_as_of`; a retired ticker does not resolve after its range
  and a future ticker does not resolve before it (tested).
- `MembershipTable`: structural ban on current-index-membership backfill —
  `MembershipRecord.effective_from` is a mandatory constructor argument (a row
  without effective dating cannot be expressed) and the table exposes ONLY
  `members_as_of`; there is no `members()`/`current_members()` accessor
  (asserted by test).
- `build_rebalance_snapshot`: retains ACCEPTED and REJECTED rows, each with a
  mandatory non-empty reason; members without metrics fail closed; stable
  canonical sha256 snapshot `digest()`.
- S0 floors as validators (`evaluate_s0_floors` / `assert_s0_floors`):
  >= 8y joint daily history over the ELIGIBLE population, >= 30 eligible names
  per cross-sectional decision, delisting retention via
  `evaluate_delisting_retention` (observations must reach the final valid
  event), and S0 ending >= 12 months before the latest complete date.
- `SealedWindows` / `declare_sealed_windows`: S0 bounds usable, `s1_window()`
  ALWAYS raises `SealedWindowError`, `require_within_s0` fails closed on any
  range that crosses the S0/S1 boundary. The 12-month separation is enforced
  at construction (exact 12 months allowed).

### loader.py — local parquet bars/events (pyarrow)
- Layout `<root>/<security_id>/bars_<YYYY>.parquet` + `checksum_manifest.json`
  (sha256 per file). Every row carries `ts_exchange` and `ts_ingest`
  (tz-aware); `ts_ingest >= ts_exchange` and duplicate exchange timestamps are
  validated (duplicates allowed only via explicit
  `allow_duplicate_timestamps=True` for event streams).
- Fail-closed: missing partition for any covered year, unmanifested or
  tampered file (checksum verified BEFORE read), schema violations, empty
  windows, and gaps beyond a DECLARED `gap_tolerance_days` (required ctor arg,
  no implicit tolerance). When a session predicate is injected, gap accounting
  counts only session days; otherwise raw calendar days count.

### data_audit.py — PIT audit, verdicts PASS/FAIL/NOT_RUN only
- Checks: `checksum_and_partitions`, `pit_timestamps`,
  `regular_session_gaps_explained` (FAIL on ANY unexplained regular-session
  gap between first and last observation; the session predicate is an
  INJECTED `Callable[[date], bool]` — the official calendar belongs to the
  calendar lane, so with no predicate injected the check is NOT_RUN, never a
  silent pass and never a locally implemented calendar),
  `delisting_retention`.
- Overall verdict: FAIL if any check failed, else NOT_RUN if any did not run,
  else PASS. `PitAuditReport.canonical_json()` / `gate_evidence("SD0_DATA_PIT_PASS")`
  provide the payload for the gate evidence file; the audit itself writes nothing.

## Tests (synthetic, tmp_path only)
`tests/assets/stocks/test_universe.py` (24 tests) + `test_data_pit.py` (31 tests):
delisted name, ticker change, rejected snapshot rows, a missing-Friday gap
next to a weekend (proves predicate-scoped gap accounting), tampered/unmanifested/
missing partitions, ingest-before-exchange, duplicate timestamps, holiday-
explained gaps, NOT_RUN without predicate, and a `git status` unchanged proof
(`test_suite_writes_nothing_to_the_repository`).

Acceptance: `.venv/bin/python -m pytest tests/assets/stocks/test_data_pit.py
tests/assets/stocks/test_universe.py -q` -> 55 passed. Full `tests/assets` ->
112 passed; `compileall` clean; protocol contract/metric tests unaffected (21 passed).

## Assumptions / handoffs
- The session predicate signature `(date) -> bool` intentionally matches
  `SessionCalendar.is_session_day` in `research/assets/common/calendar.py` so
  A4's real calendar can be injected directly later.
- `write_bars`/`write_checksum_manifest` are data-preparation helpers for
  staging locations (and test fixtures); the loader itself is read-only.
- Floors: 8y/30-names/12-month buffer are defaults on `evaluate_s0_floors`;
  actual S0/S1 dates stay frozen at real data intake (none exists this sprint).
