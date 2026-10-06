# VERIFY_EXEC — EXEC-BUILD wave, FUTURES-ES-PB1-V1 (fresh-context, 2026-10-05)

Final independent pre-GO verification of the completed execution runner.
Audit only; nothing repaired; zero network; no real outcome computation
(SANDBOX synthetic suites re-run as required — synthetic fixtures only).

## Pins (permitted git: 1 rev-parse each + status start/end)

- Worktree `…/.worktrees/futures-es-reg/prep` (prep/futures-es-reg-20261004)
  HEAD = `d0657cb811f2b07d0efb5cd395208262cda84cb9` — MATCH.
- ROOT `/Users/hoangminhlong/my-quantitative` (main) HEAD =
  `0d1fe426da9bec718105192e3e663cd1c65c120e` — MATCH.
- Status at start: both clean. Status at end: both clean, HEADs unchanged
  (see "hygiene" below for the test_logs restore).

## E1 — Stub eradication: PASS

- `grep "WOULD EXECUTE|execution_stub|pre_go_stub"` over
  `gate6/runner/scored_runner.py` + `scored_executor.py` + both test files
  at this SHA: only (a) removal-record docstrings (runner L18–19, executor
  L4) and (b) a NEGATIVE assertion (`test_execution_path.py:218` asserts
  "WOULD EXECUTE" NOT in stderr). Zero code occurrences.
- Execution branch (`scored_runner.py` L956–1038): after R0–R5 +
  RefusalGate all pass, imports `scored_executor` and delegates to
  `run_scored_execution(cfg)` (L1032) — the real path.
- Fail-closed code-read: exit 0 is returned ONLY from the runner's executor
  completion (`rc` from `run_scored_execution`); the executor returns 0
  ONLY when `failure_reasons` is empty AND `observed_denominator == 24`
  (executor L719–743); every exception path terminates with
  COMPUTE/ABORTED state + exit 3; `exit_code=None` in `finally` is forced
  to EXIT_FAILURE (L763–766); refusal recording failure upgrades to
  EXIT_TECHNICAL, never silent pass (runner `_refuse`, executor `_refuse`).
  Withdrawal record `GO_READY_WITHDRAWAL.md` present at runner dir.
- v2.1 contract addendum `new_pins` all match disk sha256:
  scored_executor `f5ad7d48…`, scored_runner `18258cf1…`,
  test_execution_path `d9d011c1…`, test_runner_refusals `3678446b…`,
  make_sandbox_fixtures `588775db…`, plus `trial_ledger_fixed`
  `bf89be55…` (contract pin == disk).

## E2 — Tests drive the PRODUCTION path: PASS

- `test_execution_path.py` happy path (T1) launches the REAL
  `scored_runner.py` CLI as a subprocess with sandbox fixtures
  (`sandbox_argv`); no executor mock anywhere; the runner delegates to the
  real `scored_executor.run_scored_execution`. Machinery of record
  `final/dryrun_builder_v3.py` is imported verbatim (executor
  `load_builder_module`); sandbox only overrides location constants.
- Fault injections are sandbox-only, guarded at BOTH layers:
  runner L975–979 (`--sandbox-fault` without `--sandbox-root` → exit 3)
  and executor L517–521 (`fault and not sandbox` → AssertionError;
  T10(f) asserts it).
- RE-RUN (this audit, ROOT .venv, at the pinned SHA):
  `test_runner_refusals.py` → exit 0, "Ran 14 tests … OK" (14/14).
  `test_execution_path.py` → exit 0, "Ran 10 tests … OK" (T1–T10, 144 s).
  T6 internally re-ran the refusal suite (OK).

## E3 — Ledger/trial accounting, lock lifecycle, failure handling: PASS
(verified from the re-run artifacts, not only test assertions)

- T1: `sandbox/ledger/t1.jsonl` = 24 identity rows, all PASS, all
  `counts_observed=true`, all published, all SYNTHETIC-SANDBOX-stamped;
  `observed_denominator=24` exact; handoff EXECUTION_COMPLETE / exit 0 /
  lock FINISHED / twin byte_match true / reconciliation pass.
- T5: fault run ABORTED_SANDBOX_FAULT after 5 terminals
  (observed=5); retry handoff `pass_a.skipped_terminal` == the 5 frozen
  first identities, `computed` = 19, zero overlap; ledger replay
  `observed_before_run=5` with prior_terminal list; final ledger 24
  identity rows / 24 observed; the 5 prior output files byte-identical
  between t5-fault and t5-retry (`cmp` per file). No recompute, no
  double-count.
