# SYSTEM-HARDENING-V1 — CLOSEOUT REPORT (plan §12)

Cycle: `SYSTEM-HARDENING-V1` · Controller: A1_SHV1_CONTROLLER ·
A7 verdict: **`SYSTEM_HARDENING_V1_PASS`** (fresh-context, commit `8b2a5ca` on
`orca/system-hardening-v1-audit`) · Status: **CLOSED — resume recommended,
owner keys required per cycle (P-8)**.

## 1. SHA chain and tree cleanliness

```text
main:            54d349a (Lead closeout sync) -> 16555f2 OWNER_PLAN_SHA
                 -> 89fbbdf (H0 baseline projection) -> cb8954f (H0 packets)
                 -> eda97ab (H0 correction)            == SHV1_WAVE_SHA
integration:     eda97ab -> 979b088 (H1 freeze) -> 5250e8b (gate correction)
                 -> e34a24a (freeze amendment) -> a611465 (pick A2 53d76e9)
                 -> 1e71194 (pick A3 e514140) -> 8ac27b6 (pick A4 57033ad)
                 -> ff35283 (H5 report) -> 88da553 (H6 registry reconciliation)
                 -> 8ddfefe (resume packets) -> <this commit> (closeout)
lanes:           router 53d76e9 · scheduler e514140 · dashboard 57033ad ·
                 audit 8b2a5ca (A7 verdict artifacts)
cycle branches:  V17 2b176e3 -> 41de5c9 (pause) · V8 5b1c23c -> 94e78f6 (pause)
                 · V12 5a9b42d (TERMINAL, untouched by SHV1)
trees:           main + all 5 SHV1 lanes + 3 cycle worktrees CLEAN
                 (porcelain empty; owner .zcode/ untracked space exempt)
```

## 2. File ownership and merge order

Frozen at H1 (`research/governance/shv1/H1_CONTRACT_FREEZE.json`, one
pre-lane amendment disclosed `e34a24a`). **Merge order for the owner (single
squash-merge or fast-forward of `orca/system-hardening-v1-integration` to
main; lanes merge ONLY through integration, never directly):**
A2 `53d76e9` → A3 `e514140` → A4 `57033ad` → A1 reconciliation
(`ff35283`, `88da553`, `8ddfefe`, closeout). A7's audit lane stays a side
evidence branch (or may be merged last; artifacts are additive).

Ownership: A2 router/schema/CLI/registry (`research/governance/{cycle_registry,
atomic_io,legacy_adapters}.py`, `research/researchctl.py`,
`plans/CYCLE_REGISTRY.json` + `.events.jsonl`); A3 scheduler
(`research/governance/{scheduler,retry_classifier}.py`); A4 dashboard/doctor
(`dashboard_collect.py` read-only fix, `doctor.py`, `docs/RESEARCHCTL.md`,
dashboard tests); A1 SHV1 phase artifacts; A7 audit artifacts only.

## 3. Gates — commands, exits, counts, logs

| Gate | Command (abridged) | Result | Evidence |
|---|---|---|---|
| G0 baseline | `python3 .runtime/shv1_h0_gate.py` | **PASS, 14/14, exit 0** | `.runtime/shv1_h0_gate.log`; `plans/system_hardening_v1/` packets |
| G1 router truth | `pytest tests/test_cycle_registry.py test_legacy_adapters.py` + `researchctl cycle list/doctor` | **PASS — 22/22** | registry resolves V17/V8 paused, V12 TERMINAL; closed never active |
| G2 atomic state | `pytest tests/test_atomic_io.py` (parallel-writer flock, truncated, malformed, CAS) | **PASS — fail closed everywhere** | `tests/test_atomic_io.py`; A7 re-ran negatives independently |
| G3 retry safety | `pytest tests/test_scheduler.py::test_fromisoformat…` | **PASS — fixture executes once, CODE_OR_SCHEMA_ERROR, zero backoff** | INC_V12_4 fixture; 12/12 scheduler tests |
| G4 resource safety | admission/heavy-lock tests + alone-condition measured | **PASS — NOT_RUN_RESOURCE_CONFLICT, no attempt consumed** | `tests/test_scheduler.py`; ps+lock sweep pre-suite |
| G5 monitoring purity | `pytest tests/test_dashboard_purity.py` + A7's own collector run | **PASS — git status identical, projection byte-frozen** | `18 passed/1 skipped` (skip = no host lock registry: truthful NOT_RUN) |
| G6 legacy compat | adapters byte-hash assertions + existing suites | **PASS — zero SHV1 commits touch `research/control/**` (eda97ab..ff35283 empty)** | A7-verified; 1012-suite green inside |
| G7 regression | targeted after every pick + `git diff --check` + full suite ALONE | **PASS — 1012 passed/1 skipped/6 errors, errors PROVEN PRE-EXISTING AT BASE** (identical rerun on pristine audit lane `eda97ab`: same 6 names, `TypeError` `scripts/v9_universe_audit.py:567`) | `.runtime/shv1_full_suite_integration.log`; `H5_INTEGRATION_REPORT.json` |
| G8 independent audit | A7 fresh-context, 21 commands recomputed | **PASS — 0 HIGH/CRITICAL, 4 LOW** | `8b2a5ca`, `A7_AUDIT_VERDICT.json` |

H1 gate: `h1_reproduce_inventory.py` exit 0 (56 worktrees / 324 branches /
hashes / heads). H6 verdict: `SYSTEM_HARDENING_V1_PASS`.

## 4. Negative-test results (atomicity / retry / lock / dashboard)

- **Atomicity**: parallel writer while sidecar flock held → `WriteLockBusy`,
  bytes untouched; truncated + malformed registry → `CONTROL_STATE_DRIFT`, no
  self-repair; CAS mismatch → refuse with byte-identical file (A7 reproduced
  all three from scratch).
