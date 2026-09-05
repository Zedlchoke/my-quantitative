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

---

## Forex program state (synced 2026-09-05 — separate from the V10R→V11 track above)

Forex V3 closed with provisional survivor FXFV3-A6-P1 (vol-gated policy-rate
carry); the V3R data-authority remediation then recorded
`FOREX_FREE_V3_DATA_AUTHORITY_INVALIDATED` (anchor fails frozen
STRESS_TIER_2.0 under evidenced announcement availability — PF 1.2825
fin-adj, expectancy +20.72; control arm refused by the frozen validator, so
mechanism sanity is null; A7 PASS 9/9, 0 blocking). Family2 is in the
forbidden inventory with the economic observation recorded; front-door
re-entry only via a future owner-preregistered plan under the standard
ancestry rho gates. S1 never opened, stays SEALED. No forex thread is
preregistered. Detail:
`.worktrees/forex-free-v3r/integration/research/control/forex_free_v3r_run/terminal_verdict.json`.
