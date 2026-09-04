# A7 INDEPENDENT AUDIT REPORT — FREE DATA FUSION V1

- Auditor: A7 (independent; no shared output with A1/A2/A3/A4 before this verdict)
- Audit worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/data-fusion-v1/a7-audit`
- Branch: `orca/data-fusion-v1-a7-audit`
- Candidate SHA audited: `c6a0576ef98dd4392e90805c8ba33821da62eabc`
- Base SHA (owner plan on main): `047c68524760f6bee9798682f6cd7723657ed53c`
- Audit date: 2026-09-04
- Method: all items recomputed independently in this worktree (code read, tests re-run,
  golden cases built from scratch via in-memory python, git history inspected).
  No tracked file was modified; the only file created by this audit is this report.

---

## 0. INTAKE

| Check | Expected | Observed | Result |
| --- | --- | --- | --- |
| `git rev-parse HEAD` | `c6a0576ef98dd4392e90805c8ba33821da62eabc` | identical | PASS |
| `git branch --show-current` | `orca/data-fusion-v1-a7-audit` | identical | PASS |
| `git status --porcelain=v1` (pre-audit) | clean | empty output | PASS |

---

## 1. ITEM-BY-ITEM RECOMPUTATION

### (a) Future-vintage leakage — PASS

Evidence:

- `research/data_fusion/pit.py`: `select_asof` filters candidates through
  `NormalizedRecord.eligible_at(T)`, which requires `available_time_utc <= T`
  (and `effective_time_utc <= T` when effectiveness is required and present).
  A revision can never be selected before its own availability instant.
- Existing test `tests/data_fusion/test_pit.py::test_later_revision_does_not_leak_backward`
  re-run as part of the 204-test suite: PASS.
- Independent golden case (built from scratch in this audit, not copied from tests):
  v1 available 2024-05-01T23:59:59Z value 4.0; v2 available 2024-06-15T23:59:59Z value 4.25.
  - G1a `select_asof(..., T=2024-06-01).value == 4.0` PASS (revision invisible)
  - G1b `select_asof(..., T=2024-06-16).value == 4.25` PASS
  - G1c `select_asof(..., T=2024-05-01T12:00) is None` PASS
  - G2 a record retrieved 2026-08-01 is still eligible for a 2024 decision because
    `available_time` (evidence-based), not `retrieved_time`, gates eligibility. PASS.

### (b) available / effective / vintage / retrieved semantics — PASS

Evidence:

- `research/data_fusion/models.py`: `available_time_utc > retrieved_time_utc` and
  `vintage_time_utc > retrieved_time_utc` are construction errors (G3 PASS).
  `retrieved_time` is never written into `available_time` by any adapter — all six
  adapters derive availability from owner-captured `ReleaseEvidence` only.
- SEC: `research/data_fusion/adapters/sec.py` maps date-only `filingDate` to
  `end_of_utc_day(filed_day)` with `AvailabilityBasis.DATE_ONLY_UPPER_BOUND` and note
  `SEC_FILED_DATE_ONLY_NOT_EXACT_AVAILABILITY`. `acceptanceDateTime` seeds event/effective
  time only, never availability (`SEC_ACCEPTANCE_TIME_NOT_DISSEMINATION_PROOF`), and an
  acceptance after the end-of-day bound is refused. `require_exact_availability()` raises
  `NON_EXACT_AVAILABLE_TIME_FORBIDDEN` for date-only evidence (tested in test_sec/test_finra/test_truefx).
- ECB / BIS: `parse_series` / `parse_policy_rates` raise `MISSING_AVAILABLE_TIME_EVIDENCE`
  when `release_evidence is None` (re-verified independently: G10 PASS). SDMX
  `header.prepared` is validated for shape only and never used as availability.
- FRED/ALFRED: `realtime_start` vintage date is date-only proof → end-of-vintage-UTC-day
  upper bound; exact wire release time is a forbidden inference field.
- TrueFX: monthly archive with no publication timestamp → availability = END of the
  archive month (UTC), `DATE_ONLY_UPPER_BOUND`, note `TRUEFX_MONTH_END_UPPER_BOUND`;
  no tick eligible before month end (verified by test and by audit probe).

Boundary probe (reproduced in audit): the TrueFX fixture's last tick
(event 2024-01-31T23:59:59.999Z) has `available_time = 2024-01-31T23:59:59Z` and is
`eligible_at(2024-01-31T23:59:59.500)` — i.e. `event_time > available_time` by <1s.
See Finding F1 (LOW). Direction is fail-safe everywhere else; leakage window <= 1 second
at day boundaries.

### (c) Current-ticker backward projection — PASS

Evidence:

- `research/data_fusion/identity.py`: `TemporalAlias.active_at(t)` requires
  `available_time_utc <= t AND valid_from_utc <= t AND (valid_to is None or t < valid_to)`.
  A current alias (`valid_from` in the future relative to the query, or only known later)
  resolves to `None` for earlier timestamps.
- Test `test_current_alias_is_not_projected_backward` PASS.
- Independent golden: current alias NEW (valid_from 2022) at 2020 → None (G6a);
  at 2023 → SEC-1 (G6b); alias with `available_time` 2021 is not usable at 2019 (G6c).

### (d) Conflict refusal — PASS

Evidence:

- `research/data_fusion/conflicts.py::SourcePolicy.primary_source`: zero PRIMARY →
  `ConflictError("NO_PRIMARY_SOURCE_DECLARED")`; more than one →
  `ConflictError("MULTIPLE_PRIMARY_SOURCES")`. Exactly one is required.
- `research/data_fusion/pit.py`: `VintageSeries.append` refuses different content at an
  already-filled `(available, vintage, retrieved)` rank with `AmbiguousVintageError`
  (`AMBIGUOUS_VINTAGE_RANK`); byte-identical re-append is idempotent; earlier records are
  never mutated (frozen dataclass, new tuple on append).
- `select_asof` raises `AmbiguousVintageError` when the winner's rank carries two distinct
  canonical payloads.
- Independent golden: G4 same-rank overwrite refused; G4b series unchanged after refusal;
  G5 append-only growth with original series intact.

### (e) No cross-source gap patching — PASS

Evidence:

- `resolve_primary(records, policy)` returns `primary` exclusively from the policy's single
  PRIMARY source; CROSS_CHECK/DIAGNOSTIC rows are returned in a separate `checks` mapping
  and are never merged into `primary` when it is empty.
- Test `test_cross_check_never_patches_primary_gap` PASS; independent golden G9 PASS
  (TWELVE_DATA row with empty SEC primary → `primary == []`).

### (f) Manifest determinism and raw-hash binding — PASS

Evidence:

- `SourceManifest.canonical_payload()` sorts `files` by path; `canonical_json_bytes` uses
  `sort_keys=True, separators=(",",":")` with `allow_nan=False`. Duplicate raw paths refused;
  path traversal refused; sha256 lowercase 64-hex enforced in both `RawFileEvidence` and
  `NormalizedRecord` (`^[0-9a-f]{64}$`).
- Independent golden: G7a manifests built with files in opposite order share a digest;
  G7b digest equals an independently computed `sha256(json.dumps(payload, sort_keys=True,
  separators=(",",":")))`.
- Raw binding: G11 — every ECB record's `raw_sha256` equals `sha256(fixture bytes)` of the
  committed fixture; `AdapterOutput.raw_sha256 = RawResponse.sha256_hex()` of actual body bytes.

### (g) License/entitlement fail-closed — PASS

Evidence:

- `evaluate_authority` (authority.py): unknown internal-research right →
  `CANDIDATE_NOT_AUTHORIZED` (`INTERNAL_RESEARCH_RIGHT_UNKNOWN`); key required but not
  authorized → `ACCOUNT_OR_KEY_NOT_AUTHORIZED` → not authorized; missing historical
  available time → `HISTORICAL_AVAILABLE_TIME_MISSING` → not authorized; forbidden
  local storage → `REJECTED_LICENSE`. Only a fully-evidenced record yields
  `AUTHORIZED_INTERNAL_RESEARCH` (G8a–G8d PASS).
- `research/data_fusion/source_registry.py::SOURCES`: 10 sources, none
  `AUTHORIZED_INTERNAL_RESEARCH` (asserted by `test_source_ids_are_unique_and_not_implicitly_authorized`).
- `research/control/data_fusion_v1_run/source_registry.json`: all 10 sources carry
  `verdict: NOT_USABLE_FOR_SCORED_RESEARCH`; adapters present are `DOCUMENTED_CANDIDATE`
  or `CANDIDATE_NOT_AUTHORIZED`; key-gated FRED/Alpha Vantage/Massive/Twelve Data stay
  `CANDIDATE_NOT_AUTHORIZED` (`entitlement_id=api-key-required-not-provisioned` for FRED).
- Every adapter class declares `authority_status != AUTHORIZED_*` (asserted per-adapter in
  test_sec/test_ecb/test_bis/test_finra/test_fred/test_truefx). TRUEFX evidence doc records
  license rights as UNKNOWN / PENDING with `terms_captured = NO` (fail-closed).

### (h) Raw data not tracked in Git — PASS

Evidence:

- `git diff --name-only BASE..HEAD` adds exactly 7 data files, all in
  `tests/data_fusion/adapters/fixtures/`: `bis_cbpol.json` (568 B), `ecb_sdmx_exr.json`
  (713 B), `finra_shortsale_daily.txt` (138 B), `fred_alfred_obs.json` (655 B),
  `fred_vintagedates.json` (29 B), `sec_companyfacts.json` (1,225 B),
  `sec_submissions.json` (403 B), plus `truefx_ticks_usdjpy.csv` (138 B). All are visibly
  hand-written (read in full by auditor; e.g. `sec_companyfacts.json` contains 3 facts and
  the entityName "Handwritten Fixture Issuer"), provenance documented in
  `tests/data_fusion/adapters/fixtures/README.md` and per-lane evidence MDs.
  No ZIP/parquet/bulk archive is added; the TrueFX ZIP is built in memory from the tiny CSV.
- All other tracked `.parquet/.csv/.json` files in the repo (`catalog/data/...`,
  `results/...`, prior-cycle audits) pre-date this cycle and are absent from the BASE..HEAD diff.
- Note: `sec_companyfacts.json` is 1,225 bytes, marginally above the 1 KB heuristic in the
  audit checklist; substance (tiny hand-written fixture) is satisfied — recorded as INFO (F4).

### (i) Zero S1 / zero PnL / zero strategy — PASS

Evidence:

- `git diff --stat 047c685..HEAD`: 73 files, +6,509 / -0, containing ONLY
  `research/data_fusion/**`, `tests/data_fusion/**`,
  `research/control/data_fusion_v1_run/**`. No asset-cycle file, no scoring engine,
  no PnL path, no deployment artifact.
- Keyword scan of the full diff for `pnl|backtest|sharpe|drawdown|strategy|broker|s1_`:
  every match is a negative control statement ("scored_cells: 0", "no strategy PnL",
  "never auto-unlock a carry strategy", forbidden-action lists) — zero strategy code.

### (j) Fixture expectations recomputed by hand — PASS (7 fixtures verified)

| Fixture | Hand-computed expectation | Test assert | Match |
| --- | --- | --- | --- |
| `ecb_sdmx_exr.json` | series `0:0:0:0:0` → `D.USD.EUR.SP00.A`; obs[0]=2024-01-02 → **1.0951**, obs[1]=2024-01-03 → 1.0969; availability = end of evidence day 2024-01-03 | `value == 1.0951`, entity `ECB:EXR:D.USD.EUR.SP00.A`, `available == 2024-01-03T23:59:59Z` | YES |
| `bis_cbpol.json` | series `0:0` → `US.P`; 2024-03-20 → **4.0**, 2024-05-01 → 4.25 | `value == 4.0`, event/effective 2024-03-20, available 2024-05-01T23:59:59Z | YES |
| `finra_shortsale_daily.txt` | AAPL 1000/100/5000 mkt B; MSFT 2000/0/7000 mkt Q; 8 records total | identical asserts | YES |
| `truefx_ticks_usdjpy.csv` | 3 ticks: 141.085/141.115, 141.090/141.120, 141.095/141.125; first event 2024-01-01T22:00:00.123Z; month-end bound 2024-01-31T23:59:59Z | identical asserts incl. microsecond timestamp | YES |
| `fred_vintagedates.json` | two vintages 2024-01-12, 2024-02-09 → end-of-day availability | identical asserts | YES |
| `fred_alfred_obs.json` | 2023-12-01 revised 272.712 → 272.690 across two vintages (both kept); 2024-01-01 `.` → null; revision ineligible at 2024-02-09T12:00, eligible 2024-02-10 | identical asserts | YES |
| `sec_submissions.json` / `sec_companyfacts.json` | accn 0000000001-24-000001 accepted 2024-01-03T14:30Z (event 14:30, avail EOD); Assets 5000 (avail 01-08 EOD) and revision 5100 (avail 04-15 EOD), same period end; dei instant 1000 shares; Revenues (duration) skipped with count 1 | identical asserts | YES |

### (k) Compatibility gates re-run in audit worktree — PASS (4/4)

| Gate | Command | Result |
| --- | --- | --- |
| data_fusion suite | `.venv/bin/python -m pytest tests/data_fusion -q` | **204 passed** in 0.50s |
| protocol suite | `.venv/bin/python -m pytest tests/test_protocol_contracts.py tests/test_protocol_metrics.py -q` | **21 passed** |
| compileall | `.venv/bin/python -m compileall research/data_fusion` | exit 0 |
| git diff --check | `git diff --check` | exit 0 |

Full-suite record (`research/control/data_fusion_v1_run/gates/integration_full_suite.json`)
reviewed, not re-run: exit 0, "1116 passed, 16 warnings in 65.51s" (run alone at HEAD^
`b02df77c8fac1afafb254999ae5a7b8bbac62f4b`, i.e. the tree state this cycle froze before
adding gate records), workers documented as zero. All 10 gate JSONs carry exit_code,
`output_sha256` and verdict; **all 10 recorded `output_sha256` values were re-hashed by the
auditor against the committed `*.stdout.txt` files and match exactly** (empty-output hash
`e3b0c442...` for `git diff --check` is the canonical sha256 of zero bytes — correct).

### (l) Control plane — PASS

Evidence:

- `event_log.jsonl`: seq 1..12 strictly increasing, no gaps/duplicates (programmatically
  verified); append-only JSONL; a self-correction event (seq 8 CORRECTION_SEQ7) is logged
  rather than rewriting history.
- Gate records: see (k) — exit codes + verified output hashes.
- `lane_worktrees.json` vs `git log`: A2 delivery `8384b871...`, A3 `cba3549b...`,
  A4 `8a3187f6...` all exist as commit objects (`git cat-file -t` = commit) and integrate as
  cherry-picks `7787c78` (A2 stocks), `561185f` (A3 macro), `8cd4aa7` (A4 TrueFX) — all three
  present in `git log --oneline` with matching subjects. Lane base `ce0037bf` (DF1 + shared
  base layer) also exists; deviation note for lane base is recorded in the manifest and event
  log (transparent, no history rewrite).
- `run_contract.json` matches PLAN_data_fusion.md boundaries (Crypto V12 never adopts V1;
  Stocks V4 / Forex V2 pre-freeze-only).

### (m) No modifications made

No tracked file was edited, added, staged, committed or reset. The sole file created by this
audit is this report (untracked).

---

## 2. FINDINGS

No CRITICAL or HIGH findings.

| ID | Severity | Summary |
| --- | --- | --- |
| F1 | LOW | `end_of_utc_day()` returns `23:59:59.000000`, one second short of the true day end. A record whose event falls in the final second of its bound day can carry `event_time > available_time` (reproduced: TrueFX tick 2024-01-31T23:59:59.999Z is `eligible_at(23:59:59.500)`). Worst-case mis-timing is <1 second, only in the final second of a date-only bound; all decisions earlier in the day remain conservative. Recommendation for a future cycle: define the bound as next-day midnight minus 1 microsecond (or `23:59:59.999999`). |
| F2 | LOW | `select_asof` rank tie-break includes `retrieved_time_utc` + `raw_sha256`. Two records with identical `(available, vintage)` but different content and different retrieval instants are silently ranked (later retrieval wins) instead of refused; `AmbiguousVintageError` fires only when all three rank fields match. Not a leakage (availability is identical) and deterministic, but a content-conflict blind spot for a source that mutates bytes without bumping its vintage date. Mitigated today by adapter duplicate refusals and two-pull-equality tests on expected-immutable sources. |
| F3 | LOW | `research/control/data_fusion_v1_run/state.json` has `updated_at_utc = 2026-09-04T02:31:23Z` (equal to `created_at_utc`) although its `steps` describe the lane merges completed 03:13:07Z. Stale metadata field only; the content itself is corroborated by event_log and git log. |
| F4 | INFO | `sec_companyfacts.json` fixture is 1,225 bytes (checklist heuristic said "<1KB"). It is manifestly a 3-fact hand-written fixture documented in `fixtures/README.md`; no policy violated. |
| F5 | INFO | Consequence of F1: an SEC `acceptanceDateTime` in the final second after 23:59:59.000 of the filed day would be refused (`SCHEMA_INVARIANT_VIOLATED`). Direction is fail-closed (no leakage); real EDGAR acceptance windows make this practically unreachable. |

---

## 3. GATES SUMMARY (self-run)

- `tests/data_fusion`: 204 passed (0 failed)
- `tests/test_protocol_contracts.py tests/test_protocol_metrics.py`: 21 passed (0 failed)
- `python -m compileall research/data_fusion`: exit 0
- `git diff --check`: exit 0
- Gate-record hash audit: 10/10 recorded `output_sha256` match committed stdout files
- Golden independent recompute: 21/21 checks passed
- Fixture hand-recompute: 7/7 fixtures match test asserts

---

## 4. VERDICT

All leakage, identity, conflict, provenance, authority and boundary invariants hold under
independent recomputation. No unresolved CRITICAL or HIGH findings; findings F1–F5 are
LOW/INFO and do not block.

VERDICT: DATA_FUSION_V1_FREEZE_AUTHORIZED
