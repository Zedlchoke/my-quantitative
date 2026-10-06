# EXEC_BUILD_REPORT — lane EXEC-BUILD, cycle FUTURES-ES-PB1-V1 (2026-10-05)

Pre-GO implementation lane: the scored-execution STUB of
`gate6/runner/scored_runner.py` (withdrawal record
`GO_READY_WITHDRAWAL.md`) is REPLACED by the real execution path
`gate6/runner/scored_executor.py`, and the whole path is proven
END-TO-END THROUGH THE PRODUCTION RUNNER with SYNTHETIC fixtures inside an
isolated `--sandbox-root`. This is PRE-GO work: the runner still REFUSES
scored execution on real inputs today (no GO exists — verified below); no
real outcome was computed; no S1; frozen laws unchanged.

Dispatch HEAD: `8bb9d4a8ee55a99bac769e3ccff81f65d53430c8`
(branch `prep/futures-es-reg-20261004`; one `rev-parse` at lane start;
no other git mutations; no commit — `commit_sha` null).

## 1. What was wired

1. **`gate6/runner/scored_executor.py` (NEW, sha `f5ad7d48…`)** — the
   executor:
   - **Lock lifecycle**: acquire via the CANONICAL
     `governance.heavy_lock.acquire` (imported; never reimplemented). In
     sandbox mode the canonical runtime is redirected under the sandbox
     (`_patch_sandbox_lock_runtime`, restore in `finally`; production mode
     never patches — AST-proven, see T8b). Lock held at acquire ⇒ ledger
     REFUSED row `NOT_RUN_RESOURCE_CONFLICT`, exit 75. AFTER acquire the
     runner's `reverify_authority` closure re-checks the GO artifact, the
     registry head (MATCH required) and the input pins
     (freeze/exclude/panel/chain/identity table/builder/trial-ledger) — the
     TOCTOU guard; any drift ⇒ `REFUSED_CONTROL_STATE_DRIFT`, exit 2.
     Release in `finally` ALWAYS — `FINISHED` on success, `FAILED` on
     failures, `TECHABORT` on the injected abort (T7 proves the flock is
     free and the registry row cleared after an exception).
   - **Computation**: the machinery of record
     `final/dryrun_builder_v3.py` is IMPORTED, never forked:
     `load_inputs / build_sessions / derive_state / parse_identity /
     simulate / c1_sign / check_cost_sample / check_warmup_regression` run
     from the pinned module (production = the pinned file verbatim; sandbox
     = the SAME source executed into a module namespace whose location
     constants `WT/ES_CACHE/PIN_SPEC/PIN_PANEL/PIN_CHAIN` point at the
     sandbox fixtures — the simulation logic is byte-identical). The
     executor also re-hashes the builder file against the contract pin
     before load.
   - **Ledger**: the FIXED `gate6/trial_ledger.py` (sha-pinned
     `bf89be55…`) opens the 24-slot ledger. Every scientifically computed
     result is recorded to the observed denominator — PASS, or FAIL when
     the identity's computation raised — with `published=false` when
     publication failed (still counts observed, per plan §6). Per-identity
     terminal rows exactly once. Interrupted-run law: the retry replays the
     ledger, SKIPS already-terminal slots (never recomputes, never
     double-counts, never mints identities) and copies the prior run's
     published bytes after verifying the recorded `result_sha`.
   - **Publication + reconciliation**: per-identity outputs + trades index
     + summary under a run dir; `reconciliation.json` checks the output
     file set against the frozen identity table (order+set), terminal-slot
     exactness, prior-output availability, and the machinery's own
     integrity checks (cost recomputation sample + warmup regression —
     both PASS on the synthetic surface); any mismatch ⇒ fail-closed.
   - **Reproduction twin**: a second independent pass (fresh machinery
     module instance, fresh input load from disk, separate output dir)
     must be byte-identical (`trial_ledger.twin_manifest` /
     `twin_compare`); mismatch ⇒ terminal `TWIN_MISMATCH`, NEVER success.
   - **Terminal handoff**: `runs/<label>/terminal_handoff.json` — paths +
     shas of outputs, twin manifests, ledger summary + file sha, lock
     record (acquired/runtime/released-status), verdict — for the post-GO
     terminal A7.
   - **Fail-closed**: any failure ⇒ non-zero exit + terminal state
     recorded; exit 0 ONLY for `EXECUTION_COMPLETE` (24 observed rows, all
     published, twin byte-match, reconciliation pass).