- T4: ledger 24 identity rows, ALL `counts_observed=true`, exactly 4
  `published=false` (from the injected read-only dir at
  FBES1-PLA-D0-S2); terminal PUBLICATION_FAILURE, exit 3.
- T7: after the injected mid-compute exception — live
  `heavy_lock.flock_state(sandbox/heavy_runtime)` = `free`; registry row
  file ABSENT; ledger chain `verify()` ok with observed=7; handoff
  COMPUTE_FAILURE / lock_released_status FAILED / exit 3.
- T3: terminal TWIN_MISMATCH, verdict EXECUTION_FAILED, exit 3,
  `twin_compare.byte_match=false`, 24 rows still observed — never success.
- T9: fresh reopen of t1.jsonl — verify ok, observed 24, complete, file
  bytes unchanged (byte-compare before/after reopen).

## E4 — Authority/pin bindings: PASS

- Contract `LAUNCH_CONTRACT_V2.json` schema `launch_contract@2`,
  canonical GO phrase exact; v2.1 addendum append-only (stub-removal
  record + new pins, all sha-verified against disk above).
- Runner order enforced by code-read: R0 registry → R2 auth → R3 lock →
  R4 drift (re-hash every pin + freeze round-trips) → R5 adjudication →
  R1 GO (byte-exact verbatim, OWNER-typed, delegation-marker scan,
  A7-v3-digest binding) → RefusalGate → only then `import
  scored_executor`; executor re-verifies GO/registry-head/pins AFTER
  heavy-lock acquire (TOCTOU closure, runner L996–1012).
- Production default path: my own grep — "scratch"/"synthetic" appear in
  runner/executor ONLY in docstrings; no fixture path literal in code;
  T8(b) AST check (re-ran PASS) confines `RUNTIME_DIRNAME` writes to
  sandbox-named functions; `resolve_lock_runtime(None)` returns None.
  Production-mode override guard (`production_authority_violations`)
  refuses any authority-path override reaching the execution branch
  (T8a + refusals test_08 re-ran PASS). Sandbox mix-refusal re-proven
  (T8c: `--sandbox-root` + real freeze → SANDBOX-ISOLATION, exit 2).
- Fake GO exists at EXACTLY ONE path in both trees:
  `gate6/runner/scratch/synthetic/sandbox/research/control/
  FUTURES-ES-PB1-V1/authority/GO_RECORDED.json` (fixture, stamped).
  Real gate `auth/GO_RECORDED.json` ABSENT in worktree AND root.

## E5 — No real outcomes: PASS

- Production ledger dir `gate6/ledger/` does NOT exist in worktree or
  root — never written.
- Full ledger inventory in the cycle tree: `gate6/smoke/*_synthetic.jsonl`
  (prior-wave synthetic smoke fixtures, note="synthetic"),
  `gate6/fix/smoke_regress/**` copies (same), `gate6/runner/sandbox/
  trial_ledger.jsonl` (1 REFUSED), and 11 sandbox ledgers under
  `scratch/synthetic/sandbox/` — every identity row carries the
  SYNTHETIC-SANDBOX stamp in its note (t1/t2a/t2b/t3/t4/t5: 24/24 each;
  t7: 7/7; t10a/b/c + trial_ledger: REFUSED-only, observed=0).
- Zero references to the real panel/chain parquet paths in either test
  file; the synthetic panels are generated by the committed generator
  (fabricated sha256-seeded walk; PROVENANCE banner).

## E6 — Registry + incident + doctor + wave diff: FAIL (one sub-check)

- Registry row (ROOT `plans/CYCLE_REGISTRY.json`): head =
  `999ece6024ba739ed9a4046dcbcbb382f4d6650c` (EXEC_SHA) ✓;
  go_phrase byte-exact `GO FUTURES-ES-PB1-V1 SCORED EXECUTION` ✓;
  go_phrase_state `REGISTERED_NOT_CONSUMED` ✓; lifecycle `ACTIVE_LIGHT` ✓;
  budget 0/24 ✓; s0 OPEN / s1 SEALED_UNTOUCHED ✓.
- Lag character: `999ece60` IS a proper git ancestor of worktree HEAD
  `d0657cb…` (merge-base verified); exactly ONE commit between them —
  the append-only INCIDENT record (adds only
  `INCIDENT_registry_bundle_0d1fe426.md`, 29 lines).
- `cycle doctor --json` (read-only): 70 machine-wide findings; exactly 1
  for this cycle — HEAD_MISMATCH LOW (branch d0657cb vs registry
  999ece6), i.e. the disclosed verified-ancestor lag whose clearance is
  the E8 "registry-head sync of the final SHA" blocker. No other
  findings for this cycle.
