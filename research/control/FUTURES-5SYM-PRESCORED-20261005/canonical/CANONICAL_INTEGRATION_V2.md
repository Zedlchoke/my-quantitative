# CANONICAL_INTEGRATION_V2 — the canonical-integration layer AS CODE

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave 4, lane **CANONICAL-CODE**,
  2026-10-06, worktree `/Users/hoangminhlong/my-quantitative/.worktrees/
  futures-5sym-prescored/prep`, base `f1f69c8e18e6d5ba4ab801632e22428251950131`.
- Supersedes the documentation-only posture of
  `freeze_wiring/CANONICAL_INTEGRATION.md` (wave 3). ERRATUM 2 narrowed that
  wave's claim: the .md was a documented sequence, not implemented+tested
  code. This round CLOSES that gap at the wrapper level; the real-surface
  executions remain NOT_RUN (fail-closed, see matrix).
- Code: `canonical/production_exec.py` (wrapper), `canonical/realstate.py`
  (read-only real-state checks), `canonical/test_production_exec.py`
  (T1–T14). Everything imports the repo's canonical governance modules
  (`research/governance/heavy_lock.py`, `cycle_registry.py`, `atomic_io.py`)
  from THIS worktree — the same modules `researchctl.py` uses. No flock,
  CAS, journal or registry semantics are reimplemented anywhere.

## 1. Implemented-vs-documented matrix

