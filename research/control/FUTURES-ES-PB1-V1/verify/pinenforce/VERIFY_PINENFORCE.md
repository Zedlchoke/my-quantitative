# VERIFY_PINENFORCE — fresh-context verifier, PIN-ENFORCE wave (F-V1/F-V2 closure)

- Verifier: compact fresh-context subagent, 2026-10-05. Audit only; zero
  network; synthetic sandbox runs only; NEVER real outcomes.
- Measured worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`
  branch `prep/futures-es-reg-20261004`, HEAD **`aef543dce634d072b27ecf01081eb8e4e9665da0`**
  (rev-parse matched the pinned SHA exactly).
- ROOT main HEAD: `cd48a1d9f546bd9fbfcb5f8c98bd6b41e31d81a6`; ROOT status clean
  at start and end. Worktree clean at start and at end except this verifier's
  own outputs under `verify/pinenforce/` (disclosed temporary churn below).

## VERDICT: PIN_ENFORCE_VERIFIED

All checks E1–E7 PASS (E6 optional P-suite re-run not repeated — committed
results + verifier spot-checks recorded). No blocking findings.

## E1 — FAIL-before-fix order: PASS

- `git log --diff-filter=A` shows `fix3/FAIL_FV2.md` was ADDED at commit
  `47e54e55ca0e4cb3757ba7296fa3186a12ec942a` ("FAIL record F-V2 (BEFORE fix)…
  NO fix in this commit"), and `47e54e55` is a git ancestor of HEAD
  (`merge-base --is-ancestor` ⇒ YES). Single fix commit `aef543dc` follows.
- Bytes at `47e54e55:…fix3/FAIL_FV2.md` contain BOTH the append-only claim
  erratum (prior "TOCTOU-side checks catch addendum drift" / "preflight
  wiring + drift.pass catch it" enforcement claims were WRONG for the
  execution path) AND the D-8 rescission ("deliberately deferred"
  disposition for F-V2 RESCINDED as insufficient — PRE-GO blocker).

## E2 — The flip, reproduced by the verifier: PASS (strongest level)

**Post-fix (my own run, fresh `--force` sandbox regenerated from HEAD
fixtures, root .venv):** `fix3/repro_fv2_after_fix.py` ⇒ script exit 0,
`flip_vs_FAIL_FV2=true`, ALL 8 checks true:

| check | value |
|---|---|
| tampered_live_pin_in | `v2_3_addendum` |
| exit_2 | true |
| reason_REFUSED_DRIFT | true |
| names_scored_executor | true |
| ledger_REFUSED_row | true |
| no_runs_dir | true |
| no_execution_artifacts | true |
| no_EXECUTION_COMPLETE_in_stdout | true |

**Pre-fix (my own reconstruction from git bytes at `47e54e55` — FULL
behavioral level, not just document-level):** built a temp mirror
(`/tmp/fv2_prefix/...`) from `git show 47e54e55:` bytes of `scored_runner.py`,
`scored_executor.py`, `LAUNCH_CONTRACT_V2.json`, `make_sandbox_fixtures.py`
and all 14 COPY_REAL authority sources; verified the extracted module bytes
hash EXACTLY to the operative v2_2 addendum pins (executor `2e3c4387…`,
runner `58217ad4…`; v2_1 rows show their superseded shas as expected).
Generated the pre-fix sandbox (same deterministic fixture shas as HEAD:
freeze `aad7dcde11f1a427`, panel `a12e26db383f06e7`, chain `9ced4e1380d86662`),
patched the sandbox rowcopy branch/head to the real values (provisioning
only — the generator ran in a non-git temp mirror), applied the EXACT
FAIL_FV2 tamper (v2_2_addendum.scored_executor.sha256 → `f`*64) and ran the
pre-fix production runner:

- `runner_rc = 0`, stderr `SCORED EXECUTION: verdict=EXECUTION_COMPLETE
  terminal_state=EXECUTION_COMPLETE exit=0`
- ledger 24 rows, 0 REFUSED; `runs/fv2_prefix_repro/` full execution
  artifacts (pass_a/pass_b/`terminal_handoff.json` verdict
  EXECUTION_COMPLETE exit_code 0) — **the false-success reproduced**.
- Same machine, same venv, same generator, same tamper — only the
  runner/executor/contract bytes differ ⇒ **the flip is caused by the fix,
  not the environment.**
- Direct call to pre-fix `check_drift` on the tampered contract: `pass=False`
  (drift was RECORDED pre-fix) while the run still completed ⇒ confirms the
  hole was enforcement, not detection. Pre-fix gate-facts source quoted:
  `input_sha_matches = { … for p in contract["pins"] …}` — BASE-ONLY, the
  tampered addendum pin never reached the gate.

Disclosure: my pre-fix reconstruction shows mismatched = [scored_runner,
test_execution_path, test_runner_refusals_v2_1, make_sandbox_fixtures] vs the
FAIL record's [scored_executor]: pre-fix addendum pin paths resolved against
the REAL worktree, so my mirror run (worktree at HEAD, post-fix module bytes)
adds mismatches for the re-pinned modules. Reconstruction-environment
artifact, moot post-fix (the HEAD generator stages ALL live pins under the
sandbox). The behavioral hole proof is identical in both.

## E3 — Code-read of the enforcement (HEAD): PASS

All four laws present, quoted from `gate6/runner/scored_runner.py` /
`scored_executor.py`:

(a) **Execution refuses on drift.pass=false** — `scored_runner.py:1115-1128`:
`elif allowed and not drift.get("pass"): allowed, reason = False,
"REFUSED_DRIFT"` with detail gate `R4-drift-failclosed` ("the execution gate
refuses whenever check_drift reports pass=false — base and addendum pins
alike; the RefusalGate facts are not the only enforcement path").

(b) **Gate facts use the live set** — `scored_runner.py:1079-1084`:
`input_sha_matches = { name: bool(row.get("match")) for name, row in
drift["pins_live"].items() }` — "built from the FULL LIVE pin set (base +
every addendum; NO hardcoded names)".

(c) **Reverify closure covers the full live set** —
`build_reverify_closure` (`:603-640`) iterates `pins_live` (the
`live_operative_pins` list passed at `:1257-1261`), re-verifying GO artifact
+ registry head + every live pin (sandbox paths dict first, then
worktree-relative contract path; missing/unreadable = named drift, fail
closed). Consumed by the executor AFTER `heavy_lock.acquire`:
`scored_executor.py:631-639` `drifts = list(cfg["reverify_authority"]() or
[])` ⇒ refuses `REFUSED_CONTROL_STATE_DRIFT`, gate `TOCTOU-post-acquire`.

(d) **Self-integrity binds imported bytes** — `:1239-1250` calls
`self_integrity_violations(contract, worktree, runner_file=os.path.abspath(__file__),
executor_file=os.path.abspath(scored_executor.__file__))`; the function
(`:643-687`) resolves each module's realpath → relpath → finds the live pin
BY PATH ("no pin name is hardcoded"), then enforces sha equality AND path
equality; any violation refuses BEFORE computation
(`REFUSED_CONTROL_STATE_DRIFT`, gate `SELF-INTEGRITY`).

**No base-only pin list remains in an enforcement path:** `grep
TOCTOU_PIN_NAMES` across runner/executor/tests hits ONLY comments marking it
removed (`scored_executor.py:133` "the former base-only hardcoded
TOCTOU_PIN_NAMES tuple is REMOVED"; runner comments at :47/:614/:1255). The
executor only ever calls the caller-supplied closure. `live_operative_pins()`
(`:356-406`) is the one law: base + all `v2_*_addendum` new_pins, deduped BY
ARTIFACT PATH later-wins, `*_HISTORY` names demoted; `operative_pins()` is a
compat wrapper (live + history, history carries `_status` HISTORY*).

## E4 — P4 no-hardcode proof: PASS

`fix3/test_pin_enforce.py` P4 injects a brand-new `v2_4_addendum` with new
pin `pin_enforce_probe_prego` (→ `auth/PREGO_REPAIR_RECORDED.json` path) —
NO production code change. (a) correct sha ⇒ exit 0 EXECUTION_COMPLETE with
the probe in `drift_check.pins_live` match=true; (b) tampered sha (`0`*64) ⇒
exit 2 `REFUSED_DRIFT` with the probe named in `mismatched_pins`, ledger
REFUSED row, no execution; (c) asserts the probe name exists in NO
production source (runner + executor text). `pin_enforce_results.json` P4:
`green_exit 0, probe_in_pins_live true, no_hardcoded_names true,
mismatched [pin_enforce_probe_prego], tampered_exit 2`. Enforcement is
purely the generic live-pin law (`live_operative_pins` consumes any
`v2_*_addendum` key by construction).

## E5 — Diagnostics F-V1 (real contract, read-only import): PASS

Direct `check_drift` on the real `LAUNCH_CONTRACT_V2.json` (no run, no
writes): `pass=true`, **`pins_live` has 23 names INCLUDING `scored_executor`
(match=true, source `v2_3_addendum`; `scored_runner` match=true,
`v2_3_addendum`)**, `mismatched_pins=[]`. `pins_history` holds 6 names with
the superseded twins: `scored_executor` entries `f5ad7d481605` (v2_1) +
`2e3c43878b53` (v2_2); `scored_runner` entry `58217ad434b2` (v2_2);
`scored_runner_v2_1` `18258cf1…`; `make_sandbox_fixtures`; plus the explicit
HISTORY rows (`a7_adjudicated_freeze_bytes_HISTORY`,
`donor_law_carryover_HISTORY`). No name clobber: the live row keeps its
`match` verdict; history is aggregated under `entries[]` with supersession
notes. Matches committed P7 (23 live / 6 history / 2 executor twins).

## E6 — Suites at HEAD: PASS

- Verifier re-ran `test_runner_refusals.py` + `test_execution_path.py`:
  **24 passed in 95.12s** (controller's committed re-run: 97s — consistent).
- `pin_enforce_results.json` records P9's three exit-0 regressions:
  `P9:test_runner_refusals.py exit 0 tail [OK]`,
  `P9:test_execution_path.py exit 0 tail [OK]`,
  `P9:fix2/test_finalization_fix.py exit 0 tail [OK]`.
- The ~23-min P-suite (P1–P10, committed 10/10 in 1381s) was NOT re-run —
  OPTIONAL per dispatch. Compensating verifier evidence: E2 (P2-equivalent
  flip end-to-end, both directions), E5 (P7-equivalent live/history split),
  E3 code-reads of the P3/P4/P5 enforcement sites, plus committed
  `pin_enforce_results.json` (P1–P10 all present with exit codes) and the
  committed P-run logs under `scratch/synthetic/test_logs/P*.stdout.txt`.

## E7 — Hygiene: PASS

- **Wave diff `47e54e55..aef543dc` confined to the cycle dir**: every changed
  path starts `research/control/FUTURES-ES-PB1-V1/` (fix3 artifacts, runner +
  executor + generator + contract, EXEC_BUILD_REPORT, handoff_PIN-ENFORCE.json,
  test_logs churn = new P-run evidence + T-suite re-run evidence — disclosed).
- **D-8 now fixed-with-evidence**: `EXEC_BUILD_REPORT.md:318-329` appended
  disposition — "F-V1/F-V2 FIXED with evidence — this entry SUPERSEDES the
  earlier 'deliberately deferred' framing, which was rescinded by
  fix3/FAIL_FV2.md… The owner is no longer asked to accept any enforcement
  defect; nothing in D-8 remains pending." Grep: remaining "deliberately
  deferred"/"TOCTOU-side" occurrences are only the superseded historical
  entry (explicitly marked superseded) and the rescission record itself.
- **D-1..D-7 pending language intact**: section 7 "Decision packet —
  [IMPLEMENTED-DEFAULT-PENDING-RATIFICATION]"; D-1..D-6 entries present,
  D-7 "[IMPLEMENTED-DEFAULT-PENDING-RATIFICATION]".
- **Stale-value sweep = 0**: pre-fix module shas (`2e3c4387`, `58217ad4`,
  `f5ad7d48`, `18258cf1`) appear ONLY in contract superseded addendum rows
  (history by law, confirmed by E5) and in historical evidence
  (prior-wave logs / prior verify artifacts / dispatch handoff). ZERO
  occurrences in production enforcement source; zero as live values. Live
  contract v2_3 pins match HEAD bytes exactly (executor `7fea1e0a3286`,
  runner `fcb42769dd7b`, fixtures `33bff94803df`).
- **Registry row** (ROOT `plans/CYCLE_REGISTRY.json`, the only registry
  containing the cycle): head `9bad9621ef24…` — LAGS actual HEAD by 2
  commits; `merge-base --is-ancestor` ⇒ proper ancestor (disclosed N-1 lag
  character; doctor HEAD_MISMATCH LOW). `go_phrase_state
  REGISTERED_NOT_CONSUMED`; budget 0/24 (scored 0/24); phase REGISTERED;
  lifecycle ACTIVE_LIGHT; s1 SEALED_UNTOUCHED; workers 0; active_heavy false.
- **Doctor findings for the cycle** (2, both LOW):
  `HEAD_MISMATCH LOW — FUTURES-ES-PB1-V1: branch aef543d vs registry 9bad962`;
  `STALE_HEARTBEAT LOW — heartbeat 2026-10-04T11:57:51Z is 1d old (label
  only)`. (Doctor totals across all cycles: LOW 20 / MEDIUM 39 / HIGH 14 —
  unrelated legacy cycles; none block this cycle's ratification packet.)
- **Trees clean at end**: ROOT clean; worktree shows only this verifier's
  outputs (`verify/pinenforce/`). Verification runs temporarily modified 11
  tracked evidence files (repro stderr + 10 T-suite logs) — restored to HEAD
  via `git checkout --` after evidence capture; net-zero (disclosed).

## E8 — Verdict + pre-GO readiness

**PIN_ENFORCE_VERIFIED.** F-V2 (execution-pin enforcement) and F-V1
(live/history diagnostics clobber) are closed with reproduced behavioral
evidence: the exact FAIL_FV2 false-success was reproduced by this verifier
from pre-fix git bytes and flipped to a fail-closed refusal by the fix, with
the generic live-pin law proven by the injected P4 probe and the four
enforcement sites confirmed by code read at HEAD.

Remaining before GO (unchanged scope): D-1..D-7 owner ratifications (D-8 no
longer asks the owner to accept a defect), registry head reconcile
(`9bad9621` → current HEAD via the registry's own tooling; currently a
disclosed ancestor-lag that FAILS the execution gate until reconciled), and
the owner's typed GO at the cycle's own gate. No scored outcomes exist
(0/24); nothing in this wave touched real outcomes, S1, or the root
registry.

## Findings by severity

- **BLOCKING: none.**
- **MEDIUM: none.**
- **LOW-1 (recorded):** registry row head `9bad9621` lags actual HEAD
  `aef543dc` by 2 commits (ancestor-confirmed; doctor HEAD_MISMATCH LOW) —
  expected pre-reconcile state; execution gate refuses LAG_ANCESTOR until
  the controller reconciles via the registry's own tooling before GO.
- **LOW-2 (recorded):** STALE_HEARTBEAT LOW (1d old) — label only for a
  REGISTERED cycle.
- **INFO:** verifier runs temporarily dirtied then restored 11 tracked
  evidence files; pre-fix reconstruction used a temp mirror with rowcopy
  branch/head patch + explicit `--worktree` (provisioning only); worktree
  has no `.venv` — root `.venv` used (as the lane does).

— End verifier report. Written under the wave write boundary
`research/control/FUTURES-ES-PB1-V1/verify/pinenforce/` in the WORKTREE only.