2. **`gate6/runner/scored_runner.py` (updated, sha `18258cf1…`)** —
   ALL existing authority gates (R0 registry self-read, R1 GO verbatim,
   R2 A7-v3 auth, R3 lock inspect, R4 drift, R5 adjudication) are
   UNCHANGED; the stub branch (formerly ~L749) is replaced by: the
   production-default authority guard, then the executor invocation with
   the TOCTOU closure. New: `--sandbox-root`, `--run-label`,
   `--sandbox-fault` (sandbox-only, suppressed help) and the sandbox
   isolation machinery (`sandbox_setup`, `sandbox_isolation_violations`,
   `_refuse_sandbox_isolation`, `production_authority_violations`,
   `resolve_sandbox_paths`, `apply_path_overrides`).

3. **Stub removal (grep-able)**: `WOULD EXECUTE` / `execution_stub` /
   `pre_go_stub` appear in scored_runner.py ONLY in the docstring's removal
   record (line 18). Zero code occurrences (verified by grep during the
   lane and asserted by the suite).

4. **LAUNCH_CONTRACT_V2** gains the append-only `v2_1_addendum` (JSON) and
   §v2.1 (md): executor sha + stub-removal note + new pins + exit-code
   semantics. History not rewritten; schema still `launch_contract@2`.

## 2. Sandbox isolation law (statement)

`--sandbox-root <dir>` is the ONLY way to drive synthetic execution:
(a) authority inputs (contract, registry row COPY, GO artifact, freeze/
panel paths via the sandbox contract pins, ledger, lock runtime) resolve
under the sandbox; (b) every output carries the `SYNTHETIC-SANDBOX` stamp
(identity records, index, summary, manifests, handoff, refusal notes);
(c) `--sandbox-root` combined with any real-root authority path REFUSES
(`SANDBOX-ISOLATION`, REFUSED row + refusal_record written ONLY under the
sandbox — the violated path is never written); (d) the production default
(no flag) uses ONLY the real paths + real authority — any authority-path
override reaching the execution branch refuses
(`PRODUCTION-DEFAULT-AUTHORITY` guard) so the refusal tests' path overrides
remain usable while the production execution path is un-spoofable;
(e) a sandbox run cannot write the real ledger, the real registry, or the
machine-wide lock (verified: real `gate6/ledger/` directory does NOT exist
after the whole suite; the real GO artifact is absent; heavy-lock writes
went to `<sandbox>/heavy_runtime` only). Registry R0 in sandbox mode keeps
the REAL worktree for read-only branch/HEAD git identity — the row is a
sandbox COPY of the real registry values (see Decision D-4).

## 3. Synthetic fixtures

`scratch/synthetic/make_sandbox_fixtures.py` (committed, sha `588775db…`)
fabricates `<scratch/synthetic/sandbox>/` (gitignored output, PROVENANCE.md
banner, seed
`FUTURES-ES-PB1-V1/EXEC-BUILD/synthetic-sandbox-v1/2026-10-05`):

- **Surface**: 4,241 business days from 2016-01-04; 91 one-minute bars per
  session (08:30–10:00 CT, UTC ns `ts_event`, fixed-point 1e-9); 50 dash
  strays exercising the E5 dash filter. Fold windows carry the FROZEN
  counts: warmup 252/fold head + eval 375/948/708/890 = **2,921** exactly.
  sha256-based deterministic prices (overnight gaps ±10 pts ⇒ ~20% q80-tail
  sessions on both tails).
- **Donor law exercised**: 139-session v1-label carryover set +
  6 v3-only-flagged gap sessions (flag-based SPEC §4 [ERRATUM A7-SPEC-M5]);
  28 FOMC days inside eval regions feed the FOMCIN identities.
