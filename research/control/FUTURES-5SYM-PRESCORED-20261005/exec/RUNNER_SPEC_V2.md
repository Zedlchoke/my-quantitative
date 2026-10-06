# RUNNER_SPEC_V2 — symbol-parameterized scored runner for the 5-symbol PREP cycle

- Cycle: `FUTURES-5SYM-PRESCORED-20261005` · Lane: EXEC · 2026-10-05
- Artifact: `exec/scored_runner_v2.py` (single importable module + real CLI)
- Contract data: `exec/symbol_contracts.json`
- Lineage: FUTURES-ES-PB1-V1 gate-6 scored runner
  (`exec/_upstream_scored_runner.py`, FAIL-record revision c17ab2bf) + its
  refusal suite (`exec/_upstream_test_runner_refusals.py`, 999ece60) + its
  v1 execution contract (`exec/_upstream_scored_runner_spec.md`, a855dab8).
- **This spec authorizes nothing.** The runner is PREP infrastructure for
  FUTURE registered cycles. In THIS build it cannot touch anything real:
  the real governance dir is refused unconditionally (see R-GOV), so every
  run that computes is, by construction, a synthetic-sandbox run stamped
  `SYNTHETIC-SANDBOX`. No scored outcome produced by this runner is a
  research result.

## 1. CLI

```
python scored_runner_v2.py \
  --cycle-id FUTURES-5SYM-PRESCORED-20261005 \
  --governance-dir <sandbox>/gov \            # REQUIRED; real dir refused (R-GOV)
  --go-artifact <path>/GO_RECORDED.json \     # REQUIRED (T2/T3/T4)
  --authority-file <gov>/authority/authority_pack.json \  # REQUIRED (T5)
  --input-manifest <inputs>/input_manifest.json \         # REQUIRED (T6/T19)
  --spec-packet <inputs>/spec_packet.json \               # REQUIRED
  --cost-manifest <inputs>/cost_manifest.json \           # REQUIRED
  --symbol-contracts exec/symbol_contracts.json \         # default: sibling file
  --ledger <out>/ledger/trial_ledger.jsonl \              # REQUIRED, append-only
  --run-dir <out>/runs/<label> \                          # REQUIRED
  --final-status-out <out>/FINAL_STATUS.<label>.json \    # REQUIRED
  --run-label run1 \
  [--allow-real-governance]        # DEAD LAW: always refused (R-ALLOW-REAL)
  [--resume-with-recovery-check]   # T20 recovery path
  [--test-fault name[,name...]]    # sandbox-only fault injection
```

`--test-fault` names (all proven by tests; they can never reach the real
governance dir because R-GOV refuses it before any fault is evaluated):
`fail_release` (T11) · `fail_handoff_write` (T12) · `fail_publication` (T13)
· `fail_ledger_summary` (BUG2 sibling) · `force_twin_drift` (T15) ·
`post_acquire_foreign_row` (T9) · `mid_run_exception` (T10).

## 2. Exit codes

| code | meaning |
|------|---------|
| 0    | `EXECUTION_COMPLETE` — EVERY mandatory step measured done, incl. lock release and every finalization write |
| 2    | any `REFUSED_*` gate |
| 3    | any `FAILED_*` (compute, twin, publication, ledger summary, handoff write, lock release, final-status write, uncaught) |
| 75   | `NOT_RUN_RESOURCE_CONFLICT` — heavy lock held |

Never a silent pass: every non-success path exits non-zero with a
machine-readable `FINAL_STATUS.json`
`{status, exit_code, failed_step, failure_code, refusal_code, refusals[],
computation_complete, mandatory_steps{}, finalization_failures[],
failures[], lock{acquired, released_status}, observed_identity_count,
published_identity_count, handoff_written, sandbox_stamp}`.

**Success-token law (BUG2 class):** the string `EXECUTION_COMPLETE` appears
in a runner output (FINAL_STATUS / handoff.json / stdout verdict line) ONLY
when every mandatory step — including lock release, publication, ledger
summary, handoff write and final-status write — measured done. The runner
source obviously contains the token as the success constant; outputs never
claim it falsely.

## 3. Refusal gates (pre-computation, in evaluation order)

