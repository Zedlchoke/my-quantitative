# CANONICAL_INTEGRATION — production lock/registry posture for a future
# registered FUTURES-5SYM-PRESCORED cycle (integration contract; PREP-only
# round — nothing in this document was executed against the real surfaces
# beyond READ-ONLY inspection).

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave 3, lane **FREEZE-WIRING**,
  2026-10-05.
- Sources read (read-only): `/Users/hoangminhlong/my-quantitative/research/researchctl.py`
  (`cmd_cycle_register`, `cmd_cycle_update`, `cmd_cycle_reconcile`,
  `cmd_locks_inspect`), `/Users/hoangminhlong/my-quantitative/research/governance/heavy_lock.py`,
  the real runtime listing `~/.my-quantitative-governance/heavy_runtime/`, and
  one `researchctl.py locks inspect` run (twice — lane start and lane end).

## 0. THE ONE-LINE POSTURE (binding statement)

**The sandbox flock used by this round (`exec/scored_runner_v2.py`'s
`HeavyLock` under `<sandbox gov>/lock_runtime/heavy.lock`) is NOT evidence of
canonical machine-wide lock integration.** It proves the runner's INTERNAL
lock lifecycle (TOCTOU recheck, release-always, drift refusal) on sandbox
files only. The canonical lock is `governance.heavy_lock` on
`~/.my-quantitative-governance/heavy_runtime/` — a different implementation,
different file names, different registry semantics — and it was never
acquired by this lane (suite is light; every invocation < 2 s).

## 1. The canonical surfaces (measured, read-only)

```
/Users/hoangminhlong/.my-quantitative-governance/heavy_runtime/
  heavy_worker.lock            # 0 bytes; exclusive fcntl.flock target
  heavy_worker.registry.json   # SINGLE RUNNING row (absent when free)
  heavy_worker.history.jsonl   # append-only archive of released rows
  scheduler_jobs.json
```
Measured listing 2026-10-05: `heavy_worker.history.jsonl` (503,815 B),
`heavy_worker.lock` (0 B), `scheduler_jobs.json`; NO
`heavy_worker.registry.json` present (the registry row exists only while a
worker holds the lock — it is unlinked on clean release; the last history row
shows a FINISHED `FX-BACKFILL` row of `FUTURES-DEEPRESEARCH-V2-20261003` with
`process_start_token: "ps:..."`, `command_digest`, `expected_artifacts`,
`started_at/last_heartbeat/released_at`).

`researchctl.py locks inspect` (run twice this lane, both):
```json
{"verdict": "FREE_PROVEN",
 "reason": "no registry row and the lock file is not flocked",
 "evidence": {"registry_path": ".../heavy_runtime/heavy_worker.registry.json",
              "lock_path": ".../heavy_runtime/heavy_worker.lock",
              "flock_state": "free", ...}}
```
Tri-state law: `HELD_PROVEN` (pid alive + process-start token match + flock
held) / `FREE_PROVEN` (no registry row AND free flock) /
`CONTROL_STATE_DRIFT` (anything else — ambiguous NEVER becomes FREE; read-only,
never reclaimed by inspect).

## 2. The registry (cycle authority)

`research/researchctl.py` resolves cycle ids ONLY through
`/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json`:
- `cycle register --cycle <ID> --plan <plans/PLAN_*.md> --branch <branch>
  [--head <sha>] [--lifecycle ...]` — atomic CAS write
  (`cycle_registry.register_cycle(..., prev_sha=sha256(REGISTRY_PATH))`) +
  append-only journal event + projection regeneration. Registration itself is
  an OWNER action; lanes never register (P-law).
- `cycle update --cycle <ID> --head <sha>|--lifecycle <S>|--phase <P>` —
  atomic measured-head/lifecycle updates (TERMINAL absorbing; closing kills
  the GO phrase per P-8), same CAS + journal path.
- The runner's preflight (`scored_runner_v2.py` step 2) consumes a registry
  JSON with `cycles[]` and refuses `REFUSED_REGISTRY_MISMATCH` when the
  cycle-id is absent or the declared branch mismatches the worktree. For a
  registered cycle the runner reads the REAL registry shape; this round's
  sandbox runs used a sandbox registry file with the same reader, which is
  exactly the "same-shape, non-canonical" caveat recorded below.

## 3. Exactly how the production runner invocation will use the canonical lock

Programmatic path (the only lawful one for a scored run; the CLI `locks`
subcommand is inspect-only by design):

