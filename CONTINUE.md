# CONTINUE.md — NEW AGENT HANDOFF FOR V9H-R → V10

Read `PLAN.md` completely before acting. This is a status pointer, not a
replacement for the plan.

## Current measured state

- Root: `main=e5b0bab`, `origin/main=425843d`; no push authorized.
- Integration: `/Users/hoangminhlong/my-quantitative-v10-wt/integration-v10`,
  `orca/v10-integration=b7c39a2`, clean.
- V9 closed `V9_REJECT_ALL_MULTI_FAMILY`; denominator=117.
- Archive/restore complete: 356 files, 231,797,462 bytes, bundle hash
  `b5ce4097e09f8de1f99b67a4bc0dbf4b2390daad78cc594591907b9a60a12b12`.
- H1/H2 commits are integrated. Do not redo them.
- A8/A9 not started; V10 scored budget consumed=0.
- Missing: committed A7 PASS, final H01–H14 ledger, final integrated full-suite
  and measured resource-cap reports.
- Previous deadline `2026-08-26T23:51:56Z` expired.
- Existing A7 tree is dirty in A10's golden report. Preserve it; create a new
  clean A7-R worktree rather than overwriting it.

## Exact next action

1. Verify all V10 worktree HEADs/tree states and active owned workers.
2. Freeze a new maximum four-hour `recovery_contract.json`; explicitly preserve
   the expired deadline and zero V10 budget.
3. Reconcile actual H2 commits/tests/clean states into both manifests.
4. Create clean A7-R from `b7c39a2`; leave old dirty A7 untouched.
5. Produce missing test/resource/gate evidence and run A7-R H01–H14 audit.
6. Close `V9H_PASS_V10_AUTHORIZED` or
   `V9H_BLOCKED_V10_NOT_AUTHORIZED`.
7. Only after PASS, freeze a separate 12-hour V10 contract and dispatch A8/A9
   proposal agents in parallel. No implementation/backtest before blinded
   selection.

## Agent rules

- A1 alone creates worktrees, merges, freezes and launches.
- Maximum four light agents including A1; heavy workers =
  `min(2, frozen_governor_cap)`.
- Separate worktree and non-overlapping allowlist per role.
- Each agent returns clean commit, tests, limitations and SHA.
- Never edit root/main from subagent worktrees or recreate completed A2–A6/A10.

## Stop boundaries

No V10 score without V9H+A7 PASS. No rejected-family rescue, S1, equity score,
paper/testnet/live/order, push or worktree deletion. On permission or deadline
block, write evidence and stop cleanly instead of bypassing safeguards.

## Required first report

Return actual root/integration SHA, worktree HEADs/states, owned workers,
old/new deadlines, missing H01–H14 evidence, planned agent wave, and confirmation
that V10 budget remains 0.
