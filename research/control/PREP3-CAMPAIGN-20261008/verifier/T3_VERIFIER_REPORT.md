# T3_VERIFIER_REPORT — FRESH-CONTEXT VERIFIER T3, Q1 block-lift gate (owner turn 3)

- verifier: T3 (A7-class independent, fresh context; verified from bytes only; repaired nothing)
- date: 2026-10-08 · cycle `PREP3-CAMPAIGN-20261008` · task `PREP3-FRESH-VERIFY-T3`
- gate under decision: Lead records the owner's two verbatim approvals into a new auth file,
  then deletes `research/control/PREP-FUTURES-Q1Q2Q3-20261007/prospective/COLLECTOR_BLOCKED.json`
  in a dedicated commit.
- code verified at exact HEAD:
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-q1q2q3-prep/prep`
  branch `prep/futures-q1q2q3-prep-20261007`, HEAD `325c40306b878c9edf0c404ff15ff9b4b6980637`
  (parent `256df848` dispatch; grandparent `b8d52076` Lane H fix; `50456e0f` = block commit).
  Re-measured at verification start; worktree porcelain-clean; on-disk blobs == HEAD blobs
  (`git status` empty; `git hash-object` == `git rev-parse HEAD:` for all five prospective files).
- ROOT main HEAD at verification start: `5b1ec2824d78d1dde512492b4619fdbc23241046` (matches the
  commit cited by the Lead's automation dump). No root history rewritten by this verification.

# OVERALL VERDICT: **PASS_WITH_FINDINGS**

The block-lift gate PASSES: the collector code at `325c4030` implements every law the block
was guarding, all prior fail-closed laws are intact, the full suite is 43/43 green (exit 0),
the invariants hold (ledger 0 rows ever, block file byte-identical, skip manifest armed and
verbatim), and 36 auth does not exist yet. Findings F-1..F-5 (one MEDIUM, four LOW) do NOT
block the auth-append + block-removal; F-1 and F-5 are repairable by the Lead before the next
13:30Z fire.

---

## A. COLLECTOR CODE at 325c4030 — file `research/control/PREP-FUTURES-Q1Q2Q3-20261007/prospective/q1_collector.py` (1404 lines)

### A1. Invocation window + fetch cutoff — **PASS**
- L126: `FORECAST_WINDOW_ET = ((10, 0, 0), (10, 5, 0))` — inclusive start, exclusive end.
- L836-841 `in_forecast_window`: `lo <= t < hi` on ET wall-clock tuple — exact `[10:00:00, 10:05:00)`
  America/New_York semantics (AMENDMENT 34).
- L952-958 `forecast_step`: outside window → `NOT_RUN_INPUT_WINDOW_STALE` (exit 5).
- L127 `BAR_COMPLETED_ET = (10,0,0)`; L850-855 `require_bar_completed` → `NOT_RUN_BAR_INCOMPLETE`
  if invoked before the 09:59 bar completes at 10:00:00 ET; called L959.
- L997: fetch `end_et = et_wallclock(session_date, (10, 0, 0))` — fetch endDateTime stays 10:00:00 ET;
  L651-659 `ib_end_str` converts ET→UTC dash; no bar starting ≥10:00 ET can enter.
- L227 `CUTOFF_ET = tod_ns(10, 0)` (exclusive); L714-731 `cut_input_window`: ANY day-D bar
  ts ≥ 10:00:00 ET → `NOT_RUN_BAR_CUTOFF_VIOLATION` (exit 6) for the WHOLE input set; invoked L1001.
- Boundary tests: T10 `test_in_forecast_window_boundaries` (9:59:59 F / 10:00:00 T / 10:04:59 T /
  10:05:00 F); T11 `test_window_boundary_invocations`.

### A2. Three timestamps + append discipline — **PASS**
- `bar_completed_at`: L844-847; recorded as a separate row field at L1032 (result field L987-989).
- `data_arrival_at`: L999-1000 — fetch-return wall-clock per symbol, recorded immediately after each
  fetch; separate per-row field L1033.
- `forecast_made_at`: L1060-1063 — `require_before_deadline` (L858-869) is called immediately BEFORE
  `forecast_made = now_utc_iso()`, which is written only AFTER the full Phase-A loop (L992-1056)
  has fetched BOTH symbols and built BOTH payloads; one shared value stamped into both rows
  (L1062-1063).
- Wall-clock re-checked immediately before EVERY `append_ledger`: L1070-1071 `require_before_deadline`
  inside the append loop, immediately before L1072 `append_ledger`. Also L1060 before the final
  forecast_made_at write. T11 `test_row_timestamp_fields` asserts all three fields, shared single
  `forecast_made_at` post-fetch, and ES→NQ arrival ordering; `test_deadline_expiry_after_fetches_
  appends_nothing` proves the write-gate fires after BOTH fetches with ZERO rows.
- BOTH-before-EITHER: Phase A (L992-1056) fetches + validates + persists raw per symbol but appends
  NOTHING; Phase B (L1057-1077) pre-validates duplicates for BOTH rows (L1064-1069) then appends
  both with per-append rechecks. T11 `test_nq_failure_after_es_fetch_strands_nothing`.

### A3. Block-file refusal — **PASS**
- L872-881 `check_block_file`: `COLLECTOR_BLOCKED.json` exists → `NOT_RUN_BLOCKED_BY_FINDING`
  (exit 14). Called at L943 in `forecast_step` as step 2 — after prechecks (L940), before ANY
  market access. observe_close is NOT gated (L1085-1201 has no block/skip gate) — correct:
  MISSED bookkeeping stays lawful.
- Live evidence at HEAD: `prospective/ops/ops_log.jsonl` line at `2026-10-08T09:16:09Z`
  `TERMINAL_FAIL_CLOSED NOT_RUN_BLOCKED_BY_FINDING exit_code 14` (real production-path refusal
  under the block). T11 `test_block_file_refuses_forecast`; T12 `test_d_block_file_takes_precedence`.

### A4. Session-skip enforcement (NEW, Lane K) — **PASS**
- `load_session_skip` L884-920: loaded ONLY in the forecast path (`check_session_skip` L923-935,
  called at L970). Absent file = lawful no-skip (`set()`); present-but-malformed (bad JSON, wrong
  schema, `sessions` not a list, non-string/non-ISO entries, unreadable bytes) →
  `NOT_RUN_SKIP_FILE_MALFORMED` exit 15.
- Listed session → `NOT_RUN_OWNER_DECLARED_MISSED` exit 15 (L929-934). Positioned AFTER the
  block-file check (L943) and BOTH duplicate checks (L961-965; the second at L1064-1069 is
  post-fetch), BEFORE chain resolution / BLS / any fetch (first fetch L998). Zero market access
  on refusal — T12 `test_a` asserts `fetch_calls == 0`.
- observe_close NOT gated: L1085-1123 — for a session with no forecast row and no NOT_RUN row it
  appends `record_type=session_missed`, `status=NOT_RUN_NO_FORECAST_RECORDED` per symbol
  (idempotent: `SKIPPED_SESSION_ALREADY_NOT_RUN` on repeat). T12 `test_e` proves exactly this with
  zero fetches. T12 `test_f` pins the production manifest to exactly `{"2026-10-08"}`.

### A5. Observe-close endDateTime = UTC-dash form (error-10314 fix) — **PASS**
- The single `reqHistoricalData` site is L688 (`endDateTime=ib_end_str(end_et)`) inside
  `fetch_session_bars`, used by BOTH the forecast path (end_et = 10:00:00 ET, L997) and the
  observe-close path (end_et = 17:10:00 ET, L1127-1128). The 3 recorded request strings are
  L1011 and L1131 (`write_raw` request records) — all fed by the same `ib_end_str` (L651-659):
  `end_et.astimezone(UTC).strftime("%Y%m%d-%H:%M:%S")`. Static check PASS.
- LIVE read-only fetch (verifier-run, 2026-10-08 ~11:25Z, TWS 127.0.0.1:7497 readonly clientId 9418,
  past session 2026-09-30, duration 120 S, pacing honored):
  `endDateTime sent = "20260930-14:00:00"` (UTC dash construction exactly as `ib_end_str` produces)
  → NO error 10314, 2 bars returned (starts 09:58:00 and 09:59:00 ET, closes 7762.0/7767.5,
  volumes 5013/7521), all timestamps tz-aware, NO bar ≥ 10:00 ET entered. Fetch recorded PASS;
  the throwaway script lives in `/tmp` only — worktree untouched.

### A6. Prior fail-closed laws intact — **PASS**
- Pins L108-119: calibration `17_null_calibration_raw_v2.json` = `e0dc703e2139a031…`,
  panel `04_Q1_VOL_PANEL.json` = `12dc7fbef95415…`, `lane_q1.py` = `82d1b8e6dc9dd259…`,
  expiry `es_expiry_coverage.json` = `8e2b98c59263458a…`, BLS `bls_dates.json` = `ad41d2a7670822…`;
  `verify_pins` L263-277 → `NOT_RUN_PIN_DRIFT` exit 4. T6 green (incl.
  `test_production_pins_currently_verify` — pins verified against disk during the suite run).
- Heavy-lock precheck: L310-315 requires `FREE_PROVEN` else `NOT_RUN_RESOURCE_CONFLICT` exit 2;
  run first in `run_prechecks` L795-801 for every step. T8 green.
- Duplicate refusal: `append_ledger` L357-375 → `DUPLICATE_REFUSED` exit 12; forecast_step
  pre-checks L961-965 and L1064-1069. T3 + T11 green.
- Redaction: L140 `REDACT_RE`, L172-173 `redact()`, applied to every ops-log string L196-206.
- Pacing: L136 `PACING_S = 3.0`; `time.sleep(PACING_S)` after EVERY historical request (L702).
- Byte cap: L138 `BYTE_CAP = 50_000_000`; checked L1006-1007 → `NOT_RUN_BYTE_CAP`.
- No-backfill: `check_session_window` L804-814 (`FIRST_COLLECTIBLE_SESSION = 2026-10-08` L121;
  weekend + future refusals) and L946-948 (`session_date != today_ny` → `NOT_RUN_INPUT_WINDOW_STALE`).

## B. TESTS — **PASS** (43/43, exit 0)

Verifier re-ran the full suite from the worktree:
`/Users/hoangminhlong/my-quantitative/.venv/bin/python research/control/PREP-FUTURES-Q1Q2Q3-20261007/prospective/test_q1_collector.py`
→ `Ran 43 tests in 16.696s`, `OK`, **exit code 0**. Composition: 37 prior (26 lane-G-era + 5 T10
+ 6 T11) + 6 new T12.

- **T10WindowLaw (5)**: constants `((10,0,0),(10,5,0))`/`(10,0,0)`/cutoff unchanged; window
  boundary semantics; `NOT_RUN_BAR_INCOMPLETE` before 10:00:00 ET and allowed exactly at it;
  `NOT_RUN_INPUT_WINDOW_STALE` exit 5 at the deadline; `fire_utc` = window start, DST-correct
  (2026-11-02→15:00Z EST, 2026-10-09→14:00Z EDT).
- **T11FixedForecastPath (6)**: block refusal exit 14 + proceeds once removed; 09:59:59 invocation
  refused; deadline expiry AFTER both fetches refuses at the write gate with ZERO rows (fetch
  counter == 2); NQ failure after ES fetch strands no ES row, restart completes both; duplicate
  restart idempotent (`DUPLICATE_REFUSED`, bytes unchanged); three timestamp fields on rows,
  one shared `forecast_made_at` written after all fetches, arrivals ordered ES→NQ pre-append.
- **T12SessionSkip (6)**: (a) listed 2026-10-08 → `NOT_RUN_OWNER_DECLARED_MISSED` exit 15, zero
  rows, zero fetches; (b) 2026-10-09 unaffected (full forecast, 2 fetches); (c) 8 malformed
  variants (incl. binary garbage) → `NOT_RUN_SKIP_FILE_MALFORMED` before any market access;
  (d) block-file refusal takes precedence while the block exists; (e) observe_close NOT gated —
  writes 2 lawful `NOT_RUN_NO_FORECAST_RECORDED` MISSED rows with zero fetches; (f) production
  skip manifest loads to exactly `{"2026-10-08"}`.

## C. PARITY EVIDENCE — **PASS** (`35_IBKR_DATABENTO_PARITY.md` + `.json`)

- §1 pin precedes results: md §1 "recorded verbatim BEFORE any metric computation"; §2 header
  "computed AFTER the §1 pin"; JSON `pin.recorded_before_computation: true`. PASS.
- ES bit-exact claim: §2 "median AND max rel diff = 0.0 (bit-exact after /1e9 scaling)", RV5/RV30
  0.0 all sessions; analytic bound ES max |Δŷ_full| = 0.0. PASS.
- NQ RV30 divergence: §2/JSON `median_rv30_rel = 2.099e-05 > 1e-6`, M4 fired
  (`materiality_hits: {"M4": ["NQ median_rv30_rel=2.1e-05"]}`). T2's median-convention LOW finding
  INDEPENDENTLY REPRODUCED by this verifier from `ops/parity_results_2026-10-08.json` per-session
  values (n=14: seven zeros; value-sorted index 7 = 2.098851e-05 = the doc's upper-middle
  convention; interpolated median = 1.049426e-05). **Both conventions > 1e-6 → M4 fires either
  way; verdict unchanged.** (F-3, LOW.)
- Verdict `BLOCK_PROSPECTIVE_PENDING_OWNER` present (md §3, JSON `verdict`) with owner options §3
  (1 accept-and-disclose / 2 vendor reconciliation / 3 extend evidence).
- OPTION 1 semantics verbatim: "ES — the PRIMARY series (15 §8: 'ES quyết định; NQ báo, không
  cứu') — shows BIT-EXACT feature parity … NQ is control/reporting-only; the observed NQ
  divergence (median RV30 rel 2.1e-05, worst 1.4e-02) never flipped a guard and would be disclosed
  in every prospective report" — ES primary decides, NQ control cannot rescue, divergence
  disclosed; 14-session/one-contract limit recorded (§1.2 pin + §1.6 limitations).
- Forbidden metrics: grep over md+json — `ΔR²/PnL` appear ONLY in the scope-law forbiddance
  (md L4-5) and the JSON `forbidden_and_not_computed` list (`delta_R2`,
  `rest30_target_model_evaluation`, `pnl`). Nothing computed. PASS.
- Coverage limitation recorded: 14 sessions (2026-09-11…09-30), single chain contract Z6
  (202612), months 2021-03/2024-06 NOT_RUN (IBKR error 200, expired contracts — probe evidence
  `parity_probe_2026-10-08.json`). PASS.

## D. OWNER DECISIONS vs ARTIFACTS — **PASS**

- `34_AMENDMENT_DRAFT_ISSUE_WINDOW.md` content matches what the owner approved (as attested in the
  Lead's automation dump `owner_decisions_enforced` and the dispatch packet): invocation window
  `[10:00:00,10:05:00)` America/New_York inclusive-start/exclusive-end strictly after 09:59-bar
  completion (explicit `bar_completed_at` = 10:00:00 ET); fetch `endDateTime` 10:00:00 ET
  unchanged; PIT information set "moves zero"; trial-accounting impact none (scoring condition
  unchanged, no backfill); MISSED rules unchanged (close-time `NOT_RUN_NO_FORECAST_RECORDED`
  stays lawful); observe_close unchanged; all other fail-closed laws unchanged.
- The doc still says `AMENDMENT_DRAFT_NOT_APPROVED` / `NOT IN FORCE` — correct pre-auth state;
  activation conditions listed in the required order (owner approval → verifier → Lead deletes
  the block in a dedicated commit).
- `36_OWNER_AUTH_Q1_PROSPECTIVE_LIFT.md` does NOT exist — confirmed absent in the worktree control
  dir (no `36_*` file) and repo-wide `find` (empty).
- Verbatim skip quote cross-checked: `33B_DISPATCH_LANE_K_SESSION_SKIP.md` "Không chạy bù phiên
  2026-10-08; ghi MISSED/NOT_RUN đúng luật. Phiên hợp lệ kế tiếp mới được phép tạo forecast
  prospective thật." == `SESSION_SKIP_OWNER.json.owner_instruction_quote` byte-for-byte.

## E. AUTOMATION CONFIG (Lead-dumped live state, `lead_evidence/automation_state_2026-10-08T1120Z.json`) — **PASS_WITH_FINDINGS**

Encoded and verified:
- Fire 13:30Z daily: `cronExpr "30 13 * * *"`, recurring, enabled, lifecycleStatus active,
  `nextRunAt_utc 2026-10-08T13:30:00Z`, runCount 0.
- STEP 0 block check: in `prompt_note`. STEP 0b session-skip check with 2026-10-08 listed: in
  `prompt_note`.
- PART A window `[10:00:00,10:05:00)` ET with sleep-until 10:00:30 ET and refuse ≥10:05: in
  `prompt_note`.
- PART B observe-close 16:20 ET with MISSED bookkeeping note: in `prompt_note`.
- `owner_decisions_enforced` lists all three owner decisions (amendment 34 window; parity option 1
  accept-and-disclose with "ES primary decides, NQ control cannot rescue"; 2026-10-08 MISSED,
  first real session 2026-10-09).

**GAP (F-1, MEDIUM): the three-timestamp reporting requirement is NOT encoded anywhere in the
dump** — `prompt_note` enumerates STEP 0 / STEP 0b / PART A / PART B but no requirement to report
`bar_completed_at` / `data_arrival_at` / `forecast_made_at`. Related (F-5, LOW): the dump carries
a `prompt_note` SUMMARY, not the verbatim full prompt text, so the live prompt's exact contents
rest on the Lead's attestation. Mitigation already in code: the collector itself writes all three
fields into every row and T11 asserts them, so the gate is not weakened — but the Lead should
confirm the CronUpdate prompt includes the three-timestamp reporting requirement (and dump the
full prompt text) before the next 13:30Z fire.

## F. INVARIANTS — **PASS**

- Ledger ABSENT: `prospective/ledger_q1_prospective.jsonl` does not exist; `prospective/raw/` does
  not exist; repo-wide find under the cycle dir returns no ledger file. 0 rows ever. (T9 green.)
- `COLLECTOR_BLOCKED.json` intact: on-disk sha256
  `2302f8d69d882c03975262e85b4e53a5b2c71e9045cce5392a2d9cabb27f6ed0` == `git cat-file` content
  hash at `50456e0f`; git blob `b2a96fa3e1cdebdb74b5752e053d5dbe89c9c7d1` identical at HEAD and
  `50456e0f`.
- Byte-identity to `e2e651ac`: all 66 control files shared between worktree HEAD and root-main
  `e2e651ac` are blob-identical (66/66). Specifically `26_Q1_TRIAL_LOG.json` blob `ace532dc…` and
  `27_Q1_OOS_VAL_RESULTS.json` blob `c4089d06…` identical — trial accounting untouched. (The
  inherited "26/27" phrasing from the PREP3 verifier handoff refers to this same untouched-set
  check; at T3's HEAD the measured identity is 66/66 — stricter than the claim. No file drifted.)
- `SESSION_SKIP_OWNER.json` exists (sha256
  `f8c660511faa6c2d20af3f7fda7cfd4c4c8e16c69cb06c468efc77fc9f7a3526`), schema `q1_session_skip@1`,
  `sessions` exactly `["2026-10-08"]`, verbatim owner quote present (== 33B dispatch doc).
- Heavy lock measured FREE_PROVEN at verifier start (`researchctl.py locks inspect`: no registry
  row, flock free; last history row = verifier R4 release).
- TWS ports re-measured (nc, 127.0.0.1): 7497 OPEN, 7496 closed, 4001 closed, 4002 closed.
- No push: neither lane branch exists under `refs/remotes/*` (`prep/futures-q1q2q3-prep-20261007`
  and `prep/futures-cfd-feasibility-20261008` are local-only; the only `cfd`-grep hits are
  unrelated `orca/*` remote branches). HEAD commit reachable only from the local branch ref.
- Live refusal evidence while blocked: ops_log `2026-10-08T09:16:09Z TERMINAL_FAIL_CLOSED
  NOT_RUN_BLOCKED_BY_FINDING exit 14`.

## G. POST-LIFT PROOF SPEC (for the Lead to execute after the block-removal commit)

1. **State-delta proof (collector-level):** after `COLLECTOR_BLOCKED.json` is deleted, invoke the
   collector OUTSIDE the live window (e.g. immediately, or any time not in
   `[10:00:00,10:05:00)` ET) for the current NY session with `--ledger/--state/--ops/--raw-dir`
   overrides pointed at the production paths — expected refusal is
   **`NOT_RUN_INPUT_WINDOW_STALE` (exit 5), NOT `NOT_RUN_BLOCKED_BY_FINDING` (exit 14)**. That
   status delta is the proof the new block-free state was actually read (the old code could only
   emit 14). Zero ledger rows must result.
2. **Skip-arm proof (same window):** any in-window invocation for session 2026-10-08 must refuse
   `NOT_RUN_OWNER_DECLARED_MISSED` (exit 15) — the skip gate survives the lift (already proven in
   logic by T12a/f; a live observation is optional but recommended at the 13:30Z fire).
3. **Observe-close proof (tonight ≥16:15 ET):** observe_close for 2026-10-08 must write exactly 2
   rows `record_type=session_missed`, `status=NOT_RUN_NO_FORECAST_RECORDED` (ES, NQ) and ZERO
   forecast rows — then be idempotent on repeat (`SKIPPED_SESSION_ALREADY_NOT_RUN`).
4. **Automation proof (next 13:30Z fire):** the fire must take STEP 0 (block now absent →
   proceed), STEP 0b for 2026-10-08 (owner-declared MISSED — no forecast attempted), and PART A
   for 2026-10-09 sleeping until 10:00:30 ET (= 14:00:30Z), inside `[10:00:00,10:05:00)` ET —
   the first REAL prospective forecast window. Its report must carry the three timestamps
   (bar_completed_at = 2026-10-09T14:00:00Z, data_arrival_at per symbol, forecast_made_at shared
   post-fetch) — which is exactly requirement F-1 that the automation prompt should state.
5. All post-lift proof evidence should land under the campaign's control dir; ledger rows for
   2026-10-09 must appear ONLY after the 10:00:30 ET fire, never before, never for 2026-10-08.

## FINDINGS

- **F-1 (MEDIUM)** — Automation dump does not encode the three-timestamp reporting requirement;
  `prompt_note` is a summary and the verbatim full prompt is not dumped (also F-5, LOW). Not
  gate-weakening (code + T11 enforce the fields); Lead should amend/dump before the next fire.
- **F-2 (LOW)** — `COLLECTOR_STATE.json` at HEAD carries `script_sha256 ca5d0b96…` (Lane-H-era
  collector; current Lane K collector sha256 = `3451d380da382bed0b588d736d6b58f6a155e610f7037e9
  8b9c31ddb98ab33e`, blob `d2e57c3e…`). Stale bookkeeping only; refreshed by the next
  `build_state`/`update_state_next_fire` call; the gate never reads it.
- **F-3 (LOW, inherited from T2, independently reproduced)** — NQ RV30 median convention: doc's
  2.099e-05 is the upper-middle of the 14 per-session rel diffs; the interpolated median is
  1.049e-05. Both > 1e-6 → M4 fires either way; verdict `BLOCK_PROSPECTIVE_PENDING_OWNER`
  unchanged; option-1 disclosure should quote the convention.
- **F-4 (LOW, observation)** — rehearsal at 09:41:45Z returned `REHEARSAL_TERMINAL OK exit 0`
  because TWS was up ("CONNECTED (unexpected in rehearsal)"); writes OPS+state only; ledger still
  0 rows. Expected code behavior, recorded for completeness.

## Verifier independence / boundary statement

Fresh context; verified from bytes only; nothing repaired; no real forecast attempted (the only
live IBKR touch was one read-only 120 S fetch of a PAST session per check A5); TEST untouched; no
push/merge; the only writes by this verifier are the three files under
`research/control/PREP3-CAMPAIGN-20261008/verifier/` (this report, its JSON twin, the handoff) in
a single root-main commit restricted to that pathspec.