- **Retry**: fromisoformat TypeError → executes exactly once, no retry, no
  backoff (the H3 gate fixture); transient → bounded 30/60/120s frozen
  schedule then FAILED; rate-limited → WAITING with provider `retry_after`,
  attempt not consumed; **unrecognized failures fail closed to
  CODE_OR_SCHEMA_ERROR**.
- **Lock**: admission with held lock → `WAITING /
  NOT_RUN_RESOURCE_CONFLICT`; stale RUNNING rows reclaimed only on
  PROVEN pid-dead (round-2 discipline); journal survives controller restart.
- **Dashboard**: repeated `write_outputs` (launch + refresh signatures) →
  `git status --porcelain=v1` unchanged, `plans/ACTIVE_CYCLES.json`
  byte-frozen, snapshot only into gitignored `dashboard/`; doctor read-only
  (mtime-asserted).

## 5. Scientific freeze — pre/post hashes (all MATCH, drift NONE)

| Asset freeze | sha256 | State |
|---|---|---|
| V17 contract freeze v5 | `1ca4fa3d45342e64…` | MATCH pre-pause / H0 / H5 / A7 / resume |
| V17 extractor + reconcile self-pins | `9ea77d21…` / `26737e56…` | MATCH |
| V16 daily panels BTC/ETH (V17 anchors) | `5bb5016d…` / `c5414767…` | MATCH |
| V8 selection freeze / p3 invariants / proposal | `e5d8f7e4…` / `5ca0bcea…` / `240e5290…` | MATCH |
| V8 staged FRED raw (13 series) vs manifest | aggregate | 13/13 MATCH (verified 3× independent) |
| V12 panel / cohort / v10-timing / v10-revision pins | `67591464…` `6a95401f…` `b1477ea3…` `7110cbf0…` | MATCH (A7 at cc85fc5 → H0 → resume: same values) |

## 6. Program counters, budgets, S1, workers, locks

- Ledger (P-9 authority): **233 published / 236 observed, 0 survivors**;
  crypto 155/158, stocks 39/39, forex 39/39 — unchanged across the entire
  cycle; **no scored cell anywhere in SHV1**.
- Budgets: V17 **0/6**, V8 **0/6** (selection binds 3 cells), V12 **0/6**
  (closed, slots dead). S1: **SEALED_UNTOUCHED** everywhere.
- Workers 0; machine heavy lock FREE (0-byte lock, no registry holder; last
  release STOCKS-FREE-V12/D2 FINISHED 07:50:35Z). Scheduler job journal ready
  at `~/.my-quantitative-governance/heavy_runtime/scheduler_jobs.json`.

## 7. A7 objections and verdict

**`SYSTEM_HARDENING_V1_PASS`** — 4 objections, all LOW, dispositions:
1. Registry V8 go_phrase fields empty vs packet → **FIXED** at `88da553`
   through the canonical `cycle_registry.save()` path (CAS + journal); V17
   state wording reconciled in the same commit.
2. V8 pause commit re-encoded 2 state.json lines (escape `\uXXXX` → UTF-8
   literal, semantic no-op) beyond the disclosed additive field → **recorded,
   verdict-neutral** (history append-only; no scientific field changed; A7
   adjudicated).
3. `CYCLE_REGISTRY.events.jsonl` not yet exercised → **resolved**: journal
   created and exercised by the OBJ-1 reconciliation write (1 append-only
   `REGISTRY_SAVED` row).
4. `.runtime/shv1_drafts/` RESUME_* are drafts, not evidence → **superseded**:
   packets formally promoted and published at `8ddfefe` after the verdict.

## 8. Exact next actions (plan §10 order — operational, not profitability)

1. **FOREX-FREE-V8 first**: resume packet `RESUME_FOREX_V8.{json,md}`;
   next action = I implementation (A8 lane) of FXFV8-A5-P1 from the selection
   freeze (3 cells). Preconditions: owner merges the SHV1 wave; owner types a
   **fresh GO** at the cycle's own prelaunch (P-8 — no GO carries across the
   pause).
2. **CRYPTO-V17 second**: next action = full 39-symbol-month build attempt 3
   (freeze v5, stall-hardened) under the machine-wide heavy lock; same
   fresh-GO + prelaunch requirements.
3. **STOCKS-FREE-V12**: **no resume** — TERMINAL. Continuation requires a
   materially new information set and is a **later owner decision**
   (`RESUME_STOCKS_V12.*` is record-only).

## 9. Deferred to SHV2 (explicit)

- Content-addressed store for historical data; worktree/branch archive or
  deletion policy (51→56 worktrees / 319→324 branches left untouched by
  design).
- Unifying all asset runners into one framework; a new statistics service.
- Any change to scientific gates, thresholds, families, or scored-cell
  budgets.
- `plans/ACTIVE_CYCLES.json` projection regeneration semantics (closed-cycle
  wording) once the canonical registry is adopted at merge; doctor's
  REGISTRY_NOT_ADOPTED label disappears at the same point.
- Scheduler heavy-admission wiring into the existing per-cycle heavy-lock
  acquisition paths (module + tests shipped; production adoption lands with
  the next heavy job per cycle-owner).

## 10. Resume-readiness (machine summary)

```json
{"verdict": "SYSTEM_HARDENING_V1_PASS", "resume_recommended": true,
 "owner_keys_required": ["merge SHV1 wave to main", "fresh GO forex V8 prelaunch", "fresh GO crypto V17 prelaunch"],
 "stocks_v12": "no resume - later owner decision",
 "scientific_drift": "NONE", "budgets": "0/6 everywhere", "s1": "SEALED_UNTOUCHED"}
```
