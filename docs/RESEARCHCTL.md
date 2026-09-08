# researchctl — operator entrypoint (SHV1 §7.1)

One documented command surface for cycle control. Cycle IDs resolve ONLY
through the canonical registry (`plans/CYCLE_REGISTRY.json`, schema
`cycle_registry@1`) — never from worktree existence.

```bash
PY=.venv/bin/python

$PY research/researchctl.py cycle list            # registry table + drift warnings
$PY research/researchctl.py cycle doctor          # read-only consistency diagnostics
$PY research/researchctl.py cycle doctor --json   # machine-readable findings
$PY research/researchctl.py cycle pause <CYCLE> --reason "..." [--hard-stop-reason ...]
$PY research/researchctl.py cycle resume <CYCLE>              # DRY-RUN checklist (default)
$PY research/researchctl.py cycle resume <CYCLE> --execute-live
$PY research/researchctl.py job list | job cancel <id>        # H3 scheduler (if present)
$PY research/researchctl.py locks inspect                     # machine-wide heavy lock
$PY research/researchctl.py program counters                  # ledger denominators (P-9)
```

Full §7.6 diagnostics (10 detection classes incl. live-worker vs state,
dead lock owners, frozen-artifact hash drift, monitoring purity):

```bash
$PY -m governance.doctor            # from research/ on sys.path
$PY research/governance/doctor.py   # direct
```

## Semantics that bind operators

- **Writes are transactional only** (`governance/atomic_io.py`): schema
  validation → sibling tmp → fsync → atomic rename → read-back → append-only
  event journal (`plans/CYCLE_REGISTRY.events.jsonl`). Parallel writers fail
  closed (flock sidecar + CAS on previous content sha256). Malformed,
  truncated or stale state is `CONTROL_STATE_DRIFT` — refuse, never repair.
- **Legacy records are never rewritten.** The three asset cycle state files
  and `plans/ACTIVE_CYCLES.json` are read-only; adapters normalize in memory
  and surface drift as warnings (the two H0-recorded head drifts are examples).
- **`cycle resume` is dry-run by default** and prints the SHV1 §10 checklist.
  `--execute-live` flips the registry lifecycle only — scored execution still
  requires the cycle's own gates plus a **fresh owner GO** (P-8: no GO
  carries across the maintenance pause).
- **TERMINAL is absorbing.** A closed cycle never re-opens through the
  registry; its GO phrase is DEAD (extinguished unconsumed).
- **Monitoring purity (§7.5):** the dashboard collector never writes a tracked
  file; refresh snapshots go to the gitignored `dashboard/` runtime dir.
  Repeated refreshes must leave `git status --porcelain=v1` unchanged (G5).