| code | trigger | test |
|------|---------|------|
| `REFUSED_BAD_ARGS` | missing required CLI args / unknown `--test-fault` | test_refusals |
| `REFUSED_ALLOW_REAL_GOVERNANCE_DISABLED` | `--allow-real-governance` — hard-compiled refusal in this PREP build | test_refusals::test_allow_real_governance_flag_is_dead_law |
| `REFUSED_REAL_GOVERNANCE_DIR` | `--governance-dir` (or registry/ledger/run-dir/final-status-out) resolves to `/Users/hoangminhlong/.my-quantitative-governance`, to the real `plans/CYCLE_REGISTRY.json` path, or into the real plans dir | test_isolation T16/T16b/T16c/T16d |
| `REFUSED_REGISTRY_MISMATCH` | governance registry unreadable/malformed, cycle-id absent, or declared-branch mismatch | T7/T7b |
| `REFUSED_NO_GO_ARTIFACT` | GO file absent | T2 |
| `REFUSED_GO_ARTIFACT_INVALID` | GO unparseable / wrong schema / missing key object | T5b-class |
| `REFUSED_GO_CYCLE_MISMATCH` | GO names a different cycle-id (checked BEFORE phrase) | T4 |
| `REFUSED_GO_NOT_OWNER_TYPED` | delegation markers (`delegat`, `on behalf of`, `thay mặt`, `proxy`) anywhere in the GO, or `typed_by != OWNER` / `typed_by_owner != true` (upstream 3a-c lineage) | test_refusals delegated-* |
| `REFUSED_GO_PHRASE_MISMATCH` | verbatim not BYTE-equal `GO <CYCLE-ID> SCORED EXECUTION` (no trim, no case-fold) | T3/T3b |
| `REFUSED_NO_AUTHORITY` | authority file absent | T5 |
| `REFUSED_AUTHORITY_INVALID` | authority content: wrong cycle-id or `typed_by_owner != true` | T5b |
| `REFUSED_CONTRACTS_INVALID` | symbol_contracts.json missing/malformed | static+suite |
| `REFUSED_INPUT_MANIFEST_INVALID` | manifest unreadable/wrong schema/cycle mismatch | suite |
| `REFUSED_MISSING_PRIOR_ARTIFACT` | a manifest `prior_artifacts[]` entry does not exist | T19 |
| `REFUSED_INPUT_DRIFT` | any re-hashed sha mismatch (fixtures, spec, cost, contracts, prior-artifact pins) or fixture unparseable/bar-count pin mismatch | T6/T6b |
| `REFUSED_SPEC_INVALID` | SPEC packet malformed (folds, identity ids, arms `long-if-bar-up`/`short-if-bar-down` only, tiers, stresses, fold-vs-bars ranges) | suite |
| `REFUSED_COST_MANIFEST_INVALID` | cost manifest unparseable | suite |
| `REFUSED_STALE_IN_PROGRESS` | ANY `IN_PROGRESS.json` under the runs root (cycle-scoped) without `--resume-with-recovery-check` + integrity pass | T20/T20c |
| `REFUSED_LOCK_DRIFT` | lock file free while RUNNING registry rows exist (bookkeeping drift; reclaim is never this runner's job) | law row |
| `NOT_RUN_RESOURCE_CONFLICT` | flock held (rc 75, zero denominator consumed) | T8 |

Every refusal: unique code, `FINAL_STATUS.json` written in the sandbox, a
`REFUSED` ledger row (`counts_observed=false`; skipped only if the existing
ledger fails integrity — the runner NEVER appends to a torn ledger and says
so on stderr), and `refusal_record.json` next to the FINAL_STATUS (or in the
run dir when the FINAL_STATUS parent itself is the isolation violation).

## 4. Canonical heavy-lock lifecycle

Self-contained under `<governance-dir>/lock_runtime/` (`heavy.lock` flock +
`heavy_registry.json` rows). The machine-wide canonical lock is NEVER
touched (the whole point of the sandbox-governance law).

1. pre-check: flock held (by anyone) => `NOT_RUN_RESOURCE_CONFLICT`; free
   flock + RUNNING row => `REFUSED_LOCK_DRIFT`.
2. acquire: `flock(LOCK_EX|LOCK_NB)` + append our RUNNING row
   `{cycle_id, pid, role=EXEC, nonce}`.
3. POST-ACQUIRE RECHECK (TOCTOU closure): re-read registry — any foreign
   RUNNING row => abort `FAILED_POST_ACQUIRE_FOREIGN_ROW`; a second
   descriptor able to take the flock => abort
   `FAILED_POST_ACQUIRE_LOST_FLOCK` (T9 proves the foreign-row abort with
   lock released + probe row preserved as evidence).
4. release is ALWAYS attempted — success, refusal-free completion, fault,
   or exception. Steps: remove our row, then `flock(LOCK_UN)`.
   **BUG1-class fix:** if release itself raises (or the fault fires), the
   release is NOT counted as done: `lock_released_status = "RELEASE_RAISED"`,
   a finalization failure is recorded, the terminal status is computed AFTER
   release from measured evidence, and the run exits 3 (`FAILED_LOCK_RELEASE`).
   Evidence is preserved (a raised release leaves the RUNNING row in place;
   the runner never force-unlocks, kills or deletes). T11 proves: non-zero
   exit, `RELEASE_RAISED`, no `EXECUTION_COMPLETE` anywhere, no handoff
   artifact — despite `computation_complete: true`.

Terminal-handoff ordering: `handoff.json` is written only AFTER release
measured `RELEASED` — so a release failure can never coexist with a
handoff claiming completion. `IN_PROGRESS.json` markers are removed BEFORE
the handoff write (a failed cleanup denies completion; the next run then
demands recovery).

## 5. Deterministic engine (accounting under test, no strategy intelligence)

Inputs: frozen input manifest (fixture CSV paths + expected sha256 +
bars_expected pins + spec/cost/contracts sha pins + optional
prior_artifacts), frozen SPEC packet (folds by bar index; identities with
`identity_id, symbol, arm, hold_bars, cost_tier, stress`), frozen cost
manifest (`fee_per_side_usd_by_tier`, `spread_ticks_by_stress`,
`slip_ticks_by_stress` at x1.0/x1.5/x2.0), symbol contracts.

Per identity, per fold:
- arms: `long-if-bar-up` (close>open on signal bar) / `short-if-bar-down`
  (close<open), direction +1/-1;
- fills at NEXT-bar open (entry `i+1`, exit `i+1+hold_bars`; conservative
  fill law), each fill rounded to the ERA tick grid;
- **era law:** one trade carries one era — the LAST era row whose
  `effective_from <= entry-bar date` (inclusive); a trade straddling an era
  boundary uses its entry era for both fills, grid rounding AND cost
  conversion;
- gross PnL: `direction * (exit - entry) * (tick_value_usd / tick_size)`
  of that era — equivalently `direction * (exit - entry) * multiplier`
  (the invariant `tick_value/tick_size == multiplier` holds for every era
  and is statically asserted);
- cost per side: `fee(tier) + (spread_ticks(stress) + slip_ticks(stress))
  * tick_value_usd(era)`; applied per side (entry + exit);
- money rounded to 6dp; no wall-clock fields anywhere (byte-identical
  outputs given identical inputs).

**6J quote-direction law:** CME 6J is quoted USD per 1 JPY (~0.0067), not
JPY-per-USD (~150). `long_base_sign = +1`: a long profits when the quoted
number RISES. The runner applies the same formula to every symbol; T18
proves the sign convention on synthetic up-moves AND that the inverted
(JPY-per-USD) misread would flip every sign.

**6A era law:** the only two-era contract: era-1 `1900-01-01`,
0.0001 / $10.00 per tick; era-2 from `2020-11-23`, 0.00005 / $5.00 per tick
(D8-era-aware cost law carrier). T17 proves era-1 vs era-2 COST rows differ
correctly around the boundary while the per-price-unit gross factor stays
100,000. All numbers, and the boundary date itself, are
`VERIFICATION: PLACEHOLDER-PENDING-PER-SYMBOL-LANE` — data to the runner,
never verified by it.

## 6. Ledger (append-only JSONL)

Row envelope: `{"schema": "futures_5sym_prescored/ledger_row@1", "seq",
"row_type", "counts_observed", "identity_id", "payload"}` — reopened and
appended, NEVER truncated; `seq = max(existing)+1`.

| row_type | counts_observed | meaning |
|----------|-----------------|---------|
| `REFUSED` | false | run-level refusal |
| `TRIAL` | **true** | one per identity (per-fold sub-records + totals + provenance shas inside) |
| `DUPLICATE_RETRY` | false | identity_id already observed => skipped, NOT recomputed (T14) |
| `FOLD` | false | per-fold aggregate |
| `ABORT` | false | post-acquire abort / failure evidence |
| `PUBLICATION` | false | published evidence |

Observed vs published are SEPARATE counters: observed = distinct TRIAL
identity ids (already true at append time); publication writes
`published_summary.json` (published == observed on success). **Publication
failure (T13):** observed rows stand in the ledger, `published_summary.json`
is withheld, `PUBLICATION_QUARANTINE.json` is written, run exits 3
(`FAILED_PUBLICATION`) — the denominator is never lost and never
double-counted.

## 7. Reproduction twin

A second, independent engine pass over the SAME frozen inputs (faults never
injected in the twin) is compared STRUCTURALLY to pass 1 (per-identity
records + fold aggregates; typed diff walk, capped sample). Any diff =>
`FAILED_TWIN_MISMATCH`, exit 3, `reconciliation_report.json` written with
`match:false` and the diff sample (T15). On success the report is written
with `match:true` and the handoff pins the artifact shas.

## 8. Recovery rules (stale IN_PROGRESS marker)

`IN_PROGRESS.json` is written after lock acquisition, removed before the
terminal handoff. Markers are CYCLE-scoped: ANY marker under the runs root
blocks ANY new run => `REFUSED_STALE_IN_PROGRESS` (T20 step 2), unless
`--resume-with-recovery-check` AND integrity passes: every marker parseable
+ every existing ledger line complete JSON (no torn write). The recovery
run then resumes with identity-ID dedupe (no double count) and, on success,
adopts (removes) every cycle marker (T20 step 3). A torn ledger line fails
integrity even WITH the flag (T20c); the runner also refuses to APPEND to a
ledger failing integrity (refusal rows included) and says so on stderr.

## 9. BUG1/BUG2-class fixes and their proofs

| upstream defect (c17ab2bf FAIL record) | v2 fix | proof |
|---|---|---|
| BUG1: `handle.release()` raising => exit 0 + EXECUTION_COMPLETE + `lock_released_status FINISHED` (status written outside the try merely because release was CALLED) | release ALWAYS attempted; raise => `RELEASE_RAISED` + finalization failure; terminal status computed AFTER release from measured evidence; evidence preserved, never force-unlocked | T11 (`--test-fault fail_release`): exit 3, `FAILED_LOCK_RELEASE`, `RELEASE_RAISED`, no success token anywhere, no handoff, RUNNING row preserved |
| BUG2: terminal handoff write raising => exit 0 + EXECUTION_COMPLETE without the terminal artifact | handoff guarded; failure => `FAILED_HANDOFF_WRITE` exit 3; handoff written only after release measured RELEASED; success token only with every mandatory step done | T12 (`--test-fault fail_handoff_write`): exit 3, no handoff, no success token, publication stands |
| same class: ledger-summary failure path (error recorded, exit unchanged) | ledger summary guarded; failure => `FAILED_LEDGER_SUMMARY` exit 3 | `fail_ledger_summary` test |
| (adjacent) publication failure | observed kept, published withheld, quarantine marker, exit 3 | T13 |

Developed-and-fixed during THIS build (see FIX_LOG.md): the
mandatory-step chicken-and-egg (terminal_state demanded not-yet-possible
steps), the refusal_record isolation leak into the real governance dir
(caught by the suite's own T16 snapshot guard), and the per-run-dir marker
bypass (now cycle-scoped).

## 10. Isolation summary (T16)

- every lock, ledger, registry, GO, authority, fixture and output path in
  the suite lives under pytest tmp dirs;
- `--governance-dir` pointing at the real governance dir / real registry /
  real plans dir refuses BEFORE any read or write there (T16 direct,
  T16b, T16c);
- a `--final-status-out` under the real dir refuses and its evidence falls
  back to the sandbox run dir; the real dir is never written by ANY code
  path including refusal recording (T16d);
- a session-scoped snapshot (content sha + size + mtime for all real
  governance files except the DISCLOSED-EXCLUDED canonical `heavy_runtime`
  contents, which belong to other cycles' lock lifecycles; plus the real
  `plans/CYCLE_REGISTRY.json` and the real ES `GO_RECORDED.json`) asserts
  the real surfaces byte-identical before vs after the ENTIRE suite.