- **Frozen laws kept**: 24 identity ids byte-exact; Variant-A cost table
  verbatim (T1 sample trade RT cost = 67.0 USD S2); folds F1–F4; warmup
  positional law; donor supersedes record pointing at the real
  DONOR_LAW_CARRYOVER sha `314ae947…`.
- **Real authority copied byte-identical (read-only)**: SPEC, builder v3 +
  lineage, A7-v3 md/digest, identity table, PREGO/DA45/FAIL_DONOR/
  DONOR_LAW_CARRYOVER records, trial_ledger.py.
- **Sandbox-only fixtures**: fake typed-owner GO artifact (exists ONLY in
  the sandbox), registry row copy, sandbox launch contract
  (embedded_laws byte-identical to the operative contract; pins → sandbox).
  **NO real-cycle GO_RECORDED.json exists anywhere** (verified:
  `auth/GO_RECORDED.json` absent).

## 4. Test matrix (all through the production path)

Suite: `gate6/runner/test_execution_path.py` — **10/10 PASS, exit 0**
(full transcript: `scratch/synthetic/test_logs/T1-T10_full_run.txt`;
per-test transcripts `test_logs/T*.stdout.txt` / `T*.stderr.txt`).

| test | proves | exit | key evidence |
|---|---|---|---|
| T1 | happy path (sandbox, synthetic) | **0** | 24 ledger identity rows all PASS, observed=24 exactly, complete=true; outputs 24+index+summary in BOTH pass dirs; twin byte_match 26/26, no diffs; `terminal_handoff.json` verdict EXECUTION_COMPLETE, lock released FINISHED; stamps SYNTHETIC-SANDBOX; machinery integrity cost-sample PASS + warmup PASS; era validation 4241/4241 |
| T2 | reproduction | **0** | two independent sandbox runs (t2a/t2b): cross-run pass_a manifests byte-match via `trial_ledger.twin_compare`; each run's internal twin also matched |
| T3 | twin mismatch | **3** | injected one-bit perturbation in pass B ⇒ terminal `TWIN_MISMATCH`, verdict EXECUTION_FAILED, non-zero, never success; the 24 computed rows still observed |
| T4 | publication failure | **3** | injected read-only output dir at FBES1-PLA-D0-S2 ⇒ 24 rows counted observed (4 with published=false), terminal `PUBLICATION_FAILURE`, fail-closed |
| T5 | interrupted + retry | **3 then 0** | abort after 5 ⇒ 5 terminals, observed=5, TECHABORT; retry completes remaining 19: 24 identity rows TOTAL, observed=24, `skipped_terminal` == the 5 (never recomputed — copied bytes byte-equal), no overlap with `computed`, ledger bytes prefix-preserved, EXECUTION_COMPLETE |
| T6 | existing refusal suite | **0** | `test_runner_refusals.py` 14/14 PASS (see §5) |
| T7 | lock released on exception | **3** | injected executor exception mid-computation ⇒ flock `free`, registry row cleared, `trial_ledger.verify()` ok with 7 terminals, lock released FAILED |
| T8 | production-default safety | **0 (asserts refusals)** | (a) no sandbox + no GO ⇒ exit 2 (live real-state refusal: REFUSED_CONTROL_STATE_DRIFT / LAG_ANCESTOR disclosed — or REFUSED_NO_GO on a matched head); (b) grep: no `scratch/synthetic` reference in either source; AST: every `RUNTIME_DIRNAME` access confined to sandbox-named functions; `resolve_lock_runtime(None)` is None; (c) `--sandbox-root` + real-root `--freeze-path` ⇒ SANDBOX-ISOLATION refusal, exit 2 |
| T9 | reopen-after-execution | **0** | fresh TrialLedger over the T1 ledger: verify ok, observed 24, complete, reopen mutates zero bytes |
| T10 | invalid variants at BOTH boundaries | **0 (asserts refusals)** | runner boundary in sandbox: paraphrased GO ⇒ REFUSED_NO_GO (2); diverged registry head ⇒ REFUSED_CONTROL_STATE_DRIFT (2); tampered sandbox freeze ⇒ REFUSED_DRIFT (2). executor boundary (direct calls): TOCTOU drift ⇒ exit 2 + REFUSED row; pre-held sandbox lock ⇒ exit 75 + NOT_RUN_RESOURCE_CONFLICT row; fault injection in production mode ⇒ AssertionError by construction |