| capability | wave-3 (CANONICAL_INTEGRATION.md) | wave-4 (this lane) | evidence |
|---|---|---|---|
| authority read: registry row parse (real schema `cycle_registry@1` via strict loader) | documented | **CODE + tested** | `read_authority()`; T2 |
| authority checks: HEAD (incl. unmeasured placeholder) / BRANCH / lifecycle executability | documented | **CODE + tested** | T3, T4, T5 |
| GO verification: real `auth/GO_RECORDED.json` (`dev1_go_auth@1`), cycle-before-phrase, byte-exact phrase, `two_key` completeness | documented | **CODE + tested** | T6 |
| heavy-lock acquire THROUGH `governance.heavy_lock` (no reimplemented flock) | documented | **CODE + tested (sandbox-isolated through the same code)** | `acquire_canonical_lock()`; T1, T7 |
| pre-acquire inspect tri-state gate (FREE / HELD→NOT_RUN_RESOURCE_CONFLICT / DRIFT→fail-closed) | documented | **CODE + tested** | T7; T8 (drift) |
| post-acquire TOCTOU recheck: fresh inspect HELD_PROVEN + every registry field ours (cycle/role/pid/process_start_token); drift ⇒ evidence preserved, flock returned | documented | **CODE + tested** | `GuardedCanonicalLock.recheck()`; T8 (`LOCK_POSTACQUIRE_DRIFT`) |
| guarded execution: exception ⇒ release ALWAYS attempted, ledger untouched, FAILED non-zero | documented | **CODE + tested** | `execute_cycle_step()`; T9 |
| BUG1 class: raised release ⇒ FAILED non-zero even when computation completed | documented | **CODE + tested** | T10 |
| BUG2 class: terminal handoff written INSIDE the guarded path; raised handoff ⇒ FAILED, no success token | documented | **CODE + tested** | T11 |
| FINAL_STATUS.json machine-readable on EVERY terminal path | documented | **CODE + tested** | T1, T9–T12 |
| registry CAS update THROUGH `governance.cycle_registry.update_cycle` (CAS + journal + projection) | documented | **CODE + tested (sandbox)** | `registry_cas_update()`; T1, T13 |
| real-mode refusal: registry write / lock acquire against real surfaces refused BEFORE any real write (hard-compiled `PREP_BUILD`, the runner's R-GOV/`--allow-real-governance` law) | documented | **CODE + tested** | T12 |
| read-only real-state checks (registry parse + counts + absence, locks-inspect verdict parse, governance listing digest) | partial (manual) | **CODE + tested against the REAL state** | `realstate.py`; T14 |
| real `heavy_lock.acquire()` on `~/.my-quantitative-governance/heavy_runtime/` | NOT_RUN | **NOT_RUN (owner authorization I)** — refused by `PREP_BUILD` before any real lock touch | T12 proves the refusal fires |
| real `cycle register` / `cycle update` writes to `plans/CYCLE_REGISTRY.json` | NOT_RUN | **NOT_RUN (owner authorization I)** — refused (`REGISTRY_WRITE_REAL_REFUSED`) before any read-modify-write | T12 |
| real GO artifact consumption at a real cycle gate | NOT_RUN | **NOT_RUN (owner authorization II)** — no typed owner GO exists for this round; fake GOs only inside pytest tmp dirs | T6 uses the real FORMAT, sandbox files |
| scored outcome / PnL statistic | NOT_RUN | NOT_RUN (outcome-blind PREP law, unchanged) | — |

**Owner authorizations that unlock the NOT_RUN parts:**

- **I — real-governance execution authorization**: an explicit owner
  instruction naming this wrapper (`canonical/production_exec.py`) that (a)
  flips the hard-compiled `PREP_BUILD` constant, and (b) is backed by a
  REGISTERED cycle row in `plans/CYCLE_REGISTRY.json` (lifecycle
  ACTIVE_HEAVY, measured HEAD, branch match). This unlocks real
  `heavy_lock.acquire()` and real CAS registry updates.
- **II — typed owner GO**: a `GO_RECORDED.json` recorded at the cycle's OWN
  gate (P-8), schema `dev1_go_auth@1`, byte-exact phrase
  `GO <CYCLE-ID> SCORED EXECUTION`, complete `two_key`
  (`key_1_a7` + `key_2_owner_go`). This unlocks `read_authority()` passing
  against the real `research/control/<CYCLE>/auth/` artifact.

## 2. The exact production sequence (function names)

```python
from canonical import production_exec as pe          # this wrapper

outcome = pe.run_protected_step(                     # = CANONICAL_INTEGRATION §3 as one call
    registry_path=<plans/CYCLE_REGISTRY.json>,       # refused if real (PREP_BUILD)
    cycle_id=<registered cycle>, role="EXEC",
    worktree=<integration worktree>,
    command=[<python>, <runner argv ...>],
    expected_artifacts=[<ledger>, <FINAL_STATUS>, <summary>],
    step_callable=<the actual cycle step>,
    final_status_path=..., handoff_path=...,
    target_root=None)                                # None = real mode => REFUSED today
```

`run_protected_step` executes, in order:

1. `read_authority()` — strict-loads the registry (`cycle_registry.load`),
   resolves the row, compares MEASURED head/branch, enforces executable
   lifecycle, verifies the GO artifact (cycle → phrase → two_key).
   Any gap ⇒ `REFUSED` (exit 2) before the lock.
2. `acquire_canonical_lock()` — pre-inspect (`heavy_lock.inspect()`;
   DRIFT ⇒ fail-closed; HELD ⇒ `heavy_lock.acquire` raises
   `LockBusyError` ⇒ `NOT_RUN_RESOURCE_CONFLICT`, exit 75), then the
   canonical `heavy_lock.acquire()`, then `recheck()` (fresh
   HELD_PROVEN + every field ours; drift ⇒ `abandon_preserving_row()` +
   `LOCK_POSTACQUIRE_DRIFT`, row bytes preserved).
3. `execute_cycle_step()` — step callable inside the lock;
   exception ⇒ release ALWAYS attempted + ledger-untouched proof;
   handoff INSIDE the guarded path; raised release ⇒ FAILED (BUG1);
   raised handoff ⇒ FAILED, no success token (BUG2); FINAL_STATUS.json
   machine-readable always.
4. `registry_cas_update()` — post-step measured update through
   `cycle_registry.update_cycle` (CAS on prev sha + journal + projection);
   CAS conflict ⇒ `CAS_MISMATCH`, no partial write (T13).
5. Final `locks inspect` ⇒ `FREE_PROVEN` recorded (suite bookends below).

## 3. Sandbox-vs-real law (binding statement)

The sandbox tests drive the IDENTICAL wrapper and canonical governance code;
the only difference is the runtime directory (`heavy_lock.RUNTIME_DIRNAME`
scoped redirection via `F5SYM_GOVERNANCE_DIR` / `target_root=`, the ONE
sanctioned override — callers still cannot pick arbitrary lock semantics).
**This is evidence of integration correctness of the WRAPPER — the refusal
paths, lock lifecycle, CAS and bug-class laws. Real-lock integration and
real registry writes remain NOT_RUN until owner authorization I (+II for the
GO) lands; any claim that this lane "exercised the real machine-wide lock"
or "wrote the real registry" would be FALSE.**

## 4. Suite evidence (measured 2026-10-06)

- `pytest research/control/FUTURES-5SYM-PRESCORED-20261005/canonical/
  test_production_exec.py` ⇒ **14 passed**, exit 0 (~0.6 s; suite light).
- Locks-inspect bookends: start `FREE_PROVEN`, end `FREE_PROVEN`.
- Suite-level isolation proof: sha256 snapshot of the real registry,
  projection, and all four `heavy_runtime` files before/after the suite ⇒
  **byte-identical** (the `heavy_worker.registry.json` member recorded ABSENT
  on both sides — no row while the lock is free).
- T14 additionally runs the real-state checks (parse + 100 unique cycle ids +
  FUTURES-5SYM-PRESCORED-20261005 absent + real locks-inspect verdict parse)
  with its own before/after snapshot ⇒ identical.

## 5. NOT_RUN (explicit, unchanged from wave 3 where applicable)

| item | status |
|---|---|
| real `heavy_lock.acquire()` on `~/.my-quantitative-governance` | NOT_RUN (owner authorization I; `PREP_BUILD` refuses first — proven by T12) |
| real `cycle register` / `cycle update` on `plans/CYCLE_REGISTRY.json` | NOT_RUN (owner authorization I; `REGISTRY_WRITE_REAL_REFUSED` — proven by T12) |
| real GO artifact consumption | NOT_RUN (owner authorization II) |
| any scored outcome / PnL statistic | NOT_RUN (outcome-blind PREP law) |
