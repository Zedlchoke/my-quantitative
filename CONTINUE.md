# CONTINUE.md — V10P TERMINAL: V10_BLOCKED_PRELAUNCH

Read `PLAN.md` completely. It is the fresh-context authority. This file records
the measured terminal state of sprint V10P-R and the exact entry conditions for
the next thread.

## Measured terminal state (2026-08-27T15:03Z)

- Terminal outcome: **`V10_BLOCKED_PRELAUNCH`** (A7 verdict
  `NO_GO_BLOCKED_PRELAUNCH`, 0/3 scored cells consumed, denominator still 117).
- Integration HEAD: `orca/v10-integration@86b7274`, clean
  (`83627bc` = A7 audit commit; `86b7274` = terminal closeout on top).
  - `W2` (code-bearing, R1b/R2b pin): `d61a483`
  - docs handoff: `1fabeff` (root, not pushed); BOOTSTRAP_SHA `5bb1a90`
- Deadline `2026-08-27T16:55:00Z` had ~112 minutes left at close; the
  `<120 min` scored-launch cutoff (14:55Z) had already passed, and the
  measured resource cap was `final_cap=0` — E1 could not open either way.

## Why blocked (A7 recompute, all gates self-measured at W2)

1. **HIGH — G05_COVERAGE_SHORTFALL**: staged bars end
   `2026-08-20T02:29:59.999Z` vs preregistered window end
   `2026-08-21T00:00:00Z` → 86 bars / 21.5 h short (99.7545% coverage).
   `build_daily_closes` silently synthesizes the final daily close from a
   21.5 h-old bar instead of failing closed; no control artifact recorded the
   gap. **Owner-scope remediation**: re-stage catalog data through the window
   end, or owner re-declares the window end; and make coverage fail-closed.
2. **BLK-2**: scored launch window closed (<120 min) at 14:55Z.
3. **BLK-3**: `final_cap=0` at audit time (available 1.98 GB < 2.0 GB
   reserve). `final_cap = min(owner_ceiling=1, measured_safe_cap)`; a fresh
   probe with more headroom may yield 1, never above it.

Everything else PASSED independent recompute: G05 ETH loader (0 duplicates,
70,079 raw), window/folds pins, BG1–BG6, G15 hand-reconciled, F2 cache strict
proof (adopted, raw_reads 2 vs 6, byte parity), G17 one measured authority,
H08 cases 12–20 enumerated+tested, W2/R1b/R2b identity, budget purity, full
suite 1275 passed / 1 skipped (exit 0).

## Built this sprint (reuse, do not rebuild)

- Generic adapter `research/adapter_v10/` (contract
  `research/control/v10p_run/adapter_contract_v10.json`), dummy + M01 plugin
  reuse proven; BG1–BG6 closed; exactly-once publish in adapter layer.
- `research/funding_settlements_v10.py` (BG3), G15 independent fixtures,
  `research/cache_resource_measure_v10.py` (F2/G17 probes, exit-code
  semantics), G3 acceptance + fault-injection suites (52 tests), H08 12–20.
- Fresh detached execution trees `exec-v10-R1b` / `exec-v10-R2b` at `d61a483`,
  staged data verified 47/47 manifest entries, byte-identical, read-only.
  **NOTE**: `catalog/` extras and `funding_data/scan_2026/<SYM>/funding.json`
  are NOT git-tracked — fresh worktrees must copy them from the root repo or
  old exec trees, then verify against
  `research/control/v10_discovery_run/stage_manifest_R1.csv`.
- Consolidated artifacts in `research/control/v10p_run/`: remediation ledger,
  acceptance/funding/cache-resource/fault/integration reports, terminal
  closeout, worktree manifest, event log, heartbeat.
- Old `W=79fc883` and `exec-v10-R1/R2` preserved untouched; never score from
  them.

## Immediate critical path for the next thread

1. Owner decides: re-stage data to cover `2026-08-21T00:00:00Z` OR re-declare
   the scored window end. Make `build_daily_closes`/coverage fail-closed.
2. Re-run `research/cache_resource_measure_v10.py --probe-resource`; require
   `measured_safe_cap >= 1` (monotone clamp: only keep or lower afterwards).
3. Fresh A7 prelaunch re-audit on the new freeze (recompute, not read).
4. Only `V10_LAUNCH_AUTHORIZED` + fresh probe >= 1 + >=120 min remaining opens
   E1: anchor → 30-day-dispersion neighbor → C2 price-placebo, serial,
   then R2b reproduction 3/3 and terminal science (PLAN §11–§13).

## Boundaries (unchanged)

No new hypothesis, no M01 tuning on observed PnL, no push, no deletion, no S1,
no equity scored run, no paper/testnet/live/orders. Honest evidence:
`BLOCKED_PRELAUNCH` is a valid, recorded outcome; budget 0/3 is preserved.
