# VERIFY_FINALIZE — independent verifier, FINALIZE-FIX wave

- Cycle: `FUTURES-ES-PB1-V1`
- Audited worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`
  branch `prep/futures-es-reg-20261004`, HEAD **`7258f8d24b4b2d04a51ece493710570b999fcf3e`**
  (rev-parse re-measured at audit start; matches the mandated SHA exactly;
  worktree `scored_executor.py` byte-identical to the commit: sha256
  `2e3c43878b5311978d5df109588ab7791bdca17209af149223d83ffcba7696f8` both).
- ROOT `/Users/hoangminhlong/my-quantitative` `main` HEAD at audit start and
  end: `0bd1fb334710bc093836d22de506fa1387cdd2a1`, status clean (start and end).
- Audit only; zero network; no real outcome computation. All executions were
  the synthetic sandbox path; machine-wide heavy lock inspected FREE_PROVEN at
  start (`researchctl.py locks inspect`). No handoff JSON written by the
  verifier (sub-wave; per dispatch).
- Verifier side-effects outside the write boundary (test-suite reruns rewrite
  tracked test logs + write an untracked results file) were disclosed, then
  restored/removed; final tree state: worktree clean except
  `verify/finalize/**`; root clean.

## Verdict: FINALIZATION_FIX_VERIFIED

Every mandated check H1–H6 passes; one HIGH finding (GO-blocking, outside the
fix's own correctness) and one LOW finding recorded below.

---

## H1 — FAIL-before-fix + reproduction fidelity: PASS

1. **Order proven via git**: `6ae88e9c` (fix) has parent
   `c17ab2bf1ddb434c1205e12278a413f42bad6f46` (FAIL record, "NO fix in this
   commit"). FAIL record commits the bug reproductions BEFORE the fix.
2. **Pre-fix repro (verifier's own, against PRE-FIX bytes)**: extracted
   `git show c17ab2bf:…scored_executor.py` to a temp module (sha256
   `f5ad7d4816054a9c…`), ran the same boundary-fault pattern as
   `fix2/repro_finalization_bugs.py` (driver preserved at
   `evidence/verifier_repro_prefix_driver.py`; runtime module binding proven
   via `SE.__file__` + byte hash). Output verbatim:
   - BUG1 (release raises): `exit_code 0`, `terminal_state EXECUTION_COMPLETE`,
     `lock_released_status FINISHED`,
     `lock_release_error RuntimeError('INJECTED release failure')`,
     `handoff_claimed true`, `verdict_success_reported true` → **false
     success reproduced**.
   - BUG2 (handoff write raises): `exit_code 0`,
     `terminal_state EXECUTION_COMPLETE`,
     `terminal_handoff_error OSError('INJECTED handoff write failure')`,
     `handoff_path_claimed false`, `verdict_success_reported true` → **false
     success reproduced** (terminal artifact absent, success still reported).
3. **Post-fix repro (committed repro, verbatim run)**: BUG1 → `exit_code 4`,
   `FINALIZATION_FAILURE`, `UNVERIFIED_RELEASE_RAISED`, no FINISHED, no
   success; BUG2 → `exit_code 4`, `FINALIZATION_FAILURE`, no handoff-path
   claim, no success. Value-identical to the lane's committed
   `repro_after_fix_output.json`. Both outputs archived under `evidence/`.

## H2 — Fix law conformance (code-read, scored_executor.py @7258f8d2): PASS

All quotes from the committed bytes (verified byte-identical to worktree).

- **(a) ledger summary failure ⇒ failure + rows stand** — L817-825: the
  summary+file-sha step runs in its own try; on exception it records
  `ledger_summary_error` and appends
  `{"stage": "ledger_summary", …}` to `finalization_failures[]`; nothing
  rewrites the ledger. Proven behaviorally by F05/F07 (rows stand, bytes
  unchanged).
- **(b) release RAISE ⇒ no released claim; inspect PRE-restore** — L843-858:
  on release exception, `lock_release_error` recorded, canonical
  `heavy_lock.inspect()` evidence stored in
  `lock_inspect_after_release_failure`, and
  `terminal["lock_released_status"] = "UNVERIFIED_RELEASE_RAISED"`
  (L852) — a released status is only set on normal return (L842). Code order
  verified: the inspect (step b, L845-851) executes BEFORE
  `restore_runtime()` (step c, L862-869), i.e. against the same pre-restore
  runtime. No force-unlock/kill/delete anywhere: grep for
  `fcntl|flock(|unlink(|rmtree|.kill(|LOCK_UN|os.remove|shutil` over the
  executor returns zero hits; the only post-failure lock mechanism is
  `heavy_lock.inspect()` (L847).
- **(c) runtime restore own-try** — L862-869: restore wrapped in its own
  try; failure → `runtime_restore_error` + `finalization_failures[]` entry;
  cannot mask (a)/(b) or skip (d)/(e).
- **(d) handoff write failure ⇒ failure + diagnostics + NO path claim +
  fallback best-effort** — L896-930: `terminal_handoff_path` is set ONLY on
  successful `_write_atomic` (L900); `OSError` → `terminal_handoff_error`,
  `finalization_failures[]` entry, verdict fixup, fallback
  `terminal_handoff_ERROR.json` best-effort (L919-926), and if even the
  fallback fails: `terminal_handoff_recorded = "IN_MEMORY_ONLY"` (L930) —
  no artifact existence ever claimed.
- **(e) FINALIZATION_FAILURE + exit 4; computation_complete separate** —
  `EXIT_FINALIZATION = 4` (L101); fixup at L878-883 turns any otherwise-clean
  run with `finalization_failures` into `FINALIZATION_FAILURE`/exit 4; the
  handoff-write failure applies the same fixup at L907-911.
  `computation_complete` is set independently (L565, L769) and never confers
  success. Nuance (as documented in D-7(iv), consistent with the fix law):
  an already-failed run keeps its ORIGINAL terminal state/exit (3/2/75 —
  never masked, never a success) with the finalization dimension in
  `finalization_failures[]`; F06 (exit stays 3) and F08a prove this.
- **(f) cleanup order: each step own try, errors collected, original error
  never masked** — finally block L795-932 implements steps (a)–(e) each in
  its own try, appending to `finalization_failures[]` (L566 init); the
  already-failed branch (L808-811) keeps the original state. F06/F08 assert
  both errors coexist.
- **(g) ledger bytes/observed untouched by finalization** — the finalization
  block only READS (`ledger.summary()`, `sha256_file`); no append/write
  calls. F07 re-opens every ledger used by F1–F6: verify ok, observed
  correct, file sha unchanged since the run.

## H3 — Test verification (re-run by verifier): PASS

| suite | command (cwd) | verifier exit | result |
|---|---|---|---|
| finalization fix F01-F10 | `.venv/bin/python fix2/test_finalization_fix.py` | **0** | 10/10 OK (1420.6s) |
| regression T1-T10 | `.venv/bin/python test_execution_path.py` | **0** | 10/10 OK (96.2s standalone; also 0/100.5s inside F9) |
| regression refusals | `.venv/bin/python test_runner_refusals.py` | **0** | 14/14 OK (4.5s standalone; also 0/6.1s inside F9) |

- **F10 baseline correction independently verified**: AST-parse of the
  PRE-FIX bytes (`git show c17ab2bf:…`) counts exactly **3**
  `RUNTIME_DIRNAME` Attribute nodes, enclosing functions
  `[['_patch_sandbox_lock_runtime'], ['_patch_sandbox_lock_runtime'],
  ['restore','_patch_sandbox_lock_runtime']]` — all inside sandbox code.
  Current bytes: also 3, same containment. The lane's original
  `assertEqual(hits, 2)` was its own stale baseline; the corrected test
  (assert 3 + containment) is factually right, and the containment property
  itself passed in both versions.
- **F04 semantics spot-verified from artifacts** (handoff re-generated by a
  verifier F04 re-run): `runs/f4/terminal_handoff.json` shows
  `exit_code 4`, `terminal_state FINALIZATION_FAILURE`,
  `lock_released_status UNVERIFIED_RELEASE_RAISED`,
  `lock_release_error RuntimeError('INJECTED release failure (raised AFTER
  the real unlock)')`, inspect evidence `verdict FREE_PROVEN` /
  `evidence.flock_state free` — the MEASURED free state, runtime
  sandbox-confined — and `computation_complete true`. Release-raises-after-
  real-unlock still fails closed: confirmed.

## H4 — Authority/safety unchanged: PASS with 1 HIGH finding

- Production default path: no fixture references (grep `scratch/synthetic`
  in scored_executor.py + scored_runner.py: zero hits); fault injection
  non-constructible in production (L540-544 raises `AssertionError` when
  `fault and not sandbox`; F10a + T10f prove it).
- Sandbox isolation law intact: `resolve_lock_runtime(None) → None`
  (canonical runtime untouched in production); all `RUNTIME_DIRNAME`
  accesses sandbox-confined pre- and post-fix (AST, 3 nodes).
- No force-unlock/kill/delete primitives anywhere in the executor (grep
  zero hits; inspect is the only post-failure lock mechanism).
- **FINDING F1 (HIGH, GO-blocking): LAUNCH_CONTRACT_V2 executor/runner pins
  drifted, not disclosed.** The append-only `v2_1_addendum.new_pins` still
  pin `scored_executor = f5ad7d48…` and `scored_runner_v2_1 = 18258cf1…`
  (LAUNCH_CONTRACT_V2.json L315/L321; also .md L170). The wave changed both
  files: committed executor is now `2e3c4387…`, runner `87930663…` (runner
  change is docstring-only: the exit-4 line). The other three v2.1 pins
  (test_execution_path `d9d011c1…`, test_runner_refusals `3678446b…`,
  make_sandbox_fixtures `588775db…`) still match. Gate-role analysis: the
  runner's R4 pin gate re-hashes ONLY `contract["pins"]` (scored_runner.py
  L343 `for pin in contract["pins"]:`) — `new_pins` are NOT re-hashed, so
  the drift never fails closed at launch; a future GO typed against this
  contract would bind to a stale operative-execution-path pin silently.
  The `exit_codes_v2_1` string in the same addendum also predates exit 4.
  Not disclosed in FINALIZE_FIX_REPORT.md, the handoff, or either wave
  commit message. Remedy (owner/controller, not verifier): an append-only
  contract amendment (v2.2-style addendum) re-pinning executor + runner and
  recording the exit-4 code, ratified alongside D-1..D-7 before GO.

## H5 — D-7 + decision packet: PASS

- EXEC_BUILD_REPORT §7 D-7 is complete (7 numbered law points: single class
  state + per-stage `finalization_failures[]`; exit 4 distinct from 3;
  `computation_complete` separate; already-failed runs unmasked; lock
  evidence law; handoff-failure law; ledger-untouched law), minimal (names
  the authority gap honestly: the registered plan carries no executor
  terminal vocabulary; SPEC §9 `*_BLOCKED_<reason>` is the A7 layer, never
  runner-selectable), declares no frozen-law change, and is classified
  GO-blocking-owner-ratification ("*GO-blocking if ratified differently: the
  exit-code table and the FINALIZATION_FAILURE state name.*").
- Unratified sweep: the only "ratif-" hits in the wave artifacts are the
  conditional "GO-blocking if ratified differently" phrasing — no
  self-ratification language anywhere. Handoff states "D-1..D-7 UNRATIFIED";
  report states "D-1..D-7 all unratified"; the F-suite docstring states
  "D-1..D-7 remain unratified".

## H6 — Wave hygiene + registry: PASS

- Wave diff `c17ab2bf..7258f8d2`: 22 files, ALL under
  `research/control/FUTURES-ES-PB1-V1/` (grep for non-cycle paths: zero).
- Incidents disclosed: lane-inactivity timeout + controller completion
  (FINALIZE_FIX_REPORT provenance note + handoff `incidents[]` +
  `no_commit_disclosure`); first handoff write failed on a relative path,
  rewritten (handoff incident #2; follow-up commit 7258f8d2 exists).
- `handoff_FINALIZE-FIX.json`: schema field `zcode_orch_v3_handoff@1`;
  `dispatch_sha == actual_start_sha == c17ab2bf…` (equality law holds);
  `commit_sha 6ae88e9c…` exists; outputs' sha256s verified against disk
  (FINALIZE_FIX_REPORT `b33cf4a0…` ✓, executor `2e3c4387…` ✓). **FINDING F2
  (LOW): schema deviations** — `tests[]` entries carry `{command, verdict,
  result}` but omit the required `exit_code` and `log_digest`, and the
  required `recommended_next_action` field is absent; `authority_claims[]`
  is non-empty (all negative assurances — mitigating, handoff is
  controller-authored after the lane went inactive). Evidence content is
  independently confirmed by this audit's re-runs.
- Registry row (`plans/CYCLE_REGISTRY.json`): wave did not touch the
  registry at all (follows from diff confinement), so all non-head fields
  are unchanged: `go_phrase` exactly
  `GO FUTURES-ES-PB1-V1 SCORED EXECUTION`,
  `go_phrase_state REGISTERED_NOT_CONSUMED`, lifecycle `ACTIVE_LIGHT`,
  budget 0/24, s1 SEALED_UNTOUCHED. Row `head = 44269de…` vs audited
  `7258f8d2`: lag of 3 commits, ancestor relationship verified
  (`git merge-base --is-ancestor` YES; chain 44269de → c17ab2bf → 6ae88e9c
  → 7258f8d2). Controller reconciles after this audit, as mandated.
- `cycle doctor --json` (read-only), this cycle: exactly
  `HEAD_MISMATCH LOW` ("branch 7258f8d vs registry 44269de" — the expected
  lag) plus a label-only `STALE_HEARTBEAT LOW` (1d old; advisory for a
  cycle awaiting reconcile; recorded, not a defect). No other findings for
  this cycle.
- Stale-value sweep: old shas (`f5ad7d48`, `18258cf1`) appear at HEAD in 4
  files; classified: handoff_EXEC-BUILD.json + EXEC_BUILD_REPORT.md =
  historical lane records pinned to their own time (RECORD);
  verify/exec/VERIFY_EXEC.{md,json} = prior verifier records, true at their
  pinned SHA (RECORD); LAUNCH_CONTRACT_V2.json L315/L321 + .md L170 =
  **USE-AS-VALUE and STALE** (= finding F1). Code and test files contain
  zero stale-sha use-as-value.
- Safety spot checks: real `gate6/ledger/` directory ABSENT; real
  `GO_RECORDED.json` ABSENT (runner + cycle auth dirs); machine-wide heavy
  lock FREE_PROVEN; executor diff hunks confined to docstring, D-7
  constants, terminal-dict init, verdict bookkeeping, and the finally-block
  rebuild — no compute/publication/ledger-write path touched.

## Findings

- **F1 — HIGH (GO-blocking)**: LAUNCH_CONTRACT_V2 `v2_1_addendum.new_pins`
  for `scored_executor` (`f5ad7d48…`) and `scored_runner_v2_1`
  (`18258cf1…`) no longer match the operative bytes (`2e3c4387…`,
  `87930663…`); R4 does not re-hash `new_pins`, so the drift is silent at
  launch; `exit_codes_v2_1` predates exit 4; undisclosed in the wave's
  report/handoff/commit messages. Requires an owner-visible append-only
  contract amendment before GO.
- **F2 — LOW**: `handoff_FINALIZE-FIX.json` schema deviations vs
  `zcode_orch_v3_handoff@1`: `tests[]` missing `exit_code` + `log_digest`;
  missing `recommended_next_action`; non-empty `authority_claims[]`
  (negative assurances, controller-authored). Substantively confirmed by
  this audit's independent re-runs.

## Files written (this audit)

- `research/control/FUTURES-ES-PB1-V1/verify/finalize/VERIFY_FINALIZE.md` (this file)
- `research/control/FUTURES-ES-PB1-V1/verify/finalize/VERIFY_FINALIZE.json` (mirror)
- `research/control/FUTURES-ES-PB1-V1/verify/finalize/evidence/` — verifier
  run transcripts: pre-fix repro driver + output, post-fix repro output,
  F-suite stdout/stderr + results JSON, standalone T-suite and refusals
  stdout/stderr, F04 re-run transcript.

No handoff JSON written (sub-wave, per dispatch). Registry, ledgers,
contract, and all audited artifacts untouched; worktree clean except
`verify/finalize/**`; root clean.