```python
from governance import heavy_lock                       # research/governance

# 0. pre-check (refuse early, before compiling anything):
report = heavy_lock.inspect()
# must be heavy_lock.VERDICT_FREE_PROVEN; HELD_PROVEN -> NOT_RUN_RESOURCE_
# CONFLICT (zero denominator consumed); CONTROL_STATE_DRIFT -> fail closed,
# hand to the owner (never reclaim from the worker).

# 1. acquire (runtime dir is derived internally; callers CANNOT select it):
handle = heavy_lock.acquire(
    cycle_id="FUTURES-5SYM-PRESCORED-<date>",
    role="EXEC",                                        # registry row role
    worktree="/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep",
    command=[<python>, ".../exec/scored_runner_v2.py", <full argv>],
    expected_artifacts=[<ledger path>, <FINAL_STATUS path>, <published_summary path>])
# LockBusyError          -> NOT_RUN_RESOURCE_CONFLICT (exit-75 posture)
# HeavyLockError(CONTROL_STATE_DRIFT) -> fail closed, row preserved

# 2. POST-ACQUIRE RECHECK (TOCTOU closure) — MUST compare, on a fresh read:
recheck = heavy_lock.inspect()
#   verdict == HELD_PROVEN, AND the registry row matches OURS on EVERY field:
#     row["cycle_id"] == our cycle_id
#     row["role"]     == "EXEC"
#     row["pid"]      == os.getpid()
#     row["process_start_token"] == heavy_lock.process_start_token(os.getpid())
#   any OTHER status=="RUNNING" row  -> abort (FAILED_POST_ACQUIRE_FOREIGN_ROW
#   posture; evidence preserved, never deleted)
#   a second descriptor able to take the flock -> FAILED_POST_ACQUIRE_LOST_FLOCK
#   posture (our hold was lost)

# 3. run the wiring inside the lock, per identity / per symbol:
#    wiring.spec_compiler.compile_and_run(...) drives the UNMODIFIED
#    exec/scored_runner_v2.py (see freeze_wiring/wiring/spec_compiler.py);
#    the runner's OWN sandbox lock remains as defense-in-depth but is not
#    the machine-wide authority.

# 4. release — ALWAYS attempted (success, failure, or exception):
handle.release(status="FINISHED", note="<run label>")
# a raised release is a FINALIZATION FAILURE (BUG1-class law): the run is
# FAILED non-zero even if computation completed; never force-unlock, never
# kill, never delete rows.

# 5. record the measured outcome:
#   researchctl.py cycle update --cycle <ID> --head <measured sha> \
#       --lifecycle <next> --reason "..."
# (CAS on sha256(CYCLE_REGISTRY.json); journal + projection by researchctl)
```

Command-sequence summary for the future registered cycle:
1. `research/researchctl.py locks inspect` → must print `FREE_PROVEN`
   (recorded in the lane log; a HELD/DRIFT verdict ⇒ `NOT_RUN_RESOURCE_CONFLICT`).
2. `heavy_lock.acquire(cycle_id, role="EXEC", worktree, command, expected_artifacts)`.
3. post-acquire recheck per §3 step 2 (foreign-row + lost-flock aborts).
4. drive the unmodified runner through `freeze_wiring/wiring/spec_compiler.py`
   on the frozen bundle + compiled fixtures (owner GO/authority only).
5. `handle.release(...)` always attempted; failure ⇒ FAILED_LOCK_RELEASE posture.
6. `research/researchctl.py cycle update --head/--lifecycle` (CAS + journal).
7. `research/researchctl.py locks inspect` again → `FREE_PROVEN` recorded.

## 4. Registry-file format the post-acquire recheck must compare

Sandbox mirror used by this round (same reader, NON-canonical file):
`{"schema": "futures_5sym_prescored/heavy_registry@1", "rows": [{cycle_id,
pid, role, status, nonce}]}` (exec/scored_runner_v2.py HeavyLock).
Canonical: `heavy_worker.registry.json` — a SINGLE owner row with
`cycle_id, pid, role, status("RUNNING"), command, command_digest,
expected_artifacts, worktree, started_at, last_heartbeat,
process_start_token("ps:...")`. The recheck must compare the canonical fields
(cycle_id/role/pid/process_start_token + no foreign RUNNING row), NOT the
sandbox nonce shape.

## 5. NOT_RUN this round (explicit)

| item | status |
|---|---|
| real `heavy_lock.acquire()` on `~/.my-quantitative-governance` | NOT_RUN (suite light; never needed; taking it would violate the one-heavy-job discipline for no cause) |
| real `cycle register` / `cycle update` writes to `plans/CYCLE_REGISTRY.json` | NOT_RUN (owner-only authority; read-only inspection only) |
| real GO artifact / real authority pack consumption | NOT_RUN (owner-typed GO does not exist; fake authority only inside pytest tmp dirs) |
| real freeze manifests (cache_v3-class inputs) | NOT_RUN (GATE-0 authority unsigned: D9 / PB2 / PB3+D8 / 6J ceiling) |
| any scored outcome / PnL statistic | NOT_RUN (outcome-blind PREP law; sandbox runs are SYNTHETIC-SANDBOX only) |

The `test_isolation.py` snapshot (real governance + real registry
byte-identical before/after the suite, `heavy_runtime` contents excluded as
other cycles' live lock lifecycle) is the enforcement of "read-only
inspection" claimed here.

## 6. Sandbox-vs-canonical distinction (restated for the handoff)

- Sandbox flock (`<sandbox gov>/lock_runtime/heavy.lock` +
  `heavy_registry.json`): runner-internal lifecycle proof — concurrency
  semantics, release-failure accounting, drift refusal. PROVEN by tests.
- Canonical machine-wide lock (`governance.heavy_lock` + `heavy_runtime/`):
  NOT exercised beyond `inspect()` this round. Any claim that this lane
  "integrated the machine-wide lock" would be FALSE; what exists is the
  documented invocation contract above plus the compile/runner machinery
  that will sit INSIDE the canonical critical section.
