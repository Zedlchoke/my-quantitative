# CONTINUE.md — V10R → V11 ENTRY STATE

Read `PLAN.md` completely. It is the fresh-context authority.

## Measured entry state

- Prior sprint V10P-R closed `V10_BLOCKED_PRELAUNCH` with budget 0/3
  consumed (now 0/9 under the owner amendment) and denominator 117.
- Full record: `research/control/v10p_run/terminal_closeout_v10p.json`;
  integration `orca/v10-integration@86b7274`, clean, pushed to GitHub.
- The reusable adapter pipeline (BG1–BG6, G15, F2, G17, H08 12–20) is built,
  accepted (52-test matrix) and frozen at `W2=d61a483` with detached
  `exec-v10-R1b`/`exec-v10-R2b`. Do not rebuild any of it.
- Single remaining HIGH: `G05_COVERAGE_SHORTFALL` — staged bars end 21.5 h
  before the preregistered window end `2026-08-21T00:00:00Z`; the daily-close
  builder silently synthesizes the stale tail instead of failing closed.
- Owner directives (2026-08-28): **Option A** (fetch the missing data, window
  unchanged), **24 h clock**, second wave = **2 families / 6 cells**
  (authorized ceiling now 3 families / 9 cells total).

## Immediate critical path

1. Go-live: record the 24 h deadline in
   `research/control/v10r_run/heartbeat.json`.
2. R0: extend staged bars (and funding if short) through the window end using
   existing download infra; make `build_daily_closes`/coverage fail-closed
   with a regression test pinning the V10P defect; re-stage + byte-verify.
3. R1: freeze W3; detached `exec-v10-R1c`/`exec-v10-R2c`; full suite alone.
4. R2: fresh A7 prelaunch audit on W3; launch only on authorized verdict +
   fresh resource probe ≥1 heavy worker + ≥120 min left.
5. R3/R4: M01 anchor → neighbor → C2, serial; reproduce 3/3 from R2c; family
   terminal science; write lessons into the register.
6. V11: blinded proposals → novelty + rescue → freeze 2 families → implement
   through the adapter → prelaunch audit → 3 cells each → reproduce → close.

## Boundaries

Unchanged from PLAN §10. Honest evidence first: REJECT_ALL, BLOCKED,
INCOMPLETE are valid outcomes; no tuning on observed PnL; no S1, equity
scored runs, paper/testnet/live, orders; historical trees preserved; push
only on owner instruction.

## First fresh-thread report

Return measured UTC, deadline remaining, integration HEAD, budget, and the
R0 plan; then continue without repeated GO.

## Host handoff — 2026-08-28T00:56Z (A1, mid-sprint, machine move to 16GB host)

- R0 DONE: D1 fail-closed coverage (`78d77e1`) + D2 restage verify (`1a66e90`)
  merged; D2 premise correction: staged tree already covers window end
  (filename-range artifact caused the V10P stale-tail reading); BTC/ETH
  duplicate-parts flag routed to R2 A7 recompute. Fixtures aligned per lesson
  (d) (`c968b5c`).
- R1 DONE: full suite alone **1283 passed / 1 skipped / 0 failed**;
  **W3 = `2d5c30dcd32e4e3bfa02fe7d41de8804212327a5`** (code-identity vs suite
  SHA verified); exec `R1c`/`R2c` detached at W3, staged read-only,
  byte-identical 50/50, manifests 27+20 all_match.
- Budget 0/9, denominator 117, deadline **2026-08-29T00:05:50Z** absolute.
- NEXT (on the 16GB host): clone `orca/v10-integration` at W3, migration bundle
  `/Users/hoangminhlong/v10r_migration_bundle/` (README inside) → R2 fresh A7 +
  fresh `--probe-resource` (gate `measured_safe_cap ≥ 1`) → R3 3 M01 cells
  serial → R4 reproduce → V11 wave. Open questions for A7 are listed in
  `research/control/v10r_run/r1_freeze_W3.json`.
- Old host's `exec-v10-R1c`/`R2c` are machine-local: recreate detached at W3 on
  the new host per `worktree_manifest_v10r.json`; do NOT carry stale trees.

## Owner amendment — 2026-08-28 (ceiling)

Heavy-worker ceiling raised to **3**, scoped ONLY to: R4 reproduction
processes, V11 cross-family chains (within-family serial preserved), V11
reproduction waves. **R3 M01 cells stay serial ceiling=1.** G17 floor
`min(ceiling, measured_safe_cap)` unchanged; measured 0 still = no launch.
See `research/control/v10r_run/owner_amendment_ceiling_v10r.json`; A7 audits
against this amended contract.
