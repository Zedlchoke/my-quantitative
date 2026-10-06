# VERIFY_GATE6 — final fresh-context independent verifier, GATE-6 PRE-GO wave

- Cycle `FUTURES-ES-PB1-V1` · 2026-10-05 · verifier: fresh-context independent
  agent (audit only; repair nothing; zero network; synthetic/read-only inputs).
- Measured at EXACT committed SHAs (one bare `rev-parse` per repo, both MATCH;
  `git status` clean at start):
  - worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`
    (branch `prep/futures-es-reg-20261004`) HEAD
    `4c0c7504aac9c1b029e2c0adaed234c4e549fcab`
  - ROOT `/Users/hoangminhlong/my-quantitative` (main) HEAD
    `f2c59429450a14d877afc1ea25eb4c3ccf290518`
- Write boundary honored: only `research/control/FUTURES-ES-PB1-V1/verify/gate6/**`
  (this report + JSON mirror; all sandbox/scratch under `/tmp`).
- **Sub-wave: NO handoff JSON written** — this verification is a sub-wave of the
  GATE-6 PRE-GO wave; chat prose + these artifacts are the deliverable.

---

## G1 — FAIL-before-fix discipline (ledger): **PASS**

| proof | result |
|---|---|
| commit order | `2291d562c32f01d484d77947650609d8050d6ad1` (2026-10-05 13:49:15 +0700, message "…NO fix in this commit", touches ONLY `gate6/fix/FAIL_LEDGER_REPLAY.md` +29) is a proper git **ancestor** of `8c8c5020174c8a1a5dd00e5d53ba168235407ec9` (14:03:07 +0700, LEDGER-FIX) — `git merge-base --is-ancestor` rc 0 |
| fix diff | `git diff 2291d562 8c8c5020 -- gate6/trial_ledger.py` = EXACTLY one line at L125: `self._prev_sha = row.get("prev_row_sha")` → `self._prev_sha = _row_sha(row)` (hunk `@@ -122,7 +122,7 @@`) |
| fix at HEAD | `git diff 8c8c5020 4c0c7504` on the file = empty; file sha `bf89be55…` matches the contract pin |
| original bug reproduced (OLD bytes) | pre-fix module extracted via `git show 2291d562:…` into `/tmp`; two separate interpreter processes: session 1 `record_result("SYNTH-00","PASS")` + `verify()["ok"]=True`; session 2 reopen + `record_result("SYNTH-01","PASS")` → **`LedgerError: hash-chain break at line 2 (predecessor tampered or link rewritten)`**, exit 3 — byte-for-byte the FAIL_LEDGER_REPLAY.md reproduction |
| fix verified (current bytes) | same two-process scenario against HEAD bytes: reopen+append OK, `verify()["ok"]=True`, rows 2, observed 2 |

## G2 — Ledger suite re-run (independent): **PASS**

- Re-ran `gate6/fix/test_ledger_fix.py` myself (synthetic `SYNTH-*` only):
  **33 pass / 1 recorded deviation / 2 findings**, output byte-identical to the
  committed verbatim `test_ledger_fix_output.txt` (modulo scratch path).
- Category results confirmed: A 3/3 (FAIL-record repro now green); B 9/9
  (multi-session reopen ×5 sessions 8/4/4/4/4 over 24 ids incl. independent
  disk-bytes chain re-verification — fresh parse + `_row_sha`, not module
  verify); C 3/3 (session-1 bytes an EXACT PREFIX of final bytes — append-only);
  D 4/4 (non-final tamper names successor line 3; final tamper via
  `summary().file_sha256` digest change per frozen law; truncated middle line
  fail-closed); E 4/4 (torn final line FAILS CLOSED as raw `json.JSONDecodeError`,
  file never rewritten); F 8/8 (double-terminal PASS→PASS and PASS→FAIL refused;
  slot-REFUSED terminal; run-level refusal consumes no slot; observed ==
  PASS+FAIL == 3 incl. `published=False`; terminal law restored across reopen);
  G 2/3 (G1 is the BY-DESIGN recorded deviation → finding L-F2).
- Original smoke test re-run in MY OWN fresh sandbox (`/tmp`; byte-copied
  `synthetic_smoke_test.py` via `cmp`, `trial_ledger.py` symlinked to the real
  FIXED module, freeze copy at the resolved `parents[3]` depth): **28 pass /
  0 fail — ALL GREEN**. Committed `smoke/smoke_digest.json`: 28/0, observed 16,
  twin A-vs-B byte_match True, A-vs-C exactly 1 differing file.
- L-F1/L-F2 recorded, not invented: L-F1 (frozen law SILENT on torn final
  lines; actual = fail-closed JSONDecodeError, no repair) asserted by suite
  cases E1–E4; L-F2 (`verify()` on never-written path raises
  `FileNotFoundError`) additionally proven PRE-EXISTING by me: reproduces
  against the OLD bytes at 2291d562 too — orthogonal to the one-line fix.

## G3 — Runner audit: **PASS**

### (a) LAUNCH_CONTRACT_V2.json pins — re-hashed at HEAD 4c0c7504

All **19 live-file pins MATCH** (0 drift); the 20th pin is the disclosed
HISTORY record (`a7_adjudicated_freeze_bytes_HISTORY` `a992baac…` — superseded
bytes, not a live path). Key pins: operative freeze v3 `0b0d269a…` ==
`final/OPERATIVE_FREEZE_PIN.md` pin, and the pin file's text carries
`0b0d269a…`; exclude v3 `b101f5c7…`; builder v3 `5a08c9fd…` (+ generators
`b8adbd67…`/`cf0fd897…`); A7-v3 md `f8842e3d…` / digest `d42f27d9…`; SPEC
`445f7499…`; panel `7ae6de2d…`; chain `7b6179d2…`; ledger `bf89be55…`.
Runner self-hashes match RUNNER_REPORT §6 (contract md `b0cc4d76…`, json
`16e53d24…`, runner `9bb81567…`, tests `4c5c8951…`, manifests `2e601747…`).

Superseded-authority grep (freeze v2 `cf150e24` / builder v2.1 `00141bf0` /
`DONOR_LAW_CARRYOVER` / a7 v1-v2) over the OPERATIVE runner artifacts: every
occurrence is verified-withdrawn HISTORY framing — the v1 spec is declared
superseded (file untouched); the runner's ONLY `DONOR_LAW_CARRYOVER` use is
R4's check that the operative freeze DECLARES it withdrawn
(`freeze.donor_law.supersedes.path/.sha256` == the HISTORY pin, plus the
`A7-SPEC-M5` marker). `OPERATIVE_FREEZE_PIN.md` records `a992baac…` only as
superseded; freeze v3 records `cf150e24…` only inside its append-only
supersession lineage block.

### (b) scored_runner.py code review

- **Reads the registry ITSELF**: `check_registry()` loads the ROOT
  `plans/CYCLE_REGISTRY.json`, selects the cycle row, and verifies branch ==
  `git rev-parse --abbrev-ref HEAD`, `go_phrase` byte-exact canonical, and head
  policy MATCH / LAG_ANCESTOR (`merge-base --is-ancestor` rc 0 → must-reconcile,
  fails execution gate) / DIVERGED (→ `REFUSED_CONTROL_STATE_DRIFT`). No
  caller-supplied booleans anywhere: CLI overrides are PATH-level only, and
  every decision re-derives from contract-pinned shas + the registry + files.
- **GO law**: `check_go()` — artifact presence; `cycle_id`; `key_2_owner_go.
  verbatim` BYTE-equality with `GO FUTURES-ES-PB1-V1 SCORED EXECUTION` (no
  trim/case-fold); `typed_by_owner is True`; `typed_by == "OWNER"`;
  delegation-marker scan (`delegat*`, "on behalf of", "thay mặt", "proxy")
  over EVERY string in the artifact via `walk_strings`; `key_1_a7_prelaunch.
  sha256` must equal the operative A7-v3 digest pin (early/superseded GO dies);
  registry `go_phrase` consistency. Paraphrase/delegation/early →
  `REFUSED_NO_GO`.
- **Pin re-hash**: `check_drift()` re-hashes all 19 live pins + 8 freeze
  round-trips (identity ids byte-exact vs contract, exclude-sha round-trip,
  donor-law withdraw declaration, Variant-A cost table, forbidden-value ban,
  eval 2,921 + F1–F4, operative pin carries operative sha, fixed ledger sha).
- **Canonical lock check**: `lock_inspect()` reimplements
  `governance.heavy_lock.inspect()` with an injectable runtime dir; compared
  line-by-line against `research/governance/heavy_lock.py::inspect()` — SAME
  decision inputs and SAME verdict tree (malformed registry → DRIFT; no row +
  free flock → FREE_PROVEN; flocked-no-row → DRIFT; non-RUNNING row → DRIFT;
  non-int pid → DRIFT; HELD_PROVEN = alive + process-start-token match + flock
  held; dead pid / missing token / token mismatch / alive-token-match-but-free-
  flock → DRIFT), DELEGATED to the governance module's own primitives
  (`_load_registry`, `flock_state`, `_pid_alive`, `process_start_token`) —
  never a weaker check.
- **Execution stub**: all-gates-pass path logs "WOULD EXECUTE" + the planned
  invocation sketch and computes NOTHING; real scored wiring is the post-GO
  lane's job per contract §4. Exit codes 0/2/3/75 as documented; ledger
  failures are TECHNICAL (exit 3), never silently skipped.

## G4 — Refusal re-verification (tests re-run by verifier): **PASS** (1 finding)

- `test_runner_refusals.py` re-run at the audited SHAs: **13/14** — the single
  failure is `test_09_real_state_refuses_in_execution_mode`, whose EXPECTED
  REASON is stale post-reconcile (see FINDING V-1): it hardcodes the
  pre-reconcile real state (head lag `71326c8c` → `REFUSED_CONTROL_STATE_DRIFT`
  / LAG_ANCESTOR). Post-reconcile the real row head == actual HEAD → R0 MATCH,
  so the first failing gate is R1 (GO absent) → `REFUSED_NO_GO`. The refusal
  itself fires identically (rc 2 + REFUSED row + `counts_observed=false`);
  the RUNNER is correct, the committed test EXPECTATION is stale. The lane's
  committed "14/14" claim was true at ITS head against the then-registry.
- Three manual injections (verifier's own harness, sandbox registry with MATCH
  head, sandbox ledgers):
  1. tampered freeze copy (1-byte field rename) → **rc 2 `REFUSED_DRIFT`**,
     REFUSED row written (`counts_observed=false`, `identity_id=null`);
  2. paraphrased GO artifact → **rc 2 `REFUSED_NO_GO`**, REFUSED row written;
  3. REAL `flock(LOCK_EX)` held on a temp runtime + RUNNING holder row →
     **rc 75 `NOT_RUN_RESOURCE_CONFLICT`**, REFUSED row written.
- Real preflight (`--preflight-only`, real registry + real paths) run TWICE:
  exit 0 both, `wiring_failures: []`, all 19 pins match, 8/8 round-trips TRUE,
  lock FREE_PROVEN, A7-v3 AUTHORIZED_WITH_FINDINGS C/H/M=0, D-A4/D-A5
  ADJUDICATED_AUTHORITY_EXISTS, gate verdict `REFUSED_NO_GO` (expected pre-GO).
- Real-state execution mode (GO absent): **exit 2, `REFUSED_NO_GO`, REFUSED
  ledger row seq 1 `counts_observed=false` — the runner refuses TODAY.**

## G5 — Twin + wiring: **PASS**

- My own two preflight runs: `manifest_run1.json` and `manifest_run2.json`
  **BYTE-IDENTICAL** (`cmp`) — deterministic, no wall-clock fields.
- Committed lane twins also byte-identical (sha `2e601747…` == RUNNER_REPORT
  claim). Delta committed-vs-verifier-rerun is EXCLUSIVELY the registry-state
  fields changed by reconcile `f2c59429` (row head `71326c8c`→`4c0c7504`,
  LAG_ANCESTOR→MATCH, R0 reason→R1 reason); every pin hash identical across
  the two generations of manifests.
- Preflight 19/19 live-pin matches re-proven independently (all 19 re-hashed by
  verifier; named spot-check subset: freeze v3 `0b0d269a`, builder v3
  `5a08c9fd`, A7-v3 digest `d42f27d9`, SPEC `445f7499`, ledger `bf89be55`,
  exclude v3 `b101f5c7`).

## G6 — Registry / doctor / hygiene: **PASS**

- Registry row (ROOT): `head 4c0c7504…` (== actual worktree HEAD; runner R0
  MATCH), `go_phrase` byte-exact canonical, `go_phrase_state
  REGISTERED_NOT_CONSUMED`, `lifecycle ACTIVE_LIGHT`, `budget {used:0, max:24}`.
- Reconcile `f2c59429` surgical: EXACTLY 3 control-plane files
  (`plans/ACTIVE_CYCLES.json`, `plans/CYCLE_REGISTRY.json`,
  `plans/CYCLE_REGISTRY.events.jsonl`); only header timestamps/write_token +
  THIS cycle's row (head, updated_at) changed; foreign rows byte-identical;
  events = REGISTRY_SAVED + CYCLE_UPDATED (this cycle).
- `cycle doctor --json` (read-only): 71 findings registry-wide, **0 for
  FUTURES-ES-PB1-V1**.
- Wave diff `71326c8c..4c0c7504`: 100 files, **0 outside
  `research/control/FUTURES-ES-PB1-V1/`**; 3 commits (2291d562 FAIL →
  8c8c5020 LEDGER-FIX → 4c0c7504 RUNNER).
- Stale-value sweep: **0 use-as-value**. ROOT control-plane files contain no
  stale head (`71326c8c`/`456dac6b` absent). Cycle-dir occurrences of stale
  SHAs are confined to dated lane records / historical reports / lineage
  supersession blocks / the LAG_ANCESTOR test fixture.
- GO string sweep: `GO FUTURES-ES-PB1-V1 SCORED EXECUTION` appears ONLY in law
  contexts (registry field, contract, runner constant, synthetic test fixtures,
  audits/reports quoting the law). NO `GO_RECORDED.json` for this cycle exists
  anywhere (`auth/` holds only `PREGO_REPAIR_RECORDED.json`; root cycle dir has
  none). Registry state REGISTERED_NOT_CONSUMED — nothing consumed.
- Both trees clean at end except verifier outputs (see end status below).

## G7 — Pre-GO verdict

| # | gate item | state |
|---|---|---|
| 1 | Trial ledger | FIXED + PROVEN (FAIL-before-fix discipline held; 33+2×28 synthetic green; L-F1/L-F2 recorded) |
| 2 | Scored runner | BUILT, refuses-without-GO (verified today, rc 2 + row), contract v2 current (19/19 pins green at HEAD) |
| 3 | Gates 1–4 | v3 state (freeze v3 == OPERATIVE_FREEZE_PIN `0b0d269a…`; A7-v3 AUTHORIZED_WITH_FINDINGS 0C/0H/0M; dryrun-v3 lineage green) |
| 4 | D-A4/D-A5 | AUTHORITY_EXISTS both (SPEC-dispositive); owner acknowledgment = formality riding GO |
| 5 | Registry | synced to `4c0c7504…` (reconcile f2c59429 surgical); doctor 0 findings for this cycle |
| 6 | Denominator law | implemented + verified (REFUSED/NOT_RUN never count; 0/24 used) |

## VERDICT: **GO_READY**

Nothing remains on the machine/control plane except the two owner-side
formalities that by definition ride the GO itself:
1. The typed OWNER GO — key 2 of 2, byte-exact
   `GO FUTURES-ES-PB1-V1 SCORED EXECUTION`, never delegated, consumed at this
   cycle's own gate (absent today — verified).
2. Owner acknowledgment of the D-A4/D-A5 adjudication one-liners
   (`pins2/DA45_DECISION_PACKET.md` §2.5/§3.3) — formal only; both pins already
   AUTHORITY_EXISTS.

### Findings (none blocking)

- **V-1 [LOW — test staleness, not a runner defect]**: `gate6/runner/
  test_runner_refusals.py::test_09` asserts the PRE-reconcile real-state
  refusal reason (`REFUSED_CONTROL_STATE_DRIFT`/LAG_ANCESTOR). Post-reconcile
  (row head == HEAD) the real state refuses `REFUSED_NO_GO`, so the committed
  suite is 13/14 at the audited SHAs. The refusal itself fires identically
  (rc 2 + REFUSED row, denominator untouched) — verified directly by the
  verifier. Remedy: one-line test-expectation update by the controller/post-GO
  lane; no GO decision depends on it.
- **V-2 [INFO — carried L-F1/L-F2]**: ledger law is SILENT on torn final lines
  (actual behavior fail-closed raw `JSONDecodeError`, file never rewritten);
  `verify()` on a never-written path raises `FileNotFoundError` (proven
  pre-existing at the FAIL-record HEAD too). Both recorded, unfixed by design
  (outside the one-line mandate).
- **V-3 [INFO]**: committed preflight manifests (`2e601747…`) record the
  pre-reconcile registry (LAG_ANCESTOR + `must_reconcile_before_go=true`);
  verifier's post-reconcile twins are internally byte-identical with the delta
  confined to registry fields. Historical evidence, correctly superseded.
- **V-4 [INFO]**: `GATE6_READINESS.md` and `scored_runner_spec.md` (v1) are
  dated pre-v3 lane artifacts referencing freeze v2 / a7-v2 as their
  then-operative authority; both superseded by `LAUNCH_CONTRACT_V2` as the
  sole operative launch contract (declared in the contract; v1 file untouched
  by law). Their stale references are history, never consumed by the runner.
- **V-5 [INFO — carried obligations]**: `VERIFIED_VS_ACCOUNT` remains NOT_RUN
  (cost model stays MODELED COST); real scored execution, real G8 twin, and
  terminal A7 are the post-GO lane's work.

— End VERIFY_GATE6 (sub-wave: no handoff JSON written; this report + .json
mirror are the artifacts).