- Wave diff `8bb9d4a8..d0657cb8`: 41 files, ALL under
  `research/control/FUTURES-ES-PB1-V1/` (grep for non-cycle paths: none).
- **INCIDENT sub-check FAIL (F-1, MEDIUM):** the record states the bundle
  = ES head update + "NFL-WINPROB-NG-SCORED-V1" registration as the only
  foreign addition. Measured diff of ROOT commit `0d1fe426` actually adds
  TWO foreign registrations (0 occurrences of either in the parent
  registry): `NFL-WINPROB-NG-SCORED-V1` (carries a registered
  REGISTERED_NOT_CONSUMED GO phrase) AND `WINPROB-PLAYERFEAT-PREP-V1`
  (no GO phrase, NOT_REGISTERED), each with 3 events + ACTIVE_CYCLES
  projection entries. The incident record exists, is append-only, its
  process fix stands, and the ES row content is exactly as intended —
  but its content audit materially under-reports the bundled foreign
  content. Remediation: append-only correction line to the incident
  record (controller); no machinery impact.

## E7 — Decision packet §7 D-1..D-6: PASS

Each is a genuine SPEC/plan gap with a minimal deterministic default, and
none silently changes a frozen law:
- D-1 ledger PASS/FAIL semantics for the FIRST computation (no scientific
  threshold exists) — costs/warmup stay run-level reconciliation,
  fail-closed; GO-blocking if ratified differently (status distribution of
  the 24 terminal rows).
- D-2 run-level files under publication failure — recorded, pass
  completes, run ends non-zero; no partial success.
- D-3 retry with missing/unverifiable prior output — budget law wins
  (never recompute; PRIOR_TERMINAL_OUTPUT_MISSING fail-closed); explicit
  owner-amendment path if recompute preferred.
- D-4 sandbox R0 keeps the REAL worktree for git identity — stricter,
  simpler reading; sandbox refuses on real-checkout divergence.
- D-5 production artifact home `<gate6/ledger>/runs/<label>` — recorded
  in the contract addendum; change needs amendment.
- D-6 exit 3 covers all terminal execution failure states, distinguished
  by terminal_state in manifest/handoff.
All six are classified IMPLEMENTED-DEFAULT-PENDING-RATIFICATION = GO-
blocking-owner-ratification. No identity/cost/fold/donor/budget law is
touched.

## E8 — Verdict

**FAIL + items** (single item; execution path itself fully verified):

- **F-1 (MEDIUM, GO-adjacent doc accuracy, not a machinery defect):**
  `INCIDENT_registry_bundle_0d1fe426.md` under-reports what ROOT commit
  `0d1fe426` bundled — two foreign registrations (NFL-WINPROB-NG-SCORED-V1
  AND WINPROB-PLAYERFEAT-PREP-V1), not one. E6's "NFL row is the only
  foreign addition" cannot be confirmed. Clear via an append-only
  incident-record correction before GO.

Everything else: E1, E2, E3, E4, E5, E7 PASS.

**Pre-GO readiness statement:** the scored-execution machinery is
COMPLETE and TESTED — real runner+executor (stub eradicated, sha-pinned),
T1–T10 10/10 + refusal suite 14/14 re-run green at this SHA through the
production path on synthetic-only fixtures; ledger/trial accounting, lock
lifecycle and fail-closed behavior verified from artifacts; no real
outcome computed and the production ledger was never written. Remaining
pre-GO blockers: (1) owner ratification of D-1..D-6; (2) registry-head
sync of the final SHA (currently verified-ancestor lag at `999ece60`,
doctor LOW HEAD_MISMATCH); (3) minor: append-only correction to the
incident record covering the second bundled registration (F-1). The GO
itself remains owner-only; `auth/GO_RECORDED.json` stays ABSENT.

## Hygiene (this audit's own writes)

- Wrote ONLY `research/control/FUTURES-ES-PB1-V1/verify/exec/**`
  (this file + .json mirror). No handoff JSON: sub-wave verifier.
- Re-running the required suites rewrote 10 tracked files under
  `gate6/runner/scratch/synthetic/test_logs/` (wall-clock fields in run
  manifests); all were restored to the committed pinned bytes
  (`git checkout --` of that dir); end status clean, both HEADs unchanged.
- Sandbox artifacts created by the re-runs live under the gitignored
  `scratch/synthetic/sandbox/` (SYNTHETIC-SANDBOX only).
