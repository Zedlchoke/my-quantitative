# FOREX-FREE-V9 — A7 PRELAUNCH AUDIT NOTES (fresh-context)

- Auditor: A7, independent, first contact with this cycle. Head audited
  `5b9e6d11045ea3fddd3fd8ce893436160ac72007`, branch
  `orca/forex-free-v9-q-a7-prelaunch`, porcelain 0 at start and end.
- Verdict: **`FOREX_FREE_V9_PRELAUNCH_REFUSED`** — 1 CRITICAL, 1 HIGH,
  3 MEDIUM, 4 LOW, all unresolved. `launch_gate.s0_launch_authorized`
  stays FALSE; nothing was repaired, nothing authorized, no push.

## What was verified clean (substance)

- **Worktree/pins**: all 6 pinned staged bytes re-hashed MATCH (GB ONS
  `164f5f89…`, CA tidy `21ab59af…`, GB_CAL `aad19697…`, CA_CAL_V3
  `0f1a9328…`, AU_CAL `42a4e4a3…`, NZ_CAL `62f82c23…`); FRED manifest row
  counts match the P0 census (4737/5091/1551/1958/1962).
- **Tests**: FOREX V9 suite 100/100 PASS (signals 26 + golden e2e 4 +
  runner 70); v6+v8 kernel suites 152 passed / 1 skipped / 0 failed —
  P1's zero-kernel-regression claim holds. (tests/test_v9_universe_audit.py
  is a different program's V9 — crypto cohort-10 — and its tmp-path
  fixture errors are unrelated to this cycle.)
- **Q reproduced end-to-end**: my own `--dry-run` on the copied gitignored
  staging reproduces the recorded non-vacuity evidence exactly
  (P1 135 pooled anchor entries, folds 47/44/44; P2 198, folds 56/73/69);
  twin smoke run twice in fresh sandboxes → artifacts byte-identical;
  dry-run report contains zero PnL-shaped fields (only `pnl_suppressed`);
  my own `validate_contract` and `smoke_check_twin_rerun` (absolute driver
  path, fresh sandbox) both `DIAGNOSTIC_CONTRACT_PASS`.
- **Scored refusal PROVEN**: `scored` without authorization → exit 2,
  refusal JSON (`missing_gates: [s0_launch_authorized, owner_fresh_go]`),
  contract byte-unchanged, no ledger created, porcelain stayed 0. The
  reader fails closed on a missing contract file; no bypass path found
  (no hidden mode; dry-run sanitized by construction; budget rule
  `used + 6 <= 6` enforced).
- **A8 adjudications independently audited**: CA ref-month = release−1
  (~12 ref-months/yr measured from the pinned calendar); AU in-S0 rebase
  (vintage 2018-10-09) rebase-safety verified FROM STAGED BYTES (2017-07-01
  re-issued at 103.459 new base in that vintage; 2018-07-01 first binds
  2018-11-13 at 105.4098 same base); family-level gate-10 stamping
  implemented and disclosed; +7d sham shifts every binding instant
  (fixtures present; P1 neighbour counts identical 135=135; P2 196 vs 198
  noted).
- **Governance hygiene**: no PnL-shaped key anywhere in
  `research/control/forex_free_v9_run/` (grep 0 hits); S1 SEALED_UNTOUCHED
  in every artifact; budget 0/6; registry row ACTIVE_LIGHT; **no V9 cycle
  branch exists on the remote and no local V9 branch has an upstream**.
  Gate encodings in the V9 driver are line-identical to V8's
  (`evaluate_gates` diff), so thresholds are the frozen V7/V8 ones.

## Why REFUSED

### F-CRIT-1 — D2 novelty PASS refuted (both selected families)

The frozen D2 gate is `pooled |rho| <= 0.20 vs ALL forbidden ancestry`
(p3 freeze, identical-to-V7/V8 machinery: 3 pooled Spearman variants on
±1 exposure-cell maps, cell `f..x-1`). I rebuilt the machinery from the
committed V7 script (`compute_ancestry_rhos_v7.py` — V9's port was never
committed) and **validated it exactly**: it reproduces the recorded
identifiability values 0.2296 / 0.2607 / 0.1273 to the digit.

