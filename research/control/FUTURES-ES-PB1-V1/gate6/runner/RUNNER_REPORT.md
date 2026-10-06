# RUNNER_REPORT — FUTURES-ES-PB1-V1 gate-6 runner lane (RUNNER, pre-GO)

- Lane RUNNER · 2026-10-05 · worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`,
  branch `prep/futures-es-reg-20261004`, start HEAD
  `8c8c5020174c8a1a5dd00e5d53ba168235407ec9` (== dispatch SHA; HEAD unchanged —
  this lane commits nothing).
- **PRE-GO LAW HOLDS**: the runner refuses to compute scored outcomes today and
  will refuse until the typed owner GO exists at this cycle's registered gate.
  Zero outcome computation on real data happened in this lane (existence+sha
  checks only; the execution path is a documented stub).

## 1. M1 — gate-6 audit conclusion: no scored runner existed (built, M3)

Swept the cycle dir + repo for any existing scored-runner implementation:

| found | verdict |
|---|---|
| `gate6/runner/` | **ABSENT before this lane** — no runner existed for this cycle |
| `gate6/trial_ledger.py` (`bf89be55…`, the FIXED module, commit `8c8c502`) | REUSED — the runner imports it (ledger + RefusalGate + twin bookkeeping) and re-hashes it against the contract pin at startup |
| `final/dryrun_builder_v3.py` (`5a08c9fd…`) | machinery of record — the post-GO scored wiring adapts it; NOT invoked by this lane (stub only) |
| `gate6/scored_runner_spec.md` (v1) | HISTORY — pointed at superseded freeze v2 / builder v2.1 / withdrawn DONOR_LAW_CARRYOVER; superseded by `runner/LAUNCH_CONTRACT_V2.*` (v1 file not edited) |
| `DAYTRADER-100-V1/run_scored_locked.py`, `BTC-COMBO6-SCORED-V1/run_scored_locked.py` | prior cycles' lock-wrapper PATTERN only — bound to other SPECs/panels, not reusable; their GO_RECORDED.json format is the artifact precedent |
| `gate6/synthetic_smoke_test.py`, `gate6/fix/`, `gate6/smoke/` | bookkeeping smoke/repair history — not a runner |
| root checkout `research/control/FUTURES-ES-PB1-V1/` | no gate6/ (this worktree is the registered integration surface) |

Conclusion: **build (M3)** — a contract-v2 pre-flight authority gate + ledger
integration + execution stub, reusing the fixed ledger machinery verbatim.

## 2. Contract v2 (operative; supersedes spec v1)

`LAUNCH_CONTRACT_V2.md` (+ `.json` = the runner's pin source), written and
verified at HEAD `8c8c5020…`:
- Operative freeze `final/selection_freeze_v3.json` sha
  `0b0d269abbcafd065fa84ba3ba1047ac27df7fcc86675ccfef6f47666d951ff9` —
  re-measured, EXACTLY the `OPERATIVE_FREEZE_PIN.md` sha (pin file itself
  pinned `5b3ea93c…`; its text verified to carry the operative sha). The
  A7-adjudicated bytes `a992baac…` are recorded as HISTORY (superseded by the
  two disclosed display-only corrections F-1 + VP3-L1).
- Exclusion set `exclude_list_v3.json` `b101f5c7…` (+ in-freeze round-trip).
- Machinery `final/dryrun_builder_v3.py` `5a08c9fd…` (+ generator lineage
  `b8adbd67…` / `cf0fd897…`).
- Donor law: SPEC §4 [ERRATUM A7-SPEC-M5] flag-based on the CURRENT freeze;
  the runner verifies the freeze itself declares `DONOR_LAW_CARRYOVER.md`
  (`314ae947…`) withdrawn — the carryover law is REJECTED as superseded
  history, never an operative input.
- A7-v3 (`f8842e3d…` / digest `d42f27d9…`): verdict AUTHORIZED_WITH_FINDINGS,
  0 CRITICAL / 0 HIGH / 0 MEDIUM (1 LOW F-1, 2 NOTE N-1/N-2); R2
  non-inheritance from a7 v1/v2 enforced.
- Identities 24 (byte-exact order+set vs the live freeze; contract list
  transcribed from the freeze and re-verified byte-exact); costs Variant A
  (fees 2.25/side = 0.85+1.38+0.02; all-in 21.00/33.50/46.00; RT ×2;
  forbidden 1.386/21.006/33.506/46.006 asserted ban-only); eval 2,921
  (F1 375 / F2 948 / F3 708 / F4 890); budget 24; GO phrase
  `GO FUTURES-ES-PB1-V1 SCORED EXECUTION` REGISTERED_NOT_CONSUMED.
- SPEC `445f7499…`; panel `7ae6de2d…` (existence+sha ONLY); chain
  `7b6179d2…`; identity-table source `6e391980…`; PREGO_REPAIR `db0360fa…`;
  holiday `f3a8b4d4…`; DA45 `3acc6e9d…`/`76fd46c0…` (both AUTHORITY_EXISTS);
  FAIL_DONOR_VIOLATION `2f06de66…`; trial_ledger `bf89be55…`.

## 3. Refusal test matrix — 14/14 PASS (`test_runner_refusals.py`, synthetic + sandbox only)

| # | scenario | verdict | exit | REFUSED ledger row |
|---|---|---|---|---|
| 1 | no GO artifact | REFUSED_NO_GO | 2 | yes (`counts_observed=false`) |
| 2 | paraphrased GO (`SCORRED`) | REFUSED_NO_GO | 2 | yes |
| 3a | delegated GO (`typed_by_owner=false`, `typed_by=CONTROLLER`) | REFUSED_NO_GO | 2 | yes |
| 3b | delegated language ("on behalf of the owner") | REFUSED_NO_GO | 2 | yes |
| 3c | early GO (key_1 bound to a non-operative audit sha) | REFUSED_NO_GO | 2 | yes |
| 4 | freeze drift (tampered copy) | REFUSED_DRIFT | 2 | yes |
| 5a | registry head DIVERGED (non-ancestor / non-commit row head) | REFUSED_CONTROL_STATE_DRIFT | 2 | yes |
| 5b | registry head LAG_ANCESTOR (stale-but-ancestor row) | REFUSED_CONTROL_STATE_DRIFT | 2 | yes |
| 6 | heavy lock HELD (REAL flock + registry row in a temp runtime; the check reuses `governance.heavy_lock` primitives with injectable runtime dir — never a weaker check) | NOT_RUN_RESOURCE_CONFLICT | 75 | yes |
| 7 | A7 digest missing | REFUSED_NO_AUTH | 2 | yes |
| 8 | fully-valid SYNTHETIC GO + consistent simulated state (sandbox) | **WOULD EXECUTE stub only** (rc 0; nothing computed; ledger stays empty) | 0 | — |
| 9 | REAL state (real registry head-lag, GO absent) in execution mode | REFUSED_CONTROL_STATE_DRIFT | 2 | yes — the runner refuses TODAY, in its own smoke test |
| 10 | reproduction: deterministic preflight manifest run twice | **BYTE-IDENTICAL twin** (also via `trial_ledger.twin_compare`) | 0 | — |
| 11 | preflight-only writes nothing (ledger path pointed at a probe dir) | no files created | 0 | — |

Suite result: **Ran 14 tests — OK** (ROOT .venv). Every refusal test verified
the non-zero exit AND the REFUSED row in the sandbox ledger written by the
FIXED `trial_ledger.py`; REFUSED rows never increment the observed denominator.

## 4. M5 — read-only REAL-input preflight (`--preflight-only`): wiring GREEN

Real freeze/panel/authority hashes from the real paths (no outcome
computation, no parquet parse), run twice; artifacts under `runner/preflight/`:

- 20/20 contract pin entries reconciled (19 live-file sha MATCHES — incl.
  selection_freeze_v3 == OPERATIVE_FREEZE_PIN sha `0b0d269a…`, exclude_list_v3
  `b101f5c7…`, builder v3 `5a08c9fd…`, A7-v3 `f8842e3d…`/`d42f27d9…`, SPEC
  `445f7499…`, panel `7ae6de2d…`, chain `7b6179d2…`, identity source
  `6e391980…`, DA45 `3acc6e9d…`/`76fd46c0…`, PREGO `db0360fa…`, holiday
  `f3a8b4d4…`, FAIL_DONOR_VIOLATION `2f06de66…`, DONOR_LAW_CARRYOVER history
  `314ae947…`, trial_ledger `bf89be55…` — plus 1 history record for the
  superseded A7-adjudicated freeze bytes `a992baac…`); 8/8 freeze round-trips
  TRUE (exclude-sha round-trip, identity ids byte-exact, donor-law supersedes
  record, Variant-A cost table, forbidden-value ban, eval 2,921 + F1–F4,
  operative pin carries operative sha, fixed trial_ledger sha).
- A7-v3: AUTHORIZED_WITH_FINDINGS, unresolved C/H/M = 0. Heavy lock:
  FREE_PROVEN (canonical decision tree, real machine runtime). D-A4/D-A5:
  ADJUDICATED_AUTHORITY_EXISTS. GO artifact: ABSENT — the expected pre-GO
  state (exit-neutral in preflight). `wiring_failures: []` → exit 0 both runs.
- **Gate verdict (honest): REFUSED** — `REFUSED_CONTROL_STATE_DRIFT` from R0:
  the REAL registry row head is `71326c8c22307bc62ef2f81b80b3fef3ada5e96e`
  vs actual HEAD `8c8c5020174c8a1a5dd00e5d53ba168235407ec9` — classified
  `LAG_ANCESTOR` (merge-base-verified proper ancestor; the disclosed N-1
  head-lag character, researchctl doctor LOW). Exit-neutral for the wiring
  check, flagged `must_reconcile_before_go: true`, and it FAILS the execution
  gate: the controller must reconcile the registry via its own tooling before
  any scored execution.
- **Twin manifests: BYTE-IDENTICAL** —
  sha256 `2e60174761d7f9c13f324b224cfd82b91bc62b00cf9d853623b79a639b156b90`
  for both `preflight/manifest_run1.json` and `manifest_run2.json`
  (deterministic: no wall-clock fields). The reproduction twin of scored
  OUTPUTS remains post-GO; here the PREFLIGHT manifest is twinned, as scoped.
- Execution-mode demonstration on the real state (ledger sandboxed under
  `runner/sandbox/`): exit 2, REFUSED_CONTROL_STATE_DRIFT row recorded
  (seq 1, `counts_observed=false`), ledger `verify()` ok, observed denominator
  0 — zero consumption.

## 5. Honesty register

- The registry head-lag is REAL and disclosed above; it is this cycle's
  recurring N-1 character. The runner refuses on it by design (row head must
  equal actual HEAD at scored-execution time).
- GO artifact absent everywhere — nothing was typed, consumed, or fabricated;
  the synthetic GO used by tests exists only inside temp sandboxes.
- The execution path is a STUB: it proves gate passage end-to-end and logs
  the planned invocation; the real scored wiring (two-pass twin over
  `dryrun_builder_v3.py`, G8 byte-match, terminal A7 hook) is the post-GO
  lane's job against LAUNCH_CONTRACT_V2 §4.
- No S1, no network, no push/merge/commit, no registry writes, root
  read-only; the only writes are inside
  `research/control/FUTURES-ES-PB1-V1/gate6/runner/**` and
  `dispatch/handoff_RUNNER.json`.

## 6. Files (this lane's write boundary)

```
gate6/runner/LAUNCH_CONTRACT_V2.md          sha256 b0cc4d76792fce7efa352f17bd4e6b06e51b8b9319ce6770347e572089b3f019
gate6/runner/LAUNCH_CONTRACT_V2.json        sha256 16e53d24b633c5416e180083ccad74c7300561979ffd23f64111db947995811b
gate6/runner/scored_runner.py               sha256 9bb8156756db6cc9100900a85302a58ef5df252703d9fa822154397096e5eeeb
gate6/runner/test_runner_refusals.py        sha256 4c5c89513b9b3bff1e0052dd4d6b50a0ca25ade029e53eee7f4dba2c0192ba8c
gate6/runner/preflight/manifest_run1.json   sha256 2e60174761d7f9c13f324b224cfd82b91bc62b00cf9d853623b79a639b156b90  (== run2)
gate6/runner/preflight/manifest_run2.json   sha256 2e60174761d7f9c13f324b224cfd82b91bc62b00cf9d853623b79a639b156b90  (== run1)
gate6/runner/preflight/run{1,2}.stderr.txt  preflight stderr transcripts
gate6/runner/sandbox/trial_ledger.jsonl     real-state refusal demo row (REFUSED, seq 1)
gate6/runner/sandbox/refusal_record.json    refusal record mirror
gate6/runner/sandbox/demo_refusal.stderr.txt demo transcript
gate6/runner/RUNNER_REPORT.md               this report
dispatch/handoff_RUNNER.json                structured handoff (zcode_orch_v3_handoff@1)
```

— End RUNNER_REPORT.
