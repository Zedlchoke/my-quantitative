# CONTINUE.md — STOCKS-FREE-V2R RECONCILED / V3 ENTRY STATE

Read `PLAN_stocks.md` completely. It is the fresh-context Stocks authority.

## Measured entry state

- STOCKS-FREE-V2 is TERMINAL and reconciled. Effective sprint verdict:
  `STOCKS_FREE_V1_REJECT_ALL` (terminal A7 recomputation superseded the
  conservative `INCOMPLETE_NOT_PROMOTABLE` label; the original report and
  pre-amendment `family_verdicts.json` are preserved byte-for-byte as history).
- Effective family verdicts: A4 momentum `STOCKS_FREE_V1_FAMILY_REJECT`;
  A5 trend/defensive `STOCKS_FREE_V1_FAMILY_REJECT` (per
  `family_verdicts_amendment.json`; the A5 fail-closed concentration ruling
  was a staged-runner sidecar artifact — CASH counted in turnover, cost
  accumulated twice — verified independently by terminal A7 at ~1e-15).
- Counters 6/6 observed/published; budget 6/6; reproduction 6/6 EXACT_MATCH
  (`z9_reproduction.json`). Canonical code freeze
  `STOCKS_FREE_W1 = 106378230abecbaefff4248eeb373794f1b73038` — the stale
  `5046a87…` self-reference in `state.json` is superseded
  (`w1_freeze.json` correction; detached z8-exec-1/z8-exec-2/z9-reproduce
  trees pin the canonical SHA).
- FD2 carries `PASS_AMENDED_V2_SPLIT_FACTORS` (the stale
  `A7_REAUDIT_PENDING` suffix is superseded; the re-audit is complete).
- S1 `2025-08-01..2026-07-31` remains SEALED_UNTOUCHED. No paper, testnet,
  live or order authority exists. Workers zero.
- Reconciliation record:
  `research/control/stocks_free_v2_run/v2r_reconciliation_intake.json`;
  unambiguous effective-verdict surface:
  `research/control/stocks_free_v2_run/terminal_effective_verdict.json`.

## Next cycle: STOCKS-FREE-V3

- Authority: `PLAN_stocks.md` (V2R reconciliation + outcome-blind V3
  discovery). V3 is a screening cycle on reused S0 — not OOS. Maximum two
  genuinely new families × three frozen arms = six scored cells; budget 0/6;
  V3 counters start 0/0; historical Stocks denominator 6.
- Forbidden ancestry: A4 momentum parameter variants, A5 trend/SMA/vol-target
  variants, selected-ETF rescue, plain long-SPY-beta results, and anything
  needing paid data, new accounts or network fetch.
- No scored cell may start without a separate owner `GO STOCKS V3 SCORED
  EXECUTION` after a fresh A7 prelaunch
  (`STOCKS_FREE_V3_S0_LAUNCH_AUTHORIZED`).

## Boundaries

Unchanged: honest evidence first — REJECT_ALL, BLOCKED, INCOMPLETE are valid
outcomes; no tuning after observing a fold; no S1 access; no paper/live;
historical trees preserved; no push, main merge, worktree deletion or history
rewrite without explicit owner instruction; missing evidence is
`NOT_RUN`/`UNAVAILABLE_FAIL_CLOSED`, never inferred PASS.