Refusal ledger law held everywhere: run-level REFUSED rows carry
`identity_id=None` and never increment the observed denominator.

## 5. T6 — the pre-existing refusal suite (14/14, exit 0)

`test_runner_refusals.py` re-run: **14/14 PASS, exit 0**
(`test_logs/T6_refusals_full_run.txt`). 13 tests pass byte-unchanged
(no-GO, paraphrase, delegated flag/language, early-GO binding, freeze
drift, DIVERGED + LAG_ANCESTOR heads, real flock conflict 75, A7 missing,
real-state refusal, preflight twin, preflight-writes-nothing).

**One honest change**: `test_08` asserted the WOULD-EXECUTE STUB — the
exact artifact this lane removes. It now asserts its successor law: a
fully-valid synthetic GO + consistent simulated state passes every gate and
then dies at the `PRODUCTION-DEFAULT-AUTHORITY` guard
(`REFUSED_CONTROL_STATE_DRIFT`, exit 2) because production execution
refuses authority-path overrides. The refusal suite's sha is pinned in the
contract v2.1 addendum.

## 6. Lock lifecycle evidence

- Acquire: canonical `governance.heavy_lock.acquire(cycle_id=…, role=
  "SCORED-EXECUTION")` — sandbox T1 handoff records
  `{"acquired": true, "role": "SCORED-EXECUTION", "runtime":
  "<sandbox>/heavy_runtime", "pid": <run pid>}`; released `FINISHED`.
- Conflict: T6 test_06 (gate level) + T10e (executor level) ⇒ exit 75 +
  REFUSED row, foreign holder never touched.
- Exception safety: T7 ⇒ flock free + registry cleared + ledger consistent.
- Production mode never redirects the runtime (T8b AST proof; the only
  `heavy_lock.RUNTIME_DIRNAME` accesses live inside
  `_patch_sandbox_lock_runtime`/`restore`).
- The real machine-wide runtime was never written by this lane.

## 7. Decision packet — [IMPLEMENTED-DEFAULT-PENDING-RATIFICATION]

No SPEC/plan law governs the following execution details. Each is the
minimal deterministic reading; none touches a frozen law (24 identities,
signal/fill/exit/donor laws, Variant A, folds v3, budget 24). GO-blocking
consequence is named per item.

- **D-1 Ledger PASS/FAIL semantics for scored identities.** The scored run
  is the FIRST computation; no scientific pass/fail threshold exists for
  an identity. Implemented default: `PASS` = the identity's mechanics
  completed (record produced); `FAIL` = the identity's computation raised.
  Cost/warmup regressions run as run-level reconciliation checks
  (fail-closed) rather than per-identity verdicts. *GO-blocking if
  ratified differently: the 24 terminal rows' status distribution.*
- **D-2 Run-level files under an injected publication failure.** With the
  output dir read-only, `trades_index.json`/`summary.json` writes fail and
  are recorded as publication failures (`identity_id: null`); the pass
  still completes so the twin + reconciliation run and the failure is
  fail-closed. *Consequence: a publication-failed run always ends
  non-zero; no partial success exists.*
- **D-3 Retry with a missing/unverifiable prior output.** A terminal slot
  whose prior published bytes are missing or fail the recorded
  `result_sha` is NEVER recomputed (budget law wins); the run ends
  `PRIOR_TERMINAL_OUTPUT_MISSING` (fail-closed). *GO-blocking if the owner
  prefers re-computation over fail-closed: requires an owner amendment to
  the budget law.*
- **D-4 Sandbox R0 keeps the REAL worktree for git identity.** Isolation
  law (c) is enforced on all authority INPUT/OUTPUT paths; the registry
  check queries the real checkout read-only (branch/HEAD) against the
  sandbox registry row COPY. Reading (ii) of "real-root path". *Consequence:
  a sandbox run refuses if the real checkout identity diverges from the
  row copy — intended.*
