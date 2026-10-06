# VERIFY_REMEDIATION — F1/F2-REMEDIATION wave, FUTURES-ES-PB1-V1

- Verifier: compact fresh-context verifier (audit only; zero network; no
  real-outcome computation; sandbox suite re-runs only).
- Date: 2026-10-05.
- Measured at EXACT committed SHAs:
  - worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`
    (branch `prep/futures-es-reg-20261004`) HEAD = **`cad6daea1e28bebff76c722ed9c42426e62c2d58`**
    (rev-parse at verify start — matches the dispatch SHA, zero drift).
  - ROOT `main` HEAD = **`77a21c1e9727198b21fc2f19331e46d8cc688a5d`** (matches dispatch).
  - Registry row for FUTURES-ES-PB1-V1 `head` == `cad6daea1e28…` (reconcile commit
    `77a21c1e` applied). R0 preflight: `head_check = MATCH`.
- Both trees clean at start (0 entries each).

## R1 — Drift hole actually closed: **PASS**

`operative_pins()` (scored_runner.py:339–367): base `pins` + every `v2_*_addendum`
`new_pins`, deduped by ARTIFACT PATH, later addendum wins; superseded rows kept at
the tail with `_status=HISTORY_SUPERSEDED`. Three consumers verified:

1. **check_drift loop** — iterates `operative_pins()`; HISTORY rows recorded
   never live-checked; everything else re-hashed. Behavioral proof (module
   imported from the worktree at cad6daea):
   - (a) COPY of the real contract in `/tmp` with ONE v2_2 pin sha tampered
     (`scored_executor` `2e3c4387…` → `000…0`), `check_drift` against REAL worktree
     paths ⇒ `pass=False`, `mismatched_pins == ['scored_executor']` exactly, no
     other mismatches. Second data point: v2_1 test-file pin
     (`test_runner_refusals_v2_1`) tampered ⇒ `mismatched_pins ==
     ['test_runner_refusals_v2_1']`. Untampered control ⇒ `pass=True`. NEW PINS
     ARE LIVE-VERIFIED.
   - End-to-end: real runner `--preflight-only --contract <tampered copy>` ⇒
     **exit 2, wiring_failures = ['REFUSED_DRIFT']** (manifest:
     `preflight_tampered.json`). Untampered real preflight ⇒ exit 0,
     `wiring_failures=[]`, drift pass over 26 pin entries, gate = REFUSED_NO_GO
     (expected pre-GO) (`preflight_real_cad6daea.json`).
   - (b) `operative_pins()` on the real contract: 27 entries = 25 live + 2
     HISTORY_SUPERSEDED; `scored_runner_v2_1` (v2_1 runner pin, `18258cf1…`,
     same path as the v2_2 pin) comes out `_status=HISTORY_SUPERSEDED` with the
     supersession note; the live runner pin is `scored_runner` `58217ad4…` (v2_2).
     Same demotion for v2_1 `scored_executor` (`f5ad7d48…` → superseded by
     `2e3c4387…`). Visible in the R4 output of the committed T-suite logs and in
     my real preflight manifest.
2. **resolve_sandbox_paths** — resolves every non-HISTORY operative pin under the
   sandbox root (verified: `pin:scored_executor` → sandbox runner path; HISTORY
   skipped). Exercised end-to-end by the T-suite re-run (10/10, below).
3. **pins_by_name / TOCTOU** — `pins_by_name` built from `operative_pins()`;
   runner consumers are `a7_prelaunch_v3_digest` and `machinery_builder_v3`
   (both base pins, never re-pinned ⇒ not affected by the name-view clobbering
   observation F-V1 below); the post-acquire TOCTOU re-verify looks up the same
   two plus the base-only `TOCTOU_PIN_NAMES`.

## R2 — Pins true at HEAD: **PASS (100%)**

Independent script over `operative_pins()`: **24/24 non-HISTORY pins match disk**,
0 mismatched; 3 HISTORY records skipped (a7_adjudicated_freeze_bytes_HISTORY +
the 2 superseded rows). Spot checks: `scored_executor` = `2e3c43878b53…` MATCH;
`scored_runner` = `58217ad434b2…` MATCH; v2_1 test-file pins `test_execution_path`
`d9d011c1…`, `test_runner_refusals_v2_1` `3678446b…`, `make_sandbox_fixtures`
`588775db…` all MATCH. Corroborated by the real preflight (drift pass, 26-entry
R4 output).

## R3 — No fixture literals: **PASS**

`grep -c "scratch/synthetic"` in scored_runner.py = 0 and scored_executor.py = 0.
Only generic docstring uses of the word "synthetic" (sandbox law prose). No /tmp
or fixture path literals in production source.

## R4 — Suites: **PASS**

- Refusals (MANDATORY re-run by me, at cad6daea): **14/14 OK in 4.447s**, exit 0
  (log: /tmp evidence, mirrored in the JSON below).
- Execution T-suite (re-run by me at cad6daea, sandbox-only): **10/10 OK in
  96.601s**, exit 0 — exercised the operative_pins code path end-to-end with
  `actual_head = cad6daea…` recorded in the sandbox manifests.
- Finalization F-suite: **committed-log check, not re-run** (permitted: logs are
  committed and consistent). `verify/finalize/evidence/verifier_Fsuite_stderr.txt`:
  10/10 OK in 1420.610s; `verifier_Fsuite_results.json` `_suite` = {tests_run 10,
  errors 0, failures 0}; per-test terminal records show the D-7 law exactly
  (F2/F3/F4/F5 exit 4 FINALIZATION_FAILURE with computation_complete=true;
  F3/F4 lock_released_status=UNVERIFIED_RELEASE_RAISED; F6 exit 3 no masking;
  F8 retry variants). fix2/test_logs_finalization/F9_*: refusals 14/14 (4.297s)
  + T-suite 10/10 (98.021s), exit 0. Reproduction outputs (BUG1/BUG2 → exit 4,
  no success claim) committed. Report claims (14/14 / 10/10 / 10/10) are
  consistent with the committed evidence (duration-quote wobble: F-V3).
- Worktree test-log files overwritten by my T-suite re-run were verified
  wall-clock-only (timestamps/pids/sandbox ledger shas; my run recorded
  actual_head cad6daea) and **restored to HEAD** — worktree clean at end.

## R5 — D-7 / v2.2 ratification status: **PASS**

- EXEC_BUILD_REPORT §7: **D-7 [IMPLEMENTED-DEFAULT-PENDING-RATIFICATION]** with
  per-stage law and "GO-blocking if ratified differently" consequences.
- Contract `v2_2_addendum.owner_ratification_pending`: "D-7 (finalization-failure
  law + exit 4) and this addendum's re-pins ride the same owner ratification as
  D-1..D-6 before GO."
- Wave-diff ratification sweep: every "ratif-" hit is pending/conditional
  ("pending owner ratification", "D-1..D-7 UNRATIFIED", "D-7 + v2.2 re-pins
  pending owner ratification (GO-blocking)", "GO-blocking if ratified
  differently", "ratified alongside D-1..D-7 before GO"). **No self-ratification
  language anywhere.** Handoff_FINALIZE-FIX.json `recommended_next_action` =
  owner ratifies D-1..D-7 then typed GO.

## R6 — Wave hygiene: **PASS**

- Wave diff `7258f8d2..cad6daea`: 31 files, **all under
  `research/control/FUTURES-ES-PB1-V1/`** — none outside the cycle dir.
- Registry reconcile commit `77a21c1e` on ROOT: exactly 3 control-plane files
  (CYCLE_REGISTRY.json / ACTIVE_CYCLES.json projection / events.jsonl +2
  append-only lines). CYCLE_REGISTRY.json: 4 changed lines = envelope
  updated_at/writer/write_token + the PB1 row's `head` and `updated_at`;
  **programmatic proof: exactly one cycle row changed (FUTURES-ES-PB1-V1); all
  foreign rows byte-identical.** Row head `cad6daea…` == actual worktree HEAD.
- `cycle doctor --json` (read-only): 72 total findings, **none of them a
  registry/head finding for this cycle**; the single mention is
  `STALE_HEARTBEAT LOW — label only` (expected-stale for a REGISTERED,
  non-running cycle; pre-existing class, not a drift finding).
- Stale-value sweep (use-as-value convention): 0.
  - Old v2_1 shas (`f5ad7d48…`, `18258cf1…`): only in law/history contexts — the
    v2_1 addendum's own recorded new_pins (demoted HISTORY_SUPERSEDED by the
    operative-pins law), T-suite R4 HISTORY output, and the F1 disclosure prose.
    **0 occurrences in any production module** (runner/executor/trial_ledger/
    both test files) and never as a live pin.
  - Old registry head `44269de…`: 1 occurrence — the PRIOR verifier's recorded
    `row_head` in VERIFY_FINALIZE.json (history evidence; live row is cad6daea).
  - Forbidden retired cost values (1.386 / 21.006 / 33.506 / 46.006): **absent
    from the operative cost table** (operative all_in 21.0/33.5/46.0, exchange
    1.38); remaining occurrences are the ban law itself and sandbox-ban
    assertions (string contexts).
  - Withdrawn "WOULD EXECUTE" stub: only in withdrawal-record prose/docstrings
    (runner line 18 is the docstring withdrawal note); no stub code.
- Trees at end: **worktree clean (0 entries)**; ROOT carries only this verify
  output (per write boundary).

## Findings (none GO-blocking)

- **F-V1 [LOW, diagnostic]** In `check_drift`'s name-keyed `pins` output the LIVE
  v2_2 `scored_executor` entry is clobbered by the tail HISTORY_SUPERSEDED entry
  of the same name — R4 displays the old `f5ad7d48…` HISTORY row for that name
  and the live `2e3c4387…` entry's diagnostics never appear (also visible in the
  committed T-suite logs). Enforcement is UNAFFECTED: `mismatched_pins`/`pass`
  are computed inline and correct (proven: tampered run exit 2,
  mismatched=['scored_executor']). Cosmetic/forensics-only; one-line fix
  candidate for a future append-only amendment.
- **F-V2 [LOW, latent, reachable only post-GO]** The execution-mode refusal
  gate's `input_sha_matches` facts are built from the BASE `contract["pins"]`
  only (scored_runner.py ~line 910), so in a post-GO production run a drifted
  ADDENDUM pin would not refuse via the R4 gate facts (drift.pass IS computed
  over all operative pins and preflight wiring flags REFUSED_DRIFT; the
  post-acquire TOCTOU set is base-only). Pre-GO this is unreachable (the gate
  refuses at R1 first; no GO exists; scored 0/24). Note: the sandbox happy-path
  T-suite structurally relies on the base-only facts set (the sandbox does not
  mirror runner/executor bytes — proven by T1's mismatched list), so extending
  the facts naively would break sandbox law; any closure belongs in the owner
  ratification packet (e.g. production-mode-only extension or sandbox mirroring
  of the code pins).
- **F-V3 [INFO]** FINALIZE_FIX_REPORT remediation addendum quotes suite durations
  (1361s / 96.8s / 4.56s) that differ slightly from the committed logs
  (1420.610s / 96.150s / 4.467s) — pass/fail claims match the committed
  evidence; duration quoting imprecision only.

## Verdict

**REMEDIATION_VERIFIED** — F1 (silent-drift hole) closed and behaviorally
proven; F2 (handoff schema) closed; pins 100% true at HEAD; no fixture
literals; suites green (refusals 14/14 + T 10/10 re-run by this verifier at
cad6daea; F-suite 10/10 via consistent committed logs); D-7/v2.2 correctly
PENDING-RATIFICATION with no self-ratification; wave confined; registry
reconcile surgical; doctor clean of registry findings; both trees clean at end.

## Pre-GO readiness statement

Machinery state: runner + executor + contract operative pins verified byte-true
at `cad6daea1e28…` (registry synced, R0 MATCH; preflight all-pins-green with
expected gate REFUSED_NO_GO; lock FREE_PROVEN; no real ledger exists; scored
0/24; no real outcome ever computed). Remaining before scored execution is
exactly the owner chain: (1) owner ratification of the D-1..D-7 decision packet
(EXEC_BUILD_REPORT §7), including D-7 finalization law + exit 4 and the v2.2
re-pins riding the same ratification (recommend folding findings F-V1/F-V2 into
that packet); (2) the typed owner GO `GO FUTURES-ES-PB1-V1 SCORED EXECUTION` at
this cycle's own gate. Nothing else is NOT_RUN on the machinery side.

— End VERIFY_REMEDIATION.