Measured on **the frozen daily 16:00-NY decision-grid books the runners
actually produce** (anchor ±1 exposure maps from `run_arm`, same ancestor
set the D2 verdict names — V7 evidence 14 + V8 family schedules 9, both
committed):

| schedule | worst ancestor | netsigned | full_grid | verdict @0.20 |
|---|---|---|---|---|
| FXFV9-A5-P1 anchor | FXFV8-A5-P1-anchor | **0.3034** | 0.2117 | VETO |
| FXFV9-A5-P2 anchor | FXFV8-A5-P1-anchor | **0.3119** | 0.2258 | VETO |
| FXFV9-A5-P1 neighbour | FXFV8-A5-P1-anchor | 0.2974 | 0.2065 | VETO |
| FXFV9-A5-P2 neighbour | FXFV8-A5-P1-anchor | 0.3002 | 0.2191 | VETO |

Robust: span-restricting to the ancestors' observable window (2020-01-30+)
raises the values (0.3208 / 0.3303); two of three pooled variants exceed
the bar. `FXFV8-A5-P1-anchor` is a forbidden V8 entry (dispersion family,
veto (a) class).

Root cause: the committed D2 A5 evidence cells are a **different
construction** — monthly-grid ±1 state maps keyed `YYYY-MM|pair` spanning
1917-01..2026-07 (930 months; e.g. `1949-01|USDCAD`) — not the frozen
daily S0 books. That representation was never frozen, disclosed, or
adjudicated; its downsampling plus ~700 pre-S0 dead months destroyed
exactly the daily co-exposure structure the gate measures, yielding the
recorded PASSes 0.1062 / 0.0580. The A4 vetoes are confirmed (A4-P1 is
even stronger under my recompute: netsigned 0.9276 vs V4-commodity-trigger),
so the builder audit caught the A4 side but not the A5 representation.

Consequence: the selection freeze (6/6 cells to A5-P1+A5-P2) stands on a
refuted measurement. As measured, no family is eligible — a measured
reject-all-shaped closure is the expected terminal unless a spec-conformant
re-measurement (committed port + committed maps, no tuning) contradicts it.

### F-HIGH-1 — GB/CA conditioning channel violates the frozen PIT mandate

`conditioning.build_economy_legs` reads GB and CA entirely from
current-vintage official tables. The frozen proposals say (AX2-C1)
"current-vintage pulls forbidden in scored paths"; official tables are
flagged tail continuations only (GB after 2025-03), and the P3 freeze
repeats it ("the PIT qualification rests on the vintaged channel"). The
vintaged GB/CA archives are staged and sha-manifested — and unconsumed.
Availability instants still come from the pinned calendars and AU/NZ/US
are vintaged, so the defect is confined to the consumed VALUES of 2 of 5
legs; it injects no PnL and bypasses no gate, but the Q dry-run evidence
certifies the deviating implementation. Not covered by any of the four
adjudications.

### MEDIUM / LOW

- **F-MED-1** `run_contract.json` diagnostic contract still says
  `N = 39 + V8 cells` — residual V8 copy-over (sibling of the cycle_id
  oversight that WAS fixed); freeze/plan say N = 42 + V9 cells. Validator
  ignores the string, so the recorded gate PASS is genuine.
- **F-MED-2** recorded D2 magnitudes not reproducible from committed cells
  (A4-P1 0.2599, A4-P2 0.4842, A5-P1 ident 0.2008 — the continuous zstand
  layer was never committed); A4 veto verdicts unaffected/conservative.
- **F-MED-3** Q dry-run evidence lives at `/tmp/p0work/dryrun9_int.json`
  ("copied evidence pending") — bytes never committed; substance
  independently reproduced (135/198 exact).
- **F-LOW-1..4** identifiability bar "0.98 hard" cited from a freeze that
  doesn't contain it (inherited V8 chain); event log stops at P0;
  `state.json` head stale; registry phase field stale (ACTIVE_LIGHT
  itself is correct).

## What this audit did NOT do

Did not repair anything, did not re-stage or modify data bytes, did not
authorize anything, did not push, did not contact the implementer. Data
bytes copied from the integration worktree into `data_raw/` (gitignored,
never committed). The audit deliverables are committed by explicit
pathspec.