- **D-5 Production run-artifact location.** Post-GO scored outputs default
  to `<gate6/ledger>/runs/<run-label>/` (next to the real ledger). The
  contract v2.1 addendum records this; a different home needs a contract
  amendment.
- **D-6 Exit code 3 covers terminal execution failure states.**
  `TWIN_MISMATCH` / `PUBLICATION_FAILURE` / `COMPUTE_FAILURE` /
  `RECONCILIATION_FAILURE` / `ABORTED_SANDBOX_FAULT` /
  `PRIOR_TERMINAL_OUTPUT_MISSING` all exit 3 (the v2 contract's
  technical-failure code), distinguished by the terminal state in the
  manifest/handoff.
- **D-7 Finalization-failure law [IMPLEMENTED-DEFAULT-PENDING-RATIFICATION;
  added by FINALIZE-FIX 2026-10-05 after the FAIL_FINALIZATION
  reproduction].** A finalization failure (ledger summary/sha, lock
  release, terminal-handoff write, runtime restore — any cleanup step of
  the executor's `finally`) can NEVER keep a success verdict. Authority
  check: the registered plan carries no executor terminal vocabulary (the
  SPEC §9 `*_BLOCKED_<reason>` names are pre-decided A7 terminal-audit
  outcomes, a different layer the runner must never select), so this
  packet records the implemented default. Law: (i) terminal state
  `FINALIZATION_FAILURE` — a SINGLE class state consistent with the D-6
  reason-class convention, with per-stage detail in the run's
  `finalization_failures[]` list (`stage`: ledger_summary / lock_release /
  runtime_restore / terminal_handoff) because several cleanup steps can
  fail in one run and the cleanup-order law requires collecting ALL;
  (ii) exit code 4 — distinct from 3 so a finalization failure
  (computation may be complete, evidentiary closure failed) stays
  machine-distinguishable from a terminal execution failure; no prior
  contract code used 4; (iii) `computation_complete` (true/false) records
  the computation phase separately from the finalization verdict — a
  computation-complete run with a finalization failure is a FAILURE,
  never EXECUTION_COMPLETE; (iv) an already-failed run keeps its original
  terminal state (original error never masked) with the finalization
  dimension in `finalization_failures[]`; refusal exits (2/75) stand;
  (v) lock evidence law — `lock_released_status` is claimed ONLY from
  measured evidence: normal return ⇒ intended FINISHED/FAILED/TECHABORT;
  a raise ⇒ `UNVERIFIED_RELEASE_RAISED` + a canonical read-only
  `heavy_lock.inspect()` against the same runtime dir recorded in
  `lock_inspect_after_release_failure`; never force-unlock, never kill
  workers, never delete lock files; (vi) handoff write failure ⇒ the
  primary path is never claimed, best-effort `terminal_handoff_ERROR.json`
  fallback, and if even that fails the record is IN-MEMORY ONLY (stated);
  (vii) ledger bytes / observed denominator / computed results are never
  rewritten. *GO-blocking if ratified differently: the exit-code table and
  the FINALIZATION_FAILURE state name.*

## 8. Live findings (carried, not introduced by this lane)

- **F-1 (LOW, carried)** Real ROOT registry row head `609d7ac9…` is a
  proper git ancestor of the actual HEAD `8bb9d4a8…` (merge-base verified
  by the runner's R0) — the disclosed N-1 lag character; the execution
  gate refuses on it until the controller reconciles the registry via its
  own tooling (`must_reconcile_before_go`). Demonstrated live by T8a.
- **F-2 (NOTE)** `auth/GO_RECORDED.json` ABSENT — the expected pre-GO
  state; the runner refuses (T8a, T6 test_01/09). The fake GO exists only
  inside the sandbox.

## 9. Files

- `gate6/runner/scored_executor.py` (NEW) f5ad7d48…
- `gate6/runner/scored_runner.py` (stub removed; executor wired; sandbox
  law) 18258cf1…
- `gate6/runner/test_execution_path.py` (NEW, T1–T10) d9d011c1…
- `gate6/runner/test_runner_refusals.py` (test_08 converted) 3678446b…
- `gate6/runner/scratch/synthetic/make_sandbox_fixtures.py` (NEW, committed
  generator) 588775db… · `.gitignore` a64a374a… ·
  `test_logs/` (recorded exit codes + transcripts)
- `gate6/runner/LAUNCH_CONTRACT_V2.json` / `.md` (append-only v2.1)
- `gate6/runner/EXEC_BUILD_REPORT.md` (this file)
- `dispatch/handoff_EXEC-BUILD.json`

## 10. Authority claims

PRE-GO ONLY: this lane typed no GO, consumed no GO; the real gate's GO
artifact remains ABSENT and the runner refuses on the real state today. NO
real outcome/PnL computed — every scored number this lane produced came
from the SYNTHETIC sandbox panel and is stamped SYNTHETIC-SANDBOX. Frozen
laws unchanged. Root checkout read-only except this lane's write boundary
(`gate6/runner/**` + `dispatch/handoff_EXEC-BUILD.json`); the real ledger
directory does not exist; no registry write; no push/merge/history-rewrite;
no S1; zero network; Python = ROOT .venv; no commit (HEAD unchanged).

- **D-8 Residual verification-display/coverage items [IMPLEMENTATED-AS-DISCLOSED; folded per verifier F-V1/F-V2, 2026-10-05].**
  (i) F-V1 [LOW, diagnostic-only]: check_drift's name-keyed `pins` output
  map clobbers the live v2_2 `scored_executor` entry with the tail
  HISTORY entry of the same name — enforcement (mismatch list) computed
  inline and proven correct; display only. (ii) F-V2 [LOW, latent,
  post-GO-only]: the execution-mode refusal-gate `facts` block covers
  BASE pins only; a drifted *addendum* pin post-GO is caught by preflight
  wiring + drift.pass + TOCTOU-side checks but not by the facts-block
  itself. Both are recorded as known limitations for owner visibility in
  the same ratification packet as D-1..D-7; fixing either pre-GO would
  re-pin the runner and re-open the wave cycle for cosmetic/latent-only
  gain — deliberately deferred.

- **D-8 disposition UPDATED (append-only, 2026-10-05, PIN-ENFORCE wave):
  F-V1/F-V2 FIXED with evidence — this entry SUPERSEDES the earlier
  "deliberately deferred" framing, which was rescinded by fix3/FAIL_FV2.md
  (the enforcement hole was reproduced to completion and is a PRE-GO
  blocker; the owner's directive was correct).** Fix + behavioral proof:
  fix3/PIN_ENFORCE_REPORT.md (live_operative_pins law everywhere; gate
  fails closed on drift.pass=false; post-acquire reverify = full live
  set; self-integrity binding of the imported module; live/history
  diagnostics separated; P1-P10 10/10 through the production path; the
  exact FAIL_FV2 tamper now refuses BEFORE computation with zero
  artifacts). The owner is no longer asked to accept any enforcement
  defect; nothing in D-8 remains pending.

- **D-1 rationale ERRATUM (append-only, 2026-10-05, per owner
  directive)**: the original D-1 line "The scored run is the FIRST
  computation; no scientific pass/fail threshold exists for an identity"
  was WRONG as stated. Correct law (two layers): **ledger PASS/FAIL is
  EXECUTION status; the scientific criteria ARE pre-registered at SPEC
  §8 (Stage-A gates G1-G9 + K2 family-kill, per identity); the
  scientific evaluation is currently NOT_RUN and will be evaluated by
  terminal A7 after the scored run.** The D-1 DECISION itself (what the
  owner ratifies: PASS = mechanics-complete, FAIL = computation-raised,
  execution-layer semantics) is UNCHANGED; only the rationale sentence is
  corrected. The owner's verbatim directive is recorded in the packet
  correction note.

- **RATIFICATION RECORD (append-only, 2026-10-05)**: owner ratified
  **D-1..D-7 at the implemented defaults** + **ACKNOWLEDGE AUTHORITY**
  for DA45 (verbatim quote + effect map at
  `auth/RATIFICATION_RECORDED.json`; contract v2_4 addendum carries the
  status). Zero implementation bytes changed. The decision packet's
  pending list is now EMPTY. NOT a GO; scored remains 0/24.
